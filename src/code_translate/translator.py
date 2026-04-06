"""Translation engine wrapping HuggingFace transformers pipeline.

Key optimisations over a naïve per-chunk approach:

- **Batch processing**: all uncached chunks are collected and sent to the
  model in batches (default 16), leveraging the pipeline's native batching.
- **Deduplication**: identical chunks across segments are translated once.
- **Memory management**: ``torch.no_grad()`` prevents gradient tracking;
  ``gc.collect()`` / ``torch.cuda.empty_cache()`` between batches.
- **Separate tokenizer**: loaded independently so that token-counting for
  text splitting does not pull the full model into memory.
- **Disk cache**: SHA-256 keyed JSON files with metadata, backward-compatible
  with the legacy ``.txt`` cache format.
"""

from __future__ import annotations

import gc
import hashlib
import json
import logging
import re
import shutil
import warnings
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    """A piece of translatable text extracted from a source file."""

    text: str
    line_start: int  # 1-based
    line_end: int  # 1-based, inclusive
    kind: str  # "comment", "docstring", "markdown_text"


@dataclass
class TranslatedSegment:
    """A translated segment with its original position info."""

    text: str
    line_start: int
    line_end: int
    kind: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Regex to split on sentence boundaries (period, exclamation, question mark
# followed by whitespace or end of string).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Default cache directory: ~/.cache/codetranslate/
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "codetranslate"


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------


class Translator:
    """Wraps a HuggingFace translation pipeline for batch translation.

    Translations are cached to disk so that:

    - Repeated runs skip the model entirely for cached chunks (zero memory
      pressure).
    - Identical segments across files are translated once.
    - Crashed runs can be resumed without re-translating.

    Processing pipeline::

        split segments → deduplicate chunks → batch cache lookup
            → batch translate uncached → cache new results → reassemble
    """

    BATCH_SIZE = 16
    # Hard limit for input tokens (OPUS-MT models typically support 512)
    MAX_INPUT_TOKENS = 512
    # Maximum output tokens (slightly higher to allow for translation expansion)
    MAX_OUTPUT_TOKENS = 512

    def __init__(
        self,
        model_name: str,
        *,
        cache_dir: Path | None = None,
        no_cache: bool = False,
    ) -> None:
        self._model_name = model_name
        self._pipeline = None
        self._tokenizer = None
        self._no_cache = no_cache
        self._cache_dir = cache_dir or DEFAULT_CACHE_DIR
        if not self._no_cache:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Lazy-loading of heavy objects
    # ------------------------------------------------------------------

    @property
    def tokenizer(self):
        """Lazy-load the tokenizer independently of the model.

        This lets us count tokens for text splitting *before* loading the
        full translation model into memory.
        """
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        return self._tokenizer

    @property
    def pipeline(self):
        """Lazy-load the translation pipeline, reusing the tokenizer."""
        if self._pipeline is None:
            import torch
            from transformers import pipeline as hf_pipeline

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._pipeline = hf_pipeline(
                    "translation",
                    model=self._model_name,
                    tokenizer=self.tokenizer,
                    truncation=True,
                    device=self._select_device(),
                )
            logger.info("Loaded translation model: %s", self._model_name)
        return self._pipeline

    @staticmethod
    def _select_device() -> int | str:
        """Pick the best available device for the pipeline.

        Returns:
            - ``"mps"`` for Apple Silicon GPU (if available)
            - ``0`` for the first CUDA device (if available with >= 1 GiB free)
            - ``-1`` for CPU otherwise
        """
        try:
            import torch

            # Prefer Apple Silicon MPS if available
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"

            # Fall back to CUDA if available
            if torch.cuda.is_available():
                free_mem = torch.cuda.mem_get_info(0)[0]  # free bytes
                if free_mem >= 1 * 1024**3:  # >= 1 GiB free
                    return 0
        except Exception:
            pass
        return -1

    @property
    def max_input_tokens(self) -> int:
        """Maximum input token count.

        Uses the minimum of the model's max_length and our hard limit of 512
        to ensure compatibility with OPUS-MT models.
        """
        try:
            model_max = self.tokenizer.model_max_length
            # Use the minimum to stay within safe bounds
            return min(model_max, self.MAX_INPUT_TOKENS)
        except Exception:
            return self.MAX_INPUT_TOKENS

    # ------------------------------------------------------------------
    # Disk cache
    # ------------------------------------------------------------------

    def _cache_key(self, text: str) -> str:
        """Deterministic SHA-256 hash for (model_name, text)."""
        h = hashlib.sha256()
        h.update(self._model_name.encode("utf-8"))
        h.update(text.encode("utf-8"))
        return h.hexdigest()

    def _cache_path(self, key: str) -> Path:
        """File path for a cache entry, sharded into 256 sub-directories."""
        return self._cache_dir / key[:2] / f"{key}.json"

    def _legacy_cache_path(self, key: str) -> Path:
        """Path for legacy .txt cache entries (pre-batch format)."""
        return self._cache_dir / key[:2] / f"{key}.txt"

    def _read_cache(self, text: str) -> str | None:
        """Return cached translation, or None on miss.

        Tries the JSON format first, then falls back to the legacy .txt
        format for backward compatibility.
        """
        if self._no_cache:
            return None
        key = self._cache_key(text)

        # Try JSON format
        json_path = self._cache_path(key)
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text("utf-8"))
                return data["translation"]
            except (json.JSONDecodeError, KeyError):
                pass

        # Fall back to legacy .txt format
        txt_path = self._legacy_cache_path(key)
        if txt_path.exists():
            translation = txt_path.read_text("utf-8")
            # Migrate to JSON on read
            self._write_cache(text, translation)
            txt_path.unlink(missing_ok=True)
            return translation

        return None

    def _write_cache(self, text: str, translation: str) -> None:
        """Persist a translation to the disk cache in JSON format."""
        if self._no_cache:
            return
        path = self._cache_path(self._cache_key(text))
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model": self._model_name,
            "translation": translation,
        }
        path.write_text(json.dumps(data, ensure_ascii=False), "utf-8")

    def _batch_read_cache(self, texts: list[str]) -> dict[int, str]:
        """Read cache for multiple texts.  Returns ``{index: translation}``."""
        if self._no_cache:
            return {}
        results: dict[int, str] = {}
        for i, text in enumerate(texts):
            cached = self._read_cache(text)
            if cached is not None:
                results[i] = cached
        if results:
            logger.debug("Cache hit for %d / %d chunks", len(results), len(texts))
        return results

    def _batch_write_cache(self, pairs: list[tuple[str, str]]) -> None:
        """Write multiple translations to cache."""
        if self._no_cache:
            return
        for text, translation in pairs:
            self._write_cache(text, translation)

    # ------------------------------------------------------------------
    # Token-aware text splitting
    # ------------------------------------------------------------------

    def _token_length(self, text: str) -> int:
        """Return the number of tokens for the given text.

        Uses the tokenizer directly — no model weights loaded.
        """
        return len(self.tokenizer.encode(text, add_special_tokens=True))

    def _split_text(self, text: str, max_tokens: int) -> list[str]:
        """Split text into chunks that each fit within *max_tokens*.

        Tries to split at sentence boundaries.  Falls back to newline
        boundaries, then word boundaries.
        """
        if self._token_length(text) <= max_tokens:
            return [text]

        chunks: list[str] = []

        # Strategy 1: sentence boundaries
        sentences = _SENTENCE_SPLIT_RE.split(text)
        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if self._token_length(candidate) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if self._token_length(sentence) > max_tokens:
                    chunks.extend(self._split_by_lines(sentence, max_tokens))
                    current = ""
                else:
                    current = sentence
        if current:
            chunks.append(current)

        return chunks if chunks else [text[:200]]

    def _split_by_lines(self, text: str, max_tokens: int) -> list[str]:
        """Split text by newline boundaries, falling back to word boundaries."""
        lines = text.split("\n")
        chunks: list[str] = []
        current = ""
        for line in lines:
            candidate = f"{current}\n{line}" if current else line
            if self._token_length(candidate) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if self._token_length(line) > max_tokens:
                    chunks.extend(self._split_by_words(line, max_tokens))
                    current = ""
                else:
                    current = line
        if current:
            chunks.append(current)
        return chunks

    def _split_by_words(self, text: str, max_tokens: int) -> list[str]:
        """Split text by word boundaries as a last resort."""
        words = text.split()
        chunks: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            if self._token_length(candidate) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # Even a single word may exceed the limit (e.g. a long URL);
                # truncate to stay within bounds.
                if self._token_length(word) > max_tokens:
                    chunks.append(word[:max_tokens * 4])
                    current = ""
                else:
                    current = word
        if current:
            chunks.append(current)
        return chunks

    # ------------------------------------------------------------------
    # Core translation with batch processing
    # ------------------------------------------------------------------

    def _truncate_to_max_tokens(self, text: str) -> str:
        """Hard-truncate text to the model's maximum token count.

        This is a safety net: even after ``_split_text``, a chunk could
        exceed the model's position embedding table size if the tokenizer
        counts differently from the pipeline's internal encoder.  By
        encoding and decoding here we guarantee the token IDs never
        exceed ``model_max_length``.
        """
        max_len = self.max_input_tokens
        tokens = self.tokenizer.encode(text, truncation=True, max_length=max_len)
        return self.tokenizer.decode(tokens, skip_special_tokens=True)

    def _translate_batch(self, chunks: list[str]) -> list[str]:
        """Translate a list of chunks using the pipeline in one batch call.

        * Pre-truncates every chunk to ``MAX_INPUT_TOKENS`` so token IDs
          never exceed the embedding table size.
        * Uses ``torch.no_grad()`` to prevent gradient tracking.
        * Suppresses tokenizer warnings.
        """
        import torch

        # Safety: force every chunk within the model's token limit
        truncated_chunks = [self._truncate_to_max_tokens(c) for c in chunks]

        with torch.no_grad(), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = self.pipeline(
                truncated_chunks,
                max_length=self.MAX_OUTPUT_TOKENS,
                truncation=True,
                batch_size=len(truncated_chunks),
            )

        translations: list[str] = []
        for r in results:
            if isinstance(r, list):
                translations.append(r[0]["translation_text"])
            else:
                translations.append(r["translation_text"])
        return translations

    def _translate_chunks(self, chunks: list[str]) -> list[str]:
        """Translate chunks with caching and batch processing.

        1. Batch cache lookup for all chunks.
        2. Batch-translate uncached chunks (in sub-batches of ``BATCH_SIZE``).
        3. Cache new translations.
        4. Return results in original order.
        """
        if not chunks:
            return []

        # Step 1: check cache
        cached = self._batch_read_cache(chunks)
        uncached_indices = [i for i in range(len(chunks)) if i not in cached]

        if not uncached_indices:
            logger.info("All %d chunk(s) served from cache", len(chunks))
            return [cached[i] for i in range(len(chunks))]

        logger.info(
            "Translating %d chunk(s) (%d cached, %d new)",
            len(chunks),
            len(cached),
            len(uncached_indices),
        )

        # Step 2: translate uncached chunks in sub-batches
        all_translations: dict[int, str] = dict(cached)

        for batch_start in range(0, len(uncached_indices), self.BATCH_SIZE):
            batch_indices = uncached_indices[batch_start : batch_start + self.BATCH_SIZE]
            batch_texts = [chunks[i] for i in batch_indices]

            batch_results = self._translate_batch(batch_texts)

            # Step 3: cache and collect results
            cache_pairs: list[tuple[str, str]] = []
            for idx, text, translation in zip(batch_indices, batch_texts, batch_results):
                all_translations[idx] = translation
                cache_pairs.append((text, translation))

            self._batch_write_cache(cache_pairs)

            # Free memory between batches
            del batch_results, cache_pairs
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except ImportError:
                pass

        return [all_translations[i] for i in range(len(chunks))]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate_segments(self, segments: list[Segment]) -> list[TranslatedSegment]:
        """Translate a list of segments, returning results in the same order.

        Long segments are split into sub-chunks at sentence boundaries so
        that each chunk fits within the model's input limit.  **All unique
        chunks across all segments are collected, deduplicated, and
        batch-translated** for maximum throughput.
        """
        if not segments:
            return []

        # Phase 1: split all segments into chunks, recording the mapping.
        # segment_chunks[i] = list of chunk indices belonging to segment i
        all_chunks: list[str] = []
        segment_chunks: list[list[int]] = []

        for seg in segments:
            chunks = self._split_text(seg.text, self.max_input_tokens)
            if len(chunks) > 1:
                logger.info(
                    "Segment at lines %d-%d split into %d chunk(s)",
                    seg.line_start,
                    seg.line_end,
                    len(chunks),
                )
            start_idx = len(all_chunks)
            all_chunks.extend(chunks)
            segment_chunks.append(list(range(start_idx, len(all_chunks))))

        # Phase 2: deduplicate — translate each unique text exactly once.
        unique_chunks: list[str] = []
        chunk_to_unique: dict[int, int] = {}
        seen: dict[str, int] = {}

        for i, chunk in enumerate(all_chunks):
            if chunk not in seen:
                seen[chunk] = len(unique_chunks)
                unique_chunks.append(chunk)
            chunk_to_unique[i] = seen[chunk]

        if len(unique_chunks) < len(all_chunks):
            logger.info(
                "Deduplicated %d chunks → %d unique",
                len(all_chunks),
                len(unique_chunks),
            )

        # Phase 3: batch-translate all unique chunks (cache-aware).
        unique_translations = self._translate_chunks(unique_chunks)

        # Phase 4: reassemble segments from translated chunks.
        translated: list[TranslatedSegment] = []
        for seg_idx, seg in enumerate(segments):
            chunk_indices = segment_chunks[seg_idx]
            parts = [unique_translations[chunk_to_unique[ci]] for ci in chunk_indices]
            # Preserve the line-break style of the original text
            joiner = "\n" if "\n" in seg.text else " "
            combined = joiner.join(parts)

            translated.append(
                TranslatedSegment(
                    text=combined,
                    line_start=seg.line_start,
                    line_end=seg.line_end,
                    kind=seg.kind,
                )
            )

        return translated

    def translate_text(self, text: str) -> str:
        """Translate a single string, splitting and caching if necessary."""
        chunks = self._split_text(text, self.max_input_tokens)
        results = self._translate_chunks(chunks)
        joiner = "\n" if "\n" in text else " "
        return joiner.join(results)

    @classmethod
    def clear_cache(cls, cache_dir: Path | None = None) -> int:
        """Remove all cached translations. Returns the number of entries deleted."""
        cache_dir = cache_dir or DEFAULT_CACHE_DIR
        if not cache_dir.exists():
            return 0
        count = sum(1 for _ in cache_dir.rglob("*.json"))
        count += sum(1 for _ in cache_dir.rglob("*.txt"))
        shutil.rmtree(cache_dir, ignore_errors=True)
        return count

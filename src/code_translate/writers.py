"""Reconstruct source files with translated comments/docs, preserving structure."""

from __future__ import annotations

from pathlib import Path

from .parsers import ParseResult
from .translator import TranslatedSegment


def write_translated(
    parsed: ParseResult,
    translated: list[TranslatedSegment],
    dest: Path,
) -> None:
    """Write a file with translated segments replacing the originals.

    The strategy depends on the file type:
    - For code files: replace comments/docstrings in-place line by line.
    - For Markdown/txt files: replace full text segments.
    """
    suffix = parsed.filepath.suffix.lower()

    if suffix == ".md":
        _write_markdown(parsed, translated, dest)
    elif suffix == ".txt":
        _write_plain_text(parsed, translated, dest)
    else:
        _write_code_file(parsed, translated, dest)


def _write_code_file(
    parsed: ParseResult,
    translated: list[TranslatedSegment],
    dest: Path,
) -> None:
    """Replace comments and docstrings in a code file, preserving code."""
    lines = list(parsed.lines)  # copy

    # Build a map: (line_start, line_end) -> translated text lines
    replacements: dict[tuple[int, int], list[str]] = {}
    for seg in translated:
        replacements[(seg.line_start, seg.line_end)] = seg.text.splitlines()

    # Apply replacements in reverse order so line numbers stay valid
    for (start, end), new_lines in sorted(replacements.items(), reverse=True):
        # start and end are 1-based, convert to 0-based
        start_idx = start - 1
        end_idx = end  # slice exclusive
        lines[start_idx:end_idx] = new_lines

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(
    parsed: ParseResult,
    translated: list[TranslatedSegment],
    dest: Path,
) -> None:
    """Replace prose segments in a Markdown file, preserving code blocks and structure."""
    lines = list(parsed.lines)
    # Build replacement map
    replacements: dict[tuple[int, int], list[str]] = {}
    for seg in translated:
        replacements[(seg.line_start, seg.line_end)] = seg.text.splitlines()

    # Apply replacements in reverse order
    for (start, end), new_lines in sorted(replacements.items(), reverse=True):
        start_idx = start - 1
        end_idx = end  # slice exclusive
        lines[start_idx:end_idx] = new_lines

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_plain_text(
    parsed: ParseResult,
    translated: list[TranslatedSegment],
    dest: Path,
) -> None:
    """Replace the entire text content of a plain text file."""
    if not translated:
        dest.write_text(parsed.filepath.read_text(encoding="utf-8"), encoding="utf-8")
        return

    # For plain text, there should be one segment covering the whole file
    dest.write_text(translated[0].text + "\n", encoding="utf-8")

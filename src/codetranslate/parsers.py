"""Extract translatable text (comments, docstrings, Markdown prose) from source files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .translator import Segment


@dataclass
class ParseResult:
    """Result of parsing a file: extracted translatable segments + raw lines."""

    filepath: Path
    lines: list[str] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Language-specific comment patterns
# ---------------------------------------------------------------------------

# Single-line comment starters per file extension
LINE_COMMENT_PREFIX: dict[str, str] = {
    ".py": "#",
    ".js": "//",
    ".ts": "//",
    ".tsx": "//",
    ".jsx": "//",
    ".rs": "//",
    ".go": "//",
    ".java": "//",
    ".c": "//",
    ".cpp": "//",
    ".h": "//",
    ".hpp": "//",
    ".cs": "//",
    ".rb": "#",
    ".sh": "#",
    ".bash": "#",
    ".yaml": "#",
    ".yml": "#",
    ".toml": "#",
}

# Block comment delimiters: (open, close)
BLOCK_COMMENT: dict[str, tuple[str, str]] = {
    ".py": ('"""', '"""'),
    ".js": ("/*", "*/"),
    ".ts": ("/*", "*/"),
    ".tsx": ("/*", "*/"),
    ".jsx": ("/*", "*/"),
    ".rs": ("/*", "*/"),
    ".go": ("/*", "*/"),
    ".java": ("/*", "*/"),
    ".c": ("/*", "*/"),
    ".cpp": ("/*", "*/"),
    ".h": ("/*", "*/"),
    ".hpp": ("/*", "*/"),
    ".cs": ("/*", "*/"),
}


def parse_file(filepath: Path) -> ParseResult:
    """Parse a file and extract translatable segments."""
    suffix = filepath.suffix.lower()
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    if suffix == ".md":
        return _parse_markdown(filepath, lines)
    elif suffix == ".txt":
        return _parse_plain_text(filepath, lines)
    elif suffix in LINE_COMMENT_PREFIX or suffix in BLOCK_COMMENT:
        return _parse_code_file(filepath, lines, suffix)
    else:
        return ParseResult(filepath=filepath, lines=lines)


# ---------------------------------------------------------------------------
# Markdown parser — translate prose, skip fenced code blocks
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")


def _parse_markdown(filepath: Path, lines: list[str]) -> ParseResult:
    """Extract translatable prose from Markdown, skipping code fences."""
    result = ParseResult(filepath=filepath, lines=lines)
    in_code_block = False
    segment_start: int | None = None
    segment_lines: list[str] = []

    for i, line in enumerate(lines):
        lineno = i + 1
        fence_match = _CODE_FENCE_RE.match(line)

        if fence_match and not in_code_block:
            # Flush accumulated text
            _flush_segment(result, segment_start, segment_lines, "markdown_text")
            segment_start = None
            segment_lines = []
            in_code_block = True
            continue
        elif fence_match and in_code_block:
            in_code_block = False
            continue

        if in_code_block:
            continue

        stripped = line.strip()
        if stripped == "":
            _flush_segment(result, segment_start, segment_lines, "markdown_text")
            segment_start = None
            segment_lines = []
            continue

        if segment_start is None:
            segment_start = lineno
        segment_lines.append(stripped)

    _flush_segment(result, segment_start, segment_lines, "markdown_text")
    return result


# ---------------------------------------------------------------------------
# Plain text parser — treat entire file as translatable
# ---------------------------------------------------------------------------

def _parse_plain_text(filepath: Path, lines: list[str]) -> ParseResult:
    """Treat all non-empty lines of a .txt file as one translatable segment."""
    result = ParseResult(filepath=filepath, lines=lines)
    non_empty = [line.strip() for line in lines if line.strip()]
    if non_empty:
        result.segments.append(
            Segment(text="\n".join(non_empty), line_start=1, line_end=len(lines), kind="markdown_text")
        )
    return result


# ---------------------------------------------------------------------------
# Code file parser — extract line comments and block docstrings
# ---------------------------------------------------------------------------

def _parse_code_file(filepath: Path, lines: list[str], suffix: str) -> ParseResult:
    """Extract comments and docstrings from a source code file."""
    result = ParseResult(filepath=filepath, lines=lines)
    prefix = LINE_COMMENT_PREFIX.get(suffix)
    block_open, block_close = BLOCK_COMMENT.get(suffix, ("/*", "*/"))

    # --- Extract line comments (consecutive runs merged into one segment) ---
    segment_start: int | None = None
    segment_lines: list[str] = []

    for i, line in enumerate(lines):
        lineno = i + 1
        stripped = line.strip()

        if prefix and stripped.startswith(prefix):
            # Strip the prefix and optional leading space
            comment_text = stripped[len(prefix):]
            if comment_text.startswith(" "):
                comment_text = comment_text[1:]
            # Skip shebangs, pragma comments, noqa, etc.
            if i == 0 and comment_text.startswith("!"):
                _flush_segment(result, segment_start, segment_lines, "comment")
                segment_start = None
                segment_lines = []
                continue
            if comment_text.lower().startswith(("noqa", "pragma", "type:", "pylint:")):
                _flush_segment(result, segment_start, segment_lines, "comment")
                segment_start = None
                segment_lines = []
                continue

            if segment_start is None:
                segment_start = lineno
            segment_lines.append(comment_text)
        else:
            _flush_segment(result, segment_start, segment_lines, "comment")
            segment_start = None
            segment_lines = []

    _flush_segment(result, segment_start, segment_lines, "comment")

    # --- Extract block docstrings ---
    if suffix == ".py":
        _extract_python_docstrings(result, lines)
    else:
        _extract_block_comments(result, lines, block_open, block_close)

    return result


def _extract_python_docstrings(result: ParseResult, lines: list[str]) -> None:
    """Extract triple-quoted docstrings from Python source."""
    docstring_re = re.compile(r'^(\s*)(r|u|f|rf|fr)?("""|\'\'\')(.*?)\3', re.DOTALL | re.MULTILINE)
    text = "\n".join(lines)

    for match in docstring_re.finditer(text):
        content = match.group(4).strip()
        if not content:
            continue

        # Calculate line numbers from character position
        start_char = match.start()
        line_start = text[:start_char].count("\n") + 1
        end_char = match.end()
        line_end = text[:end_char].count("\n") + 1

        result.segments.append(
            Segment(text=content, line_start=line_start, line_end=line_end, kind="docstring")
        )


def _extract_block_comments(
    result: ParseResult, lines: list[str], open_delim: str, close_delim: str
) -> None:
    """Extract /* ... */ style block comments from source code."""
    in_block = False
    block_start_line = 0
    block_lines: list[str] = []

    for i, line in enumerate(lines):
        lineno = i + 1
        stripped = line.strip()

        if not in_block:
            if stripped.startswith(open_delim):
                in_block = True
                block_start_line = lineno
                # Content starts after opening delimiter
                rest = stripped[len(open_delim):]
                # Check if closing on same line
                if close_delim in rest:
                    content = rest[: rest.index(close_delim)].strip()
                    if content:
                        result.segments.append(
                            Segment(text=content, line_start=lineno, line_end=lineno, kind="docstring")
                        )
                    in_block = False
                    block_lines = []
                    continue
                elif rest.strip():
                    block_lines.append(rest.strip())
        else:
            if close_delim in stripped:
                rest = stripped[: stripped.index(close_delim)].strip()
                if rest:
                    block_lines.append(rest)
                content = "\n".join(block_lines)
                if content:
                    result.segments.append(
                        Segment(
                            text=content,
                            line_start=block_start_line,
                            line_end=lineno,
                            kind="docstring",
                        )
                    )
                in_block = False
                block_lines = []
            else:
                block_lines.append(stripped)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flush_segment(
    result: ParseResult,
    start: int | None,
    lines: list[str],
    kind: str,
) -> None:
    """Flush accumulated lines into a segment on the parse result."""
    if start is None or not lines:
        return
    text = "\n".join(lines)
    result.segments.append(
        Segment(text=text, line_start=start, line_end=start + len(lines) - 1, kind=kind)
    )

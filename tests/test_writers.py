"""Tests for the writers module."""

from pathlib import Path
import tempfile

from codetranslate.parsers import ParseResult, parse_file
from codetranslate.translator import TranslatedSegment
from codetranslate.writers import write_translated


FIXTURES = Path(__file__).parent / "fixtures"


class TestWriteCodeFile:
    def test_replace_line_comments(self):
        """Translated comments should replace originals in code files."""
        original = parse_file(FIXTURES / "sample.py")

        # Create fake translations
        fake_translated = [
            TranslatedSegment(
                text="Ceci est un fichier Python",
                line_start=s.line_start,
                line_end=s.line_end,
                kind=s.kind,
            )
            for s in original.segments
        ]

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            dest = Path(f.name)

        try:
            write_translated(original, fake_translated, dest)
            result_text = dest.read_text(encoding="utf-8")
            assert "Ceci est un fichier Python" in result_text
            # Code should still be intact
            assert "def add(" in result_text
            assert "return a + b" in result_text
        finally:
            dest.unlink()

    def test_preserves_code_structure(self):
        """Code lines not part of comments/docstrings should be unchanged."""
        original = parse_file(FIXTURES / "sample.py")

        fake_translated = [
            TranslatedSegment(
                text="Translated docstring here",
                line_start=s.line_start,
                line_end=s.line_end,
                kind=s.kind,
            )
            for s in original.segments
        ]

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            dest = Path(f.name)

        try:
            write_translated(original, fake_translated, dest)
            result_text = dest.read_text(encoding="utf-8")
            # Function signatures preserved
            assert "def add(a: int, b: int) -> int:" in result_text
            assert "def factorial(n: int) -> int:" in result_text
            # Return statements preserved
            assert "return a + b" in result_text
            assert "return 1" in result_text
        finally:
            dest.unlink()


class TestWriteMarkdownFile:
    def test_replace_prose_preserve_code_blocks(self):
        """Markdown prose is replaced, code blocks are preserved."""
        original = parse_file(FIXTURES / "sample.md")

        fake_translated = [
            TranslatedSegment(
                text="Contenu traduit ici",
                line_start=s.line_start,
                line_end=s.line_end,
                kind=s.kind,
            )
            for s in original.segments
        ]

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            dest = Path(f.name)

        try:
            write_translated(original, fake_translated, dest)
            result_text = dest.read_text(encoding="utf-8")
            assert "Contenu traduit ici" in result_text
            # Code fences should still exist
            assert "```" in result_text
        finally:
            dest.unlink()


class TestWriteEmptyTranslation:
    def test_no_segments_no_change(self):
        """If there are no segments, the file should still be written."""
        p = Path("/tmp/_test_no_seg.py")
        p.write_text("x = 1\n", encoding="utf-8")
        try:
            parsed = parse_file(p)
            assert len(parsed.segments) == 0

            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
                dest = Path(f.name)
            try:
                write_translated(parsed, [], dest)
                assert dest.read_text(encoding="utf-8") == "x = 1\n"
            finally:
                dest.unlink()
        finally:
            p.unlink()

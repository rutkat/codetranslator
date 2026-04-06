"""Tests for the parsers module."""

from pathlib import Path
import textwrap

from code_translate.parsers import parse_file, _parse_markdown, _parse_code_file, ParseResult


FIXTURES = Path(__file__).parent / "fixtures"


class TestParsePythonFile:
    def test_extracts_line_comments(self):
        result = parse_file(FIXTURES / "sample.py")
        assert isinstance(result, ParseResult)

        # Should find line comment segments
        comment_segs = [s for s in result.segments if s.kind == "comment"]
        assert len(comment_segs) >= 2
        # First comment block: lines 1-2
        assert comment_segs[0].text.startswith("This is a sample Python file")

    def test_extracts_docstrings(self):
        result = parse_file(FIXTURES / "sample.py")
        docstring_segs = [s for s in result.segments if s.kind == "docstring"]
        assert len(docstring_segs) == 2
        assert "Add two numbers" in docstring_segs[0].text
        assert "factorial" in docstring_segs[1].text

    def test_preserves_all_lines(self):
        result = parse_file(FIXTURES / "sample.py")
        assert len(result.lines) > 0

    def test_skips_shebang(self):
        p = Path("/tmp/_test_shebang.py")
        p.write_text("#!/usr/bin/env python3\n# A real comment\n", encoding="utf-8")
        try:
            result = parse_file(p)
            comment_segs = [s for s in result.segments if s.kind == "comment"]
            texts = [s.text for s in comment_segs]
            assert not any("usr/bin/env" in t for t in texts)
            assert any("real comment" in t for t in texts)
        finally:
            p.unlink()

    def test_skips_noqa(self):
        p = Path("/tmp/_test_noqa.py")
        p.write_text("x = 1  # noqa: E501\n# A real comment\n", encoding="utf-8")
        try:
            result = parse_file(p)
            comment_segs = [s for s in result.segments if s.kind == "comment"]
            texts = [s.text for s in comment_segs]
            assert not any("noqa" in t for t in texts)
            assert any("real comment" in t for t in texts)
        finally:
            p.unlink()


class TestParseMarkdownFile:
    def test_extracts_prose_skips_code_blocks(self):
        result = parse_file(FIXTURES / "sample.md")
        assert isinstance(result, ParseResult)
        md_segs = [s for s in result.segments if s.kind == "markdown_text"]
        assert len(md_segs) >= 3  # Multiple prose sections

        # Code block content should NOT appear in segments
        all_text = " ".join(s.text for s in md_segs)
        assert "pip install" not in all_text
        assert "codetranslate" not in all_text
        # But prose should be there
        assert "Project README" in all_text or "sample project" in all_text


class TestParseJSFile:
    def test_extracts_line_comments(self):
        result = parse_file(FIXTURES / "sample.js")
        comment_segs = [s for s in result.segments if s.kind == "comment"]
        assert len(comment_segs) >= 2

    def test_extracts_block_comments(self):
        result = parse_file(FIXTURES / "sample.js")
        docstring_segs = [s for s in result.segments if s.kind == "docstring"]
        assert len(docstring_segs) == 1
        assert "Calculate the sum" in docstring_segs[0].text


class TestParseEmptyFile:
    def test_empty_file_returns_no_segments(self):
        p = Path("/tmp/_test_empty.py")
        p.write_text("", encoding="utf-8")
        try:
            result = parse_file(p)
            assert len(result.segments) == 0
        finally:
            p.unlink()

    def test_code_only_file_returns_no_segments(self):
        p = Path("/tmp/_test_code_only.py")
        p.write_text("x = 1\ny = 2\nprint(x + y)\n", encoding="utf-8")
        try:
            result = parse_file(p)
            assert len(result.segments) == 0
        finally:
            p.unlink()

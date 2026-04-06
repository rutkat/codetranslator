"""Tests for the languages module."""

import pytest

from code_translate.languages import list_languages, resolve_model


class TestListLanguages:
    def test_returns_dict(self):
        langs = list_languages()
        assert isinstance(langs, dict)

    def test_common_languages_present(self):
        langs = list_languages()
        for code in ["en", "fr", "es", "zh", "ru"]:
            assert code in langs, f"Missing language code: {code}"

    def test_names_are_strings(self):
        langs = list_languages()
        for code, name in langs.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0


class TestResolveModel:
    def test_basic_pair(self):
        model = resolve_model("en", "fr")
        assert model == "Helsinki-NLP/opus-mt-en-fr"

    def test_case_insensitive(self):
        model = resolve_model("EN", "FR")
        assert model == "Helsinki-NLP/opus-mt-en-fr"

    def test_alias_zh_cn(self):
        model = resolve_model("zh-cn", "en")
        assert model == "Helsinki-NLP/opus-mt-zh-en"

    def test_same_language_raises(self):
        with pytest.raises(ValueError, match="same"):
            resolve_model("en", "en")

    def test_whitespace_trimmed(self):
        model = resolve_model("  en  ", "  fr  ")
        assert model == "Helsinki-NLP/opus-mt-en-fr"

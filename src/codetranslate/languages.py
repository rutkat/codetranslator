"""Language code mapping and Helsinki-NLP model name resolution."""

# Common language code -> display name mapping
LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "nl": "Dutch",
    "ru": "Russian",
    "zh": "Chinese",
}

# Group codes used by Helsinki-NLP for multi-source or multi-target models
LANG_GROUPS: dict[str, list[str]] = {
    "ROMANCE": ["fr", "it", "es"],
}


def list_languages() -> dict[str, str]:
    """Return the supported language code -> name mapping."""
    return dict(LANGUAGES)


def resolve_model(source: str, target: str) -> str:
    """Resolve source and target language codes to a Helsinki-NLP model name.

    Raises ValueError if the language pair is not recognized.
    """
    source = source.lower().strip()
    target = target.lower().strip()

    # Normalize common variants
    alias_map: dict[str, str] = {
        "zh-cn": "zh", "zh-tw": "zh",
    }
    source = alias_map.get(source, source)
    target = alias_map.get(target, target)

    if source == target:
        raise ValueError(f"Source and target languages are the same: {source}")

    model_name = f"Helsinki-NLP/opus-mt-{source}-{target}"
    return model_name

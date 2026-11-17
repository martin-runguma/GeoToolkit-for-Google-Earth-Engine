"""Offline interface translation catalog for GeoToolkit.

Dataset/product identifiers and provider names are intentionally preserved.
Delegates to the modular i18n loader and per-language translation packs.
"""

from .. import i18n

# Kept for backward compatibility; translations now live in translations/<lang>.py.
TRANSLATIONS = {}


def translate(text, language="en"):
    """Translate interface text while preserving dynamic counters and values."""
    if not isinstance(text, str):
        return text
    lang = i18n.normalise(language)
    if lang == "en":
        return text
    result = i18n.tr(text, lang)
    if result != text:
        return result
    # Dynamic patterns: category headings with counts, e.g. "Imagery (3)".
    for source in ("Imagery", "Indices", "Other Rasters", "Vector"):
        target = i18n.tr(source, lang)
        if target != source:
            for sep in ("  (", " ("):
                if text.startswith(source + sep):
                    return target + text[len(source):]
    for source_key in ("Selected datasets (", "Vector export options ("):
        if text.startswith(source_key):
            translated = i18n.tr(source_key, lang)
            if translated != source_key:
                return translated + text[len(source_key):]
            prefix = source_key.rstrip("(").rstrip()
            tprefix = i18n.tr(prefix, lang)
            if tprefix != prefix:
                return tprefix + text[len(prefix):]
    return text

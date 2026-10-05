"""Internationalization (gettext-based)."""

import gettext
import locale as _locale
import os
from pathlib import Path

_DOMAIN = "open_tmux_tabs"

# Native names for known language codes. Add to this when new
# locales are translated.
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "nl": "Nederlands",
    "pl": "Polski",
    "ja": "日本語",
    "zh": "中文",
    "eo": "Esperanto",
    "tlh": "tlhIngan Hol",
    "ur": "اردو",
}


def find_locales_dir() -> Path:
    """Locate the locales directory.

    Checks inside the package first (wheel/pip install), then falls
    back to the repo root layout (editable install / development).
    """
    here = Path(__file__).resolve()
    candidates = [
        here.parent / "locales",                 # inside package (wheel)
        here.parent.parent.parent / "locales",   # repo root (editable)
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def get_available_languages() -> list[str]:
    """Return language codes for which a compiled .mo file exists,
    plus the source language ('en')."""
    locales_dir = find_locales_dir()
    found = {"en"}  # Source language is always available
    if locales_dir.exists():
        for child in locales_dir.iterdir():
            mo = child / "LC_MESSAGES" / f"{_DOMAIN}.mo"
            if mo.exists():
                found.add(child.name)
    return sorted(found)


def get_native_name(language: str) -> str:
    """Return the native display name for a language code."""
    return LANGUAGE_NAMES.get(language, language)


def detect_system_language() -> str:
    """Detect language from environment / locale settings."""
    raw = (
        os.environ.get("LANG", "")
        or os.environ.get("LC_ALL", "")
        or (_locale.getdefaultlocale()[0] or "en")
    )
    return raw.split("_")[0].split(".")[0] or "en"


def setup_i18n(language: str | None = None) -> str:
    """Install the gettext _() function globally.

    Args:
        language: Locale code (e.g. 'de', 'en'). If None, detected
            from environment.

    Returns:
        The actual language code that was installed.
    """
    locales_dir = find_locales_dir()

    if language is None:
        language = detect_system_language()

    try:
        translation = gettext.translation(
            _DOMAIN,
            localedir=str(locales_dir),
            languages=[language],
            fallback=True,
        )
    except FileNotFoundError:
        translation = gettext.NullTranslations()

    translation.install()
    return language


def _(message: str) -> str:
    """Fallback translator if setup_i18n() was never called."""
    import builtins
    if hasattr(builtins, "_"):
        return builtins._(message)
    return message

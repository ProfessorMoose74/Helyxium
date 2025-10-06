"""
Translation Management System

Handles multi-language support with dynamic language switching,
CJK font management, and platform-specific text rendering.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .detector import language_detector


class LocalizationManager:
    """Manages translations and localization features."""

    def __init__(self) -> None:
        """Initialize the localization manager."""
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._current_language: str = "en"
        self._translations_dir = Path(__file__).parent / "translations"

        # Initialize with detected system language
        self._current_language = language_detector.detect_system_language()
        self._load_translations()

    def initialize(self, language_code: str) -> bool:
        """
        Initialize the localization manager with a specific language.

        Args:
            language_code: Language code to initialize with

        Returns:
            True if initialization was successful
        """
        return self.set_language(language_code)

    def _load_translations(self) -> None:
        """Load all available translations."""
        if not self._translations_dir.exists():
            return

        for translation_file in self._translations_dir.glob("*.json"):
            lang_code = translation_file.stem
            try:
                with open(translation_file, "r", encoding="utf-8") as f:
                    self._translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Failed to load translation for {lang_code}: {e}")

    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.

        Args:
            language_code: Language code (e.g., 'zh_CN', 'en')

        Returns:
            True if language was set successfully
        """
        if language_code in self._translations:
            self._current_language = language_code
            return True
        elif language_code.split("_")[0] in self._translations:
            # Fallback to base language if specific variant not available
            self._current_language = language_code.split("_")[0]
            return True

        return False

    def get_current_language(self) -> str:
        """Get the current language code."""
        return self._current_language

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get all available languages.

        Returns:
            Dictionary mapping language codes to language names
        """
        return {
            lang_code: language_detector.get_language_name(lang_code)
            for lang_code in self._translations.keys()
        }

    def translate(self, key: str, **kwargs: Any) -> str:
        """
        Translate a key to the current language.

        Args:
            key: Translation key in dot notation (e.g., 'ui.main_window.title')
            **kwargs: Variables for string formatting

        Returns:
            Translated string or the key if translation not found
        """
        # Get translation for current language
        translation = self._get_nested_value(
            self._translations.get(self._current_language, {}), key
        )

        # Fallback to English if not found
        if translation is None and self._current_language != "en":
            translation = self._get_nested_value(self._translations.get("en", {}), key)

        # Final fallback to the key itself
        if translation is None:
            translation = key

        # Format string with provided variables
        if kwargs and isinstance(translation, str):
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Return unformatted string if formatting fails

        return str(translation)

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        """
        Get a nested value from dictionary using dot notation.

        Args:
            data: Dictionary to search in
            key: Dot-separated key path

        Returns:
            Value if found, None otherwise
        """
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def is_rtl_language(self, language_code: Optional[str] = None) -> bool:
        """
        Check if the language is right-to-left.

        Args:
            language_code: Language code to check (uses current if None)

        Returns:
            True if the language is RTL
        """
        if language_code is None:
            language_code = self._current_language

        rtl_languages = {"ar", "he", "fa", "ur"}
        return language_code.split("_")[0] in rtl_languages

    def is_cjk_language(self, language_code: Optional[str] = None) -> bool:
        """
        Check if the language is CJK (Chinese, Japanese, Korean).

        Args:
            language_code: Language code to check (uses current if None)

        Returns:
            True if the language is CJK
        """
        if language_code is None:
            language_code = self._current_language

        return language_detector.is_cjk_language(language_code)

    def get_font_family(self, language_code: Optional[str] = None) -> str:
        """
        Get the recommended font family for the language.

        Args:
            language_code: Language code (uses current if None)

        Returns:
            Font family name
        """
        if language_code is None:
            language_code = self._current_language

        # CJK font preferences
        cjk_fonts = {
            "zh_CN": "Microsoft YaHei, SimHei, WenQuanYi Micro Hei, sans-serif",
            "zh_TW": "Microsoft JhengHei, PMingLiU, WenQuanYi Micro Hei, sans-serif",
            "ja": "Yu Gothic, Meiryo, Hiragino Sans, sans-serif",
            "ko": "Malgun Gothic, Dotum, UnDotum, sans-serif",
        }

        if language_code in cjk_fonts:
            return cjk_fonts[language_code]

        # Default to system font for other languages
        return "Segoe UI, Arial, sans-serif"

    def get_font_size_multiplier(self, language_code: Optional[str] = None) -> float:
        """
        Get the font size multiplier for better readability.

        Args:
            language_code: Language code (uses current if None)

        Returns:
            Font size multiplier (1.0 = normal size)
        """
        if language_code is None:
            language_code = self._current_language

        # CJK languages often need slightly larger fonts for readability
        if self.is_cjk_language(language_code):
            return 1.1

        return 1.0

    def format_number(self, number: float, language_code: Optional[str] = None) -> str:
        """
        Format a number according to locale conventions.

        Args:
            number: Number to format
            language_code: Language code (uses current if None)

        Returns:
            Formatted number string
        """
        if language_code is None:
            language_code = self._current_language

        try:
            import locale

            # Map language codes to locale names
            locale_map = {
                "zh_CN": "zh_CN.UTF-8",
                "zh_TW": "zh_TW.UTF-8",
                "ja": "ja_JP.UTF-8",
                "ko": "ko_KR.UTF-8",
                "en": "en_US.UTF-8",
                "de": "de_DE.UTF-8",
                "fr": "fr_FR.UTF-8",
                "es": "es_ES.UTF-8",
            }

            locale_name = locale_map.get(language_code, "C")

            # Try to set locale and format number
            try:
                locale.setlocale(locale.LC_NUMERIC, locale_name)
                return locale.format_string("%.2f", number, grouping=True)
            except locale.Error:
                # Fallback to English formatting
                return f"{number:,.2f}"

        except ImportError:
            # Fallback formatting without locale
            return f"{number:,.2f}"

    def get_text_direction(self, language_code: Optional[str] = None) -> str:
        """
        Get the text direction for the language.

        Args:
            language_code: Language code (uses current if None)

        Returns:
            'rtl' for right-to-left, 'ltr' for left-to-right
        """
        if self.is_rtl_language(language_code):
            return "rtl"
        return "ltr"


# Global instance for easy access
localization_manager = LocalizationManager()


# Convenience function for translations
def tr(key: str, **kwargs: Any) -> str:
    """
    Convenience function for translations.

    Args:
        key: Translation key
        **kwargs: Variables for string formatting

    Returns:
        Translated string
    """
    return localization_manager.translate(key, **kwargs)

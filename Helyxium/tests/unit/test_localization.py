"""Tests for localization system."""

import pytest

from src.localization.detector import LanguageDetector
from src.localization.manager import LocalizationManager


def test_language_detector_initialization(language_detector):
    """Test LanguageDetector initializes correctly."""
    assert language_detector is not None


def test_detect_system_language(language_detector):
    """Test system language detection."""
    language = language_detector.detect_system_language()
    assert isinstance(language, str)
    assert len(language) == 2  # ISO 639-1 two-letter code


def test_is_cjk_language(language_detector):
    """Test CJK language detection."""
    assert language_detector.is_cjk_language("zh") is True
    assert language_detector.is_cjk_language("ja") is True
    assert language_detector.is_cjk_language("ko") is True
    assert language_detector.is_cjk_language("en") is False
    assert language_detector.is_cjk_language("es") is False


def test_localization_manager_initialization():
    """Test LocalizationManager initializes correctly."""
    loc_manager = LocalizationManager()
    assert loc_manager is not None


def test_get_available_languages():
    """Test retrieving available languages."""
    loc_manager = LocalizationManager()
    languages = loc_manager.get_available_languages()
    assert isinstance(languages, dict)
    assert len(languages) > 0
    assert "en" in languages


def test_current_language():
    """Test getting current language."""
    loc_manager = LocalizationManager()
    current = loc_manager.get_current_language()
    assert isinstance(current, str)
    assert len(current) == 2

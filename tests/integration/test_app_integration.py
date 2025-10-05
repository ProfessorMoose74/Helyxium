"""Integration tests for the main application."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
def test_app_initialization_flow(monkeypatch):
    """Test complete application initialization flow."""
    # Mock PyQt6 to avoid GUI requirements
    mock_qapp = Mock()
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication", Mock(return_value=mock_qapp))

    from src.core.application import HelyxiumApp

    app = HelyxiumApp()
    assert app is not None
    assert hasattr(app, 'config_manager')
    assert hasattr(app, 'language_detector')
    assert hasattr(app, 'hardware_detector')


@pytest.mark.integration
def test_detection_pipeline(monkeypatch):
    """Test hardware and platform detection pipeline."""
    from src.detection.hardware import HardwareDetector
    from src.detection.platforms import PlatformDetector

    hw_detector = HardwareDetector()
    platform_detector = PlatformDetector()

    hw_result = hw_detector.detect_vr_hardware()
    platform_result = platform_detector.detect_vr_platforms()

    assert 'devices_detected' in hw_result
    assert 'platforms_detected' in platform_result


@pytest.mark.integration
def test_localization_integration():
    """Test localization system integration."""
    from src.localization.detector import LanguageDetector
    from src.localization.manager import LocalizationManager

    lang_detector = LanguageDetector()
    loc_manager = LocalizationManager()

    detected_lang = lang_detector.detect_system_language()
    loc_manager.initialize(detected_lang)

    assert loc_manager.get_current_language() is not None

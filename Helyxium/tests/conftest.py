"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_qt_app(monkeypatch):
    """Mock PyQt6 QApplication for testing without GUI."""
    mock_app = MagicMock()
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication", Mock(return_value=mock_app))
    return mock_app


@pytest.fixture
def config_manager():
    """Provide a clean ConfigManager instance for testing."""
    from src.utils.config import ConfigManager

    config = ConfigManager()
    yield config
    # Cleanup: reset to defaults after test
    config._config = config._load_defaults()


@pytest.fixture
def language_detector():
    """Provide a LanguageDetector instance for testing."""
    from src.localization.detector import LanguageDetector

    return LanguageDetector()


@pytest.fixture
def theme_manager():
    """Provide a ThemeManager instance for testing."""
    from src.ui.themes import ThemeManager

    return ThemeManager()


@pytest.fixture
def mock_vr_device():
    """Provide a mock VR device for testing."""
    from src.detection.hardware import VRCapabilities, VRDevice, VRHeadsetType

    return VRDevice(
        device_type=VRHeadsetType.META_QUEST_2,
        name="Meta Quest 2",
        manufacturer="Meta",
        serial_number="TEST123456",
        firmware_version="v42.0",
        connection_type="USB",
        is_connected=True,
        capabilities=VRCapabilities(
            has_6dof=True,
            has_hand_tracking=True,
            has_passthrough=True,
            max_refresh_rate=120,
        ),
    )

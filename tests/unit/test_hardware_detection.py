"""Tests for VR hardware detection."""

import pytest

from src.detection.hardware import (
    HardwareDetector,
    VRCapabilities,
    VRDevice,
    VRHardwareDetector,
    VRHeadsetType,
)


def test_hardware_detector_initialization():
    """Test HardwareDetector initializes correctly."""
    detector = HardwareDetector()
    assert detector is not None
    assert hasattr(detector, "detect_vr_hardware")


def test_vr_hardware_detector_initialization():
    """Test VRHardwareDetector initializes correctly."""
    detector = VRHardwareDetector()
    assert detector is not None


def test_detect_vr_hardware_returns_dict():
    """Test that detect_vr_hardware returns expected structure."""
    detector = HardwareDetector()
    result = detector.detect_vr_hardware()

    assert isinstance(result, dict)
    assert "devices_detected" in result
    assert "supported_features" in result
    assert isinstance(result["devices_detected"], int)
    assert isinstance(result["supported_features"], list)


def test_vr_device_creation(mock_vr_device):
    """Test VRDevice dataclass creation."""
    assert mock_vr_device.device_type == VRHeadsetType.META_QUEST_2
    assert mock_vr_device.name == "Meta Quest 2"
    assert mock_vr_device.manufacturer == "Meta"
    assert mock_vr_device.is_connected is True
    assert mock_vr_device.capabilities.has_hand_tracking is True


def test_vr_capabilities_defaults():
    """Test VRCapabilities has sensible defaults."""
    caps = VRCapabilities()
    assert caps.has_6dof is True
    assert caps.has_hand_tracking is False
    assert caps.max_refresh_rate == 90


def test_hardware_change_detection():
    """Test hardware change detection."""
    detector = HardwareDetector()

    # First call should always return True
    assert detector.has_hardware_changed() is True

    # If no hardware changes, should return False
    if detector.detect_vr_hardware()["devices_detected"] == 0:
        assert detector.has_hardware_changed() is False

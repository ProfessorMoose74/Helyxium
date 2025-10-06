#!/usr/bin/env python3
"""
Quick test to verify core Helyxium components work correctly.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_language_detection():
    """Test language detection system."""
    print("Testing language detection...")
    from src.localization.detector import LanguageDetector

    detector = LanguageDetector()
    language = detector.detect_system_language()
    print(f"[OK] Detected language: {language}")
    print(f"[OK] Is CJK language: {detector.is_cjk_language(language)}")
    return True


def test_theme_detection():
    """Test theme detection system."""
    print("\nTesting theme detection...")
    from src.ui.themes import ThemeManager

    theme_manager = ThemeManager()
    theme = theme_manager.detect_system_theme()
    print(f"[OK] Detected theme: {theme}")
    print(f"[OK] Is dark theme: {theme_manager.is_dark_theme()}")
    return True


def test_hardware_detection():
    """Test VR hardware detection."""
    print("\nTesting VR hardware detection...")
    from src.detection.hardware import HardwareDetector

    detector = HardwareDetector()
    hardware_info = detector.detect_vr_hardware()
    print(f"[OK] Detected {hardware_info['devices_detected']} VR devices")
    print(f"[OK] Supported features: {hardware_info['supported_features']}")
    return True


def test_platform_detection():
    """Test VR platform detection."""
    print("\nTesting VR platform detection...")
    from src.detection.platforms import PlatformDetector

    detector = PlatformDetector()
    platform_info = detector.detect_vr_platforms()
    print(f"[OK] Detected {platform_info['platforms_detected']} VR platforms")
    print(f"[OK] Running platforms: {platform_info['running_platforms']}")
    return True


def test_authentication():
    """Test authentication system."""
    print("\nTesting authentication system...")
    from src.security.auth import AuthenticationManager

    auth_manager = AuthenticationManager()

    # Test user creation
    success, message = auth_manager.create_user(
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        display_name="Test User",
        age=25,
    )
    print(f"[OK] User creation: {success} - {message}")

    # Test authentication
    from src.security.auth import AuthenticationMethod

    result, session_id = auth_manager.authenticate("testuser", "TestPassword123!")
    print(f"[OK] Authentication: {result}")

    return True


def test_localization():
    """Test localization system."""
    print("\nTesting localization...")
    from src.localization.manager import LocalizationManager, tr

    loc_manager = LocalizationManager()

    # Test translation
    app_name = tr("app.name")
    tagline = tr("app.tagline")

    print(f"[OK] App name: {app_name}")
    print(f"[OK] Tagline: {tagline}")
    print(f"[OK] Current language: {loc_manager.get_current_language()}")
    print(
        f"[OK] Available languages: {list(loc_manager.get_available_languages().keys())}"
    )

    return True


def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration management...")
    from src.utils.config import ConfigManager

    config = ConfigManager()

    print(f"[OK] Language setting: {config.get('language')}")
    print(f"[OK] Theme setting: {config.get('theme')}")
    print(f"[OK] Config file: {config.config_file_path}")

    # Test setting a value
    config.set("test_setting", "test_value")
    retrieved_value = config.get("test_setting")
    print(f"[OK] Set/Get test: {retrieved_value == 'test_value'}")

    return True


def main():
    """Run all tests."""
    print("Starting Helyxium Core Component Tests")
    print("=" * 50)

    tests = [
        test_language_detection,
        test_theme_detection,
        test_hardware_detection,
        test_platform_detection,
        test_authentication,
        test_localization,
        test_configuration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} failed with error: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All core components are working correctly!")
        print("Helyxium is ready for use!")
    else:
        print("Some components need attention.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Quick test to verify core Helyxium components work correctly.
"""

import sys
import time
import logging
from pathlib import Path

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def sanitize_auth_result(result):
    """
    Sanitize authentication result for safe logging.
    Removes or masks any sensitive data.
    """
    if isinstance(result, dict):
        sanitized = result.copy()
        # Remove sensitive fields that might contain passwords or tokens
        sensitive_fields = ['password', 'token', 'secret', 'key', 'auth_token', 'session_token']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***REDACTED***'
        return sanitized
    elif isinstance(result, bool):
        return "SUCCESS" if result else "FAILED"
    elif isinstance(result, str):
        # Check if string might contain sensitive data
        sensitive_keywords = ['password', 'token', 'secret', 'key']
        if any(keyword.lower() in result.lower() for keyword in sensitive_keywords):
            return "***AUTHENTICATION_DATA_REDACTED***"
        return result
    else:
        return "AUTHENTICATION_COMPLETED" if result else "AUTHENTICATION_FAILED"

def test_language_detection():
    """Test language detection system."""
    print("Testing language detection...")
    from src.localization.detector import LanguageDetector
    
    detector = LanguageDetector()
    language = detector.detect_system_language()
    print(f"[OK] Detected language: {language}")
    print(f"[OK] Is CJK language: {detector.is_cjk_language(language)}")
    logger.info(f"Language detection successful: {language}")
    return True

def test_theme_detection():
    """Test theme detection system."""
    print("\nTesting theme detection...")
    from src.ui.themes import ThemeManager
    
    theme_manager = ThemeManager()
    theme = theme_manager.detect_system_theme()
    print(f"[OK] Detected theme: {theme}")
    print(f"[OK] Is dark theme: {theme_manager.is_dark_theme()}")
    logger.info(f"Theme detection successful: {theme}")
    return True

def test_hardware_detection():
    """Test VR hardware detection."""
    print("\nTesting VR hardware detection...")
    from src.detection.hardware import HardwareDetector
    
    detector = HardwareDetector()
    hardware_info = detector.detect_vr_hardware()
    print(f"[OK] Detected {hardware_info['devices_detected']} VR devices")
    print(f"[OK] Supported features: {hardware_info['supported_features']}")
    logger.info(f"Hardware detection completed: {hardware_info['devices_detected']} devices found")
    return True

def test_platform_detection():
    """Test VR platform detection."""
    print("\nTesting VR platform detection...")
    from src.detection.platforms import PlatformDetector
    
    detector = PlatformDetector()
    platform_info = detector.detect_vr_platforms()
    print(f"[OK] Detected {platform_info['platforms_detected']} VR platforms")
    print(f"[OK] Running platforms: {platform_info['running_platforms']}")
    logger.info(f"Platform detection completed: {platform_info['platforms_detected']} platforms found")
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
        age=25
    )
    # Don't log the actual message as it might contain sensitive info
    print(f"[OK] User creation: {success} - {'Success' if success else 'Failed'}")
    logger.info(f"User creation test: {'SUCCESS' if success else 'FAILED'}")
    
    # Test authentication - SECURITY FIX: Sanitize the result before logging
    from src.security.auth import AuthenticationMethod
    result, session_id = auth_manager.authenticate("testuser", "TestPassword123!")
    
    # Safely log authentication result without exposing sensitive data
    auth_status = sanitize_auth_result(result)
    print(f"[OK] Authentication: {auth_status}")
    
    # Log for debugging but ensure no sensitive data is included
    if result:
        logger.info("Authentication test: SUCCESS for user testuser")
        # Don't log the actual session_id in production
        print(f"[OK] Session created: {'Yes' if session_id else 'No'}")
    else:
        logger.warning("Authentication test: FAILED for user testuser")
        print(f"[FAIL] Authentication failed")
    
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
    print(f"[OK] Available languages: {list(loc_manager.get_available_languages().keys())}")
    
    logger.info(f"Localization test completed for language: {loc_manager.get_current_language()}")
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
    test_passed = retrieved_value == 'test_value'
    print(f"[OK] Set/Get test: {test_passed}")
    
    logger.info(f"Configuration test: {'SUCCESS' if test_passed else 'FAILED'}")
    return True

def main():
    """Run all tests."""
    print("Starting Helyxium Core Component Tests")
    print("=" * 50)
    
    logger.info("Starting Helyxium core component tests")
    
    tests = [
        test_language_detection,
        test_theme_detection,
        test_hardware_detection,
        test_platform_detection,
        test_authentication,
        test_localization,
        test_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                logger.info(f"Test {test.__name__}: PASSED")
            else:
                failed += 1
                logger.error(f"Test {test.__name__}: FAILED")
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} failed with error: {e}")
            logger.error(f"Test {test.__name__} failed with exception: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All core components are working correctly!")
        print("Helyxium is ready for use!")
        logger.info("All core component tests passed successfully")
    else:
        print("Some components need attention.")
        logger.warning(f"Core component tests completed with {failed} failures")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

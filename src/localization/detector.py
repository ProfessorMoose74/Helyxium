"""
Language Detection System with CJK Priority Support

Implements automatic detection of system language with priority for:
- Simplified Chinese (zh_CN)
- Traditional Chinese (zh_TW) 
- Japanese (ja)
- Korean (ko)
- English (en) and other Western languages
"""

import locale
import os
import platform
import sys
from typing import Dict, List, Optional, Tuple

try:
    import winreg
except ImportError:
    winreg = None


class LanguageDetector:
    """Detects system language with CJK priority support."""
    
    CJK_LANGUAGES = {
        "zh_CN": "Simplified Chinese",
        "zh_TW": "Traditional Chinese",
        "ja": "Japanese",
        "ko": "Korean"
    }
    
    SUPPORTED_LANGUAGES = {
        **CJK_LANGUAGES,
        "en": "English",
        "de": "German",
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi"
    }
    
    def __init__(self) -> None:
        """Initialize the language detector."""
        self._detected_language: Optional[str] = None
        self._detection_method: Optional[str] = None
    
    def detect_system_language(self) -> str:
        """
        Detect system language with priority for CJK languages.
        
        Detection methods (in order):
        1. System locale (primary)
        2. Platform-specific APIs (Windows, macOS, Linux)
        3. Environment variables (fallback)
        
        Returns:
            Language code (e.g., 'zh_CN', 'en', etc.)
        """
        if self._detected_language:
            return self._detected_language
        
        detection_methods = [
            self._detect_from_locale,
            self._detect_from_platform_api,
            self._detect_from_environment
        ]
        
        for method in detection_methods:
            try:
                lang_code = method()
                if lang_code:
                    self._detected_language = lang_code
                    self._detection_method = method.__name__
                    return lang_code
            except Exception:
                continue
        
        # Fallback to English
        self._detected_language = "en"
        self._detection_method = "fallback"
        return "en"
    
    def _detect_from_locale(self) -> Optional[str]:
        """Detect language from system locale."""
        try:
            # Get system default locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                return self._normalize_language_code(system_locale)
            
            # Try locale.getlocale()
            current_locale = locale.getlocale()[0]
            if current_locale:
                return self._normalize_language_code(current_locale)
                
        except Exception:
            pass
        
        return None
    
    def _detect_from_platform_api(self) -> Optional[str]:
        """Detect language using platform-specific APIs."""
        system = platform.system().lower()
        
        if system == "windows":
            return self._detect_windows_language()
        elif system == "darwin":  # macOS
            return self._detect_macos_language()
        elif system == "linux":
            return self._detect_linux_language()
        
        return None
    
    def _detect_windows_language(self) -> Optional[str]:
        """Detect language on Windows using registry."""
        if not winreg:
            return None
        
        # Try multiple registry approaches for different Windows versions
        registry_attempts = [
            # Windows 10/11 preferred UI language
            (winreg.HKEY_CURRENT_USER, r"Control Panel\International", "LocaleName"),
            # Windows 10/11 user profile
            (winreg.HKEY_CURRENT_USER, r"Control Panel\International\User Profile", "Languages"),
            # System default UI language
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Nls\Language", "Default"),
            # Fallback to install language
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Nls\Language", "InstallLanguage")
        ]
        
        for hkey, subkey, value_name in registry_attempts:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    value = winreg.QueryValueEx(key, value_name)[0]
                    if value_name == "Default" or value_name == "InstallLanguage":
                        result = self._windows_lcid_to_language(value)
                    else:
                        result = self._normalize_language_code(value)
                    
                    if result:
                        return result
            except (WindowsError, FileNotFoundError, OSError):
                continue
        
        return None
    
    def _detect_macos_language(self) -> Optional[str]:
        """Detect language on macOS using system preferences."""
        try:
            import subprocess
            
            # Get preferred languages from system preferences
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLanguages"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse the output to get the first language
                output = result.stdout.strip()
                if output.startswith("(") and output.endswith(")"):
                    languages = output[1:-1].split(",")
                    if languages:
                        first_lang = languages[0].strip().strip('"')
                        return self._normalize_language_code(first_lang)
                        
        except Exception:
            pass
        
        return None
    
    def _detect_linux_language(self) -> Optional[str]:
        """Detect language on Linux using environment variables."""
        # Check various locale environment variables
        env_vars = ["LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES"]
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                # Extract language code from locale string
                lang_code = value.split(".")[0].split("_")[0:2]
                if len(lang_code) >= 2:
                    return f"{lang_code[0]}_{lang_code[1]}"
                elif len(lang_code) == 1:
                    return lang_code[0]
        
        return None
    
    def _detect_from_environment(self) -> Optional[str]:
        """Detect language from environment variables (fallback)."""
        env_vars = ["LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LOCALE"]
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                normalized = self._normalize_language_code(value)
                if normalized:
                    return normalized
        
        return None
    
    def _normalize_language_code(self, lang_code: str) -> Optional[str]:
        """
        Normalize language code to supported format.
        
        Args:
            lang_code: Raw language code from system
            
        Returns:
            Normalized language code or None if unsupported
        """
        if not lang_code:
            return None
        
        # Clean up the language code
        lang_code = lang_code.lower().replace("-", "_")
        
        # Remove encoding and other suffixes
        lang_code = lang_code.split(".")[0].split("@")[0]
        
        # Handle different Chinese variants
        if lang_code.startswith("zh"):
            if "cn" in lang_code or "hans" in lang_code or "simplified" in lang_code:
                return "zh_CN"
            elif "tw" in lang_code or "hant" in lang_code or "traditional" in lang_code:
                return "zh_TW"
            elif "hk" in lang_code or "mo" in lang_code:
                return "zh_TW"  # Use Traditional Chinese for Hong Kong/Macau
            else:
                return "zh_CN"  # Default to Simplified Chinese
        
        # Handle full language codes (e.g., ja_JP -> ja)
        if "_" in lang_code:
            lang, region = lang_code.split("_", 1)
            
            # Special cases for languages with important regional variants
            if lang == "zh":
                if region in ["cn", "sg"]:
                    return "zh_CN"
                elif region in ["tw", "hk", "mo"]:
                    return "zh_TW"
                else:
                    return "zh_CN"
            
            # For other languages, check if we support the full code
            if lang_code in self.SUPPORTED_LANGUAGES:
                return lang_code
            
            # Otherwise, use just the language part
            if lang in self.SUPPORTED_LANGUAGES:
                return lang
        
        # Check if the language code is directly supported
        if lang_code in self.SUPPORTED_LANGUAGES:
            return lang_code
        
        return None
    
    def _windows_lcid_to_language(self, lcid: str) -> Optional[str]:
        """Convert Windows LCID to language code."""
        # Common Windows LCIDs for supported languages
        lcid_map = {
            "0804": "zh_CN",  # Chinese (Simplified, PRC)
            "0404": "zh_TW",  # Chinese (Traditional, Taiwan)
            "0c04": "zh_TW",  # Chinese (Traditional, Hong Kong)
            "1404": "zh_TW",  # Chinese (Traditional, Macau)
            "0411": "ja",     # Japanese
            "0412": "ko",     # Korean
            "0409": "en",     # English (US)
            "0809": "en",     # English (UK)
            "0407": "de",     # German
            "040c": "fr",     # French
            "0c0a": "es",     # Spanish
            "0410": "it",     # Italian
            "0816": "pt",     # Portuguese
            "0419": "ru",     # Russian
        }
        
        return lcid_map.get(lcid.lower())
    
    def get_detection_info(self) -> Dict[str, Optional[str]]:
        """
        Get information about the language detection process.
        
        Returns:
            Dictionary with detection details
        """
        return {
            "detected_language": self._detected_language,
            "detection_method": self._detection_method,
            "supported_languages": list(self.SUPPORTED_LANGUAGES.keys()),
            "cjk_languages": list(self.CJK_LANGUAGES.keys())
        }
    
    def is_cjk_language(self, lang_code: Optional[str] = None) -> bool:
        """
        Check if the detected or specified language is a CJK language.
        
        Args:
            lang_code: Language code to check (uses detected if None)
            
        Returns:
            True if the language is CJK
        """
        if lang_code is None:
            lang_code = self.detect_system_language()
        
        return lang_code in self.CJK_LANGUAGES
    
    def get_language_name(self, lang_code: Optional[str] = None) -> str:
        """
        Get the human-readable name of the detected or specified language.
        
        Args:
            lang_code: Language code to get name for (uses detected if None)
            
        Returns:
            Human-readable language name
        """
        if lang_code is None:
            lang_code = self.detect_system_language()
        
        return self.SUPPORTED_LANGUAGES.get(lang_code, "Unknown")


# Global instance for easy access
language_detector = LanguageDetector()
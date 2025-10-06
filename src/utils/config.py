"""
Configuration Management
Handles application settings and user preferences.
"""

import json
import logging
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class HelyxiumConfig:
    """Application configuration structure."""

    # Language and localization
    language: str = "auto"
    detected_language: Optional[str] = None

    # Theme settings
    theme: str = "auto"  # auto, light, dark
    detected_theme: Optional[str] = None

    # VR Hardware preferences
    preferred_headset: Optional[str] = None
    hardware_polling_interval: int = 5000  # milliseconds

    # Platform preferences
    auto_connect_platforms: bool = True
    platform_polling_interval: int = 10000  # milliseconds
    enabled_platforms: Dict[str, bool] = None

    # Security settings
    biometric_auth_enabled: bool = False
    require_auth_on_startup: bool = False
    session_timeout_minutes: int = 30

    # Privacy settings
    local_processing_only: bool = True
    data_collection_consent: Optional[bool] = None
    coppa_mode: bool = False
    age_verified: Optional[bool] = None

    # UI preferences
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    show_system_tray: bool = True
    minimize_to_tray: bool = True

    # Performance settings
    max_translation_threads: int = 4
    enable_hardware_acceleration: bool = True
    low_latency_mode: bool = False

    def __post_init__(self):
        """Initialize default values that depend on runtime conditions."""
        if self.enabled_platforms is None:
            self.enabled_platforms = {
                "meta": True,
                "steam": True,
                "playstation": True,
                "vrchat": True,
                "recroom": True,
                "horizon": True,
            }


class ConfigManager:
    """Manages application configuration and user preferences."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config: HelyxiumConfig = HelyxiumConfig()
        self._config_file = self._get_config_file_path()
        self._load_config()

    def _get_config_file_path(self) -> Path:
        """Get the configuration file path based on the platform."""
        system = platform.system().lower()

        if system == "windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "Helyxium"
        elif system == "darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "Helyxium"
        else:  # Linux and others
            config_dir = Path.home() / ".config" / "helyxium"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _load_config(self):
        """Load configuration from file."""
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Update config object with loaded values
                for key, value in config_data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

                self.logger.info(f"Configuration loaded from {self._config_file}")
            else:
                self.logger.info("No existing configuration found, using defaults")
                self.save_config()  # Save default config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.logger.info("Using default configuration")

    def save_config(self):
        """Save current configuration to file."""
        try:
            config_data = asdict(self.config)

            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration saved to {self._config_file}")

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any, save: bool = True):
        """Set a configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            if save:
                self.save_config()
            self.logger.debug(f"Configuration updated: {key} = {value}")
        else:
            self.logger.warning(f"Unknown configuration key: {key}")

    def update(self, updates: Dict[str, Any], save: bool = True):
        """Update multiple configuration values."""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                self.logger.warning(f"Unknown configuration key: {key}")

        if save:
            self.save_config()

    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = HelyxiumConfig()
        self.save_config()
        self.logger.info("Configuration reset to defaults")

    def get_platform_config(self, platform_name: str) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        return {
            "enabled": self.config.enabled_platforms.get(platform_name, False),
            "auto_connect": self.config.auto_connect_platforms,
            "polling_interval": self.config.platform_polling_interval,
        }

    def set_platform_enabled(self, platform_name: str, enabled: bool):
        """Enable or disable a specific platform."""
        self.config.enabled_platforms[platform_name] = enabled
        self.save_config()
        self.logger.info(
            f"Platform {platform_name} {'enabled' if enabled else 'disabled'}"
        )

    def is_privacy_mode_enabled(self) -> bool:
        """Check if privacy mode is enabled."""
        return self.config.local_processing_only

    def is_coppa_mode_enabled(self) -> bool:
        """Check if COPPA compliance mode is enabled."""
        return self.config.coppa_mode

    def get_ui_geometry(self) -> Dict[str, int]:
        """Get UI window geometry settings."""
        return {
            "width": self.config.window_width,
            "height": self.config.window_height,
            "maximized": self.config.window_maximized,
        }

    def set_ui_geometry(self, width: int, height: int, maximized: bool = False):
        """Set UI window geometry settings."""
        self.config.window_width = width
        self.config.window_height = height
        self.config.window_maximized = maximized
        self.save_config()

    @property
    def config_file_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_file

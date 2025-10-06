"""Tests for configuration management."""

import pytest

from src.utils.config import ConfigManager


def test_config_manager_initialization():
    """Test ConfigManager initializes with defaults."""
    config = ConfigManager()
    assert config is not None
    assert config.get("language") == "en"
    assert config.get("theme") in ["light", "dark", "auto"]


def test_config_set_and_get(config_manager):
    """Test setting and getting configuration values."""
    config_manager.set("test_key", "test_value")
    assert config_manager.get("test_key") == "test_value"


def test_config_get_nonexistent_key(config_manager):
    """Test getting a non-existent key returns default."""
    assert config_manager.get("nonexistent", "default") == "default"
    assert config_manager.get("nonexistent") is None


def test_config_persistence(tmp_path, monkeypatch):
    """Test configuration persists to file."""
    monkeypatch.setattr("src.utils.config.Path.home", lambda: tmp_path)

    config1 = ConfigManager()
    config1.set("persist_test", "value123")
    config1.save_config()

    # Create new instance to test persistence
    config2 = ConfigManager()
    assert config2.get("persist_test") == "value123"

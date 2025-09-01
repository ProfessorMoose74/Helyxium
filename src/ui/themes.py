"""
Theme Detection and Management System

Implements automatic theme detection and switching with support for:
- System dark/light mode detection
- Real-time theme switching when system changes
- Platform-specific theme adaptation
- User override capability
"""

import os
import platform
from enum import Enum
from typing import Dict, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

try:
    import darkdetect
except ImportError:
    darkdetect = None

try:
    import winreg
except ImportError:
    winreg = None


class ThemeType(Enum):
    """Available theme types."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ThemeManager(QObject):
    """Manages application themes with automatic detection and switching."""
    
    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str)  # Emits theme name: "light" or "dark"
    
    def __init__(self) -> None:
        """Initialize the theme manager."""
        super().__init__()
        
        self._current_theme: ThemeType = ThemeType.AUTO
        self._detected_theme: str = "light"
        self._user_override: Optional[ThemeType] = None
        self._theme_monitor_timer: Optional[QTimer] = None
        self._last_detected_theme: Optional[str] = None
        
        # Theme change callbacks
        self._theme_callbacks: Dict[str, Callable[[str], None]] = {}
        
        # Detect initial theme
        self._detect_system_theme()
        
        # Start monitoring for theme changes
        self._start_theme_monitoring()
    
    def detect_system_theme(self) -> str:
        """
        Detect the current system theme.
        
        Returns:
            'light' or 'dark'
        """
        return self._detect_system_theme()
    
    def _detect_system_theme(self) -> str:
        """
        Internal method to detect system theme using multiple methods.
        
        Returns:
            'light' or 'dark'
        """
        # Method 1: Use darkdetect library if available
        if darkdetect:
            try:
                detected = darkdetect.isDark()
                if detected is not None:
                    theme = "dark" if detected else "light"
                    self._detected_theme = theme
                    return theme
            except Exception:
                pass
        
        # Method 2: Platform-specific detection
        system = platform.system().lower()
        
        if system == "windows":
            theme = self._detect_windows_theme()
        elif system == "darwin":  # macOS
            theme = self._detect_macos_theme()
        elif system == "linux":
            theme = self._detect_linux_theme()
        else:
            theme = "light"  # Default fallback
        
        if theme:
            self._detected_theme = theme
            return theme
        
        # Final fallback
        self._detected_theme = "light"
        return "light"
    
    def _detect_windows_theme(self) -> Optional[str]:
        """Detect theme on Windows using registry."""
        if not winreg:
            return None
        
        try:
            # Check if dark mode is enabled for apps
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            ) as key:
                try:
                    # AppsUseLightTheme: 0 = dark, 1 = light
                    apps_use_light = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                    return "light" if apps_use_light else "dark"
                except FileNotFoundError:
                    # Try SystemUsesLightTheme as fallback
                    try:
                        system_use_light = winreg.QueryValueEx(key, "SystemUsesLightTheme")[0]
                        return "light" if system_use_light else "dark"
                    except FileNotFoundError:
                        pass
        except Exception:
            pass
        
        return None
    
    def _detect_macos_theme(self) -> Optional[str]:
        """Detect theme on macOS using system preferences."""
        try:
            import subprocess
            
            # Get the current appearance setting
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # If the command succeeds, dark mode is enabled
                return "dark"
            else:
                # If the command fails, light mode is likely enabled
                return "light"
                
        except Exception:
            pass
        
        return None
    
    def _detect_linux_theme(self) -> Optional[str]:
        """Detect theme on Linux using various methods."""
        # Method 1: Check GNOME theme
        try:
            import subprocess
            
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                theme_name = result.stdout.strip().lower()
                if "dark" in theme_name:
                    return "dark"
                elif "light" in theme_name:
                    return "light"
                    
        except Exception:
            pass
        
        # Method 2: Check KDE theme
        try:
            kde_config_path = os.path.expanduser("~/.config/kdeglobals")
            if os.path.exists(kde_config_path):
                with open(kde_config_path, "r") as f:
                    content = f.read().lower()
                    if "colorscheme=breezedark" in content or "dark" in content:
                        return "dark"
                    elif "colorscheme=breeze" in content or "light" in content:
                        return "light"
        except Exception:
            pass
        
        # Method 3: Check environment variables
        gtk_theme = os.environ.get("GTK_THEME", "").lower()
        if "dark" in gtk_theme:
            return "dark"
        elif "light" in gtk_theme:
            return "light"
        
        return None
    
    def get_current_theme(self) -> str:
        """
        Get the current effective theme.
        
        Returns:
            'light' or 'dark'
        """
        if self._user_override:
            if self._user_override == ThemeType.LIGHT:
                return "light"
            elif self._user_override == ThemeType.DARK:
                return "dark"
        
        # Auto mode or no override - use detected theme
        return self._detected_theme
    
    def set_theme(self, theme: ThemeType) -> None:
        """
        Set the application theme.
        
        Args:
            theme: Theme to set (LIGHT, DARK, or AUTO)
        """
        old_effective_theme = self.get_current_theme()
        
        if theme == ThemeType.AUTO:
            self._user_override = None
            self._current_theme = ThemeType.AUTO
        else:
            self._user_override = theme
            self._current_theme = theme
        
        new_effective_theme = self.get_current_theme()
        
        # Emit signal if effective theme changed
        if old_effective_theme != new_effective_theme:
            self.theme_changed.emit(new_effective_theme)
            self._notify_theme_callbacks(new_effective_theme)
    
    def get_theme_setting(self) -> ThemeType:
        """
        Get the current theme setting (not the effective theme).
        
        Returns:
            Current theme setting
        """
        return self._current_theme
    
    def is_dark_theme(self) -> bool:
        """
        Check if the current effective theme is dark.
        
        Returns:
            True if dark theme is active
        """
        return self.get_current_theme() == "dark"
    
    def is_light_theme(self) -> bool:
        """
        Check if the current effective theme is light.
        
        Returns:
            True if light theme is active
        """
        return self.get_current_theme() == "light"
    
    def register_theme_callback(self, name: str, callback: Callable[[str], None]) -> None:
        """
        Register a callback to be called when theme changes.
        
        Args:
            name: Unique name for the callback
            callback: Function to call with theme name ('light' or 'dark')
        """
        self._theme_callbacks[name] = callback
    
    def unregister_theme_callback(self, name: str) -> None:
        """
        Unregister a theme change callback.
        
        Args:
            name: Name of the callback to remove
        """
        self._theme_callbacks.pop(name, None)
    
    def _notify_theme_callbacks(self, theme: str) -> None:
        """Notify all registered callbacks of theme change."""
        for callback in self._theme_callbacks.values():
            try:
                callback(theme)
            except Exception as e:
                print(f"Error in theme callback: {e}")
    
    def _start_theme_monitoring(self) -> None:
        """Start monitoring system theme changes."""
        if self._theme_monitor_timer:
            return
        
        self._theme_monitor_timer = QTimer()
        self._theme_monitor_timer.timeout.connect(self._check_theme_change)
        # Check every 2 seconds for theme changes
        self._theme_monitor_timer.start(2000)
        
        self._last_detected_theme = self._detected_theme
    
    def _check_theme_change(self) -> None:
        """Check if system theme has changed."""
        if self._user_override and self._user_override != ThemeType.AUTO:
            # Don't monitor if user has manual override
            return
        
        old_theme = self._detected_theme
        new_theme = self._detect_system_theme()
        
        if old_theme != new_theme:
            self._detected_theme = new_theme
            
            # Only emit signal if we're in auto mode
            if not self._user_override or self._user_override == ThemeType.AUTO:
                self.theme_changed.emit(new_theme)
                self._notify_theme_callbacks(new_theme)
    
    def get_theme_stylesheet(self, theme: Optional[str] = None) -> str:
        """
        Get CSS stylesheet for the specified theme.
        
        Args:
            theme: Theme name ('light' or 'dark'), uses current if None
            
        Returns:
            CSS stylesheet string
        """
        if theme is None:
            theme = self.get_current_theme()
        
        if theme == "dark":
            return self._get_dark_stylesheet()
        else:
            return self._get_light_stylesheet()
    
    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet."""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #333333;
        }
        
        QWidget {
            background-color: #ffffff;
            color: #333333;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #333333;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #cccccc;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QLineEdit {
            border: 1px solid #cccccc;
            padding: 6px;
            border-radius: 4px;
            background-color: #ffffff;
        }
        
        QLineEdit:focus {
            border: 2px solid #0078d4;
        }
        
        QListWidget {
            border: 1px solid #cccccc;
            background-color: #ffffff;
            alternate-background-color: #f8f8f8;
        }
        
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #eeeeee;
        }
        
        QListWidget::item:selected {
            background-color: #0078d4;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #e0e0e0;
        }
        
        QStatusBar {
            background-color: #f0f0f0;
            border-top: 1px solid #cccccc;
        }
        
        QMenuBar {
            background-color: #ffffff;
            color: #333333;
        }
        
        QMenuBar::item {
            padding: 6px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        
        QMenu::item {
            padding: 6px 12px;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
            color: white;
        }
        """
    
    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet."""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #555555;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom: 1px solid #2b2b2b;
        }
        
        QTabBar::tab:hover {
            background-color: #4a4a4a;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #999999;
        }
        
        QLineEdit {
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 4px;
            background-color: #3c3c3c;
            color: #ffffff;
        }
        
        QLineEdit:focus {
            border: 2px solid #0078d4;
        }
        
        QListWidget {
            border: 1px solid #555555;
            background-color: #2b2b2b;
            alternate-background-color: #353535;
        }
        
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #404040;
        }
        
        QListWidget::item:selected {
            background-color: #0078d4;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #404040;
        }
        
        QStatusBar {
            background-color: #3c3c3c;
            border-top: 1px solid #555555;
        }
        
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QMenuBar::item {
            padding: 6px 12px;
        }
        
        QMenuBar::item:selected {
            background-color: #404040;
        }
        
        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #555555;
        }
        
        QMenu::item {
            padding: 6px 12px;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
            color: white;
        }
        """
    
    def apply_theme(self, theme: Optional[str] = None) -> None:
        """
        Apply theme to the current application.
        
        Args:
            theme: Theme name ('light' or 'dark'), uses current if None
        """
        if theme is not None:
            # If a specific theme is requested, set it
            if theme == "light":
                self.set_theme(ThemeType.LIGHT)
            elif theme == "dark":
                self.set_theme(ThemeType.DARK)
        
        # Apply to current QApplication if available
        app = QApplication.instance()
        if app:
            stylesheet = self.get_theme_stylesheet(theme)
            app.setStyleSheet(stylesheet)
    
    def apply_theme_to_application(self, app: QApplication, theme: Optional[str] = None) -> None:
        """
        Apply theme stylesheet to the application.
        
        Args:
            app: QApplication instance
            theme: Theme name ('light' or 'dark'), uses current if None
        """
        stylesheet = self.get_theme_stylesheet(theme)
        app.setStyleSheet(stylesheet)
    
    def stop_monitoring(self) -> None:
        """Stop monitoring theme changes."""
        if self._theme_monitor_timer:
            self._theme_monitor_timer.stop()
            self._theme_monitor_timer = None


# Global instance for easy access
theme_manager = ThemeManager()
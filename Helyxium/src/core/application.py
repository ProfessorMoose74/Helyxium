"""
Helyxium Core Application
Main application class that orchestrates all components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from .. import __version__
from ..detection.hardware import HardwareDetector
from ..detection.platforms import PlatformDetector
from ..localization.detector import LanguageDetector
from ..localization.manager import LocalizationManager
from ..security.auth import AuthenticationManager
from ..ui.main_window import MainWindow
from ..ui.themes import ThemeManager
from ..utils.config import ConfigManager
from ..utils.logging import setup_logging


class HelyxiumApp(QObject):
    """Main Helyxium application class."""

    # Signals
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    vr_hardware_detected = pyqtSignal(dict)
    platform_detected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        # Initialize logging first
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Helyxium application...")

        # Core application components
        self.qt_app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.system_tray: Optional[QSystemTrayIcon] = None

        # Managers and detectors
        self.config_manager = ConfigManager()
        self.language_detector = LanguageDetector()
        self.localization_manager = LocalizationManager()
        self.theme_manager = ThemeManager()
        self.hardware_detector = HardwareDetector()
        self.platform_detector = PlatformDetector()
        self.auth_manager = AuthenticationManager()

        # Detection timers
        self.hardware_check_timer = QTimer()
        self.platform_check_timer = QTimer()

        # Initialize flag
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize all application components."""
        try:
            self.logger.info("Starting application initialization...")

            # Create Qt application
            self.qt_app = QApplication(sys.argv)
            self.qt_app.setApplicationName("Helyxium")
            self.qt_app.setApplicationVersion(__version__)
            self.qt_app.setOrganizationName("Helyxium")
            self.qt_app.setOrganizationDomain("helyxium.com")

            # Set application icon
            logo_path = str(
                Path(__file__).parent.parent.parent
                / "assets"
                / "icons"
                / "helyxium_logo.png"
            )
            if Path(logo_path).exists():
                self.qt_app.setWindowIcon(QIcon(logo_path))

            # Auto-detect language
            detected_language = self.language_detector.detect_system_language()
            self.logger.info(f"Detected system language: {detected_language}")

            # Initialize localization
            self.localization_manager.initialize(detected_language)
            self.language_changed.emit(detected_language)

            # Auto-detect and apply theme
            detected_theme = self.theme_manager.detect_system_theme()
            self.logger.info(f"Detected system theme: {detected_theme}")
            self.theme_manager.apply_theme(detected_theme)
            self.theme_changed.emit(detected_theme)

            # Create main window
            self.main_window = MainWindow(
                theme_manager=self.theme_manager,
                localization_manager=self.localization_manager,
            )

            # Connect signals
            self._connect_signals()

            # Initialize system tray if available
            if QSystemTrayIcon.isSystemTrayAvailable():
                self._setup_system_tray()

            # Start hardware and platform detection
            self._start_detection_timers()

            # Perform initial detections
            self._perform_initial_detections()

            self._initialized = True
            self.logger.info("Application initialization completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def run(self) -> int:
        """Run the main application event loop."""
        if not self._initialized:
            if not self.initialize():
                self.logger.error("Failed to initialize application")
                return 1

        try:
            # Show main window
            if self.main_window:
                self.main_window.show()
                self.main_window.show_welcome_screen()

            self.logger.info("Starting Qt application event loop...")
            return self.qt_app.exec() if self.qt_app else 1

        except Exception as e:
            self.logger.error(f"Application runtime error: {e}")
            return 1

    def shutdown(self):
        """Clean shutdown of the application."""
        self.logger.info("Shutting down Helyxium application...")

        # Stop detection timers
        if self.hardware_check_timer.isActive():
            self.hardware_check_timer.stop()
        if self.platform_check_timer.isActive():
            self.platform_check_timer.stop()

        # Save configuration
        self.config_manager.save_config()

        # Close main window
        if self.main_window:
            self.main_window.close()

        # Hide system tray
        if self.system_tray:
            self.system_tray.hide()

        self.logger.info("Application shutdown completed")

    def _connect_signals(self):
        """Connect internal signals and slots."""
        # Theme change detection
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        # Hardware detection
        self.hardware_check_timer.timeout.connect(self._check_hardware)

        # Platform detection
        self.platform_check_timer.timeout.connect(self._check_platforms)

        # Application quit
        if self.qt_app:
            self.qt_app.aboutToQuit.connect(self.shutdown)

    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        try:
            self.system_tray = QSystemTrayIcon(self)
            # Set Helyxium logo as system tray icon
            assets_path = Path(__file__).parent.parent.parent / "assets" / "icons"
            tray_icon_paths = [
                assets_path / "helyxium_tray.png",  # Optimized for system tray
                assets_path / "helyxium_small.png",  # Small version fallback
                assets_path / "helyxium_logo.png",  # Original logo fallback
            ]

            icon_set = False
            for icon_path in tray_icon_paths:
                if icon_path.exists():
                    self.system_tray.setIcon(QIcon(str(icon_path)))
                    icon_set = True
                    break

            if not icon_set:
                # Final fallback to default system tray icon
                self.system_tray.setIcon(
                    self.qt_app.style().standardIcon(
                        self.qt_app.style().SP_ComputerIcon
                    )
                )
            self.system_tray.setToolTip("Helyxium - Universal VR Bridge")

            # TODO: Add system tray menu
            self.system_tray.show()

        except Exception as e:
            self.logger.warning(f"Failed to setup system tray: {e}")

    def _start_detection_timers(self):
        """Start periodic hardware and platform detection."""
        # Check for hardware changes every 5 seconds
        self.hardware_check_timer.start(5000)

        # Check for platform changes every 10 seconds
        self.platform_check_timer.start(10000)

    def _perform_initial_detections(self):
        """Perform initial hardware and platform detection."""
        try:
            # Detect VR hardware
            hardware_info = self.hardware_detector.detect_vr_hardware()
            self.logger.info(f"Detected VR hardware: {len(hardware_info)} devices")
            self.vr_hardware_detected.emit(hardware_info)

            # Detect VR platforms
            platform_info = self.platform_detector.detect_vr_platforms()
            self.logger.info(f"Detected VR platforms: {len(platform_info)} platforms")
            self.platform_detected.emit(platform_info)

        except Exception as e:
            self.logger.error(f"Initial detection failed: {e}")

    def _check_hardware(self):
        """Periodic hardware detection check."""
        try:
            hardware_info = self.hardware_detector.detect_vr_hardware()
            # Only emit if there are changes
            if self.hardware_detector.has_hardware_changed():
                self.vr_hardware_detected.emit(hardware_info)

        except Exception as e:
            self.logger.warning(f"Hardware detection check failed: {e}")

    def _check_platforms(self):
        """Periodic platform detection check."""
        try:
            platform_info = self.platform_detector.detect_vr_platforms()
            # Only emit if there are changes
            if self.platform_detector.has_platforms_changed():
                self.platform_detected.emit(platform_info)

        except Exception as e:
            self.logger.warning(f"Platform detection check failed: {e}")

    def _on_theme_changed(self, theme: str):
        """Handle system theme changes."""
        self.logger.info(f"System theme changed to: {theme}")
        self.theme_changed.emit(theme)

        if self.main_window:
            self.main_window.apply_theme(theme)

    @property
    def is_initialized(self) -> bool:
        """Check if application is initialized."""
        return self._initialized

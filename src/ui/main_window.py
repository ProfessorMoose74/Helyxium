"""
Main Window Implementation
Primary application window with tabbed interface for VR platform management.
"""

import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QMenuBar, QMenu, QMessageBox, QPushButton,
    QFrame, QSplitter, QListWidget, QTextEdit, QGridLayout,
    QGroupBox, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap

from .. import __version__
from .themes import ThemeManager
from .logo_3d import create_logo_widget
from ..localization.manager import LocalizationManager, tr
from ..utils.logging import get_logger


class WelcomeWidget(QWidget):
    """Welcome screen widget displayed on first startup with 3D animated logo."""
    
    def __init__(self, localization_manager: LocalizationManager, theme_manager: ThemeManager):
        super().__init__()
        self.localization_manager = localization_manager
        self.theme_manager = theme_manager
        self.logger = get_logger(__name__)
        
        # 3D Logo widget
        self.logo_widget = None
        self._logo_animation_timer = QTimer()
        
        self._setup_ui()
        
        # Connect theme changes
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _setup_ui(self):
        """Setup the welcome screen UI with 3D logo."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # 3D Animated Logo
        self.logo_widget = create_logo_widget(self)
        self.logo_widget.setFixedSize(400, 400)
        
        # Connect animation finished signal
        if hasattr(self.logo_widget, 'animation_finished'):
            self.logo_widget.animation_finished.connect(self._on_logo_animation_finished)
        
        layout.addWidget(self.logo_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Main title with fade-in effect
        title_label = QLabel(tr("app.name"))
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #0078d4; margin: 10px;")
        layout.addWidget(title_label)
        
        # Tagline with elegant styling
        tagline_label = QLabel(tr("app.tagline"))
        tagline_font = QFont()
        tagline_font.setPointSize(16)
        tagline_font.setItalic(True)
        tagline_label.setFont(tagline_font)
        tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline_label.setStyleSheet("color: #666666; margin: 5px;")
        layout.addWidget(tagline_label)
        
        # Description with better formatting
        desc_label = QLabel(tr("app.description"))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #888888; margin: 15px; max-width: 500px;")
        layout.addWidget(desc_label)
        
        # Premium start button
        start_button = QPushButton("Enter Helyxium")
        start_button.setMinimumHeight(50)
        start_button.setMinimumWidth(200)
        start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078d4, stop:1 #106ebe);
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #106ebe, stop:1 #005a9e);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #005a9e, stop:1 #004578);
            }
        """)
        start_button.clicked.connect(self._on_get_started)
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
    
    def showEvent(self, event):
        """Start logo animation when widget is shown."""
        super().showEvent(event)
        if self.logo_widget and hasattr(self.logo_widget, 'start_animation'):
            # Update theme colors first
            is_dark = self.theme_manager.is_dark_theme()
            self.logo_widget.set_theme_colors(is_dark)
            
            # Start the animation
            self.logo_widget.start_animation()
            
            self.logger.info("Started 3D logo animation")
    
    def hideEvent(self, event):
        """Stop logo animation when widget is hidden."""
        super().hideEvent(event)
        if self.logo_widget and hasattr(self.logo_widget, 'stop_animation'):
            self.logo_widget.stop_animation()
    
    def _on_theme_changed(self, theme: str):
        """Update logo colors when theme changes."""
        if self.logo_widget and hasattr(self.logo_widget, 'set_theme_colors'):
            is_dark = theme == "dark"
            self.logo_widget.set_theme_colors(is_dark)
    
    def _on_logo_animation_finished(self):
        """Handle logo animation completion."""
        self.logger.info("Logo animation completed")
    
    def _on_get_started(self):
        """Handle get started button click."""
        self.logger.info("User clicked Enter Helyxium button")
        
        # Stop logo animation
        if self.logo_widget and hasattr(self.logo_widget, 'stop_animation'):
            self.logo_widget.stop_animation()
        
        self.hide()


class DashboardWidget(QWidget):
    """Dashboard widget showing system status and quick actions."""
    
    def __init__(self, localization_manager: LocalizationManager):
        super().__init__()
        self.localization_manager = localization_manager
        self.logger = get_logger(__name__)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dashboard UI."""
        layout = QVBoxLayout(self)
        
        # Welcome section
        welcome_label = QLabel(tr("ui.dashboard.welcome"))
        welcome_font = QFont()
        welcome_font.setPointSize(18)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        layout.addWidget(welcome_label)
        
        # Main content in grid
        grid_layout = QGridLayout()
        
        # System Status
        status_group = QGroupBox(tr("ui.dashboard.status"))
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel(tr("messages.connecting"))
        status_layout.addWidget(self.status_label)
        
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 0)  # Indeterminate progress
        status_layout.addWidget(self.status_progress)
        
        grid_layout.addWidget(status_group, 0, 0)
        
        # Connected Platforms
        platforms_group = QGroupBox(tr("ui.dashboard.connected_platforms"))
        platforms_layout = QVBoxLayout(platforms_group)
        
        self.platforms_list = QListWidget()
        self.platforms_list.addItem(tr("messages.loading"))
        platforms_layout.addWidget(self.platforms_list)
        
        grid_layout.addWidget(platforms_group, 0, 1)
        
        # Recent Worlds
        worlds_group = QGroupBox(tr("ui.dashboard.recent_worlds"))
        worlds_layout = QVBoxLayout(worlds_group)
        
        self.worlds_list = QListWidget()
        self.worlds_list.addItem(tr("messages.loading"))
        worlds_layout.addWidget(self.worlds_list)
        
        grid_layout.addWidget(worlds_group, 1, 0)
        
        # Quick Actions
        actions_group = QGroupBox(tr("ui.dashboard.quick_actions"))
        actions_layout = QVBoxLayout(actions_group)
        
        refresh_btn = QPushButton(tr("buttons.refresh"))
        refresh_btn.clicked.connect(self._refresh_dashboard)
        actions_layout.addWidget(refresh_btn)
        
        connect_btn = QPushButton(tr("buttons.connect"))
        connect_btn.clicked.connect(self._quick_connect)
        actions_layout.addWidget(connect_btn)
        
        actions_layout.addStretch()
        
        grid_layout.addWidget(actions_group, 1, 1)
        
        layout.addLayout(grid_layout)
        layout.addStretch()
    
    def update_status(self, status: str):
        """Update the system status."""
        self.status_label.setText(status)
        if status == tr("messages.connected"):
            self.status_progress.setRange(0, 1)
            self.status_progress.setValue(1)
    
    def update_platforms(self, platforms: Dict[str, Any]):
        """Update the connected platforms list."""
        self.platforms_list.clear()
        for platform, info in platforms.items():
            status = tr("messages.connected") if info.get("connected") else tr("messages.disconnected")
            self.platforms_list.addItem(f"{platform}: {status}")
    
    def update_worlds(self, worlds: list):
        """Update the recent worlds list."""
        self.worlds_list.clear()
        if not worlds:
            self.worlds_list.addItem(tr("messages.loading"))
        else:
            for world in worlds:
                self.worlds_list.addItem(world.get("name", "Unknown World"))
    
    def _refresh_dashboard(self):
        """Refresh dashboard data."""
        self.logger.info("Refreshing dashboard")
        self.status_label.setText(tr("messages.loading"))
        # TODO: Trigger actual refresh
    
    def _quick_connect(self):
        """Quick connect to available platforms."""
        self.logger.info("Quick connect requested")
        # TODO: Implement quick connect


class PlatformsWidget(QWidget):
    """Widget for managing VR platform connections."""
    
    def __init__(self, localization_manager: LocalizationManager):
        super().__init__()
        self.localization_manager = localization_manager
        self.logger = get_logger(__name__)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the platforms management UI."""
        layout = QVBoxLayout(self)
        
        title_label = QLabel(tr("ui.platforms.title"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Platform list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - platform list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        connected_group = QGroupBox(tr("ui.platforms.connected"))
        connected_layout = QVBoxLayout(connected_group)
        self.connected_platforms = QListWidget()
        connected_layout.addWidget(self.connected_platforms)
        list_layout.addWidget(connected_group)
        
        available_group = QGroupBox(tr("ui.platforms.available"))
        available_layout = QVBoxLayout(available_group)
        self.available_platforms = QListWidget()
        available_layout.addWidget(self.available_platforms)
        
        # Platform action buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton(tr("ui.platforms.connect"))
        self.disconnect_btn = QPushButton(tr("ui.platforms.disconnect"))
        self.configure_btn = QPushButton(tr("ui.platforms.configure"))
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addWidget(self.configure_btn)
        
        available_layout.addLayout(button_layout)
        list_layout.addWidget(available_group)
        
        splitter.addWidget(list_widget)
        
        # Right side - platform details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        details_title = QLabel("Platform Details")
        details_title.setFont(title_font)
        details_layout.addWidget(details_title)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)


class SettingsWidget(QWidget):
    """Settings and configuration widget."""
    
    def __init__(self, localization_manager: LocalizationManager, theme_manager: ThemeManager):
        super().__init__()
        self.localization_manager = localization_manager
        self.theme_manager = theme_manager
        self.logger = get_logger(__name__)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the settings UI."""
        layout = QVBoxLayout(self)
        
        title_label = QLabel(tr("ui.settings.title"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Settings tabs
        settings_tabs = QTabWidget()
        
        # General settings
        general_widget = QWidget()
        general_layout = QVBoxLayout(general_widget)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        theme_auto_btn = QPushButton("Auto (System)")
        theme_light_btn = QPushButton("Light")
        theme_dark_btn = QPushButton("Dark")
        
        theme_layout.addWidget(theme_auto_btn)
        theme_layout.addWidget(theme_light_btn)
        theme_layout.addWidget(theme_dark_btn)
        theme_layout.addStretch()
        
        general_layout.addWidget(theme_group)
        general_layout.addStretch()
        
        settings_tabs.addTab(general_widget, tr("ui.settings.general"))
        
        # Platform settings
        platforms_widget = QWidget()
        settings_tabs.addTab(platforms_widget, tr("ui.settings.platforms"))
        
        # Security settings
        security_widget = QWidget()
        settings_tabs.addTab(security_widget, tr("ui.settings.security"))
        
        # Privacy settings
        privacy_widget = QWidget()
        settings_tabs.addTab(privacy_widget, tr("ui.settings.privacy"))
        
        layout.addWidget(settings_tabs)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""
    
    # Signals
    closing = pyqtSignal()
    vr_hardware_changed = pyqtSignal(dict)
    platform_status_changed = pyqtSignal(str, dict)
    
    def __init__(self, theme_manager: ThemeManager, localization_manager: LocalizationManager):
        super().__init__()
        
        self.theme_manager = theme_manager
        self.localization_manager = localization_manager
        self.logger = get_logger(__name__)
        
        # Window state
        self._is_welcome_visible = True
        
        # Child widgets
        self.welcome_widget: Optional[WelcomeWidget] = None
        self.main_tabs: Optional[QTabWidget] = None
        self.dashboard_widget: Optional[DashboardWidget] = None
        self.platforms_widget: Optional[PlatformsWidget] = None
        self.settings_widget: Optional[SettingsWidget] = None
        
        # Status bar widgets
        self.status_label: Optional[QLabel] = None
        self.connection_status: Optional[QLabel] = None
        
        self._setup_ui()
        self._connect_signals()
        
        # Apply initial theme
        self.apply_theme(self.theme_manager.get_current_theme())
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle(tr("ui.main_window.title"))
        self.setMinimumSize(QSize(1000, 700))
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Welcome widget (shown initially)
        self.welcome_widget = WelcomeWidget(self.localization_manager, self.theme_manager)
        main_layout.addWidget(self.welcome_widget)
        
        # Main tabs (hidden initially)
        self.main_tabs = QTabWidget()
        self.main_tabs.hide()
        
        # Dashboard tab
        self.dashboard_widget = DashboardWidget(self.localization_manager)
        self.main_tabs.addTab(self.dashboard_widget, tr("ui.main_window.tabs.dashboard"))
        
        # Platforms tab
        self.platforms_widget = PlatformsWidget(self.localization_manager)
        self.main_tabs.addTab(self.platforms_widget, tr("ui.main_window.tabs.platforms"))
        
        # Worlds tab
        worlds_widget = QWidget()
        self.main_tabs.addTab(worlds_widget, tr("ui.main_window.tabs.worlds"))
        
        # Social tab
        social_widget = QWidget()
        self.main_tabs.addTab(social_widget, tr("ui.main_window.tabs.social"))
        
        # Settings tab
        self.settings_widget = SettingsWidget(self.localization_manager, self.theme_manager)
        self.main_tabs.addTab(self.settings_widget, tr("ui.main_window.tabs.settings"))
        
        main_layout.addWidget(self.main_tabs)
        
        # Setup menu bar
        self._setup_menu_bar()
        
        # Setup status bar
        self._setup_status_bar()
    
    def _setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(tr("ui.main_window.menu.file"))
        
        exit_action = QAction(tr("buttons.close"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu(tr("ui.main_window.menu.view"))
        
        dashboard_action = QAction(tr("ui.main_window.tabs.dashboard"), self)
        dashboard_action.triggered.connect(lambda: self.main_tabs.setCurrentIndex(0))
        view_menu.addAction(dashboard_action)
        
        platforms_action = QAction(tr("ui.main_window.tabs.platforms"), self)
        platforms_action.triggered.connect(lambda: self.main_tabs.setCurrentIndex(1))
        view_menu.addAction(platforms_action)
        
        # Tools menu
        tools_menu = menubar.addMenu(tr("ui.main_window.menu.tools"))
        
        refresh_action = QAction(tr("buttons.refresh"), self)
        refresh_action.triggered.connect(self._refresh_all)
        tools_menu.addAction(refresh_action)
        
        settings_action = QAction(tr("ui.settings.title"), self)
        settings_action.triggered.connect(lambda: self.main_tabs.setCurrentIndex(4))
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu(tr("ui.main_window.menu.help"))
        
        about_action = QAction("About Helyxium", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        status_bar = self.statusBar()
        
        # Main status label
        self.status_label = QLabel(tr("messages.loading"))
        status_bar.addWidget(self.status_label)
        
        # Connection status
        status_bar.addPermanentWidget(QLabel("|"))
        self.connection_status = QLabel(tr("messages.disconnected"))
        status_bar.addPermanentWidget(self.connection_status)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.theme_manager.theme_changed.connect(self.apply_theme)
        
        if self.welcome_widget:
            # Connect welcome widget hide to show main interface
            def on_welcome_hidden():
                self.show_main_interface()
            
            # Since welcome widget doesn't have a built-in hide signal,
            # we'll use a timer to check
            self._welcome_timer = QTimer()
            self._welcome_timer.timeout.connect(self._check_welcome_visibility)
            self._welcome_timer.start(100)
    
    def _check_welcome_visibility(self):
        """Check if welcome widget is still visible."""
        if self.welcome_widget and not self.welcome_widget.isVisible() and self._is_welcome_visible:
            self._is_welcome_visible = False
            self.show_main_interface()
            self._welcome_timer.stop()
    
    def show_welcome_screen(self):
        """Show the welcome screen."""
        if self.welcome_widget and self.main_tabs:
            self.welcome_widget.show()
            self.main_tabs.hide()
            self._is_welcome_visible = True
            self.logger.info("Showing welcome screen")
    
    def show_main_interface(self):
        """Show the main tabbed interface."""
        if self.welcome_widget and self.main_tabs:
            self.welcome_widget.hide()
            self.main_tabs.show()
            self._is_welcome_visible = False
            self.logger.info("Showing main interface")
    
    def apply_theme(self, theme: str):
        """Apply theme to the window."""
        try:
            stylesheet = self.theme_manager.get_theme_stylesheet(theme)
            self.setStyleSheet(stylesheet)
            self.logger.debug(f"Applied {theme} theme to main window")
        except Exception as e:
            self.logger.error(f"Failed to apply theme {theme}: {e}")
    
    def update_status(self, message: str):
        """Update the main status message."""
        if self.status_label:
            self.status_label.setText(message)
    
    def update_connection_status(self, status: str):
        """Update the connection status."""
        if self.connection_status:
            self.connection_status.setText(status)
    
    def update_dashboard_data(self, platforms: Dict[str, Any], worlds: list):
        """Update dashboard with latest data."""
        if self.dashboard_widget:
            self.dashboard_widget.update_platforms(platforms)
            self.dashboard_widget.update_worlds(worlds)
            self.dashboard_widget.update_status(tr("messages.connected"))
    
    def _refresh_all(self):
        """Refresh all data in the application."""
        self.logger.info("Refreshing all application data")
        self.update_status(tr("messages.loading"))
        # TODO: Trigger actual refresh of all components
    
    def _show_about(self):
        """Show about dialog."""
        about_text = f"""
        <h2>{tr("app.name")}</h2>
        <p>{tr("app.tagline")}</p>
        <p>{tr("app.description")}</p>
        <p>Version: {__version__}</p>
        """

        QMessageBox.about(self, "About Helyxium", about_text)
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Main window closing")
        self.closing.emit()
        event.accept()
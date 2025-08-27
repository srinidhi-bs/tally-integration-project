"""
TallyPrime Integration Manager - Main Window
Professional Desktop Application using PySide6/Qt6

This module contains the main application window that provides the primary
user interface for the TallyPrime Integration Manager. It demonstrates
professional Qt6 GUI development patterns and best practices.

Key Learning Points:
- QMainWindow: Professional application window with menu, toolbar, status bar
- Layout management and widget organization
- Signal-slot connections for event handling
- Professional UI design patterns

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
"""

import logging
from typing import Optional

# PySide6/Qt6 imports for GUI components
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QStatusBar, QMenuBar, QMenu, QToolBar,
    QSizePolicy, QSplitter, QDockWidget, QTextEdit, QPushButton,
    QFrame, QGroupBox
)

# Import our professional connection widget
from .widgets.connection_widget import ConnectionWidget

from PySide6.QtCore import QSettings, Signal, Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QFont

# Import TallyPrime integration components
from core.tally.connector import TallyConnector, TallyConnectionConfig
from app.settings import SettingsManager


class MainWindow(QMainWindow):
    """
    Main Application Window - Primary User Interface
    
    This class creates the main window that users interact with. It demonstrates:
    - Professional window layout with menu bar, toolbar, and status bar
    - Proper widget organization and layout management
    - Event handling through Qt's signal-slot mechanism
    - Settings persistence and window state management
    
    Learning Points:
    - QMainWindow provides the framework for professional desktop applications
    - Central widget contains the main content area
    - Dock widgets provide resizable, movable panels
    - Status bar shows application status and information
    """
    
    # Custom signals for communication with other components
    # Signals are Qt's way of implementing the Observer pattern
    closing = Signal()  # Emitted when window is about to close
    
    def __init__(self, config: dict, settings: QSettings):
        """
        Initialize the main application window.
        
        Args:
            config: Application configuration dictionary
            settings: QSettings object for persistent storage
            
        Learning: Main window should receive its configuration, not load it directly
        """
        super().__init__()  # Initialize the QMainWindow parent class
        
        # Store configuration and settings
        self.config = config
        self.settings = settings
        
        # Set up logging for this class
        self.logger = logging.getLogger(__name__)
        
        # Window components (will be created in setup methods)
        self.central_widget: Optional[QWidget] = None
        self.status_bar: Optional[QStatusBar] = None
        self.menu_bar: Optional[QMenuBar] = None
        
        # Dock widgets for professional panel layout
        self.control_panel_dock: Optional[QDockWidget] = None
        self.log_panel_dock: Optional[QDockWidget] = None
        
        # TallyPrime integration components
        self.tally_connector: Optional[TallyConnector] = None
        self.settings_manager: Optional[SettingsManager] = None
        self.connection_widget: Optional[ConnectionWidget] = None
        
        # Initialize the window
        self._setup_window_properties()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_dock_widgets()
        self._create_status_bar()
        self._setup_tally_integration()
        self._restore_window_state()
        
        self.logger.info("Main window initialized successfully")
    
    def _setup_window_properties(self):
        """
        Set up basic window properties like title, size, and icon.
        
        Learning: Window properties should be set before creating other components
        """
        # Set window title from configuration
        window_title = self.config.get('application', {}).get('window_title', 
                                                             'TallyPrime Integration Manager')
        self.setWindowTitle(window_title)
        
        # Set default window size from configuration
        ui_config = self.config.get('ui_settings', {})
        default_width = ui_config.get('window_width', 1200)
        default_height = ui_config.get('window_height', 800)
        self.resize(default_width, default_height)
        
        # Set minimum window size to ensure usability
        self.setMinimumSize(800, 600)
        
        # Enable window state persistence
        # This allows Qt to remember window position and size
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.logger.info(f"Window properties set: {window_title} ({default_width}x{default_height})")
    
    def _create_menu_bar(self):
        """
        Create the application menu bar with standard menus.
        
        Learning: Professional applications should have comprehensive menu systems
        """
        # Get the menu bar (QMainWindow creates it automatically)
        self.menu_bar = self.menuBar()
        
        # Create File menu
        file_menu = self.menu_bar.addMenu("&File")
        
        # Add File menu actions
        # &N creates Alt+N keyboard shortcut, Ctrl+N is the standard shortcut
        new_action = QAction("&New Connection", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.setStatusTip("Create a new TallyPrime connection")
        new_action.triggered.connect(self._on_new_connection)
        file_menu.addAction(new_action)
        
        # Separator creates a visual divider in the menu
        file_menu.addSeparator()
        
        # Exit action with standard shortcut
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create View menu
        view_menu = self.menu_bar.addMenu("&View")
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.setStatusTip("Refresh data from TallyPrime")
        refresh_action.triggered.connect(self._on_refresh)
        view_menu.addAction(refresh_action)
        
        # Add separator before panel toggles
        view_menu.addSeparator()
        
        # Panel visibility actions (will be connected after dock widgets are created)
        self.control_panel_action = QAction("&Control Panel", self)
        self.control_panel_action.setCheckable(True)
        self.control_panel_action.setChecked(True)
        self.control_panel_action.setStatusTip("Show/hide the control panel")
        view_menu.addAction(self.control_panel_action)
        
        self.log_panel_action = QAction("&Log Panel", self)
        self.log_panel_action.setCheckable(True)
        self.log_panel_action.setChecked(True)
        self.log_panel_action.setStatusTip("Show/hide the log panel")
        view_menu.addAction(self.log_panel_action)
        
        # Create Tools menu
        tools_menu = self.menu_bar.addMenu("&Tools")
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)
        
        # Create Help menu
        help_menu = self.menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
        self.logger.info("Menu bar created with File, View, Tools, and Help menus")
    
    def _create_toolbar(self):
        """
        Create a toolbar with commonly used actions.
        
        Learning: Toolbars provide quick access to frequently used functions
        """
        # Create main toolbar
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(True)  # Allow users to move the toolbar
        
        # Add toolbar actions (these would have icons in a real application)
        connect_action = QAction("Connect", self)
        connect_action.setStatusTip("Test TallyPrime connection")
        connect_action.triggered.connect(self._on_test_connection)
        toolbar.addAction(connect_action)
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh data from TallyPrime")
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)
        
        self.logger.info("Toolbar created with connection and refresh actions")
    
    def _create_central_widget(self):
        """
        Create the central widget that contains the main application content.
        
        With dock widgets, the central widget focuses on the main data display area.
        The control and log panels will be implemented as dockable widgets.
        
        Learning: QMainWindow's central widget should contain the primary content,
        while secondary features use dock widgets for better user customization.
        """
        # Create the central widget container
        self.central_widget = self._create_main_content_area()
        self.setCentralWidget(self.central_widget)
        
        self.logger.info("Central widget created for main content display")
    
    def _create_dock_widgets(self):
        """
        Create professional dockable panels for the application.
        
        This method creates:
        1. Control Panel - Connection management and operation controls
        2. Log Panel - Real-time logging and status information
        
        Learning Points:
        - QDockWidget provides movable, resizable panels
        - Dock widgets can be floated, tabbed, and repositioned by users
        - Professional applications use dock widgets for customizable layouts
        """
        # Create Control Panel Dock Widget
        self.control_panel_dock = QDockWidget("Control Panel", self)
        self.control_panel_dock.setObjectName("ControlPanelDock")  # Important for state saving
        
        # Create the professional connection widget
        self.connection_widget = ConnectionWidget()
        self.control_panel_dock.setWidget(self.connection_widget)
        
        # Connect connection widget signals to main window handlers
        self.connection_widget.connection_test_requested.connect(self._on_test_connection)
        self.connection_widget.settings_dialog_requested.connect(self._on_settings)
        self.connection_widget.refresh_data_requested.connect(self._on_refresh)
        
        # Set dock widget properties
        self.control_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.control_panel_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetClosable | 
            QDockWidget.DockWidgetFloatable
        )
        
        # Add to main window (left side)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.control_panel_dock)
        
        # Create Log Panel Dock Widget
        self.log_panel_dock = QDockWidget("Operations Log", self)
        self.log_panel_dock.setObjectName("LogPanelDock")  # Important for state saving
        
        # Create the log panel content
        log_panel_content = self._create_log_panel_content()
        self.log_panel_dock.setWidget(log_panel_content)
        
        # Set dock widget properties
        self.log_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.log_panel_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetClosable | 
            QDockWidget.DockWidgetFloatable
        )
        
        # Add to main window (right side)
        self.addDockWidget(Qt.RightDockWidgetArea, self.log_panel_dock)
        
        # Connect dock widget visibility to menu actions
        self._connect_dock_widget_actions()
        
        self.logger.info("Dock widgets created: Control Panel (left) and Log Panel (right)")
    
    def _setup_tally_integration(self):
        """
        Set up TallyPrime integration components
        
        This method initializes:
        - SettingsManager for configuration management
        - TallyConnector for TallyPrime communication
        - Integration with the connection widget
        
        Learning: Separating initialization logic improves code organization
        """
        try:
            # Initialize settings manager
            self.settings_manager = SettingsManager()
            
            # Get connection configuration from settings
            connection_config = self.settings_manager.connection_config
            
            # Initialize TallyConnector with configuration
            self.tally_connector = TallyConnector(connection_config)
            
            # Connect TallyConnector to connection widget
            if self.connection_widget:
                self.connection_widget.set_tally_connector(self.tally_connector)
                self.connection_widget.set_settings_manager(self.settings_manager)
            
            # Connect TallyConnector signals to main window
            self.tally_connector.connection_status_changed.connect(self._on_tally_status_changed)
            self.tally_connector.company_info_received.connect(self._on_company_info_received)
            self.tally_connector.error_occurred.connect(self._on_tally_error)
            
            self.logger.info("TallyPrime integration components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TallyPrime integration: {str(e)}")
    
    
    def _create_log_panel_content(self) -> QWidget:
        """
        Create the content for the log panel dock widget.
        
        This panel contains:
        - Real-time operation logging
        - Status messages and updates
        - Error reporting and debugging information
        
        Returns:
            QWidget: Configured log panel content
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Log header
        header_label = QLabel("Live Operations Log")
        header_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 4px;")
        layout.addWidget(header_label)
        
        # Log display area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        # Note: QTextEdit doesn't have setMaximumBlockCount, we'll manage log size manually
        
        # Style the log display
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                padding: 4px;
            }
        """)
        
        # Add some initial log entries
        self._add_log_entry("🔗 Application started - TallyPrime Integration Manager", "info")
        self._add_log_entry("📊 Waiting for TallyPrime connection...", "info")
        self._add_log_entry("⚡ System ready for operations", "success")
        
        layout.addWidget(self.log_display)
        
        return widget
    
    def _create_main_content_area(self) -> QWidget:
        """
        Create the main content area for the central widget.
        
        This area will contain:
        - Data tables and visualizations
        - Form inputs and data entry
        - Primary application content
        
        Returns:
            QWidget: Main content area widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Main content placeholder
        content_label = QLabel("Main Content Area")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                padding: 40px;
                margin: 20px;
            }
        """)
        
        desc_label = QLabel(
            "TallyPrime data tables, forms, and visualizations will appear here.\n\n"
            "• Ledger listings with professional tables\n"
            "• Balance sheets and financial reports\n"
            "• Data entry forms for vouchers\n"
            "• Real-time data operations"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #6c757d; font-size: 12px; margin: 10px;")
        
        layout.addWidget(content_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        
        return widget
    
    def _connect_dock_widget_actions(self):
        """
        Connect dock widget visibility to menu actions.
        
        Learning: This creates bidirectional sync between menu checkboxes
        and dock widget visibility state.
        """
        # Control Panel visibility sync
        self.control_panel_action.triggered.connect(
            lambda checked: self.control_panel_dock.setVisible(checked)
        )
        self.control_panel_dock.visibilityChanged.connect(
            self.control_panel_action.setChecked
        )
        
        # Log Panel visibility sync
        self.log_panel_action.triggered.connect(
            lambda checked: self.log_panel_dock.setVisible(checked)
        )
        self.log_panel_dock.visibilityChanged.connect(
            self.log_panel_action.setChecked
        )
    
    def _add_log_entry(self, message: str, level: str = "info"):
        """
        Add an entry to the log display with timestamp and styling.
        
        Args:
            message: Log message to display
            level: Log level (info, success, warning, error)
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on log level
        colors = {
            "info": "#3498db",      # Blue
            "success": "#27ae60",   # Green  
            "warning": "#f39c12",   # Orange
            "error": "#e74c3c"      # Red
        }
        
        color = colors.get(level, "#ecf0f1")
        
        formatted_entry = f'<span style="color: {color}">{timestamp} - {message}</span>'
        self.log_display.append(formatted_entry)
        
        # Auto-scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
    
    def _create_placeholder_panel(self, title: str, description: str) -> QWidget:
        """
        Create a placeholder panel with title and description.
        
        Args:
            title: Panel title
            description: Panel description text
            
        Returns:
            QWidget: Configured placeholder panel
            
        Learning: Helper methods make code more organized and reusable
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create title label with larger font
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Create description label
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)  # Allow text to wrap to multiple lines
        
        # Add labels to layout
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        # Add stretch to center the content vertically
        layout.addStretch()
        
        # Set panel styling
        panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 4px;
            }
            QLabel {
                border: none;
                padding: 8px;
            }
        """)
        
        return panel
    
    def _create_status_bar(self):
        """
        Create the status bar that shows application status and information.
        
        Learning: Status bars provide important feedback to users about application state
        """
        self.status_bar = self.statusBar()
        
        # Show initial status message
        self.status_bar.showMessage("Ready - TallyPrime Integration Manager initialized")
        
        # Add permanent status indicators (these stay visible on the right side)
        connection_label = QLabel("Status: Not Connected")
        self.status_bar.addPermanentWidget(connection_label)
        
        self.logger.info("Status bar created with connection status")
    
    def _restore_window_state(self):
        """
        Restore window position and state from previous session.
        
        Learning: Professional applications remember user preferences between sessions
        """
        # Only restore if the user wants us to remember window position
        if self.config.get('ui_settings', {}).get('remember_window_position', True):
            # Restore window geometry (position and size)
            geometry = self.settings.value("window_geometry")
            if geometry:
                self.restoreGeometry(geometry)
                
            # Restore window state (maximized, toolbars, etc.)
            state = self.settings.value("window_state")
            if state:
                self.restoreState(state)
                
            self.logger.info("Window state restored from previous session")
    
    def closeEvent(self, event):
        """
        Handle window close event - called when user tries to close the window.
        
        Args:
            event: QCloseEvent object
            
        Learning: closeEvent() is automatically called by Qt when window closes
        """
        self.logger.info("Window close event received")
        
        # Save window state for next session
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        
        # Emit our custom signal to notify other components
        self.closing.emit()
        
        # Accept the close event (allow window to close)
        event.accept()
        
        self.logger.info("Window state saved and close event accepted")
    
    # Menu and toolbar action handlers
    # These methods will be expanded in later development phases
    
    def _on_new_connection(self):
        """Handle New Connection menu action."""
        self.status_bar.showMessage("New Connection action triggered")
        self.logger.info("New Connection action triggered")
    
    def _on_refresh(self):
        """Handle Refresh menu action."""
        self.status_bar.showMessage("Refresh action triggered")
        self.logger.info("Refresh action triggered")
    
    def _on_settings(self):
        """Handle Settings menu action."""
        self.status_bar.showMessage("Settings action triggered")
        self.logger.info("Settings action triggered")
    
    def _on_about(self):
        """Handle About menu action."""
        self.status_bar.showMessage("About action triggered")
        self.logger.info("About action triggered")
    
    def _on_test_connection(self):
        """Handle Test Connection action from toolbar or connection widget."""
        self.status_bar.showMessage("Testing TallyPrime connection...")
        self.logger.info("Test Connection action triggered")
        self._add_log_entry("🔍 Testing TallyPrime connection...", "info")
        
        # If we have a TallyConnector, use it for the test
        if self.tally_connector:
            self.tally_connector.test_connection()
        else:
            self.logger.warning("TallyConnector not available for connection test")
            self._add_log_entry("⚠ TallyConnector not initialized", "warning")
    
    # New action handlers for control panel buttons
    
    def _on_view_ledgers(self):
        """Handle View Ledgers action."""
        self.status_bar.showMessage("Loading ledger data from TallyPrime...")
        self.logger.info("View Ledgers action triggered")
        self._add_log_entry("📋 Loading ledger data from TallyPrime...", "info")
    
    def _on_balance_sheet(self):
        """Handle Balance Sheet action."""
        self.status_bar.showMessage("Generating balance sheet report...")
        self.logger.info("Balance Sheet action triggered")
        self._add_log_entry("📊 Generating balance sheet report...", "info")
    
    def _on_export_data(self):
        """Handle Export Data action."""
        self.status_bar.showMessage("Preparing data export...")
        self.logger.info("Export Data action triggered")
        self._add_log_entry("💾 Preparing data export...", "info")
    
    # TallyPrime integration signal handlers
    
    def _on_tally_status_changed(self, status, message: str = ""):
        """
        Handle TallyPrime connection status changes
        
        Args:
            status: Connection status
            message: Status message
        """
        # Update status bar with connection information
        if hasattr(status, 'value'):
            status_text = f"TallyPrime: {status.value.title()}"
        else:
            status_text = f"TallyPrime: {str(status)}"
        
        if message:
            status_text += f" - {message}"
        
        self.status_bar.showMessage(status_text)
        
        # Add log entry
        log_message = f"🔗 Connection status: {status_text}"
        log_level = "success" if "connected" in status_text.lower() else "info"
        self._add_log_entry(log_message, log_level)
        
        self.logger.info(f"TallyPrime status changed: {status}")
    
    def _on_company_info_received(self, company_info):
        """
        Handle company information received from TallyPrime
        
        Args:
            company_info: Company information object
        """
        company_name = getattr(company_info, 'name', 'Unknown Company')
        message = f"📊 Company info received: {company_name}"
        
        self._add_log_entry(message, "success")
        self.status_bar.showMessage(f"Connected to {company_name}")
        
        self.logger.info(f"Company information received: {company_name}")
    
    def _on_tally_error(self, error_type: str, error_message: str):
        """
        Handle TallyPrime connection errors
        
        Args:
            error_type: Type of error
            error_message: Error message
        """
        error_text = f"⚠ TallyPrime Error: {error_message}"
        
        self._add_log_entry(error_text, "error")
        self.status_bar.showMessage(f"Error: {error_message}")
        
        self.logger.error(f"TallyPrime error: {error_type} - {error_message}")
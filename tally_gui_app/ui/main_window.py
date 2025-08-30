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

# Import our professional widgets
from .widgets.connection_widget import ConnectionWidget
from .widgets.data_table_widget import ProfessionalDataTableWidget
from .widgets.log_widget import ProfessionalLogWidget
from .widgets.progress_widget import ProgressWidget
from .dialogs.connection_dialog import ConnectionDialog
from .dialogs.voucher_dialog import VoucherEntryDialog

from PySide6.QtCore import QSettings, Signal, Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QFont

# Import TallyPrime integration components
from core.tally.connector import TallyConnector, TallyConnectionConfig
from core.tally.data_reader import TallyDataReader
from core.models.ledger_model import LedgerInfo, LedgerBalance, LedgerType
from app.settings import SettingsManager

# Import threading framework for responsive UI
from core.utils.threading_utils import (
    TaskManager, DataLoadWorker, TaskStatus, TaskResult, TaskProgress,
    create_task_manager, create_data_load_task
)


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
        self.data_reader: Optional[TallyDataReader] = None
        self.settings_manager: Optional[SettingsManager] = None
        self.connection_widget: Optional[ConnectionWidget] = None
        self.log_widget: Optional[ProfessionalLogWidget] = None
        
        # Threading framework components for responsive UI
        self.task_manager: Optional[TaskManager] = None
        self.progress_widget: Optional[ProgressWidget] = None
        self.progress_dock: Optional[QDockWidget] = None
        
        # Initialize the window
        self._setup_window_properties()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_dock_widgets()
        self._create_status_bar()
        self._setup_tally_integration()
        self._setup_threading_framework()
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
        
        self.progress_panel_action = QAction("&Progress Panel", self)
        self.progress_panel_action.setCheckable(True)
        self.progress_panel_action.setChecked(True)
        self.progress_panel_action.setStatusTip("Show/hide the background tasks progress panel")
        view_menu.addAction(self.progress_panel_action)
        
        # Create Tools menu
        tools_menu = self.menu_bar.addMenu("&Tools")
        
        # Add voucher entry actions
        new_voucher_action = QAction("&New Voucher", self)
        new_voucher_action.setShortcut(QKeySequence("Ctrl+N"))
        new_voucher_action.setStatusTip("Create a new voucher entry")
        new_voucher_action.triggered.connect(self._on_new_voucher)
        tools_menu.addAction(new_voucher_action)
        
        tools_menu.addSeparator()
        
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
        
        # Connect data operation signals to load different data types
        self.connection_widget.load_ledgers_requested.connect(self._on_load_ledgers)
        self.connection_widget.load_balance_sheet_requested.connect(self._on_load_balance_sheet)
        self.connection_widget.load_recent_transactions_requested.connect(self._on_load_recent_transactions)
        
        # Connect voucher entry signals
        self.connection_widget.new_voucher_requested.connect(self._on_new_voucher)
        self.connection_widget.edit_voucher_requested.connect(self._on_edit_voucher)
        
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
        
        # Create Progress Panel Dock Widget for background task tracking
        self.progress_dock = QDockWidget("Background Tasks", self)
        self.progress_dock.setObjectName("ProgressPanelDock")  # Important for state saving
        
        # Create the progress widget
        self.progress_widget = ProgressWidget()
        self.progress_dock.setWidget(self.progress_widget)
        
        # Set dock widget properties
        self.progress_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.progress_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetClosable | 
            QDockWidget.DockWidgetFloatable
        )
        
        # Add to main window (bottom area)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.progress_dock)
        
        # Connect dock widget visibility to menu actions
        self._connect_dock_widget_actions()
        
        self.logger.info("Dock widgets created: Control Panel (left), Log Panel (right), and Progress Panel (bottom)")
    
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
            
            # Initialize TallyDataReader with the connector
            self.data_reader = TallyDataReader(self.tally_connector)
            
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
    
    def _setup_threading_framework(self):
        """
        Set up the threading framework for responsive UI operations
        
        This method initializes:
        - TaskManager for centralized thread management
        - Progress widget integration for task monitoring
        - Signal connections for background operations
        
        Learning: Threading framework provides professional non-blocking UI
        """
        try:
            # Initialize task manager with optimal thread count
            self.task_manager = create_task_manager(max_threads=4)
            
            # Connect task manager signals to UI components
            self.task_manager.task_added.connect(self._on_task_added)
            self.task_manager.task_started.connect(self._on_task_started)
            self.task_manager.task_completed.connect(self._on_task_completed)
            self.task_manager.task_cancelled.connect(self._on_task_cancelled)
            self.task_manager.task_progress.connect(self._on_task_progress)
            
            # Connect progress widget cancellation requests to task manager
            if self.progress_widget:
                self.progress_widget.cancel_requested.connect(self.task_manager.cancel_task)
            
            self._add_log_entry(
                "🧵 Threading framework initialized - Ready for background operations", 
                "info", 
                "Threading"
            )
            
            self.logger.info("Threading framework initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize threading framework: {str(e)}")
            self._add_log_entry(f"❌ Threading framework initialization failed: {str(e)}", "error")
    
    
    def _create_log_panel_content(self) -> QWidget:
        """
        Create the content for the log panel dock widget.
        
        This panel now contains the advanced ProfessionalLogWidget which provides:
        - Real-time colored operation logging with professional formatting
        - Advanced filtering by log level, content, and time range
        - Professional search functionality with regex support
        - Log export to multiple formats (TXT, CSV, JSON)
        - Log rotation and size management
        - Auto-scroll and manual positioning controls
        - Professional UI with theme integration
        
        Returns:
            ProfessionalLogWidget: Advanced log widget
        """
        # Create the professional log widget
        self.log_widget = ProfessionalLogWidget(self)
        
        # Connect log widget signals for integration
        self.log_widget.log_exported.connect(self._on_log_exported)
        self.log_widget.filter_changed.connect(self._on_log_filter_changed)
        
        # Add some initial application startup log entries
        self.log_widget.add_log_entry(
            "🔗 Application started - TallyPrime Integration Manager", 
            "INFO", 
            "MainWindow"
        )
        self.log_widget.add_log_entry(
            "📊 Waiting for TallyPrime connection...", 
            "INFO", 
            "MainWindow"
        )
        self.log_widget.add_log_entry(
            "⚡ System ready for operations", 
            "INFO", 
            "MainWindow"
        )
        
        return self.log_widget
    
    def _create_main_content_area(self) -> QWidget:
        """
        Create the main content area with professional data table.
        
        This contains the primary application functionality including:
        - Professional data table widget for TallyPrime data display
        - Advanced filtering, sorting, and search capabilities
        - Export functionality to CSV/Excel/PDF formats
        - Real-time data updates with caching integration
        
        Returns:
            ProfessionalDataTableWidget: Main data table widget
        """
        # Create the professional data table widget
        # This replaces the placeholder with our fully functional table
        self.data_table = ProfessionalDataTableWidget()
        
        # Set up initial welcome data to show table structure
        # This helps users understand the interface before connecting to TallyPrime
        from decimal import Decimal
        welcome_ledgers = [
            LedgerInfo(
                name="Welcome to TallyPrime Integration Manager",
                ledger_type=LedgerType.OTHER,
                parent_group_name="System",
                balance=LedgerBalance(opening_balance=Decimal("0"))
            ),
            LedgerInfo(
                name="Connection Instructions",
                ledger_type=LedgerType.OTHER,
                parent_group_name="Help",
                balance=LedgerBalance(opening_balance=Decimal("0"))
            ),
            LedgerInfo(
                name="Data Operations",
                ledger_type=LedgerType.OTHER,
                parent_group_name="Help", 
                balance=LedgerBalance(opening_balance=Decimal("0"))
            )
        ]
        
        # Set the welcome data to show the table structure
        self.data_table.set_ledger_data(welcome_ledgers)
        
        return self.data_table
    
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
        
        # Progress Panel visibility sync
        self.progress_panel_action.triggered.connect(
            lambda checked: self.progress_dock.setVisible(checked)
        )
        self.progress_dock.visibilityChanged.connect(
            self.progress_panel_action.setChecked
        )
    
    def _add_log_entry(self, message: str, level: str = "info", source: str = "MainWindow"):
        """
        Add an entry to the advanced log display with professional formatting.
        
        This method now uses the ProfessionalLogWidget which provides:
        - Professional timestamp and color formatting
        - Thread-safe logging operations
        - Automatic filtering and search integration
        - Export capability and log rotation
        
        Args:
            message: Log message to display
            level: Log level (info, success, warning, error, debug, critical)
            source: Source component generating the log (for organization)
        """
        if self.log_widget:
            # Map legacy level names to standard logging levels
            level_mapping = {
                "info": "INFO",
                "success": "INFO",  # Success messages are INFO level with success indicators
                "warning": "WARNING",
                "error": "ERROR",
                "debug": "DEBUG",
                "critical": "CRITICAL"
            }
            
            mapped_level = level_mapping.get(level.lower(), "INFO")
            
            # Use the professional log widget's advanced logging
            self.log_widget.add_log_entry(message, mapped_level, source)
        else:
            # Fallback to console logging if widget not available
            self.logger.info(f"[{source}] {message}")
    
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
        """
        Handle Settings menu action and connection settings dialog request.
        
        This method creates and shows the professional connection settings dialog
        with all current settings pre-loaded for user modification.
        """
        try:
            # Create connection settings dialog
            dialog = ConnectionDialog(parent=self, settings_manager=self.settings_manager)
            
            # Connect dialog signals to handle configuration changes
            dialog.connection_config_changed.connect(self._on_connection_config_changed)
            
            # Show the dialog modally
            result = dialog.exec()
            
            if result == ConnectionDialog.Accepted:
                self.status_bar.showMessage("Connection settings updated successfully", 3000)
                self.logger.info("Connection settings updated through dialog")
                
                # Update the connection widget with new settings
                if self.connection_widget and self.tally_connector:
                    # Re-initialize TallyConnector with new configuration
                    new_config = self.settings_manager.connection_config
                    self.tally_connector.update_config(new_config)
                    
            else:
                self.status_bar.showMessage("Connection settings dialog cancelled", 2000)
                self.logger.info("Connection settings dialog was cancelled")
                
        except Exception as e:
            self.logger.error(f"Error opening connection settings dialog: {str(e)}")
            self.status_bar.showMessage(f"Error opening settings: {str(e)}", 5000)
    
    def _on_connection_config_changed(self, new_config: TallyConnectionConfig):
        """
        Handle connection configuration changes from the settings dialog.
        
        Args:
            new_config: New TallyPrime connection configuration
        """
        try:
            self.logger.info(f"Connection configuration changed to: {new_config.host}:{new_config.port}")
            
            # Update TallyConnector with new configuration
            if self.tally_connector:
                self.tally_connector.update_config(new_config)
            
            # Log the configuration change
            self._add_log_entry(
                f"🔧 Connection settings updated: {new_config.host}:{new_config.port} "
                f"(timeout: {new_config.timeout}s)", 
                "info"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating connection configuration: {str(e)}")
            self._add_log_entry(f"❌ Error updating connection settings: {str(e)}", "error")
    
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
    
    def _on_load_ledgers(self):
        """Handle Load Ledgers button from connection widget."""
        self.status_bar.showMessage("Loading ledger accounts from TallyPrime...")
        self.logger.info("Load Ledgers action triggered from connection widget")
        self._add_log_entry("📋 Loading ledger accounts from TallyPrime...", "info")
        
        # Load ledger data using data reader and populate the data table
        if hasattr(self, 'data_table') and self.tally_connector:
            self._load_ledger_data()
        else:
            self._add_log_entry("⚠ Data table or TallyConnector not available", "warning")
    
    def _on_load_balance_sheet(self):
        """Handle Load Balance Sheet button from connection widget."""
        self.status_bar.showMessage("Loading balance sheet data from TallyPrime...")
        self.logger.info("Load Balance Sheet action triggered from connection widget")
        self._add_log_entry("📊 Loading balance sheet data from TallyPrime...", "info")
        
        # Load balance sheet data using data reader and populate the data table
        if hasattr(self, 'data_table') and self.tally_connector:
            self._load_balance_sheet_data()
        else:
            self._add_log_entry("⚠ Data table or TallyConnector not available", "warning")
    
    def _on_load_recent_transactions(self):
        """Handle Load Recent Transactions button from connection widget."""
        self.status_bar.showMessage("Loading recent transactions from TallyPrime...")
        self.logger.info("Load Recent Transactions action triggered from connection widget")
        self._add_log_entry("📈 Loading recent transactions from TallyPrime...", "info")
        
        # Load recent transaction data using data reader and populate the data table
        if hasattr(self, 'data_table') and self.tally_connector:
            self._load_transaction_data()
        else:
            self._add_log_entry("⚠ Data table or TallyConnector not available", "warning")
    
    def _on_new_voucher(self):
        """Handle New Voucher button from connection widget."""
        self.status_bar.showMessage("Opening new voucher dialog...")
        self.logger.info("New Voucher action triggered from connection widget")
        self._add_log_entry("📝 Opening new voucher entry dialog...", "info")
        
        try:
            # Create new voucher dialog
            dialog = VoucherEntryDialog(
                connector=self.tally_connector,
                data_reader=self.data_reader,
                voucher=None,  # New voucher
                parent=self
            )
            
            # Connect voucher creation signal
            dialog.voucher_created.connect(self._on_voucher_created)
            
            # Show dialog
            result = dialog.exec()
            
            if result == dialog.Accepted:
                self._add_log_entry("✅ New voucher dialog completed successfully", "success")
            else:
                self._add_log_entry("❌ New voucher dialog cancelled", "warning")
                
        except Exception as e:
            self.logger.error(f"Error opening new voucher dialog: {str(e)}")
            self._add_log_entry(f"❌ Error opening voucher dialog: {str(e)}", "error")
        
        self.status_bar.clearMessage()
    
    def _on_edit_voucher(self):
        """Handle Edit Voucher button from connection widget."""
        self.status_bar.showMessage("Edit voucher functionality coming soon...")
        self.logger.info("Edit Voucher action triggered from connection widget")
        self._add_log_entry("✏️ Edit voucher functionality - coming in Task 5.2", "info")
        
        # TODO: Implement voucher selection and editing in Task 5.2
        # For now, just show a placeholder message
        self._add_log_entry("⚠️ Please use 'New Voucher' for now - editing existing vouchers will be implemented in Task 5.2", "warning")
        
        self.status_bar.clearMessage()
    
    def _on_voucher_created(self, voucher):
        """Handle voucher creation from dialog."""
        self.logger.info(f"New voucher created: {voucher.voucher_number}")
        self._add_log_entry(f"✅ Voucher created successfully: {voucher.get_voucher_display()}", "success")
        
        # TODO: In Task 5.2, we'll implement voucher posting to TallyPrime
        # For now, just log the creation
        self._add_log_entry(f"📋 Voucher details: {len(voucher.entries)} entries, Total: ₹{voucher.total_amount}", "info")
    
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
    
    # Data loading methods for populating the professional data table
    
    def _load_ledger_data(self):
        """
        Load ledger data from TallyPrime using background threading
        
        This method now uses the threading framework to perform data loading
        in the background, keeping the UI responsive during the operation.
        
        Learning: Professional applications should never block the UI thread
        for network operations or heavy computations.
        """
        if not self.task_manager or not self.tally_connector:
            self._add_log_entry("⚠ Threading framework or TallyConnector not available", "warning")
            return
        
        try:
            # Create a background data loading task
            data_worker = create_data_load_task(self.tally_connector, "ledgers")
            
            # Submit the task to the task manager
            task_id = self.task_manager.submit_task(data_worker)
            
            self._add_log_entry("🔄 Starting background ledger data loading...", "info")
            self.status_bar.showMessage("Loading ledger data in background...")
            
            self.logger.info(f"Ledger data loading task submitted: {task_id}")
            
        except Exception as e:
            error_msg = f"❌ Error starting ledger data loading: {str(e)}"
            self._add_log_entry(error_msg, "error")
            self.status_bar.showMessage("Failed to start ledger data loading")
            self.logger.error(f"Error starting ledger data loading: {e}")
    
    def _load_balance_sheet_data(self):
        """
        Load balance sheet data from TallyPrime using background threading
        
        This method creates a background task for loading balance sheet data,
        demonstrating how different types of data operations can use the same
        threading framework.
        """
        if not self.task_manager or not self.tally_connector:
            self._add_log_entry("⚠ Threading framework or TallyConnector not available", "warning")
            return
        
        try:
            # Create a background data loading task for balance sheet
            data_worker = create_data_load_task(self.tally_connector, "balance_sheet")
            
            # Submit the task to the task manager
            task_id = self.task_manager.submit_task(data_worker)
            
            self._add_log_entry("🔄 Starting background balance sheet data loading...", "info")
            self.status_bar.showMessage("Loading balance sheet data in background...")
            
            self.logger.info(f"Balance sheet data loading task submitted: {task_id}")
            
        except Exception as e:
            error_msg = f"❌ Error starting balance sheet data loading: {str(e)}"
            self._add_log_entry(error_msg, "error")
            self.status_bar.showMessage("Failed to start balance sheet data loading")
            self.logger.error(f"Error starting balance sheet data loading: {e}")
    
    def _load_transaction_data(self):
        """
        Load recent transaction data from TallyPrime using background threading
        
        This method demonstrates loading transaction data in a background thread,
        maintaining UI responsiveness while performing potentially time-consuming
        data retrieval operations.
        """
        if not self.task_manager or not self.tally_connector:
            self._add_log_entry("⚠ Threading framework or TallyConnector not available", "warning")
            return
        
        try:
            # Create a background data loading task for transactions
            data_worker = create_data_load_task(self.tally_connector, "transactions")
            
            # Submit the task to the task manager
            task_id = self.task_manager.submit_task(data_worker)
            
            self._add_log_entry("🔄 Starting background transaction data loading...", "info")
            self.status_bar.showMessage("Loading transaction data in background...")
            
            self.logger.info(f"Transaction data loading task submitted: {task_id}")
            
        except Exception as e:
            error_msg = f"❌ Error starting transaction data loading: {str(e)}"
            self._add_log_entry(error_msg, "error")
            self.status_bar.showMessage("Failed to start transaction data loading")
            self.logger.error(f"Error starting transaction data loading: {e}")
    
    # Signal handlers for the professional log widget
    
    def _on_log_exported(self, file_path: str, success: bool, error_message: str):
        """
        Handle log export completion from the advanced log widget
        
        Args:
            file_path: The file path where logs were exported
            success: Whether export was successful
            error_message: Error message if export failed
        """
        if success:
            self.status_bar.showMessage(f"Logs exported successfully to {file_path}", 5000)
            self.logger.info(f"Log export successful: {file_path}")
        else:
            self.status_bar.showMessage(f"Log export failed: {error_message}", 8000)
            self.logger.error(f"Log export failed: {error_message}")
    
    def _on_log_filter_changed(self, level_filter: str, text_filter: str):
        """
        Handle log filter changes from the advanced log widget
        
        Args:
            level_filter: Current log level filter
            text_filter: Current text search filter
        """
        # Update status bar with filter information
        if level_filter != "ALL" or text_filter:
            filter_info = []
            if level_filter != "ALL":
                filter_info.append(f"Level: {level_filter}")
            if text_filter:
                filter_info.append(f"Search: '{text_filter[:20]}{'...' if len(text_filter) > 20 else ''}'")
            
            filter_status = f"Log filters: {', '.join(filter_info)}"
            self.status_bar.showMessage(filter_status, 3000)
        
        self.logger.debug(f"Log filters changed - Level: {level_filter}, Text: '{text_filter}'")
    
    # Threading framework signal handlers
    
    def _on_task_added(self, task_id, task_name: str):
        """
        Handle task addition to the task manager
        
        Args:
            task_id: Unique task identifier
            task_name: Display name for the task
        """
        # Add task to progress widget for monitoring
        if self.progress_widget:
            self.progress_widget.add_task(task_id, task_name)
        
        self._add_log_entry(f"🚀 Background task started: {task_name}", "info", "Threading")
        self.logger.info(f"Background task added: {task_name} (ID: {task_id})")
    
    def _on_task_started(self, task_id):
        """Handle task start notification"""
        self.logger.debug(f"Task started: {task_id}")
    
    def _on_task_completed(self, task_id, result: TaskResult):
        """
        Handle task completion from the task manager
        
        Args:
            task_id: Task identifier
            result: Task execution result
        """
        # Update progress widget status
        if self.progress_widget:
            self.progress_widget.update_task_status(task_id, result.status)
        
        # Log the result
        if result.is_success:
            execution_time = result.execution_time_ms / 1000.0  # Convert to seconds
            self._add_log_entry(
                f"✅ Background task completed successfully in {execution_time:.1f}s", 
                "success", 
                "Threading"
            )
            
            # Handle specific data loading results
            self._handle_data_loading_result(task_id, result)
            
        else:
            self._add_log_entry(
                f"❌ Background task failed: {result.error}", 
                "error", 
                "Threading"
            )
        
        self.logger.info(f"Task completed: {task_id} - Status: {result.status.value}")
    
    def _on_task_cancelled(self, task_id):
        """Handle task cancellation"""
        if self.progress_widget:
            self.progress_widget.update_task_status(task_id, TaskStatus.CANCELLED)
        
        self._add_log_entry("⏹️ Background task cancelled by user", "info", "Threading")
        self.logger.info(f"Task cancelled: {task_id}")
    
    def _on_task_progress(self, task_id, progress: TaskProgress):
        """
        Handle task progress updates
        
        Args:
            task_id: Task identifier  
            progress: Progress information
        """
        # Update progress widget
        if self.progress_widget:
            self.progress_widget.update_task_progress(task_id, progress)
        
        # Log significant progress milestones
        if progress.percentage % 25 == 0 and progress.percentage > 0:
            self.logger.debug(f"Task progress: {task_id} - {progress.percentage}%")
    
    def _handle_data_loading_result(self, task_id, result: TaskResult):
        """
        Handle results from data loading tasks
        
        Args:
            task_id: Task identifier
            result: Task result containing loaded data
        """
        if result.is_success and result.data:
            # Update the data table with loaded data
            if hasattr(self, 'data_table') and result.data:
                try:
                    # Assume result.data contains ledger information
                    if isinstance(result.data, list) and len(result.data) > 0:
                        self.data_table.set_ledger_data(result.data)
                        
                        count = len(result.data)
                        self.status_bar.showMessage(f"Loaded {count} records successfully")
                        self._add_log_entry(f"📊 Data table updated with {count} records", "success")
                        
                except Exception as e:
                    self.logger.error(f"Error updating data table: {e}")
                    self._add_log_entry(f"❌ Error updating data table: {str(e)}", "error")
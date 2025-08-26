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
    QSizePolicy, QSplitter
)
from PySide6.QtCore import QSettings, Signal, Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QFont


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
        
        # Initialize the window
        self._setup_window_properties()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_status_bar()
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
        
        Learning: QMainWindow requires a central widget for the main content area
        """
        # Create the central widget container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create a horizontal layout for the main content
        main_layout = QHBoxLayout(self.central_widget)
        
        # Create a splitter to allow resizable panels
        # QSplitter allows users to resize panels by dragging the divider
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create placeholder panels for now
        # In later phases, these will be replaced with professional widgets
        
        # Left panel - Control Panel (will become connection and operation controls)
        left_panel = self._create_placeholder_panel("Control Panel", 
                                                   "Connection status and controls will appear here")
        left_panel.setMinimumWidth(250)
        left_panel.setMaximumWidth(400)
        splitter.addWidget(left_panel)
        
        # Right panel - Main Content Area (will become data tables and forms)
        right_panel = self._create_placeholder_panel("Main Content", 
                                                    "TallyPrime data and operations will appear here")
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (25% left, 75% right)
        splitter.setSizes([300, 900])
        
        self.logger.info("Central widget created with resizable panels")
    
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
        """Handle Test Connection toolbar action."""
        self.status_bar.showMessage("Testing TallyPrime connection...")
        self.logger.info("Test Connection action triggered")
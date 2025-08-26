"""
TallyPrime Integration Manager - Main Application Class
Professional Desktop Application using PySide6/Qt6

This module contains the main application class that coordinates all components
of the TallyPrime Integration Manager. It acts as the central coordinator
between the UI, business logic, and system components.

Key Learning Points:
- Application architecture and component coordination
- Settings management and configuration loading
- Error handling and logging integration
- Professional application lifecycle management

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
"""

import json
import logging
from pathlib import Path
from typing import Optional

# PySide6/Qt6 imports
from PySide6.QtCore import QObject, QSettings, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

# Import our UI components
from ui.main_window import MainWindow


class TallyIntegrationApp(QObject):
    """
    Main Application Class - Central Coordinator
    
    This class serves as the main application controller that:
    - Manages application lifecycle (startup, shutdown)
    - Coordinates between UI components and business logic
    - Handles configuration and settings management
    - Provides centralized error handling and logging
    - Manages application state and data flow
    
    Learning Points:
    - Inherits from QObject to use Qt's signal-slot system
    - Follows the Model-View-Controller (MVC) pattern
    - Demonstrates professional application architecture
    """
    
    # Qt Signals for application-wide communication
    # Signals allow loose coupling between components
    application_closing = Signal()
    settings_changed = Signal(dict)
    
    def __init__(self, app_directory: Path):
        """
        Initialize the TallyPrime Integration Application.
        
        Args:
            app_directory: Path to the application directory
            
        Learning: Constructor should only store parameters and set up basic state.
        Heavy initialization should be done in a separate initialize() method.
        """
        super().__init__()  # Initialize the QObject parent class
        
        # Store core application paths
        self.app_directory = app_directory
        self.config_directory = app_directory / "config"
        
        # Application components (initialized in initialize() method)
        self.main_window: Optional[MainWindow] = None
        self.settings: Optional[QSettings] = None
        self.application_config: dict = {}
        
        # Set up logging for this class
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"TallyIntegrationApp created with directory: {app_directory}")
    
    def initialize(self) -> bool:
        """
        Initialize all application components.
        
        This method sets up:
        - Application settings and configuration
        - Main window and UI components
        - System integration features
        - Error handling and logging
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Learning: Separate initialization from construction for better error handling
        """
        try:
            self.logger.info("Initializing TallyPrime Integration Manager...")
            
            # Step 1: Load application configuration
            if not self._load_configuration():
                return False
                
            # Step 2: Set up Qt Settings for persistent storage
            self._setup_qt_settings()
            
            # Step 3: Create and initialize the main window
            if not self._initialize_main_window():
                return False
                
            # Step 4: Set up application-wide features
            self._setup_application_features()
            
            self.logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            self._show_error_dialog("Initialization Error", 
                                  f"Failed to initialize application: {e}")
            return False
    
    def _load_configuration(self) -> bool:
        """
        Load application configuration from JSON file.
        
        Returns:
            bool: True if configuration loaded successfully
            
        Learning: Configuration should be loaded early in application startup
        """
        try:
            config_file = self.config_directory / "default_settings.json"
            
            if not config_file.exists():
                self.logger.error(f"Configuration file not found: {config_file}")
                return False
                
            with open(config_file, 'r', encoding='utf-8') as f:
                self.application_config = json.load(f)
                
            self.logger.info(f"Configuration loaded from: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _setup_qt_settings(self):
        """
        Set up Qt Settings for persistent application preferences.
        
        Learning: QSettings provides cross-platform settings storage
        (Windows Registry, macOS plist, Linux config files)
        """
        # Qt Settings automatically uses the application metadata we set in main.py
        self.settings = QSettings()
        self.logger.info("Qt Settings initialized")
    
    def _initialize_main_window(self) -> bool:
        """
        Create and initialize the main application window.
        
        Returns:
            bool: True if main window created successfully
            
        Learning: Main window creation should be separate from application setup
        """
        try:
            # Create the main window with configuration
            self.main_window = MainWindow(
                config=self.application_config,
                settings=self.settings
            )
            
            # Connect main window signals to application handlers
            self.main_window.closing.connect(self._on_main_window_closing)
            
            self.logger.info("Main window created and configured")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create main window: {e}")
            return False
    
    def _setup_application_features(self):
        """
        Set up application-wide features and integrations.
        
        Learning: Professional applications need various system integrations
        """
        # Set up application icon (when we have one)
        # QApplication.instance().setWindowIcon(QIcon("path/to/icon"))
        
        # Set up any application-wide timers or background tasks
        # (We'll add these later as needed)
        
        self.logger.info("Application features configured")
    
    def show(self):
        """
        Show the main application window.
        
        Learning: Showing the window should be a separate step from creation
        """
        if self.main_window:
            self.main_window.show()
            self.logger.info("Main window displayed")
        else:
            self.logger.error("Cannot show main window - not initialized")
    
    def _on_main_window_closing(self):
        """
        Handle main window closing event.
        
        Learning: Proper cleanup is essential for professional applications
        """
        self.logger.info("Main window closing - starting application cleanup")
        
        # Emit signal to notify other components
        self.application_closing.emit()
        
        # Save any pending settings
        if self.settings:
            self.settings.sync()
            
        # Additional cleanup can be added here
        self.logger.info("Application cleanup completed")
    
    def _show_error_dialog(self, title: str, message: str):
        """
        Show a professional error dialog to the user.
        
        Args:
            title: Dialog title
            message: Error message to display
            
        Learning: User-friendly error reporting is crucial for desktop applications
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setDetailedText(f"Application Directory: {self.app_directory}")
        msg_box.exec()
    
    def get_config_value(self, key_path: str, default=None):
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Configuration key in dot notation (e.g., 'ui_settings.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            theme = app.get_config_value('ui_settings.theme', 'default')
        """
        try:
            keys = key_path.split('.')
            value = self.application_config
            
            for key in keys:
                value = value[key]
                
            return value
            
        except (KeyError, TypeError):
            return default
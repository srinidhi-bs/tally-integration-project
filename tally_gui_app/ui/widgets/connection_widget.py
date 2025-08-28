#!/usr/bin/env python3
"""
TallyPrime Connection Control Widget
Professional Qt6 widget for managing TallyPrime connections

This widget provides a comprehensive interface for:
- Real-time connection status monitoring
- Connection testing and management
- Company information display
- Auto-refresh functionality with timers

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
Date: August 26, 2025
"""

import logging
from typing import Optional
from datetime import datetime

# PySide6/Qt6 imports for GUI components
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFrame, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Signal, QTimer, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QFont

# Import our TallyConnector and related classes  
from core.tally.connector import TallyConnector, ConnectionStatus, TallyConnectionConfig
from app.settings import SettingsManager
from ui.resources.styles.theme_manager import get_theme_manager


class ConnectionStatusIndicator(QLabel):
    """
    Professional connection status indicator with animated visual feedback
    
    Learning Points:
    - Custom widget creation by subclassing QLabel
    - CSS styling for professional appearance
    - State-based visual feedback using colors and animations
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the status indicator widget
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Set up the indicator properties
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)
        
        # Initialize with disconnected state
        self.set_status(ConnectionStatus.DISCONNECTED)
        
        # Set up the base styling
        self._setup_styling()
    
    def _setup_styling(self):
        """Set up the base CSS styling for the indicator"""
        self.setStyleSheet("""
            QLabel {
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px 12px;
                border: 2px solid transparent;
            }
        """)
    
    def set_status(self, status: ConnectionStatus, message: str = ""):
        """
        Update the indicator based on connection status
        
        Args:
            status: Current connection status
            message: Optional status message
            
        Learning: This method demonstrates state-based UI updates
        """
        # Define status configurations with colors and text
        status_config = {
            ConnectionStatus.DISCONNECTED: {
                'text': '● DISCONNECTED',
                'color': '#e74c3c',  # Red
                'bg_color': '#fadbd8'  # Light red background
            },
            ConnectionStatus.CONNECTING: {
                'text': '⏳ CONNECTING...',
                'color': '#f39c12',  # Orange
                'bg_color': '#fdeaa7'  # Light orange background
            },
            ConnectionStatus.CONNECTED: {
                'text': '● CONNECTED',
                'color': '#27ae60',  # Green
                'bg_color': '#d5f4e6'  # Light green background
            },
            ConnectionStatus.ERROR: {
                'text': '⚠ ERROR',
                'color': '#e74c3c',  # Red
                'bg_color': '#fadbd8'  # Light red background
            },
            ConnectionStatus.TIMEOUT: {
                'text': '⏰ TIMEOUT',
                'color': '#f39c12',  # Orange
                'bg_color': '#fdeaa7'  # Light orange background
            },
            ConnectionStatus.TESTING: {
                'text': '🔍 TESTING...',
                'color': '#3498db',  # Blue
                'bg_color': '#d6eaf8'  # Light blue background
            }
        }
        
        config = status_config.get(status, status_config[ConnectionStatus.DISCONNECTED])
        
        # Update the display text
        display_text = config['text']
        if message:
            display_text += f"\n{message}"
        
        self.setText(display_text)
        
        # Apply the styling based on status
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {config['bg_color']};
                color: {config['color']};
                border: 2px solid {config['color']};
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px 12px;
            }}
        """)


class ConnectionWidget(QWidget):
    """
    Professional TallyPrime Connection Management Widget
    
    This widget provides a comprehensive interface for managing TallyPrime connections.
    It integrates with the TallyConnector class to provide real-time status updates
    and connection management functionality.
    
    Key Features:
    - Real-time connection status monitoring with visual indicators
    - Test connection functionality with progress feedback
    - Company information display when connected
    - Auto-refresh functionality with configurable timers
    - Connection settings management
    - Professional styling with hover effects and animations
    
    Learning Points:
    - Complex widget composition using multiple child widgets
    - Signal-slot connections for real-time communication
    - Timer-based functionality for auto-refresh
    - Professional error handling and user feedback
    - Integration with existing backend systems
    """
    
    # Custom signals for communication with main application
    connection_test_requested = Signal()
    settings_dialog_requested = Signal()
    refresh_data_requested = Signal()
    
    # Data operation signals
    load_ledgers_requested = Signal()
    load_balance_sheet_requested = Signal()
    load_recent_transactions_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the connection widget
        
        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Set up logging for this widget
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.tally_connector: Optional[TallyConnector] = None
        self.settings_manager: Optional[SettingsManager] = None
        
        # UI Components (will be created in setup methods)
        self.status_indicator: Optional[ConnectionStatusIndicator] = None
        self.company_info_label: Optional[QLabel] = None
        self.last_sync_label: Optional[QLabel] = None
        self.test_connection_btn: Optional[QPushButton] = None
        self.settings_btn: Optional[QPushButton] = None
        self.refresh_btn: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        # Auto-refresh timer
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self._auto_refresh)
        
        # Current connection state
        self.current_status = ConnectionStatus.DISCONNECTED
        self.company_info = None
        self.last_sync_time = None
        
        # Set up the widget
        self._setup_ui()
        self._setup_styling()
        self._setup_connections()
        
        self.logger.info("Connection widget initialized successfully")
    
    def _setup_ui(self):
        """
        Set up the user interface layout and components
        
        Learning: This method demonstrates professional UI composition
        """
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Connection Status Section
        self._create_status_section(main_layout)
        
        # Connection Actions Section
        self._create_actions_section(main_layout)
        
        # Data Operations Section (new)
        self._create_data_operations_section(main_layout)
        
        # Company Information Section
        self._create_company_info_section(main_layout)
        
        # Progress Bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Add stretch to push content to top
        main_layout.addStretch()
    
    def _create_status_section(self, parent_layout: QVBoxLayout):
        """
        Create the connection status display section
        
        Args:
            parent_layout: Parent layout to add this section to
        """
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        # Status indicator
        self.status_indicator = ConnectionStatusIndicator()
        status_layout.addWidget(self.status_indicator)
        
        # Company information (initially hidden)
        self.company_info_label = QLabel("Company: Not Connected")
        self.company_info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 11px;
                padding: 2px 4px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.company_info_label)
        
        # Last sync time
        self.last_sync_label = QLabel("Last Sync: Never")
        self.last_sync_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 10px;
                padding: 2px 4px;
            }
        """)
        status_layout.addWidget(self.last_sync_label)
        
        parent_layout.addWidget(status_group)
    
    def _create_actions_section(self, parent_layout: QVBoxLayout):
        """
        Create the connection action buttons section
        
        Args:
            parent_layout: Parent layout to add this section to
        """
        actions_group = QGroupBox("Connection Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Test Connection Button
        self.test_connection_btn = QPushButton("🔍 Test Connection")
        self.test_connection_btn.clicked.connect(self._on_test_connection)
        self.test_connection_btn.setToolTip("Test connection to TallyPrime HTTP Gateway")
        actions_layout.addWidget(self.test_connection_btn)
        
        # Refresh Data Button
        self.refresh_btn = QPushButton("🔄 Refresh Data")
        self.refresh_btn.clicked.connect(self._on_refresh_data)
        self.refresh_btn.setToolTip("Refresh data from TallyPrime")
        self.refresh_btn.setEnabled(False)  # Disabled until connected
        actions_layout.addWidget(self.refresh_btn)
        
        # Connection Settings Button
        self.settings_btn = QPushButton("⚙️ Connection Settings")
        self.settings_btn.clicked.connect(self._on_connection_settings)
        self.settings_btn.setToolTip("Configure TallyPrime connection settings")
        actions_layout.addWidget(self.settings_btn)
        
        parent_layout.addWidget(actions_group)
    
    def _create_data_operations_section(self, parent_layout: QVBoxLayout):
        """
        Create the data operations section for loading different data types
        
        Args:
            parent_layout: Parent layout to add this section to
        """
        data_ops_group = QGroupBox("Data Operations")
        data_ops_layout = QVBoxLayout(data_ops_group)
        
        # List Ledgers Button
        self.list_ledgers_btn = QPushButton("📋 List Ledgers")
        self.list_ledgers_btn.clicked.connect(self._on_load_ledgers)
        self.list_ledgers_btn.setToolTip("Load and display all ledger accounts")
        self.list_ledgers_btn.setEnabled(False)  # Disabled until connected
        data_ops_layout.addWidget(self.list_ledgers_btn)
        
        # Show Balance Sheet Button
        self.balance_sheet_btn = QPushButton("📊 Balance Sheet")
        self.balance_sheet_btn.clicked.connect(self._on_load_balance_sheet)
        self.balance_sheet_btn.setToolTip("Display balance sheet data")
        self.balance_sheet_btn.setEnabled(False)  # Disabled until connected
        data_ops_layout.addWidget(self.balance_sheet_btn)
        
        # Recent Transactions Button
        self.recent_transactions_btn = QPushButton("📈 Recent Transactions")
        self.recent_transactions_btn.clicked.connect(self._on_load_recent_transactions)
        self.recent_transactions_btn.setToolTip("Show recent transaction entries")
        self.recent_transactions_btn.setEnabled(False)  # Disabled until connected
        data_ops_layout.addWidget(self.recent_transactions_btn)
        
        parent_layout.addWidget(data_ops_group)
    
    def _create_company_info_section(self, parent_layout: QVBoxLayout):
        """
        Create the company information display section
        
        Args:
            parent_layout: Parent layout to add this section to
        """
        info_group = QGroupBox("Company Information")
        info_layout = QVBoxLayout(info_group)
        
        # Company details (will be populated when connected)
        self.company_details_label = QLabel("Connect to TallyPrime to view company information")
        self.company_details_label.setWordWrap(True)
        self.company_details_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 11px;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                line-height: 1.4;
            }
        """)
        info_layout.addWidget(self.company_details_label)
        
        parent_layout.addWidget(info_group)
    
    def _setup_styling(self):
        """
        Set up the professional styling for the widget with dark theme support
        
        Learning: Using centralized theme manager for consistent styling
        """
        # Use centralized theme manager
        theme_manager = get_theme_manager()
        stylesheet = theme_manager.get_stylesheet_for_widget('connection_widget')
        self.setStyleSheet(stylesheet)
        
        # Connect to theme changes for dynamic updates
        theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_mode):
        """
        Handle theme changes for dynamic theme switching
        
        Args:
            theme_mode: New theme mode
        """
        # Reapply styling with new theme
        theme_manager = get_theme_manager()
        stylesheet = theme_manager.get_stylesheet_for_widget('connection_widget')
        self.setStyleSheet(stylesheet)
        
        self.logger.info(f"Connection widget theme changed to: {theme_mode.value}")
    
    def _setup_connections(self):
        """
        Set up signal-slot connections for the widget
        
        Learning: Signal-slot connections enable reactive UI updates
        """
        # Timer connections are already set up in __init__
        # Additional connections will be established when TallyConnector is set
        pass
    
    def set_tally_connector(self, connector: TallyConnector):
        """
        Set the TallyConnector instance for this widget
        
        Args:
            connector: TallyConnector instance
        """
        self.tally_connector = connector
        
        # Connect to TallyConnector signals for real-time updates
        self.tally_connector.connection_status_changed.connect(self._on_connection_status_changed)
        self.tally_connector.company_info_received.connect(self._on_company_info_received)
        self.tally_connector.error_occurred.connect(self._on_error_occurred)
        
        self.logger.info("TallyConnector connected to connection widget")
    
    def set_settings_manager(self, settings_manager: SettingsManager):
        """
        Set the SettingsManager instance for this widget
        
        Args:
            settings_manager: SettingsManager instance
        """
        self.settings_manager = settings_manager
        self.logger.info("SettingsManager connected to connection widget")
    
    def _on_test_connection(self):
        """
        Handle test connection button click
        
        Learning: Button click handlers should provide immediate feedback
        """
        if not self.tally_connector:
            self.logger.warning("TallyConnector not available for connection test")
            return
        
        # Show progress and disable button
        self._show_progress("Testing connection...")
        self.test_connection_btn.setEnabled(False)
        
        # Emit signal to request connection test
        self.connection_test_requested.emit()
        
        # Start the connection test
        self.tally_connector.test_connection()
        
        self.logger.info("Connection test initiated")
    
    def _on_refresh_data(self):
        """
        Handle refresh data button click
        """
        if not self.tally_connector:
            self.logger.warning("TallyConnector not available for data refresh")
            return
        
        # Show progress
        self._show_progress("Refreshing data...")
        
        # Emit signal and update last sync time
        self.refresh_data_requested.emit()
        self._update_last_sync_time()
        
        self.logger.info("Data refresh initiated")
    
    def _on_connection_settings(self):
        """
        Handle connection settings button click
        """
        # Emit signal to request settings dialog
        self.settings_dialog_requested.emit()
        self.logger.info("Connection settings dialog requested")
    
    def _on_load_ledgers(self):
        """
        Handle load ledgers button click
        """
        # Emit signal to request ledger data loading
        self.load_ledgers_requested.emit()
        self.logger.info("Ledger data loading requested")
    
    def _on_load_balance_sheet(self):
        """
        Handle load balance sheet button click
        """
        # Emit signal to request balance sheet data loading
        self.load_balance_sheet_requested.emit()
        self.logger.info("Balance sheet data loading requested")
    
    def _on_load_recent_transactions(self):
        """
        Handle load recent transactions button click
        """
        # Emit signal to request recent transactions data loading
        self.load_recent_transactions_requested.emit()
        self.logger.info("Recent transactions data loading requested")
    
    def _on_connection_status_changed(self, status: ConnectionStatus, message: str = ""):
        """
        Handle connection status changes from TallyConnector
        
        Args:
            status: New connection status
            message: Status message
            
        Learning: This method demonstrates reactive UI programming
        """
        self.current_status = status
        
        # Update status indicator
        self.status_indicator.set_status(status, message)
        
        # Update button states based on connection status
        self._update_button_states(status)
        
        # Hide progress bar if not connecting/testing
        if status not in [ConnectionStatus.CONNECTING, ConnectionStatus.TESTING]:
            self._hide_progress()
        
        # Update last sync time if connected
        if status == ConnectionStatus.CONNECTED:
            self._update_last_sync_time()
            # Start auto-refresh if enabled
            self._start_auto_refresh()
        else:
            # Stop auto-refresh if disconnected
            self._stop_auto_refresh()
        
        self.logger.info(f"Connection status changed to: {status.value}")
    
    def _on_company_info_received(self, company_info):
        """
        Handle company information received from TallyConnector
        
        Args:
            company_info: Company information object
        """
        self.company_info = company_info
        self._update_company_display()
        self.logger.info(f"Company information received: {company_info.name}")
    
    def _on_error_occurred(self, error_type: str, error_message: str):
        """
        Handle errors from TallyConnector
        
        Args:
            error_type: Type of error
            error_message: Error message
        """
        # Hide progress and re-enable buttons
        self._hide_progress()
        self.test_connection_btn.setEnabled(True)
        
        self.logger.error(f"Connection error occurred: {error_type} - {error_message}")
    
    def _update_button_states(self, status: ConnectionStatus):
        """
        Update button enabled states based on connection status
        
        Args:
            status: Current connection status
        """
        # Test connection button is always enabled (unless testing)
        self.test_connection_btn.setEnabled(status != ConnectionStatus.TESTING)
        
        # Refresh button only enabled when connected
        self.refresh_btn.setEnabled(status == ConnectionStatus.CONNECTED)
        
        # Settings button always enabled
        self.settings_btn.setEnabled(True)
        
        # Data operation buttons only enabled when connected
        data_buttons_enabled = (status == ConnectionStatus.CONNECTED)
        self.list_ledgers_btn.setEnabled(data_buttons_enabled)
        self.balance_sheet_btn.setEnabled(data_buttons_enabled)
        self.recent_transactions_btn.setEnabled(data_buttons_enabled)
    
    def _update_company_display(self):
        """
        Update the company information display
        """
        if not self.company_info:
            self.company_info_label.setText("Company: Not Connected")
            self.company_details_label.setText("Connect to TallyPrime to view company information")
            return
        
        # Update company name in status
        self.company_info_label.setText(f"Company: {self.company_info.name}")
        
        # Create detailed company information
        details = [
            f"📊 Company: {self.company_info.name}",
            f"📅 Financial Year: {getattr(self.company_info, 'financial_year', 'N/A')}",
            f"📋 Ledgers: {getattr(self.company_info, 'ledger_count', 'N/A')}",
            f"💰 Currency: {getattr(self.company_info, 'currency', 'N/A')}",
            f"📍 Location: {getattr(self.company_info, 'address', 'N/A')}"
        ]
        
        self.company_details_label.setText("\n".join(details))
    
    def _update_last_sync_time(self):
        """
        Update the last sync time display
        """
        self.last_sync_time = datetime.now()
        time_str = self.last_sync_time.strftime("%H:%M:%S")
        self.last_sync_label.setText(f"Last Sync: {time_str}")
    
    def _show_progress(self, message: str = "Please wait..."):
        """
        Show progress bar with message
        
        Args:
            message: Progress message to display
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setFormat(message)
    
    def _hide_progress(self):
        """
        Hide the progress bar
        """
        self.progress_bar.setVisible(False)
    
    def _start_auto_refresh(self):
        """
        Start the auto-refresh timer if enabled in settings
        """
        if self.settings_manager:
            # Get auto-refresh interval from settings (default 5 minutes)
            # For now, use default values - this can be enhanced later when settings dialog is implemented
            auto_refresh_enabled = False  # Default: disabled
            auto_refresh_interval = 300   # Default: 5 minutes
            
            if auto_refresh_enabled and auto_refresh_interval > 0:
                self.auto_refresh_timer.start(auto_refresh_interval * 1000)  # Convert to milliseconds
                self.logger.info(f"Auto-refresh started with {auto_refresh_interval} second interval")
    
    def _stop_auto_refresh(self):
        """
        Stop the auto-refresh timer
        """
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
            self.logger.info("Auto-refresh stopped")
    
    def _auto_refresh(self):
        """
        Handle auto-refresh timer timeout
        """
        if self.current_status == ConnectionStatus.CONNECTED:
            self._on_refresh_data()
            self.logger.info("Auto-refresh triggered")
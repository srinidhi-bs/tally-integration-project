#!/usr/bin/env python3
"""
TallyPrime Connection Settings Dialog
Professional Qt6 dialog for configuring TallyPrime connection settings

This dialog provides a comprehensive interface for:
- Connection configuration (IP, port, timeout)
- Input validation with immediate feedback
- Connection testing within the dialog
- Connection history and saved configurations
- Advanced connection settings

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
Date: August 27, 2025
"""

import logging
import re
import socket
from typing import Optional, List, Dict, Any
from datetime import datetime

# PySide6/Qt6 imports for GUI components
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QSpinBox, QComboBox, QGroupBox,
    QTabWidget, QWidget, QListWidget, QListWidgetItem,
    QProgressBar, QTextEdit, QCheckBox, QSlider,
    QDialogButtonBox, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Signal, QTimer, Qt, QThread
from PySide6.QtGui import QValidator, QIntValidator, QFont, QPalette, QIcon

# Import our TallyConnector and related classes  
from core.tally.connector import TallyConnector, ConnectionStatus, TallyConnectionConfig
from app.settings import SettingsManager
from ui.resources.styles.theme_manager import get_theme_manager


class IPAddressValidator(QValidator):
    """
    Custom validator for IP address input fields
    
    Learning Points:
    - Custom validator creation by subclassing QValidator
    - Real-time input validation using regular expressions
    - State-based validation (Invalid, Intermediate, Acceptable)
    """
    
    def validate(self, input_text: str, pos: int) -> tuple:
        """
        Validate IP address input
        
        Args:
            input_text: Current input text
            pos: Current cursor position
            
        Returns:
            Tuple of (validation_state, validated_text, cursor_position)
        """
        # Allow empty input for intermediate state
        if not input_text.strip():
            return (QValidator.Intermediate, input_text, pos)
        
        # Check if it's a valid IP address pattern
        ip_pattern = r'^(\d{1,3}\.){0,3}\d{0,3}$'
        if not re.match(ip_pattern, input_text):
            return (QValidator.Invalid, input_text, pos)
        
        # Check each octet if complete IP address
        parts = input_text.split('.')
        if len(parts) == 4:
            try:
                for part in parts:
                    if not part:  # Empty part
                        return (QValidator.Intermediate, input_text, pos)
                    num = int(part)
                    if num < 0 or num > 255:
                        return (QValidator.Invalid, input_text, pos)
                # Valid complete IP address
                return (QValidator.Acceptable, input_text, pos)
            except ValueError:
                return (QValidator.Invalid, input_text, pos)
        
        # Incomplete but valid so far
        return (QValidator.Intermediate, input_text, pos)


class ConnectionTestWorker(QThread):
    """
    Background thread worker for connection testing
    
    Learning Points:
    - QThread usage for non-blocking UI operations
    - Signal-slot communication between threads
    - Proper thread cleanup and resource management
    """
    
    # Signals for communicating with UI thread
    test_started = Signal()
    test_completed = Signal(bool, str)  # success, message
    progress_update = Signal(str)  # status message
    
    def __init__(self, host: str, port: int, timeout: int = 5):
        """
        Initialize the connection test worker
        
        Args:
            host: TallyPrime server IP address
            port: TallyPrime server port
            timeout: Connection timeout in seconds
        """
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """
        Execute the connection test in background thread
        """
        try:
            self.test_started.emit()
            self.progress_update.emit("Connecting to TallyPrime...")
            
            # Create a temporary TallyConnector for testing
            config = TallyConnectionConfig(
                host=self.host,
                port=self.port,
                timeout=self.timeout
            )
            
            temp_connector = TallyConnector(config)
            
            # Test the connection
            self.progress_update.emit("Testing HTTP-XML Gateway...")
            success, message = temp_connector.test_connection_sync()
            
            if success:
                self.progress_update.emit("Retrieving company information...")
                # Try to get company info as additional validation
                try:
                    company_info = temp_connector.get_company_info()
                    if company_info:
                        message = f"✅ Connected successfully to {company_info.name}"
                    else:
                        message = "✅ Connected successfully (no company info available)"
                except Exception as e:
                    # Connection works but couldn't get company info
                    message = f"✅ Connected successfully (company info error: {str(e)[:50]}...)"
                    success = True  # Still consider it successful
            
            self.test_completed.emit(success, message)
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            self.test_completed.emit(False, f"❌ Connection failed: {str(e)}")


class ConnectionDialog(QDialog):
    """
    Professional TallyPrime Connection Settings Dialog
    
    This dialog provides a comprehensive interface for configuring TallyPrime
    connection settings with professional validation, testing, and history management.
    
    Key Features:
    - Tabbed interface for organized settings
    - Real-time input validation with visual feedback
    - Built-in connection testing with progress indication
    - Connection history and saved configurations
    - Advanced settings for timeouts and connection pooling
    - Professional styling that matches application theme
    
    Learning Points:
    - Complex dialog composition with multiple tabs
    - Custom validators for specialized input fields
    - Background threading for non-blocking operations
    - Signal-slot communication for real-time updates
    - Professional error handling and user feedback
    """
    
    # Signals for communication with parent application
    connection_config_changed = Signal(TallyConnectionConfig)
    test_connection_requested = Signal(str, int)  # host, port
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 settings_manager: Optional[SettingsManager] = None):
        """
        Initialize the connection settings dialog
        
        Args:
            parent: Parent widget (optional)
            settings_manager: Settings manager instance
        """
        super().__init__(parent)
        
        # Set up logging for this dialog
        self.logger = logging.getLogger(__name__)
        
        # Store references
        self.settings_manager = settings_manager
        self.original_config: Optional[TallyConnectionConfig] = None
        self.connection_test_worker: Optional[ConnectionTestWorker] = None
        
        # UI Components (will be initialized in setup methods)
        self.host_input: Optional[QLineEdit] = None
        self.port_input: Optional[QSpinBox] = None
        self.timeout_input: Optional[QSpinBox] = None
        self.test_button: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.test_results_text: Optional[QTextEdit] = None
        self.history_list: Optional[QListWidget] = None
        
        # Advanced settings
        self.retry_count_input: Optional[QSpinBox] = None
        self.connection_pool_checkbox: Optional[QCheckBox] = None
        self.auto_discover_checkbox: Optional[QCheckBox] = None
        
        # Set up the dialog
        self._setup_dialog()
        self._setup_ui()
        self._setup_styling()
        self._setup_connections()
        self._load_current_settings()
        
        self.logger.info("Connection settings dialog initialized")
    
    def _setup_dialog(self):
        """
        Set up basic dialog properties
        """
        self.setWindowTitle("TallyPrime Connection Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(650, 550)
        
        # Set window icon if available
        # self.setWindowIcon(QIcon(":/icons/settings.png"))  # Uncomment when icon is available
    
    def _setup_ui(self):
        """
        Set up the user interface with tabbed layout
        
        Learning: This method demonstrates complex dialog composition
        """
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Create tab widget for organized settings
        tab_widget = QTabWidget()
        
        # Add tabs
        tab_widget.addTab(self._create_connection_tab(), "🔗 Connection")
        tab_widget.addTab(self._create_testing_tab(), "🧪 Testing")
        tab_widget.addTab(self._create_history_tab(), "📋 History")
        tab_widget.addTab(self._create_advanced_tab(), "⚙️ Advanced")
        
        main_layout.addWidget(tab_widget)
        
        # Add dialog buttons
        self._create_dialog_buttons(main_layout)
    
    def _create_connection_tab(self) -> QWidget:
        """
        Create the main connection configuration tab
        
        Returns:
            Widget containing connection settings
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Basic Connection Settings Group
        basic_group = QGroupBox("Basic Connection Settings")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(12)
        
        # TallyPrime Server IP Address
        basic_layout.addWidget(QLabel("TallyPrime Server IP:"), 0, 0)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("e.g., 192.168.1.100 or localhost")
        self.host_input.setValidator(IPAddressValidator())
        self.host_input.textChanged.connect(self._on_connection_settings_changed)
        basic_layout.addWidget(self.host_input, 0, 1, 1, 2)
        
        # Host input help text
        host_help = QLabel("💡 Enter the IP address where TallyPrime is running")
        host_help.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        basic_layout.addWidget(host_help, 1, 1, 1, 2)
        
        # TallyPrime HTTP Gateway Port
        basic_layout.addWidget(QLabel("HTTP Gateway Port:"), 2, 0)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(9000)
        self.port_input.setSuffix(" ")
        self.port_input.valueChanged.connect(self._on_connection_settings_changed)
        basic_layout.addWidget(self.port_input, 2, 1)
        
        # Port help text
        port_help = QLabel("💡 Default TallyPrime port is 9000")
        port_help.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        basic_layout.addWidget(port_help, 3, 1, 1, 2)
        
        # Connection Timeout
        basic_layout.addWidget(QLabel("Connection Timeout:"), 4, 0)
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 60)
        self.timeout_input.setValue(10)
        self.timeout_input.setSuffix(" seconds")
        self.timeout_input.valueChanged.connect(self._on_connection_settings_changed)
        basic_layout.addWidget(self.timeout_input, 4, 1)
        
        # Timeout help text
        timeout_help = QLabel("💡 How long to wait for TallyPrime to respond")
        timeout_help.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        basic_layout.addWidget(timeout_help, 5, 1, 1, 2)
        
        layout.addWidget(basic_group)
        
        # Quick Connection Options
        quick_group = QGroupBox("Quick Connection Options")
        quick_layout = QHBoxLayout(quick_group)
        
        # Localhost button
        localhost_btn = QPushButton("🏠 Use Localhost")
        localhost_btn.setToolTip("Set connection to local TallyPrime instance")
        localhost_btn.clicked.connect(lambda: self._set_quick_connection("localhost", 9000))
        quick_layout.addWidget(localhost_btn)
        
        # Common port buttons
        port_9000_btn = QPushButton("🔗 Port 9000")
        port_9000_btn.setToolTip("Use default TallyPrime port 9000")
        port_9000_btn.clicked.connect(lambda: self.port_input.setValue(9000))
        quick_layout.addWidget(port_9000_btn)
        
        port_9999_btn = QPushButton("🔗 Port 9999")
        port_9999_btn.setToolTip("Use alternative TallyPrime port 9999")
        port_9999_btn.clicked.connect(lambda: self.port_input.setValue(9999))
        quick_layout.addWidget(port_9999_btn)
        
        quick_layout.addStretch()
        layout.addWidget(quick_group)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        return tab
    
    def _create_testing_tab(self) -> QWidget:
        """
        Create the connection testing tab
        
        Returns:
            Widget containing connection testing interface
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Test Connection Group
        test_group = QGroupBox("Connection Testing")
        test_layout = QVBoxLayout(test_group)
        test_layout.setSpacing(12)
        
        # Test button and progress
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("🧪 Test Connection")
        self.test_button.setMinimumHeight(40)
        self.test_button.clicked.connect(self._on_test_connection)
        button_layout.addWidget(self.test_button)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)
        
        test_layout.addLayout(button_layout)
        
        # Test results display
        results_label = QLabel("Test Results:")
        results_label.setFont(QFont("", 10, QFont.Bold))
        test_layout.addWidget(results_label)
        
        self.test_results_text = QTextEdit()
        self.test_results_text.setReadOnly(True)
        self.test_results_text.setMaximumHeight(200)
        self.test_results_text.setPlainText("Click 'Test Connection' to verify TallyPrime connectivity...")
        test_layout.addWidget(self.test_results_text)
        
        layout.addWidget(test_group)
        
        # Connection Information Group
        info_group = QGroupBox("Connection Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
<b>TallyPrime HTTP-XML Gateway Requirements:</b><br>
• TallyPrime should be running and company should be loaded<br>
• HTTP-XML Gateway must be enabled in TallyPrime<br>
• Default port is 9000 (can be changed in TallyPrime)<br>
• Firewall should allow connections on the specified port<br><br>

<b>Troubleshooting Tips:</b><br>
• Ensure TallyPrime is running with a company loaded<br>
• Check if HTTP-XML Gateway is enabled in TallyPrime configuration<br>
• Verify network connectivity if connecting to remote TallyPrime<br>
• Try alternative ports (9999, 8000) if default doesn't work
        """)
        info_text.setWordWrap(True)
        info_text.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                line-height: 1.5;
            }
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return tab
    
    def _create_history_tab(self) -> QWidget:
        """
        Create the connection history tab
        
        Returns:
            Widget containing connection history management
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Connection History Group
        history_group = QGroupBox("Recent Connections")
        history_layout = QVBoxLayout(history_group)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemDoubleClicked.connect(self._on_history_item_selected)
        history_layout.addWidget(self.history_list)
        
        # History buttons
        history_buttons = QHBoxLayout()
        
        load_btn = QPushButton("📥 Load Selected")
        load_btn.clicked.connect(self._load_selected_history)
        history_buttons.addWidget(load_btn)
        
        save_btn = QPushButton("💾 Save Current")
        save_btn.clicked.connect(self._save_current_connection)
        history_buttons.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.clicked.connect(self._clear_connection_history)
        history_buttons.addWidget(clear_btn)
        
        history_buttons.addStretch()
        history_layout.addLayout(history_buttons)
        
        layout.addWidget(history_group)
        
        # Saved Connections Group (for future enhancement)
        saved_group = QGroupBox("Saved Configurations")
        saved_layout = QVBoxLayout(saved_group)
        
        saved_info = QLabel("💡 Saved connection configurations will be available in future versions")
        saved_info.setStyleSheet("color: #6c757d; font-style: italic; padding: 20px;")
        saved_info.setAlignment(Qt.AlignCenter)
        saved_layout.addWidget(saved_info)
        
        layout.addWidget(saved_group)
        layout.addStretch()
        
        return tab
    
    def _create_advanced_tab(self) -> QWidget:
        """
        Create the advanced settings tab
        
        Returns:
            Widget containing advanced connection options
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Advanced Connection Settings Group
        advanced_group = QGroupBox("Advanced Connection Settings")
        advanced_layout = QGridLayout(advanced_group)
        advanced_layout.setSpacing(12)
        
        # Retry Count
        advanced_layout.addWidget(QLabel("Connection Retry Count:"), 0, 0)
        self.retry_count_input = QSpinBox()
        self.retry_count_input.setRange(0, 10)
        self.retry_count_input.setValue(3)
        self.retry_count_input.setToolTip("Number of times to retry failed connections")
        advanced_layout.addWidget(self.retry_count_input, 0, 1)
        
        retry_help = QLabel("💡 How many times to retry if connection fails")
        retry_help.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        advanced_layout.addWidget(retry_help, 1, 1, 1, 2)
        
        # Connection Pooling
        self.connection_pool_checkbox = QCheckBox("Enable Connection Pooling")
        self.connection_pool_checkbox.setToolTip("Use connection pooling for better performance")
        self.connection_pool_checkbox.setChecked(True)
        advanced_layout.addWidget(self.connection_pool_checkbox, 2, 0, 1, 2)
        
        pool_help = QLabel("💡 Keeps connections alive for better performance")
        pool_help.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        advanced_layout.addWidget(pool_help, 3, 0, 1, 2)
        
        # Auto-Discovery
        self.auto_discover_checkbox = QCheckBox("Enable Auto-Discovery")
        self.auto_discover_checkbox.setToolTip("Automatically discover TallyPrime instances on network")
        self.auto_discover_checkbox.setChecked(False)
        advanced_layout.addWidget(self.auto_discover_checkbox, 4, 0, 1, 2)
        
        discover_help = QLabel("💡 Scan network for TallyPrime instances (may be slow)")
        discover_help.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        advanced_layout.addWidget(discover_help, 5, 0, 1, 2)
        
        layout.addWidget(advanced_group)
        
        # Performance Settings Group
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QGridLayout(performance_group)
        
        # Keep-alive settings
        performance_layout.addWidget(QLabel("Keep-Alive Interval:"), 0, 0)
        keepalive_slider = QSlider(Qt.Horizontal)
        keepalive_slider.setRange(5, 300)  # 5 seconds to 5 minutes
        keepalive_slider.setValue(30)
        keepalive_slider.setToolTip("How often to send keep-alive packets (seconds)")
        performance_layout.addWidget(keepalive_slider, 0, 1)
        
        keepalive_label = QLabel("30 seconds")
        keepalive_slider.valueChanged.connect(lambda v: keepalive_label.setText(f"{v} seconds"))
        performance_layout.addWidget(keepalive_label, 0, 2)
        
        layout.addWidget(performance_group)
        
        # Development/Debug Group
        debug_group = QGroupBox("Development & Debug")
        debug_layout = QVBoxLayout(debug_group)
        
        verbose_checkbox = QCheckBox("Enable Verbose Logging")
        verbose_checkbox.setToolTip("Enable detailed logging for troubleshooting")
        debug_layout.addWidget(verbose_checkbox)
        
        debug_checkbox = QCheckBox("Enable Debug Mode")
        debug_checkbox.setToolTip("Enable debug mode with additional validation")
        debug_layout.addWidget(debug_checkbox)
        
        layout.addWidget(debug_group)
        layout.addStretch()
        
        return tab
    
    def _create_dialog_buttons(self, parent_layout: QVBoxLayout):
        """
        Create standard dialog buttons
        
        Args:
            parent_layout: Parent layout to add buttons to
        """
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        parent_layout.addWidget(separator)
        
        # Create button box with standard buttons
        button_box = QDialogButtonBox()
        
        # OK button
        ok_button = button_box.addButton(QDialogButtonBox.Ok)
        ok_button.setText("💾 Save & Apply")
        ok_button.setToolTip("Save settings and apply changes")
        
        # Cancel button  
        cancel_button = button_box.addButton(QDialogButtonBox.Cancel)
        cancel_button.setText("❌ Cancel")
        cancel_button.setToolTip("Cancel changes and close dialog")
        
        # Reset button
        reset_button = button_box.addButton(QDialogButtonBox.Reset)
        reset_button.setText("🔄 Reset")
        reset_button.setToolTip("Reset to original settings")
        
        # Connect button signals
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self._on_reject)
        reset_button.clicked.connect(self._on_reset)
        
        parent_layout.addWidget(button_box)
    
    def _setup_styling(self):
        """
        Set up professional styling for the dialog with dark theme support
        
        Learning: Using centralized theme manager for consistent styling
        """
        # Use centralized theme manager
        theme_manager = get_theme_manager()
        stylesheet = theme_manager.get_stylesheet_for_widget('dialog')
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
        stylesheet = theme_manager.get_stylesheet_for_widget('dialog')
        self.setStyleSheet(stylesheet)
        
        self.logger.info(f"Theme changed to: {theme_mode.value}")
    
    def _setup_connections(self):
        """
        Set up signal-slot connections for the dialog
        """
        # Input validation connections
        self.host_input.textChanged.connect(self._validate_inputs)
        self.port_input.valueChanged.connect(self._validate_inputs)
        
        # Real-time settings change notifications
        if self.settings_manager:
            self.connection_config_changed.connect(
                self.settings_manager.update_connection_config
            )
    
    def _load_current_settings(self):
        """
        Load current settings into the dialog fields
        """
        if not self.settings_manager:
            return
        
        config = self.settings_manager.connection_config
        self.original_config = TallyConnectionConfig(
            host=config.host,
            port=config.port,
            timeout=config.timeout,
            retry_count=config.retry_count,
            enable_pooling=config.enable_pooling
        )
        
        # Populate fields with current settings
        self.host_input.setText(config.host)
        self.port_input.setValue(config.port)
        self.timeout_input.setValue(config.timeout)
        
        if self.retry_count_input:
            self.retry_count_input.setValue(config.retry_count)
        if self.connection_pool_checkbox:
            self.connection_pool_checkbox.setChecked(config.enable_pooling)
        
        # Load connection history
        self._load_connection_history()
        
        self.logger.info("Current settings loaded into dialog")
    
    def _load_connection_history(self):
        """
        Load connection history into the history list
        """
        if not self.settings_manager or not self.history_list:
            return
        
        history = getattr(self.settings_manager.settings, 'connection_history', [])
        self.history_list.clear()
        
        for entry in history[-10:]:  # Show last 10 connections
            item_text = f"{entry.get('host', 'Unknown')}:{entry.get('port', 'Unknown')}"
            timestamp = entry.get('timestamp', '')
            if timestamp:
                item_text += f" ({timestamp})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, entry)
            self.history_list.addItem(item)
    
    def _validate_inputs(self):
        """
        Validate all input fields and provide visual feedback
        """
        # Validate IP address
        host_valid = self.host_input.hasAcceptableInput() or self.host_input.text().strip() == ""
        self.host_input.setProperty("invalid", not host_valid)
        
        # Validate port (SpinBox handles this automatically)
        port_valid = 1 <= self.port_input.value() <= 65535
        
        # Update test button state
        can_test = host_valid and port_valid and self.host_input.text().strip()
        if self.test_button:
            self.test_button.setEnabled(can_test and not self._is_testing())
        
        # Refresh styling
        self.host_input.style().polish(self.host_input)
    
    def _is_testing(self) -> bool:
        """
        Check if connection test is currently running
        
        Returns:
            True if test is in progress
        """
        return (self.connection_test_worker and 
                self.connection_test_worker.isRunning())
    
    def _set_quick_connection(self, host: str, port: int):
        """
        Set quick connection parameters
        
        Args:
            host: Host address to set
            port: Port number to set
        """
        self.host_input.setText(host)
        self.port_input.setValue(port)
        self.logger.info(f"Quick connection set to {host}:{port}")
    
    def _on_connection_settings_changed(self):
        """
        Handle connection settings changes for validation
        """
        self._validate_inputs()
    
    def _on_test_connection(self):
        """
        Handle test connection button click
        """
        if self._is_testing():
            return
        
        host = self.host_input.text().strip()
        port = self.port_input.value()
        timeout = self.timeout_input.value()
        
        if not host:
            QMessageBox.warning(self, "Invalid Input", 
                              "Please enter a valid IP address or hostname.")
            return
        
        # Start connection test in background thread
        self.connection_test_worker = ConnectionTestWorker(host, port, timeout)
        
        # Connect worker signals
        self.connection_test_worker.test_started.connect(self._on_test_started)
        self.connection_test_worker.test_completed.connect(self._on_test_completed)
        self.connection_test_worker.progress_update.connect(self._on_test_progress)
        
        # Start the worker
        self.connection_test_worker.start()
        
        self.logger.info(f"Starting connection test to {host}:{port}")
    
    def _on_test_started(self):
        """
        Handle test started signal
        """
        self.test_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.test_results_text.setPlainText("Connection test in progress...\n")
    
    def _on_test_progress(self, message: str):
        """
        Handle test progress updates
        
        Args:
            message: Progress message
        """
        current_text = self.test_results_text.toPlainText()
        self.test_results_text.setPlainText(current_text + f"{message}\n")
        
        # Scroll to bottom
        cursor = self.test_results_text.textCursor()
        cursor.movePosition(cursor.End)
        self.test_results_text.setTextCursor(cursor)
    
    def _on_test_completed(self, success: bool, message: str):
        """
        Handle test completion
        
        Args:
            success: Whether test was successful
            message: Result message
        """
        self.test_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Add final result
        current_text = self.test_results_text.toPlainText()
        result_text = f"\n{message}\n"
        result_text += "=" * 50 + "\n"
        self.test_results_text.setPlainText(current_text + result_text)
        
        # Scroll to bottom
        cursor = self.test_results_text.textCursor()
        cursor.movePosition(cursor.End)
        self.test_results_text.setTextCursor(cursor)
        
        # Clean up worker
        if self.connection_test_worker:
            self.connection_test_worker.deleteLater()
            self.connection_test_worker = None
        
        self.logger.info(f"Connection test completed: {success}")
    
    def _on_history_item_selected(self, item: QListWidgetItem):
        """
        Handle history item double-click
        
        Args:
            item: Selected history item
        """
        self._load_selected_history()
    
    def _load_selected_history(self):
        """
        Load selected history item into current settings
        """
        current_item = self.history_list.currentItem()
        if not current_item:
            return
        
        entry = current_item.data(Qt.UserRole)
        if entry:
            self.host_input.setText(entry.get('host', ''))
            self.port_input.setValue(entry.get('port', 9000))
            self.timeout_input.setValue(entry.get('timeout', 10))
            
            self.logger.info(f"Loaded history entry: {entry.get('host')}:{entry.get('port')}")
    
    def _save_current_connection(self):
        """
        Save current connection settings to history
        """
        if not self.settings_manager:
            return
        
        # Create history entry
        entry = {
            'host': self.host_input.text().strip(),
            'port': self.port_input.value(),
            'timeout': self.timeout_input.value(),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to history (avoiding duplicates)
        history = getattr(self.settings_manager.settings, 'connection_history', [])
        
        # Remove existing entry for same host:port
        history = [h for h in history if not (
            h.get('host') == entry['host'] and h.get('port') == entry['port']
        )]
        
        # Add new entry
        history.append(entry)
        
        # Keep only last 20 entries
        if len(history) > 20:
            history = history[-20:]
        
        # Update settings
        self.settings_manager.settings.connection_history = history
        
        # Refresh history display
        self._load_connection_history()
        
        self.logger.info("Current connection saved to history")
    
    def _clear_connection_history(self):
        """
        Clear all connection history
        """
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all connection history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.settings_manager:
                self.settings_manager.settings.connection_history = []
            self.history_list.clear()
            self.logger.info("Connection history cleared")
    
    def _on_accept(self):
        """
        Handle OK button click - save settings and close
        """
        if not self._validate_and_apply_settings():
            return
        
        self.accept()
    
    def _on_reject(self):
        """
        Handle Cancel button click - discard changes and close
        """
        self.reject()
    
    def _on_reset(self):
        """
        Handle Reset button click - restore original settings
        """
        if self.original_config:
            self.host_input.setText(self.original_config.host)
            self.port_input.setValue(self.original_config.port)
            self.timeout_input.setValue(self.original_config.timeout)
            
            if self.retry_count_input:
                self.retry_count_input.setValue(self.original_config.retry_count)
            if self.connection_pool_checkbox:
                self.connection_pool_checkbox.setChecked(self.original_config.enable_pooling)
            
            self.logger.info("Settings reset to original values")
    
    def _validate_and_apply_settings(self) -> bool:
        """
        Validate current settings and apply them if valid
        
        Returns:
            True if settings are valid and applied, False otherwise
        """
        # Validate inputs
        host = self.host_input.text().strip()
        if not host:
            QMessageBox.warning(self, "Invalid Input", 
                              "Please enter a valid IP address or hostname.")
            return False
        
        # Create new configuration
        new_config = TallyConnectionConfig(
            host=host,
            port=self.port_input.value(),
            timeout=self.timeout_input.value(),
            retry_count=self.retry_count_input.value() if self.retry_count_input else 3,
            enable_pooling=self.connection_pool_checkbox.isChecked() if self.connection_pool_checkbox else True
        )
        
        # Apply settings through settings manager
        if self.settings_manager:
            self.settings_manager.update_connection_config(new_config)
            self.settings_manager.save_settings()
        
        # Emit signal for other components
        self.connection_config_changed.emit(new_config)
        
        # Save to history
        self._save_current_connection()
        
        self.logger.info("Settings validated and applied successfully")
        return True
    
    def closeEvent(self, event):
        """
        Handle dialog close event
        
        Args:
            event: Close event
        """
        # Clean up any running threads
        if self.connection_test_worker and self.connection_test_worker.isRunning():
            self.connection_test_worker.quit()
            self.connection_test_worker.wait()
        
        super().closeEvent(event)
        self.logger.info("Connection dialog closed")


if __name__ == "__main__":
    """
    Test the connection dialog independently
    """
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create test dialog
    dialog = ConnectionDialog()
    dialog.show()
    
    sys.exit(app.exec())
#!/usr/bin/env python3
"""
Manual Test Application for Advanced Logging System
TallyPrime Integration Manager

This is a simplified test application to demonstrate and manually validate
the new Advanced Logging System features. It creates a minimal interface
focused specifically on showcasing the professional logging capabilities.

Features Demonstrated:
- Professional log widget with colored entries
- Advanced filtering by log level and content
- Real-time search with regex support
- Log export to TXT, CSV, and JSON formats
- Log rotation and size management
- Theme-aware styling
- Performance with large log volumes

Usage:
    python manual_test_advanced_logging.py

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
"""

import sys
import os
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QSpinBox, QCheckBox, QComboBox,
    QMessageBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

# Import the advanced log widget
from ui.widgets.log_widget import ProfessionalLogWidget


class AdvancedLoggingDemoWindow(QMainWindow):
    """
    Demonstration window for the Advanced Logging System
    
    This window provides a focused interface to showcase all the
    advanced logging capabilities without the complexity of the
    full TallyPrime integration application.
    """
    
    def __init__(self):
        """Initialize the demo window"""
        super().__init__()
        
        # Window properties
        self.setWindowTitle("🔍 Advanced Logging System Demo - TallyPrime Integration Manager")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Demo data for realistic log generation
        self.demo_sources = [
            "TallyConnector", "DataReader", "MainWindow", "ConnectionWidget",
            "DataTableWidget", "SettingsManager", "ExportWorker", "ThemeManager"
        ]
        
        self.demo_operations = [
            "Connection established successfully",
            "Loading company information",
            "Fetching ledger accounts from TallyPrime",
            "Processing transaction data",
            "Updating user interface",
            "Saving configuration settings",
            "Exporting data to CSV format",
            "Applying theme changes",
            "Validating input parameters",
            "Refreshing data display",
            "Managing cache operations",
            "Handling user interaction",
            "Performing background operations",
            "Synchronizing with TallyPrime",
            "Optimizing performance settings"
        ]
        
        self.demo_warnings = [
            "Connection timeout detected, retrying...",
            "Large dataset detected, may take longer to load",
            "Cache size approaching limit",
            "Network latency detected",
            "Disk space running low",
            "Some data fields are empty",
            "Outdated configuration detected"
        ]
        
        self.demo_errors = [
            "Failed to connect to TallyPrime server",
            "Invalid XML response received",
            "Database connection lost",
            "File permission denied",
            "Network connection interrupted",
            "Authentication failed",
            "Memory allocation error"
        ]
        
        # Auto-generate timer
        self.auto_log_timer = QTimer()
        self.auto_log_timer.timeout.connect(self._generate_random_log)
        
        # Set up the UI
        self._setup_ui()
        
        # Add initial demonstration logs
        self._add_initial_demo_logs()
    
    def _setup_ui(self):
        """Set up the user interface"""
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Create splitter for control panel and log widget
        splitter = QSplitter(Qt.Horizontal)
        
        # Control panel
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # Advanced log widget
        self.log_widget = ProfessionalLogWidget(self)
        splitter.addWidget(self.log_widget)
        
        # Set splitter proportions (30% control, 70% log)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter, 1)
        
        # Status bar
        self.statusBar().showMessage("🚀 Advanced Logging System Demo Ready")
        
        # Connect log widget signals
        self.log_widget.log_exported.connect(self._on_log_exported)
        self.log_widget.filter_changed.connect(self._on_filter_changed)
        
    def _create_header(self) -> QWidget:
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🔍 Advanced Logging System Demonstration")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "This demo showcases the professional logging capabilities of the TallyPrime Integration Manager. "
            "Experience advanced filtering, search, export, and real-time log management features."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin: 5px;")
        header_layout.addWidget(desc_label)
        
        return header_frame
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with demo functions"""
        control_widget = QWidget()
        control_widget.setFixedWidth(280)
        control_layout = QVBoxLayout(control_widget)
        
        # Manual Log Generation
        manual_group = QGroupBox("📝 Manual Log Generation")
        manual_layout = QVBoxLayout(manual_group)
        
        # Individual log level buttons
        log_levels = [
            ("🔵 Add INFO Log", "INFO", "#17a2b8"),
            ("🟡 Add WARNING Log", "WARNING", "#ffc107"),
            ("🔴 Add ERROR Log", "ERROR", "#dc3545"),
            ("🟢 Add SUCCESS Log", "INFO", "#28a745"),
            ("⚪ Add DEBUG Log", "DEBUG", "#6c757d")
        ]
        
        for text, level, color in log_levels:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}; 
                    color: white; 
                    border: none; 
                    padding: 8px; 
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
            """)
            btn.clicked.connect(lambda checked, l=level: self._add_manual_log(l))
            manual_layout.addWidget(btn)
        
        control_layout.addWidget(manual_group)
        
        # Auto Generation
        auto_group = QGroupBox("🤖 Automatic Log Generation")
        auto_layout = QVBoxLayout(auto_group)
        
        # Auto generation controls
        auto_controls_layout = QHBoxLayout()
        
        self.auto_interval_spinbox = QSpinBox()
        self.auto_interval_spinbox.setRange(100, 5000)
        self.auto_interval_spinbox.setValue(1000)
        self.auto_interval_spinbox.setSuffix(" ms")
        auto_controls_layout.addWidget(QLabel("Interval:"))
        auto_controls_layout.addWidget(self.auto_interval_spinbox)
        
        auto_layout.addLayout(auto_controls_layout)
        
        # Auto generation buttons
        self.start_auto_button = QPushButton("▶️ Start Auto Generation")
        self.start_auto_button.clicked.connect(self._start_auto_generation)
        auto_layout.addWidget(self.start_auto_button)
        
        self.stop_auto_button = QPushButton("⏸️ Stop Auto Generation")
        self.stop_auto_button.clicked.connect(self._stop_auto_generation)
        self.stop_auto_button.setEnabled(False)
        auto_layout.addWidget(self.stop_auto_button)
        
        control_layout.addWidget(auto_group)
        
        # Bulk Operations
        bulk_group = QGroupBox("📊 Bulk Operations")
        bulk_layout = QVBoxLayout(bulk_group)
        
        # Bulk count selection
        bulk_controls_layout = QHBoxLayout()
        
        self.bulk_count_spinbox = QSpinBox()
        self.bulk_count_spinbox.setRange(10, 1000)
        self.bulk_count_spinbox.setValue(100)
        bulk_controls_layout.addWidget(QLabel("Count:"))
        bulk_controls_layout.addWidget(self.bulk_count_spinbox)
        
        bulk_layout.addLayout(bulk_controls_layout)
        
        # Bulk generation buttons
        bulk_mixed_button = QPushButton("🎲 Generate Mixed Logs")
        bulk_mixed_button.clicked.connect(self._generate_bulk_mixed)
        bulk_layout.addWidget(bulk_mixed_button)
        
        bulk_errors_button = QPushButton("⚠️ Generate Error Logs")
        bulk_errors_button.clicked.connect(self._generate_bulk_errors)
        bulk_layout.addWidget(bulk_errors_button)
        
        control_layout.addWidget(bulk_group)
        
        # Performance Testing
        perf_group = QGroupBox("⚡ Performance Testing")
        perf_layout = QVBoxLayout(perf_group)
        
        perf_1k_button = QPushButton("🚀 Add 1,000 Logs")
        perf_1k_button.clicked.connect(lambda: self._performance_test(1000))
        perf_layout.addWidget(perf_1k_button)
        
        perf_5k_button = QPushButton("🚀 Add 5,000 Logs")
        perf_5k_button.clicked.connect(lambda: self._performance_test(5000))
        perf_layout.addWidget(perf_5k_button)
        
        control_layout.addWidget(perf_group)
        
        # Demo Scenarios
        scenario_group = QGroupBox("🎬 Demo Scenarios")
        scenario_layout = QVBoxLayout(scenario_group)
        
        scenario_connection_button = QPushButton("🔗 TallyPrime Connection")
        scenario_connection_button.clicked.connect(self._demo_connection_scenario)
        scenario_layout.addWidget(scenario_connection_button)
        
        scenario_data_button = QPushButton("📊 Data Loading")
        scenario_data_button.clicked.connect(self._demo_data_loading_scenario)
        scenario_layout.addWidget(scenario_data_button)
        
        scenario_error_button = QPushButton("❌ Error Handling")
        scenario_error_button.clicked.connect(self._demo_error_scenario)
        scenario_layout.addWidget(scenario_error_button)
        
        control_layout.addWidget(scenario_group)
        
        control_layout.addStretch()
        
        return control_widget
    
    def _add_initial_demo_logs(self):
        """Add initial demonstration logs"""
        
        initial_logs = [
            ("🚀 Advanced Logging System Demo started", "INFO", "DemoApp"),
            ("🔧 Initializing professional log widget components", "INFO", "LogWidget"),
            ("📊 Demo data sources loaded successfully", "INFO", "DemoApp"),
            ("✅ All systems ready for logging demonstration", "INFO", "DemoApp"),
            ("💡 Try the controls on the left to generate different types of logs!", "INFO", "DemoApp")
        ]
        
        for message, level, source in initial_logs:
            self.log_widget.add_log_entry(message, level, source)
    
    def _add_manual_log(self, level: str):
        """Add a manual log entry of specified level"""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "INFO":
            operation = random.choice(self.demo_operations)
            message = f"🔵 [{timestamp}] {operation}"
        elif level == "WARNING":
            warning = random.choice(self.demo_warnings)
            message = f"🟡 [{timestamp}] {warning}"
        elif level == "ERROR":
            error = random.choice(self.demo_errors)
            message = f"🔴 [{timestamp}] {error}"
        elif level == "DEBUG":
            message = f"⚪ [{timestamp}] Debug: Processing internal state information"
        else:
            message = f"✅ [{timestamp}] Operation completed successfully"
        
        source = random.choice(self.demo_sources)
        self.log_widget.add_log_entry(message, level, source)
        
        # Update status bar
        self.statusBar().showMessage(f"Added {level} log entry", 2000)
    
    def _start_auto_generation(self):
        """Start automatic log generation"""
        interval = self.auto_interval_spinbox.value()
        self.auto_log_timer.start(interval)
        
        self.start_auto_button.setEnabled(False)
        self.stop_auto_button.setEnabled(True)
        
        self.log_widget.add_log_entry("🤖 Automatic log generation started", "INFO", "DemoApp")
        self.statusBar().showMessage(f"Auto-generation started (interval: {interval}ms)")
    
    def _stop_auto_generation(self):
        """Stop automatic log generation"""
        self.auto_log_timer.stop()
        
        self.start_auto_button.setEnabled(True)
        self.stop_auto_button.setEnabled(False)
        
        self.log_widget.add_log_entry("⏸️ Automatic log generation stopped", "INFO", "DemoApp")
        self.statusBar().showMessage("Auto-generation stopped")
    
    def _generate_random_log(self):
        """Generate a random log entry for auto-generation"""
        
        # Weighted random level selection (more INFO, some WARNING/ERROR)
        levels = ["INFO"] * 6 + ["WARNING"] * 2 + ["ERROR"] * 1 + ["DEBUG"] * 1
        level = random.choice(levels)
        
        self._add_manual_log(level)
    
    def _generate_bulk_mixed(self):
        """Generate bulk mixed log entries"""
        count = self.bulk_count_spinbox.value()
        
        self.log_widget.add_log_entry(f"📊 Generating {count} mixed log entries...", "INFO", "DemoApp")
        self.statusBar().showMessage(f"Generating {count} mixed logs...")
        
        start_time = time.time()
        
        for i in range(count):
            # Mix of different levels
            if i % 10 == 0:
                level = "ERROR"
            elif i % 5 == 0:
                level = "WARNING"
            elif i % 20 == 0:
                level = "DEBUG"
            else:
                level = "INFO"
                
            self._add_manual_log(level)
            
            # Process events periodically to keep UI responsive
            if i % 50 == 0:
                QApplication.processEvents()
        
        elapsed = time.time() - start_time
        
        completion_msg = f"✅ Generated {count} mixed logs in {elapsed:.2f} seconds"
        self.log_widget.add_log_entry(completion_msg, "INFO", "DemoApp")
        self.statusBar().showMessage(f"Bulk generation completed ({elapsed:.2f}s)")
    
    def _generate_bulk_errors(self):
        """Generate bulk error log entries"""
        count = self.bulk_count_spinbox.value()
        
        self.log_widget.add_log_entry(f"⚠️ Generating {count} error log entries...", "WARNING", "DemoApp")
        self.statusBar().showMessage(f"Generating {count} error logs...")
        
        start_time = time.time()
        
        for i in range(count):
            self._add_manual_log("ERROR")
            
            if i % 50 == 0:
                QApplication.processEvents()
        
        elapsed = time.time() - start_time
        
        completion_msg = f"❌ Generated {count} error logs in {elapsed:.2f} seconds"
        self.log_widget.add_log_entry(completion_msg, "ERROR", "DemoApp")
        self.statusBar().showMessage(f"Error bulk generation completed ({elapsed:.2f}s)")
    
    def _performance_test(self, count: int):
        """Run performance test with specified number of entries"""
        
        self.log_widget.add_log_entry(f"⚡ Starting performance test with {count} log entries...", "INFO", "PerformanceTest")
        self.statusBar().showMessage(f"Performance test started ({count} entries)...")
        
        # Disable UI during test
        self.setEnabled(False)
        QApplication.processEvents()
        
        start_time = time.time()
        
        try:
            for i in range(count):
                # Realistic mix of log levels
                if i % 100 == 0:
                    level = "ERROR"
                elif i % 25 == 0:
                    level = "WARNING"
                elif i % 50 == 0:
                    level = "DEBUG"
                else:
                    level = "INFO"
                
                message = f"Performance test entry {i+1}/{count} - {random.choice(self.demo_operations)}"
                source = f"PerfTest{i%10}"
                
                self.log_widget.add_log_entry(message, level, source)
                
                # Process events occasionally to prevent complete UI freeze
                if i % 200 == 0:
                    QApplication.processEvents()
            
            elapsed = time.time() - start_time
            
            completion_msg = (f"🏆 Performance test completed! "
                            f"{count} entries added in {elapsed:.2f} seconds "
                            f"({count/elapsed:.1f} entries/sec)")
            
            self.log_widget.add_log_entry(completion_msg, "INFO", "PerformanceTest")
            self.statusBar().showMessage(f"Performance test completed: {elapsed:.2f}s ({count/elapsed:.1f} entries/sec)")
            
        finally:
            # Re-enable UI
            self.setEnabled(True)
    
    def _demo_connection_scenario(self):
        """Demonstrate a TallyPrime connection scenario"""
        
        scenario_logs = [
            ("🔍 Initiating TallyPrime connection sequence...", "INFO", "TallyConnector"),
            ("📡 Discovering TallyPrime instances on network", "INFO", "NetworkDiscovery"),
            ("✅ Found TallyPrime at 172.28.208.1:9000", "INFO", "NetworkDiscovery"),
            ("🔗 Establishing HTTP connection...", "INFO", "TallyConnector"),
            ("📋 Requesting company information", "INFO", "TallyConnector"),
            ("✅ Company 'Irya Smartec Pvt Ltd' connected successfully", "INFO", "TallyConnector"),
            ("📊 Loading company configuration", "INFO", "DataReader"),
            ("🔍 Retrieving ledger account structure", "INFO", "DataReader"),
            ("✅ Found 2,468 ledger accounts", "INFO", "DataReader"),
            ("🚀 TallyPrime connection established - Ready for operations", "INFO", "MainWindow")
        ]
        
        self._play_scenario(scenario_logs, "TallyPrime Connection Scenario")
    
    def _demo_data_loading_scenario(self):
        """Demonstrate a data loading scenario"""
        
        scenario_logs = [
            ("📊 Data loading operation initiated", "INFO", "DataReader"),
            ("🔍 Querying TallyPrime for ledger data", "INFO", "DataReader"),
            ("📈 Processing transaction history", "INFO", "DataReader"),
            ("⚠ Large dataset detected - enabling progress tracking", "WARNING", "DataReader"),
            ("🔄 Processing batch 1/10 (250 entries)", "INFO", "DataProcessor"),
            ("🔄 Processing batch 2/10 (500 entries)", "INFO", "DataProcessor"),
            ("🔄 Processing batch 3/10 (750 entries)", "INFO", "DataProcessor"),
            ("💾 Updating data cache for improved performance", "INFO", "CacheManager"),
            ("🔄 Processing remaining batches...", "INFO", "DataProcessor"),
            ("✅ Data loading completed - 2,468 records processed", "INFO", "DataReader"),
            ("🎯 Data display updated successfully", "INFO", "DataTableWidget")
        ]
        
        self._play_scenario(scenario_logs, "Data Loading Scenario")
    
    def _demo_error_scenario(self):
        """Demonstrate an error handling scenario"""
        
        scenario_logs = [
            ("🔗 Attempting TallyPrime connection", "INFO", "TallyConnector"),
            ("⚠ Connection timeout detected - retrying...", "WARNING", "TallyConnector"),
            ("🔄 Retry attempt 1/3", "INFO", "TallyConnector"),
            ("❌ Connection failed - TallyPrime not responding", "ERROR", "TallyConnector"),
            ("🔄 Retry attempt 2/3", "INFO", "TallyConnector"),
            ("❌ HTTP timeout - network may be unstable", "ERROR", "NetworkManager"),
            ("⚠ Falling back to cached data", "WARNING", "CacheManager"),
            ("✅ Cached data loaded successfully", "INFO", "CacheManager"),
            ("💡 Suggestion: Check TallyPrime service and network connection", "INFO", "ErrorHandler"),
            ("🔔 User notification sent: Connection issue detected", "INFO", "NotificationManager"),
            ("🛠 Error recovery completed - Application remains functional", "INFO", "MainWindow")
        ]
        
        self._play_scenario(scenario_logs, "Error Handling Scenario")
    
    def _play_scenario(self, scenario_logs, scenario_name):
        """Play a scenario with timed log entries"""
        
        self.log_widget.add_log_entry(f"🎬 Starting scenario: {scenario_name}", "INFO", "DemoApp")
        self.statusBar().showMessage(f"Playing scenario: {scenario_name}")
        
        # Use a timer to add logs with realistic timing
        self.scenario_index = 0
        self.scenario_logs = scenario_logs
        
        self.scenario_timer = QTimer()
        self.scenario_timer.timeout.connect(self._add_next_scenario_log)
        self.scenario_timer.start(800)  # 800ms between log entries
    
    def _add_next_scenario_log(self):
        """Add the next log entry in the scenario"""
        
        if self.scenario_index < len(self.scenario_logs):
            message, level, source = self.scenario_logs[self.scenario_index]
            self.log_widget.add_log_entry(message, level, source)
            self.scenario_index += 1
        else:
            # Scenario completed
            self.scenario_timer.stop()
            self.log_widget.add_log_entry("🎬 Scenario completed", "INFO", "DemoApp")
            self.statusBar().showMessage("Scenario completed", 3000)
    
    def _on_log_exported(self, file_path: str, success: bool, error_message: str):
        """Handle log export completion"""
        if success:
            QMessageBox.information(
                self,
                "Export Successful",
                f"Logs successfully exported to:\n{file_path}\n\nYou can now open the file to view the exported logs."
            )
            self.statusBar().showMessage(f"Logs exported to {file_path}", 5000)
        else:
            QMessageBox.critical(
                self,
                "Export Failed", 
                f"Log export failed:\n{error_message}"
            )
            self.statusBar().showMessage(f"Export failed: {error_message}", 5000)
    
    def _on_filter_changed(self, level_filter: str, text_filter: str):
        """Handle filter changes"""
        filter_info = []
        if level_filter != "ALL":
            filter_info.append(f"Level: {level_filter}")
        if text_filter:
            filter_info.append(f"Search: '{text_filter[:20]}{'...' if len(text_filter) > 20 else ''}'")
        
        if filter_info:
            status = f"Filters applied: {', '.join(filter_info)}"
        else:
            status = "No filters applied"
            
        self.statusBar().showMessage(status, 3000)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop any running timers
        if hasattr(self, 'auto_log_timer') and self.auto_log_timer.isActive():
            self.auto_log_timer.stop()
        if hasattr(self, 'scenario_timer') and self.scenario_timer.isActive():
            self.scenario_timer.stop()
        
        event.accept()


def main():
    """Main function to run the advanced logging demo"""
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Advanced Logging System Demo")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TallyPrime Integration Manager")
    
    try:
        # Create and show the demo window
        demo_window = AdvancedLoggingDemoWindow()
        demo_window.show()
        
        print("🚀 Advanced Logging System Demo started!")
        print("📋 Features to try:")
        print("   • Manual log generation with different levels")
        print("   • Automatic log generation with configurable timing")
        print("   • Bulk operations for performance testing") 
        print("   • Realistic demo scenarios (Connection, Data Loading, Error Handling)")
        print("   • Advanced filtering by level and content")
        print("   • Search functionality with regex support")
        print("   • Log export to TXT, CSV, and JSON formats")
        print("   • Theme-aware styling and professional appearance")
        print("   • Performance testing with large log volumes")
        print("")
        print("💡 Use the controls on the left side to generate different types of logs!")
        print("🔍 Try the filtering and search features in the log widget!")
        print("💾 Test the export functionality to save logs in different formats!")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error starting demo: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
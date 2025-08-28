"""
TallyPrime Integration Manager - Advanced Professional Log Widget
Professional Desktop Application using PySide6/Qt6

This module contains a comprehensive logging widget that provides:
- Real-time colored log display with level-based styling
- Advanced filtering by log level, content, and time range
- Professional search functionality with regex support
- Log export to multiple formats (TXT, CSV, JSON)
- Log rotation and size management
- Auto-scroll and manual positioning controls
- Professional UI with theme integration

Key Learning Points:
- QTextEdit advanced usage for log display
- Custom filtering and search implementation
- Signal-slot architecture for real-time updates
- Professional UI controls and layout management
- File I/O operations for log export
- Performance optimization for large log volumes

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)  
Framework: PySide6 (Qt6)
"""

import re
import json
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# PySide6/Qt6 imports for GUI components
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QLineEdit, QCheckBox, QSpinBox,
    QGroupBox, QSplitter, QFileDialog, QMessageBox, QProgressBar,
    QToolBar, QSizePolicy, QFrame, QScrollArea, QApplication
)

from PySide6.QtCore import (
    Qt, Signal, QTimer, QThread, QMutex, QMutexLocker,
    QDateTime, QFileInfo
)

from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, QAction, 
    QKeySequence, QTextDocument, QIcon
)

# Import theme manager for professional styling
try:
    from ui.resources.styles.theme_manager import ThemeManager
except ImportError:
    # Fallback if theme manager not available
    ThemeManager = None


@dataclass
class LogEntry:
    """
    Professional log entry data structure
    
    This class represents a single log entry with comprehensive metadata
    for advanced filtering, searching, and export capabilities.
    
    Learning Points:
    - dataclass decorator provides automatic constructor and comparison methods
    - Type hints ensure data integrity and IDE support
    - Structured data enables advanced log operations
    """
    timestamp: datetime
    level: str
    message: str
    source: str = "Application"
    thread_id: Optional[int] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert log entry to dictionary for JSON export"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def matches_filter(self, 
                      level_filter: Optional[str] = None,
                      text_filter: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      use_regex: bool = False) -> bool:
        """
        Check if log entry matches filtering criteria
        
        Args:
            level_filter: Log level to filter by (None for all levels)
            text_filter: Text to search for in message (None for all)
            start_time: Earliest timestamp to include
            end_time: Latest timestamp to include
            use_regex: Whether to treat text_filter as regex pattern
            
        Returns:
            bool: True if entry matches all criteria
        """
        # Level filtering
        if level_filter and level_filter != "ALL" and self.level != level_filter:
            return False
            
        # Time range filtering
        if start_time and self.timestamp < start_time:
            return False
        if end_time and self.timestamp > end_time:
            return False
            
        # Text filtering
        if text_filter:
            text_to_search = self.message.lower()
            if use_regex:
                try:
                    if not re.search(text_filter.lower(), text_to_search):
                        return False
                except re.error:
                    # Invalid regex, fall back to simple text search
                    if text_filter.lower() not in text_to_search:
                        return False
            else:
                if text_filter.lower() not in text_to_search:
                    return False
                    
        return True


class LogExportWorker(QThread):
    """
    Background worker thread for log export operations
    
    This worker handles log export to different formats without blocking the UI.
    Demonstrates professional threading patterns in Qt6 applications.
    
    Learning Points:
    - QThread usage for background operations  
    - Signal-slot communication between threads
    - Progress reporting during long operations
    - Error handling in worker threads
    """
    
    # Signals for communicating with the main thread
    progress_updated = Signal(int, str)  # progress percentage, status message
    export_completed = Signal(str, bool, str)  # filepath, success, error_message
    
    def __init__(self, log_entries: List[LogEntry], file_path: str, export_format: str):
        """
        Initialize the export worker
        
        Args:
            log_entries: List of log entries to export
            file_path: Destination file path
            export_format: Export format ('txt', 'csv', 'json')
        """
        super().__init__()
        self.log_entries = log_entries
        self.file_path = file_path
        self.export_format = export_format.lower()
        self.mutex = QMutex()  # Thread safety for shared data
    
    def run(self):
        """Main worker thread execution"""
        try:
            total_entries = len(self.log_entries)
            self.progress_updated.emit(0, "Starting export...")
            
            # Determine export method based on format
            if self.export_format == 'txt':
                self._export_to_text()
            elif self.export_format == 'csv':
                self._export_to_csv()
            elif self.export_format == 'json':
                self._export_to_json()
            else:
                raise ValueError(f"Unsupported export format: {self.export_format}")
                
            self.progress_updated.emit(100, "Export completed successfully")
            self.export_completed.emit(self.file_path, True, "")
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.progress_updated.emit(0, error_msg)
            self.export_completed.emit(self.file_path, False, error_msg)
    
    def _export_to_text(self):
        """Export logs to plain text format"""
        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(f"TallyPrime Integration Manager - Log Export\n")
            file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Total entries: {len(self.log_entries)}\n")
            file.write("=" * 80 + "\n\n")
            
            for i, entry in enumerate(self.log_entries):
                # Update progress periodically
                if i % 100 == 0:
                    progress = int((i / len(self.log_entries)) * 100)
                    self.progress_updated.emit(progress, f"Exporting entry {i+1}/{len(self.log_entries)}")
                
                # Format timestamp
                timestamp_str = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                # Write log entry
                file.write(f"[{timestamp_str}] {entry.level.upper():8} | {entry.message}\n")
                if entry.source != "Application":
                    file.write(f"                           Source: {entry.source}\n")
                file.write("\n")
    
    def _export_to_csv(self):
        """Export logs to CSV format"""
        with open(self.file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header
            writer.writerow(['Timestamp', 'Level', 'Message', 'Source', 'Thread ID', 'Session ID'])
            
            # Write data
            for i, entry in enumerate(self.log_entries):
                if i % 100 == 0:
                    progress = int((i / len(self.log_entries)) * 100)
                    self.progress_updated.emit(progress, f"Exporting entry {i+1}/{len(self.log_entries)}")
                
                writer.writerow([
                    entry.timestamp.isoformat(),
                    entry.level,
                    entry.message,
                    entry.source,
                    entry.thread_id,
                    entry.session_id
                ])
    
    def _export_to_json(self):
        """Export logs to JSON format"""
        # Convert log entries to dictionaries
        log_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_entries': len(self.log_entries),
                'application': 'TallyPrime Integration Manager'
            },
            'logs': []
        }
        
        for i, entry in enumerate(self.log_entries):
            if i % 100 == 0:
                progress = int((i / len(self.log_entries)) * 100)
                self.progress_updated.emit(progress, f"Exporting entry {i+1}/{len(self.log_entries)}")
            
            log_data['logs'].append(entry.to_dict())
        
        # Write JSON file with proper formatting
        with open(self.file_path, 'w', encoding='utf-8') as file:
            json.dump(log_data, file, indent=2, ensure_ascii=False)


class ProfessionalLogWidget(QWidget):
    """
    Advanced Professional Log Display Widget
    
    This widget provides comprehensive logging capabilities including:
    - Real-time colored log display with professional formatting
    - Advanced filtering by level, content, and time range
    - Professional search with regex support and highlighting
    - Export functionality to multiple formats
    - Log rotation and size management
    - Performance optimization for large log volumes
    
    Learning Points:
    - Advanced QTextEdit manipulation for colored logs
    - Custom filtering and search implementation
    - Background threading for export operations
    - Professional UI design with control panels
    - Signal-slot architecture for component communication
    - Performance considerations for real-time logging
    
    Signals:
        log_exported: Emitted when log export is completed
        filter_changed: Emitted when log filter settings change
    """
    
    # Custom signals for external communication
    log_exported = Signal(str, bool, str)  # filepath, success, error_message
    filter_changed = Signal(str, str)      # level_filter, text_filter
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the professional log widget
        
        Args:
            parent: Parent widget (usually the main window)
        """
        super().__init__(parent)
        
        # Set up logging for this widget
        self.logger = logging.getLogger(__name__)
        
        # Log storage and management
        self.log_entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.max_entries = 10000  # Maximum log entries to keep in memory
        self.auto_scroll = True
        
        # Filtering and search state
        self.current_level_filter = "ALL"
        self.current_text_filter = ""
        self.use_regex_search = False
        self.search_highlights: List[Tuple[int, int]] = []  # (start, length) pairs
        
        # Thread safety
        self.log_mutex = QMutex()
        
        # Export worker thread
        self.export_worker: Optional[LogExportWorker] = None
        
        # Theme integration
        self.theme_manager = ThemeManager() if ThemeManager else None
        
        # Initialize the widget
        self._setup_ui()
        self._connect_signals()
        self._apply_initial_styling()
        
        # Add some welcome log entries
        self._add_welcome_logs()
        
        self.logger.info("Professional log widget initialized successfully")
    
    def _setup_ui(self):
        """
        Set up the user interface components
        
        This method creates the complete UI layout including:
        - Control panel with filtering and search controls
        - Main log display area with syntax highlighting
        - Export controls and progress indicators
        - Status information and statistics
        
        Learning: Complex UI setup is separated into logical sections
        """
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create header section
        header_section = self._create_header_section()
        main_layout.addWidget(header_section)
        
        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Create main log display
        log_display_section = self._create_log_display_section()
        main_layout.addWidget(log_display_section, 1)  # Give it stretch factor
        
        # Create status section
        status_section = self._create_status_section()
        main_layout.addWidget(status_section)
        
        self.logger.debug("UI setup completed successfully")
    
    def _create_header_section(self) -> QWidget:
        """Create the header section with title and basic info"""
        header_widget = QFrame()
        header_widget.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header_widget)
        
        # Title label
        title_label = QLabel("🔍 Advanced Operations Log")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 4px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Auto-scroll control
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.setToolTip("Automatically scroll to newest log entries")
        header_layout.addWidget(self.auto_scroll_checkbox)
        
        return header_widget
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with filtering and search controls"""
        control_group = QGroupBox("Log Controls")
        control_layout = QVBoxLayout(control_group)
        
        # First row: Level filtering and search
        first_row_layout = QHBoxLayout()
        
        # Log level filter
        first_row_layout.addWidget(QLabel("Level:"))
        self.level_filter_combo = QComboBox()
        self.level_filter_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter_combo.setCurrentText("ALL")
        self.level_filter_combo.setToolTip("Filter logs by severity level")
        first_row_layout.addWidget(self.level_filter_combo)
        
        first_row_layout.addSpacing(20)
        
        # Search controls
        first_row_layout.addWidget(QLabel("Search:"))
        self.search_line_edit = QLineEdit()
        self.search_line_edit.setPlaceholderText("Enter search text or regex pattern...")
        self.search_line_edit.setToolTip("Search log messages (supports regex if enabled)")
        first_row_layout.addWidget(self.search_line_edit)
        
        # Regex checkbox
        self.regex_checkbox = QCheckBox("Regex")
        self.regex_checkbox.setToolTip("Enable regular expression search")
        first_row_layout.addWidget(self.regex_checkbox)
        
        # Search buttons
        self.search_button = QPushButton("🔍 Search")
        self.search_button.setToolTip("Search log entries")
        first_row_layout.addWidget(self.search_button)
        
        self.clear_search_button = QPushButton("✕ Clear")
        self.clear_search_button.setToolTip("Clear search and show all logs")
        first_row_layout.addWidget(self.clear_search_button)
        
        control_layout.addLayout(first_row_layout)
        
        # Second row: Export and management controls
        second_row_layout = QHBoxLayout()
        
        # Log management controls
        second_row_layout.addWidget(QLabel("Max entries:"))
        self.max_entries_spinbox = QSpinBox()
        self.max_entries_spinbox.setRange(1000, 50000)
        self.max_entries_spinbox.setValue(self.max_entries)
        self.max_entries_spinbox.setSingleStep(1000)
        self.max_entries_spinbox.setToolTip("Maximum number of log entries to keep in memory")
        second_row_layout.addWidget(self.max_entries_spinbox)
        
        second_row_layout.addStretch()
        
        # Export controls
        self.export_button = QPushButton("💾 Export Logs")
        self.export_button.setToolTip("Export logs to file (TXT, CSV, or JSON)")
        second_row_layout.addWidget(self.export_button)
        
        self.clear_logs_button = QPushButton("🗑️ Clear Logs")
        self.clear_logs_button.setToolTip("Clear all log entries")
        second_row_layout.addWidget(self.clear_logs_button)
        
        control_layout.addLayout(second_row_layout)
        
        return control_group
    
    def _create_log_display_section(self) -> QWidget:
        """Create the main log display area with professional formatting"""
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        display_layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress bar for export operations (initially hidden)
        self.export_progress_bar = QProgressBar()
        self.export_progress_bar.setVisible(False)
        display_layout.addWidget(self.export_progress_bar)
        
        # Main log text display
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Configure the text edit for optimal log display
        font = QFont("Consolas", 9)  # Monospace font for proper alignment
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.log_text_edit.setFont(font)
        
        # Set initial size and scroll behavior
        self.log_text_edit.setMinimumHeight(200)
        self.log_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        display_layout.addWidget(self.log_text_edit)
        
        return display_widget
    
    def _create_status_section(self) -> QWidget:
        """Create the status section with log statistics"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        # Status labels
        self.total_entries_label = QLabel("Total: 0")
        self.total_entries_label.setToolTip("Total number of log entries")
        status_layout.addWidget(self.total_entries_label)
        
        status_layout.addSpacing(20)
        
        self.filtered_entries_label = QLabel("Filtered: 0")
        self.filtered_entries_label.setToolTip("Number of entries matching current filter")
        status_layout.addWidget(self.filtered_entries_label)
        
        status_layout.addSpacing(20)
        
        self.last_update_label = QLabel("Last update: Never")
        self.last_update_label.setToolTip("Timestamp of most recent log entry")
        status_layout.addWidget(self.last_update_label)
        
        status_layout.addStretch()
        
        # Export status
        self.export_status_label = QLabel("")
        status_layout.addWidget(self.export_status_label)
        
        return status_frame
    
    def _connect_signals(self):
        """Connect all signal-slot pairs for widget interaction"""
        
        # Control panel signals
        self.level_filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self.search_line_edit.textChanged.connect(self._on_search_text_changed)
        self.search_line_edit.returnPressed.connect(self._on_search_requested)
        self.regex_checkbox.toggled.connect(self._on_regex_toggled)
        self.search_button.clicked.connect(self._on_search_requested)
        self.clear_search_button.clicked.connect(self._on_clear_search)
        
        # Management controls
        self.max_entries_spinbox.valueChanged.connect(self._on_max_entries_changed)
        self.auto_scroll_checkbox.toggled.connect(self._on_auto_scroll_toggled)
        
        # Action buttons
        self.export_button.clicked.connect(self._on_export_requested)
        self.clear_logs_button.clicked.connect(self._on_clear_logs)
        
        self.logger.debug("Signal connections established")
    
    def _apply_initial_styling(self):
        """Apply initial styling based on current theme"""
        
        if self.theme_manager:
            colors = self.theme_manager.colors
            is_dark = self.theme_manager.is_dark_theme
        else:
            # Fallback colors if theme manager not available
            colors = {
                'background': '#ffffff',
                'surface': '#f8f9fa',
                'text_primary': '#2c3e50',
                'text_secondary': '#6c757d',
                'border': '#dee2e6'
            }
            is_dark = False
        
        # Style the log text display
        log_bg = '#1a1a1a' if is_dark else '#ffffff'
        log_text = '#e0e0e0' if is_dark else '#2c3e50'
        log_border = '#404040' if is_dark else '#dee2e6'
        
        self.log_text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {log_bg};
                color: {log_text};
                border: 1px solid {log_border};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {'#404040' if is_dark else '#e3f2fd'};
            }}
        """)
        
        self.logger.debug("Initial styling applied successfully")
    
    def _add_welcome_logs(self):
        """Add initial welcome log entries"""
        
        welcome_entries = [
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="🔍 Advanced Logging System initialized successfully",
                source="LogWidget"
            ),
            LogEntry(
                timestamp=datetime.now(),
                level="INFO", 
                message="📊 Ready to capture application events and operations",
                source="LogWidget"
            ),
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="⚡ Features: Color coding, filtering, search, export, and more",
                source="LogWidget"
            )
        ]
        
        for entry in welcome_entries:
            self._add_log_entry_internal(entry)
    
    # Public API methods
    
    def add_log_entry(self, 
                     message: str, 
                     level: str = "INFO", 
                     source: str = "Application",
                     timestamp: Optional[datetime] = None):
        """
        Add a new log entry to the widget
        
        This is the main public API method for adding log entries.
        It provides thread-safe logging with professional formatting.
        
        Args:
            message: The log message text
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            source: Source component that generated the log
            timestamp: Optional timestamp (uses current time if None)
        """
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create log entry object
        entry = LogEntry(
            timestamp=timestamp,
            level=level.upper(),
            message=message,
            source=source,
            thread_id=None  # Thread ID not critical for basic functionality
        )
        
        # Add to log (thread-safe)
        self._add_log_entry_internal(entry)
    
    def set_max_entries(self, max_entries: int):
        """Set the maximum number of log entries to keep in memory"""
        self.max_entries = max(1000, min(50000, max_entries))
        self.max_entries_spinbox.setValue(self.max_entries)
        self._trim_log_entries()
    
    def clear_logs(self):
        """Clear all log entries"""
        with QMutexLocker(self.log_mutex):
            self.log_entries.clear()
            self.filtered_entries.clear()
        
        self._refresh_display()
        self._update_status_labels()
        
        # Add a log entry about the clearing
        self.add_log_entry("🗑️ Log entries cleared by user", "INFO", "LogWidget")
    
    def export_logs(self, file_path: str, export_format: str = "txt"):
        """
        Export logs to file in specified format
        
        Args:
            file_path: Destination file path
            export_format: Export format ('txt', 'csv', 'json')
        """
        
        if self.export_worker and self.export_worker.isRunning():
            QMessageBox.information(self, "Export in Progress", 
                                  "A log export operation is already in progress. Please wait for it to complete.")
            return
        
        # Get current filtered entries for export
        with QMutexLocker(self.log_mutex):
            entries_to_export = self.filtered_entries.copy()
        
        if not entries_to_export:
            QMessageBox.information(self, "No Logs", "No log entries to export.")
            return
        
        # Start export worker thread
        self.export_worker = LogExportWorker(entries_to_export, file_path, export_format)
        self.export_worker.progress_updated.connect(self._on_export_progress)
        self.export_worker.export_completed.connect(self._on_export_completed)
        
        # Show progress bar
        self.export_progress_bar.setVisible(True)
        self.export_progress_bar.setValue(0)
        self.export_status_label.setText("Exporting logs...")
        self.export_button.setEnabled(False)
        
        self.export_worker.start()
        
        self.logger.info(f"Started log export to {file_path} in {export_format} format")
    
    # Internal implementation methods
    
    def _add_log_entry_internal(self, entry: LogEntry):
        """Internal method to add log entry with thread safety"""
        
        with QMutexLocker(self.log_mutex):
            # Add to main log storage
            self.log_entries.append(entry)
            
            # Trim entries if we exceed maximum
            if len(self.log_entries) > self.max_entries:
                # Remove oldest entries (keep most recent 90% when trimming)
                trim_count = len(self.log_entries) - int(self.max_entries * 0.9)
                self.log_entries = self.log_entries[trim_count:]
        
        # Update display (must be done on main thread)
        self._apply_filters_and_refresh()
        self._update_status_labels()
    
    def _apply_filters_and_refresh(self):
        """Apply current filters and refresh the display"""
        
        with QMutexLocker(self.log_mutex):
            # Apply current filters to get filtered entries
            self.filtered_entries = [
                entry for entry in self.log_entries
                if entry.matches_filter(
                    level_filter=self.current_level_filter,
                    text_filter=self.current_text_filter,
                    use_regex=self.use_regex_search
                )
            ]
        
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the log display with current filtered entries"""
        
        # Clear current display
        self.log_text_edit.clear()
        
        # Get display entries (thread-safe copy)
        with QMutexLocker(self.log_mutex):
            display_entries = self.filtered_entries.copy()
        
        # Define colors for different log levels
        if self.theme_manager and hasattr(self.theme_manager, 'is_dark_theme'):
            is_dark = self.theme_manager.is_dark_theme
        else:
            # Fallback theme detection
            is_dark = self.palette().color(self.backgroundRole()).lightness() < 128
        
        level_colors = {
            'DEBUG': '#6c757d' if not is_dark else '#9ca3af',    # Gray
            'INFO': '#17a2b8' if not is_dark else '#06b6d4',     # Teal  
            'WARNING': '#ffc107' if not is_dark else '#f59e0b',  # Amber
            'ERROR': '#dc3545' if not is_dark else '#ef4444',    # Red
            'CRITICAL': '#6f42c1' if not is_dark else '#8b5cf6'  # Purple
        }
        
        # Add entries to display
        cursor = self.log_text_edit.textCursor()
        
        for entry in display_entries:
            # Format timestamp
            timestamp_str = entry.timestamp.strftime('%H:%M:%S.%f')[:-3]
            
            # Create formatted log line
            level_padded = entry.level.ljust(8)
            log_line = f"[{timestamp_str}] {level_padded} | {entry.message}"
            
            # Set color format for this log level
            char_format = QTextCharFormat()
            level_color = level_colors.get(entry.level, '#2c3e50' if not is_dark else '#e0e0e0')
            char_format.setForeground(QColor(level_color))
            
            # Apply formatting and insert text
            cursor.setCharFormat(char_format)
            cursor.insertText(log_line + '\n')
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            scrollbar = self.log_text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _update_status_labels(self):
        """Update the status labels with current log statistics"""
        
        with QMutexLocker(self.log_mutex):
            total_count = len(self.log_entries)
            filtered_count = len(self.filtered_entries)
        
        self.total_entries_label.setText(f"Total: {total_count}")
        self.filtered_entries_label.setText(f"Filtered: {filtered_count}")
        
        if self.log_entries:
            last_entry = self.log_entries[-1]
            last_update_str = last_entry.timestamp.strftime('%H:%M:%S')
            self.last_update_label.setText(f"Last update: {last_update_str}")
    
    def _trim_log_entries(self):
        """Remove excess log entries to maintain maximum count"""
        
        with QMutexLocker(self.log_mutex):
            if len(self.log_entries) > self.max_entries:
                # Keep most recent entries
                trim_count = len(self.log_entries) - self.max_entries
                self.log_entries = self.log_entries[trim_count:]
                
                self.logger.info(f"Trimmed {trim_count} oldest log entries (max: {self.max_entries})")
        
        self._apply_filters_and_refresh()
        self._update_status_labels()
    
    # Signal handlers
    
    def _on_filter_changed(self, new_level: str):
        """Handle log level filter changes"""
        self.current_level_filter = new_level
        self._apply_filters_and_refresh()
        self._update_status_labels()
        
        # Emit filter changed signal
        self.filter_changed.emit(self.current_level_filter, self.current_text_filter)
        
        self.logger.debug(f"Log level filter changed to: {new_level}")
    
    def _on_search_text_changed(self, text: str):
        """Handle search text changes"""
        self.current_text_filter = text
        # Apply filter in real-time for responsive UI
        self._apply_filters_and_refresh()
        self._update_status_labels()
    
    def _on_regex_toggled(self, enabled: bool):
        """Handle regex search toggle"""
        self.use_regex_search = enabled
        # Re-apply search with new regex setting
        if self.current_text_filter:
            self._apply_filters_and_refresh()
            self._update_status_labels()
    
    def _on_search_requested(self):
        """Handle explicit search button click"""
        search_text = self.search_line_edit.text()
        self.current_text_filter = search_text
        self._apply_filters_and_refresh()
        self._update_status_labels()
        
        # Emit filter changed signal
        self.filter_changed.emit(self.current_level_filter, self.current_text_filter)
        
        if search_text:
            self.logger.info(f"Search performed: '{search_text}' (regex: {self.use_regex_search})")
    
    def _on_clear_search(self):
        """Handle clear search button click"""
        self.search_line_edit.clear()
        self.current_text_filter = ""
        self.level_filter_combo.setCurrentText("ALL")
        self.current_level_filter = "ALL"
        
        self._apply_filters_and_refresh()
        self._update_status_labels()
        
        # Emit filter changed signal
        self.filter_changed.emit(self.current_level_filter, self.current_text_filter)
        
        self.logger.info("Search and filters cleared")
    
    def _on_auto_scroll_toggled(self, enabled: bool):
        """Handle auto-scroll toggle"""
        self.auto_scroll = enabled
        self.logger.debug(f"Auto-scroll {'enabled' if enabled else 'disabled'}")
    
    def _on_max_entries_changed(self, value: int):
        """Handle maximum entries change"""
        self.max_entries = value
        self._trim_log_entries()
        self.logger.debug(f"Maximum log entries set to: {value}")
    
    def _on_export_requested(self):
        """Handle export logs request"""
        
        # Show file dialog to select export location
        file_dialog = QFileDialog(self, "Export Logs")
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilters([
            "Text Files (*.txt)",
            "CSV Files (*.csv)", 
            "JSON Files (*.json)"
        ])
        file_dialog.setDefaultSuffix("txt")
        
        if file_dialog.exec() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            selected_filter = file_dialog.selectedNameFilter()
            
            # Determine format from selected filter
            if "CSV" in selected_filter:
                export_format = "csv"
            elif "JSON" in selected_filter:
                export_format = "json"
            else:
                export_format = "txt"
            
            self.export_logs(file_path, export_format)
    
    def _on_clear_logs(self):
        """Handle clear logs request"""
        
        # Confirm with user
        reply = QMessageBox.question(
            self, 
            "Clear Logs", 
            "Are you sure you want to clear all log entries?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_logs()
    
    def _on_export_progress(self, progress: int, status: str):
        """Handle export progress updates"""
        self.export_progress_bar.setValue(progress)
        self.export_status_label.setText(status)
    
    def _on_export_completed(self, file_path: str, success: bool, error_message: str):
        """Handle export completion"""
        
        # Hide progress bar
        self.export_progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        
        if success:
            self.export_status_label.setText(f"Exported to: {QFileInfo(file_path).fileName()}")
            
            # Show success message
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Logs successfully exported to:\n{file_path}"
            )
            
            self.add_log_entry(f"📄 Logs exported successfully to {file_path}", "INFO", "LogWidget")
            
        else:
            self.export_status_label.setText("Export failed")
            
            # Show error message
            QMessageBox.critical(
                self, 
                "Export Failed", 
                f"Failed to export logs:\n{error_message}"
            )
            
            self.add_log_entry(f"❌ Log export failed: {error_message}", "ERROR", "LogWidget")
        
        # Emit signal for external handling
        self.log_exported.emit(file_path, success, error_message)
        
        # Clean up worker thread
        if self.export_worker:
            self.export_worker.deleteLater()
            self.export_worker = None
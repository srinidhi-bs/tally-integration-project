#!/usr/bin/env python3
"""
Progress Widget for Background Operations

Professional progress display widget providing:
- Real-time progress bars for background tasks
- Task status display with colored indicators
- Task cancellation controls
- Multiple concurrent task tracking
- Integration with TaskManager and worker threads

This widget demonstrates:
- Qt progress bar customization and styling
- Signal-slot communication with background threads
- Professional UI patterns for long-running operations
- User-friendly task management interface

Author: Srinidhi BS & Claude
Created: August 29, 2025
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from PySide6.QtCore import (
    Qt, Signal, QTimer, Slot
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QScrollArea, QFrame, QSizePolicy, QSpacerItem
)

from core.utils.threading_utils import TaskProgress, TaskStatus, TaskResult
from ui.resources.styles.theme_manager import get_theme_manager


class TaskProgressWidget(QFrame):
    """
    Individual task progress display widget
    
    Features:
    - Progress bar with percentage display
    - Task name and status message
    - Elapsed time indicator
    - Cancel button for running tasks
    - Status-based color coding
    
    Learning: This demonstrates how to create reusable UI components
    that can be dynamically added and removed from layouts.
    """
    
    # Signal emitted when user requests task cancellation
    cancel_requested = Signal(UUID)
    
    def __init__(self, task_id: UUID, task_name: str, parent=None):
        """
        Initialize task progress widget
        
        Args:
            task_id: Unique identifier for the task
            task_name: Display name for the task
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.task_id = task_id
        self.task_name = task_name
        self.start_time = datetime.now()
        self.is_completed = False
        
        # Logger for debugging
        self.logger = logging.getLogger(f"{__name__}.TaskProgressWidget")
        
        self._setup_ui()
        self._apply_styling()
        
        # Timer for elapsed time updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_elapsed_time)
        self.timer.start(1000)  # Update every second
        
        self.logger.debug(f"Created progress widget for task: {task_name}")
    
    def _setup_ui(self):
        """Set up the user interface components"""
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Header with task name and cancel button
        header_layout = QHBoxLayout()
        
        self.task_label = QLabel(self.task_name)
        self.task_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.task_label)
        
        # Spacer to push cancel button to the right
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.cancel_button = QPushButton("✕")
        self.cancel_button.setFixedSize(20, 20)
        self.cancel_button.setToolTip("Cancel this task")
        self.cancel_button.clicked.connect(self._request_cancellation)
        header_layout.addWidget(self.cancel_button)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status and timing information
        info_layout = QHBoxLayout()
        
        self.status_label = QLabel("Starting...")
        self.status_label.setStyleSheet("color: #666666; font-size: 11px;")
        info_layout.addWidget(self.status_label)
        
        info_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.time_label = QLabel("0s")
        self.time_label.setStyleSheet("color: #666666; font-size: 11px;")
        info_layout.addWidget(self.time_label)
        
        layout.addLayout(info_layout)
        
        # Set minimum height for consistent appearance
        self.setMinimumHeight(80)
    
    def _apply_styling(self):
        """Apply professional styling to the widget"""
        
        # Get current theme colors
        theme_manager = get_theme_manager()
        colors = theme_manager.colors
        
        # Style the frame
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {colors['border']};
                border-radius: 6px;
                background-color: {colors['surface']};
                margin: 2px;
            }}
            
            QPushButton {{
                background-color: {colors['danger']};
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }}
            
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 3px;
            }}
        """)
    
    def update_progress(self, progress: TaskProgress):
        """
        Update the progress display
        
        Args:
            progress: Task progress information
        """
        self.progress_bar.setValue(progress.percentage)
        self.status_label.setText(progress.message)
        
        # Update progress bar color based on percentage
        if progress.percentage >= 100:
            self._set_progress_color("#27ae60")  # Success green
        elif progress.percentage >= 75:
            self._set_progress_color("#3498db")  # Primary blue
        elif progress.percentage >= 50:
            self._set_progress_color("#f39c12")  # Warning orange
        else:
            self._set_progress_color("#95a5a6")  # Neutral gray
    
    def update_status(self, status: TaskStatus, message: str = ""):
        """
        Update task status display
        
        Args:
            status: Current task status
            message: Status message (optional)
        """
        if message:
            self.status_label.setText(message)
        
        # Update styling based on status
        if status == TaskStatus.COMPLETED:
            self._set_completed_style(True)
            self.cancel_button.setVisible(False)
        elif status == TaskStatus.FAILED:
            self._set_completed_style(False)
            self.cancel_button.setVisible(False)
        elif status == TaskStatus.CANCELLED:
            self._set_cancelled_style()
            self.cancel_button.setVisible(False)
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.is_completed = True
            self.timer.stop()
    
    def _set_progress_color(self, color: str):
        """Set progress bar color"""
        theme_manager = get_theme_manager()
        colors = theme_manager.colors
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
            }}
            
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
    
    def _set_completed_style(self, success: bool):
        """Set styling for completed tasks"""
        color = "#27ae60" if success else "#e74c3c"  # Green for success, red for failure
        
        self.task_label.setStyleSheet(f"""
            font-weight: bold; 
            font-size: 12px; 
            color: {color};
        """)
        
        self.progress_bar.setValue(100 if success else 0)
        self._set_progress_color(color)
        
        if success:
            self.status_label.setText("✅ Completed successfully")
        else:
            self.status_label.setText("❌ Task failed")
    
    def _set_cancelled_style(self):
        """Set styling for cancelled tasks"""
        self.task_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 12px; 
            color: #95a5a6;
        """)
        
        self.progress_bar.setValue(0)
        self._set_progress_color("#95a5a6")
        self.status_label.setText("⏹️ Task cancelled")
    
    def _update_elapsed_time(self):
        """Update elapsed time display"""
        if not self.is_completed:
            elapsed = datetime.now() - self.start_time
            seconds = int(elapsed.total_seconds())
            
            if seconds < 60:
                time_text = f"{seconds}s"
            elif seconds < 3600:
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                time_text = f"{minutes}m {remaining_seconds}s"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                time_text = f"{hours}h {minutes}m"
            
            self.time_label.setText(time_text)
    
    def _request_cancellation(self):
        """Handle cancel button click"""
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("⏳")
        self.status_label.setText("Cancellation requested...")
        
        self.cancel_requested.emit(self.task_id)
        self.logger.info(f"Cancellation requested for task: {self.task_name}")


class ProgressWidget(QWidget):
    """
    Main progress widget for displaying all active background tasks
    
    Features:
    - Scrollable list of active tasks
    - Automatic cleanup of completed tasks
    - Task statistics display
    - Integration with TaskManager
    
    Learning: This demonstrates how to create a master widget that
    manages multiple child widgets dynamically.
    """
    
    # Signal emitted when user requests task cancellation
    cancel_requested = Signal(UUID)
    
    def __init__(self, parent=None):
        """Initialize the progress widget"""
        super().__init__(parent)
        
        self.active_tasks: Dict[UUID, TaskProgressWidget] = {}
        self.completed_count = 0
        self.failed_count = 0
        
        # Logger for debugging
        self.logger = logging.getLogger(f"{__name__}.ProgressWidget")
        
        self._setup_ui()
        self._apply_styling()
        
        # Timer for automatic cleanup of completed tasks
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_completed_tasks)
        self.cleanup_timer.start(10000)  # Cleanup every 10 seconds
        
        self.logger.debug("Progress widget initialized")
    
    def _setup_ui(self):
        """Set up the user interface"""
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Background Tasks")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.stats_label = QLabel("No active tasks")
        self.stats_label.setStyleSheet("color: #666666; font-size: 11px;")
        header_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(header_layout)
        
        # Scrollable area for task widgets
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget for scroll area
        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(2)
        
        # Add spacer to push tasks to the top
        self.container_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.scroll_area.setWidget(self.container_widget)
        main_layout.addWidget(self.scroll_area)
        
        # Set minimum size
        self.setMinimumSize(300, 200)
    
    def _apply_styling(self):
        """Apply professional styling"""
        
        theme_manager = get_theme_manager()
        colors = theme_manager.colors
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            
            QScrollArea {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                background-color: {colors['surface']};
            }}
        """)
    
    def add_task(self, task_id: UUID, task_name: str):
        """
        Add a new task to the progress display
        
        Args:
            task_id: Unique task identifier
            task_name: Display name for the task
        """
        if task_id in self.active_tasks:
            self.logger.warning(f"Task already exists: {task_id}")
            return
        
        # Create task widget
        task_widget = TaskProgressWidget(task_id, task_name)
        task_widget.cancel_requested.connect(self._on_cancel_requested)
        
        # Add to container (insert before the spacer)
        self.container_layout.insertWidget(self.container_layout.count() - 1, task_widget)
        
        # Track the task
        self.active_tasks[task_id] = task_widget
        
        self._update_stats()
        self.logger.debug(f"Added task to progress display: {task_name}")
    
    def update_task_progress(self, task_id: UUID, progress: TaskProgress):
        """
        Update progress for a specific task
        
        Args:
            task_id: Task identifier
            progress: Progress information
        """
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update_progress(progress)
    
    def update_task_status(self, task_id: UUID, status: TaskStatus, message: str = ""):
        """
        Update status for a specific task
        
        Args:
            task_id: Task identifier
            status: New task status
            message: Status message
        """
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update_status(status, message)
            
            # Update completion counters
            if status == TaskStatus.COMPLETED:
                self.completed_count += 1
            elif status == TaskStatus.FAILED:
                self.failed_count += 1
            
            self._update_stats()
    
    def remove_task(self, task_id: UUID):
        """
        Remove a task from the display
        
        Args:
            task_id: Task identifier to remove
        """
        if task_id in self.active_tasks:
            task_widget = self.active_tasks.pop(task_id)
            self.container_layout.removeWidget(task_widget)
            task_widget.deleteLater()
            
            self._update_stats()
            self.logger.debug(f"Removed task from display: {task_id}")
    
    def clear_completed_tasks(self):
        """Remove all completed tasks from the display"""
        completed_task_ids = [
            task_id for task_id, widget in self.active_tasks.items()
            if widget.is_completed
        ]
        
        for task_id in completed_task_ids:
            self.remove_task(task_id)
        
        self.logger.info(f"Cleared {len(completed_task_ids)} completed tasks")
    
    def _update_stats(self):
        """Update the statistics display"""
        active_count = len(self.active_tasks)
        
        if active_count == 0:
            stats_text = f"Completed: {self.completed_count}, Failed: {self.failed_count}"
            if self.completed_count == 0 and self.failed_count == 0:
                stats_text = "No active tasks"
        else:
            stats_text = f"Active: {active_count}, Completed: {self.completed_count}"
            if self.failed_count > 0:
                stats_text += f", Failed: {self.failed_count}"
        
        self.stats_label.setText(stats_text)
    
    def _cleanup_completed_tasks(self):
        """Automatically remove old completed tasks"""
        # Keep completed tasks for 30 seconds, then remove them
        completed_tasks = []
        cutoff_time = datetime.now()
        
        for task_id, widget in self.active_tasks.items():
            if widget.is_completed:
                # Check if task has been completed for more than 30 seconds
                if (cutoff_time - widget.start_time).total_seconds() > 30:
                    completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            self.remove_task(task_id)
    
    @Slot(UUID)
    def _on_cancel_requested(self, task_id: UUID):
        """Handle task cancellation request from child widget"""
        self.logger.info(f"Task cancellation requested: {task_id}")
        
        # Forward the cancellation request via signal
        self.cancel_requested.emit(task_id)
        # This signal would be connected to the TaskManager in the main window


if __name__ == "__main__":
    """
    Manual testing and demonstration of progress widgets
    """
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
    from uuid import uuid4
    import threading
    import random
    
    class ProgressTestWindow(QMainWindow):
        """Test window for progress widgets"""
        
        def __init__(self):
            super().__init__()
            
            self.setWindowTitle("Progress Widget Test")
            self.setGeometry(100, 100, 500, 600)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # Progress widget
            self.progress_widget = ProgressWidget()
            layout.addWidget(self.progress_widget)
            
            # Test buttons
            button_layout = QHBoxLayout()
            
            add_button = QPushButton("Add Test Task")
            add_button.clicked.connect(self.add_test_task)
            button_layout.addWidget(add_button)
            
            clear_button = QPushButton("Clear Completed")
            clear_button.clicked.connect(self.progress_widget.clear_completed_tasks)
            button_layout.addWidget(clear_button)
            
            layout.addLayout(button_layout)
        
        def add_test_task(self):
            """Add a test task with simulated progress"""
            task_id = uuid4()
            task_name = f"Test Task {random.randint(1, 1000)}"
            
            self.progress_widget.add_task(task_id, task_name)
            
            # Simulate progress updates in separate thread
            def simulate_progress():
                import time
                
                for i in range(101):
                    progress = TaskProgress(
                        percentage=i,
                        message=f"Processing step {i}/100...",
                        current_step=f"Step {i}",
                        completed_steps=i,
                        total_steps=100
                    )
                    
                    self.progress_widget.update_task_progress(task_id, progress)
                    time.sleep(0.05)  # 50ms delay
                
                # Mark as completed
                status = TaskStatus.COMPLETED if random.random() > 0.2 else TaskStatus.FAILED
                self.progress_widget.update_task_status(task_id, status)
            
            # Start simulation thread
            thread = threading.Thread(target=simulate_progress)
            thread.daemon = True
            thread.start()
    
    # Run test application
    app = QApplication(sys.argv)
    window = ProgressTestWindow()
    window.show()
    
    print("Progress Widget Test Application")
    print("Click 'Add Test Task' to simulate background operations")
    print("Tasks will automatically progress and complete")
    
    sys.exit(app.exec())
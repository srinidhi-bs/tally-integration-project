#!/usr/bin/env python3
"""
Manual Testing Application for Threading Framework

This application demonstrates and tests the professional threading framework
implemented for the TallyPrime Integration Manager. It provides:

- Interactive testing of background tasks
- Real-time progress monitoring
- Task cancellation capabilities
- Error handling demonstration
- Performance testing with concurrent tasks

Key Learning Points:
- Professional Qt threading patterns
- Task management and monitoring
- User interface responsiveness
- Error handling in background operations

Author: Srinidhi BS & Claude
Created: August 29, 2025
"""

import sys
import time
import logging
import random
from pathlib import Path
from typing import List
from uuid import UUID

# Add the parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Qt imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSpinBox, QComboBox, QGroupBox,
    QProgressBar, QStatusBar, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont

# Import our threading framework
from core.utils.threading_utils import (
    BaseWorkerThread, TaskManager, TaskStatus, TaskResult, TaskProgress,
    TaskPriority, create_task_manager
)
from ui.widgets.progress_widget import ProgressWidget
from ui.resources.styles.theme_manager import ThemeManager


class DemoWorkerThread(BaseWorkerThread):
    """
    Demo worker thread for testing the threading framework
    
    This worker simulates various types of background operations:
    - CPU-intensive calculations
    - Network-like delays
    - Progress reporting
    - Error conditions
    """
    
    def __init__(self, task_name: str, duration_seconds: float = 2.0, 
                 should_fail: bool = False, progress_steps: int = 10):
        """
        Initialize demo worker
        
        Args:
            task_name: Display name for the task
            duration_seconds: How long the task should run
            should_fail: Whether the task should simulate failure
            progress_steps: Number of progress updates to make
        """
        super().__init__(task_name, TaskPriority.NORMAL)
        self.duration_seconds = duration_seconds
        self.should_fail = should_fail
        self.progress_steps = progress_steps
    
    def execute(self):
        """Execute the demo task with simulated work"""
        start_time = time.time()
        
        for step in range(self.progress_steps):
            # Check for cancellation
            if self.is_cancelled:
                return None
            
            # Calculate progress
            progress_percentage = int((step + 1) / self.progress_steps * 100)
            step_duration = self.duration_seconds / self.progress_steps
            
            # Update progress
            self.update_progress(
                percentage=progress_percentage,
                message=f"Processing step {step + 1} of {self.progress_steps}",
                current_step=f"Step {step + 1}",
                completed_steps=step + 1
            )
            self.update_status(f"Working on step {step + 1}...")
            
            # Simulate work with delay
            time.sleep(step_duration)
            
            # Simulate random failure
            if self.should_fail and step == self.progress_steps // 2:
                raise Exception(f"Simulated failure in {self.task_name}")
        
        # Calculate actual execution time
        actual_time = time.time() - start_time
        
        return {
            "message": "Demo task completed successfully",
            "actual_duration": actual_time,
            "expected_duration": self.duration_seconds,
            "steps_completed": self.progress_steps
        }


class ThreadingTestWindow(QMainWindow):
    """
    Main test window for the threading framework
    
    This window provides comprehensive testing capabilities:
    - Task creation with various parameters
    - Real-time monitoring of active tasks
    - Task cancellation and error handling
    - Performance testing with multiple concurrent tasks
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Threading Framework Test Application")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize theme manager for professional appearance
        self.theme_manager = ThemeManager()
        
        # Create task manager
        self.task_manager = create_task_manager(max_threads=4)
        self.active_tasks: List[UUID] = []
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("Threading test application initialized")
    
    def _setup_ui(self):
        """Set up the user interface"""
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # Right panel - Progress monitoring
        progress_panel = self._create_progress_panel()
        splitter.addWidget(progress_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 800])
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Threading Framework Test Application")
        
        # Apply professional styling
        self._apply_styling()
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel for task management"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Threading Framework Test Controls")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Task creation group
        task_group = QGroupBox("Create Test Task")
        task_layout = QVBoxLayout(task_group)
        
        # Task name
        self.task_name_combo = QComboBox()
        self.task_name_combo.setEditable(True)
        self.task_name_combo.addItems([
            "Data Processing Task",
            "File Upload Simulation",
            "Report Generation",
            "Database Sync",
            "Image Processing",
            "Network Download"
        ])
        task_layout.addWidget(QLabel("Task Name:"))
        task_layout.addWidget(self.task_name_combo)
        
        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(5)
        duration_layout.addWidget(self.duration_spin)
        task_layout.addLayout(duration_layout)
        
        # Progress steps
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Progress Steps:"))
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(5, 100)
        self.steps_spin.setValue(20)
        steps_layout.addWidget(self.steps_spin)
        task_layout.addLayout(steps_layout)
        
        # Failure simulation
        self.failure_combo = QComboBox()
        self.failure_combo.addItems(["Success", "Simulate Failure"])
        task_layout.addWidget(QLabel("Behavior:"))
        task_layout.addWidget(self.failure_combo)
        
        layout.addWidget(task_group)
        
        # Control buttons
        button_group = QGroupBox("Task Management")
        button_layout = QVBoxLayout(button_group)
        
        self.start_task_btn = QPushButton("▶️ Start Single Task")
        self.start_task_btn.clicked.connect(self._start_single_task)
        button_layout.addWidget(self.start_task_btn)
        
        self.start_multiple_btn = QPushButton("⚡ Start 3 Concurrent Tasks")
        self.start_multiple_btn.clicked.connect(self._start_multiple_tasks)
        button_layout.addWidget(self.start_multiple_btn)
        
        self.cancel_all_btn = QPushButton("⏹️ Cancel All Tasks")
        self.cancel_all_btn.clicked.connect(self._cancel_all_tasks)
        button_layout.addWidget(self.cancel_all_btn)
        
        self.clear_completed_btn = QPushButton("🧹 Clear Completed Tasks")
        self.clear_completed_btn.clicked.connect(self._clear_completed_tasks)
        button_layout.addWidget(self.clear_completed_btn)
        
        layout.addWidget(button_group)
        
        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("No tasks executed yet")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # Event log
        log_group = QGroupBox("Event Log")
        log_layout = QVBoxLayout(log_group)
        
        self.event_log = QTextEdit()
        self.event_log.setMaximumHeight(200)
        self.event_log.setReadOnly(True)
        log_layout.addWidget(self.event_log)
        
        layout.addWidget(log_group)
        
        # Add stretch
        layout.addStretch()
        
        return panel
    
    def _create_progress_panel(self) -> QWidget:
        """Create the progress monitoring panel"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Background Task Progress Monitor")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Progress widget
        self.progress_widget = ProgressWidget()
        layout.addWidget(self.progress_widget)
        
        return panel
    
    def _connect_signals(self):
        """Connect task manager signals to UI handlers"""
        
        self.task_manager.task_added.connect(self._on_task_added)
        self.task_manager.task_started.connect(self._on_task_started)
        self.task_manager.task_completed.connect(self._on_task_completed)
        self.task_manager.task_cancelled.connect(self._on_task_cancelled)
        self.task_manager.task_progress.connect(self._on_task_progress)
        
        # Connect progress widget cancellation to task manager
        self.progress_widget._on_cancel_requested.connect(self.task_manager.cancel_task)
    
    def _apply_styling(self):
        """Apply professional styling to the application"""
        
        colors = self.theme_manager.get_colors()
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {colors['border']};
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 15px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {colors['primary']};
            }}
            
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['secondary']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['accent']};
            }}
            
            QTextEdit {{
                border: 1px solid {colors['border']};
                border-radius: 4px;
                background-color: {colors['surface']};
                font-family: "Consolas", "Monaco", monospace;
                font-size: 10px;
            }}
        """)
    
    def _log_event(self, message: str):
        """Log an event to the event log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.event_log.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.event_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        self.logger.info(message)
    
    def _start_single_task(self):
        """Start a single test task"""
        task_name = self.task_name_combo.currentText()
        duration = self.duration_spin.value()
        steps = self.steps_spin.value()
        should_fail = self.failure_combo.currentText() == "Simulate Failure"
        
        worker = DemoWorkerThread(
            task_name=task_name,
            duration_seconds=duration,
            should_fail=should_fail,
            progress_steps=steps
        )
        
        try:
            task_id = self.task_manager.submit_task(worker)
            self.active_tasks.append(task_id)
            
            self._log_event(f"Started task: {task_name} (Duration: {duration}s, Steps: {steps})")
            self._update_button_states()
            
        except Exception as e:
            self._log_event(f"Failed to start task: {str(e)}")
            QMessageBox.warning(self, "Task Start Error", f"Failed to start task:\n{str(e)}")
    
    def _start_multiple_tasks(self):
        """Start multiple concurrent tasks for testing"""
        
        task_configs = [
            ("Quick Task", 2, 10, False),
            ("Medium Task", 4, 20, False),
            ("Slow Task", 6, 30, False)
        ]
        
        for name, duration, steps, should_fail in task_configs:
            worker = DemoWorkerThread(
                task_name=name,
                duration_seconds=duration,
                should_fail=should_fail,
                progress_steps=steps
            )
            
            try:
                task_id = self.task_manager.submit_task(worker)
                self.active_tasks.append(task_id)
                
            except Exception as e:
                self._log_event(f"Failed to start {name}: {str(e)}")
        
        self._log_event("Started 3 concurrent tasks for performance testing")
        self._update_button_states()
    
    def _cancel_all_tasks(self):
        """Cancel all active tasks"""
        active_tasks = self.task_manager.get_active_tasks()
        
        if not active_tasks:
            self._log_event("No active tasks to cancel")
            return
        
        self.task_manager.cancel_all_tasks()
        self._log_event(f"Requested cancellation of {len(active_tasks)} active tasks")
    
    def _clear_completed_tasks(self):
        """Clear completed tasks from the progress widget"""
        self.progress_widget.clear_completed_tasks()
        self._log_event("Cleared completed tasks from progress display")
    
    def _update_button_states(self):
        """Update button states based on task manager status"""
        active_tasks = self.task_manager.get_active_tasks()
        has_active = len(active_tasks) > 0
        
        self.cancel_all_btn.setEnabled(has_active)
        self.start_multiple_btn.setEnabled(len(active_tasks) < 2)  # Prevent too many concurrent tasks
    
    def _update_statistics(self):
        """Update the statistics display"""
        history = self.task_manager.get_task_history(limit=100)
        active_tasks = self.task_manager.get_active_tasks()
        
        completed = len([r for r in history if r.status == TaskStatus.COMPLETED])
        failed = len([r for r in history if r.status == TaskStatus.FAILED])
        cancelled = len([r for r in history if r.status == TaskStatus.CANCELLED])
        
        avg_time = 0
        if history:
            avg_time = sum(r.execution_time_ms for r in history) / len(history) / 1000.0
        
        stats_text = f"""
        Active Tasks: {len(active_tasks)}
        Total Executed: {len(history)}
        Completed: {completed}
        Failed: {failed}
        Cancelled: {cancelled}
        Average Time: {avg_time:.1f}s
        """
        
        self.stats_label.setText(stats_text.strip())
    
    # Task manager signal handlers
    
    @Slot(UUID, str)
    def _on_task_added(self, task_id: UUID, task_name: str):
        """Handle task addition"""
        self.progress_widget.add_task(task_id, task_name)
        self.status_bar.showMessage(f"Task started: {task_name}")
        self._update_button_states()
    
    @Slot(UUID)
    def _on_task_started(self, task_id: UUID):
        """Handle task start"""
        self.logger.debug(f"Task started: {task_id}")
    
    @Slot(UUID, TaskResult)
    def _on_task_completed(self, task_id: UUID, result: TaskResult):
        """Handle task completion"""
        # Remove from active tasks
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
        
        # Update progress widget
        self.progress_widget.update_task_status(task_id, result.status)
        
        # Log result
        if result.is_success:
            self._log_event(f"✅ Task completed: {result.execution_time_ms/1000:.1f}s")
            self.status_bar.showMessage("Task completed successfully", 3000)
        else:
            self._log_event(f"❌ Task failed: {result.error}")
            self.status_bar.showMessage(f"Task failed: {result.error}", 5000)
        
        self._update_button_states()
        self._update_statistics()
    
    @Slot(UUID)
    def _on_task_cancelled(self, task_id: UUID):
        """Handle task cancellation"""
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
        
        self.progress_widget.update_task_status(task_id, TaskStatus.CANCELLED)
        self._log_event("⏹️ Task cancelled")
        self.status_bar.showMessage("Task cancelled", 2000)
        
        self._update_button_states()
        self._update_statistics()
    
    @Slot(UUID, TaskProgress)
    def _on_task_progress(self, task_id: UUID, progress: TaskProgress):
        """Handle task progress updates"""
        self.progress_widget.update_task_progress(task_id, progress)
        
        # Update status bar with current task progress
        if progress.percentage % 10 == 0:  # Update every 10%
            self.status_bar.showMessage(f"Progress: {progress.percentage}% - {progress.message}", 1000)


def main():
    """Main entry point for the threading test application"""
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Threading Framework Test")
    app.setApplicationDisplayName("Threading Framework Test Application")
    app.setApplicationVersion("1.0.0")
    
    print("Threading Framework Test Application")
    print("=" * 50)
    print("This application demonstrates the professional threading framework")
    print("implemented for the TallyPrime Integration Manager.")
    print()
    print("Features to test:")
    print("• Background task execution with progress reporting")
    print("• Task cancellation and error handling")
    print("• Concurrent task management")
    print("• UI responsiveness during operations")
    print("• Professional progress monitoring")
    print()
    print("Instructions:")
    print("1. Configure task parameters in the left panel")
    print("2. Start single or multiple tasks")
    print("3. Monitor progress in the right panel")
    print("4. Test cancellation and error handling")
    print("5. Observe UI responsiveness during operations")
    print()
    
    # Create and show main window
    window = ThreadingTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
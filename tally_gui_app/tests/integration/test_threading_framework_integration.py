#!/usr/bin/env python3
"""
Threading Framework Integration Tests

This test suite validates the integration between:
- Threading utilities and existing TallyConnector
- Background tasks with ProfessionalLogWidget logging
- Progress reporting in the main GUI
- Task cancellation and error handling
- Thread-safe communication with Qt widgets

Learning Focus:
- Professional Qt threading patterns with real-world integration
- Testing background operations without blocking the test runner
- Mock objects for testing complex threading scenarios
- Signal-slot testing with QSignalSpy and manual verification

Author: Srinidhi BS & Claude
Created: August 29, 2025
"""

import pytest
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID

# Import Qt modules
from PySide6.QtCore import QTimer, QEventLoop, QCoreApplication, Signal, QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QSignalSpy

# Add the parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.utils.threading_utils import (
    BaseWorkerThread, TallyOperationWorker, DataLoadWorker,
    TaskManager, TaskStatus, TaskPriority, TaskResult, TaskProgress,
    ThreadSafeLogger, create_data_load_task, create_task_manager
)
from core.tally.connector import TallyConnector, TallyConnectionConfig
from pathlib import Path


class TestThreadingFrameworkIntegration:
    """
    Integration tests for the threading framework
    
    These tests validate that the threading components work correctly
    with the existing application infrastructure.
    """
    
    @pytest.fixture(autouse=True)
    def setup_qt_app(self):
        """Ensure QApplication exists for Qt testing"""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        yield
        # Don't quit the application as other tests may need it
    
    @pytest.fixture
    def mock_tally_connector(self):
        """Create a mock TallyConnector for testing"""
        mock_connector = Mock(spec=TallyConnector)
        mock_connector.is_connected.return_value = True
        mock_connector.test_connection_sync.return_value = (True, "Connected successfully")
        
        # Mock company info
        mock_company = Mock()
        mock_company.name = "Test Company"
        mock_connector.get_company_info.return_value = mock_company
        
        return mock_connector
    
    def test_base_worker_thread_lifecycle(self):
        """
        Test the complete lifecycle of a BaseWorkerThread
        
        Learning: This demonstrates Qt thread lifecycle management
        and proper signal-slot communication patterns.
        """
        
        class TestWorker(BaseWorkerThread):
            def execute(self):
                # Simulate work with progress updates
                for i in range(5):
                    if self.is_cancelled:
                        return None
                    self.update_progress(i * 20, f"Step {i+1} of 5")
                    time.sleep(0.1)  # Simulate work
                return "Task completed successfully"
        
        # Create and configure worker
        worker = TestWorker("Test Task", TaskPriority.NORMAL)
        
        # Set up signal spies for testing
        started_spy = QSignalSpy(worker.task_started)
        completed_spy = QSignalSpy(worker.task_completed)
        progress_spy = QSignalSpy(worker.progress_updated)
        
        # Start the worker and wait for completion
        worker.start()
        
        # Wait for task completion (max 5 seconds)
        completed_spy.wait(5000)
        
        # Verify signal emissions
        assert len(started_spy) == 1, "Task should emit started signal once"
        assert len(completed_spy) == 1, "Task should emit completed signal once"
        assert len(progress_spy) >= 5, "Task should emit multiple progress updates"
        
        # Verify result
        task_id, result = completed_spy[0]
        assert isinstance(result, TaskResult)
        assert result.is_success
        assert result.data == "Task completed successfully"
        assert result.execution_time_ms > 0
        
        # Clean up
        worker.wait(1000)
        worker.deleteLater()
    
    def test_task_cancellation(self):
        """
        Test task cancellation functionality
        
        Learning: Demonstrates how to implement cancellable background operations
        that respond quickly to user requests to stop.
        """
        
        class LongRunningWorker(BaseWorkerThread):
            def execute(self):
                # Simulate long-running task that checks for cancellation
                for i in range(100):
                    if self.is_cancelled:
                        self.update_status("Task was cancelled")
                        return None
                    
                    self.update_progress(i, f"Processing item {i}")
                    time.sleep(0.05)  # Simulate work
                
                return "Should not reach here if cancelled"
        
        worker = LongRunningWorker("Cancellable Task")
        
        # Set up signal spies
        cancelled_spy = QSignalSpy(worker.task_cancelled)
        completed_spy = QSignalSpy(worker.task_completed)
        
        # Start worker
        worker.start()
        
        # Wait a bit then cancel
        QTimer.singleShot(200, lambda: worker.cancel())
        
        # Wait for completion
        completed_spy.wait(3000)
        
        # Verify cancellation
        assert len(cancelled_spy) == 1, "Should emit cancelled signal"
        assert len(completed_spy) == 1, "Should emit completed signal even when cancelled"
        
        # Verify final status
        task_id, result = completed_spy[0]
        assert result.status == TaskStatus.CANCELLED
        
        # Clean up
        worker.wait(1000)
        worker.deleteLater()
    
    def test_data_load_worker_with_mock_connector(self, mock_tally_connector):
        """
        Test DataLoadWorker with mocked TallyConnector
        
        Learning: This shows how to test background operations that depend
        on external services using mocks for reliable, fast testing.
        """
        
        # Mock ledger data
        mock_ledgers = [
            Mock(name=f"Ledger {i}", balance=Mock(current_balance=1000 + i*100))
            for i in range(5)
        ]
        
        # Configure mock to return ledger data
        with patch('core.tally.data_reader.TallyDataReader') as mock_reader_class:
            mock_reader = mock_reader_class.return_value
            mock_reader.get_all_ledgers_info.return_value = mock_ledgers
            
            # Create and execute worker
            worker = DataLoadWorker(mock_tally_connector, "ledgers")
            
            # Set up signal spy
            completed_spy = QSignalSpy(worker.task_completed)
            progress_spy = QSignalSpy(worker.progress_updated)
            
            # Execute task
            worker.start()
            completed_spy.wait(5000)
            
            # Verify results
            assert len(completed_spy) == 1
            task_id, result = completed_spy[0]
            assert result.is_success
            assert len(result.data) == 5
            assert len(progress_spy) > 0  # Should have progress updates
            
            # Verify mock calls
            mock_tally_connector.is_connected.assert_called()
            mock_reader.get_all_ledgers_info.assert_called_once()
        
        # Clean up
        worker.wait(1000)
        worker.deleteLater()
    
    def test_task_manager_operations(self, mock_tally_connector):
        """
        Test TaskManager functionality
        
        Learning: This demonstrates centralized task management
        for professional applications with multiple concurrent operations.
        """
        
        class QuickWorker(BaseWorkerThread):
            def __init__(self, result_data):
                super().__init__(f"Quick Task {result_data}")
                self.result_data = result_data
            
            def execute(self):
                time.sleep(0.1)  # Quick task
                return self.result_data
        
        # Create task manager
        manager = create_task_manager(max_threads=2)
        
        # Set up signal spies
        task_added_spy = QSignalSpy(manager.task_added)
        task_completed_spy = QSignalSpy(manager.task_completed)
        
        # Submit multiple tasks
        worker1 = QuickWorker("Result 1")
        worker2 = QuickWorker("Result 2")
        
        task_id1 = manager.submit_task(worker1)
        task_id2 = manager.submit_task(worker2)
        
        # Wait for all tasks to complete
        start_time = time.time()
        while len(task_completed_spy) < 2 and time.time() - start_time < 10:
            QCoreApplication.processEvents()
            time.sleep(0.1)
        
        # Verify results
        assert len(task_added_spy) == 2, "Should emit task_added for both tasks"
        assert len(task_completed_spy) == 2, "Should complete both tasks"
        
        # Verify task IDs
        assert task_id1 != task_id2, "Task IDs should be unique"
        assert isinstance(task_id1, UUID), "Should return UUID for task ID"
        
        # Verify active tasks are cleaned up
        active_tasks = manager.get_active_tasks()
        assert len(active_tasks) == 0, "No tasks should be active after completion"
    
    def test_error_handling_in_worker(self):
        """
        Test comprehensive error handling in worker threads
        
        Learning: Demonstrates proper exception handling in background threads
        with user-friendly error reporting.
        """
        
        class ErrorWorker(BaseWorkerThread):
            def execute(self):
                self.update_status("About to encounter error...")
                raise ValueError("Simulated error for testing")
        
        worker = ErrorWorker("Error Test Task")
        
        # Set up signal spy
        failed_spy = QSignalSpy(worker.task_failed)
        completed_spy = QSignalSpy(worker.task_completed)
        
        # Execute task
        worker.start()
        completed_spy.wait(3000)
        
        # Verify error handling
        assert len(failed_spy) == 1, "Should emit task_failed signal"
        assert len(completed_spy) == 1, "Should emit completed signal even on error"
        
        # Verify error details
        task_id, error_message, error_details = failed_spy[0]
        assert "Simulated error for testing" in error_message
        assert "ValueError" in error_details
        
        # Verify result status
        task_id, result = completed_spy[0]
        assert result.is_failure
        assert result.status == TaskStatus.FAILED
        
        # Clean up
        worker.wait(1000)
        worker.deleteLater()
    
    def test_thread_safe_logger(self):
        """
        Test thread-safe logging functionality
        
        Learning: This demonstrates how to implement thread-safe logging
        that can be used from background threads without issues.
        """
        
        # Create thread-safe logger
        logger = ThreadSafeLogger("test.threading")
        
        # Test basic logging methods
        logger.info("Test info message from main thread")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Test logging from worker thread
        class LoggingWorker(BaseWorkerThread):
            def __init__(self, logger):
                super().__init__("Logging Test Worker")
                self.logger = logger
            
            def execute(self):
                self.logger.info("Message from worker thread")
                self.logger.debug("Debug message from worker")
                return "Logging completed"
        
        worker = LoggingWorker(logger)
        completed_spy = QSignalSpy(worker.task_completed)
        
        # Execute and verify
        worker.start()
        completed_spy.wait(3000)
        
        assert len(completed_spy) == 1
        task_id, result = completed_spy[0]
        assert result.is_success
        
        # Clean up
        worker.wait(1000)
        worker.deleteLater()
    
    def test_convenience_functions(self, mock_tally_connector):
        """
        Test convenience functions for creating workers and managers
        
        Learning: This shows how to provide user-friendly APIs
        for complex functionality while maintaining flexibility.
        """
        
        # Test task creation function
        data_worker = create_data_load_task(mock_tally_connector, "company")
        assert isinstance(data_worker, DataLoadWorker)
        assert data_worker.data_type == "company"
        assert data_worker.tally_connector == mock_tally_connector
        
        # Test task manager creation
        manager = create_task_manager(max_threads=3)
        assert isinstance(manager, TaskManager)
        assert manager.max_threads == 3
        
        # Test auto-detection (should not raise an error)
        auto_manager = create_task_manager()
        assert isinstance(auto_manager, TaskManager)
        assert 2 <= auto_manager.max_threads <= 8  # Should be reasonable range
    
    @pytest.mark.slow
    def test_concurrent_task_execution(self, mock_tally_connector):
        """
        Test concurrent execution of multiple tasks
        
        Learning: This demonstrates how the threading framework
        handles multiple concurrent operations efficiently.
        
        Note: Marked as slow test since it involves actual timing
        """
        
        class TimedWorker(BaseWorkerThread):
            def __init__(self, duration_ms, name):
                super().__init__(f"Timed Worker {name}")
                self.duration_ms = duration_ms
            
            def execute(self):
                start_time = time.time()
                
                while (time.time() - start_time) * 1000 < self.duration_ms:
                    if self.is_cancelled:
                        return None
                    
                    elapsed = int((time.time() - start_time) * 1000)
                    progress = min(100, int(elapsed / self.duration_ms * 100))
                    self.update_progress(progress, f"Working... {elapsed}ms")
                    
                    time.sleep(0.05)
                
                return f"Completed after {self.duration_ms}ms"
        
        # Create manager and workers
        manager = create_task_manager(max_threads=3)
        completed_spy = QSignalSpy(manager.task_completed)
        
        # Submit three concurrent tasks
        worker1 = TimedWorker(300, "A")  # 300ms
        worker2 = TimedWorker(200, "B")  # 200ms  
        worker3 = TimedWorker(400, "C")  # 400ms
        
        start_time = time.time()
        
        task_id1 = manager.submit_task(worker1)
        task_id2 = manager.submit_task(worker2)
        task_id3 = manager.submit_task(worker3)
        
        # Wait for all tasks to complete
        timeout = 2000  # 2 seconds should be enough
        while len(completed_spy) < 3:
            if not completed_spy.wait(timeout):
                break
        
        total_time = time.time() - start_time
        
        # Verify concurrent execution
        assert len(completed_spy) == 3, "All three tasks should complete"
        assert total_time < 1.0, "Concurrent execution should be faster than sequential"
        
        # Verify all tasks succeeded
        for i in range(3):
            task_id, result = completed_spy[i]
            assert result.is_success, f"Task {i} should succeed"
            assert "Completed after" in result.data


class TestSignalSlotIntegration:
    """
    Tests for Qt signal-slot integration with threading
    
    Learning Focus: Understanding how Qt's signal-slot system
    works across thread boundaries and how to test it properly.
    """
    
    def test_cross_thread_signal_communication(self):
        """
        Test signal emission and reception across thread boundaries
        
        Learning: This shows how Qt handles cross-thread signal emission
        automatically and safely.
        """
        
        class SignalTestObject(QObject):
            test_signal = Signal(str, int)
            
            def __init__(self):
                super().__init__()
                self.received_messages = []
            
            def slot_handler(self, message: str, number: int):
                self.received_messages.append((message, number))
        
        class SignalWorker(BaseWorkerThread):
            def __init__(self, signal_object):
                super().__init__("Signal Test Worker")
                self.signal_object = signal_object
            
            def execute(self):
                # Emit signals from worker thread
                for i in range(3):
                    self.signal_object.test_signal.emit(f"Message {i}", i)
                    time.sleep(0.1)
                return "Signals emitted"
        
        # Set up signal receiver
        receiver = SignalTestObject()
        receiver.test_signal.connect(receiver.slot_handler)
        
        # Create and run worker
        worker = SignalWorker(receiver)
        completed_spy = QSignalSpy(worker.task_completed)
        
        worker.start()
        completed_spy.wait(3000)
        
        # Process any pending events
        QCoreApplication.processEvents()
        
        # Verify signal reception
        assert len(receiver.received_messages) == 3
        for i in range(3):
            message, number = receiver.received_messages[i]
            assert message == f"Message {i}"
            assert number == i
        
        # Clean up
        worker.wait(1000)
        worker.deleteLater()


if __name__ == "__main__":
    """
    Run integration tests manually for development and debugging
    """
    # Set up logging for test observation
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create QApplication for manual testing
    app = QApplication(sys.argv)
    
    print("Threading Framework Integration Tests")
    print("=" * 50)
    print("Running manual test examples...")
    
    # Example 1: Basic worker thread
    print("\n1. Testing basic worker thread lifecycle...")
    
    class ExampleWorker(BaseWorkerThread):
        def execute(self):
            for i in range(5):
                if self.is_cancelled:
                    return None
                self.update_progress(i * 20, f"Processing step {i+1}")
                time.sleep(0.2)
            return "Example task completed"
    
    worker = ExampleWorker("Example Task")
    
    def on_progress(task_id, progress):
        print(f"Progress: {progress.percentage}% - {progress.message}")
    
    def on_completed(task_id, result):
        print(f"Task completed: {result.status.value}")
        print(f"Result: {result.data}")
        app.quit()
    
    worker.progress_updated.connect(on_progress)
    worker.task_completed.connect(on_completed)
    
    worker.start()
    
    # Run event loop
    app.exec()
    
    print("Integration tests completed successfully!")
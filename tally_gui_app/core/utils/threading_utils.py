#!/usr/bin/env python3
"""
Threading Framework for TallyPrime Integration Manager

Professional threading utilities providing:
- Standardized Qt worker thread patterns
- Progress reporting and task cancellation
- Thread pool management for efficient resource usage
- Thread-safe logging integration
- Comprehensive error handling for background operations

This framework builds upon the existing QThread patterns in the application
and provides a unified, professional approach to background operations.

Author: Srinidhi BS & Claude
Created: August 29, 2025
"""

import logging
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Union
from uuid import uuid4, UUID

from PySide6.QtCore import (
    QObject, QThread, Signal, QTimer, QMutex, QMutexLocker, 
    QThreadPool, QRunnable, Slot, QWaitCondition
)


# ================================================================================================
# ENUMS AND DATA MODELS
# ================================================================================================

class TaskStatus(Enum):
    """Enumeration of possible task states"""
    PENDING = "pending"         # Task created but not started
    RUNNING = "running"         # Task is currently executing  
    CANCELLING = "cancelling"   # Cancellation requested, cleaning up
    CANCELLED = "cancelled"     # Task was successfully cancelled
    COMPLETED = "completed"     # Task finished successfully
    FAILED = "failed"          # Task failed with error


class TaskPriority(Enum):
    """Task execution priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskProgress:
    """
    Progress information for a background task
    
    Provides detailed progress reporting with:
    - Percentage completion (0-100)
    - Status message for user display
    - Current step information
    - Time estimates and statistics
    """
    percentage: int = 0                    # Progress percentage 0-100
    message: str = "Starting task..."      # Status message for user
    current_step: str = ""                 # Current operation step
    total_steps: int = 1                   # Total number of steps
    completed_steps: int = 0               # Steps completed so far
    estimated_remaining_ms: int = 0        # Estimated time remaining (ms)
    
    def __post_init__(self):
        """Validate progress data after initialization"""
        self.percentage = max(0, min(100, self.percentage))
        self.completed_steps = max(0, min(self.total_steps, self.completed_steps))


@dataclass
class TaskResult:
    """
    Result data from a completed background task
    
    Encapsulates:
    - Success/failure status
    - Return data from successful tasks
    - Error information for failed tasks
    - Execution statistics and timing
    """
    task_id: UUID                          # Unique task identifier
    status: TaskStatus                     # Final task status
    data: Any = None                       # Task result data (if successful)
    error: Optional[str] = None            # Error message (if failed)
    error_details: Optional[str] = None    # Detailed error information
    execution_time_ms: int = 0             # Total execution time
    started_at: Optional[datetime] = None   # Task start timestamp
    completed_at: Optional[datetime] = None # Task completion timestamp
    
    @property
    def is_success(self) -> bool:
        """Check if task completed successfully"""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_failure(self) -> bool:
        """Check if task failed"""
        return self.status == TaskStatus.FAILED


# ================================================================================================
# BASE WORKER THREAD CLASS
# ================================================================================================

class BaseWorkerThread(QThread):
    """
    Professional base class for all worker threads
    
    Provides standardized patterns for:
    - Progress reporting with detailed status updates
    - Task cancellation with proper cleanup
    - Error handling with comprehensive logging
    - Signal-slot communication with UI thread
    - Resource management and thread lifecycle
    
    Learning: This demonstrates Qt threading best practices:
    1. All UI communication via signals (thread-safe)
    2. Proper resource cleanup on thread completion
    3. Cancellation support for responsive UI
    4. Comprehensive error reporting
    """
    
    # Standard signals that all worker threads should emit
    task_started = Signal(UUID)                    # task_id
    progress_updated = Signal(UUID, TaskProgress)  # task_id, progress
    status_updated = Signal(UUID, str)             # task_id, status_message
    task_completed = Signal(UUID, TaskResult)      # task_id, result
    task_cancelled = Signal(UUID)                  # task_id
    task_failed = Signal(UUID, str, str)          # task_id, error, details
    
    def __init__(self, task_name: str = "Background Task", 
                 priority: TaskPriority = TaskPriority.NORMAL,
                 timeout_ms: int = 300000):  # 5 minutes default timeout
        """
        Initialize base worker thread
        
        Args:
            task_name: Human-readable name for the task
            priority: Task execution priority
            timeout_ms: Maximum execution time before timeout
        """
        super().__init__()
        
        # Task identification
        self.task_id = uuid4()
        self.task_name = task_name
        self.priority = priority
        
        # Task control
        self._is_cancelled = False
        self._cancel_requested = False
        self._status = TaskStatus.PENDING
        self._timeout_ms = timeout_ms
        
        # Progress tracking
        self._progress = TaskProgress()
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        
        # Thread safety
        self._mutex = QMutex()
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Setup timeout timer
        self._timeout_timer = QTimer()
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._handle_timeout)
        
        self.logger.debug(f"Created worker thread: {self.task_name} (ID: {self.task_id})")
    
    def run(self):
        """
        Main thread execution - calls the abstract execute method
        
        This method handles:
        - Task lifecycle management (start/complete/error)
        - Progress tracking and timing
        - Error handling and cleanup
        - Signal emission for UI communication
        """
        try:
            # Initialize task execution
            self._started_at = datetime.now()
            self._status = TaskStatus.RUNNING
            self._timeout_timer.start(self._timeout_ms)
            
            self.logger.info(f"Starting task: {self.task_name}")
            self.task_started.emit(self.task_id)
            self.update_status("Initializing task...")
            
            # Execute the actual work (implemented by subclasses)
            result_data = self.execute()
            
            # Check if task was cancelled during execution
            if self.is_cancelled:
                self._handle_cancellation()
                return
            
            # Task completed successfully
            self._status = TaskStatus.COMPLETED
            self._completed_at = datetime.now()
            execution_time = int((self._completed_at - self._started_at).total_seconds() * 1000)
            
            result = TaskResult(
                task_id=self.task_id,
                status=self._status,
                data=result_data,
                execution_time_ms=execution_time,
                started_at=self._started_at,
                completed_at=self._completed_at
            )
            
            self.logger.info(f"Task completed successfully: {self.task_name} ({execution_time}ms)")
            self.task_completed.emit(self.task_id, result)
            
        except Exception as e:
            self._handle_error(e)
        
        finally:
            # Cleanup resources
            self._timeout_timer.stop()
            self.logger.debug(f"Worker thread finished: {self.task_name}")
    
    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the actual work - must be implemented by subclasses
        
        This method should:
        1. Perform the actual background work
        2. Call update_progress() regularly to report progress
        3. Check is_cancelled periodically and return early if cancelled
        4. Return the result data on success
        
        Returns:
            Any: Result data from the task execution
        
        Raises:
            Exception: Any errors that occur during execution
        """
        pass
    
    def cancel(self):
        """
        Request cancellation of the running task
        
        This method is thread-safe and can be called from any thread.
        The actual cancellation happens in the worker thread when it
        checks the cancellation status.
        """
        with QMutexLocker(self._mutex):
            if self._status == TaskStatus.RUNNING:
                self._cancel_requested = True
                self._status = TaskStatus.CANCELLING
                self.logger.info(f"Cancellation requested for task: {self.task_name}")
    
    @property
    def is_cancelled(self) -> bool:
        """
        Check if cancellation has been requested
        
        Worker threads should check this regularly during execution
        and return early if cancellation is requested.
        """
        with QMutexLocker(self._mutex):
            return self._cancel_requested
    
    @property
    def status(self) -> TaskStatus:
        """Get current task status (thread-safe)"""
        with QMutexLocker(self._mutex):
            return self._status
    
    def update_progress(self, percentage: int = None, message: str = None,
                       current_step: str = None, completed_steps: int = None):
        """
        Update task progress and notify UI thread
        
        Args:
            percentage: Progress percentage (0-100)
            message: Status message for display
            current_step: Description of current operation
            completed_steps: Number of completed steps
        """
        with QMutexLocker(self._mutex):
            if percentage is not None:
                self._progress.percentage = max(0, min(100, percentage))
            if message is not None:
                self._progress.message = message
            if current_step is not None:
                self._progress.current_step = current_step
            if completed_steps is not None:
                self._progress.completed_steps = completed_steps
        
        # Emit progress update (creates a copy to avoid threading issues)
        progress_copy = TaskProgress(
            percentage=self._progress.percentage,
            message=self._progress.message,
            current_step=self._progress.current_step,
            total_steps=self._progress.total_steps,
            completed_steps=self._progress.completed_steps
        )
        
        self.progress_updated.emit(self.task_id, progress_copy)
    
    def update_status(self, message: str):
        """
        Update task status message
        
        Args:
            message: Status message to display to user
        """
        self.logger.debug(f"Task status: {message}")
        self.status_updated.emit(self.task_id, message)
    
    def _handle_error(self, error: Exception):
        """
        Handle task execution errors
        
        Args:
            error: The exception that occurred
        """
        self._status = TaskStatus.FAILED
        self._completed_at = datetime.now()
        
        error_message = str(error)
        error_details = traceback.format_exc()
        
        execution_time = 0
        if self._started_at:
            execution_time = int((self._completed_at - self._started_at).total_seconds() * 1000)
        
        result = TaskResult(
            task_id=self.task_id,
            status=self._status,
            error=error_message,
            error_details=error_details,
            execution_time_ms=execution_time,
            started_at=self._started_at,
            completed_at=self._completed_at
        )
        
        self.logger.error(f"Task failed: {self.task_name} - {error_message}")
        self.logger.debug(f"Task error details: {error_details}")
        
        self.task_failed.emit(self.task_id, error_message, error_details)
        self.task_completed.emit(self.task_id, result)
    
    def _handle_cancellation(self):
        """Handle task cancellation cleanup"""
        self._status = TaskStatus.CANCELLED
        self._completed_at = datetime.now()
        self._is_cancelled = True
        
        execution_time = 0
        if self._started_at:
            execution_time = int((self._completed_at - self._started_at).total_seconds() * 1000)
        
        result = TaskResult(
            task_id=self.task_id,
            status=self._status,
            execution_time_ms=execution_time,
            started_at=self._started_at,
            completed_at=self._completed_at
        )
        
        self.logger.info(f"Task cancelled: {self.task_name}")
        self.task_cancelled.emit(self.task_id)
        self.task_completed.emit(self.task_id, result)
    
    def _handle_timeout(self):
        """Handle task timeout"""
        self.logger.warning(f"Task timeout: {self.task_name} (>{self._timeout_ms}ms)")
        self.cancel()


# ================================================================================================
# TALLY-SPECIFIC WORKER THREADS
# ================================================================================================

class TallyOperationWorker(BaseWorkerThread):
    """
    Specialized worker thread for TallyPrime operations
    
    This class provides:
    - Integration with TallyConnector for HTTP-XML operations
    - Standardized error handling for TallyPrime-specific errors
    - Progress reporting for data operations
    - Connection validation before operation execution
    
    Learning: Demonstrates how to extend the base worker thread
    for domain-specific operations while maintaining consistency.
    """
    
    def __init__(self, tally_connector, operation_name: str = "TallyPrime Operation",
                 timeout_ms: int = 600000):  # 10 minutes for Tally operations
        """
        Initialize TallyPrime operation worker
        
        Args:
            tally_connector: TallyConnector instance
            operation_name: Name of the operation for logging
            timeout_ms: Operation timeout in milliseconds
        """
        super().__init__(task_name=operation_name, timeout_ms=timeout_ms)
        self.tally_connector = tally_connector
        
        # Validate connector
        if not self.tally_connector:
            raise ValueError("TallyConnector instance is required")
    
    def execute(self) -> Any:
        """
        Execute TallyPrime operation with connection validation
        
        This method:
        1. Validates TallyPrime connection
        2. Calls the specific operation implementation
        3. Handles TallyPrime-specific errors
        
        Returns:
            Any: Result data from the operation
        """
        # Validate connection before proceeding
        self.update_status("Validating TallyPrime connection...")
        if not self.tally_connector.is_connected():
            self.update_status("Connecting to TallyPrime...")
            success, message = self.tally_connector.test_connection_sync()
            if not success:
                raise ConnectionError(f"TallyPrime connection failed: {message}")
        
        # Execute the specific TallyPrime operation
        return self.execute_tally_operation()
    
    @abstractmethod
    def execute_tally_operation(self) -> Any:
        """
        Execute the specific TallyPrime operation
        
        Subclasses must implement this method with their specific
        TallyPrime HTTP-XML operations.
        
        Returns:
            Any: Operation result data
        """
        pass


class DataLoadWorker(TallyOperationWorker):
    """
    Worker thread for loading data from TallyPrime
    
    Handles:
    - Company information loading
    - Ledger list retrieval  
    - Transaction data loading
    - Progress reporting for large datasets
    """
    
    def __init__(self, tally_connector, data_type: str, **kwargs):
        """
        Initialize data loading worker
        
        Args:
            tally_connector: TallyConnector instance
            data_type: Type of data to load ('company', 'ledgers', 'transactions')
            **kwargs: Additional parameters for specific data types
        """
        super().__init__(tally_connector, f"Load {data_type.title()} Data")
        self.data_type = data_type.lower()
        self.load_params = kwargs
    
    def execute_tally_operation(self) -> Any:
        """Execute the data loading operation"""
        self.update_status(f"Loading {self.data_type} data from TallyPrime...")
        
        if self.data_type == "company":
            return self._load_company_info()
        elif self.data_type == "ledgers":
            return self._load_ledgers()
        elif self.data_type == "transactions":
            return self._load_transactions()
        elif self.data_type == "balance_sheet":
            return self._load_balance_sheet()
        else:
            raise ValueError(f"Unsupported data type: {self.data_type}")
    
    def _load_company_info(self):
        """Load company information"""
        self.update_progress(10, "Retrieving company details...")
        
        # Check for cancellation
        if self.is_cancelled:
            return None
        
        from ..tally.data_reader import TallyDataReader
        data_reader = TallyDataReader(self.tally_connector)
        
        self.update_progress(50, "Processing company data...")
        company_info = data_reader.get_company_info()
        
        if self.is_cancelled:
            return None
        
        self.update_progress(100, "Company information loaded successfully")
        return company_info
    
    def _load_ledgers(self):
        """Load ledger list with progress reporting"""
        self.update_progress(5, "Requesting ledger list from TallyPrime...")
        
        from ..tally.data_reader import TallyDataReader
        data_reader = TallyDataReader(self.tally_connector)
        
        # Get ledger count for progress calculation
        self.update_progress(15, "Analyzing ledger data...")
        ledgers = data_reader.get_all_ledgers_info()
        
        if self.is_cancelled:
            return None
        
        total_ledgers = len(ledgers)
        self.update_status(f"Processing {total_ledgers} ledgers...")
        
        # Simulate progress for detailed processing
        # (In real implementation, this would process ledgers in batches)
        for i in range(0, total_ledgers, max(1, total_ledgers // 10)):
            if self.is_cancelled:
                return None
            
            progress = int(20 + (i / total_ledgers) * 75)  # 20-95%
            self.update_progress(progress, f"Processing ledger {i+1} of {total_ledgers}...")
            
            # Small delay to show progress (remove in production)
            time.sleep(0.01)
        
        self.update_progress(100, f"Successfully loaded {total_ledgers} ledgers")
        return ledgers
    
    def _load_transactions(self):
        """Load transaction data (placeholder implementation)"""
        self.update_progress(25, "Loading recent transactions...")
        
        if self.is_cancelled:
            return None
        
        # Create mock transaction data using LedgerInfo objects
        from decimal import Decimal
        from ..models.ledger_model import LedgerInfo, LedgerBalance, LedgerType
        
        self.update_progress(50, "Processing transaction data...")
        
        transaction_ledgers = [
            LedgerInfo(
                name="Sales Account - Recent Transactions",
                ledger_type=LedgerType.INCOME,
                parent_group_name="Sales Accounts",
                balance=LedgerBalance(opening_balance=Decimal("5000.00"))
            ),
            LedgerInfo(
                name="Purchase Account - Recent Transactions", 
                ledger_type=LedgerType.EXPENSES,
                parent_group_name="Purchase Accounts",
                balance=LedgerBalance(opening_balance=Decimal("3000.00"))
            ),
            LedgerInfo(
                name="Cash Account - Recent Transactions",
                ledger_type=LedgerType.ASSETS,
                parent_group_name="Current Assets",
                balance=LedgerBalance(opening_balance=Decimal("12000.00"))
            )
        ]
        
        self.update_progress(100, "Transaction data loaded successfully")
        return transaction_ledgers
    
    def _load_balance_sheet(self):
        """Load balance sheet data (placeholder implementation)"""
        self.update_progress(10, "Loading balance sheet data...")
        
        if self.is_cancelled:
            return None
        
        # Create mock balance sheet data using LedgerInfo objects
        from decimal import Decimal
        from ..models.ledger_model import LedgerInfo, LedgerBalance, LedgerType
        
        self.update_progress(40, "Processing balance sheet components...")
        
        balance_sheet_ledgers = [
            LedgerInfo(
                name="Current Assets",
                ledger_type=LedgerType.ASSETS,
                parent_group_name="Balance Sheet",
                balance=LedgerBalance(opening_balance=Decimal("25000.00"))
            ),
            LedgerInfo(
                name="Current Liabilities",
                ledger_type=LedgerType.LIABILITIES,
                parent_group_name="Balance Sheet",
                balance=LedgerBalance(opening_balance=Decimal("15000.00"))
            ),
            LedgerInfo(
                name="Capital Account",
                ledger_type=LedgerType.CAPITAL,
                parent_group_name="Balance Sheet",
                balance=LedgerBalance(opening_balance=Decimal("10000.00"))
            )
        ]
        
        self.update_progress(100, "Balance sheet data loaded successfully")
        return balance_sheet_ledgers


# ================================================================================================
# THREAD POOL MANAGER
# ================================================================================================

class TaskManager(QObject):
    """
    Professional thread pool manager for background operations
    
    Features:
    - Centralized management of all background tasks
    - Priority-based task scheduling
    - Task cancellation and cleanup
    - Progress monitoring and reporting
    - Thread pool optimization for system resources
    - Integration with Qt's event system
    
    Learning: Demonstrates professional application architecture
    with centralized resource management and clean separation of concerns.
    """
    
    # Signals for task management
    task_added = Signal(UUID, str)           # task_id, task_name
    task_started = Signal(UUID)              # task_id
    task_completed = Signal(UUID, TaskResult) # task_id, result
    task_cancelled = Signal(UUID)            # task_id
    task_progress = Signal(UUID, TaskProgress) # task_id, progress
    
    def __init__(self, max_threads: int = 4):
        """
        Initialize task manager with thread pool
        
        Args:
            max_threads: Maximum number of concurrent threads
        """
        super().__init__()
        
        # Thread management
        self.max_threads = max_threads
        self._active_tasks: Dict[UUID, BaseWorkerThread] = {}
        self._task_history: List[TaskResult] = []
        
        # Thread safety
        self._mutex = QMutex()
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.TaskManager")
        
        self.logger.info(f"TaskManager initialized with {max_threads} max threads")
    
    def submit_task(self, worker: BaseWorkerThread) -> UUID:
        """
        Submit a task for background execution
        
        Args:
            worker: Worker thread to execute
            
        Returns:
            UUID: Task ID for tracking
        """
        with QMutexLocker(self._mutex):
            task_id = worker.task_id
            
            # Check if we're at thread limit
            if len(self._active_tasks) >= self.max_threads:
                self.logger.warning(f"Thread pool full ({len(self._active_tasks)}/{self.max_threads})")
                # In a production system, we'd implement a queue here
                raise RuntimeError("Thread pool is full - try again later")
            
            # Connect worker signals to our slots
            self._connect_worker_signals(worker)
            
            # Add to active tasks
            self._active_tasks[task_id] = worker
            
            self.logger.info(f"Task submitted: {worker.task_name} (ID: {task_id})")
            self.task_added.emit(task_id, worker.task_name)
            
            # Start the worker thread
            worker.start()
            
            return task_id
    
    def cancel_task(self, task_id: UUID) -> bool:
        """
        Cancel a running task
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            bool: True if cancellation was requested, False if task not found
        """
        with QMutexLocker(self._mutex):
            if task_id in self._active_tasks:
                worker = self._active_tasks[task_id]
                worker.cancel()
                self.logger.info(f"Cancellation requested for task: {task_id}")
                return True
            else:
                self.logger.warning(f"Cannot cancel task - not found: {task_id}")
                return False
    
    def cancel_all_tasks(self):
        """Cancel all running tasks"""
        with QMutexLocker(self._mutex):
            task_ids = list(self._active_tasks.keys())
        
        for task_id in task_ids:
            self.cancel_task(task_id)
        
        self.logger.info(f"Cancellation requested for {len(task_ids)} active tasks")
    
    def get_active_tasks(self) -> Dict[UUID, str]:
        """
        Get list of currently active tasks
        
        Returns:
            Dict[UUID, str]: Mapping of task ID to task name
        """
        with QMutexLocker(self._mutex):
            return {task_id: worker.task_name 
                   for task_id, worker in self._active_tasks.items()}
    
    def get_task_history(self, limit: int = 50) -> List[TaskResult]:
        """
        Get recent task execution history
        
        Args:
            limit: Maximum number of historical results to return
            
        Returns:
            List[TaskResult]: Recent task results
        """
        with QMutexLocker(self._mutex):
            return self._task_history[-limit:] if self._task_history else []
    
    def _connect_worker_signals(self, worker: BaseWorkerThread):
        """Connect worker thread signals to our slots"""
        worker.task_started.connect(self._on_task_started)
        worker.task_completed.connect(self._on_task_completed)
        worker.task_cancelled.connect(self._on_task_cancelled)
        worker.progress_updated.connect(self._on_task_progress)
        worker.finished.connect(lambda: self._on_worker_finished(worker.task_id))
    
    @Slot(UUID)
    def _on_task_started(self, task_id: UUID):
        """Handle task start notification"""
        self.task_started.emit(task_id)
    
    @Slot(UUID, TaskResult)
    def _on_task_completed(self, task_id: UUID, result: TaskResult):
        """Handle task completion"""
        with QMutexLocker(self._mutex):
            # Add to history
            self._task_history.append(result)
            
            # Log result
            if result.is_success:
                self.logger.info(f"Task completed: {task_id} ({result.execution_time_ms}ms)")
            else:
                self.logger.error(f"Task failed: {task_id} - {result.error}")
        
        self.task_completed.emit(task_id, result)
    
    @Slot(UUID)
    def _on_task_cancelled(self, task_id: UUID):
        """Handle task cancellation"""
        self.task_cancelled.emit(task_id)
    
    @Slot(UUID, TaskProgress)
    def _on_task_progress(self, task_id: UUID, progress: TaskProgress):
        """Handle task progress updates"""
        self.task_progress.emit(task_id, progress)
    
    def _on_worker_finished(self, task_id: UUID):
        """Clean up finished worker thread"""
        with QMutexLocker(self._mutex):
            if task_id in self._active_tasks:
                worker = self._active_tasks.pop(task_id)
                worker.deleteLater()
                self.logger.debug(f"Worker thread cleaned up: {task_id}")


# ================================================================================================
# CONVENIENCE FUNCTIONS
# ================================================================================================

def create_data_load_task(tally_connector, data_type: str, **kwargs) -> DataLoadWorker:
    """
    Convenience function to create data loading tasks
    
    Args:
        tally_connector: TallyConnector instance
        data_type: Type of data to load
        **kwargs: Additional parameters
        
    Returns:
        DataLoadWorker: Configured worker thread
    """
    return DataLoadWorker(tally_connector, data_type, **kwargs)


def create_task_manager(max_threads: int = None) -> TaskManager:
    """
    Convenience function to create task manager
    
    Args:
        max_threads: Maximum concurrent threads (auto-detect if None)
        
    Returns:
        TaskManager: Configured task manager
    """
    if max_threads is None:
        # Auto-detect based on CPU cores (minimum 2, maximum 8)
        import os
        cpu_count = os.cpu_count() or 2
        max_threads = max(2, min(8, cpu_count))
    
    return TaskManager(max_threads)


# ================================================================================================
# THREAD-SAFE LOGGING INTEGRATION
# ================================================================================================

class ThreadSafeLogger:
    """
    Thread-safe logging wrapper for background operations
    
    This class provides:
    - Thread-safe logging operations
    - Integration with ProfessionalLogWidget
    - Automatic thread identification in log messages
    - Proper handling of logging from worker threads
    """
    
    def __init__(self, logger_name: str):
        """Initialize thread-safe logger wrapper"""
        self.logger = logging.getLogger(logger_name)
        self._mutex = QMutex()
    
    def log(self, level: int, message: str, **kwargs):
        """Thread-safe logging method"""
        with QMutexLocker(self._mutex):
            # Add thread information to log message
            thread_name = QThread.currentThread().objectName() or "MainThread"
            formatted_message = f"[{thread_name}] {message}"
            
            self.logger.log(level, formatted_message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Thread-safe debug logging"""
        self.log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Thread-safe info logging"""
        self.log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Thread-safe warning logging"""
        self.log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Thread-safe error logging"""
        self.log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Thread-safe critical logging"""
        self.log(logging.CRITICAL, message, **kwargs)


# ================================================================================================
# EXAMPLE USAGE AND TESTING
# ================================================================================================

if __name__ == "__main__":
    """
    Example usage of the threading framework
    
    This section demonstrates how to use the threading utilities
    in a real application context.
    """
    
    print("TallyPrime Integration Manager - Threading Framework")
    print("=" * 60)
    print("This module provides professional threading utilities for")
    print("background operations in the TallyPrime Integration Manager.")
    print()
    print("Key Features:")
    print("- Standardized Qt worker thread patterns")
    print("- Progress reporting and task cancellation") 
    print("- Thread pool management")
    print("- Thread-safe logging integration")
    print("- Comprehensive error handling")
    print()
    print("See the test files for usage examples and integration tests.")
"""
Audit Trail System for TallyPrime Integration

This module provides comprehensive audit trail functionality for tracking voucher posting
operations, errors, and system activities with professional logging and persistence.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 30, 2025
Framework: PySide6 (Qt6)
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import logging
import os
from pathlib import Path
from decimal import Decimal

# PySide6 imports for signals
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Enumeration of audit event types"""
    VOUCHER_CREATED = "voucher_created"
    VOUCHER_POSTED = "voucher_posted"
    POSTING_FAILED = "posting_failed"
    VALIDATION_FAILED = "validation_failed"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_FAILED = "connection_failed"
    DATA_EXPORT = "data_export"
    SYSTEM_ERROR = "system_error"
    USER_ACTION = "user_action"


class AuditSeverity(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Data class representing a single audit trail event
    
    This class captures comprehensive information about system activities
    for compliance, debugging, and user feedback purposes.
    """
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    description: str
    
    # Context information
    user_name: Optional[str] = None
    voucher_number: Optional[str] = None
    company_name: Optional[str] = None
    operation_id: Optional[str] = None
    
    # Technical details
    details: Dict[str, Any] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None
    
    # TallyPrime specific
    tally_voucher_id: Optional[str] = None
    tally_response_code: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def severity_icon(self) -> str:
        """Get emoji icon for severity level"""
        return {
            AuditSeverity.INFO: "ℹ️",
            AuditSeverity.WARNING: "⚠️",
            AuditSeverity.ERROR: "❌",
            AuditSeverity.CRITICAL: "🔥"
        }.get(self.severity, "📝")
    
    @property
    def event_icon(self) -> str:
        """Get emoji icon for event type"""
        return {
            AuditEventType.VOUCHER_CREATED: "📝",
            AuditEventType.VOUCHER_POSTED: "📤",
            AuditEventType.POSTING_FAILED: "❌",
            AuditEventType.VALIDATION_FAILED: "⚠️",
            AuditEventType.CONNECTION_ESTABLISHED: "🔗",
            AuditEventType.CONNECTION_FAILED: "💔",
            AuditEventType.DATA_EXPORT: "📊",
            AuditEventType.SYSTEM_ERROR: "🔧",
            AuditEventType.USER_ACTION: "👤"
        }.get(self.event_type, "📋")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime to ISO format string
        data['timestamp'] = self.timestamp.isoformat()
        # Convert enums to string values
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create audit event from dictionary"""
        # Convert timestamp back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        # Convert enum strings back to enums
        data['event_type'] = AuditEventType(data['event_type'])
        data['severity'] = AuditSeverity(data['severity'])
        return cls(**data)
    
    def get_summary_text(self) -> str:
        """Get a human-readable summary of the event"""
        parts = [
            f"{self.severity_icon} {self.event_icon}",
            self.timestamp.strftime("%H:%M:%S"),
            self.description
        ]
        
        if self.voucher_number:
            parts.append(f"(Voucher: {self.voucher_number})")
        
        if self.response_time_ms:
            parts.append(f"({self.response_time_ms:.0f}ms)")
        
        return " ".join(parts)


class AuditTrailManager(QObject):
    """
    Professional audit trail management system
    
    This class provides comprehensive audit trail functionality with:
    - Real-time event tracking and logging
    - Persistent storage with JSON serialization
    - Qt6 signals for UI integration
    - Professional filtering and search capabilities
    - Automatic cleanup and retention policies
    
    Learning Points:
    - Professional audit trail design
    - Event-driven architecture with Qt signals
    - Data persistence and serialization
    - Performance-optimized logging
    """
    
    # Qt signals for real-time UI updates
    event_logged = Signal(AuditEvent)
    trail_updated = Signal()
    
    def __init__(self, storage_directory: Optional[str] = None):
        """
        Initialize the audit trail manager
        
        Args:
            storage_directory: Directory for audit trail storage (default: app data)
        """
        super().__init__()
        
        # Configuration
        self.max_events_in_memory = 1000
        self.max_file_size_mb = 10
        self.retention_days = 90
        
        # Storage
        if storage_directory:
            self.storage_dir = Path(storage_directory)
        else:
            # Default to application data directory
            self.storage_dir = Path.home() / ".tally_integration" / "audit_logs"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = self.storage_dir / f"audit_{datetime.now().strftime('%Y%m')}.json"
        
        # In-memory event storage for performance
        self.recent_events: List[AuditEvent] = []
        
        # Load recent events from storage
        self._load_recent_events()
        
        logger.info(f"AuditTrailManager initialized - Storage: {self.storage_dir}")
    
    def log_event(
        self,
        event_type: AuditEventType,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        **kwargs
    ) -> AuditEvent:
        """
        Log a new audit event with comprehensive information capture
        
        Args:
            event_type: Type of event being logged
            description: Human-readable description
            severity: Severity level of the event
            **kwargs: Additional context information
            
        Returns:
            Created AuditEvent object
        """
        # Create audit event
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            description=description,
            **kwargs
        )
        
        # Add to in-memory storage
        self.recent_events.append(event)
        
        # Maintain memory limits
        if len(self.recent_events) > self.max_events_in_memory:
            self.recent_events.pop(0)
        
        # Persist to storage
        self._persist_event(event)
        
        # Emit signals for UI updates
        self.event_logged.emit(event)
        self.trail_updated.emit()
        
        # Log to system logger as well
        log_level = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }.get(severity, logging.INFO)
        
        logger.log(log_level, f"AUDIT: {description}")
        
        return event
    
    def log_voucher_posted(
        self,
        voucher_number: str,
        voucher_id: str,
        response_time_ms: float,
        company_name: Optional[str] = None
    ) -> AuditEvent:
        """Convenience method for logging successful voucher posting"""
        return self.log_event(
            event_type=AuditEventType.VOUCHER_POSTED,
            severity=AuditSeverity.INFO,
            description=f"Voucher {voucher_number} posted successfully",
            voucher_number=voucher_number,
            tally_voucher_id=voucher_id,
            company_name=company_name,
            response_time_ms=response_time_ms
        )
    
    def log_posting_failed(
        self,
        voucher_number: str,
        error_message: str,
        error_type: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> AuditEvent:
        """Convenience method for logging failed voucher posting"""
        return self.log_event(
            event_type=AuditEventType.POSTING_FAILED,
            severity=AuditSeverity.ERROR,
            description=f"Failed to post voucher {voucher_number}",
            voucher_number=voucher_number,
            error_message=error_message,
            company_name=company_name,
            details={'error_type': error_type} if error_type else {}
        )
    
    def log_connection_event(
        self,
        success: bool,
        company_name: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AuditEvent:
        """Convenience method for logging connection events"""
        if success:
            return self.log_event(
                event_type=AuditEventType.CONNECTION_ESTABLISHED,
                severity=AuditSeverity.INFO,
                description=f"Connected to TallyPrime" + (f" - {company_name}" if company_name else ""),
                company_name=company_name
            )
        else:
            return self.log_event(
                event_type=AuditEventType.CONNECTION_FAILED,
                severity=AuditSeverity.ERROR,
                description="Failed to connect to TallyPrime",
                error_message=error_message
            )
    
    def log_user_action(
        self,
        action_description: str,
        user_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Convenience method for logging user actions"""
        return self.log_event(
            event_type=AuditEventType.USER_ACTION,
            severity=AuditSeverity.INFO,
            description=action_description,
            user_name=user_name,
            details=details or {}
        )
    
    def get_recent_events(self, limit: Optional[int] = None) -> List[AuditEvent]:
        """
        Get recent audit events from memory
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent audit events, newest first
        """
        events = list(reversed(self.recent_events))  # Newest first
        if limit:
            return events[:limit]
        return events
    
    def get_events_by_type(self, event_type: AuditEventType, limit: int = 100) -> List[AuditEvent]:
        """Get events filtered by type"""
        events = [e for e in self.recent_events if e.event_type == event_type]
        return list(reversed(events))[:limit]
    
    def get_events_by_voucher(self, voucher_number: str) -> List[AuditEvent]:
        """Get all events related to a specific voucher"""
        return [e for e in self.recent_events if e.voucher_number == voucher_number]
    
    def get_events_in_timerange(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[AuditEvent]:
        """Get events within a specific time range"""
        return [
            e for e in self.recent_events
            if start_time <= e.timestamp <= end_time
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics for dashboard display"""
        total_events = len(self.recent_events)
        
        # Count by type
        type_counts = {}
        for event_type in AuditEventType:
            type_counts[event_type.value] = len(self.get_events_by_type(event_type))
        
        # Count by severity
        severity_counts = {}
        for severity in AuditSeverity:
            severity_counts[severity.value] = len([
                e for e in self.recent_events if e.severity == severity
            ])
        
        # Recent activity (last hour)
        one_hour_ago = datetime.now().replace(minute=0, second=0, microsecond=0)
        recent_activity = len(self.get_events_in_timerange(one_hour_ago, datetime.now()))
        
        return {
            'total_events': total_events,
            'events_by_type': type_counts,
            'events_by_severity': severity_counts,
            'recent_activity_count': recent_activity,
            'storage_location': str(self.storage_dir),
            'current_file': str(self.current_file)
        }
    
    def export_events(
        self,
        output_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None
    ) -> int:
        """
        Export audit events to JSON file with filtering
        
        Args:
            output_file: Path to output file
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to include
            
        Returns:
            Number of events exported
        """
        # Apply filters
        events_to_export = self.recent_events.copy()
        
        if start_date:
            events_to_export = [e for e in events_to_export if e.timestamp >= start_date]
        
        if end_date:
            events_to_export = [e for e in events_to_export if e.timestamp <= end_date]
        
        if event_types:
            events_to_export = [e for e in events_to_export if e.event_type in event_types]
        
        # Convert to dictionaries for JSON serialization
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_events': len(events_to_export),
            'filters': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'event_types': [et.value for et in event_types] if event_types else None
            },
            'events': [event.to_dict() for event in events_to_export]
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(events_to_export)} audit events to {output_file}")
        return len(events_to_export)
    
    def _persist_event(self, event: AuditEvent):
        """Persist single event to storage file"""
        try:
            # Check if we need to rotate the log file
            if self.current_file.exists() and self.current_file.stat().st_size > (self.max_file_size_mb * 1024 * 1024):
                self._rotate_log_file()
            
            # Append event to current log file
            event_data = event.to_dict()
            
            # Read existing events if file exists
            if self.current_file.exists():
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                        events = existing_data.get('events', [])
                    except json.JSONDecodeError:
                        events = []
            else:
                events = []
            
            # Add new event
            events.append(event_data)
            
            # Write back to file
            log_data = {
                'file_created': datetime.now().isoformat(),
                'total_events': len(events),
                'events': events
            }
            
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error persisting audit event: {str(e)}")
    
    def _load_recent_events(self):
        """Load recent events from storage into memory"""
        if not self.current_file.exists():
            return
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                events_data = data.get('events', [])
                
                # Load events into memory (limit to recent ones)
                recent_events_data = events_data[-self.max_events_in_memory:]
                
                for event_data in recent_events_data:
                    try:
                        event = AuditEvent.from_dict(event_data)
                        self.recent_events.append(event)
                    except Exception as e:
                        logger.warning(f"Error loading audit event: {str(e)}")
                
                logger.info(f"Loaded {len(self.recent_events)} recent audit events")
        
        except Exception as e:
            logger.error(f"Error loading audit events from storage: {str(e)}")
    
    def _rotate_log_file(self):
        """Rotate the current log file when it gets too large"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archived_file = self.storage_dir / f"audit_archived_{timestamp}.json"
        
        try:
            self.current_file.rename(archived_file)
            logger.info(f"Rotated audit log file to {archived_file}")
            
            # Create new current file
            self.current_file = self.storage_dir / f"audit_{datetime.now().strftime('%Y%m')}.json"
            
        except Exception as e:
            logger.error(f"Error rotating audit log file: {str(e)}")
    
    def cleanup_old_logs(self):
        """Clean up old audit log files based on retention policy"""
        try:
            cutoff_date = datetime.now().timestamp() - (self.retention_days * 24 * 3600)
            
            for log_file in self.storage_dir.glob("audit_*.json"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Cleaned up old audit log: {log_file}")
        
        except Exception as e:
            logger.error(f"Error during audit log cleanup: {str(e)}")


# Global audit trail manager instance
_audit_manager: Optional[AuditTrailManager] = None


def get_audit_manager() -> AuditTrailManager:
    """Get or create the global audit trail manager instance"""
    global _audit_manager
    if _audit_manager is None:
        _audit_manager = AuditTrailManager()
    return _audit_manager


def log_audit_event(
    event_type: AuditEventType,
    description: str,
    severity: AuditSeverity = AuditSeverity.INFO,
    **kwargs
) -> AuditEvent:
    """Convenience function for logging audit events"""
    return get_audit_manager().log_event(event_type, description, severity, **kwargs)
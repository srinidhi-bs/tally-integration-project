#!/usr/bin/env python3
"""
TallyPrime Connection Framework for Professional GUI Application

This module provides comprehensive HTTP-XML communication with TallyPrime Gateway.
Built with Qt6 integration for signal-based communication and robust error handling.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 26, 2025
Framework: PySide6 (Qt6)
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import time
from decimal import Decimal, InvalidOperation
import socket
from urllib.parse import urlparse

# Qt6 imports for signal-slot communication
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# Application logging
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """
    Enumeration of possible connection states
    Professional status management for UI updates
    """
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"  
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"
    TESTING = "testing"


@dataclass
class TallyConnectionConfig:
    """
    Data class to store TallyPrime connection configuration
    Provides type-safe configuration management
    """
    host: str = "172.28.208.1"  # Default Windows host IP from WSL
    port: int = 9000            # Default TallyPrime HTTP Gateway port
    timeout: int = 30           # Connection timeout in seconds
    retry_count: int = 3        # Number of retry attempts
    retry_delay: float = 1.0    # Delay between retries in seconds
    user_agent: str = "TallyPrime Integration Manager v1.0"
    enable_pooling: bool = True  # Enable connection pooling for performance
    auto_discover: bool = False  # Enable automatic TallyPrime discovery
    verbose_logging: bool = False  # Enable verbose logging for debugging
    
    @property
    def url(self) -> str:
        """Get the complete TallyPrime URL"""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            'host': self.host,
            'port': self.port,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'user_agent': self.user_agent,
            'enable_pooling': self.enable_pooling,
            'auto_discover': self.auto_discover,
            'verbose_logging': self.verbose_logging
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TallyConnectionConfig':
        """Create configuration from dictionary"""
        return cls(**data)


@dataclass 
class TallyResponse:
    """
    Data class to encapsulate TallyPrime HTTP response
    Provides structured response handling with error information
    """
    success: bool
    data: str
    status_code: int
    error_message: Optional[str] = None
    response_time: float = 0.0
    content_type: Optional[str] = None
    
    def __bool__(self) -> bool:
        """Allow boolean evaluation of response"""
        return self.success


@dataclass
class CompanyInfo:
    """
    Data class to store TallyPrime company information
    Used for displaying company details in the GUI
    """
    name: str
    guid: str = ""
    financial_year_from: str = ""
    financial_year_to: str = ""
    base_currency: str = ""
    books_from: str = ""
    
    def __str__(self) -> str:
        return f"{self.name} ({self.financial_year_from} - {self.financial_year_to})"


@dataclass
class PostingProgress:
    """
    Data class to track voucher posting progress
    Professional progress tracking for UI updates and user feedback
    """
    stage: str = "Preparing"
    progress_percent: int = 0
    current_step: str = ""
    total_steps: int = 1
    current_step_number: int = 1
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    
    @property
    def is_complete(self) -> bool:
        """Check if posting is complete"""
        return self.progress_percent >= 100
    
    @property 
    def progress_description(self) -> str:
        """Get human-readable progress description"""
        return f"[{self.current_step_number}/{self.total_steps}] {self.current_step}"

class VoucherPostingErrorType(Enum):
    """
    Enumeration of voucher posting error types for classification
    Professional error categorization for appropriate user feedback
    """
    NETWORK_ERROR = "network_error"
    MISSING_LEDGER = "missing_ledger"
    INVALID_VOUCHER_TYPE = "invalid_voucher_type"
    UNBALANCED_ENTRY = "unbalanced_entry"
    MALFORMED_XML = "malformed_xml"
    DUPLICATE_VOUCHER = "duplicate_voucher"
    ACCESS_DENIED = "access_denied"
    COMPANY_ERROR = "company_error"
    VALIDATION_ERROR = "validation_error"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    XML_PARSE_ERROR = "xml_parse_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class VoucherValidationResult:
    """
    Data class to store voucher validation results
    Used for pre-validation before posting to provide better user feedback
    """
    is_valid: bool
    issues: List[str]
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass  
class VoucherPostingResult:
    """
    Comprehensive result object for voucher posting operations
    
    This class encapsulates all information about a voucher posting attempt,
    including success/failure status, error details, and TallyPrime response data.
    
    Learning Points:
    - Comprehensive result objects for complex operations
    - Professional error handling with classification
    - Rich data for user feedback and debugging
    """
    success: bool
    voucher_id: Optional[str] = None
    created_count: int = 0
    altered_count: int = 0
    deleted_count: int = 0
    ignored_count: int = 0
    cancelled_count: int = 0
    
    # Error information
    error_type: Optional[VoucherPostingErrorType] = None
    error_message: Optional[str] = None
    error_details: List[str] = None
    
    # Performance and debugging
    response_time: float = 0.0
    raw_response: str = ""
    validation_result: Optional[VoucherValidationResult] = None
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []
    
    @property
    def total_processed(self) -> int:
        """Total number of vouchers processed (successful + failed)"""
        return self.created_count + self.altered_count + self.deleted_count
    
    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during processing"""
        return not self.success or self.error_type is not None
    
    @property
    def user_friendly_message(self) -> str:
        """Get a user-friendly status message"""
        if self.success:
            if self.created_count > 0:
                return f"✅ Voucher created successfully (ID: {self.voucher_id})"
            elif self.altered_count > 0:
                return f"✅ Voucher updated successfully (ID: {self.voucher_id})"
            else:
                return "✅ Operation completed successfully"
        else:
            error_prefix = "❌ Posting failed:"
            if self.error_type:
                return f"{error_prefix} {self.error_type.value.replace('_', ' ').title()}"
            else:
                return f"{error_prefix} {self.error_message or 'Unknown error'}"
    
    def get_detailed_summary(self) -> Dict[str, Any]:
        """Get detailed summary for logging and debugging"""
        return {
            'success': self.success,
            'voucher_id': self.voucher_id,
            'counts': {
                'created': self.created_count,
                'altered': self.altered_count,
                'deleted': self.deleted_count,
                'ignored': self.ignored_count,
                'cancelled': self.cancelled_count,
                'total_processed': self.total_processed
            },
            'error': {
                'type': self.error_type.value if self.error_type else None,
                'message': self.error_message,
                'details': self.error_details
            },
            'performance': {
                'response_time_ms': self.response_time * 1000,
                'response_size': len(self.raw_response)
            }
        }

class TallyConnector(QObject):
    """
    Professional TallyPrime HTTP-XML Gateway Connector
    
    This class provides comprehensive communication with TallyPrime using Qt6 signals
    for real-time status updates and professional error handling.
    
    Features:
    - Qt6 signal-slot integration for GUI updates
    - Automatic connection testing and validation
    - Robust error handling with detailed messages
    - Connection pooling and session management
    - Auto-discovery of TallyPrime instances
    - Configuration persistence and management
    - Professional logging integration
    
    Signals:
        connection_status_changed: Emitted when connection status changes
        company_info_received: Emitted when company information is retrieved
        error_occurred: Emitted when errors occur
        data_received: Emitted when data is successfully retrieved
    """
    
    # Qt6 Signals for real-time GUI communication
    connection_status_changed = Signal(ConnectionStatus, str)  # status, message
    company_info_received = Signal(CompanyInfo)
    error_occurred = Signal(str, str)  # error_type, error_message
    data_received = Signal(str, dict)  # operation_name, data
    posting_progress = Signal(PostingProgress)  # posting progress updates
    voucher_posted = Signal('VoucherPostingResult')  # voucher posting completed
    
    def __init__(self, config: Optional[TallyConnectionConfig] = None):
        """
        Initialize TallyPrime connector with configuration
        
        Args:
            config: Connection configuration, uses defaults if None
        """
        super().__init__()
        
        # Initialize configuration
        self.config = config or TallyConnectionConfig()
        
        # Connection state management
        self._status = ConnectionStatus.DISCONNECTED
        self._last_error = ""
        self._company_info: Optional[CompanyInfo] = None
        
        # HTTP session for connection pooling and performance
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Content-Type': 'application/xml; charset=utf-8',
            'Accept': 'application/xml, text/xml, */*'
        })
        
        # Performance tracking
        self._last_response_time = 0.0
        self._total_requests = 0
        self._successful_requests = 0
        
        # Auto-refresh timer for connection monitoring
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._monitor_connection)
        
        logger.info(f"TallyConnector initialized for {self.config.url}")
    
    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status"""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected to TallyPrime"""
        return self._status == ConnectionStatus.CONNECTED
    
    @property
    def last_error(self) -> str:
        """Get the last error message"""
        return self._last_error
    
    @property
    def company_info(self) -> Optional[CompanyInfo]:
        """Get current company information"""
        return self._company_info
    
    @property
    def connection_stats(self) -> Dict[str, Any]:
        """Get connection performance statistics"""
        success_rate = (
            (self._successful_requests / self._total_requests * 100) 
            if self._total_requests > 0 else 0.0
        )
        
        return {
            'total_requests': self._total_requests,
            'successful_requests': self._successful_requests,
            'success_rate': round(success_rate, 2),
            'last_response_time': self._last_response_time,
            'current_status': self._status.value,
            'url': self.config.url
        }
    
    def update_config(self, new_config: TallyConnectionConfig):
        """
        Update the connection configuration with new settings
        
        This method allows dynamic reconfiguration of the TallyConnector
        without recreating the instance. Useful for settings dialog updates.
        
        Args:
            new_config: New TallyPrime connection configuration
            
        Learning: This method demonstrates how to safely update configuration
        while maintaining existing connections and state where possible.
        """
        try:
            logger.info(f"Updating connection configuration from {self.config.host}:{self.config.port} "
                       f"to {new_config.host}:{new_config.port}")
            
            # Store old configuration for comparison
            old_config = self.config
            
            # Update the configuration
            self.config = new_config
            
            # Update session headers with new user agent if changed
            if old_config.user_agent != new_config.user_agent:
                self.session.headers.update({
                    'User-Agent': new_config.user_agent
                })
            
            # If host or port changed, disconnect and clear cached data
            if (old_config.host != new_config.host or 
                old_config.port != new_config.port):
                
                # Reset connection status
                self._set_status(ConnectionStatus.DISCONNECTED, 
                               "Configuration updated - ready to connect")
                
                # Clear cached company information
                self._company_info = None
                
                logger.info("Connection configuration updated - host/port changed")
                
            else:
                # Just timeout or retry settings changed
                logger.info("Connection configuration updated - performance settings changed")
                
            # Emit signal to notify UI of configuration change
            self.connection_status_changed.emit(self._status, 
                                              f"Settings updated: {new_config.host}:{new_config.port}")
            
        except Exception as e:
            logger.error(f"Error updating connection configuration: {str(e)}")
            self.error_occurred.emit("CONFIG_UPDATE_ERROR", str(e))
    
    def _set_status(self, status: ConnectionStatus, message: str = ""):
        """
        Internal method to update connection status and emit signal
        
        Args:
            status: New connection status
            message: Optional status message
        """
        if status != self._status:
            self._status = status
            logger.info(f"Connection status changed: {status.value} - {message}")
            self.connection_status_changed.emit(status, message)
    
    def _handle_error(self, error_type: str, error_message: str):
        """
        Internal method to handle errors consistently
        
        Args:
            error_type: Type of error (connection, timeout, xml, etc.)
            error_message: Detailed error message
        """
        self._last_error = error_message
        self._set_status(ConnectionStatus.ERROR, error_message)
        logger.error(f"{error_type}: {error_message}")
        self.error_occurred.emit(error_type, error_message)
    
    def send_xml_request(self, xml_request: str, description: str = "") -> TallyResponse:
        """
        Send XML request to TallyPrime with comprehensive error handling
        
        This is the core method that communicates with TallyPrime HTTP Gateway.
        It includes retry logic, performance tracking, and detailed error reporting.
        
        Args:
            xml_request: XML request string to send to TallyPrime
            description: Human-readable description for logging
            
        Returns:
            TallyResponse object with success status and response data
        """
        start_time = time.time()
        self._total_requests += 1
        
        # Log the request
        if description:
            logger.info(f"Sending XML request: {description}")
        
        # Prepare request headers with proper encoding
        headers = {
            'Content-Type': 'application/xml; charset=utf-8',
            'Content-Length': str(len(xml_request.encode('utf-8'))),
            'Connection': 'keep-alive'
        }
        
        # Retry logic for robust communication
        for attempt in range(self.config.retry_count):
            try:
                # Send POST request to TallyPrime
                response = self.session.post(
                    self.config.url,
                    data=xml_request.encode('utf-8'),
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                # Calculate response time
                response_time = time.time() - start_time
                self._last_response_time = response_time
                
                # Check HTTP status code
                if response.status_code == 200:
                    self._successful_requests += 1
                    
                    logger.debug(f"Request successful in {response_time:.2f}s")
                    
                    return TallyResponse(
                        success=True,
                        data=response.text,
                        status_code=response.status_code,
                        response_time=response_time,
                        content_type=response.headers.get('Content-Type')
                    )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.reason}"
                    logger.warning(f"HTTP error on attempt {attempt + 1}: {error_msg}")
                    
                    if attempt == self.config.retry_count - 1:  # Last attempt
                        return TallyResponse(
                            success=False,
                            data="",
                            status_code=response.status_code,
                            error_message=error_msg,
                            response_time=time.time() - start_time
                        )
            
            except requests.exceptions.ConnectionError as e:
                error_msg = f"Connection refused - TallyPrime may not be running"
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                
                if attempt == self.config.retry_count - 1:
                    self._handle_error("CONNECTION_ERROR", error_msg)
                    return TallyResponse(
                        success=False,
                        data="",
                        status_code=0,
                        error_message=error_msg,
                        response_time=time.time() - start_time
                    )
            
            except requests.exceptions.Timeout as e:
                error_msg = f"Request timeout after {self.config.timeout}s"
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                
                if attempt == self.config.retry_count - 1:
                    self._handle_error("TIMEOUT", error_msg)
                    return TallyResponse(
                        success=False,
                        data="",
                        status_code=0,
                        error_message=error_msg,
                        response_time=time.time() - start_time
                    )
            
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                
                if attempt == self.config.retry_count - 1:
                    self._handle_error("UNEXPECTED_ERROR", error_msg)
                    return TallyResponse(
                        success=False,
                        data="",
                        status_code=0,
                        error_message=error_msg,
                        response_time=time.time() - start_time
                    )
            
            # Wait before retry (except on last attempt)
            if attempt < self.config.retry_count - 1:
                time.sleep(self.config.retry_delay)
                logger.info(f"Retrying request in {self.config.retry_delay}s...")
        
        # This should never be reached, but included for completeness
        return TallyResponse(
            success=False,
            data="",
            status_code=0,
            error_message="Maximum retry attempts exceeded",
            response_time=time.time() - start_time
        )
    
    def test_connection(self) -> bool:
        """
        Test connection to TallyPrime with basic company information request
        
        This method performs a lightweight test to verify TallyPrime connectivity
        and retrieves basic company information if successful.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        logger.info("Testing TallyPrime connection...")
        self._set_status(ConnectionStatus.TESTING, "Testing connection...")
        
        # Use a simple request that should work with most TallyPrime setups
        # This matches the working pattern from working_tally_reader.py
        xml_request = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Companies</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
        
        response = self.send_xml_request(xml_request, "Connection Test")
        
        if response.success:
            # Try to parse company information from the response
            try:
                # Parse XML response to extract company info
                root = ET.fromstring(response.data)
                
                # Look for company information in various XML structures
                company_name = "Connected Company"
                
                # Try to find company name in common XML patterns
                for elem in root.iter():
                    if 'COMPANY' in elem.tag or 'NAME' in elem.tag:
                        if elem.text and len(elem.text.strip()) > 0:
                            company_name = elem.text.strip()
                            break
                
                # Create company info object
                self._company_info = CompanyInfo(name=company_name)
                
                self._set_status(ConnectionStatus.CONNECTED, f"Connected to {company_name}")
                self.company_info_received.emit(self._company_info)
                
                logger.info(f"Connection test successful - Company: {company_name}")
                return True
                
            except ET.ParseError as e:
                # Even if XML parsing fails, if we got a response, connection works
                logger.warning(f"XML parsing failed but connection is working: {e}")
                self._company_info = CompanyInfo(name="Unknown Company")
                self._set_status(ConnectionStatus.CONNECTED, "Connected (XML parsing issue)")
                return True
                
        else:
            logger.error(f"Connection test failed: {response.error_message}")
            return False
    
    def get_company_information(self) -> Optional[CompanyInfo]:
        """
        Retrieve detailed company information from TallyPrime
        
        Returns:
            CompanyInfo object if successful, None otherwise
        """
        logger.info("Retrieving company information...")
        
        # XML request for company details - using working pattern
        xml_request = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Company Features</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
        
        response = self.send_xml_request(xml_request, "Company Information")
        
        if response.success:
            try:
                root = ET.fromstring(response.data)
                
                # Extract company information from XML
                company_info = CompanyInfo(name="TallyPrime Company")
                
                # Parse various company details from XML response
                for elem in root.iter():
                    text = elem.text.strip() if elem.text else ""
                    
                    if 'NAME' in elem.tag and text:
                        company_info.name = text
                    elif 'GUID' in elem.tag and text:
                        company_info.guid = text
                    elif 'CURRENCY' in elem.tag and text:
                        company_info.base_currency = text
                
                self._company_info = company_info
                self.company_info_received.emit(company_info)
                
                logger.info(f"Company information retrieved: {company_info.name}")
                return company_info
                
            except ET.ParseError as e:
                error_msg = f"Failed to parse company information XML: {e}"
                self._handle_error("XML_PARSE_ERROR", error_msg)
                return None
        else:
            logger.error("Failed to retrieve company information")
            return None
    
    def discover_tally_instances(self) -> List[Tuple[str, int]]:
        """
        Auto-discover TallyPrime instances on the network
        
        This method scans common ports on localhost and the configured host
        to find running TallyPrime instances.
        
        Returns:
            List of (host, port) tuples where TallyPrime is detected
        """
        logger.info("Discovering TallyPrime instances...")
        
        # Common TallyPrime ports
        common_ports = [9000, 9001, 9002, 8000, 8080, 9999]
        
        # Hosts to check
        hosts_to_check = ["localhost", "127.0.0.1", self.config.host]
        if self.config.host not in hosts_to_check:
            hosts_to_check.append(self.config.host)
        
        discovered_instances = []
        
        for host in hosts_to_check:
            for port in common_ports:
                try:
                    # Quick socket test to see if port is open
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)  # Quick timeout for discovery
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:  # Port is open
                        # Test if it's actually TallyPrime by sending a basic request
                        test_config = TallyConnectionConfig(host=host, port=port, timeout=5)
                        test_connector = TallyConnector(test_config)
                        
                        if test_connector.test_connection():
                            discovered_instances.append((host, port))
                            logger.info(f"TallyPrime instance discovered at {host}:{port}")
                
                except Exception as e:
                    # Skip this host:port combination
                    continue
        
        logger.info(f"Discovery complete. Found {len(discovered_instances)} instances.")
        return discovered_instances
    
    def start_connection_monitoring(self, interval_ms: int = 30000):
        """
        Start automatic connection monitoring
        
        Args:
            interval_ms: Monitoring interval in milliseconds (default: 30 seconds)
        """
        if not self._monitor_timer.isActive():
            self._monitor_timer.start(interval_ms)
            logger.info(f"Connection monitoring started (interval: {interval_ms/1000}s)")
    
    def stop_connection_monitoring(self):
        """Stop automatic connection monitoring"""
        if self._monitor_timer.isActive():
            self._monitor_timer.stop()
            logger.info("Connection monitoring stopped")
    
    def _monitor_connection(self):
        """Internal method for periodic connection monitoring"""
        if self._status == ConnectionStatus.CONNECTED:
            # Quick ping test to verify connection is still alive
            success = self.test_connection()
            if not success:
                self._set_status(ConnectionStatus.DISCONNECTED, "Connection lost")
    
    def close(self):
        """
        Clean shutdown of the connector
        Closes sessions and stops timers
        """
        self.stop_connection_monitoring()
        
        if hasattr(self, 'session'):
            self.session.close()
        
        logger.info("TallyConnector closed")

    
    # Voucher Posting Methods
    
    def post_voucher(self, voucher_xml: str, description: str = "Voucher Posting") -> 'VoucherPostingResult':
        """
        Post a voucher to TallyPrime using HTTP-XML Gateway with progress tracking
        
        This method handles the complete voucher posting workflow including:
        - Progress tracking with real-time updates
        - XML envelope wrapping for TallyPrime import format
        - Response parsing and validation
        - Error classification and handling
        - Success/failure reporting with detailed feedback
        
        Args:
            voucher_xml: Complete TallyPrime voucher XML content
            description: Human-readable description for logging
            
        Returns:
            VoucherPostingResult object with success status, voucher ID, and details
            
        Learning Points:
        - Professional voucher posting workflow with progress tracking
        - TallyPrime import XML format handling
        - Response parsing and error classification
        - Business logic validation and feedback
        """
        start_time = time.time()
        logger.info(f"Posting voucher to TallyPrime: {description}")
        
        # Step 1: Preparing voucher (10%)
        progress = PostingProgress(
            stage="Preparing",
            progress_percent=10,
            current_step="Preparing voucher XML for posting",
            total_steps=4,
            current_step_number=1,
            elapsed_time=time.time() - start_time
        )
        self.posting_progress.emit(progress)
        
        # Wrap voucher XML in import envelope format
        import_xml = self._wrap_voucher_for_import(voucher_xml)
        
        # Step 2: Sending request (30%)
        progress.stage = "Sending"
        progress.progress_percent = 30
        progress.current_step = "Sending voucher to TallyPrime"
        progress.current_step_number = 2
        progress.elapsed_time = time.time() - start_time
        self.posting_progress.emit(progress)
        
        # Send the posting request
        response = self.send_xml_request(import_xml, f"Voucher Post - {description}")
        
        if not response.success:
            # Step 3: Error occurred (100%)
            progress.stage = "Error"
            progress.progress_percent = 100
            progress.current_step = f"Network error: {response.error_message}"
            progress.current_step_number = 4
            progress.elapsed_time = time.time() - start_time
            self.posting_progress.emit(progress)
            
            # Network or HTTP-level error
            result = VoucherPostingResult(
                success=False,
                error_type=VoucherPostingErrorType.NETWORK_ERROR,
                error_message=response.error_message,
                raw_response=response.data,
                response_time=response.response_time
            )
            logger.error(f"Network error during voucher posting: {response.error_message}")
            self.voucher_posted.emit(result)
            return result
        
        # Step 3: Processing response (70%)
        progress.stage = "Processing"
        progress.progress_percent = 70
        progress.current_step = "Processing TallyPrime response"
        progress.current_step_number = 3
        progress.elapsed_time = time.time() - start_time
        self.posting_progress.emit(progress)
        
        # Parse TallyPrime response for posting results
        result = self._parse_voucher_response(response, description)
        
        # Step 4: Complete (100%)
        progress.stage = "Complete" if result.success else "Error"
        progress.progress_percent = 100
        progress.current_step = result.user_friendly_message
        progress.current_step_number = 4
        progress.elapsed_time = time.time() - start_time
        self.posting_progress.emit(progress)
        
        # Emit completion signal
        self.voucher_posted.emit(result)
        return result
    
    def _wrap_voucher_for_import(self, voucher_xml: str) -> str:
        """
        Wrap voucher XML in TallyPrime import envelope
        
        Args:
            voucher_xml: Raw voucher XML content
            
        Returns:
            Complete import XML with proper envelope structure
        """
        return f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Import</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>Vouchers</ID>
  </HEADER>
  <BODY>
    <DESC/>
    <DATA>
      <TALLYMESSAGE>
{voucher_xml}
      </TALLYMESSAGE>
    </DATA>
  </BODY>
</ENVELOPE>"""
    
    def _parse_voucher_response(self, response: 'TallyResponse', description: str) -> 'VoucherPostingResult':
        """
        Parse TallyPrime voucher posting response
        
        Args:
            response: TallyResponse from posting request
            description: Operation description for logging
            
        Returns:
            VoucherPostingResult with parsed results
        """
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.data)
            
            # Extract response data
            created = int(self._get_xml_text(root, 'CREATED', '0'))
            altered = int(self._get_xml_text(root, 'ALTERED', '0'))
            deleted = int(self._get_xml_text(root, 'DELETED', '0'))
            ignored = int(self._get_xml_text(root, 'IGNORED', '0'))
            errors = int(self._get_xml_text(root, 'ERRORS', '0'))
            cancelled = int(self._get_xml_text(root, 'CANCELLED', '0'))
            
            # Get voucher ID if successful
            voucher_id = self._get_xml_text(root, 'LASTVCHID', '')
            
            # Extract error messages
            error_messages = [elem.text for elem in root.findall('.//LINEERROR') if elem.text]
            
            # Determine success/failure
            is_success = errors == 0 and (created > 0 or altered > 0)
            
            if is_success:
                result = VoucherPostingResult(
                    success=True,
                    voucher_id=voucher_id,
                    created_count=created,
                    altered_count=altered,
                    deleted_count=deleted,
                    raw_response=response.data,
                    response_time=response.response_time
                )
                logger.info(f"Voucher posted successfully - ID: {voucher_id}, Created: {created}, Altered: {altered}")
                return result
            else:
                # Classify the error
                error_type = self._classify_posting_error(error_messages)
                primary_error = error_messages[0] if error_messages else "Unknown error occurred"
                
                result = VoucherPostingResult(
                    success=False,
                    error_type=error_type,
                    error_message=primary_error,
                    error_details=error_messages,
                    ignored_count=ignored,
                    cancelled_count=cancelled,
                    raw_response=response.data,
                    response_time=response.response_time
                )
                logger.error(f"Voucher posting failed - {error_type.value}: {primary_error}")
                return result
                
        except ET.ParseError as e:
            result = VoucherPostingResult(
                success=False,
                error_type=VoucherPostingErrorType.XML_PARSE_ERROR,
                error_message=f"Could not parse TallyPrime response: {str(e)}",
                raw_response=response.data,
                response_time=response.response_time
            )
            logger.error(f"XML parsing error in voucher response: {str(e)}")
            return result
        except Exception as e:
            result = VoucherPostingResult(
                success=False,
                error_type=VoucherPostingErrorType.UNKNOWN_ERROR,
                error_message=f"Unexpected error processing response: {str(e)}",
                raw_response=response.data,
                response_time=response.response_time
            )
            logger.error(f"Unexpected error parsing voucher response: {str(e)}")
            return result
    
    def _get_xml_text(self, root, tag_name: str, default: str = "") -> str:
        """Helper method to safely extract text from XML element"""
        elem = root.find(f'.//{tag_name}')
        return elem.text.strip() if elem is not None and elem.text else default
    
    def _classify_posting_error(self, error_messages: List[str]) -> 'VoucherPostingErrorType':
        """
        Classify posting errors based on TallyPrime error messages
        
        Args:
            error_messages: List of error messages from TallyPrime
            
        Returns:
            Classified error type for appropriate handling
        """
        if not error_messages:
            return VoucherPostingErrorType.UNKNOWN_ERROR
        
        # Combine all error messages for analysis
        combined_errors = ' '.join(error_messages).lower()
        
        # Classification based on common TallyPrime error patterns
        if 'could not find ledger' in combined_errors:
            return VoucherPostingErrorType.MISSING_LEDGER
        elif 'voucher type does not exist' in combined_errors:
            return VoucherPostingErrorType.INVALID_VOUCHER_TYPE
        elif 'voucher totals do not match' in combined_errors or 'balance' in combined_errors:
            return VoucherPostingErrorType.UNBALANCED_ENTRY
        elif 'unknown request' in combined_errors or 'xml' in combined_errors:
            return VoucherPostingErrorType.MALFORMED_XML
        elif 'duplicate' in combined_errors or 'already exists' in combined_errors:
            return VoucherPostingErrorType.DUPLICATE_VOUCHER
        elif 'permission' in combined_errors or 'access' in combined_errors:
            return VoucherPostingErrorType.ACCESS_DENIED
        elif 'company' in combined_errors:
            return VoucherPostingErrorType.COMPANY_ERROR
        else:
            return VoucherPostingErrorType.BUSINESS_RULE_VIOLATION
    
    def validate_voucher_before_posting(self, voucher_xml: str) -> 'VoucherValidationResult':
        """
        Validate voucher XML before posting to catch issues early
        
        This method performs local validation to catch common issues before
        sending to TallyPrime, improving user experience and reducing errors.
        
        Args:
            voucher_xml: Voucher XML to validate
            
        Returns:
            VoucherValidationResult with validation status and issues
        """
        validation_issues = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(voucher_xml)
            
            # Check basic voucher structure
            voucher_elem = root.find('.//VOUCHER')
            if voucher_elem is None:
                validation_issues.append("No VOUCHER element found in XML")
                return VoucherValidationResult(
                    is_valid=False,
                    issues=validation_issues,
                    error_message="Invalid voucher XML structure"
                )
            
            # Validate voucher type
            vch_type = voucher_elem.get('VCHTYPE', '')
            if not vch_type:
                validation_issues.append("VCHTYPE attribute is missing")
            
            # Validate voucher number
            vch_number = self._get_xml_text(root, 'VOUCHERNUMBER')
            if not vch_number:
                validation_issues.append("VOUCHERNUMBER is missing")
            
            # Validate date
            date_elem = self._get_xml_text(root, 'DATE')
            if not date_elem:
                validation_issues.append("DATE is missing")
            
            # Validate ledger entries
            entries = root.findall('.//ALLLEDGERENTRIES.LIST')
            if len(entries) < 2:
                validation_issues.append("At least two ledger entries are required")
            
            # Validate balance
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')
            
            for entry in entries:
                ledger_name = self._get_xml_text(entry, 'LEDGERNAME')
                if not ledger_name:
                    validation_issues.append("Ledger name is missing in an entry")
                    continue
                
                amount_text = self._get_xml_text(entry, 'AMOUNT')
                is_deemed_positive = self._get_xml_text(entry, 'ISDEEMEDPOSITIVE')
                
                try:
                    amount = abs(Decimal(amount_text))
                    if is_deemed_positive.lower() == 'yes':
                        total_debit += amount
                    else:
                        total_credit += amount
                except (ValueError, InvalidOperation):
                    validation_issues.append(f"Invalid amount for ledger '{ledger_name}': {amount_text}")
            
            # Check balance
            difference = abs(total_debit - total_credit)
            if difference >= Decimal('0.01'):
                validation_issues.append(f"Voucher is not balanced - Debit: {total_debit}, Credit: {total_credit}")
            
            # Validate against cached ledger names if available
            if self.ledger_names:
                for entry in entries:
                    ledger_name = self._get_xml_text(entry, 'LEDGERNAME')
                    if ledger_name and ledger_name not in self.ledger_names:
                        validation_issues.append(f"Ledger '{ledger_name}' may not exist in TallyPrime")
            
        except ET.ParseError as e:
            validation_issues.append(f"XML parsing error: {str(e)}")
        except Exception as e:
            validation_issues.append(f"Validation error: {str(e)}")
        
        is_valid = len(validation_issues) == 0
        return VoucherValidationResult(
            is_valid=is_valid,
            issues=validation_issues,
            error_message=None if is_valid else "Voucher validation failed"
        )
    
    def post_voucher_with_validation(self, voucher_xml: str, description: str = "Voucher Posting") -> 'VoucherPostingResult':
        """
        Post voucher with pre-validation for enhanced error handling
        
        This is a convenience method that combines validation and posting
        for a complete workflow with better user feedback.
        
        Args:
            voucher_xml: Voucher XML to post
            description: Description for logging
            
        Returns:
            VoucherPostingResult with validation and posting results
        """
        # First validate the voucher
        validation = self.validate_voucher_before_posting(voucher_xml)
        
        if not validation.is_valid:
            # Return validation failure as posting result
            return VoucherPostingResult(
                success=False,
                error_type=VoucherPostingErrorType.VALIDATION_ERROR,
                error_message="Pre-validation failed",
                error_details=validation.issues,
                validation_result=validation
            )
        
        # Proceed with posting
        return self.post_voucher(voucher_xml, description)
    
    def get_posting_suggestion(self, error_type: 'VoucherPostingErrorType', error_message: str = "") -> str:
        """
        Get user-friendly suggestion for resolving posting errors
        
        Args:
            error_type: Type of posting error
            error_message: Original error message from TallyPrime
            
        Returns:
            Human-readable suggestion for resolving the error
        """
        suggestions = {
            VoucherPostingErrorType.MISSING_LEDGER: 
                "Create the missing ledger in TallyPrime or check the spelling/case of ledger names.",
            VoucherPostingErrorType.INVALID_VOUCHER_TYPE:
                "Use a valid voucher type that exists in your TallyPrime configuration.",
            VoucherPostingErrorType.UNBALANCED_ENTRY:
                "Ensure that total debit amounts equal total credit amounts.",
            VoucherPostingErrorType.MALFORMED_XML:
                "Check the XML structure and ensure it matches TallyPrime's expected format.",
            VoucherPostingErrorType.DUPLICATE_VOUCHER:
                "Use a unique voucher number or check if this voucher already exists.",
            VoucherPostingErrorType.ACCESS_DENIED:
                "Check TallyPrime permissions and ensure the company is not locked.",
            VoucherPostingErrorType.COMPANY_ERROR:
                "Verify the company is open and accessible in TallyPrime.",
            VoucherPostingErrorType.NETWORK_ERROR:
                "Check TallyPrime connection, ensure HTTP-XML gateway is enabled.",
            VoucherPostingErrorType.VALIDATION_ERROR:
                "Review voucher details and fix validation issues before posting.",
            VoucherPostingErrorType.BUSINESS_RULE_VIOLATION:
                "Check TallyPrime business rules and configuration settings."
        }
        
        return suggestions.get(error_type, "Review the error message and check TallyPrime configuration.")

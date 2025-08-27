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
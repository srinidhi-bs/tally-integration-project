#!/usr/bin/env python3
"""
TallyPrime Data Reader - Professional Data Extraction Framework

This module provides comprehensive data reading capabilities from TallyPrime HTTP-XML Gateway.
It handles XML request templates, response parsing, and data structuring for GUI display.

Key Features:
- XML request template management for different TallyPrime operations
- Robust XML response parsing with comprehensive error handling
- Data extraction for companies, ledgers, transactions, and reports
- Integration with existing TallyConnector framework
- Professional error handling and logging

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, date
import logging
from enum import Enum
import time
import hashlib
import json
import threading
from collections import OrderedDict
import re

# Qt6 imports for signal-based communication
from PySide6.QtCore import QObject, Signal

# Import our existing TallyConnector framework
from .connector import TallyConnector, TallyResponse, ConnectionStatus

# Set up logger for this module
logger = logging.getLogger(__name__)


class TallyXMLError(Exception):
    """
    Custom exception for XML-related errors in TallyPrime data processing
    
    This exception provides detailed information about XML parsing failures,
    malformed responses, and validation errors to help with debugging.
    """
    
    def __init__(self, message: str, error_type: str = "GENERIC", xml_content: str = None, original_error: Exception = None):
        """
        Initialize TallyXMLError with detailed error information
        
        Args:
            message: Human-readable error description
            error_type: Type of XML error (PARSE_ERROR, VALIDATION_ERROR, MALFORMED_CONTENT, etc.)
            xml_content: The problematic XML content (first 1000 chars for logging)
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.error_type = error_type
        self.xml_content = xml_content[:1000] if xml_content else None
        self.original_error = original_error
        self.timestamp = datetime.now()
    
    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get comprehensive debug information for troubleshooting
        
        Returns:
            Dictionary with error details, XML snippet, and diagnostic info
        """
        return {
            'error_type': self.error_type,
            'message': str(self),
            'timestamp': self.timestamp.isoformat(),
            'original_error': str(self.original_error) if self.original_error else None,
            'xml_snippet': self.xml_content,
            'xml_length': len(self.xml_content) if self.xml_content else 0
        }


class TallyDataType(Enum):
    """
    Enumeration of different data types that can be requested from TallyPrime
    Used to organize and categorize different XML request templates
    """
    COMPANY_INFO = "company_info"
    LEDGER_LIST = "ledger_list"
    LEDGER_DETAILS = "ledger_details"
    VOUCHER_LIST = "voucher_list"
    VOUCHER_DETAILS = "voucher_details"
    BALANCE_SHEET = "balance_sheet"
    PROFIT_LOSS = "profit_loss"
    DAY_BOOK = "day_book"
    STOCK_SUMMARY = "stock_summary"


@dataclass
class CacheEntry:
    """
    Data class representing a cached data entry
    Stores data, metadata, and expiration information for efficient caching
    """
    data: Any
    timestamp: datetime
    access_count: int
    expiry_seconds: int
    data_type: 'TallyDataType'
    cache_key: str
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return (datetime.now() - self.timestamp).total_seconds() > self.expiry_seconds
    
    def is_fresh(self, max_age_seconds: int = None) -> bool:
        """Check if cache entry is fresh enough for use"""
        age_seconds = (datetime.now() - self.timestamp).total_seconds()
        max_age = max_age_seconds or self.expiry_seconds
        return age_seconds <= max_age
    
    def update_access(self):
        """Update access statistics for cache management"""
        self.access_count += 1


class TallyDataCache:
    """
    Professional caching system for TallyPrime data with intelligent cache management
    
    Features:
    - LRU (Least Recently Used) cache eviction
    - Configurable expiry times per data type
    - Thread-safe operations for concurrent access
    - Memory usage monitoring and cleanup
    - Cache hit/miss statistics for performance analysis
    """
    
    def __init__(self, max_size: int = 100, default_expiry_seconds: int = 300):
        """
        Initialize the data cache system
        
        Args:
            max_size: Maximum number of entries in cache
            default_expiry_seconds: Default expiry time for cache entries (5 minutes)
        """
        self.max_size = max_size
        self.default_expiry_seconds = default_expiry_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Data type specific expiry settings (in seconds)
        self.expiry_settings = {
            'COMPANY_INFO': 600,      # 10 minutes - company info changes rarely
            'LEDGER_LIST': 300,       # 5 minutes - ledgers change occasionally
            'LEDGER_DETAILS': 180,    # 3 minutes - ledger details may change
            'BALANCE_SHEET': 60,      # 1 minute - financial reports change frequently
            'VOUCHER_LIST': 30,       # 30 seconds - vouchers change very frequently
            'VOUCHER_DETAILS': 60,    # 1 minute - voucher details are mostly static
            'DAY_BOOK': 30,          # 30 seconds - day book changes frequently
        }
        
        logger.info(f"Initialized TallyDataCache with max_size={max_size}, default_expiry={default_expiry_seconds}s")
    
    def _generate_cache_key(self, data_type: 'TallyDataType', **kwargs) -> str:
        """
        Generate a unique cache key for the data request
        
        Args:
            data_type: Type of data being cached
            **kwargs: Additional parameters that affect the data
            
        Returns:
            Unique cache key string
        """
        # Create a string representation of all parameters
        key_parts = [data_type.value]
        
        # Add sorted parameters for consistent key generation
        if kwargs:
            param_items = sorted(kwargs.items())
            param_str = '&'.join([f"{k}={v}" for k, v in param_items])
            key_parts.append(param_str)
        
        key_string = '|'.join(key_parts)
        
        # Generate MD5 hash for consistent key length
        cache_key = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        logger.debug(f"Generated cache key: {cache_key} for {key_string}")
        return cache_key
    
    def get(self, data_type: 'TallyDataType', **kwargs) -> Optional[Any]:
        """
        Retrieve data from cache if available and fresh
        
        Args:
            data_type: Type of data to retrieve
            **kwargs: Parameters that were used for the original request
            
        Returns:
            Cached data if available and fresh, None otherwise
        """
        with self._lock:
            cache_key = self._generate_cache_key(data_type, **kwargs)
            
            if cache_key not in self._cache:
                self.misses += 1
                logger.debug(f"Cache miss for {data_type.value}: {cache_key}")
                return None
            
            entry = self._cache[cache_key]
            
            # Check if entry has expired
            if entry.is_expired():
                logger.debug(f"Cache entry expired for {data_type.value}: {cache_key}")
                del self._cache[cache_key]
                self.misses += 1
                return None
            
            # Move to end (most recently used) and update access stats
            self._cache.move_to_end(cache_key)
            entry.update_access()
            self.hits += 1
            
            logger.debug(f"Cache hit for {data_type.value}: {cache_key} (age: {(datetime.now() - entry.timestamp).total_seconds():.1f}s)")
            return entry.data
    
    def put(self, data_type: 'TallyDataType', data: Any, **kwargs) -> None:
        """
        Store data in cache with automatic expiry and LRU management
        
        Args:
            data_type: Type of data being cached
            data: Data to cache
            **kwargs: Parameters that were used for the original request
        """
        with self._lock:
            cache_key = self._generate_cache_key(data_type, **kwargs)
            
            # Get expiry time for this data type
            expiry_seconds = self.expiry_settings.get(
                data_type.value, 
                self.default_expiry_seconds
            )
            
            # Create cache entry
            entry = CacheEntry(
                data=data,
                timestamp=datetime.now(),
                access_count=1,
                expiry_seconds=expiry_seconds,
                data_type=data_type,
                cache_key=cache_key
            )
            
            # Add to cache (overwrites existing entry)
            self._cache[cache_key] = entry
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            
            # Check if we need to evict old entries
            while len(self._cache) > self.max_size:
                # Remove least recently used entry (first item)
                oldest_key, oldest_entry = self._cache.popitem(last=False)
                self.evictions += 1
                logger.debug(f"Evicted cache entry: {oldest_entry.data_type.value} {oldest_key}")
            
            logger.debug(f"Cached {data_type.value}: {cache_key} (expires in {expiry_seconds}s)")
    
    def clear(self) -> None:
        """
        Clear all cache entries
        """
        with self._lock:
            cache_size = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared cache: {cache_size} entries removed")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics
        
        Returns:
            Dictionary with cache performance metrics
        """
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate memory usage estimation
            memory_usage_mb = len(self._cache) * 0.1  # Rough estimate: 100KB per entry
            
            return {
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate_percent': round(hit_rate, 2),
                'estimated_memory_mb': round(memory_usage_mb, 2),
                'expiry_settings': self.expiry_settings.copy()
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache
        
        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)


@dataclass
class TallyDataRequest:
    """
    Data class representing a structured data request to TallyPrime
    Encapsulates request type, parameters, and metadata
    """
    data_type: TallyDataType
    xml_template: str
    parameters: Dict[str, Any]
    description: str
    expected_root: str  # Expected XML root element for validation


class TallyDataReader(QObject):
    """
    Professional Data Reader for TallyPrime HTTP-XML Gateway
    
    This class provides high-level data extraction methods built on top of
    the TallyConnector framework. It handles XML request generation, response
    parsing, and data structuring for GUI consumption.
    
    Features:
    - Template-based XML request generation
    - Comprehensive XML response parsing
    - Data validation and error handling
    - Qt signal-slot integration for GUI updates
    - Professional logging and debugging support
    
    Usage Example:
        # Initialize with existing TallyConnector
        connector = TallyConnector(config)
        reader = TallyDataReader(connector)
        
        # Read company information
        company_data = await reader.get_company_info()
        
        # Read ledger list
        ledgers = await reader.get_ledger_list()
    """
    
    # Qt signals for GUI communication
    data_read_started = Signal(str)  # Signal when data reading starts (operation name)
    data_read_progress = Signal(int, str)  # Signal for progress updates (percentage, status)
    data_read_completed = Signal(str, bool)  # Signal when data reading completes (operation, success)
    data_read_error = Signal(str, str)  # Signal for errors (operation, error_message)
    
    def __init__(self, tally_connector: TallyConnector, enable_cache: bool = True, cache_size: int = 100):
        """
        Initialize the TallyDataReader with an existing TallyConnector
        
        Args:
            tally_connector: Configured TallyConnector instance for HTTP-XML communication
            enable_cache: Whether to enable data caching for performance
            cache_size: Maximum number of entries in cache (default: 100)
        """
        super().__init__()
        
        # Store reference to the TallyConnector
        self.connector = tally_connector
        
        # Initialize data cache if enabled
        self.cache_enabled = enable_cache
        if self.cache_enabled:
            self.cache = TallyDataCache(max_size=cache_size)
            logger.info(f"Data caching enabled with size limit: {cache_size}")
        else:
            self.cache = None
            logger.info("Data caching disabled")
        
        # Initialize XML request templates
        self.xml_templates = self._initialize_xml_templates()
        
        # Statistics and monitoring
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.xml_parse_errors = 0
        self.validation_errors = 0
        self.malformed_responses = 0
        
        # Error tracking for diagnostics
        self.recent_errors: List[TallyXMLError] = []
        self.max_recent_errors = 10
        
        # Connect to connector signals for monitoring
        if hasattr(self.connector, 'connection_status_changed'):
            self.connector.connection_status_changed.connect(self._on_connection_status_changed)
        
        logger.info("TallyDataReader initialized successfully with enhanced error handling and caching")
    
    
    def _initialize_xml_templates(self) -> Dict[TallyDataType, TallyDataRequest]:
        """
        Initialize XML request templates for different TallyPrime operations
        
        This method creates a comprehensive library of XML request templates
        that can be used to query different types of data from TallyPrime.
        Each template is carefully crafted to match TallyPrime's XML-RPC format.
        
        Returns:
            Dictionary mapping data types to their corresponding request templates
        """
        templates = {}
        
        # Company Information Request Template
        # This template retrieves basic company details, financial year, and configuration
        templates[TallyDataType.COMPANY_INFO] = TallyDataRequest(
            data_type=TallyDataType.COMPANY_INFO,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>Company Info</REPORTNAME>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={},
            description="Retrieve company information including name, address, and financial year",
            expected_root="ENVELOPE"
        )
        
        # Ledger List Request Template
        # This template retrieves all ledgers with basic information
        templates[TallyDataType.LEDGER_LIST] = TallyDataRequest(
            data_type=TallyDataType.LEDGER_LIST,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>List of Accounts</REPORTNAME>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={},
            description="Retrieve complete list of ledger accounts with basic details",
            expected_root="ENVELOPE"
        )
        
        # Ledger Details Request Template (with parameter support)
        # This template retrieves detailed information for a specific ledger
        templates[TallyDataType.LEDGER_DETAILS] = TallyDataRequest(
            data_type=TallyDataType.LEDGER_DETAILS,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>Ledger</REPORTNAME>
                            <STATICVARIABLES>
                                <LEDGERNAME>{ledger_name}</LEDGERNAME>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={"ledger_name": ""},
            description="Retrieve detailed information for a specific ledger account",
            expected_root="ENVELOPE"
        )
        
        # Balance Sheet Request Template
        # This template retrieves the balance sheet report
        templates[TallyDataType.BALANCE_SHEET] = TallyDataRequest(
            data_type=TallyDataType.BALANCE_SHEET,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>Balance Sheet</REPORTNAME>
                            <STATICVARIABLES>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={},
            description="Retrieve balance sheet report with assets and liabilities",
            expected_root="ENVELOPE"
        )
        
        # Day Book Request Template (with date parameters)
        # This template retrieves day book entries for a specific date range
        templates[TallyDataType.DAY_BOOK] = TallyDataRequest(
            data_type=TallyDataType.DAY_BOOK,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>Day Book</REPORTNAME>
                            <STATICVARIABLES>
                                <SVFROMDATE>{from_date}</SVFROMDATE>
                                <SVTODATE>{to_date}</SVTODATE>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={"from_date": "", "to_date": ""},
            description="Retrieve day book entries for specified date range",
            expected_root="ENVELOPE"
        )
        
        # Voucher List Request Template (with date parameters)
        # This template retrieves voucher list for a specific date range
        templates[TallyDataType.VOUCHER_LIST] = TallyDataRequest(
            data_type=TallyDataType.VOUCHER_LIST,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>All Vouchers</REPORTNAME>
                            <STATICVARIABLES>
                                <SVFROMDATE>{from_date}</SVFROMDATE>
                                <SVTODATE>{to_date}</SVTODATE>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={"from_date": "", "to_date": ""},
            description="Retrieve voucher list for specified date range",
            expected_root="ENVELOPE"
        )
        
        # Voucher Details Request Template (for specific voucher)
        # This template retrieves detailed information for a specific voucher
        templates[TallyDataType.VOUCHER_DETAILS] = TallyDataRequest(
            data_type=TallyDataType.VOUCHER_DETAILS,
            xml_template="""
            <ENVELOPE>
                <HEADER>
                    <TALLYREQUEST>Export Data</TALLYREQUEST>
                </HEADER>
                <BODY>
                    <EXPORTDATA>
                        <REQUESTDESC>
                            <REPORTNAME>Voucher Register</REPORTNAME>
                            <STATICVARIABLES>
                                <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
                                <VOUCHERTYPE>{voucher_type}</VOUCHERTYPE>
                                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            </STATICVARIABLES>
                        </REQUESTDESC>
                    </EXPORTDATA>
                </BODY>
            </ENVELOPE>
            """.strip(),
            parameters={"voucher_number": "", "voucher_type": ""},
            description="Retrieve detailed information for a specific voucher",
            expected_root="ENVELOPE"
        )
        
        logger.info(f"Initialized {len(templates)} XML request templates")
        return templates
    
    
    def _format_xml_template(self, data_type: TallyDataType, **kwargs) -> str:
        """
        Format XML template with provided parameters
        
        This method takes a template and replaces placeholders with actual values.
        It provides parameter validation and formatting for different data types.
        
        Args:
            data_type: Type of data being requested
            **kwargs: Parameters to substitute in the template
            
        Returns:
            Formatted XML request string
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if data_type not in self.xml_templates:
            raise ValueError(f"Unknown data type: {data_type}")
        
        template_request = self.xml_templates[data_type]
        xml_template = template_request.xml_template
        
        # Validate required parameters
        required_params = template_request.parameters.keys()
        for param in required_params:
            if param not in kwargs and template_request.parameters[param] == "":
                logger.warning(f"Missing required parameter '{param}' for {data_type}")
        
        try:
            # Format the template with provided parameters
            formatted_xml = xml_template.format(**kwargs)
            logger.debug(f"Formatted XML template for {data_type.value}")
            return formatted_xml
            
        except KeyError as e:
            error_msg = f"Missing template parameter: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error formatting XML template: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    
    async def _send_data_request(self, data_type: TallyDataType, use_cache: bool = True, **kwargs) -> TallyResponse:
        """
        Send a data request to TallyPrime with caching and enhanced error handling
        
        This is the core method that handles HTTP-XML communication with intelligent
        caching, comprehensive error handling, and performance monitoring.
        
        Args:
            data_type: Type of data being requested
            use_cache: Whether to use cached data if available (default: True)
            **kwargs: Parameters for the XML template
            
        Returns:
            TallyResponse object containing the result
        """
        # Update statistics
        self.request_count += 1
        start_time = time.time()
        
        # Emit signal that data reading has started
        operation_name = data_type.value.replace('_', ' ').title()
        self.data_read_started.emit(operation_name)
        
        try:
            # Check cache first if caching is enabled
            if self.cache_enabled and use_cache:
                cached_data = self.cache.get(data_type, **kwargs)
                if cached_data is not None:
                    logger.info(f"Cache hit for {data_type.value} - returning cached data")
                    
                    # Create successful response from cached data
                    response = TallyResponse(
                        success=True,
                        data=cached_data,
                        status_code=200,
                        response_time=time.time() - start_time,
                        from_cache=True
                    )
                    
                    # Emit completion signals
                    self.data_read_progress.emit(100, "Data retrieved from cache")
                    self.data_read_completed.emit(operation_name, True)
                    
                    return response
            
            # Format XML request
            self.data_read_progress.emit(10, "Preparing XML request...")
            xml_request = self._format_xml_template(data_type, **kwargs)
            
            # Send request via TallyConnector
            self.data_read_progress.emit(25, "Sending request to TallyPrime...")
            response = await self.connector.send_request(xml_request)
            
            self.data_read_progress.emit(60, "Processing response...")
            
            # Enhanced response validation and processing
            if response.success:
                try:
                    # Validate XML response with comprehensive error handling
                    self._validate_xml_response(response.data, data_type)
                    
                    # Cache the successful response if caching is enabled
                    if self.cache_enabled:
                        self.cache.put(data_type, response.data, **kwargs)
                        logger.debug(f"Cached response for {data_type.value}")
                    
                    # Update success statistics
                    self.successful_requests += 1
                    self.total_response_time += response.response_time
                    
                    # Emit completion signal
                    self.data_read_progress.emit(100, "Data reading completed successfully")
                    self.data_read_completed.emit(operation_name, True)
                    
                    logger.info(f"Successfully retrieved {data_type.value} data (response time: {response.response_time:.3f}s)")
                    return response
                    
                except TallyXMLError as xml_error:
                    # Handle XML validation errors with detailed information
                    self.xml_parse_errors += 1 if xml_error.error_type == "PARSE_ERROR" else 0
                    self.malformed_responses += 1
                    
                    error_msg = f"XML validation failed for {data_type.value}: {str(xml_error)}"
                    logger.error(error_msg)
                    logger.debug(f"XML error details: {xml_error.get_debug_info()}")
                    
                    # Emit error signal with detailed information
                    self.data_read_error.emit(operation_name, f"{xml_error.error_type}: {str(xml_error)}")
                    
                    # Return error response with diagnostic information
                    return TallyResponse(
                        success=False,
                        data="",
                        status_code=response.status_code,
                        error_message=error_msg,
                        response_time=response.response_time,
                        error_details=xml_error.get_debug_info()
                    )
                    
            else:
                # Handle failed HTTP request
                self.failed_requests += 1
                error_msg = response.error_message or f"Failed to retrieve {data_type.value} data"
                logger.error(f"Data request failed: {error_msg} (status: {response.status_code})")
                
                # Emit error signal
                self.data_read_error.emit(operation_name, error_msg)
                return response
                
        except Exception as e:
            # Handle unexpected errors with comprehensive logging
            self.failed_requests += 1
            error_msg = f"Unexpected error during {data_type.value} request: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Track error for diagnostics
            xml_error = TallyXMLError(
                error_msg,
                "UNEXPECTED_ERROR",
                None,
                e
            )
            self._track_error(xml_error)
            
            # Emit error signal
            self.data_read_error.emit(operation_name, error_msg)
            
            return TallyResponse(
                success=False,
                data="",
                status_code=0,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
    
    
    def _validate_xml_response(self, xml_data: str, data_type: TallyDataType) -> bool:
        """
        Enhanced XML response validation with comprehensive malformed content detection
        
        This method performs thorough validation to ensure the XML response
        has the expected structure, contains valid data, and is not malformed.
        It includes detection of various types of malformed XML that TallyPrime might return.
        
        Args:
            xml_data: Raw XML response string
            data_type: Expected data type for validation
            
        Returns:
            True if XML is valid and well-formed, False otherwise
            
        Raises:
            TallyXMLError: For detailed error reporting with diagnostic information
        """
        try:
            # Step 1: Basic content validation
            if not xml_data or not xml_data.strip():
                error = TallyXMLError(
                    "Empty or null XML response received from TallyPrime",
                    "EMPTY_RESPONSE",
                    xml_data
                )
                self._track_error(error)
                raise error
            
            # Step 2: Check minimum response size
            if len(xml_data.strip()) < 50:
                error = TallyXMLError(
                    f"XML response too short ({len(xml_data)} chars) - likely incomplete or malformed",
                    "INSUFFICIENT_CONTENT",
                    xml_data
                )
                self._track_error(error)
                raise error
            
            # Step 3: Pre-parsing content validation
            self._validate_xml_content_structure(xml_data)
            
            # Step 4: Parse XML to check if it's well-formed
            try:
                root = ET.fromstring(xml_data)
            except ET.ParseError as e:
                error = TallyXMLError(
                    f"XML parsing failed - malformed XML structure: {str(e)}",
                    "PARSE_ERROR",
                    xml_data,
                    e
                )
                self._track_error(error)
                raise error
            
            # Step 5: Validate XML structure and content
            self._validate_parsed_xml_structure(root, data_type, xml_data)
            
            # Step 6: Check for TallyPrime error responses
            self._check_tally_error_responses(root)
            
            # Step 7: Validate data content based on request type
            self._validate_data_type_specific_content(root, data_type)
            
            logger.debug(f"XML response validation successful for {data_type.value}")
            return True
            
        except TallyXMLError:
            # Re-raise TallyXMLError as-is
            self.validation_errors += 1
            raise
        except Exception as e:
            # Wrap unexpected errors in TallyXMLError
            error = TallyXMLError(
                f"Unexpected XML validation error: {str(e)}",
                "VALIDATION_ERROR",
                xml_data,
                e
            )
            self._track_error(error)
            self.validation_errors += 1
            raise error
    
    def _validate_xml_content_structure(self, xml_data: str) -> None:
        """
        Validate XML content structure before parsing
        
        Args:
            xml_data: Raw XML string to validate
            
        Raises:
            TallyXMLError: If content structure is invalid
        """
        # Check for common malformed patterns
        xml_lower = xml_data.lower().strip()
        
        # Check for HTML error pages disguised as XML
        if xml_lower.startswith('<!doctype html') or '<html' in xml_lower[:200]:
            raise TallyXMLError(
                "Received HTML response instead of XML - TallyPrime may be returning error page",
                "HTML_RESPONSE",
                xml_data
            )
        
        # Check for JSON responses
        if xml_data.strip().startswith(('{', '[')):
            raise TallyXMLError(
                "Received JSON response instead of XML",
                "JSON_RESPONSE",
                xml_data
            )
        
        # Check for plain text error messages
        if not xml_data.strip().startswith('<'):
            raise TallyXMLError(
                "Response does not appear to be valid XML - missing opening tag",
                "NON_XML_RESPONSE",
                xml_data
            )
        
        # Check for truncated XML (incomplete responses)
        if xml_data.count('<') != xml_data.count('>'):
            raise TallyXMLError(
                "XML appears truncated - unbalanced angle brackets",
                "TRUNCATED_XML",
                xml_data
            )
        
        # Check for encoding issues
        if '\x00' in xml_data or '\ufffd' in xml_data:
            raise TallyXMLError(
                "XML contains null bytes or encoding errors",
                "ENCODING_ERROR",
                xml_data
            )
    
    def _validate_parsed_xml_structure(self, root: ET.Element, data_type: TallyDataType, xml_data: str) -> None:
        """
        Validate the parsed XML structure
        
        Args:
            root: Parsed XML root element
            data_type: Expected data type
            xml_data: Original XML string for error reporting
            
        Raises:
            TallyXMLError: If structure is invalid
        """
        # Check if root element exists
        if root is None:
            raise TallyXMLError(
                "XML parsing resulted in None root element",
                "NULL_ROOT",
                xml_data
            )
        
        # Validate root element name (flexible check)
        expected_root = self.xml_templates[data_type].expected_root
        if root.tag != expected_root and root.tag not in ['ENVELOPE', 'RESPONSE', 'TALLYMESSAGE']:
            # Log warning but don't fail - TallyPrime has variations
            logger.warning(f"Unexpected root element: {root.tag}, expected: {expected_root}")
        
        # Check for completely empty XML structure
        if len(list(root)) == 0 and not root.text and not root.attrib:
            raise TallyXMLError(
                f"XML structure is empty - root element '{root.tag}' has no content",
                "EMPTY_STRUCTURE",
                xml_data
            )
    
    def _check_tally_error_responses(self, root: ET.Element) -> None:
        """
        Check for TallyPrime error responses in XML
        
        Args:
            root: Parsed XML root element
            
        Raises:
            TallyXMLError: If TallyPrime errors are found
        """
        # Check for various error elements that TallyPrime might return
        error_elements = (
            root.findall(".//ERROR") +
            root.findall(".//LINEERROR") +
            root.findall(".//TALLYMESSAGE[@vchtype='Error']") +
            root.findall(".//ERRORMESSAGE") +
            root.findall(".//REQUESTSTATUS[@status='FAILED']")
        )
        
        if error_elements:
            error_messages = []
            for elem in error_elements:
                if elem.text:
                    error_messages.append(elem.text.strip())
                elif elem.attrib:
                    error_messages.append(str(elem.attrib))
                else:
                    error_messages.append(f"Error in {elem.tag} element")
            
            combined_errors = "; ".join(error_messages)
            raise TallyXMLError(
                f"TallyPrime returned errors: {combined_errors}",
                "TALLY_ERROR_RESPONSE"
            )
        
        # Check for connection/authentication errors
        auth_errors = root.findall(".//AUTHENTICATION")
        for auth_elem in auth_errors:
            if auth_elem.text and 'failed' in auth_elem.text.lower():
                raise TallyXMLError(
                    f"TallyPrime authentication failed: {auth_elem.text}",
                    "AUTH_ERROR"
                )
    
    def _validate_data_type_specific_content(self, root: ET.Element, data_type: TallyDataType) -> None:
        """
        Validate XML content specific to the requested data type
        
        Args:
            root: Parsed XML root element
            data_type: Type of data that was requested
            
        Raises:
            TallyXMLError: If content doesn't match expected data type
        """
        # Validate based on data type
        if data_type == TallyDataType.COMPANY_INFO:
            # Should have company information elements
            company_elements = (
                root.findall(".//COMPANY") +
                root.findall(".//TALLYMESSAGE[@vchtype='Company']") +
                root.findall(".//NAME")
            )
            if not company_elements:
                raise TallyXMLError(
                    "Company information request returned no company data elements",
                    "MISSING_COMPANY_DATA"
                )
        
        elif data_type == TallyDataType.LEDGER_LIST:
            # Should have ledger elements
            ledger_elements = (
                root.findall(".//LEDGER") +
                root.findall(".//TALLYMESSAGE[@vchtype='Ledger']") +
                root.findall(".//DSP_NAME")
            )
            if not ledger_elements:
                logger.warning("Ledger list request returned no ledger elements - may be empty company")
        
        elif data_type == TallyDataType.VOUCHER_LIST:
            # Should have voucher elements (might be empty for date ranges with no vouchers)
            voucher_elements = (
                root.findall(".//VOUCHER") +
                root.findall(".//TALLYMESSAGE[@vchtype]")
            )
            if not voucher_elements:
                logger.info("Voucher list request returned no voucher elements - may be empty date range")
    
    def _track_error(self, error: TallyXMLError) -> None:
        """
        Track XML errors for diagnostics and debugging
        
        Args:
            error: TallyXMLError instance to track
        """
        # Add to recent errors list
        self.recent_errors.append(error)
        
        # Keep only recent errors to prevent memory growth
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Log error details for debugging
        logger.error(f"XML Error: {error.error_type} - {str(error)}")
        if error.xml_content:
            logger.debug(f"Problematic XML (first 500 chars): {error.xml_content[:500]}")
    
    def get_recent_errors(self) -> List[Dict[str, Any]]:
        """
        Get recent XML errors for diagnostics
        
        Returns:
            List of error information dictionaries
        """
        return [error.get_debug_info() for error in self.recent_errors]


    def _validate_xml_response_legacy(self, xml_data: str, data_type: TallyDataType) -> bool:
        """
        Validate XML response structure and content
        
        This method performs basic validation to ensure the XML response
        has the expected structure and contains valid data.
        
        Args:
            xml_data: Raw XML response string
            data_type: Expected data type for validation
            
        Returns:
            True if XML is valid, False otherwise
        """
        try:
            # Parse XML to check if it's well-formed
            root = ET.fromstring(xml_data)
            
            # Check if root element matches expected
            expected_root = self.xml_templates[data_type].expected_root
            if root.tag != expected_root:
                logger.warning(f"Unexpected root element: {root.tag}, expected: {expected_root}")
                # Don't fail validation for this - TallyPrime might have variations
            
            # Check for error elements that TallyPrime might return
            error_elements = root.findall(".//ERROR") + root.findall(".//LINEERROR")
            if error_elements:
                error_messages = [elem.text or "Unknown error" for elem in error_elements]
                logger.error(f"TallyPrime returned errors: {', '.join(error_messages)}")
                return False
            
            # Basic content validation - ensure we have some data
            if len(xml_data.strip()) < 50:  # Minimum reasonable XML response size
                logger.warning("XML response seems too short, might be empty")
                return False
            
            logger.debug(f"XML response validation successful for {data_type.value}")
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return False
        except Exception as e:
            logger.error(f"XML validation error: {e}")
            return False
    
    
    def parse_xml_response(self, xml_data: str, raise_on_error: bool = False) -> Optional[ET.Element]:
        """
        Parse XML response into ElementTree with enhanced error handling
        
        This method provides a safe way to parse XML responses with
        comprehensive error handling, malformed content detection, and logging.
        
        Args:
            xml_data: Raw XML response string
            raise_on_error: Whether to raise TallyXMLError on parsing failure
            
        Returns:
            Parsed XML root element, or None if parsing fails
            
        Raises:
            TallyXMLError: If raise_on_error is True and parsing fails
        """
        try:
            # Enhanced content cleaning and validation
            clean_xml = self._clean_xml_content(xml_data)
            
            # Parse XML with comprehensive error detection
            root = ET.fromstring(clean_xml)
            logger.debug(f"Successfully parsed XML response, root: {root.tag}")
            return root
            
        except ET.ParseError as e:
            error_msg = f"XML parsing failed: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Failed XML content (first 500 chars): {xml_data[:500]}")
            
            if raise_on_error:
                raise TallyXMLError(
                    error_msg,
                    "PARSE_ERROR",
                    xml_data,
                    e
                )
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error parsing XML: {str(e)}"
            logger.error(error_msg)
            
            if raise_on_error:
                raise TallyXMLError(
                    error_msg,
                    "UNEXPECTED_PARSE_ERROR",
                    xml_data,
                    e
                )
            return None
    
    def _clean_xml_content(self, xml_data: str) -> str:
        """
        Clean and prepare XML content for parsing
        
        Args:
            xml_data: Raw XML string
            
        Returns:
            Cleaned XML string ready for parsing
            
        Raises:
            TallyXMLError: If content cannot be cleaned or is invalid
        """
        if not xml_data:
            raise TallyXMLError(
                "Empty XML data provided for cleaning",
                "EMPTY_CONTENT"
            )
        
        # Remove BOM (Byte Order Mark) if present
        clean_xml = xml_data.strip()
        if clean_xml.startswith('\ufeff'):
            clean_xml = clean_xml[1:]
            logger.debug("Removed BOM from XML content")
        
        # Remove any leading/trailing whitespace
        clean_xml = clean_xml.strip()
        
        # Check for and handle common encoding issues
        if '\x00' in clean_xml:
            logger.warning("Removing null bytes from XML content")
            clean_xml = clean_xml.replace('\x00', '')
        
        # Handle replacement characters (encoding errors)
        if '\ufffd' in clean_xml:
            logger.warning("XML content contains encoding errors (replacement characters)")
            # Don't automatically remove - let validation catch this
        
        # Basic structure validation
        if not clean_xml.startswith('<'):
            raise TallyXMLError(
                "Cleaned XML does not start with '<' - invalid XML structure",
                "INVALID_XML_START",
                clean_xml
            )
        
        return clean_xml
    
    
    def clear_cache(self) -> None:
        """
        Clear all cached data
        
        This method clears the entire cache and can be used when you need
        fresh data from TallyPrime or when troubleshooting cache-related issues.
        """
        if self.cache_enabled and self.cache:
            self.cache.clear()
            logger.info("Data cache cleared successfully")
        else:
            logger.info("Cache is not enabled - nothing to clear")
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of expired entries removed
        """
        if self.cache_enabled and self.cache:
            return self.cache.cleanup_expired()
        return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics
        
        Returns:
            Dictionary with cache metrics or empty dict if cache disabled
        """
        if self.cache_enabled and self.cache:
            cache_stats = self.cache.get_statistics()
            cache_stats['cache_enabled'] = True
            return cache_stats
        return {'cache_enabled': False}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive data reader statistics and performance metrics
        
        Returns:
            Dictionary containing performance, error, and cache statistics
        """
        avg_response_time = 0.0
        if self.successful_requests > 0:
            avg_response_time = self.total_response_time / self.successful_requests
        
        success_rate = 0.0
        if self.request_count > 0:
            success_rate = (self.successful_requests / self.request_count) * 100
        
        # Get cache statistics if available
        cache_stats = self.get_cache_statistics()
        
        base_stats = {
            'total_requests': self.request_count,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate_percent': round(success_rate, 2),
            'average_response_time_ms': round(avg_response_time * 1000, 2),
            'xml_parse_errors': self.xml_parse_errors,
            'validation_errors': self.validation_errors,
            'malformed_responses': self.malformed_responses,
            'recent_errors_count': len(self.recent_errors),
            'available_templates': len(self.xml_templates),
            'connector_status': self.connector.status.value if hasattr(self.connector, 'status') else "unknown",
            'cache_enabled': self.cache_enabled
        }
        
        # Merge cache statistics
        base_stats.update(cache_stats)
        
        return base_stats
    
    
    def _on_connection_status_changed(self, status: ConnectionStatus):
        """
        Handle connection status changes from TallyConnector
        
        Args:
            status: New connection status
        """
        logger.info(f"TallyConnector status changed to: {status.value}")
        
        # Reset statistics on reconnection
        if status == ConnectionStatus.CONNECTED:
            logger.info("Connection restored - data reader ready for operations")
        elif status == ConnectionStatus.DISCONNECTED:
            logger.warning("Connection lost - data operations will fail until reconnection")
    
    
    # Public convenience methods for common data operations
    
    async def get_company_info(self) -> TallyResponse:
        """
        Retrieve company information from TallyPrime
        
        Returns:
            TallyResponse containing company data or error information
        """
        logger.info("Requesting company information from TallyPrime")
        return await self._send_data_request(TallyDataType.COMPANY_INFO)
    
    
    def parse_company_info(self, xml_data: str):
        """
        Parse company information from TallyPrime XML response
        
        This method extracts company details from the XML response and
        converts them into a structured CompanyInfo object for GUI display.
        
        Args:
            xml_data: Raw XML response containing company information
            
        Returns:
            CompanyInfo object or None if parsing fails
        """
        from ..models.company_model import (
            CompanyInfo, CompanyAddress, FinancialYearInfo, 
            TaxRegistrationInfo, CompanyFeatures, CompanyType,
            FinancialYearType
        )
        
        try:
            # Parse XML response
            root = self.parse_xml_response(xml_data)
            if root is None:
                logger.error("Failed to parse company XML response")
                return None
            
            # Create company info object
            company_info = CompanyInfo()
            
            # Extract company name and basic information
            # TallyPrime company info is typically in BODY/IMPORTDATA/REQUESTDATA/TALLYMESSAGE
            company_data = root.find(".//TALLYMESSAGE[@vchtype='Company']")
            if company_data is None:
                # Alternative path for company data
                company_data = root.find(".//COMPANY")
                if company_data is None:
                    logger.warning("Could not find company data in XML response")
                    # Try to extract from different XML structure
                    company_data = root
            
            # Extract basic company information
            name_elem = company_data.find(".//NAME")
            if name_elem is not None and name_elem.text:
                company_info.name = name_elem.text.strip()
                logger.debug(f"Extracted company name: {company_info.name}")
            
            # Extract company GUID/ID
            guid_elem = company_data.find(".//GUID") or company_data.find(".//REMOTEID")
            if guid_elem is not None and guid_elem.text:
                company_info.guid = guid_elem.text.strip()
            
            # Extract company number
            number_elem = company_data.find(".//COMPANYNUMBER")
            if number_elem is not None and number_elem.text:
                company_info.company_number = number_elem.text.strip()
            
            # Extract alias
            alias_elem = company_data.find(".//ALIAS")
            if alias_elem is not None and alias_elem.text:
                company_info.alias = alias_elem.text.strip()
            
            # Extract address information
            self._parse_company_address(company_data, company_info)
            
            # Extract financial year information
            self._parse_financial_year(company_data, company_info)
            
            # Extract tax registration information
            self._parse_tax_info(company_data, company_info)
            
            # Extract company features and configuration
            self._parse_company_features(company_data, company_info)
            
            # Extract currency information
            self._parse_currency_info(company_data, company_info)
            
            # Extract statistics (if available)
            self._parse_company_statistics(root, company_info)
            
            # Set metadata
            company_info.last_modified = datetime.now()
            
            logger.info(f"Successfully parsed company information for: {company_info.name}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error parsing company information: {e}", exc_info=True)
            return None
    
    
    def _parse_company_address(self, company_data, company_info):
        """
        Parse company address information from XML
        
        Args:
            company_data: XML element containing company data
            company_info: CompanyInfo object to populate
        """
        try:
            # Mailing address
            address_lines = []
            for i in range(1, 6):  # TallyPrime typically has ADDRESS1 to ADDRESS5
                addr_elem = company_data.find(f".//ADDRESS{i}")
                if addr_elem is not None and addr_elem.text:
                    address_lines.append(addr_elem.text.strip())
            
            if address_lines:
                company_info.mailing_address.line1 = address_lines[0] if len(address_lines) > 0 else ""
                company_info.mailing_address.line2 = address_lines[1] if len(address_lines) > 1 else ""
                company_info.mailing_address.line3 = address_lines[2] if len(address_lines) > 2 else ""
            
            # Extract specific address components
            state_elem = company_data.find(".//STATE")
            if state_elem is not None and state_elem.text:
                company_info.mailing_address.state = state_elem.text.strip()
            
            country_elem = company_data.find(".//COUNTRY")
            if country_elem is not None and country_elem.text:
                company_info.mailing_address.country = country_elem.text.strip()
            
            pincode_elem = company_data.find(".//PINCODE")
            if pincode_elem is not None and pincode_elem.text:
                company_info.mailing_address.postal_code = pincode_elem.text.strip()
            
            # Contact information
            phone_elem = company_data.find(".//PHONENUMBER")
            if phone_elem is not None and phone_elem.text:
                company_info.mailing_address.phone = phone_elem.text.strip()
            
            mobile_elem = company_data.find(".//MOBILENUMBER")
            if mobile_elem is not None and mobile_elem.text:
                company_info.mailing_address.mobile = mobile_elem.text.strip()
            
            email_elem = company_data.find(".//EMAIL")
            if email_elem is not None and email_elem.text:
                company_info.mailing_address.email = email_elem.text.strip()
            
            website_elem = company_data.find(".//WEBSITE")
            if website_elem is not None and website_elem.text:
                company_info.mailing_address.website = website_elem.text.strip()
            
            # Copy mailing address to billing address if not specified separately
            company_info.billing_address = company_info.mailing_address
            
            logger.debug("Parsed company address information")
            
        except Exception as e:
            logger.warning(f"Error parsing company address: {e}")
    
    
    def _parse_financial_year(self, company_data, company_info):
        """
        Parse financial year information from XML
        
        Args:
            company_data: XML element containing company data
            company_info: CompanyInfo object to populate
        """
        try:
            from datetime import datetime
            from ..models.company_model import FinancialYearInfo, FinancialYearType
            
            # Extract financial year dates
            start_date_elem = company_data.find(".//STARTINGFROM")
            end_date_elem = company_data.find(".//ENDINGAT")
            
            if start_date_elem is not None and start_date_elem.text:
                start_date_str = start_date_elem.text.strip()
                try:
                    # TallyPrime date format is typically YYYYMMDD
                    if len(start_date_str) == 8 and start_date_str.isdigit():
                        start_date = datetime.strptime(start_date_str, "%Y%m%d").date()
                        company_info.current_financial_year.start_date = start_date
                    else:
                        # Try alternative date formats
                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
                            try:
                                start_date = datetime.strptime(start_date_str, fmt).date()
                                company_info.current_financial_year.start_date = start_date
                                break
                            except ValueError:
                                continue
                except ValueError as e:
                    logger.warning(f"Could not parse start date '{start_date_str}': {e}")
            
            if end_date_elem is not None and end_date_elem.text:
                end_date_str = end_date_elem.text.strip()
                try:
                    # TallyPrime date format is typically YYYYMMDD
                    if len(end_date_str) == 8 and end_date_str.isdigit():
                        end_date = datetime.strptime(end_date_str, "%Y%m%d").date()
                        company_info.current_financial_year.end_date = end_date
                    else:
                        # Try alternative date formats
                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
                            try:
                                end_date = datetime.strptime(end_date_str, fmt).date()
                                company_info.current_financial_year.end_date = end_date
                                break
                            except ValueError:
                                continue
                except ValueError as e:
                    logger.warning(f"Could not parse end date '{end_date_str}': {e}")
            
            # Determine financial year type based on dates
            if (company_info.current_financial_year.start_date and 
                company_info.current_financial_year.start_date.month == 4 and
                company_info.current_financial_year.start_date.day == 1):
                company_info.current_financial_year.year_type = FinancialYearType.APRIL_TO_MARCH
            elif (company_info.current_financial_year.start_date and
                  company_info.current_financial_year.start_date.month == 1 and
                  company_info.current_financial_year.start_date.day == 1):
                company_info.current_financial_year.year_type = FinancialYearType.JANUARY_TO_DECEMBER
            else:
                company_info.current_financial_year.year_type = FinancialYearType.CUSTOM
            
            company_info.current_financial_year.is_current = True
            
            logger.debug("Parsed financial year information")
            
        except Exception as e:
            logger.warning(f"Error parsing financial year: {e}")
    
    
    def _parse_tax_info(self, company_data, company_info):
        """
        Parse tax registration information from XML
        
        Args:
            company_data: XML element containing company data
            company_info: CompanyInfo object to populate
        """
        try:
            # Extract GST information
            gstin_elem = company_data.find(".//GSTIN") or company_data.find(".//GSTREGISTRATIONNUMBER")
            if gstin_elem is not None and gstin_elem.text:
                company_info.tax_info.gstin = gstin_elem.text.strip()
            
            # Extract PAN information
            pan_elem = company_data.find(".//INCOMETAXNUMBER") or company_data.find(".//PAN")
            if pan_elem is not None and pan_elem.text:
                company_info.tax_info.pan = pan_elem.text.strip()
            
            # Extract other tax registrations
            tan_elem = company_data.find(".//TAN")
            if tan_elem is not None and tan_elem.text:
                company_info.tax_info.tan = tan_elem.text.strip()
            
            cin_elem = company_data.find(".//CIN")
            if cin_elem is not None and cin_elem.text:
                company_info.tax_info.cin = cin_elem.text.strip()
            
            logger.debug("Parsed tax registration information")
            
        except Exception as e:
            logger.warning(f"Error parsing tax information: {e}")
    
    
    def _parse_company_features(self, company_data, company_info):
        """
        Parse company features and configuration from XML
        
        Args:
            company_data: XML element containing company data
            company_info: CompanyInfo object to populate
        """
        try:
            from ..models.company_model import CompanyFeatures
            
            # Initialize features object
            features = CompanyFeatures()
            
            # Parse various feature flags from TallyPrime XML
            # These are typically found in REMOTECMPINFO or similar sections
            
            # Bill-wise details
            bill_wise_elem = company_data.find(".//ISBILLWISEON")
            if bill_wise_elem is not None and bill_wise_elem.text:
                features.maintain_bill_wise_details = bill_wise_elem.text.strip().lower() == "yes"
            
            # Cost centers
            cost_center_elem = company_data.find(".//ISCOSTCENTRESON")
            if cost_center_elem is not None and cost_center_elem.text:
                features.use_cost_centers = cost_center_elem.text.strip().lower() == "yes"
            
            # Multi-currency
            multicurrency_elem = company_data.find(".//ISMULTICURRENCYON")
            if multicurrency_elem is not None and multicurrency_elem.text:
                features.use_multi_currency = multicurrency_elem.text.strip().lower() == "yes"
            
            company_info.features = features
            
            logger.debug("Parsed company features")
            
        except Exception as e:
            logger.warning(f"Error parsing company features: {e}")
    
    
    def _parse_currency_info(self, company_data, company_info):
        """
        Parse currency information from XML
        
        Args:
            company_data: XML element containing company data
            company_info: CompanyInfo object to populate
        """
        try:
            # Extract base currency
            currency_elem = company_data.find(".//BASECURRENCYSYMBOL")
            if currency_elem is not None and currency_elem.text:
                company_info.base_currency_symbol = currency_elem.text.strip()
            
            currency_name_elem = company_data.find(".//BASECURRENCY")
            if currency_name_elem is not None and currency_name_elem.text:
                company_info.base_currency_name = currency_name_elem.text.strip()
            
            # Extract decimal places
            decimal_elem = company_data.find(".//DECIMALPLACES")
            if decimal_elem is not None and decimal_elem.text:
                try:
                    company_info.decimal_places = int(decimal_elem.text.strip())
                except ValueError:
                    logger.warning(f"Invalid decimal places value: {decimal_elem.text}")
            
            logger.debug("Parsed currency information")
            
        except Exception as e:
            logger.warning(f"Error parsing currency information: {e}")
    
    
    def _parse_company_statistics(self, xml_root, company_info):
        """
        Parse company statistics from XML (if available)
        
        Args:
            xml_root: XML root element
            company_info: CompanyInfo object to populate
        """
        try:
            # Statistics might be in a separate section or computed differently
            # For now, set default values - these will be updated when we implement
            # specific data reading methods
            
            # These would typically come from separate requests or be computed
            company_info.total_ledgers = 0
            company_info.total_groups = 0
            company_info.total_vouchers = 0
            company_info.total_stock_items = 0
            
            logger.debug("Initialized company statistics (to be updated separately)")
            
        except Exception as e:
            logger.warning(f"Error parsing company statistics: {e}")
    
    
    async def get_ledger_list(self) -> TallyResponse:
        """
        Retrieve list of all ledgers from TallyPrime
        
        Returns:
            TallyResponse containing ledger list data or error information
        """
        logger.info("Requesting ledger list from TallyPrime")
        return await self._send_data_request(TallyDataType.LEDGER_LIST)
    
    
    def parse_ledger_list(self, xml_data: str) -> List:
        """
        Parse ledger list from TallyPrime XML response
        
        This method extracts ledger information from the XML response and
        converts them into a list of structured LedgerInfo objects for GUI display.
        
        Args:
            xml_data: Raw XML response containing ledger list data
            
        Returns:
            List of LedgerInfo objects or empty list if parsing fails
        """
        from ..models.ledger_model import (
            LedgerInfo, LedgerBalance, LedgerContact, LedgerTaxInfo,
            LedgerType, BalanceType, classify_ledger_type
        )
        from decimal import Decimal
        
        try:
            # Parse XML response
            root = self.parse_xml_response(xml_data)
            if root is None:
                logger.error("Failed to parse ledger list XML response")
                return []
            
            ledgers = []
            
            # Find all ledger entries in XML
            # TallyPrime ledger list can be in different XML structures
            ledger_elements = (
                root.findall(".//LEDGER") +
                root.findall(".//TALLYMESSAGE[@vchtype='Ledger']") +
                root.findall(".//DSP_NAME")  # Sometimes ledgers are in DSP_NAME elements
            )
            
            if not ledger_elements:
                logger.warning("No ledger elements found in XML response")
                logger.debug(f"XML structure: {ET.tostring(root, encoding='unicode')[:500]}...")
                return []
            
            logger.info(f"Found {len(ledger_elements)} ledger elements to parse")
            
            for i, ledger_elem in enumerate(ledger_elements):
                try:
                    ledger_info = self._parse_single_ledger(ledger_elem)
                    if ledger_info:
                        ledgers.append(ledger_info)
                        if i % 50 == 0:  # Log progress for large lists
                            logger.debug(f"Parsed {i+1}/{len(ledger_elements)} ledgers")
                except Exception as e:
                    logger.warning(f"Failed to parse ledger element {i}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(ledgers)} ledgers from XML response")
            
            # Sort ledgers by name for consistent display
            ledgers.sort(key=lambda l: l.name.lower())
            
            return ledgers
            
        except Exception as e:
            logger.error(f"Error parsing ledger list: {e}", exc_info=True)
            return []
    
    
    def _parse_single_ledger(self, ledger_elem) -> Optional:
        """
        Parse a single ledger element from XML
        
        Args:
            ledger_elem: XML element containing ledger data
            
        Returns:
            LedgerInfo object or None if parsing fails
        """
        from ..models.ledger_model import (
            LedgerInfo, LedgerBalance, LedgerContact, LedgerTaxInfo,
            LedgerType, BalanceType, classify_ledger_type
        )
        from decimal import Decimal, InvalidOperation
        
        try:
            ledger_info = LedgerInfo()
            
            # Extract basic ledger information
            # Ledger name - can be in different elements
            name_elem = (
                ledger_elem.find(".//NAME") or 
                ledger_elem.find(".//LEDGERNAME") or
                ledger_elem
            )
            
            if name_elem is not None:
                if name_elem.text:
                    ledger_info.name = name_elem.text.strip()
                elif hasattr(name_elem, 'attrib') and 'NAME' in name_elem.attrib:
                    ledger_info.name = name_elem.attrib['NAME'].strip()
            
            if not ledger_info.name:
                # Try to get name from element text directly
                if ledger_elem.text and ledger_elem.text.strip():
                    ledger_info.name = ledger_elem.text.strip()
                else:
                    logger.debug("Ledger element has no name, skipping")
                    return None
            
            # Extract GUID/ID
            guid_elem = ledger_elem.find(".//GUID") or ledger_elem.find(".//MASTERID")
            if guid_elem is not None and guid_elem.text:
                ledger_info.guid = guid_elem.text.strip()
            
            # Extract alias
            alias_elem = ledger_elem.find(".//ALIAS")
            if alias_elem is not None and alias_elem.text:
                ledger_info.alias = alias_elem.text.strip()
            
            # Extract parent group
            parent_elem = (
                ledger_elem.find(".//PARENT") or 
                ledger_elem.find(".//PARENTGROUP") or
                ledger_elem.find(".//GROUP")
            )
            if parent_elem is not None and parent_elem.text:
                ledger_info.parent_group_name = parent_elem.text.strip()
            
            # Classify ledger type based on group and name
            ledger_info.ledger_type = classify_ledger_type(
                ledger_info.parent_group_name, 
                ledger_info.name
            )
            
            # Extract balance information
            self._parse_ledger_balance(ledger_elem, ledger_info)
            
            # Extract ledger properties
            self._parse_ledger_properties(ledger_elem, ledger_info)
            
            # Extract contact information
            self._parse_ledger_contact(ledger_elem, ledger_info)
            
            # Extract tax information
            self._parse_ledger_tax_info(ledger_elem, ledger_info)
            
            # Extract banking information
            self._parse_ledger_banking_info(ledger_elem, ledger_info)
            
            logger.debug(f"Successfully parsed ledger: {ledger_info.name}")
            return ledger_info
            
        except Exception as e:
            logger.warning(f"Error parsing single ledger: {e}")
            return None
    
    
    def _parse_ledger_balance(self, ledger_elem, ledger_info):
        """
        Parse ledger balance information from XML
        
        Args:
            ledger_elem: XML element containing ledger data
            ledger_info: LedgerInfo object to populate
        """
        try:
            from ..models.ledger_model import LedgerBalance, BalanceType
            from decimal import Decimal, InvalidOperation
            
            balance = LedgerBalance()
            
            # Extract current balance - can be in different elements
            balance_elements = [
                ledger_elem.find(".//CLOSINGBALANCE"),
                ledger_elem.find(".//CURRENTBALANCE"),
                ledger_elem.find(".//BALANCE"),
                ledger_elem.find(".//AMOUNT")
            ]
            
            current_balance = Decimal('0')
            balance_type = BalanceType.ZERO
            
            for balance_elem in balance_elements:
                if balance_elem is not None and balance_elem.text:
                    try:
                        # Clean the balance text (remove currency symbols, commas)
                        balance_text = balance_elem.text.strip()
                        balance_text = balance_text.replace(',', '').replace('₹', '').replace('Rs.', '')
                        
                        # Check for Dr/Cr indicators
                        is_credit = False
                        if balance_text.endswith(' Cr') or balance_text.endswith(' Credit'):
                            is_credit = True
                            balance_text = balance_text.replace(' Cr', '').replace(' Credit', '')
                        elif balance_text.endswith(' Dr') or balance_text.endswith(' Debit'):
                            balance_text = balance_text.replace(' Dr', '').replace(' Debit', '')
                        
                        # Parse the numeric value
                        current_balance = Decimal(balance_text)
                        
                        # Determine balance type
                        if current_balance == 0:
                            balance_type = BalanceType.ZERO
                        elif is_credit:
                            balance_type = BalanceType.CREDIT
                        else:
                            balance_type = BalanceType.DEBIT
                        
                        break  # Found a valid balance, stop looking
                        
                    except (InvalidOperation, ValueError) as e:
                        logger.debug(f"Could not parse balance '{balance_elem.text}': {e}")
                        continue
            
            # Set balance information
            balance.current_balance = current_balance
            balance.closing_balance = current_balance
            balance.balance_type = balance_type
            
            # Extract opening balance if available
            opening_elem = ledger_elem.find(".//OPENINGBALANCE")
            if opening_elem is not None and opening_elem.text:
                try:
                    opening_text = opening_elem.text.strip().replace(',', '').replace('₹', '').replace('Rs.', '')
                    opening_text = opening_text.replace(' Cr', '').replace(' Dr', '').replace(' Credit', '').replace(' Debit', '')
                    balance.opening_balance = Decimal(opening_text)
                except (InvalidOperation, ValueError):
                    pass
            
            # Extract year-to-date figures if available
            debit_elem = ledger_elem.find(".//TOTALDEBIT") or ledger_elem.find(".//DEBITAMOUNT")
            if debit_elem is not None and debit_elem.text:
                try:
                    debit_text = debit_elem.text.strip().replace(',', '').replace('₹', '').replace('Rs.', '')
                    balance.ytd_debit = Decimal(debit_text)
                except (InvalidOperation, ValueError):
                    pass
            
            credit_elem = ledger_elem.find(".//TOTALCREDIT") or ledger_elem.find(".//CREDITAMOUNT")
            if credit_elem is not None and credit_elem.text:
                try:
                    credit_text = credit_elem.text.strip().replace(',', '').replace('₹', '').replace('Rs.', '')
                    balance.ytd_credit = Decimal(credit_text)
                except (InvalidOperation, ValueError):
                    pass
            
            ledger_info.balance = balance
            logger.debug(f"Parsed balance for {ledger_info.name}: {balance.get_balance_display()}")
            
        except Exception as e:
            logger.warning(f"Error parsing ledger balance: {e}")
    
    
    def _parse_ledger_properties(self, ledger_elem, ledger_info):
        """
        Parse ledger properties and flags from XML
        
        Args:
            ledger_elem: XML element containing ledger data
            ledger_info: LedgerInfo object to populate
        """
        try:
            # Revenue flag
            revenue_elem = ledger_elem.find(".//ISREVENUE")
            if revenue_elem is not None and revenue_elem.text:
                ledger_info.is_revenue = revenue_elem.text.strip().lower() == "yes"
            
            # Deemed positive flag
            deemedpos_elem = ledger_elem.find(".//ISDEEMEDPOSITIVE")
            if deemedpos_elem is not None and deemedpos_elem.text:
                ledger_info.is_deemedpositive = deemedpos_elem.text.strip().lower() == "yes"
            
            # Bill-wise details flag
            billwise_elem = ledger_elem.find(".//ISBILLWISEON")
            if billwise_elem is not None and billwise_elem.text:
                ledger_info.is_bill_wise_on = billwise_elem.text.strip().lower() == "yes"
            
            # Cost center flag
            costcentre_elem = ledger_elem.find(".//ISCOSTCENTRESON")
            if costcentre_elem is not None and costcentre_elem.text:
                ledger_info.is_cost_centre_on = costcentre_elem.text.strip().lower() == "yes"
            
            # Interest flag
            interest_elem = ledger_elem.find(".//ISINTERESTON")
            if interest_elem is not None and interest_elem.text:
                ledger_info.is_interest_on = interest_elem.text.strip().lower() == "yes"
            
            # Credit limit
            credit_limit_elem = ledger_elem.find(".//CREDITLIMIT")
            if credit_limit_elem is not None and credit_limit_elem.text:
                try:
                    from decimal import Decimal
                    credit_text = credit_limit_elem.text.strip().replace(',', '').replace('₹', '').replace('Rs.', '')
                    ledger_info.credit_limit = Decimal(credit_text)
                except (ValueError, decimal.InvalidOperation):
                    pass
            
            # Credit period
            credit_period_elem = ledger_elem.find(".//CREDITPERIOD")
            if credit_period_elem is not None and credit_period_elem.text:
                try:
                    ledger_info.credit_period = int(credit_period_elem.text.strip())
                except ValueError:
                    pass
            
            logger.debug(f"Parsed properties for {ledger_info.name}")
            
        except Exception as e:
            logger.warning(f"Error parsing ledger properties: {e}")
    
    
    def _parse_ledger_contact(self, ledger_elem, ledger_info):
        """
        Parse ledger contact information from XML
        
        Args:
            ledger_elem: XML element containing ledger data
            ledger_info: LedgerInfo object to populate
        """
        try:
            from ..models.ledger_model import LedgerContact
            
            contact = LedgerContact()
            
            # Extract contact person
            contact_person_elem = ledger_elem.find(".//CONTACTPERSON")
            if contact_person_elem is not None and contact_person_elem.text:
                contact.contact_person = contact_person_elem.text.strip()
            
            # Extract phone numbers
            phone_elem = ledger_elem.find(".//PHONENUMBER")
            if phone_elem is not None and phone_elem.text:
                contact.phone = phone_elem.text.strip()
            
            mobile_elem = ledger_elem.find(".//MOBILENUMBER")
            if mobile_elem is not None and mobile_elem.text:
                contact.mobile = mobile_elem.text.strip()
            
            # Extract email
            email_elem = ledger_elem.find(".//EMAIL")
            if email_elem is not None and email_elem.text:
                contact.email = email_elem.text.strip()
            
            # Extract website
            website_elem = ledger_elem.find(".//WEBSITE")
            if website_elem is not None and website_elem.text:
                contact.website = website_elem.text.strip()
            
            # Extract address information
            address_lines = []
            for i in range(1, 6):  # ADDRESS1 to ADDRESS5
                addr_elem = ledger_elem.find(f".//ADDRESS{i}")
                if addr_elem is not None and addr_elem.text:
                    address_lines.append(addr_elem.text.strip())
            
            if address_lines:
                contact.address_line1 = address_lines[0] if len(address_lines) > 0 else ""
                contact.address_line2 = address_lines[1] if len(address_lines) > 1 else ""
            
            # Extract location details
            city_elem = ledger_elem.find(".//CITY")
            if city_elem is not None and city_elem.text:
                contact.city = city_elem.text.strip()
            
            state_elem = ledger_elem.find(".//STATE")
            if state_elem is not None and state_elem.text:
                contact.state = state_elem.text.strip()
            
            country_elem = ledger_elem.find(".//COUNTRY")
            if country_elem is not None and country_elem.text:
                contact.country = country_elem.text.strip()
            
            pincode_elem = ledger_elem.find(".//PINCODE")
            if pincode_elem is not None and pincode_elem.text:
                contact.postal_code = pincode_elem.text.strip()
            
            ledger_info.contact_info = contact
            
            if contact.email or contact.phone:
                logger.debug(f"Parsed contact info for {ledger_info.name}")
            
        except Exception as e:
            logger.warning(f"Error parsing ledger contact: {e}")
    
    
    def _parse_ledger_tax_info(self, ledger_elem, ledger_info):
        """
        Parse ledger tax information from XML
        
        Args:
            ledger_elem: XML element containing ledger data
            ledger_info: LedgerInfo object to populate
        """
        try:
            from ..models.ledger_model import LedgerTaxInfo
            from decimal import Decimal
            
            tax_info = LedgerTaxInfo()
            
            # Extract GST information
            gstin_elem = ledger_elem.find(".//GSTIN") or ledger_elem.find(".//GSTREGISTRATIONNUMBER")
            if gstin_elem is not None and gstin_elem.text:
                tax_info.gstin = gstin_elem.text.strip()
                tax_info.gst_applicable = True
            
            # Extract PAN
            pan_elem = ledger_elem.find(".//INCOMETAXNUMBER") or ledger_elem.find(".//PAN")
            if pan_elem is not None and pan_elem.text:
                tax_info.pan = pan_elem.text.strip()
            
            # Extract other tax details
            tan_elem = ledger_elem.find(".//TAN")
            if tan_elem is not None and tan_elem.text:
                tax_info.tan = tan_elem.text.strip()
            
            # Extract tax rate
            tax_rate_elem = ledger_elem.find(".//TAXRATE")
            if tax_rate_elem is not None and tax_rate_elem.text:
                try:
                    rate_text = tax_rate_elem.text.strip().replace('%', '')
                    tax_info.tax_rate = Decimal(rate_text)
                except (ValueError, decimal.InvalidOperation):
                    pass
            
            # Extract HSN code
            hsn_elem = ledger_elem.find(".//HSNCODE") or ledger_elem.find(".//HSNNUMBER")
            if hsn_elem is not None and hsn_elem.text:
                tax_info.hsn_code = hsn_elem.text.strip()
            
            ledger_info.tax_info = tax_info
            
            if tax_info.gstin:
                logger.debug(f"Parsed tax info for {ledger_info.name}: GST {tax_info.gstin}")
            
        except Exception as e:
            logger.warning(f"Error parsing ledger tax info: {e}")
    
    
    def _parse_ledger_banking_info(self, ledger_elem, ledger_info):
        """
        Parse ledger banking information from XML
        
        Args:
            ledger_elem: XML element containing ledger data
            ledger_info: LedgerInfo object to populate
        """
        try:
            # Bank name
            bank_name_elem = ledger_elem.find(".//BANKNAME")
            if bank_name_elem is not None and bank_name_elem.text:
                ledger_info.bank_name = bank_name_elem.text.strip()
            
            # Account number
            account_elem = ledger_elem.find(".//ACCOUNTNUMBER")
            if account_elem is not None and account_elem.text:
                ledger_info.account_number = account_elem.text.strip()
            
            # IFSC code
            ifsc_elem = ledger_elem.find(".//IFSCCODE")
            if ifsc_elem is not None and ifsc_elem.text:
                ledger_info.ifsc_code = ifsc_elem.text.strip()
            
            # Branch name
            branch_elem = ledger_elem.find(".//BRANCHNAME")
            if branch_elem is not None and branch_elem.text:
                ledger_info.branch_name = branch_elem.text.strip()
            
            if ledger_info.account_number:
                logger.debug(f"Parsed banking info for {ledger_info.name}: {ledger_info.account_number}")
            
        except Exception as e:
            logger.warning(f"Error parsing ledger banking info: {e}")
    
    
    async def get_ledger_details(self, ledger_name: str) -> TallyResponse:
        """
        Retrieve detailed information for a specific ledger
        
        Args:
            ledger_name: Name of the ledger to retrieve
            
        Returns:
            TallyResponse containing ledger details or error information
        """
        logger.info(f"Requesting details for ledger: {ledger_name}")
        return await self._send_data_request(
            TallyDataType.LEDGER_DETAILS,
            ledger_name=ledger_name
        )
    
    
    async def get_balance_sheet(self) -> TallyResponse:
        """
        Retrieve balance sheet report from TallyPrime
        
        Returns:
            TallyResponse containing balance sheet data or error information
        """
        logger.info("Requesting balance sheet from TallyPrime")
        return await self._send_data_request(TallyDataType.BALANCE_SHEET)
    
    
    async def get_day_book(self, from_date: str, to_date: str) -> TallyResponse:
        """
        Retrieve day book entries for specified date range
        
        Args:
            from_date: Start date in DD-MM-YYYY format
            to_date: End date in DD-MM-YYYY format
            
        Returns:
            TallyResponse containing day book data or error information
        """
        logger.info(f"Requesting day book from {from_date} to {to_date}")
        return await self._send_data_request(
            TallyDataType.DAY_BOOK,
            from_date=from_date,
            to_date=to_date
        )
    
    
    async def get_voucher_list(self, from_date: str, to_date: str) -> TallyResponse:
        """
        Retrieve voucher list for specified date range
        
        Args:
            from_date: Start date in DD-MM-YYYY format
            to_date: End date in DD-MM-YYYY format
            
        Returns:
            TallyResponse containing voucher list data or error information
        """
        logger.info(f"Requesting voucher list from {from_date} to {to_date}")
        return await self._send_data_request(
            TallyDataType.VOUCHER_LIST,
            from_date=from_date,
            to_date=to_date
        )
    
    
    async def get_voucher_details(self, voucher_number: str, voucher_type: str) -> TallyResponse:
        """
        Retrieve detailed information for a specific voucher
        
        Args:
            voucher_number: Voucher number to retrieve
            voucher_type: Type of the voucher
            
        Returns:
            TallyResponse containing voucher details or error information
        """
        logger.info(f"Requesting voucher details for {voucher_type} {voucher_number}")
        return await self._send_data_request(
            TallyDataType.VOUCHER_DETAILS,
            voucher_number=voucher_number,
            voucher_type=voucher_type
        )
    
    
    def parse_voucher_list(self, xml_data: str) -> List:
        """
        Parse voucher list from TallyPrime XML response
        
        This method extracts voucher information from the XML response and
        converts them into a list of structured VoucherInfo objects for GUI display.
        
        Args:
            xml_data: Raw XML response containing voucher list data
            
        Returns:
            List of VoucherInfo objects or empty list if parsing fails
        """
        from ..models.voucher_model import (
            VoucherInfo, TransactionEntry, VoucherType, TransactionType,
            classify_voucher_type
        )
        from decimal import Decimal
        from datetime import datetime
        
        try:
            # Parse XML response
            root = self.parse_xml_response(xml_data)
            if root is None:
                logger.error("Failed to parse voucher list XML response")
                return []
            
            vouchers = []
            
            # Find all voucher entries in XML
            # TallyPrime voucher list can be in different XML structures
            voucher_elements = (
                root.findall(".//VOUCHER") +
                root.findall(".//TALLYMESSAGE[@vchtype]") +
                root.findall(".//DSP_NAME")  # Sometimes vouchers are in DSP_NAME elements
            )
            
            if not voucher_elements:
                logger.warning("No voucher elements found in XML response")
                logger.debug(f"XML structure: {ET.tostring(root, encoding='unicode')[:500]}...")
                return []
            
            logger.info(f"Found {len(voucher_elements)} voucher elements to parse")
            
            for i, voucher_elem in enumerate(voucher_elements):
                try:
                    voucher_info = self._parse_single_voucher(voucher_elem)
                    if voucher_info:
                        vouchers.append(voucher_info)
                        if i % 25 == 0:  # Log progress for large lists
                            logger.debug(f"Parsed {i+1}/{len(voucher_elements)} vouchers")
                except Exception as e:
                    logger.warning(f"Failed to parse voucher element {i}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(vouchers)} vouchers from XML response")
            
            # Sort vouchers by date and voucher number for consistent display
            vouchers.sort(key=lambda v: (v.date or datetime.min.date(), v.voucher_number))
            
            return vouchers
            
        except Exception as e:
            logger.error(f"Error parsing voucher list: {e}", exc_info=True)
            return []
    
    
    def _parse_single_voucher(self, voucher_elem) -> Optional:
        """
        Parse a single voucher element from XML
        
        Args:
            voucher_elem: XML element containing voucher data
            
        Returns:
            VoucherInfo object or None if parsing fails
        """
        from ..models.voucher_model import (
            VoucherInfo, TransactionEntry, VoucherType, TransactionType,
            classify_voucher_type
        )
        from decimal import Decimal, InvalidOperation
        from datetime import datetime
        
        try:
            voucher_info = VoucherInfo()
            
            # Extract voucher type - can be in different attributes/elements
            voucher_type = None
            if hasattr(voucher_elem, 'attrib') and 'vchtype' in voucher_elem.attrib:
                voucher_type = voucher_elem.attrib['vchtype']
            else:
                type_elem = voucher_elem.find(".//VOUCHERTYPE") or voucher_elem.find(".//VCHTYPE")
                if type_elem is not None and type_elem.text:
                    voucher_type = type_elem.text.strip()
            
            if voucher_type:
                voucher_info.voucher_type = classify_voucher_type(voucher_type)
            
            # Extract voucher number
            number_elem = (
                voucher_elem.find(".//VOUCHERNUMBER") or
                voucher_elem.find(".//NUMBER") or
                voucher_elem.find(".//VCHNO")
            )
            if number_elem is not None and number_elem.text:
                voucher_info.voucher_number = number_elem.text.strip()
            elif hasattr(voucher_elem, 'attrib') and 'NUMBER' in voucher_elem.attrib:
                voucher_info.voucher_number = voucher_elem.attrib['NUMBER']
            
            # Extract voucher date
            date_elem = (
                voucher_elem.find(".//DATE") or
                voucher_elem.find(".//VCHDATE") or
                voucher_elem.find(".//VOUCHERDATE")
            )
            if date_elem is not None and date_elem.text:
                try:
                    date_str = date_elem.text.strip()
                    # TallyPrime date format is typically YYYYMMDD
                    if len(date_str) == 8 and date_str.isdigit():
                        voucher_info.date = datetime.strptime(date_str, "%Y%m%d").date()
                    else:
                        # Try alternative date formats
                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
                            try:
                                voucher_info.date = datetime.strptime(date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                except ValueError as e:
                    logger.debug(f"Could not parse voucher date '{date_elem.text}': {e}")
            
            # Extract GUID
            guid_elem = voucher_elem.find(".//GUID") or voucher_elem.find(".//MASTERID")
            if guid_elem is not None and guid_elem.text:
                voucher_info.guid = guid_elem.text.strip()
            
            # Extract narration
            narration_elem = (
                voucher_elem.find(".//NARRATION") or
                voucher_elem.find(".//VCHNARRATION") or
                voucher_elem.find(".//DESCRIPTION")
            )
            if narration_elem is not None and narration_elem.text:
                voucher_info.narration = narration_elem.text.strip()
            
            # Extract reference
            reference_elem = voucher_elem.find(".//REFERENCE")
            if reference_elem is not None and reference_elem.text:
                voucher_info.reference = reference_elem.text.strip()
            
            # Extract amount information
            self._parse_voucher_amounts(voucher_elem, voucher_info)
            
            # Extract transaction entries
            self._parse_voucher_entries(voucher_elem, voucher_info)
            
            # Extract party information (for party vouchers)
            self._parse_voucher_party_info(voucher_elem, voucher_info)
            
            # Extract voucher properties
            self._parse_voucher_properties(voucher_elem, voucher_info)
            
            logger.debug(f"Successfully parsed voucher: {voucher_info.voucher_type.value} {voucher_info.voucher_number}")
            return voucher_info
            
        except Exception as e:
            logger.warning(f"Error parsing single voucher: {e}")
            return None
    
    
    def _parse_voucher_amounts(self, voucher_elem, voucher_info):
        """
        Parse voucher amount information from XML
        
        Args:
            voucher_elem: XML element containing voucher data
            voucher_info: VoucherInfo object to populate
        """
        try:
            from decimal import Decimal, InvalidOperation
            
            # Extract total amount
            amount_elements = [
                voucher_elem.find(".//AMOUNT"),
                voucher_elem.find(".//TOTALAMOUNT"),
                voucher_elem.find(".//VOUCHERAMOUNT")
            ]
            
            for amount_elem in amount_elements:
                if amount_elem is not None and amount_elem.text:
                    try:
                        amount_text = amount_elem.text.strip().replace(',', '').replace('₹', '').replace('Rs.', '')
                        # Remove Dr/Cr indicators
                        amount_text = amount_text.replace(' Dr', '').replace(' Cr', '').replace(' Debit', '').replace(' Credit', '')
                        voucher_info.total_amount = abs(Decimal(amount_text))
                        break
                    except (InvalidOperation, ValueError):
                        continue
            
            # For now, assume balanced voucher (total debits = total credits = total amount)
            voucher_info.total_debit = voucher_info.total_amount
            voucher_info.total_credit = voucher_info.total_amount
            
            logger.debug(f"Parsed amounts for voucher: {voucher_info.total_amount}")
            
        except Exception as e:
            logger.warning(f"Error parsing voucher amounts: {e}")
    
    
    def _parse_voucher_entries(self, voucher_elem, voucher_info):
        """
        Parse voucher transaction entries from XML
        
        Args:
            voucher_elem: XML element containing voucher data
            voucher_info: VoucherInfo object to populate
        """
        try:
            from ..models.voucher_model import TransactionEntry, TransactionType
            from decimal import Decimal, InvalidOperation
            
            entries = []
            
            # Find ledger entries - can be in different XML structures
            entry_elements = (
                voucher_elem.findall(".//LEDGERENTRIES.LIST") +
                voucher_elem.findall(".//ALLLEDGERENTRIES.LIST") +
                voucher_elem.findall(".//LEDGER")
            )
            
            for entry_elem in entry_elements:
                try:
                    entry = TransactionEntry()
                    
                    # Extract ledger name
                    ledger_elem = (
                        entry_elem.find(".//LEDGERNAME") or
                        entry_elem.find(".//LEDGER") or
                        entry_elem.find(".//NAME")
                    )
                    if ledger_elem is not None and ledger_elem.text:
                        entry.ledger_name = ledger_elem.text.strip()
                    
                    # Extract amount and determine debit/credit
                    amount_elem = entry_elem.find(".//AMOUNT")
                    if amount_elem is not None and amount_elem.text:
                        try:
                            amount_text = amount_elem.text.strip()
                            
                            # Check for negative amount (indicates credit)
                            is_credit = amount_text.startswith('-')
                            
                            # Clean amount text
                            amount_text = amount_text.replace('-', '').replace(',', '').replace('₹', '').replace('Rs.', '')
                            amount_text = amount_text.replace(' Dr', '').replace(' Cr', '').replace(' Debit', '').replace(' Credit', '')
                            
                            entry.amount = Decimal(amount_text)
                            entry.transaction_type = TransactionType.CREDIT if is_credit else TransactionType.DEBIT
                            
                        except (InvalidOperation, ValueError) as e:
                            logger.debug(f"Could not parse entry amount '{amount_elem.text}': {e}")
                            continue
                    
                    # Extract entry narration
                    entry_narration_elem = entry_elem.find(".//NARRATION")
                    if entry_narration_elem is not None and entry_narration_elem.text:
                        entry.narration = entry_narration_elem.text.strip()
                    
                    if entry.ledger_name and entry.amount > 0:
                        entries.append(entry)
                        
                except Exception as e:
                    logger.debug(f"Error parsing voucher entry: {e}")
                    continue
            
            voucher_info.entries = entries
            
            if entries:
                logger.debug(f"Parsed {len(entries)} entries for voucher")
            
        except Exception as e:
            logger.warning(f"Error parsing voucher entries: {e}")
    
    
    def _parse_voucher_party_info(self, voucher_elem, voucher_info):
        """
        Parse voucher party information from XML
        
        Args:
            voucher_elem: XML element containing voucher data
            voucher_info: VoucherInfo object to populate
        """
        try:
            from ..models.voucher_model import VoucherType
            
            # For sales/purchase/payment/receipt vouchers, identify the party
            if voucher_info.voucher_type in [VoucherType.SALES, VoucherType.PURCHASE, 
                                           VoucherType.PAYMENT, VoucherType.RECEIPT]:
                
                # Look for party ledger in entries
                for entry in voucher_info.entries:
                    # Party is typically the non-cash, non-bank, non-tax ledger
                    ledger_lower = entry.ledger_name.lower()
                    if (not any(keyword in ledger_lower for keyword in 
                              ['cash', 'bank', 'cgst', 'sgst', 'igst', 'tax', 'sales', 'purchase'])):
                        voucher_info.party_ledger = entry.ledger_name
                        voucher_info.party_amount = entry.amount
                        break
            
            logger.debug(f"Identified party: {voucher_info.party_ledger}")
            
        except Exception as e:
            logger.warning(f"Error parsing voucher party info: {e}")
    
    
    def _parse_voucher_properties(self, voucher_elem, voucher_info):
        """
        Parse voucher properties and flags from XML
        
        Args:
            voucher_elem: XML element containing voucher data
            voucher_info: VoucherInfo object to populate
        """
        try:
            # Check if cancelled
            cancelled_elem = voucher_elem.find(".//ISCANCELLED")
            if cancelled_elem is not None and cancelled_elem.text:
                voucher_info.is_cancelled = cancelled_elem.text.strip().lower() == "yes"
            
            # Check if optional
            optional_elem = voucher_elem.find(".//ISOPTIONAL")
            if optional_elem is not None and optional_elem.text:
                voucher_info.is_optional = optional_elem.text.strip().lower() == "yes"
            
            # Check if invoice
            invoice_elem = voucher_elem.find(".//ISINVOICE")
            if invoice_elem is not None and invoice_elem.text:
                voucher_info.is_invoice = invoice_elem.text.strip().lower() == "yes"
            
            # Determine if accounting voucher (has ledger entries)
            voucher_info.is_accounting_voucher = len(voucher_info.entries) > 0
            
            from ..models.voucher_model import VoucherType
            
            # Determine if inventory voucher (check for stock entries)
            voucher_info.is_inventory_voucher = voucher_info.voucher_type in [
                VoucherType.SALES, VoucherType.PURCHASE, VoucherType.STOCK_JOURNAL
            ]
            
            logger.debug(f"Parsed properties for voucher")
            
        except Exception as e:
            logger.warning(f"Error parsing voucher properties: {e}")


# Convenience function for quick testing and development
def create_data_reader_from_config(config_dict: Dict[str, Any], enable_cache: bool = True, cache_size: int = 100) -> TallyDataReader:
    """
    Create a TallyDataReader with TallyConnector from configuration dictionary
    
    This convenience function simplifies the creation of a data reader
    for testing and development purposes with optional caching configuration.
    
    Args:
        config_dict: Configuration dictionary for TallyConnector
        enable_cache: Whether to enable data caching (default: True)
        cache_size: Maximum cache size (default: 100)
        
    Returns:
        Configured TallyDataReader instance with enhanced error handling and caching
        
    Example:
        config = {
            'host': '172.28.208.1',
            'port': 9000,
            'timeout': 30
        }
        reader = create_data_reader_from_config(config, enable_cache=True, cache_size=50)
    """
    from .connector import TallyConnectionConfig
    
    # Create connector configuration
    tally_config = TallyConnectionConfig.from_dict(config_dict)
    
    # Create and configure TallyConnector
    connector = TallyConnector(tally_config)
    
    # Create and return TallyDataReader with enhanced features
    reader = TallyDataReader(connector, enable_cache=enable_cache, cache_size=cache_size)
    
    logger.info(f"Created TallyDataReader from configuration (cache_enabled={enable_cache}, cache_size={cache_size})")
    return reader
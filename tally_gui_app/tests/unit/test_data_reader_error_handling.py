#!/usr/bin/env python3
"""
Unit Tests for TallyDataReader Enhanced Error Handling and Caching

This test suite validates the enhanced error handling capabilities and
data caching functionality of the TallyDataReader class. It covers
malformed XML handling, cache operations, and error diagnostics.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

import sys
import pytest
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add the tally_gui_app directory to sys.path for imports
current_dir = Path(__file__).parent
tally_gui_app_dir = current_dir.parent.parent
sys.path.insert(0, str(tally_gui_app_dir))

# Test imports
from core.tally.data_reader import (
    TallyDataReader, TallyDataCache, TallyXMLError, TallyDataType,
    CacheEntry, create_data_reader_from_config
)
from core.tally.connector import TallyConnector, TallyResponse


class TestTallyXMLError:
    """
    Test the TallyXMLError exception class for proper error information handling
    """
    
    def test_basic_error_creation(self):
        """Test basic TallyXMLError creation with minimal parameters"""
        error = TallyXMLError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.error_type == "GENERIC"
        assert error.xml_content is None
        assert error.original_error is None
        assert isinstance(error.timestamp, datetime)
    
    def test_detailed_error_creation(self):
        """Test TallyXMLError creation with all parameters"""
        original_exception = ValueError("Original error")
        xml_content = "<malformed>incomplete"
        
        error = TallyXMLError(
            "Detailed error message",
            "PARSE_ERROR",
            xml_content,
            original_exception
        )
        
        assert str(error) == "Detailed error message"
        assert error.error_type == "PARSE_ERROR"
        assert error.xml_content == xml_content
        assert error.original_error == original_exception
    
    def test_xml_content_truncation(self):
        """Test that XML content is truncated to 1000 characters"""
        long_xml = "<data>" + "x" * 2000 + "</data>"
        
        error = TallyXMLError("Test", "PARSE_ERROR", long_xml)
        
        assert len(error.xml_content) == 1000
        assert error.xml_content == long_xml[:1000]
    
    def test_debug_info(self):
        """Test debug information extraction"""
        original_exception = ET.ParseError("XML parsing failed")
        xml_content = "<malformed>content"
        
        error = TallyXMLError(
            "Test error",
            "PARSE_ERROR",
            xml_content,
            original_exception
        )
        
        debug_info = error.get_debug_info()
        
        assert debug_info['error_type'] == "PARSE_ERROR"
        assert debug_info['message'] == "Test error"
        assert 'timestamp' in debug_info
        assert debug_info['original_error'] == str(original_exception)
        assert debug_info['xml_snippet'] == xml_content
        assert debug_info['xml_length'] == len(xml_content)


class TestTallyDataCache:
    """
    Test the TallyDataCache class for proper caching functionality
    """
    
    def test_cache_initialization(self):
        """Test cache initialization with default and custom parameters"""
        # Test default initialization
        cache = TallyDataCache()
        assert cache.max_size == 100
        assert cache.default_expiry_seconds == 300
        assert len(cache._cache) == 0
        
        # Test custom initialization
        cache = TallyDataCache(max_size=50, default_expiry_seconds=600)
        assert cache.max_size == 50
        assert cache.default_expiry_seconds == 600
    
    def test_cache_key_generation(self):
        """Test cache key generation for consistent hashing"""
        cache = TallyDataCache()
        
        # Test basic key generation
        key1 = cache._generate_cache_key(TallyDataType.COMPANY_INFO)
        key2 = cache._generate_cache_key(TallyDataType.COMPANY_INFO)
        assert key1 == key2  # Same parameters should produce same key
        
        # Test key generation with parameters
        key3 = cache._generate_cache_key(TallyDataType.LEDGER_DETAILS, ledger_name="Cash")
        key4 = cache._generate_cache_key(TallyDataType.LEDGER_DETAILS, ledger_name="Cash")
        assert key3 == key4
        
        # Different parameters should produce different keys
        key5 = cache._generate_cache_key(TallyDataType.LEDGER_DETAILS, ledger_name="Bank")
        assert key3 != key5
    
    def test_cache_put_and_get(self):
        """Test basic cache put and get operations"""
        cache = TallyDataCache(max_size=10)
        
        test_data = "<xml>company data</xml>"
        
        # Put data in cache
        cache.put(TallyDataType.COMPANY_INFO, test_data)
        
        # Get data from cache
        retrieved_data = cache.get(TallyDataType.COMPANY_INFO)
        assert retrieved_data == test_data
        
        # Test cache miss
        missing_data = cache.get(TallyDataType.LEDGER_LIST)
        assert missing_data is None
    
    def test_cache_expiry(self):
        """Test cache entry expiry functionality"""
        cache = TallyDataCache(max_size=10, default_expiry_seconds=1)  # 1 second expiry
        
        test_data = "<xml>test data</xml>"
        cache.put(TallyDataType.COMPANY_INFO, test_data)
        
        # Should be available immediately
        assert cache.get(TallyDataType.COMPANY_INFO) == test_data
        
        # Manually expire the entry by modifying timestamp
        cache_key = cache._generate_cache_key(TallyDataType.COMPANY_INFO)
        entry = cache._cache[cache_key]
        entry.timestamp = datetime.now() - timedelta(seconds=2)
        
        # Should be None after expiry
        assert cache.get(TallyDataType.COMPANY_INFO) is None
    
    def test_cache_lru_eviction(self):
        """Test LRU (Least Recently Used) cache eviction"""
        cache = TallyDataCache(max_size=3)
        
        # Fill cache to capacity
        cache.put(TallyDataType.COMPANY_INFO, "data1")
        cache.put(TallyDataType.LEDGER_LIST, "data2")
        cache.put(TallyDataType.BALANCE_SHEET, "data3")
        
        assert len(cache._cache) == 3
        
        # Access first item to make it recently used
        cache.get(TallyDataType.COMPANY_INFO)
        
        # Add fourth item - should evict least recently used
        cache.put(TallyDataType.DAY_BOOK, "data4")
        
        assert len(cache._cache) == 3
        assert cache.get(TallyDataType.COMPANY_INFO) == "data1"  # Should still be there
        assert cache.get(TallyDataType.LEDGER_LIST) is None  # Should be evicted
    
    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        cache = TallyDataCache()
        
        # Initial statistics
        stats = cache.get_statistics()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['evictions'] == 0
        
        # Add some data and access it
        cache.put(TallyDataType.COMPANY_INFO, "test_data")
        cache.get(TallyDataType.COMPANY_INFO)  # Hit
        cache.get(TallyDataType.LEDGER_LIST)   # Miss
        
        stats = cache.get_statistics()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['cache_size'] == 1
    
    def test_cache_cleanup(self):
        """Test cleanup of expired entries"""
        cache = TallyDataCache()
        
        # Add entries with different expiry times
        cache.put(TallyDataType.COMPANY_INFO, "data1")
        cache.put(TallyDataType.LEDGER_LIST, "data2")
        
        # Manually expire one entry
        cache_key = cache._generate_cache_key(TallyDataType.COMPANY_INFO)
        entry = cache._cache[cache_key]
        entry.timestamp = datetime.now() - timedelta(seconds=entry.expiry_seconds + 1)
        
        # Cleanup expired entries
        expired_count = cache.cleanup_expired()
        
        assert expired_count == 1
        assert len(cache._cache) == 1
        assert cache.get(TallyDataType.LEDGER_LIST) == "data2"


class TestTallyDataReaderErrorHandling:
    """
    Test enhanced error handling in TallyDataReader
    """
    
    def setup_method(self):
        """Set up test environment for each test method"""
        # Create mock connector
        self.mock_connector = Mock(spec=TallyConnector)
        self.mock_connector.status = Mock()
        self.mock_connector.status.value = "connected"
        
        # Create data reader with caching enabled
        self.data_reader = TallyDataReader(self.mock_connector, enable_cache=True, cache_size=10)
    
    def test_initialization_with_cache(self):
        """Test data reader initialization with caching enabled"""
        reader = TallyDataReader(self.mock_connector, enable_cache=True, cache_size=50)
        
        assert reader.cache_enabled is True
        assert reader.cache is not None
        assert reader.cache.max_size == 50
        
        # Test disabled cache
        reader_no_cache = TallyDataReader(self.mock_connector, enable_cache=False)
        assert reader_no_cache.cache_enabled is False
        assert reader_no_cache.cache is None
    
    def test_xml_content_cleaning_valid(self):
        """Test XML content cleaning with valid XML"""
        valid_xml = "  <xml>valid content</xml>  "
        cleaned = self.data_reader._clean_xml_content(valid_xml)
        assert cleaned == "<xml>valid content</xml>"
        
        # Test BOM removal
        bom_xml = "\ufeff<xml>content</xml>"
        cleaned = self.data_reader._clean_xml_content(bom_xml)
        assert cleaned == "<xml>content</xml>"
        
        # Test null byte removal
        null_xml = "<xml>content\x00here</xml>"
        cleaned = self.data_reader._clean_xml_content(null_xml)
        assert cleaned == "<xml>contenthere</xml>"
    
    def test_xml_content_cleaning_invalid(self):
        """Test XML content cleaning with invalid content"""
        # Test empty content
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._clean_xml_content("")
        assert exc_info.value.error_type == "EMPTY_CONTENT"
        
        # Test non-XML content
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._clean_xml_content("not xml content")
        assert exc_info.value.error_type == "INVALID_XML_START"
        
        # Test HTML content
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._clean_xml_content("<!doctype html><html>error</html>")
        assert exc_info.value.error_type == "HTML_RESPONSE"
        
        # Test JSON content
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._clean_xml_content('{"error": "message"}')
        assert exc_info.value.error_type == "JSON_RESPONSE"
    
    def test_xml_structure_validation(self):
        """Test validation of parsed XML structure"""
        # Create valid XML structure
        root = ET.fromstring("<ENVELOPE><DATA>content</DATA></ENVELOPE>")
        
        # Should not raise exception for valid structure
        self.data_reader._validate_parsed_xml_structure(
            root, TallyDataType.COMPANY_INFO, "<xml>content</xml>"
        )
        
        # Test with empty root structure
        empty_root = ET.fromstring("<ENVELOPE></ENVELOPE>")
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._validate_parsed_xml_structure(
                empty_root, TallyDataType.COMPANY_INFO, "<ENVELOPE></ENVELOPE>"
            )
        assert exc_info.value.error_type == "EMPTY_STRUCTURE"
    
    def test_tally_error_detection(self):
        """Test detection of TallyPrime error responses"""
        # Create XML with error elements
        error_xml = """
        <ENVELOPE>
            <ERROR>Connection failed</ERROR>
            <DATA>some data</DATA>
        </ENVELOPE>
        """
        root = ET.fromstring(error_xml)
        
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._check_tally_error_responses(root)
        assert exc_info.value.error_type == "TALLY_ERROR_RESPONSE"
        assert "Connection failed" in str(exc_info.value)
    
    def test_data_type_specific_validation(self):
        """Test validation specific to different data types"""
        # Test company info validation with valid data
        company_xml = """
        <ENVELOPE>
            <COMPANY>
                <NAME>Test Company</NAME>
            </COMPANY>
        </ENVELOPE>
        """
        root = ET.fromstring(company_xml)
        # Should not raise exception
        self.data_reader._validate_data_type_specific_content(root, TallyDataType.COMPANY_INFO)
        
        # Test company info validation with missing data
        empty_xml = "<ENVELOPE><DATA>no company info</DATA></ENVELOPE>"
        empty_root = ET.fromstring(empty_xml)
        with pytest.raises(TallyXMLError) as exc_info:
            self.data_reader._validate_data_type_specific_content(empty_root, TallyDataType.COMPANY_INFO)
        assert exc_info.value.error_type == "MISSING_COMPANY_DATA"
    
    def test_error_tracking(self):
        """Test error tracking for diagnostics"""
        initial_error_count = len(self.data_reader.recent_errors)
        
        # Create and track an error
        error = TallyXMLError("Test error", "TEST_ERROR")
        self.data_reader._track_error(error)
        
        assert len(self.data_reader.recent_errors) == initial_error_count + 1
        
        # Test error list limiting
        for i in range(15):  # Add more than max_recent_errors
            error = TallyXMLError(f"Error {i}", "TEST_ERROR")
            self.data_reader._track_error(error)
        
        assert len(self.data_reader.recent_errors) <= self.data_reader.max_recent_errors
    
    def test_enhanced_parse_xml_response(self):
        """Test enhanced XML parsing with error handling"""
        # Test valid XML parsing
        valid_xml = "<ENVELOPE><DATA>content</DATA></ENVELOPE>"
        root = self.data_reader.parse_xml_response(valid_xml)
        assert root is not None
        assert root.tag == "ENVELOPE"
        
        # Test invalid XML with raise_on_error=False
        invalid_xml = "<malformed>incomplete"
        root = self.data_reader.parse_xml_response(invalid_xml, raise_on_error=False)
        assert root is None
        
        # Test invalid XML with raise_on_error=True
        with pytest.raises(TallyXMLError):
            self.data_reader.parse_xml_response(invalid_xml, raise_on_error=True)
    
    @pytest.mark.asyncio
    async def test_send_data_request_with_caching(self):
        """Test data request with caching functionality"""
        # Mock successful response
        mock_response = TallyResponse(
            success=True,
            data="<xml>company data</xml>",
            status_code=200,
            response_time=0.1
        )
        self.mock_connector.send_request = AsyncMock(return_value=mock_response)
        
        # Mock XML validation to pass
        with patch.object(self.data_reader, '_validate_xml_response', return_value=True):
            # First request - should hit TallyPrime
            response1 = await self.data_reader._send_data_request(TallyDataType.COMPANY_INFO)
            assert response1.success is True
            assert not hasattr(response1, 'from_cache') or not response1.from_cache
            
            # Second request - should hit cache
            response2 = await self.data_reader._send_data_request(TallyDataType.COMPANY_INFO)
            assert response2.success is True
            assert hasattr(response2, 'from_cache') and response2.from_cache
        
        # Verify connector was called only once
        assert self.mock_connector.send_request.call_count == 1
    
    def test_cache_management_methods(self):
        """Test cache management methods"""
        # Test cache clearing
        self.data_reader.cache.put(TallyDataType.COMPANY_INFO, "test_data")
        assert len(self.data_reader.cache._cache) == 1
        
        self.data_reader.clear_cache()
        assert len(self.data_reader.cache._cache) == 0
        
        # Test cache statistics
        stats = self.data_reader.get_cache_statistics()
        assert 'cache_enabled' in stats
        assert stats['cache_enabled'] is True
        
        # Test cleanup expired cache
        expired_count = self.data_reader.cleanup_expired_cache()
        assert isinstance(expired_count, int)
    
    def test_comprehensive_statistics(self):
        """Test comprehensive statistics collection"""
        # Add some test data to statistics
        self.data_reader.successful_requests = 10
        self.data_reader.failed_requests = 2
        self.data_reader.xml_parse_errors = 1
        self.data_reader.validation_errors = 1
        self.data_reader.malformed_responses = 1
        self.data_reader.total_response_time = 5.0
        
        stats = self.data_reader.get_statistics()
        
        # Check basic statistics
        assert stats['total_requests'] == 12
        assert stats['successful_requests'] == 10
        assert stats['failed_requests'] == 2
        assert stats['success_rate_percent'] == 83.33
        assert stats['xml_parse_errors'] == 1
        assert stats['validation_errors'] == 1
        assert stats['malformed_responses'] == 1
        
        # Check cache statistics are included
        assert 'cache_enabled' in stats


class TestConvenienceFunction:
    """
    Test the convenience function for creating data readers
    """
    
    @patch('core.tally.data_reader.TallyConnector')
    @patch('core.tally.data_reader.TallyConnectionConfig')
    def test_create_data_reader_from_config(self, mock_config_class, mock_connector_class):
        """Test the convenience function for creating data readers"""
        # Mock the configuration and connector
        mock_config = Mock()
        mock_config_class.from_dict.return_value = mock_config
        mock_connector = Mock()
        mock_connector_class.return_value = mock_connector
        
        # Test with default parameters
        config_dict = {
            'host': '172.28.208.1',
            'port': 9000,
            'timeout': 30
        }
        
        reader = create_data_reader_from_config(config_dict)
        
        # Verify configuration was created correctly
        mock_config_class.from_dict.assert_called_once_with(config_dict)
        mock_connector_class.assert_called_once_with(mock_config)
        
        # Verify reader has correct settings
        assert reader.cache_enabled is True
        assert reader.cache.max_size == 100
        
        # Test with custom cache settings
        reader_custom = create_data_reader_from_config(
            config_dict,
            enable_cache=False,
            cache_size=50
        )
        
        assert reader_custom.cache_enabled is False
        assert reader_custom.cache is None


if __name__ == "__main__":
    """
    Run the tests when this file is executed directly
    """
    print("Running TallyDataReader Enhanced Error Handling and Caching Tests...")
    print("=" * 70)
    
    # Run all tests with detailed output
    pytest_args = [
        __file__,
        "-v",  # Verbose output
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "--durations=10"  # Show 10 slowest tests
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ All tests passed successfully!")
        print("🔧 Enhanced error handling and caching functionality verified")
        print("📊 TallyDataReader is ready for production use")
    else:
        print("\n" + "=" * 70)
        print("❌ Some tests failed!")
        print("🔍 Please review the test output above for details")
    
    print("=" * 70)
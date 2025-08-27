#!/usr/bin/env python3
"""
Manual Test for Enhanced TallyDataReader Functionality

This script tests the enhanced error handling and caching functionality
of the TallyDataReader without requiring external testing frameworks.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)  
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

import sys
import os
from pathlib import Path

# Add the tally_gui_app directory to sys.path for imports
current_dir = Path(__file__).parent
tally_gui_app_dir = current_dir.parent.parent
sys.path.insert(0, str(tally_gui_app_dir))

def test_basic_functionality():
    """Test basic enhanced functionality without external dependencies"""
    print("🧪 Testing Enhanced TallyDataReader Functionality")
    print("=" * 60)
    
    try:
        # Test 1: Import all enhanced classes
        print("\n=== Test 1: Import Enhanced Classes ===")
        
        from core.tally.data_reader import (
            TallyDataReader, TallyDataCache, TallyXMLError, 
            TallyDataType, CacheEntry, create_data_reader_from_config
        )
        print("✅ All enhanced classes imported successfully")
        
        # Test 2: Create TallyXMLError
        print("\n=== Test 2: TallyXMLError Functionality ===")
        
        error = TallyXMLError("Test error", "TEST_ERROR", "<xml>content</xml>")
        assert str(error) == "Test error"
        assert error.error_type == "TEST_ERROR" 
        assert error.xml_content == "<xml>content</xml>"
        print("✅ TallyXMLError creation and properties work correctly")
        
        debug_info = error.get_debug_info()
        assert debug_info['error_type'] == "TEST_ERROR"
        assert debug_info['message'] == "Test error"
        print("✅ TallyXMLError debug info extraction works")
        
        # Test 3: Create TallyDataCache
        print("\n=== Test 3: TallyDataCache Functionality ===")
        
        cache = TallyDataCache(max_size=5, default_expiry_seconds=300)
        assert cache.max_size == 5
        assert cache.default_expiry_seconds == 300
        print("✅ TallyDataCache initialization works")
        
        # Test cache operations
        cache.put(TallyDataType.COMPANY_INFO, "test_data")
        cached_data = cache.get(TallyDataType.COMPANY_INFO)
        assert cached_data == "test_data"
        print("✅ Cache put and get operations work")
        
        # Test cache statistics
        stats = cache.get_statistics()
        assert stats['hits'] == 1
        assert stats['cache_size'] == 1
        print(f"✅ Cache statistics work: {stats['hits']} hits, {stats['misses']} misses")
        
        # Test 4: Create mock connector for TallyDataReader
        print("\n=== Test 4: Enhanced TallyDataReader ===")
        
        class MockConnector:
            def __init__(self):
                self.status = type('obj', (object,), {'value': 'connected'})()
                self.config = type('obj', (object,), {'url': 'http://localhost:9000'})()
        
        mock_connector = MockConnector()
        
        # Test reader with cache enabled
        reader = TallyDataReader(mock_connector, enable_cache=True, cache_size=10)
        assert reader.cache_enabled is True
        assert reader.cache is not None
        assert reader.cache.max_size == 10
        print("✅ TallyDataReader with caching initialized")
        
        # Test reader with cache disabled
        reader_no_cache = TallyDataReader(mock_connector, enable_cache=False)
        assert reader_no_cache.cache_enabled is False
        assert reader_no_cache.cache is None
        print("✅ TallyDataReader without caching initialized")
        
        # Test 5: XML Content Cleaning
        print("\n=== Test 5: XML Content Cleaning ===")
        
        # Valid XML
        valid_xml = "  <xml>content</xml>  "
        cleaned = reader._clean_xml_content(valid_xml)
        assert cleaned == "<xml>content</xml>"
        print("✅ Valid XML cleaning works")
        
        # BOM removal
        bom_xml = "\ufeff<xml>content</xml>"
        cleaned = reader._clean_xml_content(bom_xml)
        assert cleaned == "<xml>content</xml>"
        print("✅ BOM removal works")
        
        # Test error conditions
        try:
            reader._clean_xml_content("")
            print("❌ Empty XML should have failed")
            return False
        except TallyXMLError as e:
            assert e.error_type == "EMPTY_CONTENT"
            print("✅ Empty XML correctly rejected")
        
        try:
            reader._clean_xml_content("not xml")
            print("❌ Non-XML should have failed")
            return False
        except TallyXMLError as e:
            assert e.error_type == "INVALID_XML_START"
            print("✅ Non-XML correctly rejected")
        
        # Test 6: Enhanced Statistics
        print("\n=== Test 6: Enhanced Statistics ===")
        
        stats = reader.get_statistics()
        required_keys = [
            'total_requests', 'successful_requests', 'failed_requests',
            'xml_parse_errors', 'validation_errors', 'malformed_responses',
            'cache_enabled'
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"
        
        print("✅ Enhanced statistics include all required fields")
        
        # Test 7: Cache Management Methods
        print("\n=== Test 7: Cache Management ===")
        
        reader.cache.put(TallyDataType.COMPANY_INFO, "test_data_2")
        reader.clear_cache()
        
        cached_data = reader.cache.get(TallyDataType.COMPANY_INFO)
        assert cached_data is None
        print("✅ Cache clearing works")
        
        cache_stats = reader.get_cache_statistics()
        assert cache_stats['cache_enabled'] is True
        print("✅ Cache statistics retrieval works")
        
        # Test 8: Enhanced Parse XML Response
        print("\n=== Test 8: Enhanced XML Parsing ===")
        
        valid_xml = "<ENVELOPE><DATA>content</DATA></ENVELOPE>"
        root = reader.parse_xml_response(valid_xml)
        assert root is not None
        assert root.tag == "ENVELOPE"
        print("✅ Valid XML parsing works")
        
        # Test malformed XML with raise_on_error=False
        malformed_xml = "<malformed>incomplete"
        root = reader.parse_xml_response(malformed_xml, raise_on_error=False)
        assert root is None
        print("✅ Malformed XML handling works (no exception)")
        
        # Test malformed XML with raise_on_error=True
        try:
            reader.parse_xml_response(malformed_xml, raise_on_error=True)
            print("❌ Malformed XML should have raised exception")
            return False
        except TallyXMLError:
            print("✅ Malformed XML correctly raises TallyXMLError")
        
        # Test 9: Error Tracking
        print("\n=== Test 9: Error Tracking ===")
        
        initial_count = len(reader.recent_errors)
        test_error = TallyXMLError("Tracking test", "TRACK_TEST")
        reader._track_error(test_error)
        
        assert len(reader.recent_errors) == initial_count + 1
        print("✅ Error tracking works")
        
        recent_errors = reader.get_recent_errors()
        assert len(recent_errors) > 0
        assert recent_errors[-1]['error_type'] == 'TRACK_TEST'
        print("✅ Recent errors retrieval works")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Enhanced error handling functionality verified")  
        print("✅ Data caching functionality verified")
        print("✅ TallyDataReader enhancements working correctly")
        print("📊 Ready for integration testing")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    
    if success:
        print("\n🔧 Manual test completed successfully!")
        print("   Enhanced TallyDataReader is ready for production use")
        exit(0)
    else:
        print("\n⚠️  Manual test failed!")
        print("   Please review the errors above")
        exit(1)
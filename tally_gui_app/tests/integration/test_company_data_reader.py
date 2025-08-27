#!/usr/bin/env python3
"""
Test Suite for Company Information Reading and Parsing

This test suite validates the company information extraction and parsing
functionality of the TallyDataReader. It includes tests for XML parsing,
data model population, and integration with TallyPrime.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

import sys
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path

# Add the tally_gui_app directory to sys.path for imports
current_dir = Path(__file__).parent
tally_gui_app_dir = current_dir.parent.parent
sys.path.insert(0, str(tally_gui_app_dir))

# Test imports
from core.tally.data_reader import TallyDataReader, create_data_reader_from_config, TallyXMLError
from core.models.company_model import CompanyInfo, CompanyInfoTableModel, create_sample_company_info


class TestCompanyDataReader:
    """
    Test class for company information reading and parsing functionality
    """
    
    def __init__(self):
        """Initialize test environment"""
        # Test configuration for TallyPrime connection
        self.test_config = {
            'host': '172.28.208.1',
            'port': 9000,
            'timeout': 30,
            'retry_count': 2,
            'verbose_logging': True
        }
        
        # Sample XML response for testing parsing
        self.sample_company_xml = """
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Export Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <IMPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>Company Info</REPORTNAME>
                    </REQUESTDESC>
                    <REQUESTDATA>
                        <TALLYMESSAGE vchtype="Company">
                            <COMPANY NAME="Test Company Pvt Ltd" REMOTEID="12345">
                                <NAME>Test Company Pvt Ltd</NAME>
                                <GUID>12345-abcde-67890</GUID>
                                <COMPANYNUMBER>1</COMPANYNUMBER>
                                <ALIAS>Test Co</ALIAS>
                                <ADDRESS1>123 Business Park</ADDRESS1>
                                <ADDRESS2>Technology Hub</ADDRESS2>
                                <ADDRESS3>Sector 5</ADDRESS3>
                                <STATE>Karnataka</STATE>
                                <COUNTRY>India</COUNTRY>
                                <PINCODE>560001</PINCODE>
                                <PHONENUMBER>080-12345678</PHONENUMBER>
                                <MOBILENUMBER>9876543210</MOBILENUMBER>
                                <EMAIL>info@testcompany.com</EMAIL>
                                <WEBSITE>www.testcompany.com</WEBSITE>
                                <STARTINGFROM>20240401</STARTINGFROM>
                                <ENDINGAT>20250331</ENDINGAT>
                                <GSTIN>29ABCDE1234F1Z5</GSTIN>
                                <INCOMETAXNUMBER>ABCDE1234F</INCOMETAXNUMBER>
                                <ISBILLWISEON>Yes</ISBILLWISEON>
                                <ISCOSTCENTRESON>Yes</ISCOSTCENTRESON>
                                <ISMULTICURRENCYON>No</ISMULTICURRENCYON>
                                <BASECURRENCYSYMBOL>₹</BASECURRENCYSYMBOL>
                                <BASECURRENCY>Indian Rupees</BASECURRENCY>
                                <DECIMALPLACES>2</DECIMALPLACES>
                            </COMPANY>
                        </TALLYMESSAGE>
                    </REQUESTDATA>
                </IMPORTDATA>
            </BODY>
        </ENVELOPE>
        """
    
    
    def test_data_reader_initialization(self):
        """Test TallyDataReader initialization and configuration"""
        print("\n=== Testing TallyDataReader Initialization ===")
        
        try:
            # Create data reader from configuration
            reader = create_data_reader_from_config(self.test_config)
            
            # Verify initialization
            assert reader is not None, "Failed to create TallyDataReader"
            assert reader.connector is not None, "TallyConnector not initialized"
            assert len(reader.xml_templates) > 0, "XML templates not loaded"
            
            # Check template availability
            from core.tally.data_reader import TallyDataType
            assert TallyDataType.COMPANY_INFO in reader.xml_templates, "Company info template missing"
            
            # Verify statistics initialization
            stats = reader.get_statistics()
            assert stats['total_requests'] == 0, "Initial request count should be 0"
            assert stats['available_templates'] > 0, "Should have templates available"
            
            print(f"✅ TallyDataReader initialized successfully")
            print(f"   - Available templates: {stats['available_templates']}")
            print(f"   - Connector configured for: {reader.connector.config.url}")
            
            return reader
            
        except Exception as e:
            print(f"❌ Initialization test failed: {e}")
            return None
    
    
    def test_company_xml_parsing(self):
        """Test company XML parsing functionality"""
        print("\n=== Testing Company XML Parsing ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test XML parsing
            company_info = reader.parse_company_info(self.sample_company_xml)
            
            # Verify parsing results
            assert company_info is not None, "Company parsing returned None"
            assert company_info.name == "Test Company Pvt Ltd", f"Expected 'Test Company Pvt Ltd', got '{company_info.name}'"
            assert company_info.alias == "Test Co", f"Expected 'Test Co', got '{company_info.alias}'"
            assert company_info.guid == "12345-abcde-67890", f"GUID mismatch"
            
            # Verify address parsing
            assert company_info.mailing_address.line1 == "123 Business Park", "Address line 1 mismatch"
            assert company_info.mailing_address.state == "Karnataka", "State mismatch"
            assert company_info.mailing_address.postal_code == "560001", "Postal code mismatch"
            assert company_info.mailing_address.phone == "080-12345678", "Phone mismatch"
            assert company_info.mailing_address.email == "info@testcompany.com", "Email mismatch"
            
            # Verify financial year parsing
            assert company_info.current_financial_year.start_date is not None, "Start date not parsed"
            assert company_info.current_financial_year.end_date is not None, "End date not parsed"
            assert company_info.current_financial_year.start_date.year == 2024, "Start year mismatch"
            assert company_info.current_financial_year.start_date.month == 4, "Start month should be April"
            
            # Verify tax information parsing
            assert company_info.tax_info.gstin == "29ABCDE1234F1Z5", "GSTIN mismatch"
            assert company_info.tax_info.pan == "ABCDE1234F", "PAN mismatch"
            
            # Verify features parsing
            assert company_info.features.maintain_bill_wise_details == True, "Bill-wise details should be enabled"
            assert company_info.features.use_cost_centers == True, "Cost centers should be enabled"
            assert company_info.features.use_multi_currency == False, "Multi-currency should be disabled"
            
            # Verify currency information
            assert company_info.base_currency_symbol == "₹", "Currency symbol mismatch"
            assert company_info.base_currency_name == "Indian Rupees", "Currency name mismatch"
            assert company_info.decimal_places == 2, "Decimal places mismatch"
            
            print(f"✅ Company XML parsing successful")
            print(f"   - Company: {company_info.name}")
            print(f"   - Financial Year: {company_info.get_financial_year_label()}")
            print(f"   - Address: {company_info.mailing_address.line1}, {company_info.mailing_address.state}")
            print(f"   - GST: {company_info.tax_info.gstin}")
            print(f"   - Features: {len(company_info.features.get_enabled_features())} enabled")
            
            return company_info
            
        except Exception as e:
            print(f"❌ Company XML parsing test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_company_table_model(self):
        """Test Qt table model for company information display"""
        print("\n=== Testing Company Information Table Model ===")
        
        try:
            # Create sample company info
            company_info = create_sample_company_info()
            
            # Create table model
            table_model = CompanyInfoTableModel(company_info)
            
            # Verify model properties
            assert table_model.rowCount() > 0, "Table model should have rows"
            assert table_model.columnCount() == 2, "Table model should have 2 columns (Property, Value)"
            
            # Test data retrieval
            from PySide6.QtCore import Qt, QModelIndex
            
            # Test header data
            header1 = table_model.headerData(0, Qt.Horizontal, Qt.DisplayRole)
            header2 = table_model.headerData(1, Qt.Horizontal, Qt.DisplayRole)
            assert header1 == "Property", "First column header should be 'Property'"
            assert header2 == "Value", "Second column header should be 'Value'"
            
            # Test data access
            first_row_property = table_model.data(table_model.index(0, 0), Qt.DisplayRole)
            first_row_value = table_model.data(table_model.index(0, 1), Qt.DisplayRole)
            
            assert first_row_property == "Company Name", "First property should be 'Company Name'"
            assert first_row_value == company_info.name, "First value should match company name"
            
            # Test model update
            new_company = create_sample_company_info()
            new_company.name = "Updated Company Name"
            table_model.update_company_info(new_company)
            
            updated_value = table_model.data(table_model.index(0, 1), Qt.DisplayRole)
            assert updated_value == "Updated Company Name", "Model should reflect updated company name"
            
            print(f"✅ Company table model test successful")
            print(f"   - Rows: {table_model.rowCount()}")
            print(f"   - Columns: {table_model.columnCount()}")
            print(f"   - Sample data: {first_row_property} = {first_row_value}")
            
            return table_model
            
        except Exception as e:
            print(f"❌ Company table model test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    async def test_live_company_data_reading(self):
        """Test live company data reading from TallyPrime (if available)"""
        print("\n=== Testing Live Company Data Reading ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test connection first
            connection_result = await reader.connector.test_connection()
            if not connection_result.success:
                print(f"⚠️  TallyPrime not available at {reader.connector.config.url}")
                print(f"   Error: {connection_result.error_message}")
                print("   Skipping live data test...")
                return None
            
            print(f"✅ Connected to TallyPrime at {reader.connector.config.url}")
            
            # Request company information
            response = await reader.get_company_info()
            
            if response.success:
                print(f"✅ Company data request successful")
                print(f"   - Response time: {response.response_time:.3f} seconds")
                print(f"   - Data size: {len(response.data)} bytes")
                
                # Parse the company information
                company_info = reader.parse_company_info(response.data)
                
                if company_info:
                    print(f"✅ Company data parsing successful")
                    print(f"   - Company: {company_info.name}")
                    if company_info.alias:
                        print(f"   - Alias: {company_info.alias}")
                    print(f"   - Financial Year: {company_info.get_financial_year_label()}")
                    
                    if company_info.mailing_address.state:
                        print(f"   - Location: {company_info.mailing_address.state}")
                    
                    if company_info.tax_info.gstin:
                        print(f"   - GSTIN: {company_info.tax_info.gstin}")
                    
                    # Display enabled features
                    enabled_features = company_info.features.get_enabled_features()
                    if enabled_features:
                        print(f"   - Enabled Features: {', '.join(enabled_features[:3])}...")
                    
                    return company_info
                else:
                    print("❌ Company data parsing failed")
                    print("   Raw XML (first 500 chars):")
                    print(response.data[:500])
                    return None
            else:
                print(f"❌ Company data request failed: {response.error_message}")
                return None
                
        except Exception as e:
            print(f"❌ Live company data test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_data_serialization(self):
        """Test company data serialization and deserialization"""
        print("\n=== Testing Company Data Serialization ===")
        
        try:
            # Create sample company info
            original_company = create_sample_company_info()
            
            # Test serialization to dictionary
            company_dict = original_company.to_dict()
            assert isinstance(company_dict, dict), "Serialization should return dictionary"
            assert 'name' in company_dict, "Dictionary should contain name"
            assert 'tax_info' in company_dict, "Dictionary should contain tax_info"
            assert 'current_financial_year' in company_dict, "Dictionary should contain financial year"
            
            # Test deserialization from dictionary
            restored_company = CompanyInfo.from_dict(company_dict)
            assert restored_company.name == original_company.name, "Name should match after deserialization"
            assert restored_company.tax_info.gstin == original_company.tax_info.gstin, "GSTIN should match"
            assert restored_company.features.maintain_bill_wise_details == original_company.features.maintain_bill_wise_details, "Features should match"
            
            # Test JSON serialization
            import json
            json_string = json.dumps(company_dict, indent=2, default=str)
            assert len(json_string) > 100, "JSON string should be substantial"
            
            # Test JSON deserialization
            parsed_dict = json.loads(json_string)
            json_company = CompanyInfo.from_dict(parsed_dict)
            assert json_company.name == original_company.name, "JSON round-trip should preserve data"
            
            print(f"✅ Company data serialization successful")
            print(f"   - Dictionary keys: {len(company_dict)}")
            print(f"   - JSON size: {len(json_string)} characters")
            print(f"   - Round-trip preservation: ✅")
            
            return company_dict
            
        except Exception as e:
            print(f"❌ Data serialization test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_enhanced_error_handling(self):
        """Test enhanced error handling with malformed XML responses"""
        print("\n=== Testing Enhanced Error Handling ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test 1: Empty XML response
            try:
                company_info = reader.parse_company_info("")
                print("❌ Empty XML should have failed")
                return None
            except Exception:
                print("✅ Empty XML correctly rejected")
            
            # Test 2: Malformed XML
            malformed_xml = "<ENVELOPE><UNCLOSED>content"
            try:
                root = reader.parse_xml_response(malformed_xml, raise_on_error=True)
                print("❌ Malformed XML should have failed")
                return None
            except TallyXMLError as e:
                print(f"✅ Malformed XML correctly rejected: {e.error_type}")
                assert e.error_type == "PARSE_ERROR"
            
            # Test 3: HTML response instead of XML
            html_response = "<!DOCTYPE html><html><body>Error 404</body></html>"
            try:
                cleaned = reader._clean_xml_content(html_response)
                print("❌ HTML response should have been rejected")
                return None
            except TallyXMLError as e:
                print(f"✅ HTML response correctly rejected: {e.error_type}")
                assert e.error_type == "HTML_RESPONSE"
            
            # Test 4: JSON response instead of XML
            json_response = '{"error": "Invalid request"}'
            try:
                cleaned = reader._clean_xml_content(json_response)
                print("❌ JSON response should have been rejected")
                return None
            except TallyXMLError as e:
                print(f"✅ JSON response correctly rejected: {e.error_type}")
                assert e.error_type == "JSON_RESPONSE"
            
            # Test 5: XML with TallyPrime errors
            error_xml = """
            <ENVELOPE>
                <ERROR>Connection timeout</ERROR>
                <COMPANY><NAME>Test</NAME></COMPANY>
            </ENVELOPE>
            """
            try:
                from core.tally.data_reader import TallyDataType
                reader._validate_xml_response(error_xml, TallyDataType.COMPANY_INFO)
                print("❌ XML with TallyPrime errors should have failed")
                return None
            except TallyXMLError as e:
                print(f"✅ TallyPrime errors correctly detected: {e.error_type}")
                assert e.error_type == "TALLY_ERROR_RESPONSE"
            
            # Test 6: Error tracking
            initial_error_count = len(reader.recent_errors)
            error = TallyXMLError("Test tracking error", "TEST_ERROR")
            reader._track_error(error)
            
            assert len(reader.recent_errors) == initial_error_count + 1
            print(f"✅ Error tracking working: {len(reader.recent_errors)} errors tracked")
            
            # Test 7: Error statistics
            stats = reader.get_statistics()
            assert 'xml_parse_errors' in stats
            assert 'validation_errors' in stats
            assert 'malformed_responses' in stats
            print(f"✅ Error statistics available in reader stats")
            
            print(f"✅ Enhanced error handling tests completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Enhanced error handling test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_caching_functionality(self):
        """Test data caching functionality and performance"""
        print("\n=== Testing Caching Functionality ===")
        
        try:
            # Create data reader with caching enabled
            reader = create_data_reader_from_config(
                self.test_config, 
                enable_cache=True, 
                cache_size=10
            )
            
            # Verify cache initialization
            assert reader.cache_enabled is True
            assert reader.cache is not None
            assert reader.cache.max_size == 10
            print(f"✅ Cache initialized with size limit: {reader.cache.max_size}")
            
            # Test cache put and get operations
            test_data = self.sample_company_xml
            from core.tally.data_reader import TallyDataType
            
            # Put data in cache
            reader.cache.put(TallyDataType.COMPANY_INFO, test_data)
            cached_data = reader.cache.get(TallyDataType.COMPANY_INFO)
            
            assert cached_data == test_data
            print("✅ Cache put and get operations working")
            
            # Test cache statistics
            cache_stats = reader.get_cache_statistics()
            assert cache_stats['cache_enabled'] is True
            assert cache_stats['cache_size'] == 1
            assert cache_stats['hits'] >= 1
            print(f"✅ Cache statistics: {cache_stats['hits']} hits, {cache_stats['misses']} misses")
            
            # Test cache with different parameters
            reader.cache.put(TallyDataType.LEDGER_DETAILS, "ledger_data", ledger_name="Cash")
            reader.cache.put(TallyDataType.LEDGER_DETAILS, "bank_data", ledger_name="Bank")
            
            cash_data = reader.cache.get(TallyDataType.LEDGER_DETAILS, ledger_name="Cash")
            bank_data = reader.cache.get(TallyDataType.LEDGER_DETAILS, ledger_name="Bank")
            
            assert cash_data == "ledger_data"
            assert bank_data == "bank_data"
            print("✅ Cache working with parameterized requests")
            
            # Test cache clearing
            reader.clear_cache()
            cleared_data = reader.cache.get(TallyDataType.COMPANY_INFO)
            assert cleared_data is None
            print("✅ Cache clearing working correctly")
            
            # Test cache disabled reader
            reader_no_cache = create_data_reader_from_config(
                self.test_config, 
                enable_cache=False
            )
            assert reader_no_cache.cache_enabled is False
            assert reader_no_cache.cache is None
            print("✅ Cache disabled reader working correctly")
            
            # Test comprehensive statistics
            stats = reader.get_statistics()
            assert 'cache_enabled' in stats
            cache_stats = stats
            print(f"✅ Comprehensive statistics include cache metrics")
            
            print(f"✅ Caching functionality tests completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Caching functionality test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    async def test_enhanced_live_data_reading(self):
        """Test enhanced live data reading with caching and error handling"""
        print("\n=== Testing Enhanced Live Data Reading ===")
        
        try:
            # Create data reader with caching
            reader = create_data_reader_from_config(
                self.test_config,
                enable_cache=True,
                cache_size=5
            )
            
            print(f"Connecting to TallyPrime at {reader.connector.config.url}...")
            
            # Test connection first
            is_connected = await reader.connector.test_connection()
            
            if not is_connected.success:
                print(f"⚠️  Cannot connect to TallyPrime: {is_connected.error_message}")
                print("   This is expected if TallyPrime is not running")
                return "connection_failed"
            
            print("✅ Connected to TallyPrime successfully")
            
            # Test 1: First request (should hit TallyPrime)
            response1 = await reader.get_company_info()
            
            if not response1.success:
                print(f"❌ First company info request failed: {response1.error_message}")
                return None
            
            print("✅ First request successful (from TallyPrime)")
            
            # Test 2: Second request (should hit cache if implemented)
            response2 = await reader.get_company_info()
            
            if not response2.success:
                print(f"❌ Second company info request failed: {response2.error_message}")
                return None
            
            # Check if response came from cache
            from_cache = hasattr(response2, 'from_cache') and response2.from_cache
            if from_cache:
                print("✅ Second request served from cache")
            else:
                print("✅ Second request completed (cache may not be implemented in async method)")
            
            # Test 3: Parse the company data
            if response1.data:
                company_info = reader.parse_company_info(response1.data)
                if company_info:
                    print(f"✅ Company parsed: {company_info.name}")
                    print(f"   GUID: {company_info.guid}")
                    print(f"   Financial Year: {company_info.current_financial_year.start_date} to {company_info.current_financial_year.end_date}")
                else:
                    print("⚠️  Company data could not be parsed")
            
            # Test 4: Check statistics
            stats = reader.get_statistics()
            print(f"✅ Statistics: {stats['total_requests']} requests, {stats['successful_requests']} successful")
            print(f"   Success rate: {stats['success_rate_percent']}%")
            print(f"   Average response time: {stats['average_response_time_ms']}ms")
            
            # Test 5: Check cache statistics
            cache_stats = reader.get_cache_statistics()
            if cache_stats.get('cache_enabled'):
                print(f"✅ Cache stats: {cache_stats['hits']} hits, {cache_stats['misses']} misses")
                print(f"   Hit rate: {cache_stats['hit_rate_percent']}%")
            
            print("✅ Enhanced live data reading tests completed successfully")
            return response1
            
        except Exception as e:
            print(f"❌ Enhanced live data reading test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def run_all_tests(self):
        """Run all company data reader tests including enhanced functionality"""
        print("🧪 Running Company Data Reader Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Initialization
        results['initialization'] = self.test_data_reader_initialization() is not None
        
        # Test 2: XML Parsing
        results['xml_parsing'] = self.test_company_xml_parsing() is not None
        
        # Test 3: Table Model
        results['table_model'] = self.test_company_table_model() is not None
        
        # Test 4: Data Serialization
        results['serialization'] = self.test_data_serialization() is not None
        
        # Test 5: Enhanced Error Handling
        results['error_handling'] = self.test_enhanced_error_handling() is not None
        
        # Test 6: Caching Functionality
        results['caching'] = self.test_caching_functionality() is not None
        
        # Test 7: Live Data Reading (async)
        async def run_live_test():
            result = await self.test_live_company_data_reading()
            return result is not None
        
        try:
            results['live_data'] = asyncio.run(run_live_test())
        except Exception as e:
            print(f"Live data test error: {e}")
            results['live_data'] = False
        
        # Test 8: Enhanced Live Data Reading with Caching (async)
        async def run_enhanced_live_test():
            result = await self.test_enhanced_live_data_reading()
            return result is not None and result != "connection_failed"
        
        try:
            results['enhanced_live_data'] = asyncio.run(run_enhanced_live_test())
        except Exception as e:
            print(f"Enhanced live data test error: {e}")
            results['enhanced_live_data'] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        print("-" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Company data reading functionality is working correctly.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the results above.")
        
        return results


def main():
    """Main test runner"""
    # Initialize Qt Application for table model testing
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create and run tests
    test_runner = TestCompanyDataReader()
    results = test_runner.run_all_tests()
    
    # Keep app running briefly to ensure Qt cleanup
    app.processEvents()
    
    return results


if __name__ == "__main__":
    main()
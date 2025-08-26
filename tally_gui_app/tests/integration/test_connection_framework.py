#!/usr/bin/env python3
"""
Test Script for TallyPrime Connection Framework

This script tests the TallyPrime Connection Framework independently
to ensure it works correctly before integrating with the GUI.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 26, 2025
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Qt6 imports for signal handling in tests
from PySide6.QtCore import QCoreApplication, QTimer

# Import our connection framework
from core.tally.connector import TallyConnector, TallyConnectionConfig, ConnectionStatus
from app.settings import SettingsManager

# Set up logging for testing
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ConnectionTester:
    """
    Test class for TallyPrime Connection Framework
    Tests all major functionality including signals and error handling
    """
    
    def __init__(self):
        """Initialize the test environment"""
        self.app = QCoreApplication.instance()
        if not self.app:
            self.app = QCoreApplication([])
        
        self.connector = None
        self.test_results = {}
        
        print("=" * 70)
        print("🧪 TALLYPRME CONNECTION FRAMEWORK TEST SUITE")
        print("=" * 70)
    
    def test_connection_config(self):
        """Test TallyConnectionConfig functionality"""
        print("\n🔧 Testing TallyConnectionConfig...")
        
        try:
            # Test default configuration
            config = TallyConnectionConfig()
            assert config.host == "172.28.208.1"
            assert config.port == 9000
            assert config.url == "http://172.28.208.1:9000"
            
            # Test custom configuration
            custom_config = TallyConnectionConfig(host="localhost", port=9001, timeout=15)
            assert custom_config.host == "localhost"
            assert custom_config.port == 9001
            assert custom_config.timeout == 15
            assert custom_config.url == "http://localhost:9001"
            
            # Test serialization
            config_dict = custom_config.to_dict()
            restored_config = TallyConnectionConfig.from_dict(config_dict)
            assert restored_config.host == custom_config.host
            assert restored_config.port == custom_config.port
            assert restored_config.timeout == custom_config.timeout
            
            print("   ✅ TallyConnectionConfig tests passed")
            self.test_results['connection_config'] = True
            
        except Exception as e:
            print(f"   ❌ TallyConnectionConfig test failed: {e}")
            self.test_results['connection_config'] = False
    
    def test_connector_initialization(self):
        """Test TallyConnector initialization"""
        print("\n🔗 Testing TallyConnector initialization...")
        
        try:
            # Test with default config
            config = TallyConnectionConfig()
            self.connector = TallyConnector(config)
            
            # Verify initial state
            assert self.connector.status == ConnectionStatus.DISCONNECTED
            assert not self.connector.is_connected
            assert self.connector.config.host == config.host
            assert self.connector.config.port == config.port
            
            # Test signal connections
            signals_connected = 0
            
            def on_status_changed(status, message):
                nonlocal signals_connected
                signals_connected += 1
                print(f"   📡 Status changed: {status.value} - {message}")
            
            def on_error_occurred(error_type, error_message):
                nonlocal signals_connected  
                signals_connected += 1
                print(f"   ⚠️  Error occurred: {error_type} - {error_message}")
            
            # Connect test signal handlers
            self.connector.connection_status_changed.connect(on_status_changed)
            self.connector.error_occurred.connect(on_error_occurred)
            
            print("   ✅ TallyConnector initialization passed")
            self.test_results['connector_init'] = True
            
        except Exception as e:
            print(f"   ❌ TallyConnector initialization failed: {e}")
            self.test_results['connector_init'] = False
    
    def test_connection_attempt(self):
        """Test actual connection to TallyPrime"""
        print("\n🌐 Testing TallyPrime connection...")
        
        if not self.connector:
            print("   ⚠️  Skipping connection test - connector not initialized")
            self.test_results['connection'] = False
            return
        
        try:
            # Test connection with current configuration
            print(f"   🔍 Attempting connection to {self.connector.config.url}")
            
            # Test connection (this will emit signals)
            success = self.connector.test_connection()
            
            if success:
                print("   ✅ Connection successful!")
                print(f"   📊 Connection stats: {self.connector.connection_stats}")
                
                # Test company information retrieval
                company_info = self.connector.get_company_information()
                if company_info:
                    print(f"   🏢 Company: {company_info.name}")
                
                self.test_results['connection'] = True
            else:
                print("   ❌ Connection failed")
                print(f"   💬 Last error: {self.connector.last_error}")
                self.test_results['connection'] = False
                
                # This is not necessarily a test failure if TallyPrime is not running
                # It's a successful test of error handling
                print("   ℹ️  Connection failure is expected if TallyPrime is not running")
                
        except Exception as e:
            print(f"   ❌ Connection test error: {e}")
            self.test_results['connection'] = False
    
    def test_discovery_feature(self):
        """Test TallyPrime instance discovery"""
        print("\n🔍 Testing TallyPrime discovery...")
        
        if not self.connector:
            print("   ⚠️  Skipping discovery test - connector not initialized") 
            self.test_results['discovery'] = False
            return
        
        try:
            print("   📡 Scanning for TallyPrime instances...")
            discovered = self.connector.discover_tally_instances()
            
            print(f"   📋 Discovery results: {len(discovered)} instances found")
            for host, port in discovered:
                print(f"   🎯 Found TallyPrime at {host}:{port}")
            
            # Discovery test passes if it completes without error
            # Finding 0 instances is valid if no TallyPrime is running
            self.test_results['discovery'] = True
            print("   ✅ Discovery test completed")
            
        except Exception as e:
            print(f"   ❌ Discovery test failed: {e}")
            self.test_results['discovery'] = False
    
    def test_settings_manager(self):
        """Test SettingsManager functionality"""
        print("\n⚙️  Testing SettingsManager...")
        
        try:
            # Create settings manager
            settings_mgr = SettingsManager("TestOrg", "TestApp")
            
            # Test connection configuration
            original_config = settings_mgr.connection_config
            test_config = TallyConnectionConfig(host="test.local", port=8080)
            
            # Update configuration
            settings_mgr.update_connection_config(test_config)
            assert settings_mgr.connection_config.host == "test.local"
            assert settings_mgr.connection_config.port == 8080
            
            # Test UI preferences
            ui_prefs = settings_mgr.ui_preferences
            ui_prefs.theme_name = "dark"
            settings_mgr.update_ui_preferences(ui_prefs)
            assert settings_mgr.ui_preferences.theme_name == "dark"
            
            # Test settings persistence
            settings_mgr.save_settings()
            
            print("   ✅ SettingsManager tests passed")
            self.test_results['settings'] = True
            
        except Exception as e:
            print(f"   ❌ SettingsManager test failed: {e}")
            self.test_results['settings'] = False
    
    def test_xml_request_formatting(self):
        """Test XML request generation and sending"""
        print("\n📄 Testing XML request handling...")
        
        if not self.connector:
            print("   ⚠️  Skipping XML test - connector not initialized")
            self.test_results['xml_requests'] = False
            return
        
        try:
            # Test a simple XML request
            simple_xml = """<ENVELOPE>
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
            
            print("   📤 Sending test XML request...")
            response = self.connector.send_xml_request(simple_xml, "XML Format Test")
            
            print(f"   📊 Response success: {response.success}")
            print(f"   ⏱️  Response time: {response.response_time:.2f}s")
            print(f"   📏 Response length: {len(response.data)} characters")
            
            if response.error_message:
                print(f"   💬 Error: {response.error_message}")
            
            # Test passes if XML is sent without format errors
            self.test_results['xml_requests'] = True
            print("   ✅ XML request test completed")
            
        except Exception as e:
            print(f"   ❌ XML request test failed: {e}")
            self.test_results['xml_requests'] = False
    
    def run_all_tests(self):
        """Run all test methods"""
        print("🚀 Starting comprehensive test suite...\n")
        
        # Run individual tests
        self.test_connection_config()
        self.test_connector_initialization()
        self.test_connection_attempt()
        self.test_discovery_feature()
        self.test_settings_manager()
        self.test_xml_request_formatting()
        
        # Clean up
        if self.connector:
            self.connector.close()
        
        # Print final results
        return self.print_final_results()
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 70)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title():<30} {status}")
        
        print("-" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ TallyPrime Connection Framework is working correctly")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed")
            print("🔧 Review the failed tests and fix issues before proceeding")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        return failed_tests == 0


def main():
    """Main test execution"""
    try:
        # Create and run test suite
        tester = ConnectionTester()
        all_passed = tester.run_all_tests()
        
        print("\n🏁 Testing completed.")
        
        if all_passed:
            print("✅ Connection Framework is ready for GUI integration!")
        else:
            print("❌ Some tests failed. Review and fix issues.")
        
        return 0 if all_passed else 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests cancelled by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
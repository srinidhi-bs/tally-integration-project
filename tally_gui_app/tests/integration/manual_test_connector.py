#!/usr/bin/env python3
"""
Manual Testing Interface for TallyPrime Connection Framework

This interactive script allows you to manually test and explore the 
TallyPrime connection framework with real-time feedback.

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

# Qt6 imports for signal handling
from PySide6.QtCore import QCoreApplication

# Import our connection framework
from core.tally.connector import TallyConnector, TallyConnectionConfig, ConnectionStatus
from app.settings import SettingsManager

# Set up logging for interactive testing
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class InteractiveTester:
    """
    Interactive manual testing interface for TallyPrime Connection Framework
    """
    
    def __init__(self):
        """Initialize the interactive testing environment"""
        self.app = QCoreApplication.instance()
        if not self.app:
            self.app = QCoreApplication([])
        
        self.connector = None
        self.settings_manager = None
        
        print("=" * 80)
        print("🔧 MANUAL TESTING INTERFACE - TallyPrime Connection Framework")
        print("=" * 80)
        print("This interface allows you to manually test all connection features")
        print("with real-time feedback and detailed information.")
        print()
    
    def setup_signal_monitoring(self):
        """Set up signal monitoring to show real-time events"""
        if not self.connector:
            print("❌ No connector initialized")
            return
        
        def on_status_changed(status, message):
            print(f"🔔 STATUS CHANGE: {status.value.upper()} - {message}")
        
        def on_company_info_received(company_info):
            print(f"🏢 COMPANY INFO: {company_info.name}")
            if company_info.financial_year_from:
                print(f"   📅 Financial Year: {company_info.financial_year_from} to {company_info.financial_year_to}")
            if company_info.base_currency:
                print(f"   💰 Currency: {company_info.base_currency}")
        
        def on_error_occurred(error_type, error_message):
            print(f"⚠️  ERROR: {error_type} - {error_message}")
        
        def on_data_received(operation, data):
            print(f"📊 DATA RECEIVED: {operation}")
            print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Connect all signals for monitoring
        self.connector.connection_status_changed.connect(on_status_changed)
        self.connector.company_info_received.connect(on_company_info_received)
        self.connector.error_occurred.connect(on_error_occurred)
        self.connector.data_received.connect(on_data_received)
        
        print("✅ Signal monitoring activated - you'll see real-time events")
    
    def show_menu(self):
        """Display the main testing menu"""
        print("\n" + "="*50)
        print("🎛️  MANUAL TESTING MENU")
        print("="*50)
        print("1. 🔧 Setup New Connection")
        print("2. 🔍 Test Current Connection") 
        print("3. 🏢 Get Company Information")
        print("4. 📡 Discover TallyPrime Instances")
        print("5. 📊 Show Connection Statistics")
        print("6. ⚙️  Test Settings Manager")
        print("7. 📤 Send Custom XML Request")
        print("8. 🔄 Start Connection Monitoring")
        print("9. 🛑 Stop Connection Monitoring")
        print("10. 📋 Show Current Configuration")
        print("11. 🧪 Test Different Configurations")
        print("12. 💾 Test Settings Backup/Restore")
        print("0. ❌ Exit")
        print("="*50)
    
    def setup_connection(self):
        """Setup a new TallyPrime connection"""
        print("\n🔧 SETTING UP NEW CONNECTION")
        print("-" * 40)
        
        # Get configuration from user
        default_config = TallyConnectionConfig()
        
        print(f"Current defaults:")
        print(f"  Host: {default_config.host}")
        print(f"  Port: {default_config.port}")
        print(f"  Timeout: {default_config.timeout}s")
        print()
        
        use_defaults = input("Use default configuration? (y/n): ").lower().strip()
        
        if use_defaults == 'y':
            config = default_config
        else:
            host = input(f"Enter host [{default_config.host}]: ").strip() or default_config.host
            port = input(f"Enter port [{default_config.port}]: ").strip() or str(default_config.port)
            timeout = input(f"Enter timeout [{default_config.timeout}]: ").strip() or str(default_config.timeout)
            
            try:
                config = TallyConnectionConfig(
                    host=host,
                    port=int(port),
                    timeout=int(timeout)
                )
            except ValueError as e:
                print(f"❌ Invalid input: {e}")
                return
        
        # Create connector
        if self.connector:
            self.connector.close()
        
        print(f"\n🔗 Creating connector for {config.url}")
        self.connector = TallyConnector(config)
        self.setup_signal_monitoring()
        
        print("✅ Connector created successfully!")
        print(f"📍 Target: {config.url}")
        print(f"⏱️  Timeout: {config.timeout}s")
        print(f"🔄 Retry count: {config.retry_count}")
    
    def test_connection(self):
        """Test the current connection"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n🔍 TESTING CONNECTION")
        print("-" * 40)
        print(f"Target: {self.connector.config.url}")
        print("Testing connection... (watch for real-time status changes)")
        
        start_time = time.time()
        success = self.connector.test_connection()
        end_time = time.time()
        
        print(f"\n📊 Test Results:")
        print(f"  Success: {'✅ YES' if success else '❌ NO'}")
        print(f"  Duration: {end_time - start_time:.2f}s")
        print(f"  Final Status: {self.connector.status.value.upper()}")
        
        if success:
            print(f"  Company: {self.connector.company_info.name if self.connector.company_info else 'Unknown'}")
        else:
            print(f"  Error: {self.connector.last_error}")
    
    def get_company_info(self):
        """Get detailed company information"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n🏢 GETTING COMPANY INFORMATION")
        print("-" * 40)
        
        company_info = self.connector.get_company_information()
        
        if company_info:
            print("✅ Company information retrieved:")
            print(f"  📝 Name: {company_info.name}")
            print(f"  🆔 GUID: {company_info.guid or 'Not available'}")
            print(f"  📅 Financial Year: {company_info.financial_year_from or 'Not available'} to {company_info.financial_year_to or 'Not available'}")
            print(f"  💰 Base Currency: {company_info.base_currency or 'Not available'}")
            print(f"  📚 Books From: {company_info.books_from or 'Not available'}")
        else:
            print("❌ Failed to retrieve company information")
            print(f"Error: {self.connector.last_error}")
    
    def discover_instances(self):
        """Discover TallyPrime instances"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n📡 DISCOVERING TALLYPRME INSTANCES")
        print("-" * 40)
        print("Scanning network for TallyPrime instances...")
        print("(This may take a few seconds)")
        
        start_time = time.time()
        instances = self.connector.discover_tally_instances()
        end_time = time.time()
        
        print(f"\n📊 Discovery Results:")
        print(f"  Scan Duration: {end_time - start_time:.1f}s")
        print(f"  Instances Found: {len(instances)}")
        
        if instances:
            print("\n🎯 Discovered TallyPrime Instances:")
            for i, (host, port) in enumerate(instances, 1):
                print(f"  {i}. {host}:{port}")
                
                # Option to test each discovered instance
                test = input(f"     Test connection to {host}:{port}? (y/n): ").lower().strip()
                if test == 'y':
                    test_config = TallyConnectionConfig(host=host, port=port)
                    test_connector = TallyConnector(test_config)
                    success = test_connector.test_connection()
                    status = "✅ Working" if success else "❌ Failed"
                    print(f"     Result: {status}")
                    if success and test_connector.company_info:
                        print(f"     Company: {test_connector.company_info.name}")
                    test_connector.close()
        else:
            print("❌ No TallyPrime instances found")
            print("💡 Make sure TallyPrime is running and HTTP-XML Gateway is enabled")
    
    def show_statistics(self):
        """Show connection statistics"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n📊 CONNECTION STATISTICS")
        print("-" * 40)
        
        stats = self.connector.connection_stats
        
        print(f"📍 Target URL: {stats['url']}")
        print(f"🔄 Total Requests: {stats['total_requests']}")
        print(f"✅ Successful Requests: {stats['successful_requests']}")
        print(f"📈 Success Rate: {stats['success_rate']:.1f}%")
        print(f"⏱️  Last Response Time: {stats['last_response_time']:.3f}s")
        print(f"🔗 Current Status: {stats['current_status'].upper()}")
        
        # Calculate some additional metrics
        if stats['total_requests'] > 0:
            failed_requests = stats['total_requests'] - stats['successful_requests']
            print(f"❌ Failed Requests: {failed_requests}")
            
            if stats['last_response_time'] > 0:
                if stats['last_response_time'] < 0.1:
                    performance = "🚀 Excellent"
                elif stats['last_response_time'] < 0.5:
                    performance = "⚡ Good"
                elif stats['last_response_time'] < 1.0:
                    performance = "👍 Fair"
                else:
                    performance = "🐌 Slow"
                print(f"🎯 Performance: {performance}")
    
    def test_settings_manager(self):
        """Test the settings manager functionality"""
        print("\n⚙️  TESTING SETTINGS MANAGER")
        print("-" * 40)
        
        if not self.settings_manager:
            print("Creating settings manager...")
            self.settings_manager = SettingsManager("TestManual", "TallyTest")
        
        # Show current settings
        print("📋 Current Settings:")
        current_config = self.settings_manager.connection_config
        print(f"  Connection: {current_config.host}:{current_config.port}")
        print(f"  Timeout: {current_config.timeout}s")
        
        ui_prefs = self.settings_manager.ui_preferences
        print(f"  Theme: {ui_prefs.theme_name}")
        print(f"  Font: {ui_prefs.font_family} {ui_prefs.font_size}pt")
        
        # Test updating settings
        test_update = input("\nTest settings update? (y/n): ").lower().strip()
        if test_update == 'y':
            # Update connection config
            new_config = TallyConnectionConfig(
                host="test.example.com",
                port=8888,
                timeout=60
            )
            
            print("Updating connection configuration...")
            self.settings_manager.update_connection_config(new_config)
            print("✅ Settings updated and saved")
            
            # Show history
            history = self.settings_manager.get_connection_history()
            print(f"\n📚 Connection History ({len(history)} entries):")
            for i, config in enumerate(history[:5], 1):
                print(f"  {i}. {config.host}:{config.port}")
    
    def send_custom_xml(self):
        """Send a custom XML request"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n📤 SEND CUSTOM XML REQUEST")
        print("-" * 40)
        
        print("Choose a predefined XML request:")
        print("1. List of Ledgers")
        print("2. List of Groups") 
        print("3. Company Information")
        print("4. Balance Sheet")
        print("5. Custom XML (enter your own)")
        
        choice = input("Enter choice (1-5): ").strip()
        
        xml_requests = {
            "1": {
                "name": "List of Ledgers",
                "xml": """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:ASCII</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
            },
            "2": {
                "name": "List of Groups",
                "xml": """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Groups</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:ASCII</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
            },
            "3": {
                "name": "Company Information", 
                "xml": """<ENVELOPE>
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
            },
            "4": {
                "name": "Balance Sheet",
                "xml": """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Balance Sheet</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:ASCII</SVEXPORTFORMAT>
          <SVFROMDATE>1-Apr-2024</SVFROMDATE>
          <SVTODATE>31-Mar-2025</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
            }
        }
        
        if choice in xml_requests:
            request_info = xml_requests[choice]
            print(f"\nSending: {request_info['name']}")
            xml_request = request_info['xml']
        elif choice == "5":
            print("\nEnter your custom XML (end with empty line):")
            xml_lines = []
            while True:
                line = input()
                if not line:
                    break
                xml_lines.append(line)
            xml_request = "\n".join(xml_lines)
            request_info = {"name": "Custom XML"}
        else:
            print("Invalid choice")
            return
        
        print(f"\n📤 Sending XML request...")
        print(f"Request name: {request_info['name']}")
        print(f"XML length: {len(xml_request)} characters")
        
        start_time = time.time()
        response = self.connector.send_xml_request(xml_request, request_info['name'])
        end_time = time.time()
        
        print(f"\n📊 Response Results:")
        print(f"  Success: {'✅ YES' if response.success else '❌ NO'}")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Time: {end_time - start_time:.3f}s")
        print(f"  Content Type: {response.content_type or 'Not specified'}")
        print(f"  Data Length: {len(response.data)} characters")
        
        if response.error_message:
            print(f"  Error: {response.error_message}")
        
        # Option to view response data
        if response.success and response.data:
            view_data = input("\nView response data? (y/n): ").lower().strip()
            if view_data == 'y':
                print(f"\n📄 Response Data:")
                print("-" * 60)
                # Show first 1000 characters
                preview = response.data[:1000]
                print(preview)
                if len(response.data) > 1000:
                    print(f"\n... (showing first 1000 of {len(response.data)} characters)")
                    
                    show_all = input("Show full response? (y/n): ").lower().strip()
                    if show_all == 'y':
                        print("\n" + "="*60)
                        print("FULL RESPONSE:")
                        print("="*60)
                        print(response.data)
    
    def start_monitoring(self):
        """Start connection monitoring"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n🔄 STARTING CONNECTION MONITORING")
        print("-" * 40)
        
        interval = input("Enter monitoring interval in seconds [30]: ").strip() or "30"
        try:
            interval_sec = int(interval)
            interval_ms = interval_sec * 1000
            
            self.connector.start_connection_monitoring(interval_ms)
            print(f"✅ Connection monitoring started")
            print(f"⏱️  Interval: {interval_sec} seconds")
            print("🔔 You'll see automatic status updates")
        except ValueError:
            print("❌ Invalid interval value")
    
    def stop_monitoring(self):
        """Stop connection monitoring"""
        if not self.connector:
            print("❌ No connector initialized.")
            return
        
        print("\n🛑 STOPPING CONNECTION MONITORING")
        print("-" * 40)
        
        self.connector.stop_connection_monitoring()
        print("✅ Connection monitoring stopped")
    
    def show_configuration(self):
        """Show current configuration details"""
        if not self.connector:
            print("❌ No connector initialized. Use option 1 first.")
            return
        
        print("\n📋 CURRENT CONFIGURATION")
        print("-" * 40)
        
        config = self.connector.config
        print(f"🌐 Host: {config.host}")
        print(f"🔌 Port: {config.port}")
        print(f"🔗 Full URL: {config.url}")
        print(f"⏱️  Timeout: {config.timeout} seconds")
        print(f"🔄 Retry Count: {config.retry_count}")
        print(f"⏳ Retry Delay: {config.retry_delay} seconds")
        print(f"🏷️  User Agent: {config.user_agent}")
        
        print(f"\n📊 Current State:")
        print(f"🔗 Status: {self.connector.status.value.upper()}")
        print(f"🏢 Company: {self.connector.company_info.name if self.connector.company_info else 'Not connected'}")
        print(f"⚠️  Last Error: {self.connector.last_error or 'None'}")
    
    def test_different_configs(self):
        """Test different connection configurations"""
        print("\n🧪 TESTING DIFFERENT CONFIGURATIONS")
        print("-" * 40)
        
        # Test configurations to try
        test_configs = [
            {"name": "Default", "host": "172.28.208.1", "port": 9000},
            {"name": "Alternative Port", "host": "172.28.208.1", "port": 9999},
            {"name": "Localhost", "host": "localhost", "port": 9000},
            {"name": "Local IP", "host": "127.0.0.1", "port": 9000},
        ]
        
        print("Available test configurations:")
        for i, config in enumerate(test_configs, 1):
            print(f"  {i}. {config['name']}: {config['host']}:{config['port']}")
        
        choice = input("Enter configuration number to test (1-4): ").strip()
        
        try:
            config_index = int(choice) - 1
            if 0 <= config_index < len(test_configs):
                test_config_data = test_configs[config_index]
                
                print(f"\n🧪 Testing: {test_config_data['name']}")
                print(f"Target: {test_config_data['host']}:{test_config_data['port']}")
                
                # Create temporary connector for testing
                test_config = TallyConnectionConfig(
                    host=test_config_data['host'],
                    port=test_config_data['port']
                )
                
                test_connector = TallyConnector(test_config)
                
                # Test connection
                start_time = time.time()
                success = test_connector.test_connection()
                end_time = time.time()
                
                print(f"📊 Results:")
                print(f"  Success: {'✅ YES' if success else '❌ NO'}")
                print(f"  Duration: {end_time - start_time:.2f}s")
                
                if success:
                    if test_connector.company_info:
                        print(f"  Company: {test_connector.company_info.name}")
                    print(f"  Stats: {test_connector.connection_stats}")
                else:
                    print(f"  Error: {test_connector.last_error}")
                
                # Option to switch to this configuration
                if success:
                    switch = input("Switch to this configuration? (y/n): ").lower().strip()
                    if switch == 'y':
                        if self.connector:
                            self.connector.close()
                        self.connector = test_connector
                        self.setup_signal_monitoring()
                        print("✅ Switched to new configuration")
                        return
                
                test_connector.close()
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Invalid input")
    
    def test_backup_restore(self):
        """Test settings backup and restore functionality"""
        print("\n💾 TESTING SETTINGS BACKUP/RESTORE")
        print("-" * 40)
        
        if not self.settings_manager:
            self.settings_manager = SettingsManager("TestManual", "TallyTest")
        
        print("📋 Current Settings:")
        config = self.settings_manager.connection_config
        print(f"  Connection: {config.host}:{config.port}")
        
        # Create backup
        print("\n💾 Creating backup...")
        backup_path = self.settings_manager.create_backup("manual_test_backup")
        print(f"✅ Backup created: {backup_path}")
        
        # Modify settings
        print("\n🔧 Modifying settings...")
        new_config = TallyConnectionConfig(host="backup.test.com", port=7777)
        self.settings_manager.update_connection_config(new_config)
        print(f"✅ Settings modified: {new_config.host}:{new_config.port}")
        
        # Show modified settings
        modified_config = self.settings_manager.connection_config
        print(f"📋 Modified Settings: {modified_config.host}:{modified_config.port}")
        
        # Restore from backup
        restore = input("\nRestore from backup? (y/n): ").lower().strip()
        if restore == 'y':
            print("🔄 Restoring from backup...")
            success = self.settings_manager.restore_backup(backup_path)
            
            if success:
                print("✅ Settings restored successfully")
                restored_config = self.settings_manager.connection_config
                print(f"📋 Restored Settings: {restored_config.host}:{restored_config.port}")
            else:
                print("❌ Restore failed")
    
    def run_interactive_session(self):
        """Run the main interactive testing session"""
        try:
            while True:
                self.show_menu()
                choice = input("\nEnter your choice (0-12): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    self.setup_connection()
                elif choice == "2":
                    self.test_connection()
                elif choice == "3":
                    self.get_company_info()
                elif choice == "4":
                    self.discover_instances()
                elif choice == "5":
                    self.show_statistics()
                elif choice == "6":
                    self.test_settings_manager()
                elif choice == "7":
                    self.send_custom_xml()
                elif choice == "8":
                    self.start_monitoring()
                elif choice == "9":
                    self.stop_monitoring()
                elif choice == "10":
                    self.show_configuration()
                elif choice == "11":
                    self.test_different_configs()
                elif choice == "12":
                    self.test_backup_restore()
                else:
                    print("❌ Invalid choice. Please try again.")
                
                # Wait for user to read output
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n⏹️  Testing session cancelled by user")
        
        finally:
            # Clean up
            if self.connector:
                self.connector.close()
            print("\n👋 Thank you for testing! Goodbye.")


def main():
    """Main function for interactive testing"""
    print("🚀 Starting Interactive Manual Testing Session")
    print("=" * 80)
    
    tester = InteractiveTester()
    tester.run_interactive_session()


if __name__ == "__main__":
    main()
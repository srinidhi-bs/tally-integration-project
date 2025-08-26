#!/usr/bin/env python3
"""
Demo Script for Manual Testing Features

This script demonstrates the manual testing capabilities without requiring
interactive input, so you can see the functionality in action.

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

# Set up logging for demo
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class DemoTester:
    """
    Demonstrates manual testing features in action
    """
    
    def __init__(self):
        """Initialize the demo environment"""
        self.app = QCoreApplication.instance()
        if not self.app:
            self.app = QCoreApplication([])
        
        self.connector = None
        self.settings_manager = None
        
        print("=" * 80)
        print("🎬 DEMO: Manual Testing Features in Action")
        print("=" * 80)
        print("This demo shows you all the manual testing capabilities")
        print("that you can use interactively with the manual_test_connector.py script")
        print()
    
    def setup_signal_monitoring(self):
        """Set up signal monitoring to show real-time events"""
        def on_status_changed(status, message):
            print(f"🔔 SIGNAL - STATUS CHANGE: {status.value.upper()} - {message}")
        
        def on_company_info_received(company_info):
            print(f"🔔 SIGNAL - COMPANY INFO: {company_info.name}")
        
        def on_error_occurred(error_type, error_message):
            print(f"🔔 SIGNAL - ERROR: {error_type} - {error_message}")
        
        # Connect all signals for monitoring
        self.connector.connection_status_changed.connect(on_status_changed)
        self.connector.company_info_received.connect(on_company_info_received)
        self.connector.error_occurred.connect(on_error_occurred)
        
        print("✅ Real-time signal monitoring activated")
    
    def demo_connection_setup(self):
        """Demo: Setting up a connection"""
        print("\n" + "="*60)
        print("🎬 DEMO 1: Setting Up Connection")
        print("="*60)
        
        # Create configuration
        config = TallyConnectionConfig(
            host="172.28.208.1",
            port=9000,
            timeout=30
        )
        
        print(f"📋 Creating connection configuration:")
        print(f"  🌐 Host: {config.host}")
        print(f"  🔌 Port: {config.port}")
        print(f"  ⏱️  Timeout: {config.timeout}s")
        print(f"  🔗 URL: {config.url}")
        
        # Create connector
        print(f"\n🔗 Creating TallyConnector...")
        self.connector = TallyConnector(config)
        self.setup_signal_monitoring()
        
        print("✅ Connection setup complete!")
        print("   (In manual testing, you can enter custom host/port values)")
    
    def demo_connection_test(self):
        """Demo: Testing connection"""
        print("\n" + "="*60)
        print("🎬 DEMO 2: Testing Connection")
        print("="*60)
        
        if not self.connector:
            print("❌ No connector available")
            return
        
        print("🔍 Testing connection to TallyPrime...")
        print("   (Watch for real-time signal emissions)")
        
        start_time = time.time()
        success = self.connector.test_connection()
        end_time = time.time()
        
        print(f"\n📊 Connection Test Results:")
        print(f"  ✅ Success: {success}")
        print(f"  ⏱️  Duration: {end_time - start_time:.2f}s")
        print(f"  🔗 Final Status: {self.connector.status.value.upper()}")
        
        if success and self.connector.company_info:
            print(f"  🏢 Company: {self.connector.company_info.name}")
    
    def demo_company_information(self):
        """Demo: Getting company information"""
        print("\n" + "="*60)
        print("🎬 DEMO 3: Getting Company Information")
        print("="*60)
        
        if not self.connector:
            print("❌ No connector available")
            return
        
        print("🏢 Retrieving detailed company information...")
        company_info = self.connector.get_company_information()
        
        if company_info:
            print("✅ Company information retrieved:")
            print(f"  📝 Name: {company_info.name}")
            print(f"  🆔 GUID: {company_info.guid or 'Not available'}")
            print(f"  📅 Financial Year: {company_info.financial_year_from or 'N/A'} to {company_info.financial_year_to or 'N/A'}")
            print(f"  💰 Base Currency: {company_info.base_currency or 'Not available'}")
        else:
            print("❌ Could not retrieve company information")
    
    def demo_discovery(self):
        """Demo: Discovering TallyPrime instances"""
        print("\n" + "="*60)
        print("🎬 DEMO 4: TallyPrime Instance Discovery")
        print("="*60)
        
        if not self.connector:
            print("❌ No connector available")
            return
        
        print("📡 Scanning for TallyPrime instances...")
        print("   (This scans multiple ports and hosts)")
        
        start_time = time.time()
        instances = self.connector.discover_tally_instances()
        end_time = time.time()
        
        print(f"\n📊 Discovery Results:")
        print(f"  ⏱️  Scan Duration: {end_time - start_time:.1f}s")
        print(f"  🎯 Instances Found: {len(instances)}")
        
        if instances:
            print(f"\n🔍 Discovered Instances:")
            for i, (host, port) in enumerate(instances, 1):
                print(f"  {i}. {host}:{port}")
        else:
            print("   (No instances found - TallyPrime might not be running)")
    
    def demo_statistics(self):
        """Demo: Connection statistics"""
        print("\n" + "="*60)
        print("🎬 DEMO 5: Connection Statistics")
        print("="*60)
        
        if not self.connector:
            print("❌ No connector available")
            return
        
        stats = self.connector.connection_stats
        
        print("📊 Live Connection Statistics:")
        print(f"  📍 Target URL: {stats['url']}")
        print(f"  🔄 Total Requests: {stats['total_requests']}")
        print(f"  ✅ Successful Requests: {stats['successful_requests']}")
        print(f"  📈 Success Rate: {stats['success_rate']:.1f}%")
        print(f"  ⏱️  Last Response Time: {stats['last_response_time']:.3f}s")
        print(f"  🔗 Current Status: {stats['current_status'].upper()}")
        
        # Performance assessment
        if stats['last_response_time'] > 0:
            if stats['last_response_time'] < 0.1:
                performance = "🚀 Excellent"
            elif stats['last_response_time'] < 0.5:
                performance = "⚡ Good"
            else:
                performance = "👍 Fair"
            print(f"  🎯 Performance: {performance}")
    
    def demo_custom_xml(self):
        """Demo: Sending custom XML requests"""
        print("\n" + "="*60)
        print("🎬 DEMO 6: Custom XML Request")
        print("="*60)
        
        if not self.connector:
            print("❌ No connector available")
            return
        
        # Example: Get ledger list
        xml_request = """<ENVELOPE>
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
        
        print("📤 Sending XML request for 'List of Accounts'")
        print(f"   XML length: {len(xml_request)} characters")
        
        start_time = time.time()
        response = self.connector.send_xml_request(xml_request, "Demo Ledger List")
        end_time = time.time()
        
        print(f"\n📊 XML Response Results:")
        print(f"  ✅ Success: {response.success}")
        print(f"  📊 Status Code: {response.status_code}")
        print(f"  ⏱️  Response Time: {end_time - start_time:.3f}s")
        print(f"  📏 Data Length: {len(response.data)} characters")
        
        if response.success and response.data:
            # Show preview of response
            preview = response.data[:200] + "..." if len(response.data) > 200 else response.data
            print(f"\n📄 Response Preview:")
            print(f"   {preview}")
            print(f"   (In manual testing, you can view full responses)")
    
    def demo_settings_manager(self):
        """Demo: Settings manager functionality"""
        print("\n" + "="*60)
        print("🎬 DEMO 7: Settings Manager")
        print("="*60)
        
        print("⚙️ Creating settings manager...")
        self.settings_manager = SettingsManager("DemoOrg", "DemoTally")
        
        # Show current settings
        print("\n📋 Current Settings:")
        config = self.settings_manager.connection_config
        print(f"  🔗 Connection: {config.host}:{config.port}")
        print(f"  ⏱️  Timeout: {config.timeout}s")
        
        ui_prefs = self.settings_manager.ui_preferences
        print(f"  🎨 Theme: {ui_prefs.theme_name}")
        print(f"  📝 Font: {ui_prefs.font_family} {ui_prefs.font_size}pt")
        
        # Test updating settings
        print("\n🔧 Updating connection configuration...")
        new_config = TallyConnectionConfig(
            host="demo.example.com",
            port=8080,
            timeout=45
        )
        
        self.settings_manager.update_connection_config(new_config)
        print("✅ Settings updated and persisted")
        
        # Show connection history
        history = self.settings_manager.get_connection_history()
        print(f"\n📚 Connection History ({len(history)} entries):")
        for i, config in enumerate(history[:3], 1):
            print(f"  {i}. {config.host}:{config.port}")
    
    def demo_backup_restore(self):
        """Demo: Settings backup and restore"""
        print("\n" + "="*60)
        print("🎬 DEMO 8: Settings Backup & Restore")
        print("="*60)
        
        if not self.settings_manager:
            self.settings_manager = SettingsManager("DemoOrg", "DemoTally")
        
        print("💾 Creating settings backup...")
        backup_path = self.settings_manager.create_backup("demo_backup")
        print(f"✅ Backup created at: {backup_path}")
        
        # Show backup file exists
        if backup_path.exists():
            backup_size = backup_path.stat().st_size
            print(f"📁 Backup file size: {backup_size} bytes")
            
            print("\n🔄 Testing restore functionality...")
            restore_success = self.settings_manager.restore_backup(backup_path)
            print(f"✅ Restore test: {'Success' if restore_success else 'Failed'}")
    
    def demo_monitoring(self):
        """Demo: Connection monitoring"""
        print("\n" + "="*60)
        print("🎬 DEMO 9: Connection Monitoring")
        print("="*60)
        
        if not self.connector:
            print("❌ No connector available")
            return
        
        print("🔄 Starting connection monitoring...")
        print("   (In real usage, this runs in background)")
        
        # Start monitoring with short interval for demo
        self.connector.start_connection_monitoring(5000)  # 5 seconds
        print("✅ Monitoring started with 5-second intervals")
        
        # Show monitoring for a few seconds
        print("⏳ Monitoring active... (demo for 3 seconds)")
        time.sleep(3)
        
        print("🛑 Stopping monitoring...")
        self.connector.stop_connection_monitoring()
        print("✅ Monitoring stopped")
    
    def demo_configuration_testing(self):
        """Demo: Testing different configurations"""
        print("\n" + "="*60)
        print("🎬 DEMO 10: Configuration Testing")
        print("="*60)
        
        # Test different configurations
        test_configs = [
            {"name": "Primary", "host": "172.28.208.1", "port": 9000},
            {"name": "Alternative", "host": "172.28.208.1", "port": 9999},
            {"name": "Localhost", "host": "localhost", "port": 9000}
        ]
        
        print("🧪 Testing multiple configurations:")
        
        for config_data in test_configs:
            print(f"\n  🔧 Testing: {config_data['name']}")
            print(f"     Target: {config_data['host']}:{config_data['port']}")
            
            # Create test connector
            test_config = TallyConnectionConfig(
                host=config_data['host'],
                port=config_data['port'],
                timeout=10  # Shorter timeout for demo
            )
            
            test_connector = TallyConnector(test_config)
            
            # Quick test
            start_time = time.time()
            success = test_connector.test_connection()
            end_time = time.time()
            
            status = "✅ Working" if success else "❌ Failed"
            print(f"     Result: {status} ({end_time - start_time:.2f}s)")
            
            if success and test_connector.company_info:
                print(f"     Company: {test_connector.company_info.name}")
            
            test_connector.close()
    
    def run_all_demos(self):
        """Run all demonstration features"""
        print("🚀 Starting comprehensive demo of manual testing features...\n")
        
        try:
            # Run all demos in sequence
            self.demo_connection_setup()
            time.sleep(1)  # Brief pause between demos
            
            self.demo_connection_test()
            time.sleep(1)
            
            self.demo_company_information()
            time.sleep(1)
            
            self.demo_discovery()
            time.sleep(1)
            
            self.demo_statistics()
            time.sleep(1)
            
            self.demo_custom_xml()
            time.sleep(1)
            
            self.demo_settings_manager()
            time.sleep(1)
            
            self.demo_backup_restore()
            time.sleep(1)
            
            self.demo_monitoring()
            time.sleep(1)
            
            self.demo_configuration_testing()
            
            # Final summary
            print("\n" + "="*80)
            print("🎉 DEMO COMPLETE - Manual Testing Features Summary")
            print("="*80)
            print("✅ All manual testing features demonstrated successfully!")
            print()
            print("🔧 To use these features interactively:")
            print("   Run: python3 manual_test_connector.py")
            print("   (Use in a proper terminal with keyboard input)")
            print()
            print("📋 Available manual testing features:")
            print("   • Interactive connection setup with custom configurations")
            print("   • Real-time connection testing with signal monitoring")
            print("   • Live company information retrieval")
            print("   • Network discovery of TallyPrime instances")
            print("   • Performance statistics and monitoring")
            print("   • Custom XML request testing")
            print("   • Settings management and persistence")
            print("   • Backup/restore functionality")
            print("   • Multi-configuration testing")
            print("   • Live connection monitoring")
            print()
            print("🎯 Key Benefits of Manual Testing:")
            print("   • Verify real TallyPrime integration")
            print("   • Test error handling scenarios")
            print("   • Understand performance characteristics")
            print("   • Validate signal-slot communication")
            print("   • Explore configuration options")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
            
        finally:
            # Clean up
            if self.connector:
                self.connector.close()
                print("\n🧹 Demo cleanup completed")


def main():
    """Main function for demo"""
    print("🎬 Starting Manual Testing Features Demo")
    print("=" * 80)
    
    demo = DemoTester()
    demo.run_all_demos()


if __name__ == "__main__":
    main()
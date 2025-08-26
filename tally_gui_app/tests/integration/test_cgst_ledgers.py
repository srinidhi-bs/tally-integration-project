#!/usr/bin/env python3
"""
Test Script: Retrieve Ledgers Containing "CGST"

This script demonstrates searching for specific ledgers in TallyPrime
and shows how to parse and filter the response data.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 26, 2025
"""

import sys
import re
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Qt6 imports
from PySide6.QtCore import QCoreApplication

# Import our connection framework
from core.tally.connector import TallyConnector, TallyConnectionConfig, ConnectionStatus

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CGSTLedgerSearcher:
    """
    Search for ledgers containing "CGST" in TallyPrime
    """
    
    def __init__(self):
        """Initialize the searcher"""
        self.app = QCoreApplication.instance()
        if not self.app:
            self.app = QCoreApplication([])
        
        # Create connector with your TallyPrime configuration
        config = TallyConnectionConfig(
            host="172.28.208.1",
            port=9000,
            timeout=30
        )
        
        self.connector = TallyConnector(config)
        
        print("=" * 80)
        print("🔍 CGST LEDGER SEARCH TEST")
        print("=" * 80)
        print(f"Target: {config.url}")
        print("Searching for all ledgers containing 'CGST'...")
        print()
    
    def setup_signal_monitoring(self):
        """Set up signal monitoring"""
        def on_status_changed(status, message):
            print(f"🔔 STATUS: {status.value.upper()} - {message}")
        
        def on_error_occurred(error_type, error_message):
            print(f"🔔 ERROR: {error_type} - {error_message}")
        
        self.connector.connection_status_changed.connect(on_status_changed)
        self.connector.error_occurred.connect(on_error_occurred)
    
    def test_connection(self):
        """Test connection before searching"""
        print("🔧 STEP 1: Testing Connection")
        print("-" * 50)
        
        success = self.connector.test_connection()
        
        if success:
            print("✅ Connection successful!")
            if self.connector.company_info:
                print(f"🏢 Company: {self.connector.company_info.name}")
            print()
            return True
        else:
            print(f"❌ Connection failed: {self.connector.last_error}")
            return False
    
    def get_all_ledgers_raw(self):
        """Get all ledgers using ASCII format for easy parsing"""
        print("🔧 STEP 2: Retrieving All Ledgers")
        print("-" * 50)
        
        # XML request to get all ledgers in ASCII format
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
        
        print("📤 Sending request for 'List of Accounts'...")
        response = self.connector.send_xml_request(xml_request, "Get All Ledgers")
        
        if response.success:
            print(f"✅ Response received!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"⏱️  Response Time: {response.response_time:.3f}s")
            print(f"📏 Data Length: {len(response.data):,} characters")
            print()
            return response.data
        else:
            print(f"❌ Failed to get ledgers: {response.error_message}")
            return None
    
    def parse_and_search_cgst(self, raw_data):
        """Parse the raw ASCII data and search for CGST ledgers"""
        print("🔧 STEP 3: Parsing and Searching for CGST")
        print("-" * 50)
        
        if not raw_data:
            print("❌ No data to parse")
            return []
        
        print("🔍 Parsing ASCII response...")
        
        # Split into lines and process
        lines = raw_data.split('\n')
        all_ledgers = []
        cgst_ledgers = []
        
        print(f"📋 Processing {len(lines)} lines...")
        
        # Parse each line to extract ledger names
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines, headers, totals, and system entries
            if (line and 
                not line.startswith('List of') and 
                not line.startswith('Page') and
                not line.startswith('From') and
                not line.startswith('To') and
                not line.startswith('Total') and
                not line.startswith('-') and
                not line.startswith('=') and
                len(line) > 1 and
                not line.isdigit() and
                not re.match(r'^\s*\d+\.\d+\s*$', line)):  # Skip pure numbers
                
                # Clean up the line (remove trailing amounts)
                clean_line = re.sub(r'\s+[\d,.-]+\s*$', '', line)  # Remove trailing amounts
                clean_line = clean_line.strip()
                
                if clean_line and len(clean_line) > 2:
                    all_ledgers.append({
                        'name': clean_line,
                        'line_number': line_num,
                        'raw_line': line
                    })
                    
                    # Check if this ledger contains "CGST" (case-insensitive)
                    if 'CGST' in clean_line.upper():
                        cgst_ledgers.append({
                            'name': clean_line,
                            'line_number': line_num,
                            'raw_line': line
                        })
        
        # Remove duplicates while preserving order
        unique_all_ledgers = []
        unique_cgst_ledgers = []
        seen_names = set()
        
        for ledger in all_ledgers:
            if ledger['name'] not in seen_names:
                unique_all_ledgers.append(ledger)
                seen_names.add(ledger['name'])
        
        seen_cgst_names = set()
        for ledger in cgst_ledgers:
            if ledger['name'] not in seen_cgst_names:
                unique_cgst_ledgers.append(ledger)
                seen_cgst_names.add(ledger['name'])
        
        print(f"📊 Parsing Results:")
        print(f"  📋 Total Ledgers Found: {len(unique_all_ledgers)}")
        print(f"  🎯 CGST Ledgers Found: {len(unique_cgst_ledgers)}")
        print()
        
        return unique_all_ledgers, unique_cgst_ledgers
    
    def display_cgst_results(self, all_ledgers, cgst_ledgers):
        """Display the CGST search results"""
        print("🔧 STEP 4: CGST Search Results")
        print("-" * 50)
        
        if not cgst_ledgers:
            print("❌ No ledgers containing 'CGST' were found")
            print(f"💡 Searched through {len(all_ledgers)} total ledgers")
            return
        
        print(f"✅ Found {len(cgst_ledgers)} ledger(s) containing 'CGST':")
        print()
        
        for i, ledger in enumerate(cgst_ledgers, 1):
            print(f"  {i:2d}. {ledger['name']}")
            print(f"      📍 Line {ledger['line_number']}")
            print(f"      📄 Raw: {ledger['raw_line'][:100]}{'...' if len(ledger['raw_line']) > 100 else ''}")
            print()
        
        # Show some statistics
        print("📊 Analysis:")
        print(f"  📈 CGST Coverage: {len(cgst_ledgers)}/{len(all_ledgers)} ({len(cgst_ledgers)/len(all_ledgers)*100:.1f}%)")
        
        # Analyze CGST ledger patterns
        cgst_types = {}
        for ledger in cgst_ledgers:
            name = ledger['name'].upper()
            if 'INPUT' in name and 'CGST' in name:
                cgst_types['Input CGST'] = cgst_types.get('Input CGST', 0) + 1
            elif 'OUTPUT' in name and 'CGST' in name:
                cgst_types['Output CGST'] = cgst_types.get('Output CGST', 0) + 1
            elif 'PAYABLE' in name and 'CGST' in name:
                cgst_types['CGST Payable'] = cgst_types.get('CGST Payable', 0) + 1
            elif 'RECEIVABLE' in name and 'CGST' in name:
                cgst_types['CGST Receivable'] = cgst_types.get('CGST Receivable', 0) + 1
            else:
                cgst_types['Other CGST'] = cgst_types.get('Other CGST', 0) + 1
        
        if cgst_types:
            print(f"  📊 CGST Types Breakdown:")
            for cgst_type, count in cgst_types.items():
                print(f"     • {cgst_type}: {count}")
    
    def get_detailed_cgst_info(self, cgst_ledgers):
        """Get detailed information for each CGST ledger"""
        print("\n🔧 STEP 5: Getting Detailed CGST Ledger Information")
        print("-" * 50)
        
        if not cgst_ledgers:
            print("❌ No CGST ledgers to query for details")
            return
        
        print(f"📊 Getting detailed info for {len(cgst_ledgers)} CGST ledger(s)...")
        
        detailed_results = []
        
        for i, ledger in enumerate(cgst_ledgers, 1):
            print(f"\n  {i}/{len(cgst_ledgers)} - Querying: {ledger['name']}")
            
            # XML request to get detailed ledger information
            xml_request = f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Ledger</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <LEDGERNAME>{ledger['name']}</LEDGERNAME>
          <SVFROMDATE>1-Apr-2024</SVFROMDATE>
          <SVTODATE>31-Mar-2025</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
            
            response = self.connector.send_xml_request(
                xml_request, 
                f"Ledger Details: {ledger['name']}"
            )
            
            if response.success:
                print(f"      ✅ Details retrieved ({len(response.data)} chars)")
                
                # Try to extract key information from XML
                ledger_info = {
                    'name': ledger['name'],
                    'response_size': len(response.data),
                    'has_transactions': '<VOUCHER>' in response.data or 'VOUCHERTYPENAME' in response.data,
                    'balance_info_found': 'CLOSINGBALANCE' in response.data or 'AMOUNT' in response.data
                }
                
                detailed_results.append(ledger_info)
            else:
                print(f"      ❌ Failed: {response.error_message}")
        
        # Display detailed results summary
        print(f"\n📊 Detailed CGST Ledger Analysis:")
        print("-" * 40)
        
        for info in detailed_results:
            print(f"📋 {info['name']}")
            print(f"   📏 Data Size: {info['response_size']:,} characters")
            print(f"   💰 Has Transactions: {'✅ Yes' if info['has_transactions'] else '❌ No'}")
            print(f"   📊 Has Balance Info: {'✅ Yes' if info['balance_info_found'] else '❌ No'}")
            print()
    
    def run_cgst_search(self):
        """Run the complete CGST ledger search"""
        try:
            # Setup monitoring
            self.setup_signal_monitoring()
            
            # Step 1: Test connection
            if not self.test_connection():
                return False
            
            # Step 2: Get all ledgers
            raw_data = self.get_all_ledgers_raw()
            if not raw_data:
                return False
            
            # Step 3: Parse and search for CGST
            all_ledgers, cgst_ledgers = self.parse_and_search_cgst(raw_data)
            
            # Step 4: Display results
            self.display_cgst_results(all_ledgers, cgst_ledgers)
            
            # Step 5: Get detailed information if CGST ledgers found
            if cgst_ledgers:
                print("\n" + "="*60)
                get_details = True  # In interactive version, you could ask user
                if get_details:
                    self.get_detailed_cgst_info(cgst_ledgers)
            
            # Final summary
            print("\n" + "="*80)
            print("🎉 CGST LEDGER SEARCH COMPLETED")
            print("="*80)
            print(f"✅ Successfully searched through {len(all_ledgers) if 'all_ledgers' in locals() else 'N/A'} ledgers")
            print(f"🎯 Found {len(cgst_ledgers)} CGST-related ledgers")
            print(f"📊 Connection Statistics: {self.connector.connection_stats}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during CGST search: {e}")
            return False
        
        finally:
            # Cleanup
            self.connector.close()
            print("🧹 Connection closed")


def main():
    """Main function"""
    print("🔍 Starting CGST Ledger Search Test")
    print("=" * 80)
    
    searcher = CGSTLedgerSearcher()
    success = searcher.run_cgst_search()
    
    if success:
        print("\n✅ CGST search completed successfully!")
    else:
        print("\n❌ CGST search failed")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
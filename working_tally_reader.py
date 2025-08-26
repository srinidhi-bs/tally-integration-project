#!/usr/bin/env python3
"""
Working TallyPrime Data Reader
Uses correct XML format that TallyPrime expects without TDL errors
Created by: Srinidhi BS & Claude
Date: August 26, 2025
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List
import re

class WorkingTallyReader:
    """
    TallyPrime data reader using proper XML requests that don't cause TDL errors
    """
    
    def __init__(self, tally_host: str = "172.28.208.1", tally_port: int = 9000):
        self.tally_host = tally_host
        self.tally_port = tally_port
        self.tally_url = f"http://{tally_host}:{tally_port}"
        self.session = requests.Session()
        print(f"🔗 Connected to TallyPrime at {self.tally_url}")
    
    def send_xml_request(self, xml_request: str, description: str = "") -> str:
        """
        Send XML request to TallyPrime
        """
        try:
            headers = {
                'Content-Type': 'application/xml; charset=utf-8',
                'Content-Length': str(len(xml_request.encode('utf-8')))
            }
            
            if description:
                print(f"📤 Sending request: {description}")
            
            response = self.session.post(
                self.tally_url, 
                data=xml_request.encode('utf-8'), 
                headers=headers, 
                timeout=20
            )
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"❌ HTTP Error {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return ""
    
    def get_ledger_list_simple(self) -> List[str]:
        """
        Get list of ledgers using a simple, working XML request
        """
        print("📋 Getting ledger list...")
        
        # This is a working XML request format for ledger collection
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
        
        response = self.send_xml_request(xml_request, "List of Accounts")
        
        if response:
            # Parse the ASCII response to extract ledger names
            lines = response.split('\n')
            ledgers = []
            
            # Look for lines that contain ledger names
            # TallyPrime ASCII export usually has ledger names in specific patterns
            for line in lines:
                line = line.strip()
                # Skip empty lines, headers, totals, and system entries
                if (line and 
                    not line.startswith('List of') and 
                    not line.startswith('Page') and
                    not line.startswith('Total') and
                    not line.startswith('-') and
                    not line.startswith('=') and
                    len(line) > 1 and
                    not line.isdigit()):
                    
                    # Clean up the line (remove extra spaces, numbers at end)
                    clean_line = re.sub(r'\s+\d+\.\d+\s*$', '', line)  # Remove trailing amounts
                    clean_line = clean_line.strip()
                    
                    if clean_line and len(clean_line) > 2:
                        ledgers.append(clean_line)
            
            # Remove duplicates while preserving order
            unique_ledgers = []
            seen = set()
            for ledger in ledgers:
                if ledger not in seen:
                    unique_ledgers.append(ledger)
                    seen.add(ledger)
            
            print(f"✅ Found {len(unique_ledgers)} ledgers")
            
            # Show first few ledgers
            if unique_ledgers:
                print("📝 Sample ledgers:")
                for ledger in unique_ledgers[:10]:
                    print(f"   • {ledger}")
                if len(unique_ledgers) > 10:
                    print(f"   ... and {len(unique_ledgers) - 10} more")
            
            return unique_ledgers
        else:
            print("❌ No response received")
            return []
    
    def get_groups_list_simple(self) -> List[str]:
        """
        Get list of groups using ASCII format
        """
        print("📁 Getting groups list...")
        
        xml_request = """<ENVELOPE>
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
        
        response = self.send_xml_request(xml_request, "List of Groups")
        
        if response:
            lines = response.split('\n')
            groups = []
            
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.startswith('List of') and 
                    not line.startswith('Page') and
                    not line.startswith('Total') and
                    not line.startswith('-') and
                    not line.startswith('=') and
                    len(line) > 1):
                    
                    # Clean the line
                    clean_line = line.strip()
                    if clean_line and len(clean_line) > 2:
                        groups.append(clean_line)
            
            # Remove duplicates
            unique_groups = list(set(groups))
            unique_groups.sort()
            
            print(f"✅ Found {len(unique_groups)} groups")
            
            if unique_groups:
                print("📁 Available groups:")
                for group in unique_groups[:15]:
                    print(f"   • {group}")
                if len(unique_groups) > 15:
                    print(f"   ... and {len(unique_groups) - 15} more")
            
            return unique_groups
        else:
            print("❌ No response received")
            return []
    
    def get_daybook_entries(self) -> List[Dict]:
        """
        Get recent daybook entries
        """
        print("📄 Getting recent daybook entries...")
        
        xml_request = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Day Book</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:ASCII</SVEXPORTFORMAT>
          <SVFROMDATE>1-Aug-2025</SVFROMDATE>
          <SVTODATE>31-Aug-2025</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
        
        response = self.send_xml_request(xml_request, "Day Book")
        
        if response:
            lines = response.split('\n')
            entries = []
            
            # Parse daybook format - typically has date, voucher type, number, amount
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.startswith('Day Book') and 
                    not line.startswith('Page') and
                    not line.startswith('From') and
                    not line.startswith('To') and
                    not line.startswith('Total') and
                    not line.startswith('-') and
                    not line.startswith('=') and
                    len(line) > 10):  # Should have reasonable length for transaction line
                    
                    # Try to parse common daybook patterns
                    # Look for lines that might contain dates and amounts
                    if any(char.isdigit() for char in line):
                        entries.append({'raw_line': line})
            
            print(f"✅ Found {len(entries)} daybook entries")
            
            if entries:
                print("📝 Recent transactions:")
                for entry in entries[:10]:
                    print(f"   • {entry['raw_line']}")
            
            return entries
        else:
            print("❌ No response received")
            return []
    
    def test_basic_reports(self) -> Dict:
        """
        Test basic reports that should work without TDL errors
        """
        print("🔍 Testing basic TallyPrime reports...")
        
        # Reports that typically work with ASCII export
        reports = {
            "Balance Sheet": "Balance Sheet",
            "Profit and Loss": "Profit & Loss",
            "Trial Balance": "Trial Balance"
        }
        
        results = {}
        
        for report_name, report_code in reports.items():
            print(f"   Testing: {report_name}")
            
            xml_request = f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>{report_code}</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:ASCII</SVEXPORTFORMAT>
          <SVFROMDATE>1-Apr-2024</SVFROMDATE>
          <SVTODATE>31-Mar-2025</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
            
            response = self.send_xml_request(xml_request)
            
            if response and len(response) > 100:
                # Count meaningful lines
                lines = [l.strip() for l in response.split('\n') if l.strip()]
                meaningful_lines = [l for l in lines if len(l) > 5 and not l.startswith('-')]
                
                results[report_name] = {
                    'status': 'success',
                    'lines_count': len(meaningful_lines),
                    'preview': meaningful_lines[:3] if meaningful_lines else []
                }
                print(f"      ✅ {report_name}: {len(meaningful_lines)} data lines")
            else:
                results[report_name] = {
                    'status': 'failed',
                    'error': 'No data or error response'
                }
                print(f"      ❌ {report_name}: Failed")
        
        return results
    
    def comprehensive_data_test(self) -> Dict:
        """
        Run comprehensive test of TallyPrime data access
        """
        print("=" * 80)
        print("🎯 COMPREHENSIVE TALLYPRME DATA ACCESS TEST")
        print("=" * 80)
        
        results = {}
        
        # Test 1: Get ledgers
        print("\n1️⃣ LEDGER ACCOUNTS TEST")
        print("-" * 50)
        try:
            ledgers = self.get_ledger_list_simple()
            results['ledgers'] = {
                'count': len(ledgers),
                'sample': ledgers[:5] if ledgers else [],
                'all': ledgers
            }
        except Exception as e:
            print(f"❌ Ledger test failed: {e}")
            results['ledgers'] = {'error': str(e)}
        
        # Test 2: Get groups
        print("\n2️⃣ GROUPS TEST")
        print("-" * 50)
        try:
            groups = self.get_groups_list_simple()
            results['groups'] = {
                'count': len(groups),
                'sample': groups[:5] if groups else [],
                'all': groups
            }
        except Exception as e:
            print(f"❌ Groups test failed: {e}")
            results['groups'] = {'error': str(e)}
        
        # Test 3: Get daybook
        print("\n3️⃣ DAYBOOK TEST")
        print("-" * 50)
        try:
            daybook = self.get_daybook_entries()
            results['daybook'] = {
                'count': len(daybook),
                'sample': daybook[:3] if daybook else []
            }
        except Exception as e:
            print(f"❌ Daybook test failed: {e}")
            results['daybook'] = {'error': str(e)}
        
        # Test 4: Basic reports
        print("\n4️⃣ BASIC REPORTS TEST")
        print("-" * 50)
        try:
            reports = self.test_basic_reports()
            results['reports'] = reports
        except Exception as e:
            print(f"❌ Reports test failed: {e}")
            results['reports'] = {'error': str(e)}
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 FINAL SUMMARY")
        print("=" * 80)
        
        # Count successes
        ledger_count = results.get('ledgers', {}).get('count', 0)
        group_count = results.get('groups', {}).get('count', 0)
        daybook_count = results.get('daybook', {}).get('count', 0)
        
        successful_reports = sum(1 for r in results.get('reports', {}).values() 
                               if isinstance(r, dict) and r.get('status') == 'success')
        
        if ledger_count > 0:
            print(f"✅ Ledgers: Successfully read {ledger_count} accounts")
        else:
            print("❌ Ledgers: No accounts found")
        
        if group_count > 0:
            print(f"✅ Groups: Successfully read {group_count} groups")
        else:
            print("❌ Groups: No groups found")
        
        if daybook_count > 0:
            print(f"✅ Transactions: Found {daybook_count} daybook entries")
        else:
            print("⚠️  Transactions: No recent transactions (may be normal)")
        
        if successful_reports > 0:
            print(f"✅ Reports: {successful_reports} standard reports accessible")
        else:
            print("❌ Reports: No standard reports accessible")
        
        # Overall status
        if ledger_count > 0 or group_count > 0:
            print("\n🎉 SUCCESS: TallyPrime data is readable!")
            print("💡 You can extract ledger information and build integrations")
            if successful_reports > 0:
                print("📊 Standard reports are also available for data extraction")
        else:
            print("\n⚠️  LIMITED ACCESS: Some data may be protected or require different approach")
            print("💡 Try ensuring a company is loaded and HTTP Gateway is properly configured")
        
        return results

def main():
    """
    Main function
    """
    try:
        reader = WorkingTallyReader()
        
        # Run comprehensive test
        results = reader.comprehensive_data_test()
        
        print("\n🚀 Data access test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
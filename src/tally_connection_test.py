#!/usr/bin/env python3
"""
Tally HTTP-XML Gateway Connection Test Script

This script tests the connection to Tally's HTTP-XML Gateway.
Tally typically runs on port 9000 by default when HTTP-XML Gateway is enabled.

Author: Srinidhi BS
Purpose: Testing Tally ERP connectivity for learning
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def test_tally_connection():
    """
    Test connection to Tally HTTP-XML Gateway
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    # Tally HTTP-XML Gateway URL for WSL to Windows connection
    # Based on your learnings document, use Windows host IP
    tally_url = "http://172.28.208.1:9000"
    
    # Simple XML request to check if Tally is responding
    # This is a basic request to get company information
    xml_request = """
    <ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Import Data</TALLYREQUEST>
        </HEADER>
        <BODY>
            <IMPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>List of Companies</REPORTNAME>
                </REQUESTDESC>
            </IMPORTDATA>
        </BODY>
    </ENVELOPE>
    """
    
    try:
        print(f"Testing connection to Tally at: {tally_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        
        # Send POST request to Tally with XML data
        # timeout=30 means we'll wait maximum 30 seconds for response
        response = requests.post(
            tally_url, 
            data=xml_request, 
            headers={'Content-Type': 'application/xml'},
            timeout=30
        )
        
        # Check if we got a successful HTTP response (status code 200)
        if response.status_code == 200:
            print("✅ Connection successful!")
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
            
            # Try to parse the XML response to check if it's valid
            try:
                root = ET.fromstring(response.text)
                print("✅ Valid XML response received")
                
                # Print first few lines of response for inspection
                response_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
                print(f"\nResponse preview:\n{response_preview}")
                
                return True
                
            except ET.ParseError as xml_error:
                print(f"⚠️  Connection successful but invalid XML response: {xml_error}")
                print(f"Raw response: {response.text[:200]}...")
                return False
                
        else:
            print(f"❌ HTTP Error: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed: Cannot connect to Tally")
        print("Possible reasons:")
        print("  - Tally is not running")
        print("  - HTTP-XML Gateway is not enabled in Tally")
        print("  - Tally is running on a different port")
        print("  - Firewall is blocking the connection")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Connection timeout: Tally is not responding")
        print("Tally might be busy or not properly configured")
        return False
        
    except Exception as error:
        print(f"❌ Unexpected error: {error}")
        return False

def check_alternative_ports():
    """
    Check if Tally is running on alternative ports
    Sometimes Tally might be configured to run on different ports
    """
    print("\n" + "="*50)
    print("Checking alternative ports...")
    print("="*50)
    
    # Common alternative ports for Tally
    alternative_ports = [9001, 9002, 8000, 8080, 9999]
    
    for port in alternative_ports:
        try:
            url = f"http://localhost:{port}"
            print(f"\nTrying port {port}...")
            
            # Simple GET request to check if anything is listening
            response = requests.get(url, timeout=3)
            print(f"✅ Something is responding on port {port}")
            print(f"Status: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Nothing on port {port}")
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout on port {port}")
        except Exception as e:
            print(f"❌ Error on port {port}: {e}")

if __name__ == "__main__":
    """
    Main execution block
    This runs when the script is executed directly (not imported)
    """
    print("Tally HTTP-XML Gateway Connection Test")
    print("=====================================")
    
    # Test the main connection
    connection_successful = test_tally_connection()
    
    # If main connection failed, check alternative ports
    if not connection_successful:
        check_alternative_ports()
        
        print("\n" + "="*50)
        print("TROUBLESHOOTING TIPS:")
        print("="*50)
        print("1. Make sure Tally is running")
        print("2. Enable HTTP-XML Gateway in Tally:")
        print("   - Go to Gateway of Tally > Configure")
        print("   - Enable 'HTTP-XML Gateway'")
        print("   - Note the port number (usually 9000)")
        print("3. Check if Windows Firewall is blocking the connection")
        print("4. Try running this script as administrator")
    
    else:
        print("\n🎉 Tally connection test completed successfully!")
        print("You can now send XML requests to Tally for data exchange.")
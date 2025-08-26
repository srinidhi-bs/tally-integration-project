#!/usr/bin/env python3
"""
Specific IP Tally Detection Script
Test TallyPrime connection to a specific IP address (like brother's laptop)
Created by: Srinidhi BS & Claude
Date: August 26, 2025
"""

import requests
import socket
import sys
from typing import Dict, Optional

class SpecificTallyDetector:
    """
    Test TallyPrime connection to a specific IP address
    Useful when you know the target device's IP
    """
    
    def __init__(self, target_ip: str, port: int = 9000):
        self.target_ip = target_ip
        self.port = port
        self.gateway_url = f"http://{target_ip}:{port}"
        
    def test_basic_connectivity(self) -> Dict:
        """
        Test basic network connectivity to the target IP
        """
        print(f"🔗 Testing basic connectivity to {self.target_ip}...")
        
        try:
            # Test if we can reach the IP (socket connect test)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target_ip, self.port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {self.port} is open on {self.target_ip}")
                return {'connectivity': True, 'port_open': True}
            else:
                print(f"❌ Port {self.port} is closed or filtered on {self.target_ip}")
                return {'connectivity': True, 'port_open': False, 'reason': 'Port closed/filtered'}
                
        except socket.gaierror:
            print(f"❌ Cannot resolve IP address {self.target_ip}")
            return {'connectivity': False, 'error': 'DNS resolution failed'}
        except socket.timeout:
            print(f"⏱️  Connection timeout to {self.target_ip}")
            return {'connectivity': False, 'error': 'Connection timeout'}
        except Exception as e:
            print(f"❌ Network error: {e}")
            return {'connectivity': False, 'error': str(e)}
    
    def test_tally_http_gateway(self) -> Dict:
        """
        Test TallyPrime HTTP Gateway on the target IP
        """
        print(f"🌐 Testing TallyPrime HTTP Gateway at {self.gateway_url}...")
        
        try:
            # Test HTTP connection
            response = requests.get(self.gateway_url, timeout=10)
            
            if response.status_code == 200:
                response_text = response.text.strip()
                print(f"✅ HTTP Gateway responded successfully!")
                print(f"📡 Response: {response_text}")
                
                # Check if it's TallyPrime
                if "TallyPrime Server is Running" in response_text:
                    return {
                        'http_success': True,
                        'is_tally': True,
                        'response': response_text,
                        'status': 'TallyPrime HTTP Gateway is active and ready!'
                    }
                elif "Tally" in response_text:
                    return {
                        'http_success': True,
                        'is_tally': True,
                        'response': response_text,
                        'status': 'Tally Gateway detected (older version or different response)'
                    }
                else:
                    return {
                        'http_success': True,
                        'is_tally': False,
                        'response': response_text,
                        'status': 'HTTP service found but not TallyPrime'
                    }
            else:
                print(f"❌ HTTP error: Status code {response.status_code}")
                return {
                    'http_success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}'
                }
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏱️  HTTP connection timeout")
            return {'http_success': False, 'error': 'HTTP timeout'}
        except requests.exceptions.ConnectionError:
            print(f"🚫 HTTP connection refused")
            return {'http_success': False, 'error': 'Connection refused'}
        except Exception as e:
            print(f"❌ HTTP error: {e}")
            return {'http_success': False, 'error': str(e)}
    
    def get_device_info(self) -> Dict:
        """
        Try to get information about the target device
        """
        print(f"🖥️  Getting device information for {self.target_ip}...")
        
        device_info = {'ip': self.target_ip}
        
        try:
            # Try hostname lookup
            hostname = socket.gethostbyaddr(self.target_ip)[0]
            device_info['hostname'] = hostname
            print(f"🏷️  Hostname: {hostname}")
        except:
            device_info['hostname'] = 'Unknown'
            print("🏷️  Hostname: Unknown")
            
        return device_info
    
    def comprehensive_test(self) -> Dict:
        """
        Run comprehensive test on the specific IP
        """
        print("=" * 70)
        print(f"🎯 TESTING TALLY ON SPECIFIC IP: {self.target_ip}")
        print("=" * 70)
        
        results = {
            'target_ip': self.target_ip,
            'port': self.port,
            'gateway_url': self.gateway_url
        }
        
        # 1. Get device info
        print("\n1️⃣ DEVICE INFORMATION")
        print("-" * 40)
        device_info = self.get_device_info()
        results['device_info'] = device_info
        
        # 2. Test basic connectivity
        print("\n2️⃣ CONNECTIVITY TEST")
        print("-" * 40)
        connectivity = self.test_basic_connectivity()
        results['connectivity'] = connectivity
        
        # 3. Test HTTP Gateway (only if connectivity works)
        print("\n3️⃣ TALLY HTTP GATEWAY TEST")
        print("-" * 40)
        if connectivity.get('connectivity', False):
            gateway_result = self.test_tally_http_gateway()
            results['http_gateway'] = gateway_result
        else:
            print("⏭️  Skipping HTTP test due to connectivity issues")
            results['http_gateway'] = {'skipped': True, 'reason': 'No connectivity'}
        
        # Generate summary
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY")
        print("=" * 70)
        
        if results.get('http_gateway', {}).get('is_tally', False):
            status = "✅ SUCCESS: TallyPrime found and ready for integration!"
            integration_ready = True
        elif results.get('connectivity', {}).get('connectivity', False):
            status = "⚠️  Device reachable but TallyPrime not detected"
            integration_ready = False
        else:
            status = "❌ Cannot connect to device"
            integration_ready = False
        
        results['summary'] = {
            'status': status,
            'integration_ready': integration_ready,
            'hostname': device_info.get('hostname', 'Unknown')
        }
        
        print(f"Status: {status}")
        print(f"Device: {device_info.get('hostname', 'Unknown')} ({self.target_ip})")
        print(f"Integration Ready: {'Yes' if integration_ready else 'No'}")
        
        if integration_ready:
            print(f"\n🚀 You can use this gateway URL in your integration:")
            print(f"   {self.gateway_url}")
        else:
            print("\n💡 TROUBLESHOOTING:")
            if not connectivity.get('connectivity', False):
                print("   • Check if the device is powered on and connected")
                print("   • Verify the IP address is correct")
                print("   • Check network connectivity between devices")
            else:
                print("   • Ensure TallyPrime is running on the target device")
                print("   • Enable HTTP Gateway in TallyPrime:")
                print("     - Press F1 → Settings → Connectivity")
                print("     - Set 'TallyPrime acts as' = Both")
                print("     - Set Port = 9000")
                print("   • Check Windows Firewall on target device")
        
        return results

def main():
    """
    Main function - accepts IP address as command line argument
    """
    if len(sys.argv) != 2:
        print("Usage: python3 detect_specific_tally.py <IP_ADDRESS>")
        print("\nExample:")
        print("  python3 detect_specific_tally.py 192.168.1.100")
        print("  python3 detect_specific_tally.py 172.28.208.50")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    
    # Basic IP validation
    try:
        socket.inet_aton(target_ip)
    except socket.error:
        print(f"❌ Invalid IP address: {target_ip}")
        sys.exit(1)
    
    try:
        detector = SpecificTallyDetector(target_ip)
        results = detector.comprehensive_test()
        
        # Exit with appropriate code
        if results['summary']['integration_ready']:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Issues found
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Tally Application Detection Script
Detects if TallyPrime is running on Windows system from WSL environment
Created by: Srinidhi BS & Claude
Date: August 26, 2025
"""

import subprocess
import sys
import requests
from typing import Dict, List, Optional

class TallyDetector:
    """
    Detects running TallyPrime application on Windows from WSL
    Uses multiple detection methods for comprehensive coverage
    """
    
    def __init__(self):
        # Windows host IP from WSL (typically the default gateway)
        self.windows_host_ip = self._get_windows_host_ip()
        self.tally_http_port = 9000  # Default TallyPrime HTTP Gateway port
        
    def _get_windows_host_ip(self) -> str:
        """
        Get Windows host IP address from WSL environment
        Returns the default gateway IP which is typically the Windows host
        """
        try:
            # Get default route to find Windows host IP
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, check=True)
            
            # Parse output to extract IP: "default via 172.28.208.1 dev eth0"
            for line in result.stdout.strip().split('\n'):
                if 'default via' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]  # IP address after "via"
                        
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting Windows host IP: {e}")
            
        # Fallback to common WSL default gateway
        return "172.28.208.1"
    
    def detect_tally_processes(self) -> Dict:
        """
        Detect TallyPrime processes running on Windows
        Uses PowerShell commands executed from WSL
        """
        print("🔍 Checking for TallyPrime processes on Windows...")
        
        # PowerShell command to find TallyPrime related processes
        powershell_cmd = [
            'powershell.exe', '-Command',
            'Get-Process | Where-Object {$_.ProcessName -like "*tally*" -or $_.ProcessName -like "*Tally*"} | Select-Object ProcessName, Id, CPU, WorkingSet | Format-Table -AutoSize'
        ]
        
        try:
            # Execute PowerShell command from WSL
            result = subprocess.run(powershell_cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                print("✅ Found TallyPrime processes:")
                print(result.stdout)
                return {
                    'processes_found': True,
                    'process_details': result.stdout.strip(),
                    'detection_method': 'PowerShell Process List'
                }
            else:
                print("❌ No TallyPrime processes found")
                return {
                    'processes_found': False,
                    'process_details': None,
                    'detection_method': 'PowerShell Process List'
                }
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error checking processes: {e}")
            return {
                'processes_found': False,
                'error': str(e),
                'detection_method': 'PowerShell Process List'
            }
    
    def check_http_gateway(self) -> Dict:
        """
        Check if TallyPrime HTTP Gateway is accessible
        This is the most reliable method as it confirms Tally is running AND configured
        """
        print(f"🌐 Checking TallyPrime HTTP Gateway at {self.windows_host_ip}:{self.tally_http_port}...")
        
        gateway_url = f"http://{self.windows_host_ip}:{self.tally_http_port}"
        
        try:
            # Test HTTP connection with short timeout
            response = requests.get(gateway_url, timeout=5)
            
            if response.status_code == 200:
                response_text = response.text.strip()
                print(f"✅ TallyPrime HTTP Gateway is ACTIVE")
                print(f"📡 Response: {response_text}")
                
                # Check if it's the expected TallyPrime response
                if "TallyPrime Server is Running" in response_text:
                    return {
                        'http_gateway_active': True,
                        'gateway_url': gateway_url,
                        'response': response_text,
                        'status': 'TallyPrime HTTP Gateway is fully operational',
                        'ready_for_integration': True
                    }
                else:
                    return {
                        'http_gateway_active': True,
                        'gateway_url': gateway_url,
                        'response': response_text,
                        'status': 'HTTP service running but may not be TallyPrime',
                        'ready_for_integration': False
                    }
            else:
                print(f"❌ HTTP Gateway returned status code: {response.status_code}")
                return {
                    'http_gateway_active': False,
                    'gateway_url': gateway_url,
                    'status_code': response.status_code,
                    'ready_for_integration': False
                }
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏱️  Connection timeout - TallyPrime may not be running or HTTP Gateway not enabled")
            return {
                'http_gateway_active': False,
                'gateway_url': gateway_url,
                'error': 'Connection timeout',
                'ready_for_integration': False
            }
            
        except requests.exceptions.ConnectionError:
            print(f"🚫 Connection refused - TallyPrime likely not running or HTTP Gateway disabled")
            return {
                'http_gateway_active': False,
                'gateway_url': gateway_url,
                'error': 'Connection refused',
                'ready_for_integration': False
            }
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {
                'http_gateway_active': False,
                'gateway_url': gateway_url,
                'error': str(e),
                'ready_for_integration': False
            }
    
    def check_network_connectivity(self) -> Dict:
        """
        Test basic network connectivity to Windows host
        Helps diagnose network issues between WSL and Windows
        """
        print(f"🔗 Testing network connectivity to Windows host: {self.windows_host_ip}")
        
        try:
            # Ping Windows host
            ping_result = subprocess.run(['ping', '-c', '3', self.windows_host_ip], 
                                       capture_output=True, text=True, check=True)
            
            print("✅ Network connectivity to Windows host is working")
            return {
                'network_connectivity': True,
                'ping_result': ping_result.stdout.strip(),
                'windows_host_ip': self.windows_host_ip
            }
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Network connectivity issue: {e}")
            return {
                'network_connectivity': False,
                'error': str(e),
                'windows_host_ip': self.windows_host_ip
            }
    
    def comprehensive_detection(self) -> Dict:
        """
        Perform comprehensive Tally detection using all available methods
        Returns detailed status report
        """
        print("=" * 60)
        print("🎯 TALLY APPLICATION DETECTION REPORT")
        print("=" * 60)
        
        # Initialize results dictionary
        results = {
            'detection_timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
            'windows_host_ip': self.windows_host_ip,
            'detection_summary': {}
        }
        
        # 1. Check network connectivity first
        print("\n1️⃣ NETWORK CONNECTIVITY TEST")
        print("-" * 40)
        network_result = self.check_network_connectivity()
        results['network_test'] = network_result
        
        # 2. Check for TallyPrime processes
        print("\n2️⃣ PROCESS DETECTION TEST")
        print("-" * 40)
        process_result = self.detect_tally_processes()
        results['process_detection'] = process_result
        
        # 3. Check HTTP Gateway (most important)
        print("\n3️⃣ HTTP GATEWAY TEST")
        print("-" * 40)
        gateway_result = self.check_http_gateway()
        results['http_gateway'] = gateway_result
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📋 DETECTION SUMMARY")
        print("=" * 60)
        
        # Determine overall status
        if gateway_result.get('ready_for_integration', False):
            overall_status = "✅ TALLY FULLY OPERATIONAL - Ready for integration"
            integration_ready = True
        elif process_result.get('processes_found', False):
            overall_status = "⚠️  TALLY RUNNING - HTTP Gateway may need configuration"
            integration_ready = False
        elif network_result.get('network_connectivity', False):
            overall_status = "❌ TALLY NOT DETECTED - May not be running"
            integration_ready = False
        else:
            overall_status = "🚫 NETWORK ISSUES - Cannot reach Windows host"
            integration_ready = False
        
        results['detection_summary'] = {
            'overall_status': overall_status,
            'integration_ready': integration_ready,
            'network_ok': network_result.get('network_connectivity', False),
            'processes_found': process_result.get('processes_found', False),
            'http_gateway_active': gateway_result.get('http_gateway_active', False)
        }
        
        print(f"Status: {overall_status}")
        print(f"Integration Ready: {'Yes' if integration_ready else 'No'}")
        
        if integration_ready:
            print("\n🚀 You can proceed with TallyPrime integration!")
        else:
            print("\n💡 TROUBLESHOOTING SUGGESTIONS:")
            if not network_result.get('network_connectivity', False):
                print("   • Check WSL network configuration")
                print("   • Verify Windows host connectivity")
            elif not process_result.get('processes_found', False):
                print("   • Start TallyPrime application")
                print("   • Load a company in TallyPrime")
            elif not gateway_result.get('http_gateway_active', False):
                print("   • Enable HTTP Gateway in TallyPrime:")
                print("     - Press F1 → Settings → Connectivity")
                print("     - Set 'TallyPrime acts as' = Both")
                print("     - Set 'Enable ODBC' = Yes") 
                print("     - Set Port = 9000")
        
        return results

def main():
    """
    Main function to run Tally detection
    """
    try:
        # Create detector instance
        detector = TallyDetector()
        
        # Run comprehensive detection
        results = detector.comprehensive_detection()
        
        # Return appropriate exit code
        if results['detection_summary']['integration_ready']:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Issues found
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Detection cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error during detection: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
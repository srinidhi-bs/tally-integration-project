#!/usr/bin/env python3
"""
Simple Tally Connection Test
Just test if we can reach Tally with a GET request like curl does
"""

import requests

def simple_test():
    """Test basic GET request to Tally (like curl)"""
    try:
        print("Testing simple GET request to Tally...")
        response = requests.get("http://172.28.208.1:9000", timeout=10)
        print(f"✅ Success! Status: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    simple_test()
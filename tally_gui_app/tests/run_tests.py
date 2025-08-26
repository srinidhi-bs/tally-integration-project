#!/usr/bin/env python3
"""
Test Runner for TallyPrime Integration Manager

This script provides a convenient way to run all tests or specific test categories.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 26, 2025
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_root,
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def run_integration_tests():
    """Run all integration tests"""
    print("🔧 RUNNING INTEGRATION TESTS")
    print("=" * 70)
    
    integration_tests = [
        {
            "command": "python3 tests/integration/test_connection_framework.py",
            "description": "Connection Framework Test"
        },
        {
            "command": "python3 tests/integration/test_cgst_ledgers.py", 
            "description": "CGST Ledger Search Test"
        },
        {
            "command": "python3 tests/integration/demo_manual_tests.py",
            "description": "Manual Testing Demo"
        }
    ]
    
    results = []
    
    for test in integration_tests:
        success = run_command(test["command"], test["description"])
        results.append({
            "test": test["description"],
            "success": success
        })
    
    return results


def run_unit_tests():
    """Run unit tests (placeholder for future unit tests)"""
    print("🔧 RUNNING UNIT TESTS")
    print("=" * 70)
    
    # Check if there are any unit test files
    unit_test_dir = project_root / "tests" / "unit"
    unit_test_files = list(unit_test_dir.glob("test_*.py"))
    
    if not unit_test_files:
        print("ℹ️  No unit tests found in tests/unit/")
        print("💡 Unit tests will be added in future development phases")
        return [{"test": "Unit Tests", "success": True, "skipped": True}]
    
    # Run unit tests when they exist
    results = []
    for test_file in unit_test_files:
        command = f"python3 {test_file.relative_to(project_root)}"
        success = run_command(command, f"Unit Test: {test_file.name}")
        results.append({
            "test": f"Unit Test: {test_file.name}",
            "success": success
        })
    
    return results


def show_test_summary(integration_results, unit_results):
    """Show comprehensive test summary"""
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    
    all_results = integration_results + unit_results
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r["success"])
    failed_tests = total_tests - passed_tests
    skipped_tests = sum(1 for r in all_results if r.get("skipped", False))
    
    print(f"📊 Test Results:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Skipped: {skipped_tests}")
    
    print(f"\n📋 Detailed Results:")
    for result in all_results:
        if result.get("skipped"):
            status = "⏭️  SKIPPED"
        elif result["success"]:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        print(f"  {result['test']:<40} {status}")
    
    success_rate = (passed_tests / (total_tests - skipped_tests) * 100) if (total_tests - skipped_tests) > 0 else 100
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ TallyPrime Integration Manager is working correctly")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")
        print("🔧 Please review failed tests and fix issues")
    
    return failed_tests == 0


def show_menu():
    """Show test menu options"""
    print("=" * 80)
    print("🧪 TALLYPRME INTEGRATION MANAGER - TEST RUNNER")
    print("=" * 80)
    print("1. 🔗 Run Integration Tests (Connection, CGST, Manual Demo)")
    print("2. 🧱 Run Unit Tests (Framework Components)")
    print("3. 🎯 Run All Tests")
    print("4. 📋 Show Test Information")
    print("5. ❌ Exit")
    print("=" * 80)


def show_test_info():
    """Show information about the test structure"""
    print("\n📋 TEST STRUCTURE INFORMATION")
    print("=" * 80)
    
    print("🔗 Integration Tests (tests/integration/):")
    print("  • test_connection_framework.py - Complete connection framework testing")
    print("  • test_cgst_ledgers.py - Real-world CGST ledger search")
    print("  • demo_manual_tests.py - Demonstration of manual testing features")
    print("  • manual_test_connector.py - Interactive manual testing interface")
    
    print("\n🧱 Unit Tests (tests/unit/):")
    print("  • (To be added) - Individual component testing")
    print("  • (To be added) - Data model validation")
    print("  • (To be added) - XML processing tests")
    
    print("\n📁 Test Fixtures (tests/fixtures/):")
    print("  • (To be added) - Sample XML responses")
    print("  • (To be added) - Mock company data")
    print("  • (To be added) - Test configurations")
    
    print("\n🎯 Test Categories:")
    print("  ✅ Live Integration - Tests with actual TallyPrime connection")
    print("  ✅ Error Handling - Network failures, invalid responses")
    print("  ✅ Data Processing - XML parsing, data extraction")
    print("  ✅ Signal Testing - Qt6 signal-slot communication")
    print("  ✅ Settings Persistence - Configuration save/load")
    print("  ✅ Performance - Response times, connection pooling")


def main():
    """Main test runner function"""
    if len(sys.argv) > 1:
        # Command line argument provided
        arg = sys.argv[1].lower()
        
        if arg in ['integration', 'int', '1']:
            integration_results = run_integration_tests()
            unit_results = []
        elif arg in ['unit', 'u', '2']:
            integration_results = []
            unit_results = run_unit_tests()
        elif arg in ['all', 'a', '3']:
            integration_results = run_integration_tests()
            unit_results = run_unit_tests()
        elif arg in ['info', 'i', '4']:
            show_test_info()
            return 0
        else:
            print(f"❌ Unknown argument: {arg}")
            print("💡 Usage: python3 run_tests.py [integration|unit|all|info]")
            return 1
        
        # Show summary if tests were run
        if integration_results or unit_results:
            success = show_test_summary(integration_results, unit_results)
            return 0 if success else 1
        
        return 0
    
    else:
        # Interactive mode
        try:
            while True:
                show_menu()
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == "1":
                    integration_results = run_integration_tests()
                    unit_results = []
                    show_test_summary(integration_results, unit_results)
                
                elif choice == "2":
                    integration_results = []
                    unit_results = run_unit_tests()
                    show_test_summary(integration_results, unit_results)
                
                elif choice == "3":
                    integration_results = run_integration_tests()
                    unit_results = run_unit_tests()
                    success = show_test_summary(integration_results, unit_results)
                
                elif choice == "4":
                    show_test_info()
                
                elif choice == "5":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n⏹️  Test runner cancelled by user")
            return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
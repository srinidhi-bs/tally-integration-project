#!/usr/bin/env python3
"""
Test Suite for Ledger Information Reading and Parsing

This test suite validates the ledger information extraction and parsing
functionality of the TallyDataReader. It includes tests for XML parsing,
data model population, Qt table models, and integration with TallyPrime.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

import sys
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal

# Add the tally_gui_app directory to sys.path for imports
current_dir = Path(__file__).parent
tally_gui_app_dir = current_dir.parent.parent
sys.path.insert(0, str(tally_gui_app_dir))

# Test imports
from core.tally.data_reader import TallyDataReader, create_data_reader_from_config
from core.models.ledger_model import (
    LedgerInfo, LedgerTableModel, LedgerTreeModel, LedgerType, BalanceType,
    create_sample_ledgers, classify_ledger_type
)


class TestLedgerDataReader:
    """
    Test class for ledger information reading and parsing functionality
    """
    
    def __init__(self):
        """Initialize test environment"""
        # Test configuration for TallyPrime connection
        self.test_config = {
            'host': '172.28.208.1',
            'port': 9000,
            'timeout': 30,
            'retry_count': 2,
            'verbose_logging': True
        }
        
        # Sample XML response for testing ledger list parsing
        self.sample_ledger_xml = """
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Export Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <IMPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>List of Accounts</REPORTNAME>
                    </REQUESTDESC>
                    <REQUESTDATA>
                        <TALLYMESSAGE vchtype="Collection">
                            <LEDGER NAME="Cash" RESERVEDNAME="">
                                <NAME>Cash</NAME>
                                <PARENT>Cash-in-Hand</PARENT>
                                <CLOSINGBALANCE>25000.00 Dr</CLOSINGBALANCE>
                                <OPENINGBALANCE>20000.00 Dr</OPENINGBALANCE>
                            </LEDGER>
                            <LEDGER NAME="HDFC Bank" RESERVEDNAME="">
                                <NAME>HDFC Bank</NAME>
                                <ALIAS>HDFC</ALIAS>
                                <PARENT>Bank Accounts</PARENT>
                                <CLOSINGBALANCE>150000.50 Dr</CLOSINGBALANCE>
                                <OPENINGBALANCE>100000.00 Dr</OPENINGBALANCE>
                                <BANKNAME>HDFC Bank Limited</BANKNAME>
                                <ACCOUNTNUMBER>12345678901234</ACCOUNTNUMBER>
                                <IFSCCODE>HDFC0001234</IFSCCODE>
                            </LEDGER>
                            <LEDGER NAME="ABC Enterprises" RESERVEDNAME="">
                                <NAME>ABC Enterprises</NAME>
                                <PARENT>Sundry Debtors</PARENT>
                                <CLOSINGBALANCE>35000.00 Dr</CLOSINGBALANCE>
                                <GSTIN>29ABCDE1234F1Z5</GSTIN>
                                <EMAIL>contact@abcenterprises.com</EMAIL>
                                <PHONENUMBER>080-12345678</PHONENUMBER>
                                <CREDITLIMIT>50000.00</CREDITLIMIT>
                                <ISBILLWISEON>Yes</ISBILLWISEON>
                            </LEDGER>
                            <LEDGER NAME="XYZ Suppliers" RESERVEDNAME="">
                                <NAME>XYZ Suppliers</NAME>
                                <PARENT>Sundry Creditors</PARENT>
                                <CLOSINGBALANCE>20000.00 Cr</CLOSINGBALANCE>
                                <GSTIN>29XYZDE5678F2Z3</GSTIN>
                                <PAN>XYZDE5678F</PAN>
                            </LEDGER>
                            <LEDGER NAME="Sales Account" RESERVEDNAME="">
                                <NAME>Sales Account</NAME>
                                <PARENT>Sales Accounts</PARENT>
                                <CLOSINGBALANCE>500000.00 Cr</CLOSINGBALANCE>
                                <ISREVENUE>Yes</ISREVENUE>
                            </LEDGER>
                            <LEDGER NAME="Office Rent" RESERVEDNAME="">
                                <NAME>Office Rent</NAME>
                                <PARENT>Indirect Expenses</PARENT>
                                <CLOSINGBALANCE>18000.00 Dr</CLOSINGBALANCE>
                            </LEDGER>
                        </TALLYMESSAGE>
                    </REQUESTDATA>
                </IMPORTDATA>
            </BODY>
        </ENVELOPE>
        """
    
    
    def test_ledger_xml_parsing(self):
        """Test ledger XML parsing functionality"""
        print("\n=== Testing Ledger XML Parsing ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test XML parsing
            ledgers = reader.parse_ledger_list(self.sample_ledger_xml)
            
            # Verify parsing results
            assert len(ledgers) == 6, f"Expected 6 ledgers, got {len(ledgers)}"
            
            # Test specific ledger parsing
            ledger_names = [ledger.name for ledger in ledgers]
            expected_names = ["Cash", "HDFC Bank", "ABC Enterprises", "XYZ Suppliers", "Sales Account", "Office Rent"]
            
            for expected_name in expected_names:
                assert expected_name in ledger_names, f"Missing ledger: {expected_name}"
            
            # Test individual ledger details
            hdfc_ledger = next((l for l in ledgers if l.name == "HDFC Bank"), None)
            assert hdfc_ledger is not None, "HDFC Bank ledger not found"
            assert hdfc_ledger.alias == "HDFC", f"Expected alias 'HDFC', got '{hdfc_ledger.alias}'"
            assert hdfc_ledger.parent_group_name == "Bank Accounts", "Parent group mismatch"
            assert hdfc_ledger.balance.current_balance == Decimal('150000.50'), "Balance mismatch"
            assert hdfc_ledger.balance.balance_type == BalanceType.DEBIT, "Balance type mismatch"
            assert hdfc_ledger.account_number == "12345678901234", "Account number mismatch"
            assert hdfc_ledger.ledger_type == LedgerType.BANK_ACCOUNTS, "Ledger type classification failed"
            
            # Test GST ledger
            abc_ledger = next((l for l in ledgers if l.name == "ABC Enterprises"), None)
            assert abc_ledger is not None, "ABC Enterprises ledger not found"
            assert abc_ledger.tax_info.gstin == "29ABCDE1234F1Z5", "GSTIN mismatch"
            assert abc_ledger.contact_info.email == "contact@abcenterprises.com", "Email mismatch"
            assert abc_ledger.credit_limit == Decimal('50000.00'), "Credit limit mismatch"
            assert abc_ledger.is_bill_wise_on == True, "Bill-wise flag should be True"
            assert abc_ledger.ledger_type == LedgerType.SUNDRY_DEBTORS, "Ledger type should be debtors"
            
            # Test credit balance ledger
            xyz_ledger = next((l for l in ledgers if l.name == "XYZ Suppliers"), None)
            assert xyz_ledger is not None, "XYZ Suppliers ledger not found"
            assert xyz_ledger.balance.balance_type == BalanceType.CREDIT, "Should be credit balance"
            assert xyz_ledger.balance.current_balance == Decimal('20000.00'), "Credit balance amount mismatch"
            assert xyz_ledger.ledger_type == LedgerType.SUNDRY_CREDITORS, "Ledger type should be creditors"
            
            # Test revenue ledger
            sales_ledger = next((l for l in ledgers if l.name == "Sales Account"), None)
            assert sales_ledger is not None, "Sales Account ledger not found"
            assert sales_ledger.is_revenue == True, "Should be marked as revenue"
            assert sales_ledger.ledger_type == LedgerType.SALES_ACCOUNTS, "Should be sales account type"
            
            print(f"✅ Ledger XML parsing successful")
            print(f"   - Parsed {len(ledgers)} ledgers")
            print(f"   - Bank ledger: {hdfc_ledger.name} ({hdfc_ledger.get_balance_display()})")
            print(f"   - Debtor ledger: {abc_ledger.name} (GST: {abc_ledger.tax_info.gstin})")
            print(f"   - Creditor ledger: {xyz_ledger.name} ({xyz_ledger.get_balance_display()})")
            
            return ledgers
            
        except Exception as e:
            print(f"❌ Ledger XML parsing test failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    
    def test_ledger_classification(self):
        """Test ledger type classification functionality"""
        print("\n=== Testing Ledger Classification ===")
        
        try:
            # Test various classification scenarios
            test_cases = [
                ("Bank Accounts", "HDFC Bank", LedgerType.BANK_ACCOUNTS),
                ("Cash-in-Hand", "Cash", LedgerType.CASH),
                ("Sundry Debtors", "ABC Enterprises", LedgerType.SUNDRY_DEBTORS),
                ("Sundry Creditors", "XYZ Suppliers", LedgerType.SUNDRY_CREDITORS),
                ("Sales Accounts", "Sales Account", LedgerType.SALES_ACCOUNTS),
                ("Purchase Accounts", "Purchase Account", LedgerType.PURCHASE_ACCOUNTS),
                ("Direct Expenses", "Raw Material", LedgerType.DIRECT_EXPENSES),
                ("Indirect Expenses", "Office Rent", LedgerType.INDIRECT_EXPENSES),
                ("Current Assets", "Inventory", LedgerType.CURRENT_ASSETS),
                ("Fixed Assets", "Building", LedgerType.FIXED_ASSETS),
                ("Current Liabilities", "Outstanding Expenses", LedgerType.CURRENT_LIABILITIES),
            ]
            
            correct_classifications = 0
            
            for group_name, ledger_name, expected_type in test_cases:
                classified_type = classify_ledger_type(group_name, ledger_name)
                if classified_type == expected_type:
                    correct_classifications += 1
                    print(f"   ✅ {ledger_name} -> {classified_type.value}")
                else:
                    print(f"   ❌ {ledger_name} -> Expected: {expected_type.value}, Got: {classified_type.value}")
            
            accuracy = (correct_classifications / len(test_cases)) * 100
            print(f"   Classification Accuracy: {accuracy:.1f}% ({correct_classifications}/{len(test_cases)})")
            
            assert accuracy >= 90, f"Classification accuracy too low: {accuracy}%"
            
            print(f"✅ Ledger classification test successful")
            return True
            
        except Exception as e:
            print(f"❌ Ledger classification test failed: {e}")
            return False
    
    
    def test_ledger_table_model(self):
        """Test Qt table model for ledger display"""
        print("\n=== Testing Ledger Table Model ===")
        
        try:
            # Create sample ledgers
            sample_ledgers = create_sample_ledgers()
            
            # Create table model
            table_model = LedgerTableModel(sample_ledgers)
            
            # Verify model properties
            assert table_model.rowCount() == len(sample_ledgers), "Row count mismatch"
            assert table_model.columnCount() == 7, "Expected 7 columns"
            
            # Test header data
            from PySide6.QtCore import Qt
            headers = []
            for i in range(table_model.columnCount()):
                header = table_model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                headers.append(header)
            
            expected_headers = ["Ledger Name", "Group", "Balance", "Type", "GST No.", "Last Voucher", "Voucher Count"]
            assert headers == expected_headers, f"Headers mismatch: {headers}"
            
            # Test data display
            first_ledger_name = table_model.data(table_model.index(0, 0), Qt.DisplayRole)
            assert first_ledger_name is not None, "First ledger name should not be None"
            
            # Test balance formatting
            first_balance = table_model.data(table_model.index(0, 2), Qt.DisplayRole)
            assert " Dr" in first_balance or " Cr" in first_balance or first_balance == "0.00", "Balance should be formatted"
            
            # Test filtering functionality
            filter_results = table_model.filter_ledgers("HDFC")
            assert len(filter_results) > 0, "Filter should find matching ledgers"
            
            # Test ledger retrieval
            first_ledger = table_model.get_ledger(table_model.index(0, 0))
            assert first_ledger is not None, "Should be able to retrieve ledger"
            assert isinstance(first_ledger, LedgerInfo), "Should return LedgerInfo instance"
            
            print(f"✅ Ledger table model test successful")
            print(f"   - Rows: {table_model.rowCount()}")
            print(f"   - Columns: {table_model.columnCount()}")
            print(f"   - First ledger: {first_ledger_name}")
            print(f"   - First balance: {first_balance}")
            
            return table_model
            
        except Exception as e:
            print(f"❌ Ledger table model test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_ledger_tree_model(self):
        """Test Qt tree model for hierarchical ledger display"""
        print("\n=== Testing Ledger Tree Model ===")
        
        try:
            # Create sample ledgers
            sample_ledgers = create_sample_ledgers()
            
            # Create tree model
            tree_model = LedgerTreeModel(sample_ledgers)
            
            # Verify model properties
            assert tree_model.rowCount() > 0, "Tree model should have root groups"
            assert tree_model.columnCount() == 4, "Expected 4 columns for tree"
            
            # Test root level (groups)
            from PySide6.QtCore import Qt, QModelIndex
            
            root_index = QModelIndex()
            group_count = tree_model.rowCount(root_index)
            assert group_count > 0, "Should have at least one group"
            
            # Test first group
            first_group_index = tree_model.index(0, 0, root_index)
            first_group_name = tree_model.data(first_group_index, Qt.DisplayRole)
            assert first_group_name is not None, "Group name should not be None"
            
            # Test ledgers under first group
            ledger_count = tree_model.rowCount(first_group_index)
            if ledger_count > 0:
                first_ledger_index = tree_model.index(0, 0, first_group_index)
                first_ledger_name = tree_model.data(first_ledger_index, Qt.DisplayRole)
                assert first_ledger_name is not None, "Ledger name should not be None"
            
            print(f"✅ Ledger tree model test successful")
            print(f"   - Groups: {group_count}")
            print(f"   - First group: {first_group_name}")
            if ledger_count > 0:
                print(f"   - Ledgers in first group: {ledger_count}")
                print(f"   - First ledger: {first_ledger_name}")
            
            return tree_model
            
        except Exception as e:
            print(f"❌ Ledger tree model test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    async def test_live_ledger_data_reading(self):
        """Test live ledger data reading from TallyPrime (if available)"""
        print("\n=== Testing Live Ledger Data Reading ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test connection first
            connection_result = await reader.connector.test_connection()
            if not connection_result.success:
                print(f"⚠️  TallyPrime not available at {reader.connector.config.url}")
                print(f"   Error: {connection_result.error_message}")
                print("   Skipping live ledger data test...")
                return None
            
            print(f"✅ Connected to TallyPrime at {reader.connector.config.url}")
            
            # Request ledger list
            response = await reader.get_ledger_list()
            
            if response.success:
                print(f"✅ Ledger data request successful")
                print(f"   - Response time: {response.response_time:.3f} seconds")
                print(f"   - Data size: {len(response.data)} bytes")
                
                # Parse the ledger list
                ledgers = reader.parse_ledger_list(response.data)
                
                if ledgers:
                    print(f"✅ Ledger data parsing successful")
                    print(f"   - Total ledgers: {len(ledgers)}")
                    
                    # Analyze ledger types
                    type_counts = {}
                    for ledger in ledgers:
                        ledger_type = ledger.ledger_type.value
                        type_counts[ledger_type] = type_counts.get(ledger_type, 0) + 1
                    
                    print("   - Ledger type distribution:")
                    for ledger_type, count in sorted(type_counts.items()):
                        if count > 0:
                            print(f"     {ledger_type.replace('_', ' ').title()}: {count}")
                    
                    # Show sample ledgers
                    print("   - Sample ledgers:")
                    for i, ledger in enumerate(ledgers[:5]):
                        print(f"     {i+1}. {ledger.name} ({ledger.parent_group_name}) - {ledger.get_balance_display()}")
                    
                    # Count ledgers with balances
                    non_zero_balances = [l for l in ledgers if l.balance.current_balance != 0]
                    print(f"   - Ledgers with balances: {len(non_zero_balances)}")
                    
                    # Count ledgers with GST
                    gst_ledgers = [l for l in ledgers if l.tax_info.gstin]
                    print(f"   - GST registered ledgers: {len(gst_ledgers)}")
                    
                    return ledgers
                else:
                    print("❌ Ledger data parsing failed")
                    print("   Raw XML (first 500 chars):")
                    print(response.data[:500])
                    return None
            else:
                print(f"❌ Ledger data request failed: {response.error_message}")
                return None
                
        except Exception as e:
            print(f"❌ Live ledger data test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_ledger_data_serialization(self):
        """Test ledger data serialization and deserialization"""
        print("\n=== Testing Ledger Data Serialization ===")
        
        try:
            # Create sample ledgers
            original_ledgers = create_sample_ledgers()
            
            # Test individual ledger serialization
            first_ledger = original_ledgers[0]
            ledger_dict = first_ledger.to_dict()
            
            assert isinstance(ledger_dict, dict), "Serialization should return dictionary"
            assert 'name' in ledger_dict, "Dictionary should contain name"
            assert 'balance' in ledger_dict, "Dictionary should contain balance"
            assert 'tax_info' in ledger_dict, "Dictionary should contain tax_info"
            
            # Test deserialization
            restored_ledger = LedgerInfo.from_dict(ledger_dict)
            assert restored_ledger.name == first_ledger.name, "Name should match after deserialization"
            assert restored_ledger.balance.current_balance == first_ledger.balance.current_balance, "Balance should match"
            
            # Test JSON serialization of entire list
            import json
            
            ledger_list_dict = [ledger.to_dict() for ledger in original_ledgers]
            json_string = json.dumps(ledger_list_dict, indent=2, default=str)
            assert len(json_string) > 100, "JSON string should be substantial"
            
            # Test JSON deserialization
            parsed_list = json.loads(json_string)
            restored_ledgers = [LedgerInfo.from_dict(data) for data in parsed_list]
            
            assert len(restored_ledgers) == len(original_ledgers), "List length should be preserved"
            assert restored_ledgers[0].name == original_ledgers[0].name, "First ledger name should match"
            
            print(f"✅ Ledger data serialization successful")
            print(f"   - Individual ledger dict keys: {len(ledger_dict)}")
            print(f"   - JSON size for {len(original_ledgers)} ledgers: {len(json_string)} characters")
            print(f"   - Round-trip preservation: ✅")
            
            return ledger_dict
            
        except Exception as e:
            print(f"❌ Ledger data serialization test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def run_all_tests(self):
        """Run all ledger data reader tests"""
        print("🧪 Running Ledger Data Reader Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test 1: XML Parsing
        results['xml_parsing'] = len(self.test_ledger_xml_parsing()) > 0
        
        # Test 2: Ledger Classification
        results['classification'] = self.test_ledger_classification()
        
        # Test 3: Table Model
        results['table_model'] = self.test_ledger_table_model() is not None
        
        # Test 4: Tree Model
        results['tree_model'] = self.test_ledger_tree_model() is not None
        
        # Test 5: Data Serialization
        results['serialization'] = self.test_ledger_data_serialization() is not None
        
        # Test 6: Live Data Reading (async)
        async def run_live_test():
            result = await self.test_live_ledger_data_reading()
            return result is not None
        
        try:
            results['live_data'] = asyncio.run(run_live_test())
        except Exception as e:
            print(f"Live data test error: {e}")
            results['live_data'] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        print("-" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Ledger data reading functionality is working correctly.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the results above.")
        
        return results


def main():
    """Main test runner"""
    # Initialize Qt Application for model testing
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create and run tests
    test_runner = TestLedgerDataReader()
    results = test_runner.run_all_tests()
    
    # Keep app running briefly to ensure Qt cleanup
    app.processEvents()
    
    return results


if __name__ == "__main__":
    main()
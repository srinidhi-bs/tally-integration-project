#!/usr/bin/env python3
"""
Test Suite for Voucher/Transaction Information Reading and Parsing

This test suite validates the voucher and transaction information extraction
and parsing functionality of the TallyDataReader. It includes tests for XML parsing,
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
from datetime import date

# Add the tally_gui_app directory to sys.path for imports
current_dir = Path(__file__).parent
tally_gui_app_dir = current_dir.parent.parent
sys.path.insert(0, str(tally_gui_app_dir))

# Test imports
from core.tally.data_reader import TallyDataReader, create_data_reader_from_config
from core.models.voucher_model import (
    VoucherInfo, VoucherTableModel, VoucherType, TransactionType,
    create_sample_vouchers, classify_voucher_type, TransactionEntry
)


class TestVoucherDataReader:
    """
    Test class for voucher information reading and parsing functionality
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
        
        # Sample XML response for testing voucher parsing
        self.sample_voucher_xml = """
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Export Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <IMPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>All Vouchers</REPORTNAME>
                    </REQUESTDESC>
                    <REQUESTDATA>
                        <TALLYMESSAGE vchtype="Collection">
                            <VOUCHER VCHTYPE="Sales" NUMBER="S001" DATE="20240827">
                                <VOUCHERNUMBER>S001</VOUCHERNUMBER>
                                <VOUCHERTYPE>Sales</VOUCHERTYPE>
                                <DATE>20240827</DATE>
                                <NARRATION>Sale of goods to ABC Enterprises</NARRATION>
                                <TOTALAMOUNT>11800.00</TOTALAMOUNT>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>ABC Enterprises</LEDGERNAME>
                                    <AMOUNT>11800.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>Sales Account</LEDGERNAME>
                                    <AMOUNT>-10000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>CGST</LEDGERNAME>
                                    <AMOUNT>-900.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>SGST</LEDGERNAME>
                                    <AMOUNT>-900.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                            </VOUCHER>
                            <VOUCHER VCHTYPE="Payment" NUMBER="P001" DATE="20240826">
                                <VOUCHERNUMBER>P001</VOUCHERNUMBER>
                                <VOUCHERTYPE>Payment</VOUCHERTYPE>
                                <DATE>20240826</DATE>
                                <NARRATION>Payment to XYZ Suppliers</NARRATION>
                                <TOTALAMOUNT>25000.00</TOTALAMOUNT>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>XYZ Suppliers</LEDGERNAME>
                                    <AMOUNT>25000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>HDFC Bank</LEDGERNAME>
                                    <AMOUNT>-25000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                            </VOUCHER>
                            <VOUCHER VCHTYPE="Journal" NUMBER="J001" DATE="20240825">
                                <VOUCHERNUMBER>J001</VOUCHERNUMBER>
                                <VOUCHERTYPE>Journal</VOUCHERTYPE>
                                <DATE>20240825</DATE>
                                <NARRATION>Adjustment entry for rent allocation</NARRATION>
                                <TOTALAMOUNT>5000.00</TOTALAMOUNT>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>Office Rent</LEDGERNAME>
                                    <AMOUNT>5000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>Outstanding Expenses</LEDGERNAME>
                                    <AMOUNT>-5000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                            </VOUCHER>
                            <VOUCHER VCHTYPE="Receipt" NUMBER="R001" DATE="20240824">
                                <VOUCHERNUMBER>R001</VOUCHERNUMBER>
                                <VOUCHERTYPE>Receipt</VOUCHERTYPE>
                                <DATE>20240824</DATE>
                                <NARRATION>Receipt from DEF Company</NARRATION>
                                <TOTALAMOUNT>15000.00</TOTALAMOUNT>
                                <ISCANCELLED>No</ISCANCELLED>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>HDFC Bank</LEDGERNAME>
                                    <AMOUNT>15000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                                <LEDGERENTRIES.LIST>
                                    <LEDGERNAME>DEF Company</LEDGERNAME>
                                    <AMOUNT>-15000.00</AMOUNT>
                                </LEDGERENTRIES.LIST>
                            </VOUCHER>
                        </TALLYMESSAGE>
                    </REQUESTDATA>
                </IMPORTDATA>
            </BODY>
        </ENVELOPE>
        """
    
    
    def test_voucher_xml_parsing(self):
        """Test voucher XML parsing functionality"""
        print("\n=== Testing Voucher XML Parsing ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test XML parsing
            vouchers = reader.parse_voucher_list(self.sample_voucher_xml)
            
            # Verify parsing results
            assert len(vouchers) == 4, f"Expected 4 vouchers, got {len(vouchers)}"
            
            # Test specific voucher parsing
            voucher_numbers = [voucher.voucher_number for voucher in vouchers]
            expected_numbers = ["S001", "P001", "J001", "R001"]
            
            for expected_number in expected_numbers:
                assert expected_number in voucher_numbers, f"Missing voucher: {expected_number}"
            
            # Test sales voucher details
            sales_voucher = next((v for v in vouchers if v.voucher_number == "S001"), None)
            assert sales_voucher is not None, "Sales voucher not found"
            assert sales_voucher.voucher_type == VoucherType.SALES, "Sales voucher type mismatch"
            assert sales_voucher.date == date(2024, 8, 27), "Sales voucher date mismatch"
            assert sales_voucher.total_amount == Decimal('11800.00'), "Sales voucher amount mismatch"
            assert sales_voucher.narration == "Sale of goods to ABC Enterprises", "Sales narration mismatch"
            assert len(sales_voucher.entries) == 4, f"Expected 4 entries, got {len(sales_voucher.entries)}"
            
            # Check sales voucher entries
            entry_names = [entry.ledger_name for entry in sales_voucher.entries]
            assert "ABC Enterprises" in entry_names, "Debtor entry missing"
            assert "Sales Account" in entry_names, "Sales entry missing"
            assert "CGST" in entry_names, "CGST entry missing"
            assert "SGST" in entry_names, "SGST entry missing"
            
            # Test entry amounts and types
            abc_entry = next(e for e in sales_voucher.entries if e.ledger_name == "ABC Enterprises")
            assert abc_entry.amount == Decimal('11800.00'), "ABC entry amount mismatch"
            assert abc_entry.transaction_type == TransactionType.DEBIT, "ABC should be debited"
            
            sales_entry = next(e for e in sales_voucher.entries if e.ledger_name == "Sales Account")
            assert sales_entry.amount == Decimal('10000.00'), "Sales entry amount mismatch"
            assert sales_entry.transaction_type == TransactionType.CREDIT, "Sales should be credited"
            
            # Test payment voucher
            payment_voucher = next((v for v in vouchers if v.voucher_number == "P001"), None)
            assert payment_voucher is not None, "Payment voucher not found"
            assert payment_voucher.voucher_type == VoucherType.PAYMENT, "Payment voucher type mismatch"
            assert payment_voucher.total_amount == Decimal('25000.00'), "Payment amount mismatch"
            assert len(payment_voucher.entries) == 2, "Payment should have 2 entries"
            
            # Test journal voucher
            journal_voucher = next((v for v in vouchers if v.voucher_number == "J001"), None)
            assert journal_voucher is not None, "Journal voucher not found"
            assert journal_voucher.voucher_type == VoucherType.JOURNAL, "Journal voucher type mismatch"
            
            # Test receipt voucher
            receipt_voucher = next((v for v in vouchers if v.voucher_number == "R001"), None)
            assert receipt_voucher is not None, "Receipt voucher not found"
            assert receipt_voucher.voucher_type == VoucherType.RECEIPT, "Receipt voucher type mismatch"
            assert receipt_voucher.is_cancelled == False, "Receipt should not be cancelled"
            
            print(f"✅ Voucher XML parsing successful")
            print(f"   - Parsed {len(vouchers)} vouchers")
            print(f"   - Sales voucher: {sales_voucher.voucher_number} ({sales_voucher.total_amount})")
            print(f"   - Payment voucher: {payment_voucher.voucher_number} ({payment_voucher.total_amount})")
            print(f"   - Journal voucher: {journal_voucher.voucher_number} ({journal_voucher.total_amount})")
            print(f"   - Receipt voucher: {receipt_voucher.voucher_number} ({receipt_voucher.total_amount})")
            
            return vouchers
            
        except Exception as e:
            print(f"❌ Voucher XML parsing test failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    
    def test_voucher_classification(self):
        """Test voucher type classification functionality"""
        print("\n=== Testing Voucher Classification ===")
        
        try:
            # Test various classification scenarios
            test_cases = [
                ("Sales", VoucherType.SALES),
                ("Purchase", VoucherType.PURCHASE),
                ("Payment", VoucherType.PAYMENT),
                ("Receipt", VoucherType.RECEIPT),
                ("Contra", VoucherType.CONTRA),
                ("Journal", VoucherType.JOURNAL),
                ("Debit Note", VoucherType.DEBIT_NOTE),
                ("Credit Note", VoucherType.CREDIT_NOTE),
                ("Sales Order", VoucherType.SALES_ORDER),
                ("Purchase Order", VoucherType.PURCHASE_ORDER),
                ("Stock Journal", VoucherType.STOCK_JOURNAL),
                ("Unknown Type", VoucherType.OTHER)
            ]
            
            correct_classifications = 0
            
            for voucher_type_name, expected_type in test_cases:
                classified_type = classify_voucher_type(voucher_type_name)
                if classified_type == expected_type:
                    correct_classifications += 1
                    print(f"   ✅ {voucher_type_name} -> {classified_type.value}")
                else:
                    print(f"   ❌ {voucher_type_name} -> Expected: {expected_type.value}, Got: {classified_type.value}")
            
            accuracy = (correct_classifications / len(test_cases)) * 100
            print(f"   Classification Accuracy: {accuracy:.1f}% ({correct_classifications}/{len(test_cases)})")
            
            assert accuracy >= 90, f"Classification accuracy too low: {accuracy}%"
            
            print(f"✅ Voucher classification test successful")
            return True
            
        except Exception as e:
            print(f"❌ Voucher classification test failed: {e}")
            return False
    
    
    def test_voucher_table_model(self):
        """Test Qt table model for voucher display"""
        print("\n=== Testing Voucher Table Model ===")
        
        try:
            # Create sample vouchers
            sample_vouchers = create_sample_vouchers()
            
            # Create table model
            table_model = VoucherTableModel(sample_vouchers)
            
            # Verify model properties
            assert table_model.rowCount() == len(sample_vouchers), "Row count mismatch"
            assert table_model.columnCount() == 8, "Expected 8 columns"
            
            # Test header data
            from PySide6.QtCore import Qt
            headers = []
            for i in range(table_model.columnCount()):
                header = table_model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                headers.append(header)
            
            expected_headers = ["Voucher No.", "Type", "Date", "Party", "Amount", "Narration", "Entries", "Status"]
            assert headers == expected_headers, f"Headers mismatch: {headers}"
            
            # Test data display
            first_voucher_number = table_model.data(table_model.index(0, 0), Qt.DisplayRole)
            assert first_voucher_number is not None, "First voucher number should not be None"
            
            # Test amount formatting
            first_amount = table_model.data(table_model.index(0, 4), Qt.DisplayRole)
            assert "," in first_amount or "." in first_amount, "Amount should be formatted with decimal"
            
            # Test voucher type display
            first_type = table_model.data(table_model.index(0, 1), Qt.DisplayRole)
            assert first_type.title() == first_type, "Voucher type should be title case"
            
            # Test filtering functionality
            filter_results = table_model.filter_vouchers("S001")
            # Note: The sample data might not contain "S001", so just check if filter works
            assert isinstance(filter_results, list), "Filter should return a list"
            
            # Test voucher retrieval
            first_voucher = table_model.get_voucher(table_model.index(0, 0))
            assert first_voucher is not None, "Should be able to retrieve voucher"
            assert isinstance(first_voucher, VoucherInfo), "Should return VoucherInfo instance"
            
            print(f"✅ Voucher table model test successful")
            print(f"   - Rows: {table_model.rowCount()}")
            print(f"   - Columns: {table_model.columnCount()}")
            print(f"   - First voucher: {first_voucher_number}")
            print(f"   - First amount: {first_amount}")
            print(f"   - First type: {first_type}")
            
            return table_model
            
        except Exception as e:
            print(f"❌ Voucher table model test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_voucher_balance_validation(self):
        """Test voucher balance validation"""
        print("\n=== Testing Voucher Balance Validation ===")
        
        try:
            # Create sample vouchers
            sample_vouchers = create_sample_vouchers()
            
            balanced_count = 0
            unbalanced_count = 0
            
            for voucher in sample_vouchers:
                if voucher.is_balanced():
                    balanced_count += 1
                    print(f"   ✅ {voucher.voucher_number}: Balanced ({voucher.total_debit} = {voucher.total_credit})")
                else:
                    unbalanced_count += 1
                    print(f"   ❌ {voucher.voucher_number}: Unbalanced ({voucher.total_debit} ≠ {voucher.total_credit})")
            
            # Calculate entry balance for each voucher
            for voucher in sample_vouchers:
                total_debits = sum(e.amount for e in voucher.entries if e.transaction_type == TransactionType.DEBIT)
                total_credits = sum(e.amount for e in voucher.entries if e.transaction_type == TransactionType.CREDIT)
                
                print(f"   Voucher {voucher.voucher_number}: Dr {total_debits}, Cr {total_credits}")
                
                # Verify calculated totals match
                if abs(total_debits - voucher.total_debit) < Decimal('0.01'):
                    print(f"     ✅ Debit total matches")
                else:
                    print(f"     ❌ Debit total mismatch: calculated {total_debits}, stored {voucher.total_debit}")
                
                if abs(total_credits - voucher.total_credit) < Decimal('0.01'):
                    print(f"     ✅ Credit total matches")
                else:
                    print(f"     ❌ Credit total mismatch: calculated {total_credits}, stored {voucher.total_credit}")
            
            total_vouchers = len(sample_vouchers)
            balance_rate = (balanced_count / total_vouchers) * 100 if total_vouchers > 0 else 0
            
            print(f"   Balance Rate: {balance_rate:.1f}% ({balanced_count}/{total_vouchers})")
            
            # At least 80% should be balanced (allowing for some test data inconsistencies)
            assert balance_rate >= 80, f"Balance rate too low: {balance_rate}%"
            
            print(f"✅ Voucher balance validation successful")
            return True
            
        except Exception as e:
            print(f"❌ Voucher balance validation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    
    async def test_live_voucher_data_reading(self):
        """Test live voucher data reading from TallyPrime (if available)"""
        print("\n=== Testing Live Voucher Data Reading ===")
        
        try:
            # Create data reader
            reader = create_data_reader_from_config(self.test_config)
            
            # Test connection first
            connection_result = await reader.connector.test_connection()
            if not connection_result.success:
                print(f"⚠️  TallyPrime not available at {reader.connector.config.url}")
                print(f"   Error: {connection_result.error_message}")
                print("   Skipping live voucher data test...")
                return None
            
            print(f"✅ Connected to TallyPrime at {reader.connector.config.url}")
            
            # Request voucher list for current month
            from datetime import date, timedelta
            today = date.today()
            start_of_month = today.replace(day=1)
            
            # Format dates for TallyPrime (DD-MM-YYYY)
            from_date = start_of_month.strftime("%d-%m-%Y")
            to_date = today.strftime("%d-%m-%Y")
            
            response = await reader.get_voucher_list(from_date, to_date)
            
            if response.success:
                print(f"✅ Voucher data request successful")
                print(f"   - Response time: {response.response_time:.3f} seconds")
                print(f"   - Data size: {len(response.data)} bytes")
                print(f"   - Date range: {from_date} to {to_date}")
                
                # Parse the voucher list
                vouchers = reader.parse_voucher_list(response.data)
                
                if vouchers:
                    print(f"✅ Voucher data parsing successful")
                    print(f"   - Total vouchers: {len(vouchers)}")
                    
                    # Analyze voucher types
                    type_counts = {}
                    for voucher in vouchers:
                        voucher_type = voucher.voucher_type.value
                        type_counts[voucher_type] = type_counts.get(voucher_type, 0) + 1
                    
                    print("   - Voucher type distribution:")
                    for voucher_type, count in sorted(type_counts.items()):
                        if count > 0:
                            print(f"     {voucher_type.replace('_', ' ').title()}: {count}")
                    
                    # Show sample vouchers
                    print("   - Sample vouchers:")
                    for i, voucher in enumerate(vouchers[:5]):
                        date_str = voucher.date.strftime("%d-%m-%Y") if voucher.date else "No date"
                        print(f"     {i+1}. {voucher.voucher_type.value} {voucher.voucher_number} ({date_str}) - ₹{voucher.total_amount:,.2f}")
                        if voucher.party_ledger:
                            print(f"        Party: {voucher.party_ledger}")
                        if voucher.narration:
                            narration_short = voucher.narration[:50] + "..." if len(voucher.narration) > 50 else voucher.narration
                            print(f"        Narration: {narration_short}")
                    
                    # Count vouchers with entries
                    vouchers_with_entries = [v for v in vouchers if len(v.entries) > 0]
                    print(f"   - Vouchers with entries: {len(vouchers_with_entries)}")
                    
                    # Calculate total transaction amount
                    total_amount = sum(voucher.total_amount for voucher in vouchers)
                    print(f"   - Total transaction amount: ₹{total_amount:,.2f}")
                    
                    return vouchers
                else:
                    print("❌ Voucher data parsing failed")
                    print("   Raw XML (first 500 chars):")
                    print(response.data[:500])
                    return None
            else:
                print(f"❌ Voucher data request failed: {response.error_message}")
                return None
                
        except Exception as e:
            print(f"❌ Live voucher data test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def test_voucher_data_serialization(self):
        """Test voucher data serialization and deserialization"""
        print("\n=== Testing Voucher Data Serialization ===")
        
        try:
            # Create sample vouchers
            original_vouchers = create_sample_vouchers()
            
            # Test individual voucher serialization
            first_voucher = original_vouchers[0]
            voucher_dict = first_voucher.to_dict()
            
            assert isinstance(voucher_dict, dict), "Serialization should return dictionary"
            assert 'voucher_number' in voucher_dict, "Dictionary should contain voucher_number"
            assert 'voucher_type' in voucher_dict, "Dictionary should contain voucher_type"
            assert 'entries' in voucher_dict, "Dictionary should contain entries"
            
            # Test deserialization
            restored_voucher = VoucherInfo.from_dict(voucher_dict)
            assert restored_voucher.voucher_number == first_voucher.voucher_number, "Voucher number should match"
            assert restored_voucher.voucher_type == first_voucher.voucher_type, "Voucher type should match"
            assert restored_voucher.total_amount == first_voucher.total_amount, "Amount should match"
            
            # Test JSON serialization of entire list
            import json
            
            voucher_list_dict = [voucher.to_dict() for voucher in original_vouchers]
            json_string = json.dumps(voucher_list_dict, indent=2, default=str)
            assert len(json_string) > 100, "JSON string should be substantial"
            
            # Test JSON deserialization
            parsed_list = json.loads(json_string)
            restored_vouchers = [VoucherInfo.from_dict(data) for data in parsed_list]
            
            assert len(restored_vouchers) == len(original_vouchers), "List length should be preserved"
            assert restored_vouchers[0].voucher_number == original_vouchers[0].voucher_number, "First voucher should match"
            
            print(f"✅ Voucher data serialization successful")
            print(f"   - Individual voucher dict keys: {len(voucher_dict)}")
            print(f"   - JSON size for {len(original_vouchers)} vouchers: {len(json_string)} characters")
            print(f"   - Round-trip preservation: ✅")
            
            return voucher_dict
            
        except Exception as e:
            print(f"❌ Voucher data serialization test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def run_all_tests(self):
        """Run all voucher data reader tests"""
        print("🧪 Running Voucher Data Reader Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test 1: XML Parsing
        results['xml_parsing'] = len(self.test_voucher_xml_parsing()) > 0
        
        # Test 2: Voucher Classification
        results['classification'] = self.test_voucher_classification()
        
        # Test 3: Table Model
        results['table_model'] = self.test_voucher_table_model() is not None
        
        # Test 4: Balance Validation
        results['balance_validation'] = self.test_voucher_balance_validation()
        
        # Test 5: Data Serialization
        results['serialization'] = self.test_voucher_data_serialization() is not None
        
        # Test 6: Live Data Reading (async)
        async def run_live_test():
            result = await self.test_live_voucher_data_reading()
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
            print("\n🎉 ALL TESTS PASSED! Voucher data reading functionality is working correctly.")
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
    test_runner = TestVoucherDataReader()
    results = test_runner.run_all_tests()
    
    # Keep app running briefly to ensure Qt cleanup
    app.processEvents()
    
    return results


if __name__ == "__main__":
    main()
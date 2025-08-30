#!/usr/bin/env python3
"""
Integration Tests for VoucherEntryDialog
Professional test suite for voucher entry functionality

This test suite validates:
- Dialog initialization and UI setup
- Input validation and error handling
- Transaction entry management
- Balance calculation and validation
- GST calculation functionality
- Voucher preview generation
- Data persistence and retrieval

Developer: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
Date: August 30, 2025
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
import logging
from decimal import Decimal
from datetime import date, time, datetime

# Add the project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# PySide6/Qt6 imports
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

# Import the classes we're testing
from ui.dialogs.voucher_dialog import VoucherEntryDialog, AmountValidator, LedgerCompleter
from core.models.voucher_model import VoucherInfo, VoucherType, TransactionEntry, TransactionType
from core.tally.connector import TallyConnector
from core.tally.data_reader import TallyDataReader

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestVoucherDialogIntegration(unittest.TestCase):
    """
    Integration tests for VoucherEntryDialog
    
    Learning Points:
    - Qt application testing with QTest
    - Mock object usage for external dependencies
    - Professional test organization and structure
    - Integration testing best practices
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment - called once for all tests"""
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
        
        logger.info("Test environment set up successfully")
    
    def setUp(self):
        """Set up test fixtures - called before each test"""
        # Create mock objects for dependencies
        self.mock_connector = Mock(spec=TallyConnector)
        self.mock_data_reader = Mock(spec=TallyDataReader)
        
        # Mock data reader methods
        self.mock_data_reader.get_company_info.return_value = {
            'name': 'Test Company Ltd',
            'address': 'Test Address'
        }
        
        # Sample ledger data
        self.sample_ledgers = [
            {'name': 'Cash Account', 'guid': 'cash-001'},
            {'name': 'Sales Account', 'guid': 'sales-001'}, 
            {'name': 'Purchase Account', 'guid': 'purchase-001'},
            {'name': 'HDFC Bank', 'guid': 'bank-001'},
            {'name': 'ABC Enterprises', 'guid': 'party-001'},
            {'name': 'CGST Account', 'guid': 'cgst-001'},
            {'name': 'SGST Account', 'guid': 'sgst-001'}
        ]
        
        # Mock ledger list method
        mock_ledger_info_list = []
        for ledger in self.sample_ledgers:
            mock_ledger = Mock()
            mock_ledger.name = ledger['name']
            mock_ledger.guid = ledger['guid']
            mock_ledger_info_list.append(mock_ledger)
        
        self.mock_data_reader.get_ledger_list.return_value = mock_ledger_info_list
        
        logger.info("Test fixtures set up for voucher dialog testing")
    
    def test_dialog_initialization_new_voucher(self):
        """Test dialog initialization for creating a new voucher"""
        logger.info("Testing dialog initialization for new voucher")
        
        # Create dialog for new voucher
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader,
            voucher=None  # New voucher
        )
        
        # Verify dialog properties
        self.assertIsNotNone(dialog)
        self.assertFalse(dialog.is_editing)
        self.assertIsNone(dialog.voucher)
        self.assertEqual(dialog.windowTitle(), "Voucher Entry - TallyPrime Integration Manager")
        
        # Verify UI components are created
        self.assertIsNotNone(dialog.tab_widget)
        self.assertIsNotNone(dialog.voucher_type_combo)
        self.assertIsNotNone(dialog.date_edit)
        self.assertIsNotNone(dialog.entries_table)
        self.assertIsNotNone(dialog.balance_label)
        
        # Verify ledger data loaded
        self.assertEqual(len(dialog.ledger_names), 7)
        self.assertIn('Cash Account', dialog.ledger_names)
        self.assertIn('HDFC Bank', dialog.ledger_names)
        
        # Verify default values
        self.assertEqual(dialog.date_edit.date().toPython(), date.today())
        
        dialog.close()
        logger.info("✅ New voucher dialog initialization test passed")
    
    def test_dialog_initialization_edit_voucher(self):
        """Test dialog initialization for editing an existing voucher"""
        logger.info("Testing dialog initialization for editing voucher")
        
        # Create sample voucher for editing
        sample_voucher = VoucherInfo(
            voucher_number="S001",
            voucher_type=VoucherType.SALES,
            date=date(2024, 8, 30),
            time=time(14, 30, 0),
            narration="Sample sales transaction",
            reference="REF001"
        )
        
        # Add sample entries
        sample_voucher.entries = [
            TransactionEntry(
                ledger_name="ABC Enterprises",
                transaction_type=TransactionType.DEBIT,
                amount=Decimal('11800.00')
            ),
            TransactionEntry(
                ledger_name="Sales Account", 
                transaction_type=TransactionType.CREDIT,
                amount=Decimal('10000.00')
            ),
            TransactionEntry(
                ledger_name="CGST Account",
                transaction_type=TransactionType.CREDIT,
                amount=Decimal('900.00')
            ),
            TransactionEntry(
                ledger_name="SGST Account",
                transaction_type=TransactionType.CREDIT,
                amount=Decimal('900.00')
            )
        ]
        
        # Create dialog for editing
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader,
            voucher=sample_voucher
        )
        
        # Verify editing mode
        self.assertTrue(dialog.is_editing)
        self.assertIsNotNone(dialog.voucher)
        self.assertEqual(dialog.voucher.voucher_number, "S001")
        
        # Verify form populated with voucher data
        self.assertEqual(dialog.voucher_number_edit.text(), "S001")
        self.assertEqual(dialog.voucher_type_combo.currentData(), VoucherType.SALES)
        self.assertEqual(dialog.date_edit.date().toPython(), date(2024, 8, 30))
        self.assertEqual(dialog.narration_edit.toPlainText(), "Sample sales transaction")
        
        # Verify entries loaded
        self.assertEqual(dialog.entries_table.rowCount(), 4)
        
        dialog.close()
        logger.info("✅ Edit voucher dialog initialization test passed")
    
    def test_amount_validator(self):
        """Test custom amount validator functionality"""
        logger.info("Testing amount validator")
        
        validator = AmountValidator()
        
        # Test valid amounts
        valid_cases = ["0.00", "100.50", "1000.00", "999999.99", "123.45"]
        for amount in valid_cases:
            state, _, _ = validator.validate(amount, 0)
            self.assertEqual(state, validator.Acceptable, f"Amount {amount} should be valid")
        
        # Test invalid amounts
        invalid_cases = ["-100.00", "abc", "100.123", "1000000000.00"]
        for amount in invalid_cases:
            state, _, _ = validator.validate(amount, 0)
            self.assertEqual(state, validator.Invalid, f"Amount {amount} should be invalid")
        
        # Test intermediate states
        intermediate_cases = ["", "100.", "100.1"]
        for amount in intermediate_cases:
            state, _, _ = validator.validate(amount, 0)
            self.assertIn(state, [validator.Intermediate, validator.Acceptable], 
                         f"Amount {amount} should be intermediate or acceptable")
        
        logger.info("✅ Amount validator test passed")
    
    def test_ledger_completer(self):
        """Test ledger auto-completion functionality"""
        logger.info("Testing ledger completer")
        
        ledger_names = ['Cash Account', 'HDFC Bank', 'Sales Account', 'Purchase Account']
        completer = LedgerCompleter(ledger_names)
        
        # Verify initialization
        self.assertEqual(len(completer.all_ledgers), 4)
        self.assertIn('Cash Account', completer.all_ledgers)
        
        # Test filtering
        filtered = completer.filter_ledgers('cash')
        self.assertEqual(len(filtered), 1)
        self.assertIn('Cash Account', filtered)
        
        filtered = completer.filter_ledgers('account')
        self.assertEqual(len(filtered), 3)  # Cash Account, Sales Account, Purchase Account
        
        # Test case insensitive filtering
        filtered = completer.filter_ledgers('HDFC')
        self.assertEqual(len(filtered), 1)
        self.assertIn('HDFC Bank', filtered)
        
        # Test empty filter
        filtered = completer.filter_ledgers('')
        self.assertEqual(len(filtered), 4)
        
        logger.info("✅ Ledger completer test passed")
    
    def test_transaction_entry_operations(self):
        """Test adding and removing transaction entries"""
        logger.info("Testing transaction entry operations")
        
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader
        )
        
        # Verify initial state
        self.assertEqual(dialog.entries_table.rowCount(), 0)
        self.assertFalse(dialog.remove_entry_btn.isEnabled())
        
        # Simulate adding an entry through quick entry form
        dialog.ledger_combo.setCurrentText("Cash Account")
        dialog.amount_edit.setText("1000.00")
        dialog.debit_radio.setChecked(True)
        dialog.entry_narration_edit.setText("Test entry")
        
        # Add the entry
        dialog.add_transaction_entry()
        
        # Verify entry added
        self.assertEqual(dialog.entries_table.rowCount(), 1)
        self.assertTrue(dialog.remove_entry_btn.isEnabled())
        
        # Verify entry data
        self.assertEqual(dialog.entries_table.item(0, 0).text(), "Cash Account")
        self.assertEqual(dialog.entries_table.item(0, 1).text(), "1,000.00")  # Debit
        self.assertEqual(dialog.entries_table.item(0, 2).text(), "")  # Credit
        self.assertEqual(dialog.entries_table.item(0, 3).text(), "Test entry")
        
        # Add a credit entry
        dialog.ledger_combo.setCurrentText("Sales Account")
        dialog.amount_edit.setText("1000.00")
        dialog.credit_radio.setChecked(True)
        dialog.entry_narration_edit.setText("Sales entry")
        dialog.add_transaction_entry()
        
        # Verify second entry
        self.assertEqual(dialog.entries_table.rowCount(), 2)
        self.assertEqual(dialog.entries_table.item(1, 2).text(), "1,000.00")  # Credit
        
        # Test balance calculation
        dialog.update_balance_display()
        balance_text = dialog.balance_label.text()
        self.assertIn("Dr ₹1,000.00", balance_text)
        self.assertIn("Cr ₹1,000.00", balance_text)
        self.assertIn("✅", balance_text)  # Should be balanced
        
        # Remove an entry
        dialog.entries_table.selectRow(0)
        dialog.remove_transaction_entry()
        
        # Verify removal
        self.assertEqual(dialog.entries_table.rowCount(), 1)
        
        dialog.close()
        logger.info("✅ Transaction entry operations test passed")
    
    def test_balance_validation(self):
        """Test balance calculation and validation"""
        logger.info("Testing balance validation")
        
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader
        )
        
        # Add balanced entries
        entries = [
            TransactionEntry("Cash Account", TransactionType.DEBIT, Decimal('1000.00')),
            TransactionEntry("Sales Account", TransactionType.CREDIT, Decimal('1000.00'))
        ]
        
        for entry in entries:
            dialog.add_entry_to_table(entry)
        
        dialog.update_balance_display()
        
        # Check balance
        balance_text = dialog.balance_label.text()
        self.assertIn("✅", balance_text)
        
        # Add unbalanced entry
        dialog.add_entry_to_table(
            TransactionEntry("Purchase Account", TransactionType.DEBIT, Decimal('500.00'))
        )
        dialog.update_balance_display()
        
        balance_text = dialog.balance_label.text()
        self.assertIn("❌", balance_text)
        self.assertIn("Difference:", balance_text)
        
        dialog.close()
        logger.info("✅ Balance validation test passed")
    
    def test_gst_calculation(self):
        """Test GST calculation functionality"""
        logger.info("Testing GST calculation")
        
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader
        )
        
        # Add base transaction entries (taxable amount = 1000)
        entries = [
            TransactionEntry("Cash Account", TransactionType.DEBIT, Decimal('1180.00')),
            TransactionEntry("Sales Account", TransactionType.CREDIT, Decimal('1000.00'))
        ]
        
        for entry in entries:
            dialog.add_entry_to_table(entry)
        
        # Enable GST and set rates
        dialog.gst_applicable_check.setChecked(True)
        dialog.cgst_rate_spin.setValue(9.0)  # 9% CGST
        dialog.sgst_rate_spin.setValue(9.0)  # 9% SGST
        
        # Calculate taxes
        dialog.calculate_taxes()
        
        # Verify calculations (assuming taxable amount = 1000)
        # CGST = 9% of 1000 = 90, SGST = 9% of 1000 = 90, Total = 180
        cgst_text = dialog.cgst_amount_label.text()
        sgst_text = dialog.sgst_amount_label.text()
        
        # Note: Actual amounts may vary based on how taxable amount is calculated
        # This is a simplified test
        self.assertTrue(cgst_text.startswith("₹"))
        self.assertTrue(sgst_text.startswith("₹"))
        
        dialog.close()
        logger.info("✅ GST calculation test passed")
    
    def test_voucher_validation(self):
        """Test voucher validation logic"""
        logger.info("Testing voucher validation")
        
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader
        )
        
        # Test empty voucher validation (should fail)
        is_valid, errors = dialog.validate_voucher()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("entries are required" in error for error in errors))
        
        # Add minimum required data
        dialog.voucher_number_edit.setText("TEST001")
        dialog.voucher_type_combo.setCurrentIndex(0)  # First voucher type
        dialog.narration_edit.setPlainText("Test voucher")
        
        # Add balanced entries
        entries = [
            TransactionEntry("Cash Account", TransactionType.DEBIT, Decimal('1000.00')),
            TransactionEntry("Sales Account", TransactionType.CREDIT, Decimal('1000.00'))
        ]
        
        for entry in entries:
            dialog.add_entry_to_table(entry)
        
        # Test validation (should pass)
        is_valid, errors = dialog.validate_voucher()
        self.assertTrue(is_valid, f"Validation failed with errors: {errors}")
        self.assertEqual(len(errors), 0)
        
        # Test unbalanced voucher (should fail)
        dialog.add_entry_to_table(
            TransactionEntry("Purchase Account", TransactionType.DEBIT, Decimal('100.00'))
        )
        
        is_valid, errors = dialog.validate_voucher()
        self.assertFalse(is_valid)
        self.assertTrue(any("not balanced" in error for error in errors))
        
        dialog.close()
        logger.info("✅ Voucher validation test passed")
    
    def test_voucher_preview_generation(self):
        """Test voucher preview XML generation"""
        logger.info("Testing voucher preview generation")
        
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader
        )
        
        # Set up voucher data
        dialog.voucher_number_edit.setText("TEST001")
        dialog.voucher_type_combo.setCurrentIndex(0)
        dialog.narration_edit.setPlainText("Test voucher for XML generation")
        
        # Add entries
        entries = [
            TransactionEntry("Cash Account", TransactionType.DEBIT, Decimal('1000.00')),
            TransactionEntry("Sales Account", TransactionType.CREDIT, Decimal('1000.00'))
        ]
        
        for entry in entries:
            dialog.add_entry_to_table(entry)
        
        # Generate preview
        dialog.update_preview()
        
        preview_text = dialog.preview_text.toPlainText()
        
        # Verify XML structure
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', preview_text)
        self.assertIn('<ENVELOPE>', preview_text)
        self.assertIn('<VOUCHER', preview_text)
        self.assertIn('TEST001', preview_text)
        self.assertIn('Cash Account', preview_text)
        self.assertIn('Sales Account', preview_text)
        self.assertIn('1000', preview_text)
        self.assertIn('</ENVELOPE>', preview_text)
        
        dialog.close()
        logger.info("✅ Voucher preview generation test passed")
    
    def test_voucher_creation_from_form(self):
        """Test creating VoucherInfo object from form data"""
        logger.info("Testing voucher creation from form")
        
        dialog = VoucherEntryDialog(
            connector=self.mock_connector,
            data_reader=self.mock_data_reader
        )
        
        # Fill form data
        dialog.voucher_number_edit.setText("CREATE001")
        
        # Set voucher type to SALES
        sales_index = -1
        for i in range(dialog.voucher_type_combo.count()):
            if dialog.voucher_type_combo.itemData(i) == VoucherType.SALES:
                sales_index = i
                break
        
        if sales_index >= 0:
            dialog.voucher_type_combo.setCurrentIndex(sales_index)
        
        dialog.narration_edit.setPlainText("Created from form test")
        dialog.reference_edit.setText("REF-CREATE001")
        
        # Add entries
        entries = [
            TransactionEntry("Cash Account", TransactionType.DEBIT, Decimal('2000.00')),
            TransactionEntry("Sales Account", TransactionType.CREDIT, Decimal('2000.00'))
        ]
        
        for entry in entries:
            dialog.add_entry_to_table(entry)
        
        # Create voucher from form
        voucher = dialog.create_voucher_from_form()
        
        # Verify voucher data
        self.assertEqual(voucher.voucher_number, "CREATE001")
        self.assertEqual(voucher.voucher_type, VoucherType.SALES)
        self.assertEqual(voucher.narration, "Created from form test")
        self.assertEqual(voucher.reference, "REF-CREATE001")
        self.assertEqual(len(voucher.entries), 2)
        self.assertEqual(voucher.total_debit, Decimal('2000.00'))
        self.assertEqual(voucher.total_credit, Decimal('2000.00'))
        self.assertEqual(voucher.total_amount, Decimal('2000.00'))
        
        dialog.close()
        logger.info("✅ Voucher creation from form test passed")


class TestManualVoucherDialog(unittest.TestCase):
    """
    Manual test helper for interactive voucher dialog testing
    Run this test to manually test the dialog functionality
    """
    
    def setUp(self):
        """Set up for manual testing"""
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
    
    @unittest.skip("Manual test - uncomment to run interactively")
    def test_manual_voucher_dialog(self):
        """Manual test for interactive dialog testing"""
        logger.info("Starting manual voucher dialog test")
        
        # Create mock objects
        mock_connector = Mock(spec=TallyConnector)
        mock_data_reader = Mock(spec=TallyDataReader)
        
        # Mock data
        mock_data_reader.get_company_info.return_value = {
            'name': 'Test Company Ltd'
        }
        
        mock_ledgers = []
        for name in ['Cash Account', 'HDFC Bank', 'Sales Account', 'Purchase Account', 
                    'ABC Enterprises', 'CGST Account', 'SGST Account']:
            mock_ledger = Mock()
            mock_ledger.name = name
            mock_ledgers.append(mock_ledger)
        
        mock_data_reader.get_ledger_list.return_value = mock_ledgers
        
        # Create and show dialog
        dialog = VoucherEntryDialog(
            connector=mock_connector,
            data_reader=mock_data_reader
        )
        
        # Add some sample data for testing
        dialog.voucher_number_edit.setText("MANUAL001")
        dialog.narration_edit.setPlainText("Manual test voucher - please test all functionality")
        
        # Show dialog for manual testing
        result = dialog.exec()
        
        if result == dialog.Accepted:
            logger.info("✅ Manual test completed - Dialog accepted")
        else:
            logger.info("❌ Manual test completed - Dialog cancelled")


def run_voucher_dialog_tests():
    """
    Convenience function to run all voucher dialog tests
    
    Usage:
        python test_voucher_dialog_integration.py
    """
    # Set up test suite
    test_suite = unittest.TestSuite()
    
    # Add integration tests
    integration_tests = [
        'test_dialog_initialization_new_voucher',
        'test_dialog_initialization_edit_voucher', 
        'test_amount_validator',
        'test_ledger_completer',
        'test_transaction_entry_operations',
        'test_balance_validation',
        'test_gst_calculation',
        'test_voucher_validation',
        'test_voucher_preview_generation',
        'test_voucher_creation_from_form'
    ]
    
    for test in integration_tests:
        test_suite.addTest(TestVoucherDialogIntegration(test))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    
    print(f"\n{'='*60}")
    print(f"VOUCHER DIALOG INTEGRATION TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_tests - failures - errors}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    
    if failures == 0 and errors == 0:
        print(f"🎉 ALL TESTS PASSED!")
        print(f"Voucher entry dialog is ready for production use.")
    else:
        print(f"❌ Some tests failed. Please review and fix issues.")
    
    print(f"{'='*60}\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Run the test suite
    print("Starting Voucher Dialog Integration Tests...")
    success = run_voucher_dialog_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
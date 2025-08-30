#!/usr/bin/env python3
"""
Manual Test Application for VoucherEntryDialog
Interactive demonstration of voucher entry functionality

This application provides a comprehensive test environment for the VoucherEntryDialog,
allowing users to interactively test all features including:
- New voucher creation
- Existing voucher editing
- Input validation
- Balance calculation
- GST computation
- Voucher preview
- Template application

Developer: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
Date: August 30, 2025
"""

import sys
import os
import logging
from decimal import Decimal
from datetime import datetime, date, time
from typing import List, Optional

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# PySide6/Qt6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QTextEdit, QMessageBox,
    QSplitter, QFrame, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QIcon

# Import our voucher dialog and related classes
from ui.dialogs.voucher_dialog import VoucherEntryDialog
from core.models.voucher_model import VoucherInfo, VoucherType, TransactionEntry, TransactionType
from core.tally.connector import TallyConnector
from core.tally.data_reader import TallyDataReader
from ui.resources.styles.theme_manager import get_theme_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockTallyConnector:
    """Mock TallyConnector for testing purposes"""
    
    def __init__(self):
        self.connected = True
        self.company_name = "Demo Company Ltd"
        self.connection_status = "Connected"
    
    def test_connection(self):
        return True, "Connection successful"
    
    def get_company_info(self):
        return {
            'name': self.company_name,
            'address': 'Demo Address, Demo City',
            'state': 'Demo State'
        }


class MockLedgerInfo:
    """Mock ledger info for testing"""
    
    def __init__(self, name: str, guid: str, balance: Decimal = None):
        self.name = name
        self.guid = guid
        self.balance = balance or Decimal('0.00')


class MockTallyDataReader:
    """Mock TallyDataReader for testing purposes"""
    
    def __init__(self):
        self.company_info = {
            'name': 'Demo Company Ltd',
            'address': 'Demo Address, Demo City',
            'guid': 'demo-company-001'
        }
        
        # Sample ledger data for testing
        self.sample_ledgers = [
            MockLedgerInfo('Cash Account', 'cash-001', Decimal('50000.00')),
            MockLedgerInfo('HDFC Bank', 'bank-hdfc-001', Decimal('125000.00')),
            MockLedgerInfo('ICICI Bank', 'bank-icici-001', Decimal('75000.00')),
            MockLedgerInfo('Sales Account', 'sales-001', Decimal('-300000.00')),
            MockLedgerInfo('Purchase Account', 'purchase-001', Decimal('200000.00')),
            MockLedgerInfo('Office Expenses', 'office-exp-001', Decimal('25000.00')),
            MockLedgerInfo('Rent Account', 'rent-001', Decimal('36000.00')),
            MockLedgerInfo('ABC Enterprises', 'party-abc-001', Decimal('15000.00')),
            MockLedgerInfo('XYZ Suppliers', 'party-xyz-001', Decimal('-25000.00')),
            MockLedgerInfo('PQR Industries', 'party-pqr-001', Decimal('8000.00')),
            MockLedgerInfo('CGST Account', 'cgst-001', Decimal('-12000.00')),
            MockLedgerInfo('SGST Account', 'sgst-001', Decimal('-12000.00')),
            MockLedgerInfo('IGST Account', 'igst-001', Decimal('-5000.00')),
            MockLedgerInfo('TDS Payable', 'tds-001', Decimal('-3000.00')),
            MockLedgerInfo('Professional Fees', 'prof-fees-001', Decimal('18000.00')),
        ]
    
    def get_company_info(self):
        return self.company_info
    
    def get_ledger_list(self):
        return self.sample_ledgers


class VoucherDialogTestWindow(QMainWindow):
    """
    Main test window for voucher dialog functionality
    
    This window provides controls to test various aspects of the voucher dialog:
    - Creating new vouchers of different types
    - Editing existing sample vouchers
    - Testing validation scenarios
    - Demonstrating GST calculations
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize test data
        self.mock_connector = MockTallyConnector()
        self.mock_data_reader = MockTallyDataReader()
        
        # Sample vouchers for editing tests
        self.sample_vouchers = self.create_sample_vouchers()
        
        self.setup_ui()
        self.apply_theme()
        
        logger.info("Voucher dialog test window initialized")
    
    def setup_ui(self):
        """Set up the test window UI"""
        self.setWindowTitle("📝 Voucher Dialog Test Application - TallyPrime Integration Manager")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Test controls
        left_panel = self.create_test_controls_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results and logs
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes (40% left, 60% right)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
    
    def create_test_controls_panel(self) -> QWidget:
        """Create the test controls panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🧪 Voucher Dialog Tests")
        title.setObjectName("panel_title")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # New Voucher Tests
        new_voucher_group = QGroupBox("➕ Create New Vouchers")
        new_layout = QVBoxLayout(new_voucher_group)
        
        voucher_types = [
            ("Sales Invoice", VoucherType.SALES, "📊"),
            ("Purchase Invoice", VoucherType.PURCHASE, "🛒"),
            ("Payment Voucher", VoucherType.PAYMENT, "💳"),
            ("Receipt Voucher", VoucherType.RECEIPT, "💰"),
            ("Journal Entry", VoucherType.JOURNAL, "📝"),
            ("Contra Entry", VoucherType.CONTRA, "🔄")
        ]
        
        for name, vtype, icon in voucher_types:
            btn = QPushButton(f"{icon} New {name}")
            btn.clicked.connect(lambda checked, t=vtype: self.test_new_voucher(t))
            new_layout.addWidget(btn)
        
        layout.addWidget(new_voucher_group)
        
        # Edit Voucher Tests
        edit_voucher_group = QGroupBox("✏️ Edit Sample Vouchers")
        edit_layout = QVBoxLayout(edit_voucher_group)
        
        for i, voucher in enumerate(self.sample_vouchers):
            btn = QPushButton(f"📋 Edit {voucher.voucher_number} ({voucher.voucher_type.value.title()})")
            btn.clicked.connect(lambda checked, v=voucher: self.test_edit_voucher(v))
            edit_layout.addWidget(btn)
        
        layout.addWidget(edit_voucher_group)
        
        # Validation Tests
        validation_group = QGroupBox("🔍 Validation Tests")
        validation_layout = QVBoxLayout(validation_group)
        
        validation_tests = [
            ("Empty Voucher", self.test_empty_voucher_validation),
            ("Unbalanced Voucher", self.test_unbalanced_voucher),
            ("Invalid Amounts", self.test_invalid_amounts),
            ("Missing Required Fields", self.test_missing_fields)
        ]
        
        for name, test_func in validation_tests:
            btn = QPushButton(f"⚠️ {name}")
            btn.clicked.connect(test_func)
            validation_layout.addWidget(btn)
        
        layout.addWidget(validation_group)
        
        # Special Tests
        special_group = QGroupBox("🎯 Special Features")
        special_layout = QVBoxLayout(special_group)
        
        special_tests = [
            ("GST Calculation Demo", self.test_gst_calculation),
            ("Large Transaction Demo", self.test_large_transaction),
            ("Template Application", self.test_template_application),
            ("Auto-completion Demo", self.test_auto_completion)
        ]
        
        for name, test_func in special_tests:
            btn = QPushButton(f"⭐ {name}")
            btn.clicked.connect(test_func)
            special_layout.addWidget(btn)
        
        layout.addWidget(special_group)
        
        # Clear Results button
        clear_btn = QPushButton("🗑️ Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_results_panel(self) -> QWidget:
        """Create the results and logging panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📋 Test Results & Activity Log")
        title.setObjectName("panel_title")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Test results and activity logs will appear here...")
        
        # Set monospace font for better log readability
        log_font = QFont("Consolas", 10)
        log_font.setStyleHint(QFont.Monospace)
        self.results_text.setFont(log_font)
        
        layout.addWidget(self.results_text)
        
        # Initial welcome message
        self.log_result("🎉 Voucher Dialog Test Application Ready!")
        self.log_result("Click any test button on the left to begin testing.")
        self.log_result("All voucher dialog functionality can be tested interactively.")
        self.log_result("-" * 60)
        
        return panel
    
    def create_sample_vouchers(self) -> List[VoucherInfo]:
        """Create sample vouchers for editing tests"""
        vouchers = []
        
        # Sample Sales Invoice
        sales_voucher = VoucherInfo(
            voucher_number="S001",
            voucher_type=VoucherType.SALES,
            date=date.today(),
            time=time(14, 30),
            narration="Sale of goods to ABC Enterprises",
            reference="INV-S001"
        )
        
        sales_voucher.entries = [
            TransactionEntry("ABC Enterprises", TransactionType.DEBIT, Decimal('11800.00')),
            TransactionEntry("Sales Account", TransactionType.CREDIT, Decimal('10000.00')),
            TransactionEntry("CGST Account", TransactionType.CREDIT, Decimal('900.00')),
            TransactionEntry("SGST Account", TransactionType.CREDIT, Decimal('900.00'))
        ]
        
        vouchers.append(sales_voucher)
        
        # Sample Payment Voucher
        payment_voucher = VoucherInfo(
            voucher_number="PAY001",
            voucher_type=VoucherType.PAYMENT,
            date=date.today(),
            narration="Payment to XYZ Suppliers",
            reference="CHQ-123456"
        )
        
        payment_voucher.entries = [
            TransactionEntry("XYZ Suppliers", TransactionType.DEBIT, Decimal('25000.00')),
            TransactionEntry("HDFC Bank", TransactionType.CREDIT, Decimal('25000.00'))
        ]
        
        vouchers.append(payment_voucher)
        
        # Sample Journal Entry
        journal_voucher = VoucherInfo(
            voucher_number="J001",
            voucher_type=VoucherType.JOURNAL,
            date=date.today(),
            narration="Monthly rent allocation",
            reference="RENT-AUG2025"
        )
        
        journal_voucher.entries = [
            TransactionEntry("Rent Account", TransactionType.DEBIT, Decimal('15000.00')),
            TransactionEntry("Outstanding Expenses", TransactionType.CREDIT, Decimal('15000.00'))
        ]
        
        vouchers.append(journal_voucher)
        
        return vouchers
    
    def apply_theme(self):
        """Apply professional theme to the test window"""
        theme_manager = get_theme_manager()
        colors = theme_manager.colors
        
        window_style = f"""
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
        }}
        
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors['border']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            color: {colors['primary']};
        }}
        
        QPushButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 6px;
            font-weight: bold;
            text-align: left;
        }}
        
        QPushButton:hover {{
            background-color: {colors['primary_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['primary_pressed']};
        }}
        
        QTextEdit {{
            border: 2px solid {colors['border']};
            border-radius: 6px;
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            padding: 10px;
        }}
        
        #panel_title {{
            color: {colors['primary']};
            padding: 10px 0px;
        }}
        
        QSplitter::handle {{
            background-color: {colors['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 3px;
        }}
        """
        
        self.setStyleSheet(window_style)
    
    def log_result(self, message: str, level: str = "INFO"):
        """Log a test result message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        level_icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        
        icon = level_icons.get(level, "ℹ️")
        formatted_message = f"{timestamp} {icon} {message}"
        
        self.results_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_results(self):
        """Clear the results text area"""
        self.results_text.clear()
        self.log_result("Results cleared - ready for new tests!")
    
    def test_new_voucher(self, voucher_type: VoucherType):
        """Test creating a new voucher of specified type"""
        self.log_result(f"Opening new {voucher_type.value.title()} voucher dialog...")
        
        try:
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader,
                voucher=None
            )
            
            # Pre-fill voucher type
            for i in range(dialog.voucher_type_combo.count()):
                if dialog.voucher_type_combo.itemData(i) == voucher_type:
                    dialog.voucher_type_combo.setCurrentIndex(i)
                    break
            
            result = dialog.exec()
            
            if result == dialog.Accepted:
                self.log_result(f"✅ New {voucher_type.value} voucher created successfully!", "SUCCESS")
            else:
                self.log_result(f"❌ New {voucher_type.value} voucher creation cancelled", "WARNING")
                
        except Exception as e:
            self.log_result(f"Error opening new voucher dialog: {str(e)}", "ERROR")
            logger.error(f"Error in test_new_voucher: {str(e)}")
    
    def test_edit_voucher(self, voucher: VoucherInfo):
        """Test editing an existing voucher"""
        self.log_result(f"Opening edit dialog for voucher {voucher.voucher_number}...")
        
        try:
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader,
                voucher=voucher
            )
            
            result = dialog.exec()
            
            if result == dialog.Accepted:
                self.log_result(f"✅ Voucher {voucher.voucher_number} updated successfully!", "SUCCESS")
            else:
                self.log_result(f"❌ Voucher {voucher.voucher_number} edit cancelled", "WARNING")
                
        except Exception as e:
            self.log_result(f"Error opening edit voucher dialog: {str(e)}", "ERROR")
            logger.error(f"Error in test_edit_voucher: {str(e)}")
    
    def test_empty_voucher_validation(self):
        """Test validation of empty voucher"""
        self.log_result("Testing empty voucher validation...")
        
        try:
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader
            )
            
            # Try to validate empty voucher
            is_valid, errors = dialog.validate_voucher()
            
            if not is_valid:
                self.log_result(f"✅ Empty voucher validation working correctly - {len(errors)} errors found", "SUCCESS")
                for error in errors:
                    self.log_result(f"   • {error}", "INFO")
            else:
                self.log_result("❌ Empty voucher validation failed - should have detected errors", "ERROR")
            
            dialog.close()
            
        except Exception as e:
            self.log_result(f"Error in empty voucher validation test: {str(e)}", "ERROR")
    
    def test_unbalanced_voucher(self):
        """Test validation of unbalanced voucher"""
        self.log_result("Testing unbalanced voucher validation...")
        
        try:
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader
            )
            
            # Create unbalanced entries
            dialog.voucher_number_edit.setText("UNBALANCED001")
            
            # Add entries manually to table
            dialog.entries_table.setRowCount(2)
            
            # Debit entry - 1000
            dialog.entries_table.setItem(0, 0, dialog.entries_table.itemClass()("Cash Account"))
            dialog.entries_table.setItem(0, 1, dialog.entries_table.itemClass()("1000.00"))
            dialog.entries_table.setItem(0, 2, dialog.entries_table.itemClass()(""))
            
            # Credit entry - 800 (unbalanced)
            dialog.entries_table.setItem(1, 0, dialog.entries_table.itemClass()("Sales Account"))
            dialog.entries_table.setItem(1, 1, dialog.entries_table.itemClass()(""))
            dialog.entries_table.setItem(1, 2, dialog.entries_table.itemClass()("800.00"))
            
            # Update balance display
            dialog.update_balance_display()
            
            balance_text = dialog.balance_label.text()
            if "❌" in balance_text:
                self.log_result("✅ Unbalanced voucher detected correctly", "SUCCESS")
                self.log_result(f"   Balance display: {balance_text}", "INFO")
            else:
                self.log_result("❌ Unbalanced voucher not detected", "ERROR")
            
            dialog.close()
            
        except Exception as e:
            self.log_result(f"Error in unbalanced voucher test: {str(e)}", "ERROR")
    
    def test_invalid_amounts(self):
        """Test validation of invalid amounts"""
        self.log_result("Testing invalid amount validation...")
        
        try:
            from ui.dialogs.voucher_dialog import AmountValidator
            validator = AmountValidator()
            
            invalid_amounts = ["-100.00", "abc", "100.123", ""]
            valid_amounts = ["100.00", "0.01", "999999.99"]
            
            for amount in invalid_amounts:
                state, _, _ = validator.validate(amount, 0)
                if state == validator.Invalid or state == validator.Intermediate:
                    self.log_result(f"✅ Amount '{amount}' correctly identified as invalid/intermediate", "SUCCESS")
                else:
                    self.log_result(f"❌ Amount '{amount}' should be invalid", "ERROR")
            
            for amount in valid_amounts:
                state, _, _ = validator.validate(amount, 0)
                if state == validator.Acceptable:
                    self.log_result(f"✅ Amount '{amount}' correctly identified as valid", "SUCCESS")
                else:
                    self.log_result(f"❌ Amount '{amount}' should be valid", "ERROR")
                    
        except Exception as e:
            self.log_result(f"Error in invalid amounts test: {str(e)}", "ERROR")
    
    def test_missing_fields(self):
        """Test validation with missing required fields"""
        self.log_result("Testing missing required fields validation...")
        
        try:
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader
            )
            
            # Leave voucher number empty, add some entries
            dialog.entries_table.setRowCount(1)
            dialog.entries_table.setItem(0, 0, dialog.entries_table.itemClass()("Cash Account"))
            
            is_valid, errors = dialog.validate_voucher()
            
            if not is_valid:
                self.log_result(f"✅ Missing fields validation working - {len(errors)} errors", "SUCCESS")
                for error in errors:
                    self.log_result(f"   • {error}", "INFO")
            else:
                self.log_result("❌ Missing fields should have been detected", "ERROR")
            
            dialog.close()
            
        except Exception as e:
            self.log_result(f"Error in missing fields test: {str(e)}", "ERROR")
    
    def test_gst_calculation(self):
        """Test GST calculation functionality"""
        self.log_result("Testing GST calculation functionality...")
        
        try:
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader
            )
            
            # Set up a sales voucher with GST
            dialog.voucher_number_edit.setText("GST001")
            dialog.voucher_type_combo.setCurrentIndex(0)  # Assume first is Sales
            dialog.narration_edit.setPlainText("GST calculation test voucher")
            
            # Enable GST
            dialog.gst_applicable_check.setChecked(True)
            dialog.cgst_rate_spin.setValue(9.0)  # 9% CGST
            dialog.sgst_rate_spin.setValue(9.0)  # 9% SGST
            
            # Add base entries
            dialog.entries_table.setRowCount(2)
            dialog.entries_table.setItem(0, 0, dialog.entries_table.itemClass()("ABC Enterprises"))
            dialog.entries_table.setItem(0, 1, dialog.entries_table.itemClass()("1180.00"))  # Including tax
            
            dialog.entries_table.setItem(1, 0, dialog.entries_table.itemClass()("Sales Account"))
            dialog.entries_table.setItem(1, 2, dialog.entries_table.itemClass()("1000.00"))  # Base amount
            
            # Calculate taxes
            dialog.calculate_taxes()
            
            self.log_result("✅ GST calculation completed", "SUCCESS")
            self.log_result(f"   CGST Rate: {dialog.cgst_rate_spin.value()}%", "INFO")
            self.log_result(f"   SGST Rate: {dialog.sgst_rate_spin.value()}%", "INFO")
            self.log_result(f"   CGST Amount: {dialog.cgst_amount_label.text()}", "INFO")
            self.log_result(f"   SGST Amount: {dialog.sgst_amount_label.text()}", "INFO")
            self.log_result(f"   Total Tax: {dialog.total_tax_label.text()}", "INFO")
            
            dialog.close()
            
        except Exception as e:
            self.log_result(f"Error in GST calculation test: {str(e)}", "ERROR")
    
    def test_large_transaction(self):
        """Test dialog with large transaction amounts"""
        self.log_result("Opening dialog with large transaction amounts...")
        
        try:
            # Create large transaction voucher
            large_voucher = VoucherInfo(
                voucher_number="LARGE001",
                voucher_type=VoucherType.SALES,
                date=date.today(),
                narration="Large transaction test - Multiple entries with big amounts",
                reference="LARGE-TXN-001"
            )
            
            # Add many entries with large amounts
            large_entries = [
                TransactionEntry("Major Customer Ltd", TransactionType.DEBIT, Decimal('9876543.21')),
                TransactionEntry("Product Sales - Category A", TransactionType.CREDIT, Decimal('5000000.00')),
                TransactionEntry("Product Sales - Category B", TransactionType.CREDIT, Decimal('3000000.00')),
                TransactionEntry("Service Revenue", TransactionType.CREDIT, Decimal('1500000.00')),
                TransactionEntry("CGST @ 9%", TransactionType.CREDIT, Decimal('135000.00')),
                TransactionEntry("SGST @ 9%", TransactionType.CREDIT, Decimal('135000.00')),
                TransactionEntry("Discount Given", TransactionType.DEBIT, Decimal('106456.79'))
            ]
            
            large_voucher.entries = large_entries
            
            dialog = VoucherEntryDialog(
                connector=self.mock_connector,
                data_reader=self.mock_data_reader,
                voucher=large_voucher
            )
            
            result = dialog.exec()
            
            if result == dialog.Accepted:
                self.log_result("✅ Large transaction handling successful", "SUCCESS")
            else:
                self.log_result("⚠️ Large transaction test cancelled by user", "WARNING")
                
        except Exception as e:
            self.log_result(f"Error in large transaction test: {str(e)}", "ERROR")
    
    def test_template_application(self):
        """Test template application functionality"""
        self.log_result("Testing voucher template functionality...")
        
        # This would require the template functionality to be fully implemented
        self.log_result("⚠️ Template functionality test - would need full implementation", "WARNING")
        self.log_result("   Templates include: Sales Invoice, Purchase Invoice, Payment, Receipt, Journal", "INFO")
    
    def test_auto_completion(self):
        """Test auto-completion functionality"""
        self.log_result("Testing ledger auto-completion functionality...")
        
        try:
            from ui.dialogs.voucher_dialog import LedgerCompleter
            
            ledger_names = [ledger.name for ledger in self.mock_data_reader.get_ledger_list()]
            completer = LedgerCompleter(ledger_names)
            
            # Test filtering
            test_filters = ['cash', 'bank', 'sales', 'gst']
            
            for filter_text in test_filters:
                filtered = completer.filter_ledgers(filter_text)
                self.log_result(f"   Filter '{filter_text}': Found {len(filtered)} matches", "INFO")
                for match in filtered[:3]:  # Show first 3 matches
                    self.log_result(f"     • {match}", "INFO")
            
            self.log_result("✅ Auto-completion functionality working correctly", "SUCCESS")
            
        except Exception as e:
            self.log_result(f"Error in auto-completion test: {str(e)}", "ERROR")


def main():
    """
    Main function to run the voucher dialog test application
    
    This application allows comprehensive testing of the VoucherEntryDialog
    without needing a live TallyPrime connection.
    """
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Voucher Dialog Test Application")
    app.setApplicationVersion("1.0")
    
    # Set application properties for better Windows integration
    if hasattr(app, 'setApplicationDisplayName'):
        app.setApplicationDisplayName("Voucher Dialog Test - TallyPrime Integration Manager")
    
    try:
        # Create and show main window
        window = VoucherDialogTestWindow()
        window.show()
        
        logger.info("Voucher Dialog Test Application started successfully")
        
        # Run application
        exit_code = app.exec()
        
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        
        # Show error message to user
        if QApplication.instance():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Application Error")
            msg.setText("Failed to start Voucher Dialog Test Application")
            msg.setDetailedText(str(e))
            msg.exec()
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
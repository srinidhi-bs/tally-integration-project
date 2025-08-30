#!/usr/bin/env python3
"""
Test Application for Voucher Posting Integration

This application tests the complete voucher posting workflow including:
- Voucher creation and validation
- Posting confirmation dialog
- Progress tracking and error handling
- Audit trail logging

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 30, 2025
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from datetime import datetime, date
from decimal import Decimal

# Import project modules
from core.tally.connector import TallyConnector, TallyConnectionConfig
from core.models.voucher_model import VoucherInfo, VoucherType, TransactionEntry, TransactionType
from ui.dialogs.voucher_dialog import VoucherEntryDialog
from ui.dialogs.posting_confirmation_dialog import PostingConfirmationDialog
from core.utils.audit_trail import get_audit_manager, AuditEventType
from ui.resources.styles.theme_manager import get_theme_manager

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class VoucherPostingTestWindow(QMainWindow):
    """
    Test window for voucher posting integration
    
    This window provides a simple interface to test:
    - Voucher creation and editing
    - TallyPrime connection
    - Posting workflow with confirmation
    - Audit trail functionality
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voucher Posting Integration Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize components
        self.connector = None
        self.audit_manager = get_audit_manager()
        
        self.setup_ui()
        self.setup_test_data()
        self.apply_theme()
    
    def setup_ui(self):
        """Set up the test interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("📤 Voucher Posting Integration Test")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Info label
        info_label = QLabel("This application tests the complete voucher posting workflow.")
        info_label.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(info_label)
        
        # Test buttons
        self.test_connection_btn = QPushButton("🔗 Test TallyPrime Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_connection_btn)
        
        self.create_voucher_btn = QPushButton("📝 Create Test Voucher")
        self.create_voucher_btn.clicked.connect(self.create_test_voucher)
        layout.addWidget(self.create_voucher_btn)
        
        self.test_posting_btn = QPushButton("📤 Test Voucher Posting")
        self.test_posting_btn.clicked.connect(self.test_voucher_posting)
        self.test_posting_btn.setEnabled(False)
        layout.addWidget(self.test_posting_btn)
        
        self.view_audit_btn = QPushButton("📋 View Audit Trail")
        self.view_audit_btn.clicked.connect(self.view_audit_trail)
        layout.addWidget(self.view_audit_btn)
        
        # Status display
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(300)
        self.status_display.setReadOnly(True)
        self.status_display.setPlaceholderText("Test results and status updates will appear here...")
        layout.addWidget(self.status_display)
        
        # Connect to audit trail updates
        self.audit_manager.event_logged.connect(self.on_audit_event_logged)
    
    def setup_test_data(self):
        """Set up test data for voucher creation"""
        self.test_voucher = VoucherInfo(
            voucher_number="TEST/001/2025-08",
            voucher_type=VoucherType.SALES,
            date=date.today(),
            narration="Test sales voucher for posting integration"
        )
        
        # Add test entries
        self.test_voucher.entries = [
            TransactionEntry(
                ledger_name="Test Customer",
                transaction_type=TransactionType.DEBIT,
                amount=Decimal('1180.00'),
                narration="Sale amount with tax"
            ),
            TransactionEntry(
                ledger_name="Sales Account",
                transaction_type=TransactionType.CREDIT,
                amount=Decimal('1000.00'),
                narration="Sales value"
            ),
            TransactionEntry(
                ledger_name="CGST Output",
                transaction_type=TransactionType.CREDIT,
                amount=Decimal('90.00'),
                narration="CGST @ 9%"
            ),
            TransactionEntry(
                ledger_name="SGST Output",
                transaction_type=TransactionType.CREDIT,
                amount=Decimal('90.00'),
                narration="SGST @ 9%"
            )
        ]
        
        # Calculate totals
        self.test_voucher.total_debit = sum(
            e.amount for e in self.test_voucher.entries 
            if e.transaction_type == TransactionType.DEBIT
        )
        self.test_voucher.total_credit = sum(
            e.amount for e in self.test_voucher.entries 
            if e.transaction_type == TransactionType.CREDIT
        )
        self.test_voucher.total_amount = max(self.test_voucher.total_debit, self.test_voucher.total_credit)
    
    def apply_theme(self):
        """Apply theme styling"""
        theme_manager = get_theme_manager()
        colors = theme_manager.colors
        
        style = f"""
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
        }}
        
        QPushButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 14px;
        }}
        
        QPushButton:hover {{
            background-color: {colors.get('primary_hover', colors['primary'])};
        }}
        
        QPushButton:pressed {{
            background-color: {colors.get('primary_pressed', colors['primary'])};
        }}
        
        QPushButton:disabled {{
            background-color: {colors.get('disabled', '#cccccc')};
            color: {colors.get('disabled_text', '#999999')};
        }}
        
        QTextEdit {{
            border: 2px solid {colors['border']};
            border-radius: 4px;
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            padding: 8px;
        }}
        """
        
        self.setStyleSheet(style)
    
    def add_status(self, message: str):
        """Add a status message to the display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_display.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        cursor = self.status_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.status_display.setTextCursor(cursor)
    
    def test_connection(self):
        """Test TallyPrime connection"""
        self.add_status("🔗 Testing TallyPrime connection...")
        
        try:
            # Create connector with default settings
            config = TallyConnectionConfig()
            self.connector = TallyConnector(config)
            
            # Test connection
            success = self.connector.test_connection()
            
            if success:
                self.add_status("✅ Connection successful!")
                self.add_status(f"Company: {self.connector.company_info.name if self.connector.company_info else 'Unknown'}")
                self.test_posting_btn.setEnabled(True)
                
                # Log connection event
                self.audit_manager.log_connection_event(
                    success=True,
                    company_name=self.connector.company_info.name if self.connector.company_info else None
                )
            else:
                self.add_status("❌ Connection failed")
                self.add_status("Please check that TallyPrime is running with HTTP-XML enabled")
                
                # Log connection failure
                self.audit_manager.log_connection_event(
                    success=False,
                    error_message="Connection test failed"
                )
                
        except Exception as e:
            self.add_status(f"❌ Connection error: {str(e)}")
            self.audit_manager.log_connection_event(
                success=False,
                error_message=str(e)
            )
    
    def create_test_voucher(self):
        """Create a test voucher using the voucher dialog"""
        self.add_status("📝 Opening voucher creation dialog...")
        
        try:
            # Create voucher dialog
            dialog = VoucherEntryDialog(
                connector=self.connector,
                data_reader=None,  # Not needed for test
                voucher=None,
                parent=self
            )
            
            # Connect signals
            dialog.voucher_created.connect(self.on_voucher_created)
            dialog.voucher_updated.connect(self.on_voucher_updated)
            
            # Show dialog
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                self.add_status("✅ Voucher dialog completed")
            else:
                self.add_status("❌ Voucher dialog cancelled")
                
        except Exception as e:
            self.add_status(f"❌ Error opening voucher dialog: {str(e)}")
            logger.error(f"Error in create_test_voucher: {str(e)}")
    
    def test_voucher_posting(self):
        """Test voucher posting workflow"""
        if not self.connector:
            self.add_status("❌ Please test connection first")
            return
        
        self.add_status("📤 Testing voucher posting workflow...")
        
        try:
            # Create posting confirmation dialog
            dialog = PostingConfirmationDialog(
                voucher=self.test_voucher,
                connector=self.connector,
                parent=self
            )
            
            # Connect signals
            dialog.posting_confirmed.connect(self.on_posting_confirmed)
            dialog.posting_cancelled.connect(self.on_posting_cancelled)
            
            # Show dialog
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                self.add_status("✅ Posting workflow completed")
            else:
                self.add_status("❌ Posting workflow cancelled")
                
        except Exception as e:
            self.add_status(f"❌ Error in posting workflow: {str(e)}")
            logger.error(f"Error in test_voucher_posting: {str(e)}")
    
    def view_audit_trail(self):
        """Display recent audit trail events"""
        self.add_status("📋 Displaying recent audit trail events...")
        
        try:
            recent_events = self.audit_manager.get_recent_events(limit=10)
            
            if not recent_events:
                self.add_status("No audit events found")
                return
            
            self.add_status(f"Found {len(recent_events)} recent events:")
            self.add_status("-" * 50)
            
            for event in recent_events:
                summary = event.get_summary_text()
                self.add_status(summary)
            
            self.add_status("-" * 50)
            
            # Show statistics
            stats = self.audit_manager.get_statistics()
            self.add_status(f"Total events: {stats['total_events']}")
            self.add_status(f"Storage: {stats['storage_location']}")
            
        except Exception as e:
            self.add_status(f"❌ Error viewing audit trail: {str(e)}")
            logger.error(f"Error in view_audit_trail: {str(e)}")
    
    def on_voucher_created(self, voucher: VoucherInfo):
        """Handle voucher created signal"""
        self.add_status(f"✅ Voucher created: {voucher.voucher_number}")
        self.test_voucher = voucher
        
        # Log voucher creation
        self.audit_manager.log_event(
            event_type=AuditEventType.VOUCHER_CREATED,
            description=f"Test voucher {voucher.voucher_number} created",
            voucher_number=voucher.voucher_number
        )
    
    def on_voucher_updated(self, voucher: VoucherInfo):
        """Handle voucher updated signal"""
        self.add_status(f"✅ Voucher updated: {voucher.voucher_number}")
        self.test_voucher = voucher
    
    def on_posting_confirmed(self, voucher: VoucherInfo):
        """Handle posting confirmed signal"""
        self.add_status(f"✅ Voucher posted successfully: {voucher.voucher_number}")
    
    def on_posting_cancelled(self):
        """Handle posting cancelled signal"""
        self.add_status("❌ Voucher posting was cancelled")
    
    def on_audit_event_logged(self, event):
        """Handle real-time audit event logging"""
        # Only show important events in the status display
        if event.severity.value in ['warning', 'error', 'critical']:
            summary = event.get_summary_text()
            self.add_status(f"AUDIT: {summary}")


def main():
    """Main function to run the test application"""
    app = QApplication(sys.argv)
    app.setApplicationName("Voucher Posting Integration Test")
    app.setOrganizationName("TallyPrime Integration Manager")
    
    # Create and show the test window
    window = VoucherPostingTestWindow()
    window.show()
    
    # Add initial status message
    window.add_status("🚀 Voucher Posting Integration Test Application Started")
    window.add_status("Click 'Test TallyPrime Connection' to begin testing")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
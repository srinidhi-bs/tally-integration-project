"""
Voucher Posting Confirmation Dialog for TallyPrime Integration

This module provides a professional confirmation dialog for voucher posting operations
with progress tracking, validation display, and comprehensive user feedback.

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 30, 2025
Framework: PySide6 (Qt6)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QProgressBar, QFrame, QGroupBox, QFormLayout, QScrollArea, QWidget,
    QTabWidget, QPlainTextEdit, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QFont, QColor, QPalette

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from decimal import Decimal

# Import application components
from core.tally.connector import TallyConnector, VoucherPostingResult, PostingProgress, VoucherPostingErrorType
from core.models.voucher_model import VoucherInfo
from ui.resources.styles.theme_manager import get_theme_manager
from core.utils.audit_trail import get_audit_manager, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class PostingWorker(QObject):
    """
    Worker thread for posting voucher to TallyPrime
    Handles the posting operation in a separate thread for responsive UI
    """
    
    # Signals for thread communication
    progress_updated = Signal(PostingProgress)
    posting_completed = Signal(VoucherPostingResult)
    error_occurred = Signal(str)
    
    def __init__(self, connector: TallyConnector, voucher_xml: str, description: str):
        super().__init__()
        self.connector = connector
        self.voucher_xml = voucher_xml
        self.description = description
    
    def start_posting(self):
        """Start the posting operation"""
        try:
            # Connect to connector signals
            self.connector.posting_progress.connect(self.progress_updated.emit)
            self.connector.voucher_posted.connect(self.posting_completed.emit)
            
            # Start posting with validation
            result = self.connector.post_voucher_with_validation(self.voucher_xml, self.description)
            
        except Exception as e:
            logger.error(f"Error in posting worker: {str(e)}")
            self.error_occurred.emit(str(e))


class PostingConfirmationDialog(QDialog):
    """
    Professional voucher posting confirmation dialog
    
    This dialog provides comprehensive confirmation for voucher posting with:
    - Voucher summary and validation
    - Progress tracking during posting
    - Error handling and retry options
    - Success confirmation and results display
    
    Learning Points:
    - Professional confirmation workflow design
    - Threading for responsive UI during operations
    - Comprehensive error handling and user feedback
    - Progress tracking and status updates
    """
    
    # Signals for communication with main application
    posting_confirmed = Signal(VoucherInfo)
    posting_cancelled = Signal()
    
    def __init__(self, voucher: VoucherInfo, connector: TallyConnector = None, parent=None):
        """
        Initialize the posting confirmation dialog
        
        Args:
            voucher: VoucherInfo object to post
            connector: TallyConnector for posting operations
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store references
        self.voucher = voucher
        self.connector = connector
        self.posting_result: Optional[VoucherPostingResult] = None
        self.posting_thread: Optional[QThread] = None
        self.posting_worker: Optional[PostingWorker] = None
        
        # Dialog state
        self.is_posting = False
        self.posting_start_time: Optional[datetime] = None
        
        # UI components
        self.progress_bar: Optional[QProgressBar] = None
        self.progress_label: Optional[QLabel] = None
        self.status_label: Optional[QLabel] = None
        self.voucher_summary_text: Optional[QTextEdit] = None
        self.xml_preview_text: Optional[QPlainTextEdit] = None
        self.validation_text: Optional[QTextEdit] = None
        self.post_button: Optional[QPushButton] = None
        self.cancel_button: Optional[QPushButton] = None
        self.retry_button: Optional[QPushButton] = None
        self.close_button: Optional[QPushButton] = None
        
        # Initialize the dialog
        self.setup_ui()
        self.setup_connections()
        self.apply_theme()
        self.load_voucher_data()
        self.perform_pre_validation()
        
        logger.info(f"PostingConfirmationDialog initialized for voucher: {voucher.voucher_number}")
    
    def setup_ui(self):
        """Set up the user interface with professional layout"""
        self.setWindowTitle("Confirm Voucher Posting - TallyPrime Integration")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(700, 500)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header section
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("📤 Confirm Voucher Posting")
        title_label.setObjectName("dialog_title")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        subtitle_label = QLabel("Review voucher details and confirm posting to TallyPrime")
        subtitle_label.setObjectName("dialog_subtitle")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
        # Progress section (initially hidden)
        self.progress_frame = QFrame()
        self.progress_frame.setFrameStyle(QFrame.StyledPanel)
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Ready to post voucher...")
        self.progress_label.setObjectName("progress_label")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        
        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        main_layout.addWidget(self.progress_frame)
        self.progress_frame.hide()  # Initially hidden
        
        # Content tabs
        self.tab_widget = QTabWidget()
        self.setup_summary_tab()
        self.setup_validation_tab()
        self.setup_xml_preview_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Button section
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        self.post_button = QPushButton("📤 Post to TallyPrime")
        self.post_button.setObjectName("post_button")
        self.post_button.setDefault(True)
        
        self.retry_button = QPushButton("🔄 Retry Posting")
        self.retry_button.setObjectName("retry_button")
        self.retry_button.hide()  # Initially hidden
        
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.setObjectName("cancel_button")
        
        self.close_button = QPushButton("✅ Close")
        self.close_button.setObjectName("close_button")
        self.close_button.hide()  # Initially hidden
        
        button_layout.addStretch()
        button_layout.addWidget(self.post_button)
        button_layout.addWidget(self.retry_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        
        main_layout.addWidget(button_frame)
        
        self.setLayout(main_layout)
    
    def setup_summary_tab(self):
        """Set up the voucher summary tab"""
        summary_widget = QWidget()
        layout = QVBoxLayout(summary_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Voucher details group
        details_group = QGroupBox("📋 Voucher Details")
        details_layout = QFormLayout(details_group)
        
        details_layout.addRow("Voucher Number:", QLabel(self.voucher.voucher_number))
        details_layout.addRow("Voucher Type:", QLabel(self.voucher.voucher_type.value.title()))
        details_layout.addRow("Date:", QLabel(self.voucher.date.strftime("%d-%m-%Y") if self.voucher.date else "Not set"))
        details_layout.addRow("Narration:", QLabel(self.voucher.narration or "No narration"))
        details_layout.addRow("Reference:", QLabel(self.voucher.reference or "No reference"))
        
        layout.addWidget(details_group)
        
        # Transaction summary group
        transaction_group = QGroupBox("💰 Transaction Summary")
        transaction_layout = QFormLayout(transaction_group)
        
        transaction_layout.addRow("Total Debit:", QLabel(f"₹{self.voucher.total_debit:,.2f}"))
        transaction_layout.addRow("Total Credit:", QLabel(f"₹{self.voucher.total_credit:,.2f}"))
        transaction_layout.addRow("Entry Count:", QLabel(str(len(self.voucher.entries))))
        
        # Balance status
        balance_difference = abs(self.voucher.total_debit - self.voucher.total_credit)
        is_balanced = balance_difference < Decimal('0.01')
        balance_status = "✅ Balanced" if is_balanced else f"❌ Unbalanced (Diff: ₹{balance_difference:,.2f})"
        balance_label = QLabel(balance_status)
        balance_label.setObjectName("balance_status")
        transaction_layout.addRow("Balance Status:", balance_label)
        
        layout.addWidget(transaction_group)
        
        # Entries details
        entries_group = QGroupBox("📊 Ledger Entries")
        entries_layout = QVBoxLayout(entries_group)
        
        self.voucher_summary_text = QTextEdit()
        self.voucher_summary_text.setMaximumHeight(200)
        self.voucher_summary_text.setReadOnly(True)
        entries_layout.addWidget(self.voucher_summary_text)
        
        layout.addWidget(entries_group)
        
        layout.addStretch()
        self.tab_widget.addTab(summary_widget, "📋 Summary")
    
    def setup_validation_tab(self):
        """Set up the validation results tab"""
        validation_widget = QWidget()
        layout = QVBoxLayout(validation_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Validation status
        status_group = QGroupBox("✅ Validation Status")
        status_layout = QVBoxLayout(status_group)
        
        self.validation_status_label = QLabel("Performing validation...")
        self.validation_status_label.setObjectName("validation_status")
        status_layout.addWidget(self.validation_status_label)
        
        layout.addWidget(status_group)
        
        # Validation details
        details_group = QGroupBox("📝 Validation Details")
        details_layout = QVBoxLayout(details_group)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setPlaceholderText("Validation results will appear here...")
        details_layout.addWidget(self.validation_text)
        
        layout.addWidget(details_group)
        
        self.tab_widget.addTab(validation_widget, "✅ Validation")
    
    def setup_xml_preview_tab(self):
        """Set up the XML preview tab"""
        xml_widget = QWidget()
        layout = QVBoxLayout(xml_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Preview controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh XML")
        copy_btn = QPushButton("📋 Copy to Clipboard")
        
        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(copy_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # XML preview text
        xml_group = QGroupBox("📄 TallyPrime XML")
        xml_layout = QVBoxLayout(xml_group)
        
        self.xml_preview_text = QPlainTextEdit()
        self.xml_preview_text.setReadOnly(True)
        self.xml_preview_text.setPlaceholderText("Generated TallyPrime XML will appear here...")
        
        # Set monospace font for XML
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.xml_preview_text.setFont(font)
        
        xml_layout.addWidget(self.xml_preview_text)
        
        layout.addWidget(xml_group)
        
        self.tab_widget.addTab(xml_widget, "📄 XML Preview")
        
        # Connect buttons
        refresh_btn.clicked.connect(self.refresh_xml_preview)
        copy_btn.clicked.connect(self.copy_xml_to_clipboard)
    
    def setup_connections(self):
        """Set up signal-slot connections"""
        self.post_button.clicked.connect(self.start_posting)
        self.retry_button.clicked.connect(self.retry_posting)
        self.cancel_button.clicked.connect(self.cancel_posting)
        self.close_button.clicked.connect(self.accept)
        
        logger.info("Signal-slot connections established")
    
    def apply_theme(self):
        """Apply professional theme styling"""
        theme_manager = get_theme_manager()
        colors = theme_manager.colors
        
        dialog_style = f"""
        QDialog {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
        }}
        
        #dialog_title {{
            color: {colors['primary']};
        }}
        
        #dialog_subtitle {{
            color: {colors['text_secondary']};
            font-style: italic;
        }}
        
        #progress_label {{
            font-weight: bold;
            color: {colors['primary']};
        }}
        
        #status_label {{
            color: {colors['text_secondary']};
        }}
        
        #balance_status {{
            font-weight: bold;
        }}
        
        #validation_status {{
            font-weight: bold;
        }}
        
        QPushButton#post_button {{
            background-color: {colors['success']};
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
            border: none;
        }}
        
        QPushButton#post_button:hover {{
            background-color: {colors.get('success_hover', colors['success'])};
        }}
        
        QPushButton#retry_button {{
            background-color: {colors['warning']};
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
            border: none;
        }}
        
        QPushButton#cancel_button {{
            background-color: {colors['error']};
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
            border: none;
        }}
        
        QPushButton#close_button {{
            background-color: {colors['primary']};
            color: white;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
            border: none;
        }}
        
        QProgressBar {{
            border: 2px solid {colors['border']};
            border-radius: 5px;
            background-color: {colors['surface']};
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 3px;
        }}
        
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors['border']};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 5px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {colors['primary']};
        }}
        
        QTextEdit, QPlainTextEdit {{
            border: 2px solid {colors['border']};
            border-radius: 4px;
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            padding: 8px;
        }}
        """
        
        self.setStyleSheet(dialog_style)
        logger.info("Professional theme applied to posting confirmation dialog")
    
    def load_voucher_data(self):
        """Load voucher data into the summary display"""
        if not self.voucher or not self.voucher_summary_text:
            return
        
        # Generate entries summary
        entries_text = []
        entries_text.append("LEDGER ENTRIES:\n" + "="*50)
        
        for i, entry in enumerate(self.voucher.entries, 1):
            entry_type = "DR" if entry.transaction_type.value.upper() == "DEBIT" else "CR"
            entries_text.append(f"{i:2d}. {entry.ledger_name:<30} {entry_type} ₹{entry.amount:>10,.2f}")
            if entry.narration:
                entries_text.append(f"    Narration: {entry.narration}")
        
        entries_text.append("="*50)
        entries_text.append(f"Total Debit:  ₹{self.voucher.total_debit:>10,.2f}")
        entries_text.append(f"Total Credit: ₹{self.voucher.total_credit:>10,.2f}")
        
        self.voucher_summary_text.setPlainText("\n".join(entries_text))
        
        # Generate and display XML preview
        self.refresh_xml_preview()
        
        logger.info("Voucher data loaded into confirmation dialog")
    
    def perform_pre_validation(self):
        """Perform pre-validation of the voucher"""
        if not self.connector:
            self.validation_status_label.setText("⚠️ No connector available - validation skipped")
            self.validation_text.setPlainText("Validation skipped: No TallyConnector available")
            return
        
        try:
            # Generate voucher XML for validation
            voucher_xml = self.generate_voucher_xml()
            
            # Perform validation
            validation_result = self.connector.validate_voucher_before_posting(voucher_xml)
            
            if validation_result.is_valid:
                self.validation_status_label.setText("✅ Validation Passed - Ready to Post")
                self.validation_text.setPlainText("✅ Voucher validation completed successfully.\n\nAll checks passed. The voucher is ready for posting to TallyPrime.")
                self.post_button.setEnabled(True)
            else:
                self.validation_status_label.setText("❌ Validation Failed - Issues Found")
                
                issues_text = ["❌ Voucher validation failed with the following issues:\n"]
                for i, issue in enumerate(validation_result.issues, 1):
                    issues_text.append(f"{i}. {issue}")
                
                if validation_result.warnings:
                    issues_text.append("\n⚠️ Warnings:")
                    for i, warning in enumerate(validation_result.warnings, 1):
                        issues_text.append(f"{i}. {warning}")
                
                self.validation_text.setPlainText("\n".join(issues_text))
                self.post_button.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Error during pre-validation: {str(e)}")
            self.validation_status_label.setText("⚠️ Validation Error")
            self.validation_text.setPlainText(f"⚠️ Error during validation:\n{str(e)}\n\nYou may still attempt to post, but proceed with caution.")
    
    def generate_voucher_xml(self) -> str:
        """Generate TallyPrime XML for the voucher"""
        # This is a simplified version - in practice, you'd use the voucher dialog's method
        xml_parts = [
            f'<VOUCHER VCHTYPE="{self.voucher.voucher_type.value}" ACTION="Create">',
            f'  <DATE>{self.voucher.date.strftime("%Y%m%d") if self.voucher.date else ""}</DATE>',
            f'  <VOUCHERTYPENAME>{self.voucher.voucher_type.value.title()}</VOUCHERTYPENAME>',
            f'  <VOUCHERNUMBER>{self.voucher.voucher_number}</VOUCHERNUMBER>',
            f'  <NARRATION>{self.voucher.narration}</NARRATION>',
            f'  <REFERENCE>{self.voucher.reference}</REFERENCE>',
        ]
        
        # Add ledger entries
        for entry in self.voucher.entries:
            amount_sign = "-" if entry.transaction_type.value.upper() == "DEBIT" else ""
            xml_parts.extend([
                f'  <ALLLEDGERENTRIES.LIST>',
                f'    <LEDGERNAME>{entry.ledger_name}</LEDGERNAME>',
                f'    <ISDEEMEDPOSITIVE>{"Yes" if entry.transaction_type.value.upper() == "DEBIT" else "No"}</ISDEEMEDPOSITIVE>',
                f'    <AMOUNT>{amount_sign}{entry.amount}</AMOUNT>',
                f'  </ALLLEDGERENTRIES.LIST>',
            ])
        
        xml_parts.append('</VOUCHER>')
        
        return '\n'.join(xml_parts)
    
    def refresh_xml_preview(self):
        """Refresh the XML preview display"""
        try:
            voucher_xml = self.generate_voucher_xml()
            self.xml_preview_text.setPlainText(voucher_xml)
        except Exception as e:
            self.xml_preview_text.setPlainText(f"Error generating XML preview:\n{str(e)}")
    
    def copy_xml_to_clipboard(self):
        """Copy XML content to clipboard"""
        from PySide6.QtWidgets import QApplication
        
        xml_content = self.xml_preview_text.toPlainText()
        if xml_content:
            clipboard = QApplication.clipboard()
            clipboard.setText(xml_content)
            
            # Show brief feedback
            original_text = self.xml_preview_text.placeholderText()
            self.xml_preview_text.setPlaceholderText("✅ XML copied to clipboard!")
            
            # Reset after 2 seconds
            QTimer.singleShot(2000, lambda: self.xml_preview_text.setPlaceholderText(original_text))
    
    def start_posting(self):
        """Start the voucher posting process"""
        if not self.connector:
            QMessageBox.warning(self, "Error", "No TallyPrime connector available for posting.")
            return
        
        if self.is_posting:
            return
        
        # Update UI state
        self.is_posting = True
        self.posting_start_time = datetime.now()
        self.progress_frame.show()
        self.post_button.setEnabled(False)
        self.cancel_button.setText("⏸️ Stop")
        
        # Generate voucher XML
        try:
            voucher_xml = self.generate_voucher_xml()
        except Exception as e:
            self.posting_failed(f"Error generating voucher XML: {str(e)}")
            return
        
        # Create worker thread
        self.posting_thread = QThread()
        self.posting_worker = PostingWorker(
            self.connector, 
            voucher_xml, 
            f"Voucher {self.voucher.voucher_number}"
        )
        
        # Move worker to thread
        self.posting_worker.moveToThread(self.posting_thread)
        
        # Connect signals
        self.posting_worker.progress_updated.connect(self.update_posting_progress)
        self.posting_worker.posting_completed.connect(self.posting_completed)
        self.posting_worker.error_occurred.connect(self.posting_failed)
        
        self.posting_thread.started.connect(self.posting_worker.start_posting)
        self.posting_thread.finished.connect(self.posting_thread.deleteLater)
        
        # Start the thread
        self.posting_thread.start()
        
        logger.info(f"Started posting voucher: {self.voucher.voucher_number}")
    
    def update_posting_progress(self, progress: PostingProgress):
        """Update the progress display"""
        self.progress_bar.setValue(progress.progress_percent)
        self.progress_label.setText(f"Step {progress.current_step_number}/{progress.total_steps}: {progress.stage}")
        self.status_label.setText(progress.current_step)
        
        # Update progress bar text
        if progress.elapsed_time > 0:
            self.progress_bar.setFormat(f"{progress.progress_percent}% - {progress.elapsed_time:.1f}s elapsed")
    
    def posting_completed(self, result: VoucherPostingResult):
        """Handle posting completion"""
        self.posting_result = result
        self.is_posting = False
        
        # Clean up thread
        if self.posting_thread and self.posting_thread.isRunning():
            self.posting_thread.quit()
            self.posting_thread.wait()
        
        if result.success:
            # Success
            self.progress_label.setText("✅ Posting Completed Successfully")
            self.status_label.setText(f"Voucher posted successfully - ID: {result.voucher_id}")
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("100% - Completed")
            
            # Log successful posting to audit trail
            audit_manager = get_audit_manager()
            audit_manager.log_voucher_posted(
                voucher_number=self.voucher.voucher_number,
                voucher_id=result.voucher_id or "Unknown",
                response_time_ms=result.response_time * 1000,
                company_name=self.connector.company_info.name if self.connector.company_info else None
            )
            
            # Update buttons
            self.post_button.hide()
            self.cancel_button.hide()
            self.close_button.show()
            
            # Show success message
            success_msg = ("✅ Voucher posted successfully!\n\n" +
                         f"Voucher ID: {result.voucher_id}\n" +
                         f"Posting time: {result.response_time:.2f} seconds")
            QMessageBox.information(self, "Posting Successful", success_msg)
            
            # Emit success signal
            self.posting_confirmed.emit(self.voucher)
            
        else:
            # Failure
            self.posting_failed(result.user_friendly_message, result)
        
        logger.info(f"Posting completed - Success: {result.success}")
    
    def posting_failed(self, error_message: str, result: VoucherPostingResult = None):
        """Handle posting failure"""
        self.is_posting = False
        self.posting_result = result
        
        # Log failed posting to audit trail
        audit_manager = get_audit_manager()
        audit_manager.log_posting_failed(
            voucher_number=self.voucher.voucher_number,
            error_message=error_message,
            error_type=result.error_type.value if result and result.error_type else None,
            company_name=self.connector.company_info.name if self.connector.company_info else None
        )
        
        # Update UI
        self.progress_label.setText("❌ Posting Failed")
        self.status_label.setText(error_message)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Failed")
        
        # Update buttons
        self.post_button.setEnabled(True)
        self.retry_button.show()
        self.cancel_button.setText("❌ Cancel")
        
        # Show error details if available
        if result and result.error_details:
            error_details = "\n".join([f"• {detail}" for detail in result.error_details])
            full_message = f"{error_message}\n\nDetails:\n{error_details}"
        else:
            full_message = error_message
        
        if result and result.error_type:
            suggestion = self.connector.get_posting_suggestion(result.error_type, result.error_message)
            full_message += f"\n\nSuggestion: {suggestion}"
        
        QMessageBox.critical(self, "Posting Failed", full_message)
        
        logger.error(f"Posting failed: {error_message}")
    
    def retry_posting(self):
        """Retry the posting operation"""
        self.retry_button.hide()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("")
        self.start_posting()
    
    def cancel_posting(self):
        """Cancel the posting operation"""
        if self.is_posting:
            # Stop posting
            if self.posting_thread and self.posting_thread.isRunning():
                self.posting_thread.quit()
                self.posting_thread.wait()
            
            self.is_posting = False
            self.progress_label.setText("❌ Posting Cancelled")
            self.status_label.setText("Posting operation was cancelled by user")
            self.progress_bar.setValue(0)
            self.post_button.setEnabled(True)
            self.cancel_button.setText("❌ Cancel")
            
            logger.info("Posting cancelled by user")
        
        # Emit cancelled signal and close dialog
        self.posting_cancelled.emit()
        self.reject()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.is_posting:
            reply = QMessageBox.question(
                self, 
                "Posting in Progress",
                "Voucher posting is in progress. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cancel_posting()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
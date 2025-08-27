#!/usr/bin/env python3
"""
TallyPrime Voucher/Transaction Data Model - Professional Data Structures

This module provides comprehensive data models for TallyPrime voucher and transaction information.
It includes dataclasses for different voucher types, transaction entries, and related details
with Qt6 integration support for professional GUI display.

Key Features:
- Comprehensive voucher type management (Sales, Purchase, Payment, Receipt, etc.)
- Transaction entry structures with debit/credit handling
- GST and tax calculation support
- Bill-wise details and reference management
- Qt6 table models for transaction display
- JSON serialization support for caching

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
import json
import logging

# Qt6 imports for model integration
from PySide6.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, QVariant
from PySide6.QtGui import QColor

# Set up logger for this module
logger = logging.getLogger(__name__)


class VoucherType(Enum):
    """
    Enumeration of different voucher types in TallyPrime
    Each voucher type has specific behavior and validation rules
    """
    # Transaction Vouchers
    SALES = "sales"
    PURCHASE = "purchase"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    CONTRA = "contra"
    JOURNAL = "journal"
    
    # Inventory Vouchers
    SALES_ORDER = "sales_order"
    PURCHASE_ORDER = "purchase_order"
    DELIVERY_NOTE = "delivery_note"
    RECEIPT_NOTE = "receipt_note"
    REJECTION_OUT = "rejection_out"
    REJECTION_IN = "rejection_in"
    STOCK_JOURNAL = "stock_journal"
    
    # Special Vouchers
    DEBIT_NOTE = "debit_note"
    CREDIT_NOTE = "credit_note"
    REVERSING_JOURNAL = "reversing_journal"
    MEMO = "memo"
    
    # System Vouchers
    OPENING_BALANCE = "opening_balance"
    CLOSING_STOCK = "closing_stock"
    
    # Other
    OTHER = "other"


class TransactionType(Enum):
    """
    Enumeration of transaction entry types
    """
    DEBIT = "debit"
    CREDIT = "credit"


class GSTPurpose(Enum):
    """
    Enumeration of GST purposes for transactions
    """
    SALE = "sale"
    PURCHASE = "purchase"
    EXPENSE = "expense"
    REVERSE_CHARGE = "reverse_charge"
    EXPORT = "export"
    IMPORT = "import"
    OTHER = "other"


@dataclass
class VoucherReference:
    """
    Data class representing voucher reference information
    Used for bill-wise details and reference tracking
    """
    reference_type: str = ""           # "New Ref", "Against Ref", etc.
    reference_name: str = ""           # Reference number or name
    reference_date: Optional[date] = None
    reference_amount: Decimal = Decimal('0.00')
    due_date: Optional[date] = None
    
    # Bill-wise details
    bill_allocations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reference to dictionary"""
        return {
            'reference_type': self.reference_type,
            'reference_name': self.reference_name,
            'reference_date': self.reference_date.isoformat() if self.reference_date else None,
            'reference_amount': float(self.reference_amount),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'bill_allocations': self.bill_allocations
        }


@dataclass
class TaxDetails:
    """
    Data class representing tax information for transactions
    Comprehensive GST and other tax handling
    """
    # GST Information
    cgst_rate: Decimal = Decimal('0.00')
    sgst_rate: Decimal = Decimal('0.00')
    igst_rate: Decimal = Decimal('0.00')
    cess_rate: Decimal = Decimal('0.00')
    
    cgst_amount: Decimal = Decimal('0.00')
    sgst_amount: Decimal = Decimal('0.00')
    igst_amount: Decimal = Decimal('0.00')
    cess_amount: Decimal = Decimal('0.00')
    
    # Tax details
    taxable_amount: Decimal = Decimal('0.00')
    total_tax_amount: Decimal = Decimal('0.00')
    
    # GST specific
    gst_purpose: GSTPurpose = GSTPurpose.SALE
    place_of_supply: str = ""
    reverse_charge: bool = False
    
    # Other taxes
    tds_rate: Decimal = Decimal('0.00')
    tds_amount: Decimal = Decimal('0.00')
    tcs_rate: Decimal = Decimal('0.00')
    tcs_amount: Decimal = Decimal('0.00')
    
    def get_total_gst_rate(self) -> Decimal:
        """Get total GST rate"""
        return self.cgst_rate + self.sgst_rate + self.igst_rate + self.cess_rate
    
    def get_total_gst_amount(self) -> Decimal:
        """Get total GST amount"""
        return self.cgst_amount + self.sgst_amount + self.igst_amount + self.cess_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tax details to dictionary"""
        return {
            'cgst_rate': float(self.cgst_rate),
            'sgst_rate': float(self.sgst_rate),
            'igst_rate': float(self.igst_rate),
            'cess_rate': float(self.cess_rate),
            'cgst_amount': float(self.cgst_amount),
            'sgst_amount': float(self.sgst_amount),
            'igst_amount': float(self.igst_amount),
            'cess_amount': float(self.cess_amount),
            'taxable_amount': float(self.taxable_amount),
            'total_tax_amount': float(self.total_tax_amount),
            'gst_purpose': self.gst_purpose.value,
            'place_of_supply': self.place_of_supply,
            'reverse_charge': self.reverse_charge,
            'tds_rate': float(self.tds_rate),
            'tds_amount': float(self.tds_amount),
            'tcs_rate': float(self.tcs_rate),
            'tcs_amount': float(self.tcs_amount)
        }


@dataclass
class InventoryDetails:
    """
    Data class representing inventory information for transactions
    Stock item details, quantities, and rates
    """
    stock_item: str = ""
    quantity: Decimal = Decimal('0.00')
    unit: str = ""
    rate: Decimal = Decimal('0.00')
    amount: Decimal = Decimal('0.00')
    
    # Additional details
    batch: str = ""
    godown: str = ""
    tracking_number: str = ""
    
    # Dimensions (for applicable items)
    length: Decimal = Decimal('0.00')
    width: Decimal = Decimal('0.00')
    height: Decimal = Decimal('0.00')
    
    def get_total_amount(self) -> Decimal:
        """Calculate total amount (quantity * rate)"""
        return self.quantity * self.rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert inventory details to dictionary"""
        return {
            'stock_item': self.stock_item,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'rate': float(self.rate),
            'amount': float(self.amount),
            'batch': self.batch,
            'godown': self.godown,
            'tracking_number': self.tracking_number,
            'length': float(self.length),
            'width': float(self.width),
            'height': float(self.height)
        }


@dataclass
class TransactionEntry:
    """
    Data class representing a single transaction entry (ledger posting)
    Each voucher contains multiple transaction entries that balance
    """
    # Basic entry information
    ledger_name: str = ""
    transaction_type: TransactionType = TransactionType.DEBIT
    amount: Decimal = Decimal('0.00')
    
    # Entry details
    narration: str = ""
    cost_center: str = ""
    cost_category: str = ""
    
    # Reference and bill details
    reference: Optional[VoucherReference] = field(default_factory=VoucherReference)
    
    # Tax information
    tax_details: Optional[TaxDetails] = field(default_factory=TaxDetails)
    
    # Inventory information (for inventory entries)
    inventory_details: List[InventoryDetails] = field(default_factory=list)
    
    # Banking details (for bank entries)
    bank_details: Dict[str, str] = field(default_factory=dict)  # Cheque details, etc.
    
    def get_signed_amount(self) -> Decimal:
        """Get amount with sign based on transaction type"""
        if self.transaction_type == TransactionType.DEBIT:
            return self.amount
        else:
            return -self.amount
    
    def has_inventory(self) -> bool:
        """Check if this entry has inventory details"""
        return len(self.inventory_details) > 0
    
    def has_tax(self) -> bool:
        """Check if this entry has tax details"""
        return self.tax_details and self.tax_details.total_tax_amount > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction entry to dictionary"""
        return {
            'ledger_name': self.ledger_name,
            'transaction_type': self.transaction_type.value,
            'amount': float(self.amount),
            'narration': self.narration,
            'cost_center': self.cost_center,
            'cost_category': self.cost_category,
            'reference': self.reference.to_dict() if self.reference else None,
            'tax_details': self.tax_details.to_dict() if self.tax_details else None,
            'inventory_details': [inv.to_dict() for inv in self.inventory_details],
            'bank_details': self.bank_details
        }


@dataclass
class VoucherInfo:
    """
    Comprehensive data class representing TallyPrime voucher information
    
    This is the main data structure that holds all voucher-related information
    extracted from TallyPrime. It provides a complete representation of the
    transaction with all its entries, references, and calculations.
    """
    # Basic voucher information
    voucher_number: str = ""
    voucher_type: VoucherType = VoucherType.OTHER
    date: Optional[date] = None
    time: Optional[time] = None
    
    # Voucher identification
    guid: str = ""                     # Unique voucher identifier
    master_id: str = ""                # TallyPrime master ID
    voucher_key: str = ""              # Voucher key for updates
    
    # Amount information
    total_amount: Decimal = Decimal('0.00')
    total_debit: Decimal = Decimal('0.00')
    total_credit: Decimal = Decimal('0.00')
    
    # Voucher properties
    narration: str = ""                # Main voucher narration
    reference: str = ""                # Reference number or document
    
    # Party information (for party vouchers)
    party_ledger: str = ""
    party_amount: Decimal = Decimal('0.00')
    
    # Transaction entries
    entries: List[TransactionEntry] = field(default_factory=list)
    
    # Status information
    is_cancelled: bool = False
    is_optional: bool = False
    is_invoice: bool = False
    is_accounting_voucher: bool = True
    is_inventory_voucher: bool = False
    
    # Metadata
    created_by: str = ""
    modified_by: str = ""
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    
    # Additional properties
    company_name: str = ""
    financial_year: str = ""
    
    def get_voucher_display(self) -> str:
        """
        Get formatted voucher display string
        
        Returns:
            Formatted voucher string like "Sales/001/2024-25"
        """
        parts = []
        if self.voucher_type != VoucherType.OTHER:
            parts.append(self.voucher_type.value.title())
        if self.voucher_number:
            parts.append(self.voucher_number)
        if self.date:
            parts.append(self.date.strftime("%d-%m-%Y"))
        
        return "/".join(parts) if parts else "Unknown Voucher"
    
    def is_balanced(self) -> bool:
        """Check if voucher is balanced (total debits = total credits)"""
        return abs(self.total_debit - self.total_credit) < Decimal('0.01')
    
    def get_entry_count(self) -> int:
        """Get number of transaction entries"""
        return len(self.entries)
    
    def get_party_info(self) -> Optional[TransactionEntry]:
        """Get party ledger entry if this is a party voucher"""
        for entry in self.entries:
            if entry.ledger_name == self.party_ledger:
                return entry
        return None
    
    def has_inventory(self) -> bool:
        """Check if voucher has inventory entries"""
        return any(entry.has_inventory() for entry in self.entries)
    
    def has_tax(self) -> bool:
        """Check if voucher has tax entries"""
        return any(entry.has_tax() for entry in self.entries)
    
    def get_total_tax_amount(self) -> Decimal:
        """Get total tax amount across all entries"""
        total = Decimal('0.00')
        for entry in self.entries:
            if entry.tax_details:
                total += entry.tax_details.total_tax_amount
        return total
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert voucher info to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of voucher information
        """
        return {
            'voucher_number': self.voucher_number,
            'voucher_type': self.voucher_type.value,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.isoformat() if self.time else None,
            'guid': self.guid,
            'master_id': self.master_id,
            'voucher_key': self.voucher_key,
            'total_amount': float(self.total_amount),
            'total_debit': float(self.total_debit),
            'total_credit': float(self.total_credit),
            'narration': self.narration,
            'reference': self.reference,
            'party_ledger': self.party_ledger,
            'party_amount': float(self.party_amount),
            'entries': [entry.to_dict() for entry in self.entries],
            'is_cancelled': self.is_cancelled,
            'is_optional': self.is_optional,
            'is_invoice': self.is_invoice,
            'is_accounting_voucher': self.is_accounting_voucher,
            'is_inventory_voucher': self.is_inventory_voucher,
            'created_by': self.created_by,
            'modified_by': self.modified_by,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'company_name': self.company_name,
            'financial_year': self.financial_year
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoucherInfo':
        """
        Create VoucherInfo instance from dictionary
        
        Args:
            data: Dictionary containing voucher information
            
        Returns:
            VoucherInfo instance
        """
        voucher = cls()
        
        # Basic information
        voucher.voucher_number = data.get('voucher_number', '')
        
        # Voucher type
        voucher_type_str = data.get('voucher_type', 'other')
        try:
            voucher.voucher_type = VoucherType(voucher_type_str)
        except ValueError:
            voucher.voucher_type = VoucherType.OTHER
        
        # Date and time
        if data.get('date'):
            voucher.date = datetime.fromisoformat(data['date']).date()
        if data.get('time'):
            voucher.time = datetime.fromisoformat(data['time']).time()
        
        # Amounts
        voucher.total_amount = Decimal(str(data.get('total_amount', 0)))
        voucher.total_debit = Decimal(str(data.get('total_debit', 0)))
        voucher.total_credit = Decimal(str(data.get('total_credit', 0)))
        
        # Other fields
        voucher.guid = data.get('guid', '')
        voucher.narration = data.get('narration', '')
        voucher.party_ledger = data.get('party_ledger', '')
        
        # Entries
        entries_data = data.get('entries', [])
        for entry_data in entries_data:
            entry = TransactionEntry()
            entry.ledger_name = entry_data.get('ledger_name', '')
            entry.transaction_type = TransactionType(entry_data.get('transaction_type', 'debit'))
            entry.amount = Decimal(str(entry_data.get('amount', 0)))
            entry.narration = entry_data.get('narration', '')
            
            voucher.entries.append(entry)
        
        return voucher


class VoucherTableModel(QAbstractTableModel):
    """
    Qt Table Model for displaying voucher information in a professional table
    
    This model provides a structured way to display voucher lists
    in Qt table views with sorting, filtering, and formatting capabilities.
    """
    
    def __init__(self, vouchers: List[VoucherInfo] = None):
        """
        Initialize the voucher table model
        
        Args:
            vouchers: List of VoucherInfo instances to display
        """
        super().__init__()
        self.vouchers = vouchers or []
        self.headers = [
            "Voucher No.", "Type", "Date", "Party", "Amount", 
            "Narration", "Entries", "Status"
        ]
        
        # Color scheme for different voucher types
        self.color_scheme = {
            VoucherType.SALES: QColor("#2E7D32"),         # Green
            VoucherType.PURCHASE: QColor("#D32F2F"),      # Red
            VoucherType.PAYMENT: QColor("#F57C00"),       # Orange
            VoucherType.RECEIPT: QColor("#1976D2"),       # Blue
            VoucherType.JOURNAL: QColor("#7B1FA2"),       # Purple
            VoucherType.CONTRA: QColor("#5D4037")         # Brown
        }
    
    def rowCount(self, parent=QModelIndex()):
        """Return number of vouchers"""
        return len(self.vouchers)
    
    def columnCount(self, parent=QModelIndex()):
        """Return number of columns"""
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        """Return data for display"""
        if not index.isValid() or index.row() >= len(self.vouchers):
            return QVariant()
        
        voucher = self.vouchers[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Voucher No.
                return voucher.voucher_number
            elif column == 1:  # Type
                return voucher.voucher_type.value.title()
            elif column == 2:  # Date
                if voucher.date:
                    return voucher.date.strftime("%d-%m-%Y")
                return ""
            elif column == 3:  # Party
                return voucher.party_ledger
            elif column == 4:  # Amount
                return f"{voucher.total_amount:,.2f}"
            elif column == 5:  # Narration
                return voucher.narration[:50] + "..." if len(voucher.narration) > 50 else voucher.narration
            elif column == 6:  # Entries
                return str(len(voucher.entries))
            elif column == 7:  # Status
                if voucher.is_cancelled:
                    return "Cancelled"
                elif voucher.is_optional:
                    return "Optional"
                else:
                    return "Active"
        
        elif role == Qt.ForegroundRole and column == 1:  # Voucher type color
            return self.color_scheme.get(voucher.voucher_type, QColor("#000000"))
        
        elif role == Qt.TextAlignmentRole:
            if column in [4, 6]:  # Amount and Entries - right aligned
                return Qt.AlignRight | Qt.AlignVCenter
            elif column == 2:  # Date - center aligned
                return Qt.AlignCenter | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.ToolTipRole:
            if column == 0:  # Voucher tooltip
                tooltip_parts = [f"Voucher: {voucher.get_voucher_display()}"]
                if voucher.guid:
                    tooltip_parts.append(f"GUID: {voucher.guid}")
                if voucher.reference:
                    tooltip_parts.append(f"Reference: {voucher.reference}")
                return "\n".join(tooltip_parts)
            elif column == 4:  # Amount tooltip
                tooltip_parts = [f"Total Amount: {voucher.total_amount:,.2f}"]
                if voucher.total_debit != voucher.total_credit:
                    tooltip_parts.append("⚠️ Voucher not balanced!")
                tooltip_parts.append(f"Debits: {voucher.total_debit:,.2f}")
                tooltip_parts.append(f"Credits: {voucher.total_credit:,.2f}")
                return "\n".join(tooltip_parts)
            elif column == 5:  # Full narration
                return voucher.narration
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return QVariant()
    
    def update_vouchers(self, vouchers: List[VoucherInfo]):
        """
        Update the model with new voucher data
        
        Args:
            vouchers: New list of VoucherInfo instances
        """
        self.beginResetModel()
        self.vouchers = vouchers
        self.endResetModel()
        logger.info(f"VoucherTableModel updated with {len(vouchers)} vouchers")
    
    def get_voucher(self, index: QModelIndex) -> Optional[VoucherInfo]:
        """
        Get voucher info for a specific model index
        
        Args:
            index: QModelIndex for the row
            
        Returns:
            VoucherInfo instance or None
        """
        if index.isValid() and index.row() < len(self.vouchers):
            return self.vouchers[index.row()]
        return None
    
    def filter_vouchers(self, filter_text: str = "", voucher_type: Optional[VoucherType] = None,
                       date_from: Optional[date] = None, date_to: Optional[date] = None,
                       min_amount: Optional[Decimal] = None) -> List[int]:
        """
        Filter vouchers based on criteria and return matching row indices
        
        Args:
            filter_text: Text to search in voucher number, party, narration
            voucher_type: Filter by specific voucher type
            date_from: Start date filter
            date_to: End date filter
            min_amount: Minimum amount filter
            
        Returns:
            List of row indices that match the filter criteria
        """
        matching_rows = []
        
        for i, voucher in enumerate(self.vouchers):
            # Text filter
            if filter_text:
                search_text = filter_text.lower()
                if (search_text not in voucher.voucher_number.lower() and 
                    search_text not in voucher.party_ledger.lower() and
                    search_text not in voucher.narration.lower()):
                    continue
            
            # Type filter
            if voucher_type and voucher.voucher_type != voucher_type:
                continue
            
            # Date filters
            if date_from and voucher.date and voucher.date < date_from:
                continue
            if date_to and voucher.date and voucher.date > date_to:
                continue
            
            # Amount filter
            if min_amount and voucher.total_amount < min_amount:
                continue
            
            matching_rows.append(i)
        
        return matching_rows


# Utility functions for voucher data processing

def create_sample_vouchers() -> List[VoucherInfo]:
    """
    Create sample voucher data for testing and development
    
    Returns:
        List of sample VoucherInfo instances
    """
    from datetime import date, datetime, time
    
    vouchers = []
    
    # Sample sales voucher
    sales_voucher = VoucherInfo(
        voucher_number="S001",
        voucher_type=VoucherType.SALES,
        date=date(2024, 8, 27),
        total_amount=Decimal('11800.00'),
        total_debit=Decimal('11800.00'),
        total_credit=Decimal('11800.00'),
        narration="Sale of goods to ABC Enterprises",
        party_ledger="ABC Enterprises",
        party_amount=Decimal('11800.00')
    )
    
    # Add entries
    sales_voucher.entries = [
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
            ledger_name="CGST",
            transaction_type=TransactionType.CREDIT,
            amount=Decimal('900.00')
        ),
        TransactionEntry(
            ledger_name="SGST",
            transaction_type=TransactionType.CREDIT,
            amount=Decimal('900.00')
        )
    ]
    
    vouchers.append(sales_voucher)
    
    # Sample payment voucher
    payment_voucher = VoucherInfo(
        voucher_number="P001",
        voucher_type=VoucherType.PAYMENT,
        date=date(2024, 8, 26),
        total_amount=Decimal('25000.00'),
        total_debit=Decimal('25000.00'),
        total_credit=Decimal('25000.00'),
        narration="Payment to XYZ Suppliers",
        party_ledger="XYZ Suppliers"
    )
    
    payment_voucher.entries = [
        TransactionEntry(
            ledger_name="XYZ Suppliers",
            transaction_type=TransactionType.DEBIT,
            amount=Decimal('25000.00')
        ),
        TransactionEntry(
            ledger_name="HDFC Bank",
            transaction_type=TransactionType.CREDIT,
            amount=Decimal('25000.00')
        )
    ]
    
    vouchers.append(payment_voucher)
    
    # Sample journal voucher
    journal_voucher = VoucherInfo(
        voucher_number="J001",
        voucher_type=VoucherType.JOURNAL,
        date=date(2024, 8, 25),
        total_amount=Decimal('5000.00'),
        total_debit=Decimal('5000.00'),
        total_credit=Decimal('5000.00'),
        narration="Adjustment entry for rent allocation"
    )
    
    journal_voucher.entries = [
        TransactionEntry(
            ledger_name="Office Rent",
            transaction_type=TransactionType.DEBIT,
            amount=Decimal('5000.00')
        ),
        TransactionEntry(
            ledger_name="Outstanding Expenses",
            transaction_type=TransactionType.CREDIT,
            amount=Decimal('5000.00')
        )
    ]
    
    vouchers.append(journal_voucher)
    
    return vouchers


def classify_voucher_type(voucher_type_name: str) -> VoucherType:
    """
    Classify voucher type from TallyPrime voucher type name
    
    Args:
        voucher_type_name: Voucher type name from TallyPrime
        
    Returns:
        Classified VoucherType
    """
    type_lower = voucher_type_name.lower()
    
    if 'sales' in type_lower:
        return VoucherType.SALES
    elif 'purchase' in type_lower:
        return VoucherType.PURCHASE
    elif 'payment' in type_lower:
        return VoucherType.PAYMENT
    elif 'receipt' in type_lower:
        return VoucherType.RECEIPT
    elif 'contra' in type_lower:
        return VoucherType.CONTRA
    elif 'journal' in type_lower:
        return VoucherType.JOURNAL
    elif 'debit' in type_lower and 'note' in type_lower:
        return VoucherType.DEBIT_NOTE
    elif 'credit' in type_lower and 'note' in type_lower:
        return VoucherType.CREDIT_NOTE
    else:
        return VoucherType.OTHER


def calculate_gst_amounts(base_amount: Decimal, cgst_rate: Decimal, 
                         sgst_rate: Decimal, igst_rate: Decimal = Decimal('0.00')) -> TaxDetails:
    """
    Calculate GST amounts from base amount and rates
    
    Args:
        base_amount: Taxable base amount
        cgst_rate: CGST rate percentage
        sgst_rate: SGST rate percentage  
        igst_rate: IGST rate percentage
        
    Returns:
        TaxDetails with calculated amounts
    """
    tax_details = TaxDetails()
    
    tax_details.taxable_amount = base_amount
    tax_details.cgst_rate = cgst_rate
    tax_details.sgst_rate = sgst_rate
    tax_details.igst_rate = igst_rate
    
    # Calculate amounts
    tax_details.cgst_amount = (base_amount * cgst_rate) / Decimal('100')
    tax_details.sgst_amount = (base_amount * sgst_rate) / Decimal('100')
    tax_details.igst_amount = (base_amount * igst_rate) / Decimal('100')
    
    tax_details.total_tax_amount = (tax_details.cgst_amount + 
                                   tax_details.sgst_amount + 
                                   tax_details.igst_amount)
    
    return tax_details
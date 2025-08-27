#!/usr/bin/env python3
"""
TallyPrime Ledger Data Model - Professional Data Structures

This module provides comprehensive data models for TallyPrime ledger information.
It includes dataclasses for ledger accounts, groups, balances, and transactions
with Qt6 integration support for professional GUI display.

Key Features:
- Comprehensive ledger account data structures
- Ledger group hierarchy management
- Balance and transaction history representation
- Qt6 table and tree models for GUI display
- Advanced filtering and search capabilities
- JSON serialization support for caching

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json
import logging

# Qt6 imports for model integration
from PySide6.QtCore import (QObject, QAbstractTableModel, QAbstractItemModel, 
                           Qt, QModelIndex, QVariant, QPersistentModelIndex)
from PySide6.QtGui import QIcon, QColor

# Set up logger for this module
logger = logging.getLogger(__name__)


class LedgerType(Enum):
    """
    Enumeration of different ledger types in TallyPrime
    Used to categorize and handle different account types
    """
    # Asset Ledgers
    FIXED_ASSETS = "fixed_assets"
    CURRENT_ASSETS = "current_assets"
    INVESTMENTS = "investments"
    CASH = "cash"
    BANK_ACCOUNTS = "bank_accounts"
    SUNDRY_DEBTORS = "sundry_debtors"
    STOCK_IN_HAND = "stock_in_hand"
    
    # Liability Ledgers
    CAPITAL_ACCOUNT = "capital_account"
    CURRENT_LIABILITIES = "current_liabilities"
    LOANS_LIABILITY = "loans_liability"
    SUNDRY_CREDITORS = "sundry_creditors"
    DUTIES_AND_TAXES = "duties_and_taxes"
    PROVISIONS = "provisions"
    
    # Income Ledgers
    SALES_ACCOUNTS = "sales_accounts"
    DIRECT_INCOMES = "direct_incomes"
    INDIRECT_INCOMES = "indirect_incomes"
    
    # Expense Ledgers
    PURCHASE_ACCOUNTS = "purchase_accounts"
    DIRECT_EXPENSES = "direct_expenses"
    INDIRECT_EXPENSES = "indirect_expenses"
    
    # Special Ledgers
    SUSPENSE = "suspense"
    ROUNDOFF = "roundoff"
    OTHER = "other"


class BalanceType(Enum):
    """
    Enumeration of balance types for ledger accounts
    """
    DEBIT = "debit"
    CREDIT = "credit"
    ZERO = "zero"


@dataclass
class LedgerBalance:
    """
    Data class representing ledger balance information
    Comprehensive balance structure for accounting display
    """
    opening_balance: Decimal = Decimal('0.00')
    closing_balance: Decimal = Decimal('0.00')
    current_balance: Decimal = Decimal('0.00')
    balance_type: BalanceType = BalanceType.ZERO
    
    # Period-specific balances
    ytd_debit: Decimal = Decimal('0.00')    # Year-to-date debits
    ytd_credit: Decimal = Decimal('0.00')   # Year-to-date credits
    
    # Last transaction details
    last_transaction_date: Optional[date] = None
    last_transaction_amount: Decimal = Decimal('0.00')
    
    def get_balance_display(self) -> str:
        """
        Get formatted balance string for display
        
        Returns:
            Formatted balance with Dr/Cr indication
        """
        if self.current_balance == 0:
            return "0.00"
        
        amount = abs(self.current_balance)
        suffix = " Dr" if self.balance_type == BalanceType.DEBIT else " Cr"
        return f"{amount:,.2f}{suffix}"
    
    def get_net_movement(self) -> Decimal:
        """
        Calculate net movement for the period
        
        Returns:
            Net movement amount (debits - credits)
        """
        return self.ytd_debit - self.ytd_credit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert balance to dictionary for serialization"""
        return {
            'opening_balance': float(self.opening_balance),
            'closing_balance': float(self.closing_balance),
            'current_balance': float(self.current_balance),
            'balance_type': self.balance_type.value,
            'ytd_debit': float(self.ytd_debit),
            'ytd_credit': float(self.ytd_credit),
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'last_transaction_amount': float(self.last_transaction_amount)
        }


@dataclass
class LedgerGroup:
    """
    Data class representing ledger group information
    TallyPrime organizes ledgers in hierarchical groups
    """
    name: str = ""
    alias: str = ""
    parent_group: Optional[str] = None
    group_type: LedgerType = LedgerType.OTHER
    
    # Group properties
    is_system_group: bool = False
    affects_gross_profit: bool = False
    sort_position: int = 0
    
    # Group statistics (filled when group data is loaded)
    ledger_count: int = 0
    total_balance: Decimal = Decimal('0.00')
    
    def get_display_name(self) -> str:
        """
        Get the best display name for the group
        
        Returns:
            Group alias if available, otherwise name
        """
        return self.alias if self.alias else self.name
    
    def get_full_path(self) -> str:
        """
        Get full hierarchical path of the group
        
        Returns:
            Full group path like "Primary/Current Assets/Bank Accounts"
        """
        if self.parent_group:
            return f"{self.parent_group}/{self.name}"
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary for serialization"""
        return {
            'name': self.name,
            'alias': self.alias,
            'parent_group': self.parent_group,
            'group_type': self.group_type.value,
            'is_system_group': self.is_system_group,
            'affects_gross_profit': self.affects_gross_profit,
            'sort_position': self.sort_position,
            'ledger_count': self.ledger_count,
            'total_balance': float(self.total_balance)
        }


@dataclass
class LedgerContact:
    """
    Data class representing contact information for ledgers
    Comprehensive contact details for parties and entities
    """
    contact_person: str = ""
    phone: str = ""
    mobile: str = ""
    email: str = ""
    website: str = ""
    
    # Address details
    address_line1: str = ""
    address_line2: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = ""
    
    def get_formatted_address(self) -> str:
        """Get formatted address string"""
        lines = []
        if self.address_line1: lines.append(self.address_line1)
        if self.address_line2: lines.append(self.address_line2)
        
        city_state = []
        if self.city: city_state.append(self.city)
        if self.state: city_state.append(self.state)
        if city_state: lines.append(", ".join(city_state))
        
        if self.postal_code: lines.append(self.postal_code)
        if self.country: lines.append(self.country)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert contact to dictionary"""
        return {
            'contact_person': self.contact_person,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': self.email,
            'website': self.website,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code
        }


@dataclass
class LedgerTaxInfo:
    """
    Data class representing tax information for ledgers
    Comprehensive tax registration and compliance details
    """
    # GST Information
    gstin: str = ""
    gst_registration_type: str = ""  # Regular, Composition, etc.
    gst_applicable: bool = False
    
    # Tax rates and categories
    tax_rate: Decimal = Decimal('0.00')
    tax_category: str = ""
    hsn_code: str = ""
    
    # Other tax registrations
    pan: str = ""
    tan: str = ""
    vat_number: str = ""
    service_tax_number: str = ""
    
    # Tax exemptions and special cases
    is_tax_exempt: bool = False
    exemption_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tax info to dictionary"""
        return {
            'gstin': self.gstin,
            'gst_registration_type': self.gst_registration_type,
            'gst_applicable': self.gst_applicable,
            'tax_rate': float(self.tax_rate),
            'tax_category': self.tax_category,
            'hsn_code': self.hsn_code,
            'pan': self.pan,
            'tan': self.tan,
            'vat_number': self.vat_number,
            'service_tax_number': self.service_tax_number,
            'is_tax_exempt': self.is_tax_exempt,
            'exemption_reason': self.exemption_reason
        }


@dataclass
class LedgerInfo:
    """
    Comprehensive data class representing TallyPrime ledger information
    
    This is the main data structure that holds all ledger-related information
    extracted from TallyPrime. It provides a complete representation of the
    ledger account, its properties, balances, and related details.
    """
    # Basic ledger information
    name: str = ""
    alias: str = ""
    guid: str = ""                     # Unique ledger identifier
    master_id: str = ""                # TallyPrime master ID
    
    # Ledger categorization
    ledger_type: LedgerType = LedgerType.OTHER
    group: Optional[LedgerGroup] = field(default_factory=LedgerGroup)
    parent_group_name: str = ""        # Parent group name for hierarchy
    
    # Balance information
    balance: LedgerBalance = field(default_factory=LedgerBalance)
    
    # Contact and address information
    contact_info: LedgerContact = field(default_factory=LedgerContact)
    
    # Tax information
    tax_info: LedgerTaxInfo = field(default_factory=LedgerTaxInfo)
    
    # Ledger properties and settings
    is_revenue: bool = False           # Revenue account flag
    is_deemedpositive: bool = False    # Positive balance nature
    is_bill_wise_on: bool = False      # Bill-wise details enabled
    is_cost_centre_on: bool = False    # Cost center allocation enabled
    is_interest_on: bool = False       # Interest calculation enabled
    
    # Banking details (for bank ledgers)
    bank_name: str = ""
    account_number: str = ""
    ifsc_code: str = ""
    branch_name: str = ""
    
    # Credit limit and payment terms (for party ledgers)
    credit_limit: Decimal = Decimal('0.00')
    credit_period: int = 0             # Credit period in days
    
    # Metadata
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    last_voucher_date: Optional[date] = None
    
    # Statistics (filled when ledger data is loaded)
    voucher_count: int = 0
    bill_count: int = 0
    
    def get_display_name(self) -> str:
        """
        Get the best display name for the ledger
        
        Returns:
            Ledger alias if available, otherwise name
        """
        return self.alias if self.alias else self.name
    
    def get_balance_display(self) -> str:
        """Get formatted balance for display"""
        return self.balance.get_balance_display()
    
    def get_group_path(self) -> str:
        """Get full group path"""
        if self.group:
            return self.group.get_full_path()
        return self.parent_group_name
    
    def is_party_ledger(self) -> bool:
        """Check if this is a party ledger (debtors/creditors)"""
        return self.ledger_type in [LedgerType.SUNDRY_DEBTORS, LedgerType.SUNDRY_CREDITORS]
    
    def is_bank_ledger(self) -> bool:
        """Check if this is a bank ledger"""
        return self.ledger_type == LedgerType.BANK_ACCOUNTS or bool(self.account_number)
    
    def has_gst_registration(self) -> bool:
        """Check if ledger has GST registration"""
        return bool(self.tax_info.gstin)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ledger info to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of ledger information
        """
        return {
            'name': self.name,
            'alias': self.alias,
            'guid': self.guid,
            'master_id': self.master_id,
            'ledger_type': self.ledger_type.value,
            'group': self.group.to_dict() if self.group else None,
            'parent_group_name': self.parent_group_name,
            'balance': self.balance.to_dict(),
            'contact_info': self.contact_info.to_dict(),
            'tax_info': self.tax_info.to_dict(),
            'is_revenue': self.is_revenue,
            'is_deemedpositive': self.is_deemedpositive,
            'is_bill_wise_on': self.is_bill_wise_on,
            'is_cost_centre_on': self.is_cost_centre_on,
            'is_interest_on': self.is_interest_on,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'ifsc_code': self.ifsc_code,
            'branch_name': self.branch_name,
            'credit_limit': float(self.credit_limit),
            'credit_period': self.credit_period,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'last_voucher_date': self.last_voucher_date.isoformat() if self.last_voucher_date else None,
            'voucher_count': self.voucher_count,
            'bill_count': self.bill_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LedgerInfo':
        """
        Create LedgerInfo instance from dictionary
        
        Args:
            data: Dictionary containing ledger information
            
        Returns:
            LedgerInfo instance
        """
        ledger = cls()
        
        # Basic information
        ledger.name = data.get('name', '')
        ledger.alias = data.get('alias', '')
        ledger.guid = data.get('guid', '')
        ledger.master_id = data.get('master_id', '')
        
        # Ledger type
        ledger_type_str = data.get('ledger_type', 'other')
        try:
            ledger.ledger_type = LedgerType(ledger_type_str)
        except ValueError:
            ledger.ledger_type = LedgerType.OTHER
        
        ledger.parent_group_name = data.get('parent_group_name', '')
        
        # Balance information
        balance_data = data.get('balance', {})
        if balance_data:
            ledger.balance = LedgerBalance(
                opening_balance=Decimal(str(balance_data.get('opening_balance', 0))),
                closing_balance=Decimal(str(balance_data.get('closing_balance', 0))),
                current_balance=Decimal(str(balance_data.get('current_balance', 0))),
                balance_type=BalanceType(balance_data.get('balance_type', 'zero')),
                ytd_debit=Decimal(str(balance_data.get('ytd_debit', 0))),
                ytd_credit=Decimal(str(balance_data.get('ytd_credit', 0)))
            )
        
        # Contact information
        contact_data = data.get('contact_info', {})
        if contact_data:
            ledger.contact_info = LedgerContact(**contact_data)
        
        # Tax information
        tax_data = data.get('tax_info', {})
        if tax_data:
            ledger.tax_info = LedgerTaxInfo(
                gstin=tax_data.get('gstin', ''),
                gst_registration_type=tax_data.get('gst_registration_type', ''),
                gst_applicable=tax_data.get('gst_applicable', False),
                tax_rate=Decimal(str(tax_data.get('tax_rate', 0))),
                tax_category=tax_data.get('tax_category', ''),
                hsn_code=tax_data.get('hsn_code', ''),
                pan=tax_data.get('pan', ''),
                is_tax_exempt=tax_data.get('is_tax_exempt', False)
            )
        
        # Other properties
        ledger.is_revenue = data.get('is_revenue', False)
        ledger.is_bill_wise_on = data.get('is_bill_wise_on', False)
        ledger.bank_name = data.get('bank_name', '')
        ledger.account_number = data.get('account_number', '')
        ledger.credit_limit = Decimal(str(data.get('credit_limit', 0)))
        ledger.voucher_count = data.get('voucher_count', 0)
        
        return ledger


class LedgerTableModel(QAbstractTableModel):
    """
    Qt Table Model for displaying ledger information in a professional table
    
    This model provides a structured way to display ledger lists
    in Qt table views with sorting, filtering, and formatting capabilities.
    """
    
    def __init__(self, ledgers: List[LedgerInfo] = None):
        """
        Initialize the ledger table model
        
        Args:
            ledgers: List of LedgerInfo instances to display
        """
        super().__init__()
        self.ledgers = ledgers or []
        self.headers = [
            "Ledger Name", "Group", "Balance", "Type", 
            "GST No.", "Last Voucher", "Voucher Count"
        ]
        
        # Color scheme for different balance types
        self.color_scheme = {
            BalanceType.DEBIT: QColor("#2E7D32"),    # Green for debit balances
            BalanceType.CREDIT: QColor("#C62828"),    # Red for credit balances
            BalanceType.ZERO: QColor("#757575")       # Gray for zero balances
        }
    
    def rowCount(self, parent=QModelIndex()):
        """Return number of ledgers"""
        return len(self.ledgers)
    
    def columnCount(self, parent=QModelIndex()):
        """Return number of columns"""
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        """Return data for display"""
        if not index.isValid() or index.row() >= len(self.ledgers):
            return QVariant()
        
        ledger = self.ledgers[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Ledger Name
                return ledger.get_display_name()
            elif column == 1:  # Group
                return ledger.parent_group_name
            elif column == 2:  # Balance
                return ledger.get_balance_display()
            elif column == 3:  # Type
                return ledger.ledger_type.value.replace('_', ' ').title()
            elif column == 4:  # GST No.
                return ledger.tax_info.gstin
            elif column == 5:  # Last Voucher
                if ledger.last_voucher_date:
                    return ledger.last_voucher_date.strftime("%d-%m-%Y")
                return ""
            elif column == 6:  # Voucher Count
                return str(ledger.voucher_count)
        
        elif role == Qt.ForegroundRole and column == 2:  # Balance column color
            return self.color_scheme.get(ledger.balance.balance_type, QColor("#000000"))
        
        elif role == Qt.TextAlignmentRole:
            if column in [2, 6]:  # Balance and Voucher Count - right aligned
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.ToolTipRole:
            if column == 0:  # Ledger name tooltip
                tooltip_parts = [f"Name: {ledger.name}"]
                if ledger.alias:
                    tooltip_parts.append(f"Alias: {ledger.alias}")
                if ledger.contact_info.email:
                    tooltip_parts.append(f"Email: {ledger.contact_info.email}")
                if ledger.contact_info.phone:
                    tooltip_parts.append(f"Phone: {ledger.contact_info.phone}")
                return "\n".join(tooltip_parts)
            elif column == 2:  # Balance tooltip
                tooltip_parts = [f"Current Balance: {ledger.get_balance_display()}"]
                if ledger.balance.opening_balance != 0:
                    tooltip_parts.append(f"Opening Balance: {ledger.balance.opening_balance:,.2f}")
                if ledger.balance.ytd_debit != 0:
                    tooltip_parts.append(f"YTD Debits: {ledger.balance.ytd_debit:,.2f}")
                if ledger.balance.ytd_credit != 0:
                    tooltip_parts.append(f"YTD Credits: {ledger.balance.ytd_credit:,.2f}")
                return "\n".join(tooltip_parts)
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return QVariant()
    
    def update_ledgers(self, ledgers: List[LedgerInfo]):
        """
        Update the model with new ledger data
        
        Args:
            ledgers: New list of LedgerInfo instances
        """
        self.beginResetModel()
        self.ledgers = ledgers
        self.endResetModel()
        logger.info(f"LedgerTableModel updated with {len(ledgers)} ledgers")
    
    def get_ledger(self, index: QModelIndex) -> Optional[LedgerInfo]:
        """
        Get ledger info for a specific model index
        
        Args:
            index: QModelIndex for the row
            
        Returns:
            LedgerInfo instance or None
        """
        if index.isValid() and index.row() < len(self.ledgers):
            return self.ledgers[index.row()]
        return None
    
    def filter_ledgers(self, filter_text: str = "", ledger_type: Optional[LedgerType] = None,
                      min_balance: Optional[Decimal] = None) -> List[int]:
        """
        Filter ledgers based on criteria and return matching row indices
        
        Args:
            filter_text: Text to search in ledger name/alias
            ledger_type: Filter by specific ledger type
            min_balance: Minimum balance filter
            
        Returns:
            List of row indices that match the filter criteria
        """
        matching_rows = []
        
        for i, ledger in enumerate(self.ledgers):
            # Text filter
            if filter_text:
                search_text = filter_text.lower()
                if (search_text not in ledger.name.lower() and 
                    search_text not in ledger.alias.lower() and
                    search_text not in ledger.parent_group_name.lower()):
                    continue
            
            # Type filter
            if ledger_type and ledger.ledger_type != ledger_type:
                continue
            
            # Balance filter
            if min_balance and abs(ledger.balance.current_balance) < min_balance:
                continue
            
            matching_rows.append(i)
        
        return matching_rows


class LedgerTreeModel(QAbstractItemModel):
    """
    Qt Tree Model for displaying ledgers in hierarchical group structure
    
    This model provides a tree view of ledgers organized by their groups,
    showing the complete ledger hierarchy as in TallyPrime.
    """
    
    def __init__(self, ledgers: List[LedgerInfo] = None):
        """
        Initialize the ledger tree model
        
        Args:
            ledgers: List of LedgerInfo instances to display
        """
        super().__init__()
        self.ledgers = ledgers or []
        self.headers = ["Name", "Balance", "Type", "Count"]
        
        # Build tree structure
        self._build_tree_structure()
    
    def _build_tree_structure(self):
        """
        Build hierarchical tree structure from flat ledger list
        """
        # This is a simplified implementation
        # In a full implementation, you would build a proper tree structure
        # with group nodes and ledger leaf nodes
        
        self.root_groups = {}  # Group name -> list of ledgers
        
        for ledger in self.ledgers:
            group_name = ledger.parent_group_name or "Ungrouped"
            if group_name not in self.root_groups:
                self.root_groups[group_name] = []
            self.root_groups[group_name].append(ledger)
    
    def index(self, row, column, parent=QModelIndex()):
        """Create model index"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        if not parent.isValid():
            # Top-level group
            group_names = list(self.root_groups.keys())
            if row < len(group_names):
                return self.createIndex(row, column, group_names[row])
        else:
            # Ledger under group
            group_name = parent.internalPointer()
            if isinstance(group_name, str) and group_name in self.root_groups:
                ledgers = self.root_groups[group_name]
                if row < len(ledgers):
                    return self.createIndex(row, column, ledgers[row])
        
        return QModelIndex()
    
    def parent(self, index):
        """Get parent index"""
        if not index.isValid():
            return QModelIndex()
        
        item = index.internalPointer()
        if isinstance(item, LedgerInfo):
            # Find the group this ledger belongs to
            group_name = item.parent_group_name or "Ungrouped"
            group_names = list(self.root_groups.keys())
            if group_name in group_names:
                group_row = group_names.index(group_name)
                return self.createIndex(group_row, 0, group_name)
        
        return QModelIndex()
    
    def rowCount(self, parent=QModelIndex()):
        """Return number of rows"""
        if not parent.isValid():
            # Root level - return number of groups
            return len(self.root_groups)
        else:
            # Group level - return number of ledgers in group
            group_name = parent.internalPointer()
            if isinstance(group_name, str) and group_name in self.root_groups:
                return len(self.root_groups[group_name])
        
        return 0
    
    def columnCount(self, parent=QModelIndex()):
        """Return number of columns"""
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        """Return data for display"""
        if not index.isValid():
            return QVariant()
        
        item = index.internalPointer()
        column = index.column()
        
        if role == Qt.DisplayRole:
            if isinstance(item, str):  # Group node
                if column == 0:
                    return item
                elif column == 3:  # Count
                    return f"({len(self.root_groups[item])} ledgers)"
            elif isinstance(item, LedgerInfo):  # Ledger node
                if column == 0:
                    return item.get_display_name()
                elif column == 1:
                    return item.get_balance_display()
                elif column == 2:
                    return item.ledger_type.value.replace('_', ' ').title()
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return QVariant()
    
    def update_ledgers(self, ledgers: List[LedgerInfo]):
        """
        Update the model with new ledger data
        
        Args:
            ledgers: New list of LedgerInfo instances
        """
        self.beginResetModel()
        self.ledgers = ledgers
        self._build_tree_structure()
        self.endResetModel()
        logger.info(f"LedgerTreeModel updated with {len(ledgers)} ledgers in {len(self.root_groups)} groups")


# Utility functions for ledger data processing

def create_sample_ledgers() -> List[LedgerInfo]:
    """
    Create sample ledger data for testing and development
    
    Returns:
        List of sample LedgerInfo instances
    """
    from decimal import Decimal
    
    ledgers = []
    
    # Sample bank ledger
    bank_ledger = LedgerInfo(
        name="HDFC Bank Ltd",
        alias="HDFC",
        ledger_type=LedgerType.BANK_ACCOUNTS,
        parent_group_name="Bank Accounts",
        bank_name="HDFC Bank",
        account_number="12345678901234",
        ifsc_code="HDFC0001234",
        branch_name="Commercial Street Branch"
    )
    bank_ledger.balance.current_balance = Decimal('125000.50')
    bank_ledger.balance.balance_type = BalanceType.DEBIT
    bank_ledger.voucher_count = 45
    ledgers.append(bank_ledger)
    
    # Sample debtor ledger
    debtor_ledger = LedgerInfo(
        name="ABC Enterprises",
        ledger_type=LedgerType.SUNDRY_DEBTORS,
        parent_group_name="Sundry Debtors",
        credit_limit=Decimal('50000.00'),
        credit_period=30
    )
    debtor_ledger.balance.current_balance = Decimal('25000.00')
    debtor_ledger.balance.balance_type = BalanceType.DEBIT
    debtor_ledger.tax_info.gstin = "29ABCDE1234F1Z5"
    debtor_ledger.contact_info.email = "contact@abcenterprises.com"
    debtor_ledger.contact_info.phone = "080-12345678"
    debtor_ledger.voucher_count = 12
    ledgers.append(debtor_ledger)
    
    # Sample expense ledger
    expense_ledger = LedgerInfo(
        name="Office Rent",
        ledger_type=LedgerType.INDIRECT_EXPENSES,
        parent_group_name="Indirect Expenses"
    )
    expense_ledger.balance.current_balance = Decimal('15000.00')
    expense_ledger.balance.balance_type = BalanceType.DEBIT
    expense_ledger.voucher_count = 6
    ledgers.append(expense_ledger)
    
    # Sample sales ledger
    sales_ledger = LedgerInfo(
        name="Sales Account",
        ledger_type=LedgerType.SALES_ACCOUNTS,
        parent_group_name="Sales Accounts",
        is_revenue=True
    )
    sales_ledger.balance.current_balance = Decimal('200000.00')
    sales_ledger.balance.balance_type = BalanceType.CREDIT
    sales_ledger.voucher_count = 85
    ledgers.append(sales_ledger)
    
    return ledgers


def classify_ledger_type(group_name: str, ledger_name: str) -> LedgerType:
    """
    Classify ledger type based on group name and ledger name
    
    Args:
        group_name: Parent group name
        ledger_name: Ledger name
        
    Returns:
        Classified LedgerType
    """
    group_lower = group_name.lower()
    ledger_lower = ledger_name.lower()
    
    # Bank accounts
    if 'bank' in group_lower or 'bank' in ledger_lower:
        return LedgerType.BANK_ACCOUNTS
    
    # Cash accounts
    if 'cash' in group_lower or 'cash' in ledger_lower:
        return LedgerType.CASH
    
    # Debtors
    if 'debtor' in group_lower or 'receivable' in group_lower:
        return LedgerType.SUNDRY_DEBTORS
    
    # Creditors
    if 'creditor' in group_lower or 'payable' in group_lower:
        return LedgerType.SUNDRY_CREDITORS
    
    # Sales
    if 'sale' in group_lower or 'income' in group_lower or 'revenue' in group_lower:
        return LedgerType.SALES_ACCOUNTS
    
    # Purchase
    if 'purchase' in group_lower:
        return LedgerType.PURCHASE_ACCOUNTS
    
    # Expenses
    if 'expense' in group_lower or 'expenditure' in group_lower:
        if 'direct' in group_lower:
            return LedgerType.DIRECT_EXPENSES
        else:
            return LedgerType.INDIRECT_EXPENSES
    
    # Assets
    if 'asset' in group_lower:
        if 'current' in group_lower:
            return LedgerType.CURRENT_ASSETS
        else:
            return LedgerType.FIXED_ASSETS
    
    # Liabilities
    if 'liability' in group_lower or 'capital' in group_lower:
        return LedgerType.CURRENT_LIABILITIES
    
    # Default
    return LedgerType.OTHER
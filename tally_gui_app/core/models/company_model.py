#!/usr/bin/env python3
"""
TallyPrime Company Data Model - Professional Data Structures

This module provides comprehensive data models for TallyPrime company information.
It includes dataclasses for company details, financial year information, and
configuration settings with Qt6 integration support.

Key Features:
- Comprehensive company information data structures
- Financial year and period management
- Address and contact information modeling
- Configuration and settings representation
- Qt6 model integration for GUI display
- JSON serialization support for caching

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from enum import Enum
import json
import logging

# Qt6 imports for model integration
from PySide6.QtCore import QObject, QAbstractTableModel, Qt, QModelIndex, QVariant

# Set up logger for this module
logger = logging.getLogger(__name__)


class CompanyType(Enum):
    """
    Enumeration of different company types in TallyPrime
    Used to categorize and handle different business structures
    """
    PROPRIETORSHIP = "proprietorship"
    PARTNERSHIP = "partnership"
    PRIVATE_LIMITED = "private_limited"
    PUBLIC_LIMITED = "public_limited"
    LLP = "limited_liability_partnership"
    NGO = "non_profit_organization"
    GOVERNMENT = "government"
    OTHER = "other"


class FinancialYearType(Enum):
    """
    Enumeration of financial year types
    Different countries and businesses use different financial year patterns
    """
    APRIL_TO_MARCH = "april_to_march"    # India standard
    JANUARY_TO_DECEMBER = "january_to_december"  # Calendar year
    CUSTOM = "custom"                    # User-defined dates


@dataclass
class CompanyAddress:
    """
    Data class representing company address information
    Comprehensive address structure for business documentation
    """
    line1: str = ""
    line2: str = ""
    line3: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = ""
    phone: str = ""
    mobile: str = ""
    fax: str = ""
    email: str = ""
    website: str = ""
    
    def get_formatted_address(self) -> str:
        """
        Get formatted address string for display purposes
        
        Returns:
            Formatted multi-line address string
        """
        lines = []
        if self.line1: lines.append(self.line1)
        if self.line2: lines.append(self.line2)
        if self.line3: lines.append(self.line3)
        
        city_state_postal = []
        if self.city: city_state_postal.append(self.city)
        if self.state: city_state_postal.append(self.state)
        if self.postal_code: city_state_postal.append(self.postal_code)
        
        if city_state_postal:
            lines.append(" - ".join(city_state_postal))
        
        if self.country: lines.append(self.country)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert address to dictionary for serialization"""
        return {
            'line1': self.line1,
            'line2': self.line2,
            'line3': self.line3,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'mobile': self.mobile,
            'fax': self.fax,
            'email': self.email,
            'website': self.website
        }


@dataclass
class FinancialYearInfo:
    """
    Data class representing financial year information
    Comprehensive financial period management for accounting
    """
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    year_type: FinancialYearType = FinancialYearType.APRIL_TO_MARCH
    display_name: str = ""
    is_current: bool = False
    is_locked: bool = False
    books_beginning_from: Optional[date] = None
    
    def get_year_label(self) -> str:
        """
        Get formatted financial year label
        
        Returns:
            Formatted year string like "2024-25" or "FY 2024-25"
        """
        if self.display_name:
            return self.display_name
        
        if self.start_date and self.end_date:
            start_year = self.start_date.year
            end_year = self.end_date.year
            
            if start_year == end_year:
                return str(start_year)
            else:
                # Format as "2024-25" for April-March years
                return f"{start_year}-{str(end_year)[-2:]}"
        
        return "Unknown Financial Year"
    
    def get_duration_days(self) -> int:
        """
        Calculate financial year duration in days
        
        Returns:
            Number of days in the financial year
        """
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert financial year info to dictionary for serialization"""
        return {
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'year_type': self.year_type.value,
            'display_name': self.display_name,
            'is_current': self.is_current,
            'is_locked': self.is_locked,
            'books_beginning_from': self.books_beginning_from.isoformat() if self.books_beginning_from else None
        }


@dataclass
class TaxRegistrationInfo:
    """
    Data class representing tax registration information
    Comprehensive tax ID and registration details
    """
    gstin: str = ""                    # GST Identification Number (India)
    pan: str = ""                      # PAN Number (India)
    tan: str = ""                      # TAN Number (India)
    cin: str = ""                      # Corporate Identification Number (India)
    vat_number: str = ""               # VAT Registration Number
    service_tax_number: str = ""       # Service Tax Registration
    excise_registration: str = ""       # Excise Registration Number
    import_export_code: str = ""       # IEC Code for import/export
    other_registrations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tax registration info to dictionary"""
        return {
            'gstin': self.gstin,
            'pan': self.pan,
            'tan': self.tan,
            'cin': self.cin,
            'vat_number': self.vat_number,
            'service_tax_number': self.service_tax_number,
            'excise_registration': self.excise_registration,
            'import_export_code': self.import_export_code,
            'other_registrations': self.other_registrations
        }


@dataclass
class CompanyFeatures:
    """
    Data class representing enabled company features and capabilities
    TallyPrime has various features that can be enabled/disabled per company
    """
    maintain_bill_wise_details: bool = False
    use_cost_centers: bool = False
    use_budgets: bool = False
    use_credit_limits: bool = False
    maintain_payroll: bool = False
    use_interest_calculation: bool = False
    use_pos_invoicing: bool = False
    use_multi_currency: bool = False
    use_zero_valued_entries: bool = False
    use_optional_vouchers: bool = False
    use_reversing_journals: bool = False
    use_common_narration: bool = False
    show_bank_details: bool = False
    use_advanced_parameters: bool = False
    
    def get_enabled_features(self) -> List[str]:
        """
        Get list of enabled feature names
        
        Returns:
            List of enabled feature names
        """
        enabled = []
        for attr_name, value in self.__dict__.items():
            if value is True:
                # Convert snake_case to readable format
                readable_name = attr_name.replace('_', ' ').replace('use ', '').title()
                enabled.append(readable_name)
        return enabled
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert features to dictionary"""
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class CompanyInfo:
    """
    Comprehensive data class representing TallyPrime company information
    
    This is the main data structure that holds all company-related information
    extracted from TallyPrime. It provides a complete representation of the
    company profile, configuration, and settings.
    """
    # Basic company information
    name: str = ""
    guid: str = ""                     # Unique company identifier
    company_number: str = ""           # Company sequence number in TallyPrime
    alias: str = ""                    # Alternative company name
    
    # Company categorization
    company_type: CompanyType = CompanyType.OTHER
    nature_of_business: str = ""
    industry_type: str = ""
    
    # Address information
    mailing_address: CompanyAddress = field(default_factory=CompanyAddress)
    billing_address: CompanyAddress = field(default_factory=CompanyAddress)
    
    # Financial year information
    current_financial_year: FinancialYearInfo = field(default_factory=FinancialYearInfo)
    previous_financial_years: List[FinancialYearInfo] = field(default_factory=list)
    
    # Tax and registration information
    tax_info: TaxRegistrationInfo = field(default_factory=TaxRegistrationInfo)
    
    # Company features and configuration
    features: CompanyFeatures = field(default_factory=CompanyFeatures)
    
    # Currency and localization
    base_currency_symbol: str = "₹"
    base_currency_name: str = "Indian Rupees"
    decimal_places: int = 2
    
    # Metadata and status
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    data_path: str = ""                # TallyPrime data directory path
    version: str = ""                  # TallyPrime version
    
    # Statistics (filled when data is loaded)
    total_ledgers: int = 0
    total_groups: int = 0
    total_vouchers: int = 0
    total_stock_items: int = 0
    
    def get_display_name(self) -> str:
        """
        Get the best display name for the company
        
        Returns:
            Company name or alias for display purposes
        """
        return self.alias if self.alias else self.name
    
    def get_formatted_address(self, address_type: str = "mailing") -> str:
        """
        Get formatted address string
        
        Args:
            address_type: "mailing" or "billing"
            
        Returns:
            Formatted address string
        """
        if address_type == "billing":
            return self.billing_address.get_formatted_address()
        else:
            return self.mailing_address.get_formatted_address()
    
    def has_gst_registration(self) -> bool:
        """Check if company has GST registration"""
        return bool(self.tax_info.gstin)
    
    def get_financial_year_label(self) -> str:
        """Get current financial year label"""
        return self.current_financial_year.get_year_label()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert company info to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of company information
        """
        return {
            'name': self.name,
            'guid': self.guid,
            'company_number': self.company_number,
            'alias': self.alias,
            'company_type': self.company_type.value,
            'nature_of_business': self.nature_of_business,
            'industry_type': self.industry_type,
            'mailing_address': self.mailing_address.to_dict(),
            'billing_address': self.billing_address.to_dict(),
            'current_financial_year': self.current_financial_year.to_dict(),
            'previous_financial_years': [fy.to_dict() for fy in self.previous_financial_years],
            'tax_info': self.tax_info.to_dict(),
            'features': self.features.to_dict(),
            'base_currency_symbol': self.base_currency_symbol,
            'base_currency_name': self.base_currency_name,
            'decimal_places': self.decimal_places,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'data_path': self.data_path,
            'version': self.version,
            'total_ledgers': self.total_ledgers,
            'total_groups': self.total_groups,
            'total_vouchers': self.total_vouchers,
            'total_stock_items': self.total_stock_items
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyInfo':
        """
        Create CompanyInfo instance from dictionary
        
        Args:
            data: Dictionary containing company information
            
        Returns:
            CompanyInfo instance
        """
        # Create the main company info object
        company = cls()
        
        # Basic information
        company.name = data.get('name', '')
        company.guid = data.get('guid', '')
        company.company_number = data.get('company_number', '')
        company.alias = data.get('alias', '')
        
        # Company type
        company_type_str = data.get('company_type', 'other')
        try:
            company.company_type = CompanyType(company_type_str)
        except ValueError:
            company.company_type = CompanyType.OTHER
        
        company.nature_of_business = data.get('nature_of_business', '')
        company.industry_type = data.get('industry_type', '')
        
        # Addresses
        mailing_addr_data = data.get('mailing_address', {})
        company.mailing_address = CompanyAddress(**mailing_addr_data)
        
        billing_addr_data = data.get('billing_address', {})
        company.billing_address = CompanyAddress(**billing_addr_data)
        
        # Financial year
        fy_data = data.get('current_financial_year', {})
        if fy_data:
            company.current_financial_year = FinancialYearInfo(
                start_date=datetime.fromisoformat(fy_data['start_date']).date() if fy_data.get('start_date') else None,
                end_date=datetime.fromisoformat(fy_data['end_date']).date() if fy_data.get('end_date') else None,
                year_type=FinancialYearType(fy_data.get('year_type', 'april_to_march')),
                display_name=fy_data.get('display_name', ''),
                is_current=fy_data.get('is_current', False),
                is_locked=fy_data.get('is_locked', False)
            )
        
        # Tax information
        tax_data = data.get('tax_info', {})
        if tax_data:
            company.tax_info = TaxRegistrationInfo(**tax_data)
        
        # Features
        features_data = data.get('features', {})
        if features_data:
            company.features = CompanyFeatures(**features_data)
        
        # Currency and other fields
        company.base_currency_symbol = data.get('base_currency_symbol', '₹')
        company.base_currency_name = data.get('base_currency_name', 'Indian Rupees')
        company.decimal_places = data.get('decimal_places', 2)
        company.data_path = data.get('data_path', '')
        company.version = data.get('version', '')
        
        # Statistics
        company.total_ledgers = data.get('total_ledgers', 0)
        company.total_groups = data.get('total_groups', 0)
        company.total_vouchers = data.get('total_vouchers', 0)
        company.total_stock_items = data.get('total_stock_items', 0)
        
        return company


class CompanyInfoTableModel(QAbstractTableModel):
    """
    Qt Table Model for displaying company information in a professional table
    
    This model provides a structured way to display company information
    in Qt table views with proper formatting and organization.
    """
    
    def __init__(self, company_info: Optional[CompanyInfo] = None):
        """
        Initialize the table model
        
        Args:
            company_info: CompanyInfo instance to display
        """
        super().__init__()
        self.company_info = company_info
        self.headers = ["Property", "Value"]
        self._prepare_data()
    
    def _prepare_data(self):
        """
        Prepare company data for table display
        Creates a list of key-value pairs for table rows
        """
        self.data_rows = []
        
        if not self.company_info:
            return
        
        # Basic Information Section
        self.data_rows.append(("Company Name", self.company_info.name))
        self.data_rows.append(("Alias", self.company_info.alias))
        self.data_rows.append(("Company Type", self.company_info.company_type.value.title()))
        self.data_rows.append(("Nature of Business", self.company_info.nature_of_business))
        self.data_rows.append(("Industry Type", self.company_info.industry_type))
        
        # Financial Year Information
        self.data_rows.append(("Financial Year", self.company_info.get_financial_year_label()))
        if self.company_info.current_financial_year.start_date:
            self.data_rows.append(("FY Start Date", self.company_info.current_financial_year.start_date.strftime("%d-%m-%Y")))
        if self.company_info.current_financial_year.end_date:
            self.data_rows.append(("FY End Date", self.company_info.current_financial_year.end_date.strftime("%d-%m-%Y")))
        
        # Tax Information
        if self.company_info.tax_info.gstin:
            self.data_rows.append(("GSTIN", self.company_info.tax_info.gstin))
        if self.company_info.tax_info.pan:
            self.data_rows.append(("PAN", self.company_info.tax_info.pan))
        
        # Currency Information
        self.data_rows.append(("Base Currency", f"{self.company_info.base_currency_name} ({self.company_info.base_currency_symbol})"))
        self.data_rows.append(("Decimal Places", str(self.company_info.decimal_places)))
        
        # Statistics
        self.data_rows.append(("Total Ledgers", str(self.company_info.total_ledgers)))
        self.data_rows.append(("Total Groups", str(self.company_info.total_groups)))
        self.data_rows.append(("Total Vouchers", str(self.company_info.total_vouchers)))
        self.data_rows.append(("Total Stock Items", str(self.company_info.total_stock_items)))
        
        # Technical Information
        self.data_rows.append(("GUID", self.company_info.guid))
        self.data_rows.append(("Company Number", self.company_info.company_number))
        self.data_rows.append(("Data Path", self.company_info.data_path))
        self.data_rows.append(("TallyPrime Version", self.company_info.version))
    
    def rowCount(self, parent=QModelIndex()):
        """Return number of rows"""
        return len(self.data_rows)
    
    def columnCount(self, parent=QModelIndex()):
        """Return number of columns"""
        return 2
    
    def data(self, index, role=Qt.DisplayRole):
        """Return data for display"""
        if not index.isValid() or index.row() >= len(self.data_rows):
            return QVariant()
        
        if role == Qt.DisplayRole:
            row_data = self.data_rows[index.row()]
            return row_data[index.column()]
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return QVariant()
    
    def update_company_info(self, company_info: CompanyInfo):
        """
        Update the model with new company information
        
        Args:
            company_info: New CompanyInfo instance
        """
        self.beginResetModel()
        self.company_info = company_info
        self._prepare_data()
        self.endResetModel()
        logger.info("CompanyInfoTableModel updated with new data")


# Utility functions for company data processing

def parse_company_xml(xml_root) -> Optional[CompanyInfo]:
    """
    Parse company information from TallyPrime XML response
    
    This function will be implemented to parse the actual XML structure
    returned by TallyPrime for company information requests.
    
    Args:
        xml_root: XML root element from TallyPrime response
        
    Returns:
        CompanyInfo instance or None if parsing fails
    """
    # This will be implemented in the next task
    # For now, return a placeholder
    logger.info("Company XML parsing not yet implemented")
    return None


def create_sample_company_info() -> CompanyInfo:
    """
    Create a sample CompanyInfo instance for testing and development
    
    Returns:
        Sample CompanyInfo with realistic data
    """
    # Sample address
    address = CompanyAddress(
        line1="123 Business Street",
        line2="Commercial Complex",
        city="Bangalore",
        state="Karnataka",
        country="India",
        postal_code="560001",
        phone="080-12345678",
        email="info@company.com",
        website="www.company.com"
    )
    
    # Sample financial year
    financial_year = FinancialYearInfo(
        start_date=date(2024, 4, 1),
        end_date=date(2025, 3, 31),
        year_type=FinancialYearType.APRIL_TO_MARCH,
        display_name="2024-25",
        is_current=True,
        is_locked=False
    )
    
    # Sample tax info
    tax_info = TaxRegistrationInfo(
        gstin="29ABCDE1234F1Z5",
        pan="ABCDE1234F"
    )
    
    # Sample features
    features = CompanyFeatures(
        maintain_bill_wise_details=True,
        use_cost_centers=True,
        use_multi_currency=False
    )
    
    # Create company info
    company = CompanyInfo(
        name="Sample Company Ltd",
        alias="Sample Co",
        company_type=CompanyType.PRIVATE_LIMITED,
        nature_of_business="Software Development",
        industry_type="Information Technology",
        mailing_address=address,
        billing_address=address,
        current_financial_year=financial_year,
        tax_info=tax_info,
        features=features,
        total_ledgers=150,
        total_groups=25,
        total_vouchers=1250,
        total_stock_items=0
    )
    
    return company
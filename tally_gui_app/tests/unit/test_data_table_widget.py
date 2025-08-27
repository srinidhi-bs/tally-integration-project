#!/usr/bin/env python3
"""
Unit Tests for Professional Data Table Widget

This module provides comprehensive unit tests for the ProfessionalDataTableWidget
and its associated components including filtering, export, and data management.

Key Test Areas:
- Widget initialization and setup
- Data loading and display
- Filtering and search functionality
- Export operations (CSV, Excel, PDF)
- Context menu operations
- Theme integration
- Signal emission and handling
- Error handling and edge cases

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6) + pytest
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date
from typing import List
import json

# Qt imports for testing
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QModelIndex, QTimer
from PySide6.QtTest import QTest
from PySide6.QtGui import QKeySequence

# Import the widget and models to test
from ui.widgets.data_table_widget import (
    ProfessionalDataTableWidget, 
    DataTableFilterProxyModel, 
    DataExportWorker
)
from core.models.ledger_model import (
    LedgerInfo, LedgerTableModel, LedgerType, 
    LedgerBalance, BalanceType, LedgerContact, 
    LedgerTaxInfo, create_sample_ledgers
)
from ui.resources.styles.theme_manager import ThemeManager, ThemeMode
from core.utils.logger import get_logger

# Set up logger for tests
logger = get_logger(__name__)


class TestDataTableFilterProxyModel:
    """
    Test suite for DataTableFilterProxyModel
    
    These tests verify the filtering and sorting capabilities
    of the proxy model used by the data table widget.
    """
    
    @pytest.fixture
    def sample_ledgers(self) -> List[LedgerInfo]:
        """Create sample ledger data for testing"""
        return create_sample_ledgers()
    
    @pytest.fixture 
    def ledger_model(self, sample_ledgers):
        """Create ledger table model with sample data"""
        model = LedgerTableModel()
        model.update_ledgers(sample_ledgers)
        return model
    
    @pytest.fixture
    def filter_model(self, ledger_model):
        """Create filter proxy model with source model"""
        filter_model = DataTableFilterProxyModel()
        filter_model.setSourceModel(ledger_model)
        return filter_model
    
    def test_filter_model_initialization(self, filter_model):
        """Test proxy model initializes correctly"""
        # Check initial state
        assert filter_model._text_filter == ""
        assert filter_model._type_filter is None
        assert filter_model._min_balance is None
        assert filter_model._max_balance is None
        assert filter_model._show_zero_balances is True
        
        logger.info("✅ Filter model initialization test passed")
    
    def test_text_filter(self, filter_model, sample_ledgers):
        """Test text filtering functionality"""
        # Initially all rows should be visible
        initial_count = filter_model.rowCount()
        assert initial_count == len(sample_ledgers)
        
        # Apply text filter for "HDFC"
        filter_model.set_text_filter("HDFC")
        hdfc_count = filter_model.rowCount()
        assert hdfc_count < initial_count
        assert hdfc_count >= 1  # Should find at least one HDFC ledger
        
        # Clear filter
        filter_model.set_text_filter("")
        assert filter_model.rowCount() == initial_count
        
        logger.info("✅ Text filter test passed")
    
    def test_type_filter(self, filter_model, sample_ledgers):
        """Test ledger type filtering"""
        # Filter by bank accounts
        filter_model.set_type_filter(LedgerType.BANK_ACCOUNTS)
        bank_count = filter_model.rowCount()
        
        # Should have fewer rows than total
        assert bank_count < len(sample_ledgers)
        
        # Verify all visible rows are bank accounts
        for row in range(bank_count):
            index = filter_model.index(row, 0)
            source_index = filter_model.mapToSource(index)
            ledger = filter_model.sourceModel().get_ledger(source_index)
            assert ledger.ledger_type == LedgerType.BANK_ACCOUNTS
        
        # Clear filter
        filter_model.set_type_filter(None)
        assert filter_model.rowCount() == len(sample_ledgers)
        
        logger.info("✅ Type filter test passed")
    
    def test_balance_filter(self, filter_model, sample_ledgers):
        """Test balance range filtering"""
        # Filter for balances >= 10000
        min_balance = Decimal('10000')
        filter_model.set_balance_filter(min_balance=min_balance)
        filtered_count = filter_model.rowCount()
        
        # Verify all visible ledgers meet criteria
        for row in range(filtered_count):
            index = filter_model.index(row, 0)
            source_index = filter_model.mapToSource(index)
            ledger = filter_model.sourceModel().get_ledger(source_index)
            assert abs(ledger.balance.current_balance) >= min_balance
        
        logger.info("✅ Balance filter test passed")
    
    def test_zero_balance_filter(self, filter_model):
        """Test show/hide zero balance filtering"""
        # Create a ledger with zero balance
        zero_ledger = LedgerInfo(
            name="Zero Balance Ledger",
            ledger_type=LedgerType.OTHER
        )
        zero_ledger.balance.current_balance = Decimal('0')
        
        # Add to model
        model = filter_model.sourceModel()
        current_ledgers = model.ledgers[:]
        current_ledgers.append(zero_ledger)
        model.update_ledgers(current_ledgers)
        
        initial_count = filter_model.rowCount()
        
        # Hide zero balances
        filter_model.set_show_zero_balances(False)
        filtered_count = filter_model.rowCount()
        
        # Should have one less row
        assert filtered_count < initial_count
        
        # Show zero balances again
        filter_model.set_show_zero_balances(True)
        assert filter_model.rowCount() == initial_count
        
        logger.info("✅ Zero balance filter test passed")
    
    def test_custom_sorting(self, filter_model):
        """Test custom sorting logic"""
        # Test sorting by ledger name (column 0)
        filter_model.sort(0, Qt.AscendingOrder)
        
        # Verify names are in ascending order
        prev_name = ""
        for row in range(min(5, filter_model.rowCount())):  # Test first 5 rows
            index = filter_model.index(row, 0)
            source_index = filter_model.mapToSource(index)
            ledger = filter_model.sourceModel().get_ledger(source_index)
            current_name = ledger.get_display_name().lower()
            assert current_name >= prev_name
            prev_name = current_name
        
        # Test sorting by balance (column 2)
        filter_model.sort(2, Qt.AscendingOrder)
        
        # Verify balances are in ascending order
        prev_balance = Decimal('-999999999')
        for row in range(min(5, filter_model.rowCount())):
            index = filter_model.index(row, 0)
            source_index = filter_model.mapToSource(index)
            ledger = filter_model.sourceModel().get_ledger(source_index)
            current_balance = abs(ledger.balance.current_balance)
            assert current_balance >= prev_balance
            prev_balance = current_balance
        
        logger.info("✅ Custom sorting test passed")


class TestDataExportWorker:
    """
    Test suite for DataExportWorker
    
    These tests verify the export functionality for CSV, Excel, and PDF formats.
    Note: Excel and PDF tests require optional dependencies.
    """
    
    @pytest.fixture
    def sample_ledgers(self) -> List[LedgerInfo]:
        """Create sample ledger data for export testing"""
        return create_sample_ledgers()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for export files"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_csv_export(self, sample_ledgers, temp_dir):
        """Test CSV export functionality"""
        file_path = temp_dir / "test_ledgers.csv"
        
        # Create export worker
        worker = DataExportWorker(sample_ledgers, str(file_path), "csv")
        
        # Track signals
        export_completed = False
        export_failed = False
        
        def on_export_completed(path):
            nonlocal export_completed
            export_completed = True
            assert Path(path).exists()
        
        def on_export_failed(error):
            nonlocal export_failed
            export_failed = True
            logger.error(f"Export failed: {error}")
        
        # Connect signals
        worker.export_completed.connect(on_export_completed)
        worker.export_failed.connect(on_export_failed)
        
        # Run export
        worker.run()
        
        # Verify results
        assert export_completed
        assert not export_failed
        assert file_path.exists()
        
        # Verify file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Ledger Name" in content  # Header
            assert len(content.split('\n')) > len(sample_ledgers)  # Data rows
        
        logger.info("✅ CSV export test passed")
    
    def test_excel_export(self, sample_ledgers, temp_dir):
        """Test Excel export functionality (requires openpyxl)"""
        pytest.importorskip("openpyxl", reason="openpyxl not installed")
        
        file_path = temp_dir / "test_ledgers.xlsx"
        
        # Create export worker
        worker = DataExportWorker(sample_ledgers, str(file_path), "excel")
        
        # Track signals
        export_completed = False
        export_failed = False
        
        def on_export_completed(path):
            nonlocal export_completed
            export_completed = True
            assert Path(path).exists()
        
        def on_export_failed(error):
            nonlocal export_failed
            export_failed = True
            logger.error(f"Export failed: {error}")
        
        # Connect signals
        worker.export_completed.connect(on_export_completed)
        worker.export_failed.connect(on_export_failed)
        
        # Run export
        worker.run()
        
        # Verify results
        assert export_completed
        assert not export_failed
        assert file_path.exists()
        
        logger.info("✅ Excel export test passed")
    
    def test_pdf_export(self, sample_ledgers, temp_dir):
        """Test PDF export functionality (requires reportlab)"""
        pytest.importorskip("reportlab", reason="reportlab not installed")
        
        file_path = temp_dir / "test_ledgers.pdf"
        
        # Create export worker
        worker = DataExportWorker(sample_ledgers, str(file_path), "pdf")
        
        # Track signals
        export_completed = False
        export_failed = False
        
        def on_export_completed(path):
            nonlocal export_completed
            export_completed = True
            assert Path(path).exists()
        
        def on_export_failed(error):
            nonlocal export_failed
            export_failed = True
            logger.error(f"Export failed: {error}")
        
        # Connect signals
        worker.export_completed.connect(on_export_completed)
        worker.export_failed.connect(on_export_failed)
        
        # Run export
        worker.run()
        
        # Verify results
        assert export_completed
        assert not export_failed
        assert file_path.exists()
        
        logger.info("✅ PDF export test passed")
    
    def test_invalid_export_format(self, sample_ledgers, temp_dir):
        """Test handling of invalid export format"""
        file_path = temp_dir / "test_ledgers.invalid"
        
        # Create export worker with invalid format
        worker = DataExportWorker(sample_ledgers, str(file_path), "invalid")
        
        # Track signals
        export_failed = False
        error_message = ""
        
        def on_export_failed(error):
            nonlocal export_failed, error_message
            export_failed = True
            error_message = error
        
        worker.export_failed.connect(on_export_failed)
        
        # Run export
        worker.run()
        
        # Verify failure
        assert export_failed
        assert "Unsupported export format" in error_message
        
        logger.info("✅ Invalid export format test passed")


@pytest.mark.qt
class TestProfessionalDataTableWidget:
    """
    Test suite for ProfessionalDataTableWidget
    
    These tests verify the main widget functionality including
    UI components, data loading, filtering, and user interactions.
    """
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for Qt widget testing"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    
    @pytest.fixture
    def sample_ledgers(self) -> List[LedgerInfo]:
        """Create sample ledger data for widget testing"""
        return create_sample_ledgers()
    
    @pytest.fixture
    def data_table_widget(self, qapp):
        """Create data table widget for testing"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        yield widget
        widget.close()
    
    def test_widget_initialization(self, data_table_widget):
        """Test widget initializes correctly"""
        widget = data_table_widget
        
        # Check basic properties
        assert widget.isVisible()
        assert widget.ledger_model is not None
        assert widget.filter_model is not None
        assert widget.theme_manager is not None
        
        # Check UI components
        assert widget.search_edit is not None
        assert widget.type_combo is not None
        assert widget.table_view is not None
        assert widget.refresh_btn is not None
        assert widget.export_btn is not None
        
        # Check initial state
        assert widget.search_edit.text() == ""
        assert widget.type_combo.currentIndex() == 0
        assert widget.show_zero_check.isChecked()
        
        logger.info("✅ Widget initialization test passed")
    
    def test_data_loading(self, data_table_widget, sample_ledgers):
        """Test loading data into the widget"""
        widget = data_table_widget
        
        # Load sample data
        widget.set_ledger_data(sample_ledgers)
        
        # Verify data loaded
        assert widget.get_total_ledger_count() == len(sample_ledgers)
        assert widget.get_visible_ledger_count() == len(sample_ledgers)
        
        # Check status label
        assert "loaded successfully" in widget.status_label.text()
        
        logger.info("✅ Data loading test passed")
    
    def test_search_filtering(self, data_table_widget, sample_ledgers):
        """Test search filtering functionality"""
        widget = data_table_widget
        widget.set_ledger_data(sample_ledgers)
        
        initial_count = widget.get_visible_ledger_count()
        
        # Apply search filter
        widget.search_edit.setText("HDFC")
        QTest.keyClick(widget.search_edit, Qt.Key_Return)
        
        # Wait for filter to apply (debounced)
        QTest.wait(500)
        
        # Verify filtering
        filtered_count = widget.get_visible_ledger_count()
        assert filtered_count < initial_count
        
        # Clear search
        widget.search_edit.clear()
        QTest.keyClick(widget.search_edit, Qt.Key_Return)
        QTest.wait(500)
        
        # Verify filter cleared
        assert widget.get_visible_ledger_count() == initial_count
        
        logger.info("✅ Search filtering test passed")
    
    def test_type_filtering(self, data_table_widget, sample_ledgers):
        """Test type filtering functionality"""
        widget = data_table_widget
        widget.set_ledger_data(sample_ledgers)
        
        initial_count = widget.get_visible_ledger_count()
        
        # Find index for bank accounts
        bank_index = -1
        for i in range(widget.type_combo.count()):
            if widget.type_combo.itemData(i) == LedgerType.BANK_ACCOUNTS:
                bank_index = i
                break
        
        if bank_index > 0:
            # Apply type filter
            widget.type_combo.setCurrentIndex(bank_index)
            QTest.wait(100)
            
            # Verify filtering
            filtered_count = widget.get_visible_ledger_count()
            assert filtered_count < initial_count
            
            # Clear type filter
            widget.type_combo.setCurrentIndex(0)
            QTest.wait(100)
            
            # Verify filter cleared
            assert widget.get_visible_ledger_count() == initial_count
        
        logger.info("✅ Type filtering test passed")
    
    def test_ledger_selection(self, data_table_widget, sample_ledgers):
        """Test ledger selection functionality"""
        widget = data_table_widget
        widget.set_ledger_data(sample_ledgers)
        
        # Track selection signals
        selected_ledger = None
        
        def on_ledger_selected(ledger):
            nonlocal selected_ledger
            selected_ledger = ledger
        
        widget.ledger_selected.connect(on_ledger_selected)
        
        # Select first row
        if widget.get_visible_ledger_count() > 0:
            widget.table_view.selectRow(0)
            
            # Get selected ledger
            current_selection = widget.get_selected_ledger()
            assert current_selection is not None
            assert current_selection.name != ""
            
            # Test double-click selection
            index = widget.table_view.model().index(0, 0)
            QTest.mouseDClick(widget.table_view.viewport(), Qt.LeftButton, Qt.NoModifier, widget.table_view.visualRect(index).center())
            QTest.wait(100)
            
            # Should have emitted signal
            assert selected_ledger is not None
        
        logger.info("✅ Ledger selection test passed")
    
    def test_clear_filters_functionality(self, data_table_widget, sample_ledgers):
        """Test clear filters functionality"""
        widget = data_table_widget
        widget.set_ledger_data(sample_ledgers)
        
        # Apply some filters
        widget.search_edit.setText("test")
        widget.balance_min_edit.setText("1000")
        widget.show_zero_check.setChecked(False)
        
        # Clear filters using button
        QTest.mouseClick(widget.clear_filter_btn, Qt.LeftButton)
        QTest.wait(100)
        
        # Verify filters cleared
        assert widget.search_edit.text() == ""
        assert widget.balance_min_edit.text() == ""
        assert widget.show_zero_check.isChecked()
        assert widget.get_visible_ledger_count() == widget.get_total_ledger_count()
        
        logger.info("✅ Clear filters test passed")
    
    def test_keyboard_shortcuts(self, data_table_widget, sample_ledgers):
        """Test keyboard shortcuts functionality"""
        widget = data_table_widget
        widget.set_ledger_data(sample_ledgers)
        
        # Track refresh signal
        refresh_requested = False
        
        def on_refresh():
            nonlocal refresh_requested
            refresh_requested = True
        
        widget.refresh_requested.connect(on_refresh)
        
        # Test F5 refresh shortcut
        QTest.keyClick(widget, Qt.Key_F5)
        QTest.wait(100)
        
        assert refresh_requested
        
        # Test Ctrl+F search focus
        widget.search_edit.clearFocus()
        QTest.keyClick(widget, Qt.Key_F, Qt.ControlModifier)
        QTest.wait(100)
        
        # Search edit should have focus
        assert widget.search_edit.hasFocus()
        
        logger.info("✅ Keyboard shortcuts test passed")
    
    def test_filter_settings_persistence(self, data_table_widget, sample_ledgers):
        """Test filter settings get/set functionality"""
        widget = data_table_widget
        widget.set_ledger_data(sample_ledgers)
        
        # Set some filter settings
        widget.search_edit.setText("test search")
        widget.balance_min_edit.setText("5000")
        widget.balance_max_edit.setText("50000")
        widget.show_zero_check.setChecked(False)
        
        # Get current settings
        settings = widget.get_filter_settings()
        
        # Verify settings
        assert settings['search_text'] == "test search"
        assert settings['min_balance'] == "5000"
        assert settings['max_balance'] == "50000"
        assert settings['show_zero_balances'] is False
        
        # Clear filters
        widget._clear_all_filters()
        
        # Apply saved settings
        widget.apply_filter_settings(settings)
        
        # Verify settings restored
        assert widget.search_edit.text() == "test search"
        assert widget.balance_min_edit.text() == "5000"
        assert widget.balance_max_edit.text() == "50000"
        assert widget.show_zero_check.isChecked() is False
        
        logger.info("✅ Filter settings persistence test passed")
    
    def test_theme_integration(self, data_table_widget):
        """Test theme manager integration"""
        widget = data_table_widget
        
        # Test theme switching
        theme_manager = widget.theme_manager
        
        # Get current theme
        current_theme = theme_manager.current_theme_mode
        
        # Switch theme
        new_theme = ThemeMode.DARK if current_theme == ThemeMode.LIGHT else ThemeMode.LIGHT
        theme_manager.set_theme_mode(new_theme)
        
        # Wait for theme to apply
        QTest.wait(100)
        
        # Verify theme changed
        assert theme_manager.current_theme_mode == new_theme
        
        # Check if stylesheet was applied (basic check)
        stylesheet = widget.styleSheet()
        assert stylesheet != ""  # Should have some styling
        
        logger.info("✅ Theme integration test passed")
    
    def test_error_handling(self, data_table_widget):
        """Test error handling in various scenarios"""
        widget = data_table_widget
        
        # Test empty data loading
        widget.set_ledger_data([])
        assert widget.get_total_ledger_count() == 0
        assert widget.get_visible_ledger_count() == 0
        
        # Test invalid filter values
        widget.balance_min_edit.setText("invalid")
        widget.balance_max_edit.setText("also_invalid")
        
        # Should not crash when applying filters
        widget._apply_filters()
        
        # Test selection on empty data
        selected = widget.get_selected_ledger()
        assert selected is None
        
        # Test search by name on empty data
        found = widget.select_ledger_by_name("nonexistent")
        assert not found
        
        logger.info("✅ Error handling test passed")


class TestIntegrationScenarios:
    """
    Integration tests for complete data table scenarios
    
    These tests verify end-to-end workflows and complex interactions.
    """
    
    @pytest.fixture(scope="class") 
    def qapp(self):
        """Create QApplication for Qt widget testing"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    
    @pytest.fixture
    def sample_ledgers(self) -> List[LedgerInfo]:
        """Create comprehensive sample ledger data"""
        # Create diverse ledger data for thorough testing
        ledgers = create_sample_ledgers()
        
        # Add more varied data
        additional_ledgers = [
            LedgerInfo(
                name="Zero Balance Ledger",
                ledger_type=LedgerType.CASH,
                parent_group_name="Cash-in-Hand"
            ),
            LedgerInfo(
                name="High Balance Ledger", 
                ledger_type=LedgerType.BANK_ACCOUNTS,
                parent_group_name="Bank Accounts"
            ),
            LedgerInfo(
                name="GST Registered Supplier",
                ledger_type=LedgerType.SUNDRY_CREDITORS,
                parent_group_name="Sundry Creditors"
            )
        ]
        
        # Set balances
        additional_ledgers[0].balance.current_balance = Decimal('0')
        additional_ledgers[1].balance.current_balance = Decimal('1000000')
        additional_ledgers[1].balance.balance_type = BalanceType.DEBIT
        additional_ledgers[2].balance.current_balance = Decimal('25000')
        additional_ledgers[2].balance.balance_type = BalanceType.CREDIT
        additional_ledgers[2].tax_info.gstin = "27ABCDE1234F1Z8"
        
        ledgers.extend(additional_ledgers)
        return ledgers
    
    def test_complete_filter_workflow(self, qapp, sample_ledgers):
        """Test complete filtering workflow with multiple filters"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        
        try:
            # Load data
            widget.set_ledger_data(sample_ledgers)
            initial_count = widget.get_visible_ledger_count()
            
            # Apply text search
            widget.search_edit.setText("Bank")
            QTest.wait(400)
            search_count = widget.get_visible_ledger_count()
            assert search_count < initial_count
            
            # Add type filter
            bank_index = -1
            for i in range(widget.type_combo.count()):
                if widget.type_combo.itemData(i) == LedgerType.BANK_ACCOUNTS:
                    bank_index = i
                    break
            
            if bank_index > 0:
                widget.type_combo.setCurrentIndex(bank_index)
                QTest.wait(100)
                combined_count = widget.get_visible_ledger_count()
                assert combined_count <= search_count
            
            # Add balance filter
            widget.balance_min_edit.setText("10000")
            QTest.wait(600)
            balance_count = widget.get_visible_ledger_count()
            assert balance_count <= combined_count
            
            # Clear all filters
            widget._clear_all_filters()
            QTest.wait(100)
            
            # Should return to initial count
            final_count = widget.get_visible_ledger_count()
            assert final_count == initial_count
            
            logger.info("✅ Complete filter workflow test passed")
            
        finally:
            widget.close()
    
    def test_export_workflow_csv(self, qapp, sample_ledgers):
        """Test complete export workflow for CSV"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        
        try:
            # Load data
            widget.set_ledger_data(sample_ledgers)
            
            # Apply some filters first
            widget.search_edit.setText("Ledger")
            QTest.wait(400)
            
            # Get filtered ledgers count
            filtered_count = widget.get_visible_ledger_count()
            assert filtered_count > 0
            
            # Create temporary file for export
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Create export worker for filtered data
                visible_ledgers = []
                for row in range(widget.filter_model.rowCount()):
                    source_index = widget.filter_model.mapToSource(widget.filter_model.index(row, 0))
                    ledger = widget.ledger_model.get_ledger(source_index)
                    if ledger:
                        visible_ledgers.append(ledger)
                
                # Test export worker
                worker = DataExportWorker(visible_ledgers, temp_path, "csv")
                
                export_completed = False
                def on_export_completed(path):
                    nonlocal export_completed
                    export_completed = True
                
                worker.export_completed.connect(on_export_completed)
                worker.run()
                
                # Verify export
                assert export_completed
                assert Path(temp_path).exists()
                
                # Verify file content
                with open(temp_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    assert len(lines) > filtered_count  # Headers + data
                    assert "Ledger Name" in lines[0]
                
                logger.info("✅ Export workflow CSV test passed")
                
            finally:
                # Cleanup
                Path(temp_path).unlink(missing_ok=True)
            
        finally:
            widget.close()
    
    def test_data_update_workflow(self, qapp, sample_ledgers):
        """Test data update and refresh workflow"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        
        try:
            # Initial data load
            widget.set_ledger_data(sample_ledgers[:3])  # Load subset first
            initial_count = widget.get_visible_ledger_count()
            assert initial_count == 3
            
            # Apply filters
            widget.search_edit.setText("HDFC")
            QTest.wait(400)
            filtered_count = widget.get_visible_ledger_count()
            
            # Update with full data set
            widget.set_ledger_data(sample_ledgers)
            new_total = widget.get_total_ledger_count()
            assert new_total == len(sample_ledgers)
            
            # Filter should still be applied
            new_filtered_count = widget.get_visible_ledger_count()
            assert new_filtered_count >= filtered_count  # Should have same or more matches
            
            # Test refresh signal
            refresh_requested = False
            def on_refresh():
                nonlocal refresh_requested
                refresh_requested = True
            
            widget.refresh_requested.connect(on_refresh)
            widget._on_refresh_clicked()
            
            assert refresh_requested
            
            logger.info("✅ Data update workflow test passed")
            
        finally:
            widget.close()


# Test configuration and utilities

def pytest_configure(config):
    """Configure pytest for Qt testing"""
    config.addinivalue_line(
        "markers", "qt: mark test as requiring Qt application"
    )


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "--tb=short"])
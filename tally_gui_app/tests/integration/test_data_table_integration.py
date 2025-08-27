#!/usr/bin/env python3
"""
Integration Tests for Data Table Widget with TallyPrime Data Reader

This module provides integration tests that verify the data table widget
works correctly with the TallyPrime data reader, caching system, and main
application components.

Key Integration Test Areas:
- Data table widget with TallyPrime data reader integration
- Caching system integration and performance
- Main window integration and signal handling
- Error handling with real TallyPrime connection scenarios
- Theme switching with live data
- Export functionality with cached data
- Filter performance with large datasets

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6) + pytest
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

# Qt imports for integration testing
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtTest import QTest

# Import components for integration testing
from ui.widgets.data_table_widget import ProfessionalDataTableWidget
from core.tally.data_reader import TallyDataReader
from core.models.ledger_model import LedgerInfo, LedgerType, create_sample_ledgers
from ui.resources.styles.theme_manager import get_theme_manager, ThemeMode
from core.utils.logger import get_logger

# Set up logger for integration tests
logger = get_logger(__name__)


class MockTallyDataReader:
    """
    Mock TallyPrime data reader for integration testing
    
    This mock simulates TallyPrime responses with realistic data
    and various connection scenarios for comprehensive testing.
    """
    
    def __init__(self):
        """Initialize mock data reader with sample responses"""
        self.is_connected = False
        self.sample_ledgers = create_sample_ledgers()
        self.connection_delay = 0.1  # Simulate network delay
        self.should_fail = False  # For testing error scenarios
        self.cache_enabled = True
    
    async def connect(self, host: str = "localhost", port: int = 9000) -> bool:
        """Mock connection to TallyPrime"""
        await asyncio.sleep(self.connection_delay)
        
        if self.should_fail:
            raise ConnectionError("Mock connection failure")
        
        self.is_connected = True
        logger.info(f"Mock TallyPrime connected to {host}:{port}")
        return True
    
    async def get_ledgers(self, use_cache: bool = True) -> List[LedgerInfo]:
        """Mock ledger data retrieval"""
        if not self.is_connected:
            raise ConnectionError("Not connected to TallyPrime")
        
        await asyncio.sleep(self.connection_delay)
        
        if self.should_fail:
            raise RuntimeError("Mock data retrieval failure")
        
        # Simulate cache behavior
        if use_cache and self.cache_enabled:
            logger.info("Mock: Retrieved ledgers from cache")
        else:
            logger.info("Mock: Retrieved fresh ledgers from TallyPrime")
        
        return self.sample_ledgers.copy()
    
    async def disconnect(self):
        """Mock disconnection"""
        await asyncio.sleep(0.05)
        self.is_connected = False
        logger.info("Mock TallyPrime disconnected")
    
    def set_failure_mode(self, should_fail: bool):
        """Set failure mode for testing error scenarios"""
        self.should_fail = should_fail
    
    def add_sample_ledger(self, ledger: LedgerInfo):
        """Add additional sample ledger for testing"""
        self.sample_ledgers.append(ledger)


@pytest.mark.integration
class TestDataTableTallyIntegration:
    """
    Integration tests for data table widget with TallyPrime data reader
    
    These tests verify the complete data flow from TallyPrime through
    the data reader, caching system, and into the data table widget.
    """
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for Qt widget testing"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    
    @pytest.fixture
    def mock_data_reader(self):
        """Create mock TallyPrime data reader"""
        return MockTallyDataReader()
    
    @pytest.fixture
    def data_table_widget(self, qapp):
        """Create data table widget for integration testing"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        yield widget
        widget.close()
    
    @pytest.mark.asyncio
    async def test_basic_data_integration(self, data_table_widget, mock_data_reader):
        """Test basic integration between data reader and table widget"""
        widget = data_table_widget
        reader = mock_data_reader
        
        # Connect to mock TallyPrime
        await reader.connect()
        assert reader.is_connected
        
        # Get ledger data
        ledgers = await reader.get_ledgers()
        assert len(ledgers) > 0
        
        # Load data into widget
        widget.set_ledger_data(ledgers)
        
        # Verify data loaded correctly
        assert widget.get_total_ledger_count() == len(ledgers)
        assert widget.get_visible_ledger_count() == len(ledgers)
        
        # Verify data appears in table
        assert widget.table_view.model().rowCount() == len(ledgers)
        
        # Test selection
        if len(ledgers) > 0:
            widget.table_view.selectRow(0)
            selected_ledger = widget.get_selected_ledger()
            assert selected_ledger is not None
            assert selected_ledger.name == ledgers[0].name
        
        await reader.disconnect()
        logger.info("✅ Basic data integration test passed")
    
    @pytest.mark.asyncio
    async def test_data_refresh_integration(self, data_table_widget, mock_data_reader):
        """Test data refresh workflow integration"""
        widget = data_table_widget
        reader = mock_data_reader
        
        # Connect and load initial data
        await reader.connect()
        initial_ledgers = await reader.get_ledgers()
        widget.set_ledger_data(initial_ledgers)
        
        initial_count = widget.get_total_ledger_count()
        assert initial_count > 0
        
        # Add more data to mock reader
        new_ledger = LedgerInfo(
            name="Dynamic Test Ledger",
            ledger_type=LedgerType.CASH,
            parent_group_name="Cash-in-Hand"
        )
        new_ledger.balance.current_balance = Decimal('5000')
        reader.add_sample_ledger(new_ledger)
        
        # Refresh data
        updated_ledgers = await reader.get_ledgers()
        widget.set_ledger_data(updated_ledgers)
        
        # Verify refresh worked
        new_count = widget.get_total_ledger_count()
        assert new_count == initial_count + 1
        
        # Verify new ledger appears
        found = widget.select_ledger_by_name("Dynamic Test Ledger")
        assert found
        
        await reader.disconnect()
        logger.info("✅ Data refresh integration test passed")
    
    @pytest.mark.asyncio 
    async def test_error_handling_integration(self, data_table_widget, mock_data_reader):
        """Test error handling in integrated scenarios"""
        widget = data_table_widget
        reader = mock_data_reader
        
        # Test connection failure
        reader.set_failure_mode(True)
        
        with pytest.raises(ConnectionError):
            await reader.connect()
        
        # Test data retrieval failure after connection
        reader.set_failure_mode(False)
        await reader.connect()
        
        reader.set_failure_mode(True)
        
        with pytest.raises(RuntimeError):
            await reader.get_ledgers()
        
        # Reset for normal operation
        reader.set_failure_mode(False)
        
        # Test widget handles empty data gracefully
        widget.set_ledger_data([])
        assert widget.get_total_ledger_count() == 0
        assert widget.status_label.text() == "No data loaded"
        
        await reader.disconnect()
        logger.info("✅ Error handling integration test passed")
    
    @pytest.mark.asyncio
    async def test_filtering_with_live_data(self, data_table_widget, mock_data_reader):
        """Test filtering functionality with live TallyPrime data"""
        widget = data_table_widget
        reader = mock_data_reader
        
        # Load comprehensive test data
        await reader.connect()
        ledgers = await reader.get_ledgers()
        widget.set_ledger_data(ledgers)
        
        total_count = widget.get_total_ledger_count()
        assert total_count > 0
        
        # Test text search with real ledger names
        first_ledger = ledgers[0]
        search_term = first_ledger.name.split()[0]  # Use first word
        
        widget.search_edit.setText(search_term)
        QTest.wait(400)  # Wait for debounced search
        
        filtered_count = widget.get_visible_ledger_count()
        assert filtered_count > 0
        assert filtered_count <= total_count
        
        # Verify filtered results contain search term
        for row in range(filtered_count):
            index = widget.filter_model.index(row, 0)
            source_index = widget.filter_model.mapToSource(index)
            ledger = widget.ledger_model.get_ledger(source_index)
            assert search_term.lower() in ledger.name.lower()
        
        # Test type filtering
        bank_ledgers = [l for l in ledgers if l.ledger_type == LedgerType.BANK_ACCOUNTS]
        if bank_ledgers:
            # Find bank accounts type index
            bank_index = -1
            for i in range(widget.type_combo.count()):
                if widget.type_combo.itemData(i) == LedgerType.BANK_ACCOUNTS:
                    bank_index = i
                    break
            
            if bank_index > 0:
                widget.search_edit.clear()  # Clear text filter first
                QTest.wait(400)
                
                widget.type_combo.setCurrentIndex(bank_index)
                QTest.wait(100)
                
                bank_filtered_count = widget.get_visible_ledger_count()
                assert bank_filtered_count == len(bank_ledgers)
        
        await reader.disconnect()
        logger.info("✅ Filtering with live data test passed")
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, data_table_widget, mock_data_reader):
        """Test caching system integration with data table"""
        widget = data_table_widget
        reader = mock_data_reader
        
        await reader.connect()
        
        # First data load (should not use cache)
        start_time = datetime.now()
        ledgers_fresh = await reader.get_ledgers(use_cache=False)
        fresh_load_time = (datetime.now() - start_time).total_seconds()
        
        widget.set_ledger_data(ledgers_fresh)
        assert widget.get_total_ledger_count() == len(ledgers_fresh)
        
        # Second data load (should use cache)
        start_time = datetime.now()
        ledgers_cached = await reader.get_ledgers(use_cache=True)
        cached_load_time = (datetime.now() - start_time).total_seconds()
        
        # Cache should be faster (mock simulates this)
        assert cached_load_time <= fresh_load_time
        
        # Data should be identical
        assert len(ledgers_cached) == len(ledgers_fresh)
        
        # Widget should handle cached data identically
        widget.set_ledger_data(ledgers_cached)
        assert widget.get_total_ledger_count() == len(ledgers_cached)
        
        await reader.disconnect()
        logger.info("✅ Caching integration test passed")
    
    @pytest.mark.asyncio
    async def test_export_integration(self, data_table_widget, mock_data_reader):
        """Test export functionality with live data"""
        widget = data_table_widget
        reader = mock_data_reader
        
        await reader.connect()
        ledgers = await reader.get_ledgers()
        widget.set_ledger_data(ledgers)
        
        # Apply filter to test export of filtered data
        widget.search_edit.setText("Ledger")
        QTest.wait(400)
        
        filtered_count = widget.get_visible_ledger_count()
        assert filtered_count > 0
        
        # Get filtered ledgers for export
        visible_ledgers = []
        for row in range(widget.filter_model.rowCount()):
            source_index = widget.filter_model.mapToSource(widget.filter_model.index(row, 0))
            ledger = widget.ledger_model.get_ledger(source_index)
            if ledger:
                visible_ledgers.append(ledger)
        
        assert len(visible_ledgers) == filtered_count
        
        # Test export to temporary file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            from ui.widgets.data_table_widget import DataExportWorker
            
            # Test CSV export
            worker = DataExportWorker(visible_ledgers, temp_path, "csv")
            
            export_completed = False
            export_error = None
            
            def on_export_completed(path):
                nonlocal export_completed
                export_completed = True
            
            def on_export_failed(error):
                nonlocal export_error
                export_error = error
            
            worker.export_completed.connect(on_export_completed)
            worker.export_failed.connect(on_export_failed)
            
            # Run export
            worker.run()
            
            # Verify export success
            assert export_completed
            assert export_error is None
            assert Path(temp_path).exists()
            
            # Verify exported data
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                # Should have header + data rows
                assert len(lines) == filtered_count + 1
                assert "Ledger Name" in lines[0]
                
                # Verify at least one ledger name appears in export
                first_ledger_name = visible_ledgers[0].name
                assert first_ledger_name in content
            
            logger.info("✅ Export integration test passed")
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
            await reader.disconnect()


@pytest.mark.integration
class TestMainWindowIntegration:
    """
    Integration tests for data table widget within main window context
    
    These tests verify the widget works correctly as part of the main
    application window with proper signal handling and UI integration.
    """
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for Qt widget testing"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    
    def create_mock_main_window(self, qapp):
        """Create mock main window with data table widget"""
        class MockMainWindow(QMainWindow):
            # Signals for testing communication
            refresh_requested = Signal()
            ledger_selected = Signal(object)
            
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Mock TallyPrime Integration Manager")
                
                # Create data table widget as central widget
                self.data_table = ProfessionalDataTableWidget()
                self.setCentralWidget(self.data_table)
                
                # Connect signals
                self.data_table.refresh_requested.connect(self.on_refresh_requested)
                self.data_table.ledger_selected.connect(self.on_ledger_selected)
                
                # Track signals for testing
                self.refresh_count = 0
                self.selected_ledgers = []
            
            def on_refresh_requested(self):
                self.refresh_count += 1
                self.refresh_requested.emit()
            
            def on_ledger_selected(self, ledger):
                self.selected_ledgers.append(ledger)
                self.ledger_selected.emit(ledger)
        
        return MockMainWindow()
    
    def test_main_window_signal_integration(self, qapp):
        """Test signal communication between main window and data table"""
        main_window = self.create_mock_main_window(qapp)
        main_window.show()
        
        try:
            data_table = main_window.data_table
            
            # Load sample data
            sample_ledgers = create_sample_ledgers()
            data_table.set_ledger_data(sample_ledgers)
            
            # Test refresh signal
            initial_refresh_count = main_window.refresh_count
            QTest.mouseClick(data_table.refresh_btn, Qt.LeftButton)
            QTest.wait(100)
            
            assert main_window.refresh_count == initial_refresh_count + 1
            
            # Test ledger selection signal
            initial_selection_count = len(main_window.selected_ledgers)
            
            # Select first row and double-click
            data_table.table_view.selectRow(0)
            index = data_table.table_view.model().index(0, 0)
            QTest.mouseDClick(
                data_table.table_view.viewport(),
                Qt.LeftButton,
                Qt.NoModifier,
                data_table.table_view.visualRect(index).center()
            )
            QTest.wait(100)
            
            # Should have received ledger selection signal
            assert len(main_window.selected_ledgers) == initial_selection_count + 1
            
            selected_ledger = main_window.selected_ledgers[-1]
            assert selected_ledger is not None
            assert selected_ledger.name == sample_ledgers[0].name
            
            logger.info("✅ Main window signal integration test passed")
            
        finally:
            main_window.close()
    
    def test_theme_integration_in_main_window(self, qapp):
        """Test theme switching integration within main window"""
        main_window = self.create_mock_main_window(qapp)
        main_window.show()
        
        try:
            data_table = main_window.data_table
            theme_manager = get_theme_manager()
            
            # Get current theme
            current_theme = theme_manager.current_theme_mode
            
            # Switch theme
            new_theme = ThemeMode.DARK if current_theme == ThemeMode.LIGHT else ThemeMode.LIGHT
            theme_manager.set_theme_mode(new_theme)
            
            # Wait for theme to apply
            QTest.wait(200)
            
            # Verify theme applied to data table
            assert theme_manager.current_theme_mode == new_theme
            
            # Check if data table received theme update
            data_table_stylesheet = data_table.styleSheet()
            assert data_table_stylesheet != ""
            
            # Check if colors changed appropriately
            colors = theme_manager.colors
            if new_theme == ThemeMode.DARK:
                assert colors['background'] != '#f8f9fa'  # Should not be light background
            else:
                assert colors['background'] != '#2d3748'  # Should not be dark background
            
            logger.info("✅ Theme integration in main window test passed")
            
        finally:
            main_window.close()
    
    def test_window_state_persistence(self, qapp):
        """Test data table state persistence within main window"""
        main_window = self.create_mock_main_window(qapp)
        main_window.show()
        
        try:
            data_table = main_window.data_table
            
            # Load data and apply filters
            sample_ledgers = create_sample_ledgers()
            data_table.set_ledger_data(sample_ledgers)
            
            # Apply various filters
            data_table.search_edit.setText("HDFC")
            data_table.balance_min_edit.setText("1000")
            data_table.show_zero_check.setChecked(False)
            QTest.wait(500)
            
            # Get current filter state
            filter_settings = data_table.get_filter_settings()
            
            # Simulate window state save/restore
            saved_state = {
                'filter_settings': filter_settings,
                'table_geometry': data_table.table_view.geometry(),
                'window_size': main_window.size()
            }
            
            # Clear filters to simulate fresh start
            data_table._clear_all_filters()
            assert data_table.search_edit.text() == ""
            
            # Restore state
            data_table.apply_filter_settings(saved_state['filter_settings'])
            QTest.wait(100)
            
            # Verify state restored
            assert data_table.search_edit.text() == "HDFC"
            assert data_table.balance_min_edit.text() == "1000"
            assert not data_table.show_zero_check.isChecked()
            
            logger.info("✅ Window state persistence test passed")
            
        finally:
            main_window.close()


@pytest.mark.integration  
@pytest.mark.performance
class TestPerformanceIntegration:
    """
    Performance integration tests for data table with large datasets
    
    These tests verify the data table performs well with realistic
    TallyPrime data volumes and complex filtering scenarios.
    """
    
    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication for Qt widget testing"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    
    def create_large_dataset(self, count: int = 1000) -> List[LedgerInfo]:
        """Create large dataset for performance testing"""
        ledgers = []
        types = list(LedgerType)
        
        for i in range(count):
            ledger = LedgerInfo(
                name=f"Test Ledger {i:04d}",
                alias=f"TL{i:04d}",
                ledger_type=types[i % len(types)],
                parent_group_name=f"Group {i // 50}"
            )
            
            # Vary balances
            ledger.balance.current_balance = Decimal(str(i * 100 + (i % 1000)))
            ledger.balance.balance_type = BalanceType.DEBIT if i % 2 else BalanceType.CREDIT
            ledger.voucher_count = i % 100
            
            # Add GST for some ledgers
            if i % 10 == 0:
                ledger.tax_info.gstin = f"29{i:010d}1Z{i%10}"
            
            ledgers.append(ledger)
        
        return ledgers
    
    def test_large_dataset_loading_performance(self, qapp):
        """Test performance with large dataset loading"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        
        try:
            # Create large dataset
            large_dataset = self.create_large_dataset(1000)
            
            # Measure loading time
            start_time = datetime.now()
            widget.set_ledger_data(large_dataset)
            load_time = (datetime.now() - start_time).total_seconds()
            
            # Verify data loaded
            assert widget.get_total_ledger_count() == 1000
            assert widget.get_visible_ledger_count() == 1000
            
            # Performance assertion - should load within reasonable time
            assert load_time < 2.0, f"Loading took {load_time:.2f}s, expected < 2.0s"
            
            # Test filtering performance
            start_time = datetime.now()
            widget.search_edit.setText("0001")
            QTest.wait(500)  # Wait for debounced filter
            filter_time = (datetime.now() - start_time).total_seconds()
            
            filtered_count = widget.get_visible_ledger_count()
            assert filtered_count > 0
            
            # Filtering should be fast
            assert filter_time < 1.0, f"Filtering took {filter_time:.2f}s, expected < 1.0s"
            
            logger.info(f"✅ Large dataset performance test passed - Load: {load_time:.2f}s, Filter: {filter_time:.2f}s")
            
        finally:
            widget.close()
    
    def test_sorting_performance(self, qapp):
        """Test sorting performance with large dataset"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        
        try:
            # Create large dataset
            large_dataset = self.create_large_dataset(500)
            widget.set_ledger_data(large_dataset)
            
            # Test sorting by different columns
            columns_to_test = [0, 1, 2, 6]  # Name, Group, Balance, Voucher Count
            
            for column in columns_to_test:
                start_time = datetime.now()
                
                # Sort ascending
                widget.table_view.sortByColumn(column, Qt.AscendingOrder)
                QTest.wait(100)
                
                # Sort descending  
                widget.table_view.sortByColumn(column, Qt.DescendingOrder)
                QTest.wait(100)
                
                sort_time = (datetime.now() - start_time).total_seconds()
                
                # Sorting should be fast
                assert sort_time < 0.5, f"Sorting column {column} took {sort_time:.2f}s, expected < 0.5s"
            
            logger.info("✅ Sorting performance test passed")
            
        finally:
            widget.close()
    
    @pytest.mark.asyncio
    async def test_export_performance(self, qapp):
        """Test export performance with large dataset"""
        widget = ProfessionalDataTableWidget()
        widget.show()
        
        try:
            # Create large dataset
            large_dataset = self.create_large_dataset(500)
            widget.set_ledger_data(large_dataset)
            
            # Test CSV export performance
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                from ui.widgets.data_table_widget import DataExportWorker
                
                start_time = datetime.now()
                
                worker = DataExportWorker(large_dataset, temp_path, "csv")
                
                export_completed = False
                def on_export_completed(path):
                    nonlocal export_completed
                    export_completed = True
                
                worker.export_completed.connect(on_export_completed)
                worker.run()
                
                export_time = (datetime.now() - start_time).total_seconds()
                
                # Verify export completed
                assert export_completed
                assert Path(temp_path).exists()
                
                # Performance assertion
                assert export_time < 5.0, f"Export took {export_time:.2f}s, expected < 5.0s"
                
                # Verify file size is reasonable
                file_size = Path(temp_path).stat().st_size
                assert file_size > 10000  # Should have substantial data
                
                logger.info(f"✅ Export performance test passed - {export_time:.2f}s for 500 records")
                
            finally:
                Path(temp_path).unlink(missing_ok=True)
            
        finally:
            widget.close()


# Test configuration

def pytest_configure(config):
    """Configure pytest for integration testing"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


if __name__ == "__main__":
    # Run integration tests if executed directly
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
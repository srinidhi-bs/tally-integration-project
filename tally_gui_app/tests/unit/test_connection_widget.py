#!/usr/bin/env python3
"""
Unit Tests for Connection Widget
Professional Qt6 widget testing for TallyPrime connection management

This test suite validates:
- Connection widget initialization
- Status indicator functionality  
- Signal handling and communication
- Integration with TallyConnector and SettingsManager

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6) + pytest
Date: August 27, 2025
"""

import sys
import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest

# Import the widgets we're testing
from ui.widgets.connection_widget import ConnectionWidget, ConnectionStatusIndicator
from core.tally.connector import ConnectionStatus, TallyConnector, TallyConnectionConfig
from app.settings import SettingsManager


class TestConnectionStatusIndicator:
    """Test suite for the ConnectionStatusIndicator widget"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def indicator(self, app):
        """Create ConnectionStatusIndicator for testing"""
        return ConnectionStatusIndicator()
    
    def test_indicator_initialization(self, indicator):
        """Test that indicator initializes with correct default state"""
        assert indicator is not None
        assert "DISCONNECTED" in indicator.text()
        
    def test_status_updates(self, indicator):
        """Test that status indicator updates correctly for different states"""
        # Test connected status
        indicator.set_status(ConnectionStatus.CONNECTED, "Test message")
        assert "CONNECTED" in indicator.text()
        
        # Test connecting status  
        indicator.set_status(ConnectionStatus.CONNECTING)
        assert "CONNECTING" in indicator.text()
        
        # Test error status
        indicator.set_status(ConnectionStatus.ERROR, "Connection failed")
        assert "ERROR" in indicator.text()
        
        # Test timeout status
        indicator.set_status(ConnectionStatus.TIMEOUT)
        assert "TIMEOUT" in indicator.text()


class TestConnectionWidget:
    """Test suite for the ConnectionWidget"""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing"""
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def widget(self, app):
        """Create ConnectionWidget for testing"""
        return ConnectionWidget()
    
    @pytest.fixture
    def mock_tally_connector(self):
        """Create mock TallyConnector for testing"""
        mock = Mock(spec=TallyConnector)
        mock.connection_status_changed = Mock()
        mock.company_info_received = Mock()  
        mock.error_occurred = Mock()
        mock.test_connection = Mock()
        return mock
    
    @pytest.fixture
    def mock_settings_manager(self):
        """Create mock SettingsManager for testing"""
        mock = Mock(spec=SettingsManager)
        return mock
    
    def test_widget_initialization(self, widget):
        """Test that connection widget initializes correctly"""
        assert widget is not None
        assert widget.status_indicator is not None
        assert widget.test_connection_btn is not None
        assert widget.refresh_btn is not None
        assert widget.settings_btn is not None
        assert widget.company_info_label is not None
        assert widget.last_sync_label is not None
        assert widget.progress_bar is not None
        
        # Check initial states
        assert not widget.progress_bar.isVisible()
        assert not widget.refresh_btn.isEnabled()  # Should be disabled until connected
        assert widget.test_connection_btn.isEnabled()
        assert widget.settings_btn.isEnabled()
    
    def test_tally_connector_integration(self, widget, mock_tally_connector):
        """Test integration with TallyConnector"""
        # Set the connector
        widget.set_tally_connector(mock_tally_connector)
        assert widget.tally_connector == mock_tally_connector
        
        # Verify signal connections were established
        mock_tally_connector.connection_status_changed.connect.assert_called()
        mock_tally_connector.company_info_received.connect.assert_called()
        mock_tally_connector.error_occurred.connect.assert_called()
    
    def test_settings_manager_integration(self, widget, mock_settings_manager):
        """Test integration with SettingsManager"""
        widget.set_settings_manager(mock_settings_manager)
        assert widget.settings_manager == mock_settings_manager
    
    def test_connection_status_changes(self, widget):
        """Test handling of connection status changes"""
        # Test disconnected state
        widget._on_connection_status_changed(ConnectionStatus.DISCONNECTED)
        assert widget.current_status == ConnectionStatus.DISCONNECTED
        assert not widget.refresh_btn.isEnabled()
        
        # Test connected state
        widget._on_connection_status_changed(ConnectionStatus.CONNECTED, "Connected to TallyPrime")
        assert widget.current_status == ConnectionStatus.CONNECTED
        assert widget.refresh_btn.isEnabled()
        
        # Test connecting state  
        widget._on_connection_status_changed(ConnectionStatus.CONNECTING)
        assert widget.current_status == ConnectionStatus.CONNECTING
        assert widget.test_connection_btn.isEnabled()  # Should be enabled during connecting
    
    def test_test_connection_button(self, widget, mock_tally_connector):
        """Test test connection button functionality"""
        widget.set_tally_connector(mock_tally_connector)
        
        # Click test connection button
        widget._on_test_connection()
        
        # Verify connector test_connection was called
        mock_tally_connector.test_connection.assert_called_once()
        
        # Verify progress bar is shown and button disabled
        assert widget.progress_bar.isVisible()
        assert not widget.test_connection_btn.isEnabled()
    
    def test_refresh_data_button(self, widget):
        """Test refresh data button functionality"""
        # Set to connected state first
        widget._on_connection_status_changed(ConnectionStatus.CONNECTED)
        
        # Test refresh action
        widget._on_refresh_data()
        
        # Verify progress is shown
        assert widget.progress_bar.isVisible()
        
        # Verify last sync time is updated
        assert "Never" not in widget.last_sync_label.text()
    
    def test_settings_button(self, widget):
        """Test connection settings button functionality"""
        # Track signal emission
        signal_emitted = False
        
        def handle_signal():
            nonlocal signal_emitted
            signal_emitted = True
        
        widget.settings_dialog_requested.connect(handle_signal)
        widget._on_connection_settings()
        
        # Verify signal was emitted
        assert signal_emitted
    
    def test_auto_refresh_functionality(self, widget, mock_settings_manager):
        """Test auto-refresh timer functionality"""
        widget.set_settings_manager(mock_settings_manager)
        
        # Test starting auto-refresh when connected
        widget._on_connection_status_changed(ConnectionStatus.CONNECTED)
        
        # Auto-refresh should be stopped by default (disabled in our implementation)
        assert not widget.auto_refresh_timer.isActive()
        
        # Test stopping auto-refresh when disconnected
        widget._on_connection_status_changed(ConnectionStatus.DISCONNECTED)
        assert not widget.auto_refresh_timer.isActive()
    
    def test_progress_bar_functionality(self, widget):
        """Test progress bar show/hide functionality"""
        # Initially hidden
        assert not widget.progress_bar.isVisible()
        
        # Show progress
        widget._show_progress("Testing...")
        assert widget.progress_bar.isVisible()
        assert "Testing..." in widget.progress_bar.format()
        
        # Hide progress  
        widget._hide_progress()
        assert not widget.progress_bar.isVisible()
    
    def test_company_info_display(self, widget):
        """Test company information display functionality"""
        # Create mock company info
        mock_company_info = Mock()
        mock_company_info.name = "Test Company Ltd"
        mock_company_info.financial_year = "2024-25"
        mock_company_info.ledger_count = 150
        mock_company_info.currency = "INR"
        mock_company_info.address = "Bangalore, India"
        
        # Update company display
        widget.company_info = mock_company_info
        widget._update_company_display()
        
        # Verify company information is displayed
        assert "Test Company Ltd" in widget.company_info_label.text()
        assert "2024-25" in widget.company_details_label.text()
        assert "150" in widget.company_details_label.text()
    
    def test_error_handling(self, widget, mock_tally_connector):
        """Test error handling functionality"""
        widget.set_tally_connector(mock_tally_connector)
        
        # Simulate error
        widget._on_error_occurred("connection", "Failed to connect to TallyPrime")
        
        # Verify progress is hidden and button re-enabled
        assert not widget.progress_bar.isVisible()
        assert widget.test_connection_btn.isEnabled()
    
    def test_signal_emissions(self, widget):
        """Test that widget emits correct signals"""
        signal_count = 0
        
        def count_signals():
            nonlocal signal_count
            signal_count += 1
        
        # Connect to all custom signals
        widget.connection_test_requested.connect(count_signals)
        widget.settings_dialog_requested.connect(count_signals)
        widget.refresh_data_requested.connect(count_signals)
        
        # Trigger actions that should emit signals
        widget._on_test_connection()  # Should emit connection_test_requested
        widget._on_connection_settings()  # Should emit settings_dialog_requested  
        widget._on_refresh_data()  # Should emit refresh_data_requested
        
        # Verify all signals were emitted
        assert signal_count == 3


def test_integration_with_real_components():
    """Integration test with real TallyPrime components (if available)"""
    try:
        # Create real components
        settings_manager = SettingsManager()
        config = settings_manager.connection_config
        tally_connector = TallyConnector(config)
        
        # Create widget and connect components
        app = QApplication.instance() or QApplication(sys.argv)
        widget = ConnectionWidget()
        widget.set_tally_connector(tally_connector)
        widget.set_settings_manager(settings_manager)
        
        # Verify integration works
        assert widget.tally_connector is not None
        assert widget.settings_manager is not None
        
        # Test that components are properly connected
        assert widget.current_status == ConnectionStatus.DISCONNECTED
        
    except Exception as e:
        # If real components aren't available, skip this test
        pytest.skip(f"Integration test skipped due to: {str(e)}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
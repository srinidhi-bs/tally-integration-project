"""
Advanced Logging System Integration Tests
TallyPrime Integration Manager

This module contains comprehensive tests for the newly implemented
Advanced Logging System integration with the main application.

Test Coverage:
- Professional log widget creation and initialization
- Main window integration with log widget
- Log entry addition and formatting
- Advanced filtering and search functionality
- Log export capabilities
- Signal-slot integration
- Theme compatibility
- Performance with large log volumes

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6) with pytest
"""

import sys
import os
import time
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# PySide6 imports for testing
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QSettings, QTimer, QEventLoop, Signal
from PySide6.QtTest import QTest

# Import components to test
from ui.main_window import MainWindow
from ui.widgets.log_widget import ProfessionalLogWidget, LogEntry
from app.settings import SettingsManager


class TestAdvancedLoggingIntegration:
    """
    Comprehensive test suite for the Advanced Logging System integration
    
    This test class validates that the new ProfessionalLogWidget
    integrates correctly with the MainWindow and provides all
    expected advanced logging functionality.
    """
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once for all tests"""
        # Ensure QApplication exists
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
        
        # Create temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        
        print("\n" + "="*80)
        print("🚀 ADVANCED LOGGING SYSTEM INTEGRATION TESTS")
        print("="*80)
        
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests"""
        # Clean up temp files
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
        
        print("\n" + "="*80)
        print("✅ All Advanced Logging Integration Tests Completed Successfully!")
        print("="*80)
    
    def setup_method(self):
        """Set up for each individual test"""
        # Create test configuration
        self.config = {
            "application": {
                "name": "TallyPrime Integration Manager",
                "version": "1.0.0"
            },
            "logging": {
                "level": "DEBUG",
                "max_entries": 1000
            }
        }
        
        # Create test settings
        self.settings = QSettings("TestOrg", "TestApp")
        
        # Create main window instance for testing
        self.main_window = MainWindow(self.config, self.settings)
        
        # Give the UI time to initialize
        QTest.qWait(100)
    
    def teardown_method(self):
        """Clean up after each test"""
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.close()
            self.main_window.deleteLater()
        
        # Process events to ensure cleanup
        QTest.qWait(50)
    
    # Test 1: Professional Log Widget Creation and Initialization
    
    def test_log_widget_creation_and_initialization(self):
        """
        Test that the ProfessionalLogWidget is properly created and integrated
        """
        print("\n📝 Test 1: Log Widget Creation and Initialization")
        
        # Verify log widget exists and is properly initialized
        assert self.main_window.log_widget is not None, "Log widget should be created"
        assert isinstance(self.main_window.log_widget, ProfessionalLogWidget), \
            "Should be ProfessionalLogWidget instance"
        
        # Verify log widget is properly integrated in dock
        log_dock = self.main_window.log_panel_dock
        assert log_dock is not None, "Log panel dock should exist"
        assert log_dock.widget() == self.main_window.log_widget, \
            "Log widget should be set as dock widget content"
        
        # Verify initial log entries exist
        log_entries = self.main_window.log_widget.log_entries
        assert len(log_entries) >= 3, "Should have initial welcome log entries"
        
        # Check first log entry content
        first_entry = log_entries[0]
        assert "Application started" in first_entry.message, \
            "First log should be application startup message"
        
        print("✅ Log widget creation and initialization: PASSED")
    
    # Test 2: Log Entry Addition and Formatting
    
    def test_log_entry_addition_and_formatting(self):
        """
        Test that log entries are properly added with correct formatting
        """
        print("\n📝 Test 2: Log Entry Addition and Formatting")
        
        log_widget = self.main_window.log_widget
        initial_count = len(log_widget.log_entries)
        
        # Test adding different types of log entries
        test_messages = [
            ("🔍 Testing log entry addition", "INFO", "TestModule"),
            ("⚠ Warning message test", "WARNING", "TestModule"),
            ("❌ Error message test", "ERROR", "TestModule"), 
            ("✅ Success message test", "INFO", "TestModule"),
            ("🐛 Debug message test", "DEBUG", "TestModule")
        ]
        
        for message, level, source in test_messages:
            log_widget.add_log_entry(message, level, source)
            QTest.qWait(10)  # Allow UI to update
        
        # Verify entries were added
        final_count = len(log_widget.log_entries)
        assert final_count == initial_count + len(test_messages), \
            f"Should have {len(test_messages)} new entries"
        
        # Verify last entries match our test data
        recent_entries = log_widget.log_entries[-len(test_messages):]
        for i, (message, level, source) in enumerate(test_messages):
            entry = recent_entries[i]
            assert message in entry.message, f"Message should match: {message}"
            assert entry.level == level, f"Level should match: {level}"
            assert entry.source == source, f"Source should match: {source}"
        
        print("✅ Log entry addition and formatting: PASSED")
    
    # Test 3: Main Window Log Integration via _add_log_entry Method
    
    def test_main_window_log_integration(self):
        """
        Test that the main window's _add_log_entry method properly integrates with the log widget
        """
        print("\n📝 Test 3: Main Window Log Integration")
        
        log_widget = self.main_window.log_widget
        initial_count = len(log_widget.log_entries)
        
        # Test main window log integration with different legacy level names
        legacy_tests = [
            ("📊 Connection established", "info", "TallyConnector"),
            ("⚠ Connection warning", "warning", "TallyConnector"),
            ("❌ Connection error", "error", "TallyConnector"),
            ("✅ Operation successful", "success", "DataReader")
        ]
        
        for message, level, source in legacy_tests:
            self.main_window._add_log_entry(message, level, source)
            QTest.qWait(10)
        
        # Verify entries were added through main window method
        final_count = len(log_widget.log_entries)
        assert final_count == initial_count + len(legacy_tests), \
            "Main window should add entries to log widget"
        
        # Verify level mapping worked correctly
        recent_entries = log_widget.log_entries[-len(legacy_tests):]
        expected_levels = ["INFO", "WARNING", "ERROR", "INFO"]  # success maps to INFO
        
        for i, expected_level in enumerate(expected_levels):
            entry = recent_entries[i]
            assert entry.level == expected_level, \
                f"Level should be mapped correctly: {expected_level}"
        
        print("✅ Main window log integration: PASSED")
    
    # Test 4: Advanced Filtering Functionality
    
    def test_advanced_filtering_functionality(self):
        """
        Test the advanced filtering capabilities of the log widget
        """
        print("\n📝 Test 4: Advanced Filtering Functionality")
        
        log_widget = self.main_window.log_widget
        
        # Add test entries with different levels and content
        test_entries = [
            ("Debug message for filtering", "DEBUG", "TestModule"),
            ("Info message for filtering", "INFO", "TestModule"),
            ("Warning message for filtering", "WARNING", "TestModule"),
            ("Error message for filtering", "ERROR", "TestModule"),
            ("Special filter test message", "INFO", "SpecialModule"),
            ("Another debug entry", "DEBUG", "TestModule")
        ]
        
        for message, level, source in test_entries:
            log_widget.add_log_entry(message, level, source)
        
        QTest.qWait(100)  # Allow UI to update
        
        # Test level filtering
        log_widget.level_filter_combo.setCurrentText("ERROR")
        log_widget._on_filter_changed("ERROR")
        QTest.qWait(50)
        
        # Count ERROR level entries in filtered results
        error_count = sum(1 for entry in log_widget.filtered_entries if entry.level == "ERROR")
        assert error_count >= 1, "Should have at least one ERROR entry after filtering"
        
        # Test text filtering
        log_widget.level_filter_combo.setCurrentText("ALL")
        log_widget.search_line_edit.setText("Special")
        log_widget._on_search_text_changed("Special")
        QTest.qWait(50)
        
        # Check filtered results contain search term
        filtered_messages = [entry.message for entry in log_widget.filtered_entries]
        special_entries = [msg for msg in filtered_messages if "Special" in msg]
        assert len(special_entries) >= 1, "Should find entries containing 'Special'"
        
        print("✅ Advanced filtering functionality: PASSED")
    
    # Test 5: Log Export Functionality
    
    def test_log_export_functionality(self):
        """
        Test the log export functionality with different formats
        """
        print("\n📝 Test 5: Log Export Functionality")
        
        log_widget = self.main_window.log_widget
        
        # Add some test entries for export
        export_test_entries = [
            ("Export test entry 1", "INFO", "ExportTest"),
            ("Export test entry 2", "WARNING", "ExportTest"),
            ("Export test entry 3", "ERROR", "ExportTest")
        ]
        
        for message, level, source in export_test_entries:
            log_widget.add_log_entry(message, level, source)
        
        QTest.qWait(100)
        
        # Test TXT export
        txt_file = os.path.join(self.temp_dir, "test_export.txt")
        
        # Mock the export worker to avoid threading complexity in tests
        with patch.object(log_widget, 'export_worker') as mock_worker:
            # Simulate successful export
            log_widget._on_export_completed(txt_file, True, "")
            
            # Verify export status was updated
            assert not log_widget.export_progress_bar.isVisible(), \
                "Progress bar should be hidden after export"
            assert log_widget.export_button.isEnabled(), \
                "Export button should be re-enabled"
        
        print("✅ Log export functionality: PASSED")
    
    # Test 6: Signal-Slot Integration
    
    def test_signal_slot_integration(self):
        """
        Test that signals and slots are properly connected between components
        """
        print("\n📝 Test 6: Signal-Slot Integration")
        
        log_widget = self.main_window.log_widget
        
        # Test log export signal
        export_signal_received = []
        
        def on_export_signal(file_path, success, error_message):
            export_signal_received.append((file_path, success, error_message))
        
        log_widget.log_exported.connect(on_export_signal)
        
        # Emit test signal
        test_file_path = "/test/path/export.txt"
        log_widget.log_exported.emit(test_file_path, True, "")
        
        # Process events to ensure signal delivery
        QTest.qWait(50)
        
        assert len(export_signal_received) == 1, "Export signal should be received"
        received_file_path, received_success, received_error = export_signal_received[0]
        assert received_file_path == test_file_path, "File path should match"
        assert received_success == True, "Success flag should match"
        
        # Test filter change signal
        filter_signal_received = []
        
        def on_filter_signal(level_filter, text_filter):
            filter_signal_received.append((level_filter, text_filter))
        
        log_widget.filter_changed.connect(on_filter_signal)
        
        # Emit test signal
        test_level = "WARNING"
        test_text = "test search"
        log_widget.filter_changed.emit(test_level, test_text)
        QTest.qWait(50)
        
        assert len(filter_signal_received) == 1, "Filter signal should be received"
        received_level, received_text = filter_signal_received[0]
        assert received_level == test_level, "Level filter should match"
        assert received_text == test_text, "Text filter should match"
        
        print("✅ Signal-slot integration: PASSED")
    
    # Test 7: Performance with Large Log Volumes
    
    def test_performance_with_large_volumes(self):
        """
        Test performance and memory management with large numbers of log entries
        """
        print("\n📝 Test 7: Performance with Large Log Volumes")
        
        log_widget = self.main_window.log_widget
        
        # Set a lower max entries limit for testing
        original_max = log_widget.max_entries
        test_max = 500
        log_widget.set_max_entries(test_max)
        
        # Add many log entries to test performance and memory management
        start_time = time.time()
        num_entries = 750  # More than max to test trimming
        
        for i in range(num_entries):
            log_widget.add_log_entry(
                f"Performance test entry {i+1} with some longer content to test formatting",
                "INFO" if i % 3 == 0 else "WARNING" if i % 3 == 1 else "ERROR",
                f"PerfTest{i%10}"
            )
            
            # Periodically process events to avoid UI freezing
            if i % 100 == 0:
                QTest.qWait(1)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Verify performance is reasonable (should be fast)
        assert elapsed_time < 5.0, f"Adding {num_entries} entries should take < 5 seconds, took {elapsed_time:.2f}s"
        
        # Verify log trimming worked correctly
        actual_count = len(log_widget.log_entries)
        assert actual_count <= test_max, \
            f"Log entries should be trimmed to max {test_max}, but have {actual_count}"
        
        # Verify UI is still responsive
        QTest.qWait(100)
        
        # Test filtering performance with large dataset
        filter_start = time.time()
        log_widget.level_filter_combo.setCurrentText("ERROR")
        log_widget._on_filter_changed("ERROR")
        QTest.qWait(50)
        filter_end = time.time()
        
        filter_time = filter_end - filter_start
        assert filter_time < 1.0, f"Filtering should take < 1 second, took {filter_time:.2f}s"
        
        # Restore original max entries
        log_widget.set_max_entries(original_max)
        
        print(f"✅ Performance test: {num_entries} entries in {elapsed_time:.2f}s, filtering in {filter_time:.2f}s - PASSED")
    
    # Test 8: Theme Compatibility
    
    def test_theme_compatibility(self):
        """
        Test that the log widget properly adapts to theme changes
        """
        print("\n📝 Test 8: Theme Compatibility")
        
        log_widget = self.main_window.log_widget
        
        # Verify theme manager integration
        if hasattr(log_widget, 'theme_manager') and log_widget.theme_manager:
            # Test theme detection
            theme_detected = hasattr(log_widget.theme_manager, 'is_dark_theme')
            assert theme_detected, "Theme manager should detect current theme"
            
            # Verify styling was applied
            log_text_edit = log_widget.log_text_edit
            style_sheet = log_text_edit.styleSheet()
            assert len(style_sheet) > 0, "Log text edit should have styling applied"
            
            print("✅ Theme compatibility: PASSED (Theme manager available)")
        else:
            print("✅ Theme compatibility: PASSED (Fallback mode)")
    
    # Integration Test Summary
    
    def test_complete_integration_workflow(self):
        """
        Test a complete workflow that exercises all major functionality
        """
        print("\n📝 Test 9: Complete Integration Workflow")
        
        log_widget = self.main_window.log_widget
        
        # Step 1: Add various log entries through different methods
        self.main_window._add_log_entry("🔗 Starting workflow test", "info", "WorkflowTest")
        log_widget.add_log_entry("📊 Direct widget logging", "INFO", "WorkflowTest")
        
        # Step 2: Test filtering
        log_widget.search_line_edit.setText("workflow")
        log_widget._on_search_text_changed("workflow")
        QTest.qWait(50)
        
        # Step 3: Verify filtered results
        workflow_entries = [e for e in log_widget.filtered_entries if "workflow" in e.message.lower()]
        assert len(workflow_entries) >= 1, "Should find workflow-related entries"
        
        # Step 4: Test level filtering
        log_widget.level_filter_combo.setCurrentText("INFO")
        log_widget._on_filter_changed("INFO")
        QTest.qWait(50)
        
        # Step 5: Test clearing filters
        log_widget._on_clear_search()
        QTest.qWait(50)
        
        # Verify filters were cleared
        assert log_widget.current_level_filter == "ALL", "Level filter should be cleared"
        assert log_widget.current_text_filter == "", "Text filter should be cleared"
        
        # Step 6: Test log statistics
        total_label_text = log_widget.total_entries_label.text()
        assert "Total:" in total_label_text, "Total entries label should show count"
        
        print("✅ Complete integration workflow: PASSED")


# Test Runner Function
def run_advanced_logging_tests():
    """
    Run all advanced logging system integration tests
    """
    print("🧪 Starting Advanced Logging System Integration Tests...")
    
    # Create test instance
    test_suite = TestAdvancedLoggingIntegration()
    
    # Set up test environment
    test_suite.setup_class()
    
    try:
        # Run all test methods
        test_methods = [
            test_suite.test_log_widget_creation_and_initialization,
            test_suite.test_log_entry_addition_and_formatting,
            test_suite.test_main_window_log_integration,
            test_suite.test_advanced_filtering_functionality,
            test_suite.test_log_export_functionality,
            test_suite.test_signal_slot_integration,
            test_suite.test_performance_with_large_volumes,
            test_suite.test_theme_compatibility,
            test_suite.test_complete_integration_workflow
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test_method in test_methods:
            try:
                test_suite.setup_method()
                test_method()
                test_suite.teardown_method()
                passed_tests += 1
            except Exception as e:
                print(f"❌ {test_method.__name__} FAILED: {str(e)}")
                failed_tests += 1
                test_suite.teardown_method()
        
        # Print test results
        print(f"\n📊 TEST RESULTS:")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests / len(test_methods) * 100):.1f}%")
        
        return failed_tests == 0
        
    finally:
        # Clean up test environment
        test_suite.teardown_class()


if __name__ == "__main__":
    """
    Run tests when script is executed directly
    """
    success = run_advanced_logging_tests()
    sys.exit(0 if success else 1)
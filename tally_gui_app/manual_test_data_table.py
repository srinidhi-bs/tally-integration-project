#!/usr/bin/env python3
"""
Manual Test Script for Professional Data Table Widget

This script provides a simple way to manually test the data table widget
functionality without requiring a full TallyPrime connection.

Usage: python3 manual_test_data_table.py

Author: Srinidhi BS (Learning to code)
Assistant: Claude (Anthropic)
Date: August 27, 2025
Framework: PySide6 (Qt6)
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
    from PySide6.QtCore import Qt
    
    # Import our data table widget and models
    from ui.widgets.data_table_widget import ProfessionalDataTableWidget
    from core.models.ledger_model import create_sample_ledgers
    from ui.resources.styles.theme_manager import get_theme_manager, ThemeMode
    from core.utils.logger import setup_logger, get_logger
    
    # Set up logging
    setup_logger()
    logger = get_logger(__name__)
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have PySide6 installed: pip3 install PySide6")
    sys.exit(1)


class DataTableTestWindow(QMainWindow):
    """
    Test window for data table widget
    
    This window provides a simple interface to test all the features
    of the professional data table widget with sample data.
    """
    
    def __init__(self):
        """Initialize the test window"""
        super().__init__()
        
        self.setWindowTitle("TallyPrime Data Table Widget - Manual Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Initializing data table...")
        layout.addWidget(self.status_label)
        
        # Add control buttons
        self.create_control_panel(layout)
        
        # Create data table widget
        self.data_table = ProfessionalDataTableWidget()
        layout.addWidget(self.data_table)
        
        # Connect signals
        self.data_table.ledger_selected.connect(self.on_ledger_selected)
        self.data_table.refresh_requested.connect(self.on_refresh_requested)
        self.data_table.filter_changed.connect(self.on_filter_changed)
        
        # Load sample data
        self.load_sample_data()
        
        logger.info("Data table test window initialized")
    
    def create_control_panel(self, layout):
        """Create control buttons for testing"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Load data button
        self.load_data_btn = QPushButton("🔄 Load Sample Data")
        self.load_data_btn.clicked.connect(self.load_sample_data)
        control_layout.addWidget(self.load_data_btn)
        
        # Theme toggle button
        self.theme_btn = QPushButton("🌙 Toggle Dark Theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.theme_btn)
        
        # Clear data button
        self.clear_data_btn = QPushButton("🗑️ Clear Data")
        self.clear_data_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(self.clear_data_btn)
        
        control_widget.setMaximumHeight(120)
        layout.addWidget(control_widget)
    
    def load_sample_data(self):
        """Load sample ledger data into the table"""
        try:
            sample_ledgers = create_sample_ledgers()
            self.data_table.set_ledger_data(sample_ledgers)
            self.status_label.setText(f"✅ Loaded {len(sample_ledgers)} sample ledgers")
            logger.info(f"Loaded {len(sample_ledgers)} sample ledgers")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error loading data: {e}")
            logger.error(f"Error loading sample data: {e}")
    
    def clear_data(self):
        """Clear all data from the table"""
        self.data_table.set_ledger_data([])
        self.status_label.setText("🗑️ Data cleared")
        logger.info("Data cleared")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        try:
            theme_manager = get_theme_manager()
            current_theme = theme_manager.current_theme_mode
            
            # Toggle theme
            new_theme = ThemeMode.DARK if current_theme == ThemeMode.LIGHT else ThemeMode.LIGHT
            theme_manager.set_theme_mode(new_theme)
            
            # Update button text
            if new_theme == ThemeMode.DARK:
                self.theme_btn.setText("☀️ Toggle Light Theme")
                self.status_label.setText("🌙 Switched to dark theme")
            else:
                self.theme_btn.setText("🌙 Toggle Dark Theme")
                self.status_label.setText("☀️ Switched to light theme")
            
            logger.info(f"Theme switched to: {new_theme.value}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Theme switch error: {e}")
            logger.error(f"Error switching theme: {e}")
    
    def on_ledger_selected(self, ledger):
        """Handle ledger selection"""
        self.status_label.setText(f"📋 Selected: {ledger.name} (Balance: {ledger.get_balance_display()})")
        logger.info(f"Ledger selected: {ledger.name}")
    
    def on_refresh_requested(self):
        """Handle refresh request"""
        self.status_label.setText("🔄 Refresh requested - reloading data...")
        # Simulate refresh by reloading sample data
        self.load_sample_data()
        logger.info("Refresh requested")
    
    def on_filter_changed(self, filter_settings):
        """Handle filter changes"""
        active_filters = []
        
        if filter_settings.get('search_text'):
            active_filters.append(f"Search: '{filter_settings['search_text']}'")
        
        if filter_settings.get('type_filter'):
            active_filters.append(f"Type: {filter_settings['type_filter'].value}")
        
        if filter_settings.get('min_balance') or filter_settings.get('max_balance'):
            balance_filter = f"Balance: {filter_settings.get('min_balance', 'Any')} to {filter_settings.get('max_balance', 'Any')}"
            active_filters.append(balance_filter)
        
        if not filter_settings.get('show_zero_balances', True):
            active_filters.append("Hide zero balances")
        
        if active_filters:
            filter_text = " | ".join(active_filters)
            self.status_label.setText(f"🔍 Filters: {filter_text}")
        else:
            self.status_label.setText("🔍 No filters applied")
        
        logger.debug(f"Filter changed: {filter_settings}")


def main():
    """Main function to run the manual test"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("TallyPrime Data Table Test")
    app.setOrganizationName("Srinidhi BS")
    
    try:
        # Create and show test window
        window = DataTableTestWindow()
        window.show()
        
        print("\n" + "="*60)
        print("🚀 TallyPrime Data Table Widget - Manual Test")
        print("="*60)
        print("📋 Features to test:")
        print("   • Search and filtering (type in search box)")
        print("   • Type filtering (use dropdown)")
        print("   • Balance range filtering (min/max inputs)")
        print("   • Sorting (click column headers)")
        print("   • Row selection (double-click rows)")
        print("   • Context menu (right-click on rows)")
        print("   • Export functionality (Export button)")
        print("   • Theme switching (Toggle Theme button)")
        print("   • Keyboard shortcuts:")
        print("     - F5: Refresh data")
        print("     - Ctrl+F: Focus search")
        print("     - Ctrl+E: Export")
        print("     - Ctrl+R: Clear filters")
        print("\n🎯 Test all features and verify they work correctly!")
        print("="*60)
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        logger.error(f"Error running manual test: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
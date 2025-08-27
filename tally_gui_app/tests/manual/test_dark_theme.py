#!/usr/bin/env python3
"""
Dark Theme Support Test for TallyPrime Integration Manager
Test the application's dark theme compatibility and automatic theme detection

This test verifies:
- Automatic Windows theme detection
- Proper text visibility in dark mode
- Professional styling in both light and dark themes
- Dynamic theme switching capabilities

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
Date: August 27, 2025
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# PySide6 imports
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt, QTimer

# Import our components
from ui.dialogs.connection_dialog import ConnectionDialog
from ui.widgets.connection_widget import ConnectionWidget
from ui.resources.styles.theme_manager import get_theme_manager, ThemeMode
from app.settings import SettingsManager
from core.tally.connector import TallyConnector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThemeTestWindow(QMainWindow):
    """Test window for theme functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dark Theme Test - TallyPrime Integration Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # Set up UI
        self._setup_ui()
        
        # Apply theme
        self._apply_theme()
    
    def _setup_ui(self):
        """Set up the test UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Theme info
        theme_manager = get_theme_manager()
        theme_info = QLabel(f"Current Theme: {theme_manager.current_theme_mode.value.title()}")
        theme_info.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(theme_info)
        
        # Test buttons
        test_dialog_btn = QPushButton("🔧 Test Connection Settings Dialog")
        test_dialog_btn.clicked.connect(self._test_connection_dialog)
        layout.addWidget(test_dialog_btn)
        
        test_widget_btn = QPushButton("🔗 Test Connection Widget")
        test_widget_btn.clicked.connect(self._test_connection_widget)
        layout.addWidget(test_widget_btn)
        
        switch_theme_btn = QPushButton("🌓 Switch Theme Mode")
        switch_theme_btn.clicked.connect(self._switch_theme)
        layout.addWidget(switch_theme_btn)
        
        refresh_theme_btn = QPushButton("🔄 Refresh System Theme")
        refresh_theme_btn.clicked.connect(self._refresh_theme)
        layout.addWidget(refresh_theme_btn)
        
        # Instructions
        instructions = QLabel("""
Instructions for Dark Theme Testing:

1. 🖥️ Change Windows Theme:
   - Press Win + I → Personalization → Colors
   - Switch between Light and Dark mode
   - Click "Refresh System Theme" to detect changes

2. 🔧 Test Components:
   - Click "Test Connection Settings Dialog" 
   - Verify all text is visible and readable
   - Check that colors have good contrast

3. 🔗 Test Connection Widget:
   - Click "Test Connection Widget"
   - Check labels, buttons, and status indicators
   - Verify professional appearance

4. 🌓 Manual Theme Switch:
   - Click "Switch Theme Mode" to manually toggle
   - See immediate theme changes
   
Expected Behavior:
✅ All text should be clearly visible
✅ Professional color scheme in both modes  
✅ Buttons and inputs should be readable
✅ No invisible text or poor contrast
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                padding: 16px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(instructions)
        
        # Status
        self.status_label = QLabel("Ready for testing...")
        self.status_label.setStyleSheet("font-style: italic; padding: 4px;")
        layout.addWidget(self.status_label)
        
    def _apply_theme(self):
        """Apply theme to this window"""
        theme_manager = get_theme_manager()
        if theme_manager.is_dark_theme:
            # Dark theme for test window
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2d3748;
                    color: #f7fafc;
                }
                QLabel {
                    color: #e2e8f0;
                }
                QPushButton {
                    background-color: #4299e1;
                    border: none;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #3182ce;
                }
                QPushButton:pressed {
                    background-color: #2c5282;
                }
            """)
        else:
            # Light theme for test window
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                }
                QLabel {
                    color: #2c3e50;
                }
                QPushButton {
                    background-color: #3498db;
                    border: none;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """)
    
    def _test_connection_dialog(self):
        """Test connection settings dialog"""
        try:
            self.status_label.setText("Opening connection settings dialog...")
            
            # Create settings manager and dialog
            settings_manager = SettingsManager()
            dialog = ConnectionDialog(parent=self, settings_manager=settings_manager)
            
            # Show dialog
            result = dialog.exec()
            
            if result == ConnectionDialog.Accepted:
                self.status_label.setText("✅ Connection dialog test completed - settings saved")
            else:
                self.status_label.setText("ℹ️ Connection dialog test completed - cancelled")
                
            logger.info("Connection dialog theme test completed")
            
        except Exception as e:
            self.status_label.setText(f"❌ Connection dialog test failed: {str(e)}")
            logger.error(f"Connection dialog test error: {e}")
    
    def _test_connection_widget(self):
        """Test connection widget"""
        try:
            self.status_label.setText("Creating connection widget test...")
            
            # Create a simple test window for the widget
            test_window = QMainWindow()
            test_window.setWindowTitle("Connection Widget Theme Test")
            test_window.setGeometry(150, 150, 400, 600)
            
            # Create connection widget
            settings_manager = SettingsManager()
            connector = TallyConnector(settings_manager.connection_config)
            
            widget = ConnectionWidget()
            widget.set_tally_connector(connector)
            widget.set_settings_manager(settings_manager)
            
            test_window.setCentralWidget(widget)
            
            # Apply theme to test window
            theme_manager = get_theme_manager()
            if theme_manager.is_dark_theme:
                test_window.setStyleSheet("QMainWindow { background-color: #2d3748; }")
            else:
                test_window.setStyleSheet("QMainWindow { background-color: #f8f9fa; }")
            
            test_window.show()
            
            self.status_label.setText("✅ Connection widget opened in separate window")
            logger.info("Connection widget theme test window opened")
            
        except Exception as e:
            self.status_label.setText(f"❌ Connection widget test failed: {str(e)}")
            logger.error(f"Connection widget test error: {e}")
    
    def _switch_theme(self):
        """Manually switch theme mode"""
        try:
            theme_manager = get_theme_manager()
            current_mode = theme_manager.current_theme_mode
            
            if current_mode == ThemeMode.LIGHT:
                new_mode = ThemeMode.DARK
            else:
                new_mode = ThemeMode.LIGHT
            
            theme_manager.set_theme_mode(new_mode)
            
            # Reapply theme to this window
            self._apply_theme()
            
            self.status_label.setText(f"🌓 Theme switched to: {new_mode.value.title()}")
            logger.info(f"Manual theme switch to: {new_mode.value}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Theme switch failed: {str(e)}")
            logger.error(f"Theme switch error: {e}")
    
    def _refresh_theme(self):
        """Refresh system theme detection"""
        try:
            theme_manager = get_theme_manager()
            old_mode = theme_manager.current_theme_mode
            
            # Refresh system theme detection
            theme_manager.refresh_system_theme()
            theme_manager.set_theme_mode(ThemeMode.AUTO)  # Switch to auto mode
            
            new_mode = theme_manager.current_theme_mode
            
            # Reapply theme if changed
            if new_mode != old_mode:
                self._apply_theme()
            
            self.status_label.setText(f"🔄 System theme refreshed: {new_mode.value.title()}")
            logger.info(f"System theme refresh: {old_mode.value} → {new_mode.value}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Theme refresh failed: {str(e)}")
            logger.error(f"Theme refresh error: {e}")


def main():
    """Main test function"""
    logger.info("🎨 Starting Dark Theme Support Test")
    
    # Create application
    app = QApplication(sys.argv)
    
    # Show initial theme information
    theme_manager = get_theme_manager()
    logger.info(f"Detected system theme: {theme_manager.current_theme_mode.value}")
    
    # Create and show test window
    test_window = ThemeTestWindow()
    test_window.show()
    
    # Show info message
    QMessageBox.information(
        test_window,
        "Dark Theme Test",
        "Dark Theme Support Test is running!\n\n"
        "This test helps verify that:\n"
        "• Text is visible in Windows Dark Mode\n"
        "• Professional styling works in both themes\n"
        "• Components handle theme changes properly\n\n"
        "Follow the on-screen instructions to test thoroughly."
    )
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Quick Test for Main Window -> Connection Dialog Integration
Tests that the settings dialog can be opened from the main window

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
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Import application
from main import main as app_main
from ui.main_window import MainWindow
from app.application import TallyIntegrationApp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_main_window_dialog_integration():
    """Test that settings dialog opens from main window"""
    try:
        logger.info("Testing main window -> settings dialog integration...")
        
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create the main application instance
        tally_app = TallyIntegrationApp()
        
        # Get the main window
        main_window = tally_app.main_window
        
        # Test that settings manager is available
        assert main_window.settings_manager is not None
        logger.info("✅ Settings manager is available in main window")
        
        # Test that connection widget is available and connected
        assert main_window.connection_widget is not None
        logger.info("✅ Connection widget is available")
        
        # Test that the settings dialog can be triggered
        # This should work without errors
        main_window._on_settings()
        logger.info("✅ Settings dialog can be opened from main window")
        
        # Clean up
        main_window.close()
        
        logger.info("🎉 Main window dialog integration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Main window dialog integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Run test
    success = test_main_window_dialog_integration()
    
    if success:
        logger.info("✅ Integration test completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Integration test failed")
        sys.exit(1)
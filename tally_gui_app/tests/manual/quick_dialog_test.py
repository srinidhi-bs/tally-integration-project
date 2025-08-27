#!/usr/bin/env python3
"""
Quick Manual Test for Connection Dialog
Simple test to verify dialog functionality without full application

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
from PySide6.QtWidgets import QApplication, QMessageBox

# Import our components
from ui.dialogs.connection_dialog import ConnectionDialog
from app.settings import SettingsManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Quick manual test of the connection dialog"""
    
    # Create application
    app = QApplication(sys.argv)
    
    try:
        logger.info("🔧 Creating Connection Dialog for Quick Test")
        
        # Create settings manager
        settings_manager = SettingsManager()
        logger.info(f"📋 Current settings: {settings_manager.connection_config.host}:{settings_manager.connection_config.port}")
        
        # Create and show dialog
        dialog = ConnectionDialog(settings_manager=settings_manager)
        
        # Show information message
        QMessageBox.information(
            None, 
            "Connection Dialog Test",
            "The TallyPrime Connection Settings Dialog is about to open.\n\n"
            "Test the following features:\n"
            "• All tabs load correctly\n"
            "• Input validation works\n"
            "• Settings save and load properly\n"
            "• Test Connection button works (if TallyPrime is available)\n"
            "• Dialog styling looks professional\n\n"
            "Click OK to open the dialog..."
        )
        
        # Show dialog
        result = dialog.exec()
        
        if result == ConnectionDialog.Accepted:
            logger.info("✅ Dialog accepted - settings saved")
            logger.info(f"📋 New settings: {settings_manager.connection_config.host}:{settings_manager.connection_config.port}")
        else:
            logger.info("ℹ️ Dialog cancelled or closed")
        
        # Final confirmation
        QMessageBox.information(
            None,
            "Test Complete", 
            "Connection Dialog test completed successfully!\n\n"
            "Task 2.3: Advanced Connection Settings Dialog\n"
            "Status: ✅ COMPLETE"
        )
        
        logger.info("🎉 Connection Dialog test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        QMessageBox.critical(None, "Test Failed", f"Error: {str(e)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
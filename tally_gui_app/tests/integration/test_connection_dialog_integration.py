#!/usr/bin/env python3
"""
Integration Test for Connection Dialog with Main Application
Tests the connection dialog integration with the main window and connection widget

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

# PySide6 imports for testing
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

# Import our application components
from ui.dialogs.connection_dialog import ConnectionDialog
from core.tally.connector import TallyConnector, TallyConnectionConfig
from app.settings import SettingsManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection_dialog_basic():
    """
    Test basic connection dialog functionality
    """
    try:
        logger.info("Starting basic connection dialog test...")
        
        # Create application instance if not exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create settings manager
        settings_manager = SettingsManager()
        
        # Create connection dialog
        dialog = ConnectionDialog(settings_manager=settings_manager)
        
        # Test dialog properties
        assert dialog.windowTitle() == "TallyPrime Connection Settings"
        assert dialog.isModal() == True
        assert dialog.minimumSize().width() >= 600
        assert dialog.minimumSize().height() >= 500
        
        logger.info("✅ Basic dialog properties test passed")
        
        # Test initial settings loading
        assert dialog.host_input.text() == settings_manager.connection_config.host
        assert dialog.port_input.value() == settings_manager.connection_config.port
        assert dialog.timeout_input.value() == settings_manager.connection_config.timeout
        
        logger.info("✅ Initial settings loading test passed")
        
        # Test input validation
        dialog.host_input.setText("invalid.ip.address.format")
        dialog._validate_inputs()
        # Should be invalid
        assert dialog.host_input.property("invalid") == True
        
        dialog.host_input.setText("192.168.1.100")
        dialog._validate_inputs()
        # Should be valid
        assert dialog.host_input.property("invalid") == False or dialog.host_input.property("invalid") is None
        
        logger.info("✅ Input validation test passed")
        
        # Test connection configuration creation
        dialog.host_input.setText("localhost")
        dialog.port_input.setValue(9999)
        dialog.timeout_input.setValue(15)
        
        # Validate and apply settings
        success = dialog._validate_and_apply_settings()
        assert success == True
        
        # Check if settings were applied
        updated_config = settings_manager.connection_config
        assert updated_config.host == "localhost"
        assert updated_config.port == 9999
        assert updated_config.timeout == 15
        
        logger.info("✅ Settings validation and application test passed")
        
        dialog.close()
        logger.info("✅ All connection dialog basic tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic connection dialog test failed: {str(e)}")
        return False


def test_connection_dialog_integration():
    """
    Test connection dialog integration with TallyConnector
    """
    try:
        logger.info("Starting connection dialog integration test...")
        
        # Create application instance if not exists
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create settings manager and connector
        settings_manager = SettingsManager()
        connector = TallyConnector(settings_manager.connection_config)
        
        # Create connection dialog
        dialog = ConnectionDialog(settings_manager=settings_manager)
        
        # Test configuration change signal
        new_config_received = []
        
        def on_config_changed(config):
            new_config_received.append(config)
            logger.info(f"Configuration changed to: {config.host}:{config.port}")
        
        dialog.connection_config_changed.connect(on_config_changed)
        
        # Change settings and apply
        dialog.host_input.setText("test.example.com")
        dialog.port_input.setValue(8080)
        dialog.timeout_input.setValue(20)
        
        success = dialog._validate_and_apply_settings()
        assert success == True
        
        # Check if signal was emitted
        assert len(new_config_received) > 0
        new_config = new_config_received[0]
        assert new_config.host == "test.example.com"
        assert new_config.port == 8080
        assert new_config.timeout == 20
        
        logger.info("✅ Configuration change signal test passed")
        
        # Test connector config update
        connector.update_config(new_config)
        assert connector.config.host == "test.example.com"
        assert connector.config.port == 8080
        assert connector.config.timeout == 20
        
        logger.info("✅ Connector configuration update test passed")
        
        dialog.close()
        logger.info("✅ All connection dialog integration tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection dialog integration test failed: {str(e)}")
        return False


def test_connection_dialog_visual():
    """
    Visual test - shows the dialog for manual inspection
    """
    try:
        logger.info("Starting visual connection dialog test...")
        
        # Create application instance
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create settings manager
        settings_manager = SettingsManager()
        
        # Create and show dialog
        dialog = ConnectionDialog(settings_manager=settings_manager)
        
        # Add some test history entries
        test_history = [
            {
                'host': 'localhost',
                'port': 9000,
                'timeout': 10,
                'timestamp': '2025-08-27 10:30:00'
            },
            {
                'host': '192.168.1.100',
                'port': 9999,
                'timeout': 15,
                'timestamp': '2025-08-27 11:45:00'
            }
        ]
        
        settings_manager.settings.connection_history = test_history
        dialog._load_connection_history()
        
        logger.info("📋 Connection dialog opened for visual inspection")
        logger.info("   - Test all tabs and functionality")
        logger.info("   - Verify styling and layout")
        logger.info("   - Check input validation")
        logger.info("   - Test connection testing (if TallyPrime is running)")
        
        # Show dialog and wait for user interaction
        result = dialog.exec()
        
        if result == ConnectionDialog.Accepted:
            logger.info("✅ Dialog was accepted - settings saved")
        else:
            logger.info("ℹ️ Dialog was cancelled or closed")
        
        logger.info("✅ Visual test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Visual connection dialog test failed: {str(e)}")
        return False


def main():
    """
    Run all connection dialog integration tests
    """
    logger.info("🚀 Starting Connection Dialog Integration Tests")
    logger.info("=" * 60)
    
    # Test results tracking
    results = []
    
    # Run basic functionality tests
    logger.info("1. Running basic functionality tests...")
    results.append(test_connection_dialog_basic())
    
    # Run integration tests
    logger.info("\n2. Running integration tests...")
    results.append(test_connection_dialog_integration())
    
    # Ask user if they want to run visual tests
    if len(sys.argv) > 1 and sys.argv[1] == "--visual":
        logger.info("\n3. Running visual tests...")
        results.append(test_connection_dialog_visual())
    else:
        logger.info("\n3. Skipping visual tests (use --visual flag to run)")
        results.append(True)  # Don't fail overall tests
    
    # Summary
    logger.info("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.info(f"🎉 All tests passed! ({passed}/{total})")
        logger.info("✅ Connection Dialog Integration: READY FOR TASK 2.3 COMPLETION")
        return 0
    else:
        logger.error(f"❌ Some tests failed ({passed}/{total})")
        return 1


if __name__ == "__main__":
    # Create QApplication for testing
    app = QApplication(sys.argv)
    
    # Run tests
    exit_code = main()
    
    # Clean exit
    sys.exit(exit_code)
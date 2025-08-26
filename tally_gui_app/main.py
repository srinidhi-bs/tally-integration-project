#!/usr/bin/env python3
"""
TallyPrime Integration Manager - Main Application Entry Point
Professional Desktop Application using PySide6/Qt6

This is the main entry point for the TallyPrime Integration Manager.
It initializes the Qt application, sets up the main window, and starts the event loop.

Key Learning Points:
- QApplication: The foundation of any Qt application
- sys.argv: Command line arguments passed to Qt
- Qt Application lifecycle and event loop
- Professional application initialization patterns

Developer: Srinidhi BS (Accountant learning to code)
Assistant: Claude (Anthropic)
Framework: PySide6 (Qt6)
"""

import sys
import logging
from pathlib import Path

# PySide6/Qt6 imports - Core application framework
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QIcon

# Import our application modules
from app.application import TallyIntegrationApp


def setup_application_paths():
    """
    Set up application paths for resources, logs, and configuration.
    This ensures our application can find its resources regardless of 
    where it's executed from.
    
    Learning: Proper path management is crucial for desktop applications
    """
    # Get the directory where this script is located
    app_dir = Path(__file__).parent.absolute()
    
    # Add the application directory to Qt's library paths
    # This helps Qt find our custom resources and plugins
    QDir.addSearchPath("app", str(app_dir))
    QDir.addSearchPath("resources", str(app_dir / "ui" / "resources"))
    
    return app_dir


def setup_basic_logging():
    """
    Set up basic logging for the application startup.
    Later we'll replace this with more sophisticated logging.
    
    Learning: Always set up logging early in application lifecycle
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("TallyPrime Integration Manager starting up...")
    return logger


def main():
    """
    Main function - Entry point for the application.
    
    This function:
    1. Creates the QApplication instance (required for all Qt apps)
    2. Sets up application metadata and properties
    3. Initializes our custom application class
    4. Starts the Qt event loop
    
    Learning Points:
    - QApplication must be created before any other Qt objects
    - sys.exit() ensures proper cleanup when application closes
    - The event loop (app.exec()) is what keeps the application running
    """
    
    # Set up logging first (before creating Qt objects)
    logger = setup_basic_logging()
    
    # Create the Qt Application instance
    # This MUST be created before any other Qt objects
    # sys.argv allows the app to process command line arguments
    app = QApplication(sys.argv)
    
    # Set application metadata - important for professional applications
    # These appear in system dialogs and help with OS integration
    app.setApplicationName("TallyPrime Integration Manager")
    app.setApplicationVersion("1.0.0-dev")
    app.setOrganizationName("Srinidhi BS")
    app.setOrganizationDomain("github.com/srinidhi-bs")
    
    # Set up application paths for resources
    app_dir = setup_application_paths()
    logger.info(f"Application directory: {app_dir}")
    
    # Enable high DPI support for modern displays
    # This ensures the app looks crisp on high-resolution screens
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # Create our custom application instance
        # This contains all the business logic and UI setup
        tally_app = TallyIntegrationApp(app_dir)
        
        # Initialize and show the application
        tally_app.initialize()
        tally_app.show()
        
        logger.info("Application initialized successfully")
        logger.info("Entering Qt event loop...")
        
        # Start the Qt event loop
        # This keeps the application running and responsive to user input
        # The loop continues until the user closes the application
        return app.exec()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1


# This is the standard Python idiom for executable scripts
# It ensures main() only runs when this file is executed directly
# (not when imported as a module)
if __name__ == "__main__":
    # Exit with the return code from main()
    # This allows the operating system to detect if the app started successfully
    sys.exit(main())
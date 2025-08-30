#!/usr/bin/env python3
"""
Minimal Test Script to Diagnose App Startup Issues
Tests each import step by step to identify the problem
"""

import sys
import traceback

def test_step(step_name, test_func):
    """Test a step and report results"""
    try:
        print(f"🔍 Testing {step_name}...")
        result = test_func()
        print(f"✅ {step_name}: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {step_name}: FAILED")
        print(f"   Error: {str(e)}")
        print(f"   Details: {traceback.format_exc()}")
        return False

def test_basic_imports():
    """Test basic Python imports"""
    import sys, os, logging
    from datetime import datetime
    from typing import Optional
    from decimal import Decimal
    return "Basic imports OK"

def test_pyside6_imports():
    """Test PySide6 imports"""
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtCore import Signal, Qt
    from PySide6.QtGui import QAction
    return "PySide6 imports OK"

def test_project_structure():
    """Test project structure"""
    import os
    required_dirs = ['ui', 'core', 'app', 'tests']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            raise Exception(f"Missing directory: {dir_name}")
    
    required_files = [
        'ui/__init__.py',
        'ui/main_window.py',
        'core/__init__.py',
        'app/__init__.py'
    ]
    for file_name in required_files:
        if not os.path.exists(file_name):
            raise Exception(f"Missing file: {file_name}")
    
    return "Project structure OK"

def test_ui_imports():
    """Test UI module imports"""
    from ui.widgets.connection_widget import ConnectionWidget
    from ui.widgets.data_table_widget import ProfessionalDataTableWidget
    from ui.dialogs.connection_dialog import ConnectionDialog
    return "UI imports OK"

def test_core_imports():
    """Test core module imports"""
    from core.tally.connector import TallyConnector
    from core.models.ledger_model import LedgerInfo
    from app.settings import SettingsManager
    return "Core imports OK"

def test_voucher_dialog_import():
    """Test voucher dialog import"""
    from ui.dialogs.voucher_dialog import VoucherEntryDialog
    return "Voucher dialog import OK"

def test_main_window_import():
    """Test main window import"""
    from ui.main_window import MainWindow
    return "Main window import OK"

def test_qapplication_creation():
    """Test QApplication creation"""
    from PySide6.QtWidgets import QApplication
    import sys
    
    # Create QApplication
    app = QApplication(sys.argv)
    app_name = app.applicationName()
    
    # Clean up
    app.quit()
    del app
    
    return f"QApplication created OK (name: {app_name})"

def main():
    """Run all diagnostic tests"""
    print("🧪 TallyPrime Integration Manager - Startup Diagnostics")
    print("=" * 60)
    
    tests = [
        ("Basic Python Imports", test_basic_imports),
        ("PySide6 Imports", test_pyside6_imports),
        ("Project Structure", test_project_structure),
        ("UI Module Imports", test_ui_imports),
        ("Core Module Imports", test_core_imports),
        ("Voucher Dialog Import", test_voucher_dialog_import),
        ("Main Window Import", test_main_window_import),
        ("QApplication Creation", test_qapplication_creation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        if test_step(test_name, test_func):
            passed += 1
        else:
            failed += 1
        print()  # Empty line for readability
    
    print("=" * 60)
    print(f"📊 DIAGNOSTIC RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("The app should be able to start successfully.")
        print("\nTo start the app, run:")
        print("   python main.py")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED!")
        print("Please address the failed tests above before starting the app.")
        print("\nIf you're on Windows and seeing PySide6 import errors:")
        print("   pip install PySide6")
        print("\nIf you're on WSL/Linux, this is expected - run on Windows instead.")
    
    return failed == 0

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Diagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during diagnostics: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
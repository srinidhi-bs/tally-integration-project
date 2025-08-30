#!/usr/bin/env python3
"""
Simplified Test Application
Minimal version to test if the voucher dialog works
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("🔍 Starting simplified test app...")
    
    # Test basic PySide6 import
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
    from PySide6.QtCore import Qt
    print("✅ PySide6 imports successful")
    
    # Test project imports
    from ui.dialogs.voucher_dialog import VoucherEntryDialog
    print("✅ Voucher dialog import successful")
    
    class SimpleTestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("🧪 Voucher Dialog Test")
            self.setGeometry(100, 100, 400, 200)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout
            layout = QVBoxLayout(central_widget)
            
            # Test button
            test_btn = QPushButton("🚀 Test Voucher Dialog")
            test_btn.clicked.connect(self.test_voucher_dialog)
            layout.addWidget(test_btn)
            
            # Mock objects for testing
            self.mock_connector = None
            self.mock_data_reader = None
            
        def test_voucher_dialog(self):
            """Test opening the voucher dialog"""
            try:
                dialog = VoucherEntryDialog(
                    connector=self.mock_connector,
                    data_reader=self.mock_data_reader,
                    parent=self
                )
                
                result = dialog.exec()
                
                if result == dialog.Accepted:
                    QMessageBox.information(self, "Success", "Voucher dialog worked correctly!")
                else:
                    QMessageBox.information(self, "Info", "Voucher dialog was cancelled")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open voucher dialog:\n{str(e)}")
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
    
    # Create and run app
    app = QApplication(sys.argv)
    window = SimpleTestWindow()
    window.show()
    
    print("✅ Test application started successfully!")
    print("Click the 'Test Voucher Dialog' button to test the voucher functionality.")
    
    sys.exit(app.exec())
    
except ImportError as e:
    print(f"❌ Import Error: {str(e)}")
    print("\nIf you're seeing PySide6 import errors:")
    print("1. Make sure you're running on Windows (not WSL)")
    print("2. Install PySide6: pip install PySide6")
    print("3. Make sure you're in the right directory: cd C:\\Development\\tally-integration-project\\tally_gui_app")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Unexpected Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
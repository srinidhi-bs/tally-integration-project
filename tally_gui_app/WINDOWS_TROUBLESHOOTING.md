# Windows Startup Troubleshooting Guide
## TallyPrime Integration Manager

### Quick Fix Commands

**Option 1: Complete Fresh Setup**
```cmd
cd C:\Development\tally-integration-project\tally_gui_app
pip install --upgrade pip
pip install PySide6 requests
python test_startup.py
```

**Option 2: If PySide6 Issues**
```cmd
pip uninstall PySide6
pip install PySide6==6.5.2
python test_startup.py
```

**Option 3: If Import Issues**
```cmd
cd C:\Development\tally-integration-project\tally_gui_app
set PYTHONPATH=%CD%
python main.py
```

### Diagnostic Steps

1. **Run Full Diagnostics**
   ```cmd
   python test_startup.py
   ```

2. **Test Minimal App**
   ```cmd
   python simple_test_app.py
   ```

3. **Test Main App**
   ```cmd
   python main.py
   ```

### Common Solutions

#### Problem: ModuleNotFoundError
```cmd
# Solution: Install missing packages
pip install PySide6 requests
```

#### Problem: Import circular dependency
```cmd
# Solution: Test without voucher dialog first
# Edit main_window.py temporarily to comment out voucher imports
```

#### Problem: Path issues
```cmd
# Solution: Set Python path
set PYTHONPATH=%CD%
python main.py
```

#### Problem: Version conflicts
```cmd
# Solution: Use virtual environment
python -m venv venv
venv\Scripts\activate
pip install PySide6 requests
python main.py
```

### Success Indicators

When working correctly, you should see:
- ✅ All diagnostic tests pass
- Application window opens with professional interface
- Left Control Panel shows "Data Entry" section  
- Menu shows Tools → New Voucher option
- Voucher dialog opens with 4 professional tabs

### Support Commands

If still having issues:
```cmd
# Get detailed Python info
python --version
pip list | findstr PySide6
python -c "import PySide6; print(PySide6.__version__)"

# Test minimal Qt
python -c "from PySide6.QtWidgets import QApplication; print('Qt works')"
```
# TallyPrime HTTP-XML Gateway Integration

A Python project for integrating with TallyPrime using HTTP-XML Gateway to post vouchers directly without manual import files.

## Project Overview

This project enables direct posting of sales and purchase vouchers to TallyPrime from Python applications, eliminating the need for manual Excel file imports and providing real-time validation.

## Project Structure

```
tally-integration-project/
├── src/                    # Source code
│   ├── post_tally_voucher.py       # Main voucher posting script
│   ├── tally_connection_test.py    # Connection testing utility
│   └── simple_tally_test.py        # Basic connection test
├── docs/                   # Documentation
│   └── HTTP_XML_GATEWAY_LEARNINGS.md  # Complete implementation guide
├── examples/               # Example files
│   └── generated_voucher.xml       # Sample generated voucher XML
├── reference/              # Reference materials
│   └── Purchase_1.xml              # Real Tally XML export for reference
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

## Features

- ✅ Direct TallyPrime integration via HTTP-XML Gateway
- ✅ Sales and Purchase voucher posting
- ✅ Automatic GST calculation (CGST, SGST, IGST)
- ✅ Perfect double-entry balance validation
- ✅ Round-off handling
- ✅ Real-time error feedback from TallyPrime
- ✅ WSL to Windows connectivity support

## Prerequisites

### TallyPrime Setup
1. TallyPrime must be running
2. HTTP-XML Gateway must be enabled:
   - Press **F1** (Help) → **Settings** → **Connectivity**
   - Set **"TallyPrime acts as"** → **"Both"**
   - Set **"Enable ODBC"** → **"Yes"**
   - Set **"Port"** → **9000**

### Required Ledgers in TallyPrime
- Customer ledgers (Sundry Debtors)
- Supplier ledgers (Sundry Creditors)
- Sales accounts
- Purchase accounts (e.g., "18% Local Purchases")
- GST accounts: "CGST Output", "SGST Output", "CGST Input", "SGST Input"
- "Round Off" account

## Installation

1. Clone or download this project
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Connection Testing
```bash
# Basic connection test
python src/simple_tally_test.py

# Comprehensive connection test
python src/tally_connection_test.py
```

### Posting Vouchers
```bash
# Post sample voucher (edit the script to customize)
python src/post_tally_voucher.py
```

## Configuration

For WSL users, update the Tally host IP in scripts:
```python
# Find Windows host IP
ip route | grep default
# Use the IP (typically 172.28.208.1) in scripts
```

## Sample Voucher Structure

### Purchase Voucher (RK Electricals Example)
- **Supplier:** RK Electricals - ₹484 (Credit)
- **Purchase Account:** 18% Local Purchases - ₹410 (Debit)
- **CGST Input:** ₹36.90 (Debit)
- **SGST Input:** ₹36.90 (Debit)
- **Round Off:** ₹0.20 (Debit)

## Success Response
```xml
<RESPONSE>
 <CREATED>1</CREATED>
 <ERRORS>0</ERRORS>
 <LASTVCHID>4326</LASTVCHID>
</RESPONSE>
```

## Documentation

See `docs/HTTP_XML_GATEWAY_LEARNINGS.md` for complete implementation details, troubleshooting, and lessons learned.

## Author

**Srinidhi BS** - Accountant learning to code  
**Email:** mailsrinidhibs@gmail.com  
**GitHub:** https://github.com/srinidhi-bs  

## Version History

- **v1.0** - Initial implementation with sales voucher support
- **v2.0** - Added purchase voucher support with corrected debit/credit structure
- **v2.1** - Project organization and documentation

---

*This project serves as both functional code and educational material for TallyPrime integration.*
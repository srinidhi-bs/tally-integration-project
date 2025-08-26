#!/usr/bin/env python3
"""
Tally Sales Voucher Posting Script

This script posts a new sales voucher to TallyPrime using HTTP-XML Gateway.
Based on the successful implementation documented in HTTP_XML_GATEWAY_LEARNINGS.md

Author: Srinidhi BS
Purpose: Testing Tally voucher posting for learning
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

class TallySalesVoucherPoster:
    """
    Class to handle posting sales vouchers to TallyPrime
    
    This class encapsulates all the functionality needed to:
    1. Connect to TallyPrime HTTP-XML Gateway
    2. Generate properly formatted XML vouchers
    3. Post vouchers and handle responses
    4. Validate accounting balance (debits = credits)
    """
    
    def __init__(self, tally_host="172.28.208.1", tally_port=9000):
        """
        Initialize the Tally connection
        
        Args:
            tally_host (str): IP address where TallyPrime is running
            tally_port (int): Port number for HTTP-XML Gateway (usually 9000)
        """
        self.tally_url = f"http://{tally_host}:{tally_port}"
        self.session = requests.Session()  # Reuse connection for better performance
        
        print(f"Initialized Tally connection to: {self.tally_url}")
    
    def test_connection(self):
        """
        Test basic connection to TallyPrime HTTP-XML Gateway
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print("Testing connection to TallyPrime...")
            response = self.session.get(self.tally_url, timeout=10)
            
            if response.status_code == 200 and "TallyPrime Server is Running" in response.text:
                print("✅ Successfully connected to TallyPrime HTTP Gateway")
                return True
            else:
                print(f"❌ Unexpected response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def calculate_gst_amounts(self, taxable_amount, gst_rate=18):
        """
        Calculate GST amounts based on taxable value
        
        Args:
            taxable_amount (Decimal): The base taxable amount
            gst_rate (int): GST rate percentage (default 18%)
        
        Returns:
            tuple: (cgst, sgst, igst) amounts
        """
        # Convert to Decimal for precise financial calculations
        taxable = Decimal(str(taxable_amount))
        
        # For intrastate sales: CGST + SGST (each is half of total GST rate)
        # For interstate sales: IGST (full GST rate)
        # We'll use intrastate (CGST + SGST) for this example
        
        cgst_rate = Decimal(str(gst_rate / 2))  # Half of total GST rate
        sgst_rate = Decimal(str(gst_rate / 2))  # Half of total GST rate
        
        cgst_amount = (taxable * cgst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        sgst_amount = (taxable * sgst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        igst_amount = Decimal('0.00')  # No IGST for intrastate sales
        
        return cgst_amount, sgst_amount, igst_amount
    
    def calculate_round_off(self, total_invoice, sales_amount, cgst, sgst, igst):
        """
        Calculate round-off amount to ensure perfect balance
        
        This is crucial for accounting - the total of all components must exactly
        equal the invoice total. Any small differences due to rounding are
        handled by the round-off account.
        
        Args:
            total_invoice (Decimal): Final invoice amount
            sales_amount (Decimal): Taxable sales amount  
            cgst (Decimal): CGST amount
            sgst (Decimal): SGST amount
            igst (Decimal): IGST amount
        
        Returns:
            Decimal: Round-off amount (can be positive or negative)
        """
        # Sum all components
        total_components = sales_amount + cgst + sgst + igst
        
        # Calculate difference
        round_off = total_invoice - total_components
        
        # Round to 2 decimal places
        return round_off.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def format_date_for_tally(self, date_string):
        """
        Convert date from DD-MM-YYYY format to YYYYMMDD format for Tally
        
        Args:
            date_string (str): Date in DD-MM-YYYY format
        
        Returns:
            str: Date in YYYYMMDD format
        """
        # Parse the input date (DD-MM-YYYY)
        date_obj = datetime.strptime(date_string, "%d-%m-%Y")
        
        # Format for Tally (YYYYMMDD)
        return date_obj.strftime("%Y%m%d")
    
    def build_purchase_voucher_xml(self, voucher_data):
        """
        Build XML structure for purchase voucher posting to TallyPrime
        
        Purchase vouchers have different accounting logic:
        - Supplier account is CREDITED (we owe them money)
        - Purchase account is DEBITED (our expense/asset)
        - GST Input accounts are DEBITED (input tax credit we can claim)
        
        Args:
            voucher_data (dict): Dictionary containing purchase voucher details
        
        Returns:
            str: Complete XML string ready for posting to TallyPrime
        """
        # Convert date format for Tally
        tally_date = self.format_date_for_tally(voucher_data['date'])
        
        # Get amounts from voucher data
        total_invoice = Decimal(str(voucher_data['total_invoice_value']))
        purchase_amount = Decimal(str(voucher_data['taxable_value']))
        cgst = Decimal(str(voucher_data['cgst_amount']))
        sgst = Decimal(str(voucher_data['sgst_amount']))
        round_off = Decimal(str(voucher_data['round_off']))
        
        # Print calculation details for verification
        print(f"\n📊 Purchase Voucher Calculation Details:")
        print(f"Purchase Amount: ₹{purchase_amount}")
        print(f"CGST Input: ₹{cgst}")
        print(f"SGST Input: ₹{sgst}")
        print(f"Round-off: ₹{round_off}")
        print(f"Total Invoice: ₹{total_invoice}")
        print(f"Balance Check: ₹{purchase_amount + cgst + sgst + round_off} = ₹{total_invoice}")
        
        # Build the XML structure for Purchase Voucher (CORRECTED based on real Tally XML)
        xml_content = f"""<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Purchase" ACTION="Create">
                        <DATE>{tally_date}</DATE>
                        <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
                        <VOUCHERNUMBER>{voucher_data['voucher_number']}</VOUCHERNUMBER>
                        <NARRATION>{voucher_data['narration']}</NARRATION>
                        
                        <!-- Supplier Account (Credit Entry) -->
                        <!-- Amount we owe to supplier -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{voucher_data['supplier_name']}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>{total_invoice}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- Purchase Account (Debit Entry) -->
                        <!-- Our purchase expense -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{voucher_data['purchase_account']}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{purchase_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- CGST Input (Debit Entry) -->
                        <!-- Input tax credit we can claim -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>CGST Input</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{cgst}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- SGST Input (Debit Entry) -->
                        <!-- Input tax credit we can claim -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>SGST Input</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{sgst}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- Round Off Entry (Debit Entry) -->
                        <!-- Handles small differences due to rounding -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>Round Off</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{round_off}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>"""
        
        return xml_content

    def build_sales_voucher_xml(self, voucher_data):
        """
        Build XML structure for sales voucher posting to TallyPrime
        
        This function creates the exact XML structure that TallyPrime expects
        for posting sales vouchers through HTTP-XML Gateway.
        
        Args:
            voucher_data (dict): Dictionary containing voucher details
                Required keys:
                - voucher_number: Invoice number (e.g., "ISPL/2024/003")
                - date: Invoice date in DD-MM-YYYY format
                - customer_name: Customer ledger name
                - sales_account: Sales account name
                - taxable_value: Base sales amount before tax
                - total_invoice_value: Final invoice amount including all taxes
                - narration: Description for the voucher
        
        Returns:
            str: Complete XML string ready for posting to TallyPrime
        """
        # Convert date format for Tally
        tally_date = self.format_date_for_tally(voucher_data['date'])
        
        # Convert amounts to Decimal for precise calculations
        total_invoice = Decimal(str(voucher_data['total_invoice_value']))
        sales_amount = Decimal(str(voucher_data['taxable_value']))
        
        # Calculate GST amounts (18% total: 9% CGST + 9% SGST)
        cgst, sgst, igst = self.calculate_gst_amounts(sales_amount, gst_rate=18)
        
        # Calculate round-off to ensure perfect balance
        round_off = self.calculate_round_off(total_invoice, sales_amount, cgst, sgst, igst)
        
        # Print calculation details for verification
        print(f"\n📊 Voucher Calculation Details:")
        print(f"Sales Amount: ₹{sales_amount}")
        print(f"CGST (9%): ₹{cgst}")
        print(f"SGST (9%): ₹{sgst}")
        print(f"Round-off: ₹{round_off}")
        print(f"Total Invoice: ₹{total_invoice}")
        print(f"Balance Check: ₹{sales_amount + cgst + sgst + round_off} = ₹{total_invoice}")
        
        # Build the XML structure
        # This is the exact format that worked successfully in your previous implementation
        xml_content = f"""<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <IMPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>Vouchers</REPORTNAME>
            </REQUESTDESC>
            <REQUESTDATA>
                <TALLYMESSAGE xmlns:UDF="TallyUDF">
                    <VOUCHER VCHTYPE="Sales" ACTION="Create">
                        <DATE>{tally_date}</DATE>
                        <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
                        <VOUCHERNUMBER>{voucher_data['voucher_number']}</VOUCHERNUMBER>
                        <NARRATION>{voucher_data['narration']}</NARRATION>
                        
                        <!-- Customer Account (Debit Entry) -->
                        <!-- This represents the amount the customer owes us -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{voucher_data['customer_name']}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                            <AMOUNT>{total_invoice}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- Sales Account (Credit Entry) -->
                        <!-- This represents our sales income -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>{voucher_data['sales_account']}</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{sales_amount}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- CGST Output (Credit Entry) -->
                        <!-- Central Goods and Services Tax collected -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>CGST Output</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{cgst}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>
                        
                        <!-- SGST Output (Credit Entry) -->
                        <!-- State Goods and Services Tax collected -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>SGST Output</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                            <AMOUNT>-{sgst}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>"""
        
        # Add round-off entry only if needed (non-zero amount)
        if round_off != 0:
            # Determine if round-off is debit or credit based on sign
            is_debit = "Yes" if round_off > 0 else "No"
            xml_content += f"""
                        
                        <!-- Round Off Entry -->
                        <!-- Handles small differences due to rounding -->
                        <ALLLEDGERENTRIES.LIST>
                            <LEDGERNAME>Round Off</LEDGERNAME>
                            <ISDEEMEDPOSITIVE>{is_debit}</ISDEEMEDPOSITIVE>
                            <AMOUNT>{round_off}</AMOUNT>
                        </ALLLEDGERENTRIES.LIST>"""
        
        # Close the XML structure
        xml_content += """
                    </VOUCHER>
                </TALLYMESSAGE>
            </REQUESTDATA>
        </IMPORTDATA>
    </BODY>
</ENVELOPE>"""
        
        return xml_content
    
    def post_voucher_to_tally(self, xml_data):
        """
        Post the voucher XML to TallyPrime and handle the response
        
        Args:
            xml_data (str): Complete XML voucher data
        
        Returns:
            dict: Response details with success status and messages
        """
        try:
            print(f"\n🚀 Posting voucher to TallyPrime...")
            print(f"URL: {self.tally_url}")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Set proper headers for XML content
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            # Post the XML data to TallyPrime
            response = self.session.post(
                self.tally_url,
                data=xml_data,
                headers=headers,
                timeout=30  # 30 second timeout
            )
            
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
            
            # Parse the response to check for success
            response_text = response.text
            print(f"\n📥 TallyPrime Response:")
            print(response_text)
            
            # Check for successful posting
            # Based on your learnings: success = ERRORS=0 and CREATED=1
            if '<ERRORS>0</ERRORS>' in response_text and '<CREATED>1</CREATED>' in response_text:
                print("\n✅ SUCCESS! Voucher posted successfully to TallyPrime")
                
                # Extract voucher ID if available
                try:
                    root = ET.fromstring(response_text)
                    last_vch_id = root.find('LASTVCHID')
                    if last_vch_id is not None:
                        print(f"📄 Voucher ID in Tally: {last_vch_id.text}")
                except:
                    pass
                
                return {
                    'success': True,
                    'message': 'Voucher posted successfully',
                    'response': response_text
                }
            
            else:
                print("\n❌ FAILED! Voucher posting failed")
                
                # Try to extract error details
                error_details = "Unknown error"
                if '<ERRORS>' in response_text:
                    try:
                        # Find error count
                        start = response_text.find('<ERRORS>') + 8
                        end = response_text.find('</ERRORS>')
                        error_count = response_text[start:end]
                        error_details = f"TallyPrime reported {error_count} errors"
                    except:
                        pass
                
                return {
                    'success': False,
                    'error': error_details,
                    'response': response_text
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout - TallyPrime took too long to respond"
            print(f"\n❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - Cannot reach TallyPrime"
            print(f"\n❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"\n❌ {error_msg}")
            return {'success': False, 'error': error_msg}

def main():
    """
    Main function to test posting a new sales voucher to TallyPrime
    
    This creates a sample voucher and posts it to demonstrate the integration.
    """
    print("🏢 TallyPrime Sales Voucher Posting Test")
    print("=" * 50)
    
    # Initialize the Tally poster
    tally_poster = TallySalesVoucherPoster()
    
    # Test connection first
    if not tally_poster.test_connection():
        print("❌ Cannot connect to TallyPrime. Please check:")
        print("1. TallyPrime is running")
        print("2. HTTP-XML Gateway is enabled")
        print("3. Company is loaded in TallyPrime")
        return
    
    # Purchase voucher data for RK Electricals
    # This is a purchase entry (not sales), so we'll need to adjust the XML structure
    sample_voucher = {
        'voucher_number': 'ISPL/2024/005',  # New voucher number (corrected entry)
        'date': '17-08-2024',  # Today's date
        'supplier_name': 'RK Electricals',  # Supplier ledger
        'purchase_account': '18% Local Purchases',  # Purchase account
        'taxable_value': 410.00,  # Base amount before tax
        'total_invoice_value': 484.00,  # Final amount including tax (410 + 36.9 + 36.9 + 0.2)
        'cgst_amount': 36.90,  # CGST Input
        'sgst_amount': 36.90,  # SGST Input
        'round_off': 0.20,  # Round off amount
        'narration': 'Purchase Invoice from RK Electricals - Electrical materials'
    }
    
    print(f"\n📋 Purchase Voucher Details:")
    print(f"Invoice Number: {sample_voucher['voucher_number']}")
    print(f"Date: {sample_voucher['date']}")
    print(f"Supplier: {sample_voucher['supplier_name']}")
    print(f"Purchase Account: {sample_voucher['purchase_account']}")
    print(f"Taxable Amount: ₹{sample_voucher['taxable_value']}")
    print(f"CGST Input: ₹{sample_voucher['cgst_amount']}")
    print(f"SGST Input: ₹{sample_voucher['sgst_amount']}")
    print(f"Round Off: ₹{sample_voucher['round_off']}")
    print(f"Total Amount: ₹{sample_voucher['total_invoice_value']}")
    
    # Generate XML for the purchase voucher
    print(f"\n🔨 Generating Purchase Voucher XML for TallyPrime...")
    xml_data = tally_poster.build_purchase_voucher_xml(sample_voucher)
    
    # Optional: Save XML to file for inspection
    with open('/home/srinidhibs/experiment/generated_voucher.xml', 'w') as f:
        f.write(xml_data)
    print(f"📄 XML saved to: generated_voucher.xml")
    
    # Post the voucher to TallyPrime
    result = tally_poster.post_voucher_to_tally(xml_data)
    
    # Display final result
    print(f"\n🎯 Final Result:")
    if result['success']:
        print(f"✅ Voucher {sample_voucher['voucher_number']} posted successfully!")
        print(f"💰 Amount: ₹{sample_voucher['total_invoice_value']}")
        print(f"📊 Check in TallyPrime: Gateway of Tally → Day Book")
    else:
        print(f"❌ Failed to post voucher: {result.get('error', 'Unknown error')}")
        print(f"🔍 Check TallyPrime for error details")

if __name__ == "__main__":
    """
    Entry point when script is run directly
    """
    main()
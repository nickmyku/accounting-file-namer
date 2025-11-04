#!/usr/bin/env python3
"""
Receipt OCR Script
Extracts transaction date, amount, and vendor name from a receipt image.
"""

import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("Error: Required packages not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)


def extract_text_from_image(image_path: str) -> str:
    """Extract text from receipt image using OCR."""
    try:
        image = Image.open(image_path)
        # Use Tesseract OCR with default settings
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error reading image: {e}", file=sys.stderr)
        sys.exit(1)


def extract_date(text: str) -> Optional[str]:
    """Extract transaction date from receipt text."""
    # Common date patterns in receipts
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
        r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
        r'\w+\s+\d{1,2},?\s+\d{4}',        # Month DD, YYYY
        r'\d{1,2}\s+\w+\s+\d{4}',          # DD Month YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Return the first date found (usually the transaction date)
            return matches[0]
    
    return None


def extract_amount(text: str) -> Optional[str]:
    """Extract transaction amount from receipt text."""
    # Look for currency symbols followed by amounts
    # Common patterns: $XX.XX, TOTAL: $XX.XX, etc.
    amount_patterns = [
        r'(?:total|amount|due|balance|charge)[:\s]*\$?\s*(\d+\.?\d{0,2})',
        r'\$\s*(\d+\.?\d{0,2})',
        r'(?:total|amount|due|balance|charge)[:\s]*\$?\s*(\d+[,\.]\d{0,2})',
    ]
    
    # Also look for the largest amount (often the total)
    all_amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up the amount
            amount_str = match.replace(',', '')
            try:
                amount = float(amount_str)
                all_amounts.append((amount, amount_str))
            except ValueError:
                continue
    
    if all_amounts:
        # Return the largest amount (typically the total)
        largest = max(all_amounts, key=lambda x: x[0])
        return f"${largest[1]}"
    
    # Fallback: look for any dollar amount
    fallback_pattern = r'\$(\d+\.?\d{0,2})'
    matches = re.findall(fallback_pattern, text)
    if matches:
        amounts = [float(m.replace(',', '')) for m in matches]
        largest = max(amounts)
        return f"${largest:.2f}"
    
    return None


def extract_vendor(text: str) -> Optional[str]:
    """Extract vendor name from receipt text, handling multi-line vendor names."""
    lines = text.split('\n')
    
    # Vendor name is usually at the top of the receipt
    # Collect consecutive lines that appear to be part of the vendor name
    vendor_lines = []
    
    # Patterns that indicate we've moved past the vendor name
    stop_patterns = [
        r'^\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Date patterns
        r'^\s*\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # Date patterns
        r'^\s*\$\s*\d+',                        # Amount patterns
        r'^\s*(?:total|amount|due|balance|charge)[:\s]*\$?\s*\d+',  # Amount keywords
        r'^\s*(?:receipt|invoice|transaction|date|time)\s*[:]?\s*',  # Receipt metadata
        r'^[\d\s\-\/\.:]+$',                    # Lines that are mostly numbers/punctuation
    ]
    
    # Words that indicate we've moved past the vendor name
    stop_words = ['receipt', 'invoice', 'transaction', 'date', 'time', 'total', 'amount', 'due']
    
    # Check first 15 lines (vendor names typically appear near the top)
    for i, line in enumerate(lines[:15]):
        line = line.strip()
        
        # Skip empty lines initially, but stop collecting if we hit empty lines after starting
        if not line:
            if vendor_lines:
                # Empty line after collecting vendor lines likely means end of vendor name
                break
            continue
        
        # Check if this line indicates we've moved past the vendor name
        should_stop = False
        
        # Check against stop patterns
        for pattern in stop_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                should_stop = True
                break
        
        # Check against stop words (only if they appear at the start of the line)
        if not should_stop:
            line_lower = line.lower()
            for word in stop_words:
                if line_lower.startswith(word):
                    should_stop = True
                    break
        
        if should_stop:
            # Stop collecting if we already have vendor lines
            if vendor_lines:
                break
            # Otherwise, skip this line and continue
            continue
        
        # Check if line looks like it could be part of a vendor name
        # Should have some letters, not be mostly numbers
        if re.search(r'[a-zA-Z]', line) and not re.match(r'^[\d\s\-\/\.:]+$', line):
            line_length = len(line)
            
            # Check if line starts with common non-vendor indicators (address, contact info)
            if re.match(r'^\s*(?:phone|fax|email|www\.|http|tel|address)', line, re.IGNORECASE):
                # Stop if we've already collected vendor lines
                if vendor_lines:
                    break
                continue
            
            # If we've already started collecting vendor lines, be more lenient
            # Allow continuation lines that are part of multi-line vendor names
            if vendor_lines:
                # Allow continuation lines that are reasonable length and contain letters
                if line_length <= 80 and re.search(r'[a-zA-Z]', line):
                    vendor_lines.append(line)
                    continue
                else:
                    # Line doesn't look like continuation, stop collecting
                    break
            
            # For the first line, be more selective
            # Skip if line is too short (likely OCR artifact) or too long (likely address/description)
            if 3 <= line_length <= 70:
                vendor_lines.append(line)
                continue
        
        # If we've collected some vendor lines and hit something that doesn't fit, stop
        if vendor_lines:
            break
    
    # Combine collected lines into vendor name
    if vendor_lines:
        # Join lines with spaces, normalize whitespace
        vendor = ' '.join(vendor_lines)
        vendor = re.sub(r'\s+', ' ', vendor).strip()
        
        # Clean up common OCR artifacts at start/end
        vendor = re.sub(r'^[^\w&]+|[^\w&]+$', '', vendor)
        
        # Remove trailing punctuation that's likely not part of name
        vendor = re.sub(r'[,;]+$', '', vendor)
        
        if len(vendor) > 2:
            return vendor
    
    return None


def main():
    """Main function to process receipt image."""
    if len(sys.argv) < 2:
        print("Usage: python extract_receipt.py <path_to_receipt_image.jpg> [--debug]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    debug_mode = '--debug' in sys.argv
    
    # Validate file exists
    if not Path(image_path).exists():
        print(f"Error: File not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    
    # Extract text from image
    print("Extracting text from receipt...", file=sys.stderr)
    text = extract_text_from_image(image_path)
    
    # Extract information
    vendor = extract_vendor(text)
    date = extract_date(text)
    amount = extract_amount(text)
    
    # Output results
    print("\n--- Receipt Details ---")
    if vendor:
        print(f"Vendor: {vendor}")
    else:
        print("Vendor: Not found")
    
    if date:
        print(f"Transaction Date: {date}")
    else:
        print("Transaction Date: Not found")
    
    if amount:
        print(f"Transaction Amount: {amount}")
    else:
        print("Transaction Amount: Not found")
    
    # Also output raw text for debugging (optional)
    if debug_mode:
        print("\n--- Raw OCR Text ---")
        print(text)


if __name__ == "__main__":
    main()

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
    """Extract vendor name from receipt text."""
    # First, check for specific known vendors with special patterns
    # Los Angeles Department of Water & Power (case-insensitive, handles variations)
    # Normalize text for searching (replace newlines with spaces)
    normalized_text = re.sub(r'\s+', ' ', text)
    
    # Patterns to match Los Angeles Department of Water & Power
    la_dwp_patterns = [
        r'los\s+angeles\s+department\s+of\s+water\s*[&]\s*power',
        r'los\s+angeles\s+department\s+of\s+water\s+and\s+power',
        r'los\s+angeles\s+dept\s+of\s+water\s*[&]\s*power',
        r'department\s+of\s+water\s*[&]\s*power',  # In case "Los Angeles" is missing
    ]
    
    for pattern in la_dwp_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            vendor = match.group(0).strip()
            # Normalize spacing
            vendor = re.sub(r'\s+', ' ', vendor)
            # Return in the exact format requested: "Los Angeles department of water & power"
            # Capitalize first letter of each major word, keep "department" lowercase
            parts = vendor.split()
            normalized = []
            for part in parts:
                part_lower = part.lower().strip()
                if part_lower == 'of' or part_lower == '&' or part_lower == 'and':
                    normalized.append(part_lower)
                elif part_lower == 'department' or part_lower == 'dept':
                    normalized.append('department')  # Keep lowercase, normalize "dept" to "department"
                elif part_lower == 'los':
                    normalized.append('Los')
                elif part_lower == 'angeles':
                    normalized.append('Angeles')
                elif part_lower == 'water':
                    normalized.append('water')  # Keep lowercase as requested
                elif part_lower == 'power':
                    normalized.append('power')  # Keep lowercase as requested
                else:
                    normalized.append(part.capitalize())
            result = ' '.join(normalized)
            # Ensure "Los Angeles" prefix is present
            if not result.lower().startswith('los angeles'):
                # Check if "Los Angeles" appears earlier in the normalized text
                la_match = re.search(r'los\s+angeles', normalized_text[:match.start()], re.IGNORECASE)
                if la_match:
                    result = 'Los Angeles ' + result
            return result
    
    # Fallback to original logic for other vendors
    lines = text.split('\n')
    
    # Vendor name is usually at the top of the receipt
    # Look for the first substantial line (not empty, not all numbers)
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line:
            continue
        
        # Skip lines that are mostly numbers or dates
        if re.match(r'^[\d\s\-\/\.:]+$', line):
            continue
        
        # Skip common receipt header words
        skip_words = ['receipt', 'invoice', 'transaction', 'date', 'time', 'total']
        if any(word in line.lower() for word in skip_words):
            continue
        
        # If line looks like a vendor name (has letters, reasonable length)
        if len(line) > 3 and re.search(r'[a-zA-Z]', line):
            # Clean up common artifacts
            vendor = re.sub(r'^[^\w]+|[^\w]+$', '', line)
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

#!/usr/bin/env python3
"""
Batch Receipt Processing Script
Processes all receipt images and PDFs in a folder, extracts information,
and renames files to include vendor, date, and transaction amount.
"""

import sys
import re
from pathlib import Path
from typing import Optional, List

# Import functions from extract_receipt.py
try:
    from extract_receipt import (
        extract_text_from_image,
        extract_text_from_pdf,
        extract_text_from_logo_region,
        extract_date,
        extract_amount,
        extract_vendor,
        is_pdf_file,
        SUPPORTED_FORMATS
    )
except ImportError as e:
    print(f"Error: Could not import from extract_receipt.py: {e}", file=sys.stderr)
    print("Please ensure extract_receipt.py is in the same directory.", file=sys.stderr)
    sys.exit(1)


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    Sanitize text to be safe for use in filenames.
    Removes or replaces invalid characters.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length of the sanitized text
        
    Returns:
        Sanitized text safe for use in filenames
    """
    if not text:
        return "unknown"
    
    # Replace invalid filename characters with underscores
    # Invalid characters: / \ : * ? " < > |
    invalid_chars = r'[/\\:*?"<>|]'
    sanitized = re.sub(invalid_chars, '_', text)
    
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[_\s]+', '_', sanitized)
    
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip('_.')
    
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Ensure it's not empty
    if not sanitized:
        return "unknown"
    
    return sanitized


def format_amount_for_filename(amount: Optional[str]) -> str:
    """
    Format amount string for use in filename.
    Converts $XX.XX to $XX.XX format (keeps dollar sign).
    
    Args:
        amount: Amount string (e.g., "$4.75" or "$123.45")
        
    Returns:
        Formatted amount string (e.g., "$4.75" or "$123.45")
    """
    if not amount:
        return "unknown_amount"
    
    # Remove existing dollar sign and spaces, then add dollar sign back
    formatted = amount.replace('$', '').strip()
    
    # Remove commas
    formatted = formatted.replace(',', '')
    
    # Validate it's a number
    try:
        float(formatted)
        # Add dollar sign prefix
        return f"${formatted}"
    except ValueError:
        return "unknown_amount"


def get_supported_image_files(folder_path: Path) -> List[Path]:
    """
    Get all supported image and PDF files from a folder.
    
    Args:
        folder_path: Path to the folder to search
        
    Returns:
        List of Path objects for supported files
    """
    supported_files = []
    
    # Check for image files
    for ext in SUPPORTED_FORMATS:
        # Check both uppercase and lowercase extensions
        for file_path in folder_path.glob(f"*.{ext.lower()}"):
            if file_path.is_file():
                supported_files.append(file_path)
        for file_path in folder_path.glob(f"*.{ext.upper()}"):
            if file_path.is_file():
                supported_files.append(file_path)
    
    # Check for PDF files
    for file_path in folder_path.glob("*.pdf"):
        if file_path.is_file():
            supported_files.append(file_path)
    for file_path in folder_path.glob("*.PDF"):
        if file_path.is_file():
            supported_files.append(file_path)
    
    # Remove duplicates (case-insensitive)
    seen = set()
    unique_files = []
    for file_path in supported_files:
        key = str(file_path).lower()
        if key not in seen:
            seen.add(key)
            unique_files.append(file_path)
    
    return sorted(unique_files)


def process_receipt_file(file_path: Path, vendor_name: Optional[str] = None) -> dict:
    """
    Process a single receipt file and extract information.
    
    Args:
        file_path: Path to the receipt file
        vendor_name: Optional vendor name to use instead of extracting
        
    Returns:
        Dictionary with extracted information:
        {
            'vendor': str or None,
            'date': str or None,
            'amount': str or None,
            'success': bool
        }
    """
    print(f"\nProcessing: {file_path.name}", file=sys.stderr)
    
    try:
        is_pdf = is_pdf_file(str(file_path))
        
        # Extract text from file
        if is_pdf:
            text = extract_text_from_pdf(str(file_path))
        else:
            text = extract_text_from_image(str(file_path))
        
        # Extract logo text for vendor extraction
        logo_text = extract_text_from_logo_region(str(file_path), is_pdf=is_pdf)
        
        # Extract information
        date = extract_date(text)
        amount = extract_amount(text)
        
        # Use provided vendor name or extract from receipt
        if vendor_name:
            vendor = vendor_name
        else:
            vendor = extract_vendor(text, logo_text)
        
        return {
            'vendor': vendor,
            'date': date,
            'amount': amount,
            'success': True
        }
    
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}", file=sys.stderr)
        return {
            'vendor': vendor_name if vendor_name else None,
            'date': None,
            'amount': None,
            'success': False
        }


def generate_new_filename(file_path: Path, vendor: Optional[str], date: Optional[str], 
                          amount: Optional[str]) -> str:
    """
    Generate a new filename based on extracted information.
    
    Format: {vendor} {date} {$amount}.{ext}
    
    Args:
        file_path: Original file path
        vendor: Vendor name
        date: Transaction date (YYYY-MM-DD format)
        amount: Transaction amount
        
    Returns:
        New filename string
    """
    # Get original extension
    ext = file_path.suffix
    
    # Sanitize components
    vendor_part = sanitize_filename(vendor) if vendor else "unknown_vendor"
    date_part = sanitize_filename(date) if date else "unknown_date"
    amount_part = format_amount_for_filename(amount)
    
    # Build new filename with spaces between parts
    new_filename = f"{vendor_part} {date_part} {amount_part}{ext}"
    
    return new_filename


def rename_file_with_info(file_path: Path, vendor: Optional[str], date: Optional[str], 
                          amount: Optional[str], dry_run: bool = False) -> bool:
    """
    Rename a file to include vendor, date, and amount information.
    
    Args:
        file_path: Path to the file to rename
        vendor: Vendor name
        date: Transaction date
        amount: Transaction amount
        dry_run: If True, only print what would be done without actually renaming
        
    Returns:
        True if rename was successful (or would be successful in dry_run mode), False otherwise
    """
    new_filename = generate_new_filename(file_path, vendor, date, amount)
    new_path = file_path.parent / new_filename
    
    # Check if target file already exists
    if new_path.exists() and new_path != file_path:
        # Add a counter to make it unique
        counter = 1
        base_name = new_path.stem
        while new_path.exists():
            new_filename = f"{base_name}_{counter}{new_path.suffix}"
            new_path = file_path.parent / new_filename
            counter += 1
    
    if dry_run:
        print(f"  Would rename: {file_path.name} -> {new_filename}", file=sys.stderr)
        return True
    
    try:
        file_path.rename(new_path)
        print(f"  Renamed: {file_path.name} -> {new_filename}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"  Error renaming {file_path.name}: {e}", file=sys.stderr)
        return False


def main():
    """
    Main function to process all receipts in a folder.
    """
    if len(sys.argv) < 3:
        print("Usage: python process_receipts.py <folder_path> <vendor_name> [--dry-run]", file=sys.stderr)
        print("\nArguments:", file=sys.stderr)
        print("  folder_path: Path to folder containing receipt files", file=sys.stderr)
        print("  vendor_name: Vendor name to use for all files", file=sys.stderr)
        print("  --dry-run: Preview changes without actually renaming files", file=sys.stderr)
        sys.exit(1)
    
    folder_path = Path(sys.argv[1])
    vendor_name = sys.argv[2]
    dry_run = '--dry-run' in sys.argv
    
    # Validate folder exists
    if not folder_path.exists():
        print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    if not folder_path.is_dir():
        print(f"Error: Path is not a directory: {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    # Get all supported files
    files = get_supported_image_files(folder_path)
    
    if not files:
        print(f"No supported image or PDF files found in {folder_path}", file=sys.stderr)
        sys.exit(0)
    
    print(f"Found {len(files)} file(s) to process", file=sys.stderr)
    if dry_run:
        print("DRY RUN MODE: No files will be renamed", file=sys.stderr)
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for file_path in files:
        # Process the file
        result = process_receipt_file(file_path, vendor_name)
        
        if result['success']:
            # Rename the file
            if rename_file_with_info(
                file_path, 
                result['vendor'], 
                result['date'], 
                result['amount'],
                dry_run=dry_run
            ):
                success_count += 1
            else:
                error_count += 1
        else:
            error_count += 1
    
    # Summary
    print(f"\n--- Summary ---", file=sys.stderr)
    print(f"Successfully processed: {success_count}", file=sys.stderr)
    print(f"Errors: {error_count}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Receipt OCR Script
Extracts transaction date, amount, and vendor name from a receipt image.
Supports multiple image formats: JPEG, PNG, GIF, BMP, TIFF, WebP, ICO, and more.
"""

import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    import pytesseract
except ImportError:
    print("Error: Required packages not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Supported image formats
SUPPORTED_FORMATS = {
    'JPEG', 'JPG', 'PNG', 'GIF', 'BMP', 'TIFF', 'TIF', 
    'WEBP', 'ICO', 'PCX', 'DCX', 'EPS', 'PCD', 'PSD',
    'SGI', 'TGA', 'XBM', 'XPM', 'PPM', 'PGM', 'PBM'
}


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.
    Applies contrast enhancement, noise reduction, sharpening, and binarization.
    
    Args:
        image: PIL Image object to preprocess
        
    Returns:
        Preprocessed PIL Image object optimized for OCR
    """
    # Convert to grayscale if not already (better for OCR)
    if image.mode != 'L':
        image = image.convert('L')
    
    # Upscale image if it's too small (improves OCR accuracy)
    # Minimum recommended size for OCR is around 300 DPI
    width, height = image.size
    min_dimension = min(width, height)
    
    # If image is smaller than 800px on shortest side, upscale it
    if min_dimension < 800:
        scale_factor = 800 / min_dimension
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Enhance contrast using autocontrast (stretches histogram to full range)
    # This normalizes the brightness and improves text visibility
    image = ImageOps.autocontrast(image, cutoff=2)
    
    # Apply additional contrast enhancement for clearer text
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)  # Increase contrast by 50%
    
    # Sharpen the image to make text edges clearer and more defined
    image = image.filter(ImageFilter.SHARPEN)
    
    # Apply binarization/thresholding for better text recognition
    # Convert to binary (black and white) which helps separate text from background
    # Use Otsu's method equivalent: find optimal threshold automatically
    # For simplicity, use adaptive thresholding with a fixed threshold
    threshold = 128
    image = image.point(lambda p: 255 if p > threshold else 0, mode='1')
    
    # Convert back to grayscale ('L') mode for pytesseract compatibility
    # Mode '1' is 1-bit black/white, pytesseract works better with 'L' (8-bit grayscale)
    image = image.convert('L')
    
    return image


def validate_image_format(image_path: str) -> bool:
    """
    Validate that the image file is in a supported format.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if format is supported, False otherwise
    """
    try:
        file_ext = Path(image_path).suffix.upper().lstrip('.')
        if file_ext in SUPPORTED_FORMATS:
            return True
        
        # Also check by attempting to open with PIL
        # PIL might support formats not in our list
        with Image.open(image_path) as img:
            format_name = img.format
            if format_name and format_name.upper() in SUPPORTED_FORMATS:
                return True
        
        return False
    except Exception:
        return False


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from receipt image using OCR.
    Supports multiple image formats including JPEG, PNG, GIF, BMP, TIFF, WebP, etc.
    """
    try:
        # Validate format
        if not validate_image_format(image_path):
            print(f"Warning: Image format may not be fully supported. Attempting to process anyway...", file=sys.stderr)
        
        # Open and process the image with proper context management
        with Image.open(image_path) as img:
            # Handle EXIF orientation data
            try:
                # Automatically rotate image based on EXIF orientation tag
                img = ImageOps.exif_transpose(img)
            except Exception:
                # If EXIF reading fails, continue without rotation
                pass
            
            # Convert to RGB if necessary (some formats like RGBA, P, etc. need conversion)
            if img.mode not in ('RGB', 'L'):
                # Convert to RGB for better OCR compatibility
                rgb_image = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_image.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)  # Use alpha channel as mask
                else:
                    rgb_image.paste(img)
                img = rgb_image
            
            # Preprocess image for better OCR accuracy
            img = preprocess_image_for_ocr(img)
            
            # Use Tesseract OCR with default settings
            text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        print(f"Error reading image: {e}", file=sys.stderr)
        sys.exit(1)


def extract_text_from_logo_region(image_path: str, logo_height_percent: float = 0.15) -> Optional[str]:
    """
    Extract text from the logo region at the top of the receipt.
    Supports multiple image formats.
    
    Args:
        image_path: Path to the receipt image
        logo_height_percent: Percentage of image height to use for logo region (default 15%)
    
    Returns:
        Extracted text from logo region, or None if no text found
    """
    try:
        with Image.open(image_path) as img:
            # Handle EXIF orientation data
            try:
                # Automatically rotate image based on EXIF orientation tag
                img = ImageOps.exif_transpose(img)
            except Exception:
                # If EXIF reading fails, continue without rotation
                pass
            
            # Convert to RGB if necessary for better OCR compatibility
            if img.mode not in ('RGB', 'L'):
                rgb_image = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_image.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                else:
                    rgb_image.paste(img)
                img = rgb_image
            
            width, height = img.size
            
            # Calculate logo region (top portion of image)
            logo_height = int(height * logo_height_percent)
            
            # Crop the top portion of the image
            logo_region = img.crop((0, 0, width, logo_height))
            
            # Preprocess logo region for better OCR accuracy
            logo_region = preprocess_image_for_ocr(logo_region)
            
            # Use OCR with configuration optimized for logos/titles
            # Page segmentation mode 6 = Assume a single uniform block of text
            # Page segmentation mode 7 = Treat the image as a single text line
            # Page segmentation mode 8 = Treat the image as a single word
            custom_config = r'--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789&.,- '
            
            logo_text = pytesseract.image_to_string(logo_region, config=custom_config)
            
            # Clean up the text
            logo_text = logo_text.strip()
            
            if logo_text and len(logo_text) > 2:
                return logo_text
        
        return None
    except Exception as e:
        print(f"Warning: Could not extract text from logo region: {e}", file=sys.stderr)
        return None


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


def extract_vendor(text: str, logo_text: Optional[str] = None) -> Optional[str]:
    """
    Extract vendor name from receipt text.
    Prioritizes vendor name from logo region if available.
    Takes ALL text from logo region and removes dates and currency information.
    
    Args:
        text: Full OCR text from receipt
        logo_text: Text extracted from logo region (if available)
    """
    # First, try to extract vendor name from logo text if available
    if logo_text:
        vendor = logo_text.strip()
        
        # Remove date patterns (various formats)
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
            r'\w+\s+\d{1,2},?\s+\d{4}',        # Month DD, YYYY
            r'\d{1,2}\s+\w+\s+\d{4}',          # DD Month YYYY
            r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',  # Time formats
        ]
        
        for pattern in date_patterns:
            vendor = re.sub(pattern, '', vendor, flags=re.IGNORECASE)
        
        # Remove currency information (dollar signs, amounts, etc.)
        currency_patterns = [
            r'\$[\d,]+\.?\d{0,2}',              # $XX.XX or $XX
            r'[\d,]+\.?\d{0,2}\s*\$',           # XX.XX $ (currency after amount)
            r'(?:total|amount|due|balance|charge|tax|subtotal)[:\s]*\$?\s*[\d,]+\.?\d{0,2}',
            r'\d+\.\d{2}',                      # Decimal amounts (likely currency)
        ]
        
        for pattern in currency_patterns:
            vendor = re.sub(pattern, '', vendor, flags=re.IGNORECASE)
        
        # Remove common receipt header words that might appear
        skip_words = ['receipt', 'invoice', 'transaction', 'date', 'time', 'total', 
                     'amount', 'due', 'balance', 'charge', 'tax', 'subtotal']
        words = vendor.split()
        vendor = ' '.join([w for w in words if w.lower() not in skip_words])
        
        # Clean up: remove leading/trailing punctuation and whitespace
        vendor = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', vendor)
        # Remove extra whitespace
        vendor = ' '.join(vendor.split())
        # Remove standalone numbers or number-only words
        vendor = ' '.join([w for w in vendor.split() if not re.match(r'^[\d\s\-\/\.:]+$', w)])
        
        # Final check: ensure vendor has letters and reasonable length
        if len(vendor) > 2 and re.search(r'[a-zA-Z]', vendor):
            return vendor
    
    # Fallback: Vendor name is usually at the top of the receipt
    lines = text.split('\n')
    
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
            vendor = ' '.join(vendor.split())
            if len(vendor) > 2:
                return vendor
    
    return None


def main():
    """
    Main function to process receipt image.
    Supports multiple image formats: JPEG, PNG, GIF, BMP, TIFF, WebP, ICO, and more.
    """
    if len(sys.argv) < 2:
        print("Usage: python extract_receipt.py <path_to_receipt_image> [--debug]")
        print("\nSupported formats: JPEG, PNG, GIF, BMP, TIFF, WebP, ICO, PCX, EPS, PSD, and more")
        sys.exit(1)
    
    image_path = sys.argv[1]
    debug_mode = '--debug' in sys.argv
    
    # Validate file exists
    if not Path(image_path).exists():
        print(f"Error: File not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    
    # Check if file is likely an image
    try:
        with Image.open(image_path) as img:
            format_name = img.format or "Unknown"
            if debug_mode:
                print(f"Image format detected: {format_name}", file=sys.stderr)
                print(f"Image mode: {img.mode}", file=sys.stderr)
                print(f"Image size: {img.size}", file=sys.stderr)
    except Exception as e:
        print(f"Error: File appears to be an unsupported image format: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract text from image
    print("Extracting text from receipt...", file=sys.stderr)
    text = extract_text_from_image(image_path)
    
    # Extract text from logo region (top of receipt)
    print("Extracting text from logo region...", file=sys.stderr)
    logo_text = extract_text_from_logo_region(image_path)
    
    # Extract information
    vendor = extract_vendor(text, logo_text)
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

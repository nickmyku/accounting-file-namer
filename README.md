# Receipt OCR Extraction Tool

A Python-based OCR (Optical Character Recognition) script that automatically extracts key accounting information from receipt images and PDF files. The script processes receipt images and PDFs to extract vendor name, transaction date, transaction amount, and receipt/invoice number, making it useful for accounting file organization and record-keeping.

## Project Overview

**Purpose**: Extract structured data (vendor, date, amount, receipt/invoice number) from receipt images and PDF files for accounting purposes, and automatically rename files with extracted information.

**Main Scripts**:
- `extract_receipt.py` - Command-line tool that processes individual receipt images and PDF files and outputs extracted information.
- `process_receipts.py` - Batch processing tool that processes all receipt files in a folder and automatically renames them with vendor, date, and amount information.

**Key Functionality**:
- Performs OCR on receipt images and PDF files using Tesseract
- Converts PDF pages to images for OCR processing
- Applies image preprocessing to improve OCR accuracy
- Extracts vendor name from logo/header region
- Parses transaction date in multiple formats
- Identifies transaction amount (typically the total)
- Extracts receipt number or invoice number from receipt text
- Outputs structured data in human-readable format
- Batch processes multiple files and automatically renames them

## Project Structure

```
/workspace/
├── extract_receipt.py    # Single-file receipt extraction script (executable)
├── process_receipts.py   # Batch processing and renaming script (executable)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Prerequisites

### System Dependencies

**Tesseract OCR** (required):
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

**Poppler** (required for PDF support):
- **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
- **macOS**: `brew install poppler`
- **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases

### Python Dependencies

Install Python packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

**Required packages**:
- `Pillow>=10.0.0` - Image processing library
- `pytesseract>=0.3.10` - Python wrapper for Tesseract OCR
- `pdf2image>=1.16.0` - PDF to image conversion library

**Python version**: Python 3.x required (tested with Python 3.12)

## Installation Steps

1. Install Tesseract OCR on your system (see Prerequisites above)
2. Install Poppler utilities for PDF support (see Prerequisites above)
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Verify installation:
   ```bash
   python extract_receipt.py --help
   ```

## Usage

### Basic Usage

```bash
python extract_receipt.py <path_to_receipt_file> [--vendor VENDOR_NAME] [--debug]
```

**Arguments**:
- `<path_to_receipt_file>`: Path to the receipt image or PDF file (required)
- `--vendor VENDOR_NAME`: Optional vendor name to override auto-detection
- `--debug`: Optional flag to display raw OCR output and debug information

### Examples

```bash
# Process a JPEG receipt image
python extract_receipt.py receipt.jpg

# Process a PNG receipt image
python extract_receipt.py receipt.png

# Process a TIFF image (common for scanned receipts)
python extract_receipt.py receipt.tiff

# Process a PDF receipt file
python extract_receipt.py receipt.pdf

# Process with debug output
python extract_receipt.py receipt.jpg --debug

# Process PDF with debug output
python extract_receipt.py receipt.pdf --debug
```

### Output Format

The script outputs structured receipt information:

```
--- Receipt Details ---
Vendor: Starbucks Coffee
Transaction Date: 2023-12-15
Transaction Amount: $4.75
Receipt/Invoice Number: RCPT-12345
```

**Output fields**:
- **Vendor**: Business/vendor name extracted from receipt header/logo region
- **Transaction Date**: Date in YYYY-MM-DD format (ISO 8601)
- **Transaction Amount**: Currency amount in $XX.XX format
- **Receipt/Invoice Number**: Receipt number, invoice number, order number, transaction reference, or similar identifier extracted from receipt text

If a field cannot be extracted, it will display "Not found".

## Batch Processing

### Using `process_receipts.py`

The `process_receipts.py` script processes all receipt files in a folder, extracts information from each file, and automatically renames them to include vendor, date, and transaction amount.

**Usage**:
```bash
python process_receipts.py <folder_path> <vendor_name> [--dry-run]
```

**Arguments**:
- `<folder_path>`: Path to folder containing receipt files (required)
- `<vendor_name>`: Vendor name to use for all files (required)
- `--dry-run`: Preview changes without actually renaming files (optional)

**Examples**:
```bash
# Process all receipts in a folder
python process_receipts.py /path/to/receipts "Starbucks Coffee"

# Preview changes before renaming (dry-run mode)
python process_receipts.py /path/to/receipts "Starbucks Coffee" --dry-run

# Process receipts with a vendor name containing spaces
python process_receipts.py ./receipts "Target Store"
```

**File Naming Format**:
Files are renamed using the format: `{vendor}_{date}_{$amount}.{ext}`

Example output:
- `receipt.jpg` → `Starbucks_Coffee_2023-12-15_$4.75.jpg`
- `invoice.pdf` → `Target_Store_2024-01-20_$125.50.pdf`

**Features**:
- Automatically finds all supported image and PDF files in the folder
- Processes each file using OCR to extract date and amount
- Uses the provided vendor name for all files
- Sanitizes filenames to ensure they're valid (removes invalid characters)
- Handles duplicate filenames by adding a counter
- Continues processing even if individual files fail
- Shows progress and summary statistics

**Dry-Run Mode**:
Use `--dry-run` to preview what files would be renamed without actually renaming them. This is useful for verifying the vendor name and checking what information will be extracted before making changes.

**Output**:
The script prints processing status to stderr, showing:
- Number of files found
- Processing status for each file
- New filename for each file
- Summary of successful and failed operations

## Supported File Formats

### Image Formats

The script supports a wide range of image formats through the Pillow library:

- **JPEG/JPG** - Most common format for photos
- **PNG** - Lossless format with transparency support
- **GIF** - Animated or static images
- **BMP** - Windows bitmap format
- **TIFF/TIF** - High-quality format often used for scanned documents
- **WebP** - Modern web format
- **ICO** - Icon format
- **PCX** - Legacy format
- **EPS** - Encapsulated PostScript
- **PSD** - Adobe Photoshop format
- **SGI**, **TGA**, **XBM**, **XPM**, **PPM**, **PGM**, **PBM** - Additional formats

### PDF Format

The script also supports **PDF files** (both scanned PDFs and text-based PDFs):
- Converts PDF pages to images at 300 DPI for optimal OCR quality
- Processes all pages in multi-page PDFs
- Extracts text using OCR (works for scanned PDFs)

The script automatically handles:
- EXIF orientation data (auto-rotation for images)
- Color mode conversion (RGB, RGBA, grayscale)
- Image preprocessing for OCR optimization
- PDF page conversion to images

## Technical Details

### Image Preprocessing

The script applies several preprocessing steps to improve OCR accuracy:

1. **Grayscale conversion** - Converts color images to grayscale
2. **Upscaling** - Scales images smaller than 800px on shortest side
3. **Contrast enhancement** - Applies autocontrast and contrast boosting (1.5x)
4. **Sharpening** - Applies sharpening filter for clearer text edges
5. **Binarization** - Converts to binary (black/white) using thresholding

### OCR Processing

- Uses Tesseract OCR engine via `pytesseract`
- For images: Extracts full text from entire receipt image
- For PDFs: Converts pages to images, then extracts text from each page
- Separately extracts text from logo/header region (top 15% of image/first PDF page)
- Uses custom OCR configuration for logo region (PSM mode 6)

### Data Extraction Logic

**Vendor Name**:
- Prioritizes extraction from logo/header region (top 15% of image)
- Filters out addresses, phone numbers, URLs, emails, zip codes
- Removes common receipt header words (receipt, invoice, date, etc.)
- Falls back to first substantial text line if logo extraction fails

**Transaction Date**:
- Supports multiple date formats:
  - MM/DD/YYYY or DD/MM/YYYY
  - YYYY/MM/DD
  - Month DD, YYYY (e.g., "December 15, 2023")
  - DD Month YYYY (e.g., "15 December 2023")
- Normalizes output to YYYY-MM-DD format

**Transaction Amount**:
- Searches for currency patterns ($XX.XX)
- Looks for keywords: "total", "amount", "due", "balance", "charge"
- Selects largest amount found (typically the total)
- Handles comma-separated numbers

**Receipt/Invoice Number**:
- Searches for patterns containing keywords: "receipt", "invoice", "order", "transaction", "ref", "reference"
- Recognizes common formats:
  - "Receipt #12345" or "Invoice #12345"
  - "Receipt Number: 12345" or "Invoice No: 12345"
  - "RCPT-12345", "INV-12345", "ORD-12345" (abbreviated formats)
  - Standalone "#" followed by alphanumeric code
- Filters out false positives (dates, phone numbers, zip codes, years)
- Looks for alphanumeric codes (3+ characters) near receipt/invoice keywords
- Returns the first valid match found

### Error Handling

- Validates file existence before processing
- Validates image format compatibility
- Provides error messages for missing dependencies
- Handles EXIF orientation errors gracefully
- Continues processing if logo region extraction fails

## Debug Mode

Enable debug mode with `--debug` flag to see:
- Detected image format and properties
- Raw OCR text output
- Processing steps and warnings

```bash
python extract_receipt.py receipt.jpg --debug
```

Debug output includes:
- Image format, mode, and size
- Full OCR text extraction
- Processing status messages

## Features

- ✅ Extracts vendor name from receipt header/logo region
- ✅ Identifies transaction date in various formats
- ✅ Finds transaction amount (typically the total)
- ✅ Extracts receipt number or invoice number from receipt text
- ✅ Uses OCR to read text from receipt images and PDFs
- ✅ Supports multiple image formats (JPEG, PNG, TIFF, etc.)
- ✅ Supports PDF files (scanned and text-based)
- ✅ Automatic image preprocessing for better accuracy
- ✅ Handles EXIF orientation data
- ✅ Processes multi-page PDFs
- ✅ Filters out extraneous information (addresses, phone numbers, etc.)
- ✅ Debug mode for troubleshooting
- ✅ Batch processing of multiple files in a folder
- ✅ Automatic file renaming with extracted information
- ✅ Dry-run mode to preview changes before renaming

## Troubleshooting

### Common Issues

**Tesseract not found**:
```
Error: Tesseract is not installed or not in PATH
```
**Solution**: Install Tesseract OCR (see Prerequisites section)

**Missing Python packages**:
```
Error: Required packages not installed
```
**Solution**: Run `pip install -r requirements.txt`

**File not found**:
```
Error: File not found: <path>
```
**Solution**: Verify the file path is correct and file exists

**Unsupported file format**:
```
Error: File appears to be an unsupported format
```
**Solution**: Ensure the file is a valid image in a supported format or a PDF file

**PDF conversion errors**:
```
Error reading PDF: ...
```
**Solution**: Ensure Poppler utilities are installed (see Prerequisites section)

**Poor OCR accuracy**:
- Try preprocessing the image manually (increase contrast, sharpen)
- Ensure image is high resolution (at least 300 DPI recommended)
- Use debug mode to inspect raw OCR output
- Check image quality and lighting conditions

**Batch processing errors**:
```
Error: Could not import from extract_receipt.py
```
**Solution**: Ensure `extract_receipt.py` is in the same directory as `process_receipts.py`

**No files found in folder**:
```
No supported image or PDF files found in <folder>
```
**Solution**: Verify the folder path is correct and contains image or PDF files in supported formats

**Permission errors when renaming**:
```
Error renaming <filename>: Permission denied
```
**Solution**: Ensure you have write permissions in the target folder

## Code Structure

### `extract_receipt.py`

**Main Functions**:
- `main()` - Entry point, handles command-line arguments
- `extract_text_from_image()` - Performs OCR on full image
- `extract_text_from_pdf()` - Extracts text from PDF files
- `extract_text_from_logo_region()` - Extracts text from header region
- `preprocess_image_for_ocr()` - Applies image enhancements
- `extract_vendor()` - Extracts vendor name from text
- `extract_date()` - Parses and formats transaction date
- `extract_amount()` - Finds transaction amount
- `extract_receipt_or_invoice_number()` - Extracts receipt/invoice number from text
- `validate_image_format()` - Checks if image format is supported
- `is_pdf_file()` - Checks if file is a PDF

**Key Constants**:
- `SUPPORTED_FORMATS` - Set of supported image format extensions

### `process_receipts.py`

**Main Functions**:
- `main()` - Entry point, handles command-line arguments and batch processing
- `get_supported_image_files()` - Finds all supported image and PDF files in a folder
- `process_receipt_file()` - Processes a single receipt file and extracts information
- `generate_new_filename()` - Creates new filename with vendor, date, and amount
- `rename_file_with_info()` - Renames file with extracted information
- `sanitize_filename()` - Removes invalid characters from filenames
- `format_amount_for_filename()` - Formats amount for use in filename

**Key Features**:
- Imports and reuses functions from `extract_receipt.py`
- Handles batch processing of multiple files
- Provides dry-run mode for safe preview
- Error handling and progress reporting

## Development Notes

- Script is executable (`#!/usr/bin/env python3`)
- Uses type hints for better code clarity
- Handles edge cases (missing data, parsing errors)
- Provides informative error messages
- Outputs to stdout, errors to stderr

## Future Enhancements

Potential improvements:
- Support for multiple currencies
- Export to structured formats (JSON, CSV)
- Configuration file for customization
- Integration with accounting software APIs
- Option to preserve original filenames while creating organized copies
- Support for custom filename templates

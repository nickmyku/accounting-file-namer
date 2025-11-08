# Receipt OCR Extraction Tool

A Python-based OCR (Optical Character Recognition) script that automatically extracts key accounting information from receipt images and PDF files. The script processes receipt images and PDFs to extract vendor name, transaction date, and transaction amount, making it useful for accounting file organization and record-keeping.

## Project Overview

**Purpose**: Extract structured data (vendor, date, amount) from receipt images and PDF files for accounting purposes.

**Main Script**: `extract_receipt.py` - Command-line tool that processes receipt images and PDF files and outputs extracted information.

**Key Functionality**:
- Performs OCR on receipt images and PDF files using Tesseract
- Converts PDF pages to images for OCR processing
- Applies image preprocessing to improve OCR accuracy
- Extracts vendor name from logo/header region
- Parses transaction date in multiple formats
- Identifies transaction amount (typically the total)
- Outputs structured data in human-readable format

## Project Structure

```
/workspace/
├── extract_receipt.py    # Main script (executable)
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
```

**Output fields**:
- **Vendor**: Business/vendor name extracted from receipt header/logo region
- **Transaction Date**: Date in YYYY-MM-DD format (ISO 8601)
- **Transaction Amount**: Currency amount in $XX.XX format

If a field cannot be extracted, it will display "Not found".

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
- ✅ Uses OCR to read text from receipt images and PDFs
- ✅ Supports multiple image formats (JPEG, PNG, TIFF, etc.)
- ✅ Supports PDF files (scanned and text-based)
- ✅ Automatic image preprocessing for better accuracy
- ✅ Handles EXIF orientation data
- ✅ Processes multi-page PDFs
- ✅ Filters out extraneous information (addresses, phone numbers, etc.)
- ✅ Debug mode for troubleshooting

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

## Code Structure

**Main Functions**:
- `main()` - Entry point, handles command-line arguments
- `extract_text_from_image()` - Performs OCR on full image
- `extract_text_from_logo_region()` - Extracts text from header region
- `preprocess_image_for_ocr()` - Applies image enhancements
- `extract_vendor()` - Extracts vendor name from text
- `extract_date()` - Parses and formats transaction date
- `extract_amount()` - Finds transaction amount
- `validate_image_format()` - Checks if image format is supported

**Key Constants**:
- `SUPPORTED_FORMATS` - Set of supported image format extensions

## Development Notes

- Script is executable (`#!/usr/bin/env python3`)
- Uses type hints for better code clarity
- Handles edge cases (missing data, parsing errors)
- Provides informative error messages
- Outputs to stdout, errors to stderr

## Future Enhancements

Potential improvements:
- Support for multiple currencies
- Batch processing of multiple images
- Export to structured formats (JSON, CSV)
- Configuration file for customization
- Integration with accounting software APIs

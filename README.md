# accounting-file-namer
script to read a file and change its name to reflect the files content, specific to accounting related data

## Receipt OCR Script

A Python script that extracts transaction date, amount, and vendor name from receipt images.

### Prerequisites

1. Install Tesseract OCR:
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

```bash
python extract_receipt.py <path_to_receipt_image> [--debug]
```

### Supported Image Formats

The script supports a wide range of image formats including:
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
- And more formats supported by Pillow library

### Example

```bash
# JPEG image
python extract_receipt.py receipt.jpg

# PNG image
python extract_receipt.py receipt.png

# TIFF image (common for scanned receipts)
python extract_receipt.py receipt.tiff

# WebP image
python extract_receipt.py receipt.webp
```

Output:
```
--- Receipt Details ---
Vendor: Starbucks Coffee
Transaction Date: 12/15/2023
Transaction Amount: $4.75
```

### Features

- Extracts vendor name from receipt header
- Identifies transaction date in various formats
- Finds transaction amount (typically the total)
- Uses OCR to read text from receipt images

### Debug Mode

Add `--debug` flag to see raw OCR output:
```bash
python extract_receipt.py receipt.jpg --debug
```

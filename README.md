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
python extract_receipt.py <path_to_receipt_image.jpg>
```

### Example

```bash
python extract_receipt.py receipt.jpg
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

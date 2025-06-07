# Invoice OCR Extraction Project

This project extracts structured data from invoice PDF files using OCR (Tesseract) and regex-based post-processing. Outputs are stored in structured JSON format.

## Features

- PDF to text extraction using pdfplumber and pytesseract.
- Regex-based extraction of invoice details like:
  - Invoice number, date, supplier, bill-to
  - Line items (code, description, quantity, unit price, total price)
  - PO number, subtotal, VAT, total, and payment details.
- JSON output per invoice.
- Summary report generation.

## Requirements

Install required packages with:

```bash
pip install -r requirements.txt

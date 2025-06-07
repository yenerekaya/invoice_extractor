import os
import json
import pdfplumber
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io
from utils import extract_data_from_text, generate_report

INPUT_DIR = "invoices"
OUTPUT_DIR = "outputs"
REPORT_FILE = "reports/report.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("reports", exist_ok=True)

def convert_pdf_to_text(pdf_path):
    text = ""

    # İlk olarak pdfplumber ile dene
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass

    # Eğer text boşsa veya başarısızsa OCR’a geç
    if not text.strip():
        print(f"🔍 OCR uygulanıyor: {os.path.basename(pdf_path)}")
        doc = fitz.open(pdf_path)
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += pytesseract.image_to_string(img) + "\n"

    # OCR veya metin sonucu çıktısını .txt olarak kaydet
    debug_txt_path = os.path.join(OUTPUT_DIR, os.path.basename(pdf_path).replace(".pdf", ".txt"))
    with open(debug_txt_path, "w") as debug_file:
        debug_file.write(text)

    return text

def process_invoice(file_name):
    pdf_path = os.path.join(INPUT_DIR, file_name)
    text = convert_pdf_to_text(pdf_path)
    extracted_data = extract_data_from_text(text)
    output_path = os.path.join(OUTPUT_DIR, file_name.replace(".pdf", ".json"))
    with open(output_path, "w") as f:
        json.dump(extracted_data, f, indent=2)
    return extracted_data

def main():
    all_results = []
    for file in os.listdir(INPUT_DIR):
        if file.endswith(".pdf"):
            print(f"📄 İşleniyor: {file}")
            result = process_invoice(file)
            print(f"📤 Çıktı üretildi: {file.replace('.pdf', '.json')}")
            all_results.append(result)

    generate_report(all_results, REPORT_FILE)
    print("\n✅ Tüm faturalar işlendi. Rapor ve JSON çıktıları hazır.")

if __name__ == "__main__":
    main()
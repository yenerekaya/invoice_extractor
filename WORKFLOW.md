# Invoice Extraction Workflow

Bu belge, proje sürecinde kullanılan veri işleme adımlarını detaylı olarak açıklar.

---

## 1. Veri Kaynağı

- `invoices/` klasörü altına PDF formatındaki faturaları yerleştirin.

---

## 2. Veri İşleme

`main.py` çalıştırıldığında şu işlemler sırayla gerçekleşir:

### 📄 2.1 PDF Metni Çözümleme
- `pdfplumber` kullanılarak doğrudan PDF içeriği okunmaya çalışılır.
- Metin alınamazsa `pytesseract` ile OCR (optik karakter tanıma) devreye girer.

### 🔍 2.2 Bilgi Çıkarımı
- `utils.py` içindeki regex desenleriyle şu bilgiler çıkarılır:
  - Fatura numarası ve tarihi
  - Tedarikçi ve müşteri bilgileri (bill_to)
  - Ürün kalemleri (item code, description, quantity, price, PO number)
  - Toplam, subtotal, ödeme detayları

---

## 3. Çıktılar

- Tüm çıktı dosyaları `outputs/` klasörüne yazılır:
  - `.json`: Yapılandırılmış veriler
  - `.txt`: OCR veya metin çıkarımı

---

## 4. Raporlama

- `reports/report.txt`: İşlenen dosyaların dökümünü ve başarı oranını içerir.

---

## 5. Notlar

- Proje, farklı formatlardaki faturalarda esnek şekilde çalışacak şekilde tasarlanmıştır.
- OCR ile alınan metin kalitesine göre başarı oranı değişebilir.

---

## 6. Çalıştırma

```bash
python main.py

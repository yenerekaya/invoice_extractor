import re

def parse_number(s):
    if "," in s and not "." in s:
        return float(s.replace(".", "").replace(",", "."))
    return float(s.replace(",", ""))

def extract_data_from_text(text):
    # Tedarikçi adını ilk büyük harfli bloktan al (dinamik)
    supplier_line = next((line.strip() for line in text.splitlines() if re.match(r"^[A-Z][A-Z\s,&\-\.]{3,}$", line.strip())), None)

    invoice_no = re.search(r"(?i)Invoice Number[:\s]*([A-Z0-9\-]+)", text)
    invoice_date = re.search(r"(?i)(Invoice Date|Date)[:\s]*([\d/\.\-]+)", text)

    bill_to_match = re.search(
        r"BILL TO[:\s]*([\s\S]*?)(?=(DESCRIPTION|INVOICE|ITEMS|Product Code|e\s|Subtotal|Payment|Terms))",
        text, re.IGNORECASE)
    bill_to = bill_to_match.group(1).strip() if bill_to_match else None

    items = []

    single_line_text = text.replace("\n", " ")

    product_regex = re.compile(
        r"(PRD-\d+)\s+(.*?)\s+Qty[:\s]*(\d+)\s+Price[:\s]*\$?([\d.,]+)\s+Total[:\s]*\$?([\d.,]+)\s+PO[:\s]*PO-?\s*(\d+)",
        re.IGNORECASE
    )
    for match in product_regex.findall(single_line_text):
        items.append({
            "item_code": match[0],
            "description": match[1].strip(),
            "quantity": int(match[2]),
            "unit_price": parse_number(match[3]),
            "total_price": parse_number(match[4]),
            "po_number": f"PO-{match[5]}"
        })

    fallback_regex = re.compile(
        r"Product Code[:;\s]+(PRD-[\dA-Z\-]+).*?Quantity[:;\s]+(\d+)\s+units.*?Unit Price[:;\s]+\$([\d.,]+).*?Amount[:;\s]+\$([\d.,]+)",
        re.DOTALL
    )
    for match in fallback_regex.findall(single_line_text):
        items.append({
            "item_code": match[0],
            "description": None,
            "quantity": int(match[1]),
            "unit_price": parse_number(match[2]),
            "total_price": parse_number(match[3]),
            "po_number": None
        })

    lines = [ln.strip() for ln in text.splitlines()]
    for i, line in enumerate(lines):
        code_match = re.search(r"Product Code[:;\s]+(PRD-[\dA-Z\-]+)", line)
        if not code_match:
            continue

        item_code = code_match.group(1)
        description_line = None
        if i > 0:
            prev = lines[i - 1]
            if prev and not re.search(r"Product Code|Quantity|Unit Price|Amount", prev, re.I):
                num_match = re.match(r"^\d+[.,]?\s+(.+)", prev)
                description_line = num_match.group(1).strip() if num_match else prev

        blk = "\n".join(lines[i : i + 7])
        q  = re.search(r"Quantity[:;\s]+(\d+)", blk)
        up = re.search(r"Unit Price[:;\s]+\$?([\d.,]+)", blk)
        am = re.search(r"Amount[:;\s]+\$?([\d.,]+)",     blk)

        if q and up and am:
            item = {
                "item_code": item_code,
                "description": description_line,
                "quantity": int(q.group(1)),
                "unit_price": parse_number(up.group(1)),
                "total_price": parse_number(am.group(1)),
                "po_number": None
            }
            items.append(item)

    # Tekrar edenleri filtrele (açıklaması olanı tut)
    dedup = {}
    for it in items:
        key = (it["item_code"], it["quantity"], it["total_price"])
        if key not in dedup or (dedup[key]["description"] is None and it["description"]):
            dedup[key] = it
    items = list(dedup.values())

    # PO en üstte geçiyorsa uygula
    po_top = re.search(r"PO NUMBER[:;\s]+(PO-\d+)", text, re.IGNORECASE)
    if po_top:
        po_value = po_top.group(1)
        for item in items:
            if not item["po_number"]:
                item["po_number"] = po_value

    # Hizmet tipi itemlar için regex
    service_regex = re.compile(
        r"(?P<description>[A-Za-z][A-Za-z0-9\s\-\&]{3,100}?)\s*Hours[:\s]*([0-9]+)\s*[x×]\s*Rate[:\s]*\$([0-9.,]+)[\s\S]*?Amount[:\s]*\$([0-9.,]+)",
        re.IGNORECASE
    )
    for match in service_regex.findall(single_line_text):
        desc, qty, rate, amount = match
        desc = desc.strip()

        # 🔧 Temizleme burada yapılacak
        desc = re.sub(r"^(DESCRIPTION|US\d{9}|e|ITEM)\s+", "", desc, flags=re.IGNORECASE).strip()

        items.append({
            "item_code": None,
            "description": desc,
            "quantity": int(qty),
            "unit_price": parse_number(rate),
            "total_price": parse_number(amount),
            "po_number": None
        })

    subtotal = re.search(r"Subtotal[:\s]*\$?([\d.,]+)", text, re.IGNORECASE)
    vat = re.search(r"VAT\s*\(.*?\)[:\s]*\$?([\d.,]+)", text, re.IGNORECASE)
    total = re.search(r"Total[:\s]*\$?([\d.,]+)", text, re.IGNORECASE)

    # Ödeme bilgileri
    payment_dict = {}
    payment_block_match = re.search(r"(?i)Payment[\s\S]{0,1000}", text)
    if payment_block_match:
        raw_block = payment_block_match.group(0)
        lines = raw_block.strip().split("\n")
        for line in lines:
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip()
                payment_dict[key] = value

    return {
        "invoice_number": invoice_no.group(1) if invoice_no else None,
        "invoice_date": invoice_date.group(2) if invoice_date else None,
        "supplier": {
            "name": supplier_line
        },
        "bill_to": bill_to,
        "items": items,
        "subtotal": parse_number(subtotal.group(1)) if subtotal else None,
        "vat": parse_number(vat.group(1)) if vat else None,
        "total": parse_number(total.group(1)) if total else None,
        "payment_details": payment_dict
    }

def generate_report(all_results, path):
    total_items = 0
    price_correct = 0
    po_found = 0
    po_total = 0
    report_lines = []

    for invoice in all_results:
        for item in invoice["items"]:
            total_items += 1
            # Fiyat doğruluğu
            calculated = round(item["quantity"] * item["unit_price"], 2)
            if abs(calculated - item["total_price"]) < 0.1:
                price_correct += 1
            else:
                report_lines.append(f"Fiyat uyuşmazlığı: {item.get('item_code') or item.get('description') or 'Bilinmeyen ürün'}")

            # PO doğruluğu
            if item["po_number"]:
                po_found += 1
            else:
                report_lines.append(f"PO eksik: {item.get('item_code') or item.get('description') or 'Bilinmeyen ürün'}")

        # Toplam PO sayısı (benzersiz)
        po_total += len(set([i["po_number"] for i in invoice["items"] if i["po_number"]]))

    summary = f"""
Toplam Kalem: {total_items}
Fiyat Doğruluğu: {round(100 * price_correct / total_items, 2) if total_items else 0}%
PO Doğruluğu: {round(100 * po_found / total_items, 2) if total_items else 0}%
Toplam PO Sayısı: {po_total}
"""

    # rapor dosyasına yaz
    with open(path, "w") as f:
        f.write(summary.strip() + "\n\n" + "\n".join(report_lines))
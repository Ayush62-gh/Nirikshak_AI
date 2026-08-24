import re

MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08", "september": "09",
    "october": "10", "november": "11", "december": "12"
}

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _normalize_text(text: str) -> str:
    """Translates Devanagari digits to ASCII digits and cleans whitespace."""
    if not text:
        return ""
    return text.translate(DEVANAGARI_DIGITS)


def _extract_mrp(text_blocks, full_text):
    """
    Extracts MRP string preserving surrounding context (e.g. 'MRP Rs. 45.00 (incl. of all taxes)').
    Tolerates OCR misspellings like 'Pnce' for 'Price' or 'Maximum Retail Pnce'.
    """
    mrp_pattern = re.compile(
        r'(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Ret(?:ail)?\s*P[a-z]{1,4}e?|Ret(?:ail)?\s*P[a-z]{1,4}e?|Rs\.?|₹|INR)'
        r'\s*[:\.-]?\s*(?:Rs\.?|₹|INR)?\s*\d+(?:[\.,]\d{1,2}|\s+\d{2})?'
        r'(?:\s*\(?[^\n\r]*(?:incl|inclusive)[^\n\r]*\)?)?',
        re.IGNORECASE
    )

    for block in text_blocks:
        txt = block.get("text", "").strip()
        match = mrp_pattern.search(txt)
        if match:
            return txt

    match = mrp_pattern.search(full_text)
    if match:
        start = match.start()
        # Find context line
        line = full_text[start:].splitlines()[0].strip()
        return line

    return None


def _extract_net_quantity(text_blocks, full_text):
    """
    Extracts Net Quantity string (e.g. '200 g', '1.5 L', '500g', 'Net Wt: 500 g').
    """
    qty_pattern = re.compile(
        r'(?:Net\s*(?:Qty|Quantity|Wt|Weight|Vol|Volume|Content|Contents)|Nett\s*(?:Qty|Quantity|Wt|Weight))\s*[:\.-]?\s*'
        r'(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|g\.?|kg\.?|ml\.?|l\.?|ltr|liter|litres|liters|pcs|units|n))\b',
        re.IGNORECASE
    )
    generic_qty_pattern = re.compile(
        r'\b(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|kg\.?|ml\.?|ltr|liter|litres|liters))\b',
        re.IGNORECASE
    )

    for block in text_blocks:
        txt = block.get("text", "").strip()
        match = qty_pattern.search(txt)
        if match:
            return match.group(1).strip()

    match = qty_pattern.search(full_text)
    if match:
        return match.group(1).strip()

    # Fallback to generic quantity search
    for block in text_blocks:
        txt = block.get("text", "").strip()
        match = generic_qty_pattern.search(txt)
        if match and not any(kw in txt.lower() for kw in ["mrp", "rs", "₹", "date", "batch", "lot"]):
            return match.group(1).strip()

    match = generic_qty_pattern.search(full_text)
    if match:
        return match.group(1).strip()

    return None


def _extract_manufacturer(text_blocks, full_text):
    """
    Extracts manufacturer name and optional address.
    Tolerates 'Registered Address', 'Regd. Office', 'Factory Address', etc.
    """
    mfg_pattern = re.compile(
        r'(?:Manufactured\s+(?:by|in)|Mfg\s+by|Mfd\s+by|Packed\s+by|Pkd\s+by|Marketed\s+by|Mkd\s+by|Manufacturer\s*[:\.-]|Packer\s*[:\.-])\s*[:\.-]?\s*(.+)',
        re.IGNORECASE
    )
    addr_pattern = re.compile(
        r'(?:Registered\s+Address|Regd\.?\s+(?:Address|Office)|Factory\s+Address|Mfg\.\s+Address|Plant\s+Address|Address|Corp\.?\s+Office)\s*[:\.-]?\s*(.+)',
        re.IGNORECASE
    )

    blocks_text = [b.get("text", "").strip() for b in text_blocks if b.get("text")]
    if not blocks_text and full_text:
        blocks_text = [line.strip() for line in full_text.splitlines() if line.strip()]

    name = None
    address = None

    for i, line in enumerate(blocks_text):
        match = mfg_pattern.search(line)
        if match:
            extracted = match.group(1).strip()
            if extracted:
                name = extracted
            elif i + 1 < len(blocks_text):
                name = blocks_text[i + 1].strip()

            # Address extraction from subsequent line if available
            if i + 1 < len(blocks_text):
                candidate = blocks_text[i + 1].strip()
                if candidate != name and any(
                    kw in candidate.lower()
                    for kw in ["road", "street", "ind", "area", "dist", "state", "pin", "plot", "no", "nagar", "sector", "post", "bhavan", "building"]
                ):
                    address = candidate
            break

    # Look for explicit registered/factory address header if address is still None
    if not address:
        for line in blocks_text:
            match = addr_pattern.search(line)
            if match:
                extracted_addr = match.group(1).strip()
                if extracted_addr:
                    address = extracted_addr
                else:
                    address = line
                break

    if not address and full_text:
        match = addr_pattern.search(full_text)
        if match:
            address = match.group(1).split("\n")[0].strip()

    if not name and full_text:
        match = mfg_pattern.search(full_text)
        if match:
            name = match.group(1).split(",")[0].strip()

    return name, address


def _extract_dates(text_blocks, full_text):
    """
    Extracts month and year of packing / manufacture.
    Tolerates OCR typos like 'Manuiaclure' for 'Manufacture'.
    """
    date_pattern = re.compile(
        r'(?:(?:Month\s*(?:and|&)?\s*Year\s*of|Date\s*of|Month/Year\s*of)\s*)?'
        r'(?:Manui[a-z]+|Manuf[a-z]*|Mfg|Mfd|Pack[a-z]*|Pkd|DOM|DOP|Packing|Manufacture)\s*[:\.-]?\s*'
        r'(?:([0-3]?\d)[\/\.\-\s]+)?([0-1]?\d|[a-zA-Z]{3,9})[\/\.\-\s]+(20\d{2}|\d{2,4})',
        re.IGNORECASE
    )

    generic_pattern = re.compile(
        r'\b([0-1]?\d|[a-zA-Z]{3,9})[\/\.\-\s]+(20\d{2}|\d{2})\b',
        re.IGNORECASE
    )

    combined_text = " ".join([b.get("text", "") for b in text_blocks]) or full_text

    match = date_pattern.search(combined_text)
    if match:
        groups = match.groups()
        m_raw = groups[1]
        y_raw = groups[2]

        # Process month
        m_str = str(m_raw).strip().lower()
        if m_str in MONTH_MAP:
            month = MONTH_MAP[m_str]
        elif m_str.isdigit():
            month = f"{int(m_str):02d}"
        else:
            month = m_str.upper()

        # Process year
        y_str = str(y_raw).strip()
        if len(y_str) == 2:
            year = f"20{y_str}"
        else:
            year = y_str

        return month, year

    match = generic_pattern.search(combined_text)
    if match:
        groups = match.groups()
        m_raw = groups[0]
        y_raw = groups[1]

        m_str = str(m_raw).strip().lower()
        if m_str in MONTH_MAP or m_str.isdigit():
            month = MONTH_MAP.get(m_str, f"{int(m_str):02d}" if m_str.isdigit() else m_str.upper())
            y_str = str(y_raw).strip()
            year = f"20{y_str}" if len(y_str) == 2 else y_str
            return month, year

    return None, None


def _extract_consumer_care(text_blocks, full_text):
    """
    Extracts consumer care text (phone, email, or care line).
    """
    care_pattern = re.compile(
        r'(?:Consumer\s*Care|Customer\s*Care|Care\s*Cell|Contact\s*Us|Feedback|Toll\s*Free)\s*[:\.-]?\s*([^\n\r]+)',
        re.IGNORECASE
    )
    phone_pattern = re.compile(r'\b(?:1800[-\s]?\d{3}[-\s]?\d{4}|\+?91[-\s]?[6-9]\d{9}|\d{3,5}[-\s]?\d{6,8})\b')
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')

    for block in text_blocks:
        txt = block.get("text", "").strip()
        match = care_pattern.search(txt)
        if match and match.group(1).strip():
            return match.group(1).strip()

    match = care_pattern.search(full_text)
    if match and match.group(1).strip():
        return match.group(1).strip()

    email_match = email_pattern.search(full_text)
    phone_match = phone_pattern.search(full_text)

    parts = []
    if phone_match:
        parts.append(phone_match.group(0))
    if email_match:
        parts.append(email_match.group(0))

    if parts:
        return ", ".join(parts)

    return None


def _extract_product_name(text_blocks, full_text, known_extracted):
    """
    Heuristic for product name:
    Selects the first prominent text block that is not matched by any other extracted field.
    """
    used_values = set()
    for val in known_extracted:
        if val and isinstance(val, str):
            used_values.add(val.lower())

    for block in text_blocks:
        txt = block.get("text", "").strip()
        if not txt or len(txt) < 2:
            continue
        txt_lower = txt.lower()

        # Skip if part of already extracted values
        if any(txt_lower in used or used in txt_lower for used in used_values if len(used) > 2):
            continue

        # Skip header/meta keywords
        if any(kw in txt_lower for kw in [
            "mrp", "net wt", "net qty", "mfg", "mfd", "pkd", "packed",
            "consumer", "customer care", "batch", "exp", "use by", "best before"
        ]):
            continue

        return txt

    # Fallback to first line of full_text
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    for line in lines:
        line_lower = line.lower()
        if not any(kw in line_lower for kw in ["mrp", "net wt", "mfg", "pkd", "consumer"]):
            return line

    return None


def extract_fields(ocr_result: dict) -> dict:
    """
    Converts raw OCR output dictionary into structured fields matching the rule engine contract.
    
    Expected input keys:
      - quality: dict with quality_status ('ACCEPTABLE', 'POOR', 'UNREADABLE')
      - full_text: str
      - text_blocks: list of dicts with 'text', 'confidence', 'box'
    """
    if not isinstance(ocr_result, dict):
        ocr_result = {}

    quality = ocr_result.get("quality") or {}
    quality_status = quality.get("quality_status", "ACCEPTABLE")

    raw_full_text = ocr_result.get("full_text", "") or ""
    raw_text_blocks = ocr_result.get("text_blocks", []) or []

    # Normalize Devanagari digits to ASCII digits
    full_text = _normalize_text(raw_full_text)
    text_blocks = [
        {**b, "text": _normalize_text(b.get("text", ""))}
        for b in raw_text_blocks
    ]

    # Field Extractions
    mrp = _extract_mrp(text_blocks, full_text)
    net_qty = _extract_net_quantity(text_blocks, full_text)
    mfg_name, mfg_addr = _extract_manufacturer(text_blocks, full_text)
    month_pkd, year_pkd = _extract_dates(text_blocks, full_text)
    care_info = _extract_consumer_care(text_blocks, full_text)

    known_values = [mrp, net_qty, mfg_name, mfg_addr, care_info]
    product_name = _extract_product_name(text_blocks, full_text, known_values)

    # Extraction confidence flag based on image quality status
    confidence_flag = "HIGH" if quality_status == "ACCEPTABLE" else "LOW"

    return {
        "productId": None,
        "productName": product_name,
        "productType": None,
        "isImported": False,
        "manufacturerName": mfg_name,
        "manufacturerAddress": mfg_addr,
        "packerName": None,
        "importerName": None,
        "netQuantity": net_qty,
        "mrp": mrp,
        "monthOfPacking": month_pkd,
        "yearOfPacking": year_pkd,
        "consumerCare": care_info,
        "countryOfOrigin": None,
        "extraction_confidence": confidence_flag
    }


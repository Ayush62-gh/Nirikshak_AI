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


MRP_BOUNDARIES_RE = re.compile(
    r'(?i)\s*(?:Registered|Regd|Factory|Mfg|Mfd|Packed|Pkd|Marketed|Mkd|For\s+customer|Customer\s*Care|Telephone|Phone|Tel|Email|Contact|Address|Net\s*Qty|Net\s*Wt|Batch|Date|EAN|UPC|Model|Imported|Month|Year|Country)\b'
)

COMPANY_SUFFIX_PATTERN = re.compile(
    r'^(.*?Pvt\.?\s*Ltd\.?|.*?Private\s+Limited|.*?Ltd\.?|.*?Limited|.*?Inc\.?|.*?LLP|.*?Corp\.?|.*?Corporation|.*?Industries|.*?Solutions|.*?Enterprises|.*?Foods)\s*(.*)$',
    re.IGNORECASE
)

ADDRESS_KEYWORDS = [
    "road", "street", "ind", "area", "dist", "state", "pin", "pincode",
    "plot", "no", "nagar", "sector", "post", "bhavan", "building", "floor",
    "mouza", "city", "flat", "lane", "marg", "colony", "pradesh", "bengal",
    "maharashtra", "karnataka", "delhi", "haryana", "gujarat", "tamil nadu",
    "telangana", "kerala", "punjab", "nh-", "po", "tq", "distt", "howrah",
    "bangalore", "bengaluru", "mumbai", "chennai", "kolkata", "hyderabad"
]

BOUNDARY_KEYWORDS_RE = re.compile(
    r'(?i)\s*(?:For\s+customer|Customer\s*Care|Care\s*Cell|Telephone|Phone|Tel|Email|Contact|Net\s*Qty|Net\s*Wt|Batch|EAN|UPC|Model|Imported|Month\s*and\s*Year|Month|Date)\b'
)


def _is_address_text(text: str) -> bool:
    """Checks if text contains address keywords using word boundary matching for short tokens."""
    if not text:
        return False
    text_lower = text.lower()
    for kw in ADDRESS_KEYWORDS:
        if len(kw) <= 3:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return True
        else:
            if kw in text_lower:
                return True
    return False


def _normalize_mrp(raw_mrp: str) -> str:
    """
    Normalizes extracted MRP string to standard statutory format.
    Corrects OCR typos like 'Prce', 'Pnce', 'nclusive', 'incl of taxes'
    to clean format: 'MRP Rs. XX.XX (inclusive of all taxes)' or 'MRP ₹ XX.XX (inclusive of all taxes)'.
    """
    if not raw_mrp:
        return raw_mrp

    text = raw_mrp.strip()

    price_match = re.search(r'(\d+(?:[\.,]\d{1,2}|\s+\d{2})?)', text)
    if not price_match:
        return text

    price_str = price_match.group(1).strip()
    if ' ' in price_str and len(price_str.split()[-1]) == 2:
        parts = price_str.split()
        price_val = f"{parts[0]}.{parts[1]}"
    else:
        price_val = price_str.replace(',', '.')

    if '.' in price_val:
        int_part, dec_part = price_val.split('.', 1)
        if len(dec_part) == 1:
            price_val = f"{int_part}.{dec_part}0"
    else:
        price_val = f"{price_val}.00"

    has_rupee_symbol = '₹' in text
    prefix = "MRP ₹" if has_rupee_symbol else "MRP Rs."

    has_tax = bool(re.search(r'(?i)\b(?:nclusive|inclusive|incl|tax|taxes)\b', text))

    if has_tax:
        return f"{prefix} {price_val} (inclusive of all taxes)"
    else:
        return f"{prefix} {price_val}"


def _extract_mrp(text_blocks, full_text):
    """
    Extracts MRP string preserving surrounding context and normalizing OCR typos.
    Tolerates OCR misspellings like 'Pnce' for 'Price' or 'Maximum Retail Pnce'.
    Prevents over-capturing across flat OCR strings.
    """
    mrp_pattern = re.compile(
        r'(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Ret(?:ail)?\s*P[a-z]{1,4}e?|Ret(?:ail)?\s*P[a-z]{1,4}e?|Rs\.?|₹|INR)'
        r'\s*[:\.-]?\s*(?:Rs\.?|₹|INR)?\s*\d+(?:[\.,]\d{1,2}|\s+\d{2})?'
        r'(?:\s*\(?\s*(?:incl|inclusive|nclusive)[^()\n\r]{0,35}(?:taxes?|tax)?\s*\)?)?',
        re.IGNORECASE
    )

    for block in text_blocks:
        txt = block.get("text", "").strip()
        match = mrp_pattern.search(txt)
        if match:
            extracted = match.group(0).strip()
            # Truncate at boundary keyword if present in block text after match
            after_start = match.start() + len(match.group(0))
            b_match = MRP_BOUNDARIES_RE.search(txt[match.start():])
            if b_match and b_match.start() > 0:
                extracted = txt[match.start():match.start() + b_match.start()].strip()
            return _normalize_mrp(extracted)

    match = mrp_pattern.search(full_text)
    if match:
        start = match.start()
        line = full_text[start:].splitlines()[0].strip()
        b_match = MRP_BOUNDARIES_RE.search(line)
        if b_match and b_match.start() > 0:
            line = line[:b_match.start()].strip()
        return _normalize_mrp(line)

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
    Prevents over-truncating long company names (e.g. Dell International Services India Private Limited).
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
            b_match = BOUNDARY_KEYWORDS_RE.search(extracted)
            if b_match:
                extracted = extracted[:b_match.start()].strip()

            comp_match = COMPANY_SUFFIX_PATTERN.search(extracted)
            if comp_match:
                name = comp_match.group(1).strip()
                remainder = comp_match.group(2).strip()
                if remainder and _is_address_text(remainder):
                    address = remainder
            elif extracted:
                name = extracted
            elif i + 1 < len(blocks_text):
                name = blocks_text[i + 1].strip()

            # Handle broken multi-word block continuation (e.g. "Del" + "l International...")
            if name and i + 1 < len(blocks_text):
                next_block = blocks_text[i + 1].strip()
                if (len(name) < 5 or not name.endswith(("Ltd", "Limited", "Inc", "LLP"))) and not _is_address_text(next_block):
                    combined = f"{name} {next_block}".strip()
                    comp_match = COMPANY_SUFFIX_PATTERN.search(combined)
                    if comp_match:
                        name = comp_match.group(1).strip()
                        rem = comp_match.group(2).strip()
                        if rem and _is_address_text(rem):
                            address = rem
                    elif any(w in next_block.lower() for w in ["international", "services", "india", "private", "limited", "technologies", "solutions"]):
                        name = combined

            if i + 1 < len(blocks_text) and not address:
                candidate = blocks_text[i + 1].strip()
                if candidate != name and _is_address_text(candidate):
                    address = candidate
            break

    if not address or not name:
        for i, line in enumerate(blocks_text):
            match = addr_pattern.search(line)
            if match:
                raw_extracted = match.group(1).strip()
                b_match = BOUNDARY_KEYWORDS_RE.search(raw_extracted)
                if b_match:
                    raw_extracted = raw_extracted[:b_match.start()].strip()

                comp_match = COMPANY_SUFFIX_PATTERN.search(raw_extracted)
                if comp_match:
                    comp_name = comp_match.group(1).strip()
                    remainder_addr = comp_match.group(2).strip()

                    if not name:
                        name = comp_name

                    if remainder_addr and _is_address_text(remainder_addr):
                        address = remainder_addr
                    elif i + 1 < len(blocks_text):
                        next_line = blocks_text[i + 1].strip()
                        nb_match = BOUNDARY_KEYWORDS_RE.search(next_line)
                        if nb_match:
                            next_line = next_line[:nb_match.start()].strip()
                        if _is_address_text(next_line):
                            address = next_line
                else:
                    if _is_address_text(raw_extracted):
                        address = raw_extracted
                    else:
                        if not name and raw_extracted:
                            name = raw_extracted
                        if i + 1 < len(blocks_text):
                            next_line = blocks_text[i + 1].strip()
                            nb_match = BOUNDARY_KEYWORDS_RE.search(next_line)
                            if nb_match:
                                next_line = next_line[:nb_match.start()].strip()
                            if _is_address_text(next_line):
                                address = next_line
                break

    if not address and full_text:
        match = addr_pattern.search(full_text)
        if match:
            raw_extracted = match.group(1).strip()
            b_match = BOUNDARY_KEYWORDS_RE.search(raw_extracted)
            if b_match:
                raw_extracted = raw_extracted[:b_match.start()].strip()
            comp_match = COMPANY_SUFFIX_PATTERN.search(raw_extracted)
            if comp_match:
                if not name:
                    name = comp_match.group(1).strip()
                remainder_addr = comp_match.group(2).strip()
                if remainder_addr and _is_address_text(remainder_addr):
                    address = remainder_addr
            elif _is_address_text(raw_extracted):
                address = raw_extracted

    if not name and full_text:
        match = mfg_pattern.search(full_text)
        if match:
            raw = match.group(1).strip()
            comp_match = COMPANY_SUFFIX_PATTERN.search(raw)
            if comp_match:
                name = comp_match.group(1).strip()
            else:
                name = raw.split(",")[0].strip()

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


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


def _box_metrics(block):
    box = block.get("box") or []
    if len(box) < 4:
        return None
    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    return min(xs), min(ys), max(xs), max(ys), sum(xs) / len(xs), sum(ys) / len(ys)


def _nearby_blocks(blocks, anchor_index, max_vertical_gap=80):
    anchor = _box_metrics(blocks[anchor_index])
    if not anchor:
        return []
    _, top, _, bottom, _, center_y = anchor
    candidates = []
    for index, block in enumerate(blocks):
        if index == anchor_index:
            continue
        metrics = _box_metrics(block)
        if not metrics:
            continue
        _, other_top, _, other_bottom, center_x, other_center_y = metrics
        vertical_gap = max(other_top - bottom, top - other_bottom, 0)
        if vertical_gap <= max_vertical_gap and abs(other_center_y - center_y) <= max_vertical_gap * 2:
            candidates.append((vertical_gap, abs(center_x - anchor[4]), index))
    return [index for _, _, index in sorted(candidates)]


def _reading_order(blocks):
    indexed = list(enumerate(blocks))
    if not any(_box_metrics(block) for _, block in indexed):
        return indexed
    return sorted(
        indexed,
        key=lambda item: (
            _box_metrics(item[1])[1] if _box_metrics(item[1]) else item[0],
            _box_metrics(item[1])[0] if _box_metrics(item[1]) else item[0]
        )
    )


def _label_value_candidates(blocks, label_index, max_distance=180, same_row_only=False):
    label_metrics = _box_metrics(blocks[label_index])
    if not label_metrics:
        return _nearby_blocks(blocks, label_index, max_vertical_gap=max_distance)

    left, top, right, bottom, center_x, center_y = label_metrics
    candidates = []
    for index, block in enumerate(blocks):
        if index == label_index:
            continue
        metrics = _box_metrics(block)
        if not metrics:
            continue
        other_left, other_top, other_right, other_bottom, other_center_x, other_center_y = metrics
        overlap = max(0, min(bottom, other_bottom) - max(top, other_top))
        overlap_ratio = overlap / min(bottom - top, other_bottom - other_top)
        horizontal_gap = max(other_left - right, left - other_right, 0)
        same_row = overlap_ratio >= 0.5 and other_left >= right - max_distance
        below = other_top >= bottom and other_right >= left and other_left <= right
        if same_row:
            candidates.append((0, horizontal_gap, -overlap_ratio, abs(other_center_x - center_x), index))
        elif below and horizontal_gap == 0 and not same_row_only:
            candidates.append((1, other_top - bottom, 0, abs(other_center_x - center_x), index))
    return [index for _, _, _, _, index in sorted(candidates)]


def _normalized_label_text(text):
    return re.sub(r'[^a-z]+', ' ', text.lower()).strip()


FIELD_LABEL_PATTERN = re.compile(
    r'(?i)^(?:model(?:\s+number)?|country(?:\s+(?:of|oi)\s+origin)?|common\s+(?:genaric|generic)\s+name|'
    r'generic\s+name|commodity\s+name|number\s+of\s+units?|month\s+and\s+year|maximum\s+retail\s+price|'
    r'telephone|phone|email(?:\s+address)?|registered\s+address|marketed\s+by|manufactured\s+by|'
    r'packed\s+by|net\s+(?:quantity|weight|content)|batch)\s*[:.-]?$',
)


def _is_field_label(text):
    return bool(FIELD_LABEL_PATTERN.match(re.sub(r'\s+', ' ', text.strip())))


def _extract_mrp(text_blocks, full_text):
    """Extract MRP only when a retail-price label supports the numeric value."""
    label_pattern = re.compile(
        r'(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Ret(?:ail)?\s*P[a-z]{1,4}e?|Ret(?:ail)?\s*P[a-z]{1,4}e?)',
        re.IGNORECASE
    )
    price_pattern = re.compile(r'(?<!\d)(\d{2,}(?:[\.,]\d{1,2}|\s+\d{2})?)(?!\d)')
    value_pattern = re.compile(
        r'\s*[:\.-]?\s*(?:Rs\.?|₹|INR)?\s*\d+(?:[\.,]\d{1,2}|\s+\d{2})?'
        r'(?:\s*\(?\s*(?:incl|inclusive|nclusive)[^()\n\r]{0,35}(?:taxes?|tax)?\s*\)?)?',
        re.IGNORECASE
    )

    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        label_match = label_pattern.search(txt)
        if label_match:
            value_match = value_pattern.match(txt[label_match.end():])
            if value_match and price_pattern.search(value_match.group(0)):
                return _normalize_mrp(txt[label_match.start():label_match.end() + value_match.end()].strip())
            for nearby_index in _label_value_candidates(text_blocks, block_index, same_row_only=True):
                nearby = text_blocks[nearby_index]
                nearby_text = nearby.get("text", "")
                if re.search(r'(?i)\b(?:phone|tel|date|batch|licen[cs]e|ean|upc)\b|\d{3,}[-\s]\d{3,}', nearby_text):
                    continue
                price_match = price_pattern.search(nearby_text)
                if price_match and nearby.get("confidence", 0) >= 0.35:
                    return _normalize_mrp(f"{txt} {price_match.group(1)}")

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
    count_label_pattern = re.compile(
        r'(?i)\b(?:Number\s+of\s+Units?|Units?|Quantity)\b'
    )
    count_pattern = re.compile(r'(?i)\b(\d+\s*N|\d+\s+units?|\d+\s+pcs?)\b')

    def count_value(text, allow_ocr_confusion=False):
        match = count_pattern.search(text)
        if match:
            return re.sub(r'\s+', '', match.group(1)).upper()
        if allow_ocr_confusion and re.fullmatch(r'\s*IN\s*', text, re.IGNORECASE):
            return "1N"
        return None

    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        if count_label_pattern.search(txt):
            direct_count = count_value(txt[count_label_pattern.search(txt).end():])
            if direct_count:
                return direct_count
            for nearby_index in _label_value_candidates(text_blocks, block_index):
                nearby_text = text_blocks[nearby_index].get("text", "").strip()
                nearby_count = count_value(nearby_text, allow_ocr_confusion=True)
                if nearby_count:
                    return nearby_count
        if re.search(r'(?i)\b(?:Net\s*(?:Qty|Quantity|Wt|Weight|Vol|Volume|Content|Contents)|Nett\s*(?:Qty|Quantity|Wt|Weight))\b', txt):
            for nearby_index in _nearby_blocks(text_blocks, block_index):
                nearby_text = text_blocks[nearby_index].get("text", "")
                nearby_promotional = re.search(
                    r'(?i)\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters)\s*(?:\+|plus).*?[=:]\s*'
                    r'(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters))', nearby_text
                )
                if nearby_promotional:
                    return nearby_promotional.group(1).strip()
                nearby_match = generic_qty_pattern.search(nearby_text)
                if nearby_match:
                    return nearby_match.group(1).strip()

        promotional_match = re.search(
            r'(?i)\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters)\s*(?:\+|plus).*?[=:]\s*'
            r'(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters))', txt
        )
        if promotional_match:
            return promotional_match.group(1).strip()

        match = qty_pattern.search(txt)
        if match:
            return match.group(1).strip()

    promotional_match = re.search(
        r'(?i)\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters)\s*(?:\+|plus).*?[=:]\s*'
        r'(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters))', full_text
    )
    if promotional_match:
        return promotional_match.group(1).strip()

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


ALLERGEN_KEYWORDS = ("facility", "may process", "allergen", "equipment", "may contain", "processed in")


def _extract_manufacturer(text_blocks, full_text, raw_blocks=None):
    """
    Extracts manufacturer name and optional address.
    Tolerates 'Registered Address', 'Regd. Office', 'Factory Address', etc.
    Excludes statutory allergen warning disclaimers ("manufactured in a facility...").
    If manufacturerName is missing from filtered_blocks, executes fallback on raw_blocks
    using generic corporate suffix matching (e.g. Ltd, Limited, Pvt Ltd, Inc, Corp).
    """
    mfg_pattern = re.compile(
        r'(?:Manufactured\s+(?:by|in)|Mfg\s+by|Mfd\s+by|Packed\s+by|Pkd\s+by|Marketed\s+by|Mkd\s+by|Manufacturer\s*[:\.-]|Packer\s*[:\.-])\s*[:\.-]?\s*(.+)',
        re.IGNORECASE
    )
    addr_pattern = re.compile(
        r'(?:Registered\s+Address|Regd\.?\s+(?:Address|Office)|Factory\s+Address|Mfg\.\s+Address|Plant\s+Address|Address|Corp\.?\s+Office)\s*[:\.-]?\s*(.+)',
        re.IGNORECASE
    )

    def is_company_candidate(value):
        normalized = re.sub(r'\s+', ' ', value.strip())
        if not normalized:
            return False
        if '@' in normalized or re.search(r'(?i)\b(?:https?://|www(?:\.|\s))|\.[a-z]{2,}\b|\b(?:com|in|org|net)\b', normalized):
            return False
        if re.match(r'(?i)^(?:e[- ]?mail|telephone|phone|contact|customer\s+care|consumer\s+complaints|website)\b', normalized):
            return False
        if re.search(r'(?i)\b(?:use|see|incl|price|batch|mfd|mrp|product|before|belore)\b', normalized):
            return False
        if re.match(r'(?i)^(?:registered|regd|factory|plant|mfg|manufacturing)?\s*address\b', normalized):
            return False
        return True

    blocks_text = [b.get("text", "").strip() for b in text_blocks if b.get("text")]
    if not blocks_text and full_text:
        blocks_text = [line.strip() for line in full_text.splitlines() if line.strip()]

    name = None
    address = None

    section_pattern = re.compile(
        r'(?i)(?:Registered\s+Address|Regd\.?\s+(?:Address|Office)|Factory\s+Address|'
        r'Manufactured\s+by|Mfg\s+by|Mfd\s+by|Packed\s+by|Pkd\s+by|Marketed\s+by|Mkd\s+by|'
        r'Manufacturer|Packer)\s*[:.-]?'
    )
    semantic_boundary = re.compile(
        r'(?i)^(?:Country|Common|Generic|Commodity|Number\s+of|Month|Date|Maximum|MRP|'
        r'Telephone|Phone|Email|Consumer|Customer|Net\s+|Batch|Model|EAN|UPC|Imported)\b'
    )
    ordered_blocks = _reading_order(text_blocks)
    section_results = []

    for position, (block_index, block) in enumerate(ordered_blocks):
        text = block.get("text", "").strip()
        section_match = section_pattern.search(text)
        if not section_match or any(kw in text.lower() for kw in ALLERGEN_KEYWORDS):
            continue

        inline_value = text[section_match.end():].strip()
        section_blocks = []
        for _, following_block in ordered_blocks[position + 1:]:
            following_text = following_block.get("text", "").strip()
            if section_pattern.search(following_text) or semantic_boundary.search(following_text):
                break
            section_blocks.append(following_text)

        candidate_name = None
        candidate_address_lines = []
        if inline_value:
            company_match = COMPANY_SUFFIX_PATTERN.search(inline_value)
            if company_match:
                candidate_name = company_match.group(1).strip()
                remainder = company_match.group(2).strip()
                if remainder:
                    candidate_address_lines.append(remainder)
            elif not _is_address_text(inline_value):
                candidate_name = inline_value

        if not candidate_name:
            for section_line in section_blocks:
                company_match = COMPANY_SUFFIX_PATTERN.search(section_line)
                if company_match:
                    candidate_name = company_match.group(1).strip()
                    remainder = company_match.group(2).strip()
                    if remainder:
                        candidate_address_lines.append(remainder)
                    break

        if candidate_name:
            name_position = next(
                (index for index, value in enumerate(section_blocks) if candidate_name in value),
                -1
            )
            if name_position >= 0:
                candidate_address_lines.extend(section_blocks[name_position + 1:])
            elif inline_value:
                candidate_address_lines.extend(section_blocks)
            candidate_address = " ".join(line for line in candidate_address_lines if line)
            if candidate_address:
                preferred = bool(re.search(
                    r'(?i)(?:Marketed|Manufactured|Mfg|Mfd|Packed|Pkd|Packer)',
                    text[:section_match.end()]
                ))
                section_results.append((preferred, candidate_name, candidate_address))

    if section_results:
        preferred_sections = [result for result in section_results if result[0]]
        _, selected_name, selected_address = (preferred_sections or section_results)[0]
        return selected_name, selected_address

    for i, line in enumerate(blocks_text):
        if any(kw in line.lower() for kw in ALLERGEN_KEYWORDS):
            continue

        match = mfg_pattern.search(line)
        if match:
            extracted = match.group(1).strip()
            if any(kw in extracted.lower() for kw in ALLERGEN_KEYWORDS):
                continue

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
            if any(kw in line.lower() for kw in ALLERGEN_KEYWORDS):
                continue
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

    if not name:
        for index, block in enumerate(text_blocks):
            text = block.get("text", "").strip()
            if not text or any(kw in text.lower() for kw in ALLERGEN_KEYWORDS):
                continue
            if not COMPANY_SUFFIX_PATTERN.search(text):
                continue
            parts = [text]
            for nearby_index in _nearby_blocks(text_blocks, index):
                nearby_text = text_blocks[nearby_index].get("text", "").strip()
                if nearby_text and not any(kw in nearby_text.lower() for kw in ALLERGEN_KEYWORDS):
                    parts.insert(0, nearby_text)
                    combined = " ".join(parts)
                    company_match = COMPANY_SUFFIX_PATTERN.search(combined)
                    if company_match and is_company_candidate(combined):
                        name = company_match.group(1).strip()
                        break
            if name:
                break

    # Fallback to raw blocks (confidence < 0.10) if name is still missing
    if not name and raw_blocks:
        for b in raw_blocks:
            txt = b.get("text", "").strip()
            if not txt or any(kw in txt.lower() for kw in ALLERGEN_KEYWORDS):
                continue
            comp_match = COMPANY_SUFFIX_PATTERN.search(txt)
            if comp_match and is_company_candidate(txt) and len(re.findall(r'[A-Za-z]+', txt)) >= 2:
                name = comp_match.group(1).strip()
                break

    return name, address


def _extract_dates(text_blocks, full_text):
    """
    Extracts month and year of packing / manufacture.
    Tolerates OCR typos like 'Manuiaclure' for 'Manufacture'.
    """
    date_pattern = re.compile(
        r'(?:(?:Month\s*(?:and|&)?\s*Year\s*of|Date\s*of|Month/Year\s*of)\s*)?'
        r'(?:Manui[a-z]+|Manuf[a-z]*|Mfg(?:\s+Date)?|Mfd(?:\s+Date)?|Pack[a-z]*|Pkd|DOM|DOP|Packing|Manufacture)\s*[:\.-]?\s*'
        r'(?:([0-3]?\d)[\/\.\-\s]+)?([0-1]?\d|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[\/\.\-\s]+(20\d{2}|\d{2}(?!\d))',
        re.IGNORECASE
    )

    generic_pattern = re.compile(
        r'\b([0-1]?\d|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)[\/\.\-\s]+(20\d{2}|\d{2}(?!\d))\b',
        re.IGNORECASE
    )

    combined_text = " ".join([b.get("text", "") for b in text_blocks]) or full_text
    combined_text = re.sub(r'(?i)(?<=\d)[|Il](?=\d)', '1', combined_text)
    combined_text = re.sub(r'(?i)(?<=\d)[Oo](?=\d)', '0', combined_text)

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
    Extracts structured consumer care contact details (phone, email, website).
    Rejects header-only fragments (e.g. ', Contact', 'Feedback').
    """
    phone_pattern = re.compile(
        r'\b(?:\+?91[-\s]?)?(?:1800[-\s]?\d{3,4}[-\s]?\d{3,4}|\d{3,5}[-\s]?\d{6,8})\b'
    )
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    website_pattern = re.compile(r'\b(?:www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9-]+\.(?:com|in|org|net))\b', re.IGNORECASE)

    care_pattern = re.compile(
        r'(?:Consumer\s*Care|Customer\s*Care|Care\s*Cell|Contact\s*Us|Feedback|Toll\s*Free)\s*[:\.-]?\s*([^\n\r]+)',
        re.IGNORECASE
    )

    combined_text = " ".join([b.get("text", "") for b in text_blocks]) or full_text
    combined_text = re.sub(r'\s+([@.])\s+', r'\1', combined_text)
    combined_text = re.sub(r'(?i)\s+at\s+', '@', combined_text)
    combined_text = re.sub(r'(?i)\b(?:ac|at)\s+(?=[a-z0-9._%+-]+\s*@)', '', combined_text)
    combined_text = re.sub(r'\s+@', '@', combined_text)
    combined_text = re.sub(r'(?<=@)([A-Za-z0-9._%+-]+)\s+(com|in|org|net)\b', r'\1.\2', combined_text, flags=re.IGNORECASE)

    email_match = email_pattern.search(combined_text)
    phone_match = phone_pattern.search(combined_text)
    web_match = website_pattern.search(combined_text)

    structured_parts = []
    if phone_match:
        structured_parts.append(phone_match.group(0).strip())
    if email_match:
        structured_parts.append(email_match.group(0).strip())
    if web_match:
        web_str = web_match.group(0).strip()
        if not any(web_str in part for part in structured_parts):
            structured_parts.append(web_str)

    if structured_parts:
        return ", ".join(structured_parts)

    return None


def _extract_country_of_origin(text_blocks, full_text):
    """
    Extracts Country of Origin from declarations like 'Product of India',
    'Country of Origin: Germany', 'Made in China', 'Produced in USA', 'OF INDIA'.
    Returns standard country name string or None.
    """
    origin_pattern = re.compile(
        r'(?:Product\s+of|Country\s+(?:of|oi)\s+Origin|Made\s+in|Produced\s+in|Manufactured\s+in)\s*[:\.-]?\s*([A-Za-z\s]{3,30})\b',
        re.IGNORECASE
    )
    country_value_pattern = re.compile(r'^[A-Za-z]{3,30}(?:\s+[A-Za-z]{2,20}){0,2}$')
    invalid_values = {"international", "origin", "country", "common", "generic", "name", "by", "for"}

    def valid_country(value):
        value = re.sub(r'\s+', ' ', value).strip(' .,:;-')
        value = re.split(r'\b(?:by|for|from)\b', value, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        if not country_value_pattern.fullmatch(value):
            return None
        if value.lower() in invalid_values or _is_field_label(value):
            return None
        return value.split()[0].capitalize()

    blocks_text = [b.get("text", "").strip() for b in text_blocks if b.get("text")]
    combined_text = " ".join(blocks_text) or full_text

    for index, block in _reading_order(text_blocks):
        text = block.get("text", "").strip()
        normalized = _normalized_label_text(text)
        if not ("country of origin" in normalized or "country oi origin" in normalized):
            continue
        label_match = re.search(r'(?i)(?:country\s+(?:of|oi)\s+origin)\s*[:.-]?\s*(.*)$', text)
        if label_match and valid_country(label_match.group(1)):
            return valid_country(label_match.group(1))
        for candidate_index in _label_value_candidates(text_blocks, index, same_row_only=True):
            country = valid_country(text_blocks[candidate_index].get("text", ""))
            if country:
                return country

    match = origin_pattern.search(combined_text)
    if match:
        country = valid_country(match.group(1))
        if country:
            return country

    fragmented_origin_pattern = re.compile(
        r'(?i)\b(?:PRODUCT\s+OF|MADE\s+IN|PRODUCED\s+IN|MANUFACTURED\s+IN)\s*([A-Za-z]{3,30})\b'
    )
    fragmented_prefix_pattern = re.compile(
        r'(?i)^(?:product|made|produced|manufactured)$'
    )
    for index, block in _reading_order(text_blocks):
        prefix = block.get("text", "").strip()
        if not fragmented_prefix_pattern.fullmatch(prefix):
            continue
        nearby_indices = _label_value_candidates(text_blocks, index, same_row_only=True)
        nearby_texts = [text_blocks[nearby_index].get("text", "").strip() for nearby_index in nearby_indices]
        for end in range(1, min(len(nearby_texts), 2) + 1):
            candidate_text = " ".join([prefix] + nearby_texts[:end])
            candidate_text = re.sub(r'(?i)\b(of|in)(?=[a-z])', r'\1 ', candidate_text)
            fragmented_match = fragmented_origin_pattern.search(candidate_text)
            if fragmented_match:
                country = valid_country(fragmented_match.group(1))
                if country:
                    return country

    standalone_pattern = re.compile(
        r'\b(?:PRODUCT\s+OF|MADE\s+IN|ORIGIN\s+OF)\s+([A-Za-z]{3,30})\b',
        re.IGNORECASE
    )
    match = standalone_pattern.search(combined_text)
    if match:
        return valid_country(match.group(1))

    in_pattern = re.compile(r'^\s*In\s+([A-Za-z]{3,30})(?:\s+by\b|\s*$)', re.IGNORECASE)
    for block in text_blocks:
        match = in_pattern.search(block.get("text", ""))
        if match:
            country = valid_country(match.group(1))
            if country:
                return country

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

    explicit_label = re.compile(
        r'(?i)(?:Common\s*/?\s*Genaric|Common\s*/?\s*Generic|Generic|Commodity)\s+Name\s*[:.-]?\s*(.*)$'
    )
    for index, block in _reading_order(text_blocks):
        text = block.get("text", "").strip()
        label_match = explicit_label.search(text)
        if label_match:
            value = label_match.group(1).strip()
            if value:
                return value
            for candidate_index in _label_value_candidates(text_blocks, index, same_row_only=True):
                candidate = text_blocks[candidate_index].get("text", "").strip()
                if candidate and not _is_field_label(candidate):
                    return candidate
            for candidate_index in _label_value_candidates(text_blocks, index):
                candidate = text_blocks[candidate_index].get("text", "").strip()
                if candidate and not _is_field_label(candidate):
                    return candidate

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

    # Filter text blocks to only include those with confidence >= 0.10 for field extraction
    filtered_text_blocks = [
        b for b in text_blocks
        if b.get("confidence", 1.0) >= 0.10
    ]
    filtered_full_text = " ".join(
        b.get("text", "") for b in filtered_text_blocks if b.get("text")
    )
    if not filtered_full_text and full_text:
        filtered_full_text = full_text

    # Field Extractions using confidence-filtered text blocks
    mrp = _extract_mrp(filtered_text_blocks, filtered_full_text)
    net_qty = _extract_net_quantity(filtered_text_blocks, filtered_full_text)
    mfg_name, mfg_addr = _extract_manufacturer(filtered_text_blocks, filtered_full_text, raw_blocks=text_blocks)
    month_pkd, year_pkd = _extract_dates(filtered_text_blocks, filtered_full_text)
    care_info = _extract_consumer_care(filtered_text_blocks, filtered_full_text)
    country_of_origin = _extract_country_of_origin(filtered_text_blocks, filtered_full_text)

    known_values = [mrp, net_qty, mfg_name, mfg_addr, care_info]
    product_name = _extract_product_name(filtered_text_blocks, filtered_full_text, known_values)

    # Calculate weighted field-completeness score S
    mrp_pts = 1.0 if mrp is not None else 0.0
    qty_pts = 1.0 if net_qty is not None else 0.0
    mfg_pts = 1.0 if (mfg_name is not None or mfg_addr is not None) else 0.0
    date_pts = 1.0 if (month_pkd is not None or year_pkd is not None) else 0.0

    care_pts = 0.5 if care_info is not None else 0.0
    prod_pts = 0.5 if product_name is not None else 0.0

    completeness_score = mrp_pts + qty_pts + mfg_pts + date_pts + care_pts + prod_pts

    confidences = [b.get("confidence", 1.0) for b in filtered_text_blocks]
    mean_ocr_conf = sum(confidences) / len(confidences) if confidences else 0.0

    if quality_status in ("POOR", "UNREADABLE") or completeness_score < 2.0:
        confidence_flag = "LOW"
    elif quality_status == "ACCEPTABLE" and completeness_score >= 3.5 and mean_ocr_conf >= 0.40:
        confidence_flag = "HIGH"
    else:
        confidence_flag = "MEDIUM"

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
        "countryOfOrigin": country_of_origin,
        "extraction_confidence": confidence_flag
    }



import re
from difflib import SequenceMatcher

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
    r'(?i)\s*(?:For\s+customer|Customer\s*Care|Care\s*Cell|Telephone|Phone|Tel|Email|Contact|'
    r'Net\s*Qty|Net\s*Wt|For\s+Batch|Batch|EAN|UPC|Model|Imported|Month\s*and\s*Year|Month|Date|'
    r'Storage|Store\s+in|Directions|Warning|Caution|Ingredients|Nutrition|Do\s+not\s+accept|USP|MRP|'
    r'FSSAI|Lic\.?\s*No|Licence|License|TM\s*Owner|Trademark\s*Owner|For\s+(?:mfg|manufacturing)\s+unit|Read\s+first\s+character)\b'
)

def _normalized_label_text(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


CANONICAL_LABELS = {
    "PRODUCT_NAME": (
        "common generic name", "generic name", "name of commodity",
        "commodity name", "common genaric name", "common genenc name", "product name"
    ),
    "MANUFACTURER": (
        "manufactured by", "manufactured for", "manufactured in", "mfd by", "mfd for",
        "mfg by", "mfg for", "made by", "produced by", "manufacturer", "mfg unit", "factory address"
    ),
    "MARKETED_BY": (
        "marketed by", "marketed for", "marketed in", "mkd by", "marketer"
    ),
    "PACKER": (
        "packed by", "pkd by", "packer"
    ),
    "IMPORTER": (
        "imported by", "imported in", "importer"
    ),
    "REGISTERED_ADDRESS": (
        "registered address", "regd office", "regd address", "factory address",
        "manufacturing address", "plant address", "corp office", "corporate office",
        "manufacturing unit", "unit address"
    ),
    "NET_QUANTITY": (
        "net quantity", "net qty", "net weight", "net wt", "net volume",
        "net vol", "net content", "net contents", "number of units", "quantity"
    ),
    "MRP": (
        "mrp", "maximum retail price", "max retail price", "retail price",
        "mrp incl of all taxes", "mrp inclusive of all taxes"
    ),
    "UNIT_SALE_PRICE": (
        "unit sale price", "usp"
    ),
    "MANUFACTURE_DATE": (
        "month and year of manufacture", "mfg date", "mfd date",
        "date of manufacture", "dom", "manufacture date", "manufactured date"
    ),
    "PACKING_DATE": (
        "month and year of packing", "packed on", "packing date", "pkd date", "dop"
    ),
    "EXPIRY_DATE": (
        "expiry date", "exp date", "date of expiry", "best before", "use by", "use before"
    ),
    "BATCH_NUMBER": (
        "for batch no", "batch no", "batch number", "batch", "lot no", "lot number"
    ),
    "CONSUMER_CARE": (
        "consumer care", "customer care", "care cell", "consumer complaints",
        "customer complaints", "telephone", "phone", "email", "contact us", "feedback",
        "toll free", "helpline"
    ),
    "COUNTRY_OF_ORIGIN": (
        "country of origin", "country oi origin", "product of", "made in", "origin of"
    ),
    "MODEL_NUMBER": (
        "model number", "model no", "mocel number"
    ),
    "REGULATORY_LICENSE": (
        "lic no", "licence no", "license no", "fssai lic", "fssai", "fssat lic", "fssat", "licence", "license"
    ),
    "STORAGE_INSTRUCTIONS": (
        "storage instructions", "storage conditions", "store in a cool", "storage instruction"
    ),
    "USAGE_DIRECTIONS": (
        "directions for use", "how to use", "stir well before use", "serving suggestion", "directions"
    ),
    "WARNINGS_ADVISORIES": (
        "allergen advice", "allergen information", "warning", "caution",
        "do not accept if seal is tampered"
    ),
    "INGREDIENTS_NUTRITION": (
        "ingredients", "nutritional information", "nutrition facts", "composition"
    ),
    "CODES_AND_BARCODES": (
        "ean", "upc", "barcode"
    ),
    "TRADEMARK_OWNER": (
        "tm owner", "tm owners", "trademark owner", "brand owner"
    ),
    "BATCH_INSTRUCTIONS": (
        "for manufacturing unit address read first character", "for mfg unit address read", "read first character"
    )
}


def _canonical_label(text):
    normalized = _normalized_label_text(text)
    if not normalized:
        return None
    compact = normalized.replace(" ", "")

    # 1. Exact and normalized prefix matching primary
    for concept, variants in CANONICAL_LABELS.items():
        for variant in variants:
            variant_norm = _normalized_label_text(variant)
            variant_compact = variant_norm.replace(" ", "")
            if normalized == variant_norm or normalized.startswith(variant_norm + " ") or compact.startswith(variant_compact):
                return concept

    # 2. Tightly constrained fuzzy matching on long label phrases (>= 8 chars)
    if len(compact) >= 8:
        best = None
        best_score = 0.0
        for concept, variants in CANONICAL_LABELS.items():
            for variant in variants:
                variant_compact = _normalized_label_text(variant).replace(" ", "")
                if len(variant_compact) < 8:
                    continue
                candidate_slice = compact[:len(variant_compact) + 2]
                score = SequenceMatcher(None, candidate_slice, variant_compact).ratio()
                if score > best_score and score >= 0.82:
                    best = concept
                    best_score = score
        if best:
            return best

    return None


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


def _normalize_mrp(raw_mrp: str, context: str = "") -> str:
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

    combined_context = f"{text} {context}".strip()
    has_rupee_symbol = '₹' in combined_context
    prefix = "MRP ₹" if has_rupee_symbol else "MRP Rs."

    has_tax = bool(re.search(r'(?i)\b(?:nclusive|inclusive|incl|tax|taxes)\b', combined_context))

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


def _same_row_right_neighbors(blocks, anchor_index, max_gap=60):
    anchor = _box_metrics(blocks[anchor_index])
    if not anchor:
        return []
    left, top, right, bottom, _, _ = anchor
    candidates = []
    for index, block in enumerate(blocks):
        if index == anchor_index:
            continue
        metrics = _box_metrics(block)
        if not metrics:
            continue
        other_left, other_top, _, other_bottom, _, _ = metrics
        overlap = max(0, min(bottom, other_bottom) - max(top, other_top))
        gap = max(other_left - right, 0)
        if overlap > 0 and other_left >= right and gap <= max_gap:
            candidates.append((gap, other_top, index))
    return [index for _, _, index in sorted(candidates)]


def _row_groups(blocks, tolerance_factor=0.75):
    """Groups OCR blocks into visual rows using vertical overlap and center distance."""
    groups = []
    for index, block in _reading_order(blocks):
        metrics = _box_metrics(block)
        if not metrics:
            groups.append([index])
            continue
        _, top, _, bottom, _, center_y = metrics
        height = max(bottom - top, 1)
        for group in groups:
            row_metrics = [_box_metrics(blocks[item]) for item in group if _box_metrics(blocks[item])]
            if not row_metrics:
                continue
            row_top = min(item[1] for item in row_metrics)
            row_bottom = max(item[3] for item in row_metrics)
            avg_height = sum(item[3] - item[1] for item in row_metrics) / len(row_metrics)
            row_center = sum(item[5] for item in row_metrics) / len(row_metrics)
            overlap = max(0, min(bottom, row_bottom) - max(top, row_top))
            overlap_ratio = overlap / min(height, avg_height)
            if overlap_ratio >= 0.45 and abs(center_y - row_center) <= avg_height * tolerance_factor:
                group.append(index)
                break
        else:
            groups.append([index])
    return groups


def _row_text(blocks, indices):
    sorted_indices = sorted(
        indices,
        key=lambda idx: _box_metrics(blocks[idx])[0] if _box_metrics(blocks[idx]) else idx
    )
    return " ".join(blocks[index].get("text", "").strip() for index in sorted_indices if blocks[index].get("text"))


NON_ENTITY_BOUNDARY_CONCEPTS = {
    "MODEL_NUMBER", "COUNTRY_OF_ORIGIN", "PRODUCT_NAME", "NET_QUANTITY",
    "MRP", "MANUFACTURE_DATE", "PACKING_DATE", "CONSUMER_CARE", "BATCH_NUMBER",
    "STORAGE_INSTRUCTIONS", "USAGE_DIRECTIONS", "WARNINGS_ADVISORIES",
    "INGREDIENTS_NUTRITION", "EXPIRY_DATE", "UNIT_SALE_PRICE", "CODES_AND_BARCODES",
    "REGULATORY_LICENSE", "TRADEMARK_OWNER", "BATCH_INSTRUCTIONS"
}

NON_ENTITY_SECTION_HEADER_RE = re.compile(
    r'(?i)^\s*(?:'
    # Commercial & traceability
    r'for\s+batch(?:\s+no\.?)?|batch(?:\s+no\.?|\s+number)?|lot(?:\s+no\.?|\s+number)?|'
    r'mrp\b|maximum\s+retail\s+price|max\.?\s*retail|retail\s+price|'
    r'month\s+(?:and|&)?\s*year|mfg\.?\s*(?:date)?|mfd\.?\s*(?:date)?|date\s+of|dom\b|dop\b|'
    r'expiry(?:\s+date)?|exp\.?\s*(?:date)?|best\s+before|use\s+by|use\s+before|'
    r'net\s*(?:qty|quantity|wt|weight|vol|volume|content|contents)|number\s+of\s+units?|'
    r'unit\s+sale\s+price|usp\b|'
    # Storage & Usage & Advisories
    r'storage\s+instructions?|store\s+in\s+a\s+cool|storage\b|'
    r'directions\s+for\s+use|how\s+to\s+use|serving\s+suggestion|stir\s+well|directions\b|'
    r'allergen(?:\s+advice|\s+warning|\s+information)?|warning\b|caution\b|do\s+not\s+accept\s+if|'
    # Ingredients & Nutrition
    r'ingredients\b|nutritional\s+information|nutrition\s+facts|composition\b|'
    # Contact & Origin & Identifiers & Regulatory
    r'consumer\s*care|customer\s*care|care\s*cell|customer\s*complaints?|contact\s*us|feedback\b|'
    r'telephone\b|phone\b|email\b|toll\s*free|helpline\b|'
    r'country\s+(?:of|oi)\s+origin|product\s+of|made\s+in\b|'
    r'model\s+(?:number|no\.?)|mocel\s+(?:number|no\.?)|ean\b|upc\b|barcode\b|'
    r'common\s+(?:generic|genaric|genenc)\s+name|generic\s+name|commodity\s+name|name\s+of\s+commodity|'
    r'fssai\b|fssat\b|lic\.?\s*no\.?|licen[cs]e(?:\s+no\.?)?|'
    r'tm\s+owners?|trademark\s+owner|brand\s+owner|'
    r'for\s+(?:mfg|manufacturing)\s+unit(?:\s+address)?|read\s+first\s+character'
    r')\b'
)


def _looks_like_country_label(text):
    normalized = _normalized_label_text(text)
    return bool(re.search(r'\bcoun[a-z]*\s+(?:of|oi|o)?\s*ori[a-z]*\b', normalized))


def _looks_like_section_boundary(text):
    if not text:
        return False
    if NON_ENTITY_SECTION_HEADER_RE.search(text):
        return True
    canonical = _canonical_label(text)
    if canonical and canonical in NON_ENTITY_BOUNDARY_CONCEPTS:
        return True
    return False


def _is_boundary_at(ordered_blocks, position):
    text = ordered_blocks[position][1].get("text", "").strip()
    if _looks_like_section_boundary(text):
        return True

    normalized = _normalized_label_text(text)
    for _, following_block in ordered_blocks[position + 1:position + 3]:
        following_text = following_block.get("text", "").strip()
        combined = f"{normalized} {_normalized_label_text(following_text)}"
        if _looks_like_section_boundary(combined):
            return True
    return False


def _semantic_boundary_indices(ordered_blocks):
    boundary_indices = set()
    blocks = [block for _, block in ordered_blocks]
    for row in _row_groups(blocks):
        row_text = _row_text(blocks, row)
        canonical = _canonical_label(row_text)
        is_row_boundary = (
            canonical in NON_ENTITY_BOUNDARY_CONCEPTS
            or _looks_like_section_boundary(row_text)
            or any(_looks_like_section_boundary(blocks[index].get("text", "")) for index in row)
        )
        if not is_row_boundary:
            continue
        boundary_positions = [_box_metrics(blocks[index]) for index in row if _box_metrics(blocks[index])]
        if not boundary_positions:
            continue
        band_top = min(metrics[1] for metrics in boundary_positions)
        band_bottom = max(metrics[3] for metrics in boundary_positions)
        band_height = max(band_bottom - band_top, 1)
        for candidate_position, candidate_block in enumerate(blocks):
            metrics = _box_metrics(candidate_block)
            if not metrics:
                continue
            candidate_top, candidate_bottom = metrics[1], metrics[3]
            overlap = max(0, min(band_bottom, candidate_bottom) - max(band_top, candidate_top))
            if overlap > 0 or abs((candidate_top + candidate_bottom) / 2 - (band_top + band_bottom) / 2) <= band_height * 0.75:
                boundary_indices.add(candidate_position)

    return boundary_indices


def _is_plausible_address_block(previous_block, candidate_block):
    previous_box = previous_block.get("box") or []
    candidate_box = candidate_block.get("box") or []
    if len(previous_box) < 2 or len(candidate_box) < 2:
        return True

    def orientation(box):
        start, end = box[0], box[1]
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        return dy / max(dx, 1)

    candidate_slope = orientation(candidate_box)
    previous_slope = orientation(previous_box)
    return candidate_slope <= 0.12 or abs(candidate_slope - previous_slope) <= 0.04


FIELD_LABEL_PATTERN = re.compile(
    r'(?i)^\s*(?:'
    r'model(?:\s+number|\s+no\.?)?|mocel(?:\s+number|\s+no\.?)?|'
    r'country(?:\s+(?:of|oi)\s+origin)?|'
    r'common\s+(?:genaric|generic|genenc)\s+name|generic\s+name|commodity\s+name|name\s+of\s+commodity|'
    r'number\s+of\s+units?|month\s+(?:and|&)?\s*year|maximum\s+retail\s+price|max\.?\s*retail\s*price|mrp|'
    r'telephone|phone|email(?:\s+address)?|registered\s+address|regd\.?\s*office|'
    r'marketed\s+by|manufactured\s+by|mfg\s+by|mfd\s+by|packed\s+by|pkd\s+by|imported\s+by|'
    r'net\s+(?:quantity|weight|vol|volume|content|contents|qty|wt)|'
    r'for\s+batch(?:\s+no\.?)?|batch(?:\s+number|\s+no\.?)?|lot(?:\s+no\.?)?|'
    r'storage\s+instructions?|directions\s+for\s+use|allergen\s+advice|ingredients|best\s+before|expiry\s+date|'
    r'fssai(?:\s+lic)?|lic\.?\s*no\.?|licen[cs]e|tm\s+owners?|trademark\s+owner'
    r')\s*[:.-]?\s*$',
)


def _is_field_label(text):
    if not text:
        return False
    cleaned = re.sub(r'\s+', ' ', text.strip())
    if FIELD_LABEL_PATTERN.match(cleaned):
        return True
    canonical = _canonical_label(cleaned)
    if canonical:
        norm = _normalized_label_text(cleaned)
        for variant in CANONICAL_LABELS.get(canonical, ()):
            if norm == _normalized_label_text(variant):
                return True
    return False


def _extract_mrp(text_blocks, full_text):
    """
    Extract MRP only when a retail-price label supports the numeric value.
    Handles glued stamp formats where price and date are concatenated (e.g. '175.0007/25')
    only when supported by explicit MRP context.
    """
    label_pattern = re.compile(
        r'(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Ret(?:ail)?\s*P[a-z]{0,4}e?|Ret(?:ail)?\s*P[a-z]{0,4}e?)',
        re.IGNORECASE
    )
    price_pattern = re.compile(r'(?<!\d)(\d{2,}(?:[\.,]\d{1,2}|\s+\d{2})?)(?!\d|/\d)')
    glued_price_pattern = re.compile(r'(?<!\d)(\d{2,}\.\d{2})(?=\d{2}/\d{2,4})')
    value_pattern = re.compile(
        r'\s*[:\.-]?\s*(?:Rs\.?|₹|INR)?\s*\d+(?:[\.,]\d{1,2}|\s+\d{2})?'
        r'(?:\s*\(?\s*(?:incl|inclusive|nclusive)[^()\n\r]{0,35}(?:taxes?|tax)?\s*\)?)?',
        re.IGNORECASE
    )

    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        label_match = label_pattern.search(txt)
        if label_match:
            after_label = txt[label_match.end():]
            value_match = value_pattern.match(after_label)
            if value_match and price_pattern.search(value_match.group(0)):
                return _normalize_mrp(txt[label_match.start():label_match.end() + value_match.end()].strip(), context=txt)
            glued_match = glued_price_pattern.search(after_label)
            if glued_match:
                remainder_after_price = after_label[glued_match.end():]
                return _normalize_mrp(f"{label_match.group(0)} {glued_match.group(1)} {remainder_after_price}", context=txt)
            for nearby_index in _label_value_candidates(text_blocks, block_index, same_row_only=True):
                nearby = text_blocks[nearby_index]
                nearby_text = nearby.get("text", "")
                if re.search(r'(?i)\b(?:phone|tel|date|batch|licen[cs]e|ean|upc)\b|\d{3,}[-\s]\d{3,}', nearby_text):
                    continue
                price_match = price_pattern.search(nearby_text)
                if price_match and nearby.get("confidence", 0) >= 0.35:
                    return _normalize_mrp(f"{txt} {price_match.group(1)}", context=f"{txt} {nearby_text}")
                glued_match = glued_price_pattern.search(nearby_text)
                if glued_match and nearby.get("confidence", 0) >= 0.35:
                    remainder = nearby_text[glued_match.end():]
                    return _normalize_mrp(f"{txt} {glued_match.group(1)} {remainder}", context=f"{txt} {nearby_text}")

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
        return None

    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        if count_label_pattern.search(txt):
            direct_count = count_value(txt[count_label_pattern.search(txt).end():])
            if direct_count:
                return direct_count
            for nearby_index in _label_value_candidates(text_blocks, block_index):
                nearby_text = text_blocks[nearby_index].get("text", "").strip()
                nearby_count = count_value(nearby_text)
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
TM_KEYWORDS = ("tm owners", "tm owner", "trademark owner", "trademark owners", "brand owner")


def _extract_manufacturer(text_blocks, full_text, raw_blocks=None):
    """
    Extracts manufacturer name and optional address with semantic role ranking:
    1. Explicit Manufacturer: 'Manufactured by', 'Mfg by', 'Mfd by', 'Made in ... by', 'Factory Address'
    2. Explicit Packer / Regd Office: 'Packed by', 'Pkd by', 'Imported by', 'Regd Office', 'Manufactured for'
    3. Marketer: 'Marketed by', 'Mkd by'
    4. Corporate suffix fallback (Ltd, Pvt Ltd, etc.)

    Strictly excludes:
    - Trademark owners ('TM Owners...')
    - Allergen warnings ('Manufactured in a facility...')
    - Customer care and regulatory license sections
    """
    mfg_pattern = re.compile(
        r'(?:Manufactured\s+(?:by|for|in)|Mfg[.\s]*(?:by|for)|Mfd[.\s]*(?:by|for)|Packed[.\s]*by|Pkd[.\s]*by|Marketed[.\s]*by|Mkd[.\s]*by|Manufacturer\s*[:\.-]|Packer\s*[:\.-])\s*[:\.-]?\s*(.+)',
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
        if any(tm_kw in normalized.lower() for tm_kw in TM_KEYWORDS):
            return False
        if '@' in normalized:
            return False
        if re.search(r'(?i)\b(?:https?://|www\.)', normalized):
            return False
        if re.search(r'(?i)\b[a-z0-9-]+\.(?:com|org|net|gov|edu|io|co|ai)\b', normalized):
            return False
        if re.match(r'(?i)^(?:e[- ]?mail|telephone|phone|contact|customer\s+care|consumer\s+complaints|website)\b', normalized):
            return False
        if re.search(r'(?i)\b(?:use|see|incl|price|batch|mfd|mrp|product|before|belore)\b', normalized):
            return False
        if re.match(r'(?i)^(?:registered|regd|factory|plant|mfg|manufacturing)?\s*address\b', normalized):
            return False
        return True

    def role_score(header_text):
        h = header_text.lower()
        if any(mfg_term in h for mfg_term in ["manufactured by", "mfg by", "mfd by", "mfg. by", "mfd. by", "made in", "made by", "produced by", "manufacturer", "factory address", "manufacturing unit"]):
            return 4
        if any(mkt_term in h for mkt_term in ["marketed by", "marketed for", "mkd by", "marketer", "packed by", "pkd by", "imported by", "packer"]):
            return 3
        if any(regd_term in h for regd_term in ["regd office", "regd. office", "registered address", "registered office", "manufactured for", "mfd for", "mfd. for"]):
            return 2
        return 0

    blocks_text = [b.get("text", "").strip() for b in text_blocks if b.get("text")]
    if not blocks_text and full_text:
        blocks_text = [line.strip() for line in full_text.splitlines() if line.strip()]

    name = None
    address = None

    section_pattern = re.compile(
        r'(?i)(?:Registered\s+Address|Regd\.?\s*(?:Address|Office)|Factory\s+Address|'
        r'Manufactured\s+(?:by|for|in)|Mfg[.\s]*(?:by|for)|Mfd[.\s]*(?:by|for)|Packed[.\s]*by|Pkd[.\s]*by|Marketed[.\s]*by|Mkd[.\s]*by|'
        r'Made\s+in\s+[A-Za-z\s]+by|Manufacturer|Packer)\s*[:./-]?'
    )
    ordered_blocks = _reading_order(text_blocks)
    semantic_boundary_indices = _semantic_boundary_indices(ordered_blocks)
    section_results = []

    for position, (block_index, block) in enumerate(ordered_blocks):
        text = block.get("text", "").strip()
        if any(tm_kw in text.lower() for tm_kw in TM_KEYWORDS):
            continue
        section_match = section_pattern.search(text)
        if not section_match or any(kw in text.lower() for kw in ALLERGEN_KEYWORDS):
            continue

        matched_header = text[:section_match.end()]
        score = role_score(matched_header)

        inline_value = text[section_match.end():].strip()
        # Clean inline prefix leftovers like '/Regd.office' or ': '
        inline_value = re.sub(r'^(?:[/:.-]|\b(?:regd|mfd|mfg)[.\s]*(?:office|address|by|for)[/:.-]?\s*)+', '', inline_value, flags=re.IGNORECASE).strip()

        section_blocks = []
        previous_block = block
        entity_found = False
        if inline_value and COMPANY_SUFFIX_PATTERN.search(inline_value) and is_company_candidate(inline_value):
            entity_found = True

        for following_position, (_, following_block) in enumerate(ordered_blocks[position + 1:], position + 1):
            following_text = following_block.get("text", "").strip()
            if any(tm_kw in following_text.lower() for tm_kw in TM_KEYWORDS):
                break
            if following_position in semantic_boundary_indices:
                break
            if section_pattern.search(following_text) or _is_boundary_at(ordered_blocks, following_position):
                break
            if _looks_like_section_boundary(following_text):
                break
            if entity_found and COMPANY_SUFFIX_PATTERN.search(following_text) and is_company_candidate(following_text):
                break
            if COMPANY_SUFFIX_PATTERN.search(following_text) and is_company_candidate(following_text):
                entity_found = True
            if _is_plausible_address_block(previous_block, following_block):
                section_blocks.append(following_text)
                previous_block = following_block

        candidate_name = None
        candidate_address_lines = []
        continuation_completed = False
        if inline_value:
            company_match = COMPANY_SUFFIX_PATTERN.search(inline_value)
            if company_match and is_company_candidate(inline_value):
                candidate_name = company_match.group(1).strip()
                remainder = company_match.group(2).strip()
                if remainder:
                    candidate_address_lines.append(remainder)
            elif not _is_address_text(inline_value):
                continuation = inline_value
                consumed = 0
                for section_line in section_blocks:
                    continuation = f"{continuation} {section_line}".strip()
                    consumed += 1
                    company_match = COMPANY_SUFFIX_PATTERN.search(continuation)
                    if company_match and is_company_candidate(continuation):
                        candidate_name = company_match.group(1).strip()
                        remainder = company_match.group(2).strip()
                        if remainder:
                            candidate_address_lines.append(remainder)
                        candidate_address_lines.extend(section_blocks[consumed:])
                        continuation_completed = True
                        break
                if not candidate_name and is_company_candidate(inline_value):
                    candidate_name = inline_value

        if not candidate_name:
            for section_line in section_blocks:
                company_match = COMPANY_SUFFIX_PATTERN.search(section_line)
                if company_match and is_company_candidate(section_line):
                    candidate_name = company_match.group(1).strip()
                    remainder = company_match.group(2).strip()
                    if remainder:
                        candidate_address_lines.append(remainder)
                    break

        if candidate_name:
            candidate_name = re.sub(r'^[^\w\s]+', '', candidate_name).strip()
            candidate_name = re.sub(r'^\d+\s+(?=[A-Za-z])', '', candidate_name).strip()
            name_position = next(
                (index for index, value in enumerate(section_blocks) if candidate_name in value),
                -1
            )
            if name_position >= 0:
                candidate_address_lines.extend(section_blocks[name_position + 1:])
            elif inline_value and not continuation_completed and not any(candidate_name == line for line in section_blocks):
                candidate_address_lines.extend(section_blocks)
            while candidate_address_lines and re.search(r'(?i)\b(?:fssai|fssat|lic|licence|license)\b', candidate_address_lines[-1].strip()):
                candidate_address_lines.pop()
            candidate_address = " ".join(line for line in candidate_address_lines if line)
            if candidate_address:
                section_results.append((score, candidate_name, candidate_address))
            else:
                section_results.append((score, candidate_name, None))

    def clean_strings(n, a):
        if n:
            n = re.sub(r'^[^\w\s]+', '', n).strip()
            n = re.sub(r'^\d+\s+(?=[A-Za-z])', '', n).strip()
            n = n.strip(' ,;:-')
            if not n:
                n = None
        if a:
            a = a.strip(' ,;:-')
            if not a:
                a = None
        return n, a

    if section_results:
        # Sort by role score descending (4: Explicit Mfg > 3: Marketer/Packer > 2: Regd)
        section_results.sort(key=lambda item: item[0], reverse=True)
        _, selected_name, selected_address = section_results[0]
        if not selected_address:
            # Check if an address was found for the same company or a registered address in another section
            for _, cand_name, cand_addr in section_results:
                if cand_addr and (cand_name.lower() in selected_name.lower() or selected_name.lower() in cand_name.lower()):
                    selected_address = cand_addr
                    break
        return clean_strings(selected_name, selected_address)

    for i, line in enumerate(blocks_text):
        if any(kw in line.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in line.lower() for tm in TM_KEYWORDS):
            continue

        match = mfg_pattern.search(line)
        if match:
            extracted = match.group(1).strip()
            if any(kw in extracted.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in extracted.lower() for tm in TM_KEYWORDS):
                continue

            b_match = BOUNDARY_KEYWORDS_RE.search(extracted)
            if b_match:
                extracted = extracted[:b_match.start()].strip()

            comp_match = COMPANY_SUFFIX_PATTERN.search(extracted)
            if comp_match and is_company_candidate(extracted):
                name = comp_match.group(1).strip()
                remainder = comp_match.group(2).strip()
                if remainder and _is_address_text(remainder):
                    address = remainder
            elif extracted and is_company_candidate(extracted):
                name = extracted
            elif i + 1 < len(blocks_text):
                name = blocks_text[i + 1].strip()

            if name and i + 1 < len(blocks_text):
                next_block = blocks_text[i + 1].strip()
                if (len(name) < 5 or not name.endswith(("Ltd", "Limited", "Inc", "LLP"))) and not _is_address_text(next_block):
                    combined = f"{name} {next_block}".strip()
                    comp_match = COMPANY_SUFFIX_PATTERN.search(combined)
                    if comp_match and is_company_candidate(combined):
                        name = comp_match.group(1).strip()
                        rem = comp_match.group(2).strip()
                        if rem and _is_address_text(rem):
                            address = rem
                    elif any(w in next_block.lower() for w in ["international", "services", "india", "private", "limited", "technologies", "solutions"]):
                        name = combined

            if i + 1 < len(blocks_text) and not address:
                candidate = blocks_text[i + 1].strip()
                if candidate != name and _is_address_text(candidate) and not any(tm in candidate.lower() for tm in TM_KEYWORDS):
                    address = candidate
            break

    if not address or not name:
        for i, line in enumerate(blocks_text):
            if any(kw in line.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in line.lower() for tm in TM_KEYWORDS):
                continue
            match = addr_pattern.search(line)
            if match:
                raw_extracted = match.group(1).strip()
                b_match = BOUNDARY_KEYWORDS_RE.search(raw_extracted)
                if b_match:
                    raw_extracted = raw_extracted[:b_match.start()].strip()

                comp_match = COMPANY_SUFFIX_PATTERN.search(raw_extracted)
                if comp_match and is_company_candidate(raw_extracted):
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
                        if not name and raw_extracted and is_company_candidate(raw_extracted):
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
            if not text or any(kw in text.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in text.lower() for tm in TM_KEYWORDS):
                continue
            if not COMPANY_SUFFIX_PATTERN.search(text) or not is_company_candidate(text):
                continue
            parts = [text]
            for nearby_index in _nearby_blocks(text_blocks, index):
                nearby_text = text_blocks[nearby_index].get("text", "").strip()
                if nearby_text and not any(kw in nearby_text.lower() for kw in ALLERGEN_KEYWORDS) and not any(tm in nearby_text.lower() for tm in TM_KEYWORDS):
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
            if not txt or any(kw in txt.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in txt.lower() for tm in TM_KEYWORDS):
                continue
            comp_match = COMPANY_SUFFIX_PATTERN.search(txt)
            if comp_match and is_company_candidate(txt) and len(re.findall(r'[A-Za-z]+', txt)) >= 2:
                name = comp_match.group(1).strip()
                break

    return clean_strings(name, address)


def _extract_dates(text_blocks, full_text):
    """
    Extracts month and year of packing / manufacture ONLY when accompanied by explicit
    manufacturing/packing evidence (e.g. 'Month and Year of Manufacture', 'Mfg Date', 'DOM', 'Pkd').

    Strictly excludes dates associated with expiry ('Use By', 'Expiry', 'Best Before')
    or standalone batch numbers/codes.
    """
    month_pattern = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:us|ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'

    # Explicit manufacturing/packing date pattern
    date_pattern = re.compile(
        r'(?:(?:Month\s*(?:and|&)?\s*Year\s*of|Date\s*of|Month/Year\s*of)\s*)?'
        r'(?:Manu[a-z]+|Manuf[a-z]*|Mfg(?:\s+Date)?|Mfd(?:\s+Date)?|Pack[a-z]*|Pkd|DOM|DOP|Packing|Manufacture)\s*[:\.-]?\s*'
        rf'(?:([0-3]?\d)[/\.\-\s]+)?({month_pattern}|[0-1]?\d)[/\.\-\s]+(20\d{{2}}|\d{{2}}(?!\d))',
        re.IGNORECASE
    )

    expiry_or_batch_re = re.compile(
        r'(?i)\b(?:exp|expiry|best\s+before|use\s+by|use\s+before|batch|lot|b\.?\s*no)\b'
    )

    # 1. Search in blocks with explicit manufacturing/packing labels
    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        if not txt:
            continue

        # Check for explicit date pattern in block
        match = date_pattern.search(txt)
        if match:
            # Check if this block contains expiry or batch terms
            prefix = txt[:match.start()]
            if expiry_or_batch_re.search(prefix):
                continue

            groups = match.groups()
            m_raw = groups[1]
            y_raw = groups[2]

            m_str = str(m_raw).strip().lower()
            if m_str in MONTH_MAP:
                month = MONTH_MAP[m_str]
            elif len(m_str) >= 3 and any(month_name.startswith(m_str) for month_name in MONTH_MAP):
                month = MONTH_MAP[next(month_name for month_name in MONTH_MAP if month_name.startswith(m_str))]
            elif m_str.isdigit():
                month = f"{int(m_str):02d}"
            else:
                month = m_str.upper()

            y_str = str(y_raw).strip()
            year = f"20{y_str}" if len(y_str) == 2 else y_str

            return month, year

        # Check if block has manufacturing/packing label and adjacent block has date
        if re.search(r'(?i)\b(?:Month\s*(?:and|&)?\s*Year\s*of\s*(?:Manui?a?cl?ure|Manufacture|Packing)|Date\s*of\s*(?:Manufacture|Packing)|Mfg(?:\s+Date)?|Mfd(?:\s+Date)?|DOM|DOP|Pkd(?:\s+Date)?)\b', txt):
            if expiry_or_batch_re.search(txt):
                continue
            for nearby_index in _label_value_candidates(text_blocks, block_index, max_distance=150):
                nearby_txt = text_blocks[nearby_index].get("text", "").strip()
                if expiry_or_batch_re.search(nearby_txt):
                    continue
                date_match = re.search(
                    rf'\b(?:([0-3]?\d)[/\.\-\s]+)?({month_pattern}|[0-1]?\d)[/\.\-\s]+(20\d{{2}}|\d{{2}}(?!\d))\b',
                    nearby_txt,
                    re.IGNORECASE
                )
                if date_match:
                    m_raw = date_match.group(2)
                    y_raw = date_match.group(3)
                    m_str = str(m_raw).strip().lower()
                    if m_str in MONTH_MAP:
                        month = MONTH_MAP[m_str]
                    elif len(m_str) >= 3 and any(month_name.startswith(m_str) for month_name in MONTH_MAP):
                        month = MONTH_MAP[next(month_name for month_name in MONTH_MAP if month_name.startswith(m_str))]
                    elif m_str.isdigit():
                        month = f"{int(m_str):02d}"
                    else:
                        continue
                    y_str = str(y_raw).strip()
                    year = f"20{y_str}" if len(y_str) == 2 else y_str
                    return month, year

    # 2. Check full text for explicit pattern
    combined_text = " ".join([b.get("text", "") for b in text_blocks]) or full_text
    combined_text = re.sub(r'(?i)(?<=\d)[|Il](?=\d)', '1', combined_text)
    combined_text = re.sub(r'(?i)(?<=\d)[Oo](?=\d)', '0', combined_text)

    match = date_pattern.search(combined_text)
    if match:
        prefix = combined_text[max(0, match.start() - 30):match.start()]
        if not expiry_or_batch_re.search(prefix):
            groups = match.groups()
            m_raw = groups[1]
            y_raw = groups[2]

            m_str = str(m_raw).strip().lower()
            if m_str in MONTH_MAP:
                month = MONTH_MAP[m_str]
            elif len(m_str) >= 3 and any(month_name.startswith(m_str) for month_name in MONTH_MAP):
                month = MONTH_MAP[next(month_name for month_name in MONTH_MAP if month_name.startswith(m_str))]
            elif m_str.isdigit():
                month = f"{int(m_str):02d}"
            else:
                month = m_str.upper()

            y_str = str(y_raw).strip()
            year = f"20{y_str}" if len(y_str) == 2 else y_str

            return month, year

    # No unassociated/generic date fallback: ambiguous date -> None
    return None, None


def _extract_consumer_care(text_blocks, full_text):
    """
    Extracts structured consumer care contact details (phone, email, website).
    Excludes regulatory license numbers (FSSAI, Lic No, EAN, barcode, pin codes).
    """
    tollfree_pattern = re.compile(r'\b1800[-\s]?\d{3,4}[-\s]?\d{3,4}\b')
    mobile_pattern = re.compile(r'\b(?:\+?91[-\s]?)?[6-9]\d{9}\b')
    landline_pattern = re.compile(r'\b(?:0\d{2,4}|\+?91[-\s]?\d{2,4})[-\s]\d{6,8}\b|\b\d{3,5}[-\s]\d{6,8}\b')
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    website_pattern = re.compile(r'\b(?:www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9-]+\.(?:com|in|org|net))\b', re.IGNORECASE)

    regulatory_prefix_re = re.compile(r'(?i)\b(?:lic|lic\.?\s*no|licence|license|fssai|fssat|ean|upc|barcode|pin|pincode|model|batch|lot|date|mrp)\b')

    def is_valid_phone(phone_str, context_text):
        digits_only = re.sub(r'\D', '', phone_str)
        if len(digits_only) < 7 or len(digits_only) > 13:
            return False
        # Reject 12-14 digit FSSAI/barcode strings
        if len(digits_only) >= 12 and not phone_str.startswith("+"):
            return False
        # Reject if context indicates regulatory license
        if regulatory_prefix_re.search(context_text):
            return False
        return True

    blocks_text = [b.get("text", "").strip() for b in text_blocks if b.get("text")]
    combined_text = " ".join(blocks_text) or full_text
    combined_text = re.sub(r'\s+([@.])\s+', r'\1', combined_text)
    combined_text = re.sub(r'(?i)\s+at\s+', '@', combined_text)
    combined_text = re.sub(r'(?i)\b(?:ac|at)\s+(?=[a-z0-9._%+-]+\s*@)', '', combined_text)
    combined_text = re.sub(r'\s+@', '@', combined_text)
    combined_text = re.sub(r'(?<=@)([A-Za-z0-9._%+-]+)\s+(com|in|org|net)\b', r'\1.\2', combined_text, flags=re.IGNORECASE)

    email_match = email_pattern.search(combined_text)
    web_match = website_pattern.search(combined_text)

    # Phone search with strict contextual filtering
    found_phone = None
    for block in text_blocks:
        txt = block.get("text", "").strip()
        if not txt:
            continue

        tf_match = tollfree_pattern.search(txt)
        if tf_match:
            found_phone = tf_match.group(0).strip()
            break

        # Check for phone preceded by telephone/phone/contact label
        care_label_match = re.search(r'(?i)\b(?:telephone|phone|tel|customer\s*care|consumer\s*care|care\s*cell|helpline|call)\b\s*[:.-]?\s*([+\d\s-]{7,15})', txt)
        if care_label_match:
            cand = care_label_match.group(1).strip()
            if is_valid_phone(cand, txt):
                found_phone = cand
                break

        mob_match = mobile_pattern.search(txt)
        if mob_match and not regulatory_prefix_re.search(txt):
            cand = mob_match.group(0).strip()
            if is_valid_phone(cand, txt):
                found_phone = cand
                break

        ll_match = landline_pattern.search(txt)
        if ll_match and not regulatory_prefix_re.search(txt):
            cand = ll_match.group(0).strip()
            if is_valid_phone(cand, txt):
                found_phone = cand
                break

    if not found_phone:
        # Check combined text for tollfree or explicit telephone label
        tf_match = tollfree_pattern.search(combined_text)
        if tf_match:
            found_phone = tf_match.group(0).strip()
        else:
            care_label_match = re.search(r'(?i)\b(?:telephone|phone|tel|helpline)\b\s*[:.-]?\s*([+\d\s-]{7,15})', combined_text)
            if care_label_match:
                cand = care_label_match.group(1).strip()
                if is_valid_phone(cand, combined_text):
                    found_phone = cand

    structured_parts = []
    if found_phone:
        structured_parts.append(found_phone)
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
    known_countries = {
        "india", "germany", "china", "japan", "korea", "nepal", "bhutan", "bangladesh",
        "pakistan", "thailand", "vietnam", "indonesia", "malaysia", "singapore", "usa",
        "canada", "australia", "france", "italy", "spain", "united kingdom", "united states",
    }

    def valid_country(value):
        value = re.sub(r'\s+', ' ', value).strip(' .,:;-')
        value = re.split(r'\b(?:by|for|from)\b', value, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        if not country_value_pattern.fullmatch(value):
            return None
        if value.lower() in invalid_values or _is_field_label(value):
            return None
        value_lower = value.lower()
        if value_lower in known_countries:
            return value.split()[0].capitalize()
        closest = max(known_countries, key=lambda country: SequenceMatcher(None, value_lower, country).ratio())
        close_enough = SequenceMatcher(None, value_lower, closest).ratio() >= 0.65
        prefix_supported = len(value_lower) >= 4 and value_lower[:3] == closest[:3] and len(value_lower) <= len(closest) + 2
        if close_enough and prefix_supported:
            return closest.split()[0].capitalize()
        return None

    blocks_text = [b.get("text", "").strip() for b in text_blocks if b.get("text")]
    combined_text = " ".join(blocks_text) or full_text
    has_geometry = any(_box_metrics(block) for block in text_blocks)
    inline_origin = any(
        re.search(r'(?i)\b(?:product\s+of|made\s+in|produced\s+in|manufactured\s+in)\b', text)
        for text in blocks_text
    )

    for index, block in _reading_order(text_blocks):
        text = block.get("text", "").strip()
        normalized = _normalized_label_text(text)
        if not ("country of origin" in normalized or "country oi origin" in normalized or _looks_like_country_label(text)):
            continue
        label_match = re.search(r'(?i)(?:country\s+(?:of|oi)\s+origin)\s*[:.-]?\s*(.*)$', text)
        if label_match and valid_country(label_match.group(1)):
            return valid_country(label_match.group(1))
        for candidate_index in _label_value_candidates(text_blocks, index, same_row_only=True):
            country = valid_country(text_blocks[candidate_index].get("text", ""))
            if country:
                return country

    match = origin_pattern.search(combined_text) if (not has_geometry or inline_origin) else None
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

    for index, block in enumerate(text_blocks):
        prefix = block.get("text", "").strip()
        if not fragmented_prefix_pattern.fullmatch(prefix):
            continue
        for candidate_index in _same_row_right_neighbors(text_blocks, index):
            candidate = text_blocks[candidate_index].get("text", "").strip()
            candidate_text = re.sub(
                r'(?i)\b(product|made|produced|manufactured)(of|in)(?=[a-z])',
                r'\1 \2 ',
                f"{prefix} {candidate}",
            )
            fragmented_match = fragmented_origin_pattern.search(candidate_text)
            if fragmented_match:
                country = valid_country(fragmented_match.group(1))
                if country:
                    return country

    for row in _row_groups(text_blocks):
        row_value = _row_text(text_blocks, row)
        prefix_match = re.search(r'(?i)\b(product|made|produced|manufactured)\b', row_value)
        if not prefix_match:
            continue
        candidate_text = re.sub(
            r'(?i)\b(product|made|produced|manufactured)(of|in)(?=[a-z])',
            r'\1 \2 ',
            row_value,
        )
        fragmented_match = fragmented_origin_pattern.search(candidate_text)
        if fragmented_match:
            country = valid_country(fragmented_match.group(1))
            if country:
                return country

    standalone_pattern = re.compile(
        r'\b(?:PRODUCT\s+OF|MADE\s+IN|ORIGIN\s+OF)\s+([A-Za-z]{3,30})\b',
        re.IGNORECASE
    )
    match = standalone_pattern.search(combined_text) if (not has_geometry or inline_origin) else None
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
    Extracts product name with strict conservative prioritization:
    Priority 1: Explicit GENERIC_NAME / PRODUCT_NAME declaration with associated value.
    Priority 2: Strongly supported product descriptor (excluding questions, promotional taglines, price headers, instructions).
    Priority 3: Otherwise None.

    A false product name is strictly worse than None.
    """
    used_values = set()
    for val in known_extracted:
        if val and isinstance(val, str):
            used_values.add(val.lower())

    explicit_label = re.compile(
        r'(?i)^(?:Common\s*/?\s*Gen[a-z]*|Generic|Commodity|Product)\s+Name\s*[:.-]?\s*(.*)$'
    )

    interrogative_re = re.compile(
        r'(?i)^(?:what|why|how|when|where|who|whom|which|is|are|can|could|do|does|did|will|would|should)\b'
    )

    promotional_verbs_re = re.compile(
        r'(?i)\b(?:special|makes|delight|squeeze|rinse|massage|apply|lather|gently|feel|refreshing|experience|boost|enjoy|pure|goodness|secret|enriched|love|everyday\s*protein|cleanse|hydrat[a-z]*|protect[a-z]*)\b'
    )

    price_terms_re = re.compile(
        r'(?i)\b(?:sale|price|mrp|cost|rate|taxes?|tax|incl|inclusive|usp|unit\s+sale|rs|inr|off|discount|save)\b'
    )

    instructional_or_legal_re = re.compile(
        r'(?i)\b(?:directions?|how\s+to|storage|store\s+in|warning|caution|tamper|fssai|fssat|lic|licence|license|batch|lot|code|mfg|mfd|packed|pkd|expiry|exp|use\s+by|best\s+before|use\s+only|external\s+use|for\s+external|usage|ingredients?|nutrition|nutritional|allergen|consumer|customer|care|contact|feedback|telephone|phone|email|website|address|net\s+wt|net\s+qty|quantity|units?|commodity|model|origin|country)\b'
    )

    def is_declaration_or_header(val):
        """Returns True if text matches any declaration label, header, or section boundary."""
        if not val:
            return True
        if _is_field_label(val) or _looks_like_section_boundary(val):
            return True
        canonical = _canonical_label(val)
        if canonical:
            return True
        val_lower = val.lower().strip()
        header_keywords = (
            "marketed", "manufactured", "packed", "imported", "license", "licence",
            "fssai", "storage", "instruction", "instructions", "direction", "directions",
            "batch", "mrp", "retail", "expiry", "best before", "use by", "warning",
            "caution", "tamper", "allergen", "nutrition", "nutritional", "ingredient",
            "ingredients", "consumer", "customer", "complaint", "feedback", "telephone",
            "email", "website", "contact", "address", "net wt", "net qty", "quantity",
            "sale", "price"
        )
        for token in re.findall(r'[a-z]+', val_lower):
            if any(
                token == kw or (len(token) >= 5 and SequenceMatcher(None, token, kw).ratio() >= 0.84)
                for kw in header_keywords
            ):
                return True
        return False

    def valid_explicit_value(value):
        """Validates a value associated with an explicit statutory generic name declaration."""
        if not value:
            return False
        normalized = re.sub(r'\s+', ' ', value.strip())
        if len(normalized) < 2:
            return False
        if is_declaration_or_header(normalized):
            return False
        if _is_address_text(normalized) or COMPANY_SUFFIX_PATTERN.search(normalized):
            return False
        if re.search(r'(?i)@|https?://|\b(?:mrp|net\s+(?:wt|qty)|telephone|phone|email|customer\s+care|country\s+of)\b', normalized):
            return False
        return not bool(re.fullmatch(r'(?i)(?:product|information|details|label|select|of|in)', normalized))

    def valid_unlabeled_candidate(value, block, reading_pos, entity_start_pos):
        """Validates an unlabeled candidate block. Strict conservative safety criteria apply."""
        if not value:
            return False
        normalized = re.sub(r'\s+', ' ', value.strip())
        if len(normalized) < 3:
            return False
        # Reject question marks or question starters
        if '?' in normalized or interrogative_re.search(normalized):
            return False
        # Reject exclamations or full sentences
        if '!' in normalized or normalized.endswith('.'):
            return False
        # Reject promotional sentences/verbs
        if promotional_verbs_re.search(normalized):
            return False
        # Reject price headers (e.g. 'Sale Price')
        if price_terms_re.search(normalized):
            return False
        # Reject instructional or legal headers
        if instructional_or_legal_re.search(normalized):
            return False
        # High confidence requirement for unlabeled candidates
        if block.get("confidence", 1.0) < 0.75:
            return False
        if entity_start_pos is not None and reading_pos >= entity_start_pos:
            return False
        if is_declaration_or_header(normalized):
            return False
        if _is_address_text(normalized) or COMPANY_SUFFIX_PATTERN.search(normalized):
            return False
        if re.search(r'(?i)@|https?://|\b(?:mrp|net\s+(?:wt|qty)|telephone|phone|email|customer\s+care|country\s+of)\b', normalized):
            return False
        if re.match(r'^\d+$', normalized):
            return False
        norm_lower = normalized.lower()
        if any(norm_lower in used or used in norm_lower for used in used_values if len(used) > 2):
            return False
        words = re.findall(r'[A-Za-z]{2,}', normalized)
        # Require between 2 and 5 descriptive words
        if len(words) < 2 or len(words) > 5:
            return False
        if bool(re.fullmatch(r'(?i)(?:product|information|details|label|select|of|in|everyday\s*protein)', normalized)):
            return False
        return True

    ordered = _reading_order(text_blocks)
    entity_start_pos = None
    for pos, (_, block) in enumerate(ordered):
        txt = block.get("text", "").strip()
        if re.search(r'(?i)\b(?:manufactured\s+by|mfg\s+by|mfd\s+by|marketed\s+by|packed\s+by|imported\s+by)\b', txt):
            entity_start_pos = pos
            break

    # PRIORITY 1: Explicit statutory label
    for index, block in ordered:
        text = block.get("text", "").strip()
        label_match = explicit_label.search(text)
        if label_match:
            value = label_match.group(1).strip()
            if value and valid_explicit_value(value):
                return value
            for candidate_index in _label_value_candidates(text_blocks, index, same_row_only=True):
                candidate = text_blocks[candidate_index].get("text", "").strip()
                if candidate and valid_explicit_value(candidate):
                    return candidate
            for candidate_index in _label_value_candidates(text_blocks, index):
                candidate = text_blocks[candidate_index].get("text", "").strip()
                if candidate and valid_explicit_value(candidate):
                    return candidate

    # PRIORITY 2: Conservative unlabeled candidate (strong evidence only)
    for pos, (orig_index, block) in enumerate(ordered):
        txt = block.get("text", "").strip()
        if valid_unlabeled_candidate(txt, block, pos, entity_start_pos):
            return txt

    # PRIORITY 3: Otherwise None
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
    date_pts = 1.0 if (month_pkd is not None and year_pkd is not None) else (0.5 if (month_pkd is not None or year_pkd is not None) else 0.0)

    care_pts = 0.5 if care_info is not None else 0.0
    prod_pts = 0.5 if product_name is not None else 0.0

    completeness_score = mrp_pts + qty_pts + mfg_pts + date_pts + care_pts + prod_pts

    confidences = [b.get("confidence", 1.0) for b in filtered_text_blocks]
    mean_ocr_conf = sum(confidences) / len(confidences) if confidences else 0.0

    # Strict confidence assignment:
    # HIGH requires acceptable image quality, high mean OCR confidence, and full core statutory fields.
    if quality_status in ("POOR", "UNREADABLE") or completeness_score < 2.0:
        confidence_flag = "LOW"
    elif quality_status == "ACCEPTABLE" and completeness_score >= 3.5 and mean_ocr_conf >= 0.50 and mrp is not None and net_qty is not None and (mfg_name is not None or mfg_addr is not None) and (month_pkd is not None or year_pkd is not None):
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

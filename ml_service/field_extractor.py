import math
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
        "mfg by", "mfg for", "mfg/pack", "mfg / pack", "mfg/pkd", "mfg & pack",
        "made by", "produced by", "manufacturer", "mfg unit", "factory address"
    ),
    "MARKETED_BY": (
        "marketed by", "marketed for", "marketed in", "mkd by", "marketer"
    ),
    "PACKER": (
        "packed by", "packed for", "packed in", "packed", "pkd by", "packer"
    ),
    "IMPORTER": (
        "imported by", "imported in", "importer", "importer name", "import & marketed by",
        "imp by", "imported for"
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

    cleaned_context = re.sub(r'[()]', ' ', combined_context)
    has_tax = bool(re.search(r'(?i)(?:\b|(?<=\d))(?:nclusive|inclusive|incl|tax|taxes)\b', cleaned_context))

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
    r'marketed\s+by|manufactured\s+by|mfg[./\s]*(?:by|for|pack|packed|pkd)?|mfd[./\s]*(?:by|for|pack|packed|pkd)?|'
    r'packed[.\s]*(?:by)?|pkd[.\s]*(?:by)?|imported\s+by|manufacturer|packer|'
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


# Regex matching net-quantity / net-content / net-vol context phrases.
# Values extracted near these phrases must NEVER be treated as MRP.
_NET_QTY_CONTEXT_RE = re.compile(
    r'(?i)\b(?:net\s*(?:qty|quantity|wt|weight|vol|volume|content|contents)|nett\s*(?:qty|quantity|wt|weight)|net\s+content)\b'
)


def _is_net_qty_context(text: str) -> bool:
    """Returns True if the text is primarily a net-quantity/net-content block, not an MRP block."""
    if _NET_QTY_CONTEXT_RE.search(text):
        return True
    # A bare unit-of-measure value with no price prefix is a qty candidate, not a price
    if re.fullmatch(
        r'(?i)\s*\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters|pcs|units|n)\s*',
        text.strip()
    ):
        return True
    return False


def _extract_mrp(text_blocks, full_text):
    """
    Extract MRP only when a retail-price label supports the numeric value.
    Handles glued stamp formats where price and date are concatenated (e.g. '175.0007/25')
    only when supported by explicit MRP context.

    SAFETY: A value that is a net-quantity/net-content candidate must never be returned as MRP.
    """
    label_pattern = re.compile(
        r'(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Ret(?:ail)?\s*P[a-z]{0,4}e?|Ret(?:ail)?\s*P[a-z]{0,4}e?)',
        re.IGNORECASE
    )
    price_pattern = re.compile(r'(?<!\d)(\d{2,}(?:[\.,]\d{1,2}|\s+\d{2})?)(?!\d|/\d)')
    glued_price_pattern = re.compile(r'(?<!\d)(\d{2,}\.\d{2})(?=\d{2}/\d{2,4})')
    value_pattern = re.compile(
        r'\s*[:\.-]?\s*(?:Rs\.?|₹|INR)?\s*\d+(?:[\.,]\d{1,2}|\s+\d{2})?'
        r'(?:\s*[\(\)]?\s*(?:incl|inclusive|nclusive)[^\n\r]{0,35}?(?:taxes?|tax)?\s*[\(\)]?)?',
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
                # SAFETY: Never pick a nearby block that is itself a net-quantity context.
                if _is_net_qty_context(nearby_text):
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
            # First: try to find the quantity directly within this block
            direct_qty = qty_pattern.search(txt)
            if direct_qty:
                return direct_qty.group(1).strip()
            # Fallback: look at adjacent blocks (skip unit-price blocks)
            _usp_skip_re = re.compile(r'(?i)\b(?:unit\s+sale\s+price|unit\s+price|sale\s+price\s+per)\b')
            for nearby_index in _nearby_blocks(text_blocks, block_index):
                nearby_text = text_blocks[nearby_index].get("text", "")
                if _usp_skip_re.search(nearby_text):
                    continue
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

    # Fallback to generic quantity search — exclude blocks that contain a unit-price label.
    _usp_label_exclusion_re = re.compile(
        r'(?i)\b(?:unit\s+sale\s+price|unit\s+price|sale\s+price\s+per\s+unit|price\s+per)\b'
    )
    for block in text_blocks:
        txt = block.get("text", "").strip()
        match = generic_qty_pattern.search(txt)
        if match and not any(kw in txt.lower() for kw in ["mrp", "rs", "₹", "date", "batch", "lot"]) \
                and not _usp_label_exclusion_re.search(txt):
            return match.group(1).strip()

    match = generic_qty_pattern.search(full_text)
    if match:
        return match.group(1).strip()

    return None


ALLERGEN_KEYWORDS = ("facility", "may process", "allergen", "equipment", "may contain", "processed in")
TM_KEYWORDS = ("tm owners", "tm owner", "trademark owner", "trademark owners", "brand owner")


_STATUTORY_TARGET_WORDS = {
    "manufactured": 4,
    "manufacturer": 4,
    "marketed": 3,
    "marketer": 3,
    "packed": 3,
    "packer": 3,
    "registered": 2,
}

_CORRUPTED_STATUTORY_LABEL_RE = re.compile(
    r'(?i)\b([a-z]{4,15})\s*(?:by|bv|bi|for|[:.-])',
    re.IGNORECASE
)


def _match_corrupted_statutory_label(text):
    text_clean = text.strip()
    for match in _CORRUPTED_STATUTORY_LABEL_RE.finditer(text_clean):
        candidate_word = match.group(1).lower()
        for target, score in _STATUTORY_TARGET_WORDS.items():
            if SequenceMatcher(None, candidate_word, target).ratio() >= 0.70:
                end_pos = match.end()
                rest = text_clean[end_pos:]
                by_m = re.match(r'^\s*(?:by|bv|bi|for)?\s*[:.-]?', rest, re.IGNORECASE)
                if by_m:
                    end_pos += by_m.end()
                return score, end_pos, target
    return None


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
        r'(?:(?:Manufacturer|Packer|Manufactured|Marketed)\s*[:./-]+|'
        r'(?:Manufactured\s+(?:by|for|in)|Mfg[./\s]*(?:by|for|pack|packed|pkd)|Mfd[./\s]*(?:by|for|pack|packed|pkd)|'
        r'Made\s+(?:in\s+[A-Za-z]+\s+)?by|Packed\s+by|Pkd\s+by|Marketed\s+(?:by|for)|Mkd\s+by|Manufacturer\s+Name)\s*[:./-]?)\s*(.+)',
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
        if re.search(r'(?i)\b(?:use|see|incl|price|batch|mfd|mrp|product|before|belore|net\s*qty|net\s*wt)\b', normalized):
            return False
        if re.match(r'(?i)^(?:registered|regd|factory|plant|mfg|manufacturing)?\s*address\b', normalized):
            return False
        return True

    def role_score(header_text):
        h = header_text.lower()
        if any(mfg_term in h for mfg_term in ["manufactured by", "mfg by", "mfd by", "mfg. by", "mfd. by", "mfg/pack", "mfg / pack", "mfg/pkd", "mfg & pack", "made in", "made by", "produced by", "manufacturer", "factory address", "manufacturing unit"]):
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
        r'(?:Manufacturer|Packer|Manufactured|Marketed)\s*[:./-]+|'
        r'(?:Manufactured\s+(?:by|for|in)|Mfg[./\s]*(?:by|for|pack|packed|pkd)|Mfd[./\s]*(?:by|for|pack|packed|pkd)|'
        r'Packed\s+by|Pkd\s+by|Marketed\s+(?:by|for)|Mkd\s+by|'
        r'Made\s+in\s+[A-Za-z\s]+by|Manufacturer\s+Name)\s*[:./-]?)'
    )
    ordered_blocks = _reading_order(text_blocks)
    semantic_boundary_indices = _semantic_boundary_indices(ordered_blocks)
    section_results = []

    for position, (block_index, block) in enumerate(ordered_blocks):
        text = block.get("text", "").strip()
        if any(tm_kw in text.lower() for tm_kw in TM_KEYWORDS):
            continue
        section_match = section_pattern.search(text)
        corrupted_match = None
        if not section_match:
            corrupted_match = _match_corrupted_statutory_label(text)
        if (not section_match and not corrupted_match) or any(kw in text.lower() for kw in ALLERGEN_KEYWORDS):
            continue

        if section_match:
            matched_header = text[:section_match.end()]
            score = role_score(matched_header)
            inline_value = text[section_match.end():].strip()
        else:
            score, end_pos, _ = corrupted_match
            matched_header = text[:end_pos]
            inline_value = text[end_pos:].strip()
        # Clean inline prefix leftovers like '/Regd.office' or ': '
        inline_value = re.sub(
            r'^(?:[/:.-]|\b(?:regd|mfd|mfg|pack|pkd)[./\s]*(?:office|address|by|for|pack|packed|pkd)[/:.-]?\s*)+',
            '',
            inline_value,
            flags=re.IGNORECASE
        ).strip()

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
            if corrupted_match and not (COMPANY_SUFFIX_PATTERN.search(candidate_name) and is_company_candidate(candidate_name)):
                continue
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

    # Company-suffix-only unlabelled scan: only used when a nearby block carries a
    # recognisable manufacturer/packer label anchor.  This prevents an arbitrary
    # company-like word (e.g. 'VITAMINC') from being elevated to manufacturerName
    # merely because it contains a suffix like 'Industries' or 'Solutions'.
    _mfg_anchor_re = re.compile(
        r'(?i)\b(?:manufactured?\s+by|mfg[./\s]*(?:by|for|pack|packed|pkd)|mfd[./\s]*(?:by|for)|'
        r'packed\s+by|pkd\s+by|marketed\s+by|mkd\s+by|manufacturer|packer|'
        r'regd[./\s]*(?:office|ofce|offce)|ofce\b|'
        r'registered\s+address|factory\s+address|manufacturing\s+unit|'
        r'in\s+[A-Za-z]{3,20}\s+by)\b'
    )

    def _has_statutory_anchor(anchor_text):
        if not anchor_text:
            return False
        if _mfg_anchor_re.search(anchor_text):
            return True
        return _match_corrupted_statutory_label(anchor_text) is not None

    if not name:
        for index, block in enumerate(text_blocks):
            text = block.get("text", "").strip()
            if not text or any(kw in text.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in text.lower() for tm in TM_KEYWORDS):
                continue
            comp_match = COMPANY_SUFFIX_PATTERN.search(text)
            if not comp_match or not is_company_candidate(text):
                continue
            # Require that either this block or a nearby block has a manufacturer-label anchor.
            has_anchor = bool(_has_statutory_anchor(text))
            if not has_anchor:
                for nearby_index in _nearby_blocks(text_blocks, index, max_vertical_gap=60):
                    nearby_txt = text_blocks[nearby_index].get("text", "").strip()
                    if _has_statutory_anchor(nearby_txt):
                        has_anchor = True
                        break
            if not has_anchor:
                continue

            words = re.findall(r'[A-Za-z]+', comp_match.group(1).strip())
            if len(words) >= 2 and is_company_candidate(comp_match.group(1)):
                name = comp_match.group(1).strip()
                rem = comp_match.group(2).strip()
                if rem and _is_address_text(rem):
                    address = rem
            else:
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
                if not address:
                    pos = next((i for i, (orig_i, _) in enumerate(ordered_blocks) if orig_i == index), -1)
                    if pos >= 0:
                        addr_parts = []
                        prev_b = ordered_blocks[pos][1]
                        for _, follow_b in ordered_blocks[pos + 1:]:
                            f_txt = follow_b.get("text", "").strip()
                            if any(tm in f_txt.lower() for tm in TM_KEYWORDS) or _looks_like_section_boundary(f_txt):
                                break
                            if _is_plausible_address_block(prev_b, follow_b):
                                if not _has_statutory_anchor(f_txt):
                                    addr_parts.append(f_txt)
                                prev_b = follow_b
                        while addr_parts and re.search(r'(?i)\b(?:fssai|fssat|lic|licence|license|art\.?\s*\d+)\b', addr_parts[-1].strip()):
                            addr_parts.pop()
                        if addr_parts:
                            address = " ".join(addr_parts)
                break

    # Fallback to raw blocks (confidence < 0.10) if name is still missing.
    # Requires either a mfg-label anchor in the block itself, or that the block
    # was already matched via the section_pattern scan above (section_results non-empty
    # means we already found labelled context; this path is purely for
    # sub-threshold-confidence blocks that carry an explicit label).
    if not name and raw_blocks:
        for b in raw_blocks:
            txt = b.get("text", "").strip()
            if not txt or any(kw in txt.lower() for kw in ALLERGEN_KEYWORDS) or any(tm in txt.lower() for tm in TM_KEYWORDS):
                continue
            # Raw-block fallback ONLY when an explicit mfg/packer label is present in the block.
            if not _has_statutory_anchor(txt):
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

    # Explicit manufacturing/packing date pattern.
    # NOTE: The anchor keywords MUST be genuinely manufacturing/packing context.
    # Fused OCR artefacts like 'MFD.NOUSEBEFORE' must NOT match — the pattern
    # requires a positive manufacturing keyword followed (possibly via separator) by
    # date digits. The negative lookbehind in the anchor ensures 'USEBEFORE' or
    # 'USE BEFORE' fused to a manufacturing prefix is treated as expiry context.
    date_pattern = re.compile(
        r'(?:(?:Month\s*(?:and|&)?\s*Year\s*of|Date\s*of|Month/Year\s*of)\s*)?'
        r'(?:Manu[a-z]+|Manuf[a-z]*|Mfg(?:\s+Date)?|Mfd(?:\s+Date)?|Pack[a-z]*|Pkd|DOM|DOP|Packing|Manufacture)'
        r'(?!\s*\.?\s*(?:no|use\s*before|usebefore|exp|expiry|best\s*before))'
        r'\s*[:\.-]?\s*'
        rf'(?:([0-3]?\d)[/\.\-\s]+)?({month_pattern}|[0-1]?\d)[/\.\-\s]+(20\d{{2}}|\d{{2}}(?!\d))',
        re.IGNORECASE
    )

    expiry_or_batch_re = re.compile(
        r'(?i)\b(?:exp|expiry|best\s+before|use\s+by|use\s+before|usebefore|batch|lot|b\.?\s*no)\b'
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


# Consumer-care label context — used to validate that a website belongs to the
# consumer-care section rather than being an arbitrary URL on the label.
_CONSUMER_CARE_LABEL_RE = re.compile(
    r'(?i)\b(?:consumer\s*care|customer\s*care|care\s*cell|customer\s*complaints?|'
    r'consumer\s*complaints?|contact\s*us|feedback|telephone|phone|tel|helpline|'
    r'toll\s*free|email|e[- ]?mail|website|web\s*site|visit\s*us)\b'
)


def _extract_consumer_care(text_blocks, full_text):
    """
    Extracts structured consumer care contact details (phone, email, website).
    - Phone/email are extracted from blocks associated with consumer-care labels.
    - Website is only extracted when accompanied by a consumer-care context label.
    Excludes regulatory license numbers (FSSAI, Lic No, EAN, barcode, pin codes).
    """
    # Toll-free numbers: 1800 followed by groups of 2-4 digits separated by hyphens/spaces.
    # Handles formats: 1800-10-22-221, 1800-102-5353, 1800 3099 807, etc.
    tollfree_pattern = re.compile(r'\b1800(?:[-\s]?\d{2,4}){2,4}\b')
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
    combined_text = re.sub(r'\s+([.@])\s+', r'\1', combined_text)
    combined_text = re.sub(r'(?i)\s+at\s+', '@', combined_text)
    combined_text = re.sub(r'(?i)\b(?:ac|at)\s+(?=[a-z0-9._%+-]+\s*@)', '', combined_text)
    combined_text = re.sub(r'\s+@', '@', combined_text)
    combined_text = re.sub(r'(?<=@)([A-Za-z0-9._%+-]+)\s+(com|in|org|net)\b', r'\1.\2', combined_text, flags=re.IGNORECASE)

    # Determine whether the combined text carries a consumer-care label (for website validation)
    has_care_label = bool(_CONSUMER_CARE_LABEL_RE.search(combined_text))

    email_match = email_pattern.search(combined_text)

    # Website: only extract when a care label is present in the combined text
    web_match = None
    if has_care_label:
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
            # Verify it is not a regulatory / licence context
            if not regulatory_prefix_re.search(txt[:tf_match.start()]):
                break
            else:
                found_phone = None
                continue

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


# ---------------------------------------------------------------------------
# Rule 9 — Importer Name
# ---------------------------------------------------------------------------

_IMPORTER_LABEL_RE = re.compile(
    r'(?i)(?:'
    r'Importer(?:\s+Name)?|Imported\s+(?:by|for|in)|Imp(?:\.)?\s*[Bb]y|'
    r'Import(?:er)?\s*&?\s*Marketed\s+[Bb]y'
    r')\s*[:\.-]?\s*(.+)',
)

# Section-pattern recogniser for importer blocks (used for multi-block spans).
_IMPORTER_SECTION_RE = re.compile(
    r'(?i)(?:'
    r'Importer(?:\s+Name)?|Imported\s+(?:by|for|in)|Imp(?:\.)?\s*[Bb]y|'
    r'Import(?:er)?\s*&?\s*Marketed\s+[Bb]y'
    r')\s*[:\.-]?'
)

# Words that disqualify a value from being an importer name.
_IMPORTER_EXCLUSION_RE = re.compile(
    r'(?i)\b(?:manufactured|mfg|mfd|packed|pkd|marketed|marketer|batch|lot|'
    r'fssai|fssat|lic|licence|license|ean|upc|barcode|date|expiry|mrp|net\s*qty|net\s*wt|'
    r'customer\s*care|consumer\s*care|telephone|phone|email|website)\b'
)


def _extract_importer(text_blocks, full_text):
    """
    Extracts importer name from blocks with explicit importer labels.

    Recognises labels such as:
        Importer: / Importer Name: / Imported By: / Imported by: /
        IMP BY: / Import & Marketed By:

    Safety rules:
    - Explicit label required; no label → null.
    - Do not confuse manufacturer, packer, or marketer as importer.
    - Do not accept values that look like prices, dates, or batch codes.
    - Do not hardcode any company name.
    """

    def is_valid_importer_value(val):
        if not val:
            return False
        val = val.strip()
        if len(val) < 2:
            return False
        if _IMPORTER_EXCLUSION_RE.search(val):
            return False
        if '@' in val or re.search(r'(?i)\b(?:https?://|www\.)\b', val):
            return False
        if re.match(r'^[^A-Za-z]+$', val):
            return False
        # Must have at least one alphabetic word of length ≥ 2
        if not re.search(r'[A-Za-z]{2,}', val):
            return False
        return True

    # Priority 1: inline label match within a single block
    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        m = _IMPORTER_LABEL_RE.match(txt)
        if m:
            val = m.group(1).strip()
            # Truncate at any strong boundary keyword
            b_match = BOUNDARY_KEYWORDS_RE.search(val)
            if b_match:
                val = val[:b_match.start()].strip()
            # Strip company suffix and take name only if it has a suffix
            comp_m = COMPANY_SUFFIX_PATTERN.search(val)
            candidate = comp_m.group(1).strip() if comp_m else val
            if is_valid_importer_value(candidate):
                return candidate
            # Try following block
            for nearby_index in _label_value_candidates(text_blocks, block_index, same_row_only=True):
                nearby_text = text_blocks[nearby_index].get("text", "").strip()
                b_m2 = BOUNDARY_KEYWORDS_RE.search(nearby_text)
                if b_m2:
                    nearby_text = nearby_text[:b_m2.start()].strip()
                comp_m2 = COMPANY_SUFFIX_PATTERN.search(nearby_text)
                cand2 = comp_m2.group(1).strip() if comp_m2 else nearby_text
                if is_valid_importer_value(cand2):
                    return cand2

    # Priority 2: label at start of block, value on the next block(s)
    ordered = _reading_order(text_blocks)
    for pos, (block_index, block) in enumerate(ordered):
        txt = block.get("text", "").strip()
        if not _IMPORTER_SECTION_RE.match(txt):
            continue
        for _, following_block in ordered[pos + 1:pos + 4]:
            following_text = following_block.get("text", "").strip()
            if _looks_like_section_boundary(following_text):
                break
            b_m = BOUNDARY_KEYWORDS_RE.search(following_text)
            if b_m:
                following_text = following_text[:b_m.start()].strip()
            comp_m = COMPANY_SUFFIX_PATTERN.search(following_text)
            cand = comp_m.group(1).strip() if comp_m else following_text
            if is_valid_importer_value(cand):
                return cand
            break  # Only examine the immediately-following block

    return None


# ---------------------------------------------------------------------------
# Rule 10 — Expiry Date
# ---------------------------------------------------------------------------

_EXPIRY_LABEL_RE = re.compile(
    r'(?i)(?:'
    r'Expir(?:y|ed)?(?:\s+Date)?|Exp(?:\.)?(?:\s+Date)?|'
    r'Use\s+(?:Before|By)|Best\s+Before(?:\s+End)?|BBE|BB'
    r')'
    r'\s*[:\.-]?\s*'
)

_EXPIRY_DATE_RE = re.compile(
    r'(?i)'
    r'(?:(?:Expir(?:y|ed)?(?:\s+Date)?|Exp(?:\.)?(?:\s+Date)?|'
    r'Use\s+(?:Before|By)|Best\s+Before(?:\s+End)?|BBE)\s*[:\.-]?\s*)'
    r'(?:([0-3]?\d)[/\.\-\s]+)?'
    r'((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
    r'jul(?:y)?|aug(?:us|ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|'
    r'dec(?:ember)?)|[0-1]?\d)'
    r'[/\.\-\s]+(20\d{2}|\d{2}(?!\d))'
)

# Negative lookbehind context: if the preceding text carries a manufacturing
# keyword, we must not treat the date as expiry.
_MFG_ONLY_CONTEXT_RE = re.compile(
    r'(?i)\b(?:mfg|mfd|manufacture(?:d|r)?|packing|packed|pkd|dom|dop)\b'
)


def _extract_expiry_date(text_blocks, full_text):
    """
    Extracts expiry / use-before / best-before date.

    Safety rules:
    - Expiry context label is required (EXP, Expiry, Use Before, Best Before, BBE).
    - Must not pick up manufacturing/packing dates.
    - Must not interpret batch codes as expiry dates.
    - Returns (month_str, year_str) or (None, None).
    """
    month_pattern = (
        r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
        r'jul(?:y)?|aug(?:us|ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|'
        r'dec(?:ember)?)'
    )

    batch_only_re = re.compile(
        r'(?i)^\s*(?:batch|lot|b\.?\s*no)[^\d]*[A-Z0-9]+\s*$'
    )

    # Pattern: expiry label immediately followed by a date
    expiry_inline_re = re.compile(
        r'(?i)(?:'
        r'Expir(?:y|ed)?(?:\s+Date)?|Exp(?:\.)?(?:\s+Date)?|'
        r'Use\s+(?:Before|By)|Best\s+Before(?:\s+End)?|BBE|BB'
        r')\s*[:\.-]?\s*'
        rf'(?:([0-3]?\d)[/\.\-\s]+)?({month_pattern}|[0-1]?\d)[/\.\-\s]+(20\d{{2}}|\d{{2}}(?!\d))'
    )

    date_value_re = re.compile(
        rf'\b(?:([0-3]?\d)[/\.\-\s]+)?({month_pattern}|[0-1]?\d)[/\.\-\s]+(20\d{{2}}|\d{{2}}(?!\d))\b',
        re.IGNORECASE
    )

    expiry_context_re = re.compile(
        r'(?i)\b(?:exp(?:ir(?:y|ed))?(?:\s+date)?|use\s+(?:before|by)|best\s+before(?:\s+end)?|bbe|bb)\b'
    )

    def parse_date_groups(groups):
        """Parse matched (day, month, year) groups into (month_str, year_str)."""
        m_raw = groups[1] if len(groups) > 1 else groups[0]
        y_raw = groups[2] if len(groups) > 2 else groups[1]
        m_str = str(m_raw).strip().lower()
        if m_str in MONTH_MAP:
            month = MONTH_MAP[m_str]
        elif len(m_str) >= 3 and any(name.startswith(m_str) for name in MONTH_MAP):
            month = MONTH_MAP[next(name for name in MONTH_MAP if name.startswith(m_str))]
        elif m_str.isdigit():
            month = f"{int(m_str):02d}"
        else:
            return None, None
        y_str = str(y_raw).strip()
        year = f"20{y_str}" if len(y_str) == 2 else y_str
        return month, year

    # Search each block for inline expiry pattern
    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        if not txt or batch_only_re.match(txt):
            continue
        m = expiry_inline_re.search(txt)
        if m:
            # Ensure the prefix doesn't carry a manufacturing-only context
            prefix = txt[:m.start()]
            if _MFG_ONLY_CONTEXT_RE.search(prefix) and not expiry_context_re.search(prefix):
                continue
            month, year = parse_date_groups(m.groups())
            if month and year:
                return month, year

        # Block has expiry label but no inline date → look at adjacent blocks
        if expiry_context_re.search(txt):
            # Make sure there's no manufacturing-only context in this block
            if _MFG_ONLY_CONTEXT_RE.search(txt) and not expiry_context_re.search(txt):
                continue
            for nearby_index in _label_value_candidates(text_blocks, block_index, max_distance=150):
                nearby_txt = text_blocks[nearby_index].get("text", "").strip()
                if batch_only_re.match(nearby_txt):
                    continue
                if _MFG_ONLY_CONTEXT_RE.search(nearby_txt) and not expiry_context_re.search(nearby_txt):
                    continue
                dm = date_value_re.search(nearby_txt)
                if dm:
                    month, year = parse_date_groups(dm.groups())
                    if month and year:
                        return month, year

    # Full-text fallback — only when an expiry label is clearly present
    combined = " ".join(b.get("text", "") for b in text_blocks) or full_text
    m = expiry_inline_re.search(combined)
    if m:
        prefix = combined[max(0, m.start() - 30):m.start()]
        if not (_MFG_ONLY_CONTEXT_RE.search(prefix) and not expiry_context_re.search(prefix)):
            month, year = parse_date_groups(m.groups())
            if month and year:
                return month, year

    return None, None


# ---------------------------------------------------------------------------
# Rule 11 — Unit Sale Price
# ---------------------------------------------------------------------------

_UNIT_PRICE_LABEL_RE = re.compile(
    r'(?i)(?:'
    r'Unit\s+Sale\s+Price|Unit\s+Price|Sale\s+Price\s+per\s+Unit|'
    r'Price\s+per\s+(?:unit|100\s*g|100\s*ml|kg|g\b|l\b|ml\b)|'
    r'Rs\.?/?(?:100\s*g|100\s*ml|kg|g\b|l\b|ml\b)|'
    r'₹/?(?:100\s*g|100\s*ml|kg|g\b|l\b|ml\b)'
    r')\s*[:\.-]?\s*'
)

_UNIT_PRICE_VALUE_RE = re.compile(
    r'(?i)(?:Rs\.?|₹|INR)?\s*(\d+(?:[\.,]\d{1,2})?)'
    r'(?:\s*/\s*(?:100\s*g|100\s*ml|kg|g\b|l\b|ml\b|unit))?'
)

# Net-quantity units that must NEVER be treated as Unit Sale Price.
_QTY_UNIT_ONLY_RE = re.compile(
    r'(?i)^\s*\d+(?:\.\d+)?\s*(?:g|kg|ml|l|gm|gms|gram|grams|ltr|liter|litres|liters|pcs|units?|n)\s*$'
)


def _extract_unit_sale_price(text_blocks, full_text):
    """
    Extracts Unit Sale Price when accompanied by an explicit unit-price label.

    Recognised labels:
        Unit Sale Price, Unit Price, Sale Price per Unit,
        Rs./100g, Rs./100ml, Rs./kg, ₹/100g, ₹/100ml, Price per 100g, etc.

    Safety rules:
    - MRP must remain a separate field.
    - Net Quantity values (250ml, 500g, 1kg …) must never become Unit Sale Price.
    - A random numeric token is not accepted without a unit-price context label.
    """

    def is_valid_unit_price(val, context):
        """Return True if the candidate looks like a genuine price (not a quantity)."""
        if not val:
            return False
        if _QTY_UNIT_ONLY_RE.match(val):
            return False
        digits = re.sub(r'\D', '', val)
        if not digits:
            return False
        # Sanity-check: price should have 1-6 digits
        if len(digits) > 7:
            return False
        return True

    def _normalize_unit_price(value_str, label_context=""):
        """Normalise to a clean Rs./₹ price string.

        Parameters
        ----------
        value_str : str
            The numeric value portion only (e.g. '40.00', 'Rs. 100.00').
        label_context : str
            The full original text (label + value) for prefix and unit detection.
        """
        full_ctx = label_context or value_str
        has_rupee = '\u20b9' in full_ctx
        prefix = '\u20b9' if has_rupee else 'Rs.'
        price_m = re.search(r'(\d+(?:[.,]\d{1,2})?)', value_str)
        if not price_m:
            return value_str.strip()
        price_val = price_m.group(1).replace(',', '.')
        if '.' not in price_val:
            price_val = f"{price_val}.00"
        # Extract the unit denominator from the label context (e.g. /100ml /kg)
        unit_m = re.search(r'/\s*(100\s*g|100\s*ml|kg|g\b|l\b|ml\b|unit)', full_ctx, re.IGNORECASE)
        unit_str = f"/{unit_m.group(1).strip()}" if unit_m else ""
        return f"{prefix} {price_val}{unit_str}"

    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        label_m = _UNIT_PRICE_LABEL_RE.search(txt)
        if label_m:
            after = txt[label_m.end():].strip()
            # Reject if the remaining text looks like a pure quantity
            if _QTY_UNIT_ONLY_RE.match(after):
                continue
            val_m = _UNIT_PRICE_VALUE_RE.match(after)
            if val_m and val_m.group(1):
                return _normalize_unit_price(after[:val_m.end()].strip(), label_context=txt)
            # Look at same-row neighboring blocks
            for nearby_index in _label_value_candidates(text_blocks, block_index, same_row_only=True):
                nearby_text = text_blocks[nearby_index].get("text", "").strip()
                if _QTY_UNIT_ONLY_RE.match(nearby_text):
                    continue
                nv_m = _UNIT_PRICE_VALUE_RE.match(nearby_text)
                if nv_m and nv_m.group(1):
                    return _normalize_unit_price(nearby_text[:nv_m.end()].strip(), label_context=txt)

    # Full-text fallback
    label_m = _UNIT_PRICE_LABEL_RE.search(full_text)
    if label_m:
        after = full_text[label_m.end():].strip()
        if not _QTY_UNIT_ONLY_RE.match(after):
            val_m = _UNIT_PRICE_VALUE_RE.match(after)
            if val_m and val_m.group(1):
                return _normalize_unit_price(after[:val_m.end()].strip(), label_context=full_text[label_m.start():])

    return None


# ---------------------------------------------------------------------------
# Batch Number Extraction
# ---------------------------------------------------------------------------

_BATCH_LABEL_RE = re.compile(
    r'(?i)\b(?:'
    r'for\s+batch(?:\s+no\.?|\s+number)?|'
    r'batch(?:\s*/\s*lot)?(?:\s+no\.?|\s+number)?|'
    r'lot(?:\s*/\s*batch)?(?:\s+no\.?|\s+number)?|'
    r'b\.?\s*no\.?'
    r')\s*[:.\-–—]*\s*',
)

_BATCH_TRAILING_STOP_RE = re.compile(
    r'(?i)(?:'
    r'\s+(?:mfg|mfd|manufactur[a-z]*|pkd|pack[a-z]*|exp(?:ir[a-z]*)?|best\s+before|use\s+(?:by|before)|bbe|mrp|rs\.?|inr|₹|net\s*(?:qty|quantity|wt|weight|vol|volume|content)|unit\s+sale|usp|fssai|lic\.?\s*no|licen[cs]e|date|dom|dop)\b'
    r'|\s+\d{1,2}[/\.-]\d{2,4}\b'
    r'|\s+(?:see\b|refer\b|read\b|below\b|above\b)'
    r')'
)

_BATCH_INSTRUCTION_RE = re.compile(
    r'(?i)^\s*(?:'
    r'see\b|refer\b|read\b|printed\b|check\b|on\s+crimp|on\s+cap|on\s+neck|on\s+pack|on\s+bottle|'
    r'at\s+bottom|below\b|above\b|for\s+mfg|read\s+first\s+character'
    r')'
)

_BATCH_PURE_DATE_RE = re.compile(
    r'^(?:[0-3]?\d[/\.-])?[0-1]?\d[/\.-](?:20\d{2}|\d{2})$'
)

_BATCH_PURE_PRICE_RE = re.compile(
    r'^(?:rs\.?|inr|₹)?\s*\d+(?:\.\d{1,2})?(?:/-)?$',
    re.IGNORECASE
)

_BATCH_PURE_QTY_RE = re.compile(
    r'^\d+(?:\.\d+)?\s*(?:g|gm|gms|kg|ml|l|ltr|n|u|piece|count)$',
    re.IGNORECASE
)


def _clean_batch_candidate(val_str):
    if not val_str or not isinstance(val_str, str):
        return None
    m_stop = _BATCH_TRAILING_STOP_RE.search(val_str)
    if m_stop:
        val_str = val_str[:m_stop.start()]

    cleaned = val_str.strip(" :.,-–—#/\\")
    if not cleaned or len(cleaned) < 2 or len(cleaned) > 50:
        return None

    # Reject instruction text (e.g. "See Below", "Refer Crimp")
    if _BATCH_INSTRUCTION_RE.search(cleaned):
        return None

    # Reject pure date (e.g. "03/2026", "27/02/2026")
    if _BATCH_PURE_DATE_RE.match(cleaned):
        return None

    # Reject pure price (e.g. "Rs 50", "50.00")
    if _BATCH_PURE_PRICE_RE.match(cleaned):
        return None

    # Reject pure quantity (e.g. "200g", "100 ml")
    if _BATCH_PURE_QTY_RE.match(cleaned):
        return None

    # Must contain at least one alphanumeric character
    if not re.search(r'[A-Za-z0-9]', cleaned):
        return None

    # If fused without space to trailing stop words (e.g. "B12345/Mfg Date")
    if re.search(r'(?i)\b(?:mfg|mfd|exp|pkd|mrp|fssai)\b', cleaned):
        parts = re.split(r'(?i)[/,\s]+(?:mfg|mfd|exp|pkd|mrp|fssai)\b', cleaned)
        if parts and parts[0]:
            cleaned = parts[0].strip(" :.,-–—#/\\")
            if not cleaned or len(cleaned) < 2:
                return None
        else:
            return None

    return cleaned


def _extract_batch_number(text_blocks, full_text, raw_blocks=None):
    """
    Extracts batch / lot number associated with canonical batch declarations
    (e.g., 'Batch No', 'Batch Number', 'Lot No', 'Batch:', 'B. No:').

    Returns plain string when confidently found, or None when not found/ambiguous.
    """
    # 1. Search in individual text blocks for inline batch declaration
    for block_index, block in enumerate(text_blocks):
        txt = block.get("text", "").strip()
        if not txt:
            continue

        match = _BATCH_LABEL_RE.search(txt)
        if match:
            # Check if there is an inline value in the same block
            after_label = txt[match.end():].strip()
            if after_label:
                candidate = _clean_batch_candidate(after_label)
                if candidate:
                    return candidate

            # If no inline value in the same block, look at adjacent/nearby blocks
            for same_row in (True, False):
                for nearby_index in _label_value_candidates(text_blocks, block_index, max_distance=150, same_row_only=same_row):
                    nearby_txt = text_blocks[nearby_index].get("text", "").strip()
                    if not nearby_txt:
                        continue
                    if _is_field_label(nearby_txt):
                        continue
                    candidate = _clean_batch_candidate(nearby_txt)
                    if candidate:
                        return candidate

    # 2. Fallback: Search full_text line by line
    for line in full_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = _BATCH_LABEL_RE.search(line)
        if match:
            after_label = line[match.end():].strip()
            if after_label:
                candidate = _clean_batch_candidate(after_label)
                if candidate:
                    return candidate

    # 3. Fallback: Search anywhere in full_text
    match = _BATCH_LABEL_RE.search(full_text)
    if match:
        after_label = full_text[match.end():].strip()
        if after_label:
            candidate = _clean_batch_candidate(after_label)
            if candidate:
                return candidate

    return None


# ---------------------------------------------------------------------------
# Rule 12 — Font Height (mm)
# ---------------------------------------------------------------------------
# PaddleOCR provides bounding-box pixel dimensions. Converting pixels → mm
# requires a known physical calibration reference (pixels-per-mm).
# When calibration is unavailable or invalid, fontHeightMm is always None.
# ---------------------------------------------------------------------------

_STATUTORY_DECLARATION_RE = re.compile(
    r'(?i)\b(?:'
    # MRP
    r'mrp|maximum\s+retail\s+price|max\s+retail\s+price|retail\s+price|'
    r'incl(?:usive)?\s+of\s+all\s+taxes|'
    # Net Quantity
    r'net\s*(?:qty|quantity|wt|weight|vol|volume|content|contents)|'
    r'number\s+of\s+units\s*\(\s*quantity\s*\)|'
    # Manufacturer / Packer / Marketer / Importer
    r'manufactured\s+(?:by|for|in)|mfd[./\s]*(?:by|for|pack|pkd)|mfg[./\s]*(?:by|for|pack|pkd|unit)|'
    r'manufacturer(?:\s+name)?|made\s+in|produced\s+by|factory\s+address|'
    r'marketed\s+(?:by|for|in)|mkd[./\s]*by|marketer|'
    r'packed\s+(?:by|for|in)|pkd[./\s]*by|packer|'
    r'imported\s+(?:by|for|in)|importer(?:\s+name)?|imp[./\s]*by|'
    r'reg(?:istered|d)?\.?\s+(?:office|address)|corp(?:orate)?\.?\s+office|'
    # Dates
    r'(?:month\s+and\s+year\s+of\s+)?(?:manufacture|mfg|mfd)\b|'
    r'(?:month\s+and\s+year\s+of\s+)?(?:packing|pkd|packaging)\b|'
    r'packed\s+on|date\s+of\s+(?:manufacture|packing|packaging|expiry)|'
    # Expiry
    r'expiry(?:\s+date)?|exp[./\s]*(?:date)?|use\s+(?:by|before)|best\s+before|'
    # Batch / Lot
    r'for\s+batch\s+no|batch(?:\s+no|\s+number)?|lot(?:\s+no|\s+number)?|b\.?\s*no\.?|'
    # Consumer Care
    r'consumer\s+care|customer\s+care|care\s+cell|consumer\s+complaints|customer\s+complaints|'
    r'toll\s*free|helpline|contact\s+us|'
    # Country of Origin
    r'country\s+o[fi]\s+origin|'
    # Unit Sale Price
    r'unit\s+sale\s+price|usp\b'
    r')\b'
)

_EXCLUDE_NON_STATUTORY_RE = re.compile(
    r'(?i)\b(?:'
    r'product\s+name|generic\s+name|commodity\s+name|'
    r'steps\s+for|how\s+to\s+use|directions\s+for\s+use|warning|caution|'
    r'paraben\s*free|dermatologically|hypoallergenic|skin\s+compatibility'
    r')\b'
)


def _is_statutory_declaration_block(block):
    """
    Identifies whether an OCR text block corresponds to a mandatory packaged-commodity
    statutory declaration (MRP, Net Qty, Mfg/Packer/Importer, Dates, Expiry, Batch,
    Consumer Care, Country of Origin, USP, Registered Address).

    Explicitly excludes product name, brand/logo text, decorative marketing claims,
    and arbitrary code noise.
    """
    text = block.get("text", "").strip()
    if len(text) < 3:
        return False
    # Must contain at least one alphabetic character (reject pure numbers/barcodes)
    if not any(c.isalpha() for c in text):
        return False
    # Exclude explicit non-statutory categories (product name, routine claims)
    if _EXCLUDE_NON_STATUTORY_RE.search(text):
        return False
    return bool(_STATUTORY_DECLARATION_RE.search(text))


def _extract_font_height_px_comparison(text_blocks):
    """
    Measures OCR bounding-box heights in pixels for statutory Legal Metrology
    declaration blocks within the same image.

    No calibration, DPI, physical reference, or pixel-to-mm conversion is used.
    This is a relative intra-image comparison only.
    """
    measured = []

    for index, block in enumerate(text_blocks):
        if not _is_statutory_declaration_block(block):
            continue

        metrics = _box_metrics(block)
        if not metrics:
            continue

        height_px = metrics[3] - metrics[1]
        if height_px <= 0:
            continue

        measured.append({
            "block_index": index,
            "text": block.get("text", "").strip(),
            "height_px": int(round(height_px))
        })

    if not measured:
        return {
            "unit": "pixels",
            "calibration_reference_used": False,
            "measured_blocks": [],
            "smallest_height_px": None,
            "largest_height_px": None,
            "median_height_px": None,
            "height_range_px": None
        }

    heights = sorted(item["height_px"] for item in measured)
    n = len(heights)
    median = float(heights[n // 2]) if n % 2 else (heights[n // 2 - 1] + heights[n // 2]) / 2.0

    return {
        "unit": "pixels",
        "calibration_reference_used": False,
        "measured_blocks": measured,
        "smallest_height_px": min(heights),
        "largest_height_px": max(heights),
        "median_height_px": round(median, 2),
        "height_range_px": [min(heights), max(heights)]
    }


def _extract_font_height_mm(text_blocks, calibration_px_per_mm=None):
    """
    Returns physical font height in millimetres of the smallest relevant
    mandatory/statutory declaration block, or None if calibration is
    unavailable, non-positive, or invalid, or if no statutory blocks are found.

    Parameters
    ----------
    text_blocks : list of OCR block dicts (each with 'box' key)
    calibration_px_per_mm : float or None
        Pixels-per-millimetre conversion factor derived from a physical
        calibration reference present on or with the image.
        Pass None (default) when no calibration is available.

    Returns
    -------
    float or None
        Physical font height in mm, or None when calibration is unavailable or invalid.
    """
    if calibration_px_per_mm is None:
        return None

    try:
        calib = float(calibration_px_per_mm)
        if calib <= 0 or not math.isfinite(calib):
            return None
    except (ValueError, TypeError):
        return None

    statutory_heights = []
    for block in text_blocks:
        if not _is_statutory_declaration_block(block):
            continue
        m = _box_metrics(block)
        if m:
            height_px = m[3] - m[1]  # max_y - min_y
            if height_px > 0:
                statutory_heights.append(height_px)

    if not statutory_heights:
        return None

    min_pixel_height = min(statutory_heights)
    return round(min_pixel_height / calib, 2)


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
        r'(?i)\b(?:special|makes|delight|squeeze|rinse|massage|apply|lather|gently|feel|refreshing|experience|boost|enjoy|pure|goodness|secret|enriched|love|everyday\s*protein|cleanse|hydrat[a-z]*|protect[a-z]*|formula\s+with|contains?|may\s+contain|made\s+(?:with|from|of)|(?:bottle|pack|container|tube|packaging)\s+made|recycled|excluding|over\s+time|appearance|the\s+product)\b'
    )

    price_terms_re = re.compile(
        r'(?i)\b(?:sale|price|mrp|cost|rate|taxes?|tax|incl|inclusive|usp|unit\s+sale|rs|inr|off|discount|save)\b'
    )

    instructional_or_legal_re = re.compile(
        r'(?i)\b(?:directions?|how\s+to|storage|store\s+in|warning|caution|tamper|fssai|fssat|lic|licence|license|batch|lot|code|mfg|mfd|packed|pkd|expiry|exp|use\s+by|best\s+before|use\s+only|external\s+use|for\s+external|usage|ingredients?|nutrition|nutritional|allergen|consumer|customer|care|contact|feedback|telephone|phone|email|website|address|net\s+wt|net\s+qty|quantity|units?|commodity|model|origin|country|flush|avoid|occurs?|safety|first\s+aid|trademark|compatibility|dermatolog[a-z]*|clinical[a-z]*|tested|(?:see|refer|read)\s*(?:above|below|side|bottom|pkg|pack|panel))\b'
    )

    instructional_steps_re = re.compile(
        r'(?i)(?:'
        r'\b(?:\d+\s+)?steps?\s+(?:for|to|towards|in|of|ahead)\b'
        r'|\b(?:follow|these|easy|simple)\s+(?:these\s+)?steps?\b'
        r'|\bstep\s*[:.-]?\s*\d+\b'
        r'|\bhow\s+to\s+(?:use|apply|wash|cleanse)\b'
        r'|\broutine\s+steps?\b'
        r'|\binstructions?\b'
        r')'
    )

    dangling_prep_re = re.compile(
        r'(?i)\b(?:for|withs?|ofs?|in|to|by|from|on|at|and|or|&)\s*(?:a|an|the)?\s*$'
    )

    leading_conj_re = re.compile(
        r'(?i)^(?:and|or|&|with|of|in|for|by|from|to)\s+'
    )

    claims_or_attributes_re = re.compile(
        r'(?i)(?:'
        r'\bph\s*(?:skin|neutral|balanced?|level|\d+(?:\.\d+)?)\b'
        r'|\b(?:skin|body|scalp)\s*ph\b'
        r'|\b(?:paraben|soap|sulphate|sulfate|silicone|dye|microplastic|alcohol)[-\s]*free\b'
        r'|\b(?:microplastic|protecting|nourishing|cleansing)[-\s]*formula\b'
        r'|\bformula\s+with\b'
        r'|\b(?:skin|hair|scalp)\s+compatibility\b'
        r'|\bcompatibility\s+(?:tested|approved|dermatologically)\b'
        r'|\b(?:dermatolog[a-z]*|clinical[a-z]*|paediatric[a-z]*|pediatric[a-z]*|ophthalmolog[a-z]*)\s+(?:tested|proven|approved|certified)\b'
        r'|\bhypoallergenic\b'
        r'|\b(?:gentle|mild|soft|safe)\s+on\s+(?:the\s+)?(?:skin|hair|scalp|hands|body)\b'
        r'|\b(?:protects?|nourish(?:es)?|sooth(?:es)?|hydrates?|moisturiz(?:es)?|moisturis(?:es)?)\s+(?:your\s+|the\s+)?(?:skin|hair|scalp)\b'
        r'|\b(?:moisturiz(?:ed)?|moisturis(?:ed)?|hydrated)\s+skin\b'
        r'|\b(?:healthy|glowing|radiant|dry|oily|sensitive)\s+skin\s*$'
        r'|\b(?:suitable|ideal|formulated|crafted)\s+for\s+(?:all\s+)?(?:skin|hair|types?)\b'
        r'|\b(?:all|every)\s+(?:skin|hair)\s+types?\b'
        r'|\b(?:long|all-?day)\s+lasting\s+(?:freshness|fragrance|hydration|moisture|protection)\b'
        r'|\b(?:germ|bacterial|odour|odor)\s+protection\b'
        r')'
    )

    def is_declaration_or_header(val):
        """Returns True if text matches any declaration label, header, or section boundary."""
        if not val:
            return True
        if _is_field_label(val) or _looks_like_section_boundary(val):
            return True
        if instructional_steps_re.search(val) or dangling_prep_re.search(val) or leading_conj_re.search(val):
            return True
        if claims_or_attributes_re.search(val):
            return True
        if re.search(r'(?i)(?:feedback|complaints?|queries|query|careline|toll\s*free|(?:see|refer|read)\s*(?:above|below|side|bottom|pkg|pack|panel))', val):
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

    # Regex that matches strings which look like price/rate codes or batch identifiers
    # and therefore should never be treated as product names.
    _price_code_re = re.compile(
        r'(?i)'
        r'(?:'
        # price-like: digits optionally followed by /- or currency and more digits
        r'\d+(?:[.,]\d+)?\s*/?[-]?\s*\d*(?:\.\d+)?\s*/\s*(?:ml|g|kg|l|gm|unit)'
        r'|\d+\s*/[-]'
        r'|Rs\.?\s*\d+'
        r'|\d+\s*/-'
        # batch/code-like: standalone uppercase alphanumeric codes with digits mixed in
        r'|[A-Z]{1,4}\d{3,}'
        r'|\d{3,}[A-Z]{1,4}'
        # ratio/unit price patterns e.g. 0.72/ml
        r'|\d+\.\d+\s*/\s*[a-zA-Z]+'
        r')'
    )

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
        # Reject instructional step phrases
        if instructional_steps_re.search(normalized):
            return False
        # Reject trailing prepositions or conjunctions
        if dangling_prep_re.search(normalized) or leading_conj_re.search(normalized):
            return False
        # Reject claim and attribute phrases (benefits, testing, formula, skin attributes)
        if claims_or_attributes_re.search(normalized):
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
        if re.search(r'(?i)@|https?://|www\.|\.[a-z]{2,}\b|\b(?:mrp|net\s+(?:wt|qty)|telephone|phone|email|customer\s+care|country\s+of|trademark)\b|(?:feedback|complaints?|queries|query|careline|toll\s*free|(?:see|refer|read)\s*(?:above|below|side|bottom|pkg|pack|panel))', normalized):
            return False
        if re.match(r'^\d+$', normalized):
            return False
        norm_lower = normalized.lower()
        if any(norm_lower in used or used in norm_lower for used in used_values if len(used) > 2):
            return False
        # Must contain at least some meaningful alphabetic content
        alpha_words = re.findall(r'[A-Za-z]{2,}', normalized)
        # Require between 2 and 5 descriptive words
        if len(alpha_words) < 2 or len(alpha_words) > 5:
            return False
        # Reject price/code/batch-like strings (e.g. 'AA*180/-0.72/ml', 'B011 @10/28')
        if _price_code_re.search(normalized):
            return False
        # The string must not be dominated by non-alpha characters
        alpha_ratio = sum(1 for ch in normalized if ch.isalpha()) / max(len(normalized), 1)
        if alpha_ratio < 0.40:
            return False
        if bool(re.fullmatch(r'(?i)(?:product|information|details|label|select|of|in|everyday\s*protein)', normalized)):
            return False
        return True

    ordered = _reading_order(text_blocks)
    entity_start_pos = None
    for pos, (_, block) in enumerate(ordered):
        txt = block.get("text", "").strip()
        if re.search(r'(?i)\b(?:manufactured\s+by|mfg[./\s]*(?:by|for|pack|packed|pkd)|mfd[./\s]*(?:by|for|pack|packed|pkd)|marketed\s+by|packed\s+by|imported\s+by|manufacturer|packer)\b', txt):
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


def extract_fields(ocr_result: dict, calibration_px_per_mm: float = None) -> dict:
    """
    Converts raw OCR output dictionary into structured fields matching the rule engine contract.

    Expected input keys:
      - quality: dict with quality_status ('ACCEPTABLE', 'POOR', 'UNREADABLE')
      - full_text: str
      - text_blocks: list of dicts with 'text', 'confidence', 'box'

    Returns a dict covering Rules 1–12 extraction fields + batchNumber.
    Rule 12 (fontHeightMm) is None unless a valid positive calibration_px_per_mm is supplied.
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

    # -----------------------------------------------------------------------
    # Field Extractions using confidence-filtered text blocks
    # -----------------------------------------------------------------------
    mrp = _extract_mrp(filtered_text_blocks, filtered_full_text)
    net_qty = _extract_net_quantity(filtered_text_blocks, filtered_full_text)
    mfg_name, mfg_addr = _extract_manufacturer(filtered_text_blocks, filtered_full_text, raw_blocks=text_blocks)
    month_pkd, year_pkd = _extract_dates(filtered_text_blocks, filtered_full_text)
    exp_month, exp_year = _extract_expiry_date(filtered_text_blocks, filtered_full_text)  # Rule 10
    care_info = _extract_consumer_care(filtered_text_blocks, filtered_full_text)
    country_of_origin = _extract_country_of_origin(filtered_text_blocks, filtered_full_text)
    importer_name = _extract_importer(filtered_text_blocks, filtered_full_text)           # Rule 9
    unit_sale_price = _extract_unit_sale_price(filtered_text_blocks, filtered_full_text)  # Rule 11

    # Rule 12: font height mm — requires physical calibration reference.
    font_height_mm = _extract_font_height_mm(filtered_text_blocks, calibration_px_per_mm=calibration_px_per_mm)

    # Relative font-size comparison using direct OCR bounding-box heights in pixels.
    font_height_px_comparison = _extract_font_height_px_comparison(filtered_text_blocks)

    # Batch Number Extraction
    batch_number = _extract_batch_number(filtered_text_blocks, filtered_full_text, raw_blocks=text_blocks)

    known_values = [mrp, net_qty, mfg_name, mfg_addr, care_info]
    product_name = _extract_product_name(filtered_text_blocks, filtered_full_text, known_values)

    # -----------------------------------------------------------------------
    # Extraction Confidence — weighted field-completeness + quality signals
    #
    # HIGH requires:
    #   - ACCEPTABLE image quality
    #   - High mean OCR confidence (>= 0.50)
    #   - All four core statutory fields present (MRP, Net Qty, Mfg, Date)
    #   - Completeness score >= 3.5 (i.e., most mandatory fields filled)
    #
    # LOW:    POOR/UNREADABLE quality, OR completeness_score < 2.0
    # MEDIUM: everything else
    # -----------------------------------------------------------------------
    mrp_pts = 1.0 if mrp is not None else 0.0
    qty_pts = 1.0 if net_qty is not None else 0.0
    mfg_pts = 1.0 if (mfg_name is not None or mfg_addr is not None) else 0.0
    date_pts = (
        1.0 if (month_pkd is not None and year_pkd is not None)
        else (0.5 if (month_pkd is not None or year_pkd is not None) else 0.0)
    )
    care_pts = 0.5 if care_info is not None else 0.0
    prod_pts = 0.5 if product_name is not None else 0.0

    completeness_score = mrp_pts + qty_pts + mfg_pts + date_pts + care_pts + prod_pts

    confidences = [b.get("confidence", 1.0) for b in filtered_text_blocks]
    mean_ocr_conf = sum(confidences) / len(confidences) if confidences else 0.0

    if quality_status in ("POOR", "UNREADABLE") or completeness_score < 2.0:
        confidence_flag = "LOW"
    elif (
        quality_status == "ACCEPTABLE"
        and completeness_score >= 3.5
        and mean_ocr_conf >= 0.50
        and mrp is not None
        and net_qty is not None
        and (mfg_name is not None or mfg_addr is not None)
        and (month_pkd is not None or year_pkd is not None)
    ):
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
        "importerName": importer_name,           # Rule 9
        "netQuantity": net_qty,
        "mrp": mrp,
        "unitSalePrice": unit_sale_price,         # Rule 11
        "monthOfPacking": month_pkd,
        "yearOfPacking": year_pkd,
        "expiryMonth": exp_month,                 # Rule 10
        "expiryYear": exp_year,                   # Rule 10
        "consumerCare": care_info,
        "countryOfOrigin": country_of_origin,
        "fontHeightMm": font_height_mm,           # Rule 12 — always None without calibration
        "fontHeightPxComparison": font_height_px_comparison,
        "batchNumber": batch_number,
        "extraction_confidence": confidence_flag
    }

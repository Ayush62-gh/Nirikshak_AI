import re
from typing import Optional, Set, Tuple

# Official Legal Metrology (Packaged Commodities) Standard Units
LEGAL_METROLOGY_STANDARD_UNITS: Set[str] = {
    "g", "kg", "ml", "l", "m", "cm", "mm", "N", "U", "sq. m", "sq. cm", "cubic cm", "cubic m"
}

PINCODE_PATTERN = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_PATTERN = re.compile(
    r"(?:(?:\+|0{0,2})91[\s-]?)?(?:1800[\s-]?[0-9]{3}[\s-]?[0-9]{3,4}|[6-9][0-9]{9}|\d{3,5}[\s-]?\d{6,8})"
)
TAX_INCLUSIVE_PATTERN = re.compile(
    r"(?:incl\.?|inclusive)\s+(?:of\s+)?(?:all\s+)?taxes", re.IGNORECASE
)
DATE_PATTERN = re.compile(
    r"\b(?:0[1-9]|1[0-2]|[1-9])\s*[\/\.-]\s*(?:20\d{2}|19\d{2}|\d{2})\b|\b(?:0[1-9]|[12][0-9]|3[01])\s*[\/\.-]\s*(?:0[1-9]|1[0-2])\s*[\/\.-]\s*(?:20\d{2}|19\d{2}|\d{2})\b"
)


def is_valid_pincode(pincode: str) -> bool:
    """Validate 6-digit Indian PIN code."""
    if not pincode:
        return False
    return bool(PINCODE_PATTERN.search(pincode.strip()))


def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    return bool(EMAIL_PATTERN.fullmatch(email.strip()))


def is_valid_phone(phone: str) -> bool:
    """Validate phone/toll-free/customer care number."""
    if not phone:
        return False
    cleaned = re.sub(r"[\s\(\)-]", "", phone)
    return len(cleaned) >= 8 and bool(PHONE_PATTERN.search(phone))


def is_legal_unit(unit: str) -> bool:
    """Check whether a unit matches Legal Metrology prescribed standard units."""
    if not unit:
        return False
    return unit.strip() in LEGAL_METROLOGY_STANDARD_UNITS


def has_tax_inclusive_declaration(text: str) -> bool:
    """Check if the text specifies 'inclusive of all taxes' or 'incl. of all taxes'."""
    if not text:
        return False
    return bool(TAX_INCLUSIVE_PATTERN.search(text))

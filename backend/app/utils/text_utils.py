import re
from typing import List, Optional


def clean_ocr_text(text: str) -> str:
    """Clean and normalize OCR text output."""
    if not text:
        return ""
    # Normalize multiple whitespace and linebreaks
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    # Remove non-printable control characters except standard whitespace
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in ("\n", "\t"))
    return cleaned.strip()


def normalize_mrp_text(text: str) -> str:
    """Normalize common OCR misreadings in MRP strings."""
    t = text
    # Replace common OCR misreads like 'MRP : Rs .' -> 'MRP Rs.'
    t = re.sub(r"M\s*\.?\s*R\s*\.?\s*P\s*\.?", "MRP", t, flags=re.IGNORECASE)
    t = re.sub(r"R\s*s\s*\.?", "Rs.", t, flags=re.IGNORECASE)
    t = re.sub(r"₹\s*", "Rs. ", t)
    return t


def normalize_quantity_unit(unit_str: str) -> str:
    """Standardize unit representations to SI / Legal Metrology standard units."""
    unit = unit_str.strip().lower()
    unit_map = {
        "g": "g",
        "gm": "g",
        "gms": "g",
        "gram": "g",
        "grams": "g",
        "kg": "kg",
        "kgs": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "ml": "ml",
        "m.l.": "ml",
        "millilitre": "ml",
        "millilitres": "ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "l": "l",
        "ltr": "l",
        "litre": "l",
        "litres": "l",
        "liter": "l",
        "liters": "l",
        "m": "m",
        "meter": "m",
        "metre": "m",
        "meters": "m",
        "metres": "m",
        "cm": "cm",
        "mm": "mm",
        "n": "N",
        "nos": "N",
        "no": "N",
        "number": "N",
        "numbers": "N",
        "u": "U",
        "unit": "U",
        "units": "U",
        "pc": "N",
        "pcs": "N",
        "piece": "N",
        "pieces": "N",
    }
    return unit_map.get(unit, unit_str)

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re

from app.schemas.declaration import DeclarationBase
from app.services.ocr_service import OCRResult
from app.utils.text_utils import clean_ocr_text, normalize_mrp_text, normalize_quantity_unit
from app.utils.validators import (
    EMAIL_PATTERN,
    PINCODE_PATTERN,
    PHONE_PATTERN,
    has_tax_inclusive_declaration,
    is_legal_unit,
    is_valid_email,
    is_valid_phone,
    is_valid_pincode,
)


@dataclass
class ExtractedDeclaration:
    declaration_type: str
    extracted_value: str
    normalized_value: str
    confidence: float
    source_image: Optional[str] = None
    bounding_box: Optional[Dict[str, Any]] = None
    is_valid: bool = True


class DeclarationExtractor:
    """
    Extracts and normalizes Legal Metrology declarations from OCR text and bounding boxes.
    """

    @classmethod
    def extract_all(
        cls, ocr_result: OCRResult, image_path: Optional[str] = None
    ) -> List[ExtractedDeclaration]:
        """Extract all legal metrology declarations from OCR results."""
        text = ocr_result.full_text
        source = image_path or ocr_result.image_path
        declarations: List[ExtractedDeclaration] = []

        # 1. Extract MRP
        mrp_dec = cls.extract_mrp(text, source)
        if mrp_dec:
            declarations.append(mrp_dec)

        # 2. Extract Net Quantity
        qty_dec = cls.extract_net_quantity(text, source)
        if qty_dec:
            declarations.append(qty_dec)

        # 3. Extract Dates (Manufacturing / Packaging / Expiry)
        date_decs = cls.extract_dates(text, source)
        declarations.extend(date_decs)

        # 4. Extract Manufacturer Details
        mfg_dec = cls.extract_manufacturer(text, source)
        if mfg_dec:
            declarations.append(mfg_dec)

        # 5. Extract Packer / Importer Details
        packer_dec = cls.extract_packer(text, source)
        if packer_dec:
            declarations.append(packer_dec)

        importer_dec = cls.extract_importer(text, source)
        if importer_dec:
            declarations.append(importer_dec)

        # 6. Extract Consumer Care Details (Phone, Email, Address)
        cc_decs = cls.extract_consumer_care(text, source)
        declarations.extend(cc_decs)

        # 7. Extract Country of Origin
        coo_dec = cls.extract_country_of_origin(text, source)
        if coo_dec:
            declarations.append(coo_dec)

        return declarations

    @classmethod
    def extract_mrp(cls, text: str, source: str) -> Optional[ExtractedDeclaration]:
        """Extract and validate MRP declaration and tax clause."""
        # Pattern: MRP Rs. 85.00 (incl. of all taxes)
        mrp_pattern = re.compile(
            r"(?:M\.?R\.?P\.?|MAXIMUM\s+RETAIL\s+PRICE)\s*[:\.\-]?\s*(?:Rs\.?|₹|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:[/-])?\s*([^\n\r]*)",
            re.IGNORECASE,
        )
        match = mrp_pattern.search(text)
        if match:
            amount_str = match.group(1).strip()
            suffix = match.group(2).strip()
            full_match_text = match.group(0).strip()

            has_tax = has_tax_inclusive_declaration(full_match_text) or has_tax_inclusive_declaration(text)
            normalized = f"Rs. {amount_str}" + (" (incl. of all taxes)" if has_tax else "")

            return ExtractedDeclaration(
                declaration_type="mrp",
                extracted_value=full_match_text,
                normalized_value=normalized,
                confidence=0.95 if has_tax else 0.85,
                source_image=source,
                is_valid=has_tax,  # Legal Metrology Rule 6(1)(e) requires inclusive of taxes
            )
        return None

    @classmethod
    def extract_net_quantity(cls, text: str, source: str) -> Optional[ExtractedDeclaration]:
        """Extract and validate net quantity and standard unit."""
        qty_pattern = re.compile(
            r"(?:Net\s*(?:Qty|Quantity|Wt|Weight|Content|Volume|Mass)?\s*[:\.\-]?\s*)([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z\.\s]+)",
            re.IGNORECASE,
        )
        match = qty_pattern.search(text)
        if match:
            value_str = match.group(1).strip()
            raw_unit = match.group(2).split()[0].strip()
            norm_unit = normalize_quantity_unit(raw_unit)
            full_match = f"Net Qty: {value_str} {raw_unit}"

            valid_unit = is_legal_unit(norm_unit)
            normalized = f"{value_str} {norm_unit}"

            return ExtractedDeclaration(
                declaration_type="net_quantity",
                extracted_value=match.group(0).strip(),
                normalized_value=normalized,
                confidence=0.95 if valid_unit else 0.80,
                source_image=source,
                is_valid=valid_unit,
            )
        return None

    @classmethod
    def extract_dates(cls, text: str, source: str) -> List[ExtractedDeclaration]:
        """Extract Manufacturing date, Packing date, and Best before / Expiry."""
        results: List[ExtractedDeclaration] = []

        # Manufacturing Date
        mfg_pattern = re.compile(
            r"(?:Mfg\.?\s*Date|Manufactured\s*on|Date\s*of\s*Mfg|Mfg\b)\s*[:\.\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{2,4}|[A-Za-z]{3,9}\s*[\/\.\-]?[0-9]{2,4})",
            re.IGNORECASE,
        )
        mfg_match = mfg_pattern.search(text)
        if mfg_match:
            results.append(
                ExtractedDeclaration(
                    declaration_type="mfg_date",
                    extracted_value=mfg_match.group(0).strip(),
                    normalized_value=mfg_match.group(1).strip(),
                    confidence=0.92,
                    source_image=source,
                    is_valid=True,
                )
            )

        # Packed Date
        pkd_pattern = re.compile(
            r"(?:Pkd\.?\s*Date|Packed\s*on|Date\s*of\s*Packing|Pkd\b)\s*[:\.\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{2,4}|[A-Za-z]{3,9}\s*[\/\.\-]?[0-9]{2,4})",
            re.IGNORECASE,
        )
        pkd_match = pkd_pattern.search(text)
        if pkd_match:
            results.append(
                ExtractedDeclaration(
                    declaration_type="pkd_date",
                    extracted_value=pkd_match.group(0).strip(),
                    normalized_value=pkd_match.group(1).strip(),
                    confidence=0.92,
                    source_image=source,
                    is_valid=True,
                )
            )

        # Best Before / Expiry
        exp_pattern = re.compile(
            r"(?:Best\s*Before|Expiry\s*Date|Exp\.?\s*Date|Use\s*by)\s*[:\.\-]?\s*([^\n\r]+)",
            re.IGNORECASE,
        )
        exp_match = exp_pattern.search(text)
        if exp_match:
            results.append(
                ExtractedDeclaration(
                    declaration_type="expiry_date",
                    extracted_value=exp_match.group(0).strip(),
                    normalized_value=exp_match.group(1).strip(),
                    confidence=0.90,
                    source_image=source,
                    is_valid=True,
                )
            )

        return results

    @classmethod
    def extract_manufacturer(cls, text: str, source: str) -> Optional[ExtractedDeclaration]:
        """Extract manufacturer name and complete address including PIN code."""
        mfg_pattern = re.compile(
            r"(?:Manufactured\s*(?:and\s*Marketed)?\s*by|Mfg\s*by|Mfd\s*by|Produced\s*by)\s*[:\.\-]?\s*([^\n\r]+(?:\n[^\n\r]+){0,3})",
            re.IGNORECASE,
        )
        match = mfg_pattern.search(text)
        if match:
            val = match.group(0).strip()
            # Clean newlines into single string
            cleaned_val = " ".join(val.split())
            has_pincode = is_valid_pincode(cleaned_val)

            return ExtractedDeclaration(
                declaration_type="manufacturer",
                extracted_value=cleaned_val,
                normalized_value=cleaned_val,
                confidence=0.92 if has_pincode else 0.80,
                source_image=source,
                is_valid=True,
            )
        return None

    @classmethod
    def extract_packer(cls, text: str, source: str) -> Optional[ExtractedDeclaration]:
        """Extract packer details."""
        packer_pattern = re.compile(
            r"(?:Packed\s*by|Pkd\s*by|Packaging\s*by)\s*[:\.\-]?\s*([^\n\r]+(?:\n[^\n\r]+){0,2})",
            re.IGNORECASE,
        )
        match = packer_pattern.search(text)
        if match:
            cleaned = " ".join(match.group(0).strip().split())
            return ExtractedDeclaration(
                declaration_type="packer",
                extracted_value=cleaned,
                normalized_value=cleaned,
                confidence=0.90,
                source_image=source,
                is_valid=True,
            )
        return None

    @classmethod
    def extract_importer(cls, text: str, source: str) -> Optional[ExtractedDeclaration]:
        """Extract importer details (if present)."""
        importer_pattern = re.compile(
            r"(?:Imported\s*(?:and\s*Marketed)?\s*by|Imp\s*by)\s*[:\.\-]?\s*([^\n\r]+(?:\n[^\n\r]+){0,2})",
            re.IGNORECASE,
        )
        match = importer_pattern.search(text)
        if match:
            cleaned = " ".join(match.group(0).strip().split())
            return ExtractedDeclaration(
                declaration_type="importer",
                extracted_value=cleaned,
                normalized_value=cleaned,
                confidence=0.90,
                source_image=source,
                is_valid=True,
            )
        return None

    @classmethod
    def extract_consumer_care(cls, text: str, source: str) -> List[ExtractedDeclaration]:
        """Extract consumer care email, phone/toll-free, and address."""
        results: List[ExtractedDeclaration] = []

        # 1. Email
        emails = EMAIL_PATTERN.findall(text)
        if emails:
            primary_email = emails[0]
            results.append(
                ExtractedDeclaration(
                    declaration_type="consumer_care_email",
                    extracted_value=primary_email,
                    normalized_value=primary_email.lower(),
                    confidence=0.98,
                    source_image=source,
                    is_valid=is_valid_email(primary_email),
                )
            )

        # 2. Phone / Toll-free
        phone_match = PHONE_PATTERN.search(text)
        if phone_match:
            phone_str = phone_match.group(0).strip()
            results.append(
                ExtractedDeclaration(
                    declaration_type="consumer_care_phone",
                    extracted_value=phone_str,
                    normalized_value=re.sub(r"[^\d+]", "", phone_str),
                    confidence=0.95,
                    source_image=source,
                    is_valid=is_valid_phone(phone_str),
                )
            )

        # 3. Consumer Care Address / Cell
        cc_cell_pattern = re.compile(
            r"(?:Consumer\s*Care\s*(?:Cell|Officer|Executive|Details)?|Customer\s*Care\s*(?:Cell|Officer|Executive|Details)?)\s*[:\.\-]?\s*([^\n\r]+(?:\n[^\n\r]+){0,2})",
            re.IGNORECASE,
        )
        cc_match = cc_cell_pattern.search(text)
        if cc_match:
            cleaned = " ".join(cc_match.group(0).strip().split())
            results.append(
                ExtractedDeclaration(
                    declaration_type="consumer_care_address",
                    extracted_value=cleaned,
                    normalized_value=cleaned,
                    confidence=0.90,
                    source_image=source,
                    is_valid=True,
                )
            )

        return results

    @classmethod
    def extract_country_of_origin(cls, text: str, source: str) -> Optional[ExtractedDeclaration]:
        """Extract Country of Origin."""
        coo_pattern = re.compile(
            r"(?:Country\s*of\s*Origin|Made\s*in)\s*[:\.\-]?\s*([A-Za-z\s]+)",
            re.IGNORECASE,
        )
        match = coo_pattern.search(text)
        if match:
            raw_country = match.group(1).split("\n")[0].strip()
            return ExtractedDeclaration(
                declaration_type="country_of_origin",
                extracted_value=match.group(0).strip(),
                normalized_value=raw_country.title(),
                confidence=0.94,
                source_image=source,
                is_valid=len(raw_country) >= 3,
            )
        return None

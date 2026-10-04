"""
Regression and new-field tests for Nirikshak AI OCR extraction.

Covers:
- Issue 1: MRP false positive (net-qty value mistaken for MRP)
- Issue 2: Product name false positive (price/code-like strings)
- Issue 3: Manufacturer false positive
- Issue 4: Manufacturer address
- Issue 5: Date extraction safety
- Issue 6: Consumer care extraction
- Rule 9:  importerName
- Rule 10: expiryDate (expiryMonth / expiryYear)
- Rule 11: unitSalePrice
- Rule 12: fontHeightMm (always None without calibration)
- Multi-image: new fields included in merging
- Confidence: improved semantics
"""

import pytest
from field_extractor import extract_fields


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_block(text, confidence=0.90, x=0, y=0, w=200, h=20):
    return {
        "text": text,
        "confidence": confidence,
        "box": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
    }


def _ocr(blocks, quality_status="ACCEPTABLE"):
    return {
        "quality": {"quality_status": quality_status},
        "full_text": " ".join(b["text"] for b in blocks),
        "text_blocks": blocks,
    }


# ===========================================================================
# ISSUE 1 — MRP false positive: net-quantity value must never become MRP
# ===========================================================================

def test_mrp_false_positive_250ml_nearby():
    """
    Regression: OCR 'MRP INCLOF ALL TAXES' followed nearby by '250ml'
    must NOT produce MRP Rs. 250.00.  Net-quantity context blocks are
    explicitly excluded from the MRP nearby-block scan.
    """
    blocks = [
        _make_block("MRP INCLOF ALL TAXES", 0.85, y=0),
        _make_block("250ml", 0.90, y=25),   # Net quantity — must NOT become MRP
    ]
    result = extract_fields(_ocr(blocks))
    # No price number in the MRP label block itself → MRP must be None
    assert result["mrp"] is None
    # Net quantity should remain 250ml
    assert result["netQuantity"] == "250ml"


def test_mrp_false_positive_500g_as_nearby():
    """500g must never be treated as MRP Rs. 500."""
    blocks = [
        _make_block("MRP (Incl. of all taxes)", 0.88, y=0),
        _make_block("500 g", 0.92, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["mrp"] is None
    assert result["netQuantity"] is not None
    assert "500" in result["netQuantity"]


def test_mrp_false_positive_1kg():
    """1kg near MRP label must not yield MRP Rs. 1.00."""
    blocks = [
        _make_block("MRP incl of all taxes", 0.88, y=0),
        _make_block("1kg", 0.92, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["mrp"] is None


def test_mrp_explicit_price_still_works():
    """Explicit MRP with a real price must still be extracted correctly."""
    blocks = [
        _make_block("MRP Rs. 120.00 (incl. of all taxes)", 0.94),
        _make_block("Net Qty 250ml", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["mrp"] is not None
    assert "120.00" in result["mrp"]
    assert result["netQuantity"] is not None


# ===========================================================================
# ISSUE 2 — Product name false positive: price/code strings rejected
# ===========================================================================

def test_product_name_rejects_price_code_string():
    """
    Regression: 'AA*180/-0.72/ml' must never be extracted as productName.
    """
    blocks = [
        _make_block("AA*180/-0.72/ml", 0.90, y=0),
        _make_block("Net Wt 200g", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] is None or "AA*180" not in result["productName"]


def test_product_name_rejects_batch_code_like_value():
    """Batch/code-like strings must not become product name."""
    for garbage in ["B011 @10/28", "XJ4902", "0.72/ml", "250/-"]:
        blocks = [_make_block(garbage, 0.95, y=0)]
        result = extract_fields(_ocr(blocks))
        assert result["productName"] is None, f"Should reject: {garbage!r}"


def test_product_name_rejects_symbol_dominated_string():
    """Strings with high symbol ratio are rejected."""
    blocks = [
        _make_block("##@250!!/ml", 0.95, y=0),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] is None


def test_product_name_valid_name_still_passes():
    """Generic product names are still correctly extracted."""
    blocks = [
        _make_block("Common Generic Name", 0.92, y=0),
        _make_block("Aloe Vera Gel", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] == "Aloe Vera Gel"


def test_product_name_rejects_3_steps_for():
    """A. '3 Steps for' → rejected as productName"""
    blocks = [
        _make_block("3 Steps for", 0.92, y=0),
        _make_block("Net Wt 250ml", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] is None


def test_product_name_rejects_steps_for_glowing():
    """B. 'Steps for Glowing' → rejected"""
    blocks = [
        _make_block("Steps for Glowing", 0.92, y=0),
        _make_block("Net Wt 250ml", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] is None


def test_product_name_rejects_follow_these_steps():
    """C. 'Follow these steps' → rejected"""
    blocks = [
        _make_block("Follow these steps", 0.92, y=0),
        _make_block("Net Wt 250ml", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] is None


def test_product_name_legitimate_unlabeled_multi_word_still_works():
    """D. A legitimate unlabeled multi-word product name still works"""
    blocks = [
        _make_block("Shower Gel", 0.95, y=0),
        _make_block("Net Qty 250ml", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] == "Shower Gel"


def test_product_name_existing_explicit_label_still_works():
    """E. Existing explicit product-name label still works"""
    blocks = [
        _make_block("Product Name: Nourishing Body Wash", 0.95, y=0),
        _make_block("Net Qty 250ml", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["productName"] == "Nourishing Body Wash"


# ===========================================================================
# ISSUE 3 — Manufacturer false positive
# ===========================================================================

def test_manufacturer_vitaminc_not_extracted_without_anchor():
    """
    Regression: A word like 'VITAMINC' that looks like a company suffix
    but has no manufacturer-label anchor nearby must NOT become manufacturerName.
    """
    blocks = [
        _make_block("VITAMINC", 0.90, y=0),
        _make_block("Supplement Facts", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] is None or result["manufacturerName"] != "VITAMINC"


def test_manufacturer_explicit_label_highest_priority():
    """Explicit 'Manufacturer:' label wins over company-suffix-only fallback."""
    blocks = [
        _make_block("Manufacturer: ABC Industries Pvt. Ltd.", 0.92, y=0),
        _make_block("XYZ Foods Limited", 0.90, y=200),  # far away, no anchor
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] == "ABC Industries Pvt. Ltd."


def test_manufacturer_labelled_forms_all_recognized():
    """All recognised manufacturer label variants are correctly parsed."""
    from field_extractor import _extract_manufacturer
    for label_prefix in [
        "Manufacturer: ABC Industries Pvt. Ltd.",
        "Manufactured By: ABC Industries Pvt. Ltd.",
        "Mfg By: ABC Industries Pvt. Ltd.",
        "Mfg. By : ABC Industries Pvt. Ltd.",
        "Mfd By: ABC Industries Pvt. Ltd.",
    ]:
        blocks = [{"text": label_prefix}]
        name, _ = _extract_manufacturer(blocks, label_prefix)
        assert name is not None, f"Failed for: {label_prefix!r}"
        assert "ABC Industries" in name, f"Wrong name for: {label_prefix!r}"


# ===========================================================================
# ISSUE 4 — Manufacturer address
# ===========================================================================

def test_manufacturer_address_stays_with_correct_entity():
    """Manufacturer address follows the correct entity, not the closest company block."""
    blocks = [
        _make_block("Manufactured by Apex Foods Limited", 0.92, y=0),
        _make_block("Plot 10 Sector 4 Noida", 0.90, y=25),
        _make_block("Marketed by Beta Brands Limited", 0.90, y=60),
        _make_block("Park Street Delhi", 0.90, y=85),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] == "Apex Foods Limited"
    assert result["manufacturerAddress"] is not None
    assert "Noida" in result["manufacturerAddress"] or "Plot 10" in result["manufacturerAddress"]


def test_manufacturer_address_stops_at_boundary_section():
    """Address collection must stop at FSSAI / storage-instructions boundary."""
    blocks = [
        _make_block("Manufactured by Gamma Pvt Ltd", 0.92, y=0),
        _make_block("Phase 2 Industrial Area", 0.90, y=25),
        _make_block("FSSAI Lic No 123456789012", 0.88, y=50),
        _make_block("Storage: Store in cool dry place", 0.90, y=75),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerAddress"] is not None
    assert "FSSAI" not in result["manufacturerAddress"]
    assert "Storage" not in result["manufacturerAddress"]


def test_manufacturer_address_does_not_pick_unrelated_text():
    """Address must not grab unrelated text that follows a boundary keyword."""
    blocks = [
        _make_block("Manufactured by Delta Corp Ltd", 0.92, y=0),
        _make_block("MRP Rs. 150", 0.90, y=25),   # boundary — MRP section
        _make_block("MG Road Bangalore", 0.90, y=50),
    ]
    result = extract_fields(_ocr(blocks))
    # Address after an MRP boundary must not be picked up
    if result["manufacturerAddress"] is not None:
        assert "MG Road" not in result["manufacturerAddress"]


# ===========================================================================
# ISSUE 5 — Date extraction safety
# ===========================================================================

def test_manufacturing_date_extracted_with_explicit_label():
    """Mfg date extracted when label is present."""
    blocks = [_make_block("Mfg Date: 03/2025", 0.92)]
    result = extract_fields(_ocr(blocks))
    assert result["monthOfPacking"] == "03"
    assert result["yearOfPacking"] == "2025"


def test_expiry_date_not_assigned_to_packing_date():
    """Expiry date must not pollute monthOfPacking/yearOfPacking."""
    blocks = [
        _make_block("Expiry Date: 06/2028", 0.92, y=0),
        _make_block("Best Before 12 Months", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["monthOfPacking"] is None
    assert result["yearOfPacking"] is None


def test_batch_code_not_interpreted_as_date():
    """
    OCR artefact 'B011 @10/28' — batch number/code nearby must not
    be extracted as manufacturing or expiry date without context.
    """
    blocks = [
        _make_block("MFD.NOUSEBEFORE:", 0.88, y=0),
        _make_block("05/26 B011 @10/28", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    # There's no clear MFG date context (the label says NOUSEBEFORE which is expiry)
    # and 10/28 is ambiguous. The extractor should not confidently assign a mfg date.
    # Either None or a clearly supported date is acceptable.
    # Specifically the batch token B011 must not be the month/year.
    if result["monthOfPacking"] is not None:
        assert result["monthOfPacking"] in {"05", "10"}, (
            f"Unexpected monthOfPacking: {result['monthOfPacking']}"
        )


def test_ambiguous_date_without_context_not_extracted():
    """An isolated numeric pattern without any mfg/exp context must not be extracted."""
    blocks = [
        _make_block("Batch: 4492", 0.90, y=0),
        _make_block("07/2024", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    # No manufacturing label → monthOfPacking must be None
    assert result["monthOfPacking"] is None
    assert result["yearOfPacking"] is None


def test_dom_label_correctly_extracts_mfg_date():
    """DOM label correctly extracts manufacturing date."""
    blocks = [_make_block("DOM: 08/2026", 0.91)]
    result = extract_fields(_ocr(blocks))
    assert result["monthOfPacking"] == "08"
    assert result["yearOfPacking"] == "2026"


# ===========================================================================
# ISSUE 6 — Consumer care extraction
# ===========================================================================

def test_consumer_care_toll_free_extracted():
    """Toll-free number with consumer care label is extracted."""
    blocks = [
        _make_block("Consumer Care: 1800-103-1929", 0.90, y=0),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["consumerCare"] is not None
    assert "1800-103-1929" in result["consumerCare"]


def test_consumer_care_email_and_phone():
    """Both phone and email are extracted when present."""
    blocks = [
        _make_block("Toll Free: 1800-222-3344", 0.90, y=0),
        _make_block("Email: help@example.com", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["consumerCare"] is not None
    assert "1800-222-3344" in result["consumerCare"]
    assert "help@example.com" in result["consumerCare"]


def test_consumer_care_website_requires_care_label():
    """
    A website URL present without any consumer-care label must NOT be extracted
    as consumerCare.  Only care-labelled contexts warrant website extraction.
    """
    blocks = [
        _make_block("Net Wt 200g", 0.90, y=0),
        _make_block("www.someproduct.com", 0.90, y=25),  # no care label nearby
    ]
    result = extract_fields(_ocr(blocks))
    # No care label → website should NOT be in consumerCare
    assert result["consumerCare"] is None or "someproduct.com" not in result["consumerCare"]


def test_consumer_care_website_with_care_label():
    """Website extracted when a care label is present."""
    blocks = [
        _make_block("Customer Care:", 0.90, y=0),
        _make_block("www.helpdesk.com", 0.90, y=0, x=150),
    ]
    result = extract_fields(_ocr(blocks))
    # With a care label, website should be included
    assert result["consumerCare"] is not None
    assert "helpdesk.com" in result["consumerCare"]


def test_consumer_care_no_invented_contact():
    """Without any phone/email/website, consumerCare must be None."""
    blocks = [
        _make_block("Net Wt 100g", 0.92, y=0),
        _make_block("MRP Rs. 50.00", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["consumerCare"] is None


# ===========================================================================
# RULE 9 — importerName
# ===========================================================================

def test_importer_name_imported_by():
    """'Imported By:' label recognized."""
    blocks = [_make_block("Imported By: Zeta Trading Pvt. Ltd.", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is not None
    assert "Zeta Trading" in result["importerName"]


def test_importer_name_importer_label():
    """'Importer:' label recognized."""
    blocks = [_make_block("Importer: Alpha Import Co. Ltd.", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is not None
    assert "Alpha Import" in result["importerName"]


def test_importer_name_importer_name_label():
    """'Importer Name:' label recognized."""
    blocks = [_make_block("Importer Name: Beta Importers Limited", 0.92)]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is not None
    assert "Beta Importers" in result["importerName"]


def test_importer_name_imp_by_label():
    """'IMP BY:' label recognized."""
    blocks = [_make_block("IMP BY: Gamma International Ltd.", 0.88)]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is not None
    assert "Gamma International" in result["importerName"]


def test_importer_name_import_marketed_by():
    """'Import & Marketed By:' label recognized."""
    blocks = [_make_block("Import & Marketed By: Delta Corp Ltd.", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is not None
    assert "Delta Corp" in result["importerName"]


def test_importer_name_not_extracted_without_label():
    """Without an importer label, importerName must be None."""
    blocks = [
        _make_block("Epsilon Global Limited", 0.92, y=0),
        _make_block("Some Road Some City", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is None


def test_importer_name_does_not_confuse_manufacturer():
    """Manufacturer label must not produce an importerName."""
    blocks = [_make_block("Manufactured By: Omega Foods Pvt. Ltd.", 0.92)]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is None


def test_importer_name_not_hardcoded_no_label():
    """Arbitrary company name with no importer label → None."""
    blocks = [
        _make_block("Zeta Overseas Trading Limited", 0.90),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["importerName"] is None


# ===========================================================================
# RULE 10 — expiryDate (expiryMonth / expiryYear)
# ===========================================================================

def test_expiry_date_exp_label():
    """'Exp:' label extracts expiry date."""
    blocks = [_make_block("Exp: 10/2027", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] == "10"
    assert result["expiryYear"] == "2027"


def test_expiry_date_expiry_label():
    """'Expiry Date:' label extracts expiry date."""
    blocks = [_make_block("Expiry Date: 06/2029", 0.92)]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] == "06"
    assert result["expiryYear"] == "2029"


def test_expiry_date_use_before_label():
    """'Use Before:' label extracts expiry date."""
    blocks = [_make_block("Use Before: 04/2026", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] == "04"
    assert result["expiryYear"] == "2026"


def test_expiry_date_best_before_label():
    """'Best Before:' label extracts expiry date."""
    blocks = [_make_block("Best Before: 12/2025", 0.91)]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] == "12"
    assert result["expiryYear"] == "2025"


def test_expiry_date_not_confused_with_mfg_date():
    """Mfg date must NOT populate expiryMonth/expiryYear."""
    blocks = [
        _make_block("Mfg Date: 08/2024", 0.92, y=0),
        _make_block("Use Before: 08/2026", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] == "08"
    assert result["expiryYear"] == "2026"
    assert result["monthOfPacking"] == "08"
    assert result["yearOfPacking"] == "2024"


def test_expiry_date_manufacturing_date_nearby_does_not_contaminate():
    """A manufacturing date block nearby must not produce expiryMonth."""
    blocks = [
        _make_block("Mfg Date: 08/2024", 0.92, y=0),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] is None
    assert result["expiryYear"] is None


def test_expiry_date_batch_code_not_expiry():
    """Batch numbers are not extracted as expiry dates."""
    blocks = [
        _make_block("Batch No: BR2E1728", 0.90, y=0),
        _make_block("06/2029", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    # 06/2029 is nearby a batch block only — no expiry label → should be None
    assert result["expiryMonth"] is None
    assert result["expiryYear"] is None


def test_expiry_date_null_without_expiry_context():
    """Without expiry label, expiryMonth and expiryYear must be None."""
    blocks = [
        _make_block("Net Wt 200g", 0.92, y=0),
        _make_block("08/2026", 0.90, y=25),  # ambiguous date, no label
    ]
    result = extract_fields(_ocr(blocks))
    assert result["expiryMonth"] is None
    assert result["expiryYear"] is None


# ===========================================================================
# RULE 11 — unitSalePrice
# ===========================================================================

def test_unit_sale_price_explicit_label():
    """'Unit Sale Price:' label extracts unitSalePrice."""
    blocks = [_make_block("Unit Sale Price: Rs. 100.00", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["unitSalePrice"] is not None
    assert "100" in result["unitSalePrice"]


def test_unit_sale_price_unit_price_label():
    """'Unit Price:' label extracts unitSalePrice."""
    blocks = [_make_block("Unit Price: Rs. 50.00", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["unitSalePrice"] is not None
    assert "50" in result["unitSalePrice"]


def test_unit_sale_price_per_100ml_label():
    """'Rs./100ml' context extracts unitSalePrice."""
    blocks = [_make_block("Rs./100ml 40.00", 0.90)]
    result = extract_fields(_ocr(blocks))
    assert result["unitSalePrice"] is not None
    assert "40" in result["unitSalePrice"]


def test_unit_sale_price_separate_from_mrp():
    """unitSalePrice and mrp must remain separate fields."""
    blocks = [
        _make_block("MRP Rs. 250.00", 0.92, y=0),
        _make_block("Net Quantity 250ml", 0.90, y=25),
        _make_block("Unit Sale Price Rs. 100.00/100ml", 0.90, y=50),
    ]
    result = extract_fields(_ocr(blocks))
    # All three should be distinct
    assert result["mrp"] is not None
    assert "250" in result["mrp"]
    assert result["netQuantity"] is not None
    assert "250" in result["netQuantity"]
    assert result["unitSalePrice"] is not None
    assert "100" in result["unitSalePrice"]


def test_unit_sale_price_net_qty_never_becomes_unit_price():
    """Net quantity (250ml, 500g) must never become unitSalePrice."""
    blocks = [
        _make_block("Net Qty 250ml", 0.90, y=0),
        _make_block("MRP Rs. 150.00", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["unitSalePrice"] is None


def test_unit_sale_price_random_number_not_extracted():
    """A random numeric token without unit-price label must not become unitSalePrice."""
    blocks = [
        _make_block("Serial 12345", 0.90, y=0),
        _make_block("Batch XZ99", 0.90, y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["unitSalePrice"] is None


def test_unit_sale_price_null_without_label():
    """Without a unit-price label, unitSalePrice must be None."""
    blocks = [
        _make_block("MRP Rs. 120.00", 0.90, y=0),
        _make_block("Net Qty 200g", 0.90, y=25),
        _make_block("Mfg by Example Foods Ltd", 0.90, y=50),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["unitSalePrice"] is None


# ===========================================================================
# RULE 12 — fontHeightMm
# ===========================================================================

def test_font_height_mm_is_none_without_calibration():
    """
    Rule 12: fontHeightMm must be None when no calibration reference is
    available.  Pixels must never be returned as millimetres.
    """
    blocks = [
        _make_block("MRP Rs. 120.00", 0.92, y=0, w=300, h=30),
        _make_block("Net Qty 200g", 0.90, y=35, w=200, h=20),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["fontHeightMm"] is None, (
        "fontHeightMm must be None without calibration — pixels != mm"
    )


def test_font_height_mm_present_in_output_schema():
    """fontHeightMm key must always be present in extract_fields output."""
    result = extract_fields({"quality": {"quality_status": "ACCEPTABLE"}, "full_text": "", "text_blocks": []})
    assert "fontHeightMm" in result


def test_font_height_mm_calibrated_returns_value():
    """When calibration is provided, _extract_font_height_mm returns a mm value."""
    from field_extractor import _extract_font_height_mm
    blocks = [
        {"text": "MRP Rs. 50", "confidence": 0.9, "box": [[0, 0], [100, 0], [100, 40], [0, 40]]},
    ]
    # 40 pixels / 5.0 px_per_mm = 8.0 mm
    result = _extract_font_height_mm(blocks, calibration_px_per_mm=5.0)
    assert result == 8.0


def test_font_height_mm_calibrated_none_on_empty():
    """Calibrated path returns None when no blocks have geometry."""
    from field_extractor import _extract_font_height_mm
    result = _extract_font_height_mm([], calibration_px_per_mm=5.0)
    assert result is None


# ===========================================================================
# Multi-image: new fields included in merging
# ===========================================================================

def test_multi_image_new_fields_in_schema():
    """
    All new Rule 9-12 fields must appear in extract_fields output schema.
    """
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Imported By: Test Importers Ltd Net Qty 100g MRP Rs. 50.00 Mfg by Example Ltd 05/2025",
        "text_blocks": [
            _make_block("Imported By: Test Importers Ltd", 0.90, y=0),
            _make_block("Net Qty 100g", 0.90, y=25),
            _make_block("MRP Rs. 50.00", 0.90, y=50),
            _make_block("Mfg by Example Ltd", 0.90, y=75),
            _make_block("05/2025", 0.90, y=100),
        ]
    })
    assert "importerName" in result
    assert "expiryMonth" in result
    assert "expiryYear" in result
    assert "unitSalePrice" in result
    assert "fontHeightMm" in result


def test_multi_image_importer_extracted_correctly():
    """importerName extracted correctly in a full multi-field scenario."""
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Imported By: Acme Overseas Ltd.",
        "text_blocks": [_make_block("Imported By: Acme Overseas Ltd.", 0.90)],
    })
    assert result["importerName"] is not None
    assert "Acme Overseas" in result["importerName"]


# ===========================================================================
# Confidence semantics
# ===========================================================================

def test_confidence_high_requires_all_core_fields():
    """HIGH confidence requires MRP + Net Qty + Mfg + Date at ACCEPTABLE quality."""
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Product Net Qty 100g MRP Rs 50.00 Mfg by Example Ltd 05/2025 Care 1800-100-100",
        "text_blocks": [
            _make_block("Net Qty 100g", 0.92, y=0),
            _make_block("MRP Rs 50.00", 0.90, y=25),
            _make_block("Mfg by Example Ltd", 0.90, y=50),
            _make_block("05/2025", 0.91, y=75),
            _make_block("Care 1800-100-100", 0.88, y=100),
        ]
    })
    assert result["extraction_confidence"] == "HIGH"


def test_confidence_low_when_poor_quality():
    """POOR quality image always yields LOW confidence."""
    result = extract_fields({
        "quality": {"quality_status": "POOR"},
        "full_text": "Net Qty 100g MRP Rs 50.00 Mfg by Example Ltd 05/2025",
        "text_blocks": [
            _make_block("Net Qty 100g", 0.92, y=0),
            _make_block("MRP Rs 50.00", 0.90, y=25),
        ]
    })
    assert result["extraction_confidence"] == "LOW"


def test_confidence_medium_when_date_missing():
    """Missing packing date downgrades HIGH to MEDIUM."""
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Shower Gel Net Qty 250ml MRP Rs. 175.00 Mfg by Example Ltd",
        "text_blocks": [
            _make_block("Shower Gel", 0.90, y=0),
            _make_block("Net Qty 250ml", 0.90, y=25),
            _make_block("MRP Rs. 175.00", 0.90, y=50),
            _make_block("Mfg by Example Ltd", 0.90, y=75),
        ]
    })
    assert result["extraction_confidence"] == "MEDIUM"


def test_confidence_low_on_sparse_fields():
    """Only one field extracted → LOW confidence."""
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Net Wt 200g",
        "text_blocks": [_make_block("Net Wt 200g", 0.95)],
    })
    assert result["extraction_confidence"] == "LOW"


# ===========================================================================
# ISSUE: Manufacturer extraction robustness with OCR-corrupted / split labels
# ===========================================================================

def test_manufacturer_marketed_by_existing():
    """A. Existing: 'Marketed by: ABC India Pvt. Ltd.' -> manufacturerName = 'ABC India Pvt. Ltd.'"""
    blocks = [_make_block("Marketed by: ABC India Pvt. Ltd.", y=0)]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] == "ABC India Pvt. Ltd."


def test_manufacturer_marketed_by_ocr_split():
    """
    B. OCR-split:
    Block 1: 'Marketed by ABC India'
    Block 2: 'Pvt. Ltd., Industrial Area...'
    -> correctly extract company name.
    """
    blocks = [
        _make_block("Marketed by ABC India", y=0),
        _make_block("Pvt. Ltd., Industrial Area...", y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] == "ABC India Pvt. Ltd."
    assert "Industrial Area" in (result["manufacturerAddress"] or "")


def test_manufacturer_ocr_corrupted_label_with_structural_evidence():
    """
    C. OCR-corrupted label:
    Block 1: plausible OCR-corrupted version of 'Marketed by ABC India' (e.g. 'Horketed by ABC India')
    Block 2: 'Pvt. Ltd., Industrial Area...'
    -> extract the company only when structural/context evidence supports it.
    """
    blocks = [
        _make_block("Horketed by ABC India", y=0),
        _make_block("Pvt. Ltd., Industrial Area...", y=25),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] == "ABC India Pvt. Ltd."
    assert "Industrial Area" in (result["manufacturerAddress"] or "")


def test_manufacturer_unrelated_corporate_suffix_negative():
    """
    D. Negative:
    An unrelated block such as 'ABC Technologies Pvt. Ltd.'
    with no nearby manufacturer/packer/marketer context
    must NOT automatically become manufacturerName.
    """
    blocks = [
        _make_block("Shower Gel", y=0),
        _make_block("ABC Technologies Pvt. Ltd.", y=25),
        _make_block("Skin compatibility dermatologically tested", y=50),
    ]
    result = extract_fields(_ocr(blocks))
    assert result["manufacturerName"] is None


def test_manufacturer_preserve_explicit_labels():
    """
    E. Preserve existing 'Manufactured by', 'Mfg By', 'Packer', etc. behavior.
    """
    for label in ["Manufactured by: Acme Foods Ltd.", "Mfg By Acme Pharma Pvt. Ltd.", "Packed by: Global Logistics LLP"]:
        blocks = [_make_block(label, y=0)]
        res = extract_fields(_ocr(blocks))
        assert res["manufacturerName"] is not None
        assert "Acme" in res["manufacturerName"] or "Global" in res["manufacturerName"]


# ===========================================================================
# ISSUE: ProductName false positive rejection for instructional / usage steps
# ===========================================================================

def test_product_name_rejects_3_steps_for():
    """A. '3 Steps for' -> rejected as productName."""
    blocks = [
        _make_block("3 Steps for", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] is None or "Steps" not in res["productName"]


def test_product_name_rejects_steps_for_glowing():
    """B. 'Steps for Glowing' -> rejected as productName."""
    blocks = [
        _make_block("Steps for Glowing", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] is None or "Steps" not in res["productName"]


def test_product_name_rejects_follow_these_steps():
    """C. 'Follow these steps' -> rejected as productName."""
    blocks = [
        _make_block("Follow these steps", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] is None or "steps" not in res["productName"].lower()


def test_product_name_legitimate_unlabeled_multi_word_still_works():
    """D. A legitimate unlabeled multi-word product name still works."""
    blocks = [
        _make_block("Herbal Body Wash", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
        _make_block("Manufactured by: Acme Ltd.", confidence=0.95, y=60),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] == "Herbal Body Wash"


def test_product_name_existing_explicit_label_still_works():
    """E. Existing explicit product-name label still works."""
    blocks = [
        _make_block("Product Name: Baby Steps Lotion", confidence=0.95, y=10),
        _make_block("Net Qty 100ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] == "Baby Steps Lotion"


# ===========================================================================
# ISSUE: ProductName false positive rejection for claims / attributes
# ===========================================================================

def test_product_name_rejects_ph_skin():
    """A. 'pH skin' -> rejected."""
    blocks = [
        _make_block("pH skin", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] is None or "pH" not in res["productName"]


def test_product_name_rejects_ph_skin_balanced():
    """B. 'pH skin balanced' -> rejected."""
    blocks = [
        _make_block("pH skin balanced", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] is None or "pH" not in res["productName"]


def test_product_name_rejects_dermatologically_tested():
    """C. 'dermatologically tested' -> rejected."""
    blocks = [
        _make_block("dermatologically tested", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] is None or "dermatologically" not in res["productName"].lower()


def test_product_name_accepts_herbal_body_wash():
    """D. 'Herbal Body Wash' -> accepted."""
    blocks = [
        _make_block("Herbal Body Wash", confidence=0.95, y=10),
        _make_block("Net Qty 250ml", confidence=0.95, y=30),
        _make_block("Manufactured by: Acme Ltd.", confidence=0.95, y=60),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] == "Herbal Body Wash"


def test_product_name_accepts_baby_steps_lotion():
    """E. 'Baby Steps Lotion' -> accepted."""
    blocks = [
        _make_block("Baby Steps Lotion", confidence=0.95, y=10),
        _make_block("Net Qty 100ml", confidence=0.95, y=30),
        _make_block("Manufactured by: Acme Ltd.", confidence=0.95, y=60),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] == "Baby Steps Lotion"


def test_product_name_accepts_explicit_baby_steps_lotion():
    """F. Explicit 'Product Name: Baby Steps Lotion' -> accepted."""
    blocks = [
        _make_block("Product Name: Baby Steps Lotion", confidence=0.95, y=10),
        _make_block("Net Qty 100ml", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["productName"] == "Baby Steps Lotion"


# ===========================================================================
# BATCH NUMBER EXTRACTION TESTS
# ===========================================================================

def test_batch_number_batch_no_b12345():
    """Requirement 1: 'Batch No: B12345' -> 'B12345'."""
    blocks = [
        _make_block("Batch No: B12345", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "B12345"


def test_batch_number_batch_number_abc123():
    """Requirement 2: 'Batch Number: ABC123' -> 'ABC123'."""
    blocks = [
        _make_block("Batch Number: ABC123", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "ABC123"


def test_batch_number_batch_with_trailing_mfg():
    """Requirement 3: 'Batch: B12345 Mfg 03/2026' -> 'B12345'."""
    blocks = [
        _make_block("Batch: B12345 Mfg 03/2026", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "B12345"


def test_batch_number_lot_no_l9876():
    """Requirement 4: 'Lot No: L9876' -> 'L9876'."""
    blocks = [
        _make_block("Lot No: L9876", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "L9876"


def test_batch_number_for_batch_no():
    """Canonical label: 'FOR BATCH NO: B12345' -> 'B12345'."""
    blocks = [
        _make_block("FOR BATCH NO: B12345", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "B12345"


def test_batch_number_none_when_absent():
    """Requirement 5: No batch label/value -> None."""
    blocks = [
        _make_block("MRP Rs. 150.00", confidence=0.95),
        _make_block("Net Qty 250ml", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] is None


def test_batch_number_with_expiry_and_mrp_stops():
    """Requirement 6: Batch line containing expiry/mfg date/MRP -> batch value only."""
    blocks = [
        _make_block("Batch No: X7A92 Exp: 12/2026 MRP Rs 99.00", confidence=0.95),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "X7A92"


def test_batch_number_ambiguous_or_instructional_returns_none():
    """Requirement 7: Ambiguous/malformed batch text -> None."""
    # Instruction text
    blocks_crimp = [_make_block("Batch No: See crimp of tube", confidence=0.95)]
    assert extract_fields(_ocr(blocks_crimp))["batchNumber"] is None

    blocks_refer = [_make_block("Batch Number: Refer to bottom seal", confidence=0.95)]
    assert extract_fields(_ocr(blocks_refer))["batchNumber"] is None

    # Pure date mistakenly matched
    blocks_date = [_make_block("Batch: 03/2026", confidence=0.95)]
    assert extract_fields(_ocr(blocks_date))["batchNumber"] is None

    # Pure price
    blocks_price = [_make_block("Batch: Rs. 150.00", confidence=0.95)]
    assert extract_fields(_ocr(blocks_price))["batchNumber"] is None

    # Pure net quantity
    blocks_qty = [_make_block("Batch No: 500g", confidence=0.95)]
    assert extract_fields(_ocr(blocks_qty))["batchNumber"] is None


def test_batch_number_split_across_blocks():
    """Multi-block support: label in block 1, value in block 2."""
    blocks = [
        _make_block("Batch No:", confidence=0.95, y=10),
        _make_block("BT9876", confidence=0.95, y=30),
    ]
    res = extract_fields(_ocr(blocks))
    assert res["batchNumber"] == "BT9876"


def test_batch_number_present_in_output_schema():
    """batchNumber must always be present in extract_fields dictionary."""
    res = extract_fields({"quality": {}, "full_text": "", "text_blocks": []})
    assert "batchNumber" in res
    assert "fontSizeMm" not in res
    assert "fontHeightMm" in res


# ===========================================================================
# FONT HEIGHT MM CALIBRATION TESTS
# ===========================================================================

def test_font_height_mm_valid_calibration():
    """Requirement 1: Valid calibration computes correct fontHeightMm."""
    blocks = [
        _make_block("Batch No: B12345", confidence=0.95, y=0, h=40),
    ]
    # 40px / 10 px_per_mm = 4.0 mm
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=10.0)
    assert res["fontHeightMm"] == 4.0


def test_font_height_mm_no_calibration_is_none():
    """Requirement 2: No calibration -> fontHeightMm is None."""
    blocks = [
        _make_block("Batch No: B12345", confidence=0.95, y=0, h=40),
    ]
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=None)
    assert res["fontHeightMm"] is None


def test_font_height_mm_zero_calibration_is_none():
    """Requirement 3: Zero calibration -> fontHeightMm is None."""
    blocks = [
        _make_block("Batch No: B12345", confidence=0.95, y=0, h=40),
    ]
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=0)
    assert res["fontHeightMm"] is None
    res_float = extract_fields(_ocr(blocks), calibration_px_per_mm=0.0)
    assert res_float["fontHeightMm"] is None


def test_font_height_mm_negative_calibration_is_none():
    """Requirement 4: Negative calibration -> fontHeightMm is None."""
    blocks = [
        _make_block("Batch No: B12345", confidence=0.95, y=0, h=40),
    ]
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=-5.0)
    assert res["fontHeightMm"] is None


def test_font_height_mm_invalid_calibration_is_none():
    """Requirement 5: Invalid/unusable calibration -> fontHeightMm is None."""
    blocks = [
        _make_block("Batch No: B12345", confidence=0.95, y=0, h=40),
    ]
    for invalid_val in ["not_a_number", None, float("nan"), float("inf"), float("-inf")]:
        res = extract_fields(_ocr(blocks), calibration_px_per_mm=invalid_val)
        assert res["fontHeightMm"] is None


def test_font_height_mm_output_keys_unchanged():
    """Requirement 6: Key name must remain fontHeightMm; no fontSizeMm."""
    blocks = [
        _make_block("MRP Rs 50", confidence=0.95, y=0, h=30),
    ]
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=5.0)
    assert "fontHeightMm" in res
    assert "fontSizeMm" not in res
    assert res["fontHeightMm"] == 6.0


def test_font_height_mm_selects_minimum_statutory_declaration():
    """
    Requirement 9: Font height is determined by minimum height among relevant statutory declaration blocks.
    Product name (100 px) and Logo (80 px) are ignored.
    Statutory declarations:
      - MRP: 24 px
      - Net Quantity: 22 px
      - Consumer Care: 20 px
    Expected minimum selected height: 20 px.
    With calibration 10.0 px/mm -> fontHeightMm == 2.0 (NOT 10.0 from 100px product name).
    """
    blocks = [
        _make_block("SUPER BISCUITS EXTRA DELIGHT 200g", confidence=0.95, y=0, h=100),
        _make_block("DELIGHT FOODS LOGO", confidence=0.95, y=110, h=80),
        _make_block("MRP Rs. 50.00 (incl. of all taxes)", confidence=0.95, y=200, h=24),
        _make_block("Net Quantity: 200g", confidence=0.95, y=230, h=22),
        _make_block("Customer Care: care@brand.com", confidence=0.95, y=260, h=20),
    ]
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=10.0)
    assert res["fontHeightMm"] == 2.0


def test_font_height_mm_unrelated_large_text_does_not_affect_result():
    """
    Requirement 10: Unrelated large text (promotional claims, banners) does not affect statutory font height.
    """
    blocks = [
        _make_block("NOW WITH 50% MORE CRUNCHY DELIGHT", confidence=0.95, y=0, h=160),
        _make_block("3 Steps for Glowing Radiant Skin", confidence=0.95, y=170, h=90),
        _make_block("Net Wt. 100g", confidence=0.95, y=270, h=30),
    ]
    # 30px / 10.0 px_per_mm = 3.0 mm (NOT 16.0 mm from 160px banner)
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=10.0)
    assert res["fontHeightMm"] == 3.0


def test_font_height_mm_none_when_no_statutory_blocks_present():
    """
    Requirement 11: When no relevant statutory declaration blocks are found, fontHeightMm is None
    even if valid calibration is provided.
    """
    blocks = [
        _make_block("CRUNCHY WAFER BITES", confidence=0.95, y=0, h=90),
        _make_block("Delicious taste for everyone", confidence=0.95, y=100, h=45),
        _make_block("8901234567890", confidence=0.95, y=150, h=30),
    ]
    res = extract_fields(_ocr(blocks), calibration_px_per_mm=10.0)
    assert res["fontHeightMm"] is None


# ===========================================================================
# MULTI-IMAGE CANDIDATE SELECTION FOR batchNumber
# ===========================================================================

def test_multi_image_batch_number_candidate_selection(monkeypatch):
    """Multi-image candidate scoring selects the safest/highest-evidence batch number."""
    import image_processor
    from image_processor import process_product_images
    import paddle_ocr

    monkeypatch.setattr(image_processor, "check_image_quality", lambda path: {
        "success": True,
        "quality": {"quality_status": "ACCEPTABLE", "blur_score": 90.0, "brightness": 120.0, "is_blurry": False}
    })

    # Simulate 2 images:
    # Image 1: has clear "Batch No: B12345"
    # Image 2: has weak "Batch: See crimp"
    call_idx = 0

    def mock_extract_text(image_path, **kwargs):
        nonlocal call_idx
        call_idx += 1
        if call_idx == 1:
            return {
                "success": True,
                "full_text": "Batch No: B12345 Net Qty 100g",
                "text_blocks": [
                    _make_block("Batch No: B12345", 0.95),
                    _make_block("Net Qty 100g", 0.90),
                ],
                "annotated_image_path": None,
            }
        else:
            return {
                "success": True,
                "full_text": "Batch: See crimp Net Qty 100g",
                "text_blocks": [
                    _make_block("Batch: See crimp", 0.95),
                    _make_block("Net Qty 100g", 0.90),
                ],
                "annotated_image_path": None,
            }

    monkeypatch.setattr(paddle_ocr, "extract_text", mock_extract_text)

    # Call process_product_images with dummy paths
    result = process_product_images(["dummy1.jpg", "dummy2.jpg"], calibration_px_per_mm=10.0)
    assert result["success"] is True
    assert result["fields"]["batchNumber"] == "B12345"
    assert result["fields"]["fontHeightMm"] is not None

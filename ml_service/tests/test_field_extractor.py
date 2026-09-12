import pytest
from field_extractor import extract_fields


def test_well_formatted_label_extraction():
    """Tests extraction from a well-formatted packaged commodity label."""
    ocr_result = {
        "quality": {
            "blur_score": 140.5,
            "is_blurry": False,
            "brightness": 150.0,
            "quality_status": "ACCEPTABLE"
        },
        "full_text": (
            "CATCH SPICES GARAM MASALA\n"
            "Net Wt. 200 g\n"
            "MRP Rs. 120.00 (incl. of all taxes)\n"
            "Mfg by DS Spiceco Pvt Ltd\n"
            "Plot No 4, Sector 63, Noida\n"
            "DOM: 08/2026\n"
            "Consumer Care: 1800-103-1929, care@dsgroup.com"
        ),
        "text_blocks": [
            {"text": "CATCH SPICES GARAM MASALA", "confidence": 0.96, "box": [[10, 10], [200, 10], [200, 40], [10, 40]]},
            {"text": "Net Wt. 200 g", "confidence": 0.92, "box": [[10, 50], [150, 50], [150, 70], [10, 70]]},
            {"text": "MRP Rs. 120.00 (incl. of all taxes)", "confidence": 0.94, "box": [[10, 80], [300, 80], [300, 100], [10, 100]]},
            {"text": "Mfg by DS Spiceco Pvt Ltd", "confidence": 0.90, "box": [[10, 110], [250, 110], [250, 130], [10, 130]]},
            {"text": "Plot No 4, Sector 63, Noida", "confidence": 0.88, "box": [[10, 140], [260, 140], [260, 160], [10, 160]]},
            {"text": "DOM: 08/2026", "confidence": 0.91, "box": [[10, 170], [150, 170], [150, 190], [10, 190]]},
            {"text": "Consumer Care: 1800-103-1929, care@dsgroup.com", "confidence": 0.89, "box": [[10, 200], [380, 200], [380, 220], [10, 220]]}
        ]
    }

    fields = extract_fields(ocr_result)

    assert fields["productName"] == "CATCH SPICES GARAM MASALA"
    assert fields["netQuantity"] == "200 g"
    assert "120.00" in fields["mrp"]
    assert "DS Spiceco" in fields["manufacturerName"]
    assert fields["consumerCare"] == "1800-103-1929, care@dsgroup.com"
    assert not fields["consumerCare"].startswith("Consumer Care:")
    assert fields["extraction_confidence"] == "HIGH"
    assert fields["isImported"] is False
    assert fields["countryOfOrigin"] is None


def test_messy_partial_label_extraction():
    """Tests extraction from a messy or partial text scan."""
    ocr_result = {
        "quality": {
            "blur_score": 45.0,
            "is_blurry": True,
            "brightness": 110.0,
            "quality_status": "POOR"
        },
        "full_text": "MRP ₹ 45.00 Pkd: Aug 2026 Net Qty 500ml",
        "text_blocks": [
            {"text": "MRP ₹ 45.00 Pkd: Aug 2026 Net Qty 500ml", "confidence": 0.65, "box": [[10, 10], [300, 10], [300, 50], [10, 50]]}
        ]
    }

    fields = extract_fields(ocr_result)

    assert fields["mrp"] == "MRP ₹ 45.00 Pkd: Aug 2026 Net Qty 500ml" or "45.00" in fields["mrp"]
    assert fields["netQuantity"] == "500ml" or fields["netQuantity"] == "500 ml"
    assert fields["monthOfPacking"] == "08"
    assert fields["yearOfPacking"] == "2026"
    assert fields["extraction_confidence"] == "LOW"
    assert fields["manufacturerName"] is None


def test_unreadable_quality_status_confidence():
    """Tests that UNREADABLE quality_status sets extraction_confidence to LOW."""
    ocr_result = {
        "quality": {
            "blur_score": 12.0,
            "is_blurry": True,
            "brightness": 20.0,
            "quality_status": "UNREADABLE"
        },
        "full_text": "Unreadable blur text",
        "text_blocks": []
    }

    fields = extract_fields(ocr_result)

    assert fields["extraction_confidence"] == "LOW"
    assert fields["mrp"] is None
    assert fields["netQuantity"] is None


def test_ocr_typos_and_devanagari_extraction():
    """Tests extraction with common OCR misspellings and mixed Devanagari digits."""
    ocr_result = {
        "quality": {
            "blur_score": 150.0,
            "is_blurry": False,
            "brightness": 160.0,
            "quality_status": "ACCEPTABLE"
        },
        "full_text": (
            "Premium Almond Milk\n"
            "Maximum Retail Pnce 8९९ ०० (Inclusive of all Taxes)\n"
            "Month and Year of Manuiaclure AUGUST 2024\n"
            "Manufactured by NYK Techno Solutions\n"
            "Registered Address NYK Techno Solutions, Plot 12, Industrial Area, Sector 5\n"
            "Net Quantity 500 g"
        ),
        "text_blocks": [
            {"text": "Premium Almond Milk", "confidence": 0.95, "box": [[10, 10], [200, 10], [200, 30], [10, 30]]},
            {"text": "Maximum Retail Pnce 8९९ ०० (Inclusive of all Taxes)", "confidence": 0.91, "box": [[10, 40], [350, 40], [350, 60], [10, 60]]},
            {"text": "Month and Year of Manuiaclure AUGUST 2024", "confidence": 0.89, "box": [[10, 70], [320, 70], [320, 90], [10, 90]]},
            {"text": "Manufactured by NYK Techno Solutions", "confidence": 0.93, "box": [[10, 100], [280, 100], [280, 120], [10, 120]]},
            {"text": "Registered Address NYK Techno Solutions, Plot 12, Industrial Area, Sector 5", "confidence": 0.88, "box": [[10, 130], [400, 130], [400, 150], [10, 150]]},
            {"text": "Net Quantity 500 g", "confidence": 0.94, "box": [[10, 160], [180, 160], [180, 180], [10, 180]]}
        ]
    }

    fields = extract_fields(ocr_result)

    assert fields["mrp"] is not None
    assert "899 00" in fields["mrp"] or "899" in fields["mrp"]
    assert fields["monthOfPacking"] == "08"
    assert fields["yearOfPacking"] == "2024"
    assert fields["manufacturerName"] == "NYK Techno Solutions"
    assert fields["manufacturerAddress"] is not None
    assert "NYK Techno Solutions" in fields["manufacturerAddress"] or "Industrial Area" in fields["manufacturerAddress"]
    assert fields["netQuantity"] == "500 g"


def test_dell_mouse_flat_text_extraction():
    """Tests extraction on flat OCR string without newlines mimicking real Dell mouse packaging."""
    ocr_result = {
        "quality": {
            "blur_score": 180.0,
            "is_blurry": False,
            "brightness": 160.0,
            "quality_status": "ACCEPTABLE"
        },
        "full_text": (
            "Dell Optical Mouse WM126 "
            "Maximum Retail Pnce 899 00 (Inclusive of all Taxes) "
            "Registered Address NYK Techno Solutions Pvt Limited "
            "Anmol South City No Ba/B5 Mouza Jagdishpur NH-6 Howrah West Bengal-711115 "
            "Month and Year of Manuiaclure AUGUST 2024 "
            "For customer care contact 1800-425-4026 email: care@dell.com EAN 5397184246030"
        ),
        "text_blocks": [
            {
                "text": (
                    "Dell Optical Mouse WM126 "
                    "Maximum Retail Pnce 899 00 (Inclusive of all Taxes) "
                    "Registered Address NYK Techno Solutions Pvt Limited "
                    "Anmol South City No Ba/B5 Mouza Jagdishpur NH-6 Howrah West Bengal-711115 "
                    "Month and Year of Manuiaclure AUGUST 2024 "
                    "For customer care contact 1800-425-4026 email: care@dell.com EAN 5397184246030"
                ),
                "confidence": 0.92,
                "box": [[0, 0], [500, 0], [500, 100], [0, 100]]
            }
        ]
    }

    fields = extract_fields(ocr_result)

    assert fields["mrp"] == "MRP Rs. 899.00 (inclusive of all taxes)"
    assert fields["monthOfPacking"] == "08"
    assert fields["yearOfPacking"] == "2024"
    assert fields["manufacturerName"] == "NYK Techno Solutions Pvt Limited"
    assert fields["manufacturerAddress"] is not None
    assert "Anmol South City" in fields["manufacturerAddress"]
    assert "Howrah" in fields["manufacturerAddress"] or "711115" in fields["manufacturerAddress"]
    assert "1800-425-4026" in fields["consumerCare"] or "care@dell.com" in fields["consumerCare"]


def test_dell_long_manufacturer_name_extraction():
    """Tests extraction of full multi-word company name without over-truncation to 'Del'."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": (
            "Manufactured by Dell International Services India Private Limited "
            "Divyasree Greens Ground Floor Koramangala Bangalore 560071"
        ),
        "text_blocks": [
            {
                "text": "Manufactured by Dell International Services India Private Limited Divyasree Greens Ground Floor Koramangala Bangalore 560071",
                "confidence": 0.95,
                "box": [[0, 0], [500, 0], [500, 50], [0, 50]]
            }
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["manufacturerName"] == "Dell International Services India Private Limited"
    assert fields["manufacturerAddress"] is not None
    assert "Bangalore" in fields["manufacturerAddress"] or "Koramangala" in fields["manufacturerAddress"]


def test_mrp_typo_normalization():
    """Tests normalization of raw OCR typos in MRP string."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Retail Prce 899 00 (nclusive of all Taxes)",
        "text_blocks": [
            {"text": "Retail Prce 899 00 (nclusive of all Taxes)", "confidence": 0.90, "box": [[0, 0], [300, 0], [300, 40], [0, 40]]}
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["mrp"] == "MRP Rs. 899.00 (inclusive of all taxes)"


def test_low_confidence_noise_filtering():
    """Tests that OCR blocks below 0.10 confidence are ignored during field extraction."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "MRP Rs. 50.00 Net Wt 100g !!!garbage_noise!!!",
        "text_blocks": [
            {"text": "MRP Rs. 50.00", "confidence": 0.85, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "Net Wt 100g", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "MRP Rs. 9999.00", "confidence": 0.02, "box": [[0, 60], [100, 60], [100, 80], [0, 80]]}  # noise block
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["mrp"] == "MRP Rs. 50.00"
    assert fields["netQuantity"] == "100g"


def test_weighted_extraction_confidence_scoring():
    """Tests weighted field-completeness extraction_confidence logic."""
    # Case 1: ACCEPTABLE image quality but missing core statutory fields -> LOW confidence
    incomplete_ocr = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Net Wt 200g",
        "text_blocks": [
            {"text": "Net Wt 200g", "confidence": 0.95, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]}
        ]
    }
    fields_inc = extract_fields(incomplete_ocr)
    assert fields_inc["extraction_confidence"] == "LOW"

    # Case 2: ACCEPTABLE image quality with full statutory fields -> HIGH confidence
    complete_ocr = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Ponds Soap Net Wt 100g MRP Rs 50.00 Mfg by HUL 08/2026 Care 1800-100-100",
        "text_blocks": [
            {"text": "Ponds Soap", "confidence": 0.95, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "Net Wt 100g", "confidence": 0.92, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "MRP Rs 50.00", "confidence": 0.90, "box": [[0, 60], [100, 60], [100, 80], [0, 80]]},
            {"text": "Mfg by HUL", "confidence": 0.88, "box": [[0, 90], [100, 90], [100, 110], [0, 110]]},
            {"text": "08/2026", "confidence": 0.91, "box": [[0, 120], [100, 120], [100, 140], [0, 140]]},
            {"text": "Care 1800-100-100", "confidence": 0.85, "box": [[0, 150], [100, 150], [100, 170], [0, 170]]}
        ]
    }
    fields_comp = extract_fields(complete_ocr)
    assert fields_comp["extraction_confidence"] == "HIGH"


def test_allergen_disclaimer_exclusion():
    """Tests that lines containing allergen disclaimers ('manufactured in a facility...') are never extracted as manufacturerName."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "ALLERGEN ADVICE: This product is manufactured in a facility that may process peanuts, sesame and tree nuts.",
        "text_blocks": [
            {"text": "ALLERGEN ADVICE: This product is manufactured in a facility that may process peanuts", "confidence": 0.85, "box": [[0, 0], [400, 0], [400, 20], [0, 20]]}
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["manufacturerName"] is None or "facility" not in fields["manufacturerName"].lower()


def test_low_confidence_manufacturer_fallback():
    """Tests that low confidence raw blocks (< 0.10) with corporate suffixes are safely recovered as fallback."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Net Wt 200g Regd office DHARAMPAL SATYAPAL FOODSLIMITED",
        "text_blocks": [
            {"text": "Net Wt 200g", "confidence": 0.90, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "Regd office DHARAMPAL SATYAPAL FOODSLIMITED", "confidence": 0.083, "box": [[0, 30], [300, 30], [300, 50], [0, 50]]}
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["manufacturerName"] is not None
    assert "DHARAMPAL SATYAPAL" in fields["manufacturerName"] or "FOODS" in fields["manufacturerName"]


def test_consumer_care_structured_extraction():
    """Tests that structured phone, email, and website are extracted, rejecting header fragments like ', Contact'."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "For Consumer Complaints Feedback, Contact Email: care@example.com Ph: 1800-123-4567 www.example.com",
        "text_blocks": [
            {"text": "For Consumer Complaints Feedback, Contact", "confidence": 0.80, "box": [[0, 0], [300, 0], [300, 20], [0, 20]]},
            {"text": "Email: care@example.com", "confidence": 0.85, "box": [[0, 30], [200, 30], [200, 50], [0, 50]]},
            {"text": "Ph: 1800-123-4567", "confidence": 0.90, "box": [[0, 60], [200, 60], [200, 80], [0, 80]]},
            {"text": "at www.example.com", "confidence": 0.88, "box": [[0, 90], [200, 90], [200, 110], [0, 110]]}
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["consumerCare"] is not None
    assert "1800-123-4567" in fields["consumerCare"]
    assert "care@example.com" in fields["consumerCare"]
    assert not fields["consumerCare"].startswith(", Contact")


def test_generic_country_of_origin_extraction():
    """Tests generic country of origin extractions across multiple country declarations."""
    # Case 1: Product of India
    res1 = extract_fields({"quality": {"quality_status": "ACCEPTABLE"}, "full_text": "Product of India", "text_blocks": [{"text": "Product of India", "confidence": 0.9}]})
    assert res1["countryOfOrigin"] == "India"

    # Case 2: Made in Germany
    res2 = extract_fields({"quality": {"quality_status": "ACCEPTABLE"}, "full_text": "Made in Germany", "text_blocks": [{"text": "Made in Germany", "confidence": 0.9}]})
    assert res2["countryOfOrigin"] == "Germany"

    # Case 3: Country of Origin: China
    res3 = extract_fields({"quality": {"quality_status": "ACCEPTABLE"}, "full_text": "Country of Origin: China", "text_blocks": [{"text": "Country of Origin: China", "confidence": 0.9}]})
    assert res3["countryOfOrigin"] == "China"

    # Case 4: Standalone PRODUCT OF INDIA
    res4 = extract_fields({"quality": {"quality_status": "ACCEPTABLE"}, "full_text": "PRODUCT OF INDIA", "text_blocks": [{"text": "PRODUCT OF INDIA", "confidence": 0.8}]})
    assert res4["countryOfOrigin"] == "India"


def test_mrp_requires_supported_label_and_numeric_evidence():
    weak = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "MRP २ phone 1800-102-5353 date 03/2025 licence 12345",
        "text_blocks": [
            {"text": "MRP २", "confidence": 0.25, "box": [[0, 0], [60, 0], [60, 20], [0, 20]]},
            {"text": "phone 1800-102-5353", "confidence": 0.90, "box": [[0, 30], [180, 30], [180, 50], [0, 50]]},
        ],
    })
    assert weak["mrp"] is None


def test_split_blocks_and_promotional_quantity_are_recovered():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Net Content 100 g + 20 g Extra = 120 g", "text_blocks": [
            {"text": "Net Content", "confidence": 0.80, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "100 g + 20 g Extra = 120 g", "confidence": 0.45, "box": [[110, 0], [300, 0], [300, 20], [110, 20]]},
        ],
    })
    assert result["netQuantity"] == "120 g"


def test_fragmented_manufacturer_and_contacts_and_origin():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "In India by gun pharmaceutical industries limited Or email us ac abzorb e sunpharma com",
        "text_blocks": [
            {"text": "In India by", "confidence": 0.90, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "gun", "confidence": 0.28, "box": [[105, 0], [140, 0], [140, 20], [105, 20]]},
            {"text": "pharmaceutical industries limited", "confidence": 0.80, "box": [[145, 0], [350, 0], [350, 20], [145, 20]]},
            {"text": "Or email us ac abzorb", "confidence": 0.38, "box": [[0, 30], [150, 30], [150, 50], [0, 50]]},
            {"text": "@sunpharma com", "confidence": 0.80, "box": [[155, 30], [300, 30], [300, 50], [155, 50]]},
        ],
    })
    assert "pharmaceutical industries limited" in result["manufacturerName"]
    assert "@" in result["consumerCare"]
    assert result["countryOfOrigin"] == "India"


def test_date_label_and_unsafe_date_handling():
    valid = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Mfg Date 03/2025", "text_blocks": [{"text": "Mfg Date 03/2025", "confidence": 0.80}],
    })
    assert valid["monthOfPacking"] == "03"
    assert valid["yearOfPacking"] == "2025"

    unsafe = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Mfg Date 03:202|=", "text_blocks": [{"text": "Mfg Date 03:202|=", "confidence": 0.20}],
    })
    assert unsafe["yearOfPacking"] is None


def test_explicit_common_generic_name_beats_brand_block():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "SELECT Common Genaric Name D Select Wireless Mouse DS320",
        "text_blocks": [
            {"text": "SELECT", "confidence": 0.99, "box": [[0, 0], [80, 0], [80, 20], [0, 20]]},
            {"text": "Common Genaric Name", "confidence": 0.90, "box": [[0, 40], [180, 40], [180, 60], [0, 60]]},
            {"text": "D Select Wireless Mouse DS320", "confidence": 0.92, "box": [[0, 70], [240, 70], [240, 90], [0, 90]]},
        ],
    })
    assert result["productName"] == "D Select Wireless Mouse DS320"


def test_country_label_variants_use_adjacent_value_only():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Country oi Origin India International", "text_blocks": [
            {"text": "Country oi Origin", "confidence": 0.95, "box": [[0, 0], [140, 0], [140, 20], [0, 20]]},
            {"text": "India", "confidence": 0.98, "box": [[150, 0], [210, 0], [210, 20], [150, 20]]},
            {"text": "International", "confidence": 0.98, "box": [[0, 40], [130, 40], [130, 60], [0, 60]]},
        ],
    })
    assert result["countryOfOrigin"] == "India"


def test_count_quantity_and_context_limited_in_normalization():
    labeled = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Number of Units (Quantity): IN", "text_blocks": [
            {"text": "Number of Units (Quantity):", "confidence": 0.90, "box": [[0, 0], [210, 0], [210, 20], [0, 20]]},
            {"text": "IN", "confidence": 0.80, "box": [[220, 0], [250, 0], [250, 20], [220, 20]]},
        ],
    })
    assert labeled["netQuantity"] is None

    unrelated = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "IN India", "text_blocks": [{"text": "IN India", "confidence": 0.90}],
    })
    assert unrelated["netQuantity"] is None


def test_consumer_heading_requires_actual_channel():
    heading = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "please contact Customer Care", "text_blocks": [{"text": "please contact Customer Care", "confidence": 0.90}],
    })
    assert heading["consumerCare"] is None
    assert heading["extraction_confidence"] != "HIGH"

    channels = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Telephone: 1800-3099-807 Email Address: support@example.com", "text_blocks": [
            {"text": "Telephone:", "confidence": 0.90, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "1800-3099-807", "confidence": 0.90, "box": [[110, 0], [230, 0], [230, 20], [110, 20]]},
            {"text": "Email Address:", "confidence": 0.90, "box": [[0, 30], [120, 30], [120, 50], [0, 50]]},
            {"text": "support@example.com", "confidence": 0.90, "box": [[130, 30], [300, 30], [300, 50], [130, 50]]},
        ],
    })
    assert "1800-3099-807" in channels["consumerCare"]
    assert "support@example.com" in channels["consumerCare"]


def test_company_sections_keep_addresses_with_their_entity():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Registered Address Alpha Foods Limited Alpha Road Marketed By Beta Services Private Limited Beta Park Bengaluru Country of Origin India",
        "text_blocks": [
            {"text": "Registered Address Alpha Foods Limited", "confidence": 0.90, "box": [[0, 0], [230, 0], [230, 20], [0, 20]]},
            {"text": "Alpha Road", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "Marketed By Beta Services Private Limited", "confidence": 0.90, "box": [[0, 70], [280, 70], [280, 90], [0, 90]]},
            {"text": "Beta Park Bengaluru", "confidence": 0.90, "box": [[0, 100], [180, 100], [180, 120], [0, 120]]},
            {"text": "Country of Origin", "confidence": 0.90, "box": [[0, 140], [140, 140], [140, 160], [0, 160]]},
            {"text": "India", "confidence": 0.90, "box": [[150, 140], [200, 140], [200, 160], [150, 160]]},
        ],
    })
    assert result["manufacturerName"] == "Beta Services Private Limited"
    assert "Beta Park" in result["manufacturerAddress"]
    assert "Alpha Road" not in result["manufacturerAddress"]


def test_contact_text_cannot_be_company():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Manufacturing Address or Email: foods@example.com",
        "text_blocks": [
            {"text": "Manufacturing", "confidence": 0.90, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "Address", "confidence": 0.90, "box": [[110, 0], [180, 0], [180, 20], [110, 20]]},
            {"text": "or Email: foods@example.com", "confidence": 0.90, "box": [[190, 0], [380, 0], [380, 20], [190, 20]]},
        ],
    })
    assert result["manufacturerName"] is None


def test_realistic_foods_company_remains_valid():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Manufactured By: Example Foods Limited",
        "text_blocks": [{"text": "Manufactured By: Example Foods Limited", "confidence": 0.90}],
    })
    assert result["manufacturerName"] == "Example Foods Limited"


def test_low_confidence_corporate_fallback_recovers_company():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Regd office Example Consumer Products Limited",
        "text_blocks": [{"text": "Regd office Example Consumer Products Limited", "confidence": 0.08}],
    })
    assert result["manufacturerName"] is not None
    assert "Example Consumer Products Limited" in result["manufacturerName"]


def test_allergen_text_cannot_be_company():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "This product is manufactured in a facility that may process peanuts",
        "text_blocks": [{"text": "This product is manufactured in a facility that may process peanuts", "confidence": 0.90}],
    })
    assert result["manufacturerName"] is None


def test_fragmented_product_of_country_is_extracted():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "PRODUCT OFINDIA", "text_blocks": [
            {"text": "PRODUCT", "confidence": 0.90, "box": [[0, 0], [70, 0], [70, 20], [0, 20]]},
            {"text": "OFINDIA", "confidence": 0.90, "box": [[75, 0], [145, 0], [145, 20], [75, 20]]},
        ],
    })
    assert result["countryOfOrigin"] == "India"


def test_fragmented_product_of_country_with_separate_of_is_extracted():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "PRODUCT OF GERMANY", "text_blocks": [
            {"text": "PRODUCT", "confidence": 0.90, "box": [[0, 0], [70, 0], [70, 20], [0, 20]]},
            {"text": "OF", "confidence": 0.90, "box": [[75, 0], [100, 0], [100, 20], [75, 20]]},
            {"text": "GERMANY", "confidence": 0.90, "box": [[105, 0], [180, 0], [180, 20], [105, 20]]},
        ],
    })
    assert result["countryOfOrigin"] == "Germany"


def test_country_label_variants_remain_supported():
    for label, country in [("Country of Origin", "Germany"), ("Country oi Origin", "India")]:
        result = extract_fields({
            "quality": {"quality_status": "ACCEPTABLE"},
            "full_text": f"{label} {country}", "text_blocks": [
                {"text": label, "confidence": 0.90, "box": [[0, 0], [140, 0], [140, 20], [0, 20]]},
                {"text": country, "confidence": 0.90, "box": [[145, 0], [220, 0], [220, 20], [145, 20]]},
            ],
        })
        assert result["countryOfOrigin"] == country


def test_product_without_country_does_not_use_unrelated_neighbor():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "PRODUCT information Germany", "text_blocks": [
            {"text": "PRODUCT", "confidence": 0.90, "box": [[0, 0], [70, 0], [70, 20], [0, 20]]},
            {"text": "information", "confidence": 0.90, "box": [[75, 0], [160, 0], [160, 20], [75, 20]]},
            {"text": "Germany", "confidence": 0.90, "box": [[0, 100], [75, 100], [75, 120], [0, 120]]},
        ],
    })
    assert result["countryOfOrigin"] is None


def test_mrp_label_without_numeric_value_is_none():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "MRP (Incl. of all taxes)",
        "text_blocks": [{"text": "MRP (Incl. of all taxes)", "confidence": 0.90}],
    })
    assert result["mrp"] is None


def test_observed_label_layout_reconstructs_fields_without_inventing_quantity():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "SELECT Common Genenc Name D Select Wireless Mouse DS320 Marketed By Del International Services India Private Limited Crysta Downs EGL Business Park Domlur Bengaluru 56007 Mocel Number 0$320 Couniyo Oriqin India Number of Units Ouanny Month and Yearof Manulacture AUGUS 2024 Maximum Retail Prce 899 00 Telephone 1800-3099-807",
        "text_blocks": [
            {"text": "SELECT", "confidence": 0.99, "box": [[0, 0], [80, 0], [80, 20], [0, 20]]},
            {"text": "Common Genenc Name", "confidence": 0.72, "box": [[0, 30], [180, 30], [180, 50], [0, 50]]},
            {"text": "D Select Wireless Mouse DS320", "confidence": 0.19, "box": [[0, 55], [240, 55], [240, 75], [0, 75]]},
            {"text": "Marketed By Del", "confidence": 0.72, "box": [[0, 90], [150, 90], [150, 110], [0, 110]]},
            {"text": "International Services India Private Limited", "confidence": 0.72, "box": [[0, 115], [300, 115], [300, 135], [0, 135]]},
            {"text": "Crysta Downs EGL Business Park Domlur Bengaluru 56007", "confidence": 0.70, "box": [[0, 140], [360, 140], [360, 160], [0, 160]]},
            {"text": "Mocel Number", "confidence": 0.70, "box": [[0, 180], [150, 180], [150, 200], [0, 200]]},
            {"text": "0$320", "confidence": 0.70, "box": [[0, 205], [80, 205], [80, 225], [0, 225]]},
            {"text": "Couniyo Oriqin", "confidence": 0.51, "box": [[0, 240], [150, 240], [150, 260], [0, 260]]},
            {"text": "India", "confidence": 0.99, "box": [[160, 240], [220, 240], [220, 260], [160, 260]]},
            {"text": "Number of Units", "confidence": 0.80, "box": [[0, 275], [150, 275], [150, 295], [0, 295]]},
            {"text": "Ouanny", "confidence": 0.60, "box": [[160, 275], [220, 275], [220, 295], [160, 295]]},
            {"text": "Month and Yearof Manulacture", "confidence": 0.32, "box": [[0, 310], [240, 310], [240, 330], [0, 330]]},
            {"text": "AUGUS", "confidence": 0.99, "box": [[0, 335], [80, 335], [80, 355], [0, 355]]},
            {"text": "2024", "confidence": 0.99, "box": [[90, 335], [150, 335], [150, 355], [90, 355]]},
            {"text": "Maximum Retail Prce 899 00 (nclusive of all Taxes)", "confidence": 0.90, "box": [[0, 370], [350, 370], [350, 390], [0, 390]]},
            {"text": "Telephone 1800-3099-807", "confidence": 0.90, "box": [[0, 405], [220, 405], [220, 425], [0, 425]]},
        ],
    })
    assert result["productName"] == "D Select Wireless Mouse DS320"
    assert result["manufacturerName"] == "Del International Services India Private Limited"
    assert "Crysta Downs" in result["manufacturerAddress"]
    assert "Mocel" not in result["manufacturerAddress"]
    assert result["countryOfOrigin"] == "India"
    assert result["monthOfPacking"] == "08"
    assert result["yearOfPacking"] == "2024"
    assert result["netQuantity"] is None
    assert "899.00" in result["mrp"]
    assert result["consumerCare"] == "1800-3099-807"


def test_catch_fragmented_origin_and_safe_missing_statutory_values():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Iet lleght 200g PRODUCT OF INDM trPa ofce DH RANIPAL SATYAPAL FOODS 91-120 4832860 foods@dsgroup.com",
        "text_blocks": [
            {"text": "Iet lleght", "confidence": 0.30, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "200g", "confidence": 0.90, "box": [[0, 30], [70, 30], [70, 50], [0, 50]]},
            {"text": "PRODUCT", "confidence": 0.90, "box": [[0, 70], [80, 70], [80, 90], [0, 90]]},
            {"text": "OF INDM", "confidence": 0.90, "box": [[85, 70], [160, 70], [160, 90], [85, 90]]},
            {"text": "trPa ofce", "confidence": 0.30, "box": [[0, 110], [100, 110], [100, 130], [0, 130]]},
            {"text": "DH RANIPAL SATYAPAL FOODS", "confidence": 0.70, "box": [[105, 110], [300, 110], [300, 130], [105, 130]]},
            {"text": "91-120 4832860 foods@dsgroup.com", "confidence": 0.90, "box": [[0, 150], [260, 150], [260, 170], [0, 170]]},
        ],
    })
    assert result["netQuantity"] == "200g"
    assert result["countryOfOrigin"] == "India"
    assert result["mrp"] is None
    assert result["monthOfPacking"] is None
    assert result["yearOfPacking"] is None
    assert "@" not in result["manufacturerName"]


def test_manufacturer_address_uses_plausible_blocks_and_split_boundaries():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Marketed By Example Services Private Limited First Road Second Area Village Mocel Number ABC123 Couniyo Oriqin India",
        "text_blocks": [
            {"text": "Marketed By Example Services Private Limited", "confidence": 0.90, "box": [[0, 0], [300, 0], [300, 20], [0, 20]]},
            {"text": "First Road", "confidence": 0.90, "box": [[0, 30], [120, 30], [120, 50], [0, 50]]},
            {"text": "Second Area", "confidence": 0.90, "box": [[0, 55], [140, 55], [140, 75], [0, 75]]},
            {"text": "Village", "confidence": 0.90, "box": [[500, 80], [500, 145], [520, 145], [520, 80]]},
            {"text": "Mocel", "confidence": 0.80, "box": [[0, 100], [70, 100], [70, 120], [0, 120]]},
            {"text": "Number", "confidence": 0.80, "box": [[75, 100], [145, 100], [145, 120], [75, 120]]},
            {"text": "ABC123", "confidence": 0.90, "box": [[0, 125], [90, 125], [90, 145], [0, 145]]},
            {"text": "Couniyo Oriqin", "confidence": 0.70, "box": [[0, 160], [150, 160], [150, 180], [0, 180]]},
            {"text": "India", "confidence": 0.95, "box": [[160, 160], [220, 160], [220, 180], [160, 180]]},
        ],
    })

    assert result["manufacturerName"] == "Example Services Private Limited"
    assert result["manufacturerAddress"] == "First Road Second Area"
    assert "Village" not in result["manufacturerAddress"]
    assert "ABC123" not in result["manufacturerAddress"]
    assert "Couniyo" not in result["manufacturerAddress"]
    assert result["countryOfOrigin"] == "India"


def test_manufacturer_address_preserves_valid_multi_block_continuation():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Manufactured by Example Foods Limited Plot 12 Industrial Area Sector 5 Model Number ZX9",
        "text_blocks": [
            {"text": "Manufactured by Example Foods Limited", "confidence": 0.90, "box": [[0, 0], [300, 0], [300, 20], [0, 20]]},
            {"text": "Plot 12", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "Industrial Area", "confidence": 0.90, "box": [[0, 55], [150, 55], [150, 75], [0, 75]]},
            {"text": "Sector 5", "confidence": 0.90, "box": [[0, 80], [100, 80], [100, 100], [0, 100]]},
            {"text": "Model Number", "confidence": 0.80, "box": [[0, 125], [150, 125], [150, 145], [0, 145]]},
        ],
    })

    assert result["manufacturerAddress"] == "Plot 12 Industrial Area Sector 5"


def test_same_row_model_value_is_excluded_with_split_boundary_label():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Marketed By Example Services Private Limited First Road Mocel Number 0$320 Couniyo Oriqin India",
        "text_blocks": [
            {"text": "Marketed By Example Services Private Limited", "confidence": 0.90, "box": [[0, 300], [300, 300], [300, 320], [0, 320]]},
            {"text": "First Road", "confidence": 0.90, "box": [[0, 340], [120, 340], [120, 360], [0, 360]]},
            {"text": "Mocel", "confidence": 0.80, "box": [[53, 393], [91, 393], [91, 409], [53, 409]]},
            {"text": "Number", "confidence": 0.80, "box": [[95, 393], [149, 393], [149, 407], [95, 407]]},
            {"text": "0$320", "confidence": 0.90, "box": [[275, 391], [319, 391], [319, 407], [275, 407]]},
            {"text": "Couniyo Oriqin", "confidence": 0.70, "box": [[53, 430], [150, 430], [150, 446], [53, 446]]},
            {"text": "India", "confidence": 0.95, "box": [[160, 430], [220, 430], [220, 446], [160, 446]]},
        ],
    })

    assert result["manufacturerAddress"] == "First Road"
    assert "0$320" not in result["manufacturerAddress"]


def test_isolated_skewed_address_block_is_excluded_but_horizontal_blocks_remain():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Manufactured by Example Foods Limited Crysta Downs EGL Business Park Village Model Number ZX9",
        "text_blocks": [
            {"text": "Manufactured by Example Foods Limited", "confidence": 0.90, "box": [[0, 300], [300, 300], [300, 320], [0, 320]]},
            {"text": "Crysta", "confidence": 0.90, "box": [[0, 340], [70, 340], [70, 360], [0, 360]]},
            {"text": "Downs", "confidence": 0.90, "box": [[75, 340], [140, 340], [140, 360], [75, 360]]},
            {"text": "EGL Business Park", "confidence": 0.90, "box": [[0, 365], [180, 365], [180, 385], [0, 385]]},
            {"text": "Village", "confidence": 0.90, "box": [[411, 357], [458, 364], [455, 380], [408, 374]]},
            {"text": "Model Number", "confidence": 0.80, "box": [[0, 410], [150, 410], [150, 430], [0, 430]]},
        ],
    })

    assert result["manufacturerAddress"] == "Crysta Downs EGL Business Park"
    assert "Village" not in result["manufacturerAddress"]


def test_low_confidence_unlabelled_product_candidate_is_null():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Iet lleght 200g",
        "text_blocks": [
            {"text": "Iet lleght", "confidence": 0.136, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "200g", "confidence": 0.87, "box": [[0, 30], [70, 30], [70, 50], [0, 50]]},
        ],
    })

    assert result["productName"] is None
    assert result["netQuantity"] == "200g"


def test_fragmented_product_of_row_uses_constrained_country_validation():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "PRODUCT OF INDM",
        "text_blocks": [
            {"text": "PRODUCT", "confidence": 0.43, "box": [[0, 0], [80, 0], [80, 20], [0, 20]]},
            {"text": "OF INDM", "confidence": 0.78, "box": [[85, 1], [160, 1], [160, 21], [85, 21]]},
        ],
    })

    assert result["countryOfOrigin"] == "India"


def test_mildly_skewed_address_row_remains_supported():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Manufactured by Example Foods Limited Plot 12 Industrial Area Model Number ZX9",
        "text_blocks": [
            {"text": "Manufactured by Example Foods Limited", "confidence": 0.90, "box": [[0, 0], [300, 0], [300, 20], [0, 20]]},
            {"text": "Plot 12", "confidence": 0.90, "box": [[0, 30], [100, 32], [100, 52], [0, 50]]},
            {"text": "Industrial Area", "confidence": 0.90, "box": [[0, 55], [150, 57], [150, 77], [0, 75]]},
            {"text": "Model Number", "confidence": 0.90, "box": [[0, 100], [150, 100], [150, 120], [0, 120]]},
        ],
    })

    assert result["manufacturerAddress"] == "Plot 12 Industrial Area"


def test_unlabelled_consumer_metadata_is_not_product_name():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Comolainis Feedback Conlact 200g",
        "text_blocks": [
            {"text": "Comolainis Feedback   Conlact", "confidence": 0.358, "box": [[0, 0], [240, 0], [240, 25], [0, 25]]},
            {"text": "200g", "confidence": 0.87, "box": [[0, 35], [70, 35], [70, 55], [0, 55]]},
        ],
    })

    assert result["productName"] is None
    assert result["netQuantity"] == "200g"


def test_explicit_generic_value_beats_metadata_fallback_at_low_confidence():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Common Genenc Name D Select Wireless Mouse DSJ20 Feedback Conlact",
        "text_blocks": [
            {"text": "Common Genenc Name", "confidence": 0.72, "box": [[0, 0], [180, 0], [180, 20], [0, 20]]},
            {"text": "D Select Wireless Mouse DSJ20", "confidence": 0.19, "box": [[0, 25], [240, 25], [240, 45], [0, 45]]},
            {"text": "Feedback Conlact", "confidence": 0.90, "box": [[0, 60], [150, 60], [150, 80], [0, 80]]},
        ],
    })

    assert result["productName"] == "D Select Wireless Mouse DSJ20"


def test_realistic_skewed_product_of_pair_is_reconstructed():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "PRODUCT OF INDM unrelated text",
        "text_blocks": [
            {"text": "PRODUCT", "confidence": 0.428, "box": [[233, 465], [279, 472], [277, 485], [231, 479]]},
            {"text": "OF INDM", "confidence": 0.776, "box": [[277, 473], [321, 473], [321, 487], [277, 487]]},
            {"text": "PRODUCT", "confidence": 0.90, "box": [[0, 0], [80, 0], [80, 20], [0, 20]]},
            {"text": "OF GERMANY", "confidence": 0.90, "box": [[400, 100], [500, 100], [500, 120], [400, 120]]},
        ],
    })

    assert result["countryOfOrigin"] == "India"


def test_unrelated_rotated_product_does_not_join_distant_origin_text():
    result = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "PRODUCT OF GERMANY",
        "text_blocks": [
            {"text": "PRODUCT", "confidence": 0.90, "box": [[20, 20], [25, 80], [45, 78], [40, 18]]},
            {"text": "OF GERMANY", "confidence": 0.90, "box": [[300, 200], [400, 200], [400, 220], [300, 220]]},
        ],
    })

    assert result["countryOfOrigin"] is None


def test_promotional_heading_and_pricing_rejected_as_product_name():
    """Tests that questions, promotional taglines, price headers, and instructions are rejected as productName."""
    # Case 1: Interrogative question heading
    res1 = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "What makes it so special? Net Wt 250ml MRP Rs 150.00 Mfg by Aura Ltd 05/2025",
        "text_blocks": [
            {"text": "What makes it so special?", "confidence": 0.95, "box": [[0, 0], [200, 0], [200, 20], [0, 20]]},
            {"text": "Net Wt 250ml", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "MRP Rs 150.00", "confidence": 0.90, "box": [[0, 60], [100, 60], [100, 80], [0, 80]]},
            {"text": "Mfg by Aura Ltd", "confidence": 0.90, "box": [[0, 90], [100, 90], [100, 110], [0, 110]]},
            {"text": "05/2025", "confidence": 0.90, "box": [[0, 120], [100, 120], [100, 140], [0, 140]]},
        ]
    })
    assert res1["productName"] is None

    # Case 2: Pricing header
    res2 = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Sale Price Net Wt 200g Product of India",
        "text_blocks": [
            {"text": "Sale Price", "confidence": 0.95, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "Net Wt 200g", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "Product of India", "confidence": 0.90, "box": [[0, 60], [120, 60], [120, 80], [0, 80]]},
        ]
    })
    assert res2["productName"] is None

    # Case 3: Usage instruction
    res3 = extract_fields({
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Directions for use: Apply gently Net Wt 100g",
        "text_blocks": [
            {"text": "Directions for use: Apply gently", "confidence": 0.92, "box": [[0, 0], [200, 0], [200, 20], [0, 20]]},
            {"text": "Net Wt 100g", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
        ]
    })
    assert res3["productName"] is None


def test_explicit_manufacturer_beats_tm_owner_and_marketer():
    """Tests that explicit manufacturer declarations outrank TM owners and marketers."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": (
            "Manufactured by Apex Pharma Private Limited Sector 12 Industrial Area\n"
            "Marketed by Apex Brands Limited Park Street Kolkata\n"
            "TM OWNERS ALPHA CREATORS LLP"
        ),
        "text_blocks": [
            {"text": "Manufactured by Apex Pharma Private Limited", "confidence": 0.92, "box": [[0, 0], [250, 0], [250, 20], [0, 20]]},
            {"text": "Sector 12 Industrial Area", "confidence": 0.90, "box": [[0, 25], [150, 25], [150, 45], [0, 45]]},
            {"text": "Marketed by Apex Brands Limited", "confidence": 0.90, "box": [[0, 50], [200, 50], [200, 70], [0, 70]]},
            {"text": "Park Street Kolkata", "confidence": 0.90, "box": [[0, 75], [120, 75], [120, 95], [0, 95]]},
            {"text": "TM OWNERS ALPHA CREATORS LLP", "confidence": 0.90, "box": [[0, 100], [200, 100], [200, 120], [0, 120]]},
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["manufacturerName"] == "Apex Pharma Private Limited"
    assert "Sector 12 Industrial Area" in fields["manufacturerAddress"]
    assert "ALPHA CREATORS" not in (fields["manufacturerName"] or "")


def test_expiry_and_batch_dates_never_assigned_to_packing_date():
    """Tests that expiry dates and batch codes are strictly rejected from monthOfPacking/yearOfPacking."""
    # Only expiry / batch date present -> must return None, None
    expiry_only = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Batch No: BR2E1728 Expiry Date 06/2029 Best Before 24 Months Net Wt 250ml",
        "text_blocks": [
            {"text": "Batch No: BR2E1728 06/29", "confidence": 0.90, "box": [[0, 0], [150, 0], [150, 20], [0, 20]]},
            {"text": "Expiry Date 06/2029", "confidence": 0.90, "box": [[0, 25], [120, 25], [120, 45], [0, 45]]},
            {"text": "Best Before 24 Months", "confidence": 0.90, "box": [[0, 50], [140, 50], [140, 70], [0, 70]]},
            {"text": "Net Wt 250ml", "confidence": 0.90, "box": [[0, 75], [100, 75], [100, 95], [0, 95]]},
        ]
    }
    res_exp = extract_fields(expiry_only)
    assert res_exp["monthOfPacking"] is None
    assert res_exp["yearOfPacking"] is None

    # Explicit Mfg Date present -> correctly extracted
    mfg_present = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Mfg Date: 08/2024 Use by 08/2026 Batch 4492",
        "text_blocks": [
            {"text": "Mfg Date: 08/2024", "confidence": 0.92, "box": [[0, 0], [120, 0], [120, 20], [0, 20]]},
            {"text": "Use by 08/2026", "confidence": 0.90, "box": [[0, 25], [100, 25], [100, 45], [0, 45]]},
            {"text": "Batch 4492", "confidence": 0.90, "box": [[0, 50], [80, 50], [80, 70], [0, 70]]},
        ]
    }
    res_mfg = extract_fields(mfg_present)
    assert res_mfg["monthOfPacking"] == "08"
    assert res_mfg["yearOfPacking"] == "2024"


def test_regulatory_license_numbers_not_extracted_as_consumer_phone():
    """Tests that FSSAI/Lic numbers are never extracted as consumerCare phone numbers."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "fssat LicNo.072299901593 For customer care contact 1800-425-4026 email: care@example.com",
        "text_blocks": [
            {"text": "fssat LicNo.072299901593", "confidence": 0.90, "box": [[0, 0], [180, 0], [180, 20], [0, 20]]},
            {"text": "For customer care contact 1800-425-4026", "confidence": 0.90, "box": [[0, 25], [250, 25], [250, 45], [0, 45]]},
            {"text": "email: care@example.com", "confidence": 0.90, "box": [[0, 50], [150, 50], [150, 70], [0, 70]]},
        ]
    }
    fields = extract_fields(ocr_result)
    assert "072299901593" not in fields["consumerCare"]
    assert "1800-425-4026" in fields["consumerCare"]
    assert "care@example.com" in fields["consumerCare"]


def test_fused_manufacturer_declaration_parsing():
    """Tests that fused label text like 'Mfd.for/Regd.officeCOMPANY' is parsed cleanly."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Md.foiRegd.office DHARAMPAL SATYAPAL FOODS LIMITED Plot 4 Sector 63 Noida",
        "text_blocks": [
            {"text": "Md.foiRegd.office DHARAMPAL SATYAPAL FOODS LIMITED", "confidence": 0.85, "box": [[0, 0], [350, 0], [350, 20], [0, 20]]},
            {"text": "Plot 4 Sector 63 Noida", "confidence": 0.85, "box": [[0, 25], [150, 25], [150, 45], [0, 45]]},
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["manufacturerName"] == "DHARAMPAL SATYAPAL FOODS LIMITED"
    assert "Sector 63 Noida" in fields["manufacturerAddress"]


def test_manufacturer_address_stops_at_fssai_and_instructions():
    """Tests that address collection terminates at FSSAI licenses, batch instructions, or other sections."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": (
            "Manufactured by Nutra Solutions Pvt Ltd Plot 15 Phase 2 Industrial Area\n"
            "fssat LicNo.072299901593\n"
            "FOR MANUFACTURING UNIT ADDRESS READ FIRST CHARACTER\n"
            "Storage instructions: Store in cool dry place"
        ),
        "text_blocks": [
            {"text": "Manufactured by Nutra Solutions Pvt Ltd", "confidence": 0.90, "box": [[0, 0], [250, 0], [250, 20], [0, 20]]},
            {"text": "Plot 15 Phase 2 Industrial Area", "confidence": 0.90, "box": [[0, 25], [200, 25], [200, 45], [0, 45]]},
            {"text": "fssat LicNo.072299901593", "confidence": 0.88, "box": [[0, 50], [160, 50], [160, 70], [0, 70]]},
            {"text": "FOR MANUFACTURING UNIT ADDRESS READ FIRST CHARACTER", "confidence": 0.85, "box": [[0, 75], [300, 75], [300, 95], [0, 95]]},
            {"text": "Storage instructions: Store in cool dry place", "confidence": 0.90, "box": [[0, 100], [250, 100], [250, 120], [0, 120]]},
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["manufacturerName"] == "Nutra Solutions Pvt Ltd"
    assert fields["manufacturerAddress"] == "Plot 15 Phase 2 Industrial Area"
    assert "LicNo" not in fields["manufacturerAddress"]
    assert "MANUFACTURING UNIT" not in fields["manufacturerAddress"]
    assert "Storage" not in fields["manufacturerAddress"]


def test_glued_price_date_stamp_extraction():
    """Tests extraction of price from stamped text where price and date are concatenated."""
    ocr_result = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "MRP Rs. 175.0007/25 (Incl. of all taxes) Net Qty 250ml",
        "text_blocks": [
            {"text": "MRP Rs. 175.0007/25 (Incl. of all taxes)", "confidence": 0.90, "box": [[0, 0], [250, 0], [250, 20], [0, 20]]},
            {"text": "Net Qty 250ml", "confidence": 0.90, "box": [[0, 25], [100, 25], [100, 45], [0, 45]]},
        ]
    }
    fields = extract_fields(ocr_result)
    assert fields["mrp"] == "MRP Rs. 175.00 (inclusive of all taxes)"
    assert fields["netQuantity"] == "250ml"


def test_extraction_confidence_penalizes_incomplete_or_ambiguous_fields():
    """Tests that missing core statutory fields downgrade confidence from HIGH to MEDIUM."""
    # Label with missing packing date
    ocr_missing_date = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Shower Gel Net Qty 250ml MRP Rs. 175.00 Mfg by Aura Ltd Sector 5",
        "text_blocks": [
            {"text": "Shower Gel", "confidence": 0.90, "box": [[0, 0], [100, 0], [100, 20], [0, 20]]},
            {"text": "Net Qty 250ml", "confidence": 0.90, "box": [[0, 30], [100, 30], [100, 50], [0, 50]]},
            {"text": "MRP Rs. 175.00", "confidence": 0.90, "box": [[0, 60], [100, 60], [100, 80], [0, 80]]},
            {"text": "Mfg by Aura Ltd", "confidence": 0.90, "box": [[0, 90], [100, 90], [100, 110], [0, 110]]},
            {"text": "Sector 5", "confidence": 0.90, "box": [[0, 120], [100, 120], [100, 140], [0, 140]]},
        ]
    }
    fields = extract_fields(ocr_missing_date)
    assert fields["monthOfPacking"] is None
    assert fields["extraction_confidence"] == "MEDIUM"


def test_bug1_mrp_lowercase_inclusive_and_unmatched_parenthesis():
    """
    Tests Bug 1 fixes:
    - Working case: 'Maximum Retail Price 899.00Inclusive of all Taxes'
    - Failing case: 'MRP 95.00inclusive of all taxes)' (lowercase inclusive & stray unmatched closing paren)
    """
    # Dell mouse working case
    dell_ocr = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Maximum Retail Price 899.00Inclusive of all Taxes",
        "text_blocks": [
            {"text": "Maximum Retail Price 899.00Inclusive of all Taxes", "confidence": 0.92, "box": [[0, 0], [300, 0], [300, 20], [0, 20]]}
        ]
    }
    dell_fields = extract_fields(dell_ocr)
    assert dell_fields["mrp"] == "MRP Rs. 899.00 (inclusive of all taxes)"

    # Chana label failing case
    chana_ocr = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "MRP 95.00inclusive of all taxes)",
        "text_blocks": [
            {"text": "MRP 95.00inclusive of all taxes)", "confidence": 0.90, "box": [[0, 0], [300, 0], [300, 20], [0, 20]]}
        ]
    }
    chana_fields = extract_fields(chana_ocr)
    assert chana_fields["mrp"] == "MRP Rs. 95.00 (inclusive of all taxes)"


def test_bug2_mfg_pack_prefix_recognition():
    """
    Tests Bug 2 fixes:
    - Working case: 'Marketed By:Dell International Services India Private Limited Crysta! Downs,EGL Business Park...'
    - Failing case: 'Mfg/Pack: Sunrise Agro Foods Pvt. Ltd Plot No.45,MIDC Industrial Area Nashik, Maharashtra - 422010'
    """
    # Dell mouse working case
    dell_ocr = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Marketed By:Dell International Services India Private Limited Crysta! Downs,EGL Business Park",
        "text_blocks": [
            {"text": "Marketed By:Dell International Services India Private Limited Crysta! Downs,EGL Business Park", "confidence": 0.95, "box": [[0, 0], [500, 0], [500, 20], [0, 20]]}
        ]
    }
    dell_fields = extract_fields(dell_ocr)
    assert dell_fields["manufacturerName"] == "Dell International Services India Private Limited"
    assert dell_fields["manufacturerAddress"] is not None
    assert "Crysta! Downs" in dell_fields["manufacturerAddress"] or "EGL Business Park" in dell_fields["manufacturerAddress"]

    # Chana label failing case
    chana_ocr = {
        "quality": {"quality_status": "ACCEPTABLE"},
        "full_text": "Mfg/Pack: Sunrise Agro Foods Pvt. Ltd Plot No.45,MIDC Industrial Area Nashik, Maharashtra - 422010",
        "text_blocks": [
            {"text": "Mfg/Pack: Sunrise Agro Foods Pvt. Ltd Plot No.45,MIDC Industrial Area Nashik, Maharashtra - 422010", "confidence": 0.92, "box": [[0, 0], [500, 0], [500, 20], [0, 20]]}
        ]
    }
    chana_fields = extract_fields(chana_ocr)
    assert chana_fields["manufacturerName"] == "Sunrise Agro Foods Pvt. Ltd"
    assert chana_fields["manufacturerAddress"] is not None
    assert "Plot No.45" in chana_fields["manufacturerAddress"]
    assert "Nashik" in chana_fields["manufacturerAddress"] or "Maharashtra" in chana_fields["manufacturerAddress"]




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
    assert labeled["netQuantity"] == "1N"

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







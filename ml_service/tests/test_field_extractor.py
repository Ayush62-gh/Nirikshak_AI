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

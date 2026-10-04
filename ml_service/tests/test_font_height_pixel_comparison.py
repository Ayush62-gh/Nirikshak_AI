import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from field_extractor import _extract_font_height_px_comparison, extract_fields


def _block(text, height, confidence=0.99):
    return {
        "text": text,
        "confidence": confidence,
        "box": [[0, 0], [100, 0], [100, height], [0, height]],
    }


def test_font_height_pixel_comparison_uses_only_statutory_blocks():
    blocks = [
        _block("Country of Origin", 19),
        _block("India", 20),
        _block("Maximum Retail Price", 24),
        _block("899.00 Inclusive of all Taxes", 26),
        _block("Enjoy smooth accurate cursor control", 43),
        _block("D", 83),
        _block("08023115104", 13),
    ]

    result = _extract_font_height_px_comparison(blocks)

    assert result["unit"] == "pixels"
    assert result["calibration_reference_used"] is False
    assert result["smallest_height_px"] == 19
    assert result["largest_height_px"] == 26
    assert result["height_range_px"] == [19, 26]
    assert [item["text"] for item in result["measured_blocks"]] == [
        "Country of Origin",
        "Maximum Retail Price",
        "899.00 Inclusive of all Taxes",
    ]


def test_font_height_pixel_comparison_has_no_physical_conversion():
    blocks = [
        _block("MRP", 24),
        _block("Net Quantity", 22),
    ]

    result = _extract_font_height_px_comparison(blocks)

    assert result["smallest_height_px"] == 22
    assert result["largest_height_px"] == 24
    assert result["median_height_px"] == 23.0


def test_extract_fields_exposes_pixel_comparison_without_changing_font_height_mm():
    ocr_result = {
        "quality": {
            "quality_status": "ACCEPTABLE",
            "blur_score": 100.0,
            "brightness": 100.0,
        },
        "full_text": "Country of Origin India MRP 899.00",
        "text_blocks": [
            _block("Country of Origin", 19),
            _block("Maximum Retail Price", 24),
        ],
    }

    fields = extract_fields(ocr_result)

    assert fields["fontHeightMm"] is None
    assert fields["fontHeightPxComparison"]["smallest_height_px"] == 19
    assert fields["fontHeightPxComparison"]["largest_height_px"] == 24


def test_font_height_pixel_comparison_returns_empty_measurements_when_no_statutory_blocks():
    result = _extract_font_height_px_comparison([
        _block("D Select Wireless Mouse", 50),
        _block("Enjoy smooth accurate cursor control", 30),
        _block("08023115104", 13),
    ])

    assert result["measured_blocks"] == []
    assert result["smallest_height_px"] is None
    assert result["largest_height_px"] is None
    assert result["median_height_px"] is None
    assert result["height_range_px"] is None

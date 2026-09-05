import pytest
import asyncio
from app.services.ocr_client import extract_fields
from app.services.rule_client import validate_compliance


@pytest.mark.anyio
async def test_extract_fields_mock():
    dummy_bytes = b"fake_image_binary_data_12345"
    filename = "test_package.jpg"

    result = await extract_fields(dummy_bytes, filename)

    assert isinstance(result, dict)
    assert "product_name" in result
    assert "manufacturer" in result
    assert "net_quantity" in result
    assert "mrp" in result
    assert "batch_number" in result
    assert "mfg_date" in result
    assert "consumer_care" in result
    assert "raw_ocr_text" in result

    assert result["product_name"] == "Sample Biscuits 200g"
    assert result["manufacturer"] == "ABC Foods Pvt Ltd"
    assert result["net_quantity"] == "200 g"
    assert result["mrp"] == "Rs. 45"


@pytest.mark.anyio
async def test_validate_compliance_mock():
    sample_extracted_fields = {
        "product_name": "Sample Biscuits 200g",
        "manufacturer": "ABC Foods Pvt Ltd",
        "net_quantity": "200 g",
        "mrp": "Rs. 45",
        "batch_number": "B12345",
        "mfg_date": "01/2026",
        "consumer_care": "1800-XXX-XXXX",
    }

    result = await validate_compliance(sample_extracted_fields)

    assert isinstance(result, dict)
    assert "status" in result
    assert "violations" in result
    assert result["status"] in ("COMPLIANT", "NON_COMPLIANT", "PARTIAL")
    assert isinstance(result["violations"], list)

    assert result["status"] == "PARTIAL"
    assert len(result["violations"]) == 1
    assert result["violations"][0]["rule"] == "Rule 6"
    assert result["violations"][0]["field"] == "consumer_care"

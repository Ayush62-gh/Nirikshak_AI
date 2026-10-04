import pytest
import httpx
from app.services.ocr_client import _parse_ocr_response, extract_fields
from app.core.config import settings


def test_parse_ocr_response_standard_mapping():
    real_ocr_response = {
        "quality": {
            "blur_score": 85.2,
            "is_blurry": False,
            "brightness": 120.0,
            "quality_status": "ACCEPTABLE",
        },
        "full_text": "Sample Biscuits Net Wt 200g MRP Rs 45 Mfg Date 05/2025 Mfd by ABC Foods",
        "text_blocks": [],
        "processed_image_path": "/tmp/proc.jpg",
        "annotated_image_path": "/tmp/ann.jpg",
        "fields": {
            "productId": None,
            "productName": "Sample Biscuits 200g",
            "productType": None,
            "isImported": False,
            "manufacturerName": "ABC Foods Pvt Ltd",
            "manufacturerAddress": "123 Industrial Estate, Delhi",
            "packerName": None,
            "importerName": None,
            "netQuantity": "200 g",
            "mrp": "Rs. 45",
            "monthOfPacking": "05",
            "yearOfPacking": "2025",
            "consumerCare": "care@abcfoods.com",
            "countryOfOrigin": None,
            "extraction_confidence": "HIGH",
        },
    }

    result = _parse_ocr_response(real_ocr_response)

    assert result["product_name"] == "Sample Biscuits 200g"
    assert result["manufacturer"] == "ABC Foods Pvt Ltd"
    assert result["net_quantity"] == "200 g"
    assert result["mrp"] == "Rs. 45"
    assert result["mfg_date"] == "05/2025"
    assert result["consumer_care"] == "care@abcfoods.com"
    assert result["raw_ocr_text"] == "Sample Biscuits Net Wt 200g MRP Rs 45 Mfg Date 05/2025 Mfd by ABC Foods"
    assert result["batch_number"] is None
    assert result["manufacturer_address"] == "123 Industrial Estate, Delhi"
    assert result["quality_status"] == "ACCEPTABLE"
    assert result["extraction_confidence"] == "HIGH"
    assert result["country_of_origin"] is None
    assert result["importer_name"] is None
    assert result["unit_sale_price"] is None
    assert result["font_size_mm"] is None
    assert result["expiry_date"] is None


def test_parse_ocr_response_null_packing_dates():
    real_ocr_response = {
        "quality": {
            "quality_status": "ACCEPTABLE",
        },
        "full_text": "Sample Product without date",
        "fields": {
            "productName": "Sample Product",
            "monthOfPacking": None,
            "yearOfPacking": None,
            "extraction_confidence": "HIGH",
        },
    }

    result = _parse_ocr_response(real_ocr_response)

    assert result["product_name"] == "Sample Product"
    assert result["mfg_date"] is None


def test_parse_ocr_response_partial_packing_dates():
    response_month_only = {
        "fields": {
            "monthOfPacking": "05",
            "yearOfPacking": None,
        }
    }
    assert _parse_ocr_response(response_month_only)["mfg_date"] is None

    response_year_only = {
        "fields": {
            "monthOfPacking": None,
            "yearOfPacking": "2025",
        }
    }
    assert _parse_ocr_response(response_year_only)["mfg_date"] is None


def test_parse_ocr_response_new_fields_present():
    # (a) new keys present when OCR returns them
    real_ocr_response = {
        "quality": {
            "quality_status": "ACCEPTABLE",
        },
        "full_text": "Sample Imported Biscuits",
        "fields": {
            "productName": "Imported Biscuits",
            "countryOfOrigin": "Belgium",
            "importerName": "Belgian Treats India Pvt Ltd",
            "unitSalePrice": "Rs. 1.25/g",
            "fontHeightMm": 2.5,
            "expiryMonth": "08",
            "expiryYear": "2027",
            "extraction_confidence": "HIGH",
        },
    }

    result = _parse_ocr_response(real_ocr_response)

    assert result["country_of_origin"] == "Belgium"
    assert result["importer_name"] == "Belgian Treats India Pvt Ltd"
    assert result["unit_sale_price"] == "Rs. 1.25/g"
    assert result["font_size_mm"] == 2.5
    assert result["expiry_date"] == "08/2027"


def test_parse_ocr_response_new_fields_none_when_absent_no_exception():
    # (b) all new keys are None, with no exception, when OCR returns none of them
    ocr_response_missing_fields = {
        "quality": {},
        "fields": {
            "productName": "Simple Product",
        },
    }

    result = _parse_ocr_response(ocr_response_missing_fields)

    assert result["country_of_origin"] is None
    assert result["importer_name"] is None
    assert result["unit_sale_price"] is None
    assert result["font_size_mm"] is None
    assert result["expiry_date"] is None
    assert result["batch_number"] is None

    # Empty payload with empty dicts or missing keys
    empty_result = _parse_ocr_response({})
    assert empty_result["country_of_origin"] is None
    assert empty_result["importer_name"] is None
    assert empty_result["unit_sale_price"] is None
    assert empty_result["font_size_mm"] is None
    assert empty_result["expiry_date"] is None
    assert empty_result["batch_number"] is None


def test_parse_ocr_response_partial_expiry_dates():
    # Expiry date should be None if only month or only year is present
    res_month_only = {
        "fields": {
            "expiryMonth": "06",
            "expiryYear": None,
        }
    }
    assert _parse_ocr_response(res_month_only)["expiry_date"] is None

    res_year_only = {
        "fields": {
            "expiryMonth": None,
            "expiryYear": "2028",
        }
    }
    assert _parse_ocr_response(res_year_only)["expiry_date"] is None


def test_parse_ocr_response_batch_number_present():
    ocr_response = {
        "fields": {
            "batchNumber": "B12345",
        }
    }
    result = _parse_ocr_response(ocr_response)
    assert result["batch_number"] == "B12345"


def test_parse_ocr_response_batch_number_absent_is_none_no_exception():
    ocr_response = {
        "fields": {
            "productName": "Product Without Batch",
        }
    }
    result = _parse_ocr_response(ocr_response)
    assert result["batch_number"] is None

    empty_response = {}
    result_empty = _parse_ocr_response(empty_response)
    assert result_empty["batch_number"] is None


@pytest.mark.anyio
async def test_extract_fields_low_confidence_does_not_raise(monkeypatch, caplog):
    low_conf_ocr_response = {
        "quality": {
            "blur_score": 12.0,
            "is_blurry": True,
            "brightness": 40.0,
            "quality_status": "POOR",
        },
        "full_text": "Blurry unreadable label text",
        "fields": {
            "productName": "Blurry Product",
            "manufacturerName": "Unknown",
            "netQuantity": None,
            "mrp": None,
            "monthOfPacking": None,
            "yearOfPacking": None,
            "consumerCare": None,
            "extraction_confidence": "LOW",
        },
    }

    async def mock_post(self, url, **kwargs):
        assert url == f"{settings.OCR_SERVICE_URL}/extract"
        assert "files" in kwargs
        assert "file" in kwargs["files"]
        req = httpx.Request("POST", url)
        return httpx.Response(200, json=low_conf_ocr_response, request=req)

    monkeypatch.setattr(settings, "use_mock_ocr", False)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    fake_bytes = b"fake_blurry_image_data"
    result = await extract_fields(fake_bytes, "blurry_image.jpg")

    assert isinstance(result, dict)
    assert result["product_name"] == "Blurry Product"
    assert result["extraction_confidence"] == "LOW"
    assert result["quality_status"] == "POOR"
    assert "LOW confidence" in caplog.text

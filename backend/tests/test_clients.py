import pytest
import httpx
from app.core.config import settings
from app.core.errors import ExternalServiceError, ExternalServiceRateLimitError
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


@pytest.mark.anyio
async def test_ocr_client_live_errors(monkeypatch):
    monkeypatch.setattr(settings, "use_mock_ocr", False)

    # 1. ConnectError
    def mock_connect_error(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_connect_error)

    with pytest.raises(ExternalServiceError) as exc_info:
        await extract_fields(b"bytes", "img.jpg")
    assert "OCR service request failed" in str(exc_info.value)

    # 2. TimeoutException
    def mock_timeout_error(*args, **kwargs):
        raise httpx.TimeoutException("Timed out")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_timeout_error)

    with pytest.raises(ExternalServiceError) as exc_info:
        await extract_fields(b"bytes", "img.jpg")
    assert "OCR service request failed" in str(exc_info.value)

    # 3. HTTP 500 error
    class Dummy500Response:
        status_code = 500
        def raise_for_status(self):
            request = httpx.Request("POST", "http://ocr/api/v1/ocr/extract")
            raise httpx.HTTPStatusError("500 Server Error", request=request, response=self)

    async def mock_500_post(*args, **kwargs):
        return Dummy500Response()
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_500_post)

    with pytest.raises(ExternalServiceError):
        await extract_fields(b"bytes", "img.jpg")

    # 4. Malformed JSON
    class DummyMalformedJsonResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            raise ValueError("Invalid JSON token")
    async def mock_malformed_json_post(*args, **kwargs):
        return DummyMalformedJsonResponse()
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_malformed_json_post)

    with pytest.raises(ExternalServiceError):
        await extract_fields(b"bytes", "img.jpg")

    # 5. Non-dict JSON (list)
    class DummyListJsonResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return ["not", "a", "dict"]
    async def mock_list_json_post(*args, **kwargs):
        return DummyListJsonResponse()
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_list_json_post)

    with pytest.raises(ExternalServiceError) as exc_info:
        await extract_fields(b"bytes", "img.jpg")
    assert "non-dict" in str(exc_info.value).lower()


@pytest.mark.anyio
async def test_rule_client_live_errors_and_mappings(monkeypatch):
    monkeypatch.setattr(settings, "use_mock_rule_engine", False)

    # 1. HTTP 429 Rate Limit
    class Dummy429Response:
        status_code = 429
        headers = {"Retry-After": "30"}

    async def mock_429_post(*args, **kwargs):
        return Dummy429Response()
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_429_post)

    with pytest.raises(ExternalServiceRateLimitError) as exc_info:
        await validate_compliance({"product_name": "Test"})
    assert exc_info.value.retry_after == "30"

    # 2. ConnectError
    def mock_connect_error(*args, **kwargs):
        raise httpx.ConnectError("Rule engine offline")
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_connect_error)

    with pytest.raises(ExternalServiceError) as exc_info:
        await validate_compliance({"product_name": "Test"})
    assert "Rule Engine service request failed" in str(exc_info.value)

    # 3. Status Mapping: PASS -> COMPLIANT, FAIL -> NON_COMPLIANT, MANUAL_REVIEW -> PARTIAL
    for engine_status, expected_internal in [("PASS", "COMPLIANT"), ("FAIL", "NON_COMPLIANT"), ("MANUAL_REVIEW", "PARTIAL")]:
        class DummyValidResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {"overallStatus": engine_status, "violations": []}

        async def mock_valid_post(*args, status=engine_status, **kwargs):
            return DummyValidResponse()
        monkeypatch.setattr(httpx.AsyncClient, "post", mock_valid_post)

        res = await validate_compliance({"product_name": "Test"})
        assert res["status"] == expected_internal


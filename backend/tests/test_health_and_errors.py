import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import ocr_client
from app import routers
from app.core.errors import ExternalServiceError

client = TestClient(app, raise_server_exceptions=False)


def test_get_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_validation_error_custom_format():
    response = client.get("/api/scans?page=abc")
    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    assert "detail" in data
    assert data["error"] == "validation_error"
    assert data["detail"] == "Invalid request parameters or payload"


def test_external_service_error_handling(monkeypatch):
    async def mock_failed_extract(*args, **kwargs):
        raise ExternalServiceError("OCR engine connection timed out")

    monkeypatch.setattr(ocr_client, "extract_fields", mock_failed_extract)

    fake_image_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
    files = {"image": ("test.jpg", fake_image_bytes, "image/jpeg")}

    response = client.post("/api/scan", files=files)
    assert response.status_code == 502
    data = response.json()

    assert data["error"] == "external_service_error"
    assert "OCR engine connection timed out" in data["detail"]
    assert "Traceback" not in str(data)


def test_generic_500_exception_handler_no_traceback_leak(monkeypatch):
    def mock_db_crash(*args, **kwargs):
        raise RuntimeError("Secret DB Password or raw internal stack trace details!")

    monkeypatch.setattr(routers.scan, "list_scans", mock_db_crash)

    response = client.get("/api/scans")
    assert response.status_code == 500
    data = response.json()

    assert data["error"] == "internal_server_error"
    assert data["detail"] == "Internal server error"
    assert "Secret DB Password" not in str(data)
    assert "Traceback" not in str(data)

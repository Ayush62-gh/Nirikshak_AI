import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import ocr_client
from app import routers
from app.core.errors import ExternalServiceError

client = TestClient(app, raise_server_exceptions=False)


def get_auth_header():
    user_payload = {
        "email": "health_tester@nirikshak.gov.in",
        "password": "Password123!",
        "full_name": "Health Tester",
    }
    reg = client.post("/api/auth/register", json=user_payload)
    if reg.status_code == 201:
        token = reg.json()["access_token"]
    else:
        login = client.post("/api/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_validation_error_custom_format():
    headers = get_auth_header()
    response = client.get("/api/scans?page=abc", headers=headers)
    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    assert "detail" in data
    assert data["error"] == "validation_error"
    assert data["detail"] == "Invalid request parameters or payload"


def test_external_service_error_handling(monkeypatch):
    headers = get_auth_header()

    async def mock_failed_extract(*args, **kwargs):
        raise ExternalServiceError("OCR engine connection timed out")

    monkeypatch.setattr(ocr_client, "extract_fields", mock_failed_extract)

    import io
    from PIL import Image
    img = Image.new("RGB", (10, 10), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    fake_image_bytes = buf.getvalue()
    files = {"image": ("test.jpg", fake_image_bytes, "image/jpeg")}

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 502
    data = response.json()

    assert data["error"] == "external_service_error"
    assert "OCR engine connection timed out" in data["detail"]
    assert "Traceback" not in str(data)


def test_generic_500_exception_handler_no_traceback_leak(monkeypatch):
    headers = get_auth_header()

    def mock_db_crash(*args, **kwargs):
        raise RuntimeError("Secret DB Password or raw internal stack trace details!")

    monkeypatch.setattr(routers.scan, "list_scans", mock_db_crash)

    response = client.get("/api/scans", headers=headers)
    assert response.status_code == 500
    data = response.json()

    assert data["error"] == "internal_server_error"
    assert data["detail"] == "Internal server error"
    assert "Secret DB Password" not in str(data)
    assert "Traceback" not in str(data)


def test_jwt_secret_validation_raises_error(monkeypatch):
    from pydantic import ValidationError
    from app.core.config import Settings

    monkeypatch.setenv("JWT_SECRET", "")
    with pytest.raises(ValidationError) as exc_info:
        Settings(JWT_SECRET="")
    assert "JWT_SECRET" in str(exc_info.value)


def test_cors_configuration_non_wildcard():
    # Valid configured origin returns matching Access-Control-Allow-Origin
    res_valid = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_valid.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res_valid.headers.get("access-control-allow-origin") != "*"

    # Unconfigured origin is rejected (no access-control-allow-origin header)
    res_invalid = client.options(
        "/api/health",
        headers={
            "Origin": "http://malicious-unauthorized-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_invalid.headers.get("access-control-allow-origin") != "http://malicious-unauthorized-site.com"
    assert res_invalid.headers.get("access-control-allow-origin") != "*"


def test_db_migration_error_logging(monkeypatch, caplog):
    import logging
    from app.db import session

    def mock_bad_connect(*args, **kwargs):
        raise RuntimeError("Simulated DB Connection Error during migration")

    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", mock_bad_connect)

    with caplog.at_level(logging.WARNING, logger="nirikshak.db"):
        session._migrate_add_user_id_column()

    assert any("Database user_id column migration check failed" in rec.message for rec in caplog.records)


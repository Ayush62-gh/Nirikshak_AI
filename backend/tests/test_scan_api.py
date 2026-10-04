import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_test_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_test_png_bytes() -> bytes:
    img = Image.new("RGBA", (100, 100), color=(0, 255, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_test_bmp_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    return buf.getvalue()


def get_auth_header():
    user_payload = {
        "email": "scan_tester@nirikshak.gov.in",
        "password": "Password123!",
        "full_name": "Scan Tester",
    }
    reg = client.post("/api/auth/register", json=user_payload)
    if reg.status_code == 201:
        token = reg.json()["access_token"]
    else:
        login = client.post("/api/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_auth_header_for_user(email: str, name: str):
    user_payload = {
        "email": email,
        "password": "Password123!",
        "full_name": name,
    }
    reg = client.post("/api/auth/register", json=user_payload)
    if reg.status_code == 201:
        token = reg.json()["access_token"]
    else:
        login = client.post("/api/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]})
        token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_requests_return_401():
    jpeg_bytes = make_test_jpeg_bytes()
    files = {"image": ("test.jpg", jpeg_bytes, "image/jpeg")}

    # POST /api/scan without auth -> 401
    res1 = client.post("/api/scan", files=files)
    assert res1.status_code == 401

    # GET /api/scans without auth -> 401
    res2 = client.get("/api/scans")
    assert res2.status_code == 401

    # GET /api/scans/{id} without auth -> 401
    res3 = client.get("/api/scans/some-id")
    assert res3.status_code == 401


def test_post_scan_valid_jpeg():
    headers = get_auth_header()
    jpeg_bytes = make_test_jpeg_bytes()
    files = {
        "image": ("test_label.jpg", jpeg_bytes, "image/jpeg")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert "scan_id" in data
    assert "timestamp" in data
    assert "product" in data
    assert "compliance" in data
    assert "extracted_fields" in data
    assert "image_ref" in data

    assert data["product"]["product_name"] == "Sample Biscuits 200g"
    assert data["compliance"]["status"] == "PARTIAL"


def test_post_scan_valid_png():
    headers = get_auth_header()
    png_bytes = make_test_png_bytes()
    files = {
        "image": ("test_label.png", png_bytes, "image/png")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert "scan_id" in data
    assert data["product"]["product_name"] == "Sample Biscuits 200g"


def test_post_scan_empty_file():
    headers = get_auth_header()
    files = {
        "image": ("empty.jpg", b"", "image/jpeg")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_image"
    assert "empty" in data["detail"].lower()


def test_post_scan_invalid_random_bytes():
    headers = get_auth_header()
    random_bytes = b"This is a text file pretending to be an image. 1234567890"
    files = {
        "image": ("fake.jpg", random_bytes, "image/jpeg")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_image"


def test_post_scan_jpeg_with_incorrect_content_type():
    headers = get_auth_header()
    jpeg_bytes = make_test_jpeg_bytes()
    files = {
        "image": ("label.bin", jpeg_bytes, "application/octet-stream")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 201
    assert "scan_id" in response.json()


def test_post_scan_png_with_incorrect_content_type():
    headers = get_auth_header()
    png_bytes = make_test_png_bytes()
    files = {
        "image": ("document.txt", png_bytes, "text/plain")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 201
    assert "scan_id" in response.json()


def test_post_scan_unsupported_format_bmp():
    headers = get_auth_header()
    bmp_bytes = make_test_bmp_bytes()
    files = {
        "image": ("label.bmp", bmp_bytes, "image/bmp")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_image"
    assert "unsupported" in data["detail"].lower() or "bmp" in data["detail"].lower()


def test_post_scan_file_at_size_limit():
    headers = get_auth_header()
    base_jpeg = make_test_jpeg_bytes()
    limit = 10 * 1024 * 1024
    padded_jpeg = base_jpeg + b"\x00" * (limit - len(base_jpeg))
    assert len(padded_jpeg) == limit

    files = {
        "image": ("limit.jpg", padded_jpeg, "image/jpeg")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 201
    assert "scan_id" in response.json()


def test_post_scan_file_exceeding_size_limit():
    headers = get_auth_header()
    base_jpeg = make_test_jpeg_bytes()
    limit = 10 * 1024 * 1024
    oversized_jpeg = base_jpeg + b"\x00" * (limit + 1 - len(base_jpeg))
    assert len(oversized_jpeg) == limit + 1

    files = {
        "image": ("oversized.jpg", oversized_jpeg, "image/jpeg")
    }

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "file_too_large"
    assert "10mb" in data["detail"].lower()


def test_get_scans_list_and_get_by_id():
    headers = get_auth_header()
    jpeg_bytes = make_test_jpeg_bytes()
    files = {
        "image": ("package_scan.png", jpeg_bytes, "image/png")
    }
    post_res = client.post("/api/scan", files=files, headers=headers)
    assert post_res.status_code == 201
    created_scan_id = post_res.json()["scan_id"]

    get_list_res = client.get("/api/scans", headers=headers)
    assert get_list_res.status_code == 200
    list_data = get_list_res.json()
    assert "scans" in list_data
    assert "total" in list_data
    assert list_data["total"] >= 1
    scan_ids = [s["scan_id"] for s in list_data["scans"]]
    assert created_scan_id in scan_ids

    get_id_res = client.get(f"/api/scans/{created_scan_id}", headers=headers)
    assert get_id_res.status_code == 200
    id_data = get_id_res.json()
    assert id_data["scan_id"] == created_scan_id
    assert id_data["product"]["product_name"] == "Sample Biscuits 200g"


def test_get_scans_pagination_total_count():
    headers = get_auth_header()
    jpeg_bytes = make_test_jpeg_bytes()
    for i in range(3):
        files = {"image": (f"test_page_{i}.jpg", jpeg_bytes, "image/jpeg")}
        res = client.post("/api/scan", files=files, headers=headers)
        assert res.status_code == 201

    response = client.get("/api/scans?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["scans"]) == 2
    assert data["total"] >= 3
    assert data["total"] > len(data["scans"])


def test_get_scan_by_invalid_id_returns_404():
    headers = get_auth_header()
    invalid_id = "non-existent-scan-id-99999"
    response = client.get(f"/api/scans/{invalid_id}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "detail" in data
    assert data["error"] == "Not Found"


def test_user_scan_isolation():
    user_a_headers = get_auth_header_for_user("user_a@nirikshak.gov.in", "User A")
    user_b_headers = get_auth_header_for_user("user_b@nirikshak.gov.in", "User B")

    jpeg_bytes = make_test_jpeg_bytes()

    # 1. User A creates scan
    files_a = {"image": ("user_a_scan.jpg", jpeg_bytes, "image/jpeg")}
    res_a = client.post("/api/scan", files=files_a, headers=user_a_headers)
    assert res_a.status_code == 201
    scan_id_a = res_a.json()["scan_id"]

    # 2. User B creates scan
    files_b = {"image": ("user_b_scan.jpg", jpeg_bytes, "image/jpeg")}
    res_b = client.post("/api/scan", files=files_b, headers=user_b_headers)
    assert res_b.status_code == 201
    scan_id_b = res_b.json()["scan_id"]

    # 3. User A can retrieve User A's scan
    get_a_own = client.get(f"/api/scans/{scan_id_a}", headers=user_a_headers)
    assert get_a_own.status_code == 200
    assert get_a_own.json()["scan_id"] == scan_id_a

    # 4. User B CANNOT retrieve User A's scan (returns 404)
    get_b_other = client.get(f"/api/scans/{scan_id_a}", headers=user_b_headers)
    assert get_b_other.status_code == 404
    assert get_b_other.json()["error"] == "Not Found"

    # 5. User A's scan does NOT appear in User B's scan list
    list_b = client.get("/api/scans", headers=user_b_headers)
    assert list_b.status_code == 200
    scans_b = list_b.json()["scans"]
    ids_b = [s["scan_id"] for s in scans_b]
    assert scan_id_a not in ids_b
    assert scan_id_b in ids_b

    # 6. User B's scan does NOT appear in User A's scan list
    list_a = client.get("/api/scans", headers=user_a_headers)
    assert list_a.status_code == 200
    scans_a = list_a.json()["scans"]
    ids_a = [s["scan_id"] for s in scans_a]
    assert scan_id_b not in ids_a
    assert scan_id_a in ids_a


def test_post_scan_rule_engine_rate_limit_returns_429(monkeypatch):
    from app.services import rule_client
    from app.core.errors import ExternalServiceRateLimitError

    headers = get_auth_header()

    async def mock_rate_limit(*args, **kwargs):
        raise ExternalServiceRateLimitError("Rule Engine rate limit exceeded", retry_after="60")

    monkeypatch.setattr(rule_client, "validate_compliance", mock_rate_limit)

    jpeg_bytes = make_test_jpeg_bytes()
    files = {"image": ("test_label.jpg", jpeg_bytes, "image/jpeg")}

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 429
    data = response.json()
    assert data["error"] == "rate_limit_exceeded"
    assert data["detail"] == "Rule Engine rate limit exceeded"
    assert response.headers.get("retry-after") == "60"


def test_post_scan_failure_prevents_db_persistence(monkeypatch):
    from app.services import ocr_client
    from app.core.errors import ExternalServiceError

    headers = get_auth_header()

    # Get initial scans count
    initial_list = client.get("/api/scans", headers=headers).json()
    initial_total = initial_list["total"]

    # Mock OCR client failure
    async def mock_ocr_failure(*args, **kwargs):
        raise ExternalServiceError("OCR microservice unavailable")

    monkeypatch.setattr(ocr_client, "extract_fields", mock_ocr_failure)

    jpeg_bytes = make_test_jpeg_bytes()
    files = {"image": ("test_label.jpg", jpeg_bytes, "image/jpeg")}

    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 502
    assert response.json()["error"] == "external_service_error"

    # Verify no new scan was added to DB
    final_list = client.get("/api/scans", headers=headers).json()
    assert final_list["total"] == initial_total


def test_post_scan_and_get_scans_new_extracted_fields(monkeypatch):
    from app.services import ocr_client

    headers = get_auth_header()

    mock_extracted = {
        "product_name": "Imported Pasta 500g",
        "manufacturer": "Italian Foods SpA",
        "net_quantity": "500 g",
        "mrp": "Rs. 250",
        "batch_number": None,
        "mfg_date": "03/2026",
        "consumer_care": "care@pasta.it",
        "raw_ocr_text": "Sample text",
        "manufacturer_address": "Rome, Italy",
        "quality_status": "ACCEPTABLE",
        "extraction_confidence": "HIGH",
        "country_of_origin": "Italy",
        "importer_name": "Indo Italian Imports Pvt Ltd",
        "unit_sale_price": "Rs. 0.50/g",
        "font_size_mm": 2.2,
        "expiry_date": "03/2028",
    }

    async def mock_extract(*args, **kwargs):
        return mock_extracted

    monkeypatch.setattr(ocr_client, "extract_fields", mock_extract)

    jpeg_bytes = make_test_jpeg_bytes()
    files = {"image": ("test_label.jpg", jpeg_bytes, "image/jpeg")}

    # 1. POST /api/scan response contains new fields under extracted_fields
    response = client.post("/api/scan", files=files, headers=headers)
    assert response.status_code == 201
    data = response.json()
    scan_id = data["scan_id"]
    extracted = data["extracted_fields"]
    assert extracted["country_of_origin"] == "Italy"
    assert extracted["importer_name"] == "Indo Italian Imports Pvt Ltd"
    assert extracted["unit_sale_price"] == "Rs. 0.50/g"
    assert extracted["font_size_mm"] == 2.2
    assert extracted["expiry_date"] == "03/2028"

    # 2. GET /api/scans response contains new fields under extracted_fields
    list_response = client.get("/api/scans", headers=headers)
    assert list_response.status_code == 200
    scans = list_response.json()["scans"]
    target_scan = next(s for s in scans if s["scan_id"] == scan_id)
    assert target_scan["extracted_fields"]["country_of_origin"] == "Italy"
    assert target_scan["extracted_fields"]["importer_name"] == "Indo Italian Imports Pvt Ltd"
    assert target_scan["extracted_fields"]["unit_sale_price"] == "Rs. 0.50/g"
    assert target_scan["extracted_fields"]["font_size_mm"] == 2.2
    assert target_scan["extracted_fields"]["expiry_date"] == "03/2028"

    # 3. GET /api/scans/{id} response contains new fields under extracted_fields
    detail_response = client.get(f"/api/scans/{scan_id}", headers=headers)
    assert detail_response.status_code == 200
    detail_extracted = detail_response.json()["extracted_fields"]
    assert detail_extracted["country_of_origin"] == "Italy"
    assert detail_extracted["importer_name"] == "Indo Italian Imports Pvt Ltd"
    assert detail_extracted["unit_sale_price"] == "Rs. 0.50/g"
    assert detail_extracted["font_size_mm"] == 2.2
    assert detail_extracted["expiry_date"] == "03/2028"


def test_post_scan_multi_success(monkeypatch):
    from app.services import ocr_client

    mock_extracted = {
        "product_name": "Sample Biscuits 200g",
        "manufacturer": "ABC Foods Pvt Ltd",
        "net_quantity": "200 g",
        "mrp": "Rs. 45",
        "batch_number": "B12345",
        "mfg_date": "01/2026",
        "consumer_care": "1800-XXX-XXXX",
        "raw_ocr_text": "Sample Biscuits 200g",
        "manufacturer_address": "Delhi, India",
        "quality_status": "ACCEPTABLE",
        "extraction_confidence": "HIGH",
        "country_of_origin": "India",
        "importer_name": None,
        "unit_sale_price": "Rs. 0.225/g",
        "font_size_mm": 1.8,
        "expiry_date": "01/2027",
    }

    async def mock_extract_multi(*args, **kwargs):
        return mock_extracted

    monkeypatch.setattr(ocr_client, "extract_fields_multi", mock_extract_multi)

    headers = get_auth_header()
    jpeg_bytes = make_test_jpeg_bytes()
    png_bytes = make_test_png_bytes()

    files = [
        ("images", ("front.jpg", jpeg_bytes, "image/jpeg")),
        ("images", ("back.png", png_bytes, "image/png")),
    ]

    response = client.post("/api/scan/multi", files=files, headers=headers)
    assert response.status_code == 201
    data = response.json()

    # ScanResponse shape
    assert "scan_id" in data
    assert "user_id" in data
    assert "timestamp" in data
    assert "product" in data
    assert "compliance" in data
    assert "extracted_fields" in data
    assert "image_ref" in data
    assert data["image_ref"] == "uploads/front.jpg"

    # New extracted_fields keys present
    extracted = data["extracted_fields"]
    assert "country_of_origin" in extracted
    assert "importer_name" in extracted
    assert "unit_sale_price" in extracted
    assert "font_size_mm" in extracted
    assert "expiry_date" in extracted
    assert extracted["country_of_origin"] == "India"
    assert extracted["unit_sale_price"] == "Rs. 0.225/g"
    assert extracted["font_size_mm"] == 1.8
    assert extracted["expiry_date"] == "01/2027"


def test_post_scan_multi_more_than_4_images():
    headers = get_auth_header()
    jpeg_bytes = make_test_jpeg_bytes()

    files = [
        ("images", (f"img_{i}.jpg", jpeg_bytes, "image/jpeg"))
        for i in range(5)
    ]

    response = client.post("/api/scan/multi", files=files, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "detail" in data
    assert data["error"] == "too_many_images"


def test_post_scan_multi_invalid_file_among_valid_ones():
    headers = get_auth_header()

    initial_list = client.get("/api/scans", headers=headers).json()
    initial_total = initial_list["total"]

    valid_jpeg = make_test_jpeg_bytes()
    corrupted_data = b"not a valid image content at all"

    files = [
        ("images", ("front.jpg", valid_jpeg, "image/jpeg")),
        ("images", ("corrupted.jpg", corrupted_data, "image/jpeg")),
    ]

    response = client.post("/api/scan/multi", files=files, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "invalid_image"

    # Confirm no DB row was saved
    final_list = client.get("/api/scans", headers=headers).json()
    assert final_list["total"] == initial_total


def test_post_scan_multi_no_auth():
    jpeg_bytes = make_test_jpeg_bytes()
    files = [
        ("images", ("front.jpg", jpeg_bytes, "image/jpeg")),
        ("images", ("back.jpg", jpeg_bytes, "image/jpeg")),
    ]

    response = client.post("/api/scan/multi", files=files)
    assert response.status_code in (401, 403)




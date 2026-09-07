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



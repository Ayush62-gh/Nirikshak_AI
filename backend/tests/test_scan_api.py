import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_post_scan_valid_image():
    # Fake small JPEG image content
    fake_image_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
    files = {
        "image": ("test_label.jpg", fake_image_bytes, "image/jpeg")
    }

    response = client.post("/api/scan", files=files)
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


def test_post_scan_invalid_content_type():
    fake_text_bytes = b"This is a text file, not an image."
    files = {
        "image": ("document.txt", fake_text_bytes, "text/plain")
    }

    response = client.post("/api/scan", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "detail" in data
    assert data["error"] == "invalid_image"
    assert "content-type" in data["detail"].lower() or "image" in data["detail"].lower()


def test_get_scans_list_and_get_by_id():
    # 1. Create a scan first
    fake_image_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
    files = {
        "image": ("package_scan.png", fake_image_bytes, "image/png")
    }
    post_res = client.post("/api/scan", files=files)
    assert post_res.status_code == 201
    created_scan_id = post_res.json()["scan_id"]

    # 2. GET /api/scans and assert created scan appears
    get_list_res = client.get("/api/scans")
    assert get_list_res.status_code == 200
    list_data = get_list_res.json()
    assert "scans" in list_data
    assert "total" in list_data
    assert list_data["total"] >= 1
    scan_ids = [s["scan_id"] for s in list_data["scans"]]
    assert created_scan_id in scan_ids

    # 3. GET /api/scans/{scan_id} for valid id
    get_id_res = client.get(f"/api/scans/{created_scan_id}")
    assert get_id_res.status_code == 200
    id_data = get_id_res.json()
    assert id_data["scan_id"] == created_scan_id
    assert id_data["product"]["product_name"] == "Sample Biscuits 200g"


def test_get_scans_pagination_total_count():
    fake_image_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xFF\xD9"
    for i in range(3):
        files = {"image": (f"test_page_{i}.jpg", fake_image_bytes, "image/jpeg")}
        res = client.post("/api/scan", files=files)
        assert res.status_code == 201

    response = client.get("/api/scans?page=1&limit=2")
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["scans"]) == 2
    assert data["total"] >= 3
    assert data["total"] > len(data["scans"])


def test_get_scan_by_invalid_id_returns_404():
    invalid_id = "non-existent-scan-id-99999"
    response = client.get(f"/api/scans/{invalid_id}")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "detail" in data
    assert data["error"] == "Not Found"

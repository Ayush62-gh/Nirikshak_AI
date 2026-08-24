import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import ocr
from api import app


def create_dummy_image(image_path):
    """Creates a temporary valid image with text for testing."""
    image = np.full((200, 400, 3), 255, dtype=np.uint8)
    cv2.putText(
        image,
        "MRP Rs 120",
        (30, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 0),
        2
    )
    cv2.imwrite(str(image_path), image)


def test_health_endpoint():
    """GET /health returns 200 and status ok."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_extract_endpoint_valid_image(tmp_path, monkeypatch):
    """POST /extract with a valid image returns 200 and exact required JSON keys."""
    image_path = tmp_path / "test_product.jpg"
    create_dummy_image(image_path)

    class FakeReader:
        def readtext(self, image, detail, paragraph):
            return [
                (
                    [[10, 20], [200, 20], [200, 60], [10, 60]],
                    "MRP Rs 120",
                    np.float32(0.95)
                )
            ]

    monkeypatch.setattr(
        ocr.easyocr,
        "Reader",
        lambda *args, **kwargs: FakeReader()
    )

    with TestClient(app) as client:
        with open(image_path, "rb") as img_file:
            files = {"file": ("test_product.jpg", img_file, "image/jpeg")}
            response = client.post("/extract", files=files)

        assert response.status_code == 200
        data = response.json()

        expected_keys = {
            "quality",
            "full_text",
            "text_blocks",
            "processed_image_path",
            "annotated_image_path",
            "fields"
        }
        assert set(data.keys()) == expected_keys
        assert data["full_text"] == "MRP Rs 120"
        assert len(data["text_blocks"]) == 1
        assert "blur_score" in data["quality"]
        assert "mrp" in data["fields"]


def test_extract_endpoint_non_image_file(tmp_path):
    """POST /extract with a non-image file returns 400."""
    text_file = tmp_path / "sample.txt"
    text_file.write_text("This is plain text, not an image.", encoding="utf-8")

    with TestClient(app) as client:
        with open(text_file, "rb") as f:
            files = {"file": ("sample.txt", f, "text/plain")}
            response = client.post("/extract", files=files)

        assert response.status_code == 400
        assert "Invalid image format" in response.json()["detail"]


def test_extract_endpoint_corrupt_image(tmp_path):
    """POST /extract with a corrupt image file returns 400."""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"not real image bytes")

    with TestClient(app) as client:
        with open(corrupt_file, "rb") as f:
            files = {"file": ("corrupt.jpg", f, "image/jpeg")}
            response = client.post("/extract", files=files)

        assert response.status_code == 400
        assert response.json()["detail"] is not None


def test_easyocr_singleton_loaded_once_at_startup(tmp_path, monkeypatch):
    """Confirms EasyOCR.Reader is instantiated only once at service startup, not per request."""
    init_count = 0

    class CountingReader:
        def __init__(self, *args, **kwargs):
            nonlocal init_count
            init_count += 1

        def readtext(self, image, detail, paragraph):
            return []

    monkeypatch.setattr(ocr.easyocr, "Reader", CountingReader)

    image_path = tmp_path / "test.jpg"
    create_dummy_image(image_path)

    with TestClient(app) as client:
        # Service startup lifespan initialized the reader once
        assert init_count == 1

        with open(image_path, "rb") as f1:
            res1 = client.post("/extract", files={"file": ("test.jpg", f1, "image/jpeg")})
            assert res1.status_code == 200

        with open(image_path, "rb") as f2:
            res2 = client.post("/extract", files={"file": ("test.jpg", f2, "image/jpeg")})
            assert res2.status_code == 200

        # init_count must remain 1 after multiple requests
        assert init_count == 1

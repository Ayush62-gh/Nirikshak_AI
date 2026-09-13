import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import image_processor
import paddle_ocr
from api import app


def create_dummy_image(image_path, text="MRP Rs 120"):
    """Creates a temporary valid image with text for testing."""
    image = np.full((200, 400, 3), 255, dtype=np.uint8)
    cv2.putText(
        image,
        text,
        (30, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 0),
        2
    )
    cv2.imwrite(str(image_path), image)


def test_extract_multi_endpoint_consensus(tmp_path, monkeypatch):
    """POST /extract-multi with agreeing images merges fields with consensus."""
    img1 = tmp_path / "front.jpg"
    img2 = tmp_path / "back.jpg"
    create_dummy_image(img1, "MRP Rs 100")
    create_dummy_image(img2, "MRP Rs 100")

    class FakePaddleReader:
        def ocr(self, image, cls=False):
            return [[[
                [[10, 20], [200, 20], [200, 60], [10, 60]],
                ("MRP Rs 100 (inclusive of all taxes)", np.float32(0.95))
            ]]]

    monkeypatch.setattr(paddle_ocr, "get_paddle_reader", lambda: FakePaddleReader())

    with TestClient(app) as client:
        with open(img1, "rb") as f1, open(img2, "rb") as f2:
            files = [
                ("files", ("front.jpg", f1, "image/jpeg")),
                ("files", ("back.jpg", f2, "image/jpeg"))
            ]
            response = client.post("/extract-multi", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["total_images"] == 2
        assert data["successful_images"] == 2
        assert data["fields"]["mrp"] is not None
        assert "100" in data["fields"]["mrp"]
        assert data["extraction_conflicts"] == {}


def test_extract_multi_endpoint_conflict_resolution(tmp_path, monkeypatch):
    """POST /extract-multi resolves disagreeing fields using higher OCR confidence tie-breaker."""
    img1 = tmp_path / "front.jpg"
    img2 = tmp_path / "back.jpg"
    create_dummy_image(img1, "MRP Rs 99")
    create_dummy_image(img2, "MRP Rs 150")

    call_count = 0

    def mock_extract_text(image_path, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {
                "success": True,
                "full_text": "MRP Rs. 99.00 (inclusive of all taxes) Net Qty: 1N Mfg by: Test Co",
                "text_blocks": [
                    {
                        "box": [[10, 20], [200, 20], [200, 60], [10, 60]],
                        "text": "MRP Rs. 99.00 (inclusive of all taxes) Net Qty: 1N Mfg by: Test Co",
                        "confidence": 0.95
                    }
                ],
                "annotated_image_path": None
            }
        else:
            return {
                "success": True,
                "full_text": "MRP Rs. 150.00 (inclusive of all taxes) Net Qty: 1N Mfg by: Test Co",
                "text_blocks": [
                    {
                        "box": [[10, 20], [200, 20], [200, 60], [10, 60]],
                        "text": "MRP Rs. 150.00 (inclusive of all taxes) Net Qty: 1N Mfg by: Test Co",
                        "confidence": 0.65
                    }
                ],
                "annotated_image_path": None
            }

    monkeypatch.setattr(paddle_ocr, "extract_text", mock_extract_text)

    with TestClient(app) as client:
        with open(img1, "rb") as f1, open(img2, "rb") as f2:
            files = [
                ("files", ("front.jpg", f1, "image/jpeg")),
                ("files", ("back.jpg", f2, "image/jpeg"))
            ]
            response = client.post("/extract-multi", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["fields"]["mrp"] == "MRP Rs. 99.00 (inclusive of all taxes)"
        assert "mrp" in data["extraction_conflicts"]
        assert data["extraction_conflicts"]["mrp"]["resolved_value"] == "MRP Rs. 99.00 (inclusive of all taxes)"


def test_fallback_preprocessed_retry(tmp_path, monkeypatch):
    """process_product_image retries with preprocess.py if raw pass misses required fields on ACCEPTABLE image."""
    img = tmp_path / "acceptable.jpg"
    create_dummy_image(img, "Dell Mouse")

    calls = []

    def mock_extract_text(image_path, **kwargs):
        path_str = str(image_path)
        calls.append(path_str)
        if "processed_images" not in path_str:
            # First pass on RAW image: misses MRP
            return {
                "success": True,
                "full_text": "Dell International Services India Private Limited",
                "text_blocks": [
                    {
                        "box": [[10, 20], [200, 20], [200, 60], [10, 60]],
                        "text": "Dell International Services India Private Limited",
                        "confidence": 0.92
                    }
                ],
                "annotated_image_path": None
            }
        else:
            # Secondary pass on PREPROCESSED image: recovers MRP
            return {
                "success": True,
                "full_text": "MRP Rs. 899.00 (inclusive of all taxes)",
                "text_blocks": [
                    {
                        "box": [[10, 20], [200, 20], [200, 60], [10, 60]],
                        "text": "MRP Rs. 899.00 (inclusive of all taxes)",
                        "confidence": 0.94
                    }
                ],
                "annotated_image_path": None
            }

    monkeypatch.setattr(paddle_ocr, "extract_text", mock_extract_text)

    result = image_processor.process_product_image(str(img))
    assert result["retried_preprocessed"] is True

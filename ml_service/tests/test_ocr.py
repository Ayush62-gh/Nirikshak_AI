import json
from pathlib import Path

import cv2
import numpy as np

import image_processor
import ocr
from quality_checker import check_image_quality


def create_test_image(image_path):
    """Testing ke liye temporary readable image banata hai."""

    image = np.full(
        (200, 400, 3),
        255,
        dtype=np.uint8
    )

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


def test_missing_image():
    """Missing image par safe error aana chahiye."""

    result = image_processor.process_product_image(
        "this_image_does_not_exist.jpg"
    )

    assert result["success"] is False
    assert result["error"] == "IMAGE_NOT_FOUND"
    assert result["full_text"] == ""
    assert result["text_blocks"] == []


def test_unsupported_format(tmp_path):
    """Unsupported extension reject honi chahiye."""

    text_file = tmp_path / "product.txt"
    text_file.write_text(
        "This is not an image.",
        encoding="utf-8"
    )

    result = check_image_quality(str(text_file))

    assert result["success"] is False
    assert result["error"] == "UNSUPPORTED_FORMAT"


def test_corrupt_image(tmp_path):
    """Fake JPG file ko corrupt image detect karna chahiye."""

    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(
        b"This is not valid image data"
    )

    result = check_image_quality(str(corrupt_file))

    assert result["success"] is False
    assert result["error"] == "CORRUPT_IMAGE"


def test_ocr_output_is_json_serializable(
    tmp_path,
    monkeypatch
):
    """
    Fake controlled OCR result se check karta hai ki
    text, confidence aur boxes JSON serializable hain.
    """

    image_path = tmp_path / "product.jpg"
    create_test_image(image_path)

    class FakeReader:
        def readtext(self, image, detail, paragraph):
            return [
                (
                    [
                        [10, 20],
                        [200, 20],
                        [200, 60],
                        [10, 60]
                    ],
                    "MRP Rs 120",
                    np.float32(0.94)
                )
            ]

    monkeypatch.setattr(
        ocr.easyocr,
        "Reader",
        lambda *args, **kwargs: FakeReader()
    )

    annotation_folder = tmp_path / "annotated"

    result = ocr.extract_text(
        str(image_path),
        create_annotation=True,
        annotation_folder=str(annotation_folder)
    )

    # Error raise nahi hona chahiye
    json_output = json.dumps(
        result,
        ensure_ascii=False
    )

    assert result["success"] is True
    assert result["full_text"] == "MRP Rs 120"
    assert len(result["text_blocks"]) == 1
    assert isinstance(
        result["text_blocks"][0]["confidence"],
        float
    )
    assert isinstance(
        result["text_blocks"][0]["box"][0][0],
        int
    )
    assert json_output is not None
    assert Path(
        result["annotated_image_path"]
    ).exists()


def test_no_text_detected(tmp_path, monkeypatch):
    """No text milne par empty result safely return hona chahiye."""

    image_path = tmp_path / "blank.jpg"
    create_test_image(image_path)

    class EmptyReader:
        def readtext(self, image, detail, paragraph):
            return []

    monkeypatch.setattr(
        ocr.easyocr,
        "Reader",
        lambda *args, **kwargs: EmptyReader()
    )

    result = ocr.extract_text(
        str(image_path)
    )

    assert result["success"] is True
    assert result["full_text"] == ""
    assert result["text_blocks"] == []
    assert result["annotated_image_path"] is None


def test_final_required_output_format(monkeypatch):
    """Final process_product_image output keys check karta hai."""

    monkeypatch.setattr(
        image_processor,
        "check_image_quality",
        lambda image_path: {
            "success": True,
            "quality": {
                "blur_score": 125.4,
                "is_blurry": False,
                "brightness": 142.0,
                "quality_status": "ACCEPTABLE"
            }
        }
    )

    monkeypatch.setattr(
        image_processor,
        "preprocess_product_image",
        lambda image_path, output_folder: {
            "success": True,
            "processed_image_path":
                "processed_images/product_processed.jpg"
        }
    )

    monkeypatch.setattr(
        image_processor,
        "extract_text",
        lambda image_path,
        create_annotation,
        annotation_folder: {
            "success": True,
            "full_text": "MRP Rs 120",
            "text_blocks": [
                {
                    "text": "MRP Rs 120",
                    "confidence": 0.94,
                    "box": [
                        [20, 40],
                        [200, 40],
                        [200, 80],
                        [20, 80]
                    ]
                }
            ],
            "annotated_image_path":
                "annotated_images/product_annotated.jpg"
        }
    )

    result = image_processor.process_product_image(
        "product.jpg"
    )

    assert set(result.keys()) == {
        "quality",
        "full_text",
        "text_blocks",
        "processed_image_path",
        "annotated_image_path"
    }

    json.dumps(result)


def test_multiple_image_support(monkeypatch):
    """Multiple images ke counts aur combined text check karta hai."""

    def fake_process_product_image(image_path):
        return {
            "quality": {
                "blur_score": 150.0,
                "is_blurry": False,
                "brightness": 120.0,
                "quality_status": "ACCEPTABLE"
            },
            "full_text": f"Text from {image_path}",
            "text_blocks": [],
            "processed_image_path":
                f"processed_images/{image_path}",
            "annotated_image_path":
                f"annotated_images/{image_path}"
        }

    monkeypatch.setattr(
        image_processor,
        "process_product_image",
        fake_process_product_image
    )

    result = image_processor.process_product_images([
        "front.jpg",
        "back.jpg"
    ])

    assert result["total_images"] == 2
    assert result["successful_images"] == 2
    assert result["failed_images"] == 0
    assert len(result["results"]) == 2
    assert "Text from front.jpg" in result[
        "combined_full_text"
    ]
    assert "Text from back.jpg" in result[
        "combined_full_text"
    ]

    json.dumps(result)
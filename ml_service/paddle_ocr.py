"""PaddleOCR PP-OCRv3 adapter for Nirikshak AI ML Service."""

import os
import time
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_paddle_reader = None
_paddle_initialization_seconds = None


def _empty_result(message="PaddleOCR completed, but no text was detected."):
    return {
        "success": True,
        "message": message,
        "full_text": "",
        "text_blocks": [],
        "annotated_image_path": None
    }


def _load_paddle_ocr():
    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    from paddleocr import PaddleOCR

    return PaddleOCR(
        lang="en",
        use_gpu=False,
        use_angle_cls=False,
        enable_mkldnn=False,
        show_log=False,
        ocr_version="PP-OCRv3"
    )


def get_paddle_reader():
    """Return the process-local PaddleOCR reader, initializing it once."""
    global _paddle_reader, _paddle_initialization_seconds

    if _paddle_reader is None:
        started = time.perf_counter()
        _paddle_reader = _load_paddle_ocr()
        _paddle_initialization_seconds = time.perf_counter() - started

    return _paddle_reader


def get_paddle_initialization_seconds():
    return _paddle_initialization_seconds


def reset_paddle_reader():
    """Reset the cached reader for isolated tests and benchmark runs."""
    global _paddle_reader, _paddle_initialization_seconds
    _paddle_reader = None
    _paddle_initialization_seconds = None


def _as_box(value):
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None

    box = []
    for point in value:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            return None
        try:
            box.append([int(point[0]), int(point[1])])
        except (TypeError, ValueError, OverflowError):
            return None

    return box


def _iter_lines(raw_result):
    if raw_result is None:
        return

    pages = raw_result if isinstance(raw_result, list) else [raw_result]
    for page in pages:
        if isinstance(page, dict):
            lines = page.get("ocr_results", page.get("rec_texts"))
            if isinstance(lines, list):
                yield from lines
            continue

        if isinstance(page, list):
            yield from page


def normalize_paddle_result(raw_result):
    """Convert PaddleOCR 2.x output into the existing OCR block contract."""
    text_blocks = []
    text_parts = []

    for line in _iter_lines(raw_result):
        if not isinstance(line, (list, tuple)) or len(line) < 2:
            continue

        box = _as_box(line[0])
        recognition = line[1]
        if box is None or not isinstance(recognition, (list, tuple)):
            continue
        if len(recognition) < 2:
            continue

        text = str(recognition[0]).strip()
        try:
            confidence = float(recognition[1])
        except (TypeError, ValueError, OverflowError):
            continue

        if not text:
            continue

        text_blocks.append({
            "text": text,
            "confidence": confidence,
            "box": box
        })
        text_parts.append(text)

    if not text_blocks:
        return _empty_result()

    return {
        "success": True,
        "message": "PaddleOCR text extracted successfully.",
        "full_text": " ".join(text_parts),
        "text_blocks": text_blocks,
        "annotated_image_path": None
    }


def create_annotated_image(
    image,
    text_blocks,
    input_path,
    output_folder="annotated_images"
):
    """
    Draws bounding boxes around detected text blocks and saves annotated image.
    """
    annotated_image = image.copy()
    output_path = Path(output_folder)

    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise OSError(f"The annotated-image output folder could not be created: {error}")

    for block in text_blocks:
        box = np.array(block["box"], dtype=np.int32)
        confidence = block["confidence"]

        colour = (0, 255, 0) if confidence >= 0.50 else (0, 165, 255)

        cv2.polylines(
            annotated_image,
            [box],
            isClosed=True,
            color=colour,
            thickness=2
        )

        label_x = int(box[0][0])
        label_y = max(int(box[0][1]) - 6, 15)

        cv2.putText(
            annotated_image,
            f"{confidence:.2f}",
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            colour,
            1,
            cv2.LINE_AA
        )

    input_file = Path(input_path)
    annotated_filename = f"{input_file.stem}_annotated.jpg"
    annotated_path = output_path / annotated_filename

    saved = cv2.imwrite(str(annotated_path), annotated_image)
    if not saved:
        raise OSError("OpenCV could not save the annotated image.")

    return str(annotated_path)


def extract_text(
    image_path,
    reader=None,
    create_annotation=True,
    annotation_folder="annotated_images"
):
    """Run PaddleOCR PP-OCRv3 and return the common OCR result shape."""
    path = Path(image_path)
    if not path.exists():
        return {
            "success": False,
            "error": "IMAGE_NOT_FOUND",
            "message": f"Image not found: {path}",
            "full_text": "",
            "text_blocks": [],
            "annotated_image_path": None
        }
    if not path.is_file() or path.suffix.lower() not in SUPPORTED_FORMATS:
        return {
            "success": False,
            "error": "UNSUPPORTED_FORMAT" if path.suffix.lower() not in SUPPORTED_FORMATS and path.is_file() else "INVALID_IMAGE_PATH",
            "message": f"The provided path is not a supported image file: {path}",
            "full_text": "",
            "text_blocks": [],
            "annotated_image_path": None
        }

    image = cv2.imread(str(path))
    if image is None:
        return {
            "success": False,
            "error": "CORRUPT_IMAGE",
            "message": "The image is corrupt or cannot be read by OpenCV.",
            "full_text": "",
            "text_blocks": [],
            "annotated_image_path": None
        }

    try:
        active_reader = reader or get_paddle_reader()
        raw_result = active_reader.ocr(image, cls=False)
        result = normalize_paddle_result(raw_result)
    except Exception as error:
        return {
            "success": False,
            "error": "OCR_EXECUTION_FAILED",
            "message": f"An error occurred during PaddleOCR execution: {error}",
            "full_text": "",
            "text_blocks": [],
            "annotated_image_path": None
        }

    annotated_image_path = None
    if create_annotation and result.get("text_blocks"):
        try:
            annotated_image_path = create_annotated_image(
                image=image,
                text_blocks=result["text_blocks"],
                input_path=path,
                output_folder=annotation_folder
            )
        except Exception:
            annotated_image_path = None

    result["annotated_image_path"] = annotated_image_path
    return result
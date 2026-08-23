import json
import sys
from pathlib import Path

import cv2
import easyocr
import numpy as np


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def error_result(error_code, message):
    """OCR errors ko consistent format mein return karta hai."""

    return {
        "success": False,
        "error": error_code,
        "message": message,
        "full_text": "",
        "text_blocks": [],
        "annotated_image_path": None
    }


def create_annotated_image(
    image,
    text_blocks,
    input_path,
    output_folder="annotated_images"
):
    """
    Detected text blocks ke around boxes draw karta hai
    aur annotated image save karta hai.
    """

    annotated_image = image.copy()
    output_path = Path(output_folder)

    try:
        output_path.mkdir(
            parents=True,
            exist_ok=True
        )
    except OSError as error:
        raise OSError(
            f"The annotated-image output folder could not be created: {error}"
        )

    for block in text_blocks:
        box = np.array(
            block["box"],
            dtype=np.int32
        )

        confidence = block["confidence"]

        # High-confidence box green, low-confidence box orange
        if confidence >= 0.50:
            colour = (0, 255, 0)
        else:
            colour = (0, 165, 255)

        cv2.polylines(
            annotated_image,
            [box],
            isClosed=True,
            color=colour,
            thickness=2
        )

        # Box ke top-left point ke paas confidence display karna
        label_x = int(box[0][0])
        label_y = max(int(box[0][1]) - 6, 15)

        confidence_label = f"{confidence:.2f}"

        cv2.putText(
            annotated_image,
            confidence_label,
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            colour,
            1,
            cv2.LINE_AA
        )

    input_file = Path(input_path)

    annotated_filename = (
        f"{input_file.stem}_annotated.jpg"
    )

    annotated_path = output_path / annotated_filename

    saved = cv2.imwrite(
        str(annotated_path),
        annotated_image
    )

    if not saved:
        raise OSError(
            "OpenCV could not save the annotated image."
        )
    

    return str(annotated_path)


def extract_text(
    image_path,
    create_annotation=True,
    annotation_folder="annotated_images"
):
    """
    Ek image se English aur Hindi text extract karta hai.
    Optional annotated image bhi generate karta hai.
    """

    path = Path(image_path)

    if not path.exists():
        return error_result(
            "IMAGE_NOT_FOUND",
            f"Image not found: {path}"
        )

    if not path.is_file():
        return error_result(
            "INVALID_IMAGE_PATH",
            f"The provided path is not an image file: {path}"
        )

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        return error_result(
            "UNSUPPORTED_FORMAT",
            f"Unsupported image format: {path.suffix}"
        )

    image = cv2.imread(str(path))

    if image is None:
        return error_result(
            "CORRUPT_IMAGE",
            "The image is corrupt or cannot be read by OpenCV."
        )

    try:
        print(
            "Loading OCR model...",
            file=sys.stderr
        )

        reader = easyocr.Reader(
            ["en", "hi"],
            gpu=False
        )

        print(
            "Extracting text from the image...",
            file=sys.stderr
        )

        results = reader.readtext(
            image,
            detail=1,
            paragraph=False
        )

    except Exception as error:
        return error_result(
            "OCR_EXECUTION_FAILED",
            f"An error occurred during OCR execution: {error}"
        )

    text_blocks = []
    text_parts = []

    for box, text, confidence in results:
        clean_text = str(text).strip()

        if not clean_text:
            continue

        normal_box = [
            [int(point[0]), int(point[1])]
            for point in box
        ]

        block = {
            "text": clean_text,
            "confidence": float(confidence),
            "box": normal_box
        }

        text_blocks.append(block)
        text_parts.append(clean_text)

    full_text = " ".join(text_parts)

    annotated_image_path = None

    if create_annotation and text_blocks:
        try:
            annotated_image_path = create_annotated_image(
                image=image,
                text_blocks=text_blocks,
                input_path=path,
                output_folder=annotation_folder
            )

        except OSError as error:
            return error_result(
                "ANNOTATED_IMAGE_SAVE_FAILED",
                str(error)
            )

        except Exception as error:
            return error_result(
                "ANNOTATION_FAILED",
                f"The annotated image could not be generated: {error}"
            )

    if not text_blocks:
        return {
            "success": True,
            "message": "OCR completed, but no text was detected.",
            "full_text": "",
            "text_blocks": [],
            "annotated_image_path": None
        }

    return {
        "success": True,
        "message": "Text and annotated image generated successfully.",
        "full_text": full_text,
        "text_blocks": text_blocks,
        "annotated_image_path": annotated_image_path
    }


def main():
    if len(sys.argv) != 2:
        result = error_result(
            "IMAGE_PATH_REQUIRED",
            'Run command: python ocr.py "input_images/product.jpg"'
        )
    else:
        result = extract_text(sys.argv[1])

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    ))


if __name__ == "__main__":
    main()
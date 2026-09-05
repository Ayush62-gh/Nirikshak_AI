import json
import sys
from pathlib import Path

import cv2


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Starting thresholds hain. Real product images test karne ke baad tune karenge.
BLURRY_THRESHOLD = 100.0
UNREADABLE_BLUR_THRESHOLD = 25.0

DARK_THRESHOLD = 60.0
VERY_DARK_THRESHOLD = 25.0

BRIGHT_THRESHOLD = 200.0
VERY_BRIGHT_THRESHOLD = 240.0


def error_result(error_code, message):
    """Quality-checking errors ko structured format mein return karta hai."""

    return {
        "success": False,
        "error": error_code,
        "message": message,
        "quality": None
    }


def calculate_image_quality(image):
    """
    Already loaded OpenCV image ka blur score,
    brightness aur quality status calculate karta hai.
    """

    # Colour image ko grayscale mein convert karna
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Laplacian variance image ke edges/sharpness measure karta hai
    blur_score = float(cv2.Laplacian(
        gray_image,
        cv2.CV_64F
    ).var())

    # Grayscale pixels ka average brightness
    brightness = float(gray_image.mean())

    is_blurry = bool(blur_score < BLURRY_THRESHOLD)

    # Bahut zyada blur/dark/bright image unreadable mani jayegi
    if (
        blur_score < UNREADABLE_BLUR_THRESHOLD
        or brightness < VERY_DARK_THRESHOLD
        or brightness > VERY_BRIGHT_THRESHOLD
    ):
        quality_status = "UNREADABLE"

    # Moderate quality problems wali image poor hogi
    elif (
        blur_score < BLURRY_THRESHOLD
        or brightness < DARK_THRESHOLD
        or brightness > BRIGHT_THRESHOLD
    ):
        quality_status = "POOR"

    else:
        quality_status = "ACCEPTABLE"

    return {
        "blur_score": round(blur_score, 2),
        "is_blurry": is_blurry,
        "brightness": round(brightness, 2),
        "quality_status": quality_status
    }


def check_image_quality(image_path):
    """Image path validate karke image-quality result return karta hai."""

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
        quality = calculate_image_quality(image)

        return {
            "success": True,
            "message": "Image quality checked successfully.",
            "quality": quality
        }

    except Exception as error:
        return error_result(
            "QUALITY_CHECK_FAILED",
            f"An error occurred while checking image quality: {error}"
        )


def main():
    if len(sys.argv) != 2:
        result = error_result(
            "IMAGE_PATH_REQUIRED",
            'Run command: python quality_checker.py "input_images/image.jpg"'
        )
    else:
        result = check_image_quality(sys.argv[1])

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
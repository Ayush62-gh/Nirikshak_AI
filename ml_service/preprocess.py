import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

MAX_IMAGE_DIMENSION = 1800
MAX_TILT_ANGLE = 10.0


def error_result(error_code, message):
    """Error ko consistent format mein return karta hai."""

    return {
        "success": False,
        "error": error_code,
        "message": message,
        "processed_image_path": None
    }


def load_with_correct_orientation(image_path):
    """
    Pillow se image load karta hai aur phone camera ki
    EXIF orientation automatically correct karta hai.
    """

    try:
        with Image.open(image_path) as pil_image:
            corrected_image = ImageOps.exif_transpose(pil_image)
            rgb_image = corrected_image.convert("RGB")

            # Pillow RGB use karta hai, OpenCV BGR use karta hai
            open_cv_image = cv2.cvtColor(
                np.array(rgb_image),
                cv2.COLOR_RGB2BGR
            )

            return open_cv_image

    except UnidentifiedImageError:
        raise ValueError("The image is corrupt or is not in a valid image format.")

    except OSError as error:
        raise ValueError(f"The image could not be opened: {error}")


def resize_large_image(image, max_dimension=MAX_IMAGE_DIMENSION):
    """
    Large image resize karta hai aur aspect ratio preserve rakhta hai.
    Small image ko change nahi karta.
    """

    height, width = image.shape[:2]
    largest_dimension = max(width, height)

    if largest_dimension <= max_dimension:
        return image, False

    scale = max_dimension / largest_dimension

    new_width = int(round(width * scale))
    new_height = int(round(height * scale))

    resized_image = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    return resized_image, True


def estimate_small_tilt(gray_image):
    """
    Image ke foreground edges se possible tilt estimate karta hai.
    Sirf chhota angle accept kiya jayega.
    """

    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)

    binary_image = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]

    coordinates = np.column_stack(
        np.where(binary_image > 0)
    )

    if len(coordinates) < 50:
        return 0.0

    angle = float(cv2.minAreaRect(coordinates)[-1])

    # OpenCV versions angle ko different ranges mein return kar sakte hain
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    # Product shape ko text tilt samajhne se bachne ke liye
    # sirf small angles allow kar rahe hain
    if abs(angle) > MAX_TILT_ANGLE:
        return 0.0

    return angle


def rotate_image(image, angle):
    """Image ko given angle se rotate karta hai."""

    if abs(angle) < 0.1:
        return image

    height, width = image.shape[:2]
    center = (width // 2, height // 2)

    rotation_matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0
    )

    rotated_image = cv2.warpAffine(
        image,
        rotation_matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return rotated_image


def enhance_readability(image):
    """
    Image ko grayscale karta hai, noise reduce karta hai
    aur CLAHE se local contrast improve karta hai.
    """

    gray_image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    denoised_image = cv2.fastNlMeansDenoising(
        gray_image,
        None,
        h=10,
        templateWindowSize=7,
        searchWindowSize=21
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced_image = clahe.apply(denoised_image)

    return enhanced_image


def preprocess_product_image(
    image_path,
    output_folder="processed_images"
):
    """Product image preprocess karke processed image save karta hai."""

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

    try:
        image = load_with_correct_orientation(path)

    except ValueError as error:
        return error_result(
            "CORRUPT_IMAGE",
            str(error)
        )

    try:
        resized_image, was_resized = resize_large_image(image)

        gray_for_tilt = cv2.cvtColor(
            resized_image,
            cv2.COLOR_BGR2GRAY
        )

        tilt_angle = estimate_small_tilt(gray_for_tilt)

        if abs(tilt_angle) < 0.01:
            tilt_angle = 0.0

        corrected_image = rotate_image(
            resized_image,
            tilt_angle
        )

        processed_image = enhance_readability(
            corrected_image
        )

    except Exception as error:
        return error_result(
            "PREPROCESSING_FAILED",
            f"An error occurred while preprocessing the image: {error}"
        )

    output_path = Path(output_folder)

    try:
        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

    except OSError as error:
        return error_result(
            "OUTPUT_FOLDER_CREATION_FAILED",
            f"The output folder could not be created: {error}"
        )

    processed_filename = f"{path.stem}_processed.jpg"
    processed_path = output_path / processed_filename

    try:
        saved = cv2.imwrite(
            str(processed_path),
            processed_image
        )

        if not saved:
            return error_result(
                "PROCESSED_IMAGE_SAVE_FAILED",
                "OpenCV could not save the processed image."
            )

    except Exception as error:
        return error_result(
            "PROCESSED_IMAGE_SAVE_FAILED",
            f"An error occurred while saving the processed image: {error}"
        )

    processed_height, processed_width = processed_image.shape[:2]

    return {
        "success": True,
        "message": "Image preprocessed successfully.",
        "processed_image_path": str(processed_path),
        "original_size": {
            "width": int(image.shape[1]),
            "height": int(image.shape[0])
        },
        "processed_size": {
            "width": int(processed_width),
            "height": int(processed_height)
        },
        "was_resized": bool(was_resized),
        "tilt_correction_angle": round(
            float(tilt_angle),
            2
        )
    }


def main():
    if len(sys.argv) != 2:
        result = error_result(
            "IMAGE_PATH_REQUIRED",
            'Run command: python preprocess.py "input_images/image.jpg"'
        )
    else:
        result = preprocess_product_image(
            sys.argv[1]
        )

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    ))


if __name__ == "__main__":
    main()
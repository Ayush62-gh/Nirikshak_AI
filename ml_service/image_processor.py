import json
import sys

from ocr import extract_text
from preprocess import preprocess_product_image
from quality_checker import check_image_quality


def create_processing_error(error_code, message, quality=None):
    """
    Processing fail hone par safe aur structured result return karta hai.

    Success result final required format mein hoga.
    Error result mein debugging ke liye success, error aur message extra hain.
    """

    return {
        "success": False,
        "error": error_code,
        "message": message,
        "quality": quality,
        "full_text": "",
        "text_blocks": [],
        "processed_image_path": None,
        "annotated_image_path": None
    }


def process_product_image(image_path):
    """
    Ek product image ka complete OCR pipeline run karta hai.

    Steps:
    1. Original image ki quality check
    2. Image preprocessing
    3. Processed image par OCR
    4. Annotated image generation
    5. Final JSON-serializable result return
    """

    # Step 1: Original image ki quality check
    quality_result = check_image_quality(image_path)

    if not quality_result.get("success"):
        return create_processing_error(
            error_code=quality_result.get(
                "error",
                "QUALITY_CHECK_FAILED"
            ),
            message=quality_result.get(
                "message",
                "Image quality check failed."
            )
        )

    quality = quality_result["quality"]

    # Step 2: Image preprocessing
    preprocessing_result = preprocess_product_image(
        image_path=image_path,
        output_folder="processed_images"
    )

    if not preprocessing_result.get("success"):
        return create_processing_error(
            error_code=preprocessing_result.get(
                "error",
                "PREPROCESSING_FAILED"
            ),
            message=preprocessing_result.get(
                "message",
                "Image preprocessing failed."
            ),
            quality=quality
        )

    processed_image_path = preprocessing_result[
        "processed_image_path"
    ]

    # Step 3: Processed image par OCR aur annotation
    ocr_result = extract_text(
        image_path=processed_image_path,
        create_annotation=True,
        annotation_folder="annotated_images"
    )

    if not ocr_result.get("success"):
        return create_processing_error(
            error_code=ocr_result.get(
                "error",
                "OCR_EXECUTION_FAILED"
            ),
            message=ocr_result.get(
                "message",
                "OCR execution failed."
            ),
            quality=quality
        )

    # Successful final integration format
    return {
        "quality": {
            "blur_score": float(
                quality["blur_score"]
            ),
            "is_blurry": bool(
                quality["is_blurry"]
            ),
            "brightness": float(
                quality["brightness"]
            ),
            "quality_status": str(
                quality["quality_status"]
            )
        },
        "full_text": str(
            ocr_result["full_text"]
        ),
        "text_blocks": ocr_result[
            "text_blocks"
        ],
        "processed_image_path": str(
            processed_image_path
        ),
        "annotated_image_path": (
            str(ocr_result["annotated_image_path"])
            if ocr_result["annotated_image_path"] is not None
            else None
        )
    }

def process_product_images(image_paths):
    """
    Same product ki multiple images process karta hai.

    Example:
    Front image, back image and side image.
    """

    if not isinstance(image_paths, (list, tuple)):
        return {
            "success": False,
            "error": "INVALID_IMAGE_LIST",
            "message": "Image paths must be provided as a list or tuple.",
            "total_images": 0,
            "successful_images": 0,
            "failed_images": 0,
            "combined_full_text": "",
            "results": []
        }

    if len(image_paths) == 0:
        return {
            "success": False,
            "error": "NO_IMAGES_PROVIDED",
            "message": "No images were provided for processing.",
            "total_images": 0,
            "successful_images": 0,
            "failed_images": 0,
            "combined_full_text": "",
            "results": []
        }

    results = []
    combined_text_parts = []

    successful_images = 0
    failed_images = 0

    for image_path in image_paths:
        image_result = process_product_image(
            image_path
        )

        # Input path bhi result ke saath preserve kar rahe hain
        result_with_path = {
            "input_image_path": str(image_path),
            **image_result
        }

        results.append(result_with_path)

        if image_result.get("success") is False:
            failed_images += 1
        else:
            successful_images += 1

            full_text = image_result.get(
                "full_text",
                ""
            ).strip()

            if full_text:
                combined_text_parts.append(full_text)

    combined_full_text = " ".join(
        combined_text_parts
    )

    return {
        "total_images": int(len(image_paths)),
        "successful_images": int(successful_images),
        "failed_images": int(failed_images),
        "combined_full_text": combined_full_text,
        "results": results
    }

def main():
    """
    Terminal se single ya multiple images test karta hai.
    """

    if len(sys.argv) < 2:
        result = create_processing_error(
            error_code="IMAGE_PATH_REQUIRED",
            message="At least one image path is required."
        )

    elif len(sys.argv) == 2:
        result = process_product_image(
            sys.argv[1]
        )

    else:
        result = process_product_images(
            sys.argv[1:]
        )

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    ))


if __name__ == "__main__":
    main()
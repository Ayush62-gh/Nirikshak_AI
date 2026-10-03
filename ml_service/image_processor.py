import json
import os
import sys

import paddle_ocr
from field_extractor import extract_fields
from preprocess import preprocess_product_image
from quality_checker import check_image_quality


def create_processing_error(error_code, message, quality=None):
    """
    Processing fail hone par safe aur structured result return karta hai.
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


def _calculate_mean_confidence(text_blocks):
    if not text_blocks:
        return 0.0
    confidences = [b.get("confidence", 0.0) for b in text_blocks if isinstance(b, dict)]
    return sum(confidences) / len(confidences) if confidences else 0.0


def process_product_image(image_path):
    """
    Ek product image ka complete OCR pipeline run karta hai.

    Steps:
    1. Original image ki quality check
    2. Quality-based image selection:
       - POOR: Always run preprocess.py first
       - GOOD/ACCEPTABLE: Run on RAW image first
    3. Fallback Retry:
       - If GOOD/ACCEPTABLE raw pass misses essential fields (MRP, Net Quantity, Mfg Name),
         automatically retry with preprocess.py and merge missing fields.
    4. Annotated image generation & return format
    """

    # Step 1: Original image ki quality check
    quality_result = check_image_quality(image_path)

    if not quality_result.get("success"):
        return create_processing_error(
            error_code=quality_result.get("error", "QUALITY_CHECK_FAILED"),
            message=quality_result.get("message", "Image quality check failed.")
        )

    quality = quality_result["quality"]
    quality_status = quality.get("quality_status", "ACCEPTABLE").upper()

    # Determine primary input image path
    is_poor_quality = (quality_status == "POOR")
    processed_image_path = None

    if is_poor_quality:
        preprocessing_result = preprocess_product_image(
            image_path=image_path,
            output_folder="processed_images"
        )
        if not preprocessing_result.get("success"):
            return create_processing_error(
                error_code=preprocessing_result.get("error", "PREPROCESSING_FAILED"),
                message=preprocessing_result.get("message", "Image preprocessing failed."),
                quality=quality
            )
        processed_image_path = preprocessing_result["processed_image_path"]
        target_image_path = processed_image_path
    else:
        target_image_path = image_path

    # Step 3: Primary OCR execution
    ocr_result = paddle_ocr.extract_text(
        image_path=target_image_path,
        create_annotation=True,
        annotation_folder="annotated_images"
    )

    if not ocr_result.get("success"):
        return create_processing_error(
            error_code=ocr_result.get("error", "OCR_EXECUTION_FAILED"),
            message=ocr_result.get("message", "OCR execution failed."),
            quality=quality
        )

    retried_preprocessed = False

    # Step 4: Fallback Retry Safety Net for ACCEPTABLE / GOOD quality images
    if not is_poor_quality:
        extracted_fields = extract_fields(ocr_result)
        key_missing = (
            extracted_fields.get("mrp") is None
            or extracted_fields.get("netQuantity") is None
            or extracted_fields.get("manufacturerName") is None
        )

        if key_missing:
            # Trigger preprocessed retry to recover missing fine-print fields
            preprocessing_result = preprocess_product_image(
                image_path=image_path,
                output_folder="processed_images"
            )
            if preprocessing_result.get("success"):
                processed_image_path = preprocessing_result["processed_image_path"]
                secondary_ocr = paddle_ocr.extract_text(
                    image_path=processed_image_path,
                    create_annotation=False
                )

                if secondary_ocr.get("success"):
                    secondary_fields = extract_fields(secondary_ocr)
                    # Recover missing key fields from preprocessed pass
                    for key_field in ("mrp", "netQuantity", "manufacturerName", "monthOfPacking", "yearOfPacking", "consumerCare"):
                        if extracted_fields.get(key_field) is None and secondary_fields.get(key_field) is not None:
                            extracted_fields[key_field] = secondary_fields[key_field]

                    # Combine additional text blocks if secondary pass found extra text
                    existing_text = ocr_result.get("full_text", "")
                    sec_text = secondary_ocr.get("full_text", "")
                    if sec_text and len(sec_text) > len(existing_text):
                        ocr_result["full_text"] = sec_text
                        ocr_result["text_blocks"] = secondary_ocr.get("text_blocks", ocr_result.get("text_blocks", []))

                    retried_preprocessed = True

    if processed_image_path is None:
        # Generate preprocessed image for audit file trace
        preprocessing_result = preprocess_product_image(
            image_path=image_path,
            output_folder="processed_images"
        )
        if preprocessing_result.get("success"):
            processed_image_path = preprocessing_result["processed_image_path"]

    return {
        "quality": {
            "blur_score": float(quality["blur_score"]),
            "is_blurry": bool(quality["is_blurry"]),
            "brightness": float(quality["brightness"]),
            "quality_status": str(quality["quality_status"])
        },
        "full_text": str(ocr_result["full_text"]),
        "text_blocks": ocr_result["text_blocks"],
        "processed_image_path": str(processed_image_path) if processed_image_path else str(image_path),
        "annotated_image_path": (
            str(ocr_result["annotated_image_path"])
            if ocr_result.get("annotated_image_path") is not None
            else None
        ),
        "retried_preprocessed": retried_preprocessed
    }


def process_product_images(image_paths):
    """
    Processes multiple images of the same product (e.g. Front, Back, Side)
    and merges extracted Metrology fields with consensus & conflict resolution.
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
            "fields": {},
            "extraction_conflicts": {},
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
            "fields": {},
            "extraction_conflicts": {},
            "results": []
        }

    results = []
    combined_text_parts = []

    successful_images = 0
    failed_images = 0

    per_image_extractions = []

    for idx, image_path in enumerate(image_paths):
        image_result = process_product_image(
            image_path
        )

        result_with_path = {
            "input_image_path": str(image_path),
            **image_result
        }
        results.append(result_with_path)

        if image_result.get("success") is False:
            failed_images += 1
        else:
            successful_images += 1
            full_text = image_result.get("full_text", "").strip()
            if full_text:
                combined_text_parts.append(full_text)

            # Perform structured field extraction on single image result
            fields = extract_fields(image_result)
            text_blocks = image_result.get("text_blocks", [])
            mean_conf = _calculate_mean_confidence(text_blocks)

            per_image_extractions.append({
                "source_index": idx,
                "source_path": str(image_path),
                "source_filename": os.path.basename(str(image_path)),
                "fields": fields,
                "mean_ocr_confidence": mean_conf
            })

    combined_full_text = " ".join(combined_text_parts)

    # Multi-Angle Field Evidence Merging Engine
    ALL_FIELD_KEYS = [
        "productId", "productName", "productType", "isImported",
        "manufacturerName", "manufacturerAddress", "packerName", "importerName",
        "netQuantity", "mrp", "monthOfPacking", "yearOfPacking",
        "consumerCare", "countryOfOrigin"
    ]

    merged_fields = {}
    extraction_conflicts = {}

    for field_key in ALL_FIELD_KEYS:
        candidates = []
        for ext in per_image_extractions:
            val = ext["fields"].get(field_key)
            if val is not None and str(val).strip() != "":
                candidates.append({
                    "value": val,
                    "source_filename": ext["source_filename"],
                    "source_path": ext["source_path"],
                    "ocr_confidence": round(ext["mean_ocr_confidence"], 3)
                })

        if not candidates:
            merged_fields[field_key] = None
            continue

        if len(candidates) == 1:
            merged_fields[field_key] = candidates[0]["value"]
            continue

        # Check for consensus (all non-None candidate values match when normalized)
        norm_values = set(str(c["value"]).strip().lower() for c in candidates)
        if len(norm_values) == 1:
            merged_fields[field_key] = candidates[0]["value"]
            continue

        # DISAGREEMENT / CONFLICT DETECTED across images!
        # Tie-breaker rule: Select candidate with highest mean OCR confidence score
        sorted_candidates = sorted(candidates, key=lambda c: c["ocr_confidence"], reverse=True)
        winning_candidate = sorted_candidates[0]

        merged_fields[field_key] = winning_candidate["value"]
        extraction_conflicts[field_key] = {
            "resolved_value": winning_candidate["value"],
            "competing_values": [
                {
                    "value": c["value"],
                    "source_image": c["source_filename"],
                    "ocr_confidence": c["ocr_confidence"]
                }
                for c in candidates
            ],
            "resolution_reason": (
                f"Selected value '{winning_candidate['value']}' from image '{winning_candidate['source_filename']}' "
                f"due to higher OCR confidence ({winning_candidate['ocr_confidence']:.3f} vs "
                f"{sorted_candidates[1]['ocr_confidence']:.3f})."
            )
        }

    # Set overall extraction_confidence grade
    if extraction_conflicts:
        merged_fields["extraction_confidence"] = "MEDIUM"
    elif any(merged_fields.values()):
        merged_fields["extraction_confidence"] = "HIGH"
    else:
        merged_fields["extraction_confidence"] = "LOW"

    return {
        "success": True,
        "total_images": int(len(image_paths)),
        "successful_images": int(successful_images),
        "failed_images": int(failed_images),
        "combined_full_text": combined_full_text,
        "fields": merged_fields,
        "extraction_conflicts": extraction_conflicts,
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
        result = process_product_image(sys.argv[1])
    else:
        result = process_product_images(sys.argv[1:])

    print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
import json
import os
import re
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


def _find_field_ocr_confidence(value, text_blocks, default_conf):
    """Finds the OCR confidence of the text block best matching the candidate value."""
    if not value or not text_blocks:
        return default_conf
    val_str = str(value).strip().lower()
    matching_confs = []
    for b in text_blocks:
        if not isinstance(b, dict):
            continue
        b_text = str(b.get("text", "")).strip().lower()
        if not b_text:
            continue
        if val_str in b_text or b_text in val_str:
            matching_confs.append(float(b.get("confidence", default_conf)))
        else:
            tokens = [t for t in re.split(r'[\s:,\-/]+', val_str) if len(t) >= 3]
            if tokens and any(t in b_text for t in tokens):
                matching_confs.append(float(b.get("confidence", default_conf)))
    if matching_confs:
        return max(matching_confs)
    return default_conf


def _score_candidate_evidence(field_key, value, text_blocks, full_text):
    """
    Evaluates field-specific extraction evidence and contextual label strength.
    Returns an integer evidence weight:
      3: Strong statutory evidence (explicit statutory label + valid field format)
      2: Moderate evidence (valid field structure / unit / format, partial contextual label)
      1: Weak evidence (unanchored, fallback, bare number or single word)
      0: Invalid (fails basic validity check for this field)
    """
    if value is None or str(value).strip() == "":
        return 0
    val_str = str(value).strip()
    val_lower = val_str.lower()
    full_lower = (full_text or "").lower()

    if field_key == "mrp":
        # Must look like a price, never a pure net-quantity unit
        if re.search(r'(?i)\b\d+\s*(?:ml|g|kg|l|gm)\b', val_str) and not re.search(r'(?i)\b(?:rs|inr|₹|mrp|/-)\b', val_str):
            return 0
        has_price_num = bool(re.search(r'\d+(?:\.\d+)?', val_str))
        if not has_price_num:
            return 0
        has_mrp_label = bool(
            re.search(r'(?i)\b(?:mrp|maximum\s*retail\s*price|incl|taxes)\b', val_str)
            or re.search(r'(?i)\b(?:mrp|maximum\s*retail\s*price)\b', full_lower)
        )
        has_curr = bool(re.search(r'(?i)(?:rs\.?|inr|₹|/-)', val_str))
        if has_mrp_label and (has_curr or re.search(r'(?i)incl.*tax', val_str)):
            return 3
        if has_mrp_label or has_curr:
            return 2
        return 1

    elif field_key == "netQuantity":
        has_unit = bool(re.search(r'(?i)\b(?:ml|l|g|kg|gm|gms|n|u|piece|count)\b', val_str))
        has_qty_label = bool(re.search(r'(?i)\b(?:net\s*qty|net\s*wt|net\s*quantity|net\s*content|net\s*vol)\b', full_lower))
        if has_unit and has_qty_label:
            return 3
        if has_unit:
            return 2
        return 1

    elif field_key in ("manufacturerName", "packerName"):
        has_mfg_label = bool(re.search(r'(?i)\b(?:manufactured\s*by|mfg\.?\s*by|mfd\.?\s*by|produced\s*by|packed\s*by|manufacturer:)\b', full_lower))
        has_corp_suffix = bool(re.search(r'(?i)\b(?:pvt\.?\s*ltd|ltd\.?|limited|private\s*limited|llp|inc\.?)\b', val_str))
        if has_mfg_label and has_corp_suffix:
            return 3
        if has_mfg_label or has_corp_suffix:
            return 2
        words = re.findall(r'[A-Za-z]{2,}', val_str)
        if len(words) >= 2:
            return 2
        return 1

    elif field_key == "importerName":
        has_imp_label = bool(re.search(r'(?i)\b(?:imported\s*by|importer\s*name|imp\.?\s*by|import\s*&\s*marketed)\b', full_lower))
        has_corp_suffix = bool(re.search(r'(?i)\b(?:pvt\.?\s*ltd|ltd\.?|limited|private\s*limited|llp|inc\.?)\b', val_str))
        if has_imp_label and has_corp_suffix:
            return 3
        if has_imp_label:
            return 2
        return 1

    elif field_key == "unitSalePrice":
        has_usp_label = bool(
            re.search(r'(?i)\b(?:unit\s*sale\s*price|unit\s*price|sale\s*price\s*per|rs\.?/\s*(?:kg|g|ml|100g|100ml))\b', val_str)
            or re.search(r'(?i)\b(?:unit\s*sale\s*price|unit\s*price)\b', full_lower)
        )
        if has_usp_label and re.search(r'\d+', val_str):
            return 3
        if re.search(r'(?i)(?:rs\.?|₹).*/\s*(?:kg|g|ml|100g|100ml|unit)', val_str):
            return 2
        return 1

    elif field_key in ("monthOfPacking", "yearOfPacking"):
        has_date_label = bool(re.search(r'(?i)\b(?:mfd|mfg|pkd|packed|manufacturing)\b', full_lower))
        if has_date_label:
            return 3
        return 2

    elif field_key in ("expiryMonth", "expiryYear"):
        has_exp_label = bool(re.search(r'(?i)\b(?:exp|expiry|use\s*before|best\s*before|bbe)\b', full_lower))
        if has_exp_label:
            return 3
        return 2

    elif field_key == "consumerCare":
        if "@" in val_str or re.search(r'\b1800\d{6,7}\b', val_str):
            return 3
        if re.search(r'(?i)\b(?:care|helpline|consumer|customer|toll[\s-]free)\b', full_lower):
            return 2
        return 1

    elif field_key == "countryOfOrigin":
        has_origin_label = bool(re.search(r'(?i)\b(?:country\s*of\s*origin|made\s*in|manufactured\s*in)\b', full_lower))
        if has_origin_label:
            return 3
        return 2

    elif field_key == "batchNumber":
        has_batch_label = bool(
            re.search(
                r'(?i)\b(?:for\s+batch(?:\s+no\.?|\s+number)?|batch(?:\s*/\s*lot)?(?:\s+no\.?|\s+number)?|lot(?:\s*/\s*batch)?(?:\s+no\.?|\s+number)?|b\.?\s*no)\b',
                full_lower
            )
        )
        has_alphanumeric = bool(re.search(r'[A-Za-z0-9]', val_str))
        if not has_alphanumeric or len(val_str) < 2:
            return 0
        if has_batch_label and len(val_str) >= 3:
            return 3
        if has_batch_label:
            return 2
        return 1

    elif field_key == "productName":
        # Price/batch/code/date text = invalid (0)
        if re.search(
            r'(?i)(?:'
            r'\d+(?:[.,]\d+)?\s*/?[-]?\s*\d*(?:\.\d+)?\s*/\s*(?:ml|g|kg|l|gm|unit)'
            r'|\d+\s*/[-]'
            r'|rs\.?\s*\d+'
            r'|\d+\s*/-'
            r'|[A-Z]{1,4}\d{3,}'
            r'|\d{3,}[A-Z]{1,4}'
            r'|\d+\.\d+\s*/\s*[a-zA-Z]+'
            r'|@\s*\d+[/-]\d+'
            r')',
            val_str
        ):
            return 0

        # Dangling prepositions or conjunctions = invalid (0)
        if re.search(r'(?i)\b(?:for|withs?|ofs?|in|to|by|from|on|at|and|or|&)\s*(?:a|an|the)?\s*$', val_str):
            return 0
        if re.search(r'(?i)^(?:and|or|&|with|of|in|for|by|from|to)\s+', val_str):
            return 0

        # Instructional step / usage phrases = invalid (0)
        if re.search(
            r'(?i)(?:'
            r'\b(?:\d+\s+)?steps?\s+(?:for|to|towards|in|of|ahead)\b'
            r'|\b(?:follow|these|easy|simple)\s+(?:these\s+)?steps?\b'
            r'|\bstep\s*[:.-]?\s*\d+\b'
            r'|\bhow\s+to\s+(?:use|apply|wash|cleanse)\b'
            r'|\broutine\s+steps?\b'
            r'|\b(?:directions?|how\s+to|storage|warning|caution|tamper|external\s+use|flush|avoid|occurs?|safety|first\s+aid|formula\s+with|contains?|may\s+contain|trademark|compatibility|dermatolog[a-z]*|clinical[a-z]*|tested|made\s+(?:with|from|of)|(?:bottle|pack|container|tube|packaging)\s+made|recycled|excluding|over\s+time|appearance|the\s+product)\b'
            r')',
            val_str
        ):
            return 0

        # Product claims, formula/skin/body attributes, benefits, and compatibility = invalid (0)
        if re.search(
            r'(?i)(?:'
            r'\bph\s*(?:skin|neutral|balanced?|level|\d+(?:\.\d+)?)\b'
            r'|\b(?:skin|body|scalp)\s*ph\b'
            r'|\b(?:paraben|soap|sulphate|sulfate|silicone|dye|microplastic|alcohol)[-\s]*free\b'
            r'|\b(?:microplastic|protecting|nourishing|cleansing)[-\s]*formula\b'
            r'|\bformula\s+with\b'
            r'|\b(?:skin|hair|scalp)\s+compatibility\b'
            r'|\bcompatibility\s+(?:tested|approved|dermatologically)\b'
            r'|\b(?:dermatolog[a-z]*|clinical[a-z]*|paediatric[a-z]*|pediatric[a-z]*|ophthalmolog[a-z]*)\s+(?:tested|proven|approved|certified)\b'
            r'|\bhypoallergenic\b'
            r'|\b(?:gentle|mild|soft|safe)\s+on\s+(?:the\s+)?(?:skin|hair|scalp|hands|body)\b'
            r'|\b(?:protects?|nourish(?:es)?|sooth(?:es)?|hydrates?|moisturiz(?:es)?|moisturis(?:es)?)\s+(?:your\s+|the\s+)?(?:skin|hair|scalp)\b'
            r'|\b(?:moisturiz(?:ed)?|moisturis(?:ed)?|hydrated)\s+skin\b'
            r'|\b(?:healthy|glowing|radiant|dry|oily|sensitive)\s+skin\s*$'
            r'|\b(?:suitable|ideal|formulated|crafted)\s+for\s+(?:all\s+)?(?:skin|hair|types?)\b'
            r'|\b(?:all|every)\s+(?:skin|hair)\s+types?\b'
            r'|\b(?:long|all-?day)\s+lasting\s+(?:freshness|fragrance|hydration|moisture|protection)\b'
            r'|\b(?:germ|bacterial|odour|odor)\s+protection\b'
            r')',
            val_str
        ):
            return 0

        # Reject URL, email, domain, or trademark strings
        if re.search(r'(?i)@|https?://|www\.|\.[a-z]{2,}\b', val_str):
            return 0

        # Reject customer care, complaint, query, feedback, and cross-reference text
        if re.search(r'(?i)(?:feedback|complaints?|queries|query|careline|toll\s*free|(?:see|refer|read)\s*(?:above|below|side|bottom|pkg|pack|panel))', val_str):
            return 0

        # Non-alpha dominated strings or sentences with punctuation = invalid (0)
        if len(val_str) < 3 or '?' in val_str or '!' in val_str or val_str.endswith('.'):
            return 0
        alpha_ratio = sum(1 for ch in val_str if ch.isalpha()) / max(len(val_str), 1)
        if alpha_ratio < 0.40:
            return 0

        # Instructional / promotional text = weak (1)
        if re.search(r'(?i)\b(?:special|makes|delight|squeeze|rinse|massage|apply|lather|gently|feel|refreshing|experience|boost|enjoy|goodness|enriched)\b', val_str):
            return 1

        # Explicit product-name labels = strong evidence (3)
        has_explicit_label = bool(
            re.search(r'(?i)\b(?:product\s+name|generic\s+name|commodity\s+name|common\s+name)\b', full_lower)
        )
        words = re.findall(r'[A-Za-z]{2,}', val_str)
        if has_explicit_label and len(words) >= 1:
            return 3

        # Plausible descriptive product text = moderate evidence (2)
        if len(words) >= 2:
            return 2
        if len(words) == 1:
            return 1
        return 0

    return 2


def process_product_image(image_path, calibration_px_per_mm=None):
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
        extracted_fields = extract_fields(ocr_result, calibration_px_per_mm=calibration_px_per_mm)
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
                    secondary_fields = extract_fields(secondary_ocr, calibration_px_per_mm=calibration_px_per_mm)
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


def process_product_images(image_paths, calibration_px_per_mm=None):
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
            image_path,
            calibration_px_per_mm=calibration_px_per_mm
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
            fields = extract_fields(image_result, calibration_px_per_mm=calibration_px_per_mm)
            text_blocks = image_result.get("text_blocks", [])
            mean_conf = _calculate_mean_confidence(text_blocks)

            per_image_extractions.append({
                "source_index": idx,
                "source_path": str(image_path),
                "source_filename": os.path.basename(str(image_path)),
                "fields": fields,
                "mean_ocr_confidence": mean_conf,
                "text_blocks": text_blocks,
                "full_text": full_text
            })

    combined_full_text = " ".join(combined_text_parts)

    # Multi-Angle Field Evidence Merging Engine
    ALL_FIELD_KEYS = [
        "productId", "productName", "productType", "isImported",
        "manufacturerName", "manufacturerAddress", "packerName", "importerName",  # Rule 9
        "netQuantity", "mrp", "unitSalePrice",                                    # Rule 11
        "monthOfPacking", "yearOfPacking",
        "expiryMonth", "expiryYear",                                              # Rule 10
        "consumerCare", "countryOfOrigin",
        "fontHeightMm",                                                           # Rule 12
        "batchNumber",
    ]

    merged_fields = {}
    extraction_conflicts = {}

    for field_key in ALL_FIELD_KEYS:
        candidates = []
        for ext in per_image_extractions:
            val = ext["fields"].get(field_key)
            if val is not None and str(val).strip() != "":
                text_blocks = ext.get("text_blocks", [])
                full_text = ext.get("full_text", "")
                mean_conf = ext["mean_ocr_confidence"]
                field_ocr_conf = _find_field_ocr_confidence(val, text_blocks, mean_conf)
                evidence_strength = _score_candidate_evidence(field_key, val, text_blocks, full_text)
                candidates.append({
                    "value": val,
                    "source_filename": ext["source_filename"],
                    "source_path": ext["source_path"],
                    "ocr_confidence": round(field_ocr_conf, 3),
                    "mean_ocr_confidence": round(mean_conf, 3),
                    "evidence_strength": evidence_strength
                })

        if not candidates:
            merged_fields[field_key] = None
            continue

        if len(candidates) == 1:
            if candidates[0]["evidence_strength"] == 0:
                merged_fields[field_key] = None
            else:
                merged_fields[field_key] = candidates[0]["value"]
            continue

        # Check for consensus (all non-None candidate values match when normalized)
        norm_values = set(str(c["value"]).strip().lower() for c in candidates)
        if len(norm_values) == 1:
            if candidates[0]["evidence_strength"] == 0:
                merged_fields[field_key] = None
            else:
                merged_fields[field_key] = candidates[0]["value"]
            continue

        # DISAGREEMENT / CONFLICT DETECTED across images!
        # Field-aware resolution priority:
        #   1. evidence_strength (contextual label evidence & field-specific validity)
        #   2. ocr_confidence (field-specific text block confidence)
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c["evidence_strength"], c["ocr_confidence"]),
            reverse=True
        )
        winning_candidate = sorted_candidates[0]
        runner_up = sorted_candidates[1]

        # Safety check: Can the conflict safely be resolved?
        # - Top candidate is invalid (evidence_strength == 0)
        # - Both top candidates are weak unsupported fallbacks without statutory labels (evidence_strength <= 1)
        # - Dead tie between contradictory candidates with identical evidence and OCR confidence
        cannot_safely_resolve = (
            winning_candidate["evidence_strength"] == 0
            or (winning_candidate["evidence_strength"] <= 1 and runner_up["evidence_strength"] <= 1)
            or (winning_candidate["evidence_strength"] == runner_up["evidence_strength"]
                and abs(winning_candidate["ocr_confidence"] - runner_up["ocr_confidence"]) < 0.001
                and str(winning_candidate["value"]).strip().lower() != str(runner_up["value"]).strip().lower())
        )

        if cannot_safely_resolve:
            merged_fields[field_key] = None
            extraction_conflicts[field_key] = {
                "resolved_value": None,
                "competing_values": [
                    {
                        "value": c["value"],
                        "source_image": c["source_filename"],
                        "ocr_confidence": c["ocr_confidence"]
                    }
                    for c in candidates
                ],
                "resolution_reason": (
                    "Candidates could not be safely resolved due to insufficient contextual "
                    "evidence or tied OCR confidence; resolved to null for verification."
                )
            }
            continue

        merged_fields[field_key] = winning_candidate["value"]
        if winning_candidate["evidence_strength"] == runner_up["evidence_strength"]:
            reason = (
                f"Selected value '{winning_candidate['value']}' from image '{winning_candidate['source_filename']}' "
                f"due to higher OCR confidence ({winning_candidate['ocr_confidence']:.3f} vs "
                f"{runner_up['ocr_confidence']:.3f})."
            )
        else:
            reason = (
                f"Selected value '{winning_candidate['value']}' from image '{winning_candidate['source_filename']}' "
                f"due to stronger statutory evidence (strength={winning_candidate['evidence_strength']} vs "
                f"{runner_up['evidence_strength']}, ocr_confidence={winning_candidate['ocr_confidence']:.3f} vs "
                f"{runner_up['ocr_confidence']:.3f})."
            )

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
            "resolution_reason": reason
        }

    # Set overall extraction_confidence grade for the merged result.
    # HIGH requires: no unresolved conflicts AND at least 2 core statutory fields extracted.
    # Simply having any extracted field is insufficient for HIGH confidence.
    _core_statutory = {"mrp", "netQuantity", "manufacturerName", "monthOfPacking", "yearOfPacking"}
    _extracted_core = sum(1 for k in _core_statutory if merged_fields.get(k) is not None)
    has_unresolved_conflicts = any(
        c.get("resolved_value") is None for c in extraction_conflicts.values()
    )

    if has_unresolved_conflicts:
        merged_fields["extraction_confidence"] = "LOW"
    elif extraction_conflicts:
        merged_fields["extraction_confidence"] = "MEDIUM"
    elif _extracted_core >= 2:
        merged_fields["extraction_confidence"] = "HIGH"
    elif _extracted_core >= 1 or any(merged_fields.get(k) for k in ALL_FIELD_KEYS if k not in _core_statutory):
        merged_fields["extraction_confidence"] = "MEDIUM"
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
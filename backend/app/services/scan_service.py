from app.services import ocr_client, rule_client
from app.db.session import save_scan, get_scan
from app.schemas.scan_schemas import ScanResponse
from app.core.errors import ExternalServiceError, ExternalServiceRateLimitError


def _build_and_save_scan_record(
    extracted_fields: dict,
    compliance_result: dict,
    filename: str,
    user_id: str,
) -> ScanResponse:
    image_ref = f"uploads/{filename}" if filename else "uploads/scanned_image.jpg"
    flat_scan_data = {
        "user_id": user_id,
        "product_name": extracted_fields.get("product_name"),
        "manufacturer": extracted_fields.get("manufacturer"),
        "net_quantity": extracted_fields.get("net_quantity"),
        "mrp": extracted_fields.get("mrp"),
        "batch_number": extracted_fields.get("batch_number"),
        "mfg_date": extracted_fields.get("mfg_date"),
        "consumer_care": extracted_fields.get("consumer_care"),
        "extracted_fields": extracted_fields,
        "compliance_status": compliance_result.get("status", "PARTIAL"),
        "violations": compliance_result.get("violations", []),
        "image_ref": image_ref,
    }

    # Save scan to database
    scan_id = save_scan(flat_scan_data, user_id=user_id)

    # Get saved row from database
    row = get_scan(scan_id, user_id=user_id)
    if not row:
        raise RuntimeError("Failed to retrieve scan after saving to database.")

    # Convert flat DB dict into nested API response schema
    return ScanResponse.from_db_row(row)


async def process_scan(image_bytes: bytes, filename: str, user_id: str) -> ScanResponse:
    """
    Orchestrates the label scan pipeline:
    1. Extract fields via OCR client
    2. Validate compliance via Rule Engine client
    3. Construct flat record for database persistence
    4. Save record to DB and retrieve updated row
    5. Convert DB row to ScanResponse Pydantic schema
    """
    try:
        # 1. OCR Extraction
        extracted_fields = await ocr_client.extract_fields(image_bytes, filename)

        # 2. Rule Engine Compliance Validation
        compliance_result = await rule_client.validate_compliance(extracted_fields)
    except (ExternalServiceError, ExternalServiceRateLimitError):
        raise
    except Exception as exc:
        raise ExternalServiceError(f"External service processing failed: {str(exc)}") from exc

    # 3-6. Save and build ScanResponse
    return _build_and_save_scan_record(extracted_fields, compliance_result, filename, user_id)


async def process_scan_multi(images: list[tuple[str, bytes]], user_id: str) -> ScanResponse:
    """
    Orchestrates the multi-image label scan pipeline:
    1. Extract merged fields via OCR client multi-image endpoint
    2. Validate compliance via Rule Engine client
    3. Construct flat record for database persistence (image_ref = first filename)
    4. Save record to DB and retrieve updated row
    5. Convert DB row to ScanResponse Pydantic schema
    """
    try:
        # 1. OCR Multi-image Extraction
        extracted_fields = await ocr_client.extract_fields_multi(images)

        # 2. Rule Engine Compliance Validation
        compliance_result = await rule_client.validate_compliance(extracted_fields)
    except (ExternalServiceError, ExternalServiceRateLimitError):
        raise
    except Exception as exc:
        raise ExternalServiceError(f"External service processing failed: {str(exc)}") from exc

    # 3-6. Save and build ScanResponse (image_ref = first filename)
    first_filename = images[0][0] if images else "scan.jpg"
    return _build_and_save_scan_record(extracted_fields, compliance_result, first_filename, user_id)

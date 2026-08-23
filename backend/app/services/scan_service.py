from app.services import ocr_client, rule_client
from app.db.session import save_scan, get_scan
from app.schemas.scan_schemas import ScanResponse


async def process_scan(image_bytes: bytes, filename: str) -> ScanResponse:
    """
    Orchestrates the label scan pipeline:
    1. Extract fields via OCR client
    2. Validate compliance via Rule Engine client
    3. Construct flat record for database persistence
    4. Save record to DB and retrieve updated row
    5. Convert DB row to ScanResponse Pydantic schema
    """
    # 1. OCR Extraction
    extracted_fields = await ocr_client.extract_fields(image_bytes, filename)

    # 2. Rule Engine Compliance Validation
    compliance_result = await rule_client.validate_compliance(extracted_fields)

    # 3. Build flat dictionary structure for database layer
    image_ref = f"uploads/{filename}" if filename else "uploads/scanned_image.jpg"
    flat_scan_data = {
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

    # 4. Save scan to database
    scan_id = save_scan(flat_scan_data)

    # 5. Get saved row from database
    row = get_scan(scan_id)
    if not row:
        raise RuntimeError("Failed to retrieve scan after saving to database.")

    # 6. Convert flat DB dict into nested API response schema
    return ScanResponse.from_db_row(row)

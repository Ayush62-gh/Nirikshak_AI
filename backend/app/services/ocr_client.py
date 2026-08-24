import asyncio
import logging
import httpx
from app.core.config import settings
from app.core.errors import ExternalServiceError

logger = logging.getLogger(__name__)


def _parse_ocr_response(response: dict) -> dict:
    fields = response.get("fields") or {}
    quality = response.get("quality") or {}

    month = fields.get("monthOfPacking")
    year = fields.get("yearOfPacking")

    if month and year:
        mfg_date = f"{month}/{year}"
    else:
        mfg_date = None

    quality_status = quality.get("quality_status") or fields.get("quality_status")
    extraction_confidence = fields.get("extraction_confidence")

    return {
        "product_name": fields.get("productName"),
        "manufacturer": fields.get("manufacturerName"),
        "net_quantity": fields.get("netQuantity"),
        "mrp": fields.get("mrp"),
        "batch_number": None,
        "mfg_date": mfg_date,
        "consumer_care": fields.get("consumerCare"),
        "raw_ocr_text": response.get("full_text"),
        "manufacturer_address": fields.get("manufacturerAddress"),
        "quality_status": quality_status,
        "extraction_confidence": extraction_confidence,
    }


async def extract_fields(image_bytes: bytes, filename: str) -> dict:
    """
    Extracts text and key Legal Metrology fields from package label image.
    When settings.use_mock_ocr is True, returns simulated mock data.
    When settings.use_mock_ocr is False, POSTs image to OCR service at /extract.
    """
    if settings.use_mock_ocr:
        # Simulate network latency of OCR service call
        await asyncio.sleep(0.1)

        return {
            "product_name": "Sample Biscuits 200g",
            "manufacturer": "ABC Foods Pvt Ltd",
            "net_quantity": "200 g",
            "mrp": "Rs. 45",
            "batch_number": "B12345",
            "mfg_date": "01/2026",
            "consumer_care": "1800-XXX-XXXX",
            "raw_ocr_text": "Sample Biscuits 200g ABC Foods Pvt Ltd Net Wt 200 g MRP Rs. 45 B12345 01/2026 Consumer Care: 1800-XXX-XXXX",
        }

    # REAL SERVICE INTEGRATION
    ocr_url = f"{settings.OCR_SERVICE_URL.rstrip('/')}/extract"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, image_bytes, "image/jpeg")}
            response = await client.post(ocr_url, files=files)
            response.raise_for_status()
            data = response.json()
            parsed = _parse_ocr_response(data)

            if parsed.get("extraction_confidence") == "LOW":
                # TODO: Eventually surface low confidence warning in the API response for the frontend to display
                logger.warning(
                    f"OCR extraction completed with LOW confidence for file '{filename}'. Quality status: {parsed.get('quality_status')}"
                )

            return parsed
    except (httpx.HTTPError, ValueError, KeyError) as err:
        raise ExternalServiceError(f"OCR service request failed: {str(err)}") from err


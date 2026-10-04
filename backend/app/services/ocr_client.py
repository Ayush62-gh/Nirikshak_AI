import asyncio
import logging
import httpx
from app.core.config import settings
from app.core.errors import ExternalServiceError

logger = logging.getLogger(__name__)


def _parse_ocr_response(response: dict) -> dict:
    if not isinstance(response, dict):
        raise ExternalServiceError("OCR service returned invalid or non-dictionary response payload.")

    fields = response.get("fields")
    if not isinstance(fields, dict):
        fields = {}

    quality = response.get("quality")
    if not isinstance(quality, dict):
        quality = {}

    month = fields.get("monthOfPacking")
    year = fields.get("yearOfPacking")

    if month and year:
        mfg_date = f"{month}/{year}"
    else:
        mfg_date = None

    exp_month = fields.get("expiryMonth")
    exp_year = fields.get("expiryYear")

    if exp_month and exp_year:
        expiry_date = f"{exp_month}/{exp_year}"
    else:
        expiry_date = None

    quality_status = quality.get("quality_status") or fields.get("quality_status")
    extraction_confidence = fields.get("extraction_confidence")

    font_px_comp = fields.get("fontHeightPxComparison")
    if isinstance(font_px_comp, dict):
        measured_blocks = font_px_comp.get("measured_blocks")
        if isinstance(measured_blocks, list) and len(measured_blocks) > 0:
            font_readability_px = {
                "smallest": font_px_comp.get("smallest_height_px"),
                "median": font_px_comp.get("median_height_px"),
                "largest": font_px_comp.get("largest_height_px"),
                "block_count": len(measured_blocks),
            }
        else:
            font_readability_px = None
    else:
        font_readability_px = None

    return {
        "product_name": fields.get("productName"),
        "manufacturer": fields.get("manufacturerName"),
        "net_quantity": fields.get("netQuantity"),
        "mrp": fields.get("mrp"),
        "batch_number": fields.get("batchNumber"),
        "mfg_date": mfg_date,
        "consumer_care": fields.get("consumerCare"),
        "raw_ocr_text": response.get("full_text") or response.get("combined_full_text"),
        "manufacturer_address": fields.get("manufacturerAddress"),
        "quality_status": quality_status,
        "extraction_confidence": extraction_confidence,
        "country_of_origin": fields.get("countryOfOrigin"),
        "importer_name": fields.get("importerName"),
        "unit_sale_price": fields.get("unitSalePrice"),
        "font_size_mm": fields.get("fontHeightMm"),
        "expiry_date": expiry_date,
        "font_readability_px": font_readability_px,
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
        timeout = httpx.Timeout(90.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
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
    except ExternalServiceError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as err:
        raise ExternalServiceError(f"OCR service request failed: {str(err)}") from err


async def extract_fields_multi(images: list[tuple[str, bytes]]) -> dict:
    """
    Extracts text and key Legal Metrology fields from multiple package label images.
    When settings.use_mock_ocr is True, returns simulated mock data.
    When settings.use_mock_ocr is False, POSTs images to OCR service at /extract-multi.
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
    ocr_url = f"{settings.OCR_SERVICE_URL.rstrip('/')}/extract-multi"
    try:
        timeout = httpx.Timeout(150.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            files = [("files", (filename, img_bytes, "image/jpeg")) for filename, img_bytes in images]
            response = await client.post(ocr_url, files=files)
            response.raise_for_status()
            data = response.json()
            parsed = _parse_ocr_response(data)

            if parsed.get("extraction_confidence") == "LOW":
                logger.warning(
                    f"OCR multi-image extraction completed with LOW confidence for {len(images)} images. Quality status: {parsed.get('quality_status')}"
                )

            return parsed
    except ExternalServiceError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as err:
        raise ExternalServiceError(f"OCR service request failed: {str(err)}") from err



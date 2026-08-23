import asyncio
import httpx
from app.core.config import settings


async def extract_fields(image_bytes: bytes, filename: str) -> dict:
    """
    Extracts text and key Legal Metrology fields from package label image.
    Currently mocked to simulate ml_service OCR behavior.
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

    # REAL SERVICE INTEGRATION (Future Phase Ready)
    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {"file": (filename, image_bytes, "image/jpeg")}
        response = await client.post(f"{settings.OCR_SERVICE_URL}/extract", files=files)
        response.raise_for_status()
        return response.json()

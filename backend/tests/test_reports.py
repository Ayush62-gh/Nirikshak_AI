import io
from pathlib import Path
from PIL import Image
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pdf_report_generation_and_download(client: AsyncClient):
    """Test generating and downloading PDF compliance audit report."""
    # 1. Register Inspector
    reg_payload = {
        "name": "Inspector Meera",
        "email": "meera.report@metrology.gov.in",
        "password": "Password123!",
        "role": "INSPECTOR",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Inspection & Upload Image
    insp_payload = {
        "product_name": "Premium Basmati Rice 1kg",
        "barcode": "8901112223334",
        "category": "Grains",
        "manufacturer": "Bharat Rice Mills Ltd",
    }
    res_insp = await client.post("/api/v1/inspections", json=insp_payload, headers=headers)
    insp_id = res_insp.json()["data"]["id"]

    # Upload valid image
    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    files = [("images", ("label.jpg", buf, "image/jpeg"))]
    await client.post(f"/api/v1/inspections/{insp_id}/images", files=files, headers=headers)

    # 3. Run Scan Pipeline
    await client.post(f"/api/v1/inspections/{insp_id}/scan", headers=headers)

    # 4. Generate Report via POST
    res_gen = await client.post(f"/api/v1/reports/{insp_id}/generate", headers=headers)
    assert res_gen.status_code == 200
    rep_data = res_gen.json()["data"]
    assert rep_data["inspection_id"] == insp_id
    assert rep_data["report_type"] == "PDF"

    # 5. Download Report via GET
    res_get = await client.get(f"/api/v1/reports/{insp_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.headers["content-type"] == "application/pdf"
    assert len(res_get.content) > 1000  # Valid PDF size
    assert res_get.content[:4] == b"%PDF"  # Valid PDF signature

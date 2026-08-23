import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_inspection_workflow(client: AsyncClient):
    """Test creating inspection, uploading images, and retrieving inspection details."""
    # 1. Register Inspector
    reg_payload = {
        "name": "Inspector Ananya Verma",
        "email": "ananya.verma@metrology.gov.in",
        "password": "Password123!",
        "role": "INSPECTOR",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Inspection with inline product details
    insp_payload = {
        "product_name": "Crunchy Potato Chips 50g",
        "barcode": "8909876543210",
        "category": "Snacks",
        "manufacturer": "SnackCorp India Ltd",
    }
    res_insp = await client.post("/api/v1/inspections", json=insp_payload, headers=headers)
    assert res_insp.status_code == 201
    insp_data = res_insp.json()["data"]
    inspection_id = insp_data["id"]
    assert insp_data["status"] == "PENDING"
    assert insp_data["product"]["product_name"] == "Crunchy Potato Chips 50g"

    # 3. Upload Sample Image to Inspection
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + (b"\x00" * 100)
    files = [
        ("images", ("label_front.jpg", io.BytesIO(fake_image_bytes), "image/jpeg"))
    ]
    res_upload = await client.post(
        f"/api/v1/inspections/{inspection_id}/images", files=files, headers=headers
    )
    assert res_upload.status_code == 200
    upload_data = res_upload.json()["data"]
    assert len(upload_data) == 1
    assert upload_data[0]["original_filename"] == "label_front.jpg"
    assert "uploads/" in upload_data[0]["image_path"]

    # 4. Attempt uploading invalid file extension
    invalid_file = [
        ("images", ("malicious.exe", io.BytesIO(b"binary_executable"), "application/octet-stream"))
    ]
    res_inv = await client.post(
        f"/api/v1/inspections/{inspection_id}/images", files=invalid_file, headers=headers
    )
    assert res_inv.status_code == 422

    # 5. Get Inspection Details
    res_get = await client.get(f"/api/v1/inspections/{inspection_id}", headers=headers)
    assert res_get.status_code == 200
    detail = res_get.json()["data"]
    assert detail["id"] == inspection_id
    assert len(detail["images"]) == 1

    # 6. List Inspections with filter
    res_list = await client.get("/api/v1/inspections?status=PENDING", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1

    # 7. Get Inspection Violations (initially empty)
    res_viol = await client.get(
        f"/api/v1/inspections/{inspection_id}/violations", headers=headers
    )
    assert res_viol.status_code == 200
    assert res_viol.json()["data"] == []

import io
from PIL import Image
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary_and_trends(client: AsyncClient):
    """Test dashboard aggregation endpoints with active inspection data."""
    # 1. Register User
    reg_payload = {
        "name": "Dashboard Analyst",
        "email": "analyst@metrology.gov.in",
        "password": "Password123!",
        "role": "INSPECTOR",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create and run an inspection
    insp_payload = {
        "product_name": "Organic Honey 500g",
        "barcode": "8904445556667",
        "category": "Food",
        "manufacturer": "Pure Bees Agro Ltd",
    }
    res_insp = await client.post("/api/v1/inspections", json=insp_payload, headers=headers)
    insp_id = res_insp.json()["data"]["id"]

    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    files = [("images", ("label.jpg", buf, "image/jpeg"))]
    await client.post(f"/api/v1/inspections/{insp_id}/images", files=files, headers=headers)
    await client.post(f"/api/v1/inspections/{insp_id}/scan", headers=headers)

    # 3. Test Dashboard Summary
    res_summary = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert res_summary.status_code == 200
    summary_data = res_summary.json()["data"]

    assert summary_data["total_inspections"] >= 1
    assert "average_compliance_score" in summary_data
    assert "violations_by_severity" in summary_data
    assert len(summary_data["recent_inspections"]) >= 1

    # 4. Test Dashboard Trends
    res_trends = await client.get("/api/v1/dashboard/trends", headers=headers)
    assert res_trends.status_code == 200
    trends_data = res_trends.json()["data"]
    assert "top_violations" in trends_data
    assert "category_breakdown" in trends_data

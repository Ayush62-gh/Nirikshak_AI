import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_crud_flow(client: AsyncClient):
    """Test full product CRUD flow with authentication."""
    # 1. Register Admin
    reg_payload = {
        "name": "Admin Product Manager",
        "email": "product.admin@metrology.gov.in",
        "password": "Password123!",
        "role": "ADMIN",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Product
    create_payload = {
        "product_name": "Premium Basmati Rice 5kg",
        "barcode": "8901234560001",
        "category": "Grains & Cereals",
        "manufacturer": "Royal Agro Foods Ltd",
    }
    res_create = await client.post("/api/v1/products", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    prod_data = res_create.json()["data"]
    assert prod_data["product_name"] == "Premium Basmati Rice 5kg"
    product_id = prod_data["id"]

    # 3. Duplicate barcode check
    res_dup = await client.post("/api/v1/products", json=create_payload, headers=headers)
    assert res_dup.status_code == 422

    # 4. Get Product by ID
    res_get = await client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["data"]["barcode"] == "8901234560001"

    # 5. List Products with search query
    res_list = await client.get("/api/v1/products?query=Basmati", headers=headers)
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert len(list_data["data"]) >= 1
    assert list_data["pagination"]["total_items"] >= 1

    # 6. Update Product
    update_payload = {"product_name": "Premium Royal Basmati Rice 5kg"}
    res_update = await client.put(f"/api/v1/products/{product_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["data"]["product_name"] == "Premium Royal Basmati Rice 5kg"

    # 7. Delete Product
    res_del = await client.delete(f"/api/v1/products/{product_id}", headers=headers)
    assert res_del.status_code == 200

    # Verify deleted
    res_get_deleted = await client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert res_get_deleted.status_code == 404

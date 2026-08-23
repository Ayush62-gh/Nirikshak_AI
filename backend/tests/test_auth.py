import pytest
from httpx import AsyncClient
from app.core.security import create_access_token
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration."""
    payload = {
        "name": "Inspector Priya Sharma",
        "email": "priya.sharma@metrology.gov.in",
        "password": "SecurePassword123!",
        "role": "INSPECTOR",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == "priya.sharma@metrology.gov.in"
    assert data["data"]["user"]["role"] == "INSPECTOR"
    assert "password_hash" not in data["data"]["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration fails when email is already taken."""
    payload = {
        "name": "Officer Vikram",
        "email": "vikram@metrology.gov.in",
        "password": "Password123!",
        "role": "INSPECTOR",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 422
    data = res2.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test user login with correct credentials."""
    # Register first
    reg_payload = {
        "name": "Admin User",
        "email": "admin@metrology.gov.in",
        "password": "AdminSecretPassword99!",
        "role": "ADMIN",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "admin@metrology.gov.in",
        "password": "AdminSecretPassword99!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["role"] == "ADMIN"
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login fails with incorrect password."""
    reg_payload = {
        "name": "Viewer User",
        "email": "viewer@metrology.gov.in",
        "password": "ViewerPassword123!",
        "role": "VIEWER",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "viewer@metrology.gov.in",
        "password": "WrongPassword!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient):
    """Test GET /api/v1/auth/me with Bearer token."""
    reg_payload = {
        "name": "Inspector Sunita",
        "email": "sunita@metrology.gov.in",
        "password": "SunitaPassword123!",
        "role": "INSPECTOR",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]

    # Request /me with token
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "sunita@metrology.gov.in"
    assert data["data"]["role"] == "INSPECTOR"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test GET /api/v1/auth/me without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_register_login_me_flow():
    # 1. Register a new user
    user_payload = {
        "email": "test_inspector@nirikshak.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Test Inspector",
    }
    reg_res = client.post("/api/auth/register", json=user_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test_inspector@nirikshak.gov.in"
    assert data["user"]["full_name"] == "Test Inspector"

    # 2. Duplicate registration attempt should fail with 400
    dup_res = client.post("/api/auth/register", json=user_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Login with correct credentials
    login_payload = {
        "email": "test_inspector@nirikshak.gov.in",
        "password": "SecurePassword123!",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    token = token_data["access_token"]
    assert token is not None

    # 4. Login with wrong password should fail with 401
    wrong_login = {
        "email": "test_inspector@nirikshak.gov.in",
        "password": "WrongPassword!",
    }
    wrong_res = client.post("/api/auth/login", json=wrong_login)
    assert wrong_res.status_code == 401

    # 5. Access /api/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "test_inspector@nirikshak.gov.in"
    assert me_data["full_name"] == "Test Inspector"

    # 6. Access /api/auth/me without token should fail with 401
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

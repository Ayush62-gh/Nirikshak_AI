import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint / returns API metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["status"] == "online"
    assert data["health"] == "/health"


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Test the GET /health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data

import pytest
from app.core.config import Settings, settings


def test_settings_loaded():
    """Verify settings defaults and types."""
    assert settings.APP_NAME is not None
    assert settings.JWT_SECRET is not None
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MAX_UPLOAD_SIZE_MB > 0


def test_cors_parsing():
    """Verify CORS origins parsing for list and strings."""
    s = Settings(CORS_ORIGINS='["http://localhost:3000"]')
    assert s.CORS_ORIGINS == ["http://localhost:3000"]

    s2 = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:8000")
    assert "http://localhost:3000" in s2.CORS_ORIGINS
    assert "http://localhost:8000" in s2.CORS_ORIGINS

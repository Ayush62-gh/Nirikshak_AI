from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "app" / "db" / "nirikshak.db"


class Settings(BaseSettings):
    OCR_SERVICE_URL: str = "http://localhost:5001"
    RULE_ENGINE_URL: str = "http://localhost:5002"
    PORT: int = 8000
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    use_mock_ocr: bool = True
    use_mock_rule_engine: bool = True

    # JWT Settings
    JWT_SECRET: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS Settings
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://nirikshak.vercel.app",
        "https://nirikshak-ai.vercel.app",
    ]
    CORS_ORIGIN_REGEX: str | None = r"https://.*\.vercel\.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("JWT_SECRET", mode="after")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("JWT_SECRET environment variable is missing or empty.")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins
        return v

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///./"):
            rel_part = v.replace("sqlite:///./", "")
            abs_path = (BASE_DIR / rel_part).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
        return v


settings = Settings()



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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///./"):
            rel_part = v.replace("sqlite:///./", "")
            abs_path = (BASE_DIR / rel_part).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
        return v


settings = Settings()


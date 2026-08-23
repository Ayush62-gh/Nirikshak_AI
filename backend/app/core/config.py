import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Nirikshak AI - Legal Metrology Compliance Engine"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./nirikshak.db"
    SYNC_DATABASE_URL: str = "sqlite:///./nirikshak.db"
    DB_ECHO: bool = False

    # Security & JWT
    JWT_SECRET: str = "supersecretjwtkeyfornirikshaklegalmetrologycompliancesystem2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # File Storage
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 25

    # Rules & Config Files
    RULES_FILE_PATH: str = "data/rules/legal_metrology_rules.json"
    RULE_PARAMS_FILE_PATH: str = "data/rules/rule_parameters.json"

    # OCR Settings
    OCR_PROVIDER: str = "tesseract"
    TESSERACT_CMD: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            p = BASE_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def report_path(self) -> Path:
        p = Path(self.REPORT_DIR)
        if not p.is_absolute():
            p = BASE_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def rules_path(self) -> Path:
        p = Path(self.RULES_FILE_PATH)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p

    @property
    def rule_params_path(self) -> Path:
        p = Path(self.RULE_PARAMS_FILE_PATH)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p


settings = Settings()

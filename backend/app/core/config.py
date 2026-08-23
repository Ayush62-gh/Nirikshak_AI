from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OCR_SERVICE_URL: str = "http://localhost:5001"
    RULE_ENGINE_URL: str = "http://localhost:5002"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./app/db/nirikshak.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

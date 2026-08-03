from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str
    BACKEND_CORS_ORIGINS: list[str] = []
    STORAGE_BASE_PATH: str = "storage"
    MAX_UPLOAD_SIZE_MB: int = 100

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            import json
            return json.loads(value)
        raise ValueError("BACKEND_CORS_ORIGINS must be a list or JSON array string")


settings = Settings()

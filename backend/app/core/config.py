import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "MultimediaToolKit API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS configuration
    ALLOWED_ORIGINS: str = "*"

    # Database configuration (PostgreSQL or local SQLite fallback)
    DATABASE_URL: str = "sqlite:///./multimediatoolkit.db"

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # File storage root directory
    STORAGE_DIR: str = os.path.join(os.getcwd(), "storage")
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB default cap

    @property
    def cors_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)

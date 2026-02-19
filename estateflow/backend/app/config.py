"""
EstateFlow configuration settings.

Uses environment variables with fallback defaults.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings.

    All settings can be overridden via environment variables.
    """

    # Application
    APP_NAME: str = "EstateFlow"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 30039

    # MongoDB
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%@127.0.0.1:27017/"
    )
    MONGODB_DB_NAME: str = "estateflow"

    # Supabase
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL",
        "https://supabase.ailabsafrica.com"
    )
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # Redis (for caching)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # CORS
    CORS_ORIGINS: list = [
        "https://estateflow.ailabsafrica.com",
        "https://dev-estateflow.ailabsafrica.com",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    UPLOAD_DIR: str = "/opt/kasaai/apps/estateflow/backend/storage"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # External APIs
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)

    class Config:
        """Pydantic configuration."""
        env_file = "/opt/kasaai/.env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()

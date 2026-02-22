"""
EstateFlow configuration settings.

Standalone local application - no external SaaS dependencies.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()


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

    # MongoDB - Local connection
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        "mongodb://localhost:27017/"
    )
    MONGODB_DB_NAME: str = "estateflow"

    # JWT Authentication (Local - no external service)
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "estateflow-super-secret-key-change-in-production-2024"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Redis (optional - for caching)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # CORS - Allow all localhost origins
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ]

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")

    # File Upload - Local storage
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        str(PROJECT_ROOT / "storage")
    )
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # External APIs (optional - for AI features)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Gemini AI Model
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Google Maps (optional - for geocoding)
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    # Payment Gateways (optional - deferred)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    FLUTTERWAVE_SECRET_KEY: Optional[str] = None
    FLUTTERWAVE_PUBLIC_KEY: Optional[str] = None
    FLUTTERWAVE_ENCRYPTION_KEY: Optional[str] = None
    FLUTTERWAVE_WEBHOOK_SECRET: Optional[str] = None

    # Default Admin User (created on first run)
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@estateflow.local")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123!")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

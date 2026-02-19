"""
Configuration settings for KasaAI Drive.

Author: AI Labs Africa
Date: 2025-11-10
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "KasaAI Drive"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("PORT", "30037"))

    # MongoDB
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin"
    )
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "kasaai_drive")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://supabase-api.ailabsafrica.com")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Organization System
    DEFAULT_ORGANIZATION_ID: str = os.getenv("DEFAULT_ORGANIZATION_ID", "ai_labs_ltd")
    DEFAULT_ORGANIZATION_NAME: str = "AI Labs Ltd."
    UNIVERSAL_ADMIN_EMAILS: str = os.getenv(
        "UNIVERSAL_ADMIN_EMAILS",
        "admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com"
    )
    UNIVERSAL_ADMIN_USER_IDS: str = os.getenv(
        "UNIVERSAL_ADMIN_USER_IDS",
        "4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06"
    )

    # Hetzner Storage
    HETZNER_STORAGE_USERNAME: str = os.getenv("HETZNER_STORAGE_USERNAME", "")
    HETZNER_STORAGE_PASSWORD: str = os.getenv("HETZNER_STORAGE_PASSWORD", "")
    HETZNER_STORAGE_HOST: str = os.getenv("HETZNER_STORAGE_HOST", "")
    HETZNER_STORAGE_PROTOCOL: str = os.getenv("HETZNER_STORAGE_PROTOCOL", "webdav")

    # Storage Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "kasaai-drive-secret-key-change-in-production")
    CORS_ORIGINS: list = [
        "https://drive.ailabsafrica.com",
        "https://dev-drive.ailabsafrica.com",
        "http://localhost:3000",
        "http://localhost:3001"
    ]

    class Config:
        env_file = "/opt/kasaai/.env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()

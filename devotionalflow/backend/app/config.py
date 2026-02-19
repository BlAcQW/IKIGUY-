"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "DevotionalFlow API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 30037

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "https://devotionalflow.ailabsafrica.com",
    ]
    FRONTEND_URL: str = "https://freshmanna.ailabsafrica.com"

    # Database
    MONGODB_URI: str
    DATABASE_NAME: str = "devotionalflow"

    # Supabase Authentication
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str

    # AI Services
    OPENAI_API_KEY: str

    # Scripture API (optional)
    BIBLE_API_KEY: str = ""
    ESV_API_KEY: str = ""

    # Pexels API (for devotional images)
    PEXELS_API_KEY: str = ""

    # Email Configuration (iRedMail via shared UnifiedEmailService)
    SMTP_HOST: str = "localhost"
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    SMTP_FROM_EMAIL: str = "noreply@freshmanna.com"
    SENDER_EMAIL: str = "noreply@freshmanna.com"
    SENDER_NAME: str = "FreshManna"

    # Storage (Hetzner from @shared/)
    HETZNER_STORAGE_ENDPOINT: str = ""
    HETZNER_STORAGE_ACCESS_KEY: str = ""
    HETZNER_STORAGE_SECRET_KEY: str = ""
    HETZNER_STORAGE_BUCKET: str = "devotionalflow"

    # Hetzner Storage Box (WebDAV) - Used by @shared/storage/
    HETZNER_STORAGE_USERNAME: str = ""
    HETZNER_STORAGE_PASSWORD: str = ""
    HETZNER_STORAGE_HOST: str = ""
    HETZNER_STORAGE_PROTOCOL: str = "webdav"
    HETZNER_STORAGE_BASE_PATH: str = "kasaai/devotionalflow"

    # Firebase (optional for push notifications)
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    
    # Web Push (VAPID keys for browser push notifications)
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_EMAIL: str = "noreply@freshmanna.com"

    # WhatsApp/Twilio (for subscription service)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""  # Format: whatsapp:+1234567890

    model_config = SettingsConfigDict(
        env_file="/opt/kasaai/apps/devotionalflow/backend/.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()

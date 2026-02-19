"""
Configuration settings for ERP application.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Project
    PROJECT_NAME: str = "KasaAI ERP"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # MongoDB
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/"
    )
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "erp")

    # Supabase Auth
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://supabase.ailabsafrica.com")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    UNIVERSAL_ADMIN_EMAILS: str = os.getenv("UNIVERSAL_ADMIN_EMAILS", "admin@ailabsafrica.com")
    UNIVERSAL_ADMIN_USER_IDS: str = os.getenv("UNIVERSAL_ADMIN_USER_IDS", "")

    # CORS
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,https://erp.ailabsafrica.com,https://dev-erp.ailabsafrica.com",
    )

    # iRedMail Email Account Management
    IREDMAIL_API_URL: str = os.getenv("IREDMAIL_API_URL", "https://iredmail-api.ailabsafrica.com")
    IREDMAIL_API_KEY: str = os.getenv("IREDMAIL_API_KEY", "")
    IREDMAIL_DEFAULT_QUOTA_MB: int = int(os.getenv("IREDMAIL_DEFAULT_QUOTA_MB", "512"))

    # File Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/opt/kasaai/apps/erp/uploads")
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    ALLOWED_EXTENSIONS: str = os.getenv(
        "ALLOWED_EXTENSIONS",
        # Documents
        ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.csv,"
        # Images
        ".jpg,.jpeg,.png,.gif,.bmp,.webp,.svg,.ico,"
        # Audio
        ".mp3,.wav,.m4a,.ogg,.flac,.aac,.wma,"
        # Video
        ".mp4,.mov,.avi,.mkv,.webm,.wmv,.flv,.m4v,"
        # Archives
        ".zip,.rar,.7z,.tar,.gz,"
        # Design/Artifacts
        ".psd,.ai,.sketch,.fig,.xd"
    )

    # Hetzner Storage Box
    HETZNER_STORAGE_USERNAME: str = os.getenv("HETZNER_STORAGE_USERNAME", "")
    HETZNER_STORAGE_PASSWORD: str = os.getenv("HETZNER_STORAGE_PASSWORD", "")
    HETZNER_STORAGE_HOST: str = os.getenv("HETZNER_STORAGE_HOST", "")
    HETZNER_STORAGE_PROTOCOL: str = os.getenv("HETZNER_STORAGE_PROTOCOL", "webdav")
    HETZNER_STORAGE_BASE_PATH: str = os.getenv("HETZNER_STORAGE_BASE_PATH", "kasaai")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


settings = Settings()

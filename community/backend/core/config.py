"""
Configuration settings for African Language Community Platform.

Manages environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Handles database connections, authentication, file storage, and external APIs.
    """

    # Application
    PROJECT_NAME: str = "African Language Community Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"  # Change in production

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://language-community.ailabsafrica.com",
        "https://kasaai.ailabsafrica.com",
        "https://api.ailabsafrica.com"
    ]

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "african_language_community"

    # Authentication (Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Redis for caching and background tasks
    REDIS_URL: str = "redis://localhost:6379"

    # File Storage
    STORAGE_TYPE: str = "local"  # "local", "s3", "minio"
    STORAGE_PATH: str = "/opt/kasaai/data/community"

    # AWS S3 (if using S3 storage)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: str = "african-language-data"

    # MinIO (if using MinIO storage)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET_NAME: str = "african-language-data"

    # External APIs
    GOOGLE_TRANSLATE_API_KEY: str = ""
    HUGGINGFACE_API_TOKEN: str = ""

    # Gamification
    DEFAULT_POINTS: dict = {
        "audio_submission": 50,
        "text_submission": 30,
        "validation": 20,
        "quality_improvement": 40,
        "cultural_note": 35,
        "external_link": 25,
        "family_resource_creation": 100,
        "dialect_expansion": 75,
        "gold_standard_promotion": 150
    }

    # Quality thresholds
    QUALITY_THRESHOLDS: dict = {
        "tier_1_minimum_score": 8.5,
        "tier_1_validators_required": 3,
        "tier_2_minimum_score": 7.0,
        "tier_2_validators_required": 2,
        "consensus_threshold": 0.8
    }

    # File limits
    MAX_FILE_SIZE_MB: int = 100
    SUPPORTED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]
    SUPPORTED_TEXT_FORMATS: List[str] = [".txt", ".md", ".pdf"]

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list."""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            return v
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings: Application configuration settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
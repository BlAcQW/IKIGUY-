"""
Configuration settings for InkWave backend.

Loads environment variables and provides application configuration.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # App Info
    APP_NAME: str = "InkWave API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Frontend URL (for generating invitation links)
    FRONTEND_URL: str = "https://inkwave.ailabsafrica.com"

    # CORS Origins
    CORS_ORIGINS: list[str] = [
        "https://dev-inkwave.ailabsafrica.com",
        "https://inkwave.ailabsafrica.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://85.214.12.174:5173",
    ]

    # Supabase (Authentication)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # MongoDB
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "inkwave"

    # PostgreSQL (pgvector for RAG)
    POSTGRES_URI: Optional[str] = None

    # Gemini AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # OpenAI (STT/TTS)
    OPENAI_API_KEY: str
    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_TTS_VOICE: str = "nova"

    # Payment Gateways
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    PAYSTACK_API_KEY: Optional[str] = None

    # Storage
    STORAGE_PROVIDER: str = "local"  # local, s3, gcs
    STORAGE_BUCKET: Optional[str] = None
    STORAGE_PATH: str = "/opt/kasaai/apps/inkwave/storage"

    # RAG Configuration
    RAG_RETRIEVAL_K: int = 5
    RAG_CONFIDENCE_THRESHOLD: float = 0.7
    RAG_TEMPERATURE: float = 0.1

    # Voice Configuration
    MAX_RECORDING_DURATION: int = 60  # seconds
    MAX_QUESTION_LENGTH: int = 500  # characters

    # Pricing (credits per unit, 100 credits = $1)
    PRICING_NARRATION_PER_MINUTE: int = 2  # 2 credits/min
    PRICING_STT_PER_MINUTE: int = 60  # 60 credits/min
    PRICING_TTS_PER_1K_CHARS: int = 150  # 150 credits/1k chars
    PRICING_RAG_PER_QUERY: int = 30  # 30 credits/query

    # Free trial
    FREE_TRIAL_CREDITS: int = 200  # $2.00

    # Slack Integration
    SLACK_WEBHOOK_URL: Optional[str] = "https://hooks.slack.com/services/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"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string to list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS


# Global settings instance
settings = Settings()

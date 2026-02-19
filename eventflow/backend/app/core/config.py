"""
EventFlow Backend Configuration.

Loads environment variables and provides configuration settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # App Info
    app_name: str = "EventFlow"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Security
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # MongoDB
    mongodb_url: str = Field(alias="MONGODB_URL")
    mongodb_database: str = Field(default="kasaai_eventflow", alias="MONGODB_DATABASE")

    # Supabase
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_anon_key: str = Field(alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")

    # VAPI
    vapi_api_key: str = Field(alias="VAPI_API_KEY")
    vapi_base_url: str = Field(
        default="https://api.vapi.ai", alias="VAPI_BASE_URL"
    )
    vapi_gh_phone_id: Optional[str] = Field(default=None, alias="VAPI_GH_PHONE_ID")

    # n8n
    n8n_base_url: Optional[str] = Field(default=None, alias="N8N_BASE_URL")
    n8n_api_key: Optional[str] = Field(default=None, alias="N8N_API_KEY")

    class Config:
        """Pydantic config."""

        env_file = "/opt/kasaai/.env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins list."""
        return [
            "https://dev-eventflow.ailabsafrica.com",
            "https://eventflow.ailabsafrica.com",
            "http://localhost:5173",
            "http://localhost:3000",
        ]


# Global settings instance
settings = Settings()

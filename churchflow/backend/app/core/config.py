"""
Application configuration using Pydantic settings.

This module loads configuration from environment variables and provides
typed access to application settings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        app_name: Application name
        app_version: Application version
        environment: Current environment (development, staging, production)
        debug: Debug mode flag
        api_host: API host address
        api_port: API port number
        api_prefix: API route prefix
        secret_key: Secret key for JWT tokens
        algorithm: JWT algorithm
        access_token_expire_minutes: Token expiration time
        mongodb_url: MongoDB connection URL
        mongodb_db_name: MongoDB database name
        supabase_url: Supabase project URL
        supabase_key: Supabase anonymous key
        supabase_service_role_key: Supabase service role key
        supabase_secret_key: Supabase JWT secret for token verification
        supabase_realtime_url: Supabase Realtime WebSocket URL
        twilio_account_sid: Twilio account SID (via n8n)
        twilio_auth_token: Twilio auth token (via n8n)
        twilio_phone_number: Twilio phone number for SMS
        twilio_whatsapp_number: Twilio WhatsApp number
        smtp_host: iRedMail SMTP host
        smtp_port: SMTP port
        smtp_username: SMTP username
        smtp_password: SMTP password
        smtp_from_email: Default sender email
        smtp_from_name: Default sender name
        smtp_use_tls: Use TLS for SMTP
        kasaai_voice_lab_url: KasaAI Voice Lab API URL
        kasaai_voice_lab_api_key: KasaAI Voice Lab API key
        cors_origins: Allowed CORS origins
        sentry_dsn: Sentry DSN for error tracking (optional)
        rate_limit_per_minute: API rate limit per minute
        nominatim_base_url: Nominatim geocoding API base URL
        nominatim_email: Contact email for OSM Nominatim service
        geocoding_timeout: Timeout for geocoding requests in seconds
        geocoding_rate_limit: Rate limit for geocoding requests (requests per second)
    """

    # Application
    app_name: str = Field(default="ChurchFlow")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")

    # Security
    secret_key: str = Field(...)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=43200)  # 30 days

    # Database
    mongodb_url: str = Field(...)
    mongodb_db_name: str = Field(default="churchflow")

    # Supabase
    supabase_url: str = Field(...)
    supabase_key: str = Field(...)
    supabase_service_role_key: str = Field(...)
    supabase_secret_key: str = Field(...)  # JWT secret for verifying Supabase tokens

    # Supabase Realtime
    supabase_realtime_url: str = Field(default="wss://supabase.ailabsafrica.com/realtime/v1")

    # Twilio (via n8n)
    twilio_account_sid: str = Field(default="placeholder-twilio-account-sid")
    twilio_auth_token: str = Field(default="placeholder-twilio-auth-token")
    twilio_phone_number: str = Field(default="+10000000000")
    twilio_whatsapp_number: str = Field(default="whatsapp:+10000000000")

    # Arkesel SMS Gateway (primary SMS provider for Ghana)
    arkesel_api_key: str = Field(default="ZldKVUlZc212UEpjdVdMZG1ab0s")
    arkesel_api_url: str = Field(default="https://sms.arkesel.com/api/v2/sms/send")
    arkesel_sender_id: str = Field(default="IMPACT2025")

    # iRedMail SMTP (Local Email)
    smtp_host: str = Field(...)
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(...)
    smtp_password: str = Field(...)
    smtp_from_email: str = Field(...)
    smtp_from_name: str = Field(default="ChurchFlow")
    smtp_use_tls: bool = Field(default=True)

    # KasaAI Voice Lab
    kasaai_voice_lab_url: str = Field(default="https://voice.kasaai.com")
    kasaai_voice_lab_api_key: str = Field(default="")

    # CORS
    churchflow_cors_origins: str = Field(default="http://localhost:3000")

    @property
    def cors_origins(self) -> str:
        """
        Alias for churchflow_cors_origins for backward compatibility.

        Returns:
            CORS origins string
        """
        return self.churchflow_cors_origins

    # Sentry
    sentry_dsn: str = Field(default="")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)

    # n8n Workflow Automation
    n8n_base_url: str = Field(default="http://automations.ailabsafrica.com")
    n8n_api_key: str = Field(default="")
    n8n_webhook_base_url: str = Field(default="http://automations.ailabsafrica.com/webhook")

    # Stripe Payment & Billing
    stripe_secret_key: str = Field(...)
    stripe_publishable_key: str = Field(...)
    stripe_webhook_secret: str = Field(...)
    stripe_environment: str = Field(default="sandbox")  # sandbox or production

    # Nominatim Geocoding
    nominatim_base_url: str = Field(default="https://nominatim.openstreetmap.org")
    nominatim_email: str = Field(default="tech@ailabsafrica.com")  # OSM recommends contact email
    geocoding_timeout: int = Field(default=10)  # seconds
    geocoding_rate_limit: float = Field(default=1.0)  # requests per second (OSM requirement)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables not in model
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS origins from comma-separated string.

        Returns:
            List of allowed origin URLs
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

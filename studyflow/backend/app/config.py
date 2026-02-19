"""
Configuration management for StudyFlow backend.

Loads environment variables and provides type-safe configuration.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseModel):
    """Application settings."""

    # Environment
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    ENVIRONMENT: str = Field(default="development")

    # API Configuration
    API_V1_STR: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="StudyFlow API")

    # AI Provider - Gemini 2.5 Flash (Latest, fastest, cheapest!)
    AI_PROVIDER: str = Field(default="gemini")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = Field(default="text-embedding-004")

    # MongoDB Configuration
    MONGODB_URL: str = Field(default="mongodb://localhost:27017/studyflow")
    MONGODB_DATABASE: str = Field(default="studyflow")

    # PostgreSQL with pgvector (for RAG embeddings)
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: str = Field(default="5432")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="postgres")

    # Supabase (Authentication)
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")

    # Organization & Multi-tenancy
    DEFAULT_ORGANIZATION_ID: str = Field(default="0d4deec6-80b0-4669-b703-c0aeded1a9c1")
    UNIVERSAL_ADMIN_EMAILS: str = Field(default="admin@ailabsafrica.com")

    # Payment Gateways
    PAYSTACK_SECRET_KEY: Optional[str] = None
    PAYSTACK_PUBLIC_KEY: Optional[str] = None
    FLUTTERWAVE_SECRET_KEY: Optional[str] = None
    MTN_MOMO_API_KEY: Optional[str] = None

    # Security
    JWT_SECRET_KEY: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000")

    # RAG Configuration
    RAG_CHUNK_SIZE: int = Field(default=1000)
    RAG_CHUNK_OVERLAP: int = Field(default=200)
    RAG_RETRIEVAL_K: int = Field(default=3)
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.3)
    RAG_CONFIDENCE_THRESHOLD: float = Field(default=0.7)

    # Pricing (in GHS - Ghana Cedis)
    FREE_TRIAL_MINUTES: int = Field(default=30)
    PAY_AS_YOU_LEARN_PRICE: float = Field(default=0.20)  # ₵20 = 100 minutes
    MONTHLY_PRICE: float = Field(default=50.00)
    SCHOOL_PRICE_PER_STUDENT: float = Field(default=30.00)

    # Features
    ENABLE_VOICE: bool = Field(default=True)
    ENABLE_IMAGE_UPLOAD: bool = Field(default=True)
    ENABLE_DOCUMENT_PROCESSING: bool = Field(default=True)
    ENABLE_SPEECH_TO_TEXT: bool = Field(default=True)

    # n8n Workflow Automation
    N8N_WEBHOOK_URL: Optional[str] = None
    N8N_API_KEY: Optional[str] = None

    # VAPI Voice Integration
    VAPI_API_KEY: Optional[str] = None
    VAPI_US_PHONE_ID: Optional[str] = None
    API_BASE_URL: str = Field(default="https://dev-studyflow-api.ailabsafrica.com")

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = Field(default=False)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def postgres_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance with environment variables loaded
    """
    return Settings(
        # Environment
        DEBUG=os.getenv("DEBUG", "false").lower() == "true",
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        ENVIRONMENT=os.getenv("ENVIRONMENT", "development"),

        # API
        API_V1_STR=os.getenv("API_V1_STR", "/api/v1"),
        PROJECT_NAME=os.getenv("PROJECT_NAME", "StudyFlow API"),

        # AI Provider - Gemini 2.5 Flash
        AI_PROVIDER=os.getenv("AI_PROVIDER", "gemini"),
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
        GEMINI_MODEL=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        GEMINI_EMBEDDING_MODEL=os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004"),

        # MongoDB
        MONGODB_URL=os.getenv("MONGODB_URL", "mongodb://localhost:27017/studyflow"),
        MONGODB_DATABASE=os.getenv("MONGODB_DATABASE", "studyflow"),

        # PostgreSQL
        POSTGRES_HOST=os.getenv("POSTGRES_HOST", "localhost"),
        POSTGRES_PORT=os.getenv("POSTGRES_PORT", "5432"),
        POSTGRES_USER=os.getenv("POSTGRES_USER", "postgres"),
        POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", ""),
        POSTGRES_DB=os.getenv("POSTGRES_DB", "postgres"),

        # Supabase
        SUPABASE_URL=os.getenv("SUPABASE_URL", ""),
        SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY", ""),
        SUPABASE_SERVICE_ROLE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),

        # Organization
        DEFAULT_ORGANIZATION_ID=os.getenv("DEFAULT_ORGANIZATION_ID", "studyflow_default"),
        UNIVERSAL_ADMIN_EMAILS=os.getenv("UNIVERSAL_ADMIN_EMAILS", "admin@ailabsafrica.com"),

        # Payment Gateways
        PAYSTACK_SECRET_KEY=os.getenv("PAYSTACK_SECRET_KEY"),
        FLUTTERWAVE_SECRET_KEY=os.getenv("FLUTTERWAVE_SECRET_KEY"),
        MTN_MOMO_API_KEY=os.getenv("MTN_MOMO_API_KEY"),

        # Security
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
        JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
        ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),

        # CORS
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:3000"),

        # RAG
        RAG_CHUNK_SIZE=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
        RAG_CHUNK_OVERLAP=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
        RAG_RETRIEVAL_K=int(os.getenv("RAG_RETRIEVAL_K", "3")),
        RAG_SIMILARITY_THRESHOLD=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.3")),
        RAG_CONFIDENCE_THRESHOLD=float(os.getenv("RAG_CONFIDENCE_THRESHOLD", "0.7")),

        # Pricing
        FREE_TRIAL_MINUTES=int(os.getenv("FREE_TRIAL_MINUTES", "30")),
        PAY_AS_YOU_LEARN_PRICE=float(os.getenv("PAY_AS_YOU_LEARN_PRICE", "0.20")),
        MONTHLY_PRICE=float(os.getenv("MONTHLY_PRICE", "50.00")),
        SCHOOL_PRICE_PER_STUDENT=float(os.getenv("SCHOOL_PRICE_PER_STUDENT", "30.00")),

        # Features
        ENABLE_VOICE=os.getenv("ENABLE_VOICE", "true").lower() == "true",
        ENABLE_IMAGE_UPLOAD=os.getenv("ENABLE_IMAGE_UPLOAD", "true").lower() == "true",
        ENABLE_DOCUMENT_PROCESSING=os.getenv("ENABLE_DOCUMENT_PROCESSING", "true").lower() == "true",
        ENABLE_SPEECH_TO_TEXT=os.getenv("ENABLE_SPEECH_TO_TEXT", "true").lower() == "true",

        # n8n
        N8N_WEBHOOK_URL=os.getenv("N8N_WEBHOOK_URL"),
        N8N_API_KEY=os.getenv("N8N_API_KEY"),

        # Monitoring
        SENTRY_DSN=os.getenv("SENTRY_DSN"),
        PROMETHEUS_ENABLED=os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true",
    )


# Global settings instance
settings = get_settings()

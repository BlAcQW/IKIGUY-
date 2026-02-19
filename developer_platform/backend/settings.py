from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration for the developer platform backend."""

    CORS_ORIGINS: str = Field(
        default="https://client.ailabsafrica.com",
        description="Comma-separated list of allowed CORS origins",
    )

    class Config:
        env_prefix = "DEV_PLATFORM_BACKEND_"
        env_file = "../../env.example"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

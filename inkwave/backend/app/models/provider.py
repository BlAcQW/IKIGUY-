"""
Provider configuration models for MongoDB.

Pydantic models for AI provider configurations (STT, TTS, LLM).
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CostInfo(BaseModel):
    """Provider cost information."""

    per_minute_usd: Optional[float] = None
    per_1k_chars_usd: Optional[float] = None
    per_query_usd: Optional[float] = None
    per_1k_tokens_usd: Optional[float] = None


class ProviderConfig(BaseModel):
    """
    Provider configuration document model.

    Stores configuration for STT, TTS, and LLM providers.
    """

    provider_type: str = Field(..., description="Provider type: stt, tts, llm")
    provider_id: str = Field(..., description="Provider ID: openai, google, elevenlabs, etc.")
    name: str  # Display name

    # Configuration
    api_key: Optional[str] = None  # Encrypted in production
    model: Optional[str] = None
    voice: Optional[str] = None  # For TTS
    config: Dict[str, Any] = Field(default_factory=dict)  # Additional config

    # Status
    enabled: bool = True
    is_default: bool = False
    status: str = "active"  # active, error, disabled

    # Cost information
    cost_info: CostInfo = Field(default_factory=CostInfo)

    # Usage tracking
    total_usage_count: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    last_used: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProviderConfigInDB(ProviderConfig):
    """
    Provider config model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

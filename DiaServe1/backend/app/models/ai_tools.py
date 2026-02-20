"""
AI Tools models for EstateFlow.

Pydantic models for AI content generation, analysis, and statistics.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GenerationType(str, Enum):
    LISTING = "listing"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    CONTRACT_ANALYSIS = "contract_analysis"


class GenerationRequest(BaseModel):
    generation_type: GenerationType
    prompt: str
    property_id: Optional[str] = None
    additional_context: Optional[str] = None


class GenerationResponse(BaseModel):
    id: str = ""
    organization_id: str = ""
    generation_type: GenerationType
    prompt: str
    result: str = ""
    property_id: Optional[str] = None
    tokens_used: Optional[int] = None
    model_used: str = "gpt-4"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = ""


class GenerationListResponse(BaseModel):
    generations: List[GenerationResponse]
    total: int
    limit: int
    offset: int


class AIStats(BaseModel):
    total_generations: int = 0
    generations_today: int = 0
    tokens_used_total: int = 0
    most_used_type: Optional[str] = None

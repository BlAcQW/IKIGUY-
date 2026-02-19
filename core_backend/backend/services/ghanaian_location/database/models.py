"""
Database models for Ghanaian Location Services

Defines Pydantic models for location data, STT corrections,
pronunciation guides, and user feedback.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class RelationshipType(str, Enum):
    """Types of relationships between locations"""
    ADJACENT = "adjacent"
    CONTAINS = "contains"
    ALIAS = "alias"
    NEARBY = "nearby"
    SIMILAR = "similar"


class LanguageContext(str, Enum):
    """Language contexts for pronunciation and STT"""
    ENGLISH = "english"
    TWI = "twi"
    GA = "ga"
    EWE = "ewe"
    HAUSA = "hausa"


class ToolContext(str, Enum):
    """Tool contexts for corrections and usage"""
    PREMIER_HEALTH = "premier_health"
    VAPI = "vapi"
    GENERAL = "general"
    N8N = "n8n"


class LocationResult(BaseModel):
    """Result from location processing"""
    original_input: str
    corrected_location: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    alternatives: List[str] = Field(default_factory=list)
    pronunciation_guide: Optional[str] = None
    geographic_context: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class GhanaianLocation(BaseModel):
    """Main location record with comprehensive metadata"""
    canonical_name: str = Field(..., description="Standard database name (uppercase)")
    display_name: str = Field(..., description="User-friendly display name")
    aliases: List[str] = Field(default_factory=list, description="Related area names")

    # Phonetic encoding for fuzzy matching
    phonetic_codes: Dict[str, str] = Field(
        default_factory=dict,
        description="Phonetic encodings (soundex, metaphone, custom)"
    )

    # Pronunciation assistance
    pronunciation: Dict[str, Any] = Field(
        default_factory=dict,
        description="IPA, SSML, speech rate, syllable breaks"
    )

    # Geographic information
    geographic: Dict[str, Any] = Field(
        default_factory=dict,
        description="Region, coordinates, proximity, landmarks"
    )

    # Context-specific metadata
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Healthcare coverage, provider counts, service types"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class STTCorrection(BaseModel):
    """STT mishearing corrections with learning capabilities"""
    misheard_input: str = Field(..., description="What STT incorrectly outputs")
    correct_location: str = Field(..., description="What it should be corrected to")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Correction confidence")
    phonetic_similarity: float = Field(..., ge=0.0, le=1.0, description="Phonetic match score")

    # Learning and usage tracking
    frequency: int = Field(default=1, description="How often this correction occurs")
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="User acceptance rate")
    language_context: LanguageContext = Field(default=LanguageContext.ENGLISH)

    # Verification and source
    verified: bool = Field(default=False, description="Human verified correction")
    source: str = Field(default="system", description="How this correction was learned")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    is_active: bool = Field(default=True)


class PronunciationGuide(BaseModel):
    """TTS pronunciation optimization guides"""
    location_name: str = Field(..., description="Location name to pronounce")
    language: LanguageContext = Field(default=LanguageContext.ENGLISH)

    # Pronunciation aids
    phonetic_spelling: Optional[str] = Field(None, description="Human-readable phonetic")
    ipa_notation: Optional[str] = Field(None, description="International Phonetic Alphabet")
    ssml_markup: Optional[str] = Field(None, description="SSML for TTS engines")

    # Alternative descriptions
    alternative_descriptions: List[str] = Field(
        default_factory=list,
        description="Alternative ways to describe the location"
    )

    # Speech optimization
    difficulty_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="0=easy to pronounce, 1=very difficult"
    )
    recommended_speech_rate: float = Field(default=1.0, description="Speech rate multiplier")
    syllable_breaks: List[str] = Field(default_factory=list)

    # Usage context
    usage_context: List[ToolContext] = Field(default_factory=list)
    effectiveness_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How well this guide works"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)


class LocationRelationship(BaseModel):
    """Relationships between locations for context and proximity"""
    primary_location: str = Field(..., description="Primary location name")
    related_location: str = Field(..., description="Related location name")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")

    # Geographic data
    distance_km: Optional[float] = Field(None, description="Distance in kilometers")
    travel_time_minutes: Optional[int] = Field(None, description="Estimated travel time")

    # Relationship strength
    relationship_strength: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Relevance/strength of the relationship"
    )
    bidirectional: bool = Field(default=True, description="Relationship works both ways")

    # Context
    context_notes: Optional[str] = Field(None, description="Additional context")
    usage_frequency: int = Field(default=0, description="How often this relationship is used")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)


class UserCorrection(BaseModel):
    """User feedback and corrections for continuous learning"""
    user_input: str = Field(..., description="Original user input")
    system_interpretation: str = Field(..., description="What system thought it was")
    user_correction: Optional[str] = Field(None, description="What user said it should be")

    # Confidence tracking
    confidence_before: float = Field(..., ge=0.0, le=1.0)
    confidence_after: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Context
    session_id: Optional[str] = Field(None, description="User session identifier")
    tool_context: ToolContext = Field(..., description="Which tool/service was being used")
    geographic_hint: Optional[str] = Field(None, description="Geographic context provided")

    # Processing
    applied_to_training: bool = Field(default=False, description="Used to improve system")
    correction_type: str = Field(default="location", description="Type of correction")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = Field(None)
    ip_address: Optional[str] = Field(None)


class LocationAnalytics(BaseModel):
    """Analytics for location processing performance"""
    location_name: str
    total_queries: int = Field(default=0)
    successful_matches: int = Field(default=0)
    user_corrections: int = Field(default=0)
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Performance metrics
    average_processing_time_ms: float = Field(default=0.0)
    phonetic_match_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    pronunciation_clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Context breakdown
    context_usage: Dict[str, int] = Field(default_factory=dict)
    language_distribution: Dict[str, int] = Field(default_factory=dict)

    # Temporal data
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    reporting_period_start: datetime
    reporting_period_end: datetime
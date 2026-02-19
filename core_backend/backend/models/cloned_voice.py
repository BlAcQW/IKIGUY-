"""
MongoDB model for cloned voices metadata

Stores metadata about voice clones created from reference audio files.
Reference audio files are stored on disk, while metadata is in MongoDB.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId compatible with Pydantic v2"""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ], serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
        raise ValueError("Invalid ObjectId")


class ClonedVoiceModel(BaseModel):
    """Pydantic model for cloned voice metadata"""

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    provider: str = Field(..., description="TTS provider (coqui_xtts, openvoice, f5tts, styletts2)")
    reference_audio_path: str = Field(..., description="Path to reference audio file on disk")
    reference_audio_size: int = Field(..., description="Size of reference audio in bytes")
    cloned_at: str = Field(..., description="ISO format timestamp of cloning")
    language: str = Field(default="en", description="Voice language")
    gender: str = Field(default="neutral", description="Voice gender")
    accent: str = Field(default="neutral", description="Voice accent")
    description: str = Field(default="", description="Voice description")
    capabilities: List[str] = Field(default_factory=list, description="Voice capabilities")
    status: str = Field(default="pending", description="Status: pending, processing, completed, failed")
    error_message: Optional[str] = Field(None, description="Error message if cloning failed")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration"""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "voice_id": "abc123def456",
                "name": "Nana Aba",
                "provider": "coqui_xtts",
                "reference_audio_path": "/opt/kasaai/apps/voice-lab/voices/nana_aba.wav",
                "reference_audio_size": 6400000,
                "cloned_at": "2025-10-20T10:30:00",
                "language": "en",
                "gender": "female",
                "accent": "Ghanaian",
                "description": "Professional female Ghanaian voice",
                "capabilities": ["voice_cloning", "real_time"],
                "status": "completed"
            }
        }


# MongoDB Collection name
CLONED_VOICES_COLLECTION = "cloned_voices"


# Indexes to create on the collection
CLONED_VOICES_INDEXES = [
    [("voice_id", 1)],  # Unique index on voice_id
    [("provider", 1)],  # Index for filtering by provider
    [("status", 1)],    # Index for filtering by status
    [("gender", 1)],    # Index for filtering by gender
    [("language", 1)],  # Index for filtering by language
    [("created_at", -1)],  # Index for sorting by creation date
]

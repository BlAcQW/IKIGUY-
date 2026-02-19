"""
MongoDB model for voice library metadata

Stores metadata about voice files in the library for reference voice cloning.
Voice files are stored on disk, while metadata is in MongoDB for dynamic management.
"""

from typing import Optional, List, Dict, Any
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


class LibraryVoiceModel(BaseModel):
    """Pydantic model for library voice metadata"""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    file_path: str = Field(..., description="Path to audio file on disk")
    file_size: int = Field(..., description="Size of audio file in bytes")
    file_size_display: str = Field(..., description="Human-readable file size (e.g., '6.1MB')")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate (Hz)")

    # Voice characteristics
    gender: str = Field(default="neutral", description="Voice gender (male, female, neutral)")
    accent: str = Field(default="neutral", description="Voice accent/dialect")
    language: str = Field(default="en", description="Primary language")
    description: str = Field(default="", description="Voice description")

    # Metadata
    is_active: bool = Field(default=True, description="Whether voice is active/available")
    is_featured: bool = Field(default=False, description="Whether voice is featured in UI")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    # Upload/tracking
    uploaded_by: Optional[str] = Field(None, description="User ID who uploaded the voice")
    upload_source: str = Field(default="manual", description="Source of upload (manual, batch, migration)")

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
                "voice_id": "nana_aba",
                "name": "Nana Aba",
                "file_path": "/opt/kasaai/apps/voice-lab/voices/nana_aba.wav",
                "file_size": 6400000,
                "file_size_display": "6.1MB",
                "duration": 42.5,
                "sample_rate": 48000,
                "gender": "female",
                "accent": "Ghanaian",
                "language": "en",
                "description": "Professional female Ghanaian voice",
                "is_active": True,
                "is_featured": True,
                "tags": ["ghanaian", "professional", "female"],
                "uploaded_by": "admin",
                "upload_source": "manual"
            }
        }


# MongoDB Collection name
LIBRARY_VOICES_COLLECTION = "library_voices"


# Indexes to create on the collection
LIBRARY_VOICES_INDEXES = [
    [("voice_id", 1)],  # Unique index on voice_id
    [("name", 1)],  # Index for searching by name
    [("gender", 1)],  # Index for filtering by gender
    [("language", 1)],  # Index for filtering by language
    [("accent", 1)],  # Index for filtering by accent
    [("is_active", 1)],  # Index for filtering active voices
    [("is_featured", 1)],  # Index for filtering featured voices
    [("tags", 1)],  # Index for tag-based filtering
    [("created_at", -1)],  # Index for sorting by creation date
]

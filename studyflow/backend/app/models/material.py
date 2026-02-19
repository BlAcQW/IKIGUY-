"""
Study material models for StudyFlow.

Tracks uploaded materials, processing status, and metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class MaterialType(str, Enum):
    """Type of study material."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class ProcessingStatus(str, Enum):
    """Material processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StudyMaterial(BaseModel):
    """
    Study material model.

    Tracks uploaded educational content and its processing status.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        school_id: School ID (optional)
        title: Material title
        description: Material description
        file_name: Original file name
        file_path: Path to stored file
        file_size: File size in bytes
        file_type: Type of material
        subject: Subject area
        topics: List of topics covered
        grade: Grade level
        uploaded_by: User ID who uploaded
        status: Processing status
        chunks_count: Number of chunks extracted
        embedding_collection: RAG collection name
        metadata: Additional material data
        created_at: Upload timestamp
        updated_at: Last update timestamp
        processed_at: Processing completion timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    school_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    file_size: int
    file_type: MaterialType

    subject: str
    topics: List[str] = Field(default_factory=list)
    grade: Optional[int] = None

    uploaded_by: str  # User ID
    status: ProcessingStatus = ProcessingStatus.PENDING

    chunks_count: int = 0
    embedding_collection: Optional[str] = None

    metadata: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class MaterialCreate(BaseModel):
    """
    Schema for creating a new material.

    Attributes:
        organization_id: Organization ID for multi-tenancy
        school_id: School ID (optional)
        title: Material title
        description: Material description
        subject: Subject area
        topics: Topics covered
        grade: Grade level
    """
    organization_id: str
    school_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    subject: str
    topics: List[str] = Field(default_factory=list)
    grade: Optional[int] = None
    metadata: dict = Field(default_factory=dict)


class MaterialUpdate(BaseModel):
    """
    Schema for updating material information.

    All fields are optional for partial updates.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    topics: Optional[List[str]] = None
    grade: Optional[int] = None
    status: Optional[ProcessingStatus] = None
    chunks_count: Optional[int] = None
    embedding_collection: Optional[str] = None
    metadata: Optional[dict] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MaterialResponse(BaseModel):
    """
    Material response model for API responses.
    """
    id: str
    organization_id: str
    school_id: Optional[str]
    title: str
    description: Optional[str]
    file_name: str
    file_size: int
    file_type: MaterialType
    subject: str
    topics: List[str]
    grade: Optional[int]
    uploaded_by: str
    status: ProcessingStatus
    chunks_count: int
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MaterialStats(BaseModel):
    """
    Statistics about uploaded materials.

    Used for admin dashboard and analytics.
    """
    total_materials: int
    by_subject: Dict[str, int] = Field(default_factory=dict)
    by_grade: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    total_size_mb: float
    total_chunks: int
    period_start: datetime
    period_end: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

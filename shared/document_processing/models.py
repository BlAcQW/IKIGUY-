"""
Base models for document processing across KasaAI applications.

These models provide a common foundation for:
- StudyFlow (study materials)
- InkWave (books)
- ChurchFlow (sermons, documents)
- Any other app that processes documents

Author: KasaAI Team
Date: 2025-11-28
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Processing status for documents/materials."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REPROCESSING = "reprocessing"


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    EPUB = "epub"
    HTML = "html"
    MARKDOWN = "md"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    UNKNOWN = "unknown"

    @classmethod
    def from_filename(cls, filename: str) -> "DocumentType":
        """
        Detect document type from filename extension.

        Args:
            filename: Original filename

        Returns:
            DocumentType enum
        """
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        type_map = {
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "doc": cls.DOCX,
            "txt": cls.TXT,
            "epub": cls.EPUB,
            "html": cls.HTML,
            "htm": cls.HTML,
            "md": cls.MARKDOWN,
            "markdown": cls.MARKDOWN,
            "jpg": cls.IMAGE,
            "jpeg": cls.IMAGE,
            "png": cls.IMAGE,
            "gif": cls.IMAGE,
            "webp": cls.IMAGE,
            "mp4": cls.VIDEO,
            "avi": cls.VIDEO,
            "mov": cls.VIDEO,
            "webm": cls.VIDEO,
            "mp3": cls.AUDIO,
            "wav": cls.AUDIO,
            "ogg": cls.AUDIO,
            "flac": cls.AUDIO,
        }
        return type_map.get(ext, cls.UNKNOWN)


class DocumentChunk(BaseModel):
    """A chunk of processed document with metadata."""

    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    word_count: int
    char_start: int = 0
    char_end: int = 0
    page_number: Optional[int] = None
    chapter_id: Optional[str] = None
    vector_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BaseDocument(BaseModel):
    """
    Base document model for all KasaAI applications.

    Extend this for app-specific documents (StudyMaterial, Book, etc.)
    """

    id: Optional[str] = None
    organization_id: Optional[str] = None
    title: str
    description: Optional[str] = None

    # File information
    file_name: str
    file_path: str
    file_size: int
    file_type: DocumentType = DocumentType.UNKNOWN

    # Processing state
    status: ProcessingStatus = ProcessingStatus.PENDING
    chunks_count: int = 0
    embedding_collection: Optional[str] = None
    error_message: Optional[str] = None

    # Ownership
    uploaded_by: str

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    topics: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class BaseDocumentCreate(BaseModel):
    """Base model for creating documents."""

    organization_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseDocumentUpdate(BaseModel):
    """Base model for updating documents."""

    title: Optional[str] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessingResult(BaseModel):
    """Result of document processing."""

    success: bool
    document_id: str
    chunks_count: int = 0
    embedding_collection: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Extracted content info
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    topics_extracted: List[str] = Field(default_factory=list)


class EmbeddingMetadata(BaseModel):
    """Metadata to include with embeddings for filtering."""

    organization_id: Optional[str] = None
    document_id: str
    chunk_index: int
    document_type: str
    uploaded_by: str
    topics: List[str] = Field(default_factory=list)
    custom: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for pgvector metadata."""
        data = {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "document_type": self.document_type,
            "uploaded_by": self.uploaded_by,
            "topics": self.topics,
        }
        if self.organization_id:
            data["organization_id"] = self.organization_id
        data.update(self.custom)
        return data


class QueryFilter(BaseModel):
    """Filter for RAG queries with organization scoping."""

    organization_id: Optional[str] = None
    document_id: Optional[str] = None
    document_type: Optional[str] = None
    topics: Optional[List[str]] = None
    uploaded_by: Optional[str] = None
    custom: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to filter dictionary for pgvector."""
        filters = {}
        if self.organization_id:
            filters["organization_id"] = self.organization_id
        if self.document_id:
            filters["document_id"] = self.document_id
        if self.document_type:
            filters["document_type"] = self.document_type
        if self.uploaded_by:
            filters["uploaded_by"] = self.uploaded_by
        filters.update(self.custom)
        return filters if filters else None

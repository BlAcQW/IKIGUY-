"""
Book models for MongoDB.

Pydantic models for book documents and related data.
"""

from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class BookVisibility(str, Enum):
    """Book visibility states."""

    DRAFT = "draft"  # Incomplete/processing, only uploader can see
    UNLISTED = "unlisted"  # Anyone with link, not in discovery
    PRIVATE = "private"  # Library/invitation only, not in discovery
    PUBLIC = "public"  # In "All Books" discovery, anyone can add to library


class BookMetadata(BaseModel):
    """Book metadata."""

    summary: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)  # AI-extracted topics
    characters: List[str] = Field(default_factory=list)
    page_count: int = 0
    word_count: int = 0
    estimated_reading_time_minutes: int = 0
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced
    genre: List[str] = Field(default_factory=list)
    language: str = "en"


class BookChapter(BaseModel):
    """Book chapter information."""

    id: str  # Unique chapter identifier (e.g., "ch_1", "ch_2")
    title: str
    order: int  # 1-based order for display/navigation
    start_chunk_id: int
    end_chunk_id: int
    word_count: int
    duration: Optional[int] = None  # Duration in seconds (calculated from audio)
    start_time: Optional[int] = None  # Start time in seconds for audio navigation


class BookStorage(BaseModel):
    """Book file storage metadata."""

    storage_type: str = "local"  # local, hetzner
    pdf_path: Optional[str] = None  # Path/URL to PDF file
    pdf_url: Optional[str] = None  # Public URL for PDF
    pdf_size: int = 0  # File size in bytes
    pdf_checksum: Optional[str] = None  # MD5 checksum
    cover_path: Optional[str] = None  # Path/URL to cover image
    cover_url: Optional[str] = None  # Public URL for cover


class Book(BaseModel):
    """
    Book document model.

    Represents a book in the MongoDB books collection.
    """

    book_id: str = Field(..., description="Unique book identifier")
    title: str
    author: str
    author_id: Optional[str] = Field(None, description="Author user_id (if linked to author account)")
    isbn: Optional[str] = None
    cover_url: Optional[str] = None  # Book cover image (public URL)
    author_image_url: Optional[str] = None  # Author photo (dynamic URL from web search)
    pdf_url: Optional[str] = None  # Public URL to PDF (for backward compat)

    # Cloud storage metadata
    storage: BookStorage = Field(default_factory=BookStorage)

    processed: bool = False
    processing_status: str = "pending"  # pending, processing, ready, error
    processing_error: Optional[str] = None
    processing_stage: str = ""  # Current stage: extracting, chunking, embedding, etc.
    processing_progress: int = 0  # 0-100 percentage
    processing_message: str = ""  # Human-readable status message

    metadata: BookMetadata = Field(default_factory=BookMetadata)
    chapters: List[BookChapter] = Field(default_factory=list)

    uploaded_by: str  # user_id
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Visibility Control (Author-controlled)
    visibility: str = Field(
        default="public",
        description="Book visibility state: draft, unlisted, private, or public"
    )
    visibility_changed_at: Optional[datetime] = Field(
        None,
        description="When visibility was last changed"
    )
    visibility_changed_by: Optional[str] = Field(
        None,
        description="User ID who changed visibility"
    )

    # Admin Moderation (soft delete/hide)
    is_hidden: bool = Field(
        default=False,
        description="Whether book is hidden by admin (visible to uploader only)"
    )
    hidden_by: Optional[str] = Field(
        None,
        description="Admin user_id who hid the book"
    )
    hidden_by_email: Optional[str] = Field(
        None,
        description="Admin email who hid the book"
    )
    hidden_at: Optional[datetime] = Field(
        None,
        description="When book was hidden"
    )
    hidden_reason: Optional[str] = Field(
        None,
        description="Reason for hiding the book"
    )

    # Soft Delete
    is_deleted: bool = Field(
        default=False,
        description="Whether book is soft-deleted (can be restored by admin)"
    )
    deleted_by: Optional[str] = Field(
        None,
        description="Admin user_id who deleted the book"
    )
    deleted_by_email: Optional[str] = Field(
        None,
        description="Admin email who deleted the book"
    )
    deleted_at: Optional[datetime] = Field(
        None,
        description="When book was deleted"
    )
    deletion_reason: Optional[str] = Field(
        None,
        description="Reason for deleting the book"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
        populate_by_name = True


class ContentType(str, Enum):
    """Content type classification for book chunks."""

    NARRATIVE = "narrative"           # Main story/content - always narrated
    CHAPTER_TITLE = "chapter_title"   # Chapter headers - read once, cleanly
    SECTION_BREAK = "section_break"   # Scene breaks (***) - silent pause
    FRONT_MATTER = "front_matter"     # Title page, dedication
    PREFACE = "preface"               # Foreword, preface, editor notes
    FOOTNOTE = "footnote"             # Footnotes and endnotes
    APPENDIX = "appendix"             # Appendix material
    COPYRIGHT = "copyright"           # Copyright notices, legal text
    TOC = "toc"                       # Table of contents
    METADATA = "metadata"             # ISBN, publisher info, edition notes
    REFERENCE = "reference"           # Bibliography, references, index
    PUBLISHER_INSTRUCTIONS = "publisher_instructions"  # Galley/review instructions


class BookChunk(BaseModel):
    """
    Book chunk document model.

    Represents a text chunk from a book with optional audio narration.
    Includes content classification for professional narration filtering.
    """

    book_id: str
    chunk_id: str  # Unique chunk identifier
    chunk_index: int  # Sequential order
    text: str  # Original text
    text_optimized: Optional[str] = None  # SSML-enhanced for TTS
    chapter_id: Optional[str] = None  # Reference to BookChapter.id (e.g., "ch_1")
    chapter_title: Optional[str] = None  # Denormalized chapter title for display
    vector_id: Optional[str] = None  # Reference to pgvector entry
    word_count: int = 0

    # Content Classification (Professional Narration)
    content_type: str = Field(
        default="narrative",
        description="Content type: narrative, chapter_title, copyright, toc, etc."
    )
    narratable: bool = Field(
        default=True,
        description="Whether this chunk should be narrated (audio generated)"
    )
    narration_text: Optional[str] = Field(
        default=None,
        description="Cleaned text for TTS narration (may differ from original)"
    )
    skip_reason: Optional[str] = Field(
        default=None,
        description="Reason for skipping narration (if narratable=False)"
    )
    is_chapter_start: bool = Field(
        default=False,
        description="True if this chunk starts a new chapter"
    )
    classification_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence of content classification (0.0-1.0)"
    )

    # Audio narration fields
    audio_url: Optional[str] = None  # URL to audio file
    audio_duration: Optional[float] = None  # Duration in seconds
    audio_provider: Optional[str] = None  # TTS provider used
    audio_voice_id: Optional[str] = None  # Voice identifier
    audio_speed: Optional[float] = None  # Playback speed
    audio_language: Optional[str] = None  # Language code
    audio_cost: Optional[float] = None  # Generation cost
    audio_generated_at: Optional[datetime] = None  # When audio was generated

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookInDB(Book):
    """
    Book model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }

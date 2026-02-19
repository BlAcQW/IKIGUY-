"""
Book schemas.

Request/response models for book-related endpoints.
"""

from typing import Optional, Union, List
from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Book chapter."""

    id: str
    title: str
    duration: int = Field(..., description="Duration in minutes")
    order: int = Field(..., ge=1)
    start_time: Optional[int] = Field(None, description="Start time in seconds")


class BookBase(BaseModel):
    """Base book model."""

    title: str
    author: str
    description: Optional[str] = None
    genre: Optional[Union[str, List[str]]] = None  # Accept both string and list
    duration: int = Field(..., description="Total duration in minutes")
    cover_url: Optional[str] = None  # Book cover image (dynamic URL)
    author_image_url: Optional[str] = None  # Author photo (dynamic URL from web search)
    background_url: Optional[str] = None


class BookListItem(BookBase):
    """Book in list view."""

    id: str
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    visibility: Optional[str] = Field(None, description="Book visibility state (draft, unlisted, private, public)")
    visibility_badge: Optional[str] = Field(None, description="Visibility badge to display (e.g., 'Hidden by Admin')")


class BookDetail(BookBase):
    """Detailed book view."""

    id: str
    chapters: list[Chapter] = Field(default_factory=list)
    audio_url: Optional[str] = None  # Pre-generated audio URL (usually None - audio generated on demand)
    pdf_url: Optional[str] = None  # PDF URL for reading/download
    total_chunks: int = Field(default=0, description="Number of text chunks for TTS")
    content_start_chunk: int = Field(default=0, description="First chunk with actual content (skips TOC/copyright)")
    progress: Optional[int] = Field(None, ge=0, le=100)
    last_position: Optional[int] = Field(None, description="Last playback position in seconds")
    visibility: Optional[str] = Field(None, description="Book visibility state (draft, unlisted, private, public)")
    visibility_badge: Optional[str] = Field(None, description="Visibility badge to display (e.g., 'Hidden by Admin')")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "book_123",
                "title": "The Midnight Library",
                "author": "Matt Haig",
                "description": "A novel about life, death, and everything in between...",
                "genre": "Fiction",
                "duration": 240,
                "cover_url": "https://example.com/cover.jpg",
                "background_url": "https://example.com/bg.jpg",
                "chapters": [
                    {
                        "id": "ch1",
                        "title": "Chapter 1",
                        "duration": 15,
                        "order": 1,
                        "start_time": 0
                    }
                ],
                "audio_url": "https://storage.example.com/audio/book_123.mp3",
                "progress": 45,
                "last_position": 3600
            }
        }


class BookListResponse(BaseModel):
    """Books list response."""

    books: list[BookListItem] = Field(default_factory=list)
    total: int
    page: int = 1
    per_page: int = 20

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "books": [],
                "total": 10,
                "page": 1,
                "per_page": 20
            }
        }


class ReadingSessionRequest(BaseModel):
    """Start/update reading session."""

    book_id: str
    chapter_id: Optional[str] = None
    position: Optional[int] = Field(None, description="Playback position in seconds")


class ReadingSessionResponse(BaseModel):
    """Reading session response."""

    book: BookDetail
    session_id: str
    started_at: str

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "book": {},
                "session_id": "session_123",
                "started_at": "2025-10-24T12:00:00Z"
            }
        }


class AuthorImageSearchRequest(BaseModel):
    """Request for author image search."""

    author_name: str = Field(..., description="Name of the author to search for")
    context: Optional[str] = Field(None, description="Additional context (e.g., book author, religious leader)")
    max_results: int = Field(5, ge=1, le=10, description="Maximum number of images to return")


class AuthorImageSearchResponse(BaseModel):
    """Response from author image search."""

    query: str = Field(..., description="Search query used")
    image_urls: List[str] = Field(default_factory=list, description="Direct image URLs found")
    source_pages: List[str] = Field(default_factory=list, description="Source page URLs")
    thumbnail_urls: List[str] = Field(default_factory=list, description="Thumbnail URLs")
    primary_image_url: Optional[str] = Field(None, description="Best/primary image URL")
    status: str = Field("success", description="Search status (success, not_found, error)")
    message: Optional[str] = Field(None, description="Additional message")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "query": "Nicholas Duncan-Williams",
                "image_urls": [
                    "https://example.com/author1.jpg",
                    "https://example.com/author2.jpg"
                ],
                "source_pages": [
                    "https://amazon.com/author/nicholas-duncan-williams",
                    "https://wikipedia.org/wiki/Nicholas_Duncan-Williams"
                ],
                "thumbnail_urls": [
                    "https://example.com/author1_thumb.jpg",
                    "https://example.com/author2_thumb.jpg"
                ],
                "primary_image_url": "https://example.com/author1.jpg",
                "status": "success",
                "message": None
            }
        }

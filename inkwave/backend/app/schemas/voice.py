"""
Voice Q&A schemas.

Request/response models for voice interaction endpoints.

Note:
    Cost structure is transitioning from credits to USD:
    - STT and RAG still use credits (stt_credits, rag_credits)
    - TTS uses USD with automatic wallet billing (tts_usd)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VoiceQuestionRequest(BaseModel):
    """Voice question request (with transcript)."""

    book_id: str = Field(..., description="Book ID to query")
    transcript: str = Field(..., min_length=1, max_length=500, description="Question text")


class VoiceQAResponse(BaseModel):
    """Voice Q&A response."""

    question: str = Field(..., description="User's question")
    answer: str = Field(..., description="AI-generated answer")
    audio_url: Optional[str] = Field(None, description="TTS audio URL")
    audio_format: Optional[str] = Field(None, description="Output audio format (mp3, ogg, wav, flac, m4a)")
    costs: dict = Field(..., description="Cost breakdown")
    transaction_ids: Optional[dict] = Field(None, description="Transaction IDs for billing")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "question": "What is the main theme of the book?",
                "answer": "The main theme explores the concept of...",
                "audio_url": "https://storage.example.com/audio/123.mp3",
                "audio_format": "mp3",
                "costs": {
                    "stt_credits": 60,
                    "rag_credits": 30,
                    "tts_usd": 0.0075,
                    "total_usd": 0.0075
                },
                "transaction_ids": {
                    "tts": "txn_abc123"
                },
                "timestamp": "2025-10-24T12:00:00Z"
            }
        }


class TranscribeRequest(BaseModel):
    """Audio transcription request (handled as multipart/form-data)."""

    pass  # File will be handled separately


class TranscribeResponse(BaseModel):
    """Audio transcription response."""

    transcript: str = Field(..., description="Transcribed text")
    duration_seconds: float = Field(..., description="Audio duration")
    cost_credits: int = Field(..., description="Credits spent")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "transcript": "What happens in chapter 3?",
                "duration_seconds": 5.2,
                "cost_credits": 60
            }
        }


class ConversationItem(BaseModel):
    """Single conversation item."""

    id: str
    question: str
    answer: str
    audio_url: Optional[str] = None
    timestamp: datetime

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "conv_123",
                "question": "Who is the main character?",
                "answer": "The main character is...",
                "audio_url": "https://storage.example.com/audio/123.mp3",
                "timestamp": "2025-10-24T12:00:00Z"
            }
        }


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""

    conversations: list[ConversationItem] = Field(default_factory=list)
    total: int = Field(..., description="Total count")
    book_id: str = Field(..., description="Book ID")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "conversations": [],
                "total": 5,
                "book_id": "book_123"
            }
        }

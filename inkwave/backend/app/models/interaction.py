"""
Interaction models for MongoDB.

Pydantic models for Q&A interactions and messages.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message in an interaction conversation."""

    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    audio_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: Optional[int] = None
    cost_cents: Optional[int] = None


class Interaction(BaseModel):
    """
    Interaction model.

    Represents a Q&A conversation during a reading session.
    """

    interaction_id: str = Field(..., description="Unique interaction identifier")
    session_id: str = Field(..., description="Reading session ID")
    user_id: str = Field(..., description="User ID from Supabase")
    book_id: str = Field(..., description="Book being discussed")

    # Context
    chunk_context: List[int] = Field(
        default_factory=list,
        description="Chunk indices providing context"
    )

    # Conversation
    messages: List[Message] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True


class InteractionInDB(Interaction):
    """
    Interaction model with MongoDB _id.

    Used for documents retrieved from database.
    """

    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InteractionCreate(BaseModel):
    """
    Model for creating a new interaction.
    """

    session_id: str
    book_id: str
    chunk_context: Optional[List[int]] = None


class MessageCreate(BaseModel):
    """
    Model for sending a message in an interaction.
    """

    content: str = Field(..., description="User question or message")

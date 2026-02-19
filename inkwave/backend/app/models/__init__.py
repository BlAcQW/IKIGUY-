"""
MongoDB models.

Pydantic models for MongoDB documents.
"""

from app.models.book import Book, BookChunk, BookMetadata, BookChapter, BookInDB
from app.models.user import User, UserProfile, InteractionPreferences, UserInDB
from app.models.provider import ProviderConfig, ProviderConfigInDB, CostInfo
from app.models.session import ReadingSession, ReadingSessionInDB, ReadingSessionUpdate, Bookmark
from app.models.interaction import Interaction, InteractionInDB, InteractionCreate, MessageCreate, Message

__all__ = [
    "Book",
    "BookChunk",
    "BookMetadata",
    "BookChapter",
    "BookInDB",
    "User",
    "UserProfile",
    "InteractionPreferences",
    "UserInDB",
    "ProviderConfig",
    "ProviderConfigInDB",
    "CostInfo",
    "ReadingSession",
    "ReadingSessionInDB",
    "ReadingSessionUpdate",
    "Bookmark",
    "Interaction",
    "InteractionInDB",
    "InteractionCreate",
    "MessageCreate",
    "Message",
]

"""
Reading session service.

Manages reading sessions, progress tracking, and bookmarks.
"""

from typing import Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from app.models.session import (
    ReadingSession,
    ReadingSessionInDB,
    ReadingSessionUpdate,
    Bookmark
)
from app.models.book import BookChunk


class ReadingService:
    """Service for managing reading sessions."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize reading service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.sessions_collection = db.reading_sessions
        self.chunks_collection = db.book_chunks

    async def create_session(
        self,
        user_id: str,
        book_id: str
    ) -> ReadingSessionInDB:
        """
        Create a new reading session or return existing active session.

        Args:
            user_id: User ID from Supabase
            book_id: Book ID

        Returns:
            ReadingSessionInDB: Created or existing session
        """
        # Check for existing active session
        existing = await self.sessions_collection.find_one({
            "user_id": user_id,
            "book_id": book_id,
            "completed": False
        })

        if existing:
            existing["_id"] = str(existing["_id"])
            # Backfill book metadata if missing (for legacy sessions)
            if not existing.get("book_title"):
                book = await self.db.books.find_one({"book_id": book_id})
                if book:
                    await self.sessions_collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {
                            "book_title": book.get("title", "Unknown"),
                            "book_author": book.get("author", "Unknown")
                        }}
                    )
                    existing["book_title"] = book.get("title", "Unknown")
                    existing["book_author"] = book.get("author", "Unknown")
            return ReadingSessionInDB(**existing)

        # Fetch book metadata for caching
        book = await self.db.books.find_one({"book_id": book_id})
        book_title = book.get("title", "Unknown") if book else "Unknown"
        book_author = book.get("author", "Unknown") if book else "Unknown"

        # Create new session with cached book metadata
        session = ReadingSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            book_id=book_id,
            book_title=book_title,
            book_author=book_author
        )

        result = await self.sessions_collection.insert_one(
            session.model_dump(by_alias=True, exclude={"id"})
        )

        session_dict = session.model_dump(by_alias=True, exclude={"id"})
        session_dict["_id"] = str(result.inserted_id)

        return ReadingSessionInDB(**session_dict)

    async def get_session(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[ReadingSessionInDB]:
        """
        Get reading session by ID.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)

        Returns:
            ReadingSessionInDB or None if not found
        """
        session = await self.sessions_collection.find_one({
            "session_id": session_id,
            "user_id": user_id
        })

        if not session:
            return None

        # Convert ObjectId to string
        session["_id"] = str(session["_id"])
        return ReadingSessionInDB(**session)

    async def update_progress(
        self,
        session_id: str,
        user_id: str,
        update: ReadingSessionUpdate
    ) -> Optional[ReadingSessionInDB]:
        """
        Update reading progress.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            update: Progress update data

        Returns:
            Updated ReadingSessionInDB or None
        """
        update_data = update.model_dump(exclude_none=True)
        update_data["last_accessed"] = datetime.now(timezone.utc)
        update_data["updated_at"] = datetime.now(timezone.utc)

        result = await self.sessions_collection.find_one_and_update(
            {"session_id": session_id, "user_id": user_id},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return ReadingSessionInDB(**result)

    async def add_bookmark(
        self,
        session_id: str,
        user_id: str,
        chunk_index: int,
        position_seconds: float = 0.0,
        note: Optional[str] = None,
        chapter_title: Optional[str] = None
    ) -> Optional[ReadingSessionInDB]:
        """
        Add a bookmark to the session.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            chunk_index: Chunk index to bookmark
            position_seconds: Position in audio (seconds)
            note: Optional note
            chapter_title: Optional chapter title

        Returns:
            Updated ReadingSessionInDB or None
        """
        bookmark = Bookmark(
            chunk_index=chunk_index,
            position_seconds=position_seconds,
            note=note,
            chapter_title=chapter_title
        )

        result = await self.sessions_collection.find_one_and_update(
            {"session_id": session_id, "user_id": user_id},
            {
                "$push": {"bookmarks": bookmark.model_dump()},
                "$set": {"last_accessed": datetime.now(timezone.utc)}
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return ReadingSessionInDB(**result)

    async def update_bookmark(
        self,
        session_id: str,
        user_id: str,
        bookmark_id: str,
        note: Optional[str] = None
    ) -> Optional[ReadingSessionInDB]:
        """
        Update a bookmark's note.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            bookmark_id: Bookmark ID
            note: New note

        Returns:
            Updated ReadingSessionInDB or None
        """
        result = await self.sessions_collection.find_one_and_update(
            {
                "session_id": session_id,
                "user_id": user_id,
                "bookmarks.bookmark_id": bookmark_id
            },
            {
                "$set": {
                    "bookmarks.$.note": note,
                    "last_accessed": datetime.now(timezone.utc)
                }
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return ReadingSessionInDB(**result)

    async def delete_bookmark(
        self,
        session_id: str,
        user_id: str,
        bookmark_id: str
    ) -> Optional[ReadingSessionInDB]:
        """
        Delete a bookmark from the session.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            bookmark_id: Bookmark ID

        Returns:
            Updated ReadingSessionInDB or None
        """
        result = await self.sessions_collection.find_one_and_update(
            {"session_id": session_id, "user_id": user_id},
            {
                "$pull": {"bookmarks": {"bookmark_id": bookmark_id}},
                "$set": {"last_accessed": datetime.now(timezone.utc)}
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return ReadingSessionInDB(**result)

    async def get_chunk(
        self,
        book_id: str,
        chunk_index: int
    ) -> Optional[BookChunk]:
        """
        Get a specific book chunk.

        Args:
            book_id: Book ID
            chunk_index: Chunk index

        Returns:
            BookChunk or None
        """
        chunk = await self.chunks_collection.find_one({
            "book_id": book_id,
            "chunk_index": chunk_index
        })

        if not chunk:
            return None

        return BookChunk(**chunk)

    async def get_next_chunk(
        self,
        book_id: str,
        current_chunk_index: int
    ) -> Optional[BookChunk]:
        """
        Get the next chunk in sequence.

        Args:
            book_id: Book ID
            current_chunk_index: Current chunk index

        Returns:
            Next BookChunk or None if at end
        """
        return await self.get_chunk(book_id, current_chunk_index + 1)

    async def get_previous_chunk(
        self,
        book_id: str,
        current_chunk_index: int
    ) -> Optional[BookChunk]:
        """
        Get the previous chunk in sequence.

        Args:
            book_id: Book ID
            current_chunk_index: Current chunk index

        Returns:
            Previous BookChunk or None if at beginning
        """
        if current_chunk_index <= 0:
            return None

        return await self.get_chunk(book_id, current_chunk_index - 1)

    async def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = False
    ) -> List[ReadingSessionInDB]:
        """
        Get all reading sessions for a user.

        Args:
            user_id: User ID
            active_only: Only return non-completed sessions

        Returns:
            List of ReadingSessionInDB
        """
        query = {"user_id": user_id}
        if active_only:
            query["completed"] = False

        sessions = await self.sessions_collection.find(query).to_list(length=100)

        # Convert ObjectId to string for each session
        for session in sessions:
            session["_id"] = str(session["_id"])

        return [ReadingSessionInDB(**session) for session in sessions]

    async def mark_completed(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[ReadingSessionInDB]:
        """
        Mark a reading session as completed.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)

        Returns:
            Updated ReadingSessionInDB or None
        """
        result = await self.sessions_collection.find_one_and_update(
            {"session_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "completed": True,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return ReadingSessionInDB(**result)

"""
Unit tests for Reading Service.

Tests reading sessions, progress tracking, and bookmarks.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.reading_service import ReadingService
from app.models.session import Bookmark, ReadingSession, ReadingSessionInDB


class TestReadingService:
    """Test cases for ReadingService."""

    @pytest.fixture
    def mock_db(self):
        """
        Create mock database.

        Returns:
            MagicMock: Mock database instance
        """
        db = MagicMock()
        db.reading_sessions = MagicMock()
        db.book_chunks = MagicMock()
        return db

    @pytest.fixture
    def reading_service(self, mock_db):
        """
        Create ReadingService with mock database.

        Args:
            mock_db: Mock database fixture

        Returns:
            ReadingService: Service instance
        """
        return ReadingService(mock_db)

    @pytest.fixture
    def sample_session_data(self):
        """
        Sample reading session data.

        Returns:
            dict: Sample session data
        """
        return {
            "_id": "test_mongo_id",
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user_123",
            "book_id": "test_book_456",
            "current_chunk_index": 0,
            "current_position_seconds": 0.0,
            "bookmarks": [],
            "total_time_spent_minutes": 0,
            "started_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "completed": False,
        }

    @pytest.mark.asyncio
    async def test_create_session_new(self, reading_service, mock_db, sample_session_data):
        """
        Test creating a new reading session.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup
        mock_db.reading_sessions.find_one = AsyncMock(return_value=None)
        mock_db.reading_sessions.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id="new_id")
        )

        # Execute
        result = await reading_service.create_session(
            user_id="test_user_123",
            book_id="test_book_456"
        )

        # Assert
        assert result is not None
        assert result.user_id == "test_user_123"
        assert result.book_id == "test_book_456"
        assert result.completed is False
        mock_db.reading_sessions.find_one.assert_called_once()
        mock_db.reading_sessions.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_existing(self, reading_service, mock_db, sample_session_data):
        """
        Test returning existing session when one exists.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup - session already exists
        mock_db.reading_sessions.find_one = AsyncMock(return_value=sample_session_data)

        # Execute
        result = await reading_service.create_session(
            user_id="test_user_123",
            book_id="test_book_456"
        )

        # Assert
        assert result is not None
        assert result.user_id == "test_user_123"
        assert result.book_id == "test_book_456"
        # insert_one should not be called since session exists
        mock_db.reading_sessions.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_bookmark(self, reading_service, mock_db, sample_session_data):
        """
        Test adding a bookmark to a session.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup
        session_with_bookmark = sample_session_data.copy()
        session_with_bookmark["bookmarks"] = [
            {
                "bookmark_id": "bm_123",
                "chunk_index": 5,
                "position_seconds": 150.5,
                "note": "Important passage",
                "chapter_title": "Chapter 3",
                "created_at": datetime.utcnow(),
            }
        ]
        mock_db.reading_sessions.find_one_and_update = AsyncMock(
            return_value=session_with_bookmark
        )

        # Execute
        result = await reading_service.add_bookmark(
            session_id=sample_session_data["session_id"],
            user_id="test_user_123",
            chunk_index=5,
            position_seconds=150.5,
            note="Important passage",
            chapter_title="Chapter 3"
        )

        # Assert
        assert result is not None
        assert len(result.bookmarks) == 1
        assert result.bookmarks[0].chunk_index == 5
        assert result.bookmarks[0].note == "Important passage"
        mock_db.reading_sessions.find_one_and_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_bookmark_not_found(self, reading_service, mock_db, sample_session_data):
        """
        Test adding bookmark to non-existent session.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup - session not found
        mock_db.reading_sessions.find_one_and_update = AsyncMock(return_value=None)

        # Execute
        result = await reading_service.add_bookmark(
            session_id="nonexistent_session",
            user_id="test_user_123",
            chunk_index=5,
            position_seconds=150.5,
            note="Test note"
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_bookmark(self, reading_service, mock_db, sample_session_data):
        """
        Test updating a bookmark note.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup
        session_with_updated_bookmark = sample_session_data.copy()
        session_with_updated_bookmark["bookmarks"] = [
            {
                "bookmark_id": "bm_123",
                "chunk_index": 5,
                "position_seconds": 150.5,
                "note": "Updated note",
                "chapter_title": "Chapter 3",
                "created_at": datetime.utcnow(),
            }
        ]
        mock_db.reading_sessions.find_one_and_update = AsyncMock(
            return_value=session_with_updated_bookmark
        )

        # Execute
        result = await reading_service.update_bookmark(
            session_id=sample_session_data["session_id"],
            user_id="test_user_123",
            bookmark_id="bm_123",
            note="Updated note"
        )

        # Assert
        assert result is not None
        assert result.bookmarks[0].note == "Updated note"

    @pytest.mark.asyncio
    async def test_delete_bookmark(self, reading_service, mock_db, sample_session_data):
        """
        Test deleting a bookmark.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup - session with no bookmarks after deletion
        session_after_delete = sample_session_data.copy()
        session_after_delete["bookmarks"] = []
        mock_db.reading_sessions.find_one_and_update = AsyncMock(
            return_value=session_after_delete
        )

        # Execute
        result = await reading_service.delete_bookmark(
            session_id=sample_session_data["session_id"],
            user_id="test_user_123",
            bookmark_id="bm_123"
        )

        # Assert
        assert result is not None
        assert len(result.bookmarks) == 0

    @pytest.mark.asyncio
    async def test_update_progress(self, reading_service, mock_db, sample_session_data):
        """
        Test updating reading progress.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup
        updated_session = sample_session_data.copy()
        updated_session["current_chunk_index"] = 10
        updated_session["current_position_seconds"] = 300.5
        mock_db.reading_sessions.find_one_and_update = AsyncMock(
            return_value=updated_session
        )

        # Execute
        from app.models.session import ReadingSessionUpdate
        update = ReadingSessionUpdate(
            current_chunk_index=10,
            current_position_seconds=300.5
        )
        result = await reading_service.update_progress(
            session_id=sample_session_data["session_id"],
            user_id="test_user_123",
            update=update
        )

        # Assert
        assert result is not None
        assert result.current_chunk_index == 10
        assert result.current_position_seconds == 300.5

    @pytest.mark.asyncio
    async def test_get_session(self, reading_service, mock_db, sample_session_data):
        """
        Test getting a session by ID.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup
        mock_db.reading_sessions.find_one = AsyncMock(return_value=sample_session_data)

        # Execute
        result = await reading_service.get_session(
            session_id=sample_session_data["session_id"],
            user_id="test_user_123"
        )

        # Assert
        assert result is not None
        assert result.session_id == sample_session_data["session_id"]
        assert result.user_id == "test_user_123"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, reading_service, mock_db):
        """
        Test getting non-existent session.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
        """
        # Setup
        mock_db.reading_sessions.find_one = AsyncMock(return_value=None)

        # Execute
        result = await reading_service.get_session(
            session_id="nonexistent",
            user_id="test_user_123"
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_completed(self, reading_service, mock_db, sample_session_data):
        """
        Test marking session as completed.

        Args:
            reading_service: ReadingService fixture
            mock_db: Mock database fixture
            sample_session_data: Sample session data
        """
        # Setup
        completed_session = sample_session_data.copy()
        completed_session["completed"] = True
        mock_db.reading_sessions.find_one_and_update = AsyncMock(
            return_value=completed_session
        )

        # Execute
        result = await reading_service.mark_completed(
            session_id=sample_session_data["session_id"],
            user_id="test_user_123"
        )

        # Assert
        assert result is not None
        assert result.completed is True


class TestBookmarkModel:
    """Test cases for Bookmark model."""

    def test_bookmark_creation(self):
        """Test creating a bookmark with all fields."""
        bookmark = Bookmark(
            chunk_index=5,
            position_seconds=150.5,
            note="Test note",
            chapter_title="Chapter 3"
        )

        assert bookmark.chunk_index == 5
        assert bookmark.position_seconds == 150.5
        assert bookmark.note == "Test note"
        assert bookmark.chapter_title == "Chapter 3"
        assert bookmark.bookmark_id is not None
        assert bookmark.created_at is not None

    def test_bookmark_default_values(self):
        """Test bookmark with default values."""
        bookmark = Bookmark(chunk_index=0)

        assert bookmark.chunk_index == 0
        assert bookmark.position_seconds == 0.0
        assert bookmark.note is None
        assert bookmark.chapter_title is None
        assert bookmark.bookmark_id is not None

    def test_bookmark_id_unique(self):
        """Test that bookmark IDs are unique."""
        bookmark1 = Bookmark(chunk_index=0)
        bookmark2 = Bookmark(chunk_index=1)

        assert bookmark1.bookmark_id != bookmark2.bookmark_id

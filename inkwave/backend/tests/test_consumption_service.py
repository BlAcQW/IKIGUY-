"""
Tests for consumption tracking service.

Tests the unified activity tracking system:
- Event recording
- Progress updates
- Completion tracking
- User/book statistics
- Admin dashboard queries
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.consumption import (
    ConsumptionEvent,
    ConsumptionEventCreate,
    ConsumptionEventType,
    ConsumptionMode,
    ProgressUpdateRequest,
    CompletionRequest,
)
from app.services.consumption_service import ConsumptionService


@pytest.fixture
def mock_db():
    """Create a mock MongoDB database."""
    db = MagicMock(spec=AsyncIOMotorDatabase)
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def consumption_service():
    """Create a consumption service instance."""
    return ConsumptionService()


class TestRecordEvent:
    """Test cases for recording consumption events."""

    @pytest.mark.asyncio
    async def test_record_book_opened_event(self, consumption_service, mock_db):
        """Test recording a book_opened event."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            # Setup mock
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id_123")
            )
            mock_db.__getitem__.return_value = mock_collection

            # Create event data
            event_data = ConsumptionEventCreate(
                book_id="book_123",
                session_id="session_456",
                event_type=ConsumptionEventType.BOOK_OPENED,
                consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
                chunk_index=0,
                total_chunks=10,
                book_title="Test Book",
                book_author="Test Author",
            )

            # Record event
            result = await consumption_service.record_event(
                user_id="user_789",
                event_data=event_data,
            )

            # Verify
            assert result is not None
            assert result.event_type == ConsumptionEventType.BOOK_OPENED
            assert result.user_id == "user_789"
            assert result.book_id == "book_123"
            mock_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_listening_started_event(self, consumption_service, mock_db):
        """Test recording a listening_started event."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id")
            )
            mock_db.__getitem__.return_value = mock_collection

            event_data = ConsumptionEventCreate(
                book_id="book_123",
                session_id="session_456",
                event_type=ConsumptionEventType.LISTENING_STARTED,
                consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
                chunk_index=0,
                position_seconds=0.0,
            )

            result = await consumption_service.record_event(
                user_id="user_789",
                event_data=event_data,
            )

            assert result.event_type == ConsumptionEventType.LISTENING_STARTED
            assert result.consumption_mode == ConsumptionMode.AUDIO_PLAYBACK

    @pytest.mark.asyncio
    async def test_record_ai_narration_event(self, consumption_service, mock_db):
        """Test that AI voice narration is tracked as a separate mode."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id")
            )
            mock_db.__getitem__.return_value = mock_collection

            event_data = ConsumptionEventCreate(
                book_id="book_123",
                session_id="session_456",
                event_type=ConsumptionEventType.LISTENING_STARTED,
                consumption_mode=ConsumptionMode.AI_VOICE_NARRATION,  # AI mode
                chunk_index=0,
            )

            result = await consumption_service.record_event(
                user_id="user_789",
                event_data=event_data,
            )

            # AI narration should count as listening time
            assert result.consumption_mode == ConsumptionMode.AI_VOICE_NARRATION


class TestProgressUpdate:
    """Test cases for progress tracking."""

    @pytest.mark.asyncio
    async def test_record_progress_update(self, consumption_service, mock_db):
        """Test recording a timer-based progress update."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id")
            )
            mock_db.__getitem__.return_value = mock_collection

            update = ProgressUpdateRequest(
                session_id="session_456",
                book_id="book_123",
                consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
                chunk_index=3,
                position_seconds=45.5,
                duration_since_last_update=30.0,  # 30 seconds since last update
                cumulative_time_seconds=120.0,
                total_chunks=10,
                is_final_chunk=False,
            )

            result = await consumption_service.record_progress_update(
                user_id="user_789",
                update=update,
            )

            assert result.event_type == ConsumptionEventType.PROGRESS_UPDATE
            assert result.chunk_index == 3
            assert result.cumulative_time_seconds == 120.0
            # Progress should be 4/10 = 40%
            assert result.progress_percentage == 40.0

    @pytest.mark.asyncio
    async def test_progress_percentage_calculation(self, consumption_service, mock_db):
        """Test that progress percentage is calculated correctly."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id")
            )
            mock_db.__getitem__.return_value = mock_collection

            # Test at chunk 8 of 10 (90%)
            update = ProgressUpdateRequest(
                session_id="session_456",
                book_id="book_123",
                consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
                chunk_index=8,
                position_seconds=0.0,
                duration_since_last_update=30.0,
                cumulative_time_seconds=300.0,
                total_chunks=10,
            )

            result = await consumption_service.record_progress_update(
                user_id="user_789",
                update=update,
            )

            # (8 + 1) / 10 = 90%
            assert result.progress_percentage == 90.0


class TestCompletion:
    """Test cases for deterministic book completion."""

    @pytest.mark.asyncio
    async def test_record_completion(self, consumption_service, mock_db):
        """Test recording a book completion event."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id")
            )
            mock_db.__getitem__.return_value = mock_collection

            completion = CompletionRequest(
                session_id="session_456",
                book_id="book_123",
                consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
                total_chunks=10,
                final_chunk_index=9,
                total_time_seconds=3600.0,  # 1 hour
                all_chunks_consumed=True,
                chunk_indices_consumed=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            )

            result = await consumption_service.record_completion(
                user_id="user_789",
                completion=completion,
            )

            assert result.event_type == ConsumptionEventType.COMPLETED
            assert result.progress_percentage == 100.0
            assert result.context["all_chunks_consumed"] is True

    @pytest.mark.asyncio
    async def test_partial_completion_tracked(self, consumption_service, mock_db):
        """Test that partial completion is tracked correctly."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id="test_id")
            )
            mock_db.__getitem__.return_value = mock_collection

            # User skipped some chunks
            completion = CompletionRequest(
                session_id="session_456",
                book_id="book_123",
                consumption_mode=ConsumptionMode.AUDIO_PLAYBACK,
                total_chunks=10,
                final_chunk_index=9,
                total_time_seconds=1800.0,
                all_chunks_consumed=False,  # Some skipped
                chunk_indices_consumed=[0, 1, 2, 7, 8, 9],  # Skipped 3-6
            )

            result = await consumption_service.record_completion(
                user_id="user_789",
                completion=completion,
            )

            assert result.event_type == ConsumptionEventType.COMPLETED
            assert result.context["all_chunks_consumed"] is False
            assert len(result.context["chunk_indices_consumed"]) == 6


class TestSessionRecovery:
    """Test cases for session recovery after page refresh."""

    @pytest.mark.asyncio
    async def test_get_session_latest_progress(self, consumption_service, mock_db):
        """Test retrieving latest progress for session recovery."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(
                return_value={
                    "session_id": "session_456",
                    "chunk_index": 5,
                    "position_seconds": 30.5,
                    "cumulative_time_seconds": 300.0,
                    "progress_percentage": 60.0,
                    "consumption_mode": "audio_playback",
                    "event_type": "progress_update",
                    "timestamp": datetime.utcnow(),
                }
            )
            mock_db.__getitem__.return_value = mock_collection

            result = await consumption_service.get_session_latest_progress(
                session_id="session_456"
            )

            assert result is not None
            assert result["chunk_index"] == 5
            assert result["cumulative_time_seconds"] == 300.0
            mock_collection.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_progress_not_found(self, consumption_service, mock_db):
        """Test handling of non-existent session."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_db.__getitem__.return_value = mock_collection

            result = await consumption_service.get_session_latest_progress(
                session_id="nonexistent_session"
            )

            assert result is None


class TestUserStats:
    """Test cases for user statistics."""

    @pytest.mark.asyncio
    async def test_get_user_stats(self, consumption_service, mock_db):
        """Test retrieving user consumption statistics."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()

            # Create async generator for books cursor
            async def books_async_iter():
                for item in [
                    {"_id": "book_1", "has_completed": 1, "has_started": 1},
                    {"_id": "book_2", "has_completed": 0, "has_started": 1},
                    {"_id": "book_3", "has_completed": 1, "has_started": 1},
                ]:
                    yield item

            # Create async generator for time cursor
            async def time_async_iter():
                for item in [
                    {"_id": "manual_reading", "total_seconds": 3600.0},
                    {"_id": "audio_playback", "total_seconds": 7200.0},
                    {"_id": "ai_voice_narration", "total_seconds": 1800.0},
                ]:
                    yield item

            books_cursor = MagicMock()
            books_cursor.__aiter__ = lambda self: books_async_iter()

            time_cursor = MagicMock()
            time_cursor.__aiter__ = lambda self: time_async_iter()

            mock_collection.aggregate = MagicMock(
                side_effect=[books_cursor, time_cursor]
            )
            mock_collection.find_one = AsyncMock(
                return_value={"timestamp": datetime.utcnow()}
            )
            mock_db.__getitem__.return_value = mock_collection

            result = await consumption_service.get_user_stats(
                user_id="user_789",
                period_days=7,
            )

            assert result.user_id == "user_789"
            assert result.total_books_opened == 3
            assert result.total_books_completed == 2
            assert result.total_books_in_progress == 1
            assert result.total_listening_time_seconds == 7200.0
            assert result.total_ai_narration_time_seconds == 1800.0


class TestAdminDashboard:
    """Test cases for admin dashboard statistics."""

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_stats(self, consumption_service, mock_db):
        """Test retrieving admin dashboard statistics."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()

            # Mock aggregation result
            cursor = MagicMock()
            cursor.to_list = AsyncMock(
                return_value=[
                    {
                        "_id": None,
                        "total_events": 1500,
                        "unique_users": ["user_1", "user_2", "user_3"],
                        "unique_books": ["book_1", "book_2"],
                        "unique_sessions": ["sess_1", "sess_2", "sess_3", "sess_4"],
                        "total_duration": 36000.0,  # 10 hours
                        "completions": 5,
                    }
                ]
            )
            mock_collection.aggregate = MagicMock(return_value=cursor)
            mock_db.__getitem__.return_value = mock_collection

            result = await consumption_service.get_admin_dashboard_stats(
                period_days=7
            )

            assert result["period_days"] == 7
            assert result["total_events"] == 1500
            assert result["unique_users"] == 3
            assert result["unique_books"] == 2
            assert result["total_sessions"] == 4
            assert result["total_duration_hours"] == 10.0
            assert result["total_completions"] == 5

    @pytest.mark.asyncio
    async def test_admin_dashboard_empty_period(self, consumption_service, mock_db):
        """Test admin dashboard with no events in period."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()

            cursor = MagicMock()
            cursor.to_list = AsyncMock(return_value=[])
            mock_collection.aggregate = MagicMock(return_value=cursor)
            mock_db.__getitem__.return_value = mock_collection

            result = await consumption_service.get_admin_dashboard_stats(
                period_days=7
            )

            assert result["total_events"] == 0
            assert result["unique_users"] == 0
            assert result["total_completions"] == 0


class TestBookStats:
    """Test cases for book statistics."""

    @pytest.mark.asyncio
    async def test_get_book_stats(self, consumption_service, mock_db):
        """Test retrieving book consumption statistics."""
        with patch("app.services.consumption_service.get_db", return_value=mock_db):
            mock_collection = MagicMock()

            # Mock find_one for book title
            mock_collection.find_one = AsyncMock(
                return_value={"book_title": "Test Book"}
            )

            # Mock users/sessions aggregation
            users_cursor = MagicMock()
            users_cursor.to_list = AsyncMock(
                return_value=[
                    {
                        "_id": None,
                        "unique_users": ["u1", "u2", "u3", "u4", "u5"],
                        "unique_sessions": ["s1", "s2", "s3", "s4", "s5", "s6"],
                        "total_time": 18000.0,  # 5 hours
                    }
                ]
            )

            # Create async generator for mode cursor
            async def mode_async_iter():
                for item in [
                    {"_id": "audio_playback", "count": 4},
                    {"_id": "ai_voice_narration", "count": 2},
                ]:
                    yield item

            mode_cursor = MagicMock()
            mode_cursor.__aiter__ = lambda self: mode_async_iter()

            mock_collection.aggregate = MagicMock(
                side_effect=[users_cursor, mode_cursor]
            )
            mock_collection.count_documents = AsyncMock(return_value=3)
            mock_db.__getitem__.return_value = mock_collection

            result = await consumption_service.get_book_stats(
                book_id="book_123",
                period_days=30,
            )

            assert result.book_id == "book_123"
            assert result.total_users == 5
            assert result.total_sessions == 6
            assert result.total_completions == 3
            assert result.completion_rate == 60.0  # 3/5

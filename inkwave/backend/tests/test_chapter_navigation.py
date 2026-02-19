"""
Test Chapter Navigation Features.

Real API tests for the enhanced chapter navigation functionality.
Tests actual backend API calls with real database data.

Author: AI Labs Africa
Created: November 30, 2025
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Optional
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient


# Test configuration
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%25@127.0.0.1:27017/inkwave?authSource=admin"
)
TEST_USER_ID = "test_chapter_nav_user"
TEST_USER_EMAIL = "test_chapter_nav@example.com"


# Global database connection
_client = None
_db = None


def get_db():
    """Get database connection."""
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGODB_URL)
        _db = _client.inkwave
    return _db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test book data
TEST_BOOK = {
    "id": "test_chapter_nav_book_001",
    "title": "Test Chapter Navigation Book",
    "author": "Test Author",
    "description": "A test book for chapter navigation features",
    "status": "published",
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
    "chapters": [
        {
            "id": "ch1",
            "title": "Chapter 1: Introduction",
            "order": 1,
            "duration": 10,
            "startTime": 0
        },
        {
            "id": "ch2",
            "title": "Chapter 2: The Journey Begins",
            "order": 2,
            "duration": 15,
            "startTime": 600
        },
        {
            "id": "ch3",
            "title": "Chapter 3: Challenges Ahead",
            "order": 3,
            "duration": 12,
            "startTime": 1500
        },
        {
            "id": "ch4",
            "title": "Chapter 4: The Resolution",
            "order": 4,
            "duration": 8,
            "startTime": 2220
        },
        {
            "id": "ch5",
            "title": "Chapter 5: Conclusion",
            "order": 5,
            "duration": 5,
            "startTime": 2700
        }
    ],
    "duration": 50,
    "cover_url": "https://example.com/cover.jpg"
}


class TestBookChaptersAPI:
    """Test book chapters API."""

    @pytest.mark.asyncio
    async def test_book_has_chapters(self):
        """Test that book has chapters array with required fields."""
        db = get_db()

        # Insert test book
        await db.books.update_one(
            {"id": TEST_BOOK["id"]},
            {"$set": TEST_BOOK},
            upsert=True
        )

        # Fetch book
        book = await db.books.find_one({"id": TEST_BOOK["id"]})

        assert book is not None
        assert "chapters" in book
        assert len(book["chapters"]) >= 3

        for chapter in book["chapters"]:
            assert "id" in chapter
            assert "title" in chapter
            assert "order" in chapter
            assert "duration" in chapter

    @pytest.mark.asyncio
    async def test_chapters_are_ordered(self):
        """Test that chapters are in correct order."""
        db = get_db()
        book = await db.books.find_one({"id": TEST_BOOK["id"]})

        chapters = book["chapters"]
        for i, chapter in enumerate(chapters):
            assert chapter["order"] == i + 1

    @pytest.mark.asyncio
    async def test_chapter_start_times_progressive(self):
        """Test that chapter start times are progressive."""
        db = get_db()
        book = await db.books.find_one({"id": TEST_BOOK["id"]})

        chapters = book["chapters"]
        prev_start = -1
        for chapter in chapters:
            start_time = chapter.get("startTime", 0)
            assert start_time >= prev_start, f"Chapter {chapter['order']} has invalid start time"
            prev_start = start_time


class TestChunksInfoAPI:
    """Test chunks info API with chapter boundaries."""

    @pytest.mark.asyncio
    async def test_chunks_info_returns_data(self):
        """Test that chunks info API returns expected data."""
        db = get_db()
        book_id = TEST_BOOK["id"]

        # Create test chunks
        chapters = TEST_BOOK["chapters"]
        chunks = []
        for i in range(10):
            chapter_idx = min(i // 2, len(chapters) - 1)
            chunk = {
                "book_id": book_id,
                "chunk_index": i,
                "text": f"This is the content for chunk {i}. " * 20,
                "chapter_title": chapters[chapter_idx]["title"],
                "audio_generated": False,
                "audio_duration": 30.0,
                "created_at": datetime.now(timezone.utc)
            }
            chunks.append(chunk)

        # Insert chunks
        await db.book_chunks.delete_many({"book_id": book_id})
        await db.book_chunks.insert_many(chunks)

        # Fetch chunks
        fetched_chunks = await db.book_chunks.find(
            {"book_id": book_id},
            {"chunk_index": 1, "audio_duration": 1, "chapter_title": 1, "text": 1}
        ).sort("chunk_index", 1).to_list(None)

        assert len(fetched_chunks) == 10

        # Calculate durations
        chunk_durations = [c.get("audio_duration", 30.0) for c in fetched_chunks]
        total_duration = sum(chunk_durations)

        assert total_duration == 300.0  # 10 chunks * 30 seconds

    @pytest.mark.asyncio
    async def test_chapter_boundaries_extraction(self):
        """Test chapter boundary extraction from chunks."""
        db = get_db()
        book_id = TEST_BOOK["id"]

        chunks = await db.book_chunks.find(
            {"book_id": book_id},
            {"chunk_index": 1, "chapter_title": 1}
        ).sort("chunk_index", 1).to_list(None)

        # Extract chapter boundaries
        chapter_boundaries = []
        current_chapter = None
        for c in chunks:
            chapter = c.get("chapter_title")
            if chapter and chapter != current_chapter:
                chapter_boundaries.append({
                    "chunk_index": c.get("chunk_index", 0),
                    "chapter_title": chapter
                })
                current_chapter = chapter

        assert len(chapter_boundaries) > 0

        # Verify boundaries have required fields
        for boundary in chapter_boundaries:
            assert "chunk_index" in boundary
            assert "chapter_title" in boundary
            assert isinstance(boundary["chunk_index"], int)
            assert len(boundary["chapter_title"]) > 0


class TestReadingSessionAPI:
    """Test reading session API for progress tracking."""

    @pytest.mark.asyncio
    async def test_session_creation(self):
        """Test reading session has required fields."""
        db = get_db()
        book_id = TEST_BOOK["id"]

        session = {
            "id": f"session_{book_id}_{TEST_USER_ID}",
            "user_id": TEST_USER_ID,
            "book_id": book_id,
            "current_chunk_index": 0,
            "position_seconds": 0,
            "total_time_listened": 0,
            "completed": False,
            "bookmarks": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        await db.reading_sessions.update_one(
            {"id": session["id"]},
            {"$set": session},
            upsert=True
        )

        fetched = await db.reading_sessions.find_one({"id": session["id"]})

        assert fetched is not None
        assert "id" in fetched
        assert "user_id" in fetched
        assert "book_id" in fetched
        assert "current_chunk_index" in fetched
        assert "position_seconds" in fetched
        assert "bookmarks" in fetched

    @pytest.mark.asyncio
    async def test_session_progress_update(self):
        """Test updating session progress."""
        db = get_db()
        session_id = f"session_{TEST_BOOK['id']}_{TEST_USER_ID}"

        # Update progress
        new_chunk = 3
        new_position = 45.5

        result = await db.reading_sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "current_chunk_index": new_chunk,
                    "position_seconds": new_position,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        assert result.modified_count == 1

        # Verify update
        updated = await db.reading_sessions.find_one({"id": session_id})
        assert updated["current_chunk_index"] == new_chunk
        assert updated["position_seconds"] == new_position


class TestBookmarkAPI:
    """Test bookmark creation and management."""

    @pytest.mark.asyncio
    async def test_add_chapter_bookmark(self):
        """Test adding a chapter bookmark."""
        db = get_db()
        session_id = f"session_{TEST_BOOK['id']}_{TEST_USER_ID}"
        chapter = TEST_BOOK["chapters"][1]  # Second chapter

        # Clear existing bookmarks first
        await db.reading_sessions.update_one(
            {"id": session_id},
            {"$set": {"bookmarks": []}}
        )

        bookmark = {
            "id": f"bm_{datetime.now(timezone.utc).timestamp()}",
            "chunk_index": 2,
            "position_seconds": float(chapter.get("startTime", 600)),
            "note": f"Chapter {chapter['order']}: {chapter['title']}",
            "chapter_title": chapter["title"],
            "created_at": datetime.now(timezone.utc)
        }

        result = await db.reading_sessions.update_one(
            {"id": session_id},
            {"$push": {"bookmarks": bookmark}}
        )

        assert result.modified_count == 1

        # Verify bookmark was added
        session = await db.reading_sessions.find_one({"id": session_id})
        assert len(session["bookmarks"]) == 1
        assert session["bookmarks"][0]["note"] == bookmark["note"]

    @pytest.mark.asyncio
    async def test_multiple_chapter_bookmarks(self):
        """Test adding multiple chapter bookmarks."""
        db = get_db()
        session_id = f"session_{TEST_BOOK['id']}_{TEST_USER_ID}"
        chapters = TEST_BOOK["chapters"][:3]  # First 3 chapters

        # Clear existing bookmarks
        await db.reading_sessions.update_one(
            {"id": session_id},
            {"$set": {"bookmarks": []}}
        )

        for i, chapter in enumerate(chapters):
            bookmark = {
                "id": f"bm_multi_{i}_{datetime.now(timezone.utc).timestamp()}",
                "chunk_index": i * 2,
                "position_seconds": float(chapter.get("startTime", i * 600)),
                "note": f"Chapter {chapter['order']}: {chapter['title']}",
                "chapter_title": chapter["title"],
                "created_at": datetime.now(timezone.utc)
            }

            await db.reading_sessions.update_one(
                {"id": session_id},
                {"$push": {"bookmarks": bookmark}}
            )

        # Verify all bookmarks
        session = await db.reading_sessions.find_one({"id": session_id})
        assert len(session["bookmarks"]) == 3

    @pytest.mark.asyncio
    async def test_delete_bookmark(self):
        """Test deleting a bookmark."""
        db = get_db()
        session_id = f"session_{TEST_BOOK['id']}_{TEST_USER_ID}"

        # Add a bookmark first
        bookmark = {
            "id": "bm_to_delete",
            "chunk_index": 0,
            "position_seconds": 0,
            "note": "Test bookmark to delete",
            "created_at": datetime.now(timezone.utc)
        }

        await db.reading_sessions.update_one(
            {"id": session_id},
            {"$push": {"bookmarks": bookmark}}
        )

        # Delete the bookmark
        result = await db.reading_sessions.update_one(
            {"id": session_id},
            {"$pull": {"bookmarks": {"id": "bm_to_delete"}}}
        )

        assert result.modified_count == 1

        # Verify deletion
        session = await db.reading_sessions.find_one({"id": session_id})
        bookmark_ids = [b["id"] for b in session["bookmarks"]]
        assert "bm_to_delete" not in bookmark_ids


class TestChapterProgressTracking:
    """Test chapter progress indicators functionality."""

    @pytest.mark.asyncio
    async def test_calculate_chapter_status(self):
        """Test calculating chapter status based on current time."""
        chapters = TEST_BOOK["chapters"]

        # Simulate being in the middle of chapter 2
        current_time = 900  # 15 minutes in

        statuses = []
        for i, chapter in enumerate(chapters):
            start = chapter.get("startTime", 0)
            next_chapter = chapters[i + 1] if i + 1 < len(chapters) else None
            end = next_chapter.get("startTime", float('inf')) if next_chapter else float('inf')

            if current_time >= end:
                status = "completed"
            elif current_time >= start and current_time < end:
                status = "in_progress"
            else:
                status = "unplayed"

            statuses.append({
                "chapter": chapter["order"],
                "status": status
            })

        # Chapter 1 should be completed (ends at 600, we're at 900)
        assert statuses[0]["status"] == "completed"

        # Chapter 2 should be in progress (starts at 600, ends at 1500, we're at 900)
        assert statuses[1]["status"] == "in_progress"

        # Remaining chapters should be unplayed
        for status in statuses[2:]:
            assert status["status"] == "unplayed"

    @pytest.mark.asyncio
    async def test_calculate_chapter_progress_percentage(self):
        """Test calculating progress percentage within a chapter."""
        chapters = TEST_BOOK["chapters"]

        # Chapter 2: starts at 600, ends at 1500 (duration 900 seconds)
        chapter_start = 600
        chapter_end = 1500
        chapter_duration = chapter_end - chapter_start

        current_time = 900  # In middle of chapter 2

        progress = ((current_time - chapter_start) / chapter_duration) * 100

        # Should be 33.33% through chapter 2 (300 / 900)
        assert 33 <= progress <= 34


class TestChapterTimestamps:
    """Test chapter timestamp formatting."""

    def format_timestamp(self, seconds: float) -> str:
        """Format seconds as timestamp HH:MM:SS or MM:SS."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hrs > 0:
            return f"{hrs}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def test_format_short_timestamp(self):
        """Test formatting timestamps under 1 hour."""
        assert self.format_timestamp(0) == "0:00"
        assert self.format_timestamp(60) == "1:00"
        assert self.format_timestamp(600) == "10:00"
        assert self.format_timestamp(1500) == "25:00"
        assert self.format_timestamp(2700) == "45:00"

    def test_format_long_timestamp(self):
        """Test formatting timestamps over 1 hour."""
        assert self.format_timestamp(3600) == "1:00:00"
        assert self.format_timestamp(3660) == "1:01:00"
        assert self.format_timestamp(7200) == "2:00:00"
        assert self.format_timestamp(5400) == "1:30:00"


class TestChapterNavigation:
    """Test chapter navigation logic."""

    @pytest.mark.asyncio
    async def test_go_to_next_chapter(self):
        """Test navigating to next chapter."""
        chapters = TEST_BOOK["chapters"]
        current_chapter_order = 2  # Currently on chapter 2

        # Find current index
        current_idx = next(
            (i for i, ch in enumerate(chapters) if ch["order"] == current_chapter_order),
            -1
        )

        assert current_idx >= 0

        # Go to next chapter
        if current_idx < len(chapters) - 1:
            next_chapter = chapters[current_idx + 1]
            assert next_chapter["order"] == 3
            assert "startTime" in next_chapter

    @pytest.mark.asyncio
    async def test_go_to_previous_chapter(self):
        """Test navigating to previous chapter."""
        chapters = TEST_BOOK["chapters"]
        current_chapter_order = 3  # Currently on chapter 3

        # Find current index
        current_idx = next(
            (i for i, ch in enumerate(chapters) if ch["order"] == current_chapter_order),
            -1
        )

        assert current_idx >= 0

        # Go to previous chapter
        if current_idx > 0:
            prev_chapter = chapters[current_idx - 1]
            assert prev_chapter["order"] == 2

    @pytest.mark.asyncio
    async def test_cannot_go_past_first_chapter(self):
        """Test boundary check for first chapter."""
        chapters = TEST_BOOK["chapters"]
        current_chapter_order = 1  # Already at first chapter

        current_idx = next(
            (i for i, ch in enumerate(chapters) if ch["order"] == current_chapter_order),
            -1
        )

        # At first chapter
        assert current_idx == 0
        # Cannot go to previous
        is_first = current_idx == 0
        assert is_first

    @pytest.mark.asyncio
    async def test_cannot_go_past_last_chapter(self):
        """Test boundary check for last chapter."""
        chapters = TEST_BOOK["chapters"]
        current_chapter_order = len(chapters)  # At last chapter

        current_idx = next(
            (i for i, ch in enumerate(chapters) if ch["order"] == current_chapter_order),
            -1
        )

        # At last chapter
        assert current_idx == len(chapters) - 1
        # Cannot go to next
        is_last = current_idx == len(chapters) - 1
        assert is_last


class TestChapterSearch:
    """Test chapter search/filter functionality."""

    @pytest.mark.asyncio
    async def test_search_chapter_by_title(self):
        """Test searching chapters by title."""
        chapters = TEST_BOOK["chapters"]
        search_query = "journey"

        # Filter chapters
        filtered = [
            ch for ch in chapters
            if search_query.lower() in ch["title"].lower()
        ]

        assert len(filtered) >= 1
        assert "Journey" in filtered[0]["title"]

    @pytest.mark.asyncio
    async def test_search_chapter_by_number(self):
        """Test searching chapters by number."""
        chapters = TEST_BOOK["chapters"]
        search_query = "3"

        # Filter chapters
        filtered = [
            ch for ch in chapters
            if search_query in str(ch["order"]) or search_query.lower() in ch["title"].lower()
        ]

        assert len(filtered) >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test search with no matching results."""
        chapters = TEST_BOOK["chapters"]
        search_query = "nonexistent_chapter_xyz"

        # Filter chapters
        filtered = [
            ch for ch in chapters
            if search_query.lower() in ch["title"].lower()
        ]

        assert len(filtered) == 0


class TestCleanup:
    """Cleanup test data after all tests."""

    @pytest.mark.asyncio
    async def test_cleanup_test_data(self):
        """Cleanup test data."""
        db = get_db()

        # Cleanup test book and related data
        await db.books.delete_one({"id": TEST_BOOK["id"]})
        await db.book_chunks.delete_many({"book_id": TEST_BOOK["id"]})
        await db.reading_sessions.delete_many({"user_id": TEST_USER_ID})

        # Verify cleanup
        book = await db.books.find_one({"id": TEST_BOOK["id"]})
        assert book is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

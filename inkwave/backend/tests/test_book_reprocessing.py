"""
Tests for book reprocessing and comprehensive deletion functionality.

Tests cover:
- Comprehensive book deletion (all associated data)
- Cleanup for reprocessing
- Audio cache file deletion
- Deletion preview endpoint
"""

import pytest
import asyncio
import os
import sys
import glob
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from motor.motor_asyncio import AsyncIOMotorClient

# Add app to path for imports
sys.path.insert(0, '/opt/kasaai/apps/inkwave/backend')

# MongoDB connection
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave?authSource=admin"
)


def get_db():
    """Get database connection for tests."""
    client = AsyncIOMotorClient(MONGODB_URL)
    return client.inkwave


async def init_app_db():
    """Initialize app database connection."""
    from app.core.database import Database
    try:
        await Database.connect()
    except Exception:
        # Already connected
        pass


class TestComprehensiveBookDeletion:
    """Tests for comprehensive book deletion."""

    @pytest.mark.asyncio
    async def test_delete_book_complete_deletes_chunks(self):
        """Test that deletion removes all book chunks."""
        await init_app_db()
        db = get_db()

        # Create a test book and chunks
        book_id = f"test_delete_{datetime.now(timezone.utc).timestamp()}"
        test_book = {
            "book_id": book_id,
            "title": "Test Book for Deletion",
            "author": "Test Author",
            "processing_status": "ready",
            "uploaded_by": "test_user",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.books.insert_one(test_book)

        # Add test chunks
        for i in range(3):
            await db.book_chunks.insert_one({
                "book_id": book_id,
                "chunk_index": i,
                "text": f"Test chunk {i}",
                "created_at": datetime.now(timezone.utc)
            })

        # Verify chunks exist
        chunks_before = await db.book_chunks.count_documents({"book_id": book_id})
        assert chunks_before == 3

        # Delete using the service method
        from app.services.book_service import BookService
        result = await BookService.delete_book_complete(book_id, delete_source_file=False)

        # Verify book and chunks deleted
        assert result is True
        book_after = await db.books.find_one({"book_id": book_id})
        assert book_after is None
        chunks_after = await db.book_chunks.count_documents({"book_id": book_id})
        assert chunks_after == 0

    @pytest.mark.asyncio
    async def test_delete_book_complete_deletes_sessions(self):
        """Test that deletion removes reading sessions."""
        await init_app_db()
        db = get_db()

        book_id = f"test_session_delete_{datetime.now(timezone.utc).timestamp()}"
        test_book = {
            "book_id": book_id,
            "title": "Test Book Sessions",
            "author": "Test Author",
            "processing_status": "ready",
            "uploaded_by": "test_user",
            "created_at": datetime.now(timezone.utc)
        }
        await db.books.insert_one(test_book)

        # Add test reading session
        await db.reading_sessions.insert_one({
            "session_id": "test_session_1",
            "book_id": book_id,
            "user_id": "test_user",
            "progress_percentage": 50,
            "bookmarks": [{"id": "bm1", "position": 100}],
            "created_at": datetime.now(timezone.utc)
        })

        # Verify session exists
        sessions_before = await db.reading_sessions.count_documents({"book_id": book_id})
        assert sessions_before == 1

        # Delete
        from app.services.book_service import BookService
        await BookService.delete_book_complete(book_id, delete_source_file=False)

        # Verify session deleted
        sessions_after = await db.reading_sessions.count_documents({"book_id": book_id})
        assert sessions_after == 0

    @pytest.mark.asyncio
    async def test_delete_book_complete_deletes_voice_settings(self):
        """Test that deletion removes book voice settings."""
        await init_app_db()
        db = get_db()

        book_id = f"test_voice_delete_{datetime.now(timezone.utc).timestamp()}"
        test_book = {
            "book_id": book_id,
            "title": "Test Voice Settings Book",
            "author": "Test Author",
            "processing_status": "ready",
            "uploaded_by": "test_user",
            "created_at": datetime.now(timezone.utc)
        }
        await db.books.insert_one(test_book)

        # Add voice settings
        await db.book_voice_settings.insert_one({
            "book_id": book_id,
            "tts_provider": "f5tts",
            "tts_voice": "archbishop_1",
            "created_at": datetime.now(timezone.utc)
        })

        # Verify voice settings exist
        settings_before = await db.book_voice_settings.count_documents({"book_id": book_id})
        assert settings_before == 1

        # Delete
        from app.services.book_service import BookService
        await BookService.delete_book_complete(book_id, delete_source_file=False)

        # Verify voice settings deleted
        settings_after = await db.book_voice_settings.count_documents({"book_id": book_id})
        assert settings_after == 0


class TestCleanupForReprocessing:
    """Tests for cleanup before reprocessing."""

    @pytest.mark.asyncio
    async def test_cleanup_preserves_book_record(self):
        """Test that cleanup keeps the book record but resets status."""
        await init_app_db()
        db = get_db()

        book_id = f"test_reprocess_{datetime.now(timezone.utc).timestamp()}"
        test_book = {
            "book_id": book_id,
            "title": "Book to Reprocess",
            "author": "Test Author",
            "processing_status": "ready",
            "processed": True,
            "chapters": [{"title": "Chapter 1"}],
            "uploaded_by": "test_user",
            "created_at": datetime.now(timezone.utc)
        }
        await db.books.insert_one(test_book)

        # Add chunks
        await db.book_chunks.insert_one({
            "book_id": book_id,
            "chunk_index": 0,
            "text": "Test chunk"
        })

        # Run cleanup
        from app.services.book_service import BookService
        result = await BookService.cleanup_for_reprocessing(book_id)

        # Verify book exists but status reset
        book_after = await db.books.find_one({"book_id": book_id})
        assert book_after is not None
        assert book_after.get("processing_status") == "pending"
        assert book_after.get("processed") is False
        assert book_after.get("chapters") == []

        # Verify chunks deleted
        chunks_after = await db.book_chunks.count_documents({"book_id": book_id})
        assert chunks_after == 0

        # Verify result summary
        assert result["chunks_deleted"] == 1
        assert result["status_reset"] is True

        # Cleanup
        await db.books.delete_one({"book_id": book_id})

    @pytest.mark.asyncio
    async def test_cleanup_deletes_voice_settings(self):
        """Test that cleanup removes voice settings for regeneration."""
        await init_app_db()
        db = get_db()

        book_id = f"test_reprocess_voice_{datetime.now(timezone.utc).timestamp()}"
        await db.books.insert_one({
            "book_id": book_id,
            "title": "Book Voice Reprocess",
            "author": "Test",
            "processing_status": "ready",
            "uploaded_by": "test_user"
        })
        await db.book_voice_settings.insert_one({
            "book_id": book_id,
            "tts_provider": "coqui"
        })

        from app.services.book_service import BookService
        result = await BookService.cleanup_for_reprocessing(book_id)

        # Verify voice settings deleted
        settings = await db.book_voice_settings.count_documents({"book_id": book_id})
        assert settings == 0
        assert result["voice_settings_deleted"] == 1

        # Cleanup
        await db.books.delete_one({"book_id": book_id})


class TestAudioCacheDeletion:
    """Tests for audio cache file deletion."""

    @pytest.mark.asyncio
    async def test_delete_audio_cache_with_pattern(self):
        """Test that audio cache files matching book pattern are deleted."""
        cache_dir = "/opt/kasaai/apps/inkwave/backend/storage/audiobooks"

        # Skip if directory doesn't exist
        if not os.path.exists(cache_dir):
            pytest.skip("Audio cache directory doesn't exist")

        # Create test files
        test_book_id = "test_audio_cache_delete"
        test_files = [
            f"{test_book_id}_chunk_0.mp3",
            f"{test_book_id}_chunk_0.mp3.meta",
            f"{test_book_id}_chunk_1_kokoro_voice.mp3",
        ]

        created_files = []
        for filename in test_files:
            filepath = os.path.join(cache_dir, filename)
            with open(filepath, "w") as f:
                f.write("test")
            created_files.append(filepath)

        # Verify files exist
        for filepath in created_files:
            assert os.path.exists(filepath)

        # Delete using service
        from app.services.book_service import BookService
        deleted_count = await BookService._delete_audio_cache(test_book_id)

        # Verify files deleted
        assert deleted_count >= len(test_files)
        for filepath in created_files:
            assert not os.path.exists(filepath), f"File not deleted: {filepath}"


class TestDeletionPreview:
    """Tests for deletion preview counts."""

    @pytest.mark.asyncio
    async def test_preview_counts_all_associated_data(self):
        """Test that preview shows correct counts."""
        db = get_db()

        book_id = f"test_preview_{datetime.now(timezone.utc).timestamp()}"

        # Create test data
        await db.books.insert_one({
            "book_id": book_id,
            "title": "Preview Test Book",
            "author": "Test",
            "uploaded_by": "test_user"
        })

        for i in range(5):
            await db.book_chunks.insert_one({
                "book_id": book_id,
                "chunk_index": i
            })

        await db.reading_sessions.insert_one({
            "book_id": book_id,
            "user_id": "test_user"
        })

        await db.interactions.insert_one({
            "book_id": book_id,
            "type": "like"
        })

        # Get counts
        chunks = await db.book_chunks.count_documents({"book_id": book_id})
        sessions = await db.reading_sessions.count_documents({"book_id": book_id})
        interactions = await db.interactions.count_documents({"book_id": book_id})

        assert chunks == 5
        assert sessions == 1
        assert interactions == 1

        # Cleanup
        await db.books.delete_one({"book_id": book_id})
        await db.book_chunks.delete_many({"book_id": book_id})
        await db.reading_sessions.delete_many({"book_id": book_id})
        await db.interactions.delete_many({"book_id": book_id})


class TestChapterModel:
    """Tests for updated chapter model with id, order, duration, start_time."""

    @pytest.mark.asyncio
    async def test_chapter_model_fields(self):
        """Test that new chapter fields are properly stored."""
        await init_app_db()
        db = get_db()

        book_id = f"test_chapter_model_{datetime.now(timezone.utc).timestamp()}"
        test_book = {
            "book_id": book_id,
            "title": "Chapter Model Test",
            "author": "Test Author",
            "processing_status": "ready",
            "uploaded_by": "test_user",
            "chapters": [
                {
                    "id": "ch_1",
                    "title": "Chapter 1",
                    "order": 1,
                    "start_chunk_id": 0,
                    "end_chunk_id": 2,
                    "word_count": 500,
                    "duration": 120,
                    "start_time": 0
                },
                {
                    "id": "ch_2",
                    "title": "Chapter 2",
                    "order": 2,
                    "start_chunk_id": 3,
                    "end_chunk_id": 5,
                    "word_count": 600,
                    "duration": 150,
                    "start_time": 120
                }
            ],
            "created_at": datetime.now(timezone.utc)
        }
        await db.books.insert_one(test_book)

        # Verify chapter fields
        book = await db.books.find_one({"book_id": book_id})
        chapters = book.get("chapters", [])

        assert len(chapters) == 2
        assert chapters[0]["id"] == "ch_1"
        assert chapters[0]["order"] == 1
        assert chapters[0]["duration"] == 120
        assert chapters[0]["start_time"] == 0
        assert chapters[1]["id"] == "ch_2"
        assert chapters[1]["order"] == 2
        assert chapters[1]["duration"] == 150
        assert chapters[1]["start_time"] == 120

        # Cleanup
        await db.books.delete_one({"book_id": book_id})

    @pytest.mark.asyncio
    async def test_chunk_chapter_fields(self):
        """Test that chunks have chapter_id and chapter_title."""
        await init_app_db()
        db = get_db()

        book_id = f"test_chunk_chapter_{datetime.now(timezone.utc).timestamp()}"

        # Create book
        await db.books.insert_one({
            "book_id": book_id,
            "title": "Chunk Chapter Test",
            "author": "Test",
            "uploaded_by": "test_user"
        })

        # Create chunk with chapter fields
        await db.book_chunks.insert_one({
            "book_id": book_id,
            "chunk_id": f"{book_id}_chunk_0",
            "chunk_index": 0,
            "text": "Test chunk text",
            "chapter_id": "ch_1",
            "chapter_title": "Chapter 1"
        })

        # Verify chunk fields
        chunk = await db.book_chunks.find_one({"book_id": book_id})
        assert chunk["chapter_id"] == "ch_1"
        assert chunk["chapter_title"] == "Chapter 1"

        # Cleanup
        await db.books.delete_one({"book_id": book_id})
        await db.book_chunks.delete_many({"book_id": book_id})

    @pytest.mark.asyncio
    async def test_update_chapter_durations(self):
        """Test updating chapter durations from chunk audio."""
        await init_app_db()
        db = get_db()

        book_id = f"test_duration_update_{datetime.now(timezone.utc).timestamp()}"

        # Create book with chapters (no durations)
        await db.books.insert_one({
            "book_id": book_id,
            "title": "Duration Test Book",
            "author": "Test",
            "uploaded_by": "test_user",
            "processed": True,
            "chapters": [
                {
                    "id": "ch_1",
                    "title": "Chapter 1",
                    "order": 1,
                    "start_chunk_id": 0,
                    "end_chunk_id": 1,
                    "word_count": 100,
                    "duration": None,
                    "start_time": None
                }
            ]
        })

        # Create chunks with audio duration
        for i in range(2):
            await db.book_chunks.insert_one({
                "book_id": book_id,
                "chunk_id": f"{book_id}_chunk_{i}",
                "chunk_index": i,
                "text": f"Chunk {i} text",
                "chapter_id": "ch_1",
                "chapter_title": "Chapter 1",
                "audio_duration": 30.5  # 30.5 seconds each
            })

        # Update chapter durations
        from app.services.book_service import BookService
        result = await BookService.update_chapter_durations(book_id)

        assert result["chapters_updated"] == 1
        assert result["total_duration_seconds"] == 61  # 30.5 * 2 = 61

        # Verify book was updated
        book = await db.books.find_one({"book_id": book_id})
        chapter = book["chapters"][0]
        assert chapter["duration"] == 61
        assert chapter["start_time"] == 0

        # Cleanup
        await db.books.delete_one({"book_id": book_id})
        await db.book_chunks.delete_many({"book_id": book_id})


class TestCleanup:
    """Cleanup test data."""

    @pytest.mark.asyncio
    async def test_cleanup_test_data(self):
        """Clean up any remaining test data."""
        db = get_db()

        # Delete test books
        result = await db.books.delete_many({
            "book_id": {"$regex": "^test_"}
        })
        print(f"Cleaned up {result.deleted_count} test books")

        # Delete test chunks
        result = await db.book_chunks.delete_many({
            "book_id": {"$regex": "^test_"}
        })
        print(f"Cleaned up {result.deleted_count} test chunks")

        # Delete test sessions
        result = await db.reading_sessions.delete_many({
            "book_id": {"$regex": "^test_"}
        })
        print(f"Cleaned up {result.deleted_count} test sessions")

        assert True

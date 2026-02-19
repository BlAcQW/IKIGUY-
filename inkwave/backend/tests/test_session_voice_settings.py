"""
Unit tests for Session Voice Settings Service.

Tests session-level voice settings overrides with real MongoDB data.
"""

import pytest
import asyncio
import uuid
from datetime import datetime

import sys
sys.path.insert(0, '/opt/kasaai/apps/shared')

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.session_voice_settings_service import (
    SessionVoiceSettingsService,
    get_session_voice_settings_service,
    EffectiveVoiceSettings,
)


@pytest.fixture
async def db_client():
    """Create MongoDB client."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    yield client
    client.close()


@pytest.fixture
async def test_db(db_client):
    """Get test database."""
    return db_client[settings.MONGODB_DB_NAME]


@pytest.fixture
def session_service():
    """Create session voice settings service."""
    return SessionVoiceSettingsService()


@pytest.fixture
def test_user_id():
    """Generate unique test user ID."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_session_id():
    """Generate unique test session ID."""
    return f"test_session_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_book_id():
    """Generate unique test book ID."""
    return f"test_book_{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def create_test_session(test_db, test_session_id, test_user_id, test_book_id):
    """Create a test reading session."""
    session_doc = {
        "session_id": test_session_id,
        "user_id": test_user_id,
        "book_id": test_book_id,
        "current_chunk_index": 0,
        "current_position_seconds": 0.0,
        "bookmarks": [],
        "total_time_spent_minutes": 0,
        "started_at": datetime.utcnow(),
        "last_accessed": datetime.utcnow(),
        "completed": False,
    }
    await test_db.reading_sessions.insert_one(session_doc)
    yield session_doc

    # Cleanup
    await test_db.reading_sessions.delete_one({"session_id": test_session_id})


@pytest.fixture
async def create_test_user_settings(test_db, test_user_id):
    """Create test user voice settings."""
    settings_doc = {
        "user_id": test_user_id,
        "tts": {
            "default_provider": "kokoro",
            "default_voice": "af_heart",
            "speed": 1.25,
            "pitch": 0.0,
        },
        "asr": {
            "default_provider": "faster_whisper_medium",
            "language": "en",
            "task": "transcribe",
        },
        "llm": {
            "default_model": "gpt-4o",
            "temperature": 0.8,
            "max_tokens": 3000,
        },
    }
    await test_db.voice_settings.insert_one(settings_doc)
    yield settings_doc

    # Cleanup
    await test_db.voice_settings.delete_one({"user_id": test_user_id})


class TestGetUserSettings:
    """Tests for retrieving user voice settings."""

    @pytest.mark.asyncio
    async def test_get_user_settings_existing(
        self, session_service, test_user_id, create_test_user_settings
    ):
        """Test getting settings for user with saved preferences."""
        settings = await session_service.get_user_settings(test_user_id)

        assert settings["tts"]["provider"] == "kokoro"
        assert settings["tts"]["voice"] == "af_heart"
        assert settings["tts"]["speed"] == 1.25
        assert settings["asr"]["provider"] == "faster_whisper_medium"
        assert settings["llm"]["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_get_user_settings_defaults(self, session_service):
        """Test getting settings for user without saved preferences."""
        settings = await session_service.get_user_settings("nonexistent_user")

        # Should return system defaults
        assert settings["tts"]["provider"] == "styletts2"
        assert settings["asr"]["provider"] == "faster_whisper_large"
        assert settings["llm"]["model"] == "gemini-2.0-flash-exp"


class TestEffectiveSettings:
    """Tests for merged effective settings."""

    @pytest.mark.asyncio
    async def test_effective_settings_no_overrides(
        self,
        session_service,
        test_user_id,
        test_session_id,
        create_test_session,
        create_test_user_settings,
    ):
        """Test effective settings with no session overrides."""
        settings = await session_service.get_effective_settings(
            session_id=test_session_id,
            user_id=test_user_id
        )

        assert isinstance(settings, EffectiveVoiceSettings)
        assert settings.has_overrides is False
        assert settings.tts.source == "user"
        assert settings.tts.provider == "kokoro"
        assert settings.tts.speed == 1.25

    @pytest.mark.asyncio
    async def test_effective_settings_with_overrides(
        self,
        session_service,
        test_user_id,
        test_session_id,
        test_db,
        create_test_session,
        create_test_user_settings,
    ):
        """Test effective settings with session overrides."""
        # Add session overrides
        await test_db.reading_sessions.update_one(
            {"session_id": test_session_id},
            {
                "$set": {
                    "voice_settings": {
                        "tts_provider": "f5tts",
                        "tts_speed": 1.5,
                        "llm_model": "claude-3-5-sonnet-20241022",
                    }
                }
            },
        )

        settings = await session_service.get_effective_settings(
            session_id=test_session_id,
            user_id=test_user_id
        )

        assert settings.has_overrides is True
        # TTS should be from session
        assert settings.tts.source == "session"
        assert settings.tts.provider == "f5tts"
        assert settings.tts.speed == 1.5
        # ASR should be from user (no override)
        assert settings.asr.source == "user"
        assert settings.asr.provider == "faster_whisper_medium"
        # LLM should be from session
        assert settings.llm.source == "session"
        assert settings.llm.model == "claude-3-5-sonnet-20241022"


class TestUpdateSessionSettings:
    """Tests for updating session voice settings."""

    @pytest.mark.asyncio
    async def test_update_session_settings(
        self,
        session_service,
        test_user_id,
        test_session_id,
        test_db,
        create_test_session,
    ):
        """Test updating session voice settings."""
        updates = {
            "tts_provider": "melotts",
            "tts_speed": 1.75,
            "llm_model": "gemini-1.5-pro",
            "llm_temperature": 0.5,
        }

        result = await session_service.update_session_settings(
            session_id=test_session_id,
            user_id=test_user_id,
            updates=updates,
        )

        assert "tts_provider" in result
        assert result["tts_provider"] == "melotts"
        assert result["tts_speed"] == 1.75
        assert result["llm_model"] == "gemini-1.5-pro"
        assert result["llm_temperature"] == 0.5

        # Verify in database
        session = await test_db.reading_sessions.find_one(
            {"session_id": test_session_id}
        )
        assert session["voice_settings"]["tts_provider"] == "melotts"

    @pytest.mark.asyncio
    async def test_update_nonexistent_session_raises(
        self, session_service, test_user_id
    ):
        """Test updating non-existent session raises error."""
        with pytest.raises(ValueError) as exc_info:
            await session_service.update_session_settings(
                session_id="nonexistent_session",
                user_id=test_user_id,
                updates={"tts_provider": "kokoro"},
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_preserves_existing_settings(
        self,
        session_service,
        test_user_id,
        test_session_id,
        test_db,
        create_test_session,
    ):
        """Test updating some settings preserves others."""
        # First update
        await session_service.update_session_settings(
            session_id=test_session_id,
            user_id=test_user_id,
            updates={"tts_provider": "kokoro", "tts_speed": 1.2},
        )

        # Second update (different settings)
        result = await session_service.update_session_settings(
            session_id=test_session_id,
            user_id=test_user_id,
            updates={"llm_model": "gpt-4o"},
        )

        # Both should be present
        session = await test_db.reading_sessions.find_one(
            {"session_id": test_session_id}
        )
        assert session["voice_settings"]["tts_provider"] == "kokoro"
        assert session["voice_settings"]["llm_model"] == "gpt-4o"


class TestClearSessionSettings:
    """Tests for clearing session voice settings."""

    @pytest.mark.asyncio
    async def test_clear_session_settings(
        self,
        session_service,
        test_user_id,
        test_session_id,
        test_db,
        create_test_session,
    ):
        """Test clearing session settings."""
        # Add some overrides first
        await session_service.update_session_settings(
            session_id=test_session_id,
            user_id=test_user_id,
            updates={"tts_provider": "kokoro", "llm_model": "gpt-4o"},
        )

        # Verify they exist
        session = await test_db.reading_sessions.find_one(
            {"session_id": test_session_id}
        )
        assert "voice_settings" in session

        # Clear settings
        result = await session_service.clear_session_settings(
            session_id=test_session_id,
            user_id=test_user_id,
        )

        assert result is True

        # Verify cleared
        session = await test_db.reading_sessions.find_one(
            {"session_id": test_session_id}
        )
        assert "voice_settings" not in session

    @pytest.mark.asyncio
    async def test_clear_no_settings_returns_false(
        self,
        session_service,
        test_user_id,
        test_session_id,
        create_test_session,
    ):
        """Test clearing when no settings exist returns False."""
        result = await session_service.clear_session_settings(
            session_id=test_session_id,
            user_id=test_user_id,
        )

        assert result is False


class TestServiceSingleton:
    """Tests for service singleton pattern."""

    @pytest.mark.asyncio
    async def test_get_service_returns_same_instance(self):
        """Test that get_session_voice_settings_service returns singleton."""
        service1 = await get_session_voice_settings_service()
        service2 = await get_session_voice_settings_service()

        assert service1 is service2

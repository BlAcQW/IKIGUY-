"""
Session Voice Settings Service.

Manages per-session voice settings overrides for InkWave.
Provides merged settings by combining session overrides with user defaults.
"""

import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Add shared services to path
sys.path.append('/opt/kasaai/apps/shared')

from app.core.database import get_db

logger = logging.getLogger(__name__)


class EffectiveTTSSettings(BaseModel):
    """Merged TTS settings with source tracking."""
    provider: str
    voice: Optional[str] = None
    speed: float = 1.0
    pitch: float = 0.0
    source: str = "system"  # session, user, org, system


class EffectiveASRSettings(BaseModel):
    """Merged ASR settings with source tracking."""
    provider: str
    language: str = "en"
    task: str = "transcribe"
    source: str = "system"


class EffectiveLLMSettings(BaseModel):
    """Merged LLM settings with source tracking."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    source: str = "system"


class EffectiveVoiceSettings(BaseModel):
    """Complete effective voice settings for a session."""
    tts: EffectiveTTSSettings
    asr: EffectiveASRSettings
    llm: EffectiveLLMSettings
    session_id: str
    has_overrides: bool = False


class SessionVoiceSettingsService:
    """
    Service for managing session-level voice settings.

    Provides merged settings by combining:
    1. Session overrides (highest priority)
    2. User defaults
    3. Organization defaults
    4. System defaults (lowest priority)
    """

    # System defaults (fallback values)
    SYSTEM_DEFAULTS = {
        "tts": {
            "provider": "styletts2",
            "voice": None,
            "speed": 1.0,
            "pitch": 0.0
        },
        "asr": {
            "provider": "faster_whisper_large",
            "language": "en",
            "task": "transcribe"
        },
        "llm": {
            "model": "gemini-2.0-flash-exp",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }

    async def get_user_settings(self, user_id: str, org_id: str = "default") -> Dict[str, Any]:
        """
        Get user's voice settings from MongoDB.

        Args:
            user_id: User identifier
            org_id: Organization identifier

        Returns:
            User voice settings or defaults
        """
        db = get_db()

        # Try to get user settings
        user_settings = await db.voice_settings.find_one({"user_id": user_id})

        if user_settings:
            return {
                "tts": {
                    "provider": user_settings.get("tts", {}).get("default_provider", self.SYSTEM_DEFAULTS["tts"]["provider"]),
                    "voice": user_settings.get("tts", {}).get("default_voice"),
                    "speed": user_settings.get("tts", {}).get("speed", self.SYSTEM_DEFAULTS["tts"]["speed"]),
                    "pitch": user_settings.get("tts", {}).get("pitch", self.SYSTEM_DEFAULTS["tts"]["pitch"]),
                },
                "asr": {
                    "provider": user_settings.get("asr", {}).get("default_provider", self.SYSTEM_DEFAULTS["asr"]["provider"]),
                    "language": user_settings.get("asr", {}).get("language", self.SYSTEM_DEFAULTS["asr"]["language"]),
                    "task": user_settings.get("asr", {}).get("task", self.SYSTEM_DEFAULTS["asr"]["task"]),
                },
                "llm": {
                    "model": user_settings.get("llm", {}).get("default_model", self.SYSTEM_DEFAULTS["llm"]["model"]),
                    "temperature": user_settings.get("llm", {}).get("temperature", self.SYSTEM_DEFAULTS["llm"]["temperature"]),
                    "max_tokens": user_settings.get("llm", {}).get("max_tokens", self.SYSTEM_DEFAULTS["llm"]["max_tokens"]),
                }
            }

        # Return system defaults
        return self.SYSTEM_DEFAULTS.copy()

    async def get_effective_settings(
        self,
        session_id: str,
        user_id: str,
        org_id: str = "default",
        book_id: Optional[str] = None
    ) -> EffectiveVoiceSettings:
        """
        Get merged voice settings for a session.

        Combines in priority order:
        1. Session overrides (highest)
        2. Book-level settings (if book_id provided)
        3. User defaults
        4. Organization defaults
        5. System defaults (lowest)

        Args:
            session_id: Reading session ID
            user_id: User ID
            org_id: Organization ID
            book_id: Optional book ID to include book-level settings

        Returns:
            EffectiveVoiceSettings with merged settings and source tracking
        """
        db = get_db()

        # Get user settings as base
        user_settings = await self.get_user_settings(user_id, org_id)

        # Get book-level settings if book_id provided
        book_settings = None
        if book_id:
            try:
                from app.services.book_voice_settings_service import get_book_voice_settings_service
                book_service = await get_book_voice_settings_service()
                book_settings = await book_service.get_book_settings(book_id, user_id)
            except Exception as e:
                logger.warning(f"Failed to get book settings: {e}")

        # Get session with voice settings
        session = await db.reading_sessions.find_one({
            "session_id": session_id,
            "user_id": user_id
        })

        session_overrides = session.get("voice_settings") if session else None
        if session and not book_id:
            # Try to get book_id from session
            book_id = session.get("book_id")
            if book_id:
                try:
                    from app.services.book_voice_settings_service import get_book_voice_settings_service
                    book_service = await get_book_voice_settings_service()
                    book_settings = await book_service.get_book_settings(book_id, user_id)
                except Exception as e:
                    logger.warning(f"Failed to get book settings: {e}")

        # Merge TTS settings (priority: session > book > user)
        tts_source = "user"
        tts = {
            "provider": user_settings["tts"]["provider"],
            "voice": user_settings["tts"]["voice"],
            "speed": user_settings["tts"]["speed"],
            "pitch": user_settings["tts"]["pitch"]
        }

        # Apply book-level settings (override user defaults)
        if book_settings:
            if book_settings.get("tts_provider"):
                tts["provider"] = book_settings["tts_provider"]
                tts_source = "book"
            if book_settings.get("tts_voice"):
                tts["voice"] = book_settings["tts_voice"]
                tts_source = "book"
            if book_settings.get("tts_speed") is not None:
                tts["speed"] = book_settings["tts_speed"]
                tts_source = "book"
            if book_settings.get("tts_pitch") is not None:
                tts["pitch"] = book_settings["tts_pitch"]
                tts_source = "book"

        # Apply session overrides (highest priority)
        if session_overrides:
            if session_overrides.get("tts_provider"):
                tts["provider"] = session_overrides["tts_provider"]
                tts_source = "session"
            if session_overrides.get("tts_voice"):
                tts["voice"] = session_overrides["tts_voice"]
                tts_source = "session"
            if session_overrides.get("tts_speed") is not None:
                tts["speed"] = session_overrides["tts_speed"]
                tts_source = "session"
            if session_overrides.get("tts_pitch") is not None:
                tts["pitch"] = session_overrides["tts_pitch"]
                tts_source = "session"

        # Merge ASR settings (priority: session > book > user)
        asr_source = "user"
        asr = {
            "provider": user_settings["asr"]["provider"],
            "language": user_settings["asr"]["language"],
            "task": user_settings["asr"]["task"]
        }

        # Apply book-level settings
        if book_settings:
            if book_settings.get("asr_provider"):
                asr["provider"] = book_settings["asr_provider"]
                asr_source = "book"
            if book_settings.get("asr_language"):
                asr["language"] = book_settings["asr_language"]
                asr_source = "book"
            if book_settings.get("asr_task"):
                asr["task"] = book_settings["asr_task"]
                asr_source = "book"

        # Apply session overrides
        if session_overrides:
            if session_overrides.get("asr_provider"):
                asr["provider"] = session_overrides["asr_provider"]
                asr_source = "session"
            if session_overrides.get("asr_language"):
                asr["language"] = session_overrides["asr_language"]
                asr_source = "session"
            if session_overrides.get("asr_task"):
                asr["task"] = session_overrides["asr_task"]
                asr_source = "session"

        # Merge LLM settings (priority: session > book > user)
        llm_source = "user"
        llm = {
            "model": user_settings["llm"]["model"],
            "temperature": user_settings["llm"]["temperature"],
            "max_tokens": user_settings["llm"]["max_tokens"]
        }

        # Apply book-level settings
        if book_settings:
            if book_settings.get("llm_model"):
                llm["model"] = book_settings["llm_model"]
                llm_source = "book"
            if book_settings.get("llm_temperature") is not None:
                llm["temperature"] = book_settings["llm_temperature"]
                llm_source = "book"
            if book_settings.get("llm_max_tokens") is not None:
                llm["max_tokens"] = book_settings["llm_max_tokens"]
                llm_source = "book"

        # Apply session overrides
        if session_overrides:
            if session_overrides.get("llm_model"):
                llm["model"] = session_overrides["llm_model"]
                llm_source = "session"
            if session_overrides.get("llm_temperature") is not None:
                llm["temperature"] = session_overrides["llm_temperature"]
                llm_source = "session"
            if session_overrides.get("llm_max_tokens") is not None:
                llm["max_tokens"] = session_overrides["llm_max_tokens"]
                llm_source = "session"

        has_overrides = (
            tts_source in ("session", "book") or
            asr_source in ("session", "book") or
            llm_source in ("session", "book")
        )

        return EffectiveVoiceSettings(
            tts=EffectiveTTSSettings(**tts, source=tts_source),
            asr=EffectiveASRSettings(**asr, source=asr_source),
            llm=EffectiveLLMSettings(**llm, source=llm_source),
            session_id=session_id,
            has_overrides=has_overrides
        )

    async def update_session_settings(
        self,
        session_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update session-level voice settings.

        Args:
            session_id: Reading session ID
            user_id: User ID
            updates: Dictionary of setting updates

        Returns:
            Updated session voice settings

        Raises:
            ValueError: If session not found
        """
        db = get_db()

        # Build voice_settings document
        voice_settings = {
            "applied_at": datetime.utcnow(),
            "source": "user_override"
        }

        # Map updates to voice_settings fields
        field_mapping = {
            "tts_provider": "tts_provider",
            "tts_voice": "tts_voice",
            "tts_speed": "tts_speed",
            "tts_pitch": "tts_pitch",
            "asr_provider": "asr_provider",
            "asr_language": "asr_language",
            "asr_task": "asr_task",
            "llm_model": "llm_model",
            "llm_temperature": "llm_temperature",
            "llm_max_tokens": "llm_max_tokens"
        }

        for key, value in updates.items():
            if key in field_mapping and value is not None:
                voice_settings[field_mapping[key]] = value

        # Update session document
        result = await db.reading_sessions.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$set": {"voice_settings": voice_settings},
                "$currentDate": {"last_accessed": True}
            }
        )

        if result.matched_count == 0:
            raise ValueError(f"Session {session_id} not found for user {user_id}")

        logger.info(f"Updated voice settings for session {session_id}")
        return voice_settings

    async def clear_session_settings(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Clear session overrides, reverting to user defaults.

        Args:
            session_id: Reading session ID
            user_id: User ID

        Returns:
            True if cleared, False if session not found
        """
        db = get_db()

        result = await db.reading_sessions.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$unset": {"voice_settings": ""},
                "$currentDate": {"last_accessed": True}
            }
        )

        if result.modified_count > 0:
            logger.info(f"Cleared voice settings for session {session_id}")
            return True

        return False


# Global service instance
_session_voice_settings_service: Optional[SessionVoiceSettingsService] = None


async def get_session_voice_settings_service() -> SessionVoiceSettingsService:
    """
    Get or create session voice settings service instance.

    Returns:
        SessionVoiceSettingsService instance
    """
    global _session_voice_settings_service

    if _session_voice_settings_service is None:
        _session_voice_settings_service = SessionVoiceSettingsService()

    return _session_voice_settings_service

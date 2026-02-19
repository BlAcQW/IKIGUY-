"""
Book Voice Settings Service.

Manages per-book voice settings that persist across sessions.
Integrates with SessionVoiceSettingsService to provide merged settings.
"""

import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Add shared services to path
sys.path.append('/opt/kasaai/apps/shared')

from app.core.database import get_db
from app.models.book_voice_settings import BookVoiceSettings, BookVoiceSettingsUpdate
from app.services.session_voice_settings_service import SessionVoiceSettingsService

logger = logging.getLogger(__name__)


class BookVoiceSettingsService:
    """
    Service for managing book-level voice settings.

    Provides methods to:
    - Get book voice settings
    - Update book voice settings
    - Clear book voice settings
    - Get effective settings (merged with user defaults)
    """

    def __init__(self):
        """Initialize book voice settings service."""
        self.session_service = None

    async def _get_session_service(self) -> SessionVoiceSettingsService:
        """Get or create session voice settings service."""
        if self.session_service is None:
            from app.services.session_voice_settings_service import get_session_voice_settings_service
            self.session_service = await get_session_voice_settings_service()
        return self.session_service

    async def get_book_settings(
        self,
        book_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get book-level voice settings for a user.

        Args:
            book_id: Book identifier
            user_id: User identifier

        Returns:
            Book voice settings dict or None if not set
        """
        db = get_db()

        settings_doc = await db.book_voice_settings.find_one({
            "book_id": book_id,
            "user_id": user_id
        })

        if settings_doc:
            # Remove MongoDB _id
            settings_doc.pop("_id", None)
            return settings_doc

        return None

    async def update_book_settings(
        self,
        book_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update book-level voice settings.

        Args:
            book_id: Book identifier
            user_id: User identifier
            updates: Dictionary of setting updates

        Returns:
            Updated book voice settings
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
            "llm_provider": "llm_provider",
            "llm_model": "llm_model",
            "llm_temperature": "llm_temperature",
            "llm_max_tokens": "llm_max_tokens",
            "system_prompt": "system_prompt"
        }

        for key, value in updates.items():
            if key in field_mapping and value is not None:
                voice_settings[field_mapping[key]] = value

        # Upsert book voice settings
        await db.book_voice_settings.update_one(
            {
                "book_id": book_id,
                "user_id": user_id
            },
            {
                "$set": {
                    **voice_settings,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "book_id": book_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        logger.info(f"Updated book voice settings: book={book_id}, user={user_id}")
        return voice_settings

    async def clear_book_settings(
        self,
        book_id: str,
        user_id: str
    ) -> bool:
        """
        Clear book-level voice settings, reverting to user defaults.

        Args:
            book_id: Book identifier
            user_id: User identifier

        Returns:
            True if cleared, False if not found
        """
        db = get_db()

        result = await db.book_voice_settings.delete_one({
            "book_id": book_id,
            "user_id": user_id
        })

        if result.deleted_count > 0:
            logger.info(f"Cleared book voice settings: book={book_id}, user={user_id}")
            return True

        return False

    async def get_effective_settings_for_session(
        self,
        session_id: str,
        book_id: str,
        user_id: str,
        org_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Get effective voice settings for a session, including book-level settings.

        Merges in priority order:
        1. Session overrides (highest)
        2. Book-level settings
        3. User defaults
        4. Organization defaults
        5. System defaults (lowest)

        Args:
            session_id: Reading session ID
            book_id: Book identifier
            user_id: User identifier
            org_id: Organization identifier

        Returns:
            Effective voice settings dict
        """
        # Get session service for merging
        session_service = await self._get_session_service()

        # Get user settings as base
        user_settings = await session_service.get_user_settings(user_id, org_id)

        # Get book-level settings
        book_settings = await self.get_book_settings(book_id, user_id)

        # Get session overrides
        db = get_db()
        session = await db.reading_sessions.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        session_overrides = session.get("voice_settings") if session else None

        # Merge settings in priority order
        # Start with user defaults
        effective = {
            "tts": user_settings["tts"].copy(),
            "asr": user_settings["asr"].copy(),
            "llm": user_settings["llm"].copy()
        }

        # Apply book-level settings (override user defaults)
        if book_settings:
            if book_settings.get("tts_provider"):
                effective["tts"]["provider"] = book_settings["tts_provider"]
            if book_settings.get("tts_voice"):
                effective["tts"]["voice"] = book_settings["tts_voice"]
            if book_settings.get("tts_speed") is not None:
                effective["tts"]["speed"] = book_settings["tts_speed"]
            if book_settings.get("tts_pitch") is not None:
                effective["tts"]["pitch"] = book_settings["tts_pitch"]

            if book_settings.get("asr_provider"):
                effective["asr"]["provider"] = book_settings["asr_provider"]
            if book_settings.get("asr_language"):
                effective["asr"]["language"] = book_settings["asr_language"]
            if book_settings.get("asr_task"):
                effective["asr"]["task"] = book_settings["asr_task"]

            if book_settings.get("llm_model"):
                effective["llm"]["model"] = book_settings["llm_model"]
            if book_settings.get("llm_temperature") is not None:
                effective["llm"]["temperature"] = book_settings["llm_temperature"]
            if book_settings.get("llm_max_tokens") is not None:
                effective["llm"]["max_tokens"] = book_settings["llm_max_tokens"]

        # Apply session overrides (highest priority)
        if session_overrides:
            if session_overrides.get("tts_provider"):
                effective["tts"]["provider"] = session_overrides["tts_provider"]
            if session_overrides.get("tts_voice"):
                effective["tts"]["voice"] = session_overrides["tts_voice"]
            if session_overrides.get("tts_speed") is not None:
                effective["tts"]["speed"] = session_overrides["tts_speed"]
            if session_overrides.get("tts_pitch") is not None:
                effective["tts"]["pitch"] = session_overrides["tts_pitch"]

            if session_overrides.get("asr_provider"):
                effective["asr"]["provider"] = session_overrides["asr_provider"]
            if session_overrides.get("asr_language"):
                effective["asr"]["language"] = session_overrides["asr_language"]
            if session_overrides.get("asr_task"):
                effective["asr"]["task"] = session_overrides["asr_task"]

            if session_overrides.get("llm_model"):
                effective["llm"]["model"] = session_overrides["llm_model"]
            if session_overrides.get("llm_temperature") is not None:
                effective["llm"]["temperature"] = session_overrides["llm_temperature"]
            if session_overrides.get("llm_max_tokens") is not None:
                effective["llm"]["max_tokens"] = session_overrides["llm_max_tokens"]

        return effective


# Global service instance
_book_voice_settings_service: Optional[BookVoiceSettingsService] = None


async def get_book_voice_settings_service() -> BookVoiceSettingsService:
    """
    Get or create book voice settings service instance.

    Returns:
        BookVoiceSettingsService instance
    """
    global _book_voice_settings_service

    if _book_voice_settings_service is None:
        _book_voice_settings_service = BookVoiceSettingsService()

    return _book_voice_settings_service


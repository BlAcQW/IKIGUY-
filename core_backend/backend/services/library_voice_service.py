"""
Library Voice Management Service

Handles CRUD operations for voice library metadata in MongoDB.
Allows dynamic management of reference voices without code changes.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import wave
import contextlib

from ..mongo import get_database
from ..models.library_voice import (
    LibraryVoiceModel,
    LIBRARY_VOICES_COLLECTION,
    LIBRARY_VOICES_INDEXES
)

logger = logging.getLogger(__name__)


class LibraryVoiceService:
    """Service for managing library voices"""

    def __init__(self):
        self.db = get_database()
        self.collection = self.db[LIBRARY_VOICES_COLLECTION]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure MongoDB indexes are created"""
        try:
            existing_indexes = self.collection.index_information()

            for index in LIBRARY_VOICES_INDEXES:
                index_name = "_".join([f"{field}_{direction}" for field, direction in index])
                if index_name not in existing_indexes:
                    self.collection.create_index(index, name=index_name)
                    logger.info(f"Created index: {index_name}")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")

    def _get_file_size_display(self, size_bytes: int) -> str:
        """
        Convert bytes to human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Human-readable size (e.g., '6.1MB')
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"

    def _get_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract audio metadata from WAV file.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with duration and sample_rate
        """
        try:
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return {
                    "duration": round(duration, 2),
                    "sample_rate": rate
                }
        except Exception as e:
            logger.warning(f"Failed to extract audio metadata from {file_path}: {str(e)}")
            return {"duration": None, "sample_rate": None}

    async def list_voices(
        self,
        gender: Optional[str] = None,
        language: Optional[str] = None,
        accent: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List library voices with optional filters.

        Args:
            gender: Filter by gender
            language: Filter by language
            accent: Filter by accent
            is_active: Filter by active status
            is_featured: Filter by featured status
            tags: Filter by tags (any match)

        Returns:
            List of voice metadata dictionaries
        """
        query = {}

        if gender:
            query["gender"] = gender
        if language:
            query["language"] = language
        if accent:
            query["accent"] = accent
        if is_active is not None:
            query["is_active"] = is_active
        if is_featured is not None:
            query["is_featured"] = is_featured
        if tags:
            query["tags"] = {"$in": tags}

        cursor = self.collection.find(query).sort("created_at", -1)
        voices = []

        async for voice in cursor:
            voice["_id"] = str(voice["_id"])
            voices.append(voice)

        return voices

    async def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single voice by ID.

        Args:
            voice_id: Unique voice identifier

        Returns:
            Voice metadata dictionary or None if not found
        """
        voice = await self.collection.find_one({"voice_id": voice_id})

        if voice:
            voice["_id"] = str(voice["_id"])

        return voice

    async def create_voice(
        self,
        voice_id: str,
        name: str,
        file_path: str,
        gender: str = "neutral",
        accent: str = "neutral",
        language: str = "en",
        description: str = "",
        is_featured: bool = False,
        tags: List[str] = None,
        uploaded_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new library voice entry.

        Args:
            voice_id: Unique voice identifier
            name: Voice name
            file_path: Path to audio file on disk
            gender: Voice gender
            accent: Voice accent
            language: Primary language
            description: Voice description
            is_featured: Whether voice is featured
            tags: Tags for categorization
            uploaded_by: User ID who uploaded

        Returns:
            Created voice metadata dictionary

        Raises:
            ValueError: If voice_id already exists or file doesn't exist
        """
        # Check if voice already exists
        existing = await self.get_voice(voice_id)
        if existing:
            raise ValueError(f"Voice with ID '{voice_id}' already exists")

        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        # Get file size
        file_size = os.path.getsize(file_path)
        file_size_display = self._get_file_size_display(file_size)

        # Extract audio metadata
        audio_metadata = self._get_audio_metadata(file_path)

        # Create voice document
        voice = LibraryVoiceModel(
            voice_id=voice_id,
            name=name,
            file_path=file_path,
            file_size=file_size,
            file_size_display=file_size_display,
            duration=audio_metadata.get("duration"),
            sample_rate=audio_metadata.get("sample_rate"),
            gender=gender,
            accent=accent,
            language=language,
            description=description,
            is_featured=is_featured,
            tags=tags or [],
            uploaded_by=uploaded_by,
            upload_source="manual"
        )

        # Insert voice (exclude _id to let MongoDB auto-generate)
        voice_dict = voice.model_dump(by_alias=True, exclude_none=True)
        if "_id" in voice_dict:
            del voice_dict["_id"]
        await self.collection.insert_one(voice_dict)

        # Return created voice
        return await self.get_voice(voice_id)

    async def update_voice(
        self,
        voice_id: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """
        Update a library voice.

        Args:
            voice_id: Unique voice identifier
            **updates: Fields to update

        Returns:
            Updated voice metadata dictionary or None if not found
        """
        # Remove _id and voice_id from updates
        updates.pop("_id", None)
        updates.pop("voice_id", None)

        # Add updated_at timestamp
        updates["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {"voice_id": voice_id},
            {"$set": updates}
        )

        if result.modified_count == 0:
            return None

        return await self.get_voice(voice_id)

    async def delete_voice(
        self,
        voice_id: str,
        delete_file: bool = False
    ) -> bool:
        """
        Delete a library voice.

        Args:
            voice_id: Unique voice identifier
            delete_file: Whether to also delete the audio file from disk

        Returns:
            True if deleted, False if not found
        """
        voice = await self.get_voice(voice_id)
        if not voice:
            return False

        # Delete from MongoDB
        result = await self.collection.delete_one({"voice_id": voice_id})

        # Optionally delete file from disk
        if delete_file and os.path.exists(voice["file_path"]):
            try:
                os.remove(voice["file_path"])
                logger.info(f"Deleted voice file: {voice['file_path']}")
            except Exception as e:
                logger.error(f"Failed to delete voice file: {str(e)}")

        return result.deleted_count > 0

    async def migrate_from_hardcoded(
        self,
        voices_dir: str = "/opt/kasaai/apps/voice-lab/voices"
    ) -> Dict[str, Any]:
        """
        Migrate existing voice files from directory to MongoDB.

        Args:
            voices_dir: Directory containing voice files

        Returns:
            Migration summary
        """
        voices_dir_path = Path(voices_dir)
        if not voices_dir_path.exists():
            raise ValueError(f"Voices directory not found: {voices_dir}")

        migrated = []
        skipped = []
        errors = []

        # Scan for WAV files
        for wav_file in voices_dir_path.glob("*.wav"):
            try:
                # Generate voice_id from filename
                voice_id = wav_file.stem

                # Check if already exists
                existing = await self.get_voice(voice_id)
                if existing:
                    skipped.append(voice_id)
                    continue

                # Create voice entry
                voice = await self.create_voice(
                    voice_id=voice_id,
                    name=voice_id.replace("_", " ").title(),
                    file_path=str(wav_file),
                    description=f"Voice file: {wav_file.name}"
                )

                migrated.append(voice_id)
                logger.info(f"Migrated voice: {voice_id}")

            except Exception as e:
                errors.append({"voice_id": voice_id, "error": str(e)})
                logger.error(f"Failed to migrate {voice_id}: {str(e)}")

        return {
            "total_migrated": len(migrated),
            "total_skipped": len(skipped),
            "total_errors": len(errors),
            "migrated": migrated,
            "skipped": skipped,
            "errors": errors
        }


# Singleton instance
_library_voice_service: Optional[LibraryVoiceService] = None


def get_library_voice_service() -> LibraryVoiceService:
    """Get or create library voice service instance"""
    global _library_voice_service
    if _library_voice_service is None:
        _library_voice_service = LibraryVoiceService()
    return _library_voice_service

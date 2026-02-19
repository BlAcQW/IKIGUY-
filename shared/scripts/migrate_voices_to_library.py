#!/usr/bin/env python3
"""
Voice Library Migration Script

Migrates existing voices from app-specific implementations to the centralized
voice library system.

Sources:
- /api/voice-lab/library-voices (old library voices)
- /api/voice-lab/voices (AKAN_MMS voices)
- /api/voice-lab/voices/cloned (cloned voices)
- InkWave voice implementations
- ChurchFlow voice implementations
- StudyFlow voice implementations
- EventFlow voice implementations

Author: AI Labs Africa
Date: November 8, 2025
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Import voice library service
from apps.shared.services.voice_library_service import (
    VoiceLibraryService,
    VoiceCreate,
    VoiceCharacteristics,
    VoiceAccess,
    VoiceMetadata,
    VoiceVisibility,
    VoiceGender,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceMigrator:
    """
    Migrates voices from old implementations to centralized voice library.
    """

    def __init__(self, mongodb_url: str, database_name: str = "kasaai_core"):
        """
        Initialize the migrator.

        Args:
            mongodb_url: MongoDB connection URL
            database_name: Database name
        """
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[database_name]
        self.voice_library_service = VoiceLibraryService(
            mongodb_url=mongodb_url,
            database_name=database_name
        )

        self.stats = {
            "total_found": 0,
            "migrated": 0,
            "skipped": 0,
            "errors": 0,
            "duplicates": 0
        }

    async def initialize(self):
        """Initialize the voice library service."""
        await self.voice_library_service.initialize()
        logger.info("Voice library service initialized")

    async def migrate_old_library_voices(self, default_user_id: str = "system"):
        """
        Migrate voices from the old library_voices collection.

        Args:
            default_user_id: Default user ID for system voices
        """
        logger.info("Migrating old library voices...")

        try:
            # Check if library_voices collection exists
            old_collection = self.db["library_voices"]
            count = await old_collection.count_documents({})

            if count == 0:
                logger.info("No old library voices found to migrate")
                return

            logger.info(f"Found {count} old library voices")
            self.stats["total_found"] += count

            async for voice_doc in old_collection.find({}):
                try:
                    # Check if already migrated (by voice_id)
                    existing = await self.voice_library_service.get_voice(
                        voice_doc.get("voice_id", str(voice_doc["_id"])),
                        default_user_id
                    )

                    if existing:
                        logger.info(f"Voice {voice_doc.get('name')} already exists, skipping")
                        self.stats["duplicates"] += 1
                        continue

                    # Create voice data
                    voice_data = VoiceCreate(
                        name=voice_doc.get("name", "Unknown Voice"),
                        description=voice_doc.get("description", "Migrated from old library"),
                        characteristics=VoiceCharacteristics(
                            gender=self._map_gender(voice_doc.get("gender", "unknown")),
                            language=voice_doc.get("language", "en"),
                            accent=voice_doc.get("accent"),
                            dialect=voice_doc.get("dialect"),
                            tone=None,
                            pace=None,
                            age_range=None
                        ),
                        access=VoiceAccess(
                            visibility=VoiceVisibility.PUBLIC if voice_doc.get("is_featured") else VoiceVisibility.ORGANIZATION
                        ),
                        metadata=VoiceMetadata(
                            tags=voice_doc.get("tags", []),
                            categories=["Migrated", "Library Voice"],
                            use_cases=["General TTS"],
                            featured=voice_doc.get("is_featured", False),
                            verified=True
                        )
                    )

                    # If there's a file path, read and upload
                    audio_file = None
                    audio_filename = None

                    if voice_doc.get("file_path"):
                        file_path = Path(voice_doc["file_path"])
                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                audio_file = f.read()
                            audio_filename = file_path.name
                            logger.info(f"Found audio file: {file_path}")

                    # Create voice in library
                    new_voice = await self.voice_library_service.create_voice(
                        voice_data=voice_data,
                        audio_file=audio_file,
                        audio_filename=audio_filename,
                        user_id=default_user_id,
                        organization_id=None
                    )

                    logger.info(f"✅ Migrated voice: {new_voice.name} ({new_voice.voice_id})")
                    self.stats["migrated"] += 1

                except Exception as e:
                    logger.error(f"❌ Error migrating voice {voice_doc.get('name')}: {e}")
                    self.stats["errors"] += 1
                    continue

        except Exception as e:
            logger.error(f"Error accessing old library_voices: {e}")

    async def migrate_cloned_voices(self, default_user_id: str = "system"):
        """
        Migrate cloned voices from the cloned_voices collection.

        Args:
            default_user_id: Default user ID for system voices
        """
        logger.info("Migrating cloned voices...")

        try:
            cloned_collection = self.db["cloned_voices"]
            count = await cloned_collection.count_documents({"status": "completed"})

            if count == 0:
                logger.info("No completed cloned voices found to migrate")
                return

            logger.info(f"Found {count} completed cloned voices")
            self.stats["total_found"] += count

            async for voice_doc in cloned_collection.find({"status": "completed"}):
                try:
                    # Check if already migrated
                    existing = await self.voice_library_service.get_voice(
                        voice_doc.get("voice_id", str(voice_doc["_id"])),
                        default_user_id
                    )

                    if existing:
                        logger.info(f"Cloned voice {voice_doc.get('name')} already exists, skipping")
                        self.stats["duplicates"] += 1
                        continue

                    # Create voice data
                    voice_data = VoiceCreate(
                        name=voice_doc.get("name", "Cloned Voice"),
                        description=voice_doc.get("description", "Cloned voice migrated from old system"),
                        characteristics=VoiceCharacteristics(
                            gender=self._map_gender(voice_doc.get("gender", "unknown")),
                            language=voice_doc.get("language", "en"),
                            accent=voice_doc.get("accent"),
                            dialect=None,
                            tone=None,
                            pace=None,
                            age_range=None
                        ),
                        access=VoiceAccess(
                            visibility=VoiceVisibility.PRIVATE
                        ),
                        metadata=VoiceMetadata(
                            tags=["cloned", voice_doc.get("provider", "unknown")],
                            categories=["Migrated", "Cloned Voice"],
                            use_cases=voice_doc.get("capabilities", ["Voice Cloning"]),
                            featured=False,
                            verified=False
                        )
                    )

                    # If there's a reference audio path, read and upload
                    audio_file = None
                    audio_filename = None

                    if voice_doc.get("reference_audio_path"):
                        file_path = Path(voice_doc["reference_audio_path"])
                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                audio_file = f.read()
                            audio_filename = file_path.name
                            logger.info(f"Found reference audio: {file_path}")

                    # Create voice in library
                    new_voice = await self.voice_library_service.create_voice(
                        voice_data=voice_data,
                        audio_file=audio_file,
                        audio_filename=audio_filename,
                        user_id=voice_doc.get("user_id", default_user_id),
                        organization_id=voice_doc.get("organization_id")
                    )

                    logger.info(f"✅ Migrated cloned voice: {new_voice.name} ({new_voice.voice_id})")
                    self.stats["migrated"] += 1

                except Exception as e:
                    logger.error(f"❌ Error migrating cloned voice {voice_doc.get('name')}: {e}")
                    self.stats["errors"] += 1
                    continue

        except Exception as e:
            logger.error(f"Error accessing cloned_voices: {e}")

    async def create_default_voices(self, default_user_id: str = "system"):
        """
        Create default AKAN voices if they don't exist.

        Args:
            default_user_id: Default user ID for system voices
        """
        logger.info("Creating default AKAN voices...")

        akan_voices = [
            {
                "name": "Asante Male 1",
                "language": "tw",
                "dialect": "asante",
                "gender": "male",
                "description": "Native Twi voice with Asante dialect - Male",
                "use_cases": ["Conversational", "Education", "Narration"]
            },
            {
                "name": "Asante Female 1",
                "language": "tw",
                "dialect": "asante",
                "gender": "female",
                "description": "Native Twi voice with Asante dialect - Female",
                "use_cases": ["Conversational", "Education", "Narration"]
            },
            {
                "name": "Fante Male 1",
                "language": "tw",
                "dialect": "fante",
                "gender": "male",
                "description": "Native Twi voice with Fante dialect - Male",
                "use_cases": ["Conversational", "Education", "Regional Content"]
            },
            {
                "name": "Akuapem Female 1",
                "language": "tw",
                "dialect": "akuapem",
                "gender": "female",
                "description": "Native Twi voice with Akuapem dialect - Female",
                "use_cases": ["Conversational", "Education", "Regional Content"]
            },
        ]

        for voice_info in akan_voices:
            try:
                # Check if exists
                voice_id = f"{voice_info['dialect']}_{voice_info['gender']}_1"
                existing = await self.voice_library_service.get_voice(voice_id, default_user_id)

                if existing:
                    logger.info(f"AKAN voice {voice_info['name']} already exists, skipping")
                    self.stats["duplicates"] += 1
                    continue

                voice_data = VoiceCreate(
                    name=voice_info["name"],
                    description=voice_info["description"],
                    characteristics=VoiceCharacteristics(
                        gender=self._map_gender(voice_info["gender"]),
                        language=voice_info["language"],
                        accent="Ghanaian",
                        dialect=voice_info["dialect"],
                        tone="Natural",
                        pace="Medium",
                        age_range="Adult"
                    ),
                    access=VoiceAccess(
                        visibility=VoiceVisibility.PUBLIC
                    ),
                    metadata=VoiceMetadata(
                        tags=["akan", "twi", voice_info["dialect"], "african"],
                        categories=["African Languages", "Twi", "MMS"],
                        use_cases=voice_info["use_cases"],
                        featured=True,
                        verified=True
                    )
                )

                new_voice = await self.voice_library_service.create_voice(
                    voice_data=voice_data,
                    audio_file=None,
                    audio_filename=None,
                    user_id=default_user_id,
                    organization_id=None
                )

                logger.info(f"✅ Created AKAN voice: {new_voice.name} ({new_voice.voice_id})")
                self.stats["migrated"] += 1

            except Exception as e:
                logger.error(f"❌ Error creating AKAN voice {voice_info['name']}: {e}")
                self.stats["errors"] += 1

    def _map_gender(self, gender: str) -> VoiceGender:
        """
        Map gender string to VoiceGender enum.

        Args:
            gender: Gender string

        Returns:
            VoiceGender enum value
        """
        gender_lower = str(gender).lower()

        if gender_lower in ["male", "m"]:
            return VoiceGender.MALE
        elif gender_lower in ["female", "f"]:
            return VoiceGender.FEMALE
        elif gender_lower in ["neutral", "n"]:
            return VoiceGender.NEUTRAL
        else:
            return VoiceGender.UNKNOWN

    async def run_migration(self, default_user_id: str = "system"):
        """
        Run the complete migration process.

        Args:
            default_user_id: Default user ID for system voices
        """
        logger.info("=" * 60)
        logger.info("Starting Voice Library Migration")
        logger.info("=" * 60)

        await self.initialize()

        # Migrate old library voices
        await self.migrate_old_library_voices(default_user_id)

        # Migrate cloned voices
        await self.migrate_cloned_voices(default_user_id)

        # Create default AKAN voices
        await self.create_default_voices(default_user_id)

        # Print statistics
        logger.info("=" * 60)
        logger.info("Migration Complete!")
        logger.info("=" * 60)
        logger.info(f"Total voices found: {self.stats['total_found']}")
        logger.info(f"Successfully migrated: {self.stats['migrated']}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)

    async def cleanup(self):
        """Cleanup resources."""
        self.client.close()


async def main():
    """Main entry point."""
    # Get MongoDB URL from environment
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        logger.error("MONGODB_URL environment variable not set")
        sys.exit(1)

    # Get default user ID
    default_user_id = os.getenv("MIGRATION_USER_ID", "system")

    # Create migrator
    migrator = VoiceMigrator(
        mongodb_url=mongodb_url,
        database_name="kasaai_core"
    )

    try:
        await migrator.run_migration(default_user_id)
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

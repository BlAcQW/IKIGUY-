"""
Voice Cloning Service - Batch clone voices using multiple TTS providers

This service handles:
1. Cloning voices from reference audio files
2. Managing cloned voice metadata in MongoDB
3. Integration with multiple TTS providers (Coqui XTTS, OpenVoice, F5-TTS, StyleTTS2)
4. Storage and retrieval of cloned voices
"""

import logging
import base64
import asyncio
import httpx
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib
import io

from pydantic import BaseModel, Field
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection

from ..models.cloned_voice import (
    ClonedVoiceModel,
    CLONED_VOICES_COLLECTION,
    CLONED_VOICES_INDEXES
)

logger = logging.getLogger(__name__)


# MongoDB connection
def get_mongodb_client() -> MongoClient:
    """Get MongoDB client from environment variable

    Returns:
        MongoClient instance
    """
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
    return MongoClient(mongodb_url)


def get_mongodb_database() -> Database:
    """Get MongoDB database

    Returns:
        Database instance
    """
    client = get_mongodb_client()
    return client.get_database("kasaai_core")


class VoiceCloneMetadata(BaseModel):
    """Metadata for a cloned voice"""
    voice_id: str
    name: str
    provider: str
    reference_audio_path: str
    reference_audio_size: int
    cloned_at: str
    language: str = "en"
    gender: str = "neutral"
    accent: str = "neutral"
    description: str = ""
    capabilities: List[str] = []
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None


class VoiceCloneRequest(BaseModel):
    """Request to clone a voice"""
    name: str
    reference_audio_path: str
    provider: str
    language: str = "en"
    gender: str = "neutral"
    accent: str = "neutral"
    description: str = ""


class VoiceCloningService:
    """Service for batch cloning voices across multiple TTS providers"""

    # TTS Provider endpoints
    TTS_PROVIDERS = {
        "coqui_xtts": {
            "endpoint": "https://coqui.ailabsafrica.com",
            "supports_cloning": True,
            "health_path": "/health",
            "clone_path": "/synthesize_with_reference"
        },
        "openvoice": {
            "endpoint": "https://openvoice.ailabsafrica.com",
            "supports_cloning": True,
            "health_path": "/health",
            "clone_path": "/synthesize_with_reference"
        },
        "f5tts": {
            "endpoint": "https://f5tts.ailabsafrica.com",
            "supports_cloning": True,
            "health_path": "/health",
            "clone_path": "/synthesize_with_reference"
        },
        "styletts2": {
            "endpoint": "https://styletts.ailabsafrica.com",
            "supports_cloning": True,
            "health_path": "/health",
            "clone_path": "/synthesize_with_reference"
        }
    }

    # Voice files from voice-lab directory
    GHANAIAN_VOICES = [
        {
            "name": "Nana Aba",
            "file": "nana_aba.wav",
            "path": "/opt/kasaai/apps/voice-lab/voices/nana_aba.wav",
            "gender": "female",
            "accent": "Ghanaian",
            "description": "Professional female Ghanaian voice",
        },
        {
            "name": "Nana Aba (24-bit)",
            "file": "nana_aba_24_bit.wav",
            "path": "/opt/kasaai/apps/voice-lab/voices/nana_aba_24_bit.wav",
            "gender": "female",
            "accent": "Ghanaian",
            "description": "High-quality 24-bit professional female Ghanaian voice",
        },
        {
            "name": "Adom Okyere",
            "file": "adom_okyere.wav",
            "path": "/opt/kasaai/apps/voice-lab/voices/adom_okyere.wav",
            "gender": "male",
            "accent": "Ghanaian",
            "description": "Male Ghanaian voice",
        },
        {
            "name": "Juliet Bawuah",
            "file": "juliet_bawuah.wav",
            "path": "/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav",
            "gender": "female",
            "accent": "Ghanaian",
            "description": "Female Ghanaian voice",
        },
        {
            "name": "Archbishop 1",
            "file": "archbishop_1.wav",
            "path": "/opt/kasaai/apps/voice-lab/voices/archbishop_1.wav",
            "gender": "male",
            "accent": "Ghanaian",
            "description": "Male Ghanaian voice - Archbishop sample 1",
        },
        {
            "name": "Archbishop 2",
            "file": "archbishop_2.wav",
            "path": "/opt/kasaai/apps/voice-lab/voices/archbishop_2.wav",
            "gender": "male",
            "accent": "Ghanaian",
            "description": "Male Ghanaian voice - Archbishop sample 2",
        }
    ]

    def __init__(self, storage_dir: str = "/opt/kasaai/apps/voice-lab/cloned_voices"):
        """Initialize voice cloning service

        Args:
            storage_dir: Directory to store reference audio files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # MongoDB setup
        self.db = get_mongodb_database()
        self.collection: Collection = self.db[CLONED_VOICES_COLLECTION]

        # Create indexes
        self._create_indexes()

        logger.info(f"Voice Cloning Service initialized with MongoDB storage and audio files at {self.storage_dir}")

    def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        try:
            # Create unique index on voice_id
            self.collection.create_index([("voice_id", ASCENDING)], unique=True)

            # Create other indexes
            for index_fields in CLONED_VOICES_INDEXES[1:]:  # Skip voice_id as it's already created
                self.collection.create_index(index_fields)

            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def _generate_voice_id(self, name: str, provider: str) -> str:
        """Generate unique voice ID

        Args:
            name: Voice name
            provider: Provider name

        Returns:
            Unique voice ID
        """
        raw_id = f"{name}_{provider}_{datetime.now().isoformat()}"
        return hashlib.md5(raw_id.encode()).hexdigest()[:16]

    async def check_provider_health(self, provider: str) -> bool:
        """Check if a TTS provider is online and healthy

        Args:
            provider: Provider name

        Returns:
            True if provider is healthy, False otherwise
        """
        if provider not in self.TTS_PROVIDERS:
            logger.warning(f"Unknown provider: {provider}")
            return False

        config = self.TTS_PROVIDERS[provider]
        health_url = f"{config['endpoint']}{config['health_path']}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    logger.info(f"✅ {provider} is healthy")
                    return True
                else:
                    logger.warning(f"⚠️ {provider} returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ {provider} health check failed: {e}")
            return False

    async def clone_voice(
        self,
        name: str,
        reference_audio_path: str,
        provider: str,
        language: str = "en",
        gender: str = "neutral",
        accent: str = "neutral",
        description: str = "",
        test_text: str = "Hello, this is a test of the cloned voice."
    ) -> Optional[VoiceCloneMetadata]:
        """Clone a voice using the specified provider

        Args:
            name: Voice name
            reference_audio_path: Path to reference audio file
            provider: TTS provider to use
            language: Voice language
            gender: Voice gender
            accent: Voice accent
            description: Voice description
            test_text: Text to synthesize for testing

        Returns:
            Voice metadata if successful, None otherwise
        """
        try:
            logger.info(f"🎭 Cloning voice '{name}' with {provider}")

            # Check if reference audio exists
            audio_path = Path(reference_audio_path)
            if not audio_path.exists():
                logger.error(f"Reference audio not found: {reference_audio_path}")
                return None

            # Check provider health
            if not await self.check_provider_health(provider):
                logger.error(f"Provider {provider} is not healthy")
                return None

            # Generate voice ID
            voice_id = self._generate_voice_id(name, provider)

            # Create metadata entry
            metadata = ClonedVoiceModel(
                voice_id=voice_id,
                name=name,
                provider=provider,
                reference_audio_path=reference_audio_path,
                reference_audio_size=audio_path.stat().st_size,
                cloned_at=datetime.now().isoformat(),
                language=language,
                gender=gender,
                accent=accent,
                description=description,
                capabilities=["voice_cloning", "real_time"],
                status="processing"
            )

            # Store metadata in MongoDB
            self.collection.insert_one(metadata.model_dump(by_alias=True, exclude={"id"}))

            # Read reference audio
            with open(reference_audio_path, 'rb') as f:
                audio_bytes = f.read()

            # Test voice cloning with the provider
            config = self.TTS_PROVIDERS[provider]
            clone_url = f"{config['endpoint']}{config['clone_path']}"

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # Prepare multipart form data
                    files = {
                        'reference_audio': ('reference.wav', audio_bytes, 'audio/wav')
                    }
                    data = {
                        'text': test_text,
                        'language': language
                    }

                    response = await client.post(clone_url, files=files, data=data)

                    if response.status_code == 200:
                        logger.info(f"✅ Successfully cloned voice '{name}' with {provider}")
                        metadata.status = "completed"
                    else:
                        logger.error(f"❌ Voice cloning failed: {response.status_code}")
                        metadata.status = "failed"
                        metadata.error_message = f"HTTP {response.status_code}"

            except Exception as e:
                logger.error(f"❌ Voice cloning request failed: {e}")
                metadata.status = "failed"
                metadata.error_message = str(e)

            # Update metadata in MongoDB
            self.collection.update_one(
                {"voice_id": voice_id},
                {"$set": {
                    "status": metadata.status,
                    "error_message": metadata.error_message,
                    "updated_at": datetime.utcnow()
                }}
            )

            return metadata

        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return None

    async def batch_clone_voices(
        self,
        providers: Optional[List[str]] = None,
        test_text: str = "Hello, this is a test of the cloned voice."
    ) -> Dict[str, List[VoiceCloneMetadata]]:
        """Batch clone all Ghanaian voices across specified providers

        Args:
            providers: List of providers to use (default: all clone-capable providers)
            test_text: Text to use for testing cloned voices

        Returns:
            Dictionary mapping provider names to list of cloned voice metadata
        """
        if providers is None:
            providers = [p for p, config in self.TTS_PROVIDERS.items()
                        if config["supports_cloning"]]

        logger.info(f"🚀 Starting batch voice cloning for {len(self.GHANAIAN_VOICES)} voices across {len(providers)} providers")

        results = {provider: [] for provider in providers}

        # Clone each voice with each provider
        tasks = []
        for voice_info in self.GHANAIAN_VOICES:
            for provider in providers:
                # Generate name from filename + provider
                # e.g., "archbishop_1" + "coqui_xtts" = "archbishop_1_coqui"
                base_filename = Path(voice_info["file"]).stem  # Remove .wav extension
                provider_short = provider.replace("_", "").replace("xtts", "").replace("tts", "")[:6]  # Shorten provider name
                cloned_name = f"{base_filename}_{provider_short}"

                task = self.clone_voice(
                    name=cloned_name,
                    reference_audio_path=voice_info["path"],
                    provider=provider,
                    language="en",  # Ghanaian voices use English
                    gender=voice_info["gender"],
                    accent=voice_info["accent"],
                    description=f"{voice_info['description']} (cloned with {provider})",
                    test_text=test_text
                )
                tasks.append((provider, task))

        # Execute cloning in parallel (with limit to avoid overwhelming providers)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent cloning operations

        async def clone_with_limit(provider, task):
            async with semaphore:
                return provider, await task

        cloning_results = await asyncio.gather(
            *[clone_with_limit(provider, task) for provider, task in tasks],
            return_exceptions=True
        )

        # Organize results
        for result in cloning_results:
            if isinstance(result, tuple):
                provider, metadata = result
                if metadata:
                    results[provider].append(metadata)

        # Summary
        total_successful = sum(len(voices) for voices in results.values())
        logger.info(f"✅ Batch cloning completed: {total_successful} successful clones")

        return results

    def list_cloned_voices(
        self,
        provider: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ClonedVoiceModel]:
        """List all cloned voices

        Args:
            provider: Filter by provider (optional)
            status: Filter by status (optional)

        Returns:
            List of voice metadata
        """
        query = {}
        if provider:
            query["provider"] = provider
        if status:
            query["status"] = status

        voices = []
        for doc in self.collection.find(query).sort("created_at", DESCENDING):
            try:
                voices.append(ClonedVoiceModel(**doc))
            except Exception as e:
                logger.error(f"Failed to parse voice document: {e}")
                continue

        return voices

    def get_voice_metadata(self, voice_id: str) -> Optional[ClonedVoiceModel]:
        """Get metadata for a specific voice

        Args:
            voice_id: Voice identifier

        Returns:
            Voice metadata if found, None otherwise
        """
        doc = self.collection.find_one({"voice_id": voice_id})
        if doc:
            try:
                return ClonedVoiceModel(**doc)
            except Exception as e:
                logger.error(f"Failed to parse voice document: {e}")
                return None
        return None

    def get_reference_audio(self, voice_id: str) -> Optional[bytes]:
        """Get reference audio for a voice

        Args:
            voice_id: Voice identifier

        Returns:
            Audio bytes if found, None otherwise
        """
        metadata = self.get_voice_metadata(voice_id)
        if not metadata:
            return None

        try:
            with open(metadata.reference_audio_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read reference audio: {e}")
            return None

    def get_reference_audio_base64(self, voice_id: str) -> Optional[str]:
        """Get reference audio as base64

        Args:
            voice_id: Voice identifier

        Returns:
            Base64 encoded audio if found, None otherwise
        """
        audio_bytes = self.get_reference_audio(voice_id)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice and its reference audio file

        Args:
            voice_id: Voice identifier

        Returns:
            True if successful, False otherwise
        """
        # Get metadata to find audio file path
        metadata = self.get_voice_metadata(voice_id)
        if not metadata:
            logger.warning(f"Voice {voice_id} not found")
            return False

        # Delete from MongoDB
        result = self.collection.delete_one({"voice_id": voice_id})

        if result.deleted_count > 0:
            logger.info(f"Deleted voice metadata from MongoDB: {voice_id}")

            # Note: We DON'T delete the original reference audio files from voice-lab/voices/
            # because they are the master copies. Only delete if there were custom uploads.
            # Check if this is a custom uploaded voice (not from the GHANAIAN_VOICES list)
            is_master_voice = any(
                metadata.reference_audio_path == voice["path"]
                for voice in self.GHANAIAN_VOICES
            )

            if not is_master_voice:
                # This is a custom upload, safe to delete the audio file
                audio_path = Path(metadata.reference_audio_path)
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                        logger.info(f"Deleted reference audio file: {metadata.reference_audio_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete audio file: {e}")
            else:
                logger.info(f"Preserved master reference audio at: {metadata.reference_audio_path}")

            return True

        return False

    async def get_provider_statistics(self) -> Dict[str, Any]:
        """Get statistics about cloned voices per provider using MongoDB aggregation

        Returns:
            Statistics dictionary
        """
        # Total count
        total_voices = self.collection.count_documents({})

        # Provider stats
        provider_pipeline = [
            {"$group": {"_id": "$provider", "count": {"$sum": 1}}}
        ]
        by_provider = {
            doc["_id"]: doc["count"]
            for doc in self.collection.aggregate(provider_pipeline)
        }

        # Status stats
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        by_status_list = list(self.collection.aggregate(status_pipeline))
        by_status = {
            "completed": 0,
            "processing": 0,
            "failed": 0,
            "pending": 0
        }
        for doc in by_status_list:
            if doc["_id"] in by_status:
                by_status[doc["_id"]] = doc["count"]

        # Gender stats
        gender_pipeline = [
            {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
        ]
        by_gender_list = list(self.collection.aggregate(gender_pipeline))
        by_gender = {
            "male": 0,
            "female": 0,
            "neutral": 0
        }
        for doc in by_gender_list:
            if doc["_id"] in by_gender:
                by_gender[doc["_id"]] = doc["count"]

        return {
            "total_voices": total_voices,
            "by_provider": by_provider,
            "by_status": by_status,
            "by_gender": by_gender
        }


# Singleton instance
_voice_cloning_service: Optional[VoiceCloningService] = None


def get_voice_cloning_service() -> VoiceCloningService:
    """Get or create voice cloning service instance

    Returns:
        VoiceCloningService instance
    """
    global _voice_cloning_service
    if _voice_cloning_service is None:
        _voice_cloning_service = VoiceCloningService()
    return _voice_cloning_service

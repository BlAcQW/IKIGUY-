"""
Centralized Reference Audio Service

Provides unified reference audio management for zero-shot TTS providers across all KasaAI applications:
- InkWave (audiobook narration)
- ChurchFlow (announcements, greetings)
- StudyFlow (tutoring voices)
- B2C Portal (voice customization)
- Any app using zero-shot TTS providers

Features:
- Reference audio CRUD operations
- File storage (local + Hetzner backup)
- Zero-shot TTS provider compatibility
- Voice library integration
- User and organization scoping

Zero-Shot TTS Providers Supported:
- StyleTTS2
- Coqui XTTS
- OpenVoice
- F5-TTS

Author: AI Labs Africa
Created: November 29, 2025
"""

import os
import logging
import hashlib
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

# Import storage services
from apps.shared.storage.hetzner_storage_box import HetznerStorageBox

logger = logging.getLogger(__name__)


# ==================== Constants ====================

ZERO_SHOT_PROVIDERS = ["styletts2", "coqui_xtts", "openvoice", "f5tts"]

ACCEPTED_FORMATS = [".wav", ".mp3", ".ogg", ".flac", ".m4a"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ==================== Enums ====================

class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"


# ==================== Data Models ====================

class ReferenceAudio(BaseModel):
    """Reference audio document model"""
    reference_audio_id: str = Field(..., description="Unique reference audio identifier")
    user_id: str = Field(..., description="Owner user ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    
    # Metadata
    name: str = Field(..., description="Reference audio name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Description", max_length=500)
    
    # File information
    audio_url: str = Field(..., description="Public URL to access the audio file")
    storage_path: Optional[str] = Field(None, description="Storage path (local or cloud)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    format: AudioFormat = Field(..., description="Audio format")
    
    # Provider compatibility
    compatible_providers: List[str] = Field(
        default_factory=lambda: ZERO_SHOT_PROVIDERS,
        description="Compatible zero-shot TTS providers"
    )
    
    # Voice library integration
    voice_id: Optional[str] = Field(None, description="Linked voice library entry ID")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class ReferenceAudioCreate(BaseModel):
    """Request to create reference audio"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    audio_bytes: bytes = Field(..., description="Audio file bytes")
    audio_filename: str = Field(..., description="Original filename")
    create_voice: bool = Field(False, description="Create voice library entry")
    gender: Optional[str] = Field(None, description="Gender for voice entry")
    language: Optional[str] = Field("en", description="Language for voice entry")
    tags: Optional[List[str]] = Field(None, description="Tags for voice entry")


class ReferenceAudioUpdate(BaseModel):
    """Request to update reference audio"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ReferenceAudioFilters(BaseModel):
    """Filters for reference audio search"""
    search: Optional[str] = Field(None, description="Search query")
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    compatible_provider: Optional[str] = Field(None, description="Filter by compatible provider")


# ==================== Service ====================

class ReferenceAudioService:
    """Centralized reference audio management service"""

    def __init__(
        self,
        mongodb_url: str = None,
        database_name: str = "kasaai_core",
        storage_config: Dict[str, Any] = None,
        storage_base_path: str = "reference_audio"
    ):
        """
        Initialize Reference Audio Service.

        Args:
            mongodb_url: MongoDB connection URL
            database_name: Database name
            storage_config: Hetzner storage configuration
            storage_base_path: Base path for storage (app-specific)
        """
        self.mongodb_url = mongodb_url or os.getenv("MONGODB_URL")
        self.database_name = database_name
        self.storage_base_path = storage_base_path
        
        # Initialize MongoDB connection
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # Storage configuration
        self.storage_config = storage_config or {}
        self.storage_backend: Optional[HetznerStorageBox] = None
        
        # Local storage fallback
        self.local_storage_path = os.getenv(
            "REFERENCE_AUDIO_STORAGE_PATH",
            "/opt/kasaai/storage/reference_audio"
        )

    async def initialize(self):
        """Initialize database and storage connections"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.database_name]
            
            # Create indexes
            await self._create_indexes()
        
        # Initialize storage backend if configured
        if self.storage_config and not self.storage_backend:
            try:
                self.storage_backend = HetznerStorageBox(
                    username=self.storage_config.get("username"),
                    password=self.storage_config.get("password"),
                    host=self.storage_config.get("host"),
                    base_path=self.storage_base_path
                )
                logger.info("Hetzner storage backend initialized for reference audio")
            except Exception as e:
                logger.warning(f"Failed to initialize Hetzner storage: {e}")

    async def _create_indexes(self):
        """Create database indexes"""
        collection = self.db.reference_audio
        
        # Create indexes
        await collection.create_index("reference_audio_id", unique=True)
        await collection.create_index("user_id")
        await collection.create_index("organization_id")
        await collection.create_index("created_at")
        await collection.create_index([("user_id", 1), ("created_at", -1)])

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def _generate_reference_audio_id(self) -> str:
        """Generate unique reference audio ID"""
        timestamp = datetime.utcnow().isoformat()
        random_bytes = os.urandom(8)
        hash_input = f"{timestamp}{random_bytes.hex()}".encode()
        hash_value = hashlib.sha256(hash_input).hexdigest()[:12]
        return f"ref_audio_{hash_value}"

    def _detect_audio_format(self, filename: str) -> AudioFormat:
        """Detect audio format from filename"""
        ext = Path(filename).suffix.lower().lstrip(".")
        try:
            return AudioFormat(ext)
        except ValueError:
            return AudioFormat.WAV  # Default

    async def _detect_duration(self, audio_bytes: bytes, format: AudioFormat) -> Optional[float]:
        """Detect audio duration using librosa"""
        try:
            import librosa
            import io
            
            audio_io = io.BytesIO(audio_bytes)
            y, sr = librosa.load(audio_io, sr=None)
            duration = len(y) / sr
            return duration
        except Exception as e:
            logger.warning(f"Failed to detect audio duration: {e}")
            return None

    async def _store_audio_file(
        self,
        audio_bytes: bytes,
        reference_audio_id: str,
        user_id: str,
        format: AudioFormat
    ) -> Tuple[Optional[str], Optional[str], bool]:
        """
        Store audio file in storage.

        Returns:
            (storage_path, audio_url, upload_success)
        """
        file_ext = f".{format.value}"
        filename = f"{reference_audio_id}{file_ext}"
        storage_path = f"{self.storage_base_path}/{user_id}/{filename}"
        
        # Ensure local directory exists
        local_dir = Path(self.local_storage_path) / user_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_file_path = local_dir / filename
        
        # Write to local storage
        try:
            with open(local_file_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Stored reference audio locally: {local_file_path}")
        except Exception as e:
            logger.error(f"Failed to store reference audio locally: {e}")
            return None, None, False
        
        # Try to upload to Hetzner storage if available
        upload_success = False
        if self.storage_backend:
            try:
                await self.storage_backend.upload_file(
                    file_path=storage_path,
                    file_data=audio_bytes
                )
                upload_success = True
                logger.info(f"Uploaded reference audio to Hetzner: {storage_path}")
            except Exception as e:
                logger.warning(f"Failed to upload to Hetzner storage: {e}")
        
        # Generate URL (will be served via API endpoint)
        audio_url = f"/api/v1/reference-audio/{reference_audio_id}/audio"
        
        return storage_path, audio_url, True

    async def create_reference_audio(
        self,
        audio_data: ReferenceAudioCreate,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> ReferenceAudio:
        """
        Create a new reference audio entry.

        Args:
            audio_data: Reference audio creation data
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Created ReferenceAudio
        """
        await self.initialize()
        
        # Generate ID
        reference_audio_id = self._generate_reference_audio_id()
        
        # Detect format
        format = self._detect_audio_format(audio_data.audio_filename)
        
        # Validate file size
        if len(audio_data.audio_bytes) > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit")
        
        # Detect duration
        duration_seconds = await self._detect_duration(audio_data.audio_bytes, format)
        
        # Store file
        storage_path, audio_url, upload_success = await self._store_audio_file(
            audio_bytes=audio_data.audio_bytes,
            reference_audio_id=reference_audio_id,
            user_id=user_id,
            format=format
        )
        
        if not upload_success:
            raise ValueError("Failed to store reference audio file")
        
        # Create document
        doc = {
            "reference_audio_id": reference_audio_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "name": audio_data.name,
            "description": audio_data.description,
            "audio_url": audio_url,
            "storage_path": storage_path,
            "file_size_bytes": len(audio_data.audio_bytes),
            "duration_seconds": duration_seconds,
            "format": format.value,
            "compatible_providers": ZERO_SHOT_PROVIDERS,
            "voice_id": None,  # Will be set if voice is created
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into database
        await self.db.reference_audio.insert_one(doc)
        
        logger.info(f"Created reference audio: {reference_audio_id} by user {user_id}")
        
        return ReferenceAudio(**doc)

    async def get_reference_audio(
        self,
        reference_audio_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ReferenceAudio]:
        """Get reference audio by ID"""
        await self.initialize()
        
        query = {"reference_audio_id": reference_audio_id}
        if user_id:
            query["user_id"] = user_id
        
        doc = await self.db.reference_audio.find_one(query)
        if not doc:
            return None
        
        return ReferenceAudio(**doc)

    async def list_reference_audio(
        self,
        filters: Optional[ReferenceAudioFilters] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ReferenceAudio], int]:
        """
        List reference audio with filtering.

        Returns:
            (list of ReferenceAudio, total count)
        """
        await self.initialize()
        
        query = {}
        
        if filters:
            if filters.user_id:
                query["user_id"] = filters.user_id
            if filters.organization_id:
                query["organization_id"] = filters.organization_id
            if filters.search:
                query["$or"] = [
                    {"name": {"$regex": filters.search, "$options": "i"}},
                    {"description": {"$regex": filters.search, "$options": "i"}}
                ]
            if filters.compatible_provider:
                query["compatible_providers"] = filters.compatible_provider
        
        # Get total count
        total = await self.db.reference_audio.count_documents(query)
        
        # Get documents
        cursor = self.db.reference_audio.find(query).sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        return [ReferenceAudio(**doc) for doc in docs], total

    async def update_reference_audio(
        self,
        reference_audio_id: str,
        updates: ReferenceAudioUpdate,
        user_id: str
    ) -> Optional[ReferenceAudio]:
        """Update reference audio"""
        await self.initialize()
        
        update_dict = {}
        if updates.name is not None:
            update_dict["name"] = updates.name
        if updates.description is not None:
            update_dict["description"] = updates.description
        
        if not update_dict:
            return await self.get_reference_audio(reference_audio_id, user_id)
        
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await self.db.reference_audio.update_one(
            {"reference_audio_id": reference_audio_id, "user_id": user_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_reference_audio(reference_audio_id, user_id)

    async def delete_reference_audio(
        self,
        reference_audio_id: str,
        user_id: str
    ) -> bool:
        """Delete reference audio"""
        await self.initialize()
        
        # Get reference audio to get storage path
        ref_audio = await self.get_reference_audio(reference_audio_id, user_id)
        if not ref_audio:
            return False
        
        # Delete from database
        result = await self.db.reference_audio.delete_one({
            "reference_audio_id": reference_audio_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            return False
        
        # Delete file from local storage
        if ref_audio.storage_path:
            parts = ref_audio.storage_path.split("/")
            if len(parts) >= 3:
                user_id_from_path = parts[1]
                filename = parts[2]
                local_file_path = Path(self.local_storage_path) / user_id_from_path / filename
                try:
                    if local_file_path.exists():
                        local_file_path.unlink()
                        logger.info(f"Deleted local reference audio file: {local_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete local file: {e}")
        
        # Delete from Hetzner storage if available
        if self.storage_backend and ref_audio.storage_path:
            try:
                await self.storage_backend.delete_file(ref_audio.storage_path)
                logger.info(f"Deleted reference audio from Hetzner: {ref_audio.storage_path}")
            except Exception as e:
                logger.warning(f"Failed to delete from Hetzner storage: {e}")
        
        logger.info(f"Deleted reference audio: {reference_audio_id}")
        return True

    async def get_audio_file_bytes(
        self,
        reference_audio_id: str,
        user_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Get audio file bytes"""
        ref_audio = await self.get_reference_audio(reference_audio_id, user_id)
        if not ref_audio or not ref_audio.storage_path:
            return None
        
        # Try to load from local storage
        parts = ref_audio.storage_path.split("/")
        if len(parts) >= 3:
            user_id_from_path = parts[1]
            filename = parts[2]
            local_file_path = Path(self.local_storage_path) / user_id_from_path / filename
            
            if local_file_path.exists():
                with open(local_file_path, "rb") as f:
                    return f.read()
        
        # Try to load from Hetzner storage
        if self.storage_backend:
            try:
                return await self.storage_backend.download_file(ref_audio.storage_path)
            except Exception as e:
                logger.warning(f"Failed to download from Hetzner: {e}")
        
        return None


# ==================== Global Service Instance ====================

_service_instance: Optional[ReferenceAudioService] = None


def get_reference_audio_service(
    mongodb_url: str = None,
    database_name: str = "kasaai_core",
    storage_config: Dict[str, Any] = None,
    storage_base_path: str = "reference_audio"
) -> ReferenceAudioService:
    """
    Get or create global reference audio service instance.

    Args:
        mongodb_url: MongoDB connection URL
        database_name: Database name
        storage_config: Hetzner storage configuration
        storage_base_path: Base path for storage (app-specific)

    Returns:
        ReferenceAudioService instance
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = ReferenceAudioService(
            mongodb_url=mongodb_url,
            database_name=database_name,
            storage_config=storage_config,
            storage_base_path=storage_base_path
        )
    
    return _service_instance





"""
Centralized Voice Library Service

Provides unified voice management across all KasaAI applications:
- InkWave (audiobook narration)
- ChurchFlow (announcements, greetings)
- StudyFlow (tutoring voices)
- EventFlow (event announcements)
- Core Backend (TTS services)

Features:
- Voice CRUD operations (create, read, update, delete)
- Voice search and filtering
- Access control (public/organization/private)
- Analytics and usage tracking
- Storage management (local + Hetzner backup)
- Voice versioning
- Favorites and ratings

Author: AI Labs Africa
Created: November 8, 2025
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

# Import storage services
from apps.shared.storage.hetzner_storage_box import HetznerStorageBox


logger = logging.getLogger(__name__)


# ==================== Enums ====================

class VoiceVisibility(str, Enum):
    """Voice visibility levels"""
    PUBLIC = "public"  # Available to all users
    ORGANIZATION = "organization"  # Available to organization members
    PRIVATE = "private"  # Only owner can access
    RESTRICTED = "restricted"  # Specific users only


class VoiceStatus(str, Enum):
    """Voice processing status"""
    ACTIVE = "active"
    PROCESSING = "processing"
    ARCHIVED = "archived"
    DELETED = "deleted"
    FAILED = "failed"


class VoiceGender(str, Enum):
    """Voice gender categories"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"


# ==================== Data Models ====================

class AudioFile(BaseModel):
    """Audio file metadata"""
    path: str = Field(..., description="File path (local or cloud)")
    url: Optional[str] = Field(None, description="Public URL (if available)")
    size: int = Field(..., description="File size in bytes")
    format: AudioFormat = Field(..., description="Audio format")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    sample_rate: Optional[int] = Field(None, description="Sample rate in Hz")
    bit_depth: Optional[int] = Field(None, description="Bit depth (e.g., 16, 24)")
    channels: Optional[int] = Field(1, description="Number of channels (1=mono, 2=stereo)")
    checksum: Optional[str] = Field(None, description="File checksum (MD5)")


class VoiceFiles(BaseModel):
    """Collection of voice audio files"""
    reference: Optional[AudioFile] = Field(None, description="Reference audio for cloning")
    preview: Optional[AudioFile] = Field(None, description="Short preview (5-10s)")
    full: Optional[AudioFile] = Field(None, description="Full recording")


class VoiceCharacteristics(BaseModel):
    """Voice characteristics and metadata"""
    gender: VoiceGender = Field(VoiceGender.UNKNOWN, description="Voice gender")
    age_range: Optional[str] = Field(None, description="Age range (child, young_adult, adult, senior)")
    accent: Optional[str] = Field(None, description="Accent (e.g., American, British, Ghanaian)")
    language: str = Field("en", description="Primary language code (ISO 639-1)")
    dialect: Optional[str] = Field(None, description="Language dialect")
    tone: Optional[str] = Field(None, description="Voice tone (friendly, professional, authoritative)")
    pace: Optional[str] = Field(None, description="Speaking pace (slow, medium, fast)")


class VoiceTechnical(BaseModel):
    """Technical details and capabilities"""
    compatible_providers: List[str] = Field(
        default_factory=list,
        description="Compatible TTS providers (coqui_xtts, f5tts, styletts2, etc.)"
    )
    quality_score: Optional[float] = Field(None, description="Quality score (0-100)", ge=0, le=100)
    cloning_difficulty: Optional[str] = Field(None, description="Cloning difficulty (easy, medium, hard)")
    trained_models: List[str] = Field(default_factory=list, description="Pre-trained model IDs")


class VoiceOwner(BaseModel):
    """Voice ownership information"""
    user_id: str = Field(..., description="Owner user ID")
    organization_id: Optional[str] = Field(None, description="Owner organization ID")
    uploaded_by: Optional[str] = Field(None, description="Uploader user ID (if different)")
    upload_source: Optional[str] = Field(None, description="Upload source (web, api, import)")


class VoiceAccess(BaseModel):
    """Access control configuration"""
    visibility: VoiceVisibility = Field(VoiceVisibility.PRIVATE, description="Visibility level")
    allowed_users: List[str] = Field(default_factory=list, description="Allowed user IDs")
    allowed_orgs: List[str] = Field(default_factory=list, description="Allowed organization IDs")
    license: Optional[str] = Field(None, description="License type (commercial, personal, restricted)")


class VoiceMetadata(BaseModel):
    """Discovery and organization metadata"""
    tags: List[str] = Field(default_factory=list, description="Search tags")
    categories: List[str] = Field(default_factory=list, description="Categories (professional, casual, narration)")
    use_cases: List[str] = Field(default_factory=list, description="Use cases (audiobook, customer_service)")
    featured: bool = Field(False, description="Featured voice")
    verified: bool = Field(False, description="Verified by admin")


class VoiceStats(BaseModel):
    """Usage statistics"""
    views: int = Field(0, description="Number of views")
    uses: int = Field(0, description="Number of uses")
    favorites: int = Field(0, description="Number of favorites")
    rating: float = Field(0.0, description="Average rating (0-5)", ge=0, le=5)
    ratings_count: int = Field(0, description="Number of ratings")


class ProcessingStatus(BaseModel):
    """Processing status details"""
    stage: Optional[str] = Field(None, description="Current processing stage")
    progress: int = Field(0, description="Progress percentage (0-100)", ge=0, le=100)
    error: Optional[str] = Field(None, description="Error message if failed")


class Voice(BaseModel):
    """Complete voice model"""
    voice_id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Voice description")

    # Audio files
    files: VoiceFiles = Field(default_factory=VoiceFiles, description="Audio files")

    # Voice properties
    characteristics: VoiceCharacteristics = Field(
        default_factory=VoiceCharacteristics,
        description="Voice characteristics"
    )
    technical: VoiceTechnical = Field(
        default_factory=VoiceTechnical,
        description="Technical details"
    )

    # Ownership and access
    owner: VoiceOwner = Field(..., description="Ownership info")
    access: VoiceAccess = Field(
        default_factory=VoiceAccess,
        description="Access control"
    )

    # Discovery
    metadata: VoiceMetadata = Field(
        default_factory=VoiceMetadata,
        description="Metadata for discovery"
    )

    # Analytics
    stats: VoiceStats = Field(
        default_factory=VoiceStats,
        description="Usage statistics"
    )

    # Versioning
    version: str = Field("1.0.0", description="Version string")
    parent_voice_id: Optional[str] = Field(None, description="Parent voice ID for versioning")
    version_history: List[str] = Field(default_factory=list, description="Version history")

    # Status
    status: VoiceStatus = Field(VoiceStatus.ACTIVE, description="Voice status")
    processing_status: Optional[ProcessingStatus] = Field(
        None,
        description="Processing status"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class VoiceCreate(BaseModel):
    """Request to create a new voice"""
    name: str = Field(..., description="Voice name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Voice description", max_length=500)
    characteristics: Optional[VoiceCharacteristics] = None
    access: Optional[VoiceAccess] = None
    metadata: Optional[VoiceMetadata] = None


class VoiceUpdate(BaseModel):
    """Request to update a voice"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    characteristics: Optional[VoiceCharacteristics] = None
    access: Optional[VoiceAccess] = None
    metadata: Optional[VoiceMetadata] = None
    status: Optional[VoiceStatus] = None


class VoiceFilters(BaseModel):
    """Filters for voice search"""
    search: Optional[str] = Field(None, description="Search query (name, description, tags)")
    gender: Optional[VoiceGender] = None
    language: Optional[str] = None
    accent: Optional[str] = None
    visibility: Optional[VoiceVisibility] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    featured: Optional[bool] = None
    verified: Optional[bool] = None
    status: Optional[VoiceStatus] = Field(VoiceStatus.ACTIVE, description="Default to active voices")
    owner_id: Optional[str] = None
    organization_id: Optional[str] = None


class Pagination(BaseModel):
    """Pagination parameters"""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: int = Field(-1, description="Sort order (1=asc, -1=desc)")


class VoiceList(BaseModel):
    """List of voices with pagination"""
    voices: List[Voice]
    total: int
    skip: int
    limit: int


# ==================== Service ====================

class VoiceLibraryService:
    """Centralized voice library management service"""

    def __init__(
        self,
        mongodb_url: str = None,
        database_name: str = "kasaai_core",
        storage_config: Dict[str, Any] = None
    ):
        """
        Initialize Voice Library Service.

        Args:
            mongodb_url: MongoDB connection URL
            database_name: Database name
            storage_config: Hetzner storage configuration
        """
        self.mongodb_url = mongodb_url or os.getenv("MONGODB_URL")
        self.database_name = database_name

        # MongoDB client (lazy initialization)
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

        # Storage service
        self.storage_config = storage_config or {
            "username": os.getenv("HETZNER_STORAGE_USERNAME"),
            "password": os.getenv("HETZNER_STORAGE_PASSWORD"),
            "host": os.getenv("HETZNER_STORAGE_HOST"),
            "base_path": "kasaai/voices"
        }
        self._storage: Optional[HetznerStorageBox] = None

        # Local storage path
        self.local_storage_path = Path("/opt/kasaai/apps/voice-lab/voices")
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"VoiceLibraryService initialized for database: {database_name}")

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database (lazy initialization)"""
        if self._db is None:
            self._client = AsyncIOMotorClient(self.mongodb_url)
            self._db = self._client[self.database_name]
        return self._db

    @property
    def collection(self):
        """Get voices collection"""
        return self.db["voice_library"]

    @property
    def usage_logs_collection(self):
        """Get voice usage logs collection"""
        return self.db["voice_usage_logs"]

    @property
    def favorites_collection(self):
        """Get voice favorites collection"""
        return self.db["voice_favorites"]

    @property
    def ratings_collection(self):
        """Get voice ratings collection"""
        return self.db["voice_ratings"]

    @property
    def storage(self) -> HetznerStorageBox:
        """Get storage service (lazy initialization)"""
        if self._storage is None:
            self._storage = HetznerStorageBox(**self.storage_config)
        return self._storage

    # ==================== Initialization ====================

    async def initialize(self):
        """Initialize database indexes and collections"""
        try:
            # Create indexes for voice_library
            await self.collection.create_index("voice_id", unique=True)
            await self.collection.create_index("name")
            await self.collection.create_index("characteristics.gender")
            await self.collection.create_index("characteristics.language")
            await self.collection.create_index("characteristics.accent")
            await self.collection.create_index("access.visibility")
            await self.collection.create_index("metadata.tags")
            await self.collection.create_index("metadata.categories")
            await self.collection.create_index("metadata.use_cases")
            await self.collection.create_index("metadata.featured")
            await self.collection.create_index("metadata.verified")
            await self.collection.create_index("status")
            await self.collection.create_index("owner.user_id")
            await self.collection.create_index("owner.organization_id")
            await self.collection.create_index("created_at")
            await self.collection.create_index("updated_at")
            await self.collection.create_index([("name", "text"), ("description", "text")])

            # Create indexes for voice_usage_logs
            await self.usage_logs_collection.create_index("voice_id")
            await self.usage_logs_collection.create_index("user_id")
            await self.usage_logs_collection.create_index("organization_id")
            await self.usage_logs_collection.create_index("timestamp")
            await self.usage_logs_collection.create_index([("voice_id", 1), ("timestamp", -1)])

            # Create indexes for voice_favorites
            await self.favorites_collection.create_index([("user_id", 1), ("voice_id", 1)], unique=True)
            await self.favorites_collection.create_index("voice_id")
            await self.favorites_collection.create_index("user_id")

            # Create indexes for voice_ratings
            await self.ratings_collection.create_index([("voice_id", 1), ("user_id", 1)], unique=True)
            await self.ratings_collection.create_index("voice_id")
            await self.ratings_collection.create_index("rating")

            logger.info("VoiceLibraryService indexes created successfully")

            # Connect to Hetzner Storage Box
            if self.storage_config.get("password"):
                try:
                    await self.storage.connect()
                    logger.info("✅ Connected to Hetzner Storage Box for voice backups")
                except Exception as e:
                    logger.warning(f"⚠️ Could not connect to Hetzner Storage Box: {e}")
                    logger.warning("Voice backups will be disabled")
            else:
                logger.info("Hetzner Storage Box credentials not configured, backups disabled")

        except Exception as e:
            logger.error(f"Error initializing VoiceLibraryService: {e}", exc_info=True)
            raise

    # ==================== CRUD Operations ====================

    async def create_voice(
        self,
        voice_data: VoiceCreate,
        audio_file: Optional[bytes] = None,
        audio_filename: Optional[str] = None,
        user_id: str = None,
        organization_id: Optional[str] = None
    ) -> Voice:
        """
        Create a new voice.

        Args:
            voice_data: Voice creation data
            audio_file: Audio file bytes
            audio_filename: Original filename
            user_id: Owner user ID
            organization_id: Owner organization ID

        Returns:
            Created voice
        """
        try:
            # Generate voice ID
            voice_id = self._generate_voice_id(voice_data.name)

            # Create voice object
            voice = Voice(
                voice_id=voice_id,
                name=voice_data.name,
                description=voice_data.description,
                characteristics=voice_data.characteristics or VoiceCharacteristics(),
                access=voice_data.access or VoiceAccess(),
                metadata=voice_data.metadata or VoiceMetadata(),
                owner=VoiceOwner(
                    user_id=user_id,
                    organization_id=organization_id,
                    uploaded_by=user_id,
                    upload_source="api"
                )
            )

            # Handle audio file if provided
            if audio_file and audio_filename:
                audio_file_info = await self._store_audio_file(
                    voice_id=voice_id,
                    audio_file=audio_file,
                    filename=audio_filename,
                    file_type="reference"
                )
                voice.files.reference = audio_file_info

                # Generate preview (5-10 seconds)
                # TODO: Implement audio trimming

            # Insert into database
            voice_dict = voice.dict(by_alias=True)
            voice_dict["created_at"] = datetime.utcnow()
            voice_dict["updated_at"] = datetime.utcnow()

            result = await self.collection.insert_one(voice_dict)

            logger.info(f"Created voice: {voice_id}")

            return voice

        except Exception as e:
            logger.error(f"Error creating voice: {e}", exc_info=True)
            raise

    async def get_voice(self, voice_id: str, user_id: Optional[str] = None) -> Optional[Voice]:
        """
        Get a voice by ID.

        Args:
            voice_id: Voice identifier
            user_id: Requesting user ID (for access control)

        Returns:
            Voice if found and accessible, None otherwise
        """
        try:
            voice_dict = await self.collection.find_one({"voice_id": voice_id})

            if not voice_dict:
                return None

            voice = Voice(**voice_dict)

            # Check access
            if not await self._check_access(voice, user_id):
                logger.warning(f"User {user_id} denied access to voice {voice_id}")
                return None

            # Increment view count
            await self.collection.update_one(
                {"voice_id": voice_id},
                {"$inc": {"stats.views": 1}}
            )

            return voice

        except Exception as e:
            logger.error(f"Error getting voice {voice_id}: {e}", exc_info=True)
            raise

    async def list_voices(
        self,
        filters: VoiceFilters = None,
        pagination: Pagination = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> VoiceList:
        """
        List voices with filtering and pagination.

        Args:
            filters: Filter criteria
            pagination: Pagination parameters
            user_id: Requesting user ID
            organization_id: Requesting user's organization ID

        Returns:
            List of voices
        """
        try:
            filters = filters or VoiceFilters()
            pagination = pagination or Pagination()

            # Build query
            query = await self._build_query(filters, user_id, organization_id)

            # Get total count
            total = await self.collection.count_documents(query)

            # Get voices
            cursor = self.collection.find(query)
            cursor = cursor.sort(pagination.sort_by, pagination.sort_order)
            cursor = cursor.skip(pagination.skip).limit(pagination.limit)

            voices = []
            async for voice_dict in cursor:
                try:
                    voice = Voice(**voice_dict)
                    voices.append(voice)
                except Exception as e:
                    logger.error(f"Error parsing voice: {e}")
                    continue

            return VoiceList(
                voices=voices,
                total=total,
                skip=pagination.skip,
                limit=pagination.limit
            )

        except Exception as e:
            logger.error(f"Error listing voices: {e}", exc_info=True)
            raise

    async def update_voice(
        self,
        voice_id: str,
        updates: VoiceUpdate,
        user_id: str
    ) -> Optional[Voice]:
        """
        Update a voice.

        Args:
            voice_id: Voice identifier
            updates: Update data
            user_id: User making the update

        Returns:
            Updated voice or None if not found/no access
        """
        try:
            # Get existing voice
            voice = await self.get_voice(voice_id, user_id)
            if not voice:
                return None

            # Check ownership
            if voice.owner.user_id != user_id:
                logger.warning(f"User {user_id} not authorized to update voice {voice_id}")
                return None

            # Build update dict
            update_dict = {}
            if updates.name is not None:
                update_dict["name"] = updates.name
            if updates.description is not None:
                update_dict["description"] = updates.description
            if updates.characteristics is not None:
                update_dict["characteristics"] = updates.characteristics.dict()
            if updates.access is not None:
                update_dict["access"] = updates.access.dict()
            if updates.metadata is not None:
                update_dict["metadata"] = updates.metadata.dict()
            if updates.status is not None:
                update_dict["status"] = updates.status.value

            update_dict["updated_at"] = datetime.utcnow()

            # Update in database
            result = await self.collection.update_one(
                {"voice_id": voice_id},
                {"$set": update_dict}
            )

            if result.modified_count == 0:
                logger.warning(f"No changes made to voice {voice_id}")

            # Return updated voice
            return await self.get_voice(voice_id, user_id)

        except Exception as e:
            logger.error(f"Error updating voice {voice_id}: {e}", exc_info=True)
            raise

    async def delete_voice(
        self,
        voice_id: str,
        user_id: str,
        soft_delete: bool = True,
        delete_files: bool = False
    ) -> bool:
        """
        Delete a voice.

        Args:
            voice_id: Voice identifier
            user_id: User requesting deletion
            soft_delete: If True, mark as deleted; if False, remove from DB
            delete_files: If True, delete associated files

        Returns:
            True if deleted successfully
        """
        try:
            # Get voice
            voice = await self.get_voice(voice_id, user_id)
            if not voice:
                return False

            # Check ownership
            if voice.owner.user_id != user_id:
                logger.warning(f"User {user_id} not authorized to delete voice {voice_id}")
                return False

            if soft_delete:
                # Mark as deleted
                await self.collection.update_one(
                    {"voice_id": voice_id},
                    {
                        "$set": {
                            "status": VoiceStatus.DELETED.value,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Soft deleted voice: {voice_id}")
            else:
                # Remove from database
                await self.collection.delete_one({"voice_id": voice_id})
                logger.info(f"Hard deleted voice: {voice_id}")

            # Delete files if requested
            if delete_files:
                await self._delete_voice_files(voice)

            return True

        except Exception as e:
            logger.error(f"Error deleting voice {voice_id}: {e}", exc_info=True)
            raise

    # ==================== Helper Methods ====================

    def _generate_voice_id(self, name: str) -> str:
        """Generate unique voice ID from name"""
        # Clean name
        clean_name = name.lower().replace(" ", "_")
        clean_name = "".join(c for c in clean_name if c.isalnum() or c == "_")

        # Add timestamp suffix for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        return f"{clean_name}_{timestamp}"

    async def _store_audio_file(
        self,
        voice_id: str,
        audio_file: bytes,
        filename: str,
        file_type: str  # reference, preview, full
    ) -> AudioFile:
        """Store audio file locally and in cloud"""
        try:
            # Determine file extension
            ext = Path(filename).suffix.lower().lstrip(".")
            audio_format = AudioFormat(ext) if ext in [f.value for f in AudioFormat] else AudioFormat.WAV

            # Generate filename
            new_filename = f"{voice_id}_{file_type}.{audio_format.value}"

            # Store locally
            local_path = self.local_storage_path / new_filename
            with open(local_path, "wb") as f:
                f.write(audio_file)

            # Calculate checksum
            checksum = hashlib.md5(audio_file).hexdigest()

            # TODO: Extract audio metadata (duration, sample_rate, bit_depth)
            # For now, use defaults

            # Store in Hetzner Storage Box (async backup)
            cloud_path = f"{file_type}/{new_filename}"
            cloud_url = None

            if self._storage and self._storage.connected:
                try:
                    await self.storage.upload_file(
                        local_path=str(local_path),
                        remote_path=cloud_path,
                        overwrite=True
                    )
                    logger.info(f"✅ Backed up voice file to Hetzner: {cloud_path}")

                    # Generate cloud URL (for WebDAV access)
                    cloud_url = f"https://{self.storage.host}/{self.storage.base_path}/{cloud_path}".replace("//", "/")

                except Exception as e:
                    logger.warning(f"⚠️ Failed to backup voice file to Hetzner: {e}")
                    # Continue without cloud backup - local storage is primary
            else:
                logger.debug("Hetzner storage not connected, skipping cloud backup")

            return AudioFile(
                path=str(local_path),
                url=cloud_url,
                size=len(audio_file),
                format=audio_format,
                duration=None,
                sample_rate=None,
                bit_depth=None,
                channels=1,
                checksum=checksum
            )

        except Exception as e:
            logger.error(f"Error storing audio file: {e}", exc_info=True)
            raise

    async def _delete_voice_files(self, voice: Voice):
        """Delete all files associated with a voice"""
        try:
            files_to_delete = []

            if voice.files.reference:
                files_to_delete.append(("reference", voice.files.reference.path))
            if voice.files.preview:
                files_to_delete.append(("preview", voice.files.preview.path))
            if voice.files.full:
                files_to_delete.append(("full", voice.files.full.path))

            for file_type, file_path in files_to_delete:
                # Delete local file
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"✅ Deleted local file: {file_path}")

                # Delete from Hetzner Storage Box
                if self._storage and self._storage.connected:
                    try:
                        # Extract filename from path
                        filename = Path(file_path).name
                        cloud_path = f"{file_type}/{filename}"

                        await self.storage.delete_file(cloud_path)
                        logger.info(f"✅ Deleted Hetzner backup: {cloud_path}")

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to delete Hetzner backup {cloud_path}: {e}")
                        # Continue - local deletion is what matters

        except Exception as e:
            logger.error(f"Error deleting voice files: {e}", exc_info=True)

    async def restore_voice_files(self, voice_id: str) -> Dict[str, bool]:
        """
        Restore voice files from Hetzner Storage Box backup.

        Args:
            voice_id: Voice identifier

        Returns:
            Dictionary with restore status for each file type
        """
        try:
            # Get voice metadata
            voice = await self.get_voice(voice_id)
            if not voice:
                raise ValueError(f"Voice {voice_id} not found")

            if not self._storage or not self._storage.connected:
                raise ValueError("Hetzner storage not connected")

            restore_status = {}
            file_types = []

            # Check which files need restoration
            if voice.files.reference:
                file_types.append(("reference", voice.files.reference.path))
            if voice.files.preview:
                file_types.append(("preview", voice.files.preview.path))
            if voice.files.full:
                file_types.append(("full", voice.files.full.path))

            for file_type, local_path in file_types:
                try:
                    # Check if local file exists
                    path = Path(local_path)
                    if path.exists():
                        logger.info(f"Local file already exists: {local_path}")
                        restore_status[file_type] = True
                        continue

                    # Download from Hetzner
                    filename = path.name
                    cloud_path = f"{file_type}/{filename}"

                    await self.storage.download_file(
                        remote_path=cloud_path,
                        local_path=local_path,
                        overwrite=True
                    )

                    logger.info(f"✅ Restored voice file from Hetzner: {cloud_path} -> {local_path}")
                    restore_status[file_type] = True

                except Exception as e:
                    logger.error(f"❌ Failed to restore {file_type} file: {e}")
                    restore_status[file_type] = False

            return restore_status

        except Exception as e:
            logger.error(f"Error restoring voice files: {e}", exc_info=True)
            raise

    async def _check_access(self, voice: Voice, user_id: Optional[str]) -> bool:
        """Check if user has access to voice"""
        # Public voices are accessible to all
        if voice.access.visibility == VoiceVisibility.PUBLIC:
            return True

        # No user ID provided
        if not user_id:
            return False

        # Owner always has access
        if voice.owner.user_id == user_id:
            return True

        # Check specific user access
        if user_id in voice.access.allowed_users:
            return True

        # TODO: Check organization access

        return False

    # ==================== Favorites ====================

    async def get_user_favorites(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Voice]:
        """
        Get user's favorite voices.

        Args:
            user_id: User ID
            skip: Number of items to skip
            limit: Number of items to return

        Returns:
            List of favorite voices
        """
        try:
            # Get favorite voice IDs
            cursor = self.favorites_collection.find({"user_id": user_id})
            cursor = cursor.skip(skip).limit(limit)

            voice_ids = []
            async for fav in cursor:
                voice_ids.append(fav["voice_id"])

            if not voice_ids:
                return []

            # Get voice details
            voices = []
            async for voice_dict in self.collection.find({"voice_id": {"$in": voice_ids}}):
                try:
                    voice = Voice(**voice_dict)
                    voices.append(voice)
                except Exception as e:
                    logger.error(f"Error parsing favorite voice: {e}")
                    continue

            return voices

        except Exception as e:
            logger.error(f"Error getting user favorites: {e}", exc_info=True)
            raise

    async def add_to_favorites(self, user_id: str, voice_id: str) -> bool:
        """
        Add a voice to user's favorites.

        Args:
            user_id: User ID
            voice_id: Voice ID

        Returns:
            True if added successfully
        """
        try:
            # Check if voice exists
            voice = await self.collection.find_one({"voice_id": voice_id})
            if not voice:
                logger.warning(f"Voice {voice_id} not found")
                return False

            # Add to favorites (upsert to avoid duplicates)
            await self.favorites_collection.update_one(
                {"user_id": user_id, "voice_id": voice_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "voice_id": voice_id,
                        "added_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

            # Increment favorites count
            await self.collection.update_one(
                {"voice_id": voice_id},
                {"$inc": {"stats.favorites": 1}}
            )

            logger.info(f"User {user_id} added voice {voice_id} to favorites")
            return True

        except Exception as e:
            logger.error(f"Error adding to favorites: {e}", exc_info=True)
            raise

    async def remove_from_favorites(self, user_id: str, voice_id: str) -> bool:
        """
        Remove a voice from user's favorites.

        Args:
            user_id: User ID
            voice_id: Voice ID

        Returns:
            True if removed successfully
        """
        try:
            result = await self.favorites_collection.delete_one({
                "user_id": user_id,
                "voice_id": voice_id
            })

            if result.deleted_count > 0:
                # Decrement favorites count
                await self.collection.update_one(
                    {"voice_id": voice_id},
                    {"$inc": {"stats.favorites": -1}}
                )
                logger.info(f"User {user_id} removed voice {voice_id} from favorites")
                return True

            return False

        except Exception as e:
            logger.error(f"Error removing from favorites: {e}", exc_info=True)
            raise

    # ==================== Ratings ====================

    async def rate_voice(
        self,
        user_id: str,
        voice_id: str,
        rating: int,
        review: Optional[str] = None
    ) -> bool:
        """
        Rate a voice.

        Args:
            user_id: User ID
            voice_id: Voice ID
            rating: Rating (1-5)
            review: Optional review text

        Returns:
            True if rated successfully
        """
        try:
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be between 1 and 5")

            # Check if voice exists
            voice = await self.collection.find_one({"voice_id": voice_id})
            if not voice:
                logger.warning(f"Voice {voice_id} not found")
                return False

            # Check if user already rated
            existing = await self.ratings_collection.find_one({
                "user_id": user_id,
                "voice_id": voice_id
            })

            # Upsert rating
            await self.ratings_collection.update_one(
                {"user_id": user_id, "voice_id": voice_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "voice_id": voice_id,
                        "rating": rating,
                        "review": review,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )

            # Recalculate average rating
            pipeline = [
                {"$match": {"voice_id": voice_id}},
                {"$group": {
                    "_id": "$voice_id",
                    "average": {"$avg": "$rating"},
                    "count": {"$sum": 1}
                }}
            ]
            result = await self.ratings_collection.aggregate(pipeline).to_list(1)

            if result:
                avg_rating = result[0]["average"]
                ratings_count = result[0]["count"]

                await self.collection.update_one(
                    {"voice_id": voice_id},
                    {
                        "$set": {
                            "stats.rating": round(avg_rating, 2),
                            "stats.ratings_count": ratings_count
                        }
                    }
                )

            logger.info(f"User {user_id} rated voice {voice_id}: {rating}")
            return True

        except Exception as e:
            logger.error(f"Error rating voice: {e}", exc_info=True)
            raise

    # ==================== Usage Tracking ====================

    async def record_usage(
        self,
        voice_id: str,
        user_id: str,
        organization_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record voice usage for analytics.

        Args:
            voice_id: Voice ID
            user_id: User ID
            organization_id: Organization ID
            context: Additional context (app, use_case, etc.)

        Returns:
            True if recorded successfully
        """
        try:
            # Insert usage log
            await self.usage_logs_collection.insert_one({
                "voice_id": voice_id,
                "user_id": user_id,
                "organization_id": organization_id,
                "context": context or {},
                "timestamp": datetime.utcnow()
            })

            # Increment usage count
            await self.collection.update_one(
                {"voice_id": voice_id},
                {
                    "$inc": {"stats.uses": 1},
                    "$set": {"last_used_at": datetime.utcnow()}
                }
            )

            logger.debug(f"Recorded usage for voice {voice_id} by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording usage: {e}", exc_info=True)
            # Don't raise - usage tracking shouldn't fail the request
            return False

    # ==================== Query Building ====================

    async def _build_query(
        self,
        filters: VoiceFilters,
        user_id: Optional[str],
        organization_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        query = {}

        # Status filter
        if filters.status:
            query["status"] = filters.status.value

        # Text search
        if filters.search:
            query["$text"] = {"$search": filters.search}

        # Gender filter
        if filters.gender:
            query["characteristics.gender"] = filters.gender.value

        # Language filter
        if filters.language:
            query["characteristics.language"] = filters.language

        # Accent filter
        if filters.accent:
            query["characteristics.accent"] = filters.accent

        # Categories filter
        if filters.categories:
            query["metadata.categories"] = {"$in": filters.categories}

        # Tags filter
        if filters.tags:
            query["metadata.tags"] = {"$in": filters.tags}

        # Use cases filter
        if filters.use_cases:
            query["metadata.use_cases"] = {"$in": filters.use_cases}

        # Featured filter
        if filters.featured is not None:
            query["metadata.featured"] = filters.featured

        # Verified filter
        if filters.verified is not None:
            query["metadata.verified"] = filters.verified

        # Owner filter
        if filters.owner_id:
            query["owner.user_id"] = filters.owner_id

        # Organization filter
        if filters.organization_id:
            query["owner.organization_id"] = filters.organization_id

        # Access control
        if user_id:
            access_query = {
                "$or": [
                    {"access.visibility": VoiceVisibility.PUBLIC.value},
                    {"owner.user_id": user_id},
                    {"access.allowed_users": user_id}
                ]
            }

            if organization_id:
                access_query["$or"].append({
                    "$and": [
                        {"access.visibility": VoiceVisibility.ORGANIZATION.value},
                        {"owner.organization_id": organization_id}
                    ]
                })

            query = {"$and": [query, access_query]} if query else access_query
        else:
            # Only public voices for anonymous users
            query["access.visibility"] = VoiceVisibility.PUBLIC.value

        return query


# ==================== Singleton Instance ====================

_voice_library_service: Optional[VoiceLibraryService] = None


def get_voice_library_service() -> VoiceLibraryService:
    """Get or create voice library service singleton"""
    global _voice_library_service

    if _voice_library_service is None:
        _voice_library_service = VoiceLibraryService()

    return _voice_library_service

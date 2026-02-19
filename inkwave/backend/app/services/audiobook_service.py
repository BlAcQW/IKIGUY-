"""
Audiobook Service for InkWave.

Provides full audiobook narration using the Vapi TTS infrastructure (20+ TTS models).
Supports chunk-based streaming, voice cloning, and multiple provider fallback.

Author: AI Labs Africa
Created: November 26, 2025
"""

import os
import sys
import logging
import asyncio
import base64
from typing import Optional, Dict, List, AsyncGenerator, Tuple
from datetime import datetime
from enum import Enum

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from pydantic import BaseModel, Field
from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult,
    VoiceCloneRequest
)
from app.core.database import get_db
from app.services.tts_text_normalizer import get_tts_normalizer, TTSTextNormalizer

logger = logging.getLogger(__name__)


class AudiobookProvider(str, Enum):
    """Available audiobook TTS providers."""
    STYLETTS2 = "styletts2"      # Default - expressive, natural
    KOKORO = "kokoro"            # Fast, reliable fallback
    F5TTS = "f5tts"              # Voice cloning specialist
    MELOTTS = "melotts"          # Melodic quality
    OPENVOICE = "openvoice"      # Voice cloning
    COQUI_XTTS = "coqui_xtts"    # Multilingual
    OPENAI_TTS = "openai_tts"    # OpenAI TTS (alloy, echo, fable, onyx, nova, shimmer)
    OPENAI_TTS_HD = "openai_tts_hd"  # OpenAI TTS HD (higher quality)
    EDGE_TTS = "edge_tts"        # Microsoft Edge TTS (free, no GPU)


class AudioChunk(BaseModel):
    """Generated audio chunk data."""
    chunk_id: str
    chunk_index: int
    audio_base64: str
    audio_format: str = "mp3"
    duration: float
    text_length: int
    provider_used: str


class AudiobookGenerationRequest(BaseModel):
    """Request to generate audiobook narration."""
    book_id: str
    provider_id: str = Field(default="styletts2", description="TTS provider")
    voice_id: Optional[str] = Field(default=None, description="Voice ID for cloning")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    language: str = Field(default="en")
    start_chunk: int = Field(default=0, description="Starting chunk index")
    end_chunk: Optional[int] = Field(default=None, description="Ending chunk index (None = all)")
    use_voice_clone: bool = Field(default=False, description="Use voice cloning if available")


class AudiobookGenerationResult(BaseModel):
    """Result of audiobook generation."""
    book_id: str
    total_chunks: int
    successful_chunks: int
    failed_chunks: int
    total_duration: float
    total_cost: float
    provider_used: str
    audio_chunks: List[Dict]


class AudiobookService:
    """
    Audiobook narration service using Vapi TTS infrastructure.

    Provides:
    - Full book narration with 20+ TTS providers
    - Chunk-by-chunk streaming for real-time playback
    - Voice cloning for consistent narrator voice
    - Automatic fallback between providers
    - Audio caching to avoid regeneration

    Example:
        >>> service = AudiobookService()
        >>> await service.initialize()
        >>>
        >>> # Generate single chunk audio
        >>> audio = await service.generate_chunk_audio(
        ...     book_id="abc123",
        ...     chunk_index=0,
        ...     provider_id="styletts2"
        ... )
        >>>
        >>> # Stream entire book
        >>> async for chunk in service.stream_book_audio(book_id):
        ...     play_audio(chunk.audio_base64)
    """

    def __init__(
        self,
        default_provider: AudiobookProvider = AudiobookProvider.STYLETTS2,
        fallback_provider: AudiobookProvider = AudiobookProvider.KOKORO,
        enable_caching: bool = True,
        cache_ttl: int = 86400  # 24 hours
    ):
        """
        Initialize audiobook service.

        Args:
            default_provider: Primary TTS provider
            fallback_provider: Fallback if primary fails
            enable_caching: Cache generated audio
            cache_ttl: Cache TTL in seconds
        """
        self.default_provider = default_provider
        self.fallback_provider = fallback_provider
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

        # Services
        self.tts_webui: Optional[TTSWebUIService] = None
        self.tts_provider: Optional[TTSProviderService] = None
        self._initialized = False

        # Storage configuration
        self.storage_path = os.getenv(
            "AUDIOBOOK_STORAGE_PATH",
            "/opt/kasaai/apps/inkwave/backend/storage/audiobooks"
        )
        self.storage_base_url = os.getenv(
            "AUDIOBOOK_STORAGE_URL",
            "https://inkwave-api.ailabsafrica.com/storage/audiobooks"
        )

        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)

        # Statistics
        self.stats = {
            "total_chunks_generated": 0,
            "total_audio_seconds": 0.0,
            "cache_hits": 0,
            "fallback_used": 0
        }

    async def initialize(self) -> None:
        """
        Initialize TTS services.

        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Initialize TTS-WebUI service (direct access to 20+ models)
            self.tts_webui = TTSWebUIService()

            # Initialize TTSProviderService (billing integration)
            self.tts_provider = TTSProviderService(
                enable_billing=True,
                enable_health_monitoring=True,
                cache_ttl=300
            )
            await self.tts_provider.initialize()

            self._initialized = True
            logger.info(
                f"AudiobookService initialized with default={self.default_provider.value}, "
                f"fallback={self.fallback_provider.value}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize AudiobookService: {e}")
            raise

    async def get_available_providers(self) -> Dict:
        """
        Get available TTS providers for audiobook narration.

        Returns:
            Dict with provider info and capabilities
        """
        return {
            "styletts2": {
                "name": "StyleTTS2",
                "description": "Expressive, natural-sounding narration",
                "supports_cloning": True,
                "languages": ["en"],
                "recommended_for": ["novels", "stories", "narrative"]
            },
            "kokoro": {
                "name": "Kokoro",
                "description": "Fast, reliable synthesis",
                "supports_cloning": False,
                "languages": ["en", "ja", "ko", "zh"],
                "recommended_for": ["quick previews", "real-time"]
            },
            "f5tts": {
                "name": "F5-TTS",
                "description": "High-quality voice cloning",
                "supports_cloning": True,
                "languages": ["en", "zh"],
                "recommended_for": ["voice cloning", "consistency"]
            },
            "melotts": {
                "name": "MeloTTS",
                "description": "Melodic, musical quality",
                "supports_cloning": False,
                "languages": ["en", "zh", "es", "fr", "ja", "ko"],
                "recommended_for": ["poetry", "lyrical content"]
            },
            "openvoice": {
                "name": "OpenVoice",
                "description": "Voice cloning specialist",
                "supports_cloning": True,
                "languages": ["en", "zh"],
                "recommended_for": ["voice cloning", "character voices"]
            },
            "coqui_xtts": {
                "name": "Coqui XTTS",
                "description": "Multilingual with cloning",
                "supports_cloning": True,
                "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"],
                "recommended_for": ["multilingual books", "global content"]
            },
            "openai_tts": {
                "name": "OpenAI TTS",
                "description": "High-quality voices (alloy, echo, fable, onyx, nova, shimmer)",
                "supports_cloning": False,
                "languages": ["en"],
                "recommended_for": ["audiobooks", "professional narration"],
                "voices": {
                    "alloy": {"name": "Alloy", "description": "Balanced, neutral - great for general narration", "gender": "neutral"},
                    "echo": {"name": "Echo", "description": "Deep, warm - male protagonists, non-fiction", "gender": "male"},
                    "fable": {"name": "Fable", "description": "British, expressive - fiction, storytelling", "gender": "neutral"},
                    "onyx": {"name": "Onyx", "description": "Deep, authoritative - business, self-help", "gender": "male"},
                    "nova": {"name": "Nova", "description": "Young, friendly - YA, children's books", "gender": "female"},
                    "shimmer": {"name": "Shimmer", "description": "Soft, gentle - romance, meditation", "gender": "female"}
                },
                "cost_per_1m_chars": 15.00
            },
            "openai_tts_hd": {
                "name": "OpenAI TTS HD",
                "description": "Premium quality voices with enhanced clarity",
                "supports_cloning": False,
                "languages": ["en"],
                "recommended_for": ["premium audiobooks", "short content"],
                "voices": {
                    "alloy": {"name": "Alloy", "description": "Balanced, neutral - great for general narration", "gender": "neutral"},
                    "echo": {"name": "Echo", "description": "Deep, warm - male protagonists, non-fiction", "gender": "male"},
                    "fable": {"name": "Fable", "description": "British, expressive - fiction, storytelling", "gender": "neutral"},
                    "onyx": {"name": "Onyx", "description": "Deep, authoritative - business, self-help", "gender": "male"},
                    "nova": {"name": "Nova", "description": "Young, friendly - YA, children's books", "gender": "female"},
                    "shimmer": {"name": "Shimmer", "description": "Soft, gentle - romance, meditation", "gender": "female"}
                },
                "cost_per_1m_chars": 30.00
            },
            "edge_tts": {
                "name": "Edge TTS (Microsoft)",
                "description": "Free Microsoft Azure TTS - reliable fallback",
                "supports_cloning": False,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"],
                "recommended_for": ["fallback", "reliable synthesis"],
                "voices": {
                    "en-US-JennyNeural": {"name": "Jenny", "description": "Female, friendly (default)", "gender": "female"},
                    "en-US-GuyNeural": {"name": "Guy", "description": "Male, professional", "gender": "male"},
                    "en-GB-SoniaNeural": {"name": "Sonia", "description": "British female", "gender": "female"},
                    "en-AU-NatashaNeural": {"name": "Natasha", "description": "Australian female", "gender": "female"}
                },
                "cost_per_1m_chars": 0.00
            }
        }

    async def generate_chunk_audio(
        self,
        book_id: str,
        chunk_index: int,
        user_id: str,
        provider_id: str = "styletts2",
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        language: str = "en",
        force_regenerate: bool = False,
        is_first_playback: bool = False,
        session_id: Optional[str] = None
    ) -> AudioChunk:
        """
        Generate audio for a single book chunk.

        Args:
            book_id: Book identifier
            chunk_index: Chunk index (0-based)
            user_id: User ID for billing
            provider_id: TTS provider to use
            voice_id: Optional voice ID for cloning
            speed: Playback speed (0.5-2.0)
            language: Language code
            force_regenerate: Force regeneration even if cached
            is_first_playback: If True, add book introduction
            session_id: Reading session ID for tracking intro state

        Returns:
            AudioChunk with base64 audio data

        Raises:
            ValueError: If chunk not found
            Exception: If generation fails
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Find chunk in database
        chunk = await db.book_chunks.find_one({
            "book_id": book_id,
            "chunk_index": chunk_index
        })

        if not chunk:
            raise ValueError(f"Chunk {chunk_index} not found for book {book_id}")

        # Check if chunk is narratable (professional narration filtering)
        if not chunk.get("narratable", True):
            skip_reason = chunk.get("skip_reason", "Non-narratable content")
            content_type = chunk.get("content_type", "unknown")
            logger.info(
                f"⏭️ Skipping non-narratable chunk {chunk_index}: "
                f"type={content_type}, reason={skip_reason}"
            )
            # Return empty audio chunk to signal skip
            return AudioChunk(
                chunk_id=f"{book_id}_{chunk_index}_skipped",
                chunk_index=chunk_index,
                audio_base64="",  # Empty audio signals skip
                audio_format="mp3",
                duration=0.0,
                text_length=0,
                provider_used="skipped"
            )

        base_chunk_id = chunk.get("chunk_id", f"{book_id}_{chunk_index}")

        # Include voice settings in cache key to support different voices
        voice_key = f"{provider_id}_{voice_id or 'default'}_{speed}"
        chunk_id = f"{base_chunk_id}_{voice_key}"

        # Check cache if not forcing regenerate
        if self.enable_caching and not force_regenerate:
            cached = await self._get_cached_audio(chunk_id)
            if cached:
                self.stats["cache_hits"] += 1
                logger.info(f"Cache hit for chunk {chunk_id}")
                return cached

        # Get text content - prefer narration_text if available (pre-cleaned for TTS)
        text = chunk.get("narration_text") or chunk.get("text", "")
        if not text:
            raise ValueError(f"Chunk {chunk_id} has no text content")

        # Determine if this is a chapter start
        is_chapter_start = chunk.get("is_chapter_start", False)
        chapter_title = chunk.get("chapter_title")
        content_type = chunk.get("content_type", "narrative")

        # Get book metadata for introductions
        book_title = None
        author = None

        # Only fetch book info if we need it for introduction
        if is_first_playback or is_chapter_start:
            book = await db.books.find_one({"book_id": book_id})
            if book:
                book_title = book.get("title", "")
                author = book.get("author", "")

                # Clean filename artifacts from title
                if book_title:
                    import re
                    # Remove date prefixes, version indicators
                    book_title = re.sub(r'^\d{6,8}[_\s]*', '', book_title)
                    book_title = re.sub(r'[_\s]*(final|v\d+|draft)[\s_]*(\(\d+\))?', '', book_title, flags=re.IGNORECASE)
                    book_title = book_title.replace('_', ' ').strip()

        # Determine if we should add book intro
        # Only on first narratable chunk of first playback
        add_book_intro = (
            is_first_playback and
            chunk.get("narratable", True) and
            book_title and author
        )

        # For chapter titles, we read the title but not as intro (it's the content)
        # Chapter intro is added before the first content chunk of a new chapter
        add_chapter_intro = (
            is_chapter_start and
            content_type == "chapter_title" and
            chapter_title
        )

        # Optimize text for TTS with introductions
        optimized_text = self._optimize_text_for_tts(
            text=text,
            is_first_chunk=add_book_intro,
            is_chapter_start=add_chapter_intro,
            book_title=book_title,
            author=author,
            chapter_title=chapter_title if add_chapter_intro else None
        )

        logger.info(
            f"Generating audio for chunk {chunk_index}: "
            f"{len(optimized_text)} chars, provider={provider_id}"
            f"{' [BOOK INTRO]' if add_book_intro else ''}"
            f"{' [CHAPTER: ' + chapter_title + ']' if add_chapter_intro else ''}"
        )

        # Generate audio with fallback support
        audio_result = await self._synthesize_with_fallback(
            text=optimized_text,
            provider_id=provider_id,
            voice_id=voice_id,
            speed=speed,
            language=language,
            user_id=user_id
        )

        # Validate audio_result
        if not audio_result or "audio_base64" not in audio_result:
            logger.error(f"Invalid audio_result for chunk {chunk_index}: {audio_result}")
            raise ValueError(f"Audio synthesis failed for chunk {chunk_index}")

        audio_base64 = audio_result.get("audio_base64", "")
        if not audio_base64 or len(audio_base64.strip()) == 0:
            logger.error(
                f"Empty audio_base64 in result for chunk {chunk_index}. "
                f"Result keys: {list(audio_result.keys())}, provider: {audio_result.get('provider_used')}"
            )
            raise ValueError(f"Audio synthesis returned empty base64 for chunk {chunk_index}")

        logger.info(
            f"Audio synthesis successful for chunk {chunk_index}: "
            f"base64_length={len(audio_base64)}, duration={audio_result.get('duration', 0):.2f}s, "
            f"provider={audio_result.get('provider_used', 'unknown')}"
        )

        # Create audio chunk response
        audio_chunk = AudioChunk(
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            audio_base64=audio_base64,
            audio_format="mp3",
            duration=audio_result.get("duration", 0),
            text_length=len(optimized_text),
            provider_used=audio_result.get("provider_used", "unknown")
        )

        # Cache the audio (pass book_id and chunk_index for Hetzner upload)
        if self.enable_caching:
            await self._cache_audio(audio_chunk, book_id, chunk_index)

        # Update stats
        self.stats["total_chunks_generated"] += 1
        self.stats["total_audio_seconds"] += audio_result["duration"]

        # Update chunk in database with audio metadata
        await db.book_chunks.update_one(
            {"chunk_id": chunk_id, "book_id": book_id},
            {
                "$set": {
                    "audio_generated": True,
                    "audio_duration": audio_result["duration"],
                    "audio_provider": audio_result["provider_used"],
                    "audio_generated_at": datetime.utcnow()
                }
            }
        )

        return audio_chunk

    async def stream_book_audio(
        self,
        book_id: str,
        user_id: str,
        provider_id: str = "styletts2",
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        language: str = "en",
        start_chunk: int = 0,
        end_chunk: Optional[int] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Stream audiobook narration chunk by chunk.

        This generator yields audio chunks as they are generated,
        enabling real-time playback while generation continues.

        Args:
            book_id: Book identifier
            user_id: User ID for billing
            provider_id: TTS provider
            voice_id: Optional voice ID for cloning
            speed: Playback speed
            language: Language code
            start_chunk: Starting chunk index
            end_chunk: Ending chunk index (None = all)

        Yields:
            AudioChunk for each book chunk

        Example:
            >>> async for chunk in service.stream_book_audio("book123", "user456"):
            ...     # Play audio immediately as it's generated
            ...     await play_audio(base64.b64decode(chunk.audio_base64))
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get chunks for book
        query = {"book_id": book_id}
        chunks = await db.book_chunks.find(query).sort("chunk_index", 1).to_list(length=None)

        if not chunks:
            raise ValueError(f"No chunks found for book {book_id}")

        # Filter by range
        if end_chunk is not None:
            chunks = [c for c in chunks if start_chunk <= c["chunk_index"] <= end_chunk]
        else:
            chunks = [c for c in chunks if c["chunk_index"] >= start_chunk]

        logger.info(
            f"Streaming {len(chunks)} chunks for book {book_id} "
            f"(range: {start_chunk} to {end_chunk or 'end'})"
        )

        # Generate and yield audio chunks
        for chunk in chunks:
            try:
                audio_chunk = await self.generate_chunk_audio(
                    book_id=book_id,
                    chunk_index=chunk["chunk_index"],
                    user_id=user_id,
                    provider_id=provider_id,
                    voice_id=voice_id,
                    speed=speed,
                    language=language
                )
                yield audio_chunk

            except Exception as e:
                logger.error(f"Failed to generate chunk {chunk['chunk_index']}: {e}")
                # Continue to next chunk on failure
                continue

    async def generate_book_audio(
        self,
        request: AudiobookGenerationRequest,
        user_id: str
    ) -> AudiobookGenerationResult:
        """
        Generate audio for entire book or section.

        Args:
            request: Generation request parameters
            user_id: User ID for billing

        Returns:
            AudiobookGenerationResult with all audio chunks
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get book chunks
        query = {"book_id": request.book_id}
        chunks = await db.book_chunks.find(query).sort("chunk_index", 1).to_list(length=None)

        if not chunks:
            raise ValueError(f"No chunks found for book {request.book_id}")

        # Filter by range
        if request.end_chunk is not None:
            chunks = [c for c in chunks if request.start_chunk <= c["chunk_index"] <= request.end_chunk]
        else:
            chunks = [c for c in chunks if c["chunk_index"] >= request.start_chunk]

        logger.info(
            f"Generating audio for {len(chunks)} chunks "
            f"(book={request.book_id}, provider={request.provider_id})"
        )

        # Generate audio for each chunk
        results = {
            "book_id": request.book_id,
            "total_chunks": len(chunks),
            "successful_chunks": 0,
            "failed_chunks": 0,
            "total_duration": 0.0,
            "total_cost": 0.0,
            "provider_used": request.provider_id,
            "audio_chunks": []
        }

        for chunk in chunks:
            try:
                audio_chunk = await self.generate_chunk_audio(
                    book_id=request.book_id,
                    chunk_index=chunk["chunk_index"],
                    user_id=user_id,
                    provider_id=request.provider_id,
                    voice_id=request.voice_id,
                    speed=request.speed,
                    language=request.language
                )

                results["successful_chunks"] += 1
                results["total_duration"] += audio_chunk.duration
                results["audio_chunks"].append({
                    "chunk_id": audio_chunk.chunk_id,
                    "chunk_index": audio_chunk.chunk_index,
                    "duration": audio_chunk.duration,
                    "audio_url": f"data:audio/mp3;base64,{audio_chunk.audio_base64}"
                })

            except Exception as e:
                logger.error(f"Failed chunk {chunk['chunk_index']}: {e}")
                results["failed_chunks"] += 1
                results["audio_chunks"].append({
                    "chunk_id": chunk.get("chunk_id"),
                    "chunk_index": chunk["chunk_index"],
                    "error": str(e)
                })

        logger.info(
            f"Book audio generation complete: "
            f"{results['successful_chunks']}/{results['total_chunks']} successful, "
            f"{results['total_duration']:.2f}s total"
        )

        return AudiobookGenerationResult(**results)

    async def get_narration_info(self, book_id: str) -> Dict:
        """
        Get narration information for a book including skip indices.

        Returns information about which chunks will be narrated and which
        will be skipped, enabling the frontend to properly handle playback.

        Args:
            book_id: Book identifier

        Returns:
            Dict with:
                - total_chunks: Total number of chunks
                - narratable_chunks: Number of narratable chunks
                - skip_indices: List of chunk indices to skip
                - content_types: Dict of content type counts
                - chapter_starts: List of chunk indices that start chapters
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get all chunks for book
        chunks = await db.book_chunks.find(
            {"book_id": book_id},
            {
                "chunk_index": 1,
                "content_type": 1,
                "narratable": 1,
                "is_chapter_start": 1,
                "chapter_title": 1,
                "skip_reason": 1
            }
        ).sort("chunk_index", 1).to_list(length=None)

        if not chunks:
            return {
                "book_id": book_id,
                "total_chunks": 0,
                "narratable_chunks": 0,
                "skip_indices": [],
                "content_types": {},
                "chapter_starts": [],
                "skip_reasons": {}
            }

        # Analyze chunks
        skip_indices = []
        content_types = {}
        chapter_starts = []
        skip_reasons = {}
        narratable_count = 0

        for chunk in chunks:
            idx = chunk["chunk_index"]
            content_type = chunk.get("content_type", "narrative")
            narratable = chunk.get("narratable", True)

            # Count content types
            content_types[content_type] = content_types.get(content_type, 0) + 1

            if narratable:
                narratable_count += 1
            else:
                skip_indices.append(idx)
                reason = chunk.get("skip_reason", "Non-narratable")
                skip_reasons[idx] = reason

            # Track chapter starts
            if chunk.get("is_chapter_start"):
                chapter_starts.append({
                    "chunk_index": idx,
                    "chapter_title": chunk.get("chapter_title", f"Chapter at chunk {idx}")
                })

        logger.info(
            f"Narration info for {book_id}: "
            f"{narratable_count}/{len(chunks)} narratable, "
            f"{len(skip_indices)} skipped"
        )

        return {
            "book_id": book_id,
            "total_chunks": len(chunks),
            "narratable_chunks": narratable_count,
            "skip_indices": skip_indices,
            "content_types": content_types,
            "chapter_starts": chapter_starts,
            "skip_reasons": skip_reasons
        }

    async def _synthesize_with_fallback(
        self,
        text: str,
        provider_id: str,
        voice_id: Optional[str],
        speed: float,
        language: str,
        user_id: str
    ) -> Dict:
        """
        Synthesize audio with provider fallback support.

        Args:
            text: Text to synthesize
            provider_id: Primary provider
            voice_id: Voice ID for cloning
            speed: Playback speed
            language: Language code
            user_id: User ID for billing

        Returns:
            Dict with audio_base64, duration, provider_used

        Raises:
            Exception: If all providers fail
        """
        # Check if this is an OpenAI TTS request
        if provider_id in ["openai_tts", "openai_tts_hd"]:
            return await self._synthesize_with_openai(
                text=text,
                provider_id=provider_id,
                voice_id=voice_id,
                speed=speed,
                user_id=user_id
            )

        # First try direct Kokoro call (bypasses status check issues)
        if provider_id == "kokoro" or True:  # Always try Kokoro first for reliability
            try:
                result = await self._synthesize_with_kokoro_direct(
                    text=text,
                    voice_id=voice_id or "af_heart",
                    speed=speed
                )
                return result
            except Exception as e:
                logger.warning(f"Direct Kokoro synthesis failed: {e}")

        # Try F5-TTS as second priority (NVIDIA A40 GPU, high availability)
        try:
            logger.info("Trying F5-TTS as fallback...")
            result = await self._synthesize_with_f5tts_direct(
                text=text,
                speed=speed
            )
            self.stats["fallback_used"] += 1
            return result
        except Exception as e:
            logger.warning(f"F5-TTS fallback failed: {e}")

        # Fallback to TTSProviderService
        providers = [
            {"id": provider_id, "voice": voice_id},
            {"id": self.fallback_provider.value, "voice": None},
        ]

        last_error = None

        for provider in providers:
            try:
                # Use TTSProviderService for synthesis
                request = SynthesisRequest(
                    provider_id=provider["id"],
                    text=text,
                    voice_id=provider["voice"],
                    speed=speed,
                    language=language,
                    output_format="mp3"
                )

                result: SynthesisResult = await self.tts_provider.synthesize(
                    user_id=user_id,
                    request=request
                )

                if provider["id"] != provider_id:
                    self.stats["fallback_used"] += 1
                    logger.info(f"Used fallback provider: {provider['id']}")

                return {
                    "audio_base64": result.audio_base64,
                    "duration": result.duration,
                    "provider_used": result.provider_id
                }

            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider['id']} failed: {e}")
                continue

        # Final fallback: OpenAI TTS (cloud-based, no GPU needed)
        logger.info("All local TTS providers failed, falling back to OpenAI TTS")
        try:
            result = await self._synthesize_with_openai(
                text=text,
                provider_id="openai_tts",  # Use standard model for cost-effectiveness
                voice_id="alloy",  # Neutral voice
                speed=speed,
                user_id=user_id
            )
            self.stats["fallback_used"] += 1
            return result
        except Exception as openai_error:
            logger.error(f"OpenAI TTS fallback also failed: {openai_error}")

        # Ultimate fallback: Edge-TTS (Microsoft's free TTS service)
        logger.info("All providers failed, using Edge-TTS (Microsoft) as final fallback")
        try:
            result = await self._synthesize_with_edge_tts(
                text=text,
                voice_id=voice_id or "en-US-JennyNeural",
                speed=speed
            )
            self.stats["fallback_used"] += 1
            return result
        except Exception as edge_error:
            logger.error(f"Edge-TTS final fallback also failed: {edge_error}")
            raise Exception(
                f"All TTS providers failed including Edge-TTS fallback. "
                f"Last local error: {last_error}, OpenAI error: {openai_error}, Edge-TTS error: {edge_error}"
            )

    async def _synthesize_with_kokoro_direct(
        self,
        text: str,
        voice_id: str = "af_heart",
        speed: float = 1.0
    ) -> Dict:
        """
        Direct synthesis using Kokoro TTS endpoint.

        Bypasses TTSProviderService status checks for reliability.

        Args:
            text: Text to synthesize
            voice_id: Kokoro voice ID
            speed: Playback speed

        Returns:
            Dict with audio_base64, duration, provider_used
        """
        import aiohttp
        import io
        from pydub import AudioSegment

        kokoro_endpoint = os.getenv("KOKORO_ENDPOINT", "https://kokoro.ailabsafrica.com")
        url = f"{kokoro_endpoint}/synthesize"

        payload = {
            "text": text,
            "voice": voice_id,
            "speed": speed,
            "pitch": 1.0
        }

        timeout = aiohttp.ClientTimeout(total=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Kokoro synthesis failed: {response.status} - {error_text}")

                audio_bytes = await response.read()

                # Convert WAV to MP3 and get duration
                try:
                    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                    duration = len(audio) / 1000.0  # Duration in seconds

                    # Convert to MP3
                    mp3_buffer = io.BytesIO()
                    audio.export(mp3_buffer, format="mp3")
                    mp3_bytes = mp3_buffer.getvalue()
                    audio_base64 = base64.b64encode(mp3_bytes).decode("utf-8")
                except Exception as e:
                    # If conversion fails, return WAV as-is
                    logger.warning(f"Audio conversion failed, returning WAV: {e}")
                    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                    duration = len(audio_bytes) / (24000 * 2)  # Estimate for 24kHz 16-bit

                logger.info(f"Kokoro synthesized {len(text)} chars, duration: {duration:.1f}s")

                return {
                    "audio_base64": audio_base64,
                    "duration": duration,
                    "provider_used": "kokoro"
                }

    async def _synthesize_with_f5tts_direct(
        self,
        text: str,
        speed: float = 1.0
    ) -> Dict:
        """
        Direct synthesis using F5-TTS endpoint (kyutai.ailabsafrica.com).

        F5-TTS is a high-quality TTS model running on NVIDIA A40 GPU.

        Args:
            text: Text to synthesize
            speed: Playback speed

        Returns:
            Dict with audio_base64, duration, provider_used
        """
        import aiohttp
        import io
        from pydub import AudioSegment

        f5tts_endpoint = os.getenv("F5TTS_ENDPOINT", "https://kyutai.ailabsafrica.com")
        url = f"{f5tts_endpoint}/synthesize"

        payload = {
            "text": text,
            "speed": speed
        }

        timeout = aiohttp.ClientTimeout(total=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"F5-TTS synthesis failed: {response.status} - {error_text}")

                audio_bytes = await response.read()

                # Convert WAV to MP3 and get duration
                try:
                    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                    duration = len(audio) / 1000.0  # Duration in seconds

                    # Convert to MP3
                    mp3_buffer = io.BytesIO()
                    audio.export(mp3_buffer, format="mp3")
                    mp3_bytes = mp3_buffer.getvalue()
                    audio_base64 = base64.b64encode(mp3_bytes).decode("utf-8")
                except Exception as e:
                    # If conversion fails, return WAV as-is
                    logger.warning(f"F5-TTS audio conversion failed, returning WAV: {e}")
                    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                    duration = len(audio_bytes) / (24000 * 2)  # Estimate for 24kHz 16-bit

                logger.info(f"F5-TTS synthesized {len(text)} chars, duration: {duration:.1f}s")

                return {
                    "audio_base64": audio_base64,
                    "duration": duration,
                    "provider_used": "f5tts"
                }

    async def _synthesize_with_openai(
        self,
        text: str,
        provider_id: str,
        voice_id: Optional[str],
        speed: float,
        user_id: str
    ) -> Dict:
        """
        Synthesize audio using OpenAI TTS.

        Args:
            text: Text to synthesize
            provider_id: openai_tts or openai_tts_hd
            voice_id: Voice (alloy, echo, fable, onyx, nova, shimmer)
            speed: Playback speed (0.25-4.0)
            user_id: User ID for billing

        Returns:
            Dict with audio_base64, duration, provider_used
        """
        from app.services.openai_tts_service import get_openai_tts_service

        openai_service = get_openai_tts_service()

        # Map provider_id to model
        model = "tts-1-hd" if provider_id == "openai_tts_hd" else "tts-1"

        # Default voice if not specified
        voice = voice_id or "alloy"

        # Validate voice
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice not in valid_voices:
            logger.warning(f"Invalid voice '{voice}', using 'alloy'")
            voice = "alloy"

        logger.info(f"Synthesizing with OpenAI TTS: model={model}, voice={voice}, {len(text)} chars")

        try:
            result = await openai_service.synthesize(
                text=text,
                voice=voice,
                model=model,
                speed=speed
            )

            return {
                "audio_base64": result.audio_base64,
                "duration": result.duration,
                "provider_used": provider_id
            }

        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            # Fall back to default provider
            logger.info("Falling back to StyleTTS2...")
            return await self._synthesize_with_fallback(
                text=text,
                provider_id=self.default_provider.value,
                voice_id=None,
                speed=speed,
                language="en",
                user_id=user_id
            )

    async def _synthesize_with_edge_tts(
        self,
        text: str,
        voice_id: str = "en-US-JennyNeural",
        speed: float = 1.0
    ) -> Dict:
        """
        Synthesize audio using Microsoft Edge TTS (free, no GPU required).

        Available voices:
        - en-US-JennyNeural: Female, friendly (default)
        - en-US-GuyNeural: Male, professional
        - en-GB-SoniaNeural: British female
        - en-AU-NatashaNeural: Australian female

        Args:
            text: Text to synthesize
            voice_id: Edge TTS voice ID
            speed: Playback speed (0.5-2.0, converted to rate string)

        Returns:
            Dict with audio_base64, duration, provider_used
        """
        import edge_tts
        import io
        from pydub import AudioSegment

        # Map common voice names to Edge TTS voices
        voice_mapping = {
            "alloy": "en-US-JennyNeural",
            "echo": "en-US-GuyNeural",
            "fable": "en-GB-SoniaNeural",
            "onyx": "en-US-GuyNeural",
            "nova": "en-US-JennyNeural",
            "shimmer": "en-US-JennyNeural",
            "af_heart": "en-US-JennyNeural",
            "af_sky": "en-US-JennyNeural",
        }

        # Use mapping if voice_id matches common names, otherwise use as-is
        edge_voice = voice_mapping.get(voice_id, voice_id)

        # Validate voice format (Edge TTS voices follow xx-XX-NameNeural pattern)
        if not edge_voice.endswith("Neural"):
            edge_voice = "en-US-JennyNeural"  # Default fallback

        # Convert speed to rate string (Edge TTS uses +X% or -X% format)
        rate_percent = int((speed - 1.0) * 100)
        rate = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"

        logger.info(f"Synthesizing with Edge-TTS: voice={edge_voice}, rate={rate}, {len(text)} chars")

        try:
            # Create Edge TTS communicator
            communicate = edge_tts.Communicate(text, edge_voice, rate=rate)

            # Collect audio chunks
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            if not audio_chunks:
                raise Exception("Edge-TTS returned no audio data")

            # Combine audio chunks
            audio_bytes = b"".join(audio_chunks)

            # Convert MP3 to get duration and base64
            try:
                audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                duration = len(audio) / 1000.0  # Duration in seconds
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.warning(f"Audio processing failed, using raw bytes: {e}")
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                # Estimate duration: MP3 at 128kbps = ~16KB/sec
                duration = len(audio_bytes) / 16000.0

            logger.info(f"Edge-TTS synthesized {len(text)} chars, duration: {duration:.1f}s")

            return {
                "audio_base64": audio_base64,
                "duration": duration,
                "provider_used": "edge_tts"
            }

        except Exception as e:
            logger.error(f"Edge-TTS synthesis failed: {e}")
            raise

    async def _get_cached_audio(self, chunk_id: str) -> Optional[AudioChunk]:
        """
        Get cached audio for chunk.

        Args:
            chunk_id: Chunk identifier

        Returns:
            AudioChunk if cached, None otherwise
        """
        cache_path = os.path.join(self.storage_path, f"{chunk_id}.mp3")

        if not os.path.exists(cache_path):
            return None

        # Check if cache is expired
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        if file_age > self.cache_ttl:
            os.remove(cache_path)
            return None

        try:
            with open(cache_path, "rb") as f:
                audio_data = f.read()

            # Get duration from metadata file
            meta_path = cache_path + ".meta"
            duration = 0.0
            provider_used = "cached"

            if os.path.exists(meta_path):
                import json
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    duration = meta.get("duration", 0.0)
                    provider_used = meta.get("provider_used", "cached")

            # Extract chunk_index from chunk_id
            # Format: book_{book_id}_chunk_{chunk_index} or book_{book_id}_chunk_{chunk_index}_{provider}_{voice}_{speed}
            # Reason: Need to handle both old and new chunk ID formats with voice settings
            chunk_index = 0
            if "chunk_" in chunk_id:
                # Split and find the part after "chunk_"
                parts = chunk_id.split("chunk_")
                if len(parts) > 1:
                    # Take the number after "chunk_" (before any provider/voice info)
                    index_part = parts[1].split("_")[0]
                    try:
                        chunk_index = int(index_part)
                    except ValueError:
                        logger.warning(f"Could not parse chunk index from {chunk_id}, using 0")
                        chunk_index = 0

            return AudioChunk(
                chunk_id=chunk_id,
                chunk_index=chunk_index,
                audio_base64=base64.b64encode(audio_data).decode("utf-8"),
                audio_format="mp3",
                duration=duration,
                text_length=0,
                provider_used=provider_used
            )

        except Exception as e:
            logger.warning(f"Failed to load cached audio for {chunk_id}: {e}")
            return None

    async def _cache_audio(self, audio_chunk: AudioChunk, book_id: str, chunk_index: int) -> None:
        """
        Cache generated audio chunk locally and upload to Hetzner storage.

        Args:
            audio_chunk: Audio chunk to cache
            book_id: Book identifier (for Hetzner upload)
            chunk_index: Chunk index (for Hetzner upload)
        """
        try:
            cache_path = os.path.join(self.storage_path, f"{audio_chunk.chunk_id}.mp3")
            meta_path = cache_path + ".meta"

            # Decode audio data
            audio_data = base64.b64decode(audio_chunk.audio_base64)
            
            # Save audio file locally
            with open(cache_path, "wb") as f:
                f.write(audio_data)

            # Save metadata locally
            import json
            meta = {
                "chunk_id": audio_chunk.chunk_id,
                "chunk_index": audio_chunk.chunk_index,
                "duration": audio_chunk.duration,
                "text_length": audio_chunk.text_length,
                "provider_used": audio_chunk.provider_used,
                "cached_at": datetime.utcnow().isoformat()
            }
            with open(meta_path, "w") as f:
                json.dump(meta, f)

            # Upload to Hetzner storage in background
            try:
                from app.services.storage_service import get_storage_service
                storage_service = await get_storage_service()

                # Use book_id and chunk_index passed as parameters (no parsing needed!)
                storage_result = await storage_service.upload_audio_chunk(
                    book_id=book_id,
                    chunk_index=chunk_index,
                    audio_content=audio_data,
                    audio_format="mp3"
                )

                logger.info(
                    f"✅ Uploaded audio chunk {audio_chunk.chunk_id} to Hetzner: "
                    f"{storage_result.get('storage_type', 'unknown')}"
                )
            except Exception as storage_error:
                # Don't fail if storage upload fails - local cache is still available
                logger.warning(
                    f"⚠️ Failed to upload audio chunk {audio_chunk.chunk_id} to Hetzner: {storage_error}"
                )

            logger.debug(f"Cached audio for {audio_chunk.chunk_id}")

        except Exception as e:
            logger.warning(f"Failed to cache audio for {audio_chunk.chunk_id}: {e}")

    def _optimize_text_for_tts(
        self,
        text: str,
        is_first_chunk: bool = False,
        is_chapter_start: bool = False,
        book_title: Optional[str] = None,
        author: Optional[str] = None,
        chapter_title: Optional[str] = None,
        chapter_number: Optional[int] = None
    ) -> str:
        """
        Optimize text for professional audiobook-quality TTS.

        Uses TTSTextNormalizer for:
        - Removing decorative separators
        - Converting punctuation to pauses (never spoken)
        - Adding book/chapter introductions
        - Cleaning symbols that might be read aloud

        Args:
            text: Original text
            is_first_chunk: Add book introduction if True
            is_chapter_start: Add chapter introduction if True
            book_title: Book title for introduction
            author: Author name for introduction
            chapter_title: Chapter title for introduction
            chapter_number: Chapter number for introduction

        Returns:
            Optimized text ready for TTS
        """
        # Get normalizer (uses SSML for pause control)
        normalizer = get_tts_normalizer(use_ssml=False)  # Most TTS don't support SSML

        # Prepare with introductions if needed
        optimized = normalizer.prepare_chunk_for_tts(
            text=text,
            is_first_chunk=is_first_chunk,
            is_chapter_start=is_chapter_start,
            book_title=book_title,
            author=author,
            chapter_title=chapter_title,
            chapter_number=chapter_number
        )

        # Additional abbreviation expansion (preserve these from original)
        replacements = {
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Ms.": "Miss",
            "Prof.": "Professor",
            "etc.": "et cetera",
            "i.e.": "that is",
            "e.g.": "for example",
            "vs.": "versus",
            "St.": "Saint",
            "Jr.": "Junior",
            "Sr.": "Senior",
            "Ltd.": "Limited",
            "Inc.": "Incorporated",
            "Co.": "Company",
            "Dept.": "Department",
            "Ave.": "Avenue",
            "Blvd.": "Boulevard",
            "Rd.": "Road",
            "Fig.": "Figure",
            "Ch.": "Chapter",
            "Vol.": "Volume",
        }

        for abbrev, full in replacements.items():
            optimized = optimized.replace(abbrev, full)

        return optimized

    async def get_stats(self) -> Dict:
        """Get service statistics."""
        return {
            **self.stats,
            "initialized": self._initialized,
            "default_provider": self.default_provider.value,
            "fallback_provider": self.fallback_provider.value,
            "caching_enabled": self.enable_caching
        }

    async def shutdown(self) -> None:
        """Cleanup when service shuts down."""
        if self.tts_provider:
            await self.tts_provider.shutdown()
        logger.info("AudiobookService shut down")


# Singleton instance
_audiobook_service: Optional[AudiobookService] = None


async def get_audiobook_service() -> AudiobookService:
    """
    Get or create singleton AudiobookService instance.

    Returns:
        Initialized AudiobookService
    """
    global _audiobook_service

    if _audiobook_service is None:
        _audiobook_service = AudiobookService()
        await _audiobook_service.initialize()

    return _audiobook_service

"""
Text-to-Speech service for InkWave.

Comprehensive TTS integration with billing, caching, and multi-provider support
using the shared TTSProviderService.
"""

import sys
import os
import logging
import base64
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

# Add project root to path for shared imports (consistent with main.py)
# From /opt/kasaai/apps/inkwave/backend/app/services/ -> /opt/kasaai/
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult,
    VoiceCloneRequest
)
from app.core.database import get_db

logger = logging.getLogger(__name__)


class TTSService:
    """
    TTS service for InkWave audiobook narration.

    Provides audio generation with automatic billing, caching,
    and access to 10+ TTS providers.
    """

    def __init__(self):
        """Initialize TTS service."""
        self.tts_provider = TTSProviderService(
            enable_billing=True,
            enable_health_monitoring=True,
            enable_email_alerts=False,
            cache_ttl=300  # Cache provider status for 5 minutes
        )
        self._initialized = False

        # Storage configuration
        self.storage_path = os.getenv(
            "AUDIO_STORAGE_PATH",
            "/opt/kasaai/apps/inkwave/backend/storage/audio"
        )
        self.storage_base_url = os.getenv(
            "AUDIO_STORAGE_URL",
            "https://inkwave-api.ailabsafrica.com/storage/audio"
        )

        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)

    async def initialize(self, provider: str = "coqui_xtts"):
        """
        Initialize the TTS provider service.

        Args:
            provider: Default TTS provider (coqui_xtts, f5tts, styletts2, etc.)

        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            return

        try:
            await self.tts_provider.initialize()
            self._initialized = True
            logger.info(f"✅ TTS Service initialized with default provider: {provider}")
        except Exception as e:
            logger.error(f"❌ TTS Service initialization failed: {e}")
            raise

    async def get_available_providers(self) -> Dict:
        """
        Get list of available TTS providers.

        Returns:
            Dict with provider IDs, names, and capabilities

        Example:
            {
                "coqui_xtts": {
                    "name": "Coqui XTTS",
                    "status": "online",
                    "capabilities": ["voice_cloning", "multi_language"]
                }
            }
        """
        if not self._initialized:
            await self.initialize()

        return await self.tts_provider.get_available_providers()

    async def narrate_chunk(
        self,
        book_id: str,
        chunk_id: str,
        user_id: str,
        provider_id: str = "coqui_xtts",
        voice_id: str = "nova",
        speed: float = 1.0,
        language: str = "en",
        force_regenerate: bool = False
    ) -> Dict:
        """
        Generate audio narration for a book chunk.

        Args:
            book_id: Book identifier
            chunk_id: Chunk identifier
            user_id: User ID for billing
            provider_id: TTS provider (coqui_xtts, f5tts, styletts2, etc.)
            voice_id: Voice identifier
            speed: Playback speed multiplier (0.5 - 2.0)
            language: Language code (en, es, fr, etc.)
            force_regenerate: Force regeneration even if cached

        Returns:
            Dict with audio_url, duration, cost, provider_used, cached

        Raises:
            ValueError: If chunk not found
            Exception: If audio generation fails
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get chunk from database
        chunk = await db.book_chunks.find_one({
            "chunk_id": chunk_id,
            "book_id": book_id
        })

        if not chunk:
            raise ValueError(f"Chunk not found: {chunk_id}")

        # Check for cached audio (unless force regenerate)
        if not force_regenerate and chunk.get("audio_url"):
            logger.info(f"Using cached audio for chunk: {chunk_id}")
            return {
                "audio_url": chunk["audio_url"],
                "duration": chunk.get("audio_duration", 0),
                "cost": 0.0,  # Cached, no charge
                "provider_used": chunk.get("audio_provider", provider_id),
                "cached": True
            }

        # Get chunk text
        text = chunk.get("text", "")
        if not text:
            raise ValueError(f"Chunk has no text: {chunk_id}")

        # Optimize text for better TTS output
        optimized_text = self.optimize_text_for_tts(text)

        # ✨ NEW: Check if book has a voice clone assigned
        book = await db.books.find_one({"book_id": book_id})
        voice_clone_id = book.get("voice_clone_id") if book else None

        if voice_clone_id:
            logger.info(f"🎙️ Using voice clone {voice_clone_id} for chunk {chunk_id}")
            # Generate audio with voice cloning
            return await self._narrate_with_voice_clone(
                chunk_id=chunk_id,
                book_id=book_id,
                text=optimized_text,
                voice_clone_id=voice_clone_id,
                user_id=user_id,
                speed=speed,
                language=language,
                db=db
            )

        logger.info(
            f"Generating audio for chunk {chunk_id}: "
            f"{len(optimized_text)} chars, provider: {provider_id}"
        )

        # Check if voice_id is a reference audio ID (ref_audio_xxx)
        if voice_id and voice_id.startswith("ref_audio_"):
            logger.info(f"🎙️ Using reference audio: {voice_id}")
            return await self._narrate_with_reference_audio(
                chunk_id=chunk_id,
                book_id=book_id,
                text=optimized_text,
                reference_audio_id=voice_id,
                provider_id=provider_id,
                user_id=user_id,
                speed=speed,
                language=language,
                db=db
            )

        # Synthesize speech
        try:
            synthesis_request = SynthesisRequest(
                provider_id=provider_id,
                text=optimized_text,
                language=language,
                voice_id=voice_id,
                speed=speed,
                output_format="mp3"
            )

            result: SynthesisResult = await self.tts_provider.synthesize(
                user_id=user_id,
                request=synthesis_request
            )

            # Save audio file
            audio_url = await self._save_audio_file(
                audio_base64=result.audio_base64,
                chunk_id=chunk_id,
                book_id=book_id
            )

            # Update chunk with audio metadata
            await db.book_chunks.update_one(
                {"chunk_id": chunk_id, "book_id": book_id},
                {
                    "$set": {
                        "audio_url": audio_url,
                        "audio_duration": result.duration,
                        "audio_provider": result.provider_id,
                        "audio_generated_at": datetime.utcnow(),
                        "audio_cost": result.cost,
                        "audio_voice_id": voice_id,
                        "audio_speed": speed,
                        "audio_language": language
                    }
                }
            )

            logger.info(
                f"✅ Audio generated: {result.duration:.2f}s, "
                f"${result.cost:.4f}, provider: {result.provider_id}"
            )

            return {
                "audio_url": audio_url,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "transaction_id": result.transaction_id,
                "cached": False
            }

        except Exception as e:
            logger.error(f"❌ Audio generation failed for chunk {chunk_id}: {e}")
            raise

    async def narrate_chapter(
        self,
        book_id: str,
        chapter_id: str,
        user_id: str,
        provider_id: str = "coqui_xtts",
        voice_id: str = "nova",
        speed: float = 1.0,
        language: str = "en"
    ) -> Dict:
        """
        Generate audio for all chunks in a chapter.

        Args:
            book_id: Book identifier
            chapter_id: Chapter identifier
            user_id: User ID for billing
            provider_id: TTS provider
            voice_id: Voice identifier
            speed: Playback speed
            language: Language code

        Returns:
            Dict with total_chunks, successful, failed, total_duration, total_cost
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get all chunks for chapter
        chunks = await db.book_chunks.find({
            "book_id": book_id,
            "chapter_id": chapter_id
        }).sort("chunk_index", 1).to_list(length=None)

        if not chunks:
            raise ValueError(f"No chunks found for chapter: {chapter_id}")

        logger.info(f"Generating audio for chapter {chapter_id}: {len(chunks)} chunks")

        results = {
            "total_chunks": len(chunks),
            "successful": 0,
            "failed": 0,
            "total_duration": 0.0,
            "total_cost": 0.0,
            "chunks": []
        }

        # Generate audio for each chunk
        for chunk in chunks:
            try:
                audio_result = await self.narrate_chunk(
                    chunk_id=chunk["chunk_id"],
                    book_id=book_id,
                    user_id=user_id,
                    provider_id=provider_id,
                    voice_id=voice_id,
                    speed=speed,
                    language=language
                )

                results["successful"] += 1
                results["total_duration"] += audio_result["duration"]
                results["total_cost"] += audio_result["cost"]
                results["chunks"].append({
                    "chunk_id": chunk["chunk_id"],
                    "status": "success",
                    "audio_url": audio_result["audio_url"],
                    "duration": audio_result["duration"],
                    "cost": audio_result["cost"]
                })

            except Exception as e:
                logger.error(f"Failed to narrate chunk {chunk['chunk_id']}: {e}")
                results["failed"] += 1
                results["chunks"].append({
                    "chunk_id": chunk["chunk_id"],
                    "status": "failed",
                    "error": str(e)
                })

        logger.info(
            f"Chapter narration complete: {results['successful']}/{results['total_chunks']} "
            f"successful, {results['total_duration']:.2f}s, ${results['total_cost']:.4f}"
        )

        return results

    async def estimate_narration_cost(
        self,
        book_id: str,
        provider_id: str = "coqui_xtts"
    ) -> Dict:
        """
        Estimate cost to narrate entire book.

        Args:
            book_id: Book identifier
            provider_id: TTS provider

        Returns:
            Dict with total_chunks, total_characters, estimated_cost, estimated_duration
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get all chunks
        chunks = await db.book_chunks.find({"book_id": book_id}).to_list(length=None)

        if not chunks:
            raise ValueError(f"No chunks found for book: {book_id}")

        # Calculate total characters
        total_chars = sum(len(chunk.get("text", "")) for chunk in chunks)

        # Get sample for cost estimation
        sample_text = " ".join(
            chunk.get("text", "")[:500]
            for chunk in chunks[:3]
        )

        cost_estimate = await self.tts_provider.estimate_cost(
            text=sample_text,
            provider_id=provider_id,
            voice_cloning=False
        )

        # Scale to full book
        sample_chars = len(sample_text)
        cost_per_char = cost_estimate.total_cost / sample_chars if sample_chars > 0 else 0
        total_estimated_cost = cost_per_char * total_chars

        # Estimate duration (TTS averages ~150 chars/second)
        estimated_duration = total_chars / 150.0

        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "estimated_cost": round(total_estimated_cost, 2),
            "estimated_duration_minutes": round(estimated_duration / 60, 1),
            "cost_per_1000_chars": round(cost_per_char * 1000, 4)
        }

    async def _narrate_with_voice_clone(
        self,
        chunk_id: str,
        book_id: str,
        text: str,
        voice_clone_id: str,
        user_id: str,
        speed: float,
        language: str,
        db
    ) -> Dict:
        """
        Generate audio narration using a voice clone.

        Args:
            chunk_id: Chunk identifier
            book_id: Book identifier
            text: Text to narrate
            voice_clone_id: Voice clone identifier
            user_id: User ID for billing
            speed: Playback speed
            language: Language code
            db: Database connection

        Returns:
            Dict with audio_url, duration, cost, provider_used, cached
        """
        # Get voice clone from database
        voice_clone = await db.voice_clones.find_one({"clone_id": voice_clone_id})

        if not voice_clone:
            logger.warning(f"Voice clone {voice_clone_id} not found, falling back to default TTS")
            # Fallback to default synthesis
            return await self._synthesize_default(
                chunk_id, book_id, text, user_id, speed, language, db
            )

        try:
            # Read reference audio file
            reference_audio_path = voice_clone["reference_audio_path"]
            if not os.path.exists(reference_audio_path):
                logger.warning(f"Voice clone audio file missing: {reference_audio_path}")
                return await self._synthesize_default(
                    chunk_id, book_id, text, user_id, speed, language, db
                )

            with open(reference_audio_path, "rb") as f:
                reference_audio = f.read()

            # Convert to base64
            reference_audio_b64 = base64.b64encode(reference_audio).decode('utf-8')

            logger.info(
                f"🎙️ Generating audio with voice clone: {voice_clone['voice_name']} "
                f"({len(text)} chars)"
            )

            # Generate audio with voice cloning (F5-TTS)
            voice_clone_request = VoiceCloneRequest(
                provider_id="f5tts",  # F5-TTS supports voice cloning
                text=text,
                reference_audio_base64=reference_audio_b64,
                language=language,
                speed=speed,
                output_format="mp3"
            )

            result = await self.tts_provider.synthesize_with_voice_cloning(
                user_id=user_id,
                request=voice_clone_request
            )

            # Save audio file
            audio_url = await self._save_audio_file(
                audio_base64=result.audio_base64,
                chunk_id=chunk_id,
                book_id=book_id
            )

            # Update chunk with audio metadata
            await db.book_chunks.update_one(
                {"chunk_id": chunk_id, "book_id": book_id},
                {
                    "$set": {
                        "audio_url": audio_url,
                        "audio_duration": result.duration,
                        "audio_provider": "f5tts_voice_clone",
                        "audio_cost": result.cost,
                        "audio_generated_at": datetime.utcnow(),
                        "voice_clone_id": voice_clone_id
                    }
                }
            )

            logger.info(
                f"✅ Voice clone audio generated: {audio_url}, "
                f"duration: {result.duration:.2f}s, cost: ${result.cost:.4f}"
            )

            return {
                "audio_url": audio_url,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": "f5tts_voice_clone",
                "cached": False,
                "voice_clone": voice_clone['voice_name']
            }

        except Exception as e:
            logger.error(f"Voice clone synthesis failed: {e}, falling back to default")
            # Fallback to default TTS on error
            return await self._synthesize_default(
                chunk_id, book_id, text, user_id, speed, language, db
            )

    async def _narrate_with_reference_audio(
        self,
        chunk_id: str,
        book_id: str,
        text: str,
        reference_audio_id: str,
        provider_id: str,
        user_id: str,
        speed: float,
        language: str,
        db
    ) -> Dict:
        """
        Generate audio narration using reference audio for zero-shot TTS providers.

        Args:
            chunk_id: Chunk identifier
            book_id: Book identifier
            text: Text to narrate
            reference_audio_id: Reference audio ID (ref_audio_xxx)
            provider_id: Zero-shot TTS provider (styletts2, coqui_xtts, openvoice, f5tts)
            user_id: User ID for billing
            speed: Playback speed
            language: Language code
            db: Database connection

        Returns:
            Dict with audio_url, duration, cost, provider_used, cached
        """
        from apps.shared.services.tts_provider_service import VoiceCloneRequest

        # Validate provider supports zero-shot
        zero_shot_providers = ["styletts2", "coqui_xtts", "openvoice", "f5tts"]
        if provider_id not in zero_shot_providers:
            logger.warning(
                f"Provider {provider_id} doesn't support zero-shot TTS. "
                f"Falling back to default synthesis."
            )
            return await self._synthesize_default(
                chunk_id, book_id, text, user_id, speed, language, db
            )

        # Get reference audio from shared service
        from apps.shared.services.reference_audio_service import get_reference_audio_service
        
        reference_audio_service = get_reference_audio_service(
            storage_base_path="inkwave/reference_audio"
        )
        await reference_audio_service.initialize()
        
        ref_audio = await reference_audio_service.get_reference_audio(
            reference_audio_id=reference_audio_id,
            user_id=user_id
        )
        
        if not ref_audio:
            logger.warning(
                f"Reference audio {reference_audio_id} not found for user {user_id}. "
                f"Falling back to default synthesis."
            )
            return await self._synthesize_default(
                chunk_id, book_id, text, user_id, speed, language, db
            )

        try:
            # Get audio file bytes from shared service
            reference_audio_bytes = await reference_audio_service.get_audio_file_bytes(
                reference_audio_id=reference_audio_id,
                user_id=user_id
            )
            
            if not reference_audio_bytes:
                raise ValueError("Failed to load reference audio file")
            
            # Convert to base64
            reference_audio_base64 = base64.b64encode(reference_audio_bytes).decode('utf-8')

            logger.info(
                f"🎙️ Generating audio with reference audio: {ref_audio.name} "
                f"using {provider_id} ({len(text)} chars)"
            )

            # Create voice clone request for zero-shot TTS
            voice_clone_request = VoiceCloneRequest(
                provider_id=provider_id,
                text=text,
                reference_audio_base64=reference_audio_base64,
                language=language,
                speed=speed,
                remove_silence=True,
                ref_text=None  # Optional: can add transcript later
            )

            result = await self.tts_provider.synthesize_with_voice_cloning(
                user_id=user_id,
                request=voice_clone_request
            )

            # Save audio file
            audio_url = await self._save_audio_file(
                audio_base64=result.audio_base64,
                chunk_id=chunk_id,
                book_id=book_id
            )

            # Update chunk with audio metadata
            await db.book_chunks.update_one(
                {"chunk_id": chunk_id, "book_id": book_id},
                {
                    "$set": {
                        "audio_url": audio_url,
                        "audio_duration": result.duration,
                        "audio_provider": result.provider_id,
                        "audio_cost": result.cost,
                        "audio_generated_at": datetime.utcnow(),
                        "audio_voice_id": reference_audio_id,
                        "audio_speed": speed,
                        "audio_language": language,
                        "reference_audio_id": reference_audio_id
                    }
                }
            )

            logger.info(
                f"✅ Reference audio synthesis complete: {audio_url}, "
                f"duration: {result.duration:.2f}s, cost: ${result.cost:.4f}"
            )

            return {
                "audio_url": audio_url,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "transaction_id": result.transaction_id,
                "cached": False,
                "reference_audio_name": ref_audio.name
            }

        except Exception as e:
            logger.error(
                f"Reference audio synthesis failed for {reference_audio_id}: {e}. "
                f"Falling back to default synthesis."
            )
            # Fallback to default TTS on error
            return await self._synthesize_default(
                chunk_id, book_id, text, user_id, speed, language, db
            )

    async def _synthesize_default(
        self,
        chunk_id: str,
        book_id: str,
        text: str,
        user_id: str,
        speed: float,
        language: str,
        db
    ) -> Dict:
        """
        Fallback synthesis using default TTS provider.
        """
        synthesis_request = SynthesisRequest(
            provider_id="coqui_xtts",
            text=text,
            language=language,
            voice_id="nova",
            speed=speed,
            output_format="mp3"
        )

        result = await self.tts_provider.synthesize(
            user_id=user_id,
            request=synthesis_request
        )

        audio_url = await self._save_audio_file(
            audio_base64=result.audio_base64,
            chunk_id=chunk_id,
            book_id=book_id
        )

        await db.book_chunks.update_one(
            {"chunk_id": chunk_id, "book_id": book_id},
            {
                "$set": {
                    "audio_url": audio_url,
                    "audio_duration": result.duration,
                    "audio_provider": result.provider_id,
                    "audio_cost": result.cost,
                    "audio_generated_at": datetime.utcnow()
                }
            }
        )

        return {
            "audio_url": audio_url,
            "duration": result.duration,
            "cost": result.cost,
            "provider_used": result.provider_id,
            "cached": False
        }

    async def _save_audio_file(
        self,
        audio_base64: str,
        chunk_id: str,
        book_id: str
    ) -> str:
        """
        Save audio file to storage.

        Args:
            audio_base64: Base64-encoded audio
            chunk_id: Chunk identifier
            book_id: Book identifier

        Returns:
            URL to access the audio file
        """
        try:
            # Decode audio
            audio_data = base64.b64decode(audio_base64)

            # Create filename
            filename = f"{book_id}_{chunk_id}.mp3"
            filepath = os.path.join(self.storage_path, filename)

            # Save file
            with open(filepath, "wb") as f:
                f.write(audio_data)

            # Generate URL
            audio_url = f"{self.storage_base_url}/{filename}"

            logger.debug(f"Audio saved: {filepath} ({len(audio_data)} bytes)")

            return audio_url

        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise

    @staticmethod
    def calculate_cost(text_length: int, provider: str = "coqui_xtts") -> float:
        """
        Calculate estimated TTS cost.

        Args:
            text_length: Number of characters
            provider: TTS provider

        Returns:
            Cost in USD
        """
        # Base cost: $0.015 per 1000 characters
        base_cost = (text_length / 1000) * 0.015

        # Premium providers (2x multiplier)
        premium_providers = ["f5tts", "styletts2", "openvoice"]
        if provider in premium_providers:
            return base_cost * 2

        return base_cost

    @staticmethod
    def optimize_text_for_tts(text: str) -> str:
        """
        Optimize text for better TTS output.

        Args:
            text: Original text

        Returns:
            Optimized text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Replace common abbreviations for better pronunciation
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
        }

        for abbrev, full in replacements.items():
            text = text.replace(abbrev, full)

        return text

    async def shutdown(self) -> None:
        """Cleanup when service shuts down."""
        if self.tts_provider:
            await self.tts_provider.shutdown()
        logger.info("TTS Service shut down")


# Legacy compatibility methods
async def generate_audio(text: str, voice: str = "alloy", cache_key: Optional[str] = None) -> bytes:
    """
    Legacy method for backward compatibility.

    Args:
        text: Text to convert
        voice: Voice ID
        cache_key: Optional cache key

    Returns:
        Audio data as bytes
    """
    service = TTSService()
    await service.initialize()

    result = await service.tts_provider.synthesize(
        user_id="legacy",
        request=SynthesisRequest(
            provider_id="coqui_xtts",
            text=text,
            voice_id=voice,
            output_format="mp3"
        )
    )

    return base64.b64decode(result.audio_base64)


async def generate_chunk_audio(
    book_id: str,
    chunk_index: int,
    text: str,
    voice: str = "alloy"
) -> bytes:
    """
    Legacy method for generating chunk audio.

    Args:
        book_id: Book ID
        chunk_index: Chunk index
        text: Text to convert
        voice: Voice ID

    Returns:
        Audio data as bytes
    """
    return await generate_audio(text, voice, f"audio:{book_id}:{chunk_index}:{voice}")

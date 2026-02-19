"""
Audio Pre-generation Service for InkWave.

Generates audio for all book chunks in the background after book upload.
This provides instant playback for users - no waiting for TTS generation.

Default voice: Kokoro with Michael voice (am_michael)

Author: AI Labs Africa
Created: November 30, 2025
"""

import os
import sys
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from app.core.database import get_db
from app.services.audiobook_service import AudiobookService, AudiobookProvider

logger = logging.getLogger(__name__)


class AudioGenerationStatus(str, Enum):
    """Audio generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


# Default voice settings for pre-generation
DEFAULT_VOICE_SETTINGS = {
    "provider_id": "kokoro",
    "voice_id": "am_michael",
    "speed": 1.0,
    "language": "en"
}


class AudioPregenerationService:
    """
    Service for pre-generating audio for all book chunks.

    This runs as a background task after book upload/processing completes.
    Pre-generated audio is stored and cached for instant playback.

    Features:
    - Generates audio for all chunks with default voice
    - Tracks progress in database
    - Handles failures gracefully (partial generation)
    - Can be resumed if interrupted
    """

    def __init__(self):
        """Initialize audio pre-generation service."""
        self.audiobook_service: Optional[AudiobookService] = None
        self._initialized = False

        # Configuration
        self.batch_size = 5  # Process 5 chunks concurrently
        self.max_retries = 2  # Retry failed chunks
        self.retry_delay = 2.0  # Seconds between retries

    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        if self._initialized:
            return

        try:
            self.audiobook_service = AudiobookService(
                default_provider=AudiobookProvider.KOKORO,
                fallback_provider=AudiobookProvider.EDGE_TTS,
                enable_caching=True
            )
            await self.audiobook_service.initialize()
            self._initialized = True
            logger.info("AudioPregenerationService initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AudioPregenerationService: {e}")
            raise

    async def pregenerate_book_audio(
        self,
        book_id: str,
        user_id: str,
        voice_settings: Optional[Dict[str, Any]] = None,
        notify_on_complete: bool = True
    ) -> Dict[str, Any]:
        """
        Pre-generate audio for all chunks in a book.

        This is the main entry point - call this after book processing completes.

        Args:
            book_id: Book identifier
            user_id: User ID who uploaded the book (for billing if applicable)
            voice_settings: Override default voice settings
            notify_on_complete: Send notification when complete

        Returns:
            Dict with generation results and statistics
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()

        # Get book and chunks
        book = await db.books.find_one({"book_id": book_id})
        if not book:
            raise ValueError(f"Book {book_id} not found")

        chunks = await db.book_chunks.find({"book_id": book_id}).sort("chunk_index", 1).to_list(length=None)
        total_chunks = len(chunks)

        if total_chunks == 0:
            logger.warning(f"No chunks found for book {book_id}")
            return {
                "book_id": book_id,
                "status": "no_chunks",
                "message": "No text chunks available for audio generation"
            }

        # Get skip chunks from book metadata (TOC, copyright, etc.)
        skip_chunks = book.get("skip_chunks", [])
        
        # Find first playable chunk (not in skip list)
        first_playable = 0
        for i in range(total_chunks):
            if i not in skip_chunks:
                first_playable = i
                break
        
        # Prioritize first playable chunks: generate first 3-5 playable chunks first
        # This ensures instant playback when user starts listening
        priority_chunks = []
        playable_count = 0
        for i in range(first_playable, total_chunks):
            if i not in skip_chunks:
                priority_chunks.append(i)
                playable_count += 1
                if playable_count >= 5:  # First 5 playable chunks
                    break
        
        # Remaining chunks (in order)
        remaining_chunks = [i for i in range(total_chunks) if i not in priority_chunks and i not in skip_chunks]
        
        # Combine: priority first, then remaining
        chunk_order = priority_chunks + remaining_chunks
        
        logger.info(
            f"Starting audio pre-generation for book {book_id}: {total_chunks} chunks "
            f"(prioritizing first {len(priority_chunks)} playable chunks)"
        )

        # Update book status
        await self._update_audio_status(
            book_id,
            AudioGenerationStatus.GENERATING,
            progress=0,
            message=f"Starting audio generation for {total_chunks} chunks..."
        )

        # Use provided settings or defaults
        settings = voice_settings or DEFAULT_VOICE_SETTINGS
        provider_id = settings.get("provider_id", "kokoro")
        voice_id = settings.get("voice_id", "am_michael")
        speed = settings.get("speed", 1.0)
        language = settings.get("language", "en")

        # Track results
        successful = 0
        failed = 0
        failed_chunks = []

        try:
            # Process chunks in prioritized order (first playable chunks first)
            for batch_start in range(0, len(chunk_order), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(chunk_order))
                batch_indices = [chunk_order[i] for i in range(batch_start, batch_end)]

                # Generate audio for batch concurrently
                tasks = [
                    self._generate_chunk_with_retry(
                        book_id=book_id,
                        chunk_index=idx,
                        user_id=user_id,
                        provider_id=provider_id,
                        voice_id=voice_id,
                        speed=speed,
                        language=language
                    )
                    for idx in batch_indices
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Count successes and failures
                for idx, result in zip(batch_indices, results):
                    if isinstance(result, Exception):
                        failed += 1
                        failed_chunks.append({"chunk_index": idx, "error": str(result)})
                        logger.error(f"Failed to generate chunk {idx}: {result}")
                    else:
                        successful += 1

                # Update progress (based on total chunks, not just chunk_order)
                progress = int((successful + failed) / total_chunks * 100)
                await self._update_audio_status(
                    book_id,
                    AudioGenerationStatus.GENERATING,
                    progress=progress,
                    message=f"Generated {successful}/{total_chunks} audio chunks...",
                    generated_count=successful,
                    failed_count=failed
                )

                logger.info(f"[{book_id}] Audio progress: {successful}/{total_chunks} ({progress}%)")

                # Small delay between batches to avoid overwhelming TTS service
                await asyncio.sleep(0.5)

            # Determine final status
            if failed == 0:
                final_status = AudioGenerationStatus.COMPLETED
                message = f"All {total_chunks} audio chunks generated successfully!"
            elif successful == 0:
                final_status = AudioGenerationStatus.FAILED
                message = f"Audio generation failed for all {total_chunks} chunks"
            else:
                final_status = AudioGenerationStatus.PARTIAL
                message = f"Generated {successful}/{total_chunks} chunks ({failed} failed)"

            # Update final status
            await self._update_audio_status(
                book_id,
                final_status,
                progress=100,
                message=message,
                generated_count=successful,
                failed_count=failed
            )

            # Update book with audio metadata
            await db.books.update_one(
                {"book_id": book_id},
                {
                    "$set": {
                        "audio_generated": True,
                        "audio_provider": provider_id,
                        "audio_voice_id": voice_id,
                        "audio_chunks_count": successful,
                        "audio_generated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"[{book_id}] Audio pre-generation complete: {successful}/{total_chunks} chunks")

            # Calculate and update chapter durations from audio
            if successful > 0:
                try:
                    from app.services.book_service import BookService
                    duration_result = await BookService.update_chapter_durations(book_id)
                    logger.info(
                        f"[{book_id}] Chapter durations updated: "
                        f"{duration_result.get('chapters_updated', 0)} chapters, "
                        f"{duration_result.get('total_duration_seconds', 0)}s total"
                    )
                except Exception as e:
                    logger.warning(f"[{book_id}] Failed to update chapter durations: {e}")

            return {
                "book_id": book_id,
                "status": final_status.value,
                "message": message,
                "total_chunks": total_chunks,
                "successful": successful,
                "failed": failed,
                "failed_chunks": failed_chunks if failed > 0 else None,
                "provider_used": provider_id,
                "voice_id": voice_id
            }

        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"[{book_id}] Audio pre-generation error: {e}", exc_info=True)

            await self._update_audio_status(
                book_id,
                AudioGenerationStatus.FAILED,
                progress=0,
                message=f"Audio generation failed: {error_msg}",
                error=error_msg
            )

            return {
                "book_id": book_id,
                "status": "error",
                "message": f"Audio generation failed: {error_msg}",
                "error": error_msg
            }

    async def _generate_chunk_with_retry(
        self,
        book_id: str,
        chunk_index: int,
        user_id: str,
        provider_id: str,
        voice_id: str,
        speed: float,
        language: str
    ) -> Dict[str, Any]:
        """
        Generate audio for a chunk with retry logic.

        Args:
            book_id: Book identifier
            chunk_index: Chunk index
            user_id: User ID for billing
            provider_id: TTS provider
            voice_id: Voice ID
            speed: Playback speed
            language: Language code

        Returns:
            AudioChunk result

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.audiobook_service.generate_chunk_audio(
                    book_id=book_id,
                    chunk_index=chunk_index,
                    user_id=user_id,
                    provider_id=provider_id,
                    voice_id=voice_id,
                    speed=speed,
                    language=language,
                    force_regenerate=False
                )
                return result

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.warning(f"Chunk {chunk_index} attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(self.retry_delay)

        raise last_error

    async def _update_audio_status(
        self,
        book_id: str,
        status: AudioGenerationStatus,
        progress: int,
        message: str,
        generated_count: int = 0,
        failed_count: int = 0,
        error: Optional[str] = None
    ) -> None:
        """
        Update audio generation status in database.

        Args:
            book_id: Book identifier
            status: Current status
            progress: Progress percentage (0-100)
            message: Status message
            generated_count: Number of chunks generated
            failed_count: Number of chunks failed
            error: Error message if failed
        """
        db = get_db()

        update_data = {
            "audio_generation_status": status.value,
            "audio_generation_progress": progress,
            "audio_generation_message": message,
            "audio_generated_count": generated_count,
            "audio_failed_count": failed_count,
            "updated_at": datetime.utcnow()
        }

        if error:
            update_data["audio_generation_error"] = error

        await db.books.update_one(
            {"book_id": book_id},
            {"$set": update_data}
        )

    async def get_audio_generation_status(self, book_id: str) -> Dict[str, Any]:
        """
        Get audio generation status for a book.

        Args:
            book_id: Book identifier

        Returns:
            Status information
        """
        db = get_db()
        book = await db.books.find_one({"book_id": book_id})

        if not book:
            return {
                "book_id": book_id,
                "status": "not_found",
                "message": "Book not found"
            }

        return {
            "book_id": book_id,
            "status": book.get("audio_generation_status", "pending"),
            "progress": book.get("audio_generation_progress", 0),
            "message": book.get("audio_generation_message", ""),
            "generated_count": book.get("audio_generated_count", 0),
            "failed_count": book.get("audio_failed_count", 0),
            "audio_generated": book.get("audio_generated", False),
            "provider": book.get("audio_provider"),
            "voice_id": book.get("audio_voice_id"),
            "generated_at": book.get("audio_generated_at")
        }

    async def resume_failed_generation(
        self,
        book_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Resume audio generation for failed/partial books.

        Only regenerates chunks that don't have cached audio.

        Args:
            book_id: Book identifier
            user_id: User ID

        Returns:
            Generation results
        """
        if not self._initialized:
            await self.initialize()

        db = get_db()
        book = await db.books.find_one({"book_id": book_id})

        if not book:
            raise ValueError(f"Book {book_id} not found")

        # Get voice settings used previously, or use defaults
        voice_settings = {
            "provider_id": book.get("audio_provider") or DEFAULT_VOICE_SETTINGS["provider_id"],
            "voice_id": book.get("audio_voice_id") or DEFAULT_VOICE_SETTINGS["voice_id"],
            "speed": DEFAULT_VOICE_SETTINGS["speed"],
            "language": DEFAULT_VOICE_SETTINGS["language"]
        }

        return await self.pregenerate_book_audio(
            book_id=book_id,
            user_id=user_id,
            voice_settings=voice_settings
        )


# Global service instance
_audio_pregeneration_service: Optional[AudioPregenerationService] = None


async def get_audio_pregeneration_service() -> AudioPregenerationService:
    """
    Get or create audio pre-generation service instance.

    Returns:
        AudioPregenerationService instance
    """
    global _audio_pregeneration_service

    if _audio_pregeneration_service is None:
        _audio_pregeneration_service = AudioPregenerationService()
        await _audio_pregeneration_service.initialize()

    return _audio_pregeneration_service


async def trigger_audio_pregeneration(
    book_id: str,
    user_id: str,
    voice_settings: Optional[Dict[str, Any]] = None
) -> None:
    """
    Trigger audio pre-generation as a background task.

    This is a fire-and-forget function - it starts the generation
    in the background and returns immediately.

    Args:
        book_id: Book identifier
        user_id: User ID who uploaded
        voice_settings: Optional voice settings override
    """
    async def _run_generation():
        try:
            service = await get_audio_pregeneration_service()
            await service.pregenerate_book_audio(
                book_id=book_id,
                user_id=user_id,
                voice_settings=voice_settings
            )
        except Exception as e:
            logger.error(f"Background audio generation failed for {book_id}: {e}")

    # Start as background task
    asyncio.create_task(_run_generation())
    logger.info(f"Triggered background audio generation for book {book_id}")

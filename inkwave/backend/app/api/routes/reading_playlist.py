"""
Playlist generation for combining multiple book chunks into one audio file.
"""

from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from pathlib import Path
import hashlib

from app.core.auth import get_test_user_or_current
from app.services.reading_service import ReadingService
from app.core.database import Database

router = APIRouter(prefix="/reading/playlist", tags=["reading"])
logger = logging.getLogger(__name__)


async def get_reading_service() -> ReadingService:
    """Get reading service instance."""
    db = Database.get_database()
    return ReadingService(db)


@router.get("/chunks/{book_id}")
async def generate_playlist(
    book_id: str,
    start: int = Query(..., description="Starting chunk index (inclusive)", ge=0),
    end: int = Query(..., description="Ending chunk index (inclusive)", ge=0),
    language: str = Query("en", description="Language code"),
    speed: float = Query(1.0, description="Playback speed (0.5 - 2.0)", ge=0.5, le=2.0),
    voice: str = Query("default", description="Voice selection (prepared for future TTS upgrade)"),
    current_user: dict = Depends(get_test_user_or_current),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Generate a playlist by combining multiple book chunks into one audio file.

    This is useful for:
    - Playing multiple chapters continuously
    - Generating long-form audio for offline listening
    - Creating audiobook segments

    Args:
        book_id: Book identifier
        start: Starting chunk index (inclusive)
        end: Ending chunk index (inclusive)
        language: Language code for TTS
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        Combined MP3 audio file

    Example:
        GET /api/v1/reading/playlist/chunks/book_123?start=0&end=5
        Returns: Combined audio of chunks 0-5
    """
    from gtts import gTTS
    from pydub import AudioSegment
    import io

    # Validate range
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid range: start ({start}) must be <= end ({end})"
        )

    chunk_count = end - start + 1
    if chunk_count > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many chunks requested ({chunk_count}). Maximum is 50 chunks per playlist."
        )

    # Map language codes
    lang_map = {
        "en": "en",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "zh": "zh-CN",
        "ja": "ja",
        "ko": "ko",
        "ar": "ar",
        "hi": "hi",
        "pt": "pt"
    }
    gtts_lang = lang_map.get(language.lower(), "en")

    # Create playlist cache key including speed and voice
    # Note: voice is included for future TTS upgrades (gTTS doesn't support voice selection)
    playlist_key = f"playlist_{book_id}_{start}_{end}_{gtts_lang}_{speed}_{voice}"
    cache_hash = hashlib.md5(playlist_key.encode()).hexdigest()

    storage_dir = Path("/opt/kasaai/apps/inkwave/backend/storage/audio/playlists")
    storage_dir.mkdir(parents=True, exist_ok=True)
    playlist_file = storage_dir / f"{cache_hash}.mp3"

    # Check if playlist is already cached
    if playlist_file.exists():
        logger.info(f"Using cached playlist for {book_id} chunks {start}-{end}")

        with open(playlist_file, "rb") as f:
            audio_data = f.read()

        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=playlist_{start}_{end}.mp3",
                "X-Book-ID": book_id,
                "X-Chunk-Range": f"{start}-{end}",
                "X-Chunk-Count": str(chunk_count),
                "X-Playback-Speed": str(speed),
                "X-Cached": "true",
                "X-TTS-Language": gtts_lang
            }
        )

    logger.info(f"Generating playlist for {book_id} chunks {start}-{end} ({chunk_count} chunks)")

    try:
        # Collect text from all chunks
        combined_text_parts = []

        for chunk_index in range(start, end + 1):
            chunk = await reading_service.get_chunk(book_id=book_id, chunk_index=chunk_index)

            if not chunk:
                logger.warning(f"Chunk {chunk_index} not found, skipping")
                continue

            text = chunk.text_optimized or chunk.text
            if text:
                # Add a slight pause between chunks for better listening
                combined_text_parts.append(text)

        if not combined_text_parts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No valid chunks found in range {start}-{end}"
            )

        # Join all text with brief pauses
        combined_text = ". ... ".join(combined_text_parts)

        logger.info(f"Combined {len(combined_text_parts)} chunks ({len(combined_text)} chars)")

        # Generate combined audio using gTTS
        tts = gTTS(text=combined_text, lang=gtts_lang, slow=False)

        # If speed is not 1.0, apply speed adjustment using pydub
        if speed != 1.0:
            # Save to temporary file first
            temp_file = storage_dir / f"temp_{cache_hash}.mp3"
            tts.save(str(temp_file))

            # Load with pydub and adjust speed
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(str(temp_file))

            # Apply speed change
            adjusted_audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            })
            adjusted_audio = adjusted_audio.set_frame_rate(audio.frame_rate)

            # Export to final cache file
            adjusted_audio.export(str(playlist_file), format="mp3")

            # Clean up temp file
            temp_file.unlink()
        else:
            # Save directly if no speed adjustment needed
            tts.save(str(playlist_file))

        # Read the generated file
        with open(playlist_file, "rb") as f:
            audio_data = f.read()

        logger.info(f"Playlist generated successfully ({len(audio_data)} bytes at {speed}x speed)")

        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=playlist_{start}_{end}.mp3",
                "X-Book-ID": book_id,
                "X-Chunk-Range": f"{start}-{end}",
                "X-Chunk-Count": str(chunk_count),
                "X-Playback-Speed": str(speed),
                "X-Cached": "false",
                "X-TTS-Language": gtts_lang,
                "X-Text-Length": str(len(combined_text))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Playlist generation failed: {str(e)}"
        )


@router.get("/chapter/{book_id}/{chapter_id}")
async def generate_chapter_audio(
    book_id: str,
    chapter_id: int,
    language: str = Query("en", description="Language code"),
    speed: float = Query(1.0, description="Playback speed (0.5 - 2.0)", ge=0.5, le=2.0),
    voice: str = Query("default", description="Voice selection (prepared for future TTS upgrade)"),
    current_user: dict = Depends(get_test_user_or_current),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Generate audio for an entire chapter.

    Args:
        book_id: Book identifier
        chapter_id: Chapter identifier
        language: Language code for TTS
        speed: Playback speed (0.5 - 2.0, default 1.0)
        voice: Voice selection (default, female, male) - prepared for future TTS upgrade

    Returns:
        Combined MP3 audio for the entire chapter
    """
    # Get book to find chapter range
    db = Database.get_database()
    book = await db.books.find_one({"book_id": book_id})

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book not found: {book_id}"
        )

    # Find chapter in book chapters
    chapter = None
    for ch in book.get("chapters", []):
        if ch.get("chapter_id") == chapter_id or book.get("chapters", []).index(ch) == chapter_id:
            chapter = ch
            break

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found in book"
        )

    # Get chunk range for chapter
    start_chunk = chapter.get("start_chunk_id", 0)
    end_chunk = chapter.get("end_chunk_id", 0)

    logger.info(f"Generating audio for chapter {chapter_id}: chunks {start_chunk}-{end_chunk}")

    # Redirect to playlist endpoint
    return await generate_playlist(
        book_id=book_id,
        start=start_chunk,
        end=end_chunk,
        language=language,
        speed=speed,
        voice=voice,
        current_user=current_user,
        reading_service=reading_service
    )

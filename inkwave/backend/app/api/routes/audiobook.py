"""
Audiobook Narration Routes for InkWave.

API endpoints for generating and streaming audiobook narration using
the Vapi TTS infrastructure (20+ TTS providers).

Author: AI Labs Africa
Created: November 26, 2025
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
from datetime import datetime
import uuid

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.audiobook_service import (
    AudiobookService,
    AudiobookGenerationRequest,
    AudiobookGenerationResult,
    AudioChunk,
    get_audiobook_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audiobook", tags=["audiobook"])


# Request/Response Models

class ChunkAudioRequest(BaseModel):
    """Request to generate audio for a single chunk."""
    provider_id: str = Field(default="styletts2", description="TTS provider")
    voice_id: Optional[str] = Field(default=None, description="Voice ID for cloning")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Playback speed")
    language: str = Field(default="en", description="Language code")
    force_regenerate: bool = Field(default=False, description="Force regeneration")


class StreamingAudioRequest(BaseModel):
    """Request to stream audiobook narration."""
    provider_id: str = Field(default="styletts2")
    voice_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    language: str = Field(default="en")
    start_chunk: int = Field(default=0)
    end_chunk: Optional[int] = None


class ChunkAudioResponse(BaseModel):
    """Response with generated audio chunk."""
    chunk_id: str
    chunk_index: int
    audio_url: str  # data:audio/mp3;base64,... format
    duration: float
    provider_used: str
    cached: bool = False


class BookAudioStatusResponse(BaseModel):
    """Status of book's generated audio."""
    book_id: str
    total_chunks: int
    generated_chunks: int
    total_duration: float
    providers_used: List[str]
    is_complete: bool


class ProvidersResponse(BaseModel):
    """Available audiobook TTS providers."""
    providers: dict


class VoiceInfo(BaseModel):
    """Voice information."""
    id: str
    name: str
    description: str
    gender: str
    accent: Optional[str] = None
    best_for: List[str] = []
    sample_text: Optional[str] = None


class VoicesResponse(BaseModel):
    """Available voices response."""
    provider: str
    voices: List[VoiceInfo]


class BookProgressResponse(BaseModel):
    """Book-level progress response."""
    book_id: str
    total_chunks: int
    total_duration: float
    generated_chunks: int
    listened_chunks: int
    current_chunk: int
    current_position: float  # seconds within current chunk
    overall_progress: float  # 0.0 to 1.0
    chunk_durations: List[float]  # Duration of each chunk


class AudiobookProgressUpdate(BaseModel):
    """Request model for updating audiobook progress."""
    current_chunk: Optional[int] = Field(default=0, description="Current chunk index")
    current_position: Optional[float] = Field(default=0.0, description="Position in seconds within current chunk")
    total_time_minutes: Optional[float] = Field(default=0.0, description="Total listening time in minutes")


class PreloadRequest(BaseModel):
    """Request to preload audio chunks."""
    start_chunk: int = 0
    num_chunks: int = Field(default=3, ge=1, le=10)
    provider_id: str = "styletts2"
    voice_id: Optional[str] = None
    speed: float = 1.0


class PreloadResponse(BaseModel):
    """Response with preloaded audio URLs."""
    book_id: str
    preloaded_chunks: List[dict]
    total_duration: float


class NarrationInfoResponse(BaseModel):
    """Response with narration information including skip indices."""
    book_id: str
    total_chunks: int
    narratable_chunks: int
    skip_indices: List[int] = Field(
        default_factory=list,
        description="Chunk indices to skip during playback"
    )
    content_types: dict = Field(
        default_factory=dict,
        description="Count of each content type"
    )
    chapter_starts: List[dict] = Field(
        default_factory=list,
        description="Chunk indices where chapters start"
    )
    skip_reasons: dict = Field(
        default_factory=dict,
        description="Reasons for skipping each chunk"
    )


# Endpoints

@router.get("/providers", response_model=ProvidersResponse)
async def get_audiobook_providers(
    current_user: dict = Depends(get_current_user)
):
    """
    Get available TTS providers for audiobook narration.

    Returns list of providers with their capabilities and
    recommended use cases.

    Example response:
        {
            "providers": {
                "styletts2": {
                    "name": "StyleTTS2",
                    "description": "Expressive, natural-sounding",
                    "supports_cloning": true,
                    "languages": ["en"],
                    "recommended_for": ["novels", "stories"]
                }
            }
        }
    """
    try:
        service = await get_audiobook_service()
        providers = await service.get_available_providers()
        return ProvidersResponse(providers=providers)

    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get providers: {str(e)}"
        )


@router.get("/books/{book_id}/narration-info", response_model=NarrationInfoResponse)
async def get_book_narration_info(
    book_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get narration information for a book.

    Returns information about which chunks will be narrated vs skipped,
    enabling professional audiobook playback that excludes:
    - Copyright notices
    - Table of contents
    - Publisher instructions
    - ISBN/metadata
    - References and index

    The frontend should use skip_indices to automatically advance
    past non-narratable content during playback.

    Args:
        book_id: Book identifier

    Returns:
        NarrationInfoResponse with:
            - total_chunks: Total chunks in book
            - narratable_chunks: Chunks that will be narrated
            - skip_indices: Chunk indices to skip
            - content_types: Count of each content type
            - chapter_starts: Where chapters begin
    """
    try:
        service = await get_audiobook_service()
        info = await service.get_narration_info(book_id)
        return NarrationInfoResponse(**info)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get narration info for {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get narration info: {str(e)}"
        )


@router.get("/voices/{provider_id}", response_model=VoicesResponse)
async def get_provider_voices(
    provider_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get available voices for a specific TTS provider.

    For OpenAI TTS providers, returns the 6 available voices:
    - alloy: Balanced, neutral - great for general narration
    - echo: Deep, warm - male protagonists, non-fiction
    - fable: British, expressive - fiction, storytelling
    - onyx: Deep, authoritative - business, self-help
    - nova: Young, friendly - YA, children's books
    - shimmer: Soft, gentle - romance, meditation

    Args:
        provider_id: TTS provider (e.g., "openai_tts", "styletts2")

    Returns:
        VoicesResponse with available voices
    """
    # OpenAI TTS voices
    openai_voices = [
        VoiceInfo(
            id="alloy",
            name="Alloy",
            description="Balanced, neutral - great for general narration",
            gender="neutral",
            accent="American",
            best_for=["non-fiction", "general", "audiobooks"],
            sample_text="The art of storytelling has been with us since the dawn of human civilization."
        ),
        VoiceInfo(
            id="echo",
            name="Echo",
            description="Deep, warm - ideal for male protagonists and non-fiction",
            gender="male",
            accent="American",
            best_for=["thrillers", "business", "biography"],
            sample_text="In the quiet of the night, the detective reviewed the evidence one more time."
        ),
        VoiceInfo(
            id="fable",
            name="Fable",
            description="British, expressive - perfect for fiction and storytelling",
            gender="neutral",
            accent="British",
            best_for=["fiction", "fantasy", "children's books"],
            sample_text="Once upon a time, in a land far away, there lived a curious young adventurer."
        ),
        VoiceInfo(
            id="onyx",
            name="Onyx",
            description="Deep, authoritative - business and self-help books",
            gender="male",
            accent="American",
            best_for=["self-help", "business", "motivational"],
            sample_text="Success is not final, failure is not fatal. It is the courage to continue that counts."
        ),
        VoiceInfo(
            id="nova",
            name="Nova",
            description="Young, friendly - YA and children's books",
            gender="female",
            accent="American",
            best_for=["young adult", "children's", "contemporary"],
            sample_text="Today was going to be different. Sarah could feel it in her bones."
        ),
        VoiceInfo(
            id="shimmer",
            name="Shimmer",
            description="Soft, gentle - romance, meditation, poetry",
            gender="female",
            accent="American",
            best_for=["romance", "poetry", "meditation", "spirituality"],
            sample_text="Take a deep breath. Feel the warmth of the sun on your skin."
        )
    ]

    # Provider-specific voice mappings
    voice_mappings = {
        "openai_tts": openai_voices,
        "openai_tts_hd": openai_voices,
        "styletts2": [
            VoiceInfo(
                id="default",
                name="Default",
                description="Natural, expressive narration",
                gender="neutral"
            )
        ],
        "kokoro": [
            VoiceInfo(id="af_sky", name="Sky", description="Clear, articulate voice", gender="female"),
            VoiceInfo(id="am_adam", name="Adam", description="Warm, engaging male voice", gender="male")
        ],
        "coqui_xtts": [
            VoiceInfo(
                id="default",
                name="Default",
                description="Multilingual voice with cloning support",
                gender="neutral"
            )
        ]
    }

    if provider_id not in voice_mappings:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_id}' not found or has no voice options"
        )

    return VoicesResponse(
        provider=provider_id,
        voices=voice_mappings[provider_id]
    )


@router.get("/books/{book_id}/progress", response_model=BookProgressResponse)
async def get_book_progress(
    book_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get book-level playback progress.

    Returns overall progress across all chunks, including:
    - Total chunks and duration
    - Current playback position
    - Progress percentage (0.0 to 1.0)
    - Duration of each chunk for seek calculations

    This is essential for Libby-style book progress bars.
    """
    try:
        db = get_db()

        # Get book chunks
        chunks = await db.book_chunks.find(
            {"book_id": book_id}
        ).sort("chunk_index", 1).to_list(None)

        if not chunks:
            raise HTTPException(status_code=404, detail=f"Book {book_id} not found")

        # Get user's reading session
        session = await db.reading_sessions.find_one({
            "user_id": current_user.user_id,
            "book_id": book_id
        })

        # Calculate chunk durations (use audio_duration if available, else estimate)
        chunk_durations = []
        for chunk in chunks:
            if chunk.get("audio_duration"):
                chunk_durations.append(chunk["audio_duration"])
            else:
                # Estimate: ~150 words/min, ~5 chars/word = ~750 chars/min
                word_count = chunk.get("word_count", len(chunk.get("text", "")) // 5)
                estimated_duration = (word_count / 150) * 60
                chunk_durations.append(estimated_duration)

        total_duration = sum(chunk_durations)

        # Get current position from session
        current_chunk = session.get("current_chunk_index", 0) if session else 0
        current_position = session.get("current_position_seconds", 0) if session else 0

        # Calculate overall progress
        elapsed_duration = sum(chunk_durations[:current_chunk]) + current_position
        overall_progress = elapsed_duration / total_duration if total_duration > 0 else 0

        # Count generated chunks (those with audio_url)
        generated_chunks = sum(1 for c in chunks if c.get("audio_url"))

        # Count listened chunks (from session)
        listened_chunks = session.get("listened_chunks", current_chunk) if session else 0

        return BookProgressResponse(
            book_id=book_id,
            total_chunks=len(chunks),
            total_duration=total_duration,
            generated_chunks=generated_chunks,
            listened_chunks=listened_chunks,
            current_chunk=current_chunk,
            current_position=current_position,
            overall_progress=overall_progress,
            chunk_durations=chunk_durations
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get book progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/books/{book_id}/preload", response_model=PreloadResponse)
async def preload_chunks(
    book_id: str,
    request: PreloadRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Preload audio for upcoming chunks.

    This endpoint pre-generates audio for the next N chunks to enable
    seamless playback without buffering gaps. Essential for good UX.

    Recommended: Preload 2-3 chunks ahead while playing current chunk.
    """
    try:
        service = await get_audiobook_service()

        preloaded = []
        total_duration = 0

        for i in range(request.num_chunks):
            chunk_index = request.start_chunk + i
            try:
                # Get user_id from Pydantic model (current_user is UserInDB object)
                user_id = current_user.user_id
                if not user_id:
                    raise HTTPException(status_code=400, detail="User ID not found in authentication token")

                audio_chunk = await service.generate_chunk_audio(
                    book_id=book_id,
                    chunk_index=chunk_index,
                    user_id=user_id,
                    provider_id=request.provider_id,
                    voice_id=request.voice_id,
                    speed=request.speed,
                    force_regenerate=False
                )

                # Use the correct MIME type
                audio_format = audio_chunk.audio_format or "mp3"
                mime_type = f"audio/{audio_format}"
                preloaded.append({
                    "chunk_index": chunk_index,
                    "chunk_id": audio_chunk.chunk_id,
                    "audio_url": f"data:{mime_type};base64,{audio_chunk.audio_base64}",
                    "duration": audio_chunk.duration
                })
                total_duration += audio_chunk.duration

            except ValueError:
                # Chunk doesn't exist (end of book)
                break
            except Exception as e:
                logger.warning(f"Failed to preload chunk {chunk_index}: {e}")
                continue

        return PreloadResponse(
            book_id=book_id,
            preloaded_chunks=preloaded,
            total_duration=total_duration
        )

    except Exception as e:
        logger.error(f"Failed to preload chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/books/{book_id}/progress")
async def update_book_progress(
    book_id: str,
    current_chunk: int = 0,
    current_position: float = 0,
    total_time_minutes: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Update book playback progress and listening time.

    Called periodically by the frontend to save playback position and accumulated time.
    Enables resume functionality and accurate usage tracking.
    """
    try:
        db = get_db()
        from datetime import datetime

        # Prepare update data
        update_data = {
            "current_chunk_index": current_chunk,
            "current_position_seconds": current_position,
            "last_accessed": datetime.utcnow()
        }

        # Update total listening time if provided
        if total_time_minutes > 0:
            update_data["total_time_spent_minutes"] = total_time_minutes

        # Upsert reading session
        await db.reading_sessions.update_one(
            {
                "user_id": current_user.user_id,
                "book_id": book_id
            },
            {
                "$set": update_data,
                "$setOnInsert": {
                    "started_at": datetime.utcnow(),
                    "listened_chunks": 0,
                    "completed": False,
                    "bookmarks": []
                }
            },
            upsert=True
        )

        return {"success": True, "message": "Progress updated"}

    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/books/{book_id}/chunks/{chunk_index}/audio",
    response_model=ChunkAudioResponse
)
async def generate_chunk_audio(
    book_id: str,
    chunk_index: int,
    request: ChunkAudioRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate audio narration for a single book chunk.

    This endpoint generates TTS audio for a specific chunk of the book.
    Audio is cached for subsequent requests unless force_regenerate is True.

    Args:
        book_id: Book identifier
        chunk_index: Chunk index (0-based)
        request: Audio generation parameters

    Returns:
        ChunkAudioResponse with data URL for immediate playback
    """
    try:
        service = await get_audiobook_service()

        audio_chunk = await service.generate_chunk_audio(
            book_id=book_id,
            chunk_index=chunk_index,
            user_id=current_user.user_id,
            provider_id=request.provider_id,
            voice_id=request.voice_id,
            speed=request.speed,
            language=request.language,
            force_regenerate=request.force_regenerate
        )

        # Validate audio_base64 before creating data URL
        if not audio_chunk.audio_base64 or len(audio_chunk.audio_base64.strip()) == 0:
            logger.error(f"Empty audio_base64 for chunk {chunk_index} of book {book_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio generation returned empty data for chunk {chunk_index}"
            )

        # Use the correct MIME type based on the actual audio format
        audio_format = audio_chunk.audio_format or "mp3"
        mime_type = f"audio/{audio_format}"

        return ChunkAudioResponse(
            chunk_id=audio_chunk.chunk_id,
            chunk_index=audio_chunk.chunk_index,
            audio_url=f"data:{mime_type};base64,{audio_chunk.audio_base64}",
            duration=audio_chunk.duration,
            provider_used=audio_chunk.provider_used,
            cached=False  # Will be True on cache hits
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate chunk audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio generation failed: {str(e)}"
        )


@router.get("/books/{book_id}/chunks/{chunk_index}/audio")
async def get_chunk_audio(
    book_id: str,
    chunk_index: int,
    provider_id: str = Query(default="styletts2"),
    voice_id: Optional[str] = Query(default=None),
    speed: float = Query(default=1.0, ge=0.5, le=2.0),
    language: str = Query(default="en"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get or generate audio for a book chunk (GET-friendly endpoint).

    This endpoint is useful for HTML5 audio elements that need a direct URL.
    Uses caching by default.

    For non-narratable chunks (front matter, TOC, etc.), returns a special
    "skipped" response with status 200 that the frontend can handle gracefully.
    """
    try:
        service = await get_audiobook_service()

        # Get user_id from Pydantic model (current_user is UserInDB object)
        user_id = current_user.user_id
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in authentication token")

        audio_chunk = await service.generate_chunk_audio(
            book_id=book_id,
            chunk_index=chunk_index,
            user_id=user_id,
            provider_id=provider_id,
            voice_id=voice_id,
            speed=speed,
            language=language,
            force_regenerate=False  # Use cache - don't regenerate unless explicitly requested
        )

        # Check if chunk was skipped (non-narratable content)
        if audio_chunk.provider_used == "skipped":
            logger.info(
                f"Chunk {chunk_index} of book {book_id} is non-narratable, returning skip response"
            )
            return {
                "chunk_id": audio_chunk.chunk_id,
                "chunk_index": audio_chunk.chunk_index,
                "audio_url": None,
                "duration": 0,
                "provider_used": "skipped",
                "skipped": True,
                "skip_reason": "Non-narratable content (front matter, TOC, copyright, etc.)"
            }

        # Validate audio_base64 before creating data URL
        if not audio_chunk.audio_base64 or len(audio_chunk.audio_base64.strip()) == 0:
            logger.error(
                f"Empty audio_base64 for chunk {chunk_index} of book {book_id}. "
                f"Provider: {audio_chunk.provider_used}, Duration: {audio_chunk.duration}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Audio generation returned empty data for chunk {chunk_index}"
            )

        # Log audio data info for debugging
        audio_url_length = len(audio_chunk.audio_base64)
        logger.info(
            f"Generated audio for chunk {chunk_index}: "
            f"base64_length={audio_url_length}, duration={audio_chunk.duration:.2f}s, "
            f"provider={audio_chunk.provider_used}"
        )

        # Validate base64 is not just whitespace
        if audio_url_length < 100:  # Base64 audio should be much longer
            logger.warning(
                f"Suspiciously short audio_base64 for chunk {chunk_index}: {audio_url_length} chars"
            )

        # Use the correct MIME type based on the actual audio format
        audio_format = audio_chunk.audio_format or "mp3"
        mime_type = f"audio/{audio_format}"
        audio_url = f"data:{mime_type};base64,{audio_chunk.audio_base64}"

        return {
            "chunk_id": audio_chunk.chunk_id,
            "chunk_index": audio_chunk.chunk_index,
            "audio_url": audio_url,
            "duration": audio_chunk.duration,
            "provider_used": audio_chunk.provider_used
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get chunk audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/books/{book_id}/generate")
async def generate_book_audio(
    book_id: str,
    request: StreamingAudioRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate audio for entire book or section.

    This endpoint generates audio for all chunks in the specified range.
    Useful for pre-generating audio before playback.

    Args:
        book_id: Book identifier
        request: Generation parameters including chunk range

    Returns:
        AudiobookGenerationResult with all generated chunks
    """
    try:
        service = await get_audiobook_service()

        generation_request = AudiobookGenerationRequest(
            book_id=book_id,
            provider_id=request.provider_id,
            voice_id=request.voice_id,
            speed=request.speed,
            language=request.language,
            start_chunk=request.start_chunk,
            end_chunk=request.end_chunk
        )

        result = await service.generate_book_audio(
            request=generation_request,
            user_id=current_user.user_id
        )

        logger.info(
            f"Generated audio for book {book_id}: "
            f"{result.successful_chunks}/{result.total_chunks} chunks, "
            f"{result.total_duration:.2f}s"
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate book audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books/{book_id}/stream")
async def stream_book_audio(
    book_id: str,
    provider_id: str = Query(default="styletts2"),
    voice_id: Optional[str] = Query(default=None),
    speed: float = Query(default=1.0, ge=0.5, le=2.0),
    language: str = Query(default="en"),
    start_chunk: int = Query(default=0),
    end_chunk: Optional[int] = Query(default=None),
    current_user: dict = Depends(get_current_user)
):
    """
    Stream audiobook narration as Server-Sent Events (SSE).

    This endpoint streams audio chunks as they are generated, enabling
    real-time playback while generation continues in the background.

    Each event contains a JSON object with the audio chunk data.

    Example client usage:
        ```javascript
        const eventSource = new EventSource('/api/v1/audiobook/books/abc/stream');
        eventSource.onmessage = (event) => {
            const chunk = JSON.parse(event.data);
            playAudio(chunk.audio_url);
        };
        ```

    Args:
        book_id: Book identifier
        provider_id: TTS provider
        voice_id: Optional voice ID
        speed: Playback speed
        language: Language code
        start_chunk: Starting chunk index
        end_chunk: Ending chunk index (None = all remaining)

    Returns:
        StreamingResponse with SSE events
    """
    try:
        service = await get_audiobook_service()

        async def generate_stream():
            """Generate SSE events for each audio chunk."""
            try:
                async for audio_chunk in service.stream_book_audio(
                    book_id=book_id,
                    user_id=current_user.user_id,
                    provider_id=provider_id,
                    voice_id=voice_id,
                    speed=speed,
                    language=language,
                    start_chunk=start_chunk,
                    end_chunk=end_chunk
                ):
                    # Format as SSE event with correct MIME type
                    audio_format = audio_chunk.audio_format or "mp3"
                    mime_type = f"audio/{audio_format}"
                    chunk_data = {
                        "chunk_id": audio_chunk.chunk_id,
                        "chunk_index": audio_chunk.chunk_index,
                        "audio_url": f"data:{mime_type};base64,{audio_chunk.audio_base64}",
                        "duration": audio_chunk.duration,
                        "provider_used": audio_chunk.provider_used,
                        "text_length": audio_chunk.text_length
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'event': 'complete'})}\n\n"

            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/books/{book_id}/status", response_model=BookAudioStatusResponse)
async def get_book_audio_status(
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get status of generated audio for a book.

    Shows how many chunks have audio generated and total duration.

    Args:
        book_id: Book identifier

    Returns:
        BookAudioStatusResponse with generation status
    """
    try:
        # Get all chunks for book
        chunks = await db.book_chunks.find({
            "book_id": book_id
        }).to_list(length=None)

        if not chunks:
            raise HTTPException(status_code=404, detail="Book not found")

        # Count chunks with audio
        generated_chunks = [c for c in chunks if c.get("audio_generated")]
        total_duration = sum(c.get("audio_duration", 0) for c in generated_chunks)
        providers_used = list(set(c.get("audio_provider") for c in generated_chunks if c.get("audio_provider")))

        return BookAudioStatusResponse(
            book_id=book_id,
            total_chunks=len(chunks),
            generated_chunks=len(generated_chunks),
            total_duration=total_duration,
            providers_used=providers_used,
            is_complete=len(generated_chunks) == len(chunks)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get book status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/books/{book_id}/audio")
async def clear_book_audio_cache(
    book_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Clear all cached audio for a book.

    This allows regeneration with different voice/settings.

    Args:
        book_id: Book identifier

    Returns:
        Success message with count of cleared chunks
    """
    try:
        # Clear audio metadata from all chunks
        result = await db.book_chunks.update_many(
            {"book_id": book_id},
            {
                "$unset": {
                    "audio_generated": "",
                    "audio_duration": "",
                    "audio_provider": "",
                    "audio_generated_at": ""
                }
            }
        )

        logger.info(f"Cleared audio cache for book {book_id}: {result.modified_count} chunks")

        return {
            "message": "Audio cache cleared successfully",
            "chunks_cleared": result.modified_count
        }

    except Exception as e:
        logger.error(f"Failed to clear audio cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/books/{book_id}/progress")
async def update_audiobook_progress(
    book_id: str,
    progress_data: Optional[AudiobookProgressUpdate] = None,
    current_chunk: int = Query(default=None, description="Current chunk index (query param fallback)"),
    current_position: float = Query(default=None, description="Position in seconds (query param fallback)"),
    total_time_minutes: float = Query(default=None, description="Total listening time in minutes (query param fallback)"),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update audiobook listening progress and track listening time.

    Creates or updates a reading session and tracks listening time for leaderboard/profile stats.
    This endpoint is called periodically by the frontend while playing audio.

    Accepts data either in request body (preferred) or query parameters.

    Args:
        book_id: Book identifier
        progress_data: Progress data in request body (optional)
        current_chunk: Current chunk index being played (query param fallback)
        current_position: Position in seconds within the current chunk (query param fallback)
        total_time_minutes: Total accumulated listening time in minutes (query param fallback)

    Returns:
        Success message
    """
    try:
        # Handle both body and query params
        if progress_data:
            chunk = progress_data.current_chunk or 0
            position = progress_data.current_position or 0.0
            time_min = progress_data.total_time_minutes or 0.0
        else:
            chunk = current_chunk if current_chunk is not None else 0
            position = current_position if current_position is not None else 0.0
            time_min = total_time_minutes if total_time_minutes is not None else 0.0
        
        logger.info(f"Progress update: book_id={book_id}, chunk={chunk}, position={position}, time={time_min} min")
        
        from app.services.reading_service import ReadingService
        from app.services.leaderboard_service import LeaderboardService
        from app.core.database import Database

        user_id = current_user.user_id
        reading_service = ReadingService(db)
        leaderboard_service = LeaderboardService(db)

        # Get or create reading session for this book
        sessions = await reading_service.get_user_sessions(user_id=user_id, active_only=True)
        session = None
        
        # Find existing session for this book
        for s in sessions:
            if s.book_id == book_id:
                session = s
                break

        # Create session if it doesn't exist
        if not session:
            session = await reading_service.create_session(user_id=user_id, book_id=book_id)

        # Get old listening time
        old_time = session.total_time_spent_minutes or 0.0
        new_time = time_min
        listening_delta = new_time - old_time

        # Update session progress
        from app.models.session import ReadingSessionUpdate
        update = ReadingSessionUpdate(
            current_chunk_index=chunk,
            current_position_seconds=position,
            total_time_spent_minutes=int(new_time)
        )
        
        updated_session = await reading_service.update_progress(
            session_id=session.session_id,
            user_id=user_id,
            update=update
        )

        # Track listening time with wallet transactions (same logic as reading.py)
        if listening_delta > 0:
            try:
                # Get the time that was tracked in the last transaction
                last_transaction_time = getattr(session, 'last_transaction_time', None) or 0.0
                accumulated_minutes = new_time - last_transaction_time

                now = datetime.utcnow()
                should_create_transaction = False

                if not session.last_transaction_at:
                    # First transaction for this session
                    should_create_transaction = True
                    accumulated_minutes = new_time
                else:
                    # Check if 5 minutes have passed OR accumulated time >= 5 minutes
                    time_since_last = (now - session.last_transaction_at).total_seconds()
                    if time_since_last >= 300 or accumulated_minutes >= 5.0:
                        should_create_transaction = True

                if should_create_transaction and accumulated_minutes > 0:
                    # Get book title
                    book_doc = await db.books.find_one({"book_id": book_id})
                    book_title = book_doc.get("title", "Unknown Book") if book_doc else "Unknown Book"

                    # Create wallet transaction
                    transaction_doc = {
                        "_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "amount": float(accumulated_minutes) * 0.10,
                        "type": "debit",
                        "description": f"Listening: {book_title} - {accumulated_minutes:.1f} minutes (FREE)",
                        "metadata": {
                            "service": "inkwave_listening",
                            "book_id": book_id,
                            "book_title": book_title,
                            "duration_minutes": float(accumulated_minutes),
                            "rate_per_minute": 0.10,
                            "session_id": session.session_id,
                            "free": True
                        },
                        "created_at": now,
                        "updated_at": now
                    }
                    await db.wallet_transactions.insert_one(transaction_doc)
                    logger.info(f"Tracked FREE listening: {user_id} - {accumulated_minutes:.1f} minutes for {book_title}")

                    # Update session's last_transaction_at and last_transaction_time
                    await reading_service.sessions_collection.update_one(
                        {"session_id": session.session_id},
                        {"$set": {
                            "last_transaction_at": now,
                            "last_transaction_time": new_time
                        }}
                    )

                    # Update user listening stats
                    await leaderboard_service.update_user_listening_stats(user_id=user_id)

                    logger.info(f"Recorded {accumulated_minutes} minutes of listening for user {user_id} on book {book_id}")

            except Exception as e:
                logger.error(f"Failed to record listening activity: {e}", exc_info=True)

        return {
            "message": "Progress updated successfully",
            "session_id": session.session_id,
            "total_time_minutes": new_time
        }

    except Exception as e:
        logger.error(f"Failed to update audiobook progress: {e}", exc_info=True)
        # Don't fail silently - return error but don't crash
        return {
            "message": "Progress update failed (non-critical)",
            "error": str(e)
        }


@router.get("/stats")
async def get_audiobook_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get audiobook service statistics.

    Returns stats on chunks generated, audio duration, cache hits, etc.
    """
    try:
        service = await get_audiobook_service()
        stats = await service.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Convenience endpoint for direct playback

@router.get("/books/{book_id}/play")
async def play_book_from_position(
    book_id: str,
    chunk_index: int = Query(default=0, description="Start from chunk"),
    provider_id: str = Query(default="styletts2"),
    speed: float = Query(default=1.0),
    current_user: dict = Depends(get_current_user)
):
    """
    Get audio for immediate playback from a specific position.

    Returns the next few chunks of audio for seamless playback.
    Useful for starting playback at a bookmark position.

    Args:
        book_id: Book identifier
        chunk_index: Starting chunk
        provider_id: TTS provider
        speed: Playback speed

    Returns:
        First audio chunk plus metadata for subsequent chunks
    """
    try:
        service = await get_audiobook_service()
        db = get_db()

        # Get total chunk count
        total_chunks = await db.book_chunks.count_documents({"book_id": book_id})

        if total_chunks == 0:
            raise HTTPException(status_code=404, detail="Book not found")

        # Generate audio for the starting chunk
        audio_chunk = await service.generate_chunk_audio(
            book_id=book_id,
            chunk_index=chunk_index,
            user_id=current_user.user_id,
            provider_id=provider_id,
            speed=speed
        )

        # Use the correct MIME type
        audio_format = audio_chunk.audio_format or "mp3"
        mime_type = f"audio/{audio_format}"

        return {
            "book_id": book_id,
            "current_chunk": {
                "chunk_id": audio_chunk.chunk_id,
                "chunk_index": audio_chunk.chunk_index,
                "audio_url": f"data:{mime_type};base64,{audio_chunk.audio_base64}",
                "duration": audio_chunk.duration,
                "provider_used": audio_chunk.provider_used
            },
            "total_chunks": total_chunks,
            "has_next": chunk_index < total_chunks - 1,
            "has_previous": chunk_index > 0,
            "playback_info": {
                "provider_id": provider_id,
                "speed": speed,
                "next_chunk_url": f"/api/v1/audiobook/books/{book_id}/chunks/{chunk_index + 1}/audio" if chunk_index < total_chunks - 1 else None
            }
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start playback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

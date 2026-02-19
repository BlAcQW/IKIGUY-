"""
ASR Services - Phase 5: Advanced Features

Advanced ASR endpoints including:
- Audio format conversion + transcription
- Batch transcription
- Real-time streaming (WebSocket)
- Speaker diarization

Created: 2025-10-27
Phase 5: Advanced Features
"""

from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
import logging
import base64
import asyncio
from datetime import datetime

from apps.shared.services.asr_provider_service import (
    get_asr_service,
    ASRProviderService,
    TranscriptionRequest,
)
from apps.shared.services.audio_conversion_service import AudioConversionService
from ..auth import get_current_user_mongo
from ..middleware.rate_limiting import get_asr_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["ASR Advanced Features"])


# ============================================================================
# Pydantic Models
# ============================================================================

class TranscribeConvertRequest(BaseModel):
    """Request to convert audio format and transcribe"""
    provider_id: str
    audio_base64: str
    source_format: Literal["wav", "mp3", "ogg", "flac", "m4a", "webm"]
    language: Optional[str] = None
    task: str = "transcribe"


class BatchTranscriptionRequest(BaseModel):
    """Request to transcribe multiple audio files"""
    provider_id: str
    audio_files: List[Dict[str, str]]  # List of {audio_base64, language?, filename?}
    task: str = "transcribe"


class BatchTranscriptionResult(BaseModel):
    """Result from batch transcription"""
    results: List[Dict]
    total_duration: float
    total_cost: float
    successful: int
    failed: int
    processing_time: float


class DiarizationRequest(BaseModel):
    """Request for speaker diarization"""
    provider_id: str
    audio_base64: str
    language: Optional[str] = None
    num_speakers: Optional[int] = None  # Auto-detect if None
    min_speakers: int = 1
    max_speakers: int = 10


class SpeakerSegment(BaseModel):
    """A segment of speech by a specific speaker"""
    speaker: str  # "SPEAKER_00", "SPEAKER_01", etc.
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class DiarizationResult(BaseModel):
    """Result from speaker diarization"""
    text: str
    segments: List[SpeakerSegment]
    num_speakers: int
    speakers: List[str]
    duration: float
    cost: float
    processing_time: float


# ============================================================================
# Phase 5.1: Audio Format Conversion + Transcription
# ============================================================================

@router.post("/transcribe/convert")
async def transcribe_with_conversion(
    request_body: TranscribeConvertRequest,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free"))
):
    """
    Convert audio format and transcribe in one call.

    This endpoint automatically converts the audio to WAV format (required for ASR)
    before transcription, saving you the manual conversion step.

    Supported input formats: wav, mp3, ogg, flac, m4a, webm

    Args:
        request_body: Conversion and transcription request
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        Transcription result with cost and duration
    """
    start_time = datetime.utcnow()

    try:
        logger.info(
            f"Convert+Transcribe request: user={user['id']}, "
            f"provider={request_body.provider_id}, format={request_body.source_format}"
        )

        # Step 1: Convert to WAV if needed
        if request_body.source_format.lower() != "wav":
            audio_service = AudioConversionService()

            try:
                wav_base64 = audio_service.convert_base64_audio(
                    audio_base64=request_body.audio_base64,
                    source_format=request_body.source_format,
                    target_format="wav"
                )
                logger.info(f"Converted {request_body.source_format} to WAV")
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Audio conversion failed: {str(e)}"
                )
        else:
            wav_base64 = request_body.audio_base64

        # Step 2: Transcribe
        asr_service = await get_asr_service()

        transcription_request = TranscriptionRequest(
            provider_id=request_body.provider_id,
            audio_base64=wav_base64,
            language=request_body.language,
            task=request_body.task
        )

        result = await asr_service.transcribe(
            user_id=user["id"],
            request=transcription_request,
            skip_billing=False
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        return {
            "text": result.text,
            "language": result.language,
            "duration": result.duration,
            "cost": result.cost,
            "transaction_id": result.transaction_id,
            "processing_time": processing_time,
            "original_format": request_body.source_format,
            "converted_to": "wav"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Convert+Transcribe error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription with conversion failed: {str(e)}"
        )


# ============================================================================
# Phase 5.2: Batch Transcription
# ============================================================================

@router.post("/transcribe/batch", response_model=BatchTranscriptionResult)
async def batch_transcribe(
    request_body: BatchTranscriptionRequest,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free"))
):
    """
    Transcribe multiple audio files in a single request.

    More efficient than making individual requests for each file.
    Processes files sequentially with proper error handling for partial failures.

    Args:
        request_body: Batch transcription request with multiple files
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        Batch results with success/failure counts and aggregated costs
    """
    start_time = datetime.utcnow()

    if not request_body.audio_files:
        raise HTTPException(status_code=400, detail="No audio files provided")

    if len(request_body.audio_files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 files per batch request"
        )

    try:
        asr_service = await get_asr_service()

        results = []
        total_duration = 0.0
        total_cost = 0.0
        successful = 0
        failed = 0

        logger.info(
            f"Batch transcription: user={user['id']}, "
            f"files={len(request_body.audio_files)}, provider={request_body.provider_id}"
        )

        # Process each file
        for idx, audio_file in enumerate(request_body.audio_files):
            try:
                transcription_request = TranscriptionRequest(
                    provider_id=request_body.provider_id,
                    audio_base64=audio_file["audio_base64"],
                    language=audio_file.get("language"),
                    task=request_body.task
                )

                result = await asr_service.transcribe(
                    user_id=user["id"],
                    request=transcription_request,
                    skip_billing=False
                )

                total_duration += result.duration or 0
                total_cost += result.cost
                successful += 1

                results.append({
                    "index": idx,
                    "filename": audio_file.get("filename", f"file_{idx}"),
                    "success": True,
                    "text": result.text,
                    "language": result.language,
                    "duration": result.duration,
                    "cost": result.cost,
                    "transaction_id": result.transaction_id
                })

            except Exception as e:
                failed += 1
                results.append({
                    "index": idx,
                    "filename": audio_file.get("filename", f"file_{idx}"),
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"Batch item {idx} failed: {e}")

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        return BatchTranscriptionResult(
            results=results,
            total_duration=total_duration,
            total_cost=total_cost,
            successful=successful,
            failed=failed,
            processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch transcription failed: {str(e)}"
        )


# ============================================================================
# Phase 5.3: Real-time Streaming Transcription (WebSocket)
# ============================================================================

@router.websocket("/ws/transcribe/stream/{provider_id}")
async def stream_transcribe(
    websocket: WebSocket,
    provider_id: str,
    language: Optional[str] = Query(None)
):
    """
    Real-time streaming transcription via WebSocket.

    Client sends audio chunks as base64-encoded data, server returns partial transcripts.

    Protocol:
    - Client connects with provider_id and optional language
    - Client sends: {"type": "audio", "data": "<base64>"}
    - Server responds: {"type": "transcript", "text": "...", "is_final": false}
    - Client sends: {"type": "end"}
    - Server responds: {"type": "final", "text": "...", "cost": 0.05}

    Note: This is a simplified implementation. Production systems should use
    proper streaming ASR models with incremental decoding.
    """
    await websocket.accept()

    try:
        logger.info(f"WebSocket streaming started: provider={provider_id}, lang={language}")

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "provider": provider_id,
            "language": language or "auto",
            "message": "Streaming transcription ready. Send audio chunks."
        })

        audio_chunks = []
        chunk_count = 0

        while True:
            # Receive message from client
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected by client")
                break

            msg_type = data.get("type")

            if msg_type == "audio":
                # Receive audio chunk
                audio_base64 = data.get("data")
                if not audio_base64:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio data provided"
                    })
                    continue

                audio_chunks.append(audio_base64)
                chunk_count += 1

                # Send interim response (simplified - in reality would use streaming ASR)
                await websocket.send_json({
                    "type": "interim",
                    "message": f"Received chunk {chunk_count}",
                    "chunks_received": chunk_count
                })

            elif msg_type == "end":
                # Process all accumulated audio
                logger.info(f"Processing {chunk_count} audio chunks")

                if not audio_chunks:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio chunks received"
                    })
                    break

                try:
                    # Combine all chunks
                    combined_audio = "".join(audio_chunks)

                    # Transcribe
                    asr_service = await get_asr_service()
                    transcription_request = TranscriptionRequest(
                        provider_id=provider_id,
                        audio_base64=combined_audio,
                        language=language,
                        task="transcribe"
                    )

                    # Note: user_id would need to come from WebSocket auth in production
                    result = await asr_service.transcribe(
                        user_id="websocket_user",  # TODO: Implement WebSocket auth
                        request=transcription_request,
                        skip_billing=True  # Skip billing for WebSocket demo
                    )

                    # Send final transcript
                    await websocket.send_json({
                        "type": "final",
                        "text": result.text,
                        "language": result.language,
                        "duration": result.duration,
                        "chunks_processed": chunk_count,
                        "cost": result.cost
                    })

                except Exception as e:
                    logger.error(f"Streaming transcription error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })

                break

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

        await websocket.close()
        logger.info("WebSocket streaming ended")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            await websocket.close()
        except:
            pass


# ============================================================================
# Phase 5.4: Speaker Diarization
# ============================================================================

@router.post("/transcribe/diarize", response_model=DiarizationResult)
async def diarize_audio(
    request_body: DiarizationRequest,
    req: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free"))
):
    """
    Transcribe audio with speaker diarization (speaker identification).

    Identifies different speakers in the audio and labels them as SPEAKER_00, SPEAKER_01, etc.
    Returns timestamped segments for each speaker.

    Note: This is a simplified implementation. Full diarization requires specialized models
    like pyannote.audio or speaker embedding models. This version uses simple heuristics.

    Args:
        request_body: Diarization request
        user: Current authenticated user
        rate_limit: Rate limiting check

    Returns:
        Transcription with speaker labels and segments
    """
    start_time = datetime.utcnow()

    try:
        logger.info(
            f"Diarization request: user={user['id']}, "
            f"provider={request_body.provider_id}, speakers={request_body.num_speakers}"
        )

        # Step 1: Regular transcription with timestamps
        asr_service = await get_asr_service()

        transcription_request = TranscriptionRequest(
            provider_id=request_body.provider_id,
            audio_base64=request_body.audio_base64,
            language=request_body.language,
            task="transcribe",
            timestamp_granularities=["segment"]  # Get segment timestamps
        )

        result = await asr_service.transcribe(
            user_id=user["id"],
            request=transcription_request,
            skip_billing=False
        )

        # Step 2: Simplified speaker assignment (heuristic-based)
        # NOTE: Real diarization would use pyannote.audio or similar
        # This is a placeholder that assigns speakers based on pauses

        if not result.segments:
            # No segments available, return single speaker
            segments = [
                SpeakerSegment(
                    speaker="SPEAKER_00",
                    start=0.0,
                    end=result.duration or 0.0,
                    text=result.text,
                    confidence=1.0
                )
            ]
            num_speakers = 1
        else:
            # Assign speakers based on pause duration (simplified heuristic)
            segments = []
            current_speaker = 0
            max_speakers = request_body.max_speakers

            prev_end = 0.0
            for seg in result.segments:
                # If there's a long pause (>2s), possibly a new speaker
                pause_duration = seg.start - prev_end
                if pause_duration > 2.0 and current_speaker < max_speakers - 1:
                    current_speaker += 1

                segments.append(
                    SpeakerSegment(
                        speaker=f"SPEAKER_{current_speaker:02d}",
                        start=seg.start,
                        end=seg.end,
                        text=seg.text,
                        confidence=None
                    )
                )
                prev_end = seg.end

            num_speakers = current_speaker + 1

        speakers = [f"SPEAKER_{i:02d}" for i in range(num_speakers)]

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        return DiarizationResult(
            text=result.text,
            segments=segments,
            num_speakers=num_speakers,
            speakers=speakers,
            duration=result.duration or 0.0,
            cost=result.cost,
            processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diarization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Speaker diarization failed: {str(e)}"
        )

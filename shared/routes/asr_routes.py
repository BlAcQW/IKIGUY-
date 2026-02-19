"""
Unified ASR (Speech Recognition) API Routes

Provides standardized ASR endpoints for all backend applications.
Includes transcription, streaming, provider management, and cost estimation.

Mount in FastAPI app:
    from apps.shared.routes.asr_routes import router as asr_router
    app.include_router(asr_router, prefix="/api/asr", tags=["ASR"])

Endpoints:
    POST   /transcribe           - Transcribe audio with billing
    POST   /transcribe/upload    - Upload file for transcription
    GET    /providers            - List available ASR providers
    GET    /providers/{id}       - Get provider details
    GET    /languages/{id}       - Get supported languages for provider
    POST   /estimate-cost        - Estimate transcription cost
    GET    /health               - Health check all providers

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, File, UploadFile, Form, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import base64
import logging

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.services.asr_provider_service import (
    ASRProviderService,
    TranscriptionRequest,
    TranscriptionResult,
    ProviderHealth,
    get_asr_service,
)
from shared.integration.ai_services.provider_registry import (
    get_global_registry,
    get_default_asr_providers_config,
    ProviderType,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize WebSocket router (mounted separately at /ws/asr)
ws_router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class TranscribeRequest(BaseModel):
    """Request model for audio transcription."""
    provider_id: str = Field(
        default="faster_whisper_large",
        description="ASR provider ID. Default: whisper.ailabsafrica.com (faster_whisper_large)"
    )
    audio_base64: str = Field(..., description="Base64-encoded audio file")
    language: Optional[str] = Field(
        None,
        description="Language code (e.g., 'en', 'tw', 'fr'). None for auto-detect."
    )
    task: str = Field(
        default="transcribe",
        description="Task type: 'transcribe' or 'translate' (translate to English)"
    )
    response_format: str = Field(
        default="json",
        description="Response format: 'json', 'text', 'srt', 'vtt'"
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (0.0-1.0). Lower = more deterministic."
    )
    timestamps: bool = Field(
        default=False,
        description="Include word-level timestamps"
    )


class TranscribeResponse(BaseModel):
    """Response model for transcription result."""
    text: str = Field(..., description="Transcribed text")
    provider_id: str = Field(..., description="Provider used")
    language: Optional[str] = Field(None, description="Detected/specified language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    segments: Optional[List[Dict[str, Any]]] = Field(
        None, description="Transcription segments with timestamps"
    )
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Billing transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    provider_id: str = Field(
        default="faster_whisper_large",
        description="ASR provider ID"
    )
    audio_base64: Optional[str] = Field(
        None, description="Base64-encoded audio (for accurate estimate)"
    )
    duration_seconds: Optional[float] = Field(
        None, description="Audio duration in seconds (alternative to audio_base64)"
    )


class CostEstimateResponse(BaseModel):
    """Response model for cost estimation."""
    provider_id: str
    estimated_cost_usd: float
    estimated_duration_seconds: float
    pricing_note: str


class ASRProviderInfo(BaseModel):
    """Provider information for ASR."""
    id: str
    name: str
    endpoint: str
    status: str
    languages: int
    language_list: List[str]
    capabilities: Dict[str, bool]
    description: str
    is_default: bool = False


class ProvidersResponse(BaseModel):
    """Response for provider listing."""
    providers: Dict[str, ASRProviderInfo]
    count: int
    default_provider: str
    timestamp: str


# ============================================================================
# Authentication Helper
# ============================================================================

async def get_user_id_from_header(authorization: str = Header(None)) -> Optional[str]:
    """
    Extract user ID from JWT token for billing.

    Falls back to anonymous if no valid token provided.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    # Try to decode JWT to get user_id
    try:
        import jwt
        # Decode without verification to get user_id
        # In production, apps should verify the token
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub") or decoded.get("user_id")
    except Exception:
        return None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    request: TranscribeRequest,
    authorization: str = Header(None),
    skip_billing: bool = Query(
        default=False,
        description="Skip wallet billing (for testing/free tier)"
    ),
):
    """
    Transcribe audio to text.

    Supports multiple ASR providers with automatic billing.
    Default provider: whisper.ailabsafrica.com (faster_whisper_large)

    Audio Requirements:
    - Supported formats: WAV, MP3, FLAC, OGG, M4A, WEBM
    - Max duration: 30 minutes (configurable per provider)
    - Recommended: 16kHz mono WAV for best results

    Languages:
    - Set language=None for auto-detection
    - Use ISO language codes (en, fr, es, tw, etc.)
    - Use task='translate' to translate to English
    """
    try:
        # Get user ID for billing
        user_id = await get_user_id_from_header(authorization)
        if not user_id:
            user_id = "anonymous"
            skip_billing = True  # Anonymous users don't get billed

        # Get ASR service
        asr_service = await get_asr_service()

        # Prepare timestamp granularities
        timestamp_granularities = ["word", "segment"] if request.timestamps else None

        # Create transcription request
        asr_request = TranscriptionRequest(
            provider_id=request.provider_id,
            audio_base64=request.audio_base64,
            language=request.language,
            task=request.task,
            response_format=request.response_format,
            temperature=request.temperature,
            timestamp_granularities=timestamp_granularities,
        )

        # Transcribe
        result = await asr_service.transcribe(
            user_id=user_id,
            request=asr_request,
            skip_billing=skip_billing,
        )

        # Convert segments to dict for response
        segments = None
        if result.segments:
            segments = [
                {
                    "id": s.id,
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                }
                for s in result.segments
            ]

        return TranscribeResponse(
            text=result.text,
            provider_id=result.provider_id,
            language=result.language,
            duration=result.duration,
            segments=segments,
            cost=result.cost,
            transaction_id=result.transaction_id,
            processing_time=result.processing_time,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/transcribe/upload", response_model=TranscribeResponse)
async def transcribe_upload(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    provider_id: str = Form(
        default="faster_whisper_large",
        description="ASR provider ID"
    ),
    language: Optional[str] = Form(
        default=None,
        description="Language code or None for auto-detect"
    ),
    task: str = Form(default="transcribe"),
    timestamps: bool = Form(default=False),
    authorization: str = Header(None),
    skip_billing: bool = Query(default=False),
):
    """
    Transcribe uploaded audio file.

    Alternative to /transcribe for multipart file uploads.
    Accepts audio files directly instead of base64-encoded data.
    """
    try:
        # Read file content
        content = await file.read()

        # Convert to base64
        audio_base64 = base64.b64encode(content).decode("utf-8")

        # Reuse the main transcribe endpoint
        request = TranscribeRequest(
            provider_id=provider_id,
            audio_base64=audio_base64,
            language=language,
            task=task,
            timestamps=timestamps,
        )

        return await transcribe_audio(
            request=request,
            authorization=authorization,
            skip_billing=skip_billing,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.get("/providers", response_model=ProvidersResponse)
async def list_asr_providers(
    online_only: bool = Query(
        default=False,
        description="Filter to show only online providers"
    ),
):
    """
    List all available ASR providers.

    Returns provider info including:
    - Supported languages
    - Capabilities (timestamps, diarization, etc.)
    - Current status
    - Default provider marker
    """
    try:
        # Ensure registry has ASR providers initialized
        registry = get_global_registry()
        if not registry.get_asr_providers():
            asr_config = get_default_asr_providers_config()
            registry.register_providers_from_config(asr_config, provider_type=ProviderType.ASR)

        # Get ASR service for health status
        asr_service = await get_asr_service()
        health_list = await asr_service.get_all_providers_health()
        health_map = {h.provider_id: h.status for h in health_list}

        # Build provider list
        providers = {}
        asr_providers = registry.get_asr_providers()

        for provider in asr_providers:
            status = health_map.get(provider.id, "unknown")

            # Skip offline providers if online_only
            if online_only and status != "online":
                continue

            # Extract capabilities
            capabilities = {}
            if provider.capabilities:
                caps = provider.capabilities
                capabilities = {
                    "multiLanguage": getattr(caps, "multiLanguage", False),
                    "timestamps": getattr(caps, "timestamps", False),
                    "wordLevelTimestamps": getattr(caps, "wordLevelTimestamps", False),
                    "diarization": getattr(caps, "diarization", False),
                    "punctuation": getattr(caps, "punctuation", False),
                    "translation": getattr(caps, "translation", False),
                    "streaming": getattr(caps, "streaming", False),
                }
                capabilities = {k: v for k, v in capabilities.items() if v}

            providers[provider.id] = ASRProviderInfo(
                id=provider.id,
                name=provider.name,
                endpoint=provider.endpoint,
                status=status,
                languages=getattr(provider, "languages", 0),
                language_list=getattr(provider, "languageList", []),
                capabilities=capabilities,
                description=provider.description or "",
                is_default=provider.id in ["faster_whisper_large", "whisper_large_v3"],
            )

        return ProvidersResponse(
            providers=providers,
            count=len(providers),
            default_provider="faster_whisper_large",
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing ASR providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider_id}")
async def get_asr_provider(provider_id: str):
    """
    Get details for a specific ASR provider.

    Returns detailed capabilities, supported languages, and current status.
    """
    try:
        registry = get_global_registry()
        provider = registry.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"ASR provider not found: {provider_id}"
            )

        # Get health status
        asr_service = await get_asr_service()
        health = await asr_service.get_provider_health(provider_id)

        # Extract capabilities
        capabilities = {}
        if provider.capabilities:
            caps = provider.capabilities
            capabilities = {
                "multiLanguage": getattr(caps, "multiLanguage", False),
                "timestamps": getattr(caps, "timestamps", False),
                "wordLevelTimestamps": getattr(caps, "wordLevelTimestamps", False),
                "diarization": getattr(caps, "diarization", False),
                "punctuation": getattr(caps, "punctuation", False),
                "translation": getattr(caps, "translation", False),
                "streaming": getattr(caps, "streaming", False),
            }

        return {
            "id": provider.id,
            "name": provider.name,
            "endpoint": provider.endpoint,
            "status": health.status,
            "languages": getattr(provider, "languages", 0),
            "language_list": getattr(provider, "languageList", []),
            "capabilities": capabilities,
            "description": provider.description or "",
            "model_name": getattr(provider, "model_name", None),
            "requires_api_key": getattr(provider, "requires_api_key", False),
            "is_default": provider_id in ["faster_whisper_large", "whisper_large_v3"],
            "response_time_ms": health.response_time_ms,
            "last_check": health.last_check.isoformat() if health.last_check else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ASR provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages/{provider_id}")
async def get_supported_languages(provider_id: str):
    """
    Get supported languages for an ASR provider.

    Returns list of ISO language codes supported by the provider.
    """
    try:
        asr_service = await get_asr_service()
        languages = await asr_service.get_available_languages(provider_id)

        if not languages:
            # Try to get from registry directly
            registry = get_global_registry()
            provider = registry.get_provider(provider_id)
            if provider:
                languages = getattr(provider, "languageList", [])

        return {
            "provider_id": provider_id,
            "languages": languages,
            "count": len(languages),
            "supports_auto_detect": True,  # Most Whisper-based providers support auto-detect
        }

    except Exception as e:
        logger.error(f"Error getting languages for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_transcription_cost(request: CostEstimateRequest):
    """
    Estimate transcription cost before processing.

    Provide either:
    - audio_base64: Base64-encoded audio for accurate size-based estimate
    - duration_seconds: Known duration for direct calculation

    Pricing varies by provider. Self-hosted providers (whisper.ailabsafrica.com)
    have lower costs than cloud providers (OpenAI, Groq).
    """
    try:
        asr_service = await get_asr_service()

        # Calculate estimated duration
        if request.audio_base64:
            estimated_cost = await asr_service.estimate_cost(
                provider_id=request.provider_id,
                audio_base64=request.audio_base64
            )
            # Estimate duration from size
            audio_bytes = base64.b64decode(request.audio_base64)
            audio_size_kb = len(audio_bytes) / 1024
            estimated_duration = audio_size_kb / 32  # ~32KB per second
        elif request.duration_seconds:
            estimated_duration = request.duration_seconds
            # Use usage calculator directly
            estimated_cost = asr_service.usage_calculator.calculate_asr_cost(
                duration_seconds=estimated_duration,
                provider=request.provider_id
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either audio_base64 or duration_seconds"
            )

        # Pricing note based on provider
        pricing_note = "Self-hosted Whisper - low cost, no API fees"
        if "openai" in request.provider_id.lower():
            pricing_note = "OpenAI Whisper - $0.006 per minute"
        elif "groq" in request.provider_id.lower():
            pricing_note = "Groq Whisper - fast inference, usage-based pricing"

        return CostEstimateResponse(
            provider_id=request.provider_id,
            estimated_cost_usd=estimated_cost,
            estimated_duration_seconds=estimated_duration,
            pricing_note=pricing_note,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cost estimation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_asr_health():
    """
    Health check for all ASR providers.

    Returns status summary for monitoring and alerting.
    """
    try:
        asr_service = await get_asr_service()
        health_list = await asr_service.get_all_providers_health(force_refresh=True)

        online_count = sum(1 for h in health_list if h.status == "online")
        offline_count = sum(1 for h in health_list if h.status == "offline")
        degraded_count = sum(1 for h in health_list if h.status == "degraded")

        providers_status = {
            h.provider_id: {
                "status": h.status,
                "endpoint": h.endpoint,
                "response_time_ms": h.response_time_ms,
                "error": h.error_message,
            }
            for h in health_list
        }

        return {
            "status": "healthy" if online_count > 0 else "degraded",
            "total_providers": len(health_list),
            "online": online_count,
            "offline": offline_count,
            "degraded": degraded_count,
            "providers": providers_status,
            "default_provider": "faster_whisper_large",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# WebSocket Streaming Endpoint
# ============================================================================

@ws_router.websocket("/stream")
async def asr_stream_websocket(
    websocket: WebSocket,
    provider_id: str = Query("faster_whisper_large", description="ASR provider ID"),
    language: Optional[str] = Query(None, description="Language code (e.g., 'en', 'tw')"),
    token: Optional[str] = Query(None, description="Authentication token")
):
    """
    Real-time ASR streaming via WebSocket.

    Protocol:
    - Client connects with provider_id and optional language
    - Client sends: {"type": "audio", "data": "<base64>"}
    - Server responds: {"type": "interim", "text": "...", "is_final": false}
    - Client sends: {"type": "end"}
    - Server responds: {"type": "final", "text": "...", "cost": 0.05}

    Note: This accumulates audio chunks and processes them when "end" is received.
    For true streaming ASR with incremental decoding, use a streaming-capable model.
    """
    await websocket.accept()

    try:
        logger.info(f"WebSocket ASR streaming started: provider={provider_id}, lang={language}")

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

                # Send interim acknowledgment
                await websocket.send_json({
                    "type": "interim",
                    "message": f"Received chunk {chunk_count}",
                    "chunks_received": chunk_count
                })

            elif msg_type == "end":
                # Process all accumulated audio
                logger.info(f"Processing {chunk_count} audio chunks for final transcription")

                if not audio_chunks:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio chunks received"
                    })
                    break

                try:
                    # Combine all chunks
                    combined_audio = "".join(audio_chunks)

                    # Get ASR service
                    asr_service = await get_asr_service()

                    # Create transcription request
                    asr_request = TranscriptionRequest(
                        provider_id=provider_id,
                        audio_base64=combined_audio,
                        language=language,
                        task="transcribe",
                        response_format="json",
                        temperature=0.0,
                        timestamp_granularities=None,
                    )

                    # Transcribe (skip billing for WebSocket demo - apps can enable if needed)
                    result = await asr_service.transcribe(
                        user_id="websocket_user",  # TODO: Extract from token in production
                        request=asr_request,
                        skip_billing=True  # Skip billing for WebSocket streaming
                    )

                    # Send final transcript
                    await websocket.send_json({
                        "type": "final",
                        "text": result.text,
                        "language": result.language,
                        "duration": result.duration,
                        "cost": result.cost,
                        "processing_time": result.processing_time,
                    })

                    # Reset for next recording
                    audio_chunks = []
                    chunk_count = 0

                except Exception as e:
                    logger.error(f"Transcription error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })

            elif msg_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})

            elif msg_type == "close":
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# VAPI Custom Transcriber WebSocket Endpoint
# ============================================================================

@ws_router.websocket("/vapi-transcriber")
async def vapi_custom_transcriber(
    websocket: WebSocket,
    provider_id: str = Query("faster_whisper_large", description="ASR provider ID"),
    language: Optional[str] = Query("en", description="Language code (e.g., 'en', 'tw')"),
):
    """
    VAPI-compatible custom transcriber WebSocket endpoint.

    Protocol (per VAPI docs):
    1. VAPI sends initial JSON: {"type": "start", "encoding": "linear16", "container": "raw", "sampleRate": 16000, "channels": 2}
    2. VAPI streams binary PCM audio (16-bit, 16kHz, stereo)
    3. Server responds with: {"type": "transcriber-response", "transcription": "...", "channel": "customer"}

    Audio format: Signed 16-bit little-endian PCM (S16LE), 16000 Hz, stereo (2 channels)
    """
    await websocket.accept()

    # Audio buffer for accumulating PCM chunks
    audio_buffer = bytearray()
    sample_rate = 16000
    channels = 2
    # Process every 1 second of audio for better transcription quality
    chunk_duration_ms = 1000
    bytes_per_sample = 2  # 16-bit = 2 bytes
    chunk_size = int(sample_rate * channels * bytes_per_sample * chunk_duration_ms / 1000)

    # Track connection state
    is_connected = True
    pending_tasks = []

    total_bytes_received = 0
    message_count = 0
    audio_message_count = 0

    try:
        logger.info(f"VAPI custom transcriber started: provider={provider_id}, lang={language}")

        while is_connected:
            try:
                # VAPI sends both text (JSON) and binary (audio) messages
                message = await websocket.receive()
                message_count += 1

                if message["type"] == "websocket.disconnect":
                    logger.info(f"VAPI WebSocket disconnected after {message_count} messages, {total_bytes_received} bytes received")
                    is_connected = False
                    break

                elif message["type"] == "websocket.receive":
                    # Check if it's text (JSON) or binary (audio)
                    if "text" in message:
                        # JSON message from VAPI
                        import json
                        data = json.loads(message["text"])
                        msg_type = data.get("type")
                        logger.info(f"VAPI transcriber JSON message: type={msg_type}, full={data}")

                        if msg_type == "start":
                            # VAPI handshake message
                            sample_rate = data.get("sampleRate", 16000)
                            channels = data.get("channels", 2)
                            encoding = data.get("encoding", "linear16")
                            logger.info(f"VAPI transcriber handshake: encoding={encoding}, sampleRate={sample_rate}, channels={channels}")

                            # Recalculate chunk size based on actual sample rate
                            chunk_size = int(sample_rate * channels * bytes_per_sample * chunk_duration_ms / 1000)
                            logger.info(f"VAPI transcriber chunk_size set to {chunk_size} bytes ({chunk_duration_ms}ms of audio)")

                        elif msg_type == "stop":
                            # VAPI stop message - process remaining audio
                            logger.info(f"VAPI transcriber stop signal received, processing remaining {len(audio_buffer)} bytes")
                            is_connected = False
                            break

                        elif msg_type == "ping":
                            await websocket.send_json({"type": "pong"})

                    elif "bytes" in message:
                        # Binary PCM audio from VAPI
                        audio_data = message["bytes"]
                        audio_buffer.extend(audio_data)
                        total_bytes_received += len(audio_data)
                        audio_message_count += 1

                        # Log every 10 audio messages
                        if audio_message_count % 10 == 0:
                            logger.info(f"VAPI audio: {audio_message_count} msgs, {total_bytes_received} total bytes, buffer={len(audio_buffer)}/{chunk_size}")

                        # Process when we have enough audio
                        if len(audio_buffer) >= chunk_size:
                            # Process in background to not block receiving
                            audio_copy = bytes(audio_buffer)
                            audio_buffer.clear()

                            logger.info(f"VAPI: Processing {len(audio_copy)} bytes of audio (enough for transcription)")

                            # Create background task for transcription
                            task = asyncio.create_task(
                                _process_and_send_transcription_safe(
                                    websocket, audio_copy, provider_id, language, sample_rate, channels
                                )
                            )
                            pending_tasks.append(task)

                            # Clean up completed tasks
                            pending_tasks = [t for t in pending_tasks if not t.done()]

                    else:
                        # Unknown message format
                        logger.warning(f"VAPI transcriber unknown message format: keys={message.keys()}")

            except Exception as e:
                error_str = str(e).lower()
                if "disconnect" in error_str or "closed" in error_str:
                    is_connected = False
                    break
                logger.error(f"VAPI transcriber message error: {e}")
                continue

    except Exception as e:
        logger.error(f"VAPI transcriber error: {e}", exc_info=True)
    finally:
        is_connected = False

        # Wait for pending transcription tasks (with timeout)
        if pending_tasks:
            try:
                await asyncio.wait(pending_tasks, timeout=2.0)
            except:
                pass

        try:
            await websocket.close()
        except:
            pass


async def _process_and_send_transcription_safe(
    websocket: WebSocket,
    audio_bytes: bytes,
    provider_id: str,
    language: str,
    sample_rate: int,
    channels: int
):
    """
    Safe wrapper for transcription that handles WebSocket closure.
    """
    try:
        await _process_and_send_transcription(
            websocket, bytearray(audio_bytes), provider_id, language, sample_rate, channels
        )
    except Exception as e:
        error_str = str(e).lower()
        if "closed" not in error_str and "disconnect" not in error_str:
            logger.error(f"Transcription task error: {e}")


async def _process_and_send_transcription(
    websocket: WebSocket,
    audio_buffer: bytearray,
    provider_id: str,
    language: str,
    sample_rate: int,
    channels: int
):
    """
    Process accumulated PCM audio and send transcription to VAPI.

    Args:
        websocket: WebSocket connection
        audio_buffer: Raw PCM audio bytes
        provider_id: ASR provider to use
        language: Language code
        sample_rate: Audio sample rate (Hz)
        channels: Number of audio channels (1=mono, 2=stereo)
    """
    import io
    import wave
    import time

    start_time = time.time()
    logger.info(f"VAPI transcription: Starting processing {len(audio_buffer)} bytes, provider={provider_id}, lang={language}")

    try:
        # Convert stereo to mono if needed (VAPI sends stereo, most ASR wants mono)
        audio_bytes = bytes(audio_buffer)

        if channels == 2:
            # Extract customer channel (channel 0) from stereo
            # Stereo PCM interleaves: [L0, R0, L1, R1, ...] where each sample is 2 bytes
            import struct
            mono_samples = []
            for i in range(0, len(audio_bytes), 4):  # 4 bytes per stereo frame (2 channels * 2 bytes)
                if i + 2 <= len(audio_bytes):
                    # Take left channel (customer) - first 2 bytes of each frame
                    sample = struct.unpack('<h', audio_bytes[i:i+2])[0]
                    mono_samples.append(sample)

            # Convert back to bytes
            audio_bytes = struct.pack('<' + 'h' * len(mono_samples), *mono_samples)
            channels = 1

        # Check minimum duration
        duration_seconds = len(audio_bytes) / (sample_rate * channels * 2)
        if duration_seconds < 0.1:
            # Too short, skip
            return

        # Convert raw PCM to WAV format for ASR
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)

        wav_buffer.seek(0)
        wav_bytes = wav_buffer.read()

        # Convert to base64 for ASR service
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

        # Get ASR service and transcribe
        asr_service = await get_asr_service()

        asr_request = TranscriptionRequest(
            provider_id=provider_id,
            audio_base64=audio_base64,
            language=language,
            task="transcribe",
            response_format="json",
            temperature=0.0,
            timestamp_granularities=None,
        )

        result = await asr_service.transcribe(
            user_id="vapi_transcriber",
            request=asr_request,
            skip_billing=True  # Internal usage
        )

        # Send transcription to VAPI in expected format
        elapsed_time = time.time() - start_time
        logger.info(f"VAPI transcription: ASR returned in {elapsed_time:.2f}s, text='{result.text[:100] if result.text else '(empty)'}'")

        if result.text and result.text.strip():
            try:
                response_payload = {
                    "type": "transcriber-response",
                    "transcription": result.text.strip(),
                    "channel": "customer"  # Customer channel (channel 0)
                }
                await websocket.send_json(response_payload)
                total_elapsed = time.time() - start_time
                logger.info(f"VAPI transcription SENT: '{result.text.strip()[:50]}...' ({duration_seconds:.2f}s audio, {total_elapsed:.2f}s total)")
            except Exception as send_err:
                # WebSocket may have closed, this is expected
                error_str = str(send_err).lower()
                if "closed" not in error_str and "disconnect" not in error_str:
                    logger.warning(f"Could not send transcription: {send_err}")
        else:
            logger.info(f"VAPI transcription: No text result from ASR, skipping send")

    except Exception as e:
        error_str = str(e).lower()
        if "closed" not in error_str and "disconnect" not in error_str:
            logger.error(f"VAPI transcription processing error: {e}", exc_info=True)


# ============================================================================
# Initialization Helper
# ============================================================================

def initialize_asr_routes():
    """
    Initialize ASR routes on app startup.

    Call this from your app's startup event to pre-warm the ASR service.
    """
    logger.info("ASR routes initialized")

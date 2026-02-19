"""
TTS Services Routes

Provides API endpoints for TTS Lab interface with automatic billing and health monitoring.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Form, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field, validator
from pathlib import Path
from datetime import datetime
import logging
import base64
import bleach
from typing import Dict, List, Optional

from apps.shared.services.tts_provider_service import (
    get_tts_service,
    TTSProviderService,
    SynthesisRequest,
    VoiceCloneRequest,
)
from ..auth import get_current_user_mongo
from ..middleware.rate_limiting import get_tts_rate_limit
from ..exceptions.tts_errors import (
    TTSError,
    InsufficientBalanceError,
    ProviderOfflineError,
    TextTooLongError,
    InvalidProviderError,
    InvalidLanguageError,
    AudioProcessingError,
    map_exception_to_tts_error,
)
from ..services.audio_history_service import (
    get_audio_history_service,
    AudioHistoryListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["TTS Services"])

# Voice files directory
VOICE_FILES_DIR = Path("/opt/kasaai/apps/voice-lab/voices")

# Available voice samples
GHANAIAN_VOICES = {
    "nana_aba.wav": {
        "id": "nana_aba",
        "name": "Nana Aba",
        "description": "Professional female Ghanaian voice",
        "size": "6.1MB",
    },
    "adom_okyere.wav": {
        "id": "adom_okyere",
        "name": "Adom Okyere",
        "description": "Male Ghanaian voice",
        "size": "13MB",
    },
    "juliet_bawuah.wav": {
        "id": "juliet_bawuah",
        "name": "Juliet Bawuah",
        "description": "Female Ghanaian voice",
        "size": "3.0MB",
    },
    "nana_aba_24_bit.wav": {
        "id": "nana_aba_24bit",
        "name": "Nana Aba (24-bit)",
        "description": "High-quality 24-bit professional female Ghanaian voice",
        "size": "9.2MB",
    },
    "archbishop_1_ref.wav": {
        "id": "archbishop_1",
        "name": "Archbishop 1",
        "description": "Male Ghanaian voice - Archbishop reference",
        "size": "751KB",
    },
    "archbishop_2_ref.wav": {
        "id": "archbishop_2",
        "name": "Archbishop 2",
        "description": "Male Ghanaian voice - Archbishop reference",
        "size": "751KB",
    },
}


# ============================================================================
# Pydantic Models for API Requests
# ============================================================================

class SynthesisRequestAPI(BaseModel):
    """API request for basic TTS synthesis."""
    provider_id: str = Field(..., description="TTS provider ID")
    text: str = Field(..., description="Text to synthesize")
    language: str = Field("en", description="Language code")
    voice_id: Optional[str] = Field(None, description="Voice ID or speaker")
    speed: float = Field(1.0, description="Speech speed (0.5-2.0)")
    pitch: float = Field(0.0, description="Pitch adjustment")
    remove_silence: bool = Field(False, description="Remove silence from output")
    output_format: str = Field("wav", description="Output format")

    @validator('text')
    def sanitize_text(cls, v):
        """
        Sanitize text input to prevent XSS attacks and enforce character limit.

        Strips all HTML tags and scripts, and enforces 5000 character limit.
        """
        # Strip all HTML tags and scripts (XSS prevention)
        sanitized = bleach.clean(v, tags=[], strip=True)

        # Enforce character limit
        if len(sanitized) > 5000:
            raise ValueError(
                f"Text is too long ({len(sanitized)} characters). "
                f"Maximum allowed: 5000 characters. Please shorten your text."
            )

        # Ensure not empty after sanitization
        if not sanitized or not sanitized.strip():
            raise ValueError("Text cannot be empty after sanitization.")

        return sanitized.strip()


class VoiceCloneRequestAPI(BaseModel):
    """API request for voice cloning synthesis."""
    provider_id: str = Field(..., description="TTS provider ID")
    text: str = Field(..., description="Text to synthesize")
    reference_audio_base64: str = Field(..., description="Reference audio in base64")
    language: str = Field("en", description="Language code")
    speed: float = Field(1.0, description="Speech speed")
    remove_silence: bool = Field(False, description="Remove silence")

    @validator('text')
    def sanitize_text(cls, v):
        """
        Sanitize text input to prevent XSS attacks and enforce character limit.

        Strips all HTML tags and scripts, and enforces 5000 character limit.
        """
        # Strip all HTML tags and scripts (XSS prevention)
        sanitized = bleach.clean(v, tags=[], strip=True)

        # Enforce character limit
        if len(sanitized) > 5000:
            raise ValueError(
                f"Text is too long ({len(sanitized)} characters). "
                f"Maximum allowed: 5000 characters. Please shorten your text."
            )

        # Ensure not empty after sanitization
        if not sanitized or not sanitized.strip():
            raise ValueError("Text cannot be empty after sanitization.")

        return sanitized.strip()


class SynthesisResponseAPI(BaseModel):
    """API response for TTS synthesis."""
    audio_base64: str = Field(..., description="Generated audio in base64")
    text: str = Field(..., description="Input text")
    provider_id: str = Field(..., description="Provider used")
    voice_id: Optional[str] = Field(None, description="Voice ID used")
    duration: float = Field(..., description="Audio duration in seconds")
    processing_time: float = Field(..., description="Processing time in seconds")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    format: str = Field("wav", description="Audio format")


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    text: str
    provider_id: str
    voice_cloning: bool = False


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost: float
    character_count: int
    provider_id: str


# ============================================================================
# TTS Synthesis Endpoints
# ============================================================================

@router.post("/synthesize", response_model=SynthesisResponseAPI)
async def synthesize(
    req_body: SynthesisRequestAPI,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("synthesize", "free"))
):
    """
    Synthesize speech with automatic billing.

    Automatically deducts cost from user wallet.

    Args:
        req_body: Synthesis request with provider, text, and parameters
        request: FastAPI request object (for rate limiting)
        user: Current authenticated user

    Returns:
        SynthesisResponseAPI: Generated audio with cost and transaction info
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Create internal synthesis request
        synthesis_request = SynthesisRequest(
            provider_id=req_body.provider_id,
            text=req_body.text,
            language=req_body.language,
            voice_id=req_body.voice_id,
            speed=req_body.speed,
            pitch=req_body.pitch,
            remove_silence=req_body.remove_silence,
            output_format=req_body.output_format
        )

        # Call service (with billing)
        # Note: MongoDB JWT uses 'sub' for user_id, not 'id'
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        result = await tts_service.synthesize(
            user_id=user_id,
            request=synthesis_request,
            skip_billing=False
        )

        logger.info(
            f"TTS synthesis completed: user={user_id}, provider={req_body.provider_id}, "
            f"chars={len(req_body.text)}, duration={result.duration:.2f}s, cost=${result.cost:.4f}"
        )

        # Save to history (non-blocking - don't fail synthesis if history fails)
        try:
            history_service = await get_audio_history_service()
            await history_service.add_to_history(
                user_id=user_id,
                text=req_body.text,
                provider_id=result.provider_id,
                audio_base64=result.audio_base64,
                duration_seconds=result.duration,
                cost=result.cost,
                voice_id=result.voice_id,
                language=req_body.language
            )
        except Exception as e:
            logger.error(f"Failed to save to history (non-critical): {e}")

        return SynthesisResponseAPI(
            audio_base64=result.audio_base64,
            text=result.text,
            provider_id=result.provider_id,
            voice_id=result.voice_id,
            duration=result.duration,
            processing_time=result.processing_time,
            cost=result.cost,
            transaction_id=result.transaction_id,
            format=result.format
        )

    except TTSError as e:
        # Custom TTS errors with user-friendly messages
        logger.warning(f"TTS synthesis error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"TTS synthesis validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Map generic exceptions to specific TTS errors
        logger.error(f"TTS synthesis unexpected error: {e}")
        tts_error = map_exception_to_tts_error(e)
        raise HTTPException(status_code=tts_error.status_code, detail=tts_error.message)


@router.post("/preview", response_model=SynthesisResponseAPI)
async def tts_preview(
    req_body: SynthesisRequestAPI,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("synthesize", "free"))
):
    """
    Preview TTS synthesis without billing.

    This endpoint is for voice preview in settings modals. It:
    - Skips wallet billing entirely
    - Limits text to 100 characters
    - Returns JSON with audio_base64 (same format as /synthesize)

    Args:
        req_body: Synthesis request with provider, text, and parameters
        request: FastAPI request object (for rate limiting)
        user: Current authenticated user

    Returns:
        SynthesisResponseAPI: Generated audio with metadata (no cost/transaction)
    """
    try:
        # Enforce preview text limit
        if len(req_body.text) > 100:
            raise HTTPException(
                status_code=400,
                detail="Preview text limited to 100 characters"
            )

        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Create internal synthesis request
        synthesis_request = SynthesisRequest(
            provider_id=req_body.provider_id,
            text=req_body.text,
            language=req_body.language,
            voice_id=req_body.voice_id,
            speed=req_body.speed,
            pitch=req_body.pitch,
            remove_silence=req_body.remove_silence,
            output_format=req_body.output_format
        )

        # Call service WITHOUT billing
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        result = await tts_service.synthesize(
            user_id=user_id,
            request=synthesis_request,
            skip_billing=True  # No billing for preview
        )

        logger.info(
            f"TTS preview completed: user={user_id}, provider={req_body.provider_id}, "
            f"chars={len(req_body.text)}, duration={result.duration:.2f}s (no charge)"
        )

        # Return same format as /synthesize but with zero cost
        return SynthesisResponseAPI(
            audio_base64=result.audio_base64,
            text=result.text,
            provider_id=result.provider_id,
            voice_id=result.voice_id,
            duration=result.duration,
            processing_time=result.processing_time,
            cost=0.0,  # No cost for preview
            transaction_id=None,  # No transaction
            format=result.format
        )

    except TTSError as e:
        logger.warning(f"TTS preview error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"TTS preview validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TTS preview unexpected error: {e}")
        tts_error = map_exception_to_tts_error(e)
        raise HTTPException(status_code=tts_error.status_code, detail=tts_error.message)


@router.post("/synthesize/upload", response_model=SynthesisResponseAPI)
async def synthesize_with_voice_cloning_upload(
    request: Request,
    audio_file: UploadFile = File(..., description="Reference audio file"),
    provider_id: str = Form(..., description="TTS provider ID"),
    text: str = Form(..., description="Text to synthesize"),
    language: str = Form("en", description="Language code"),
    speed: float = Form(1.0, description="Speech speed"),
    remove_silence: bool = Form(False, description="Remove silence"),
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("clone", "free"))
):
    """
    Synthesize speech with voice cloning (multipart form upload).

    Automatically deducts cost from user wallet.

    Args:
        audio_file: Reference audio file for cloning
        provider_id: TTS provider ID
        text: Text to synthesize
        language: Language code
        speed: Speech speed
        remove_silence: Remove silence flag
        user: Current authenticated user

    Returns:
        SynthesisResponseAPI: Generated audio with cost and transaction info
    """
    try:
        # Read reference audio file
        audio_bytes = await audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Extract user_id (MongoDB JWT uses 'sub', not 'id')
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        # Create voice clone request
        clone_request = VoiceCloneRequest(
            provider_id=provider_id,
            text=text,
            reference_audio_base64=audio_base64,
            language=language,
            speed=speed,
            remove_silence=remove_silence
        )

        # Call service (with billing)
        result = await tts_service.synthesize_with_voice_cloning(
            user_id=user_id,
            request=clone_request,
            skip_billing=False
        )

        logger.info(
            f"Voice cloning completed: user={user_id}, provider={provider_id}, "
            f"filename={audio_file.filename}, duration={result.duration:.2f}s, cost=${result.cost:.4f}"
        )

        # Save to history (non-blocking - don't fail synthesis if history fails)
        try:
            history_service = await get_audio_history_service()
            await history_service.add_to_history(
                user_id=user_id,
                text=text,
                provider_id=result.provider_id,
                audio_base64=result.audio_base64,
                duration_seconds=result.duration,
                cost=result.cost,
                voice_id=result.voice_id,
                language=language
            )
        except Exception as e:
            logger.error(f"Failed to save to history (non-critical): {e}")

        return SynthesisResponseAPI(
            audio_base64=result.audio_base64,
            text=result.text,
            provider_id=result.provider_id,
            voice_id=result.voice_id,
            duration=result.duration,
            processing_time=result.processing_time,
            cost=result.cost,
            transaction_id=result.transaction_id,
            format=result.format
        )

    except TTSError as e:
        # Custom TTS errors with user-friendly messages
        logger.warning(f"Voice cloning error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"Voice cloning validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Map generic exceptions to specific TTS errors
        logger.error(f"Voice cloning unexpected error: {e}")
        tts_error = map_exception_to_tts_error(e)
        raise HTTPException(status_code=tts_error.status_code, detail=tts_error.message)


@router.post("/clone", response_model=SynthesisResponseAPI)
async def voice_clone(
    req_body: VoiceCloneRequestAPI,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("clone", "free"))
):
    """
    Synthesize speech with voice cloning (base64 audio).

    Automatically deducts cost from user wallet.

    Args:
        req_body: Voice cloning request with base64 reference audio
        request: FastAPI request object (for rate limiting)
        user: Current authenticated user

    Returns:
        SynthesisResponseAPI: Generated audio with cost and transaction info
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Extract user_id (MongoDB JWT uses 'sub', not 'id')
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        # Create voice clone request
        clone_request = VoiceCloneRequest(
            provider_id=req_body.provider_id,
            text=req_body.text,
            reference_audio_base64=req_body.reference_audio_base64,
            language=req_body.language,
            speed=req_body.speed,
            remove_silence=req_body.remove_silence
        )

        # Call service (with billing)
        result = await tts_service.synthesize_with_voice_cloning(
            user_id=user_id,
            request=clone_request,
            skip_billing=False
        )

        logger.info(
            f"Voice cloning (base64) completed: user={user_id}, provider={req_body.provider_id}, "
            f"duration={result.duration:.2f}s, cost=${result.cost:.4f}"
        )

        # Save to history (non-blocking - don't fail synthesis if history fails)
        try:
            history_service = await get_audio_history_service()
            await history_service.add_to_history(
                user_id=user_id,
                text=req_body.text,
                provider_id=result.provider_id,
                audio_base64=result.audio_base64,
                duration_seconds=result.duration,
                cost=result.cost,
                voice_id=result.voice_id,
                language=req_body.language
            )
        except Exception as e:
            logger.error(f"Failed to save to history (non-critical): {e}")

        return SynthesisResponseAPI(
            audio_base64=result.audio_base64,
            text=result.text,
            provider_id=result.provider_id,
            voice_id=result.voice_id,
            duration=result.duration,
            processing_time=result.processing_time,
            cost=result.cost,
            transaction_id=result.transaction_id,
            format=result.format
        )

    except TTSError as e:
        # Custom TTS errors with user-friendly messages
        logger.warning(f"Voice cloning error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"Voice cloning validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Map generic exceptions to specific TTS errors
        logger.error(f"Voice cloning unexpected error: {e}")
        tts_error = map_exception_to_tts_error(e)
        raise HTTPException(status_code=tts_error.status_code, detail=tts_error.message)


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(
    req_body: CostEstimateRequest,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("estimate", "free"))
):
    """
    Estimate cost of TTS synthesis before running.

    Args:
        req_body: Cost estimation request
        request: FastAPI request object (for rate limiting)
        user: Current authenticated user

    Returns:
        CostEstimateResponse: Estimated cost and character count
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Get cost estimate
        estimate = await tts_service.estimate_cost(
            text=req_body.text,
            provider_id=req_body.provider_id,
            voice_cloning=req_body.voice_cloning
        )

        return CostEstimateResponse(
            estimated_cost=estimate.total_cost,
            character_count=estimate.character_count,
            provider_id=req_body.provider_id
        )

    except TTSError as e:
        # Custom TTS errors with user-friendly messages
        logger.warning(f"Cost estimation error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        logger.error(f"Cost estimation validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Map generic exceptions to specific TTS errors
        logger.error(f"Cost estimation unexpected error: {e}")
        tts_error = map_exception_to_tts_error(e)
        raise HTTPException(status_code=tts_error.status_code, detail=tts_error.message)


# ============================================================================
# Voice Samples & Provider Management
# ============================================================================

@router.get("/voices")
async def list_voices(
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    List all available Ghanaian voice samples.

    Returns:
        dict: List of available voice samples with metadata
    """
    try:
        voices = []
        for filename, metadata in GHANAIAN_VOICES.items():
            voice_path = VOICE_FILES_DIR / filename
            if voice_path.exists():
                voices.append({
                    **metadata,
                    "file": filename,
                    "available": True,
                })
            else:
                logger.warning(f"Voice file not found: {filename}")
                voices.append({
                    **metadata,
                    "file": filename,
                    "available": False,
                })

        return {"voices": voices, "count": len(voices)}

    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@router.get("/voices/{filename}")
async def get_voice_file(
    filename: str,
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Serve a Ghanaian voice sample file.

    Args:
        filename: Name of the voice file (e.g., 'nana_aba.wav')

    Returns:
        FileResponse: Audio file
    """
    try:
        # Validate filename is in allowed list
        if filename not in GHANAIAN_VOICES:
            raise HTTPException(
                status_code=404,
                detail=f"Voice file '{filename}' not found in available voices"
            )

        # Construct file path
        voice_path = VOICE_FILES_DIR / filename

        # Check if file exists
        if not voice_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Voice file '{filename}' exists in metadata but file not found on disk"
            )

        # Serve file
        logger.info(f"Serving voice file: {filename}")
        return FileResponse(
            path=str(voice_path),
            media_type="audio/wav",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                "X-Voice-ID": GHANAIAN_VOICES[filename]["id"],
                "X-Voice-Name": GHANAIAN_VOICES[filename]["name"],
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving voice file {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve voice file: {str(e)}"
        )


@router.get("/voices/{voice_id}/preview")
async def get_voice_preview(
    voice_id: str,
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Serve a 5-second preview sample of a Ghanaian voice.

    Args:
        voice_id: Voice ID (e.g., 'nana_aba', 'adom_okyere')

    Returns:
        FileResponse: 5-second audio preview
    """
    try:
        # Map voice_id to preview filename
        preview_filename = f"{voice_id}_preview.wav"
        preview_path = Path("/opt/kasaai/apps/voice-lab/previews") / preview_filename

        # Check if preview file exists
        if not preview_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Preview for voice '{voice_id}' not found"
            )

        # Get voice metadata if available
        voice_name = voice_id.replace("_", " ").title()
        for filename, metadata in GHANAIAN_VOICES.items():
            if metadata["id"] == voice_id:
                voice_name = metadata["name"]
                break

        # Serve preview file
        logger.info(f"Serving voice preview: {voice_id}")
        return FileResponse(
            path=str(preview_path),
            media_type="audio/wav",
            filename=preview_filename,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                "X-Voice-ID": voice_id,
                "X-Voice-Name": voice_name,
                "X-Preview-Duration": "5",  # seconds
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving voice preview {voice_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve voice preview: {str(e)}"
        )


@router.get("/providers")
async def list_providers(
    request: Request,
    force_refresh: bool = Query(False, description="Force health check refresh"),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    List all available TTS providers with real-time status.

    Args:
        force_refresh: Force health check even if cached (default: False)

    Returns:
        dict: TTS providers with dynamic status and capabilities
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Get all providers with dynamic health status
        providers_dict = await tts_service.get_available_providers(force_refresh=force_refresh)

        # Calculate counts
        online_count = sum(1 for p in providers_dict.values() if p["status"] == "online")
        offline_count = sum(1 for p in providers_dict.values() if p["status"] == "offline")

        return {
            "providers": providers_dict,
            "count": len(providers_dict),
            "online_count": online_count,
            "offline_count": offline_count,
        }

    except Exception as e:
        logger.error(f"Error listing providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get status of a specific TTS provider.

    Args:
        provider_id: Provider identifier (e.g., 'coqui_xtts', 'melotts')

    Returns:
        dict: Provider details with current status
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        provider = await tts_service.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_id}' not found"
            )

        return provider

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider: {str(e)}")


@router.get("/health/status")
async def get_all_health_status(
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get real-time health status for all TTS providers.

    Returns:
        dict: Health status for all providers with metrics
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Force refresh to get latest status
        providers_dict = await tts_service.get_available_providers(force_refresh=True)

        # Extract health info
        health_status = {}
        for provider_id, provider in providers_dict.items():
            health_status[provider_id] = {
                "status": provider.get("status", "unknown"),
                "lastChecked": provider.get("lastChecked"),
                "responseTime": provider.get("responseTime"),
                "error": provider.get("error"),
                "name": provider.get("name")
            }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "providers": health_status,
            "summary": {
                "online": sum(1 for p in health_status.values() if p["status"] == "online"),
                "offline": sum(1 for p in health_status.values() if p["status"] == "offline"),
                "degraded": sum(1 for p in health_status.values() if p["status"] == "degraded"),
                "building": sum(1 for p in health_status.values() if p["status"] == "building"),
            }
        }
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")


@router.get("/health/metrics")
async def get_health_metrics(
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get aggregated health metrics for all TTS providers.

    Returns:
        dict: Aggregated metrics including uptime, average response times, etc.
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Get all providers
        providers_dict = await tts_service.get_available_providers(force_refresh=False)

        # Calculate metrics
        response_times = []
        providers_by_status = {
            "online": [],
            "offline": [],
            "degraded": [],
            "building": []
        }

        for provider_id, provider in providers_dict.items():
            status = provider.get("status", "unknown")
            if status in providers_by_status:
                providers_by_status[status].append(provider.get("name", provider_id))

            if provider.get("responseTime"):
                response_times.append(provider["responseTime"])

        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_providers": len(providers_dict),
                "online_count": len(providers_by_status["online"]),
                "offline_count": len(providers_by_status["offline"]),
                "degraded_count": len(providers_by_status["degraded"]),
                "building_count": len(providers_by_status["building"]),
                "availability_percentage": (len(providers_by_status["online"]) / len(providers_dict) * 100) if providers_dict else 0,
                "average_response_time_ms": avg_response_time,
                "min_response_time_ms": min(response_times) if response_times else None,
                "max_response_time_ms": max(response_times) if response_times else None,
            },
            "providers_by_status": providers_by_status
        }
    except Exception as e:
        logger.error(f"Error getting health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health metrics: {str(e)}")


@router.get("/health/{provider_id}")
async def get_provider_health(
    provider_id: str,
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get real-time health status for a specific TTS provider.

    Args:
        provider_id: Provider identifier

    Returns:
        dict: Health status and metrics for the provider
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Get provider with fresh status
        providers_dict = await tts_service.get_available_providers(force_refresh=True)

        if provider_id not in providers_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_id}' not found"
            )

        provider = providers_dict[provider_id]

        return {
            "provider_id": provider_id,
            "name": provider.get("name"),
            "status": provider.get("status", "unknown"),
            "lastChecked": provider.get("lastChecked"),
            "responseTime": provider.get("responseTime"),
            "endpoint": provider.get("endpoint"),
            "error": provider.get("error"),
            "capabilities": provider.get("capabilities", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider health: {str(e)}")


@router.post("/health/test-notification")
async def test_health_notification(
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Send a test notification to verify email alerts are working.

    Returns:
        dict: Success status
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        if not tts_service.health_notifier:
            raise HTTPException(
                status_code=400,
                detail="Email notifications are not enabled"
            )

        # Send test notification
        await tts_service.health_notifier.send_test_notification()

        return {
            "success": True,
            "message": f"Test notification sent to {tts_service.health_notifier.admin_email}",
            "admin_email": tts_service.health_notifier.admin_email,
            "smtp_host": tts_service.health_notifier.smtp_host,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")


@router.get("/providers/{provider_id}/languages")
async def get_provider_languages(
    provider_id: str,
    request: Request,
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get available languages for a specific TTS provider.

    This endpoint proxies the request to avoid CORS issues.

    Args:
        provider_id: Provider identifier (e.g., 'coqui_xtts', 'melotts')

    Returns:
        dict: List of available languages
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        provider = await tts_service.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_id}' not found"
            )

        # Return language list from provider metadata
        return {
            "languages": provider.get("languageList", []),
            "count": len(provider.get("languageList", []))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting languages for provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")


@router.get("/providers/{provider_id}/speakers")
async def get_provider_speakers(
    provider_id: str,
    request: Request,
    language: Optional[str] = Query(None),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get available speakers/voices for a specific TTS provider.

    This endpoint proxies the request to avoid CORS issues.

    Args:
        provider_id: Provider identifier (e.g., 'melotts', 'akan_mms')
        language: Optional language filter

    Returns:
        dict: List of available speakers
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        provider = await tts_service.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider_id}' not found"
            )

        # For providers that support multi-speaker, try to fetch from provider
        if provider.get("capabilities", {}).get("multiSpeaker"):
            import httpx

            try:
                endpoint = provider.get("endpoint", "")
                url = f"{endpoint}/speakers"
                if language:
                    url += f"/{language}"

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        speakers = data.get("speakers", [])
                        return {"speakers": speakers, "count": len(speakers)}
            except Exception as e:
                logger.warning(f"Failed to fetch speakers from provider {provider_id}: {e}")

        # Return empty list if provider doesn't support multi-speaker
        return {"speakers": [], "count": 0}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting speakers for provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get speakers: {str(e)}")


# ============================================================================
# Audio History Endpoints
# ============================================================================

@router.get("/history", response_model=AudioHistoryListResponse)
async def get_audio_history(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search text"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
):
    """
    Get user's TTS synthesis history with pagination and filters.

    Args:
        page: Page number (1-indexed)
        limit: Items per page (1-100)
        search: Optional text search query
        provider: Optional provider filter
        user: Current authenticated user

    Returns:
        AudioHistoryListResponse: Paginated history items
    """
    try:
        # Extract user_id (MongoDB JWT uses 'sub', not 'id')
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        history_service = await get_audio_history_service()

        result = await history_service.get_user_history(
            user_id=user_id,
            page=page,
            limit=limit,
            search_text=search,
            provider_filter=provider
        )

        logger.info(
            f"Retrieved history for user={user_id}: page={page}, "
            f"total={result.total}, returned={len(result.items)}"
        )

        return result

    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/history/{item_id}")
async def get_history_item(
    item_id: str,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Get a specific history item with full audio data.

    Args:
        item_id: History item ID
        user: Current authenticated user

    Returns:
        dict: History item with full audio data
    """
    try:
        # Extract user_id (MongoDB JWT uses 'sub', not 'id')
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        history_service = await get_audio_history_service()

        item = await history_service.get_history_item(
            user_id=user_id,
            item_id=item_id
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"History item '{item_id}' not found"
            )

        logger.info(f"Retrieved history item {item_id} for user={user_id}")
        return item

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history item {item_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history item: {str(e)}"
        )


@router.delete("/history/{item_id}")
async def delete_history_item(
    item_id: str,
    request: Request,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_tts_rate_limit("info", "free"))
) -> Dict:
    """
    Soft delete a history item.

    Args:
        item_id: History item ID
        user: Current authenticated user

    Returns:
        dict: Success message
    """
    try:
        # Extract user_id (MongoDB JWT uses 'sub', not 'id')
        user_id = user.get("id") or user.get("sub") or user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        history_service = await get_audio_history_service()

        success = await history_service.delete_history_item(
            user_id=user_id,
            item_id=item_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"History item '{item_id}' not found or already deleted"
            )

        logger.info(f"Deleted history item {item_id} for user={user_id}")
        return {
            "success": True,
            "message": "History item deleted successfully",
            "item_id": item_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting history item {item_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete history item: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check for TTS services route.

    Returns:
        dict: Health status
    """
    try:
        # Get TTS service
        tts_service: TTSProviderService = await get_tts_service()

        # Get provider count
        providers = await tts_service.get_available_providers()

        return {
            "status": "healthy",
            "service": "tts-services",
            "providers_count": len(providers),
            "voices_available": len(GHANAIAN_VOICES),
            "voices_directory": str(VOICE_FILES_DIR),
            "billing_enabled": tts_service.enable_billing,
            "health_monitoring_enabled": tts_service.enable_health_monitoring,
        }

    except Exception as e:
        logger.error(f"TTS health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "tts-services",
            "error": str(e)
        }

"""
ASR Services Routes

Provides API endpoints for ASR Lab interface with automatic billing and health monitoring.

Enhanced with:
- Rate limiting (tier-based)
- Custom error handling
- Audio validation (duration, format, security)
- Comprehensive error messages

Updated: 2025-10-27 (Phase 1: Error Handling & Security)
"""

from fastapi import APIRouter, HTTPException, Query, Depends, File, UploadFile, Form, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
import base64

from apps.shared.services.asr_provider_service import (
    get_asr_service,
    ASRProviderService,
    TranscriptionRequest,
)
from apps.shared.services.audio_validation_service import (
    get_audio_validation_service,
    AudioValidationError,
    SUPPORTED_FORMATS,
)
from ..services.transcription_history_service import (
    get_transcription_history_service,
    TranscriptionHistoryListResponse,
)
from ..auth import get_current_user_mongo
from ..middleware.rate_limiting import get_asr_rate_limit
from ..exceptions.asr_errors import (
    ASRError,
    InsufficientBalanceError,
    ProviderOfflineError,
    AudioTooLongError,
    AudioTooLargeError,
    InvalidProviderError,
    InvalidLanguageError,
    AudioProcessingError,
    InvalidAudioFormatError,
    MaliciousFileError,
    map_exception_to_asr_error,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["ASR Services"])


# ============================================================================
# Pydantic Models
# ============================================================================

class TranscriptionRequestAPI(BaseModel):
    """Transcription request from API (base64 audio)."""
    provider_id: str = Field(..., description="ASR provider ID")
    audio_base64: str = Field(..., description="Base64-encoded audio file")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'tw', 'auto')")
    task: str = Field("transcribe", description="Task type: 'transcribe' or 'translate'")
    response_format: str = Field("json", description="Response format: 'json', 'text', 'srt', 'vtt'")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Sampling temperature")
    timestamp_granularities: Optional[List[str]] = Field(None, description="Timestamp levels: ['word', 'segment']")


class TranscriptionResponseAPI(BaseModel):
    """Transcription response from API."""
    text: str = Field(..., description="Transcribed text")
    provider_id: str = Field(..., description="Provider used")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    cost: float = Field(..., description="Cost in USD")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_name: Optional[str] = Field(None, description="Model name used")


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    provider_id: str
    audio_base64: str


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost: float
    estimated_duration: float
    provider_id: str


# ============================================================================
# API Routes
# ============================================================================

@router.post("/transcribe", response_model=TranscriptionResponseAPI)
async def transcribe(
    req_body: TranscriptionRequestAPI,
    request: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free"))
):
    """
    Transcribe audio with ASR model.

    Automatically deducts cost from user wallet.

    Enhanced with:
    - Rate limiting (10 requests/min for free tier)
    - Audio validation (duration, format, security)
    - Custom error messages

    Args:
        req_body: Transcription request with provider, audio, and parameters
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        TranscriptionResponseAPI: Transcription with cost and transaction info
    """
    try:
        # Get audio validation service
        validation_service = get_audio_validation_service()

        # Validate audio file (base64 → bytes + validation)
        audio_data, audio_info = validation_service.validate_audio_base64(
            audio_base64=req_body.audio_base64,
            tier="free",  # TODO: Get user's actual tier from user dict
            detect_format=True,
            check_security=True,
        )

        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Create internal transcription request
        transcription_request = TranscriptionRequest(
            provider_id=req_body.provider_id,
            audio_base64=req_body.audio_base64,
            language=req_body.language,
            task=req_body.task,
            response_format=req_body.response_format,
            temperature=req_body.temperature,
            timestamp_granularities=req_body.timestamp_granularities
        )

        # Call service (with billing)
        result = await asr_service.transcribe(
            user_id=user["id"],
            request=transcription_request,
            skip_billing=False
        )

        logger.info(
            f"ASR transcription completed: user={user['id']}, provider={req_body.provider_id}, "
            f"duration={result.duration:.2f}s, cost=${result.cost:.4f}, "
            f"format={audio_info['format']}, size={audio_info['size_mb']:.2f}MB"
        )

        # Save to history (non-blocking - don't fail transcription if history fails)
        try:
            history_service = await get_transcription_history_service()
            await history_service.add_to_history(
                user_id=user["id"],
                provider_id=result.provider_id,
                transcript=result.text,
                duration_seconds=result.duration,
                cost=result.cost,
                audio_base64=req_body.audio_base64,  # Store for replay
                language=result.language,
                model_name=result.model_name,
                task=req_body.task,
                processing_time=result.processing_time,
                metadata={
                    "format": audio_info["format"],
                    "size_mb": audio_info["size_mb"],
                    "temperature": req_body.temperature,
                    "response_format": req_body.response_format
                }
            )
        except Exception as e:
            logger.error(f"Failed to save to transcription history (non-critical): {e}")

        return TranscriptionResponseAPI(
            text=result.text,
            provider_id=result.provider_id,
            language=result.language,
            duration=result.duration,
            cost=result.cost,
            transaction_id=result.transaction_id,
            processing_time=result.processing_time,
            model_name=result.model_name
        )

    except AudioValidationError as e:
        # Convert shared audio validation errors to ASR errors
        if isinstance(e, validation_service.AudioTooLongError):
            asr_error = AudioTooLongError(e.duration, e.max_duration, e.tier)
        elif isinstance(e, validation_service.AudioTooLargeError):
            asr_error = AudioTooLargeError(e.size_mb, e.max_size_mb)
        elif isinstance(e, validation_service.InvalidAudioFormatError):
            asr_error = InvalidAudioFormatError(e.format, e.supported_formats)
        elif isinstance(e, validation_service.MaliciousFileError):
            asr_error = MaliciousFileError(str(e))
        else:
            asr_error = AudioProcessingError(str(e))

        logger.warning(f"Audio validation error: {asr_error.message}")
        raise HTTPException(status_code=asr_error.status_code, detail=asr_error.message)

    except ASRError as e:
        # Custom ASR errors with user-friendly messages
        logger.warning(f"ASR transcription error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except ValueError as e:
        logger.error(f"ASR transcription validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Map generic exceptions to specific ASR errors
        logger.error(f"ASR transcription unexpected error: {e}")
        asr_error = map_exception_to_asr_error(e, req_body.provider_id)
        raise HTTPException(status_code=asr_error.status_code, detail=asr_error.message)


@router.post("/transcribe/upload", response_model=TranscriptionResponseAPI)
async def transcribe_upload(
    request: Request,
    response: Response,
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    provider_id: str = Form(..., description="ASR provider ID"),
    language: Optional[str] = Form(None, description="Language code"),
    task: str = Form("transcribe", description="Task type: 'transcribe' or 'translate'"),
    response_format: str = Form("json", description="Response format"),
    temperature: float = Form(0.0, description="Sampling temperature"),
    skip_billing: bool = Query(False, description="Skip billing (for testing/preview)"),
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free"))
):
    """
    Transcribe audio file (multipart form upload).

    Automatically deducts cost from user wallet.

    Enhanced with:
    - Rate limiting (10 uploads/min for free tier)
    - Audio validation (duration, format, security)
    - Custom error messages

    Args:
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        audio_file: Audio file upload
        provider_id: ASR provider ID
        language: Optional language code
        task: Task type ('transcribe' or 'translate')
        response_format: Response format ('json', 'text', 'srt', 'vtt')
        temperature: Sampling temperature
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        TranscriptionResponseAPI: Transcription with cost and transaction info
    """
    try:
        # Read audio file
        audio_bytes = await audio_file.read()

        # Get audio validation service
        validation_service = get_audio_validation_service()

        # Validate audio file
        audio_info = validation_service.validate_audio_file(
            audio_data=audio_bytes,
            tier="free",  # TODO: Get user's actual tier from user dict
            detect_format=True,
            check_security=True,
        )

        # Encode to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Create internal transcription request
        transcription_request = TranscriptionRequest(
            provider_id=provider_id,
            audio_base64=audio_base64,
            language=language,
            task=task,
            response_format=response_format,
            temperature=temperature
        )

        # Call service (with optional billing skip for testing/preview)
        result = await asr_service.transcribe(
            user_id=user["id"],
            request=transcription_request,
            skip_billing=skip_billing
        )

        logger.info(
            f"ASR file transcription completed: user={user['id']}, provider={provider_id}, "
            f"filename={audio_file.filename}, duration={result.duration:.2f}s, cost=${result.cost:.4f}, "
            f"format={audio_info['format']}, size={audio_info['size_mb']:.2f}MB, skip_billing={skip_billing}"
        )

        # Save to history (non-blocking - don't fail transcription if history fails)
        try:
            history_service = await get_transcription_history_service()
            await history_service.add_to_history(
                user_id=user["id"],
                provider_id=result.provider_id,
                transcript=result.text,
                duration_seconds=result.duration,
                cost=result.cost,
                audio_filename=audio_file.filename,
                audio_base64=audio_base64,  # Store for replay
                language=result.language,
                model_name=result.model_name,
                task=task,
                processing_time=result.processing_time,
                metadata={
                    "format": audio_info["format"],
                    "size_mb": audio_info["size_mb"],
                    "temperature": temperature,
                    "response_format": response_format
                }
            )
        except Exception as e:
            logger.error(f"Failed to save to transcription history (non-critical): {e}")

        return TranscriptionResponseAPI(
            text=result.text,
            provider_id=result.provider_id,
            language=result.language,
            duration=result.duration,
            cost=result.cost,
            transaction_id=result.transaction_id,
            processing_time=result.processing_time,
            model_name=result.model_name
        )

    except AudioValidationError as e:
        # Convert shared audio validation errors to ASR errors
        if "too long" in str(e).lower():
            asr_error = AudioTooLongError(duration=0, max_duration=300, tier="free")
        elif "too large" in str(e).lower():
            asr_error = AudioTooLargeError(size_mb=0, max_size_mb=100)
        elif "format" in str(e).lower():
            asr_error = InvalidAudioFormatError(format="unknown", supported_formats=SUPPORTED_FORMATS)
        elif "malicious" in str(e).lower():
            asr_error = MaliciousFileError(str(e))
        else:
            asr_error = AudioProcessingError(str(e))

        logger.warning(f"Audio validation error: {asr_error.message}")
        raise HTTPException(status_code=asr_error.status_code, detail=asr_error.message)

    except ASRError as e:
        # Custom ASR errors with user-friendly messages
        logger.warning(f"ASR file transcription error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except ValueError as e:
        logger.error(f"ASR file transcription validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Map generic exceptions to specific ASR errors
        logger.error(f"ASR file transcription unexpected error: {e}")
        asr_error = map_exception_to_asr_error(e, provider_id)
        raise HTTPException(status_code=asr_error.status_code, detail=asr_error.message)


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(
    req_body: CostEstimateRequest,
    request: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("estimate", "free"))
):
    """
    Estimate cost of ASR transcription before running.

    Enhanced with rate limiting (30 requests/min for free tier).

    Args:
        req_body: Cost estimation request
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        CostEstimateResponse: Estimated cost and duration
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Estimate cost
        estimated_cost = await asr_service.estimate_cost(
            provider_id=req_body.provider_id,
            audio_base64=req_body.audio_base64
        )

        # Estimate duration (from base64 size)
        audio_bytes = base64.b64decode(req_body.audio_base64)
        audio_size_kb = len(audio_bytes) / 1024
        estimated_duration = audio_size_kb / 32  # Assuming 16kHz mono 16-bit

        return CostEstimateResponse(
            estimated_cost=estimated_cost,
            estimated_duration=estimated_duration,
            provider_id=req_body.provider_id
        )

    except ASRError as e:
        logger.warning(f"Cost estimation error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        logger.error(f"Cost estimation unexpected error: {e}")
        asr_error = map_exception_to_asr_error(e, req_body.provider_id)
        raise HTTPException(status_code=asr_error.status_code, detail=asr_error.message)


@router.get("/providers")
async def list_providers(
    request: Request,
    response: Response,
    force_refresh: bool = Query(False, description="Force health check refresh"),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    List all available ASR providers with real-time status.

    Args:
        force_refresh: Force health check even if cached (default: False)

    Returns:
        dict: ASR providers with dynamic status and capabilities
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Get all provider health statuses
        providers_health = await asr_service.get_all_providers_health(force_refresh=force_refresh)

        # Convert to dict format
        providers_dict = {}
        for health in providers_health:
            providers_dict[health.provider_id] = {
                "id": health.provider_id,
                "name": health.provider_id.replace("_", " ").title(),
                "endpoint": health.endpoint,
                "status": health.status,
                "last_check": health.last_check.isoformat(),
                "response_time_ms": health.response_time_ms,
                "error_message": health.error_message,
                "provider_type": "asr"
            }

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
        logger.error(f"Error listing ASR providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: str,
    request: Request,
    response: Response,
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get status of a specific ASR provider.

    Args:
        provider_id: Provider identifier (e.g., 'whisper_large_v3', 'akan_whisper_giftmark')

    Returns:
        dict: Provider details with current status
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Get provider health
        health = await asr_service.get_provider_health(provider_id)

        return {
            "id": health.provider_id,
            "name": health.provider_id.replace("_", " ").title(),
            "endpoint": health.endpoint,
            "status": health.status,
            "last_check": health.last_check.isoformat(),
            "response_time_ms": health.response_time_ms,
            "error_message": health.error_message,
            "provider_type": "asr"
        }

    except Exception as e:
        logger.error(f"Error getting ASR provider {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider: {str(e)}")


@router.get("/languages/{provider_id}")
async def get_supported_languages(
    provider_id: str,
    request: Request,
    response: Response,
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get supported languages for a specific ASR provider.

    Args:
        provider_id: Provider identifier

    Returns:
        dict: List of supported language codes
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Get supported languages
        languages = await asr_service.get_available_languages(provider_id)

        return {
            "provider_id": provider_id,
            "languages": languages,
            "count": len(languages)
        }

    except Exception as e:
        logger.error(f"Error getting languages for {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")


# ============================================================================
# Phase 4: Enhanced Provider Metadata Endpoints
# ============================================================================

# Language metadata with native names, WER scores, and cost info
LANGUAGE_METADATA = {
    "en": {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "region": "Global",
        "family": "Germanic"
    },
    "tw": {
        "code": "tw",
        "name": "Twi (Akan)",
        "native_name": "Twi",
        "region": "Ghana",
        "family": "Kwa"
    },
    "ak": {
        "code": "ak",
        "name": "Akan",
        "native_name": "Akan",
        "region": "Ghana",
        "family": "Kwa"
    },
    "es": {
        "code": "es",
        "name": "Spanish",
        "native_name": "Español",
        "region": "Global",
        "family": "Romance"
    },
    "fr": {
        "code": "fr",
        "name": "French",
        "native_name": "Français",
        "region": "Global",
        "family": "Romance"
    },
    "de": {
        "code": "de",
        "name": "German",
        "native_name": "Deutsch",
        "region": "Europe",
        "family": "Germanic"
    },
    "ar": {
        "code": "ar",
        "name": "Arabic",
        "native_name": "العربية",
        "region": "Middle East/North Africa",
        "family": "Semitic"
    },
    "zh": {
        "code": "zh",
        "name": "Chinese",
        "native_name": "中文",
        "region": "Asia",
        "family": "Sino-Tibetan"
    },
    "ja": {
        "code": "ja",
        "name": "Japanese",
        "native_name": "日本語",
        "region": "Asia",
        "family": "Japonic"
    },
    "ko": {
        "code": "ko",
        "name": "Korean",
        "native_name": "한국어",
        "region": "Asia",
        "family": "Koreanic"
    },
    "pt": {
        "code": "pt",
        "name": "Portuguese",
        "native_name": "Português",
        "region": "Global",
        "family": "Romance"
    },
    "it": {
        "code": "it",
        "name": "Italian",
        "native_name": "Italiano",
        "region": "Europe",
        "family": "Romance"
    }
}

# Model variants available for each provider
PROVIDER_MODELS = {
    "whisper_large_v3": {
        "models": [
            {
                "id": "large-v3",
                "name": "Large v3",
                "description": "Most accurate Whisper model with 1.5B parameters",
                "parameters": "1.5B",
                "speed": "slow",
                "accuracy": "highest",
                "cost_multiplier": 1.0,
                "vram_required": "10GB",
                "recommended": True
            },
            {
                "id": "medium",
                "name": "Medium",
                "description": "Balanced accuracy and speed with 769M parameters",
                "parameters": "769M",
                "speed": "medium",
                "accuracy": "high",
                "cost_multiplier": 0.6,
                "vram_required": "5GB",
                "recommended": False
            },
            {
                "id": "small",
                "name": "Small",
                "description": "Faster inference with 244M parameters",
                "parameters": "244M",
                "speed": "fast",
                "accuracy": "good",
                "cost_multiplier": 0.3,
                "vram_required": "2GB",
                "recommended": False
            }
        ]
    },
    "akan_whisper_giftmark": {
        "models": [
            {
                "id": "akan-medium-finetuned",
                "name": "Akan Medium (Fine-tuned)",
                "description": "Whisper Medium fine-tuned on Akan/Twi data",
                "parameters": "769M",
                "speed": "medium",
                "accuracy": "highest_for_akan",
                "cost_multiplier": 1.0,
                "vram_required": "5GB",
                "recommended": True,
                "training_data": "Giftmark Akan dataset"
            }
        ]
    }
}

# Benchmark WER (Word Error Rate) data by provider and language
PROVIDER_BENCHMARKS = {
    "whisper_large_v3": {
        "provider_id": "whisper_large_v3",
        "provider_name": "Whisper Large v3",
        "overall_wer": 4.0,  # Average WER across all languages
        "test_conditions": {
            "sample_count": 1000,
            "audio_quality": "clean studio recordings",
            "test_date": "2025-10-01",
            "benchmark_dataset": "Common Voice + Librispeech"
        },
        "language_results": [
            {
                "language": "en",
                "wer": 2.8,
                "accuracy": 97.2,
                "sample_count": 500,
                "avg_latency_ms": 2500
            },
            {
                "language": "es",
                "wer": 4.2,
                "accuracy": 95.8,
                "sample_count": 100,
                "avg_latency_ms": 2600
            },
            {
                "language": "fr",
                "wer": 4.5,
                "accuracy": 95.5,
                "sample_count": 100,
                "avg_latency_ms": 2550
            },
            {
                "language": "de",
                "wer": 5.1,
                "accuracy": 94.9,
                "sample_count": 80,
                "avg_latency_ms": 2700
            },
            {
                "language": "ar",
                "wer": 6.8,
                "accuracy": 93.2,
                "sample_count": 60,
                "avg_latency_ms": 2800
            },
            {
                "language": "zh",
                "wer": 5.5,
                "accuracy": 94.5,
                "sample_count": 80,
                "avg_latency_ms": 2650
            },
            {
                "language": "ja",
                "wer": 6.2,
                "accuracy": 93.8,
                "sample_count": 50,
                "avg_latency_ms": 2750
            }
        ]
    },
    "akan_whisper_giftmark": {
        "provider_id": "akan_whisper_giftmark",
        "provider_name": "GiftMark Akan Whisper",
        "overall_wer": 7.1,  # Average WER for Akan/Twi
        "test_conditions": {
            "sample_count": 300,
            "audio_quality": "mixed (studio + field recordings)",
            "test_date": "2025-09-15",
            "benchmark_dataset": "GiftMark Akan Corpus"
        },
        "language_results": [
            {
                "language": "tw",
                "wer": 7.1,
                "accuracy": 92.9,
                "sample_count": 200,
                "avg_latency_ms": 1500,
                "dialect_breakdown": {
                    "asante": {"wer": 6.5, "accuracy": 93.5},
                    "akuapem": {"wer": 7.2, "accuracy": 92.8},
                    "fante": {"wer": 7.8, "accuracy": 92.2}
                }
            },
            {
                "language": "ak",
                "wer": 7.1,
                "accuracy": 92.9,
                "sample_count": 100,
                "avg_latency_ms": 1500
            }
        ]
    }
}


@router.get("/providers/{provider_id}/languages")
async def get_provider_languages_enhanced(
    provider_id: str,
    request: Request,
    response: Response,
    include_benchmarks: bool = Query(False, description="Include WER benchmarks"),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get detailed language metadata for a specific ASR provider.

    Enhanced version with language names, native names, WER scores, and cost info.

    Args:
        provider_id: Provider identifier
        include_benchmarks: Include WER benchmark data (default: False)

    Returns:
        dict: Detailed language metadata with optional benchmarks
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Get supported language codes
        language_codes = await asr_service.get_available_languages(provider_id)

        # Enrich with metadata
        languages_detailed = []
        for code in language_codes:
            lang_info = LANGUAGE_METADATA.get(code.lower(), {
                "code": code,
                "name": code.upper(),
                "native_name": code.upper(),
                "region": "Unknown",
                "family": "Unknown"
            })

            # Add benchmark data if requested
            if include_benchmarks and provider_id in PROVIDER_BENCHMARKS:
                benchmark_data = PROVIDER_BENCHMARKS[provider_id]
                lang_benchmark = next(
                    (lr for lr in benchmark_data["language_results"] if lr["language"] == code.lower()),
                    None
                )
                if lang_benchmark:
                    lang_info["benchmark"] = {
                        "wer": lang_benchmark["wer"],
                        "accuracy": lang_benchmark["accuracy"],
                        "avg_latency_ms": lang_benchmark["avg_latency_ms"],
                        "sample_count": lang_benchmark.get("sample_count", 0)
                    }
                    if "dialect_breakdown" in lang_benchmark:
                        lang_info["benchmark"]["dialect_breakdown"] = lang_benchmark["dialect_breakdown"]

            languages_detailed.append(lang_info)

        return {
            "provider_id": provider_id,
            "languages": languages_detailed,
            "count": len(languages_detailed),
            "benchmarks_included": include_benchmarks
        }

    except Exception as e:
        logger.error(f"Error getting enhanced languages for {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get language metadata: {str(e)}")


@router.get("/providers/{provider_id}/models")
async def get_provider_models(
    provider_id: str,
    request: Request,
    response: Response,
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get available model variants for a specific ASR provider.

    Returns model sizes, speed/accuracy trade-offs, and resource requirements.

    Args:
        provider_id: Provider identifier

    Returns:
        dict: Available models with metadata
    """
    try:
        # Check if provider exists
        asr_service: ASRProviderService = await get_asr_service()
        health = await asr_service.get_provider_health(provider_id)

        if health.status == 'offline':
            raise HTTPException(
                status_code=503,
                detail=f"Provider {provider_id} is currently offline"
            )

        # Get model information
        models_data = PROVIDER_MODELS.get(provider_id, {
            "models": [
                {
                    "id": "default",
                    "name": "Default Model",
                    "description": f"Standard model for {provider_id}",
                    "parameters": "N/A",
                    "speed": "medium",
                    "accuracy": "high",
                    "cost_multiplier": 1.0,
                    "recommended": True
                }
            ]
        })

        return {
            "provider_id": provider_id,
            "provider_name": provider_id.replace("_", " ").title(),
            "models": models_data["models"],
            "model_count": len(models_data["models"]),
            "default_model": next(
                (m["id"] for m in models_data["models"] if m.get("recommended", False)),
                models_data["models"][0]["id"] if models_data["models"] else None
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models for {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model information: {str(e)}")


@router.get("/providers/{provider_id}/benchmark")
async def get_provider_benchmark(
    provider_id: str,
    request: Request,
    response: Response,
    language: Optional[str] = Query(None, description="Filter by language code"),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get WER (Word Error Rate) benchmark data for a specific ASR provider.

    Returns accuracy metrics, test conditions, and language-specific results.

    Args:
        provider_id: Provider identifier
        language: Optional language filter

    Returns:
        dict: Benchmark data with WER scores and test conditions
    """
    try:
        # Check if provider exists
        asr_service: ASRProviderService = await get_asr_service()
        health = await asr_service.get_provider_health(provider_id)

        if health.status == 'offline':
            raise HTTPException(
                status_code=503,
                detail=f"Provider {provider_id} is currently offline"
            )

        # Get benchmark data
        if provider_id not in PROVIDER_BENCHMARKS:
            return {
                "provider_id": provider_id,
                "provider_name": provider_id.replace("_", " ").title(),
                "message": "Benchmark data not yet available for this provider",
                "overall_wer": None,
                "language_results": []
            }

        benchmark_data = PROVIDER_BENCHMARKS[provider_id].copy()

        # Filter by language if specified
        if language:
            language_lower = language.lower()
            benchmark_data["language_results"] = [
                lr for lr in benchmark_data["language_results"]
                if lr["language"] == language_lower
            ]

            if not benchmark_data["language_results"]:
                raise HTTPException(
                    status_code=404,
                    detail=f"No benchmark data for language '{language}' on provider '{provider_id}'"
                )

        return benchmark_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting benchmark for {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmark data: {str(e)}")


@router.get("/compare")
async def compare_providers(
    request: Request,
    response: Response,
    language: Optional[str] = Query(None, description="Filter by language support"),
    include_offline: bool = Query(False, description="Include offline providers"),
    sort_by: str = Query("accuracy", description="Sort by: accuracy, speed, or cost"),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Compare all ASR providers side-by-side.

    Returns comprehensive comparison of capabilities, benchmarks, and metadata.
    Filterable by language support and sortable by different criteria.

    Args:
        language: Filter providers supporting this language
        include_offline: Include offline providers in comparison
        sort_by: Sort criterion (accuracy, speed, or cost)

    Returns:
        dict: Side-by-side provider comparison
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Get all providers with health status
        providers_health = await asr_service.get_all_providers_health()

        # Build comparison data
        comparison_list = []

        for health in providers_health:
            # Skip offline providers if not requested
            if health.status == 'offline' and not include_offline:
                continue

            # Get language list
            languages = await asr_service.get_available_languages(health.provider_id)

            # Filter by language if specified
            if language and language.lower() not in [l.lower() for l in languages]:
                continue

            # Get benchmark data
            benchmark = PROVIDER_BENCHMARKS.get(health.provider_id, {})

            # Get language-specific benchmark if filtering
            language_specific_wer = None
            language_specific_accuracy = None
            if language and benchmark:
                lang_result = next(
                    (lr for lr in benchmark.get("language_results", [])
                     if lr["language"] == language.lower()),
                    None
                )
                if lang_result:
                    language_specific_wer = lang_result["wer"]
                    language_specific_accuracy = lang_result["accuracy"]

            # Build comparison entry
            provider_comparison = {
                "provider_id": health.provider_id,
                "provider_name": health.provider_id.replace("_", " ").title(),
                "status": health.status,
                "endpoint": health.endpoint,
                "languages_count": len(languages),
                "languages": languages,
                "response_time_ms": health.response_time_ms,
                "overall_wer": benchmark.get("overall_wer"),
                "overall_accuracy": 100 - benchmark.get("overall_wer", 0) if benchmark.get("overall_wer") else None,
                "last_checked": health.last_check.isoformat()
            }

            # Add language-specific metrics if filtering
            if language:
                provider_comparison["language_specific"] = {
                    "language": language,
                    "wer": language_specific_wer,
                    "accuracy": language_specific_accuracy
                }

            comparison_list.append(provider_comparison)

        # Sort comparison list
        if sort_by == "accuracy":
            # Sort by WER ascending (lower is better)
            comparison_list.sort(
                key=lambda x: x.get("overall_wer") or float('inf')
            )
        elif sort_by == "speed":
            # Sort by response time ascending (faster is better)
            comparison_list.sort(
                key=lambda x: x.get("response_time_ms") or float('inf')
            )
        elif sort_by == "cost":
            # For now, just sort by response time (faster = cheaper compute)
            # TODO: Add actual cost data when available
            comparison_list.sort(
                key=lambda x: x.get("response_time_ms") or float('inf')
            )

        # Calculate summary statistics
        online_providers = [p for p in comparison_list if p["status"] == "online"]
        avg_wer = sum(p.get("overall_wer", 0) for p in online_providers if p.get("overall_wer")) / len(online_providers) if online_providers else None

        return {
            "providers": comparison_list,
            "count": len(comparison_list),
            "online_count": len(online_providers),
            "language_filter": language,
            "sort_by": sort_by,
            "summary": {
                "average_wer": round(avg_wer, 2) if avg_wer else None,
                "average_accuracy": round(100 - avg_wer, 2) if avg_wer else None,
                "best_accuracy_provider": comparison_list[0]["provider_id"] if comparison_list and sort_by == "accuracy" else None,
                "fastest_provider": comparison_list[0]["provider_id"] if comparison_list and sort_by == "speed" else None
            }
        }

    except Exception as e:
        logger.error(f"Error comparing providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare providers: {str(e)}")


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check for ASR services route.

    Returns:
        dict: Health status
    """
    try:
        # Get ASR service
        asr_service: ASRProviderService = await get_asr_service()

        # Get provider count
        providers = await asr_service.get_all_providers_health()

        return {
            "status": "healthy",
            "service": "asr-services",
            "providers_count": len(providers),
            "billing_enabled": asr_service.enable_billing,
            "health_monitoring_enabled": asr_service.enable_health_monitoring,
        }

    except Exception as e:
        logger.error(f"ASR health check error: {e}")
        return {
            "status": "unhealthy",
            "service": "asr-services",
            "error": str(e)
        }


# ============================================================================
# Transcription History Endpoints
# ============================================================================

@router.get("/history", response_model=TranscriptionHistoryListResponse)
async def get_transcription_history(
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search text in transcripts"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    language: Optional[str] = Query(None, description="Filter by language"),
    task: Optional[str] = Query(None, description="Filter by task (transcribe/translate)"),
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
):
    """
    Get user's transcription history with pagination and filters.

    Args:
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        page: Page number (1-indexed)
        limit: Items per page (1-100)
        search: Optional text search query
        provider: Optional provider filter
        language: Optional language filter
        task: Optional task filter (transcribe/translate)
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        TranscriptionHistoryListResponse: Paginated history items
    """
    try:
        history_service = await get_transcription_history_service()

        result = await history_service.get_user_history(
            user_id=user["id"],
            page=page,
            limit=limit,
            search_text=search,
            provider_filter=provider,
            language_filter=language,
            task_filter=task
        )

        logger.info(
            f"Retrieved transcription history for user={user['id']}: page={page}, "
            f"total={result.total}, returned={len(result.items)}"
        )

        return result

    except Exception as e:
        logger.error(f"Error retrieving transcription history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/history/{item_id}")
async def get_history_item(
    item_id: str,
    request: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get a specific transcription history item with full details (including audio).

    Args:
        item_id: History item ID
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        dict: History item with full audio data
    """
    try:
        history_service = await get_transcription_history_service()

        item = await history_service.get_history_item(
            user_id=user["id"],
            item_id=item_id
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription history item '{item_id}' not found"
            )

        logger.info(f"Retrieved transcription history item {item_id} for user={user['id']}")
        return item

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcription history item {item_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history item: {str(e)}"
        )


@router.delete("/history/{item_id}")
async def delete_history_item(
    item_id: str,
    request: Request,
    response: Response,
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Soft delete a transcription history item.

    Args:
        item_id: History item ID
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        dict: Success message
    """
    try:
        history_service = await get_transcription_history_service()

        success = await history_service.delete_history_item(
            user_id=user["id"],
            item_id=item_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription history item '{item_id}' not found or already deleted"
            )

        logger.info(f"Deleted transcription history item {item_id} for user={user['id']}")
        return {
            "success": True,
            "message": "Transcription history item deleted successfully",
            "item_id": item_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transcription history item {item_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete history item: {str(e)}"
        )


@router.get("/history/stats")
async def get_user_statistics(
    request: Request,
    response: Response,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: dict = Depends(get_current_user_mongo),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get user's transcription statistics for the last N days.

    Args:
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        days: Number of days to look back (1-365)
        user: Current authenticated user
        rate_limit: Rate limit dependency

    Returns:
        dict: Statistics including total transcriptions, costs, duration, etc.
    """
    try:
        history_service = await get_transcription_history_service()

        stats = await history_service.get_user_statistics(
            user_id=user["id"],
            days=days
        )

        logger.info(f"Retrieved transcription statistics for user={user['id']}, days={days}")
        return stats

    except Exception as e:
        logger.error(f"Error retrieving transcription statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

# ============================================================================
# Sample Audio Endpoints (Phase 3)
# ============================================================================

@router.get("/samples")
async def list_samples(
    request: Request,
    response: Response,
    language: Optional[str] = Query(None, description="Filter by language (en, tw, multilingual)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (easy, medium, hard)"),
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    List all available ASR test samples with metadata.

    Args:
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        language: Optional language filter
        difficulty: Optional difficulty filter
        rate_limit: Rate limit dependency

    Returns:
        dict: Sample metadata including ground truth transcripts
    """
    try:
        import json
        from pathlib import Path

        # Load metadata
        metadata_path = Path("/opt/kasaai/apps/voice-lab/asr_samples/samples_metadata.json")

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Sample metadata not found")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Apply filters
        if language:
            if language == "en":
                samples = metadata["english_samples"]
            elif language == "tw":
                samples = metadata["twi_samples"]
            elif language == "multilingual":
                samples = metadata["multilingual_samples"]
            else:
                raise HTTPException(status_code=400, detail=f"Invalid language: {language}")

            filtered_metadata = {
                "samples": samples,
                "total": len(samples),
                "language_filter": language
            }
        else:
            # Return all samples
            all_samples = (
                metadata["english_samples"] +
                metadata["twi_samples"] +
                metadata["multilingual_samples"]
            )

            filtered_metadata = {
                "samples": all_samples,
                "total": len(all_samples),
                "generation_date": metadata["generation_date"]
            }

        # Apply difficulty filter if provided
        if difficulty:
            filtered_samples = [
                s for s in filtered_metadata["samples"]
                if s.get("difficulty") == difficulty
            ]
            filtered_metadata["samples"] = filtered_samples
            filtered_metadata["total"] = len(filtered_samples)
            filtered_metadata["difficulty_filter"] = difficulty

        logger.info(f"Listed {filtered_metadata['total']} ASR samples")
        return filtered_metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing samples: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list samples: {str(e)}"
        )


@router.get("/samples/transcript/{sample_id}")
async def get_sample_transcript(
    sample_id: str,
    request: Request,
    response: Response,
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
) -> Dict:
    """
    Get ground truth transcript for a sample.

    Args:
        sample_id: Sample ID (e.g., en_hello_world, tw_akwaaba)
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        rate_limit: Rate limit dependency

    Returns:
        dict: Sample metadata including ground truth transcript
    """
    try:
        import json
        from pathlib import Path

        # Load metadata
        metadata_path = Path("/opt/kasaai/apps/voice-lab/asr_samples/samples_metadata.json")

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Sample metadata not found")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Search for sample by ID
        all_samples = (
            metadata["english_samples"] +
            metadata["twi_samples"] +
            metadata["multilingual_samples"]
        )

        sample = next((s for s in all_samples if s["id"] == sample_id), None)

        if not sample:
            raise HTTPException(
                status_code=404,
                detail=f"Sample not found: {sample_id}"
            )

        logger.info(f"Retrieved transcript for sample: {sample_id}")
        return {
            "sample_id": sample_id,
            "ground_truth": sample["ground_truth"],
            "language": sample["language"],
            "difficulty": sample.get("difficulty", "unknown"),
            "description": sample.get("description", ""),
            "duration_seconds": sample["duration_seconds"],
            "path": sample["path"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sample transcript {sample_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transcript: {str(e)}"
        )
@router.get("/samples/{category}/{filename}")
async def get_sample_file(
    category: str,
    filename: str,
    request: Request,
    response: Response,
    rate_limit: None = Depends(get_asr_rate_limit("info", "free"))
):
    """
    Serve ASR sample audio file.

    Args:
        category: Sample category (english_samples, twi_samples, multilingual_samples)
        filename: Audio filename (e.g., hello_world.wav)
        request: FastAPI request object (for rate limiting)
        response: FastAPI response object (for headers)
        rate_limit: Rate limit dependency

    Returns:
        FileResponse: Audio file
    """
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path

        # Validate category
        valid_categories = ["english_samples", "twi_samples", "multilingual_samples"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )

        # Construct file path
        base_path = Path("/opt/kasaai/apps/voice-lab/asr_samples")
        file_path = base_path / category / filename

        # Security: Ensure file is within samples directory
        if not file_path.resolve().is_relative_to(base_path.resolve()):
            raise HTTPException(status_code=403, detail="Access denied")

        # Check file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Sample file not found: {category}/{filename}"
            )

        logger.info(f"Serving sample file: {category}/{filename}")
        return FileResponse(
            path=str(file_path),
            media_type="audio/wav",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving sample file {category}/{filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve sample file: {str(e)}"
        )



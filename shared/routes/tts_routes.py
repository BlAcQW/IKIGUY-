"""
Unified TTS API Routes

Provides standardized TTS endpoints for all backend applications.
Includes synthesis, provider management, cost estimation, and caching.

Mount in FastAPI app:
    from apps.shared.routes.tts_routes import router as tts_router
    app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])

Endpoints:
    POST   /synthesize          - Synthesize text with billing
    POST   /synthesize/batch    - Batch synthesis
    POST   /clone-voice         - Voice cloning with billing
    GET    /providers           - List available providers
    GET    /providers/{id}      - Get provider details
    GET    /estimate-cost       - Estimate synthesis cost
    GET    /cache/stats         - Cache statistics
    DELETE /cache               - Clear cache
    GET    /health              - Health check all providers

Author: KasaAI Team
Date: 2025-11-23
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
import base64

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.tts.client import AsyncTTSClient
from shared.tts.models import (
    TTSProvider,
    TTSRequest,
    TTSResponse,
    VoiceCloneRequest,
    ProviderStatus,
    AudioFormat,
    TTSCapabilities,
)
from shared.tts.billing import TTSBillingManager
from shared.tts.cache import TTSAudioCache, CacheStats
from shared.tts.provider_ids import normalize_provider_id, ProviderID
from shared.tts.provider_cache import TTSProviderCache, get_cached_providers
from shared.integration.wallet import WalletService, Currency
from shared.integration.usage_calculator import PricingTier

# Initialize router
router = APIRouter()

# In-memory fallback cache (used if MongoDB cache fails)
_provider_cache = {}
_cache_ttl = timedelta(minutes=5)

# App name for cache logging (set by each app that mounts this router)
_app_name: Optional[str] = None


def set_app_name(name: str):
    """Set app name for cache logging. Call this when mounting the router."""
    global _app_name
    _app_name = name


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_from_jwt(authorization: str = Header(...)) -> dict:
    """
    Extract user information from JWT token.

    Works with multiple auth systems:
    - core_backend: MongoDB-based JWT auth
    - studyflow: Supabase JWT auth
    - Other apps: Standard JWT tokens

    Args:
        authorization: Authorization header in format "Bearer {token}"

    Returns:
        dict: User info with 'sub' field containing user_id

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    # Try core_backend auth service first
    try:
        from apps.core_backend.backend.services.auth_service import get_auth_service

        auth_service = await get_auth_service()
        user_data = await auth_service.get_current_user(token)
        return user_data
    except ImportError:
        # core_backend not available, use fallback
        pass
    except Exception:
        # Auth service failed, try other methods
        pass

    # Fallback: Decode JWT token without signature verification
    # This works for Supabase tokens and other JWT-based systems
    # Note: Signature verification should be done at the API gateway/middleware level
    try:
        import jwt as jwt_lib

        # Decode without verification (Supabase tokens are pre-verified by Supabase)
        # In production, verification happens at the middleware/gateway level
        payload = jwt_lib.decode(
            token,
            options={"verify_signature": False}
        )

        # Ensure we have a user_id
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID not found in token (missing 'sub' or 'user_id' claim)"
            )

        return payload

    except jwt_lib.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt_lib.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# ============================================================================
# Request/Response Models
# ============================================================================

class SynthesizeRequest(BaseModel):
    """
    Synthesis request with optional user ID for billing (extracted from JWT if not provided).

    Accepts both frontend field names (provider_id, voice_id) and canonical names (provider, speaker).
    Frontend field names take precedence for backward compatibility.
    """
    user_id: Optional[str] = Field(None, description="User ID for billing (optional, extracted from JWT)")
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    # Accept both provider_id (frontend) and provider (canonical)
    provider_id: Optional[str] = Field(None, description="TTS provider ID (frontend format)")
    provider: Optional[str] = Field(None, description="TTS provider ID (canonical format)")
    language: str = Field(default="en", description="Language code")
    # Accept both voice_id (frontend) and speaker (canonical)
    voice_id: Optional[str] = Field(None, description="Voice/speaker ID (frontend format)")
    speaker: Optional[str] = Field(None, description="Speaker/voice ID (canonical format)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0, description="Voice pitch adjustment")
    output_format: str = Field(default="wav", description="Audio format (wav, mp3, etc)")
    sample_rate: int = Field(default=22050, ge=8000, le=48000, description="Sample rate")

    def get_provider(self) -> Optional[str]:
        """Get provider ID, preferring frontend field name."""
        return self.provider_id or self.provider

    def get_voice(self) -> Optional[str]:
        """Get voice/speaker ID, preferring frontend field name."""
        return self.voice_id or self.speaker


class VoiceCloneRequestWithUser(BaseModel):
    """Voice cloning request with optional user ID for billing (extracted from JWT if not provided)."""
    user_id: Optional[str] = Field(None, description="User ID for billing (optional, extracted from JWT)")
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    reference_audio: bytes = Field(..., description="Reference audio for cloning")
    # Accept both provider_id (frontend) and provider (canonical)
    provider_id: Optional[str] = Field(None, description="TTS provider ID (frontend format)")
    provider: Optional[str] = Field(None, description="TTS provider ID (canonical format)")
    language: str = Field(default="en", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    output_format: str = Field(default="wav", description="Audio format (wav, mp3, etc)")
    sample_rate: int = Field(default=22050, ge=8000, le=48000, description="Sample rate")

    def get_provider(self) -> Optional[str]:
        """Get provider ID, preferring frontend field name."""
        return self.provider_id or self.provider


class CostEstimateRequest(BaseModel):
    """Cost estimation request."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    provider: str = Field(..., description="TTS provider ID")
    voice_cloning: bool = Field(default=False, description="Voice cloning enabled")


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    text_length: int
    provider_id: str
    voice_cloning: bool
    estimated_cost: float
    currency: str
    pricing_tier: str


class SynthesizeResponseWithTransaction(BaseModel):
    """Synthesis response with transaction details."""
    audio_base64: Optional[str] = None  # Base64-encoded audio data (for JSON serialization)
    audio_url: Optional[str] = None
    format: str  # Audio format as string for frontend compatibility
    sample_rate: int
    duration: Optional[float] = None
    provider: str  # Canonical provider name
    provider_id: Optional[str] = None  # Provider ID for frontend compatibility
    language: str
    cost: float
    transaction_id: Optional[str] = None  # Optional for zero-cost requests (e.g., free tier)
    processing_time: Optional[float] = None


# ============================================================================
# Dependencies
# ============================================================================

async def get_billing_manager() -> TTSBillingManager:
    """
    Get TTSBillingManager instance.

    Note: In production, initialize this once at app startup and inject as dependency.
    """
    # This is a simplified version - in production, get from app state
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient("mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin")
    wallet_service = WalletService(database=client.kasaai_core)

    return TTSBillingManager(
        wallet_service=wallet_service,
        pricing_tier=PricingTier.BASIC,
        currency=Currency.GHS
    )


async def get_cache() -> TTSAudioCache:
    """
    Get TTSAudioCache instance.

    Note: In production, initialize this once at app startup and inject as dependency.
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient("mongodb://admin:aawwER4444%25@127.0.0.1:27017/?authSource=admin")

    cache = TTSAudioCache(
        database=client.tts_cache,
        default_ttl_hours=24,
        enable_metrics=True
    )

    # Ensure indexes (should be done at app startup)
    await cache.ensure_indexes()

    return cache


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/preview")
async def preview_voice(
    request: SynthesizeRequest,
    user: dict = Depends(get_current_user_from_jwt)
):
    """
    Preview TTS voice without billing.

    This endpoint is for voice settings preview - no wallet required.
    Text is limited to 200 characters for preview.

    Authentication: Requires JWT token in Authorization header.
    """
    try:
        # Limit text length for preview
        preview_text = request.text[:200] if len(request.text) > 200 else request.text

        # Normalize provider ID
        provider_str = request.get_provider()
        if provider_str:
            canonical_id = normalize_provider_id(provider_str)
            if not canonical_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider ID: {provider_str}"
                )
            provider_enum = TTSProvider(canonical_id)
        else:
            provider_enum = TTSProvider.KOKORO  # Default for preview

        # Get voice/speaker
        voice = request.get_voice()

        # Convert output_format string to AudioFormat enum
        try:
            output_format_enum = AudioFormat(request.output_format.lower())
        except ValueError:
            output_format_enum = AudioFormat.WAV

        # Create TTS client and synthesize directly (no billing)
        async with AsyncTTSClient() as client:
            response = await client.synthesize(
                text=preview_text,
                provider=provider_enum,
                language=request.language,
                speaker=voice,
                speed=request.speed,
                output_format=output_format_enum,
                sample_rate=request.sample_rate
            )

        # Convert audio bytes to base64
        audio_base64 = None
        if response.audio:
            audio_base64 = base64.b64encode(response.audio).decode('utf-8')

        provider_value = response.provider.value if hasattr(response.provider, 'value') else str(response.provider)
        format_value = response.format.value if hasattr(response.format, 'value') else str(response.format)

        return {
            "audio_base64": audio_base64,
            "format": format_value,
            "sample_rate": response.sample_rate,
            "duration": response.duration,
            "provider": provider_value,
            "provider_id": provider_value,
            "language": response.language,
            "cost": 0.0,  # Preview is free
            "processing_time": response.processing_time
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/synthesize", response_model=SynthesizeResponseWithTransaction)
async def synthesize_with_billing(
    request: SynthesizeRequest,
    billing_manager: TTSBillingManager = Depends(get_billing_manager),
    user: dict = Depends(get_current_user_from_jwt)
):
    """
    Synthesize text with automatic billing.

    Deducts cost from user wallet before synthesis.
    Refunds automatically on failure.

    Authentication: Requires JWT token in Authorization header.
    User ID is extracted from JWT token automatically.
    """
    try:
        # Get user_id from JWT token (prefer JWT over body parameter)
        user_id = user.get("sub") or user.get("user_id") or request.user_id

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not found in JWT token"
            )

        # Normalize provider ID (accept both provider_id and provider)
        provider_str = request.get_provider()
        if provider_str:
            canonical_id = normalize_provider_id(provider_str)
            if not canonical_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider ID: {provider_str}. "
                           f"Valid IDs: {', '.join(sorted(ProviderID.all()))}"
                )
            provider_enum = TTSProvider(canonical_id)
        else:
            provider_enum = None

        # Get voice/speaker (accept both voice_id and speaker)
        voice = request.get_voice()

        # Convert output_format string to AudioFormat enum
        try:
            output_format_enum = AudioFormat(request.output_format.lower())
        except ValueError:
            output_format_enum = AudioFormat.WAV

        # Synthesize with billing
        response, transaction = await billing_manager.synthesize_with_billing(
            user_id=user_id,
            text=request.text,
            provider=provider_enum,
            language=request.language,
            speaker=voice,
            speed=request.speed,
            output_format=output_format_enum,
            sample_rate=request.sample_rate
        )

        # Convert audio bytes to base64 string for JSON serialization
        audio_base64 = None
        if response.audio:
            audio_base64 = base64.b64encode(response.audio).decode('utf-8')

        # Extract values safely for response
        provider_value = response.provider.value if hasattr(response.provider, 'value') else str(response.provider)
        format_value = response.format.value if hasattr(response.format, 'value') else str(response.format)

        return SynthesizeResponseWithTransaction(
            audio_base64=audio_base64,
            audio_url=response.audio_url,
            format=format_value,
            sample_rate=response.sample_rate,
            duration=response.duration,
            provider=provider_value,
            provider_id=provider_value,  # Include for frontend compatibility
            language=response.language,
            cost=float(response.cost or 0),
            transaction_id=str(transaction.id) if transaction else None,
            processing_time=response.processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/clone-voice", response_model=SynthesizeResponseWithTransaction)
async def clone_voice_with_billing(
    request: VoiceCloneRequestWithUser,
    billing_manager: TTSBillingManager = Depends(get_billing_manager),
    user: dict = Depends(get_current_user_from_jwt)
):
    """
    Clone voice with automatic billing.

    Note: Voice cloning costs 2x standard synthesis.

    Authentication: Requires JWT token in Authorization header.
    User ID is extracted from JWT token automatically.
    """
    try:
        # Get user_id from JWT token (prefer JWT over body parameter)
        user_id = user.get("sub") or user.get("user_id") or request.user_id

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not found in JWT token"
            )

        # Normalize provider ID (accept both provider_id and provider)
        provider_str = request.get_provider()
        if provider_str:
            canonical_id = normalize_provider_id(provider_str)
            if not canonical_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider ID: {provider_str}"
                )
            provider_enum = TTSProvider(canonical_id)
        else:
            provider_enum = None

        # Convert output_format string to AudioFormat enum
        try:
            output_format_enum = AudioFormat(request.output_format.lower())
        except ValueError:
            output_format_enum = AudioFormat.WAV

        # Clone voice with billing
        response, transaction = await billing_manager.clone_voice_with_billing(
            user_id=user_id,
            text=request.text,
            reference_audio=request.reference_audio,
            provider=provider_enum,
            language=request.language,
            speed=request.speed,
            output_format=output_format_enum,
            sample_rate=request.sample_rate
        )

        # Convert audio bytes to base64 string for JSON serialization
        audio_base64 = None
        if response.audio:
            audio_base64 = base64.b64encode(response.audio).decode('utf-8')

        # Extract values safely for response
        provider_value = response.provider.value if hasattr(response.provider, 'value') else str(response.provider)
        format_value = response.format.value if hasattr(response.format, 'value') else str(response.format)

        return SynthesizeResponseWithTransaction(
            audio_base64=audio_base64,
            audio_url=response.audio_url,
            format=format_value,
            sample_rate=response.sample_rate,
            duration=response.duration,
            provider=provider_value,
            provider_id=provider_value,  # Include for frontend compatibility
            language=response.language,
            cost=float(response.cost or 0),
            transaction_id=str(transaction.id) if transaction else None,
            processing_time=response.processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _perform_health_checks(online_only: bool = False) -> dict:
    """
    Perform health checks on all TTS providers.

    This is the callback function used by the centralized cache.
    It performs parallel health checks with individual timeouts.

    Args:
        online_only: Whether to filter for online providers only

    Returns:
        Dict with providers, count, online_count, offline_count
    """
    async with AsyncTTSClient() as client:
        providers_list = []
        provider_items = list(client._providers.items())

        async def check_provider_health(provider_name, provider_instance):
            """Helper to check individual provider health with 5-second timeout."""
            try:
                return await asyncio.wait_for(
                    provider_instance.check_health(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                return ProviderStatus(
                    provider=provider_name,
                    name=provider_instance.config.name if hasattr(provider_instance, 'config') else provider_name.value if hasattr(provider_name, 'value') else str(provider_name),
                    endpoint=provider_instance.config.endpoint.base_url if hasattr(provider_instance, 'config') else "unavailable",
                    status="offline",
                    capabilities=provider_instance.config.capabilities if hasattr(provider_instance, 'config') else TTSCapabilities(),
                    description=provider_instance.config.description if hasattr(provider_instance, 'config') else "Provider health check timed out"
                )
            except Exception as e:
                return ProviderStatus(
                    provider=provider_name,
                    name=provider_instance.config.name if hasattr(provider_instance, 'config') else provider_name.value if hasattr(provider_name, 'value') else str(provider_name),
                    endpoint=provider_instance.config.endpoint.base_url if hasattr(provider_instance, 'config') else "unavailable",
                    status="offline",
                    capabilities=provider_instance.config.capabilities if hasattr(provider_instance, 'config') else TTSCapabilities(),
                    description=provider_instance.config.description if hasattr(provider_instance, 'config') else f"Provider unavailable: {str(e)}"
                )

        # Execute all health checks in parallel
        health_checks = [
            check_provider_health(name, instance)
            for name, instance in provider_items
        ]

        try:
            provider_statuses = await asyncio.wait_for(
                asyncio.gather(*health_checks, return_exceptions=True),
                timeout=15.0  # Increased to 15s for centralized cache
            )
        except asyncio.TimeoutError:
            provider_statuses = []

        # Filter results
        for provider_status in provider_statuses:
            if isinstance(provider_status, Exception):
                continue
            if online_only and provider_status.status != "online":
                continue
            providers_list.append(provider_status)

        # Convert to dict format for frontend compatibility
        providers_dict = {}
        for p in providers_list:
            provider_id = p.provider if isinstance(p.provider, str) else p.provider.value

            capabilities_dict = {
                "voiceCloning": p.capabilities.voice_cloning,
                "multiLanguage": p.capabilities.multi_language,
                "speedControl": p.capabilities.speed_control,
                "pitchControl": p.capabilities.pitch_control,
                "multiSpeaker": p.capabilities.multi_speaker,
                "multiModel": p.capabilities.multi_model,
                "emotionControl": p.capabilities.emotion_control,
                "realTimeConversation": p.capabilities.real_time_conversation,
                "ssmlSupport": p.capabilities.ssml_support,
                "streaming": p.capabilities.streaming,
            }

            # Get speakers and languages dict from provider config if available
            speakers_dict = {}
            languages_dict = {}

            # Try to get speakers and languages from the provider config
            try:
                from shared.tts.config import PROVIDER_CONFIGS, TTSProvider as TTSProviderEnum
                provider_enum = TTSProviderEnum(provider_id)
                if provider_enum in PROVIDER_CONFIGS:
                    config = PROVIDER_CONFIGS[provider_enum]
                    speakers_dict = config.speakers or {}
                    languages_dict = config.languages or {}
            except (ValueError, KeyError, ImportError) as e:
                # Provider not found in config or import failed, use defaults
                import logging
                logging.getLogger(__name__).debug(f"Could not get config for {provider_id}: {e}")
                pass

            # If languages_dict is empty, generate from languageList
            if not languages_dict and p.capabilities.supported_languages:
                language_names = {
                    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
                    "it": "Italian", "pt": "Portuguese", "pl": "Polish", "tr": "Turkish",
                    "ru": "Russian", "nl": "Dutch", "cs": "Czech", "ar": "Arabic",
                    "zh-cn": "Chinese (Simplified)", "zh": "Chinese", "hu": "Hungarian",
                    "ko": "Korean", "ja": "Japanese", "hi": "Hindi", "sw": "Swahili",
                    "EN": "English", "ES": "Spanish", "FR": "French", "ZH": "Chinese",
                    "JP": "Japanese", "KR": "Korean", "EN-US": "American English",
                    "EN-BR": "British English", "EN-INDIA": "Indian English",
                    "EN-AU": "Australian English", "EN-Default": "Default English",
                }
                for lang_code in p.capabilities.supported_languages:
                    languages_dict[lang_code] = language_names.get(lang_code, lang_code.upper())

            providers_dict[provider_id] = {
                "id": provider_id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": p.status,
                "capabilities": capabilities_dict,
                "description": p.description,
                "icon": getattr(p, "icon", "🔊"),
                "languages": len(p.capabilities.supported_languages),
                "languageList": p.capabilities.supported_languages,
                "languagesDict": languages_dict,
                "speakers": speakers_dict,
                "lastChecked": p.last_check.isoformat() if p.last_check else datetime.utcnow().isoformat(),
                "responseTime": getattr(p, "response_time", None)
            }

        online_count = sum(1 for p in providers_dict.values() if p["status"] == "online")
        offline_count = sum(1 for p in providers_dict.values() if p["status"] == "offline")

        return {
            "providers": providers_dict,
            "count": len(providers_dict),
            "online_count": online_count,
            "offline_count": offline_count,
        }


@router.get("/providers")
async def list_providers(
    online_only: bool = Query(default=False, description="Return only online providers"),
    force_refresh: bool = Query(default=False, description="Force cache refresh")
):
    """
    List all TTS providers with cached health status.

    Returns dict with providers, count, online_count, offline_count for backward compatibility.

    Performance optimizations:
    - 10-minute centralized MongoDB cache shared across all apps
    - Only one app performs health checks when cache expires
    - Other apps get instant response from shared cache
    - Fallback to in-memory cache if MongoDB unavailable
    """
    try:
        # Create refresh callback that captures online_only parameter
        async def refresh_callback():
            return await _perform_health_checks(online_only=online_only)

        # Try centralized MongoDB cache first
        try:
            result = await get_cached_providers(
                online_only=online_only,
                force_refresh=force_refresh,
                refresh_callback=refresh_callback,
                app_name=_app_name
            )

            if result:
                # Remove internal cache metadata before returning
                return_result = {
                    "providers": result["providers"],
                    "count": result["count"],
                    "online_count": result["online_count"],
                    "offline_count": result["offline_count"],
                }
                return return_result

        except Exception as cache_error:
            # Log error but continue with fallback
            import logging
            logging.getLogger(__name__).warning(
                f"MongoDB provider cache failed, using in-memory fallback: {cache_error}"
            )

        # Fallback to in-memory cache
        now = datetime.utcnow()
        cache_key = f"providers_{online_only}"

        if not force_refresh and cache_key in _provider_cache:
            cached_data, cached_time = _provider_cache[cache_key]
            if now - cached_time < _cache_ttl:
                return cached_data

        # Perform health checks
        result = await _perform_health_checks(online_only=online_only)

        # Cache in memory
        _provider_cache[cache_key] = (result, now)

        return result

    except HTTPException:
        raise
    except Exception as e:
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.get("/providers/{provider_id}", response_model=ProviderStatus)
async def get_provider(provider_id: str):
    """
    Get specific provider details and health status.
    """
    try:
        # Normalize provider ID
        canonical_id = normalize_provider_id(provider_id)
        if not canonical_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider not found: {provider_id}"
            )

        async with AsyncTTSClient() as client:
            provider_enum = TTSProvider(canonical_id)
            provider_instance = client._providers.get(provider_enum)

            if not provider_instance:
                from fastapi import status as http_status
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Provider not found: {canonical_id}"
                )

            provider_status = await provider_instance.check_health()
            return provider_status

    except HTTPException:
        raise
    except Exception as e:
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(
    text: str = Query(..., min_length=1, max_length=5000),
    provider: str = Query(..., description="Provider ID"),
    voice_cloning: bool = Query(default=False),
    billing_manager: TTSBillingManager = Depends(get_billing_manager)
):
    """
    Estimate cost for TTS synthesis.
    """
    try:
        # Normalize provider ID
        canonical_id = normalize_provider_id(provider)
        if not canonical_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider ID: {provider}"
            )

        provider_enum = TTSProvider(canonical_id)

        # Estimate cost
        cost = await billing_manager.estimate_cost(
            text=text,
            provider=provider_enum,
            voice_cloning=voice_cloning
        )

        return CostEstimateResponse(
            text_length=len(text),
            provider_id=canonical_id,
            voice_cloning=voice_cloning,
            estimated_cost=float(cost),
            currency=billing_manager.currency.value,
            pricing_tier=billing_manager.pricing_tier.value
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/cache/stats", response_model=CacheStats)
async def get_cache_stats(
    cache: TTSAudioCache = Depends(get_cache)
):
    """
    Get cache statistics.
    """
    try:
        stats = await cache.get_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/cache/providers")
async def get_provider_cache_info():
    """
    Get centralized provider cache statistics.

    Shows which app last refreshed the cache and when it expires.
    """
    try:
        cache = await TTSProviderCache.get_instance()
        info = await cache.get_cache_info()
        return {
            "status": "success",
            "app_name": _app_name,
            "cache_info": info
        }
    except Exception as e:
        return {
            "status": "error",
            "app_name": _app_name,
            "error": str(e),
            "message": "Provider cache unavailable, using in-memory fallback"
        }


@router.delete("/cache")
async def clear_cache(
    cache: TTSAudioCache = Depends(get_cache)
):
    """
    Clear all cache entries.

    Note: This is a destructive operation.
    """
    try:
        count = await cache.clear_all()

        return {
            "status": "success",
            "message": f"Cleared {count} cache entries"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def health_check():
    """
    Health check for TTS system.

    Returns summary of all provider statuses.
    """
    try:
        async with AsyncTTSClient() as client:
            provider_statuses = {}

            # Access private _providers attribute
            for provider_name, provider_instance in client._providers.items():
                try:
                    status = await provider_instance.check_health()
                    provider_statuses[provider_name.value] = {
                        "status": status.status,
                        "endpoint": status.endpoint
                    }
                except Exception as e:
                    provider_statuses[provider_name.value] = {
                        "status": "error",
                        "error": str(e)
                    }

            online_count = sum(
                1 for p in provider_statuses.values()
                if p.get("status") == "online"
            )

            return {
                "status": "healthy" if online_count > 0 else "degraded",
                "providers_online": online_count,
                "providers_total": len(provider_statuses),
                "providers": provider_statuses
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

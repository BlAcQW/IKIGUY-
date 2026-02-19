"""
Unified Provider Discovery Routes

Provides standardized endpoints for discovering AI providers across TTS, ASR, and LLM.
All apps can mount this router to get consistent provider discovery APIs.

Mount in FastAPI app:
    from apps.shared.routes.provider_routes import router as provider_router
    app.include_router(provider_router, prefix="/api/v1", tags=["Providers"])

Endpoints:
    GET    /providers/tts       - List all TTS providers
    GET    /providers/asr       - List all ASR providers
    GET    /providers/llm       - List all LLM providers
    GET    /providers/all       - List all providers grouped by type
    GET    /providers/{type}/{id} - Get specific provider details
    GET    /providers/health    - Health check all providers

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import logging

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.ai_services.provider_registry import (
    get_global_registry,
    get_default_tts_providers_config,
    get_default_asr_providers_config,
    get_default_llm_providers_config,
)
from shared.integration.ai_services.ai_provider_service import (
    ProviderType,
    ProviderStatus,
    AIProvider,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/providers", tags=["AI Providers"])

# Cache for provider data
_provider_cache: Dict[str, Any] = {}
_cache_ttl_seconds = 300  # 5 minutes


# ============================================================================
# Response Models
# ============================================================================

class ProviderInfo(BaseModel):
    """Provider information response model."""
    id: str
    name: str
    endpoint: str
    provider_type: str
    status: str = "unknown"
    languages: int = 0
    languageList: List[str] = []
    capabilities: Dict[str, bool] = {}
    description: str = ""
    icon: str = ""
    metadata: Dict[str, Any] = {}
    requires_api_key: bool = False
    api_key_env: Optional[str] = None
    is_default: bool = False  # Marks the default provider for each type


class ProvidersListResponse(BaseModel):
    """Response model for provider listing."""
    providers: Dict[str, ProviderInfo]
    count: int
    timestamp: str


class AllProvidersResponse(BaseModel):
    """Response model for all providers grouped by type."""
    tts: Dict[str, ProviderInfo]
    asr: Dict[str, ProviderInfo]
    llm: Dict[str, ProviderInfo]
    stats: Dict[str, int]
    timestamp: str


# ============================================================================
# Helper Functions
# ============================================================================

def _ensure_registry_initialized() -> None:
    """
    Ensure the global registry is initialized with default providers.

    This is called on each request to ensure providers are loaded.
    In production, this should be done once at app startup.
    """
    registry = get_global_registry()

    # Check if already initialized
    if registry.get_stats()["total"] > 0:
        return

    # Load default provider configs
    logger.info("Initializing provider registry with defaults...")

    tts_config = get_default_tts_providers_config()
    registry.register_providers_from_config(tts_config, provider_type=ProviderType.TTS)

    asr_config = get_default_asr_providers_config()
    registry.register_providers_from_config(asr_config, provider_type=ProviderType.ASR)

    llm_config = get_default_llm_providers_config()
    registry.register_providers_from_config(llm_config, provider_type=ProviderType.LLM)

    stats = registry.get_stats()
    logger.info(f"Provider registry initialized: {stats}")


def _provider_to_dict(provider: AIProvider) -> Dict[str, Any]:
    """
    Convert AIProvider to dict for API response.

    Args:
        provider: AIProvider instance

    Returns:
        Dict representation for frontend
    """
    # Extract capabilities
    capabilities = {}
    if provider.capabilities:
        caps = provider.capabilities
        capabilities = {
            "voiceCloning": getattr(caps, "voiceCloning", False),
            "multiLanguage": getattr(caps, "multiLanguage", False),
            "speedControl": getattr(caps, "speedControl", False),
            "pitchControl": getattr(caps, "pitchControl", False),
            "emotionControl": getattr(caps, "emotionControl", False),
            "streaming": getattr(caps, "streaming", False),
            "realtime": getattr(caps, "realtime", False),
            "timestamps": getattr(caps, "timestamps", False),
            "wordLevelTimestamps": getattr(caps, "wordLevelTimestamps", False),
            "diarization": getattr(caps, "diarization", False),
            "punctuation": getattr(caps, "punctuation", False),
            "translation": getattr(caps, "translation", False),
            "reasoning": getattr(caps, "reasoning", False),
            "codeGeneration": getattr(caps, "codeGeneration", False),
            "functionCalling": getattr(caps, "functionCalling", False),
            "vision": getattr(caps, "vision", False),
            "culturalContext": getattr(caps, "culturalContext", False),
            "longContext": getattr(caps, "longContext", False),
        }
        # Remove False values to keep response clean
        capabilities = {k: v for k, v in capabilities.items() if v}

    # Extract status as string
    status_str = provider.status.value if hasattr(provider.status, "value") else str(provider.status)

    # Extract provider type as string
    type_str = provider.provider_type.value if hasattr(provider.provider_type, "value") else str(provider.provider_type)

    return {
        "id": provider.id,
        "name": provider.name,
        "endpoint": provider.endpoint,
        "provider_type": type_str,
        "status": status_str,
        "languages": getattr(provider, "languages", 0),
        "languageList": getattr(provider, "languageList", []),
        "capabilities": capabilities,
        "description": provider.description or "",
        "icon": getattr(provider, "icon", ""),
        "metadata": getattr(provider, "metadata", {}),
        "requires_api_key": getattr(provider, "requires_api_key", False),
        "api_key_env": getattr(provider, "api_key_env", None),
    }


def _get_cached_or_fresh(
    cache_key: str,
    fetch_func: callable,
) -> Dict[str, Any]:
    """
    Get cached data or fetch fresh data.

    Args:
        cache_key: Cache key
        fetch_func: Function to call if cache miss

    Returns:
        Cached or fresh data
    """
    now = datetime.utcnow()

    if cache_key in _provider_cache:
        cached_data, cached_time = _provider_cache[cache_key]
        age_seconds = (now - cached_time).total_seconds()
        if age_seconds < _cache_ttl_seconds:
            return cached_data

    # Fetch fresh data
    fresh_data = fetch_func()
    _provider_cache[cache_key] = (fresh_data, now)
    return fresh_data


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/tts", response_model=ProvidersListResponse)
async def get_tts_providers(
    online_only: bool = Query(default=False, description="Filter for online providers only"),
    force_refresh: bool = Query(default=False, description="Force cache refresh"),
):
    """
    List all TTS providers.

    Returns dict of TTS providers with capabilities, status, and metadata.
    Results are cached for 5 minutes unless force_refresh=True.
    """
    try:
        _ensure_registry_initialized()
        registry = get_global_registry()

        def fetch_providers():
            providers = registry.get_tts_providers()
            result = {}
            for p in providers:
                if online_only and p.status != ProviderStatus.ONLINE:
                    continue
                result[p.id] = _provider_to_dict(p)
            return result

        cache_key = f"tts_{online_only}"
        if force_refresh and cache_key in _provider_cache:
            del _provider_cache[cache_key]

        providers_dict = _get_cached_or_fresh(cache_key, fetch_providers)

        return ProvidersListResponse(
            providers=providers_dict,
            count=len(providers_dict),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing TTS providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/asr", response_model=ProvidersListResponse)
async def get_asr_providers(
    online_only: bool = Query(default=False, description="Filter for online providers only"),
    force_refresh: bool = Query(default=False, description="Force cache refresh"),
):
    """
    List all ASR providers.

    Returns dict of ASR providers with capabilities, status, and metadata.
    Default provider: whisper.ailabsafrica.com (faster_whisper_large)
    """
    try:
        _ensure_registry_initialized()
        registry = get_global_registry()

        def fetch_providers():
            providers = registry.get_asr_providers()
            result = {}
            for p in providers:
                if online_only and p.status != ProviderStatus.ONLINE:
                    continue
                provider_dict = _provider_to_dict(p)
                # Mark default provider
                if p.id in ["faster_whisper_large", "whisper_large_v3"]:
                    provider_dict["is_default"] = True
                result[p.id] = provider_dict
            return result

        cache_key = f"asr_{online_only}"
        if force_refresh and cache_key in _provider_cache:
            del _provider_cache[cache_key]

        providers_dict = _get_cached_or_fresh(cache_key, fetch_providers)

        return ProvidersListResponse(
            providers=providers_dict,
            count=len(providers_dict),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing ASR providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm", response_model=ProvidersListResponse)
async def get_llm_providers(
    online_only: bool = Query(default=False, description="Filter for online providers only"),
    force_refresh: bool = Query(default=False, description="Force cache refresh"),
):
    """
    List all LLM providers.

    Returns dict of LLM providers with capabilities, pricing, and metadata.
    Default provider: gemini-2.5-flash
    """
    try:
        _ensure_registry_initialized()
        registry = get_global_registry()

        def fetch_providers():
            providers = registry.get_llm_providers()
            result = {}
            for p in providers:
                if online_only and p.status != ProviderStatus.ONLINE:
                    continue
                provider_dict = _provider_to_dict(p)
                # Mark default provider
                if p.id == "gemini-2.5-flash":
                    provider_dict["is_default"] = True
                result[p.id] = provider_dict
            return result

        cache_key = f"llm_{online_only}"
        if force_refresh and cache_key in _provider_cache:
            del _provider_cache[cache_key]

        providers_dict = _get_cached_or_fresh(cache_key, fetch_providers)

        return ProvidersListResponse(
            providers=providers_dict,
            count=len(providers_dict),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing LLM providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=AllProvidersResponse)
async def get_all_providers(
    online_only: bool = Query(default=False, description="Filter for online providers only"),
    force_refresh: bool = Query(default=False, description="Force cache refresh"),
):
    """
    List all providers grouped by type.

    Returns TTS, ASR, and LLM providers in a single response.
    Useful for initial app load to get all provider options.
    """
    try:
        _ensure_registry_initialized()
        registry = get_global_registry()

        def fetch_all():
            tts = {}
            asr = {}
            llm = {}

            for p in registry.get_tts_providers():
                if online_only and p.status != ProviderStatus.ONLINE:
                    continue
                tts[p.id] = _provider_to_dict(p)

            for p in registry.get_asr_providers():
                if online_only and p.status != ProviderStatus.ONLINE:
                    continue
                provider_dict = _provider_to_dict(p)
                if p.id in ["faster_whisper_large", "whisper_large_v3"]:
                    provider_dict["is_default"] = True
                asr[p.id] = provider_dict

            for p in registry.get_llm_providers():
                if online_only and p.status != ProviderStatus.ONLINE:
                    continue
                provider_dict = _provider_to_dict(p)
                if p.id == "gemini-2.5-flash":
                    provider_dict["is_default"] = True
                llm[p.id] = provider_dict

            return {
                "tts": tts,
                "asr": asr,
                "llm": llm,
            }

        cache_key = f"all_{online_only}"
        if force_refresh and cache_key in _provider_cache:
            del _provider_cache[cache_key]

        data = _get_cached_or_fresh(cache_key, fetch_all)

        return AllProvidersResponse(
            tts=data["tts"],
            asr=data["asr"],
            llm=data["llm"],
            stats={
                "tts_count": len(data["tts"]),
                "asr_count": len(data["asr"]),
                "llm_count": len(data["llm"]),
                "total": len(data["tts"]) + len(data["asr"]) + len(data["llm"]),
            },
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing all providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider_type}/{provider_id}")
async def get_provider_details(
    provider_type: str,
    provider_id: str,
):
    """
    Get details for a specific provider.

    Args:
        provider_type: Provider type (tts, asr, llm)
        provider_id: Provider identifier

    Returns:
        Provider details with capabilities and metadata
    """
    try:
        _ensure_registry_initialized()
        registry = get_global_registry()

        provider = registry.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=404,
                detail=f"Provider not found: {provider_id}"
            )

        # Verify provider type matches
        provider_type_enum = ProviderType(provider_type.lower())
        if provider.provider_type != provider_type_enum:
            raise HTTPException(
                status_code=400,
                detail=f"Provider {provider_id} is not of type {provider_type}"
            )

        return _provider_to_dict(provider)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider type: {provider_type}"
        )
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_providers_health():
    """
    Health check for all providers.

    Returns summary of provider status by type.
    This is a lightweight check using registry status, not live health checks.
    For live health checks, use the individual service health endpoints.
    """
    try:
        _ensure_registry_initialized()
        registry = get_global_registry()

        stats = registry.get_stats()

        return {
            "status": "healthy",
            "total_providers": stats["total"],
            "by_type": stats["by_type"],
            "by_status": stats["by_status"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking providers health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.post("/refresh-cache")
async def refresh_provider_cache():
    """
    Force refresh the provider cache.

    Clears all cached provider data, causing next requests to fetch fresh data.
    """
    global _provider_cache
    _provider_cache.clear()

    return {
        "status": "success",
        "message": "Provider cache cleared",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Initialization Helper
# ============================================================================

def initialize_providers():
    """
    Initialize providers on app startup.

    Call this from your app's startup event:

        @app.on_event("startup")
        async def startup():
            from apps.shared.routes.provider_routes import initialize_providers
            initialize_providers()
    """
    _ensure_registry_initialized()
    logger.info("Provider routes initialized")

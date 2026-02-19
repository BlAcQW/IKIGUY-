"""
TTS Provider Routes for StudyFlow

⚠️ DEPRECATED (2025-11-23) ⚠️

This file is deprecated and no longer used.
StudyFlow now uses unified TTS routes from @shared/routes/tts_routes.py at /api/tts

Migration:
- Old: GET /api/v1/tts/providers
- New: GET /api/tts/providers

- Old: GET /api/v1/tts/providers/{provider_id}
- New: GET /api/tts/providers/{provider_id}

See: @shared/tts/MIGRATION.md for full migration guide

Author: KasaAI
Created: 2025-11-16
Deprecated: 2025-11-23
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
import logging
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.tts.config import get_available_providers
from app.core.auth import get_current_user_with_org

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["TTS"])


@router.get("/providers")
async def list_tts_providers(
    user_context: dict = Depends(get_current_user_with_org)
) -> Dict[str, Any]:
    """
    List all available TTS providers with their capabilities.

    Returns information about TTS providers that can be used for
    voice generation across StudyFlow features (tutoring, pronunciation, etc.).

    Returns:
        Dict with providers list and metadata
    """
    try:
        # Get all available TTS providers from shared library
        providers = get_available_providers()

        # Format providers for frontend consumption
        provider_list = []
        for provider_id, provider_info in providers.items():
            provider_list.append({
                "id": provider_id,
                "name": provider_info.get("name", provider_id),
                "description": provider_info.get("description", ""),
                "voices": provider_info.get("voices", []),
                "languages": provider_info.get("languages", []),
                "features": provider_info.get("features", {}),
                "is_available": provider_info.get("is_available", True),
                "quality": provider_info.get("quality", "medium"),
                "latency": provider_info.get("latency", "medium")
            })

        return {
            "providers": provider_list,
            "total": len(provider_list),
            "default_provider": "openai"  # Can be made configurable
        }

    except Exception as e:
        logger.error(f"Failed to list TTS providers: {str(e)}", exc_info=True)
        # Return minimal fallback list instead of error
        return {
            "providers": [{
                "id": "openai",
                "name": "OpenAI TTS",
                "description": "OpenAI Text-to-Speech API",
                "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "languages": ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ar", "zh", "ja", "hi"],
                "features": {"streaming": True, "multilingual": True},
                "is_available": True,
                "quality": "high",
                "latency": "low"
            }],
            "total": 1,
            "default_provider": "openai",
            "error": str(e)
        }


@router.get("/providers/{provider_id}")
async def get_tts_provider_details(
    provider_id: str,
    user_context: dict = Depends(get_current_user_with_org)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific TTS provider.

    Args:
        provider_id: The provider ID (e.g., 'openai', 'elevenlabs', 'cartesia')

    Returns:
        Detailed provider information
    """
    try:
        providers = get_available_providers()

        if provider_id not in providers:
            return {
                "error": f"Provider '{provider_id}' not found",
                "available_providers": list(providers.keys())
            }

        provider_info = providers[provider_id]

        return {
            "id": provider_id,
            "name": provider_info.get("name", provider_id),
            "description": provider_info.get("description", ""),
            "voices": provider_info.get("voices", []),
            "languages": provider_info.get("languages", []),
            "features": provider_info.get("features", {}),
            "is_available": provider_info.get("is_available", True),
            "quality": provider_info.get("quality", "medium"),
            "latency": provider_info.get("latency", "medium"),
            "pricing": provider_info.get("pricing", {}),
            "limits": provider_info.get("limits", {})
        }

    except Exception as e:
        logger.error(f"Failed to get provider details for {provider_id}: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "provider_id": provider_id
        }

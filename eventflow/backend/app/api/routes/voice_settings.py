"""
Voice Settings API Routes for EventFlow

Provides TTS/ASR provider information for voice configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging
import sys

sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.integration.ai_services.provider_registry import (
    AIProviderRegistry,
    get_default_asr_providers_config,
    get_default_tts_providers_config,
    ProviderType
)
from app.core.auth import get_current_user_with_org

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-settings", tags=["Voice Settings"])


@router.get("/providers")
async def get_available_providers(
    user_context: dict = Depends(get_current_user_with_org)
):
    """Get available TTS and ASR providers."""
    try:
        # Get providers from registry and load default configs
        registry = AIProviderRegistry()
        registry.register_providers_from_config(
            get_default_asr_providers_config(),
            provider_type=ProviderType.ASR
        )
        registry.register_providers_from_config(
            get_default_tts_providers_config(),
            provider_type=ProviderType.TTS
        )

        # Get ASR providers
        asr_providers_list = registry.get_asr_providers()
        asr_providers = [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": "online"
            }
            for p in asr_providers_list
        ]

        # Get TTS providers
        tts_providers_list = registry.get_tts_providers()
        tts_providers = [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": "online",
                "deployment": "cloud",
                "languages": p.languages,
                "languageList": p.languageList,
                "capabilities": p.capabilities.dict() if hasattr(p.capabilities, 'dict') else p.capabilities,
                "description": p.description,
                "icon": p.icon
            }
            for p in tts_providers_list
        ]

        logger.info(f"Returning {len(asr_providers)} ASR providers and {len(tts_providers)} TTS providers")

        # Convert TTS providers array to dict keyed by ID for frontend compatibility
        tts_providers_dict = {p["id"]: p for p in tts_providers}

        from datetime import datetime
        return {
            "asr_providers": asr_providers,
            "tts_providers": tts_providers,
            "providers": tts_providers_dict,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )

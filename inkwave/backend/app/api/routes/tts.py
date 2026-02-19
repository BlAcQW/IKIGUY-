"""
TTS Providers API Routes for InkWave

Provides TTS provider information for voice configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging
import sys
from pathlib import Path

# Add project root to path for shared imports (consistent with main.py)
# From /opt/kasaai/apps/inkwave/backend/app/api/routes/ -> /opt/kasaai/
project_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.shared.integration.ai_services.provider_registry import (
    AIProviderRegistry,
    get_default_tts_providers_config,
    ProviderType
)
from apps.shared.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["TTS"])


@router.get("/providers")
async def get_tts_providers(
    current_user: dict = Depends(get_current_user)
):
    """Get available TTS providers."""
    try:
        # Get providers from registry and load default configs
        registry = AIProviderRegistry()
        registry.register_providers_from_config(
            get_default_tts_providers_config(),
            provider_type=ProviderType.TTS
        )
        
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
        
        # Convert TTS providers array to dict keyed by ID for frontend compatibility
        tts_providers_dict = {p["id"]: p for p in tts_providers}
        
        from datetime import datetime
        return {
            "providers": tts_providers_dict,  # For useComprehensiveTTS hook
            "tts_providers": tts_providers,  # Array format
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get TTS providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve TTS providers: {str(e)}"
        )

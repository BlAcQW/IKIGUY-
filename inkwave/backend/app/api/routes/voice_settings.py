"""
Voice Settings API Routes for InkWave

Provides endpoints for managing user voice preferences (TTS, ASR, LLM settings).

Author: KasaAI
Date: 2025-11-03
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from typing import Dict, Any, Optional
import sys
import os

# Add shared services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../shared'))

from apps.shared.services.voice_settings_service import (
    VoiceSettingsService,
    VoiceSettings
)
from app.core.database import get_db
from apps.shared.dependencies.auth import get_current_user

router = APIRouter(prefix="/voice-settings", tags=["voice-settings"])


@router.get("/my-settings", response_model=Dict[str, Any])
async def get_my_voice_settings(
    request: Request,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Get current user's voice settings.

    If user is not authenticated, returns default system settings.

    Returns:
        Voice settings including TTS, ASR, and LLM preferences
    """
    try:
        # Try to get authenticated user
        current_user = None
        if authorization:
            try:
                current_user = await get_current_user(request, authorization)
            except:
                pass  # Not authenticated, will return defaults

        if current_user:
            # Return user-specific settings
            service = VoiceSettingsService(db)
            user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.get("user_id")
            org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else current_user.get("organization_id", "default")

            settings = await service.get_settings(user_id, org_id)
            return settings.dict()
        else:
            # Return default system settings for unauthenticated users
            return {
                "tts": {
                    "default_provider": "coqui_xtts",
                    "default_voice": None,
                    "speed": 1.0,
                    "pitch": 0.0
                },
                "asr": {
                    "default_provider": "faster_whisper_large",
                    "language": "en",
                    "task": "transcribe"
                },
                "llm": {
                    "default_model": "llama3.2",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "voices": {
                    "favorite_voices": [],
                    "custom_voices": []
                }
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load voice settings: {str(e)}"
        )


@router.put("/my-settings", response_model=Dict[str, Any])
async def update_my_voice_settings(
    request: Request,
    updates: Dict[str, Any],
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Update current user's voice settings.

    Requires authentication.

    Args:
        updates: Partial update of settings (tts, asr, llm, voices)

    Returns:
        Updated voice settings
    """
    try:
        # Authentication required for updates
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to update settings"
            )

        current_user = await get_current_user(request, authorization)

        service = VoiceSettingsService(db)
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.get("user_id")
        org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else current_user.get("organization_id", "default")

        updated_settings = await service.update_settings(user_id, org_id, updates)

        return updated_settings.dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update voice settings: {str(e)}"
        )


@router.get("/org-defaults", response_model=Dict[str, Any])
async def get_organization_defaults(
    request: Request,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Get organization default voice settings.

    If user is not authenticated, returns system defaults.

    Returns:
        Organization default settings or system defaults
    """
    try:
        # Try to get authenticated user
        current_user = None
        if authorization:
            try:
                current_user = await get_current_user(request, authorization)
            except:
                pass  # Not authenticated, will return system defaults

        if current_user:
            service = VoiceSettingsService(db)
            org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else current_user.get("organization_id", "default")
            org_defaults = await service.get_organization_defaults(org_id)

            if org_defaults:
                return org_defaults.dict()

        # Return system defaults if no org defaults exist or user not authenticated
        return {
            "tts": {
                "default_provider": "coqui_xtts",
                "default_voice": None,
                "speed": 1.0,
                "pitch": 0.0
            },
            "asr": {
                "default_provider": "whisper_local",
                "language": "en",
                "task": "transcribe"
            },
            "llm": {
                "default_model": "llama3.2",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "voices": {
                "favorite_voices": [],
                "custom_voices": []
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load organization defaults: {str(e)}"
        )


@router.put("/org-defaults", response_model=Dict[str, Any])
async def set_organization_defaults(
    request: Request,
    settings: Dict[str, Any],
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Set organization default voice settings.

    Only organization admins can update org defaults.

    Args:
        settings: Default settings for the organization

    Returns:
        Updated organization defaults
    """
    try:
        # Authentication required
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        current_user = await get_current_user(request, authorization)

        # Check if user is admin
        is_admin = (hasattr(current_user, 'is_admin') and current_user.is_admin) or \
                   (hasattr(current_user, 'role') and current_user.role == "admin") or \
                   (hasattr(current_user, 'is_universal_admin') and current_user.is_universal_admin) or \
                   current_user.get("is_admin", False) or \
                   current_user.get("role") == "admin" or \
                   current_user.get("is_universal_admin", False)

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization admins can update default settings"
            )

        service = VoiceSettingsService(db)
        org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else current_user.get("organization_id", "default")

        updated_defaults = await service.set_organization_defaults(org_id, settings)

        return updated_defaults.dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization defaults: {str(e)}"
        )


@router.delete("/my-settings")
async def delete_my_voice_settings(
    request: Request,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Delete current user's voice settings (revert to defaults).

    Requires authentication.

    Returns:
        Success message
    """
    try:
        # Authentication required
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        current_user = await get_current_user(request, authorization)

        service = VoiceSettingsService(db)
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.get("user_id")
        org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else current_user.get("organization_id", "default")

        deleted = await service.delete_settings(user_id, org_id)

        if deleted:
            return {"message": "Voice settings deleted successfully"}
        else:
            return {"message": "No settings found to delete"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete voice settings: {str(e)}"
        )


@router.get("/providers")
async def get_available_providers(
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Get available voice providers (ASR, TTS, and LLM) with capabilities.

    Returns current provider availability and capabilities for all voice services.

    Returns:
        Dict with ASR, TTS, and LLM provider information
    """
    try:
        import logging
        logger = logging.getLogger(__name__)

        # Import provider registry
        from apps.shared.integration.ai_services.provider_registry import (
            AIProviderRegistry,
            get_default_asr_providers_config,
            get_default_tts_providers_config,
            get_default_llm_providers_config,
            ProviderType
        )

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
        registry.register_providers_from_config(
            get_default_llm_providers_config(),
            provider_type=ProviderType.LLM
        )

        # Get ASR providers
        asr_providers_list = registry.get_asr_providers()
        asr_providers = [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": "online",
                "languages": getattr(p, 'languages', 0),
                "languageList": getattr(p, 'languageList', []),
                "capabilities": p.capabilities.dict() if hasattr(p.capabilities, 'dict') else p.capabilities,
                "description": getattr(p, 'description', ''),
                "icon": getattr(p, 'icon', '🎤'),
                "metadata": getattr(p, 'metadata', {})
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

        # Get LLM providers
        llm_providers_list = registry.get_llm_providers()
        llm_providers = [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": getattr(p, 'status', 'online'),
                "languages": getattr(p, 'languages', 0),
                "languageList": getattr(p, 'languageList', []),
                "capabilities": p.capabilities.dict() if hasattr(p.capabilities, 'dict') else p.capabilities,
                "description": getattr(p, 'description', ''),
                "icon": getattr(p, 'icon', '🤖'),
                "metadata": getattr(p, 'metadata', {})
            }
            for p in llm_providers_list
        ]

        logger.info(
            f"Returning {len(asr_providers)} ASR, {len(tts_providers)} TTS, "
            f"and {len(llm_providers)} LLM providers"
        )

        # Convert to dicts keyed by ID for frontend compatibility
        tts_providers_dict = {p["id"]: p for p in tts_providers}
        llm_providers_dict = {p["id"]: p for p in llm_providers}

        from datetime import datetime
        return {
            "asr_providers": asr_providers,
            "tts_providers": tts_providers,
            "llm_providers": llm_providers,
            "providers": tts_providers_dict,
            "llm_providers_dict": llm_providers_dict,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )


@router.get("/org-statistics", response_model=Dict[str, Any])
async def get_organization_statistics(
    request: Request,
    authorization: Optional[str] = Header(None),
    db=Depends(get_db)
):
    """
    Get statistics about voice settings usage for the organization.

    Only available to organization admins.

    Returns:
        Statistics including provider usage, user count, etc.
    """
    try:
        # Authentication required
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        current_user = await get_current_user(request, authorization)

        # Check if user is admin
        is_admin = (hasattr(current_user, 'is_admin') and current_user.is_admin) or \
                   (hasattr(current_user, 'role') and current_user.role == "admin") or \
                   (hasattr(current_user, 'is_universal_admin') and current_user.is_universal_admin) or \
                   current_user.get("is_admin", False) or \
                   current_user.get("role") == "admin" or \
                   current_user.get("is_universal_admin", False)

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization admins can view statistics"
            )

        service = VoiceSettingsService(db)
        org_id = current_user.organization_id if hasattr(current_user, 'organization_id') else current_user.get("organization_id", "default")

        stats = await service.get_statistics(org_id)

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load statistics: {str(e)}"
        )

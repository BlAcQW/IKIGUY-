"""
Voice Settings API Routes for StudyFlow

Enhanced voice preferences management with organization context and
integration with voice tutoring services.

Features:
- User-specific voice settings (TTS, ASR, LLM)
- Organization-wide defaults
- Provider availability checking
- Settings presets for common use cases
- Statistics and analytics (admin only)

Author: KasaAI
Updated: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.voice_settings_service import (
    VoiceSettingsService,
    VoiceSettings,
    TTSSettings,
    ASRSettings,
    LLMSettings
)
from app.core.database import MongoDB
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole
from app.services.voice_tutoring_service import VoiceTutoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-settings", tags=["Voice Settings"])

# Only admins can set organization defaults
require_admin = OrganizationRoleChecker([UserRole.ADMIN])


# ============================================================================
# Helper Functions
# ============================================================================

def get_database():
    """Get MongoDB database instance."""
    return MongoDB.get_database()


def get_voice_settings_service() -> VoiceSettingsService:
    """Get voice settings service instance."""
    return VoiceSettingsService(get_database())


# ============================================================================
# Request/Response Models
# ============================================================================

class VoiceSettingsUpdate(BaseModel):
    """Model for updating voice settings."""
    tts: Optional[Dict[str, Any]] = None
    asr: Optional[Dict[str, Any]] = None
    llm: Optional[Dict[str, Any]] = None
    voices: Optional[Dict[str, Any]] = None


class PresetSettings(BaseModel):
    """Voice settings preset."""
    name: str
    description: str
    settings: Dict[str, Any]


# ============================================================================
# User Settings Endpoints
# ============================================================================

@router.get("/me", response_model=Dict[str, Any])
async def get_my_voice_settings(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get current user's voice settings with organization context.

    Returns user-specific settings, falling back to organization defaults.

    Args:
        user_context: User context with organization info

    Returns:
        Complete voice settings (TTS, ASR, LLM, voices)
    """
    try:
        service = get_voice_settings_service()
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        settings = await service.get_settings(user_id, organization_id)

        logger.info(f"Retrieved voice settings for user {user_id}")
        return settings.dict()

    except Exception as e:
        logger.error(f"Failed to load voice settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load voice settings: {str(e)}"
        )


@router.put("/me", response_model=Dict[str, Any])
async def update_my_voice_settings(
    updates: VoiceSettingsUpdate,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Update current user's voice settings.

    Performs partial update - only updates provided fields.

    Args:
        updates: Settings to update (tts, asr, llm, voices)
        user_context: User context with organization info

    Returns:
        Updated voice settings

    Example:
        {
            "tts": {
                "default_provider": "coqui_xtts",
                "speed": 0.9
            },
            "asr": {
                "language": "en"
            }
        }
    """
    try:
        service = get_voice_settings_service()
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        # Convert to dict, excluding None values
        update_dict = updates.dict(exclude_none=True)

        updated_settings = await service.update_settings(
            user_id,
            organization_id,
            update_dict
        )

        logger.info(f"User {user_id} updated voice settings")
        return updated_settings.dict()

    except Exception as e:
        logger.error(f"Failed to update voice settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update voice settings: {str(e)}"
        )


# Alias endpoints for backward compatibility with shared frontend components
@router.get("/my-settings", response_model=Dict[str, Any])
async def get_my_settings_alias(user_context: dict = Depends(get_current_user_with_org)):
    """Alias for /me endpoint - for backward compatibility."""
    return await get_my_voice_settings(user_context)


@router.put("/my-settings", response_model=Dict[str, Any])
async def update_my_settings_alias(
    updates: VoiceSettingsUpdate,
    user_context: dict = Depends(get_current_user_with_org)
):
    """Alias for /me endpoint - for backward compatibility."""
    return await update_my_voice_settings(updates, user_context)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def reset_my_settings(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Reset user's voice settings to organization defaults.

    Deletes user's custom settings. Future requests will return org defaults.

    Args:
        user_context: User context with organization info
    """
    try:
        service = get_voice_settings_service()
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        await service.delete_settings(user_id, organization_id)

        logger.info(f"User {user_id} reset voice settings")
        return None

    except Exception as e:
        logger.error(f"Failed to reset settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset settings: {str(e)}"
        )


# ============================================================================
# Organization Defaults Endpoints
# ============================================================================

@router.get("/org-defaults", response_model=Dict[str, Any])
async def get_organization_defaults(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get organization-wide default voice settings.

    These are the fallback settings for users who haven't customized theirs.

    Args:
        user_context: User context with organization info

    Returns:
        Organization default settings or None
    """
    try:
        service = get_voice_settings_service()
        organization_id = user_context["organization_id"]

        defaults = await service.get_organization_defaults(organization_id)

        if defaults:
            return defaults.dict()
        else:
            return {"message": "No organization defaults set"}

    except Exception as e:
        logger.error(f"Failed to get org defaults: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization defaults: {str(e)}"
        )


@router.put("/org-defaults", response_model=Dict[str, Any])
async def set_organization_defaults(
    settings: VoiceSettingsUpdate,
    user_context: dict = Depends(require_admin)
):
    """
    Set organization-wide default voice settings.

    Only admins can set organization defaults. These become the default
    for all users in the organization who haven't customized their settings.

    Args:
        settings: Default settings to apply
        user_context: Admin user context

    Returns:
        Updated organization defaults
    """
    try:
        service = get_voice_settings_service()
        organization_id = user_context["organization_id"]
        user_id = user_context["user_id"]

        # Convert to dict
        settings_dict = settings.dict(exclude_none=True)

        org_defaults = await service.set_organization_defaults(
            organization_id,
            settings_dict
        )

        logger.info(f"Admin {user_id} set org defaults for {organization_id}")
        return org_defaults.dict()

    except Exception as e:
        logger.error(f"Failed to set org defaults: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set organization defaults: {str(e)}"
        )


# ============================================================================
# Provider and Capabilities Endpoints
# ============================================================================

@router.get("/providers")
async def get_available_providers(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get available voice providers (ASR, TTS, and LLM) with health status.

    Returns current provider availability and capabilities for all voice services.

    Args:
        user_context: User context with organization info

    Returns:
        Dict with ASR, TTS, and LLM provider information
    """
    try:
        # Import provider services directly to avoid wallet initialization issues
        sys.path.insert(0, "/opt/kasaai/apps")
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
                "icon": getattr(p, 'icon', '🎤')
            }
            for p in asr_providers_list
        ]

        # Get TTS providers directly from registry
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
            "providers": tts_providers_dict,  # TTS dict for useComprehensiveTTS hook
            "llm_providers_dict": llm_providers_dict,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )


# ============================================================================
# Presets Endpoints
# ============================================================================

@router.get("/presets")
async def get_settings_presets(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get predefined voice settings presets for common use cases.

    Returns recommended settings configurations for different scenarios.

    Args:
        user_context: User context with organization info

    Returns:
        List of preset configurations
    """
    # All presets now use self-hosted Whisper at whisper.ailabsafrica.com
    presets = [
        PresetSettings(
            name="Fast Learning",
            description="Optimized for quick responses with lower quality",
            settings={
                "tts": {
                    "default_provider": "coqui_xtts",
                    "speed": 1.2
                },
                "asr": {
                    "default_provider": "whisper_large_v3",
                    "language": "en"
                },
                "llm": {
                    "default_model": "gemini-2.5-flash",
                    "temperature": 0.1,
                    "max_tokens": 300
                }
            }
        ),
        PresetSettings(
            name="High Quality",
            description="Best quality for detailed learning sessions",
            settings={
                "tts": {
                    "default_provider": "coqui_xtts",
                    "speed": 0.9
                },
                "asr": {
                    "default_provider": "whisper_large_v3",
                    "language": "en"
                },
                "llm": {
                    "default_model": "gemini-2.5-flash",
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            }
        ),
        PresetSettings(
            name="Language Learning",
            description="Slower speech for language practice",
            settings={
                "tts": {
                    "default_provider": "coqui_xtts",
                    "speed": 0.7
                },
                "asr": {
                    "default_provider": "whisper_large_v3",
                    "language": "auto"
                },
                "llm": {
                    "default_model": "gemini-2.5-flash",
                    "temperature": 0.2,
                    "max_tokens": 400
                }
            }
        ),
        PresetSettings(
            name="Interactive Tutoring",
            description="Balanced settings for conversational learning",
            settings={
                "tts": {
                    "default_provider": "coqui_xtts",
                    "speed": 0.9
                },
                "asr": {
                    "default_provider": "whisper_large_v3",
                    "language": "en"
                },
                "llm": {
                    "default_model": "gemini-2.5-flash",
                    "temperature": 0.5,
                    "max_tokens": 350
                }
            }
        )
    ]

    return {
        "presets": [preset.dict() for preset in presets],
        "total": len(presets)
    }


@router.post("/apply-preset")
async def apply_preset(
    preset_name: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Apply a predefined preset to user's voice settings.

    Args:
        preset_name: Name of preset to apply
        user_context: User context with organization info

    Returns:
        Updated voice settings
    """
    try:
        # Get presets
        presets_response = await get_settings_presets(user_context)
        presets = presets_response["presets"]

        # Find requested preset
        preset = next((p for p in presets if p["name"] == preset_name), None)

        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{preset_name}' not found"
            )

        # Apply preset settings
        service = get_voice_settings_service()
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        updated_settings = await service.update_settings(
            user_id,
            organization_id,
            preset["settings"]
        )

        logger.info(f"User {user_id} applied preset '{preset_name}'")
        return {
            "message": f"Applied preset: {preset_name}",
            "settings": updated_settings.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply preset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply preset: {str(e)}"
        )


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/statistics")
async def get_organization_statistics(
    user_context: dict = Depends(require_admin)
):
    """
    Get statistics about voice settings usage for the organization.

    Only admins can view organization-wide statistics.

    Args:
        user_context: Admin user context

    Returns:
        Usage statistics (total users, popular providers, etc.)
    """
    try:
        service = get_voice_settings_service()
        organization_id = user_context["organization_id"]

        stats = await service.get_statistics(organization_id)

        return stats

    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/all-users")
async def get_all_user_settings(
    limit: int = 50,
    skip: int = 0,
    user_context: dict = Depends(require_admin)
):
    """
    Get voice settings for all users in the organization.

    Only admins can view all user settings. Useful for support and analytics.

    Args:
        limit: Maximum results to return
        skip: Number of results to skip (pagination)
        user_context: Admin user context

    Returns:
        List of user voice settings
    """
    try:
        service = get_voice_settings_service()
        organization_id = user_context["organization_id"]

        all_settings = await service.get_all_settings_for_org(
            organization_id,
            limit=limit,
            skip=skip
        )

        return {
            "settings": [s.dict() for s in all_settings],
            "total": len(all_settings),
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        logger.error(f"Failed to get all user settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user settings: {str(e)}"
        )

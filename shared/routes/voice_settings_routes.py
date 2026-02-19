"""
Unified Voice Settings Routes

Provides standardized voice settings endpoints for all backend applications.
Manages user preferences for TTS, ASR, and LLM across apps.

Mount in FastAPI app:
    from apps.shared.routes.voice_settings_routes import create_voice_settings_router

    voice_settings_router = create_voice_settings_router(
        get_current_user_func=get_current_user,
        get_database_func=get_database
    )
    app.include_router(voice_settings_router, prefix="/api/voice-settings", tags=["Voice Settings"])

Endpoints:
    GET    /me                - Get current user's voice settings
    PUT    /me                - Update current user's voice settings
    DELETE /me                - Reset user settings to defaults
    GET    /org-defaults      - Get organization defaults
    PUT    /org-defaults      - Set organization defaults (admin only)
    GET    /presets           - Get recommended presets
    GET    /stats             - Get usage statistics (admin only)

Author: KasaAI Team
Date: 2025-11-26
"""

from typing import Optional, Dict, Any, Callable, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import logging

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from shared.services.voice_settings_service import (
    VoiceSettingsService,
    VoiceSettings,
    TTSSettings,
    ASRSettings,
    LLMSettings,
    VoicePreferences,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class TTSSettingsUpdate(BaseModel):
    """TTS settings update model."""
    default_provider: Optional[str] = Field(
        None, description="Default TTS provider ID (e.g., 'coqui_xtts', 'f5tts')"
    )
    default_voice: Optional[str] = Field(
        None, description="Default voice ID"
    )
    speed: Optional[float] = Field(
        None, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)"
    )
    pitch: Optional[float] = Field(
        None, ge=-1.0, le=1.0, description="Pitch adjustment (-1.0 to 1.0)"
    )


class ASRSettingsUpdate(BaseModel):
    """ASR settings update model."""
    default_provider: Optional[str] = Field(
        None, description="Default ASR provider ID (e.g., 'faster_whisper_large')"
    )
    language: Optional[str] = Field(
        None, description="Default language code (e.g., 'en', 'fr', 'tw')"
    )
    task: Optional[str] = Field(
        None, description="Default task: 'transcribe' or 'translate'"
    )


class LLMSettingsUpdate(BaseModel):
    """LLM settings update model."""
    default_model: Optional[str] = Field(
        None, description="Default LLM model ID (e.g., 'gemini-2.5-flash')"
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Default temperature (0.0-2.0)"
    )
    max_tokens: Optional[int] = Field(
        None, ge=1, le=100000, description="Default max tokens"
    )


class VoicePreferencesUpdate(BaseModel):
    """Voice preferences update model."""
    favorite_voices: Optional[List[str]] = Field(
        None, description="List of favorite voice IDs"
    )
    custom_voices: Optional[List[str]] = Field(
        None, description="List of custom/cloned voice IDs"
    )


class VoiceSettingsUpdate(BaseModel):
    """Voice settings update request."""
    tts: Optional[TTSSettingsUpdate] = None
    asr: Optional[ASRSettingsUpdate] = None
    llm: Optional[LLMSettingsUpdate] = None
    voices: Optional[VoicePreferencesUpdate] = None


class VoiceSettingsResponse(BaseModel):
    """Voice settings response model."""
    user_id: str
    organization_id: str
    tts: Dict[str, Any]
    asr: Dict[str, Any]
    llm: Dict[str, Any]
    voices: Dict[str, Any]
    created_at: str
    updated_at: str


class OrgDefaultsRequest(BaseModel):
    """Organization defaults request."""
    tts: Optional[TTSSettingsUpdate] = None
    asr: Optional[ASRSettingsUpdate] = None
    llm: Optional[LLMSettingsUpdate] = None


class PresetResponse(BaseModel):
    """Voice preset response."""
    id: str
    name: str
    description: str
    tts: Dict[str, Any]
    asr: Dict[str, Any]
    llm: Dict[str, Any]


# ============================================================================
# Predefined Presets
# ============================================================================

VOICE_PRESETS = [
    {
        "id": "default",
        "name": "Default",
        "description": "Balanced settings for general use",
        "tts": {"default_provider": "kokoro", "speed": 1.0, "pitch": 0.0},
        "asr": {"default_provider": "faster_whisper_large", "language": "en", "task": "transcribe"},
        "llm": {"default_model": "gemini-2.5-flash", "temperature": 0.7, "max_tokens": 2000}
    },
    {
        "id": "fast_response",
        "name": "Fast Response",
        "description": "Optimized for speed with slightly lower quality",
        "tts": {"default_provider": "melotts", "speed": 1.2, "pitch": 0.0},
        "asr": {"default_provider": "groq_whisper_large_v3_turbo", "language": "en", "task": "transcribe"},
        "llm": {"default_model": "gemini-2.0-flash-exp", "temperature": 0.5, "max_tokens": 1000}
    },
    {
        "id": "high_quality",
        "name": "High Quality",
        "description": "Best quality for professional use",
        "tts": {"default_provider": "f5tts", "speed": 1.0, "pitch": 0.0},
        "asr": {"default_provider": "faster_whisper_large", "language": "en", "task": "transcribe"},
        "llm": {"default_model": "gemini-2.5-flash", "temperature": 0.7, "max_tokens": 4000}
    },
    {
        "id": "african_languages",
        "name": "African Languages",
        "description": "Optimized for African language support",
        "tts": {"default_provider": "coqui_xtts", "speed": 1.0, "pitch": 0.0},
        "asr": {"default_provider": "faster_whisper_large", "language": "auto", "task": "transcribe"},
        "llm": {"default_model": "gemini-2.5-flash", "temperature": 0.7, "max_tokens": 2000}
    },
    {
        "id": "cost_effective",
        "name": "Cost Effective",
        "description": "Minimizes costs with self-hosted services",
        "tts": {"default_provider": "kokoro", "speed": 1.0, "pitch": 0.0},
        "asr": {"default_provider": "faster_whisper_large", "language": "en", "task": "transcribe"},
        "llm": {"default_model": "gemini-2.0-flash-exp", "temperature": 0.7, "max_tokens": 1500}
    }
]


# ============================================================================
# Router Factory
# ============================================================================

def create_voice_settings_router(
    get_current_user_func: Callable,
    get_database_func: Callable,
) -> APIRouter:
    """
    Create voice settings router with injected dependencies.

    Args:
        get_current_user_func: Dependency function that returns current user
        get_database_func: Dependency function that returns MongoDB database

    Returns:
        APIRouter with voice settings endpoints

    Usage:
        router = create_voice_settings_router(
            get_current_user_func=get_current_user,
            get_database_func=lambda: MongoDB.get_database()
        )
        app.include_router(router, prefix="/api/voice-settings")
    """
    router = APIRouter()

    async def get_voice_service():
        """Get voice settings service instance."""
        db = get_database_func()
        service = VoiceSettingsService(db)
        return service

    @router.get("/me", response_model=VoiceSettingsResponse)
    async def get_my_settings(
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Get current user's voice settings.

        Returns user's TTS, ASR, and LLM preferences.
        Creates default settings if none exist.
        """
        try:
            service = await get_voice_service()

            user_id = current_user.get("sub") or current_user.get("id") or current_user.get("user_id")
            org_id = current_user.get("organization_id", "default")

            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found in token")

            settings = await service.get_settings(user_id, org_id)

            return VoiceSettingsResponse(
                user_id=settings.user_id,
                organization_id=settings.organization_id,
                tts=settings.tts.dict(),
                asr=settings.asr.dict(),
                llm=settings.llm.dict(),
                voices=settings.voices.dict(),
                created_at=settings.created_at.isoformat(),
                updated_at=settings.updated_at.isoformat(),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting voice settings: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/me", response_model=VoiceSettingsResponse)
    async def update_my_settings(
        updates: VoiceSettingsUpdate,
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Update current user's voice settings.

        Performs partial update - only updates provided fields.
        """
        try:
            service = await get_voice_service()

            user_id = current_user.get("sub") or current_user.get("id") or current_user.get("user_id")
            org_id = current_user.get("organization_id", "default")

            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found in token")

            # Build update dict (exclude None values)
            update_dict = {}
            if updates.tts:
                update_dict["tts"] = {k: v for k, v in updates.tts.dict().items() if v is not None}
            if updates.asr:
                update_dict["asr"] = {k: v for k, v in updates.asr.dict().items() if v is not None}
            if updates.llm:
                update_dict["llm"] = {k: v for k, v in updates.llm.dict().items() if v is not None}
            if updates.voices:
                update_dict["voices"] = {k: v for k, v in updates.voices.dict().items() if v is not None}

            if not update_dict:
                raise HTTPException(status_code=400, detail="No updates provided")

            settings = await service.update_settings(user_id, org_id, update_dict)

            return VoiceSettingsResponse(
                user_id=settings.user_id,
                organization_id=settings.organization_id,
                tts=settings.tts.dict(),
                asr=settings.asr.dict(),
                llm=settings.llm.dict(),
                voices=settings.voices.dict(),
                created_at=settings.created_at.isoformat(),
                updated_at=settings.updated_at.isoformat(),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating voice settings: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/me")
    async def reset_my_settings(
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Reset user's voice settings to defaults.

        Deletes current settings and re-creates with organization defaults.
        """
        try:
            service = await get_voice_service()

            user_id = current_user.get("sub") or current_user.get("id") or current_user.get("user_id")
            org_id = current_user.get("organization_id", "default")

            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found in token")

            # Delete current settings
            deleted = await service.delete_settings(user_id, org_id)

            # Get fresh settings (will use org defaults)
            settings = await service.get_settings(user_id, org_id)

            return {
                "message": "Settings reset to defaults",
                "user_id": user_id,
                "organization_id": org_id,
                "settings": {
                    "tts": settings.tts.dict(),
                    "asr": settings.asr.dict(),
                    "llm": settings.llm.dict(),
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting voice settings: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/org-defaults")
    async def get_organization_defaults(
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Get organization-wide default settings.

        Returns the default TTS, ASR, and LLM settings for the organization.
        """
        try:
            service = await get_voice_service()

            org_id = current_user.get("organization_id", "default")

            defaults = await service.get_organization_defaults(org_id)

            if defaults:
                return {
                    "organization_id": org_id,
                    "has_defaults": True,
                    "tts": defaults.tts.dict(),
                    "asr": defaults.asr.dict(),
                    "llm": defaults.llm.dict(),
                    "updated_at": defaults.updated_at.isoformat(),
                }
            else:
                # Return system defaults
                return {
                    "organization_id": org_id,
                    "has_defaults": False,
                    "tts": TTSSettings().dict(),
                    "asr": ASRSettings().dict(),
                    "llm": LLMSettings().dict(),
                    "note": "Using system defaults (no org defaults configured)"
                }

        except Exception as e:
            logger.error(f"Error getting org defaults: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/org-defaults")
    async def set_organization_defaults(
        defaults: OrgDefaultsRequest,
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Set organization-wide default settings.

        Requires admin role. New users will inherit these defaults.
        """
        try:
            service = await get_voice_service()

            # Check for admin role
            user_role = current_user.get("role", "user")
            if user_role not in ["admin", "owner", "super_admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="Only administrators can set organization defaults"
                )

            org_id = current_user.get("organization_id", "default")

            # Build settings dict
            settings_dict = {}
            if defaults.tts:
                settings_dict["tts"] = {k: v for k, v in defaults.tts.dict().items() if v is not None}
            if defaults.asr:
                settings_dict["asr"] = {k: v for k, v in defaults.asr.dict().items() if v is not None}
            if defaults.llm:
                settings_dict["llm"] = {k: v for k, v in defaults.llm.dict().items() if v is not None}

            result = await service.set_organization_defaults(org_id, settings_dict)

            return {
                "message": "Organization defaults updated",
                "organization_id": org_id,
                "tts": result.tts.dict(),
                "asr": result.asr.dict(),
                "llm": result.llm.dict(),
                "updated_at": result.updated_at.isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error setting org defaults: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/presets", response_model=List[PresetResponse])
    async def get_presets():
        """
        Get recommended voice presets.

        Returns predefined presets for common use cases.
        No authentication required.
        """
        return VOICE_PRESETS

    @router.post("/apply-preset/{preset_id}", response_model=VoiceSettingsResponse)
    async def apply_preset(
        preset_id: str,
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Apply a preset to current user's settings.

        Overwrites TTS, ASR, and LLM settings with preset values.
        """
        try:
            # Find preset
            preset = next((p for p in VOICE_PRESETS if p["id"] == preset_id), None)
            if not preset:
                raise HTTPException(
                    status_code=404,
                    detail=f"Preset not found: {preset_id}"
                )

            service = await get_voice_service()

            user_id = current_user.get("sub") or current_user.get("id") or current_user.get("user_id")
            org_id = current_user.get("organization_id", "default")

            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found in token")

            # Apply preset
            update_dict = {
                "tts": preset["tts"],
                "asr": preset["asr"],
                "llm": preset["llm"],
            }

            settings = await service.update_settings(user_id, org_id, update_dict)

            return VoiceSettingsResponse(
                user_id=settings.user_id,
                organization_id=settings.organization_id,
                tts=settings.tts.dict(),
                asr=settings.asr.dict(),
                llm=settings.llm.dict(),
                voices=settings.voices.dict(),
                created_at=settings.created_at.isoformat(),
                updated_at=settings.updated_at.isoformat(),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error applying preset: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats")
    async def get_statistics(
        current_user: dict = Depends(get_current_user_func),
    ):
        """
        Get voice settings usage statistics.

        Requires admin role. Returns provider usage across organization.
        """
        try:
            # Check for admin role
            user_role = current_user.get("role", "user")
            if user_role not in ["admin", "owner", "super_admin"]:
                raise HTTPException(
                    status_code=403,
                    detail="Only administrators can view statistics"
                )

            service = await get_voice_service()
            org_id = current_user.get("organization_id", "default")

            stats = await service.get_statistics(org_id)

            return {
                "organization_id": org_id,
                "total_users_with_settings": stats.get("total_users", 0),
                "tts_providers_in_use": stats.get("tts_providers", []),
                "asr_providers_in_use": stats.get("asr_providers", []),
                "llm_models_in_use": stats.get("llm_models", []),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router


# ============================================================================
# Simple Router (without auth, for testing)
# ============================================================================

def create_simple_voice_settings_router(
    get_database_func: Callable,
) -> APIRouter:
    """
    Create voice settings router without authentication (for testing).

    Uses a fixed test user and organization.
    """
    router = APIRouter()

    async def get_voice_service():
        db = get_database_func()
        return VoiceSettingsService(db)

    @router.get("/presets", response_model=List[PresetResponse])
    async def get_presets():
        """Get recommended voice presets."""
        return VOICE_PRESETS

    @router.get("/test-settings")
    async def get_test_settings():
        """Get settings for test user."""
        try:
            service = await get_voice_service()
            settings = await service.get_settings("test_user", "test_org")
            return {
                "tts": settings.tts.dict(),
                "asr": settings.asr.dict(),
                "llm": settings.llm.dict(),
            }
        except Exception as e:
            return {"error": str(e)}

    return router

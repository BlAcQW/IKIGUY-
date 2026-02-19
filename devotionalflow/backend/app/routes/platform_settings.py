"""
Settings routes for platform configuration (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.models.settings import (
    PlatformSettings,
    PlatformSettingsUpdate,
    PlatformSettingsResponse,
)
from app.models.user import TokenData
from app.services.settings_service import SettingsService
from app.utils.auth import get_current_admin

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=PlatformSettingsResponse)
async def get_platform_settings(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Get current platform settings.

    Requires admin role.

    Returns:
        Current platform settings
    """
    service = SettingsService()
    try:
        settings = await service.get_settings()
        return PlatformSettingsResponse(
            settings=settings,
            last_updated=settings.updated_at,
            last_updated_by=settings.updated_by,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settings: {str(e)}",
        )


@router.patch("", response_model=PlatformSettingsResponse)
async def update_platform_settings(
    settings_update: PlatformSettingsUpdate,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Update platform settings.

    Requires admin role.

    Args:
        settings_update: Settings to update (only provided fields will be updated)

    Returns:
        Updated platform settings
    """
    service = SettingsService()
    try:
        updated_settings = await service.update_settings(
            settings_update, current_user.user_id
        )
        
        # If subscription drip feed settings changed, reschedule the job
        if settings_update.notifications and (
            settings_update.notifications.subscription_drip_feed_time is not None or
            settings_update.notifications.enable_subscription_drip_feed is not None
        ):
            try:
                from app.main import reschedule_drip_feed
                await reschedule_drip_feed()
            except Exception as e:
                # Log but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to reschedule drip feed: {e}")
        
        return PlatformSettingsResponse(
            settings=updated_settings,
            last_updated=updated_settings.updated_at,
            last_updated_by=updated_settings.updated_by,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}",
        )


@router.post("/reset", response_model=PlatformSettingsResponse)
async def reset_to_default_settings(
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Reset all settings to default values.

    Requires admin role.

    WARNING: This action will reset all platform settings to defaults.

    Returns:
        Default platform settings
    """
    service = SettingsService()
    try:
        default_settings = await service.reset_to_defaults(current_user.user_id)
        return PlatformSettingsResponse(
            settings=default_settings,
            last_updated=default_settings.updated_at,
            last_updated_by=default_settings.updated_by,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset settings: {str(e)}",
        )

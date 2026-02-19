"""App settings routes for managing global application configuration."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models import (
    AppSettings, AppSettingsCreate, AppSettingsUpdate,
    AutomationSettings, BrandingSettings
)
from ..services.app_settings_service import app_settings_service
from ..services.organization_service import organization_service
from ..auth import get_current_user_mongo

router = APIRouter(prefix="/api/app-settings", tags=["app-settings"])


def require_universal_admin(user: dict = Depends(get_current_user_mongo)):
    """Require universal admin access for app settings."""
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
    user_email = user.get("email", "")

    if not organization_service.is_universal_admin(user_id, user_email):
        raise HTTPException(
            status_code=403,
            detail="Universal admin access required to manage app settings"
        )
    return user


@router.get("/", response_model=AppSettings)
def get_app_settings():
    """Get current app settings. No authentication required for reading settings."""
    settings = app_settings_service.get_app_settings()
    if not settings:
        # Initialize default settings if none exist
        settings = app_settings_service.initialize_default_settings("system")
    return settings


@router.post("/", response_model=AppSettings)
def create_app_settings(
    settings_data: AppSettingsCreate,
    user: dict = Depends(require_universal_admin)
):
    """Create new app settings (universal admin only)."""
    try:
        user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
        settings = app_settings_service.create_app_settings(settings_data, user_id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/", response_model=AppSettings)
def update_app_settings(
    update_data: AppSettingsUpdate,
    user: dict = Depends(require_universal_admin)
):
    """Update current app settings (universal admin only)."""
    try:
        user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
        settings = app_settings_service.update_app_settings(update_data, user_id)

        if not settings:
            raise HTTPException(status_code=404, detail="No active app settings found")

        return settings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/automation", response_model=AutomationSettings)
def get_automation_settings():
    """Get current automation settings. No authentication required for reading."""
    settings = app_settings_service.get_automation_settings()
    if not settings:
        # Initialize default settings if none exist
        app_settings_service.initialize_default_settings("system")
        settings = app_settings_service.get_automation_settings()
    return settings


@router.put("/automation", response_model=AutomationSettings)
def update_automation_settings(
    automation_settings: AutomationSettings,
    user: dict = Depends(require_universal_admin)
):
    """Update automation settings (universal admin only)."""
    try:
        user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
        updated_settings = app_settings_service.update_automation_settings(automation_settings, user_id)

        if not updated_settings:
            raise HTTPException(status_code=404, detail="Failed to update automation settings")

        return updated_settings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/branding", response_model=BrandingSettings)
def get_branding_settings():
    """Get current branding settings. No authentication required for reading."""
    settings = app_settings_service.get_branding_settings()
    if not settings:
        # Initialize default settings if none exist
        app_settings_service.initialize_default_settings("system")
        settings = app_settings_service.get_branding_settings()
    return settings


@router.put("/branding", response_model=BrandingSettings)
def update_branding_settings(
    branding_settings: BrandingSettings,
    user: dict = Depends(require_universal_admin)
):
    """Update branding settings (universal admin only)."""
    try:
        user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
        updated_settings = app_settings_service.update_branding_settings(branding_settings, user_id)

        if not updated_settings:
            raise HTTPException(status_code=404, detail="Failed to update branding settings")

        return updated_settings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/industries/enabled", response_model=List[str])
def get_enabled_industries():
    """Get list of enabled industries for automation. No authentication required for reading."""
    return app_settings_service.get_enabled_industries()


@router.get("/industries/available", response_model=List[str])
def get_available_industries():
    """Get list of all available industry types from database templates."""
    return app_settings_service.get_available_industries()


@router.get("/industries/{industry}/enabled")
def check_industry_enabled(industry: str):
    """Check if a specific industry is enabled for automation."""
    is_enabled = app_settings_service.is_industry_enabled(industry)
    return {
        "industry": industry,
        "enabled": is_enabled
    }


@router.get("/templates/enabled", response_model=List[str])
def get_enabled_templates():
    """Get list of enabled automation template IDs."""
    return app_settings_service.get_enabled_templates()


@router.get("/templates/all")
def get_all_templates():
    """Get all automation templates from database."""
    return app_settings_service.get_automation_templates()


@router.get("/templates/by-industry")
def get_templates_by_industry():
    """Get automation templates grouped by industry."""
    return app_settings_service.get_templates_by_industry()


@router.get("/templates/{template_id}/enabled")
def check_template_enabled(template_id: str):
    """Check if a specific automation template is enabled."""
    is_enabled = app_settings_service.is_template_enabled(template_id)
    return {
        "template_id": template_id,
        "enabled": is_enabled
    }


@router.post("/initialize", response_model=AppSettings)
def initialize_default_settings(
    user: dict = Depends(require_universal_admin)
):
    """Initialize default app settings (universal admin only)."""
    try:
        user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub", "default-account")
        settings = app_settings_service.initialize_default_settings(user_id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
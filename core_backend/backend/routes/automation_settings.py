"""
Automation Settings Routes

API endpoints for managing automation-specific settings including
custom cost rates for billing.

Only accessible by universal_admin users.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from bson import ObjectId

from ..auth import get_current_user_mongo
from ..mongo import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation-settings", tags=["automation-settings"])


class CostSettings(BaseModel):
    """Cost configuration for an automation."""
    rate_per_call: Optional[float] = Field(None, description="Custom rate per call")
    currency: str = Field("GHS", description="Currency code (e.g., GHS, USD)")
    currency_symbol: str = Field("GH₵", description="Currency symbol (e.g., GH₵, $)")


class AutomationSettingsUpdate(BaseModel):
    """Request model for updating automation settings."""
    cost_settings: Optional[CostSettings] = None


class AutomationSettingsResponse(BaseModel):
    """Response model for automation settings."""
    automation_id: str
    cost_settings: Optional[CostSettings] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


def check_universal_admin(user: dict) -> bool:
    """Check if user is a universal admin."""
    return user.get("is_universal_admin", False)


@router.get("/{automation_id}")
async def get_automation_settings(
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get settings for an automation.

    Args:
        automation_id: The automation configuration ID

    Returns:
        Automation settings including cost configuration
    """
    try:
        # Verify user is universal admin
        if not check_universal_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only universal admins can view automation settings"
            )

        # Get database connection
        db = get_database()

        # Get settings from database
        settings = await db.automation_settings.find_one({
            "automation_id": automation_id
        })

        if not settings:
            # Return empty settings if none exist
            return {
                "success": True,
                "data": {
                    "automation_id": automation_id,
                    "cost_settings": None,
                    "updated_at": None,
                    "updated_by": None
                }
            }

        return {
            "success": True,
            "data": {
                "automation_id": automation_id,
                "cost_settings": settings.get("cost_settings"),
                "updated_at": settings.get("updated_at"),
                "updated_by": settings.get("updated_by")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{automation_id}")
async def update_automation_settings(
    automation_id: str,
    settings_update: AutomationSettingsUpdate,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Update settings for an automation.

    Args:
        automation_id: The automation configuration ID
        settings_update: The settings to update

    Returns:
        Updated automation settings
    """
    try:
        # Verify user is universal admin
        if not check_universal_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only universal admins can update automation settings"
            )

        # Get database connection
        db = get_database()

        # Verify automation exists
        automation = await db.automation_configs.find_one({
            "_id": ObjectId(automation_id)
        })

        if not automation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Automation not found"
            )

        # Prepare update data
        update_data = {
            "automation_id": automation_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get("email", current_user.get("_id"))
        }

        if settings_update.cost_settings:
            update_data["cost_settings"] = {
                "rate_per_call": settings_update.cost_settings.rate_per_call,
                "currency": settings_update.cost_settings.currency,
                "currency_symbol": settings_update.cost_settings.currency_symbol
            }

            # Also update the assistant_id for quick lookup in analytics
            assistant_id = None
            if automation.get("deployment_info", {}).get("vapi_assistant_id"):
                assistant_id = automation["deployment_info"]["vapi_assistant_id"]
            elif automation.get("vapi_agent", {}).get("assistant_id"):
                assistant_id = automation["vapi_agent"]["assistant_id"]
            elif automation.get("assistant_id"):
                assistant_id = automation["assistant_id"]

            if assistant_id:
                update_data["assistant_id"] = assistant_id

        # Upsert settings
        await db.automation_settings.update_one(
            {"automation_id": automation_id},
            {"$set": update_data},
            upsert=True
        )

        logger.info(f"Updated automation settings for {automation_id} by {current_user.get('email')}")

        return {
            "success": True,
            "message": "Settings updated successfully",
            "data": {
                "automation_id": automation_id,
                "cost_settings": update_data.get("cost_settings"),
                "updated_at": update_data["updated_at"],
                "updated_by": update_data["updated_by"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating automation settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{automation_id}")
async def delete_automation_settings(
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete settings for an automation (reset to defaults).

    Args:
        automation_id: The automation configuration ID

    Returns:
        Deletion confirmation
    """
    try:
        # Verify user is universal admin
        if not check_universal_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only universal admins can delete automation settings"
            )

        # Get database connection
        db = get_database()

        result = await db.automation_settings.delete_one({
            "automation_id": automation_id
        })

        if result.deleted_count == 0:
            return {
                "success": True,
                "message": "No settings found to delete"
            }

        logger.info(f"Deleted automation settings for {automation_id} by {current_user.get('email')}")

        return {
            "success": True,
            "message": "Settings deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting automation settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

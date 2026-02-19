"""
Member Portal API Routes for ChurchFlow

Handles member self-service operations.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_current_user, require_organization_access
from app.core.database import get_database
from app.services.member_portal_service import get_member_portal_service
from app.schemas.member_portal import (
    MemberProfileResponse,
    UpdateMemberProfileRequest,
    MemberPreferencesResponse,
    UpdatePreferencesRequest,
    MemberActivityResponse,
    MemberDashboardResponse,
    MemberDirectoryResponse,
    MyRegistrationsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Profile Management ====================

@router.get("/profile/me", response_model=MemberProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current member's profile.

    Returns own profile information.
    """
    portal_service = get_member_portal_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    profile = await portal_service.get_member_profile(user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile


@router.patch("/profile/me", response_model=MemberProfileResponse)
async def update_my_profile(
    profile_data: UpdateMemberProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update current member's profile.

    Allows members to edit their own information.
    """
    portal_service = get_member_portal_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    updated_profile = await portal_service.update_member_profile(
        user_id=user_id,
        update_data=profile_data.model_dump(exclude_none=True)
    )

    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )

    logger.info(f"Member {user_id} updated their profile")
    return updated_profile


# ==================== Preferences Management ====================

@router.get("/preferences", response_model=MemberPreferencesResponse)
async def get_my_preferences(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current member's preferences.

    Returns notification and privacy preferences.
    """
    portal_service = get_member_portal_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    preferences = await portal_service.get_member_preferences(user_id)
    return preferences


@router.patch("/preferences", response_model=MemberPreferencesResponse)
async def update_my_preferences(
    preferences_data: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update current member's preferences.

    Allows members to control their notifications and privacy settings.
    """
    portal_service = get_member_portal_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    # Convert to dict, removing None values
    update_data = {}
    if preferences_data.notifications:
        update_data["notifications"] = preferences_data.notifications.model_dump()
    if preferences_data.privacy:
        update_data["privacy"] = preferences_data.privacy.model_dump()
    if preferences_data.language:
        update_data["language"] = preferences_data.language
    if preferences_data.timezone:
        update_data["timezone"] = preferences_data.timezone

    updated_preferences = await portal_service.update_member_preferences(
        user_id=user_id,
        preferences=update_data
    )

    logger.info(f"Member {user_id} updated their preferences")
    return updated_preferences


# ==================== Activity & Dashboard ====================

@router.get("/activity/me", response_model=MemberActivityResponse)
async def get_my_activity(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current member's activity summary.

    Returns conferences attended, donations, volunteer hours, etc.
    """
    portal_service = get_member_portal_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    activity = await portal_service.get_member_activity(user_id)
    return activity


@router.get("/dashboard", response_model=MemberDashboardResponse)
async def get_member_dashboard(
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get complete member dashboard.

    Returns profile, activity, upcoming events, recent donations, and notifications.
    """
    try:
        portal_service = get_member_portal_service(db)
        user_id = current_user.get("id") or current_user.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not found in token"
            )

        dashboard = await portal_service.get_member_dashboard(
            user_id=user_id,
            organization_id=organization_id
        )

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard data not found"
            )

        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching member dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


# ==================== Member Directory ====================

@router.get("/directory", response_model=MemberDirectoryResponse)
async def get_member_directory(
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    Get member directory.

    Returns list of members who opted into directory visibility.
    Respects privacy settings (email/phone only shown if allowed).
    """
    try:
        portal_service = get_member_portal_service(db)

        directory = await portal_service.get_member_directory(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            search=search
        )

        return directory
    except Exception as e:
        logger.error(f"Error fetching member directory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load member directory: {str(e)}"
        )


# ==================== My Registrations ====================

@router.get("/registrations/my", response_model=MyRegistrationsResponse)
async def get_my_registrations(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current member's event registrations.

    Returns upcoming and past conference registrations with attendance stats.
    """
    portal_service = get_member_portal_service(db)
    user_id = current_user.get("id") or current_user.get("sub")

    registrations = await portal_service.get_my_registrations(user_id)
    return registrations


# ==================== Profile Picture Upload ====================

@router.post("/profile/picture")
async def upload_profile_picture(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload profile picture.

    TODO: Implement file upload handling.
    """
    # This would integrate with cloud storage (S3, Cloudinary, etc.)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Profile picture upload not yet implemented"
    )


# ==================== Delete Account ====================

@router.delete("/account")
async def delete_my_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Request account deletion.

    Marks account for deletion (soft delete).
    """
    # This should be a soft delete with admin approval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account deletion requires admin approval. Please contact support."
    )

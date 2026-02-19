"""
Notification API routes for InkWave.

Endpoints:
- GET    /notifications                 - Get user's notifications
- GET    /notifications/unread-count    - Get unread notification count
- PUT    /notifications/{id}/read       - Mark notification as read
- PUT    /notifications/mark-all-read   - Mark all as read
- DELETE /notifications/{id}            - Delete notification
- GET    /notifications/preferences     - Get notification preferences
- PUT    /notifications/preferences     - Update notification preferences
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Header, Request, Query
from pydantic import BaseModel

from app.core.database import get_db
from app.services.notification_service import NotificationService
from apps.shared.dependencies.auth import get_current_user
from app.models.notification import Notification, NotificationPreferences

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================================================
# SCHEMAS
# ============================================================================

class NotificationsResponse(BaseModel):
    """Response with notifications list."""
    notifications: List[Notification]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Response with unread count."""
    unread_count: int


class MarkReadResponse(BaseModel):
    """Response for mark as read."""
    message: str
    marked_count: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=NotificationsResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Max notifications to return"),
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get user's notifications.

    Args:
        unread_only: Filter for unread only
        limit: Maximum results
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's notifications
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    notification_service = NotificationService(db)

    try:
        # Get notifications
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )

        # Get unread count
        unread_count = await notification_service.get_unread_count(user_id)

        return NotificationsResponse(
            notifications=notifications,
            total=len(notifications),
            unread_count=unread_count
        )

    except Exception as e:
        logger.error(f"Failed to get notifications for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get count of unread notifications.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Unread notification count
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    notification_service = NotificationService(db)

    try:
        unread_count = await notification_service.get_unread_count(user_id)

        return UnreadCountResponse(unread_count=unread_count)

    except Exception as e:
        logger.error(f"Failed to get unread count for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Mark a notification as read.

    Args:
        notification_id: Notification ID
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Success message
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    notification_service = NotificationService(db)

    try:
        success = await notification_service.mark_as_read(user_id, notification_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        return {"message": "Notification marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification"
        )


@router.put("/mark-all-read", response_model=MarkReadResponse)
async def mark_all_notifications_as_read(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Mark all user's notifications as read.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Number of notifications marked
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    notification_service = NotificationService(db)

    try:
        marked_count = await notification_service.mark_all_as_read(user_id)

        return MarkReadResponse(
            message=f"Marked {marked_count} notifications as read",
            marked_count=marked_count
        )

    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications"
        )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a notification.

    Args:
        notification_id: Notification ID
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Success message
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    notification_service = NotificationService(db)

    try:
        success = await notification_service.delete_notification(user_id, notification_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        return {"message": "Notification deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get user's notification preferences.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Notification preferences
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()

    try:
        user_doc = await db.users.find_one({"user_id": user_id})

        if not user_doc or "notification_preferences" not in user_doc:
            # Return default preferences
            return NotificationPreferences()

        return NotificationPreferences(**user_doc["notification_preferences"])

    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preferences"
        )


@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Update user's notification preferences.

    Args:
        preferences: New preferences
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Updated preferences
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()

    try:
        # Update preferences
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "notification_preferences": preferences.dict()
                }
            }
        )

        return preferences

    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

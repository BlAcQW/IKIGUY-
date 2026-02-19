"""
Notification API routes for DevotionalFlow.
Handles push notifications, daily reminders, and notification preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import logging

from app.services.notification_service import (
    schedule_daily_reminder,
    get_user_notifications,
    mark_notification_read,
)
from app.utils.auth import get_current_user
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reminders/schedule")
async def schedule_reminder_endpoint(
    reminder_time: str = Query(..., description="Time in HH:MM format (e.g., '08:00')"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Schedule a daily reminder notification.

    **Query Parameters:**
    - reminder_time: Time in HH:MM format (e.g., "08:00")

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} scheduling reminder for {reminder_time}")
    await schedule_daily_reminder(current_user.user_id, reminder_time)
    return {"message": "Daily reminder scheduled successfully", "reminder_time": reminder_time}


@router.get("/", response_model=dict)
async def get_notifications_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get notifications for the current user.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - unread_only: Only return unread notifications (default: false)

    **Auth Required:** Yes
    """
    notifications = await get_user_notifications(
        current_user.user_id, page=page, page_size=page_size, unread_only=unread_only
    )
    return notifications


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read_endpoint(
    notification_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Mark a notification as read.

    **Path Parameters:**
    - notification_id: Notification ID

    **Auth Required:** Yes
    """
    logger.info(f"User {current_user.user_id} marking notification {notification_id} as read")
    await mark_notification_read(notification_id, current_user.user_id)
    return {"message": "Notification marked as read"}






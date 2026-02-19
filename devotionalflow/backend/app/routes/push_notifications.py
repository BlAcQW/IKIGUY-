"""
Push notification API routes for DevotionalFlow.
Handles push subscription, announcements, and notification management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional, List
from datetime import datetime
import logging

from app.services.push_notification_service import (
    save_push_subscription,
    remove_push_subscription,
    send_push_notification,
    send_bulk_push_notifications,
    get_user_segments,
    get_users_by_segment,
    check_notification_frequency,
)
from app.services.notification_service import send_new_devotional_notification
from app.models.push_notification import (
    PushSubscriptionCreate,
    AnnouncementCreate,
    AnnouncementResponse,
    NotificationFrequencySettings,
)
from app.utils.auth import get_current_user, get_current_admin
from app.models.user import TokenData
from app.db.mongodb import get_database
from app.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """
    Get VAPID public key for push notification subscription.

    **Returns:**
    - VAPID public key

    **Note:**
    - This endpoint is public (no auth required)
    - Used by frontend to subscribe to push notifications
    """
    vapid_public_key = getattr(settings, "VAPID_PUBLIC_KEY", None)
    if not vapid_public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are not configured",
        )
    return {"public_key": vapid_public_key}


@router.post("/subscribe")
async def subscribe_push_notification(
    subscription: PushSubscriptionCreate,
    user_agent: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Subscribe to push notifications.

    **Request Body:**
    - endpoint: Push subscription endpoint
    - keys: Web Push keys (p256dh and auth)
    - user_agent: Optional user agent string

    **Auth Required:** Yes
    """
    try:
        subscription_dict = subscription.model_dump()
        if user_agent:
            subscription_dict["user_agent"] = user_agent
        
        await save_push_subscription(
            current_user.user_id,
            subscription_dict
        )
        return {"message": "Successfully subscribed to push notifications"}
    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to subscribe: {str(e)}",
        )


@router.post("/unsubscribe")
async def unsubscribe_push_notification(
    endpoint: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Unsubscribe from push notifications.

    **Query Parameters:**
    - endpoint: Optional specific endpoint to unsubscribe. If not provided, unsubscribes all.

    **Auth Required:** Yes
    """
    try:
        await remove_push_subscription(current_user.user_id, endpoint)
        return {"message": "Successfully unsubscribed from push notifications"}
    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe: {str(e)}",
        )


@router.get("/segments")
async def get_segments_endpoint(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get user segments for the current user.

    **Returns:**
    - List of segment names the user belongs to

    **Auth Required:** Yes
    """
    try:
        segments = await get_user_segments(current_user.user_id)
        return {"segments": segments}
    except Exception as e:
        logger.error(f"Error getting user segments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get segments: {str(e)}",
        )


async def send_announcement_background(announcement_id: str):
    """Background task to send announcement."""
    db = get_database()
    
    try:
        announcement = await db.announcements.find_one({"_id": ObjectId(announcement_id)})
        if not announcement:
            return
        
        # Get target user IDs
        user_ids = announcement.get("user_ids", [])
        
        # Add users from segments
        for segment in announcement.get("segments", []):
            segment_users = await get_users_by_segment(segment)
            user_ids.extend(segment_users)
        
        # Remove duplicates
        user_ids = list(set(user_ids))
        
        # Send notifications
        stats = await send_bulk_push_notifications(
            user_ids=user_ids,
            title=announcement["title"],
            body=announcement["message"],
            data=announcement.get("data"),
            segment="announcement",
        )
        
        # Update announcement status
        await db.announcements.update_one(
            {"_id": ObjectId(announcement_id)},
            {
                "$set": {
                    "status": "sent",
                    "sent_at": datetime.utcnow(),
                    "stats": stats,
                }
            }
        )
        
        logger.info(f"Announcement {announcement_id} sent to {stats['sent']} users")
    except Exception as e:
        logger.error(f"Error sending announcement {announcement_id}: {e}", exc_info=True)
        await db.announcements.update_one(
            {"_id": ObjectId(announcement_id)},
            {"$set": {"status": "failed", "error": str(e)}}
        )


@router.post("/announcements", response_model=AnnouncementResponse)
async def create_announcement(
    announcement: AnnouncementCreate,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    Create and send a custom announcement to readers.

    **Request Body:**
    - title: Announcement title
    - message: Announcement message
    - segments: Target segments (e.g., ['all_users', 'active_readers'])
    - user_ids: Optional specific user IDs
    - scheduled_at: Optional scheduled time (ISO datetime)
    - data: Optional data payload

    **Auth Required:** Admin only
    """
    try:
        db = get_database()
        
        # Validate segments
        valid_segments = [
            "all_users", "active_readers", "regular_readers", "new_readers",
            "engaged_readers", "notification_enabled", "mobile_users", "desktop_users"
        ]
        for segment in announcement.segments:
            if not segment.startswith("country_") and segment not in valid_segments:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid segment: {segment}",
                )
        
        # Create announcement record
        announcement_dict = announcement.model_dump()
        announcement_dict["created_by"] = ObjectId(current_user.user_id)
        announcement_dict["created_at"] = datetime.utcnow()
        announcement_dict["status"] = "pending"
        
        if announcement.scheduled_at:
            scheduled_time = datetime.fromisoformat(announcement.scheduled_at.replace('Z', '+00:00'))
            if scheduled_time > datetime.utcnow():
                announcement_dict["status"] = "scheduled"
            else:
                announcement_dict["status"] = "pending"
        
        result = await db.announcements.insert_one(announcement_dict)
        announcement_id = str(result.inserted_id)
        
        # Send immediately if not scheduled
        if not announcement.scheduled_at or announcement_dict["status"] == "pending":
            background_tasks.add_task(send_announcement_background, announcement_id)
        
        return {
            "id": announcement_id,
            **announcement_dict,
            "scheduled_at": announcement.scheduled_at,
            "sent_at": None,
            "stats": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating announcement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create announcement: {str(e)}",
        )


@router.get("/announcements", response_model=List[AnnouncementResponse])
async def list_announcements(
    limit: int = 50,
    current_user: TokenData = Depends(get_current_admin),
):
    """
    List all announcements.

    **Query Parameters:**
    - limit: Maximum number of announcements to return

    **Auth Required:** Admin only
    """
    try:
        db = get_database()
        
        cursor = db.announcements.find().sort("created_at", -1).limit(limit)
        announcements = []
        
        async for ann in cursor:
            announcements.append({
                "id": str(ann["_id"]),
                "title": ann.get("title", ""),
                "message": ann.get("message", ""),
                "segments": ann.get("segments", []),
                "user_ids": [str(uid) for uid in ann.get("user_ids", [])] if ann.get("user_ids") else None,
                "scheduled_at": ann.get("scheduled_at").isoformat() if ann.get("scheduled_at") else None,
                "sent_at": ann.get("sent_at").isoformat() if ann.get("sent_at") else None,
                "stats": ann.get("stats"),
                "status": ann.get("status", "pending"),
            })
        
        return announcements
    except Exception as e:
        logger.error(f"Error listing announcements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list announcements: {str(e)}",
        )


@router.put("/frequency", response_model=NotificationFrequencySettings)
async def update_notification_frequency(
    settings: NotificationFrequencySettings,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Update notification frequency settings for current user.

    **Request Body:**
    - daily_reminders: Max daily reminders per day (0-3)
    - new_devotionals: Max new devotional notifications per day (0-10)
    - announcements: Max announcement notifications per day (0-5)
    - total_per_day: Max total notifications per day (0-20)

    **Auth Required:** Yes
    """
    try:
        db = get_database()
        
        await db.users.update_one(
            {"_id": ObjectId(current_user.user_id)},
            {
                "$set": {
                    "notification_frequency": settings.model_dump(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        return settings
    except Exception as e:
        logger.error(f"Error updating notification frequency: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update frequency settings: {str(e)}",
        )


@router.get("/frequency", response_model=NotificationFrequencySettings)
async def get_notification_frequency(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get notification frequency settings for current user.

    **Returns:**
    - Current frequency settings

    **Auth Required:** Yes
    """
    try:
        db = get_database()
        
        user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        frequency = user.get("notification_frequency", {})
        return NotificationFrequencySettings(**frequency) if frequency else NotificationFrequencySettings()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification frequency: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get frequency settings: {str(e)}",
        )

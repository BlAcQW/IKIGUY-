"""
Notification service for DevotionalFlow.
Handles push notifications, daily reminders, and email notifications.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException, status

from app.db.mongodb import get_database
import logging

logger = logging.getLogger(__name__)


async def schedule_daily_reminder(user_id: str, reminder_time: str = "08:00") -> None:
    """
    Schedule a daily reminder for a user.

    Args:
        user_id: User ID.
        reminder_time: Time in HH:MM format (default: "08:00").
    """
    db = get_database()

    # Parse reminder time
    try:
        hour, minute = map(int, reminder_time.split(":"))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError("Invalid time format")
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reminder time format. Use HH:MM (e.g., '08:00')",
        )

    # Update user preferences
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "reading_preferences.notification_time": reminder_time,
                "reading_preferences.notifications_enabled": True,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    logger.info(f"Scheduled daily reminder for user {user_id} at {reminder_time}")


async def send_daily_reminder(user_id: str) -> bool:
    """
    Send daily reminder notification to a user.
    This should be called by a scheduled job (cron).

    Args:
        user_id: User ID.

    Returns:
        bool: True if reminder was sent, False otherwise.
    """
    db = get_database()

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return False

    # Check if notifications are enabled
    prefs = user.get("reading_preferences", {})
    if not prefs.get("notifications_enabled", True):
        return False

    # Check if user already read today's devotional
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    already_read = await db.reading_history.find_one(
        {
            "user_id": ObjectId(user_id),
            "read_at": {"$gte": start_of_day, "$lte": end_of_day},
        }
    )

    if already_read:
        logger.info(f"User {user_id} already read today's devotional, skipping reminder")
        return False

    # Send push notification
    from app.services.push_notification_service import send_push_notification, check_notification_frequency
    
    # Check frequency limit
    if not await check_notification_frequency(user_id, "daily_reminder", max_per_day=1):
        logger.info(f"Daily reminder frequency limit reached for user {user_id}")
        return False
    
    # Send push notification
    await send_push_notification(
        user_id=user_id,
        title="Daily Devotional Reminder",
        body="Don't forget to read today's devotional!",
        data={"type": "daily_reminder", "action": "/today"},
        tag="daily_reminder",
    )

    # Record notification sent
    await db.notifications.insert_one(
        {
            "user_id": ObjectId(user_id),
            "type": "daily_reminder",
            "title": "Daily Devotional Reminder",
            "message": "Don't forget to read today's devotional!",
            "sent_at": datetime.utcnow(),
            "read_at": None,
        }
    )

    return True


async def send_new_devotional_notification(devotional_id: str, author_id: str) -> None:
    """
    Send notification to all followers/readers when a new devotional is published.

    Args:
        devotional_id: Devotional ID.
        author_id: Author ID.
    """
    db = get_database()

    # Get devotional
    devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
    if not devotional:
        return

    # Get all users who have notifications enabled
    # For MVP, we'll notify all active users
    # In future, can filter by followers or preferences
    users_cursor = db.users.find(
        {
            "reading_preferences.notifications_enabled": {"$ne": False},
            "role": "user",  # Only notify readers, not other pastors
        }
    )

    from app.services.push_notification_service import send_push_notification, check_notification_frequency
    
    notification_count = 0
    async for user in users_cursor:
        user_id = str(user["_id"])
        
        # Check frequency limit
        if not await check_notification_frequency(user_id, "new_devotional", max_per_day=3):
            continue
        
        # Send push notification
        await send_push_notification(
            user_id=user_id,
            title=f"New Devotional: {devotional['title']}",
            body=f"A new devotional has been published by {devotional.get('author_name', 'Unknown')}",
            data={
                "type": "new_devotional",
                "devotional_id": str(devotional_id),
                "action": f"/devotional/{devotional_id}",
            },
            tag="new_devotional",
        )

        # Record notification
        await db.notifications.insert_one(
            {
                "user_id": user["_id"],
                "type": "new_devotional",
                "title": f"New Devotional: {devotional['title']}",
                "message": f"A new devotional has been published by {devotional.get('author_name', 'Unknown')}",
                "devotional_id": ObjectId(devotional_id),
                "sent_at": datetime.utcnow(),
                "read_at": None,
            }
        )
        notification_count += 1

    logger.info(f"Sent new devotional notifications to {notification_count} users")


async def get_user_notifications(
    user_id: str, page: int = 1, page_size: int = 20, unread_only: bool = False
) -> dict:
    """
    Get notifications for a user.

    Args:
        user_id: User ID.
        page: Page number.
        page_size: Items per page.
        unread_only: Only return unread notifications.

    Returns:
        dict: Notifications with pagination.
    """
    db = get_database()

    query = {"user_id": ObjectId(user_id)}
    if unread_only:
        query["read_at"] = None

    total = await db.notifications.count_documents(query)

    skip = (page - 1) * page_size
    cursor = (
        db.notifications.find(query)
        .sort("sent_at", -1)
        .skip(skip)
        .limit(page_size)
    )

    notifications = []
    async for notif in cursor:
        notifications.append(
            {
                "id": str(notif["_id"]),
                "type": notif.get("type", "unknown"),
                "title": notif.get("title", ""),
                "message": notif.get("message", ""),
                "devotional_id": str(notif["devotional_id"]) if notif.get("devotional_id") else None,
                "sent_at": notif.get("sent_at", datetime.utcnow()).isoformat(),
                "read_at": notif.get("read_at").isoformat() if notif.get("read_at") else None,
                "is_read": notif.get("read_at") is not None,
            }
        )

    total_pages = (total + page_size - 1) // page_size

    return {
        "notifications": notifications,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


async def mark_notification_read(notification_id: str, user_id: str) -> None:
    """
    Mark a notification as read.

    Args:
        notification_id: Notification ID.
        user_id: User ID.
    """
    db = get_database()

    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id), "user_id": ObjectId(user_id)},
        {"$set": {"read_at": datetime.utcnow()}},
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )


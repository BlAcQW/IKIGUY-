"""
Push notification service for DevotionalFlow.
Handles Web Push API notifications.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import HTTPException, status
import json
import logging

from app.db.mongodb import get_database
from app.config import settings

logger = logging.getLogger(__name__)

# Web Push requires pywebpush library
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logger.warning("pywebpush not installed. Push notifications will be disabled.")


async def save_push_subscription(user_id: str, subscription: Dict[str, Any]) -> None:
    """
    Save push notification subscription for a user.

    Args:
        user_id: User ID.
        subscription: Push subscription object from browser.
    """
    db = get_database()

    subscription_data = {
        "endpoint": subscription.get("endpoint"),
        "keys": subscription.get("keys", {}),
        "user_agent": subscription.get("user_agent"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Upsert subscription
    await db.push_subscriptions.update_one(
        {
            "user_id": ObjectId(user_id),
            "endpoint": subscription_data["endpoint"],
        },
        {
            "$set": subscription_data,
            "$setOnInsert": {
                "user_id": ObjectId(user_id),
            }
        },
        upsert=True,
    )

    logger.info(f"Saved push subscription for user {user_id}")


async def remove_push_subscription(user_id: str, endpoint: Optional[str] = None) -> None:
    """
    Remove push notification subscription for a user.

    Args:
        user_id: User ID.
        endpoint: Optional specific endpoint to remove. If None, removes all.
    """
    db = get_database()

    query = {"user_id": ObjectId(user_id)}
    if endpoint:
        query["endpoint"] = endpoint

    result = await db.push_subscriptions.delete_many(query)
    logger.info(f"Removed {result.deleted_count} push subscription(s) for user {user_id}")


async def send_push_notification(
    user_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    icon: Optional[str] = None,
    badge: Optional[str] = None,
    tag: Optional[str] = None,
) -> bool:
    """
    Send push notification to a user.

    Args:
        user_id: User ID.
        title: Notification title.
        body: Notification body.
        data: Optional data payload.
        icon: Optional icon URL.
        badge: Optional badge URL.
        tag: Optional notification tag (for grouping).

    Returns:
        bool: True if sent successfully, False otherwise.
    """
    if not WEBPUSH_AVAILABLE:
        logger.warning("WebPush not available, skipping push notification")
        return False

    db = get_database()

    # Get user's push subscriptions
    subscriptions = await db.push_subscriptions.find(
        {"user_id": ObjectId(user_id)}
    ).to_list(length=None)

    if not subscriptions:
        logger.info(f"No push subscriptions found for user {user_id}")
        return False

    # Get VAPID keys from settings
    vapid_private_key = getattr(settings, "VAPID_PRIVATE_KEY", None)
    vapid_public_key = getattr(settings, "VAPID_PUBLIC_KEY", None)
    vapid_email = getattr(settings, "VAPID_EMAIL", "noreply@freshmanna.com")

    if not vapid_private_key or not vapid_public_key:
        logger.warning("VAPID keys not configured, skipping push notification")
        # Still record notification in database even if push fails
        return False

    # Prepare notification payload
    payload = {
        "title": title,
        "body": body,
        "icon": icon or "/icon-192x192.png",
        "badge": badge or "/icon-96x96.png",
        "tag": tag,
        "data": data or {},
    }

    success_count = 0
    failed_endpoints = []

    for subscription in subscriptions:
        try:
            subscription_info = {
                "endpoint": subscription["endpoint"],
                "keys": subscription.get("keys", {}),
            }

            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{vapid_email}",
                },
            )
            success_count += 1
            logger.info(f"Sent push notification to user {user_id} via {subscription['endpoint']}")

        except WebPushException as e:
            logger.error(f"Failed to send push notification: {e}")
            # Remove invalid subscriptions (410 = Gone, 404 = Not Found)
            status_code = getattr(e, 'response', None)
            if status_code:
                if hasattr(status_code, 'status_code') and status_code.status_code in [410, 404]:
                    failed_endpoints.append(subscription["endpoint"])
            elif "410" in str(e) or "404" in str(e) or "Gone" in str(e):
                failed_endpoints.append(subscription["endpoint"])
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            failed_endpoints.append(subscription["endpoint"])

    # Clean up failed subscriptions
    if failed_endpoints:
        await db.push_subscriptions.delete_many(
            {"user_id": ObjectId(user_id), "endpoint": {"$in": failed_endpoints}}
        )

    return success_count > 0


async def send_bulk_push_notifications(
    user_ids: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    segment: Optional[str] = None,
) -> Dict[str, int]:
    """
    Send push notifications to multiple users.

    Args:
        user_ids: List of user IDs.
        title: Notification title.
        body: Notification body.
        data: Optional data payload.
        segment: Optional segment name for tracking.

    Returns:
        dict: Statistics about sent notifications.
    """
    stats = {
        "total": len(user_ids),
        "sent": 0,
        "failed": 0,
        "no_subscription": 0,
    }

    for user_id in user_ids:
        try:
            success = await send_push_notification(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
            )
            if success:
                stats["sent"] += 1
            else:
                stats["no_subscription"] += 1
        except Exception as e:
            logger.error(f"Error sending push to user {user_id}: {e}")
            stats["failed"] += 1

    logger.info(f"Bulk push notification stats: {stats}")
    return stats


async def get_user_segments(user_id: str) -> List[str]:
    """
    Get user segments for targeting.

    Args:
        user_id: User ID.

    Returns:
        List of segment names.
    """
    db = get_database()

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return []

    segments = []

    # Activity-based segments
    reading_history_count = await db.reading_history.count_documents(
        {"user_id": ObjectId(user_id)}
    )
    if reading_history_count >= 30:
        segments.append("active_readers")
    elif reading_history_count >= 7:
        segments.append("regular_readers")
    else:
        segments.append("new_readers")

    # Engagement-based segments
    bookmarks_count = await db.bookmarks.count_documents(
        {"user_id": ObjectId(user_id)}
    )
    if bookmarks_count >= 10:
        segments.append("engaged_readers")

    # Device-based segments
    device = user.get("last_device_type", "unknown")
    if device == "mobile":
        segments.append("mobile_users")
    elif device == "desktop":
        segments.append("desktop_users")

    # Preference-based segments
    prefs = user.get("reading_preferences", {})
    if prefs.get("notifications_enabled", True):
        segments.append("notification_enabled")

    # Geographic segments (if available)
    country = user.get("country") or user.get("country_code")
    if country:
        segments.append(f"country_{country.lower()}")

    return segments


async def get_users_by_segment(segment: str, limit: Optional[int] = None) -> List[str]:
    """
    Get user IDs for a specific segment.

    Args:
        segment: Segment name.
        limit: Optional limit on number of users.

    Returns:
        List of user IDs.
    """
    db = get_database()

    user_ids = []

    if segment == "active_readers":
        # Users with 30+ reading history entries
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 30}}},
        ]
        if limit:
            pipeline.append({"$limit": limit})
        cursor = db.reading_history.aggregate(pipeline)
        async for doc in cursor:
            user_ids.append(str(doc["_id"]))

    elif segment == "regular_readers":
        # Users with 7-29 reading history entries
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 7, "$lt": 30}}},
        ]
        if limit:
            pipeline.append({"$limit": limit})
        cursor = db.reading_history.aggregate(pipeline)
        async for doc in cursor:
            user_ids.append(str(doc["_id"]))

    elif segment == "new_readers":
        # Users with < 7 reading history entries
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$lt": 7}}},
        ]
        if limit:
            pipeline.append({"$limit": limit})
        cursor = db.reading_history.aggregate(pipeline)
        async for doc in cursor:
            user_ids.append(str(doc["_id"]))

    elif segment == "engaged_readers":
        # Users with 10+ bookmarks
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 10}}},
        ]
        if limit:
            pipeline.append({"$limit": limit})
        cursor = db.bookmarks.aggregate(pipeline)
        async for doc in cursor:
            user_ids.append(str(doc["_id"]))

    elif segment == "notification_enabled":
        # Users with notifications enabled
        cursor = db.users.find(
            {"reading_preferences.notifications_enabled": {"$ne": False}},
            {"_id": 1}
        )
        if limit:
            cursor = cursor.limit(limit)
        async for user in cursor:
            user_ids.append(str(user["_id"]))

    elif segment.startswith("country_"):
        # Geographic segment
        country = segment.replace("country_", "").upper()
        cursor = db.users.find(
            {"$or": [{"country": country}, {"country_code": country}]},
            {"_id": 1}
        )
        if limit:
            cursor = cursor.limit(limit)
        async for user in cursor:
            user_ids.append(str(user["_id"]))

    elif segment == "all_users":
        # All active users
        cursor = db.users.find({"role": "user"}, {"_id": 1})
        if limit:
            cursor = cursor.limit(limit)
        async for user in cursor:
            user_ids.append(str(user["_id"]))

    return user_ids


async def check_notification_frequency(
    user_id: str,
    notification_type: str,
    max_per_day: int = 3,
) -> bool:
    """
    Check if user can receive notification based on frequency limits.

    Args:
        user_id: User ID.
        notification_type: Type of notification.
        max_per_day: Maximum notifications per day for this type.

    Returns:
        bool: True if notification can be sent, False if limit reached.
    """
    db = get_database()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    count = await db.notifications.count_documents({
        "user_id": ObjectId(user_id),
        "type": notification_type,
        "sent_at": {"$gte": today_start, "$lt": today_end},
    })

    return count < max_per_day


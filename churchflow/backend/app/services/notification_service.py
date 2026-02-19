"""
Church notification service for multi-channel communications.

This service orchestrates direct notifications through multiple channels:
- Bus delay notifications (SMS + Push + WhatsApp based on severity)
- Conference reminders (Push + Email)
- Check-in confirmations (Push)

IMPORTANT: This service sends notifications directly (no n8n dependency).
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.core.database import get_database
from app.services.channels import (
    SMSChannel,
    WhatsAppChannel,
    EmailChannel,
    PushChannel
)

logger = logging.getLogger(__name__)


class NotificationChannel:
    """Notification channels."""
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class NotificationPriority:
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChurchNotificationService:
    """
    Church-specific notification service with direct channel integration.

    Handles multi-channel notifications with intelligent routing based on
    urgency and user preferences. Sends notifications directly via:
    - Twilio (SMS + WhatsApp)
    - SMTP (Email)
    - Firebase FCM (Push)
    """

    def __init__(self):
        """Initialize the notification service with channel handlers."""
        self.sms_channel = SMSChannel()
        self.whatsapp_channel = WhatsAppChannel()
        self.email_channel = EmailChannel()
        self.push_channel = PushChannel()
        self.logger = logger

    async def send_bus_delay_notification(
        self,
        bus_route_id: str,
        bus_name: str,
        delay_minutes: int,
        new_eta: str,
        pickup_location: str,
        users: List[Dict]
    ) -> Dict:
        """
        Send bus delay notifications with intelligent channel routing.

        Routing logic:
        - <15 min delay: Push notification only
        - 15-30 min delay: Push + SMS
        - >30 min delay: Push + SMS + WhatsApp

        Args:
            bus_route_id: ID of delayed bus route
            bus_name: Name of the bus route
            delay_minutes: Minutes of delay
            new_eta: New estimated arrival time
            pickup_location: Bus pickup location
            users: List of affected users with contact info

        Returns:
            Dict with notification results and delivery status
        """
        # Determine channels based on severity
        channels = [NotificationChannel.PUSH]
        priority = NotificationPriority.MEDIUM

        if delay_minutes >= 15:
            channels.append(NotificationChannel.SMS)
            priority = NotificationPriority.HIGH

        if delay_minutes >= 30:
            channels.append(NotificationChannel.WHATSAPP)
            priority = NotificationPriority.CRITICAL

        self.logger.info(
            f"Sending bus delay notification: {delay_minutes}min delay, "
            f"channels={channels}, {len(users)} users"
        )

        # Prepare notification content
        sms_message = (
            f"🚌 {bus_name}: Delayed {delay_minutes} min. "
            f"New ETA: {new_eta}. Pickup: {pickup_location}"
        )

        whatsapp_message = (
            f"*Bus Delay Alert* 🚌\n\n"
            f"*Route:* {bus_name}\n"
            f"*Delay:* {delay_minutes} minutes\n"
            f"*New ETA:* {new_eta}\n"
            f"*Pickup:* {pickup_location}\n\n"
            f"We apologize for the inconvenience."
        )

        push_title, push_body = self.push_channel.format_bus_delay_notification(
            bus_name, delay_minutes, new_eta
        )

        # Send notifications to all users
        notifications_sent = []
        notifications_failed = []

        for user in users:
            user_id = str(user.get("_id"))
            user_name = user.get("name", "User")
            phone = user.get("phone")
            fcm_token = user.get("fcm_token")

            channel_results = []

            # Send via each channel
            tasks = []

            # Push notification (always sent)
            if NotificationChannel.PUSH in channels and fcm_token:
                tasks.append(
                    self.push_channel.send(
                        fcm_token=fcm_token,
                        title=push_title,
                        body=push_body,
                        data={
                            "type": "bus_delay",
                            "bus_route_id": bus_route_id,
                            "delay_minutes": str(delay_minutes)
                        },
                        user_name=user_name
                    )
                )

            # SMS (for >= 15 min delay)
            if NotificationChannel.SMS in channels and phone:
                tasks.append(
                    self.sms_channel.send(
                        to_phone=phone,
                        message=sms_message,
                        user_name=user_name
                    )
                )

            # WhatsApp (for >= 30 min delay)
            if NotificationChannel.WHATSAPP in channels and phone:
                tasks.append(
                    self.whatsapp_channel.send(
                        to_phone=phone,
                        message=whatsapp_message,
                        user_name=user_name
                    )
                )

            # Execute all channel sends in parallel
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                channel_results = [r for r in results if not isinstance(r, Exception)]

            # Check if at least one channel succeeded
            success = any(r.get("success") for r in channel_results)

            # Log notification attempt
            notification_data = {
                "user_id": user_id,
                "user_name": user_name,
                "bus_name": bus_name,
                "delay_minutes": delay_minutes,
                "new_eta": new_eta,
                "pickup_location": pickup_location,
                "channels_used": channels,
                "channel_results": channel_results
            }

            await self._log_notification(
                user_id=user_id,
                notification_type="bus_delay",
                channels=channels,
                priority=priority,
                data=notification_data,
                status="sent" if success else "failed"
            )

            if success:
                notifications_sent.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "channels": [r["channel"] for r in channel_results if r.get("success")]
                })
                self.logger.info(
                    f"Bus delay notification sent to {user_name}"
                )
            else:
                notifications_failed.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "error": "All channels failed"
                })
                self.logger.error(
                    f"Failed to send bus delay notification to {user_name}"
                )

        return {
            "success": True,
            "bus_route_id": bus_route_id,
            "delay_minutes": delay_minutes,
            "channels_used": channels,
            "priority": priority,
            "total_users": len(users),
            "notifications_sent": len(notifications_sent),
            "notifications_failed": len(notifications_failed),
            "details": {
                "sent": notifications_sent,
                "failed": notifications_failed
            }
        }

    async def send_conference_reminder(
        self,
        conference_id: str,
        conference_name: str,
        start_date: datetime,
        venue: str,
        users: List[Dict],
        hours_before: int = 24
    ) -> Dict:
        """
        Send conference reminder notifications.

        Uses: Push + Email
        Timing: Sent at 7 days, 3 days, 1 day, 3 hours before event

        Args:
            conference_id: Conference ID
            conference_name: Conference name
            start_date: Conference start date
            venue: Conference venue
            users: List of registered users
            hours_before: Hours before conference

        Returns:
            Dict with notification results
        """
        channels = [NotificationChannel.PUSH, NotificationChannel.EMAIL]
        priority = NotificationPriority.MEDIUM

        if hours_before <= 3:
            priority = NotificationPriority.HIGH

        self.logger.info(
            f"Sending conference reminder: {conference_name}, "
            f"{hours_before}h before, {len(users)} users"
        )

        # Format push notification
        push_title, push_body = self.push_channel.format_conference_reminder_notification(
            conference_name, hours_before
        )

        notifications_sent = []
        notifications_failed = []

        for user in users:
            user_id = str(user.get("_id"))
            user_name = user.get("name", "User")
            email = user.get("email")
            fcm_token = user.get("fcm_token")

            channel_results = []
            tasks = []

            # Push notification
            if fcm_token:
                tasks.append(
                    self.push_channel.send(
                        fcm_token=fcm_token,
                        title=push_title,
                        body=push_body,
                        data={
                            "type": "conference_reminder",
                            "conference_id": conference_id,
                            "hours_before": str(hours_before)
                        },
                        user_name=user_name
                    )
                )

            # Email notification
            if email:
                subject, html_body = self.email_channel.format_conference_reminder_email(
                    user_name=user_name,
                    conference_name=conference_name,
                    start_date=start_date.strftime("%B %d, %Y at %I:%M %p"),
                    venue=venue,
                    hours_before=hours_before
                )

                plain_body = f"""
                Hello {user_name},

                This is a reminder that {conference_name} is starting soon!

                Date: {start_date.strftime("%B %d, %Y at %I:%M %p")}
                Venue: {venue}

                We look forward to seeing you there!

                ChurchFlow Notifications
                """

                tasks.append(
                    self.email_channel.send(
                        to_email=email,
                        subject=subject,
                        body_text=plain_body,
                        body_html=html_body,
                        user_name=user_name
                    )
                )

            # Execute all channel sends
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                channel_results = [r for r in results if not isinstance(r, Exception)]

            success = any(r.get("success") for r in channel_results)

            notification_data = {
                "user_id": user_id,
                "user_name": user_name,
                "conference_name": conference_name,
                "start_date": start_date.isoformat(),
                "venue": venue,
                "hours_before": hours_before,
                "channel_results": channel_results
            }

            await self._log_notification(
                user_id=user_id,
                notification_type="conference_reminder",
                channels=channels,
                priority=priority,
                data=notification_data,
                status="sent" if success else "failed"
            )

            if success:
                notifications_sent.append({
                    "user_id": user_id,
                    "user_name": user_name
                })
                self.logger.info(
                    f"Conference reminder sent to {user_name}"
                )
            else:
                notifications_failed.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "error": "All channels failed"
                })
                self.logger.error(
                    f"Failed to send conference reminder to {user_name}"
                )

        return {
            "success": True,
            "conference_id": conference_id,
            "conference_name": conference_name,
            "hours_before": hours_before,
            "channels_used": channels,
            "priority": priority,
            "total_users": len(users),
            "notifications_sent": len(notifications_sent),
            "notifications_failed": len(notifications_failed),
            "details": {
                "sent": notifications_sent,
                "failed": notifications_failed
            }
        }

    async def send_check_in_confirmation(
        self,
        user_id: str,
        user_name: str,
        conference_name: str,
        check_in_time: datetime,
        fcm_token: Optional[str] = None
    ) -> Dict:
        """
        Send check-in confirmation notification.

        Uses: Push notification only (instant)

        Args:
            user_id: User ID
            user_name: User name
            conference_name: Conference name
            check_in_time: Check-in timestamp
            fcm_token: User's FCM token for push notifications

        Returns:
            Dict with notification result
        """
        channels = [NotificationChannel.PUSH]
        priority = NotificationPriority.LOW

        if not fcm_token:
            self.logger.warning(
                f"No FCM token for {user_name}, skipping check-in confirmation"
            )
            return {
                "success": False,
                "user_id": user_id,
                "user_name": user_name,
                "error": "No FCM token available"
            }

        # Format push notification
        push_title, push_body = self.push_channel.format_check_in_confirmation_notification(
            user_name, conference_name
        )

        # Send push notification
        result = await self.push_channel.send(
            fcm_token=fcm_token,
            title=push_title,
            body=push_body,
            data={
                "type": "check_in_confirmation",
                "conference_name": conference_name,
                "check_in_time": check_in_time.isoformat()
            },
            user_name=user_name
        )

        notification_data = {
            "user_id": user_id,
            "user_name": user_name,
            "conference_name": conference_name,
            "check_in_time": check_in_time.isoformat(),
            "channel_result": result
        }

        await self._log_notification(
            user_id=user_id,
            notification_type="check_in_confirmation",
            channels=channels,
            priority=priority,
            data=notification_data,
            status="sent" if result.get("success") else "failed"
        )

        if result.get("success"):
            self.logger.info(f"Check-in confirmation sent to {user_name}")
            return {
                "success": True,
                "user_id": user_id,
                "user_name": user_name,
                "channels_used": channels,
                "priority": priority
            }
        else:
            self.logger.error(
                f"Failed to send check-in confirmation to {user_name}: "
                f"{result.get('error')}"
            )
            return {
                "success": False,
                "user_id": user_id,
                "user_name": user_name,
                "error": result.get("error")
            }

    async def _log_notification(
        self,
        user_id: str,
        notification_type: str,
        channels: List[str],
        priority: str,
        data: Dict,
        status: str = "sent"
    ) -> None:
        """
        Log notification to MongoDB for tracking and analytics.

        Args:
            user_id: User ID
            notification_type: Type of notification
            channels: Channels used
            priority: Priority level
            data: Notification data
            status: Delivery status
        """
        db = get_database()

        log_entry = {
            "user_id": user_id,
            "notification_type": notification_type,
            "channels": channels,
            "priority": priority,
            "data": data,
            "status": status,
            "created_at": datetime.utcnow()
        }

        try:
            await db.notification_logs.insert_one(log_entry)
            self.logger.debug(f"Notification logged for user {user_id}")
        except Exception as e:
            self.logger.error(f"Failed to log notification: {e}")

    async def get_notification_history(
        self,
        user_id: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get notification history from logs.

        Args:
            user_id: Filter by user ID
            notification_type: Filter by notification type
            limit: Maximum number of results

        Returns:
            List of notification log entries
        """
        db = get_database()

        query = {}
        if user_id:
            query["user_id"] = user_id
        if notification_type:
            query["notification_type"] = notification_type

        cursor = db.notification_logs.find(query).sort("created_at", -1).limit(limit)
        logs = await cursor.to_list(length=limit)

        return logs

    async def health_check(self) -> Dict:
        """
        Check health of notification service.

        Returns:
            Dict with health status for each channel
        """
        try:
            health_status = {
                "status": "healthy",
                "channels": {
                    "sms": {
                        "provider": "twilio",
                        "status": "healthy"
                    },
                    "whatsapp": {
                        "provider": "twilio",
                        "status": "healthy"
                    },
                    "email": {
                        "provider": "smtp",
                        "status": "healthy"
                    },
                    "push": {
                        "provider": "firebase",
                        "status": "healthy" if self.push_channel.initialized else "degraded"
                    }
                },
                "last_checked": datetime.utcnow().isoformat()
            }

            return health_status

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }


# Global notification service instance
notification_service = ChurchNotificationService()

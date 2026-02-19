"""
Notification Service for Wallet System

This service handles sending email and SMS notifications for wallet events,
managing user preferences, and tracking notification delivery.

Author: KasaAI Team
Date: 2025-10-27
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from .notification_models import (
    Notification,
    NotificationPreference,
    NotificationTemplate,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
    NotificationPriority,
    NotificationFrequency,
)
from .models import Transaction, Wallet, PaymentMethod
from ..resend import ResendIntegration, ResendEmail, ResendConfig
from ..sms import SMSIntegration, SMSProvider


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing wallet notifications.

    Handles sending email/SMS notifications for wallet events,
    managing user preferences, and tracking delivery status.
    """

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        resend_api_key: Optional[str] = None,
        twilio_config: Optional[Dict[str, str]] = None,
        from_email: str = "notifications@kasaai.ailabsafrica.com",
        from_phone: Optional[str] = None,
    ):
        """
        Initialize notification service.

        Args:
            database: MongoDB database connection
            resend_api_key: Resend API key for email
            twilio_config: Twilio configuration for SMS
            from_email: Default sender email address
            from_phone: Default sender phone number
        """
        self.db = database
        self.from_email = from_email
        self.from_phone = from_phone

        # Initialize email service (Resend)
        self.email_service = None
        if resend_api_key:
            resend_config = ResendConfig(api_key=resend_api_key)
            self.email_service = ResendIntegration(resend_config)
            logger.info("Email service (Resend) initialized")

        # Initialize SMS service (Twilio)
        self.sms_service = None
        if twilio_config:
            sms_config = {"providers": {"twilio": twilio_config}, "default_provider": "twilio"}
            self.sms_service = SMSIntegration(sms_config)
            logger.info("SMS service (Twilio) initialized")

        # Collections
        self.notifications_collection = database["wallet_notifications"]
        self.preferences_collection = database["wallet_notification_preferences"]
        self.templates_collection = database["wallet_notification_templates"]

    # ==================== Preference Management ====================

    async def get_user_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """
        Get user's notification preferences.

        Args:
            user_id: User ID

        Returns:
            NotificationPreference or None
        """
        try:
            prefs_data = await self.preferences_collection.find_one({"user_id": user_id})

            if not prefs_data:
                # Return default preferences
                return NotificationPreference(user_id=user_id)

            return NotificationPreference(**prefs_data)

        except Exception as e:
            logger.error(f"Error getting notification preferences for user {user_id}: {e}")
            return None

    async def update_user_preferences(
        self, user_id: str, preferences_update: Dict[str, Any]
    ) -> Optional[NotificationPreference]:
        """
        Update user's notification preferences.

        Args:
            user_id: User ID
            preferences_update: Fields to update

        Returns:
            Updated NotificationPreference or None
        """
        try:
            # Get existing preferences or create new
            existing_prefs = await self.get_user_preferences(user_id)

            if existing_prefs:
                # Update existing
                update_data = preferences_update.copy()
                update_data["updated_at"] = datetime.utcnow()

                await self.preferences_collection.update_one(
                    {"user_id": user_id}, {"$set": update_data}, upsert=True
                )
            else:
                # Create new
                new_prefs = NotificationPreference(user_id=user_id, **preferences_update)
                await self.preferences_collection.insert_one(new_prefs.dict())

            # Return updated preferences
            return await self.get_user_preferences(user_id)

        except Exception as e:
            logger.error(f"Error updating notification preferences for user {user_id}: {e}")
            return None

    # ==================== Core Notification Methods ====================

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        subject: str,
        message: str,
        channel: Optional[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        html_message: Optional[str] = None,
        transaction_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        wallet_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Send a notification to a user.

        Args:
            user_id: User ID
            notification_type: Type of notification
            subject: Notification subject
            message: Notification message
            channel: Preferred channel (auto-detect if None)
            priority: Notification priority
            html_message: HTML version of message (for email)
            transaction_id: Related transaction ID
            payment_method_id: Related payment method ID
            metadata: Additional metadata
            wallet_id: Related wallet ID

        Returns:
            Notification object or None
        """
        try:
            # Get user preferences
            prefs = await self.get_user_preferences(user_id)

            # Check if notifications are enabled for this type
            if not self._should_send_notification(notification_type, prefs):
                logger.info(
                    f"Notification {notification_type} disabled for user {user_id}, skipping"
                )
                return None

            # Determine channel if not specified
            if not channel:
                channel = self._determine_channel(notification_type, prefs, priority)

            # Create notification record
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                wallet_id=wallet_id,
                type=notification_type,
                channel=channel,
                priority=priority,
                subject=subject,
                message=message,
                html_message=html_message,
                transaction_id=transaction_id,
                payment_method_id=payment_method_id,
                metadata=metadata or {},
                status=NotificationStatus.QUEUED,
                queued_at=datetime.utcnow(),
            )

            # Save to database
            await self.notifications_collection.insert_one(notification.dict())

            # Send notification asynchronously
            asyncio.create_task(self._send_notification_async(notification, prefs))

            return notification

        except Exception as e:
            logger.error(
                f"Error sending notification to user {user_id}, type {notification_type}: {e}"
            )
            return None

    async def _send_notification_async(
        self, notification: Notification, prefs: NotificationPreference
    ):
        """
        Send notification asynchronously (internal method).

        Args:
            notification: Notification to send
            prefs: User preferences
        """
        try:
            # Update status to sending
            await self.notifications_collection.update_one(
                {"id": notification.id},
                {"$set": {"status": NotificationStatus.SENDING.value}},
            )

            # Send based on channel
            if notification.channel == NotificationChannel.EMAIL:
                success = await self._send_email_notification(notification, prefs)
            elif notification.channel == NotificationChannel.SMS:
                success = await self._send_sms_notification(notification, prefs)
            else:
                logger.warning(
                    f"Unsupported notification channel: {notification.channel}"
                )
                success = False

            # Update status
            if success:
                await self.notifications_collection.update_one(
                    {"id": notification.id},
                    {
                        "$set": {
                            "status": NotificationStatus.SENT.value,
                            "sent_at": datetime.utcnow().isoformat(),
                        }
                    },
                )
            else:
                await self._handle_notification_failure(notification)

        except Exception as e:
            logger.error(f"Error in async notification send: {e}")
            await self._handle_notification_failure(notification, str(e))

    async def _send_email_notification(
        self, notification: Notification, prefs: NotificationPreference
    ) -> bool:
        """Send email notification."""
        if not self.email_service:
            logger.error("Email service not configured")
            return False

        if not prefs.email or not prefs.email_enabled:
            logger.info(f"Email not configured or disabled for user {notification.user_id}")
            return False

        try:
            # Prepare email
            email = ResendEmail(
                from_=self.from_email,
                to=[prefs.email],
                subject=notification.subject,
                text=notification.message,
                html=notification.html_message,
            )

            # Send email
            result = await self.email_service.send_email(email)

            if result.success:
                # Update notification with provider info
                await self.notifications_collection.update_one(
                    {"id": notification.id},
                    {
                        "$set": {
                            "provider": "resend",
                            "provider_message_id": result.email_id,
                        }
                    },
                )
                return True
            else:
                logger.error(f"Failed to send email: {result.error}")
                return False

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False

    async def _send_sms_notification(
        self, notification: Notification, prefs: NotificationPreference
    ) -> bool:
        """Send SMS notification."""
        if not self.sms_service:
            logger.error("SMS service not configured")
            return False

        if not prefs.phone_number or not prefs.sms_enabled:
            logger.info(f"Phone not configured or SMS disabled for user {notification.user_id}")
            return False

        if not self.from_phone:
            logger.error("From phone number not configured")
            return False

        try:
            # Send SMS
            result = await self.sms_service.send_sms(
                to=prefs.phone_number,
                message=notification.message,
                from_number=self.from_phone,
                provider=SMSProvider.TWILIO,
            )

            if result.get("success"):
                # Update notification with provider info
                await self.notifications_collection.update_one(
                    {"id": notification.id},
                    {
                        "$set": {
                            "provider": "twilio",
                            "provider_message_id": result.get("message_id"),
                        }
                    },
                )
                return True
            else:
                logger.error(f"Failed to send SMS: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False

    async def _handle_notification_failure(
        self, notification: Notification, error_message: Optional[str] = None
    ):
        """Handle notification sending failure."""
        retry_count = notification.retry_count + 1

        update_data = {
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
        }

        if error_message:
            update_data["error_message"] = error_message

        # Check if should retry
        if retry_count < notification.max_retries:
            update_data["status"] = NotificationStatus.QUEUED.value
            logger.info(
                f"Notification {notification.id} failed, will retry ({retry_count}/{notification.max_retries})"
            )

            # Schedule retry with exponential backoff
            retry_delay = 2**retry_count * 60  # 2min, 4min, 8min, etc.
            asyncio.create_task(self._retry_notification(notification.id, retry_delay))
        else:
            update_data["status"] = NotificationStatus.FAILED.value
            logger.error(
                f"Notification {notification.id} failed permanently after {retry_count} attempts"
            )

        await self.notifications_collection.update_one({"id": notification.id}, {"$set": update_data})

    async def _retry_notification(self, notification_id: str, delay_seconds: int):
        """Retry sending notification after delay."""
        await asyncio.sleep(delay_seconds)

        notification_data = await self.notifications_collection.find_one({"id": notification_id})
        if not notification_data:
            return

        notification = Notification(**notification_data)
        prefs = await self.get_user_preferences(notification.user_id)

        await self._send_notification_async(notification, prefs)

    # ==================== Wallet Event Notifications ====================

    async def notify_transaction_completed(self, transaction: Transaction, wallet: Wallet):
        """Send notification for completed transaction."""
        amount_str = f"{transaction.amount} {transaction.currency}"

        subject = f"Transaction Completed - {amount_str}"
        message = f"Your {transaction.transaction_type} transaction of {amount_str} has been completed successfully."
        html_message = f"""
        <h2>Transaction Completed</h2>
        <p>Your {transaction.transaction_type} transaction has been completed successfully.</p>
        <ul>
            <li><strong>Amount:</strong> {amount_str}</li>
            <li><strong>Type:</strong> {transaction.transaction_type}</li>
            <li><strong>Status:</strong> {transaction.status}</li>
            <li><strong>Date:</strong> {transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
        <p>Your new balance is {wallet.balance} {wallet.currency}.</p>
        """

        await self.send_notification(
            user_id=wallet.user_id,
            notification_type=NotificationType.TRANSACTION_COMPLETED,
            subject=subject,
            message=message,
            html_message=html_message,
            transaction_id=transaction.id,
            wallet_id=wallet.id,
            priority=NotificationPriority.NORMAL,
        )

    async def notify_transaction_failed(self, transaction: Transaction, wallet: Wallet, reason: str):
        """Send notification for failed transaction."""
        amount_str = f"{transaction.amount} {transaction.currency}"

        subject = f"Transaction Failed - {amount_str}"
        message = f"Your {transaction.transaction_type} transaction of {amount_str} has failed. Reason: {reason}"
        html_message = f"""
        <h2>Transaction Failed</h2>
        <p>Unfortunately, your transaction could not be completed.</p>
        <ul>
            <li><strong>Amount:</strong> {amount_str}</li>
            <li><strong>Type:</strong> {transaction.transaction_type}</li>
            <li><strong>Reason:</strong> {reason}</li>
        </ul>
        <p>Please try again or contact support if the issue persists.</p>
        """

        await self.send_notification(
            user_id=wallet.user_id,
            notification_type=NotificationType.TRANSACTION_FAILED,
            subject=subject,
            message=message,
            html_message=html_message,
            transaction_id=transaction.id,
            wallet_id=wallet.id,
            priority=NotificationPriority.HIGH,
        )

    async def notify_low_balance(self, wallet: Wallet, threshold: Decimal):
        """Send low balance alert."""
        subject = "Low Balance Alert"
        message = f"Your wallet balance ({wallet.balance} {wallet.currency}) is below the threshold of {threshold} {wallet.currency}."
        html_message = f"""
        <h2>Low Balance Alert</h2>
        <p>Your wallet balance is running low.</p>
        <ul>
            <li><strong>Current Balance:</strong> {wallet.balance} {wallet.currency}</li>
            <li><strong>Threshold:</strong> {threshold} {wallet.currency}</li>
        </ul>
        <p>Please add funds to your wallet to continue using our services.</p>
        """

        await self.send_notification(
            user_id=wallet.user_id,
            notification_type=NotificationType.LOW_BALANCE_ALERT,
            subject=subject,
            message=message,
            html_message=html_message,
            wallet_id=wallet.id,
            priority=NotificationPriority.HIGH,
        )

    async def notify_suspicious_activity(self, wallet: Wallet, reason: str):
        """Send security alert for suspicious activity."""
        subject = "Security Alert - Suspicious Activity Detected"
        message = f"Suspicious activity detected on your wallet. Reason: {reason}. If this wasn't you, please contact support immediately."
        html_message = f"""
        <h2>Security Alert</h2>
        <p><strong>Suspicious activity detected on your wallet.</strong></p>
        <ul>
            <li><strong>Wallet ID:</strong> {wallet.id}</li>
            <li><strong>Reason:</strong> {reason}</li>
            <li><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
        </ul>
        <p>If this wasn't you, please contact support immediately.</p>
        <p><strong>For security, we've temporarily paused suspicious transactions.</strong></p>
        """

        await self.send_notification(
            user_id=wallet.user_id,
            notification_type=NotificationType.SUSPICIOUS_ACTIVITY,
            subject=subject,
            message=message,
            html_message=html_message,
            wallet_id=wallet.id,
            priority=NotificationPriority.URGENT,
            # Send via both email and SMS for security alerts
            channel=NotificationChannel.EMAIL,
        )

        # Also send SMS if enabled
        await self.send_notification(
            user_id=wallet.user_id,
            notification_type=NotificationType.SUSPICIOUS_ACTIVITY,
            subject=subject,
            message=message,
            wallet_id=wallet.id,
            priority=NotificationPriority.URGENT,
            channel=NotificationChannel.SMS,
        )

    # ==================== Helper Methods ====================

    def _should_send_notification(
        self, notification_type: NotificationType, prefs: NotificationPreference
    ) -> bool:
        """Check if notification should be sent based on preferences."""
        # Check category preferences
        if "transaction" in notification_type.value:
            if not prefs.transaction_notifications:
                return False
        elif "security" in notification_type.value or "suspicious" in notification_type.value:
            if not prefs.security_notifications:
                return False
        elif "balance" in notification_type.value or "reload" in notification_type.value:
            if not prefs.balance_notifications:
                return False
        elif "payment_method" in notification_type.value:
            if not prefs.payment_method_notifications:
                return False

        return True

    def _determine_channel(
        self,
        notification_type: NotificationType,
        prefs: NotificationPreference,
        priority: NotificationPriority,
    ) -> NotificationChannel:
        """Determine best channel for notification."""
        # Urgent notifications prefer SMS
        if priority == NotificationPriority.URGENT and prefs.sms_enabled:
            return NotificationChannel.SMS

        # Security notifications prefer email by default
        if "security" in notification_type.value or "suspicious" in notification_type.value:
            if prefs.email_enabled:
                return NotificationChannel.EMAIL
            elif prefs.sms_enabled:
                return NotificationChannel.SMS

        # Default to email if enabled
        if prefs.email_enabled:
            return NotificationChannel.EMAIL
        elif prefs.sms_enabled:
            return NotificationChannel.SMS
        else:
            return NotificationChannel.EMAIL  # Fallback

    # ==================== Query Methods ====================

    async def get_user_notifications(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Notification]:
        """
        Get user's notification history.

        Args:
            user_id: User ID
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip

        Returns:
            List of notifications
        """
        try:
            cursor = (
                self.notifications_collection.find({"user_id": user_id})
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )

            notifications = []
            async for notif_data in cursor:
                notifications.append(Notification(**notif_data))

            return notifications

        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []

    async def mark_notification_read(self, notification_id: str) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            True if successful
        """
        try:
            result = await self.notifications_collection.update_one(
                {"id": notification_id}, {"$set": {"read_at": datetime.utcnow().isoformat()}}
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return False

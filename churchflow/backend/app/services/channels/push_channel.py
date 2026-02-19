"""
Push notification channel using Firebase Cloud Messaging (FCM).

Sends push notifications to mobile devices via Firebase.
"""

import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

# Firebase Admin SDK requires credentials file
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase Admin SDK not available")


class PushChannel:
    """
    Push notification channel using Firebase Cloud Messaging.

    Handles sending push notifications to iOS and Android devices.
    """

    def __init__(self):
        """Initialize Firebase Admin SDK."""
        self.logger = logger
        self.initialized = False

        if not FIREBASE_AVAILABLE:
            self.logger.error("Firebase Admin SDK not installed")
            return

        # Check if Firebase is already initialized
        if not firebase_admin._apps:
            # Try to initialize Firebase
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

            if cred_path and os.path.exists(cred_path):
                try:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    self.initialized = True
                    self.logger.info("Firebase Admin SDK initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Firebase: {e}")
            else:
                self.logger.warning(
                    "Firebase credentials not found. Set FIREBASE_CREDENTIALS_PATH. "
                    "Push notifications will be logged but not sent."
                )
        else:
            self.initialized = True
            self.logger.info("Firebase Admin SDK already initialized")

    async def send(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        user_name: Optional[str] = None
    ) -> Dict:
        """
        Send push notification via Firebase Cloud Messaging.

        Args:
            fcm_token: Device FCM registration token
            title: Notification title
            body: Notification body text
            data: Optional data payload (key-value pairs)
            user_name: Optional user name for logging

        Returns:
            Dict with delivery status and message ID

        Raises:
            firebase_admin.exceptions.FirebaseError: If push sending fails
        """
        if not FIREBASE_AVAILABLE or not self.initialized:
            self.logger.warning(
                f"Firebase not available. Would send push to {user_name or fcm_token}: "
                f"{title} - {body}"
            )
            return {
                "success": False,
                "channel": "push",
                "to": fcm_token,
                "error": "Firebase not initialized",
                "provider": "firebase"
            }

        try:
            self.logger.info(
                f"Sending push notification to {user_name or fcm_token}: {title}"
            )

            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=fcm_token
            )

            # Send message
            response = messaging.send(message)

            self.logger.info(
                f"Push notification sent successfully to {user_name or fcm_token}, "
                f"Message ID: {response}"
            )

            return {
                "success": True,
                "channel": "push",
                "to": fcm_token,
                "message_id": response,
                "provider": "firebase"
            }

        except Exception as e:
            # Check if it's an UnregisteredError (invalid/expired token)
            if "UnregisteredError" in str(type(e).__name__):
                self.logger.error(
                    f"FCM token is invalid or expired for {user_name or fcm_token}"
                )
                return {
                    "success": False,
                    "channel": "push",
                    "to": fcm_token,
                    "error": "Invalid or expired FCM token",
                    "provider": "firebase"
                }
            self.logger.error(
                f"Failed to send push notification to {user_name or fcm_token}: {e}"
            )
            return {
                "success": False,
                "channel": "push",
                "to": fcm_token,
                "error": str(e),
                "provider": "firebase"
            }

    async def send_multicast(
        self,
        fcm_tokens: list[str],
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Send push notification to multiple devices.

        Args:
            fcm_tokens: List of device FCM tokens
            title: Notification title
            body: Notification body text
            data: Optional data payload

        Returns:
            Dict with delivery results for all tokens
        """
        if not FIREBASE_AVAILABLE or not self.initialized:
            self.logger.warning(
                f"Firebase not available. Would send push to {len(fcm_tokens)} devices"
            )
            return {
                "success": False,
                "channel": "push",
                "total_tokens": len(fcm_tokens),
                "success_count": 0,
                "failure_count": len(fcm_tokens),
                "error": "Firebase not initialized"
            }

        try:
            self.logger.info(
                f"Sending multicast push notification to {len(fcm_tokens)} devices"
            )

            # Create multicast message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=fcm_tokens
            )

            # Send multicast
            response = messaging.send_multicast(message)

            self.logger.info(
                f"Multicast push sent: {response.success_count} success, "
                f"{response.failure_count} failures"
            )

            return {
                "success": True,
                "channel": "push",
                "total_tokens": len(fcm_tokens),
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "provider": "firebase"
            }

        except Exception as e:
            self.logger.error(f"Failed to send multicast push: {e}")
            return {
                "success": False,
                "channel": "push",
                "total_tokens": len(fcm_tokens),
                "error": str(e),
                "provider": "firebase"
            }

    def format_bus_delay_notification(
        self,
        bus_name: str,
        delay_minutes: int,
        new_eta: str
    ) -> tuple[str, str]:
        """
        Format bus delay push notification.

        Args:
            bus_name: Bus route name
            delay_minutes: Delay in minutes
            new_eta: New estimated arrival time

        Returns:
            Tuple of (title, body)
        """
        title = f"🚌 {bus_name} - Delayed"
        body = f"Delayed by {delay_minutes} min. New ETA: {new_eta}"
        return title, body

    def format_conference_reminder_notification(
        self,
        conference_name: str,
        hours_before: int
    ) -> tuple[str, str]:
        """
        Format conference reminder push notification.

        Args:
            conference_name: Conference name
            hours_before: Hours before conference

        Returns:
            Tuple of (title, body)
        """
        timing = f"{hours_before}h" if hours_before < 24 else f"{hours_before // 24}d"
        title = f"📅 {conference_name}"
        body = f"Starting in {timing}. Don't forget to attend!"
        return title, body

    def format_check_in_confirmation_notification(
        self,
        user_name: str,
        conference_name: str
    ) -> tuple[str, str]:
        """
        Format check-in confirmation push notification.

        Args:
            user_name: User name
            conference_name: Conference name

        Returns:
            Tuple of (title, body)
        """
        title = "✅ Check-in Confirmed"
        body = f"Welcome {user_name}! You're checked in to {conference_name}"
        return title, body

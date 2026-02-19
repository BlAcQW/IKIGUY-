"""
Slack Notification Service.

Handles sending notifications to Slack channels via webhooks.
Used for critical alerts like low phone credit, system errors, etc.
"""

import logging
import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Slack webhook URLs from environment (secure storage)
SLACK_LOW_CREDIT_WEBHOOK = os.getenv(
    "SLACK_LOW_CREDIT_WEBHOOK",
    "https://hooks.slack.com/services/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"
)


class SlackNotificationService:
    """Service for sending Slack webhook notifications."""

    def __init__(self):
        """Initialize the Slack notification service."""
        self.low_credit_webhook = SLACK_LOW_CREDIT_WEBHOOK
        self._sent_alerts: Dict[str, datetime] = {}  # Track sent alerts to prevent spam
        self._alert_cooldown_minutes = 60  # Only alert once per hour per phone
        logger.info("Slack notification service initialized")

    def _should_send_alert(self, phone_number: str) -> bool:
        """
        Check if we should send an alert (prevents spam).

        Args:
            phone_number: The phone number to check

        Returns:
            True if enough time has passed since last alert
        """
        if phone_number not in self._sent_alerts:
            return True

        last_sent = self._sent_alerts[phone_number]
        time_diff = (datetime.utcnow() - last_sent).total_seconds() / 60

        return time_diff >= self._alert_cooldown_minutes

    def _record_alert_sent(self, phone_number: str):
        """Record that an alert was sent for a phone number."""
        self._sent_alerts[phone_number] = datetime.utcnow()

    async def send_low_credit_alert(
        self,
        phone_number: str,
        current_balance: float,
        threshold: float,
        currency: str = "GHC",
        phone_name: Optional[str] = None,
        remaining_minutes: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Send a low credit alert to Slack.

        Args:
            phone_number: The phone number with low credit
            current_balance: Current credit balance
            threshold: The threshold that was breached
            currency: Currency code (default: GHC)
            phone_name: Optional friendly name for the phone
            remaining_minutes: Optional remaining call minutes

        Returns:
            Result dict with success status
        """
        if not self.low_credit_webhook:
            logger.warning("No Slack webhook configured for low credit alerts")
            return {"success": False, "error": "No webhook configured"}

        # Check cooldown to prevent spam
        if not self._should_send_alert(phone_number):
            logger.info(f"Skipping low credit alert for {phone_number} - cooldown active")
            return {"success": True, "skipped": True, "reason": "cooldown_active"}

        try:
            # Build the Slack message with rich formatting
            display_name = phone_name or phone_number
            remaining_info = f" ({remaining_minutes:.1f} minutes remaining)" if remaining_minutes else ""

            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Low Phone Credit Alert",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Phone Number:*\n{display_name}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Current Balance:*\n{currency} {current_balance:.2f}{remaining_info}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Alert Threshold:*\n{currency} {threshold:.2f}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "⚠️ Please add credit to avoid service interruption"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "📱 Manage Phone Numbers",
                                    "emoji": True
                                },
                                "url": "https://kasaai.ailabsafrica.com/phone-numbers",
                                "style": "primary"
                            }
                        ]
                    }
                ],
                "text": f"Low credit alert: {display_name} has {currency} {current_balance:.2f} remaining"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.low_credit_webhook,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    self._record_alert_sent(phone_number)
                    logger.info(f"Sent low credit Slack alert for {phone_number}")
                    return {"success": True}
                else:
                    logger.error(
                        f"Failed to send Slack alert: {response.status_code} - {response.text}"
                    )
                    return {
                        "success": False,
                        "error": f"Slack API error: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"Error sending Slack low credit alert: {e}")
            return {"success": False, "error": str(e)}

    async def send_critical_balance_alert(
        self,
        total_balance: float,
        threshold: float,
        currency: str = "GHC",
        phones_below_threshold: int = 0
    ) -> Dict[str, Any]:
        """
        Send a critical alert when total balance across all phones is low.

        Args:
            total_balance: Total credit balance across all phones
            threshold: Critical threshold
            currency: Currency code
            phones_below_threshold: Number of phones below individual threshold

        Returns:
            Result dict with success status
        """
        if not self.low_credit_webhook:
            return {"success": False, "error": "No webhook configured"}

        try:
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🔴 CRITICAL: System-Wide Low Credit",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Total system credit is critically low!*\n\n"
                                    f"• Total Balance: *{currency} {total_balance:.2f}*\n"
                                    f"• Critical Threshold: {currency} {threshold:.2f}\n"
                                    f"• Phones Below Threshold: {phones_below_threshold}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"🕐 Alert time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "⚡ *Immediate action required to prevent service disruption*"
                        }
                    }
                ],
                "text": f"CRITICAL: Total phone credit is {currency} {total_balance:.2f}"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.low_credit_webhook,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    logger.info("Sent critical balance Slack alert")
                    return {"success": True}
                else:
                    return {"success": False, "error": f"Slack API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error sending critical balance Slack alert: {e}")
            return {"success": False, "error": str(e)}


# Global instance
slack_notification_service = SlackNotificationService()

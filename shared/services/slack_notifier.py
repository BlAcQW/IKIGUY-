"""
Slack Notification Service

Sends notifications to Slack webhooks for campaign failures and other alerts.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Service for sending notifications to Slack via webhooks.

    Attributes:
        webhook_url: Slack webhook URL for sending notifications
        timeout: HTTP request timeout in seconds
    """

    def __init__(self, webhook_url: str, timeout: int = 10):
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL
            timeout: HTTP request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.logger = logger

    async def send_notification(
        self,
        message: str,
        title: Optional[str] = None,
        color: str = "#FF0000",  # Red for errors by default
        fields: Optional[list] = None
    ) -> bool:
        """
        Send a notification to Slack.

        Args:
            message: Main message text
            title: Optional title for the notification
            color: Color for the message attachment (hex code)
            fields: Optional list of field dictionaries with 'title' and 'value'

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            # Build Slack message payload
            attachment = {
                "color": color,
                "text": message,
                "ts": int(datetime.utcnow().timestamp())
            }

            if title:
                attachment["title"] = title

            if fields:
                attachment["fields"] = fields

            payload = {
                "attachments": [attachment]
            }

            # Send to Slack webhook
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload
                )

                if response.status_code == 200:
                    self.logger.info(f"Slack notification sent successfully: {title or message[:50]}")
                    return True
                else:
                    self.logger.error(
                        f"Failed to send Slack notification. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}", exc_info=True)
            return False

    async def notify_sms_failure(
        self,
        campaign_id: str,
        campaign_name: str,
        error_message: str,
        organization_id: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        provider: Optional[str] = None
    ) -> bool:
        """
        Send notification for SMS campaign message failure.

        Args:
            campaign_id: Campaign identifier
            campaign_name: Campaign name
            error_message: Error message
            organization_id: Organization ID
            recipient_phone: Recipient phone number (optional)
            provider: SMS provider used (optional)

        Returns:
            True if notification sent successfully
        """
        title = f"🚨 SMS Campaign Failure: {campaign_name}"

        fields = [
            {
                "title": "Campaign ID",
                "value": campaign_id,
                "short": True
            },
            {
                "title": "Error",
                "value": error_message,
                "short": False
            }
        ]

        if organization_id:
            fields.append({
                "title": "Organization",
                "value": organization_id,
                "short": True
            })

        if recipient_phone:
            fields.append({
                "title": "Recipient",
                "value": recipient_phone,
                "short": True
            })

        if provider:
            fields.append({
                "title": "Provider",
                "value": provider,
                "short": True
            })

        message = f"An SMS message in campaign '{campaign_name}' has failed."

        return await self.send_notification(
            message=message,
            title=title,
            color="#FF0000",  # Red for failures
            fields=fields
        )

    async def notify_voice_failure(
        self,
        campaign_id: str,
        campaign_name: str,
        error_message: str,
        organization_id: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        call_id: Optional[str] = None
    ) -> bool:
        """
        Send notification for voice campaign call failure.

        Args:
            campaign_id: Campaign identifier
            campaign_name: Campaign name
            error_message: Error message
            organization_id: Organization ID
            recipient_phone: Recipient phone number (optional)
            call_id: Call ID (optional)

        Returns:
            True if notification sent successfully
        """
        title = f"🚨 Voice Campaign Failure: {campaign_name}"

        fields = [
            {
                "title": "Campaign ID",
                "value": campaign_id,
                "short": True
            },
            {
                "title": "Error",
                "value": error_message,
                "short": False
            }
        ]

        if organization_id:
            fields.append({
                "title": "Organization",
                "value": organization_id,
                "short": True
            })

        if recipient_phone:
            fields.append({
                "title": "Recipient",
                "value": recipient_phone,
                "short": True
            })

        if call_id:
            fields.append({
                "title": "Call ID",
                "value": call_id,
                "short": True
            })

        message = f"A voice call in campaign '{campaign_name}' has failed."

        return await self.send_notification(
            message=message,
            title=title,
            color="#FF0000",  # Red for failures
            fields=fields
        )


# Singleton instance with default webhook URL
# Can be overridden by setting SLACK_WEBHOOK_URL environment variable
DEFAULT_WEBHOOK_URL = "https://hooks.slack.com/services/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"

_slack_notifier_instance: Optional[SlackNotifier] = None


def get_slack_notifier(webhook_url: Optional[str] = None) -> SlackNotifier:
    """
    Get singleton Slack notifier instance.

    Args:
        webhook_url: Optional webhook URL override

    Returns:
        SlackNotifier instance
    """
    global _slack_notifier_instance

    if _slack_notifier_instance is None or webhook_url is not None:
        url = webhook_url or DEFAULT_WEBHOOK_URL
        _slack_notifier_instance = SlackNotifier(webhook_url=url)

    return _slack_notifier_instance

"""
Slack Notification Service.

Sends notifications to Slack channels via webhooks.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SlackNotificationService:
    """Service for sending Slack notifications."""

    def __init__(self):
        """Initialize the Slack notification service."""
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        self.timeout = 10.0  # seconds

    async def send_message(
        self,
        text: str,
        blocks: Optional[list] = None,
        attachments: Optional[list] = None
    ) -> bool:
        """
        Send a message to Slack.

        Args:
            text: Fallback text for notifications
            blocks: Rich message blocks (optional)
            attachments: Message attachments (optional)

        Returns:
            bool: True if message sent successfully
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        payload: Dict[str, Any] = {"text": text}

        if blocks:
            payload["blocks"] = blocks
        if attachments:
            payload["attachments"] = attachments

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    logger.info(f"Slack notification sent successfully for: {text[:50]}...")
                    return True
                else:
                    logger.error(
                        f"Slack notification failed: {response.status_code} - {response.text}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error("Slack notification timed out")
            return False
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False

    async def notify_new_signup(
        self,
        email: str,
        user_id: str,
        invitation_redeemed: bool = False,
        book_title: Optional[str] = None
    ) -> bool:
        """
        Send notification for a new user signup.

        Args:
            email: User's email address
            user_id: User's unique ID
            invitation_redeemed: Whether user came from an invitation
            book_title: Title of book if invitation was redeemed

        Returns:
            bool: True if notification sent successfully
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build the message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "New InkWave Signup",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Email:*\n{email}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*User ID:*\n`{user_id[:8]}...`"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{timestamp}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{'Invitation Link' if invitation_redeemed else 'Direct Signup'}"
                    }
                ]
            }
        ]

        # Add book info if from invitation
        if invitation_redeemed and book_title:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Book Added:* {book_title}"
                }
            })

        # Add divider
        blocks.append({"type": "divider"})

        # Fallback text
        text = f"New InkWave signup: {email}"
        if invitation_redeemed:
            text += f" (via invitation for '{book_title}')"

        return await self.send_message(text=text, blocks=blocks)


# Singleton instance
slack_notification_service = SlackNotificationService()

"""
SMS notification channel using Arkesel (primary) with Twilio fallback.

Sends SMS messages to users via Arkesel SMS Gateway (optimized for Ghana).
"""

import logging
import aiohttp
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSChannel:
    """
    SMS notification channel using Arkesel (primary) and Twilio (fallback).

    Handles sending SMS messages with retry logic and error handling.
    Arkesel is optimized for Ghana and African markets.
    """

    def __init__(self):
        """Initialize SMS channel with Arkesel as primary provider."""
        self.arkesel_api_key = settings.arkesel_api_key
        self.arkesel_api_url = settings.arkesel_api_url
        self.arkesel_sender_id = settings.arkesel_sender_id
        self.logger = logger

    async def send(
        self,
        to_phone: str,
        message: str,
        user_name: Optional[str] = None
    ) -> Dict:
        """
        Send SMS message via Arkesel.

        Args:
            to_phone: Recipient phone number (supports various formats)
            message: SMS message content (max 160 chars recommended)
            user_name: Optional user name for logging

        Returns:
            Dict with delivery status and message details
        """
        # Normalize phone number for Arkesel (expects local format for Ghana)
        normalized_phone = self._normalize_phone(to_phone)

        try:
            self.logger.info(
                f"Sending SMS via Arkesel to {user_name or normalized_phone}: {message[:50]}..."
            )

            # Arkesel API request
            headers = {
                "api-key": self.arkesel_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "sender": self.arkesel_sender_id,
                "message": message,
                "recipients": [normalized_phone]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.arkesel_api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_data = await response.json()

                    if response.status == 200 and response_data.get("status") == "success":
                        self.logger.info(
                            f"SMS sent successfully via Arkesel to {user_name or normalized_phone}"
                        )
                        return {
                            "success": True,
                            "channel": "sms",
                            "to": normalized_phone,
                            "message_id": response_data.get("data", [{}])[0].get("id"),
                            "status": "sent",
                            "provider": "arkesel"
                        }
                    else:
                        error_msg = response_data.get("message", "Unknown error")
                        self.logger.error(
                            f"Arkesel SMS failed for {user_name or normalized_phone}: {error_msg}"
                        )
                        return {
                            "success": False,
                            "channel": "sms",
                            "to": normalized_phone,
                            "error": error_msg,
                            "provider": "arkesel"
                        }

        except aiohttp.ClientError as e:
            self.logger.error(
                f"Network error sending SMS to {user_name or normalized_phone}: {e}"
            )
            return {
                "success": False,
                "channel": "sms",
                "to": normalized_phone,
                "error": f"Network error: {str(e)}",
                "provider": "arkesel"
            }

        except Exception as e:
            self.logger.error(
                f"Unexpected error sending SMS to {user_name or normalized_phone}: {e}"
            )
            return {
                "success": False,
                "channel": "sms",
                "to": normalized_phone,
                "error": str(e),
                "provider": "arkesel"
            }

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number for Arkesel API.

        Arkesel expects Ghana numbers in format: 0XXXXXXXXX or 233XXXXXXXXX

        Args:
            phone: Phone number in any format

        Returns:
            Normalized phone number for Arkesel
        """
        # Remove spaces, dashes, and other formatting
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")

        # Remove + prefix
        if cleaned.startswith("+"):
            cleaned = cleaned[1:]

        # If starts with 233, it's already in international format
        if cleaned.startswith("233"):
            return cleaned

        # If starts with 0, convert to international format
        if cleaned.startswith("0") and len(cleaned) == 10:
            return "233" + cleaned[1:]

        # Default: assume it's already correct
        return cleaned

    def format_message(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        Format SMS message from template.

        Args:
            template: Message template with {placeholders}
            **kwargs: Values to substitute in template

        Returns:
            Formatted message (truncated to 160 chars if needed)
        """
        try:
            message = template.format(**kwargs)
        except KeyError as e:
            self.logger.warning(f"Missing placeholder in SMS template: {e}")
            message = template

        # SMS best practice: Keep under 160 characters
        if len(message) > 160:
            message = message[:157] + "..."
            self.logger.warning(
                f"SMS message truncated to 160 characters: {message}"
            )

        return message

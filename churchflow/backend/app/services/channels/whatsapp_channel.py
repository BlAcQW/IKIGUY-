"""
WhatsApp notification channel using Twilio.

Sends WhatsApp messages to users via Twilio WhatsApp API.
"""

import logging
from typing import Dict, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppChannel:
    """
    WhatsApp notification channel using Twilio.

    Handles sending WhatsApp messages with rich formatting support.
    """

    def __init__(self):
        """Initialize Twilio client."""
        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token
        )
        self.from_number = settings.twilio_whatsapp_number
        self.logger = logger

    async def send(
        self,
        to_phone: str,
        message: str,
        user_name: Optional[str] = None
    ) -> Dict:
        """
        Send WhatsApp message via Twilio.

        Args:
            to_phone: Recipient phone number (must be WhatsApp-enabled)
                     Format: +233... (will be converted to whatsapp:+233...)
            message: WhatsApp message content (up to 1600 chars)
            user_name: Optional user name for logging

        Returns:
            Dict with delivery status and message SID

        Raises:
            TwilioRestException: If WhatsApp sending fails
        """
        try:
            # Ensure phone number has 'whatsapp:' prefix
            if not to_phone.startswith("whatsapp:"):
                to_phone = f"whatsapp:{to_phone}"

            self.logger.info(
                f"Sending WhatsApp to {user_name or to_phone}: {message[:50]}..."
            )

            # Send WhatsApp via Twilio
            twilio_message = self.client.messages.create(
                to=to_phone,
                from_=self.from_number,
                body=message
            )

            self.logger.info(
                f"WhatsApp sent successfully to {user_name or to_phone}, "
                f"SID: {twilio_message.sid}"
            )

            return {
                "success": True,
                "channel": "whatsapp",
                "to": to_phone,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
                "provider": "twilio"
            }

        except TwilioRestException as e:
            self.logger.error(
                f"Failed to send WhatsApp to {user_name or to_phone}: "
                f"{e.code} - {e.msg}"
            )
            return {
                "success": False,
                "channel": "whatsapp",
                "to": to_phone,
                "error": f"Twilio error {e.code}: {e.msg}",
                "provider": "twilio"
            }

        except Exception as e:
            self.logger.error(
                f"Unexpected error sending WhatsApp to {user_name or to_phone}: {e}"
            )
            return {
                "success": False,
                "channel": "whatsapp",
                "to": to_phone,
                "error": str(e),
                "provider": "twilio"
            }

    def format_message(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        Format WhatsApp message from template.

        WhatsApp supports rich formatting:
        - *bold*
        - _italic_
        - ~strikethrough~
        - ```code```

        Args:
            template: Message template with {placeholders}
            **kwargs: Values to substitute in template

        Returns:
            Formatted message (max 1600 chars)
        """
        message = template.format(**kwargs)

        # WhatsApp supports up to 1600 characters
        if len(message) > 1600:
            message = message[:1597] + "..."
            self.logger.warning(
                f"WhatsApp message truncated to 1600 characters"
            )

        return message

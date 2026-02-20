"""
WhatsApp Business API Client for EstateFlow.

Sends WhatsApp messages via the WhatsApp Business Cloud API.
"""

import logging
import os
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


class WhatsAppClient:
    """Standalone WhatsApp Business API client."""

    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    async def send_message(
        self,
        to: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp text message.

        Args:
            to: Recipient phone number (international format, no +)
            message: Message text

        Returns:
            Response dict with success status
        """
        if not self.is_configured():
            logger.warning(f"WhatsApp not configured - would send to {to}: {message[:50]}...")
            return {"success": False, "error": "WhatsApp API not configured"}

        url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to.replace("+", ""),
            "type": "text",
            "text": {"body": message}
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"WhatsApp message sent to {to}")
                return {"success": True, "data": data}
        except Exception as e:
            logger.error(f"WhatsApp error to {to}: {e}")
            return {"success": False, "error": str(e)}

    async def send_bulk_messages(
        self,
        recipients: List[Dict[str, str]],
        message_template: str
    ) -> Dict[str, Any]:
        """
        Send bulk WhatsApp messages with personalization.

        Args:
            recipients: List of {phone, name} dicts
            message_template: Message with {{name}} placeholder

        Returns:
            Summary of sent/failed counts
        """
        sent = 0
        failed = 0

        for recipient in recipients:
            personalized = message_template.replace("{{name}}", recipient.get("name", "Customer"))
            result = await self.send_message(to=recipient["phone"], message=personalized)
            if result.get("success"):
                sent += 1
            else:
                failed += 1

        return {"sent": sent, "failed": failed, "total": len(recipients)}

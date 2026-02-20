"""
Arkesel SMS Client for EstateFlow.

Sends SMS messages via Arkesel HTTP API (Ghana SMS provider).
"""

import logging
import os
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)

ARKESEL_API_URL = "https://sms.arkesel.com/api/v2/sms/send"


class ArkeselClient:
    """Standalone Arkesel SMS client."""

    def __init__(self):
        self.api_key = os.getenv("ARKESEL_API_KEY", "")
        self.sender_id = os.getenv("ARKESEL_SENDER_ID", "EstateFlow")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def send_sms(
        self,
        to: str,
        message: str,
        sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a single SMS via Arkesel.

        Args:
            to: Recipient phone number (international format)
            message: SMS message body
            sender_id: Optional sender ID override

        Returns:
            Response dict with success status
        """
        if not self.is_configured():
            logger.warning(f"Arkesel not configured - would send SMS to {to}: {message[:50]}...")
            return {"success": False, "error": "Arkesel API key not configured"}

        payload = {
            "sender": sender_id or self.sender_id,
            "message": message,
            "recipients": [to]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    ARKESEL_API_URL,
                    json=payload,
                    headers={"api-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"SMS sent to {to} via Arkesel")
                return {"success": True, "data": data}
        except Exception as e:
            logger.error(f"Arkesel SMS error to {to}: {e}")
            return {"success": False, "error": str(e)}

    async def send_bulk_sms(
        self,
        recipients: List[Dict[str, str]],
        message_template: str
    ) -> Dict[str, Any]:
        """
        Send bulk SMS with personalization.

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
            result = await self.send_sms(to=recipient["phone"], message=personalized)
            if result.get("success"):
                sent += 1
            else:
                failed += 1

        return {"sent": sent, "failed": failed, "total": len(recipients)}

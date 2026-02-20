"""
Vapi Voice AI Client for EstateFlow.

Makes outbound voice calls via the Vapi API.
"""

import logging
import os
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)

VAPI_API_URL = "https://api.vapi.ai"


class VapiClient:
    """Standalone Vapi voice call client."""

    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def make_call(
        self,
        phone_number: str,
        assistant_id: str,
        customer_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate an outbound voice call via Vapi.

        Args:
            phone_number: Recipient phone number
            assistant_id: Vapi assistant ID to use
            customer_name: Optional customer name for personalization
            metadata: Optional metadata to pass to the assistant

        Returns:
            Response dict with success status and call ID
        """
        if not self.is_configured():
            logger.warning(f"Vapi not configured - would call {phone_number} with assistant {assistant_id}")
            return {"success": False, "error": "Vapi API key not configured"}

        payload = {
            "assistantId": assistant_id,
            "customer": {
                "number": phone_number,
                "name": customer_name or "Customer"
            }
        }

        if metadata:
            payload["metadata"] = metadata

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{VAPI_API_URL}/call/phone",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                call_id = data.get("id", "unknown")
                logger.info(f"Vapi call initiated to {phone_number}, call_id={call_id}")
                return {"success": True, "call_id": call_id, "data": data}
        except Exception as e:
            logger.error(f"Vapi call error to {phone_number}: {e}")
            return {"success": False, "error": str(e)}

    async def make_bulk_calls(
        self,
        recipients: List[Dict[str, Any]],
        assistant_id: str
    ) -> Dict[str, Any]:
        """
        Make bulk outbound calls.

        Args:
            recipients: List of {phone, name, data} dicts
            assistant_id: Vapi assistant ID

        Returns:
            Summary of initiated/failed counts
        """
        initiated = 0
        failed = 0

        for recipient in recipients:
            result = await self.make_call(
                phone_number=recipient["phone"],
                assistant_id=assistant_id,
                customer_name=recipient.get("name"),
                metadata=recipient.get("data")
            )
            if result.get("success"):
                initiated += 1
            else:
                failed += 1

        return {"initiated": initiated, "failed": failed, "total": len(recipients)}

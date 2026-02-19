"""
SMS Service for sending notifications via multiple providers.

Supports:
- Twilio
- Africa's Talking
- Hubtel (Ghana)
- Termii (Nigeria)
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SMSMessage(BaseModel):
    """SMS message model."""
    to_number: str = Field(..., description="Recipient phone number (E.164 format)")
    message: str = Field(..., description="Message content", max_length=160)
    from_number: Optional[str] = Field(None, description="Sender ID or phone number")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SMSService:
    """
    Service for sending SMS notifications.

    Supports multiple SMS providers with unified interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SMS service with configuration.

        Args:
            config: Configuration dictionary with provider-specific settings
        """
        self.config = config or {}
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize supported SMS providers."""
        # Twilio Provider
        if self.config.get("twilio_enabled", False):
            self.providers["twilio"] = {
                "account_sid": self.config.get("twilio_account_sid"),
                "auth_token": self.config.get("twilio_auth_token"),
                "from_number": self.config.get("twilio_from_number")
            }

        # Africa's Talking Provider
        if self.config.get("africastalking_enabled", False):
            self.providers["africastalking"] = {
                "api_key": self.config.get("africastalking_api_key"),
                "username": self.config.get("africastalking_username"),
                "from_id": self.config.get("africastalking_from_id", "KasaAI")
            }

        # Hubtel Provider (Ghana)
        if self.config.get("hubtel_enabled", False):
            self.providers["hubtel"] = {
                "client_id": self.config.get("hubtel_client_id"),
                "client_secret": self.config.get("hubtel_client_secret"),
                "from_id": self.config.get("hubtel_from_id", "KasaAI")
            }

        # Termii Provider (Nigeria, multi-country)
        if self.config.get("termii_enabled", False):
            self.providers["termii"] = {
                "api_key": self.config.get("termii_api_key"),
                "from_id": self.config.get("termii_from_id", "KasaAI"),
                "channel": self.config.get("termii_channel", "generic")
            }

        logger.info(f"Initialized SMS service with providers: {list(self.providers.keys())}")

    async def send_sms(
        self,
        provider: str,
        sms: SMSMessage,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS through specified provider.

        Args:
            provider: Provider name (twilio, africastalking, hubtel, termii)
            sms: SMS message to send
            context: Additional context

        Returns:
            Result of SMS sending operation
        """
        try:
            if provider not in self.providers:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not configured",
                    "available_providers": list(self.providers.keys())
                }

            provider_config = self.providers[provider]

            # Route to appropriate provider
            if provider == "twilio":
                return await self._send_twilio_sms(sms, provider_config, context)
            elif provider == "africastalking":
                return await self._send_africastalking_sms(sms, provider_config, context)
            elif provider == "hubtel":
                return await self._send_hubtel_sms(sms, provider_config, context)
            elif provider == "termii":
                return await self._send_termii_sms(sms, provider_config, context)
            else:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' handler not implemented"
                }

        except Exception as e:
            logger.error(f"Error sending SMS via {provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    async def _send_twilio_sms(
        self,
        sms: SMSMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS through Twilio."""
        try:
            import base64

            account_sid = config.get("account_sid")
            auth_token = config.get("auth_token")
            from_number = sms.from_number or config.get("from_number")

            # Twilio API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

            # Basic auth credentials
            credentials = f"{account_sid}:{auth_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Basic {encoded_credentials}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "To": sms.to_number,
                        "From": from_number,
                        "Body": sms.message
                    },
                    timeout=30.0
                )

                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Twilio SMS sent to {sms.to_number}: {result.get('sid')}")
                    return {
                        "success": True,
                        "provider": "twilio",
                        "message_id": result.get("sid"),
                        "to_number": sms.to_number,
                        "status": result.get("status"),
                        "sent_at": datetime.now().isoformat()
                    }
                else:
                    error_data = response.json()
                    return {
                        "success": False,
                        "provider": "twilio",
                        "error": error_data.get("message", "Unknown error"),
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return {"success": False, "error": str(e), "provider": "twilio"}

    async def _send_africastalking_sms(
        self,
        sms: SMSMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS through Africa's Talking."""
        try:
            api_key = config.get("api_key")
            username = config.get("username")
            from_id = sms.from_number or config.get("from_id", "KasaAI")

            url = "https://api.africastalking.com/version1/messaging"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "apiKey": api_key,
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "username": username,
                        "to": sms.to_number,
                        "message": sms.message,
                        "from": from_id
                    },
                    timeout=30.0
                )

                if response.status_code == 201:
                    result = response.json()
                    recipients = result.get("SMSMessageData", {}).get("Recipients", [])

                    if recipients and recipients[0].get("status") == "Success":
                        logger.info(f"Africa's Talking SMS sent to {sms.to_number}")
                        return {
                            "success": True,
                            "provider": "africastalking",
                            "message_id": recipients[0].get("messageId"),
                            "to_number": sms.to_number,
                            "status": "sent",
                            "sent_at": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "success": False,
                            "provider": "africastalking",
                            "error": recipients[0].get("status") if recipients else "Unknown error"
                        }
                else:
                    return {
                        "success": False,
                        "provider": "africastalking",
                        "error": "Failed to send SMS",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Africa's Talking SMS error: {e}")
            return {"success": False, "error": str(e), "provider": "africastalking"}

    async def _send_hubtel_sms(
        self,
        sms: SMSMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS through Hubtel (Ghana)."""
        try:
            import base64

            client_id = config.get("client_id")
            client_secret = config.get("client_secret")
            from_id = sms.from_number or config.get("from_id", "KasaAI")

            url = "https://api.hubtel.com/v1/messages/send"

            # Basic auth
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Basic {encoded_credentials}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "From": from_id,
                        "To": sms.to_number,
                        "Content": sms.message
                    },
                    timeout=30.0
                )

                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    logger.info(f"Hubtel SMS sent to {sms.to_number}")
                    return {
                        "success": True,
                        "provider": "hubtel",
                        "message_id": result.get("MessageId"),
                        "to_number": sms.to_number,
                        "status": "sent",
                        "sent_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "provider": "hubtel",
                        "error": response.text,
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Hubtel SMS error: {e}")
            return {"success": False, "error": str(e), "provider": "hubtel"}

    async def _send_termii_sms(
        self,
        sms: SMSMessage,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS through Termii."""
        try:
            api_key = config.get("api_key")
            from_id = sms.from_number or config.get("from_id", "KasaAI")
            channel = config.get("channel", "generic")

            url = "https://api.ng.termii.com/api/sms/send"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "to": sms.to_number,
                        "from": from_id,
                        "sms": sms.message,
                        "type": "plain",
                        "channel": channel,
                        "api_key": api_key
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Termii SMS sent to {sms.to_number}")
                    return {
                        "success": True,
                        "provider": "termii",
                        "message_id": result.get("message_id"),
                        "to_number": sms.to_number,
                        "status": "sent",
                        "sent_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "provider": "termii",
                        "error": response.text,
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Termii SMS error: {e}")
            return {"success": False, "error": str(e), "provider": "termii"}

    async def send_bulk_sms(
        self,
        provider: str,
        messages: List[SMSMessage],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Send multiple SMS messages in batches.

        Args:
            provider: Provider name
            messages: List of SMS messages
            batch_size: Number of messages per batch

        Returns:
            Bulk send result
        """
        try:
            if provider not in self.providers:
                return {
                    "success": False,
                    "error": f"Provider '{provider}' not configured"
                }

            results = []
            total_messages = len(messages)
            successful = 0
            failed = 0

            for i in range(0, total_messages, batch_size):
                batch = messages[i:i + batch_size]
                batch_results = []

                for message in batch:
                    result = await self.send_sms(provider, message)
                    batch_results.append(result)

                    if result.get("success"):
                        successful += 1
                    else:
                        failed += 1

                results.extend(batch_results)

                # Brief pause between batches
                if i + batch_size < total_messages:
                    await asyncio.sleep(1)

            return {
                "success": True,
                "total_messages": total_messages,
                "successful": successful,
                "failed": failed,
                "success_rate": (successful / total_messages) * 100 if total_messages > 0 else 0,
                "results": results,
                "completed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Bulk SMS error: {e}")
            return {"success": False, "error": str(e)}

    def get_supported_providers(self) -> List[str]:
        """Get list of supported SMS providers."""
        return list(self.providers.keys())


# Global SMS service instance
# Configure based on environment variables or config
sms_service = SMSService({
    # For now, we'll configure Africa's Talking as default for Ghana/Kenya/Nigeria
    "africastalking_enabled": True,
    "africastalking_api_key": "your_api_key_here",  # Should be in environment
    "africastalking_username": "sandbox",  # or production username
    "africastalking_from_id": "KasaAI"
})

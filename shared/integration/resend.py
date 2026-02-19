"""
Resend Integration Service.
Handles Resend email sending, domain management, and webhook functionality.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field
import json
import requests
import hashlib
import hmac

logger = logging.getLogger(__name__)

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend library not available. Install with: pip install resend")


@dataclass
class ResendConfig:
    """Configuration for Resend integration."""
    api_key: str
    base_url: str = "https://api.resend.com"
    timeout: int = 30
    verify_ssl: bool = True
    webhook_secret: Optional[str] = None


@dataclass
class ResendEmail:
    """Resend email data model."""
    from_: str  # Using from_ to avoid Python keyword conflict
    to: List[str]
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[Dict[str, str]]] = None
    headers: Optional[Dict[str, str]] = None
    scheduled_at: Optional[str] = None


@dataclass
class ResendDomain:
    """Resend domain data model."""
    name: str
    region: Optional[str] = "us-east-1"
    id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    records: Optional[List[Dict[str, Any]]] = None


@dataclass
class ResendContact:
    """Resend contact data model."""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    unsubscribed: bool = False
    id: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class ResendResponse:
    """Resend API response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    email_id: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class ResendIntegration:
    """
    Comprehensive Resend integration service.
    Provides email sending, domain management, contact management, and webhook functionality.
    """

    def __init__(self, config: ResendConfig):
        """
        Initialize Resend integration.

        Args:
            config: Resend configuration
        """
        self.config = config
        self._connected = False
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'KasaAI-Resend-Integration/1.0'
        })

        try:
            # Initialize resend library if available
            if RESEND_AVAILABLE and self.config.api_key:
                resend.api_key = self.config.api_key
                self._connected = True
                logger.info("Resend integration initialized successfully")
            elif self.config.api_key:
                self._connected = True
                logger.info("Resend integration initialized with HTTP client")
            else:
                logger.warning("Resend integration initialized without API key")
        except Exception as e:
            logger.error(f"Failed to initialize Resend client: {e}")
            self._connected = False

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> ResendResponse:
        """Make HTTP request to Resend API."""
        if not self._connected:
            return ResendResponse(
                success=False,
                error="Resend not connected"
            )

        try:
            url = f"{self.config.base_url}/{endpoint}"

            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )

            response_data = None
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"text": response.text}

            if response.status_code >= 200 and response.status_code < 300:
                return ResendResponse(
                    success=True,
                    data=response_data,
                    email_id=response_data.get("id") if isinstance(response_data, dict) else None,
                    status_code=response.status_code
                )
            else:
                error_message = "Unknown error"
                if response_data and isinstance(response_data, dict):
                    error_message = (
                        response_data.get('message') or
                        response_data.get('error') or
                        str(response_data)
                    )

                return ResendResponse(
                    success=False,
                    error=error_message,
                    status_code=response.status_code,
                    data=response_data
                )

        except requests.RequestException as e:
            logger.error(f"Resend API request failed: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in Resend request: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    # Email Methods
    async def send_email(self, email: ResendEmail) -> ResendResponse:
        """
        Send a single email.

        Args:
            email: Email configuration

        Returns:
            ResendResponse: Email sending response
        """
        try:
            # Use native library if available
            if RESEND_AVAILABLE:
                params = {
                    "from": email.from_,
                    "to": email.to,
                    "subject": email.subject
                }

                if email.html:
                    params["html"] = email.html
                if email.text:
                    params["text"] = email.text
                if email.cc:
                    params["cc"] = email.cc
                if email.bcc:
                    params["bcc"] = email.bcc
                if email.reply_to:
                    params["reply_to"] = email.reply_to
                if email.attachments:
                    params["attachments"] = email.attachments
                if email.tags:
                    params["tags"] = email.tags
                if email.headers:
                    params["headers"] = email.headers

                result = resend.Emails.send(params)

                return ResendResponse(
                    success=True,
                    data={"id": result.id} if hasattr(result, 'id') else {"result": str(result)},
                    email_id=result.id if hasattr(result, 'id') else None
                )
            else:
                # Use HTTP API
                data = {
                    "from": email.from_,
                    "to": email.to,
                    "subject": email.subject
                }

                if email.html:
                    data["html"] = email.html
                if email.text:
                    data["text"] = email.text
                if email.cc:
                    data["cc"] = email.cc
                if email.bcc:
                    data["bcc"] = email.bcc
                if email.reply_to:
                    data["reply_to"] = email.reply_to
                if email.attachments:
                    data["attachments"] = email.attachments
                if email.tags:
                    data["tags"] = email.tags
                if email.headers:
                    data["headers"] = email.headers
                if email.scheduled_at:
                    data["scheduled_at"] = email.scheduled_at

                return await self._make_request("POST", "emails", data)

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def send_batch_emails(self, emails: List[ResendEmail]) -> ResendResponse:
        """
        Send multiple emails in a batch (up to 100).

        Args:
            emails: List of email configurations

        Returns:
            ResendResponse: Batch sending response
        """
        try:
            if len(emails) > 100:
                return ResendResponse(
                    success=False,
                    error="Batch size cannot exceed 100 emails"
                )

            # Prepare batch data
            batch_data = []
            for email in emails:
                email_data = {
                    "from": email.from_,
                    "to": email.to,
                    "subject": email.subject
                }

                if email.html:
                    email_data["html"] = email.html
                if email.text:
                    email_data["text"] = email.text
                if email.cc:
                    email_data["cc"] = email.cc
                if email.bcc:
                    email_data["bcc"] = email.bcc
                if email.reply_to:
                    email_data["reply_to"] = email.reply_to
                if email.attachments:
                    email_data["attachments"] = email.attachments
                if email.tags:
                    email_data["tags"] = email.tags
                if email.headers:
                    email_data["headers"] = email.headers

                batch_data.append(email_data)

            return await self._make_request("POST", "emails/batch", batch_data)

        except Exception as e:
            logger.error(f"Error sending batch emails: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def get_email_details(self, email_id: str) -> ResendResponse:
        """
        Get email details by ID.

        Args:
            email_id: Email ID

        Returns:
            ResendResponse: Email details
        """
        try:
            return await self._make_request("GET", f"emails/{email_id}")

        except Exception as e:
            logger.error(f"Error getting email details: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def cancel_email(self, email_id: str) -> ResendResponse:
        """
        Cancel a scheduled email.

        Args:
            email_id: Email ID

        Returns:
            ResendResponse: Cancellation response
        """
        try:
            return await self._make_request("POST", f"emails/{email_id}/cancel")

        except Exception as e:
            logger.error(f"Error canceling email: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    # Domain Methods
    async def create_domain(self, domain: ResendDomain) -> ResendResponse:
        """
        Create a new domain.

        Args:
            domain: Domain configuration

        Returns:
            ResendResponse: Domain creation response
        """
        try:
            data = {
                "name": domain.name,
                "region": domain.region or "us-east-1"
            }

            return await self._make_request("POST", "domains", data)

        except Exception as e:
            logger.error(f"Error creating domain: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def get_domain(self, domain_id: str) -> ResendResponse:
        """
        Get domain details by ID.

        Args:
            domain_id: Domain ID

        Returns:
            ResendResponse: Domain details
        """
        try:
            return await self._make_request("GET", f"domains/{domain_id}")

        except Exception as e:
            logger.error(f"Error getting domain: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def list_domains(self) -> ResendResponse:
        """
        List all domains.

        Returns:
            ResendResponse: Domains list
        """
        try:
            return await self._make_request("GET", "domains")

        except Exception as e:
            logger.error(f"Error listing domains: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def delete_domain(self, domain_id: str) -> ResendResponse:
        """
        Delete a domain.

        Args:
            domain_id: Domain ID

        Returns:
            ResendResponse: Deletion response
        """
        try:
            return await self._make_request("DELETE", f"domains/{domain_id}")

        except Exception as e:
            logger.error(f"Error deleting domain: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def verify_domain(self, domain_id: str) -> ResendResponse:
        """
        Verify a domain.

        Args:
            domain_id: Domain ID

        Returns:
            ResendResponse: Verification response
        """
        try:
            return await self._make_request("POST", f"domains/{domain_id}/verify")

        except Exception as e:
            logger.error(f"Error verifying domain: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    # Contact and Audience Methods
    async def create_contact(self, audience_id: str, contact: ResendContact) -> ResendResponse:
        """
        Create a new contact in an audience.

        Args:
            audience_id: Audience ID
            contact: Contact configuration

        Returns:
            ResendResponse: Contact creation response
        """
        try:
            data = {
                "email": contact.email,
                "unsubscribed": contact.unsubscribed
            }

            if contact.first_name:
                data["first_name"] = contact.first_name
            if contact.last_name:
                data["last_name"] = contact.last_name

            return await self._make_request("POST", f"audiences/{audience_id}/contacts", data)

        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def get_contact(self, audience_id: str, contact_id: str) -> ResendResponse:
        """
        Get contact details.

        Args:
            audience_id: Audience ID
            contact_id: Contact ID

        Returns:
            ResendResponse: Contact details
        """
        try:
            return await self._make_request("GET", f"audiences/{audience_id}/contacts/{contact_id}")

        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def list_contacts(self, audience_id: str) -> ResendResponse:
        """
        List contacts in an audience.

        Args:
            audience_id: Audience ID

        Returns:
            ResendResponse: Contacts list
        """
        try:
            return await self._make_request("GET", f"audiences/{audience_id}/contacts")

        except Exception as e:
            logger.error(f"Error listing contacts: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def delete_contact(self, audience_id: str, contact_id: str) -> ResendResponse:
        """
        Delete a contact.

        Args:
            audience_id: Audience ID
            contact_id: Contact ID

        Returns:
            ResendResponse: Deletion response
        """
        try:
            return await self._make_request("DELETE", f"audiences/{audience_id}/contacts/{contact_id}")

        except Exception as e:
            logger.error(f"Error deleting contact: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    # Webhook Methods
    async def create_webhook(
        self,
        endpoint: str,
        events: List[str]
    ) -> ResendResponse:
        """
        Create a webhook.

        Args:
            endpoint: Webhook endpoint URL
            events: List of events to subscribe to

        Returns:
            ResendResponse: Webhook creation response
        """
        try:
            data = {
                "endpoint": endpoint,
                "events": events
            }

            return await self._make_request("POST", "webhooks", data)

        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def list_webhooks(self) -> ResendResponse:
        """
        List all webhooks.

        Returns:
            ResendResponse: Webhooks list
        """
        try:
            return await self._make_request("GET", "webhooks")

        except Exception as e:
            logger.error(f"Error listing webhooks: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def delete_webhook(self, webhook_id: str) -> ResendResponse:
        """
        Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            ResendResponse: Deletion response
        """
        try:
            return await self._make_request("DELETE", f"webhooks/{webhook_id}")

        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    def validate_webhook_signature(
        self,
        payload: str,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Validate webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            timestamp: Webhook timestamp

        Returns:
            bool: Signature validity
        """
        try:
            if not self.config.webhook_secret:
                logger.warning("No webhook secret configured")
                return False

            # Create expected signature
            signed_payload = f"{timestamp}.{payload}"
            expected_signature = hmac.new(
                self.config.webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(f"sha256={expected_signature}", signature)

        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False

    # API Keys Methods
    async def create_api_key(self, name: str, permission: str = "full_access") -> ResendResponse:
        """
        Create an API key.

        Args:
            name: API key name
            permission: Permission level (full_access or sending_access)

        Returns:
            ResendResponse: API key creation response
        """
        try:
            data = {
                "name": name,
                "permission": permission
            }

            return await self._make_request("POST", "api-keys", data)

        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def list_api_keys(self) -> ResendResponse:
        """
        List all API keys.

        Returns:
            ResendResponse: API keys list
        """
        try:
            return await self._make_request("GET", "api-keys")

        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    async def delete_api_key(self, api_key_id: str) -> ResendResponse:
        """
        Delete an API key.

        Args:
            api_key_id: API key ID

        Returns:
            ResendResponse: Deletion response
        """
        try:
            return await self._make_request("DELETE", f"api-keys/{api_key_id}")

        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return ResendResponse(
                success=False,
                error=str(e)
            )

    # Utility Methods
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Dict[str, Any]: Health status
        """
        try:
            # Test with domains endpoint
            response = await self.list_domains()

            return {
                "status": "healthy" if response.success else "degraded",
                "connected": self._connected,
                "library_available": RESEND_AVAILABLE,
                "api_key_configured": bool(self.config.api_key),
                "base_url": self.config.base_url,
                "test_result": response.data if response.success else response.error
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get service capabilities.

        Returns:
            Dict[str, Any]: Service capabilities
        """
        capabilities = [
            "send_email", "send_batch_emails", "get_email_details", "cancel_email",
            "create_domain", "get_domain", "list_domains", "delete_domain", "verify_domain",
            "create_contact", "get_contact", "list_contacts", "delete_contact",
            "create_webhook", "list_webhooks", "delete_webhook", "validate_webhook_signature",
            "create_api_key", "list_api_keys", "delete_api_key",
            "health_check"
        ]

        return {
            "service": "resend",
            "capabilities": capabilities,
            "connected": self._connected,
            "library_available": RESEND_AVAILABLE,
            "email_sending": True,
            "batch_sending": True,
            "domain_management": True,
            "contact_management": True,
            "webhook_support": True,
            "api_key_management": True,
            "scheduled_emails": True,
            "attachments": True,
            "api_reference": "https://resend.com/docs/api-reference",
            "documentation": "https://resend.com/docs",
            "mcp_available": True  # MCP server available for Resend
        }
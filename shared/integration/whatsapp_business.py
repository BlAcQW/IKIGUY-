"""
WhatsApp Business Integration Module

This module provides integration with WhatsApp Business API for advanced messaging,
template messages, media sharing, and interactive message capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    WHATSAPP_BUSINESS_AVAILABLE = True
except ImportError:
    WHATSAPP_BUSINESS_AVAILABLE = False
    logging.warning("WhatsApp Business APIs not available. Install requests")

logger = logging.getLogger(__name__)


class WhatsAppMessageType(Enum):
    """WhatsApp message types."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"
    STICKER = "sticker"


class WhatsAppTemplateStatus(Enum):
    """WhatsApp template status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISABLED = "disabled"


class WhatsAppInteractiveType(Enum):
    """WhatsApp interactive message types."""
    BUTTON = "button"
    LIST = "list"
    PRODUCT = "product"
    PRODUCT_LIST = "product_list"


class WhatsAppButtonType(Enum):
    """WhatsApp button types."""
    REPLY = "reply"
    URL = "url"
    PHONE_NUMBER = "phone_number"
    COPY_CODE = "copy_code"


@dataclass
class WhatsAppBusinessConfig:
    """Configuration for WhatsApp Business integration."""
    
    access_token: str
    """WhatsApp Business API access token."""
    
    phone_number_id: str
    """Phone number ID."""
    
    business_account_id: str
    """Business account ID."""
    
    api_version: str = "v18.0"
    """API version."""
    
    base_url: str = "https://graph.facebook.com"
    """Base URL for API calls."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    webhook_verify_token: Optional[str] = None
    """Webhook verification token."""
    
    webhook_secret: Optional[str] = None
    """Webhook secret for signature verification."""


@dataclass
class WhatsAppMedia:
    """WhatsApp media data structure."""
    
    mime_type: str
    """MIME type."""
    
    id: Optional[str] = None
    """Media ID."""
    
    url: Optional[str] = None
    """Media URL."""
    
    sha256: Optional[str] = None
    """SHA256 hash."""
    
    file_size: Optional[int] = None
    """File size in bytes."""
    
    filename: Optional[str] = None
    """Filename."""
    
    caption: Optional[str] = None
    """Media caption."""


@dataclass
class WhatsAppButton:
    """WhatsApp button data structure."""
    
    type: WhatsAppButtonType
    """Button type."""
    
    title: str
    """Button title."""
    
    payload: Optional[str] = None
    """Button payload."""
    
    url: Optional[str] = None
    """Button URL."""
    
    phone_number: Optional[str] = None
    """Phone number for call button."""


@dataclass
class WhatsAppInteractive:
    """WhatsApp interactive message data structure."""

    type: WhatsAppInteractiveType
    """Interactive type."""

    body: Dict[str, Any]
    """Message body."""

    action: Dict[str, Any]
    """Interactive action."""

    header: Optional[Dict[str, Any]] = None
    """Message header."""

    footer: Optional[Dict[str, Any]] = None
    """Message footer."""

    buttons: Optional[List[WhatsAppButton]] = None
    """List of buttons."""


@dataclass
class WhatsAppTemplate:
    """WhatsApp template data structure."""
    
    name: str
    """Template name."""
    
    language: str
    """Template language."""
    
    category: str
    """Template category."""
    
    components: List[Dict[str, Any]] = field(default_factory=list)
    """Template components."""
    
    status: WhatsAppTemplateStatus = WhatsAppTemplateStatus.PENDING
    """Template status."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class WhatsAppMessage:
    """WhatsApp message data structure."""

    from_number: str
    """Sender phone number."""

    to_number: str
    """Recipient phone number."""

    message_type: WhatsAppMessageType
    """Message type."""

    id: Optional[str] = None
    """Message ID."""

    text: Optional[str] = None
    """Message text."""

    media: Optional[WhatsAppMedia] = None
    """Message media."""

    template: Optional[WhatsAppTemplate] = None
    """Message template."""

    interactive: Optional[WhatsAppInteractive] = None
    """Interactive message."""

    timestamp: Optional[datetime] = None
    """Message timestamp."""

    status: Optional[str] = None
    """Message status."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Message metadata."""


@dataclass
class WhatsAppWebhookEvent:
    """WhatsApp webhook event data structure."""
    
    object: str
    """Event object."""
    
    entry: List[Dict[str, Any]]
    """Event entries."""
    
    timestamp: Optional[datetime] = None
    """Event timestamp."""
    
    signature: Optional[str] = None
    """Event signature."""


class WhatsAppBusinessIntegration:
    """WhatsApp Business integration for advanced messaging capabilities."""
    
    def __init__(self, config: WhatsAppBusinessConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json"
        })
        
        self.api_url = f"{config.base_url}/{config.api_version}"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the WhatsApp Business API."""
        try:
            url = f"{self.api_url}/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    async def send_text_message(
        self,
        to_number: str,
        text: str,
        preview_url: Optional[bool] = None
    ) -> WhatsAppMessage:
        """
        Send a text message.
        
        Args:
            to_number: Recipient phone number
            text: Message text
            preview_url: Enable URL preview
            
        Returns:
            Message data
        """
        try:
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": text
                }
            }
            
            if preview_url is not None:
                data["text"]["preview_url"] = preview_url
            
            result = self._make_request("POST", f"{self.config.phone_number_id}/messages", data)
            
            return WhatsAppMessage(
                id=result.get("messages", [{}])[0].get("id"),
                from_number=self.config.phone_number_id,
                to_number=to_number,
                message_type=WhatsAppMessageType.TEXT,
                text=text,
                timestamp=datetime.now(),
                status="sent"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send text message: {e}")
            raise
    
    async def send_media_message(
        self,
        to_number: str,
        media: WhatsAppMedia
    ) -> WhatsAppMessage:
        """
        Send a media message.
        
        Args:
            to_number: Recipient phone number
            media: Media data
            
        Returns:
            Message data
        """
        try:
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": media.mime_type.split("/")[0],
                media.mime_type.split("/")[0]: {
                    "id": media.id
                }
            }
            
            if media.caption:
                data[media.mime_type.split("/")[0]]["caption"] = media.caption
            
            result = self._make_request("POST", f"{self.config.phone_number_id}/messages", data)
            
            return WhatsAppMessage(
                id=result.get("messages", [{}])[0].get("id"),
                from_number=self.config.phone_number_id,
                to_number=to_number,
                message_type=WhatsAppMessageType(media.mime_type.split("/")[0]),
                media=media,
                timestamp=datetime.now(),
                status="sent"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send media message: {e}")
            raise
    
    async def send_template_message(
        self,
        to_number: str,
        template: WhatsAppTemplate,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> WhatsAppMessage:
        """
        Send a template message.
        
        Args:
            to_number: Recipient phone number
            template: Template data
            components: Template components
            
        Returns:
            Message data
        """
        try:
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template.name,
                    "language": {
                        "code": template.language
                    }
                }
            }
            
            if components:
                data["template"]["components"] = components
            
            result = self._make_request("POST", f"{self.config.phone_number_id}/messages", data)
            
            return WhatsAppMessage(
                id=result.get("messages", [{}])[0].get("id"),
                from_number=self.config.phone_number_id,
                to_number=to_number,
                message_type=WhatsAppMessageType.TEMPLATE,
                template=template,
                timestamp=datetime.now(),
                status="sent"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send template message: {e}")
            raise
    
    async def send_interactive_message(
        self,
        to_number: str,
        interactive: WhatsAppInteractive
    ) -> WhatsAppMessage:
        """
        Send an interactive message.
        
        Args:
            to_number: Recipient phone number
            interactive: Interactive message data
            
        Returns:
            Message data
        """
        try:
            data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "interactive",
                "interactive": {
                    "type": interactive.type.value,
                    "body": interactive.body,
                    "action": interactive.action
                }
            }
            
            if interactive.header:
                data["interactive"]["header"] = interactive.header
            if interactive.footer:
                data["interactive"]["footer"] = interactive.footer
            
            result = self._make_request("POST", f"{self.config.phone_number_id}/messages", data)
            
            return WhatsAppMessage(
                id=result.get("messages", [{}])[0].get("id"),
                from_number=self.config.phone_number_id,
                to_number=to_number,
                message_type=WhatsAppMessageType.INTERACTIVE,
                interactive=interactive,
                timestamp=datetime.now(),
                status="sent"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send interactive message: {e}")
            raise
    
    async def upload_media(
        self,
        file_path: str,
        mime_type: str
    ) -> WhatsAppMedia:
        """
        Upload media to WhatsApp.
        
        Args:
            file_path: Path to media file
            mime_type: MIME type of the file
            
        Returns:
            Media data
        """
        try:
            with open(file_path, "rb") as file:
                files = {"file": file}
                data = {"messaging_product": "whatsapp"}
                
                response = self.session.post(
                    f"{self.api_url}/{self.config.phone_number_id}/media",
                    data=data,
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                
                return WhatsAppMedia(
                    id=result.get("id"),
                    mime_type=mime_type
                )
                
        except Exception as e:
            self.logger.error(f"Failed to upload media: {e}")
            raise
    
    async def get_media(self, media_id: str) -> WhatsAppMedia:
        """
        Get media information.
        
        Args:
            media_id: Media ID
            
        Returns:
            Media data
        """
        try:
            result = self._make_request("GET", media_id)
            
            return WhatsAppMedia(
                id=result.get("id"),
                url=result.get("url"),
                mime_type=result.get("mime_type"),
                sha256=result.get("sha256"),
                file_size=result.get("file_size")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get media: {e}")
            raise
    
    async def download_media(self, media_id: str, output_path: str) -> bool:
        """
        Download media file.
        
        Args:
            media_id: Media ID
            output_path: Output file path
            
        Returns:
            Success status
        """
        try:
            media = await self.get_media(media_id)
            
            if not media.url:
                raise ValueError("Media URL not available")
            
            response = self.session.get(media.url)
            response.raise_for_status()
            
            with open(output_path, "wb") as file:
                file.write(response.content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download media: {e}")
            raise
    
    async def create_template(
        self,
        name: str,
        language: str,
        category: str,
        components: List[Dict[str, Any]]
    ) -> WhatsAppTemplate:
        """
        Create a message template.
        
        Args:
            name: Template name
            language: Template language
            category: Template category
            components: Template components
            
        Returns:
            Template data
        """
        try:
            data = {
                "name": name,
                "language": language,
                "category": category,
                "components": components
            }
            
            result = self._make_request("POST", f"{self.config.phone_number_id}/message_templates", data)
            
            return WhatsAppTemplate(
                name=result.get("name"),
                language=result.get("language"),
                category=result.get("category"),
                components=result.get("components", []),
                status=WhatsAppTemplateStatus(result.get("status", "pending")),
                created_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create template: {e}")
            raise
    
    async def get_templates(self) -> List[WhatsAppTemplate]:
        """
        Get message templates.
        
        Returns:
            List of templates
        """
        try:
            result = self._make_request("GET", f"{self.config.phone_number_id}/message_templates")
            
            templates = []
            for item in result.get("data", []):
                template = WhatsAppTemplate(
                    name=item.get("name"),
                    language=item.get("language"),
                    category=item.get("category"),
                    components=item.get("components", []),
                    status=WhatsAppTemplateStatus(item.get("status", "pending")),
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")) if item.get("created_at") else None,
                    updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")) if item.get("updated_at") else None
                )
                templates.append(template)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to get templates: {e}")
            raise
    
    async def delete_template(self, template_name: str) -> bool:
        """
        Delete a message template.
        
        Args:
            template_name: Template name
            
        Returns:
            Success status
        """
        try:
            self._make_request("DELETE", f"{template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete template: {e}")
            raise
    
    async def get_phone_numbers(self) -> List[Dict[str, Any]]:
        """
        Get phone numbers.
        
        Returns:
            List of phone numbers
        """
        try:
            result = self._make_request("GET", f"{self.config.business_account_id}/phone_numbers")
            
            return result.get("data", [])
            
        except Exception as e:
            self.logger.error(f"Failed to get phone numbers: {e}")
            raise
    
    async def get_business_profile(self) -> Dict[str, Any]:
        """
        Get business profile.
        
        Returns:
            Business profile data
        """
        try:
            result = self._make_request("GET", f"{self.config.phone_number_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get business profile: {e}")
            raise
    
    async def update_business_profile(
        self,
        messaging_product: str = "whatsapp",
        about: Optional[str] = None,
        address: Optional[str] = None,
        description: Optional[str] = None,
        email: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        websites: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update business profile.
        
        Args:
            messaging_product: Messaging product
            about: About text
            address: Business address
            description: Business description
            email: Business email
            profile_picture_url: Profile picture URL
            websites: Business websites
            
        Returns:
            Updated profile data
        """
        try:
            data = {"messaging_product": messaging_product}
            
            if about:
                data["about"] = about
            if address:
                data["address"] = address
            if description:
                data["description"] = description
            if email:
                data["email"] = email
            if profile_picture_url:
                data["profile_picture_url"] = profile_picture_url
            if websites:
                data["websites"] = websites
            
            result = self._make_request("POST", f"{self.config.phone_number_id}", data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to update business profile: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the WhatsApp Business integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting business profile
            profile = await self.get_business_profile()
            
            return {
                "status": "healthy",
                "phone_number_id": self.config.phone_number_id,
                "business_account_id": self.config.business_account_id,
                "api_version": self.config.api_version,
                "business_name": profile.get("verified_name"),
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


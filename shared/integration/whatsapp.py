"""
WhatsApp Business Integration System

This module provides WhatsApp Business integration capabilities for the KasaAI platform.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Third-party imports (would be added to requirements.txt)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class WhatsAppMessageType(Enum):
    """Supported WhatsApp message types"""
    TEXT = "text"
    TEMPLATE = "template"
    MEDIA = "media"
    INTERACTIVE = "interactive"
    LOCATION = "location"
    CONTACTS = "contacts"


@dataclass
class WhatsAppButton:
    """WhatsApp button definition"""
    button_id: str
    title: str
    button_type: str = "reply"  # reply, url, phone_number


@dataclass
class WhatsAppMedia:
    """WhatsApp media definition"""
    media_url: str
    media_type: str  # image, video, audio, document
    caption: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class WhatsAppTemplate:
    """WhatsApp template definition"""
    template_name: str
    language: str = "en"
    components: List[Dict[str, Any]] = None


@dataclass
class WhatsAppDeliveryReport:
    """WhatsApp delivery report"""
    message_id: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    provider_response: Optional[str] = None


class WhatsAppIntegration:
    """WhatsApp Business integration class"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize WhatsApp integration"""
        self.config = config
        self.logger = logging.getLogger("WhatsAppIntegration")
        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = config.get("phone_number_id")
        self.access_token = config.get("access_token")
        self.verify_token = config.get("verify_token")
        
        if not REQUESTS_AVAILABLE:
            self.logger.warning("Requests library not available. WhatsApp integration will be limited.")
    
    async def send_message(self, to: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        """Send a WhatsApp message"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Requests library not available",
                "provider": "whatsapp"
            }
        
        try:
            if message_type == WhatsAppMessageType.TEXT.value:
                return await self._send_text_message(to, message)
            elif message_type == WhatsAppMessageType.TEMPLATE.value:
                return await self._send_template_message(to, message)
            elif message_type == WhatsAppMessageType.MEDIA.value:
                return await self._send_media_message(to, message)
            elif message_type == WhatsAppMessageType.INTERACTIVE.value:
                return await self._send_interactive_message(to, message)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported message type: {message_type}",
                    "provider": "whatsapp"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "whatsapp"
            }
    
    async def send_template_message(self, template_name: str, to: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send a WhatsApp template message"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Requests library not available",
                "provider": "whatsapp"
            }
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Prepare template components
            components = []
            if variables:
                body_components = []
                for key, value in variables.items():
                    body_components.append({
                        "type": "text",
                        "text": str(value)
                    })
                
                if body_components:
                    components.append({
                        "type": "body",
                        "parameters": body_components
                    })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "en"
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(url, json=payload, headers=headers)
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "provider": "whatsapp",
                    "template_name": template_name,
                    "to": to
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "whatsapp"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp template message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "whatsapp"
            }
    
    async def send_media_message(self, to: str, media_url: str, caption: str = None) -> Dict[str, Any]:
        """Send a WhatsApp media message"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Requests library not available",
                "provider": "whatsapp"
            }
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Determine media type from URL
            media_type = self._get_media_type_from_url(media_url)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: {
                    "link": media_url
                }
            }
            
            if caption:
                payload[media_type]["caption"] = caption
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(url, json=payload, headers=headers)
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "provider": "whatsapp",
                    "media_type": media_type,
                    "to": to
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "whatsapp"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp media message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "whatsapp"
            }
    
    async def send_interactive_message(self, to: str, buttons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send a WhatsApp interactive message with buttons"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Requests library not available",
                "provider": "whatsapp"
            }
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Prepare button components
            button_components = []
            for button in buttons:
                button_components.append({
                    "type": button.get("type", "reply"),
                    "reply": {
                        "id": button.get("id"),
                        "title": button.get("title")
                    }
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": "Please select an option:"
                    },
                    "action": {
                        "buttons": button_components
                    }
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(url, json=payload, headers=headers)
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "provider": "whatsapp",
                    "interactive_type": "button",
                    "to": to
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "whatsapp"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp interactive message: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "whatsapp"
            }
    
    async def receive_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming WhatsApp webhook"""
        try:
            # Extract webhook data
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Handle different types of webhooks
            if "messages" in value:
                return await self._process_message_webhook(value["messages"])
            elif "statuses" in value:
                return await self._process_status_webhook(value["statuses"])
            else:
                return {
                    "success": True,
                    "webhook_type": "unknown",
                    "provider": "whatsapp"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to process WhatsApp webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "whatsapp"
            }
    
    async def get_message_status(self, message_id: str) -> WhatsAppDeliveryReport:
        """Get WhatsApp message status"""
        if not REQUESTS_AVAILABLE:
            return WhatsAppDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response="Requests library not available"
            )
        
        try:
            url = f"{self.base_url}/{message_id}"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(url, headers=headers)
            )
            
            if response.status_code == 200:
                data = response.json()
                return WhatsAppDeliveryReport(
                    message_id=message_id,
                    status=data.get("status", "unknown"),
                    sent_at=datetime.now() if data.get("status") == "sent" else None,
                    delivered_at=datetime.now() if data.get("status") == "delivered" else None,
                    read_at=datetime.now() if data.get("status") == "read" else None
                )
            else:
                return WhatsAppDeliveryReport(
                    message_id=message_id,
                    status="error",
                    provider_response=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get WhatsApp message status: {e}")
            return WhatsAppDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response=str(e)
            )
    
    async def _send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.post(url, json=payload, headers=headers)
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message_id": data.get("messages", [{}])[0].get("id"),
                "provider": "whatsapp",
                "to": to
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "provider": "whatsapp"
            }
    
    async def _process_message_webhook(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process incoming message webhook"""
        if not messages:
            return {
                "success": True,
                "webhook_type": "message",
                "provider": "whatsapp"
            }
        
        message = messages[0]
        
        return {
            "success": True,
            "webhook_type": "message",
            "message_id": message.get("id"),
            "from": message.get("from"),
            "timestamp": message.get("timestamp"),
            "type": message.get("type"),
            "text": message.get("text", {}).get("body") if message.get("type") == "text" else None,
            "provider": "whatsapp"
        }
    
    async def _process_status_webhook(self, statuses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process status update webhook"""
        if not statuses:
            return {
                "success": True,
                "webhook_type": "status",
                "provider": "whatsapp"
            }
        
        status = statuses[0]
        
        return {
            "success": True,
            "webhook_type": "status",
            "message_id": status.get("id"),
            "status": status.get("status"),
            "timestamp": status.get("timestamp"),
            "provider": "whatsapp"
        }
    
    def _get_media_type_from_url(self, url: str) -> str:
        """Determine media type from URL"""
        url_lower = url.lower()
        
        if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            return "image"
        elif any(ext in url_lower for ext in ['.mp4', '.avi', '.mov', '.wmv']):
            return "video"
        elif any(ext in url_lower for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
            return "audio"
        elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx']):
            return "document"
        else:
            return "image"  # Default to image
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Dict[str, Any]:
        """Verify WhatsApp webhook"""
        if mode == "subscribe" and token == self.verify_token:
            return {
                "success": True,
                "challenge": challenge
            }
        else:
            return {
                "success": False,
                "error": "Invalid verification token"
            }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get available WhatsApp templates"""
        # This would typically make an API call to get templates
        # For now, return a placeholder
        return [
            {
                "name": "hello_world",
                "language": "en",
                "status": "APPROVED"
            },
            {
                "name": "appointment_reminder",
                "language": "en",
                "status": "APPROVED"
            }
        ]
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get WhatsApp Business account information"""
        return {
            "phone_number_id": self.phone_number_id,
            "base_url": self.base_url,
            "provider": "whatsapp"
        }

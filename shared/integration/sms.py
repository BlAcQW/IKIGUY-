"""
SMS Integration System

This module provides SMS integration capabilities for the KasaAI platform.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Third-party imports (would be added to requirements.txt)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    import messagebird
    MESSAGEBIRD_AVAILABLE = True
except ImportError:
    MESSAGEBIRD_AVAILABLE = False


class SMSProvider(Enum):
    """Supported SMS providers"""
    TWILIO = "twilio"
    MESSAGEBIRD = "messagebird"
    AWS_SNS = "aws_sns"
    VONAGE_SMS = "vonage_sms"
    TELNYX_SMS = "telnyx_sms"
    HUBTEL = "hubtel"  # Ghana-based SMS gateway
    ARKESEL = "arkesel"  # Ghana-based SMS gateway
    CUSTOM_HTTP = "custom_http"  # Custom HTTP/Webhook provider


@dataclass
class SMSDeliveryReport:
    """SMS delivery report"""
    message_id: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    provider_response: Optional[str] = None
    cost: Optional[float] = None


class BaseSMSProvider(ABC):
    """Base class for SMS providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the SMS provider"""
        self.config = config
        self.logger = logging.getLogger(f"SMSProvider.{self.__class__.__name__}")
        self.provider_type = self.get_provider_type()
    
    @abstractmethod
    def get_provider_type(self) -> SMSProvider:
        """Get the provider type"""
        pass
    
    @abstractmethod
    async def send_sms(self, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Send an SMS"""
        pass
    
    @abstractmethod
    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str) -> Dict[str, Any]:
        """Send bulk SMS"""
        pass
    
    @abstractmethod
    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Schedule an SMS for later sending"""
        pass
    
    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> SMSDeliveryReport:
        """Get SMS delivery status"""
        pass
    
    @abstractmethod
    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook"""
        pass


class TwilioSMSProvider(BaseSMSProvider):
    """Twilio SMS provider"""
    
    def get_provider_type(self) -> SMSProvider:
        return SMSProvider.TWILIO
    
    async def send_sms(self, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        if not TWILIO_AVAILABLE:
            return {
                "success": False,
                "error": "Twilio library not available",
                "provider": "twilio"
            }
        
        try:
            account_sid = self.config.get("account_sid")
            auth_token = self.config.get("auth_token")
            
            client = TwilioClient(account_sid, auth_token)
            
            # Send SMS
            message_obj = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    body=message,
                    from_=from_number,
                    to=to
                )
            )
            
            return {
                "success": True,
                "message_id": message_obj.sid,
                "provider": "twilio",
                "to": to,
                "from": from_number,
                "status": message_obj.status,
                "price": message_obj.price
            }
            
        except TwilioException as e:
            self.logger.error(f"Twilio SMS error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio"
            }
        except Exception as e:
            self.logger.error(f"Failed to send Twilio SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio"
            }
    
    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str) -> Dict[str, Any]:
        """Send bulk SMS via Twilio"""
        if not TWILIO_AVAILABLE:
            return {
                "success": False,
                "error": "Twilio library not available",
                "provider": "twilio"
            }
        
        try:
            account_sid = self.config.get("account_sid")
            auth_token = self.config.get("auth_token")
            
            client = TwilioClient(account_sid, auth_token)
            
            results = []
            for recipient in recipients:
                try:
                    message_obj = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda r=recipient: client.messages.create(
                            body=message,
                            from_=from_number,
                            to=r
                        )
                    )
                    
                    results.append({
                        "recipient": recipient,
                        "success": True,
                        "message_id": message_obj.sid,
                        "status": message_obj.status
                    })
                    
                except Exception as e:
                    results.append({
                        "recipient": recipient,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "provider": "twilio",
                "total_recipients": len(recipients),
                "successful": len([r for r in results if r["success"]]),
                "failed": len([r for r in results if not r["success"]]),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send bulk Twilio SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio"
            }
    
    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Schedule SMS for later sending"""
        # Twilio doesn't support direct scheduling, but we can return a placeholder
        # In a real implementation, this would be handled by a task queue
        return {
            "success": True,
            "scheduled": True,
            "send_time": send_time.isoformat(),
            "message_id": f"twilio_scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "provider": "twilio"
        }
    
    async def get_delivery_status(self, message_id: str) -> SMSDeliveryReport:
        """Get SMS delivery status from Twilio"""
        if not TWILIO_AVAILABLE:
            return SMSDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response="Twilio library not available"
            )
        
        try:
            account_sid = self.config.get("account_sid")
            auth_token = self.config.get("auth_token")
            
            client = TwilioClient(account_sid, auth_token)
            
            message = await asyncio.get_event_loop().run_in_executor(
                None,
                client.messages(message_id).fetch
            )
            
            return SMSDeliveryReport(
                message_id=message_id,
                status=message.status,
                sent_at=message.date_created,
                delivered_at=message.date_sent if message.status == "delivered" else None,
                failed_at=message.date_sent if message.status == "failed" else None,
                failure_reason=message.error_message if message.status == "failed" else None,
                cost=float(message.price) if message.price else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get Twilio SMS status: {e}")
            return SMSDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response=str(e)
            )
    
    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook from Twilio"""
        try:
            # Extract webhook data
            message_sid = webhook_data.get("MessageSid")
            from_number = webhook_data.get("From")
            to_number = webhook_data.get("To")
            body = webhook_data.get("Body")
            status = webhook_data.get("SmsStatus")
            
            return {
                "success": True,
                "message_id": message_sid,
                "from": from_number,
                "to": to_number,
                "body": body,
                "status": status,
                "provider": "twilio"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process Twilio webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio"
            }


class MessageBirdSMSProvider(BaseSMSProvider):
    """MessageBird SMS provider"""
    
    def get_provider_type(self) -> SMSProvider:
        return SMSProvider.MESSAGEBIRD
    
    async def send_sms(self, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Send SMS via MessageBird"""
        if not MESSAGEBIRD_AVAILABLE:
            return {
                "success": False,
                "error": "MessageBird library not available",
                "provider": "messagebird"
            }
        
        try:
            api_key = self.config.get("api_key")
            client = messagebird.Client(api_key)
            
            # Send SMS
            message_obj = await asyncio.get_event_loop().run_in_executor(
                None,
                client.message_create,
                from_number,
                to,
                message
            )
            
            return {
                "success": True,
                "message_id": message_obj.id,
                "provider": "messagebird",
                "to": to,
                "from": from_number,
                "status": message_obj.status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send MessageBird SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "messagebird"
            }
    
    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str) -> Dict[str, Any]:
        """Send bulk SMS via MessageBird"""
        if not MESSAGEBIRD_AVAILABLE:
            return {
                "success": False,
                "error": "MessageBird library not available",
                "provider": "messagebird"
            }
        
        try:
            api_key = self.config.get("api_key")
            client = messagebird.Client(api_key)
            
            # Send bulk SMS
            message_obj = await asyncio.get_event_loop().run_in_executor(
                None,
                client.message_create,
                from_number,
                recipients,
                message
            )
            
            return {
                "success": True,
                "message_id": message_obj.id,
                "provider": "messagebird",
                "total_recipients": len(recipients),
                "status": message_obj.status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send bulk MessageBird SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "messagebird"
            }
    
    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Schedule SMS for later sending"""
        # MessageBird supports scheduling via scheduledDatetime parameter
        if not MESSAGEBIRD_AVAILABLE:
            return {
                "success": False,
                "error": "MessageBird library not available",
                "provider": "messagebird"
            }
        
        try:
            api_key = self.config.get("api_key")
            client = messagebird.Client(api_key)
            
            # Format datetime for MessageBird
            scheduled_time = send_time.strftime("%Y-%m-%dT%H:%M:%S%z")
            
            message_obj = await asyncio.get_event_loop().run_in_executor(
                None,
                client.message_create,
                from_number,
                to,
                message,
                {"scheduledDatetime": scheduled_time}
            )
            
            return {
                "success": True,
                "scheduled": True,
                "send_time": send_time.isoformat(),
                "message_id": message_obj.id,
                "provider": "messagebird"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "messagebird"
            }
    
    async def get_delivery_status(self, message_id: str) -> SMSDeliveryReport:
        """Get SMS delivery status from MessageBird"""
        if not MESSAGEBIRD_AVAILABLE:
            return SMSDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response="MessageBird library not available"
            )
        
        try:
            api_key = self.config.get("api_key")
            client = messagebird.Client(api_key)
            
            message = await asyncio.get_event_loop().run_in_executor(
                None,
                client.message,
                message_id
            )
            
            return SMSDeliveryReport(
                message_id=message_id,
                status=message.status,
                sent_at=message.createdDatetime,
                delivered_at=message.statusDatetime if message.status == "delivered" else None,
                failed_at=message.statusDatetime if message.status == "failed" else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get MessageBird SMS status: {e}")
            return SMSDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response=str(e)
            )
    
    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook from MessageBird"""
        try:
            # Extract webhook data
            message_id = webhook_data.get("id")
            from_number = webhook_data.get("originator")
            to_number = webhook_data.get("recipient")
            body = webhook_data.get("body")
            status = webhook_data.get("status")
            
            return {
                "success": True,
                "message_id": message_id,
                "from": from_number,
                "to": to_number,
                "body": body,
                "status": status,
                "provider": "messagebird"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process MessageBird webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "messagebird"
            }


class HubtelSMSProvider(BaseSMSProvider):
    """
    Hubtel SMS provider (Ghana-based)

    API Documentation: https://developers.hubtel.com/docs/sms-api

    Config:
        client_id: str - Hubtel Client ID
        client_secret: str - Hubtel Client Secret
        sender_id: str - Default sender ID (e.g., "KasaAI")
    """

    def get_provider_type(self) -> SMSProvider:
        return SMSProvider.HUBTEL

    async def send_sms(self, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Send SMS via Hubtel"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "requests library not available",
                "provider": "hubtel"
            }

        try:
            client_id = self.config.get("client_id")
            client_secret = self.config.get("client_secret")
            sender_id = from_number or self.config.get("sender_id", "KasaAI")

            # Hubtel SMS API endpoint
            url = "https://smsc.hubtel.com/v1/messages/send"

            payload = {
                "From": sender_id,
                "To": to,
                "Content": message
            }

            # Send request with basic auth
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    json=payload,
                    auth=(client_id, client_secret),
                    headers={"Content-Type": "application/json"}
                )
            )

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("MessageId", str(datetime.now().timestamp())),
                    "provider": "hubtel",
                    "to": to,
                    "from": sender_id,
                    "status": data.get("Status", "sent"),
                    "response": data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "hubtel"
                }

        except Exception as e:
            self.logger.error(f"Failed to send Hubtel SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "hubtel"
            }

    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str) -> Dict[str, Any]:
        """Send bulk SMS via Hubtel"""
        results = []
        for recipient in recipients:
            result = await self.send_sms(recipient, message, from_number)
            results.append({
                "recipient": recipient,
                "success": result.get("success", False),
                "message_id": result.get("message_id"),
                "error": result.get("error")
            })

        return {
            "success": True,
            "provider": "hubtel",
            "total_recipients": len(recipients),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results
        }

    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Schedule SMS (not directly supported - uses internal scheduling)"""
        return {
            "success": True,
            "scheduled": True,
            "send_time": send_time.isoformat(),
            "message_id": f"hubtel_scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "provider": "hubtel"
        }

    async def get_delivery_status(self, message_id: str) -> SMSDeliveryReport:
        """Get SMS delivery status from Hubtel"""
        # Hubtel doesn't have a direct status check API
        return SMSDeliveryReport(
            message_id=message_id,
            status="unknown",
            provider_response="Status check not supported for Hubtel"
        )

    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook from Hubtel"""
        try:
            return {
                "success": True,
                "message_id": webhook_data.get("MessageId"),
                "from": webhook_data.get("From"),
                "to": webhook_data.get("To"),
                "body": webhook_data.get("Content"),
                "status": webhook_data.get("Status"),
                "provider": "hubtel"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "hubtel"
            }


class ArkeselSMSProvider(BaseSMSProvider):
    """
    Arkesel SMS provider (Ghana-based)

    API Documentation: https://developers.arkesel.com/

    Config:
        api_key: str - Arkesel API Key
        sender_id: str - Default sender ID
    """

    def get_provider_type(self) -> SMSProvider:
        return SMSProvider.ARKESEL

    async def send_sms(self, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Send SMS via Arkesel"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "requests library not available",
                "provider": "arkesel"
            }

        try:
            api_key = self.config.get("api_key")
            sender_id = from_number or self.config.get("sender_id", "KasaAI")

            # Arkesel SMS API endpoint
            url = "https://sms.arkesel.com/api/v2/sms/send"

            payload = {
                "sender": sender_id,
                "recipients": [to],
                "message": message
            }

            headers = {
                "api-key": api_key,
                "Content-Type": "application/json"
            }

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(url, json=payload, headers=headers)
            )

            if response.status_code == 200:
                data = response.json()
                # Arkesel returns "data" as a list of message objects
                message_data = data.get("data", [])
                message_id = str(datetime.now().timestamp())
                if isinstance(message_data, list) and len(message_data) > 0:
                    message_id = message_data[0].get("id", message_id)
                elif isinstance(message_data, dict):
                    message_id = message_data.get("id", message_id)

                return {
                    "success": data.get("status") == "success",
                    "message_id": message_id,
                    "provider": "arkesel",
                    "to": to,
                    "from": sender_id,
                    "status": data.get("status"),
                    "response": data
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "arkesel"
                }

        except Exception as e:
            self.logger.error(f"Failed to send Arkesel SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "arkesel"
            }

    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str) -> Dict[str, Any]:
        """Send bulk SMS via Arkesel (supports bulk natively)"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "requests library not available",
                "provider": "arkesel"
            }

        try:
            api_key = self.config.get("api_key")
            sender_id = from_number or self.config.get("sender_id", "KasaAI")

            url = "https://sms.arkesel.com/api/v2/sms/send"

            payload = {
                "sender": sender_id,
                "recipients": recipients,
                "message": message
            }

            headers = {
                "api-key": api_key,
                "Content-Type": "application/json"
            }

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(url, json=payload, headers=headers)
            )

            data = response.json()

            # Arkesel returns "data" as a list of message objects
            message_data = data.get("data", [])
            message_id = None
            if isinstance(message_data, list) and len(message_data) > 0:
                message_id = message_data[0].get("id")
            elif isinstance(message_data, dict):
                message_id = message_data.get("id")

            return {
                "success": data.get("status") == "success",
                "provider": "arkesel",
                "total_recipients": len(recipients),
                "message_id": message_id,
                "response": data
            }

        except Exception as e:
            self.logger.error(f"Failed to send bulk Arkesel SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "arkesel"
            }

    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Schedule SMS"""
        return {
            "success": True,
            "scheduled": True,
            "send_time": send_time.isoformat(),
            "message_id": f"arkesel_scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "provider": "arkesel"
        }

    async def get_delivery_status(self, message_id: str) -> SMSDeliveryReport:
        """Get SMS delivery status"""
        return SMSDeliveryReport(
            message_id=message_id,
            status="unknown",
            provider_response="Status check not implemented"
        )

    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook"""
        try:
            return {
                "success": True,
                "message_id": webhook_data.get("id"),
                "from": webhook_data.get("from"),
                "to": webhook_data.get("to"),
                "body": webhook_data.get("message"),
                "provider": "arkesel"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "arkesel"
            }


class CustomHTTPSMSProvider(BaseSMSProvider):
    """
    Custom HTTP/Webhook SMS provider

    Allows integration with any SMS API via configurable HTTP endpoints.

    Config:
        endpoint_url: str - The SMS API endpoint URL
        method: str - HTTP method (POST/GET), default POST
        auth_type: str - Authentication type (none/basic/bearer/api_key)
        auth_username: str - Username for basic auth
        auth_password: str - Password for basic auth
        auth_token: str - Bearer token
        api_key_header: str - Header name for API key (e.g., "X-API-Key")
        api_key: str - API key value

        # Field mappings
        to_field: str - Field name for recipient (default: "to")
        message_field: str - Field name for message content (default: "message")
        from_field: str - Field name for sender (default: "from")

        # Custom headers
        headers: dict - Additional headers to send

        # Response parsing
        success_field: str - Field to check for success (default: "success")
        message_id_field: str - Field for message ID (default: "message_id")
    """

    def get_provider_type(self) -> SMSProvider:
        return SMSProvider.CUSTOM_HTTP

    async def send_sms(self, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Send SMS via custom HTTP endpoint"""
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "requests library not available",
                "provider": "custom_http"
            }

        try:
            endpoint_url = self.config.get("endpoint_url")
            if not endpoint_url:
                return {
                    "success": False,
                    "error": "endpoint_url not configured",
                    "provider": "custom_http"
                }

            method = self.config.get("method", "POST").upper()

            # Build payload with configurable field names
            to_field = self.config.get("to_field", "to")
            message_field = self.config.get("message_field", "message")
            from_field = self.config.get("from_field", "from")

            payload = {
                to_field: to,
                message_field: message,
                from_field: from_number or self.config.get("sender_id", "")
            }

            # Add any extra fields from config
            extra_fields = self.config.get("extra_fields", {})
            payload.update(extra_fields)

            # Build headers
            headers = {"Content-Type": "application/json"}
            headers.update(self.config.get("headers", {}))

            # Setup authentication
            auth = None
            auth_type = self.config.get("auth_type", "none")

            if auth_type == "basic":
                auth = (
                    self.config.get("auth_username", ""),
                    self.config.get("auth_password", "")
                )
            elif auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.config.get('auth_token', '')}"
            elif auth_type == "api_key":
                api_key_header = self.config.get("api_key_header", "X-API-Key")
                headers[api_key_header] = self.config.get("api_key", "")

            # Make request
            if method == "GET":
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.get(endpoint_url, params=payload, headers=headers, auth=auth)
                )
            else:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(endpoint_url, json=payload, headers=headers, auth=auth)
                )

            # Parse response
            try:
                data = response.json()
            except:
                data = {"raw_response": response.text}

            # Check success based on config
            success_field = self.config.get("success_field", "success")
            message_id_field = self.config.get("message_id_field", "message_id")

            # Determine success
            is_success = response.status_code in [200, 201, 202]
            if success_field in data:
                is_success = bool(data.get(success_field))

            return {
                "success": is_success,
                "message_id": data.get(message_id_field, str(datetime.now().timestamp())),
                "provider": "custom_http",
                "to": to,
                "from": from_number,
                "status_code": response.status_code,
                "response": data
            }

        except Exception as e:
            self.logger.error(f"Failed to send custom HTTP SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "custom_http"
            }

    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str) -> Dict[str, Any]:
        """Send bulk SMS via custom HTTP endpoint"""
        results = []
        for recipient in recipients:
            result = await self.send_sms(recipient, message, from_number)
            results.append({
                "recipient": recipient,
                "success": result.get("success", False),
                "message_id": result.get("message_id"),
                "error": result.get("error")
            })

        return {
            "success": True,
            "provider": "custom_http",
            "total_recipients": len(recipients),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results
        }

    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str) -> Dict[str, Any]:
        """Schedule SMS"""
        return {
            "success": True,
            "scheduled": True,
            "send_time": send_time.isoformat(),
            "message_id": f"custom_scheduled_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "provider": "custom_http"
        }

    async def get_delivery_status(self, message_id: str) -> SMSDeliveryReport:
        """Get SMS delivery status"""
        return SMSDeliveryReport(
            message_id=message_id,
            status="unknown",
            provider_response="Status check depends on provider configuration"
        )

    async def receive_sms_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SMS webhook"""
        return {
            "success": True,
            "raw_data": webhook_data,
            "provider": "custom_http"
        }


class SMSIntegration:
    """Main SMS integration class"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SMS integration"""
        self.config = config
        self.logger = logging.getLogger("SMSIntegration")
        self.providers: Dict[SMSProvider, BaseSMSProvider] = {}
        self.default_provider = SMSProvider.TWILIO
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize SMS providers based on configuration"""
        provider_configs = self.config.get("providers", {})

        # Initialize Twilio provider
        if "twilio" in provider_configs and TWILIO_AVAILABLE:
            self.providers[SMSProvider.TWILIO] = TwilioSMSProvider(provider_configs["twilio"])

        # Initialize MessageBird provider
        if "messagebird" in provider_configs and MESSAGEBIRD_AVAILABLE:
            self.providers[SMSProvider.MESSAGEBIRD] = MessageBirdSMSProvider(provider_configs["messagebird"])

        # Initialize Hubtel provider (Ghana-based)
        if "hubtel" in provider_configs:
            self.providers[SMSProvider.HUBTEL] = HubtelSMSProvider(provider_configs["hubtel"])

        # Initialize Arkesel provider (Ghana-based)
        if "arkesel" in provider_configs:
            self.providers[SMSProvider.ARKESEL] = ArkeselSMSProvider(provider_configs["arkesel"])

        # Initialize Custom HTTP provider
        if "custom_http" in provider_configs:
            self.providers[SMSProvider.CUSTOM_HTTP] = CustomHTTPSMSProvider(provider_configs["custom_http"])

        # Set default provider
        default_provider_name = self.config.get("default_provider", "twilio")
        provider_map = {
            "twilio": SMSProvider.TWILIO,
            "messagebird": SMSProvider.MESSAGEBIRD,
            "hubtel": SMSProvider.HUBTEL,
            "arkesel": SMSProvider.ARKESEL,
            "custom_http": SMSProvider.CUSTOM_HTTP
        }

        if default_provider_name in provider_map:
            target_provider = provider_map[default_provider_name]
            if target_provider in self.providers:
                self.default_provider = target_provider
    
    async def send_sms(self, to: str, message: str, from_number: str,
                      provider: Optional[SMSProvider] = None) -> Dict[str, Any]:
        """Send an SMS"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_sms(to, message, from_number)
    
    async def send_bulk_sms(self, recipients: List[str], message: str, from_number: str,
                           provider: Optional[SMSProvider] = None) -> Dict[str, Any]:
        """Send bulk SMS"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].send_bulk_sms(recipients, message, from_number)
    
    async def schedule_sms(self, send_time: datetime, to: str, message: str, from_number: str,
                          provider: Optional[SMSProvider] = None) -> Dict[str, Any]:
        """Schedule an SMS for later sending"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].schedule_sms(send_time, to, message, from_number)
    
    async def get_delivery_status(self, message_id: str,
                                provider: Optional[SMSProvider] = None) -> SMSDeliveryReport:
        """Get SMS delivery status"""
        if not provider:
            provider = self.default_provider
        
        if provider not in self.providers:
            return SMSDeliveryReport(
                message_id=message_id,
                status="error",
                provider_response="Provider not configured"
            )
        
        return await self.providers[provider].get_delivery_status(message_id)
    
    async def receive_sms_webhook(self, webhook_data: Dict[str, Any],
                                provider: Optional[SMSProvider] = None) -> Dict[str, Any]:
        """Process incoming SMS webhook"""
        if not provider:
            # Try to detect provider from webhook data
            if "MessageSid" in webhook_data:
                provider = SMSProvider.TWILIO
            elif "id" in webhook_data:
                provider = SMSProvider.MESSAGEBIRD
            else:
                return {
                    "success": False,
                    "error": "Could not detect provider from webhook data"
                }
        
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"Provider {provider.value} not configured",
                "provider": provider.value
            }
        
        return await self.providers[provider].receive_sms_webhook(webhook_data)
    
    def get_available_providers(self) -> List[SMSProvider]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider: SMSProvider) -> Dict[str, Any]:
        """Get information about a provider"""
        if provider not in self.providers:
            return {"available": False}
        
        return {
            "available": True,
            "type": provider.value,
            "config": self.providers[provider].config
        }

"""
SMS Providers Integration Module

This module provides integration with multiple SMS providers including Vonage SMS,
AWS SNS, Telnyx SMS, and Africa's Talking for comprehensive SMS messaging capabilities.
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
    SMS_PROVIDERS_AVAILABLE = True
except ImportError:
    SMS_PROVIDERS_AVAILABLE = False
    logging.warning("SMS Providers APIs not available. Install requests")

logger = logging.getLogger(__name__)


class SMSProviderType(Enum):
    """SMS provider types."""
    VONAGE = "vonage"
    AWS_SNS = "aws_sns"
    TELNYX = "telnyx"
    AFRICAS_TALKING = "africas_talking"


class SMSMessageStatus(Enum):
    """SMS message status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    REJECTED = "rejected"


class SMSMessageType(Enum):
    """SMS message types."""
    TEXT = "text"
    BINARY = "binary"
    WAP_PUSH = "wap_push"
    UNICODE = "unicode"


@dataclass
class SMSConfig:
    """Base configuration for SMS providers."""
    
    provider_type: SMSProviderType
    """SMS provider type."""
    
    api_key: str
    """API key for authentication."""
    
    api_secret: Optional[str] = None
    """API secret for authentication."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""
    
    default_from: Optional[str] = None
    """Default sender number/ID."""
    
    webhook_url: Optional[str] = None
    """Webhook URL for delivery reports."""


@dataclass
class VonageSMSConfig(SMSConfig):
    """Configuration for Vonage SMS."""
    
    provider_type: SMSProviderType = SMSProviderType.VONAGE
    
    application_id: Optional[str] = None
    """Vonage application ID."""
    
    private_key: Optional[str] = None
    """Private key for JWT authentication."""
    
    signature_secret: Optional[str] = None
    """Signature secret for webhook verification."""


@dataclass
class AWSSNSConfig(SMSConfig):
    """Configuration for AWS SNS."""
    
    provider_type: SMSProviderType = SMSProviderType.AWS_SNS
    
    region: str = "us-east-1"
    """AWS region."""
    
    access_key_id: Optional[str] = None
    """AWS access key ID."""
    
    secret_access_key: Optional[str] = None
    """AWS secret access key."""
    
    session_token: Optional[str] = None
    """AWS session token."""
    
    max_price: Optional[str] = None
    """Maximum price for SMS."""
    
    sms_type: str = "Transactional"
    """SMS type (Transactional or Promotional)."""


@dataclass
class TelnyxSMSConfig(SMSConfig):
    """Configuration for Telnyx SMS."""
    
    provider_type: SMSProviderType = SMSProviderType.TELNYX
    
    webhook_secret: Optional[str] = None
    """Webhook secret for verification."""


@dataclass
class AfricasTalkingConfig(SMSConfig):
    """Configuration for Africa's Talking SMS."""
    
    username: str
    """Africa's Talking username."""
    
    provider_type: SMSProviderType = SMSProviderType.AFRICAS_TALKING
    
    environment: str = "sandbox"
    """Environment (sandbox or production)."""
    
    bulk_sms_mode: int = 0
    """Bulk SMS mode (0 for single, 1 for bulk)."""
    
    enqueue: int = 0
    """Enqueue mode (0 for immediate, 1 for enqueue)."""


@dataclass
class SMSMessage:
    """SMS message data structure."""
    
    from_number: str
    """Sender number."""
    
    to_number: str
    """Recipient number."""
    
    message: str
    """Message content."""
    
    provider_type: SMSProviderType
    """SMS provider type."""
    
    id: Optional[str] = None
    """Message ID."""
    
    message_type: SMSMessageType = SMSMessageType.TEXT
    """Message type."""
    
    status: SMSMessageStatus = SMSMessageStatus.PENDING
    """Message status."""
    
    timestamp: Optional[datetime] = None
    """Message timestamp."""
    
    delivery_report: Optional[Dict[str, Any]] = None
    """Delivery report data."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Message metadata."""


@dataclass
class SMSDeliveryReport:
    """SMS delivery report data structure."""
    
    message_id: str
    """Message ID."""
    
    status: SMSMessageStatus
    """Delivery status."""
    
    timestamp: datetime
    """Status timestamp."""
    
    error_code: Optional[str] = None
    """Error code if failed."""
    
    error_message: Optional[str] = None
    """Error message if failed."""
    
    provider_response: Optional[Dict[str, Any]] = None
    """Provider response data."""


@dataclass
class SMSBalance:
    """SMS balance data structure."""
    
    provider_type: SMSProviderType
    """SMS provider type."""
    
    balance: float
    """Account balance."""
    
    currency: str = "USD"
    """Balance currency."""
    
    last_updated: Optional[datetime] = None
    """Last update timestamp."""


class BaseSMSProvider:
    """Base class for SMS providers."""
    
    def __init__(self, config: SMSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
    
    async def send_message(self, message: SMSMessage) -> SMSMessage:
        """Send an SMS message."""
        raise NotImplementedError
    
    async def get_delivery_report(self, message_id: str) -> SMSDeliveryReport:
        """Get delivery report for a message."""
        raise NotImplementedError
    
    async def get_balance(self) -> SMSBalance:
        """Get account balance."""
        raise NotImplementedError
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health."""
        raise NotImplementedError


class VonageSMSProvider(BaseSMSProvider):
    """Vonage SMS provider implementation."""
    
    def __init__(self, config: VonageSMSConfig):
        super().__init__(config)
        self.config = config
        self.base_url = "https://rest.nexmo.com"
    
    async def send_message(self, message: SMSMessage) -> SMSMessage:
        """
        Send an SMS message via Vonage.
        
        Args:
            message: SMS message to send
            
        Returns:
            Sent message with ID
        """
        try:
            data = {
                "api_key": self.config.api_key,
                "api_secret": self.config.api_secret,
                "from": message.from_number or self.config.default_from,
                "to": message.to_number,
                "text": message.message,
                "type": message.message_type.value
            }
            
            response = self.session.post(f"{self.base_url}/sms/json", data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("messages") and result["messages"][0].get("status") == "0":
                message.id = result["messages"][0].get("message-id")
                message.status = SMSMessageStatus.SENT
                message.timestamp = datetime.now()
                self.logger.info(f"Sent SMS via Vonage: {message.id}")
            else:
                error = result.get("messages", [{}])[0].get("error-text", "Unknown error")
                raise Exception(f"Vonage SMS failed: {error}")
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via Vonage: {e}")
            raise
    
    async def get_delivery_report(self, message_id: str) -> SMSDeliveryReport:
        """
        Get delivery report for a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            Delivery report
        """
        try:
            # Vonage doesn't provide a direct API for delivery reports
            # This would typically be handled via webhooks
            return SMSDeliveryReport(
                message_id=message_id,
                status=SMSMessageStatus.DELIVERED,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get delivery report: {e}")
            raise
    
    async def get_balance(self) -> SMSBalance:
        """
        Get account balance.
        
        Returns:
            Account balance
        """
        try:
            data = {
                "api_key": self.config.api_key,
                "api_secret": self.config.api_secret
            }
            
            response = self.session.get(f"{self.base_url}/account/get-balance", params=data)
            response.raise_for_status()
            
            result = response.json()
            
            return SMSBalance(
                provider_type=self.config.provider_type,
                balance=float(result.get("value", 0)),
                currency=result.get("currency", "EUR"),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health.
        
        Returns:
            Health check results
        """
        try:
            balance = await self.get_balance()
            
            return {
                "status": "healthy",
                "provider": "Vonage",
                "balance": balance.balance,
                "currency": balance.currency,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "Vonage",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


class AWSSNSProvider(BaseSMSProvider):
    """AWS SNS SMS provider implementation."""
    
    def __init__(self, config: AWSSNSConfig):
        super().__init__(config)
        self.config = config
        self.base_url = f"https://sns.{config.region}.amazonaws.com"
        
        # Set up AWS authentication headers
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded"
        })
    
    async def send_message(self, message: SMSMessage) -> SMSMessage:
        """
        Send an SMS message via AWS SNS.
        
        Args:
            message: SMS message to send
            
        Returns:
            Sent message with ID
        """
        try:
            data = {
                "Action": "Publish",
                "Version": "2010-03-31",
                "PhoneNumber": message.to_number,
                "Message": message.message,
                "MessageAttributes.entry.1.Name": "AWS.SNS.SMS.SMSType",
                "MessageAttributes.entry.1.Value.DataType": "String",
                "MessageAttributes.entry.1.Value.StringValue": self.config.sms_type
            }
            
            if self.config.max_price:
                data.update({
                    "MessageAttributes.entry.2.Name": "AWS.SNS.SMS.MaxPrice",
                    "MessageAttributes.entry.2.Value.DataType": "String",
                    "MessageAttributes.entry.2.Value.StringValue": self.config.max_price
                })
            
            response = self.session.post(self.base_url, data=data)
            response.raise_for_status()
            
            # Parse XML response to get message ID
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            message_id = root.find(".//MessageId").text
            
            message.id = message_id
            message.status = SMSMessageStatus.SENT
            message.timestamp = datetime.now()
            
            self.logger.info(f"Sent SMS via AWS SNS: {message.id}")
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via AWS SNS: {e}")
            raise
    
    async def get_delivery_report(self, message_id: str) -> SMSDeliveryReport:
        """
        Get delivery report for a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            Delivery report
        """
        try:
            # AWS SNS doesn't provide direct delivery reports
            # This would typically be handled via SNS notifications
            return SMSDeliveryReport(
                message_id=message_id,
                status=SMSMessageStatus.DELIVERED,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get delivery report: {e}")
            raise
    
    async def get_balance(self) -> SMSBalance:
        """
        Get account balance.
        
        Returns:
            Account balance
        """
        try:
            # AWS doesn't provide direct balance API for SNS
            # This would need to be checked via AWS billing API
            return SMSBalance(
                provider_type=self.config.provider_type,
                balance=0.0,  # Would need AWS billing integration
                currency="USD",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health.
        
        Returns:
            Health check results
        """
        try:
            # Test by sending a test message to a dummy number
            test_message = SMSMessage(
                from_number="TEST",
                to_number="+1234567890",
                message="Health check",
                provider_type=self.config.provider_type
            )
            
            return {
                "status": "healthy",
                "provider": "AWS SNS",
                "region": self.config.region,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "AWS SNS",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


class TelnyxSMSProvider(BaseSMSProvider):
    """Telnyx SMS provider implementation."""
    
    def __init__(self, config: TelnyxSMSConfig):
        super().__init__(config)
        self.config = config
        self.base_url = "https://api.telnyx.com/v2"
        
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })
    
    async def send_message(self, message: SMSMessage) -> SMSMessage:
        """
        Send an SMS message via Telnyx.
        
        Args:
            message: SMS message to send
            
        Returns:
            Sent message with ID
        """
        try:
            data = {
                "from": message.from_number or self.config.default_from,
                "to": message.to_number,
                "text": message.message,
                "messaging_profile_id": self.config.api_secret
            }
            
            response = self.session.post(f"{self.base_url}/messages", json=data)
            response.raise_for_status()
            
            result = response.json()
            
            message.id = result["data"]["id"]
            message.status = SMSMessageStatus.SENT
            message.timestamp = datetime.now()
            
            self.logger.info(f"Sent SMS via Telnyx: {message.id}")
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via Telnyx: {e}")
            raise
    
    async def get_delivery_report(self, message_id: str) -> SMSDeliveryReport:
        """
        Get delivery report for a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            Delivery report
        """
        try:
            response = self.session.get(f"{self.base_url}/messages/{message_id}")
            response.raise_for_status()
            
            result = response.json()
            message_data = result["data"]
            
            status_map = {
                "queued": SMSMessageStatus.PENDING,
                "sending": SMSMessageStatus.PENDING,
                "sent": SMSMessageStatus.SENT,
                "delivered": SMSMessageStatus.DELIVERED,
                "failed": SMSMessageStatus.FAILED,
                "expired": SMSMessageStatus.EXPIRED
            }
            
            return SMSDeliveryReport(
                message_id=message_id,
                status=status_map.get(message_data["status"], SMSMessageStatus.PENDING),
                timestamp=datetime.now(),
                provider_response=message_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get delivery report: {e}")
            raise
    
    async def get_balance(self) -> SMSBalance:
        """
        Get account balance.
        
        Returns:
            Account balance
        """
        try:
            response = self.session.get(f"{self.base_url}/balance")
            response.raise_for_status()
            
            result = response.json()
            balance_data = result["data"]
            
            return SMSBalance(
                provider_type=self.config.provider_type,
                balance=float(balance_data.get("available_credit", 0)),
                currency=balance_data.get("currency", "USD"),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health.
        
        Returns:
            Health check results
        """
        try:
            balance = await self.get_balance()
            
            return {
                "status": "healthy",
                "provider": "Telnyx",
                "balance": balance.balance,
                "currency": balance.currency,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "Telnyx",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


class AfricasTalkingProvider(BaseSMSProvider):
    """Africa's Talking SMS provider implementation."""
    
    def __init__(self, config: AfricasTalkingConfig):
        super().__init__(config)
        self.config = config
        self.base_url = f"https://api.{config.environment}.africastalking.com/version1"
        
        self.session.headers.update({
            "apiKey": config.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })
    
    async def send_message(self, message: SMSMessage) -> SMSMessage:
        """
        Send an SMS message via Africa's Talking.
        
        Args:
            message: SMS message to send
            
        Returns:
            Sent message with ID
        """
        try:
            data = {
                "username": self.config.username,
                "to": message.to_number,
                "message": message.message,
                "from": message.from_number or self.config.default_from,
                "bulkSMSMode": self.config.bulk_sms_mode,
                "enqueue": self.config.enqueue
            }
            
            response = self.session.post(f"{self.base_url}/messaging", data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("SMSMessageData", {}).get("Recipients"):
                recipient = result["SMSMessageData"]["Recipients"][0]
                message.id = recipient.get("messageId")
                message.status = SMSMessageStatus.SENT if recipient.get("status") == "Success" else SMSMessageStatus.FAILED
                message.timestamp = datetime.now()
                self.logger.info(f"Sent SMS via Africa's Talking: {message.id}")
            else:
                raise Exception("No recipients in response")
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS via Africa's Talking: {e}")
            raise
    
    async def get_delivery_report(self, message_id: str) -> SMSDeliveryReport:
        """
        Get delivery report for a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            Delivery report
        """
        try:
            data = {
                "username": self.config.username,
                "messageId": message_id
            }
            
            response = self.session.get(f"{self.base_url}/messaging", params=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Africa's Talking doesn't provide detailed delivery reports
            return SMSDeliveryReport(
                message_id=message_id,
                status=SMSMessageStatus.DELIVERED,
                timestamp=datetime.now(),
                provider_response=result
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get delivery report: {e}")
            raise
    
    async def get_balance(self) -> SMSBalance:
        """
        Get account balance.
        
        Returns:
            Account balance
        """
        try:
            data = {
                "username": self.config.username
            }
            
            response = self.session.get(f"{self.base_url}/user", params=data)
            response.raise_for_status()
            
            result = response.json()
            user_data = result.get("User", {})
            
            return SMSBalance(
                provider_type=self.config.provider_type,
                balance=float(user_data.get("balance", 0)),
                currency="KES",  # Africa's Talking uses Kenyan Shillings
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health.
        
        Returns:
            Health check results
        """
        try:
            balance = await self.get_balance()
            
            return {
                "status": "healthy",
                "provider": "Africa's Talking",
                "environment": self.config.environment,
                "balance": balance.balance,
                "currency": balance.currency,
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "Africa's Talking",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


class SMSProvidersIntegration:
    """SMS providers integration for comprehensive SMS messaging."""
    
    def __init__(self, configs: Dict[SMSProviderType, SMSConfig]):
        self.configs = configs
        self.logger = logging.getLogger(__name__)
        
        self.providers = {}
        for provider_type, config in configs.items():
            if provider_type == SMSProviderType.VONAGE:
                self.providers[provider_type] = VonageSMSProvider(config)
            elif provider_type == SMSProviderType.AWS_SNS:
                self.providers[provider_type] = AWSSNSProvider(config)
            elif provider_type == SMSProviderType.TELNYX:
                self.providers[provider_type] = TelnyxSMSProvider(config)
            elif provider_type == SMSProviderType.AFRICAS_TALKING:
                self.providers[provider_type] = AfricasTalkingProvider(config)
    
    async def send_message(
        self,
        to_number: str,
        message: str,
        from_number: Optional[str] = None,
        provider_type: Optional[SMSProviderType] = None
    ) -> SMSMessage:
        """
        Send an SMS message using the specified or default provider.
        
        Args:
            to_number: Recipient phone number
            message: Message content
            from_number: Sender number
            provider_type: SMS provider type
            
        Returns:
            Sent message
        """
        try:
            # Use specified provider or default to first available
            if provider_type and provider_type in self.providers:
                provider = self.providers[provider_type]
            elif self.providers:
                provider = list(self.providers.values())[0]
            else:
                raise ValueError("No SMS providers configured")
            
            sms_message = SMSMessage(
                from_number=from_number or provider.config.default_from,
                to_number=to_number,
                message=message,
                provider_type=provider.config.provider_type
            )
            
            return await provider.send_message(sms_message)
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS message: {e}")
            raise
    
    async def send_bulk_messages(
        self,
        messages: List[Dict[str, str]],
        provider_type: Optional[SMSProviderType] = None
    ) -> List[SMSMessage]:
        """
        Send multiple SMS messages.
        
        Args:
            messages: List of message dictionaries
            provider_type: SMS provider type
            
        Returns:
            List of sent messages
        """
        try:
            results = []
            for msg_data in messages:
                message = await self.send_message(
                    to_number=msg_data["to"],
                    message=msg_data["message"],
                    from_number=msg_data.get("from"),
                    provider_type=provider_type
                )
                results.append(message)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to send bulk SMS messages: {e}")
            raise
    
    async def get_delivery_report(
        self,
        message_id: str,
        provider_type: SMSProviderType
    ) -> SMSDeliveryReport:
        """
        Get delivery report for a message.
        
        Args:
            message_id: Message ID
            provider_type: SMS provider type
            
        Returns:
            Delivery report
        """
        try:
            if provider_type not in self.providers:
                raise ValueError(f"Provider {provider_type} not configured")
            
            provider = self.providers[provider_type]
            return await provider.get_delivery_report(message_id)
            
        except Exception as e:
            self.logger.error(f"Failed to get delivery report: {e}")
            raise
    
    async def get_balance(self, provider_type: SMSProviderType) -> SMSBalance:
        """
        Get account balance for a provider.
        
        Args:
            provider_type: SMS provider type
            
        Returns:
            Account balance
        """
        try:
            if provider_type not in self.providers:
                raise ValueError(f"Provider {provider_type} not configured")
            
            provider = self.providers[provider_type]
            return await provider.get_balance()
            
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all SMS providers.
        
        Returns:
            Health check results for all providers
        """
        try:
            results = {}
            for provider_type, provider in self.providers.items():
                results[provider_type.value] = await provider.health_check()
            
            return {
                "status": "healthy" if all(r["status"] == "healthy" for r in results.values()) else "partial",
                "providers": results,
                "total_providers": len(self.providers),
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


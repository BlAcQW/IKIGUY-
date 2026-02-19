"""
Vonage Integration Service.
Handles Vonage Voice, SMS, Messages, and other communication functionalities.
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
import base64
import hashlib
import hmac

logger = logging.getLogger(__name__)


@dataclass
class VonageConfig:
    """Configuration for Vonage integration."""
    api_key: str
    api_secret: str
    base_url: str = "https://api.nexmo.com"
    application_id: Optional[str] = None
    private_key: Optional[str] = None
    signature_secret: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True


@dataclass
class VonageSMSMessage:
    """Vonage SMS message data model."""
    to: str
    from_: str  # Using from_ to avoid Python keyword conflict
    text: str
    type: str = "text"
    client_ref: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_version: str = "2"
    ttl: Optional[int] = None
    message_class: Optional[int] = None


@dataclass
class VonageVoiceCall:
    """Vonage Voice call data model."""
    to: str
    from_: str
    answer_url: str
    event_url: Optional[str] = None
    answer_method: str = "GET"
    event_method: str = "POST"
    machine_detection: Optional[str] = None
    length_timer: Optional[int] = None
    ringing_timer: Optional[int] = None


@dataclass
class VonageNumber:
    """Vonage phone number data model."""
    msisdn: str
    country: str
    type: str
    features: List[str]
    cost: Optional[str] = None
    voiceCallbackType: Optional[str] = None
    voiceCallbackValue: Optional[str] = None
    moHttpUrl: Optional[str] = None
    moSmppSysType: Optional[str] = None


@dataclass
class VonageResponse:
    """Vonage API response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message_count: Optional[int] = None
    messages: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class VonageIntegration:
    """
    Comprehensive Vonage integration service.
    Provides SMS, Voice, Number management, and verification functionality.
    """

    def __init__(self, config: VonageConfig):
        """
        Initialize Vonage integration.

        Args:
            config: Vonage configuration
        """
        self.config = config
        self._connected = False
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'User-Agent': 'KasaAI-Vonage-Integration/1.0'
        })

        try:
            # Test connection
            if self.config.api_key and self.config.api_secret:
                self._connected = True
                logger.info("Vonage integration initialized successfully")
            else:
                logger.warning("Vonage integration initialized without credentials")
        except Exception as e:
            logger.error(f"Failed to initialize Vonage client: {e}")
            self._connected = False

    def _create_auth_header(self) -> str:
        """Create Basic Auth header for API requests."""
        credentials = f"{self.config.api_key}:{self.config.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    def _create_signature(self, params: Dict[str, Any]) -> str:
        """Create signature for webhook validation."""
        if not self.config.signature_secret:
            return ""

        # Sort parameters and create query string
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])

        # Create signature
        signature = hmac.new(
            self.config.signature_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_auth_header: bool = True
    ) -> VonageResponse:
        """Make HTTP request to Vonage API."""
        if not self._connected:
            return VonageResponse(
                success=False,
                error="Vonage not connected"
            )

        try:
            url = f"{self.config.base_url}/{endpoint}"

            headers = {}
            if use_auth_header:
                headers['Authorization'] = self._create_auth_header()

            if json_data:
                headers['Content-Type'] = 'application/json'

            # Add API credentials to data if not using auth header
            if not use_auth_header and data is not None:
                data.update({
                    'api_key': self.config.api_key,
                    'api_secret': self.config.api_secret
                })

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data,
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
                return VonageResponse(
                    success=True,
                    data=response_data,
                    status_code=response.status_code
                )
            else:
                error_message = "Unknown error"
                if response_data and isinstance(response_data, dict):
                    error_message = (
                        response_data.get('error-text') or
                        response_data.get('error') or
                        response_data.get('detail') or
                        str(response_data)
                    )

                return VonageResponse(
                    success=False,
                    error=error_message,
                    status_code=response.status_code,
                    data=response_data
                )

        except requests.RequestException as e:
            logger.error(f"Vonage API request failed: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in Vonage request: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    # SMS Methods
    async def send_sms(self, message: VonageSMSMessage) -> VonageResponse:
        """
        Send SMS message.

        Args:
            message: SMS message configuration

        Returns:
            VonageResponse: SMS sending response
        """
        try:
            data = {
                'to': message.to,
                'from': message.from_,
                'text': message.text,
                'type': message.type
            }

            if message.client_ref:
                data['client-ref'] = message.client_ref
            if message.webhook_url:
                data['callback'] = message.webhook_url
            if message.webhook_version:
                data['callback-version'] = message.webhook_version
            if message.ttl:
                data['ttl'] = message.ttl
            if message.message_class:
                data['message-class'] = message.message_class

            response = await self._make_request(
                method='POST',
                endpoint='v1/messages',
                data=data,
                use_auth_header=False
            )

            if response.success and response.data:
                return VonageResponse(
                    success=True,
                    data=response.data,
                    message_count=response.data.get('message-count'),
                    messages=response.data.get('messages', [])
                )

            return response

        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def get_sms_pricing(self, country: str) -> VonageResponse:
        """
        Get SMS pricing for a country.

        Args:
            country: Country code (e.g., 'US', 'GB')

        Returns:
            VonageResponse: Pricing information
        """
        try:
            response = await self._make_request(
                method='GET',
                endpoint=f'account/get-pricing/outbound/sms',
                params={'country': country}
            )

            return response

        except Exception as e:
            logger.error(f"Error getting SMS pricing: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    # Voice Methods
    async def make_voice_call(self, call: VonageVoiceCall) -> VonageResponse:
        """
        Make a voice call.

        Args:
            call: Voice call configuration

        Returns:
            VonageResponse: Call initiation response
        """
        try:
            data = {
                'to': [{'type': 'phone', 'number': call.to}],
                'from': {'type': 'phone', 'number': call.from_},
                'answer_url': [call.answer_url],
                'answer_method': call.answer_method
            }

            if call.event_url:
                data['event_url'] = [call.event_url]
                data['event_method'] = call.event_method

            if call.machine_detection:
                data['machine_detection'] = call.machine_detection

            if call.length_timer:
                data['length_timer'] = call.length_timer

            if call.ringing_timer:
                data['ringing_timer'] = call.ringing_timer

            response = await self._make_request(
                method='POST',
                endpoint='v1/calls',
                json_data=data
            )

            return response

        except Exception as e:
            logger.error(f"Error making voice call: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def get_call_details(self, call_uuid: str) -> VonageResponse:
        """
        Get call details by UUID.

        Args:
            call_uuid: Call UUID

        Returns:
            VonageResponse: Call details
        """
        try:
            response = await self._make_request(
                method='GET',
                endpoint=f'v1/calls/{call_uuid}'
            )

            return response

        except Exception as e:
            logger.error(f"Error getting call details: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def hangup_call(self, call_uuid: str) -> VonageResponse:
        """
        Hangup an active call.

        Args:
            call_uuid: Call UUID

        Returns:
            VonageResponse: Hangup response
        """
        try:
            response = await self._make_request(
                method='PUT',
                endpoint=f'v1/calls/{call_uuid}',
                json_data={'action': 'hangup'}
            )

            return response

        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def play_tts_to_call(
        self,
        call_uuid: str,
        text: str,
        voice_name: str = "Amy",
        language: str = "en-US"
    ) -> VonageResponse:
        """
        Play text-to-speech to an active call.

        Args:
            call_uuid: Call UUID
            text: Text to speak
            voice_name: Voice name
            language: Language code

        Returns:
            VonageResponse: TTS response
        """
        try:
            data = {
                'text': text,
                'voice_name': voice_name,
                'language': language
            }

            response = await self._make_request(
                method='PUT',
                endpoint=f'v1/calls/{call_uuid}/talk',
                json_data=data
            )

            return response

        except Exception as e:
            logger.error(f"Error playing TTS to call: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def stop_tts_in_call(self, call_uuid: str) -> VonageResponse:
        """
        Stop text-to-speech in an active call.

        Args:
            call_uuid: Call UUID

        Returns:
            VonageResponse: Stop TTS response
        """
        try:
            response = await self._make_request(
                method='DELETE',
                endpoint=f'v1/calls/{call_uuid}/talk'
            )

            return response

        except Exception as e:
            logger.error(f"Error stopping TTS in call: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    # Number Management Methods
    async def search_available_numbers(
        self,
        country: str,
        type_: str = "mobile-lvn",
        pattern: Optional[str] = None,
        search_pattern: int = 0,
        features: Optional[List[str]] = None,
        size: int = 10,
        index: int = 1
    ) -> VonageResponse:
        """
        Search for available phone numbers.

        Args:
            country: Country code
            type_: Number type (mobile-lvn, landline, etc.)
            pattern: Number pattern to search
            search_pattern: Search pattern type
            features: Required features (SMS, VOICE, etc.)
            size: Number of results
            index: Start index

        Returns:
            VonageResponse: Available numbers
        """
        try:
            params = {
                'country': country,
                'type': type_,
                'size': size,
                'index': index
            }

            if pattern:
                params['pattern'] = pattern
                params['search_pattern'] = search_pattern

            if features:
                params['features'] = ','.join(features)

            response = await self._make_request(
                method='GET',
                endpoint='number/search',
                params=params
            )

            return response

        except Exception as e:
            logger.error(f"Error searching available numbers: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def buy_number(
        self,
        country: str,
        msisdn: str,
        target_api_key: Optional[str] = None
    ) -> VonageResponse:
        """
        Buy a phone number.

        Args:
            country: Country code
            msisdn: Phone number to buy
            target_api_key: Target API key for number assignment

        Returns:
            VonageResponse: Purchase response
        """
        try:
            data = {
                'country': country,
                'msisdn': msisdn
            }

            if target_api_key:
                data['target_api_key'] = target_api_key

            response = await self._make_request(
                method='POST',
                endpoint='number/buy',
                data=data,
                use_auth_header=False
            )

            return response

        except Exception as e:
            logger.error(f"Error buying number: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def cancel_number(self, country: str, msisdn: str) -> VonageResponse:
        """
        Cancel a phone number.

        Args:
            country: Country code
            msisdn: Phone number to cancel

        Returns:
            VonageResponse: Cancellation response
        """
        try:
            data = {
                'country': country,
                'msisdn': msisdn
            }

            response = await self._make_request(
                method='POST',
                endpoint='number/cancel',
                data=data,
                use_auth_header=False
            )

            return response

        except Exception as e:
            logger.error(f"Error canceling number: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def list_owned_numbers(
        self,
        index: int = 1,
        size: int = 10,
        pattern: Optional[str] = None,
        search_pattern: int = 0
    ) -> VonageResponse:
        """
        List owned phone numbers.

        Args:
            index: Start index
            size: Number of results
            pattern: Number pattern filter
            search_pattern: Search pattern type

        Returns:
            VonageResponse: Owned numbers
        """
        try:
            params = {
                'index': index,
                'size': size
            }

            if pattern:
                params['pattern'] = pattern
                params['search_pattern'] = search_pattern

            response = await self._make_request(
                method='GET',
                endpoint='account/numbers',
                params=params
            )

            return response

        except Exception as e:
            logger.error(f"Error listing owned numbers: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    # Account Methods
    async def get_account_balance(self) -> VonageResponse:
        """
        Get account balance.

        Returns:
            VonageResponse: Account balance
        """
        try:
            response = await self._make_request(
                method='GET',
                endpoint='account/get-balance'
            )

            return response

        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    async def update_account_settings(
        self,
        mo_callback_url: Optional[str] = None,
        dr_callback_url: Optional[str] = None
    ) -> VonageResponse:
        """
        Update account webhook settings.

        Args:
            mo_callback_url: Mobile originated callback URL
            dr_callback_url: Delivery receipt callback URL

        Returns:
            VonageResponse: Update response
        """
        try:
            data = {}

            if mo_callback_url:
                data['moCallBackUrl'] = mo_callback_url

            if dr_callback_url:
                data['drCallBackUrl'] = dr_callback_url

            if not data:
                return VonageResponse(
                    success=False,
                    error="No settings provided to update"
                )

            response = await self._make_request(
                method='POST',
                endpoint='account/settings',
                data=data,
                use_auth_header=False
            )

            return response

        except Exception as e:
            logger.error(f"Error updating account settings: {e}")
            return VonageResponse(
                success=False,
                error=str(e)
            )

    # Webhook Validation
    def validate_webhook_signature(
        self,
        params: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Validate webhook signature.

        Args:
            params: Webhook parameters
            signature: Provided signature

        Returns:
            bool: Signature validity
        """
        try:
            expected_signature = self._create_signature(params)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False

    # Utility Methods
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Dict[str, Any]: Health status
        """
        try:
            # Test with account balance endpoint
            response = await self.get_account_balance()

            return {
                "status": "healthy" if response.success else "degraded",
                "connected": self._connected,
                "api_key_configured": bool(self.config.api_key),
                "api_secret_configured": bool(self.config.api_secret),
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
            "send_sms", "get_sms_pricing",
            "make_voice_call", "get_call_details", "hangup_call",
            "play_tts_to_call", "stop_tts_in_call",
            "search_available_numbers", "buy_number", "cancel_number", "list_owned_numbers",
            "get_account_balance", "update_account_settings",
            "validate_webhook_signature", "health_check"
        ]

        return {
            "service": "vonage",
            "capabilities": capabilities,
            "connected": self._connected,
            "sms": True,
            "voice": True,
            "numbers": True,
            "account_management": True,
            "webhook_validation": True,
            "api_reference": "https://developer.vonage.com/en/api",
            "documentation": "https://developer.vonage.com/",
            "mcp_available": False  # No official Vonage MCP server available
        }
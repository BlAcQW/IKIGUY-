"""
Consolidated Vonage Integration Service.
Handles all Vonage-related functionality with unified interface.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import from shared integration
from apps.shared.integration.vonage import (
    VonageIntegration,
    VonageConfig,
    VonageSMSMessage,
    VonageVoiceCall,
    VonageNumber,
    VonageResponse
)

logger = logging.getLogger(__name__)


class VonageServiceWrapper(VonageIntegration):
    """
    Consolidated service for Vonage integration.
    Extends the shared Vonage service with additional functionality.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Vonage service with configuration.

        Args:
            config: Configuration dictionary with Vonage settings
        """
        if config:
            # Convert dict config to VonageConfig
            vonage_config = VonageConfig(
                api_key=config.get("api_key", ""),
                api_secret=config.get("api_secret", ""),
                base_url=config.get("base_url", "https://api.nexmo.com"),
                application_id=config.get("application_id"),
                private_key=config.get("private_key"),
                signature_secret=config.get("signature_secret"),
                timeout=config.get("timeout", 30),
                verify_ssl=config.get("verify_ssl", True)
            )
            super().__init__(vonage_config)
        else:
            # Create default config
            vonage_config = VonageConfig(
                api_key="",
                api_secret="",
                timeout=30,
                verify_ssl=True
            )
            super().__init__(vonage_config)

        self.tenant_campaigns = {}  # Track tenant-specific campaigns
        self.tenant_contexts = {}  # Track tenant-specific contexts

    async def send_tenant_sms(
        self,
        tenant_id: str,
        message: VonageSMSMessage,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send tenant-specific SMS message.

        Args:
            tenant_id: Tenant identifier
            message: SMS message configuration
            context: Additional context

        Returns:
            dict: SMS result with tenant info
        """
        try:
            # Add tenant-specific client reference
            if not message.client_ref:
                message.client_ref = f"tenant_{tenant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            result = await self.send_sms(message)

            if result.success:
                # Store SMS event for tenant analytics
                if not hasattr(self, 'tenant_sms_events'):
                    self.tenant_sms_events = {}

                if tenant_id not in self.tenant_sms_events:
                    self.tenant_sms_events[tenant_id] = []

                self.tenant_sms_events[tenant_id].append({
                    "message": {
                        "to": message.to,
                        "from": message.from_,
                        "text": message.text[:50] + "..." if len(message.text) > 50 else message.text,
                        "client_ref": message.client_ref
                    },
                    "result": result.data,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat()
                })

                return {
                    "success": True,
                    "data": result.data,
                    "message_count": result.message_count,
                    "messages": result.messages,
                    "tenant_id": tenant_id,
                    "client_ref": message.client_ref,
                    "context": context or {}
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "tenant_id": tenant_id,
                    "context": context or {}
                }

        except Exception as e:
            logger.error(f"Error sending tenant SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def make_tenant_voice_call(
        self,
        tenant_id: str,
        call: VonageVoiceCall,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make tenant-specific voice call.

        Args:
            tenant_id: Tenant identifier
            call: Voice call configuration
            context: Additional context

        Returns:
            dict: Call result with tenant info
        """
        try:
            result = await self.make_voice_call(call)

            if result.success:
                # Store call event for tenant analytics
                if not hasattr(self, 'tenant_call_events'):
                    self.tenant_call_events = {}

                if tenant_id not in self.tenant_call_events:
                    self.tenant_call_events[tenant_id] = []

                call_uuid = result.data.get("uuid") if result.data else None

                self.tenant_call_events[tenant_id].append({
                    "call": {
                        "to": call.to,
                        "from": call.from_,
                        "answer_url": call.answer_url,
                        "uuid": call_uuid
                    },
                    "result": result.data,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat()
                })

                return {
                    "success": True,
                    "data": result.data,
                    "call_uuid": call_uuid,
                    "tenant_id": tenant_id,
                    "context": context or {}
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "tenant_id": tenant_id,
                    "context": context or {}
                }

        except Exception as e:
            logger.error(f"Error making tenant voice call: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def manage_tenant_numbers(
        self,
        tenant_id: str,
        operation: str,
        country: str,
        msisdn: Optional[str] = None,
        search_params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manage tenant-specific phone numbers.

        Args:
            tenant_id: Tenant identifier
            operation: Operation (search, buy, cancel, list)
            country: Country code
            msisdn: Phone number (for buy/cancel operations)
            search_params: Parameters for search operation
            context: Additional context

        Returns:
            dict: Operation result with tenant info
        """
        try:
            result = None

            if operation == "search":
                search_params = search_params or {}
                result = await self.search_available_numbers(
                    country=country,
                    type_=search_params.get("type", "mobile-lvn"),
                    pattern=search_params.get("pattern"),
                    search_pattern=search_params.get("search_pattern", 0),
                    features=search_params.get("features"),
                    size=search_params.get("size", 10),
                    index=search_params.get("index", 1)
                )
            elif operation == "buy":
                if not msisdn:
                    return {
                        "success": False,
                        "error": "MSISDN required for buy operation",
                        "tenant_id": tenant_id
                    }
                result = await self.buy_number(country, msisdn)
            elif operation == "cancel":
                if not msisdn:
                    return {
                        "success": False,
                        "error": "MSISDN required for cancel operation",
                        "tenant_id": tenant_id
                    }
                result = await self.cancel_number(country, msisdn)
            elif operation == "list":
                search_params = search_params or {}
                result = await self.list_owned_numbers(
                    index=search_params.get("index", 1),
                    size=search_params.get("size", 10),
                    pattern=search_params.get("pattern"),
                    search_pattern=search_params.get("search_pattern", 0)
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation: {operation}",
                    "tenant_id": tenant_id
                }

            if result and result.success:
                # Store number management event for tenant analytics
                if not hasattr(self, 'tenant_number_events'):
                    self.tenant_number_events = {}

                if tenant_id not in self.tenant_number_events:
                    self.tenant_number_events[tenant_id] = []

                self.tenant_number_events[tenant_id].append({
                    "operation": operation,
                    "country": country,
                    "msisdn": msisdn,
                    "search_params": search_params,
                    "result": result.data,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat()
                })

                return {
                    "success": True,
                    "data": result.data,
                    "operation": operation,
                    "tenant_id": tenant_id,
                    "context": context or {}
                }
            else:
                return {
                    "success": False,
                    "error": result.error if result else "Operation failed",
                    "operation": operation,
                    "tenant_id": tenant_id,
                    "context": context or {}
                }

        except Exception as e:
            logger.error(f"Error in tenant number management: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "tenant_id": tenant_id
            }

    async def get_tenant_voice_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get voice analytics for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            dict: Voice analytics with tenant info
        """
        try:
            analytics = {
                "tenant_id": tenant_id,
                "generated_at": datetime.now().isoformat(),
                "voice_calls": {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "recent_calls": []
                },
                "sms_messages": {
                    "total_messages": 0,
                    "successful_messages": 0,
                    "failed_messages": 0,
                    "recent_messages": []
                },
                "number_management": {
                    "total_operations": 0,
                    "recent_operations": []
                }
            }

            # Analyze call events
            if hasattr(self, 'tenant_call_events') and tenant_id in self.tenant_call_events:
                call_events = self.tenant_call_events[tenant_id]
                analytics["voice_calls"]["total_calls"] = len(call_events)
                analytics["voice_calls"]["recent_calls"] = call_events[-5:]

            # Analyze SMS events
            if hasattr(self, 'tenant_sms_events') and tenant_id in self.tenant_sms_events:
                sms_events = self.tenant_sms_events[tenant_id]
                analytics["sms_messages"]["total_messages"] = len(sms_events)
                analytics["sms_messages"]["recent_messages"] = sms_events[-5:]

            # Analyze number management events
            if hasattr(self, 'tenant_number_events') and tenant_id in self.tenant_number_events:
                number_events = self.tenant_number_events[tenant_id]
                analytics["number_management"]["total_operations"] = len(number_events)
                analytics["number_management"]["recent_operations"] = number_events[-5:]

            # Add date range info
            if start_date:
                analytics["start_date"] = start_date.isoformat()
            if end_date:
                analytics["end_date"] = end_date.isoformat()

            return {
                "success": True,
                "analytics": analytics,
                "tenant_id": tenant_id
            }

        except Exception as e:
            logger.error(f"Error getting tenant voice analytics: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def handle_tenant_webhook(
        self,
        tenant_id: str,
        webhook_data: Dict[str, Any],
        signature: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle tenant-specific Vonage webhooks.

        Args:
            tenant_id: Tenant identifier
            webhook_data: Webhook payload
            signature: Webhook signature for validation
            context: Additional context

        Returns:
            dict: Webhook processing result
        """
        try:
            # Validate signature if provided
            if signature and self.config.signature_secret:
                is_valid = self.validate_webhook_signature(webhook_data, signature)
                if not is_valid:
                    return {
                        "success": False,
                        "error": "Invalid webhook signature",
                        "tenant_id": tenant_id
                    }

            # Process webhook based on type
            webhook_type = webhook_data.get("type") or webhook_data.get("status")

            # Store webhook event for tenant analytics
            if not hasattr(self, 'tenant_webhook_events'):
                self.tenant_webhook_events = {}

            if tenant_id not in self.tenant_webhook_events:
                self.tenant_webhook_events[tenant_id] = []

            self.tenant_webhook_events[tenant_id].append({
                "webhook_data": webhook_data,
                "webhook_type": webhook_type,
                "signature_valid": signature is not None,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": True,
                "webhook_type": webhook_type,
                "data": webhook_data,
                "tenant_id": tenant_id,
                "processed_at": datetime.now().isoformat(),
                "context": context or {}
            }

        except Exception as e:
            logger.error(f"Error handling tenant webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def get_tenant_account_info(
        self,
        tenant_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get account information for tenant context.

        Args:
            tenant_id: Tenant identifier
            context: Additional context

        Returns:
            dict: Account info with tenant context
        """
        try:
            balance_result = await self.get_account_balance()

            if balance_result.success:
                return {
                    "success": True,
                    "account_balance": balance_result.data,
                    "tenant_id": tenant_id,
                    "retrieved_at": datetime.now().isoformat(),
                    "context": context or {}
                }
            else:
                return {
                    "success": False,
                    "error": balance_result.error,
                    "tenant_id": tenant_id,
                    "context": context or {}
                }

        except Exception as e:
            logger.error(f"Error getting tenant account info: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get base capabilities from shared integration.

        Returns:
            dict: Base capabilities
        """
        base_capabilities = super().get_capabilities()
        return base_capabilities

    def get_extended_capabilities(self) -> Dict[str, Any]:
        """
        Get extended capabilities including tenant-specific features.

        Returns:
            dict: Extended capabilities
        """
        base_capabilities = self.get_capabilities()

        extended_capabilities = [
            "send_tenant_sms",
            "make_tenant_voice_call",
            "manage_tenant_numbers",
            "get_tenant_voice_analytics",
            "handle_tenant_webhook",
            "get_tenant_account_info"
        ]

        base_capabilities["capabilities"].extend(extended_capabilities)
        base_capabilities["tenant_support"] = True
        base_capabilities["multi_tenant_analytics"] = True
        base_capabilities["webhook_handling"] = True

        return base_capabilities


# Global Vonage service instance
vonage_consolidated_service = VonageServiceWrapper({
    "api_key": os.getenv("VONAGE_API_KEY"),
    "api_secret": os.getenv("VONAGE_API_SECRET"),
    "base_url": os.getenv("VONAGE_BASE_URL", "https://api.nexmo.com"),
    "signature_secret": os.getenv("VONAGE_WEBHOOK_SECRET")
})
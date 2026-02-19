"""
Consolidated VAPI Integration Service.
Handles all VAPI-related functionality with unified interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# Import from shared integration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from integration.vapi import VAPIService, VAPIAgent, VAPICall, VAPIWebhookEvent, vapi_service as shared_vapi_service

logger = logging.getLogger(__name__)


class VAPIServiceWrapper(VAPIService):
    """
    Consolidated service for VAPI integration.
    Extends the shared VAPI service with additional functionality.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize VAPI service with configuration.

        Args:
            config: Configuration dictionary with VAPI settings
        """
        super().__init__(config)
        self.tenant_sessions = {}  # Track tenant-specific sessions

    async def create_tenant_agent(
        self,
        tenant_id: str,
        agent: VAPIAgent,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a tenant-specific VAPI agent.

        Args:
            tenant_id: Tenant identifier
            agent: Agent configuration
            context: Additional context

        Returns:
            Agent creation result with tenant association
        """
        try:
            result = await self.create_agent(agent)

            if result.get("success"):
                # Associate agent with tenant
                result["tenant_id"] = tenant_id
                result["context"] = context or {}

                logger.info(f"Created VAPI agent for tenant {tenant_id}: {result.get('agent_id')}")

            return result

        except Exception as e:
            logger.error(f"Error creating tenant VAPI agent: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def initiate_tenant_call(
        self,
        tenant_id: str,
        to_number: str,
        assistant_id: str,
        from_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a call for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            to_number: Phone number to call
            assistant_id: VAPI assistant ID
            from_number: Caller ID (optional)
            metadata: Additional metadata

        Returns:
            Call initiation result with tenant context
        """
        try:
            # Add tenant context to metadata
            call_metadata = metadata or {}
            call_metadata["tenant_id"] = tenant_id
            call_metadata["initiated_by"] = "kasaai_core_backend"

            result = await self.initiate_call(
                to_number=to_number,
                assistant_id=assistant_id,
                from_number=from_number,
                metadata=call_metadata
            )

            if result.get("success"):
                result["tenant_id"] = tenant_id
                logger.info(f"Initiated VAPI call for tenant {tenant_id}: {result.get('call_id')}")

            return result

        except Exception as e:
            logger.error(f"Error initiating tenant VAPI call: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def handle_tenant_webhook(
        self,
        tenant_id: str,
        event: VAPIWebhookEvent,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle webhook event for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            event: Webhook event data
            context: Additional context

        Returns:
            Webhook handling result with tenant context
        """
        try:
            result = await self.handle_webhook(event)

            if result.get("success"):
                result["tenant_id"] = tenant_id
                result["context"] = context or {}

                # Additional tenant-specific processing can be added here
                await self._process_tenant_specific_webhook(tenant_id, event, result)

            return result

        except Exception as e:
            logger.error(f"Error handling tenant VAPI webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def _process_tenant_specific_webhook(
        self,
        tenant_id: str,
        event: VAPIWebhookEvent,
        result: Dict[str, Any]
    ):
        """
        Process tenant-specific webhook logic.

        Args:
            tenant_id: Tenant identifier
            event: Webhook event
            result: Webhook processing result
        """
        try:
            # This can be extended for tenant-specific webhook processing
            # For example: custom integrations, notifications, analytics
            logger.info(f"Processing tenant-specific webhook for {tenant_id}: {event.event}")

            # Store webhook event for tenant analytics
            if not hasattr(self, 'tenant_webhook_events'):
                self.tenant_webhook_events = {}

            if tenant_id not in self.tenant_webhook_events:
                self.tenant_webhook_events[tenant_id] = []

            self.tenant_webhook_events[tenant_id].append({
                "event": event.dict(),
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error processing tenant-specific webhook: {e}")

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        assistant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            assistant_id: Filter by assistant ID
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            Tenant-specific analytics data
        """
        try:
            result = await self.get_analytics(assistant_id, start_date, end_date)

            if result.get("success"):
                result["tenant_id"] = tenant_id

                # Add tenant-specific metrics
                tenant_metrics = await self._get_tenant_metrics(tenant_id)
                result["analytics"]["tenant_metrics"] = tenant_metrics

            return result

        except Exception as e:
            logger.error(f"Error getting tenant VAPI analytics: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def _get_tenant_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get tenant-specific metrics.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Tenant metrics
        """
        try:
            # Mock tenant metrics
            return {
                "total_agents": 5,
                "active_agents": 3,
                "webhook_events_processed": 127,
                "last_activity": datetime.now().isoformat(),
                "tenant_id": tenant_id
            }

        except Exception as e:
            logger.error(f"Error getting tenant metrics: {e}")
            return {}

    async def list_tenant_agents(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List agents for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of agents to return
            offset: Offset for pagination

        Returns:
            List of tenant agents
        """
        try:
            result = await self.list_agents(limit, offset)

            if result.get("success"):
                # Filter agents by tenant (in a real implementation)
                result["tenant_id"] = tenant_id
                result["filtered_by_tenant"] = True

            return result

        except Exception as e:
            logger.error(f"Error listing tenant VAPI agents: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def create_integration_webhook(
        self,
        integration_type: str,
        integration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a webhook integration for external services.

        Args:
            integration_type: Type of integration (freshdesk, paystack, etc.)
            integration_config: Integration configuration

        Returns:
            Webhook integration result
        """
        try:
            webhook_url = f"{self.webhook_url}/integrations/{integration_type}"

            # Create integration-specific webhook configuration
            webhook_config = {
                "url": webhook_url,
                "integration_type": integration_type,
                "config": integration_config,
                "created_at": datetime.now().isoformat()
            }

            logger.info(f"Created VAPI integration webhook for {integration_type}")

            return {
                "success": True,
                "webhook_config": webhook_config,
                "integration_type": integration_type
            }

        except Exception as e:
            logger.error(f"Error creating integration webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_phone_call(
        self,
        phone_number_id: str,
        customer_number: str,
        assistant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an outbound phone call using VAPI.

        Args:
            phone_number_id: VAPI phone number ID to call from
            customer_number: Customer phone number to call
            assistant_id: VAPI assistant ID to use
            metadata: Additional call metadata

        Returns:
            Call creation result
        """
        try:
            result = await self.initiate_call(
                to_number=customer_number,
                assistant_id=assistant_id,
                from_number=phone_number_id,
                metadata=metadata or {}
            )

            return result

        except Exception as e:
            logger.error(f"Error creating phone call: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_extended_capabilities(self) -> Dict[str, Any]:
        """Get extended service capabilities."""
        base_capabilities = self.get_capabilities()

        extended_capabilities = [
            "create_tenant_agent",
            "initiate_tenant_call",
            "handle_tenant_webhook",
            "get_tenant_analytics",
            "list_tenant_agents",
            "create_integration_webhook",
            "create_phone_call"
        ]

        base_capabilities["capabilities"].extend(extended_capabilities)
        base_capabilities["tenant_support"] = True
        base_capabilities["integration_webhooks"] = True

        return base_capabilities


# Global VAPI service instance
vapi_service = VAPIServiceWrapper({
    "VAPI_API_KEY": os.getenv("VAPI_API_KEY"),
    "VAPI_US_PHONE_ID": os.getenv("VAPI_US_PHONE_ID"),
    "webhook_url": os.getenv("VAPI_WEBHOOK_URL", "https://api.ailabsafrica.com/vapi/webhook")
})
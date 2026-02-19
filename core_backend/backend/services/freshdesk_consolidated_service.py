"""
Consolidated Freshdesk Integration Service.
Handles all Freshdesk-related functionality with unified interface.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import from shared integration
from apps.shared.integration.freshdesk import (
    FreshdeskIntegration,
    FreshdeskConfig,
    FreshdeskTicket,
    FreshdeskContact,
    FreshdeskTicketStatus,
    FreshdeskTicketPriority
)

logger = logging.getLogger(__name__)


class FreshdeskServiceWrapper(FreshdeskIntegration):
    """
    Consolidated service for Freshdesk integration.
    Extends the shared Freshdesk service with additional functionality.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Freshdesk service with configuration.

        Args:
            config: Configuration dictionary with Freshdesk settings
        """
        if config:
            # Convert dict config to FreshdeskConfig
            freshdesk_config = FreshdeskConfig(
                domain=config.get("domain", ""),
                api_key=config.get("api_key", ""),
                timeout=config.get("timeout", 30),
                verify_ssl=config.get("verify_ssl", True),
                webhook_secret=config.get("webhook_secret")
            )
            super().__init__(freshdesk_config)
        else:
            # Create default config
            freshdesk_config = FreshdeskConfig(
                domain="",
                api_key="",
                timeout=30,
                verify_ssl=True
            )
            super().__init__(freshdesk_config)

        self.tenant_sessions = {}  # Track tenant-specific sessions

    async def create_tenant_ticket(
        self,
        tenant_id: str,
        ticket: FreshdeskTicket,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a tenant-specific Freshdesk ticket.

        Args:
            tenant_id: Tenant identifier
            ticket: Ticket configuration
            context: Additional context

        Returns:
            dict: Creation result with tenant info
        """
        try:
            result = await self.create_ticket(ticket)

            if result.get("success"):
                result["tenant_id"] = tenant_id
                result["context"] = context or {}

                # Additional tenant-specific processing can be added here
                await self._process_tenant_specific_ticket(tenant_id, ticket, result)

            return result

        except Exception as e:
            logger.error(f"Error creating tenant Freshdesk ticket: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def get_tenant_tickets(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get tickets for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            filters: Search filters
            limit: Maximum number of tickets
            offset: Pagination offset

        Returns:
            dict: Tickets with tenant info
        """
        try:
            # Add tenant-specific filters if needed
            tenant_filters = filters or {}
            tenant_filters["tenant_id"] = tenant_id

            result = await self.search_tickets(tenant_filters, limit, offset)

            if result.get("success"):
                result["tenant_id"] = tenant_id

            return result

        except Exception as e:
            logger.error(f"Error getting tenant Freshdesk tickets: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def handle_tenant_webhook(
        self,
        tenant_id: str,
        webhook_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle tenant-specific Freshdesk webhooks.

        Args:
            tenant_id: Tenant identifier
            webhook_data: Webhook payload
            context: Additional context

        Returns:
            dict: Webhook processing result
        """
        try:
            result = await self.handle_webhook(webhook_data)

            if result.get("success"):
                result["tenant_id"] = tenant_id
                result["context"] = context or {}

                # Additional tenant-specific processing can be added here
                await self._process_tenant_specific_webhook(tenant_id, webhook_data, result)

            return result

        except Exception as e:
            logger.error(f"Error handling tenant Freshdesk webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def get_tenant_analytics(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Start date for analytics
            end_date: End date for analytics

        Returns:
            dict: Analytics data with tenant info
        """
        try:
            result = await self.get_analytics(start_date, end_date)

            if result.get("success"):
                result["tenant_id"] = tenant_id

                # Add tenant-specific analytics processing
                await self._process_tenant_analytics(tenant_id, result)

            return result

        except Exception as e:
            logger.error(f"Error getting tenant Freshdesk analytics: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": tenant_id
            }

    async def _process_tenant_specific_ticket(
        self,
        tenant_id: str,
        ticket: FreshdeskTicket,
        result: Dict[str, Any]
    ):
        """
        Process tenant-specific ticket logic.

        Args:
            tenant_id: Tenant identifier
            ticket: Ticket configuration
            result: Ticket creation result
        """
        try:
            # This can be extended for tenant-specific ticket processing
            # For example: custom fields, routing rules, notifications
            logger.info(f"Processing tenant-specific ticket for {tenant_id}: {ticket.subject}")

            # Store ticket event for tenant analytics
            if not hasattr(self, 'tenant_ticket_events'):
                self.tenant_ticket_events = {}

            if tenant_id not in self.tenant_ticket_events:
                self.tenant_ticket_events[tenant_id] = []

            self.tenant_ticket_events[tenant_id].append({
                "ticket": ticket.dict(),
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error processing tenant-specific ticket: {e}")

    async def _process_tenant_specific_webhook(
        self,
        tenant_id: str,
        webhook_data: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        Process tenant-specific webhook logic.

        Args:
            tenant_id: Tenant identifier
            webhook_data: Webhook data
            result: Webhook processing result
        """
        try:
            # This can be extended for tenant-specific webhook processing
            # For example: custom integrations, notifications, analytics
            logger.info(f"Processing tenant-specific webhook for {tenant_id}")

            # Store webhook event for tenant analytics
            if not hasattr(self, 'tenant_webhook_events'):
                self.tenant_webhook_events = {}

            if tenant_id not in self.tenant_webhook_events:
                self.tenant_webhook_events[tenant_id] = []

            self.tenant_webhook_events[tenant_id].append({
                "webhook_data": webhook_data,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error processing tenant-specific webhook: {e}")

    async def _process_tenant_analytics(
        self,
        tenant_id: str,
        result: Dict[str, Any]
    ):
        """
        Process tenant-specific analytics.

        Args:
            tenant_id: Tenant identifier
            result: Analytics result
        """
        try:
            # Add tenant-specific metrics
            if hasattr(self, 'tenant_ticket_events') and tenant_id in self.tenant_ticket_events:
                result["tenant_tickets_created"] = len(self.tenant_ticket_events[tenant_id])

            if hasattr(self, 'tenant_webhook_events') and tenant_id in self.tenant_webhook_events:
                result["tenant_webhook_events"] = len(self.tenant_webhook_events[tenant_id])

        except Exception as e:
            logger.error(f"Error processing tenant analytics: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get base capabilities from shared integration.

        Returns:
            dict: Base capabilities
        """
        # Get methods available in the shared integration
        base_methods = [
            "create_ticket",
            "get_ticket",
            "get_tickets",
            "update_ticket",
            "delete_ticket",
            "create_contact",
            "get_contact",
            "update_contact",
            "delete_contact",
            "create_company",
            "get_company",
            "get_agents",
            "add_conversation",
            "health_check"
        ]

        return {
            "service": "freshdesk",
            "capabilities": base_methods,
            "api_reference": "https://developers.freshdesk.com/api/",
            "documentation": "https://developers.freshdesk.com/",
            "configured": bool(self.config.domain and self.config.api_key)
        }

    def get_extended_capabilities(self) -> Dict[str, Any]:
        """
        Get extended capabilities including tenant-specific features.

        Returns:
            dict: Extended capabilities
        """
        base_capabilities = self.get_capabilities()

        extended_capabilities = [
            "create_tenant_ticket",
            "get_tenant_tickets",
            "handle_tenant_webhook",
            "get_tenant_analytics",
            "create_integration_webhook"
        ]

        base_capabilities["capabilities"].extend(extended_capabilities)
        base_capabilities["tenant_support"] = True
        base_capabilities["integration_webhooks"] = True

        return base_capabilities


# Global Freshdesk service instance
freshdesk_consolidated_service = FreshdeskServiceWrapper({
    "domain": os.getenv("FRESHDESK_DOMAIN"),
    "api_key": os.getenv("FRESHDESK_API_KEY"),
    "webhook_secret": os.getenv("FRESHDESK_WEBHOOK_SECRET")
})
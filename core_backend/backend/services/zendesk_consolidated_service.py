"""
Zendesk Consolidated Integration Service.
Handles all Zendesk-related functionality with unified interface and MCP support.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import from shared integration
import sys
sys.path.append('/opt/kasaai/apps/shared')
from integration.zendesk import ZendeskIntegration, ZendeskConfig

logger = logging.getLogger(__name__)


class ZendeskServiceWrapper(ZendeskIntegration):
    """
    Consolidated service for Zendesk integration.
    Extends the shared Zendesk service with additional functionality and MCP support.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Zendesk service with configuration.

        Args:
            config: Configuration dictionary with Zendesk settings
        """
        if config:
            # Convert dict config to ZendeskConfig
            zendesk_config = ZendeskConfig(
                subdomain=config.get("subdomain", os.getenv("ZENDESK_SUBDOMAIN", "")),
                email=config.get("email", os.getenv("ZENDESK_EMAIL", "")),
                token=config.get("token", os.getenv("ZENDESK_TOKEN", "")),
                timeout=config.get("timeout", 30)
            )
            super().__init__(zendesk_config)
        else:
            # Use environment variables with defaults
            zendesk_config = ZendeskConfig(
                subdomain=os.getenv("ZENDESK_SUBDOMAIN", ""),
                email=os.getenv("ZENDESK_EMAIL", ""),
                token=os.getenv("ZENDESK_TOKEN", ""),
                timeout=30
            )
            super().__init__(zendesk_config)

    # Additional consolidated service methods
    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information and status."""
        try:
            account_info = await self.get_account_settings()
            return {
                "service_name": "Zendesk Consolidated",
                "service_type": "Customer Support Platform",
                "version": "1.0.0",
                "account_info": account_info,
                "capabilities": [
                    "ticket_management",
                    "user_management",
                    "organization_management",
                    "knowledge_base",
                    "reporting",
                    "automation",
                    "chat_support"
                ]
            }
        except Exception as e:
            return {
                "service_name": "Zendesk Consolidated",
                "service_type": "Customer Support Platform",
                "version": "1.0.0",
                "error": str(e),
                "capabilities": []
            }

    async def bulk_create_tickets(self, tickets_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple tickets in batch."""
        results = []
        for ticket_data in tickets_data:
            try:
                result = await self.create_ticket(ticket_data)
                results.append({"success": True, "data": result})
            except Exception as e:
                results.append({"success": False, "error": str(e), "data": ticket_data})
        return results

    async def get_ticket_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get ticket analytics for the last N days."""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date.replace(day=end_date.day - days) if end_date.day > days else end_date.replace(month=end_date.month - 1)

            tickets = await self.search_tickets(f"created>={start_date.strftime('%Y-%m-%d')}")

            # Process analytics
            total_tickets = len(tickets.get("results", []))
            resolved_tickets = len([t for t in tickets.get("results", []) if t.get("status") == "solved"])

            return {
                "period_days": days,
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0,
                "analytics_generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating ticket analytics: {e}")
            return {"error": str(e)}

    async def auto_assign_ticket(self, ticket_id: str, assignment_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-assign ticket based on rules."""
        try:
            ticket = await self.get_ticket(ticket_id)

            # Simple rule-based assignment
            assignee_id = None
            if "priority" in assignment_rules:
                priority = ticket.get("priority", "normal")
                assignee_id = assignment_rules["priority"].get(priority)

            if assignee_id:
                result = await self.update_ticket(ticket_id, {"assignee_id": assignee_id})
                return {"success": True, "assigned_to": assignee_id, "data": result}
            else:
                return {"success": False, "error": "No assignment rule matched"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def escalate_ticket(self, ticket_id: str, escalation_reason: str) -> Dict[str, Any]:
        """Escalate a ticket with reason."""
        try:
            update_data = {
                "priority": "urgent",
                "comment": {
                    "body": f"Ticket escalated: {escalation_reason}",
                    "public": False
                }
            }

            result = await self.update_ticket(ticket_id, update_data)
            return {"success": True, "data": result, "escalation_reason": escalation_reason}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Create a singleton instance for use throughout the application
def get_zendesk_service(config: Optional[Dict[str, Any]] = None) -> ZendeskServiceWrapper:
    """Get Zendesk service instance."""
    return ZendeskServiceWrapper(config)


# For backward compatibility
zendesk_consolidated_service = get_zendesk_service()
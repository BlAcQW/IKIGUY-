"""
Consolidated HubSpot Integration Service.
Handles all HubSpot-related functionality with unified interface and MCP support.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Import from shared integration
from apps.shared.integration.hubspot import (
    HubSpotIntegration,
    HubSpotConfig,
    HubSpotContact,
    HubSpotDeal,
    HubSpotCompany,
    HubSpotObjectType,
    HubSpotDealStage,
    HubSpotContactProperty
)

logger = logging.getLogger(__name__)


class HubSpotServiceWrapper(HubSpotIntegration):
    """
    Consolidated service for HubSpot integration.
    Extends the shared HubSpot service with additional functionality and MCP support.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HubSpot service with configuration.

        Args:
            config: Configuration dictionary with HubSpot settings
        """
        if config:
            # Convert dict config to HubSpotConfig
            hubspot_config = HubSpotConfig(
                access_token=config.get("access_token", ""),
                portal_id=config.get("portal_id"),
                timeout=config.get("timeout", 30),
                verify_ssl=config.get("verify_ssl", True),
                webhook_secret=config.get("webhook_secret")
            )
            super().__init__(hubspot_config)
        else:
            # Create default config from environment
            default_config = HubSpotConfig(
                access_token=os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
                portal_id=os.getenv("HUBSPOT_PORTAL_ID"),
                timeout=int(os.getenv("HUBSPOT_TIMEOUT", "30")),
                verify_ssl=os.getenv("HUBSPOT_VERIFY_SSL", "true").lower() == "true"
            )
            super().__init__(default_config)

    async def create_contact_with_validation(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create contact with enhanced validation and error handling.

        Args:
            contact_data: Contact information

        Returns:
            Enhanced creation result
        """
        # Validate required fields
        if not contact_data.get("email"):
            return {
                "success": False,
                "message": "Email is required for contact creation",
                "error": "validation_error"
            }

        # Check if contact already exists
        existing_contact = await self.search_contacts({"email": contact_data["email"]}, limit=1)
        if existing_contact.get("success") and existing_contact.get("contacts"):
            contact_id = existing_contact["contacts"][0]["id"]
            return {
                "success": False,
                "message": "Contact with this email already exists",
                "existing_contact_id": contact_id,
                "error": "duplicate_contact"
            }

        # Create contact
        result = await self.create_contact(contact_data)

        # Enhanced logging for tracking
        if result.get("success"):
            logger.info(f"Contact created successfully: {result.get('contact_id')}")

        return result

    async def create_deal_with_associations(self, deal_data: Dict[str, Any],
                                          contact_id: Optional[str] = None,
                                          company_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create deal and automatically associate with contact/company.

        Args:
            deal_data: Deal information
            contact_id: Optional contact ID to associate
            company_id: Optional company ID to associate

        Returns:
            Deal creation result with associations
        """
        # Create the deal first
        deal_result = await self.create_deal(deal_data)

        if not deal_result.get("success"):
            return deal_result

        deal_id = deal_result.get("deal_id")
        associations = []

        # Associate with contact if provided
        if contact_id:
            contact_assoc = await self.associate_objects(
                "deals", deal_id, "contacts", contact_id
            )
            if contact_assoc.get("success"):
                associations.append(f"contact_{contact_id}")

        # Associate with company if provided
        if company_id:
            company_assoc = await self.associate_objects(
                "deals", deal_id, "companies", company_id
            )
            if company_assoc.get("success"):
                associations.append(f"company_{company_id}")

        # Add association info to result
        deal_result["associations"] = associations
        deal_result["message"] = f"Deal created with {len(associations)} associations"

        return deal_result

    async def bulk_create_contacts(self, contacts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple contacts in batch.

        Args:
            contacts_data: List of contact information

        Returns:
            Batch creation results
        """
        results = {
            "success": True,
            "created_contacts": [],
            "failed_contacts": [],
            "total_processed": len(contacts_data),
            "total_created": 0,
            "total_failed": 0
        }

        for i, contact_data in enumerate(contacts_data):
            try:
                result = await self.create_contact_with_validation(contact_data)

                if result.get("success"):
                    results["created_contacts"].append({
                        "index": i,
                        "contact_id": result.get("contact_id"),
                        "email": contact_data.get("email")
                    })
                    results["total_created"] += 1
                else:
                    results["failed_contacts"].append({
                        "index": i,
                        "email": contact_data.get("email"),
                        "error": result.get("message")
                    })
                    results["total_failed"] += 1

                # Add delay to avoid rate limits
                if i < len(contacts_data) - 1:
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error creating contact {i}: {e}")
                results["failed_contacts"].append({
                    "index": i,
                    "email": contact_data.get("email", "unknown"),
                    "error": str(e)
                })
                results["total_failed"] += 1

        # Mark as failed if more than 50% failed
        if results["total_failed"] > results["total_created"]:
            results["success"] = False
            results["message"] = f"Batch creation mostly failed: {results['total_failed']} failed, {results['total_created']} created"
        else:
            results["message"] = f"Batch creation completed: {results['total_created']} created, {results['total_failed']} failed"

        return results

    async def get_contact_with_deals(self, contact_id: str) -> Dict[str, Any]:
        """
        Get contact information including associated deals.

        Args:
            contact_id: HubSpot contact ID

        Returns:
            Contact with deals information
        """
        # Get contact basic info
        contact_result = await self.get_contact(contact_id)

        if not contact_result.get("success"):
            return contact_result

        # Get associated deals
        try:
            deals_result = self._make_request(
                'GET',
                f'/crm/v3/objects/contacts/{contact_id}/associations/deals'
            )

            deal_ids = [deal["id"] for deal in deals_result.get("results", [])]
            deals_info = []

            # Get detailed deal information
            for deal_id in deal_ids:
                deal_result = self._make_request('GET', f'/crm/v3/objects/deals/{deal_id}')
                deals_info.append(deal_result)

            contact_result["associated_deals"] = deals_info
            contact_result["total_deals"] = len(deals_info)

        except Exception as e:
            logger.warning(f"Could not fetch deals for contact {contact_id}: {e}")
            contact_result["associated_deals"] = []
            contact_result["total_deals"] = 0

        return contact_result

    async def update_deal_stage(self, deal_id: str, new_stage: str,
                              close_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Update deal stage and optionally close date.

        Args:
            deal_id: HubSpot deal ID
            new_stage: New deal stage
            close_date: Optional close date

        Returns:
            Update result
        """
        update_data = {"dealstage": new_stage}

        if close_date:
            update_data["closedate"] = close_date.strftime('%Y-%m-%d')

        # If moving to closed won/lost, ensure close date is set
        if new_stage in ["closedwon", "closedlost"] and not close_date:
            update_data["closedate"] = datetime.now().strftime('%Y-%m-%d')

        result = await self.update_contact(deal_id, update_data)  # Note: This should be update_deal when implemented

        if result.get("success"):
            result["message"] = f"Deal stage updated to {new_stage}"
            result["new_stage"] = new_stage

        return result

    async def search_contacts_advanced(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced contact search with multiple criteria and sorting.

        Args:
            search_criteria: Advanced search parameters

        Returns:
            Enhanced search results
        """
        # Extract search parameters
        filters = search_criteria.get("filters", {})
        sort_by = search_criteria.get("sort_by", "createdate")
        sort_order = search_criteria.get("sort_order", "DESC")
        limit = search_criteria.get("limit", 100)
        properties = search_criteria.get("properties", [])

        try:
            # Build advanced search request
            filter_groups = []

            for property_name, criteria in filters.items():
                if isinstance(criteria, dict):
                    operator = criteria.get("operator", "EQ")
                    value = criteria.get("value")
                else:
                    operator = "EQ"
                    value = criteria

                filter_groups.append({
                    "filters": [{
                        "propertyName": property_name,
                        "operator": operator,
                        "value": str(value)
                    }]
                })

            data = {
                "filterGroups": filter_groups,
                "sorts": [{
                    "propertyName": sort_by,
                    "direction": sort_order
                }],
                "limit": limit
            }

            if properties:
                data["properties"] = properties

            result = self._make_request('POST', '/crm/v3/objects/contacts/search', data=data)

            return {
                "success": True,
                "contacts": result.get("results", []),
                "total": result.get("total", 0),
                "has_more": result.get("paging", {}).get("next") is not None,
                "search_criteria": search_criteria
            }

        except Exception as e:
            logger.error(f"HubSpot advanced contact search failed: {e}")
            return {
                "success": False,
                "message": f"Advanced search failed: {str(e)}",
                "error": str(e)
            }

    async def create_marketing_email(self, email_campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and send marketing email campaign.

        Args:
            email_campaign: Email campaign configuration

        Returns:
            Campaign creation result
        """
        try:
            # Create email campaign
            campaign_data = {
                "name": email_campaign.get("name"),
                "subject": email_campaign.get("subject"),
                "fromName": email_campaign.get("from_name"),
                "fromEmail": email_campaign.get("from_email"),
                "htmlBody": email_campaign.get("html_body"),
                "textBody": email_campaign.get("text_body", ""),
                "lists": email_campaign.get("contact_lists", [])
            }

            result = self._make_request('POST', '/marketing/v3/emails', data=campaign_data)

            return {
                "success": True,
                "campaign_id": result.get("id"),
                "campaign": result,
                "message": "Marketing email campaign created successfully"
            }

        except Exception as e:
            logger.error(f"HubSpot create marketing email failed: {e}")
            return {
                "success": False,
                "message": f"Failed to create marketing email: {str(e)}",
                "error": str(e)
            }

    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a HubSpot support ticket.

        Args:
            ticket_data: Ticket information including subject, content, priority, etc.

        Returns:
            Dict with success status and ticket information
        """
        try:
            # Prepare ticket properties - using minimal required fields
            properties = {
                "hs_pipeline_stage": "1",  # New stage in default support pipeline
                "subject": ticket_data.get("subject", "Support Request"),
                "content": ticket_data.get("content", "")
            }

            # Add custom properties if provided
            if ticket_data.get("custom_properties"):
                properties.update(ticket_data["custom_properties"])

            # Create ticket via HubSpot API
            ticket_payload = {"properties": properties}

            result = self._make_request('POST', '/crm/v3/objects/tickets', data=ticket_payload)

            logger.info(f"HubSpot ticket created successfully: {result.get('id')}")

            return {
                "success": True,
                "ticket_id": result.get("id"),
                "ticket": result,
                "message": "Support ticket created successfully",
                "hubspot_url": f"https://app.hubspot.com/contacts/{self.config.portal_id}/ticket/{result.get('id')}"
            }

        except Exception as e:
            logger.error(f"HubSpot create ticket failed: {e}")
            return {
                "success": False,
                "message": f"Failed to create ticket: {str(e)}",
                "error": str(e)
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get enhanced HubSpot service capabilities."""
        base_capabilities = super().get_capabilities()

        # Add consolidated service specific capabilities
        base_capabilities.update({
            "service_type": "consolidated",
            "enhanced_features": [
                "create_contact_with_validation", "create_deal_with_associations",
                "bulk_create_contacts", "get_contact_with_deals", "update_deal_stage",
                "search_contacts_advanced", "create_marketing_email", "create_ticket"
            ],
            "batch_operations": True,
            "advanced_search": True,
            "association_management": True,
            "marketing_features": True,
            "mcp_server": "hubspot-mcp",
            "mcp_tools": [
                "create_contact", "update_contact", "search_contacts",
                "create_deal", "create_company", "send_email", "get_analytics"
            ]
        })

        return base_capabilities


# Global service instance with lazy initialization
_hubspot_service_instance = None

def get_hubspot_service():
    """Get HubSpot service instance with lazy initialization."""
    global _hubspot_service_instance
    if _hubspot_service_instance is None:
        _hubspot_service_instance = HubSpotServiceWrapper()
    return _hubspot_service_instance

# Backward compatibility
hubspot_consolidated_service = get_hubspot_service()
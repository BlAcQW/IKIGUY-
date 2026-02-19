#!/usr/bin/env python3
"""
HubSpot MCP Server

Provides MCP-compliant server for HubSpot integration with comprehensive
CRM, marketing, and sales automation capabilities.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

# MCP Server imports
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP server libraries not available. Install with: pip install mcp")

# Import HubSpot integration
from hubspot import HubSpotIntegration, HubSpotConfig

logger = logging.getLogger(__name__)

class HubSpotMCPServer:
    """MCP Server for HubSpot integration."""

    def __init__(self):
        """Initialize HubSpot MCP server."""
        self.hubspot = None
        self.server = Server("hubspot-mcp")
        self._setup_tools()

    def _get_hubspot_client(self) -> HubSpotIntegration:
        """Get or create HubSpot client."""
        if not self.hubspot:
            config = HubSpotConfig(
                access_token=os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
                portal_id=os.getenv("HUBSPOT_PORTAL_ID"),
                timeout=int(os.getenv("HUBSPOT_TIMEOUT", "30"))
            )
            self.hubspot = HubSpotIntegration(config)
        return self.hubspot

    def _setup_tools(self):
        """Setup MCP tools for HubSpot operations."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available HubSpot tools."""
            return [
                types.Tool(
                    name="test_hubspot_connection",
                    description="Test HubSpot API connection and authentication",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="create_hubspot_contact",
                    description="Create a new contact in HubSpot CRM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "Contact email address (required)"},
                            "firstname": {"type": "string", "description": "Contact first name"},
                            "lastname": {"type": "string", "description": "Contact last name"},
                            "phone": {"type": "string", "description": "Contact phone number"},
                            "company": {"type": "string", "description": "Contact company name"},
                            "jobtitle": {"type": "string", "description": "Contact job title"},
                            "website": {"type": "string", "description": "Contact website"},
                            "lifecyclestage": {"type": "string", "description": "Lifecycle stage (subscriber, lead, marketingqualifiedlead, salesqualifiedlead, opportunity, customer, evangelist, other)"},
                            "leadsource": {"type": "string", "description": "Lead source"}
                        },
                        "required": ["email"]
                    }
                ),
                types.Tool(
                    name="update_hubspot_contact",
                    description="Update an existing contact in HubSpot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contact_id": {"type": "string", "description": "HubSpot contact ID"},
                            "email": {"type": "string", "description": "Updated email address"},
                            "firstname": {"type": "string", "description": "Updated first name"},
                            "lastname": {"type": "string", "description": "Updated last name"},
                            "phone": {"type": "string", "description": "Updated phone number"},
                            "company": {"type": "string", "description": "Updated company name"},
                            "jobtitle": {"type": "string", "description": "Updated job title"},
                            "lifecyclestage": {"type": "string", "description": "Updated lifecycle stage"}
                        },
                        "required": ["contact_id"]
                    }
                ),
                types.Tool(
                    name="search_hubspot_contacts",
                    description="Search for contacts in HubSpot CRM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "Search by email address"},
                            "company": {"type": "string", "description": "Search by company name"},
                            "firstname": {"type": "string", "description": "Search by first name"},
                            "lastname": {"type": "string", "description": "Search by last name"},
                            "limit": {"type": "integer", "description": "Maximum number of results (default: 100)", "minimum": 1, "maximum": 1000}
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_hubspot_contact",
                    description="Get detailed contact information from HubSpot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contact_id": {"type": "string", "description": "HubSpot contact ID"},
                            "properties": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific properties to retrieve (optional)"
                            }
                        },
                        "required": ["contact_id"]
                    }
                ),
                types.Tool(
                    name="create_hubspot_deal",
                    description="Create a new deal in HubSpot CRM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dealname": {"type": "string", "description": "Deal name (required)"},
                            "amount": {"type": "number", "description": "Deal amount/value"},
                            "dealstage": {"type": "string", "description": "Deal stage (appointmentscheduled, qualifiedtobuy, presentationscheduled, decisionmakerboughtin, contractsent, closedwon, closedlost)"},
                            "closedate": {"type": "string", "format": "date", "description": "Expected close date (YYYY-MM-DD)"},
                            "pipeline": {"type": "string", "description": "Sales pipeline"},
                            "dealtype": {"type": "string", "description": "Deal type"},
                            "description": {"type": "string", "description": "Deal description"}
                        },
                        "required": ["dealname"]
                    }
                ),
                types.Tool(
                    name="create_hubspot_company",
                    description="Create a new company in HubSpot CRM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Company name (required)"},
                            "domain": {"type": "string", "description": "Company domain/website"},
                            "industry": {"type": "string", "description": "Company industry"},
                            "phone": {"type": "string", "description": "Company phone number"},
                            "city": {"type": "string", "description": "Company city"},
                            "state": {"type": "string", "description": "Company state/region"},
                            "country": {"type": "string", "description": "Company country"},
                            "website": {"type": "string", "description": "Company website URL"}
                        },
                        "required": ["name"]
                    }
                ),
                types.Tool(
                    name="associate_hubspot_objects",
                    description="Create associations between HubSpot objects (contact-company, contact-deal, company-deal)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_object_type": {"type": "string", "description": "Source object type (contacts, companies, deals)", "enum": ["contacts", "companies", "deals"]},
                            "from_object_id": {"type": "string", "description": "Source object ID"},
                            "to_object_type": {"type": "string", "description": "Target object type (contacts, companies, deals)", "enum": ["contacts", "companies", "deals"]},
                            "to_object_id": {"type": "string", "description": "Target object ID"},
                            "association_type": {"type": "string", "description": "Association type (default: default)", "default": "default"}
                        },
                        "required": ["from_object_type", "from_object_id", "to_object_type", "to_object_id"]
                    }
                ),
                types.Tool(
                    name="send_hubspot_email",
                    description="Send transactional email through HubSpot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "Recipient email address"},
                            "from": {"type": "string", "description": "Sender email address"},
                            "subject": {"type": "string", "description": "Email subject"},
                            "body": {"type": "string", "description": "Email body (HTML or text)"},
                            "template_id": {"type": "string", "description": "HubSpot email template ID (optional)"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                ),
                types.Tool(
                    name="get_hubspot_analytics",
                    description="Get analytics data from HubSpot for specified object type and date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_type": {"type": "string", "description": "Object type for analytics (contacts, deals, companies)", "enum": ["contacts", "deals", "companies"]},
                            "start_date": {"type": "string", "format": "date", "description": "Start date for analytics (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "format": "date", "description": "End date for analytics (YYYY-MM-DD)"}
                        },
                        "required": ["object_type", "start_date", "end_date"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls for HubSpot operations."""
            try:
                hubspot_client = self._get_hubspot_client()

                if name == "test_hubspot_connection":
                    result = await hubspot_client.test_connection()

                elif name == "create_hubspot_contact":
                    result = await hubspot_client.create_contact(arguments)

                elif name == "update_hubspot_contact":
                    contact_id = arguments.pop("contact_id")
                    result = await hubspot_client.update_contact(contact_id, arguments)

                elif name == "search_hubspot_contacts":
                    limit = arguments.pop("limit", 100)
                    filters = {k: v for k, v in arguments.items() if v is not None}
                    result = await hubspot_client.search_contacts(filters, limit)

                elif name == "get_hubspot_contact":
                    contact_id = arguments["contact_id"]
                    properties = arguments.get("properties")
                    result = await hubspot_client.get_contact(contact_id, properties)

                elif name == "create_hubspot_deal":
                    # Convert date string to datetime if provided
                    if "closedate" in arguments and arguments["closedate"]:
                        arguments["closedate"] = datetime.strptime(arguments["closedate"], "%Y-%m-%d")
                    result = await hubspot_client.create_deal(arguments)

                elif name == "create_hubspot_company":
                    result = await hubspot_client.create_company(arguments)

                elif name == "associate_hubspot_objects":
                    result = await hubspot_client.associate_objects(
                        arguments["from_object_type"],
                        arguments["from_object_id"],
                        arguments["to_object_type"],
                        arguments["to_object_id"],
                        arguments.get("association_type", "default")
                    )

                elif name == "send_hubspot_email":
                    result = await hubspot_client.send_email(arguments)

                elif name == "get_hubspot_analytics":
                    start_date = datetime.strptime(arguments["start_date"], "%Y-%m-%d")
                    end_date = datetime.strptime(arguments["end_date"], "%Y-%m-%d")
                    result = await hubspot_client.get_analytics(
                        arguments["object_type"],
                        start_date,
                        end_date
                    )

                else:
                    result = {
                        "success": False,
                        "error": f"Unknown tool: {name}"
                    }

                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]

            except Exception as e:
                logger.error(f"HubSpot MCP tool error: {e}")
                error_result = {
                    "success": False,
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }
                return [types.TextContent(
                    type="text",
                    text=json.dumps(error_result, indent=2)
                )]

async def main():
    """Run the HubSpot MCP server."""
    if not MCP_AVAILABLE:
        print("ERROR: MCP server libraries not available")
        print("Install with: pip install mcp")
        return

    # Validate environment
    if not os.getenv("HUBSPOT_ACCESS_TOKEN"):
        print("WARNING: HUBSPOT_ACCESS_TOKEN not set")

    server_instance = HubSpotMCPServer()

    # Run server
    options = InitializationOptions(
        server_name="hubspot-mcp",
        server_version="1.0.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )

    await mcp.server.stdio.stdio_server(server_instance.server, options)

if __name__ == "__main__":
    asyncio.run(main())
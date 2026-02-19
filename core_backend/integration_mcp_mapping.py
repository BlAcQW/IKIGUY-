"""
Integration MCP (Model Context Protocol) Endpoint Mappings
Maps integrations to their available MCP servers and endpoints
"""

INTEGRATION_MCP_ENDPOINTS = {
    # Available MCP Servers (based on current session capabilities)

    # Automation Platforms - n8n has dedicated MCP server
    "n8n": {
        "mcp_server_name": "n8n-mcp",
        "mcp_endpoint_url": "mcp://n8n-mcp/workflows",
        "mcp_available": True
    },

    # Database - Supabase has dedicated MCP server
    "mongodb": {
        "mcp_server_name": "supabase",  # MongoDB operations via Supabase
        "mcp_endpoint_url": "mcp://supabase/database",
        "mcp_available": True
    },

    # Documentation & Context - Context7 for documentation lookup
    "confluence": {
        "mcp_server_name": "context7",
        "mcp_endpoint_url": "mcp://context7/docs/confluence",
        "mcp_available": True
    },
    "notion": {
        "mcp_server_name": "context7",
        "mcp_endpoint_url": "mcp://context7/docs/notion",
        "mcp_available": True
    },

    # Search & Web - Brave Search and Firecrawl
    "brave": {
        "mcp_server_name": "brave-search",
        "mcp_endpoint_url": "mcp://brave-search/search",
        "mcp_available": True
    },
    "google_analytics": {
        "mcp_server_name": "brave-search",
        "mcp_endpoint_url": "mcp://brave-search/analytics",
        "mcp_available": True
    },

    # Web Scraping & Content
    "web_chat": {
        "mcp_server_name": "firecrawl",
        "mcp_endpoint_url": "mcp://firecrawl/web-content",
        "mcp_available": True
    },

    # Voice AI - Vapi has dedicated MCP server
    "chat": {
        "mcp_server_name": "vapi",
        "mcp_endpoint_url": "mcp://vapi/chat",
        "mcp_available": True
    },
    "vapi": {
        "mcp_server_name": "vapi",
        "mcp_endpoint_url": "mcp://vapi/assistants",
        "mcp_available": True
    },

    # Future MCP Server Candidates (currently API-only but could have MCP)
    "freshdesk": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "zendesk": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "pipedrive": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "intercom": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "mixpanel": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "zoho": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "servicenow": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "grafana": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "prometheus": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },

    # Payment Systems - Could benefit from MCP servers
    "paystack": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "flutterwave": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },

    # Communication Platforms
    "telegram": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "whatsapp": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "whatsapp_business": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "discord": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },

    # Cloud & Productivity
    "google_drive": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "google_workspace": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "microsoft_365": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "microsoft_dynamics": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },

    # Automation (additional)
    "make": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    },
    "zapier": {
        "mcp_server_name": None,
        "mcp_endpoint_url": None,
        "mcp_available": False
    }
}

# Summary of MCP Integration Coverage
MCP_INTEGRATION_STATS = {
    "total_integrations": 44,
    "mcp_available": len([k for k, v in INTEGRATION_MCP_ENDPOINTS.items() if v.get("mcp_available", False)]),
    "mcp_servers_used": list(set([v.get("mcp_server_name") for v in INTEGRATION_MCP_ENDPOINTS.values() if v.get("mcp_server_name")])),
    "coverage_percentage": 0  # Will be calculated
}

MCP_INTEGRATION_STATS["coverage_percentage"] = (MCP_INTEGRATION_STATS["mcp_available"] / MCP_INTEGRATION_STATS["total_integrations"]) * 100

# Recommended Priority Integrations for New MCP Servers
PRIORITY_MCP_CANDIDATES = [
    {
        "integration": "freshdesk",
        "category": "Business Tools",
        "priority": "High",
        "reason": "Major CRM platform, high automation value"
    },
    {
        "integration": "paystack",
        "category": "Payment Gateways",
        "priority": "High",
        "reason": "Critical payment infrastructure for African markets"
    },
    {
        "integration": "telegram",
        "category": "Communication",
        "priority": "High",
        "reason": "Major messaging platform with bot ecosystem"
    },
    {
        "integration": "google_drive",
        "category": "Productivity & Cloud",
        "priority": "High",
        "reason": "Essential file management and collaboration"
    },
    {
        "integration": "whatsapp_business",
        "category": "Communication",
        "priority": "Medium",
        "reason": "Important for business messaging in emerging markets"
    }
]
"""
Integration Catalog Service for managing third-party service integrations.
"""

import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..mongo import get_database
from .integration_category_service import integration_category_service


class Integration(BaseModel):
    """Integration model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Name of the integration")
    file_name: str = Field(..., description="File name of the integration module")
    description: str = Field(..., description="Description of the integration capabilities")
    integration_category_id: str = Field(..., description="ID of the integration category")
    providers: List[str] = Field(default_factory=list, description="List of supported providers")
    features: List[str] = Field(default_factory=list, description="List of available features")
    authentication_methods: List[str] = Field(default_factory=list, description="Supported authentication methods")
    capabilities: List[str] = Field(default_factory=list, description="Core capabilities")
    api_reference_url: Optional[str] = Field(default=None, description="URL to API reference documentation")
    documentation_url: Optional[str] = Field(default=None, description="URL to general documentation")
    mcp_server_name: Optional[str] = Field(default=None, description="MCP server name for this integration")
    mcp_endpoint_url: Optional[str] = Field(default=None, description="MCP endpoint URL for direct integration access")
    mcp_available: bool = Field(default=False, description="Whether MCP access is available for this integration")
    is_active: bool = Field(default=True)


class IntegrationCreate(BaseModel):
    """Model for creating integrations."""
    name: str
    file_name: str
    description: str
    integration_category_id: str
    providers: List[str] = []
    features: List[str] = []
    authentication_methods: List[str] = []
    capabilities: List[str] = []
    api_reference_url: Optional[str] = None
    documentation_url: Optional[str] = None
    mcp_server_name: Optional[str] = None
    mcp_endpoint_url: Optional[str] = None
    mcp_available: bool = False


class IntegrationUpdate(BaseModel):
    """Model for updating integrations."""
    name: Optional[str] = None
    file_name: Optional[str] = None
    description: Optional[str] = None
    integration_category_id: Optional[str] = None
    providers: Optional[List[str]] = None
    features: Optional[List[str]] = None
    authentication_methods: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    api_reference_url: Optional[str] = None
    documentation_url: Optional[str] = None
    mcp_server_name: Optional[str] = None
    mcp_endpoint_url: Optional[str] = None
    mcp_available: Optional[bool] = None
    is_active: Optional[bool] = None


class IntegrationCatalogService:
    """Service for managing integrations catalog."""

    def __init__(self):
        self.db = get_database()
        self.collection = self.db.integrations

    async def create_integration(self, integration_data: IntegrationCreate) -> Integration:
        """Create a new integration."""
        integration = Integration(**integration_data.dict())
        result = await self.collection.insert_one(integration.dict())
        if result.inserted_id:
            return integration
        raise Exception("Failed to create integration")

    async def get_integration(self, integration_id: str) -> Optional[Integration]:
        """Get integration by ID."""
        integration_doc = await self.collection.find_one({"id": integration_id})
        if integration_doc:
            return Integration(**integration_doc)
        return None

    async def get_integration_by_name(self, name: str) -> Optional[Integration]:
        """Get integration by name."""
        integration_doc = await self.collection.find_one({"name": name})
        if integration_doc:
            return Integration(**integration_doc)
        return None

    async def list_integrations(self) -> List[Integration]:
        """List all integrations."""
        cursor = self.collection.find({"is_active": True})
        integrations_docs = await cursor.to_list(length=None)
        return [Integration(**doc) for doc in integrations_docs]

    async def list_integrations_by_category(self, category_id: str) -> List[Integration]:
        """List integrations by category."""
        cursor = self.collection.find({
            "integration_category_id": category_id,
            "is_active": True
        })
        integrations_docs = await cursor.to_list(length=None)
        return [Integration(**doc) for doc in integrations_docs]

    async def update_integration(self, integration_id: str, update_data: IntegrationUpdate) -> Optional[Integration]:
        """Update an integration."""
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if not update_dict:
            return await self.get_integration(integration_id)

        result = await self.collection.update_one(
            {"id": integration_id},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return await self.get_integration(integration_id)
        return None

    async def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration (soft delete)."""
        result = await self.collection.update_one(
            {"id": integration_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0

    async def populate_default_integrations(self) -> List[Integration]:
        """Populate default integrations from SIMPLE_INTEGRATIONS_LIST."""
        # Import URL and MCP mappings
        from ...integration_urls_mapping import INTEGRATION_URLS
        from ...integration_mcp_mapping import INTEGRATION_MCP_ENDPOINTS

        # Get all categories first
        categories = await integration_category_service.list_categories()
        category_map = {cat.name: cat.id for cat in categories}

        # Integration data organized by category
        integrations_data = {
            "Communication": [
                {
                    "name": "Chat",
                    "file_name": "chat.py",
                    "description": "General chat system integration for real-time messaging and communication",
                    "capabilities": ["message_sending", "real_time_chat", "group_messaging", "chat_history"]
                },
                {
                    "name": "Email",
                    "file_name": "email.py",
                    "description": "Email service providers including SendGrid, Gmail API, AWS SES, and SMTP",
                    "providers": ["SendGrid", "Gmail API", "AWS SES", "SMTP"],
                    "capabilities": ["email_sending", "template_messaging", "bulk_email", "delivery_tracking"]
                },
                {
                    "name": "SMS",
                    "file_name": "sms.py",
                    "description": "SMS messaging services for mobile communication",
                    "capabilities": ["sms_sending", "bulk_sms", "delivery_reports", "two_way_messaging"]
                },
                {
                    "name": "SMS Providers",
                    "file_name": "sms_providers.py",
                    "description": "Multiple SMS gateway providers for diverse messaging needs",
                    "capabilities": ["multi_provider_sms", "failover_messaging", "cost_optimization"]
                },
                {
                    "name": "Telegram",
                    "file_name": "telegram.py",
                    "description": "Telegram bot and messaging API integration",
                    "capabilities": ["bot_messaging", "group_management", "media_sharing", "webhook_handling"]
                },
                {
                    "name": "Web Chat",
                    "file_name": "web_chat.py",
                    "description": "Website chat widget integration for customer support",
                    "capabilities": ["widget_embedding", "live_chat", "visitor_tracking", "chat_routing"]
                },
                {
                    "name": "WhatsApp",
                    "file_name": "whatsapp.py",
                    "description": "WhatsApp Business API integration",
                    "capabilities": ["whatsapp_messaging", "media_sharing", "template_messages", "business_profile"]
                },
                {
                    "name": "WhatsApp Business",
                    "file_name": "whatsapp_business.py",
                    "description": "Enhanced WhatsApp Business features for enterprise communication",
                    "capabilities": ["advanced_templates", "catalog_integration", "payment_links", "customer_support"]
                }
            ],
            "Payment Systems": [
                {
                    "name": "Bank USSD",
                    "file_name": "bank_ussd.py",
                    "description": "Bank USSD APIs for mobile banking operations and transactions",
                    "capabilities": ["ussd_transactions", "balance_inquiry", "bill_payments", "mobile_banking"]
                },
                {
                    "name": "Ghana Interbank",
                    "file_name": "ghana_interbank.py",
                    "description": "Ghana interbank payment systems for financial transactions",
                    "capabilities": ["interbank_transfers", "payment_processing", "transaction_verification"]
                },
                {
                    "name": "Local Payment Systems",
                    "file_name": "local_payment_systems.py",
                    "description": "Local and regional payment methods for diverse markets",
                    "capabilities": ["local_payments", "regional_gateways", "currency_support"]
                },
                {
                    "name": "MTN Mobile Money",
                    "file_name": "mtn_mobile_money.py",
                    "description": "MTN mobile money integration for African markets",
                    "capabilities": ["mobile_money", "payment_processing", "transaction_status", "balance_inquiry"]
                }
            ],
            "Business Tools": [
                {
                    "name": "HubSpot",
                    "file_name": "hubspot.py",
                    "description": "Comprehensive CRM, marketing, sales, and service platform with helpdesk capabilities",
                    "providers": ["HubSpot"],
                    "capabilities": ["crm_management", "lead_management", "deal_tracking", "contact_management", "ticket_management", "helpdesk", "email_marketing", "sales_automation", "analytics", "reporting"],
                    "authentication_methods": ["Private App Token", "Developer API Key"],
                    "features": ["contacts", "companies", "deals", "tickets", "emails", "calls", "meetings", "tasks", "notes", "pipelines", "workflows"]
                },
                {
                    "name": "Freshdesk",
                    "file_name": "freshdesk.py",
                    "description": "Customer support ticketing system integration",
                    "capabilities": ["ticket_management", "customer_support", "knowledge_base", "agent_workflows"]
                },
                {
                    "name": "Freshsales",
                    "file_name": "freshsales.py",
                    "description": "Sales CRM platform integration",
                    "capabilities": ["lead_management", "sales_pipeline", "contact_management", "deal_tracking"]
                },
                {
                    "name": "Intercom",
                    "file_name": "intercom.py",
                    "description": "Customer messaging platform for support and engagement",
                    "capabilities": ["customer_messaging", "live_chat", "user_segmentation", "automation"]
                },
                {
                    "name": "Mixpanel",
                    "file_name": "mixpanel.py",
                    "description": "Analytics and user tracking platform",
                    "capabilities": ["event_tracking", "user_analytics", "cohort_analysis", "funnel_analysis"]
                },
                {
                    "name": "Pipedrive",
                    "file_name": "pipedrive.py",
                    "description": "Sales CRM and pipeline management system",
                    "capabilities": ["pipeline_management", "deal_tracking", "sales_automation", "reporting"]
                },
                {
                    "name": "ServiceNow",
                    "file_name": "servicenow.py",
                    "description": "IT service management platform for enterprise operations",
                    "capabilities": ["incident_management", "change_management", "service_catalog", "workflow_automation"]
                },
                {
                    "name": "Zendesk",
                    "file_name": "zendesk.py",
                    "description": "Customer service platform integration",
                    "capabilities": ["ticket_management", "customer_support", "knowledge_base", "reporting"]
                },
                {
                    "name": "Zoho",
                    "file_name": "zoho.py",
                    "description": "Business application suite integration",
                    "capabilities": ["crm_integration", "email_marketing", "project_management", "accounting"]
                },
                {
                    "name": "FindHelp",
                    "file_name": "findhelp.py",
                    "description": "Social services resource platform integration",
                    "capabilities": ["resource_directory", "social_services", "community_support"]
                },
                {
                    "name": "Grafana",
                    "file_name": "grafana.py",
                    "description": "Monitoring and observability platform",
                    "capabilities": ["dashboard_creation", "metrics_visualization", "alerting", "monitoring"]
                },
                {
                    "name": "Prometheus",
                    "file_name": "prometheus.py",
                    "description": "Monitoring and alerting system",
                    "capabilities": ["metrics_collection", "time_series_data", "alerting", "monitoring"]
                }
            ],
            "Productivity & Cloud": [
                {
                    "name": "Google Analytics",
                    "file_name": "google_analytics.py",
                    "description": "Web analytics and tracking platform",
                    "capabilities": ["web_analytics", "traffic_analysis", "conversion_tracking", "reporting"]
                },
                {
                    "name": "Google Drive",
                    "file_name": "google_drive.py",
                    "description": "Cloud file storage and management system",
                    "capabilities": ["file_storage", "document_sharing", "collaboration", "sync"]
                },
                {
                    "name": "Google Maps Clinics",
                    "file_name": "google_maps_clinics.py",
                    "description": "Healthcare location services and clinic mapping",
                    "capabilities": ["location_services", "clinic_finder", "mapping", "directions"]
                },
                {
                    "name": "Google Workspace",
                    "file_name": "google_workspace.py",
                    "description": "Gmail, Drive, Calendar, Docs integration suite",
                    "capabilities": ["email_integration", "calendar_management", "document_collaboration", "workspace_automation"]
                },
                {
                    "name": "Microsoft 365",
                    "file_name": "microsoft_365.py",
                    "description": "Office suite integration for productivity",
                    "capabilities": ["office_integration", "email_management", "document_editing", "collaboration"]
                },
                {
                    "name": "Microsoft Dynamics",
                    "file_name": "microsoft_dynamics.py",
                    "description": "CRM and business applications platform",
                    "capabilities": ["crm_integration", "business_processes", "customer_management", "sales_automation"]
                },
                {
                    "name": "Notion",
                    "file_name": "notion.py",
                    "description": "Note-taking and collaboration platform",
                    "capabilities": ["note_management", "team_collaboration", "knowledge_base", "project_planning"]
                }
            ],
            "ERP & Accounting": [
                {
                    "name": "Financial Systems",
                    "file_name": "financial_systems.py",
                    "description": "General financial system integration for accounting and finance",
                    "capabilities": ["financial_reporting", "accounting_automation", "transaction_management", "compliance"]
                },
                {
                    "name": "Odoo",
                    "file_name": "odoo.py",
                    "description": "Open-source ERP platform integration",
                    "capabilities": ["erp_integration", "inventory_management", "accounting", "project_management"]
                },
                {
                    "name": "QuickBooks",
                    "file_name": "quickbooks.py",
                    "description": "Accounting and bookkeeping software integration",
                    "capabilities": ["accounting_integration", "financial_reporting", "invoice_management", "expense_tracking"]
                },
                {
                    "name": "MongoDB",
                    "file_name": "mongodb.py",
                    "description": "Database integration and management system",
                    "capabilities": ["database_integration", "data_management", "query_automation", "backup_management"]
                }
            ],
            "Automation Platforms": [
                {
                    "name": "Make",
                    "file_name": "make.py",
                    "description": "Visual automation platform (formerly Integromat)",
                    "capabilities": ["workflow_automation", "visual_builder", "multi_app_integration", "data_transformation"]
                },
                {
                    "name": "N8N",
                    "file_name": "n8n.py",
                    "description": "Open-source workflow automation platform",
                    "capabilities": ["workflow_creation", "node_based_automation", "trigger_management", "data_processing"]
                },
                {
                    "name": "Zapier",
                    "file_name": "zapier.py",
                    "description": "Popular automation platform for app integration",
                    "capabilities": ["zap_automation", "trigger_actions", "multi_app_workflows", "conditional_logic"]
                }
            ],
            "Payment Gateways": [
                {
                    "name": "Flutterwave",
                    "file_name": "flutterwave.py",
                    "description": "African payment gateway for online transactions",
                    "capabilities": ["payment_processing", "multi_currency", "card_payments", "mobile_money"]
                },
                {
                    "name": "Paystack",
                    "file_name": "paystack.py",
                    "description": "Nigerian payment platform for online businesses",
                    "capabilities": ["payment_processing", "subscription_billing", "transfer_automation", "payment_links"]
                }
            ],
            "Specialized Services": [
                {
                    "name": "Confluence",
                    "file_name": "confluence.py",
                    "description": "Team collaboration and documentation platform",
                    "capabilities": ["documentation", "team_collaboration", "knowledge_sharing", "content_management"]
                },
                {
                    "name": "Discord",
                    "file_name": "discord.py",
                    "description": "Community platform integration for team communication",
                    "capabilities": ["community_management", "voice_chat", "server_automation", "bot_integration"]
                },
                {
                    "name": "Healthcare Systems",
                    "file_name": "healthcare_systems.py",
                    "description": "Medical system integrations for healthcare providers",
                    "capabilities": ["ehr_integration", "patient_management", "appointment_scheduling", "medical_records"]
                },
                {
                    "name": "Integration Manager",
                    "file_name": "integration_manager.py",
                    "description": "Core integration management system",
                    "capabilities": ["integration_lifecycle", "api_coordination", "webhook_handling", "system_monitoring"]
                },
                {
                    "name": "Types",
                    "file_name": "types.py",
                    "description": "Integration type definitions and schemas",
                    "capabilities": ["type_definitions", "schema_validation", "data_models", "api_contracts"]
                }
            ]
        }

        created_integrations = []
        for category_name, integrations in integrations_data.items():
            category_id = category_map.get(category_name)
            if not category_id:
                continue

            for integration_data in integrations:
                existing = await self.get_integration_by_name(integration_data["name"])
                if not existing:
                    # Get file name without .py extension for URL and MCP lookup
                    file_key = integration_data["file_name"].replace(".py", "")
                    urls = INTEGRATION_URLS.get(file_key, {})
                    mcp_data = INTEGRATION_MCP_ENDPOINTS.get(file_key, {})

                    # Add URL and MCP fields to integration data
                    integration_data_with_urls = {
                        **integration_data,
                        "api_reference_url": urls.get("api_reference_url"),
                        "documentation_url": urls.get("documentation_url"),
                        "mcp_server_name": mcp_data.get("mcp_server_name"),
                        "mcp_endpoint_url": mcp_data.get("mcp_endpoint_url"),
                        "mcp_available": mcp_data.get("mcp_available", False)
                    }

                    integration_create = IntegrationCreate(
                        integration_category_id=category_id,
                        **integration_data_with_urls
                    )
                    integration = await self.create_integration(integration_create)
                    created_integrations.append(integration)
                else:
                    created_integrations.append(existing)

        return created_integrations


# Global service instance
integration_catalog_service = IntegrationCatalogService()
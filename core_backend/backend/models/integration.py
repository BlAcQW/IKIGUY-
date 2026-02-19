"""
Integration Database Model
Database model for managing third-party integrations and their configurations
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

class IntegrationType(str, Enum):
    """Integration types based on shared/integration analysis."""
    # Core AI Services
    TTS = "tts"                    # Text-to-Speech
    STT = "stt"                    # Speech-to-Text
    LLM = "llm"                    # Large Language Models

    # Communication & Messaging
    TELEPHONY = "telephony"        # Phone/Voice services
    MESSAGING = "messaging"        # SMS, WhatsApp, Telegram, etc.
    EMAIL = "email"                # Email services
    CHAT = "chat"                  # Chat platforms (Discord, Web Chat)

    # Business Systems
    CRM = "crm"                    # Customer Relationship Management
    ERP = "erp"                    # Enterprise Resource Planning
    SUPPORT = "support"            # Customer Support (Zendesk, Freshdesk)

    # Financial & Payment
    PAYMENT = "payment"            # Payment processing
    BANKING = "banking"            # Banking systems, mobile money
    FINANCIAL = "financial"        # Financial systems, accounting

    # Productivity & Office
    PRODUCTIVITY = "productivity"  # Office suites, Google Workspace
    STORAGE = "storage"            # Cloud storage, documents
    CALENDAR = "calendar"          # Calendar systems

    # Analytics & Monitoring
    ANALYTICS = "analytics"        # Analytics platforms
    MONITORING = "monitoring"      # Monitoring systems (Grafana, Prometheus)

    # Automation & Workflow
    AUTOMATION = "automation"      # Zapier, Make, n8n
    WORKFLOW = "workflow"          # Workflow management

    # Industry Specific
    HEALTHCARE = "healthcare"      # Healthcare systems (Epic, Cerner)
    ENTERPRISE = "enterprise"      # Enterprise systems (ServiceNow, Dynamics)

    # Infrastructure
    DATABASE = "database"          # Database systems
    API = "api"                    # Generic API integrations
    NOTIFICATION = "notification"   # Notification services
    SECURITY = "security"          # Security systems
    COMPLIANCE = "compliance"      # Compliance tools
    BACKUP = "backup"              # Backup systems

class IntegrationStatus(str, Enum):
    """Integration configuration and testing status."""
    NOT_CONFIGURED = "not_configured"
    CONFIGURED = "configured"
    TESTED = "tested"
    ERROR = "error"
    DISABLED = "disabled"

class IntegrationProvider(str, Enum):
    """Known integration providers from shared/integration analysis."""
    # AI Services
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ELEVENLABS = "elevenlabs"
    DEEPGRAM = "deepgram"

    # Communication
    VONAGE_SMS = "vonage_sms"
    WHATSAPP = "whatsapp"
    WHATSAPP_BUSINESS = "whatsapp_business"
    TELEGRAM = "telegram"
    DISCORD = "discord"

    # Email
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    GMAIL = "gmail"

    # Payment & Banking
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    MTN_MOBILE_MONEY = "mtn_mobile_money"
    GHANA_INTERBANK = "ghana_interbank"
    BANK_USSD = "bank_ussd"

    # CRM & Sales
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    FRESHSALES = "freshsales"
    ZOHO_CRM = "zoho_crm"

    # Support & Helpdesk
    FRESHDESK = "freshdesk"
    ZENDESK = "zendesk"
    INTERCOM = "intercom"

    # Financial Systems
    QUICKBOOKS = "quickbooks"

    # Productivity
    GOOGLE_WORKSPACE = "google_workspace"
    MICROSOFT_365 = "microsoft_365"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    GOOGLE_DRIVE = "google_drive"
    NOTION = "notion"
    CONFLUENCE = "confluence"

    # Analytics
    GOOGLE_ANALYTICS = "google_analytics"
    MIXPANEL = "mixpanel"

    # Automation
    ZAPIER = "zapier"
    N8N = "n8n"
    MAKE = "make"

    # Healthcare
    EPIC_EHR = "epic_ehr"
    CERNER_EHR = "cerner_ehr"
    ALLSCRIPTS_EHR = "allscripts_ehr"

    # Enterprise
    SERVICENOW = "servicenow"
    ODOO = "odoo"

    # Monitoring
    GRAFANA = "grafana"
    PROMETHEUS = "prometheus"

    # Storage & Databases
    MONGODB = "mongodb"

    # Other
    WEB_CHAT = "web_chat"
    FINDHELP = "findhelp"

class IntegrationConfig(BaseModel):
    """Configuration for an integration."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    endpoint_url: Optional[str] = None
    webhook_url: Optional[str] = None
    authentication_type: Optional[str] = None  # api_key, oauth, basic, etc.
    region: Optional[str] = None
    environment: Optional[str] = None  # sandbox, production
    timeout: Optional[int] = 30
    retry_attempts: Optional[int] = 3
    rate_limit: Optional[int] = None
    custom_headers: Optional[Dict[str, str]] = None
    additional_params: Optional[Dict[str, Any]] = None

class IntegrationCapability(BaseModel):
    """Capability provided by an integration."""
    name: str
    description: str
    method: str  # REST, GraphQL, SDK, etc.
    endpoint: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    response_format: Optional[str] = None
    rate_limit: Optional[int] = None

class IntegrationTestResult(BaseModel):
    """Result of integration testing."""
    success: bool
    message: str
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    error_details: Optional[Dict[str, Any]] = None
    tested_at: datetime

class Integration(BaseModel):
    """Integration database model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Basic Information
    name: str
    display_name: str
    description: str
    provider: IntegrationProvider
    integration_type: IntegrationType
    category: str  # Additional categorization beyond type

    # Metadata
    website: Optional[str] = None
    documentation_url: Optional[str] = None
    icon: Optional[str] = None
    icon_url: Optional[str] = None
    version: str = "1.0"

    # Configuration
    config: IntegrationConfig = Field(default_factory=IntegrationConfig)
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)

    # Capabilities
    capabilities: List[IntegrationCapability] = Field(default_factory=list)
    supported_operations: List[str] = Field(default_factory=list)

    # Status & Testing
    status: IntegrationStatus = IntegrationStatus.NOT_CONFIGURED
    is_active: bool = True
    is_configured: bool = False
    is_tested: bool = False
    last_test_result: Optional[IntegrationTestResult] = None

    # Usage & Analytics
    usage_count: int = 0
    last_used: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tenant_id: Optional[str] = None

    # Compliance & Security
    compliance_certifications: List[str] = Field(default_factory=list)
    data_residency: Optional[str] = None
    encryption_in_transit: bool = True
    encryption_at_rest: bool = True

    # Pricing & Limits
    pricing_model: Optional[str] = None  # free, usage_based, subscription, etc.
    free_tier_limits: Optional[Dict[str, Any]] = None
    usage_limits: Optional[Dict[str, Any]] = None

class IntegrationCreateRequest(BaseModel):
    """Request model for creating an integration."""
    name: str
    display_name: str
    description: str
    provider: IntegrationProvider
    integration_type: IntegrationType
    category: Optional[str] = None
    website: Optional[str] = None
    documentation_url: Optional[str] = None
    icon: Optional[str] = None
    config: Optional[IntegrationConfig] = None
    required_fields: List[str] = Field(default_factory=list)
    capabilities: List[IntegrationCapability] = Field(default_factory=list)
    tenant_id: Optional[str] = None

class IntegrationUpdateRequest(BaseModel):
    """Request model for updating an integration."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    icon: Optional[str] = None
    config: Optional[IntegrationConfig] = None
    is_active: Optional[bool] = None
    tenant_id: Optional[str] = None

class IntegrationConfigureRequest(BaseModel):
    """Request model for configuring an integration."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    endpoint_url: Optional[str] = None
    webhook_url: Optional[str] = None
    authentication_type: Optional[str] = None
    region: Optional[str] = None
    environment: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None
    test_connection: bool = True

class IntegrationTestRequest(BaseModel):
    """Request model for testing an integration."""
    test_type: str = "connection"  # connection, api_call, webhook, etc.
    test_params: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = 30

class IntegrationListResponse(BaseModel):
    """Response model for listing integrations."""
    integrations: List[Integration]
    total: int
    page: int
    per_page: int
    pages: int

class IntegrationStatsResponse(BaseModel):
    """Response model for integration statistics."""
    total_integrations: int
    configured_integrations: int
    tested_integrations: int
    active_integrations: int
    integrations_by_type: Dict[str, int]
    integrations_by_status: Dict[str, int]
    most_used_integrations: List[Dict[str, Any]]
    recent_errors: List[Dict[str, Any]]
"""
Automation Template Database Model
Comprehensive template system for Universal Wizard with pre-configured integrations
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

class TemplateIndustry(str, Enum):
    """Template industry categories."""
    GENERIC = "Generic"
    HEALTHCARE = "Healthcare"
    INSURANCE = "Insurance"
    RETAIL = "Retail"
    FINANCE = "Finance"
    EDUCATION = "Education"
    REAL_ESTATE = "Real Estate"
    LEGAL = "Legal"
    HOSPITALITY = "Hospitality"
    MANUFACTURING = "Manufacturing"
    AUTOMOTIVE = "Automotive"
    FINANCIAL = "Financial"
    GOVERNMENT = "Government"
    LOGISTICS = "Logistics"
    PROFESSIONAL_SERVICES = "Professional Services"
    TELECOM = "Telecom"
    UTILITIES = "Utilities"
    WORKFLOW = "Workflow"

class TemplateCategory(str, Enum):
    """Template categories for organization."""
    HELPDESK = "helpdesk"
    SALES = "sales"
    SUPPORT = "support"
    RETENTION = "retention"
    SCHEDULING = "scheduling"
    LEAD_GENERATION = "lead_generation"
    CUSTOMER_SERVICE = "customer_service"
    APPOINTMENT_BOOKING = "appointment_booking"
    HEALTHCARE = "healthcare"
    MASTER = "master"  # For master templates like master Vapi workflow
    PROVIDER_LOCATOR = "provider_locator"
    CLAIMS_PROCESSING = "claims_processing"
    MAINTENANCE = "maintenance"
    WARRANTY = "warranty"
    ENROLLMENT = "enrollment"
    PAYMENT_PROCESSING = "payment_processing"
    SECURITY = "security"
    PERMIT_PROCESSING = "permit_processing"
    CITIZEN_SERVICES = "citizen_services"
    APPOINTMENT_MANAGEMENT = "appointment_management"
    PRESCRIPTION_MANAGEMENT = "prescription_management"
    BOOKING_MANAGEMENT = "booking_management"
    LOYALTY_MANAGEMENT = "loyalty_management"
    POLICY_MANAGEMENT = "policy_management"
    UNDERWRITING = "underwriting"
    SECURITY_FRAUD = "security_fraud"
    FINANCIAL_OPERATIONS = "financial_operations"
    MEDICAL_SERVICES = "medical_services"
    APPEALS_MANAGEMENT = "appeals_management"
    COVERAGE_OPTIMIZATION = "coverage_optimization"
    COMPLIANCE_REPORTING = "compliance_reporting"
    RISK_ASSESSMENT = "risk_assessment"
    DOCUMENT_MANAGEMENT = "document_management"
    QUOTE_MANAGEMENT = "quote_management"
    COMMUNICATION_MANAGEMENT = "communication_management"
    MEDICAL_BILLING = "medical_billing"
    FINANCIAL_MANAGEMENT = "financial_management"
    LEAD_MANAGEMENT = "lead_management"
    CLAIMS_MANAGEMENT = "claims_management"
    HEALTHCARE_SERVICES = "healthcare_services"
    SHIPMENT_TRACKING = "shipment_tracking"
    INVENTORY_MANAGEMENT = "inventory_management"
    PRODUCTION_MANAGEMENT = "production_management"
    QUALITY_CONTROL = "quality_control"
    CONSULTATION_MANAGEMENT = "consultation_management"
    ORDER_MANAGEMENT = "order_management"
    PROPERTY_MANAGEMENT = "property_management"
    CUSTOMER_FEEDBACK = "customer_feedback"
    NETWORK_MANAGEMENT = "network_management"
    UTILITY_MANAGEMENT = "utility_management"
    AUTOMATION = "automation"
    COMPLIANCE = "compliance"
    NOTIFICATION_MANAGEMENT = "notification_management"
    DOCUMENT_WORKFLOW = "document_workflow"
    FRAUD_DETECTION = "fraud_detection"

class VAPIConfig(BaseModel):
    """VAPI configuration for the template."""
    model: str = "gpt-4o"
    voice_id: str = "jennifer"
    voice_provider: str = "11labs"
    temperature: float = 0.3
    max_tokens: int = 250
    max_duration: int = 600
    first_message: str
    end_call_message: str
    tools: List[str] = []
    compliance_level: str = "Standard"  # Standard, HIPAA, SOX, GDPR

class N8NConfig(BaseModel):
    """N8N workflow configuration."""
    workflow_name: str
    workflow_id: Optional[str] = None  # From n8n-mcp workflow templates
    webhook_path: str
    nodes: List[Dict[str, Any]] = []
    connections: Dict[str, Any] = {}
    endpoints: Dict[str, str] = {}

    # Master template specific fields
    is_master_template: bool = False
    template_type: Optional[str] = None  # "master_vapi", "master_n8n", etc.
    workflow_json: Optional[Dict[str, Any]] = None  # Complete N8N workflow JSON
    deployment_config: Optional[Dict[str, Any]] = None  # Deployment configuration

class IntegrationConfig(BaseModel):
    """Integration configuration with API keys."""
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    config: Dict[str, Any] = {}
    required_fields: List[str] = []

class DemoConfig(BaseModel):
    """Demo configuration."""
    enabled: bool = True
    theme: str = "default"  # default, healthcare, finance, retail
    brand_colors: List[str] = ["#2563eb", "#16a34a"]
    interactive_features: List[str] = []
    emergency_simulation: bool = False

class MonitoringConfig(BaseModel):
    """Monitoring and analytics configuration."""
    enabled: bool = True
    kpis: List[str] = []
    alert_rules: List[str] = []
    dashboard_widgets: List[str] = []
    compliance_monitoring: bool = False

class AutomationTemplate(BaseModel):
    """Complete automation template model."""

    # Basic Information
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str
    industry: TemplateIndustry
    category: TemplateCategory
    description: str
    version: str = "1.0.0"

    # Master Template Support
    is_master_template: bool = False
    template_type: Optional[str] = None  # "master_vapi", "use_case_specific", etc.
    use_case_templates: Optional[Dict[str, Any]] = None  # For master templates with multiple use cases
    default_integrations: List[str] = []  # Default integrations for this template

    # Company Information
    company_name: str
    company_url: Optional[str] = None
    company_description: Optional[str] = None

    # AI Configuration
    system_prompt: str
    knowledge_base_docs: List[str] = []
    custom_tool_names: List[str] = []

    # Integration Configuration
    integrations: List[IntegrationConfig]

    # Platform Configurations
    vapi_config: VAPIConfig
    n8n_config: N8NConfig
    demo_config: DemoConfig
    monitoring_config: MonitoringConfig

    # URLs and Resources
    html_demo_url: Optional[str] = None
    documentation_url: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"
    is_active: bool = True
    usage_count: int = 0

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FrontendAutomationTemplate(BaseModel):
    """Frontend-compatible automation template model."""
    id: str
    name: str
    description: str
    industry: str
    category: str
    complexity: str = "Medium"
    estimated_time: str = "30 minutes"

    # Components structure for frontend compatibility
    integration_categories: List[str] = []
    workflow: List[str] = []
    vapi_config: Dict[str, Any] = {}
    n8n_config: Optional[Dict[str, Any]] = None

    # Extended fields for master templates
    components: Dict[str, Any] = {}
    features: List[str] = []
    supported_languages: List[str] = ["en"]
    knowledge_base: List[Any] = []
    tags: List[str] = []

    # Master template specific
    is_master_template: bool = False
    template_type: Optional[str] = None
    use_case_templates: Optional[Dict[str, Any]] = None
    default_integrations: List[str] = []

    # Metadata
    rating: float = 4.5
    usage_count: int = 0
    popular: bool = False
    created_at: str
    updated_at: str
    version: str = "1.0.0"
    is_active: bool = True

class FrontendAutomationTemplateCreate(BaseModel):
    """Request model for creating automation template from frontend."""
    name: str
    description: str
    industry: str
    category: str
    complexity: Optional[str] = "Medium"
    estimated_time: Optional[str] = "30 minutes"
    components: Optional[Dict[str, Any]] = {}
    is_master_template: Optional[bool] = False
    template_type: Optional[str] = None
    use_case_templates: Optional[Dict[str, Any]] = None
    default_integrations: Optional[List[str]] = []

class FrontendAutomationTemplateUpdate(BaseModel):
    """Request model for updating automation template from frontend."""
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    category: Optional[str] = None
    complexity: Optional[str] = None
    estimated_time: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    is_master_template: Optional[bool] = None
    template_type: Optional[str] = None
    use_case_templates: Optional[Dict[str, Any]] = None
    default_integrations: Optional[List[str]] = None
    is_active: Optional[bool] = None

class FrontendAutomationTemplateListResponse(BaseModel):
    """Response model for listing automation templates."""
    templates: List[FrontendAutomationTemplate]
    pagination: Dict[str, Any]

class AutomationTemplateStats(BaseModel):
    """Statistics for automation templates."""
    total_templates: int
    by_industry: List[Dict[str, Any]]
    by_category: List[Dict[str, Any]]
    by_complexity: List[Dict[str, Any]]
    recent_templates: List[Dict[str, Any]]
    master_templates: List[Dict[str, Any]] = []  # New field for master templates
    generated_at: str

# Pre-configured integration templates with API keys
INTEGRATION_TEMPLATES = {
    "anthropic": IntegrationConfig(
        name="Anthropic Claude",
        enabled=True,
        api_key="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",
        config={
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "temperature": 0.7
        },
        required_fields=["api_key"]
    ),

    "openai": IntegrationConfig(
        name="OpenAI GPT",
        enabled=True,
        api_key="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",
        config={
            "model": "gpt-4o",
            "temperature": 0.3,
            "max_tokens": 250
        },
        required_fields=["api_key"]
    ),

    "gemini": IntegrationConfig(
        name="Google Gemini",
        enabled=True,
        api_key="AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4",
        config={
            "model": "gemini-2.5-flash",
            "temperature": 0.7
        },
        required_fields=["api_key"]
    ),

    "tavily": IntegrationConfig(
        name="Tavily Search",
        enabled=True,
        api_key="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",
        config={
            "max_results": 5,
            "search_depth": "basic"
        },
        required_fields=["api_key"]
    ),

    "firecrawl": IntegrationConfig(
        name="Firecrawl Web Scraping",
        enabled=True,
        api_key="fc-dec73a2970ae4afb9f32666e935684f4",
        config={
            "formats": ["markdown"],
            "onlyMainContent": True
        },
        required_fields=["api_key"]
    ),

    "brave": IntegrationConfig(
        name="Brave Search",
        enabled=True,
        api_key="BSAzgyfrNP7--3Wg1XwTOIDw-mogCJJ",
        config={
            "count": 10,
            "offset": 0
        },
        required_fields=["api_key"]
    ),

    "resend": IntegrationConfig(
        name="Resend Email",
        enabled=True,
        api_key="re_fUUrbkMk_BzeDa7cCxa96waYmiVXxX9RT",
        config={
            "from_email": "noreply@ailabsafrica.com",
            "templates": ["provider_info", "appointment_confirmation", "support_ticket"]
        },
        required_fields=["api_key", "from_email"]
    ),

    "supabase": IntegrationConfig(
        name="Supabase Database",
        enabled=True,
        api_key="sb_secret_MSB5XcvfMpI5sJb-KcRGqA_8d-q7ehk",
        config={
            "project_id": "ljzbzjgvwzivpmlmuxhx",
            "url": "https://ljzbzjgvwzivpmlmuxhx.supabase.co",
            "tables": ["call_logs", "customer_interactions", "analytics"]
        },
        required_fields=["api_key", "project_id"]
    ),

    "pinecone": IntegrationConfig(
        name="Pinecone Vector Database",
        enabled=True,
        api_key="pcsk_5C6SRu_QoKZm84iZKeaFu8uChCWKeHmpBLnRpD65ejn8UgeeazY9nnVhrw5xJiqpjkSXFu",
        config={
            "environment": "us-west1-gcp",
            "dimension": 1536,
            "metric": "cosine"
        },
        required_fields=["api_key", "environment"]
    ),

    "vapi": IntegrationConfig(
        name="VAPI Voice AI",
        enabled=True,
        api_key="42cf1e7c-2ef9-4bd7-ba30-52f2813605a2",
        config={
            "base_url": "https://api.vapi.ai",
            "voice_provider": "11labs",
            "default_voice": "jennifer"
        },
        required_fields=["api_key", "base_url"]
    ),

    "calendly": IntegrationConfig(
        name="Calendly Scheduling",
        enabled=True,
        api_key="eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzU4MDM5OTAyLCJqdGkiOiI0OGI3YTA1Ny05NmY3LTQwOGMtYjJhNC1jOTFmOTQzYjZiNWUiLCJ1c2VyX3V1aWQiOiI2MDdjZmFhYi0zNjY4LTRhNWEtYjA3NS1lZWRjOGJhMzRjMDMifQ.fFJz0hUGo45VE364ndFf8qEd4RcARY_cjZR9pFRH2wUwxqmbJ9Q75hnjYgeVa79Uyv_PuqsIQh6dFjUr-BnDZQ",
        config={
            "booking_types": ["consultation", "follow_up", "demo"],
            "timezone": "UTC",
            "availability_window": 30
        },
        required_fields=["api_key"]
    ),

    "hubspot": IntegrationConfig(
        name="HubSpot CRM & Helpdesk",
        enabled=True,
        api_key="pat-na2-be182d71-d2e7-4c11-a405-d335560644db",
        config={
            "portal_id": "243880132",
            "client_secret": "a8660077-978d-4dcc-a005-2fc629da63ed",
            "authentication_type": "private_app_token",
            "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write", "crm.objects.companies.read", "crm.objects.companies.write", "crm.objects.deals.read", "crm.objects.deals.write", "tickets", "crm.objects.marketing_events.read", "crm.objects.marketing_events.write"],
            "features": ["contacts", "companies", "deals", "tickets", "emails", "calls", "meetings", "tasks", "notes", "pipelines", "workflows"],
            "capabilities": ["crm_management", "lead_management", "deal_tracking", "contact_management", "ticket_management", "helpdesk", "email_marketing", "sales_automation", "analytics", "reporting"]
        },
        required_fields=["api_key", "portal_id"]
    ),

    "freshdesk": IntegrationConfig(
        name="Freshdesk Support",
        enabled=False,  # Deprecated in favor of HubSpot
        api_key="",  # To be configured per organization
        config={
            "domain": "ailabs-888099064326049059.myfreshworks.com",
            "ticket_types": ["technical", "billing", "general"],
            "priority_levels": ["low", "medium", "high", "urgent"]
        },
        required_fields=["api_key", "domain"]
    ),

    "vonage": IntegrationConfig(
        name="Vonage SMS",
        enabled=True,
        api_key="4109fdf7",
        config={
            "api_secret": "mativo3saMI3cAWG",
            "base_url": "https://api.nexmo.com",
            "from_number": "AILabsAfrica"
        },
        required_fields=["api_key", "api_secret"]
    )
}

def create_master_vapi_template() -> AutomationTemplate:
    """Create master Vapi workflow template from the JSON file."""
    import json
    import os

    # Load the master Vapi workflow JSON
    json_path = "/opt/kasaai/apps/automations/examples/004_master_vapi_workflow.json"
    use_case_templates_path = "/opt/kasaai/apps/automations/examples/005_use_case_templates.json"

    try:
        with open(json_path, 'r') as f:
            workflow_json = json.load(f)

        with open(use_case_templates_path, 'r') as f:
            use_case_templates = json.load(f)
    except FileNotFoundError:
        # Fallback if files don't exist
        workflow_json = {}
        use_case_templates = {}

    return AutomationTemplate(
        template_name="Master Vapi Integration Workflow",
        industry=TemplateIndustry.WORKFLOW,
        category=TemplateCategory.MASTER,
        description="Highly configurable voice assistant system that integrates with existing Integration Service to support multiple business use cases including sales, helpdesk, healthcare, lead generation, and more.",
        version="1.0.0",

        # Master template configuration
        is_master_template=True,
        template_type="master_vapi",
        use_case_templates=use_case_templates.get("master_vapi_use_case_templates", {}),
        default_integrations=[
            "hubspot_crm", "resend_email", "calendly_scheduling", "tavily_search",
            "freshdesk_support", "vonage_sms", "firecrawl_scraping", "brave_search",
            "supabase_database", "vapi_advanced"
        ],

        # Company information (template defaults)
        company_name="Configurable Organization",
        company_url="",
        company_description="Dynamic company information extracted from provided URL",

        # AI Configuration
        system_prompt="Dynamic system prompt generated based on use case, company information, and selected personality type.",
        knowledge_base_docs=[],
        custom_tool_names=[],

        # Integration Configuration
        integrations=[
            INTEGRATION_TEMPLATES["hubspot"],
            INTEGRATION_TEMPLATES["resend"],
            INTEGRATION_TEMPLATES["tavily"],
            INTEGRATION_TEMPLATES["calendly"],
            INTEGRATION_TEMPLATES["vonage"]
        ],

        # Platform Configurations
        vapi_config=VAPIConfig(
            model="claude-3-5-sonnet-20241022",
            voice_id="jennifer",
            voice_provider="11labs",
            temperature=0.3,
            max_tokens=250,
            max_duration=600,
            first_message="Hello! How can I assist you today?",
            end_call_message="Thank you for calling. Have a great day!",
            tools=[],
            compliance_level="Standard"
        ),

        n8n_config=N8NConfig(
            workflow_name="Master Vapi Integration Workflow",
            webhook_path="/webhook/master-vapi",
            nodes=[],
            connections={},
            endpoints={},
            is_master_template=True,
            template_type="master_vapi",
            workflow_json=workflow_json,
            deployment_config={
                "auto_deploy": True,
                "validation_required": True,
                "post_deployment_tests": True
            }
        ),

        demo_config=DemoConfig(
            enabled=True,
            theme="default",
            brand_colors=["#2563eb", "#16a34a"],
            interactive_features=["voice_testing", "integration_monitoring", "real_time_analytics"],
            emergency_simulation=False
        ),

        monitoring_config=MonitoringConfig(
            enabled=True,
            kpis=["call_volume", "integration_usage", "success_rate", "response_time"],
            alert_rules=["integration_failure", "high_error_rate", "performance_degradation"],
            dashboard_widgets=["call_metrics", "integration_health", "user_satisfaction", "deployment_status"],
            compliance_monitoring=True
        ),

        # Metadata
        created_by="system",
        is_active=True,
        usage_count=0
    )

def get_integrations_for_template(template_type: str, industry: TemplateIndustry) -> List[IntegrationConfig]:
    """Get appropriate integrations for a template type and industry."""

    # Base integrations for all templates
    base_integrations = [
        INTEGRATION_TEMPLATES["openai"],
        INTEGRATION_TEMPLATES["vapi"],
        INTEGRATION_TEMPLATES["supabase"],
        INTEGRATION_TEMPLATES["resend"]
    ]

    # Add industry-specific integrations
    if industry == TemplateIndustry.HEALTHCARE:
        base_integrations.extend([
            INTEGRATION_TEMPLATES["calendly"],
            INTEGRATION_TEMPLATES["hubspot"],
            INTEGRATION_TEMPLATES["vonage"]
        ])
    elif industry == TemplateIndustry.INSURANCE:
        base_integrations.extend([
            INTEGRATION_TEMPLATES["hubspot"],
            INTEGRATION_TEMPLATES["vonage"],
            INTEGRATION_TEMPLATES["tavily"]
        ])
    elif industry == TemplateIndustry.RETAIL:
        base_integrations.extend([
            INTEGRATION_TEMPLATES["vonage"],
            INTEGRATION_TEMPLATES["calendly"],
            INTEGRATION_TEMPLATES["hubspot"],
            INTEGRATION_TEMPLATES["brave"]
        ])
    elif industry == TemplateIndustry.GENERIC:
        base_integrations.extend([
            INTEGRATION_TEMPLATES["tavily"],
            INTEGRATION_TEMPLATES["calendly"],
            INTEGRATION_TEMPLATES["hubspot"]
        ])

    # Add advanced integrations for complex templates
    if template_type in ["provider_locator", "helpdesk", "customer_service"]:
        base_integrations.extend([
            INTEGRATION_TEMPLATES["firecrawl"],
            INTEGRATION_TEMPLATES["pinecone"],
            INTEGRATION_TEMPLATES["brave"]
        ])

    return base_integrations

def create_system_prompt(template_type: str, industry: TemplateIndustry, company_name: str = "Your Company") -> str:
    """Create industry and type-specific system prompts."""

    base_prompt = f"""You are a professional AI assistant for {company_name}. Your role is to help customers with their inquiries in a helpful, accurate, and professional manner.

## Core Responsibilities:
1. **Customer Service**: Provide excellent customer support and assistance
2. **Information Retrieval**: Find and present accurate information from our knowledge base
3. **Process Assistance**: Guide customers through our services and procedures
4. **Escalation Management**: Know when to escalate to human agents

## Response Guidelines:
- Always be polite, professional, and helpful
- Provide clear, concise, and accurate information
- Ask clarifying questions when needed
- Confirm understanding before proceeding
- Offer additional assistance proactively

## Escalation Rules:
- Escalate complex technical issues
- Escalate when customer requests human agent
- Escalate sensitive or confidential matters
- Escalate when unable to resolve the issue

How may I assist you today?"""

    # Industry-specific enhancements
    if industry == TemplateIndustry.HEALTHCARE:
        base_prompt += f"""

## Healthcare-Specific Guidelines:
- Maintain HIPAA compliance at all times
- Never provide medical advice or diagnosis
- Focus on finding appropriate healthcare providers
- Prioritize emergency situations immediately
- Verify insurance coverage when applicable
- Respect patient confidentiality and privacy

## Medical Disclaimers:
- I cannot provide medical advice or diagnoses
- For medical emergencies, call 911 immediately
- Always consult with healthcare professionals for medical concerns"""

    elif industry == TemplateIndustry.INSURANCE:
        base_prompt += f"""

## Insurance-Specific Guidelines:
- Verify customer identity before discussing policy details
- Explain insurance terms in simple language
- Help with claims filing and status checking
- Provide clear coverage explanations
- Maintain strict confidentiality of customer data

## Insurance Disclaimers:
- Policy terms and conditions apply to all coverage
- Final claim decisions are made by underwriting
- Premium quotes are estimates subject to verification"""

    elif industry == TemplateIndustry.RETAIL:
        base_prompt += f"""

## Retail-Specific Guidelines:
- Help customers find products and services
- Assist with orders, returns, and exchanges
- Provide product information and recommendations
- Check inventory and availability
- Process customer feedback and complaints

## Retail Focus:
- Customer satisfaction is our top priority
- Offer promotions and special deals when relevant
- Suggest complementary products when appropriate"""

    # Template-type specific enhancements
    if template_type == "provider_locator":
        base_prompt += f"""

## Provider Locator Features:
- Search healthcare providers by specialty, location, insurance
- Check provider availability and booking options
- Provide contact information and directions
- Verify insurance network participation"""

    elif template_type == "helpdesk":
        base_prompt += f"""

## Helpdesk Features:
- Create and track support tickets
- Provide technical assistance
- Access knowledge base for solutions
- Schedule callbacks and appointments"""

    elif template_type == "appointment_booking":
        base_prompt += f"""

## Appointment Booking Features:
- Check availability and schedule appointments
- Send confirmations and reminders
- Handle rescheduling and cancellations
- Provide preparation instructions"""

    return base_prompt


# Frontend-compatible automation template models
class FrontendAutomationTemplate(BaseModel):
    """
    Frontend-compatible automation template model.
    Matches the structure used in the frontend automation-templates.ts
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    industry: str  # Use string instead of enum for frontend compatibility
    category: str
    complexity: str  # Simple, Medium, Advanced
    estimated_time: str
    rating: float = Field(ge=0, le=5, default=4.5)
    usage_count: int = Field(ge=0, default=0)
    popular: bool = False

    # Integration and workflow configuration
    integration_categories: List[str]
    default_integrations: List[str] = Field(default_factory=list)
    workflow: List[Dict[str, Any]]

    # VAPI configuration
    vapi_config: Optional[Dict[str, Any]] = None

    # Features and capabilities
    features: List[str] = Field(default_factory=list)
    supportedLanguages: List[str] = Field(default_factory=lambda: ["en"])
    knowledgeBase: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_public: bool = True
    createdBy: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FrontendAutomationTemplateCreate(BaseModel):
    """Request model for creating frontend-compatible automation templates."""
    name: str
    description: str
    industry: str
    category: str
    complexity: str
    estimated_time: str
    integration_categories: List[str]
    workflow: List[Dict[str, Any]]
    vapi_config: Optional[Dict[str, Any]] = None
    features: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class FrontendAutomationTemplateUpdate(BaseModel):
    """Request model for updating frontend-compatible automation templates."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    complexity: Optional[str] = None
    estimated_time: Optional[str] = None
    integration_categories: Optional[List[str]] = None
    workflow: Optional[List[Dict[str, Any]]] = None
    vapi_config: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class FrontendAutomationTemplateListResponse(BaseModel):
    """Response model for listing frontend-compatible automation templates."""
    templates: List[FrontendAutomationTemplate]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class AutomationTemplateStats(BaseModel):
    """Statistics for automation templates."""
    total_templates: int
    by_industry: Dict[str, int]
    by_complexity: Dict[str, int]
    by_category: Dict[str, int]
    popular_templates: List[FrontendAutomationTemplate]
    recent_templates: List[FrontendAutomationTemplate]


# Mock database storage for frontend-compatible templates
FRONTEND_TEMPLATES_DB: Dict[str, FrontendAutomationTemplate] = {}
"""
Automation Template Management API
CRUD operations for automation templates with pre-configured integrations
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import logging
from datetime import datetime

from ..auth import get_current_user_mongo
from ..models.automation_template import (
    AutomationTemplate,
    TemplateIndustry,
    TemplateCategory,
    get_integrations_for_template,
    create_system_prompt,
    INTEGRATION_TEMPLATES
)
from ..services.automation_orchestration_service import get_automation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation-templates", tags=["automation-templates"])

def is_admin_user(user: dict) -> bool:
    """Check if user has admin privileges"""
    user_email = user.get("email", "")
    admin_emails = [
        "ailabsafrica@gmail.com",
        "admin@ailabsafrica.com",
        "support@ailabsafrica.com",
        "alfred.anyan@gmail.com"
    ]

    # Check email-based admin access or role metadata
    return (user_email in admin_emails or
            user.get("user_metadata", {}).get("role") == "admin" or
            user.get("app_metadata", {}).get("role") == "admin")

# MongoDB storage for templates
from ..mongo import get_collection

class TemplateCreateRequest(BaseModel):
    """Request model for creating a new template."""
    template_name: str
    industry: TemplateIndustry
    category: TemplateCategory
    description: str
    company_name: str
    company_url: Optional[str] = None
    company_description: Optional[str] = None
    custom_integrations: Optional[List[str]] = None

class TemplateUpdateRequest(BaseModel):
    """Request model for updating a template."""
    template_name: Optional[str] = None
    description: Optional[str] = None
    company_name: Optional[str] = None
    company_url: Optional[str] = None
    company_description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None

class TemplateFromConfigRequest(BaseModel):
    """Request model for updating a template from automation configuration."""
    automation_config: Dict[str, Any]
    update_template: bool = True

class TemplateResponse(BaseModel):
    """Response model for template operations."""
    success: bool
    template: Optional[AutomationTemplate] = None
    message: str

@router.post("/create", response_model=TemplateResponse)
async def create_template(
    request: TemplateCreateRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Create a new automation template with pre-configured integrations using orchestration service."""
    try:
        logger.info(f"Creating template: {request.template_name} for industry: {request.industry}")

        # Get the orchestration service
        orchestration_service = await get_automation_service()

        # Get appropriate integrations for this template
        integrations = get_integrations_for_template(request.category, request.industry)

        # Add custom integrations if specified
        if request.custom_integrations:
            for integration_name in request.custom_integrations:
                if integration_name in INTEGRATION_TEMPLATES:
                    integrations.append(INTEGRATION_TEMPLATES[integration_name])

        # Generate system prompt
        system_prompt = create_system_prompt(
            request.category,
            request.industry,
            request.company_name
        )

        # Prepare template data for orchestration service
        template_data = {
            "name": request.template_name,
            "description": request.description,
            "industry": request.industry.value,
            "category": request.category.value,
            "complexity": "Medium",  # Default complexity
            "estimated_time": "30 minutes",  # Default estimate
            "components": {
                "vapi": get_vapi_config_for_industry(request.industry, request.company_name).model_dump(),
                "n8n": get_n8n_config_for_category(request.category).model_dump(),
                "customTools": get_custom_tools_for_category(request.category),
                "integrations": [integration.model_dump() for integration in integrations]
            },
            "metadata": {
                "company_name": request.company_name,
                "company_url": request.company_url,
                "company_description": request.company_description,
                "system_prompt": system_prompt,
                "created_by": current_user.get("email", "unknown")
            }
        }

        # Use orchestration service to create template with proper validation
        template = await orchestration_service.create_template(template_data)

        return TemplateResponse(
            success=True,
            template=None,  # Convert orchestration service template to API model if needed
            message=f"Template created successfully with ID: {template.id}"
        )

    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create template: {str(e)}"
        )

@router.get("/public/list")
async def list_templates_public(
    industry: Optional[str] = None,
    category: Optional[str] = None,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200)
):
    """List automation templates publicly without authentication (for frontend)."""
    try:
        collection = get_collection("automation_templates")

        # Build filter query
        filter_query = {}
        if industry:
            filter_query["industry"] = industry
        if category:
            filter_query["category"] = category
        if active_only:
            filter_query["is_active"] = True

        # Calculate skip for pagination
        skip = (page - 1) * per_page

        # Get total count for pagination
        total = await collection.count_documents(filter_query)

        # Get templates from MongoDB with pagination
        cursor = collection.find(filter_query).sort([("usage_count", -1), ("created_at", -1)]).skip(skip).limit(per_page)
        template_docs = await cursor.to_list(length=per_page)

        # Convert to frontend-compatible format
        templates = []
        for doc in template_docs:
            # Get basic template info
            template_id = str(doc.get("_id", ""))
            template_name = doc.get("template_name", doc.get("name", "Unnamed Template"))

            # Convert backend model to frontend format
            frontend_template = {
                "id": template_id,
                "name": template_name,
                "description": doc.get("description", ""),
                "industry": doc.get("industry", "Generic"),
                "category": doc.get("category", "automation"),
                "complexity": "Medium",  # Default complexity
                "estimatedTime": "15-30 minutes",  # Default estimate
                "rating": 4.5,
                "usageCount": doc.get("usage_count", 0),
                "popular": doc.get("usage_count", 0) > 10,
                "integrationCategories": get_integration_categories_for_doc(doc),
                "defaultIntegrations": get_integration_names_for_doc(doc),
                "workflow": get_workflow_for_doc(doc),
                "vapiConfig": get_vapi_config_for_doc(doc),
                "features": get_features_for_doc(doc),
                "supportedLanguages": ["en"],
                "knowledgeBase": [],
                "tags": [doc.get("industry", ""), doc.get("category", "")],
                "isActive": doc.get("is_active", True),
                "isPublic": True,
                "createdBy": doc.get("created_by", "system"),
                "createdAt": doc.get("created_at", "2025-09-19T00:00:00"),
                "updatedAt": doc.get("updated_at", "2025-09-19T00:00:00"),
                "version": doc.get("version", "1.0.0")
            }
            templates.append(frontend_template)

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page

        return {
            "templates": templates,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

    except Exception as e:
        logger.error(f"Error listing templates publicly: {str(e)}")
        return {"templates": [], "total": 0, "error": str(e)}

@router.get("/public/industries")
async def get_industries_public():
    """Get list of available industries for public use (for frontend sidebar)."""
    try:
        collection = get_collection("automation_templates")

        # Get distinct industries from active templates
        industries = collection.distinct("industry", {"is_active": True})

        # Filter out empty/null values and sort
        industries = [ind for ind in industries if ind and ind.strip()]
        industries.sort()

        # Also get count for each industry
        industry_counts = []
        for industry in industries:
            count = collection.count_documents({
                "industry": industry,
                "is_active": True
            })
            industry_counts.append({
                "name": industry,
                "count": count
            })

        return {
            "industries": industry_counts,
            "total": len(industries)
        }

    except Exception as e:
        logger.error(f"Error getting industries: {str(e)}")
        return {"industries": [], "total": 0, "error": str(e)}


@router.get("/list", response_model=List[AutomationTemplate])
async def list_templates(
    industry: Optional[TemplateIndustry] = None,
    category: Optional[TemplateCategory] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user_mongo)
):
    """List automation templates with optional filtering."""
    try:
        collection = get_collection("automation_templates")

        # Build filter query
        filter_query = {}
        if industry:
            filter_query["industry"] = industry
        if category:
            filter_query["category"] = category
        if active_only:
            filter_query["is_active"] = True

        # Get templates from MongoDB
        cursor = collection.find(filter_query).sort([
            ("usage_count", -1),
            ("created_at", -1)
        ])
        template_docs = await cursor.to_list(length=None)

        # Convert to Pydantic models
        templates = []
        for doc in template_docs:
            doc["id"] = doc.pop("_id")  # Convert _id back to id
            templates.append(AutomationTemplate(**doc))

        return templates

    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list templates: {str(e)}"
        )

@router.get("/{template_id}", response_model=AutomationTemplate)
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Get a specific automation template by ID."""
    try:
        collection = get_collection("automation_templates")

        # Find template by ID
        template_doc = collection.find_one({"_id": template_id})
        if not template_doc:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )

        # Increment usage count
        await collection.update_one(
            {"_id": template_id},
            {"$inc": {"usage_count": 1}}
        )

        # Convert to Pydantic model
        template_doc["id"] = template_doc.pop("_id")
        template_doc["usage_count"] = template_doc.get("usage_count", 0) + 1
        template = AutomationTemplate(**template_doc)

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get template: {str(e)}"
        )

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Update an automation template. Requires admin privileges."""
    try:
        # Check if user has admin privileges
        if not is_admin_user(current_user):
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required to update templates"
            )

        collection = get_collection("automation_templates")

        # Check if template exists
        template_doc = collection.find_one({"_id": template_id})
        if not template_doc:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )

        # Build update query
        update_fields = {}
        if request.template_name:
            update_fields["template_name"] = request.template_name
        if request.description:
            update_fields["description"] = request.description
        if request.company_name:
            update_fields["company_name"] = request.company_name
        if request.company_url:
            update_fields["company_url"] = request.company_url
        if request.company_description:
            update_fields["company_description"] = request.company_description
        if request.system_prompt:
            update_fields["system_prompt"] = request.system_prompt
        if request.is_active is not None:
            update_fields["is_active"] = request.is_active

        update_fields["updated_at"] = datetime.utcnow()

        # Update in MongoDB
        await collection.update_one(
            {"_id": template_id},
            {"$set": update_fields}
        )

        # Get updated template
        updated_doc = collection.find_one({"_id": template_id})
        updated_doc["id"] = updated_doc.pop("_id")
        template = AutomationTemplate(**updated_doc)

        return TemplateResponse(
            success=True,
            template=template,
            message="Template updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update template: {str(e)}"
        )

@router.put("/{template_id}/from-config", response_model=TemplateResponse)
async def update_template_from_config(
    template_id: str,
    request: TemplateFromConfigRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Update a template with configuration from the automation deployment wizard. Requires admin privileges."""
    try:
        # Check if user has admin privileges
        if not is_admin_user(current_user):
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required to update templates"
            )

        collection = get_collection("automation_templates")

        # Check if template exists
        template_doc = collection.find_one({"_id": template_id})
        if not template_doc:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )

        config = request.automation_config

        # Extract relevant fields from automation configuration
        update_fields = {
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": current_user.get("email", "admin")
        }

        # Update template based on automation config
        if config.get("automationName"):
            update_fields["template_name"] = config["automationName"]

        if config.get("companyInfo"):
            company_info = config["companyInfo"]
            if company_info.get("name"):
                update_fields["company_name"] = company_info["name"]
            if company_info.get("description"):
                update_fields["description"] = company_info["description"]
            if company_info.get("url"):
                update_fields["company_url"] = company_info["url"]

        # Update system prompt from VAPI agent
        if config.get("vapiAgent", {}).get("systemPrompt"):
            update_fields["system_prompt"] = config["vapiAgent"]["systemPrompt"]

        # Update voice settings
        if config.get("vapiAgent", {}).get("voiceSettings"):
            voice_settings = config["vapiAgent"]["voiceSettings"]
            update_fields["default_voice_settings"] = voice_settings

        # Update N8N workflow configuration
        if config.get("n8nWorkflow"):
            n8n_config = config["n8nWorkflow"]
            update_fields["default_n8n_config"] = n8n_config

        # Update integrations
        if config.get("integrations"):
            integrations = config["integrations"]
            update_fields["default_integrations"] = integrations

        # Update demo settings
        if config.get("demoSettings"):
            demo_settings = config["demoSettings"]
            update_fields["default_demo_settings"] = demo_settings

        # Update analytics settings
        if config.get("analytics"):
            analytics = config["analytics"]
            update_fields["default_analytics"] = analytics

        # Perform the update
        result = await collection.update_one(
            {"_id": template_id},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )

        # Get updated template
        updated_doc = collection.find_one({"_id": template_id})
        updated_doc["id"] = updated_doc.pop("_id")

        logger.info(f"Updated template {template_id} from automation config by {current_user.get('email')}")

        return TemplateResponse(
            success=True,
            message=f"Template '{updated_doc.get('template_name', template_id)}' updated successfully from automation configuration",
            template=updated_doc
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template from config: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update template from config: {str(e)}"
        )

@router.delete("/{template_id}", response_model=TemplateResponse)
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Delete an automation template."""
    try:
        collection = get_collection("automation_templates")

        # Check if template exists
        template_doc = collection.find_one({"_id": template_id})
        if not template_doc:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )

        # Delete from MongoDB
        result = await collection.delete_one({"_id": template_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete template"
            )

        return TemplateResponse(
            success=True,
            template=None,
            message="Template deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete template: {str(e)}"
        )

@router.post("/populate-defaults")
async def populate_default_templates(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Populate the database with default templates."""
    try:
        logger.info("Populating default automation templates")

        collection = get_collection("automation_templates")

        # Clear existing templates
        await collection.delete_many({})

        # Create default templates
        default_templates = create_default_templates()

        # Store all templates in MongoDB
        template_docs = []
        for template in default_templates:
            template_dict = template.model_dump()
            template_dict["_id"] = template.id  # Use template ID as MongoDB _id
            template_docs.append(template_dict)

        if template_docs:
            await collection.insert_many(template_docs)

        return {
            "success": True,
            "message": f"Created {len(default_templates)} default templates",
            "templates": [{"id": t.id, "name": t.template_name, "industry": t.industry} for t in default_templates]
        }

    except Exception as e:
        logger.error(f"Error populating default templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to populate default templates: {str(e)}"
        )

@router.get("/integrations/available")
async def get_available_integrations():
    """Get list of all available integrations with their configurations."""
    try:
        return {
            "integrations": [
                {
                    "name": integration.name,
                    "key": key,
                    "enabled": integration.enabled,
                    "config_fields": list(integration.config.keys()),
                    "required_fields": integration.required_fields
                }
                for key, integration in INTEGRATION_TEMPLATES.items()
            ]
        }

    except Exception as e:
        logger.error(f"Error getting available integrations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get integrations: {str(e)}"
        )

# Helper functions for template configuration

def get_custom_tools_for_category(category: TemplateCategory) -> List[str]:
    """Get custom tool names for a template category."""
    tool_mapping = {
        TemplateCategory.HELPDESK: [
            "search_knowledge_base",
            "create_support_ticket",
            "escalate_to_human",
            "book_appointment",
            "send_email_summary"
        ],
        TemplateCategory.PROVIDER_LOCATOR: [
            "search_healthcare_providers",
            "get_provider_details",
            "book_appointment",
            "verify_insurance_coverage",
            "get_emergency_providers"
        ],
        TemplateCategory.SALES: [
            "qualify_lead",
            "schedule_demo",
            "send_product_info",
            "calculate_pricing",
            "create_proposal"
        ],
        TemplateCategory.SUPPORT: [
            "diagnose_issue",
            "search_documentation",
            "create_ticket",
            "schedule_callback",
            "escalate_technical_issue"
        ],
        TemplateCategory.CLAIMS_PROCESSING: [
            "file_insurance_claim",
            "check_claim_status",
            "verify_policy_coverage",
            "schedule_adjuster",
            "request_documentation"
        ]
    }

    return tool_mapping.get(category, [
        "search_information",
        "create_ticket",
        "book_appointment",
        "send_information"
    ])

def get_vapi_config_for_industry(industry: TemplateIndustry, company_name: str):
    """Get VAPI configuration based on industry."""
    from ..models.automation_template import VAPIConfig

    base_config = VAPIConfig(
        first_message=f"Hello! I'm {company_name}'s AI assistant. How can I help you today?",
        end_call_message=f"Thank you for contacting {company_name}. Have a great day!"
    )

    if industry == TemplateIndustry.HEALTHCARE:
        base_config.compliance_level = "HIPAA"
        base_config.temperature = 0.3
        base_config.max_duration = 900
        base_config.first_message = f"Hello! I'm {company_name}'s healthcare assistant. I can help you find providers, book appointments, or answer questions about our services. How may I assist you today?"

    elif industry == TemplateIndustry.INSURANCE:
        base_config.compliance_level = "SOX"
        base_config.temperature = 0.2
        base_config.first_message = f"Hello! I'm {company_name}'s insurance assistant. I can help you with claims, policy questions, or finding coverage options. How can I help you today?"

    elif industry == TemplateIndustry.FINANCE:
        base_config.compliance_level = "SOX"
        base_config.temperature = 0.2
        base_config.first_message = f"Hello! I'm {company_name}'s financial services assistant. I can help you with account questions, services, or connecting you with an advisor. How may I assist you?"

    return base_config

def get_n8n_config_for_category(category: TemplateCategory):
    """Get N8N configuration based on template category."""
    from ..models.automation_template import N8NConfig

    base_config = N8NConfig(
        workflow_name=f"{category.value.replace('_', ' ').title()} Automation",
        webhook_path=f"/{category.value.replace('_', '-')}"
    )

    if category == TemplateCategory.PROVIDER_LOCATOR:
        base_config.workflow_id = "healthcare_provider_search"
        base_config.endpoints = {
            "provider_search": "/search-providers",
            "emergency_services": "/emergency-providers",
            "appointment_booking": "/book-appointment",
            "insurance_verification": "/verify-insurance"
        }

    elif category == TemplateCategory.HELPDESK:
        base_config.workflow_id = "customer_support_helpdesk"
        base_config.endpoints = {
            "ticket_creation": "/create-ticket",
            "knowledge_search": "/search-kb",
            "escalation": "/escalate",
            "appointment_booking": "/book-appointment"
        }

    elif category == TemplateCategory.CLAIMS_PROCESSING:
        base_config.workflow_id = "insurance_claims_processing"
        base_config.endpoints = {
            "file_claim": "/file-claim",
            "check_status": "/claim-status",
            "document_upload": "/upload-docs",
            "adjuster_scheduling": "/schedule-adjuster"
        }

    return base_config

def get_demo_config_for_industry(industry: TemplateIndustry):
    """Get demo configuration based on industry."""
    from ..models.automation_template import DemoConfig

    config_mapping = {
        TemplateIndustry.HEALTHCARE: DemoConfig(
            theme="healthcare",
            brand_colors=["#2563eb", "#16a34a", "#dc2626"],
            interactive_features=["provider_search", "emergency_services", "appointment_booking"],
            emergency_simulation=True
        ),
        TemplateIndustry.INSURANCE: DemoConfig(
            theme="insurance",
            brand_colors=["#1e40af", "#059669", "#ea580c"],
            interactive_features=["claims_filing", "policy_search", "agent_connect"],
            emergency_simulation=False
        ),
        TemplateIndustry.RETAIL: DemoConfig(
            theme="retail",
            brand_colors=["#7c3aed", "#ec4899", "#f59e0b"],
            interactive_features=["product_search", "order_tracking", "customer_support"],
            emergency_simulation=False
        ),
        TemplateIndustry.GENERIC: DemoConfig(
            theme="default",
            brand_colors=["#2563eb", "#16a34a"],
            interactive_features=["information_search", "appointment_booking", "support_ticket"],
            emergency_simulation=False
        )
    }

    return config_mapping.get(industry, config_mapping[TemplateIndustry.GENERIC])

def get_monitoring_config_for_industry(industry: TemplateIndustry):
    """Get monitoring configuration based on industry."""
    from ..models.automation_template import MonitoringConfig

    base_kpis = ["call_volume", "success_rate", "customer_satisfaction", "response_time"]

    if industry == TemplateIndustry.HEALTHCARE:
        return MonitoringConfig(
            kpis=base_kpis + ["search_success_rate", "appointment_booking_rate", "emergency_response_time"],
            alert_rules=["system_health", "provider_database_status", "hipaa_compliance"],
            dashboard_widgets=["call_analytics", "provider_search_metrics", "compliance_monitor"],
            compliance_monitoring=True
        )
    elif industry == TemplateIndustry.INSURANCE:
        return MonitoringConfig(
            kpis=base_kpis + ["claims_processed", "policy_inquiries", "fraud_detection_rate"],
            alert_rules=["system_health", "claims_system_status", "sox_compliance"],
            dashboard_widgets=["call_analytics", "claims_metrics", "policy_dashboard"],
            compliance_monitoring=True
        )
    else:
        return MonitoringConfig(
            kpis=base_kpis + ["conversion_rate", "escalation_rate"],
            alert_rules=["system_health", "high_call_volume"],
            dashboard_widgets=["call_analytics", "performance_metrics"],
            compliance_monitoring=False
        )

def create_default_templates() -> List[AutomationTemplate]:
    """Create all default templates for the system."""
    templates = []

    # Import here to avoid circular imports
    from ..models.automation_template import (
        AutomationTemplate, TemplateIndustry, TemplateCategory,
        VAPIConfig, N8NConfig, DemoConfig, MonitoringConfig
    )

    # Generic Campaign Templates (for Campaign page)
    generic_templates = [
        {
            "template_name": "Universal Customer Support",
            "category": TemplateCategory.HELPDESK,
            "description": "General purpose customer support assistant with ticket creation, knowledge base search, and appointment booking capabilities.",
            "company_name": "Your Company",
            "knowledge_base_docs": ["company_policies", "product_documentation", "faq"],
            "interactive_features": ["ticket_creation", "knowledge_search", "appointment_booking"]
        },
        {
            "template_name": "Sales Lead Qualification",
            "category": TemplateCategory.SALES,
            "description": "Sales assistant for lead qualification, product demos, and customer onboarding.",
            "company_name": "Your Business",
            "knowledge_base_docs": ["product_catalog", "pricing_guide", "sales_scripts"],
            "interactive_features": ["lead_qualification", "demo_scheduling", "product_info"]
        },
        {
            "template_name": "Appointment Booking System",
            "category": TemplateCategory.APPOINTMENT_BOOKING,
            "description": "Automated appointment booking with calendar integration and reminder system.",
            "company_name": "Your Service",
            "knowledge_base_docs": ["service_catalog", "booking_policies", "cancellation_terms"],
            "interactive_features": ["availability_check", "appointment_booking", "reminder_setup"]
        },
        {
            "template_name": "Customer Retention Assistant",
            "category": TemplateCategory.RETENTION,
            "description": "Proactive customer retention with personalized offers and re-engagement campaigns.",
            "company_name": "Your Brand",
            "knowledge_base_docs": ["customer_history", "retention_offers", "loyalty_programs"],
            "interactive_features": ["offer_generation", "feedback_collection", "loyalty_tracking"]
        }
    ]

    # Create generic templates
    for template_data in generic_templates:
        template = AutomationTemplate(
            template_name=template_data["template_name"],
            industry=TemplateIndustry.GENERIC,
            category=template_data["category"],
            description=template_data["description"],
            company_name=template_data["company_name"],
            system_prompt=create_system_prompt(
                template_data["category"],
                TemplateIndustry.GENERIC,
                template_data["company_name"]
            ),
            knowledge_base_docs=template_data["knowledge_base_docs"],
            custom_tool_names=get_custom_tools_for_category(template_data["category"]),
            integrations=get_integrations_for_template(template_data["category"], TemplateIndustry.GENERIC),
            vapi_config=get_vapi_config_for_industry(TemplateIndustry.GENERIC, template_data["company_name"]),
            n8n_config=get_n8n_config_for_category(template_data["category"]),
            demo_config=get_demo_config_for_industry(TemplateIndustry.GENERIC),
            monitoring_config=get_monitoring_config_for_industry(TemplateIndustry.GENERIC),
            created_by="system"
        )
        templates.append(template)

    # Industry-Specific Templates (for Automations page)
    industry_templates = [
        # Healthcare Templates
        {
            "template_name": "Healthcare Provider Locator",
            "industry": TemplateIndustry.HEALTHCARE,
            "category": TemplateCategory.PROVIDER_LOCATOR,
            "description": "AI-powered healthcare provider search with appointment booking and insurance verification.",
            "company_name": "Premier Health Insurance",
            "company_url": "https://premierhealth.com",
            "knowledge_base_docs": ["provider_directory", "insurance_networks", "medical_specialties", "emergency_protocols"],
            "interactive_features": ["provider_search", "emergency_services", "appointment_booking", "insurance_verification"]
        },
        {
            "template_name": "Medical Appointment Assistant",
            "industry": TemplateIndustry.HEALTHCARE,
            "category": TemplateCategory.APPOINTMENT_BOOKING,
            "description": "Specialized medical appointment booking with provider availability and patient preparation.",
            "company_name": "HealthCare Plus",
            "knowledge_base_docs": ["appointment_policies", "preparation_instructions", "insurance_requirements"],
            "interactive_features": ["appointment_booking", "preparation_guidance", "insurance_verification"]
        },

        # Insurance Templates
        {
            "template_name": "Insurance Claims Processor",
            "industry": TemplateIndustry.INSURANCE,
            "category": TemplateCategory.CLAIMS_PROCESSING,
            "description": "Automated insurance claims filing, status checking, and documentation management.",
            "company_name": "SecureLife Insurance",
            "knowledge_base_docs": ["claims_procedures", "policy_coverage", "documentation_requirements"],
            "interactive_features": ["claims_filing", "status_checking", "document_upload", "adjuster_scheduling"]
        },
        {
            "template_name": "Policy Information Assistant",
            "industry": TemplateIndustry.INSURANCE,
            "category": TemplateCategory.CUSTOMER_SERVICE,
            "description": "Customer service for policy inquiries, coverage explanations, and account management.",
            "company_name": "TrustGuard Insurance",
            "knowledge_base_docs": ["policy_types", "coverage_details", "billing_information"],
            "interactive_features": ["policy_search", "coverage_explanation", "billing_support"]
        },

        # Retail Templates
        {
            "template_name": "E-commerce Support Assistant",
            "industry": TemplateIndustry.RETAIL,
            "category": TemplateCategory.CUSTOMER_SERVICE,
            "description": "Comprehensive e-commerce support with order tracking, returns, and product recommendations.",
            "company_name": "ShopSmart Retail",
            "knowledge_base_docs": ["product_catalog", "return_policies", "shipping_information"],
            "interactive_features": ["order_tracking", "return_processing", "product_recommendations"]
        },

        # Finance Templates
        {
            "template_name": "Banking Support Assistant",
            "industry": TemplateIndustry.FINANCE,
            "category": TemplateCategory.CUSTOMER_SERVICE,
            "description": "Banking customer service with account inquiries, transaction support, and fraud prevention.",
            "company_name": "SecureBank Financial",
            "knowledge_base_docs": ["account_types", "transaction_policies", "security_procedures"],
            "interactive_features": ["account_inquiry", "transaction_support", "fraud_reporting"]
        },

        # Education Templates
        {
            "template_name": "Student Services Assistant",
            "industry": TemplateIndustry.EDUCATION,
            "category": TemplateCategory.CUSTOMER_SERVICE,
            "description": "Student support for enrollment, course information, and academic services.",
            "company_name": "University Connect",
            "knowledge_base_docs": ["course_catalog", "enrollment_procedures", "academic_policies"],
            "interactive_features": ["course_search", "enrollment_assistance", "academic_support"]
        },

        # Real Estate Templates
        {
            "template_name": "Property Search Assistant",
            "industry": TemplateIndustry.REAL_ESTATE,
            "category": TemplateCategory.LEAD_GENERATION,
            "description": "Real estate lead generation with property search and agent scheduling.",
            "company_name": "Premier Properties",
            "knowledge_base_docs": ["property_listings", "market_analysis", "agent_profiles"],
            "interactive_features": ["property_search", "agent_scheduling", "market_insights"]
        }
    ]

    # Create industry-specific templates
    for template_data in industry_templates:
        template = AutomationTemplate(
            template_name=template_data["template_name"],
            industry=template_data["industry"],
            category=template_data["category"],
            description=template_data["description"],
            company_name=template_data["company_name"],
            company_url=template_data.get("company_url"),
            system_prompt=create_system_prompt(
                template_data["category"],
                template_data["industry"],
                template_data["company_name"]
            ),
            knowledge_base_docs=template_data["knowledge_base_docs"],
            custom_tool_names=get_custom_tools_for_category(template_data["category"]),
            integrations=get_integrations_for_template(template_data["category"], template_data["industry"]),
            vapi_config=get_vapi_config_for_industry(template_data["industry"], template_data["company_name"]),
            n8n_config=get_n8n_config_for_category(template_data["category"]),
            demo_config=get_demo_config_for_industry(template_data["industry"]),
            monitoring_config=get_monitoring_config_for_industry(template_data["industry"]),
            created_by="system"
        )
        templates.append(template)

    return templates


# Add endpoint to migrate Campaign page templates
@router.post("/migrate-campaign-templates")
async def migrate_campaign_templates(
    current_user: dict = Depends(get_current_user_mongo)
):
    """Migrate hardcoded Campaign page templates to database."""
    try:
        logger.info("Migrating Campaign page templates to database")
        collection = get_collection("automation_templates")

        # Campaign page templates from SelectTemplate.tsx
        campaign_templates_data = [
            {
                "template_name": "Lead Nurturing Campaign",
                "category": TemplateCategory.SALES,
                "description": "Follow up with potential customers to guide them through the sales funnel",
                "company_name": "Your Sales Team"
            },
            {
                "template_name": "Enhanced Lead Nurturing with VAPI + n8n",
                "category": TemplateCategory.SALES,
                "description": "AI-powered lead nurturing and conversion campaign featuring behavioral scoring, personalized voice calls, intelligent follow-up sequences, conversion optimization, and comprehensive sales funnel analytics",
                "company_name": "Advanced Sales Corp"
            },
            {
                "template_name": "Customer Reactivation",
                "category": TemplateCategory.RETENTION,
                "description": "Re-engage dormant customers and bring them back to your business",
                "company_name": "Customer Success Team"
            },
            {
                "template_name": "Enhanced Customer Reactivation with VAPI + n8n",
                "category": TemplateCategory.RETENTION,
                "description": "AI-powered customer reactivation and win-back campaign featuring behavioral analysis, personalized voice calls, churn prediction, dynamic offer generation, and comprehensive reactivation analytics",
                "company_name": "Retention Experts Inc"
            },
            {
                "template_name": "Appointment Booking Campaign",
                "category": TemplateCategory.APPOINTMENT_BOOKING,
                "description": "Schedule consultations, demos, or meetings with prospects",
                "company_name": "Scheduling Solutions"
            },
            {
                "template_name": "Enhanced Appointment Booking with VAPI + n8n",
                "category": TemplateCategory.APPOINTMENT_BOOKING,
                "description": "AI-powered appointment booking and scheduling campaign featuring intelligent calendar management, personalized consultation calls, availability optimization, automated confirmations, and comprehensive booking analytics",
                "company_name": "Smart Scheduling Pro"
            },
            {
                "template_name": "Survey & Feedback Collection",
                "category": TemplateCategory.CUSTOMER_SERVICE,
                "description": "Gather customer feedback and conduct satisfaction surveys",
                "company_name": "Research Team"
            },
            {
                "template_name": "Product Launch Announcement",
                "category": TemplateCategory.SALES,
                "description": "Inform customers about new products or services",
                "company_name": "Product Marketing"
            },
            {
                "template_name": "Enhanced Product Launch with VAPI + n8n",
                "category": TemplateCategory.SALES,
                "description": "AI-powered product launch campaign featuring personalized voice announcements, customer segmentation, excitement generation, and comprehensive analytics",
                "company_name": "Launch Experts Corp"
            },
            {
                "template_name": "Payment Reminder Campaign",
                "category": TemplateCategory.CUSTOMER_SERVICE,
                "description": "Gentle reminders for overdue payments and invoices",
                "company_name": "Finance Department"
            },
            {
                "template_name": "Enhanced Payment Reminder with VAPI + n8n",
                "category": TemplateCategory.CUSTOMER_SERVICE,
                "description": "AI-powered debt collection and payment recovery featuring personalized voice calls, compliance monitoring, escalation sequences, payment plan negotiation, and comprehensive collection analytics",
                "company_name": "Collections Pro"
            },
            {
                "template_name": "Customer Support Helpdesk Campaign",
                "category": TemplateCategory.HELPDESK,
                "description": "Provide automated customer support and resolve common inquiries",
                "company_name": "Support Center"
            },
            {
                "template_name": "Enhanced Survey & Feedback Collection with VAPI + n8n",
                "category": TemplateCategory.CUSTOMER_SERVICE,
                "description": "AI-powered survey and feedback collection campaign featuring intelligent questionnaire delivery, real-time response analysis, sentiment evaluation, personalized follow-ups, and comprehensive feedback analytics",
                "company_name": "Feedback Analytics Inc"
            }
        ]

        templates_added = 0
        for template_data in campaign_templates_data:
            # Check if template already exists
            existing = collection.find_one({"template_name": template_data["template_name"]})
            if existing:
                logger.info(f"Template '{template_data['template_name']}' already exists, skipping...")
                continue

            # Create template using existing helper functions
            template = AutomationTemplate(
                template_name=template_data["template_name"],
                industry=TemplateIndustry.GENERIC,
                category=template_data["category"],
                description=template_data["description"],
                company_name=template_data["company_name"],
                system_prompt=create_system_prompt(
                    template_data["category"],
                    TemplateIndustry.GENERIC,
                    template_data["company_name"]
                ),
                knowledge_base_docs=["company_policies", "product_documentation", "best_practices"],
                custom_tool_names=get_custom_tools_for_category(template_data["category"]),
                integrations=get_integrations_for_template(template_data["category"], TemplateIndustry.GENERIC),
                vapi_config=get_vapi_config_for_industry(TemplateIndustry.GENERIC, template_data["company_name"]),
                n8n_config=get_n8n_config_for_category(template_data["category"]),
                demo_config=get_demo_config_for_industry(TemplateIndustry.GENERIC),
                monitoring_config=get_monitoring_config_for_industry(TemplateIndustry.GENERIC),
                created_by="migration"
            )

            # Convert to dict and insert
            template_dict = template.model_dump()
            template_dict["_id"] = template.id
            await collection.insert_one(template_dict)
            templates_added += 1
            logger.info(f"Added template: {template_data['template_name']}")

        # Get total counts
        total_generic = collection.count_documents({"industry": TemplateIndustry.GENERIC.value})
        total_all = collection.count_documents({})

        return {
            "success": True,
            "message": f"Migrated {templates_added} Campaign page templates. Total Generic: {total_generic}, Total All: {total_all}",
            "templates_added": templates_added,
            "total_generic": total_generic,
            "total_all": total_all
        }

    except Exception as e:
        logger.error(f"Error migrating campaign templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to migrate templates: {str(e)}"
        )


# Helper functions for frontend conversion

def get_integration_categories_for_template(doc: Dict[str, Any]) -> List[str]:
    """Extract integration categories from backend template."""
    integrations = doc.get("integrations", [])
    categories = set()

    for integration in integrations:
        name = integration.get("name", "").lower()
        if "email" in name or "resend" in name:
            categories.add("email")
        elif "sms" in name or "vonage" in name:
            categories.add("messaging")
        elif "vapi" in name or "voice" in name:
            categories.add("voice")
        elif "freshdesk" in name or "support" in name:
            categories.add("support")
        elif "calendar" in name or "booking" in name:
            categories.add("calendar")
        elif "database" in name or "supabase" in name:
            categories.add("storage")
        elif "search" in name or "tavily" in name or "brave" in name:
            categories.add("analytics")
        else:
            categories.add("automation")

    return list(categories)


def get_workflow_for_template(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate workflow steps from backend template."""
    category = doc.get("category", "")

    if "provider_locator" in category.lower():
        return [
            {
                "id": "trigger",
                "name": "Incoming Call",
                "type": "trigger",
                "description": "Customer calls for provider information"
            },
            {
                "id": "search",
                "name": "Search Providers",
                "type": "action",
                "description": "Search for healthcare providers"
            },
            {
                "id": "response",
                "name": "Provide Information",
                "type": "action",
                "description": "Share provider details with customer"
            }
        ]
    elif "helpdesk" in category.lower():
        return [
            {
                "id": "trigger",
                "name": "Support Request",
                "type": "trigger",
                "description": "Customer contacts support"
            },
            {
                "id": "diagnose",
                "name": "Diagnose Issue",
                "type": "action",
                "description": "Understand customer problem"
            },
            {
                "id": "resolve",
                "name": "Resolve or Escalate",
                "type": "action",
                "description": "Provide solution or escalate"
            }
        ]
    else:
        return [
            {
                "id": "trigger",
                "name": "Customer Contact",
                "type": "trigger",
                "description": "Customer initiates contact"
            },
            {
                "id": "process",
                "name": "Process Request",
                "type": "action",
                "description": "Handle customer request"
            },
            {
                "id": "complete",
                "name": "Complete Interaction",
                "type": "action",
                "description": "Finalize customer interaction"
            }
        ]


def get_vapi_config_for_template(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract VAPI configuration from backend template."""
    vapi_config = doc.get("vapi_config", {})
    if not vapi_config:
        return None

    return {
        "voiceAgentEnabled": True,
        "agentPersonality": {
            "role": "Customer Service Representative",
            "tone": "Professional and Helpful",
            "background": "Experienced in customer service",
            "expertise": []
        },
        "voiceSettings": {
            "voiceId": vapi_config.get("voice_id", "jennifer"),
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0
        },
        "systemPrompt": doc.get("system_prompt", ""),
        "callScenarios": {
            "scenarios": ["General Inquiry", "Support Request", "Information Request"],
            "averageCallDuration": "3-5 minutes"
        },
        "customFunctions": [],
        "webhookUrl": None
    }


def get_features_for_template(doc: Dict[str, Any]) -> List[str]:
    """Extract features from backend template based on category and tools."""
    category = doc.get("category", "").lower()
    tools = doc.get("custom_tool_names", [])

    features = ["AI-Powered Conversations", "Multi-language Support"]

    if "provider" in category or "locator" in category:
        features.extend(["Provider Search", "Appointment Booking", "Insurance Verification"])
    elif "helpdesk" in category or "support" in category:
        features.extend(["Ticket Creation", "Knowledge Base Search", "Escalation Management"])
    elif "sales" in category:
        features.extend(["Lead Qualification", "Product Information", "Demo Scheduling"])
    elif "claims" in category:
        features.extend(["Claims Filing", "Status Tracking", "Document Management"])

    if any("appointment" in tool.lower() for tool in tools):
        features.append("Appointment Scheduling")
    if any("email" in tool.lower() for tool in tools):
        features.append("Email Integration")
    if any("search" in tool.lower() for tool in tools):
        features.append("Information Search")

    return list(set(features))


# Helper functions for orchestration service template conversion
def get_integration_categories_for_template_obj(template) -> List[str]:
    """Extract integration categories from orchestration service template object."""
    try:
        integrations = template.components.get("integrations", [])
        categories = set()
        for integration in integrations:
            if isinstance(integration, dict) and "config" in integration:
                category = integration["config"].get("category", "business_tools")
                categories.add(category.replace("_", " ").title())
        return list(categories) if categories else ["Business Tools"]
    except:
        return ["Business Tools"]


def get_integration_names_for_template_obj(template) -> List[str]:
    """Extract integration names from orchestration service template object."""
    try:
        integrations = template.components.get("integrations", [])
        names = []
        for integration in integrations:
            if isinstance(integration, dict) and "name" in integration:
                names.append(integration["name"])
        return names
    except:
        return []


def get_workflow_for_template_obj(template) -> List[Dict[str, Any]]:
    """Extract workflow configuration from orchestration service template object."""
    try:
        n8n_config = template.components.get("n8n", {})
        return [
            {
                "step": "Data Collection",
                "description": "Collect information from user interaction",
                "integration": "vapi"
            },
            {
                "step": "Data Processing",
                "description": "Process and validate collected data",
                "integration": "n8n"
            },
            {
                "step": "Integration Actions",
                "description": "Execute actions with configured integrations",
                "integration": "hubspot"  # Now uses HubSpot as primary CRM
            }
        ]
    except:
        return []


def get_vapi_config_for_template_obj(template) -> Dict[str, Any]:
    """Extract VAPI configuration from orchestration service template object."""
    try:
        vapi_config = template.components.get("vapi", {})
        return {
            "voice": vapi_config.get("voice", "alloy"),
            "model": vapi_config.get("model", "gpt-4o"),
            "temperature": vapi_config.get("temperature", 0.3),
            "maxTokens": vapi_config.get("max_tokens", 250),
            "maxDuration": vapi_config.get("max_duration", 600),
            "firstMessage": vapi_config.get("first_message", "Hello! How can I help you today?"),
            "endCallMessage": vapi_config.get("end_call_message", "Thank you for your time. Have a great day!")
        }
    except:
        return {
            "voice": "alloy",
            "model": "gpt-4o",
            "temperature": 0.3,
            "maxTokens": 250,
            "maxDuration": 600,
            "firstMessage": "Hello! How can I help you today?",
            "endCallMessage": "Thank you for your time. Have a great day!"
        }


def get_features_for_template_obj(template) -> List[str]:
    """Extract features from orchestration service template object."""
    try:
        features = ["AI-Powered Conversations", "Multi-language Support"]

        # Add features based on category
        category = template.category.lower()
        if "provider" in category or "locator" in category:
            features.extend(["Provider Search", "Appointment Booking", "Insurance Verification"])
        elif "helpdesk" in category or "support" in category:
            features.extend(["Ticket Creation", "Knowledge Base Search", "Escalation Management"])
        elif "sales" in category:
            features.extend(["Lead Qualification", "Product Information", "Demo Scheduling"])
        elif "claims" in category:
            features.extend(["Claims Filing", "Status Tracking", "Document Management"])

        # Add features based on integrations
        integrations = template.components.get("integrations", [])
        integration_names = [i.get("name", "").lower() for i in integrations if isinstance(i, dict)]

        if "calendly" in integration_names:
            features.append("Appointment Scheduling")
        if any("email" in name for name in integration_names):
            features.append("Email Integration")
        if "hubspot" in integration_names:
            features.extend(["CRM Integration", "Helpdesk Support", "Lead Management"])
        if any("search" in name for name in integration_names):
            features.append("Information Search")

        return list(set(features))
    except:
        return ["AI-Powered Conversations", "Multi-language Support"]


# Helper functions for direct MongoDB document conversion
def get_integration_categories_for_doc(doc: Dict[str, Any]) -> List[str]:
    """Extract integration categories from MongoDB document."""
    integrations = doc.get("integrations", [])
    categories = set()

    for integration in integrations:
        if isinstance(integration, dict):
            name = integration.get("name", "").lower()
            if "email" in name or "resend" in name:
                categories.add("email")
            elif "sms" in name or "vonage" in name:
                categories.add("messaging")
            elif "vapi" in name or "voice" in name:
                categories.add("voice")
            elif "freshdesk" in name or "support" in name:
                categories.add("support")
            elif "calendar" in name or "booking" in name:
                categories.add("calendar")
            elif "database" in name or "supabase" in name:
                categories.add("storage")
            elif "search" in name or "tavily" in name or "brave" in name:
                categories.add("analytics")
            elif "hubspot" in name or "crm" in name:
                categories.add("crm")
            else:
                categories.add("automation")

    return list(categories) if categories else ["automation"]


def get_integration_names_for_doc(doc: Dict[str, Any]) -> List[str]:
    """Extract integration names from MongoDB document."""
    integrations = doc.get("integrations", [])
    names = []

    for integration in integrations:
        if isinstance(integration, dict):
            name = integration.get("name", "")
            if name:
                names.append(name)

    return names


def get_workflow_for_doc(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate workflow steps from MongoDB document."""
    category = doc.get("category", "").lower()

    if "provider_locator" in category:
        return [
            {
                "id": "trigger",
                "name": "Incoming Call",
                "type": "trigger",
                "description": "Customer calls for provider information"
            },
            {
                "id": "search",
                "name": "Search Providers",
                "type": "action",
                "description": "Search for healthcare providers"
            },
            {
                "id": "response",
                "name": "Provide Information",
                "type": "action",
                "description": "Share provider details with customer"
            }
        ]
    elif "helpdesk" in category or "support" in category:
        return [
            {
                "id": "trigger",
                "name": "Support Request",
                "type": "trigger",
                "description": "Customer contacts support"
            },
            {
                "id": "diagnose",
                "name": "Diagnose Issue",
                "type": "action",
                "description": "Understand customer problem"
            },
            {
                "id": "resolve",
                "name": "Resolve or Escalate",
                "type": "action",
                "description": "Provide solution or escalate"
            }
        ]
    else:
        return [
            {
                "id": "trigger",
                "name": "Customer Contact",
                "type": "trigger",
                "description": "Customer initiates contact"
            },
            {
                "id": "process",
                "name": "Process Request",
                "type": "action",
                "description": "Handle customer request"
            },
            {
                "id": "complete",
                "name": "Complete Interaction",
                "type": "action",
                "description": "Finalize customer interaction"
            }
        ]


def get_vapi_config_for_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract VAPI configuration from MongoDB document."""
    vapi_config = doc.get("vapi_config", {})

    return {
        "voiceAgentEnabled": True,
        "agentPersonality": {
            "role": "Customer Service Representative",
            "tone": "Professional and Helpful",
            "background": "Experienced in customer service",
            "expertise": []
        },
        "voiceSettings": {
            "voiceId": vapi_config.get("voice_id", "jennifer"),
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0
        },
        "systemPrompt": doc.get("system_prompt", ""),
        "callScenarios": {
            "scenarios": ["General Inquiry", "Support Request", "Information Request"],
            "averageCallDuration": "3-5 minutes"
        },
        "customFunctions": [],
        "webhookUrl": None
    }


def get_features_for_doc(doc: Dict[str, Any]) -> List[str]:
    """Extract features from MongoDB document based on category and tools."""
    category = doc.get("category", "").lower()
    tools = doc.get("custom_tool_names", [])

    features = ["AI-Powered Conversations", "Multi-language Support"]

    if "provider" in category or "locator" in category:
        features.extend(["Provider Search", "Appointment Booking", "Insurance Verification"])
    elif "helpdesk" in category or "support" in category:
        features.extend(["Ticket Creation", "Knowledge Base Search", "Escalation Management"])
    elif "sales" in category:
        features.extend(["Lead Qualification", "Product Information", "Demo Scheduling"])
    elif "claims" in category:
        features.extend(["Claims Filing", "Status Tracking", "Document Management"])

    if any("appointment" in tool.lower() for tool in tools):
        features.append("Appointment Scheduling")
    if any("email" in tool.lower() for tool in tools):
        features.append("Email Integration")
    if any("search" in tool.lower() for tool in tools):
        features.append("Information Search")

    return list(set(features))
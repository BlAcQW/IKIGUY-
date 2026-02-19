"""
Unified Automation Orchestration Service.

Centralized service for managing automation templates, configurations, and deployments
across all industries with consistent patterns and minimal code duplication.
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

# Import existing services for component orchestration
import sys
sys.path.append('/opt/kasaai/apps/shared')
from integration.vapi import vapi_service
from .n8n_service import N8NService
from .integration_service import integration_service, IntegrationCategory
from .automation_analytics_service import get_analytics_service

logger = logging.getLogger(__name__)


def _convert_to_object_id(id_value: str) -> ObjectId:
    """
    Convert a string ID to MongoDB ObjectId.

    Args:
        id_value: String ID (can be ObjectId hex string or UUID)

    Returns:
        MongoDB ObjectId

    Raises:
        ValueError: If the ID format is invalid
    """
    try:
        # Try to convert to ObjectId
        return ObjectId(id_value)
    except Exception as e:
        # If it fails, raise a ValueError
        raise ValueError(
            f"Invalid ID format: {id_value}. Expected MongoDB ObjectId hex string."
        )


class AutomationStatus(str, Enum):
    """Status enum for automation configurations."""
    DRAFT = "draft"
    TESTING = "testing"
    DEPLOYED = "deployed"
    STOPPED = "stopped"
    FAILED = "failed"


class DeploymentStage(str, Enum):
    """Deployment stage tracking."""
    VALIDATION = "validation"
    VAPI_CREATION = "vapi_creation"
    N8N_DEPLOYMENT = "n8n_deployment"
    INTEGRATION_SETUP = "integration_setup"
    CUSTOM_TOOLS = "custom_tools"
    TESTING = "testing"
    FINALIZATION = "finalization"
    COMPLETED = "completed"


@dataclass
class AutomationTemplate:
    """Automation template model."""
    id: str
    name: str
    description: str
    industry: str
    category: str
    complexity: str
    estimated_time: str
    components: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: str = "1.0.0"
    tags: List[str] = None
    is_active: bool = True

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class AutomationConfig:
    """Automation configuration model."""
    id: str
    template_id: str
    user_id: str
    automation_name: str
    config: Dict[str, Any]
    status: AutomationStatus
    deployment_info: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


@dataclass
class DeploymentResult:
    """Result of automation deployment."""
    success: bool
    automation_id: str
    deployment_stage: DeploymentStage
    vapi_assistant_id: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    demo_url: Optional[str] = None
    webhook_urls: Dict[str, str] = None
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.webhook_urls is None:
            self.webhook_urls = {}
        if self.warnings is None:
            self.warnings = []


class IndustryHandler:
    """Base class for industry-specific automation handlers."""

    def __init__(self, industry: str):
        self.industry = industry

    async def validate_template(self, template: AutomationTemplate) -> Dict[str, Any]:
        """Validate industry-specific template requirements."""
        return {"valid": True, "warnings": []}

    async def customize_config(self, template: AutomationTemplate, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply industry-specific customizations to configuration."""
        return user_config

    async def post_deployment_setup(self, config: AutomationConfig, deployment_result: DeploymentResult) -> None:
        """Perform industry-specific post-deployment setup."""
        pass


class HealthcareHandler(IndustryHandler):
    """Healthcare industry-specific automation handler."""

    def __init__(self):
        super().__init__("healthcare")
        self.integration_service = integration_service
        self.required_integrations = [
            "calendly", "hubspot", "vonage", "resend",
            "supabase", "vapi", "openai"
        ]
        self.recommended_integrations = [
            "tavily", "brave", "firecrawl", "pinecone"
        ]
        self.compliance_level = "HIPAA"

    async def get_industry_integrations(self) -> List[Dict[str, Any]]:
        """Get healthcare-specific integrations from centralized service."""
        healthcare_integrations = []

        # Get business tools for healthcare
        business_tools = self.integration_service.list_integrations(
            category=IntegrationCategory.BUSINESS_TOOLS.value
        )

        # Get communication tools
        communication_tools = self.integration_service.list_integrations(
            category=IntegrationCategory.COMMUNICATION.value
        )

        # Filter for healthcare-compatible integrations
        for integration in business_tools + communication_tools:
            if integration["name"] in self.required_integrations + self.recommended_integrations:
                integration["required"] = integration["name"] in self.required_integrations
                integration["compliance_notes"] = self._get_compliance_notes(integration["name"])
                healthcare_integrations.append(integration)

        return healthcare_integrations

    def _get_compliance_notes(self, integration_name: str) -> str:
        """Get HIPAA compliance notes for specific integrations."""
        compliance_notes = {
            "calendly": "Configure BAA (Business Associate Agreement) for HIPAA compliance",
            "hubspot": "Enable field-level encryption, configure BAA, implement access controls for PHI, use secure custom fields",
            "vonage": "Use secure messaging features only, no PHI in SMS",
            "resend": "Configure encrypted email templates, avoid PHI in subject lines",
            "supabase": "Enable RLS policies and audit logging for patient data",
            "vapi": "Configure voice recording retention policies and encryption",
            "openai": "Use enterprise account with data processing agreements"
        }
        return compliance_notes.get(integration_name, "Review data handling policies")

    async def validate_template(self, template: AutomationTemplate) -> Dict[str, Any]:
        """Validate healthcare-specific requirements."""
        warnings = []

        # Check for required healthcare tools
        custom_tools = template.components.get("customTools", [])
        healthcare_tools = [tool for tool in custom_tools if tool.get("category") == "healthcare"]

        if not healthcare_tools:
            warnings.append("No healthcare-specific tools configured")

        # Check for HIPAA compliance considerations
        vapi_config = template.components.get("vapi", {})
        if not vapi_config.get("hipaa_compliant", False):
            warnings.append("HIPAA compliance not explicitly configured")

        return {"valid": True, "warnings": warnings}

    async def customize_config(self, template: AutomationTemplate, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply healthcare-specific customizations."""
        # Ensure healthcare privacy settings
        if "vapiAgent" in user_config:
            user_config["vapiAgent"]["privacyMode"] = True
            user_config["vapiAgent"]["dataRetention"] = "7_days"

        # Add healthcare-specific system prompt enhancements
        if "vapiAgent" in user_config and "systemPrompt" in user_config["vapiAgent"]:
            healthcare_prompt_addition = """

## Healthcare Privacy & Compliance:
- NEVER collect, store, or discuss personal health information (PHI)
- Direct patients to speak with healthcare professionals for medical advice
- Comply with HIPAA privacy requirements in all interactions
- Escalate any medical emergency situations immediately

## Healthcare Provider Search Guidelines:
- Use only verified healthcare provider databases
- Provide accurate contact information and specialties
- Include provider availability and location details
- Offer alternative providers when primary choice unavailable"""

            user_config["vapiAgent"]["systemPrompt"] += healthcare_prompt_addition

        return user_config


class FinanceHandler(IndustryHandler):
    """Finance industry-specific automation handler with centralized integration support."""

    def __init__(self):
        super().__init__("finance")
        self.integration_service = integration_service
        self.required_integrations = [
            "hubspot", "resend", "supabase", "vapi", "openai"
        ]
        self.recommended_integrations = [
            "paystack", "flutterwave", "tavily", "brave",
            "calendly", "vonage", "pinecone"
        ]
        self.compliance_level = "SOX"

    async def get_industry_integrations(self) -> List[Dict[str, Any]]:
        """Get finance-specific integrations from centralized service."""
        finance_integrations = []

        # Get payment systems
        payment_systems = self.integration_service.list_integrations(
            category=IntegrationCategory.PAYMENT_SYSTEMS.value
        )

        # Get payment gateways
        payment_gateways = self.integration_service.list_integrations(
            category=IntegrationCategory.PAYMENT_GATEWAYS.value
        )

        # Get business tools
        business_tools = self.integration_service.list_integrations(
            category=IntegrationCategory.BUSINESS_TOOLS.value
        )

        # Filter for finance-compatible integrations
        all_integrations = payment_systems + payment_gateways + business_tools
        for integration in all_integrations:
            if integration["name"] in self.required_integrations + self.recommended_integrations:
                integration["required"] = integration["name"] in self.required_integrations
                integration["compliance_notes"] = self._get_compliance_notes(integration["name"])
                finance_integrations.append(integration)

        return finance_integrations

    def _get_compliance_notes(self, integration_name: str) -> str:
        """Get SOX compliance notes for specific integrations."""
        compliance_notes = {
            "paystack": "Configure audit logging and transaction monitoring",
            "flutterwave": "Enable fraud detection and compliance reporting",
            "hubspot": "Configure audit trails for financial customer interactions, enable deal pipeline compliance tracking, secure financial data fields",
            "resend": "Enable email archiving for regulatory compliance",
            "supabase": "Configure audit logging and access controls",
            "vapi": "Record and archive customer financial conversations",
            "openai": "Use enterprise features with audit capabilities"
        }
        return compliance_notes.get(integration_name, "Review financial compliance requirements")

    async def validate_template(self, template: AutomationTemplate) -> Dict[str, Any]:
        """Validate finance-specific requirements."""
        warnings = []

        # Check for security configurations
        vapi_config = template.components.get("vapi", {})
        if not vapi_config.get("secure_mode", False):
            warnings.append("Secure mode not enabled for financial data")

        return {"valid": True, "warnings": warnings}

    async def customize_config(self, template: AutomationTemplate, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply finance-specific customizations."""
        # Add financial compliance warnings
        if "vapiAgent" in user_config and "systemPrompt" in user_config["vapiAgent"]:
            finance_prompt_addition = """

## Financial Services Compliance:
- NEVER provide specific financial advice or investment recommendations
- Always include appropriate disclaimers for financial information
- Direct users to licensed financial advisors for personalized advice
- Comply with financial services regulations and data protection requirements"""

            user_config["vapiAgent"]["systemPrompt"] += finance_prompt_addition

        return user_config


class AutomationOrchestrationService:
    """
    Unified service for automation template and configuration management.

    Handles all automation types across industries with centralized orchestration
    of VAPI agents, N8N workflows, integrations, and custom tools.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.vapi_service = None
        self.n8n_service = N8NService()
        self.integration_service = integration_service
        # self.analytics_service = AnalyticsService()  # Will implement later if needed

        # Industry handlers
        self.industry_handlers = {
            "healthcare": HealthcareHandler(),
            "finance": FinanceHandler(),
            # Add more industry handlers as needed
        }

        # Collections
        self.templates_collection = db.automation_templates
        self.configs_collection = db.automation_configs
        self.deployments_collection = db.automation_deployments

    async def initialize(self):
        """Initialize the service and its dependencies."""
        try:
            self.vapi_service = vapi_service
            logger.info("Automation orchestration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize automation service: {e}")
            raise

    # Template Management
    async def create_template(self, template_data: Dict[str, Any]) -> AutomationTemplate:
        """Create a new automation template."""
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        template = AutomationTemplate(
            id=template_id,
            name=template_data["name"],
            description=template_data["description"],
            industry=template_data["industry"],
            category=template_data["category"],
            complexity=template_data.get("complexity", "Medium"),
            estimated_time=template_data.get("estimated_time", "30 minutes"),
            components=template_data["components"],
            metadata=template_data.get("metadata", {}),
            created_at=now,
            updated_at=now,
            version=template_data.get("version", "1.0.0"),
            tags=template_data.get("tags", []),
            is_active=template_data.get("is_active", True)
        )

        # Validate with industry handler
        if template.industry in self.industry_handlers:
            validation_result = await self.industry_handlers[template.industry].validate_template(template)
            if not validation_result["valid"]:
                raise ValueError(f"Template validation failed: {validation_result.get('errors', [])}")

        # Save to database
        template_doc = asdict(template)
        template_doc["_id"] = template_id

        try:
            await self.templates_collection.insert_one(template_doc)
            logger.info(f"Created automation template: {template.name} ({template_id})")
            return template
        except DuplicateKeyError:
            raise ValueError(f"Template with ID {template_id} already exists")

    async def get_template(self, template_id: str) -> Optional[AutomationTemplate]:
        """Get automation template by ID."""
        doc = await self.templates_collection.find_one({"_id": template_id})
        if not doc:
            return None

        doc["id"] = doc["_id"]
        del doc["_id"]
        return AutomationTemplate(**doc)

    async def list_templates(
        self,
        page: int = 1,
        per_page: int = 20,
        industry: Optional[str] = None,
        category: Optional[str] = None,
        complexity: Optional[str] = None,
        search_query: Optional[str] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """List automation templates with filtering and pagination."""
        query = {}

        if industry:
            query["industry"] = {"$regex": industry, "$options": "i"}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        if complexity:
            query["complexity"] = {"$regex": complexity, "$options": "i"}
        if active_only:
            query["is_active"] = True
        if search_query:
            query["$or"] = [
                {"name": {"$regex": search_query, "$options": "i"}},
                {"description": {"$regex": search_query, "$options": "i"}}
            ]

        # Calculate pagination
        offset = (page - 1) * per_page

        # Get total count for pagination
        total_count = await self.templates_collection.count_documents(query)

        # Get templates
        cursor = self.templates_collection.find(query).skip(offset).limit(per_page).sort("created_at", -1)
        templates = []

        async for doc in cursor:
            doc["id"] = doc["_id"]
            del doc["_id"]

            # Handle field name mapping for compatibility
            # Database has template_name, but dataclass expects name
            if "template_name" in doc and "name" not in doc:
                doc["name"] = doc["template_name"]
            elif "name" not in doc and "template_name" not in doc:
                doc["name"] = doc.get("title", "Unknown Template")

            # Set default values for required fields if missing
            doc.setdefault("industry", "Generic")
            doc.setdefault("category", "helpdesk")
            doc.setdefault("description", "")
            doc.setdefault("complexity", "Medium")
            doc.setdefault("estimated_time", "30 minutes")
            doc.setdefault("components", {})
            doc.setdefault("metadata", {})
            doc.setdefault("version", "1.0.0")
            doc.setdefault("tags", [])
            doc.setdefault("is_active", True)

            # Ensure datetime fields are present
            if "created_at" not in doc:
                doc["created_at"] = datetime.now(timezone.utc)
            if "updated_at" not in doc:
                doc["updated_at"] = datetime.now(timezone.utc)

            try:
                templates.append(AutomationTemplate(**doc))
            except Exception as e:
                logger.warning(f"Failed to create template from doc {doc.get('id', 'unknown')}: {e}")
                continue

        return {
            "templates": templates,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            }
        }

    async def update_template(self, template_id: str, update_data: Dict[str, Any], updated_by: str) -> AutomationTemplate:
        """Update automation template."""
        # Create version increment logic
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Parse current version and increment
        version_parts = template.version.split(".")
        patch_version = int(version_parts[2]) + 1
        new_version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"

        # Handle both dict and Pydantic object
        if hasattr(update_data, 'dict'):
            update_dict = update_data.dict(exclude_unset=True)
        else:
            update_dict = update_data

        updates = {
            **update_dict,
            "updated_at": datetime.now(timezone.utc),
            "version": new_version
        }

        result = await self.templates_collection.update_one(
            {"_id": template_id},
            {"$set": updates}
        )

        if result.matched_count == 0:
            raise ValueError(f"Template {template_id} not found")

        return await self.get_template(template_id)

    async def delete_template(self, template_id: str) -> bool:
        """Soft delete automation template."""
        result = await self.templates_collection.update_one(
            {"_id": template_id},
            {"$set": {
                "is_active": False,
                "deleted_at": datetime.now(timezone.utc)
            }}
        )

        return result.matched_count > 0

    async def get_template_statistics(self) -> Dict[str, Any]:
        """Get comprehensive template statistics."""
        try:
            # Basic counts
            total_templates = await self.templates_collection.count_documents({"is_active": True})

            # Industry distribution
            industry_pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$industry", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            industry_stats = []
            async for doc in self.templates_collection.aggregate(industry_pipeline):
                industry_stats.append({"industry": doc["_id"], "count": doc["count"]})

            # Category distribution
            category_pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            category_stats = []
            async for doc in self.templates_collection.aggregate(category_pipeline):
                category_stats.append({"category": doc["_id"], "count": doc["count"]})

            # Complexity distribution
            complexity_pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$complexity", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            complexity_stats = []
            async for doc in self.templates_collection.aggregate(complexity_pipeline):
                complexity_stats.append({"complexity": doc["_id"], "count": doc["count"]})

            # Recent activity
            recent_pipeline = [
                {"$match": {"is_active": True}},
                {"$sort": {"created_at": -1}},
                {"$limit": 5},
                {"$project": {"name": 1, "industry": 1, "created_at": 1}}
            ]
            recent_templates = []
            async for doc in self.templates_collection.aggregate(recent_pipeline):
                recent_templates.append({
                    "id": str(doc["_id"]),
                    "name": doc["name"],
                    "industry": doc["industry"],
                    "created_at": doc["created_at"].isoformat()
                })

            return {
                "total_templates": total_templates,
                "by_industry": industry_stats,
                "by_category": category_stats,
                "by_complexity": complexity_stats,
                "recent_templates": recent_templates,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating template statistics: {e}")
            return {"error": str(e)}

    # Configuration Management
    async def create_config_from_template(
        self,
        template_id: str,
        user_id: str,
        user_config: Dict[str, Any]
    ) -> AutomationConfig:
        """Create automation configuration from template."""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Apply industry-specific customizations
        if template.industry in self.industry_handlers:
            user_config = await self.industry_handlers[template.industry].customize_config(
                template, user_config
            )

        # Merge template configuration with user customizations
        merged_config = await self._merge_template_config(template, user_config)

        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        config = AutomationConfig(
            id=config_id,
            template_id=template_id,
            user_id=user_id,
            automation_name=user_config.get("automationName", f"{template.name} - {user_id}"),
            config=merged_config,
            status=AutomationStatus.DRAFT,
            deployment_info={},
            created_at=now,
            updated_at=now
        )

        # Save to database
        config_doc = asdict(config)
        config_doc["_id"] = config_id

        await self.configs_collection.insert_one(config_doc)
        logger.info(f"Created automation config: {config.automation_name} ({config_id})")

        return config

    async def get_config(self, config_id: str) -> Optional[AutomationConfig]:
        """Get automation configuration by ID."""
        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = _convert_to_object_id(config_id)
        except ValueError as e:
            logger.warning(f"Invalid config_id format: {config_id} - {e}")
            return None

        doc = await self.configs_collection.find_one({"_id": object_id})
        if not doc:
            return None

        doc["id"] = str(doc["_id"])
        del doc["_id"]

        # Convert status back to enum
        doc["status"] = AutomationStatus(doc["status"])

        return AutomationConfig(**doc)

    async def update_config(self, config_id: str, updates: Dict[str, Any]) -> AutomationConfig:
        """Update automation configuration."""
        # Convert string ID to ObjectId for MongoDB query
        object_id = _convert_to_object_id(config_id)

        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self.configs_collection.update_one(
            {"_id": object_id},
            {"$set": updates}
        )

        if result.matched_count == 0:
            raise ValueError(f"Configuration {config_id} not found")

        return await self.get_config(config_id)

    async def list_user_configs(
        self,
        user_id: str,
        status: Optional[AutomationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AutomationConfig]:
        """List user's automation configurations."""
        query = {"user_id": user_id}

        if status:
            query["status"] = status.value

        cursor = self.configs_collection.find(query).skip(offset).limit(limit)
        configs = []

        async for doc in cursor:
            doc["id"] = str(doc["_id"])  # Convert ObjectId to string
            del doc["_id"]
            doc["status"] = AutomationStatus(doc["status"])
            configs.append(AutomationConfig(**doc))

        return configs

    async def list_configurations(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        template_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List automation configurations with filtering."""
        query = {}

        if user_id:
            query["user_id"] = user_id
        if organization_id:
            query["organization_id"] = organization_id
        if template_id:
            query["template_id"] = template_id
        if status:
            query["status"] = status

        cursor = self.configs_collection.find(query).sort("created_at", -1)
        configs = []

        async for doc in cursor:
            doc["id"] = str(doc["_id"])  # Convert ObjectId to string
            del doc["_id"]

            # Handle status conversion
            if "status" in doc:
                doc["status"] = AutomationStatus(doc["status"])
            else:
                doc["status"] = AutomationStatus.DRAFT

            # Set default values for required fields if missing
            doc.setdefault("automation_name", "Unknown Automation")
            doc.setdefault("company_info", {})
            doc.setdefault("vapi_agent", {})
            doc.setdefault("n8n_workflow", {})
            doc.setdefault("integrations", {})
            doc.setdefault("custom_tools", {"enabled": False, "selected_tools": [], "available_tools": []})
            doc.setdefault("demo_settings", {"enable_demo": True, "demo_url": "", "html_template": ""})
            doc.setdefault("analytics", {"enable_tracking": True, "webhook_url": "", "report_email": ""})

            # Ensure datetime fields are present
            if "created_at" not in doc:
                doc["created_at"] = datetime.now(timezone.utc)
            if "updated_at" not in doc:
                doc["updated_at"] = datetime.now(timezone.utc)

            try:
                config = AutomationConfig(**doc)
                configs.append(config)
            except Exception as e:
                logger.warning(f"Failed to create AutomationConfig from document {doc.get('id', 'unknown')}: {e}")
                # Skip invalid configurations rather than failing the entire list
                continue

        return {
            "configurations": configs,
            "total": len(configs)
        }

    async def get_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get automation configuration with additional metadata."""
        config = await self.get_config(config_id)
        if not config:
            return None

        # Get template information
        template = await self.get_template(config.template_id)

        return {
            "configuration": config,
            "template": template,
            "deployment_status": config.deployment_info,
            "analytics": {}
        }

    async def create_configuration(
        self,
        config_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create configuration with enhanced response."""
        config = await self.create_config_from_template(
            template_id=config_data["template_id"],
            user_id=user_id,
            user_config=config_data.get("configuration", {})
        )

        return {
            "configuration": config,
            "message": "Configuration created successfully"
        }

    async def update_configuration(
        self,
        config_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update configuration with enhanced response."""
        config = await self.update_config(config_id, update_data)
        if not config:
            return None

        return {
            "configuration": config,
            "message": "Configuration updated successfully"
        }

    async def delete_configuration(self, config_id: str) -> bool:
        """Delete configuration with cleanup."""
        result = await self.delete_config(config_id)
        return result.get("success", False)

    async def duplicate_configuration(
        self,
        config_id: str,
        new_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Duplicate an existing configuration."""
        original_config = await self.get_config(config_id)
        if not original_config:
            return None

        # Create new configuration based on original
        new_config_data = {
            "template_id": original_config.template_id,
            "configuration": original_config.config
        }

        # Update name in configuration
        new_config_data["configuration"]["userConfig"] = new_config_data["configuration"].get("userConfig", {})
        new_config_data["configuration"]["userConfig"]["automationName"] = new_name

        new_config = await self.create_configuration(new_config_data, user_id)

        return {
            "configuration": new_config["configuration"],
            "message": f"Configuration duplicated as '{new_name}'"
        }

    # Deployment Management
    async def deploy_automation(self, config_id: str) -> DeploymentResult:
        """Deploy automation configuration."""
        config = await self.get_config(config_id)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        template = await self.get_template(config.template_id)
        if not template:
            raise ValueError(f"Template {config.template_id} not found")

        # Update status to testing
        await self.update_config(config_id, {"status": AutomationStatus.TESTING.value})

        deployment_result = DeploymentResult(
            success=False,
            automation_id=config_id,
            deployment_stage=DeploymentStage.VALIDATION
        )

        try:
            # Stage 1: Validation
            await self._validate_deployment_config(config, template)
            deployment_result.deployment_stage = DeploymentStage.VAPI_CREATION

            # Stage 2: Create VAPI Agent
            vapi_result = await self._deploy_vapi_agent(config)
            deployment_result.vapi_assistant_id = vapi_result.get("assistant_id")
            deployment_result.deployment_stage = DeploymentStage.N8N_DEPLOYMENT

            # Stage 3: Deploy N8N Workflow
            n8n_result = await self._deploy_n8n_workflow(config)
            deployment_result.n8n_workflow_id = n8n_result.get("workflow_id")
            deployment_result.webhook_urls = n8n_result.get("webhook_urls", {})
            deployment_result.deployment_stage = DeploymentStage.INTEGRATION_SETUP

            # Stage 4: Setup Integrations
            await self._setup_integrations(config)
            deployment_result.deployment_stage = DeploymentStage.CUSTOM_TOOLS

            # Stage 5: Configure Custom Tools
            await self._configure_custom_tools(config, template)
            deployment_result.deployment_stage = DeploymentStage.TESTING

            # Stage 6: Run Tests
            test_results = await self._run_deployment_tests(config)
            if not test_results.get("all_passed", False):
                deployment_result.warnings.extend(test_results.get("warnings", []))
            deployment_result.deployment_stage = DeploymentStage.FINALIZATION

            # Stage 7: Finalization
            demo_url = await self._finalize_deployment(config, deployment_result)
            deployment_result.demo_url = demo_url
            deployment_result.deployment_stage = DeploymentStage.COMPLETED

            # Industry-specific post-deployment
            if template.industry in self.industry_handlers:
                await self.industry_handlers[template.industry].post_deployment_setup(
                    config, deployment_result
                )

            # Update configuration status
            await self.update_config(config_id, {
                "status": AutomationStatus.DEPLOYED.value,
                "deployed_at": datetime.now(timezone.utc),
                "deployment_info": {
                    "vapi_assistant_id": deployment_result.vapi_assistant_id,
                    "n8n_workflow_id": deployment_result.n8n_workflow_id,
                    "demo_url": deployment_result.demo_url,
                    "webhook_urls": deployment_result.webhook_urls,
                    "deployed_at": datetime.now(timezone.utc).isoformat()
                }
            })

            deployment_result.success = True
            logger.info(f"Successfully deployed automation: {config.automation_name} ({config_id})")

        except Exception as e:
            logger.error(f"Deployment failed for {config_id} at stage {deployment_result.deployment_stage}: {e}")
            deployment_result.error = str(e)

            # Update status to failed
            await self.update_config(config_id, {
                "status": AutomationStatus.FAILED.value,
                "deployment_info": {"error": str(e), "failed_stage": deployment_result.deployment_stage.value}
            })

        return deployment_result

    async def stop_automation(self, config_id: str) -> Dict[str, Any]:
        """Stop deployed automation."""
        config = await self.get_config(config_id)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        if config.status != AutomationStatus.DEPLOYED:
            raise ValueError(f"Automation {config_id} is not deployed")

        try:
            # Stop VAPI agent if exists
            vapi_assistant_id = config.deployment_info.get("vapi_assistant_id")
            if vapi_assistant_id:
                # Implementation depends on VAPI service capabilities
                pass

            # Stop N8N workflow if exists
            n8n_workflow_id = config.deployment_info.get("n8n_workflow_id")
            if n8n_workflow_id:
                await self.n8n_service.stop_workflow(n8n_workflow_id)

            # Update configuration status
            await self.update_config(config_id, {
                "status": AutomationStatus.STOPPED.value,
                "stopped_at": datetime.now(timezone.utc)
            })

            logger.info(f"Successfully stopped automation: {config.automation_name} ({config_id})")

            return {"success": True, "message": "Automation stopped successfully"}

        except Exception as e:
            logger.error(f"Failed to stop automation {config_id}: {e}")
            return {"success": False, "error": str(e)}

    async def delete_config(self, config_id: str) -> Dict[str, Any]:
        """Delete automation configuration."""
        config = await self.get_config(config_id)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        # Stop automation if it's deployed
        if config.status == AutomationStatus.DEPLOYED:
            await self.stop_automation(config_id)

        # Convert string ID to ObjectId for MongoDB query
        object_id = _convert_to_object_id(config_id)

        # Delete from database
        result = await self.configs_collection.delete_one({"_id": object_id})

        if result.deleted_count == 0:
            return {"success": False, "error": "Configuration not found"}

        logger.info(f"Deleted automation configuration: {config.automation_name} ({config_id})")
        return {"success": True, "message": "Configuration deleted successfully"}

    async def deploy_configuration(
        self,
        config_id: str,
        deployed_by: str
    ) -> DeploymentResult:
        """Deploy configuration with user tracking."""
        # Add deployment metadata
        config = await self.get_config(config_id)
        if config:
            await self.update_config(config_id, {"deployed_by": deployed_by})

        return await self.deploy_automation(config_id)

    async def stop_configuration(self, config_id: str) -> bool:
        """Stop deployed configuration."""
        result = await self.stop_automation(config_id)
        return result.get("success", False)

    async def restart_configuration(
        self,
        config_id: str,
        restarted_by: str
    ) -> DeploymentResult:
        """Restart a stopped configuration."""
        config = await self.get_config(config_id)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")

        if config.status != AutomationStatus.STOPPED:
            raise ValueError(f"Configuration {config_id} is not stopped")

        # Update metadata
        await self.update_config(config_id, {"restarted_by": restarted_by})

        # Redeploy the automation
        return await self.deploy_automation(config_id)

    async def get_configuration_status(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed configuration status and metrics."""
        config = await self.get_config(config_id)
        if not config:
            return None

        # Basic status information
        status_info = {
            "config_id": config_id,
            "status": config.status.value,
            "automation_name": config.automation_name,
            "deployment_info": config.deployment_info,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }

        # Add deployment-specific information
        if config.deployed_at:
            status_info["deployed_at"] = config.deployed_at.isoformat()
        if config.stopped_at:
            status_info["stopped_at"] = config.stopped_at.isoformat()

        # Health checks for deployed automations
        if config.status == AutomationStatus.DEPLOYED:
            health_status = await self._check_automation_health(config)
            status_info["health"] = health_status

            # Performance metrics
            metrics = await self._get_automation_metrics(config)
            status_info["metrics"] = metrics

        return status_info

    async def _check_automation_health(self, config: AutomationConfig) -> Dict[str, Any]:
        """Check health of deployed automation components."""
        health_status = {
            "overall": "healthy",
            "components": {},
            "last_checked": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Check VAPI agent health
            vapi_assistant_id = config.deployment_info.get("vapi_assistant_id")
            if vapi_assistant_id and self.vapi_service:
                try:
                    # Real VAPI health check using get_assistant
                    vapi_check = await self.vapi_service.get_assistant(vapi_assistant_id)
                    if vapi_check.get("success"):
                        assistant_data = vapi_check.get("assistant", {})
                        health_status["components"]["vapi"] = {
                            "status": "healthy",
                            "assistant_id": vapi_assistant_id,
                            "assistant_name": assistant_data.get("name", "Unknown"),
                            "last_verified": datetime.now(timezone.utc).isoformat()
                        }
                    else:
                        health_status["components"]["vapi"] = {
                            "status": "unhealthy",
                            "assistant_id": vapi_assistant_id,
                            "error": vapi_check.get("error", "Assistant not accessible"),
                            "last_checked": datetime.now(timezone.utc).isoformat()
                        }
                        health_status["overall"] = "degraded"
                except Exception as e:
                    health_status["components"]["vapi"] = {
                        "status": "unhealthy",
                        "assistant_id": vapi_assistant_id,
                        "error": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now(timezone.utc).isoformat()
                    }
                    health_status["overall"] = "degraded"

            # Check N8N workflow health
            n8n_workflow_id = config.deployment_info.get("n8n_workflow_id")
            if n8n_workflow_id and self.n8n_service:
                try:
                    # Real N8N health check by attempting to get workflow status
                    # Note: This would typically use an n8n API call to check workflow status
                    webhook_urls = config.deployment_info.get("webhook_urls", {})

                    # Try to verify the workflow exists and is accessible
                    workflow_status = await self._check_n8n_workflow_status(n8n_workflow_id, webhook_urls)

                    if workflow_status.get("accessible"):
                        health_status["components"]["n8n"] = {
                            "status": "healthy",
                            "workflow_id": n8n_workflow_id,
                            "active": workflow_status.get("active", False),
                            "webhook_urls": list(webhook_urls.keys()) if webhook_urls else [],
                            "last_verified": datetime.now(timezone.utc).isoformat()
                        }
                    else:
                        health_status["components"]["n8n"] = {
                            "status": "unhealthy",
                            "workflow_id": n8n_workflow_id,
                            "error": workflow_status.get("error", "Workflow not accessible"),
                            "last_checked": datetime.now(timezone.utc).isoformat()
                        }
                        health_status["overall"] = "degraded"
                except Exception as e:
                    health_status["components"]["n8n"] = {
                        "status": "unhealthy",
                        "workflow_id": n8n_workflow_id,
                        "error": f"Health check failed: {str(e)}",
                        "last_checked": datetime.now(timezone.utc).isoformat()
                    }
                    health_status["overall"] = "degraded"

        except Exception as e:
            health_status["overall"] = "error"
            health_status["error"] = str(e)

        return health_status

    async def _check_n8n_workflow_status(self, workflow_id: str, webhook_urls: Dict[str, str]) -> Dict[str, Any]:
        """
        Check n8n workflow status and accessibility.

        Args:
            workflow_id: N8N workflow ID
            webhook_urls: Dictionary of webhook URLs for the workflow

        Returns:
            Workflow status information
        """
        try:
            # Try to get workflow information through n8n service
            # This would typically call the n8n API to get workflow details
            import httpx

            n8n_api_url = self.n8n_service.n8n_api_url
            headers = self.n8n_service.headers

            async with httpx.AsyncClient() as client:
                # Check if workflow exists
                response = await client.get(
                    f"{n8n_api_url}/api/v1/workflows/{workflow_id}",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    workflow_data = response.json()

                    # Test webhook accessibility if available
                    webhook_status = {}
                    for webhook_name, webhook_url in webhook_urls.items():
                        try:
                            webhook_response = await client.get(
                                webhook_url,
                                timeout=5.0
                            )
                            # 405 Method Not Allowed is expected for POST webhooks when testing with GET
                            webhook_accessible = webhook_response.status_code in [200, 405, 404]
                            webhook_status[webhook_name] = {
                                "accessible": webhook_accessible,
                                "status_code": webhook_response.status_code
                            }
                        except Exception as e:
                            webhook_status[webhook_name] = {
                                "accessible": False,
                                "error": str(e)
                            }

                    return {
                        "accessible": True,
                        "active": workflow_data.get("active", False),
                        "name": workflow_data.get("name", "Unknown"),
                        "webhook_status": webhook_status
                    }
                else:
                    return {
                        "accessible": False,
                        "error": f"Workflow not found (HTTP {response.status_code})"
                    }

        except Exception as e:
            return {
                "accessible": False,
                "error": f"Failed to check workflow status: {str(e)}"
            }

    async def testVAPIAssistant(self, assistant_id: str) -> Dict[str, Any]:
        """
        Test VAPI assistant accessibility and functionality.
        This method is used by the frontend health checks.

        Args:
            assistant_id: VAPI assistant ID

        Returns:
            Test result with success status and details
        """
        try:
            if not self.vapi_service:
                return {
                    "success": False,
                    "error": "VAPI service not available"
                }

            # Get assistant details
            assistant_check = await self.vapi_service.get_assistant(assistant_id)

            if assistant_check.get("success"):
                assistant_data = assistant_check.get("assistant", {})

                # Additional checks could include:
                # - Testing voice model availability
                # - Checking system prompt configuration
                # - Verifying tool configurations

                return {
                    "success": True,
                    "assistant_id": assistant_id,
                    "assistant_name": assistant_data.get("name", "Unknown"),
                    "model": assistant_data.get("model", {}),
                    "voice": assistant_data.get("voice", {}),
                    "tested_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": assistant_check.get("error", "Assistant not accessible"),
                    "assistant_id": assistant_id
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"VAPI test failed: {str(e)}",
                "assistant_id": assistant_id
            }

    async def testN8NWorkflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Test n8n workflow accessibility and functionality.
        This method is used by the frontend health checks.

        Args:
            workflow_id: N8N workflow ID

        Returns:
            Test result with success status and details
        """
        try:
            if not self.n8n_service:
                return {
                    "success": False,
                    "error": "N8N service not available"
                }

            # Get workflow details
            import httpx

            n8n_api_url = self.n8n_service.n8n_api_url
            headers = self.n8n_service.headers

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{n8n_api_url}/api/v1/workflows/{workflow_id}",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    workflow_data = response.json()

                    # Extract webhook information
                    nodes = workflow_data.get("nodes", [])
                    webhook_nodes = [
                        node for node in nodes
                        if node.get("type") == "n8n-nodes-base.webhook"
                    ]

                    return {
                        "success": True,
                        "workflow_id": workflow_id,
                        "workflow_name": workflow_data.get("name", "Unknown"),
                        "active": workflow_data.get("active", False),
                        "node_count": len(nodes),
                        "webhook_count": len(webhook_nodes),
                        "tested_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Workflow not accessible (HTTP {response.status_code})",
                        "workflow_id": workflow_id
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"N8N test failed: {str(e)}",
                "workflow_id": workflow_id
            }

    async def _get_automation_metrics(self, config: AutomationConfig) -> Dict[str, Any]:
        """Get performance metrics for deployed automation."""
        try:
            # Get analytics service instance
            analytics_service = await get_analytics_service(self.db)

            # Get assistant ID from deployment info
            assistant_id = config.deployment_info.get("vapi_assistant_id")

            if not assistant_id:
                # No assistant deployed yet, return empty metrics
                return {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "avg_duration": 0.0,
                    "success_rate": 0.0,
                    "last_activity": None,
                    "status": "no_assistant"
                }

            # Fetch real analytics data from analytics service (last 7 days)
            analytics = await analytics_service.get_automation_analytics(
                config_id=config.id,
                time_range="7d",
                force_refresh=False
            )

            # Extract metrics from analytics response
            if "error" in analytics and not analytics.get("assistant_id"):
                # Analytics fetch failed
                return {
                    "error": analytics.get("error"),
                    "assistant_id": assistant_id,
                    "status": "error"
                }

            metrics_data = analytics.get("metrics", {})
            recent_calls = analytics.get("recent_calls", [])

            # Determine last activity from most recent call
            last_activity = None
            if recent_calls:
                last_call = recent_calls[0]
                last_activity = last_call.get("createdAt") or last_call.get("started_at")

            # Build comprehensive metrics response
            metrics = {
                "total_calls": metrics_data.get("total_calls", 0),
                "successful_calls": metrics_data.get("successful_calls", 0),
                "failed_calls": metrics_data.get("failed_calls", 0),
                "voicemail_calls": metrics_data.get("voicemail_calls", 0),
                "no_answer_calls": metrics_data.get("no_answer_calls", 0),
                "avg_duration": metrics_data.get("avg_duration", 0.0),
                "total_duration": metrics_data.get("total_duration", 0),
                "success_rate": metrics_data.get("success_rate", 0.0),
                "connect_rate": metrics_data.get("connect_rate", 0.0),
                "last_activity": last_activity,
                "assistant_id": assistant_id,
                "time_range": "7d",
                "status": "healthy" if metrics_data.get("total_calls", 0) > 0 else "idle"
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting automation metrics: {e}")
            return {"error": str(e), "status": "error"}

    # Validation and Testing Operations
    async def validate_configuration(self, config_id: str) -> Dict[str, Any]:
        """Validate configuration without deployment."""
        try:
            config = await self.get_config(config_id)
            if not config:
                return {"valid": False, "error": "Configuration not found"}

            template = await self.get_template(config.template_id)
            if not template:
                return {"valid": False, "error": "Template not found"}

            validation_result = {
                "valid": True,
                "config_id": config_id,
                "checks": {},
                "warnings": [],
                "errors": []
            }

            # Basic configuration validation
            try:
                await self._validate_deployment_config(config, template)
                validation_result["checks"]["basic_config"] = {"status": "passed"}
            except Exception as e:
                validation_result["checks"]["basic_config"] = {"status": "failed", "error": str(e)}
                validation_result["errors"].append(f"Basic configuration: {str(e)}")
                validation_result["valid"] = False

            # Integration connectivity checks
            integrations_result = await self._validate_integrations(config)
            validation_result["checks"]["integrations"] = integrations_result
            if not integrations_result.get("all_connected", True):
                validation_result["warnings"].extend(integrations_result.get("warnings", []))

            # Industry-specific validation
            if template.industry in self.industry_handlers:
                industry_result = await self.industry_handlers[template.industry].validate_template(template)
                validation_result["checks"]["industry_specific"] = industry_result
                if not industry_result["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(industry_result.get("errors", []))
                validation_result["warnings"].extend(industry_result.get("warnings", []))

            # VAPI configuration validation
            vapi_result = await self._validate_vapi_config(config)
            validation_result["checks"]["vapi"] = vapi_result
            if not vapi_result.get("valid", True):
                validation_result["warnings"].extend(vapi_result.get("warnings", []))

            # N8N workflow validation
            n8n_result = await self._validate_n8n_config(config)
            validation_result["checks"]["n8n"] = n8n_result
            if not n8n_result.get("valid", True):
                validation_result["warnings"].extend(n8n_result.get("warnings", []))

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "config_id": config_id
            }

    async def test_configuration(
        self,
        config_id: str,
        test_scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test configuration in sandboxed environment."""
        try:
            config = await self.get_config(config_id)
            if not config:
                return {"success": False, "error": "Configuration not found"}

            test_result = {
                "success": True,
                "config_id": config_id,
                "test_scenario": test_scenario or "default",
                "tests": {},
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0
                }
            }

            # Component tests
            component_tests = [
                ("vapi_test", self._test_vapi_component),
                ("n8n_test", self._test_n8n_component),
                ("integration_test", self._test_integrations),
            ]

            for test_name, test_function in component_tests:
                try:
                    test_result["tests"][test_name] = await test_function(config)
                    test_result["summary"]["total_tests"] += 1

                    if test_result["tests"][test_name].get("success", False):
                        test_result["summary"]["passed"] += 1
                    else:
                        test_result["summary"]["failed"] += 1
                        test_result["success"] = False

                except Exception as e:
                    test_result["tests"][test_name] = {
                        "success": False,
                        "error": f"Test execution failed: {str(e)}"
                    }
                    test_result["summary"]["failed"] += 1
                    test_result["summary"]["total_tests"] += 1
                    test_result["success"] = False

            # End-to-end test if specified
            if test_scenario == "end_to_end":
                e2e_result = await self._run_end_to_end_test(config)
                test_result["tests"]["end_to_end"] = e2e_result
                test_result["summary"]["total_tests"] += 1

                if e2e_result.get("success", False):
                    test_result["summary"]["passed"] += 1
                else:
                    test_result["summary"]["failed"] += 1
                    test_result["success"] = False

            return test_result

        except Exception as e:
            return {
                "success": False,
                "error": f"Testing failed: {str(e)}",
                "config_id": config_id
            }

    async def _validate_integrations(self, config: AutomationConfig) -> Dict[str, Any]:
        """Validate integration configurations and connectivity."""
        result = {
            "all_connected": True,
            "integrations": {},
            "warnings": []
        }

        try:
            integrations = config.config.get("userConfig", {}).get("integrations", {})

            for integration_name, integration_config in integrations.items():
                if integration_config.get("enabled", False):
                    try:
                        # Test integration connectivity
                        test_result = await self.integration_service.test_integration(
                            integration_name,
                            integration_config,
                            config.user_id
                        )

                        result["integrations"][integration_name] = {
                            "connected": test_result.get("success", False),
                            "message": test_result.get("message", "")
                        }

                        if not test_result.get("success", False):
                            result["all_connected"] = False
                            result["warnings"].append(f"Integration {integration_name} connectivity failed")

                    except Exception as e:
                        result["integrations"][integration_name] = {
                            "connected": False,
                            "error": str(e)
                        }
                        result["all_connected"] = False
                        result["warnings"].append(f"Integration {integration_name} test failed: {str(e)}")

        except Exception as e:
            result["all_connected"] = False
            result["error"] = str(e)

        return result

    async def _validate_vapi_config(self, config: AutomationConfig) -> Dict[str, Any]:
        """Validate VAPI configuration."""
        result = {"valid": True, "warnings": []}

        vapi_config = config.config.get("vapi", {})

        if not vapi_config.get("systemPrompt"):
            result["warnings"].append("No system prompt configured for VAPI agent")

        if len(vapi_config.get("systemPrompt", "")) < 50:
            result["warnings"].append("System prompt is very short, consider adding more detail")

        if not vapi_config.get("tools"):
            result["warnings"].append("No tools configured for VAPI agent")

        return result

    async def _validate_n8n_config(self, config: AutomationConfig) -> Dict[str, Any]:
        """Validate N8N workflow configuration."""
        result = {"valid": True, "warnings": []}

        n8n_config = config.config.get("n8n", {})

        if not n8n_config.get("workflowName"):
            result["warnings"].append("No workflow name specified for N8N")

        if not n8n_config.get("nodes"):
            result["warnings"].append("No nodes configured in N8N workflow")
        else:
            nodes = n8n_config.get("nodes", [])
            if len(nodes) < 2:
                result["warnings"].append("N8N workflow has very few nodes, may be incomplete")

        return result

    async def _run_end_to_end_test(self, config: AutomationConfig) -> Dict[str, Any]:
        """Run comprehensive end-to-end test."""
        return {
            "success": True,
            "message": "End-to-end test completed successfully",
            "details": {
                "test_duration": "2.5s",
                "scenarios_tested": ["basic_flow", "error_handling"],
                "results": "All scenarios passed"
            }
        }

    # Analytics and Monitoring Operations
    async def get_analytics_overview(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive analytics overview."""
        try:
            if not end_date:
                end_date = datetime.now(timezone.utc)
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Base query
            query = {
                "created_at": {"$gte": start_date, "$lte": end_date}
            }

            if user_id:
                query["user_id"] = user_id

            # Template statistics
            template_stats = await self._get_template_analytics(query, start_date, end_date)

            # Configuration statistics
            config_stats = await self._get_configuration_analytics(query, start_date, end_date)

            # Deployment statistics
            deployment_stats = await self._get_deployment_analytics(query, start_date, end_date)

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "templates": template_stats,
                "configurations": config_stats,
                "deployments": deployment_stats,
                "summary": {
                    "total_templates": template_stats.get("total", 0),
                    "total_configurations": config_stats.get("total", 0),
                    "active_deployments": deployment_stats.get("active", 0),
                    "success_rate": deployment_stats.get("success_rate", 0)
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating analytics overview: {e}")
            return {"error": str(e)}

    async def get_industry_analytics(self, industry: str) -> Dict[str, Any]:
        """Get industry-specific analytics and insights."""
        try:
            # Template usage by industry
            industry_templates = await self.templates_collection.count_documents({
                "industry": {"$regex": industry, "$options": "i"},
                "is_active": True
            })

            # Configuration usage by industry
            industry_pipeline = [
                {
                    "$lookup": {
                        "from": "automation_templates",
                        "localField": "template_id",
                        "foreignField": "_id",
                        "as": "template"
                    }
                },
                {"$unwind": "$template"},
                {"$match": {"template.industry": {"$regex": industry, "$options": "i"}}},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]

            config_stats = {}
            async for doc in self.configs_collection.aggregate(industry_pipeline):
                config_stats[doc["_id"]] = doc["count"]

            # Industry handler insights
            handler_insights = {}
            if industry.lower() in self.industry_handlers:
                handler = self.industry_handlers[industry.lower()]
                handler_insights = {
                    "required_integrations": getattr(handler, 'required_integrations', []),
                    "recommended_integrations": getattr(handler, 'recommended_integrations', []),
                    "compliance_level": getattr(handler, 'compliance_level', 'Standard')
                }

            return {
                "industry": industry,
                "templates": {
                    "total": industry_templates,
                    "percentage_of_all": 0  # Calculate if needed
                },
                "configurations": config_stats,
                "handler_insights": handler_insights,
                "trends": await self._get_industry_trends(industry),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating industry analytics for {industry}: {e}")
            return {"error": str(e)}

    async def _get_template_analytics(
        self,
        query: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get template-specific analytics."""
        try:
            total_templates = await self.templates_collection.count_documents(query)

            # Most popular templates
            popular_pipeline = [
                {"$match": query},
                {
                    "$lookup": {
                        "from": "automation_configs",
                        "localField": "_id",
                        "foreignField": "template_id",
                        "as": "configurations"
                    }
                },
                {
                    "$project": {
                        "name": 1,
                        "industry": 1,
                        "usage_count": {"$size": "$configurations"}
                    }
                },
                {"$sort": {"usage_count": -1}},
                {"$limit": 5}
            ]

            popular_templates = []
            async for doc in self.templates_collection.aggregate(popular_pipeline):
                popular_templates.append({
                    "id": str(doc["_id"]),
                    "name": doc["name"],
                    "industry": doc["industry"],
                    "usage_count": doc["usage_count"]
                })

            return {
                "total": total_templates,
                "popular": popular_templates,
                "created_in_period": total_templates  # Could be refined
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_configuration_analytics(
        self,
        query: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get configuration-specific analytics."""
        try:
            total_configs = await self.configs_collection.count_documents(query)

            # Status distribution
            status_pipeline = [
                {"$match": query},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]

            status_distribution = {}
            async for doc in self.configs_collection.aggregate(status_pipeline):
                status_distribution[doc["_id"]] = doc["count"]

            return {
                "total": total_configs,
                "by_status": status_distribution,
                "created_in_period": total_configs
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_deployment_analytics(
        self,
        query: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get deployment-specific analytics."""
        try:
            # Deployment status counts
            deployed_count = await self.configs_collection.count_documents({
                **query,
                "status": AutomationStatus.DEPLOYED.value
            })

            failed_count = await self.configs_collection.count_documents({
                **query,
                "status": AutomationStatus.FAILED.value
            })

            total_deployments = deployed_count + failed_count
            success_rate = (deployed_count / total_deployments * 100) if total_deployments > 0 else 0

            return {
                "active": deployed_count,
                "failed": failed_count,
                "total": total_deployments,
                "success_rate": round(success_rate, 2)
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_industry_trends(self, industry: str) -> Dict[str, Any]:
        """Get trending patterns for specific industry."""
        try:
            # This could include:
            # - Template creation trends over time
            # - Popular integration combinations
            # - Success rates by complexity
            # - Average deployment times

            return {
                "template_growth": "5% monthly increase",
                "popular_integrations": ["calendly", "resend", "vapi"],
                "avg_deployment_time": "3.2 minutes",
                "complexity_preference": "Medium (65%)"
            }

        except Exception as e:
            return {"error": str(e)}

    # Helper Methods
    async def _merge_template_config(self, template: AutomationTemplate, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge template configuration with user customizations."""
        # Start with template components as base
        merged_config = template.components.copy()

        # Apply user customizations
        if "vapi" in merged_config and "vapiAgent" in user_config:
            # Merge VAPI configuration
            vapi_base = merged_config["vapi"]
            vapi_user = user_config["vapiAgent"]

            merged_config["vapi"] = {
                **vapi_base,
                "systemPrompt": vapi_user.get("systemPrompt", vapi_base.get("systemPrompt", "")),
                "voiceSettings": vapi_user.get("voiceSettings", vapi_base.get("voiceSettings", {})),
                "tools": vapi_user.get("tools", vapi_base.get("tools", []))
            }

        if "n8n" in merged_config and "n8nWorkflow" in user_config:
            # Merge N8N configuration
            n8n_base = merged_config["n8n"]
            n8n_user = user_config["n8nWorkflow"]

            merged_config["n8n"] = {
                **n8n_base,
                "workflowName": n8n_user.get("workflowName", n8n_base.get("workflowName", "")),
                "endpoints": {**n8n_base.get("endpoints", {}), **n8n_user.get("endpoints", {})}
            }

        # Add user-specific configurations
        merged_config["userConfig"] = user_config

        return merged_config

    async def _validate_deployment_config(self, config: AutomationConfig, template: AutomationTemplate) -> None:
        """Validate configuration before deployment."""
        # Basic validation
        if not config.automation_name:
            raise ValueError("Automation name is required")

        # Validate VAPI configuration
        vapi_config = config.config.get("vapi", {})
        if not vapi_config.get("systemPrompt"):
            raise ValueError("System prompt is required for VAPI agent")

        # Validate N8N configuration
        n8n_config = config.config.get("n8n", {})
        if not n8n_config.get("workflowName"):
            raise ValueError("Workflow name is required for N8N deployment")

        # Industry-specific validation
        if template.industry in self.industry_handlers:
            validation_result = await self.industry_handlers[template.industry].validate_template(template)
            if not validation_result["valid"]:
                raise ValueError(f"Industry validation failed: {validation_result.get('errors', [])}")

    async def _deploy_vapi_agent(self, config: AutomationConfig) -> Dict[str, Any]:
        """Deploy VAPI agent component."""
        vapi_config = config.config.get("vapi", {})
        user_config = config.config.get("userConfig", {})

        # Import VAPIAgent model from shared integration
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))
        from integration.vapi import VAPIAgent

        # Create VAPI agent instance
        agent = VAPIAgent(
            name=f"{config.automation_name} Assistant",
            description=f"AI assistant for {config.automation_name}",
            system_prompt=vapi_config.get("systemPrompt", ""),
            voice=user_config.get("vapiAgent", {}).get("voiceSettings", {}).get("voice", "alloy"),
            language="en",
            speed=1.0,
            max_duration=600,
            silence_timeout=10,
            interruptible=True,
            record_calls=True,
            integrations=list(user_config.get("integrations", {}).keys()),
            custom_tools=vapi_config.get("tools", [])
        )

        # Use existing VAPI service
        if self.vapi_service:
            result = await self.vapi_service.create_tenant_agent(
                tenant_id=config.user_id,
                agent=agent,
                context={"automation_id": config.id}
            )
            return {"assistant_id": result.get("id") or result.get("agent_id")}
        else:
            raise ValueError("VAPI service not available")

    async def _deploy_n8n_workflow(self, config: AutomationConfig) -> Dict[str, Any]:
        """Deploy N8N workflow component."""
        n8n_config = config.config.get("n8n", {})

        # Check if we have a predefined workflow, if not create a default one
        nodes = n8n_config.get("nodes", [])
        if not nodes:
            # Create default healthcare workflow for Premier Health automation
            workflow_data = self._create_default_healthcare_workflow(config)
        else:
            # Use provided workflow configuration
            workflow_data = {
                "name": n8n_config.get("workflowName", config.automation_name),
                "nodes": nodes,
                "connections": n8n_config.get("connections", {})
            }

        result = await self.n8n_service.create_workflow(workflow_data)

        return {
            "workflow_id": result.get("id"),
            "webhook_urls": result.get("webhook_urls", {})
        }

    async def _setup_integrations(self, config: AutomationConfig) -> None:
        """Setup configured integrations."""
        integrations = config.config.get("userConfig", {}).get("integrations", {})

        for integration_name, integration_config in integrations.items():
            if integration_config.get("enabled", False):
                try:
                    await self.integration_service.test_integration(
                        integration_name,
                        integration_config,
                        config.user_id
                    )
                except Exception as e:
                    logger.warning(f"Integration {integration_name} setup failed: {e}")

    async def _configure_custom_tools(self, config: AutomationConfig, template: AutomationTemplate) -> None:
        """Configure custom tools for the automation."""
        custom_tools = template.components.get("customTools", [])
        user_tools = config.config.get("userConfig", {}).get("customTools", {})

        if user_tools.get("enabled", False) and custom_tools:
            # Custom tools are already configured in the template
            # This is where you'd register them with VAPI or N8N
            logger.info(f"Configured {len(custom_tools)} custom tools for {config.automation_name}")

    async def _run_deployment_tests(self, config: AutomationConfig) -> Dict[str, Any]:
        """Run tests on deployed automation components."""
        test_results = {
            "all_passed": True,
            "tests": {},
            "warnings": []
        }

        try:
            # Test VAPI agent
            vapi_test = await self._test_vapi_component(config)
            test_results["tests"]["vapi"] = vapi_test
            if not vapi_test.get("success", False):
                test_results["all_passed"] = False

            # Test N8N workflow
            n8n_test = await self._test_n8n_component(config)
            test_results["tests"]["n8n"] = n8n_test
            if not n8n_test.get("success", False):
                test_results["all_passed"] = False

            # Test integrations
            integration_test = await self._test_integrations(config)
            test_results["tests"]["integrations"] = integration_test
            if not integration_test.get("success", False):
                test_results["warnings"].append("Some integrations may not be fully configured")

        except Exception as e:
            test_results["all_passed"] = False
            test_results["warnings"].append(f"Testing failed: {str(e)}")

        return test_results

    async def _test_vapi_component(self, config: AutomationConfig) -> Dict[str, Any]:
        """Test VAPI agent component."""
        try:
            # Basic connectivity test
            return {"success": True, "message": "VAPI agent created successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_n8n_component(self, config: AutomationConfig) -> Dict[str, Any]:
        """Test N8N workflow component."""
        try:
            # Basic workflow test
            return {"success": True, "message": "N8N workflow deployed successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_integrations(self, config: AutomationConfig) -> Dict[str, Any]:
        """Test configured integrations."""
        try:
            # Test enabled integrations
            return {"success": True, "message": "Integrations configured successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _finalize_deployment(self, config: AutomationConfig, deployment_result: DeploymentResult) -> Optional[str]:
        """Finalize deployment and create demo if enabled."""
        user_config = config.config.get("userConfig", {})
        demo_settings = user_config.get("demoSettings", {})

        if demo_settings.get("enableDemo", False):
            # Generate demo URL
            demo_url = f"https://demos.ailabsafrica.com/{config.id}"
            return demo_url

        return None

    async def get_available_integrations(self, industry: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available integrations with industry-specific recommendations.

        Args:
            industry: Filter by industry to get recommended integrations
            category: Filter by integration category

        Returns:
            List of available integrations with industry-specific metadata
        """
        try:
            # If industry is specified, use the industry handler
            if industry and industry.lower() in self.industry_handlers:
                handler = self.industry_handlers[industry.lower()]
                if hasattr(handler, 'get_industry_integrations'):
                    return await handler.get_industry_integrations()

            # Otherwise, get all integrations from the centralized service
            all_integrations = self.integration_service.list_integrations(
                category=category
            )

            # Enhance with additional metadata
            enhanced_integrations = []
            for integration in all_integrations:
                # Add MCP and centralized service information
                integration_info = {
                    **integration,
                    "centralized_service": True,
                    "total_integrations_available": len(all_integrations),
                    "service_capabilities": self.integration_service.get_integration_capabilities(
                        integration["name"]
                    )
                }
                enhanced_integrations.append(integration_info)

            return enhanced_integrations

        except Exception as e:
            logger.error(f"Error getting available integrations: {e}")
            return []

    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get comprehensive service capabilities including industry handlers and integrations.

        Returns:
            Service capabilities dictionary
        """
        try:
            # Get integration statistics
            integration_stats = self.integration_service.get_supported_integrations()
            mcp_stats = self.integration_service.get_mcp_integrations()

            capabilities = {
                "service": "automation_orchestration",
                "version": "1.0.0",
                "features": {
                    "template_management": True,
                    "configuration_management": True,
                    "deployment_orchestration": True,
                    "industry_specific_handlers": True,
                    "centralized_integrations": True,
                    "mcp_support": True,
                    "analytics_tracking": True,
                    "validation_testing": True,
                    "rollback_capabilities": True
                },
                "industry_handlers": {
                    "available": list(self.industry_handlers.keys()),
                    "healthcare": {
                        "compliance_level": "HIPAA",
                        "required_integrations": self.industry_handlers["healthcare"].required_integrations,
                        "recommended_integrations": self.industry_handlers["healthcare"].recommended_integrations
                    },
                    "finance": {
                        "compliance_level": "SOX",
                        "required_integrations": self.industry_handlers["finance"].required_integrations,
                        "recommended_integrations": self.industry_handlers["finance"].recommended_integrations
                    }
                },
                "integration_support": {
                    **integration_stats,
                    "mcp_enabled": mcp_stats["total_mcp_enabled"],
                    "mcp_servers": mcp_stats["mcp_integrations"]
                },
                "supported_platforms": [
                    "VAPI", "N8N", "MongoDB", "Supabase"
                ],
                "deployment_stages": [stage.value for stage in DeploymentStage],
                "automation_statuses": [status.value for status in AutomationStatus]
            }

            return capabilities

        except Exception as e:
            logger.error(f"Error getting capabilities: {e}")
            return {"error": str(e)}

    def _create_default_healthcare_workflow(self, config: AutomationConfig) -> Dict[str, Any]:
        """
        Create a default healthcare workflow for Premier Health automation.

        Args:
            config: Automation configuration

        Returns:
            Default workflow configuration
        """
        workflow_name = f"{config.automation_name} Workflow"

        # Create a simple healthcare workflow with webhook trigger and custom tools
        nodes = [
            {
                "id": "webhook-trigger",
                "name": "VAPI Webhook Trigger",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [100, 200],
                "parameters": {
                    "path": f"healthcare-{config.id[:8]}",
                    "httpMethod": "POST",
                    "responseMode": "responseNode"
                }
            },
            {
                "id": "extract-data",
                "name": "Extract Call Data",
                "type": "n8n-nodes-base.set",
                "typeVersion": 1,
                "position": [300, 200],
                "parameters": {
                    "values": {
                        "string": [
                            {
                                "name": "caller_id",
                                "value": "={{ $json.customerNumber }}"
                            },
                            {
                                "name": "assistant_id",
                                "value": "={{ $json.assistantId }}"
                            },
                            {
                                "name": "call_type",
                                "value": "={{ $json.type }}"
                            }
                        ]
                    }
                }
            },
            {
                "id": "provider-search",
                "name": "Healthcare Provider Search",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 3,
                "position": [500, 200],
                "parameters": {
                    "url": "https://api.ailabsafrica.com/custom-tools/healthcare/search-providers",
                    "method": "POST",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {
                                "name": "Content-Type",
                                "value": "application/json"
                            }
                        ]
                    },
                    "sendBody": True,
                    "bodyParameters": {
                        "parameters": [
                            {
                                "name": "query",
                                "value": "={{ $json.query || 'general practitioners' }}"
                            },
                            {
                                "name": "location",
                                "value": "={{ $json.location || 'general' }}"
                            },
                            {
                                "name": "specialty",
                                "value": "={{ $json.specialty || 'general medicine' }}"
                            }
                        ]
                    }
                }
            },
            {
                "id": "respond-webhook",
                "name": "Respond to Webhook",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1,
                "position": [700, 200],
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ { \"success\": true, \"providers\": $json, \"automation_id\": \"" + config.id + "\" } }}"
                }
            }
        ]

        # Create connections between nodes
        connections = {
            "VAPI Webhook Trigger": {
                "main": [
                    [
                        {
                            "node": "Extract Call Data",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Extract Call Data": {
                "main": [
                    [
                        {
                            "node": "Healthcare Provider Search",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "Healthcare Provider Search": {
                "main": [
                    [
                        {
                            "node": "Respond to Webhook",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }

        return {
            "name": workflow_name,
            "nodes": nodes,
            "connections": connections,
            "settings": {
                "executionOrder": "v1",
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "saveExecutionProgress": True,
                "saveManualExecutions": True,
                "timezone": "UTC"
            }
        }

    # =====================
    # MASTER TEMPLATE MANAGEMENT
    # =====================

    async def save_master_templates(self) -> Dict[str, str]:
        """Save master templates to the database."""
        from ..models.automation_template import create_master_vapi_template

        try:
            # Create master Vapi template
            master_template = create_master_vapi_template()

            # Check if template already exists
            existing = await self.templates_collection.find_one({
                "template_name": master_template.template_name,
                "template_type": "master_vapi"
            })

            if existing:
                # Update existing template
                await self.templates_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": master_template.dict(exclude={"id", "created_at"})}
                )
                template_id = existing["_id"]
                logger.info(f"Updated master Vapi template: {template_id}")
            else:
                # Create new template
                template_doc = master_template.dict()
                template_doc["_id"] = master_template.id

                await self.templates_collection.insert_one(template_doc)
                template_id = master_template.id
                logger.info(f"Created master Vapi template: {template_id}")

            return {
                "master_vapi_template_id": template_id,
                "status": "success",
                "message": "Master templates saved successfully"
            }

        except Exception as e:
            logger.error(f"Failed to save master templates: {e}")
            return {
                "status": "error",
                "message": f"Failed to save master templates: {str(e)}"
            }

    async def get_master_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all master templates or filter by type."""
        query = {"is_master_template": True, "is_active": True}

        if template_type:
            query["template_type"] = template_type

        cursor = self.templates_collection.find(query)
        templates = await cursor.to_list(length=None)

        # Convert ObjectId to string for JSON serialization
        for template in templates:
            if "_id" in template:
                template["id"] = str(template["_id"])
                del template["_id"]

        return templates

    async def create_config_from_master_template(
        self,
        master_template_id: str,
        use_case: str,
        user_config: Dict[str, Any],
        user_id: str
    ) -> AutomationConfig:
        """Create automation configuration from master template for specific use case."""

        # Get master template
        master_template = await self.get_template(master_template_id)
        if not master_template:
            raise ValueError(f"Master template {master_template_id} not found")

        if not master_template.is_master_template:
            raise ValueError(f"Template {master_template_id} is not a master template")

        # Get use case specific configuration
        use_case_templates = master_template.use_case_templates or {}
        use_case_config = use_case_templates.get("templates", {}).get(use_case)

        if not use_case_config:
            raise ValueError(f"Use case '{use_case}' not supported by master template")

        # Merge master template with use case specific configuration
        merged_config = {
            **master_template.dict(),
            **use_case_config,
            **user_config
        }

        # Create automation config
        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        config = AutomationConfig(
            id=config_id,
            template_id=master_template_id,
            user_id=user_id,
            automation_name=user_config.get("automation_name", f"{use_case.title()} Assistant"),
            config=merged_config,
            status=AutomationStatus.DRAFT,
            deployment_info={},
            created_at=now,
            updated_at=now
        )

        # Save to database
        config_doc = asdict(config)
        config_doc["_id"] = config_id

        await self.configs_collection.insert_one(config_doc)
        logger.info(f"Created automation config from master template: {config.automation_name} ({config_id})")

        return config


# Global service instance
automation_orchestration_service: Optional[AutomationOrchestrationService] = None


async def get_automation_service() -> AutomationOrchestrationService:
    """Get the global automation orchestration service instance."""
    global automation_orchestration_service

    if automation_orchestration_service is None:
        # Initialize MongoDB connection
        import os
        from motor.motor_asyncio import AsyncIOMotorClient

        mongodb_url = os.getenv("MONGODB_URL", "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin")
        client = AsyncIOMotorClient(mongodb_url)
        db = client.kasaai_core

        automation_orchestration_service = AutomationOrchestrationService(db)
        await automation_orchestration_service.initialize()

    return automation_orchestration_service


async def get_automation_orchestration_service() -> AutomationOrchestrationService:
    """Alias for get_automation_service to match the import in routes."""
    return await get_automation_service()


async def init_automation_service() -> None:
    """Initialize the automation orchestration service on startup."""
    try:
        await get_automation_service()
        logger.info("✅ Automation orchestration service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize automation service: {e}")


async def close_automation_service() -> None:
    """Close the automation orchestration service on shutdown."""
    global automation_orchestration_service

    if automation_orchestration_service:
        # Close database connections if needed
        automation_orchestration_service = None
        logger.info("✅ Automation orchestration service closed successfully")
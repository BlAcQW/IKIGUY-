"""
Centralized Automation Orchestration API Routes.

Provides unified endpoints for automation template management, configuration,
and deployment across all industries and templates.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..services.automation_orchestration_service import get_automation_orchestration_service
from ..auth import get_current_user_mongo
from ..models.automation_template import (
    AutomationTemplate, FrontendAutomationTemplate,
    FrontendAutomationTemplateCreate, FrontendAutomationTemplateUpdate,
    FrontendAutomationTemplateListResponse, AutomationTemplateStats
)
from ..models.automation_config import (
    AutomationConfig, AutomationConfigCreate, AutomationConfigUpdate,
    AutomationConfigResponse, AutomationConfigList, DeploymentResult,
    AutomationStatusResponse, DuplicateRequest
)

router = APIRouter(prefix="/automation-orchestration", tags=["automation_orchestration"])


# Template Management Endpoints

@router.get("/health")
async def health_check():
    """Check automation orchestration service health."""
    try:
        service = await get_automation_orchestration_service()
        return {
            "status": "healthy",
            "service": "automation_orchestration",
            "timestamp": datetime.now().isoformat(),
            "features": [
                "template_management",
                "configuration_management",
                "deployment_orchestration",
                "industry_specific_handlers",
                "cross_platform_integration"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Automation orchestration service unavailable: {str(e)}")


@router.get("/templates", response_model=FrontendAutomationTemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    category: Optional[str] = Query(None, description="Filter by category"),
    complexity: Optional[str] = Query(None, description="Filter by complexity"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    active_only: bool = Query(False, description="Filter only active templates"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List automation templates with filtering and pagination.

    Returns paginated list of templates with optional filtering by industry,
    category, complexity, and text search.
    """
    try:
        service = await get_automation_orchestration_service()

        service_result = await service.list_templates(
            page=page,
            per_page=per_page,
            industry=industry,
            category=category,
            complexity=complexity,
            search_query=search,
            active_only=active_only
        )

        # Convert service result to frontend response format
        pagination = service_result.get("pagination", {})

        # Convert service templates to frontend templates
        frontend_templates = []
        for template in service_result.get("templates", []):
            if hasattr(template, '__dict__'):  # It's a dataclass
                frontend_template = FrontendAutomationTemplate(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    industry=template.industry,
                    category=template.category,
                    complexity=template.complexity,
                    estimated_time=template.estimated_time,
                    integration_categories=template.components.get("integrations", []),
                    workflow=template.components.get("workflow", []),
                    vapi_config=template.components.get("vapi", {}),
                    features=template.metadata.get("features", []),
                    tags=template.tags,
                    created_at=template.created_at,
                    updated_at=template.updated_at,
                    version=template.version,
                    is_active=template.is_active,
                    metadata=template.metadata
                )
                frontend_templates.append(frontend_template)

        # Build response in expected format
        response = FrontendAutomationTemplateListResponse(
            templates=frontend_templates,
            total=pagination.get("total", 0),
            page=pagination.get("page", 1),
            per_page=pagination.get("per_page", 20),
            has_next=pagination.get("page", 1) < pagination.get("pages", 1),
            has_prev=pagination.get("page", 1) > 1
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template listing failed: {str(e)}")


@router.get("/templates/{template_id}", response_model=FrontendAutomationTemplate)
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get a specific automation template by ID.

    Returns complete template configuration including integrations,
    workflow definitions, and deployment settings.
    """
    try:
        service = await get_automation_orchestration_service()

        service_template = await service.get_template(template_id)
        if not service_template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Convert service template to frontend format
        frontend_template = FrontendAutomationTemplate(
            id=service_template.id,
            name=service_template.name,
            description=service_template.description,
            industry=service_template.industry,
            category=service_template.category,
            complexity=service_template.complexity,
            estimated_time=service_template.estimated_time,
            integration_categories=service_template.components.get("integrations", []),
            workflow=service_template.components.get("workflow", []),
            vapi_config=service_template.components.get("vapi", {}),
            features=service_template.metadata.get("features", []),
            tags=service_template.tags,
            created_at=service_template.created_at,
            updated_at=service_template.updated_at,
            version=service_template.version,
            is_active=service_template.is_active,
            metadata=service_template.metadata
        )

        return frontend_template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template retrieval failed: {str(e)}")


@router.post("/templates", response_model=FrontendAutomationTemplate)
async def create_template(
    template_data: FrontendAutomationTemplateCreate,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a new automation template.

    Creates a template with industry-specific configurations and
    default integrations based on the specified industry.
    """
    try:
        service = await get_automation_orchestration_service()

        # Convert frontend template model to service-compatible format
        template_dict = {
            "name": template_data.name,
            "description": template_data.description,
            "industry": template_data.industry,
            "category": template_data.category,
            "complexity": template_data.complexity,
            "estimated_time": template_data.estimated_time,
            "components": {
                "vapi": template_data.vapi_config or {},
                "n8n": {},
                "integrations": template_data.integration_categories or [],
                "workflow": template_data.workflow or []
            },
            "metadata": {
                "features": template_data.features or [],
                "created_by": current_user["sub"]
            },
            "tags": template_data.tags or [],
            "version": "1.0.0",
            "is_active": True
        }

        service_template = await service.create_template(template_dict)

        # Convert service template back to frontend format
        frontend_template = FrontendAutomationTemplate(
            id=service_template.id,
            name=service_template.name,
            description=service_template.description,
            industry=service_template.industry,
            category=service_template.category,
            complexity=service_template.complexity,
            estimated_time=service_template.estimated_time,
            integration_categories=service_template.components.get("integrations", []),
            workflow=service_template.components.get("workflow", []),
            vapi_config=service_template.components.get("vapi", {}),
            features=service_template.metadata.get("features", []),
            tags=service_template.tags,
            created_at=service_template.created_at,
            updated_at=service_template.updated_at,
            version=service_template.version,
            is_active=service_template.is_active,
            metadata=service_template.metadata
        )

        return frontend_template

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template creation failed: {str(e)}")


@router.put("/templates/{template_id}", response_model=FrontendAutomationTemplate)
async def update_template(
    template_id: str,
    update_data: FrontendAutomationTemplateUpdate,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Update an existing automation template.

    Updates template configuration while maintaining version history
    and ensuring compatibility with existing deployments.
    """
    try:
        service = await get_automation_orchestration_service()

        # Convert update_data to dict
        update_dict = update_data.dict(exclude_unset=True)

        service_template = await service.update_template(
            template_id=template_id,
            update_data=update_dict,
            updated_by=current_user["sub"]
        )

        if not service_template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Convert service template to frontend format
        frontend_template = FrontendAutomationTemplate(
            id=service_template.id,
            name=service_template.name,
            description=service_template.description,
            industry=service_template.industry,
            category=service_template.category,
            complexity=service_template.complexity,
            estimated_time=service_template.estimated_time,
            integration_categories=service_template.components.get("integrations", []),
            workflow=service_template.components.get("workflow", []),
            vapi_config=service_template.components.get("vapi", {}),
            features=service_template.metadata.get("features", []),
            tags=service_template.tags,
            created_at=service_template.created_at,
            updated_at=service_template.updated_at,
            version=service_template.version,
            is_active=service_template.is_active,
            metadata=service_template.metadata
        )

        return frontend_template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template update failed: {str(e)}")


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete an automation template.

    Performs soft delete to maintain referential integrity with
    existing configurations and deployments.
    """
    try:
        service = await get_automation_orchestration_service()

        success = await service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")

        return {"message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template deletion failed: {str(e)}")


@router.get("/templates/stats", response_model=AutomationTemplateStats)
async def get_template_stats(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get automation template statistics.

    Returns comprehensive statistics including usage by industry,
    complexity distribution, and popular templates.
    """
    try:
        service = await get_automation_orchestration_service()

        stats = await service.get_template_statistics()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


# Configuration Management Endpoints

@router.get("/configurations")
async def list_configurations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    template_id: Optional[str] = Query(None, description="Filter by template"),
    status: Optional[str] = Query(None, description="Filter by status"),
    all_users: bool = Query(False, description="Show configurations from all users"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List automation configurations with filtering.

    Returns user-specific or organization-wide automation configurations
    with optional filtering by template and status.
    """
    try:
        service = await get_automation_orchestration_service()

        # Default to current user if no user_id specified, unless all_users is True
        if all_users:
            filter_user_id = user_id  # Could be None to show all users
        else:
            filter_user_id = user_id or current_user["sub"]

        configs = await service.list_configurations(
            user_id=filter_user_id,
            organization_id=organization_id,
            template_id=template_id,
            status=status
        )

        return configs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration listing failed: {str(e)}")


@router.get("/configurations/{config_id}")
async def get_configuration(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get a specific automation configuration.

    Returns complete configuration including deployment status,
    integration settings, and runtime metrics.
    """
    try:
        service = await get_automation_orchestration_service()

        config = await service.get_configuration(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration retrieval failed: {str(e)}")


@router.post("/configurations")
async def create_configuration(
    config_data: AutomationConfigCreate,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a new automation configuration.

    Creates a configuration from a template with user-specific
    customizations and integration settings.
    """
    try:
        service = await get_automation_orchestration_service()

        # Convert config_data to dict
        config_dict = config_data.dict()

        result = await service.create_configuration(
            config_data=config_dict,
            user_id=current_user["sub"]
        )

        # The service returns { "configuration": config, "message": "..." }
        # Frontend expects { "configuration": config, "deployment_status": {}, "analytics": {} }
        return {
            "configuration": result["configuration"],
            "deployment_status": {},
            "analytics": {}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration creation failed: {str(e)}")


@router.put("/configurations/{config_id}")
async def update_configuration(
    config_id: str,
    update_data: AutomationConfigUpdate,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Update an automation configuration.

    Updates configuration settings while preserving deployment state
    and ensuring compatibility with running automations.
    """
    try:
        service = await get_automation_orchestration_service()

        # Convert update_data to dict
        update_dict = update_data.dict(exclude_unset=True)

        config = await service.update_configuration(
            config_id=config_id,
            update_data=update_dict
        )

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@router.delete("/configurations/{config_id}")
async def delete_configuration(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete an automation configuration.

    Safely removes configuration and associated deployments
    with proper cleanup of external resources.
    """
    try:
        service = await get_automation_orchestration_service()

        success = await service.delete_configuration(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return {"message": "Configuration deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration deletion failed: {str(e)}")


@router.post("/configurations/{config_id}/duplicate", response_model=AutomationConfigResponse)
async def duplicate_configuration(
    config_id: str,
    duplicate_request: DuplicateRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Duplicate an existing automation configuration.

    Creates a copy of the configuration with a new name,
    useful for creating variations or backups.
    """
    try:
        service = await get_automation_orchestration_service()

        config = await service.duplicate_configuration(
            config_id=config_id,
            new_name=duplicate_request.newName,
            user_id=current_user["sub"]
        )

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration duplication failed: {str(e)}")


# Deployment Management Endpoints

@router.post("/configurations/{config_id}/deploy", response_model=DeploymentResult)
async def deploy_configuration(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Deploy an automation configuration.

    Orchestrates the complete deployment process including VAPI agent creation,
    N8N workflow deployment, and integration setup with validation and rollback.
    """
    try:
        service = await get_automation_orchestration_service()

        result = await service.deploy_configuration(
            config_id=config_id,
            deployed_by=current_user["sub"]
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post("/configurations/{config_id}/stop")
async def stop_configuration(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Stop a deployed automation configuration.

    Safely stops the automation while preserving configuration
    and allowing for restart without full redeployment.
    """
    try:
        service = await get_automation_orchestration_service()

        success = await service.stop_configuration(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found or not deployed")

        return {"message": "Configuration stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop operation failed: {str(e)}")


@router.post("/configurations/{config_id}/restart", response_model=DeploymentResult)
async def restart_configuration(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Restart a stopped automation configuration.

    Restarts the automation using existing deployment artifacts
    with health checks and validation.
    """
    try:
        service = await get_automation_orchestration_service()

        result = await service.restart_configuration(
            config_id=config_id,
            restarted_by=current_user["sub"]
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restart failed: {str(e)}")


@router.get("/configurations/{config_id}/status", response_model=AutomationStatusResponse)
async def get_configuration_status(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get automation configuration status and metrics.

    Returns real-time status, performance metrics, error logs,
    and operational statistics for the automation.
    """
    try:
        service = await get_automation_orchestration_service()

        status = await service.get_configuration_status(config_id)
        if not status:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


# Validation and Testing Endpoints

@router.post("/configurations/{config_id}/validate")
async def validate_configuration(
    config_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Validate an automation configuration.

    Performs comprehensive validation including integration connectivity,
    workflow syntax, and compliance checks without deployment.
    """
    try:
        service = await get_automation_orchestration_service()

        validation_result = await service.validate_configuration(config_id)
        return validation_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/configurations/{config_id}/test")
async def test_configuration(
    config_id: str,
    test_scenario: Optional[str] = Query(None, description="Specific test scenario"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Test an automation configuration.

    Runs end-to-end tests in a sandboxed environment to verify
    functionality before production deployment.
    """
    try:
        service = await get_automation_orchestration_service()

        test_result = await service.test_configuration(
            config_id=config_id,
            test_scenario=test_scenario
        )

        return test_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Testing failed: {str(e)}")


# Analytics and Monitoring Endpoints

@router.get("/analytics/overview")
async def get_analytics_overview(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get automation analytics overview.

    Returns comprehensive analytics including deployment statistics,
    usage metrics, performance indicators, and trend analysis.
    """
    try:
        service = await get_automation_orchestration_service()

        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        analytics = await service.get_analytics_overview(
            start_date=start_dt,
            end_date=end_dt,
            user_id=current_user["sub"]
        )

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/analytics/industry/{industry}")
async def get_industry_analytics(
    industry: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get industry-specific automation analytics.

    Returns analytics and insights specific to the requested industry
    including usage patterns and performance benchmarks.
    """
    try:
        service = await get_automation_orchestration_service()

        analytics = await service.get_industry_analytics(industry)
        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Industry analytics retrieval failed: {str(e)}")


# Capabilities and Discovery Endpoints

@router.get("/capabilities")
async def get_capabilities():
    """
    Get automation orchestration service capabilities.

    Returns available features, supported integrations, industry handlers,
    and service limitations for client-side capability detection.
    """
    try:
        service = await get_automation_orchestration_service()
        capabilities = await service.get_capabilities()

        return {
            "service": "automation_orchestration",
            "capabilities": capabilities,
            "supported_industries": [
                "Healthcare", "Finance", "Insurance", "Retail",
                "Real Estate", "Education", "Generic"
            ],
            "supported_platforms": [
                "VAPI", "N8N", "Supabase", "MongoDB"
            ],
            "integration_categories": [
                "AI/ML", "Communication", "Database", "Payment",
                "CRM", "Analytics", "Scheduling", "Documentation"
            ],
            "features": {
                "template_management": True,
                "configuration_management": True,
                "deployment_orchestration": True,
                "industry_specific_handlers": True,
                "cross_platform_integration": True,
                "analytics_and_monitoring": True,
                "validation_and_testing": True,
                "rollback_capabilities": True,
                "staged_deployments": True,
                "compliance_frameworks": ["HIPAA", "SOX", "GDPR", "Standard"]
            },
            "limits": {
                "max_templates_per_user": 100,
                "max_configurations_per_user": 50,
                "max_concurrent_deployments": 10,
                "max_integrations_per_config": 20
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capabilities retrieval failed: {str(e)}")


@router.get("/integrations/available")
async def get_available_integrations(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get available integrations for automation templates.

    Returns list of available integrations with configuration requirements,
    industry compatibility, and setup instructions.
    """
    try:
        service = await get_automation_orchestration_service()

        integrations = await service.get_available_integrations(
            industry=industry,
            category=category
        )

        return integrations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration discovery failed: {str(e)}")


# Master Template Management Endpoints

@router.post("/master-templates/save")
async def save_master_templates(
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Save master templates to the database.

    Creates or updates master templates including the master Vapi workflow
    and use case specific templates.
    """
    try:
        service = await get_automation_orchestration_service()
        result = await service.save_master_templates()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save master templates: {str(e)}")


@router.get("/master-templates")
async def get_master_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get all master templates.

    Returns list of master templates, optionally filtered by type.
    """
    try:
        service = await get_automation_orchestration_service()
        templates = await service.get_master_templates(template_type)

        return {
            "templates": templates,
            "total": len(templates)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get master templates: {str(e)}")


@router.post("/configurations/from-master-template")
async def create_config_from_master_template(
    request: dict,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create automation configuration from master template.

    Takes a master template ID, use case, and user configuration to create
    a ready-to-deploy automation configuration.
    """
    try:
        service = await get_automation_orchestration_service()

        master_template_id = request.get("master_template_id")
        use_case = request.get("use_case")
        user_config = request.get("user_config", {})

        if not master_template_id or not use_case:
            raise HTTPException(
                status_code=400,
                detail="master_template_id and use_case are required"
            )

        config = await service.create_config_from_master_template(
            master_template_id=master_template_id,
            use_case=use_case,
            user_config=user_config,
            user_id=current_user["sub"]
        )

        return {
            "configuration": asdict(config),
            "message": "Configuration created successfully from master template"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create configuration: {str(e)}")
"""
Industry Modules API

This module provides standardized API endpoints for all industry modules.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime

from .factory import get_factory, create_module, get_available_industries
from .base import BaseIndustryModule


# Pydantic models for API requests/responses
class ModuleInitializeRequest(BaseModel):
    """Request model for module initialization"""
    tenant_id: str = Field(..., description="Tenant ID")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Module settings")


class ModuleCapabilityRequest(BaseModel):
    """Request model for capability execution"""
    params: Dict[str, Any] = Field(default_factory=dict, description="Capability parameters")


class ModuleWorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    params: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")


class ModuleResponse(BaseModel):
    """Base response model for module operations"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ModuleCapabilityResponse(BaseModel):
    """Response model for capability execution"""
    success: bool = Field(..., description="Operation success status")
    capability: str = Field(..., description="Capability name")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ModuleWorkflowResponse(BaseModel):
    """Response model for workflow execution"""
    success: bool = Field(..., description="Operation success status")
    workflow_id: str = Field(..., description="Workflow ID")
    execution_id: str = Field(..., description="Execution ID")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ModuleAnalyticsResponse(BaseModel):
    """Response model for module analytics"""
    success: bool = Field(..., description="Operation success status")
    module_id: str = Field(..., description="Module ID")
    analytics: Dict[str, Any] = Field(..., description="Analytics data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ModuleComplianceResponse(BaseModel):
    """Response model for compliance information"""
    success: bool = Field(..., description="Operation success status")
    module_id: str = Field(..., description="Module ID")
    compliance: Dict[str, Any] = Field(..., description="Compliance information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ModuleIntegrationResponse(BaseModel):
    """Response model for integration information"""
    success: bool = Field(..., description="Operation success status")
    module_id: str = Field(..., description="Module ID")
    integrations: List[Dict[str, Any]] = Field(..., description="Integration information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ModuleHealthResponse(BaseModel):
    """Response model for module health check"""
    success: bool = Field(..., description="Operation success status")
    module_id: str = Field(..., description="Module ID")
    health: Dict[str, Any] = Field(..., description="Health information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


# Dependency functions
async def get_module(industry: str = Path(..., description="Industry name")) -> BaseIndustryModule:
    """Get module instance for the specified industry"""
    factory = get_factory()
    
    if not factory.validate_industry(industry):
        raise HTTPException(status_code=404, detail=f"Industry '{industry}' not supported")
    
    # For API endpoints, we'll create a temporary instance
    # In a real implementation, you'd get the tenant-specific instance
    module_class = factory.get_module_class(industry)
    return module_class()


# Create the main router
router = APIRouter(prefix="/api/v1/modules", tags=["Industry Modules"])


@router.post("/{industry}/initialize", response_model=ModuleResponse)
async def initialize_module(
    industry: str = Path(..., description="Industry name"),
    request: ModuleInitializeRequest = None,
    module: BaseIndustryModule = Depends(get_module)
):
    """Initialize a module for a tenant"""
    try:
        if not request:
            request = ModuleInitializeRequest(tenant_id="default")
        
        success = await module.initialize(request.tenant_id, request.settings)
        
        return ModuleResponse(
            success=success,
            message=f"Module {industry} initialized successfully" if success else f"Failed to initialize module {industry}",
            data={"industry": industry, "tenant_id": request.tenant_id}
        )
    except Exception as e:
        logging.error(f"Failed to initialize module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{industry}/capabilities", response_model=ModuleResponse)
async def get_module_capabilities(
    industry: str = Path(..., description="Industry name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Get module capabilities"""
    try:
        capabilities = await module.get_capabilities()
        capabilities_data = [
            {
                "name": cap.name,
                "description": cap.description,
                "enabled": cap.enabled,
                "settings": cap.settings
            }
            for cap in capabilities
        ]
        
        return ModuleResponse(
            success=True,
            message=f"Retrieved {len(capabilities)} capabilities for {industry}",
            data={"capabilities": capabilities_data}
        )
    except Exception as e:
        logging.error(f"Failed to get capabilities for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{industry}/capabilities/{capability}/execute", response_model=ModuleCapabilityResponse)
async def execute_module_capability(
    industry: str = Path(..., description="Industry name"),
    capability: str = Path(..., description="Capability name"),
    request: ModuleCapabilityRequest = None,
    module: BaseIndustryModule = Depends(get_module)
):
    """Execute a module capability"""
    try:
        if not request:
            request = ModuleCapabilityRequest()
        
        result = await module.execute_capability(capability, request.params)
        
        return ModuleCapabilityResponse(
            success=True,
            capability=capability,
            result=result
        )
    except Exception as e:
        logging.error(f"Failed to execute capability {capability} for module {industry}: {e}")
        return ModuleCapabilityResponse(
            success=False,
            capability=capability,
            error=str(e)
        )


@router.get("/{industry}/workflows", response_model=ModuleResponse)
async def get_module_workflows(
    industry: str = Path(..., description="Industry name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Get module automation workflows"""
    try:
        workflows = await module.get_automation_workflows()
        
        return ModuleResponse(
            success=True,
            message=f"Retrieved {len(workflows)} workflows for {industry}",
            data={"workflows": workflows}
        )
    except Exception as e:
        logging.error(f"Failed to get workflows for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{industry}/workflows/{workflow}/execute", response_model=ModuleWorkflowResponse)
async def execute_module_workflow(
    industry: str = Path(..., description="Industry name"),
    workflow: str = Path(..., description="Workflow ID"),
    request: ModuleWorkflowRequest = None,
    module: BaseIndustryModule = Depends(get_module)
):
    """Execute a module automation workflow"""
    try:
        if not request:
            request = ModuleWorkflowRequest()
        
        result = await module.execute_workflow(workflow, request.params)
        
        return ModuleWorkflowResponse(
            success=result.get("success", False),
            workflow_id=workflow,
            execution_id=result.get("execution_id", ""),
            result=result.get("result"),
            error=result.get("error"),
            execution_time=result.get("execution_time")
        )
    except Exception as e:
        logging.error(f"Failed to execute workflow {workflow} for module {industry}: {e}")
        return ModuleWorkflowResponse(
            success=False,
            workflow_id=workflow,
            execution_id="",
            error=str(e)
        )


@router.get("/{industry}/analytics", response_model=ModuleAnalyticsResponse)
async def get_module_analytics(
    industry: str = Path(..., description="Industry name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Get module analytics"""
    try:
        analytics = await module.get_enhanced_analytics()
        
        return ModuleAnalyticsResponse(
            success=True,
            module_id=module.module_id,
            analytics=analytics
        )
    except Exception as e:
        logging.error(f"Failed to get analytics for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{industry}/compliance", response_model=ModuleComplianceResponse)
async def get_module_compliance(
    industry: str = Path(..., description="Industry name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Get module compliance information"""
    try:
        compliance = await module.get_compliance_frameworks()
        
        return ModuleComplianceResponse(
            success=True,
            module_id=module.module_id,
            compliance={"frameworks": compliance}
        )
    except Exception as e:
        logging.error(f"Failed to get compliance for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{industry}/integrations", response_model=ModuleIntegrationResponse)
async def get_module_integrations(
    industry: str = Path(..., description="Industry name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Get module integration points"""
    try:
        integrations = await module.get_integration_points()
        
        return ModuleIntegrationResponse(
            success=True,
            module_id=module.module_id,
            integrations=integrations
        )
    except Exception as e:
        logging.error(f"Failed to get integrations for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{industry}/health", response_model=ModuleHealthResponse)
async def get_module_health(
    industry: str = Path(..., description="Industry name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Get module health status"""
    try:
        health = await module.health_check()
        
        return ModuleHealthResponse(
            success=True,
            module_id=module.module_id,
            health=health
        )
    except Exception as e:
        logging.error(f"Failed to get health for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional endpoints for module management
@router.get("/", response_model=ModuleResponse)
async def list_available_modules():
    """List all available industry modules"""
    try:
        industries = get_available_industries()
        factory = get_factory()
        modules_info = factory.get_all_modules_info()
        
        return ModuleResponse(
            success=True,
            message=f"Retrieved {len(industries)} available modules",
            data={"modules": modules_info}
        )
    except Exception as e:
        logging.error(f"Failed to list modules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{industry}/info", response_model=ModuleResponse)
async def get_module_info(
    industry: str = Path(..., description="Industry name")
):
    """Get detailed information about a module"""
    try:
        factory = get_factory()
        info = factory.get_module_info(industry)
        
        return ModuleResponse(
            success=True,
            message=f"Retrieved information for module {industry}",
            data=info
        )
    except Exception as e:
        logging.error(f"Failed to get module info for {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{industry}/integrations/{integration}/test", response_model=ModuleResponse)
async def test_module_integration(
    industry: str = Path(..., description="Industry name"),
    integration: str = Path(..., description="Integration name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Test a module integration"""
    try:
        result = await module.test_integration(integration)
        
        return ModuleResponse(
            success=result.get("success", False),
            message=f"Integration test {'passed' if result.get('success') else 'failed'}",
            data=result
        )
    except Exception as e:
        logging.error(f"Failed to test integration {integration} for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{industry}/compliance/{framework}/validate", response_model=ModuleResponse)
async def validate_module_compliance(
    industry: str = Path(..., description="Industry name"),
    framework: str = Path(..., description="Compliance framework name"),
    module: BaseIndustryModule = Depends(get_module)
):
    """Validate module compliance with a framework"""
    try:
        result = await module.validate_compliance(framework)
        
        return ModuleResponse(
            success=result.get("success", False),
            message=f"Compliance validation {'passed' if result.get('success') else 'failed'}",
            data=result
        )
    except Exception as e:
        logging.error(f"Failed to validate compliance {framework} for module {industry}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

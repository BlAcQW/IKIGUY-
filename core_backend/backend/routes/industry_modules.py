"""
Industry Module API endpoints for Core Backend.

This module provides REST API endpoints for managing industry-specific modules
and their capabilities, workflows, and analytics.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import logging

from ..services.industry_modules import IndustryModuleService
from ..auth import get_current_tenant_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/modules", tags=["Industry Modules"])


class ModuleInitializeRequest(BaseModel):
    """Request model for module initialization."""
    settings: Dict[str, Any]
    tenant_config: Optional[Dict[str, Any]] = None


class CapabilityExecuteRequest(BaseModel):
    """Request model for capability execution."""
    params: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class WorkflowExecuteRequest(BaseModel):
    """Request model for workflow execution."""
    params: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class AnalyticsRequest(BaseModel):
    """Request model for analytics data."""
    metrics: List[str]
    time_range: str
    filters: Optional[Dict[str, Any]] = None


@router.post("/{industry}/initialize")
async def initialize_module(
    industry: str,
    request: ModuleInitializeRequest,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Initialize an industry module for a tenant.
    
    Args:
        industry: Industry type (e.g., 'education', 'healthcare', 'real_estate')
        request: Initialization request with settings
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing initialization status and module info
    """
    try:
        service = IndustryModuleService()
        result = await service.initialize_module(
            tenant_id=tenant_id,
            industry=industry,
            settings=request.settings
        )
        return {
            "success": True,
            "module_id": f"{industry}_{tenant_id}",
            "status": "initialized",
            "capabilities": result.get("capabilities", []),
            "workflows": result.get("workflows", [])
        }
    except Exception as e:
        logger.error(f"Failed to initialize {industry} module for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize module: {str(e)}")


@router.get("/{industry}/capabilities")
async def get_module_capabilities(
    industry: str,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Get available capabilities for an industry module.
    
    Args:
        industry: Industry type
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing available capabilities
    """
    try:
        service = IndustryModuleService()
        capabilities = await service.get_module_capabilities(
            tenant_id=tenant_id,
            industry=industry
        )
        return {
            "success": True,
            "industry": industry,
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Failed to get capabilities for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.post("/{industry}/capabilities/{capability}/execute")
async def execute_module_capability(
    industry: str,
    capability: str,
    request: CapabilityExecuteRequest,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Execute a specific capability of an industry module.
    
    Args:
        industry: Industry type
        capability: Capability name to execute
        request: Execution parameters
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing execution results
    """
    try:
        service = IndustryModuleService()
        result = await service.execute_capability(
            tenant_id=tenant_id,
            industry=industry,
            capability=capability,
            params=request.params
        )
        return {
            "success": True,
            "industry": industry,
            "capability": capability,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to execute capability {capability} for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute capability: {str(e)}")


@router.get("/{industry}/workflows")
async def get_module_workflows(
    industry: str,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Get available workflows for an industry module.
    
    Args:
        industry: Industry type
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing available workflows
    """
    try:
        service = IndustryModuleService()
        workflows = await service.get_module_workflows(
            tenant_id=tenant_id,
            industry=industry
        )
        return {
            "success": True,
            "industry": industry,
            "workflows": workflows
        }
    except Exception as e:
        logger.error(f"Failed to get workflows for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


@router.post("/{industry}/workflows/{workflow}/execute")
async def execute_module_workflow(
    industry: str,
    workflow: str,
    request: WorkflowExecuteRequest,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Execute a specific workflow of an industry module.
    
    Args:
        industry: Industry type
        workflow: Workflow name to execute
        request: Execution parameters
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing workflow execution results
    """
    try:
        service = IndustryModuleService()
        result = await service.execute_workflow(
            tenant_id=tenant_id,
            industry=industry,
            workflow=workflow,
            params=request.params
        )
        return {
            "success": True,
            "industry": industry,
            "workflow": workflow,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow} for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/{industry}/analytics")
async def get_module_analytics(
    industry: str,
    metrics: List[str] = Query(...),
    time_range: str = Query("7d"),
    filters: Optional[str] = Query(None),
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Get analytics data for an industry module.
    
    Args:
        industry: Industry type
        metrics: List of metrics to retrieve
        time_range: Time range for analytics (e.g., "7d", "30d", "1y")
        filters: Optional filters as JSON string
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing analytics data
    """
    try:
        import json
        filters_dict = json.loads(filters) if filters else {}
        
        service = IndustryModuleService()
        analytics = await service.get_module_analytics(
            tenant_id=tenant_id,
            industry=industry,
            metrics=metrics,
            time_range=time_range,
            filters=filters_dict
        )
        return {
            "success": True,
            "industry": industry,
            "analytics": analytics
        }
    except Exception as e:
        logger.error(f"Failed to get analytics for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/{industry}/compliance")
async def get_module_compliance(
    industry: str,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Get compliance information for an industry module.
    
    Args:
        industry: Industry type
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing compliance information
    """
    try:
        service = IndustryModuleService()
        compliance = await service.get_module_compliance(
            tenant_id=tenant_id,
            industry=industry
        )
        return {
            "success": True,
            "industry": industry,
            "compliance": compliance
        }
    except Exception as e:
        logger.error(f"Failed to get compliance for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance: {str(e)}")


@router.get("/{industry}/integrations")
async def get_module_integrations(
    industry: str,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Get integration points for an industry module.
    
    Args:
        industry: Industry type
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing integration points
    """
    try:
        service = IndustryModuleService()
        integrations = await service.get_module_integrations(
            tenant_id=tenant_id,
            industry=industry
        )
        return {
            "success": True,
            "industry": industry,
            "integrations": integrations
        }
    except Exception as e:
        logger.error(f"Failed to get integrations for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get integrations: {str(e)}")


@router.get("/{industry}/health")
async def get_module_health(
    industry: str,
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Get health status for an industry module.
    
    Args:
        industry: Industry type
        tenant_id: Current tenant ID
        
    Returns:
        Dict containing health status
    """
    try:
        service = IndustryModuleService()
        health = await service.get_module_health(
            tenant_id=tenant_id,
            industry=industry
        )
        return {
            "success": True,
            "industry": industry,
            "health": health
        }
    except Exception as e:
        logger.error(f"Failed to get health for {industry} module: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health: {str(e)}")


@router.get("/available")
async def get_available_industries() -> Dict[str, Any]:
    """
    Get list of available industry modules.
    
    Returns:
        Dict containing available industries
    """
    try:
        service = IndustryModuleService()
        industries = await service.get_available_industries()
        return {
            "success": True,
            "industries": industries
        }
    except Exception as e:
        logger.error(f"Failed to get available industries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available industries: {str(e)}")

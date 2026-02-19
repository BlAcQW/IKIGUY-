"""
Deployment Tracking API Routes

API endpoints for tracking automation deployments, VAPI agents, N8N workflows,
and managing the automation templates industry field migration.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from ..auth import get_current_user_mongo
from ..services.automation_deployment_tracking_service import (
    AutomationDeploymentTrackingService,
    ComponentType,
    DeploymentStatus
)


router = APIRouter(prefix="/deployment-tracking", tags=["deployment_tracking"])

# Initialize tracking service
tracking_service = AutomationDeploymentTrackingService()


class ComponentRegistrationRequest(BaseModel):
    """Request model for registering a deployed component."""
    automation_id: str
    component_type: str  # Will be validated against ComponentType enum
    component_config: Dict[str, Any]
    deployment_info: Dict[str, Any]
    tenant_id: str


class ComponentStatusUpdate(BaseModel):
    """Request model for updating component status."""
    status: str  # Will be validated against DeploymentStatus enum
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/automations/{automation_id}/status")
async def get_automation_deployment_status(
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get comprehensive deployment status for an automation.

    Returns detailed information about:
    - Overall deployment status
    - Individual component statuses
    - Deployment metrics and history
    - Recent activity logs
    """
    try:
        status = await tracking_service.get_automation_deployment_status(automation_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting deployment status: {str(e)}")


@router.post("/components/register")
async def register_deployed_component(
    registration: ComponentRegistrationRequest,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Register a successfully deployed automation component.

    This endpoint should be called after a component (VAPI agent, N8N workflow,
    integration, or custom tool) has been successfully deployed.
    """
    try:
        # Validate component type
        try:
            component_type = ComponentType(registration.component_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid component type. Must be one of: {[t.value for t in ComponentType]}"
            )

        result = await tracking_service.register_deployed_component(
            automation_id=registration.automation_id,
            component_type=component_type,
            component_config=registration.component_config,
            deployment_info=registration.deployment_info,
            tenant_id=registration.tenant_id
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "message": "Component registered successfully",
            "component_id": result["component_id"],
            "status": result["status"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering component: {str(e)}")


@router.put("/components/{component_id}/status")
async def update_component_status(
    component_id: str,
    status_update: ComponentStatusUpdate,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Update the deployment status of a component.

    Use this endpoint to update component status when:
    - Component fails after deployment
    - Component is stopped or restarted
    - Component status changes during operation
    """
    try:
        # Validate status
        try:
            status = DeploymentStatus(status_update.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in DeploymentStatus]}"
            )

        result = await tracking_service.update_component_status(
            component_id=component_id,
            status=status,
            error_message=status_update.error_message,
            metadata=status_update.metadata
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "message": "Component status updated successfully",
            "component_id": component_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating component status: {str(e)}")


@router.get("/vapi-agents")
async def get_vapi_agent_deployments(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get all deployed VAPI agents with their current status.

    Returns comprehensive information about all VAPI agents including:
    - Assistant IDs and phone number assignments
    - Deployment status and health
    - Associated automation details
    """
    try:
        deployments = await tracking_service.get_vapi_agent_deployments(tenant_id)
        return {
            "vapi_agents": deployments,
            "total_count": len(deployments),
            "tenant_filter": tenant_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting VAPI deployments: {str(e)}")


@router.get("/n8n-workflows")
async def get_n8n_workflow_deployments(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get all deployed N8N workflows with their current status.

    Returns comprehensive information about all N8N workflows including:
    - Workflow IDs and webhook URLs
    - Deployment status and health
    - Associated automation details
    """
    try:
        deployments = await tracking_service.get_n8n_workflow_deployments(tenant_id)
        return {
            "n8n_workflows": deployments,
            "total_count": len(deployments),
            "tenant_filter": tenant_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting N8N deployments: {str(e)}")


@router.get("/tenants/{tenant_id}/summary")
async def get_tenant_deployment_summary(
    tenant_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get deployment summary for a specific tenant.

    Provides overview of all automations and components for a tenant including:
    - Total and deployed automation counts
    - Component breakdown by type
    - Success rates and statistics
    - Recent deployment activity
    """
    try:
        summary = await tracking_service.get_tenant_deployment_summary(tenant_id)
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting tenant summary: {str(e)}")


@router.post("/automations/{automation_id}/stop")
async def stop_automation_deployment(
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Stop a deployed automation and all its components.

    This will:
    - Set automation status to 'stopped'
    - Stop all deployed components
    - Log the stop activity
    """
    try:
        user_id = current_user.get("user_id", "unknown")
        result = await tracking_service.stop_automation_deployment(
            automation_id=automation_id,
            stopped_by=user_id
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "message": "Automation stopped successfully",
            "automation_id": automation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping automation: {str(e)}")


@router.post("/automations/{automation_id}/restart")
async def restart_automation_deployment(
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Restart a stopped automation deployment.

    This will:
    - Set automation status to 'deployed'
    - Restart all stopped components
    - Log the restart activity
    """
    try:
        user_id = current_user.get("user_id", "unknown")
        result = await tracking_service.restart_automation_deployment(
            automation_id=automation_id,
            restarted_by=user_id
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "message": "Automation restarted successfully",
            "automation_id": automation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restarting automation: {str(e)}")


@router.post("/migrations/automation-templates-industry")
async def migrate_automation_templates_industry(
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Migrate automation_templates collection to use industry_id and industry_name fields.

    This migration:
    1. Examines the current 'industry' field
    2. Creates separate 'industry_id' and 'industry_name' fields
    3. Removes the old 'industry' field

    Note: This is a one-time migration that can be run safely multiple times.
    """
    try:
        from ..migrations.fix_automation_templates_industry import migrate_automation_templates_industry

        result = await migrate_automation_templates_industry()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.get("/migrations/automation-templates-industry/verify")
async def verify_automation_templates_migration(
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Verify the automation templates industry field migration.

    Returns:
    - Migration status and statistics
    - Industry distribution after migration
    - Any templates that still need migration
    """
    try:
        from ..migrations.fix_automation_templates_industry import verify_migration

        result = await verify_migration()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/dashboard")
async def get_deployment_dashboard(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get comprehensive deployment dashboard data.

    Returns aggregated deployment information suitable for dashboard display,
    including deployment statistics, component health, and recent activity.
    """
    try:
        # Get deployment statistics
        if tenant_id:
            summary = await tracking_service.get_tenant_deployment_summary(tenant_id)
            vapi_agents = await tracking_service.get_vapi_agent_deployments(tenant_id)
            n8n_workflows = await tracking_service.get_n8n_workflow_deployments(tenant_id)
        else:
            # Get all deployments (you might want to limit this for performance)
            vapi_agents = await tracking_service.get_vapi_agent_deployments()
            n8n_workflows = await tracking_service.get_n8n_workflow_deployments()
            summary = {
                "summary": {
                    "total_components": len(vapi_agents) + len(n8n_workflows),
                    "active_components": len([a for a in vapi_agents if a["status"] == "deployed"]) +
                                       len([w for w in n8n_workflows if w["status"] == "deployed"])
                }
            }

        # Calculate overall statistics
        total_vapi = len(vapi_agents)
        active_vapi = len([a for a in vapi_agents if a["status"] == "deployed"])
        total_n8n = len(n8n_workflows)
        active_n8n = len([w for w in n8n_workflows if w["status"] == "deployed"])

        dashboard_data = {
            "overview": {
                "total_automations": summary.get("summary", {}).get("total_automations", 0),
                "deployed_automations": summary.get("summary", {}).get("deployed_automations", 0),
                "total_components": total_vapi + total_n8n,
                "active_components": active_vapi + active_n8n,
                "success_rate": summary.get("summary", {}).get("success_rate", 0)
            },
            "component_breakdown": {
                "vapi_agents": {"total": total_vapi, "active": active_vapi},
                "n8n_workflows": {"total": total_n8n, "active": active_n8n}
            },
            "recent_deployments": {
                "vapi_agents": sorted(vapi_agents, key=lambda x: x.get("deployed_at") or "", reverse=True)[:5],
                "n8n_workflows": sorted(n8n_workflows, key=lambda x: x.get("deployed_at") or "", reverse=True)[:5]
            },
            "tenant_filter": tenant_id,
            "dashboard_updated_at": datetime.now()
        }

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")
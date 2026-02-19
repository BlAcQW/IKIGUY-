"""
Automation Health Monitoring API Routes

Provides endpoints for managing and monitoring automation component health.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from ..auth import get_current_user_mongo
from ..services.automation_health_service import (
    AutomationHealthService,
    ComponentType,
    HealthStatus
)

router = APIRouter(prefix="/automation-health", tags=["automation_health"])

# Initialize health service
health_service = AutomationHealthService()


class ComponentRegistration(BaseModel):
    """Request model for registering a component for health monitoring."""
    component_id: str = Field(..., description="Unique identifier for the component")
    component_type: str = Field(..., description="Type of component (vapi_agent, n8n_workflow, etc.)")
    automation_id: str = Field(..., description="ID of the automation this component belongs to")
    tenant_id: str = Field(..., description="Tenant ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Component configuration metadata")


class HealthStatusUpdate(BaseModel):
    """Request model for manually updating component health status."""
    status: str = Field(..., description="Health status (healthy, warning, critical, unknown)")
    error_message: Optional[str] = Field(None, description="Error message if status is not healthy")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


@router.post("/components/register")
async def register_component(
    registration: ComponentRegistration,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Register a component for health monitoring.

    This endpoint allows you to register automation components (VAPI agents,
    N8N workflows, integrations, custom tools) for continuous health monitoring.
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

        result = await health_service.register_component(
            component_id=registration.component_id,
            component_type=component_type,
            automation_id=registration.automation_id,
            tenant_id=registration.tenant_id,
            metadata=registration.metadata
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "message": "Component registered successfully",
            "component_id": registration.component_id,
            "monitoring_enabled": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering component: {str(e)}")


@router.get("/components/{component_id}/check")
async def trigger_health_check(
    component_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Trigger an immediate health check for a specific component.

    This endpoint performs an on-demand health check for the specified component.
    """
    try:
        health_check = await health_service.perform_health_check(component_id)

        if not health_check:
            raise HTTPException(status_code=404, detail="Component not found or health check failed")

        return {
            "component_id": component_id,
            "status": health_check.status.value,
            "response_time": health_check.response_time,
            "error_message": health_check.error_message,
            "checked_at": health_check.checked_at,
            "metadata": health_check.metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing health check: {str(e)}")


@router.get("/automations/{automation_id}/status")
async def get_automation_health(
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get overall health status for an automation and all its components.

    Returns comprehensive health information including:
    - Overall automation health status
    - Individual component statuses
    - Health score (0-100)
    - Component summary by status
    """
    try:
        health_status = await health_service.get_automation_health_status(automation_id)
        return health_status

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automation health: {str(e)}")


@router.get("/metrics")
async def get_health_metrics(
    automation_id: Optional[str] = Query(None, description="Filter by automation ID"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get health metrics and analytics for components.

    Provides historical health data and analytics including:
    - Health trends over time
    - Response time analytics
    - Status distribution
    - Current health summary
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")

        metrics = await health_service.get_health_metrics(
            automation_id=automation_id,
            tenant_id=tenant_id,
            start_date=start_dt,
            end_date=end_dt
        )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting health metrics: {str(e)}")


@router.post("/monitoring/start")
async def start_monitoring(
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Start continuous health monitoring for all registered components.

    This starts the background monitoring service that periodically checks
    the health of all registered components.
    """
    try:
        await health_service.start_monitoring()
        return {
            "message": "Health monitoring started successfully",
            "monitoring_active": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring(
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Stop continuous health monitoring.

    This stops the background monitoring service. Manual health checks
    can still be triggered via the /check endpoint.
    """
    try:
        await health_service.stop_monitoring()
        return {
            "message": "Health monitoring stopped successfully",
            "monitoring_active": False
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping monitoring: {str(e)}")


@router.put("/components/{component_id}/status")
async def update_component_status(
    component_id: str,
    status_update: HealthStatusUpdate,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Manually update the health status of a component.

    This endpoint allows manual override of component health status,
    useful for maintenance periods or when automated checks are not sufficient.
    """
    try:
        # Validate status
        try:
            health_status = HealthStatus(status_update.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in HealthStatus]}"
            )

        # Get component from database
        component = health_service.components_collection.find_one({"component_id": component_id})
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Update health status
        from ..services.automation_health_service import HealthCheck

        health_check = HealthCheck(
            component_id=component_id,
            component_type=ComponentType(component["component_type"]),
            status=health_status,
            error_message=status_update.error_message,
            metadata=status_update.metadata or {}
        )

        await health_service.store_health_check(health_check)

        # Update component record
        health_service.components_collection.update_one(
            {"component_id": component_id},
            {
                "$set": {
                    "status": health_status.value,
                    "last_checked": datetime.now(timezone.utc),
                    "last_error": status_update.error_message,
                    "manual_override": True,
                    "updated_by": current_user.get("user_id", "unknown")
                }
            }
        )

        return {
            "message": "Component status updated successfully",
            "component_id": component_id,
            "new_status": health_status.value,
            "updated_at": datetime.now(timezone.utc)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating component status: {str(e)}")


@router.get("/components")
async def list_monitored_components(
    automation_id: Optional[str] = Query(None, description="Filter by automation ID"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    component_type: Optional[str] = Query(None, description="Filter by component type"),
    status: Optional[str] = Query(None, description="Filter by health status"),
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    List all components registered for health monitoring.

    Returns a list of all monitored components with their current health status,
    optionally filtered by various criteria.
    """
    try:
        # Build query filter
        query_filter = {}

        if automation_id:
            query_filter["automation_id"] = automation_id

        if tenant_id:
            query_filter["tenant_id"] = tenant_id

        if component_type:
            # Validate component type
            try:
                ComponentType(component_type)
                query_filter["component_type"] = component_type
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid component type. Must be one of: {[t.value for t in ComponentType]}"
                )

        if status:
            # Validate status
            try:
                HealthStatus(status)
                query_filter["status"] = status
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {[s.value for s in HealthStatus]}"
                )

        # Get components
        components = list(health_service.components_collection.find(query_filter))

        # Get current health status for each component
        component_list = []
        for component in components:
            component_id = component["component_id"]
            health_doc = health_service.health_collection.find_one({"component_id": component_id})

            component_info = {
                "component_id": component_id,
                "component_type": component["component_type"],
                "automation_id": component["automation_id"],
                "tenant_id": component["tenant_id"],
                "check_enabled": component.get("check_enabled", True),
                "registered_at": component["registered_at"],
                "metadata": component.get("metadata", {})
            }

            if health_doc:
                component_info.update({
                    "status": health_doc["status"],
                    "last_checked": health_doc.get("checked_at"),
                    "response_time": health_doc.get("response_time"),
                    "error_message": health_doc.get("error_message")
                })
            else:
                component_info.update({
                    "status": "unknown",
                    "last_checked": None,
                    "response_time": None,
                    "error_message": "No health data available"
                })

            component_list.append(component_info)

        return {
            "components": component_list,
            "total_count": len(component_list),
            "filters_applied": {
                "automation_id": automation_id,
                "tenant_id": tenant_id,
                "component_type": component_type,
                "status": status
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing components: {str(e)}")


@router.delete("/components/{component_id}")
async def unregister_component(
    component_id: str,
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Unregister a component from health monitoring.

    This removes the component from the monitoring system and deletes
    its health history data.
    """
    try:
        # Check if component exists
        component = health_service.components_collection.find_one({"component_id": component_id})
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Remove component from monitoring
        health_service.components_collection.delete_one({"component_id": component_id})

        # Remove current health status
        health_service.health_collection.delete_one({"component_id": component_id})

        # Remove health history
        health_service.health_history_collection.delete_many({"component_id": component_id})

        return {
            "message": "Component unregistered successfully",
            "component_id": component_id,
            "removed_at": datetime.now(timezone.utc)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unregistering component: {str(e)}")


@router.get("/dashboard")
async def get_health_dashboard(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    current_user: dict = Depends(get_current_user_mongo)
) -> Dict[str, Any]:
    """
    Get comprehensive health dashboard data.

    Returns aggregated health information suitable for dashboard display,
    including overall statistics, recent alerts, and trend data.
    """
    try:
        # Build query filter
        query_filter = {}
        if tenant_id:
            query_filter["tenant_id"] = tenant_id

        # Get all components
        components = list(health_service.components_collection.find(query_filter))

        # Get current health statuses
        component_ids = [c["component_id"] for c in components]
        health_statuses = list(health_service.health_collection.find({
            "component_id": {"$in": component_ids}
        }))

        # Calculate summary statistics
        total_components = len(components)
        status_counts = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}

        for health in health_statuses:
            status = health.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Components without health data are unknown
        components_with_health = len(health_statuses)
        status_counts["unknown"] += (total_components - components_with_health)

        # Get recent critical/warning alerts (last 24 hours)
        recent_alerts_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_alerts = list(health_service.health_history_collection.find({
            "component_id": {"$in": component_ids},
            "status": {"$in": ["critical", "warning"]},
            "checked_at": {"$gte": recent_alerts_cutoff}
        }).sort("checked_at", -1).limit(10))

        # Get automation health summaries
        automation_healths = {}
        automations = set(c["automation_id"] for c in components)

        for automation_id in automations:
            automation_health = await health_service.get_automation_health_status(automation_id)
            automation_healths[automation_id] = {
                "overall_status": automation_health["overall_status"],
                "health_score": automation_health.get("health_score", 0),
                "total_components": automation_health.get("total_components", 0)
            }

        return {
            "summary": {
                "total_components": total_components,
                "total_automations": len(automations),
                "status_distribution": status_counts,
                "overall_health_score": health_service._calculate_health_score(status_counts)
            },
            "recent_alerts": [
                {
                    "component_id": alert["component_id"],
                    "status": alert["status"],
                    "error_message": alert.get("error_message"),
                    "checked_at": alert["checked_at"]
                }
                for alert in recent_alerts
            ],
            "automation_health": automation_healths,
            "dashboard_updated_at": datetime.now(timezone.utc)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")
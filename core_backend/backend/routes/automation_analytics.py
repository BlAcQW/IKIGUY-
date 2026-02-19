"""
Automation Analytics Routes

Provides REST API endpoints for automation analytics and metrics.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Dict, Any, Optional
from datetime import datetime

from ..auth import get_current_user_mongo
from ..services.automation_analytics_service import get_analytics_service
from apps.shared.services.billing_service import get_billing_service
from ..mongo import get_database
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation-analytics", tags=["Automation Analytics"])


@router.get("/{config_id}")
async def get_automation_analytics(
    request: Request,
    config_id: str,
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, all"),
    force_refresh: bool = Query(False, description="Force refresh from VAPI"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get comprehensive analytics for an automation configuration.

    Returns metrics, trend data, and recent calls.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting automation analytics for config_id={config_id}, organization={org_id}")

        db = get_database()
        analytics_service = await get_analytics_service(db)

        analytics = await analytics_service.get_automation_analytics(
            config_id=config_id,
            time_range=time_range,
            force_refresh=force_refresh,
            organization_id=org_id
        )

        if "error" in analytics and analytics.get("assistant_id") is None:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return {
            "success": True,
            "data": analytics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation analytics for config_id={config_id}, organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/summary")
async def get_automation_analytics_summary(
    request: Request,
    config_id: str,
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d, all"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get summary metrics for an automation configuration.

    Returns only the core metrics without detailed trend data.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting automation analytics summary for config_id={config_id}, organization={org_id}")

        db = get_database()
        analytics_service = await get_analytics_service(db)

        analytics = await analytics_service.get_automation_analytics(
            config_id=config_id,
            time_range=time_range,
            force_refresh=False,
            organization_id=org_id
        )

        if "error" in analytics and analytics.get("assistant_id") is None:
            raise HTTPException(status_code=404, detail=analytics["error"])

        # Return only summary data
        summary = {
            "automation_id": analytics.get("automation_id"),
            "automation_name": analytics.get("automation_name"),
            "assistant_id": analytics.get("assistant_id"),
            "time_range": analytics.get("time_range"),
            "metrics": analytics.get("metrics", {}),
            "last_updated": analytics.get("last_updated")
        }

        return {
            "success": True,
            "data": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation analytics summary for config_id={config_id}, organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/calls")
async def get_automation_calls(
    request: Request,
    config_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get paginated call history for an automation configuration.

    Supports filtering by call status and pagination.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting automation calls for config_id={config_id}, organization={org_id}, page={page}")

        db = get_database()
        analytics_service = await get_analytics_service(db)

        calls_data = await analytics_service.get_automation_calls(
            config_id=config_id,
            page=page,
            limit=limit,
            status_filter=status,
            organization_id=org_id
        )

        return {
            "success": True,
            "data": calls_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automation calls for config_id={config_id}, organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_id}/refresh")
async def refresh_automation_analytics(
    request: Request,
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Force refresh analytics from VAPI.

    Fetches latest call data from VAPI and updates analytics.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Refreshing automation analytics for config_id={config_id}, organization={org_id}")

        db = get_database()
        analytics_service = await get_analytics_service(db)

        # Force refresh by getting analytics with force_refresh=True
        analytics = await analytics_service.get_automation_analytics(
            config_id=config_id,
            time_range="30d",
            force_refresh=True,
            organization_id=org_id
        )

        if "error" in analytics and analytics.get("assistant_id") is None:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return {
            "success": True,
            "message": "Analytics refreshed successfully",
            "data": {
                "automation_id": analytics.get("automation_id"),
                "last_updated": analytics.get("last_updated"),
                "metrics": analytics.get("metrics", {})
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing automation analytics for config_id={config_id}, organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_id}/sync")
async def sync_automation_calls(
    request: Request,
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Sync call data from VAPI to local database.

    Fetches all calls for the automation and stores them locally.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Syncing automation calls for config_id={config_id}, organization={org_id}")

        db = get_database()
        analytics_service = await get_analytics_service(db)

        sync_result = await analytics_service.sync_automation_calls(config_id, organization_id=org_id)

        if not sync_result.get("success"):
            raise HTTPException(status_code=400, detail=sync_result.get("error"))

        return sync_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing automation calls for config_id={config_id}, organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}/health")
async def get_automation_health(
    request: Request,
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get health status for an automation's analytics components.

    Checks VAPI connection and data availability.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Checking automation health for config_id={config_id}, organization={org_id}")

        db = get_database()
        analytics_service = await get_analytics_service(db)

        # Get basic analytics to check health
        analytics = await analytics_service.get_automation_analytics(
            config_id=config_id,
            time_range="7d",
            force_refresh=False,
            organization_id=org_id
        )

        health_status = {
            "automation_id": config_id,
            "healthy": True,
            "components": {
                "vapi": {
                    "status": "healthy" if analytics.get("assistant_id") else "unavailable",
                    "assistant_id": analytics.get("assistant_id")
                },
                "analytics": {
                    "status": "healthy" if "metrics" in analytics else "degraded",
                    "last_updated": analytics.get("last_updated")
                }
            },
            "checked_at": datetime.now().isoformat()
        }

        # Mark unhealthy if no assistant or error
        if not analytics.get("assistant_id") or "error" in analytics:
            health_status["healthy"] = False
            health_status["error"] = analytics.get("error")

        return {
            "success": True,
            "data": health_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking automation health for config_id={config_id}, organization={org_id}: {e}")
        return {
            "success": False,
            "data": {
                "automation_id": config_id,
                "healthy": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }
        }


@router.post("/{config_id}/create-billing")
async def create_billing_records(
    request: Request,
    config_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Create billing records from automation calls.

    Generates billing records for all calls that don't have billing records yet.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Creating billing records for config_id={config_id}, organization={org_id}")

        db = get_database()
        billing_service = await get_billing_service(db)

        result = await billing_service.create_billing_records_for_automation(config_id, organization_id=org_id)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating billing records for config_id={config_id}, organization={org_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

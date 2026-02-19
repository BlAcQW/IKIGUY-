"""
Analytics API Routes for Automations, Campaigns, and Costs.

Provides comprehensive analytics endpoints for all automation components,
health monitoring, and cost tracking.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timedelta
import logging

from ..auth import get_current_user_mongo, get_user_from_header
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)
from ..services.analytics_service import analytics_service
from ..services.wallet_service import WalletService
from ..models.wallet import Currency
from ..mongo import get_database

# Import unified analytics service from shared
import sys
import os
sys.path.append('/opt/kasaai/apps/shared')
from integration.vapi import vapi_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../shared"))
from apps.shared.services.unified_analytics_service import UnifiedAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_analytics_overview(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_user_from_header)
):
    """
    Get comprehensive analytics overview for all automations and services.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting analytics overview for organization: {org_id}")

        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        # Get all analytics data scoped to organization
        automation_analytics = await analytics_service.get_automation_analytics(
            start_date=start_dt, end_date=end_dt, organization_id=org_id
        )
        vapi_analytics = await analytics_service.get_vapi_analytics(
            start_date=start_dt, end_date=end_dt, organization_id=org_id
        )
        n8n_analytics = await analytics_service.get_n8n_analytics(
            start_date=start_dt, end_date=end_dt, organization_id=org_id
        )
        cost_analytics = await analytics_service.get_cost_analytics(
            start_date=start_dt, end_date=end_dt, organization_id=org_id
        )

        # Get profit margin analytics (ADMIN ONLY - shows actual costs vs revenue)
        profit_analytics = await analytics_service.get_profit_margin_analytics(
            start_date=start_dt, end_date=end_dt, organization_id=org_id
        )

        return {
            "overview": {
                "period": {
                    "start_date": start_dt.isoformat() if start_dt else None,
                    "end_date": end_dt.isoformat() if end_dt else None
                },
                "automation_summary": automation_analytics.get("summary", {}),
                "vapi_summary": vapi_analytics.get("calls", {}),
                "n8n_summary": n8n_analytics.get("workflows", {}),
                "cost_summary": cost_analytics.get("cost_analytics", {}).get("summary", {}),
                "profit_summary": profit_analytics.get("profit_analytics", {}).get("summary", {}),
                "generated_at": datetime.utcnow().isoformat()
            },
            "detailed_data": {
                "automations": automation_analytics,
                "vapi": vapi_analytics,
                "n8n": n8n_analytics,
                "costs": cost_analytics,
                "profit_margins": profit_analytics
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics overview: {str(e)}")


@router.get("/automations")
async def get_automation_analytics(
    request: Request,
    automation_id: Optional[str] = Query(None, description="Specific automation ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get detailed analytics for automations.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting automation analytics for organization: {org_id}, automation: {automation_id}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        analytics = await analytics_service.get_automation_analytics(
            automation_id=automation_id,
            start_date=start_dt,
            end_date=end_dt,
            organization_id=org_id
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get automation analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation analytics: {str(e)}")


@router.get("/automations/{automation_id}/health")
async def get_automation_health(
    request: Request,
    automation_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get real-time health status for a specific automation.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting automation health for organization: {org_id}, automation: {automation_id}")

        health_status = await analytics_service.get_automation_health_status(
            automation_id, organization_id=org_id
        )
        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get automation health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation health: {str(e)}")


@router.get("/vapi")
async def get_vapi_analytics(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get VAPI call analytics and performance metrics.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting VAPI analytics for organization: {org_id}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        analytics = await analytics_service.get_vapi_analytics(
            start_date=start_dt,
            end_date=end_dt,
            organization_id=org_id
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get VAPI analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get VAPI analytics: {str(e)}")


@router.get("/n8n")
async def get_n8n_analytics(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get N8N workflow analytics and execution metrics.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting N8N analytics for organization: {org_id}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        analytics = await analytics_service.get_n8n_analytics(
            start_date=start_dt,
            end_date=end_dt,
            organization_id=org_id
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get N8N analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get N8N analytics: {str(e)}")


@router.get("/costs")
async def get_cost_analytics(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    group_by: str = Query("service", description="Group costs by: service, automation, organization"),
    current_user: dict = Depends(get_user_from_header)
):
    """
    Get comprehensive cost analytics across all services.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting cost analytics for organization: {org_id}, group_by: {group_by}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        analytics = await analytics_service.get_cost_analytics(
            start_date=start_dt,
            end_date=end_dt,
            group_by=group_by,
            organization_id=org_id
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cost analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost analytics: {str(e)}")


@router.get("/profit-margins")
async def get_profit_margin_analytics(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID (deprecated, use organization_id)"),
    provider: Optional[str] = Query(None, description="Filter by provider (vapi, twilio, etc.)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get profit margin analytics (ADMIN ONLY).

    Shows actual costs paid to providers vs. what we charged customers.
    Includes revenue, costs, profit, and margin percentages.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting profit margin analytics for organization: {org_id}, provider: {provider}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        # Use organization_id instead of deprecated tenant_id
        profit_analytics = await analytics_service.get_profit_margin_analytics(
            start_date=start_dt,
            end_date=end_dt,
            organization_id=org_id or tenant_id,  # Fallback to tenant_id for backward compatibility
            provider=provider
        )

        return profit_analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profit margin analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get profit margin analytics: {str(e)}")


@router.get("/services/{service}")
async def get_service_metrics(
    request: Request,
    service: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get metrics for a specific service (last 24 hours).

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting service metrics for organization: {org_id}, service: {service}")

        metrics = await analytics_service.get_service_metrics(service, organization_id=org_id)
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get service metrics: {str(e)}")


@router.get("/tenants/{tenant_id}")
async def get_tenant_analytics(
    request: Request,
    tenant_id: str,
    service: str = Query("all", description="Service name or 'all'"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get analytics for a specific tenant (deprecated - use organization context instead).

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting tenant analytics for organization: {org_id}, tenant: {tenant_id}, service: {service}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        # Use organization_id, fallback to tenant_id for backward compatibility
        analytics = await analytics_service.get_tenant_analytics(
            tenant_id=org_id or tenant_id,
            service=service,
            start_date=start_dt,
            end_date=end_dt
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tenant analytics: {str(e)}")


@router.post("/record")
async def record_analytics_operation(
    request: Request,
    analytics_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Record an analytics operation.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Add organization_id to analytics data
        analytics_data["organization_id"] = org_id

        logger.info(f"Recording analytics operation for organization: {org_id}")

        await analytics_service.record_operation(analytics_data)
        return {"success": True, "message": "Analytics operation recorded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record analytics operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record operation: {str(e)}")


@router.get("/health/all")
async def get_all_automation_health(
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get health status for all automations.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting all automation health for organization: {org_id}")

        from ..mongo import get_collection

        # Get all automation configs scoped to organization
        automations_collection = get_collection("automation_configs")
        query = {"organization_id": org_id} if org_id else {}
        cursor = automations_collection.find(query, {"_id": 1, "automationName": 1, "status": 1})
        automations = await cursor.to_list(length=None)

        health_statuses = []
        for automation in automations:
            automation_id = automation["_id"]
            health_status = await analytics_service.get_automation_health_status(automation_id)

            # Add basic automation info
            health_status["automation_name"] = automation.get("automationName", "Unknown")
            health_status["deployment_status"] = automation.get("status", "unknown")

            health_statuses.append(health_status)

        # Calculate overall summary
        total_automations = len(health_statuses)
        healthy_count = len([h for h in health_statuses if h.get("overall_health") == "healthy"])
        warning_count = len([h for h in health_statuses if h.get("overall_health") == "warning"])
        critical_count = len([h for h in health_statuses if h.get("overall_health") == "critical"])

        return {
            "health_overview": {
                "total_automations": total_automations,
                "healthy": healthy_count,
                "warning": warning_count,
                "critical": critical_count,
                "overall_health_percentage": (healthy_count / total_automations * 100) if total_automations > 0 else 0
            },
            "automation_health": health_statuses,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all automation health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get automation health: {str(e)}")


@router.get("/campaigns")
async def get_campaign_analytics(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get campaign analytics and performance metrics.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting campaign analytics for organization: {org_id}")

        from ..mongo import get_collection

        campaigns_collection = get_collection("campaigns")

        # Default to last 30 days if no dates provided
        if not end_date:
            end_dt = datetime.utcnow()
        else:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if not start_date:
            start_dt = end_dt - timedelta(days=30)
        else:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        # Get campaigns created in the period, scoped to organization
        query = {
            "created_at": {"$gte": start_dt, "$lte": end_dt}
        }
        if org_id:
            query["organization_id"] = org_id

        cursor = campaigns_collection.find(query)
        campaigns = await cursor.to_list(length=None)

        # Get campaign operations from analytics, scoped to organization
        operations_query = {
            "timestamp": {"$gte": start_dt, "$lte": end_dt},
            "operation": {"$regex": "campaign", "$options": "i"}
        }
        if org_id:
            operations_query["organization_id"] = org_id

        cursor = analytics_service.analytics_collection.find(operations_query)
        campaign_operations = await cursor.to_list(length=None)

        # Calculate metrics
        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.get("status") == "active"])
        total_operations = len(campaign_operations)
        successful_operations = len([op for op in campaign_operations if op.get("success")])

        return {
            "campaign_analytics": {
                "period": {
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat()
                },
                "summary": {
                    "total_campaigns": total_campaigns,
                    "active_campaigns": active_campaigns,
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0
                },
                "campaigns": campaigns,
                "recent_operations": campaign_operations[-10:] if campaign_operations else []
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get campaign analytics: {str(e)}")


@router.get("/integrations")
async def get_integration_analytics(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get analytics for all integration services.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting integration analytics for organization: {org_id}")

        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        if not end_dt:
            end_dt = datetime.utcnow()
        if not start_dt:
            start_dt = end_dt - timedelta(days=7)

        # Get integration usage from analytics scoped to organization
        match_filter = {
            "timestamp": {"$gte": start_dt, "$lte": end_dt}
        }
        if org_id:
            match_filter["organization_id"] = org_id

        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": "$service",
                "total_operations": {"$sum": 1},
                "successful_operations": {"$sum": {"$cond": ["$success", 1, 0]}},
                "total_cost": {"$sum": "$cost"},
                "avg_response_time": {"$avg": "$response_time"},
                "last_used": {"$max": "$timestamp"}
            }},
            {"$sort": {"total_operations": -1}}
        ]

        integration_stats = list(analytics_service.analytics_collection.aggregate(pipeline))

        # Calculate success rates
        for stat in integration_stats:
            stat["success_rate"] = (
                stat["successful_operations"] / stat["total_operations"] * 100
                if stat["total_operations"] > 0 else 0
            )
            stat["error_rate"] = 100 - stat["success_rate"]

        return {
            "integration_analytics": {
                "period": {
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat()
                },
                "summary": {
                    "total_integrations_used": len(integration_stats),
                    "total_operations": sum(s["total_operations"] for s in integration_stats),
                    "total_cost": sum(s["total_cost"] for s in integration_stats),
                    "overall_success_rate": (
                        sum(s["successful_operations"] for s in integration_stats) /
                        sum(s["total_operations"] for s in integration_stats) * 100
                        if any(s["total_operations"] for s in integration_stats) else 0
                    )
                },
                "integration_breakdown": integration_stats
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration analytics: {str(e)}")


@router.get("/assistants/{assistant_id}/costs")
async def get_assistant_costs(
    request: Request,
    assistant_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: dict = Depends(get_user_from_header)
):
    """
    Get comprehensive cost breakdown for a VAPI assistant across all services.

    Returns aggregated costs from:
    - VAPI call logs
    - Vonage phone calls
    - Twilio messages
    - LLM inference
    - TTS synthesis
    - ASR transcription

    All costs associated with the given assistant ID across all services.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting assistant costs for organization: {org_id}, assistant: {assistant_id}")

        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

        # Get user ID
        user_id = current_user.get("user_id") or current_user.get("sub")

        # Initialize unified analytics service
        db = get_database()
        unified_analytics = UnifiedAnalyticsService(db)

        # Get comprehensive costs scoped to organization
        costs = await unified_analytics.get_assistant_costs(
            assistant_id=assistant_id,
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id,
            organization_id=org_id
        )

        return costs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assistant costs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get assistant costs: {str(e)}")


@router.get("/dashboard-data")
async def get_dashboard_data(
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get comprehensive dashboard data for the analytics page.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting dashboard data for organization: {org_id}")

        # Get wallet balance
        db = get_database()
        wallet_service = WalletService(db)
        user_id = current_user.get("user_id") or current_user.get("id")

        wallet_balance = None
        try:
            wallet_data = await wallet_service.get_wallet_balance(user_id, Currency.USD, organization_id=org_id)
            wallet_balance = {
                "balance": wallet_data["balance"],
                "available_balance": wallet_data["available_balance"],
                "currency": wallet_data["currency"],
                "low_balance_warning": wallet_data.get("available_balance", 0) < 10.00  # Warning if below $10
            }
        except Exception as e:
            logger.warning(f"Could not fetch wallet balance: {str(e)}")

        # Get data for the last 7 days for quick dashboard overview
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        # Get all key metrics in parallel, scoped to organization
        automation_analytics = await analytics_service.get_automation_analytics(
            start_date=start_date, end_date=end_date, organization_id=org_id
        )
        vapi_analytics = await analytics_service.get_vapi_analytics(
            start_date=start_date, end_date=end_date, organization_id=org_id
        )
        n8n_analytics = await analytics_service.get_n8n_analytics(
            start_date=start_date, end_date=end_date, organization_id=org_id
        )
        cost_analytics = await analytics_service.get_cost_analytics(
            start_date=start_date, end_date=end_date, organization_id=org_id
        )

        # Get recent operations scoped to organization
        operations_query = {"timestamp": {"$gte": start_date}}
        if org_id:
            operations_query["organization_id"] = org_id

        cursor = analytics_service.analytics_collection.find(operations_query).sort([("timestamp", -1)]).limit(20)
        recent_operations = await cursor.to_list(length=20)

        # Convert ObjectId to string for JSON serialization
        for op in recent_operations:
            if "_id" in op:
                op["_id"] = str(op["_id"])

        return {
            "dashboard": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period_name": "Last 7 Days"
                },
                "wallet": wallet_balance,  # Add wallet balance to dashboard
                "summary_cards": {
                    "total_automations": len(automation_analytics.get("automation_analytics", [])),
                    "total_operations": automation_analytics.get("summary", {}).get("total_operations", 0),
                    "total_cost": automation_analytics.get("summary", {}).get("total_cost", 0),
                    "avg_success_rate": automation_analytics.get("summary", {}).get("avg_success_rate", 0),
                    "vapi_calls": vapi_analytics.get("calls", {}).get("total_calls", 0),
                    "n8n_executions": n8n_analytics.get("workflows", {}).get("total_executions", 0)
                },
                "charts_data": {
                    "automation_performance": automation_analytics.get("automation_analytics", []),
                    "cost_breakdown": cost_analytics.get("cost_analytics", {}).get("summary", {}).get("cost_by_service", []),
                    "service_usage": [
                        {"service": "VAPI", "operations": vapi_analytics.get("calls", {}).get("total_calls", 0)},
                        {"service": "N8N", "operations": n8n_analytics.get("workflows", {}).get("total_executions", 0)}
                    ]
                },
                "recent_activity": recent_operations,
                "generated_at": datetime.utcnow().isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/dashboard-stats")
async def get_dashboard_stats(
    request: Request,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get main dashboard KPI statistics.

    Returns real-time stats for:
    - Active automations count
    - Running campaigns count
    - Connect rate (calls answered / calls made)
    - Conversion rate (successful outcomes / total calls)
    - Total calls, duration, and cost (last 7 days)
    - Phone numbers count
    - Total audience size (sum of all audience sizes)
    - Total audiences count
    - Call statistics per automation (with Vapi assistant)
    - Recent activity from call logs

    All data is scoped to the user's organization.
    """
    try:
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        db = get_database()
        user_id = current_user.get("user_id") or current_user.get("id")

        # Time ranges for comparison
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        # Build organization filter
        org_filter = {"organization_id": org_id} if org_id else {}

        # 1. Get active automations count (deployed automations from automation_configs)
        automations_collection = db["automation_configs"]
        active_automations_query = {**org_filter, "status": "deployed"}
        active_automations = await automations_collection.count_documents(active_automations_query)

        # Previous period for comparison
        prev_automations_query = {
            **org_filter,
            "status": "deployed",
            "created_at": {"$lt": seven_days_ago}
        }
        prev_active_automations = await automations_collection.count_documents(prev_automations_query)
        automation_change = active_automations - prev_active_automations

        # 2. Get running campaigns count
        campaigns_collection = db["automation_campaigns"]
        running_campaigns_query = {**org_filter, "status": {"$in": ["running", "active"]}}
        running_campaigns = await campaigns_collection.count_documents(running_campaigns_query)

        # Previous period campaigns
        prev_campaigns_query = {
            **org_filter,
            "status": {"$in": ["running", "active"]},
            "created_at": {"$lt": seven_days_ago}
        }
        prev_running_campaigns = await campaigns_collection.count_documents(prev_campaigns_query)
        campaign_change = running_campaigns - prev_running_campaigns

        # 3. Calculate connect rate and conversion rate from call logs
        calls_collection = db["vapi_calls"]

        # Current period aggregation
        # Note: Handle both string and date types for created_at
        current_period_pipeline = [
            {"$match": {
                **org_filter,
                "$or": [
                    {"created_at": {"$gte": seven_days_ago}},
                    {"created_at": {"$gte": seven_days_ago.isoformat()}}
                ]
            }},
            {"$group": {
                "_id": None,
                "total_calls": {"$sum": 1},
                "answered_calls": {"$sum": {"$cond": [
                    {"$in": ["$status", ["completed", "ended", "in-progress", "forwarding"]]},
                    1, 0
                ]}},
                "successful_calls": {"$sum": {"$cond": [
                    {"$and": [
                        {"$in": ["$status", ["completed", "ended"]]},
                        {"$or": [
                            {"$gte": ["$duration", 30]},  # Call lasted at least 30 seconds
                            {"$eq": ["$ended_reason", "assistant-ended-call"]},
                            {"$eq": ["$ended_reason", "customer-ended-call"]}
                        ]}
                    ]},
                    1, 0
                ]}},
                "total_duration": {"$sum": {"$ifNull": ["$duration", 0]}},
                "total_cost": {"$sum": {"$ifNull": ["$cost", 0]}}
            }}
        ]

        current_stats = await calls_collection.aggregate(current_period_pipeline).to_list(1)
        current_data = current_stats[0] if current_stats else {
            "total_calls": 0, "answered_calls": 0, "successful_calls": 0,
            "total_duration": 0, "total_cost": 0
        }

        # Previous period for comparison
        # Note: Handle both string and date types for created_at
        prev_period_pipeline = [
            {"$match": {
                **org_filter,
                "$or": [
                    {"created_at": {"$gte": fourteen_days_ago, "$lt": seven_days_ago}},
                    {"created_at": {"$gte": fourteen_days_ago.isoformat(), "$lt": seven_days_ago.isoformat()}}
                ]
            }},
            {"$group": {
                "_id": None,
                "total_calls": {"$sum": 1},
                "answered_calls": {"$sum": {"$cond": [
                    {"$in": ["$status", ["completed", "ended", "in-progress", "forwarding"]]},
                    1, 0
                ]}},
                "successful_calls": {"$sum": {"$cond": [
                    {"$and": [
                        {"$in": ["$status", ["completed", "ended"]]},
                        {"$or": [
                            {"$gte": ["$duration", 30]},
                            {"$eq": ["$ended_reason", "assistant-ended-call"]},
                            {"$eq": ["$ended_reason", "customer-ended-call"]}
                        ]}
                    ]},
                    1, 0
                ]}}
            }}
        ]

        prev_stats = await calls_collection.aggregate(prev_period_pipeline).to_list(1)
        prev_data = prev_stats[0] if prev_stats else {
            "total_calls": 0, "answered_calls": 0, "successful_calls": 0
        }

        # Calculate rates
        total_calls = current_data.get("total_calls", 0)
        answered_calls = current_data.get("answered_calls", 0)
        successful_calls = current_data.get("successful_calls", 0)

        connect_rate = round((answered_calls / total_calls * 100), 1) if total_calls > 0 else 0
        conversion_rate = round((successful_calls / total_calls * 100), 1) if total_calls > 0 else 0

        # Previous period rates
        prev_total = prev_data.get("total_calls", 0)
        prev_answered = prev_data.get("answered_calls", 0)
        prev_successful = prev_data.get("successful_calls", 0)

        prev_connect_rate = round((prev_answered / prev_total * 100), 1) if prev_total > 0 else 0
        prev_conversion_rate = round((prev_successful / prev_total * 100), 1) if prev_total > 0 else 0

        connect_rate_change = round(connect_rate - prev_connect_rate, 1)
        conversion_rate_change = round(conversion_rate - prev_conversion_rate, 1)

        # 4. Get recent activity (last 10 call events)
        recent_activity_pipeline = [
            {"$match": org_filter},
            {"$sort": {"created_at": -1}},
            {"$limit": 10},
            {"$project": {
                "_id": 0,
                "title": {"$ifNull": ["$assistant_name", "Voice Assistant"]},
                "description": {"$concat": [
                    {"$cond": [
                        {"$eq": ["$status", "completed"]},
                        "Completed call",
                        {"$cond": [
                            {"$eq": ["$status", "ended"]},
                            "Call ended",
                            {"$concat": ["Call ", {"$ifNull": ["$status", "unknown"]}]}
                        ]}
                    ]},
                    " - ",
                    {"$toString": {"$round": [{"$ifNull": ["$duration", 0]}, 0]}},
                    "s duration"
                ]},
                "time": "$created_at",
                "status": {"$cond": [
                    {"$in": ["$status", ["completed", "ended"]]},
                    "success",
                    {"$cond": [
                        {"$in": ["$status", ["failed", "error"]]},
                        "warning",
                        "info"
                    ]}
                ]}
            }}
        ]

        recent_calls = await calls_collection.aggregate(recent_activity_pipeline).to_list(10)

        # Format timestamps to relative time
        def format_relative_time(dt):
            if not dt:
                return "Unknown"
            diff = now - dt
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            hours = diff.seconds // 3600
            if hours > 0:
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            minutes = diff.seconds // 60
            if minutes > 0:
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            return "Just now"

        recent_activity = []
        for call in recent_calls:
            recent_activity.append({
                "title": call.get("title", "Voice Assistant"),
                "description": call.get("description", "Call activity"),
                "time": format_relative_time(call.get("time")),
                "status": call.get("status", "info")
            })

        # 5. Get phone numbers count
        phone_numbers_collection = db["phone_numbers"]
        phone_numbers_count = await phone_numbers_collection.count_documents(
            {**org_filter, "status": {"$in": ["active", None]}}
        )

        # 6. Get total audience size (sum of all audience sizes)
        audiences_collection = db["audiences"]
        audience_pipeline = [
            {"$match": {**org_filter, "status": "active"}},
            {"$group": {
                "_id": None,
                "total_audience": {"$sum": {"$ifNull": ["$size", 0]}},
                "total_audiences": {"$sum": 1}
            }}
        ]
        audience_stats = await audiences_collection.aggregate(audience_pipeline).to_list(1)
        audience_data = audience_stats[0] if audience_stats else {"total_audience": 0, "total_audiences": 0}

        # Previous period audience comparison
        prev_audience_pipeline = [
            {"$match": {
                **org_filter,
                "status": "active",
                "created_at": {"$lt": seven_days_ago}
            }},
            {"$group": {
                "_id": None,
                "total_audience": {"$sum": {"$ifNull": ["$size", 0]}}
            }}
        ]
        prev_audience_stats = await audiences_collection.aggregate(prev_audience_pipeline).to_list(1)
        prev_audience_data = prev_audience_stats[0] if prev_audience_stats else {"total_audience": 0}

        total_audience = audience_data.get("total_audience", 0)
        prev_total_audience = prev_audience_data.get("total_audience", 0)
        audience_change = total_audience - prev_total_audience

        # 7. Get call statistics per automation (with Vapi assistant)
        # Get automations with Vapi assistant IDs (checking multiple possible field names)
        automations_with_vapi = await automations_collection.find(
            {
                **org_filter,
                "$or": [
                    {"assistant_id": {"$exists": True, "$ne": None}},
                    {"vapi_assistant_id": {"$exists": True, "$ne": None}},
                    {"vapi_agent.assistant_id": {"$exists": True, "$ne": None}}
                ]
            },
            {
                "_id": 1,
                "automation_name": 1,
                "name": 1,
                "assistant_id": 1,
                "vapi_assistant_id": 1,
                "vapi_agent.assistant_id": 1
            }
        ).to_list(None)

        # Aggregate call counts per automation
        automation_call_stats = []
        for automation in automations_with_vapi:
            automation_id = str(automation.get("_id"))
            automation_name = (
                automation.get("automation_name") or
                automation.get("name") or
                "Unknown"
            )

            # Get assistant_id from multiple possible locations
            assistant_id = (
                automation.get("assistant_id") or
                automation.get("vapi_assistant_id") or
                automation.get("vapi_agent", {}).get("assistant_id")
            )

            if not assistant_id:
                continue

            # Get accurate call counts from VAPI Analytics API
            # Reason: MongoDB may be incomplete due to null organization_ids and webhook delays
            # VAPI Analytics API provides accurate totals without pagination limits
            try:
                vapi_analytics = await vapi_service.get_assistant_analytics(
                    assistant_id=assistant_id,
                    start_date=seven_days_ago,
                    end_date=now
                )

                if vapi_analytics.get("success") and vapi_analytics.get("total_calls", 0) > 0:
                    automation_call_stats.append({
                        "automation_id": automation_id,
                        "automation_name": automation_name,
                        "assistant_id": assistant_id,
                        "total_calls": vapi_analytics.get("total_calls", 0),
                        "completed_calls": vapi_analytics.get("total_calls", 0),  # Analytics API doesn't distinguish
                        "total_duration": round(vapi_analytics.get("total_duration_seconds", 0), 0),
                        "avg_duration": round(vapi_analytics.get("avg_duration_seconds", 0), 1),
                        "total_cost": round(vapi_analytics.get("total_cost", 0), 2)
                    })
                else:
                    # Fallback to MongoDB if Vapi API fails
                    call_count_pipeline = [
                        {"$match": {
                            "assistant_id": assistant_id,
                            "$or": [
                                {"created_at": {"$gte": seven_days_ago}},
                                {"created_at": {"$gte": seven_days_ago.isoformat()}}
                            ]
                        }},
                        {"$group": {
                            "_id": None,
                            "total_calls": {"$sum": 1},
                            "total_duration": {"$sum": {"$ifNull": ["$duration", 0]}},
                            "total_cost": {"$sum": {"$ifNull": ["$cost", 0]}},
                            "avg_duration": {"$avg": {"$ifNull": ["$duration", 0]}}
                        }}
                    ]
                    call_stats = await calls_collection.aggregate(call_count_pipeline).to_list(1)
                    if call_stats and call_stats[0].get("total_calls", 0) > 0:
                        stats = call_stats[0]
                        automation_call_stats.append({
                            "automation_id": automation_id,
                            "automation_name": automation_name,
                            "assistant_id": assistant_id,
                            "total_calls": stats.get("total_calls", 0),
                            "completed_calls": stats.get("total_calls", 0),
                            "total_duration": round(stats.get("total_duration", 0), 0),
                            "avg_duration": round(stats.get("avg_duration", 0), 1),
                            "total_cost": round(stats.get("total_cost", 0), 2)
                        })
            except Exception as e:
                logger.error(f"Error fetching VAPI analytics for assistant {assistant_id}: {e}")
                # Continue with next automation instead of failing entire request
                continue

        return {
            "success": True,
            "stats": {
                "activeAutomations": active_automations,
                "runningCampaigns": running_campaigns,
                "connectRate": connect_rate,
                "conversionRate": conversion_rate,
                "automationChange": f"+{automation_change}" if automation_change >= 0 else str(automation_change),
                "campaignChange": f"+{campaign_change}" if campaign_change >= 0 else str(campaign_change),
                "connectRateChange": f"+{connect_rate_change}%" if connect_rate_change >= 0 else f"{connect_rate_change}%",
                "conversionRateChange": f"+{conversion_rate_change}%" if conversion_rate_change >= 0 else f"{conversion_rate_change}%",
                "totalCalls": total_calls,
                "totalDuration": round(current_data.get("total_duration", 0), 0),
                "totalCost": round(current_data.get("total_cost", 0), 2),
                "phoneNumbers": phone_numbers_count,
                "totalAudience": total_audience,
                "totalAudiences": audience_data.get("total_audiences", 0),
                "audienceChange": f"+{audience_change}" if audience_change >= 0 else str(audience_change)
            },
            "recentActivity": recent_activity,
            "automationCallStats": automation_call_stats,
            "period": {
                "start": seven_days_ago.isoformat(),
                "end": now.isoformat(),
                "label": "Last 7 days"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


@router.get("/profit-margins/trends")
async def get_profit_margin_trends(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    interval: str = Query("daily", description="Interval: daily, weekly, monthly"),
    providers: Optional[str] = Query(None, description="Comma-separated provider list"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get profit margin trends over time for visualization (ADMIN ONLY).

    Returns time-series data showing margin changes across providers.
    Perfect for line charts and trend analysis.

    Now properly scoped to organization. Requires authentication.
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        logger.info(f"Getting profit margin trends for organization: {org_id}, interval: {interval}")

        from ..mongo import get_database
        from apps.shared.services.cost_record_service import CostRecordService

        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else datetime.utcnow() - timedelta(days=30)
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else datetime.utcnow()

        # Parse providers
        provider_list = providers.split(',') if providers else None

        # Get database
        db = get_database()
        cost_service = CostRecordService(db.client, db.name)

        # Determine grouping based on interval
        if interval == "hourly":
            date_format = "%Y-%m-%d %H:00"
            group_format = {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}}
        elif interval == "weekly":
            date_format = "%Y-W%V"
            group_format = {"$dateToString": {"format": "%Y-W%V", "date": "$timestamp"}}
        elif interval == "monthly":
            date_format = "%Y-%m"
            group_format = {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}}
        else:  # daily
            date_format = "%Y-%m-%d"
            group_format = {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}

        # Build aggregation pipeline with organization filter
        match_stage = {
            "timestamp": {
                "$gte": start_dt,
                "$lte": end_dt
            }
        }

        # Add organization filter
        if org_id:
            match_stage["organization_id"] = org_id

        # Add provider filter if specified
        if provider_list:
            match_stage["provider"] = {"$in": provider_list}

        pipeline = [{"$match": match_stage}]

        # Group by date and provider
        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "date": group_format,
                        "provider": "$provider"
                    },
                    "total_revenue": {"$sum": "$customer_charge"},
                    "total_costs": {"$sum": "$actual_cost"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {
                "$addFields": {
                    "total_profit": {"$subtract": ["$total_revenue", "$total_costs"]},
                    "margin_percentage": {
                        "$cond": {
                            "if": {"$eq": ["$total_revenue", 0]},
                            "then": 0,
                            "else": {
                                "$multiply": [
                                    {
                                        "$divide": [
                                            {"$subtract": ["$total_revenue", "$total_costs"]},
                                            "$total_revenue"
                                        ]
                                    },
                                    100
                                ]
                            }
                        }
                    }
                }
            },
            {"$sort": {"_id.date": 1}}
        ])

        # Execute aggregation
        collection = cost_service.collection
        results = await collection.aggregate(pipeline).to_list(length=None)

        # Transform results into chart-friendly format
        # Group by date first, then create objects with provider columns
        date_map = {}
        providers_set = set()

        for item in results:
            date = item["_id"]["date"]
            provider = item["_id"]["provider"]
            margin = round(item["margin_percentage"], 2)
            revenue = round(item["total_revenue"], 2)
            costs = round(item["total_costs"], 2)
            profit = round(item["total_profit"], 2)

            providers_set.add(provider)

            if date not in date_map:
                date_map[date] = {"date": date}

            # Store multiple metrics per provider
            date_map[date][f"{provider}_margin"] = margin
            date_map[date][f"{provider}_revenue"] = revenue
            date_map[date][f"{provider}_costs"] = costs
            date_map[date][f"{provider}_profit"] = profit
            date_map[date][f"{provider}_transactions"] = item["transaction_count"]

        # Convert to list and sort
        trends = sorted(date_map.values(), key=lambda x: x["date"])

        # Calculate aggregate margins per date (across all providers)
        for trend in trends:
            total_revenue = sum(trend.get(f"{p}_revenue", 0) for p in providers_set)
            total_costs = sum(trend.get(f"{p}_costs", 0) for p in providers_set)

            if total_revenue > 0:
                trend["overall_margin"] = round(((total_revenue - total_costs) / total_revenue) * 100, 2)
            else:
                trend["overall_margin"] = 0

            trend["overall_revenue"] = round(total_revenue, 2)
            trend["overall_costs"] = round(total_costs, 2)
            trend["overall_profit"] = round(total_revenue - total_costs, 2)

        return {
            "success": True,
            "trends": trends,
            "providers": sorted(list(providers_set)),
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "interval": interval,
                "data_points": len(trends)
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profit margin trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get profit margin trends: {str(e)}")
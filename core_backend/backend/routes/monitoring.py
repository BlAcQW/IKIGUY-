"""
Monitoring API endpoints for automation health and VAPI call analytics.

This module provides endpoints for tracking and analyzing automation performance,
VAPI call metrics, and campaign health across the platform.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.automation_monitoring_service import (
    AutomationMonitoringService,
    VAPICallMetrics,
    AutomationHealth,
    CampaignPerformance
)
from ..auth import get_current_user_mongo

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class VAPICallMetricsRequest(BaseModel):
    """Request model for recording VAPI call metrics."""
    automation_id: str = Field(..., description="ID of the automation")
    campaign_id: Optional[str] = Field(None, description="ID of the campaign")
    call_duration: float = Field(..., description="Duration of call in seconds")
    call_status: str = Field(..., description="Status of the call")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score")
    transcript: Optional[str] = Field(None, description="Call transcript")
    cost: Optional[float] = Field(None, description="Cost of the call")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional call metadata")


class AutomationHealthRequest(BaseModel):
    """Request model for updating automation health status."""
    automation_id: str = Field(..., description="ID of the automation")
    campaign_id: Optional[str] = Field(None, description="ID of the campaign")
    status: str = Field(..., description="Current automation status")
    error_count: int = Field(0, description="Number of errors")
    success_rate: float = Field(..., description="Success rate percentage")
    last_execution: datetime = Field(..., description="Last execution timestamp")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance data")


class MetricsQuery(BaseModel):
    """Query parameters for metrics retrieval."""
    start_date: Optional[datetime] = Field(None, description="Start date for metrics")
    end_date: Optional[datetime] = Field(None, description="End date for metrics")
    automation_id: Optional[str] = Field(None, description="Filter by automation ID")
    campaign_id: Optional[str] = Field(None, description="Filter by campaign ID")
    limit: int = Field(100, description="Maximum number of records to return")


@router.post("/vapi-calls", response_model=Dict[str, str])
async def record_vapi_call_metrics(
    request: VAPICallMetricsRequest,
    current_user=Depends(get_current_user_mongo)
):
    """
    Record VAPI call metrics for monitoring and analysis.

    Args:
        request: VAPI call metrics data
        current_user: Authenticated user

    Returns:
        Dict containing the created metrics ID
    """
    try:
        service = AutomationMonitoringService()

        call_data = {
            "automation_id": request.automation_id,
            "campaign_id": request.campaign_id,
            "tenant_id": current_user.get("tenant_id", "default"),
            "call_duration": request.call_duration,
            "call_status": request.call_status,
            "sentiment_score": request.sentiment_score,
            "transcript": request.transcript,
            "cost": request.cost,
            "metadata": request.metadata or {}
        }

        metrics_id = await service.record_vapi_call_metrics(call_data)
        return {"metrics_id": metrics_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record VAPI call metrics: {str(e)}")


@router.post("/automation-health", response_model=Dict[str, str])
async def update_automation_health(
    request: AutomationHealthRequest,
    current_user=Depends(get_current_user_mongo)
):
    """
    Update automation health status and metrics.

    Args:
        request: Automation health data
        current_user: Authenticated user

    Returns:
        Dict containing the health record ID
    """
    try:
        service = AutomationMonitoringService()

        health_data = {
            "automation_id": request.automation_id,
            "campaign_id": request.campaign_id,
            "tenant_id": current_user.get("tenant_id", "default"),
            "status": request.status,
            "error_count": request.error_count,
            "success_rate": request.success_rate,
            "last_execution": request.last_execution,
            "performance_metrics": request.performance_metrics or {}
        }

        health_id = await service.update_automation_health(health_data)
        return {"health_id": health_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update automation health: {str(e)}")


@router.get("/vapi-calls", response_model=List[VAPICallMetrics])
async def get_vapi_call_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    automation_id: Optional[str] = Query(None, description="Filter by automation ID"),
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    limit: int = Query(100, description="Maximum records to return"),
    current_user=Depends(get_current_user_mongo)
):
    """
    Retrieve VAPI call metrics with optional filtering.

    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
        automation_id: Filter by automation ID
        campaign_id: Filter by campaign ID
        limit: Maximum number of records
        current_user: Authenticated user

    Returns:
        List of VAPI call metrics
    """
    try:
        service = AutomationMonitoringService()
        tenant_id = current_user.get("tenant_id", "default")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        metrics = await service.get_vapi_call_metrics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            automation_id=automation_id,
            campaign_id=campaign_id,
            limit=limit
        )

        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve VAPI call metrics: {str(e)}")


@router.get("/automation-health", response_model=List[AutomationHealth])
async def get_automation_health(
    automation_id: Optional[str] = Query(None, description="Filter by automation ID"),
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user_mongo)
):
    """
    Retrieve automation health status and metrics.

    Args:
        automation_id: Filter by automation ID
        campaign_id: Filter by campaign ID
        status: Filter by status
        current_user: Authenticated user

    Returns:
        List of automation health records
    """
    try:
        service = AutomationMonitoringService()
        tenant_id = current_user.get("tenant_id", "default")

        health_records = await service.get_automation_health(
            tenant_id=tenant_id,
            automation_id=automation_id,
            campaign_id=campaign_id,
            status=status
        )

        return health_records

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve automation health: {str(e)}")


@router.get("/campaign-performance", response_model=List[CampaignPerformance])
async def get_campaign_performance(
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user=Depends(get_current_user_mongo)
):
    """
    Retrieve campaign performance analytics.

    Args:
        campaign_id: Filter by campaign ID
        start_date: Start date for filtering
        end_date: End date for filtering
        current_user: Authenticated user

    Returns:
        List of campaign performance records
    """
    try:
        service = AutomationMonitoringService()
        tenant_id = current_user.get("tenant_id", "default")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        performance_data = await service.get_campaign_performance(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date
        )

        return performance_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve campaign performance: {str(e)}")


@router.get("/dashboard-summary", response_model=Dict[str, Any])
async def get_dashboard_summary(
    current_user=Depends(get_current_user_mongo)
):
    """
    Get comprehensive dashboard summary with key metrics.

    Args:
        current_user: Authenticated user

    Returns:
        Dict containing dashboard summary data
    """
    try:
        service = AutomationMonitoringService()
        tenant_id = current_user.get("tenant_id", "default")

        # Get metrics for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Gather summary data
        vapi_metrics = await service.get_vapi_call_metrics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        automation_health = await service.get_automation_health(
            tenant_id=tenant_id
        )

        campaign_performance = await service.get_campaign_performance(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        # Calculate summary statistics
        total_calls = len(vapi_metrics)
        total_cost = sum(call.total_cost for call in vapi_metrics if call.total_cost)
        avg_call_duration = sum(call.duration_seconds for call in vapi_metrics if call.duration_seconds) / max(total_calls, 1)
        avg_sentiment = sum(call.sentiment_score for call in vapi_metrics if call.sentiment_score) / max(
            len([call for call in vapi_metrics if call.sentiment_score]), 1
        )

        healthy_automations = len([health for health in automation_health if health.status == "healthy"])
        total_automations = len(automation_health)

        total_campaigns = len(campaign_performance)
        avg_success_rate = sum(perf.conversion_rate for perf in campaign_performance) / max(total_campaigns, 1)

        summary = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "vapi_metrics": {
                "total_calls": total_calls,
                "total_cost": round(total_cost, 2),
                "avg_call_duration": round(avg_call_duration, 2),
                "avg_sentiment_score": round(avg_sentiment, 2)
            },
            "automation_health": {
                "total_automations": total_automations,
                "healthy_automations": healthy_automations,
                "health_percentage": round((healthy_automations / max(total_automations, 1)) * 100, 1)
            },
            "campaign_performance": {
                "total_campaigns": total_campaigns,
                "avg_success_rate": round(avg_success_rate, 1),
                "total_conversions": sum(perf.conversions for perf in campaign_performance)
            }
        }

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard summary: {str(e)}")


@router.post("/webhook/vapi-call", response_model=Dict[str, str])
async def handle_vapi_webhook(
    webhook_data: Dict[str, Any]
):
    """
    Handle VAPI webhook for automatic call metrics recording.

    Args:
        webhook_data: Webhook payload from VAPI

    Returns:
        Dict containing processing status
    """
    try:
        service = AutomationMonitoringService()

        # Extract relevant data from webhook
        call_data = {
            "automation_id": webhook_data.get("metadata", {}).get("automation_id"),
            "campaign_id": webhook_data.get("metadata", {}).get("campaign_id"),
            "tenant_id": webhook_data.get("metadata", {}).get("tenant_id", "default"),
            "call_duration": webhook_data.get("duration", 0),
            "call_status": webhook_data.get("status", "unknown"),
            "transcript": webhook_data.get("transcript"),
            "cost": webhook_data.get("cost"),
            "metadata": webhook_data
        }

        # Only process if we have required data
        if call_data["automation_id"]:
            metrics_id = await service.record_vapi_call_metrics(call_data)
            return {"status": "processed", "metrics_id": metrics_id}
        else:
            return {"status": "skipped", "reason": "missing automation_id"}

    except Exception as e:
        # Log error but don't fail webhook
        return {"status": "error", "error": str(e)}
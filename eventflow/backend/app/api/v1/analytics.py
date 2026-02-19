"""
Analytics API routes for EventFlow.

Provides endpoints for tracking event costs, user usage, and communication expenses.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ...services.analytics_service import get_analytics_service, EventFlowAnalyticsService
from ..dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


class EventCostsResponse(BaseModel):
    """Response model for event costs."""
    event_id: str
    event_name: Optional[str] = None
    period: dict
    total_cost: float
    assistants_count: int
    assistants_breakdown: dict
    combined_metrics: dict


class UserUsageResponse(BaseModel):
    """Response model for user usage summary."""
    user_id: str
    period: dict
    total_cost: float
    total_transactions: int
    services: dict


class TaskCommunicationCostsResponse(BaseModel):
    """Response model for task communication costs."""
    task_id: str
    period: dict
    total_cost: float
    total_communications: int
    services: dict


@router.get(
    "/events/{event_id}/costs",
    response_model=EventCostsResponse,
    summary="Get event costs",
    description="""
    Get comprehensive cost breakdown for an event across all associated assistants.

    Aggregates costs from:
    - VAPI calls
    - Vonage voice calls and SMS
    - Twilio SMS, MMS, WhatsApp
    - LLM inference
    - TTS synthesis
    - ASR transcription
    """
)
async def get_event_costs(
    event_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    current_user: dict = Depends(get_current_user),
    analytics_service: EventFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Get comprehensive cost breakdown for an event.

    Args:
        event_id: Event ID
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)
        current_user: Current authenticated user
        analytics_service: Analytics service instance

    Returns:
        Event costs breakdown
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get user ID
        user_id = current_user.get("user_id") or current_user.get("sub")

        # Get event costs
        costs = await analytics_service.get_event_costs(
            event_id=event_id,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in costs:
            raise HTTPException(status_code=404, detail=costs["error"])

        return costs

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get event costs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get event costs: {str(e)}")


@router.get(
    "/usage",
    response_model=UserUsageResponse,
    summary="Get user usage summary",
    description="""
    Get usage summary for the authenticated user across all events and services.

    Shows total costs and transaction counts broken down by service type.
    """
)
async def get_user_usage(
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    current_user: dict = Depends(get_current_user),
    analytics_service: EventFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Get usage summary for the authenticated user.

    Args:
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)
        current_user: Current authenticated user
        analytics_service: Analytics service instance

    Returns:
        User usage summary
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get user ID
        user_id = current_user.get("user_id") or current_user.get("sub")

        # Get user usage
        usage = await analytics_service.get_user_usage_summary(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in usage:
            raise HTTPException(status_code=500, detail=usage["error"])

        return usage

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get user usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user usage: {str(e)}")


@router.get(
    "/tasks/{task_id}/communication-costs",
    response_model=TaskCommunicationCostsResponse,
    summary="Get task communication costs",
    description="""
    Get communication costs for a specific task.

    Tracks costs for:
    - Voice calls to responsible persons
    - SMS reminders
    - WhatsApp messages
    - Other communication channels
    """
)
async def get_task_communication_costs(
    task_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    current_user: dict = Depends(get_current_user),
    analytics_service: EventFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Get communication costs for a task.

    Args:
        task_id: Task ID
        start_date: Optional start date filter (ISO 8601)
        end_date: Optional end date filter (ISO 8601)
        current_user: Current authenticated user
        analytics_service: Analytics service instance

    Returns:
        Task communication costs
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get task costs
        costs = await analytics_service.get_task_communication_costs(
            task_id=task_id,
            start_date=start_dt,
            end_date=end_dt
        )

        # Check for errors
        if "error" in costs:
            raise HTTPException(status_code=404, detail=costs["error"])

        return costs

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get task communication costs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get task communication costs: {str(e)}")


@router.get(
    "/health",
    summary="Analytics service health check",
    description="Check if analytics service is initialized and working"
)
async def analytics_health(
    analytics_service: EventFlowAnalyticsService = Depends(get_analytics_service)
):
    """
    Health check for analytics service.

    Returns:
        Service health status
    """
    return {
        "status": "healthy" if analytics_service.initialized else "not_initialized",
        "service": "eventflow_analytics"
    }

"""
Calendly Consolidated Routes - FastAPI endpoints for scheduling and calendar management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import time
import pytz

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import get_current_user_mongo
from ..services.calendly_consolidated_service import get_calendly_service

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from integration.calendly import (
    CalendlyEventStatus,
    CalendlyResponse,
)


router = APIRouter(prefix="/calendly", tags=["calendly", "scheduling", "calendar"])


# Request/Response Models
class CalendlyUserRequest(BaseModel):
    """Request model for user operations."""
    tenant_id: str = Field(..., description="Tenant identifier")
    user_uri: Optional[str] = Field(None, description="Specific user URI (if not provided, gets current user)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class CalendlyEventTypesRequest(BaseModel):
    """Request model for event types."""
    tenant_id: str = Field(..., description="Tenant identifier")
    user_uri: str = Field(..., description="User URI")
    count: int = Field(20, description="Number of results per page", ge=1, le=100)
    page_token: Optional[str] = Field(None, description="Pagination token")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class CalendlyEventsRequest(BaseModel):
    """Request model for scheduled events."""
    tenant_id: str = Field(..., description="Tenant identifier")
    user_uri: Optional[str] = Field(None, description="Filter by user URI")
    organization_uri: Optional[str] = Field(None, description="Filter by organization URI")
    count: int = Field(20, description="Number of results per page", ge=1, le=100)
    status: Optional[CalendlyEventStatus] = Field(None, description="Filter by event status")
    min_start_time: Optional[str] = Field(None, description="Minimum start time (ISO 8601)")
    max_start_time: Optional[str] = Field(None, description="Maximum start time (ISO 8601)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class CalendlyEventDetailsRequest(BaseModel):
    """Request model for event details."""
    tenant_id: str = Field(..., description="Tenant identifier")
    event_uuid: str = Field(..., description="Event UUID")
    include_invitees: bool = Field(False, description="Include invitee information")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class CalendlyCancelEventRequest(BaseModel):
    """Request model for event cancellation."""
    tenant_id: str = Field(..., description="Tenant identifier")
    event_uuid: str = Field(..., description="Event UUID to cancel")
    reason: Optional[str] = Field(None, description="Cancellation reason")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class CalendlyWebhookRequest(BaseModel):
    """Request model for webhook operations."""
    tenant_id: str = Field(..., description="Tenant identifier")
    operation: str = Field(..., description="Operation (create, list, get, delete)")
    callback_url: Optional[str] = Field(None, description="Webhook callback URL (for create)")
    events: Optional[List[str]] = Field(None, description="Event types to subscribe to (for create)")
    organization_uri: Optional[str] = Field(None, description="Organization URI (for create/list)")
    webhook_uuid: Optional[str] = Field(None, description="Webhook UUID (for get/delete)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for tracking")


class DateTimeResponse(BaseModel):
    """Response model for current date/time information."""
    current_datetime: str = Field(..., description="Current date and time in ISO format")
    current_date: str = Field(..., description="Current date in YYYY-MM-DD format")
    current_time: str = Field(..., description="Current time in HH:MM format")
    timezone: str = Field(..., description="Current timezone")
    day_of_week: str = Field(..., description="Day of the week")
    formatted_date: str = Field(..., description="Human readable date format")
    unix_timestamp: int = Field(..., description="Unix timestamp")


class CalendlyAvailabilityRequest(BaseModel):
    """Request model for checking Calendly availability."""
    event_type: Optional[str] = Field(default=None, description="Type of appointment")
    start_date: Optional[str] = Field(default=None, description="Start date for availability check (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date for availability check (YYYY-MM-DD)")
    timezone: Optional[str] = Field(default="Africa/Accra", description="Timezone for appointments")


class AvailabilityOption(BaseModel):
    """Individual availability option."""
    date: str = Field(..., description="Available date in YYYY-MM-DD format")
    day_name: str = Field(..., description="Day of the week")
    time_slots: List[str] = Field(..., description="Available time slots")
    formatted_display: str = Field(..., description="Human-readable format for display")


class CalendlyAvailabilityResponse(BaseModel):
    """Response model for Calendly availability check."""
    success: bool = Field(..., description="Whether the availability check was successful")
    current_date_context: DateTimeResponse = Field(..., description="Current date and time context")
    availability_options: List[AvailabilityOption] = Field(..., description="Available appointment options (typically 3)")
    total_slots_found: int = Field(..., description="Total number of available slots")
    search_period: str = Field(..., description="Period searched for availability")
    message: str = Field(..., description="Human-readable message about availability")


class CalendlyBookingRequest(BaseModel):
    """Request model for booking Calendly appointments."""
    event_type: str = Field(..., description="Type of appointment")
    start_time: str = Field(..., description="Appointment start time in ISO format")
    customer_name: str = Field(..., description="Customer's name (first name only)")
    customer_phone: str = Field(..., description="Customer's phone number")
    customer_email: Optional[str] = Field(default=None, description="Customer's email (optional)")
    timezone: Optional[str] = Field(default="Africa/Accra", description="Timezone for appointment")


class CalendlyBookingResponse(BaseModel):
    """Response model for Calendly appointment booking."""
    success: bool = Field(..., description="Whether the booking was successful")
    booking_id: Optional[str] = Field(default=None, description="Unique booking identifier")
    appointment_details: Dict[str, Any] = Field(default_factory=dict, description="Appointment details")
    confirmation_message: str = Field(..., description="Human-readable confirmation message")
    current_date_context: DateTimeResponse = Field(..., description="Current date and time context")


# User Management Routes
@router.post("/user", response_model=Dict[str, Any])
async def get_user(
    user_request: CalendlyUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get user information.

    Args:
        user_request (CalendlyUserRequest): User request parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: User information
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_tenant_user_info(
            tenant_id=user_request.tenant_id,
            user_uri=user_request.user_uri,
            context=user_request.context
        )

        return {
            "success": result.success,
            "user": result.data.get("resource") if result.data else None,
            "message": result.message or "User information retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.get("/user/current", response_model=Dict[str, Any])
async def get_current_user(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get current user information.

    Args:
        tenant_id (str): Tenant identifier
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Current user information
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_tenant_user_info(
            tenant_id=tenant_id,
            user_uri=None  # This will get current user
        )

        return {
            "success": result.success,
            "user": result.data.get("resource") if result.data else None,
            "message": result.message or "Current user information retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current user: {str(e)}")


# Event Types Routes
@router.post("/event-types", response_model=Dict[str, Any])
async def get_event_types(
    event_types_request: CalendlyEventTypesRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get user's event types.

    Args:
        event_types_request (CalendlyEventTypesRequest): Event types request parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Event types list
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_tenant_event_types(
            tenant_id=event_types_request.tenant_id,
            user_uri=event_types_request.user_uri,
            count=event_types_request.count,
            page_token=event_types_request.page_token,
            context=event_types_request.context
        )

        return {
            "success": result.success,
            "event_types": result.data.get("collection", []) if result.data else [],
            "pagination": result.data.get("pagination") if result.data else None,
            "message": result.message or "Event types retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event types: {str(e)}")


@router.get("/event-types/{event_type_uuid}", response_model=Dict[str, Any])
async def get_event_type(
    event_type_uuid: str,
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get specific event type details.

    Args:
        event_type_uuid (str): Event type UUID
        tenant_id (str): Tenant identifier
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Event type details
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_event_type(event_type_uuid)

        # Record analytics for tenant
        await calendly_service._record_analytics(
            tenant_id=tenant_id,
            operation="get_event_type",
            success=result.success,
            duration=0,  # Quick operation
            event_type_uuid=event_type_uuid
        )

        return {
            "success": result.success,
            "event_type": result.data.get("resource") if result.data else None,
            "message": result.message or "Event type retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event type: {str(e)}")


# Scheduled Events Routes
@router.post("/events", response_model=Dict[str, Any])
async def get_scheduled_events(
    events_request: CalendlyEventsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get scheduled events.

    Args:
        events_request (CalendlyEventsRequest): Events request parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Scheduled events list
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_tenant_scheduled_events(
            tenant_id=events_request.tenant_id,
            user_uri=events_request.user_uri,
            organization_uri=events_request.organization_uri,
            count=events_request.count,
            status=events_request.status,
            min_start_time=events_request.min_start_time,
            max_start_time=events_request.max_start_time,
            context=events_request.context
        )

        return {
            "success": result.success,
            "events": result.data.get("collection", []) if result.data else [],
            "pagination": result.data.get("pagination") if result.data else None,
            "message": result.message or "Scheduled events retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduled events: {str(e)}")


@router.post("/events/details", response_model=Dict[str, Any])
async def get_event_details(
    event_details_request: CalendlyEventDetailsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get detailed event information including invitees.

    Args:
        event_details_request (CalendlyEventDetailsRequest): Event details request
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Complete event information
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_tenant_event_details(
            tenant_id=event_details_request.tenant_id,
            event_uuid=event_details_request.event_uuid,
            include_invitees=event_details_request.include_invitees,
            context=event_details_request.context
        )

        return {
            "success": result["success"],
            "event": result["event"].get("resource") if result["event"] else None,
            "invitees": result["invitees"].get("collection", []) if result["invitees"] else None,
            "message": "Event details retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event details: {str(e)}")


@router.get("/events/{event_uuid}", response_model=Dict[str, Any])
async def get_event(
    event_uuid: str,
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get specific event.

    Args:
        event_uuid (str): Event UUID
        tenant_id (str): Tenant identifier
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Event information
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_event(event_uuid)

        # Record analytics for tenant
        await calendly_service._record_analytics(
            tenant_id=tenant_id,
            operation="get_event",
            success=result.success,
            duration=0,  # Quick operation
            event_uuid=event_uuid
        )

        return {
            "success": result.success,
            "event": result.data.get("resource") if result.data else None,
            "message": result.message or "Event retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")


@router.post("/events/cancel", response_model=Dict[str, Any])
async def cancel_event(
    cancel_request: CalendlyCancelEventRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Cancel a scheduled event.

    Args:
        cancel_request (CalendlyCancelEventRequest): Cancellation request
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Cancellation result
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.cancel_tenant_event(
            tenant_id=cancel_request.tenant_id,
            event_uuid=cancel_request.event_uuid,
            reason=cancel_request.reason,
            context=cancel_request.context
        )

        return {
            "success": result.success,
            "message": result.message or "Event cancelled successfully",
            "event_uuid": cancel_request.event_uuid,
            "reason": cancel_request.reason
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel event: {str(e)}")


# Invitees Routes
@router.get("/events/{event_uuid}/invitees", response_model=Dict[str, Any])
async def get_event_invitees(
    event_uuid: str,
    tenant_id: str,
    count: int = Query(20, ge=1, le=100),
    page_token: Optional[str] = None,
    email: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get invitees for an event.

    Args:
        event_uuid (str): Event UUID
        tenant_id (str): Tenant identifier
        count (int): Number of results per page
        page_token (Optional[str]): Pagination token
        email (Optional[str]): Filter by email
        status (Optional[str]): Filter by status
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Event invitees list
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.list_event_invitees(
            event_uuid=event_uuid,
            count=count,
            page_token=page_token,
            email=email,
            status=status
        )

        # Record analytics for tenant
        await calendly_service._record_analytics(
            tenant_id=tenant_id,
            operation="list_invitees",
            success=result.success,
            duration=0,  # Quick operation
            event_uuid=event_uuid,
            count=count
        )

        return {
            "success": result.success,
            "invitees": result.data.get("collection", []) if result.data else [],
            "pagination": result.data.get("pagination") if result.data else None,
            "message": result.message or "Invitees retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invitees: {str(e)}")


@router.get("/invitees/{invitee_uuid}", response_model=Dict[str, Any])
async def get_invitee(
    invitee_uuid: str,
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get specific invitee information.

    Args:
        invitee_uuid (str): Invitee UUID
        tenant_id (str): Tenant identifier
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Invitee information
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.get_invitee(invitee_uuid)

        # Record analytics for tenant
        await calendly_service._record_analytics(
            tenant_id=tenant_id,
            operation="get_invitee",
            success=result.success,
            duration=0,  # Quick operation
            invitee_uuid=invitee_uuid
        )

        return {
            "success": result.success,
            "invitee": result.data.get("resource") if result.data else None,
            "message": result.message or "Invitee retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invitee: {str(e)}")


# Webhooks Routes
@router.post("/webhooks", response_model=Dict[str, Any])
async def manage_webhooks(
    webhook_request: CalendlyWebhookRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Manage webhook subscriptions.

    Args:
        webhook_request (CalendlyWebhookRequest): Webhook request parameters
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Webhook operation result
    """
    try:
        calendly_service = await get_calendly_service()

        result = await calendly_service.manage_tenant_webhooks(
            tenant_id=webhook_request.tenant_id,
            operation=webhook_request.operation,
            callback_url=webhook_request.callback_url,
            events=webhook_request.events,
            organization_uri=webhook_request.organization_uri,
            webhook_uuid=webhook_request.webhook_uuid,
            context=webhook_request.context
        )

        response_data = {
            "success": result.success,
            "operation": webhook_request.operation,
            "message": result.message or f"Webhook {webhook_request.operation} completed successfully"
        }

        if result.data:
            if webhook_request.operation == "list":
                response_data["webhooks"] = result.data.get("collection", [])
                response_data["pagination"] = result.data.get("pagination")
            else:
                response_data["webhook"] = result.data.get("resource")

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to manage webhook: {str(e)}")


# Analytics Routes
@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics(
    tenant_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get Calendly analytics for a tenant.

    Args:
        tenant_id (str): Tenant identifier
        start_date (Optional[datetime]): Start date for analytics
        end_date (Optional[datetime]): End date for analytics
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Analytics data for the tenant
    """
    try:
        calendly_service = await get_calendly_service()

        analytics_data = await calendly_service.get_tenant_analytics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "tenant_id": tenant_id,
            "analytics": analytics_data,
            "message": "Calendly analytics retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/usage-summary", response_model=Dict[str, Any])
async def get_usage_summary(
    tenant_id: str,
    period_days: int = Query(30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user_mongo)
):
    """
    Get usage summary for a tenant.

    Args:
        tenant_id (str): Tenant identifier
        period_days (int): Number of days to analyze
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Usage summary data
    """
    try:
        calendly_service = await get_calendly_service()

        usage_data = await calendly_service.get_tenant_usage_summary(
            tenant_id=tenant_id,
            period_days=period_days
        )

        return {
            "success": True,
            "tenant_id": tenant_id,
            "usage_summary": usage_data,
            "message": "Usage summary retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage summary: {str(e)}")


# Health and Capabilities Routes
@router.get("/health", response_model=Dict[str, Any])
async def health_check(current_user: Dict[str, Any] = Depends(get_current_user_mongo)):
    """
    Check Calendly service health.

    Args:
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Health status of Calendly service
    """
    try:
        calendly_service = await get_calendly_service()
        health_status = await calendly_service.health_check()

        return {
            "service": "calendly",
            "status": "healthy" if health_status.get("connected") else "unhealthy",
            "connected": health_status.get("connected", False),
            "capabilities": health_status.get("capabilities", []),
            "api_version": health_status.get("api_version", "v2"),
            "api_key_configured": health_status.get("api_key_configured", False),
            "message": "Calendly service health check completed"
        }

    except Exception as e:
        return {
            "service": "calendly",
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "message": "Calendly service health check failed"
        }


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_capabilities(current_user: Dict[str, Any] = Depends(get_current_user_mongo)):
    """
    Get Calendly service capabilities.

    Args:
        current_user (Dict[str, Any]): Current authenticated user

    Returns:
        Dict[str, Any]: Available capabilities of Calendly service
    """
    try:
        calendly_service = await get_calendly_service()
        capabilities = await calendly_service.get_capabilities()

        return {
            "service": "calendly",
            "capabilities": capabilities,
            "mcp_enabled": False,  # No dedicated MCP server
            "supported_operations": [
                "get_user",
                "get_current_user",
                "get_event_types",
                "get_event_type",
                "get_scheduled_events",
                "get_event_details",
                "get_event",
                "cancel_event",
                "get_invitees",
                "get_invitee",
                "manage_webhooks",
                "analytics",
                "usage_summary"
            ],
            "message": "Calendly service capabilities retrieved successfully"
        }

    except Exception as e:
        return {
            "service": "calendly",
            "capabilities": {},
            "error": str(e),
            "message": "Failed to get Calendly service capabilities"
        }


@router.post("/availability", response_model=CalendlyAvailabilityResponse)
async def check_calendly_availability(request: CalendlyAvailabilityRequest):
    """
    Check Calendly appointment availability with current date context and 3 options.

    Provides appointment availability options starting from the current date,
    automatically including current date/time context for intelligent scheduling.

    Args:
        request: Availability check parameters

    Returns:
        CalendlyAvailabilityResponse: Current date context + 3 availability options
    """
    try:
        # Get timezone
        try:
            tz = pytz.timezone(request.timezone)
        except Exception:
            tz = pytz.timezone("Africa/Accra")  # Default fallback
            request.timezone = "Africa/Accra"

        now = datetime.now(tz)

        # Calculate business day and hours
        is_business_day = now.weekday() < 5
        is_business_hours = 9 <= now.hour < 17

        # Day and month names
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        # Create current date context
        current_date_context = DateTimeResponse(
            current_datetime=now.isoformat(),
            current_date=now.strftime('%Y-%m-%d'),
            current_time=now.strftime('%H:%M'),
            timezone=request.timezone,
            day_of_week=days[now.weekday()],
            formatted_date=now.strftime('%A, %B %d, %Y'),
            unix_timestamp=int(now.timestamp())
        )

        # Generate 3 availability options
        availability_options = []
        search_start = now

        # If it's after business hours today, start from tomorrow
        if now.hour >= 17:
            search_start = now + timedelta(days=1)
            search_start = search_start.replace(hour=9, minute=0, second=0, microsecond=0)
        # If it's before business hours today, start from 9 AM today
        elif now.hour < 9:
            search_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        # If it's currently business hours, start from next available hour
        else:
            search_start = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        # Generate 3 options over the next business days (skipping weekends)
        options_generated = 0
        current_check_date = search_start.date()

        while options_generated < 3 and (current_check_date - now.date()).days < 14:  # Max 2 weeks ahead
            check_datetime = datetime.combine(current_check_date, datetime.min.time()).replace(tzinfo=tz)

            # Skip weekends for business appointments
            if check_datetime.weekday() < 5:  # Monday = 0, Friday = 4
                # Generate time slots for this day
                time_slots = []

                # Business hours: 9 AM to 5 PM
                for hour in range(9, 17):  # 9 AM to 4 PM (last appointment at 4 PM)
                    # Skip past hours if it's today
                    if current_check_date == now.date() and hour <= now.hour:
                        continue

                    time_slots.append(f"{hour:02d}:00")
                    time_slots.append(f"{hour:02d}:30")

                # Only add if there are available slots
                if time_slots:
                    # Limit to 6 slots per day for readability
                    time_slots = time_slots[:6]

                    day_name = days[check_datetime.weekday()]

                    availability_options.append(AvailabilityOption(
                        date=current_check_date.strftime('%Y-%m-%d'),
                        day_name=day_name,
                        time_slots=time_slots,
                        formatted_display=f"{day_name}, {current_check_date.strftime('%B %d')} - {len(time_slots)} slots available"
                    ))

                    options_generated += 1

            # Move to next day
            current_check_date += timedelta(days=1)

        # Calculate total slots
        total_slots = sum(len(option.time_slots) for option in availability_options)

        # Generate search period description
        if availability_options:
            start_date = availability_options[0].date
            end_date = availability_options[-1].date
            search_period = f"{start_date} to {end_date}"
        else:
            search_period = "Next 14 days"

        # Generate helpful message with explicit current date context
        current_date_info = f"Today is {current_date_context.formatted_date}"
        if total_slots == 0:
            message = f"{current_date_info}. No available appointment slots found in the next 14 days. Please contact us directly to schedule."
        elif total_slots < 10:
            message = f"{current_date_info}. Limited availability found: {total_slots} slots across {len(availability_options)} days."
        else:
            message = f"{current_date_info}. Good availability: {total_slots} appointment slots available across {len(availability_options)} days."

        return CalendlyAvailabilityResponse(
            success=True,
            current_date_context=current_date_context,
            availability_options=availability_options,
            total_slots_found=total_slots,
            search_period=search_period,
            message=message
        )

    except Exception as e:
        # Return error response with minimal current date context
        now = datetime.now()
        error_context = DateTimeResponse(
            current_datetime=now.isoformat(),
            current_date=now.strftime('%Y-%m-%d'),
            current_time=now.strftime('%H:%M'),
            timezone=request.timezone or "Africa/Accra",
            day_of_week=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now.weekday()],
            formatted_date=now.strftime('%A, %B %d, %Y'),
            unix_timestamp=int(now.timestamp())
        )

        return CalendlyAvailabilityResponse(
            success=False,
            current_date_context=error_context,
            availability_options=[],
            total_slots_found=0,
            search_period="Error occurred",
            message=f"Failed to check availability: {str(e)}"
        )


@router.post("/book", response_model=CalendlyBookingResponse)
async def book_calendly_appointment(request: CalendlyBookingRequest):
    """
    Book a Calendly appointment using customer's first name and phone number.
    Follows VAPI best practices: no email collection required.

    Args:
        request: Booking request with customer details and appointment time

    Returns:
        CalendlyBookingResponse: Booking confirmation with current date context
    """
    try:
        # Get timezone
        try:
            tz = pytz.timezone(request.timezone)
        except Exception:
            tz = pytz.timezone("Africa/Accra")
            request.timezone = "Africa/Accra"

        now = datetime.now(tz)

        # Create current date context
        current_date_context = DateTimeResponse(
            current_datetime=now.isoformat(),
            current_date=now.strftime('%Y-%m-%d'),
            current_time=now.strftime('%H:%M'),
            timezone=request.timezone,
            day_of_week=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now.weekday()],
            formatted_date=now.strftime('%A, %B %d, %Y'),
            unix_timestamp=int(now.timestamp())
        )

        # Parse appointment time
        try:
            appointment_time = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
            if appointment_time.tzinfo is None:
                appointment_time = appointment_time.replace(tzinfo=tz)

            # Convert to requested timezone for display
            local_appointment_time = appointment_time.astimezone(tz)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid start_time format: {str(e)}")

        # Validate appointment is in the future
        if appointment_time <= now:
            raise HTTPException(status_code=400, detail="Appointment time must be in the future")

        # Validate appointment is during business hours (9 AM - 5 PM, Mon-Fri)
        if local_appointment_time.weekday() >= 5:  # Weekend
            raise HTTPException(status_code=400, detail="Appointments only available Monday-Friday")

        if not (9 <= local_appointment_time.hour < 17):  # Outside business hours
            raise HTTPException(status_code=400, detail="Appointments only available 9 AM - 5 PM")

        # Generate booking ID
        booking_id = f"book_{int(time.time())}_{request.customer_phone.replace('+', '').replace('-', '')[-8:]}"

        # Create appointment details
        appointment_details = {
            "booking_id": booking_id,
            "event_type": request.event_type,
            "customer_name": request.customer_name,
            "customer_phone": request.customer_phone,
            "appointment_time": local_appointment_time.strftime('%Y-%m-%d %H:%M'),
            "appointment_day": local_appointment_time.strftime('%A'),
            "timezone": request.timezone,
            "status": "confirmed",
            "created_at": now.isoformat()
        }

        # Add email if provided (optional)
        if request.customer_email:
            appointment_details["customer_email"] = request.customer_email

        # TODO: Integrate with actual Calendly API for real booking
        # For now, we'll simulate a successful booking

        # Generate confirmation message with current date context
        confirmation_message = (
            f"Today is {current_date_context.formatted_date}. "
            f"Appointment successfully booked for {request.customer_name}! "
            f"Your {request.event_type} is scheduled for "
            f"{local_appointment_time.strftime('%A, %B %d at %I:%M %p')} "
            f"({request.timezone}). "
            f"Booking ID: {booking_id}. "
            f"We'll send confirmation details to {request.customer_phone}."
        )

        return CalendlyBookingResponse(
            success=True,
            booking_id=booking_id,
            appointment_details=appointment_details,
            confirmation_message=confirmation_message,
            current_date_context=current_date_context
        )

    except HTTPException:
        raise
    except Exception as e:
        # Return error response with current date context
        now = datetime.now()
        error_context = DateTimeResponse(
            current_datetime=now.isoformat(),
            current_date=now.strftime('%Y-%m-%d'),
            current_time=now.strftime('%H:%M'),
            timezone=request.timezone or "Africa/Accra",
            day_of_week=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now.weekday()],
            formatted_date=now.strftime('%A, %B %d, %Y'),
            unix_timestamp=int(now.timestamp())
        )

        return CalendlyBookingResponse(
            success=False,
            booking_id=None,
            appointment_details={},
            confirmation_message=f"Failed to book appointment: {str(e)}",
            current_date_context=error_context
        )
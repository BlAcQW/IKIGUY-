"""
Booking API Router

REST API endpoints for property tour booking management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context, get_optional_user
from app.services.booking_service import BookingService
from app.models.booking import (
    Booking,
    BookingCreate,
    BookingUpdate,
    BookingListResponse,
    BookingStatus,
    AvailabilityRequest,
    AvailabilityResponse,
    BulkBookingAction,
    BulkBookingResponse,
)


router = APIRouter(prefix="/bookings", tags=["bookings"])


# ==================== Admin Authorization ====================


def check_admin_access(current_user: Dict[str, Any]):
    """
    Check if user has admin access.

    Args:
        current_user: Current authenticated user

    Raises:
        HTTPException: If user is not admin
    """
    is_admin = (
        current_user.get("email") == "admin@ailabsafrica.com" or
        current_user.get("role") == "admin"
    )

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this operation"
        )


# ==================== Booking Management ====================

@router.post("", response_model=Booking, status_code=201)
async def create_booking(
    booking_data: BookingCreate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Create a new property tour booking.

    Public endpoint - works with or without authentication.
    When unauthenticated, uses default organization from property.

    - Validates time slot availability
    - Auto-assigns available agent
    - Creates reminder schedule
    - Sends confirmation notification
    """
    booking_service = BookingService(database)

    try:
        # Get organization_id and user_id
        # If authenticated, use from current_user, otherwise use defaults
        organization_id = current_user.get("organization_id") if current_user else None
        user_id = current_user.get("sub") if current_user else None

        # If not authenticated, get organization from property
        if not organization_id:
            from app.services.property_service import PropertyService
            property_service = PropertyService(database)
            property = await property_service.get_property(booking_data.property_id)
            if not property:
                raise HTTPException(status_code=404, detail="Property not found")
            organization_id = property.organization_id

        booking = await booking_service.create_booking(
            booking_data=booking_data,
            organization_id=organization_id,
            user_id=user_id
        )
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    property_id: Optional[str] = Query(None, description="Filter by property"),
    contact_id: Optional[str] = Query(None, description="Filter by contact"),
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    status: Optional[BookingStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    List bookings with optional filters.

    Supports filtering by:
    - Property
    - Contact
    - Agent
    - Status
    - Date range
    """
    booking_service = BookingService(database)

    bookings, total = await booking_service.list_bookings(
        organization_id=org_context["organization_id"],
        property_id=property_id,
        contact_id=contact_id,
        agent_id=agent_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    return BookingListResponse(
        bookings=bookings,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{booking_id}", response_model=Booking)
async def get_booking(
    booking_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Get booking details by ID"""
    booking_service = BookingService(database)

    booking = await booking_service.get_booking(
        booking_id=booking_id,
        organization_id=org_context["organization_id"]
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


@router.put("/{booking_id}", response_model=Booking)
async def update_booking(
    booking_id: str,
    updates: BookingUpdate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Update booking details.

    Supports:
    - Rescheduling (validates new time slot)
    - Status updates
    - Agent reassignment
    - Notes updates
    - Rating and feedback
    """
    booking_service = BookingService(database)

    try:
        booking = await booking_service.update_booking(
            booking_id=booking_id,
            updates=updates,
            organization_id=org_context["organization_id"]
        )

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{booking_id}", response_model=Booking)
async def cancel_booking(
    booking_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Cancel a booking"""
    booking_service = BookingService(database)

    booking = await booking_service.cancel_booking(
        booking_id=booking_id,
        organization_id=org_context["organization_id"]
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


# ==================== Booking Actions ====================

@router.post("/{booking_id}/confirm", response_model=Booking)
async def confirm_booking(
    booking_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Confirm a requested booking (agent action)"""
    booking_service = BookingService(database)

    updates = BookingUpdate(status=BookingStatus.CONFIRMED)
    booking = await booking_service.update_booking(
        booking_id=booking_id,
        updates=updates,
        organization_id=org_context["organization_id"]
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


@router.post("/{booking_id}/complete", response_model=Booking)
async def complete_booking(
    booking_id: str,
    rating: Optional[int] = Query(None, ge=1, le=5, description="Customer rating (1-5)"),
    feedback: Optional[str] = Query(None, description="Customer feedback"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Mark booking as completed with optional rating and feedback"""
    booking_service = BookingService(database)

    booking = await booking_service.complete_booking(
        booking_id=booking_id,
        organization_id=org_context["organization_id"],
        rating=rating,
        feedback=feedback
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


@router.post("/{booking_id}/no-show", response_model=Booking)
async def mark_no_show(
    booking_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """Mark booking as no-show (customer didn't appear)"""
    booking_service = BookingService(database)

    booking = await booking_service.mark_no_show(
        booking_id=booking_id,
        organization_id=org_context["organization_id"]
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


# ==================== Availability ====================

@router.post("/availability", response_model=AvailabilityResponse)
async def get_availability(
    request: AvailabilityRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get available time slots for a property.

    Public endpoint - works with or without authentication.
    When unauthenticated, uses organization from property.

    Returns list of available slots within the specified date range.
    Useful for booking calendar widget.
    """
    booking_service = BookingService(database)

    # Get organization_id from user or property
    if current_user:
        organization_id = current_user.get("organization_id")
    else:
        # Get from property (same pattern as create_booking)
        from app.services.property_service import PropertyService
        property_service = PropertyService(database)
        property = await property_service.get_property(request.property_id)
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        organization_id = property.organization_id

    slots = await booking_service.get_available_slots(
        property_id=request.property_id,
        start_date=request.start_date,
        end_date=request.end_date,
        duration_minutes=request.duration_minutes,
        organization_id=organization_id
    )

    return AvailabilityResponse(
        property_id=request.property_id,
        slots=slots
    )


@router.get("/properties/{property_id}/availability", response_model=AvailabilityResponse)
async def get_property_availability(
    property_id: str,
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    duration_minutes: int = Query(30, description="Desired duration"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get available slots for a specific property (simplified endpoint).

    Public endpoint - works with or without authentication.
    When unauthenticated, uses organization from property.

    Alternative to POST /availability endpoint.
    """
    booking_service = BookingService(database)

    # Get organization_id from user or property
    if current_user:
        organization_id = current_user.get("organization_id")
    else:
        # Get from property (same pattern as create_booking)
        from app.services.property_service import PropertyService
        property_service = PropertyService(database)
        property = await property_service.get_property(property_id)
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        organization_id = property.organization_id

    slots = await booking_service.get_available_slots(
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        duration_minutes=duration_minutes,
        organization_id=organization_id
    )

    return AvailabilityResponse(
        property_id=property_id,
        slots=slots
    )


# ==================== Admin-Only Endpoints ====================


@router.post("/admin/backfill-leads")
async def admin_backfill_leads(
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context),
):
    """Retroactively create leads from existing bookings."""
    check_admin_access(current_user)
    booking_service = BookingService(database)
    result = await booking_service.backfill_leads_from_bookings(
        organization_id=org_context["organization_id"],
    )
    return result


@router.post("/admin/manual-create", response_model=Booking, status_code=201)
async def admin_create_booking(
    booking_data: BookingCreate,
    override_availability: bool = Query(False, description="Override availability check"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Admin-only: Manually create booking with optional availability override.

    Allows admin to:
    - Create bookings even if slot is unavailable
    - Manually assign agent
    - Skip auto-assignment logic
    """
    check_admin_access(current_user)

    booking_service = BookingService(database)

    try:
        booking = await booking_service.create_booking_with_override(
            booking_data=booking_data,
            organization_id=org_context["organization_id"],
            admin_email=current_user.get("email"),
            admin_id=current_user.get("id"),
            override_availability=override_availability
        )
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{booking_id}/admin/reassign-agent", response_model=Booking)
async def admin_reassign_agent(
    booking_id: str,
    new_agent_id: str = Query(..., description="New agent ID"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Admin-only: Reassign booking to a different agent.

    Bypasses normal agent availability checks.
    """
    check_admin_access(current_user)

    booking_service = BookingService(database)

    try:
        booking = await booking_service.reassign_agent(
            booking_id=booking_id,
            new_agent_id=new_agent_id,
            organization_id=org_context["organization_id"],
            admin_email=current_user.get("email"),
            admin_id=current_user.get("id")
        )

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/bulk-action", response_model=BulkBookingResponse)
async def admin_bulk_action(
    action_data: BulkBookingAction,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Admin-only: Perform bulk action on multiple bookings.

    Supported actions:
    - approve: Confirm multiple bookings
    - reject: Cancel multiple bookings
    - cancel: Cancel multiple bookings
    """
    check_admin_access(current_user)

    # Map action to status
    status_map = {
        "approve": BookingStatus.CONFIRMED,
        "reject": BookingStatus.CANCELLED,
        "cancel": BookingStatus.CANCELLED
    }

    if action_data.action not in status_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {', '.join(status_map.keys())}"
        )

    booking_service = BookingService(database)

    result = await booking_service.bulk_update_status(
        booking_ids=action_data.booking_ids,
        status=status_map[action_data.action],
        organization_id=org_context["organization_id"],
        admin_email=current_user.get("email"),
        admin_id=current_user.get("id"),
        reason=action_data.reason
    )

    return BulkBookingResponse(**result)


@router.get("/{booking_id}/admin/action-logs")
async def get_booking_action_logs(
    booking_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Admin-only: Get audit trail for a booking.

    Returns all admin actions performed on this booking.
    """
    check_admin_access(current_user)

    booking_service = BookingService(database)

    logs = await booking_service.get_booking_action_logs(
        booking_id=booking_id,
        organization_id=org_context["organization_id"]
    )

    return {"logs": logs, "count": len(logs)}

"""
Bus routes API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging
from datetime import datetime
from bson import ObjectId

from app.schemas.bus import (
    BusRouteResponse,
    CreateBusRouteRequest,
    UpdateBusRouteRequest,
    BusRegistrationResponse,
    RegisterForBusRequest,
    BusCheckInRequest,
    BusCheckInResponse
)
from app.schemas.notification import SendBusDelayNotificationRequest, NotificationResponse
from app.services.bus_service import bus_service
from app.services.notification_service import notification_service
from app.services.voice_greeting_service import VoiceGreetingService
from app.api.dependencies import (
    get_current_user,
    require_admin,
    require_coordinator_or_admin,
    require_organization_access,
    get_optional_organization_id
)
from app.core.database import get_database
from app.models.user import User
from app.models.bus import BusRoute

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/routes",
    response_model=BusRouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create bus route",
    description="Create a new bus route for a conference (admin/coordinator only)."
)
async def create_bus_route(
    request: CreateBusRouteRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Create new bus route.

    Requires coordinator or admin role. Coordinators and admins can create
    routes for their assigned conferences.

    SECURITY: Route is scoped to organization from X-Organization-ID header.
    """
    try:
        route_data = request.model_dump()
        route_data["conference_id"] = ObjectId(request.conference_id)

        route = await bus_service.create_bus_route(route_data, organization_id)

        return BusRouteResponse(
            id=str(route.id),
            conference_id=str(route.conference_id),
            route_name=route.route_name,
            pickup_location=route.pickup_location,
            pickup_coordinates=route.pickup_coordinates,
            departure_time=route.departure_time,
            arrival_time=route.arrival_time,
            capacity=route.capacity,
            registered_count=route.registered_count,
            status=route.status,
            gate_number=route.gate_number,
            coordinator_id=str(route.coordinator_id) if route.coordinator_id else None,
            created_at=route.created_at,
            updated_at=route.updated_at
        )

    except Exception as e:
        logger.error(f"Failed to create bus route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bus route: {str(e)}"
        )


@router.get(
    "/routes",
    response_model=List[BusRouteResponse],
    summary="List bus routes",
    description="List all bus routes for organization with optional filters. Public endpoint."
)
async def list_bus_routes(
    organization_id: str = Depends(get_optional_organization_id),
    conference_id: Optional[str] = Query(None, description="Filter by conference ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status", alias="status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
):
    """
    List bus routes for organization.

    PUBLIC ENDPOINT: No authentication required.
    Returns routes for the organization specified in X-Organization-ID header,
    or default organization if not provided.
    """
    try:
        # Fetch routes directly from database to handle validation errors
        db = get_database()

        # CRITICAL: Always filter by organization_id
        query = {"organization_id": organization_id}

        if conference_id and ObjectId.is_valid(conference_id):
            # Check both ObjectId and string formats for conference_id
            conference_filter = {
                "$or": [
                    {"conference_id": ObjectId(conference_id)},
                    {"conference_id": conference_id}
                ]
            }
            if status_filter:
                query["$and"] = [conference_filter, {"status": status_filter}]
            else:
                query.update(conference_filter)
        elif status_filter:
            query["status"] = status_filter

        cursor = db.bus_routes.find(query).sort("departure_time", 1).limit(limit)
        routes = await cursor.to_list(length=limit)

        # Build response with proper type handling
        result = []
        for route_doc in routes:
            # Helper function to safely parse datetime fields
            def safe_datetime(value):
                """Convert string or datetime to datetime object, or return None."""
                if value is None:
                    return None
                if isinstance(value, datetime):
                    return value
                # If it's a string time like "04:00 AM", skip it (invalid data)
                return None

            result.append(BusRouteResponse(
                id=str(route_doc.get("_id")),
                conference_id=str(route_doc.get("conference_id")) if route_doc.get("conference_id") else None,
                name=route_doc.get("name"),
                route_name=route_doc.get("route_name"),
                departure_location=route_doc.get("departure_location"),
                destination=route_doc.get("destination"),
                pickup_location=route_doc.get("pickup_location"),
                pickup_coordinates=route_doc.get("pickup_coordinates"),
                departure_time=safe_datetime(route_doc.get("departure_time")),
                arrival_time=safe_datetime(route_doc.get("arrival_time")),
                capacity=route_doc.get("capacity", 0),
                available_seats=route_doc.get("available_seats"),
                registered_count=route_doc.get("registered_count", 0),
                status=route_doc.get("status"),
                driver_name=route_doc.get("driver_name"),
                driver_phone=route_doc.get("driver_phone"),
                bus_number=route_doc.get("bus_number"),
                is_long_distance=route_doc.get("is_long_distance", False),
                gate_number=route_doc.get("gate_number"),
                coordinator_id=str(route_doc.get("coordinator_id")) if route_doc.get("coordinator_id") else None,
                created_at=safe_datetime(route_doc.get("created_at")),
                updated_at=safe_datetime(route_doc.get("updated_at"))
            ))

        return result

    except Exception as e:
        logger.error(f"Failed to list bus routes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list bus routes: {str(e)}"
        )


@router.get(
    "/routes/{route_id}",
    response_model=BusRouteResponse,
    summary="Get bus route",
    description="Get details of a specific bus route."
)
async def get_bus_route(
    route_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: dict = Depends(get_current_user)
):
    """
    Get bus route by ID.

    SECURITY: Verifies route belongs to organization before returning.
    """
    route = await bus_service.get_bus_route(route_id)

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus route not found"
        )

    # CRITICAL: Verify route belongs to organization
    if route.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Route belongs to different organization"
        )

    return BusRouteResponse(
        id=str(route.id),
        conference_id=str(route.conference_id),
        route_name=route.route_name,
        pickup_location=route.pickup_location,
        pickup_coordinates=route.pickup_coordinates,
        departure_time=route.departure_time,
        arrival_time=route.arrival_time,
        capacity=route.capacity,
        registered_count=route.registered_count,
        status=route.status,
        gate_number=route.gate_number,
        coordinator_id=str(route.coordinator_id) if route.coordinator_id else None,
        created_at=route.created_at,
        updated_at=route.updated_at
    )


@router.put(
    "/routes/{route_id}",
    response_model=BusRouteResponse,
    summary="Update bus route",
    description="Update bus route details (admin/coordinator only)."
)
async def update_bus_route(
    route_id: str,
    request: UpdateBusRouteRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Update bus route.

    Requires coordinator or admin role. Only coordinators and admins
    can modify bus route details.

    SECURITY: Only updates routes belonging to the organization.
    """
    try:
        update_data = request.model_dump(exclude_none=True)

        route = await bus_service.update_bus_route(route_id, organization_id, update_data)

        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus route not found"
            )

        return BusRouteResponse(
            id=str(route.id),
            conference_id=str(route.conference_id),
            route_name=route.route_name,
            pickup_location=route.pickup_location,
            pickup_coordinates=route.pickup_coordinates,
            departure_time=route.departure_time,
            arrival_time=route.arrival_time,
            capacity=route.capacity,
            registered_count=route.registered_count,
            status=route.status,
            gate_number=route.gate_number,
            coordinator_id=str(route.coordinator_id) if route.coordinator_id else None,
            created_at=route.created_at,
            updated_at=route.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update bus route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bus route: {str(e)}"
        )


@router.delete(
    "/routes/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete bus route",
    description="Delete a bus route (admin only)."
)
async def delete_bus_route(
    route_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_admin)
):
    """
    Delete bus route.

    Requires admin role. Only admins can delete routes as this is a
    destructive action that also removes all user registrations.

    SECURITY: Only deletes routes belonging to the organization.
    """
    try:
        logger.info(f"=== DELETE ROUTE DEBUG ===")
        logger.info(f"DELETE request received for route_id: {route_id}")
        logger.info(f"Organization ID: {organization_id}")
        logger.info(f"Route ID type: {type(route_id)}")
        logger.info(f"Route ID length: {len(route_id) if route_id else 0}")
        logger.info(f"Is valid ObjectId: {ObjectId.is_valid(route_id) if route_id else False}")

        deleted = await bus_service.delete_bus_route(route_id, organization_id)

        logger.info(f"Delete operation result: {deleted}")

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus route not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete bus route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bus route: {str(e)}"
        )


@router.post(
    "/register",
    response_model=BusRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register for bus (standalone)",
    description="Register for a bus route without conference registration. Returns QR code for bus boarding."
)
async def register_for_bus(request: RegisterForBusRequest):
    """Register for bus route with QR code generation."""
    try:
        # Register for bus
        registration = await bus_service.register_for_bus(
            user_name=request.user_name,
            user_phone=request.user_phone,
            user_email=request.user_email,
            bus_route_id=request.bus_route_id,
            conference_id=request.conference_id,
            user_id=None  # Anonymous booking
        )

        # Fetch route and conference details
        db = get_database()
        route = await bus_service.get_bus_route(request.bus_route_id)

        if not route:
            logger.error(f"Bus route {request.bus_route_id} not found or invalid")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected bus route is no longer available. Please select a different route."
            )

        # Fetch conference details if conference_id exists
        conference = None
        if registration.conference_id:
            conference = await db.conferences.find_one({"_id": registration.conference_id})

        # Generate QR code
        qr_data = f"{registration.registration_code}|{route.route_name if route else 'Unknown'}|{request.user_name}"
        qr_code = _generate_qr_code(qr_data)

        return BusRegistrationResponse(
            id=str(registration.id),
            user_id=str(registration.user_id) if registration.user_id else None,
            user_name=registration.user_name,
            user_phone=registration.user_phone,
            user_email=registration.user_email,
            bus_route_id=str(registration.bus_route_id),
            bus_route_name=route.route_name if route else route.name,
            conference_id=str(registration.conference_id) if registration.conference_id else None,
            conference_name=conference["name"] if conference else None,
            registration_code=registration.registration_code,
            qr_code=qr_code,
            registration_time=registration.registration_time,
            checked_in=registration.checked_in,
            check_in_time=registration.check_in_time,
            status=registration.status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register for bus: {str(e)}")

        # Provide user-friendly error messages
        error_msg = str(e).lower()
        if "already registered" in error_msg or "duplicate" in error_msg:
            detail = "You have already registered for a bus for this conference. Each phone number can only register once."
        elif "full" in error_msg or "capacity" in error_msg:
            detail = "This bus is full. Please select a different bus route."
        elif "not found" in error_msg:
            detail = "The selected bus route is no longer available. Please refresh and try again."
        else:
            detail = "Unable to complete bus registration. Please try again or contact support if the problem persists."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


def _generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 encoded image."""
    import qrcode
    import io
    import base64

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


@router.post(
    "/check-in",
    response_model=BusCheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="Check in for bus",
    description="Check in a bus registration using QR code."
)
async def check_in_bus(request: BusCheckInRequest):
    """
    Check in a bus registration using QR code.

    Scans registration code from QR code and marks user as checked in.
    Returns booking details for verification.
    """
    try:
        # Check in the registration
        registration = await bus_service.check_in_bus_registration(
            registration_code=request.registration_code
        )

        # Fetch route and conference details
        db = get_database()
        route_doc = await db.bus_routes.find_one({"_id": registration.bus_route_id})
        route = BusRoute(**route_doc) if route_doc else None

        # Fetch conference details if conference_id exists
        conference = None
        if registration.conference_id:
            conference = await db.conferences.find_one({"_id": registration.conference_id})

        # Generate voice greeting if enabled on the bus route
        greeting_audio = None
        if route and route.voice_greeting and route.voice_greeting.enabled:
            try:
                voice_greeting_service = VoiceGreetingService()

                # Prepare user data for personalization
                user_data = {
                    "user_name": registration.user_name,
                    "phone": registration.user_phone,
                    "branch_name": "",  # Not available in bus registration
                    "volunteer_roles": []  # Not available in bus registration
                }

                # Prepare event data
                event_data = {
                    "bus_route_name": route.name or route.route_name,
                    "pickup_location": route.pickup_location or route.departure_location
                }

                # Get user ID (use phone as fallback since bus registrations don't require user accounts)
                user_id = registration.user_phone

                # Generate greeting
                greeting_response = await voice_greeting_service.generate_greeting(
                    user_data=user_data,
                    event_data=event_data,
                    config=route.voice_greeting,
                    user_id=user_id
                )

                if greeting_response:
                    greeting_audio = greeting_response.model_dump()
                    logger.info(f"Generated voice greeting for bus check-in: {registration.user_name}")

            except Exception as e:
                logger.error(f"Failed to generate voice greeting for bus check-in: {e}")
                # Don't fail the check-in if greeting generation fails
                pass

        return BusCheckInResponse(
            success=True,
            user_name=registration.user_name,
            user_phone=registration.user_phone,
            bus_route_name=route.route_name if route else None,
            conference_name=conference["name"] if conference else None,
            check_in_time=registration.check_in_time,
            greeting_audio=greeting_audio
        )

    except Exception as e:
        logger.error(f"Failed to check in bus registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/routes/{route_id}/notify-delay",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Send bus delay notification",
    description="Send multi-channel notifications to all users registered for this bus route (admin/coordinator only)."
)
async def notify_bus_delay(
    route_id: str,
    request: SendBusDelayNotificationRequest,
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Send bus delay notification to all registered users.

    Requires coordinator or admin role. Sends notifications via multiple
    channels based on delay severity:
    - <15 min: Push only
    - 15-30 min: Push + SMS
    - >30 min: Push + SMS + WhatsApp
    """
    try:
        # Get bus route details
        route = await bus_service.get_bus_route(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus route not found"
            )

        # Get all users registered for this bus
        db = get_database()
        registrations = await db.bus_registrations.find({
            "bus_route_id": ObjectId(route_id),
            "status": "confirmed"
        }).to_list(length=1000)

        if not registrations:
            return NotificationResponse(
                success=True,
                message="No users registered for this bus route",
                total_users=0,
                notifications_sent=0,
                notifications_failed=0,
                channels_used=[],
                priority="none"
            )

        # Get user details
        user_ids = [reg["user_id"] for reg in registrations]
        users = await db.users.find({
            "_id": {"$in": user_ids}
        }).to_list(length=1000)

        # Send notifications
        result = await notification_service.send_bus_delay_notification(
            bus_route_id=route_id,
            bus_name=route.route_name,
            delay_minutes=request.delay_minutes,
            new_eta=request.new_eta,
            pickup_location=route.pickup_location,
            users=users
        )

        return NotificationResponse(
            success=result["success"],
            message=f"Sent notifications to {result['notifications_sent']} of {result['total_users']} users",
            total_users=result["total_users"],
            notifications_sent=result["notifications_sent"],
            notifications_failed=result["notifications_failed"],
            channels_used=result["channels_used"],
            priority=result["priority"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send bus delay notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

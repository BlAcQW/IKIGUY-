"""
Conference registration API routes.

Endpoints for managing conference registrations with QR code generation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient
import os
import qrcode
import io
import base64
import secrets
import logging
import math

from app.services.voice_greeting_service import VoiceGreetingService
from app.services.registration_cache import get_cache
from app.services.session_attendance_service import session_attendance_service
from app.api.dependencies import require_admin, require_coordinator_or_admin
from app.models.user import User
from app.utils.phone import normalize_phone_number, validate_phone_number

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Registrations"])


async def generate_voice_greeting_async(
    registration_id: str,
    user_data: dict,
    event_data: dict,
    voice_config: dict,
    user_id: str
):
    """
    Background task to generate voice greeting after check-in.

    This allows check-in to return immediately while greeting generates in background.

    Args:
        registration_id: Registration ID to update with greeting
        user_data: User data for personalization
        event_data: Event data for context
        voice_config: Voice greeting configuration
        user_id: User ID for caching
    """
    try:
        logger.info(f"🎵 [BACKGROUND] Generating voice greeting for registration {registration_id}")

        voice_greeting_service = VoiceGreetingService()

        from app.models.voice_greeting import VoiceGreetingConfig
        config = VoiceGreetingConfig(**voice_config) if voice_config else VoiceGreetingConfig()

        greeting_response = await voice_greeting_service.generate_greeting(
            user_data=user_data,
            event_data=event_data,
            config=config,
            user_id=user_id
        )

        if greeting_response:
            # Store greeting in database for future retrieval
            db = get_db()
            db.conference_registrations.update_one(
                {"_id": ObjectId(registration_id)},
                {
                    "$set": {
                        "voice_greeting": greeting_response.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"✅ [BACKGROUND] Voice greeting generated and stored for registration {registration_id}")
        else:
            logger.warning(f"⚠️  [BACKGROUND] Voice greeting generation returned None for registration {registration_id}")

    except Exception as e:
        logger.error(f"❌ [BACKGROUND] Failed to generate voice greeting for registration {registration_id}: {e}", exc_info=True)

# MongoDB connection
def get_db():
    """Get MongoDB database connection."""
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
    )
    client = MongoClient(mongodb_url)
    return client.churchflow


# Request/Response Models
class CreateRegistrationRequest(BaseModel):
    """Request model for creating a conference registration."""
    conference_id: str
    user_phone: str
    user_name: str
    user_email: Optional[str] = None
    branch_id: Optional[str] = None
    church_name: Optional[str] = Field(None, min_length=3, max_length=200)
    requires_bus: bool = False
    bus_route_id: Optional[str] = None
    special_needs: Optional[str] = None
    emergency_contact: Optional[str] = None
    # Optional fields for on-site session check-in
    session_id: Optional[str] = Field(None, description="Optional session ID to check into immediately")
    latitude: Optional[float] = Field(None, description="User's GPS latitude for validation")
    longitude: Optional[float] = Field(None, description="User's GPS longitude for validation")

    def validate_branch_or_church(self):
        """Validate that at least one of branch_id or church_name is provided."""
        if not self.branch_id and not self.church_name:
            raise ValueError("Either branch_id or church_name must be provided")
        if self.branch_id and self.church_name:
            raise ValueError("Only one of branch_id or church_name can be provided, not both")
        return self


class UpdateRegistrationRequest(BaseModel):
    """Request model for updating a registration."""
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    church_name: Optional[str] = None
    requires_bus: Optional[bool] = None
    bus_route_id: Optional[str] = None
    special_needs: Optional[str] = None
    checked_in: Optional[bool] = None


class RegistrationResponse(BaseModel):
    """Response model for a registration."""
    id: str
    conference_id: str
    conference_name: str
    user_phone: str
    user_name: str
    user_email: Optional[str] = None
    branch_id: Optional[str] = None
    branch_name: Optional[str] = None
    church_name: Optional[str] = None  # For non-branch members
    registration_code: str
    qr_code: Optional[str] = None  # Base64 encoded QR code image
    requires_bus: bool = False
    bus_route_id: Optional[str] = None
    bus_route_name: Optional[str] = None
    pickup_location: Optional[str] = None
    special_needs: Optional[str] = None
    emergency_contact: Optional[str] = None
    checked_in: bool = False
    checked_in_at: Optional[str] = None
    created_at: str
    status: str  # pending, confirmed, cancelled
    greeting_audio: Optional[dict] = None  # Voice greeting audio data
    is_repeat_checkin: bool = False  # True if user was already checked in
    # Conference location details for location-based check-in
    venue: Optional[str] = None
    venue_latitude: Optional[float] = None
    venue_longitude: Optional[float] = None
    venue_checkin_radius: Optional[int] = None  # in meters
    self_checkin_enabled: bool = True
    # Session check-in fields (for on-site registration)
    session_checked_in: Optional[bool] = None  # True if checked into a session during registration
    session_name: Optional[str] = None  # Name of session checked into
    session_check_in_warning: Optional[str] = None  # Warning message if session check-in failed
    # Conference dates (for checking if conference is ongoing)
    conference_start_date: Optional[str] = None
    conference_end_date: Optional[str] = None


class RegistrationStats(BaseModel):
    """Aggregate statistics for registrations."""
    total: int = Field(0, description="Total number of registrations")
    confirmed: int = Field(0, description="Number of confirmed registrations")
    pending: int = Field(0, description="Number of pending registrations")
    cancelled: int = Field(0, description="Number of cancelled registrations")
    checked_in: int = Field(0, description="Number of checked-in registrations")
    requires_bus: int = Field(0, description="Number requiring bus transportation")


class PaginatedRegistrationResponse(BaseModel):
    """Paginated response model for registrations."""
    items: List[RegistrationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    stats: Optional[RegistrationStats] = None  # Aggregate stats for all matching registrations
    conference_start_date: Optional[str] = None
    conference_end_date: Optional[str] = None


class CheckInRequest(BaseModel):
    """Request model for checking in with QR code."""
    registration_code: str
    is_self_checkin: bool = False  # True if checking in via self-service page
    latitude: Optional[float] = None  # User's current latitude for location-based check-in
    longitude: Optional[float] = None  # User's current longitude for location-based check-in


def generate_registration_code() -> str:
    """Generate a unique registration code."""
    return f"REG-{secrets.token_urlsafe(8).upper()}"


def generate_qr_code(data: str) -> str:
    """
    Generate QR code and return as base64 encoded image.

    Args:
        data: Data to encode in QR code

    Returns:
        Base64 encoded PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        Distance in meters
    """
    # Reason: Earth's radius in meters
    R = 6371000

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


@router.post("/", response_model=RegistrationResponse, status_code=201)
async def create_registration(request: CreateRegistrationRequest):
    """
    Create a new conference registration.

    Args:
        request: Registration data

    Returns:
        Created registration with QR code
    """
    # Log incoming request for debugging
    print(f"Registration request received: {request.model_dump()}")

    # Validate branch or church name is provided
    try:
        request.validate_branch_or_church()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = get_db()

    # Validate conference exists
    if not ObjectId.is_valid(request.conference_id):
        raise HTTPException(status_code=400, detail="Invalid conference ID")

    conference = db.conferences.find_one({"_id": ObjectId(request.conference_id)})
    if not conference:
        raise HTTPException(status_code=404, detail="Conference not found")

    # Check if registration is still open
    if not conference.get("registration_open", False):
        raise HTTPException(status_code=400, detail="Registration is closed for this conference")

    # Check if user already registered - if so, return existing registration with QR code
    # Reason: Allow users to re-access their QR code if they forgot to download it
    existing = db.conference_registrations.find_one({
        "conference_id": ObjectId(request.conference_id),
        "user_phone": request.user_phone,
        "status": {"$ne": "cancelled"}
    })
    if existing:
        # Get related data for existing registration
        existing_branch = db.branches.find_one({"_id": existing["branch_id"]}) if existing.get("branch_id") else None
        existing_bus_route = db.bus_routes.find_one({"_id": existing["bus_route_id"]}) if existing.get("bus_route_id") else None

        # Generate QR code with self-checkin URL
        frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
        qr_data = f"{frontend_url}/self-checkin?code={existing['registration_code']}"
        qr_code = generate_qr_code(qr_data)

        logger.info(f"Returning existing registration for phone {request.user_phone} - conference {request.conference_id}")

        return RegistrationResponse(
            id=str(existing["_id"]),
            conference_id=str(existing["conference_id"]),
            conference_name=conference["name"],
            user_phone=existing["user_phone"],
            user_name=existing["user_name"],
            user_email=existing.get("user_email"),
            branch_id=str(existing["branch_id"]) if existing.get("branch_id") else None,
            branch_name=existing_branch["name"] if existing_branch else None,
            church_name=existing.get("church_name"),
            registration_code=existing["registration_code"],
            qr_code=qr_code,
            requires_bus=existing.get("requires_bus", False),
            bus_route_id=str(existing["bus_route_id"]) if existing.get("bus_route_id") else None,
            bus_route_name=existing_bus_route.get("name") or existing_bus_route.get("route_name") if existing_bus_route else None,
            pickup_location=existing_bus_route.get("pickup_location") if existing_bus_route else None,
            special_needs=existing.get("special_needs"),
            emergency_contact=existing.get("emergency_contact"),
            checked_in=existing.get("checked_in", False),
            checked_in_at=existing["checked_in_at"].isoformat() if existing.get("checked_in_at") else None,
            created_at=existing["created_at"].isoformat(),
            status=existing.get("status", "confirmed"),
            greeting_audio=None  # Greetings only generated during check-in
        )

    # Validate branch if provided (only validate if not "other")
    branch = None
    if request.branch_id and request.branch_id != "other":
        if not ObjectId.is_valid(request.branch_id):
            raise HTTPException(status_code=400, detail="Invalid branch ID")

        branch = db.branches.find_one({"_id": ObjectId(request.branch_id)})
        if not branch:
            raise HTTPException(status_code=404, detail="Branch not found")

    # Validate bus route if provided
    bus_route = None
    if request.requires_bus and request.bus_route_id:
        if not ObjectId.is_valid(request.bus_route_id):
            raise HTTPException(status_code=400, detail="Invalid bus route ID")

        bus_route = db.bus_routes.find_one({"_id": ObjectId(request.bus_route_id)})
        if not bus_route:
            raise HTTPException(status_code=404, detail="Bus route not found")

    # Generate unique registration code
    registration_code = generate_registration_code()
    while db.conference_registrations.find_one({"registration_code": registration_code}):
        registration_code = generate_registration_code()

    # Determine branch_id and church_name based on input
    # Reason: If user selects "other", use church_name; otherwise use branch_id
    final_branch_id = None
    final_church_name = None

    if request.branch_id and request.branch_id != "other":
        final_branch_id = ObjectId(request.branch_id)
    elif request.church_name:
        final_church_name = request.church_name

    # OPTIMIZATION: Generate QR code once and store it (don't regenerate on every check-in)
    frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
    qr_data = f"{frontend_url}/self-checkin?code={registration_code}"
    qr_code = generate_qr_code(qr_data)

    # Create registration with QR code cached
    registration = {
        "conference_id": ObjectId(request.conference_id),
        "user_phone": request.user_phone,
        "user_name": request.user_name,
        "user_email": request.user_email,
        "branch_id": final_branch_id,
        "church_name": final_church_name,
        "registration_code": registration_code,
        "qr_code_base64": qr_code,  # Cache QR code to avoid regeneration
        "requires_bus": request.requires_bus,
        "bus_route_id": ObjectId(request.bus_route_id) if request.bus_route_id else None,
        "special_needs": request.special_needs,
        "emergency_contact": request.emergency_contact,
        "checked_in": False,
        "checked_in_at": None,
        "status": "confirmed",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {}
    }

    result = db.conference_registrations.insert_one(registration)
    registration["_id"] = result.inserted_id

    # Increment bus route registered count if bus is required
    if request.requires_bus and request.bus_route_id:
        db.bus_routes.update_one(
            {"_id": ObjectId(request.bus_route_id)},
            {
                "$inc": {"registered_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    # Invalidate cache for this conference
    # Reason: New registration affects stats and search results
    cache = await get_cache()
    await cache.invalidate_conference(request.conference_id)

    # Initialize session check-in fields
    session_checked_in = False
    session_name = None
    session_check_in_warning = None

    # Optional: Attempt session check-in if session_id provided (on-site registration)
    if request.session_id:
        try:
            logger.info(f"Attempting session check-in for registration {registration_code} to session {request.session_id}")

            # Use the member check-in service to check into session
            session_attendance = await session_attendance_service.member_check_in_by_code(
                session_id=request.session_id,
                registration_code=registration_code,
                latitude=request.latitude,
                longitude=request.longitude
            )

            # Session check-in successful
            session_checked_in = True
            session_name = session_attendance.get("session_name") if isinstance(session_attendance, dict) else getattr(session_attendance, "session_name", None)
            logger.info(f"Successfully checked into session {request.session_id} for registration {registration_code}")

        except Exception as e:
            # Log error but don't fail registration
            logger.warning(f"Session check-in failed for registration {registration_code}: {str(e)}")
            session_check_in_warning = f"Registration successful, but session check-in failed: {str(e)}"

    return RegistrationResponse(
        id=str(registration["_id"]),
        conference_id=str(registration["conference_id"]),
        conference_name=conference["name"],
        user_phone=registration["user_phone"],
        user_name=registration["user_name"],
        user_email=registration.get("user_email"),
        branch_id=str(registration["branch_id"]) if registration.get("branch_id") else None,
        branch_name=branch["name"] if branch else None,
        church_name=registration.get("church_name"),
        registration_code=registration["registration_code"],
        qr_code=qr_code,
        requires_bus=registration["requires_bus"],
        bus_route_id=str(registration["bus_route_id"]) if registration.get("bus_route_id") else None,
        bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
        pickup_location=bus_route.get("pickup_location") if bus_route else None,
        special_needs=registration.get("special_needs"),
        emergency_contact=registration.get("emergency_contact"),
        checked_in=registration["checked_in"],
        checked_in_at=None,
        created_at=registration["created_at"].isoformat(),
        status=registration["status"],
        greeting_audio=None,  # Greetings only generated during check-in
        # Session check-in fields
        session_checked_in=session_checked_in,
        session_name=session_name,
        session_check_in_warning=session_check_in_warning,
        # Conference dates for frontend to check if conference is ongoing
        conference_start_date=conference["start_date"].isoformat() if conference.get("start_date") else None,
        conference_end_date=conference["end_date"].isoformat() if conference.get("end_date") else None,
        # Venue information for location-based check-in
        venue=conference.get("venue"),
        venue_latitude=conference.get("venue_latitude"),
        venue_longitude=conference.get("venue_longitude"),
        venue_checkin_radius=conference.get("venue_checkin_radius", 1000),
        self_checkin_enabled=conference.get("self_checkin_enabled", True)
    )


@router.get("/", response_model=PaginatedRegistrationResponse)
async def list_registrations(
    conference_id: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    checked_in: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by name, phone, email, or registration code"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """
    List registrations with optional filters and pagination for infinite scroll.

    Args:
        conference_id: Filter by conference
        branch_id: Filter by branch
        checked_in: Filter by check-in status
        status: Filter by status (pending, confirmed, cancelled)
        search: Search by name, phone, email, or registration code
        limit: Number of items to return (default: 50, max: 100)
        offset: Number of items to skip (default: 0)

    Returns:
        Paginated list of registrations
    """
    db = get_db()
    cache = await get_cache()

    # Build filter
    filter_query = {}
    if conference_id:
        if not ObjectId.is_valid(conference_id):
            raise HTTPException(status_code=400, detail="Invalid conference ID")
        filter_query["conference_id"] = ObjectId(conference_id)

    if branch_id:
        if not ObjectId.is_valid(branch_id):
            raise HTTPException(status_code=400, detail="Invalid branch ID")
        filter_query["branch_id"] = ObjectId(branch_id)

    if checked_in is not None:
        filter_query["checked_in"] = checked_in

    if status:
        filter_query["status"] = status

    # Add search filter
    # Reason: Search across multiple fields using case-insensitive regex
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        filter_query["$or"] = [
            {"user_name": search_regex},
            {"user_phone": search_regex},
            {"user_email": search_regex},
            {"registration_code": search_regex}
        ]

    # Get total count
    total_count = db.conference_registrations.count_documents(filter_query)

    # Try to get stats from cache first
    # Reason: Stats aggregation is expensive, cache for 45s
    cached_stats = await cache.get_stats(conference_id, status, checked_in)

    if cached_stats:
        logger.debug("📦 Using cached stats")
        registration_stats = RegistrationStats(**cached_stats)
    else:
        logger.debug("🔄 Computing stats (cache miss)")
        # Calculate aggregate stats using MongoDB aggregation pipeline
        # Reason: Get accurate counts for all matching registrations, not just the current page
        stats_pipeline = [
            {"$match": filter_query},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "confirmed": {
                        "$sum": {"$cond": [{"$eq": ["$status", "confirmed"]}, 1, 0]}
                    },
                    "pending": {
                        "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                    },
                    "cancelled": {
                        "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                    },
                    "checked_in": {
                        "$sum": {"$cond": [{"$eq": ["$checked_in", True]}, 1, 0]}
                    },
                    "requires_bus": {
                        "$sum": {"$cond": [{"$eq": ["$requires_bus", True]}, 1, 0]}
                    }
                }
            }
        ]
        stats_result = list(db.conference_registrations.aggregate(stats_pipeline))

        if stats_result:
            stats_data = stats_result[0]
            registration_stats = RegistrationStats(
                total=stats_data.get("total", 0),
                confirmed=stats_data.get("confirmed", 0),
                pending=stats_data.get("pending", 0),
                cancelled=stats_data.get("cancelled", 0),
                checked_in=stats_data.get("checked_in", 0),
                requires_bus=stats_data.get("requires_bus", 0)
            )
        else:
            registration_stats = RegistrationStats()

        # Cache stats for 45 seconds
        await cache.set_stats(
            conference_id,
            status,
            checked_in,
            registration_stats.dict(),
            ttl=45
        )

    # Get registrations with pagination (sorted by created_at desc for newest first)
    registrations = list(
        db.conference_registrations
        .find(filter_query)
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )

    # Fetch related data
    conference_ids = set([r["conference_id"] for r in registrations])
    branch_ids = set([r.get("branch_id") for r in registrations if r.get("branch_id")])
    bus_route_ids = set([r.get("bus_route_id") for r in registrations if r.get("bus_route_id")])

    conferences = {c["_id"]: c for c in db.conferences.find({"_id": {"$in": list(conference_ids)}})}
    branches = {b["_id"]: b for b in db.branches.find({"_id": {"$in": list(branch_ids)}})}
    bus_routes = {br["_id"]: br for br in db.bus_routes.find({"_id": {"$in": list(bus_route_ids)}})}

    # Format response
    result = []
    for reg in registrations:
        conference = conferences.get(reg["conference_id"])
        branch = branches.get(reg.get("branch_id"))
        bus_route = bus_routes.get(reg.get("bus_route_id"))

        # Generate QR code with self-checkin URL
        frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
        qr_data = f"{frontend_url}/self-checkin?code={reg['registration_code']}"
        qr_code = generate_qr_code(qr_data)

        result.append(RegistrationResponse(
            id=str(reg["_id"]),
            conference_id=str(reg["conference_id"]),
            conference_name=conference["name"] if conference else "Unknown",
            user_phone=reg["user_phone"],
            user_name=reg["user_name"],
            user_email=reg.get("user_email"),
            branch_id=str(reg["branch_id"]) if reg.get("branch_id") else None,
            branch_name=branch["name"] if branch else None,
            church_name=reg.get("church_name"),
            registration_code=reg["registration_code"],
            qr_code=qr_code,
            requires_bus=reg.get("requires_bus", False),
            bus_route_id=str(reg["bus_route_id"]) if reg.get("bus_route_id") else None,
            bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
            pickup_location=bus_route.get("pickup_location") if bus_route else None,
            special_needs=reg.get("special_needs"),
            emergency_contact=reg.get("emergency_contact"),
            checked_in=reg.get("checked_in", False),
            checked_in_at=reg["checked_in_at"].isoformat() if reg.get("checked_in_at") else None,
            created_at=reg["created_at"].isoformat(),
            status=reg.get("status", "confirmed"),
            greeting_audio=None  # Greetings only generated during check-in
        ))

    # Calculate pagination metadata
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
    current_page = (offset // limit) + 1 if limit > 0 else 1

    return PaginatedRegistrationResponse(
        items=result,
        total=total_count,
        page=current_page,
        page_size=limit,
        total_pages=total_pages,
        stats=registration_stats
    )


@router.get("/export", response_model=List[RegistrationResponse])
async def export_all_registrations(
    conference_id: Optional[str] = Query(None, description="Filter by conference ID"),
    branch_id: Optional[str] = Query(None, description="Filter by branch ID"),
    checked_in: Optional[bool] = Query(None, description="Filter by check-in status"),
    status: Optional[str] = Query(None, description="Filter by status (pending, confirmed, cancelled)"),
    search: Optional[str] = Query(None, description="Search by name, phone, email, or registration code"),
    current_user: User = Depends(require_coordinator_or_admin),
):
    """
    Export ALL registrations matching filters (no pagination limit).

    Use this endpoint for CSV exports to get complete dataset.

    Args:
        conference_id: Filter by conference
        branch_id: Filter by branch
        checked_in: Filter by check-in status
        status: Filter by status
        search: Search by name, phone, email, or registration code

    Returns:
        Complete list of all matching registrations (no limit)
    """
    logger.info(f"=== EXPORT ENDPOINT REACHED === User: {current_user.id if current_user else 'None'}, Roles: {current_user.roles if current_user else 'None'}")
    logger.info(f"Export request - conference_id: {conference_id}, branch_id: {branch_id}, checked_in: {checked_in}, status: {status}, search: {search}")

    db = get_db()

    try:
        # Build filter
        filter_query = {}
        if conference_id:
            if not ObjectId.is_valid(conference_id):
                logger.error(f"Invalid conference ID: {conference_id}")
                raise HTTPException(status_code=400, detail="Invalid conference ID")
            filter_query["conference_id"] = ObjectId(conference_id)

        if branch_id:
            if not ObjectId.is_valid(branch_id):
                logger.error(f"Invalid branch ID: {branch_id}")
                raise HTTPException(status_code=400, detail="Invalid branch ID")
            filter_query["branch_id"] = ObjectId(branch_id)

        if checked_in is not None:
            filter_query["checked_in"] = checked_in

        if status:
            filter_query["status"] = status

        # Add search filter
        # Reason: Search across multiple fields using case-insensitive regex
        if search:
            search_regex = {"$regex": search, "$options": "i"}
            filter_query["$or"] = [
                {"user_name": search_regex},
                {"user_phone": search_regex},
                {"user_email": search_regex},
                {"registration_code": search_regex}
            ]

        logger.info(f"Executing query with filter: {filter_query}")

        # Get ALL registrations (no limit) sorted by created_at desc
        registrations = list(
            db.conference_registrations
            .find(filter_query)
            .sort("created_at", -1)
        )

        logger.info(f"Found {len(registrations)} registrations")

        # Fetch related data
        conference_ids = set([r["conference_id"] for r in registrations])
        branch_ids = set([r.get("branch_id") for r in registrations if r.get("branch_id")])
        bus_route_ids = set([r.get("bus_route_id") for r in registrations if r.get("bus_route_id")])

        conferences = {c["_id"]: c for c in db.conferences.find({"_id": {"$in": list(conference_ids)}})}
        branches = {b["_id"]: b for b in db.branches.find({"_id": {"$in": list(branch_ids)}})}
        bus_routes = {br["_id"]: br for br in db.bus_routes.find({"_id": {"$in": list(bus_route_ids)}})}

        # Format response
        result = []
        for reg in registrations:
            conference = conferences.get(reg["conference_id"])
            branch = branches.get(reg.get("branch_id"))
            bus_route = bus_routes.get(reg.get("bus_route_id"))

            result.append(RegistrationResponse(
                id=str(reg["_id"]),
                conference_id=str(reg["conference_id"]),
                conference_name=conference["name"] if conference else "Unknown",
                user_phone=reg["user_phone"],
                user_name=reg["user_name"],
                user_email=reg.get("user_email"),
                branch_id=str(reg["branch_id"]) if reg.get("branch_id") else None,
                branch_name=branch["name"] if branch else None,
                church_name=reg.get("church_name"),
                registration_code=reg["registration_code"],
                qr_code=None,  # Skip QR code generation for bulk export (performance)
                requires_bus=reg.get("requires_bus", False),
                bus_route_id=str(reg["bus_route_id"]) if reg.get("bus_route_id") else None,
                bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
                pickup_location=bus_route.get("pickup_location") if bus_route else None,
                special_needs=reg.get("special_needs"),
                emergency_contact=reg.get("emergency_contact"),
                checked_in=reg.get("checked_in", False),
                checked_in_at=reg["checked_in_at"].isoformat() if reg.get("checked_in_at") else None,
                created_at=reg["created_at"].isoformat(),
                status=reg.get("status", "confirmed"),
                greeting_audio=None
            ))

        logger.info(f"Successfully formatted {len(result)} registration records for export")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error during processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/{registration_id}", response_model=RegistrationResponse)
async def get_registration(registration_id: str):
    """
    Get a specific registration by ID.

    Args:
        registration_id: Registration ID

    Returns:
        Registration details with QR code
    """
    db = get_db()

    if not ObjectId.is_valid(registration_id):
        raise HTTPException(status_code=400, detail="Invalid registration ID")

    registration = db.conference_registrations.find_one({"_id": ObjectId(registration_id)})
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Get related data
    conference = db.conferences.find_one({"_id": registration["conference_id"]})
    branch = db.branches.find_one({"_id": registration["branch_id"]}) if registration.get("branch_id") else None
    bus_route = db.bus_routes.find_one({"_id": registration["bus_route_id"]}) if registration.get("bus_route_id") else None

    # OPTIMIZATION: Use cached QR code if available, otherwise generate it
    qr_code = registration.get("qr_code_base64")
    if not qr_code:
        # Fallback: Generate QR code if not cached (for old registrations)
        frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
        qr_data = f"{frontend_url}/self-checkin?code={registration['registration_code']}"
        qr_code = generate_qr_code(qr_data)

    return RegistrationResponse(
        id=str(registration["_id"]),
        conference_id=str(registration["conference_id"]),
        conference_name=conference["name"] if conference else "Unknown",
        user_phone=registration["user_phone"],
        user_name=registration["user_name"],
        user_email=registration.get("user_email"),
        branch_id=str(registration["branch_id"]) if registration.get("branch_id") else None,
        branch_name=branch["name"] if branch else None,
        church_name=registration.get("church_name"),
        registration_code=registration["registration_code"],
        qr_code=qr_code,
        requires_bus=registration.get("requires_bus", False),
        bus_route_id=str(registration["bus_route_id"]) if registration.get("bus_route_id") else None,
        bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
        pickup_location=bus_route.get("pickup_location") if bus_route else None,
        special_needs=registration.get("special_needs"),
        emergency_contact=registration.get("emergency_contact"),
        checked_in=registration.get("checked_in", False),
        checked_in_at=registration["checked_in_at"].isoformat() if registration.get("checked_in_at") else None,
        created_at=registration["created_at"].isoformat(),
        status=registration.get("status", "confirmed"),
        greeting_audio=None,  # Greetings only generated during check-in
        venue=conference.get("venue") if conference else None,
        venue_latitude=conference.get("venue_latitude") if conference else None,
        venue_longitude=conference.get("venue_longitude") if conference else None,
        venue_checkin_radius=conference.get("venue_checkin_radius", 1000) if conference else 1000,
        self_checkin_enabled=conference.get("self_checkin_enabled", True) if conference else True,
        conference_start_date=conference["start_date"].isoformat() if conference and conference.get("start_date") else None,
        conference_end_date=conference["end_date"].isoformat() if conference and conference.get("end_date") else None
    )


@router.get("/by-code/{registration_code}", response_model=RegistrationResponse)
async def get_registration_by_code(registration_code: str):
    """
    Get a specific registration by registration code.

    This endpoint is used by the Members page to look up registration details
    using the registration code (e.g., REG-XXXXXXXX).

    Args:
        registration_code: Registration code (e.g., REG-XXXXXXXX)

    Returns:
        Registration details with conference location data for check-in validation
    """
    db = get_db()

    registration = db.conference_registrations.find_one({"registration_code": registration_code})
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found. Please check your registration code.")

    # Get related data
    conference = db.conferences.find_one({"_id": registration["conference_id"]})
    branch = db.branches.find_one({"_id": registration["branch_id"]}) if registration.get("branch_id") else None
    bus_route = db.bus_routes.find_one({"_id": registration["bus_route_id"]}) if registration.get("bus_route_id") else None

    # OPTIMIZATION: Use cached QR code if available, otherwise generate it
    qr_code = registration.get("qr_code_base64")
    if not qr_code:
        # Fallback: Generate QR code if not cached (for old registrations)
        frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
        qr_data = f"{frontend_url}/self-checkin?code={registration['registration_code']}"
        qr_code = generate_qr_code(qr_data)

    return RegistrationResponse(
        id=str(registration["_id"]),
        conference_id=str(registration["conference_id"]),
        conference_name=conference["name"] if conference else "Unknown",
        user_phone=registration["user_phone"],
        user_name=registration["user_name"],
        user_email=registration.get("user_email"),
        branch_id=str(registration["branch_id"]) if registration.get("branch_id") else None,
        branch_name=branch["name"] if branch else None,
        church_name=registration.get("church_name"),
        registration_code=registration["registration_code"],
        qr_code=qr_code,
        requires_bus=registration.get("requires_bus", False),
        bus_route_id=str(registration["bus_route_id"]) if registration.get("bus_route_id") else None,
        bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
        pickup_location=bus_route.get("pickup_location") if bus_route else None,
        special_needs=registration.get("special_needs"),
        emergency_contact=registration.get("emergency_contact"),
        checked_in=registration.get("checked_in", False),
        checked_in_at=registration["checked_in_at"].isoformat() if registration.get("checked_in_at") else None,
        created_at=registration["created_at"].isoformat(),
        status=registration.get("status", "confirmed"),
        greeting_audio=None,  # Greetings only generated during check-in
        venue=conference.get("venue") if conference else None,
        venue_latitude=conference.get("venue_latitude") if conference else None,
        venue_longitude=conference.get("venue_longitude") if conference else None,
        venue_checkin_radius=conference.get("venue_checkin_radius", 1000) if conference else 1000,
        self_checkin_enabled=conference.get("self_checkin_enabled", True) if conference else True,
        conference_start_date=conference["start_date"].isoformat() if conference and conference.get("start_date") else None,
        conference_end_date=conference["end_date"].isoformat() if conference and conference.get("end_date") else None
    )


@router.get("/by-phone/{phone}", response_model=List[RegistrationResponse])
async def get_registrations_by_phone(
    phone: str,
    conference_id: Optional[str] = Query(None, description="Filter by specific conference ID"),
    user: User = Depends(require_coordinator_or_admin)
):
    """
    Get registrations by phone number (Staff/Admin only).

    This endpoint is used by staff/admin on the QR Scanner page to look up
    attendees by phone number for check-in. Requires coordinator or admin role.

    The endpoint normalizes the phone number to handle various formats:
    - International: +233244123456
    - National: 0244123456
    - Local: 244123456

    Args:
        phone: Phone number in any format
        conference_id: Optional conference ID to filter results
        user: Current authenticated user (coordinator or admin)

    Returns:
        List of registrations matching the phone number

    Raises:
        HTTPException: 400 if phone number format is invalid
        HTTPException: 404 if no registrations found
        HTTPException: 403 if user is not coordinator or admin
    """
    db = get_db()

    # Validate phone number format
    if not validate_phone_number(phone):
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number format. Please enter a valid phone number."
        )

    # Normalize phone number to handle different formats
    normalized_phones = normalize_phone_number(phone)
    logger.info(f"Searching for phone: {phone}, normalized to: {normalized_phones}")

    # Build query - search both primary phone and alternate phones in metadata
    # Reason: Users may register with multiple phone numbers stored in metadata.alternate_phones
    query = {
        "$or": [
            {"user_phone": {"$in": normalized_phones}},
            {"metadata.alternate_phones": {"$in": normalized_phones}}
        ],
        "status": "confirmed"
    }

    # Filter by conference if provided
    if conference_id:
        try:
            query["conference_id"] = ObjectId(conference_id)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid conference ID format"
            )

    # Find all matching registrations
    registrations = list(db.conference_registrations.find(query))

    if not registrations:
        raise HTTPException(
            status_code=404,
            detail=f"No registrations found for phone number {phone}"
        )

    logger.info(f"Found {len(registrations)} registration(s) for phone: {phone}")

    # Build response with full details for each registration
    results = []
    for registration in registrations:
        # Get related data
        conference = db.conferences.find_one({"_id": registration["conference_id"]})
        branch = db.branches.find_one({"_id": registration["branch_id"]}) if registration.get("branch_id") else None
        bus_route = db.bus_routes.find_one({"_id": registration["bus_route_id"]}) if registration.get("bus_route_id") else None

        # Generate QR code
        frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
        qr_data = f"{frontend_url}/self-checkin?code={registration['registration_code']}"
        qr_code = generate_qr_code(qr_data)

        results.append(RegistrationResponse(
            id=str(registration["_id"]),
            conference_id=str(registration["conference_id"]),
            conference_name=conference["name"] if conference else "Unknown",
            user_phone=registration["user_phone"],
            user_name=registration["user_name"],
            user_email=registration.get("user_email"),
            branch_id=str(registration["branch_id"]) if registration.get("branch_id") else None,
            branch_name=branch["name"] if branch else None,
            church_name=registration.get("church_name"),
            registration_code=registration["registration_code"],
            qr_code=qr_code,
            requires_bus=registration.get("requires_bus", False),
            bus_route_id=str(registration["bus_route_id"]) if registration.get("bus_route_id") else None,
            bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
            pickup_location=bus_route.get("pickup_location") if bus_route else None,
            special_needs=registration.get("special_needs"),
            emergency_contact=registration.get("emergency_contact"),
            checked_in=registration.get("checked_in", False),
            checked_in_at=registration["checked_in_at"].isoformat() if registration.get("checked_in_at") else None,
            created_at=registration["created_at"].isoformat(),
            status=registration.get("status", "confirmed"),
            greeting_audio=None,  # Greetings only generated during check-in
            venue=conference.get("venue") if conference else None,
            venue_latitude=conference.get("venue_latitude") if conference else None,
            venue_longitude=conference.get("venue_longitude") if conference else None,
            venue_checkin_radius=conference.get("venue_checkin_radius", 1000) if conference else 1000,
            self_checkin_enabled=conference.get("self_checkin_enabled", True) if conference else True,
        ))

    return results


@router.post("/check-in", response_model=RegistrationResponse)
async def check_in(request: CheckInRequest, background_tasks: BackgroundTasks):
    """
    Check in a user with their registration code.

    Args:
        request: Check-in data containing registration code

    Returns:
        Updated registration with voice greeting audio (if enabled)
    """
    db = get_db()

    # Find registration by code (check without status filter first for better error messages)
    registration = db.conference_registrations.find_one({
        "registration_code": request.registration_code
    })

    if not registration:
        logger.warning(f"Registration code not found: {request.registration_code}")
        raise HTTPException(
            status_code=404,
            detail="Registration not found. Please verify your QR code is correct."
        )

    # Check if registration is cancelled
    if registration.get("status") != "confirmed":
        logger.warning(f"Registration {request.registration_code} has status: {registration.get('status')}")
        raise HTTPException(
            status_code=400,
            detail=f"This registration has been {registration.get('status', 'cancelled')}. Please contact event staff."
        )

    # Get conference to check self-checkin setting and reuse later
    # Optimization: Fetch conference only once instead of twice
    conference = db.conferences.find_one({"_id": registration["conference_id"]})

    # Check if self-checkin is allowed (only applies to self-service, not staff check-in)
    if request.is_self_checkin and conference:
        if not conference.get("self_checkin_enabled", True):
            raise HTTPException(
                status_code=403,
                detail="Self-service check-in is currently disabled for this event. Please check in with event staff."
            )

        # Validate GPS location for location-based check-in
        # Reason: Only validate location if coordinates are provided in the request
        if request.latitude is not None and request.longitude is not None:
            venue_lat = conference.get("venue_latitude")
            venue_lon = conference.get("venue_longitude")
            venue_radius = conference.get("venue_checkin_radius", 1000)  # Default 1000m

            if venue_lat is None or venue_lon is None:
                logger.warning(f"Conference {conference['_id']} has no venue coordinates set")
                raise HTTPException(
                    status_code=400,
                    detail="Conference venue location is not configured. Please check in with event staff."
                )

            # Calculate distance between user and venue
            distance = calculate_distance(
                request.latitude, request.longitude,
                venue_lat, venue_lon
            )

            logger.info(f"Check-in location validation: Distance={distance:.2f}m, Radius={venue_radius}m")

            if distance > venue_radius:
                raise HTTPException(
                    status_code=403,
                    detail=f"You are too far from the venue to check in. You are {distance:.0f}m away (maximum: {venue_radius}m). Please move closer to the venue."
                )

    # Track if this is a repeat check-in
    already_checked_in = registration.get("checked_in", False)
    original_checkin_time = registration.get("checked_in_at")

    # Check if repeat check-in is allowed
    if already_checked_in and conference:
        if not conference.get("allow_repeat_checkin", True):
            raise HTTPException(
                status_code=400,
                detail="You have already checked in for this event. Multiple check-ins are not allowed."
            )

    # Update check-in status if not already checked in
    if not already_checked_in:
        db.conference_registrations.update_one(
            {"_id": registration["_id"]},
            {
                "$set": {
                    "checked_in": True,
                    "checked_in_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        # Get updated registration
        registration = db.conference_registrations.find_one({"_id": registration["_id"]})

        # Invalidate cache since checked_in stats changed
        cache = await get_cache()
        await cache.invalidate_conference(str(registration["conference_id"]))

    # OPTIMIZATION: Use MongoDB aggregation to fetch related data in one query
    # This replaces 2-3 separate queries with a single aggregated query
    pipeline = [
        {"$match": {"_id": registration["_id"]}},
        {
            "$lookup": {
                "from": "branches",
                "localField": "branch_id",
                "foreignField": "_id",
                "as": "branch_data"
            }
        },
        {
            "$lookup": {
                "from": "bus_routes",
                "localField": "bus_route_id",
                "foreignField": "_id",
                "as": "bus_route_data"
            }
        }
    ]

    aggregated = list(db.conference_registrations.aggregate(pipeline))
    if aggregated:
        branch = aggregated[0].get("branch_data", [None])[0]
        bus_route = aggregated[0].get("bus_route_data", [None])[0]
    else:
        # Fallback to individual queries if aggregation fails
        branch = db.branches.find_one({"_id": registration["branch_id"]}) if registration.get("branch_id") else None
        bus_route = db.bus_routes.find_one({"_id": registration["bus_route_id"]}) if registration.get("bus_route_id") else None

    # OPTIMIZATION: Generate voice greeting in background (non-blocking)
    # This saves 500-2000ms from check-in response time
    greeting_audio = None

    # Check if greeting was already generated and stored
    if registration.get("voice_greeting"):
        greeting_audio = registration["voice_greeting"]
        logger.info(f"Using cached voice greeting for registration {registration['_id']}")
    elif conference and conference.get("voice_greeting") and conference["voice_greeting"].get("enabled", True):
        # Schedule voice greeting generation as background task
        # This allows check-in to complete immediately while greeting generates async
        user_data = {
            "user_name": registration.get("user_name", "Guest"),
            "phone": registration.get("user_phone", ""),
            "branch_name": branch["name"] if branch else registration.get("church_name", ""),
            "volunteer_roles": []
        }

        event_data = {
            "event_name": conference["name"] if conference else "our event",
            "conference_name": conference["name"] if conference else "our conference"
        }

        user_id = str(registration.get("user_id")) if registration.get("user_id") else registration.get("user_phone", "guest")
        voice_config_dict = conference.get("voice_greeting", {})

        # Add background task to generate greeting async
        background_tasks.add_task(
            generate_voice_greeting_async,
            registration_id=str(registration["_id"]),
            user_data=user_data,
            event_data=event_data,
            voice_config=voice_config_dict,
            user_id=user_id
        )

        logger.info(f"🎵 Scheduled voice greeting generation for {registration['user_name']} (async)")
        # greeting_audio stays None - frontend can poll or use WebSocket to get it when ready

    # OPTIMIZATION: Use cached QR code if available, otherwise generate it
    qr_code = registration.get("qr_code_base64")
    if not qr_code:
        # Fallback: Generate QR code if not cached (for old registrations)
        frontend_url = "https://churchflow.ailabsafrica.com"  # TODO: Move to config
        qr_data = f"{frontend_url}/self-checkin?code={registration['registration_code']}"
        qr_code = generate_qr_code(qr_data)

    return RegistrationResponse(
        id=str(registration["_id"]),
        conference_id=str(registration["conference_id"]),
        conference_name=conference["name"] if conference else "Unknown",
        user_phone=registration["user_phone"],
        user_name=registration["user_name"],
        user_email=registration.get("user_email"),
        branch_id=str(registration["branch_id"]) if registration.get("branch_id") else None,
        branch_name=branch["name"] if branch else None,
        church_name=registration.get("church_name"),
        registration_code=registration["registration_code"],
        qr_code=qr_code,
        requires_bus=registration.get("requires_bus", False),
        bus_route_id=str(registration["bus_route_id"]) if registration.get("bus_route_id") else None,
        bus_route_name=bus_route.get("name") or bus_route.get("route_name") if bus_route else None,
        pickup_location=bus_route.get("pickup_location") if bus_route else None,
        special_needs=registration.get("special_needs"),
        emergency_contact=registration.get("emergency_contact"),
        checked_in=registration.get("checked_in", False),
        checked_in_at=registration["checked_in_at"].isoformat() if registration.get("checked_in_at") else None,
        created_at=registration["created_at"].isoformat(),
        status=registration.get("status", "confirmed"),
        greeting_audio=greeting_audio,  # Include voice greeting audio
        is_repeat_checkin=already_checked_in  # Indicate if this was a repeat check-in
    )


@router.delete("/{registration_id}", status_code=204)
async def delete_registration(
    registration_id: str,
    current_user: User = Depends(require_admin)
):
    """
    Delete a registration (admin only).

    Args:
        registration_id: Registration ID
        current_user: Current authenticated admin user

    Raises:
        HTTPException: 400 if invalid ID, 404 if not found, 403 if not admin
    """
    db = get_db()

    if not ObjectId.is_valid(registration_id):
        raise HTTPException(status_code=400, detail="Invalid registration ID")

    registration = db.conference_registrations.find_one({"_id": ObjectId(registration_id)})
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Decrement bus route count if registration had a bus
    if registration.get("requires_bus") and registration.get("bus_route_id"):
        db.bus_routes.update_one(
            {"_id": registration["bus_route_id"]},
            {
                "$inc": {"registered_count": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    # Permanently delete the registration
    db.conference_registrations.delete_one({"_id": ObjectId(registration_id)})

    # Invalidate cache for this conference
    cache = await get_cache()
    await cache.invalidate_conference(str(registration["conference_id"]))

    logger.info(f"Admin {current_user.id} deleted registration {registration_id}")

    return None


@router.put("/{registration_id}", response_model=RegistrationResponse)
async def update_registration(
    registration_id: str,
    request: UpdateRegistrationRequest,
    current_user: User = Depends(require_admin)
):
    """
    Update a registration (admin only).

    Args:
        registration_id: Registration ID
        request: Update data
        current_user: Current authenticated admin user

    Returns:
        Updated registration details

    Raises:
        HTTPException: 400 if invalid ID, 404 if not found, 403 if not admin
    """
    db = get_db()

    if not ObjectId.is_valid(registration_id):
        raise HTTPException(status_code=400, detail="Invalid registration ID")

    registration = db.conference_registrations.find_one({"_id": ObjectId(registration_id)})
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Build update data (only include fields that are provided)
    update_data = {}
    if request.user_name is not None:
        update_data["user_name"] = request.user_name
    if request.user_phone is not None:
        # Validate and normalize phone number
        if not validate_phone_number(request.user_phone):
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        update_data["user_phone"] = normalize_phone_number(request.user_phone)
    if request.user_email is not None:
        update_data["user_email"] = request.user_email if request.user_email else None
    if request.church_name is not None:
        update_data["church_name"] = request.church_name if request.church_name else None
    if request.special_needs is not None:
        update_data["special_needs"] = request.special_needs if request.special_needs else None
    if request.requires_bus is not None:
        update_data["requires_bus"] = request.requires_bus
    if request.bus_route_id is not None:
        update_data["bus_route_id"] = ObjectId(request.bus_route_id) if request.bus_route_id else None
    if request.checked_in is not None:
        update_data["checked_in"] = request.checked_in

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.utcnow()

    # Update the registration
    db.conference_registrations.update_one(
        {"_id": ObjectId(registration_id)},
        {"$set": update_data}
    )

    # Invalidate cache for this conference
    cache = await get_cache()
    await cache.invalidate_conference(str(registration["conference_id"]))

    logger.info(f"Admin {current_user.id} updated registration {registration_id}: {list(update_data.keys())}")

    # Fetch and return updated registration
    updated_registration = db.conference_registrations.find_one({"_id": ObjectId(registration_id)})

    # Fetch conference details
    conference = db.conferences.find_one({"_id": updated_registration["conference_id"]})

    # Fetch branch name if exists
    branch_name = None
    if updated_registration.get("branch_id"):
        branch = db.branches.find_one({"_id": updated_registration["branch_id"]})
        if branch:
            branch_name = branch.get("name")

    # Fetch bus route name if exists
    bus_route_name = None
    pickup_location = None
    if updated_registration.get("bus_route_id"):
        bus_route = db.bus_routes.find_one({"_id": updated_registration["bus_route_id"]})
        if bus_route:
            bus_route_name = bus_route.get("name")
            pickup_location = bus_route.get("route")

    return RegistrationResponse(
        id=str(updated_registration["_id"]),
        conference_id=str(updated_registration["conference_id"]),
        conference_name=conference.get("name") if conference else "Unknown Conference",
        user_phone=updated_registration["user_phone"],
        user_name=updated_registration["user_name"],
        user_email=updated_registration.get("user_email"),
        branch_id=str(updated_registration["branch_id"]) if updated_registration.get("branch_id") else None,
        branch_name=branch_name,
        church_name=updated_registration.get("church_name"),
        registration_code=updated_registration["registration_code"],
        qr_code=updated_registration.get("qr_code"),
        requires_bus=updated_registration.get("requires_bus", False),
        bus_route_id=str(updated_registration["bus_route_id"]) if updated_registration.get("bus_route_id") else None,
        bus_route_name=bus_route_name,
        pickup_location=pickup_location,
        special_needs=updated_registration.get("special_needs"),
        emergency_contact=updated_registration.get("emergency_contact"),
        checked_in=updated_registration.get("checked_in", False),
        checked_in_at=updated_registration.get("checked_in_at").isoformat() if updated_registration.get("checked_in_at") else None,
        created_at=updated_registration["created_at"].isoformat() if isinstance(updated_registration["created_at"], datetime) else updated_registration["created_at"],
        status=updated_registration.get("status", "confirmed"),
        greeting_audio=None,
        is_repeat_checkin=False,
        venue=conference.get("venue") if conference else None,
        venue_latitude=conference.get("venue_latitude") if conference else None,
        venue_longitude=conference.get("venue_longitude") if conference else None,
        venue_checkin_radius=conference.get("venue_checkin_radius", 1000) if conference else 1000,
        self_checkin_enabled=conference.get("self_checkin_enabled", True) if conference else True,
        session_checked_in=None,
        session_name=None,
        session_check_in_warning=None,
        conference_start_date=conference.get("start_date").isoformat() if conference and conference.get("start_date") else None,
        conference_end_date=conference.get("end_date").isoformat() if conference and conference.get("end_date") else None
    )


@router.delete("/bulk-delete/all")
async def delete_all_registrations(
    conference_id: Optional[str] = Query(None, description="Delete only registrations for this conference. If omitted, deletes ALL registrations."),
    current_user: User = Depends(require_admin)
):
    """
    Delete all registrations with optional conference filter (admin only).

    WARNING: This is a destructive operation that permanently deletes registrations.

    Args:
        conference_id: Optional conference ID to filter deletions. If not provided, deletes ALL registrations.
        current_user: Current authenticated admin user

    Returns:
        Dictionary with count of deleted registrations

    Raises:
        HTTPException: 400 if invalid conference ID, 403 if not admin
    """
    db = get_db()

    # Build filter query
    filter_query = {}
    if conference_id:
        if not ObjectId.is_valid(conference_id):
            raise HTTPException(status_code=400, detail="Invalid conference ID")
        filter_query["conference_id"] = ObjectId(conference_id)

    # Get all registrations to be deleted (for bus count updates)
    registrations_to_delete = list(db.conference_registrations.find(filter_query))

    if not registrations_to_delete:
        return {"deleted_count": 0, "message": "No registrations found to delete"}

    # Decrement bus route counts for registrations with buses
    bus_route_decrements = {}
    for reg in registrations_to_delete:
        if reg.get("requires_bus") and reg.get("bus_route_id"):
            bus_route_id = reg["bus_route_id"]
            bus_route_decrements[bus_route_id] = bus_route_decrements.get(bus_route_id, 0) + 1

    # Update bus route counts
    for bus_route_id, decrement in bus_route_decrements.items():
        db.bus_routes.update_one(
            {"_id": bus_route_id},
            {
                "$inc": {"registered_count": -decrement},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    # Delete all matching registrations
    result = db.conference_registrations.delete_many(filter_query)

    # Invalidate cache
    cache = await get_cache()
    if conference_id:
        await cache.invalidate_conference(conference_id)
    else:
        await cache.invalidate_all()

    logger.info(f"Bulk deleted {result.deleted_count} registrations. Conference filter: {conference_id or 'ALL'}")

    return {
        "deleted_count": result.deleted_count,
        "message": f"Successfully deleted {result.deleted_count} registration(s)",
        "conference_id": conference_id
    }


class BulkDeleteRequest(BaseModel):
    """Request model for bulk deleting selected registrations."""
    registration_ids: List[str] = Field(..., min_items=1, description="List of registration IDs to delete")


@router.post("/bulk-delete/selected")
async def delete_selected_registrations(
    request: BulkDeleteRequest,
    current_user: User = Depends(require_admin)
):
    """
    Delete selected registrations by IDs (admin only).

    Allows admins to delete multiple specific registrations at once using checkboxes.

    Args:
        request: List of registration IDs to delete
        current_user: Current authenticated admin user

    Returns:
        Dictionary with count of deleted registrations and any errors

    Raises:
        HTTPException: 400 if invalid IDs, 403 if not admin
    """
    db = get_db()

    # Validate all IDs
    invalid_ids = [rid for rid in request.registration_ids if not ObjectId.is_valid(rid)]
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid registration IDs: {', '.join(invalid_ids)}"
        )

    # Convert to ObjectIds
    object_ids = [ObjectId(rid) for rid in request.registration_ids]

    # Get registrations to be deleted (for bus count updates)
    registrations_to_delete = list(db.conference_registrations.find({"_id": {"$in": object_ids}}))

    if not registrations_to_delete:
        return {
            "deleted_count": 0,
            "message": "No registrations found with the provided IDs",
            "not_found_count": len(request.registration_ids)
        }

    # Decrement bus route counts for registrations with buses
    bus_route_decrements = {}
    for reg in registrations_to_delete:
        if reg.get("requires_bus") and reg.get("bus_route_id"):
            bus_route_id = reg["bus_route_id"]
            bus_route_decrements[bus_route_id] = bus_route_decrements.get(bus_route_id, 0) + 1

    # Update bus route counts
    for bus_route_id, decrement in bus_route_decrements.items():
        db.bus_routes.update_one(
            {"_id": bus_route_id},
            {
                "$inc": {"registered_count": -decrement},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    # Delete selected registrations
    result = db.conference_registrations.delete_many({"_id": {"$in": object_ids}})

    # Invalidate cache for affected conferences
    cache = await get_cache()
    affected_conferences = set(str(reg["conference_id"]) for reg in registrations_to_delete)
    for conf_id in affected_conferences:
        await cache.invalidate_conference(conf_id)

    logger.info(f"Admin {current_user.id} bulk deleted {result.deleted_count} selected registrations")

    return {
        "deleted_count": result.deleted_count,
        "message": f"Successfully deleted {result.deleted_count} registration(s)",
        "requested_count": len(request.registration_ids),
        "not_found_count": len(request.registration_ids) - result.deleted_count
    }

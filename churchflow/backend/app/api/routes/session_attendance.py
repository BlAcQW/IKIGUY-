"""
Session attendance API routes.

Endpoints for checking attendees into specific conference sessions
and retrieving attendance lists.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging
from bson import ObjectId

from app.api.dependencies import require_coordinator_or_admin, require_organization_access
from app.services.session_attendance_service import session_attendance_service
from app.services.session_service import session_service
from app.services.voice_greeting_service import VoiceGreetingService
from app.services.gamification_service import get_gamification_service
from app.models.voice_greeting import VoiceGreetingConfig, GreetingAudioResponse
from app.models.user import User
from app.core.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Session Attendance"])

# Voice greeting service instance
voice_greeting_service = VoiceGreetingService()


# Request/Response Models
class SessionCheckInRequest(BaseModel):
    """Request for QR code session check-in."""
    registration_code: str = Field(..., description="Registration code from QR (REG-XXXXXXXX)")


class ManualCheckInRequest(BaseModel):
    """Request for manual session check-in after search."""
    registration_id: str = Field(..., description="Registration ID from search results")


class PhoneCheckInRequest(BaseModel):
    """Request for direct phone check-in."""
    phone: str = Field(..., min_length=6, description="Phone number")


class GreetingAudioResponseModel(BaseModel):
    """Voice greeting audio response embedded in check-in response."""
    audio_url: str
    text: str
    duration_seconds: Optional[float] = None
    provider_used: str
    cost_usd: Optional[float] = None
    is_fallback: bool = False


class SessionCheckInResponse(BaseModel):
    """Session check-in success response."""
    id: str
    session_id: str
    session_name: str
    conference_id: str
    user_name: str
    user_phone: str
    checked_in_at: datetime
    check_in_method: str
    message: str = "Check-in successful"
    greeting_audio: Optional[GreetingAudioResponseModel] = None
    is_repeat_checkin: bool = False


class AttendeeResponse(BaseModel):
    """Single attendee in attendance list."""
    id: str
    user_name: str
    user_phone: str
    checked_in_at: datetime
    check_in_method: str


class SessionAttendanceListResponse(BaseModel):
    """Session attendance list response."""
    session_id: str
    session_name: str
    attendees: List[AttendeeResponse]
    total_checked_in: int


class RegistrationSearchResult(BaseModel):
    """Search result for check-in."""
    id: str
    user_name: str
    user_phone: str
    user_email: Optional[str] = None
    church_name: Optional[str] = None
    registration_code: str


class AttendanceReportItem(BaseModel):
    """Single item in conference attendance report."""
    registration_id: str
    user_name: str
    user_phone: str
    user_email: Optional[str] = None
    branch_name: Optional[str] = None
    bus_route_name: Optional[str] = None
    bus_pickup_location: Optional[str] = None
    sessions_attended: List[str]
    total_sessions: int
    first_check_in: datetime


class ConferenceAttendanceReportResponse(BaseModel):
    """Conference attendance report response."""
    conference_id: str
    total_attendees: int
    report: List[AttendanceReportItem]


@router.post(
    "/conferences/{conference_id}/sessions/{session_id}/check-in",
    response_model=SessionCheckInResponse,
    summary="Check in to session via QR code"
)
async def check_in_to_session(
    conference_id: str,
    session_id: str,
    request: SessionCheckInRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Check in attendee to session using registration code from QR scan.

    Requires coordinator or admin role.

    SECURITY: Verifies that the conference belongs to the organization
    before allowing check-in.

    Args:
        conference_id: Conference ID
        session_id: Session ID to check into
        request: Registration code
        organization_id: Organization ID from X-Organization-ID header

    Returns:
        SessionCheckInResponse with check-in details and optional voice greeting
    """
    try:
        # CRITICAL: Verify conference belongs to organization before check-in
        from bson import ObjectId
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )

        checkin = await session_attendance_service.check_in_by_code(
            registration_code=request.registration_code,
            session_id=session_id,
            admin_id=str(current_user.id) if current_user.id else None
        )

        # Generate voice greeting if conference has it enabled
        greeting_audio = None
        try:
            db = get_database()
            conference = await db.conferences.find_one({"_id": checkin.conference_id})

            if conference and conference.get("voice_greeting"):
                voice_config = VoiceGreetingConfig(**conference["voice_greeting"])

                if voice_config.enabled:
                    # Get registration for user data
                    registration = await db.conference_registrations.find_one({
                        "registration_code": request.registration_code
                    })

                    user_data = {
                        "user_name": checkin.user_name or "Guest",
                        "branch_name": registration.get("church_name") if registration else None,
                        "volunteer_roles": registration.get("volunteer_roles", []) if registration else []
                    }

                    event_data = {
                        "conference_name": conference.get("name", "Conference"),
                        "venue": conference.get("venue", "")
                    }

                    audio_response = await voice_greeting_service.generate_greeting(
                        user_data=user_data,
                        event_data=event_data,
                        config=voice_config,
                        user_id=str(current_user.id) if current_user.id else "system"
                    )

                    if audio_response:
                        greeting_audio = GreetingAudioResponseModel(
                            audio_url=audio_response.audio_url,
                            text=audio_response.text,
                            duration_seconds=audio_response.duration_seconds,
                            provider_used=audio_response.provider_used,
                            cost_usd=audio_response.cost_usd,
                            is_fallback=audio_response.is_fallback
                        )

        except Exception as greeting_err:
            # Don't fail check-in if greeting generation fails
            logger.warning(f"Voice greeting generation failed: {greeting_err}")

        # Build appropriate message based on repeat status
        is_repeat = getattr(checkin, 'is_repeat_checkin', False)
        if is_repeat:
            message = f"{checkin.user_name} was already checked in"
        else:
            message = f"{checkin.user_name} checked in successfully"

        return SessionCheckInResponse(
            id=str(checkin.id),
            session_id=str(checkin.session_id),
            session_name=checkin.session_name or "Session",
            conference_id=str(checkin.conference_id),
            user_name=checkin.user_name or "Unknown",
            user_phone=checkin.user_phone or "",
            checked_in_at=checkin.checked_in_at,
            check_in_method=checkin.check_in_method,
            message=message,
            greeting_audio=greeting_audio,
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Session check-in validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/conferences/{conference_id}/sessions/{session_id}/check-in/manual",
    response_model=SessionCheckInResponse,
    summary="Check in to session via manual search"
)
async def check_in_to_session_manual(
    conference_id: str,
    session_id: str,
    request: ManualCheckInRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Check in attendee using registration ID from search results.

    Requires coordinator or admin role.

    SECURITY: Verifies that the conference belongs to the organization
    before allowing check-in.

    Args:
        conference_id: Conference ID
        session_id: Session ID to check into
        request: Registration ID from search
        organization_id: Organization ID from X-Organization-ID header

    Returns:
        SessionCheckInResponse with check-in details
    """
    try:
        # CRITICAL: Verify conference belongs to organization before check-in
        from bson import ObjectId
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )
        checkin = await session_attendance_service.check_in_by_registration_id(
            registration_id=request.registration_id,
            session_id=session_id,
            admin_id=str(current_user.id) if current_user.id else None
        )

        # Build appropriate message based on repeat status
        is_repeat = getattr(checkin, 'is_repeat_checkin', False)
        if is_repeat:
            message = f"{checkin.user_name} was already checked in"
        else:
            message = f"{checkin.user_name} checked in successfully"

        return SessionCheckInResponse(
            id=str(checkin.id),
            session_id=str(checkin.session_id),
            session_name=checkin.session_name or "Session",
            conference_id=str(checkin.conference_id),
            user_name=checkin.user_name or "Unknown",
            user_phone=checkin.user_phone or "",
            checked_in_at=checkin.checked_in_at,
            check_in_method=checkin.check_in_method,
            message=message,
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Session check-in validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/conferences/{conference_id}/sessions/{session_id}/check-in/phone",
    response_model=SessionCheckInResponse,
    summary="Check in to session via phone number"
)
async def check_in_to_session_by_phone(
    conference_id: str,
    session_id: str,
    request: PhoneCheckInRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Check in attendee using phone number directly.

    Requires coordinator or admin role.

    Args:
        conference_id: Conference ID
        session_id: Session ID to check into
        request: Phone number
        organization_id: Organization ID (verified from header)

    Returns:
        SessionCheckInResponse with check-in details
    """
    try:
        # CRITICAL: Verify conference belongs to organization before check-in
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )

        checkin = await session_attendance_service.check_in_by_phone(
            phone=request.phone,
            session_id=session_id,
            admin_id=str(current_user.id) if current_user.id else None
        )

        # Build appropriate message based on repeat status
        is_repeat = getattr(checkin, 'is_repeat_checkin', False)
        if is_repeat:
            message = f"{checkin.user_name} was already checked in"
        else:
            message = f"{checkin.user_name} checked in successfully"

        return SessionCheckInResponse(
            id=str(checkin.id),
            session_id=str(checkin.session_id),
            session_name=checkin.session_name or "Session",
            conference_id=str(checkin.conference_id),
            user_name=checkin.user_name or "Unknown",
            user_phone=checkin.user_phone or "",
            checked_in_at=checkin.checked_in_at,
            check_in_method=checkin.check_in_method,
            message=message,
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Phone check-in validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Phone check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/conferences/{conference_id}/sessions/{session_id}/attendance",
    response_model=SessionAttendanceListResponse,
    summary="Get session attendance list"
)
async def get_session_attendance(
    conference_id: str,
    session_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Get list of all attendees checked into a session.

    Requires coordinator or admin role.

    Args:
        conference_id: Conference ID
        session_id: Session ID
        organization_id: Organization ID (verified from header)

    Returns:
        SessionAttendanceListResponse with attendee list
    """
    try:
        # CRITICAL: Verify conference belongs to organization
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )

        # Get session info
        session = await session_service.get_session(session_id, conference_id)
        session_name = session.name if session else "Unknown Session"

        # Get attendance list
        checkins = await session_attendance_service.get_session_attendance(
            session_id=session_id,
            conference_id=conference_id
        )

        logger.info(
            f"Getting attendance for session {session_id} in conference {conference_id}: "
            f"found {len(checkins)} check-ins"
        )

        attendees = [
            AttendeeResponse(
                id=str(c.id),
                user_name=c.user_name or "Unknown",
                user_phone=c.user_phone or "",
                checked_in_at=c.checked_in_at,
                check_in_method=c.check_in_method
            )
            for c in checkins
        ]

        return SessionAttendanceListResponse(
            session_id=session_id,
            session_name=session_name,
            attendees=attendees,
            total_checked_in=len(attendees)
        )
    except Exception as e:
        logger.error(
            f"Error getting session attendance for session {session_id} "
            f"in conference {conference_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session attendance: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/registrations/search",
    response_model=List[RegistrationSearchResult],
    summary="Search registrations for check-in"
)
async def search_registrations_for_checkin(
    conference_id: str,
    q: str = Query(..., min_length=2, description="Search by name or phone"),
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Search conference registrations by name or phone for manual check-in.

    Requires coordinator or admin role.

    Args:
        conference_id: Conference ID to search within
        q: Search query (minimum 2 characters)
        organization_id: Organization ID (verified from header)

    Returns:
        List of matching registrations
    """
    # CRITICAL: Verify conference belongs to organization
    db = get_database()
    conference = await db.conferences.find_one({
        "_id": ObjectId(conference_id),
        "organization_id": organization_id
    })

    if not conference:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Conference not in your organization"
        )

    results = await session_attendance_service.search_registrations(
        conference_id=conference_id,
        query=q
    )

    return [
        RegistrationSearchResult(
            id=str(r["_id"]),
            user_name=r.get("user_name", "Unknown"),
            user_phone=r.get("user_phone", ""),
            user_email=r.get("user_email"),
            church_name=r.get("church_name"),
            registration_code=r.get("registration_code", "")
        )
        for r in results
    ]


@router.get(
    "/conferences/{conference_id}/attendance-report",
    response_model=ConferenceAttendanceReportResponse,
    summary="Get conference attendance report"
)
async def get_conference_attendance_report(
    conference_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(require_coordinator_or_admin)
):
    """
    Get report of all attendees who checked into at least one session.

    Includes: user details, sessions attended, branch, bus route.
    Requires coordinator or admin role.

    Args:
        conference_id: Conference ID
        organization_id: Organization ID (verified from header)

    Returns:
        ConferenceAttendanceReportResponse with attendance report
    """
    try:
        # CRITICAL: Verify conference belongs to organization
        db = get_database()
        conference = await db.conferences.find_one({
            "_id": ObjectId(conference_id),
            "organization_id": organization_id
        })

        if not conference:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Conference not in your organization"
            )

        report = await session_attendance_service.get_conference_attendance_report(
            conference_id=conference_id
        )

        return ConferenceAttendanceReportResponse(
            conference_id=conference_id,
            total_attendees=len(report),
            report=[
                AttendanceReportItem(
                    registration_id=item["registration_id"],
                    user_name=item["user_name"],
                    user_phone=item["user_phone"],
                    user_email=item.get("user_email"),
                    branch_name=item.get("branch_name"),
                    bus_route_name=item.get("bus_route_name"),
                    bus_pickup_location=item.get("bus_pickup_location"),
                    sessions_attended=item["sessions_attended"],
                    total_sessions=item["total_sessions"],
                    first_check_in=item["first_check_in"]
                )
                for item in report
            ]
        )

    except Exception as e:
        logger.error(f"Error getting attendance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MEMBER SELF-SERVICE ENDPOINTS (Public - No authentication required)
# =============================================================================

class MemberSessionCheckInRequest(BaseModel):
    """Request for member self-service session check-in by registration code."""
    registration_code: str = Field(..., description="Registration code (REG-XXXXXXXX)")
    latitude: float = Field(..., description="User's current latitude")
    longitude: float = Field(..., description="User's current longitude")


class MemberPhoneSessionCheckInRequest(BaseModel):
    """Request for member self-service session check-in by phone number."""
    phone: str = Field(..., min_length=6, description="Phone number")
    latitude: float = Field(..., description="User's current latitude")
    longitude: float = Field(..., description="User's current longitude")


class TodaysSessionResponse(BaseModel):
    """Session available for check-in today."""
    id: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    day_number: int
    day_label: str
    order: int
    session_date: Optional[datetime] = None
    already_checked_in: bool = False


class MemberRegistrationResponse(BaseModel):
    """Registration response for phone lookup."""
    id: str
    user_name: str
    user_phone: str
    conference_id: str
    conference_name: str
    registration_code: str
    venue: Optional[str] = None
    venue_latitude: Optional[float] = None
    venue_longitude: Optional[float] = None
    venue_checkin_radius: Optional[float] = None


class MemberSessionLookupResponse(BaseModel):
    """Response for today's sessions lookup."""
    registration_id: str
    user_name: str
    user_phone: str
    conference_id: str
    conference_name: str
    venue: Optional[str] = None
    venue_latitude: Optional[float] = None
    venue_longitude: Optional[float] = None
    venue_checkin_radius: Optional[float] = None
    location_checkin_required: bool = True
    todays_sessions: List[TodaysSessionResponse]


@router.get(
    "/member/sessions/today/{registration_code}",
    response_model=MemberSessionLookupResponse,
    summary="Get today's sessions for member check-in (Public)"
)
async def get_todays_sessions_for_member(registration_code: str):
    """
    Get today's sessions for a registration with check-in status.

    Public endpoint - no authentication required.
    Used by member self-service check-in page.

    Args:
        registration_code: Registration code (REG-XXXXXXXX)

    Returns:
        MemberSessionLookupResponse with registration info and today's sessions
    """
    from app.core.database import get_database
    from bson import ObjectId

    db = get_database()

    # Find registration by code
    registration = await db.conference_registrations.find_one({
        "registration_code": registration_code,
        "status": "confirmed"
    })
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found or cancelled")

    # Get conference info
    conference = await db.conferences.find_one({
        "_id": registration["conference_id"]
    })
    if not conference:
        raise HTTPException(status_code=404, detail="Conference not found")

    # Check if conference is ongoing (today falls within start and end date)
    from datetime import datetime
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    conf_start = conference.get("start_date")
    conf_end = conference.get("end_date")

    # Conference hasn't started if start date is after today
    if conf_start and conf_start > today_end:
        raise HTTPException(status_code=400, detail="Conference has not started yet")
    # Conference has ended if end date is before today
    if conf_end and conf_end < today_start:
        raise HTTPException(status_code=400, detail="Conference has ended")

    # Get today's sessions with check-in status
    todays_sessions = await session_service.get_todays_sessions(
        conference_id=str(registration["conference_id"]),
        registration_id=str(registration["_id"])
    )

    return MemberSessionLookupResponse(
        registration_id=str(registration["_id"]),
        user_name=registration.get("user_name", "Unknown"),
        user_phone=registration.get("user_phone", ""),
        conference_id=str(registration["conference_id"]),
        conference_name=conference.get("name", "Conference"),
        venue=conference.get("venue"),
        venue_latitude=conference.get("venue_latitude"),
        venue_longitude=conference.get("venue_longitude"),
        venue_checkin_radius=conference.get("venue_checkin_radius", 1000),
        location_checkin_required=conference.get("location_checkin_required", True),
        todays_sessions=[
            TodaysSessionResponse(
                id=s["id"],
                name=s["name"],
                description=s.get("description"),
                location=s.get("location"),
                day_number=s["day_number"],
                day_label=s["day_label"],
                order=s["order"],
                session_date=s.get("session_date"),
                already_checked_in=s["already_checked_in"]
            )
            for s in todays_sessions
        ]
    )


@router.post(
    "/member/sessions/{session_id}/check-in",
    response_model=SessionCheckInResponse,
    summary="Member self-service session check-in by code (Public)"
)
async def member_session_check_in_by_code(
    session_id: str,
    request: MemberSessionCheckInRequest
):
    """
    Check in to session using registration code with GPS validation.

    Public endpoint - no authentication required.
    Validates user is within venue radius before allowing check-in.

    Args:
        session_id: Session ID to check into
        request: Registration code and GPS coordinates

    Returns:
        SessionCheckInResponse with check-in details and optional voice greeting
    """
    try:
        checkin = await session_attendance_service.member_check_in_by_code(
            registration_code=request.registration_code,
            session_id=session_id,
            latitude=request.latitude,
            longitude=request.longitude
        )

        # Generate voice greeting if conference has it enabled
        greeting_audio = None
        try:
            db = get_database()
            conference = await db.conferences.find_one({"_id": checkin.conference_id})

            if conference and conference.get("voice_greeting"):
                voice_config = VoiceGreetingConfig(**conference["voice_greeting"])

                if voice_config.enabled:
                    # Get registration for user data
                    registration = await db.conference_registrations.find_one({
                        "registration_code": request.registration_code
                    })

                    user_data = {
                        "user_name": checkin.user_name or "Guest",
                        "branch_name": registration.get("church_name") if registration else None,
                        "volunteer_roles": registration.get("volunteer_roles", []) if registration else []
                    }

                    event_data = {
                        "conference_name": conference.get("name", "Conference"),
                        "venue": conference.get("venue", "")
                    }

                    audio_response = await voice_greeting_service.generate_greeting(
                        user_data=user_data,
                        event_data=event_data,
                        config=voice_config,
                        user_id="member-self-checkin"
                    )

                    if audio_response:
                        greeting_audio = GreetingAudioResponseModel(
                            audio_url=audio_response.audio_url,
                            text=audio_response.text,
                            duration_seconds=audio_response.duration_seconds,
                            provider_used=audio_response.provider_used,
                            cost_usd=audio_response.cost_usd,
                            is_fallback=audio_response.is_fallback
                        )

        except Exception as greeting_err:
            # Don't fail check-in if greeting generation fails
            logger.warning(f"Voice greeting generation failed: {greeting_err}")

        # Build appropriate message based on repeat status
        is_repeat = getattr(checkin, 'is_repeat_checkin', False)
        if is_repeat:
            message = f"{checkin.user_name} was already checked in"
        else:
            message = f"{checkin.user_name} checked into session successfully"

        return SessionCheckInResponse(
            id=str(checkin.id),
            session_id=str(checkin.session_id),
            session_name=checkin.session_name or "Session",
            conference_id=str(checkin.conference_id),
            user_name=checkin.user_name or "Unknown",
            user_phone=checkin.user_phone or "",
            checked_in_at=checkin.checked_in_at,
            check_in_method=checkin.check_in_method,
            message=message,
            greeting_audio=greeting_audio,
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Member session check-in validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Member session check-in GPS error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Member session check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/member/registrations/by-phone/{phone}",
    response_model=List[MemberRegistrationResponse],
    summary="Get registrations by phone for ongoing conferences (Public)"
)
async def get_member_registrations_by_phone(phone: str):
    """
    Get all registrations for a phone number in ongoing conferences.

    Public endpoint - no authentication required.
    Returns only registrations for conferences that are currently ongoing
    (conference date range includes today).

    Args:
        phone: Phone number to look up

    Returns:
        List of registrations for ongoing conferences
    """
    from app.core.database import get_database
    from bson import ObjectId
    from datetime import datetime
    from app.utils.phone import normalize_phone_number

    db = get_database()

    # Normalize phone to get all possible formats
    phone_variants = normalize_phone_number(phone)
    if not phone_variants:
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Find registrations by phone with ongoing conference filter
    # Conference is "ongoing" if today falls within start_date and end_date
    pipeline = [
        {
            "$match": {
                "user_phone": {"$in": phone_variants},
                "status": "confirmed"
            }
        },
        {
            "$lookup": {
                "from": "conferences",
                "localField": "conference_id",
                "foreignField": "_id",
                "as": "conference"
            }
        },
        {"$unwind": "$conference"},
        {
            "$match": {
                # Conference start date is today or earlier
                "conference.start_date": {"$lte": today_end},
                # Conference end date is today or later
                "conference.end_date": {"$gte": today_start}
            }
        }
    ]

    registrations = await db.conference_registrations.aggregate(pipeline).to_list(length=100)

    if not registrations:
        raise HTTPException(
            status_code=404,
            detail="No registrations found for this phone number in ongoing conferences"
        )

    return [
        MemberRegistrationResponse(
            id=str(r["_id"]),
            user_name=r.get("user_name", "Unknown"),
            user_phone=r.get("user_phone", ""),
            conference_id=str(r["conference_id"]),
            conference_name=r["conference"].get("name", "Conference"),
            registration_code=r.get("registration_code", ""),
            venue=r["conference"].get("venue"),
            venue_latitude=r["conference"].get("venue_latitude"),
            venue_longitude=r["conference"].get("venue_longitude"),
            venue_checkin_radius=r["conference"].get("venue_checkin_radius", 1000)
        )
        for r in registrations
    ]


@router.post(
    "/member/sessions/{session_id}/check-in/phone",
    response_model=SessionCheckInResponse,
    summary="Member self-service session check-in by phone (Public)"
)
async def member_session_check_in_by_phone(
    session_id: str,
    request: MemberPhoneSessionCheckInRequest
):
    """
    Check in to session using phone number with GPS validation.

    Public endpoint - no authentication required.
    Validates user is within venue radius before allowing check-in.

    Args:
        session_id: Session ID to check into
        request: Phone number and GPS coordinates

    Returns:
        SessionCheckInResponse with check-in details and optional voice greeting
    """
    try:
        checkin = await session_attendance_service.member_check_in_by_phone(
            phone=request.phone,
            session_id=session_id,
            latitude=request.latitude,
            longitude=request.longitude
        )

        # Generate voice greeting if conference has it enabled
        greeting_audio = None
        try:
            db = get_database()
            conference = await db.conferences.find_one({"_id": checkin.conference_id})

            if conference and conference.get("voice_greeting"):
                voice_config = VoiceGreetingConfig(**conference["voice_greeting"])

                if voice_config.enabled:
                    # Get registration for user data
                    from app.utils.phone import normalize_phone_number
                    phone_variants = normalize_phone_number(request.phone)
                    registration = await db.conference_registrations.find_one({
                        "user_phone": {"$in": phone_variants} if phone_variants else request.phone,
                        "conference_id": checkin.conference_id
                    })

                    user_data = {
                        "user_name": checkin.user_name or "Guest",
                        "branch_name": registration.get("church_name") if registration else None,
                        "volunteer_roles": registration.get("volunteer_roles", []) if registration else []
                    }

                    event_data = {
                        "conference_name": conference.get("name", "Conference"),
                        "venue": conference.get("venue", "")
                    }

                    audio_response = await voice_greeting_service.generate_greeting(
                        user_data=user_data,
                        event_data=event_data,
                        config=voice_config,
                        user_id="member-self-checkin"
                    )

                    if audio_response:
                        greeting_audio = GreetingAudioResponseModel(
                            audio_url=audio_response.audio_url,
                            text=audio_response.text,
                            duration_seconds=audio_response.duration_seconds,
                            provider_used=audio_response.provider_used,
                            cost_usd=audio_response.cost_usd,
                            is_fallback=audio_response.is_fallback
                        )

        except Exception as greeting_err:
            # Don't fail check-in if greeting generation fails
            logger.warning(f"Voice greeting generation failed: {greeting_err}")

        # Build appropriate message based on repeat status
        is_repeat = getattr(checkin, 'is_repeat_checkin', False)
        if is_repeat:
            message = f"{checkin.user_name} was already checked in"
        else:
            message = f"{checkin.user_name} checked into session successfully"

        return SessionCheckInResponse(
            id=str(checkin.id),
            session_id=str(checkin.session_id),
            session_name=checkin.session_name or "Session",
            conference_id=str(checkin.conference_id),
            user_name=checkin.user_name or "Unknown",
            user_phone=checkin.user_phone or "",
            checked_in_at=checkin.checked_in_at,
            check_in_method=checkin.check_in_method,
            message=message,
            greeting_audio=greeting_audio,
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Member phone session check-in validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Member phone session check-in GPS error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Member phone session check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SERVICE CHECK-IN ENDPOINTS
# ============================================

class ServiceMemberCheckInRequest(BaseModel):
    """Request for member check-in to service."""
    user_id: Optional[str] = Field(None, description="User ID (if known)")
    phone: Optional[str] = Field(None, description="Phone number for lookup")
    check_in_method: str = Field("phone_lookup", description="Check-in method")
    latitude: Optional[float] = Field(None, description="User latitude")
    longitude: Optional[float] = Field(None, description="User longitude")


class ServiceVisitorCheckInRequest(BaseModel):
    """Request for visitor registration and check-in to service."""
    name: str = Field(..., description="Visitor name")
    phone: str = Field(..., description="Visitor phone number")
    email: Optional[str] = Field(None, description="Visitor email")
    church_name: Optional[str] = Field(None, description="Visitor's church")
    department_interests: List[str] = Field(default_factory=list, description="Interested departments")


class ServiceCheckInResponse(BaseModel):
    """Response for service check-in."""
    success: bool
    message: str
    user_id: str
    attendance_id: str
    is_new_visitor: Optional[bool] = None
    is_repeat_checkin: Optional[bool] = None


@router.post(
    "/services/{service_id}/check-in/member",
    response_model=ServiceCheckInResponse,
    summary="Check in member to service",
    description="Check in existing member to a church service"
)
async def check_in_member_to_service(
    service_id: str,
    request: ServiceMemberCheckInRequest,
    background_tasks: BackgroundTasks,
    admin_user: Optional[User] = Depends(require_coordinator_or_admin)
):
    """
    Check in member to service.

    Requires either user_id or phone number for lookup.
    Awards gamification points and updates streaks in background.
    """
    try:
        # Determine user_id from request
        user_id = request.user_id
        db = get_database()

        if not user_id and request.phone:
            # Look up user by phone
            from app.utils.phone import normalize_phone_number

            phone_variants = normalize_phone_number(request.phone)
            if not phone_variants:
                raise ValueError("Invalid phone number format")

            user = await db.users.find_one({
                "phone": {"$in": phone_variants}
            })
            if not user:
                raise ValueError(f"No member found with phone: {request.phone}")

            user_id = str(user["_id"])

        if not user_id:
            raise ValueError("Either user_id or phone must be provided")

        # Get user for organization_id
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise ValueError("User not found")

        organization_id = str(user_doc.get("organization_id"))

        # Perform check-in
        attendance = await session_attendance_service.check_in_member_to_service(
            service_id=service_id,
            user_id=user_id,
            check_in_method=request.check_in_method,
            latitude=request.latitude,
            longitude=request.longitude,
            admin_id=str(admin_user.id) if admin_user else None
        )

        is_repeat = getattr(attendance, 'is_repeat_checkin', False)

        # GAMIFICATION: Award points and update streak in background (only for new check-ins)
        if not is_repeat and organization_id:
            background_tasks.add_task(
                award_attendance_gamification,
                user_id=user_id,
                organization_id=organization_id,
                attendance_id=str(attendance.id),
                service_type="sunday_morning"  # Default, could be inferred from service metadata
            )

        message = "Already checked in" if is_repeat else "Check-in successful"

        return ServiceCheckInResponse(
            success=True,
            message=message,
            user_id=user_id,
            attendance_id=str(attendance.id),
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Service member check-in validation error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Service member check-in GPS error: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Service member check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/services/{service_id}/check-in/visitor",
    response_model=ServiceCheckInResponse,
    summary="Register visitor and check in to service",
    description="Register new visitor and check them in to service simultaneously"
)
async def check_in_visitor_to_service(
    service_id: str,
    request: ServiceVisitorCheckInRequest
):
    """
    Register visitor and check in to service.

    Creates new visitor profile if doesn't exist, then checks them in.
    """
    try:
        visitor_data = {
            "name": request.name,
            "phone": request.phone,
            "email": request.email,
            "church_name": request.church_name,
            "department_interests": request.department_interests
        }

        result = await session_attendance_service.check_in_visitor_to_service(
            service_id=service_id,
            visitor_data=visitor_data
        )

        is_new = result.get("is_new_visitor", False)
        is_repeat = result.get("is_repeat_checkin", False)

        if is_repeat:
            message = "Already checked in to this service"
        elif is_new:
            message = "Welcome! Visitor profile created and checked in"
        else:
            message = "Welcome back! Checked in successfully"

        return ServiceCheckInResponse(
            success=True,
            message=message,
            user_id=result["user_id"],
            attendance_id=result["attendance_id"],
            is_new_visitor=is_new,
            is_repeat_checkin=is_repeat
        )

    except ValueError as e:
        logger.warning(f"Service visitor check-in validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Service visitor check-in error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AttendeeInfoResponse(BaseModel):
    """Attendee information response."""
    user_id: str
    name: str
    phone: Optional[str]
    member_status: Optional[str]
    current_spiritual_stage: Optional[str]
    checked_in_at: datetime
    check_in_method: str


@router.get(
    "/services/{service_id}/attendees",
    response_model=List[AttendeeInfoResponse],
    summary="Get service attendees",
    description="Get list of attendees for a service with optional member status filter"
)
async def get_service_attendees(
    service_id: str,
    member_status: Optional[str] = Query(None, description="Filter by member status"),
    admin_user: User = Depends(require_coordinator_or_admin)
):
    """Get service attendees."""
    try:
        attendees = await session_attendance_service.get_service_attendees(
            service_id=service_id,
            member_status=member_status
        )

        return [
            AttendeeInfoResponse(
                user_id=att["user_id"],
                name=att["name"],
                phone=att.get("phone"),
                member_status=att.get("member_status"),
                current_spiritual_stage=att.get("current_spiritual_stage"),
                checked_in_at=att["checked_in_at"],
                check_in_method=att["check_in_method"]
            )
            for att in attendees
        ]

    except Exception as e:
        logger.error(f"Get service attendees error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GAMIFICATION BACKGROUND TASKS
# ============================================================================

async def award_attendance_gamification(
    user_id: str,
    organization_id: str,
    attendance_id: str,
    service_type: str
):
    """
    Background task to award gamification points and update streaks for attendance.

    Args:
        user_id: User ID who checked in
        organization_id: Organization ID
        attendance_id: Attendance record ID
        service_type: Type of service (sunday_morning, midweek_service, conference, etc.)
    """
    try:
        db = get_database()
        gamification_service = get_gamification_service(db)

        # Award points for attendance
        points_result = await gamification_service.award_attendance_points(
            user_id=user_id,
            organization_id=organization_id,
            attendance_id=attendance_id,
            service_type=service_type
        )

        logger.info(
            f"Gamification points awarded: user={user_id}, "
            f"points={points_result['points_awarded']}, "
            f"level_up={points_result['level_up']}, "
            f"new_level={points_result.get('new_level')}"
        )

        # Update attendance streak
        streak_result = await gamification_service.calculate_streak(
            user_id=user_id,
            organization_id=organization_id
        )

        logger.info(
            f"Attendance streak updated: user={user_id}, "
            f"current_streak={streak_result['current_streak']}, "
            f"badges_earned={len(streak_result.get('milestone_badges_earned', []))}"
        )

        # TODO: Send notifications for level up, badges, streak milestones
        # if points_result['level_up']:
        #     await notification_service.send_level_up_notification(...)
        # for badge_id in points_result.get('badges_unlocked', []):
        #     await notification_service.send_badge_earned_notification(...)

    except Exception as e:
        # Log error but don't fail the check-in
        logger.error(f"Gamification background task error: {e}", exc_info=True)

"""
Conference session API endpoints.

This module provides REST API endpoints for managing conference sessions.
Sessions can be created, read, updated, and deleted by conference admins.
Public users can view sessions for any conference.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict
import logging
from datetime import datetime, timezone

from app.schemas.session import (
    SessionResponse,
    CreateSessionRequest,
    UpdateSessionRequest,
    SessionListResponse,
    SessionsByDayResponse,
    ConferenceDaysResponse,
    ConferenceDayInfo
)
from app.services.session_service import session_service
from app.services.session_attendance_service import session_attendance_service
from app.services.conference_service import conference_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


async def _session_to_response(session, include_attendance: bool = True) -> SessionResponse:
    """
    Convert session model to response schema.

    Args:
        session: ConferenceSession model
        include_attendance: Whether to include attendance count (default: True)

    Returns:
        SessionResponse schema
    """
    attendance_count = None
    if include_attendance:
        try:
            attendance_count = await session_attendance_service.get_attendance_count(
                session_id=str(session.id)
            )
        except Exception as e:
            logger.warning(f"Failed to get attendance count for session {session.id}: {e}")
            attendance_count = 0

    return SessionResponse(
        id=str(session.id),
        conference_id=str(session.conference_id),
        name=session.name,
        description=session.description,
        location=session.location,
        day_number=session.day_number,
        day_label=session.day_label,
        session_date=session.session_date,
        start_time=getattr(session, 'start_time', None),
        end_time=getattr(session, 'end_time', None),
        order=session.order,
        sms_confirmation_enabled=getattr(session, 'sms_confirmation_enabled', False) or False,
        sms_confirmation_template=getattr(session, 'sms_confirmation_template', None),
        created_by=str(session.created_by) if session.created_by else None,
        created_at=session.created_at,
        updated_at=session.updated_at,
        attendance_count=attendance_count
    )


@router.post(
    "/conferences/{conference_id}/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conference session",
    description="Create a new session for a conference (admin only)."
)
async def create_session(
    conference_id: str,
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new conference session.

    Only conference admins can create sessions.

    Args:
        conference_id: Parent conference ID
        request: Session creation request
        current_user: Authenticated user (from JWT)

    Returns:
        Created session details

    Raises:
        HTTPException: 400 if validation fails, 404 if conference not found, 500 for server errors
    """
    try:
        session_data = request.model_dump()
        user_id = current_user.get("sub")

        session = await session_service.create_session(
            conference_id=conference_id,
            session_data=session_data,
            user_id=user_id
        )

        return await _session_to_response(session)

    except ValueError as e:
        logger.error(f"Validation error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/sessions",
    response_model=SessionListResponse,
    summary="List conference sessions",
    description="List all sessions for a conference, optionally filtered by day."
)
async def list_sessions(
    conference_id: str,
    day_number: Optional[int] = Query(None, ge=1, description="Filter by day number"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
):
    """
    List all sessions for a conference.

    Public endpoint - anyone can view sessions.

    Args:
        conference_id: Conference ID
        day_number: Optional day number filter
        limit: Maximum number of results

    Returns:
        List of sessions

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        sessions = await session_service.list_sessions(
            conference_id=conference_id,
            day_number=day_number,
            limit=limit
        )

        # Include attendance counts for all sessions
        session_responses = []
        for s in sessions:
            session_responses.append(await _session_to_response(s, include_attendance=True))

        return SessionListResponse(
            sessions=session_responses,
            total=len(sessions),
            conference_id=conference_id
        )

    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/sessions/by-day",
    response_model=SessionsByDayResponse,
    summary="List sessions grouped by day",
    description="Get all sessions organized by day number for easy display."
)
async def list_sessions_by_day(
    conference_id: str
):
    """
    List sessions grouped by conference day.

    Organizes sessions by day_number for easy UI rendering.
    Public endpoint - anyone can view.

    Args:
        conference_id: Conference ID

    Returns:
        Sessions grouped by day number

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        sessions_by_day = await session_service.list_sessions_grouped_by_day(
            conference_id=conference_id
        )

        # Convert to response format with attendance counts
        response_by_day: Dict[str, List[SessionResponse]] = {}
        total_sessions = 0

        for day_num, sessions_list in sessions_by_day.items():
            session_responses = []
            for s in sessions_list:
                session_responses.append(await _session_to_response(s, include_attendance=True))
            response_by_day[str(day_num)] = session_responses
            total_sessions += len(sessions_list)

        return SessionsByDayResponse(
            conference_id=conference_id,
            sessions_by_day=response_by_day,
            total_days=len(sessions_by_day),
            total_sessions=total_sessions
        )

    except Exception as e:
        logger.error(f"Failed to list sessions by day: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions by day: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/days",
    response_model=ConferenceDaysResponse,
    summary="Get conference days",
    description="Get list of all days within the conference date range."
)
async def get_conference_days(
    conference_id: str
):
    """
    Get list of conference days.

    Helpful for UI to show available days when creating sessions.
    Public endpoint.

    Args:
        conference_id: Conference ID

    Returns:
        List of conference days with metadata

    Raises:
        HTTPException: 404 if conference not found, 500 for server errors
    """
    try:
        days = await session_service.generate_conference_days(conference_id)

        return ConferenceDaysResponse(
            conference_id=conference_id,
            days=[ConferenceDayInfo(**day) for day in days],
            total_days=len(days)
        )

    except ValueError as e:
        logger.error(f"Conference not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get conference days: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conference days: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/sessions/today",
    response_model=List[SessionResponse],
    summary="Get today's sessions",
    description="Get all sessions scheduled for today for a conference."
)
async def get_todays_sessions(
    conference_id: str
):
    """
    Get sessions scheduled for today.

    Returns sessions that have session_date matching today's date.
    Public endpoint - anyone can view.

    Args:
        conference_id: Conference ID

    Returns:
        List of sessions scheduled for today

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        sessions = await session_service.get_todays_sessions(
            conference_id=conference_id
        )

        return [
            SessionResponse(
                id=str(s.get("id", s.get("_id", ""))),
                conference_id=str(s.get("conference_id", "")),
                name=s.get("name", ""),
                description=s.get("description"),
                location=s.get("location"),
                day_number=s.get("day_number", 1),
                day_label=s.get("day_label", "Day 1"),
                session_date=s.get("session_date"),
                order=s.get("order", 0),
                sms_confirmation_enabled=s.get("sms_confirmation_enabled", False),
                sms_confirmation_template=s.get("sms_confirmation_template"),
                created_by=str(s.get("created_by")) if s.get("created_by") else None,
                created_at=s.get("created_at"),
                updated_at=s.get("updated_at"),
                attendance_count=s.get("attendance_count", 0)
            )
            for s in sessions
        ]

    except Exception as e:
        logger.error(f"Failed to get today's sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's sessions: {str(e)}"
        )


@router.get(
    "/conferences/{conference_id}/sessions/today-public",
    response_model=List[SessionResponse],
    summary="Get today's sessions (for registration)",
    description="Get today's sessions only if conference is ongoing. Used by registration form for on-site check-in."
)
async def get_todays_sessions_for_registration(
    conference_id: str
):
    """
    Get today's sessions for on-site registration.

    Only returns sessions if the conference is currently ongoing (current datetime
    is between start_date and end_date). Returns empty list if conference is not ongoing.

    This endpoint is used by the registration form to show session options
    when a user is registering at the venue during an ongoing conference.

    Public endpoint - no authentication required.

    Args:
        conference_id: Conference ID

    Returns:
        List of sessions scheduled for today if conference is ongoing, empty list otherwise

    Raises:
        HTTPException: 404 if conference not found, 500 for server errors
    """
    try:
        # Get conference to check if it's ongoing
        conference = await conference_service.get_conference(conference_id)
        if not conference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conference not found"
            )

        # Check if conference is currently ongoing
        now = datetime.utcnow()  # Use timezone-naive datetime to match conference dates
        if not (conference.start_date <= now <= conference.end_date):
            # Conference not ongoing, return empty list
            logger.info(f"Conference {conference_id} is not ongoing. Start: {conference.start_date}, End: {conference.end_date}, Now: {now}")
            return []

        # Conference is ongoing, get today's sessions
        sessions = await session_service.get_todays_sessions(
            conference_id=conference_id
        )

        return [
            SessionResponse(
                id=str(s.get("id", s.get("_id", ""))),
                conference_id=str(s.get("conference_id", "")),
                name=s.get("name", ""),
                description=s.get("description"),
                location=s.get("location"),
                day_number=s.get("day_number", 1),
                day_label=s.get("day_label", "Day 1"),
                session_date=s.get("session_date"),
                order=s.get("order", 0),
                sms_confirmation_enabled=s.get("sms_confirmation_enabled", False),
                sms_confirmation_template=s.get("sms_confirmation_template"),
                created_by=str(s.get("created_by")) if s.get("created_by") else None,
                created_at=s.get("created_at"),
                updated_at=s.get("updated_at"),
                attendance_count=s.get("attendance_count", 0)
            )
            for s in sessions
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get today's sessions for registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's sessions: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session by ID",
    description="Get details of a specific session by session ID only."
)
async def get_session_by_id(
    session_id: str
):
    """
    Get session by ID only (without conference_id).

    Public endpoint - anyone can view session details.
    Useful when you only have the session ID.

    Args:
        session_id: Session ID

    Returns:
        Session details

    Raises:
        HTTPException: 404 if not found
    """
    session = await session_service.get_session(
        session_id=session_id,
        conference_id=None
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return await _session_to_response(session)


@router.get(
    "/conferences/{conference_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session",
    description="Get details of a specific session."
)
async def get_session(
    conference_id: str,
    session_id: str
):
    """
    Get session by ID.

    Public endpoint - anyone can view session details.

    Args:
        conference_id: Conference ID
        session_id: Session ID

    Returns:
        Session details

    Raises:
        HTTPException: 404 if not found
    """
    session = await session_service.get_session(
        session_id=session_id,
        conference_id=conference_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return await _session_to_response(session)


@router.put(
    "/conferences/{conference_id}/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Update session",
    description="Update a conference session (admin only)."
)
async def update_session(
    conference_id: str,
    session_id: str,
    request: UpdateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update conference session.

    Only conference admins can update sessions.

    Args:
        conference_id: Conference ID
        session_id: Session ID
        request: Session update request
        current_user: Authenticated user (from JWT)

    Returns:
        Updated session details

    Raises:
        HTTPException: 404 if not found, 400 for validation errors, 500 for server errors
    """
    try:
        # Only include fields that were actually provided in the request
        update_data = request.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        session = await session_service.update_session(
            session_id=session_id,
            conference_id=conference_id,
            update_data=update_data
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        return await _session_to_response(session)

    except ValueError as e:
        logger.error(f"Validation error updating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete(
    "/conferences/{conference_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete a conference session (admin only)."
)
async def delete_session(
    conference_id: str,
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete conference session.

    Only conference admins can delete sessions.

    Args:
        conference_id: Conference ID
        session_id: Session ID
        current_user: Authenticated user (from JWT)

    Returns:
        No content (204)

    Raises:
        HTTPException: 404 if not found
    """
    deleted = await session_service.delete_session(
        session_id=session_id,
        conference_id=conference_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return None

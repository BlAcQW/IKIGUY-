"""
Conference API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging
from bson import ObjectId

from app.schemas.conference import (
    ConferenceResponse,
    SpeakerResponse,
    CreateConferenceRequest,
    UpdateConferenceRequest,
    ConferenceRegistrationResponse,
    RegisterForConferenceRequest,
    CheckInRequest,
    CheckInResponse
)
from app.services.conference_service import conference_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ConferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conference",
    description="Create a new conference (admin only)."
)
async def create_conference(
    request: CreateConferenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create new conference."""
    try:
        conference_data = request.model_dump()
        conference = await conference_service.create_conference(conference_data)

        return ConferenceResponse(
            id=str(conference.id),
            name=conference.name,
            description=conference.description,
            banner_url=conference.banner_url,
            venue=conference.venue,
            start_date=conference.start_date,
            end_date=conference.end_date,
            registration_open=conference.registration_open,
            registration_deadline=conference.registration_deadline,
            max_attendees=conference.max_attendees,
            current_attendees=conference.current_attendees,
            status=conference.status,
            organizer_id=str(conference.organizer_id) if conference.organizer_id else None,
            created_at=conference.created_at,
            updated_at=conference.updated_at
        )

    except Exception as e:
        logger.error(f"Failed to create conference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conference: {str(e)}"
        )


@router.get(
    "",
    response_model=List[ConferenceResponse],
    summary="List conferences",
    description="List all conferences with optional filters."
)
async def list_conferences(
    status_filter: Optional[str] = Query(None, description="Filter by status", alias="status"),
    registration_open: Optional[bool] = Query(None, description="Filter by registration status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
):
    """List conferences - public endpoint."""
    try:
        conferences = await conference_service.list_conferences(
            status=status_filter,
            registration_open=registration_open,
            limit=limit
        )

        return [
            ConferenceResponse(
                id=str(conf.id),
                name=conf.name,
                description=conf.description,
                theme=getattr(conf, 'theme', None),
                banner_url=conf.banner_url,
                venue=conf.venue,
                venue_latitude=getattr(conf, 'venue_latitude', None),
                venue_longitude=getattr(conf, 'venue_longitude', None),
                venue_checkin_radius=getattr(conf, 'venue_checkin_radius', 1000),
                start_date=conf.start_date,
                end_date=conf.end_date,
                registration_open=conf.registration_open,
                registration_deadline=conf.registration_deadline,
                max_attendees=conf.max_attendees,
                expected_attendance=getattr(conf, 'expected_attendance', None),
                current_attendees=conf.current_attendees,
                status=conf.status,
                self_checkin_enabled=getattr(conf, 'self_checkin_enabled', True),
                allow_repeat_checkin=getattr(conf, 'allow_repeat_checkin', True),
                location_checkin_required=getattr(conf, 'location_checkin_required', True),
                speakers=[
                    SpeakerResponse(
                        name=s.name if hasattr(s, 'name') else s['name'],
                        title=s.title if hasattr(s, 'title') else s.get('title'),
                        image_url=s.image_url if hasattr(s, 'image_url') else s.get('image_url'),
                        bio=s.bio if hasattr(s, 'bio') else s.get('bio')
                    )
                    for s in getattr(conf, 'speakers', [])
                ],
                organizer_id=str(conf.organizer_id) if conf.organizer_id else None,
                contact_phone=getattr(conf, 'contact_phone', None),
                contact_email=getattr(conf, 'contact_email', None),
                website=getattr(conf, 'website', None),
                created_at=conf.created_at,
                updated_at=conf.updated_at
            )
            for conf in conferences
        ]

    except Exception as e:
        logger.error(f"Failed to list conferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conferences: {str(e)}"
        )


@router.get(
    "/{conference_id}",
    response_model=ConferenceResponse,
    summary="Get conference",
    description="Get details of a specific conference."
)
async def get_conference(
    conference_id: str
):
    """Get conference by ID - public endpoint."""
    conference = await conference_service.get_conference(conference_id)

    if not conference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conference not found"
        )

    return ConferenceResponse(
        id=str(conference.id),
        name=conference.name,
        description=conference.description,
        theme=getattr(conference, 'theme', None),
        banner_url=conference.banner_url,
        venue=conference.venue,
        venue_latitude=getattr(conference, 'venue_latitude', None),
        venue_longitude=getattr(conference, 'venue_longitude', None),
        venue_checkin_radius=getattr(conference, 'venue_checkin_radius', 1000),
        start_date=conference.start_date,
        end_date=conference.end_date,
        registration_open=conference.registration_open,
        registration_deadline=conference.registration_deadline,
        max_attendees=conference.max_attendees,
        expected_attendance=getattr(conference, 'expected_attendance', None),
        current_attendees=conference.current_attendees,
        status=conference.status,
        self_checkin_enabled=getattr(conference, 'self_checkin_enabled', True),
        allow_repeat_checkin=getattr(conference, 'allow_repeat_checkin', True),
        location_checkin_required=getattr(conference, 'location_checkin_required', True),
        speakers=[
            SpeakerResponse(
                name=s.name if hasattr(s, 'name') else s['name'],
                title=s.title if hasattr(s, 'title') else s.get('title'),
                image_url=s.image_url if hasattr(s, 'image_url') else s.get('image_url'),
                bio=s.bio if hasattr(s, 'bio') else s.get('bio')
            )
            for s in getattr(conference, 'speakers', [])
        ],
        organizer_id=str(conference.organizer_id) if conference.organizer_id else None,
        contact_phone=getattr(conference, 'contact_phone', None),
        contact_email=getattr(conference, 'contact_email', None),
        website=getattr(conference, 'website', None),
        created_at=conference.created_at,
        updated_at=conference.updated_at
    )


@router.put(
    "/{conference_id}",
    response_model=ConferenceResponse,
    summary="Update conference",
    description="Update conference details (admin only)."
)
async def update_conference(
    conference_id: str,
    request: UpdateConferenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update conference."""
    try:
        update_data = request.model_dump(exclude_none=True)

        conference = await conference_service.update_conference(conference_id, update_data)

        if not conference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conference not found"
            )

        return ConferenceResponse(
            id=str(conference.id),
            name=conference.name,
            description=conference.description,
            banner_url=conference.banner_url,
            venue=conference.venue,
            venue_latitude=conference.venue_latitude,
            venue_longitude=conference.venue_longitude,
            venue_checkin_radius=conference.venue_checkin_radius,
            start_date=conference.start_date,
            end_date=conference.end_date,
            registration_open=conference.registration_open,
            registration_deadline=conference.registration_deadline,
            max_attendees=conference.max_attendees,
            current_attendees=conference.current_attendees,
            status=conference.status,
            self_checkin_enabled=getattr(conference, 'self_checkin_enabled', True),
            allow_repeat_checkin=getattr(conference, 'allow_repeat_checkin', True),
            location_checkin_required=getattr(conference, 'location_checkin_required', True),
            organizer_id=str(conference.organizer_id) if conference.organizer_id else None,
            created_at=conference.created_at,
            updated_at=conference.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conference: {str(e)}"
        )


@router.delete(
    "/{conference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conference",
    description="Delete a conference (admin only)."
)
async def delete_conference(
    conference_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete conference."""
    try:
        deleted = await conference_service.delete_conference(conference_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conference not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conference: {str(e)}"
        )


@router.post(
    "/{conference_id}/register",
    response_model=ConferenceRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register for conference",
    description="Register current user for a conference."
)
async def register_for_conference(
    conference_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Register for conference."""
    try:
        registration = await conference_service.register_for_conference(
            user_id=current_user["sub"],
            conference_id=conference_id
        )

        return ConferenceRegistrationResponse(
            id=str(registration.id),
            user_id=str(registration.user_id),
            conference_id=str(registration.conference_id),
            qr_code=registration.qr_code,
            registration_time=registration.registration_time,
            checked_in=registration.checked_in,
            check_in_time=registration.check_in_time,
            status=registration.status
        )

    except Exception as e:
        logger.error(f"Failed to register for conference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/check-in",
    response_model=CheckInResponse,
    summary="Check in user with QR code",
    description="Check in a user using their QR code."
)
async def check_in_user(
    request: CheckInRequest,
    current_user: dict = Depends(get_current_user)
):
    """Check in user with QR code."""
    try:
        result = await conference_service.check_in_user(request.qr_code)

        return CheckInResponse(**result)

    except Exception as e:
        logger.error(f"Failed to check in user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

"""
Events API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.database import get_database
from ...schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    DashboardResponse,
)
from ...schemas.task import TaskResponse
from ...schemas.responsible_person import ResponsiblePersonResponse
from ...services.event_service import EventService


router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a new event.

    Args:
        event_data: Event creation data
        db: Database instance

    Returns:
        Created event
    """
    # Use demo organizer ID for public demo
    demo_organizer_id = "demo_user_123"
    event_service = EventService(db)
    event = await event_service.create_event(demo_organizer_id, event_data)

    return EventResponse(**event.model_dump())


@router.get("", response_model=EventListResponse)
async def list_events(
    status: Optional[str] = Query(None, description="Filter by status (comma-separated)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List all events (public demo mode).

    Args:
        status: Optional status filter
        page: Page number
        page_size: Page size
        db: Database instance

    Returns:
        List of events
    """
    event_service = EventService(db)

    # Parse status filter
    status_filter = None
    if status:
        status_filter = [s.strip() for s in status.split(",")]

    skip = (page - 1) * page_size
    # Return all events (no user filtering for public demo)
    events, total = await event_service.list_all_events(
        status_filter=status_filter,
        skip=skip,
        limit=page_size,
    )

    return EventListResponse(
        data=[EventResponse(**e.model_dump()) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get event by ID (public demo mode).

    Args:
        event_id: Event ID
        db: Database instance

    Returns:
        Event details
    """
    event_service = EventService(db)
    event = await event_service.get_event_public(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return EventResponse(**event.model_dump())


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update event (public demo mode).

    Args:
        event_id: Event ID
        event_update: Update data
        db: Database instance

    Returns:
        Updated event
    """
    event_service = EventService(db)
    event = await event_service.update_event_public(event_id, event_update)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return EventResponse(**event.model_dump())


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Delete event (public demo mode).

    Args:
        event_id: Event ID
        db: Database instance
    """
    event_service = EventService(db)
    deleted = await event_service.delete_event_public(event_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )


@router.get("/{event_id}/dashboard", response_model=DashboardResponse)
async def get_event_dashboard(
    event_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get event dashboard with statistics (public demo mode).

    Args:
        event_id: Event ID
        db: Database instance

    Returns:
        Dashboard statistics
    """
    event_service = EventService(db)
    dashboard = await event_service.get_dashboard_public(event_id)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return dashboard


@router.post("/{event_id}/generate-tasks", response_model=List[TaskResponse])
async def generate_event_tasks(
    event_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Generate AI-powered tasks for event (public demo mode).

    Args:
        event_id: Event ID
        db: Database instance

    Returns:
        List of generated tasks
    """
    event_service = EventService(db)
    tasks = await event_service.generate_tasks_public(event_id)

    return [TaskResponse(**t.model_dump()) for t in tasks]


@router.get("/{event_id}/persons", response_model=List[ResponsiblePersonResponse])
async def list_event_persons(
    event_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List responsible persons for an event (public demo mode).

    Args:
        event_id: Event ID
        db: Database instance

    Returns:
        List of responsible persons for the event
    """
    # Verify event exists
    event_service = EventService(db)
    event = await event_service.get_event_public(event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Get all persons for this event
    persons = []
    async for person_doc in db["responsible_persons"].find({"event_id": event_id}):
        person_doc["_id"] = str(person_doc["_id"])
        persons.append(ResponsiblePersonResponse(**person_doc))

    return persons

"""
Event schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    """Event creation schema."""

    name: str = Field(..., description="Event name")
    type: str = Field(..., description="Event type")
    date: datetime = Field(..., description="Event date")
    location: str = Field(..., description="Event location")
    num_guests: int = Field(..., description="Number of guests")
    budget_min: Optional[float] = Field(None, description="Minimum budget")
    budget_max: Optional[float] = Field(None, description="Maximum budget")
    description: Optional[str] = Field(None, description="Event description")
    tags: List[str] = Field(default_factory=list, description="Tags")


class EventUpdate(BaseModel):
    """Event update schema."""

    name: Optional[str] = None
    type: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    num_guests: Optional[int] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class EventResponse(BaseModel):
    """Event response schema."""

    id: str
    name: str
    type: str
    date: datetime
    location: str
    num_guests: int
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    status: str
    organizer_id: str
    description: Optional[str] = None
    documents: List[str] = []
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    """Event list response schema."""

    data: List[EventResponse]
    total: int
    page: int = 1
    page_size: int = 50


class TaskStats(BaseModel):
    """Task statistics."""

    total: int
    completed: int
    in_progress: int
    pending: int
    overdue: int
    completion_rate: float


class DashboardResponse(BaseModel):
    """Event dashboard response schema."""

    event_id: str
    tasks: TaskStats
    responsible_persons_count: int
    days_until_event: int
    budget_spent: float = 0.0
    budget_remaining: float = 0.0

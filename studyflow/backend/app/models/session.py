"""
Study session models for StudyFlow.

Tracks tutoring sessions, questions asked, and learning activity.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class SessionStatus(str, Enum):
    """Study session status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StudySession(BaseModel):
    """
    Study session model.

    Tracks a student's learning session including questions asked,
    time spent, and costs incurred.

    Attributes:
        id: MongoDB ObjectId as string
        organization_id: Organization ID for multi-tenancy
        school_id: School ID (optional)
        student_id: Student user ID
        subject: Subject being studied
        topics: List of topics covered
        status: Session status
        started_at: Session start time
        ended_at: Session end time
        duration_minutes: Total session duration
        questions_asked: Number of questions asked
        questions_answered: Number of questions answered
        cost_incurred: Total cost in GHS
        rag_queries: List of RAG queries made
        metadata: Additional session data
        created_at: Session creation timestamp
        updated_at: Last update timestamp
    """
    id: Optional[str] = Field(default=None, alias="_id")
    organization_id: str
    school_id: Optional[str] = None
    student_id: str
    subject: str
    topics: List[str] = Field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_minutes: float = 0.0

    questions_asked: int = 0
    questions_answered: int = 0
    cost_incurred: float = 0.0

    rag_queries: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class SessionCreate(BaseModel):
    """
    Schema for creating a new study session.

    Attributes:
        organization_id: Organization ID for multi-tenancy
        school_id: School ID (optional)
        student_id: Student user ID
        subject: Subject being studied
        topics: Initial topics (optional)
    """
    organization_id: str
    school_id: Optional[str] = None
    student_id: str
    subject: str
    topics: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    """
    Schema for updating a study session.

    All fields are optional for partial updates.
    """
    status: Optional[SessionStatus] = None
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    questions_asked: Optional[int] = None
    questions_answered: Optional[int] = None
    cost_incurred: Optional[float] = None
    topics: Optional[List[str]] = None
    metadata: Optional[dict] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionResponse(BaseModel):
    """
    Study session response model for API responses.
    """
    id: str
    organization_id: str
    school_id: Optional[str]
    student_id: str
    subject: str
    topics: List[str]
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: float
    questions_asked: int
    questions_answered: int
    cost_incurred: float

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionSummary(BaseModel):
    """
    Summary of study sessions for analytics.

    Used for dashboard displays and reports.
    """
    total_sessions: int
    total_duration_minutes: float
    total_questions: int
    total_cost: float
    subjects_studied: List[str]
    most_active_subject: Optional[str] = None
    average_session_duration: float = 0.0
    period_start: datetime
    period_end: datetime

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

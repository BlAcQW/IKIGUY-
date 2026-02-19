"""
Task model for EventFlow.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class Task(BaseModel):
    """Task model."""

    event_id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    category: str = Field(..., description="Task category/department")
    priority: str = Field(default="medium", description="Task priority")
    status: str = Field(default="pending", description="Task status")
    assigned_to: Optional[str] = Field(
        None, description="ID of responsible person"
    )
    deadline: datetime = Field(..., description="Task deadline")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    notes: Optional[str] = Field(None, description="Task notes")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost (GHS)")
    dependencies: list[str] = Field(
        default_factory=list, description="Task IDs that must complete first"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "event_id": "507f1f77bcf86cd799439011",
                "title": "Book conference venue",
                "description": "Confirm booking for main hall",
                "category": "venue",
                "priority": "high",
                "status": "pending",
                "assigned_to": "507f1f77bcf86cd799439012",
                "deadline": "2025-02-01T23:59:59Z",
                "cost_estimate": 15000,
            }
        }


class TaskInDB(Task):
    """Task model with database ID."""

    id: str = Field(alias="_id")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

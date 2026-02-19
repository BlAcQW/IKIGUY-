"""
Task schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Task creation schema."""

    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    category: str = Field(..., description="Task category")
    priority: str = Field(default="medium", description="Task priority")
    assigned_to: Optional[str] = Field(None, description="Responsible person ID")
    deadline: datetime = Field(..., description="Task deadline")
    cost_estimate: Optional[float] = Field(None, description="Cost estimate")


class TaskUpdate(BaseModel):
    """Task update schema."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None
    cost_estimate: Optional[float] = None


class ResponsiblePersonInfo(BaseModel):
    """Responsible person info in task response."""

    id: str
    name: str
    phone: str
    role: str


class TaskResponse(BaseModel):
    """Task response schema."""

    id: str
    event_id: str
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    assigned_person: Optional[ResponsiblePersonInfo] = None
    deadline: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    cost_estimate: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Task list response schema."""

    data: List[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 100

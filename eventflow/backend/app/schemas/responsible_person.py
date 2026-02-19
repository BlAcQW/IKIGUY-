"""
Responsible Person schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ResponsiblePersonCreate(BaseModel):
    """Responsible person creation schema."""

    name: str = Field(..., description="Person's full name")
    phone: str = Field(..., description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    role: str = Field(..., description="Role/department")
    notes: Optional[str] = Field(None, description="Notes")


class ResponsiblePersonUpdate(BaseModel):
    """Responsible person update schema."""

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class ResponsiblePersonResponse(BaseModel):
    """Responsible person response schema."""

    id: str
    event_id: str
    name: str
    phone: str
    email: Optional[str] = None
    role: str
    user_id: Optional[str] = None
    notes: Optional[str] = None

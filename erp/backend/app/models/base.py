"""
Base model for all ERP entities.

All models inherit from this to ensure organization scoping.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel, Field
import uuid


class BaseModel(PydanticBaseModel):
    """
    Base model for all ERP entities.

    Automatically includes organization_id for multi-tenant isolation.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = Field(..., description="Organization this entity belongs to")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User ID who created this")
    updated_by: Optional[str] = Field(None, description="User ID who last updated this")
    is_active: bool = Field(default=True)

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat() if isinstance(v, date) else v
        }
        populate_by_name = True

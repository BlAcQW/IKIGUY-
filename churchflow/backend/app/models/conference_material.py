"""
Conference Material Model.

Represents files and documents attached to conferences (brochures, schedules, maps, etc).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class ConferenceMaterial(BaseModel):
    """
    Conference material document model.

    Attributes:
        id: Unique identifier
        conference_id: ID of associated conference
        organization_id: ID of organization
        title: Material title/name
        description: Optional description
        file_name: Original filename
        file_path: Storage path on server
        file_size: File size in bytes
        file_type: MIME type
        material_type: Category (brochure, schedule, map, form, other)
        is_public: Whether material is publicly accessible
        display_on_landing: Whether to show on conference landing page
        display_order: Order for display (lower numbers first)
        uploaded_by: User ID who uploaded the material
        created_at: Upload timestamp
        updated_at: Last update timestamp
    """

    id: Optional[ObjectId] = Field(None, alias="_id")
    conference_id: ObjectId
    organization_id: ObjectId
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    file_name: str
    file_path: str
    file_size: int = Field(..., gt=0)
    file_type: str
    material_type: str = Field(
        default="other",
        pattern="^(brochure|schedule|map|form|flyer|guide|other)$"
    )
    is_public: bool = Field(default=True)
    display_on_landing: bool = Field(default=False)
    display_order: int = Field(default=0, ge=0)
    uploaded_by: ObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "conference_id": "507f1f77bcf86cd799439011",
                "organization_id": "507f1f77bcf86cd799439012",
                "title": "ACI Impact 2025 Brochure",
                "description": "Official conference brochure with schedule and speaker information",
                "file_name": "aci-impact-2025-brochure.pdf",
                "file_path": "storage/conference_materials/aci-impact-2025-brochure.pdf",
                "file_size": 8077824,
                "file_type": "application/pdf",
                "material_type": "brochure",
                "is_public": True,
                "display_on_landing": True,
                "display_order": 1,
                "uploaded_by": "507f1f77bcf86cd799439013"
            }
        }

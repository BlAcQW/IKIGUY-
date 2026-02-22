"""
Leads API Router

Public endpoint for lead form submissions (no auth required).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_database
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadSubmission(BaseModel):
    """Request model for public lead form submission."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=30)
    property_id: str = Field(..., min_length=1)


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_lead(
    data: LeadSubmission,
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Submit a lead from the public contact form.

    Public endpoint - no authentication required.
    Resolves organization_id from the property.
    Creates a warm lead via LeadService.

    Args:
        data: Lead form submission data
        database: Database instance

    Returns:
        Success message with contact_id
    """
    # Resolve organization_id from the property
    from bson import ObjectId

    properties_collection = database["properties"]

    # Try ObjectId lookup first, then string id field
    property_doc = None
    try:
        property_doc = await properties_collection.find_one(
            {"_id": ObjectId(data.property_id)}
        )
    except Exception:
        pass

    if not property_doc:
        property_doc = await properties_collection.find_one(
            {"id": data.property_id}
        )

    if not property_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    organization_id = property_doc.get("organization_id")
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property has no associated organization",
        )

    property_name = property_doc.get("title") or property_doc.get("name")

    lead_service = LeadService(database)
    result = await lead_service.upsert_lead(
        organization_id=organization_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        interest_status="warm",
        source="lead_form",
        property_id=data.property_id,
        property_name=property_name,
    )

    return {
        "message": "Thank you! We'll be in touch shortly.",
        "contact_id": result["contact_id"],
    }

"""Industry routes for managing industry configurations."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models import Industry, IndustryCreate, IndustryUpdate
from ..services.industry_service import industry_service
from ..auth import get_current_user_mongo

router = APIRouter(prefix="/api/industries", tags=["industries"])


@router.get("/", response_model=List[Industry])
def list_industries(active_only: bool = True):
    """List all industries."""
    return industry_service.list_industries(active_only=active_only)


@router.get("/{industry_id}", response_model=Industry)
def get_industry(industry_id: str):
    """Get an industry by ID."""
    industry = industry_service.get_industry(industry_id)
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry


@router.post("/", response_model=Industry)
def create_industry(
    industry_data: IndustryCreate,
    user: dict = Depends(get_current_user_mongo)
):
    """Create a new industry (authenticated users only)."""
    try:
        return industry_service.create_industry(industry_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{industry_id}", response_model=Industry)
def update_industry(
    industry_id: str,
    update_data: IndustryUpdate,
    user: dict = Depends(get_current_user_mongo)
):
    """Update an industry (authenticated users only)."""
    industry = industry_service.update_industry(industry_id, update_data)
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry


@router.delete("/{industry_id}")
def delete_industry(
    industry_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Delete an industry (authenticated users only)."""
    success = industry_service.delete_industry(industry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Industry not found")
    return {"message": "Industry deleted successfully"}


@router.get("/{industry_id}/integrations")
def get_industry_integrations(industry_id: str):
    """Get standard integrations for an industry."""
    integrations = industry_service.get_industry_integrations(industry_id)
    return {"industry_id": industry_id, "integrations": integrations}


@router.post("/populate-defaults", response_model=List[Industry])
def populate_default_industries(user: dict = Depends(get_current_user_mongo)):
    """Populate default industries (authenticated users only)."""
    try:
        industries = industry_service.populate_default_industries()
        return industries
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-name/{name}", response_model=Industry)
def get_industry_by_name(name: str):
    """Get an industry by name."""
    industry = industry_service.get_industry_by_name(name)
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry
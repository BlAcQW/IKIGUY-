"""
Integration Categories API routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..services.integration_category_service import (
    integration_category_service,
    IntegrationCategory,
    IntegrationCategoryCreate,
    IntegrationCategoryUpdate
)
from ..auth import get_current_user_mongo

router = APIRouter(prefix="/integration-categories", tags=["Integration Categories"])


@router.get("/", response_model=List[IntegrationCategory])
def list_integration_categories():
    """List all integration categories."""
    return integration_category_service.list_categories()


@router.get("/{category_id}", response_model=IntegrationCategory)
def get_integration_category(category_id: str):
    """Get integration category by ID."""
    category = integration_category_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Integration category not found")
    return category


@router.post("/", response_model=IntegrationCategory)
def create_integration_category(
    category_data: IntegrationCategoryCreate,
    user: dict = Depends(get_current_user_mongo)
):
    """Create a new integration category (authenticated users only)."""
    return integration_category_service.create_category(category_data)


@router.put("/{category_id}", response_model=IntegrationCategory)
def update_integration_category(
    category_id: str,
    update_data: IntegrationCategoryUpdate,
    user: dict = Depends(get_current_user_mongo)
):
    """Update an integration category (authenticated users only)."""
    category = integration_category_service.update_category(category_id, update_data)
    if not category:
        raise HTTPException(status_code=404, detail="Integration category not found")
    return category


@router.delete("/{category_id}")
def delete_integration_category(
    category_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Delete an integration category (authenticated users only)."""
    success = integration_category_service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration category not found")
    return {"message": "Integration category deleted successfully"}


@router.post("/populate-defaults", response_model=List[IntegrationCategory])
def populate_default_integration_categories(user: dict = Depends(get_current_user_mongo)):
    """Populate default integration categories (authenticated users only)."""
    return integration_category_service.populate_default_categories()
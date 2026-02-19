"""
Integrations API routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ..services.integration_catalog_service import (
    integration_catalog_service,
    Integration,
    IntegrationCreate,
    IntegrationUpdate
)
from ..auth import get_current_user_mongo

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("/", response_model=List[Integration])
async def list_integrations():
    """List all integrations."""
    return await integration_catalog_service.list_integrations()


@router.get("/category/{category_id}", response_model=List[Integration])
async def list_integrations_by_category(category_id: str):
    """List integrations by category."""
    return await integration_catalog_service.list_integrations_by_category(category_id)


@router.get("/{integration_id}", response_model=Integration)
async def get_integration(integration_id: str):
    """Get integration by ID."""
    integration = await integration_catalog_service.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.post("/", response_model=Integration)
async def create_integration(
    integration_data: IntegrationCreate,
    user: dict = Depends(get_current_user_mongo)
):
    """Create a new integration (authenticated users only)."""
    return await integration_catalog_service.create_integration(integration_data)


@router.put("/{integration_id}", response_model=Integration)
async def update_integration(
    integration_id: str,
    update_data: IntegrationUpdate,
    user: dict = Depends(get_current_user_mongo)
):
    """Update an integration (authenticated users only)."""
    integration = await integration_catalog_service.update_integration(integration_id, update_data)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    user: dict = Depends(get_current_user_mongo)
):
    """Delete an integration (authenticated users only)."""
    success = await integration_catalog_service.delete_integration(integration_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"message": "Integration deleted successfully"}


@router.post("/populate-defaults", response_model=List[Integration])
async def populate_default_integrations(user: dict = Depends(get_current_user_mongo)):
    """Populate default integrations (authenticated users only)."""
    return await integration_catalog_service.populate_default_integrations()
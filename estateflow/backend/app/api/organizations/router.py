"""
Organization API endpoints for EstateFlow.

Provides organization management for admin users.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.database import get_database
from app.core.auth import get_current_user
from app.models.organization import Organization, OrganizationListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    """Organization creation model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    email: str | None = None
    phone: str | None = None


class OrganizationUpdate(BaseModel):
    """Organization update model."""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    email: str | None = None
    phone: str | None = None


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all organizations (admin only).

    Regular users will only see their own organization.
    Admin users (admin@ailabsafrica.com or role=admin) see all organizations.

    Args:
        limit: Page size
        offset: Page offset
        database: Database instance
        current_user: Current authenticated user

    Returns:
        List of organizations
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        organizations_collection = database["organizations"]

        if is_admin:
            # Admin: fetch all organizations
            total = await organizations_collection.count_documents({})
            cursor = organizations_collection.find({}).skip(offset).limit(limit)
            orgs_list = await cursor.to_list(length=limit)
        else:
            # Regular user: only their organization
            user_org_id = current_user.get("organization_id") or current_user.get("id")
            org = await organizations_collection.find_one({"id": user_org_id})
            orgs_list = [org] if org else []
            total = 1 if org else 0

        organizations = [Organization(**org) for org in orgs_list]

        return OrganizationListResponse(
            organizations=organizations,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing organizations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list organizations"
        )


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get organization by ID.

    Args:
        organization_id: Organization ID
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Organization details

    Raises:
        HTTPException: If organization not found or access denied
    """
    try:
        # Check if user is admin or accessing their own organization
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )
        user_org_id = current_user.get("organization_id") or current_user.get("id")

        if not is_admin and organization_id != user_org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot access other organizations"
            )

        organizations_collection = database["organizations"]
        org = await organizations_collection.find_one({"id": organization_id})

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )

        return Organization(**org)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization"
        )


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new organization (admin only).

    Args:
        org_data: Organization data
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Created organization

    Raises:
        HTTPException: If user is not admin or creation fails
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create organizations"
            )

        organizations_collection = database["organizations"]

        # Check if organization name already exists
        existing = await organizations_collection.find_one({"name": org_data.name})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with name '{org_data.name}' already exists"
            )

        # Create organization document
        org_id = str(uuid.uuid4()).replace("-", "")[:24]
        now = datetime.utcnow()

        org_doc = {
            "id": org_id,
            "name": org_data.name,
            "description": org_data.description,
            "email": org_data.email,
            "phone": org_data.phone,
            "created_at": now,
            "updated_at": now
        }

        # Insert into database
        await organizations_collection.insert_one(org_doc)

        logger.info(f"Organization created: {org_id} by {current_user.get('email')}")

        return Organization(**org_doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )


@router.put("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: str,
    org_data: OrganizationUpdate,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update organization (admin only).

    Args:
        organization_id: Organization ID
        org_data: Organization update data
        database: Database instance
        current_user: Current authenticated user

    Returns:
        Updated organization

    Raises:
        HTTPException: If user is not admin, organization not found, or update fails
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update organizations"
            )

        organizations_collection = database["organizations"]

        # Check if organization exists
        org = await organizations_collection.find_one({"id": organization_id})
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )

        # Build update document (only include provided fields)
        update_data = {"updated_at": datetime.utcnow()}

        if org_data.name is not None:
            # Check if new name conflicts with existing organization
            existing = await organizations_collection.find_one({
                "name": org_data.name,
                "id": {"$ne": organization_id}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Organization with name '{org_data.name}' already exists"
                )
            update_data["name"] = org_data.name

        if org_data.description is not None:
            update_data["description"] = org_data.description
        if org_data.email is not None:
            update_data["email"] = org_data.email
        if org_data.phone is not None:
            update_data["phone"] = org_data.phone

        # Update organization
        await organizations_collection.update_one(
            {"id": organization_id},
            {"$set": update_data}
        )

        # Fetch updated organization
        updated_org = await organizations_collection.find_one({"id": organization_id})

        logger.info(f"Organization updated: {organization_id} by {current_user.get('email')}")

        return Organization(**updated_org)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete organization (admin only).

    WARNING: This will not delete associated data (properties, contacts, etc.).
    Use with caution.

    Args:
        organization_id: Organization ID
        database: Database instance
        current_user: Current authenticated user

    Raises:
        HTTPException: If user is not admin, organization not found, or deletion fails
    """
    try:
        # Check if user is admin
        is_admin = (
            current_user.get("email") == "admin@ailabsafrica.com" or
            current_user.get("role") == "admin"
        )

        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete organizations"
            )

        organizations_collection = database["organizations"]

        # Check if organization exists
        org = await organizations_collection.find_one({"id": organization_id})
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )

        # TODO: Check if organization has associated data
        # For now, we'll allow deletion and orphan the data
        # In production, you might want to:
        # 1. Prevent deletion if data exists
        # 2. Cascade delete all associated data
        # 3. Soft delete (mark as deleted)

        # Delete organization
        result = await organizations_collection.delete_one({"id": organization_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete organization"
            )

        logger.info(f"Organization deleted: {organization_id} by {current_user.get('email')}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization"
        )

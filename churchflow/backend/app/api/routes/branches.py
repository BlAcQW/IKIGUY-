"""
Branch management API routes.

Endpoints for managing church branches.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient
import os

router = APIRouter(tags=["Branches"])

# MongoDB connection
def get_db():
    """Get MongoDB database connection."""
    mongodb_url = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:aawwER4444%25@127.0.0.1:27017/churchflow?authSource=admin"
    )
    client = MongoClient(mongodb_url)
    return client.churchflow


# Request/Response Models
class CreateBranchRequest(BaseModel):
    """Request model for creating a branch."""
    name: str
    location: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    capacity: Optional[int] = 100
    status: str = "active"


class UpdateBranchRequest(BaseModel):
    """Request model for updating a branch."""
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class BranchResponse(BaseModel):
    """Response model for a branch."""
    id: str
    name: str
    location: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    capacity: Optional[int] = None
    status: str
    created_at: str


@router.get("/", response_model=List[BranchResponse])
async def list_branches():
    """
    List all branches.

    Returns:
        List of branches sorted alphabetically by name
    """
    db = get_db()

    # Get branches sorted alphabetically by name
    # Reason: Using MongoDB sort for better performance than Python sorting
    branches = list(db.branches.find().sort("name", 1))

    # Format response
    return [
        BranchResponse(
            id=str(branch["_id"]),
            name=branch["name"],
            location=branch["location"],
            address=branch.get("address"),
            contact_person=branch.get("contact_person"),
            contact_phone=branch.get("contact_phone"),
            capacity=branch.get("capacity", 100),
            status=branch.get("status", "active"),
            created_at=branch["created_at"].isoformat() if isinstance(branch.get("created_at"), datetime) else datetime.utcnow().isoformat()
        )
        for branch in branches
    ]


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(branch_id: str):
    """
    Get a specific branch by ID.

    Args:
        branch_id: Branch ID

    Returns:
        Branch details
    """
    db = get_db()

    # Validate ObjectId
    if not ObjectId.is_valid(branch_id):
        raise HTTPException(status_code=400, detail="Invalid branch ID")

    # Get branch
    branch = db.branches.find_one({"_id": ObjectId(branch_id)})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    return BranchResponse(
        id=str(branch["_id"]),
        name=branch["name"],
        location=branch["location"],
        address=branch.get("address"),
        contact_person=branch.get("contact_person"),
        contact_phone=branch.get("contact_phone"),
        capacity=branch.get("capacity", 100),
        status=branch.get("status", "active"),
        created_at=branch["created_at"].isoformat() if isinstance(branch.get("created_at"), datetime) else datetime.utcnow().isoformat()
    )


@router.post("/", response_model=BranchResponse, status_code=201)
async def create_branch(request: CreateBranchRequest):
    """
    Create a new branch.

    DISABLED: Branch creation is not allowed. Branches are predefined.

    Args:
        request: Branch creation data

    Returns:
        Created branch
    """
    # Reason: Branches are now fixed and cannot be created through the API
    raise HTTPException(
        status_code=403,
        detail="Branch creation is disabled. Branches are predefined and cannot be modified through the admin interface."
    )


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(branch_id: str, request: UpdateBranchRequest):
    """
    Update a branch.

    DISABLED: Branch updates are not allowed. Branches are predefined.

    Args:
        branch_id: Branch ID
        request: Branch update data

    Returns:
        Updated branch
    """
    # Reason: Branches are now fixed and cannot be updated through the API
    raise HTTPException(
        status_code=403,
        detail="Branch updates are disabled. Branches are predefined and cannot be modified through the admin interface."
    )


@router.delete("/{branch_id}", status_code=204)
async def delete_branch(branch_id: str):
    """
    Delete a branch.

    DISABLED: Branch deletion is not allowed. Branches are predefined.

    Args:
        branch_id: Branch ID
    """
    # Reason: Branches are now fixed and cannot be deleted through the API
    raise HTTPException(
        status_code=403,
        detail="Branch deletion is disabled. Branches are predefined and cannot be modified through the admin interface."
    )

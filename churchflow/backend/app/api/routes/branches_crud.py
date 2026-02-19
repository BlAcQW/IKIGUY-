"""
Branch CRUD API routes with geolocation support.

Provides complete CRUD operations for managing church branches with GPS coordinates
for proximity-based check-in functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.database import get_database
from app.models.branch import (
    Branch,
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    ServiceSchedule
)
from app.models.user import User
from app.dependencies import get_current_user_profile

router = APIRouter(prefix="/branches", tags=["branches"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def verify_organization_access(current_user: User, organization_id: str) -> None:
    """
    Verify user has access to the specified organization.

    Args:
        current_user: Current authenticated user
        organization_id: Organization ID to check access for

    Raises:
        HTTPException: 403 if user doesn't have access
    """
    user_org_id = str(current_user.organization_id) if current_user.organization_id else None
    is_admin = "admin" in current_user.roles or "universal_admin" in current_user.roles
    if not is_admin and user_org_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You don't have access to this organization"
        )


def branch_to_response(branch_doc: dict) -> BranchResponse:
    """
    Convert MongoDB branch document to API response.

    Args:
        branch_doc: Branch document from MongoDB

    Returns:
        BranchResponse model
    """
    # Calculate computed fields
    has_coordinates = (
        branch_doc.get("latitude") is not None and
        branch_doc.get("longitude") is not None
    )
    can_auto_checkin = (
        has_coordinates and
        branch_doc.get("auto_checkin_enabled", False) and
        branch_doc.get("is_active", True)
    )

    return BranchResponse(
        id=str(branch_doc["_id"]),
        organization_id=str(branch_doc["organization_id"]),
        name=branch_doc.get("name") or "",
        location=branch_doc.get("location") or "",
        region=branch_doc.get("region") or "",
        latitude=branch_doc.get("latitude"),
        longitude=branch_doc.get("longitude"),
        checkin_radius=branch_doc.get("checkin_radius", 500),
        auto_checkin_enabled=branch_doc.get("auto_checkin_enabled", False),
        geocoding_accuracy=branch_doc.get("geocoding_accuracy"),
        service_times=branch_doc.get("service_times", []),
        is_active=branch_doc.get("is_active", True),
        created_at=branch_doc.get("created_at", datetime.utcnow()),
        updated_at=branch_doc.get("updated_at", datetime.utcnow()),
        has_coordinates=has_coordinates,
        can_auto_checkin=can_auto_checkin
    )


# ============================================================================
# READ OPERATIONS
# ============================================================================

@router.get("/", response_model=List[BranchResponse])
async def list_branches(
    organization_id: Optional[str] = Query(None, description="Organization ID (defaults to user's organization)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    has_coordinates: Optional[bool] = Query(None, description="Filter branches with GPS coordinates"),
    auto_checkin_enabled: Optional[bool] = Query(None, description="Filter by auto check-in status"),
    region: Optional[str] = Query(None, description="Filter by region"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    List all branches for an organization with optional filtering.

    Query Parameters:
        organization_id: Organization ID (optional, defaults to user's organization)
        is_active: Filter by active status
        has_coordinates: Filter branches with GPS data
        auto_checkin_enabled: Filter by auto check-in status
        region: Filter by region name
        skip: Pagination offset
        limit: Maximum results (1-500)

    Returns:
        List of branches sorted by name
    """
    # Default to user's organization if not specified
    if not organization_id:
        if not current_user.organization_id:
            raise HTTPException(
                status_code=400,
                detail="No organization_id specified and user is not associated with an organization"
            )
        organization_id = str(current_user.organization_id)
    else:
        # Verify user has access to the requested organization
        verify_organization_access(current_user, organization_id)

    # Build query filter
    query_filter = {"organization_id": ObjectId(organization_id)}

    if is_active is not None:
        query_filter["is_active"] = is_active

    if has_coordinates is not None:
        if has_coordinates:
            query_filter["latitude"] = {"$ne": None}
            query_filter["longitude"] = {"$ne": None}
        else:
            query_filter["$or"] = [
                {"latitude": None},
                {"longitude": None}
            ]

    if auto_checkin_enabled is not None:
        query_filter["auto_checkin_enabled"] = auto_checkin_enabled

    if region:
        query_filter["region"] = {"$regex": region, "$options": "i"}

    # Execute query
    cursor = db.branches.find(query_filter).sort("name", 1).skip(skip).limit(limit)
    branches = await cursor.to_list(length=limit)

    return [branch_to_response(branch) for branch in branches]


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Get a single branch by ID.

    Args:
        branch_id: Branch ID

    Returns:
        Branch details

    Raises:
        404: Branch not found
        403: User doesn't have access to organization
    """
    # Find branch
    branch = await db.branches.find_one({"_id": ObjectId(branch_id)})

    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    # Verify user has access to organization
    verify_organization_access(current_user, str(branch["organization_id"]))

    return branch_to_response(branch)


@router.get("/search/nearby")
async def search_nearby_branches(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude coordinate"),
    max_distance: int = Query(5000, ge=100, le=50000, description="Maximum distance in meters"),
    organization_id: str = Query(..., description="Organization ID"),
    auto_checkin_only: bool = Query(False, description="Only branches with auto check-in enabled"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Search for branches near a GPS coordinate.

    Uses MongoDB geospatial query to find branches within specified distance.

    Query Parameters:
        latitude: GPS latitude (-90 to 90)
        longitude: GPS longitude (-180 to 180)
        max_distance: Maximum distance in meters (100-50000)
        organization_id: Organization ID
        auto_checkin_only: Only return branches with auto check-in enabled

    Returns:
        List of nearby branches sorted by distance (nearest first)
    """
    # Verify user has access
    verify_organization_access(current_user, organization_id)

    # Build query
    query_filter = {
        "organization_id": ObjectId(organization_id),
        "is_active": True,
        "latitude": {"$ne": None},
        "longitude": {"$ne": None}
    }

    if auto_checkin_only:
        query_filter["auto_checkin_enabled"] = True

    # Fetch all branches with coordinates
    cursor = db.branches.find(query_filter)
    branches = await cursor.to_list(length=None)

    # Calculate distances using Haversine formula
    import math

    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance in meters."""
        R = 6371000  # Earth radius in meters
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # Filter by distance and add distance field
    nearby_branches = []
    for branch in branches:
        distance = haversine_distance(
            latitude, longitude,
            branch["latitude"], branch["longitude"]
        )

        if distance <= max_distance:
            branch_response = branch_to_response(branch)
            nearby_branches.append({
                **branch_response.model_dump(),
                "distance": round(distance, 2)  # Distance in meters
            })

    # Sort by distance
    nearby_branches.sort(key=lambda x: x["distance"])

    return nearby_branches


# ============================================================================
# CREATE OPERATION
# ============================================================================

@router.post("/", response_model=BranchResponse, status_code=201)
async def create_branch(
    branch_data: BranchCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Create a new branch.

    Requires admin role.

    Request Body:
        BranchCreate model with branch details

    Returns:
        Created branch

    Raises:
        403: User is not an admin
        400: Invalid data or duplicate branch name
    """
    # Verify user is admin
    if "admin" not in current_user.roles and "universal_admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can create branches"
        )

    # Verify user has access to organization
    verify_organization_access(current_user, str(branch_data.organization_id))

    # Check for duplicate name
    existing_branch = await db.branches.find_one({
        "organization_id": branch_data.organization_id,
        "name": branch_data.name
    })

    if existing_branch:
        raise HTTPException(
            status_code=400,
            detail=f"Branch with name '{branch_data.name}' already exists in this organization"
        )

    # Create branch document
    branch_doc = {
        **branch_data.model_dump(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    # Insert into database
    result = await db.branches.insert_one(branch_doc)
    branch_doc["_id"] = result.inserted_id

    return branch_to_response(branch_doc)


# ============================================================================
# UPDATE OPERATION
# ============================================================================

@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    branch_update: BranchUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Update an existing branch.

    Requires admin role. Only provided fields will be updated.

    Path Parameters:
        branch_id: Branch ID to update

    Request Body:
        BranchUpdate model with fields to update

    Returns:
        Updated branch

    Raises:
        403: User is not an admin
        404: Branch not found
        400: Invalid data or duplicate name
    """
    # Verify user is admin
    if "admin" not in current_user.roles and "universal_admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update branches"
        )

    # Find existing branch
    branch = await db.branches.find_one({"_id": ObjectId(branch_id)})

    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    # Verify user has access to organization
    verify_organization_access(current_user, str(branch["organization_id"]))

    # Build update document (only include provided fields)
    update_data = branch_update.model_dump(exclude_unset=True)

    if not update_data:
        # No fields to update
        return branch_to_response(branch)

    # Check for duplicate name if name is being changed
    if "name" in update_data and update_data["name"] != branch["name"]:
        existing_branch = await db.branches.find_one({
            "organization_id": branch["organization_id"],
            "name": update_data["name"],
            "_id": {"$ne": ObjectId(branch_id)}
        })

        if existing_branch:
            raise HTTPException(
                status_code=400,
                detail=f"Branch with name '{update_data['name']}' already exists"
            )

    # Add updated_at timestamp
    update_data["updated_at"] = datetime.utcnow()

    # Update branch
    await db.branches.update_one(
        {"_id": ObjectId(branch_id)},
        {"$set": update_data}
    )

    # Fetch and return updated branch
    updated_branch = await db.branches.find_one({"_id": ObjectId(branch_id)})
    return branch_to_response(updated_branch)


# ============================================================================
# DELETE OPERATION
# ============================================================================

@router.delete("/{branch_id}", status_code=204)
async def delete_branch(
    branch_id: str,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) instead of hard delete"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Delete a branch.

    Requires admin role. By default performs soft delete (sets is_active=False).

    Path Parameters:
        branch_id: Branch ID to delete

    Query Parameters:
        soft_delete: If True (default), deactivates branch. If False, permanently deletes.

    Returns:
        204 No Content on success

    Raises:
        403: User is not an admin
        404: Branch not found
        400: Branch has active references (if hard delete)
    """
    # Verify user is admin
    if "admin" not in current_user.roles and "universal_admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete branches"
        )

    # Find branch
    branch = await db.branches.find_one({"_id": ObjectId(branch_id)})

    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    # Verify user has access to organization
    verify_organization_access(current_user, str(branch["organization_id"]))

    if soft_delete:
        # Soft delete: deactivate branch
        await db.branches.update_one(
            {"_id": ObjectId(branch_id)},
            {
                "$set": {
                    "is_active": False,
                    "auto_checkin_enabled": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Hard delete: check for references
        # Check if branch is referenced in registrations
        registration_count = await db.registrations.count_documents({
            "branch_id": ObjectId(branch_id)
        })

        if registration_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete branch: {registration_count} registrations reference this branch. Use soft delete instead."
            )

        # Check if branch is referenced in auto_checkin_logs
        log_count = await db.auto_checkin_logs.count_documents({
            "branch_id": ObjectId(branch_id)
        })

        if log_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete branch: {log_count} check-in logs reference this branch. Use soft delete instead."
            )

        # Safe to delete
        await db.branches.delete_one({"_id": ObjectId(branch_id)})

    return None  # 204 No Content


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/stats/summary")
async def get_branch_statistics(
    organization_id: str = Query(..., description="Organization ID"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user_profile)
):
    """
    Get summary statistics about branches.

    Returns counts and percentages for various branch statuses.

    Returns:
        {
            "total_branches": int,
            "active_branches": int,
            "inactive_branches": int,
            "with_coordinates": int,
            "without_coordinates": int,
            "auto_checkin_enabled": int,
            "by_region": {...}
        }
    """
    # Verify user has access
    verify_organization_access(current_user, organization_id)

    # Aggregate statistics
    pipeline = [
        {"$match": {"organization_id": ObjectId(organization_id)}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "active": {
                    "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                },
                "with_coordinates": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$ne": ["$latitude", None]},
                                {"$ne": ["$longitude", None]}
                            ]},
                            1, 0
                        ]
                    }
                },
                "auto_checkin_enabled": {
                    "$sum": {"$cond": [{"$eq": ["$auto_checkin_enabled", True]}, 1, 0]}
                }
            }
        }
    ]

    result = await db.branches.aggregate(pipeline).to_list(length=1)

    if not result:
        return {
            "total_branches": 0,
            "active_branches": 0,
            "inactive_branches": 0,
            "with_coordinates": 0,
            "without_coordinates": 0,
            "auto_checkin_enabled": 0,
            "by_region": {}
        }

    stats = result[0]

    # Get region breakdown
    region_pipeline = [
        {"$match": {"organization_id": ObjectId(organization_id)}},
        {"$group": {"_id": "$region", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    regions = await db.branches.aggregate(region_pipeline).to_list(length=None)
    by_region = {r["_id"]: r["count"] for r in regions}

    return {
        "total_branches": stats["total"],
        "active_branches": stats["active"],
        "inactive_branches": stats["total"] - stats["active"],
        "with_coordinates": stats["with_coordinates"],
        "without_coordinates": stats["total"] - stats["with_coordinates"],
        "auto_checkin_enabled": stats["auto_checkin_enabled"],
        "by_region": by_region
    }

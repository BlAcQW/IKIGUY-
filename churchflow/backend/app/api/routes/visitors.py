"""
Visitor Management API Routes.

Handles visitor capture, assignment, and follow-up communication.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_current_user_profile, require_roles, require_organization_access
from app.models.user import User
from app.services.visitor_service import visitor_service
from app.services.discipleship_service import discipleship_service

router = APIRouter()


# Request/Response Models

class CaptureVisitorRequest(BaseModel):
    """Request model for capturing visitor."""

    phone: str = Field(..., description="Phone number (required)")
    name: Optional[str] = Field(None, description="Visitor's name")
    full_name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    branch_id: Optional[str] = Field(None, description="Branch ID")
    first_visit_source: Optional[str] = Field(None, description="How they heard about the church")
    send_immediate_welcome: bool = Field(True, description="Send welcome message immediately")

    # Optional profile fields
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    preferred_communication_channel: Optional[str] = Field(default="sms", pattern="^(sms|whatsapp|voice|email)$")

    class Config:
        json_schema_extra = {
            "example": {
                "phone": "+233501234567",
                "name": "Kwame Mensah",
                "full_name": "Kwame Osei Mensah",
                "email": "kwame@example.com",
                "first_visit_source": "Friend invitation",
                "send_immediate_welcome": True,
                "preferred_communication_channel": "whatsapp"
            }
        }


class UpdateVisitorRequest(BaseModel):
    """Request model for updating visitor."""

    name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    branch_id: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    preferred_communication_channel: Optional[str] = Field(None, pattern="^(sms|whatsapp|voice|email)$")


class VisitorResponse(BaseModel):
    """Response model for visitor."""

    id: str
    phone: str
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    member_status: Optional[str] = None
    current_spiritual_stage: Optional[str] = None
    first_visit_date: Optional[datetime] = None
    visit_count: int = 0
    last_visit_date: Optional[datetime] = None
    cell_group_id: Optional[str] = None
    assigned_cell_leader_id: Optional[str] = None
    preferred_communication_channel: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VisitorListResponse(BaseModel):
    """Response model for visitor list."""

    visitors: List[VisitorResponse]
    total: int
    limit: int
    skip: int


# Endpoints

@router.post("/", response_model=VisitorResponse, status_code=status.HTTP_201_CREATED)
async def capture_visitor(
    request: CaptureVisitorRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader")),
    organization_id: str = Depends(require_organization_access)
):
    """
    Capture new visitor or update existing.

    Creates a new visitor record or updates an existing one if the phone number
    matches. Automatically triggers welcome communication if enabled.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Created or updated visitor profile
    """
    try:
        # Prepare visitor data
        visitor_data = request.dict(exclude_none=True)

        # Capture visitor
        user = await visitor_service.capture_visitor(
            visitor_data=visitor_data,
            organization_id=organization_id,
            captured_by_user_id=str(current_user.id),
            send_immediate_welcome=request.send_immediate_welcome
        )

        # Convert to response model
        return VisitorResponse(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            full_name=user.full_name,
            email=user.email,
            member_status=user.member_status,
            current_spiritual_stage=user.current_spiritual_stage,
            first_visit_date=user.first_visit_date,
            visit_count=user.visit_count,
            last_visit_date=user.last_visit_date,
            cell_group_id=str(user.cell_group_id) if user.cell_group_id else None,
            assigned_cell_leader_id=str(user.assigned_cell_leader_id) if user.assigned_cell_leader_id else None,
            preferred_communication_channel=user.preferred_communication_channel,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to capture visitor: {str(e)}"
        )


class VisitorStatsResponse(BaseModel):
    """Response model for visitor statistics."""

    total_users: int = Field(..., description="Total number of users")
    active_members: int = Field(..., description="Active members (with branch assignments)")
    visitors: int = Field(..., description="Visitors (from other churches)")
    inactive_members: int = Field(0, description="Inactive members")
    alumni: int = Field(0, description="Alumni")


@router.get("/stats", response_model=VisitorStatsResponse)
async def get_visitor_stats(
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get overall visitor and member statistics.

    - Members = users WITH branch_id (Action Chapel members)
    - Visitors = users WITHOUT branch_id (from other churches, e.g., IMPACT attendees)

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Overall statistics for all users in the system
    """
    try:
        from app.core.database import get_database

        db = get_database()

        # Count total users
        total_users = await db.users.count_documents({})

        # Members = users WITH valid branch_id (Action Chapel members)
        # branch_id is an ObjectId (all valid branch assignments are ObjectIds)
        active_members = await db.users.count_documents({
            "branch_id": {"$type": "objectId"}
        })

        # Visitors = users WITHOUT branch_id (from other churches)
        # These are people who registered at IMPACT conference from other churches
        # branch_id is null, empty string, or doesn't exist
        visitors = await db.users.count_documents({
            "$or": [
                {"branch_id": {"$exists": False}},
                {"branch_id": None}
            ]
        })

        # Count inactive members (member_status = 'inactive_member')
        inactive_members = await db.users.count_documents({"member_status": "inactive_member"})

        # Count alumni
        alumni = await db.users.count_documents({"member_status": "alumni"})

        return VisitorStatsResponse(
            total_users=total_users,
            active_members=active_members,
            visitors=visitors,
            inactive_members=inactive_members,
            alumni=alumni
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get visitor stats: {str(e)}"
        )


@router.get("/", response_model=VisitorListResponse)
async def list_visitors(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of results"),
    skip: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader")),
    organization_id: str = Depends(require_organization_access)
):
    """
    List recent visitors.

    Returns visitors captured in the last N days, sorted by first visit date (newest first).

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Query Parameters**:
    - days: Number of days to look back (default: 7, max: 365)
    - limit: Maximum results to return (default: 50, max: 200)
    - skip: Number of results to skip for pagination (default: 0)

    **Returns**: List of recent visitors with pagination metadata
    """
    try:

        # Fetch visitors
        visitors = await visitor_service.get_recent_visitors(
            organization_id=organization_id,
            days=days,
            limit=limit,
            skip=skip
        )

        # Convert to response models
        visitor_responses = [
            VisitorResponse(
                id=str(visitor.id),
                phone=visitor.phone,
                name=visitor.name,
                full_name=visitor.full_name,
                email=visitor.email,
                member_status=visitor.member_status,
                current_spiritual_stage=visitor.current_spiritual_stage,
                first_visit_date=visitor.first_visit_date,
                visit_count=visitor.visit_count,
                last_visit_date=visitor.last_visit_date,
                cell_group_id=str(visitor.cell_group_id) if visitor.cell_group_id else None,
                assigned_cell_leader_id=str(visitor.assigned_cell_leader_id) if visitor.assigned_cell_leader_id else None,
                preferred_communication_channel=visitor.preferred_communication_channel,
                created_at=visitor.created_at,
                updated_at=visitor.updated_at
            )
            for visitor in visitors
        ]

        return VisitorListResponse(
            visitors=visitor_responses,
            total=len(visitor_responses),
            limit=limit,
            skip=skip
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list visitors: {str(e)}"
        )


@router.get("/{user_id}")
async def get_visitor_details(
    user_id: str,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get visitor details with journey history.

    Returns complete visitor profile including:
    - Basic information
    - Current journey stages
    - Stage transition history
    - Cell group assignment
    - Communication preferences

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Complete visitor profile with journey history
    """
    try:
        from app.services.user_service import user_service

        # Fetch user
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Visitor {user_id} not found"
            )

        # Get stage history
        stage_history = await discipleship_service.get_stage_transition_history(user_id)

        # Build response
        return {
            "id": str(user.id),
            "phone": user.phone,
            "name": user.name,
            "full_name": user.full_name,
            "email": user.email,
            "member_status": user.member_status,
            "current_spiritual_stage": user.current_spiritual_stage,
            "current_cell_stage": user.current_cell_stage,
            "current_ministry_stage": user.current_ministry_stage,
            "first_visit_date": user.first_visit_date.isoformat() if user.first_visit_date else None,
            "visit_count": user.visit_count,
            "last_visit_date": user.last_visit_date.isoformat() if user.last_visit_date else None,
            "consecutive_absences": user.consecutive_absences,
            "first_visit_source": user.first_visit_source,
            "cell_group_id": str(user.cell_group_id) if user.cell_group_id else None,
            "assigned_cell_leader_id": str(user.assigned_cell_leader_id) if user.assigned_cell_leader_id else None,
            "zone_id": str(user.zone_id) if user.zone_id else None,
            "preferred_communication_channel": user.preferred_communication_channel,
            "allow_automated_communications": user.allow_automated_communications,
            "stage_history": stage_history,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get visitor details: {str(e)}"
        )


@router.put("/{user_id}", response_model=VisitorResponse)
async def update_visitor(
    user_id: str,
    request: UpdateVisitorRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Update visitor information.

    Updates basic visitor information. For data enrichment with audit trail,
    use the /api/members/{user_id}/enrich endpoint instead.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Updated visitor profile
    """
    try:
        from app.services.user_service import user_service
        from app.core.database import get_database
        from bson import ObjectId

        # Fetch user
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Visitor {user_id} not found"
            )

        # Build update document
        update_data = request.dict(exclude_none=True)
        update_data["updated_at"] = datetime.utcnow()

        # Convert branch_id to ObjectId if provided
        if "branch_id" in update_data and update_data["branch_id"]:
            update_data["branch_id"] = ObjectId(update_data["branch_id"])

        # Update user
        db = get_database()
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        # Fetch updated user
        updated_user = await user_service.get_user_by_id(user_id)

        return VisitorResponse(
            id=str(updated_user.id),
            phone=updated_user.phone,
            name=updated_user.name,
            full_name=updated_user.full_name,
            email=updated_user.email,
            member_status=updated_user.member_status,
            current_spiritual_stage=updated_user.current_spiritual_stage,
            first_visit_date=updated_user.first_visit_date,
            visit_count=updated_user.visit_count,
            last_visit_date=updated_user.last_visit_date,
            cell_group_id=str(updated_user.cell_group_id) if updated_user.cell_group_id else None,
            assigned_cell_leader_id=str(updated_user.assigned_cell_leader_id) if updated_user.assigned_cell_leader_id else None,
            preferred_communication_channel=updated_user.preferred_communication_channel,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update visitor: {str(e)}"
        )


@router.post("/{user_id}/resend-welcome")
async def resend_welcome_communication(
    user_id: str,
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Manually resend welcome communication to visitor.

    Triggers immediate welcome message via configured channels.
    Bypasses deduplication check.

    **Required Role**: admin or coordinator

    **Returns**: Status of welcome communication
    """
    try:
        from app.services.user_service import user_service

        # Fetch user
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Visitor {user_id} not found"
            )

        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Send welcome communication
        result = await visitor_service.send_welcome_communication(
            user_id=user_id,
            organization_id=organization_id,
            stage_name=user.current_spiritual_stage or "first_timer"
        )

        return {
            "status": "success",
            "message": "Welcome communication sent",
            "details": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend welcome communication: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_visitor(
    user_id: str,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Delete a visitor/user from the system.

    This permanently removes the user and all associated data.

    **Required Role**: admin only

    **Returns**: Deletion confirmation
    """
    try:
        from app.core.database import get_database
        from bson import ObjectId

        db = get_database()

        # Check if user exists
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Delete the user
        result = await db.users.delete_one({"_id": ObjectId(user_id)})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )

        return {
            "status": "success",
            "message": f"User {user_id} deleted successfully",
            "deleted_count": result.deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete."""

    user_ids: List[str] = Field(..., description="List of user IDs to delete", min_length=1)


@router.post("/bulk-delete")
async def bulk_delete_visitors(
    request: BulkDeleteRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Delete multiple visitors/users from the system.

    This permanently removes the users and all associated data.

    **Required Role**: admin only

    **Returns**: Deletion summary with count of deleted users
    """
    try:
        from app.core.database import get_database
        from bson import ObjectId

        db = get_database()

        # Convert string IDs to ObjectIds
        object_ids = []
        for user_id in request.user_ids:
            try:
                object_ids.append(ObjectId(user_id))
            except Exception:
                pass  # Skip invalid IDs

        if not object_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid user IDs provided"
            )

        # Delete the users
        result = await db.users.delete_many({"_id": {"$in": object_ids}})

        return {
            "status": "success",
            "message": f"Deleted {result.deleted_count} users",
            "deleted_count": result.deleted_count,
            "requested_count": len(request.user_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete users: {str(e)}"
        )

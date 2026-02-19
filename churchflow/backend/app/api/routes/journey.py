"""
Journey Management API Routes.

Handles discipleship journey stages, member advancement, and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.models.journey_stage import JourneyStage, ScheduledFollowup
from app.services.discipleship_service import discipleship_service
from app.core.database import get_database
from bson import ObjectId

router = APIRouter()


# Request/Response Models

class ScheduledFollowupRequest(BaseModel):
    """Request model for scheduled follow-up."""

    delay_days: int = Field(..., ge=0, description="Days after stage entry (0 = immediate)")
    message_template: str = Field(..., min_length=1, description="Message template with {{variables}}")
    communication_channels: List[str] = Field(default=["sms"], description="Channels: sms, whatsapp, voice, email")
    requires_action: bool = Field(default=False, description="Whether leader action is required")
    action_description: Optional[str] = Field(None, description="Description of required action")


class CreateJourneyStageRequest(BaseModel):
    """Request model for creating journey stage."""

    stage_name: str = Field(..., min_length=1, max_length=100, description="Internal identifier")
    stage_display_name: str = Field(..., min_length=1, max_length=200, description="User-friendly name")
    journey_type: str = Field(..., pattern="^(spiritual|cell|ministry)$", description="Journey type")
    stage_order: int = Field(..., ge=1, description="Sequential order (1 = first stage)")
    is_custom: bool = Field(default=True, description="Custom stage vs. predefined")
    description: Optional[str] = Field(None, max_length=1000)

    # Welcome automation
    auto_send_welcome: bool = Field(default=True)
    welcome_delay_minutes: int = Field(default=5, ge=0, le=1440)
    welcome_message_template: Optional[str] = None
    welcome_channels: List[str] = Field(default=["sms"])

    # Scheduled follow-ups
    scheduled_followups: List[ScheduledFollowupRequest] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "stage_name": "small_group_member",
                "stage_display_name": "Small Group Member",
                "journey_type": "cell",
                "stage_order": 2,
                "is_custom": True,
                "auto_send_welcome": True,
                "welcome_delay_minutes": 5,
                "welcome_message_template": "Welcome {{name}}! You're now part of {{cell_group_name}}!",
                "welcome_channels": ["whatsapp", "sms"],
                "scheduled_followups": [
                    {
                        "delay_days": 3,
                        "message_template": "Hi {{name}}! How has your first week been in the small group?",
                        "communication_channels": ["whatsapp"]
                    }
                ]
            }
        }


class AdvanceMemberRequest(BaseModel):
    """Request model for advancing member to new stage."""

    user_id: str = Field(..., description="User ID to advance")
    journey_type: str = Field(..., pattern="^(spiritual|cell|ministry)$", description="Journey type")
    new_stage: str = Field(..., description="New stage name")
    notes: Optional[str] = Field(None, description="Optional notes about the transition")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "journey_type": "spiritual",
                "new_stage": "new_convert",
                "notes": "Completed first-timers class"
            }
        }


# Endpoints

@router.post("/stages", status_code=status.HTTP_201_CREATED)
async def create_journey_stage(
    request: CreateJourneyStageRequest,
    current_user: User = Depends(require_roles("admin"))
):
    """
    Create or update custom journey stage.

    Creates a new journey stage with automation configuration including
    welcome messages and scheduled follow-ups.

    **Required Role**: admin

    **Returns**: Created journey stage
    """
    try:
        db = get_database()

        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Check if stage name already exists
        existing = await db.journey_stages.find_one({
            "organization_id": ObjectId(organization_id),
            "stage_name": request.stage_name
        })

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stage '{request.stage_name}' already exists"
            )

        # Create journey stage
        stage_doc = {
            "organization_id": ObjectId(organization_id),
            "stage_name": request.stage_name,
            "stage_display_name": request.stage_display_name,
            "journey_type": request.journey_type,
            "stage_order": request.stage_order,
            "is_custom": request.is_custom,
            "is_active": True,
            "auto_send_welcome": request.auto_send_welcome,
            "welcome_delay_minutes": request.welcome_delay_minutes,
            "welcome_message_template": request.welcome_message_template,
            "welcome_channels": request.welcome_channels,
            "scheduled_followups": [f.dict() for f in request.scheduled_followups],
            "description": request.description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by_user_id": current_user.id
        }

        result = await db.journey_stages.insert_one(stage_doc)
        stage_doc["_id"] = result.inserted_id

        return {
            "id": str(stage_doc["_id"]),
            "stage_name": stage_doc["stage_name"],
            "stage_display_name": stage_doc["stage_display_name"],
            "journey_type": stage_doc["journey_type"],
            "stage_order": stage_doc["stage_order"],
            "is_custom": stage_doc["is_custom"],
            "message": "Journey stage created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create journey stage: {str(e)}"
        )


@router.get("/stages")
async def list_journey_stages(
    journey_type: Optional[str] = Query(None, pattern="^(spiritual|cell|ministry)$", description="Filter by journey type"),
    is_active: bool = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user_profile)
):
    """
    List all journey stages for organization.

    Returns stages sorted by stage_order, optionally filtered by journey type.

    **Query Parameters**:
    - journey_type: Filter by type (spiritual, cell, ministry) - optional
    - is_active: Filter by active status (default: True)

    **Returns**: List of journey stages
    """
    try:
        db = get_database()

        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Build query
        query = {
            "organization_id": ObjectId(organization_id),
            "is_active": is_active
        }

        if journey_type:
            query["journey_type"] = journey_type

        # Fetch stages
        cursor = db.journey_stages.find(query).sort("stage_order", 1)

        stages = []
        async for stage_doc in cursor:
            stages.append({
                "id": str(stage_doc["_id"]),
                "stage_name": stage_doc["stage_name"],
                "stage_display_name": stage_doc["stage_display_name"],
                "journey_type": stage_doc["journey_type"],
                "stage_order": stage_doc["stage_order"],
                "is_custom": stage_doc.get("is_custom", False),
                "is_active": stage_doc["is_active"],
                "auto_send_welcome": stage_doc.get("auto_send_welcome", True),
                "welcome_delay_minutes": stage_doc.get("welcome_delay_minutes", 5),
                "scheduled_followups_count": len(stage_doc.get("scheduled_followups", [])),
                "description": stage_doc.get("description")
            })

        return {
            "stages": stages,
            "total": len(stages),
            "journey_type": journey_type or "all"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list journey stages: {str(e)}"
        )


@router.post("/advance")
async def advance_member_stage(
    request: AdvanceMemberRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Advance member to new journey stage.

    Updates member's current stage, records transition in history,
    and triggers automated follow-up communications.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Updated user with new stage
    """
    try:
        # Advance member
        updated_user = await discipleship_service.advance_member_stage(
            user_id=request.user_id,
            journey_type=request.journey_type,
            new_stage=request.new_stage,
            transitioned_by_user_id=str(current_user.id),
            notes=request.notes
        )

        return {
            "id": str(updated_user.id),
            "phone": updated_user.phone,
            "name": updated_user.full_name or updated_user.name,
            "journey_type": request.journey_type,
            "new_stage": request.new_stage,
            "current_spiritual_stage": updated_user.current_spiritual_stage,
            "current_cell_stage": updated_user.current_cell_stage,
            "current_ministry_stage": updated_user.current_ministry_stage,
            "message": f"Successfully advanced to {request.new_stage}"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to advance member: {str(e)}"
        )


@router.get("/history/{user_id}")
async def get_journey_history(
    user_id: str,
    journey_type: Optional[str] = Query(None, pattern="^(spiritual|cell|ministry)$", description="Filter by journey type"),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get complete journey history for a member.

    Returns all stage transitions for a member, optionally filtered by journey type.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Query Parameters**:
    - journey_type: Filter by type (spiritual, cell, ministry) - optional

    **Returns**: List of stage transitions, newest first
    """
    try:
        # Get stage transition history
        history = await discipleship_service.get_stage_transition_history(
            user_id=user_id,
            journey_type=journey_type
        )

        return {
            "user_id": user_id,
            "journey_type": journey_type or "all",
            "transitions": history,
            "total": len(history)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get journey history: {str(e)}"
        )


@router.get("/analytics/funnel")
async def get_journey_funnel_analytics(
    journey_type: str = Query(..., pattern="^(spiritual|cell|ministry)$", description="Journey type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering (ISO format)"),
    current_user: User = Depends(require_roles("admin", "coordinator", "zone_leader"))
):
    """
    Get journey funnel analytics with conversion rates.

    Provides insights into member progression through journey stages including:
    - Member count at each stage
    - Conversion rates between stages
    - Total members in journey

    **Required Role**: admin, coordinator, or zone_leader

    **Query Parameters**:
    - journey_type: Type of journey (spiritual, cell, ministry) - required
    - start_date: Start date for filtering (optional)
    - end_date: End date for filtering (optional)

    **Returns**: Journey analytics with funnel metrics
    """
    try:
        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Get journey analytics
        analytics = await discipleship_service.get_journey_analytics(
            organization_id=organization_id,
            journey_type=journey_type,
            start_date=start_date,
            end_date=end_date
        )

        return analytics

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get journey analytics: {str(e)}"
        )


@router.get("/members")
async def get_members_by_stage(
    journey_type: str = Query(..., pattern="^(spiritual|cell|ministry)$", description="Journey type"),
    stage: str = Query(..., description="Stage name"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum results"),
    skip: int = Query(default=0, ge=0, description="Results to skip"),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get all members at a specific journey stage.

    Useful for creating targeted campaigns or generating stage-specific reports.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Query Parameters**:
    - journey_type: Type of journey (spiritual, cell, ministry) - required
    - stage: Stage name - required
    - limit: Maximum results (default: 100, max: 500)
    - skip: Results to skip for pagination (default: 0)

    **Returns**: List of members at this stage
    """
    try:
        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Get members at stage
        members = await discipleship_service.get_members_by_stage(
            organization_id=organization_id,
            journey_type=journey_type,
            stage=stage,
            limit=limit,
            skip=skip
        )

        # Convert to response format
        member_list = [
            {
                "id": str(member.id),
                "phone": member.phone,
                "name": member.full_name or member.name,
                "email": member.email,
                "current_spiritual_stage": member.current_spiritual_stage,
                "current_cell_stage": member.current_cell_stage,
                "current_ministry_stage": member.current_ministry_stage,
                "first_visit_date": member.first_visit_date.isoformat() if member.first_visit_date else None,
                "visit_count": member.visit_count,
                "cell_group_id": str(member.cell_group_id) if member.cell_group_id else None
            }
            for member in members
        ]

        return {
            "journey_type": journey_type,
            "stage": stage,
            "members": member_list,
            "total": len(member_list),
            "limit": limit,
            "skip": skip
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get members by stage: {str(e)}"
        )

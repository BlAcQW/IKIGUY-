"""
Journey Communications API Routes.

Handles manual and automated communications for discipleship journeys
including SMS, WhatsApp, and voice calls.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.services.communication_orchestration_service import communication_orchestration_service
from app.services.discipleship_service import discipleship_service
from app.core.database import get_database

router = APIRouter()


# Request/Response Models

class SendCommunicationRequest(BaseModel):
    """Request model for sending communication."""

    user_ids: List[str] = Field(..., min_items=1, description="List of user IDs to send to")
    message_template: str = Field(..., min_length=1, description="Message template with {{variables}}")
    channels: List[str] = Field(..., min_items=1, description="Channels: sms, whatsapp, voice")
    template_variables: Dict[str, str] = Field(default_factory=dict, description="Template variables")

    class Config:
        json_schema_extra = {
            "example": {
                "user_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"],
                "message_template": "Hi {{name}}! We have an exciting event this Sunday at {{church_name}}.",
                "channels": ["whatsapp", "sms"],
                "template_variables": {
                    "church_name": "Victory Church"
                }
            }
        }


class CreateCampaignRequest(BaseModel):
    """Request model for creating stage-based campaign."""

    journey_type: str = Field(..., pattern="^(spiritual|cell|ministry)$", description="Journey type")
    stage_name: str = Field(..., description="Stage name to target")
    message_template: str = Field(..., min_length=1, description="Message template")
    channels: List[str] = Field(..., min_items=1, description="Channels: sms, whatsapp, voice")
    template_variables: Dict[str, str] = Field(default_factory=dict, description="Template variables")

    class Config:
        json_schema_extra = {
            "example": {
                "journey_type": "spiritual",
                "stage_name": "first_timer",
                "message_template": "Hi {{name}}! Thank you for joining us at {{church_name}}. We'd love to see you again!",
                "channels": ["whatsapp"],
                "template_variables": {
                    "church_name": "Victory Church"
                }
            }
        }


# Endpoints

@router.post("/send")
async def send_communication(
    request: SendCommunicationRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Manually send communication to selected members.

    Sends immediate communication via specified channels to one or more members.
    Bypasses deduplication check for manual sends.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Summary with success/failure counts
    """
    try:
        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Send bulk communication
        summary = await communication_orchestration_service.send_bulk_communication(
            user_ids=request.user_ids,
            message_template=request.message_template,
            template_variables=request.template_variables,
            channels=request.channels,
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        return {
            **summary,
            "sent_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name
            },
            "channels": request.channels
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send communication: {str(e)}"
        )


@router.get("/scheduled")
async def get_scheduled_communications(
    status_filter: Optional[str] = Query(None, pattern="^(pending|sent|failed|cancelled)$", description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    View scheduled communications.

    Returns list of scheduled communications, optionally filtered by status or user.

    **Required Role**: admin or coordinator

    **Query Parameters**:
    - status_filter: Filter by status (pending, sent, failed, cancelled) - optional
    - user_id: Filter by recipient user ID - optional
    - limit: Maximum results (default: 50, max: 200)
    - skip: Results to skip (default: 0)

    **Returns**: List of scheduled communications
    """
    try:
        db = get_database()

        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Build query
        query = {"organization_id": ObjectId(organization_id)}

        if status_filter:
            query["status"] = status_filter

        if user_id:
            query["user_id"] = ObjectId(user_id)

        # Fetch scheduled communications
        cursor = db.scheduled_communications.find(query).sort("scheduled_for", -1).skip(skip).limit(limit)

        scheduled_comms = []
        async for comm_doc in cursor:
            scheduled_comms.append({
                "id": str(comm_doc["_id"]),
                "user_id": str(comm_doc["user_id"]),
                "followup_type": comm_doc["followup_type"],
                "scheduled_for": comm_doc["scheduled_for"].isoformat(),
                "channels": comm_doc["channels"],
                "message_template": comm_doc["message_template"],
                "status": comm_doc["status"],
                "sent_at": comm_doc["sent_at"].isoformat() if comm_doc.get("sent_at") else None,
                "retry_count": comm_doc.get("retry_count", 0),
                "error_message": comm_doc.get("error_message")
            })

        return {
            "scheduled_communications": scheduled_comms,
            "total": len(scheduled_comms),
            "limit": limit,
            "skip": skip,
            "status_filter": status_filter or "all"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduled communications: {str(e)}"
        )


@router.delete("/scheduled/{scheduled_comm_id}")
async def cancel_scheduled_communication(
    scheduled_comm_id: str,
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Cancel scheduled communication.

    Marks a pending scheduled communication as cancelled, preventing it from being sent.

    **Required Role**: admin or coordinator

    **Returns**: Cancellation confirmation
    """
    try:
        db = get_database()

        # Fetch scheduled communication
        comm = await db.scheduled_communications.find_one({"_id": ObjectId(scheduled_comm_id)})

        if not comm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled communication {scheduled_comm_id} not found"
            )

        # Check if already sent
        if comm["status"] == "sent":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel communication that has already been sent"
            )

        # Cancel the communication
        await db.scheduled_communications.update_one(
            {"_id": ObjectId(scheduled_comm_id)},
            {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
        )

        # Cancel the scheduled job (if it exists)
        try:
            from app.scheduler.scheduler_service import scheduler_service
            await scheduler_service.cancel_scheduled_communication(scheduled_comm_id)
        except Exception as e:
            # Job might not exist yet, that's okay
            pass

        return {
            "id": scheduled_comm_id,
            "status": "cancelled",
            "cancelled_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name
            },
            "message": "Scheduled communication cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel scheduled communication: {str(e)}"
        )


@router.post("/campaign")
async def create_stage_campaign(
    request: CreateCampaignRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "zone_leader"))
):
    """
    Create campaign for all members at specific journey stage.

    Sends communication to all members currently at a specific journey stage.
    Useful for stage-specific announcements, invitations, or follow-ups.

    **Required Role**: admin, coordinator, or zone_leader

    **Returns**: Summary with success/failure counts
    """
    try:
        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Get all members at this stage
        members = await discipleship_service.get_members_by_stage(
            organization_id=organization_id,
            journey_type=request.journey_type,
            stage=request.stage_name,
            limit=500  # Process up to 500 members
        )

        if not members:
            return {
                "total": 0,
                "success": 0,
                "failure": 0,
                "message": f"No members found at {request.journey_type} stage: {request.stage_name}"
            }

        # Get user IDs
        user_ids = [str(member.id) for member in members]

        # Send bulk communication
        summary = await communication_orchestration_service.send_bulk_communication(
            user_ids=user_ids,
            message_template=request.message_template,
            template_variables=request.template_variables,
            channels=request.channels,
            organization_id=organization_id,
            created_by_user_id=str(current_user.id)
        )

        return {
            **summary,
            "journey_type": request.journey_type,
            "stage_name": request.stage_name,
            "channels": request.channels,
            "created_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create stage campaign: {str(e)}"
        )


@router.get("/stats")
async def get_communication_stats(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Get communication statistics.

    Provides insights into communication effectiveness including:
    - Total communications sent
    - Breakdown by channel (SMS, WhatsApp, Voice)
    - Success/failure rates
    - Recent trends

    **Required Role**: admin or coordinator

    **Query Parameters**:
    - days: Number of days to analyze (default: 30, max: 365)

    **Returns**: Communication statistics
    """
    try:
        db = get_database()

        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Calculate date range
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        # Aggregate statistics
        pipeline = [
            {
                "$match": {
                    "organization_id": ObjectId(organization_id),
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        status_counts = {}
        async for result in db.scheduled_communications.aggregate(pipeline):
            status_counts[result["_id"]] = result["count"]

        # Count by channel
        channel_pipeline = [
            {
                "$match": {
                    "organization_id": ObjectId(organization_id),
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$unwind": "$channels"
            },
            {
                "$group": {
                    "_id": "$channels",
                    "count": {"$sum": 1}
                }
            }
        ]

        channel_counts = {}
        async for result in db.scheduled_communications.aggregate(channel_pipeline):
            channel_counts[result["_id"]] = result["count"]

        # Calculate totals
        total_sent = status_counts.get("sent", 0)
        total_failed = status_counts.get("failed", 0)
        total_pending = status_counts.get("pending", 0)
        total_cancelled = status_counts.get("cancelled", 0)
        total = total_sent + total_failed + total_pending + total_cancelled

        # Calculate success rate
        success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0

        return {
            "period_days": days,
            "date_range": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "total_communications": total,
            "by_status": {
                "sent": total_sent,
                "failed": total_failed,
                "pending": total_pending,
                "cancelled": total_cancelled
            },
            "by_channel": channel_counts,
            "success_rate": round(success_rate, 2),
            "insights": {
                "most_used_channel": max(channel_counts.items(), key=lambda x: x[1])[0] if channel_counts else None,
                "average_per_day": round(total / days, 2) if days > 0 else 0
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get communication stats: {str(e)}"
        )

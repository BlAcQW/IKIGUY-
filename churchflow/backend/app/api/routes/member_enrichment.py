"""
Member Data Enrichment API Routes.

Handles data enrichment with audit trail and life event tracking
for pastoral care and member relationships.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_current_user_profile, require_roles
from app.models.user import User
from app.services.enrichment_service import enrichment_service

router = APIRouter()


# Request/Response Models

class EnrichMemberDataRequest(BaseModel):
    """Request model for enriching member data."""

    field_updates: Dict[str, Any] = Field(..., description="Fields to update with new values")
    notes: Optional[str] = Field(None, description="Optional notes about the enrichment")

    class Config:
        json_schema_extra = {
            "example": {
                "field_updates": {
                    "occupation": "Teacher",
                    "marital_status": "Married",
                    "address": "123 Main St, Accra"
                },
                "notes": "Updated during home visit"
            }
        }


class RecordLifeEventRequest(BaseModel):
    """Request model for recording life event."""

    event_type: str = Field(
        ...,
        pattern="^(birth|death|marriage|job_change|relocation|illness|celebration|other)$",
        description="Type of life event"
    )
    event_date: datetime = Field(..., description="When the event occurred")
    description: str = Field(..., min_length=1, description="Event description")
    requires_followup: bool = Field(default=False, description="Whether follow-up is needed")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "birth",
                "event_date": "2025-11-15T00:00:00",
                "description": "Welcomed baby girl - Sarah",
                "requires_followup": True
            }
        }


class MarkFollowupCompletedRequest(BaseModel):
    """Request model for marking follow-up completed."""

    event_index: int = Field(..., ge=0, description="Index of life event in array")


# Endpoints

@router.put("/{user_id}/enrich")
async def enrich_member_data(
    user_id: str,
    request: EnrichMemberDataRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Enrich member data with full audit trail.

    Updates member profile fields while recording who made the changes,
    when, and what changed. Provides accountability and data quality tracking.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Allowed Fields**:
    - Extended profile: date_of_birth, gender, occupation, marital_status, address,
      emergency_contact_name, emergency_contact_phone
    - Basic info: email, full_name
    - Preferences: preferred_communication_channel
    - Location: branch_id

    **Returns**: Updated user with enrichment history
    """
    try:
        # Determine enricher role
        enriched_by_role = "admin"
        if "cell_leader" in (current_user.roles or []):
            enriched_by_role = "cell_leader"
        elif "zone_leader" in (current_user.roles or []):
            enriched_by_role = "zone_leader"
        elif "coordinator" in (current_user.roles or []):
            enriched_by_role = "coordinator"

        # Enrich member data
        updated_user = await enrichment_service.enrich_member_data(
            user_id=user_id,
            field_updates=request.field_updates,
            enriched_by_user_id=str(current_user.id),
            enriched_by_role=enriched_by_role,
            notes=request.notes
        )

        return {
            "id": str(updated_user.id),
            "name": updated_user.full_name or updated_user.name,
            "updated_fields": list(request.field_updates.keys()),
            "enriched_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name,
                "role": enriched_by_role
            },
            "enrichment_count": len(updated_user.enrichment_history or []),
            "message": "Member data enriched successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enrich member data: {str(e)}"
        )


@router.post("/{user_id}/life-events")
async def record_life_event(
    user_id: str,
    request: RecordLifeEventRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Record significant life event for member.

    Life events help leaders provide better pastoral care and maintain
    meaningful relationships with members.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Event Types**:
    - birth: Birth of child
    - death: Death of family member
    - marriage: Wedding
    - job_change: New job or job loss
    - relocation: Moving to new location
    - illness: Serious illness
    - celebration: Achievement or milestone
    - other: Other significant events

    **Returns**: Updated user with life event added
    """
    try:
        # Record life event
        updated_user = await enrichment_service.record_life_event(
            user_id=user_id,
            event_type=request.event_type,
            event_date=request.event_date,
            description=request.description,
            recorded_by_user_id=str(current_user.id),
            requires_followup=request.requires_followup
        )

        return {
            "id": str(updated_user.id),
            "name": updated_user.full_name or updated_user.name,
            "event_type": request.event_type,
            "event_date": request.event_date.isoformat(),
            "requires_followup": request.requires_followup,
            "recorded_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name
            },
            "life_events_count": len(updated_user.life_events or []),
            "message": "Life event recorded successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record life event: {str(e)}"
        )


@router.get("/life-events/pending-followups")
async def get_pending_followups(
    assigned_to_me: bool = Query(False, description="Filter by current user's assignments"),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get life events requiring follow-up.

    Returns list of pending follow-ups for pastoral care, optionally filtered
    to show only those assigned to the current user.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Query Parameters**:
    - assigned_to_me: Only show follow-ups for my assigned members (default: False)
    - limit: Maximum results (default: 50, max: 200)
    - skip: Results to skip (default: 0)

    **Returns**: List of pending follow-ups with member details
    """
    try:
        # Get organization ID
        organization_id = str(current_user.branch_id) if current_user.branch_id else "default"

        # Get pending follow-ups
        assigned_to_user_id = str(current_user.id) if assigned_to_me else None

        followups = await enrichment_service.get_pending_followups(
            organization_id=organization_id,
            assigned_to_user_id=assigned_to_user_id,
            limit=limit,
            skip=skip
        )

        return {
            "followups": followups,
            "total": len(followups),
            "limit": limit,
            "skip": skip,
            "assigned_to_me": assigned_to_me
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending follow-ups: {str(e)}"
        )


@router.post("/{user_id}/life-events/mark-completed")
async def mark_followup_completed(
    user_id: str,
    request: MarkFollowupCompletedRequest,
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Mark life event follow-up as completed.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Returns**: Updated user
    """
    try:
        # Mark follow-up completed
        updated_user = await enrichment_service.mark_followup_completed(
            user_id=user_id,
            event_index=request.event_index,
            completed_by_user_id=str(current_user.id)
        )

        return {
            "id": str(updated_user.id),
            "name": updated_user.full_name or updated_user.name,
            "event_index": request.event_index,
            "completed_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name
            },
            "message": "Follow-up marked as completed"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark follow-up completed: {str(e)}"
        )


@router.get("/{user_id}/enrichment-history")
async def get_enrichment_history(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get complete enrichment history for member.

    Shows audit trail of all data updates including who made each change,
    when, and what was changed.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Query Parameters**:
    - limit: Maximum results (default: 50, max: 200)
    - skip: Results to skip (default: 0)

    **Returns**: List of enrichment records, newest first
    """
    try:
        # Get enrichment history
        history = await enrichment_service.get_enrichment_history(
            user_id=user_id,
            limit=limit,
            skip=skip
        )

        return {
            "user_id": user_id,
            "enrichment_history": history,
            "total": len(history),
            "limit": limit,
            "skip": skip
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enrichment history: {str(e)}"
        )


@router.get("/{user_id}/life-events")
async def get_life_events(
    user_id: str,
    event_type: Optional[str] = Query(
        None,
        pattern="^(birth|death|marriage|job_change|relocation|illness|celebration|other)$",
        description="Filter by event type"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(require_roles("admin", "coordinator", "cell_leader", "zone_leader"))
):
    """
    Get life events for member.

    **Required Role**: admin, coordinator, cell_leader, or zone_leader

    **Query Parameters**:
    - event_type: Filter by event type (optional)
    - limit: Maximum results (default: 50, max: 200)
    - skip: Results to skip (default: 0)

    **Returns**: List of life events, newest first
    """
    try:
        # Get life events
        events = await enrichment_service.get_life_events(
            user_id=user_id,
            event_type=event_type,
            limit=limit,
            skip=skip
        )

        return {
            "user_id": user_id,
            "life_events": events,
            "total": len(events),
            "limit": limit,
            "skip": skip,
            "event_type": event_type or "all"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get life events: {str(e)}"
        )


@router.post("/bulk-enrich")
async def bulk_enrich_members(
    enrichments: List[Dict[str, Any]],
    current_user: User = Depends(require_roles("admin", "coordinator"))
):
    """
    Bulk enrich multiple members at once.

    Useful for importing data from external sources or mass updates.

    **Required Role**: admin or coordinator

    **Request Body**: List of enrichment records, each containing:
    - user_id: User ID to enrich
    - field_updates: Dictionary of fields to update
    - notes: Optional notes

    **Returns**: Summary with success/failure counts
    """
    try:
        # Determine enricher role
        enriched_by_role = "admin" if "admin" in (current_user.roles or []) else "coordinator"

        # Bulk enrich
        summary = await enrichment_service.bulk_enrich_members(
            enrichments=enrichments,
            enriched_by_user_id=str(current_user.id),
            enriched_by_role=enriched_by_role
        )

        return {
            **summary,
            "enriched_by": {
                "user_id": str(current_user.id),
                "name": current_user.full_name or current_user.name,
                "role": enriched_by_role
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk enrich members: {str(e)}"
        )

"""
Community governance routes for dispute resolution and content moderation.

Handles disputes, content reports, moderation actions, and community guidelines.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from datetime import datetime

from models.governance_models import (
    Dispute, DisputeCreate, DisputeUpdate, DisputeStats,
    ContentReport, ContentReportCreate,
    ModerationActionRecord, ModerationActionCreate, ModerationStats
)
from models.user_models import User
from models.responses import DataResponse, ListResponse
from routes.auth import get_current_user
from services.governance_service import GovernanceService

router = APIRouter()
governance_service = GovernanceService()


# Helper function to check moderator permissions
def require_moderator(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user has moderator permissions."""
    if current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator permissions required"
        )
    return current_user


# Dispute Management Routes
@router.post("/disputes", response_model=DataResponse)
async def create_dispute(
    dispute_data: DisputeCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new dispute.

    Args:
        dispute_data: Dispute creation data
        current_user: Authenticated user

    Returns:
        DataResponse: Created dispute
    """
    try:
        dispute = await governance_service.create_dispute(
            dispute_data=dispute_data,
            reporter_id=str(current_user.id)
        )

        return DataResponse(
            data=dispute.dict(),
            message="Dispute created successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/disputes", response_model=ListResponse)
async def get_disputes(
    status: Optional[str] = Query(None, description="Filter by status"),
    dispute_type: Optional[str] = Query(None, description="Filter by type"),
    language_code: Optional[str] = Query(None, description="Filter by language"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned moderator"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
):
    """
    Get disputes with filtering and pagination.

    Args:
        status: Filter by status
        dispute_type: Filter by type
        language_code: Filter by language
        assigned_to: Filter by assigned moderator
        page: Page number
        page_size: Items per page
        current_user: Authenticated user

    Returns:
        ListResponse: Disputes with pagination
    """
    try:
        # Regular users can only see their own disputes
        if current_user.role not in ["moderator", "admin"]:
            # Add filter for user's own disputes
            pass

        disputes, total_count = await governance_service.get_disputes(
            status=status,
            dispute_type=dispute_type,
            language_code=language_code,
            assigned_to=assigned_to,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            items=[dispute.dict() for dispute in disputes],
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/disputes/{dispute_id}", response_model=DataResponse)
async def update_dispute(
    dispute_id: str,
    update_data: DisputeUpdate,
    current_user: User = Depends(require_moderator)
):
    """
    Update a dispute (moderators only).

    Args:
        dispute_id: Dispute ID
        update_data: Update data
        current_user: Authenticated moderator

    Returns:
        DataResponse: Updated dispute
    """
    try:
        dispute = await governance_service.update_dispute(
            dispute_id=dispute_id,
            update_data=update_data,
            moderator_id=str(current_user.id)
        )

        return DataResponse(
            data=dispute.dict(),
            message="Dispute updated successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/disputes/{dispute_id}/vote", response_model=DataResponse)
async def vote_on_dispute(
    dispute_id: str,
    vote: int = Query(..., ge=-1, le=1, description="Vote: -1 (disagree), 0 (neutral), 1 (agree)"),
    current_user: User = Depends(get_current_user)
):
    """
    Vote on a dispute (community voting).

    Args:
        dispute_id: Dispute ID
        vote: Vote value (-1, 0, 1)
        current_user: Authenticated user

    Returns:
        DataResponse: Success message
    """
    try:
        await governance_service.vote_on_dispute(
            dispute_id=dispute_id,
            user_id=str(current_user.id),
            vote=vote
        )

        return DataResponse(
            data={"vote": vote},
            message="Vote recorded successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Content Moderation Routes
@router.get("/reports", response_model=ListResponse)
async def get_content_reports(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_moderator)
):
    """
    Get content reports (moderators only).

    Args:
        status_filter: Filter by status
        category: Filter by category
        page: Page number
        page_size: Items per page
        current_user: Authenticated moderator

    Returns:
        ListResponse: List of content reports
    """
    try:
        reports, total_count = await governance_service.get_content_reports(
            status=status_filter,
            category=category,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            data=[report.dict() for report in reports],
            total=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/reports", response_model=DataResponse)
async def create_content_report(
    report_data: ContentReportCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Report content for moderation.

    Args:
        report_data: Content report data
        current_user: Authenticated user

    Returns:
        DataResponse: Created report
    """
    try:
        report = await governance_service.create_content_report(
            report_data=report_data,
            reporter_id=str(current_user.id)
        )

        return DataResponse(
            data=report.dict(),
            message="Content report submitted successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/moderation/actions", response_model=ListResponse)
async def get_moderation_actions(
    moderator_id: Optional[str] = Query(None, description="Filter by moderator ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_moderator)
):
    """
    Get moderation actions (moderators only).

    Args:
        moderator_id: Filter by moderator ID
        action_type: Filter by action type
        page: Page number
        page_size: Items per page
        current_user: Authenticated moderator

    Returns:
        ListResponse: List of moderation actions
    """
    try:
        actions, total_count = await governance_service.get_moderation_actions(
            moderator_id=moderator_id,
            action_type=action_type,
            page=page,
            page_size=page_size
        )

        return ListResponse.create(
            data=[action.dict() for action in actions],
            total=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/moderation/actions", response_model=DataResponse)
async def execute_moderation_action(
    action_data: ModerationActionCreate,
    current_user: User = Depends(require_moderator)
):
    """
    Execute a moderation action (moderators only).

    Args:
        action_data: Moderation action data
        current_user: Authenticated moderator

    Returns:
        DataResponse: Executed action record
    """
    try:
        action_record = await governance_service.execute_moderation_action(
            action_data=action_data,
            moderator_id=str(current_user.id)
        )

        return DataResponse(
            data=action_record.dict(),
            message="Moderation action executed successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/moderation/stats", response_model=DataResponse)
async def get_moderation_stats(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: User = Depends(require_moderator)
):
    """
    Get moderation statistics (moderators only).

    Args:
        start_date: Start date filter
        end_date: End date filter
        current_user: Authenticated moderator

    Returns:
        DataResponse: Moderation statistics
    """
    try:
        stats = await governance_service.get_moderation_stats(
            start_date=start_date,
            end_date=end_date
        )

        return DataResponse(
            data=stats.dict(),
            message="Moderation statistics retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Community Guidelines Routes
@router.get("/guidelines", response_model=ListResponse)
async def get_community_guidelines(
    category: Optional[str] = Query(None, description="Filter by category"),
    language_specific: Optional[bool] = Query(None, description="Filter language-specific guidelines"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get community guidelines.

    Args:
        category: Filter by category
        language_specific: Filter language-specific guidelines
        page: Page number
        page_size: Items per page

    Returns:
        ListResponse: Community guidelines
    """
    try:
        # This would be implemented to fetch guidelines from database
        # For now, return placeholder data
        guidelines = [
            {
                "id": "1",
                "title": "Respectful Communication",
                "description": "All community members must communicate respectfully and constructively.",
                "category": "behavior",
                "severity_level": 3,
                "examples": [
                    "Use polite language when providing feedback",
                    "Avoid personal attacks or discriminatory language",
                    "Provide constructive criticism rather than simple rejection"
                ],
                "consequences": [
                    "First offense: Warning",
                    "Repeated offenses: Temporary suspension",
                    "Severe violations: Permanent ban"
                ]
            },
            {
                "id": "2",
                "title": "Quality Submissions",
                "description": "All submissions must meet minimum quality standards.",
                "category": "content",
                "severity_level": 4,
                "examples": [
                    "Clear audio without background noise",
                    "Accurate transcriptions",
                    "Culturally appropriate content"
                ],
                "consequences": [
                    "Low quality: Content removal",
                    "Repeated low quality: Points deduction",
                    "Intentional spam: Suspension"
                ]
            }
        ]

        return ListResponse.create(
            items=guidelines,
            total_count=len(guidelines),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Dashboard for moderators
@router.get("/moderation/dashboard", response_model=DataResponse)
async def get_moderation_dashboard(
    current_user: User = Depends(require_moderator)
):
    """
    Get moderation dashboard data (moderators only).

    Args:
        current_user: Authenticated moderator

    Returns:
        DataResponse: Dashboard data
    """
    try:
        # Get various statistics for the dashboard
        stats = await governance_service.get_moderation_stats()

        # Get recent disputes assigned to this moderator
        recent_disputes, _ = await governance_service.get_disputes(
            assigned_to=str(current_user.id),
            page=1,
            page_size=5
        )

        dashboard_data = {
            "moderation_stats": stats.model_dump() if hasattr(stats, 'model_dump') else stats.dict(),
            "recent_disputes": [dispute.model_dump() if hasattr(dispute, 'model_dump') else dispute.dict() for dispute in recent_disputes],
            "pending_reports_count": 0,  # Would be implemented
            "escalated_issues_count": 0   # Would be implemented
        }

        return DataResponse(
            data=dashboard_data,
            message="Moderation dashboard data retrieved successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
"""
Gamification API Routes for StudyFlow.

Provides gamification features including points, levels, leaderboards,
and challenges to enhance student engagement.

Features:
- View personal stats (points, level, streak)
- Organization leaderboards
- Daily/weekly challenges
- Challenge completion tracking
- Activity history

Author: KasaAI
Created: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.gamification_service import (
    GamificationService,
    ActivityType,
    ChallengeType
)

from app.core.database import MongoDB
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification", tags=["Gamification"])

# Admin-only actions
require_admin = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


# ============================================================================
# Request/Response Models
# ============================================================================

class UserStatsResponse(BaseModel):
    """User gamification statistics."""
    total_points: int
    current_level: int
    current_streak: int
    longest_streak: int
    points_to_next_level: int
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str
    user_name: str
    total_points: int
    current_level: int
    current_streak: int


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""
    timeframe: str
    entries: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    user_points: Optional[int] = None


class ChallengeCreateRequest(BaseModel):
    """Request to create a challenge."""
    challenge_type: ChallengeType
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    target: int = Field(..., gt=0)
    target_metric: str = Field(..., description="Metric to track (modules, questions, assessments)")
    points_reward: int = Field(..., gt=0)
    start_date: datetime
    end_date: datetime


class ChallengeResponse(BaseModel):
    """Challenge response."""
    id: str
    challenge_type: str
    title: str
    description: str
    target: int
    target_metric: str
    points_reward: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    is_completed: Optional[bool] = None
    progress: Optional[Dict[str, Any]] = None


class ChallengeProgressResponse(BaseModel):
    """Challenge progress response."""
    challenge_id: str
    completed: bool
    progress: int
    target: int
    percentage: float


# ============================================================================
# Helper Functions
# ============================================================================

def get_gamification_service() -> GamificationService:
    """Get gamification service instance."""
    db = MongoDB.get_database()
    return GamificationService(db)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/me", response_model=UserStatsResponse)
async def get_my_stats(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get current user's gamification statistics.

    Returns:
        User stats including points, level, streak, and recent activities
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        gamification_service = get_gamification_service()

        # Update streak on every stats request
        await gamification_service.update_streak(user_id, organization_id)

        # Get stats
        stats = await gamification_service.get_user_stats(user_id, organization_id)

        return UserStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get user stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    timeframe: str = Query("all_time", description="Timeframe (all_time, month, week)"),
    limit: int = Query(10, ge=5, le=100),
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get leaderboard for organization.

    Args:
        timeframe: Timeframe filter (all_time, month, week)
        limit: Number of entries to return

    Returns:
        Leaderboard with rankings and user's own position
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        gamification_service = get_gamification_service()

        # Get leaderboard
        leaderboard = await gamification_service.get_leaderboard(
            organization_id,
            timeframe,
            limit
        )

        # Find user's rank
        user_rank = None
        user_points = None

        for entry in leaderboard:
            if entry["user_id"] == user_id:
                user_rank = entry["rank"]
                user_points = entry["total_points"]
                break

        # Convert to response models
        entries = [LeaderboardEntry(**entry) for entry in leaderboard]

        return LeaderboardResponse(
            timeframe=timeframe,
            entries=entries,
            user_rank=user_rank,
            user_points=user_points
        )

    except Exception as e:
        logger.error(f"Failed to get leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leaderboard: {str(e)}"
        )


@router.post("/challenges", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    request: ChallengeCreateRequest,
    user_context: dict = Depends(require_admin)
):
    """
    Create a challenge for students (admin/teacher only).

    Args:
        request: Challenge creation request
        user_context: Admin user context

    Returns:
        Created challenge
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        gamification_service = get_gamification_service()

        # Validate dates
        if request.end_date <= request.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )

        # Validate target metric
        valid_metrics = ["modules", "questions", "assessments"]
        if request.target_metric not in valid_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_metric. Must be one of: {', '.join(valid_metrics)}"
            )

        # Create challenge
        challenge = await gamification_service.create_challenge(
            organization_id=organization_id,
            challenge_type=request.challenge_type,
            title=request.title,
            description=request.description,
            target=request.target,
            target_metric=request.target_metric,
            points_reward=request.points_reward,
            start_date=request.start_date,
            end_date=request.end_date,
            created_by=user_id
        )

        return ChallengeResponse(
            id=challenge["_id"],
            challenge_type=challenge["challenge_type"],
            title=challenge["title"],
            description=challenge["description"],
            target=challenge["target"],
            target_metric=challenge["target_metric"],
            points_reward=challenge["points_reward"],
            start_date=challenge["start_date"],
            end_date=challenge["end_date"],
            is_active=challenge["is_active"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create challenge: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create challenge: {str(e)}"
        )


@router.get("/challenges", response_model=List[ChallengeResponse])
async def get_challenges(
    challenge_type: Optional[str] = Query(None, description="Filter by challenge type"),
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get active challenges for organization.

    Args:
        challenge_type: Optional filter by challenge type (daily, weekly, special)
        user_context: User context

    Returns:
        List of active challenges with user's progress
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        gamification_service = get_gamification_service()

        # Get active challenges
        filter_type = ChallengeType(challenge_type) if challenge_type else None
        challenges = await gamification_service.get_active_challenges(
            organization_id,
            filter_type
        )

        # Check user's progress on each challenge
        result = []
        for challenge in challenges:
            challenge_id = str(challenge["_id"])

            # Check completion
            completed, progress_data = await gamification_service.check_challenge_completion(
                user_id,
                organization_id,
                challenge_id
            )

            result.append(ChallengeResponse(
                id=challenge_id,
                challenge_type=challenge["challenge_type"],
                title=challenge["title"],
                description=challenge["description"],
                target=challenge["target"],
                target_metric=challenge["target_metric"],
                points_reward=challenge["points_reward"],
                start_date=challenge["start_date"],
                end_date=challenge["end_date"],
                is_active=challenge["is_active"],
                is_completed=completed,
                progress=progress_data
            ))

        return result

    except Exception as e:
        logger.error(f"Failed to get challenges: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get challenges: {str(e)}"
        )


@router.post("/challenges/{challenge_id}/check", response_model=ChallengeProgressResponse)
async def check_challenge_progress(
    challenge_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Check user's progress on a specific challenge.

    Args:
        challenge_id: Challenge identifier
        user_context: User context

    Returns:
        Challenge progress and completion status
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        gamification_service = get_gamification_service()

        # Check completion
        completed, progress_data = await gamification_service.check_challenge_completion(
            user_id,
            organization_id,
            challenge_id
        )

        return ChallengeProgressResponse(
            challenge_id=challenge_id,
            completed=completed,
            progress=progress_data.get("progress", 0),
            target=progress_data.get("target", 0),
            percentage=progress_data.get("percentage", 0)
        )

    except Exception as e:
        logger.error(f"Failed to check challenge progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check challenge progress: {str(e)}"
        )


@router.get("/points-config")
async def get_points_config():
    """
    Get points configuration for all activities (public).

    Returns:
        Points awarded for each activity type
    """
    from apps.shared.services.gamification_service import POINTS_CONFIG

    return {
        "activities": {
            activity_type.value: points
            for activity_type, points in POINTS_CONFIG.items()
        }
    }


@router.get("/levels")
async def get_levels_config():
    """
    Get level thresholds configuration (public).

    Returns:
        Points needed for each level
    """
    from apps.shared.services.gamification_service import LEVEL_THRESHOLDS

    return {
        "levels": [
            {
                "level": i + 1,
                "points_required": threshold
            }
            for i, threshold in enumerate(LEVEL_THRESHOLDS)
        ]
    }

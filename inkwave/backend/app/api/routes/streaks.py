"""
Streak API routes for InkWave.

Endpoints:
- GET    /streaks/my-streak            - Get current user's streak
- GET    /streaks/leaderboard           - Top streaks leaderboard
- POST   /streaks/check-expiry          - Check if streak has expired (admin/cron)
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header, Request, Query
from pydantic import BaseModel

from app.core.database import get_db
from app.services.streak_service import StreakService
from apps.shared.dependencies.auth import get_current_user
from app.models.streak import ListeningStreak

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaks", tags=["streaks"])


# ============================================================================
# SCHEMAS
# ============================================================================

class StreakResponse(BaseModel):
    """Response with user's streak data."""
    current_days: int
    longest_days: int
    total_active_days: int
    last_activity_date: Optional[str]
    streak_start_date: Optional[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/my-streak", response_model=StreakResponse)
async def get_my_streak(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's listening streak.

    Returns current streak, longest streak, and activity history.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's streak data
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    streak_service = StreakService(db)

    try:
        # Check if streak has expired first
        streak = await streak_service.check_streak_expiry(user_id)

        if not streak:
            # No streak data yet
            streak = ListeningStreak()

        return StreakResponse(
            current_days=streak.current_days,
            longest_days=streak.longest_days,
            total_active_days=streak.total_active_days,
            last_activity_date=streak.last_activity_date.isoformat() if streak.last_activity_date else None,
            streak_start_date=streak.streak_start_date.isoformat() if streak.streak_start_date else None
        )

    except Exception as e:
        logger.error(f"Failed to get streak for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get streak data"
        )


@router.get("/leaderboard")
async def get_streak_leaderboard(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get leaderboard of users by current streak.

    Args:
        limit: Number of results to return

    Returns:
        Top users by streak
    """
    db = get_db()
    streak_service = StreakService(db)

    try:
        leaderboard = await streak_service.get_leaderboard(limit=limit)

        return {
            "entries": leaderboard,
            "total": len(leaderboard)
        }

    except Exception as e:
        logger.error(f"Failed to get streak leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )


@router.post("/check-expiry")
async def check_all_streak_expiries(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Check and update expired streaks for all users.

    Admin/cron endpoint to be called daily to reset expired streaks.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Number of streaks checked and reset
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_role = user.get("role", "user")

    # Check if admin
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    db = get_db()
    streak_service = StreakService(db)

    try:
        # Get all users with streaks
        users = await db.users.find({
            "streak.current_days": {"$gt": 0}
        }).to_list(length=None)

        checked_count = 0
        reset_count = 0

        for user in users:
            user_id = user["user_id"]
            old_streak = user.get("streak", {}).get("current_days", 0)

            # Check expiry
            streak = await streak_service.check_streak_expiry(user_id)
            checked_count += 1

            if streak.current_days == 0 and old_streak > 0:
                reset_count += 1
                logger.info(f"Reset expired streak for user {user_id} (was {old_streak} days)")

        return {
            "message": f"Checked {checked_count} streaks, reset {reset_count}",
            "checked": checked_count,
            "reset": reset_count
        }

    except Exception as e:
        logger.error(f"Failed to check streak expiries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check expiries"
        )

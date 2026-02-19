"""
Achievement API routes for InkWave.

Endpoints:
- GET    /achievements                 - Get user's achievements
- POST   /achievements/check           - Check and award achievements
- PUT    /achievements/{id}/viewed     - Mark achievement as viewed
- GET    /achievements/leaderboard     - Top achievers
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header, Request, Query
from pydantic import BaseModel

from app.core.database import get_db
from app.services.achievement_service import AchievementService
from apps.shared.dependencies.auth import get_current_user
from app.models.achievement import UserAchievementsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/achievements", tags=["achievements"])


# ============================================================================
# SCHEMAS
# ============================================================================

class CheckAchievementsResponse(BaseModel):
    """Response from checking achievements."""
    newly_earned: list
    total_earned: int
    message: str


class MarkViewedRequest(BaseModel):
    """Request to mark achievement as viewed."""
    achievement_id: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=UserAchievementsResponse)
async def get_user_achievements(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Get all achievements for the current user.

    Returns earned, in-progress, and available achievements.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        User's achievements organized by status
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    achievement_service = AchievementService(db)

    try:
        achievements = await achievement_service.get_user_achievements(user_id)
        return achievements

    except Exception as e:
        logger.error(f"Failed to get achievements for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get achievements"
        )


@router.post("/check", response_model=CheckAchievementsResponse)
async def check_achievements(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Check and award any newly earned achievements for the current user.

    This is called after actions that might trigger achievements
    (e.g., after listening, completing a book, etc.).

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        List of newly earned achievements
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    achievement_service = AchievementService(db)

    try:
        newly_earned = await achievement_service.check_and_award_achievements(user_id)

        # Get total earned achievements
        user_achievements = await achievement_service.get_user_achievements(user_id)

        message = "No new achievements" if not newly_earned else f"Earned {len(newly_earned)} new achievement(s)!"

        return CheckAchievementsResponse(
            newly_earned=[{
                "achievement_id": ach.achievement_id,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "tier": ach.tier,
                "points": ach.points
            } for ach in newly_earned],
            total_earned=user_achievements.achievements_earned,
            message=message
        )

    except Exception as e:
        logger.error(f"Failed to check achievements for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check achievements"
        )


@router.put("/{achievement_id}/viewed")
async def mark_achievement_viewed(
    achievement_id: str,
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Mark an achievement as viewed by the user.

    Args:
        achievement_id: Achievement ID
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Success message
    """
    # Get current user
    user = await get_current_user(request, authorization)
    user_id = user.get("id") or user.get("user_id")

    db = get_db()
    achievement_service = AchievementService(db)

    try:
        success = await achievement_service.mark_viewed(user_id, achievement_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Achievement not found"
            )

        return {"message": "Achievement marked as viewed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark achievement viewed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update achievement"
        )


@router.get("/leaderboard")
async def get_achievement_leaderboard(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get leaderboard of users by achievement points.

    Args:
        limit: Number of results to return

    Returns:
        Top achievers leaderboard
    """
    db = get_db()

    try:
        # Get top users by achievement points
        pipeline = [
            {
                "$match": {
                    "social_stats.achievement_points": {"$gt": 0},
                    "privacy_settings.appear_in_leaderboard": True,
                    "privacy_settings.leaderboard_display_mode": {"$ne": "opt_out"}
                }
            },
            {
                "$project": {
                    "user_id": 1,
                    "username": 1,
                    "display_name": 1,
                    "avatar_url": 1,
                    "achievement_points": "$social_stats.achievement_points",
                    "achievements_earned": "$social_stats.achievements_earned",
                    "display_mode": "$privacy_settings.leaderboard_display_mode"
                }
            },
            {
                "$sort": {"achievement_points": -1}
            },
            {
                "$limit": limit
            }
        ]

        users = await db.users.aggregate(pipeline).to_list(length=limit)

        # Add ranks and handle privacy
        leaderboard = []
        for rank, user in enumerate(users, 1):
            display_mode = user.get("display_mode", "full_profile")

            entry = {
                "rank": rank,
                "user_id": user["user_id"],
                "achievement_points": user.get("achievement_points", 0),
                "achievements_earned": user.get("achievements_earned", 0),
                "display_mode": display_mode
            }

            # Apply privacy settings
            if display_mode == "anonymous":
                # Generate nature-inspired username if user doesn't have one
                from app.services.username_generator import get_display_username
                display_username = get_display_username(user)

                entry["username"] = display_username
                entry["display_name"] = display_username
                entry["avatar_url"] = None
            else:
                entry["username"] = user.get("username")
                entry["display_name"] = user.get("display_name")
                entry["avatar_url"] = user.get("avatar_url")

            leaderboard.append(entry)

        return {
            "entries": leaderboard,
            "total": len(leaderboard)
        }

    except Exception as e:
        logger.error(f"Failed to get achievement leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )


@router.post("/initialize")
async def initialize_achievements(
    request: Request = None,
    authorization: Optional[str] = Header(None)
):
    """
    Initialize achievement definitions in database.

    Admin endpoint to set up or update achievements.

    Args:
        request: FastAPI request object
        authorization: Auth token

    Returns:
        Number of achievements created
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
    achievement_service = AchievementService(db)

    try:
        count = await achievement_service.initialize_achievements()

        return {
            "message": f"Successfully initialized {count} new achievements",
            "total_created": count
        }

    except Exception as e:
        logger.error(f"Failed to initialize achievements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize achievements"
        )

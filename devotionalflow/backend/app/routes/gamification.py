"""
Gamification API routes for Fresh Manna.
Handles streaks, points, achievements, and leaderboards.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.utils.auth import get_current_user, get_current_user_optional
from app.models.user import TokenData
from app.models.gamification import (
    GamificationProfileResponse,
    AchievementResponse,
    StreakResponse,
    LeaderboardEntry,
)
from app.services.gamification_service import (
    get_profile_response,
    get_or_create_profile,
    get_streak_response,
    use_streak_freeze,
    update_achievement_progress,
)
from app.constants.achievements import ACHIEVEMENTS, get_achievement
from app.db.mongodb import get_database
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== PROFILE =====

@router.get("/profile", response_model=GamificationProfileResponse)
async def get_gamification_profile(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get user's gamification profile.

    **Returns:**
    - Current streak, level, XP, achievements count, etc.
    """
    return await get_profile_response(current_user.user_id)


# ===== STREAK =====

@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get user's streak information.

    **Returns:**
    - Current streak, longest streak, total days read
    - Streak freezes available
    - Next milestone info
    """
    return await get_streak_response(current_user.user_id)


@router.post("/streak/freeze")
async def use_freeze(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Use a streak freeze to protect streak.

    **Returns:**
    - Success status
    """
    success = await use_streak_freeze(current_user.user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No streak freezes available"
        )

    return {"success": True, "message": "Streak freeze used successfully"}


# ===== ACHIEVEMENTS =====

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_achievements(
    current_user: TokenData = Depends(get_current_user),
    category: Optional[str] = None,
    unlocked_only: bool = False,
):
    """
    Get all achievements with user's progress.

    **Query Parameters:**
    - category: Filter by category (reading, engagement, social, spiritual, special)
    - unlocked_only: Only show unlocked achievements

    **Returns:**
    - List of achievements with progress
    """
    profile = await get_or_create_profile(current_user.user_id)

    # Get user achievements map
    user_achievements_map = {
        ua.achievement_id: ua for ua in profile.achievements
    }

    achievements_response = []

    for achievement in ACHIEVEMENTS:
        # Filter by category if specified
        if category and achievement.category != category:
            continue

        user_achievement = user_achievements_map.get(achievement.id)

        # Check if unlocked
        unlocked = user_achievement.unlocked if user_achievement else False

        # Filter unlocked_only
        if unlocked_only and not unlocked:
            continue

        achievements_response.append(AchievementResponse(
            id=achievement.id,
            name=achievement.name,
            description=achievement.description,
            category=achievement.category,
            rarity=achievement.rarity,
            icon_name=achievement.icon_name,
            points_reward=achievement.points_reward,
            coins_reward=achievement.coins_reward,
            unlocked=unlocked,
            progress=user_achievement.progress if user_achievement else 0,
            progress_target=achievement.requirement.target,
            unlocked_at=user_achievement.unlocked_at if user_achievement else None
        ))

    return achievements_response


@router.get("/achievements/{achievement_id}", response_model=AchievementResponse)
async def get_achievement_detail(
    achievement_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get specific achievement details with user's progress.

    **Parameters:**
    - achievement_id: Achievement ID

    **Returns:**
    - Achievement details with user progress
    """
    achievement = get_achievement(achievement_id)

    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement {achievement_id} not found"
        )

    profile = await get_or_create_profile(current_user.user_id)

    user_achievement = next(
        (ua for ua in profile.achievements if ua.achievement_id == achievement_id),
        None
    )

    return AchievementResponse(
        id=achievement.id,
        name=achievement.name,
        description=achievement.description,
        category=achievement.category,
        rarity=achievement.rarity,
        icon_name=achievement.icon_name,
        points_reward=achievement.points_reward,
        coins_reward=achievement.coins_reward,
        unlocked=user_achievement.unlocked if user_achievement else False,
        progress=user_achievement.progress if user_achievement else 0,
        progress_target=achievement.requirement.target,
        unlocked_at=user_achievement.unlocked_at if user_achievement else None
    )


# ===== LEADERBOARD =====

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    type: str = "global",  # global, friends, weekly
    limit: int = 100,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
):
    """
    Get leaderboard rankings.

    **Public Endpoint** - Authentication optional. Logged-in users can access friends leaderboard.

    **Query Parameters:**
    - type: Leaderboard type (global, friends, weekly)
    - limit: Maximum number of entries (default 100)

    **Returns:**
    - List of leaderboard entries
    """
    db = get_database()

    if type == "global":
        # Get top users by total XP
        cursor = db.gamification_profiles.find().sort("level.total_xp", -1).limit(limit)

        entries = []
        rank = 1

        async for doc in cursor:
            # Get user info
            user_doc = await db.users.find_one({"_id": doc["user_id"]})

            if user_doc:
                entries.append(LeaderboardEntry(
                    rank=rank,
                    user_id=doc["user_id"],
                    username=user_doc.get("name", "Anonymous"),
                    avatar_url=user_doc.get("avatar_url"),
                    level=doc["level"]["current_level"],
                    total_xp=doc["level"]["total_xp"],
                    current_streak=doc["streak"]["current_streak"],
                    change_from_yesterday=0  # TODO: Calculate daily change
                ))
                rank += 1

        return entries

    elif type == "friends":
        # TODO: Implement friends leaderboard
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Friends leaderboard not yet implemented"
        )

    elif type == "weekly":
        # TODO: Implement weekly challenge leaderboard
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Weekly leaderboard not yet implemented"
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid leaderboard type. Use: global, friends, weekly"
        )


# ===== STATISTICS =====

@router.get("/stats")
async def get_stats(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get user's gamification statistics.

    **Returns:**
    - Detailed statistics and progress
    """
    profile = await get_or_create_profile(current_user.user_id)

    return {
        "user_id": current_user.user_id,
        "level": {
            "current_level": profile.level.current_level,
            "level_tier": profile.level.level_tier,
            "total_xp": profile.level.total_xp,
            "xp_to_next_level": profile.level.xp_to_next_level,
            "progress_percentage": (profile.level.total_xp / profile.level.xp_to_next_level) * 100
        },
        "streak": {
            "current": profile.streak.current_streak,
            "longest": profile.streak.longest_streak,
            "total_days": profile.streak.total_days_read,
            "freezes": profile.streak.streak_freezes_available
        },
        "achievements": {
            "unlocked": len([a for a in profile.achievements if a.unlocked]),
            "total": len(ACHIEVEMENTS),
            "completion_percentage": (len([a for a in profile.achievements if a.unlocked]) / len(ACHIEVEMENTS)) * 100
        },
        "currency": {
            "manna_coins": profile.manna_coins
        },
        "activity": {
            "total_devotionals_read": profile.total_devotionals_read,
            "total_comments": profile.total_comments,
            "total_shares": profile.total_shares,
            "total_likes_given": profile.total_likes_given,
            "total_likes_received": profile.total_likes_received,
            "total_reading_time_minutes": profile.total_reading_time_minutes
        }
    }


# ===== ADMIN ENDPOINTS =====

@router.post("/admin/reset-user/{user_id}")
async def reset_user_gamification(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Reset user's gamification profile (admin only).

    **Parameters:**
    - user_id: User ID to reset

    **Note:**
    - This is destructive and cannot be undone
    """
    # Check if admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    db = get_database()

    # Delete gamification profile
    result = await db.gamification_profiles.delete_one({"user_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User gamification profile not found"
        )

    return {"success": True, "message": f"Gamification profile reset for user {user_id}"}


# ===== CHALLENGES =====

@router.get("/challenges")
async def get_daily_challenges(
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get today's active challenges.

    **Returns:**
    - List of daily and weekly challenges active today
    """
    from app.constants.challenges import get_active_templates

    templates = get_active_templates(include_weekly=True)

    # Convert templates to response format
    challenges = []
    for template in templates:
        challenges.append({
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "type": template.type,
            "requirement_type": template.requirement_type,
            "requirement_target": template.requirement_target,
            "points_reward": template.points_reward,
            "coins_reward": template.coins_reward,
            "progress": 0,  # TODO: Track actual progress
            "completed": False
        })

    return challenges

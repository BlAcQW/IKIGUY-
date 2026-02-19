"""
Gamification service for Fresh Manna.
Handles streaks, points, achievements, and challenges.
"""

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict
from app.db.mongodb import get_database
from app.models.gamification import (
    UserGamificationProfile,
    StreakData,
    LevelData,
    PointsTransaction,
    UserAchievement,
    UserChallenge,
    AchievementResponse,
    GamificationProfileResponse,
    StreakResponse,
)
from app.constants.achievements import ACHIEVEMENTS, get_achievement
import logging

logger = logging.getLogger(__name__)


# ===== STREAK MANAGEMENT =====

async def update_streak(user_id: str) -> StreakData:
    """
    Update user's reading streak.
    Called when user completes a devotional.

    Args:
        user_id: User ID

    Returns:
        Updated streak data
    """
    db = get_database()
    profile = await get_or_create_profile(user_id)

    today = datetime.utcnow().date()
    last_read = profile.streak.last_read_date.date() if profile.streak.last_read_date else None

    # Check if already read today
    if last_read == today:
        logger.info(f"User {user_id} already read today - streak unchanged")
        return profile.streak

    # Check if streak continues
    if last_read:
        days_diff = (today - last_read).days

        if days_diff == 1:
            # Consecutive day - increment streak
            profile.streak.current_streak += 1
            profile.streak.total_days_read += 1

            # Update longest streak if needed
            if profile.streak.current_streak > profile.streak.longest_streak:
                profile.streak.longest_streak = profile.streak.current_streak

        elif days_diff > 1:
            # Streak broken - check for freeze
            if profile.streak.streak_freezes_available > 0:
                # Use a freeze
                profile.streak.streak_freezes_available -= 1
                profile.streak.current_streak += 1
                profile.streak.total_days_read += 1
                logger.info(f"User {user_id} used streak freeze")
            else:
                # Streak broken - reset
                profile.streak.current_streak = 1
                profile.streak.total_days_read += 1
                profile.streak.streak_start_date = datetime.utcnow()
                logger.info(f"User {user_id} streak broken - reset to 1")
    else:
        # First read ever
        profile.streak.current_streak = 1
        profile.streak.total_days_read = 1
        profile.streak.streak_start_date = datetime.utcnow()

    # Update last read date
    profile.streak.last_read_date = datetime.utcnow()

    # Check for streak milestones and award freezes
    if profile.streak.current_streak == 7:
        profile.streak.streak_freezes_available += 1
        profile.streak.milestones_achieved.append("7_day")
        await check_and_award_achievement(user_id, "steadfast")
    elif profile.streak.current_streak == 30:
        profile.streak.streak_freezes_available += 1
        profile.streak.milestones_achieved.append("30_day")
        await check_and_award_achievement(user_id, "devoted")
    elif profile.streak.current_streak == 90:
        profile.streak.streak_freezes_available += 2
        profile.streak.milestones_achieved.append("90_day")
        await check_and_award_achievement(user_id, "faithful_warrior")
    elif profile.streak.current_streak == 3:
        profile.streak.milestones_achieved.append("3_day")
        await check_and_award_achievement(user_id, "ignited")

    # Save profile
    profile.updated_at = datetime.utcnow()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {"$set": profile.dict()},
        upsert=True
    )

    return profile.streak


async def use_streak_freeze(user_id: str) -> bool:
    """
    Use a streak freeze to protect streak.

    Args:
        user_id: User ID

    Returns:
        True if freeze was used successfully
    """
    db = get_database()
    profile = await get_or_create_profile(user_id)

    if profile.streak.streak_freezes_available > 0:
        profile.streak.streak_freezes_available -= 1
        profile.updated_at = datetime.utcnow()

        await db.gamification_profiles.update_one(
            {"user_id": user_id},
            {"$set": profile.dict()}
        )

        return True

    return False


# ===== POINTS & LEVELS =====

async def award_points(user_id: str, action: str, points: int, metadata: Optional[Dict] = None) -> LevelData:
    """
    Award points to user for an action.

    Args:
        user_id: User ID
        action: Action that earned points
        points: Points to award
        metadata: Additional metadata

    Returns:
        Updated level data
    """
    db = get_database()
    profile = await get_or_create_profile(user_id)

    # Create transaction
    transaction = PointsTransaction(
        action=action,
        points=points,
        metadata=metadata
    )

    # Add points
    profile.level.total_xp += points
    profile.points_history.append(transaction)

    # Check for level up
    while profile.level.total_xp >= profile.level.xp_to_next_level:
        profile.level.current_level += 1
        profile.level.xp_to_next_level = profile.level.calculate_next_level_xp()

        # Update tier
        if profile.level.current_level <= 10:
            profile.level.level_tier = "Seeker"
        elif profile.level.current_level <= 25:
            profile.level.level_tier = "Disciple"
        elif profile.level.current_level <= 50:
            profile.level.level_tier = "Faithful"
        elif profile.level.current_level <= 75:
            profile.level.level_tier = "Shepherd"
        else:
            profile.level.level_tier = "Elder"

        logger.info(f"User {user_id} leveled up to {profile.level.current_level}")

    # Save profile
    profile.updated_at = datetime.utcnow()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {"$set": profile.dict()},
        upsert=True
    )

    return profile.level


# ===== ACHIEVEMENTS =====

async def check_and_award_achievement(user_id: str, achievement_id: str) -> Optional[AchievementResponse]:
    """
    Check if user qualifies for achievement and award it.

    Args:
        user_id: User ID
        achievement_id: Achievement ID

    Returns:
        Achievement response if awarded, None if already unlocked
    """
    db = get_database()
    profile = await get_or_create_profile(user_id)

    # Check if already unlocked
    user_achievement = next(
        (a for a in profile.achievements if a.achievement_id == achievement_id),
        None
    )

    if user_achievement and user_achievement.unlocked:
        return None

    # Get achievement definition
    achievement = get_achievement(achievement_id)
    if not achievement:
        logger.error(f"Achievement {achievement_id} not found")
        return None

    # Award achievement
    if user_achievement:
        user_achievement.unlocked = True
        user_achievement.unlocked_at = datetime.utcnow()
    else:
        user_achievement = UserAchievement(
            achievement_id=achievement_id,
            unlocked=True,
            unlocked_at=datetime.utcnow()
        )
        profile.achievements.append(user_achievement)

    # Award points and coins
    await award_points(user_id, f"achievement_{achievement_id}", achievement.points_reward)
    profile.manna_coins += achievement.coins_reward

    # Save profile
    profile.updated_at = datetime.utcnow()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {"$set": profile.dict()},
        upsert=True
    )

    logger.info(f"User {user_id} unlocked achievement {achievement_id}")

    return AchievementResponse(
        id=achievement.id,
        name=achievement.name,
        description=achievement.description,
        category=achievement.category,
        rarity=achievement.rarity,
        icon_name=achievement.icon_name,
        points_reward=achievement.points_reward,
        coins_reward=achievement.coins_reward,
        unlocked=True,
        progress=achievement.requirement.target,
        progress_target=achievement.requirement.target,
        unlocked_at=user_achievement.unlocked_at
    )


async def update_achievement_progress(user_id: str, requirement_type: str, increment: int = 1):
    """
    Update progress for all achievements with matching requirement type.

    Args:
        user_id: User ID
        requirement_type: Type of requirement (e.g., 'read_count')
        increment: How much to increment by
    """
    db = get_database()
    profile = await get_or_create_profile(user_id)

    # Find all achievements with this requirement type
    for achievement in ACHIEVEMENTS:
        if achievement.requirement.type == requirement_type:
            # Find or create user achievement
            user_achievement = next(
                (a for a in profile.achievements if a.achievement_id == achievement.id),
                None
            )

            if not user_achievement:
                user_achievement = UserAchievement(
                    achievement_id=achievement.id,
                    progress=0
                )
                profile.achievements.append(user_achievement)

            if not user_achievement.unlocked:
                user_achievement.progress += increment

                # Check if unlocked
                if user_achievement.progress >= achievement.requirement.target:
                    await check_and_award_achievement(user_id, achievement.id)

    # Save profile
    profile.updated_at = datetime.utcnow()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {"$set": profile.dict()},
        upsert=True
    )


# ===== PROFILE MANAGEMENT =====

async def get_or_create_profile(user_id: str) -> UserGamificationProfile:
    """
    Get user's gamification profile or create if doesn't exist.

    Args:
        user_id: User ID

    Returns:
        User gamification profile
    """
    db = get_database()

    # Try to get existing profile
    profile_doc = await db.gamification_profiles.find_one({"user_id": user_id})

    if profile_doc:
        return UserGamificationProfile(**profile_doc)

    # Create new profile
    profile = UserGamificationProfile(user_id=user_id)

    # Award welcome achievement
    profile.achievements.append(UserAchievement(
        achievement_id="first_day",
        unlocked=True,
        progress=1,
        unlocked_at=datetime.utcnow()
    ))

    # Save to database
    await db.gamification_profiles.insert_one(profile.dict())

    logger.info(f"Created new gamification profile for user {user_id}")

    return profile


async def get_profile_response(user_id: str) -> GamificationProfileResponse:
    """
    Get gamification profile response for API.

    Args:
        user_id: User ID

    Returns:
        Gamification profile response
    """
    profile = await get_or_create_profile(user_id)

    return GamificationProfileResponse(
        user_id=user_id,
        current_streak=profile.streak.current_streak,
        longest_streak=profile.streak.longest_streak,
        current_level=profile.level.current_level,
        level_tier=profile.level.level_tier,
        total_xp=profile.level.total_xp,
        xp_to_next_level=profile.level.xp_to_next_level,
        achievements_unlocked=len([a for a in profile.achievements if a.unlocked]),
        total_achievements=len(ACHIEVEMENTS),
        manna_coins=profile.manna_coins,
        active_challenges_count=len(profile.active_challenges),
        total_devotionals_read=profile.total_devotionals_read
    )


async def get_streak_response(user_id: str) -> StreakResponse:
    """
    Get streak information for API.

    Args:
        user_id: User ID

    Returns:
        Streak response
    """
    profile = await get_or_create_profile(user_id)

    # Determine next milestone
    next_milestone = None
    current = profile.streak.current_streak

    if current < 3:
        next_milestone = {"days": 3, "reward": "Ignited badge 🔥"}
    elif current < 7:
        next_milestone = {"days": 7, "reward": "Steadfast badge ⭐ + Streak Freeze"}
    elif current < 30:
        next_milestone = {"days": 30, "reward": "Devoted badge 💎 + Streak Freeze"}
    elif current < 90:
        next_milestone = {"days": 90, "reward": "Faithful Warrior badge 👑 + 2 Streak Freezes"}
    elif current < 365:
        next_milestone = {"days": 365, "reward": "Spiritual Champion badge 🏆"}

    return StreakResponse(
        current_streak=profile.streak.current_streak,
        longest_streak=profile.streak.longest_streak,
        total_days_read=profile.streak.total_days_read,
        streak_freezes_available=profile.streak.streak_freezes_available,
        last_read_date=profile.streak.last_read_date,
        next_milestone=next_milestone
    )


# ===== ACTION HANDLERS =====

async def handle_devotional_read(user_id: str, devotional_id: str, read_time: Optional[datetime] = None):
    """
    Handle when user reads a devotional.
    Awards points, updates streak, updates statistics.

    Args:
        user_id: User ID
        devotional_id: Devotional ID
        read_time: Time of read (defaults to now)
    """
    read_time = read_time or datetime.utcnow()

    # Update streak
    await update_streak(user_id)

    # Award points
    await award_points(user_id, "read_devotional", 10, {"devotional_id": devotional_id})

    # Update statistics
    db = get_database()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_devotionals_read": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # Update achievement progress
    await update_achievement_progress(user_id, "read_count", 1)

    # Check time-based achievements
    hour = read_time.hour
    if hour < 6:
        await update_achievement_progress(user_id, "early_morning_reads", 1)
    elif hour >= 22:
        await update_achievement_progress(user_id, "late_night_reads", 1)


async def handle_comment(user_id: str, devotional_id: str):
    """Handle when user comments on devotional."""
    # Award points
    await award_points(user_id, "comment", 3, {"devotional_id": devotional_id})

    # Update statistics
    db = get_database()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_comments": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # Update achievement progress
    await update_achievement_progress(user_id, "comment_count", 1)


async def handle_share(user_id: str, devotional_id: str, platform: str):
    """Handle when user shares devotional."""
    # Award points
    await award_points(user_id, "share", 5, {"devotional_id": devotional_id, "platform": platform})

    # Update statistics
    db = get_database()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_shares": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # Update achievement progress
    await update_achievement_progress(user_id, "share_count", 1)


async def handle_like(user_id: str, devotional_id: str):
    """Handle when user likes devotional."""
    # Award points
    await award_points(user_id, "like", 1, {"devotional_id": devotional_id})

    # Update statistics
    db = get_database()
    await db.gamification_profiles.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_likes_given": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # Update achievement progress
    await update_achievement_progress(user_id, "likes_given", 1)


async def handle_bookmark(user_id: str, devotional_id: str):
    """Handle when user bookmarks devotional."""
    # Update achievement progress
    await update_achievement_progress(user_id, "bookmark_count", 1)

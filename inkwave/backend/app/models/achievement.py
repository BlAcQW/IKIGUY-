"""
Achievement models for InkWave gamification system.

Defines achievements, badges, and user progress tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AchievementCategory(str, Enum):
    """Achievement categories."""
    LISTENING_TIME = "listening_time"
    BOOKS_COMPLETED = "books_completed"
    STREAKS = "streaks"
    SOCIAL = "social"
    SPECIAL = "special"


class AchievementTier(str, Enum):
    """Achievement tiers/levels."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class Achievement(BaseModel):
    """
    Achievement definition.

    Defines what needs to be accomplished to earn the achievement.
    """

    achievement_id: str = Field(..., description="Unique achievement identifier")
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="Achievement description")
    category: AchievementCategory = Field(..., description="Achievement category")
    tier: AchievementTier = Field(..., description="Achievement tier/level")

    # Achievement requirements
    requirement_type: str = Field(..., description="Type of requirement (e.g., 'listening_hours', 'books_completed')")
    requirement_value: float = Field(..., description="Value needed to unlock (e.g., 10 for '10 hours')")

    # Visual elements
    icon: Optional[str] = Field(None, description="Icon name or emoji")
    color: Optional[str] = Field(None, description="Badge color hex code")

    # Metadata
    points: int = Field(default=0, description="Points awarded for earning this achievement")
    is_secret: bool = Field(default=False, description="Hidden until earned")
    is_active: bool = Field(default=True, description="Whether achievement is currently available")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        use_enum_values = True


class UserAchievement(BaseModel):
    """
    User's progress and earned achievements.

    Tracks which achievements a user has earned and their progress.
    """

    user_achievement_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_id: str = Field(..., description="User ID")
    achievement_id: str = Field(..., description="Achievement ID")

    # Progress tracking
    current_progress: float = Field(default=0.0, description="Current progress toward achievement")
    is_completed: bool = Field(default=False, description="Whether achievement is earned")
    completed_at: Optional[datetime] = Field(None, description="When achievement was earned")

    # Notification tracking
    notification_sent: bool = Field(default=False, description="Whether user was notified")
    viewed: bool = Field(default=False, description="Whether user has viewed the achievement")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AchievementInDB(Achievement):
    """Achievement model with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True


class UserAchievementInDB(UserAchievement):
    """User achievement model with MongoDB _id."""
    id: Optional[str] = Field(None, alias="_id")

    class Config:
        """Pydantic config."""
        populate_by_name = True


class AchievementProgress(BaseModel):
    """User's progress on a specific achievement."""
    achievement: Achievement
    current_progress: float
    requirement_value: float
    percentage: float
    is_completed: bool
    completed_at: Optional[datetime]


class UserAchievementsResponse(BaseModel):
    """Response with user's achievements."""
    earned: List[Dict[str, Any]]  # Completed achievements
    in_progress: List[AchievementProgress]  # Achievements being worked on
    available: List[Achievement]  # Not yet started
    total_points: int
    achievements_earned: int
    achievements_total: int


# Achievement definitions
ACHIEVEMENT_DEFINITIONS = [
    # Listening Time Achievements
    {
        "achievement_id": "first_listen",
        "name": "First Listen",
        "description": "Listen to your first audiobook",
        "category": AchievementCategory.LISTENING_TIME,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "listening_minutes",
        "requirement_value": 1.0,
        "icon": "🎧",
        "color": "#CD7F32",
        "points": 10
    },
    {
        "achievement_id": "bronze_listener",
        "name": "Bronze Listener",
        "description": "Listen for 10 hours",
        "category": AchievementCategory.LISTENING_TIME,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "listening_hours",
        "requirement_value": 10.0,
        "icon": "🥉",
        "color": "#CD7F32",
        "points": 50
    },
    {
        "achievement_id": "silver_listener",
        "name": "Silver Listener",
        "description": "Listen for 50 hours",
        "category": AchievementCategory.LISTENING_TIME,
        "tier": AchievementTier.SILVER,
        "requirement_type": "listening_hours",
        "requirement_value": 50.0,
        "icon": "🥈",
        "color": "#C0C0C0",
        "points": 100
    },
    {
        "achievement_id": "gold_listener",
        "name": "Gold Listener",
        "description": "Listen for 100 hours",
        "category": AchievementCategory.LISTENING_TIME,
        "tier": AchievementTier.GOLD,
        "requirement_type": "listening_hours",
        "requirement_value": 100.0,
        "icon": "🥇",
        "color": "#FFD700",
        "points": 200
    },
    {
        "achievement_id": "platinum_listener",
        "name": "Platinum Listener",
        "description": "Listen for 500 hours",
        "category": AchievementCategory.LISTENING_TIME,
        "tier": AchievementTier.PLATINUM,
        "requirement_type": "listening_hours",
        "requirement_value": 500.0,
        "icon": "💎",
        "color": "#E5E4E2",
        "points": 500
    },

    # Books Completed Achievements
    {
        "achievement_id": "first_book",
        "name": "Book Worm",
        "description": "Complete your first book",
        "category": AchievementCategory.BOOKS_COMPLETED,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "books_completed",
        "requirement_value": 1.0,
        "icon": "📚",
        "color": "#CD7F32",
        "points": 20
    },
    {
        "achievement_id": "bibliophile",
        "name": "Bibliophile",
        "description": "Complete 10 books",
        "category": AchievementCategory.BOOKS_COMPLETED,
        "tier": AchievementTier.SILVER,
        "requirement_type": "books_completed",
        "requirement_value": 10.0,
        "icon": "📖",
        "color": "#C0C0C0",
        "points": 100
    },
    {
        "achievement_id": "voracious_reader",
        "name": "Voracious Reader",
        "description": "Complete 50 books",
        "category": AchievementCategory.BOOKS_COMPLETED,
        "tier": AchievementTier.GOLD,
        "requirement_type": "books_completed",
        "requirement_value": 50.0,
        "icon": "📚",
        "color": "#FFD700",
        "points": 300
    },

    # Streak Achievements
    {
        "achievement_id": "streak_7",
        "name": "Week Warrior",
        "description": "Listen for 7 days in a row",
        "category": AchievementCategory.STREAKS,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "streak_days",
        "requirement_value": 7.0,
        "icon": "🔥",
        "color": "#CD7F32",
        "points": 50
    },
    {
        "achievement_id": "streak_30",
        "name": "Monthly Master",
        "description": "Listen for 30 days in a row",
        "category": AchievementCategory.STREAKS,
        "tier": AchievementTier.SILVER,
        "requirement_type": "streak_days",
        "requirement_value": 30.0,
        "icon": "🔥",
        "color": "#C0C0C0",
        "points": 150
    },
    {
        "achievement_id": "streak_100",
        "name": "Century Streak",
        "description": "Listen for 100 days in a row",
        "category": AchievementCategory.STREAKS,
        "tier": AchievementTier.GOLD,
        "requirement_type": "streak_days",
        "requirement_value": 100.0,
        "icon": "🔥",
        "color": "#FFD700",
        "points": 500
    },

    # Time-based Achievements
    {
        "achievement_id": "night_owl",
        "name": "Night Owl",
        "description": "Listen for 10 hours between 10 PM and 6 AM",
        "category": AchievementCategory.SPECIAL,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "listening_hours_night",
        "requirement_value": 10.0,
        "icon": "🦉",
        "color": "#4B0082",
        "points": 75
    },
    {
        "achievement_id": "early_bird",
        "name": "Early Bird",
        "description": "Listen for 10 hours between 5 AM and 8 AM",
        "category": AchievementCategory.SPECIAL,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "listening_hours_morning",
        "requirement_value": 10.0,
        "icon": "🐦",
        "color": "#FF6347",
        "points": 75
    },

    # Social Achievements
    {
        "achievement_id": "social_butterfly",
        "name": "Social Butterfly",
        "description": "Follow 10 other listeners",
        "category": AchievementCategory.SOCIAL,
        "tier": AchievementTier.BRONZE,
        "requirement_type": "following_count",
        "requirement_value": 10.0,
        "icon": "🦋",
        "color": "#FF69B4",
        "points": 50
    },
    {
        "achievement_id": "popular",
        "name": "Popular",
        "description": "Get 25 followers",
        "category": AchievementCategory.SOCIAL,
        "tier": AchievementTier.SILVER,
        "requirement_type": "followers_count",
        "requirement_value": 25.0,
        "icon": "⭐",
        "color": "#C0C0C0",
        "points": 100
    }
]

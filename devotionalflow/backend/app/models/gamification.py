"""
Gamification models for Fresh Manna.
Handles streaks, points, levels, achievements, and challenges.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# ===== STREAK MODELS =====

class StreakData(BaseModel):
    """User streak tracking data."""
    current_streak: int = 0
    longest_streak: int = 0
    total_days_read: int = 0
    streak_freezes_available: int = 0
    last_read_date: Optional[datetime] = None
    streak_start_date: Optional[datetime] = None
    milestones_achieved: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===== POINTS & LEVEL MODELS =====

class PointsTransaction(BaseModel):
    """Record of points earned."""
    action: str  # 'read_devotional', 'share', 'comment', etc.
    points: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LevelData(BaseModel):
    """User level and XP data."""
    current_level: int = 1
    total_xp: int = 0
    xp_to_next_level: int = 100
    level_tier: str = "Seeker"  # Seeker, Disciple, Faithful, Shepherd, Elder

    def calculate_next_level_xp(self) -> int:
        """Calculate XP needed for next level using exponential curve."""
        return int(100 * (1.15 ** (self.current_level - 1)))


# ===== ACHIEVEMENT MODELS =====

class AchievementRequirement(BaseModel):
    """Requirements to unlock an achievement."""
    type: str  # 'read_count', 'streak_days', 'comments', 'shares', etc.
    target: int
    current: int = 0


class Achievement(BaseModel):
    """Achievement/badge definition."""
    id: str
    name: str
    description: str
    category: Literal['reading', 'engagement', 'social', 'spiritual', 'special']
    rarity: Literal['common', 'rare', 'epic', 'legendary']
    icon_name: str  # Icon identifier (will map to emoji or image)
    points_reward: int
    coins_reward: int = 0
    requirement: AchievementRequirement
    hidden: bool = False  # Hidden until unlocked


class UserAchievement(BaseModel):
    """User's achievement progress/unlock."""
    achievement_id: str
    unlocked: bool = False
    progress: int = 0
    unlocked_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===== CHALLENGE MODELS =====

class ChallengeRequirement(BaseModel):
    """Single requirement within a challenge."""
    type: str  # 'read_devotional', 'comment', 'share', etc.
    target: int
    current: int = 0
    description: str


class Challenge(BaseModel):
    """Challenge definition."""
    id: str
    name: str
    description: str
    type: Literal['daily', 'weekly', 'monthly', 'special']
    start_date: datetime
    end_date: datetime
    requirements: List[ChallengeRequirement]
    rewards: Dict = Field(default_factory=lambda: {"points": 25, "coins": 0})
    difficulty: Literal['easy', 'medium', 'hard'] = 'medium'
    participants_count: int = 0
    completion_rate: float = 0.0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserChallenge(BaseModel):
    """User's challenge participation."""
    challenge_id: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    completed: bool = False
    completed_at: Optional[datetime] = None
    requirements_progress: List[ChallengeRequirement] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===== MAIN GAMIFICATION PROFILE =====

class UserGamificationProfile(BaseModel):
    """Complete gamification profile for a user."""
    user_id: str

    # Streaks
    streak: StreakData = Field(default_factory=StreakData)

    # Points & Levels
    level: LevelData = Field(default_factory=LevelData)
    points_history: List[PointsTransaction] = Field(default_factory=list)

    # Achievements
    achievements: List[UserAchievement] = Field(default_factory=list)

    # Challenges
    active_challenges: List[UserChallenge] = Field(default_factory=list)
    completed_challenges: List[str] = Field(default_factory=list)

    # Currency
    manna_coins: int = 0

    # Statistics
    total_devotionals_read: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_likes_given: int = 0
    total_likes_received: int = 0
    favorite_category: Optional[str] = None
    total_reading_time_minutes: int = 0

    # Preferences
    notification_preferences: Dict = Field(default_factory=lambda: {
        "daily_reminder": True,
        "achievement_unlocked": True,
        "challenge_updates": True,
        "friend_activity": False
    })
    reminder_time: str = "08:00"  # HH:MM format

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ===== RESPONSE MODELS =====

class GamificationProfileResponse(BaseModel):
    """Gamification profile response for API."""
    user_id: str
    current_streak: int
    longest_streak: int
    current_level: int
    level_tier: str
    total_xp: int
    xp_to_next_level: int
    achievements_unlocked: int
    total_achievements: int
    manna_coins: int
    active_challenges_count: int
    total_devotionals_read: int


class AchievementResponse(BaseModel):
    """Achievement response for API."""
    id: str
    name: str
    description: str
    category: str
    rarity: str
    icon_name: str
    points_reward: int
    coins_reward: int
    unlocked: bool
    progress: int
    progress_target: int
    unlocked_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChallengeResponse(BaseModel):
    """Challenge response for API."""
    id: str
    name: str
    description: str
    type: str
    difficulty: str
    start_date: datetime
    end_date: datetime
    rewards: Dict
    joined: bool = False
    completed: bool = False
    progress_percentage: float = 0.0
    requirements_progress: List[ChallengeRequirement] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    user_id: str
    username: str
    avatar_url: Optional[str] = None
    level: int
    total_xp: int
    current_streak: int
    change_from_yesterday: int = 0  # +5, -2, 0


class StreakResponse(BaseModel):
    """Streak information response."""
    current_streak: int
    longest_streak: int
    total_days_read: int
    streak_freezes_available: int
    last_read_date: Optional[datetime] = None
    next_milestone: Optional[Dict] = None  # {"days": 7, "reward": "Steadfast badge"}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

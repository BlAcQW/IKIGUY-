"""
Gamification database models.

Defines the structure for the gamification system including:
- Member profiles (points, levels, streaks)
- Badge definitions and achievements
- Challenges and competitions
- Leaderboards and rankings
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models (Pydantic v2 compatible)."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        """Pydantic v2 core schema for ObjectId validation."""
        from pydantic_core import core_schema

        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x), return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def _validate(cls, v, _info):
        """Validate and convert value to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")


# ============================================================================
# POINT TRANSACTION MODEL
# ============================================================================

class PointTransaction(BaseModel):
    """
    Individual point transaction record.

    Tracks a single instance of points being awarded for an action.
    """
    action: str = Field(
        ...,
        description="Action type (attend_service, volunteer_hour, bring_visitor, etc.)"
    )
    points: int = Field(
        ...,
        ge=0,
        description="Points awarded"
    )
    date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When points were awarded"
    )
    reference_id: Optional[PyObjectId] = Field(
        None,
        description="Reference to related entity (session_attendance_id, donation_id, etc.)"
    )
    reference_type: str = Field(
        ...,
        description="Type of reference: attendance, donation, volunteer, manual"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context about the transaction"
    )


# ============================================================================
# BADGE MODELS
# ============================================================================

class BadgeProgress(BaseModel):
    """
    Progress towards earning a badge.

    Tracks how close a member is to unlocking a specific badge.
    """
    badge_id: str = Field(..., description="Badge identifier")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    current_count: int = Field(..., ge=0, description="Current progress count")
    target_count: int = Field(..., gt=0, description="Target count to unlock badge")


class EarnedBadge(BaseModel):
    """
    Record of a badge that has been earned.

    Represents a badge that a member has successfully unlocked.
    """
    badge_id: str = Field(..., description="Badge identifier")
    earned_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When badge was earned"
    )
    progress: float = Field(default=100.0, description="Progress percentage (always 100)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context about earning (e.g., services_attended: 52)"
    )


# ============================================================================
# GAMIFICATION PROFILE MODEL
# ============================================================================

class GamificationProfile(BaseModel):
    """
    Member gamification profile.

    Central profile tracking all gamification data for a single member including
    points, levels, streaks, badges, and participation in challenges.

    Attributes:
        id: MongoDB document ID
        user_id: Reference to users collection
        organization_id: Reference to organization

        total_points: Lifetime points earned
        current_level: Current level (1-50)
        level_tier: Level tier (bronze, silver, gold, platinum)
        points_to_next_level: Points needed for next level

        current_streak: Consecutive weeks attended
        longest_streak: Best streak ever achieved
        last_attendance_week: ISO week of last attendance (YYYY-Www format)
        streak_freeze_expires: When streak freeze expires (if active)

        badges_earned: List of unlocked badges
        badges_in_progress: List of badges being worked towards

        leaderboard_visible: Whether to show on public leaderboards
        display_name: Name to display on leaderboards

        total_services_attended: Count of all service attendances
        total_volunteer_hours: Total volunteer time
        total_donations_count: Number of donations made
        visitors_brought: Count of visitors invited

        points_history: Full transaction history
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
        last_activity: Last gamification activity
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(..., description="Reference to users collection")
    organization_id: PyObjectId = Field(..., description="Reference to organization")

    # Points & Levels
    total_points: int = Field(default=0, ge=0, description="Lifetime points earned")
    current_level: int = Field(default=1, ge=1, le=50, description="Current level (1-50)")
    level_tier: str = Field(
        default="bronze",
        description="Level tier: bronze, silver, gold, platinum"
    )
    points_to_next_level: int = Field(
        default=100,
        ge=0,
        description="Points needed to reach next level"
    )

    # Streaks
    current_streak: int = Field(default=0, ge=0, description="Consecutive weeks attended")
    longest_streak: int = Field(default=0, ge=0, description="Best streak ever")
    last_attendance_week: Optional[str] = Field(
        None,
        description="ISO week of last attendance (YYYY-Www format, e.g., 2025-W49)"
    )
    streak_freeze_expires: Optional[datetime] = Field(
        None,
        description="When streak freeze expires (None if not active)"
    )
    streak_milestones_reached: List[int] = Field(
        default_factory=list,
        description="Streak milestones achieved (e.g., [4, 8, 13])"
    )

    # Badges
    badges_earned: List[EarnedBadge] = Field(
        default_factory=list,
        description="Badges that have been unlocked"
    )
    badges_in_progress: List[BadgeProgress] = Field(
        default_factory=list,
        description="Badges being worked towards"
    )

    # Leaderboard Settings
    leaderboard_visible: bool = Field(
        default=True,
        description="Whether to appear on public leaderboards"
    )
    display_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Name to display on leaderboards (e.g., 'John D.')"
    )

    # Statistics
    total_services_attended: int = Field(default=0, ge=0, description="All-time service count")
    total_volunteer_hours: float = Field(default=0.0, ge=0, description="Total volunteer time")
    total_donations_count: int = Field(default=0, ge=0, description="Number of donations")
    visitors_brought: int = Field(default=0, ge=0, description="Visitors invited")

    # Transaction History
    points_history: List[PointTransaction] = Field(
        default_factory=list,
        description="Full point transaction log"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "user_id": "674e9a2b3f1234567890abcd",
                "organization_id": "674e9a2b3f1234567890abce",
                "total_points": 530,
                "current_level": 13,
                "level_tier": "silver",
                "points_to_next_level": 170,
                "current_streak": 7,
                "longest_streak": 15,
                "last_attendance_week": "2025-W49",
                "streak_freeze_expires": None,
                "badges_earned": [
                    {
                        "badge_id": "early_bird",
                        "earned_at": "2025-11-15T10:30:00",
                        "progress": 100,
                        "metadata": {"services_attended": 10}
                    }
                ],
                "leaderboard_visible": True,
                "display_name": "John D.",
                "total_services_attended": 42
            }
        }

    @field_validator("level_tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """Validate level tier."""
        valid_tiers = ["bronze", "silver", "gold", "platinum"]
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier: {v}. Must be one of {valid_tiers}")
        return v


# ============================================================================
# BADGE DEFINITION MODEL
# ============================================================================

class GamificationBadge(BaseModel):
    """
    Badge definition.

    Defines the requirements and metadata for a specific badge achievement.

    Attributes:
        id: MongoDB document ID
        badge_id: Unique identifier (e.g., "early_bird", "faithful")
        name: Display name (e.g., "Early Bird", "Faithful")
        description: What the badge represents
        category: Badge category (attendance, engagement, special)
        icon_url: URL to badge icon image (optional)
        icon_emoji: Emoji representation (e.g., "🐦", "🏆")

        requirement_type: How badge is earned (count, streak, event, milestone, special)
        requirement_field: Which stat to check (total_services_attended, current_streak, etc.)
        requirement_value: Target value to reach

        points_reward: Points awarded when badge is earned
        tier: Badge tier (bronze, silver, gold, platinum)

        is_active: Whether badge can currently be earned
        is_hidden: Secret badge (not visible until earned)
        order: Sort order for display

        organization_id: Organization-specific badge (None = global)
        created_at: Badge creation timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    badge_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique identifier (e.g., 'early_bird')"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name (e.g., 'Early Bird')"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="What the badge represents"
    )
    category: str = Field(
        ...,
        description="Category: attendance, engagement, or special"
    )
    icon_url: Optional[str] = Field(None, description="URL to badge icon image")
    icon_emoji: str = Field(..., min_length=1, max_length=10, description="Emoji (e.g., '🐦')")

    # Requirements
    requirement_type: str = Field(
        ...,
        description="Type: count, streak, event, milestone, or special"
    )
    requirement_field: Optional[str] = Field(
        None,
        description="Field to check (e.g., 'total_services_attended', 'current_streak')"
    )
    requirement_value: Optional[int] = Field(
        None,
        ge=1,
        description="Target value to reach"
    )

    # Rewards
    points_reward: int = Field(..., ge=0, description="Points awarded when earned")
    tier: str = Field(
        default="bronze",
        description="Tier: bronze, silver, gold, or platinum"
    )

    # Visibility
    is_active: bool = Field(default=True, description="Whether badge can be earned")
    is_hidden: bool = Field(default=False, description="Secret badge (hidden until earned)")
    order: int = Field(default=0, description="Display sort order")

    # Organization
    organization_id: Optional[PyObjectId] = Field(
        None,
        description="Organization-specific badge (None = global)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate badge category."""
        valid_categories = ["attendance", "engagement", "special"]
        if v not in valid_categories:
            raise ValueError(f"Invalid category: {v}. Must be one of {valid_categories}")
        return v

    @field_validator("requirement_type")
    @classmethod
    def validate_requirement_type(cls, v: str) -> str:
        """Validate requirement type."""
        valid_types = ["count", "streak", "event", "milestone", "special"]
        if v not in valid_types:
            raise ValueError(f"Invalid requirement_type: {v}. Must be one of {valid_types}")
        return v


# ============================================================================
# CHALLENGE ENUMS
# ============================================================================

class ChallengeStatus(str, Enum):
    """Challenge status enum."""
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"


class ChallengeType(str, Enum):
    """Challenge type enum."""
    INDIVIDUAL = "individual"
    TEAM = "team"
    CELL_GROUP = "cell_group"


# ============================================================================
# CHALLENGE MODELS
# ============================================================================

class ChallengeParticipant(BaseModel):
    """
    Individual participant in a challenge.

    Tracks one member's progress in a specific challenge.
    """
    user_id: PyObjectId
    current_progress: int = Field(default=0, ge=0, description="Current progress count")
    completed: bool = Field(default=False, description="Whether challenge is completed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    team_name: Optional[str] = Field(None, description="Team name for team challenges")
    rewards_claimed: bool = Field(default=False, description="Whether rewards have been claimed")
    rewards_claimed_at: Optional[datetime] = Field(None, description="When rewards were claimed")


class ChallengeGroupRanking(BaseModel):
    """
    Cell group or branch ranking in a challenge.

    Tracks team performance in group challenges.
    """
    group_id: PyObjectId = Field(..., description="Cell group ID or branch ID")
    group_name: str = Field(..., description="Group display name")
    total_points: int = Field(default=0, ge=0, description="Combined points earned")
    members_completed: int = Field(default=0, ge=0, description="Number who completed")
    active_members: int = Field(default=0, ge=0, description="Total participating members")


class GamificationChallenge(BaseModel):
    """
    Time-bound gamification challenge.

    Represents a competition or goal that members can participate in for
    a limited time period (e.g., "21-Day Commitment Challenge").

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to organization
        name: Challenge name
        description: What the challenge involves
        challenge_type: Type (individual, cell_group, or branch)

        start_date: When challenge begins
        end_date: When challenge ends
        is_active: Whether challenge is currently active

        goal_type: What to accomplish (attendance, volunteer, visitors, custom)
        goal_target: Target value to achieve
        goal_unit: Unit of measurement (weeks, services, hours, count)

        points_reward: Points awarded on completion
        badge_reward_id: Optional badge to award

        participants: List of individual participants
        group_leaderboard: Rankings for group challenges

        created_by: User who created the challenge
        created_at: Challenge creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    challenge_type: str = Field(
        ...,
        description="Type: individual, cell_group, or branch"
    )

    # Timeframe
    start_date: datetime
    end_date: datetime
    status: str = Field(default="upcoming", description="Status: upcoming, active, completed")
    completed_at: Optional[datetime] = Field(None, description="When challenge was completed")

    # Goals
    goal_type: str = Field(
        ...,
        description="Type: attendance, volunteer, visitors, or custom"
    )
    goal_target: int = Field(..., gt=0, description="Target value to achieve")
    goal_unit: str = Field(
        default="count",
        description="Unit: weeks, services, hours, or count"
    )

    # Rewards
    points_reward: int = Field(default=0, ge=0, description="Points for completion")
    badge_reward: Optional[str] = Field(None, description="Badge ID to award")

    # Participants
    participants: List[ChallengeParticipant] = Field(default_factory=list)
    group_leaderboard: List[ChallengeGroupRanking] = Field(default_factory=list)
    max_participants: Optional[int] = Field(None, description="Maximum number of participants")
    is_public: bool = Field(default=True, description="Whether challenge is publicly visible")

    # Metadata
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}

    @field_validator("challenge_type")
    @classmethod
    def validate_challenge_type(cls, v: str) -> str:
        """Validate challenge type."""
        valid_types = ["individual", "cell_group", "branch"]
        if v not in valid_types:
            raise ValueError(f"Invalid challenge_type: {v}. Must be one of {valid_types}")
        return v


# ============================================================================
# LEADERBOARD MODELS
# ============================================================================

class LeaderboardEntry(BaseModel):
    """
    Individual entry on a leaderboard.

    Represents one member's rank and stats on a leaderboard.
    """
    rank: int = Field(..., ge=1, description="Current rank position")
    user_id: PyObjectId
    display_name: str = Field(..., description="Name to display")
    points: int = Field(..., ge=0, description="Points for this period")
    level: int = Field(..., ge=1, le=50, description="Current level")
    level_tier: str = Field(..., description="Level tier")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    change: int = Field(default=0, description="Position change from last period")


class CellGroupRanking(BaseModel):
    """
    Cell group ranking entry.

    Tracks a cell group's combined performance on the leaderboard.
    """
    rank: int = Field(..., ge=1)
    cell_group_id: PyObjectId
    cell_group_name: str
    total_points: int = Field(..., ge=0, description="Combined points")
    active_members: int = Field(..., ge=0, description="Active participants")
    avg_points_per_member: float = Field(..., ge=0, description="Average points")


class BranchRanking(BaseModel):
    """
    Branch ranking entry.

    Tracks a branch's combined performance on the leaderboard.
    """
    rank: int = Field(..., ge=1)
    branch_id: PyObjectId
    branch_name: str
    total_points: int = Field(..., ge=0, description="Combined points")
    active_members: int = Field(..., ge=0, description="Active participants")


class GamificationLeaderboard(BaseModel):
    """
    Pre-calculated leaderboard snapshot.

    Cached leaderboard rankings to improve performance. Recalculated periodically
    (every 30 minutes) and stored with TTL expiry.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to organization
        leaderboard_type: Type (weekly, monthly, all_time, or streak)
        period: Time period identifier (e.g., "2025-W49", "2025-12", "all-time")

        rankings: Individual member rankings
        cell_group_rankings: Cell group rankings
        branch_rankings: Branch rankings

        calculated_at: When leaderboard was calculated
        expires_at: When cached data expires (TTL)
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId
    leaderboard_type: str = Field(
        ...,
        description="Type: weekly, monthly, all_time, or streak"
    )
    period: str = Field(
        ...,
        description="Period identifier (ISO week/month or 'all-time')"
    )

    # Rankings
    rankings: List[LeaderboardEntry] = Field(default_factory=list)
    cell_group_rankings: List[CellGroupRanking] = Field(default_factory=list)
    branch_rankings: List[BranchRanking] = Field(default_factory=list)

    # Cache metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        ...,
        description="When cached data expires (30-60 min from calculation)"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}

    @field_validator("leaderboard_type")
    @classmethod
    def validate_leaderboard_type(cls, v: str) -> str:
        """Validate leaderboard type."""
        valid_types = ["weekly", "monthly", "all_time", "streak"]
        if v not in valid_types:
            raise ValueError(f"Invalid leaderboard_type: {v}. Must be one of {valid_types}")
        return v

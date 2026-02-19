"""
Gamification API Routes.

Provides endpoints for points, levels, streaks, badges, and leaderboards to
encourage member engagement and consistent attendance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.models.user import User
from app.dependencies import get_current_user, require_organization_access
from app.services.gamification_service import get_gamification_service
from app.services.gamification_challenges_service import get_gamification_challenges_service
from apps.shared.dependencies import require_organization_admin_role

router = APIRouter(prefix="/gamification", tags=["gamification"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UpdatePreferencesRequest(BaseModel):
    """Request model for updating gamification preferences."""

    leaderboard_visible: Optional[bool] = None
    display_name: Optional[str] = Field(None, max_length=50)
    notification_preferences: Optional[dict] = None


class ProfileResponse(BaseModel):
    """Gamification profile response model."""

    user_id: str
    total_points: int
    current_level: int
    level_tier: str
    points_to_next_level: int
    current_streak: int
    longest_streak: int
    badges_earned_count: int
    badges_earned: List[dict]
    total_services_attended: int
    total_volunteer_hours: float
    total_donations_count: int
    visitors_brought: int
    leaderboard_visible: bool
    created_at: datetime
    updated_at: datetime


class BadgeResponse(BaseModel):
    """Badge definition response model."""

    badge_id: str
    name: str
    description: str
    category: str
    icon_emoji: str
    requirement_type: str
    requirement_value: int
    points_reward: int
    tier: str


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry."""

    rank: int
    user_id: str
    display_name: str
    total_points: int
    current_level: int
    level_tier: str
    current_streak: int
    badges_count: int
    is_current_user: bool = False


# ============================================================================
# PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile", response_model=ProfileResponse)
async def get_my_profile(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's gamification profile.

    Returns complete profile with points, level, streaks, and badges.

    Returns:
        Gamification profile data

    Example Response:
        {
            "user_id": "...",
            "total_points": 530,
            "current_level": 13,
            "level_tier": "silver",
            "points_to_next_level": 170,
            "current_streak": 7,
            "longest_streak": 12,
            "badges_earned_count": 5,
            "badges_earned": [...]
        }
    """
    gamification_service = get_gamification_service(db)

    profile = await gamification_service.get_profile_summary(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id)
    )

    return profile


@router.get("/points-history")
async def get_points_history(
    limit: int = Query(50, ge=1, le=500, description="Maximum entries to return"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get points transaction history for current user.

    Query Parameters:
        limit: Maximum number of entries (1-500)

    Returns:
        List of point transactions

    Example Response:
        [
            {
                "action": "attend_service",
                "points": 10,
                "date": "2025-12-09T08:15:00Z",
                "reference_id": "...",
                "reference_type": "attendance",
                "metadata": {"service_type": "sunday_morning"}
            }
        ]
    """
    gamification_service = get_gamification_service(db)

    history = await gamification_service.get_points_history(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id),
        limit=limit
    )

    return {"history": history, "count": len(history)}


@router.post("/preferences")
async def update_preferences(
    request: UpdatePreferencesRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Update gamification preferences.

    Request Body:
        {
            "leaderboard_visible": true,
            "display_name": "John D.",
            "notification_preferences": {...}
        }

    Returns:
        Success message
    """
    # Build update document
    update_doc = {"$set": {"updated_at": datetime.utcnow()}}

    if request.leaderboard_visible is not None:
        update_doc["$set"]["leaderboard_visible"] = request.leaderboard_visible

    if request.display_name is not None:
        update_doc["$set"]["display_name"] = request.display_name

    if request.notification_preferences is not None:
        update_doc["$set"]["notification_preferences"] = request.notification_preferences

    # Update profile
    result = await db.gamification_profiles.update_one(
        {
            "user_id": current_user.id,
            "organization_id": current_user.organization_id
        },
        update_doc
    )

    if result.matched_count == 0:
        # Create profile if doesn't exist
        gamification_service = get_gamification_service(db)
        await gamification_service.get_or_create_profile(
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id)
        )
        # Try update again
        await db.gamification_profiles.update_one(
            {
                "user_id": current_user.id,
                "organization_id": current_user.organization_id
            },
            update_doc
        )

    return {"success": True, "message": "Preferences updated successfully"}


# ============================================================================
# BADGE ENDPOINTS
# ============================================================================

@router.get("/badges", response_model=List[BadgeResponse])
async def get_all_badges(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get all available badges.

    Query Parameters:
        category: Filter by badge category (optional)

    Returns:
        List of badge definitions
    """
    query_filter = {"organization_id": current_user.organization_id}

    if category:
        query_filter["category"] = category

    cursor = db.gamification_badges.find(query_filter).sort("requirement_value", 1)
    badges = await cursor.to_list(length=None)

    # Convert ObjectIds to strings
    for badge in badges:
        badge["_id"] = str(badge["_id"])
        badge["organization_id"] = str(badge["organization_id"])

    return badges


@router.get("/badges/{badge_id}")
async def get_badge_details(
    badge_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get details for a specific badge.

    Path Parameters:
        badge_id: Badge identifier

    Returns:
        Badge details

    Raises:
        404: Badge not found
    """
    badge = await db.gamification_badges.find_one({
        "badge_id": badge_id,
        "organization_id": current_user.organization_id
    })

    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    # Convert ObjectIds
    badge["_id"] = str(badge["_id"])
    badge["organization_id"] = str(badge["organization_id"])

    return badge


@router.get("/my-badges")
async def get_my_badges(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's earned badges.

    Returns:
        {
            "earned": [...],
            "in_progress": [...],
            "locked": [...]
        }
    """
    gamification_service = get_gamification_service(db)

    # Get profile
    profile = await gamification_service.get_or_create_profile(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id)
    )

    # Get all badges
    cursor = db.gamification_badges.find({
        "organization_id": current_user.organization_id
    })
    all_badges = await cursor.to_list(length=None)

    earned = profile.get("badges_earned", [])
    earned_ids = [b["badge_id"] for b in earned]

    # Categorize badges
    in_progress = []
    locked = []

    for badge in all_badges:
        if badge["badge_id"] not in earned_ids:
            # Check progress
            req_field = badge.get("requirement_field")
            req_value = badge.get("requirement_value")
            current_value = profile.get(req_field, 0)

            if current_value > 0 and current_value < req_value:
                # In progress
                in_progress.append({
                    "badge_id": badge["badge_id"],
                    "name": badge["name"],
                    "description": badge["description"],
                    "icon_emoji": badge.get("icon_emoji", "🏆"),
                    "progress": current_value,
                    "target": req_value,
                    "percentage": round((current_value / req_value) * 100, 1)
                })
            else:
                # Locked
                locked.append({
                    "badge_id": badge["badge_id"],
                    "name": badge["name"],
                    "description": badge["description"],
                    "icon_emoji": badge.get("icon_emoji", "🏆"),
                    "requirement": f"{req_value} {req_field.replace('_', ' ')}"
                })

    return {
        "earned": earned,
        "in_progress": in_progress,
        "locked": locked
    }


# ============================================================================
# LEADERBOARD ENDPOINTS
# ============================================================================

@router.get("/leaderboard/{leaderboard_type}")
async def get_leaderboard(
    leaderboard_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get leaderboard rankings.

    Path Parameters:
        leaderboard_type: Type of leaderboard (weekly, monthly, all_time, streak)

    Query Parameters:
        skip: Pagination offset
        limit: Maximum results

    Returns:
        {
            "rankings": [...],
            "current_user_rank": {...},
            "total_participants": int
        }
    """
    # Determine sort field
    sort_field_map = {
        "all_time": "total_points",
        "weekly": "total_points",  # TODO: Implement weekly points
        "monthly": "total_points",  # TODO: Implement monthly points
        "streak": "current_streak"
    }

    sort_field = sort_field_map.get(leaderboard_type, "total_points")

    # Get profiles (only visible ones)
    cursor = (
        db.gamification_profiles
        .find({
            "organization_id": current_user.organization_id,
            "leaderboard_visible": True
        })
        .sort(sort_field, -1)
        .skip(skip)
        .limit(limit)
    )

    profiles = await cursor.to_list(length=limit)

    # Get total count
    total_count = await db.gamification_profiles.count_documents({
        "organization_id": current_user.organization_id,
        "leaderboard_visible": True
    })

    # Format rankings
    rankings = []
    current_user_rank = None

    for idx, profile in enumerate(profiles, start=skip + 1):
        # Get user info
        user_doc = await db.users.find_one({"_id": profile["user_id"]})

        display_name = profile.get("display_name")
        if not display_name and user_doc:
            display_name = user_doc.get("full_name", "Member")

        entry = LeaderboardEntry(
            rank=idx,
            user_id=str(profile["user_id"]),
            display_name=display_name or "Member",
            total_points=profile["total_points"],
            current_level=profile["current_level"],
            level_tier=profile["level_tier"],
            current_streak=profile.get("current_streak", 0),
            badges_count=len(profile.get("badges_earned", [])),
            is_current_user=(profile["user_id"] == current_user.id)
        )

        rankings.append(entry)

        if profile["user_id"] == current_user.id:
            current_user_rank = entry

    # If current user not in results, find their rank
    if not current_user_rank:
        current_profile = await db.gamification_profiles.find_one({
            "user_id": current_user.id,
            "organization_id": current_user.organization_id
        })

        if current_profile:
            # Count how many profiles have higher score
            rank = await db.gamification_profiles.count_documents({
                "organization_id": current_user.organization_id,
                "leaderboard_visible": True,
                sort_field: {"$gt": current_profile.get(sort_field, 0)}
            }) + 1

            user_doc = await db.users.find_one({"_id": current_user.id})

            current_user_rank = LeaderboardEntry(
                rank=rank,
                user_id=str(current_user.id),
                display_name=current_profile.get("display_name") or user_doc.get("full_name", "You"),
                total_points=current_profile["total_points"],
                current_level=current_profile["current_level"],
                level_tier=current_profile["level_tier"],
                current_streak=current_profile.get("current_streak", 0),
                badges_count=len(current_profile.get("badges_earned", [])),
                is_current_user=True
            )

    return {
        "rankings": rankings,
        "current_user_rank": current_user_rank,
        "total_participants": total_count,
        "leaderboard_type": leaderboard_type
    }


@router.get("/my-rank")
async def get_my_rank(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's rank on all leaderboards.

    Returns:
        {
            "all_time_rank": int,
            "streak_rank": int,
            "total_participants": int
        }
    """
    profile = await db.gamification_profiles.find_one({
        "user_id": current_user.id,
        "organization_id": current_user.organization_id
    })

    if not profile:
        return {
            "all_time_rank": None,
            "streak_rank": None,
            "total_participants": 0
        }

    # Get all-time rank
    all_time_rank = await db.gamification_profiles.count_documents({
        "organization_id": current_user.organization_id,
        "leaderboard_visible": True,
        "total_points": {"$gt": profile["total_points"]}
    }) + 1

    # Get streak rank
    streak_rank = await db.gamification_profiles.count_documents({
        "organization_id": current_user.organization_id,
        "leaderboard_visible": True,
        "current_streak": {"$gt": profile.get("current_streak", 0)}
    }) + 1

    # Get total participants
    total_participants = await db.gamification_profiles.count_documents({
        "organization_id": current_user.organization_id,
        "leaderboard_visible": True
    })

    return {
        "all_time_rank": all_time_rank,
        "streak_rank": streak_rank,
        "total_participants": total_participants
    }

# ============================================================================
# CHALLENGES ENDPOINTS
# ============================================================================

class CreateChallengeRequest(BaseModel):
    """Request model for creating a challenge."""
    
    name: str = Field(..., max_length=100)
    description: str = Field(default="")
    challenge_type: str = Field(default="individual")  # individual, team, cell_group
    start_date: datetime
    end_date: datetime
    goal_type: str  # attendance, donations, volunteering, visitors
    goal_target: int = Field(..., gt=0)
    goal_unit: str = Field(default="count")
    points_reward: int = Field(default=0, ge=0)
    badge_reward: Optional[str] = None
    max_participants: Optional[int] = Field(None, gt=0)
    is_public: bool = Field(default=True)


class JoinChallengeRequest(BaseModel):
    """Request model for joining a challenge."""
    
    team_name: Optional[str] = Field(None, max_length=50)


@router.post("/challenges", status_code=201)
async def create_challenge(
    request: CreateChallengeRequest,
    organization_id: str = Depends(require_organization_admin_role),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new challenge (admin only).
    
    Args:
        request: Challenge details
        organization_id: Organization ID (from admin check)
        current_user: Current user (admin)
        db: Database connection
        
    Returns:
        Created challenge
    """
    challenges_service = get_gamification_challenges_service(db)
    
    challenge = await challenges_service.create_challenge(
        organization_id=organization_id,
        challenge_data=request.model_dump(),
        created_by=str(current_user.id)
    )
    
    return challenge


@router.get("/challenges")
async def list_challenges(
    organization_id: str = Depends(require_organization_access),
    status: Optional[str] = Query(None),
    challenge_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all challenges for organization.
    
    Args:
        organization_id: Organization ID
        status: Filter by status (upcoming, active, completed)
        challenge_type: Filter by type (individual, team, cell_group)
        page: Page number
        page_size: Items per page
        
    Returns:
        Paginated list of challenges
    """
    from app.models.gamification import ChallengeStatus, ChallengeType
    
    challenges_service = get_gamification_challenges_service(db)
    
    # Convert string to enum if provided
    status_enum = None
    if status:
        try:
            status_enum = ChallengeStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    type_enum = None
    if challenge_type:
        try:
            type_enum = ChallengeType(challenge_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid challenge type: {challenge_type}")
    
    result = await challenges_service.list_challenges(
        organization_id=organization_id,
        status=status_enum,
        challenge_type=type_enum,
        page=page,
        page_size=page_size
    )
    
    return result


@router.get("/challenges/{challenge_id}")
async def get_challenge(
    challenge_id: str,
    organization_id: str = Depends(require_organization_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get challenge details by ID.
    
    Args:
        challenge_id: Challenge ID
        organization_id: Organization ID
        
    Returns:
        Challenge details with participant progress
    """
    challenges_service = get_gamification_challenges_service(db)
    
    challenge = await challenges_service.get_challenge(challenge_id)
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Verify organization access
    if str(challenge.organization_id) != organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return challenge


@router.post("/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: str,
    request: JoinChallengeRequest,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Join a challenge.
    
    Args:
        challenge_id: Challenge ID
        request: Join request (team name if team challenge)
        organization_id: Organization ID
        current_user: Current user
        
    Returns:
        Updated challenge with user added to participants
    """
    challenges_service = get_gamification_challenges_service(db)
    
    try:
        challenge = await challenges_service.join_challenge(
            challenge_id=challenge_id,
            user_id=str(current_user.id),
            team_name=request.team_name
        )
        
        return {
            "success": True,
            "message": f"Successfully joined {challenge.name}",
            "challenge": challenge
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/challenges/{challenge_id}/leave")
async def leave_challenge(
    challenge_id: str,
    organization_id: str = Depends(require_organization_access),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Leave a challenge (only if not completed).
    
    Args:
        challenge_id: Challenge ID
        organization_id: Organization ID
        current_user: Current user
        
    Returns:
        Success message
    """
    challenges_service = get_gamification_challenges_service(db)
    
    try:
        await challenges_service.leave_challenge(
            challenge_id=challenge_id,
            user_id=str(current_user.id)
        )
        
        return {
            "success": True,
            "message": "Successfully left challenge"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-challenges")
async def get_my_challenges(
    organization_id: str = Depends(require_organization_access),
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get all challenges current user is participating in.
    
    Args:
        organization_id: Organization ID
        active_only: Only return active challenges
        current_user: Current user
        
    Returns:
        List of challenges user is participating in
    """
    challenges_service = get_gamification_challenges_service(db)
    
    challenges = await challenges_service.get_user_challenges(
        user_id=str(current_user.id),
        organization_id=organization_id,
        active_only=active_only
    )
    
    return {"challenges": challenges, "total": len(challenges)}


# ============================================================================
# ADMIN ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/admin/analytics")
async def get_gamification_analytics(
    organization_id: str = Depends(require_organization_admin_role),
    period: str = Query("30d", description="Period: 7d, 30d, 90d"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get comprehensive gamification analytics (admin only).
    
    Returns system-wide statistics including:
    - User engagement metrics
    - Point distribution
    - Badge statistics
    - Challenge performance
    - Streak analytics
    - Leaderboard participation
    
    Args:
        organization_id: Organization ID (from admin check)
        period: Time period for analysis
        db: Database connection
        
    Returns:
        Comprehensive analytics data
    """
    from datetime import timedelta
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:  # default 30d
        start_date = now - timedelta(days=30)
    
    org_id = ObjectId(organization_id)
    
    # Overview statistics
    total_profiles = await db.gamification_profiles.count_documents({"organization_id": org_id})
    
    profiles_cursor = db.gamification_profiles.find({"organization_id": org_id})
    profiles = await profiles_cursor.to_list(length=None)
    
    total_points = sum(p.get("total_points", 0) for p in profiles)
    avg_points = total_points / total_profiles if total_profiles > 0 else 0
    avg_level = sum(p.get("current_level", 1) for p in profiles) / total_profiles if total_profiles > 0 else 1
    
    total_badges_earned = sum(len(p.get("badges_earned", [])) for p in profiles)
    
    # Count total check-ins (attendance records)
    total_check_ins = await db.session_attendance.count_documents({
        "organization_id": org_id,
        "checked_in_at": {"$gte": start_date}
    })
    
    # Active challenges
    active_challenges = await db.gamification_challenges.count_documents({
        "organization_id": org_id,
        "status": "active"
    })
    
    # Level distribution
    level_dist = {"bronze": 0, "silver": 0, "gold": 0, "platinum": 0}
    for p in profiles:
        tier = p.get("level_tier", "bronze")
        level_dist[tier] = level_dist.get(tier, 0) + 1
    
    level_distribution = [
        {
            "tier": tier,
            "count": count,
            "percentage": (count / total_profiles * 100) if total_profiles > 0 else 0
        }
        for tier, count in level_dist.items()
    ]
    
    # Badge statistics
    badge_counts = {}
    for p in profiles:
        for badge in p.get("badges_earned", []):
            badge_id = badge.get("badge_id")
            if badge_id:
                if badge_id not in badge_counts:
                    badge_counts[badge_id] = {
                        "badge_id": badge_id,
                        "name": badge.get("name", "Unknown"),
                        "icon_emoji": badge.get("icon_emoji", "🏆"),
                        "earned_count": 0
                    }
                badge_counts[badge_id]["earned_count"] += 1
    
    most_earned_badges = sorted(badge_counts.values(), key=lambda x: x["earned_count"], reverse=True)[:5]
    
    # Streak statistics
    users_with_streak = sum(1 for p in profiles if p.get("current_streak", 0) > 0)
    avg_streak = sum(p.get("current_streak", 0) for p in profiles) / total_profiles if total_profiles > 0 else 0
    longest_streak = max((p.get("current_streak", 0) for p in profiles), default=0)
    users_4plus = sum(1 for p in profiles if p.get("current_streak", 0) >= 4)
    
    # Challenge statistics
    all_challenges = await db.gamification_challenges.find({"organization_id": org_id}).to_list(length=None)
    total_challenges = len(all_challenges)
    completed_challenges = [c for c in all_challenges if c.get("status") == "completed"]
    
    total_participants = sum(len(c.get("participants", [])) for c in all_challenges)
    avg_participants = total_participants / total_challenges if total_challenges > 0 else 0
    
    completed_count = sum(
        sum(1 for p in c.get("participants", []) if p.get("completed"))
        for c in completed_challenges
    )
    total_participant_slots = sum(len(c.get("participants", [])) for c in completed_challenges)
    completion_rate = (completed_count / total_participant_slots * 100) if total_participant_slots > 0 else 0
    
    # Leaderboard stats
    visible_profiles = sum(1 for p in profiles if p.get("leaderboard_visible", True))
    hidden_profiles = total_profiles - visible_profiles
    opt_in_rate = (visible_profiles / total_profiles * 100) if total_profiles > 0 else 0
    
    return {
        "overview": {
            "total_active_users": total_profiles,
            "total_points_awarded": total_points,
            "average_points_per_user": avg_points,
            "average_level": avg_level,
            "total_badges_earned": total_badges_earned,
            "active_challenges": active_challenges,
            "total_check_ins": total_check_ins
        },
        "levels": {
            "level_distribution": level_distribution
        },
        "badges": {
            "most_earned": most_earned_badges,
            "total_badges": len(badge_counts),
            "average_per_user": total_badges_earned / total_profiles if total_profiles > 0 else 0
        },
        "challenges": {
            "total_created": total_challenges,
            "active_count": active_challenges,
            "completion_rate": completion_rate,
            "average_participants": avg_participants
        },
        "streaks": {
            "users_with_streak": users_with_streak,
            "average_streak": avg_streak,
            "longest_current_streak": longest_streak,
            "users_4plus_weeks": users_4plus
        },
        "leaderboard": {
            "opt_in_rate": opt_in_rate,
            "total_visible": visible_profiles,
            "total_hidden": hidden_profiles
        },
        "trends": {
            "points_last_7_days": [],  # TODO: Implement time-series data
            "check_ins_last_7_days": []
        }
    }

"""
Proximity-Based Auto Check-In API Routes.

Provides endpoints for geolocation-based automatic check-in to church services
and events when members are near branch locations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_database
from app.models.user import User
from app.api.dependencies import get_current_user, require_organization_access, get_optional_organization_id
from app.services.proximity_checkin_service import ProximityCheckinService

router = APIRouter(prefix="/proximity-checkin", tags=["proximity-checkin"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class NearbyBranchesRequest(BaseModel):
    """Request model for finding nearby branches."""

    latitude: float = Field(..., ge=-90, le=90, description="User's GPS latitude")
    longitude: float = Field(..., ge=-180, le=180, description="User's GPS longitude")
    max_distance: int = Field(
        default=5000,
        ge=100,
        le=50000,
        description="Maximum search radius in meters"
    )
    auto_checkin_only: bool = Field(
        default=False,
        description="Only return branches with auto check-in enabled"
    )


class AutoCheckinRequest(BaseModel):
    """Request model for automatic check-in."""

    latitude: float = Field(..., ge=-90, le=90, description="User's GPS latitude")
    longitude: float = Field(..., ge=-180, le=180, description="User's GPS longitude")
    accuracy: float = Field(..., ge=0, le=1000, description="GPS accuracy in meters")
    branch_id: Optional[str] = Field(
        None,
        description="Branch ID (auto-detected if omitted)"
    )
    service_type: Optional[str] = Field(
        None,
        description="Service type (auto-detected if omitted)"
    )


class ActiveService(BaseModel):
    """Active service information."""

    service_id: Optional[str] = None
    service_type: str
    start_time: str
    end_time: str
    can_checkin: bool
    reason: Optional[str] = None


class NearbyBranch(BaseModel):
    """Nearby branch response model."""

    branch_id: str
    name: str
    location: str
    distance: float
    active_service: Optional[ActiveService] = None


class AutoCheckinResponse(BaseModel):
    """Auto check-in response model."""

    success: bool
    message: str
    attendance_id: Optional[str] = None
    branch: Optional[str] = None
    service: Optional[str] = None
    distance: Optional[float] = None

    # Gamification data (placeholders for Phase 2.3+)
    points_awarded: int = 0
    level_up: bool = False
    new_level: Optional[int] = None
    badges_unlocked: List[str] = []
    streak_updated: bool = False
    current_streak: int = 0


class CheckinStatus(BaseModel):
    """Check-in status response model."""

    checked_in_today: bool
    last_checkin: Optional[dict] = None
    can_checkin_again: bool
    next_available_checkin: Optional[datetime] = None
    cooldown_remaining_minutes: Optional[int] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/nearby-branches", response_model=List[NearbyBranch])
async def find_nearby_branches(
    request: NearbyBranchesRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Find church branches near user's current location.

    This endpoint helps members discover which branches are within proximity
    for automatic check-in. It returns branches sorted by distance (nearest first).

    Args:
        request: GPS coordinates and search parameters
        db: Database connection
        current_user: Authenticated user

    Returns:
        List of nearby branches with active service information

    Example Response:
        [
            {
                "branch_id": "674e9a2b3f1234567890abcd",
                "name": "Adenta",
                "location": "Adenta, Greater Accra, Ghana",
                "distance": 342.5,
                "active_service": {
                    "service_type": "sunday_morning",
                    "start_time": "08:00",
                    "end_time": "10:00",
                    "can_checkin": true
                }
            }
        ]
    """
    # Initialize service
    proximity_service = ProximityCheckinService(db)

    # Find nearby branches
    nearby_branches = await proximity_service.find_nearby_branches(
        latitude=request.latitude,
        longitude=request.longitude,
        organization_id=str(current_user.organization_id),
        max_distance=request.max_distance,
        auto_checkin_only=request.auto_checkin_only
    )

    # Format response with active service information
    result = []
    for branch in nearby_branches:
        # Check if service is currently active
        active_service_data = await proximity_service.check_service_active(
            branch_id=str(branch["_id"])
        )

        active_service = None
        if active_service_data:
            # Check if user can check in
            can_checkin, reason = await proximity_service.can_check_in(
                user_id=str(current_user.id),
                branch_id=str(branch["_id"]),
                service_type=active_service_data["type"]
            )

            active_service = ActiveService(
                service_type=active_service_data["type"],
                start_time=active_service_data["start_time"],
                end_time=active_service_data["end_time"],
                can_checkin=can_checkin,
                reason=None if can_checkin else reason
            )

        result.append(NearbyBranch(
            branch_id=str(branch["_id"]),
            name=branch["name"],
            location=branch["location"],
            distance=branch["distance"],
            active_service=active_service
        ))

    return result


@router.post("/nearby-branches/public", response_model=List[NearbyBranch])
async def find_nearby_branches_public(
    request: NearbyBranchesRequest,
    organization_id: str = Depends(get_optional_organization_id),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Find church branches near user's current location (public endpoint).
    
    This endpoint works for both authenticated and unauthenticated users.
    It's designed for PWA users who may not be logged in but have installed the app.

    Args:
        request: GPS coordinates and search parameters
        organization_id: Organization ID (from header or default)
        db: Database connection

    Returns:
        List of nearby branches sorted by distance (nearest first)
    """
    # Initialize service
    proximity_service = ProximityCheckinService(db)

    # Find nearby branches (without requiring auto_checkin_enabled for public endpoint)
    nearby_branches = await proximity_service.find_nearby_branches(
        latitude=request.latitude,
        longitude=request.longitude,
        organization_id=organization_id,
        max_distance=request.max_distance,
        auto_checkin_only=False  # Show all branches for public endpoint
    )

    # Format response (simplified - no active service info for public endpoint)
    result = []
    for branch in nearby_branches:
        result.append(NearbyBranch(
            branch_id=str(branch["_id"]),
            name=branch["name"],
            location=branch["location"],
            distance=branch["distance"],
            active_service=None  # No service info for public endpoint
        ))

    return result


@router.post("/auto-checkin", response_model=AutoCheckinResponse)
async def perform_auto_checkin(
    request: AutoCheckinRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Perform automatic proximity-based check-in.

    This endpoint automatically checks in a member when they are near a branch
    with an active service. It validates proximity, service status, and user
    eligibility before creating the attendance record.

    Args:
        request: GPS coordinates and optional branch/service IDs
        background_tasks: FastAPI background tasks
        db: Database connection
        current_user: Authenticated user

    Returns:
        Check-in result with gamification data

    Raises:
        HTTPException: 400 if check-in validation fails
        HTTPException: 404 if branch/service not found

    Example Response:
        {
            "success": true,
            "message": "Successfully checked in to Sunday Morning Service",
            "attendance_id": "674e9a2b3f1234567890abcd",
            "branch": "Adenta",
            "service": "Sunday Morning Service",
            "distance": 342.5,
            "points_awarded": 10,
            "streak_updated": true,
            "current_streak": 5
        }
    """
    proximity_service = ProximityCheckinService(db)

    # Auto-detect branch if not provided
    branch_id = request.branch_id
    if not branch_id:
        nearby = await proximity_service.find_nearby_branches(
            latitude=request.latitude,
            longitude=request.longitude,
            organization_id=str(current_user.organization_id),
            max_distance=1000,  # 1km for auto-detection
            auto_checkin_only=True
        )

        if not nearby:
            return AutoCheckinResponse(
                success=False,
                message="No branches with auto check-in enabled found nearby"
            )

        # Use nearest branch
        branch_id = str(nearby[0]["_id"])

    # Validate GPS accuracy
    if request.accuracy > 100:
        return AutoCheckinResponse(
            success=False,
            message=f"GPS accuracy too low ({request.accuracy}m). Please try again with better signal."
        )

    # Check if user can check in
    can_checkin, reason = await proximity_service.can_check_in(
        user_id=str(current_user.id),
        branch_id=branch_id,
        service_type=request.service_type
    )

    if not can_checkin:
        return AutoCheckinResponse(
            success=False,
            message=reason or "Unable to check in at this time"
        )

    # Perform auto check-in
    try:
        result = await proximity_service.auto_checkin_user(
            user_id=str(current_user.id),
            branch_id=branch_id,
            latitude=request.latitude,
            longitude=request.longitude,
            accuracy=request.accuracy,
            service_type=request.service_type
        )

        # GAMIFICATION: Award points and update streak in background
        background_tasks.add_task(
            award_proximity_checkin_gamification,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            attendance_id=result["attendance_id"],
            service_type=result["service_type"]
        )

        return AutoCheckinResponse(
            success=True,
            message=f"Successfully checked in to {result['service_type'].replace('_', ' ').title()}",
            attendance_id=result["attendance_id"],
            branch=result["branch_name"],
            service=result["service_type"].replace('_', ' ').title(),
            distance=result["distance"],
            # Gamification data will be populated in Phase 2.3+
            points_awarded=0,
            level_up=False,
            streak_updated=False,
            current_streak=0
        )

    except ValueError as e:
        # Expected validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Check-in failed: {str(e)}"
        )


@router.get("/status", response_model=CheckinStatus)
async def get_checkin_status(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's current check-in status.

    Returns information about today's check-ins and whether the user
    can check in again (based on cooldown period).

    Args:
        db: Database connection
        current_user: Authenticated user

    Returns:
        Check-in status with cooldown information

    Example Response:
        {
            "checked_in_today": true,
            "last_checkin": {
                "service": "Sunday Morning Service",
                "branch": "Adenta",
                "time": "2025-12-09T08:15:00Z",
                "method": "auto_geofence"
            },
            "can_checkin_again": false,
            "next_available_checkin": "2025-12-09T10:15:00Z",
            "cooldown_remaining_minutes": 45
        }
    """
    proximity_service = ProximityCheckinService(db)

    # Get status
    status = await proximity_service.get_checkin_status(
        user_id=str(current_user.id)
    )

    # Calculate cooldown remaining time
    cooldown_minutes = None
    if status["next_available_checkin"]:
        remaining = status["next_available_checkin"] - datetime.utcnow()
        cooldown_minutes = max(0, int(remaining.total_seconds() / 60))

    return CheckinStatus(
        checked_in_today=status["checked_in_today"],
        last_checkin=status["last_checkin"],
        can_checkin_again=status["can_checkin_again"],
        next_available_checkin=status["next_available_checkin"],
        cooldown_remaining_minutes=cooldown_minutes
    )


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.get("/admin/logs", dependencies=[Depends(get_current_user)])
async def get_checkin_logs(
    organization_id: str = Query(..., description="Organization ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    success_only: bool = Query(False, description="Only show successful check-ins"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get auto check-in logs for analytics (admin only).

    Returns all check-in attempts with GPS data, success/failure status,
    and fraud detection flags for administrative review.

    Args:
        organization_id: Organization ID
        start_date: Filter logs from this date
        end_date: Filter logs until this date
        success_only: Only return successful check-ins
        skip: Pagination offset
        limit: Maximum results
        db: Database connection
        current_user: Authenticated user (must be admin)

    Returns:
        List of check-in log entries

    Raises:
        HTTPException: 403 if user is not admin
    """
    # Verify admin access
    if "admin" not in current_user.roles and "universal_admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can view check-in logs"
        )

    # Verify organization access
    await require_organization_access(current_user, organization_id, db)

    # Build query filter
    from bson import ObjectId
    query_filter = {"organization_id": ObjectId(organization_id)}

    if start_date:
        query_filter["created_at"] = {"$gte": start_date}

    if end_date:
        if "created_at" in query_filter:
            query_filter["created_at"]["$lte"] = end_date
        else:
            query_filter["created_at"] = {"$lte": end_date}

    if success_only:
        query_filter["success"] = True

    # Fetch logs
    cursor = (
        db.auto_checkin_logs
        .find(query_filter)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    logs = await cursor.to_list(length=limit)

    # Convert ObjectIds to strings
    for log in logs:
        log["_id"] = str(log["_id"])
        log["user_id"] = str(log["user_id"])
        log["organization_id"] = str(log["organization_id"])
        log["branch_id"] = str(log["branch_id"])
        if log.get("attendance_id"):
            log["attendance_id"] = str(log["attendance_id"])

    return {
        "logs": logs,
        "count": len(logs),
        "skip": skip,
        "limit": limit
    }


@router.get("/admin/analytics", dependencies=[Depends(get_current_user)])
async def get_checkin_analytics(
    organization_id: str = Query(..., description="Organization ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Get auto check-in analytics and statistics (admin only).

    Provides insights into check-in patterns, success rates, and potential
    fraud indicators for administrative monitoring.

    Args:
        organization_id: Organization ID
        days: Number of days to include in analysis
        db: Database connection
        current_user: Authenticated user (must be admin)

    Returns:
        Analytics summary with success rates, fraud flags, etc.

    Raises:
        HTTPException: 403 if user is not admin
    """
    # Verify admin access
    if "admin" not in current_user.roles and "universal_admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can view analytics"
        )

    # Verify organization access
    await require_organization_access(current_user, organization_id, db)

    from bson import ObjectId
    from datetime import timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    # Aggregation pipeline for analytics
    pipeline = [
        {
            "$match": {
                "organization_id": ObjectId(organization_id),
                "created_at": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_attempts": {"$sum": 1},
                "successful": {
                    "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                },
                "failed": {
                    "$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}
                },
                "suspicious_velocity": {
                    "$sum": {"$cond": [{"$eq": ["$suspicious_velocity", True]}, 1, 0]}
                },
                "suspicious_accuracy": {
                    "$sum": {"$cond": [{"$eq": ["$suspicious_accuracy", True]}, 1, 0]}
                },
                "avg_distance": {"$avg": "$distance_to_branch"},
                "avg_accuracy": {"$avg": "$accuracy"}
            }
        }
    ]

    result = await db.auto_checkin_logs.aggregate(pipeline).to_list(length=1)

    if not result:
        return {
            "period_days": days,
            "total_attempts": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0,
            "fraud_flags": 0,
            "avg_distance_meters": 0.0,
            "avg_accuracy_meters": 0.0
        }

    stats = result[0]
    success_rate = (
        (stats["successful"] / stats["total_attempts"] * 100)
        if stats["total_attempts"] > 0
        else 0.0
    )

    fraud_flags = stats["suspicious_velocity"] + stats["suspicious_accuracy"]

    return {
        "period_days": days,
        "total_attempts": stats["total_attempts"],
        "successful": stats["successful"],
        "failed": stats["failed"],
        "success_rate": round(success_rate, 2),
        "fraud_flags": fraud_flags,
        "suspicious_velocity_count": stats["suspicious_velocity"],
        "suspicious_accuracy_count": stats["suspicious_accuracy"],
        "avg_distance_meters": round(stats["avg_distance"] or 0, 2),
        "avg_accuracy_meters": round(stats["avg_accuracy"] or 0, 2)
    }


# ============================================================================
# GAMIFICATION BACKGROUND TASKS
# ============================================================================

async def award_proximity_checkin_gamification(
    user_id: str,
    organization_id: str,
    attendance_id: str,
    service_type: str
):
    """
    Background task to award gamification points for proximity check-in.

    Args:
        user_id: User ID who checked in
        organization_id: Organization ID
        attendance_id: Attendance record ID
        service_type: Type of service
    """
    try:
        from app.services.gamification_service import get_gamification_service
        from app.core.database import get_database
        import logging

        logger = logging.getLogger(__name__)
        db = get_database()
        gamification_service = get_gamification_service(db)

        # Award points for attendance
        points_result = await gamification_service.award_attendance_points(
            user_id=user_id,
            organization_id=organization_id,
            attendance_id=attendance_id,
            service_type=service_type
        )

        logger.info(
            f"[Proximity Check-In] Gamification points awarded: user={user_id}, "
            f"points={points_result['points_awarded']}, "
            f"level_up={points_result['level_up']}"
        )

        # Update attendance streak
        streak_result = await gamification_service.calculate_streak(
            user_id=user_id,
            organization_id=organization_id
        )

        logger.info(
            f"[Proximity Check-In] Streak updated: user={user_id}, "
            f"current_streak={streak_result['current_streak']}"
        )

    except Exception as e:
        # Log error but don't fail the check-in
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Proximity check-in gamification error: {e}", exc_info=True)

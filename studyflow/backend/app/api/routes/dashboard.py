"""
Progress Dashboard API for StudyFlow.

Provides comprehensive progress tracking and analytics for students
and administrators.

Features:
- Module completion tracking
- Assessment scores timeline
- Achievement badges
- Learning streaks
- Personalized recommendations
- Organization-wide analytics (admin)

Author: KasaAI
Created: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole
from app.core.database import MongoDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Require admin for organization-wide stats
require_admin = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


# ============================================================================
# Response Models
# ============================================================================

class ModuleProgress(BaseModel):
    """Progress for a single module."""
    module_number: int
    module_title: str
    status: str  # not_started, in_progress, completed
    score: Optional[float] = None
    time_spent_minutes: float = 0
    questions_asked: int = 0
    assessment_completed: bool = False
    completed_at: Optional[datetime] = None


class Achievement(BaseModel):
    """Achievement badge."""
    id: str
    name: str
    description: str
    icon: str
    earned_at: datetime
    points: int


class OverallProgress(BaseModel):
    """Overall progress summary."""
    modules_completed: int
    total_modules: int
    completion_percentage: float
    assessments_passed: int
    assessments_failed: int
    assessments_pending: int
    average_score: float
    total_time_minutes: float
    total_questions_asked: int


class TimelineData(BaseModel):
    """Timeline information."""
    started_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    days_active: int
    streak_days: int
    longest_streak: int


class DashboardData(BaseModel):
    """Complete dashboard data for a student."""
    # Student info
    student_id: str
    organization_id: str

    # Overall progress
    overall_progress: OverallProgress

    # Module-level progress
    module_progress: List[ModuleProgress]

    # Timeline
    timeline: TimelineData

    # Achievements
    achievements: List[Achievement]
    total_points: int

    # Next steps
    next_module: Optional[str] = None
    recommended_actions: List[str] = Field(default_factory=list)

    # Recent activity
    recent_questions: int = 0
    recent_assessments: int = 0


class OrganizationDashboard(BaseModel):
    """Organization-wide dashboard (admin only)."""
    organization_id: str

    # Summary stats
    total_students: int
    active_students: int
    completed_course: int
    average_completion_rate: float
    average_score: float

    # Time metrics
    average_time_to_complete_days: float
    total_learning_hours: float

    # Module performance
    most_challenging_module: Optional[str] = None
    easiest_module: Optional[str] = None

    # Engagement
    voice_questions_asked: int
    assessments_completed: int
    total_cost: float


# ============================================================================
# Helper Functions
# ============================================================================

async def get_module_progress(
    organization_id: str,
    user_id: str
) -> List[ModuleProgress]:
    """Get progress for all modules."""
    db = MongoDB.get_database()

    # Get all modules for organization
    materials = await db["materials"].find({
        "organization_id": organization_id,
        "subject": "Software Engineering"  # Onboarding modules
    }).sort("metadata.module_number", 1).to_list(None)

    module_progress = []

    for material in materials:
        module_num = material.get("metadata", {}).get("module_number", 0)
        if module_num == 0:
            continue

        # Check if there are questions asked on this module
        questions = await db["questions"].count_documents({
            "student_id": user_id,
            "subject": material["subject"],
            "metadata.module_number": module_num
        })

        # Check if assessment completed
        assessment = await db["assessment_sessions"].find_one({
            "organization_id": organization_id,
            "user_id": user_id,
            "metadata.module_number": module_num,
            "status": "completed"
        })

        # Determine status
        if assessment:
            status = "completed"
            score = assessment.get("overall_score", 0)
            completed_at = assessment.get("completed_at")
        elif questions > 0:
            status = "in_progress"
            score = None
            completed_at = None
        else:
            status = "not_started"
            score = None
            completed_at = None

        module_progress.append(ModuleProgress(
            module_number=module_num,
            module_title=material["title"],
            status=status,
            score=score,
            time_spent_minutes=0,  # TODO: Track time
            questions_asked=questions,
            assessment_completed=assessment is not None,
            completed_at=completed_at
        ))

    return module_progress


async def calculate_achievements(
    organization_id: str,
    user_id: str,
    module_progress: List[ModuleProgress]
) -> tuple[List[Achievement], int]:
    """Calculate earned achievements and points."""
    db = MongoDB.get_database()
    achievements = []
    total_points = 0

    # Achievement: First Steps
    if any(m.status != "not_started" for m in module_progress):
        achievements.append(Achievement(
            id="first_steps",
            name="First Steps",
            description="Started the onboarding course",
            icon="🚀",
            earned_at=datetime.utcnow(),
            points=50
        ))
        total_points += 50

    # Achievement: First Module Complete
    completed_modules = [m for m in module_progress if m.status == "completed"]
    if len(completed_modules) >= 1:
        achievements.append(Achievement(
            id="first_module",
            name="First Module",
            description="Completed your first module",
            icon="✅",
            earned_at=completed_modules[0].completed_at or datetime.utcnow(),
            points=100
        ))
        total_points += 100

    # Achievement: Halfway There
    if len(completed_modules) >= 5:
        achievements.append(Achievement(
            id="halfway",
            name="Halfway There",
            description="Completed 5 modules",
            icon="🎯",
            earned_at=completed_modules[4].completed_at or datetime.utcnow(),
            points=200
        ))
        total_points += 200

    # Achievement: Course Complete
    if len(completed_modules) >= 10:
        achievements.append(Achievement(
            id="graduate",
            name="Graduate",
            description="Completed all 10 modules",
            icon="🎓",
            earned_at=completed_modules[9].completed_at or datetime.utcnow(),
            points=500
        ))
        total_points += 500

    # Achievement: Perfect Score
    perfect_scores = [m for m in completed_modules if m.score and m.score >= 0.95]
    if perfect_scores:
        achievements.append(Achievement(
            id="perfectionist",
            name="Perfectionist",
            description="Scored 95%+ on an assessment",
            icon="💯",
            earned_at=perfect_scores[0].completed_at or datetime.utcnow(),
            points=150
        ))
        total_points += 150

    # Achievement: Voice Master
    voice_questions = await db["questions"].count_documents({
        "student_id": user_id,
        "question_type": "voice"
    })
    if voice_questions >= 20:
        achievements.append(Achievement(
            id="voice_master",
            name="Voice Master",
            description="Asked 20+ voice questions",
            icon="🎤",
            earned_at=datetime.utcnow(),
            points=100
        ))
        total_points += 100

    return achievements, total_points


def calculate_next_steps(module_progress: List[ModuleProgress]) -> tuple[Optional[str], List[str]]:
    """Calculate next module and recommended actions."""
    # Find next module to work on
    next_module = None
    for module in sorted(module_progress, key=lambda m: m.module_number):
        if module.status == "not_started":
            next_module = module.module_title
            break

    # Generate recommendations
    recommendations = []

    # Not started yet
    if all(m.status == "not_started" for m in module_progress):
        recommendations.append("Start with Module 1: Welcome and Overview")
        recommendations.append("Try asking a voice question to get started")

    # In progress
    elif any(m.status == "in_progress" for m in module_progress):
        in_progress = [m for m in module_progress if m.status == "in_progress"]
        for module in in_progress[:2]:  # Top 2
            if not module.assessment_completed:
                recommendations.append(f"Complete assessment for {module.module_title}")

    # Review low scores
    low_scores = [m for m in module_progress if m.score and m.score < 0.7]
    if low_scores:
        recommendations.append(f"Review {low_scores[0].module_title} (score: {low_scores[0].score:.0%})")

    # Next module
    if next_module:
        recommendations.append(f"Continue with {next_module}")

    # Keep streak
    recommendations.append("Log in daily to maintain your learning streak")

    return next_module, recommendations[:5]  # Top 5 recommendations


# ============================================================================
# Student Endpoints
# ============================================================================

@router.get("/me", response_model=DashboardData)
async def get_my_dashboard(
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get dashboard data for current user.

    Returns:
        Complete dashboard with progress, achievements, and recommendations
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        db = MongoDB.get_database()

        # Get module progress
        module_progress = await get_module_progress(organization_id, user_id)

        # Calculate overall progress
        completed = len([m for m in module_progress if m.status == "completed"])
        total = len(module_progress)

        # Get all assessments
        assessments = await db["assessment_sessions"].find({
            "organization_id": organization_id,
            "user_id": user_id
        }).to_list(None)

        passed = len([a for a in assessments if a.get("status") == "completed" and a.get("overall_score", 0) >= 0.7])
        failed = len([a for a in assessments if a.get("status") == "completed" and a.get("overall_score", 0) < 0.7])
        pending = len([a for a in assessments if a.get("status") in ["not_started", "in_progress"]])

        avg_score = 0.0
        if assessments:
            completed_assessments = [a for a in assessments if a.get("status") == "completed"]
            if completed_assessments:
                avg_score = sum(a.get("overall_score", 0) for a in completed_assessments) / len(completed_assessments)

        # Get total questions
        total_questions = await db["questions"].count_documents({
            "student_id": user_id
        })

        overall_progress = OverallProgress(
            modules_completed=completed,
            total_modules=total,
            completion_percentage=(completed / total * 100) if total > 0 else 0,
            assessments_passed=passed,
            assessments_failed=failed,
            assessments_pending=pending,
            average_score=avg_score,
            total_time_minutes=0,  # TODO: Track time
            total_questions_asked=total_questions
        )

        # Calculate timeline
        first_question = await db["questions"].find_one(
            {"student_id": user_id},
            sort=[("created_at", 1)]
        )
        last_question = await db["questions"].find_one(
            {"student_id": user_id},
            sort=[("created_at", -1)]
        )

        started_at = first_question.get("created_at") if first_question else None
        last_activity = last_question.get("created_at") if last_question else None

        # Calculate streak (simplified)
        days_active = 1  # TODO: Calculate actual active days
        streak_days = 1  # TODO: Calculate current streak

        timeline = TimelineData(
            started_at=started_at,
            last_activity_at=last_activity,
            estimated_completion=None,  # TODO: Calculate
            days_active=days_active,
            streak_days=streak_days,
            longest_streak=streak_days
        )

        # Calculate achievements
        achievements, total_points = await calculate_achievements(
            organization_id,
            user_id,
            module_progress
        )

        # Next steps
        next_module, recommendations = calculate_next_steps(module_progress)

        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_questions = await db["questions"].count_documents({
            "student_id": user_id,
            "created_at": {"$gte": week_ago}
        })
        recent_assessments = await db["assessment_sessions"].count_documents({
            "user_id": user_id,
            "created_at": {"$gte": week_ago}
        })

        return DashboardData(
            student_id=user_id,
            organization_id=organization_id,
            overall_progress=overall_progress,
            module_progress=module_progress,
            timeline=timeline,
            achievements=achievements,
            total_points=total_points,
            next_module=next_module,
            recommended_actions=recommendations,
            recent_questions=recent_questions,
            recent_assessments=recent_assessments
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/organization", response_model=OrganizationDashboard)
async def get_organization_dashboard(
    user_context: dict = Depends(require_admin)
):
    """
    Get organization-wide dashboard (admin only).

    Returns:
        Organization analytics and metrics
    """
    try:
        organization_id = user_context["organization_id"]
        db = MongoDB.get_database()

        # Get all users in organization
        # TODO: Get from users collection
        all_students = await db["questions"].distinct("student_id", {
            "organization_id": organization_id
        })
        total_students = len(all_students)

        # Active students (activity in last 30 days)
        month_ago = datetime.utcnow() - timedelta(days=30)
        active_students_list = await db["questions"].distinct("student_id", {
            "organization_id": organization_id,
            "created_at": {"$gte": month_ago}
        })
        active_students = len(active_students_list)

        # Completed course
        completed = await db["assessment_sessions"].count_documents({
            "organization_id": organization_id,
            "metadata.module_number": 10,
            "status": "completed"
        })

        # Average completion rate
        avg_completion = (completed / total_students * 100) if total_students > 0 else 0

        # Average score
        all_assessments = await db["assessment_sessions"].find({
            "organization_id": organization_id,
            "status": "completed"
        }).to_list(None)

        avg_score = 0.0
        if all_assessments:
            avg_score = sum(a.get("overall_score", 0) for a in all_assessments) / len(all_assessments)

        # Voice questions
        voice_questions = await db["questions"].count_documents({
            "organization_id": organization_id,
            "question_type": "voice"
        })

        # Assessments completed
        assessments_count = await db["assessment_sessions"].count_documents({
            "organization_id": organization_id,
            "status": "completed"
        })

        # Total cost
        questions_with_cost = await db["questions"].find({
            "organization_id": organization_id
        }).to_list(None)
        total_cost = sum(q.get("cost", 0) or 0 for q in questions_with_cost)

        return OrganizationDashboard(
            organization_id=organization_id,
            total_students=total_students,
            active_students=active_students,
            completed_course=completed,
            average_completion_rate=avg_completion,
            average_score=avg_score,
            average_time_to_complete_days=0,  # TODO: Calculate
            total_learning_hours=0,  # TODO: Calculate
            most_challenging_module=None,  # TODO: Calculate
            easiest_module=None,  # TODO: Calculate
            voice_questions_asked=voice_questions,
            assessments_completed=assessments_count,
            total_cost=total_cost
        )

    except Exception as e:
        logger.error(f"Failed to get org dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization dashboard: {str(e)}"
        )

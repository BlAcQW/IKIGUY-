"""
Progress tracking routes for StudyFlow.

Provides endpoints for students and parents to view learning progress.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status

from app.models.progress import ProgressResponse, SubjectProgress
from app.models.user import UserRole
from app.services.progress_service import ProgressService
from app.services.user_service import UserService
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["Progress"])

# Role checkers
require_student = OrganizationRoleChecker([UserRole.STUDENT])
require_parent = OrganizationRoleChecker([UserRole.PARENT])


@router.get("/me", response_model=ProgressResponse)
async def get_my_progress(
    user_context: dict = Depends(require_student)
):
    """
    Get current student's progress with organization filtering.

    Returns overall learning metrics, streaks, and subject progress.

    Args:
        user_context: User context with organization info

    Returns:
        Student progress data

    Raises:
        HTTPException: If progress not found
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]
    school_id = user_context.get("school_id")

    progress = await ProgressService.get_student_progress(
        user_id,
        organization_id=organization_id,
        school_id=school_id
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )

    return ProgressResponse(
        student_id=progress.student_id,
        total_sessions=progress.total_sessions,
        total_time_minutes=progress.total_time_minutes,
        total_questions=progress.total_questions,
        total_exercises=progress.total_exercises,
        current_streak_days=progress.current_streak_days,
        subjects_progress=progress.subjects_progress,
        updated_at=progress.updated_at
    )


@router.get("/student/{student_id}", response_model=ProgressResponse)
async def get_student_progress_by_id(
    student_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get progress for a specific student with organization filtering.

    Parents can view their linked students' progress.
    Students can only view their own progress.
    All queries are organization-scoped.

    Args:
        student_id: Student ID to retrieve progress for
        user_context: User context with organization info

    Returns:
        Student progress data

    Raises:
        HTTPException: If unauthorized or progress not found
    """
    current_user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]
    user_role = user_context.get("role")

    # Students can only view their own progress
    if user_role == UserRole.STUDENT.value and student_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own progress"
        )

    # Parents can view linked students
    if user_role == UserRole.PARENT.value:
        parent = await UserService.get_user_by_id(current_user_id, organization_id)
        if not parent or student_id not in parent.student_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view progress of your linked students"
            )

    progress = await ProgressService.get_student_progress(
        student_id,
        organization_id=organization_id
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )

    return ProgressResponse(
        student_id=progress.student_id,
        total_sessions=progress.total_sessions,
        total_time_minutes=progress.total_time_minutes,
        total_questions=progress.total_questions,
        total_exercises=progress.total_exercises,
        current_streak_days=progress.current_streak_days,
        subjects_progress=progress.subjects_progress,
        updated_at=progress.updated_at
    )


@router.get("/subject/{subject}")
async def get_subject_progress(
    subject: str,
    user_context: dict = Depends(require_student)
):
    """
    Get progress for a specific subject with organization filtering.

    Args:
        subject: Subject name
        user_context: User context with organization info

    Returns:
        Subject progress details

    Raises:
        HTTPException: If subject progress not found
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]
    school_id = user_context.get("school_id")

    subject_progress = await ProgressService.get_subject_progress(
        user_id,
        subject,
        organization_id=organization_id,
        school_id=school_id
    )

    if not subject_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress found for subject: {subject}"
        )

    return subject_progress.dict()


@router.get("/weekly-summary")
async def get_weekly_summary(
    user_context: dict = Depends(require_student)
):
    """
    Get weekly learning summary with organization filtering.

    Returns last 7 days of learning activity.

    Args:
        user_context: User context with organization info

    Returns:
        Weekly summary statistics
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    summary = await ProgressService.get_weekly_summary(
        user_id,
        organization_id=organization_id
    )
    return summary


@router.get("/parent-dashboard")
async def get_parent_dashboard(
    user_context: dict = Depends(require_parent)
):
    """
    Get parent dashboard with all linked students' progress with organization filtering.

    Provides overview of all children's learning activity.

    Args:
        user_context: User context with organization info

    Returns:
        Dashboard with all students' data

    Raises:
        HTTPException: If parent not found or has no linked students
    """
    current_user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    # Get parent user
    parent = await UserService.get_user_by_id(current_user_id, organization_id)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )

    if not parent.student_ids:
        return {
            "parent_id": current_user_id,
            "students": [],
            "message": "No students linked to this parent account"
        }

    # Get dashboard data with organization filtering
    dashboard = await ProgressService.get_parent_dashboard(
        current_user_id,
        parent.student_ids,
        organization_id=organization_id
    )

    return dashboard


@router.get("/streak")
async def get_streak_info(
    user_context: dict = Depends(require_student)
):
    """
    Get learning streak information with organization filtering.

    Args:
        user_context: User context with organization info

    Returns:
        Streak data (current and longest streaks)
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    progress = await ProgressService.get_student_progress(
        user_id,
        organization_id=organization_id
    )

    if not progress:
        return {
            "current_streak_days": 0,
            "longest_streak_days": 0,
            "last_activity_date": None
        }

    return {
        "current_streak_days": progress.current_streak_days,
        "longest_streak_days": progress.longest_streak_days,
        "last_activity_date": progress.last_activity_date.isoformat() if progress.last_activity_date else None
    }


@router.get("/topics")
async def get_topic_mastery(
    user_context: dict = Depends(require_student)
):
    """
    Get mastery levels for all topics with organization filtering.

    Args:
        user_context: User context with organization info

    Returns:
        List of topics with mastery scores
    """
    user_id = user_context["user_id"]
    organization_id = user_context["organization_id"]

    progress = await ProgressService.get_student_progress(
        user_id,
        organization_id=organization_id
    )

    if not progress or not progress.topic_mastery:
        return []

    # Add mastery level to each topic
    topics_with_levels = []
    for topic in progress.topic_mastery:
        level = await ProgressService.calculate_mastery_level(topic.mastery_score)
        topics_with_levels.append({
            "topic": topic.topic,
            "questions_asked": topic.questions_asked,
            "mastery_score": topic.mastery_score,
            "mastery_level": level,
            "last_practiced": topic.last_practiced.isoformat() if topic.last_practiced else None
        })

    # Sort by mastery score descending
    topics_with_levels.sort(key=lambda x: x["mastery_score"], reverse=True)

    return topics_with_levels


@router.get("/leaderboard")
async def get_leaderboard(
    subject: Optional[str] = None,
    limit: int = 10,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get leaderboard of top learners with organization scoping.

    Optional: Filter by subject. Leaderboard is scoped to the user's organization.

    Args:
        subject: Optional subject filter
        limit: Number of top learners to return
        user_context: User context with organization info

    Returns:
        List of top learners with their stats
    """
    organization_id = user_context["organization_id"]

    # TODO: Implement leaderboard with privacy considerations
    # Will be organization-scoped to prevent cross-org data leakage
    # For now, return placeholder
    return {
        "leaderboard": [],
        "message": "Leaderboard feature coming soon",
        "subject": subject,
        "organization_id": organization_id
    }

"""
Exercise API Routes for StudyFlow.

Provides exercise generation, management, and submission capabilities
with adaptive difficulty based on student performance.

Features:
- Generate exercises from study materials using RAG
- Create manual exercises
- Submit and score exercises
- Adaptive difficulty recommendations
- Performance tracking

Author: KasaAI
Created: 2025-11-18
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import logging

from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole
from app.models.exercise import (
    ExerciseGenerateRequest,
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseDetailResponse,
    SubmissionCreate,
    SubmissionResponse,
    PerformanceRecommendation,
    DifficultyLevel,
    ExerciseStatus,
    SubmissionFeedbackResponse,
)
from app.services.exercise_service import ExerciseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["Exercises"])

# Only teachers and admins can create/generate exercises
require_teacher_or_admin = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


@router.post("/generate", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def generate_exercise(
    request: ExerciseGenerateRequest,
    background_tasks: BackgroundTasks,
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Generate exercise from study material using RAG.

    Requires teacher or admin role.

    Args:
        request: Exercise generation parameters
        user_context: User context with organization info

    Returns:
        Generated exercise metadata

    Raises:
        HTTPException: If generation fails
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        school_id = user_context.get("school_id")

        logger.info(
            f"Generating exercise for material {request.material_id} "
            f"by user {user_id}"
        )

        # Generate exercise (async operation)
        exercise = await ExerciseService.generate_exercise(
            request=request,
            organization_id=organization_id,
            created_by=user_id,
            school_id=school_id
        )

        return ExerciseResponse(
            id=exercise.id,
            title=exercise.title,
            description=exercise.description,
            subject=exercise.subject,
            topics=exercise.topics,
            difficulty=exercise.difficulty,
            total_points=exercise.total_points,
            num_questions=len(exercise.questions),
            time_limit_minutes=exercise.time_limit_minutes,
            passing_score_percentage=exercise.passing_score_percentage,
            created_by=exercise.created_by,
            created_at=exercise.created_at,
            status=exercise.status
        )

    except ValueError as e:
        logger.error(f"Exercise generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating exercise: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate exercise: {str(e)}"
        )


@router.post("/", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    user_context: dict = Depends(require_teacher_or_admin)
):
    """
    Manually create an exercise.

    Requires teacher or admin role.

    Args:
        exercise_data: Exercise creation data
        user_context: User context with organization info

    Returns:
        Created exercise

    Raises:
        HTTPException: If creation fails
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]
        school_id = user_context.get("school_id")

        exercise = await ExerciseService.create_exercise(
            exercise_data=exercise_data,
            organization_id=organization_id,
            created_by=user_id,
            school_id=school_id
        )

        return ExerciseResponse(
            id=exercise.id,
            title=exercise.title,
            description=exercise.description,
            subject=exercise.subject,
            topics=exercise.topics,
            difficulty=exercise.difficulty,
            total_points=exercise.total_points,
            num_questions=len(exercise.questions),
            time_limit_minutes=exercise.time_limit_minutes,
            passing_score_percentage=exercise.passing_score_percentage,
            created_by=exercise.created_by,
            created_at=exercise.created_at,
            status=exercise.status
        )

    except Exception as e:
        logger.error(f"Exercise creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exercise: {str(e)}"
        )


@router.get("/", response_model=List[ExerciseResponse])
async def list_exercises(
    subject: Optional[str] = None,
    difficulty: Optional[DifficultyLevel] = None,
    created_by: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    List available exercises with filtering.

    Args:
        subject: Filter by subject
        difficulty: Filter by difficulty
        created_by: Filter by creator
        limit: Maximum exercises to return
        skip: Number to skip (pagination)
        user_context: User context with organization info

    Returns:
        List of exercises
    """
    # Universal admins can see all exercises (no organization filter)
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]

    exercises = await ExerciseService.list_exercises(
        organization_id=organization_id,
        subject=subject,
        difficulty=difficulty,
        created_by=created_by,
        limit=limit,
        skip=skip
    )

    return [
        ExerciseResponse(
            id=ex.id,
            title=ex.title,
            description=ex.description,
            subject=ex.subject,
            topics=ex.topics,
            difficulty=ex.difficulty,
            total_points=ex.total_points,
            num_questions=len(ex.questions),
            time_limit_minutes=ex.time_limit_minutes,
            passing_score_percentage=ex.passing_score_percentage,
            created_by=ex.created_by,
            created_at=ex.created_at,
            status=ex.status
        )
        for ex in exercises
    ]


@router.get("/{exercise_id}", response_model=ExerciseDetailResponse)
async def get_exercise(
    exercise_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get exercise details including questions.

    Args:
        exercise_id: Exercise ID
        user_context: User context with organization info

    Returns:
        Exercise with questions

    Raises:
        HTTPException: If exercise not found
    """
    # Universal admins can access any exercise
    is_universal_admin = user_context.get("is_universal_admin", False)
    organization_id = None if is_universal_admin else user_context["organization_id"]

    exercise = await ExerciseService.get_exercise(
        exercise_id=exercise_id,
        organization_id=organization_id
    )

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    return ExerciseDetailResponse(
        id=exercise.id,
        title=exercise.title,
        description=exercise.description,
        subject=exercise.subject,
        topics=exercise.topics,
        difficulty=exercise.difficulty,
        total_points=exercise.total_points,
        num_questions=len(exercise.questions),
        time_limit_minutes=exercise.time_limit_minutes,
        passing_score_percentage=exercise.passing_score_percentage,
        created_by=exercise.created_by,
        created_at=exercise.created_at,
        status=exercise.status,
        questions=exercise.questions
    )


@router.post("/{exercise_id}/submit", response_model=SubmissionResponse)
async def submit_exercise(
    exercise_id: str,
    submission: SubmissionCreate,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Submit exercise answers and get scored results.

    Args:
        exercise_id: Exercise ID
        submission: Student answers
        user_context: User context with organization info

    Returns:
        Submission result with score and recommendations

    Raises:
        HTTPException: If submission fails
    """
    try:
        student_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        result = await ExerciseService.submit_exercise(
            exercise_id=exercise_id,
            student_id=student_id,
            answers=submission.answers,
            time_taken_seconds=submission.time_taken_seconds,
            organization_id=organization_id
        )

        return SubmissionResponse(
            id=result.id,
            exercise_id=result.exercise_id,
            student_id=result.student_id,
            score=result.score,
            max_score=result.max_score,
            percentage=result.percentage,
            passed=result.passed,
            questions_correct=result.questions_correct,
            questions_total=result.questions_total,
            time_taken_seconds=result.time_taken_seconds,
            recommended_next_difficulty=result.recommended_next_difficulty,
            weak_topics=result.weak_topics,
            submitted_at=result.submitted_at
        )

    except ValueError as e:
        logger.error(f"Submission failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit exercise: {str(e)}"
        )


@router.get("/submissions/{submission_id}/feedback", response_model=SubmissionFeedbackResponse)
async def get_submission_feedback(
    submission_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get detailed feedback for a submission.

    Includes per-question feedback, explanations, and performance summary.

    Args:
        submission_id: Submission ID
        user_context: User context with organization info

    Returns:
        Detailed feedback with recommendations

    Raises:
        HTTPException: If submission not found
    """
    try:
        feedback = await ExerciseService.get_submission_feedback(
            submission_id=submission_id
        )

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )

        # Verify user has access to this submission
        student_id = user_context["user_id"]
        is_universal_admin = user_context.get("is_universal_admin", False)

        if not is_universal_admin and feedback.student_id != student_id:
            # Check if user is a teacher/admin in the same organization
            user_role = user_context.get("role")
            if user_role not in [UserRole.ADMIN, UserRole.TEACHER]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )


@router.get("/performance/{subject}", response_model=PerformanceRecommendation)
async def get_recommendations(
    subject: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get personalized exercise recommendations based on performance.

    Args:
        subject: Subject to get recommendations for
        user_context: User context with organization info

    Returns:
        Personalized recommendations

    Raises:
        HTTPException: If no performance data found
    """
    student_id = user_context["user_id"]

    performance = await ExerciseService.get_performance(
        student_id=student_id,
        subject=subject
    )

    if not performance:
        # Return default recommendation for new students
        return PerformanceRecommendation(
            recommended_difficulty=DifficultyLevel.EASY,
            recommended_topics=[],
            reason="No previous performance data. Starting with easy difficulty.",
            focus_areas=["Build foundational knowledge"]
        )

    # Build recommendation based on performance
    focus_areas = []
    if performance.weak_topics:
        focus_areas.append(f"Review: {', '.join(performance.weak_topics[:3])}")
    if performance.average_recent_score < 70:
        focus_areas.append("Practice fundamentals")
    elif performance.average_recent_score >= 85:
        focus_areas.append("Challenge yourself with harder questions")

    recommended_topics = performance.weak_topics if performance.weak_topics else performance.mastered_topics

    reason = f"Based on {performance.total_exercises} exercises "
    reason += f"with {performance.average_recent_score:.1f}% recent average. "
    if performance.average_recent_score >= 80:
        reason += "Great job! Moving to next level."
    elif performance.average_recent_score < 60:
        reason += "Let's reinforce the basics."
    else:
        reason += "Keep practicing at this level."

    return PerformanceRecommendation(
        recommended_difficulty=performance.current_difficulty,
        recommended_topics=recommended_topics[:5],  # Top 5
        reason=reason,
        focus_areas=focus_areas
    )


@router.get("/submissions/me", response_model=List[SubmissionResponse])
async def get_my_submissions(
    limit: Optional[int] = 100,
    skip: Optional[int] = 0,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get current user's exercise submission history.

    Args:
        limit: Maximum number of submissions to return (default 100)
        skip: Number of submissions to skip for pagination (default 0)
        user_context: User context with organization info

    Returns:
        List of submissions with exercise details

    Raises:
        HTTPException: If failed to retrieve submissions
    """
    try:
        user_id = user_context["user_id"]

        # Get all submissions for the user
        submissions = await ExerciseService.get_user_submissions(
            user_id=user_id,
            limit=limit,
            skip=skip
        )

        return submissions

    except Exception as e:
        logger.error(f"Error getting user submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get submissions: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for exercises service."""
    return {"status": "healthy", "service": "exercises"}

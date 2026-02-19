"""
Assessment API Routes for StudyFlow.

Provides conversational assessment capabilities for evaluating student
understanding through interactive Q&A with voice and text support.

Features:
- Create and start assessment sessions
- Submit answers with automatic evaluation
- Real-time feedback and adaptive questioning
- Voice-enabled assessments (ASR + TTS)
- Comprehensive results and analytics

Author: KasaAI
Created: 2025-11-07
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.conversational_assessment_service import (
    ConversationalAssessmentService
)
from apps.shared.models.assessment_models import (
    AssessmentRequest,
    AnswerSubmission,
    AssessmentSession,
    AssessmentSummary,
    AssessmentType,
    QuestionDifficulty
)
from apps.shared.integration.rag import RAGConfig

from app.core.database import MongoDB
from app.core.auth import get_current_user_with_org, OrganizationRoleChecker
from app.models.user import UserRole
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["Assessments"])

# Only admins and teachers can create assessments
require_staff = OrganizationRoleChecker([UserRole.ADMIN, UserRole.TEACHER])


# ============================================================================
# Helper Functions
# ============================================================================

def get_assessment_service() -> ConversationalAssessmentService:
    """Get assessment service instance."""
    # Create RAG configuration
    rag_config = RAGConfig(
        postgres_host=settings.POSTGRES_HOST,
        postgres_port=settings.POSTGRES_PORT,
        postgres_user=settings.POSTGRES_USER,
        postgres_password=settings.POSTGRES_PASSWORD,
        postgres_db=settings.POSTGRES_DB,
        ai_provider=settings.AI_PROVIDER,
        api_key=settings.GEMINI_API_KEY,
        llm_model=settings.GEMINI_MODEL,
        embedding_model=settings.GEMINI_EMBEDDING_MODEL
    )

    return ConversationalAssessmentService(
        db=MongoDB.get_database(),
        rag_config=rag_config
    )


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateAssessmentRequest(BaseModel):
    """Request to create a new assessment."""
    subject: str
    topics: List[str] = Field(..., min_items=1)
    collection_name: Optional[str] = None  # Auto-determined if not provided

    # Configuration
    assessment_type: AssessmentType = AssessmentType.FORMATIVE
    num_questions: int = Field(5, ge=1, le=20)
    difficulty_levels: List[QuestionDifficulty] = Field(
        default_factory=lambda: [
            QuestionDifficulty.BEGINNER,
            QuestionDifficulty.INTERMEDIATE
        ]
    )

    # Optional
    custom_instructions: Optional[str] = None
    time_limit_seconds: Optional[int] = None


class SubmitAnswerRequest(BaseModel):
    """Request to submit answer to assessment question."""
    session_id: str
    question_id: str
    answer_text: str
    response_time_seconds: float = 0.0
    audio_base64: Optional[str] = None  # For voice answers


class AssessmentListResponse(BaseModel):
    """List of assessments response."""
    assessments: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


# ============================================================================
# Student Endpoints
# ============================================================================

@router.post("/create", response_model=Dict[str, Any])
async def create_assessment(
    request: CreateAssessmentRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Create a new assessment session for the current user.

    Generates questions from the knowledge base on specified topics.

    Args:
        request: Assessment configuration
        user_context: User context with organization info

    Returns:
        Created assessment session with questions

    Example:
        {
            "subject": "Mathematics",
            "topics": ["Algebra", "Equations"],
            "num_questions": 5,
            "difficulty_levels": ["beginner", "intermediate"]
        }
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        # Determine collection name if not provided
        collection_name = request.collection_name
        if not collection_name:
            # Auto-generate from subject
            subject_normalized = request.subject.lower().replace(" ", "_")
            collection_name = f"{organization_id}_{subject_normalized}"

        # Create assessment request
        assessment_request = AssessmentRequest(
            organization_id=organization_id,
            user_id=user_id,
            subject=request.subject,
            topics=request.topics,
            collection_name=collection_name,
            assessment_type=request.assessment_type,
            num_questions=request.num_questions,
            difficulty_range=request.difficulty_levels,
            custom_instructions=request.custom_instructions,
            time_limit_seconds=request.time_limit_seconds
        )

        # Create assessment session
        service = get_assessment_service()
        await service.initialize()

        session = await service.create_assessment_session(assessment_request)

        logger.info(
            f"Assessment created: session={session.id}, user={user_id}, "
            f"questions={session.total_questions}"
        )

        return {
            "session_id": session.id,
            "status": session.status,
            "total_questions": session.total_questions,
            "subject": session.subject,
            "topics": session.topics,
            "assessment_type": session.assessment_type,
            "message": "Assessment created successfully. Use /start to begin."
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create assessment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assessment: {str(e)}"
        )


@router.post("/{session_id}/start", response_model=Dict[str, Any])
async def start_assessment(
    session_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Start an assessment session.

    Changes status to IN_PROGRESS and returns the first question.

    Args:
        session_id: Assessment session ID
        user_context: User context with organization info

    Returns:
        First question and session info
    """
    try:
        service = get_assessment_service()
        await service.initialize()

        # Start session
        session = await service.start_assessment(session_id)

        # Verify user access
        if session.user_id != user_context["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this assessment"
            )

        # Get first question
        first_question = session.questions[0] if session.questions else None

        return {
            "session_id": session.id,
            "status": session.status,
            "current_question_index": session.current_question_index,
            "total_questions": session.total_questions,
            "question": first_question.dict() if first_question else None,
            "started_at": session.started_at.isoformat() if session.started_at else None
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start assessment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start assessment: {str(e)}"
        )


@router.post("/submit-answer", response_model=Dict[str, Any])
async def submit_answer(
    request: SubmitAnswerRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Submit an answer to an assessment question.

    Evaluates the answer, provides feedback, and returns the next question
    if available, or assessment summary if complete.

    Args:
        request: Answer submission
        user_context: User context with organization info

    Returns:
        Evaluation feedback and next question or final summary

    Example Response:
        {
            "evaluation": {
                "score": 0.85,
                "understanding_level": "good",
                "is_correct": true,
                "feedback": "Excellent answer! ...",
                ...
            },
            "is_complete": false,
            "progress": {
                "current": 2,
                "total": 5,
                "percentage": 40
            },
            "next_question": { ... }
        }
    """
    try:
        service = get_assessment_service()
        await service.initialize()

        # Verify user access
        session = await service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment session not found"
            )

        if session.user_id != user_context["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this assessment"
            )

        # Submit answer
        submission = AnswerSubmission(
            session_id=request.session_id,
            question_id=request.question_id,
            answer_text=request.answer_text,
            audio_base64=request.audio_base64,
            response_time_seconds=request.response_time_seconds
        )

        result = await service.submit_answer(submission)

        logger.info(
            f"Answer submitted: session={request.session_id}, "
            f"question={request.question_id}, "
            f"score={result['evaluation']['score']:.2f}"
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit answer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_assessment(
    session_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get assessment session details.

    Args:
        session_id: Assessment session ID
        user_context: User context with organization info

    Returns:
        Complete assessment session data
    """
    try:
        service = get_assessment_service()
        await service.initialize()

        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )

        # Verify user access
        if session.user_id != user_context["user_id"]:
            # Allow admins to view any assessment
            if user_context.get("role") not in [UserRole.ADMIN, UserRole.STAFF]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this assessment"
                )

        return session.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessment: {str(e)}"
        )


@router.get("/{session_id}/summary", response_model=Dict[str, Any])
async def get_assessment_summary(
    session_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get comprehensive summary of completed assessment.

    Args:
        session_id: Assessment session ID
        user_context: User context with organization info

    Returns:
        Assessment summary with scores, analysis, and recommendations

    Raises:
        HTTPException: If assessment not found or not completed
    """
    try:
        service = get_assessment_service()
        await service.initialize()

        # Verify access
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )

        if session.user_id != user_context["user_id"]:
            if user_context.get("role") not in [UserRole.ADMIN, UserRole.STAFF]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this assessment"
                )

        # Get summary
        summary = await service.get_assessment_summary(session_id)

        return summary.dict()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessment summary: {str(e)}"
        )


@router.get("/my/list", response_model=AssessmentListResponse)
async def get_my_assessments(
    page: int = 1,
    page_size: int = 10,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get all assessment sessions for the current user.

    Args:
        page: Page number (1-indexed)
        page_size: Results per page
        user_context: User context with organization info

    Returns:
        Paginated list of user's assessments
    """
    try:
        service = get_assessment_service()
        await service.initialize()

        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        skip = (page - 1) * page_size
        limit = page_size

        assessments = await service.get_user_assessments(
            user_id=user_id,
            organization_id=organization_id,
            limit=limit,
            skip=skip
        )

        return AssessmentListResponse(
            assessments=[a.dict() for a in assessments],
            total=len(assessments),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to get assessments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessments: {str(e)}"
        )


# ============================================================================
# Admin/Teacher Endpoints
# ============================================================================

@router.get("/organization/stats", response_model=Dict[str, Any])
async def get_organization_assessment_stats(
    user_context: dict = Depends(require_staff)
):
    """
    Get assessment statistics for the organization (admin/teacher only).

    Args:
        user_context: Admin/teacher user context

    Returns:
        Organization-wide assessment statistics

    TODO: Implement comprehensive statistics aggregation
    """
    try:
        # TODO: Implement statistics aggregation
        # This would query all assessments for the organization
        # and compute various metrics

        return {
            "message": "Assessment statistics endpoint - implementation pending",
            "organization_id": user_context["organization_id"]
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

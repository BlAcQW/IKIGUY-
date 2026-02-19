"""
Tutoring routes for StudyFlow.

Handles AI-powered Q&A sessions with TTS support for answer pronunciation.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.models.question import Question, QuestionCreate, QuestionResponse, QuestionType
from app.models.session import StudySession, SessionCreate, SessionResponse
from app.services.tutoring_service import TutoringService
from app.services.pronunciation_service import PronunciationService
from app.core.auth import get_current_user_with_org

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutoring", tags=["Tutoring"])


class AskQuestionRequest(BaseModel):
    """Request model for asking a question."""
    session_id: str
    subject: str
    topic: str = None
    question_text: str
    question_type: QuestionType = QuestionType.TEXT


class AskQuestionResponse(BaseModel):
    """Response model for question answer."""
    question_id: str
    answer: str
    confidence_score: float
    sources: List[str]
    cost: float
    response_time_ms: int


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_tutoring_session(
    session_data: SessionCreate,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Create a new tutoring session with organization context.

    A session represents a learning period where a student asks multiple questions.

    Args:
        session_data: Session creation data
        user_context: User context with organization info

    Returns:
        Created session

    Raises:
        HTTPException: If creation fails
    """
    try:
        # Verify student_id matches current user (or is their child)
        # TODO: Add parent-student relationship check

        # Ensure session_data has organization context
        if not session_data.organization_id:
            session_data.organization_id = user_context["organization_id"]
        if not session_data.school_id and user_context.get("school_id"):
            session_data.school_id = user_context["school_id"]

        session = await TutoringService.create_session(session_data)

        logger.info(f"Tutoring session created: {session.id}")

        return SessionResponse(
            id=session.id,
            organization_id=session.organization_id,
            school_id=session.school_id,
            student_id=session.student_id,
            subject=session.subject,
            topics=session.topics,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_minutes=session.duration_minutes,
            questions_asked=session.questions_asked,
            questions_answered=session.questions_answered,
            cost_incurred=session.cost_incurred
        )

    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Ask a question and get AI-powered answer with organization context.

    Uses RAG to retrieve relevant information from study materials
    and generate contextual answers.

    Args:
        request: Question request
        user_context: User context with organization info

    Returns:
        Question answer with sources and confidence

    Raises:
        HTTPException: If question processing fails
    """
    try:
        user_id = user_context["user_id"]
        organization_id = user_context["organization_id"]

        # Verify session exists with organization access control
        session = await TutoringService.get_session(request.session_id, organization_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # TODO: Verify user owns this session

        # Get organization-scoped collection name for subject
        collection_name = TutoringService.get_collection_name_for_subject(
            request.subject,
            grade=None,  # TODO: Get from student profile
            organization_id=organization_id
        )

        # Create question data
        question_data = QuestionCreate(
            session_id=request.session_id,
            student_id=user_id,
            subject=request.subject,
            topic=request.topic,
            question_text=request.question_text,
            question_type=request.question_type
        )

        # Ask question and get answer with organization filtering
        question = await TutoringService.ask_question(
            question_data=question_data,
            collection_name=collection_name,
            organization_id=organization_id
        )

        logger.info(f"Question answered: {question.id} in session {request.session_id}")

        return AskQuestionResponse(
            question_id=question.id,
            answer=question.answer_text,
            confidence_score=question.confidence_score,
            sources=question.sources_used,
            cost=question.cost,
            response_time_ms=question.response_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question answering error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get session details with organization access control.

    Args:
        session_id: Session ID
        user_context: User context with organization info

    Returns:
        Session details

    Raises:
        HTTPException: If session not found
    """
    organization_id = user_context["organization_id"]

    session = await TutoringService.get_session(session_id, organization_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # TODO: Verify user owns this session

    return SessionResponse(
        id=session.id,
        organization_id=session.organization_id,
        school_id=session.school_id,
        student_id=session.student_id,
        subject=session.subject,
        topics=session.topics,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_minutes=session.duration_minutes,
        questions_asked=session.questions_asked,
        questions_answered=session.questions_answered,
        cost_incurred=session.cost_incurred
    )


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    End a tutoring session with organization access control.

    Marks the session as completed and calculates final statistics.

    Args:
        session_id: Session ID
        user_context: User context with organization info

    Returns:
        Updated session

    Raises:
        HTTPException: If session not found or update fails
    """
    organization_id = user_context["organization_id"]

    session = await TutoringService.end_session(session_id, organization_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    logger.info(f"Session ended: {session_id}")

    return SessionResponse(
        id=session.id,
        organization_id=session.organization_id,
        school_id=session.school_id,
        student_id=session.student_id,
        subject=session.subject,
        topics=session.topics,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_minutes=session.duration_minutes,
        questions_asked=session.questions_asked,
        questions_answered=session.questions_answered,
        cost_incurred=session.cost_incurred
    )


@router.get("/sessions/{session_id}/questions", response_model=List[QuestionResponse])
async def get_session_questions(
    session_id: str,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get all questions from a session with organization access control.

    Returns the conversation history for a tutoring session.

    Args:
        session_id: Session ID
        user_context: User context with organization info

    Returns:
        List of questions and answers

    Raises:
        HTTPException: If session not found
    """
    organization_id = user_context["organization_id"]

    # Verify session exists with organization access control
    session = await TutoringService.get_session(session_id, organization_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # TODO: Verify user owns this session

    # Get questions with organization access control
    questions = await TutoringService.get_session_questions(session_id, organization_id=organization_id)

    return [
        QuestionResponse(
            id=q.id,
            session_id=q.session_id,
            student_id=q.student_id,
            subject=q.subject,
            topic=q.topic,
            question_text=q.question_text,
            question_type=q.question_type,
            answer_text=q.answer_text,
            confidence_score=q.confidence_score,
            sources_used=q.sources_used,
            cost=q.cost,
            created_at=q.created_at
        )
        for q in questions
    ]


@router.post("/questions/{question_id}/audio")
async def generate_answer_audio(
    question_id: str,
    provider_id: str = "coqui_xtts",
    language: str = "en",
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Generate audio pronunciation for an answer with organization context.

    Returns MP3 audio of the answer text synthesized by TTS provider.
    Cost is automatically deducted from user's wallet.

    Args:
        question_id: Question ID
        provider_id: TTS provider to use (default: coqui_xtts)
        language: Language code (default: en)
        user_context: User context with organization info

    Returns:
        Audio file (audio/mpeg)

    Raises:
        HTTPException: If question not found or audio generation fails
    """
    try:
        user_id = user_context["user_id"]

        # TODO: Verify user owns this question/session

        # Generate audio
        audio_bytes, cost, transaction_id = await TutoringService.generate_answer_audio(
            question_id=question_id,
            user_id=user_id,
            provider_id=provider_id,
            language=language
        )

        logger.info(
            f"Answer audio generated for question {question_id}, "
            f"cost=${cost:.4f}, transaction={transaction_id}"
        )

        # Return audio as MP3
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=answer_{question_id}.mp3",
                "X-Audio-Cost": str(cost),
                "X-Transaction-ID": transaction_id
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Audio generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audio: {str(e)}"
        )


class PronounceRequest(BaseModel):
    """Request model for word/phrase pronunciation."""
    text: str
    language: str = "en"
    provider_id: str = "coqui_xtts"


class PronounceResponse(BaseModel):
    """Response model for pronunciation."""
    audio_base64: str
    cost: float
    transaction_id: str


@router.post("/pronounce", response_model=PronounceResponse)
async def pronounce_word(
    request: PronounceRequest,
    user_context: dict = Depends(get_current_user_with_org)
):
    """
    Get pronunciation audio for a word or phrase with organization context.

    Useful for language learning - students can hear correct pronunciation
    of difficult words or phrases.

    Args:
        request: Pronunciation request
        user_context: User context with organization info

    Returns:
        Base64-encoded audio with cost info

    Raises:
        HTTPException: If pronunciation generation fails
    """
    try:
        user_id = user_context["user_id"]

        # Generate pronunciation audio
        audio_bytes, cost, transaction_id = await PronunciationService.synthesize_word_pronunciation(
            user_id=user_id,
            word=request.text,
            language=request.language,
            provider_id=request.provider_id
        )

        # Encode to base64
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        logger.info(
            f"Pronunciation generated: '{request.text}' ({request.language}), "
            f"cost=${cost:.4f}"
        )

        return PronounceResponse(
            audio_base64=audio_base64,
            cost=cost,
            transaction_id=transaction_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Pronunciation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pronunciation: {str(e)}"
        )


@router.get("/providers")
async def get_tts_providers():
    """
    Get available TTS providers and their capabilities.

    Returns information about all available TTS providers that can be
    used for answer audio and pronunciation.

    Returns:
        Dict of provider information
    """
    try:
        providers = await PronunciationService.get_available_providers()
        return {"providers": providers}

    except Exception as e:
        logger.error(f"Failed to get providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )

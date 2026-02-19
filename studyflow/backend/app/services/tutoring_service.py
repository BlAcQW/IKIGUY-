"""
Tutoring service for StudyFlow.

Handles AI-powered Q&A using RAG and conversation management.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.integration.rag import RAGService, RAGConfig
from shared.document_processing import CollectionNaming

from app.models.question import Question, QuestionCreate, QuestionType
from app.models.session import StudySession, SessionCreate, SessionStatus
from app.core.database import mongodb, COLLECTION_QUESTIONS, COLLECTION_SESSIONS
from app.config import settings
from bson import ObjectId

# Import progress service for tracking
from app.services.progress_service import ProgressService

# Import wallet service for cost deduction
from app.services.wallet_service import WalletService

# Import usage service for usage tracking
from app.services.usage_service import UsageService

# Import pronunciation service for TTS
from app.services.pronunciation_service import PronunciationService

logger = logging.getLogger(__name__)


class TutoringService:
    """
    Service for AI tutoring functionality.

    Integrates with RAG service for knowledge-based Q&A.
    """

    _rag_service: Optional[RAGService] = None

    @classmethod
    def get_rag_service(cls) -> RAGService:
        """
        Get or create RAG service instance.

        Returns:
            RAGService instance

        Raises:
            RuntimeError: If RAG configuration is incomplete
        """
        if cls._rag_service is None:
            # Create RAG configuration
            config = RAGConfig(
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

            cls._rag_service = RAGService(config)
            logger.info("✓ RAG Service initialized for tutoring")

        return cls._rag_service

    @staticmethod
    async def create_session(session_data: SessionCreate) -> StudySession:
        """
        Create a new study session.

        Args:
            session_data: Session creation data

        Returns:
            Created session
        """
        session = StudySession(
            organization_id=session_data.organization_id,  # Organization scoping
            school_id=session_data.school_id,
            student_id=session_data.student_id,
            subject=session_data.subject,
            topics=session_data.topics,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow(),
            metadata=session_data.metadata
        )

        collection = mongodb.get_collection(COLLECTION_SESSIONS)
        result = await collection.insert_one(session.dict(by_alias=True, exclude={"id"}))

        session.id = str(result.inserted_id)
        logger.info(f"Session created: {session.id} for student {session.student_id}")
        return session

    @staticmethod
    async def get_session(
        session_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[StudySession]:
        """
        Get session by ID with optional organization filtering.

        Args:
            session_id: Session ID
            organization_id: Organization ID for access control (optional)

        Returns:
            Session if found and accessible, None otherwise
        """
        # Build query
        query = {"_id": ObjectId(session_id)}
        if organization_id:
            query["organization_id"] = organization_id

        collection = mongodb.get_collection(COLLECTION_SESSIONS)
        session_doc = await collection.find_one(query)

        if session_doc:
            session_doc["id"] = str(session_doc["_id"])
            return StudySession(**session_doc)
        return None

    @staticmethod
    async def end_session(
        session_id: str,
        organization_id: Optional[str] = None
    ) -> Optional[StudySession]:
        """
        End a study session with organization access control.

        Args:
            session_id: Session ID
            organization_id: Organization ID for access control (optional)

        Returns:
            Updated session
        """
        session = await TutoringService.get_session(session_id, organization_id)
        if not session:
            return None

        # Calculate duration
        duration = (datetime.utcnow() - session.started_at).total_seconds() / 60

        # Update session
        collection = mongodb.get_collection(COLLECTION_SESSIONS)
        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": SessionStatus.COMPLETED.value,
                    "ended_at": datetime.utcnow(),
                    "duration_minutes": duration,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Update progress tracking
        await ProgressService.update_progress_after_session(session_id)

        # Deduct session cost from parent's wallet (if any cost incurred)
        if session.cost_incurred > 0:
            try:
                # Get student's parent ID
                from app.services.user_service import UserService
                student = await UserService.get_user_by_supabase_id(session.student_id)

                if student and student.parent_id:
                    # Deduct cost from parent's wallet
                    await WalletService.deduct_cost(
                        user_id=student.parent_id,
                        amount=session.cost_incurred,
                        description=f"Tutoring session - {session.subject}",
                        metadata={
                            "session_id": session_id,
                            "student_id": session.student_id,
                            "subject": session.subject,
                            "duration_minutes": duration,
                            "questions_asked": session.questions_asked
                        }
                    )
                    logger.info(f"Wallet debited: {session.cost_incurred} GHS for session {session_id}")
            except ValueError as e:
                # Insufficient balance - log warning but don't fail session
                logger.warning(f"Could not deduct session cost: {str(e)}")
            except Exception as e:
                logger.error(f"Wallet deduction error: {str(e)}")

        logger.info(f"Session ended: {session_id} (duration: {duration:.1f} min)")
        return await TutoringService.get_session(session_id, organization_id)

    @staticmethod
    async def ask_question(
        question_data: QuestionCreate,
        collection_name: str,
        organization_id: Optional[str] = None
    ) -> Question:
        """
        Ask a question and get AI answer using RAG with organization filtering.

        Args:
            question_data: Question data
            collection_name: RAG collection name for subject
            organization_id: Organization ID for metadata filtering (optional)

        Returns:
            Question with AI-generated answer

        Raises:
            Exception: If RAG query fails
        """
        start_time = datetime.utcnow()

        try:
            # Get RAG service
            rag = TutoringService.get_rag_service()

            # Build context from session/student data
            context = {
                "student_id": question_data.student_id,
                "subject": question_data.subject,
                "topic": question_data.topic or "",
            }

            # Build metadata filters for organization scoping
            filters = {}
            if organization_id:
                filters["organization_id"] = organization_id
                logger.info(f"Filtering RAG query by organization: {organization_id}")

            # Query knowledge base with organization filtering
            result = await rag.query_knowledge_base(
                collection_name=collection_name,
                query=question_data.question_text,
                context=context,
                filters=filters if filters else None
            )

            # Calculate response time
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Get token usage from result
            input_tokens = result.get("input_tokens", 0)
            output_tokens = result.get("output_tokens", 0)
            total_tokens = result.get("tokens_used", input_tokens + output_tokens)

            # Create question record
            question = Question(
                session_id=question_data.session_id,
                student_id=question_data.student_id,
                subject=question_data.subject,
                topic=question_data.topic,
                question_text=question_data.question_text,
                question_type=question_data.question_type,
                answer_text=result.get("response", "I couldn't find an answer to your question."),
                confidence_score=result.get("confidence_score", 0.0),
                sources_used=result.get("sources", []),
                tokens_used=total_tokens,
                cost=result.get("cost", 0.0),
                response_time_ms=response_time,
                metadata=question_data.metadata
            )

            # Save to database
            collection = mongodb.get_collection(COLLECTION_QUESTIONS)
            db_result = await collection.insert_one(question.dict(by_alias=True, exclude={"id"}))

            question.id = str(db_result.inserted_id)

            # Track usage with UsageService
            if input_tokens > 0 or output_tokens > 0:
                try:
                    await UsageService.track_rag_usage(
                        user_id=question_data.student_id,
                        session_id=question_data.session_id,
                        question_id=question.id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        num_queries=1,
                        provider=settings.AI_PROVIDER,
                        model=settings.GEMINI_MODEL,
                        subject=question_data.subject,
                        topic=question_data.topic
                    )
                except Exception as e:
                    # Don't fail question if usage tracking fails
                    logger.warning(f"Usage tracking failed for question {question.id}: {str(e)}")

            # Update session stats
            await TutoringService._update_session_stats(
                question_data.session_id,
                questions_increment=1,
                cost_increment=question.cost
            )

            # Update progress tracking
            await ProgressService.update_progress_after_question(question.id)

            logger.info(f"Question answered: {question.id} (confidence: {question.confidence_score:.2f})")
            return question

        except Exception as e:
            logger.error(f"Question answering error: {str(e)}")

            # Create question with error
            question = Question(
                session_id=question_data.session_id,
                student_id=question_data.student_id,
                subject=question_data.subject,
                topic=question_data.topic,
                question_text=question_data.question_text,
                question_type=question_data.question_type,
                answer_text=f"Sorry, I encountered an error: {str(e)}",
                confidence_score=0.0,
                metadata=question_data.metadata
            )

            # Save error question
            collection = mongodb.get_collection(COLLECTION_QUESTIONS)
            db_result = await collection.insert_one(question.dict(by_alias=True, exclude={"id"}))
            question.id = str(db_result.inserted_id)

            return question

    @staticmethod
    async def _update_session_stats(
        session_id: str,
        questions_increment: int = 0,
        cost_increment: float = 0.0
    ):
        """
        Update session statistics.

        Args:
            session_id: Session ID
            questions_increment: Number of questions to add
            cost_increment: Cost to add
        """
        collection = mongodb.get_collection(COLLECTION_SESSIONS)
        await collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$inc": {
                    "questions_asked": questions_increment,
                    "questions_answered": questions_increment,
                    "cost_incurred": cost_increment
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    @staticmethod
    async def get_session_questions(
        session_id: str,
        limit: int = 50,
        organization_id: Optional[str] = None
    ) -> list[Question]:
        """
        Get all questions from a session with organization access control.

        Args:
            session_id: Session ID
            limit: Maximum questions to return
            organization_id: Organization ID for access control (optional)

        Returns:
            List of questions
        """
        # First verify session access if organization_id provided
        if organization_id:
            session = await TutoringService.get_session(session_id, organization_id)
            if not session:
                # Session doesn't exist or not accessible
                return []

        collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        cursor = collection.find(
            {"session_id": session_id}
        ).sort("created_at", 1).limit(limit)

        questions = []
        async for question_doc in cursor:
            question_doc["id"] = str(question_doc["_id"])
            questions.append(Question(**question_doc))

        return questions

    @staticmethod
    async def generate_answer_audio(
        question_id: str,
        user_id: str,
        provider_id: str = "coqui_xtts",
        language: str = "en"
    ) -> Tuple[bytes, float, str]:
        """
        Generate audio pronunciation for an existing answer.

        Args:
            question_id: Question ID
            user_id: User ID for billing (parent wallet)
            provider_id: TTS provider to use (default: coqui_xtts)
            language: Language code (default: en)

        Returns:
            Tuple of (audio_bytes, cost_usd, transaction_id)

        Raises:
            ValueError: If question not found
            Exception: If audio generation fails
        """
        # Get question
        collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        question_doc = await collection.find_one({"_id": ObjectId(question_id)})

        if not question_doc:
            raise ValueError(f"Question {question_id} not found")

        # Get answer text
        answer_text = question_doc.get("answer_text", "")
        if not answer_text:
            raise ValueError("No answer text to synthesize")

        # Generate audio using pronunciation service
        audio_bytes, cost, transaction_id = await PronunciationService.synthesize_answer(
            user_id=user_id,
            answer_text=answer_text,
            language=language,
            provider_id=provider_id,
            speed=0.9  # Slightly slower for student comprehension
        )

        # Update question with audio metadata
        await collection.update_one(
            {"_id": ObjectId(question_id)},
            {
                "$set": {
                    "audio_generated": True,
                    "audio_cost": cost,
                    "audio_transaction_id": transaction_id,
                    "audio_provider": provider_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Audio generated for question {question_id}, cost=${cost:.4f}")

        return audio_bytes, cost, transaction_id

    @staticmethod
    def get_collection_name_for_subject(
        subject: str,
        grade: Optional[int] = None,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Get RAG collection name for a subject with organization scoping.

        Now uses shared CollectionNaming utility for consistency across apps.

        Collection naming pattern:
        - With org: studyflow_{org_id}_{subject}_grade{X}
        - Without org: studyflow_{subject}_grade{X} (legacy)

        Args:
            subject: Subject name
            grade: Grade level (optional)
            organization_id: Organization ID for multi-tenancy (optional)

        Returns:
            Collection name
        """
        # Use shared CollectionNaming utility
        return CollectionNaming.for_subject_grade(
            app_name="studyflow",
            subject=subject,
            grade=grade,
            organization_id=organization_id
        )

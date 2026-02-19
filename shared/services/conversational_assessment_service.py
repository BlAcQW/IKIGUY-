"""
Conversational Assessment Service.

Provides intelligent assessment capabilities with:
- Question generation from RAG knowledge bases
- Answer evaluation with LLM grading
- Adaptive difficulty adjustment
- Personalized feedback
- Voice and text interaction support

Author: KasaAI
Created: 2025-11-07
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

import sys
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.models.assessment_models import (
    AssessmentSession,
    AssessmentQuestion,
    QuestionResponse,
    AssessmentEvaluation,
    AssessmentSummary,
    AssessmentRequest,
    AnswerSubmission,
    AssessmentType,
    AssessmentStatus,
    QuestionDifficulty,
    UnderstandingLevel
)
from apps.shared.integration.rag import RAGConfig, RAGService

logger = logging.getLogger(__name__)


class ConversationalAssessmentService:
    """
    Service for managing conversational assessments.

    Provides comprehensive assessment capabilities including question
    generation, answer evaluation, and adaptive learning paths.
    """

    COLLECTION_NAME = "assessment_sessions"

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        rag_config: RAGConfig,
        llm_provider_service: Optional[Any] = None
    ):
        """
        Initialize the assessment service.

        Args:
            db: MongoDB database instance
            rag_config: RAG configuration for knowledge retrieval
            llm_provider_service: Optional LLM provider service for grading
        """
        self.db = db
        self.collection: AsyncIOMotorCollection = db[self.COLLECTION_NAME]
        self.rag_service = RAGService(rag_config)
        self.llm_provider_service = llm_provider_service

        logger.info("✓ ConversationalAssessmentService initialized")

    async def initialize(self):
        """Initialize service and create database indexes."""
        await self._create_indexes()
        logger.info("✅ ConversationalAssessmentService ready")

    async def _create_indexes(self):
        """Create MongoDB indexes for efficient querying."""
        await self.collection.create_index([
            ("organization_id", 1),
            ("user_id", 1)
        ])
        await self.collection.create_index([("status", 1)])
        await self.collection.create_index([("created_at", -1)])
        await self.collection.create_index([
            ("organization_id", 1),
            ("subject", 1)
        ])
        logger.info("✓ Assessment indexes created")

    async def create_assessment_session(
        self,
        request: AssessmentRequest
    ) -> AssessmentSession:
        """
        Create a new assessment session with auto-generated questions.

        Args:
            request: Assessment configuration request

        Returns:
            Created assessment session

        Raises:
            ValueError: If invalid request parameters
        """
        # Validate request
        if not request.topics:
            raise ValueError("At least one topic must be specified")

        # Generate questions from RAG knowledge base
        questions = await self._generate_questions(
            collection_name=request.collection_name,
            topics=request.topics,
            num_questions=request.num_questions,
            difficulty_range=request.difficulty_range,
            organization_id=request.organization_id
        )

        if not questions:
            raise ValueError(
                f"Could not generate questions for topics: {request.topics}"
            )

        # Create session
        session = AssessmentSession(
            id=str(uuid.uuid4()),
            organization_id=request.organization_id,
            user_id=request.user_id,
            assessment_type=request.assessment_type,
            status=AssessmentStatus.NOT_STARTED,
            subject=request.subject,
            topics=request.topics,
            collection_name=request.collection_name,
            questions=questions,
            total_questions=len(questions),
            metadata={
                "custom_instructions": request.custom_instructions,
                "time_limit_seconds": request.time_limit_seconds
            }
        )

        # Save to database
        await self.collection.insert_one(session.dict(by_alias=True, exclude={"id"}))

        logger.info(
            f"Assessment session created: {session.id}, "
            f"questions={len(questions)}, topics={request.topics}"
        )

        return session

    async def _generate_questions(
        self,
        collection_name: str,
        topics: List[str],
        num_questions: int,
        difficulty_range: List[QuestionDifficulty],
        organization_id: str
    ) -> List[AssessmentQuestion]:
        """
        Generate assessment questions from RAG knowledge base.

        Uses RAG to find relevant content and LLM to generate questions.

        Args:
            collection_name: RAG collection name
            topics: Topics to cover
            num_questions: Number of questions to generate
            difficulty_range: Difficulty levels to include
            organization_id: Organization ID for scoping

        Returns:
            List of generated assessment questions
        """
        questions = []

        # Build query for each topic
        for topic in topics:
            # Query RAG for relevant content
            query = f"Explain key concepts about {topic}"

            try:
                rag_result = await self.rag_service.query_with_context(
                    query=query,
                    collection_name=collection_name,
                    top_k=3,
                    filters={"organization_id": organization_id}
                )

                # Generate questions from context
                topic_questions = await self._generate_questions_from_context(
                    topic=topic,
                    context=rag_result["context"],
                    documents=rag_result["documents"],
                    num_questions=max(1, num_questions // len(topics)),
                    difficulty_range=difficulty_range
                )

                questions.extend(topic_questions)

            except Exception as e:
                logger.error(f"Failed to generate questions for topic {topic}: {e}")
                continue

        # Trim to requested number
        questions = questions[:num_questions]

        logger.info(f"Generated {len(questions)} assessment questions")
        return questions

    async def _generate_questions_from_context(
        self,
        topic: str,
        context: str,
        documents: List[Dict[str, Any]],
        num_questions: int,
        difficulty_range: List[QuestionDifficulty]
    ) -> List[AssessmentQuestion]:
        """
        Generate questions from RAG context using LLM.

        Args:
            topic: Topic name
            context: RAG context text
            documents: Source documents
            num_questions: Number of questions to generate
            difficulty_range: Difficulty levels

        Returns:
            List of assessment questions
        """
        # Prompt for question generation
        prompt = f"""Generate {num_questions} assessment questions about: {topic}

Based on this content:
{context[:1500]}

For each question, provide:
1. The question text (clear and specific)
2. Expected answer (concise)
3. Key concepts being tested (list)
4. Difficulty level ({', '.join(d.value for d in difficulty_range)})

Format as JSON array with fields: question_text, expected_answer, key_concepts, difficulty
"""

        try:
            # Use LLM to generate questions
            if self.llm_provider_service:
                # TODO: Integrate with LLMProviderService
                # For now, create template questions
                pass

            # Fallback: Create questions from context
            questions = self._create_template_questions(
                topic=topic,
                context=context,
                num_questions=num_questions,
                difficulty_range=difficulty_range,
                documents=documents
            )

            return questions

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return []

    def _create_template_questions(
        self,
        topic: str,
        context: str,
        num_questions: int,
        difficulty_range: List[QuestionDifficulty],
        documents: List[Dict[str, Any]]
    ) -> List[AssessmentQuestion]:
        """
        Create template questions when LLM generation fails.

        Args:
            topic: Topic name
            context: Context text
            num_questions: Number of questions
            difficulty_range: Difficulty levels
            documents: Source documents

        Returns:
            List of template assessment questions
        """
        questions = []

        # Extract key sentences from context
        sentences = [s.strip() for s in context.split('.') if len(s.strip()) > 20]
        sentences = sentences[:num_questions]

        for i, sentence in enumerate(sentences):
            difficulty = difficulty_range[i % len(difficulty_range)]

            question = AssessmentQuestion(
                id=str(uuid.uuid4()),
                question_text=f"Explain the following about {topic}: {sentence[:100]}?",
                expected_answer=sentence,
                key_concepts=[topic],
                difficulty=difficulty,
                topic=topic,
                relevant_documents=[d.get("title", "") for d in documents[:3]],
                context_snippet=sentence[:200]
            )
            questions.append(question)

        return questions

    async def start_assessment(self, session_id: str) -> AssessmentSession:
        """
        Start an assessment session.

        Args:
            session_id: Assessment session ID

        Returns:
            Updated session with status IN_PROGRESS

        Raises:
            ValueError: If session not found or already started
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Assessment session not found: {session_id}")

        if session.status != AssessmentStatus.NOT_STARTED:
            raise ValueError(f"Assessment already started: {session.status}")

        # Update status
        session.status = AssessmentStatus.IN_PROGRESS
        session.started_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()

        await self.collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": session.status,
                    "started_at": session.started_at,
                    "updated_at": session.updated_at
                }
            }
        )

        logger.info(f"Assessment started: {session_id}")
        return session

    async def submit_answer(
        self,
        submission: AnswerSubmission
    ) -> Dict[str, Any]:
        """
        Submit and evaluate an answer to an assessment question.

        Args:
            submission: Answer submission with session and question IDs

        Returns:
            Evaluation result with feedback and next question

        Raises:
            ValueError: If session or question not found
        """
        # Get session
        session = await self.get_session(submission.session_id)
        if not session:
            raise ValueError(f"Session not found: {submission.session_id}")

        # Find question
        question = next(
            (q for q in session.questions if q.id == submission.question_id),
            None
        )
        if not question:
            raise ValueError(f"Question not found: {submission.question_id}")

        # Evaluate answer
        evaluation = await self._evaluate_answer(
            question=question,
            student_answer=submission.answer_text,
            collection_name=session.collection_name,
            organization_id=session.organization_id
        )

        # Create response record
        response = QuestionResponse(
            question_id=question.id,
            question_text=question.question_text,
            student_answer=submission.answer_text,
            expected_answer=question.expected_answer,
            score=evaluation.score,
            understanding_level=evaluation.understanding_level,
            is_correct=evaluation.is_correct,
            key_concepts_identified=evaluation.key_concepts_identified,
            missing_concepts=evaluation.missing_concepts,
            feedback=evaluation.feedback,
            response_time_seconds=submission.response_time_seconds,
            confidence_score=evaluation.confidence,
            difficulty=question.difficulty
        )

        # Update session
        session.responses.append(response)
        session.current_question_index += 1
        session.updated_at = datetime.utcnow()

        # Check if assessment complete
        is_complete = session.current_question_index >= session.total_questions

        if is_complete:
            session = await self._complete_assessment(session)

        # Save session
        await self.collection.update_one(
            {"_id": submission.session_id},
            {
                "$set": session.dict(by_alias=True, exclude={"id"})
            }
        )

        # Prepare response
        result = {
            "evaluation": evaluation.dict(),
            "is_complete": is_complete,
            "progress": {
                "current": session.current_question_index,
                "total": session.total_questions,
                "percentage": (session.current_question_index / session.total_questions) * 100
            }
        }

        if not is_complete:
            # Get next question
            next_question = session.questions[session.current_question_index]
            result["next_question"] = next_question.dict()
        else:
            # Provide summary
            summary = await self.get_assessment_summary(submission.session_id)
            result["summary"] = summary.dict()

        logger.info(
            f"Answer submitted: session={submission.session_id}, "
            f"score={evaluation.score:.2f}, complete={is_complete}"
        )

        return result

    async def _evaluate_answer(
        self,
        question: AssessmentQuestion,
        student_answer: str,
        collection_name: str,
        organization_id: str
    ) -> AssessmentEvaluation:
        """
        Evaluate student answer using RAG context and LLM grading.

        This is the core evaluation engine (Phase 4.2).

        Args:
            question: The assessment question
            student_answer: Student's answer text
            collection_name: RAG collection for verification
            organization_id: Organization ID

        Returns:
            Detailed evaluation with score and feedback
        """
        # Query RAG for verification context
        try:
            rag_result = await self.rag_service.query_with_context(
                query=student_answer,
                collection_name=collection_name,
                top_k=3,
                filters={"organization_id": organization_id}
            )
            context = rag_result["context"]
        except Exception as e:
            logger.warning(f"RAG query failed during evaluation: {e}")
            context = question.context_snippet or ""

        # Build evaluation prompt
        prompt = f"""Evaluate this student answer for an assessment question.

Question: {question.question_text}

Expected Answer: {question.expected_answer}

Key Concepts: {', '.join(question.key_concepts)}

Student Answer: {student_answer}

Reference Context:
{context[:1000]}

Provide evaluation as JSON with:
1. score (0.0-1.0)
2. is_correct (boolean)
3. understanding_level (no_understanding, minimal, partial, good, excellent)
4. key_concepts_identified (list of concepts student demonstrated)
5. missing_concepts (list of concepts student missed)
6. feedback (constructive feedback for student, 2-3 sentences)
7. explanation (why this score was given)
8. hints_for_improvement (list of specific suggestions)
"""

        try:
            # Use LLM for evaluation
            if self.llm_provider_service:
                # TODO: Integrate with actual LLM service
                # For now, use fallback evaluation
                pass

            # Fallback: Simple keyword-based evaluation
            evaluation = self._fallback_evaluation(
                question=question,
                student_answer=student_answer,
                context=context
            )

            return evaluation

        except Exception as e:
            logger.error(f"Answer evaluation failed: {e}")
            # Return minimal evaluation
            return AssessmentEvaluation(
                score=0.5,
                understanding_level=UnderstandingLevel.PARTIAL,
                is_correct=False,
                feedback="Answer received. Unable to complete full evaluation.",
                evaluation_method="fallback"
            )

    def _fallback_evaluation(
        self,
        question: AssessmentQuestion,
        student_answer: str,
        context: str
    ) -> AssessmentEvaluation:
        """
        Fallback evaluation using keyword matching and basic heuristics.

        Args:
            question: Assessment question
            student_answer: Student's answer
            context: Reference context

        Returns:
            Basic evaluation result
        """
        student_lower = student_answer.lower()
        expected_lower = (question.expected_answer or "").lower()

        # Check for key concepts
        concepts_found = [
            concept for concept in question.key_concepts
            if concept.lower() in student_lower
        ]

        concepts_missing = [
            concept for concept in question.key_concepts
            if concept.lower() not in student_lower
        ]

        # Calculate score based on concept coverage
        if question.key_concepts:
            concept_score = len(concepts_found) / len(question.key_concepts)
        else:
            concept_score = 0.5

        # Check answer length (should be substantial)
        length_score = min(len(student_answer) / 100, 1.0)

        # Combine scores
        score = (concept_score * 0.7) + (length_score * 0.3)

        # Determine understanding level
        if score >= 0.8:
            understanding = UnderstandingLevel.EXCELLENT
        elif score >= 0.6:
            understanding = UnderstandingLevel.GOOD
        elif score >= 0.4:
            understanding = UnderstandingLevel.PARTIAL
        elif score >= 0.2:
            understanding = UnderstandingLevel.MINIMAL
        else:
            understanding = UnderstandingLevel.NO_UNDERSTANDING

        # Generate feedback
        if score >= 0.8:
            feedback = f"Excellent answer! You demonstrated strong understanding of {', '.join(concepts_found)}."
        elif score >= 0.6:
            feedback = f"Good work! You covered {', '.join(concepts_found)}. "
            if concepts_missing:
                feedback += f"Consider also discussing {', '.join(concepts_missing[:2])}."
        else:
            feedback = "Your answer shows some understanding, but could be more complete. "
            if concepts_missing:
                feedback += f"Try to include information about {', '.join(concepts_missing[:2])}."

        return AssessmentEvaluation(
            score=round(score, 2),
            understanding_level=understanding,
            is_correct=score >= 0.7,
            key_concepts_identified=concepts_found,
            missing_concepts=concepts_missing,
            feedback=feedback,
            evaluation_method="fallback_keyword",
            confidence=0.6
        )

    async def _complete_assessment(
        self,
        session: AssessmentSession
    ) -> AssessmentSession:
        """
        Complete an assessment and calculate final scores.

        Args:
            session: Assessment session to complete

        Returns:
            Updated session with final scores and feedback
        """
        session.status = AssessmentStatus.COMPLETED
        session.completed_at = datetime.utcnow()

        if session.started_at:
            session.total_time_seconds = (
                session.completed_at - session.started_at
            ).total_seconds()

        # Calculate overall score
        if session.responses:
            scores = [r.score for r in session.responses]
            session.overall_score = sum(scores) / len(scores)

            # Determine overall understanding
            percentage = session.overall_score * 100
            if percentage >= 80:
                session.overall_understanding = UnderstandingLevel.EXCELLENT
            elif percentage >= 60:
                session.overall_understanding = UnderstandingLevel.GOOD
            elif percentage >= 40:
                session.overall_understanding = UnderstandingLevel.PARTIAL
            elif percentage >= 20:
                session.overall_understanding = UnderstandingLevel.MINIMAL
            else:
                session.overall_understanding = UnderstandingLevel.NO_UNDERSTANDING

        # Analyze performance
        session = await self._analyze_performance(session)

        # Generate final feedback
        session.final_feedback = self._generate_final_feedback(session)
        session.encouragement_message = self._generate_encouragement(session)

        logger.info(
            f"Assessment completed: {session.id}, "
            f"score={session.overall_score:.2f}, "
            f"understanding={session.overall_understanding}"
        )

        return session

    async def _analyze_performance(
        self,
        session: AssessmentSession
    ) -> AssessmentSession:
        """
        Analyze assessment performance to identify strengths and weaknesses.

        Args:
            session: Assessment session

        Returns:
            Session with performance analysis
        """
        # Identify strong areas (score >= 0.7)
        strong_topics = set()
        weak_topics = set()

        for response in session.responses:
            if response.score >= 0.7:
                strong_topics.update(response.key_concepts_identified)
            elif response.score < 0.5:
                weak_topics.update(response.missing_concepts)

        session.strong_areas = list(strong_topics)
        session.weak_areas = list(weak_topics)

        # Recommend topics for review
        session.recommended_topics = list(weak_topics)[:5]

        return session

    def _generate_final_feedback(self, session: AssessmentSession) -> str:
        """
        Generate personalized final feedback.

        This is part of Phase 4.3 (Feedback Generation).

        Args:
            session: Completed assessment session

        Returns:
            Final feedback message
        """
        percentage = session.overall_score * 100

        feedback_parts = []

        # Overall performance
        if percentage >= 80:
            feedback_parts.append(
                f"Outstanding performance! You scored {percentage:.0f}% overall."
            )
        elif percentage >= 60:
            feedback_parts.append(
                f"Good work! You achieved {percentage:.0f}% on this assessment."
            )
        elif percentage >= 40:
            feedback_parts.append(
                f"You scored {percentage:.0f}%. There's room for improvement."
            )
        else:
            feedback_parts.append(
                f"You scored {percentage:.0f}%. Let's work on building your understanding."
            )

        # Strong areas
        if session.strong_areas:
            feedback_parts.append(
                f"You demonstrated strong understanding of: {', '.join(session.strong_areas[:3])}."
            )

        # Areas for improvement
        if session.weak_areas:
            feedback_parts.append(
                f"Focus on reviewing: {', '.join(session.weak_areas[:3])}."
            )

        # Recommendations
        if session.recommended_topics:
            feedback_parts.append(
                f"I recommend studying these topics next: {', '.join(session.recommended_topics[:3])}."
            )

        return " ".join(feedback_parts)

    def _generate_encouragement(self, session: AssessmentSession) -> str:
        """
        Generate encouraging message based on performance.

        Args:
            session: Assessment session

        Returns:
            Encouragement message
        """
        percentage = session.overall_score * 100

        if percentage >= 90:
            return "Excellent work! You're mastering this subject. Keep it up!"
        elif percentage >= 70:
            return "Great job! You're on the right track. Continue practicing!"
        elif percentage >= 50:
            return "Good effort! With more practice, you'll improve even more."
        else:
            return "Keep practicing! Every assessment helps you learn and grow."

    async def get_session(self, session_id: str) -> Optional[AssessmentSession]:
        """
        Get assessment session by ID.

        Args:
            session_id: Session ID

        Returns:
            Assessment session or None if not found
        """
        doc = await self.collection.find_one({"_id": session_id})
        if doc:
            doc.pop("_id", None)
            doc["id"] = session_id
            return AssessmentSession(**doc)
        return None

    async def get_assessment_summary(
        self,
        session_id: str
    ) -> AssessmentSummary:
        """
        Get comprehensive summary of completed assessment.

        Args:
            session_id: Assessment session ID

        Returns:
            Assessment summary with results and analysis

        Raises:
            ValueError: If session not found or not completed
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Assessment session not found: {session_id}")

        if session.status != AssessmentStatus.COMPLETED:
            raise ValueError(f"Assessment not completed: {session.status}")

        # Calculate score breakdown
        score_by_topic = {}
        score_by_difficulty = {}

        for response in session.responses:
            # By topic
            topic = next(
                (q.topic for q in session.questions if q.id == response.question_id),
                "General"
            )
            if topic not in score_by_topic:
                score_by_topic[topic] = []
            score_by_topic[topic].append(response.score)

            # By difficulty
            difficulty = response.difficulty.value
            if difficulty not in score_by_difficulty:
                score_by_difficulty[difficulty] = []
            score_by_difficulty[difficulty].append(response.score)

        # Average scores
        score_by_topic = {
            topic: sum(scores) / len(scores)
            for topic, scores in score_by_topic.items()
        }
        score_by_difficulty = {
            diff: sum(scores) / len(scores)
            for diff, scores in score_by_difficulty.items()
        }

        # Calculate timing
        avg_time = session.total_time_seconds / max(len(session.responses), 1)

        summary = AssessmentSummary(
            session_id=session.id,
            user_id=session.user_id,
            organization_id=session.organization_id,
            subject=session.subject,
            topics=session.topics,
            assessment_type=session.assessment_type,
            total_questions=session.total_questions,
            questions_answered=len(session.responses),
            overall_score=session.overall_score,
            overall_percentage=session.overall_score * 100,
            understanding_level=session.overall_understanding,
            score_by_topic=score_by_topic,
            score_by_difficulty=score_by_difficulty,
            strong_areas=session.strong_areas,
            weak_areas=session.weak_areas,
            recommended_next_steps=session.recommended_topics,
            total_time_seconds=session.total_time_seconds,
            average_time_per_question=avg_time,
            final_feedback=session.final_feedback,
            encouragement_message=session.encouragement_message,
            completed_at=session.completed_at
        )

        return summary

    async def get_user_assessments(
        self,
        user_id: str,
        organization_id: str,
        limit: int = 10,
        skip: int = 0
    ) -> List[AssessmentSession]:
        """
        Get all assessment sessions for a user.

        Args:
            user_id: User ID
            organization_id: Organization ID
            limit: Maximum results
            skip: Results to skip (pagination)

        Returns:
            List of assessment sessions
        """
        cursor = self.collection.find({
            "user_id": user_id,
            "organization_id": organization_id
        }).sort("created_at", -1).skip(skip).limit(limit)

        sessions = []
        async for doc in cursor:
            doc.pop("_id", None)
            doc["id"] = doc.get("id", str(uuid.uuid4()))
            sessions.append(AssessmentSession(**doc))

        return sessions

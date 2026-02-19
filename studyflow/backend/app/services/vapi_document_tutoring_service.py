"""
VAPI Document Tutoring Service for StudyFlow.

Provides conversational voice tutoring for uploaded documents using VAPI.
Students can have natural voice conversations with AI about their study materials.

Features:
- Document-specific VAPI assistants
- Function calling for knowledge base queries
- Exercise generation and evaluation
- Session tracking and cost management
"""

import logging
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.integration.vapi import VAPIService, VAPIAgent
from apps.shared.integration.rag import RAGService

from app.models.session import StudySession
from app.models.question import Question, QuestionType
from app.models.material import StudyMaterial, MaterialUpdate
from app.core.database import mongodb, COLLECTION_QUESTIONS, COLLECTION_SESSIONS
from app.services.tutoring_service import TutoringService
from app.services.exercise_service import ExerciseService
from app.services.material_service import MaterialService
from app.services.progress_service import ProgressService
from app.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)


class VAPIDocumentTutoringService:
    """
    VAPI-powered conversational voice tutoring for documents.

    Creates VAPI assistants for uploaded study materials, enabling
    students to have natural voice conversations about the content.
    """

    _vapi_service: Optional[VAPIService] = None
    _rag_service: Optional[RAGService] = None

    @classmethod
    def get_vapi_service(cls) -> VAPIService:
        """
        Get or create VAPI service instance.

        Returns:
            VAPIService instance
        """
        if cls._vapi_service is None:
            cls._vapi_service = VAPIService({
                "VAPI_API_KEY": settings.VAPI_API_KEY,
                "VAPI_US_PHONE_ID": settings.VAPI_US_PHONE_ID,
                "webhook_url": f"{settings.API_BASE_URL}/api/v1/vapi/webhook"
            })
            logger.info("✓ VAPI Service initialized for document tutoring")

        return cls._vapi_service

    @classmethod
    def get_rag_service(cls) -> RAGService:
        """
        Get or create RAG service instance.

        Returns:
            RAGService instance
        """
        if cls._rag_service is None:
            cls._rag_service = TutoringService.get_rag_service()
            logger.info("✓ RAG Service initialized for VAPI document tutoring")

        return cls._rag_service

    @staticmethod
    async def create_document_assistant(
        material_id: str,
        organization_id: str,
        user_id: str,
        voice_id: str = "jennifer",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Create a VAPI assistant for a specific document.

        Args:
            material_id: Study material ID
            organization_id: Organization ID
            user_id: User ID creating the assistant
            voice_id: VAPI voice ID (default: jennifer - warm, patient voice)
            language: Language code (default: en)

        Returns:
            Dict with assistant creation result

        Raises:
            ValueError: If material not found
            Exception: If assistant creation fails
        """
        # Get material
        material = await MaterialService.get_material_by_id(material_id, organization_id)
        if not material:
            raise ValueError(f"Material not found: {material_id}")

        if material.status != "completed":
            raise ValueError(f"Material not processed yet: {material.status}")

        # Get collection name for material
        collection_name = TutoringService.get_collection_name_for_subject(
            subject=material.subject,
            organization_id=organization_id
        )

        # Build system prompt
        system_prompt = f"""You are a warm, patient, and encouraging AI tutor helping a student learn about {material.subject}.

Your role:
- Answer questions about the study material "{material.title}"
- Break down complex concepts into simple explanations
- Provide examples and analogies
- Generate practice exercises when asked
- Evaluate student responses with constructive feedback
- Encourage the student's learning journey

Guidelines:
- Be conversational and friendly
- Ask clarifying questions if needed
- Cite specific parts of the material when answering
- Adapt your explanations to the student's understanding level
- Celebrate progress and provide constructive feedback

Study Material: {material.title}
Subject: {material.subject}
Topics: {', '.join(material.topics or [])}
Grade Level: {material.grade or 'General'}
"""

        # Create VAPI agent configuration
        agent = VAPIAgent(
            name=f"Tutor for {material.title[:30]}",
            description=f"AI tutor for {material.subject} - {material.title}",
            system_prompt=system_prompt,
            voice=voice_id,
            language=language,
            speed=0.95,  # Slightly slower for comprehension
            max_duration=1800,  # 30 minutes max
            silence_timeout=15,  # Allow thinking time
            interruptible=True,
            record_calls=True,
            metadata={
                "material_id": material_id,
                "subject": material.subject,
                "organization_id": organization_id,
                "created_by": user_id,
                "collection_name": collection_name
            }
        )

        # Create assistant with VAPI
        vapi = VAPIDocumentTutoringService.get_vapi_service()
        result = await vapi.create_agent(agent)

        if not result.get("success"):
            raise Exception(f"Failed to create VAPI assistant: {result.get('error')}")

        # Store assistant ID in material metadata
        await MaterialService.update_material(
            material_id,
            MaterialUpdate(
                metadata={
                    **(material.metadata or {}),
                    "vapi_assistant_id": result.get("assistant_id"),
                    "vapi_assistant_created_at": datetime.utcnow().isoformat()
                }
            ),
            organization_id
        )

        logger.info(
            f"VAPI assistant created for material {material_id}: "
            f"assistant_id={result.get('assistant_id')}"
        )

        return {
            "success": True,
            "assistant_id": result.get("assistant_id"),
            "material": {
                "id": material.id,
                "title": material.title,
                "subject": material.subject
            },
            "voice": voice_id,
            "language": language
        }

    @staticmethod
    async def start_voice_session(
        material_id: str,
        student_id: str,
        organization_id: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Start a VAPI voice tutoring session for a document.

        Args:
            material_id: Study material ID
            student_id: Student user ID
            organization_id: Organization ID
            phone_number: Student's phone number for outbound call

        Returns:
            Dict with call initiation result

        Raises:
            ValueError: If material or assistant not found
            Exception: If call initiation fails
        """
        # Get material with assistant
        material = await MaterialService.get_material_by_id(material_id, organization_id)
        if not material:
            raise ValueError(f"Material not found: {material_id}")

        assistant_id = material.metadata.get("vapi_assistant_id") if material.metadata else None
        if not assistant_id:
            raise ValueError(f"No VAPI assistant found for material {material_id}. Create one first.")

        # Create study session
        from app.models.session import SessionCreate
        session_data = SessionCreate(
            organization_id=organization_id,
            school_id=material.school_id,
            student_id=student_id,
            subject=material.subject,
            topics=material.topics or [],
            metadata={
                "material_id": material_id,
                "vapi_assistant_id": assistant_id,
                "session_type": "vapi_voice"
            }
        )

        session = await TutoringService.create_session(session_data)

        # Initiate VAPI call
        vapi = VAPIDocumentTutoringService.get_vapi_service()
        call_result = await vapi.initiate_call(
            to_number=phone_number,
            assistant_id=assistant_id,
            metadata={
                "session_id": session.id,
                "student_id": student_id,
                "material_id": material_id,
                "organization_id": organization_id
            }
        )

        if not call_result.get("success"):
            raise Exception(f"Failed to initiate call: {call_result.get('error')}")

        logger.info(
            f"VAPI voice session started: session={session.id}, "
            f"call_id={call_result.get('call_id')}"
        )

        return {
            "success": True,
            "session_id": session.id,
            "call_id": call_result.get("call_id"),
            "status": call_result.get("status"),
            "material": {
                "id": material.id,
                "title": material.title,
                "subject": material.subject
            }
        }

    @staticmethod
    async def handle_function_call(
        function_name: str,
        arguments: Dict[str, Any],
        session_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Handle VAPI function calls from the assistant.

        Supported functions:
        - answer_from_knowledge_base: Query RAG for answers
        - generate_exercise: Create practice questions
        - evaluate_answer: Assess student responses

        Args:
            function_name: Name of the function to call
            arguments: Function arguments
            session_id: Current session ID
            organization_id: Organization ID

        Returns:
            Function result dict

        Raises:
            ValueError: If function not supported
        """
        logger.info(f"VAPI function call: {function_name} with args: {arguments}")

        if function_name == "answer_from_knowledge_base":
            return await VAPIDocumentTutoringService._answer_from_knowledge_base(
                question=arguments.get("question", ""),
                topic=arguments.get("topic"),
                session_id=session_id,
                organization_id=organization_id
            )

        elif function_name == "generate_exercise":
            return await VAPIDocumentTutoringService._generate_exercise(
                topic=arguments.get("topic", ""),
                difficulty=arguments.get("difficulty", "medium"),
                session_id=session_id,
                organization_id=organization_id
            )

        elif function_name == "evaluate_answer":
            return await VAPIDocumentTutoringService._evaluate_answer(
                question=arguments.get("question", ""),
                student_answer=arguments.get("student_answer", ""),
                correct_answer=arguments.get("correct_answer"),
                session_id=session_id,
                organization_id=organization_id
            )

        else:
            raise ValueError(f"Unsupported function: {function_name}")

    @staticmethod
    async def _answer_from_knowledge_base(
        question: str,
        topic: Optional[str],
        session_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Answer question using RAG knowledge base.

        Args:
            question: Student's question
            topic: Optional topic filter
            session_id: Current session ID
            organization_id: Organization ID

        Returns:
            Answer with sources and confidence
        """
        # Get session to get material info
        session = await TutoringService.get_session(session_id, organization_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        # Get collection name
        collection_name = TutoringService.get_collection_name_for_subject(
            subject=session.subject,
            organization_id=organization_id
        )

        # Query RAG
        rag = VAPIDocumentTutoringService.get_rag_service()

        context = {
            "student_id": session.student_id,
            "subject": session.subject,
            "topic": topic or "",
            "session_id": session_id
        }

        filters = {"organization_id": organization_id}
        if topic:
            filters["topic"] = topic

        result = await rag.query_knowledge_base(
            collection_name=collection_name,
            query=question,
            context=context,
            filters=filters
        )

        # Create question record
        # Convert sources from dicts to strings
        sources = result.get("sources", [])
        sources_list = []
        for source in sources:
            if isinstance(source, dict):
                # Convert dict to string representation
                sources_list.append(f"Page {source.get('page', 'N/A')}: {source.get('content', '')[:100]}")
            else:
                sources_list.append(str(source))

        question_obj = Question(
            session_id=session_id,
            student_id=session.student_id,
            subject=session.subject,
            topic=topic,
            question_text=question,
            question_type=QuestionType.VOICE,
            answer_text=result.get("response", ""),
            confidence_score=result.get("confidence_score", 0.0),
            sources_used=sources_list,
            tokens_used=result.get("tokens_used", 0),
            cost=result.get("cost", 0.0),
            metadata={"vapi_function_call": True}
        )

        collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        db_result = await collection.insert_one(question_obj.dict(by_alias=True, exclude={"id"}))
        question_obj.id = str(db_result.inserted_id)

        # Update session stats
        await TutoringService._update_session_stats(
            session_id,
            questions_increment=1,
            cost_increment=question_obj.cost
        )

        logger.info(f"Knowledge base answer: question_id={question_obj.id}")

        return {
            "success": True,
            "answer": result.get("response", ""),
            "confidence": result.get("confidence_score", 0.0),
            "sources": result.get("sources", [])
        }

    @staticmethod
    async def _generate_exercise(
        topic: str,
        difficulty: str,
        session_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Generate practice exercise for the student.

        Args:
            topic: Topic for the exercise
            difficulty: Difficulty level (easy/medium/hard)
            session_id: Current session ID
            organization_id: Organization ID

        Returns:
            Generated exercise
        """
        # Get session
        session = await TutoringService.get_session(session_id, organization_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        # Get material ID from session
        material_id = session.metadata.get("material_id") if session.metadata else None
        if not material_id:
            return {
                "success": False,
                "error": "No material associated with session"
            }

        # Generate exercise using ExerciseService
        from app.models.exercise import ExerciseGenerateRequest, QuestionType as ExerciseQuestionType

        generate_request = ExerciseGenerateRequest(
            material_id=material_id,
            topics=[topic],
            difficulty=difficulty,
            num_questions=3,  # Start with 3 questions for voice
            question_types=[ExerciseQuestionType.MULTIPLE_CHOICE, ExerciseQuestionType.SHORT_ANSWER]
        )

        exercise = await ExerciseService.generate_exercise(
            generate_request,
            organization_id,
            session.student_id
        )

        logger.info(f"Exercise generated: exercise_id={exercise.id}")

        # Format questions for voice response
        questions_text = []
        for idx, q in enumerate(exercise.questions, 1):
            questions_text.append(
                f"Question {idx}: {q.question_text}\n"
                + (f"Options: {', '.join(q.options)}" if q.options else "")
            )

        return {
            "success": True,
            "exercise_id": exercise.id,
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": len(exercise.questions),
            "questions": "\n\n".join(questions_text),
            "message": f"I've generated {len(exercise.questions)} practice questions on {topic}. Would you like to try them?"
        }

    @staticmethod
    async def _evaluate_answer(
        question: str,
        student_answer: str,
        correct_answer: Optional[str],
        session_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate student's answer to a question.

        Args:
            question: The question asked
            student_answer: Student's answer
            correct_answer: Expected correct answer (optional)
            session_id: Current session ID
            organization_id: Organization ID

        Returns:
            Evaluation result with feedback
        """
        # Get session
        session = await TutoringService.get_session(session_id, organization_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        # Use RAG to evaluate answer quality
        rag = VAPIDocumentTutoringService.get_rag_service()

        evaluation_prompt = f"""Evaluate this student's answer:

Question: {question}
Student's Answer: {student_answer}
{f"Expected Answer: {correct_answer}" if correct_answer else ""}

Provide:
1. Is the answer correct/partially correct/incorrect?
2. What did the student get right?
3. What could be improved?
4. Constructive feedback to help them learn

Be encouraging and supportive."""

        collection_name = TutoringService.get_collection_name_for_subject(
            subject=session.subject,
            organization_id=organization_id
        )

        result = await rag.query_knowledge_base(
            collection_name=collection_name,
            query=evaluation_prompt,
            context={"session_id": session_id},
            filters={"organization_id": organization_id}
        )

        evaluation = result.get("response", "")

        # Determine if answer is correct (simple heuristic)
        is_correct = "correct" in evaluation.lower() and "incorrect" not in evaluation.lower()

        logger.info(f"Answer evaluated: session={session_id}, correct={is_correct}")

        return {
            "success": True,
            "is_correct": is_correct,
            "feedback": evaluation,
            "encouragement": "Great effort!" if is_correct else "Keep trying! You're learning!"
        }

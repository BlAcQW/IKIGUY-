"""
Voice Tutoring Service for StudyFlow.

Provides conversational AI tutoring with voice interaction using the shared
ConversationalVoiceService infrastructure.

Features:
- Voice-to-voice tutoring sessions
- Organization-scoped knowledge bases
- Material-specific RAG filtering (material_id in rag_filters)
- Dynamic prompts with material title/topics
- Conversation history for context continuity
- Session tracking and analytics
- Cost tracking and wallet integration
- Multi-language support
"""

import logging
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.conversational_voice_service import (
    ConversationalVoiceService,
    VoiceConversationRequest,
    VoiceConversationResult
)
from apps.shared.integration.rag import RAGConfig
from apps.shared.services.voice_settings_service import VoiceSettingsService, VoiceSettings

from app.models.session import StudySession
from app.models.question import Question, QuestionType
from app.models.material import StudyMaterial
from app.core.database import mongodb, MongoDB, COLLECTION_QUESTIONS, COLLECTION_SESSIONS, COLLECTION_MATERIALS
from app.services.tutoring_service import TutoringService
from app.services.progress_service import ProgressService
from app.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)


class VoiceTutoringService:
    """
    Voice tutoring service for StudyFlow.

    Wraps the shared ConversationalVoiceService with StudyFlow-specific
    business logic for tutoring sessions, progress tracking, and analytics.
    """

    _voice_service: Optional[ConversationalVoiceService] = None

    @classmethod
    def get_voice_service(cls) -> ConversationalVoiceService:
        """
        Get or create conversational voice service instance.

        Returns:
            ConversationalVoiceService instance
        """
        if cls._voice_service is None:
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

            cls._voice_service = ConversationalVoiceService(rag_config=rag_config)
            logger.info("✓ ConversationalVoiceService initialized for voice tutoring")

        return cls._voice_service

    @classmethod
    async def initialize(cls):
        """Initialize the voice tutoring service."""
        service = cls.get_voice_service()
        await service.initialize()
        logger.info("✅ VoiceTutoringService ready")

    @staticmethod
    async def get_user_voice_settings(
        user_id: str,
        organization_id: str
    ) -> Optional[VoiceSettings]:
        """
        Get user's voice settings from database.

        Retrieves the user's TTS, ASR, and LLM preferences configured
        in the Voice Settings page.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            VoiceSettings object or None if not found
        """
        try:
            db = MongoDB.get_database()
            voice_settings_service = VoiceSettingsService(db)
            voice_settings = await voice_settings_service.get_settings(user_id, organization_id)
            return voice_settings
        except Exception as e:
            logger.warning(f"Could not get voice settings for user {user_id}: {e}")
            return None

    @staticmethod
    async def get_material_by_id(
        material_id: str,
        organization_id: str
    ) -> Optional[StudyMaterial]:
        """
        Get material by ID with organization scoping.

        Args:
            material_id: Material ID
            organization_id: Organization ID for access control

        Returns:
            StudyMaterial if found and accessible, None otherwise
        """
        try:
            collection = mongodb.get_collection(COLLECTION_MATERIALS)
            material_doc = await collection.find_one({
                "_id": ObjectId(material_id),
                "organization_id": organization_id
            })

            if material_doc:
                # Convert ObjectId to string for Pydantic
                material_doc["_id"] = str(material_doc["_id"])
                return StudyMaterial(**material_doc)
            return None
        except Exception as e:
            logger.warning(f"Failed to get material {material_id}: {str(e)}")
            return None

    @staticmethod
    async def get_conversation_history(
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Load conversation history from previous questions in the session.

        Args:
            session_id: Session ID
            limit: Maximum number of previous exchanges to load

        Returns:
            List of conversation messages in format [{"role": "user"/"assistant", "content": "..."}]
        """
        try:
            collection = mongodb.get_collection(COLLECTION_QUESTIONS)
            # Sort by created_at ascending to get chronological order
            cursor = collection.find(
                {"session_id": session_id}
            ).sort("created_at", 1).limit(limit)

            history = []
            async for question_doc in cursor:
                # Add user question
                history.append({
                    "role": "user",
                    "content": question_doc.get("question_text", "")
                })
                # Add assistant answer
                history.append({
                    "role": "assistant",
                    "content": question_doc.get("answer_text", "")
                })

            return history
        except Exception as e:
            logger.warning(f"Failed to load conversation history for session {session_id}: {str(e)}")
            return []

    @staticmethod
    def build_material_aware_prompt(
        material: Optional[StudyMaterial],
        session: StudySession,
        base_prompt: Optional[str] = None
    ) -> str:
        """
        Build a custom prompt enhanced with material context.

        Args:
            material: StudyMaterial if session is material-based
            session: Current study session
            base_prompt: Optional base prompt to enhance

        Returns:
            Enhanced prompt string with material context
        """
        # Start with base tutoring prompt
        prompt_parts = []

        # Add material context if available
        if material:
            prompt_parts.append(f"You are an AI tutor helping a student learn from the document: \"{material.title}\".")
            if material.description:
                prompt_parts.append(f"Document description: {material.description}")
            if material.topics:
                topics_str = ", ".join(material.topics)
                prompt_parts.append(f"Topics covered in this material: {topics_str}")
            prompt_parts.append(f"Subject: {material.subject}")
            if material.grade:
                prompt_parts.append(f"Grade level: {material.grade}")
        else:
            prompt_parts.append(f"You are an AI tutor helping a student learn {session.subject}.")

        # Add session topics if available
        if session.topics and not material:
            topics_str = ", ".join(session.topics)
            prompt_parts.append(f"Current topics: {topics_str}")

        # Add tutoring guidelines
        prompt_parts.append("""
Based on the knowledge base information:

1. Provide clear, educational answers directly from the study material
2. Break down complex concepts step-by-step
3. Use examples from the material to illustrate points
4. Encourage the student's learning
5. If the question is unclear, ask for clarification
6. Reference specific sections of the material when possible
7. Stay focused on the material content - don't invent information

Context from knowledge base:
{context}

Question: {query}

Answer (be concise and educational):""")

        return "\n".join(prompt_parts)

    @staticmethod
    async def process_voice_question(
        session_id: str,
        audio_base64: str,
        organization_id: str,
        user_id: str,
        asr_provider_id: Optional[str] = None,
        tts_provider_id: Optional[str] = None,
        tts_voice_id: Optional[str] = None,
        tts_speed: Optional[float] = None,
        tts_pitch: Optional[float] = None,
        language: Optional[str] = None,
        include_history: bool = True,
        history_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Process a voice question in a tutoring session.

        Uses the user's voice settings from the Voice Settings page for:
        - TTS: provider, voice, speed, pitch
        - ASR: provider, language
        - LLM: temperature, max_tokens

        Args:
            session_id: Active study session ID
            audio_base64: Base64-encoded audio question
            organization_id: Organization ID
            user_id: Student user ID
            asr_provider_id: ASR provider override (uses voice settings if None)
            tts_provider_id: TTS provider override (uses voice settings if None)
            tts_voice_id: TTS voice ID override (uses voice settings if None)
            tts_speed: TTS speed override (uses voice settings if None)
            tts_pitch: TTS pitch override (uses voice settings if None)
            language: Language code override (uses voice settings if None)
            include_history: Whether to include conversation history
            history_limit: Maximum number of previous exchanges to include

        Returns:
            Dict with transcription, response, audio, and session info

        Raises:
            ValueError: If session not found or invalid
            Exception: If processing fails
        """
        # Get session
        session = await TutoringService.get_session(session_id, organization_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != "active":
            raise ValueError(f"Session is not active: {session.status}")

        # Get material_id from session metadata (if session is material-based)
        material_id = session.metadata.get("material_id") if session.metadata else None
        material: Optional[StudyMaterial] = None

        if material_id:
            material = await VoiceTutoringService.get_material_by_id(
                material_id=material_id,
                organization_id=organization_id
            )
            if material:
                logger.info(f"Voice tutoring with material: {material.title} (ID: {material_id})")

        # Get user's voice settings from Voice Settings page
        voice_settings = await VoiceTutoringService.get_user_voice_settings(user_id, organization_id)

        # Apply TTS settings from Voice Settings page
        llm_max_tokens = 500  # Default for tutoring
        llm_temperature = 0.1  # Default temperature
        if voice_settings:
            tts_settings = voice_settings.tts
            if not tts_provider_id:
                tts_provider_id = tts_settings.default_provider or "coqui_xtts"
            if not tts_voice_id:
                tts_voice_id = tts_settings.default_voice
            if tts_speed is None:
                tts_speed = tts_settings.speed or 1.0
            if tts_pitch is None:
                tts_pitch = tts_settings.pitch or 0.0

            # Apply ASR settings from Voice Settings page
            asr_settings = voice_settings.asr
            if not asr_provider_id:
                asr_provider_id = asr_settings.default_provider or "faster_whisper_large"
            if not language:
                language = asr_settings.language or "en"

            # Get LLM settings for temperature and max_tokens
            llm_settings = voice_settings.llm
            llm_temperature = llm_settings.temperature if llm_settings.temperature is not None else 0.1
            # Reason: Cap LLM output to ensure TTS can synthesize (XTTS ~400 token limit)
            llm_max_tokens = min(llm_settings.max_tokens or 500, 500)

            logger.info(
                f"Using voice settings for user {user_id}: "
                f"TTS={tts_provider_id}/{tts_voice_id} speed={tts_speed} pitch={tts_pitch}, "
                f"ASR={asr_provider_id} lang={language}, "
                f"LLM temp={llm_temperature} max_tokens={llm_max_tokens}"
            )
        else:
            # Fallback to defaults if no voice settings found
            logger.warning(f"No voice settings found for user {user_id}, using defaults")
            tts_provider_id = tts_provider_id or "coqui_xtts"
            tts_speed = tts_speed if tts_speed is not None else 0.9
            tts_pitch = tts_pitch if tts_pitch is not None else 0.0
            asr_provider_id = asr_provider_id or "whisper_large_v3"
            language = language or "en"

        # Get collection name for subject
        collection_name = TutoringService.get_collection_name_for_subject(
            session.subject,
            grade=material.grade if material else None,
            organization_id=organization_id
        )

        # Build RAG filters - include material_id for precise filtering
        rag_filters: Dict[str, Any] = {"organization_id": organization_id}
        if material_id:
            rag_filters["material_id"] = material_id
            logger.debug(f"RAG filtering by material_id: {material_id}")

        # Build context
        context = {
            "session_id": session_id,
            "student_id": session.student_id,
            "subject": session.subject,
            "topics": session.topics,
            "organization_id": organization_id
        }

        # Add material context if available
        if material:
            context["material_id"] = material_id
            context["material_title"] = material.title
            context["material_topics"] = material.topics
            if material.grade:
                context["grade"] = material.grade

        # Build enhanced custom prompt with material context
        custom_prompt = VoiceTutoringService.build_material_aware_prompt(
            material=material,
            session=session
        )

        # Load conversation history for context continuity
        conversation_history: Optional[List[Dict[str, str]]] = None
        if include_history:
            conversation_history = await VoiceTutoringService.get_conversation_history(
                session_id=session_id,
                limit=history_limit
            )
            if conversation_history:
                logger.debug(f"Loaded {len(conversation_history)} history messages for context")

        # Process voice message
        voice_service = VoiceTutoringService.get_voice_service()

        request = VoiceConversationRequest(
            audio_base64=audio_base64,
            collection_name=collection_name,
            organization_id=organization_id,
            context=context,
            conversation_history=conversation_history,
            asr_provider_id=asr_provider_id,
            asr_language=language,
            tts_provider_id=tts_provider_id,
            tts_voice_id=tts_voice_id,  # Use voice from Voice Settings
            tts_language=language,
            tts_speed=tts_speed,  # Use speed from Voice Settings
            tts_pitch=tts_pitch,  # Use pitch from Voice Settings
            rag_filters=rag_filters,
            custom_prompt=custom_prompt,
            max_tokens=llm_max_tokens,  # Use max_tokens from Voice Settings
            temperature=llm_temperature  # Use temperature from Voice Settings
        )

        result: VoiceConversationResult = await voice_service.process_voice_message(
            user_id=user_id,
            request=request,
            organization_id=organization_id
        )

        # Build question metadata with material info
        question_metadata = {
            "asr_provider": asr_provider_id,
            "tts_provider": tts_provider_id,
            "language": language,
            "asr_cost": result.asr_cost,
            "tts_cost": result.tts_cost,
            "total_cost": result.total_cost,
            "detected_language": result.detected_language,
            "audio_duration": result.audio_duration,
            "asr_transaction_id": result.asr_transaction_id,
            "tts_transaction_id": result.tts_transaction_id
        }

        # Add material info to metadata if available
        if material:
            question_metadata["material_id"] = material_id
            question_metadata["material_title"] = material.title

        # Determine topic from material or session
        topic = None
        if material and material.topics:
            topic = material.topics[0]  # Use first topic from material
        elif session.topics:
            topic = session.topics[0]  # Use first topic from session

        # Create question record
        question = Question(
            session_id=session_id,
            student_id=session.student_id,
            subject=session.subject,
            topic=topic,
            question_text=result.transcribed_text,
            question_type=QuestionType.VOICE,
            answer_text=result.response_text,
            confidence_score=result.confidence_score,
            sources_used=result.sources_used,
            tokens_used=0,  # TODO: Track from RAG
            cost=result.llm_cost,
            response_time_ms=int(result.total_processing_time * 1000),
            metadata=question_metadata
        )

        # Save question to database
        collection = mongodb.get_collection(COLLECTION_QUESTIONS)
        db_result = await collection.insert_one(question.dict(by_alias=True, exclude={"id"}))
        question.id = str(db_result.inserted_id)

        # Update session stats
        await TutoringService._update_session_stats(
            session_id,
            questions_increment=1,
            cost_increment=result.total_cost
        )

        # Update progress tracking
        await ProgressService.update_progress_after_question(question.id)

        logger.info(
            f"Voice question processed: session={session_id}, "
            f"question_id={question.id}, material_id={material_id or 'none'}, "
            f"cost=${result.total_cost:.4f}"
        )

        # Build response with material context
        response = {
            "question_id": question.id,
            "transcribed_text": result.transcribed_text,
            "detected_language": result.detected_language,
            "response_text": result.response_text,
            "response_audio_base64": result.response_audio_base64,
            "audio_duration": result.audio_duration,
            "confidence_score": result.confidence_score,
            "sources": result.sources_used,
            "cost_breakdown": {
                "asr": result.asr_cost,
                "llm": result.llm_cost,
                "tts": result.tts_cost,
                "total": result.total_cost
            },
            "performance": {
                "asr_time": result.asr_processing_time,
                "rag_time": result.rag_processing_time,
                "tts_time": result.tts_processing_time,
                "total_time": result.total_processing_time
            }
        }

        # Add material context to response if available
        if material:
            response["material"] = {
                "id": material_id,
                "title": material.title,
                "subject": material.subject,
                "topics": material.topics,
                "grade": material.grade
            }

        # Add conversation history info
        if conversation_history:
            response["history_used"] = len(conversation_history)

        return response

    @staticmethod
    async def get_available_voice_providers() -> Dict[str, Any]:
        """
        Get available ASR and TTS providers for voice tutoring.

        Returns:
            Dict with provider information and health status
        """
        voice_service = VoiceTutoringService.get_voice_service()
        return await voice_service.get_available_providers()

    @staticmethod
    async def estimate_voice_cost(
        audio_duration_seconds: float,
        expected_response_length: int = 500,
        asr_provider_id: str = "whisper_large_v3",  # Self-hosted at whisper.ailabsafrica.com
        tts_provider_id: str = "coqui_xtts"
    ) -> Dict[str, float]:
        """
        Estimate cost for a voice tutoring interaction.

        Args:
            audio_duration_seconds: Student's audio question duration
            expected_response_length: Expected character count of response
            asr_provider_id: ASR provider
            tts_provider_id: TTS provider

        Returns:
            Cost estimate breakdown
        """
        voice_service = VoiceTutoringService.get_voice_service()
        return await voice_service.estimate_cost(
            audio_duration_seconds,
            expected_response_length,
            asr_provider_id,
            tts_provider_id
        )

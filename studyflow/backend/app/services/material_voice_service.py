"""
Material Voice Service for StudyFlow.

Provides voice interaction directly with study materials using their
RAG embeddings. This enables browser-based voice chat without requiring
a tutoring session.

Features:
- Voice-to-voice chat with documents
- Uses user's voice settings for TTS/ASR/LLM
- Full integration with Voice Settings page preferences
- Conversation history tracking
- Cost tracking and wallet integration
"""

import logging
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.conversational_voice_service import (
    ConversationalVoiceService,
    VoiceConversationRequest,
    VoiceConversationResult
)
from apps.shared.integration.rag import RAGConfig
from apps.shared.services.voice_settings_service import VoiceSettingsService, VoiceSettings

from app.core.database import mongodb, MongoDB, COLLECTION_MATERIALS
from app.config import settings

logger = logging.getLogger(__name__)

# Collection for voice chat history
COLLECTION_VOICE_CHAT_HISTORY = "voice_chat_history"


class MaterialVoiceService:
    """
    Voice service for direct material interaction.

    Allows students to have voice conversations about specific
    study materials using browser-based audio.
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

            # Reason: Disable billing for now as users may not have wallets configured
            # Billing can be enabled later when wallet infrastructure is fully set up
            cls._voice_service = ConversationalVoiceService(
                rag_config=rag_config,
                enable_billing=False  # Disabled until wallet system is properly integrated
            )
            logger.info("✓ ConversationalVoiceService initialized for material voice chat (billing disabled)")

        return cls._voice_service

    @classmethod
    async def initialize(cls):
        """Initialize the material voice service."""
        service = cls.get_voice_service()
        await service.initialize()
        logger.info("✅ MaterialVoiceService ready")

    @staticmethod
    async def get_user_voice_settings(
        user_id: str,
        organization_id: str
    ) -> Optional[VoiceSettings]:
        """
        Get user's voice settings from database.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            VoiceSettings object or None if not found
        """
        try:
            db = MongoDB.get_database()
            voice_settings_service = VoiceSettingsService(db)
            settings = await voice_settings_service.get_settings(user_id, organization_id)
            return settings
        except Exception as e:
            logger.warning(f"Could not get voice settings for user {user_id}: {e}")
            return None

    @staticmethod
    async def get_material(
        material_id: str,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get material by ID with organization scoping.

        Args:
            material_id: Material ID
            organization_id: Organization ID

        Returns:
            Material document or None
        """
        collection = mongodb.get_collection(COLLECTION_MATERIALS)

        try:
            material = await collection.find_one({
                "_id": ObjectId(material_id),
                "organization_id": organization_id
            })
            return material
        except Exception as e:
            logger.error(f"Error fetching material {material_id}: {e}")
            return None

    @staticmethod
    async def process_voice_question(
        material_id: str,
        audio_base64: str,
        organization_id: str,
        user_id: str,
        asr_provider_id: Optional[str] = None,
        tts_provider_id: Optional[str] = None,
        tts_voice_id: Optional[str] = None,
        tts_speed: Optional[float] = None,
        tts_pitch: Optional[float] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a voice question about a specific material.

        Uses the user's voice settings from the Voice Settings page for:
        - TTS: provider, voice, speed, pitch
        - ASR: provider, language
        - LLM: temperature, max_tokens

        Args:
            material_id: Study material ID
            audio_base64: Base64-encoded audio question
            organization_id: Organization ID
            user_id: User ID
            asr_provider_id: ASR provider override (uses voice settings if None)
            tts_provider_id: TTS provider override (uses voice settings if None)
            tts_voice_id: TTS voice ID override (uses voice settings if None)
            tts_speed: TTS speed override (uses voice settings if None)
            tts_pitch: TTS pitch override (uses voice settings if None)
            language: Language code override (uses voice settings if None)

        Returns:
            Dict with transcription, response, audio, and metadata

        Raises:
            ValueError: If material not found or not processed
        """
        # Get material
        material = await MaterialVoiceService.get_material(material_id, organization_id)
        if not material:
            raise ValueError(f"Material not found: {material_id}")

        # Check material has embeddings
        embedding_collection = material.get("embedding_collection")
        if not embedding_collection:
            raise ValueError(f"Material has not been processed yet: {material_id}")

        # Get user's voice settings from Voice Settings page
        voice_settings = await MaterialVoiceService.get_user_voice_settings(user_id, organization_id)

        # Apply TTS settings from Voice Settings page
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
            # Reason: XTTS has ~400 token limit, so cap LLM output to ensure TTS can synthesize
            llm_max_tokens = min(llm_settings.max_tokens or 300, 300)

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
            tts_speed = tts_speed if tts_speed is not None else 1.0
            tts_pitch = tts_pitch if tts_pitch is not None else 0.0
            asr_provider_id = asr_provider_id or "faster_whisper_large"
            language = language or "en"
            llm_temperature = 0.1
            llm_max_tokens = 300

        # Build context
        material_title = material.get("title", "Study Material")
        material_subject = material.get("subject", "General")
        material_topics = material.get("topics", [])

        # Get recent conversation history for context (last 5 exchanges)
        recent_history = await MaterialVoiceService.get_chat_history(
            material_id=material_id,
            organization_id=organization_id,
            user_id=user_id,
            limit=5
        )

        # Format conversation history for the prompt
        conversation_context = ""
        if recent_history:
            conversation_context = "\n\nRecent conversation:\n"
            for entry in recent_history:
                q_text = entry.get("question_text", "")[:200]  # Limit length
                a_text = entry.get("answer_text", "")[:300]
                conversation_context += f"Student: {q_text}\nTutor: {a_text}\n\n"

        context = {
            "material_id": material_id,
            "material_title": material_title,
            "subject": material_subject,
            "topics": material_topics,
            "organization_id": organization_id,
            "has_conversation_history": len(recent_history) > 0
        }

        # Build custom prompt for document Q&A with conversation context
        # Reason: Keep responses short to stay within XTTS 400 token limit
        topics_str = ", ".join(material_topics[:5]) if material_topics else "various topics"
        custom_prompt = f"""You are an AI tutor helping a student understand "{material_title}" ({material_subject}).
Topics: {topics_str}.
{conversation_context}
Answer based on the document content below. Be concise and clear.

IMPORTANT: Keep your response brief (2-4 sentences max). Focus on the key point.

Document content:
{{context}}

Question: {{query}}

Brief answer:"""

        # Process voice message
        voice_service = MaterialVoiceService.get_voice_service()

        # Reason: XTTS has a 400 token limit, so we limit LLM output to ~300 tokens
        # to ensure the TTS can synthesize the full response
        # Reason: Add material_id filter to ensure RAG only retrieves chunks from
        # this specific document, not other documents in the same collection
        request = VoiceConversationRequest(
            audio_base64=audio_base64,
            collection_name=embedding_collection,
            organization_id=organization_id,
            context=context,
            rag_filters={"material_id": material_id},  # Filter by specific material
            asr_provider_id=asr_provider_id,
            asr_language=language,
            tts_provider_id=tts_provider_id,
            tts_voice_id=tts_voice_id,
            tts_language=language,
            tts_speed=tts_speed,
            tts_pitch=tts_pitch,  # Apply pitch from Voice Settings
            custom_prompt=custom_prompt,
            max_tokens=llm_max_tokens,  # Use max_tokens from Voice Settings
            temperature=llm_temperature  # Use temperature from Voice Settings
        )

        result: VoiceConversationResult = await voice_service.process_voice_message(
            user_id=user_id,
            request=request,
            organization_id=organization_id
        )

        # Save to chat history
        chat_entry = {
            "material_id": material_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "question_text": result.transcribed_text,
            "question_language": result.detected_language,
            "answer_text": result.response_text,
            "confidence_score": result.confidence_score,
            "sources_used": result.sources_used,
            "asr_provider": asr_provider_id,
            "tts_provider": tts_provider_id,
            "tts_voice": tts_voice_id,
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
            },
            "created_at": datetime.utcnow()
        }

        history_collection = mongodb.get_collection(COLLECTION_VOICE_CHAT_HISTORY)
        db_result = await history_collection.insert_one(chat_entry)
        chat_id = str(db_result.inserted_id)

        logger.info(
            f"Material voice chat processed: material={material_id}, "
            f"chat_id={chat_id}, cost=${result.total_cost:.4f}"
        )

        return {
            "chat_id": chat_id,
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

    @staticmethod
    async def get_chat_history(
        material_id: str,
        organization_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a material.

        Args:
            material_id: Material ID
            organization_id: Organization ID
            user_id: User ID
            limit: Maximum entries to return

        Returns:
            List of chat history entries
        """
        collection = mongodb.get_collection(COLLECTION_VOICE_CHAT_HISTORY)

        cursor = collection.find({
            "material_id": material_id,
            "organization_id": organization_id,
            "user_id": user_id
        }).sort("created_at", -1).limit(limit)

        history = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            history.append(doc)

        return list(reversed(history))  # Return oldest first

    @staticmethod
    async def clear_chat_history(
        material_id: str,
        organization_id: str,
        user_id: str
    ) -> int:
        """
        Clear chat history for a material.

        Args:
            material_id: Material ID
            organization_id: Organization ID
            user_id: User ID

        Returns:
            Number of entries deleted
        """
        collection = mongodb.get_collection(COLLECTION_VOICE_CHAT_HISTORY)

        result = await collection.delete_many({
            "material_id": material_id,
            "organization_id": organization_id,
            "user_id": user_id
        })

        logger.info(f"Cleared {result.deleted_count} chat history entries for material {material_id}")
        return result.deleted_count

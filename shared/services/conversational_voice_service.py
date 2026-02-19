"""
Conversational Voice Service - Unified Voice Chat with RAG Integration

Provides complete conversational voice capabilities by combining:
- ASR (Automatic Speech Recognition)
- RAG (Retrieval-Augmented Generation) with LLM
- TTS (Text-to-Speech)
- Real-time streaming support

This service can be used by any app (StudyFlow, Inkwave, ChurchFlow, etc.) to add
voice chat capabilities with domain-specific knowledge bases.

Architecture:
    User Voice Input
        ↓
    ASRProviderService → Text
        ↓
    ConversationalVoiceService → RAGService + LLM → Response Text
        ↓
    TTSProviderService → Audio Response
        ↓
    User Audio Output

Usage Example:
    ```python
    from apps.shared.services.conversational_voice_service import (
        ConversationalVoiceService,
        VoiceConversationRequest,
        VoiceConversationResult
    )

    service = ConversationalVoiceService()
    await service.initialize()

    result = await service.process_voice_message(
        user_id="user_123",
        request=VoiceConversationRequest(
            audio_base64="...",
            collection_name="studyflow_ailabs_mathematics",
            context={"student_id": "...", "subject": "mathematics"},
            asr_provider_id="openai_whisper",
            tts_provider_id="coqui_xtts",
            language="en"
        )
    )
    ```

Author: AI Labs Africa
Created: 2025-11-07
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import sys

# Add shared services to path
sys.path.insert(0, "/opt/kasaai/apps")

from apps.shared.services.asr_provider_service import (
    ASRProviderService,
    TranscriptionRequest,
    TranscriptionResult
)
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult
)
from apps.shared.integration.rag import RAGService, RAGConfig

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class VoiceConversationRequest(BaseModel):
    """Request for voice conversation processing."""
    audio_base64: str = Field(..., description="Base64-encoded audio input")
    collection_name: str = Field(..., description="RAG collection to query")
    organization_id: Optional[str] = Field(None, description="Organization ID for filtering")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for RAG")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous messages")

    # ASR settings
    asr_provider_id: str = Field("openai_whisper", description="ASR provider to use")
    asr_language: Optional[str] = Field(None, description="Language code (auto-detect if None)")

    # TTS settings
    tts_provider_id: str = Field("coqui_xtts", description="TTS provider to use")
    tts_voice_id: Optional[str] = Field(None, description="Voice ID for TTS")
    tts_language: str = Field("en", description="TTS output language")
    tts_speed: float = Field(0.9, description="TTS playback speed")
    tts_pitch: float = Field(0.0, ge=-1.0, le=1.0, description="TTS pitch adjustment (-1.0 to 1.0)")

    # RAG settings
    rag_filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters for RAG")
    custom_prompt: Optional[str] = Field(None, description="Custom system prompt for LLM")
    max_tokens: int = Field(500, description="Maximum tokens for LLM response")
    temperature: float = Field(0.1, description="LLM temperature")


class VoiceConversationResult(BaseModel):
    """Result from voice conversation processing."""
    # Input processing
    transcribed_text: str = Field(..., description="User's transcribed speech")
    transcription_confidence: Optional[float] = Field(None, description="ASR confidence")
    detected_language: Optional[str] = Field(None, description="Detected input language")

    # LLM response
    response_text: str = Field(..., description="AI response text")
    confidence_score: float = Field(..., description="RAG confidence score")
    sources_used: List[str] = Field(default_factory=list, description="Knowledge sources used")

    # Audio output
    response_audio_base64: str = Field(..., description="TTS audio response")
    audio_duration: float = Field(..., description="Audio duration in seconds")

    # Cost tracking
    asr_cost: float = Field(0.0, description="ASR processing cost")
    llm_cost: float = Field(0.0, description="LLM processing cost")
    tts_cost: float = Field(0.0, description="TTS synthesis cost")
    total_cost: float = Field(0.0, description="Total cost for this conversation turn")

    # Transaction IDs
    asr_transaction_id: Optional[str] = None
    tts_transaction_id: Optional[str] = None

    # Performance metrics
    asr_processing_time: float = Field(0.0, description="ASR time in seconds")
    rag_processing_time: float = Field(0.0, description="RAG time in seconds")
    tts_processing_time: float = Field(0.0, description="TTS time in seconds")
    total_processing_time: float = Field(0.0, description="Total time in seconds")


class StreamingVoiceChunk(BaseModel):
    """Chunk of streaming voice response."""
    type: str = Field(..., description="Chunk type: 'transcript', 'response_text', 'audio_chunk'")
    data: Any = Field(..., description="Chunk data")
    is_final: bool = Field(False, description="Is this the final chunk?")
    sequence: int = Field(..., description="Sequence number")


# ============================================================================
# Conversational Voice Service
# ============================================================================

class ConversationalVoiceService:
    """
    Unified conversational voice service with RAG integration.

    Features:
    - Complete voice-to-voice pipeline (ASR → RAG → TTS)
    - Multi-provider support for ASR and TTS
    - Organization-scoped knowledge bases
    - Automatic cost calculation and billing
    - Real-time streaming support
    - Multi-language support
    - Conversation history management
    """

    def __init__(
        self,
        rag_config: Optional[RAGConfig] = None,
        enable_billing: bool = True,
        enable_health_monitoring: bool = True
    ):
        """
        Initialize conversational voice service.

        Args:
            rag_config: RAG service configuration (optional, can be set later)
            enable_billing: Enable automatic wallet billing
            enable_health_monitoring: Enable provider health monitoring
        """
        self.enable_billing = enable_billing
        self.enable_health_monitoring = enable_health_monitoring

        # Initialize services
        self.asr_service: Optional[ASRProviderService] = None
        self.tts_service: Optional[TTSProviderService] = None
        self.rag_service: Optional[RAGService] = None

        # RAG configuration
        self._rag_config = rag_config

        logger.info("ConversationalVoiceService initialized")

    async def initialize(self, rag_config: Optional[RAGConfig] = None):
        """
        Initialize all dependent services.

        Args:
            rag_config: RAG configuration (required if not provided in __init__)
        """
        # Use provided config or stored config
        if rag_config:
            self._rag_config = rag_config

        if not self._rag_config:
            raise ValueError("RAG configuration is required")

        # Initialize ASR service
        self.asr_service = ASRProviderService(
            enable_billing=self.enable_billing,
            enable_health_monitoring=self.enable_health_monitoring
        )
        await self.asr_service.initialize()
        logger.info("✓ ASR service initialized")

        # Initialize TTS service
        self.tts_service = TTSProviderService(
            enable_billing=self.enable_billing,
            enable_health_monitoring=self.enable_health_monitoring
        )
        await self.tts_service.initialize()
        logger.info("✓ TTS service initialized")

        # Initialize RAG service
        self.rag_service = RAGService(self._rag_config)
        logger.info("✓ RAG service initialized")

        logger.info("✅ ConversationalVoiceService fully initialized")

    async def process_voice_message(
        self,
        user_id: str,
        request: VoiceConversationRequest,
        organization_id: Optional[str] = None
    ) -> VoiceConversationResult:
        """
        Process a complete voice conversation turn: ASR → RAG → TTS.

        Args:
            user_id: User ID for billing
            request: Voice conversation request
            organization_id: Organization ID for scoping (optional, can be in request)

        Returns:
            Complete voice conversation result with transcription, response, and audio

        Raises:
            ValueError: If services not initialized
            Exception: If processing fails
        """
        if not self.asr_service or not self.tts_service or not self.rag_service:
            raise ValueError("Service not initialized. Call initialize() first.")

        start_time = datetime.utcnow()

        # Use organization_id from parameter or request
        org_id = organization_id or request.organization_id

        logger.info(
            f"🎤 Voice conversation started for user {user_id}, "
            f"collection={request.collection_name}, org={org_id}"
        )

        # ========================================================================
        # Step 1: Transcribe audio (ASR)
        # ========================================================================
        asr_start = datetime.utcnow()

        transcription = await self.asr_service.transcribe(
            user_id=user_id,
            request=TranscriptionRequest(
                provider_id=request.asr_provider_id,
                audio_base64=request.audio_base64,
                language=request.asr_language,
                task="transcribe",
                response_format="json"
            )
        )

        asr_time = (datetime.utcnow() - asr_start).total_seconds()
        logger.info(
            f"📝 Transcription: '{transcription.text[:100]}...' "
            f"(language={transcription.language}, time={asr_time:.2f}s)"
        )

        # ========================================================================
        # Step 2: Query RAG and get LLM response
        # ========================================================================
        rag_start = datetime.utcnow()

        # Build context
        context = request.context or {}
        context["user_id"] = user_id
        if org_id:
            context["organization_id"] = org_id

        # Build filters for organization scoping
        filters = request.rag_filters or {}
        if org_id:
            filters["organization_id"] = org_id

        # Query knowledge base
        rag_result = await self.rag_service.query_knowledge_base(
            collection_name=request.collection_name,
            query=transcription.text,
            context=context,
            filters=filters if filters else None,
            system_prompt_template=request.custom_prompt
        )

        rag_time = (datetime.utcnow() - rag_start).total_seconds()
        logger.info(
            f"🧠 RAG response: '{rag_result.response[:100]}...' "
            f"(confidence={rag_result.confidence_score:.2f}, time={rag_time:.2f}s)"
        )

        # ========================================================================
        # Step 3: Synthesize response to audio (TTS)
        # ========================================================================
        tts_start = datetime.utcnow()

        synthesis = await self.tts_service.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id=request.tts_provider_id,
                text=rag_result.response or "I couldn't generate a response.",
                language=request.tts_language,
                voice_id=request.tts_voice_id,
                speed=request.tts_speed,
                pitch=request.tts_pitch,  # Apply pitch from voice settings
                output_format="mp3"  # MP3 for better compression
            )
        )

        tts_time = (datetime.utcnow() - tts_start).total_seconds()
        logger.info(
            f"🔊 TTS generated: {synthesis.duration:.2f}s audio (time={tts_time:.2f}s)"
        )

        # ========================================================================
        # Calculate total metrics
        # ========================================================================
        total_time = (datetime.utcnow() - start_time).total_seconds()
        # Note: QueryResult doesn't have a cost attribute, LLM cost is tracked separately
        llm_cost = 0.0  # TODO: Add LLM cost tracking to RAG service if needed
        total_cost = transcription.cost + llm_cost + synthesis.cost

        logger.info(
            f"✅ Voice conversation completed in {total_time:.2f}s, "
            f"total cost=${total_cost:.4f}"
        )

        return VoiceConversationResult(
            # Transcription
            transcribed_text=transcription.text,
            transcription_confidence=None,  # Not always available
            detected_language=transcription.language,

            # Response
            response_text=rag_result.response,
            confidence_score=rag_result.confidence_score,
            sources_used=rag_result.sources_used,

            # Audio
            response_audio_base64=synthesis.audio_base64,
            audio_duration=synthesis.duration,

            # Costs
            asr_cost=transcription.cost,
            llm_cost=llm_cost,
            tts_cost=synthesis.cost,
            total_cost=total_cost,

            # Transactions
            asr_transaction_id=transcription.transaction_id,
            tts_transaction_id=synthesis.transaction_id,

            # Performance
            asr_processing_time=asr_time,
            rag_processing_time=rag_time,
            tts_processing_time=tts_time,
            total_processing_time=total_time
        )

    async def get_available_providers(self) -> Dict[str, Any]:
        """
        Get available ASR and TTS providers with health status.

        Returns:
            Dict with ASR and TTS provider information
        """
        if not self.asr_service or not self.tts_service:
            raise ValueError("Service not initialized")

        asr_providers = await self.asr_service.get_available_providers()
        tts_providers = await self.tts_service.get_available_providers()

        return {
            "asr_providers": asr_providers,
            "tts_providers": tts_providers,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def estimate_cost(
        self,
        transcription_duration_seconds: float,
        response_text_length: int,
        asr_provider_id: str = "openai_whisper",
        tts_provider_id: str = "coqui_xtts"
    ) -> Dict[str, float]:
        """
        Estimate cost for a voice conversation turn.

        Args:
            transcription_duration_seconds: Audio duration for ASR
            response_text_length: Character count for TTS
            asr_provider_id: ASR provider
            tts_provider_id: TTS provider

        Returns:
            Cost breakdown estimate
        """
        # This would integrate with usage calculator
        # For now, rough estimates based on typical costs

        asr_cost = transcription_duration_seconds * 0.0001  # ~$0.01 per minute
        llm_cost = (response_text_length / 1000) * 0.001   # ~$0.001 per 1K chars
        tts_cost = (response_text_length / 1000) * 0.005   # ~$0.005 per 1K chars

        return {
            "asr_cost": asr_cost,
            "llm_cost": llm_cost,
            "tts_cost": tts_cost,
            "total_cost": asr_cost + llm_cost + tts_cost,
            "provider_ids": {
                "asr": asr_provider_id,
                "tts": tts_provider_id
            }
        }

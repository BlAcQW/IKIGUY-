"""
Conversation Pipeline

Orchestrates the ASR -> LLM -> TTS pipeline for voice conversations.
Handles multi-turn context management and cost tracking.

Author: KasaAI Team
Date: 2025-11-26
"""

import logging
import uuid
import time
import base64
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime

from .models import (
    ConversationState,
    ConversationTurn,
    ConversationConfig,
    TurnResult,
    TurnRole,
)
from .manager import ConversationManager

logger = logging.getLogger(__name__)


class ConversationPipeline:
    """
    Orchestrates voice conversation pipeline.

    Processes: Audio Input -> ASR -> LLM -> TTS -> Audio Output
    Maintains conversation context across turns.
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        asr_service: Any = None,
        llm_service: Any = None,
        tts_client: Any = None,
    ):
        """
        Initialize the pipeline.

        Args:
            conversation_manager: Manager for conversation persistence
            asr_service: ASR provider service for transcription
            llm_service: LLM provider service for chat
            tts_client: TTS client for speech synthesis
        """
        self.manager = conversation_manager
        self.asr_service = asr_service
        self.llm_service = llm_service
        self.tts_client = tts_client

    async def process_voice_turn(
        self,
        conversation_id: str,
        audio_base64: str,
        user_id: Optional[str] = None,
        audio_format: str = "wav",
        generate_audio: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> TurnResult:
        """
        Process a complete voice turn.

        Pipeline: Audio -> Transcription -> LLM Response -> TTS -> Audio

        Args:
            conversation_id: Conversation ID
            audio_base64: Base64-encoded audio input
            user_id: User ID for access control
            audio_format: Format of input audio
            generate_audio: Whether to generate TTS audio
            context: Additional context for processing

        Returns:
            TurnResult with transcription, response, and optional audio
        """
        start_time = time.time()
        context = context or {}

        # Get conversation
        conversation = await self.manager.get_conversation(
            conversation_id, user_id
        )
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Initialize timing and cost tracking
        asr_time_ms = 0.0
        llm_time_ms = 0.0
        tts_time_ms = 0.0
        asr_cost = 0.0
        llm_cost = 0.0
        tts_cost = 0.0

        # Step 1: ASR - Transcribe audio
        asr_start = time.time()
        transcription_result = await self._transcribe_audio(
            audio_base64=audio_base64,
            audio_format=audio_format,
            config=conversation.config,
            context=context,
        )
        asr_time_ms = (time.time() - asr_start) * 1000

        user_text = transcription_result.get("text", "")
        detected_language = transcription_result.get("language")
        asr_confidence = transcription_result.get("confidence")
        asr_cost = transcription_result.get("cost", 0.0)

        if not user_text.strip():
            raise ValueError("No speech detected in audio")

        # Create user turn
        user_turn = ConversationTurn(
            id=f"turn_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role=TurnRole.USER,
            content=user_text,
            language=detected_language,
            asr_provider=conversation.config.asr_provider,
            asr_confidence=asr_confidence,
            cost_usd=asr_cost,
            processing_time_ms=asr_time_ms,
        )

        # Add user turn to conversation
        await self.manager.add_turn(conversation_id, user_turn, user_id)

        # Step 2: LLM - Generate response
        llm_start = time.time()

        # Refresh conversation to get updated history
        conversation = await self.manager.get_conversation(
            conversation_id, user_id
        )

        llm_result = await self._generate_response(
            conversation=conversation,
            user_text=user_text,
            context=context,
        )
        llm_time_ms = (time.time() - llm_start) * 1000

        assistant_text = llm_result.get("response", "")
        llm_tokens = llm_result.get("tokens", {})
        llm_cost = llm_result.get("cost", 0.0)

        # Step 3: TTS - Generate audio (optional)
        audio_base64_response = None
        audio_duration = None

        if generate_audio and conversation.config.auto_respond_with_audio:
            tts_start = time.time()
            tts_result = await self._synthesize_speech(
                text=assistant_text,
                config=conversation.config,
                context=context,
            )
            tts_time_ms = (time.time() - tts_start) * 1000

            audio_base64_response = tts_result.get("audio_base64")
            audio_duration = tts_result.get("duration")
            tts_cost = tts_result.get("cost", 0.0)

        # Create assistant turn
        assistant_turn = ConversationTurn(
            id=f"turn_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role=TurnRole.ASSISTANT,
            content=assistant_text,
            llm_model=conversation.config.llm_model,
            llm_tokens=llm_tokens,
            tts_provider=conversation.config.tts_provider if generate_audio else None,
            cost_usd=llm_cost + tts_cost,
            processing_time_ms=llm_time_ms + tts_time_ms,
        )

        # Add assistant turn to conversation
        await self.manager.add_turn(conversation_id, assistant_turn, user_id)

        # Calculate totals
        total_cost = asr_cost + llm_cost + tts_cost
        total_time_ms = (time.time() - start_time) * 1000

        return TurnResult(
            conversation_id=conversation_id,
            turn_id=assistant_turn.id,
            user_text=user_text,
            detected_language=detected_language,
            assistant_text=assistant_text,
            audio_base64=audio_base64_response,
            audio_format="wav",
            audio_duration=audio_duration,
            asr_cost=asr_cost,
            llm_cost=llm_cost,
            tts_cost=tts_cost,
            total_cost=total_cost,
            processing_time_ms=total_time_ms,
            asr_time_ms=asr_time_ms,
            llm_time_ms=llm_time_ms,
            tts_time_ms=tts_time_ms,
            providers_used={
                "asr": conversation.config.asr_provider,
                "llm": conversation.config.llm_model,
                "tts": conversation.config.tts_provider,
            },
        )

    async def process_text_turn(
        self,
        conversation_id: str,
        user_text: str,
        user_id: Optional[str] = None,
        generate_audio: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> TurnResult:
        """
        Process a text-only turn (no ASR).

        Pipeline: Text Input -> LLM Response -> Optional TTS

        Args:
            conversation_id: Conversation ID
            user_text: User's text input
            user_id: User ID for access control
            generate_audio: Whether to generate TTS audio
            context: Additional context

        Returns:
            TurnResult with response and optional audio
        """
        start_time = time.time()
        context = context or {}

        # Get conversation
        conversation = await self.manager.get_conversation(
            conversation_id, user_id
        )
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create user turn
        user_turn = ConversationTurn(
            id=f"turn_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role=TurnRole.USER,
            content=user_text,
            cost_usd=0.0,
        )

        # Add user turn
        await self.manager.add_turn(conversation_id, user_turn, user_id)

        # Generate LLM response
        llm_start = time.time()
        conversation = await self.manager.get_conversation(
            conversation_id, user_id
        )

        llm_result = await self._generate_response(
            conversation=conversation,
            user_text=user_text,
            context=context,
        )
        llm_time_ms = (time.time() - llm_start) * 1000

        assistant_text = llm_result.get("response", "")
        llm_tokens = llm_result.get("tokens", {})
        llm_cost = llm_result.get("cost", 0.0)

        # Optional TTS
        tts_time_ms = 0.0
        tts_cost = 0.0
        audio_base64_response = None
        audio_duration = None

        if generate_audio:
            tts_start = time.time()
            tts_result = await self._synthesize_speech(
                text=assistant_text,
                config=conversation.config,
                context=context,
            )
            tts_time_ms = (time.time() - tts_start) * 1000
            audio_base64_response = tts_result.get("audio_base64")
            audio_duration = tts_result.get("duration")
            tts_cost = tts_result.get("cost", 0.0)

        # Create assistant turn
        assistant_turn = ConversationTurn(
            id=f"turn_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role=TurnRole.ASSISTANT,
            content=assistant_text,
            llm_model=conversation.config.llm_model,
            llm_tokens=llm_tokens,
            tts_provider=conversation.config.tts_provider if generate_audio else None,
            cost_usd=llm_cost + tts_cost,
            processing_time_ms=llm_time_ms + tts_time_ms,
        )

        await self.manager.add_turn(conversation_id, assistant_turn, user_id)

        total_cost = llm_cost + tts_cost
        total_time_ms = (time.time() - start_time) * 1000

        return TurnResult(
            conversation_id=conversation_id,
            turn_id=assistant_turn.id,
            user_text=user_text,
            detected_language=None,
            assistant_text=assistant_text,
            audio_base64=audio_base64_response,
            audio_format="wav",
            audio_duration=audio_duration,
            asr_cost=0.0,
            llm_cost=llm_cost,
            tts_cost=tts_cost,
            total_cost=total_cost,
            processing_time_ms=total_time_ms,
            asr_time_ms=0.0,
            llm_time_ms=llm_time_ms,
            tts_time_ms=tts_time_ms,
            providers_used={
                "llm": conversation.config.llm_model,
                "tts": conversation.config.tts_provider if generate_audio else None,
            },
        )

    async def stream_response(
        self,
        conversation_id: str,
        user_text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response for real-time display.

        Yields text chunks as they're generated.

        Args:
            conversation_id: Conversation ID
            user_text: User's input text
            user_id: User ID
            context: Additional context

        Yields:
            Text chunks from LLM
        """
        context = context or {}

        # Get conversation
        conversation = await self.manager.get_conversation(
            conversation_id, user_id
        )
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create user turn
        user_turn = ConversationTurn(
            id=f"turn_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role=TurnRole.USER,
            content=user_text,
            cost_usd=0.0,
        )
        await self.manager.add_turn(conversation_id, user_turn, user_id)

        # Stream LLM response
        conversation = await self.manager.get_conversation(
            conversation_id, user_id
        )

        history = conversation.get_history_for_llm()
        full_response = ""

        if self.llm_service:
            async for chunk in self._stream_llm_response(
                history=history,
                config=conversation.config,
                context=context,
            ):
                full_response += chunk
                yield chunk
        else:
            # Fallback for testing
            full_response = "Streaming response not available without LLM service."
            yield full_response

        # Create assistant turn after streaming completes
        assistant_turn = ConversationTurn(
            id=f"turn_{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            role=TurnRole.ASSISTANT,
            content=full_response,
            llm_model=conversation.config.llm_model,
            cost_usd=0.0,  # Cost calculated after
        )
        await self.manager.add_turn(conversation_id, assistant_turn, user_id)

    async def _transcribe_audio(
        self,
        audio_base64: str,
        audio_format: str,
        config: ConversationConfig,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Transcribe audio using configured ASR provider.

        Args:
            audio_base64: Base64-encoded audio
            audio_format: Audio format
            config: Conversation configuration
            context: Additional context

        Returns:
            Dict with text, language, confidence, cost
        """
        if not self.asr_service:
            logger.warning("No ASR service configured, returning empty transcription")
            return {
                "text": "",
                "language": None,
                "confidence": 0.0,
                "cost": 0.0,
            }

        try:
            # Decode audio
            audio_bytes = base64.b64decode(audio_base64)

            # Use ASR service
            result = await self.asr_service.transcribe(
                audio_data=audio_bytes,
                provider=config.asr_provider,
                language=config.asr_language,
            )

            return {
                "text": result.get("text", ""),
                "language": result.get("language"),
                "confidence": result.get("confidence", 0.0),
                "cost": result.get("cost", 0.0),
            }

        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            raise

    async def _generate_response(
        self,
        conversation: ConversationState,
        user_text: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate LLM response using conversation history.

        Args:
            conversation: Current conversation state
            user_text: Latest user input
            context: Additional context

        Returns:
            Dict with response, tokens, cost
        """
        if not self.llm_service:
            logger.warning("No LLM service configured, returning default response")
            return {
                "response": "I understand. How can I help you further?",
                "tokens": {"input": 0, "output": 0},
                "cost": 0.0,
            }

        try:
            # Get conversation history for LLM
            history = conversation.get_history_for_llm()

            # Call LLM service
            result = await self.llm_service.chat(
                messages=history,
                model=conversation.config.llm_model,
                temperature=conversation.config.llm_temperature,
                max_tokens=conversation.config.llm_max_tokens,
            )

            return {
                "response": result.get("response", ""),
                "tokens": result.get("tokens", {}),
                "cost": result.get("cost", 0.0),
            }

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def _synthesize_speech(
        self,
        text: str,
        config: ConversationConfig,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesize speech using configured TTS provider.

        Args:
            text: Text to synthesize
            config: Conversation configuration
            context: Additional context

        Returns:
            Dict with audio_base64, duration, cost
        """
        if not self.tts_client:
            logger.warning("No TTS client configured, returning no audio")
            return {
                "audio_base64": None,
                "duration": None,
                "cost": 0.0,
            }

        try:
            # Call TTS client
            result = await self.tts_client.synthesize(
                text=text,
                provider=config.tts_provider,
                voice=config.tts_voice,
                speed=config.tts_speed,
            )

            # Encode audio to base64 if needed
            audio_data = result.get("audio")
            if isinstance(audio_data, bytes):
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            else:
                audio_base64 = audio_data

            return {
                "audio_base64": audio_base64,
                "duration": result.get("duration"),
                "cost": result.get("cost", 0.0),
            }

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise

    async def _stream_llm_response(
        self,
        history: list,
        config: ConversationConfig,
        context: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response chunks.

        Args:
            history: Conversation history
            config: Configuration
            context: Additional context

        Yields:
            Text chunks
        """
        if not self.llm_service:
            yield "Streaming not available."
            return

        try:
            async for chunk in self.llm_service.stream_chat(
                messages=history,
                model=config.llm_model,
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens,
            ):
                yield chunk

        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            raise

    async def create_conversation(
        self,
        user_id: str,
        organization_id: str = "default",
        config: Optional[ConversationConfig] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        """
        Create a new conversation.

        Convenience method that delegates to manager.

        Args:
            user_id: User ID
            organization_id: Organization ID
            config: Optional configuration
            title: Optional title
            metadata: Optional metadata

        Returns:
            Created ConversationState
        """
        return await self.manager.create_conversation(
            user_id=user_id,
            organization_id=organization_id,
            config=config,
            title=title,
            metadata=metadata,
        )

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ConversationState]:
        """
        Get a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID for access control

        Returns:
            ConversationState or None
        """
        return await self.manager.get_conversation(conversation_id, user_id)

    async def end_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ConversationState]:
        """
        End/complete a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: Optional user ID

        Returns:
            Updated ConversationState or None
        """
        return await self.manager.end_conversation(conversation_id, user_id)

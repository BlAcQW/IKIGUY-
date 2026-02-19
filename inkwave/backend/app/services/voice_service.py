"""
Voice Q&A Service.

Handles voice interactions using shared AI services:
- STT (Speech-to-Text) via OpenAI Whisper
- RAG (Retrieval Augmented Generation) via Gemini 2.5 Flash
- TTS (Text-to-Speech) via centralized TTS Provider Service

Integrates with @apps/shared/services/ and @apps/shared/integration/.

Uses centralized TTSProviderService for access to all self-hosted TTS providers
with integrated billing and health monitoring.
"""

import sys
import os
import io
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Add shared services to path
sys.path.append('/opt/kasaai/apps/shared')

# Import from @shared/integration and @shared/services
try:
    from integration.gemini_service import GeminiService
    from integration.rag import RAGService, RAGConfig
    from integration.ai_services.stt_service import STTService
    from integration.usage_calculator import UsageCalculator
    from integration.analytics_service import get_analytics_service

    # Import centralized TTS Provider Service
    from services.tts_provider_service import (
        TTSProviderService,
        SynthesisRequest,
        SynthesisResult
    )

    # Import audio conversion service for format conversion
    from services.audio_conversion_service import AudioConversionService

    SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import shared services: {e}")
    SERVICES_AVAILABLE = False

from app.core.config import settings


class VoiceService:
    """
    Voice Q&A service using shared AI services.

    Handles complete voice interaction pipeline:
    1. Transcribe audio to text (STT)
    2. Query book content (RAG)
    3. Generate audio response (TTS)
    """

    def __init__(self):
        """
        Initialize voice service with shared integrations.

        Uses real services if available, falls back to mocks otherwise.
        """

        self.services_available = SERVICES_AVAILABLE
        self.tts_initialized = False

        if SERVICES_AVAILABLE:
            try:
                # STT Service (Whisper)
                self.stt_service = STTService(
                    provider="openai",
                    api_key=settings.OPENAI_API_KEY
                )

                # Centralized TTS Provider Service (all self-hosted providers)
                self.tts_service = TTSProviderService(
                    enable_billing=True,
                    enable_health_monitoring=True
                )
                # Note: TTS service needs async initialization
                # Will be initialized in async context

                # TODO: Initialize RAG service when needed
                # Gemini Service
                # self.gemini_service = GeminiService(
                #     api_key=settings.GEMINI_API_KEY,
                #     model=settings.GEMINI_MODEL
                # )
                #
                # RAG Configuration
                # rag_config = RAGConfig(
                #     ai_provider="gemini",
                #     api_key=settings.GEMINI_API_KEY,
                #     embedding_model=settings.GEMINI_EMBEDDING_MODEL,
                #     llm_model=settings.GEMINI_MODEL,
                #     retrieval_k=settings.RAG_RETRIEVAL_K,
                #     confidence_threshold=settings.RAG_CONFIDENCE_THRESHOLD,
                #     temperature=settings.RAG_TEMPERATURE
                # )
                # self.rag_service = RAGService(rag_config)

                # Analytics service
                self.analytics = get_analytics_service()

                logger.info("VoiceService initialized (TTS requires async init)")
            except Exception as e:
                logger.error(f"Failed to initialize voice services: {e}")
                self.services_available = False
        else:
            logger.warning("Using mock voice services (real services not available)")

    async def _ensure_tts_initialized(self):
        """
        Ensure TTS service is initialized.

        TTS service requires async initialization for provider health checks.
        """
        if self.services_available and not self.tts_initialized:
            try:
                await self.tts_service.initialize()
                self.tts_initialized = True
                logger.info("TTSProviderService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize TTS service: {e}")
                self.services_available = False

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm"
    ) -> Tuple[str, float, int]:
        """
        Transcribe audio to text using Whisper.

        Args:
            audio_bytes: Audio file bytes
            audio_format: Audio format (webm, mp3, wav, etc.)

        Returns:
            Tuple of (transcript, duration_seconds, cost_credits)
        """
        if self.services_available:
            try:
                # Real STT service
                transcript = await self.stt_service.transcribe(audio_bytes, audio_format)
                logger.info(f"Real STT transcription: {transcript[:50]}...")
            except Exception as e:
                logger.error(f"STT transcription failed: {e}")
                transcript = "What is the main theme of this book?"  # Fallback
        else:
            # Mock transcription for development
            transcript = "What is the main theme of this book?"

        # Estimate duration (rough estimate: 1 byte ≈ 0.0001 seconds for compressed audio)
        duration_seconds = len(audio_bytes) * 0.0001

        # Calculate cost (Whisper: $0.006/minute = 60 credits/minute)
        cost_credits = int((duration_seconds / 60) * settings.PRICING_STT_PER_MINUTE)

        return transcript, duration_seconds, cost_credits

    async def query_book(
        self,
        question: str,
        book_id: str
    ) -> Tuple[str, int]:
        """
        Query book content using RAG with Gemini 2.5 Flash.

        Args:
            question: User's question
            book_id: Book identifier

        Returns:
            Tuple of (answer, cost_credits)
        """
        # TODO: Replace with real RAG service
        # collection_name = f"book_{book_id}"
        # context = await self.rag_service.retrieve(
        #     query=question,
        #     collection=collection_name,
        #     k=settings.RAG_RETRIEVAL_K
        # )
        # answer = await self.rag_service.generate(
        #     query=question,
        #     context=context,
        #     book_id=book_id
        # )

        # Mock answer for development
        answer = f"Based on your question '{question}', here's what I found in the book: This is a mock AI-generated response. The actual implementation will use Gemini 2.5 Flash with RAG to provide contextually relevant answers from the book's content. The system will retrieve the most relevant passages and generate a comprehensive answer based on the book's context."

        # Calculate RAG cost
        cost_credits = settings.PRICING_RAG_PER_QUERY

        return answer, cost_credits

    async def synthesize_speech(
        self,
        text: str,
        user_id: str,
        provider_id: str = "coqui_xtts",
        language: str = "en",
        speed: float = 1.0,
        output_format: str = "mp3",
        bitrate: str = "192k"
    ) -> Tuple[bytes, str, float, str]:
        """
        Convert text to speech using centralized TTS Provider Service.

        Supports multiple output formats with automatic conversion.

        Args:
            text: Text to synthesize
            user_id: User ID for billing
            provider_id: TTS provider to use (default: coqui_xtts)
            language: Language code (default: en)
            speed: Speech speed (default: 1.0)
            output_format: Audio format (mp3, ogg, wav, flac, m4a) (default: mp3)
            bitrate: Quality for lossy formats (128k-320k) (default: 192k)

        Returns:
            Tuple of (audio_bytes, audio_format, cost_usd, transaction_id)

        Note:
            - TTS service returns WAV format, which is converted to requested format
            - Cost is automatically deducted from user's wallet
            - MP3 format recommended for mobile (8x smaller than WAV)
            - Use skip_billing=True parameter for testing

        Raises:
            ValueError: If output_format or bitrate is invalid
        """
        # Ensure TTS service is initialized
        await self._ensure_tts_initialized()

        if self.services_available and self.tts_initialized:
            try:
                # Use centralized TTS Provider Service
                request = SynthesisRequest(
                    provider_id=provider_id,
                    text=text,
                    language=language,
                    speed=speed
                )

                result: SynthesisResult = await self.tts_service.synthesize(
                    user_id=user_id,
                    request=request
                )

                # Decode base64 audio to bytes
                import base64
                audio_bytes = base64.b64decode(result.audio_base64)

                logger.info(
                    f"TTS synthesis complete: {len(audio_bytes)} bytes, "
                    f"duration={result.duration}s, cost=${result.cost:.4f}"
                )

                # Convert format if needed (TTS service returns WAV)
                actual_format = "wav"  # TTS service returns WAV format

                if output_format.lower() != "wav":
                    try:
                        converter = AudioConversionService()
                        audio_bytes = converter.convert_audio(
                            audio_data=audio_bytes,
                            source_format="wav",
                            target_format=output_format.lower(),
                            bitrate=bitrate
                        )
                        actual_format = output_format.lower()

                        logger.info(
                            f"Converted audio from WAV to {output_format.upper()}: "
                            f"{len(audio_bytes)} bytes (bitrate: {bitrate})"
                        )
                    except Exception as e:
                        logger.error(f"Audio conversion failed: {e}, returning WAV")
                        # Return WAV if conversion fails
                        actual_format = "wav"

                return audio_bytes, actual_format, result.cost, result.transaction_id

            except ValueError as e:
                logger.error(f"TTS synthesis validation error: {e}")
                # Return empty audio on validation error
                return b"", output_format.lower(), 0.0, ""
            except Exception as e:
                logger.error(f"TTS synthesis failed: {e}")
                # Return empty audio on synthesis failure
                return b"", output_format.lower(), 0.0, ""
        else:
            # Mock audio bytes (empty for now)
            logger.warning("TTS service not available, returning empty audio")
            return b"", output_format.lower(), 0.0, ""

    async def complete_voice_qa(
        self,
        audio_bytes: bytes,
        book_id: str,
        user_id: str,
        audio_format: str = "webm",
        tts_provider: str = "coqui_xtts",
        output_format: str = "mp3",
        bitrate: str = "192k"
    ) -> dict:
        """
        Complete voice Q&A pipeline: STT → RAG → TTS.

        Args:
            audio_bytes: Voice question audio
            book_id: Book to query
            user_id: User ID for billing
            audio_format: Input audio format (default: webm)
            tts_provider: TTS provider to use (default: coqui_xtts)
            output_format: Output audio format (mp3, ogg, wav, flac, m4a) (default: mp3)
            bitrate: Quality for lossy formats (128k-320k) (default: 192k)

        Returns:
            dict with question, answer, audio_url, costs, timestamp, transaction_ids

        Note:
            - TTS cost is in USD and automatically deducted from user's wallet
            - STT and RAG costs are still in credits (to be migrated later)
            - MP3 format recommended for mobile users (8x smaller files)
        """
        total_cost_usd = 0.0
        costs = {}
        transaction_ids = {}

        # Step 1: Transcribe audio to text
        transcript, duration, stt_cost = await self.transcribe_audio(
            audio_bytes, audio_format
        )
        costs["stt_credits"] = stt_cost  # Still using credits for STT

        # Step 2: Query book with RAG
        answer, rag_cost = await self.query_book(transcript, book_id)
        costs["rag_credits"] = rag_cost  # Still using credits for RAG

        # Step 3: Synthesize answer to audio (with automatic billing and format conversion)
        answer_audio, audio_fmt, tts_cost_usd, transaction_id = await self.synthesize_speech(
            text=answer,
            user_id=user_id,
            provider_id=tts_provider,
            output_format=output_format,
            bitrate=bitrate
        )
        total_cost_usd += tts_cost_usd
        costs["tts_usd"] = tts_cost_usd
        costs["total_usd"] = total_cost_usd
        transaction_ids["tts"] = transaction_id

        # TODO: Upload audio_bytes to storage and get URL
        audio_url = None  # Will be implemented with storage service

        return {
            "question": transcript,
            "answer": answer,
            "audio_url": audio_url,
            "audio_format": audio_fmt,  # Include actual format in response
            "costs": costs,
            "transaction_ids": transaction_ids,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def save_conversation(
        self,
        user_id: str,
        book_id: str,
        question: str,
        answer: str,
        audio_url: Optional[str] = None
    ) -> str:
        """
        Save conversation to database.

        Args:
            user_id: User identifier
            book_id: Book identifier
            question: User's question
            answer: AI's answer
            audio_url: TTS audio URL

        Returns:
            Conversation ID
        """
        # TODO: Implement MongoDB storage
        conversation_id = f"conv_{datetime.utcnow().timestamp()}"

        # conversation_data = {
        #     "id": conversation_id,
        #     "user_id": user_id,
        #     "book_id": book_id,
        #     "question": question,
        #     "answer": answer,
        #     "audio_url": audio_url,
        #     "timestamp": datetime.utcnow()
        # }
        # await db.conversations.insert_one(conversation_data)

        return conversation_id

    async def get_conversation_history(
        self,
        user_id: str,
        book_id: str,
        limit: int = 50
    ) -> list[dict]:
        """
        Get user's conversation history for a book.

        Args:
            user_id: User identifier
            book_id: Book identifier
            limit: Maximum number of conversations

        Returns:
            List of conversations
        """
        # TODO: Implement MongoDB query
        conversations = []

        # conversations = await db.conversations.find({
        #     "user_id": user_id,
        #     "book_id": book_id
        # }).sort("timestamp", -1).limit(limit).to_list()

        return conversations


# Global voice service instance
voice_service = VoiceService()

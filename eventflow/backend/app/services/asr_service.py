"""
ASR Service for EventFlow.

Provides automatic speech recognition for:
- Voice notes on tasks
- Voice input for task updates
- Transcription of voice call responses
- Multi-language support (30+ languages via Whisper)
"""

import base64
import logging
from typing import Dict, Optional

from apps.shared.services.asr_provider_service import (
    ASRProviderService,
    TranscriptionRequest,
    TranscriptionResult
)

logger = logging.getLogger(__name__)


class EventFlowASRService:
    """
    ASR service for EventFlow voice features.

    Handles:
    - Task update voice input transcription
    - Voice notes on tasks and events
    - Call response transcription
    - Multi-language support (English, Twi, Ga, French, etc.)
    """

    def __init__(self):
        """Initialize ASR service with shared ASRProviderService."""
        self.asr_provider = ASRProviderService(
            enable_billing=True,
            enable_health_monitoring=True
        )
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize ASR service.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            await self.asr_provider.initialize()
            self._initialized = True
            logger.info("EventFlowASRService initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ASR service: {e}")
            return False

    async def transcribe_task_update(
        self,
        audio_data: bytes,
        user_id: str,
        task_id: str,
        language: Optional[str] = None,
        provider_id: str = "whisper_large_v3"
    ) -> Optional[Dict]:
        """
        Transcribe voice input for task update.

        Args:
            audio_data: Audio file bytes
            user_id: User ID for billing
            task_id: Task ID
            language: Language code (auto-detect if None)
            provider_id: ASR provider to use

        Returns:
            Dict with text, confidence, language, cost, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Create transcription request
            transcription_request = TranscriptionRequest(
                provider_id=provider_id,
                audio_base64=audio_base64,
                language=language,
                task="transcribe",
                response_format="json"
            )

            # Transcribe
            result: TranscriptionResult = await self.asr_provider.transcribe(
                user_id=user_id,
                request=transcription_request
            )

            logger.info(f"Transcribed task update for task {task_id}: {result.text[:50]}...")

            return {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "task_id": task_id
            }

        except Exception as e:
            logger.error(f"Failed to transcribe task update: {e}")
            return None

    async def transcribe_voice_note(
        self,
        audio_data: bytes,
        user_id: str,
        event_id: Optional[str] = None,
        task_id: Optional[str] = None,
        language: Optional[str] = None,
        provider_id: str = "whisper_large_v3"
    ) -> Optional[Dict]:
        """
        Transcribe voice note attached to event or task.

        Args:
            audio_data: Audio file bytes
            user_id: User ID for billing
            event_id: Event ID (optional)
            task_id: Task ID (optional)
            language: Language code (auto-detect if None)
            provider_id: ASR provider

        Returns:
            Dict with transcription result, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            transcription_request = TranscriptionRequest(
                provider_id=provider_id,
                audio_base64=audio_base64,
                language=language,
                task="transcribe",
                response_format="json"
            )

            result: TranscriptionResult = await self.asr_provider.transcribe(
                user_id=user_id,
                request=transcription_request
            )

            logger.info(
                f"Transcribed voice note: {result.text[:50]}... "
                f"(language: {result.language}, confidence: {result.confidence:.2f})"
            )

            return {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "event_id": event_id,
                "task_id": task_id
            }

        except Exception as e:
            logger.error(f"Failed to transcribe voice note: {e}")
            return None

    async def transcribe_voice_question(
        self,
        audio_data: bytes,
        user_id: str,
        context: str,
        language: Optional[str] = None,
        provider_id: str = "whisper_large_v3"
    ) -> Optional[Dict]:
        """
        Transcribe voice question from user.

        Used for voice-based event planning queries like:
        "What tasks are pending for the wedding?"
        "How many people confirmed for the bus?"

        Args:
            audio_data: Audio file bytes
            user_id: User ID for billing
            context: Context for the question (event name, etc.)
            language: Language code (auto-detect if None)
            provider_id: ASR provider

        Returns:
            Dict with transcription result, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            transcription_request = TranscriptionRequest(
                provider_id=provider_id,
                audio_base64=audio_base64,
                language=language,
                task="transcribe",
                response_format="json"
            )

            result: TranscriptionResult = await self.asr_provider.transcribe(
                user_id=user_id,
                request=transcription_request
            )

            logger.info(f"Transcribed voice question: {result.text}")

            return {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "context": context
            }

        except Exception as e:
            logger.error(f"Failed to transcribe voice question: {e}")
            return None

    async def transcribe_call_response(
        self,
        audio_data: bytes,
        user_id: str,
        call_id: str,
        task_id: str,
        language: Optional[str] = None,
        provider_id: str = "whisper_large_v3"
    ) -> Optional[Dict]:
        """
        Transcribe response from VAPI voice call.

        Used to transcribe what responsible person said during call.

        Args:
            audio_data: Audio file bytes
            user_id: User ID for billing
            call_id: VAPI call ID
            task_id: Task being discussed
            language: Language code (auto-detect if None)
            provider_id: ASR provider

        Returns:
            Dict with transcription result, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            transcription_request = TranscriptionRequest(
                provider_id=provider_id,
                audio_base64=audio_base64,
                language=language,
                task="transcribe",
                response_format="json"
            )

            result: TranscriptionResult = await self.asr_provider.transcribe(
                user_id=user_id,
                request=transcription_request
            )

            logger.info(
                f"Transcribed call response for call {call_id}: "
                f"{result.text[:50]}..."
            )

            return {
                "text": result.text,
                "confidence": result.confidence,
                "language": result.language,
                "duration": result.duration,
                "cost": result.cost,
                "provider_used": result.provider_id,
                "call_id": call_id,
                "task_id": task_id
            }

        except Exception as e:
            logger.error(f"Failed to transcribe call response: {e}")
            return None

    async def get_supported_languages(self) -> Dict:
        """
        Get all supported languages for ASR.

        Returns:
            Dict mapping providers to supported languages
        """
        if not self._initialized:
            await self.initialize()

        try:
            languages = await self.asr_provider.get_supported_languages()
            return languages
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return {"success": False, "error": str(e)}

    async def get_providers_status(self) -> Dict:
        """
        Get status of all ASR providers.

        Returns:
            Dict with provider statuses
        """
        if not self._initialized:
            await self.initialize()

        try:
            status = await self.asr_provider.get_providers_status()
            return status
        except Exception as e:
            logger.error(f"Failed to get providers status: {e}")
            return {"success": False, "error": str(e)}

    async def translate_transcription(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> Optional[str]:
        """
        Translate transcribed text to another language.

        Useful for multi-lingual events where organizer speaks English
        but team member responds in Twi.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code

        Returns:
            Translated text, or None if translation fails
        """
        # TODO: Implement translation via LLM service
        # For now, return original text
        logger.warning(
            f"Translation not yet implemented: {source_language} -> {target_language}"
        )
        return text

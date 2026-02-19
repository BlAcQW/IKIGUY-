"""
ASR (Automatic Speech Recognition) service for InkWave.

Handles voice-to-text transcription using the shared ASRProviderService.
"""

import sys
import os
import logging
import base64
from typing import Optional, Dict
from datetime import datetime

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from apps.shared.services.asr_provider_service import ASRProviderService

logger = logging.getLogger(__name__)


class ASRService:
    """
    ASR service for InkWave voice question transcription.

    Provides speech-to-text with automatic billing and
    multiple ASR provider support.
    """

    def __init__(self):
        """Initialize ASR service."""
        self.asr_provider = ASRProviderService(
            enable_billing=True,
            enable_health_monitoring=True
        )
        self._initialized = False

    async def initialize(self):
        """
        Initialize the ASR provider service.

        Raises:
            Exception: If initialization fails
        """
        if self._initialized:
            return

        try:
            await self.asr_provider.initialize()
            self._initialized = True
            logger.info("✅ ASR Service initialized")
        except Exception as e:
            logger.error(f"❌ ASR Service initialization failed: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_data: bytes,
        user_id: str,
        provider_id: str = "whisper",
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio file bytes
            user_id: User ID for billing
            provider_id: ASR provider (whisper, etc.)
            language: Optional language code for better accuracy

        Returns:
            Dict with text, confidence, duration, cost

        Raises:
            Exception: If transcription fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Convert audio bytes to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            logger.info(
                f"Transcribing audio: {len(audio_data)} bytes, "
                f"provider: {provider_id}, language: {language}"
            )

            # Transcribe using ASR provider service
            result = await self.asr_provider.transcribe(
                user_id=user_id,
                audio_base64=audio_base64,
                provider_id=provider_id,
                language=language
            )

            logger.info(
                f"✅ Transcription complete: '{result.get('text', '')[:50]}...', "
                f"confidence: {result.get('confidence', 0):.2f}, "
                f"${result.get('cost', 0):.4f}"
            )

            return {
                "text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "duration": result.get("duration", 0.0),
                "cost": result.get("cost", 0.0),
                "provider_used": result.get("provider_id", provider_id),
                "transaction_id": result.get("transaction_id"),
                "language_detected": result.get("language")
            }

        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {e}")
            raise

    async def transcribe_file(
        self,
        file_path: str,
        user_id: str,
        provider_id: str = "whisper",
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio file to text.

        Args:
            file_path: Path to audio file
            user_id: User ID for billing
            provider_id: ASR provider
            language: Optional language code

        Returns:
            Dict with transcription results

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If transcription fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Read file
        with open(file_path, "rb") as f:
            audio_data = f.read()

        return await self.transcribe_audio(
            audio_data=audio_data,
            user_id=user_id,
            provider_id=provider_id,
            language=language
        )

    async def estimate_transcription_cost(
        self,
        audio_duration_seconds: float,
        provider_id: str = "whisper"
    ) -> Dict:
        """
        Estimate cost to transcribe audio.

        Args:
            audio_duration_seconds: Audio duration in seconds
            provider_id: ASR provider

        Returns:
            Dict with estimated_cost
        """
        if not self._initialized:
            await self.initialize()

        # Whisper pricing: ~$0.006 per minute
        cost_per_minute = 0.006
        minutes = audio_duration_seconds / 60.0
        estimated_cost = minutes * cost_per_minute

        return {
            "estimated_cost": round(estimated_cost, 4),
            "duration_minutes": round(minutes, 2),
            "cost_per_minute": cost_per_minute,
            "provider_id": provider_id
        }

    async def shutdown(self) -> None:
        """Cleanup when service shuts down."""
        if self.asr_provider:
            await self.asr_provider.shutdown()
        logger.info("ASR Service shut down")


# Singleton instance
_asr_service_instance: Optional[ASRService] = None


async def get_asr_service() -> ASRService:
    """
    Get or create ASR service singleton.

    Returns:
        ASRService instance

    Raises:
        Exception: If initialization fails
    """
    global _asr_service_instance

    if _asr_service_instance is None:
        _asr_service_instance = ASRService()
        await _asr_service_instance.initialize()

    return _asr_service_instance

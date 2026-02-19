"""
AI service for devotional features:
- Text-to-speech (TTS) generation
- Devotional summarization
- Scripture explanation
Uses shared TTSProviderService from @apps/shared/
"""

import os
import base64
from typing import Optional, Dict
import logging

# Import shared TTS provider service
import sys
sys.path.append("/opt/kasaai/apps")
from shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    SynthesisResult,
)

from app.config import settings
from app.db.mongodb import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)


class AIService:
    """AI service for devotional features."""

    def __init__(self):
        """Initialize AI service."""
        self.tts_provider: Optional[TTSProviderService] = None
        self.storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "storage",
            "audio",
        )
        self.storage_url = settings.CORS_ORIGINS[0].replace(
            "http://localhost:8080", "http://localhost:30042"
        ) + "/storage/audio"

        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)

    async def initialize(self):
        """Initialize TTS provider service."""
        try:
            self.tts_provider = TTSProviderService(enable_billing=False)
            await self.tts_provider.initialize()
            logger.info("TTS provider service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS provider: {e}")
            logger.warning("TTS features will be disabled")

    async def generate_devotional_audio(
        self,
        devotional_id: str,
        text: str,
        user_id: str,
        provider_id: str = "f5tts",
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        language: str = "en",
        force_regenerate: bool = False,
    ) -> Dict:
        """
        Generate audio narration for a devotional.

        Args:
            devotional_id (str): Devotional ID.
            text (str): Devotional text content.
            user_id (str): User ID (for billing tracking).
            provider_id (str): TTS provider (f5tts, coqui_xtts, openai_tts, etc.).
            voice_id (Optional[str]): Voice ID (provider-specific).
            speed (float): Speech speed (0.5-2.0).
            language (str): Language code (en, es, fr, etc.).
            force_regenerate (bool): Force regeneration even if cached.

        Returns:
            Dict: Audio metadata with URL, duration, cost.

        Raises:
            Exception: If TTS generation fails.
        """
        db = get_database()

        # Check if audio already exists
        if not force_regenerate:
            devotional = await db.devotionals.find_one({"_id": ObjectId(devotional_id)})
            if devotional and devotional.get("audio_url"):
                logger.info(f"Using cached audio for devotional {devotional_id}")
                return {
                    "audio_url": devotional["audio_url"],
                    "duration": devotional.get("audio_duration", 0),
                    "cost": 0.0,
                    "provider_used": devotional.get("audio_provider", "cached"),
                    "cached": True,
                }

        # Initialize TTS provider if needed
        if not self.tts_provider:
            await self.initialize()

        if not self.tts_provider:
            raise Exception("TTS provider not available")

        # Optimize text for TTS (replace abbreviations)
        optimized_text = self._optimize_text_for_tts(text)

        # Set default voice based on provider
        if not voice_id:
            voice_id = self._get_default_voice(provider_id)

        # Generate audio with fallback
        result = await self._generate_with_fallback(
            text=optimized_text,
            user_id=user_id,
            provider_id=provider_id,
            voice_id=voice_id,
            speed=speed,
            language=language,
        )

        # Save audio file
        audio_url = await self._save_audio_file(
            audio_base64=result.audio_base64,
            devotional_id=devotional_id,
        )

        # Update devotional in database
        await db.devotionals.update_one(
            {"_id": ObjectId(devotional_id)},
            {
                "$set": {
                    "audio_url": audio_url,
                    "audio_duration": result.duration,
                    "audio_cost": result.cost,
                    "audio_provider": result.provider_id,
                }
            },
        )

        logger.info(
            f"Generated audio for devotional {devotional_id} "
            f"using {result.provider_id} (duration: {result.duration}s, cost: ${result.cost:.4f})"
        )

        return {
            "audio_url": audio_url,
            "duration": result.duration,
            "cost": result.cost,
            "provider_used": result.provider_id,
            "cached": False,
        }

    async def _generate_with_fallback(
        self,
        text: str,
        user_id: str,
        provider_id: str,
        voice_id: Optional[str],
        speed: float,
        language: str,
    ) -> SynthesisResult:
        """
        Generate audio with fallback providers for reliability.

        Args:
            text (str): Text to synthesize.
            user_id (str): User ID.
            provider_id (str): Primary provider ID.
            voice_id (Optional[str]): Voice ID.
            speed (float): Speech speed.
            language (str): Language code.

        Returns:
            SynthesisResult: Synthesis result.

        Raises:
            Exception: If all providers fail.
        """
        # Provider fallback chain
        providers = [
            (provider_id, voice_id),  # Primary provider
            ("coqui_xtts", "nova"),  # Fallback 1: Coqui XTTS
            ("openai_tts", "alloy"),  # Fallback 2: OpenAI TTS (requires API key)
        ]

        for pid, vid in providers:
            try:
                logger.info(f"Attempting TTS with provider: {pid}, voice: {vid}")

                result: SynthesisResult = await self.tts_provider.synthesize(
                    user_id=user_id,
                    request=SynthesisRequest(
                        provider_id=pid,
                        text=text,
                        language=language,
                        voice_id=vid,
                        speed=speed,
                        output_format="mp3",
                    ),
                )

                logger.info(f"Successfully generated audio with {pid}")
                return result

            except Exception as e:
                logger.warning(f"Provider {pid} failed: {e}")
                continue

        raise Exception("All TTS providers failed. Please try again later.")

    async def _save_audio_file(self, audio_base64: str, devotional_id: str) -> str:
        """
        Save audio file to storage and return public URL.

        Args:
            audio_base64 (str): Base64-encoded audio data.
            devotional_id (str): Devotional ID.

        Returns:
            str: Public URL to audio file.
        """
        # Decode audio
        audio_data = base64.b64decode(audio_base64)

        # Generate filename
        filename = f"devotional_{devotional_id}.mp3"
        filepath = os.path.join(self.storage_path, filename)

        # Save file
        with open(filepath, "wb") as f:
            f.write(audio_data)

        # Generate URL
        audio_url = f"{self.storage_url}/{filename}"

        logger.info(f"Saved audio to {filepath}, URL: {audio_url}")

        return audio_url

    def _optimize_text_for_tts(self, text: str) -> str:
        """
        Optimize text for TTS by replacing abbreviations and cleaning formatting.

        Args:
            text (str): Original text.

        Returns:
            str: Optimized text.
        """
        # Common abbreviations to expand
        replacements = {
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Misses",
            "Ms.": "Miss",
            "Rev.": "Reverend",
            "St.": "Saint",
            "etc.": "et cetera",
            "i.e.": "that is",
            "e.g.": "for example",
            "vs.": "versus",
            "Jr.": "Junior",
            "Sr.": "Senior",
            "Gen.": "Genesis",
            "Matt.": "Matthew",
            "Cor.": "Corinthians",
            "Gal.": "Galatians",
            "Phil.": "Philippians",
            "Col.": "Colossians",
            "Thess.": "Thessalonians",
            "Tim.": "Timothy",
            "Heb.": "Hebrews",
            "Jas.": "James",
            "Pet.": "Peter",
            "Rev.": "Revelation",
        }

        optimized = text
        for abbr, full in replacements.items():
            optimized = optimized.replace(abbr, full)

        # Remove excessive whitespace
        optimized = " ".join(optimized.split())

        return optimized

    def _get_default_voice(self, provider_id: str) -> str:
        """
        Get default voice for a provider.

        Args:
            provider_id (str): Provider ID.

        Returns:
            str: Default voice ID.
        """
        default_voices = {
            "f5tts": None,  # F5-TTS uses reference audio for cloning
            "coqui_xtts": "nova",
            "openai_tts": "alloy",
            "edge_tts": "en-US-JennyNeural",
            "kokoro": "default",
            "melotts": "default",
            "styletts2": "default",
        }

        return default_voices.get(provider_id, "default")


# Global AI service instance
_ai_service: Optional[AIService] = None


async def get_ai_service() -> AIService:
    """
    Get or create AI service instance.

    Returns:
        AIService: AI service instance.
    """
    global _ai_service

    if _ai_service is None:
        _ai_service = AIService()
        await _ai_service.initialize()

    return _ai_service

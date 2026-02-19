"""
OpenAI TTS Service for InkWave Audiobooks.

Provides high-quality audiobook narration using OpenAI's TTS models:
- tts-1: Fast, good quality, cost-effective for long audiobooks
- tts-1-hd: Highest quality, slower, premium option
- gpt-4o-mini-tts: Latest model with enhanced expressiveness (when available)

Voices available:
- alloy: Balanced, neutral - great for general narration
- echo: Deep, warm - ideal for male protagonists, non-fiction
- fable: British, expressive - perfect for fiction, storytelling
- onyx: Deep, authoritative - business, self-help books
- nova: Young, friendly - YA, children's books
- shimmer: Soft, gentle - romance, meditation, poetry

Author: AI Labs Africa
Created: November 26, 2025
"""

import os
import logging
import base64
import asyncio
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)


class OpenAIVoice(str, Enum):
    """Available OpenAI TTS voices."""
    ALLOY = "alloy"      # Balanced, neutral
    ECHO = "echo"        # Deep, warm
    FABLE = "fable"      # British, expressive
    ONYX = "onyx"        # Deep, authoritative
    NOVA = "nova"        # Young, friendly
    SHIMMER = "shimmer"  # Soft, gentle


class OpenAITTSModel(str, Enum):
    """Available OpenAI TTS models."""
    TTS_1 = "tts-1"           # Fast, good quality
    TTS_1_HD = "tts-1-hd"     # High quality, slower


# Voice metadata for UI display
VOICE_METADATA = {
    "alloy": {
        "name": "Alloy",
        "description": "Balanced, neutral voice - great for general narration",
        "gender": "neutral",
        "accent": "American",
        "best_for": ["non-fiction", "general", "audiobooks"],
        "sample_text": "The art of storytelling has been with us since the dawn of human civilization."
    },
    "echo": {
        "name": "Echo",
        "description": "Deep, warm voice - ideal for male protagonists and non-fiction",
        "gender": "male",
        "accent": "American",
        "best_for": ["thrillers", "business", "biography"],
        "sample_text": "In the quiet of the night, the detective reviewed the evidence one more time."
    },
    "fable": {
        "name": "Fable",
        "description": "British, expressive voice - perfect for fiction and storytelling",
        "gender": "neutral",
        "accent": "British",
        "best_for": ["fiction", "fantasy", "children's books"],
        "sample_text": "Once upon a time, in a land far away, there lived a curious young adventurer."
    },
    "onyx": {
        "name": "Onyx",
        "description": "Deep, authoritative voice - business and self-help books",
        "gender": "male",
        "accent": "American",
        "best_for": ["self-help", "business", "motivational"],
        "sample_text": "Success is not final, failure is not fatal. It is the courage to continue that counts."
    },
    "nova": {
        "name": "Nova",
        "description": "Young, friendly voice - YA and children's books",
        "gender": "female",
        "accent": "American",
        "best_for": ["young adult", "children's", "contemporary"],
        "sample_text": "Today was going to be different. Sarah could feel it in her bones."
    },
    "shimmer": {
        "name": "Shimmer",
        "description": "Soft, gentle voice - romance, meditation, poetry",
        "gender": "female",
        "accent": "American",
        "best_for": ["romance", "poetry", "meditation", "spirituality"],
        "sample_text": "Take a deep breath. Feel the warmth of the sun on your skin."
    }
}


class OpenAITTSRequest(BaseModel):
    """Request for OpenAI TTS synthesis."""
    text: str = Field(..., description="Text to synthesize (max 4096 chars)")
    model: str = Field(default="tts-1", description="TTS model")
    voice: str = Field(default="alloy", description="Voice to use")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Playback speed")
    response_format: str = Field(default="mp3", description="Audio format")


class OpenAITTSResult(BaseModel):
    """Result from OpenAI TTS synthesis."""
    audio_base64: str
    text: str
    model: str
    voice: str
    duration: float
    cost: float
    character_count: int


class OpenAITTSService:
    """
    OpenAI TTS Service for audiobook narration.

    Provides high-quality text-to-speech using OpenAI's API with
    automatic cost tracking and caching support.

    Example:
        >>> service = OpenAITTSService()
        >>> result = await service.synthesize(
        ...     text="Hello, welcome to this audiobook.",
        ...     voice="fable",
        ...     model="tts-1"
        ... )
        >>> print(f"Audio duration: {result.duration}s, cost: ${result.cost:.4f}")
    """

    # Pricing per character (OpenAI pricing as of 2024)
    PRICING = {
        "tts-1": Decimal("0.000015"),      # $15 per 1M chars
        "tts-1-hd": Decimal("0.00003"),    # $30 per 1M chars
    }

    # Maximum characters per request
    MAX_CHARS = 4096

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "tts-1",
        default_voice: str = "alloy",
        enable_caching: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize OpenAI TTS Service.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            base_url: OpenAI API base URL
            default_model: Default TTS model
            default_voice: Default voice
            enable_caching: Enable audio caching
            cache_dir: Directory for cached audio files
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not configured - TTS will fail")

        self.base_url = base_url
        self.default_model = default_model
        self.default_voice = default_voice
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir or "/opt/kasaai/apps/inkwave/backend/storage/openai_tts_cache"

        # Create cache directory
        if self.enable_caching:
            os.makedirs(self.cache_dir, exist_ok=True)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "total_characters": 0,
            "total_cost": Decimal("0"),
            "cache_hits": 0
        }

    def get_available_voices(self) -> Dict[str, Dict]:
        """
        Get all available voices with metadata.

        Returns:
            Dict mapping voice IDs to their metadata
        """
        return VOICE_METADATA.copy()

    def get_available_models(self) -> List[Dict]:
        """
        Get available TTS models with descriptions.

        Returns:
            List of model info dicts
        """
        return [
            {
                "id": "tts-1",
                "name": "TTS-1 (Standard)",
                "description": "Fast, good quality - recommended for audiobooks",
                "cost_per_1m_chars": 15.00,
                "speed": "fast",
                "quality": "good"
            },
            {
                "id": "tts-1-hd",
                "name": "TTS-1-HD (High Definition)",
                "description": "Highest quality - premium option for short content",
                "cost_per_1m_chars": 30.00,
                "speed": "slower",
                "quality": "excellent"
            }
        ]

    def estimate_cost(
        self,
        text: str,
        model: str = "tts-1"
    ) -> Dict:
        """
        Estimate cost for TTS synthesis.

        Args:
            text: Text to synthesize
            model: TTS model to use

        Returns:
            Dict with cost breakdown
        """
        char_count = len(text)
        cost_per_char = self.PRICING.get(model, self.PRICING["tts-1"])
        total_cost = cost_per_char * char_count

        # Estimate duration (~150 words/minute, ~5 chars/word)
        estimated_words = char_count / 5
        estimated_duration = (estimated_words / 150) * 60  # seconds

        return {
            "character_count": char_count,
            "model": model,
            "cost_per_1m_chars": float(cost_per_char * 1_000_000),
            "estimated_cost": float(total_cost),
            "estimated_duration_seconds": estimated_duration
        }

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: float = 1.0,
        response_format: str = "mp3"
    ) -> OpenAITTSResult:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize (max 4096 chars)
            voice: Voice to use (default: alloy)
            model: TTS model (default: tts-1)
            speed: Playback speed 0.25-4.0 (default: 1.0)
            response_format: Audio format (mp3, opus, aac, flac)

        Returns:
            OpenAITTSResult with audio data

        Raises:
            ValueError: If text exceeds max length
            Exception: If API call fails
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        if len(text) > self.MAX_CHARS:
            raise ValueError(f"Text exceeds maximum {self.MAX_CHARS} characters")

        voice = voice or self.default_voice
        model = model or self.default_model

        # Check cache first
        if self.enable_caching:
            cached = await self._get_cached_audio(text, voice, model, speed)
            if cached:
                self.stats["cache_hits"] += 1
                return cached

        # Make API request
        url = f"{self.base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": response_format
        }

        logger.info(f"Synthesizing {len(text)} chars with voice={voice}, model={model}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenAI TTS failed: {response.status_code} - {error_detail}")
                raise Exception(f"OpenAI TTS failed: {response.status_code}")

            audio_bytes = response.content

        # Encode to base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Calculate cost
        char_count = len(text)
        cost_per_char = self.PRICING.get(model, self.PRICING["tts-1"])
        cost = float(cost_per_char * char_count)

        # Estimate duration from audio size
        # MP3 at 128kbps = 16KB/sec
        duration = len(audio_bytes) / 16000.0

        # Update stats
        self.stats["total_requests"] += 1
        self.stats["total_characters"] += char_count
        self.stats["total_cost"] += Decimal(str(cost))

        result = OpenAITTSResult(
            audio_base64=audio_base64,
            text=text,
            model=model,
            voice=voice,
            duration=duration,
            cost=cost,
            character_count=char_count
        )

        # Cache the result
        if self.enable_caching:
            await self._cache_audio(result, speed)

        return result

    async def synthesize_long_text(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: float = 1.0
    ) -> List[OpenAITTSResult]:
        """
        Synthesize long text by chunking.

        Automatically splits text into chunks of max 4096 characters
        at sentence boundaries for seamless narration.

        Args:
            text: Text to synthesize (any length)
            voice: Voice to use
            model: TTS model
            speed: Playback speed

        Returns:
            List of OpenAITTSResult objects
        """
        chunks = self._chunk_text(text)
        results = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")
            result = await self.synthesize(
                text=chunk,
                voice=voice,
                model=model,
                speed=speed
            )
            results.append(result)

        return results

    def _chunk_text(self, text: str, max_chars: int = 4000) -> List[str]:
        """
        Split text into chunks at sentence boundaries.

        Args:
            text: Text to chunk
            max_chars: Maximum characters per chunk (slightly less than API limit)

        Returns:
            List of text chunks
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += (" " if current_chunk else "") + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Handle very long sentences
                if len(sentence) > max_chars:
                    # Split at word boundaries
                    words = sentence.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) + 1 <= max_chars:
                            current_chunk += (" " if current_chunk else "") + word
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = word
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    async def _get_cached_audio(
        self,
        text: str,
        voice: str,
        model: str,
        speed: float
    ) -> Optional[OpenAITTSResult]:
        """Get cached audio if available."""
        import hashlib

        # Create cache key from parameters
        cache_key = hashlib.md5(
            f"{text}:{voice}:{model}:{speed}".encode()
        ).hexdigest()

        cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        meta_path = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_path) or not os.path.exists(meta_path):
            return None

        try:
            import json

            # Load metadata
            with open(meta_path, "r") as f:
                meta = json.load(f)

            # Load audio
            with open(cache_path, "rb") as f:
                audio_bytes = f.read()

            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            return OpenAITTSResult(
                audio_base64=audio_base64,
                text=meta["text"],
                model=meta["model"],
                voice=meta["voice"],
                duration=meta["duration"],
                cost=0.0,  # Cached, no cost
                character_count=meta["character_count"]
            )

        except Exception as e:
            logger.warning(f"Failed to load cached audio: {e}")
            return None

    async def _cache_audio(
        self,
        result: OpenAITTSResult,
        speed: float
    ) -> None:
        """Cache audio result."""
        import hashlib
        import json

        cache_key = hashlib.md5(
            f"{result.text}:{result.voice}:{result.model}:{speed}".encode()
        ).hexdigest()

        cache_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        meta_path = os.path.join(self.cache_dir, f"{cache_key}.json")

        try:
            # Save audio
            audio_bytes = base64.b64decode(result.audio_base64)
            with open(cache_path, "wb") as f:
                f.write(audio_bytes)

            # Save metadata
            meta = {
                "text": result.text,
                "model": result.model,
                "voice": result.voice,
                "duration": result.duration,
                "character_count": result.character_count,
                "cached_at": datetime.utcnow().isoformat()
            }
            with open(meta_path, "w") as f:
                json.dump(meta, f)

        except Exception as e:
            logger.warning(f"Failed to cache audio: {e}")

    def get_stats(self) -> Dict:
        """Get service statistics."""
        return {
            "total_requests": self.stats["total_requests"],
            "total_characters": self.stats["total_characters"],
            "total_cost": float(self.stats["total_cost"]),
            "cache_hits": self.stats["cache_hits"],
            "cache_enabled": self.enable_caching
        }


# Singleton instance
_openai_tts_service: Optional[OpenAITTSService] = None


def get_openai_tts_service() -> OpenAITTSService:
    """
    Get or create singleton OpenAITTSService instance.

    Returns:
        OpenAITTSService instance
    """
    global _openai_tts_service

    if _openai_tts_service is None:
        _openai_tts_service = OpenAITTSService()

    return _openai_tts_service

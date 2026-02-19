#!/usr/bin/env python3
"""
Whisper API Client for standalone whisper.ailabsafrica.com service.

This client provides the same interface as faster_whisper_service.py
but calls the standalone GPU-accelerated Whisper API instead of loading
models locally.

Usage:
    from services.whisper_api_client import get_whisper_api_client

    client = get_whisper_api_client()
    result = await client.transcribe_audio("audio.wav", language="en")
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WhisperTranscriptionResult:
    """
    Result from Whisper API - matches FasterWhisperTranscriptionResult.

    This is identical to the format in faster_whisper_service.py
    """
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]]
    task: str = "transcribe"
    model: str = ""
    model_size: str = ""


class WhisperAPIClient:
    """
    Client for standalone Whisper API at whisper.ailabsafrica.com.

    Provides the same interface as FasterWhisperService but uses
    the dedicated GPU-accelerated service instead of local inference.
    """

    def __init__(
        self,
        base_url: str = None,
        timeout: float = 300.0,  # 5 minute timeout for long audio
        default_model: str = "base"  # Changed to match RunPod service default
    ):
        """
        Initialize Whisper API client.

        Args:
            base_url: Base URL of the Whisper API (default: whisper.ailabsafrica.com)
            timeout: Request timeout in seconds
            default_model: Default model to use (tiny, base, small, medium, large-v2, large-v3)
        """
        self.base_url = base_url or os.getenv(
            "WHISPER_API_URL",
            "https://whisper.ailabsafrica.com"
        )
        self.timeout = timeout
        self.default_model = default_model

        # For compatibility with FasterWhisperService interface
        self.models_loaded = True
        self.models = {}

        logger.info(f"WhisperAPIClient initialized with base_url: {self.base_url}")

    async def initialize(self, model_size: str = "medium"):
        """
        Initialize is a no-op for the API client.
        Models are managed by the standalone service.
        """
        logger.info(f"WhisperAPIClient: Using standalone service for model {model_size}")
        self.default_model = model_size

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "auto",
        task: str = "transcribe",
        model_size: str = None,
        prompt: str = None
    ) -> WhisperTranscriptionResult:
        """
        Transcribe audio using the standalone Whisper API.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'tw', 'fr'). 'auto' for detection.
            task: Task type ('transcribe' or 'translate')
            model_size: Model to use (defaults to instance default)
            prompt: Optional prompt for better transcription

        Returns:
            WhisperTranscriptionResult with transcription details
        """
        model_size = model_size or self.default_model

        logger.info(f"Transcribing {audio_path} with model {model_size} via API")

        # Determine endpoint based on task
        if task == "translate":
            endpoint = f"{self.base_url}/v1/audio/translations"
        else:
            endpoint = f"{self.base_url}/v1/audio/transcriptions"

        # Prepare form data
        data = {
            "model": model_size,
            "response_format": "json",
            "temperature": "0.0"
        }

        if language and language != "auto":
            data["language"] = language

        if prompt:
            data["prompt"] = prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Read audio file
                audio_path = Path(audio_path)
                if not audio_path.exists():
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")

                with open(audio_path, "rb") as f:
                    files = {
                        "file": (audio_path.name, f, "audio/wav")
                    }

                    response = await client.post(
                        endpoint,
                        data=data,
                        files=files
                    )

                if response.status_code != 200:
                    logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                    raise Exception(f"Whisper API error: {response.status_code}")

                result = response.json()

                # Convert API response to WhisperTranscriptionResult
                segments = []
                for seg in result.get("segments", []):
                    segment_data = {
                        "text": seg.get("text", ""),
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 0.0),
                        "confidence": seg.get("confidence", 0.0),
                        "words": []
                    }

                    # Include word-level timestamps if available
                    for word in seg.get("words", []):
                        segment_data["words"].append({
                            "word": word.get("word", ""),
                            "start": word.get("start", 0.0),
                            "end": word.get("end", 0.0),
                            "probability": word.get("probability", 0.0)
                        })

                    segments.append(segment_data)

                transcription = WhisperTranscriptionResult(
                    text=result.get("text", ""),
                    language=result.get("language", language or "unknown"),
                    confidence=result.get("confidence", 0.0),
                    duration=result.get("duration", 0.0),
                    segments=segments,
                    task=result.get("task", task),
                    model=result.get("model", f"faster-whisper-{model_size}"),
                    model_size=result.get("model_size", model_size)
                )

                logger.info(f"Transcription complete: {len(transcription.text)} chars")
                return transcription

        except httpx.TimeoutException:
            logger.error(f"Whisper API timeout after {self.timeout}s")
            raise Exception(f"Whisper API timeout")
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            raise

    async def translate_audio(
        self,
        audio_path: str,
        target_language: str = "en",
        model_size: str = None
    ) -> WhisperTranscriptionResult:
        """
        Translate audio to English using the Whisper API.

        Args:
            audio_path: Path to audio file
            target_language: Target language (usually 'en')
            model_size: Model to use

        Returns:
            WhisperTranscriptionResult with translation
        """
        return await self.transcribe_audio(
            audio_path=audio_path,
            language="auto",
            task="translate",
            model_size=model_size
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the standalone Whisper API.

        Returns:
            Health status dict
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Status code: {response.status_code}"
                    }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }

    async def get_model_info(self, model_size: str = None) -> Dict[str, Any]:
        """
        Get information about available models.

        Args:
            model_size: Specific model to get info for

        Returns:
            Model information
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/models/loaded")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {}
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}


# Global instance
_whisper_api_client = None


def get_whisper_api_client(
    base_url: str = None,
    default_model: str = "base"  # Changed to match RunPod service default
) -> WhisperAPIClient:
    """
    Get singleton WhisperAPIClient instance.

    Args:
        base_url: Optional custom API URL
        default_model: Default model to use

    Returns:
        WhisperAPIClient instance
    """
    global _whisper_api_client

    if _whisper_api_client is None:
        _whisper_api_client = WhisperAPIClient(
            base_url=base_url,
            default_model=default_model
        )

    return _whisper_api_client

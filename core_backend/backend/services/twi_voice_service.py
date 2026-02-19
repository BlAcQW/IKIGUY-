"""
Twi Voice Service
Integrates MeloTTS and Faster-Whisper models via RunPod Serverless
Provides ASR and TTS capabilities for Twi language
"""

import os
import base64
import logging
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Pydantic Models
class TTSRequest(BaseModel):
    """Text-to-speech request model"""
    text: str = Field(..., description="Text to synthesize")
    speaker: str = Field(default="TWI-Speaker", description="Speaker ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    output_format: str = Field(default="base64", description="Output format: base64 or bytes")


class TTSResponse(BaseModel):
    """Text-to-speech response model"""
    audio: str = Field(..., description="Base64-encoded audio")
    sample_rate: int = Field(default=44100)
    duration: float = Field(..., description="Audio duration in seconds")
    text: str = Field(..., description="Input text")
    speaker: str = Field(..., description="Speaker ID")
    format: str = Field(..., description="Audio format")


class ASRRequest(BaseModel):
    """Automatic speech recognition request model"""
    audio: str = Field(..., description="Base64-encoded audio or file path")
    language: str = Field(default="tw", description="Language code")
    task: str = Field(default="transcribe", description="transcribe or translate")
    return_timestamps: bool = Field(default=True, description="Include word timestamps")
    vad_filter: bool = Field(default=True, description="Use voice activity detection")


class ASRSegment(BaseModel):
    """ASR segment with timestamps"""
    start: float
    end: float
    text: str
    words: Optional[List[Dict[str, Any]]] = None


class ASRResponse(BaseModel):
    """Automatic speech recognition response model"""
    text: str = Field(..., description="Full transcription")
    segments: List[ASRSegment] = Field(default_factory=list)
    language: str = Field(..., description="Detected language")
    language_probability: float
    duration: float = Field(..., description="Audio duration")
    num_segments: int


class TwiVoiceService:
    """Service for Twi voice operations (ASR + TTS)"""

    def __init__(self):
        """Initialize the Twi Voice Service"""
        # RunPod configuration
        self.runpod_api_key = os.getenv("RUNPOD_API_KEY")
        self.tts_endpoint_id = os.getenv("RUNPOD_TTS_ENDPOINT_ID")
        self.asr_endpoint_id = os.getenv("RUNPOD_ASR_ENDPOINT_ID")

        # Validate configuration
        if not self.runpod_api_key:
            logger.warning("RUNPOD_API_KEY not set - RunPod integration disabled")

        if not self.tts_endpoint_id:
            logger.warning("RUNPOD_TTS_ENDPOINT_ID not set - TTS disabled")

        if not self.asr_endpoint_id:
            logger.warning("RUNPOD_ASR_ENDPOINT_ID not set - ASR disabled")

        # HTTP client
        self.client = httpx.AsyncClient(timeout=120.0)

    async def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Convert text to speech using MeloTTS via RunPod

        Args:
            request: TTS request with text and parameters

        Returns:
            TTSResponse with audio and metadata

        Raises:
            Exception: If TTS fails
        """
        if not self.tts_endpoint_id or not self.runpod_api_key:
            raise Exception("TTS service not configured")

        try:
            url = f"https://api.runpod.ai/v2/{self.tts_endpoint_id}/runsync"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.runpod_api_key}"
            }

            payload = {
                "input": {
                    "text": request.text,
                    "speaker": request.speaker,
                    "speed": request.speed,
                    "output_format": request.output_format
                }
            }

            logger.info(f"TTS request: '{request.text[:50]}...' (speaker: {request.speaker})")

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("status") == "COMPLETED":
                output = result.get("output", {})
                return TTSResponse(**output)
            else:
                error_msg = result.get("error", "Unknown error")
                raise Exception(f"TTS failed: {error_msg}")

        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            raise

    async def speech_to_text(self, request: ASRRequest) -> ASRResponse:
        """
        Convert speech to text using Faster-Whisper via RunPod

        Args:
            request: ASR request with audio and parameters

        Returns:
            ASRResponse with transcription and metadata

        Raises:
            Exception: If ASR fails
        """
        if not self.asr_endpoint_id or not self.runpod_api_key:
            raise Exception("ASR service not configured")

        try:
            url = f"https://api.runpod.ai/v2/{self.asr_endpoint_id}/runsync"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.runpod_api_key}"
            }

            payload = {
                "input": {
                    "audio": request.audio,
                    "language": request.language,
                    "task": request.task,
                    "return_timestamps": request.return_timestamps,
                    "vad_filter": request.vad_filter
                }
            }

            logger.info(f"ASR request (language: {request.language}, task: {request.task})")

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("status") == "COMPLETED":
                output = result.get("output", {})

                # Convert segments
                segments = [ASRSegment(**seg) for seg in output.get("segments", [])]

                return ASRResponse(
                    text=output["text"],
                    segments=segments,
                    language=output["language"],
                    language_probability=output["language_probability"],
                    duration=output["duration"],
                    num_segments=len(segments)
                )
            else:
                error_msg = result.get("error", "Unknown error")
                raise Exception(f"ASR failed: {error_msg}")

        except Exception as e:
            logger.error(f"ASR error: {str(e)}")
            raise

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
twi_voice_service = TwiVoiceService()

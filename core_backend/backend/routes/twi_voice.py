"""
Twi Voice API Routes
Provides endpoints for Twi text-to-speech and speech-to-text
"""

import base64
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from typing import Optional

from backend.services.twi_voice_service import (
    twi_voice_service,
    TTSRequest,
    TTSResponse,
    ASRRequest,
    ASRResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twi-voice", tags=["Twi Voice"])


@router.post("/tts", response_model=TTSResponse, summary="Text-to-Speech (Twi)")
async def text_to_speech(request: TTSRequest):
    """
    Convert Twi text to speech

    **Parameters:**
    - **text**: Twi text to synthesize (required)
    - **speaker**: Speaker ID (default: "TWI-Speaker")
    - **speed**: Speech speed 0.5-2.0 (default: 1.0)
    - **output_format**: "base64" or "bytes" (default: "base64")

    **Returns:**
    - Base64-encoded audio
    - Sample rate
    - Duration
    - Input text and speaker

    **Example:**
    ```json
    {
      "text": "Akwaaba! Ɛte sɛn?",
      "speaker": "TWI-Speaker",
      "speed": 1.0
    }
    ```
    """
    try:
        response = await twi_voice_service.text_to_speech(request)
        return response

    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/audio", summary="Text-to-Speech (Twi) - Audio File")
async def text_to_speech_audio(
    text: str = Form(..., description="Twi text to synthesize"),
    speaker: str = Form(default="TWI-Speaker", description="Speaker ID"),
    speed: float = Form(default=1.0, ge=0.5, le=2.0, description="Speech speed")
):
    """
    Convert Twi text to speech and return WAV audio file

    **Parameters:**
    - **text**: Twi text to synthesize (form field)
    - **speaker**: Speaker ID (optional)
    - **speed**: Speech speed (optional)

    **Returns:**
    - WAV audio file (audio/wav)

    **Example Usage:**
    ```bash
    curl -X POST "https://api.ailabsafrica.com/twi-voice/tts/audio" \\
      -F "text=Akwaaba! Ɛte sɛn?" \\
      -F "speaker=TWI-Speaker" \\
      -F "speed=1.0" \\
      -o output.wav
    ```
    """
    try:
        # Create TTS request
        request = TTSRequest(
            text=text,
            speaker=speaker,
            speed=speed,
            output_format="base64"
        )

        # Get TTS response
        response = await twi_voice_service.text_to_speech(request)

        # Decode base64 audio
        audio_bytes = base64.b64decode(response.audio)

        # Return as audio file
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=twi_tts_{text[:20]}.wav"
            }
        )

    except Exception as e:
        logger.error(f"TTS audio error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/asr", response_model=ASRResponse, summary="Speech-to-Text (Twi)")
async def speech_to_text(request: ASRRequest):
    """
    Convert Twi speech to text

    **Parameters:**
    - **audio**: Base64-encoded audio (required)
    - **language**: Language code (default: "tw")
    - **task**: "transcribe" or "translate" (default: "transcribe")
    - **return_timestamps**: Include word timestamps (default: true)
    - **vad_filter**: Use voice activity detection (default: true)

    **Returns:**
    - Full transcription
    - Segments with timestamps
    - Detected language and probability
    - Audio duration

    **Example:**
    ```json
    {
      "audio": "UklGRh4AAABXQVZFZm10...",
      "language": "tw",
      "task": "transcribe",
      "return_timestamps": true
    }
    ```
    """
    try:
        response = await twi_voice_service.speech_to_text(request)
        return response

    except Exception as e:
        logger.error(f"ASR error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/asr/upload", response_model=ASRResponse, summary="Speech-to-Text (Twi) - Upload File")
async def speech_to_text_upload(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, etc.)"),
    language: str = Form(default="tw", description="Language code"),
    task: str = Form(default="transcribe", description="transcribe or translate"),
    return_timestamps: bool = Form(default=True, description="Include timestamps")
):
    """
    Convert Twi speech to text by uploading an audio file

    **Parameters:**
    - **file**: Audio file (WAV, MP3, FLAC, etc.)
    - **language**: Language code (optional, default: "tw")
    - **task**: Task type (optional, default: "transcribe")
    - **return_timestamps**: Include timestamps (optional, default: true)

    **Returns:**
    - Full transcription
    - Segments with timestamps
    - Detected language
    - Audio duration

    **Example Usage:**
    ```bash
    curl -X POST "https://api.ailabsafrica.com/twi-voice/asr/upload" \\
      -F "file=@audio.wav" \\
      -F "language=tw" \\
      -F "task=transcribe"
    ```
    """
    try:
        # Read audio file
        audio_bytes = await file.read()

        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Create ASR request
        request = ASRRequest(
            audio=audio_b64,
            language=language,
            task=task,
            return_timestamps=return_timestamps,
            vad_filter=True
        )

        # Get ASR response
        response = await twi_voice_service.speech_to_text(request)

        return response

    except Exception as e:
        logger.error(f"ASR upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation", summary="Full Conversation (ASR + TTS)")
async def conversation(
    file: UploadFile = File(..., description="User audio input"),
    response_text: Optional[str] = Form(None, description="Optional: Pre-defined response text"),
    speaker: str = Form(default="TWI-Speaker", description="TTS speaker"),
    speed: float = Form(default=1.0, description="TTS speed")
):
    """
    Complete conversation cycle: ASR (user speech) → TTS (bot response)

    **Use Case**: Voice bot conversation
    1. User speaks in Twi (upload audio)
    2. ASR converts to text
    3. Your app processes the text (optional: provide response_text)
    4. TTS converts response back to speech
    5. Return both transcription and audio response

    **Parameters:**
    - **file**: User audio input (WAV, MP3, etc.)
    - **response_text**: Bot response text (if not provided, echo user's transcription)
    - **speaker**: TTS speaker ID
    - **speed**: TTS speech speed

    **Returns:**
    - user_transcription: What the user said
    - user_segments: Timestamped segments
    - response_text: Bot's response text
    - response_audio: Base64-encoded audio response
    - response_duration: Audio duration

    **Example Usage:**
    ```bash
    curl -X POST "https://api.ailabsafrica.com/twi-voice/conversation" \\
      -F "file=@user_audio.wav" \\
      -F "response_text=Meda wo ase! Me din de Kofi."
    ```
    """
    try:
        # Step 1: ASR - Transcribe user audio
        audio_bytes = await file.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        asr_request = ASRRequest(
            audio=audio_b64,
            language="tw",
            task="transcribe",
            return_timestamps=True
        )

        asr_response = await twi_voice_service.speech_to_text(asr_request)

        logger.info(f"User said: {asr_response.text}")

        # Step 2: Determine response text
        if not response_text:
            # Echo back what user said (for testing)
            response_text = f"Me tee sɛ woka sɛ: {asr_response.text}"

        # Step 3: TTS - Generate audio response
        tts_request = TTSRequest(
            text=response_text,
            speaker=speaker,
            speed=speed
        )

        tts_response = await twi_voice_service.text_to_speech(tts_request)

        logger.info(f"Bot responded: {response_text}")

        # Step 4: Return complete conversation
        return {
            "user_transcription": asr_response.text,
            "user_segments": [seg.dict() for seg in asr_response.segments],
            "user_duration": asr_response.duration,
            "response_text": response_text,
            "response_audio": tts_response.audio,
            "response_sample_rate": tts_response.sample_rate,
            "response_duration": tts_response.duration,
            "conversation_id": f"{file.filename}_{int(__import__('time').time())}"
        }

    except Exception as e:
        logger.error(f"Conversation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health Check")
async def health_check():
    """
    Check if Twi Voice services are available

    **Returns:**
    - tts_available: True if TTS is configured
    - asr_available: True if ASR is configured
    - status: "healthy" or "degraded"
    """
    tts_available = bool(twi_voice_service.tts_endpoint_id and twi_voice_service.runpod_api_key)
    asr_available = bool(twi_voice_service.asr_endpoint_id and twi_voice_service.runpod_api_key)

    status = "healthy" if (tts_available and asr_available) else "degraded"

    return {
        "status": status,
        "tts_available": tts_available,
        "asr_available": asr_available,
        "service": "Twi Voice API",
        "version": "1.0.0"
    }

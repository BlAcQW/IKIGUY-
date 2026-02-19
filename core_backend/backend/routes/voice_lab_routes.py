"""
Voice Lab Routes - ASR and TTS services for Twi/Akan languages
Integrated into core_backend to serve the B2C portal
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks, WebSocket, Form
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import json
import io
import base64
import time
from pydantic import BaseModel, Field
import asyncio
import httpx

from ..services.voice_lab_service import VoiceLabService
from ..services.unified_asr_service import get_unified_asr_service, ASRModel
from apps.shared.integration.ai_services import get_unified_tts_service, TTSModel
from ..services.gemini_service import get_gemini_service
from ..auth import get_current_account
from fastapi import Request, Header
from ..services import service_account_service
from ..services.conversation_manager import get_conversation_manager
# from ..services.simple_tts_service import SimpleTTSService  # TODO: File not found
from ..services.akan_tts_service import get_akan_tts_service
from ..services.voice_cloning_service import get_voice_cloning_service, VoiceCloneMetadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-lab", tags=["voice-lab"])

# Initialize Services
voice_lab_service = VoiceLabService()
unified_asr_service = get_unified_asr_service()
unified_tts_service = get_unified_tts_service()
gemini_service = get_gemini_service()


# Optional authentication dependency
async def get_optional_account(x_service_token: Optional[str] = Header(None)) -> Optional[Dict]:
    """Get current account if token is provided, otherwise return None."""
    if x_service_token:
        account = service_account_service.get_by_token(x_service_token)
        if account:
            return {"id": account.id, "name": account.name}
    return None


# Request/Response Models
class TranscribeRequest(BaseModel):
    """Request model for transcription"""
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    language: str = Field(default="tw", description="Language code")
    dialect: str = Field(default="asante", description="Dialect (asante, akuapem, fante)")
    model: str = Field(default="akan-whisper", description="ASR model to use")
    return_timestamps: bool = Field(default=False, description="Return word timestamps")
    enhance_text: bool = Field(default=True, description="Apply text enhancements")
    enable_streaming: bool = Field(default=False, description="Enable streaming mode")
    enable_vad: bool = Field(default=False, description="Enable voice activity detection")


class TranscribeResponse(BaseModel):
    """Response model for transcription"""
    text: str = Field(..., description="Transcribed text")
    enhanced_text: Optional[str] = Field(None, description="Enhanced text with numbers/dates processed")
    confidence: float = Field(..., description="Confidence score")
    language: str = Field(..., description="Detected language")
    dialect: Optional[str] = Field(None, description="Detected dialect")
    duration: float = Field(..., description="Audio duration in seconds")
    timestamps: Optional[List[Dict]] = Field(None, description="Word-level timestamps")
    processing_time: float = Field(..., description="Processing time in seconds")


class SynthesizeRequest(BaseModel):
    """Request model for TTS synthesis"""
    text: str = Field(..., description="Text to synthesize")
    language: str = Field(default="tw", description="Language code")
    dialect: str = Field(default="asante", description="Dialect")
    model: str = Field(default="akan-mms", description="TTS model to use")
    voice_id: str = Field(default="asante_male_1", description="Voice ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=0.0, ge=-5, le=5, description="Pitch adjustment")
    enhance_text: bool = Field(default=True, description="Process text enhancements before synthesis")
    output_format: str = Field(default="wav", description="Output format (wav, mp3)")


class VoiceInfo(BaseModel):
    """Voice information model"""
    voice_id: str
    name: str
    language: str
    dialect: str
    gender: str
    age_group: str
    description: str
    sample_url: Optional[str] = None


class VoiceCloneRequest(BaseModel):
    """Request for voice cloning"""
    reference_audio_base64: str = Field(..., description="Base64 encoded reference audio")
    text: str = Field(..., description="Text to synthesize in cloned voice")
    voice_name: str = Field(default="custom", description="Name for cloned voice")


class TextProcessRequest(BaseModel):
    """Request for text processing"""
    text: str = Field(..., description="Input text")
    dialect: str = Field(default="asante", description="Target dialect")
    expand_numbers: bool = Field(default=True, description="Expand numbers to words")
    expand_abbreviations: bool = Field(default=True, description="Expand abbreviations")
    process_datetime: bool = Field(default=True, description="Process date/time to Twi")
    generate_phonemes: bool = Field(default=False, description="Generate IPA phonemes")


@router.get("/")
async def voice_lab_info():
    """Get Voice Lab information"""
    return {
        "name": "Voice Lab",
        "version": "1.0.0",
        "description": "ASR and TTS services for Twi/Akan languages",
        "features": [
            "Speech-to-Text (ASR)",
            "Text-to-Speech (TTS)",
            "Voice Cloning",
            "Multi-dialect Support",
            "Enhanced Text Processing"
        ],
        "languages": ["tw"],
        "dialects": ["asante", "akuapem", "fante"]
    }


@router.get("/models")
async def get_models():
    """Get available ASR and TTS models with detailed information

    Returns:
        List of available models with their capabilities and statistics
    """
    try:
        # Get model info from unified services
        asr_info = unified_asr_service.get_model_info()
        tts_info = unified_tts_service.get_model_info()

        # Format ASR models
        asr_models = []
        for model_id, info in asr_info.items():
            try:
                asr_models.append({
                    "id": model_id,
                    "name": info["name"],
                    "accuracy": f"{info['accuracy']*100:.1f}%",
                    "languages": info["languages"],
                    "dialects": info.get("dialects", []),
                    "provider": info["provider"],
                    "status": "loaded" if info["loaded"] else "available",
                    "supports_streaming": info.get("supports_streaming", False),
                    "supports_timestamps": info.get("supports_timestamps", False),
                    "stats": info["stats"]
                })
            except Exception as e:
                logger.error(f"Failed to format ASR model {model_id}: {e}")
                continue

        # Format TTS models
        tts_models = []
        for model_id, info in tts_info.items():
            try:
                tts_models.append({
                    "id": model_id,
                    "name": info["name"],
                    "quality_score": info.get("quality_score", 0),
                    "languages": info["languages"],
                    "dialects": info.get("dialects", []),
                    "provider": info["provider"],
                    "status": "loaded" if info["loaded"] else "available",
                    "supports_cloning": info.get("supports_cloning", False),
                    "supports_speed_control": info.get("supports_speed_control", False),
                    "sample_rate": info.get("sample_rate", 16000),
                    "stats": info["stats"]
                })
            except Exception as e:
                logger.error(f"Failed to format TTS model {model_id}: {e}")
                continue

        return {
            "asr_models": asr_models,
            "tts_models": tts_models
        }
    except Exception as e:
        logger.error(f"Failed to get models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/models/stats")
async def get_model_statistics():
    """Get performance statistics for all models

    Returns:
        Detailed statistics for ASR and TTS models
    """
    return {
        "asr_statistics": unified_asr_service.get_statistics(),
        "tts_statistics": unified_tts_service.get_statistics()
    }


@router.get("/models/{model_type}/{model_id}")
async def get_model_details(model_type: str, model_id: str):
    """Get detailed information about a specific model

    Args:
        model_type: Type of model (asr or tts)
        model_id: Model identifier

    Returns:
        Detailed model information
    """
    try:
        if model_type == "asr":
            model_enum = ASRModel(model_id)
            return unified_asr_service.get_model_info(model_enum)
        elif model_type == "tts":
            model_enum = TTSModel(model_id)
            return unified_tts_service.get_model_info(model_enum)
        else:
            raise HTTPException(status_code=400, detail="Invalid model_type. Use 'asr' or 'tts'")
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: TranscribeRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Transcribe audio to text with model selection support

    Args:
        request: Transcription request with model selection
        current_account: Current authenticated account (optional)

    Returns:
        Transcription response
    """
    logger.info("=" * 60)
    logger.info("🎤 TRANSCRIBE REQUEST RECEIVED")
    logger.info(f"Model: {request.model}")
    logger.info(f"Language: {request.language}, Dialect: {request.dialect}")
    logger.info(f"VAD: {request.enable_vad}, Streaming: {request.enable_streaming}")

    try:
        # Use a default user_id if no account is provided
        user_id = current_account.get("id") if current_account else "anonymous"
        logger.info(f"User ID: {user_id}")

        # Decode audio
        logger.info("📝 Step 1: Decoding base64 audio...")
        import base64
        try:
            audio_bytes = base64.b64decode(request.audio_base64)
            logger.info(f"✅ Decoded {len(audio_bytes)} bytes of audio")
        except Exception as e:
            logger.error(f"❌ Failed to decode base64: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio: {str(e)}")

        # Convert to numpy array
        logger.info("📝 Step 2: Converting to audio array...")
        import io
        import soundfile as sf
        try:
            audio_io = io.BytesIO(audio_bytes)
            audio_data, sample_rate = sf.read(audio_io)
            logger.info(f"✅ Audio array shape: {audio_data.shape}, sample_rate: {sample_rate}")
        except Exception as e:
            logger.error(f"❌ Failed to read audio: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid audio format: {str(e)}")

        # Map model string to ASRModel enum
        logger.info("📝 Step 3: Mapping model...")
        try:
            asr_model = ASRModel(request.model)
            logger.info(f"✅ Using model: {asr_model.value}")
        except ValueError:
            logger.warning(f"⚠️ Unknown model {request.model}, defaulting to akan-whisper")
            asr_model = ASRModel.AKAN_WHISPER

        # Use unified ASR service
        logger.info("📝 Step 4: Calling unified ASR service...")
        try:
            result = await unified_asr_service.transcribe(
                audio_data=audio_data,
                sample_rate=sample_rate,
                model=asr_model,
                language=request.language,
                dialect=request.dialect,
                return_timestamps=request.return_timestamps,
                enable_vad=request.enable_vad,
                enable_streaming=request.enable_streaming,
                user_id=user_id
            )
            logger.info(f"✅ ASR completed: '{result.text}' (confidence: {result.confidence:.2%})")
        except Exception as e:
            logger.error(f"❌ ASR service failed: {e}")
            raise

        # Convert to response format
        logger.info("📝 Step 5: Building response...")
        response = TranscribeResponse(
            text=result.text,
            enhanced_text=result.text if request.enhance_text else None,
            confidence=result.confidence,
            language=result.language,
            dialect=result.dialect,
            duration=result.duration,
            timestamps=result.timestamps,
            processing_time=result.processing_time
        )
        logger.info(f"✅ Response ready: {len(result.text)} chars")
        logger.info("=" * 60)
        return response

    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ TRANSCRIPTION FAILED: {e}")
        logger.error("=" * 60)
        logger.exception("Full stack trace:")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize(
    request: SynthesizeRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Synthesize text to speech with model selection support

    Args:
        request: Synthesis request with model selection
        current_account: Current authenticated account (optional)

    Returns:
        Audio file response with base64 audio
    """
    try:
        # Use a default user_id if no account is provided
        user_id = current_account.get("id") if current_account else "anonymous"

        # Map model string to TTSModel enum
        try:
            tts_model = TTSModel(request.model)
        except ValueError:
            logger.warning(f"Unknown model {request.model}, using akan-mms")
            tts_model = TTSModel.AKAN_MMS

        # Use unified TTS service
        result = unified_tts_service.synthesize(
            text=request.text,
            model=tts_model,
            voice_id=request.voice_id,
            speed=request.speed,
            pitch=request.pitch,
            language=request.language,
            dialect=request.dialect,
            output_format=request.output_format,
            user_id=user_id
        )

        return {
            "audio_base64": result.audio_base64,
            "text": result.text,
            "voice_id": result.voice_id,
            "duration": result.duration,
            "sample_rate": result.sample_rate,
            "processing_time": result.processing_time,
            "model": result.model,
            "format": result.format
        }
    except Exception as e:
        logger.error(f"Synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices():
    """List available voices
    
    Returns:
        List of available voices
    """
    try:
        voices = await voice_lab_service.get_available_voices()
        return [VoiceInfo(**voice) for voice in voices]
    except Exception as e:
        logger.error(f"Failed to list voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone-voice")
async def clone_voice(
    request: VoiceCloneRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Clone a voice from reference audio
    
    Args:
        request: Voice cloning request
        current_account: Current authenticated account (optional)
        
    Returns:
        Synthesized audio in cloned voice
    """
    try:
        # Use a default user_id if no account is provided
        user_id = current_account.get("id") if current_account else "anonymous"
        
        result = await voice_lab_service.clone_voice(
            reference_audio_base64=request.reference_audio_base64,
            text=request.text,
            voice_name=request.voice_name,
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_languages():
    """Get supported languages and dialects
    
    Returns:
        Supported languages and dialects
    """
    return {
        "languages": [
            {
                "code": "tw",
                "name": "Twi/Akan",
                "dialects": [
                    {"code": "asante", "name": "Asante Twi"},
                    {"code": "akuapem", "name": "Akuapem Twi"},
                    {"code": "fante", "name": "Fante"},
                    {"code": "bono", "name": "Bono"}
                ]
            }
        ],
        "default_language": "tw",
        "default_dialect": "asante"
    }


@router.post("/process-text")
async def process_text(request: TextProcessRequest):
    """Process text with enhanced Twi processor
    
    Args:
        request: Text processing request
        
    Returns:
        Processed text with various enhancements
    """
    try:
        result = await voice_lab_service.process_text(
            text=request.text,
            dialect=request.dialect,
            expand_numbers=request.expand_numbers,
            expand_abbreviations=request.expand_abbreviations,
            process_datetime=request.process_datetime,
            generate_phonemes=request.generate_phonemes
        )
        return result
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/stream")
async def websocket_stream(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """WebSocket endpoint for real-time streaming ASR/TTS

    Args:
        websocket: WebSocket connection
        token: Authentication token
    """
    import uuid

    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"Voice Lab WebSocket connection established (session: {session_id})")

    try:
        # Verify authentication if token provided
        if token:
            # Validate token (implementation depends on your auth system)
            pass

        while True:
            # Receive message
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "audio_chunk":
                # Process audio chunk for streaming ASR
                audio_base64 = data.get("audio")
                dialect = data.get("dialect", "asante")
                audio_format = data.get("format", "auto")
                sample_rate = data.get("sample_rate", None)
                channels = data.get("channels", None)

                # Process chunk with session-based buffering
                result = await voice_lab_service.process_audio_chunk(
                    audio_base64,
                    dialect,
                    format=audio_format,
                    sample_rate_in=sample_rate,
                    channels=channels,
                    session_id=session_id
                )

                # Only send transcription if we have text (buffer is full)
                if result.get("text"):
                    await websocket.send_json({
                        "type": "partial_transcript",
                        "text": result.get("text", ""),
                        "is_final": result.get("is_final", False),
                        "confidence": result.get("confidence", 0.0)
                    })
                # Optionally send buffer fill status
                elif result.get("buffer_fill") is not None:
                    logger.debug(f"Buffer filling: {result['buffer_fill']*100:.1f}%")

            elif message_type == "synthesize_stream":
                # Stream TTS audio
                text = data.get("text")
                voice_id = data.get("voice_id", "asante_male_1")

                # Generate audio chunks
                async for chunk in voice_lab_service.synthesize_stream(text, voice_id):
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "chunk_id": chunk["id"],
                        "audio": chunk["audio"],
                        "is_final": chunk["is_final"]
                    })

            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})

            elif message_type == "close":
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up session buffer
        voice_lab_service.clear_stream_buffer(session_id)
        logger.info(f"Voice Lab WebSocket connection closed (session: {session_id})")


@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    dialect: str = "asante",
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Upload audio file for processing
    
    Args:
        file: Audio file
        dialect: Target dialect
        current_account: Current authenticated account (optional)
        
    Returns:
        Upload confirmation with file ID
    """
    try:
        # Use a default user_id if no account is provided
        user_id = current_account.get("id") if current_account else "anonymous"
        
        # Validate file type
        allowed_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/webm"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Process upload
        result = await voice_lab_service.process_audio_upload(
            content=content,
            filename=file.filename,
            content_type=file.content_type,
            dialect=dialect,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(current_account: Optional[Dict] = Depends(get_optional_account)):
    """Get Voice Lab usage statistics
    
    Args:
        current_account: Current authenticated account (optional)
        
    Returns:
        Usage statistics
    """
    try:
        # Use a default user_id if no account is provided
        user_id = current_account.get("id") if current_account else "anonymous"
        
        # Return basic stats for now
        return {
            "user_id": user_id,
            "total_requests": 0,
            "transcription_requests": 0,
            "synthesis_requests": 0,
            "total_duration": 0,
            "languages_used": ["tw", "en"],
            "models_used": ["akan-whisper", "akan-mms", "gtts"]
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dialects")
async def get_dialects():
    """Get supported Twi dialects
    
    Returns:
        List of supported dialects
    """
    return {
        "dialects": [
            {
                "code": "asante",
                "name": "Asante Twi",
                "description": "Most widely spoken Twi dialect",
                "region": "Ashanti Region",
                "speakers": "~7 million"
            },
            {
                "code": "akuapem", 
                "name": "Akuapem Twi",
                "description": "Twi dialect from Eastern Region",
                "region": "Eastern Region",
                "speakers": "~2 million"
            },
            {
                "code": "fante",
                "name": "Fante",
                "description": "Akan dialect from Central Region", 
                "region": "Central Region",
                "speakers": "~2.3 million"
            }
        ]
    }


@router.get("/datasets")
async def get_datasets():
    """Get available training datasets
    
    Returns:
        List of available datasets for voice training
    """
    return {
        "datasets": [
            {
                "id": "bible_tts_twi",
                "name": "BibleTTS Twi (Asante)",
                "language": "Twi",
                "speakers": 2,
                "duration": "12 hours",
                "description": "High-quality Asante Twi speech from biblical text readings",
                "source": "BibleTTS Research Project",
                "quality": "high",
                "available": True
            },
            {
                "id": "bible_tts_akuapem",
                "name": "BibleTTS Twi (Akuapem)",
                "language": "Twi",
                "speakers": 2,
                "duration": "10 hours",
                "description": "Natural Akuapem Twi speech recordings",
                "source": "BibleTTS Research Project",
                "quality": "high",
                "available": True
            },
            {
                "id": "ghananlp_twi",
                "name": "GhanaNLP Twi Corpus",
                "language": "Twi",
                "speakers": 15,
                "duration": "25 hours",
                "description": "Diverse Twi speech corpus from Ghana",
                "source": "GhanaNLP",
                "quality": "medium",
                "available": True
            },
            {
                "id": "meta_mms_ga",
                "name": "Meta MMS Ga Corpus",
                "language": "Ga",
                "speakers": 5,
                "duration": "8 hours",
                "description": "Ga language speech corpus from Meta MMS project",
                "source": "Meta AI",
                "quality": "medium",
                "available": True
            },
            {
                "id": "meta_mms_ewe",
                "name": "Meta MMS Ewe Corpus",
                "language": "Ewe",
                "speakers": 3,
                "duration": "6 hours",
                "description": "Ewe language speech corpus from Meta MMS project",
                "source": "Meta AI",
                "quality": "medium",
                "available": True
            }
        ]
    }


# ============= Voice Training Endpoints =============

async def handle_local_tts_training(provider: str, voice_data: Dict, dataset_id: str, job_id: str) -> tuple[bool, str]:
    """Handle training/creation with local TTS services"""
    
    # Map providers to their service ports
    service_ports = {
        "coqui_tts": 30040,
        "f5_tts": 30037,
        "melotts": 30039,
        "openvoice": 30041
    }
    
    port = service_ports.get(provider.lower())
    if not port:
        return False, f"Unknown provider: {provider}"
    
    try:
        # Check service health
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_response = await client.get(f"http://localhost:{port}/")
            if health_response.status_code != 200:
                return False, f"Service {provider} not responding"
            
            service_info = health_response.json()
            if not service_info.get("model_loaded", False):
                return False, f"Service {provider} model not loaded"
            
            # For now, just validate the service is ready
            # In full implementation, this would:
            # 1. Upload training data to service
            # 2. Start training job
            # 3. Return job status
            
            logger.info(f"✅ {provider} service ready for voice creation")
            return True, f"Voice creation started on {provider}"
            
    except Exception as e:
        logger.error(f"Error connecting to {provider} service: {e}")
        return False, f"Service connection failed: {str(e)}"


@router.post("/voice/train")
async def train_voice(
    request: dict,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Start voice training process
    
    Args:
        request: Voice training request with voice data and configuration
        current_account: Current authenticated account (optional)
        
    Returns:
        Training job details
    """
    try:
        # Extract training parameters
        voice_data = request.get("voiceData", {})
        dataset_id = request.get("dataset")
        training_config = request.get("config", {})
        
        user_id = current_account.get("id") if current_account else "anonymous"
        
        # Generate training job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Validate provider
        provider = voice_data.get("provider", "coqui_tts").lower()
        local_providers = ["coqui_tts", "f5_tts", "melotts", "openvoice"]
        external_providers = ["elevenlabs", "meta_mms", "11labs", "playht"]
        all_providers = local_providers + external_providers
        
        if provider not in [p.lower() for p in all_providers]:
            raise HTTPException(status_code=400, detail=f"Unsupported provider '{provider}'. Available: {[p.lower() for p in all_providers]}")
        
        # Handle local TTS services
        if provider in ["coqui_tts", "f5_tts", "melotts", "openvoice"]:
            # Route to appropriate local TTS service
            success, message = await handle_local_tts_training(provider, voice_data, dataset_id, job_id)
            
            if not success:
                raise HTTPException(status_code=500, detail=f"Local TTS training failed: {message}")
                
            status = "processing"
        else:
            # External provider - simulate for now
            status = "queued"
            message = "Voice training job queued successfully"
        
        logger.info(f"🚀 Starting voice training job {job_id} for user {user_id}")
        logger.info(f"   Provider: {provider}")
        logger.info(f"   Voice: {voice_data.get('name', 'Unnamed')}")
        logger.info(f"   Dataset: {dataset_id}")
        
        return {
            "job_id": job_id,
            "status": status,
            "message": message if 'message' in locals() else "Voice training started",
            "estimated_time": "5-15 minutes" if provider.lower() in local_providers else "15-30 minutes",
            "provider": provider,
            "voice_name": voice_data.get("name", "Unnamed Voice"),
            "dataset": dataset_id,
            "config": training_config,
            "progress_url": f"/api/voice-lab/voice/train/{job_id}/status"
        }
        
    except Exception as e:
        logger.error(f"Voice training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize-voice")
async def synthesize_with_created_voice(
    request: dict,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Synthesize speech using a created voice
    
    Args:
        request: Contains text, voice_id, and provider
        current_account: Current authenticated account (optional)
        
    Returns:
        Audio stream of synthesized speech
    """
    try:
        text = request.get("text", "Hello, this is a test.")
        voice_id = request.get("voice_id")
        provider = request.get("provider", "coqui_tts")
        gender = request.get("gender", "neutral")
        accent = request.get("accent", "neutral")
        language = request.get("language", "en")
        
        logger.info(f"🎙️ Synthesizing voice: {voice_id} with {provider}")
        logger.info(f"📝 Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        logger.info(f"🔧 Voice config - Gender: {gender}, Accent: {accent}, Language: {language}")
        
        # For now, route to the appropriate TTS service for synthesis
        if provider == "coqui_tts":
            port = 30040
        elif provider == "f5_tts":
            port = 30037
        elif provider == "melotts":
            port = 30039
        elif provider == "openvoice":
            port = 30041
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        # Make request to local TTS service
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First check if the service is available
            health_response = await client.get(f"http://localhost:{port}/")
            if health_response.status_code != 200:
                logger.error(f"❌ {provider} service not available")
                raise HTTPException(status_code=503, detail=f"{provider} service unavailable")
            
            service_info = health_response.json()
            if not service_info.get("model_loaded", False):
                logger.error(f"❌ {provider} model not loaded")
                raise HTTPException(status_code=503, detail=f"{provider} model not loaded")
            
            # Prepare TTS request with voice configuration
            tts_request = {
                "text": text, 
                "language": language,
                "gender": gender,
                "accent": accent,
                "speaker": gender  # Some TTS services use 'speaker' instead of 'gender'
            }
            
            tts_response = await client.post(
                f"http://localhost:{port}/synthesize",
                json=tts_request
            )
            
            if tts_response.status_code == 200:
                logger.info(f"✅ Voice synthesis successful with {provider}")
                
                # Check if response is JSON (error) or binary audio
                content_type = tts_response.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Handle JSON response with base64 audio
                    response_json = tts_response.json()
                    if "audio" in response_json:
                        import base64
                        audio_data = base64.b64decode(response_json["audio"])
                        return StreamingResponse(
                            io.BytesIO(audio_data),
                            media_type="audio/wav",
                            headers={"Content-Disposition": "attachment; filename=synthesized_voice.wav"}
                        )
                    else:
                        logger.error(f"❌ No audio data in JSON response")
                        raise HTTPException(status_code=500, detail="No audio data received")
                else:
                    # Handle binary audio response
                    return StreamingResponse(
                        io.BytesIO(tts_response.content),
                        media_type="audio/wav",
                        headers={"Content-Disposition": "attachment; filename=synthesized_voice.wav"}
                    )
            else:
                logger.error(f"❌ TTS service error: {tts_response.status_code}")
                raise HTTPException(status_code=500, detail="Voice synthesis failed")
                
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/train/{job_id}/status")
async def get_training_status(
    job_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Get voice training job status
    
    Args:
        job_id: Training job ID
        current_account: Current authenticated account (optional)
        
    Returns:
        Training job status and progress
    """
    try:
        # In production, this would query actual training status
        # For now, return mock status
        
        return {
            "job_id": job_id,
            "status": "training",
            "progress": 45,
            "message": "Training voice model...",
            "estimated_remaining": "12 minutes",
            "current_epoch": 450,
            "total_epochs": 1000,
            "loss": 0.0234,
            "created_at": "2025-09-09T06:00:00Z",
            "started_at": "2025-09-09T06:02:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/clone")
async def clone_voice(
    name: str = Form(...),
    description: str = Form(""),
    provider: str = Form("coqui"),
    audio_file: UploadFile = File(...),
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Clone a voice from uploaded audio sample
    
    Args:
        name: Voice name
        description: Voice description
        provider: TTS provider to use
        audio_file: Audio file for cloning
        current_account: Current authenticated account (optional)
        
    Returns:
        Voice cloning job details
    """
    try:
        user_id = current_account.get("id") if current_account else "anonymous"
        
        # Validate audio file
        if audio_file.content_type not in ["audio/wav", "audio/mp3", "audio/mpeg", "audio/m4a"]:
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Read audio file
        audio_data = await audio_file.read()
        
        if len(audio_data) < 1000:  # Minimum size check
            raise HTTPException(status_code=400, detail="Audio file too small")
        
        if len(audio_data) > 50 * 1024 * 1024:  # 50MB max
            raise HTTPException(status_code=400, detail="Audio file too large (max 50MB)")
        
        # Generate voice ID
        import uuid
        voice_id = str(uuid.uuid4())
        
        logger.info(f"🎭 Cloning voice '{name}' for user {user_id}")
        logger.info(f"   Provider: {provider}")
        logger.info(f"   Audio size: {len(audio_data)} bytes")
        
        # In production, this would:
        # 1. Process audio for cloning
        # 2. Create voice embedding
        # 3. Store voice model
        
        return {
            "voice_id": voice_id,
            "name": name,
            "description": description,
            "provider": provider,
            "status": "processing",
            "message": "Voice cloning in progress...",
            "estimated_time": "5-10 minutes",
            "created_at": datetime.now().isoformat(),
            "audio_duration": "3.5 seconds",  # Mock duration
            "quality_score": 0.85
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Batch Voice Cloning Endpoints
# ============================================================================

@router.post("/voices/batch-clone")
async def batch_clone_voices(
    providers: Optional[List[str]] = None,
    test_text: str = "Hello, this is a test of the cloned voice.",
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Batch clone all Ghanaian voices across specified TTS providers

    This endpoint clones all voices from /opt/kasaai/apps/voice-lab/voices/
    using the specified TTS providers (Coqui XTTS, OpenVoice, F5-TTS, StyleTTS2).

    Args:
        providers: List of provider names (default: all clone-capable providers)
        test_text: Text to use for testing cloned voices
        current_account: Current authenticated account (optional)

    Returns:
        Batch cloning results with metadata for each cloned voice
    """
    try:
        user_id = current_account.get("id") if current_account else "anonymous"
        logger.info(f"🚀 Starting batch voice cloning for user {user_id}")

        # Get voice cloning service
        cloning_service = get_voice_cloning_service()

        # Start batch cloning
        results = await cloning_service.batch_clone_voices(
            providers=providers,
            test_text=test_text
        )

        # Format response
        response = {
            "status": "completed",
            "total_voices": sum(len(voices) for voices in results.values()),
            "providers": {
                provider: {
                    "count": len(voices),
                    "voices": [voice.model_dump() for voice in voices]
                }
                for provider, voices in results.items()
            },
            "started_at": datetime.now().isoformat()
        }

        logger.info(f"✅ Batch cloning completed: {response['total_voices']} voices cloned")
        return response

    except Exception as e:
        logger.error(f"Batch voice cloning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/cloned")
async def list_cloned_voices(
    provider: Optional[str] = None,
    status: Optional[str] = None,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """List all cloned voices

    Args:
        provider: Filter by provider (optional)
        status: Filter by status (optional)
        current_account: Current authenticated account (optional)

    Returns:
        List of cloned voices with metadata
    """
    try:
        cloning_service = get_voice_cloning_service()
        voices = cloning_service.list_cloned_voices(provider=provider, status=status)

        return {
            "voices": [voice.model_dump() for voice in voices],
            "total": len(voices),
            "filter": {
                "provider": provider,
                "status": status
            }
        }

    except Exception as e:
        logger.error(f"Failed to list cloned voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/cloned/{voice_id}")
async def get_cloned_voice(
    voice_id: str,
    include_audio: bool = False,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Get details about a cloned voice

    Args:
        voice_id: Voice identifier
        include_audio: Include reference audio in response (base64 encoded)
        current_account: Current authenticated account (optional)

    Returns:
        Voice metadata and optionally reference audio
    """
    try:
        cloning_service = get_voice_cloning_service()

        # Get metadata
        metadata = cloning_service.get_voice_metadata(voice_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Voice not found")

        response = metadata.model_dump()

        # Include audio if requested
        if include_audio:
            audio_base64 = cloning_service.get_reference_audio_base64(voice_id)
            if audio_base64:
                response["reference_audio_base64"] = audio_base64

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cloned voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/cloned/{voice_id}/audio")
async def get_cloned_voice_audio(
    voice_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Get reference audio for a cloned voice

    Args:
        voice_id: Voice identifier
        current_account: Current authenticated account (optional)

    Returns:
        Reference audio as streaming response
    """
    try:
        cloning_service = get_voice_cloning_service()

        # Get audio bytes
        audio_bytes = cloning_service.get_reference_audio(voice_id)
        if not audio_bytes:
            raise HTTPException(status_code=404, detail="Voice audio not found")

        # Get metadata for filename
        metadata = cloning_service.get_voice_metadata(voice_id)
        filename = f"{metadata.name}_{metadata.provider}.wav" if metadata else "voice.wav"

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/voices/cloned/{voice_id}")
async def delete_cloned_voice(
    voice_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Delete a cloned voice

    Args:
        voice_id: Voice identifier
        current_account: Current authenticated account (optional)

    Returns:
        Deletion confirmation
    """
    try:
        user_id = current_account.get("id") if current_account else "anonymous"
        logger.info(f"Deleting cloned voice {voice_id} for user {user_id}")

        cloning_service = get_voice_cloning_service()
        success = cloning_service.delete_voice(voice_id)

        if not success:
            raise HTTPException(status_code=404, detail="Voice not found")

        return {
            "voice_id": voice_id,
            "status": "deleted",
            "message": "Voice successfully deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete cloned voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices/cloned/statistics")
async def get_cloning_statistics(
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Get statistics about cloned voices

    Args:
        current_account: Current authenticated account (optional)

    Returns:
        Statistics about cloned voices
    """
    try:
        cloning_service = get_voice_cloning_service()
        stats = await cloning_service.get_provider_statistics()

        return stats

    except Exception as e:
        logger.error(f"Failed to get cloning statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Conversational AI Endpoints =============

class ChatRequest(BaseModel):
    """Simplified chat request for frontend compatibility"""
    message: str = Field(..., description="User message text")
    model: str = Field(default="gemini-2.5-flash", description="LLM model to use")
    mode: str = Field(default="general", description="Conversation mode")
    history: List[Dict[str, str]] = Field(default=[], description="Conversation history")
    language: str = Field(default="tw", description="Language code")
    dialect: str = Field(default="asante", description="Dialect")


class ChatResponse(BaseModel):
    """Simplified chat response"""
    response: str = Field(..., description="AI response")
    model: str = Field(..., description="Model used")
    processing_time: float = Field(..., description="Processing time in seconds")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """
    Simplified chat endpoint for frontend compatibility.

    Provides conversational AI using Gemini with conversation history.

    Args:
        request: Chat request with message and history
        current_account: Current authenticated account (optional)

    Returns:
        AI response
    """
    try:
        start_time = time.time()
        user_id = current_account.get("id") if current_account else "anonymous"

        # Build conversation context
        context_messages = []

        # Add system prompt based on mode
        mode_prompts = {
            "healthcare": "You are a helpful healthcare assistant providing medical information in a clear, compassionate manner. Always remind users to consult healthcare professionals for specific medical advice.",
            "education": "You are an educational tutor helping students learn effectively. Provide clear explanations and encourage critical thinking.",
            "finance": "You are a financial advisor providing general financial guidance. Always remind users to consult licensed financial professionals for specific investment advice.",
            "general": "You are a helpful AI assistant providing accurate and useful information."
        }

        system_prompt = mode_prompts.get(request.mode, mode_prompts["general"])

        # If language is Twi, add language context
        if request.language == "tw":
            system_prompt += f" The user speaks {request.dialect.capitalize()} Twi. Provide responses that are culturally appropriate for Ghana."

        # Build full prompt with history
        conversation_text = f"{system_prompt}\n\n"

        for msg in request.history[-10:]:  # Last 10 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation_text += f"{role.capitalize()}: {content}\n"

        conversation_text += f"User: {request.message}\nAssistant:"

        # Generate response using Gemini
        # Note: Gemini 2.5 Flash uses "extended thinking" which can consume ~1000 tokens
        # for internal reasoning before generating response. Set higher limit to accommodate.
        response = await gemini_service.generate_content(
            prompt=conversation_text,
            temperature=0.7,
            max_output_tokens=2048  # Increased from 1000 to accommodate thinking tokens
        )

        processing_time = time.time() - start_time

        logger.info(f"✅ Chat response generated in {processing_time:.2f}s for user {user_id}")

        return ChatResponse(
            response=response["content"],
            model=request.model,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ChatStartRequest(BaseModel):
    """Request to start a chat session"""
    domain: str = Field(default="general", description="Domain: general, healthcare, education, finance")
    language: str = Field(default="tw", description="Language code")
    dialect: str = Field(default="asante", description="Dialect")


class ChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User message text")


class ChatVoiceRequest(BaseModel):
    """Request for voice chat"""
    session_id: str = Field(..., description="Chat session ID")
    audio_base64: str = Field(..., description="Base64 encoded audio")


@router.post("/chat/start")
async def start_chat(
    request: ChatStartRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Start a new chat conversation session
    
    Args:
        request: Chat start request
        current_account: Current authenticated account (optional)
        
    Returns:
        Session information with welcome message
    """
    try:
        user_id = current_account.get("id") if current_account else "anonymous"
        
        conversation_manager = get_conversation_manager()
        
        session_id = await conversation_manager.create_session(
            user_id=user_id,
            domain=request.domain,
            metadata={
                "language": request.language,
                "dialect": request.dialect
            }
        )
        
        session = conversation_manager.get_session(session_id)
        
        return {
            "session_id": session_id,
            "domain": request.domain,
            "welcome_message": session.messages[0]["content"] if session.messages else "",
            "created_at": session.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/message")
async def send_chat_message(
    request: ChatMessageRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Send text message in chat conversation
    
    Args:
        request: Chat message request
        current_account: Current authenticated account (optional)
        
    Returns:
        AI response
    """
    try:
        conversation_manager = get_conversation_manager()
        
        result = await conversation_manager.process_text_message(
            session_id=request.session_id,
            text=request.message
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/voice")
async def send_voice_message(
    request: ChatVoiceRequest,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Send voice message in chat conversation
    
    Args:
        request: Voice message request
        current_account: Current authenticated account (optional)
        
    Returns:
        Transcription and AI response
    """
    try:
        conversation_manager = get_conversation_manager()
        
        # Decode audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        result = await conversation_manager.process_voice_message(
            session_id=request.session_id,
            audio_data=audio_bytes
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process voice message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Get conversation history for a session
    
    Args:
        session_id: Chat session ID
        current_account: Current authenticated account (optional)
        
    Returns:
        Conversation history
    """
    try:
        conversation_manager = get_conversation_manager()
        
        history = conversation_manager.get_session_history(session_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {
            "session_id": session_id,
            "messages": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{session_id}/clear")
async def clear_chat_context(
    session_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Clear conversation context while keeping session
    
    Args:
        session_id: Chat session ID
        current_account: Current authenticated account (optional)
        
    Returns:
        Confirmation
    """
    try:
        conversation_manager = get_conversation_manager()
        
        conversation_manager.clear_session_context(session_id)
        
        return {
            "session_id": session_id,
            "status": "context_cleared"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{session_id}/export")
async def export_chat(
    session_id: str,
    format: str = "json",
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Export conversation data
    
    Args:
        session_id: Chat session ID
        format: Export format (json or text)
        current_account: Current authenticated account (optional)
        
    Returns:
        Exported conversation data
    """
    try:
        conversation_manager = get_conversation_manager()
        
        exported_data = conversation_manager.export_session(session_id, format)
        
        if not exported_data:
            raise HTTPException(status_code=404, detail="Session not found")
            
        if format == "json":
            return JSONResponse(content=json.loads(exported_data))
        else:
            return {"session_id": session_id, "format": format, "data": exported_data}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{session_id}/stats")
async def get_chat_stats(
    session_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """Get conversation statistics
    
    Args:
        session_id: Chat session ID
        current_account: Current authenticated account (optional)
        
    Returns:
        Session statistics
    """
    try:
        conversation_manager = get_conversation_manager()
        
        stats = conversation_manager.get_statistics(session_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/{session_id}/end")
async def end_chat(
    session_id: str,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """End chat session
    
    Args:
        session_id: Chat session ID
        current_account: Current authenticated account (optional)
        
    Returns:
        Final session data
    """
    try:
        conversation_manager = get_conversation_manager()
        
        session_data = conversation_manager.end_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Reference Voice Library Endpoints
# ============================================================================

@router.post("/reference-voices/validate")
async def validate_reference_audio(audio_base64: str):
    """Validate reference audio for voice cloning"""
    try:
        from ..services.voice_reference_library import AudioValidator

        result = AudioValidator.validate_base64_audio(audio_base64)
        return result

    except Exception as e:
        logger.error(f"Audio validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reference-voices/add")
async def add_reference_voice(
    request: Dict[str, Any]
):
    """Add a reference voice to the library"""
    try:
        from ..services.voice_reference_library import get_voice_reference_library

        voice_id = request.get("voice_id")
        audio_base64 = request.get("audio_base64")
        metadata = request.get("metadata")

        library = get_voice_reference_library()
        audio_bytes = base64.b64decode(audio_base64)

        result = library.add_reference_voice(
            voice_id=voice_id,
            audio_bytes=audio_bytes,
            metadata=metadata
        )

        return result

    except Exception as e:
        logger.error(f"Failed to add reference voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reference-voices")
async def list_reference_voices():
    """List all reference voices in the library"""
    try:
        from ..services.voice_reference_library import get_voice_reference_library

        library = get_voice_reference_library()
        voices = library.list_reference_voices()

        return {"voices": voices, "total": len(voices)}

    except Exception as e:
        logger.error(f"Failed to list reference voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reference-voices/{voice_id}")
async def get_reference_voice(voice_id: str):
    """Get a reference voice audio"""
    try:
        from ..services.voice_reference_library import get_voice_reference_library

        library = get_voice_reference_library()
        audio_bytes = library.get_reference_voice(voice_id)

        if audio_bytes:
            return {
                "voice_id": voice_id,
                "audio_base64": base64.b64encode(audio_bytes).decode('utf-8')
            }
        else:
            raise HTTPException(status_code=404, detail="Voice not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reference voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reference-voices/{voice_id}")
async def delete_reference_voice(voice_id: str):
    """Delete a reference voice from the library"""
    try:
        from ..services.voice_reference_library import get_voice_reference_library

        library = get_voice_reference_library()
        success = library.delete_reference_voice(voice_id)

        if success:
            return {"success": True, "message": f"Voice {voice_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Voice not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete reference voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    session_id: Optional[str] = None
):
    """WebSocket endpoint for real-time voice conversation with AI

    Args:
        websocket: WebSocket connection
        session_id: Optional existing session ID
    """
    await websocket.accept()
    logger.info("🔌 Chat WebSocket connection established")
    
    conversation_manager = get_conversation_manager()
    
    try:
        # Create or get session
        if not session_id:
            session_id = await conversation_manager.create_session(
                user_id="websocket_user",
                domain="general"
            )
            
            await websocket.send_json({
                "type": "session_created",
                "session_id": session_id
            })
        
        # Audio buffer for streaming
        audio_buffer = []
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            logger.info(f"📨 Received WebSocket message type: {message_type}")
            
            if message_type == "start_session":
                # Create new session with specified parameters
                domain = data.get("domain", "general")
                language = data.get("language", "tw")
                dialect = data.get("dialect", "asante")
                tts_provider = data.get("tts_provider", "akan")  # Default to Akan TTS
                
                session_id = await conversation_manager.create_session(
                    user_id="websocket_user",
                    domain=domain,
                    metadata={
                        "language": language,
                        "dialect": dialect,
                        "tts_provider": tts_provider
                    },
                    tts_provider=tts_provider
                )
                logger.info(f"✅ Session created: {session_id}")
                
                response = {
                    "type": "session_started",
                    "session_id": session_id
                }
                await websocket.send_json(response)
                logger.info(f"📤 Sent session_started response")
                
            elif message_type == "voice_message":
                # Process complete voice message
                audio_base64 = data.get("audio_base64")
                session_id_msg = data.get("session_id")
                logger.info(f"🎤 Processing voice message, Session: {session_id_msg}, Audio size: {len(audio_base64) if audio_base64 else 0} bytes")
                
                if audio_base64:
                    try:
                        audio_bytes = base64.b64decode(audio_base64)
                        logger.info(f"🎧 Decoded audio: {len(audio_bytes)} bytes")
                        
                        # Use session_id from message if provided, otherwise use current session
                        use_session_id = session_id_msg or session_id
                        
                        result = await conversation_manager.process_voice_message(
                            use_session_id,
                            audio_bytes
                        )
                    except Exception as e:
                        logger.error(f"❌ Error processing voice message: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to process audio: {str(e)}"
                        })
                        continue
                    logger.info(f"🤖 Got result - Transcription: {result['transcription'][:50]}... Response: {result['response'][:50]}...")
                    
                    # Send final transcription
                    transcription_msg = {
                        "type": "final_transcription",
                        "text": result["transcription"],
                        "confidence": result["confidence"],
                        "language": result["language"]
                    }
                    await websocket.send_json(transcription_msg)
                    
                    # Send AI response with audio
                    response_text = result["response"]
                    
                    # Generate TTS audio for response
                    audio_base64 = None
                    try:
                        # Get TTS provider from session metadata
                        session = conversation_manager.get_session(use_session_id)
                        tts_provider = session.metadata.get("tts_provider", "akan") if session else "akan"
                        
                        logger.info(f"🔊 Using TTS provider: {tts_provider}")
                        
                        if tts_provider == "akan":
                            # Use Akan TTS for native pronunciation
                            akan_tts = get_akan_tts_service()
                            audio_base64 = akan_tts.synthesize_to_base64(
                                text=response_text,
                                speed=1.0
                            )
                            if audio_base64:
                                logger.info(f"✅ Akan TTS audio generated: {len(audio_base64)} bytes (base64)")
                        else:
                            # Use gTTS as fallback
                            tts_service = SimpleTTSService()
                            tts_result = tts_service.synthesize(
                                text=response_text,
                                language="en",
                                speed=0.9
                            )
                            
                            if tts_result and tts_result.get("audio"):
                                # Convert audio bytes to base64
                                import base64 as b64
                                audio_base64 = b64.b64encode(tts_result["audio"]).decode('utf-8')
                                logger.info(f"✅ gTTS audio generated: {len(audio_base64)} bytes (base64)")
                        
                        if not audio_base64:
                            logger.warning(f"⚠️ No audio generated from TTS provider: {tts_provider}")
                    except Exception as e:
                        logger.error(f"❌ TTS generation failed: {e}", exc_info=True)
                    
                    response_msg = {
                        "type": "response",
                        "text": response_text,
                        "audio": audio_base64,
                        "turn_number": result["turn_number"]
                    }
                    await websocket.send_json(response_msg)
                    logger.info(f"📤 Sent response with audio: {audio_base64 is not None}")
                    
            elif message_type == "audio_chunk":
                # Add to buffer
                audio_base64 = data.get("audio")
                audio_bytes = base64.b64decode(audio_base64)
                audio_buffer.append(audio_bytes)
                
                # Check if end of speech
                if data.get("is_final"):
                    # Process complete audio
                    full_audio = b"".join(audio_buffer)
                    audio_buffer = []
                    
                    # Process through conversation manager
                    result = await conversation_manager.process_voice_message(
                        session_id,
                        full_audio
                    )
                    
                    # Send transcription
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result["transcription"],
                        "confidence": result["confidence"]
                    })
                    
                    # Send AI response with audio
                    response_text = result["response"]
                    
                    # Generate TTS audio for response
                    audio_base64 = None
                    try:
                        # Get TTS provider from session metadata
                        session = conversation_manager.get_session(use_session_id)
                        tts_provider = session.metadata.get("tts_provider", "akan") if session else "akan"
                        
                        logger.info(f"🔊 Using TTS provider: {tts_provider}")
                        
                        if tts_provider == "akan":
                            # Use Akan TTS for native pronunciation
                            akan_tts = get_akan_tts_service()
                            audio_base64 = akan_tts.synthesize_to_base64(
                                text=response_text,
                                speed=1.0
                            )
                            if audio_base64:
                                logger.info(f"✅ Akan TTS audio generated: {len(audio_base64)} bytes (base64)")
                        else:
                            # Use gTTS as fallback
                            tts_service = SimpleTTSService()
                            tts_result = tts_service.synthesize(
                                text=response_text,
                                language="en",
                                speed=0.9
                            )
                            
                            if tts_result and tts_result.get("audio"):
                                # Convert audio bytes to base64
                                import base64 as b64
                                audio_base64 = b64.b64encode(tts_result["audio"]).decode('utf-8')
                                logger.info(f"✅ gTTS audio generated: {len(audio_base64)} bytes (base64)")
                        
                        if not audio_base64:
                            logger.warning(f"⚠️ No audio generated from TTS provider: {tts_provider}")
                    except Exception as e:
                        logger.error(f"❌ TTS generation failed: {e}", exc_info=True)
                    
                    response_msg = {
                        "type": "response",
                        "text": response_text,
                        "audio": audio_base64,
                        "turn_number": result["turn_number"]
                    }
                    await websocket.send_json(response_msg)
                    logger.info(f"📤 Sent response with audio: {audio_base64 is not None}")
                    
            elif message_type == "change_tts_provider":
                # Change TTS provider for the session
                new_tts_provider = data.get("tts_provider", "akan")
                session_id_msg = data.get("session_id") or session_id
                
                logger.info(f"🔊 Changing TTS provider to: {new_tts_provider} for session: {session_id_msg}")
                
                # Update session metadata with new TTS provider
                if session_id_msg:
                    # Update in Redis
                    redis_manager = conversation_manager.redis_manager
                    redis_manager.update_tts_provider(session_id_msg, new_tts_provider)
                    
                    # Update local session if exists
                    session = conversation_manager.sessions.get(session_id_msg)
                    if session:
                        session.metadata["tts_provider"] = new_tts_provider
                    
                    await websocket.send_json({
                        "type": "tts_provider_changed",
                        "tts_provider": new_tts_provider,
                        "session_id": session_id_msg
                    })
                    logger.info(f"✅ TTS provider changed to: {new_tts_provider}")
                
            elif message_type == "text_message":
                # Process text message
                text = data.get("text")
                
                result = await conversation_manager.process_text_message(
                    session_id,
                    text
                )
                
                # Send response with audio
                response_text = result["response"]
                
                # Generate TTS audio for response (optional - only if TTS is available)
                audio_base64 = None
                try:
                    # Simple fallback - just send text for now
                    # TODO: Integrate actual TTS when service is ready
                    pass
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e}")
                
                await websocket.send_json({
                    "type": "response",
                    "text": response_text,
                    "audio": audio_base64,  # Will be None for now
                    "turn_number": result["turn_number"]
                })
                
            elif message_type == "change_domain":
                # Change conversation domain
                domain = data.get("domain", "general")
                conversation_manager.update_session_domain(session_id, domain)
                
                await websocket.send_json({
                    "type": "domain_changed",
                    "domain": domain
                })
                
            elif message_type == "change_tts_provider":
                # Change TTS provider
                tts_provider = data.get("tts_provider", "akan")
                session = conversation_manager.get_session(session_id)
                if session:
                    session.metadata["tts_provider"] = tts_provider
                    logger.info(f"🔊 Changed TTS provider to: {tts_provider}")
                
                await websocket.send_json({
                    "type": "tts_provider_changed",
                    "tts_provider": tts_provider
                })
                
            elif message_type == "get_history":
                # Send conversation history
                history = conversation_manager.get_session_history(session_id)
                
                await websocket.send_json({
                    "type": "history",
                    "messages": history
                })
                
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
                
            elif message_type == "close":
                break
                
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        logger.info(f"Chat WebSocket connection closed for session {session_id}")


# ==================== Library Voice Management Routes ====================

from ..services.library_voice_service import get_library_voice_service


class LibraryVoiceCreate(BaseModel):
    """Request model for creating a library voice"""
    voice_id: str
    name: str
    file_path: str
    gender: str = "neutral"
    accent: str = "neutral"
    language: str = "en"
    description: str = ""
    is_featured: bool = False
    tags: List[str] = []


class LibraryVoiceUpdate(BaseModel):
    """Request model for updating a library voice"""
    name: Optional[str] = None
    file_path: Optional[str] = None
    gender: Optional[str] = None
    accent: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[str] = None


@router.get("/library-voices")
async def list_library_voices(
    gender: Optional[str] = None,
    language: Optional[str] = None,
    accent: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    tags: Optional[str] = None
):
    """
    List all library voices with optional filters.

    Args:
        gender: Filter by gender (male, female, neutral)
        language: Filter by language code
        accent: Filter by accent
        is_active: Filter by active status
        is_featured: Filter by featured status
        tags: Comma-separated list of tags

    Returns:
        List of library voices
    """
    try:
        service = get_library_voice_service()

        # Parse tags if provided
        tags_list = tags.split(",") if tags else None

        voices = await service.list_voices(
            gender=gender,
            language=language,
            accent=accent,
            is_active=is_active,
            is_featured=is_featured,
            tags=tags_list
        )

        return {
            "voices": voices,
            "count": len(voices)
        }
    except Exception as e:
        logger.error(f"Error listing library voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list library voices: {str(e)}")


@router.get("/library-voices/{voice_id}")
async def get_library_voice(voice_id: str):
    """
    Get a specific library voice by ID.

    Args:
        voice_id: Unique voice identifier

    Returns:
        Library voice metadata
    """
    try:
        service = get_library_voice_service()
        voice = await service.get_voice(voice_id)

        if not voice:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

        return voice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting library voice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get library voice: {str(e)}")


@router.post("/library-voices")
async def create_library_voice(
    voice: LibraryVoiceCreate,
    current_account: Optional[Dict] = Depends(get_optional_account)
):
    """
    Create a new library voice entry.

    Args:
        voice: Voice creation data
        current_account: Current user account (if authenticated)

    Returns:
        Created library voice metadata
    """
    try:
        service = get_library_voice_service()

        uploaded_by = current_account.get("id") if current_account else None

        created_voice = await service.create_voice(
            voice_id=voice.voice_id,
            name=voice.name,
            file_path=voice.file_path,
            gender=voice.gender,
            accent=voice.accent,
            language=voice.language,
            description=voice.description,
            is_featured=voice.is_featured,
            tags=voice.tags,
            uploaded_by=uploaded_by
        )

        return created_voice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating library voice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create library voice: {str(e)}")


@router.put("/library-voices/{voice_id}")
async def update_library_voice(
    voice_id: str,
    updates: LibraryVoiceUpdate
):
    """
    Update a library voice.

    Args:
        voice_id: Unique voice identifier
        updates: Fields to update

    Returns:
        Updated library voice metadata
    """
    try:
        service = get_library_voice_service()

        # Filter out None values
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}

        updated_voice = await service.update_voice(voice_id, **update_dict)

        if not updated_voice:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

        return updated_voice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating library voice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update library voice: {str(e)}")


@router.delete("/library-voices/{voice_id}")
async def delete_library_voice(
    voice_id: str,
    delete_file: bool = False
):
    """
    Delete a library voice.

    Args:
        voice_id: Unique voice identifier
        delete_file: Whether to also delete the audio file from disk

    Returns:
        Deletion status
    """
    try:
        service = get_library_voice_service()

        deleted = await service.delete_voice(voice_id, delete_file=delete_file)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

        return {
            "success": True,
            "message": f"Voice '{voice_id}' deleted successfully",
            "file_deleted": delete_file
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting library voice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete library voice: {str(e)}")


@router.post("/library-voices/migrate")
async def migrate_library_voices(
    voices_dir: str = "/opt/kasaai/apps/voice-lab/voices"
):
    """
    Migrate existing voice files from directory to MongoDB.

    This is a one-time migration endpoint to populate the database
    with existing voice files.

    Args:
        voices_dir: Directory containing voice files

    Returns:
        Migration summary
    """
    try:
        service = get_library_voice_service()

        result = await service.migrate_from_hardcoded(voices_dir)

        return result
    except Exception as e:
        logger.error(f"Error migrating library voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate library voices: {str(e)}")


@router.post("/library-voices/upload")
async def upload_library_voice(
    audio: UploadFile = File(...),
    voice_id: str = Form(...),
    name: str = Form(...),
    gender: str = Form("neutral"),
    accent: str = Form("neutral"),
    language: str = Form("en"),
    description: str = Form(""),
    is_featured: bool = Form(False),
    tags: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None)
):
    """
    Upload an audio file directly to the library.

    This endpoint accepts audio files (recorded or uploaded) and adds them
    to the voice library for use in voice cloning.

    Args:
        audio: Audio file (WAV, MP3, etc.)
        voice_id: Unique identifier for the voice
        name: Display name for the voice
        gender: Voice gender (male, female, neutral)
        accent: Voice accent/dialect
        language: Primary language code
        description: Voice description
        is_featured: Whether to feature this voice
        tags: Comma-separated list of tags
        uploaded_by: User ID who uploaded the voice

    Returns:
        Created library voice metadata
    """
    try:
        import os
        import shutil
        from pathlib import Path

        service = get_library_voice_service()

        # Check if voice_id already exists
        existing = await service.get_voice(voice_id)
        if existing:
            raise HTTPException(status_code=400, detail=f"Voice with ID '{voice_id}' already exists")

        # Validate audio file
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Determine file extension
        file_extension = audio.filename.split(".")[-1] if "." in audio.filename else "wav"

        # Create voices directory if it doesn't exist
        voices_dir = Path("/opt/kasaai/apps/voice-lab/voices")
        voices_dir.mkdir(parents=True, exist_ok=True)

        # Save audio file to disk
        file_path = voices_dir / f"{voice_id}.{file_extension}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        logger.info(f"Saved audio file to {file_path}")

        # Parse tags
        tags_list = [t.strip() for t in tags.split(",")] if tags else []

        # Create voice entry in database
        voice = await service.create_voice(
            voice_id=voice_id,
            name=name,
            file_path=str(file_path),
            gender=gender,
            accent=accent,
            language=language,
            description=description,
            is_featured=is_featured,
            tags=tags_list,
            uploaded_by=uploaded_by
        )

        logger.info(f"Created library voice: {voice_id}")

        return voice

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading library voice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload library voice: {str(e)}")


@router.get("/library-voices/{voice_id}/audio")
async def get_library_voice_audio(voice_id: str):
    """
    Get the audio file for a library voice.

    This endpoint serves the actual audio file for playback/preview.

    Args:
        voice_id: Voice ID to get audio for

    Returns:
        Audio file as streaming response
    """
    try:
        import os
        from fastapi.responses import FileResponse

        service = get_library_voice_service()

        # Get voice metadata
        voice = await service.get_voice(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

        # Check if file exists
        file_path = voice.get('file_path')
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Audio file not found for voice '{voice_id}'")

        # Determine media type
        if file_path.endswith('.mp3'):
            media_type = 'audio/mpeg'
        elif file_path.endswith('.ogg'):
            media_type = 'audio/ogg'
        elif file_path.endswith('.webm'):
            media_type = 'audio/webm'
        else:
            media_type = 'audio/wav'

        # Return file
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=f"{voice_id}.{file_path.split('.')[-1]}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting library voice audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get library voice audio: {str(e)}")


# ============================================================================
# FASTER-WHISPER ENDPOINTS (Medium and Large-v3 models)
# ============================================================================

from ..services.whisper_api_client import get_whisper_api_client

# Use RunPod Whisper API service (whisper.ailabsafrica.com)
whisper_api_client = get_whisper_api_client(default_model="base")


@router.post("/whisper-medium/transcribe")
async def transcribe_whisper_medium(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe"),
    return_timestamps: bool = Form(True)
):
    """
    Transcribe audio using Faster-Whisper Medium model (1.5GB).

    Args:
        file: Audio file to transcribe
        language: Language code (e.g., 'en', 'tw', 'ak'). Auto-detect if None.
        task: "transcribe" or "translate"
        return_timestamps: Return word-level timestamps

    Returns:
        Transcription result with text, language, segments, and metadata
    """
    import tempfile
    import os

    try:
        logger.info(f"📥 Whisper Medium transcription request: {file.filename}")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Use RunPod Whisper API service
            result = await whisper_api_client.transcribe_audio(
                audio_path=temp_path,
                language=language,
                task=task,
                model_size="medium"
            )

            return {
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
                "duration": result.duration,
                "segments": result.segments if return_timestamps else None,
                "model": "faster-whisper-medium",
                "model_size": "medium"
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Whisper Medium transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whisper-large/transcribe")
async def transcribe_whisper_large(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe"),
    return_timestamps: bool = Form(True)
):
    """
    Transcribe audio using Faster-Whisper Large-v3 model (3.1GB).
    Most accurate multilingual model.

    Args:
        file: Audio file to transcribe
        language: Language code (e.g., 'en', 'tw', 'ak'). Auto-detect if None.
        task: "transcribe" or "translate"
        return_timestamps: Return word-level timestamps

    Returns:
        Transcription result with text, language, segments, and metadata
    """
    import tempfile
    import os

    try:
        logger.info(f"📥 Whisper Large-v3 transcription request: {file.filename}")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Use RunPod Whisper API service
            result = await whisper_api_client.transcribe_audio(
                audio_path=temp_path,
                language=language,
                task=task,
                model_size="large-v3"
            )

            return {
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
                "duration": result.duration,
                "segments": result.segments if return_timestamps else None,
                "model": "faster-whisper-large-v3",
                "model_size": "large-v3"
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Whisper Large-v3 transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faster-whisper/transcribe")
async def transcribe_faster_whisper(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    model_size: str = Form("medium"),
    task: str = Form("transcribe"),
    return_timestamps: bool = Form(True)
):
    """
    Transcribe audio using Faster-Whisper with configurable model size.

    Args:
        file: Audio file to transcribe
        language: Language code (e.g., 'en', 'tw', 'ak'). Auto-detect if None.
        model_size: Model size ("medium", "large-v3")
        task: "transcribe" or "translate"
        return_timestamps: Return word-level timestamps

    Returns:
        Transcription result with text, language, segments, and metadata
    """
    import tempfile
    import os

    try:
        logger.info(f"📥 Faster-Whisper ({model_size}) transcription request: {file.filename}")

        # Validate model size
        if model_size not in ["medium", "large-v3"]:
            raise HTTPException(status_code=400, detail=f"Invalid model_size: {model_size}. Use 'medium' or 'large-v3'")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Use RunPod Whisper API service
            result = await whisper_api_client.transcribe_audio(
                audio_path=temp_path,
                language=language,
                task=task,
                model_size=model_size
            )

            return {
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
                "duration": result.duration,
                "segments": result.segments if return_timestamps else None,
                "model": f"faster-whisper-{model_size}",
                "model_size": model_size
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Faster-Whisper transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
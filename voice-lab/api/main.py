#!/usr/bin/env python3
"""
Voice Lab API - FastAPI backend for Twi/Akan ASR and TTS services
Provides REST and WebSocket endpoints for voice processing

Also includes a comprehensive directory of all TTS, ASR, and LLM services.
"""

from fastapi import FastAPI, File, UploadFile, WebSocket, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
import asyncio
import torch
import torchaudio
import numpy as np
from pathlib import Path
import tempfile
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import io
import base64
from pydantic import BaseModel, Field
import uvicorn

# Import directory module
from directory import (
    ServiceCategory,
    ServiceStatus,
    DeploymentType,
    ServiceEndpoint,
    ServiceDirectory,
    get_service_directory,
    get_services_by_category,
    get_active_services,
    get_services_with_feature,
    get_services_by_language,
    get_services_by_deployment,
    get_directory_summary,
    TTS_SERVICES,
    ASR_SERVICES,
    LLM_SERVICES,
    TOOLS_SERVICES,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    # Try to import enhanced processor
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "enhanced_twi_processor",
        str(Path(__file__).parent.parent / "notebooks" / "000_enhanced_twi_processor.py")
    )
    enhanced_twi_processor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enhanced_twi_processor)
    from enhanced_twi_processor import EnhancedTwiTextProcessor
except:
    logger.warning("Enhanced Twi processor not found, using basic text processing")
    EnhancedTwiTextProcessor = None


# Request/Response Models
class TranscribeRequest(BaseModel):
    """Request model for transcription"""
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    language: str = Field(default="tw", description="Language code")
    dialect: str = Field(default="asante", description="Dialect (asante, akuapem, fante)")
    return_timestamps: bool = Field(default=False, description="Return word timestamps")
    enhance_text: bool = Field(default=True, description="Apply text enhancements")


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


# Global model storage
models = {}
text_processor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Starting Voice Lab API...")
    
    # Initialize text processor
    global text_processor
    if EnhancedTwiTextProcessor:
        text_processor = EnhancedTwiTextProcessor(dialect="asante")
        logger.info("Enhanced Twi text processor initialized")
    
    # Load models (placeholder - actual model loading would go here)
    models["asr"] = {"loaded": True, "type": "whisper"}
    models["tts"] = {"loaded": True, "type": "coqui"}
    
    logger.info("Models loaded successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voice Lab API...")
    models.clear()


# Create FastAPI app
app = FastAPI(
    title="Voice Lab API",
    description="ASR and TTS services for Twi/Akan languages",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:8080", 
        "https://api.ailabsafrica.com",
        "https://kasaai.ailabsafrica.com",
        "http://kasaai.ailabsafrica.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def decode_audio(audio_base64: str) -> tuple[np.ndarray, int]:
    """Decode base64 audio to numpy array
    
    Args:
        audio_base64: Base64 encoded audio
        
    Returns:
        Audio array and sample rate
    """
    try:
        # Decode base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Load audio
        audio_io = io.BytesIO(audio_bytes)
        waveform, sample_rate = torchaudio.load(audio_io)
        
        # Convert to numpy
        audio_array = waveform.numpy()
        
        return audio_array, sample_rate
        
    except Exception as e:
        logger.error(f"Failed to decode audio: {e}")
        raise HTTPException(status_code=400, detail="Invalid audio data")


def encode_audio(audio_array: np.ndarray, sample_rate: int, format: str = "wav") -> str:
    """Encode audio array to base64
    
    Args:
        audio_array: Audio numpy array
        sample_rate: Sample rate
        format: Output format
        
    Returns:
        Base64 encoded audio
    """
    try:
        # Convert to tensor
        waveform = torch.from_numpy(audio_array)
        
        # Save to bytes
        audio_io = io.BytesIO()
        torchaudio.save(audio_io, waveform, sample_rate, format=format)
        
        # Encode to base64
        audio_io.seek(0)
        audio_base64 = base64.b64encode(audio_io.read()).decode('utf-8')
        
        return audio_base64
        
    except Exception as e:
        logger.error(f"Failed to encode audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to encode audio")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Voice Lab API",
        "version": "1.0.0",
        "status": "running",
        "models": {
            "asr": models.get("asr", {}).get("loaded", False),
            "tts": models.get("tts", {}).get("loaded", False)
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": len(models) > 0
    }


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest):
    """Transcribe audio to text
    
    Args:
        request: Transcription request
        
    Returns:
        Transcription response
    """
    start_time = datetime.now()
    
    try:
        # Decode audio
        audio_array, sample_rate = decode_audio(request.audio_base64)
        
        # Calculate duration
        duration = len(audio_array[0]) / sample_rate
        
        # Perform transcription (placeholder - actual ASR would go here)
        # In production, this would use Whisper or other ASR model
        transcribed_text = "Akwaaba, me din de Kofi. Me pɛ sɛ mekasa Twi."
        confidence = 0.95
        
        # Enhance text if requested
        enhanced_text = None
        if request.enhance_text and text_processor:
            result = text_processor.process_text(
                transcribed_text,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=True,
                apply_dialect=True,
                generate_phonemes=False
            )
            enhanced_text = result['processed']
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TranscribeResponse(
            text=transcribed_text,
            enhanced_text=enhanced_text,
            confidence=confidence,
            language=request.language,
            dialect=request.dialect,
            duration=duration,
            timestamps=None,  # Would be populated with actual timestamps
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Synthesize text to speech
    
    Args:
        request: Synthesis request
        
    Returns:
        Audio file response
    """
    try:
        # Process text if requested
        text_to_synthesize = request.text
        if request.enhance_text and text_processor:
            result = text_processor.process_text(
                request.text,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=True,
                apply_dialect=True,
                generate_phonemes=True
            )
            text_to_synthesize = result['processed']
        
        # Perform synthesis (placeholder - actual TTS would go here)
        # In production, this would use Coqui TTS or other TTS model
        sample_rate = 22050
        duration = len(text_to_synthesize) * 0.05  # Rough estimate
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_array = np.sin(2 * np.pi * 440 * t) * 0.3  # Placeholder sine wave
        
        # Apply speed adjustment
        if request.speed != 1.0:
            # Simple speed adjustment by resampling
            new_length = int(len(audio_array) / request.speed)
            audio_array = np.interp(
                np.linspace(0, len(audio_array), new_length),
                np.arange(len(audio_array)),
                audio_array
            )
        
        # Encode audio
        audio_base64 = encode_audio(
            audio_array.reshape(1, -1),
            sample_rate,
            request.output_format
        )
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": sample_rate,
            "duration": duration,
            "text_processed": text_to_synthesize,
            "voice_id": request.voice_id
        }
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voices", response_model=List[VoiceInfo])
async def list_voices():
    """List available voices
    
    Returns:
        List of available voices
    """
    voices = [
        VoiceInfo(
            voice_id="asante_male_1",
            name="Kofi (Asante)",
            language="tw",
            dialect="asante",
            gender="male",
            age_group="adult",
            description="Natural male voice for Asante Twi"
        ),
        VoiceInfo(
            voice_id="asante_female_1",
            name="Ama (Asante)",
            language="tw",
            dialect="asante",
            gender="female",
            age_group="adult",
            description="Natural female voice for Asante Twi"
        ),
        VoiceInfo(
            voice_id="akuapem_male_1",
            name="Kwame (Akuapem)",
            language="tw",
            dialect="akuapem",
            gender="male",
            age_group="adult",
            description="Natural male voice for Akuapem Twi"
        ),
        VoiceInfo(
            voice_id="akuapem_female_1",
            name="Adwoa (Akuapem)",
            language="tw",
            dialect="akuapem",
            gender="female",
            age_group="adult",
            description="Natural female voice for Akuapem Twi"
        ),
        VoiceInfo(
            voice_id="fante_male_1",
            name="Kwesi (Fante)",
            language="tw",
            dialect="fante",
            gender="male",
            age_group="adult",
            description="Natural male voice for Fante"
        ),
        VoiceInfo(
            voice_id="fante_female_1",
            name="Esi (Fante)",
            language="tw",
            dialect="fante",
            gender="female",
            age_group="adult",
            description="Natural female voice for Fante"
        )
    ]
    
    return voices


@app.post("/api/clone-voice")
async def clone_voice(request: VoiceCloneRequest):
    """Clone a voice from reference audio
    
    Args:
        request: Voice cloning request
        
    Returns:
        Synthesized audio in cloned voice
    """
    try:
        # Decode reference audio
        ref_audio, ref_sr = decode_audio(request.reference_audio_base64)
        
        # Extract voice characteristics (placeholder)
        # In production, this would use XTTS or similar
        
        # Synthesize with cloned voice (placeholder)
        sample_rate = 22050
        duration = len(request.text) * 0.06
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_array = np.sin(2 * np.pi * 350 * t) * 0.3  # Different frequency for "cloned" voice
        
        # Encode audio
        audio_base64 = encode_audio(
            audio_array.reshape(1, -1),
            sample_rate,
            "wav"
        )
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": sample_rate,
            "duration": duration,
            "voice_name": request.voice_name,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for streaming
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming ASR/TTS
    
    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "audio_chunk":
                # Process audio chunk for streaming ASR
                audio_base64 = data.get("audio")
                
                # Decode and process (simplified)
                # In production, this would buffer and process chunks
                
                # Send partial transcript
                await websocket.send_json({
                    "type": "partial_transcript",
                    "text": "Me pɛ sɛ...",
                    "is_final": False
                })
                
            elif message_type == "synthesize_stream":
                # Stream TTS audio
                text = data.get("text")
                voice_id = data.get("voice_id", "asante_male_1")
                
                # Generate audio chunks (simplified)
                # In production, this would stream actual TTS output
                
                for i in range(3):  # Send 3 chunks as example
                    await asyncio.sleep(0.1)
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "chunk_id": i,
                        "audio": "base64_audio_chunk_here",
                        "is_final": i == 2
                    })
                    
            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
                
            elif message_type == "close":
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")


@app.get("/api/languages")
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
                    {"code": "fante", "name": "Fante"}
                ]
            }
        ],
        "default_language": "tw",
        "default_dialect": "asante"
    }


@app.post("/api/process-text")
async def process_text(text: str, dialect: str = "asante"):
    """Process text with enhanced Twi processor
    
    Args:
        text: Input text
        dialect: Target dialect
        
    Returns:
        Processed text with various enhancements
    """
    if not text_processor:
        raise HTTPException(status_code=503, detail="Text processor not available")
    
    try:
        result = text_processor.process_text(
            text,
            expand_numbers=True,
            expand_abbreviations=True,
            process_datetime=True,
            apply_dialect=True,
            generate_phonemes=True
        )
        
        return {
            "original": text,
            "processed": result['processed'],
            "phonemes": result.get('phonemes', ''),
            "dialect": dialect,
            "features": {
                "numbers_expanded": result.get('numbers_found', []),
                "dates_processed": result.get('dates_found', []),
                "abbreviations_expanded": result.get('abbreviations_found', [])
            }
        }
        
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Service Directory Endpoints
# ============================================================================

@app.get("/api/directory", response_model=ServiceDirectory, tags=["directory"])
async def get_directory():
    """
    Get the complete service directory.

    Returns all TTS, ASR, LLM, and tool services available in the KasaAI infrastructure.

    Returns:
        Complete service directory grouped by category.
    """
    return get_service_directory()


@app.get("/api/directory/summary", tags=["directory"])
async def get_summary():
    """
    Get a summary of the service directory.

    Returns statistics about available services including counts by category,
    deployment type, available features, and supported languages.

    Returns:
        Summary statistics of the service directory.
    """
    return get_directory_summary()


@app.get("/api/directory/tts", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_tts_services():
    """
    Get all TTS (Text-to-Speech) services.

    Returns a list of all available TTS services including Kokoro, Coqui,
    MeloTTS, OpenVoice, StyleTTS2, F5-TTS, and more.

    Returns:
        List of TTS service endpoints.
    """
    return TTS_SERVICES


@app.get("/api/directory/asr", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_asr_services():
    """
    Get all ASR (Automatic Speech Recognition) services.

    Returns a list of all available ASR services including Whisper ASR
    and Voice Lab specialized ASR for Twi/Akan.

    Returns:
        List of ASR service endpoints.
    """
    return ASR_SERVICES


@app.get("/api/directory/llm", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_llm_services():
    """
    Get all LLM (Large Language Model) services.

    Returns a list of all available LLM services including Ollama,
    Open WebUI, Flowise, and Kyutai Moshi.

    Returns:
        List of LLM service endpoints.
    """
    return LLM_SERVICES


@app.get("/api/directory/tools", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_tool_services():
    """
    Get all AI tools and utility services.

    Returns a list of available tools including Crawl4AI, demo portals,
    and Supabase.

    Returns:
        List of tool service endpoints.
    """
    return TOOLS_SERVICES


@app.get("/api/directory/active", response_model=ServiceDirectory, tags=["directory"])
async def get_active_directory():
    """
    Get only active services.

    Filters the directory to return only services with status 'active'.

    Returns:
        Service directory containing only active services.
    """
    return get_active_services()


@app.get("/api/directory/by-feature", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_by_feature(
    feature: str = Query(..., description="Feature to filter by (e.g., 'voice-cloning', 'streaming')")
):
    """
    Get services by feature.

    Filter services by a specific feature such as 'voice-cloning',
    'streaming', 'multi-language', etc.

    Args:
        feature: Feature name to filter by.

    Returns:
        List of services with the specified feature.
    """
    services = get_services_with_feature(feature)
    if not services:
        raise HTTPException(
            status_code=404,
            detail=f"No services found with feature: {feature}"
        )
    return services


@app.get("/api/directory/by-language", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_by_language(
    language: str = Query(..., description="Language code (e.g., 'en', 'zh', 'tw', 'ja')")
):
    """
    Get services by language.

    Filter services by supported language code.

    Args:
        language: Language code to filter by.

    Returns:
        List of services supporting the specified language.
    """
    services = get_services_by_language(language)
    if not services:
        raise HTTPException(
            status_code=404,
            detail=f"No services found supporting language: {language}"
        )
    return services


@app.get("/api/directory/by-deployment", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_by_deployment(
    deployment: DeploymentType = Query(..., description="Deployment type")
):
    """
    Get services by deployment type.

    Filter services by deployment type: local_docker, runpod_gpu, or external.

    Args:
        deployment: Deployment type to filter by.

    Returns:
        List of services with the specified deployment type.
    """
    return get_services_by_deployment(deployment)


@app.get("/api/directory/category/{category}", response_model=List[ServiceEndpoint], tags=["directory"])
async def get_category_services(category: ServiceCategory):
    """
    Get services by category.

    Get all services in a specific category (tts, asr, llm, or tools).

    Args:
        category: Service category.

    Returns:
        List of services in the specified category.
    """
    return get_services_by_category(category)


if __name__ == "__main__":
    # Run the API
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
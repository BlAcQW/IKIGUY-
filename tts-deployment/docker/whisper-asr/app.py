"""
Whisper ASR API Service for RunPod
Port: 8011
Provides OpenAI-compatible Whisper API powered by Faster Whisper
Includes WebSocket streaming for real-time transcription
Supports Gift Mark Akan Whisper model for Twi (92.9% accuracy)

Response format matches core_backend FasterWhisperTranscriptionResult exactly.
Based on apps/core_backend/backend/services/faster_whisper_service.py
"""

import os
import sys
import logging
import tempfile
import time
import base64
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("whisper-asr")

# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Service configuration"""
    PORT = int(os.getenv("WHISPER_PORT", "8011"))
    HOST = os.getenv("WHISPER_HOST", "0.0.0.0")
    
    # Model configuration
    DEFAULT_MODEL = os.getenv("WHISPER_MODEL", "base")
    DEVICE = os.getenv("WHISPER_DEVICE", "cuda")  # cuda or cpu
    COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")  # float16, int8, int8_float16
    
    # Available models
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    
    # Preload models on startup (comma-separated)
    PRELOAD_MODELS = os.getenv("WHISPER_PRELOAD_MODELS", "base").split(",")
    
    # Akan Whisper model path (Gift Mark - 92.9% accuracy on Twi)
    AKAN_MODEL_PATH = os.getenv("AKAN_MODEL_PATH", "/workspace/models/akan_whisper")


# ============================================================================
# Response Models
# ============================================================================

class WordTimestamp(BaseModel):
    """Word-level timestamp data"""
    word: str
    start: float
    end: float
    probability: float


class TranscriptionSegment(BaseModel):
    """A segment of transcribed text with timestamps"""
    text: str
    start: float
    end: float
    confidence: float
    words: List[WordTimestamp] = []


class TranscriptionResponse(BaseModel):
    """Response format matching core_backend FasterWhisperTranscriptionResult"""
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[TranscriptionSegment] = []
    task: str = "transcribe"  # 'transcribe' or 'translate'
    model: str = ""
    model_size: str = ""


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: List[str]
    gpu_available: bool
    device: str


# ============================================================================
# Model Manager - Matching faster_whisper_service.py
# ============================================================================

class WhisperModelManager:
    """Manages Faster Whisper model instances with Akan model support"""

    def __init__(self):
        self.models: Dict[str, WhisperModel] = {}
        self.device = Config.DEVICE
        self.compute_type = Config.COMPUTE_TYPE
        
        # Ghanaian language codes supported by Whisper (matching faster_whisper_service.py)
        self.ghanaian_languages = {
            "twi": "tw",  # Twi (Akan)
            "tw": "tw",   # Twi alias
            "asante_twi": "tw",  # Asante Twi
            "akuapem_twi": "tw",  # Akuapem Twi
            "ewe": "ee",  # Ewe
            "ga": "ga",    # Ga
            "dagbani": "dag",  # Dagbani
            "hausa": "ha",  # Hausa
            "yoruba": "yo",  # Yoruba
            "igbo": "ig",  # Igbo
            "swahili": "sw",  # Swahili
            "english": "en",  # English
            "en": "en",   # English alias
            "auto": "auto"  # Auto-detect
        }
        
        # Akan Whisper model (Gift Mark) - best for Twi with 92.9% accuracy
        self.akan_model_path = Config.AKAN_MODEL_PATH
        self.akan_model = None
        self.akan_processor = None

        # Check CUDA availability
        try:
            import torch
            self.gpu_available = torch.cuda.is_available()
            if self.gpu_available:
                logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
            else:
                logger.warning("No GPU available, falling back to CPU")
                self.device = "cpu"
                self.compute_type = "int8"
        except ImportError:
            self.gpu_available = False
            self.device = "cpu"
            self.compute_type = "int8"

    def load_model(self, model_size: str) -> WhisperModel:
        """Load a Whisper model"""
        if model_size not in Config.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model size: {model_size}. Available: {Config.AVAILABLE_MODELS}")

        if model_size in self.models:
            logger.info(f"Model '{model_size}' already loaded")
            return self.models[model_size]

        logger.info(f"Loading Whisper model: {model_size} on {self.device} with {self.compute_type}")
        start_time = time.time()

        model = WhisperModel(
            model_size_or_path=model_size,
            device=self.device,
            compute_type=self.compute_type
        )

        self.models[model_size] = model
        load_time = time.time() - start_time
        logger.info(f"Model '{model_size}' loaded in {load_time:.2f}s")

        return model

    def get_model(self, model_size: str) -> WhisperModel:
        """Get or load a model"""
        if model_size not in self.models:
            return self.load_model(model_size)
        return self.models[model_size]

    def preload_models(self, model_sizes: List[str]):
        """Preload multiple models"""
        for model_size in model_sizes:
            model_size = model_size.strip()
            if model_size and model_size in Config.AVAILABLE_MODELS:
                try:
                    self.load_model(model_size)
                except Exception as e:
                    logger.error(f"Failed to preload model '{model_size}': {e}")

    def get_loaded_models(self) -> List[str]:
        """Get list of loaded models"""
        return list(self.models.keys())
    
    async def initialize_akan_model(self):
        """Initialize Gift Mark Akan Whisper model for Twi transcription."""
        try:
            logger.info(f"🔄 Initializing Gift Mark Akan Whisper model...")

            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            import os

            if not os.path.exists(self.akan_model_path):
                logger.warning(f"⚠️ Akan model not found at {self.akan_model_path}")
                return False

            # Load Akan Whisper model
            self.akan_processor = WhisperProcessor.from_pretrained(self.akan_model_path)
            self.akan_model = WhisperForConditionalGeneration.from_pretrained(self.akan_model_path)

            # 🚀 torch.compile optimization (HF best practice: 20-30% speedup)
            import torch
            if torch.cuda.is_available():
                logger.info("🚀 Compiling Akan Whisper model with torch.compile for 20-30% speedup...")
                self.akan_model = torch.compile(
                    self.akan_model,
                    mode="reduce-overhead"  # Optimized for repeated inference
                )

            logger.info(f"✅ Akan Whisper model initialized (92.9% accuracy on Twi)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Akan model: {e}")
            return False
    
    async def transcribe_with_akan_model(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using the Gift Mark Akan Whisper model (92.9% accuracy).
        Optimized for Twi/Akan languages.
        """
        try:
            import torch
            import librosa

            if not self.akan_model or not self.akan_processor:
                logger.info("🔄 Loading Akan model on-demand...")
                success = await self.initialize_akan_model()
                if not success:
                    raise Exception("Failed to load Akan model")

            logger.info(f"🎤 Transcribing with Akan Whisper model: {audio_path}")

            # Load audio with librosa
            audio, sr = librosa.load(audio_path, sr=16000)

            # Limit to 30 seconds
            max_duration = 30
            if len(audio) > max_duration * 16000:
                audio = audio[:max_duration * 16000]

            # Process audio
            inputs = self.akan_processor(audio, sampling_rate=16000, return_tensors="pt")

            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.akan_model.generate(inputs.input_features)

            # Decode
            transcription = self.akan_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            logger.info(f"✅ Akan transcription: '{transcription[:100]}...'")

            # Return in standard format
            duration = len(audio) / 16000.0
            return {
                "text": transcription,
                "language": "tw",  # Twi/Akan
                "confidence": 0.929,  # Model's reported accuracy
                "duration": duration,
                "segments": [{
                    "text": transcription,
                    "start": 0.0,
                    "end": duration,
                    "confidence": 0.929,
                    "words": []
                }],
                "task": "transcribe"
            }

        except Exception as e:
            logger.error(f"❌ Error in Akan transcription: {e}")
            raise
    
    def get_language_code(self, language: str) -> Optional[str]:
        """Get Whisper language code for given language."""
        return self.ghanaian_languages.get(language.lower())


# Global model manager
model_manager = WhisperModelManager()


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - preload models on startup"""
    logger.info("Starting Whisper ASR service on RunPod (Port 8011)...")
    logger.info(f"Device: {model_manager.device}, Compute type: {model_manager.compute_type}")

    # Preload configured models
    if Config.PRELOAD_MODELS:
        logger.info(f"Preloading models: {Config.PRELOAD_MODELS}")
        model_manager.preload_models(Config.PRELOAD_MODELS)
    
    # Try to load Akan model if available
    try:
        await model_manager.initialize_akan_model()
    except Exception as e:
        logger.warning(f"Could not load Akan model: {e}")

    yield

    logger.info("Shutting down Whisper ASR service...")


app = FastAPI(
    title="Whisper ASR API (RunPod)",
    description="OpenAI-compatible Whisper API powered by Faster Whisper",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        models_loaded=model_manager.get_loaded_models(),
        gpu_available=model_manager.gpu_available,
        device=model_manager.device
    )


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)"""
    models = []
    for model_id in Config.AVAILABLE_MODELS:
        models.append({
            "id": f"whisper-{model_id}",
            "object": "model",
            "created": 1677610602,
            "owned_by": "openai",
            "loaded": model_id in model_manager.models
        })
    return {"object": "list", "data": models}


@app.post("/v1/audio/transcriptions", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Query("whisper-base", description="Model to use"),
    language: Optional[str] = Query(None, description="Language code (auto-detect if None)"),
    prompt: Optional[str] = Query(None, description="Optional text to guide the model"),
    response_format: str = Query("json", description="Response format"),
    temperature: float = Query(0.0, description="Temperature for sampling"),
    task: str = Query("transcribe", description="Task: transcribe or translate"),
    word_timestamps: bool = Query(False, description="Include word-level timestamps")
):
    """
    Transcribe audio file (OpenAI-compatible endpoint).
    
    Response format matches core_backend FasterWhisperTranscriptionResult exactly.
    Uses Gift Mark Akan model for Twi/Akan languages (92.9% accuracy).
    """
    try:
        # Extract model size
        model_size = model.replace("whisper-", "").strip()
        
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix if file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_path = tmp_file.name
            content = await file.read()
            tmp_file.write(content)

        try:
            # Use Akan model for Twi/Akan languages (matching faster_whisper_service.py)
            if language and language.lower() in ['twi', 'tw', 'akan']:
                logger.info("🎯 Using Gift Mark Akan model for Twi transcription")
                result = await model_manager.transcribe_with_akan_model(tmp_path)
                
                # Convert to response format
                segments = []
                for seg in result["segments"]:
                    segments.append(TranscriptionSegment(
                        text=seg["text"],
                        start=seg["start"],
                        end=seg["end"],
                        confidence=seg["confidence"],
                        words=seg.get("words", [])
                    ))
                
                return TranscriptionResponse(
                    text=result["text"],
                    language=result["language"],
                    confidence=result["confidence"],
                    duration=result["duration"],
                    segments=segments,
                    task=result["task"],
                    model="akan-whisper",
                    model_size="akan"
                )
            
            # Use Faster Whisper for other languages
            if model_size not in Config.AVAILABLE_MODELS:
                model_size = Config.DEFAULT_MODEL

            # Get model
            whisper_model = model_manager.get_model(model_size)

            # Configure transcription options - matching faster_whisper_service.py
            options = {
                "task": task,
                "language": language if language and language != "auto" else None,
                "word_timestamps": True,  # Always get word timestamps
                "temperature": temperature,
                "vad_filter": True,
                "vad_parameters": {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400
                }
            }
            
            # Map language code if needed
            if language and language != "auto" and language in model_manager.ghanaian_languages:
                options["language"] = model_manager.ghanaian_languages[language]

            if prompt:
                options["initial_prompt"] = prompt

            segments_iter, info = whisper_model.transcribe(tmp_path, **options)

            # Build response - matching faster_whisper_service.py format
            segments = []
            full_text = ""
            total_confidence = 0.0
            segment_count = 0

            for segment in segments_iter:
                segment_text = segment.text.strip()
                full_text += segment_text + " "

                # Build word timestamps
                segment_words = []
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        segment_words.append(WordTimestamp(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            probability=word.probability
                        ))

                # Calculate segment confidence (matching faster_whisper_service.py)
                seg_confidence = segment.avg_logprob if hasattr(segment, 'avg_logprob') else 0.0

                segments.append(TranscriptionSegment(
                    text=segment_text,
                    start=segment.start,
                    end=segment.end,
                    confidence=seg_confidence,
                    words=segment_words
                ))
                total_confidence += seg_confidence
                segment_count += 1

            # Calculate overall confidence
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0

            return TranscriptionResponse(
                text=full_text.strip(),
                language=info.language if hasattr(info, 'language') else (language or "unknown"),
                confidence=avg_confidence,
                duration=info.duration if hasattr(info, 'duration') else 0.0,
                segments=segments,
                task=task,
                model=f"faster-whisper-{model_size}",
                model_size=model_size
            )

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio_file: UploadFile = File(...),
    model: str = Query("base", description="Model size: tiny, base, small, medium, large, large-v2, large-v3"),
    language: Optional[str] = Query(None, description="Language code (auto-detect if None)"),
    task: str = Query("transcribe", description="Task: transcribe or translate"),
    word_timestamps: bool = Query(False, description="Include word-level timestamps"),
    prompt: Optional[str] = Query(None, description="Optional prompt for better transcription")
):
    """
    Transcribe audio file (simplified endpoint).
    
    Response format matches core_backend FasterWhisperTranscriptionResult exactly.
    Uses Gift Mark Akan model for Twi/Akan languages (92.9% accuracy).
    """
    try:
        # Save uploaded file temporarily
        suffix = Path(audio_file.filename).suffix if audio_file.filename else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_path = tmp_file.name
            content = await audio_file.read()
            tmp_file.write(content)

        try:
            # Use Akan model for Twi/Akan languages (matching faster_whisper_service.py)
            if language and language.lower() in ['twi', 'tw', 'akan']:
                logger.info("🎯 Using Gift Mark Akan model for Twi transcription")
                result = await model_manager.transcribe_with_akan_model(tmp_path)
                
                # Convert to response format
                segments = []
                for seg in result["segments"]:
                    segments.append(TranscriptionSegment(
                        text=seg["text"],
                        start=seg["start"],
                        end=seg["end"],
                        confidence=seg["confidence"],
                        words=seg.get("words", [])
                    ))
                
                return TranscriptionResponse(
                    text=result["text"],
                    language=result["language"],
                    confidence=result["confidence"],
                    duration=result["duration"],
                    segments=segments,
                    task=result["task"],
                    model="akan-whisper",
                    model_size="akan"
                )
            
            # Use Faster Whisper for other languages
            if model not in Config.AVAILABLE_MODELS:
                model = Config.DEFAULT_MODEL

            # Get model
            whisper_model = model_manager.get_model(model)

            # Configure transcription options - matching faster_whisper_service.py
            options = {
                "task": task,
                "language": language if language and language != "auto" else None,
                "word_timestamps": True,  # Always get word timestamps
                "vad_filter": True,
                "vad_parameters": {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400
                }
            }
            
            # Map language code if needed
            if language and language != "auto" and language in model_manager.ghanaian_languages:
                options["language"] = model_manager.ghanaian_languages[language]
            
            if prompt:
                options["initial_prompt"] = prompt

            segments_iter, info = whisper_model.transcribe(tmp_path, **options)

            # Build response - matching faster_whisper_service.py format
            segments = []
            full_text = ""
            total_confidence = 0.0
            segment_count = 0

            for segment in segments_iter:
                segment_text = segment.text.strip()
                full_text += segment_text + " "

                # Build word timestamps
                segment_words = []
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        segment_words.append(WordTimestamp(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            probability=word.probability
                        ))

                # Calculate segment confidence (matching faster_whisper_service.py)
                seg_confidence = segment.avg_logprob if hasattr(segment, 'avg_logprob') else 0.0

                segments.append(TranscriptionSegment(
                    text=segment_text,
                    start=segment.start,
                    end=segment.end,
                    confidence=seg_confidence,
                    words=segment_words
                ))
                total_confidence += seg_confidence
                segment_count += 1

            # Calculate overall confidence
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0

            return TranscriptionResponse(
                text=full_text.strip(),
                language=info.language if hasattr(info, 'language') else (language or "unknown"),
                confidence=avg_confidence,
                duration=info.duration if hasattr(info, 'duration') else 0.0,
                segments=segments,
                task=task,
                model=f"faster-whisper-{model}",
                model_size=model
            )

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Streaming Endpoint
# ============================================================================

@app.websocket("/ws/stream")
async def asr_stream_websocket(
    websocket: WebSocket,
    model: str = Query("medium", description="Model size"),
    language: Optional[str] = Query(None, description="Language code"),
    task: str = Query("transcribe", description="Task: transcribe or translate")
):
    """
    Real-time ASR streaming via WebSocket.
    
    Protocol (matching apps/shared/routes/asr_routes.py):
    - Client connects with model and optional language
    - Client sends: {"type": "audio", "data": "<base64>"}
    - Server responds: {"type": "interim", "text": "...", "is_final": false}
    - Client sends: {"type": "end"}
    - Server responds: {"type": "final", "text": "...", "language": "...", "duration": 0.0}
    """
    await websocket.accept()
    
    try:
        logger.info(f"WebSocket ASR streaming started: model={model}, lang={language}, task={task}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "model": model,
            "language": language or "auto",
            "task": task,
            "message": "Streaming transcription ready. Send audio chunks."
        })
        
        audio_chunks = []
        chunk_count = 0
        
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected by client")
                break
            
            msg_type = data.get("type")
            
            if msg_type == "audio":
                # Receive audio chunk (base64)
                audio_base64 = data.get("data")
                if not audio_base64:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio data provided"
                    })
                    continue
                
                audio_chunks.append(audio_base64)
                chunk_count += 1
                
                # Send interim acknowledgment
                await websocket.send_json({
                    "type": "interim",
                    "message": f"Received chunk {chunk_count}",
                    "chunks_received": chunk_count,
                    "is_final": False
                })
            
            elif msg_type == "end":
                # Process all accumulated audio
                logger.info(f"Processing {chunk_count} audio chunks for final transcription")
                
                if not audio_chunks:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio chunks received"
                    })
                    break
                
                try:
                    # Combine all chunks and decode
                    combined_base64 = "".join(audio_chunks)
                    audio_bytes = base64.b64decode(combined_base64)
                    
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_path = tmp_file.name
                        tmp_file.write(audio_bytes)
                    
                    try:
                        # Use Akan model for Twi/Akan languages
                        if language and language.lower() in ['twi', 'tw', 'akan']:
                            logger.info("🎯 Using Gift Mark Akan model for Twi transcription")
                            result = await model_manager.transcribe_with_akan_model(tmp_path)
                            
                            # Send final transcript
                            await websocket.send_json({
                                "type": "final",
                                "text": result["text"],
                                "language": result["language"],
                                "confidence": result["confidence"],
                                "duration": result["duration"],
                                "segments": result["segments"],
                                "is_final": True
                            })
                            
                            # Reset for next recording
                            audio_chunks = []
                            chunk_count = 0
                            continue
                        
                        # Get model
                        if model not in Config.AVAILABLE_MODELS:
                            model = Config.DEFAULT_MODEL
                        whisper_model = model_manager.get_model(model)
                        
                        # Configure transcription options - matching faster_whisper_service.py
                        options = {
                            "task": task,
                            "language": language if language and language != "auto" else None,
                            "word_timestamps": True,
                            "vad_filter": True,
                            "vad_parameters": {
                                "min_silence_duration_ms": 500,
                                "speech_pad_ms": 400
                            }
                        }
                        
                        # Map language code if needed
                        if language and language != "auto" and language in model_manager.ghanaian_languages:
                            options["language"] = model_manager.ghanaian_languages[language]
                        
                        # Transcribe
                        segments_iter, info = whisper_model.transcribe(tmp_path, **options)
                        
                        # Build response - matching faster_whisper_service.py format
                        segments_list = []
                        full_text = ""
                        total_confidence = 0.0
                        segment_count = 0
                        
                        for segment in segments_iter:
                            segment_text = segment.text.strip()
                            full_text += segment_text + " "
                            
                            seg_confidence = segment.avg_logprob if hasattr(segment, 'avg_logprob') else 0.0
                            segments_list.append({
                                "text": segment_text,
                                "start": segment.start,
                                "end": segment.end,
                                "confidence": seg_confidence
                            })
                            total_confidence += seg_confidence
                            segment_count += 1
                        
                        avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
                        
                        # Send final transcript
                        await websocket.send_json({
                            "type": "final",
                            "text": full_text.strip(),
                            "language": info.language if hasattr(info, 'language') else (language or "unknown"),
                            "confidence": avg_confidence,
                            "duration": info.duration if hasattr(info, 'duration') else 0.0,
                            "segments": segments_list,
                            "is_final": True
                        })
                        
                        # Reset for next recording
                        audio_chunks = []
                        chunk_count = 0
                        
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                
                except Exception as e:
                    logger.error(f"Transcription error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })
            
            elif msg_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "close":
                break
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        workers=1,  # Single worker for GPU memory management
        log_level="info"
    )


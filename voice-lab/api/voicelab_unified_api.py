#!/usr/bin/env python3
"""
Voice Lab Unified API - Single API Gateway for All TTS/ASR/LLM Providers

This consolidated API provides a single entry point for all voice AI services,
routing requests to the appropriate backend providers (RunPod GPU or Local Docker).

Deployment: Hetzner Server - Acts as reverse proxy to both local Docker
containers and RunPod GPU services.

Local providers (Kokoro, MeloTTS, Coqui, Chatterbox, OpenVoice) run on this server.
GPU providers (F5-TTS, StyleTTS2, GPT-SoVITS, etc.) are proxied to RunPod.

Author: AI Labs Africa
Created: November 29, 2025
Updated: November 29, 2025 - Moved to Hetzner deployment
"""

import os
import logging
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Provider Configuration
# ============================================================================

class TTSProvider(str, Enum):
    """Available TTS providers."""
    F5TTS = "f5tts"
    STYLETTS2 = "styletts2"
    FISH_SPEECH = "fish_speech"
    ZONOS = "zonos"
    GPT_SOVITS = "gpt_sovits"
    TTS_WEBUI = "tts_webui"
    KOKORO = "kokoro"
    MELOTTS = "melotts"
    OPENVOICE = "openvoice"
    COQUI = "coqui"
    CHATTERBOX = "chatterbox"
    WHISPER = "whisper"  # ASR provider
    MOSHI = "moshi"  # Real-time conversational AI


class ProviderConfig(BaseModel):
    """Provider configuration."""
    name: str
    base_url: str
    health_endpoint: str = "/"
    synthesize_endpoint: str = "/synthesize"
    clone_endpoint: Optional[str] = None
    is_local: bool = False  # True for local Docker, False for RunPod
    timeout: int = 120
    features: List[str] = []


# RunPod base URL for proxy
RUNPOD_PROXY_BASE = "https://jzfmzviw26huka-{port}.proxy.runpod.net"

# Provider backends - RunPod GPU providers accessed via RunPod proxy URLs
# These are accessed from Hetzner, so we use the public RunPod proxy URLs
RUNPOD_PROVIDERS: Dict[TTSProvider, ProviderConfig] = {
    TTSProvider.F5TTS: ProviderConfig(
        name="F5-TTS",
        base_url=RUNPOD_PROXY_BASE.format(port="8010"),  # F5-TTS Gradio UI on 8010
        health_endpoint="/",
        synthesize_endpoint="/api/predict",
        clone_endpoint="/api/predict",
        features=["voice-cloning", "multi-language", "en-zh-ja-ko"]
    ),
    TTSProvider.STYLETTS2: ProviderConfig(
        name="StyleTTS2",
        base_url=RUNPOD_PROXY_BASE.format(port="8013"),  # StyleTTS2 API on 8013
        health_endpoint="/",
        synthesize_endpoint="/synthesize",
        clone_endpoint="/clone",
        features=["voice-cloning", "style-transfer", "emotion-control"]
    ),
    TTSProvider.FISH_SPEECH: ProviderConfig(
        name="Fish Speech",
        base_url=RUNPOD_PROXY_BASE.format(port="8015"),  # Fish Speech on 8015
        health_endpoint="/",
        synthesize_endpoint="/v1/tts",
        clone_endpoint="/v1/tts",
        features=["zero-shot-cloning", "fast-inference", "8-languages"]
    ),
    TTSProvider.ZONOS: ProviderConfig(
        name="Zonos TTS",
        base_url=RUNPOD_PROXY_BASE.format(port="8014"),  # Zonos on 8014
        health_endpoint="/",
        synthesize_endpoint="/synthesize",
        features=["emotion-sliders", "prosody-control", "experimental"]
    ),
    TTSProvider.GPT_SOVITS: ProviderConfig(
        name="GPT-SoVITS",
        base_url=RUNPOD_PROXY_BASE.format(port="8016"),  # GPT-SoVITS Gradio on 8016
        health_endpoint="/",
        synthesize_endpoint="/api/predict",
        clone_endpoint="/api/predict",
        features=["zero-shot-cloning", "gpt-based", "high-quality"]
    ),
    TTSProvider.TTS_WEBUI: ProviderConfig(
        name="TTS-WebUI",
        base_url=RUNPOD_PROXY_BASE.format(port="8017"),  # TTS-WebUI on 8017
        health_endpoint="/",
        synthesize_endpoint="/api/v1/audio/speech",
        features=["multi-model", "openai-compatible", "20+-models", "rvc"]
    ),
    TTSProvider.WHISPER: ProviderConfig(
        name="Whisper ASR",
        base_url=RUNPOD_PROXY_BASE.format(port="8011"),  # Whisper ASR on 8011
        health_endpoint="/",
        synthesize_endpoint="/transcribe",
        features=["multilingual", "streaming", "timestamps", "100+-languages"]
    ),
    TTSProvider.MOSHI: ProviderConfig(
        name="Kyutai Moshi",
        base_url=RUNPOD_PROXY_BASE.format(port="8018"),  # Moshi on 8018 (proxied from 8008)
        health_endpoint="/",
        synthesize_endpoint="/ws/conversation",  # WebSocket endpoint
        features=["real-time-conversation", "full-duplex", "low-latency", "websocket"]
    ),
}

# Local Docker providers (Hetzner) - These run on this server
# Verified from: sudo docker ps --format "{{.Names}}: {{.Ports}}"
LOCAL_PROVIDERS: Dict[TTSProvider, ProviderConfig] = {
    TTSProvider.KOKORO: ProviderConfig(
        name="Kokoro TTS",
        base_url="http://127.0.0.1:8010",  # kokoro container on port 8010
        health_endpoint="/health",
        synthesize_endpoint="/synthesize",
        is_local=True,
        timeout=60,
        features=["multi-speaker", "speed-control", "11-voices"]
    ),
    TTSProvider.MELOTTS: ProviderConfig(
        name="MeloTTS",
        base_url="http://127.0.0.1:8001",  # melotts container on port 8001
        health_endpoint="/health",
        synthesize_endpoint="/synthesize",
        is_local=True,
        timeout=60,
        features=["multi-language", "multi-speaker", "fast"]
    ),
    TTSProvider.OPENVOICE: ProviderConfig(
        name="OpenVoice",
        base_url="http://127.0.0.1:8003",  # openvoice container on port 8003
        health_endpoint="/",
        synthesize_endpoint="/synthesize",
        clone_endpoint="/clone",
        is_local=True,
        timeout=90,
        features=["voice-cloning", "emotion-control"]
    ),
    TTSProvider.COQUI: ProviderConfig(
        name="Coqui XTTS",
        base_url="http://127.0.0.1:8005",  # coqui container on port 8005
        health_endpoint="/health",
        synthesize_endpoint="/synthesize",
        clone_endpoint="/clone",
        is_local=True,
        timeout=120,
        features=["voice-cloning", "17-languages", "ssml"]
    ),
    TTSProvider.CHATTERBOX: ProviderConfig(
        name="Chatterbox",
        base_url="http://127.0.0.1:8004",  # chatterbox container on port 8004
        health_endpoint="/",
        synthesize_endpoint="/gradio_api/call/generate_tts_audio",
        is_local=True,
        timeout=120,
        features=["voice-cloning", "expressive-speech"]
    ),
}

# Combine all providers
ALL_PROVIDERS = {**RUNPOD_PROVIDERS, **LOCAL_PROVIDERS}


# ============================================================================
# Request/Response Models
# ============================================================================

class SynthesizeRequest(BaseModel):
    """TTS synthesis request."""
    text: str = Field(..., description="Text to synthesize")
    provider: TTSProvider = Field(default=TTSProvider.KOKORO, description="TTS provider to use")
    voice: Optional[str] = Field(None, description="Voice ID or name")
    language: Optional[str] = Field("en", description="Language code")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(0.0, ge=-5.0, le=5.0, description="Pitch adjustment")
    output_format: str = Field("wav", description="Output format (wav, mp3)")


class VoiceCloneRequest(BaseModel):
    """Voice cloning request."""
    text: str = Field(..., description="Text to synthesize")
    provider: TTSProvider = Field(default=TTSProvider.F5TTS, description="Provider for cloning")
    reference_audio_url: Optional[str] = Field(None, description="URL to reference audio")
    voice_name: Optional[str] = Field("custom", description="Name for cloned voice")


class TranscribeRequest(BaseModel):
    """ASR transcription request."""
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    language: Optional[str] = Field(None, description="Language hint")
    return_timestamps: bool = Field(False, description="Include word timestamps")


class ProviderStatus(BaseModel):
    """Provider health status."""
    provider: str
    name: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: Optional[float] = None
    features: List[str] = []
    is_local: bool = False
    error: Optional[str] = None


class DirectoryEntry(BaseModel):
    """Service directory entry."""
    id: str
    name: str
    url: str
    api_url: Optional[str] = None
    category: str  # tts, asr, llm
    deployment: str  # runpod_gpu, local_docker
    status: str = "active"
    features: List[str] = []
    languages: List[str] = []


# ============================================================================
# HTTP Client
# ============================================================================

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global http_client

    logger.info("=" * 80)
    logger.info("Starting Voice Lab Unified API")
    logger.info("=" * 80)

    # Initialize HTTP client with SSL support for RunPod connections
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(120.0, connect=30.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        verify=True,  # Verify SSL for RunPod connections
        follow_redirects=True
    )

    # Check provider health
    logger.info("Checking provider health...")
    healthy_count = 0
    for provider_id, config in ALL_PROVIDERS.items():
        try:
            response = await http_client.get(
                f"{config.base_url}{config.health_endpoint}",
                timeout=5.0
            )
            if response.status_code == 200:
                healthy_count += 1
                logger.info(f"  ✓ {config.name} is healthy")
            else:
                logger.warning(f"  ✗ {config.name} returned {response.status_code}")
        except Exception as e:
            logger.warning(f"  ✗ {config.name} is unreachable: {e}")

    logger.info(f"Providers ready: {healthy_count}/{len(ALL_PROVIDERS)}")
    logger.info("=" * 80)
    logger.info("Voice Lab Unified API ready!")
    logger.info("=" * 80)

    yield

    # Cleanup
    logger.info("Shutting down Voice Lab Unified API")
    if http_client:
        await http_client.aclose()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Voice Lab Unified API",
    description=(
        "Unified gateway for all TTS, ASR, and LLM services. "
        "Routes requests to RunPod GPU and Local Docker providers."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Core Endpoints
# ============================================================================

@app.get("/", tags=["info"])
async def root():
    """API root - service information."""
    return {
        "service": "Voice Lab Unified API",
        "version": "1.0.0",
        "description": "Unified gateway for TTS, ASR, and LLM services",
        "endpoints": {
            "directory": "/api/directory",
            "health": "/api/health",
            "synthesize": "/api/tts/synthesize",
            "transcribe": "/api/asr/transcribe",
            "providers": "/api/providers",
        },
        "documentation": "/docs"
    }


@app.get("/health", tags=["monitoring"])
@app.get("/api/health", tags=["monitoring"])
async def health_check():
    """Health check with provider status."""
    provider_statuses = []
    healthy_count = 0

    for provider_id, config in ALL_PROVIDERS.items():
        status = ProviderStatus(
            provider=provider_id.value,
            name=config.name,
            status="unknown",
            features=config.features,
            is_local=config.is_local
        )

        try:
            start = datetime.now()
            response = await http_client.get(
                f"{config.base_url}{config.health_endpoint}",
                timeout=5.0
            )
            elapsed = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                status.status = "healthy"
                status.response_time_ms = round(elapsed, 2)
                healthy_count += 1
            else:
                status.status = "unhealthy"
                status.error = f"HTTP {response.status_code}"
        except Exception as e:
            status.status = "unhealthy"
            status.error = str(e)

        provider_statuses.append(status)

    overall_status = "healthy" if healthy_count > len(ALL_PROVIDERS) // 2 else "degraded"
    if healthy_count == 0:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "healthy_providers": healthy_count,
        "total_providers": len(ALL_PROVIDERS),
        "timestamp": datetime.now().isoformat(),
        "providers": provider_statuses
    }


# ============================================================================
# Directory Endpoints
# ============================================================================

@app.get("/api/directory", tags=["directory"])
async def get_directory():
    """Get complete service directory."""
    entries = []

    for provider_id, config in ALL_PROVIDERS.items():
        entry = DirectoryEntry(
            id=provider_id.value,
            name=config.name,
            url=f"/api/tts/{provider_id.value}",
            api_url=f"/api/tts/{provider_id.value}/synthesize",
            category="tts" if provider_id != TTSProvider.WHISPER else "asr",
            deployment="local_docker" if config.is_local else "runpod_gpu",
            features=config.features
        )
        entries.append(entry)

    return {
        "total": len(entries),
        "tts_providers": [e for e in entries if e.category == "tts"],
        "asr_providers": [e for e in entries if e.category == "asr"],
    }


@app.get("/api/providers", tags=["directory"])
async def list_providers():
    """List all available providers."""
    providers = []
    for provider_id, config in ALL_PROVIDERS.items():
        providers.append({
            "id": provider_id.value,
            "name": config.name,
            "category": "tts" if provider_id != TTSProvider.WHISPER else "asr",
            "deployment": "local" if config.is_local else "runpod",
            "features": config.features,
            "endpoints": {
                "synthesize": f"/api/tts/{provider_id.value}/synthesize",
                "health": f"/api/tts/{provider_id.value}/health"
            }
        })
    return {"providers": providers}


# ============================================================================
# TTS Endpoints
# ============================================================================

@app.post("/api/tts/synthesize", tags=["tts"])
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech using the specified provider.

    Routes the request to the appropriate backend (RunPod GPU or Local Docker).
    """
    provider_id = request.provider
    if provider_id not in ALL_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_id}")

    config = ALL_PROVIDERS[provider_id]

    try:
        # Build provider-specific request
        if provider_id == TTSProvider.KOKORO:
            payload = {
                "text": request.text,
                "voice": request.voice or "af_sarah",
                "speed": request.speed
            }
        elif provider_id == TTSProvider.F5TTS:
            payload = {
                "text": request.text,
                "ref_audio": request.voice,  # Reference audio path
                "speed": request.speed
            }
        elif provider_id == TTSProvider.STYLETTS2:
            # Gradio API format
            payload = {
                "data": [request.text, request.voice or "default"]
            }
        elif provider_id == TTSProvider.FISH_SPEECH:
            payload = {
                "text": request.text,
                "reference_audio": request.voice,
                "speed": request.speed
            }
        else:
            # Generic payload
            payload = {
                "text": request.text,
                "voice": request.voice,
                "speed": request.speed,
                "language": request.language
            }

        # Make request to provider
        response = await http_client.post(
            f"{config.base_url}{config.synthesize_endpoint}",
            json=payload,
            timeout=config.timeout
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Provider error: {response.text}"
            )

        # Return audio response
        content_type = response.headers.get("content-type", "audio/wav")
        return Response(
            content=response.content,
            media_type=content_type
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Provider {config.name} timeout")
    except Exception as e:
        logger.error(f"Synthesis error with {config.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tts/{provider}/health", tags=["tts"])
async def provider_health(provider: str):
    """Check health of a specific provider."""
    try:
        provider_id = TTSProvider(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    config = ALL_PROVIDERS[provider_id]

    try:
        start = datetime.now()
        response = await http_client.get(
            f"{config.base_url}{config.health_endpoint}",
            timeout=10.0
        )
        elapsed = (datetime.now() - start).total_seconds() * 1000

        return {
            "provider": provider,
            "name": config.name,
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "response_time_ms": round(elapsed, 2),
            "features": config.features
        }
    except Exception as e:
        return {
            "provider": provider,
            "name": config.name,
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/api/tts/{provider}/synthesize", tags=["tts"])
async def synthesize_with_provider(
    provider: str,
    text: str = Form(...),
    voice: Optional[str] = Form(None),
    speed: float = Form(1.0),
    language: str = Form("en"),
    reference_audio: Optional[UploadFile] = File(None)
):
    """
    Synthesize speech with a specific provider.

    Supports multipart form data for reference audio upload.
    """
    try:
        provider_id = TTSProvider(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    config = ALL_PROVIDERS[provider_id]

    try:
        # Handle file upload for voice cloning
        files = {}
        data = {
            "text": text,
            "voice": voice,
            "speed": speed,
            "language": language
        }

        if reference_audio:
            files["reference_audio"] = (
                reference_audio.filename,
                await reference_audio.read(),
                reference_audio.content_type
            )

        if files:
            response = await http_client.post(
                f"{config.base_url}{config.synthesize_endpoint}",
                data=data,
                files=files,
                timeout=config.timeout
            )
        else:
            response = await http_client.post(
                f"{config.base_url}{config.synthesize_endpoint}",
                json=data,
                timeout=config.timeout
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Provider error: {response.text}"
            )

        return Response(
            content=response.content,
            media_type=response.headers.get("content-type", "audio/wav")
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Provider {config.name} timeout")
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ASR Endpoints
# ============================================================================

@app.post("/api/asr/transcribe", tags=["asr"])
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    return_timestamps: bool = Form(False)
):
    """
    Transcribe audio using Whisper ASR.
    """
    config = ALL_PROVIDERS.get(TTSProvider.WHISPER)
    if not config:
        raise HTTPException(status_code=503, detail="Whisper ASR not available")

    try:
        files = {
            "audio": (audio.filename, await audio.read(), audio.content_type)
        }
        data = {
            "language": language,
            "return_timestamps": str(return_timestamps).lower()
        }

        response = await http_client.post(
            f"{config.base_url}{config.synthesize_endpoint}",
            data=data,
            files=files,
            timeout=config.timeout
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ASR error: {response.text}"
            )

        return response.json()

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Proxy Endpoints - Pass-through to providers
# ============================================================================

@app.api_route(
    "/api/tts/{provider}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["proxy"]
)
async def proxy_to_provider(provider: str, path: str, request: Request):
    """
    Proxy any request to a specific provider.

    This allows direct access to provider-specific endpoints.
    """
    try:
        provider_id = TTSProvider(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    config = ALL_PROVIDERS[provider_id]
    target_url = f"{config.base_url}/{path}"

    try:
        # Forward request
        method = request.method
        headers = dict(request.headers)
        headers.pop("host", None)

        if method == "GET":
            response = await http_client.get(
                target_url,
                params=request.query_params,
                headers=headers,
                timeout=config.timeout
            )
        else:
            body = await request.body()
            response = await http_client.request(
                method,
                target_url,
                content=body,
                headers=headers,
                timeout=config.timeout
            )

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Default port 30038 for Hetzner deployment (following kasaai service port pattern)
    # 30037 is used by core_backend
    port = int(os.getenv("PORT", "30038"))
    uvicorn.run(
        "voicelab_unified_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )

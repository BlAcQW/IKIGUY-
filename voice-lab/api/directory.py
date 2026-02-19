"""
Voice Lab Directory - Comprehensive API Directory for TTS, ASR, and LLM services.

This module provides a centralized directory of all voice AI services available
in the KasaAI infrastructure, grouped by category (TTS, ASR, LLM).

Author: AI Labs Africa
Created: November 29, 2025
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class ServiceCategory(str, Enum):
    """Service category enumeration."""
    TTS = "tts"
    ASR = "asr"
    LLM = "llm"
    TOOLS = "tools"


class ServiceStatus(str, Enum):
    """Service deployment status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class DeploymentType(str, Enum):
    """Service deployment type."""
    LOCAL_DOCKER = "local_docker"
    RUNPOD_GPU = "runpod_gpu"
    EXTERNAL = "external"


class ServiceEndpoint(BaseModel):
    """Individual service endpoint details."""
    name: str = Field(..., description="Display name of the service")
    url: str = Field(..., description="Public URL for the service")
    api_url: Optional[str] = Field(None, description="API endpoint URL (if different from UI)")
    description: str = Field(..., description="Brief description of the service")
    deployment: DeploymentType = Field(..., description="Where the service is deployed")
    port: Optional[int] = Field(None, description="Internal port number")
    status: ServiceStatus = Field(default=ServiceStatus.ACTIVE, description="Current status")
    features: List[str] = Field(default_factory=list, description="Key features")
    languages: List[str] = Field(default_factory=list, description="Supported languages")
    documentation_url: Optional[str] = Field(None, description="Link to documentation")
    health_endpoint: Optional[str] = Field(None, description="Health check endpoint")
    websocket_url: Optional[str] = Field(None, description="WebSocket endpoint if supported")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ServiceDirectory(BaseModel):
    """Complete service directory grouped by category."""
    tts: List[ServiceEndpoint] = Field(default_factory=list, description="TTS services")
    asr: List[ServiceEndpoint] = Field(default_factory=list, description="ASR services")
    llm: List[ServiceEndpoint] = Field(default_factory=list, description="LLM services")
    tools: List[ServiceEndpoint] = Field(default_factory=list, description="AI tools and utilities")


# TTS Services Directory
TTS_SERVICES: List[ServiceEndpoint] = [
    # Local Docker Services
    ServiceEndpoint(
        name="Kokoro TTS",
        url="https://kokoro.ailabsafrica.com",
        api_url="https://kokoro.ailabsafrica.com/synthesize",
        description="Fast, high-quality TTS with natural prosody. Based on Kokoro-82M model with 11 voice packs.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8010,
        status=ServiceStatus.ACTIVE,
        features=["multi-speaker", "speed-control", "pitch-control", "natural-prosody"],
        languages=["en"],
        health_endpoint="/health",
        metadata={
            "speakers": ["af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky",
                        "am_adam", "am_michael", "bf_emma", "bf_isabella", "bm_george", "bm_lewis"]
        }
    ),
    ServiceEndpoint(
        name="Kokoro TTS UI",
        url="https://kokoro-ui.ailabsafrica.com",
        description="Web interface for Kokoro TTS with voice selection and audio preview.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8021,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "voice-preview", "batch-synthesis"],
        languages=["en"]
    ),
    ServiceEndpoint(
        name="Coqui XTTS v2",
        url="https://coqui.ailabsafrica.com",
        api_url="https://coqui.ailabsafrica.com/synthesize",
        description="Multilingual TTS with voice cloning. Supports 17 languages.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8005,
        status=ServiceStatus.ACTIVE,
        features=["voice-cloning", "multi-language", "ssml-support", "speed-control"],
        languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "hu", "ko", "ja", "hi"],
        health_endpoint="/health"
    ),
    ServiceEndpoint(
        name="Coqui TTS UI",
        url="https://coqui-ui.ailabsafrica.com",
        description="Web interface for Coqui XTTS with voice cloning capabilities.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8015,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "voice-cloning", "reference-audio"],
        languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "hu", "ko", "ja", "hi"]
    ),
    ServiceEndpoint(
        name="MeloTTS",
        url="https://melotts.ailabsafrica.com",
        api_url="https://melotts.ailabsafrica.com/synthesize",
        description="Fast multilingual synthesis with multi-speaker support.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8001,
        status=ServiceStatus.ACTIVE,
        features=["multi-language", "multi-speaker", "speed-control", "ssml-support"],
        languages=["EN", "ES", "FR", "ZH", "JP", "KR"],
        health_endpoint="/health",
        metadata={
            "speakers": ["EN-US", "EN-BR", "EN-INDIA", "EN-AU", "EN-Default"]
        }
    ),
    ServiceEndpoint(
        name="MeloTTS UI",
        url="https://melotts-ui.ailabsafrica.com",
        description="Web interface for MeloTTS with speaker selection.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8011,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "speaker-selection", "language-selection"],
        languages=["EN", "ES", "FR", "ZH", "JP", "KR"]
    ),
    ServiceEndpoint(
        name="OpenVoice",
        url="https://openvoice.ailabsafrica.com",
        api_url="https://openvoice.ailabsafrica.com/synthesize",
        description="Advanced voice cloning with emotion and style control.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8003,
        status=ServiceStatus.ACTIVE,
        features=["voice-cloning", "emotion-control", "style-transfer", "speed-control"],
        languages=["EN", "ZH"],
        health_endpoint="/"
    ),
    ServiceEndpoint(
        name="OpenVoice UI",
        url="https://openvoice-ui.ailabsafrica.com",
        description="Web interface for OpenVoice with emotion sliders.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8013,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "emotion-control", "voice-cloning"],
        languages=["EN", "ZH"]
    ),
    ServiceEndpoint(
        name="Chatterbox",
        url="https://chatterbox.ailabsafrica.com",
        api_url="https://chatterbox.ailabsafrica.com/gradio_api/call/generate_tts_audio",
        description="Expressive TTS with reference audio support for voice cloning.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8004,
        status=ServiceStatus.ACTIVE,
        features=["voice-cloning", "reference-audio", "expressive-speech"],
        languages=["en"],
        health_endpoint="/",
        metadata={"platform": "gradio"}
    ),

    # RunPod GPU Services
    ServiceEndpoint(
        name="F5-TTS",
        url="https://f5tts.ailabsafrica.com",
        api_url="https://f5tts.ailabsafrica.com/synthesize",
        description="Flow-matching based TTS with voice cloning. High-quality, multilingual.",
        deployment=DeploymentType.RUNPOD_GPU,
        port=8012,
        status=ServiceStatus.ACTIVE,
        features=["voice-cloning", "multi-language", "streaming", "flow-matching"],
        languages=["en", "zh", "ja", "ko"],
        health_endpoint="/health"
    ),
    ServiceEndpoint(
        name="F5-TTS UI",
        url="https://f5tts-ui.ailabsafrica.com",
        description="Web interface for F5-TTS with Gradio UI.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "voice-cloning", "reference-audio"],
        languages=["en", "zh", "ja", "ko"]
    ),
    ServiceEndpoint(
        name="StyleTTS2",
        url="https://styletts.ailabsafrica.com",
        api_url="https://styletts.ailabsafrica.com/gradio_api/call/basic_tts",
        description="High-quality expressive TTS with style transfer. Natural prosody and emotion.",
        deployment=DeploymentType.RUNPOD_GPU,
        port=8013,
        status=ServiceStatus.ACTIVE,
        features=["voice-cloning", "style-transfer", "emotion-control", "expressive"],
        languages=["en"],
        health_endpoint="/",
        metadata={"platform": "gradio"}
    ),
    ServiceEndpoint(
        name="StyleTTS2 UI",
        url="https://styletts-ui.ailabsafrica.com",
        description="Web interface for StyleTTS2 with style controls.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "style-selection", "emotion-sliders"],
        languages=["en"]
    ),
    ServiceEndpoint(
        name="Fish Speech",
        url="https://fishspeech.ailabsafrica.com",
        api_url="https://fishspeech.ailabsafrica.com/synthesize",
        description="Zero-shot voice cloning with minimal reference audio. Fast inference.",
        deployment=DeploymentType.RUNPOD_GPU,
        port=8015,
        status=ServiceStatus.ACTIVE,
        features=["zero-shot-cloning", "few-shot-cloning", "fast-inference", "streaming"],
        languages=["en", "zh", "ja", "ko", "es", "fr", "de", "ru"],
        health_endpoint="/"
    ),
    ServiceEndpoint(
        name="Zonos TTS",
        url="https://zonos.ailabsafrica.com",
        description="Experimental TTS with emotion control sliders. Highly customizable.",
        deployment=DeploymentType.RUNPOD_GPU,
        port=8014,
        status=ServiceStatus.ACTIVE,
        features=["emotion-sliders", "prosody-control", "expressiveness"],
        languages=["en"],
        health_endpoint="/",
        metadata={"experimental": True}
    ),
    ServiceEndpoint(
        name="GPT-SoVITS",
        url="https://gptsovits.ailabsafrica.com",
        api_url="https://gptsovits.ailabsafrica.com/synthesize",
        description="GPT-based zero-shot voice cloning. High quality with minimal reference.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["zero-shot-cloning", "gpt-based", "high-quality"],
        languages=["en", "zh", "ja", "ko"],
        health_endpoint="/"
    ),
    ServiceEndpoint(
        name="GPT-SoVITS UI",
        url="https://gptsovits-ui.ailabsafrica.com",
        description="Web interface for GPT-SoVITS with reference audio upload.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["web-ui", "reference-audio", "voice-cloning"],
        languages=["en", "zh", "ja", "ko"]
    ),
    ServiceEndpoint(
        name="TTS-WebUI",
        url="https://tts-webui.ailabsafrica.com",
        api_url="https://tts-webui.ailabsafrica.com/api/v1/audio/speech",
        description="Comprehensive TTS platform with 20+ models. OpenAI-compatible API.",
        deployment=DeploymentType.RUNPOD_GPU,
        port=8016,
        status=ServiceStatus.ACTIVE,
        features=["multi-model", "openai-compatible", "voice-cloning", "rvc", "streaming"],
        languages=["en", "es", "fr", "de", "zh", "ja", "ko", "pt", "ru"],
        health_endpoint="/",
        metadata={
            "models": ["styletts2", "rvc", "bark", "tortoise", "melotts", "mms", "f5-tts",
                      "xtts_v2", "openvoice", "kokoro", "parler-tts", "whisper", "musicgen",
                      "stable-audio", "demucs", "gpt-sovits", "chatterbox", "mahaTTS", "vall-e-x"],
            "openai_compatible": True
        }
    ),
    ServiceEndpoint(
        name="TTS Lab",
        url="https://ttslab.ailabsafrica.com",
        description="Unified TTS testing and comparison interface. Compare multiple TTS models.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["model-comparison", "ab-testing", "quality-metrics"],
        languages=["en", "es", "fr", "de", "zh", "ja", "ko"]
    ),
    ServiceEndpoint(
        name="RVC (Retrieval Voice Conversion)",
        url="https://rvc.ailabsafrica.com",
        description="Voice conversion and cloning using retrieval-based methods.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["voice-conversion", "voice-cloning", "pitch-shift"],
        languages=["en"],
        health_endpoint="/"
    ),
    ServiceEndpoint(
        name="Vapi TTS Webhook",
        url="https://vapi-tts.ailabsafrica.com",
        api_url="https://vapi-tts.ailabsafrica.com/api/vapi/tts-webhook",
        description="Custom TTS webhook service for Vapi voice assistants.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=30036,
        status=ServiceStatus.ACTIVE,
        features=["vapi-integration", "pcm-audio", "rate-limiting", "fallback"],
        languages=["en"],
        health_endpoint="/api/vapi/health",
        metadata={"default_provider": "styletts2", "fallback_provider": "kokoro"}
    ),
]

# ASR Services Directory
ASR_SERVICES: List[ServiceEndpoint] = [
    ServiceEndpoint(
        name="Whisper ASR",
        url="https://whisper.ailabsafrica.com",
        api_url="https://whisper.ailabsafrica.com/transcribe",
        description="Faster Whisper ASR with GPU acceleration. Supports 100+ languages.",
        deployment=DeploymentType.RUNPOD_GPU,
        port=8011,
        status=ServiceStatus.ACTIVE,
        features=["multilingual", "streaming", "timestamps", "gpu-accelerated"],
        languages=["en", "es", "fr", "de", "zh", "ja", "ko", "ar", "hi", "pt", "ru", "and 90+ more"],
        health_endpoint="/health",
        websocket_url="wss://whisper.ailabsafrica.com/ws/"
    ),
    ServiceEndpoint(
        name="Voice Lab ASR",
        url="https://api.ailabsafrica.com/api/voice-lab",
        api_url="https://api.ailabsafrica.com/api/voice-lab/transcribe",
        description="Twi/Akan specialized ASR with dialect support (Asante, Akuapem, Fante).",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=30027,
        status=ServiceStatus.ACTIVE,
        features=["twi-specialized", "dialect-detection", "text-enhancement"],
        languages=["tw", "ak", "ee"],
        health_endpoint="/health",
        metadata={"dialects": ["asante", "akuapem", "fante"]}
    ),
]

# LLM Services Directory
LLM_SERVICES: List[ServiceEndpoint] = [
    ServiceEndpoint(
        name="Ollama",
        url="https://ollama.ailabsafrica.com",
        api_url="https://ollama.ailabsafrica.com/api/generate",
        description="Local LLM inference with multiple models. OpenAI-compatible API.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=11434,
        status=ServiceStatus.ACTIVE,
        features=["multi-model", "streaming", "embeddings", "openai-compatible"],
        languages=["en", "multilingual"],
        health_endpoint="/api/tags",
        metadata={
            "models_endpoint": "/api/tags",
            "chat_endpoint": "/api/chat",
            "embeddings_endpoint": "/api/embeddings"
        }
    ),
    ServiceEndpoint(
        name="Open WebUI",
        url="https://openwebui.ailabsafrica.com",
        description="All-in-one LLM chat interface with TTS/ASR integration.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8007,
        status=ServiceStatus.ACTIVE,
        features=["chat-ui", "document-upload", "tts-integration", "multi-model"],
        languages=["en", "multilingual"],
        health_endpoint="/health"
    ),
    ServiceEndpoint(
        name="Flowise",
        url="https://flowise.ailabsafrica.com",
        description="Low-code LLM orchestration and workflow builder.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=3001,
        status=ServiceStatus.ACTIVE,
        features=["low-code", "workflow-builder", "agents", "chatflows"],
        languages=["en", "multilingual"]
    ),
    ServiceEndpoint(
        name="Kyutai Moshi",
        url="https://kyutai.ailabsafrica.com",
        description="Real-time conversational AI with full-duplex dialogue capability.",
        deployment=DeploymentType.RUNPOD_GPU,
        status=ServiceStatus.ACTIVE,
        features=["real-time-conversation", "full-duplex", "streaming"],
        languages=["en"],
        websocket_url="wss://kyutai.ailabsafrica.com/ws/conversation"
    ),
]

# Tools and Utilities Directory
TOOLS_SERVICES: List[ServiceEndpoint] = [
    ServiceEndpoint(
        name="Crawl4AI",
        url="https://crawl4ai.ailabsafrica.com",
        description="AI-powered web scraping and content extraction service.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8009,
        status=ServiceStatus.ACTIVE,
        features=["web-scraping", "content-extraction", "ai-powered"],
        languages=["en", "multilingual"]
    ),
    ServiceEndpoint(
        name="Voice Demos",
        url="https://voice-demos.ailabsafrica.com",
        description="Interactive voice AI demos and showcases.",
        deployment=DeploymentType.LOCAL_DOCKER,
        status=ServiceStatus.ACTIVE,
        features=["demos", "showcases", "interactive"],
        languages=["en"]
    ),
    ServiceEndpoint(
        name="Demos Portal",
        url="https://demos.ailabsafrica.com",
        description="Collection of AI demos and proof-of-concepts.",
        deployment=DeploymentType.LOCAL_DOCKER,
        status=ServiceStatus.ACTIVE,
        features=["demos", "poc", "showcase"],
        languages=["en"]
    ),
    ServiceEndpoint(
        name="Supabase",
        url="https://supabase.ailabsafrica.com",
        api_url="https://supabase-api.ailabsafrica.com",
        description="Self-hosted Supabase for authentication and database.",
        deployment=DeploymentType.LOCAL_DOCKER,
        port=8000,
        status=ServiceStatus.ACTIVE,
        features=["authentication", "database", "realtime", "storage"],
        languages=["en"],
        metadata={
            "realtime_url": "wss://supabase.ailabsafrica.com/realtime/v1"
        }
    ),
]


def get_service_directory() -> ServiceDirectory:
    """
    Get the complete service directory.

    Returns:
        ServiceDirectory: Complete directory of all services grouped by category.
    """
    return ServiceDirectory(
        tts=TTS_SERVICES,
        asr=ASR_SERVICES,
        llm=LLM_SERVICES,
        tools=TOOLS_SERVICES
    )


def get_services_by_category(category: ServiceCategory) -> List[ServiceEndpoint]:
    """
    Get services by category.

    Args:
        category: Service category (tts, asr, llm, tools)

    Returns:
        List of services in the specified category.
    """
    category_map = {
        ServiceCategory.TTS: TTS_SERVICES,
        ServiceCategory.ASR: ASR_SERVICES,
        ServiceCategory.LLM: LLM_SERVICES,
        ServiceCategory.TOOLS: TOOLS_SERVICES,
    }
    return category_map.get(category, [])


def get_active_services() -> ServiceDirectory:
    """
    Get only active services.

    Returns:
        ServiceDirectory: Directory containing only active services.
    """
    return ServiceDirectory(
        tts=[s for s in TTS_SERVICES if s.status == ServiceStatus.ACTIVE],
        asr=[s for s in ASR_SERVICES if s.status == ServiceStatus.ACTIVE],
        llm=[s for s in LLM_SERVICES if s.status == ServiceStatus.ACTIVE],
        tools=[s for s in TOOLS_SERVICES if s.status == ServiceStatus.ACTIVE]
    )


def get_services_with_feature(feature: str) -> List[ServiceEndpoint]:
    """
    Get all services that have a specific feature.

    Args:
        feature: Feature to filter by (e.g., 'voice-cloning', 'streaming')

    Returns:
        List of services with the specified feature.
    """
    all_services = TTS_SERVICES + ASR_SERVICES + LLM_SERVICES + TOOLS_SERVICES
    return [s for s in all_services if feature.lower() in [f.lower() for f in s.features]]


def get_services_by_language(language: str) -> List[ServiceEndpoint]:
    """
    Get all services that support a specific language.

    Args:
        language: Language code to filter by (e.g., 'en', 'zh', 'tw')

    Returns:
        List of services supporting the specified language.
    """
    all_services = TTS_SERVICES + ASR_SERVICES + LLM_SERVICES + TOOLS_SERVICES
    return [s for s in all_services if language.lower() in [l.lower() for l in s.languages]]


def get_services_by_deployment(deployment: DeploymentType) -> List[ServiceEndpoint]:
    """
    Get all services by deployment type.

    Args:
        deployment: Deployment type (local_docker, runpod_gpu, external)

    Returns:
        List of services with the specified deployment type.
    """
    all_services = TTS_SERVICES + ASR_SERVICES + LLM_SERVICES + TOOLS_SERVICES
    return [s for s in all_services if s.deployment == deployment]


def get_directory_summary() -> Dict[str, Any]:
    """
    Get a summary of the service directory.

    Returns:
        Dictionary with summary statistics.
    """
    all_services = TTS_SERVICES + ASR_SERVICES + LLM_SERVICES + TOOLS_SERVICES
    active_services = [s for s in all_services if s.status == ServiceStatus.ACTIVE]

    return {
        "total_services": len(all_services),
        "active_services": len(active_services),
        "by_category": {
            "tts": len(TTS_SERVICES),
            "asr": len(ASR_SERVICES),
            "llm": len(LLM_SERVICES),
            "tools": len(TOOLS_SERVICES)
        },
        "by_deployment": {
            "local_docker": len([s for s in all_services if s.deployment == DeploymentType.LOCAL_DOCKER]),
            "runpod_gpu": len([s for s in all_services if s.deployment == DeploymentType.RUNPOD_GPU]),
            "external": len([s for s in all_services if s.deployment == DeploymentType.EXTERNAL])
        },
        "features_available": list(set(
            feature for s in all_services for feature in s.features
        )),
        "languages_supported": list(set(
            lang for s in all_services for lang in s.languages
        ))
    }

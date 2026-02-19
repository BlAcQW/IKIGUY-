"""
Shared AI Services Module

Provides generic, reusable services for managing AI providers (TTS, LLM, ASR, VAD, etc.)
across all applications in the platform.

Usage:
    from apps.shared.integration.ai_services import (
        AIProviderService,
        ProviderRegistry,
        HealthMonitor,
        VADSession,
        VoiceActivityDetector
    )
"""

from .ai_provider_service import (
    AIProviderService,
    AIProvider,
    ProviderCapabilities,
    ProviderType,
    ProviderStatus,
)
from .provider_registry import (
    ProviderRegistry,
    get_global_registry,
    reset_global_registry,
    get_default_tts_providers_config,
    get_default_llm_providers_config,
    get_default_asr_providers_config,
)
from .health_monitor_service import HealthMonitorService
from .vad_service import (
    VoiceActivityDetector,
    VADSession,
    create_vad_session,
    process_pcm_stream,
)
from .streaming_tts_service import (
    StreamingTTSService,
    get_streaming_tts_service,
)
from .melotts_service import (
    MeloTTSService,
    get_melotts_service,
)
from .f5tts_service import (
    F5TTSService,
    get_f5tts_service,
)
from .openvoice_service import (
    OpenVoiceService,
    get_openvoice_service,
)
from .styletts2_service import (
    StyleTTS2Service,
    get_styletts2_service,
)
from .kokoro_service import (
    KokoroService,
    get_kokoro_service,
)
from .unified_tts_service import (
    UnifiedTTSService,
    TTSModel,
    TTSResult,
    get_unified_tts_service,
)

# Import VoicePipeline (avoid circular import by importing at module level)
try:
    from ..voice_pipeline import (
        VoicePipeline,
        create_voice_pipeline,
    )
except ImportError:
    # Voice pipeline may have dependencies that aren't always available
    VoicePipeline = None
    create_voice_pipeline = None

__all__ = [
    # AI Provider Services
    "AIProviderService",
    "AIProvider",
    "ProviderCapabilities",
    "ProviderType",
    "ProviderStatus",
    # Provider Registry
    "ProviderRegistry",
    "get_global_registry",
    "reset_global_registry",
    "get_default_tts_providers_config",
    "get_default_llm_providers_config",
    "get_default_asr_providers_config",
    # Health Monitoring
    "HealthMonitorService",
    # Voice Activity Detection
    "VoiceActivityDetector",
    "VADSession",
    "create_vad_session",
    "process_pcm_stream",
    # Streaming TTS
    "StreamingTTSService",
    "get_streaming_tts_service",
    # MeloTTS
    "MeloTTSService",
    "get_melotts_service",
    # F5-TTS
    "F5TTSService",
    "get_f5tts_service",
    # OpenVoice
    "OpenVoiceService",
    "get_openvoice_service",
    # StyleTTS2
    "StyleTTS2Service",
    "get_styletts2_service",
    # Kokoro-82M
    "KokoroService",
    "get_kokoro_service",
    # Unified TTS Service
    "UnifiedTTSService",
    "TTSModel",
    "TTSResult",
    "get_unified_tts_service",
    # Voice Pipeline
    "VoicePipeline",
    "create_voice_pipeline",
]

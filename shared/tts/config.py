"""
TTS Provider Configuration
Central configuration for all TTS providers.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .models import TTSProvider, TTSCapabilities, AudioFormat


class ProviderEndpoint(BaseModel):
    """Provider endpoint configuration."""
    base_url: str
    health_path: str = "/health"
    synthesize_path: str = "/synthesize"
    voice_clone_path: Optional[str] = None
    websocket_path: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 1


class TTSProviderConfig(BaseModel):
    """TTS provider configuration."""
    id: TTSProvider
    name: str
    description: str
    endpoint: ProviderEndpoint
    capabilities: TTSCapabilities
    languages: Dict[str, str] = Field(default_factory=dict)
    speakers: Dict[str, str] = Field(default_factory=dict)
    auth_required: bool = False
    api_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Provider configurations
PROVIDER_CONFIGS: Dict[TTSProvider, TTSProviderConfig] = {
    TTSProvider.F5TTS: TTSProviderConfig(
        id=TTSProvider.F5TTS,
        name="F5-TTS",
        description="Flow-matching based TTS with voice cloning. Running on RunPod GPU (Port 8010).",
        endpoint=ProviderEndpoint(
            base_url="https://f5tts.ailabsafrica.com",  # F5-TTS on RunPod port 8010
            health_path="/",
            synthesize_path="/api/predict",
            voice_clone_path="/api/predict"
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,
            pitch_control=True,  # Enable pitch control
            streaming=True,
            supported_languages=["en", "zh", "ja", "ko"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean"
        }
    ),

    TTSProvider.STYLETTS2: TTSProviderConfig(
        id=TTSProvider.STYLETTS2,
        name="StyleTTS2",
        description="High-quality expressive TTS with style transfer. Running on RunPod GPU (Port 8012 for UI, 8013 for API).",
        endpoint=ProviderEndpoint(
            base_url="https://styletts-ui.ailabsafrica.com",  # StyleTTS2 Gradio UI on RunPod port 8012
            health_path="/",  # Gradio root endpoint
            synthesize_path="/api/predict",  # Gradio API endpoint
            voice_clone_path="/api/predict"
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            speed_control=True,  # Enable speed control
            pitch_control=True,  # Enable pitch control
            emotion_control=True,
            streaming=True,
            supported_languages=["en"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English"
        }
    ),

    # Moshi/Kyutai - Real-time conversational AI
    # Running on RunPod internal port 8008, exposed via port 8018
    # Access: Via Voice Lab Unified API (ttslab.ailabsafrica.com) or direct WebSocket
    TTSProvider.MOSHI: TTSProviderConfig(
        id=TTSProvider.MOSHI,
        name="Kyutai Moshi",
        description="Real-time conversational AI with full-duplex dialogue. Supports WebSocket for real-time conversation. Running on RunPod GPU (Port 8018).",
        endpoint=ProviderEndpoint(
            base_url="https://ttslab.ailabsafrica.com",  # Via Voice Lab Unified API
            health_path="/api/moshi/health",
            synthesize_path="/api/moshi/ws/conversation",  # WebSocket endpoint
            websocket_path="/api/moshi/ws/conversation",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            real_time_conversation=True,
            streaming=True,
            supported_languages=["en"],
            supported_formats=[AudioFormat.PCM, AudioFormat.WAV]
        ),
        languages={
            "en": "English"
        },
        metadata={
            "runpod_internal_port": 8008,
            "runpod_external_port": 8018,
            "interface": "web-ui",
            "requires_websocket": True,
            "unified_api": "https://ttslab.ailabsafrica.com",
            "direct_access": "https://kyutai.ailabsafrica.com",
            "moshi_info": "/api/moshi/info",
            "moshi_health": "/api/moshi/health",
            "moshi_ws": "/api/moshi/ws/conversation"
        }
    ),

    TTSProvider.COQUI_XTTS: TTSProviderConfig(
        id=TTSProvider.COQUI_XTTS,
        name="Coqui XTTS v2",
        description="Multilingual TTS with voice cloning. Running locally on Docker (Port 8005).",
        endpoint=ProviderEndpoint(
            base_url="https://coqui.ailabsafrica.com",
            synthesize_path="/synthesize",
            voice_clone_path="/clone"
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,
            pitch_control=True,  # Enable pitch control
            ssml_support=True,
            supported_languages=[
                "en", "es", "fr", "de", "it", "pt", "pl", "tr",
                "ru", "nl", "cs", "ar", "zh-cn", "hu", "ko", "ja", "hi"
            ],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3, AudioFormat.OGG]
        ),
        languages={
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "pl": "Polish",
            "tr": "Turkish",
            "ru": "Russian",
            "nl": "Dutch",
            "cs": "Czech",
            "ar": "Arabic",
            "zh-cn": "Chinese (Simplified)",
            "hu": "Hungarian",
            "ko": "Korean",
            "ja": "Japanese",
            "hi": "Hindi"
        }
    ),

    TTSProvider.MELOTTS: TTSProviderConfig(
        id=TTSProvider.MELOTTS,
        name="MeloTTS",
        description="Fast multilingual synthesis with multi-speaker support. Running locally on Docker (Port 8001).",
        endpoint=ProviderEndpoint(
            base_url="https://melotts.ailabsafrica.com",
            synthesize_path="/synthesize"
        ),
        capabilities=TTSCapabilities(
            multi_language=True,
            speed_control=True,
            pitch_control=True,
            multi_speaker=True,
            ssml_support=True,
            supported_languages=["EN", "ES", "FR", "ZH", "JP", "KR"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "EN": "English",
            "ES": "Spanish",
            "FR": "French",
            "ZH": "Chinese",
            "JP": "Japanese",
            "KR": "Korean"
        },
        speakers={
            "EN-US": "American English",
            "EN-BR": "British English",
            "EN-INDIA": "Indian English",
            "EN-AU": "Australian English",
            "EN-Default": "Default English"
        }
    ),

    TTSProvider.OPENVOICE: TTSProviderConfig(
        id=TTSProvider.OPENVOICE,
        name="OpenVoice",
        description="Advanced voice cloning with emotion control. Running locally on Docker (Port 8003).",
        endpoint=ProviderEndpoint(
            base_url="https://openvoice.ailabsafrica.com",
            synthesize_path="/synthesize",
            voice_clone_path="/clone"
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,  # Enable speed control
            pitch_control=True,
            emotion_control=True,
            supported_languages=["EN", "ZH"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "EN": "English",
            "ZH": "Chinese"
        }
    ),

    TTSProvider.KOKORO: TTSProviderConfig(
        id=TTSProvider.KOKORO,
        name="Kokoro TTS",
        description="Fast, high-quality TTS with natural prosody. Based on Kokoro-82M model. Running locally on Docker (Port 8010).",
        endpoint=ProviderEndpoint(
            base_url="https://kokoro.ailabsafrica.com",
            synthesize_path="/synthesize",
            voice_clone_path=None  # Kokoro doesn't support voice cloning
        ),
        capabilities=TTSCapabilities(
            voice_cloning=False,
            multi_language=False,  # English only (American & British)
            speed_control=True,
            pitch_control=True,
            multi_speaker=True,  # 11 voice packs
            supported_languages=["en"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English"
        },
        speakers={
            "af_heart": "Heart (female, American)",
            "af_bella": "Bella (female, American)",
            "af_nicole": "Nicole (female, American)",
            "af_sarah": "Sarah (female, American)",
            "af_sky": "Sky (female, American)",
            "am_adam": "Adam (male, American)",
            "am_michael": "Michael (male, American)",
            "bf_emma": "Emma (female, British)",
            "bf_isabella": "Isabella (female, British)",
            "bm_george": "George (male, British)",
            "bm_lewis": "Lewis (male, British)"
        }
    ),

    TTSProvider.CHATTERBOX: TTSProviderConfig(
        id=TTSProvider.CHATTERBOX,
        name="Chatterbox",
        description="Expressive text-to-speech model with reference audio support for voice cloning. Running locally on Docker (Port 8004).",
        endpoint=ProviderEndpoint(
            base_url="https://chatterbox.ailabsafrica.com",
            health_path="/",  # Gradio root endpoint
            synthesize_path="/gradio_api/call/generate_tts_audio",  # Gradio API endpoint
            voice_clone_path="/gradio_api/call/generate_tts_audio",  # Gradio API endpoint (same for cloning)
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=False,  # English primarily
            speed_control=True,
            pitch_control=False,
            multi_speaker=False,
            supported_languages=["en"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English"
        },
        speakers={
            "chatterbox-default": "Default voice",
            "chatterbox-female-1": "Female voice 1",
            "chatterbox-male-1": "Male voice 1"
        },
        metadata={
            "deployment": "local-docker",
            "platform": "gradio",
            "features": ["voice-cloning", "reference-audio", "expressive-speech"]
        }
    ),

    # TTS-WebUI / Voice Lab Unified API
    # Comprehensive gateway for TTS, ASR, and LLM services on RunPod
    # Available at ttslab.ailabsafrica.com (port 8019)
    TTSProvider.TTS_WEBUI: TTSProviderConfig(
        id=TTSProvider.TTS_WEBUI,
        name="Voice Lab Unified API",
        description="Unified gateway for TTS, ASR, and LLM services. Provides access to multiple providers through a single API. Running on RunPod GPU (Port 8019).",
        endpoint=ProviderEndpoint(
            base_url="https://ttslab.ailabsafrica.com",  # Voice Lab Unified API on RunPod port 8019
            synthesize_path="/api/tts/synthesize",
            health_path="/api/health",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            multi_model=True,
            speed_control=True,
            emotion_control=True,
            streaming=True,
            supported_languages=["en", "es", "fr", "de", "zh", "ja", "ko", "pt", "ru"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3, AudioFormat.PCM],
            available_models=[
                "f5-tts", "styletts2", "gpt-sovits", "zonos", "fish-speech",
                "whisper-asr"
            ]
        ),
        languages={
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "pt": "Portuguese",
            "ru": "Russian"
        },
        metadata={
            "runpod_port": 8019,
            "api_docs": "https://ttslab.ailabsafrica.com/docs",
            "endpoints": {
                "directory": "/api/directory",
                "health": "/api/health",
                "synthesize": "/api/tts/synthesize",
                "transcribe": "/api/asr/transcribe",
                "providers": "/api/providers"
            },
            "deployment": "runpod"
        }
    ),

    TTSProvider.FISH_SPEECH: TTSProviderConfig(
        id=TTSProvider.FISH_SPEECH,
        name="Fish Speech",
        description="Zero-shot voice cloning with minimal reference audio. Fast inference and natural speech. Running on RunPod GPU (Port 8015).",
        endpoint=ProviderEndpoint(
            base_url="https://fishspeech.ailabsafrica.com",
            health_path="/",  # Gradio root endpoint
            synthesize_path="/synthesize",
            voice_clone_path="/clone",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,
            streaming=True,
            supported_languages=["en", "zh", "ja", "ko", "es", "fr", "de", "ru"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ru": "Russian"
        },
        metadata={
            "gradio_ui": "https://fishspeech.ailabsafrica.com",
            "deployment": "runpod",
            "community_rank": 2,
            "features": ["zero-shot", "few-shot", "fast-inference"]
        }
    ),

    TTSProvider.ZONOS: TTSProviderConfig(
        id=TTSProvider.ZONOS,
        name="Zonos TTS",
        description="Experimental TTS with emotion control sliders. Highly customizable prosody and expressiveness. Running on RunPod GPU (Port 8014).",
        endpoint=ProviderEndpoint(
            base_url="https://zonos.ailabsafrica.com",
            health_path="/",  # Gradio root endpoint
            synthesize_path="/synthesize",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=False,
            multi_language=False,
            emotion_control=True,
            speed_control=True,
            pitch_control=True,
            supported_languages=["en"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English"
        },
        metadata={
            "gradio_ui": "https://zonos.ailabsafrica.com",
            "deployment": "runpod",
            "experimental": True,
            "features": ["emotion-sliders", "prosody-control", "expressiveness"]
        }
    ),

    # NOTE: IndexTTS requires TTS-WebUI which is NOT deployed.
    TTSProvider.INDEXTTS: TTSProviderConfig(
        id=TTSProvider.INDEXTTS,
        name="IndexTTS 2.0 (UNAVAILABLE)",
        description="[NOT DEPLOYED] Advanced TTS with voice cloning. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            health_path="/",
            synthesize_path="/synthesize",
            voice_clone_path="/clone",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            emotion_control=True,
            speed_control=True,
            multi_speaker=True,
            supported_languages=["en", "zh"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "zh": "Chinese"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "platform": "tts-webui-extension"
        }
    ),

    # NOTE: VoxCPM requires TTS-WebUI which is NOT deployed.
    TTSProvider.VOXCPM: TTSProviderConfig(
        id=TTSProvider.VOXCPM,
        name="VoxCPM (UNAVAILABLE)",
        description="[NOT DEPLOYED] Context-aware TTS model. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            health_path="/",
            synthesize_path="/synthesize",
            voice_clone_path="/clone",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,
            supported_languages=["en", "zh"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "zh": "Chinese"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "model_family": "CPM"
        }
    ),

    TTSProvider.GPT_SOVITS: TTSProviderConfig(
        id=TTSProvider.GPT_SOVITS,
        name="GPT-SoVITS",
        description="Powerful zero-shot voice cloning with GPT-based TTS. Minimal reference audio needed for high-quality voice cloning. Running on RunPod GPU (Port 8016).",
        endpoint=ProviderEndpoint(
            base_url="https://gptsovits-ui.ailabsafrica.com",  # GPT-SoVITS Gradio UI on RunPod port 8016
            health_path="/",  # Gradio root endpoint
            synthesize_path="/api/predict",  # Gradio API endpoint
            voice_clone_path="/api/predict",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,
            emotion_control=True,
            supported_languages=["en", "zh", "ja", "ko"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean"
        },
        metadata={
            "deployment": "runpod",
            "interface": "gradio",
            "features": ["zero-shot-cloning", "few-shot-cloning", "gpt-based", "high-quality"]
        }
    ),

    # NOTE: All TTS-WebUI Model-Specific Providers are UNAVAILABLE because TTS-WebUI is not deployed.
    # These providers require TTS-WebUI which currently points to GPT-SoVITS instead.

    TTSProvider.BARK: TTSProviderConfig(
        id=TTSProvider.BARK,
        name="Bark (UNAVAILABLE)",
        description="[NOT DEPLOYED] Multi-language generative TTS. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            synthesize_path="/api/v1/audio/speech",
            health_path="/",
            timeout=90
        ),
        capabilities=TTSCapabilities(
            multi_language=True,
            speed_control=True,
            supported_languages=["en", "de", "es", "fr", "hi", "it", "ja", "ko", "pl", "pt", "ru", "tr", "zh"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "de": "German",
            "es": "Spanish",
            "fr": "French",
            "hi": "Hindi",
            "it": "Italian",
            "ja": "Japanese",
            "ko": "Korean",
            "pl": "Polish",
            "pt": "Portuguese",
            "ru": "Russian",
            "tr": "Turkish",
            "zh": "Chinese"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "platform": "tts-webui",
            "model": "bark"
        }
    ),

    TTSProvider.TORTOISE: TTSProviderConfig(
        id=TTSProvider.TORTOISE,
        name="Tortoise TTS (UNAVAILABLE)",
        description="[NOT DEPLOYED] High-quality TTS with voice cloning. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            synthesize_path="/api/v1/audio/speech",
            health_path="/",
            timeout=120
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            speed_control=True,
            supported_languages=["en"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "platform": "tts-webui",
            "model": "tortoise"
        }
    ),

    TTSProvider.MAHATTS: TTSProviderConfig(
        id=TTSProvider.MAHATTS,
        name="MahaTTS (UNAVAILABLE)",
        description="[NOT DEPLOYED] Indic language TTS. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            synthesize_path="/api/v1/audio/speech",
            health_path="/",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            multi_language=True,
            speed_control=True,
            supported_languages=["as", "bn", "gu", "hi", "kn", "ml", "mr", "or", "pa", "ta", "te"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "as": "Assamese",
            "bn": "Bengali",
            "gu": "Gujarati",
            "hi": "Hindi",
            "kn": "Kannada",
            "ml": "Malayalam",
            "mr": "Marathi",
            "or": "Odia",
            "pa": "Punjabi",
            "ta": "Tamil",
            "te": "Telugu"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "platform": "tts-webui",
            "model": "mahatts"
        }
    ),

    TTSProvider.MMS: TTSProviderConfig(
        id=TTSProvider.MMS,
        name="Meta MMS (UNAVAILABLE)",
        description="[NOT DEPLOYED] Meta's Massively Multilingual Speech model. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            synthesize_path="/api/v1/audio/speech",
            health_path="/",
            timeout=60
        ),
        capabilities=TTSCapabilities(
            multi_language=True,
            speed_control=True,
            supported_languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hi", "sw"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "pl": "Polish",
            "tr": "Turkish",
            "ru": "Russian",
            "nl": "Dutch",
            "cs": "Czech",
            "ar": "Arabic",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "hi": "Hindi",
            "sw": "Swahili"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "platform": "tts-webui",
            "model": "mms"
        }
    ),

    TTSProvider.VALLE_X: TTSProviderConfig(
        id=TTSProvider.VALLE_X,
        name="VALL-E X (UNAVAILABLE)",
        description="[NOT DEPLOYED] Zero-shot voice cloning with cross-lingual capabilities. Requires TTS-WebUI which is not currently running.",
        endpoint=ProviderEndpoint(
            base_url="https://tts-webui.ailabsafrica.com",  # WARNING: Points to GPT-SoVITS!
            synthesize_path="/api/v1/audio/speech",
            health_path="/",
            timeout=90
        ),
        capabilities=TTSCapabilities(
            voice_cloning=True,
            multi_language=True,
            speed_control=True,
            supported_languages=["en", "zh", "ja"],
            supported_formats=[AudioFormat.WAV, AudioFormat.MP3]
        ),
        languages={
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese"
        },
        metadata={
            "status": "unavailable",
            "reason": "Requires TTS-WebUI which is not deployed",
            "deployment": "runpod",
            "platform": "tts-webui",
            "model": "valle-x",
            "features": ["zero-shot", "voice-cloning", "cross-lingual"]
        }
    ),
}


# Ghanaian voice samples configuration
GHANAIAN_VOICES = {
    "nana_aba": {
        "name": "Nana Aba",
        "file": "nana_aba.wav",
        "path": "/opt/kasaai/apps/voice-lab/voices/nana_aba.wav",
        "description": "Professional female Ghanaian voice",
        "gender": "female",
        "language": "en-GH"
    },
    "adom_okyere": {
        "name": "Adom Okyere",
        "file": "adom_okyere.wav",
        "path": "/opt/kasaai/apps/voice-lab/voices/adom_okyere.wav",
        "description": "Male Ghanaian voice",
        "gender": "male",
        "language": "en-GH"
    },
    "juliet_bawuah": {
        "name": "Juliet Bawuah",
        "file": "juliet_bawuah.wav",
        "path": "/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav",
        "description": "Female Ghanaian voice",
        "gender": "female",
        "language": "en-GH"
    },
}


def get_provider_config(provider: TTSProvider) -> TTSProviderConfig:
    """Get configuration for a specific provider.

    Args:
        provider: TTS provider enum

    Returns:
        Provider configuration

    Raises:
        ValueError: If provider not found
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider}")
    return PROVIDER_CONFIGS[provider]


def get_available_providers() -> Dict[TTSProvider, TTSProviderConfig]:
    """Get all available provider configurations.

    Returns:
        Dictionary of provider configurations
    """
    return PROVIDER_CONFIGS.copy()


def get_deployed_providers() -> Dict[TTSProvider, TTSProviderConfig]:
    """Get only providers that are actually deployed and running.

    Filters out providers marked as unavailable in their metadata.

    Returns:
        Dictionary of deployed provider configurations
    """
    result = {}
    for provider_id, config in PROVIDER_CONFIGS.items():
        # Check if provider is marked as unavailable
        if config.metadata.get("status") == "unavailable":
            continue
        # Check if name contains "(UNAVAILABLE)"
        if "(UNAVAILABLE)" in config.name:
            continue
        result[provider_id] = config
    return result


def get_providers_with_capability(capability: str) -> Dict[TTSProvider, TTSProviderConfig]:
    """Get providers with a specific capability.

    Args:
        capability: Capability name (e.g., 'voice_cloning', 'multi_language')

    Returns:
        Dictionary of providers with the capability
    """
    result = {}
    for provider_id, config in PROVIDER_CONFIGS.items():
        if hasattr(config.capabilities, capability):
            if getattr(config.capabilities, capability):
                result[provider_id] = config
    return result
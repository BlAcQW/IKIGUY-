"""
Shared TTS Module
Provides unified interface for all TTS services across Kasaai applications.
"""

from .providers import (
    TTSProvider,
    TTSProviderConfig,
    F5TTSProvider,
    StyleTTS2Provider,
    MoshiProvider,
    CoquiXTTSProvider,
    MeloTTSProvider,
    OpenVoiceProvider,
    KokoroTTSProvider,
    TTSWebUIProvider,
    FishSpeechProvider,
    ZonosTTSProvider,
)
from .client import TTSClient, AsyncTTSClient
from .models import (
    TTSRequest,
    TTSResponse,
    VoiceCloneRequest,
    ConversationRequest,
    TTSCapabilities,
)
from .exceptions import (
    TTSException,
    ProviderNotAvailableError,
    ModelNotLoadedError,
    AudioProcessingError,
)
from .utils import AudioUtils, AudioFormat

__all__ = [
    # Providers
    'TTSProvider',
    'TTSProviderConfig',
    'F5TTSProvider',
    'StyleTTS2Provider',
    'MoshiProvider',
    'CoquiXTTSProvider',
    'MeloTTSProvider',
    'OpenVoiceProvider',
    'KokoroTTSProvider',
    'TTSWebUIProvider',
    'FishSpeechProvider',
    'ZonosTTSProvider',

    # Clients
    'TTSClient',
    'AsyncTTSClient',

    # Models
    'TTSRequest',
    'TTSResponse',
    'VoiceCloneRequest',
    'ConversationRequest',
    'TTSCapabilities',

    # Exceptions
    'TTSException',
    'ProviderNotAvailableError',
    'ModelNotLoadedError',
    'AudioProcessingError',

    # Utils
    'AudioUtils',
    'AudioFormat',
]

__version__ = '1.0.0'
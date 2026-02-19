"""
PCM Audio and VAD Handler for InkWave Voice Chat.

DEPRECATED: This module is deprecated. Please use the shared library instead:
    from apps.shared.voice import PCMVADHandler, pcm_to_wav, pcm_base64_to_wav_base64

This module re-exports from apps.shared.voice for backwards compatibility.
"""

import warnings
import sys

# Add shared to path
sys.path.insert(0, '/opt/kasaai/apps')

warnings.warn(
    "inkwave.app.services.pcm_vad_handler is deprecated. "
    "Use apps.shared.voice instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from shared for backwards compatibility
from apps.shared.voice import (
    PCMVADHandler,
    SimplePCMAccumulator,
    pcm_to_wav,
    pcm_base64_to_wav_base64,
)

__all__ = [
    'pcm_to_wav',
    'PCMVADHandler',
    'SimplePCMAccumulator',
    'pcm_base64_to_wav_base64'
]

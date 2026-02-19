"""Utilities for the shared voice engine.

This package exposes helper classes and functions lazily to avoid importing optional
dependencies like ``requests`` during test collection.
"""

# Import all voice engine functions from the main voice_engine.py module
# Using absolute import to avoid circular import issues
import sys
import importlib.util

# Import functions from voice_engine.py at module level
spec = importlib.util.spec_from_file_location("voice_engine_funcs", "/opt/kasaai/apps/shared/voice_engine.py")
ve_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ve_module)

# Expose the functions
calculate_energy = ve_module.calculate_energy
calculate_wer = ve_module.calculate_wer
is_silence = ve_module.is_silence
synthesize_text = ve_module.synthesize_text
synthesize_with_voice = ve_module.synthesize_with_voice
get_registered_voices = ve_module.get_registered_voices
transcribe_samples = ve_module.transcribe_samples
register_voice = ve_module.register_voice
loop_samples = ve_module.loop_samples
barge_in = ve_module.barge_in

# Add missing functions as stubs until they are properly implemented
def retry_with_fallback(func, *args, **kwargs):
    """Retry function with fallback - stub implementation."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Log and return a default result
        import logging
        logging.warning(f"retry_with_fallback: Function {func.__name__} failed: {e}")
        return None

def redact_pii(text: str) -> str:
    """Redact PII from text - stub implementation."""
    import logging
    logging.warning("redact_pii: Stub implementation - no PII redaction performed")
    return text

def detect_consent(audio_data) -> bool:
    """Detect consent in audio - stub implementation."""
    import logging
    logging.warning("detect_consent: Stub implementation - always returns True")
    return True

def maybe_retain_audio(audio_data, consent: bool = True):
    """Maybe retain audio based on consent - stub implementation."""
    import logging
    logging.warning("maybe_retain_audio: Stub implementation - no audio retention")
    return None

__all__ = [
    "OutboundCallManager", 
    "create_manager_from_env", 
    "webrtc_router",
    "calculate_energy",
    "calculate_wer", 
    "is_silence",
    "synthesize_text",
    "synthesize_with_voice",
    "get_registered_voices",
    "transcribe_samples",
    "register_voice",
    "loop_samples",
    "barge_in",
    "retry_with_fallback",
    "redact_pii",
    "detect_consent",
    "maybe_retain_audio"
]


def __getattr__(name: str):
    """Dynamically import outbound call helpers on first access.

    Args:
        name: Attribute requested.

    Returns:
        Object defined in :mod:`.outbound_call` or :mod:`.webrtc_bridge`.

    Raises:
        AttributeError: If ``name`` is not a known helper.
    """

    if name in ["OutboundCallManager", "create_manager_from_env"]:
        from .outbound_call import OutboundCallManager, create_manager_from_env

        mapping = {
            "OutboundCallManager": OutboundCallManager,
            "create_manager_from_env": create_manager_from_env,
        }
        return mapping[name]
    elif name == "webrtc_router":
        from .webrtc_bridge import router as webrtc_router
        return webrtc_router
    
    raise AttributeError(f"module 'voice_engine' has no attribute {name!r}")

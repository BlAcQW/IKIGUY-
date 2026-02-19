"""
TTS Provider ID Standardization

Provides canonical snake_case provider IDs and mapping from legacy IDs.
Ensures consistent provider identification across all TTS systems.

Canonical Format: lowercase_snake_case
Examples: coqui_xtts, style_tts2, f5_tts, melo_tts

Usage:
    from apps.shared.tts.provider_ids import ProviderID, normalize_provider_id

    # Use canonical IDs
    provider = ProviderID.COQUI_XTTS

    # Normalize legacy ID
    canonical = normalize_provider_id("XTTS")  # Returns "coqui_xtts"

Author: KasaAI Team
Date: 2025-11-23
"""

from typing import Optional, Dict, Set, Any
from enum import Enum


class ProviderID:
    """
    Canonical TTS provider IDs.

    All IDs use lowercase snake_case format for consistency.
    """

    # Core providers (must match TTSProvider enum values)
    COQUI_XTTS = "coqui_xtts"
    F5TTS = "f5tts"
    STYLETTS2 = "styletts2"
    MELOTTS = "melotts"
    OPENVOICE = "openvoice"
    MOSHI = "moshi"

    # Additional providers
    KOKORO = "kokoro"
    CHATTERBOX = "chatterbox"
    TTS_WEBUI = "tts_webui"
    FISH_SPEECH = "fish_speech"
    ZONOS = "zonos"
    CRAWL4AI = "crawl4ai"
    INDEXTTS = "indextts"
    VOXCPM = "voxcpm"
    GPT_SOVITS = "gpt_sovits"

    # TTS-WebUI models (2025-11-24)
    BARK = "bark"
    TORTOISE = "tortoise"
    MAHATTS = "mahatts"
    MMS = "mms"
    VALLE_X = "valle_x"

    @classmethod
    def all(cls) -> Set[str]:
        """
        Get all canonical provider IDs.

        Returns:
            Set of canonical provider IDs
        """
        return {
            value for key, value in cls.__dict__.items()
            if not key.startswith('_') and isinstance(value, str)
        }

    @classmethod
    def is_valid(cls, provider_id: str) -> bool:
        """
        Check if provider ID is valid canonical format.

        Args:
            provider_id: Provider ID to validate

        Returns:
            True if valid canonical ID, False otherwise
        """
        return provider_id in cls.all()


# Legacy provider ID mappings
# Maps old/inconsistent IDs to canonical IDs
LEGACY_PROVIDER_MAP: Dict[str, str] = {
    # Coqui XTTS variations
    "XTTS": ProviderID.COQUI_XTTS,
    "xtts": ProviderID.COQUI_XTTS,
    "Coqui-XTTS": ProviderID.COQUI_XTTS,
    "coqui-xtts": ProviderID.COQUI_XTTS,
    "CoquiXTTS": ProviderID.COQUI_XTTS,
    "coqui_xtts": ProviderID.COQUI_XTTS,

    # F5-TTS variations
    "F5-TTS": ProviderID.F5TTS,
    "f5-tts": ProviderID.F5TTS,
    "F5TTS": ProviderID.F5TTS,
    "f5_tts": ProviderID.F5TTS,

    # StyleTTS2 variations
    "StyleTTS2": ProviderID.STYLETTS2,
    "style-tts2": ProviderID.STYLETTS2,
    "StyleTTS-2": ProviderID.STYLETTS2,
    "style_tts2": ProviderID.STYLETTS2,

    # MeloTTS variations
    "Melo-TTS": ProviderID.MELOTTS,
    "melo-tts": ProviderID.MELOTTS,
    "MeloTTS": ProviderID.MELOTTS,
    "melo_tts": ProviderID.MELOTTS,

    # OpenVoice variations
    "Open-Voice": ProviderID.OPENVOICE,
    "OpenVoice": ProviderID.OPENVOICE,
    "open-voice": ProviderID.OPENVOICE,
    "open_voice": ProviderID.OPENVOICE,

    # Moshi variations
    "Moshi": ProviderID.MOSHI,
    "MOSHI": ProviderID.MOSHI,

    # Kokoro variations
    "Kokoro-TTS": ProviderID.KOKORO,
    "KokoroTTS": ProviderID.KOKORO,
    "kokoro-tts": ProviderID.KOKORO,

    # Chatterbox variations
    "Chatterbox": ProviderID.CHATTERBOX,
    "ChatterBox": ProviderID.CHATTERBOX,
    "chatterbox": ProviderID.CHATTERBOX,

    # TTS-WebUI variations
    "TTS-WebUI": ProviderID.TTS_WEBUI,
    "TTSWebUI": ProviderID.TTS_WEBUI,
    "tts-webui": ProviderID.TTS_WEBUI,
    "ttswebui": ProviderID.TTS_WEBUI,

    # Fish Speech variations
    "Fish-Speech": ProviderID.FISH_SPEECH,
    "FishSpeech": ProviderID.FISH_SPEECH,
    "fish-speech": ProviderID.FISH_SPEECH,
    "fishspeech": ProviderID.FISH_SPEECH,

    # Zonos variations
    "Zonos": ProviderID.ZONOS,
    "ZONOS": ProviderID.ZONOS,
    "zonos": ProviderID.ZONOS,

    # Crawl4AI variations
    "Crawl4AI": ProviderID.CRAWL4AI,
    "crawl-4ai": ProviderID.CRAWL4AI,
    "crawl4ai": ProviderID.CRAWL4AI,

    # IndexTTS variations
    "IndexTTS": ProviderID.INDEXTTS,
    "index-tts": ProviderID.INDEXTTS,
    "index_tts": ProviderID.INDEXTTS,

    # VoxCPM variations
    "VoxCPM": ProviderID.VOXCPM,
    "vox-cpm": ProviderID.VOXCPM,
    "vox_cpm": ProviderID.VOXCPM,

    # GPT-SoVITS variations
    "GPT-SoVITS": ProviderID.GPT_SOVITS,
    "GPTSoVITS": ProviderID.GPT_SOVITS,
    "gpt-sovits": ProviderID.GPT_SOVITS,
    "gptsovits": ProviderID.GPT_SOVITS,

    # Bark variations
    "Bark": ProviderID.BARK,
    "BARK": ProviderID.BARK,

    # Tortoise variations
    "Tortoise": ProviderID.TORTOISE,
    "TORTOISE": ProviderID.TORTOISE,
    "Tortoise-TTS": ProviderID.TORTOISE,
    "tortoise-tts": ProviderID.TORTOISE,

    # MahaTTS variations
    "MahaTTS": ProviderID.MAHATTS,
    "maha-tts": ProviderID.MAHATTS,
    "maha_tts": ProviderID.MAHATTS,

    # MMS variations
    "MMS": ProviderID.MMS,
    "Meta-MMS": ProviderID.MMS,
    "meta-mms": ProviderID.MMS,

    # VALL-E X variations
    "VALL-E X": ProviderID.VALLE_X,
    "VALLE_X": ProviderID.VALLE_X,
    "valle-x": ProviderID.VALLE_X,
    "vallex": ProviderID.VALLE_X,
}


def normalize_provider_id(provider_id: str) -> Optional[str]:
    """
    Normalize provider ID to canonical format.

    Args:
        provider_id: Provider ID (may be legacy format)

    Returns:
        Canonical provider ID if valid, None if unknown

    Examples:
        >>> normalize_provider_id("XTTS")
        'coqui_xtts'

        >>> normalize_provider_id("coqui_xtts")
        'coqui_xtts'

        >>> normalize_provider_id("unknown_provider")
        None
    """
    if not provider_id:
        return None

    # Check if already canonical
    if ProviderID.is_valid(provider_id):
        return provider_id

    # Check legacy mapping
    if provider_id in LEGACY_PROVIDER_MAP:
        return LEGACY_PROVIDER_MAP[provider_id]

    # Unknown provider ID
    return None


def get_legacy_ids(canonical_id: str) -> Set[str]:
    """
    Get all legacy IDs that map to a canonical ID.

    Args:
        canonical_id: Canonical provider ID

    Returns:
        Set of legacy IDs that map to this canonical ID

    Examples:
        >>> get_legacy_ids("coqui_xtts")
        {'XTTS', 'xtts', 'Coqui-XTTS', ...}
    """
    return {
        legacy_id for legacy_id, canonical in LEGACY_PROVIDER_MAP.items()
        if canonical == canonical_id
    }


def validate_provider_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize provider configuration.

    Ensures provider_id field uses canonical format.

    Args:
        config: Provider configuration dict

    Returns:
        Normalized configuration

    Raises:
        ValueError: If provider_id is invalid
    """
    if "provider_id" not in config:
        raise ValueError("Missing 'provider_id' field in configuration")

    provider_id = config["provider_id"]
    canonical_id = normalize_provider_id(provider_id)

    if not canonical_id:
        raise ValueError(
            f"Invalid provider_id: '{provider_id}'. "
            f"Valid IDs: {', '.join(sorted(ProviderID.all()))}"
        )

    # Update config with canonical ID
    config["provider_id"] = canonical_id

    return config


# Export canonical IDs for easy access
__all__ = [
    "ProviderID",
    "normalize_provider_id",
    "get_legacy_ids",
    "validate_provider_config",
    "LEGACY_PROVIDER_MAP",
]

"""
Simple Integration for Ghanaian Location Services

Provides one-line functions that can be easily integrated into premier_health.py
for testing and gradual adoption.
"""

import logging
from typing import Optional, Dict, Any
import asyncio
from functools import lru_cache

# Simple fallback corrections for immediate use
FALLBACK_CORRECTIONS = {
    "madena": "Madina",
    "zorwulu": "Dzorwulu",
    "dzolvulu": "Dzorwulu",
    "jorvulu": "Dzorwulu",
    "kanashi": "Kaneshie",
    "kaneshi": "Kaneshie",
    "adabaka": "Adabraka",
    "adbraka": "Adabraka",
    "kokolemle": "Kokomlemle",
    "kokomlemele": "Kokomlemle",
    "east legion": "East Legon",
    "accraw": "Accra",
    "akra": "Accra",
    "tema station": "Tema",
    "sakumono": "Sakumono Estate",
    "spintech": "Spintex",
    "ashaman": "Ashaiman",
    "haatso road": "Haatso",
    "ofankor": "Ofankor",
    "tantra hills": "Tantra Hill"
}

logger = logging.getLogger(__name__)

# Global cache for database service
_location_service = None
_service_initialized = False


def correct_location_simple(location_input: str) -> str:
    """
    Simple synchronous location correction using fallback dictionary

    Args:
        location_input: User location input (potentially misheard)

    Returns:
        Corrected location name

    Usage in premier_health.py:
        corrected_location = correct_location_simple(user_input)
    """
    if not location_input:
        return location_input

    return FALLBACK_CORRECTIONS.get(location_input.lower().strip(), location_input)


async def correct_location_async(location_input: str) -> Dict[str, Any]:
    """
    Async location correction using full database system with fallback

    Args:
        location_input: User location input (potentially misheard)

    Returns:
        Dict with correction details

    Usage in premier_health.py:
        result = await correct_location_async(user_input)
        corrected = result['corrected']
    """
    if not location_input:
        return {
            "original": location_input,
            "corrected": location_input,
            "confidence": 1.0,
            "source": "no_input"
        }

    try:
        # Try database-backed correction first
        result = await _get_database_correction(location_input)
        if result:
            return result

    except Exception as e:
        logger.warning(f"Database correction failed for '{location_input}': {e}")

    # Fallback to simple dictionary
    corrected = correct_location_simple(location_input)
    is_corrected = corrected.lower() != location_input.lower()

    return {
        "original": location_input,
        "corrected": corrected,
        "confidence": 0.9 if is_corrected else 1.0,
        "source": "fallback_dict" if is_corrected else "no_correction"
    }


async def _get_database_correction(location_input: str) -> Optional[Dict[str, Any]]:
    """Try to get correction from database system"""
    global _location_service, _service_initialized

    if not _service_initialized:
        try:
            await _initialize_location_service()
            _service_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize location service: {e}")
            return None

    if not _location_service:
        return None

    try:
        from ..integration_helpers import quick_healthcare_lookup
        from ...mongo import get_database

        db = get_database()
        result, _ = await quick_healthcare_lookup(db, location_input, "healthcare")

        if result.success and result.confidence > 0.6:
            return {
                "original": location_input,
                "corrected": result.corrected_location,
                "confidence": result.confidence,
                "source": "database",
                "alternatives": result.alternatives[:2] if result.alternatives else []
            }

    except Exception as e:
        logger.error(f"Database lookup failed for '{location_input}': {e}")

    return None


async def _initialize_location_service():
    """Initialize the location service with sample data"""
    global _location_service

    try:
        from ...mongo import get_database
        from .database.repositories import LocationRepository
        from .core_service import GhanaianLocationService

        db = get_database()
        repository = LocationRepository(db)
        _location_service = GhanaianLocationService(repository)

        # Try to initialize with existing data, or create sample data
        try:
            await _location_service.initialize()
        except Exception:
            # If initialization fails, create minimal sample data
            await _create_minimal_sample_data(repository)
            await _location_service.initialize()

        logger.info("✅ Location service initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize location service: {e}")
        _location_service = None
        raise


async def _create_minimal_sample_data(repository):
    """Create minimal sample data for immediate use"""
    try:
        from .database.models import GhanaianLocation, STTCorrection

        # Create sample locations
        sample_locations = [
            ("DZORWULU", "Dzorwulu", ["ZORWULU"]),
            ("MADINA", "Madina", ["MADINA TOWN"]),
            ("KANESHIE", "Kaneshie", ["KANESHIE MARKET"]),
            ("ADABRAKA", "Adabraka", []),
            ("EAST LEGON", "East Legon", ["EASTLEGON"])
        ]

        for canonical, display, aliases in sample_locations:
            try:
                location = GhanaianLocation(
                    canonical_name=canonical,
                    display_name=display,
                    aliases=aliases,
                    phonetic_codes={},
                    pronunciation={"difficulty_score": 0.5},
                    geographic={"region": "Greater Accra"},
                    context={"healthcare": {"provider_count": 5}}
                )
                await repository.create_location(location)
            except Exception:
                pass  # Location might already exist

        # Create sample STT corrections
        for misheard, correct in FALLBACK_CORRECTIONS.items():
            try:
                correction = STTCorrection(
                    misheard_input=misheard,
                    correct_location=correct.upper(),
                    confidence=0.8,
                    phonetic_similarity=0.7,
                    frequency=1,
                    verified=False,
                    source="sample_data"
                )
                await repository.create_stt_correction(correction)
            except Exception:
                pass  # Correction might already exist

        logger.info("✅ Created minimal sample data")

    except Exception as e:
        logger.warning(f"Failed to create sample data: {e}")


# Cached pronunciation guides for immediate use
@lru_cache(maxsize=100)
def get_pronunciation_guide(location: str) -> Dict[str, Any]:
    """
    Get pronunciation guide for a location (cached)

    Args:
        location: Location name

    Returns:
        Dict with pronunciation guidance

    Usage in premier_health.py:
        guide = get_pronunciation_guide(corrected_location)
        if guide['needs_slow_speech']:
            # Use slower TTS rate
    """
    guides = {
        "Dzorwulu": {
            "phonetic": "ZOR-wu-lu",
            "tip": "Say 'zor' like 'more' with Z, then 'wu-lu'",
            "speech_rate": 0.8,
            "needs_slow_speech": True,
            "difficulty": "high"
        },
        "Kokomlemle": {
            "phonetic": "KO-kom-lem-le",
            "tip": "Break into four parts: ko-kom-lem-le",
            "speech_rate": 0.8,
            "needs_slow_speech": True,
            "difficulty": "high"
        },
        "Kwabenya": {
            "phonetic": "KWA-ben-ya",
            "tip": "Say 'kwa' like 'quarter' without 'r-ter'",
            "speech_rate": 0.9,
            "needs_slow_speech": True,
            "difficulty": "medium"
        },
        "Nyamekye": {
            "phonetic": "NYA-me-kye",
            "tip": "Start with 'nya' like 'new ya'",
            "speech_rate": 0.85,
            "needs_slow_speech": True,
            "difficulty": "medium"
        },
        "Abelenkpe": {
            "phonetic": "A-bel-en-kpe",
            "tip": "Break into parts: a-bel-en-kpe",
            "speech_rate": 0.85,
            "needs_slow_speech": True,
            "difficulty": "medium"
        }
    }

    guide = guides.get(location, {
        "phonetic": location,
        "speech_rate": 1.0,
        "needs_slow_speech": False,
        "difficulty": "low",
        "tip": f"Pronounce as written: {location}"
    })

    guide["location"] = location
    return guide


def format_for_tts(text: str, slow_speech_locations: list = None) -> str:
    """
    Format text for TTS with pronunciation optimizations

    Args:
        text: Original text
        slow_speech_locations: List of locations that need slow speech

    Returns:
        TTS-optimized text

    Usage in premier_health.py:
        response = "Found providers in Dzorwulu"
        tts_response = format_for_tts(response, ["Dzorwulu"])
    """
    if not slow_speech_locations:
        return text

    # Simple SSML wrapper for slow speech
    optimized = text
    for location in slow_speech_locations:
        guide = get_pronunciation_guide(location)
        if guide.get('needs_slow_speech'):
            # Replace with slower speech markup
            phonetic = guide.get('phonetic', location)
            optimized = optimized.replace(
                location,
                f'<prosody rate="{guide.get("speech_rate", 0.9):.1f}">{phonetic}</prosody>'
            )

    return f"<speak>{optimized}</speak>" if any(guide.get('needs_slow_speech') for guide in [get_pronunciation_guide(loc) for loc in slow_speech_locations]) else text


# === ONE-LINE INTEGRATION FUNCTIONS ===

def fix_location(location_input: str) -> str:
    """ONE-LINE: Simple location correction - can be commented out easily"""
    return correct_location_simple(location_input)


async def fix_location_async(location_input: str) -> str:
    """ONE-LINE: Async location correction - can be commented out easily"""
    result = await correct_location_async(location_input)
    return result['corrected']


def make_pronounceable(text: str, location: str) -> str:
    """ONE-LINE: Make response pronounceable - can be commented out easily"""
    guide = get_pronunciation_guide(location)
    return format_for_tts(text, [location] if guide.get('needs_slow_speech') else [])


# === INTEGRATION EXAMPLES ===
"""
Example integration in premier_health.py:

# 1. Simple correction (sync)
def search_providers(location_input: str):
    # corrected_location = fix_location(location_input)  # <- ONE LINE
    corrected_location = location_input  # Remove this line after testing

    # Your existing provider search logic...
    providers = search_database(corrected_location)
    return providers

# 2. Async correction with confidence
async def search_providers_async(location_input: str):
    # corrected_location = await fix_location_async(location_input)  # <- ONE LINE
    corrected_location = location_input  # Remove this line after testing

    # Your existing provider search logic...
    providers = await search_database_async(corrected_location)
    return providers

# 3. TTS optimization
def format_response(text: str, location: str):
    # tts_text = make_pronounceable(text, location)  # <- ONE LINE
    tts_text = text  # Remove this line after testing
    return tts_text
"""
"""
Constants and configuration for the voice engine module.
"""

from pathlib import Path
from typing import List, Set
try:
    import yaml
except ImportError:
    yaml = None
import logging

# Lazy import to avoid dependency issues
def _get_system_config():
    """Lazy import for system config."""
    try:
        from apps.shared.config.models import SystemConfig
        return SystemConfig
    except ImportError:
        return None

logger = logging.getLogger(__name__)

# Configuration
CONFIG_PATH = Path(__file__).resolve().parents[5] / "shared" / "config" / "system.yaml"

try:
    SystemConfig = _get_system_config()
    if SystemConfig and yaml and CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            _cfg = SystemConfig(**yaml.safe_load(f))
            LANGUAGE_DETECT_THRESHOLD = _cfg.language_detect_threshold
    else:
        LANGUAGE_DETECT_THRESHOLD = 0.5
except Exception as e:
    logger.warning(f"Could not load system config: {e}")
    LANGUAGE_DETECT_THRESHOLD = 0.5

# Available voices for African and emerging market languages
AVAILABLE_VOICES: Set[str] = {
    "akuapem_female",
    "asante_male", 
    "asante_female",
    "ewe_female",
    "ewe_male",
    "ga_male",
    "ga_female",
    "hausa_male",
    "hausa_female",
    "dagbani_male",
    "dagbani_female",
    "yoruba_male",
    "yoruba_female",
    "igbo_male",
    "igbo_female",
    "swahili_male",
    "swahili_female",
    "kikuyu_male",
    "kikuyu_female",
    "luo_male",
    "luo_female",
    "zulu_male",
    "zulu_female",
    "xhosa_male",
    "xhosa_female",
    "afrikaans_male",
    "afrikaans_female",
}

# Supported languages and countries
LANGUAGES: List[str] = [
    "English", "Twi", "Asante Twi", "Akuapem Twi", "Ewe", "Ga", "Dagbani", 
    "Hausa", "Yoruba", "Igbo", "Swahili"
]

COUNTRIES: List[str] = ["Ghana", "Kenya"]

# Global session state (TODO: Replace with proper session management)
CURRENT_LANGUAGE = "en"
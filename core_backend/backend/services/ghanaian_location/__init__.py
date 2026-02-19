"""
Ghanaian Location Services Module

Comprehensive STT correction, phonetic matching, and TTS optimization
for Ghanaian location names in healthcare and voice applications.

Main Components:
- GhanaianLocationService: Main orchestrator service
- PhoneticMatcher: Multi-algorithm phonetic matching with fuzzy search
- PronunciationService: TTS optimization with SSML generation
- Adapters: Tool-specific behavior customization

Usage:
    from backend.services.ghanaian_location import (
        create_location_service,
        quick_location_lookup
    )

    # For premier health integration
    service, adapter = create_location_service(db, 'premier_health')
    result = await adapter.process_location("dzorwulu hospital")

    # Quick lookup
    result = await quick_location_lookup(db, "madina", 'vapi')
"""

from .database.models import (
    GhanaianLocation,
    STTCorrection,
    PronunciationGuide,
    LocationRelationship,
    UserCorrection,
    LocationAnalytics,
    LocationResult,
    ToolContext,
    LanguageContext,
    RelationshipType
)

from .database.repositories import LocationRepository
from .phonetic_matcher import PhoneticMatcher, PhoneticMatch
from .pronunciation_service import PronunciationService, PronunciationResult
from .core_service import GhanaianLocationService

# Import adapters
from .adapters import (
    BaseLocationAdapter,
    PremierHealthAdapter,
    VapiAdapter,
    GeneralAdapter
)

__version__ = "1.0.0"
__author__ = "KasaAI Team"

__all__ = [
    # Core service
    'GhanaianLocationService',

    # Database models
    'GhanaianLocation',
    'STTCorrection',
    'PronunciationGuide',
    'LocationRelationship',
    'UserCorrection',
    'LocationAnalytics',
    'LocationResult',

    # Enums
    'ToolContext',
    'LanguageContext',
    'RelationshipType',

    # Service components
    'LocationRepository',
    'PhoneticMatcher',
    'PhoneticMatch',
    'PronunciationService',
    'PronunciationResult',

    # Adapters
    'BaseLocationAdapter',
    'PremierHealthAdapter',
    'VapiAdapter',
    'GeneralAdapter',

    # Factory functions
    'create_location_service',
    'quick_location_lookup'
]


def create_location_service(database_connection, adapter_type: str = 'general'):
    """
    Factory function to create a configured location service with adapter

    Args:
        database_connection: MongoDB database connection
        adapter_type: Type of adapter ('premier_health', 'vapi', 'general')

    Returns:
        Tuple of (GhanaianLocationService, Adapter)
    """
    repository = LocationRepository(database_connection)
    core_service = GhanaianLocationService(repository)

    # Create appropriate adapter
    adapters = {
        'premier_health': PremierHealthAdapter,
        'vapi': VapiAdapter,
        'general': GeneralAdapter
    }

    adapter_class = adapters.get(adapter_type, GeneralAdapter)
    adapter = adapter_class(core_service)

    return core_service, adapter


async def quick_location_lookup(database_connection, query: str, context: str = 'general'):
    """
    Quick helper function for simple location lookups

    Args:
        database_connection: MongoDB database connection
        query: Location query text
        context: Context type ('premier_health', 'vapi', 'general')

    Returns:
        LocationResult with best match
    """
    core_service, adapter = create_location_service(database_connection, context)
    await core_service.initialize()

    result = await adapter.process_location(query)
    return result
"""
Integration helpers for Ghanaian Location Services

Provides easy integration functions for existing services like premier_health.py
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .database.models import LocationResult, ToolContext
from . import create_location_service, quick_location_lookup

logger = logging.getLogger(__name__)


class PremierHealthLocationHelper:
    """
    Helper class for integrating Ghanaian Location Services with Premier Health
    """

    def __init__(self, database_connection):
        """
        Initialize the helper with database connection

        Args:
            database_connection: MongoDB database connection
        """
        self.db = database_connection
        self.service = None
        self.adapter = None

    async def initialize(self):
        """Initialize the location service"""
        if not self.service:
            self.service, self.adapter = create_location_service(self.db, 'premier_health')
            await self.service.initialize()

    async def process_healthcare_location(self,
                                        location_query: str,
                                        provider_type: Optional[str] = None,
                                        specialty: Optional[str] = None,
                                        urgency: str = 'routine') -> LocationResult:
        """
        Process location query for healthcare provider search

        Args:
            location_query: User's location input (potentially misheard)
            provider_type: Type of provider (doctor, clinic, etc.)
            specialty: Medical specialty
            urgency: Urgency level (emergency, urgent, routine)

        Returns:
            LocationResult with healthcare-optimized matching
        """
        await self.initialize()

        healthcare_context = {
            'provider_type': provider_type,
            'specialty': specialty,
            'urgency': urgency
        }

        result = await self.adapter.process_location(location_query, healthcare_context)

        # Log successful matches for analytics
        if result.success:
            logger.info(
                f"🏥 Healthcare location matched: '{location_query}' -> '{result.corrected_location}' "
                f"(confidence: {result.confidence:.2f})"
            )

        return result

    async def optimize_healthcare_response(self,
                                         response_text: str,
                                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Optimize response text for healthcare TTS

        Args:
            response_text: Original response text
            context: Healthcare context

        Returns:
            TTS-optimized response text
        """
        await self.initialize()

        optimized = await self.adapter.optimize_response_text(response_text, context)

        return optimized

    async def format_provider_response(self,
                                     location_result: LocationResult,
                                     providers: List[Dict[str, Any]],
                                     search_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a complete healthcare provider response

        Args:
            location_result: Location matching result
            providers: List of provider data
            search_context: Search context (specialty, provider type, etc.)

        Returns:
            Formatted healthcare response
        """
        await self.initialize()

        if not location_result.success:
            return f"I couldn't find healthcare providers for '{location_result.original_input}'. " \
                   f"Could you please specify the location more clearly?"

        response_parts = []

        # Location confirmation
        if location_result.confidence >= 0.8:
            response_parts.append(f"I found {len(providers)} healthcare providers in {location_result.corrected_location}.")
        else:
            response_parts.append(f"I found {len(providers)} providers in what I think you meant: {location_result.corrected_location}.")

        # Add provider details
        if providers:
            provider_count = len(providers)
            if search_context and search_context.get('specialty'):
                specialty = search_context['specialty']
                response_parts.append(f"This includes providers specializing in {specialty}.")

            # Add availability info if present
            if search_context and search_context.get('availability'):
                response_parts.append(f"Availability: {search_context['availability']}")

        # Handle low confidence with alternatives
        if location_result.confidence < 0.7 and location_result.alternatives:
            alt = location_result.alternatives[0]
            response_parts.append(f"If you meant {alt}, I can search there too.")

        response_text = " ".join(response_parts)

        # Optimize for TTS
        optimized_response = await self.optimize_healthcare_response(response_text, search_context)

        return optimized_response

    async def learn_from_user_feedback(self,
                                     original_query: str,
                                     system_interpretation: str,
                                     user_correction: str,
                                     session_id: Optional[str] = None) -> bool:
        """
        Learn from user feedback to improve future matches

        Args:
            original_query: What user originally said/typed
            system_interpretation: What system thought it was
            user_correction: What user said it should be
            session_id: Session identifier

        Returns:
            True if learning was successful
        """
        await self.initialize()

        success = await self.service.learn_from_user_correction(
            original_query=original_query,
            system_interpretation=system_interpretation,
            user_correction=user_correction,
            confidence_before=0.5,  # Assume low confidence if user corrected
            context=ToolContext.PREMIER_HEALTH,
            session_id=session_id
        )

        if success:
            logger.info(f"🧠 Learned from healthcare feedback: '{original_query}' -> '{user_correction}'")

        return success


async def quick_healthcare_lookup(database_connection,
                                location_query: str,
                                provider_type: Optional[str] = None,
                                specialty: Optional[str] = None) -> Tuple[LocationResult, str]:
    """
    Quick healthcare location lookup with formatted response

    Args:
        database_connection: MongoDB database connection
        location_query: Location query from user
        provider_type: Optional provider type
        specialty: Optional specialty

    Returns:
        Tuple of (LocationResult, formatted_response)
    """
    try:
        result = await quick_location_lookup(database_connection, location_query, 'premier_health')

        if result.success:
            response_parts = []

            # Base response
            if result.confidence >= 0.8:
                response_parts.append(f"Found healthcare providers in {result.corrected_location}.")
            else:
                response_parts.append(f"Found providers in {result.corrected_location} (did you mean this area?).")

            # Add context if provided
            if provider_type or specialty:
                context_parts = []
                if provider_type:
                    context_parts.append(f"{provider_type}s")
                if specialty:
                    context_parts.append(f"{specialty} specialists")

                if context_parts:
                    response_parts.append(f"Looking for {' and '.join(context_parts)} in this area.")

            response = " ".join(response_parts)
        else:
            response = f"I couldn't find healthcare providers for '{location_query}'. Could you please specify the location more clearly?"

        return result, response

    except Exception as e:
        logger.error(f"Quick healthcare lookup failed for '{location_query}': {e}")
        error_result = LocationResult(
            original_input=location_query,
            confidence=0.0,
            success=False,
            error_message=str(e)
        )
        error_response = f"I had trouble processing '{location_query}'. Please try again."
        return error_result, error_response


def get_location_pronunciation_guide(location_name: str) -> Dict[str, Any]:
    """
    Get pronunciation guidance for a specific location

    Args:
        location_name: Location name to get guidance for

    Returns:
        Dictionary with pronunciation information
    """
    # Common pronunciation guides for difficult Ghanaian locations
    pronunciation_guides = {
        'DZORWULU': {
            'phonetic': 'ZOR-wu-lu',
            'difficulty': 'high',
            'tips': 'Say "zor" like "more" with a Z, then "wu-lu"',
            'ssml': '<phoneme alphabet="ipa" ph="d͡zoɾwulu">Dzorwulu</phoneme>',
            'alternatives': ['the Dzorwulu area', 'near Roman Ridge']
        },
        'KOKOMLEMLE': {
            'phonetic': 'KO-kom-lem-le',
            'difficulty': 'high',
            'tips': 'Break it into four parts: "ko-kom-lem-le"',
            'ssml': '<phoneme alphabet="ipa" ph="kokomlɛmle">Kokomlemle</phoneme>',
            'alternatives': ['the Kokomlemle area', 'near Achimota']
        },
        'NYAMEKYE': {
            'phonetic': 'NYA-me-kye',
            'difficulty': 'medium',
            'tips': 'Start with "nya" like "new ya", then "me-kye"',
            'ssml': '<phoneme alphabet="ipa" ph="njamɛkje">Nyamekye</phoneme>',
            'alternatives': ['the Nyamekye area', 'near Lapaz']
        },
        'KWABENYA': {
            'phonetic': 'KWA-ben-ya',
            'difficulty': 'medium',
            'tips': 'Say "kwa" like "quarter" without the "r-ter", then "ben-ya"',
            'alternatives': ['the Kwabenya area', 'near Dome']
        }
    }

    location_upper = location_name.upper()
    guide = pronunciation_guides.get(location_upper)

    if guide:
        return {
            'location': location_name,
            'has_guide': True,
            **guide
        }
    else:
        return {
            'location': location_name,
            'has_guide': False,
            'phonetic': location_name.title(),
            'difficulty': 'low',
            'tips': f'Pronounce as written: {location_name.title()}'
        }
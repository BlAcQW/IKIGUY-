"""
VAPI (Voice AI) specific adapter for location processing

Optimizes location processing for voice interactions with
emphasis on TTS clarity and conversational responses.
"""

import re
from typing import Dict, Any, List, Optional
import logging

from ..database.models import LocationResult, ToolContext, LanguageContext
from .base_adapter import BaseLocationAdapter

logger = logging.getLogger(__name__)


class VapiAdapter(BaseLocationAdapter):
    """
    VAPI-specific location processing adapter

    Provides voice-optimized customizations:
    - Enhanced pronunciation guides for TTS
    - Conversational response formatting
    - Voice-friendly alternative suggestions
    - Phonetic spelling integration
    """

    def get_tool_context(self) -> ToolContext:
        """Get tool context for VAPI"""
        return ToolContext.VAPI

    async def preprocess_query(self,
                             query: str,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocess voice input for location matching

        Args:
            query: Voice-transcribed location query
            context: VAPI conversation context

        Returns:
            Preprocessed query optimized for voice input
        """
        processed_query = query.strip()

        # Handle common voice transcription errors
        voice_corrections = {
            # Common STT mishearings for Ghanaian locations
            r'\baccra central\b': 'ACCRA CENTRAL',
            r'\baccra centrum\b': 'ACCRA CENTRAL',
            r'\bakra central\b': 'ACCRA CENTRAL',

            r'\bmadina\b': 'MADINA',
            r'\bmadena\b': 'MADINA',
            r'\bmadina town\b': 'MADINA',

            r'\bkaneshie\b': 'KANESHIE',
            r'\bkanashi\b': 'KANESHIE',
            r'\bkaneshi\b': 'KANESHIE',

            r'\badabraka\b': 'ADABRAKA',
            r'\badabaka\b': 'ADABRAKA',
            r'\badbraka\b': 'ADABRAKA',

            r'\bdzorwulu\b': 'DZORWULU',
            r'\bzorwulu\b': 'DZORWULU',
            r'\bjorvulu\b': 'DZORWULU',

            r'\bkokomlemle\b': 'KOKOMLEMLE',
            r'\bkokomlemele\b': 'KOKOMLEMLE',
            r'\bkokolemle\b': 'KOKOMLEMLE',
        }

        for pattern, correction in voice_corrections.items():
            processed_query = re.sub(pattern, correction, processed_query, flags=re.IGNORECASE)

        # Remove conversational filler words that might interfere with matching
        filler_words = [
            r'\b(um|uh|er|ah)\s+',
            r'\b(you know|like|basically|actually)\s+',
            r'\b(please|can you|could you)\s+',
            r'\b(find|locate|search for|look for)\s+',
            r'\b(in the area of|near|around)\s+',
        ]

        for filler_pattern in filler_words:
            processed_query = re.sub(filler_pattern, '', processed_query, flags=re.IGNORECASE).strip()

        # Handle voice-specific location references
        voice_location_patterns = {
            r'\bthat place called\s+': '',
            r'\bthe area they call\s+': '',
            r'\bsomewhere called\s+': '',
            r'\bin that\s+(.+)\s+area\b': r'\1',
        }

        for pattern, replacement in voice_location_patterns.items():
            processed_query = re.sub(pattern, replacement, processed_query, flags=re.IGNORECASE).strip()

        logger.debug(f"🎙️ Voice query preprocessed: '{query}' -> '{processed_query}'")
        return processed_query

    async def postprocess_result(self,
                               result: LocationResult,
                               context: Optional[Dict[str, Any]] = None) -> LocationResult:
        """
        Postprocess results for voice interaction

        Args:
            result: Original location result
            context: VAPI conversation context

        Returns:
            Voice-optimized location result
        """
        if not result.success:
            # Enhance error messages for voice
            voice_friendly_error = self._create_voice_friendly_error_message(
                result.original_input, result.error_message
            )
            result.error_message = voice_friendly_error

        return result

    async def preprocess_response_text(self,
                                     text: str,
                                     context: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocess response text for voice synthesis

        Args:
            text: Original response text
            context: VAPI context

        Returns:
            Voice-optimized response text
        """
        processed_text = text

        # Make responses more conversational
        formal_to_conversational = {
            r'\bI have found\b': 'I found',
            r'\bI have located\b': 'I found',
            r'\bThere are available\b': 'There are',
            r'\bPlease note that\b': 'Just so you know,',
            r'\bIt should be noted\b': 'Note that',
        }

        for formal, conversational in formal_to_conversational.items():
            processed_text = re.sub(formal, conversational, processed_text, flags=re.IGNORECASE)

        # Add natural pauses for better voice flow
        processed_text = re.sub(r'([.!?])\s+', r'\1 <break time="0.5s"/> ', processed_text)
        processed_text = re.sub(r'([,:;])\s+', r'\1 <break time="0.3s"/> ', processed_text)

        return processed_text

    async def postprocess_response_text(self,
                                      text: str,
                                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Final voice optimization of response text

        Args:
            text: TTS-optimized text
            context: VAPI context

        Returns:
            Final voice-ready text
        """
        processed_text = text

        # Add emphasis to important location names
        location_emphasis_patterns = [
            (r'\b(ACCRA CENTRAL|MADINA|KANESHIE|ADABRAKA|DZORWULU|KOKOMLEMLE)\b',
             r'<emphasis level="moderate">\1</emphasis>'),
        ]

        for pattern, replacement in location_emphasis_patterns.items():
            processed_text = re.sub(pattern, replacement, processed_text)

        # Ensure proper pacing for difficult names
        difficult_names = [
            'DZORWULU', 'KOKOMLEMLE', 'NYAMEKYE', 'ABELENKPE', 'KWABENYA'
        ]

        for name in difficult_names:
            if name in processed_text:
                # Add slower speech rate for difficult names
                processed_text = processed_text.replace(
                    name,
                    f'<prosody rate="0.8">{name}</prosody>'
                )

        return processed_text

    def should_include_pronunciation(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Always include pronunciation for voice applications

        Args:
            context: VAPI context

        Returns:
            True (always include pronunciation for voice)
        """
        return True

    def get_max_alternatives(self, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Limit alternatives for voice to avoid overwhelming users

        Args:
            context: VAPI context

        Returns:
            Maximum number of alternatives (2 for voice)
        """
        return 2  # Fewer alternatives for voice to avoid confusion

    def get_confidence_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Use moderate confidence threshold for voice

        Args:
            context: VAPI context

        Returns:
            Confidence threshold optimized for voice interaction
        """
        return 0.65  # Slightly higher than general use for voice clarity

    async def create_voice_confirmation_prompt(self,
                                             result: LocationResult) -> str:
        """
        Create a natural voice confirmation for location matches

        Args:
            result: Location matching result

        Returns:
            Natural voice confirmation text
        """
        if not result.success:
            return f"I couldn't find a location matching '{result.original_input}'. " \
                   f"Could you please say the area name again?"

        confirmation_parts = []

        # Confidence-based confirmation
        if result.confidence >= 0.9:
            confirmation_parts.append(f"I found {result.corrected_location}.")
        elif result.confidence >= 0.7:
            confirmation_parts.append(f"I think you mean {result.corrected_location}.")
        else:
            confirmation_parts.append(f"Did you mean {result.corrected_location}?")

        # Add alternatives for low confidence
        if result.confidence < 0.8 and result.alternatives:
            first_alt = result.alternatives[0] if result.alternatives else None
            if first_alt:
                confirmation_parts.append(f"Or perhaps {first_alt}?")

        return " ".join(confirmation_parts)

    async def create_location_suggestion_prompt(self,
                                              original_query: str,
                                              alternatives: List[str]) -> str:
        """
        Create natural voice suggestions when no exact match is found

        Args:
            original_query: Original user query
            alternatives: List of alternative location suggestions

        Returns:
            Natural voice suggestion text
        """
        if not alternatives:
            return f"I couldn't find '{original_query}'. Could you try saying it differently " \
                   f"or mention a nearby landmark?"

        suggestion_parts = [f"I couldn't find an exact match for '{original_query}'."]

        if len(alternatives) == 1:
            suggestion_parts.append(f"Did you mean {alternatives[0]}?")
        else:
            first_two = alternatives[:2]
            suggestion_parts.append(f"Did you mean {first_two[0]} or {first_two[1]}?")

        return " ".join(suggestion_parts)

    def _create_voice_friendly_error_message(self,
                                           original_input: str,
                                           error_message: Optional[str]) -> str:
        """
        Convert technical error messages to voice-friendly ones

        Args:
            original_input: User's original input
            error_message: Technical error message

        Returns:
            Voice-friendly error message
        """
        if not error_message:
            return f"I had trouble understanding '{original_input}'. " \
                   f"Could you please say it again more clearly?"

        # Convert technical errors to friendly voice messages
        voice_friendly_errors = {
            'No matching location found': f"I couldn't find a location called '{original_input}'. "
                                        f"Could you try saying it differently?",
            'Empty query provided': "I didn't catch that. Could you please tell me the location?",
            'Processing error': f"I had trouble processing '{original_input}'. "
                              f"Could you please try again?",
        }

        for technical, friendly in voice_friendly_errors.items():
            if technical in error_message:
                return friendly

        return f"I had trouble with '{original_input}'. Could you please try again?"

    async def format_voice_location_response(self,
                                           result: LocationResult,
                                           include_alternatives: bool = True) -> str:
        """
        Format a complete voice response for location queries

        Args:
            result: Location processing result
            include_alternatives: Whether to include alternative suggestions

        Returns:
            Complete voice-ready response
        """
        if not result.success:
            return self._create_voice_friendly_error_message(
                result.original_input, result.error_message
            )

        response_parts = []

        # Main confirmation
        confirmation = await self.create_voice_confirmation_prompt(result)
        response_parts.append(confirmation)

        # Geographic context if available
        if result.geographic_context:
            response_parts.append(f"That's in the {result.geographic_context} region.")

        # Include alternatives only if confidence is low and requested
        if (include_alternatives and
            result.confidence < 0.8 and
            result.alternatives and
            result.confidence >= 0.6):
            alt_text = await self.create_location_suggestion_prompt(
                result.original_input, result.alternatives
            )
            response_parts.append(alt_text)

        return " ".join(response_parts)
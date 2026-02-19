"""
General purpose adapter for location processing

Provides standard location processing behavior without
tool-specific customizations. Suitable for general use cases.
"""

from typing import Dict, Any, Optional
import logging

from ..database.models import LocationResult, ToolContext, LanguageContext
from .base_adapter import BaseLocationAdapter

logger = logging.getLogger(__name__)


class GeneralAdapter(BaseLocationAdapter):
    """
    General purpose location processing adapter

    Provides standard behavior without tool-specific customizations.
    Suitable for:
    - API endpoints requiring location processing
    - General location lookup services
    - Testing and development
    - Integration with new tools
    """

    def get_tool_context(self) -> ToolContext:
        """Get tool context for general use"""
        return ToolContext.GENERAL

    async def preprocess_query(self,
                             query: str,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Basic query preprocessing

        Args:
            query: Original location query
            context: General context (unused)

        Returns:
            Lightly preprocessed query
        """
        # Basic cleaning only
        processed_query = query.strip()

        # Remove excessive whitespace
        processed_query = ' '.join(processed_query.split())

        # Convert to uppercase for consistency (matches database format)
        processed_query = processed_query.upper()

        logger.debug(f"📍 General query preprocessed: '{query}' -> '{processed_query}'")
        return processed_query

    async def postprocess_result(self,
                               result: LocationResult,
                               context: Optional[Dict[str, Any]] = None) -> LocationResult:
        """
        Standard result postprocessing

        Args:
            result: Original location result
            context: General context (unused)

        Returns:
            Unmodified result (standard behavior)
        """
        # No modifications for general use
        return result

    async def preprocess_response_text(self,
                                     text: str,
                                     context: Optional[Dict[str, Any]] = None) -> str:
        """
        Basic response text preprocessing

        Args:
            text: Original response text
            context: General context (unused)

        Returns:
            Lightly preprocessed text
        """
        # Basic text cleaning only
        processed_text = text.strip()

        # Normalize excessive whitespace
        processed_text = ' '.join(processed_text.split())

        return processed_text

    async def postprocess_response_text(self,
                                      text: str,
                                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Basic response text postprocessing

        Args:
            text: TTS-optimized text
            context: General context (unused)

        Returns:
            Unmodified text (standard behavior)
        """
        # No modifications for general use
        return text

    def get_language_preference(self, context: Optional[Dict[str, Any]] = None) -> LanguageContext:
        """
        Get default language preference

        Args:
            context: May contain language preference

        Returns:
            Language context (English by default)
        """
        # Check if language is specified in context
        if context and 'language' in context:
            try:
                return LanguageContext(context['language'])
            except ValueError:
                # Invalid language, use default
                pass

        return LanguageContext.ENGLISH

    def should_include_pronunciation(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if pronunciation should be included

        Args:
            context: May contain pronunciation preference

        Returns:
            True if pronunciation requested, False by default
        """
        # Check if pronunciation is explicitly requested
        if context:
            return context.get('include_pronunciation', True)

        return True  # Include by default for general use

    def get_max_alternatives(self, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Get maximum number of alternatives

        Args:
            context: May contain max_alternatives preference

        Returns:
            Maximum alternatives (3 by default)
        """
        if context and 'max_alternatives' in context:
            try:
                max_alts = int(context['max_alternatives'])
                return max(0, min(max_alts, 10))  # Clamp between 0 and 10
            except (ValueError, TypeError):
                # Invalid value, use default
                pass

        return 3

    def get_confidence_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Get confidence threshold

        Args:
            context: May contain confidence_threshold preference

        Returns:
            Confidence threshold (0.6 by default)
        """
        if context and 'confidence_threshold' in context:
            try:
                threshold = float(context['confidence_threshold'])
                return max(0.0, min(threshold, 1.0))  # Clamp between 0.0 and 1.0
            except (ValueError, TypeError):
                # Invalid value, use default
                pass

        return 0.6

    async def create_standard_response(self,
                                     result: LocationResult,
                                     include_confidence: bool = False) -> str:
        """
        Create a standard formatted response for location queries

        Args:
            result: Location processing result
            include_confidence: Whether to include confidence score

        Returns:
            Standard formatted response
        """
        if not result.success:
            return f"Location '{result.original_input}' not found. " \
                   f"{result.error_message or 'Please try a different location.'}"

        response_parts = []

        # Main result
        if result.corrected_location != result.original_input:
            response_parts.append(
                f"Location '{result.original_input}' matched to '{result.corrected_location}'"
            )
        else:
            response_parts.append(f"Location '{result.corrected_location}' found")

        # Confidence if requested
        if include_confidence:
            confidence_pct = int(result.confidence * 100)
            response_parts.append(f"(confidence: {confidence_pct}%)")

        # Geographic context
        if result.geographic_context:
            response_parts.append(f"in {result.geographic_context}")

        # Alternatives for low confidence
        if result.confidence < 0.8 and result.alternatives:
            alt_list = ", ".join(result.alternatives[:2])
            response_parts.append(f"Other possible matches: {alt_list}")

        return ". ".join(response_parts) + "."

    async def create_api_response(self,
                                result: LocationResult,
                                include_metadata: bool = True) -> Dict[str, Any]:
        """
        Create a structured API response for location queries

        Args:
            result: Location processing result
            include_metadata: Whether to include additional metadata

        Returns:
            Structured API response dictionary
        """
        api_response = {
            'success': result.success,
            'original_input': result.original_input,
        }

        if result.success:
            api_response.update({
                'corrected_location': result.corrected_location,
                'confidence': result.confidence,
                'alternatives': result.alternatives,
            })

            if include_metadata:
                api_response.update({
                    'geographic_context': result.geographic_context,
                    'pronunciation_guide': result.pronunciation_guide,
                })
        else:
            api_response['error'] = result.error_message

        return api_response
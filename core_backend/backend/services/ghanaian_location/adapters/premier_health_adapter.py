"""
Premier Health specific adapter for location processing

Customizes location processing behavior for healthcare provider
searches and medical appointment scheduling.
"""

import re
from typing import Dict, Any, List, Optional
import logging

from ..database.models import LocationResult, ToolContext, LanguageContext
from .base_adapter import BaseLocationAdapter

logger = logging.getLogger(__name__)


class PremierHealthAdapter(BaseLocationAdapter):
    """
    Premier Health specific location processing adapter

    Provides healthcare-focused customizations:
    - Medical terminology preprocessing
    - Healthcare-specific pronunciation guides
    - Provider availability context
    - Appointment scheduling optimizations
    """

    def get_tool_context(self) -> ToolContext:
        """Get tool context for Premier Health"""
        return ToolContext.PREMIER_HEALTH

    async def preprocess_query(self,
                             query: str,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocess healthcare-related location queries

        Args:
            query: Original location query
            context: Healthcare-specific context

        Returns:
            Preprocessed query optimized for medical use
        """
        # Normalize healthcare-related terms
        processed_query = query.strip()

        # Remove common healthcare prefixes that might interfere with location matching
        healthcare_prefixes = [
            r'\b(find|locate|search)\s+(for\s+)?(doctors?|physicians?|providers?)\s+(in|at|near)\s+',
            r'\b(medical|health)\s+(facilities?|centers?|clinics?)\s+(in|at|near)\s+',
            r'\b(hospitals?|clinics?)\s+(in|at|near)\s+',
            r'\b(dentists?|specialists?)\s+(in|at|near)\s+',
            r'\b(appointment|booking)\s+(in|at|near)\s+',
        ]

        for prefix_pattern in healthcare_prefixes:
            processed_query = re.sub(prefix_pattern, '', processed_query, flags=re.IGNORECASE).strip()

        # Remove common healthcare suffixes
        healthcare_suffixes = [
            r'\s+(hospital|clinic|medical center|health center)$',
            r'\s+(area|region|zone)$',
        ]

        for suffix_pattern in healthcare_suffixes:
            processed_query = re.sub(suffix_pattern, '', processed_query, flags=re.IGNORECASE).strip()

        # Handle common medical area references
        medical_area_mappings = {
            r'\baccra\s+central\b': 'ACCRA CENTRAL',
            r'\bmadina\s+(town|area)?\b': 'MADINA',
            r'\bkaneshie\s+(market|area)?\b': 'KANESHIE',
            r'\badabraka\s+(area|zone)?\b': 'ADABRAKA',
            r'\bosu\s+(area|zone)?\b': 'OSU',
        }

        for pattern, replacement in medical_area_mappings.items():
            processed_query = re.sub(pattern, replacement, processed_query, flags=re.IGNORECASE)

        logger.debug(f"🏥 Healthcare query preprocessed: '{query}' -> '{processed_query}'")
        return processed_query

    async def postprocess_result(self,
                               result: LocationResult,
                               context: Optional[Dict[str, Any]] = None) -> LocationResult:
        """
        Postprocess results with healthcare-specific enhancements

        Args:
            result: Original location result
            context: Healthcare context (provider type, specialty, etc.)

        Returns:
            Enhanced result with healthcare metadata
        """
        if not result.success:
            return result

        # Add healthcare-specific context
        provider_type = self.extract_context_value(context, 'provider_type')
        specialty = self.extract_context_value(context, 'specialty')
        appointment_urgency = self.extract_context_value(context, 'urgency', 'routine')

        # Enhance geographic context with healthcare information
        enhanced_context = result.geographic_context or ""
        if provider_type:
            enhanced_context = f"{enhanced_context}, {provider_type} providers available"
        if specialty:
            enhanced_context = f"{enhanced_context}, {specialty} specialists in area"

        # Customize alternatives for healthcare context
        enhanced_alternatives = []
        for alt in result.alternatives:
            # Add healthcare context to alternatives
            healthcare_alt = f"{alt} medical area"
            enhanced_alternatives.append(healthcare_alt)

        # Create enhanced result
        enhanced_result = LocationResult(
            original_input=result.original_input,
            corrected_location=result.corrected_location,
            confidence=result.confidence,
            alternatives=enhanced_alternatives[:3],  # Limit to top 3
            pronunciation_guide=result.pronunciation_guide,
            geographic_context=enhanced_context.strip(", "),
            success=result.success,
            error_message=result.error_message
        )

        logger.debug(f"🏥 Healthcare result enhanced: {result.corrected_location}")
        return enhanced_result

    async def preprocess_response_text(self,
                                     text: str,
                                     context: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocess healthcare response text for better TTS

        Args:
            text: Original response text
            context: Healthcare context

        Returns:
            Preprocessed text optimized for medical responses
        """
        processed_text = text

        # Replace medical abbreviations with full words for better pronunciation
        medical_abbreviations = {
            r'\bDr\.?\s+': 'Doctor ',
            r'\bMD\b': 'Medical Doctor',
            r'\bGP\b': 'General Practitioner',
            r'\bER\b': 'Emergency Room',
            r'\bICU\b': 'Intensive Care Unit',
            r'\bOPD\b': 'Out-Patient Department',
        }

        for abbrev, full_form in medical_abbreviations.items():
            processed_text = re.sub(abbrev, full_form, processed_text, flags=re.IGNORECASE)

        # Ensure medical terms are properly spaced for pronunciation
        processed_text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 to \2', processed_text)  # Time ranges
        processed_text = re.sub(r'(\d+)\s*am\b', r'\1 AM', processed_text, flags=re.IGNORECASE)
        processed_text = re.sub(r'(\d+)\s*pm\b', r'\1 PM', processed_text, flags=re.IGNORECASE)

        return processed_text

    async def postprocess_response_text(self,
                                      text: str,
                                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Postprocess healthcare response text after TTS optimization

        Args:
            text: TTS-optimized text
            context: Healthcare context

        Returns:
            Final healthcare-optimized text
        """
        processed_text = text

        # Add pauses before important medical information
        medical_pause_patterns = [
            (r'\b(available at|located in|found in)\s+', r'\1 <break time="0.3s"/>'),
            (r'\b(appointment|consultation)\s+', r'<break time="0.2s"/>\1 '),
            (r'\b(emergency|urgent)\s+', r'<break time="0.2s"/>\1 '),
        ]

        for pattern, replacement in medical_pause_patterns:
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)

        # Ensure proper pronunciation of common healthcare phrases
        healthcare_pronunciations = {
            r'\bhealthcare providers?\b': 'health care providers',
            r'\bmedical facilities?\b': 'medical fa-cil-i-ties',
            r'\bspecialists?\b': 'spe-cial-ists',
        }

        for pattern, pronunciation in healthcare_pronunciations.items():
            processed_text = re.sub(pattern, pronunciation, processed_text, flags=re.IGNORECASE)

        return processed_text

    def get_max_alternatives(self, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Get maximum alternatives for healthcare queries

        Returns fewer alternatives for urgent cases, more for routine searches

        Args:
            context: Healthcare context

        Returns:
            Maximum number of alternatives
        """
        urgency = self.extract_context_value(context, 'urgency', 'routine')

        if urgency == 'emergency':
            return 1  # Only best match for emergencies
        elif urgency == 'urgent':
            return 2  # Limited alternatives for urgent care
        else:
            return 4  # More alternatives for routine healthcare

    def get_confidence_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Get confidence threshold for healthcare queries

        Higher threshold for emergency/urgent cases to ensure accuracy

        Args:
            context: Healthcare context

        Returns:
            Minimum confidence threshold
        """
        urgency = self.extract_context_value(context, 'urgency', 'routine')

        if urgency == 'emergency':
            return 0.8  # High confidence for emergencies
        elif urgency == 'urgent':
            return 0.7  # Moderate-high confidence for urgent care
        else:
            return 0.6  # Standard confidence for routine healthcare

    def should_include_pronunciation(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if pronunciation should be included for healthcare responses

        Always include pronunciation for healthcare to ensure clear communication

        Args:
            context: Healthcare context

        Returns:
            True (always include pronunciation for healthcare)
        """
        return True

    async def get_provider_context_hint(self,
                                      location_name: str,
                                      provider_type: Optional[str] = None,
                                      specialty: Optional[str] = None) -> str:
        """
        Generate healthcare-specific context hint for the location

        Args:
            location_name: Matched location name
            provider_type: Type of provider (doctor, clinic, etc.)
            specialty: Medical specialty

        Returns:
            Healthcare context hint
        """
        context_parts = []

        if provider_type:
            context_parts.append(f"{provider_type}s available")

        if specialty:
            context_parts.append(f"{specialty} specialists")

        context_parts.append(f"in {location_name}")

        return ", ".join(context_parts)

    async def format_healthcare_response(self,
                                       location_result: LocationResult,
                                       provider_count: Optional[int] = None,
                                       availability: Optional[str] = None) -> str:
        """
        Format a healthcare-specific response with location and provider information

        Args:
            location_result: Location matching result
            provider_count: Number of providers in the area
            availability: Provider availability information

        Returns:
            Formatted healthcare response
        """
        if not location_result.success:
            return f"I couldn't find healthcare providers for '{location_result.original_input}'. " \
                   f"Could you please specify the area more clearly?"

        response_parts = []

        # Main location confirmation
        response_parts.append(f"I found healthcare providers in {location_result.corrected_location}.")

        # Provider count if available
        if provider_count:
            response_parts.append(f"There are {provider_count} providers in this area.")

        # Availability information
        if availability:
            response_parts.append(f"Availability: {availability}")

        # Alternatives if confidence is low
        if location_result.confidence < 0.8 and location_result.alternatives:
            alt_list = ", ".join(location_result.alternatives[:2])
            response_parts.append(f"Did you mean one of these areas: {alt_list}?")

        return " ".join(response_parts)
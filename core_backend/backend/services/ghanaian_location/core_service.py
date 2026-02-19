"""
Core Ghanaian Location Service

Main orchestration service that coordinates phonetic matching, pronunciation
optimization, and learning from user feedback for Ghanaian location names.
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
import logging
from datetime import datetime
import time

from .database.models import (
    GhanaianLocation, LocationResult, UserCorrection, ToolContext, LanguageContext
)
from .database.repositories import LocationRepository
from .phonetic_matcher import PhoneticMatcher, PhoneticMatch
from .pronunciation_service import PronunciationService, PronunciationResult

logger = logging.getLogger(__name__)


class GhanaianLocationService:
    """
    Main service for processing Ghanaian location names

    Provides comprehensive STT correction, phonetic matching, and TTS optimization
    for healthcare and other applications dealing with Ghanaian location names.
    """

    def __init__(self, repository: LocationRepository):
        """
        Initialize the service with database repository

        Args:
            repository: Database repository for location data
        """
        self.repository = repository
        self.phonetic_matcher = PhoneticMatcher(repository)
        self.pronunciation_service = PronunciationService(repository)
        self._initialized = False

        # Performance tracking
        self._query_stats = {
            'total_queries': 0,
            'successful_matches': 0,
            'user_corrections': 0,
            'average_processing_time': 0.0
        }

    async def initialize(self):
        """Initialize the service components"""
        if self._initialized:
            return

        try:
            logger.info("🔄 Initializing GhanaianLocationService...")

            # Setup database indexes
            await self.repository.setup_indexes()

            # Initialize phonetic matcher (loads and caches location data)
            await self.phonetic_matcher.initialize()

            self._initialized = True
            logger.info("✅ GhanaianLocationService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize GhanaianLocationService: {e}")
            raise

    async def process_location_query(self,
                                   query: str,
                                   context: ToolContext = ToolContext.GENERAL,
                                   language: LanguageContext = LanguageContext.ENGLISH,
                                   include_pronunciation: bool = True,
                                   max_alternatives: int = 3) -> LocationResult:
        """
        Process a location query with comprehensive matching and optimization

        Args:
            query: User input text (potentially misheard by STT)
            context: Tool context for specialized behavior
            language: Target language for pronunciation
            include_pronunciation: Whether to include pronunciation guidance
            max_alternatives: Maximum number of alternative matches to return

        Returns:
            LocationResult with best match and pronunciation guidance
        """
        start_time = time.time()

        try:
            await self._ensure_initialized()

            if not query or not query.strip():
                return LocationResult(
                    original_input=query,
                    confidence=0.0,
                    success=False,
                    error_message="Empty query provided"
                )

            logger.debug(f"🔍 Processing location query: '{query}' (context: {context})")

            # Step 1: Find phonetic matches
            matches = await self.phonetic_matcher.find_matches(
                query, max_matches=max_alternatives + 1
            )

            if not matches:
                await self._record_failed_query(query, context)
                return LocationResult(
                    original_input=query,
                    confidence=0.0,
                    success=False,
                    error_message="No matching location found"
                )

            # Step 2: Get best match
            best_match = matches[0]
            alternatives = [m.location.canonical_name for m in matches[1:max_alternatives+1]]

            # Step 3: Get pronunciation guidance if requested
            pronunciation_guide = None
            pronunciation_data = None

            if include_pronunciation:
                pronunciation_data = await self.pronunciation_service.optimize_for_tts(
                    best_match.location.canonical_name,
                    context=context.value,
                    language=language
                )
                pronunciation_guide = pronunciation_data.ssml_markup

            # Step 4: Create result
            result = LocationResult(
                original_input=query,
                corrected_location=best_match.location.canonical_name,
                confidence=best_match.confidence,
                alternatives=alternatives,
                pronunciation_guide=pronunciation_guide,
                geographic_context=best_match.location.geographic.get('region'),
                success=True
            )

            # Step 5: Update analytics
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            await self._update_analytics(
                location_name=best_match.location.canonical_name,
                success=True,
                confidence=best_match.confidence,
                processing_time=processing_time,
                context=context
            )

            logger.debug(
                f"✅ Location processed: '{query}' -> '{result.corrected_location}' "
                f"(confidence: {result.confidence:.2f}, time: {processing_time:.1f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing location query '{query}': {e}")
            await self._record_failed_query(query, context)

            return LocationResult(
                original_input=query,
                confidence=0.0,
                success=False,
                error_message=f"Processing error: {str(e)}"
            )

    async def optimize_response_for_tts(self,
                                      response_text: str,
                                      context: ToolContext = ToolContext.GENERAL) -> str:
        """
        Optimize an entire response text for TTS pronunciation

        Args:
            response_text: Full response containing location names
            context: Response context for optimization

        Returns:
            Optimized response text with better pronunciation
        """
        try:
            await self._ensure_initialized()

            optimized_text = await self.pronunciation_service.optimize_response_text(
                response_text, context=context.value
            )

            logger.debug(f"🗣️ Response optimized for TTS (context: {context})")
            return optimized_text

        except Exception as e:
            logger.error(f"Failed to optimize response for TTS: {e}")
            return response_text  # Return original on error

    async def learn_from_user_correction(self,
                                       original_query: str,
                                       system_interpretation: str,
                                       user_correction: str,
                                       confidence_before: float,
                                       context: ToolContext,
                                       session_id: Optional[str] = None) -> bool:
        """
        Learn from user feedback to improve future matches

        Args:
            original_query: What the user originally said/typed
            system_interpretation: What our system thought it was
            user_correction: What the user said it should be
            confidence_before: System confidence before correction
            context: Tool context where correction occurred
            session_id: Optional session identifier

        Returns:
            True if learning was successful
        """
        try:
            await self._ensure_initialized()

            # Record user correction
            user_correction_record = UserCorrection(
                user_input=original_query,
                system_interpretation=system_interpretation,
                user_correction=user_correction,
                confidence_before=confidence_before,
                tool_context=context,
                session_id=session_id,
                timestamp=datetime.utcnow()
            )

            await self.repository.record_user_correction(user_correction_record)

            # Update phonetic matcher learning
            learning_success = await self.phonetic_matcher.learn_from_correction(
                original_query, user_correction, confidence=0.8
            )

            if learning_success:
                self._query_stats['user_corrections'] += 1
                logger.info(f"✅ Learned from user correction: '{original_query}' -> '{user_correction}'")

            return learning_success

        except Exception as e:
            logger.error(f"Failed to learn from user correction: {e}")
            return False

    async def create_pronunciation_guide(self,
                                       location_name: str,
                                       phonetic_spelling: Optional[str] = None,
                                       ipa_notation: Optional[str] = None,
                                       ssml_markup: Optional[str] = None) -> bool:
        """
        Create a custom pronunciation guide for a location

        Args:
            location_name: Location name to create guide for
            phonetic_spelling: Human-readable phonetic spelling
            ipa_notation: International Phonetic Alphabet notation
            ssml_markup: Custom SSML markup for TTS

        Returns:
            True if guide was created successfully
        """
        try:
            await self._ensure_initialized()

            return await self.pronunciation_service.create_pronunciation_guide(
                location_name=location_name,
                phonetic_spelling=phonetic_spelling,
                ipa_notation=ipa_notation,
                ssml_markup=ssml_markup
            )

        except Exception as e:
            logger.error(f"Failed to create pronunciation guide for '{location_name}': {e}")
            return False

    async def get_location_matches(self,
                                 query: str,
                                 max_matches: int = 5) -> List[PhoneticMatch]:
        """
        Get detailed phonetic matches for analysis or debugging

        Args:
            query: Query text to match
            max_matches: Maximum number of matches to return

        Returns:
            List of detailed PhoneticMatch objects
        """
        try:
            await self._ensure_initialized()
            return await self.phonetic_matcher.find_matches(query, max_matches)
        except Exception as e:
            logger.error(f"Failed to get location matches for '{query}': {e}")
            return []

    async def get_pronunciation_analysis(self,
                                       location_name: str,
                                       context: str = 'general') -> Optional[PronunciationResult]:
        """
        Get detailed pronunciation analysis for a location

        Args:
            location_name: Location name to analyze
            context: Context for pronunciation analysis

        Returns:
            Detailed PronunciationResult or None
        """
        try:
            await self._ensure_initialized()
            return await self.pronunciation_service.optimize_for_tts(location_name, context)
        except Exception as e:
            logger.error(f"Failed to get pronunciation analysis for '{location_name}': {e}")
            return None

    async def get_service_statistics(self) -> Dict[str, Any]:
        """
        Get service performance and usage statistics

        Returns:
            Dictionary with service statistics
        """
        try:
            repository_stats = await self.repository.health_check()

            return {
                **self._query_stats,
                **repository_stats,
                'service_initialized': self._initialized,
                'phonetic_matcher_ready': hasattr(self.phonetic_matcher, '_location_cache') and
                                        len(self.phonetic_matcher._location_cache) > 0
            }
        except Exception as e:
            logger.error(f"Failed to get service statistics: {e}")
            return {'error': str(e)}

    # Private helper methods

    async def _ensure_initialized(self):
        """Ensure service is initialized before use"""
        if not self._initialized:
            await self.initialize()

    async def _record_failed_query(self, query: str, context: ToolContext):
        """Record a failed query for analysis"""
        try:
            await self._update_analytics(
                location_name="UNKNOWN",
                success=False,
                confidence=0.0,
                processing_time=0.0,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to record failed query: {e}")

    async def _update_analytics(self,
                              location_name: str,
                              success: bool,
                              confidence: float,
                              processing_time: float,
                              context: ToolContext):
        """Update service analytics"""
        try:
            # Update internal stats
            self._query_stats['total_queries'] += 1
            if success:
                self._query_stats['successful_matches'] += 1

            # Update running average processing time
            current_avg = self._query_stats['average_processing_time']
            total_queries = self._query_stats['total_queries']
            new_avg = ((current_avg * (total_queries - 1)) + processing_time) / total_queries
            self._query_stats['average_processing_time'] = new_avg

            # Update repository analytics
            if location_name != "UNKNOWN":
                await self.repository.update_usage_analytics(
                    location_name=location_name,
                    success=success,
                    confidence=confidence,
                    processing_time_ms=processing_time,
                    context=context
                )

        except Exception as e:
            logger.error(f"Failed to update analytics: {e}")
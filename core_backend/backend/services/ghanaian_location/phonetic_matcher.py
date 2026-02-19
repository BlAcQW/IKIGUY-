"""
Phonetic Matcher for Ghanaian Location Names

Uses multiple phonetic algorithms and fuzzy matching to find
location matches despite STT mishearings and pronunciation variations.
"""

import asyncio
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
import phonetics
from rapidfuzz import fuzz, process
from unidecode import unidecode

from .database.models import GhanaianLocation, STTCorrection, LocationResult
from .database.repositories import LocationRepository

logger = logging.getLogger(__name__)


@dataclass
class PhoneticMatch:
    """Result from phonetic matching"""
    location: GhanaianLocation
    confidence: float
    algorithm: str
    similarity_score: float
    match_type: str  # 'exact', 'phonetic', 'fuzzy', 'alias'


class PhoneticMatcher:
    """
    Advanced phonetic matching for Ghanaian location names

    Combines multiple algorithms:
    - Soundex: Classic phonetic algorithm
    - NYSIIS: More accurate than Soundex
    - Double Metaphone: Handles multiple pronunciations
    - Fuzzy matching: Character-based similarity
    - Custom Ghanaian patterns: Twi/Ga/Ewe specific rules
    """

    def __init__(self, repository: LocationRepository):
        self.repository = repository
        self.confidence_threshold = 0.6
        self.fuzzy_threshold = 70  # rapidfuzz threshold (0-100)

        # Cache for performance
        self._location_cache: List[GhanaianLocation] = []
        self._phonetic_cache: Dict[str, Dict[str, str]] = {}
        self._last_cache_update = None

    async def initialize(self):
        """Initialize the matcher by loading and caching location data"""
        try:
            logger.info("🔄 Initializing PhoneticMatcher...")

            # Load all active locations
            self._location_cache = await self.repository.get_all_active_locations()

            # Pre-compute phonetic codes for all locations
            for location in self._location_cache:
                canonical = location.canonical_name
                self._phonetic_cache[canonical] = self._compute_all_phonetic_codes(canonical)

                # Also compute for aliases
                for alias in location.aliases:
                    if alias not in self._phonetic_cache:
                        self._phonetic_cache[alias] = self._compute_all_phonetic_codes(alias)

            logger.info(f"✅ PhoneticMatcher initialized with {len(self._location_cache)} locations")

        except Exception as e:
            logger.error(f"Failed to initialize PhoneticMatcher: {e}")
            raise

    def _compute_all_phonetic_codes(self, text: str) -> Dict[str, str]:
        """Compute all phonetic codes for a given text"""
        normalized = self._normalize_text(text)

        codes = {
            'soundex': phonetics.soundex(normalized),
            'nysiis': phonetics.nysiis(normalized),
            'metaphone': phonetics.metaphone(normalized),
            'dmetaphone_primary': phonetics.dmetaphone(normalized)[0] or '',
            'dmetaphone_secondary': phonetics.dmetaphone(normalized)[1] or '',
        }

        # Add custom Ghanaian phonetic patterns
        codes['ghana_pattern'] = self._compute_ghana_pattern(normalized)

        return codes

    def _normalize_text(self, text: str) -> str:
        """Normalize text for phonetic processing"""
        if not text:
            return ""

        # Remove accents and convert to ASCII
        normalized = unidecode(text)

        # Convert to uppercase and remove extra spaces
        normalized = normalized.upper().strip()

        # Remove common prefixes/suffixes that don't affect phonetics
        prefixes_to_remove = ['THE ', 'GREATER ', 'EAST ', 'WEST ', 'NORTH ', 'SOUTH ']
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()

        return normalized

    def _compute_ghana_pattern(self, text: str) -> str:
        """
        Custom phonetic pattern for Ghanaian location names
        Based on Twi, Ga, and Ewe phonetic patterns
        """
        if not text:
            return ""

        # Common Ghanaian phonetic substitutions
        substitutions = {
            'KW': 'QU',    # Kwabenya -> Quabenya
            'NY': 'NI',    # Nyamekye -> Niamekye
            'DZ': 'Z',     # Dzorwulu -> Zorwulu
            'TSH': 'CH',   # Common in some pronunciations
            'PH': 'F',     # Standard substitution
            'GH': 'G',     # Ghana -> Gana
            'WH': 'W',     # What -> Wat
        }

        pattern = text
        for old, new in substitutions.items():
            pattern = pattern.replace(old, new)

        # Remove vowels except the first one (similar to soundex but more aggressive)
        if len(pattern) > 1:
            first_char = pattern[0]
            rest = ''.join(c for c in pattern[1:] if c not in 'AEIOU')
            pattern = first_char + rest

        # Limit to 6 characters for consistency
        return pattern[:6].ljust(6, '0')

    async def find_matches(self, query: str, max_matches: int = 5) -> List[PhoneticMatch]:
        """
        Find location matches using multiple phonetic algorithms

        Args:
            query: User input text to match
            max_matches: Maximum number of matches to return

        Returns:
            List of PhoneticMatch objects sorted by confidence
        """
        if not query or not query.strip():
            return []

        try:
            # Check cache freshness and refresh if needed
            await self._refresh_cache_if_needed()

            matches = []
            normalized_query = self._normalize_text(query)

            # Step 1: Check for direct STT corrections first
            stt_correction = await self.repository.get_stt_correction(query.lower())
            if stt_correction and stt_correction.confidence > self.confidence_threshold:
                location = await self.repository.get_location_by_name(stt_correction.correct_location)
                if location:
                    match = PhoneticMatch(
                        location=location,
                        confidence=stt_correction.confidence,
                        algorithm='stt_correction',
                        similarity_score=1.0,
                        match_type='exact'
                    )
                    matches.append(match)

                    # Update usage statistics
                    await self.repository.update_correction_usage(query.lower(), success=True)

            # Step 2: Exact name matches
            exact_match = await self.repository.get_location_by_name(normalized_query)
            if exact_match:
                match = PhoneticMatch(
                    location=exact_match,
                    confidence=1.0,
                    algorithm='exact',
                    similarity_score=1.0,
                    match_type='exact'
                )
                if match not in matches:  # Avoid duplicates
                    matches.append(match)

            # Step 3: Alias matches
            alias_matches = await self.repository.find_locations_by_alias(normalized_query)
            for location in alias_matches:
                if not any(m.location.canonical_name == location.canonical_name for m in matches):
                    match = PhoneticMatch(
                        location=location,
                        confidence=0.95,
                        algorithm='alias',
                        similarity_score=0.95,
                        match_type='alias'
                    )
                    matches.append(match)

            # Step 4: Phonetic matches
            if len(matches) < max_matches:
                phonetic_matches = await self._find_phonetic_matches(normalized_query, max_matches - len(matches))
                for match in phonetic_matches:
                    if not any(m.location.canonical_name == match.location.canonical_name for m in matches):
                        matches.append(match)

            # Step 5: Fuzzy matches (fallback for very different inputs)
            if len(matches) < max_matches:
                fuzzy_matches = await self._find_fuzzy_matches(normalized_query, max_matches - len(matches))
                for match in fuzzy_matches:
                    if not any(m.location.canonical_name == match.location.canonical_name for m in matches):
                        matches.append(match)

            # Sort by confidence and return top matches
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches[:max_matches]

        except Exception as e:
            logger.error(f"Error finding matches for '{query}': {e}")
            return []

    async def _find_phonetic_matches(self, query: str, max_matches: int) -> List[PhoneticMatch]:
        """Find matches using phonetic algorithms"""
        matches = []
        query_codes = self._compute_all_phonetic_codes(query)

        for location in self._location_cache:
            best_confidence = 0.0
            best_algorithm = None

            # Check main location name
            location_codes = self._phonetic_cache.get(location.canonical_name, {})
            for algorithm, query_code in query_codes.items():
                if algorithm in location_codes and query_code:
                    location_code = location_codes[algorithm]
                    if query_code == location_code:
                        confidence = self._calculate_phonetic_confidence(algorithm, query, location.canonical_name)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_algorithm = algorithm

            # Check aliases
            for alias in location.aliases:
                alias_codes = self._phonetic_cache.get(alias, {})
                for algorithm, query_code in query_codes.items():
                    if algorithm in alias_codes and query_code:
                        alias_code = alias_codes[algorithm]
                        if query_code == alias_code:
                            confidence = self._calculate_phonetic_confidence(algorithm, query, alias)
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_algorithm = algorithm

            # Add to matches if confidence is high enough
            if best_confidence > self.confidence_threshold:
                match = PhoneticMatch(
                    location=location,
                    confidence=best_confidence,
                    algorithm=best_algorithm,
                    similarity_score=best_confidence,
                    match_type='phonetic'
                )
                matches.append(match)

        # Sort by confidence and return top matches
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:max_matches]

    async def _find_fuzzy_matches(self, query: str, max_matches: int) -> List[PhoneticMatch]:
        """Find matches using fuzzy string matching"""
        matches = []

        # Create list of all possible match targets
        targets = []
        location_map = {}

        for location in self._location_cache:
            # Add canonical name
            targets.append(location.canonical_name)
            location_map[location.canonical_name] = location

            # Add aliases
            for alias in location.aliases:
                targets.append(alias)
                location_map[alias] = location

        # Use rapidfuzz for fuzzy matching
        fuzzy_results = process.extract(
            query,
            targets,
            scorer=fuzz.WRatio,  # Weighted ratio - good for location names
            limit=max_matches * 2  # Get more to filter duplicates
        )

        seen_locations = set()
        for target, score, _ in fuzzy_results:
            if score >= self.fuzzy_threshold:
                location = location_map[target]
                if location.canonical_name not in seen_locations:
                    confidence = min(0.9, score / 100.0)  # Cap at 0.9 for fuzzy matches
                    match = PhoneticMatch(
                        location=location,
                        confidence=confidence,
                        algorithm='fuzzy',
                        similarity_score=score / 100.0,
                        match_type='fuzzy'
                    )
                    matches.append(match)
                    seen_locations.add(location.canonical_name)

                    if len(matches) >= max_matches:
                        break

        return matches

    def _calculate_phonetic_confidence(self, algorithm: str, query: str, match: str) -> float:
        """Calculate confidence score for a phonetic match"""
        base_confidences = {
            'soundex': 0.7,
            'nysiis': 0.75,
            'metaphone': 0.72,
            'dmetaphone_primary': 0.8,
            'dmetaphone_secondary': 0.75,
            'ghana_pattern': 0.85  # Higher confidence for custom pattern
        }

        base_confidence = base_confidences.get(algorithm, 0.7)

        # Adjust based on string length similarity
        len_ratio = min(len(query), len(match)) / max(len(query), len(match))
        length_adjustment = len_ratio * 0.1

        # Adjust based on exact character overlap
        common_chars = set(query.lower()) & set(match.lower())
        char_ratio = len(common_chars) / max(len(set(query.lower())), len(set(match.lower())))
        char_adjustment = char_ratio * 0.05

        final_confidence = base_confidence + length_adjustment + char_adjustment
        return min(1.0, final_confidence)

    async def _refresh_cache_if_needed(self):
        """Refresh location cache if it's stale"""
        # For now, we'll refresh every hour or if cache is empty
        import time
        current_time = time.time()

        if (not self._location_cache or
            not self._last_cache_update or
            current_time - self._last_cache_update > 3600):  # 1 hour

            await self.initialize()
            self._last_cache_update = current_time

    async def get_best_match(self, query: str) -> Optional[LocationResult]:
        """
        Get the single best match for a query

        Args:
            query: User input text to match

        Returns:
            LocationResult with the best match or None
        """
        matches = await self.find_matches(query, max_matches=1)

        if matches:
            best_match = matches[0]

            # Get pronunciation guide if available
            pronunciation_guide = await self.repository.get_pronunciation_guide(
                best_match.location.canonical_name
            )

            return LocationResult(
                original_input=query,
                corrected_location=best_match.location.canonical_name,
                confidence=best_match.confidence,
                alternatives=[m.location.canonical_name for m in matches[1:6]],  # Top 5 alternatives
                pronunciation_guide=pronunciation_guide.ssml_markup if pronunciation_guide else None,
                geographic_context=best_match.location.geographic.get('region'),
                success=True
            )
        else:
            return LocationResult(
                original_input=query,
                confidence=0.0,
                success=False,
                error_message="No matching location found"
            )

    async def learn_from_correction(self, original_query: str, corrected_location: str,
                                  confidence: float = 0.8) -> bool:
        """
        Learn from a user correction to improve future matches

        Args:
            original_query: The original misheard input
            corrected_location: What the user said it should be
            confidence: Confidence in this correction

        Returns:
            True if learning was successful
        """
        try:
            # Check if location exists
            location = await self.repository.get_location_by_name(corrected_location)
            if not location:
                logger.warning(f"Cannot learn correction: location '{corrected_location}' not found")
                return False

            # Check if correction already exists
            existing = await self.repository.get_stt_correction(original_query.lower())

            if existing:
                # Update existing correction
                await self.repository.update_correction_usage(original_query.lower(), success=True)
            else:
                # Create new STT correction
                new_correction = STTCorrection(
                    misheard_input=original_query.lower(),
                    correct_location=corrected_location.upper(),
                    confidence=confidence,
                    phonetic_similarity=self._calculate_phonetic_similarity(original_query, corrected_location),
                    frequency=1,
                    verified=False,
                    source="user_correction"
                )
                await self.repository.create_stt_correction(new_correction)

            logger.info(f"✅ Learned correction: '{original_query}' -> '{corrected_location}'")
            return True

        except Exception as e:
            logger.error(f"Failed to learn from correction: {e}")
            return False

    def _calculate_phonetic_similarity(self, text1: str, text2: str) -> float:
        """Calculate phonetic similarity between two texts"""
        codes1 = self._compute_all_phonetic_codes(text1)
        codes2 = self._compute_all_phonetic_codes(text2)

        matches = 0
        total = 0

        for algorithm in codes1:
            if algorithm in codes2:
                total += 1
                if codes1[algorithm] == codes2[algorithm] and codes1[algorithm]:
                    matches += 1

        return matches / total if total > 0 else 0.0
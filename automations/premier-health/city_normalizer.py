#!/usr/bin/env python3
"""
City Name Normalizer for Ghana STT Mappings
============================================

Helper module for normalizing speech-to-text city names to their correct forms.
Provides utilities for lookup, validation, and fuzzy matching.

Author: AI Labs Africa
Date: October 2025
Version: 1.0
"""

from typing import Optional, List, Tuple, Dict
from difflib import SequenceMatcher
from ghana_cities_stt_mapping import (
    GHANA_CITY_STT_MAPPING,
    STT_TO_CORRECT_CITY,
    REGIONAL_GROUPINGS,
    get_statistics as get_mapping_statistics
)


class CityNormalizer:
    """
    Helper class for normalizing and validating Ghana city names from STT input.

    Example:
        normalizer = CityNormalizer()

        # Normalize STT input
        city = normalizer.normalize("medina")  # Returns: "MADINA"

        # Get variations
        variations = normalizer.get_variations("MADINA")  # Returns: ['medina', 'madonna', ...]

        # Fuzzy match
        matches = normalizer.find_closest_match("winnepeg")  # Returns: [("WINNEBA", 0.95)]
    """

    # Ghana regions blacklist to prevent region-to-city confusion (e.g., "Ashanti" → "Ashaiman")
    # Reason: STT often confuses region names with city names, causing incorrect matches
    GHANA_REGIONS = {
        'GREATER_ACCRA', 'GREATER ACCRA', 'ACCRA REGION',
        'CENTRAL', 'CENTRAL REGION',
        'ASHANTI', 'ASHANTI REGION',
        'BRONG_AHAFO', 'BRONG AHAFO', 'BONO', 'BONO REGION',
        'EASTERN', 'EASTERN REGION',
        'WESTERN', 'WESTERN REGION',
        'VOLTA', 'VOLTA REGION',
        'NORTHERN', 'NORTHERN REGION',
        'UPPER_EAST', 'UPPER EAST', 'UPPER EAST REGION',
        'UPPER_WEST', 'UPPER WEST', 'UPPER WEST REGION',
    }

    def __init__(self):
        """Initialize the city normalizer with mappings."""
        self.city_mapping = GHANA_CITY_STT_MAPPING
        self.reverse_mapping = STT_TO_CORRECT_CITY
        self.regional_groupings = REGIONAL_GROUPINGS

    def normalize_city(self, input_text: str, case_sensitive: bool = False) -> Optional[str]:
        """
        Normalize an STT input to the correct city name.

        Args:
            input_text (str): STT input text (e.g., "medina", "winnipeg")
            case_sensitive (bool): Whether to perform case-sensitive matching

        Returns:
            Optional[str]: Correct city name (e.g., "MADINA") or None if not found

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.normalize_city("medina")
            'MADINA'
            >>> normalizer.normalize_city("circus")
            'CIRCLE'
            >>> normalizer.normalize_city("unknown")
            None
        """
        if not input_text:
            return None

        # Convert to uppercase for lookup unless case-sensitive
        lookup_key = input_text if case_sensitive else input_text.upper()

        # Direct lookup in reverse mapping
        return self.reverse_mapping.get(lookup_key)

    def get_variations(self, city: str) -> List[str]:
        """
        Get all STT variations for a given city.

        Args:
            city (str): Correct city name (e.g., "MADINA")

        Returns:
            List[str]: List of STT variations

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.get_variations("MADINA")
            ['medina', 'madonna', 'moderna', 'marina', ...]
        """
        if not city:
            return []

        return self.city_mapping.get(city.upper(), [])

    def is_valid_city(self, city: str) -> bool:
        """
        Check if a city name is valid (exists in our mappings).

        Args:
            city (str): City name to check

        Returns:
            bool: True if valid city, False otherwise

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.is_valid_city("MADINA")
            True
            >>> normalizer.is_valid_city("INVALID")
            False
        """
        if not city:
            return False

        return city.upper() in self.city_mapping

    def is_valid_variation(self, variation: str) -> bool:
        """
        Check if an STT variation exists in our mappings.

        Args:
            variation (str): STT variation to check

        Returns:
            bool: True if valid variation, False otherwise

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.is_valid_variation("medina")
            True
            >>> normalizer.is_valid_variation("xyz123")
            False
        """
        if not variation:
            return False

        return variation.upper() in self.reverse_mapping

    def get_cities_by_region(self, region: str) -> List[str]:
        """
        Get all cities in a specific region.

        Args:
            region (str): Region name (e.g., "GREATER_ACCRA", "ASHANTI")

        Returns:
            List[str]: List of cities in that region

        Example:
            >>> normalizer = CityNormalizer()
            >>> cities = normalizer.get_cities_by_region("VOLTA")
            >>> print(cities)
            ['HO', 'HOHOE']
        """
        if not region:
            return []

        return self.regional_groupings.get(region.upper(), [])

    def get_all_regions(self) -> List[str]:
        """
        Get list of all regions.

        Returns:
            List[str]: List of region names

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.get_all_regions()
            ['GREATER_ACCRA', 'CENTRAL', 'ASHANTI', ...]
        """
        return list(self.regional_groupings.keys())

    def find_closest_match(
        self,
        input_text: str,
        threshold: float = 0.6,
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find closest matching cities using fuzzy matching.
        Useful when exact STT variation doesn't exist in mappings.

        Args:
            input_text (str): STT input text
            threshold (float): Minimum similarity score (0.0 to 1.0)
            limit (int): Maximum number of matches to return

        Returns:
            List[Tuple[str, float]]: List of (city_name, similarity_score) tuples

        Example:
            >>> normalizer = CityNormalizer()
            >>> matches = normalizer.find_closest_match("winnepeg", threshold=0.6)
            >>> print(matches)
            [('WINNEBA', 0.85), ...]
        """
        if not input_text:
            return []

        # Normalize input
        input_normalized = input_text.lower().strip()

        # Calculate similarity scores for all cities
        matches = []

        # Check against all variations
        for correct_city, variations in self.city_mapping.items():
            for variation in variations:
                similarity = SequenceMatcher(None, input_normalized, variation.lower()).ratio()

                if similarity >= threshold:
                    matches.append((correct_city, similarity))

        # Remove duplicates and sort by similarity (descending)
        unique_matches = {}
        for city, score in matches:
            if city not in unique_matches or score > unique_matches[city]:
                unique_matches[city] = score

        sorted_matches = sorted(unique_matches.items(), key=lambda x: x[1], reverse=True)

        return sorted_matches[:limit]

    def is_region_name(self, input_text: str) -> bool:
        """
        Check if input text is a Ghana region name (to prevent region-to-city confusion).

        Args:
            input_text (str): Input text to check

        Returns:
            bool: True if input matches a region name, False otherwise

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.is_region_name("Ashanti")
            True
            >>> normalizer.is_region_name("Madina")
            False
        """
        if not input_text:
            return False

        # Check exact match (case-insensitive)
        input_upper = input_text.upper().strip()
        if input_upper in self.GHANA_REGIONS:
            return True

        # Check fuzzy match against regions (high threshold to avoid false positives)
        # Reason: "Ashanti" should match ASHANTI region, not ASHAIMAN city
        for region in self.GHANA_REGIONS:
            similarity = SequenceMatcher(None, input_upper, region).ratio()
            if similarity >= 0.85:  # High threshold for region matching
                return True

        return False

    def detect_region_name(self, input_text: str) -> Optional[str]:
        """
        Detect and return the normalized region name from input text.

        Args:
            input_text (str): Input text to check

        Returns:
            Optional[str]: Normalized region name (e.g., "WESTERN", "ASHANTI") or None

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.detect_region_name("Ashanti Region")
            'ASHANTI'
            >>> normalizer.detect_region_name("Western")
            'WESTERN'
            >>> normalizer.detect_region_name("Madina")
            None
        """
        if not input_text:
            return None

        input_upper = input_text.upper().strip()

        # Check exact match first
        if input_upper in self.GHANA_REGIONS:
            # Normalize to simple region name (e.g., "ASHANTI REGION" → "ASHANTI")
            return input_upper.replace(' REGION', '').replace('_', ' ')

        # Check fuzzy match against regions
        # Reason: "ashanti" should match "ASHANTI REGION"
        best_match = None
        best_score = 0.0
        for region in self.GHANA_REGIONS:
            similarity = SequenceMatcher(None, input_upper, region).ratio()
            if similarity >= 0.85 and similarity > best_score:
                best_match = region
                best_score = similarity

        if best_match:
            # Normalize to simple region name
            return best_match.replace(' REGION', '').replace('_', ' ')

        return None

    def normalize_with_confidence(
        self,
        input_text: str,
        fuzzy_threshold: float = 0.85,  # Increased from 0.8 to 0.85 for better accuracy
        allow_regions: bool = False  # New parameter to control region blocking
    ) -> Tuple[Optional[str], float, str]:
        """
        Normalize with confidence score and method used.

        Args:
            input_text (str): STT input text
            fuzzy_threshold (float): Threshold for fuzzy matching (default: 0.85)
            allow_regions (bool): If True, return region name instead of blocking (default: False)

        Returns:
            Tuple[Optional[str], float, str]: (city_or_region_name, confidence, method)
                - city_or_region_name: Correct city/region name or None
                - confidence: Confidence score (0.0 to 1.0)
                - method: "exact", "fuzzy", "region_detected", "region_blocked", or "not_found"

        Example:
            >>> normalizer = CityNormalizer()
            >>> city, confidence, method = normalizer.normalize_with_confidence("medina")
            >>> print(f"{city} ({confidence:.2f}) via {method}")
            MADINA (1.00) via exact

            >>> city, confidence, method = normalizer.normalize_with_confidence("Ashanti", allow_regions=False)
            >>> print(f"{city} ({confidence:.2f}) via {method}")
            None (0.00) via region_blocked

            >>> region, confidence, method = normalizer.normalize_with_confidence("Ashanti", allow_regions=True)
            >>> print(f"{region} ({confidence:.2f}) via {method}")
            ASHANTI (0.95) via region_detected
        """
        if not input_text:
            return (None, 0.0, "not_found")

        # Check if input is a region name
        # Reason: Prevents "Ashanti" (region) from matching "ASHAIMAN" (city)
        region_name = self.detect_region_name(input_text)
        if region_name:
            if allow_regions:
                # Return the detected region for regional queries
                return (region_name, 0.95, "region_detected")
            else:
                # Block region-to-city confusion
                return (None, 0.0, "region_blocked")

        # Try exact match first
        exact_match = self.normalize_city(input_text)
        if exact_match:
            return (exact_match, 1.0, "exact")

        # Try fuzzy matching with increased threshold (0.85 instead of 0.8)
        # Reason: Higher threshold reduces false positives like "Ashanti" → "ASHAIMAN" (0.71)
        fuzzy_matches = self.find_closest_match(input_text, threshold=fuzzy_threshold, limit=1)
        if fuzzy_matches:
            city, score = fuzzy_matches[0]
            return (city, score, "fuzzy")

        return (None, 0.0, "not_found")

    def get_region_for_city(self, city: str) -> Optional[str]:
        """
        Get the region for a given city.

        Args:
            city (str): City name

        Returns:
            Optional[str]: Region name or None if not found

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.get_region_for_city("MADINA")
            'GREATER_ACCRA'
        """
        if not city:
            return None

        city_upper = city.upper()

        for region, cities in self.regional_groupings.items():
            if city_upper in cities:
                return region

        return None

    def get_cities_for_region(self, region: str) -> List[str]:
        """
        Get all cities for a given region.

        Args:
            region (str): Region name (e.g., "WESTERN", "ASHANTI")

        Returns:
            List[str]: List of city names in the region

        Example:
            >>> normalizer = CityNormalizer()
            >>> cities = normalizer.get_cities_for_region("WESTERN")
            >>> print(cities)
            ['TAKORADI', 'SEKONDI', 'TARKWA', ...]
        """
        if not region:
            return []

        # Normalize region name (handle variations like "WESTERN REGION", "western", etc.)
        region_normalized = region.upper().replace(' REGION', '').replace('_', ' ').strip()

        # Try direct lookup
        if region_normalized in self.regional_groupings:
            return self.regional_groupings[region_normalized]

        # Try variations
        for reg_key, cities in self.regional_groupings.items():
            if reg_key.replace('_', ' ') == region_normalized:
                return cities

        return []

    def batch_normalize(
        self,
        input_texts: List[str],
        include_confidence: bool = False
    ) -> List[Dict]:
        """
        Normalize multiple STT inputs in batch.

        Args:
            input_texts (List[str]): List of STT inputs
            include_confidence (bool): Include confidence scores

        Returns:
            List[Dict]: List of normalization results

        Example:
            >>> normalizer = CityNormalizer()
            >>> results = normalizer.batch_normalize(["medina", "circus", "unknown"])
            >>> for result in results:
            ...     print(result)
            {'input': 'medina', 'city': 'MADINA', 'region': 'GREATER_ACCRA'}
            {'input': 'circus', 'city': 'CIRCLE', 'region': 'GREATER_ACCRA'}
            {'input': 'unknown', 'city': None, 'region': None}
        """
        results = []

        for input_text in input_texts:
            if include_confidence:
                city, confidence, method = self.normalize_with_confidence(input_text)
                region = self.get_region_for_city(city) if city else None

                results.append({
                    'input': input_text,
                    'city': city,
                    'region': region,
                    'confidence': confidence,
                    'method': method
                })
            else:
                city = self.normalize_city(input_text)
                region = self.get_region_for_city(city) if city else None

                results.append({
                    'input': input_text,
                    'city': city,
                    'region': region
                })

        return results

    def normalize_plan_type(self, input_text: str) -> Optional[str]:
        """
        Normalize plan type input to standard format.

        Args:
            input_text (str): Plan type input (e.g., "plat", "mer", "platinum plus")

        Returns:
            Optional[str]: Normalized plan type or None if not recognized

        Example:
            >>> normalizer = CityNormalizer()
            >>> normalizer.normalize_plan_type("plat")
            'PLATINUM'
            >>> normalizer.normalize_plan_type("mer")
            'MERCURY'
            >>> normalizer.normalize_plan_type("platinum plus")
            'PLATINUM PLUS'
        """
        if not input_text:
            return None

        # Normalize input
        normalized_input = input_text.upper().strip()

        # Direct match
        if normalized_input in self.reverse_mapping:
            return self.reverse_mapping[normalized_input]

        # Check case-insensitive
        for key, value in self.reverse_mapping.items():
            if key.upper() == normalized_input:
                return value

        return None

    def get_statistics(self) -> Dict:
        """
        Get statistics about the mappings.

        Returns:
            Dict: Statistics dictionary

        Example:
            >>> normalizer = CityNormalizer()
            >>> stats = normalizer.get_statistics()
            >>> print(stats)
            {'total_cities': 106, 'total_variations': 600+, ...}
        """
        return get_mapping_statistics()


# Convenience functions for quick usage without instantiating class

_normalizer_instance = None


def get_normalizer() -> CityNormalizer:
    """
    Get singleton instance of CityNormalizer.

    Returns:
        CityNormalizer: Singleton normalizer instance
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = CityNormalizer()
    return _normalizer_instance


def normalize(input_text: str) -> Optional[str]:
    """
    Quick normalize function - convenience wrapper.

    Args:
        input_text (str): STT input text

    Returns:
        Optional[str]: Correct city name or None

    Example:
        >>> from city_normalizer import normalize
        >>> normalize("medina")
        'MADINA'
    """
    return get_normalizer().normalize_city(input_text)


def get_variations(city: str) -> List[str]:
    """
    Quick get_variations function - convenience wrapper.

    Args:
        city (str): City name

    Returns:
        List[str]: List of variations

    Example:
        >>> from city_normalizer import get_variations
        >>> get_variations("MADINA")
        ['medina', 'madonna', 'moderna', ...]
    """
    return get_normalizer().get_variations(city)


def find_closest(input_text: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
    """
    Quick find_closest_match function - convenience wrapper.

    Args:
        input_text (str): STT input text
        threshold (float): Minimum similarity threshold

    Returns:
        List[Tuple[str, float]]: List of (city, score) tuples

    Example:
        >>> from city_normalizer import find_closest
        >>> find_closest("winnepeg")
        [('WINNEBA', 0.95), ...]
    """
    return get_normalizer().find_closest_match(input_text, threshold=threshold)


# Module metadata
__version__ = '1.0.0'
__author__ = 'AI Labs Africa'
__description__ = 'City name normalizer for Ghana STT mappings'


if __name__ == '__main__':
    # Demo usage
    print("=" * 80)
    print("GHANA CITY NORMALIZER - DEMO")
    print("=" * 80)

    normalizer = CityNormalizer()

    # Test cases
    test_inputs = [
        'medina',
        'circus',
        'winnipeg',
        'jaw wulu',
        'coffee ridua',
        'taco radi',
        'unknown_city'
    ]

    print("\n1. EXACT NORMALIZATION:")
    print("-" * 80)
    for test_input in test_inputs:
        result = normalizer.normalize_city(test_input)
        status = "✓" if result else "✗"
        print(f"{status} Input: '{test_input}' → {result}")

    print("\n2. NORMALIZATION WITH CONFIDENCE:")
    print("-" * 80)
    for test_input in test_inputs:
        city, confidence, method = normalizer.normalize_with_confidence(test_input)
        if city:
            region = normalizer.get_region_for_city(city)
            print(f"✓ '{test_input}' → {city} ({region}) | Confidence: {confidence:.2f} | Method: {method}")
        else:
            print(f"✗ '{test_input}' → Not found")

    print("\n3. GET VARIATIONS:")
    print("-" * 80)
    test_cities = ['MADINA', 'WINNEBA', 'DZORWULU']
    for city in test_cities:
        variations = normalizer.get_variations(city)
        print(f"{city}: {', '.join(variations[:5])}... ({len(variations)} total)")

    print("\n4. FUZZY MATCHING:")
    print("-" * 80)
    fuzzy_tests = ['winnepeg', 'madenna', 'circuis']
    for test_input in fuzzy_tests:
        matches = normalizer.find_closest_match(test_input, threshold=0.6, limit=3)
        print(f"'{test_input}' → {matches}")

    print("\n5. BATCH NORMALIZATION:")
    print("-" * 80)
    batch_inputs = ['medina', 'circus', 'winnepeg']
    results = normalizer.batch_normalize(batch_inputs, include_confidence=True)
    for result in results:
        print(f"  {result}")

    print("\n6. STATISTICS:")
    print("-" * 80)
    stats = normalizer.get_statistics()
    print(f"Total Cities: {stats['total_cities']}")
    print(f"Total Variations: {stats['total_variations']}")
    print(f"Avg Variations per City: {stats['average_variations_per_city']}")
    print(f"Total Regions: {stats['regions']}")

    print("\n" + "=" * 80)

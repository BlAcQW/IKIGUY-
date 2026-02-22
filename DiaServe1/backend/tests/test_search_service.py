"""
Tests for PropertySearchService.

Covers:
- _normalize_amenity: direct match, partial match, unknown
- _fallback_amenity_extraction: multi-amenity extraction
- _parse_query_with_regex: bedrooms, price, locations, amenities, pet policy, furnished, intent
- search(): integration test with mocked MongoDB
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add backend to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.search import (
    PetPolicy,
    PropertyType,
    SearchFilters,
    SearchIntent,
    SearchRequest,
    SearchResponse,
)
from app.services.search_service import PropertySearchService


# ==================== Fixtures ====================


@pytest.fixture
def mock_database():
    """Create a mock AsyncIOMotorDatabase."""
    db = MagicMock()
    db.__getitem__ = MagicMock(side_effect=lambda name: MagicMock())
    return db


@pytest.fixture
def search_service(mock_database):
    """Create a PropertySearchService with mocked database."""
    return PropertySearchService(mock_database)


def _make_property_doc(
    *,
    name: str = "Test Property",
    city: str = "Accra",
    neighborhood: str = "East Legon",
    property_type: str = "apartment",
    price_usd: float = 250_000,
    bedrooms: int = 3,
    bathrooms: int = 2,
    pool: bool = True,
    gym: bool = False,
    garden: bool = True,
    pet_policy: str = "allowed",
    furnished: bool = False,
) -> Dict[str, Any]:
    """Build a realistic property document matching MongoDB schema."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": f"A lovely {property_type} in {city}",
        "property_type": property_type,
        "status": "active",
        "organization_id": "test-org",
        "location": {
            "city": city,
            "state": "Greater Accra",
            "neighborhood": neighborhood,
            "country": "Ghana",
        },
        "features": {
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "sqft": 1500,
            "pool": pool,
            "gym": gym,
            "garden": garden,
            "balcony": True,
            "elevator": False,
            "air_conditioning": True,
            "heating": False,
            "fireplace": False,
            "security_system": True,
            "storage": False,
            "parking_spaces": 2,
            "pet_policy": pet_policy,
            "furnished": furnished,
        },
        "financial": {
            "price_usd": price_usd,
            "base_currency": "USD",
        },
        "created_at": datetime.utcnow().isoformat(),
    }


# ==================== _normalize_amenity ====================


class TestNormalizeAmenity:
    """Tests for _normalize_amenity."""

    def test_direct_match(self, search_service):
        assert search_service._normalize_amenity("pool") == "pool"
        assert search_service._normalize_amenity("gym") == "gym"
        assert search_service._normalize_amenity("parking") == "parking_spaces"

    def test_multi_word_direct_match(self, search_service):
        assert search_service._normalize_amenity("swimming pool") == "pool"
        assert search_service._normalize_amenity("fitness center") == "gym"
        assert search_service._normalize_amenity("security system") == "security_system"

    def test_case_insensitive(self, search_service):
        assert search_service._normalize_amenity("POOL") == "pool"
        assert search_service._normalize_amenity("Swimming Pool") == "pool"

    def test_partial_match(self, search_service):
        assert search_service._normalize_amenity("swimming") == "pool"
        assert search_service._normalize_amenity("fitness") == "gym"

    def test_unknown_returns_none(self, search_service):
        assert search_service._normalize_amenity("jacuzzi") is None
        assert search_service._normalize_amenity("helipad") is None
        assert search_service._normalize_amenity("") is None


# ==================== _fallback_amenity_extraction ====================


class TestFallbackAmenityExtraction:
    """Tests for _fallback_amenity_extraction."""

    def test_single_amenity(self, search_service):
        result = search_service._fallback_amenity_extraction("I want a pool")
        assert "pool" in result

    def test_multiple_amenities(self, search_service):
        result = search_service._fallback_amenity_extraction(
            "apartment with swimming pool and gym and garden"
        )
        assert "pool" in result
        assert "gym" in result
        assert "garden" in result

    def test_no_amenities(self, search_service):
        result = search_service._fallback_amenity_extraction("3 bedroom house in Accra")
        assert result == []

    def test_multi_word_phrase_priority(self, search_service):
        result = search_service._fallback_amenity_extraction(
            "need a swimming pool and security system"
        )
        assert "pool" in result
        assert "security_system" in result

    def test_no_duplicates(self, search_service):
        result = search_service._fallback_amenity_extraction(
            "pool and swimming pool area"
        )
        assert result.count("pool") == 1


# ==================== _parse_query_with_regex ====================


class TestParseQueryWithRegex:
    """Tests for _parse_query_with_regex."""

    def test_bedrooms(self, search_service):
        parsed = search_service._parse_query_with_regex("3 bedroom apartment")
        assert parsed.min_bedrooms == 3
        assert parsed.max_bedrooms == 3

    def test_bathrooms(self, search_service):
        parsed = search_service._parse_query_with_regex("2 bathroom house")
        assert parsed.min_bathrooms == 2

    def test_bedrooms_shorthand(self, search_service):
        parsed = search_service._parse_query_with_regex("4 bed villa")
        assert parsed.min_bedrooms == 4

    def test_price_under(self, search_service):
        parsed = search_service._parse_query_with_regex("under $500k")
        assert parsed.max_price == 500_000
        assert parsed.min_price is None

    def test_price_above(self, search_service):
        parsed = search_service._parse_query_with_regex("above $200k")
        assert parsed.min_price == 200_000
        assert parsed.max_price is None

    def test_price_around(self, search_service):
        parsed = search_service._parse_query_with_regex("around $500k")
        assert parsed.min_price == pytest.approx(400_000)
        assert parsed.max_price == pytest.approx(600_000)

    def test_price_millions(self, search_service):
        parsed = search_service._parse_query_with_regex("under $1.2M")
        assert parsed.max_price == 1_200_000

    def test_price_standalone(self, search_service):
        parsed = search_service._parse_query_with_regex("apartment $300k")
        assert parsed.max_price == 300_000

    def test_locations_single(self, search_service):
        parsed = search_service._parse_query_with_regex("house in Accra")
        assert "Accra" in parsed.locations

    def test_locations_multiple(self, search_service):
        parsed = search_service._parse_query_with_regex("property in East Legon or Kumasi")
        assert "East Legon" in parsed.locations
        assert "Kumasi" in parsed.locations

    def test_locations_case_insensitive(self, search_service):
        parsed = search_service._parse_query_with_regex("house in accra")
        assert "Accra" in parsed.locations

    def test_property_type_apartment(self, search_service):
        parsed = search_service._parse_query_with_regex("2 bedroom apartment")
        assert PropertyType.APARTMENT in parsed.property_types

    def test_property_type_villa(self, search_service):
        parsed = search_service._parse_query_with_regex("luxury villa in Accra")
        assert PropertyType.VILLA in parsed.property_types

    def test_amenities_extraction(self, search_service):
        parsed = search_service._parse_query_with_regex(
            "apartment with pool and gym"
        )
        assert "pool" in parsed.must_have_amenities
        assert "gym" in parsed.must_have_amenities

    def test_pet_friendly(self, search_service):
        parsed = search_service._parse_query_with_regex("pet-friendly apartment")
        assert parsed.pet_policy == PetPolicy.ALLOWED

    def test_no_pets(self, search_service):
        parsed = search_service._parse_query_with_regex("no pets allowed house")
        assert parsed.pet_policy == PetPolicy.NOT_ALLOWED

    def test_furnished(self, search_service):
        parsed = search_service._parse_query_with_regex("furnished apartment in Accra")
        assert parsed.furnished is True

    def test_unfurnished(self, search_service):
        parsed = search_service._parse_query_with_regex("unfurnished house")
        assert parsed.furnished is False

    def test_intent_budget_focused(self, search_service):
        parsed = search_service._parse_query_with_regex("apartment under $300k")
        assert parsed.intent == SearchIntent.BUDGET_FOCUSED

    def test_intent_location_focused(self, search_service):
        parsed = search_service._parse_query_with_regex("property in Accra")
        assert parsed.intent == SearchIntent.LOCATION_FOCUSED

    def test_intent_investment(self, search_service):
        parsed = search_service._parse_query_with_regex("investment property with good ROI")
        assert parsed.intent == SearchIntent.INVESTMENT

    def test_intent_amenity_focused(self, search_service):
        parsed = search_service._parse_query_with_regex("place with pool and gym")
        assert parsed.intent == SearchIntent.AMENITY_FOCUSED

    def test_confidence_increases_with_more_fields(self, search_service):
        basic = search_service._parse_query_with_regex("show me properties")
        detailed = search_service._parse_query_with_regex(
            "3 bedroom apartment in Accra with pool under $500k furnished"
        )
        assert detailed.confidence > basic.confidence

    def test_semantic_keywords(self, search_service):
        parsed = search_service._parse_query_with_regex("luxury modern apartment")
        assert "luxury" in parsed.semantic_keywords
        assert "modern" in parsed.semantic_keywords

    def test_complex_query(self, search_service):
        parsed = search_service._parse_query_with_regex(
            "3 bedroom apartment in Accra with pool under $500k"
        )
        assert parsed.min_bedrooms == 3
        assert PropertyType.APARTMENT in parsed.property_types
        assert "Accra" in parsed.locations
        assert "pool" in parsed.must_have_amenities
        assert parsed.max_price == 500_000


# ==================== search() integration ====================


class TestSearch:
    """Integration tests for search() with mocked MongoDB."""

    @pytest.mark.asyncio
    async def test_search_returns_response(self, mock_database):
        """search() returns a valid SearchResponse."""
        service = PropertySearchService(mock_database)

        # Mock the collections
        props = [_make_property_doc()]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=props)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        service.properties_collection = MagicMock()
        service.properties_collection.find = MagicMock(return_value=mock_cursor)

        # Mock aggregation for alternative locations
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list = AsyncMock(return_value=[
            {"_id": "Accra", "count": 10},
            {"_id": "Kumasi", "count": 5},
        ])
        service.properties_collection.aggregate = MagicMock(return_value=mock_agg_cursor)

        # Mock analytics insert
        service.search_analytics_collection = MagicMock()
        service.search_analytics_collection.insert_one = AsyncMock()

        request = SearchRequest(query="3 bedroom apartment in Accra with pool under $500k")
        response = await service.search(request, organization_id=None)

        assert isinstance(response, SearchResponse)
        assert response.total == 1
        assert len(response.matches) == 1
        assert response.parsed_query is not None
        assert response.parsed_query.min_bedrooms == 3
        assert response.search_time_ms > 0
        assert response.limit == 20

    @pytest.mark.asyncio
    async def test_search_empty_query(self, mock_database):
        """search() with no query returns results with no parsed_query."""
        service = PropertySearchService(mock_database)

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        service.properties_collection = MagicMock()
        service.properties_collection.find = MagicMock(return_value=mock_cursor)

        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list = AsyncMock(return_value=[])
        service.properties_collection.aggregate = MagicMock(return_value=mock_agg_cursor)

        service.search_analytics_collection = MagicMock()
        service.search_analytics_collection.insert_one = AsyncMock()

        request = SearchRequest(query=None)
        response = await service.search(request, organization_id=None)

        assert isinstance(response, SearchResponse)
        assert response.parsed_query is None
        assert response.total == 0

    @pytest.mark.asyncio
    async def test_search_with_direct_filters(self, mock_database):
        """search() respects direct filters over NLP parsing."""
        service = PropertySearchService(mock_database)

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        service.properties_collection = MagicMock()
        service.properties_collection.find = MagicMock(return_value=mock_cursor)

        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list = AsyncMock(return_value=[])
        service.properties_collection.aggregate = MagicMock(return_value=mock_agg_cursor)

        service.search_analytics_collection = MagicMock()
        service.search_analytics_collection.insert_one = AsyncMock()

        filters = SearchFilters(
            min_bedrooms=4,
            max_price=800_000,
            locations=["Kumasi"],
        )
        request = SearchRequest(query="ignore this", filters=filters)
        response = await service.search(request, organization_id="org-123")

        assert isinstance(response, SearchResponse)
        # Filters should be the direct ones, not parsed from query
        assert response.applied_filters.get("min_bedrooms") == 4
        assert response.applied_filters.get("max_price") == 800_000

    @pytest.mark.asyncio
    async def test_search_suggests_refinements_on_zero_results(self, mock_database):
        """search() provides refinement suggestions when no results found."""
        service = PropertySearchService(mock_database)

        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        service.properties_collection = MagicMock()
        service.properties_collection.find = MagicMock(return_value=mock_cursor)

        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list = AsyncMock(return_value=[
            {"_id": "Accra", "count": 5},
        ])
        service.properties_collection.aggregate = MagicMock(return_value=mock_agg_cursor)

        service.search_analytics_collection = MagicMock()
        service.search_analytics_collection.insert_one = AsyncMock()

        request = SearchRequest(query="10 bedroom penthouse in Wa under $50k")
        response = await service.search(request, organization_id=None)

        assert len(response.suggested_refinements) > 0
        assert len(response.alternative_locations) > 0


# ==================== _build_filters ====================


class TestBuildFilters:
    """Tests for _build_filters."""

    def test_direct_filters_take_priority(self, search_service):
        direct = SearchFilters(min_bedrooms=5, max_price=1_000_000)
        result = search_service._build_filters(parsed_query=None, direct_filters=direct)
        assert result.min_bedrooms == 5

    def test_no_query_no_filters_returns_defaults(self, search_service):
        result = search_service._build_filters(parsed_query=None, direct_filters=None)
        assert isinstance(result, SearchFilters)
        assert result.limit == 20

    def test_parsed_query_converted_to_filters(self, search_service):
        parsed = search_service._parse_query_with_regex(
            "3 bedroom apartment in Accra with pool under $500k"
        )
        result = search_service._build_filters(parsed_query=parsed, direct_filters=None)
        assert result.min_bedrooms == 3
        assert result.max_price == 500_000
        assert result.amenities is not None
        assert "pool" in result.amenities


# ==================== _extract_semantic_keywords ====================


class TestExtractSemanticKeywords:
    """Tests for _extract_semantic_keywords."""

    def test_removes_stopwords(self, search_service):
        keywords = search_service._extract_semantic_keywords("I want a luxury apartment")
        assert "luxury" in keywords
        assert "apartment" in keywords
        assert "want" not in keywords
        assert "the" not in keywords

    def test_returns_query_if_all_stopwords(self, search_service):
        keywords = search_service._extract_semantic_keywords("I am")
        assert len(keywords) >= 1


# ==================== _determine_intent ====================


class TestDetermineIntent:
    """Tests for _determine_intent."""

    def test_investment_intent(self, search_service):
        intent = search_service._determine_intent(
            property_types=[], locations=[], amenities=[],
            min_price=None, max_price=None,
            q_lower="investment property with good roi",
        )
        assert intent == SearchIntent.INVESTMENT

    def test_urgent_intent(self, search_service):
        intent = search_service._determine_intent(
            property_types=[], locations=[], amenities=[],
            min_price=None, max_price=None,
            q_lower="need apartment asap",
        )
        assert intent == SearchIntent.URGENT

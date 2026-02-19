"""
AI Property Search Service

Natural language property search with semantic understanding and intelligent filtering.
"""

import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchFilters,
    ParsedSearchQuery,
    PropertyMatch,
    SearchIntent,
    PropertyType,
    PetPolicy,
    PropertyEmbedding,
    SearchAnalytics
)
from app.models.property import Property

import logging
import re

logger = logging.getLogger(__name__)

# Amenity normalization mapping
# Maps natural language terms to PropertyFeatures field names
AMENITY_MAPPING = {
    # Pool variants
    "pool": "pool",
    "swimming pool": "pool",
    "swim pool": "pool",
    "pool area": "pool",

    # Gym variants
    "gym": "gym",
    "fitness center": "gym",
    "fitness room": "gym",
    "workout room": "gym",
    "exercise room": "gym",

    # Garden variants
    "garden": "garden",
    "yard": "garden",
    "backyard": "garden",
    "outdoor space": "garden",

    # Parking variants
    "parking": "parking_spaces",
    "garage": "parking_spaces",
    "parking space": "parking_spaces",
    "parking spot": "parking_spaces",

    # Balcony variants
    "balcony": "balcony",
    "terrace": "balcony",
    "patio": "balcony",

    # Elevator
    "elevator": "elevator",
    "lift": "elevator",

    # AC
    "ac": "air_conditioning",
    "air conditioning": "air_conditioning",
    "air-conditioning": "air_conditioning",
    "cooling": "air_conditioning",

    # Heating
    "heating": "heating",
    "hvac": "heating",

    # Security
    "security": "security_system",
    "security system": "security_system",
    "alarm": "security_system",
    "security alarm": "security_system",

    # Storage
    "storage": "storage",
    "storage unit": "storage",

    # Fireplace
    "fireplace": "fireplace",
    "wood stove": "fireplace",
}


class PropertySearchService:
    """
    AI-powered property search with NLP query parsing and semantic search.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.properties_collection = database["properties"]
        self.embeddings_collection = database["property_embeddings"]
        self.search_analytics_collection = database["search_analytics"]
    async def _parse_query(self, query: str) -> ParsedSearchQuery:
        """
        Parse natural language query using simple regex extraction (Standalone Mode).

        Args:
            query: Natural language search query

        Returns:
            Parsed structured query
        """
        # Try fallback amenity extraction using regex
        fallback_amenities = self._fallback_amenity_extraction(query)
        
        # Simple extraction for other fields could go here
        # For now, we rely on the client to use filters or simple text search

        # Fallback: return basic parsed query with fallback amenities
        return ParsedSearchQuery(
            original_query=query,
            intent=SearchIntent.BROWSE,
            confidence=0.5,
            must_have_amenities=fallback_amenities,
            semantic_keywords=[query],
            parsed_at=datetime.utcnow()
        )


    def _build_filters(
        self,
        parsed_query: Optional[ParsedSearchQuery],
        direct_filters: Optional[SearchFilters]
    ) -> SearchFilters:
        """
        Build search filters from parsed query or direct filters.

        Args:
            parsed_query: Parsed NLP query
            direct_filters: Direct filters from UI

        Returns:
            Unified search filters
        """
        if direct_filters:
            return direct_filters

        if not parsed_query:
            return SearchFilters()

        # Normalize and validate amenities
        normalized_amenities = []
        if parsed_query.must_have_amenities:
            for amenity in parsed_query.must_have_amenities:
                normalized = self._normalize_amenity(amenity)
                if normalized and normalized not in normalized_amenities:
                    normalized_amenities.append(normalized)

        # Log if amenities were extracted and normalized
        if parsed_query.must_have_amenities:
            logger.info(
                f"Amenities extracted: {parsed_query.must_have_amenities} → "
                f"Normalized: {normalized_amenities}"
            )

        # Convert parsed query to filters
        return SearchFilters(
            property_types=parsed_query.property_types or None,
            locations=parsed_query.locations or None,
            min_price=parsed_query.min_price,
            max_price=parsed_query.max_price,
            min_bedrooms=parsed_query.min_bedrooms,
            max_bedrooms=parsed_query.max_bedrooms,
            min_bathrooms=parsed_query.min_bathrooms,
            min_sqft=parsed_query.min_sqft,
            max_sqft=parsed_query.max_sqft,
            amenities=normalized_amenities or None,
            pet_policy=parsed_query.pet_policy,
            furnished=parsed_query.furnished,
            sort_by="created_at",
            sort_order="desc",
            limit=20,
            offset=0
        )

    async def _filter_search(
        self,
        filters: SearchFilters,
        organization_id: str,
        search_text: Optional[str] = None
    ) -> List[PropertyMatch]:
        """
        Traditional filter-based search with optional text search.

        Args:
            filters: Search filters
            organization_id: Organization ID
            search_text: Optional text to search in name/description fields

        Returns:
            List of matching properties
        """
        # Build MongoDB query
        # Reason: Only filter by organization if authenticated
        # For public users (organization_id=None), show ALL active properties
        # For authenticated users, scope to their organization
        query: Dict[str, Any] = {"status": "active"}

        if organization_id is not None:
            query["organization_id"] = organization_id

        # Add text search on name/description if provided
        if search_text:
            query["$text"] = {"$search": search_text}
            logger.info(f"Added text search for: '{search_text}'")

        if filters.property_types:
            query["property_type"] = {"$in": [pt.value for pt in filters.property_types]}

        if filters.locations:
            # Search in city, state, or neighborhood
            query["$or"] = [
                {"location.city": {"$in": filters.locations}},
                {"location.state": {"$in": filters.locations}},
                {"location.neighborhood": {"$in": filters.locations}}
            ]

        # Price range
        if filters.min_price is not None or filters.max_price is not None:
            price_query = {}
            if filters.min_price is not None:
                price_query["$gte"] = filters.min_price
            if filters.max_price is not None:
                price_query["$lte"] = filters.max_price
            query["financial.price_usd"] = price_query

        # Bedrooms
        if filters.min_bedrooms is not None or filters.max_bedrooms is not None:
            bedroom_query = {}
            if filters.min_bedrooms is not None:
                bedroom_query["$gte"] = filters.min_bedrooms
            if filters.max_bedrooms is not None:
                bedroom_query["$lte"] = filters.max_bedrooms
            query["features.bedrooms"] = bedroom_query

        # Bathrooms
        if filters.min_bathrooms is not None:
            query["features.bathrooms"] = {"$gte": filters.min_bathrooms}

        # Square footage
        if filters.min_sqft is not None or filters.max_sqft is not None:
            sqft_query = {}
            if filters.min_sqft is not None:
                sqft_query["$gte"] = filters.min_sqft
            if filters.max_sqft is not None:
                sqft_query["$lte"] = filters.max_sqft
            query["features.sqft"] = sqft_query

        # Amenities (all must be present)
        if filters.amenities:
            amenity_queries = []
            for amenity in filters.amenities:
                # Validate amenity is a known field
                if amenity in ["pool", "gym", "garden", "balcony", "elevator",
                               "air_conditioning", "heating", "fireplace",
                               "security_system", "storage", "furnished"]:
                    # Boolean amenity field
                    amenity_queries.append({f"features.{amenity}": True})
                elif amenity == "parking_spaces":
                    # Parking is numeric, check > 0
                    amenity_queries.append({"features.parking_spaces": {"$gt": 0}})
                else:
                    logger.warning(f"Invalid amenity field '{amenity}' in filter - skipping")

            if amenity_queries:
                query["$and"] = amenity_queries
                logger.info(f"Applied amenity filters: {amenity_queries}")

        # Pet policy
        if filters.pet_policy:
            query["features.pet_policy"] = filters.pet_policy.value

        # Furnished
        if filters.furnished is not None:
            query["features.furnished"] = filters.furnished

        # Execute query with sorting
        if search_text:
            # When text search is used, sort by relevance score first
            cursor = self.properties_collection.find(
                query,
                {"score": {"$meta": "textScore"}}  # Include text score
            ).sort([
                ("score", {"$meta": "textScore"}),  # Sort by relevance
                (filters.sort_by, -1 if filters.sort_order == "desc" else 1)
            ]).skip(filters.offset).limit(filters.limit)
        else:
            # Normal sorting when no text search
            cursor = self.properties_collection.find(query).sort(
                filters.sort_by, -1 if filters.sort_order == "desc" else 1
            ).skip(filters.offset).limit(filters.limit)

        properties = await cursor.to_list(length=filters.limit)

        # Convert to PropertyMatch
        matches = []
        for prop in properties:
            # Reason: Convert ObjectId to string 'id' field for consistency with PropertyService
            # Raw MongoDB documents have _id (ObjectId) but not id (string)
            # Remove _id to avoid Pydantic serialization errors (ObjectId is not JSON serializable)
            if "_id" in prop:
                prop["id"] = str(prop["_id"])
                del prop["_id"]  # Remove to avoid serialization errors

            match_reasons = self._calculate_match_reasons(prop, filters)
            missing_criteria = self._calculate_missing_criteria(prop, filters)

            # Add text match reason if text search was used
            if search_text:
                if search_text.lower() in prop.get("name", "").lower():
                    match_reasons.insert(0, f"Name matches: '{search_text}'")
                elif search_text.lower() in prop.get("description", "").lower():
                    match_reasons.insert(0, f"Description matches: '{search_text}'")
                else:
                    match_reasons.insert(0, f"Text match: '{search_text}'")

            matches.append(PropertyMatch(
                property_id=prop["id"],
                relevance_score=self._calculate_filter_score(prop, filters),
                filter_score=self._calculate_filter_score(prop, filters),
                match_reasons=match_reasons,
                missing_criteria=missing_criteria,
                property_data=prop
            ))

        return matches

    async def _semantic_search(
        self,
        parsed_query: ParsedSearchQuery,
        filters: SearchFilters,
        organization_id: str
    ) -> List[PropertyMatch]:
        """
        Semantic vector search using embeddings.

        Args:
            parsed_query: Parsed query with keywords
            filters: Additional filters
            organization_id: Organization ID

        Returns:
            List of matching properties with semantic scores
        """
        # Generate query embedding
        query_text = " ".join(parsed_query.semantic_keywords)
        # Note: In production, you would call OpenAI embedding API here
        # For now, fallback to filter search
        # query_embedding = await self._generate_embedding(query_text)

        # TODO: Implement vector search with MongoDB Atlas Search or pgvector
        # For now, use filter search with text search on query
        return await self._filter_search(filters, organization_id, search_text=query_text)

    def _calculate_filter_score(self, property_doc: Dict[str, Any], filters: SearchFilters) -> float:
        """
        Calculate how well property matches filters.

        Args:
            property_doc: Property document
            filters: Search filters

        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        total_criteria = 0
        matched_criteria = 0

        # Property type match
        if filters.property_types:
            total_criteria += 1
            if property_doc.get("property_type") in [pt.value for pt in filters.property_types]:
                matched_criteria += 1

        # Price range match
        if filters.min_price or filters.max_price:
            total_criteria += 1
            price = property_doc.get("financial", {}).get("price_usd", 0)
            in_range = True
            if filters.min_price and price < filters.min_price:
                in_range = False
            if filters.max_price and price > filters.max_price:
                in_range = False
            if in_range:
                matched_criteria += 1

        # Bedroom match
        if filters.min_bedrooms or filters.max_bedrooms:
            total_criteria += 1
            bedrooms = property_doc.get("features", {}).get("bedrooms", 0)
            in_range = True
            if filters.min_bedrooms and bedrooms < filters.min_bedrooms:
                in_range = False
            if filters.max_bedrooms and bedrooms > filters.max_bedrooms:
                in_range = False
            if in_range:
                matched_criteria += 1

        if total_criteria > 0:
            score = matched_criteria / total_criteria

        return score

    def _calculate_match_reasons(self, property_doc: Dict[str, Any], filters: SearchFilters) -> List[str]:
        """Calculate why this property matches."""
        reasons = []

        if filters.property_types and property_doc.get("property_type") in [pt.value for pt in filters.property_types]:
            reasons.append(f"Property type: {property_doc.get('property_type')}")

        if filters.min_bedrooms:
            bedrooms = property_doc.get("features", {}).get("bedrooms", 0)
            if bedrooms >= filters.min_bedrooms:
                reasons.append(f"{bedrooms} bedrooms")

        if filters.amenities:
            features = property_doc.get("features", {})
            matched_amenities = [a for a in filters.amenities if features.get(a)]
            if matched_amenities:
                reasons.append(f"Has: {', '.join(matched_amenities)}")

        return reasons

    def _calculate_missing_criteria(self, property_doc: Dict[str, Any], filters: SearchFilters) -> List[str]:
        """Calculate what criteria are not met."""
        missing = []

        if filters.amenities:
            features = property_doc.get("features", {})
            missing_amenities = [a for a in filters.amenities if not features.get(a)]
            if missing_amenities:
                missing.append(f"Missing: {', '.join(missing_amenities)}")

        return missing

    def _generate_refinements(self, parsed_query: Optional[ParsedSearchQuery], results_count: int) -> List[str]:
        """Generate suggested search refinements."""
        suggestions = []

        if results_count == 0:
            suggestions.append("Try increasing your budget range")
            suggestions.append("Expand your location search")
            suggestions.append("Reduce bedroom requirements")
        elif results_count > 50:
            suggestions.append("Add more specific location")
            suggestions.append("Narrow price range")
            suggestions.append("Specify preferred amenities")

        return suggestions

    async def _get_alternative_locations(self, filters: SearchFilters, organization_id: str) -> List[str]:
        """Get alternative locations with available properties."""
        # Find locations with active properties
        # Reason: Only filter by organization if authenticated
        # Build match query conditionally to handle public users (organization_id=None)
        match_query = {"status": "active"}

        if organization_id is not None:
            match_query["organization_id"] = organization_id

        pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$location.city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]

        results = await self.properties_collection.aggregate(pipeline).to_list(length=5)
        return [r["_id"] for r in results if r["_id"]]

    async def _log_search(
        self,
        query: str,
        parsed_query: Optional[ParsedSearchQuery],
        results_count: int,
        top_result_id: Optional[str],
        search_time_ms: float,
        organization_id: str,
        user_id: Optional[str]
    ):
        """Log search analytics."""
        import uuid

        analytics = SearchAnalytics(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            query=query,
            parsed_query=parsed_query,
            results_count=results_count,
            top_result_id=top_result_id,
            search_time_ms=search_time_ms,
            user_id=user_id,
            created_at=datetime.utcnow()
        )

        await self.search_analytics_collection.insert_one(analytics.dict())

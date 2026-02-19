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
from apps.shared.services.llm_provider_service import LLMProviderService, ChatRequest, ChatMessage
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
        self.llm_service = LLMProviderService()

    async def search(
        self,
        search_request: SearchRequest,
        organization_id: str,
        user_id: Optional[str] = None
    ) -> SearchResponse:
        """
        Main search method.

        Args:
            search_request: Search request
            organization_id: Organization ID
            user_id: User ID (optional)

        Returns:
            Search results with matches
        """
        start_time = time.time()

        # Parse natural language query if provided
        parsed_query = None
        if search_request.query:
            parsed_query = await self._parse_query(search_request.query)

        # Build filters from parsed query or direct filters
        filters = self._build_filters(parsed_query, search_request.filters)

        # Execute search
        if search_request.use_semantic_search and parsed_query and parsed_query.semantic_keywords:
            # Semantic search (vector search)
            matches = await self._semantic_search(
                parsed_query,
                filters,
                organization_id
            )
        else:
            # Traditional filter-based search with text search
            search_text = search_request.query if search_request.query else None
            matches = await self._filter_search(
                filters,
                organization_id,
                search_text=search_text
            )

        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000

        # Generate suggestions
        suggested_refinements = self._generate_refinements(parsed_query, len(matches))
        alternative_locations = await self._get_alternative_locations(filters, organization_id)

        # Log analytics
        await self._log_search(
            query=search_request.query or "",
            parsed_query=parsed_query,
            results_count=len(matches),
            top_result_id=matches[0].property_id if matches else None,
            search_time_ms=search_time_ms,
            organization_id=organization_id,
            user_id=user_id
        )

        return SearchResponse(
            matches=matches,
            total=len(matches),
            parsed_query=parsed_query,
            applied_filters=filters.dict(exclude_none=True) if filters else {},
            search_time_ms=search_time_ms,
            used_semantic_search=search_request.use_semantic_search and parsed_query is not None,
            suggested_refinements=suggested_refinements,
            alternative_locations=alternative_locations,
            limit=filters.limit if filters else 20,
            offset=filters.offset if filters else 0
        )

    def _normalize_amenity(self, amenity: str) -> Optional[str]:
        """
        Normalize amenity name to match PropertyFeatures field name.

        Args:
            amenity: Natural language amenity name

        Returns:
            Normalized field name or None if not recognized
        """
        # Convert to lowercase and strip whitespace
        amenity_clean = amenity.lower().strip()

        # Direct lookup
        if amenity_clean in AMENITY_MAPPING:
            return AMENITY_MAPPING[amenity_clean]

        # Try partial matching for common words
        for phrase, field_name in AMENITY_MAPPING.items():
            if phrase in amenity_clean or amenity_clean in phrase:
                return field_name

        # Log unrecognized amenity for debugging
        logger.warning(f"Unrecognized amenity: '{amenity}' - not mapped to any field")
        return None

    def _fallback_amenity_extraction(self, query: str) -> List[str]:
        """
        Fallback: Extract amenities using regex if Gemini fails.

        Args:
            query: Natural language query

        Returns:
            List of extracted amenity field names
        """
        query_lower = query.lower()
        extracted = []

        # Check for common amenity phrases
        amenity_patterns = {
            "pool": r'\b(pool|swimming|swim)\b',
            "gym": r'\b(gym|fitness|workout)\b',
            "garden": r'\b(garden|yard|outdoor space)\b',
            "parking_spaces": r'\b(parking|garage)\b',
            "balcony": r'\b(balcony|terrace|patio)\b',
            "elevator": r'\b(elevator|lift)\b',
            "air_conditioning": r'\b(ac|air condition|cooling)\b',
            "security_system": r'\b(security|alarm)\b',
            "furnished": r'\b(furnished|furniture)\b',
        }

        for field_name, pattern in amenity_patterns.items():
            if re.search(pattern, query_lower):
                extracted.append(field_name)

        if extracted:
            logger.info(f"Fallback extraction found amenities: {extracted}")

        return extracted

    async def _parse_query(self, query: str) -> ParsedSearchQuery:
        """
        Parse natural language query using LLM.

        Args:
            query: Natural language search query

        Returns:
            Parsed structured query
        """
        # System prompt for NLP parsing
        system_prompt = """You are a real estate search assistant. Parse the user's search query and extract structured information.

Extract:
1. **Intent**: browse, specific_property, investment, urgent, budget_focused, location_focused, or amenity_focused
2. **Property types**: apartment, house, villa, penthouse, loft, townhouse, land, commercial
3. **Locations**: cities, neighborhoods, areas (be flexible with spellings)
4. **Price range**: min and max price in USD (convert if other currency mentioned)
5. **Bedrooms**: min and max bedrooms
6. **Bathrooms**: minimum bathrooms
7. **Square footage**: min and max sqft
8. **Amenities (must_have_amenities & nice_to_have_amenities)**:
   - Extract amenities mentioned in the query
   - Use EXACT field names from this list ONLY:
     * "pool" - swimming pool, pool area
     * "gym" - fitness center, workout room, exercise room
     * "garden" - yard, outdoor space, backyard
     * "balcony" - terrace, patio
     * "parking_spaces" - parking, garage, parking spot
     * "elevator" - lift
     * "air_conditioning" - AC, cooling, air-conditioning
     * "heating" - HVAC
     * "fireplace" - wood stove
     * "security_system" - security, alarm, security alarm
     * "storage" - storage unit
     * "furnished" - furniture included

   - Place REQUIRED amenities (explicit "must have", "need", "require", "with") in must_have_amenities
   - Place PREFERRED amenities (nice to have, prefer, preferably) in nice_to_have_amenities

   Examples:
   - "apartment with pool" → must_have_amenities: ["pool"]
   - "house with pool and gym" → must_have_amenities: ["pool", "gym"]
   - "preferably with balcony" → nice_to_have_amenities: ["balcony"]
   - "need parking" → must_have_amenities: ["parking_spaces"]
   - "apartment with swimming pool and security" → must_have_amenities: ["pool", "security_system"]

9. **Pet policy**: allowed, not_allowed, or conditional
10. **Furnished**: true or false (only if explicitly mentioned; amenities list handles "furnished" too)
11. **Keywords**: important semantic keywords for vector search

IMPORTANT: Return valid JSON with this EXACT structure:
{
    "intent": "browse",
    "property_types": ["apartment"],
    "locations": ["Accra"],
    "min_price": null,
    "max_price": null,
    "min_bedrooms": null,
    "max_bedrooms": null,
    "min_bathrooms": null,
    "min_sqft": null,
    "max_sqft": null,
    "must_have_amenities": ["pool"],
    "nice_to_have_amenities": [],
    "pet_policy": null,
    "furnished": null,
    "keywords": ["apartment", "Accra", "pool"],
    "confidence": 0.9,
    "language": "en"
}

Return JSON with these fields. Use null for unspecified fields. Be generous with semantic keywords."""

        # Call LLM
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Parse this property search query: \"{query}\"")
        ]

        try:
            # Create chat request
            chat_request = ChatRequest(
                model_id="gemini-2.0-flash-exp",  # Fast and cheap
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )

            # Call LLM service
            chat_response = await self.llm_service.chat(
                user_id="system",  # System user for search parsing
                request=chat_request,
                skip_billing=True  # Don't bill for internal search parsing
            )

            # Parse JSON response
            response_text = chat_response.message
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text.strip()

            parsed_data = json.loads(json_text)

            # Build ParsedSearchQuery
            parsed_query = ParsedSearchQuery(
                original_query=query,
                intent=SearchIntent(parsed_data.get("intent", "browse")),
                confidence=parsed_data.get("confidence", 0.8),
                property_types=[PropertyType(pt) for pt in parsed_data.get("property_types", [])],
                locations=parsed_data.get("locations", []),
                min_price=parsed_data.get("min_price"),
                max_price=parsed_data.get("max_price"),
                min_bedrooms=parsed_data.get("min_bedrooms"),
                max_bedrooms=parsed_data.get("max_bedrooms"),
                min_bathrooms=parsed_data.get("min_bathrooms"),
                min_sqft=parsed_data.get("min_sqft"),
                max_sqft=parsed_data.get("max_sqft"),
                must_have_amenities=parsed_data.get("must_have_amenities", []),
                nice_to_have_amenities=parsed_data.get("nice_to_have_amenities", []),
                pet_policy=PetPolicy(parsed_data["pet_policy"]) if parsed_data.get("pet_policy") else None,
                furnished=parsed_data.get("furnished"),
                semantic_keywords=parsed_data.get("keywords", [query]),
                language=parsed_data.get("language", "en"),
                parsed_at=datetime.utcnow()
            )

            # Log what Gemini extracted for debugging
            logger.info(
                f"Gemini parsed query '{query}': "
                f"types={parsed_query.property_types}, "
                f"locations={parsed_query.locations}, "
                f"must_have_amenities={parsed_query.must_have_amenities}, "
                f"nice_to_have_amenities={parsed_query.nice_to_have_amenities}"
            )

            return parsed_query

        except Exception as e:
            # Log parsing failure
            logger.error(f"Failed to parse query '{query}': {str(e)}")

            # Try to log what Gemini returned for debugging
            try:
                if 'response_text' in locals():
                    logger.error(f"Gemini response was: {response_text[:200]}")
            except:
                pass

            # Try fallback amenity extraction using regex
            fallback_amenities = self._fallback_amenity_extraction(query)

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

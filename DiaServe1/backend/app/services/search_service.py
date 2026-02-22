"""
AI Property Search Service

Natural language property search with semantic understanding and intelligent filtering.
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

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
    SearchAnalytics
)
from app.models.property import Property

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

# Known Ghana locations for regex matching
GHANA_LOCATIONS = [
    # Major cities
    "Accra", "Kumasi", "Tamale", "Takoradi", "Cape Coast",
    "Tema", "Sunyani", "Ho", "Koforidua", "Wa",
    # Popular neighborhoods / areas in Accra
    "East Legon", "Airport Residential", "Cantonments", "Labone",
    "Osu", "Ridge", "Roman Ridge", "Dzorwulu", "Abelemkpe",
    "Tesano", "North Legon", "Adenta", "Madina", "Spintex",
    "Teshie", "Nungua", "Dansoman", "Kasoa", "Sakumono",
    "Community 25", "Tema Community", "Ashongman",
    # Popular areas in Kumasi
    "Ahodwo", "Nhyiaeso", "Adum", "Bantama",
    # Regions / broader areas
    "Greater Accra", "Ashanti", "Western Region", "Eastern Region",
    "Trasacco", "Airport Hills", "Trassaco Valley",
]

# Stopwords for semantic keyword extraction
STOPWORDS = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "they", "them", "the", "a", "an", "and", "or", "but", "in", "on",
    "at", "to", "for", "of", "with", "by", "from", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "can", "may", "might",
    "need", "want", "looking", "search", "find", "show", "get", "give",
    "like", "around", "about", "near", "close", "under", "over", "above",
    "below", "between", "that", "this", "those", "these", "some", "any",
    "all", "each", "every", "not", "no", "than", "very", "just", "also",
    "more", "most", "less", "am", "up", "so", "if", "what", "which",
    "who", "whom", "when", "where", "how", "much", "many",
}


ALLOWED_SORT_FIELDS = {
    "created_at", "financial.price_usd", "features.bedrooms",
    "features.bathrooms", "features.sqft", "name",
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

        # Lazy-init Gemini (import only if available)
        self._gemini = None
        self._gemini_checked = False

    @property
    def gemini(self):
        """Lazy-load GeminiService to avoid import errors if not installed."""
        if not self._gemini_checked:
            self._gemini_checked = True
            try:
                from app.integration.gemini_client import GeminiService
                self._gemini = GeminiService()
            except Exception as e:
                logger.warning(f"Gemini service not available: {e}")
        return self._gemini

    # ==================== Public API ====================

    async def search(
        self,
        search_request: SearchRequest,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SearchResponse:
        """
        Main search orchestration method.

        1. Parse NLP query (if provided)
        2. Build filters from parsed query or direct filters
        3. Execute filter search with text search from semantic keywords
        4. Sort by relevance_score descending
        5. Generate refinement suggestions
        6. Get alternative locations if few results
        7. Log search analytics (non-blocking)
        8. Return SearchResponse
        """
        start_time = time.time()

        # Step 1: Parse NLP query
        parsed_query: Optional[ParsedSearchQuery] = None
        if search_request.query:
            parsed_query = await self._parse_query(search_request.query)

        # Step 2: Build filters
        filters = self._build_filters(parsed_query, search_request.filters)

        # Step 3: Execute search
        search_text = None
        if parsed_query and parsed_query.semantic_keywords:
            search_text = " ".join(parsed_query.semantic_keywords)

        matches = await self._filter_search(filters, organization_id, search_text=search_text)

        # Step 4: Sort by relevance_score descending
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        # Step 5: Refinement suggestions
        refinements = self._generate_refinements(parsed_query, len(matches))

        # Step 6: Alternative locations if few results
        alternative_locations: List[str] = []
        if len(matches) < 3:
            alternative_locations = await self._get_alternative_locations(
                filters, organization_id
            )

        # Step 7: Log analytics (non-blocking, catch errors)
        query_text = search_request.query or ""
        top_result_id = matches[0].property_id if matches else None
        search_time_ms = (time.time() - start_time) * 1000

        try:
            await self._log_search(
                query=query_text,
                parsed_query=parsed_query,
                results_count=len(matches),
                top_result_id=top_result_id,
                search_time_ms=search_time_ms,
                organization_id=organization_id,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Failed to log search analytics: {e}")

        # Step 8: Build response
        applied_filters = filters.model_dump(exclude_none=True)

        return SearchResponse(
            matches=matches,
            total=len(matches),
            parsed_query=parsed_query,
            applied_filters=applied_filters,
            search_time_ms=round(search_time_ms, 2),
            used_semantic_search=False,
            suggested_refinements=refinements,
            alternative_locations=alternative_locations,
            limit=filters.limit,
            offset=filters.offset,
        )

    # ==================== Query Parsing ====================

    async def _parse_query(self, query: str) -> ParsedSearchQuery:
        """
        Parse natural language query.

        Tries Gemini first (if available), falls back to regex parser.
        """
        # Try Gemini-powered parsing
        if self.gemini and self.gemini.is_available():
            try:
                result = await self._parse_query_with_gemini(query)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"Gemini parsing failed, falling back to regex: {e}")

        # Fallback to deterministic regex parser
        return self._parse_query_with_regex(query)

    def _parse_query_with_regex(self, query: str) -> ParsedSearchQuery:
        """
        Deterministic regex-based query parser.

        Extracts property types, bedrooms, bathrooms, price, locations,
        amenities, pet policy, furnished status, and intent from natural
        language queries.
        """
        q_lower = query.lower()

        # --- Property types ---
        property_types: List[PropertyType] = []
        for pt in PropertyType:
            if re.search(rf"\b{pt.value}\b", q_lower):
                property_types.append(pt)

        # --- Bedrooms ---
        min_bedrooms: Optional[int] = None
        max_bedrooms: Optional[int] = None
        bed_match = re.search(
            r"(\d+)\s*(?:bed(?:room)?s?|br|bd)", q_lower
        )
        if bed_match:
            min_bedrooms = int(bed_match.group(1))
            max_bedrooms = int(bed_match.group(1))

        # --- Bathrooms ---
        min_bathrooms: Optional[int] = None
        bath_match = re.search(
            r"(\d+)\s*(?:bath(?:room)?s?|ba)", q_lower
        )
        if bath_match:
            min_bathrooms = int(bath_match.group(1))

        # --- Price ---
        min_price: Optional[float] = None
        max_price: Optional[float] = None

        def _parse_price_value(match_str: str) -> Optional[float]:
            """Convert price string like '500k', '1.2M', '200000' to float."""
            try:
                clean = match_str.strip().replace(",", "").replace("$", "")
                multiplier = 1.0
                if clean.lower().endswith("k"):
                    multiplier = 1_000
                    clean = clean[:-1]
                elif clean.lower().endswith("m"):
                    multiplier = 1_000_000
                    clean = clean[:-1]
                return float(clean) * multiplier
            except (ValueError, IndexError):
                return None

        # "under $500k", "below $1M", "less than $200000", "max $500k"
        under_match = re.search(
            r"(?:under|below|less\s+than|max|up\s+to|within|budget)\s*\$?([\d,.]+[kKmM]?)",
            q_lower,
        )
        # "above $200k", "over $300k", "more than $100k", "min $500k", "at least $200k"
        above_match = re.search(
            r"(?:above|over|more\s+than|min(?:imum)?|at\s+least|from|starting)\s*\$?([\d,.]+[kKmM]?)",
            q_lower,
        )
        # "around $500k", "about $400k", "approximately $300k" -> +-20% range
        around_match = re.search(
            r"(?:around|about|approximately|roughly|~)\s*\$?([\d,.]+[kKmM]?)",
            q_lower,
        )
        # "$500k" or "$1.2M" standalone price
        standalone_price = re.search(
            r"\$([\d,.]+[kKmM]?)", q_lower
        )

        if under_match:
            max_price = _parse_price_value(under_match.group(1))
        if above_match:
            min_price = _parse_price_value(above_match.group(1))
        if around_match and min_price is None and max_price is None:
            center = _parse_price_value(around_match.group(1))
            min_price = center * 0.8
            max_price = center * 1.2
        # If only standalone $ with no directional word, treat as max
        if standalone_price and min_price is None and max_price is None:
            max_price = _parse_price_value(standalone_price.group(1))

        # --- Locations ---
        locations: List[str] = []
        for loc in GHANA_LOCATIONS:
            if re.search(rf"\b{re.escape(loc)}\b", query, re.IGNORECASE):
                locations.append(loc)

        # --- Amenities ---
        amenities = self._fallback_amenity_extraction(query)

        # --- Pet policy ---
        pet_policy: Optional[PetPolicy] = None
        if re.search(r"\bpet[\s-]?friendly\b", q_lower):
            pet_policy = PetPolicy.ALLOWED
        elif re.search(r"\bno\s+pets?\b", q_lower):
            pet_policy = PetPolicy.NOT_ALLOWED

        # --- Furnished ---
        furnished: Optional[bool] = None
        if re.search(r"\bunfurnished\b", q_lower):
            furnished = False
        elif re.search(r"\bfurnished\b", q_lower):
            furnished = True

        # --- Intent ---
        intent = self._determine_intent(
            property_types=property_types,
            locations=locations,
            amenities=amenities,
            min_price=min_price,
            max_price=max_price,
            q_lower=q_lower,
        )

        # --- Confidence ---
        extracted_count = sum([
            bool(property_types),
            bool(locations),
            bool(amenities),
            min_bedrooms is not None,
            min_price is not None or max_price is not None,
            pet_policy is not None,
            furnished is not None,
        ])
        confidence = min(0.5 + extracted_count * 0.1, 1.0)

        # --- Semantic keywords ---
        semantic_keywords = self._extract_semantic_keywords(query)

        return ParsedSearchQuery(
            original_query=query,
            intent=intent,
            confidence=confidence,
            property_types=property_types,
            locations=locations,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            min_bathrooms=min_bathrooms,
            must_have_amenities=amenities,
            pet_policy=pet_policy,
            furnished=furnished,
            semantic_keywords=semantic_keywords,
            parsed_at=datetime.now(timezone.utc),
        )

    async def _parse_query_with_gemini(
        self, query: str
    ) -> Optional[ParsedSearchQuery]:
        """
        Parse query using Gemini AI for more accurate NLP extraction.

        Returns None on any failure so caller falls back to regex.
        """
        # Sanitize user input: truncate and escape quotes to limit prompt injection
        sanitized = query[:500].replace('"', "'")
        prompt = f"""You are a real estate search query parser. Extract structured search parameters from the following natural language query. Return ONLY valid JSON with no markdown formatting.

Query: "{sanitized}"

Return JSON with these fields (omit fields that aren't mentioned):
{{
  "property_types": ["apartment", "house", "villa", "penthouse", "loft", "townhouse", "land", "commercial"],
  "locations": ["list of city/neighborhood names"],
  "min_price": number or null,
  "max_price": number or null,
  "min_bedrooms": number or null,
  "max_bedrooms": number or null,
  "min_bathrooms": number or null,
  "amenities": ["pool", "gym", "garden", "parking", "balcony", "elevator", "air_conditioning", "heating", "security", "storage", "fireplace"],
  "pet_policy": "allowed" or "not_allowed" or null,
  "furnished": true or false or null,
  "intent": "browse" or "budget_focused" or "location_focused" or "amenity_focused" or "investment" or "urgent"
}}

Only include fields that are clearly stated or strongly implied in the query."""

        result = await self.gemini.generate_content(
            prompt=prompt,
            temperature=0.1,
            max_output_tokens=500,
        )

        if not result.get("success"):
            return None

        content = result.get("content", "").strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Gemini returned invalid JSON: {content[:200]}")
            return None

        # Validate and construct ParsedSearchQuery
        property_types: List[PropertyType] = []
        for pt_str in data.get("property_types", []):
            try:
                property_types.append(PropertyType(pt_str))
            except ValueError:
                pass

        pet_policy: Optional[PetPolicy] = None
        if data.get("pet_policy"):
            try:
                pet_policy = PetPolicy(data["pet_policy"])
            except ValueError:
                pass

        intent = SearchIntent.BROWSE
        if data.get("intent"):
            try:
                intent = SearchIntent(data["intent"])
            except ValueError:
                pass

        amenities = []
        for a in data.get("amenities", []):
            normalized = self._normalize_amenity(a)
            if normalized:
                amenities.append(normalized)

        return ParsedSearchQuery(
            original_query=query,
            intent=intent,
            confidence=0.85,
            property_types=property_types,
            locations=data.get("locations", []),
            min_price=data.get("min_price"),
            max_price=data.get("max_price"),
            min_bedrooms=data.get("min_bedrooms"),
            max_bedrooms=data.get("max_bedrooms"),
            min_bathrooms=data.get("min_bathrooms"),
            must_have_amenities=amenities,
            pet_policy=pet_policy,
            furnished=data.get("furnished"),
            semantic_keywords=self._extract_semantic_keywords(query),
            parsed_at=datetime.now(timezone.utc),
        )

    # ==================== Helper Methods ====================

    def _normalize_amenity(self, amenity: str) -> Optional[str]:
        """
        Look up amenity string in AMENITY_MAPPING, return canonical field name.

        Falls back to partial substring match if no exact match.
        Only considers partial matches where the overlap is at least 4 characters
        to avoid false positives (e.g. "ac" matching inside "Accra").
        """
        key = amenity.lower().strip()

        # Exact match
        if key in AMENITY_MAPPING:
            return AMENITY_MAPPING[key]

        # Partial / substring match — require minimum 4-char overlap
        for mapping_key, field_name in AMENITY_MAPPING.items():
            if len(mapping_key) >= 4 and mapping_key in key:
                return field_name
            if len(key) >= 4 and key in mapping_key:
                return field_name

        return None

    def _fallback_amenity_extraction(self, query: str) -> List[str]:
        """
        Scan query text for any AMENITY_MAPPING keys (longest-first).

        Uses word-boundary matching to avoid false positives
        (e.g. "ac" inside "Accra").

        Returns list of unique normalized field names.
        """
        q_lower = query.lower()
        found: List[str] = []

        # Sort keys longest-first to match multi-word phrases before single words
        sorted_keys = sorted(AMENITY_MAPPING.keys(), key=len, reverse=True)

        for key in sorted_keys:
            # Use word-boundary regex to avoid partial word matches
            pattern = r"\b" + re.escape(key) + r"\b"
            if re.search(pattern, q_lower):
                field_name = AMENITY_MAPPING[key]
                if field_name not in found:
                    found.append(field_name)

        return found

    def _determine_intent(
        self,
        property_types: List[PropertyType],
        locations: List[str],
        amenities: List[str],
        min_price: Optional[float],
        max_price: Optional[float],
        q_lower: str,
    ) -> SearchIntent:
        """Determine search intent based on extracted fields."""
        if re.search(r"\b(?:invest(?:ment)?|roi|rental\s+yield|return)\b", q_lower):
            return SearchIntent.INVESTMENT
        if re.search(r"\b(?:urgent|asap|immediately|right\s+away)\b", q_lower):
            return SearchIntent.URGENT

        has_price = min_price is not None or max_price is not None
        has_location = bool(locations)
        has_amenities = bool(amenities)

        if has_price and not has_location and not has_amenities:
            return SearchIntent.BUDGET_FOCUSED
        if has_location and not has_price and not has_amenities:
            return SearchIntent.LOCATION_FOCUSED
        if has_amenities and not has_price and not has_location:
            return SearchIntent.AMENITY_FOCUSED

        # Multiple signals present
        if has_price or has_location or has_amenities or bool(property_types):
            return SearchIntent.BROWSE

        return SearchIntent.BROWSE

    def _extract_semantic_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query after stopword removal."""
        words = re.findall(r"[a-zA-Z]+", query.lower())
        keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]
        return keywords if keywords else [query]

    # ==================== Filter Building ====================

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
                f"Amenities extracted: {parsed_query.must_have_amenities} -> "
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

    # ==================== Database Search ====================

    async def _filter_search(
        self,
        filters: SearchFilters,
        organization_id: Optional[str],
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
            # Case-insensitive regex matching for locations
            location_conditions = []
            for loc in filters.locations:
                pattern = re.escape(loc)
                regex_filter = {"$regex": pattern, "$options": "i"}
                location_conditions.append({"location.city": regex_filter})
                location_conditions.append({"location.state": regex_filter})
                location_conditions.append({"location.neighborhood": regex_filter})
            query["$or"] = location_conditions

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
                if amenity in ["pool", "gym", "garden", "balcony", "elevator",
                               "air_conditioning", "heating", "fireplace",
                               "security_system", "storage", "furnished"]:
                    amenity_queries.append({f"features.{amenity}": True})
                elif amenity == "parking_spaces":
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

        # Validate sort field against allowlist
        sort_field = filters.sort_by if filters.sort_by in ALLOWED_SORT_FIELDS else "created_at"
        sort_direction = -1 if filters.sort_order == "desc" else 1

        # Execute query with sorting
        if search_text:
            cursor = self.properties_collection.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort([
                ("score", {"$meta": "textScore"}),
                (sort_field, sort_direction)
            ]).skip(filters.offset).limit(filters.limit)
        else:
            cursor = self.properties_collection.find(query).sort(
                sort_field, sort_direction
            ).skip(filters.offset).limit(filters.limit)

        properties = await cursor.to_list(length=filters.limit)

        # Convert to PropertyMatch
        matches = []
        for prop in properties:
            if "_id" in prop:
                prop["id"] = str(prop["_id"])
                del prop["_id"]

            match_reasons = self._calculate_match_reasons(prop, filters)
            missing_criteria = self._calculate_missing_criteria(prop, filters)

            if search_text:
                if search_text.lower() in prop.get("name", "").lower():
                    match_reasons.insert(0, f"Name matches: '{search_text}'")
                elif search_text.lower() in prop.get("description", "").lower():
                    match_reasons.insert(0, f"Description matches: '{search_text}'")
                else:
                    match_reasons.insert(0, f"Text match: '{search_text}'")

            score = self._calculate_filter_score(prop, filters)
            matches.append(PropertyMatch(
                property_id=prop["id"],
                relevance_score=score,
                filter_score=score,
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
        query_text = " ".join(parsed_query.semantic_keywords)
        return await self._filter_search(filters, organization_id, search_text=query_text)

    # ==================== Scoring ====================

    def _calculate_filter_score(self, property_doc: Dict[str, Any], filters: SearchFilters) -> float:
        """
        Calculate how well property matches filters.

        Returns score from 0.0 to 1.0.
        """
        total_criteria = 0
        matched_criteria = 0

        # Property type match
        if filters.property_types:
            total_criteria += 1
            if property_doc.get("property_type") in [pt.value for pt in filters.property_types]:
                matched_criteria += 1

        # Price range match
        if filters.min_price is not None or filters.max_price is not None:
            total_criteria += 1
            price = property_doc.get("financial", {}).get("price_usd", 0)
            in_range = True
            if filters.min_price is not None and price < filters.min_price:
                in_range = False
            if filters.max_price is not None and price > filters.max_price:
                in_range = False
            if in_range:
                matched_criteria += 1

        # Bedroom match
        if filters.min_bedrooms is not None or filters.max_bedrooms is not None:
            total_criteria += 1
            bedrooms = property_doc.get("features", {}).get("bedrooms", 0)
            in_range = True
            if filters.min_bedrooms is not None and bedrooms < filters.min_bedrooms:
                in_range = False
            if filters.max_bedrooms is not None and bedrooms > filters.max_bedrooms:
                in_range = False
            if in_range:
                matched_criteria += 1

        # Location match
        if filters.locations:
            total_criteria += 1
            prop_city = (property_doc.get("location", {}).get("city") or "").lower()
            prop_neighborhood = (property_doc.get("location", {}).get("neighborhood") or "").lower()
            for loc in filters.locations:
                if loc.lower() in prop_city or loc.lower() in prop_neighborhood:
                    matched_criteria += 1
                    break

        # Amenity match
        if filters.amenities:
            total_criteria += 1
            features = property_doc.get("features", {})
            matched_amenities = sum(1 for a in filters.amenities if features.get(a))
            if matched_amenities == len(filters.amenities):
                matched_criteria += 1
            elif matched_amenities > 0:
                # Partial credit
                matched_criteria += matched_amenities / len(filters.amenities)

        if total_criteria > 0:
            return round(matched_criteria / total_criteria, 3)

        return 1.0

    def _calculate_match_reasons(self, property_doc: Dict[str, Any], filters: SearchFilters) -> List[str]:
        """Calculate why this property matches."""
        reasons = []

        if filters.property_types and property_doc.get("property_type") in [pt.value for pt in filters.property_types]:
            reasons.append(f"Property type: {property_doc.get('property_type')}")

        if filters.locations:
            city = property_doc.get("location", {}).get("city", "")
            neighborhood = property_doc.get("location", {}).get("neighborhood", "")
            for loc in filters.locations:
                if loc.lower() in (city or "").lower() or loc.lower() in (neighborhood or "").lower():
                    reasons.append(f"Location: {city or neighborhood}")
                    break

        if filters.min_bedrooms is not None:
            bedrooms = property_doc.get("features", {}).get("bedrooms", 0)
            if bedrooms >= filters.min_bedrooms:
                reasons.append(f"{bedrooms} bedrooms")

        if filters.min_price is not None or filters.max_price is not None:
            price = property_doc.get("financial", {}).get("price_usd", 0)
            if price:
                reasons.append(f"Price: ${price:,.0f}")

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

    # ==================== Analytics ====================

    async def _get_alternative_locations(self, filters: SearchFilters, organization_id: Optional[str]) -> List[str]:
        """Get alternative locations with available properties."""
        match_query: Dict[str, Any] = {"status": "active"}

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
        organization_id: Optional[str],
        user_id: Optional[str]
    ) -> None:
        """Log search analytics."""
        analytics = SearchAnalytics(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            query=query,
            parsed_query=parsed_query,
            results_count=results_count,
            top_result_id=top_result_id,
            search_time_ms=search_time_ms,
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )

        await self.search_analytics_collection.insert_one(analytics.model_dump())

"""
Search Data Models

AI-powered property search with natural language processing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SearchIntent(str, Enum):
    """Detected user search intent"""
    BROWSE = "browse"  # General browsing
    SPECIFIC_PROPERTY = "specific_property"  # Looking for specific property
    INVESTMENT = "investment"  # Investment properties
    URGENT = "urgent"  # Urgent need
    BUDGET_FOCUSED = "budget_focused"  # Price-sensitive
    LOCATION_FOCUSED = "location_focused"  # Location is priority
    AMENITY_FOCUSED = "amenity_focused"  # Amenities are priority


class PropertyType(str, Enum):
    """Property types"""
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    PENTHOUSE = "penthouse"
    LOFT = "loft"
    TOWNHOUSE = "townhouse"
    LAND = "land"
    COMMERCIAL = "commercial"


class PetPolicy(str, Enum):
    """Pet policies"""
    ALLOWED = "allowed"
    NOT_ALLOWED = "not_allowed"
    CONDITIONAL = "conditional"


class ParsedSearchQuery(BaseModel):
    """
    Parsed natural language search query.

    AI extracts structured filters from natural language.
    """
    # Original query
    original_query: str = Field(..., description="Original search text")

    # Detected intent
    intent: SearchIntent = Field(SearchIntent.BROWSE, description="User intent")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Intent confidence")

    # Extracted filters
    property_types: List[PropertyType] = Field(default_factory=list, description="Property types")
    locations: List[str] = Field(default_factory=list, description="Locations, cities, neighborhoods")
    min_price: Optional[float] = Field(None, description="Minimum price (USD)")
    max_price: Optional[float] = Field(None, description="Maximum price (USD)")
    min_bedrooms: Optional[int] = Field(None, description="Minimum bedrooms")
    max_bedrooms: Optional[int] = Field(None, description="Maximum bedrooms")
    min_bathrooms: Optional[int] = Field(None, description="Minimum bathrooms")
    min_sqft: Optional[int] = Field(None, description="Minimum square feet")
    max_sqft: Optional[int] = Field(None, description="Maximum square feet")

    # Amenities
    must_have_amenities: List[str] = Field(default_factory=list, description="Required amenities")
    nice_to_have_amenities: List[str] = Field(default_factory=list, description="Preferred amenities")

    # Special requirements
    pet_policy: Optional[PetPolicy] = Field(None, description="Pet requirement")
    furnished: Optional[bool] = Field(None, description="Furnished requirement")

    # Semantic search
    semantic_keywords: List[str] = Field(default_factory=list, description="Keywords for semantic search")

    # Metadata
    language: str = Field("en", description="Query language")
    parsed_at: datetime = Field(default_factory=datetime.utcnow, description="When parsed")


class SearchFilters(BaseModel):
    """
    Direct search filters (for UI-based search).

    Alternative to NLP parsing.
    """
    property_types: Optional[List[PropertyType]] = Field(None, description="Filter by property types")
    locations: Optional[List[str]] = Field(None, description="Filter by locations")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price (USD)")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price (USD)")
    min_bedrooms: Optional[int] = Field(None, ge=0, description="Minimum bedrooms")
    max_bedrooms: Optional[int] = Field(None, ge=0, description="Maximum bedrooms")
    min_bathrooms: Optional[int] = Field(None, ge=0, description="Minimum bathrooms")
    min_sqft: Optional[int] = Field(None, ge=0, description="Minimum square feet")
    max_sqft: Optional[int] = Field(None, ge=0, description="Maximum square feet")
    amenities: Optional[List[str]] = Field(None, description="Required amenities")
    pet_policy: Optional[PetPolicy] = Field(None, description="Pet policy requirement")
    furnished: Optional[bool] = Field(None, description="Furnished requirement")

    # Sorting
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    # Pagination
    limit: int = Field(20, ge=1, le=100, description="Results per page")
    offset: int = Field(0, ge=0, description="Page offset")


class SearchRequest(BaseModel):
    """
    Search request from user.

    Supports both NLP and structured search.
    """
    # Natural language query (optional)
    query: Optional[str] = Field(None, description="Natural language search query")

    # Direct filters (optional)
    filters: Optional[SearchFilters] = Field(None, description="Direct search filters")

    # Search mode
    use_semantic_search: bool = Field(True, description="Enable semantic/vector search")

    # Currency preference
    currency: str = Field("USD", description="Preferred currency for results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "I need a 3 bedroom apartment in Accra with a pool, budget around $500k",
                "use_semantic_search": True,
                "currency": "USD"
            }
        }


class PropertyMatch(BaseModel):
    """
    Property search result with match metadata.
    """
    property_id: str = Field(..., description="Property ID")

    # Match scoring
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Match relevance (0-1)")
    semantic_score: Optional[float] = Field(None, description="Semantic similarity score")
    filter_score: float = Field(..., description="Filter match score")

    # Match reasons
    match_reasons: List[str] = Field(default_factory=list, description="Why this property matches")
    missing_criteria: List[str] = Field(default_factory=list, description="Criteria not met")

    # Property data (embedded for performance)
    property_data: Dict[str, Any] = Field(..., description="Property details")


class SearchResponse(BaseModel):
    """
    Search results response.
    """
    # Results
    matches: List[PropertyMatch] = Field(..., description="Matching properties")
    total: int = Field(..., description="Total matches")

    # Query metadata
    parsed_query: Optional[ParsedSearchQuery] = Field(None, description="Parsed NLP query")
    applied_filters: Dict[str, Any] = Field(..., description="Actual filters applied")

    # Search metadata
    search_time_ms: float = Field(..., description="Search duration in ms")
    used_semantic_search: bool = Field(False, description="Whether semantic search was used")

    # Suggestions
    suggested_refinements: List[str] = Field(default_factory=list, description="Suggested search refinements")
    alternative_locations: List[str] = Field(default_factory=list, description="Alternative locations")

    # Pagination
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Page offset")


class PropertyEmbedding(BaseModel):
    """
    Property vector embedding for semantic search.

    Stored separately for efficient vector search.
    """
    property_id: str = Field(..., description="Property ID")
    organization_id: str = Field(..., description="Organization ID")

    # Embedding vector
    embedding: List[float] = Field(..., description="Dense vector embedding (1536 dimensions)")

    # Source text used for embedding
    embedded_text: str = Field(..., description="Text that was embedded")

    # Metadata
    embedding_model: str = Field("text-embedding-3-small", description="Model used")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Updated timestamp")


class SearchAnalytics(BaseModel):
    """
    Search analytics for improving results.
    """
    id: str = Field(..., description="Analytics ID")
    organization_id: Optional[str] = Field(None, description="Organization ID (optional for public searches)")

    # Query info
    query: str = Field(..., description="Search query")
    parsed_query: Optional[ParsedSearchQuery] = Field(None, description="Parsed query")

    # Results
    results_count: int = Field(..., description="Number of results")
    top_result_id: Optional[str] = Field(None, description="Top result property ID")

    # User interaction
    clicked_property_ids: List[str] = Field(default_factory=list, description="Properties clicked")
    booked_property_id: Optional[str] = Field(None, description="Property booked from search")

    # Performance
    search_time_ms: float = Field(..., description="Search duration")

    # Metadata
    user_id: Optional[str] = Field(None, description="User who searched")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")

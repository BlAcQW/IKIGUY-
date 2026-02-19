"""
Search API Router

AI-powered property search endpoints with natural language processing.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context, get_optional_user, get_optional_organization_context
from app.services.search_service import PropertySearchService
from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchFilters,
    PropertyType,
    PetPolicy
)


router = APIRouter(prefix="/search", tags=["search"])


# ==================== AI Search ====================

@router.post("", response_model=SearchResponse)
async def search_properties(
    search_request: SearchRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    org_context: Optional[Dict[str, str]] = Depends(get_optional_organization_context)
):
    """
    AI-powered property search.

    Supports both natural language queries and structured filters:

    **Natural Language Examples:**
    - "I need a 3 bedroom apartment in Accra with a pool, budget around $500k"
    - "Looking for pet-friendly house in East Legon under $300k"
    - "Show me investment properties with good rental yield"

    **Features:**
    - NLP query parsing with intent detection
    - Semantic search for better matching
    - Intelligent filter extraction
    - Match scoring with reasons
    - Search refinement suggestions

    **Authentication:**
    - Optional - Works for both authenticated and public users
    - Authenticated users may see personalized results
    """
    search_service = PropertySearchService(database)

    try:
        results = await search_service.search(
            search_request=search_request,
            organization_id=org_context["organization_id"] if org_context else None,
            user_id=org_context.get("user_id") if org_context else None
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("", response_model=SearchResponse)
async def search_properties_get(
    query: str = Query(..., description="Natural language search query"),
    property_type: list[PropertyType] | None = Query(None, description="Filter by property types"),
    location: list[str] | None = Query(None, description="Filter by locations"),
    min_price: float | None = Query(None, ge=0, description="Minimum price (USD)"),
    max_price: float | None = Query(None, ge=0, description="Maximum price (USD)"),
    min_bedrooms: int | None = Query(None, ge=0, description="Minimum bedrooms"),
    max_bedrooms: int | None = Query(None, ge=0, description="Maximum bedrooms"),
    min_bathrooms: int | None = Query(None, ge=0, description="Minimum bathrooms"),
    amenities: list[str] | None = Query(None, description="Required amenities"),
    pet_policy: PetPolicy | None = Query(None, description="Pet policy requirement"),
    furnished: bool | None = Query(None, description="Furnished requirement"),
    use_semantic_search: bool = Query(True, description="Enable semantic search"),
    currency: str = Query("USD", description="Preferred currency"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    org_context: Optional[Dict[str, str]] = Depends(get_optional_organization_context)
):
    """
    Search properties with GET request (for simple URL-based searches).

    Alternative to POST endpoint for easier browser integration.

    **Authentication:**
    - Optional - Works for both authenticated and public users
    """
    # Build search request
    filters = SearchFilters(
        property_types=property_type,
        locations=location,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        min_bathrooms=min_bathrooms,
        amenities=amenities,
        pet_policy=pet_policy,
        furnished=furnished,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    search_request = SearchRequest(
        query=query,
        filters=filters,
        use_semantic_search=use_semantic_search,
        currency=currency
    )

    search_service = PropertySearchService(database)

    try:
        results = await search_service.search(
            search_request=search_request,
            organization_id=org_context["organization_id"] if org_context else None,
            user_id=org_context.get("user_id") if org_context else None
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== Search Analytics ====================

@router.get("/analytics/popular-searches")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get most popular search queries.

    Useful for understanding user search patterns.
    """
    search_analytics_collection = database["search_analytics"]

    pipeline = [
        {"$match": {"organization_id": org_context["organization_id"]}},
        {"$group": {"_id": "$query", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]

    results = await search_analytics_collection.aggregate(pipeline).to_list(length=limit)

    return {
        "popular_searches": [
            {"query": r["_id"], "count": r["count"]}
            for r in results
        ]
    }


@router.get("/analytics/zero-results")
async def get_zero_result_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get searches that returned zero results.

    Useful for identifying gaps in inventory or improving search.
    """
    search_analytics_collection = database["search_analytics"]

    cursor = search_analytics_collection.find({
        "organization_id": org_context["organization_id"],
        "results_count": 0
    }).sort("created_at", -1).limit(limit)

    results = await cursor.to_list(length=limit)

    return {
        "zero_result_searches": [
            {
                "query": r["query"],
                "parsed_query": r.get("parsed_query"),
                "timestamp": r["created_at"]
            }
            for r in results
        ]
    }


@router.get("/analytics/performance")
async def get_search_performance(
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get search performance metrics.

    Returns average search time, result counts, etc.
    """
    search_analytics_collection = database["search_analytics"]

    pipeline = [
        {"$match": {"organization_id": org_context["organization_id"]}},
        {
            "$group": {
                "_id": None,
                "total_searches": {"$sum": 1},
                "avg_search_time_ms": {"$avg": "$search_time_ms"},
                "avg_results": {"$avg": "$results_count"},
                "zero_results": {
                    "$sum": {"$cond": [{"$eq": ["$results_count", 0]}, 1, 0]}
                }
            }
        }
    ]

    results = await search_analytics_collection.aggregate(pipeline).to_list(length=1)

    if not results:
        return {
            "total_searches": 0,
            "avg_search_time_ms": 0,
            "avg_results": 0,
            "zero_results_rate": 0
        }

    stats = results[0]
    return {
        "total_searches": stats["total_searches"],
        "avg_search_time_ms": round(stats["avg_search_time_ms"], 2),
        "avg_results": round(stats["avg_results"], 2),
        "zero_results_rate": round(stats["zero_results"] / stats["total_searches"] * 100, 2)
    }


# ==================== Search Suggestions ====================

@router.get("/suggestions/locations")
async def get_location_suggestions(
    query: str = Query(..., min_length=1, description="Location search query"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get location autocomplete suggestions.

    Searches cities, states, and neighborhoods.
    """
    properties_collection = database["properties"]

    # Regex search for locations
    regex_query = {"$regex": f"^{query}", "$options": "i"}

    pipeline = [
        {
            "$match": {
                "organization_id": org_context["organization_id"],
                "status": "active",
                "$or": [
                    {"location.city": regex_query},
                    {"location.state": regex_query},
                    {"location.neighborhood": regex_query}
                ]
            }
        },
        {
            "$group": {
                "_id": None,
                "cities": {"$addToSet": "$location.city"},
                "neighborhoods": {"$addToSet": "$location.neighborhood"}
            }
        }
    ]

    results = await properties_collection.aggregate(pipeline).to_list(length=1)

    if not results:
        return {"suggestions": []}

    locations = set()
    if results[0].get("cities"):
        locations.update(results[0]["cities"])
    if results[0].get("neighborhoods"):
        locations.update(results[0]["neighborhoods"])

    # Filter and sort
    suggestions = [
        loc for loc in locations
        if loc and loc.lower().startswith(query.lower())
    ]
    suggestions.sort()

    return {"suggestions": suggestions[:limit]}


@router.get("/suggestions/amenities")
async def get_amenity_suggestions(
    query: str = Query("", description="Amenity search query"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions"),
    database: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user),
    org_context: Dict[str, str] = Depends(get_organization_context)
):
    """
    Get amenity suggestions.

    Returns common amenities available in properties.
    """
    # Common amenities
    all_amenities = [
        "pool", "gym", "parking", "garden", "balcony", "elevator",
        "security", "air_conditioning", "heating", "laundry", "storage",
        "playground", "tennis_court", "basketball_court", "clubhouse",
        "concierge", "doorman", "pet_spa", "bike_storage", "ev_charging"
    ]

    # Filter by query
    if query:
        suggestions = [a for a in all_amenities if query.lower() in a.lower()]
    else:
        suggestions = all_amenities

    return {"suggestions": suggestions[:limit]}

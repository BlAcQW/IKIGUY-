"""
Property API router for EstateFlow.

Provides RESTful endpoints for property management with multi-currency support.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, get_optional_user, get_organization_context
from app.core.database import MongoDB, get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.property import (
    Property,
    PropertyCreate,
    PropertyUpdate,
    PropertyFilter,
    PropertyType,
    PropertyStatus,
    PetPolicy,
)
from app.services.property_service import PropertyService
from app.services.currency_service import CurrencyService, Currency


logger = logging.getLogger(__name__)

router = APIRouter(tags=["properties"])


# Dependency to get property service
def get_property_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> PropertyService:
    """Get property service instance."""
    return PropertyService(db)


# Dependency to get currency service
def get_currency_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> CurrencyService:
    """Get currency service instance."""
    # TODO: Get API key from environment variable
    return CurrencyService(db)


class PropertyListResponse(BaseModel):
    """Response model for property list endpoint."""
    properties: List[Property]
    total: int
    limit: int
    offset: int
    has_more: bool


class PropertyWithConvertedPrice(Property):
    """Property model with converted price information."""
    converted_price: Optional[float] = Field(None, description="Price in requested currency")
    conversion_currency: Optional[str] = Field(None, description="Currency code for conversion")
    exchange_rate: Optional[float] = Field(None, description="Exchange rate used")


# ==================== Property CRUD Endpoints ====================

@router.post(
    "/properties",
    response_model=Property,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property"
)
async def create_property(
    property_data: PropertyCreate,
    current_user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
    service: PropertyService = Depends(get_property_service)
) -> Property:
    """
    Create a new property listing.

    Requires authentication. Property will be created under the user's organization.

    Args:
        property_data: Property creation data
        current_user: Current authenticated user
        org_context: Organization context
        service: Property service dependency

    Returns:
        Property: Created property with generated ID

    Raises:
        HTTPException 400: If validation fails
        HTTPException 401: If not authenticated
    """
    try:
        organization_id = org_context["organization_id"]

        # Ensure property belongs to user's organization
        property_data.organization_id = organization_id

        property_obj = await service.create_property(property_data, organization_id)

        return property_obj

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create property"
        )


@router.get(
    "/properties/{property_id}",
    response_model=Property,
    summary="Get property by ID"
)
async def get_property(
    property_id: str,
    currency: Optional[str] = Query(None, description="Convert price to this currency (USD, EUR, GHS, etc.)"),
    current_user: Optional[dict] = Depends(get_optional_user),
    service: PropertyService = Depends(get_property_service),
    currency_service: CurrencyService = Depends(get_currency_service)
) -> Property:
    """
    Get property details by ID.

    Public endpoint - no authentication required.
    Optionally convert price to a different currency using the `currency` query parameter.

    Args:
        property_id: Property ID (MongoDB ObjectId string)
        currency: Optional currency code for price conversion
        current_user: Optional authenticated user (for scoped access)
        service: Property service dependency
        currency_service: Currency service dependency

    Returns:
        Property: Property details

    Raises:
        HTTPException 404: If property not found
    """
    try:
        # Get organization_id if user is authenticated
        organization_id = current_user.get("organization_id") if current_user else None

        property_obj = await service.get_property(property_id, organization_id)

        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found"
            )

        # Convert price if currency parameter provided
        if currency and currency.upper() != "USD":
            try:
                converted = await currency_service.convert_property_price(
                    property_obj.financial.price_usd,
                    currency.upper()
                )
                # Add conversion info to response (as extra fields)
                property_dict = property_obj.model_dump()
                property_dict["converted_price"] = converted["price"]
                property_dict["conversion_currency"] = currency.upper()
                property_dict["exchange_rate"] = converted["exchange_rate"]
                return Property(**property_dict)
            except ValueError:
                # Invalid currency code, just return USD price
                logger.warning(f"Invalid currency code: {currency}")

        return property_obj

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property"
        )


@router.get(
    "/properties",
    response_model=PropertyListResponse,
    summary="List properties with filtering"
)
async def list_properties(
    # Filtering parameters
    property_type: Optional[List[PropertyType]] = Query(None, description="Filter by property type"),
    status: Optional[List[PropertyStatus]] = Query(None, description="Filter by status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price (USD)"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price (USD)"),
    min_bedrooms: Optional[int] = Query(None, ge=0, description="Minimum bedrooms"),
    max_bedrooms: Optional[int] = Query(None, ge=0, description="Maximum bedrooms"),
    min_bathrooms: Optional[float] = Query(None, ge=0, description="Minimum bathrooms"),
    max_bathrooms: Optional[float] = Query(None, ge=0, description="Maximum bathrooms"),
    city: Optional[str] = Query(None, description="Filter by city"),
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    location: Optional[str] = Query(None, description="Search by location (city, neighborhood, or address)"),
    pet_policy: Optional[List[PetPolicy]] = Query(None, description="Filter by pet policy"),
    has_pool: Optional[bool] = Query(None, description="Has swimming pool"),
    has_garden: Optional[bool] = Query(None, description="Has garden"),
    furnished: Optional[bool] = Query(None, description="Is furnished"),
    # Pagination
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort field (price, created_at, sqft)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    # Currency conversion
    currency: Optional[str] = Query(None, description="Convert prices to this currency"),
    # Dependencies
    current_user: Optional[dict] = Depends(get_optional_user),
    service: PropertyService = Depends(get_property_service),
    currency_service: CurrencyService = Depends(get_currency_service)
) -> PropertyListResponse:
    """
    List properties with filtering, sorting, and pagination.

    Public endpoint - no authentication required.
    Supports extensive filtering by property attributes, location, and features.
    Optionally convert all prices to a different currency.

    Args:
        property_type: Filter by property type(s)
        status: Filter by status(es)
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        min_bedrooms: Minimum bedrooms
        max_bedrooms: Maximum bedrooms
        min_bathrooms: Minimum bathrooms
        max_bathrooms: Maximum bathrooms
        city: City filter
        neighborhood: Neighborhood filter
        location: General location search (city, neighborhood, or address)
        pet_policy: Pet policy filter
        has_pool: Pool filter
        has_garden: Garden filter
        furnished: Furnished filter
        limit: Results per page
        offset: Pagination offset
        sort_by: Sort field
        sort_order: Sort order
        currency: Currency for price conversion
        current_user: Optional authenticated user (for scoped access)
        service: Property service dependency
        currency_service: Currency service dependency

    Returns:
        PropertyListResponse: List of properties with pagination info
    """
    try:
        # Get organization_id if user is authenticated (for scoped access)
        organization_id = current_user.get("organization_id") if current_user else None

        # Build filter object
        filters = PropertyFilter(
            property_type=property_type,
            status=status,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            min_bathrooms=min_bathrooms,
            max_bathrooms=max_bathrooms,
            city=city,
            neighborhood=neighborhood,
            location=location,
            pet_policy=pet_policy,
            has_pool=has_pool,
            has_garden=has_garden,
            furnished=furnished,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        properties, total = await service.list_properties(filters, organization_id)

        # Convert prices if currency parameter provided
        if currency and currency.upper() != "USD":
            try:
                converted_properties = []
                for prop in properties:
                    converted = await currency_service.convert_property_price(
                        prop.financial.price_usd,
                        currency.upper()
                    )
                    prop_dict = prop.model_dump()
                    prop_dict["converted_price"] = converted["price"]
                    prop_dict["conversion_currency"] = currency.upper()
                    prop_dict["exchange_rate"] = converted["exchange_rate"]
                    converted_properties.append(Property(**prop_dict))
                properties = converted_properties
            except ValueError:
                logger.warning(f"Invalid currency code: {currency}")

        has_more = (offset + limit) < total

        return PropertyListResponse(
            properties=properties,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Error listing properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list properties"
        )


@router.put(
    "/properties/{property_id}",
    response_model=Property,
    summary="Update property"
)
async def update_property(
    property_id: str,
    updates: PropertyUpdate,
    current_user: dict = Depends(get_current_user),
    service: PropertyService = Depends(get_property_service)
) -> Property:
    """
    Update property information.

    Supports partial updates - only provide fields you want to change.

    Args:
        property_id: Property ID
        updates: Update data (partial)
        current_user: Current authenticated user
        service: Property service dependency

    Returns:
        Property: Updated property

    Raises:
        HTTPException 404: If property not found
        HTTPException 400: If validation fails
    """
    try:
        organization_id = current_user.get("organization_id")

        property_obj = await service.update_property(property_id, updates, organization_id)

        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found"
            )

        return property_obj

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update property"
        )


@router.delete(
    "/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete property"
)
async def delete_property(
    property_id: str,
    current_user: dict = Depends(get_current_user),
    service: PropertyService = Depends(get_property_service)
):
    """
    Delete property (soft delete - sets status to INACTIVE).

    Args:
        property_id: Property ID
        current_user: Current authenticated user
        service: Property service dependency

    Raises:
        HTTPException 404: If property not found
    """
    try:
        organization_id = current_user.get("organization_id")

        deleted = await service.delete_property(property_id, organization_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete property"
        )


# ==================== Search Endpoint ====================

@router.get(
    "/properties/search",
    response_model=PropertyListResponse,
    summary="Search properties"
)
async def search_properties(
    q: str = Query(..., min_length=1, description="Search query"),
    # Use same filter parameters as list endpoint
    property_type: Optional[List[PropertyType]] = Query(None),
    status: Optional[List[PropertyStatus]] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    city: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    currency: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_user),
    service: PropertyService = Depends(get_property_service),
    currency_service: CurrencyService = Depends(get_currency_service)
) -> PropertyListResponse:
    """
    Search properties using full-text search.

    Public endpoint - no authentication required.
    Searches in property name and description fields.

    Args:
        q: Search query string
        property_type: Filter by property type
        status: Filter by status
        min_price: Minimum price
        max_price: Maximum price
        city: City filter
        limit: Results per page
        offset: Pagination offset
        currency: Currency for price conversion
        current_user: Optional authenticated user (for scoped access)
        service: Property service dependency
        currency_service: Currency service dependency

    Returns:
        PropertyListResponse: Search results with pagination
    """
    try:
        # Get organization_id if user is authenticated (for scoped access)
        organization_id = current_user.get("organization_id") if current_user else None

        filters = PropertyFilter(
            property_type=property_type,
            status=status,
            min_price=min_price,
            max_price=max_price,
            city=city,
            limit=limit,
            offset=offset
        )

        properties, total = await service.search_properties(q, filters, organization_id)

        # Convert prices if needed
        if currency and currency.upper() != "USD":
            try:
                converted_properties = []
                for prop in properties:
                    converted = await currency_service.convert_property_price(
                        prop.financial.price_usd,
                        currency.upper()
                    )
                    prop_dict = prop.model_dump()
                    prop_dict["converted_price"] = converted["price"]
                    prop_dict["conversion_currency"] = currency.upper()
                    converted_properties.append(Property(**prop_dict))
                properties = converted_properties
            except ValueError:
                logger.warning(f"Invalid currency code: {currency}")

        has_more = (offset + limit) < total

        return PropertyListResponse(
            properties=properties,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search properties"
        )


# ==================== Currency Endpoints ====================

@router.get(
    "/currencies",
    response_model=List[Currency],
    summary="List supported currencies"
)
async def list_currencies(
    currency_service: CurrencyService = Depends(get_currency_service)
) -> List[Currency]:
    """
    Get list of supported currencies.

    Returns:
        List[Currency]: List of supported currency objects with codes, names, and symbols
    """
    return await currency_service.get_supported_currencies()


@router.get(
    "/currencies/rates",
    summary="Get current exchange rates"
)
async def get_exchange_rates(
    force_refresh: bool = Query(False, description="Force API refresh"),
    currency_service: CurrencyService = Depends(get_currency_service)
):
    """
    Get current exchange rates (base USD).

    Results are cached for 1 hour to minimize API calls.

    Args:
        force_refresh: Force fetch from API even if cache is valid
        currency_service: Currency service dependency

    Returns:
        dict: Exchange rate data with base currency, rates, and timestamp
    """
    try:
        rates = await currency_service.get_exchange_rates(force_refresh)
        return rates.model_dump()
    except Exception as e:
        logger.error(f"Error getting exchange rates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch exchange rates"
        )


# ==================== Analytics Endpoint ====================

@router.get(
    "/properties/stats/counts",
    summary="Get property counts by status"
)
async def get_property_counts(
    current_user: dict = Depends(get_current_user),
    service: PropertyService = Depends(get_property_service)
):
    """
    Get property counts grouped by status.

    Useful for dashboard statistics.

    Args:
        current_user: Current authenticated user
        service: Property service dependency

    Returns:
        dict: Status counts (active, pending, sold, rented, inactive, total)
    """
    try:
        organization_id = current_user.get("organization_id")
        counts = await service.get_property_count(organization_id)
        return counts
    except Exception as e:
        logger.error(f"Error getting property counts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property counts"
        )

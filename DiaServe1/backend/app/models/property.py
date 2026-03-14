"""
Property models for EstateFlow.

This module contains all Pydantic models related to properties, including:
- Property type and status enums
- Location and neighborhood data
- Property features and amenities
- Financial information with multi-currency support
- Pet policies
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.models.image import ImageSummary


class PropertyType(str, Enum):
    """
    Property type enumeration.

    Supports various residential and commercial property types.
    """
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    PENTHOUSE = "penthouse"
    LOFT = "loft"
    TOWNHOUSE = "townhouse"
    LAND = "land"
    COMMERCIAL = "commercial"


class PropertyStatus(str, Enum):
    """
    Property listing status enumeration.

    Tracks the current state of a property listing.
    """
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    RENTED = "rented"
    INACTIVE = "inactive"


class PetPolicy(str, Enum):
    """
    Pet policy enumeration.

    Defines whether pets are allowed in a property.
    """
    ALLOWED = "allowed"
    NOT_ALLOWED = "not_allowed"
    CONDITIONAL = "conditional"  # Allowed with conditions (deposit, breed restrictions, etc.)


class Location(BaseModel):
    """
    Property location details with geocoding support.

    Attributes:
        address: Street address
        city: City name
        state: State/Province
        zip_code: Postal code
        country: Country name
        digital_address: Ghana Post digital address (e.g., GD-123-4567)
        latitude: Latitude coordinate for map display
        longitude: Longitude coordinate for map display
        neighborhood: Neighborhood or district name
    """
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: Optional[str] = Field(None, description="State/Province")
    zip_code: Optional[str] = Field(None, description="Postal code")
    country: str = Field(..., description="Country name")
    digital_address: Optional[str] = Field(None, description="Ghana Post GPS digital address")
    latitude: Optional[float] = Field(None, description="Latitude coordinate", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Longitude coordinate", ge=-180, le=180)
    neighborhood: Optional[str] = Field(None, description="Neighborhood or district name")


class School(BaseModel):
    """
    Nearby school information.

    Attributes:
        name: School name
        type: School type (elementary, middle, high, university)
        distance_km: Distance from property in kilometers
        rating: School rating (0-10 scale)
    """
    name: str = Field(..., description="School name")
    type: str = Field(..., description="School type (elementary, middle, high, university)")
    distance_km: float = Field(..., description="Distance from property in kilometers", ge=0)
    rating: Optional[float] = Field(None, description="School rating (0-10 scale)", ge=0, le=10)


class Amenity(BaseModel):
    """
    Nearby amenity information.

    Attributes:
        name: Amenity name
        category: Category (grocery, restaurant, park, transit, hospital, etc.)
        distance_km: Distance from property in kilometers
    """
    name: str = Field(..., description="Amenity name")
    category: str = Field(..., description="Category (grocery, restaurant, park, transit, hospital)")
    distance_km: float = Field(..., description="Distance from property in kilometers", ge=0)


class NeighborhoodData(BaseModel):
    """
    Comprehensive neighborhood information.

    Attributes:
        schools: List of nearby schools with ratings
        amenities: List of nearby amenities
        safety_rating: Neighborhood safety rating (0-10 scale)
        walkability_score: Walkability score (0-100)
        transit_score: Public transit accessibility score (0-100)
    """
    schools: List[School] = Field(default_factory=list, description="Nearby schools")
    amenities: List[Amenity] = Field(default_factory=list, description="Nearby amenities")
    safety_rating: Optional[float] = Field(None, description="Safety rating (0-10)", ge=0, le=10)
    walkability_score: Optional[int] = Field(None, description="Walkability score (0-100)", ge=0, le=100)
    transit_score: Optional[int] = Field(None, description="Transit score (0-100)", ge=0, le=100)


class PropertyFeatures(BaseModel):
    """
    Property features and amenities.

    Attributes:
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms
        sqft: Interior square footage
        lot_size: Lot size in square feet
        year_built: Year property was built
        parking_spaces: Number of parking spaces
        pool: Has swimming pool
        garden: Has garden/yard
        balcony: Has balcony/terrace
        pet_policy: Pet policy (allowed, not_allowed, conditional)
        pet_deposit: Pet deposit amount (if conditional or allowed)
        furnished: Is furnished
        elevator: Has elevator
        air_conditioning: Has air conditioning
        heating: Has heating system
        fireplace: Has fireplace
        security_system: Has security system
        gym: Has gym/fitness center
        storage: Has storage unit
    """
    bedrooms: int = Field(..., description="Number of bedrooms", ge=0)
    bathrooms: float = Field(..., description="Number of bathrooms", ge=0)
    sqft: Optional[float] = Field(None, description="Interior square footage", ge=0)
    lot_size: Optional[float] = Field(None, description="Lot size in square feet", ge=0)
    year_built: Optional[int] = Field(None, description="Year property was built", ge=1800, le=2100)
    parking_spaces: int = Field(0, description="Number of parking spaces", ge=0)
    pool: bool = Field(False, description="Has swimming pool")
    garden: bool = Field(False, description="Has garden/yard")
    balcony: bool = Field(False, description="Has balcony/terrace")
    pet_policy: PetPolicy = Field(PetPolicy.NOT_ALLOWED, description="Pet policy")
    pet_deposit: Optional[float] = Field(None, description="Pet deposit amount", ge=0)
    furnished: bool = Field(False, description="Is furnished")
    elevator: bool = Field(False, description="Has elevator")
    air_conditioning: bool = Field(False, description="Has air conditioning")
    heating: bool = Field(False, description="Has heating system")
    fireplace: bool = Field(False, description="Has fireplace")
    security_system: bool = Field(False, description="Has security system")
    gym: bool = Field(False, description="Has gym/fitness center")
    storage: bool = Field(False, description="Has storage unit")
    custom_features: Optional[List[str]] = Field(
        default_factory=list,
        description="Custom features not covered by standard checkboxes",
        max_length=20,
    )

    @field_validator('pet_deposit')
    @classmethod
    def validate_pet_deposit(cls, v, info):
        """
        Validate pet_deposit is only set when pet_policy allows pets.

        Args:
            v: Pet deposit value
            info: Validation info containing other field values

        Returns:
            float: Validated pet deposit
        """
        # Reason: Pet deposit should only exist if pets are allowed or conditional
        pet_policy = info.data.get('pet_policy')
        if v is not None and pet_policy == PetPolicy.NOT_ALLOWED:
            raise ValueError("Pet deposit cannot be set when pets are not allowed")
        return v


class FinancialInfo(BaseModel):
    """
    Property financial information with multi-currency support.

    Attributes:
        price_usd: Price in USD (base currency for all conversions)
        base_currency: Original currency the price was set in (USD, EUR, GHS, etc.)
        hoa_fees_monthly: Monthly HOA/maintenance fees in USD
        property_tax_annual: Annual property tax in USD
        insurance_estimate: Annual insurance estimate in USD
    """
    price_usd: float = Field(..., description="Price in USD (base currency)", gt=0)
    base_currency: str = Field("USD", description="Original currency (USD, EUR, GHS, etc.)")
    hoa_fees_monthly: Optional[float] = Field(None, description="Monthly HOA fees in USD", ge=0)
    property_tax_annual: Optional[float] = Field(None, description="Annual property tax in USD", ge=0)
    insurance_estimate: Optional[float] = Field(None, description="Annual insurance estimate in USD", ge=0)


class Property(BaseModel):
    """
    Main property model with all details.

    Attributes:
        id: Unique property identifier (MongoDB ObjectId as string)
        organization_id: Organization ID for multi-tenancy
        name: Property name/title
        description: Detailed property description
        property_type: Type of property (apartment, house, villa, etc.)
        status: Current status (active, pending, sold, rented, inactive)
        location: Location details with geocoding
        neighborhood_data: Neighborhood information (schools, amenities, scores)
        features: Property features and amenities
        financial: Financial information with multi-currency support
        images: List of image URLs
        video_url: Optional video tour URL
        virtual_tour_url: Optional 360° virtual tour URL
        agent_id: ID of assigned real estate agent
        agent_name: Name of assigned agent
        ai_context_cache: Cached AI context string for chat (internal use)
        ai_context_cache_updated_at: When AI context was last updated
        created_at: When property was created
        updated_at: When property was last updated
    """
    id: Optional[str] = Field(None, description="Property ID (MongoDB ObjectId)")
    organization_id: str = Field(..., description="Organization ID for multi-tenancy")

    # Basic info
    name: str = Field(..., description="Property name/title", min_length=1, max_length=200)
    description: str = Field(..., description="Detailed property description", min_length=1)
    property_type: PropertyType = Field(..., description="Property type")
    status: PropertyStatus = Field(PropertyStatus.ACTIVE, description="Property status")

    # Location and neighborhood
    location: Location = Field(..., description="Location details")
    neighborhood_data: NeighborhoodData = Field(
        default_factory=NeighborhoodData,
        description="Neighborhood information"
    )

    # Features
    features: PropertyFeatures = Field(..., description="Property features and amenities")

    # Financial
    financial: FinancialInfo = Field(..., description="Financial information")

    # Media
    images: List[str] = Field(default_factory=list, description="Image URLs (legacy, for backward compatibility)")
    images_v2: Optional[List[ImageSummary]] = Field(
        None,
        description="Structured image data with GridFS references and metadata"
    )
    video_url: Optional[str] = Field(None, description="Video tour URL")
    virtual_tour_url: Optional[str] = Field(None, description="360° virtual tour URL")

    # Agent info
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    agent_name: Optional[str] = Field(None, description="Assigned agent name")

    # AI context caching (internal use - not exposed in API responses)
    ai_context_cache: Optional[str] = Field(None, description="Cached AI context", exclude=True)
    ai_context_cache_updated_at: Optional[datetime] = Field(None, description="AI context cache timestamp", exclude=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "name": "Luxury Villa in East Legon",
                "description": "Stunning 4-bedroom villa with modern amenities in the heart of East Legon. Perfect for families seeking comfort and elegance.",
                "property_type": "villa",
                "status": "active",
                "location": {
                    "address": "123 Independence Avenue",
                    "city": "Accra",
                    "state": "Greater Accra",
                    "zip_code": "00233",
                    "country": "Ghana",
                    "digital_address": "GD-123-4567",
                    "latitude": 5.6037,
                    "longitude": -0.1870,
                    "neighborhood": "East Legon"
                },
                "neighborhood_data": {
                    "schools": [
                        {
                            "name": "Lincoln Community School",
                            "type": "elementary",
                            "distance_km": 1.2,
                            "rating": 9.0
                        }
                    ],
                    "amenities": [
                        {
                            "name": "MaxMart",
                            "category": "grocery",
                            "distance_km": 0.8
                        }
                    ],
                    "safety_rating": 8.5,
                    "walkability_score": 75,
                    "transit_score": 65
                },
                "features": {
                    "bedrooms": 4,
                    "bathrooms": 3.5,
                    "sqft": 3500,
                    "lot_size": 5000,
                    "year_built": 2020,
                    "parking_spaces": 2,
                    "pool": True,
                    "garden": True,
                    "balcony": True,
                    "pet_policy": "conditional",
                    "pet_deposit": 500.0,
                    "furnished": False,
                    "elevator": False,
                    "air_conditioning": True,
                    "heating": False,
                    "security_system": True
                },
                "financial": {
                    "price_usd": 750000.0,
                    "base_currency": "USD",
                    "hoa_fees_monthly": 200.0,
                    "property_tax_annual": 5000.0,
                    "insurance_estimate": 2000.0
                },
                "images": [
                    "https://example.com/images/property1_front.jpg",
                    "https://example.com/images/property1_interior.jpg"
                ],
                "video_url": "https://example.com/videos/property1_tour.mp4",
                "agent_id": "agent_456",
                "agent_name": "John Doe"
            }
        }


class PropertyCreate(BaseModel):
    """
    Model for creating a new property.

    Excludes id, timestamps, and cached fields.
    organization_id is optional in the request - will be set from authenticated user.
    """
    organization_id: Optional[str] = Field(None, description="Organization ID (auto-filled from auth)")
    name: str = Field(..., description="Property name", min_length=1, max_length=200)
    description: str = Field(..., description="Property description", min_length=1)
    property_type: PropertyType = Field(..., description="Property type")
    status: PropertyStatus = Field(PropertyStatus.ACTIVE, description="Property status")
    location: Location = Field(..., description="Location details")
    neighborhood_data: NeighborhoodData = Field(
        default_factory=NeighborhoodData,
        description="Neighborhood information"
    )
    features: PropertyFeatures = Field(..., description="Property features")
    financial: FinancialInfo = Field(..., description="Financial information")
    images: List[str] = Field(default_factory=list, description="Image URLs (legacy)")
    images_v2: Optional[List[ImageSummary]] = Field(None, description="Structured image data with GridFS")
    video_url: Optional[str] = Field(None, description="Video tour URL")
    virtual_tour_url: Optional[str] = Field(None, description="Virtual tour URL")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    agent_name: Optional[str] = Field(None, description="Agent name")


class PropertyUpdate(BaseModel):
    """
    Model for updating an existing property.

    All fields are optional to allow partial updates.
    """
    name: Optional[str] = Field(None, description="Property name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Property description", min_length=1)
    property_type: Optional[PropertyType] = Field(None, description="Property type")
    status: Optional[PropertyStatus] = Field(None, description="Property status")
    location: Optional[Location] = Field(None, description="Location details")
    neighborhood_data: Optional[NeighborhoodData] = Field(None, description="Neighborhood information")
    features: Optional[PropertyFeatures] = Field(None, description="Property features")
    financial: Optional[FinancialInfo] = Field(None, description="Financial information")
    images: Optional[List[str]] = Field(None, description="Image URLs (legacy)")
    images_v2: Optional[List[ImageSummary]] = Field(None, description="Structured image data with GridFS")
    video_url: Optional[str] = Field(None, description="Video tour URL")
    virtual_tour_url: Optional[str] = Field(None, description="Virtual tour URL")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    agent_name: Optional[str] = Field(None, description="Agent name")


class PropertyFilter(BaseModel):
    """
    Model for filtering properties in list queries.

    Attributes:
        property_type: Filter by property type(s)
        status: Filter by status(es)
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        min_bedrooms: Minimum number of bedrooms
        max_bedrooms: Maximum number of bedrooms
        min_bathrooms: Minimum number of bathrooms
        max_bathrooms: Maximum number of bathrooms
        city: Filter by city name
        neighborhood: Filter by neighborhood name
        location: General location search (city, neighborhood, or address)
        pet_policy: Filter by pet policy
        has_pool: Filter properties with pool
        has_garden: Filter properties with garden
        furnished: Filter furnished properties
        limit: Number of results per page (max 100)
        offset: Pagination offset
        sort_by: Sort field (price, created_at, sqft)
        sort_order: Sort order (asc, desc)
    """
    property_type: Optional[List[PropertyType]] = Field(None, description="Property type filter")
    status: Optional[List[PropertyStatus]] = Field(None, description="Status filter")
    min_price: Optional[float] = Field(None, description="Minimum price USD", ge=0)
    max_price: Optional[float] = Field(None, description="Maximum price USD", ge=0)
    min_bedrooms: Optional[int] = Field(None, description="Minimum bedrooms", ge=0)
    max_bedrooms: Optional[int] = Field(None, description="Maximum bedrooms", ge=0)
    min_bathrooms: Optional[float] = Field(None, description="Minimum bathrooms", ge=0)
    max_bathrooms: Optional[float] = Field(None, description="Maximum bathrooms", ge=0)
    city: Optional[str] = Field(None, description="City filter")
    neighborhood: Optional[str] = Field(None, description="Neighborhood filter")
    location: Optional[str] = Field(None, description="General location search (city, neighborhood, or address)")
    pet_policy: Optional[List[PetPolicy]] = Field(None, description="Pet policy filter")
    has_pool: Optional[bool] = Field(None, description="Has pool filter")
    has_garden: Optional[bool] = Field(None, description="Has garden filter")
    furnished: Optional[bool] = Field(None, description="Furnished filter")
    limit: int = Field(20, description="Results per page", ge=1, le=100)
    offset: int = Field(0, description="Pagination offset", ge=0)
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc, desc)")

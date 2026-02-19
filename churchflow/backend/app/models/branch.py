"""
Branch database model with geolocation support.

Defines the structure for church branches with GPS coordinates for proximity-based
check-ins. Extends the original hardcoded branch constants with location data.
"""

from datetime import datetime, time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models (Pydantic v2 compatible)."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        """Pydantic v2 core schema for ObjectId validation."""
        from pydantic_core import core_schema

        return core_schema.with_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x), return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def _validate(cls, v, _info):
        """Validate and convert value to ObjectId."""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")


class ServiceSchedule(BaseModel):
    """
    Service schedule for a branch.

    Defines regular service times (e.g., Sunday 8am, 10am, midweek services).
    """
    day_of_week: str = Field(
        ...,
        description="Day of week: sunday, monday, tuesday, wednesday, thursday, friday, saturday"
    )
    service_type: str = Field(
        ...,
        description="Service type: sunday_morning, sunday_evening, midweek, prayer_meeting"
    )
    start_time: str = Field(
        ...,
        description="Start time in HH:MM format (24-hour)"
    )
    duration_minutes: int = Field(
        default=120,
        ge=30,
        le=300,
        description="Service duration in minutes (30-300)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether this service is currently active"
    )

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v: str) -> str:
        """Validate day of week."""
        valid_days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        v_lower = v.lower()
        if v_lower not in valid_days:
            raise ValueError(f"Invalid day_of_week: {v}. Must be one of {valid_days}")
        return v_lower

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        """Validate time format (HH:MM)."""
        try:
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid start_time format: {v}. Must be HH:MM (24-hour)")


class Branch(BaseModel):
    """
    Church branch with geolocation support.

    Represents a physical church branch/location with GPS coordinates for
    proximity-based auto check-in functionality.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to parent organization
        name: Branch name (e.g., "Adenta", "Legon")
        location: Human-readable location string (e.g., "Adenta, Greater Accra, Ghana")
        region: Region/area name (e.g., "Greater Accra", "Ashanti")

        latitude: GPS latitude coordinate (decimal degrees, -90 to 90)
        longitude: GPS longitude coordinate (decimal degrees, -180 to 180)
        checkin_radius: Radius in meters for auto check-in (50-5000m)
        auto_checkin_enabled: Whether proximity check-in is enabled for this branch
        geocoding_accuracy: Accuracy level of geocoded coordinates

        service_times: List of regular service schedules
        is_active: Whether branch is currently active
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: PyObjectId = Field(
        ...,
        description="Reference to parent organization"
    )

    # Core branch information
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Branch name (e.g., 'Adenta', 'Legon')"
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable location (e.g., 'Adenta, Greater Accra, Ghana')"
    )
    region: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Region/area name (e.g., 'Greater Accra', 'Ashanti')"
    )

    # Geolocation fields
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="GPS latitude coordinate (decimal degrees)"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="GPS longitude coordinate (decimal degrees)"
    )
    checkin_radius: int = Field(
        default=500,
        ge=50,
        le=5000,
        description="Check-in radius in meters (50-5000m)"
    )
    auto_checkin_enabled: bool = Field(
        default=False,
        description="Whether proximity-based auto check-in is enabled"
    )
    geocoding_accuracy: Optional[str] = Field(
        None,
        description="Geocoding accuracy: exact, street, city, approximate, or None if manual"
    )

    # Service schedule
    service_times: List[ServiceSchedule] = Field(
        default_factory=list,
        description="Regular service schedule for this branch"
    )

    # Metadata
    is_active: bool = Field(
        default=True,
        description="Whether this branch is currently active"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record last update timestamp"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "organization_id": "674e9a2b3f1234567890abcd",
                "name": "Adenta",
                "location": "Adenta, Greater Accra, Ghana",
                "region": "Greater Accra",
                "latitude": 5.7108,
                "longitude": -0.1673,
                "checkin_radius": 500,
                "auto_checkin_enabled": True,
                "geocoding_accuracy": "street",
                "service_times": [
                    {
                        "day_of_week": "sunday",
                        "service_type": "sunday_morning",
                        "start_time": "08:00",
                        "duration_minutes": 120,
                        "is_active": True
                    },
                    {
                        "day_of_week": "sunday",
                        "service_type": "sunday_evening",
                        "start_time": "18:00",
                        "duration_minutes": 90,
                        "is_active": True
                    }
                ],
                "is_active": True
            }
        }

    def has_coordinates(self) -> bool:
        """
        Check if branch has valid GPS coordinates.

        Returns:
            True if latitude and longitude are set, False otherwise
        """
        return self.latitude is not None and self.longitude is not None

    def can_auto_checkin(self) -> bool:
        """
        Check if branch supports auto check-in.

        Returns:
            True if branch has coordinates and auto check-in is enabled
        """
        return self.has_coordinates() and self.auto_checkin_enabled and self.is_active


class BranchCreate(BaseModel):
    """Schema for creating a new branch."""
    organization_id: PyObjectId
    name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=200)
    region: str = Field(..., min_length=1, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    checkin_radius: int = Field(default=500, ge=50, le=5000)
    auto_checkin_enabled: bool = Field(default=False)
    geocoding_accuracy: Optional[str] = None
    service_times: List[ServiceSchedule] = Field(default_factory=list)


class BranchUpdate(BaseModel):
    """Schema for updating an existing branch."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    region: Optional[str] = Field(None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    checkin_radius: Optional[int] = Field(None, ge=50, le=5000)
    auto_checkin_enabled: Optional[bool] = None
    geocoding_accuracy: Optional[str] = None
    service_times: Optional[List[ServiceSchedule]] = None
    is_active: Optional[bool] = None


class BranchResponse(BaseModel):
    """Schema for branch API responses."""
    id: str = Field(..., alias="_id")
    organization_id: str
    name: str
    location: str
    region: str
    latitude: Optional[float]
    longitude: Optional[float]
    checkin_radius: int
    auto_checkin_enabled: bool
    geocoding_accuracy: Optional[str]
    service_times: List[ServiceSchedule]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    has_coordinates: bool
    can_auto_checkin: bool

    class Config:
        populate_by_name = True

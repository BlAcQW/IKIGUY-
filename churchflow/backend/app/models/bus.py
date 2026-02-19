"""
Bus route database models.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.voice_greeting import VoiceGreetingConfig


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler=None):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class BusRoute(BaseModel):
    """
    Bus route model for conference transportation.

    Attributes:
        id: MongoDB document ID
        organization_id: Reference to owning organization (required for multi-tenant isolation)
        conference_id: Reference to associated conference (string or ObjectId)
        name: Name of the route (e.g., "Legon to Spintex Route")
        departure_location: Departure location name
        destination: Destination location name
        pickup_location: Pickup location name (alias for departure_location)
        pickup_coordinates: GPS coordinates [latitude, longitude]
        departure_time: Scheduled departure datetime
        arrival_time: Estimated arrival datetime
        capacity: Maximum passenger capacity
        available_seats: Number of available seats
        registered_count: Current number of registered passengers
        status: Route status (active, full, cancelled, completed)
        driver_name: Bus driver name
        driver_phone: Bus driver phone number
        bus_number: Bus identification number
        is_long_distance: Whether this is a long distance route
        gate_number: Gate number for boarding
        coordinator_id: User ID of transport coordinator
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    organization_id: Optional[str] = None  # Organization that owns this route
    conference_id: Optional[str] = None  # Can be string or ObjectId
    name: Optional[str] = Field(None, max_length=200)
    route_name: Optional[str] = Field(None, max_length=100)  # Legacy field
    departure_location: Optional[str] = Field(None, max_length=200)
    destination: Optional[str] = Field(None, max_length=200)
    pickup_location: Optional[str] = Field(None, max_length=200)
    pickup_coordinates: Optional[List[float]] = None
    departure_time: Optional[datetime] = None  # Scheduled departure datetime
    arrival_time: Optional[datetime] = None  # Estimated arrival datetime
    capacity: int = Field(default=0, ge=0, le=10000)
    available_seats: Optional[int] = Field(None, ge=0)
    registered_count: int = Field(default=0, ge=0)
    status: Optional[str] = Field(default="active")
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    bus_number: Optional[str] = None
    is_long_distance: Optional[bool] = Field(default=False)
    gate_number: Optional[str] = None
    coordinator_id: Optional[PyObjectId] = None
    voice_greeting: Optional[VoiceGreetingConfig] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "conference_id": "507f1f77bcf86cd799439011",
                "route_name": "Legon Bus #1",
                "pickup_location": "Legon Campus Main Gate",
                "pickup_coordinates": [5.6512, -0.1879],
                "departure_time": "2025-11-15T14:30:00",
                "arrival_time": "2025-11-15T16:00:00",
                "capacity": 45,
                "registered_count": 0,
                "status": "active",
                "gate_number": "Gate 3",
            }
        }


class BusRegistration(BaseModel):
    """
    Bus registration for a user (standalone bus booking).

    Attributes:
        id: MongoDB document ID
        user_id: Reference to user (optional for anonymous bookings)
        user_name: Full name of the user
        user_phone: Phone number of the user
        user_email: Email address of the user (optional)
        bus_route_id: Reference to bus route
        conference_id: Reference to conference
        registration_code: Unique registration code (e.g., "BUS-ABC123XYZ")
        registration_time: When user registered
        checked_in: Whether user has checked in at bus boarding
        check_in_time: When user checked in (if checked in)
        status: Registration status (confirmed, cancelled, boarded)
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: Optional[PyObjectId] = None  # Optional for anonymous bookings
    user_name: str = Field(..., min_length=1, max_length=200)
    user_phone: str = Field(..., min_length=1)
    user_email: Optional[str] = None
    bus_route_id: PyObjectId = Field(...)
    conference_id: Optional[PyObjectId] = None  # Optional for non-conference buses
    registration_code: str = Field(..., min_length=1)
    registration_time: datetime = Field(default_factory=datetime.utcnow)
    checked_in: bool = Field(default=False)
    check_in_time: Optional[datetime] = None
    status: str = Field(
        default="confirmed",
        pattern="^(confirmed|cancelled|boarded)$"
    )

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}

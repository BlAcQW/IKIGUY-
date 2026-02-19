"""
Bus route request/response schemas.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BusRouteResponse(BaseModel):
    """Bus route response schema."""

    id: str = Field(..., description="Bus route ID")
    conference_id: Optional[str] = Field(None, description="Conference ID")
    name: Optional[str] = Field(None, description="Route name")
    route_name: Optional[str] = Field(None, description="Route name (legacy)")
    departure_location: Optional[str] = Field(None, description="Departure location")
    destination: Optional[str] = Field(None, description="Destination location")
    pickup_location: Optional[str] = Field(None, description="Pickup location")
    pickup_coordinates: Optional[List[float]] = Field(None, description="GPS coordinates [lat, lng]")
    departure_time: Optional[datetime] = Field(None, description="Departure datetime")
    arrival_time: Optional[datetime] = Field(None, description="Arrival datetime")
    capacity: int = Field(default=0, description="Max capacity")
    available_seats: Optional[int] = Field(None, description="Available seats")
    registered_count: int = Field(default=0, description="Current registrations")
    status: Optional[str] = Field(None, description="Status (active, full, cancelled, completed)")
    driver_name: Optional[str] = Field(None, description="Driver name")
    driver_phone: Optional[str] = Field(None, description="Driver phone")
    bus_number: Optional[str] = Field(None, description="Bus number")
    is_long_distance: Optional[bool] = Field(None, description="Long distance route")
    gate_number: Optional[str] = Field(None, description="Gate number")
    coordinator_id: Optional[str] = Field(None, description="Coordinator user ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class CreateBusRouteRequest(BaseModel):
    """Request schema for creating bus route - simplified."""

    conference_id: str = Field(..., description="Conference ID")
    route_name: str = Field(..., min_length=1, max_length=100, description="Route name")
    pickup_location: str = Field(..., min_length=1, max_length=200, description="Pickup location")


class UpdateBusRouteRequest(BaseModel):
    """Request schema for updating bus route - simplified."""

    route_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Route name")
    pickup_location: Optional[str] = Field(None, min_length=1, max_length=200, description="Pickup location")
    status: Optional[str] = Field(None, pattern="^(active|full|cancelled|completed)$", description="Status")


class BusRegistrationResponse(BaseModel):
    """Bus registration response schema with QR code."""

    id: str = Field(..., description="Registration ID")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    user_name: str = Field(..., description="User full name")
    user_phone: str = Field(..., description="User phone number")
    user_email: Optional[str] = Field(None, description="User email address")
    bus_route_id: str = Field(..., description="Bus route ID")
    bus_route_name: Optional[str] = Field(None, description="Bus route name")
    conference_id: Optional[str] = Field(None, description="Conference ID (if applicable)")
    conference_name: Optional[str] = Field(None, description="Conference name (if applicable)")
    registration_code: str = Field(..., description="Unique registration code")
    qr_code: Optional[str] = Field(None, description="QR code as base64 image")
    registration_time: datetime = Field(..., description="Registration timestamp")
    checked_in: bool = Field(default=False, description="Check-in status")
    check_in_time: Optional[datetime] = Field(None, description="Check-in timestamp")
    status: str = Field(..., description="Status (confirmed, cancelled, boarded)")


class RegisterForBusRequest(BaseModel):
    """Request schema for standalone bus booking."""

    bus_route_id: str = Field(..., description="Bus route ID")
    conference_id: Optional[str] = Field(None, description="Conference ID (optional)")
    user_name: str = Field(..., min_length=1, max_length=200, description="User full name")
    user_phone: str = Field(..., min_length=1, description="User phone number")
    user_email: Optional[str] = Field(None, description="User email address (optional)")


class BusCheckInRequest(BaseModel):
    """Request schema for bus check-in."""

    registration_code: str = Field(..., min_length=1, description="Registration code from QR code")


class BusCheckInResponse(BaseModel):
    """Response schema for bus check-in."""

    success: bool = Field(..., description="Check-in successful")
    user_name: str = Field(..., description="User full name")
    user_phone: str = Field(..., description="User phone number")
    bus_route_name: Optional[str] = Field(None, description="Bus route name")
    conference_name: Optional[str] = Field(None, description="Conference name (if applicable)")
    check_in_time: datetime = Field(..., description="Check-in timestamp")
    greeting_audio: Optional[dict] = Field(None, description="Voice greeting audio (if enabled)")

"""
Auto check-in log database model.

Tracks all proximity-based auto check-in attempts for analytics,
fraud detection, and debugging purposes.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from pydantic_core import core_schema
from typing import Any


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models (Pydantic v2 compatible)."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        """Pydantic v2 core schema for ObjectId validation."""
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


class AutoCheckinLog(BaseModel):
    """
    Auto check-in attempt log.

    Records every proximity-based check-in attempt (successful and failed)
    for analytics, fraud detection, and system monitoring.

    Attributes:
        id: MongoDB document ID
        user_id: Reference to user attempting check-in
        organization_id: Reference to organization

        latitude: GPS latitude coordinate provided
        longitude: GPS longitude coordinate provided
        accuracy: GPS accuracy in meters

        branch_id: Target branch for check-in
        service_id: Target service (if applicable)
        distance_to_branch: Calculated distance in meters

        success: Whether check-in was successful
        failure_reason: Why check-in failed (if applicable)
        attendance_id: Created session_attendance record (if successful)

        suspicious_velocity: Flag for impossible travel speed
        suspicious_accuracy: Flag for poor GPS accuracy
        suspicious_spoofing: Flag for potential GPS spoofing

        user_agent: Browser/device info
        ip_address: IP address of request

        created_at: Log timestamp
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId = Field(..., description="User attempting check-in")
    organization_id: PyObjectId = Field(..., description="Organization context")

    # Location data
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="GPS latitude coordinate"
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="GPS longitude coordinate"
    )
    accuracy: float = Field(
        ...,
        ge=0,
        description="GPS accuracy in meters"
    )

    # Check-in target
    branch_id: PyObjectId = Field(..., description="Target branch")
    service_id: Optional[PyObjectId] = Field(None, description="Target service (if applicable)")
    distance_to_branch: float = Field(
        ...,
        ge=0,
        description="Calculated distance to branch in meters"
    )

    # Result
    success: bool = Field(..., description="Whether check-in succeeded")
    failure_reason: Optional[str] = Field(
        None,
        max_length=200,
        description="Reason for failure: too_far, already_checked_in, no_active_service, poor_accuracy, disabled, cooldown"
    )
    attendance_id: Optional[PyObjectId] = Field(
        None,
        description="Created session_attendance ID (if successful)"
    )

    # Fraud detection flags
    suspicious_velocity: bool = Field(
        default=False,
        description="User moved impossibly fast from last location"
    )
    suspicious_accuracy: bool = Field(
        default=False,
        description="GPS accuracy too poor (>100m)"
    )
    suspicious_spoofing: bool = Field(
        default=False,
        description="Potential GPS spoofing detected"
    )

    # Request metadata
    user_agent: Optional[str] = Field(None, max_length=500, description="Browser/device info")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address (IPv4/IPv6)")

    # Timestamp
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When attempt occurred"
    )

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "user_id": "674e9a2b3f1234567890abcd",
                "organization_id": "674e9a2b3f1234567890abce",
                "latitude": 5.7108,
                "longitude": -0.1673,
                "accuracy": 12.5,
                "branch_id": "674e9a2b3f1234567890abcf",
                "service_id": "674e9a2b3f1234567890abd0",
                "distance_to_branch": 342.5,
                "success": True,
                "failure_reason": None,
                "attendance_id": "674e9a2b3f1234567890abd1",
                "suspicious_velocity": False,
                "suspicious_accuracy": False,
                "suspicious_spoofing": False,
                "user_agent": "Mozilla/5.0...",
                "ip_address": "192.168.1.1",
                "created_at": "2025-12-09T08:15:30Z"
            }
        }


class AutoCheckinAttemptSummary(BaseModel):
    """
    Summary statistics for auto check-in attempts.

    Aggregated analytics for monitoring system performance and user behavior.
    """
    total_attempts: int = Field(default=0, description="Total check-in attempts")
    successful_attempts: int = Field(default=0, description="Successful check-ins")
    failed_attempts: int = Field(default=0, description="Failed check-ins")
    success_rate: float = Field(default=0.0, description="Success rate percentage")

    # Failure reasons breakdown
    too_far_count: int = Field(default=0, description="Failed: too far from branch")
    already_checked_in_count: int = Field(default=0, description="Failed: already checked in")
    no_active_service_count: int = Field(default=0, description="Failed: no active service")
    poor_accuracy_count: int = Field(default=0, description="Failed: poor GPS accuracy")
    disabled_count: int = Field(default=0, description="Failed: auto-checkin disabled")
    cooldown_count: int = Field(default=0, description="Failed: in cooldown period")

    # Fraud flags
    suspicious_velocity_count: int = Field(default=0, description="Flagged: suspicious velocity")
    suspicious_accuracy_count: int = Field(default=0, description="Flagged: suspicious accuracy")
    suspicious_spoofing_count: int = Field(default=0, description="Flagged: potential spoofing")

    # Distance statistics
    avg_distance: float = Field(default=0.0, description="Average distance to branch (meters)")
    min_distance: float = Field(default=0.0, description="Minimum distance (meters)")
    max_distance: float = Field(default=0.0, description="Maximum distance (meters)")

    # Accuracy statistics
    avg_accuracy: float = Field(default=0.0, description="Average GPS accuracy (meters)")
    min_accuracy: float = Field(default=0.0, description="Best GPS accuracy (meters)")
    max_accuracy: float = Field(default=0.0, description="Worst GPS accuracy (meters)")

    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")

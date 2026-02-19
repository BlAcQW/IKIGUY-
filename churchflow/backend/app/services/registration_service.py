"""
Registration service for managing conference registrations.

Provides business logic for registration updates and retrieval.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.api.routes.registrations import validate_phone_number, normalize_phone_number


class RegistrationService:
    """Service for managing conference registrations."""

    def __init__(self):
        """Initialize the registration service."""
        pass

    async def update_registration(
        self,
        registration_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a conference registration.

        Args:
            registration_id: Registration ID to update
            update_data: Dictionary of fields to update

        Returns:
            Updated registration document, or None if not found

        Raises:
            ValueError: If phone number is invalid
        """
        db = get_database()

        if not ObjectId.is_valid(registration_id):
            raise ValueError("Invalid registration ID")

        # Find existing registration
        registration = await db.conference_registrations.find_one(
            {"_id": ObjectId(registration_id)}
        )
        if not registration:
            return None

        # Build update document
        update_doc = {}

        # Handle phone number with validation and normalization
        if "user_phone" in update_data:
            phone = update_data["user_phone"]
            if phone:
                if not validate_phone_number(phone):
                    raise ValueError("Invalid phone number format")
                # normalize_phone_number returns a list of formats
                # Use the international format (starts with +) for storage
                formats = normalize_phone_number(phone)
                international_format = next((f for f in formats if f.startswith('+')), formats[0] if formats else phone)
                update_doc["user_phone"] = international_format

        # Handle other fields
        if "user_name" in update_data:
            update_doc["user_name"] = update_data["user_name"]
        if "user_email" in update_data:
            update_doc["user_email"] = update_data["user_email"] if update_data["user_email"] else None
        if "church_name" in update_data:
            update_doc["church_name"] = update_data["church_name"] if update_data["church_name"] else None
        if "special_needs" in update_data:
            update_doc["special_needs"] = update_data["special_needs"] if update_data["special_needs"] else None

        if not update_doc:
            # No fields to update
            return registration

        # Add timestamp
        update_doc["updated_at"] = datetime.utcnow()

        # Perform update
        await db.conference_registrations.update_one(
            {"_id": ObjectId(registration_id)},
            {"$set": update_doc}
        )

        # Fetch and return updated registration
        updated = await db.conference_registrations.find_one(
            {"_id": ObjectId(registration_id)}
        )

        return updated

    async def get_registration(
        self,
        registration_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a conference registration by ID.

        Args:
            registration_id: Registration ID

        Returns:
            Registration document, or None if not found
        """
        db = get_database()

        if not ObjectId.is_valid(registration_id):
            return None

        registration = await db.conference_registrations.find_one(
            {"_id": ObjectId(registration_id)}
        )

        return registration

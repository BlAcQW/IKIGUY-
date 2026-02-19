"""
Bus route management service.
"""

from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime
import logging

from app.core.database import get_database
from app.models.bus import BusRoute, BusRegistration
from app.models.voice_greeting import VoiceGreetingConfig
from app.services.voice_greeting_service import VoiceGreetingService

logger = logging.getLogger(__name__)


class BusService:
    """Service for bus route operations."""

    async def create_bus_route(self, route_data: Dict, organization_id: str) -> BusRoute:
        """
        Create new bus route.

        Args:
            route_data: Bus route data
            organization_id: Organization that owns this route

        Returns:
            Created BusRoute object
        """
        db = get_database()

        # Set default values for simplified bus route creation
        # Reason: Allow unlimited bookings without capacity/time tracking
        route_data["organization_id"] = organization_id  # Multi-tenant isolation
        route_data["created_at"] = datetime.utcnow()
        route_data["updated_at"] = datetime.utcnow()
        route_data["registered_count"] = 0
        route_data["capacity"] = 9999  # Effectively unlimited
        route_data["departure_time"] = None  # No time tracking
        route_data["arrival_time"] = None  # No time tracking
        route_data["gate_number"] = None  # Not required
        route_data["status"] = "active"  # Default status

        try:
            result = await db.bus_routes.insert_one(route_data)
            route_data["_id"] = result.inserted_id

            # Convert ObjectId to string for Pydantic validation
            if isinstance(route_data.get("conference_id"), ObjectId):
                route_data["conference_id"] = str(route_data["conference_id"])

            logger.info(f"Created bus route: {route_data.get('route_name')}")
            return BusRoute(**route_data)

        except Exception as e:
            logger.error(f"Failed to create bus route: {str(e)}")
            raise Exception(f"Failed to create bus route: {str(e)}")

    async def get_bus_route(self, route_id: str) -> Optional[BusRoute]:
        """Get bus route by ID."""
        db = get_database()

        if not ObjectId.is_valid(route_id):
            return None

        route_doc = await db.bus_routes.find_one({"_id": ObjectId(route_id)})

        if route_doc:
            # Clean datetime fields before validation
            # Reason: Handle legacy data with invalid datetime strings like "04:00 AM"
            if route_doc.get('departure_time') and isinstance(route_doc.get('departure_time'), str):
                route_doc['departure_time'] = None
            if route_doc.get('arrival_time') and isinstance(route_doc.get('arrival_time'), str):
                route_doc['arrival_time'] = None

            # Convert ObjectId to string for Pydantic validation
            # Reason: conference_id is stored as ObjectId in DB but model expects string
            if isinstance(route_doc.get('conference_id'), ObjectId):
                route_doc['conference_id'] = str(route_doc['conference_id'])

            try:
                return BusRoute(**route_doc)
            except Exception as e:
                logger.error(f"Failed to parse bus route {route_id}: {str(e)}")
                return None
        return None

    async def list_bus_routes(
        self,
        organization_id: str,
        conference_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[BusRoute]:
        """
        List bus routes with optional filters.

        Args:
            organization_id: Filter by organization (required for multi-tenant isolation)
            conference_id: Filter by conference
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of BusRoute objects
        """
        db = get_database()

        # CRITICAL: Always filter by organization_id for multi-tenant isolation
        query = {"organization_id": organization_id}

        if conference_id and ObjectId.is_valid(conference_id):
            # Check both ObjectId and string formats for conference_id
            conference_filter = {
                "$or": [
                    {"conference_id": ObjectId(conference_id)},
                    {"conference_id": conference_id}
                ]
            }
            if status:
                # Combine organization, conference, and status filters
                query["$and"] = [conference_filter, {"status": status}]
            else:
                query.update(conference_filter)
        elif status:
            query["status"] = status

        cursor = db.bus_routes.find(query).sort("departure_time", 1).limit(limit)
        routes = await cursor.to_list(length=limit)

        # Parse routes with error handling for invalid data
        valid_routes = []
        for route in routes:
            # Clean datetime fields before validation
            # Reason: Handle legacy data with invalid datetime strings like "04:00 AM"
            if route.get('departure_time') and isinstance(route.get('departure_time'), str):
                route['departure_time'] = None
            if route.get('arrival_time') and isinstance(route.get('arrival_time'), str):
                route['arrival_time'] = None

            # Convert ObjectId to string for Pydantic validation
            # Reason: conference_id is stored as ObjectId in DB but model expects string
            if isinstance(route.get('conference_id'), ObjectId):
                route['conference_id'] = str(route['conference_id'])

            try:
                valid_routes.append(BusRoute(**route))
            except Exception as e:
                logger.error(f"Skipping invalid bus route {route.get('_id')}: {str(e)}")
                continue

        return valid_routes

    async def update_bus_route(self, route_id: str, organization_id: str, update_data: Dict) -> Optional[BusRoute]:
        """
        Update bus route.

        Args:
            route_id: Bus route ID
            organization_id: Organization ID (for ownership verification)
            update_data: Fields to update

        Returns:
            Updated BusRoute object
        """
        db = get_database()

        if not ObjectId.is_valid(route_id):
            return None

        update_data["updated_at"] = datetime.utcnow()

        try:
            # CRITICAL: Verify route belongs to organization before update
            result = await db.bus_routes.find_one_and_update(
                {
                    "_id": ObjectId(route_id),
                    "organization_id": organization_id  # Multi-tenant isolation
                },
                {"$set": update_data},
                return_document=True
            )

            if result:
                # Convert ObjectId to string for Pydantic validation
                if isinstance(result.get("conference_id"), ObjectId):
                    result["conference_id"] = str(result["conference_id"])

                logger.info(f"Updated bus route: {route_id}")
                return BusRoute(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to update bus route: {str(e)}")
            raise Exception(f"Failed to update bus route: {str(e)}")

    async def update_voice_greeting(
        self,
        route_id: str,
        voice_greeting_config: Dict
    ) -> Optional[BusRoute]:
        """
        Update voice greeting configuration for a bus route.

        Args:
            route_id: Bus route ID
            voice_greeting_config: Voice greeting configuration data

        Returns:
            Updated BusRoute object
        """
        db = get_database()

        if not ObjectId.is_valid(route_id):
            return None

        try:
            # Get current route
            route = await self.get_bus_route(route_id)
            if not route:
                return None

            # Merge with existing config if present
            current_config = route.voice_greeting.model_dump() if route.voice_greeting else {}
            updated_config = {**current_config, **voice_greeting_config}

            # Create VoiceGreetingConfig object to validate
            greeting_config = VoiceGreetingConfig(**updated_config)

            # Update in database
            result = await db.bus_routes.find_one_and_update(
                {"_id": ObjectId(route_id)},
                {
                    "$set": {
                        "voice_greeting": greeting_config.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )

            if result:
                logger.info(f"Updated voice greeting for bus route: {route_id}")
                return BusRoute(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to update voice greeting: {str(e)}")
            raise Exception(f"Failed to update voice greeting: {str(e)}")

    async def delete_bus_route(self, route_id: str, organization_id: str) -> bool:
        """
        Delete bus route.

        Args:
            route_id: Bus route ID
            organization_id: Organization ID (for ownership verification)

        Returns:
            True if deleted successfully
        """
        db = get_database()

        if not ObjectId.is_valid(route_id):
            return False

        try:
            # CRITICAL: Verify route belongs to organization before delete
            result = await db.bus_routes.delete_one({
                "_id": ObjectId(route_id),
                "organization_id": organization_id  # Multi-tenant isolation
            })

            if result.deleted_count > 0:
                # Also delete all registrations for this route
                await db.bus_registrations.delete_many({"bus_route_id": ObjectId(route_id)})
                logger.info(f"Deleted bus route: {route_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete bus route: {str(e)}")
            raise Exception(f"Failed to delete bus route: {str(e)}")

    async def register_for_bus(
        self,
        user_name: str,
        user_phone: str,
        user_email: Optional[str],
        bus_route_id: str,
        conference_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> BusRegistration:
        """
        Register user for bus route (standalone booking).

        Args:
            user_name: User's full name
            user_phone: User's phone number
            user_email: User's email (optional)
            bus_route_id: Bus route ID
            conference_id: Conference ID (optional - for conference-linked routes)
            user_id: User ID (optional, for authenticated users)

        Returns:
            BusRegistration object with registration code
        """
        db = get_database()

        # Check if route exists
        route = await self.get_bus_route(bus_route_id)
        if not route:
            raise Exception("Bus route not found")

        # Check if phone already registered for this bus route
        # Reason: Prevent duplicate bookings per route instead of per conference
        existing = await db.bus_registrations.find_one({
            "user_phone": user_phone,
            "bus_route_id": ObjectId(bus_route_id),
            "status": "confirmed"
        })

        if existing:
            raise Exception("This phone number is already registered for this bus route")

        # Generate unique registration code
        registration_code = self._generate_bus_registration_code()
        while await db.bus_registrations.find_one({"registration_code": registration_code}):
            registration_code = self._generate_bus_registration_code()

        # Create registration
        registration_data = {
            "user_id": ObjectId(user_id) if user_id else None,
            "user_name": user_name,
            "user_phone": user_phone,
            "user_email": user_email,
            "bus_route_id": ObjectId(bus_route_id),
            "conference_id": ObjectId(conference_id) if conference_id else None,
            "registration_code": registration_code,
            "registration_time": datetime.utcnow(),
            "checked_in": False,
            "check_in_time": None,
            "status": "confirmed"
        }

        try:
            result = await db.bus_registrations.insert_one(registration_data)
            registration_data["_id"] = result.inserted_id

            # Increment registered count for statistics
            # Reason: Keep count for reporting, but no capacity limit enforcement
            await db.bus_routes.update_one(
                {"_id": ObjectId(bus_route_id)},
                {
                    "$inc": {"registered_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            logger.info(f"User {user_name} ({user_phone}) registered for bus {bus_route_id}")
            return BusRegistration(**registration_data)

        except Exception as e:
            logger.error(f"Failed to register for bus: {str(e)}")
            raise Exception(f"Failed to register for bus: {str(e)}")

    def _generate_bus_registration_code(self) -> str:
        """Generate unique bus registration code."""
        import secrets
        return f"BUS-{secrets.token_urlsafe(8).upper()}"

    async def check_in_bus_registration(
        self,
        registration_code: str
    ) -> BusRegistration:
        """
        Check in a bus registration using QR code.

        Args:
            registration_code: Unique registration code

        Returns:
            Updated BusRegistration
        """
        db = get_database()

        # Find registration
        registration = await db.bus_registrations.find_one({
            "registration_code": registration_code,
            "status": "confirmed"
        })

        if not registration:
            raise Exception("Registration not found or cancelled")

        if registration.get("checked_in"):
            check_in_time = registration.get("check_in_time")
            time_str = check_in_time.isoformat() if check_in_time else "unknown time"
            raise Exception(f"Already checked in at {time_str}")

        # Update check-in status
        await db.bus_registrations.update_one(
            {"_id": registration["_id"]},
            {
                "$set": {
                    "checked_in": True,
                    "check_in_time": datetime.utcnow()
                }
            }
        )

        # Get updated registration
        registration = await db.bus_registrations.find_one({"_id": registration["_id"]})
        logger.info(f"Bus registration {registration_code} checked in successfully")
        return BusRegistration(**registration)

    async def clear_all_registrations(self) -> Dict:
        """
        Clear all bus registrations and reset all bus route counters to 0.

        ADMIN ONLY - This will delete all registration records from the database
        and reset the registered_count field on all bus routes.

        Returns:
            Dict with counts of deleted registrations and updated routes
        """
        db = get_database()

        try:
            # Count registrations before deletion
            registrations_count = await db.bus_registrations.count_documents({})

            # Delete all bus registration records
            # Reason: Complete cleanup of all user registrations
            delete_result = await db.bus_registrations.delete_many({})

            # Reset registered_count to 0 for all bus routes
            # Reason: Sync counter with empty registrations collection
            update_result = await db.bus_routes.update_many(
                {},
                {
                    "$set": {
                        "registered_count": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.warning(
                f"ADMIN ACTION: Cleared all bus registrations. "
                f"Deleted: {delete_result.deleted_count} registrations, "
                f"Updated: {update_result.modified_count} bus routes"
            )

            return {
                "deleted_registrations": delete_result.deleted_count,
                "updated_routes": update_result.modified_count,
                "success": True,
                "message": f"Successfully deleted {delete_result.deleted_count} registrations and reset {update_result.modified_count} bus routes"
            }

        except Exception as e:
            logger.error(f"Failed to clear all registrations: {str(e)}")
            raise Exception(f"Failed to clear all registrations: {str(e)}")


# Global bus service instance
bus_service = BusService()

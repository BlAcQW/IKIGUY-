"""
Conference management service.
"""

from typing import List, Optional, Dict
from bson import ObjectId
from datetime import datetime
import logging
import secrets
import hashlib

from app.core.database import get_database
from app.models.conference import Conference, ConferenceRegistration
from app.models.voice_greeting import VoiceGreetingConfig
from app.services.voice_greeting_service import VoiceGreetingService

logger = logging.getLogger(__name__)


class ConferenceService:
    """Service for conference operations."""

    def _generate_qr_code(self, user_id: str, conference_id: str) -> str:
        """
        Generate unique QR code for user registration.

        Args:
            user_id: User ID
            conference_id: Conference ID

        Returns:
            Unique QR code string
        """
        # Create deterministic but unique hash
        data = f"{user_id}:{conference_id}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    async def create_conference(self, conference_data: Dict) -> Conference:
        """
        Create new conference.

        Args:
            conference_data: Conference data

        Returns:
            Created Conference object
        """
        db = get_database()

        conference_data["created_at"] = datetime.utcnow()
        conference_data["updated_at"] = datetime.utcnow()
        conference_data["current_attendees"] = 0

        try:
            result = await db.conferences.insert_one(conference_data)
            conference_data["_id"] = result.inserted_id

            logger.info(f"Created conference: {conference_data.get('name')}")
            return Conference(**conference_data)

        except Exception as e:
            logger.error(f"Failed to create conference: {str(e)}")
            raise Exception(f"Failed to create conference: {str(e)}")

    async def get_conference(self, conference_id: str) -> Optional[Conference]:
        """
        Get conference by ID with dynamically calculated current_attendees.
        
        Args:
            conference_id: Conference ID
            
        Returns:
            Conference object with accurate current_attendees count
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return None

        conf_doc = await db.conferences.find_one({"_id": ObjectId(conference_id)})

        if conf_doc:
            # Calculate current_attendees dynamically from actual registrations
            registration_count = await db.conference_registrations.count_documents({
                "conference_id": ObjectId(conference_id),
                "status": "confirmed"
            })
            conf_doc["current_attendees"] = registration_count
            return Conference(**conf_doc)
        return None

    async def list_conferences(
        self,
        status: Optional[str] = None,
        registration_open: Optional[bool] = None,
        limit: int = 100
    ) -> List[Conference]:
        """
        List conferences with optional filters.

        Args:
            status: Filter by status
            registration_open: Filter by registration status
            limit: Maximum number of results

        Returns:
            List of Conference objects with dynamically calculated current_attendees
        """
        db = get_database()

        query = {}
        if status:
            query["status"] = status
        if registration_open is not None:
            query["registration_open"] = registration_open

        cursor = db.conferences.find(query).sort("start_date", -1).limit(limit)
        conferences = await cursor.to_list(length=limit)

        # Calculate current_attendees dynamically for each conference
        result = []
        for conf in conferences:
            # Count actual confirmed registrations
            registration_count = await db.conference_registrations.count_documents({
                "conference_id": conf["_id"],
                "status": "confirmed"
            })
            # Update the current_attendees field with actual count
            conf["current_attendees"] = registration_count
            result.append(Conference(**conf))

        return result

    async def update_conference(
        self,
        conference_id: str,
        update_data: Dict
    ) -> Optional[Conference]:
        """
        Update conference.

        Args:
            conference_id: Conference ID
            update_data: Fields to update

        Returns:
            Updated Conference object
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return None

        update_data["updated_at"] = datetime.utcnow()

        try:
            result = await db.conferences.find_one_and_update(
                {"_id": ObjectId(conference_id)},
                {"$set": update_data},
                return_document=True
            )

            if result:
                logger.info(f"Updated conference: {conference_id}")
                return Conference(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to update conference: {str(e)}")
            raise Exception(f"Failed to update conference: {str(e)}")

    async def update_voice_greeting(
        self,
        conference_id: str,
        voice_greeting_config: Dict
    ) -> Optional[Conference]:
        """
        Update voice greeting configuration for a conference.

        Args:
            conference_id: Conference ID
            voice_greeting_config: Voice greeting configuration data

        Returns:
            Updated Conference object
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return None

        try:
            # Get current conference
            conference = await self.get_conference(conference_id)
            if not conference:
                return None

            # Merge with existing config if present
            current_config = conference.voice_greeting.model_dump() if conference.voice_greeting else {}
            updated_config = {**current_config, **voice_greeting_config}

            # Create VoiceGreetingConfig object to validate
            greeting_config = VoiceGreetingConfig(**updated_config)

            # Update in database
            result = await db.conferences.find_one_and_update(
                {"_id": ObjectId(conference_id)},
                {
                    "$set": {
                        "voice_greeting": greeting_config.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )

            if result:
                logger.info(f"Updated voice greeting for conference: {conference_id}")
                return Conference(**result)

            return None

        except Exception as e:
            logger.error(f"Failed to update voice greeting: {str(e)}")
            raise Exception(f"Failed to update voice greeting: {str(e)}")

    async def delete_conference(self, conference_id: str) -> bool:
        """
        Delete conference.

        Args:
            conference_id: Conference ID

        Returns:
            True if deleted successfully
        """
        db = get_database()

        if not ObjectId.is_valid(conference_id):
            return False

        try:
            result = await db.conferences.delete_one({"_id": ObjectId(conference_id)})

            if result.deleted_count > 0:
                # Also delete all registrations for this conference
                await db.conference_registrations.delete_many(
                    {"conference_id": ObjectId(conference_id)}
                )
                logger.info(f"Deleted conference: {conference_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete conference: {str(e)}")
            raise Exception(f"Failed to delete conference: {str(e)}")

    async def register_for_conference(
        self,
        user_id: str,
        conference_id: str
    ) -> ConferenceRegistration:
        """
        Register user for conference.

        Args:
            user_id: User ID
            conference_id: Conference ID

        Returns:
            ConferenceRegistration object
        """
        db = get_database()

        # Check if conference exists
        conference = await self.get_conference(conference_id)
        if not conference:
            raise Exception("Conference not found")

        if not conference.registration_open:
            raise Exception("Registration is closed")

        # Check if max attendees reached
        if conference.max_attendees and conference.current_attendees >= conference.max_attendees:
            raise Exception("Conference is full")

        # Check if user already registered
        existing = await db.conference_registrations.find_one({
            "user_id": ObjectId(user_id),
            "conference_id": ObjectId(conference_id),
            "status": "confirmed"
        })

        if existing:
            raise Exception("User already registered for this conference")

        # Generate unique QR code
        qr_code = self._generate_qr_code(user_id, conference_id)

        # Create registration
        registration_data = {
            "user_id": ObjectId(user_id),
            "conference_id": ObjectId(conference_id),
            "qr_code": qr_code,
            "registration_time": datetime.utcnow(),
            "checked_in": False,
            "status": "confirmed"
        }

        try:
            result = await db.conference_registrations.insert_one(registration_data)
            registration_data["_id"] = result.inserted_id

            # Increment attendee count
            await db.conferences.update_one(
                {"_id": ObjectId(conference_id)},
                {
                    "$inc": {"current_attendees": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            logger.info(f"User {user_id} registered for conference {conference_id}")
            return ConferenceRegistration(**registration_data)

        except Exception as e:
            logger.error(f"Failed to register for conference: {str(e)}")
            raise Exception(f"Failed to register for conference: {str(e)}")

    async def check_in_user(self, qr_code: str) -> Dict:
        """
        Check in user using QR code.

        Args:
            qr_code: User's QR code

        Returns:
            Dict with check-in result and user info, including optional greeting audio
        """
        db = get_database()

        # Find registration by QR code
        registration = await db.conference_registrations.find_one({
            "qr_code": qr_code,
            "status": "confirmed"
        })

        if not registration:
            raise Exception("Invalid QR code or registration not found")

        if registration.get("checked_in"):
            raise Exception("User already checked in")

        # Get user info
        user = await db.users.find_one({"_id": registration["user_id"]})
        if not user:
            raise Exception("User not found")

        # Get conference info with voice greeting config
        conference_doc = await db.conferences.find_one({"_id": registration["conference_id"]})
        if not conference_doc:
            raise Exception("Conference not found")

        conference = Conference(**conference_doc)

        # Update registration
        check_in_time = datetime.utcnow()
        await db.conference_registrations.update_one(
            {"_id": registration["_id"]},
            {
                "$set": {
                    "checked_in": True,
                    "check_in_time": check_in_time
                }
            }
        )

        logger.info(f"Checked in user {user.get('name')} for conference {conference.name}")

        # Build response
        response = {
            "success": True,
            "user_name": user.get("name"),
            "user_phone": user.get("phone"),
            "conference_name": conference.name,
            "check_in_time": check_in_time
        }

        # Generate voice greeting if enabled
        if conference.voice_greeting and conference.voice_greeting.enabled:
            try:
                voice_greeting_service = VoiceGreetingService()

                # Prepare user data for personalization
                user_data = {
                    "user_name": user.get("name"),
                    "phone": user.get("phone"),
                    "branch_name": user.get("branch_name", ""),
                    "volunteer_roles": user.get("volunteer_roles", [])
                }

                # Prepare event data
                event_data = {
                    "conference_name": conference.name,
                    "venue": conference.venue
                }

                # Get user ID for billing
                user_id = str(user.get("_id", ""))

                # Generate greeting
                greeting_audio = await voice_greeting_service.generate_greeting(
                    user_data=user_data,
                    event_data=event_data,
                    config=conference.voice_greeting,
                    user_id=user_id
                )

                if greeting_audio:
                    response["greeting_audio"] = greeting_audio.model_dump()
                    logger.info(f"Generated voice greeting for {user.get('name')}")

            except Exception as e:
                logger.error(f"Failed to generate voice greeting: {e}")
                # Don't fail the check-in if greeting generation fails
                pass

        return response


# Global conference service instance
conference_service = ConferenceService()

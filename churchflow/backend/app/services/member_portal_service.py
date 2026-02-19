"""
Member Portal Service for ChurchFlow

Handles member self-service operations: profile management, preferences, activity tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


class MemberPortalService:
    """
    Member portal service for self-service operations.

    Provides:
    - Profile viewing and editing
    - Preference management
    - Activity tracking
    - Member directory access
    - Volunteer role management
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize member portal service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.users_collection = db.users
        self.preferences_collection = db.member_preferences
        self.registrations_collection = db.registrations
        self.conferences_collection = db.conferences

    # ==================== Profile Management ====================

    async def get_member_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get member's own profile.

        Args:
            user_id: User ID

        Returns:
            User profile dict or None
        """
        # Try supabase_id first (for JWT tokens), fallback to MongoDB _id
        user = await self.users_collection.find_one({"supabase_id": user_id})
        if not user:
            try:
                user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            except:
                pass

        if user:
            user["_id"] = str(user["_id"])
            # Convert ObjectIds to strings
            if user.get("branch_id"):
                user["branch_id"] = str(user["branch_id"])
            return user
        return None

    async def update_member_profile(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update member's own profile.

        Args:
            user_id: User ID
            update_data: Fields to update

        Returns:
            Updated profile or None
        """
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        if not update_data:
            return await self.get_member_profile(user_id)

        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Update user - try supabase_id first, fallback to _id
        query = {"supabase_id": user_id}
        existing_user = await self.users_collection.find_one(query)
        if not existing_user:
            try:
                query = {"_id": ObjectId(user_id)}
            except:
                return None

        result = await self.users_collection.update_one(
            query,
            {"$set": update_data}
        )

        if result.modified_count > 0:
            return await self.get_member_profile(user_id)

        return None

    # ==================== Preferences Management ====================

    async def get_member_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get member's preferences.

        Args:
            user_id: User ID

        Returns:
            Preferences dict
        """
        prefs = await self.preferences_collection.find_one({"user_id": user_id})

        if not prefs:
            # Return defaults
            return {
                "user_id": user_id,
                "notifications": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True,
                    "event_reminders": True,
                    "giving_receipts": True,
                    "newsletter": True,
                    "prayer_requests": True
                },
                "privacy": {
                    "show_profile_in_directory": True,
                    "show_phone_number": False,
                    "show_email": False,
                    "show_address": False,
                    "allow_contact_from_members": True
                },
                "language": "en",
                "timezone": "UTC",
                "updated_at": datetime.utcnow()
            }

        prefs["_id"] = str(prefs["_id"])
        return prefs

    async def update_member_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update member's preferences.

        Args:
            user_id: User ID
            preferences: Preferences to update

        Returns:
            Updated preferences
        """
        update_data = {**preferences, "updated_at": datetime.utcnow()}

        await self.preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )

        return await self.get_member_preferences(user_id)

    # ==================== Activity Tracking ====================

    async def get_member_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Get member's activity summary.

        Args:
            user_id: User ID

        Returns:
            Activity summary dict
        """
        # Try supabase_id first (for JWT tokens), fallback to MongoDB _id
        user = await self.users_collection.find_one({"supabase_id": user_id})
        if not user:
            try:
                user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            except:
                pass

        # Count conference registrations
        registrations_cursor = self.registrations_collection.find({
            "user_id": user_id
        })
        registrations = await registrations_cursor.to_list(length=None)
        conferences_attended = sum(1 for r in registrations if r.get("checked_in"))

        # Count donations (if donor profile exists)
        donor_profile = await self.db.donor_profiles.find_one({
            "user_id": user_id
        })

        donations_made = donor_profile.get("donation_count", 0) if donor_profile else 0
        last_donation = donor_profile.get("last_donation_date") if donor_profile else None

        # Get last attendance
        last_attendance = None
        if registrations:
            checked_in_registrations = [r for r in registrations if r.get("checked_in")]
            if checked_in_registrations:
                checked_in_registrations.sort(key=lambda x: x.get("check_in_time", x.get("created_at")), reverse=True)
                last_attendance = checked_in_registrations[0].get("check_in_time") or checked_in_registrations[0].get("created_at")

        return {
            "conferences_attended": conferences_attended,
            "events_registered": len(registrations),
            "donations_made": donations_made,
            "volunteer_hours": 0.0,  # TODO: Implement volunteer hours tracking
            "cell_group": user.get("cell_group_name") if user else None,
            "last_attendance": last_attendance,
            "last_donation": last_donation,
            "member_since": user.get("joined_at") if user else None
        }

    async def get_member_dashboard(
        self,
        user_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Get complete member dashboard data.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            Dashboard data
        """
        # Get profile
        profile = await self.get_member_profile(user_id)
        
        if not profile:
            # Return empty dashboard if profile not found
            return {
                "profile": None,
                "activity": {
                    "conferences_attended": 0,
                    "events_registered": 0,
                    "donations_made": 0,
                    "volunteer_hours": 0.0,
                    "cell_group": None,
                    "last_attendance": None,
                    "last_donation": None,
                    "member_since": None
                },
                "upcoming_conferences": [],
                "recent_donations": [],
                "notification_count": 0,
                "unread_messages": 0
            }

        # Get activity
        activity = await self.get_member_activity(user_id)

        # Get upcoming conferences
        upcoming_conferences = await self._get_upcoming_conferences(user_id)

        # Get recent donations
        recent_donations = []
        try:
            if await self.db.donations.count_documents({"donor_id": user_id}) > 0:
                cursor = self.db.donations.find({
                    "donor_id": user_id,
                    "status": "completed"
                }).sort("completed_at", -1).limit(5)
                recent_donations = await cursor.to_list(length=5)
                for donation in recent_donations:
                    donation["_id"] = str(donation["_id"])
        except Exception as e:
            # Log error but don't fail the entire dashboard
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error fetching donations for user {user_id}: {str(e)}")

        return {
            "profile": profile,
            "activity": activity,
            "upcoming_conferences": upcoming_conferences,
            "recent_donations": recent_donations,
            "notification_count": 0,  # TODO: Implement notifications
            "unread_messages": 0  # TODO: Implement messaging
        }

    async def _get_upcoming_conferences(self, user_id: str) -> List[Dict[str, Any]]:
        """Get member's upcoming conference registrations"""
        now = datetime.utcnow()

        # Get registrations
        cursor = self.registrations_collection.find({"user_id": user_id})
        registrations = await cursor.to_list(length=None)

        upcoming = []
        for reg in registrations:
            try:
                # Validate conference_id before converting to ObjectId
                conference_id = reg.get("conference_id")
                if not conference_id:
                    continue
                    
                # Try to convert to ObjectId if it's a string
                if isinstance(conference_id, str):
                    if not ObjectId.is_valid(conference_id):
                        continue
                    conference_id = ObjectId(conference_id)
                elif not isinstance(conference_id, ObjectId):
                    continue

                # Get conference details
                conference = await self.conferences_collection.find_one({
                    "_id": conference_id
                })

                if conference and conference.get("start_date", now) >= now:
                    upcoming.append({
                        "conference_id": str(conference["_id"]),
                        "conference_name": conference.get("name", ""),
                        "start_date": conference.get("start_date"),
                        "end_date": conference.get("end_date"),
                        "registration_date": reg.get("created_at"),
                        "checked_in": reg.get("checked_in", False),
                        "qr_code": reg.get("qr_code")
                    })
            except Exception as e:
                # Log error but continue processing other registrations
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error processing registration {reg.get('_id')}: {str(e)}")
                continue

        # Sort by start date
        upcoming.sort(key=lambda x: x.get("start_date") or now)
        return upcoming[:5]  # Limit to 5 upcoming

    # ==================== Member Directory ====================

    async def get_member_directory(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get member directory (respecting privacy settings).

        Args:
            organization_id: Organization ID
            page: Page number
            page_size: Items per page
            search: Search term

        Returns:
            Paginated member list
        """
        try:
            import logging
            logger = logging.getLogger(__name__)

            # Convert organization_id to ObjectId for proper querying
            try:
                org_id_obj = ObjectId(organization_id)
            except Exception:
                org_id_obj = organization_id

            # Query users directly from users collection with organization_id
            # This is the primary source of members (9000+ users)
            base_query: Dict[str, Any] = {"organization_id": org_id_obj}

            # Add search filter if provided
            if search:
                search_regex = {"$regex": search, "$options": "i"}
                base_query["$or"] = [
                    {"name": search_regex},
                    {"full_name": search_regex},
                    {"phone": search_regex},
                    {"email": search_regex}
                ]

            # Get total count
            total = await self.db.users.count_documents(base_query)
            logger.info(f"[get_member_directory] Found {total} members for org {organization_id}")

            if total == 0:
                return {
                    "members": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "has_more": False
                }

            # Get paginated results directly from users collection
            skip = (page - 1) * page_size
            cursor = self.db.users.find(base_query).sort("full_name", 1).skip(skip).limit(page_size)
            users = await cursor.to_list(length=page_size)
            logger.info(f"[get_member_directory] Retrieved {len(users)} users for page {page}")

            # Format results
            members = []
            for user in users:
                user_id = str(user["_id"])
                prefs = await self.get_member_preferences(user_id)

                member = {
                    "_id": user_id,
                    "full_name": user.get("full_name") or user.get("name", ""),
                    "profile_picture_url": user.get("profile_picture_url"),
                    "cell_group": user.get("cell_group_name"),
                    "roles": user.get("roles", []),
                    "volunteer_roles": user.get("volunteer_roles", []),
                    "joined_at": user.get("joined_at")
                }

                # Add email/phone only if privacy allows
                if prefs.get("privacy", {}).get("show_email"):
                    member["email"] = user.get("email")
                if prefs.get("privacy", {}).get("show_phone_number"):
                    member["phone"] = user.get("phone")

                members.append(member)

            return {
                "members": members,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_more": skip + len(members) < total
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching member directory for org {organization_id}: {str(e)}", exc_info=True)
            # Return empty result on error rather than crashing
            return {
                "members": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_more": False
            }

    # ==================== Event Registrations ====================

    async def get_my_registrations(self, user_id: str) -> Dict[str, Any]:
        """
        Get member's event registrations.

        Args:
            user_id: User ID

        Returns:
            Registration summary
        """
        now = datetime.utcnow()

        cursor = self.registrations_collection.find({"user_id": user_id})
        registrations = await cursor.to_list(length=None)

        upcoming = []
        past = []

        for reg in registrations:
            conference = await self.conferences_collection.find_one({
                "_id": ObjectId(reg["conference_id"])
            })

            if not conference:
                continue

            summary = {
                "conference_id": str(conference["_id"]),
                "conference_name": conference.get("name", ""),
                "start_date": conference.get("start_date"),
                "end_date": conference.get("end_date"),
                "registration_date": reg.get("created_at"),
                "checked_in": reg.get("checked_in", False),
                "qr_code": reg.get("qr_code")
            }

            if conference.get("start_date", now) >= now:
                upcoming.append(summary)
            else:
                past.append(summary)

        # Sort
        upcoming.sort(key=lambda x: x["start_date"])
        past.sort(key=lambda x: x["start_date"], reverse=True)

        total_attended = sum(1 for r in registrations if r.get("checked_in"))
        attendance_rate = (total_attended / len(registrations) * 100) if registrations else 0

        return {
            "upcoming": upcoming,
            "past": past,
            "total_registered": len(registrations),
            "total_attended": total_attended,
            "attendance_rate": attendance_rate
        }


# Singleton instance
_member_portal_service: Optional[MemberPortalService] = None


def get_member_portal_service(db: AsyncIOMotorDatabase) -> MemberPortalService:
    """Get or create member portal service singleton"""
    global _member_portal_service
    if _member_portal_service is None:
        _member_portal_service = MemberPortalService(db)
    return _member_portal_service

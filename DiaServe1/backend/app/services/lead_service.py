"""
Lead Service for DiaServe.

Auto-creates contacts as warm/hot leads from property interactions.
Handles deduplication by email+org and interest_status escalation.
"""

from datetime import datetime
from typing import Optional
import logging

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.campaign import InterestStatus, LeadStatus

logger = logging.getLogger(__name__)


class LeadService:
    """Service for upserting leads from property interactions."""

    INTEREST_RANK = {
        InterestStatus.UNQUALIFIED.value: 0,
        InterestStatus.COLD.value: 1,
        InterestStatus.WARM.value: 2,
        InterestStatus.HOT.value: 3,
    }

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database["contacts"]

    async def upsert_lead(
        self,
        organization_id: str,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        interest_status: str,
        source: str,
        property_id: Optional[str] = None,
        property_name: Optional[str] = None,
    ) -> dict:
        """
        Create or update a contact lead with escalation logic.

        Deduplicates by email+organization_id (or phone+organization_id).
        Escalates interest_status only upward (warm->hot, never hot->warm).

        Args:
            organization_id: Organization the property belongs to
            name: Contact's name
            email: Contact's email
            phone: Contact's phone
            interest_status: Desired interest status (warm/hot)
            source: Lead source (property_save, tour_booking, lead_form)
            property_id: Optional property ID
            property_name: Optional property name

        Returns:
            Dict with contact_id, created, and escalated flags
        """
        now = datetime.utcnow()

        logger.debug(
            f"upsert_lead called: org={organization_id}, email={email}, "
            f"phone={phone}, status={interest_status}, source={source}"
        )

        property_entry = None
        if property_id:
            property_entry = {
                "property_id": property_id,
                "property_name": property_name,
                "source": source,
                "timestamp": now,
            }

        # Try to find existing contact by email+org or phone+org
        existing = None
        if email:
            existing = await self.collection.find_one({
                "email": email,
                "organization_id": organization_id,
            })
        if not existing and phone:
            existing = await self.collection.find_one({
                "phone": phone,
                "organization_id": organization_id,
            })

        if existing:
            return await self._update_existing(
                existing, interest_status, source, property_entry, now
            )

        return await self._create_new(
            organization_id, name, email, phone,
            interest_status, source, property_entry, now
        )

    async def _create_new(
        self,
        organization_id: str,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        interest_status: str,
        source: str,
        property_entry: Optional[dict],
        now: datetime,
    ) -> dict:
        """Insert a new contact document."""
        contact_id = str(ObjectId())

        properties_interested = []
        if property_entry:
            properties_interested.append(property_entry)

        contact_doc = {
            "id": contact_id,
            "organization_id": organization_id,
            "name": name,
            "email": email,
            "phone": phone,
            "property_type_preferences": [],
            "location_preferences": [],
            "budget_min": None,
            "budget_max": None,
            "bedrooms_min": None,
            "bedrooms_max": None,
            "interest_status": interest_status,
            "lead_status": LeadStatus.NEW.value,
            "tags": [source],
            "source": source,
            "opt_out_channels": [],
            "notes": None,
            "metadata": {
                "properties_interested": properties_interested,
            },
            "created_at": now,
            "updated_at": now,
            "last_contacted": None,
        }

        await self.collection.insert_one(contact_doc)

        logger.info(
            f"Created lead {contact_id} ({interest_status}) "
            f"from {source} for org {organization_id}"
        )

        return {"contact_id": contact_id, "created": True, "escalated": False}

    async def _update_existing(
        self,
        existing: dict,
        interest_status: str,
        source: str,
        property_entry: Optional[dict],
        now: datetime,
    ) -> dict:
        """Update an existing contact with escalation logic."""
        contact_id = existing["id"]
        current_status = existing.get("interest_status", InterestStatus.COLD.value)
        new_rank = self.INTEREST_RANK.get(interest_status, 0)
        current_rank = self.INTEREST_RANK.get(current_status, 0)

        update_ops: dict = {
            "$set": {"updated_at": now},
            "$addToSet": {"tags": source},
        }

        escalated = False
        if new_rank > current_rank:
            update_ops["$set"]["interest_status"] = interest_status
            escalated = True

        if property_entry:
            update_ops["$push"] = {
                "metadata.properties_interested": property_entry,
            }

        await self.collection.update_one(
            {"id": contact_id},
            update_ops,
        )

        logger.info(
            f"Updated lead {contact_id} from {source} "
            f"(escalated={escalated}, {current_status}->{interest_status})"
        )

        return {"contact_id": contact_id, "created": False, "escalated": escalated}

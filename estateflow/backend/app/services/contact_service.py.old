"""
Contact Service for EstateFlow.

Manages contacts/leads for marketing campaigns.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.campaign import (
    Contact,
    ContactCreate,
    ContactUpdate,
    SegmentFilter,
    CampaignType
)

logger = logging.getLogger(__name__)


class ContactService:
    """Service for managing contacts and leads."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize contact service.

        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection = database["contacts"]

    async def create_contact(
        self,
        contact_data: ContactCreate,
        organization_id: str,
        user_id: str
    ) -> Contact:
        """
        Create a new contact.

        Args:
            contact_data: Contact creation data
            organization_id: Organization ID
            user_id: User ID creating the contact

        Returns:
            Created contact
        """
        from bson import ObjectId

        # Generate ID
        contact_id = str(ObjectId())

        # Build contact document
        contact_dict = contact_data.dict()
        contact_dict.update({
            "id": contact_id,
            "organization_id": organization_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_contacted": None,
            "opt_out_channels": [],
            "metadata": {}
        })

        # Insert into database
        await self.collection.insert_one(contact_dict)

        logger.info(f"Created contact {contact_id} for organization {organization_id}")

        return Contact(**contact_dict)

    async def get_contact(
        self,
        contact_id: str,
        organization_id: str
    ) -> Optional[Contact]:
        """
        Get a contact by ID.

        Args:
            contact_id: Contact ID
            organization_id: Organization ID for access control

        Returns:
            Contact if found, None otherwise
        """
        contact_doc = await self.collection.find_one({
            "id": contact_id,
            "organization_id": organization_id
        })

        if not contact_doc:
            return None

        # Remove MongoDB _id
        contact_doc.pop("_id", None)

        return Contact(**contact_doc)

    async def list_contacts(
        self,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> tuple[List[Contact], int]:
        """
        List contacts for an organization.

        Args:
            organization_id: Organization ID
            limit: Maximum number of contacts to return
            offset: Number of contacts to skip
            search: Optional search query (name, email, phone)

        Returns:
            Tuple of (contacts list, total count)
        """
        # Build query
        query = {"organization_id": organization_id}

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total = await self.collection.count_documents(query)

        # Get contacts with pagination
        cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
        contacts_docs = await cursor.to_list(length=limit)

        contacts = []
        for doc in contacts_docs:
            doc.pop("_id", None)
            contacts.append(Contact(**doc))

        return contacts, total

    async def update_contact(
        self,
        contact_id: str,
        updates: ContactUpdate,
        organization_id: str
    ) -> Optional[Contact]:
        """
        Update a contact.

        Args:
            contact_id: Contact ID
            updates: Update data
            organization_id: Organization ID for access control

        Returns:
            Updated contact if found, None otherwise
        """
        # Build update document
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()

        # Update in database
        result = await self.collection.update_one(
            {"id": contact_id, "organization_id": organization_id},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            return None

        # Return updated contact
        return await self.get_contact(contact_id, organization_id)

    async def delete_contact(
        self,
        contact_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete a contact.

        Args:
            contact_id: Contact ID
            organization_id: Organization ID for access control

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({
            "id": contact_id,
            "organization_id": organization_id
        })

        return result.deleted_count > 0

    async def apply_segment_filter(
        self,
        segment_filter: SegmentFilter,
        organization_id: str,
        campaign_type: Optional[CampaignType] = None,
        limit: Optional[int] = None
    ) -> List[Contact]:
        """
        Get contacts matching a segment filter.

        Args:
            segment_filter: Filter criteria
            organization_id: Organization ID
            campaign_type: Campaign type (for opt-out filtering)
            limit: Optional limit on results

        Returns:
            List of matching contacts
        """
        # Build MongoDB query
        query = {"organization_id": organization_id}

        # Property types filter
        if segment_filter.property_types:
            query["property_type_preferences"] = {"$in": segment_filter.property_types}

        # Locations filter
        if segment_filter.locations:
            query["location_preferences"] = {"$in": segment_filter.locations}

        # Budget filters
        if segment_filter.budget_min is not None:
            query["budget_max"] = {"$gte": segment_filter.budget_min}

        if segment_filter.budget_max is not None:
            query["budget_min"] = {"$lte": segment_filter.budget_max}

        # Bedrooms filters
        if segment_filter.bedrooms_min is not None:
            query["bedrooms_max"] = {"$gte": segment_filter.bedrooms_min}

        if segment_filter.bedrooms_max is not None:
            query["bedrooms_min"] = {"$lte": segment_filter.bedrooms_max}

        # Interest status filter
        if segment_filter.interest_statuses:
            query["interest_status"] = {"$in": [s.value for s in segment_filter.interest_statuses]}

        # Lead status filter
        if segment_filter.lead_statuses:
            query["lead_status"] = {"$in": [s.value for s in segment_filter.lead_statuses]}

        # Tags filter (all must match)
        if segment_filter.tags:
            query["tags"] = {"$all": segment_filter.tags}

        # Opt-out filter
        if segment_filter.exclude_opted_out and campaign_type:
            channel_name = campaign_type.value
            query["opt_out_channels"] = {"$nin": [channel_name]}

        # Execute query
        cursor = self.collection.find(query)
        if limit:
            cursor = cursor.limit(limit)

        contacts_docs = await cursor.to_list(length=limit or 1000)

        contacts = []
        for doc in contacts_docs:
            doc.pop("_id", None)
            contacts.append(Contact(**doc))

        logger.info(f"Segment filter matched {len(contacts)} contacts for organization {organization_id}")

        return contacts

    async def update_opt_out(
        self,
        contact_id: str,
        channel: str,
        opt_out: bool,
        organization_id: str
    ) -> Optional[Contact]:
        """
        Update contact's opt-out status for a channel.

        Args:
            contact_id: Contact ID
            channel: Channel name (sms, email, whatsapp, voice)
            opt_out: True to opt out, False to opt in
            organization_id: Organization ID for access control

        Returns:
            Updated contact if found, None otherwise
        """
        if opt_out:
            # Add to opt-out list
            await self.collection.update_one(
                {"id": contact_id, "organization_id": organization_id},
                {"$addToSet": {"opt_out_channels": channel}}
            )
        else:
            # Remove from opt-out list
            await self.collection.update_one(
                {"id": contact_id, "organization_id": organization_id},
                {"$pull": {"opt_out_channels": channel}}
            )

        return await self.get_contact(contact_id, organization_id)

    async def bulk_import_contacts(
        self,
        contacts_data: List[Dict[str, Any]],
        organization_id: str,
        user_id: str
    ) -> int:
        """
        Bulk import contacts from CSV or other source.

        Args:
            contacts_data: List of contact dictionaries
            organization_id: Organization ID
            user_id: User ID importing contacts

        Returns:
            Number of contacts imported
        """
        from bson import ObjectId

        # Prepare documents
        documents = []
        for contact_dict in contacts_data:
            doc = {
                "id": str(ObjectId()),
                "organization_id": organization_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_contacted": None,
                "opt_out_channels": [],
                "metadata": {},
                **contact_dict
            }
            documents.append(doc)

        # Bulk insert
        if documents:
            result = await self.collection.insert_many(documents)
            logger.info(f"Imported {len(result.inserted_ids)} contacts for organization {organization_id}")
            return len(result.inserted_ids)

        return 0

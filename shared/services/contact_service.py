"""
Centralized Contact Service

Unified service for managing contacts/leads across all applications.
Handles CRUD operations, contact import, segmentation, and analytics.

Used by: EstateFlow, ChurchFlow, StudyFlow, InkWave, EventFlow, etc.
"""

import logging
import csv
import io
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

import sys
sys.path.insert(0, '/opt/kasaai/apps')

from shared.models.contact import (
    Contact,
    ContactCreate,
    ContactUpdate,
    ContactFilters,
    ContactListResponse,
    ContactImportResult,
    ContactStats,
    ContactType,
    InterestLevel
)

logger = logging.getLogger(__name__)


class ContactService:
    """
    Service for managing contacts/leads.

    Provides complete contact management functionality:
    - CRUD operations
    - Import/export
    - Segmentation
    - Analytics
    """

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
        organization_id: str
    ) -> Contact:
        """
        Create a new contact.

        Args:
            contact_data: Contact creation data
            organization_id: Organization ID

        Returns:
            Created contact
        """
        contact_id = str(ObjectId())

        contact_dict = contact_data.dict()
        contact_dict.update({
            "id": contact_id,
            "organization_id": organization_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None,
            "is_deleted": False,
            "last_contacted": None,
            "last_email_opened": None,
            "last_email_clicked": None,
            "total_campaigns_sent": 0,
            "total_campaigns_opened": 0
        })

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
            organization_id: Organization ID

        Returns:
            Contact or None if not found
        """
        doc = await self.collection.find_one({
            "id": contact_id,
            "organization_id": organization_id,
            "is_deleted": False
        })

        if doc:
            return Contact(**doc)

        return None

    async def list_contacts(
        self,
        organization_id: str,
        filters: ContactFilters
    ) -> ContactListResponse:
        """
        List contacts with filtering and pagination.

        Args:
            organization_id: Organization ID
            filters: Contact filters

        Returns:
            Contact list response with pagination
        """
        query = {
            "organization_id": organization_id,
            "is_deleted": False
        }

        # Apply filters
        if filters.contact_type:
            query["contact_type"] = filters.contact_type.value

        if filters.interest_level:
            query["interest_level"] = filters.interest_level.value

        if filters.tags:
            query["tags"] = {"$in": filters.tags}

        if filters.segments:
            query["segments"] = {"$in": filters.segments}

        if filters.has_email is not None:
            if filters.has_email:
                query["email"] = {"$exists": True, "$ne": None, "$ne": ""}
            else:
                query["$or"] = [
                    {"email": {"$exists": False}},
                    {"email": None},
                    {"email": ""}
                ]

        if filters.has_phone is not None:
            if filters.has_phone:
                query["phone"] = {"$exists": True, "$ne": None, "$ne": ""}
            else:
                query["$or"] = [
                    {"phone": {"$exists": False}},
                    {"phone": None},
                    {"phone": ""}
                ]

        if filters.source:
            query["source"] = filters.source

        if filters.created_after:
            query.setdefault("created_at", {})["$gte"] = filters.created_after

        if filters.created_before:
            query.setdefault("created_at", {})["$lte"] = filters.created_before

        if filters.search:
            # Search in name, email, phone
            search_pattern = {"$regex": filters.search, "$options": "i"}
            query["$or"] = [
                {"first_name": search_pattern},
                {"last_name": search_pattern},
                {"email": search_pattern},
                {"phone": search_pattern}
            ]

        if filters.exclude_opted_out and filters.opted_out_channel:
            query["opt_out_channels"] = {"$ne": filters.opted_out_channel}

        # Count total
        total = await self.collection.count_documents(query)

        # Get paginated results
        cursor = self.collection.find(query)\
            .sort(filters.sort_by, -1 if filters.sort_order == "desc" else 1)\
            .skip(filters.offset)\
            .limit(filters.limit)

        contacts = []
        async for doc in cursor:
            contacts.append(Contact(**doc))

        has_more = (filters.offset + filters.limit) < total

        return ContactListResponse(
            contacts=contacts,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            has_more=has_more
        )

    async def update_contact(
        self,
        contact_id: str,
        organization_id: str,
        updates: ContactUpdate
    ) -> Optional[Contact]:
        """
        Update a contact.

        Args:
            contact_id: Contact ID
            organization_id: Organization ID
            updates: Fields to update

        Returns:
            Updated contact or None if not found
        """
        update_dict = updates.dict(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {
                "id": contact_id,
                "organization_id": organization_id,
                "is_deleted": False
            },
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            return await self.get_contact(contact_id, organization_id)

        return None

    async def delete_contact(
        self,
        contact_id: str,
        organization_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a contact.

        Args:
            contact_id: Contact ID
            organization_id: Organization ID
            soft_delete: If True, soft delete (default), otherwise hard delete

        Returns:
            True if deleted successfully
        """
        if soft_delete:
            result = await self.collection.update_one(
                {
                    "id": contact_id,
                    "organization_id": organization_id,
                    "is_deleted": False
                },
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        else:
            result = await self.collection.delete_one({
                "id": contact_id,
                "organization_id": organization_id
            })
            return result.deleted_count > 0

    async def import_contacts(
        self,
        organization_id: str,
        csv_content: str,
        update_existing: bool = False
    ) -> ContactImportResult:
        """
        Import contacts from CSV content.

        Args:
            organization_id: Organization ID
            csv_content: CSV file content as string
            update_existing: If True, update existing contacts by email

        Returns:
            Import result with statistics
        """
        result = ContactImportResult(
            total_rows=0,
            imported=0,
            updated=0,
            skipped=0,
            errors=[],
            imported_ids=[]
        )

        # Parse CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        for row_num, row in enumerate(reader, start=1):
            result.total_rows += 1

            try:
                # Validate required fields
                if not row.get("first_name") or not row.get("last_name"):
                    result.skipped += 1
                    result.errors.append({
                        "row": row_num,
                        "error": "Missing required fields: first_name, last_name"
                    })
                    continue

                email = row.get("email", "").strip() or None
                phone = row.get("phone", "").strip() or None

                if not email and not phone:
                    result.skipped += 1
                    result.errors.append({
                        "row": row_num,
                        "error": "At least one of email or phone is required"
                    })
                    continue

                # Check if contact exists (by email)
                existing = None
                if email and update_existing:
                    existing = await self.collection.find_one({
                        "organization_id": organization_id,
                        "email": email,
                        "is_deleted": False
                    })

                if existing and update_existing:
                    # Update existing contact
                    update_data = {
                        "first_name": row.get("first_name"),
                        "last_name": row.get("last_name"),
                        "phone": phone,
                        "updated_at": datetime.utcnow()
                    }

                    # Optional fields
                    if row.get("contact_type"):
                        update_data["contact_type"] = row.get("contact_type")
                    if row.get("tags"):
                        update_data["tags"] = row.get("tags").split(",")
                    if row.get("source"):
                        update_data["source"] = row.get("source")

                    await self.collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": update_data}
                    )

                    result.updated += 1

                elif existing:
                    # Skip if exists and not updating
                    result.skipped += 1
                    continue

                else:
                    # Create new contact
                    contact_data = ContactCreate(
                        first_name=row.get("first_name"),
                        last_name=row.get("last_name"),
                        email=email,
                        phone=phone,
                        contact_type=ContactType(row.get("contact_type", "lead")),
                        tags=row.get("tags", "").split(",") if row.get("tags") else [],
                        source=row.get("source") or "import"
                    )

                    contact = await self.create_contact(contact_data, organization_id)
                    result.imported += 1
                    result.imported_ids.append(contact.id)

            except Exception as e:
                logger.error(f"Error importing row {row_num}: {e}")
                result.errors.append({
                    "row": row_num,
                    "error": str(e)
                })
                result.skipped += 1

        logger.info(f"Import completed: {result.imported} imported, {result.updated} updated, {result.skipped} skipped")

        return result

    async def get_contact_stats(
        self,
        organization_id: str
    ) -> ContactStats:
        """
        Get contact database statistics.

        Args:
            organization_id: Organization ID

        Returns:
            Contact statistics
        """
        base_query = {
            "organization_id": organization_id,
            "is_deleted": False
        }

        # Get counts
        total_contacts = await self.collection.count_documents(base_query)

        # Count by type
        leads = await self.collection.count_documents({**base_query, "contact_type": ContactType.LEAD.value})
        customers = await self.collection.count_documents({**base_query, "contact_type": ContactType.CUSTOMER.value})
        prospects = await self.collection.count_documents({**base_query, "contact_type": ContactType.PROSPECT.value})

        # Count by interest level
        hot = await self.collection.count_documents({**base_query, "interest_level": InterestLevel.HOT.value})
        warm = await self.collection.count_documents({**base_query, "interest_level": InterestLevel.WARM.value})
        cold = await self.collection.count_documents({**base_query, "interest_level": InterestLevel.COLD.value})

        # Count by channel availability
        with_email = await self.collection.count_documents({
            **base_query,
            "email": {"$exists": True, "$ne": None, "$ne": ""}
        })

        with_phone = await self.collection.count_documents({
            **base_query,
            "phone": {"$exists": True, "$ne": None, "$ne": ""}
        })

        # Count opted-out
        opted_out_email = await self.collection.count_documents({
            **base_query,
            "opt_out_channels": "email"
        })

        opted_out_sms = await self.collection.count_documents({
            **base_query,
            "opt_out_channels": "sms"
        })

        # Count recent additions
        month_ago = datetime.utcnow() - timedelta(days=30)
        week_ago = datetime.utcnow() - timedelta(days=7)

        created_this_month = await self.collection.count_documents({
            **base_query,
            "created_at": {"$gte": month_ago}
        })

        created_this_week = await self.collection.count_documents({
            **base_query,
            "created_at": {"$gte": week_ago}
        })

        return ContactStats(
            total_contacts=total_contacts,
            leads=leads,
            customers=customers,
            prospects=prospects,
            hot=hot,
            warm=warm,
            cold=cold,
            with_email=with_email,
            with_phone=with_phone,
            opted_out_email=opted_out_email,
            opted_out_sms=opted_out_sms,
            created_this_month=created_this_month,
            created_this_week=created_this_week
        )


# Singleton instance
_contact_service_instance: Optional[ContactService] = None


def get_contact_service(db: AsyncIOMotorDatabase) -> ContactService:
    """
    Get the contact service instance.

    Args:
        db: MongoDB database instance

    Returns:
        ContactService: Contact service
    """
    global _contact_service_instance

    if _contact_service_instance is None:
        _contact_service_instance = ContactService(db)

    return _contact_service_instance

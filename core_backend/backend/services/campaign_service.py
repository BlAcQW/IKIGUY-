"""Data service for Campaign documents stored in MongoDB."""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from ..mongo import get_collection
from ..models import Campaign, CampaignCreate

logger = logging.getLogger(__name__)

_collection = get_collection("campaigns")


def _serialize(campaign: Campaign) -> dict:
    """Convert a campaign to a MongoDB document.

    Args:
        campaign (Campaign): Campaign instance to serialize.

    Returns:
        dict: Serialized MongoDB document.
    """

    doc = campaign.model_dump()
    doc["_id"] = str(doc.pop("id"))
    doc["tenant_id"] = str(doc["tenant_id"])
    if doc.get("assistant_id"):
        doc["assistant_id"] = str(doc["assistant_id"])
    if doc.get("audience_id"):
        doc["audience_id"] = str(doc["audience_id"])
    return doc


async def create_campaign(payload: CampaignCreate, organization_id: Optional[str] = None) -> Campaign:
    """Create a new campaign document.

    Args:
        payload (CampaignCreate): Campaign data.
        organization_id (Optional[str]): Organization ID for multi-tenant isolation.

    Returns:
        Campaign: Persisted campaign instance.
    """

    campaign = Campaign(**payload.model_dump())
    await _collection.insert_one(_serialize(campaign))

    logger.info(f"Created campaign {campaign.id} for organization={organization_id or campaign.tenant_id}")
    return campaign


async def get_campaign(campaign_id: UUID, organization_id: Optional[str] = None) -> Optional[Campaign]:
    """Retrieve a campaign by its ID.

    Args:
        campaign_id (UUID): Campaign identifier.
        organization_id (Optional[str]): Organization ID for validation (optional).

    Returns:
        Optional[Campaign]: Campaign if found, otherwise ``None``.
    """

    # Build query filter
    query_filter = {"_id": str(campaign_id)}
    if organization_id:
        query_filter["tenant_id"] = organization_id

    doc = await _collection.find_one(query_filter)
    if not doc:
        if organization_id:
            logger.warning(f"Campaign {campaign_id} not found for organization={organization_id}")
        return None

    doc["id"] = doc["_id"]
    logger.info(f"Retrieved campaign {campaign_id} for organization={organization_id or doc.get('tenant_id')}")
    return Campaign.model_validate(doc)


async def list_campaigns(tenant_id: UUID = None, organization_id: Optional[str] = None) -> List[Campaign]:
    """List campaigns for the given tenant/organization.

    Args:
        tenant_id (UUID): Tenant identifier (deprecated, use organization_id).
        organization_id (Optional[str]): Organization identifier for multi-tenant isolation.

    Returns:
        List[Campaign]: Campaigns belonging to the organization.
    """

    # Use organization_id if provided, fallback to tenant_id for backward compatibility
    filter_id = organization_id or (str(tenant_id) if tenant_id else None)

    if not filter_id:
        logger.warning("list_campaigns called without tenant_id or organization_id")
        return []

    results: List[Campaign] = []
    async for doc in _collection.find({"tenant_id": filter_id}):
        doc["id"] = doc["_id"]
        results.append(Campaign.model_validate(doc))

    logger.info(f"Listed {len(results)} campaigns for organization={filter_id}")
    return results


async def update_campaign(
    campaign_id: UUID,
    updates: dict,
    organization_id: Optional[str] = None
) -> Optional[Campaign]:
    """Update a campaign.

    Args:
        campaign_id (UUID): Campaign identifier.
        updates (dict): Fields to update.
        organization_id (Optional[str]): Organization ID for validation.

    Returns:
        Optional[Campaign]: Updated campaign if found, otherwise None.
    """

    # Build query filter
    query_filter = {"_id": str(campaign_id)}
    if organization_id:
        query_filter["tenant_id"] = organization_id

    result = await _collection.update_one(
        query_filter,
        {"$set": updates}
    )

    if result.matched_count == 0:
        if organization_id:
            logger.warning(f"Campaign {campaign_id} not found for update, organization={organization_id}")
        return None

    logger.info(f"Updated campaign {campaign_id} for organization={organization_id}")
    return await get_campaign(campaign_id, organization_id)


async def delete_campaign(campaign_id: UUID, organization_id: Optional[str] = None) -> bool:
    """Delete a campaign.

    Args:
        campaign_id (UUID): Campaign identifier.
        organization_id (Optional[str]): Organization ID for validation.

    Returns:
        bool: True if campaign was deleted, False if not found.
    """

    # Build query filter
    query_filter = {"_id": str(campaign_id)}
    if organization_id:
        query_filter["tenant_id"] = organization_id

    result = await _collection.delete_one(query_filter)

    success = result.deleted_count > 0
    if success:
        logger.info(f"Deleted campaign {campaign_id} for organization={organization_id}")
    else:
        logger.warning(f"Campaign {campaign_id} not found for deletion, organization={organization_id}")

    return success

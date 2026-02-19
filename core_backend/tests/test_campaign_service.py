"""Tests for MongoDB-based campaign service."""

from uuid import uuid4

import mongomock

from backend.models import CampaignCreate
from backend.services import campaign_service


def setup_module() -> None:
    """Use an in-memory MongoDB instance for tests."""
    campaign_service._collection = mongomock.MongoClient().db.campaigns


def test_create_and_get_campaign() -> None:
    """Campaign can be created and retrieved."""
    payload = CampaignCreate(
        tenant_id=uuid4(),
        name="Test",
        cron="* * * * *",
        pacing_per_minute=10,
    )
    created = campaign_service.create_campaign(payload)
    fetched = campaign_service.get_campaign(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_list_campaigns_empty() -> None:
    """Listing campaigns for a tenant with none returns empty list."""
    results = campaign_service.list_campaigns(uuid4())
    assert results == []


def test_get_campaign_missing() -> None:
    """Fetching a non-existent campaign returns None."""
    result = campaign_service.get_campaign(uuid4())
    assert result is None

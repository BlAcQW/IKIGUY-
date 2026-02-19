"""MongoDB service for managing service accounts."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from ..mongo import get_collection
from ..models import ServiceAccount

_collection = get_collection("service_accounts")


def _serialize(account: ServiceAccount) -> dict:
    """Convert a service account to a MongoDB document.

    Args:
        account (ServiceAccount): Account instance to serialize.

    Returns:
        dict: Serialized MongoDB document.
    """
    doc = account.model_dump()
    doc["_id"] = str(doc.pop("id"))
    return doc


def create_account(account: ServiceAccount) -> ServiceAccount:
    """Persist a new service account document.

    Args:
        account (ServiceAccount): Account to store.

    Returns:
        ServiceAccount: Stored account instance.
    """
    _collection.insert_one(_serialize(account))
    return account


def get_account(account_id: UUID) -> Optional[ServiceAccount]:
    """Retrieve a service account by its identifier."""
    doc = _collection.find_one({"_id": str(account_id)})
    if not doc:
        return None
    doc["id"] = doc["_id"]
    return ServiceAccount.model_validate(doc)


def get_by_token(token: str) -> Optional[ServiceAccount]:
    """Retrieve a service account by token."""
    doc = _collection.find_one({"token": token})
    if not doc:
        return None
    doc["id"] = doc["_id"]
    return ServiceAccount.model_validate(doc)

"""MongoDB service for persisting event records."""

from __future__ import annotations

from ..mongo import get_collection
from ..models import EventRecord

_collection = get_collection("events")


def _serialize(record: EventRecord) -> dict:
    """Convert an EventRecord to a MongoDB document."""
    doc = record.model_dump()
    doc["_id"] = str(doc.pop("id"))
    return doc


def create_record(record: EventRecord) -> EventRecord:
    """Persist a new event record."""
    _collection.insert_one(_serialize(record))
    return record

"""ETL worker to persist events from the in-memory bus."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .auth import get_current_account
from .events import event_bus
from .models import EventRecord
from .services import event_record_service

router = APIRouter()


def run_event_etl() -> int:
    """Persist events to the warehouse and clear the bus.

    Returns:
        int: Number of events persisted.
    """

    count = 0
    for ev in event_bus.list():
        record = EventRecord(
            type=ev.type.value, payload=ev.payload, timestamp=ev.timestamp
        )
        event_record_service.create_record(record)
        count += 1
    event_bus.clear()
    return count


@router.post("/internal/events/etl", dependencies=[Depends(get_current_account)])
def etl_events() -> dict[str, int]:
    """Flush events into the warehouse table."""
    count = run_event_etl()
    return {"persisted": count}

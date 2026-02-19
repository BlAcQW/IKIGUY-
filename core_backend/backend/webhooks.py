"""Webhook queue endpoints for Developer Platform."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .auth import get_current_account
from .events import webhook_queue

router = APIRouter()


@router.get("/internal/events/webhooks", dependencies=[Depends(get_current_account)])
def dequeue_webhook_events() -> list[dict[str, object]]:
    """Return and clear queued events for webhook delivery."""

    events = [
        {
            "type": ev.type.value,
            "payload": ev.payload,
            "timestamp": ev.timestamp.isoformat(),
        }
        for ev in webhook_queue.drain()
    ]
    return events

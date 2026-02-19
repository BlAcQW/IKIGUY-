"""Inbound PSTN call handling utilities.

This module provides helpers for bridging inbound telephony webhooks to the
voice engine's WebSocket interface. It logs consent information and initial
transcripts for Demo 19 (Inbound PSTN).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List

from .interfaces import TelephonyEvent, TelephonyEventType

# In-memory store for recorded inbound call events. In production this would be
# persisted to a database or analytics pipeline. # Reason: Simplifies demo use.
INBOUND_CALL_LOG: List[TelephonyEvent] = []


async def bridge_webhook_to_ws(
    webhook_payload: Dict[str, Any],
    ws_send: Callable[[Dict[str, Any]], Awaitable[None]],
) -> TelephonyEvent:
    """Bridge an inbound PSTN webhook to the voice engine WebSocket.

    Args:
        webhook_payload (Dict[str, Any]): Data from the telephony provider
            containing ``call_id``, caller number, initial transcript and
            consent flag.
        ws_send (Callable[[Dict[str, Any]], Awaitable[None]]): Coroutine used to
            forward messages to the voice engine over WebSocket.

    Returns:
        TelephonyEvent: Event capturing the inbound call and consent status.
    """

    call_id = webhook_payload.get("call_id", "")
    caller = webhook_payload.get("from", "")
    transcript = webhook_payload.get("transcript", "")
    consent = bool(webhook_payload.get("consent", False))

    # Forward the transcript to the voice engine over WebSocket.
    await ws_send({"call_id": call_id, "text": transcript})

    event = TelephonyEvent(
        event_type=TelephonyEventType.CALL_STARTED,
        call_id=call_id,
        timestamp=datetime.now(timezone.utc),
        provider=webhook_payload.get("provider", "pstn"),
        data={"caller": caller, "consent": consent, "transcript": transcript},
    )

    INBOUND_CALL_LOG.append(event)
    return event


__all__ = ["bridge_webhook_to_ws", "INBOUND_CALL_LOG"]

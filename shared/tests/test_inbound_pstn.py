"""Tests for inbound PSTN helpers."""

import asyncio
import pytest

from apps.shared.telephony.inbound import INBOUND_CALL_LOG, bridge_webhook_to_ws
from apps.shared.telephony.interfaces import TelephonyEventType


@pytest.mark.asyncio
async def test_bridge_webhook_to_ws_records_consent() -> None:
    """Inbound webhook is bridged and consent stored."""

    sent_messages = []

    async def dummy_ws_send(message):  # type: ignore[explicit-any]
        sent_messages.append(message)

    payload = {
        "call_id": "abc123",
        "from": "+15551234567",
        "transcript": "me din de Kofi",
        "consent": True,
    }

    event = await bridge_webhook_to_ws(payload, dummy_ws_send)

    assert sent_messages == [{"call_id": "abc123", "text": "me din de Kofi"}]
    assert event.event_type == TelephonyEventType.CALL_STARTED
    assert event.data["consent"] is True
    assert INBOUND_CALL_LOG[-1] == event


@pytest.mark.asyncio
async def test_bridge_webhook_to_ws_missing_fields() -> None:
    """Missing fields default correctly and event recorded."""

    async def noop_ws_send(message):  # type: ignore[explicit-any]
        pass

    payload = {"call_id": "xyz", "transcript": "", "from": "+1"}
    event = await bridge_webhook_to_ws(payload, noop_ws_send)

    assert event.data["transcript"] == ""
    assert event.data["consent"] is False


@pytest.mark.asyncio
async def test_bridge_webhook_ws_error_propagates() -> None:
    """Errors from WebSocket send surface to caller."""

    async def failing_ws_send(message):  # type: ignore[explicit-any]
        raise RuntimeError("ws failure")

    payload = {"call_id": "err", "from": "+1", "transcript": "hi"}
    with pytest.raises(RuntimeError):
        await bridge_webhook_to_ws(payload, failing_ws_send)

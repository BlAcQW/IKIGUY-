"""Simple in-memory event bus for Core backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class EventType(str, Enum):
    """Normalized event names used across the platform."""

    CALL_STARTED = "call.started"
    CALL_TURN = "call.turn"
    CALL_ENDED = "call.ended"
    OUTCOME_CONVERTED = "outcome.converted"
    QA_SCORE_CREATED = "qa.score.created"
    CRM_LEAD_CREATED = "crm.lead.created"
    CRM_CONTACT_UPDATED = "crm.contact.updated"
    HELPDESK_TICKET_CREATED = "helpdesk.ticket.created"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_WEBHOOK_RECEIVED = "payment.webhook.received"
    WALLET_CHARGED = "wallet.charged"
    LANGUAGE_DETECTED = "language.detected"

    # MCP Integration Events
    EMAIL_SENT = "email.sent"
    SMS_SENT = "sms.sent"
    CALENDAR_EVENT_CREATED = "calendar.event.created"
    DOCUMENT_UPLOADED = "document.uploaded"
    AI_CONTENT_GENERATED = "ai.content.generated"


@dataclass
class Event:
    """Structured event record."""

    type: EventType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Collects events for analytics and webhooks."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def emit(self, event_type: EventType, **payload: Any) -> Event:
        """Store a new event in the bus.

        Args:
            event_type (EventType): Name of the event.
            **payload (Any): Arbitrary payload data.

        Returns:
            Event: The recorded event.
        """

        event = Event(type=event_type, payload=payload)
        self.events.append(event)
        webhook_queue.push(event)
        return event

    def list(self) -> List[Event]:
        """Return all recorded events."""

        return list(self.events)

    def clear(self) -> None:
        """Remove all stored events."""

        self.events.clear()


# Webhook queue storing events for the Developer Platform
class WebhookQueue:
    """Simple in-memory queue for webhook delivery."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def push(self, event: Event) -> None:
        """Append an event to the queue."""

        self.events.append(event)

    def drain(self) -> List[Event]:
        """Return and clear all queued events."""

        items = list(self.events)
        self.events.clear()
        return items


# Global webhook queue consumed by the Developer Platform
webhook_queue = WebhookQueue()

# Global event bus instance used by the app
# Reason: Tests and modules share a single bus for simplicity
# and can reset it between runs.
event_bus = EventBus()

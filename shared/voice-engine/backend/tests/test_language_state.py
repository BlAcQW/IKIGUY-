from importlib import util
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.shared.events.interfaces import Event, EventBus

# Dynamically load the module because the directory name contains a hyphen.
module_path = Path(__file__).resolve().parent.parent / "language_state.py"
spec = util.spec_from_file_location("language_state", module_path)
language_state = util.module_from_spec(spec)
spec.loader.exec_module(language_state)  # type: ignore[arg-type]

LanguageState = language_state.LanguageState
HYSTERESIS_MARGIN = language_state.HYSTERESIS_MARGIN


class DummyEventBus(EventBus):
    """Event bus that records published events for inspection."""

    def __init__(self) -> None:  # type: ignore[override]
        super().__init__(backend=None)
        self.events: List[Event] = []

    async def publish(self, event: Event) -> bool:  # type: ignore[override]
        self.events.append(event)
        return True

    # The remaining abstract methods are unused in tests.
    async def subscribe(self, event_type: str, handler: Any) -> str:  # type: ignore[override]
        return ""

    async def unsubscribe(self, subscription_id: str) -> bool:  # type: ignore[override]
        return True

    async def get_events(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> List[Event]:  # type: ignore[override]
        return []

    async def get_event_by_id(self, event_id: str) -> Optional[Event]:  # type: ignore[override]
        return None

    async def get_events_by_type(
        self, event_type: str, limit: int = 100
    ) -> List[Event]:  # type: ignore[override]
        return []

    async def get_events_by_tenant(
        self, tenant_id: str, limit: int = 100
    ) -> List[Event]:  # type: ignore[override]
        return []


def test_language_switch_emits_event():
    state = LanguageState()
    bus = DummyEventBus()
    assert state.update("en", 0.6, bus)
    assert state.language == "en"
    assert bus.events and bus.events[0].data["new_language"] == "en"


def test_same_language_updates_confidence_without_event():
    state = LanguageState(language="en", confidence=0.5)
    bus = DummyEventBus()
    assert not state.update("en", 0.7, bus)
    assert state.confidence == 0.7
    assert not bus.events


def test_low_confidence_no_switch():
    state = LanguageState(language="en", confidence=0.7)
    bus = DummyEventBus()
    low_conf = state.confidence + HYSTERESIS_MARGIN - 0.01
    assert not state.update("fr", low_conf, bus)
    assert state.language == "en"
    assert not bus.events

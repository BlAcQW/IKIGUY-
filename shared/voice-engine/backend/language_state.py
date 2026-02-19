from __future__ import annotations

"""Language tracking for the voice engine backend.

This module keeps track of the current detected language and the
confidence level of that detection. It exposes :func:`update_language`
which applies a simple hysteresis rule before switching languages and
emits a ``language_changed`` event whenever a switch occurs.
"""

from typing import Optional
import asyncio
from uuid import uuid4

from pydantic import BaseModel

from apps.shared.events import Event, EventBus

# Minimum confidence delta required to switch languages
HYSTERESIS_MARGIN = 0.2


class LanguageState(BaseModel):
    """Track the currently detected language and its confidence."""

    language: Optional[str] = None
    confidence: float = 0.0

    async def _emit_language_changed(
        self, bus: EventBus, old: Optional[str], new: str, confidence: float
    ) -> None:
        """Emit a ``language_changed`` event via the provided event bus."""
        event = Event(
            event_id=str(uuid4()),
            event_type="language_changed",
            source="voice-engine",
            data={"old_language": old, "new_language": new, "confidence": confidence},
        )
        await bus.publish(event)

    def update(
        self, new_lang: str, new_conf: float, event_bus: Optional[EventBus] = None
    ) -> bool:
        """Update the tracked language using hysteresis.

        The language is switched only if ``new_lang`` differs from the current
        language *and* its confidence exceeds the current confidence by at
        least :data:`HYSTERESIS_MARGIN`.

        Args:
            new_lang: Newly detected language code.
            new_conf: Confidence score for ``new_lang``.
            event_bus: Optional event bus for emitting ``language_changed`` events.

        Returns:
            bool: ``True`` if the language changed, ``False`` otherwise.
        """
        changed = False
        if self.language is None:
            changed = True
        elif (
            new_lang != self.language
            and new_conf >= self.confidence + HYSTERESIS_MARGIN
        ):
            changed = True
        else:
            if new_lang == self.language and new_conf > self.confidence:
                self.confidence = new_conf
            return False

        old_language = self.language
        self.language = new_lang
        self.confidence = new_conf

        if event_bus is not None:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(
                    self._emit_language_changed(
                        event_bus, old_language, new_lang, new_conf
                    )
                )
            except RuntimeError:
                # Reason: ``update`` may be called from synchronous code without a running
                # event loop, so we fall back to ``asyncio.run`` to ensure the event is sent.
                asyncio.run(
                    self._emit_language_changed(
                        event_bus, old_language, new_lang, new_conf
                    )
                )

        return True


_GLOBAL_STATE = LanguageState()


def update_language(
    new_lang: str, new_conf: float, event_bus: Optional[EventBus] = None
) -> bool:
    """Update the global language state.

    This helper is a thin wrapper around :class:`LanguageState` for modules that
    do not need to manage instances directly.

    Args:
        new_lang: Newly detected language code.
        new_conf: Confidence score for ``new_lang``.
        event_bus: Optional event bus for emitting ``language_changed`` events.

    Returns:
        bool: ``True`` if the language changed, ``False`` otherwise.
    """

    return _GLOBAL_STATE.update(new_lang, new_conf, event_bus)

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple
from uuid import UUID

from .events import EventType, event_bus


@dataclass
class SessionLog:
    """Conversation log for a session."""

    messages: List[Tuple[str, str]] = field(default_factory=list)
    handover_target: str | None = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None


class SessionManager:
    """In-memory store for session transcripts."""

    def __init__(self, bus=event_bus) -> None:
        self.sessions: Dict[UUID, SessionLog] = {}
        self.events = bus

    def start_session(self, session_id: UUID) -> None:
        """Ensure a session entry exists."""

        if session_id not in self.sessions:
            self.sessions[session_id] = SessionLog()
            if self.events:
                self.events.emit(EventType.CALL_STARTED, session_id=str(session_id))

    def add_turn(self, session_id: UUID, role: str, text: str) -> None:
        """Append a turn to a session."""

        self.start_session(session_id)
        self.sessions[session_id].messages.append((role, text))
        if self.events:
            self.events.emit(EventType.CALL_TURN, session_id=str(session_id), role=role)

    def get_log(self, session_id: UUID) -> List[Tuple[str, str]]:
        """Return the transcript for a session."""

        return self.sessions.get(session_id, SessionLog()).messages

    def handover(self, session_id: UUID, target: str) -> None:
        """Mark the session for human handover.

        Args:
            session_id (UUID): Session identifier.
            target (str): SIP address or destination for transfer.
        """

        self.start_session(session_id)
        self.sessions[session_id].handover_target = target

    def status(self, session_id: UUID) -> SessionLog:
        """Return the stored session state."""

        self.start_session(session_id)
        return self.sessions[session_id]

    def end_session(self, session_id: UUID) -> None:
        """Mark the session as ended and stamp the end time."""

        self.start_session(session_id)
        self.sessions[session_id].end_time = datetime.utcnow()
        if self.events:
            self.events.emit(EventType.CALL_ENDED, session_id=str(session_id))

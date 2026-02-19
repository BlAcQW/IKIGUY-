"""Service for persisting voice session turns."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from ..mongo import get_collection
from ..models import VoiceSession, VoiceTurn

_collection = get_collection("voice_sessions")


def _serialize_session(session: VoiceSession) -> dict:
    """Convert a VoiceSession into a MongoDB document."""

    doc = session.model_dump()
    doc["_id"] = str(doc.pop("id"))
    doc["turns"] = [t.model_dump() for t in session.turns]
    return doc


def _deserialize_session(doc: dict) -> VoiceSession:
    """Convert a MongoDB document into a VoiceSession."""

    data = doc.copy()
    data["id"] = str(data.pop("_id"))
    data["turns"] = [VoiceTurn(**t) for t in data.get("turns", [])]
    return VoiceSession(**data)


def create_session(session: VoiceSession) -> VoiceSession:
    """Persist a new voice session."""

    _collection.insert_one(_serialize_session(session))
    return session


def append_turn(session_id: UUID, turn: VoiceTurn) -> VoiceTurn:
    """Append a turn to the voice session identified by ``session_id``."""

    doc = _collection.find_one({"_id": str(session_id)})
    if not doc:
        # Create a new session with the correct structure
        session = VoiceSession(
            id=str(session_id),
            user_id="test_user",  # Default for testing
            assistant_id="test_assistant",  # Default for testing
            session_type="conversation",
            status="active",
            start_time=datetime.utcnow(),
            language="",
            country="",
            metadata={},
            turns=[turn]
        )
        doc = _serialize_session(session)
        _collection.insert_one(doc)
    else:
        # Add the new turn to existing document
        doc.setdefault("turns", []).append(turn.model_dump())
        _collection.replace_one({"_id": str(session_id)}, doc, upsert=True)
    
    return turn


def get_session(session_id: UUID) -> Optional[VoiceSession]:
    """Retrieve a voice session by ``session_id``."""

    doc = _collection.find_one({"_id": str(session_id)})
    if not doc:
        return None
    return _deserialize_session(doc)

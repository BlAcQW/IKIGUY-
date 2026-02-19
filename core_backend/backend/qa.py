"""QA scoring endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .auth import get_current_account
from .events import event_bus, EventType


class QaScore(BaseModel):
    """QA score for a session."""

    session_id: UUID = Field(..., description="Session identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score")


router = APIRouter(prefix="/internal/qa", dependencies=[Depends(get_current_account)])


@router.post("/score")
async def create_score(payload: QaScore) -> dict[str, str]:
    """Emit a QA score created event."""

    event_bus.emit(
        EventType.QA_SCORE_CREATED,
        session_id=str(payload.session_id),
        score=payload.score,
    )
    return {"status": "ok"}

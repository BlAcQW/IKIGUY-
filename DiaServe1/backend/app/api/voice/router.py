"""
Voice Agent API router for EstateFlow.

Provides endpoints for voice call management, configuration, and statistics.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.voice import (
    VoiceCall,
    VoiceConfig,
    VoiceConfigUpdate,
    CallStats,
    CallListResponse,
)
from app.services.voice_service import VoiceService
from app.core.auth import get_current_user, get_organization_context
from app.core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


def get_voice_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> VoiceService:
    return VoiceService(db)


@router.get("/calls", response_model=CallListResponse, summary="List voice calls")
async def list_calls(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    call_status: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
    service: VoiceService = Depends(get_voice_service),
):
    """List voice calls for the organization."""
    organization_id = org_context["organization_id"]
    calls, total = await service.list_calls(
        organization_id=organization_id,
        limit=limit,
        offset=offset,
        status=call_status,
    )
    return CallListResponse(calls=calls, total=total, limit=limit, offset=offset)


@router.get("/calls/{call_id}", response_model=VoiceCall, summary="Get call details")
async def get_call(
    call_id: str,
    current_user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
    service: VoiceService = Depends(get_voice_service),
):
    """Get a specific voice call by ID."""
    organization_id = org_context["organization_id"]
    call = await service.get_call(call_id, organization_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/stats", response_model=CallStats, summary="Get call statistics")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
    service: VoiceService = Depends(get_voice_service),
):
    """Get voice call statistics for the organization."""
    organization_id = org_context["organization_id"]
    return await service.get_stats(organization_id)


@router.get("/config", response_model=VoiceConfig, summary="Get voice config")
async def get_config(
    current_user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
    service: VoiceService = Depends(get_voice_service),
):
    """Get voice agent configuration."""
    organization_id = org_context["organization_id"]
    return await service.get_config(organization_id)


@router.put("/config", response_model=VoiceConfig, summary="Update voice config")
async def update_config(
    updates: VoiceConfigUpdate,
    current_user: dict = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context),
    service: VoiceService = Depends(get_voice_service),
):
    """Update voice agent configuration."""
    organization_id = org_context["organization_id"]
    return await service.update_config(organization_id, updates)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Vapi webhook receiver",
)
async def vapi_webhook(
    payload: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Receive webhook events from Vapi for call status updates.

    This endpoint is called by Vapi when call events occur (started, ended, etc.).
    """
    service = VoiceService(db)
    event_type = payload.get("type", "")
    call_data = payload.get("call", {})

    logger.info(f"Vapi webhook: {event_type}")

    if event_type in ("call.ended", "call-ended"):
        org_id = call_data.get("metadata", {}).get("organization_id", "")
        if org_id:
            await service.create_call(
                {
                    "caller_name": call_data.get("customer", {}).get(
                        "name", "Unknown"
                    ),
                    "caller_phone": call_data.get("customer", {}).get(
                        "number", ""
                    ),
                    "direction": "inbound",
                    "status": "completed",
                    "outcome": "information_provided",
                    "duration_seconds": call_data.get("duration", 0),
                    "metadata": call_data.get("metadata", {}),
                },
                organization_id=org_id,
            )

    return {"status": "ok"}

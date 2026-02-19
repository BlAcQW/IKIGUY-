#!/usr/bin/env python3
"""
Dynamic WebRTC Voice Chat Router
Supports per-assistant WebRTC connections with first message streaming.

This replaces the static FastRTC setup with dynamic assistant-based routing.
"""

import logging
import asyncio
import json
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime

from apps.shared.integration.webrtc import WebRTCVoiceAgent, create_webrtc_stream
from apps.core_backend.backend.services.assistant_service import assistant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice/webrtc", tags=["webrtc"])

# Store active WebRTC sessions
active_sessions: Dict[str, Dict] = {}


class WebRTCOfferRequest(BaseModel):
    """WebRTC offer from client"""
    sdp: str
    type: str
    assistant_id: str


class WebRTCAnswerResponse(BaseModel):
    """WebRTC answer to client"""
    sdp: str
    type: str


@router.post("/offer", response_model=WebRTCAnswerResponse)
async def handle_webrtc_offer(offer: WebRTCOfferRequest):
    """
    Handle WebRTC offer with dynamic assistant support.

    This endpoint:
    1. Validates the assistant exists and is accessible
    2. Creates a WebRTC agent for that specific assistant
    3. Processes the SDP offer
    4. Returns an SDP answer for connection establishment

    Args:
        offer: WebRTC offer containing SDP, type, and assistant_id

    Returns:
        WebRTC answer with SDP and type

    Raises:
        HTTPException: If assistant not found or WebRTC setup fails
    """
    try:
        logger.info(f"📞 WebRTC offer received for assistant: {offer.assistant_id}")

        # Validate assistant exists
        assistant = assistant_service.get_assistant(offer.assistant_id)
        if not assistant:
            logger.error(f"❌ Assistant not found: {offer.assistant_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Assistant {offer.assistant_id} not found"
            )

        logger.info(f"✅ Found assistant: {assistant.name}")

        # Create WebRTC agent for this assistant
        agent = WebRTCVoiceAgent(
            assistant_id=offer.assistant_id,
            pause_threshold_ms=1500,
            sample_rate=16000
        )

        # Create FastRTC stream with startup_fn for first message
        stream = create_webrtc_stream(
            assistant_id=offer.assistant_id,
            pause_threshold_ms=1500,
            sample_rate=16000,
            ui_title=f"{assistant.name} - Voice Chat",
            ui_subtitle="Speak naturally - I'll respond when you pause"
        )

        if not stream:
            logger.error("❌ Failed to create WebRTC stream")
            raise HTTPException(
                status_code=500,
                detail="Failed to create WebRTC stream"
            )

        # Process the offer using FastRTC's handler
        # FastRTC expects offer in specific format
        logger.info("📝 Processing WebRTC offer...")

        # Create session ID
        session_id = f"{offer.assistant_id}_{datetime.now().timestamp()}"

        # Store session info
        active_sessions[session_id] = {
            "assistant_id": offer.assistant_id,
            "assistant_name": assistant.name,
            "agent": agent,
            "stream": stream,
            "created_at": datetime.now()
        }

        logger.info(f"✅ Session created: {session_id}")
        logger.info(f"📊 Active sessions: {len(active_sessions)}")

        # For now, return a placeholder answer
        # TODO: Implement proper SDP answer generation using FastRTC
        # This requires deeper FastRTC integration

        logger.warning("⚠️ WebRTC SDP answer generation not yet implemented")
        logger.warning("⚠️ This endpoint is a work in progress")

        raise HTTPException(
            status_code=501,
            detail="WebRTC dynamic routing is under construction. Please use WebSocket mode."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error handling WebRTC offer: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process WebRTC offer: {str(e)}"
        )


@router.get("/sessions")
async def get_active_sessions():
    """
    Get list of active WebRTC sessions (for debugging).

    Returns:
        Dictionary of active sessions with metadata
    """
    return {
        "count": len(active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "assistant_id": info["assistant_id"],
                "assistant_name": info["assistant_name"],
                "created_at": info["created_at"].isoformat()
            }
            for sid, info in active_sessions.items()
        ]
    }


@router.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """
    Close a WebRTC session and cleanup resources.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    if session_id in active_sessions:
        session = active_sessions.pop(session_id)
        logger.info(f"🔌 Closed session: {session_id} (assistant: {session['assistant_name']})")
        return {"message": "Session closed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# Export router
__all__ = ['router']

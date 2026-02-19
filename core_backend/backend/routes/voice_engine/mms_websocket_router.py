"""WebSocket router for Meta MMS continuous conversation"""

from fastapi import APIRouter, WebSocket, Query
from .mms_websocket import websocket_conversation

router = APIRouter(prefix="/mms", tags=["mms-websocket"])

@router.websocket("/conversation")
async def voice_conversation_endpoint(websocket: WebSocket, lang_code: str = Query(default="eng")):
    """WebSocket endpoint for continuous voice conversation"""
    await websocket_conversation(websocket, lang_code)
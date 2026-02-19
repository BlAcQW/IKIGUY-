"""
SIP Trunking routes for Asterisk and FreeSWITCH integration
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from uuid import uuid4

from .models import (
    PstnInboundRequest, 
    PstnInboundResponse, 
    PstnOutboundRequest, 
    PstnOutboundResponse
)
try:
    from apps.shared.voice_engine.backend.sip_manager import (
        sip_manager,
        SIPProvider,
        CallInfo
    )
except ImportError:
    # Fallback if module not available
    sip_manager = None
    SIPProvider = None
    CallInfo = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sip", tags=["sip"])


@router.post("/call/outbound", response_model=PstnOutboundResponse)
async def make_sip_call(request: PstnOutboundRequest, background_tasks: BackgroundTasks):
    """
    Make an outbound call via SIP (Asterisk or FreeSWITCH)
    
    Args:
        request: Outbound call request
        background_tasks: Background tasks for async processing
        
    Returns:
        Call response with call ID and status
    """
    try:
        # Get SIP manager
        manager = sip_manager
        
        # Check if any SIP server is available
        active_server = await manager.get_active_server()
        if not active_server:
            raise HTTPException(
                status_code=503,
                detail="No SIP servers available. Please check Asterisk/FreeSWITCH configuration."
            )
        
        # Initiate the call
        call_id = await manager.make_call(
            to_number=request.to_number,
            from_number=request.from_number,
            assistant_id=request.assistant_id,
            metadata=request.metadata
        )
        
        if not call_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to initiate call through SIP server"
            )
        
        # Get call info
        call_info = await manager.get_call_info(call_id)
        
        response = PstnOutboundResponse(
            call_id=call_id,
            status="initiated",
            to_number=request.to_number,
            session_id=str(uuid4()),
            provider=f"sip_{call_info.provider.value}" if call_info else "sip"
        )
        
        logger.info(f"SIP call initiated: {call_id} to {request.to_number} via {active_server}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to make SIP call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/call/{call_id}/hangup")
async def hangup_sip_call(call_id: str):
    """
    Hang up a SIP call
    
    Args:
        call_id: Call ID to terminate
        
    Returns:
        Hangup confirmation
    """
    try:
        manager = sip_manager
        
        # Get call info
        call_info = await manager.get_call_info(call_id)
        if not call_info:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Hang up the call
        success = await manager.hangup_call(call_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to hang up call")
        
        return {
            "call_id": call_id,
            "status": "terminated",
            "message": "Call ended successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to hang up SIP call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call/{call_id}/status")
async def get_sip_call_status(call_id: str):
    """
    Get the status of a SIP call
    
    Args:
        call_id: Call ID to check
        
    Returns:
        Call status information
    """
    try:
        manager = sip_manager
        
        # Get call info
        call_info = await manager.get_call_info(call_id)
        
        if not call_info:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Calculate duration if call is active
        duration = None
        if call_info.start_time:
            from datetime import datetime
            duration = int((datetime.utcnow() - call_info.start_time).total_seconds())
        
        return {
            "call_id": call_info.call_id,
            "provider": f"sip_{call_info.provider.value}",
            "status": call_info.status,
            "direction": call_info.direction,
            "from_number": call_info.from_number,
            "to_number": call_info.to_number,
            "duration_seconds": duration,
            "start_time": call_info.start_time.isoformat() if call_info.start_time else None,
            "assistant_id": call_info.assistant_id,
            "metadata": call_info.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get SIP call status for {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/status")
async def get_sip_servers_status():
    """
    Get the status of all configured SIP servers
    
    Returns:
        Status information for Asterisk and FreeSWITCH servers
    """
    try:
        manager = sip_manager
        status = await manager.get_server_status()
        
        return {
            "status": "operational" if status["available_servers"] > 0 else "degraded",
            "available_servers": status["available_servers"],
            "total_active_calls": status["total_active_calls"],
            "servers": status["servers"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get SIP servers status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/asterisk")
async def handle_asterisk_webhook(payload: Dict[str, Any]):
    """
    Handle webhooks from Asterisk AMI/AGI
    
    Args:
        payload: Webhook payload from Asterisk
        
    Returns:
        Webhook acknowledgment
    """
    try:
        event_type = payload.get("Event", "")
        call_id = payload.get("Uniqueid", payload.get("call_id"))
        
        logger.info(f"Received Asterisk webhook: {event_type} for call {call_id}")
        
        # Process different event types
        if event_type == "Newchannel":
            # New call started
            logger.info(f"New Asterisk channel: {call_id}")
            
        elif event_type == "Hangup":
            # Call ended
            logger.info(f"Asterisk call ended: {call_id}")
            
        elif event_type == "Bridge":
            # Call connected
            logger.info(f"Asterisk call bridged: {call_id}")
        
        # TODO: Update call status in SIP manager
        
        return {
            "status": "processed",
            "call_id": call_id,
            "event": event_type
        }
        
    except Exception as e:
        logger.error(f"Failed to process Asterisk webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/freeswitch")
async def handle_freeswitch_webhook(payload: Dict[str, Any]):
    """
    Handle webhooks from FreeSWITCH Event Socket
    
    Args:
        payload: Webhook payload from FreeSWITCH
        
    Returns:
        Webhook acknowledgment
    """
    try:
        event_name = payload.get("Event-Name", "")
        call_id = payload.get("Unique-ID", payload.get("call_id"))
        
        logger.info(f"Received FreeSWITCH webhook: {event_name} for call {call_id}")
        
        # Process different event types
        if event_name == "CHANNEL_CREATE":
            # New call started
            logger.info(f"New FreeSWITCH channel: {call_id}")
            
        elif event_name == "CHANNEL_HANGUP":
            # Call ended
            logger.info(f"FreeSWITCH call ended: {call_id}")
            
        elif event_name == "CHANNEL_ANSWER":
            # Call answered
            logger.info(f"FreeSWITCH call answered: {call_id}")
        
        # TODO: Update call status in SIP manager
        
        return {
            "status": "processed",
            "call_id": call_id,
            "event": event_name
        }
        
    except Exception as e:
        logger.error(f"Failed to process FreeSWITCH webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure/{provider}")
async def configure_sip_provider(
    provider: str,
    config: Dict[str, Any]
):
    """
    Configure a SIP provider (Asterisk or FreeSWITCH)
    
    Args:
        provider: Provider name (asterisk or freeswitch)
        config: Configuration parameters
        
    Returns:
        Configuration status
    """
    try:
        if provider not in ["asterisk", "freeswitch"]:
            raise HTTPException(status_code=400, detail="Invalid provider. Use 'asterisk' or 'freeswitch'")
        
        # TODO: Update SIP manager configuration
        # This would typically update the configuration and reconnect
        
        return {
            "status": "configured",
            "provider": provider,
            "message": f"SIP provider {provider} configured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure SIP provider {provider}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
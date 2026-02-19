"""
Premier Health VAPI Transfer Event Handling

This module handles VAPI server messages including:
- Transfer events (transfer-update, transfer-destination-request)
- Transcripts
- End-of-call reports
- Webhook secret validation
"""

import os
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
import logging

from ..mongo import get_collection

logger = logging.getLogger(__name__)

router = APIRouter()

# Load webhook secrets from environment
WEBHOOK_SECRETS = {
    "router": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_ROUTER"),
    "greater_accra": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_GREATER_ACCRA"),
    "ashanti": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_ASHANTI"),
    "northern_regions": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_NORTHERN_REGIONS"),
    "western_and_central": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_WESTERN_AND_CENTRAL"),
    "eastern_and_volta": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_EASTERN_AND_VOLTA"),
    "bono_regions": os.getenv("PREMIER_HEALTH_WEBHOOK_SECRET_BONO_REGIONS"),
}


class VAPIServerMessageRequest(BaseModel):
    """Request model for VAPI server messages."""
    message: Dict[str, Any]
    call: Optional[Dict[str, Any]] = None
    assistant: Optional[Dict[str, Any]] = None


def validate_webhook_secret(payload: bytes, signature: Optional[str], assistant_name: Optional[str]) -> bool:
    """
    Validate VAPI webhook signature.

    Args:
        payload: Raw request payload
        signature: Signature from X-Vapi-Secret header
        assistant_name: Name of assistant to identify correct secret

    Returns:
        bool: True if signature is valid
    """
    if not signature:
        logger.warning("No webhook signature provided")
        return False

    # Try to identify which assistant this is from
    secret = None
    if assistant_name:
        for key, assistant_secret in WEBHOOK_SECRETS.items():
            if key.replace("_", " ").lower() in assistant_name.lower():
                secret = assistant_secret
                break

    # If we couldn't identify the assistant, try all secrets
    if not secret:
        for assistant_secret in WEBHOOK_SECRETS.values():
            if assistant_secret:
                computed = hmac.new(
                    assistant_secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                if hmac.compare_digest(computed, signature):
                    return True
        return False

    # Validate signature
    computed = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


async def log_transfer_event(
    call_id: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> None:
    """
    Log transfer event to MongoDB.

    Args:
        call_id: VAPI call ID
        event_type: Type of transfer event
        event_data: Event data dictionary
    """
    try:
        transfers_collection = get_collection("premier_health_transfers")

        transfer_log = {
            "call_id": call_id,
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }

        await transfers_collection.insert_one(transfer_log)
        logger.info(f"✅ Transfer event logged: {event_type} for call {call_id}")

    except Exception as e:
        logger.error(f"Failed to log transfer event: {e}")


async def handle_transfer_update(call_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle transfer-update event.

    Args:
        call_id: VAPI call ID
        message: Message data

    Returns:
        dict: Response to VAPI
    """
    transfer_data = {
        "status": message.get("status"),
        "destination": message.get("destination"),
        "timestamp": message.get("timestamp"),
    }

    logger.info(f"🔄 Transfer update for call {call_id}: {transfer_data['status']}")

    # Log to MongoDB
    await log_transfer_event(call_id, "transfer_update", transfer_data)

    return {"success": True}


async def handle_transfer_destination_request(
    call_id: str,
    message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle transfer-destination-request event.

    This allows dynamic transfer destination selection if needed.

    Args:
        call_id: VAPI call ID
        message: Message data

    Returns:
        dict: Transfer destination or empty dict to use default
    """
    logger.info(f"📍 Transfer destination request for call {call_id}")

    # Log the request
    await log_transfer_event(
        call_id,
        "transfer_destination_request",
        {"message": message}
    )

    # For now, use default destinations from assistant configuration
    # Could add custom logic here to dynamically select destination
    return {}


async def handle_transcript(call_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle transcript event.

    Args:
        call_id: VAPI call ID
        message: Message data

    Returns:
        dict: Response to VAPI
    """
    transcript_data = {
        "role": message.get("role"),
        "content": message.get("content"),
        "timestamp": message.get("timestamp"),
    }

    logger.debug(f"📝 Transcript for call {call_id}: {transcript_data['role']}")

    # Could log transcripts to MongoDB if needed
    # For now, just acknowledge
    return {"success": True}


async def handle_end_of_call_report(call_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle end-of-call-report event.

    Args:
        call_id: VAPI call ID
        message: Message data

    Returns:
        dict: Response to VAPI
    """
    report_data = {
        "duration": message.get("duration"),
        "cost": message.get("cost"),
        "ended_reason": message.get("endedReason"),
        "summary": message.get("summary"),
    }

    logger.info(f"📊 End of call report for {call_id}: duration={report_data['duration']}s")

    # Log to MongoDB
    await log_transfer_event(call_id, "end_of_call_report", report_data)

    return {"success": True}


@router.post("/vapi-server-messages")
async def handle_vapi_server_messages(
    request: Request,
    background_tasks: BackgroundTasks,
    x_vapi_secret: Optional[str] = Header(None)
):
    """
    Handle VAPI server messages including transfer events.

    This endpoint receives:
    - transfer-update: Transfer status updates
    - transfer-destination-request: Dynamic transfer routing
    - transcript: Call transcripts
    - end-of-call-report: Call completion reports
    - status-update: General status updates

    Webhook signature validation is performed using HMAC SHA256.
    """
    try:
        # Get raw payload for signature verification
        payload = await request.body()

        # Parse JSON
        data = await request.json()

        # Extract message type and call info
        message = data.get("message", {})
        message_type = message.get("type")
        call = data.get("call", {})
        call_id = call.get("id", "unknown")
        assistant = data.get("assistant", {})
        assistant_name = assistant.get("name")

        logger.info(f"📨 Received VAPI server message: type={message_type}, call={call_id}")

        # Validate webhook secret
        # Note: Skip validation in development if no secret is configured
        if any(WEBHOOK_SECRETS.values()):
            if not validate_webhook_secret(payload, x_vapi_secret, assistant_name):
                logger.warning(f"❌ Invalid webhook signature for call {call_id}")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            logger.debug("✅ Webhook signature validated")

        # Route message to appropriate handler
        if message_type == "transfer-update":
            return await handle_transfer_update(call_id, message)

        elif message_type == "transfer-destination-request":
            return await handle_transfer_destination_request(call_id, message)

        elif message_type == "transcript":
            return await handle_transcript(call_id, message)

        elif message_type == "end-of-call-report":
            return await handle_end_of_call_report(call_id, message)

        elif message_type == "status-update":
            logger.info(f"📡 Status update for call {call_id}: {message.get('status')}")
            return {"success": True}

        else:
            logger.warning(f"⚠️  Unknown message type: {message_type}")
            return {"success": True}  # Acknowledge unknown messages

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling VAPI server message: {str(e)}")
        # Return 200 to prevent VAPI from retrying
        return {"success": False, "error": str(e)}


@router.get("/transfer-statistics")
async def get_transfer_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    Get transfer statistics for monitoring.

    Query Parameters:
        start_date: ISO format date string
        end_date: ISO format date string

    Returns:
        dict: Transfer statistics
    """
    try:
        transfers_collection = get_collection("premier_health_transfers")

        # Build query
        query = {}
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                query["timestamp"]["$lte"] = datetime.fromisoformat(end_date)

        # Get statistics
        total_transfers = await transfers_collection.count_documents(
            {"event_type": "transfer_update"}
        )

        # Get successful transfers
        successful_transfers = await transfers_collection.count_documents({
            "event_type": "transfer_update",
            "event_data.status": "completed"
        })

        # Get failed transfers
        failed_transfers = await transfers_collection.count_documents({
            "event_type": "transfer_update",
            "event_data.status": "failed"
        })

        # Get recent transfers
        recent_transfers = await transfers_collection.find(
            {"event_type": "transfer_update"}
        ).sort("timestamp", -1).limit(10).to_list(length=10)

        return {
            "success": True,
            "statistics": {
                "total_transfers": total_transfers,
                "successful_transfers": successful_transfers,
                "failed_transfers": failed_transfers,
                "success_rate": (successful_transfers / total_transfers * 100) if total_transfers > 0 else 0,
            },
            "recent_transfers": recent_transfers
        }

    except Exception as e:
        logger.error(f"Error getting transfer statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get transfer statistics: {str(e)}"
        )

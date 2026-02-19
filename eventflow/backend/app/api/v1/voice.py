"""
Voice API endpoints.

Handles VAPI integration for task follow-up calls.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from ...core.database import get_database
from ...models.user import UserInDB
from ...api.dependencies import get_current_user
from ...services.vapi_service import EventFlowVAPIService
from ...core.config import settings

router = APIRouter(prefix="/voice", tags=["Voice Calls"])

# Global VAPI service instance (initialized at app startup)
_vapi_service_instance: Optional[EventFlowVAPIService] = None


async def get_vapi_service() -> EventFlowVAPIService:
    """Get or initialize VAPI service."""
    global _vapi_service_instance
    if _vapi_service_instance is None:
        _vapi_service_instance = EventFlowVAPIService()
        await _vapi_service_instance.initialize(
            vapi_api_key=settings.vapi_api_key
        )
    return _vapi_service_instance


@router.post("/call/{task_id}")
async def initiate_task_call(
    task_id: str,
    current_user: UserInDB = Depends(get_current_user),
    vapi_service: EventFlowVAPIService = Depends(get_vapi_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Initiate a voice call to the responsible person for a task.

    This will call the assigned person and have Ama (AI assistant) ask for:
    - Task status update
    - Progress percentage
    - Any blockers or issues
    - Estimated completion date

    The call is recorded and transcribed for later review.
    """
    # Get task
    task = await db["tasks"].find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify user owns the event
    event = await db["events"].find_one({
        "_id": ObjectId(task["event_id"]),
        "organizer_id": current_user.id,
    })
    if not event:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to call about this task"
        )

    # Check if task has assigned person
    if not task.get("assigned_to"):
        raise HTTPException(
            status_code=400,
            detail="Task has no assigned responsible person"
        )

    # Get responsible person
    person = await db["responsible_persons"].find_one({
        "_id": ObjectId(task["assigned_to"])
    })
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Responsible person not found"
        )

    # Check if user has wallet
    if not current_user.wallet_id:
        raise HTTPException(
            status_code=400,
            detail="No wallet found. Please set up your wallet first."
        )

    # Initiate call via VAPI service
    result = await vapi_service.call_responsible_person(
        task_id=str(task["_id"]),
        event_id=task["event_id"],
        person_name=person["name"],
        person_phone=person["phone"],
        task_title=task["title"],
        task_deadline=task["deadline"],
        wallet_id=current_user.wallet_id
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate call: {result.get('error')}"
        )

    # Save call record in database
    call_record = {
        "call_id": result.get("call_id"),
        "task_id": task_id,
        "event_id": task["event_id"],
        "responsible_person_id": str(person["_id"]),
        "person_name": person["name"],
        "person_phone": person["phone"],
        "initiated_by": current_user.id,
        "status": "initiated",
        "created_at": datetime.utcnow()
    }

    await db["voice_calls"].insert_one(call_record)

    return {
        "success": True,
        "call_id": result.get("call_id"),
        "message": f"Call initiated to {person['name']}",
        "status": result.get("status"),
        "person": {
            "name": person["name"],
            "phone": person["phone"],
            "role": person["role"]
        },
        "task": {
            "id": task_id,
            "title": task["title"],
            "deadline": task["deadline"]
        }
    }


@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    vapi_service: EventFlowVAPIService = Depends(get_vapi_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Handle VAPI webhook events.

    This endpoint receives webhook events from VAPI including:
    - call.started: Call connected
    - call.ended: Call finished (deducts cost from wallet)
    - function-call: Ama called a function (e.g., update_task_status)
    - transcript: Call transcript available

    Note: This endpoint is public (no auth) as it's called by VAPI service.
    """
    # Get webhook data
    try:
        webhook_data = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid webhook data: {str(e)}"
        )

    # Process webhook via VAPI service
    result = await vapi_service.handle_webhook(webhook_data)

    # Update call record in database if call ended
    event_type = webhook_data.get("event")
    call_id = webhook_data.get("callId")

    if event_type == "call.ended" and call_id:
        await db["voice_calls"].update_one(
            {"call_id": call_id},
            {
                "$set": {
                    "status": "ended",
                    "duration": webhook_data.get("duration"),
                    "ended_at": datetime.utcnow(),
                    "ended_reason": webhook_data.get("endedReason"),
                    "recording_url": webhook_data.get("recordingUrl"),
                    "transcript": webhook_data.get("transcript")
                }
            }
        )

    # Return 200 OK to VAPI
    return {
        "success": True,
        "event_type": event_type,
        "call_id": call_id,
        "processed": result.get("success", False)
    }


@router.get("/calls")
async def list_voice_calls(
    event_id: Optional[str] = None,
    task_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user),
    vapi_service: EventFlowVAPIService = Depends(get_vapi_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get voice call history for user's events.

    Can filter by event_id or task_id.
    """
    # Build query
    query = {"initiated_by": current_user.id}

    if event_id:
        # Verify user owns event
        event = await db["events"].find_one({
            "_id": ObjectId(event_id),
            "organizer_id": current_user.id,
        })
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        query["event_id"] = event_id

    if task_id:
        query["task_id"] = task_id

    # Get calls from database
    calls = []
    async for call_doc in db["voice_calls"].find(query).sort("created_at", -1):
        call_doc["_id"] = str(call_doc["_id"])
        calls.append(call_doc)

    return {
        "success": True,
        "calls": calls,
        "total": len(calls)
    }


@router.get("/calls/{call_id}")
async def get_call_details(
    call_id: str,
    current_user: UserInDB = Depends(get_current_user),
    vapi_service: EventFlowVAPIService = Depends(get_vapi_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get details of a specific voice call including transcript.
    """
    # Get call from database
    call = await db["voice_calls"].find_one({
        "call_id": call_id,
        "initiated_by": current_user.id
    })

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    call["_id"] = str(call["_id"])

    # Get task details
    if call.get("task_id"):
        task = await db["tasks"].find_one({"_id": ObjectId(call["task_id"])})
        if task:
            call["task"] = {
                "id": str(task["_id"]),
                "title": task["title"],
                "status": task["status"],
                "deadline": task["deadline"]
            }

    # Get event details
    if call.get("event_id"):
        event = await db["events"].find_one({"_id": ObjectId(call["event_id"])})
        if event:
            call["event"] = {
                "id": str(event["_id"]),
                "name": event["name"],
                "type": event["type"]
            }

    return {
        "success": True,
        "call": call
    }


@router.get("/status")
async def vapi_service_status(
    vapi_service: EventFlowVAPIService = Depends(get_vapi_service),
):
    """
    Get VAPI service status and configuration.

    Public endpoint for health checks.
    """
    return {
        "service": "EventFlow VAPI Integration",
        "initialized": vapi_service.initialized,
        "ama_assistant_ready": vapi_service.ama_assistant_id is not None,
        "ama_assistant_id": vapi_service.ama_assistant_id,
        "capabilities": [
            "task_follow_up_calls",
            "automated_status_updates",
            "call_recording",
            "transcription",
            "webhook_processing"
        ],
        "status": "operational" if vapi_service.initialized else "not_configured"
    }

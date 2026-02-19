"""
Notifications API endpoints.

Handles n8n workflow automation for multi-channel notifications.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel

from ...core.database import get_database
from ...models.user import UserInDB
from ...api.dependencies import get_current_user
from ...services.n8n_workflow_service import EventFlowN8NService
from ...core.config import settings

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Global n8n service instance (initialized at app startup)
_n8n_service_instance: Optional[EventFlowN8NService] = None


class TaskReminderRequest(BaseModel):
    """Task reminder request model."""
    channels: Optional[List[str]] = ["sms"]


class DailySummaryRequest(BaseModel):
    """Daily summary request model."""
    email_only: bool = False


async def get_n8n_service() -> EventFlowN8NService:
    """Get or initialize n8n service."""
    global _n8n_service_instance
    if _n8n_service_instance is None:
        _n8n_service_instance = EventFlowN8NService()
        await _n8n_service_instance.initialize(
            n8n_base_url=getattr(settings, 'n8n_base_url', None),
            n8n_api_key=getattr(settings, 'n8n_api_key', None)
        )
    return _n8n_service_instance


@router.post("/tasks/{task_id}/remind")
async def send_task_reminder(
    task_id: str,
    request: TaskReminderRequest,
    current_user: UserInDB = Depends(get_current_user),
    n8n_service: EventFlowN8NService = Depends(get_n8n_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Send task reminder to responsible person.

    Sends reminder via specified channels (SMS, WhatsApp, Email).
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
            detail="You don't have permission to send reminders for this task"
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

    # Send reminder via n8n workflow
    result = await n8n_service.send_task_reminder(
        task_id=str(task["_id"]),
        event_id=task["event_id"],
        task_title=task["title"],
        task_deadline=task["deadline"],
        responsible_person_name=person["name"],
        responsible_person_phone=person["phone"],
        responsible_person_email=person.get("email"),
        channels=request.channels
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send reminder: {result.get('error')}"
        )

    # Log notification in database
    notification_record = {
        "type": "task_reminder",
        "task_id": task_id,
        "event_id": task["event_id"],
        "responsible_person_id": str(person["_id"]),
        "channels": request.channels,
        "execution_id": result.get("execution_id"),
        "sent_by": current_user.id,
        "sent_at": datetime.utcnow()
    }

    await db["notifications"].insert_one(notification_record)

    return {
        "success": True,
        "message": f"Reminder sent to {person['name']}",
        "channels": request.channels,
        "execution_id": result.get("execution_id"),
        "person": {
            "name": person["name"],
            "phone": person["phone"],
            "email": person.get("email")
        }
    }


@router.post("/events/{event_id}/daily-summary")
async def send_daily_summary(
    event_id: str,
    request: DailySummaryRequest,
    current_user: UserInDB = Depends(get_current_user),
    n8n_service: EventFlowN8NService = Depends(get_n8n_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Send daily summary for an event.

    Includes task statistics and overdue alerts.
    """
    # Verify user owns the event
    event = await db["events"].find_one({
        "_id": ObjectId(event_id),
        "organizer_id": current_user.id,
    })
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get task summary
    tasks = await db["tasks"].find({"event_id": event_id}).to_list(length=None)

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t["status"] == "completed"])
    pending_tasks = len([t for t in tasks if t["status"] in ["pending", "in_progress"]])
    overdue_tasks = len([
        t for t in tasks
        if t["status"] != "completed" and t["deadline"] < datetime.utcnow()
    ])

    summary_data = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

    # Send summary via n8n workflow
    result = await n8n_service.send_daily_summary(
        event_id=event_id,
        event_name=event["name"],
        organizer_phone=current_user.phone,
        organizer_email=current_user.email if not request.email_only else current_user.email,
        summary_data=summary_data
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send daily summary: {result.get('error')}"
        )

    return {
        "success": True,
        "message": "Daily summary sent",
        "summary": summary_data,
        "execution_id": result.get("execution_id")
    }


@router.get("/workflows")
async def list_workflows(
    current_user: UserInDB = Depends(get_current_user),
    n8n_service: EventFlowN8NService = Depends(get_n8n_service),
):
    """
    List all EventFlow notification workflows.

    Returns workflow status and configuration.
    """
    result = await n8n_service.list_workflows()

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflows: {result.get('error')}"
        )

    return result


@router.get("/workflows/{workflow_name}")
async def get_workflow_status(
    workflow_name: str,
    current_user: UserInDB = Depends(get_current_user),
    n8n_service: EventFlowN8NService = Depends(get_n8n_service),
):
    """
    Get status of a specific workflow.

    Available workflows:
    - task_reminder
    - deadline_alert
    - task_escalation
    - daily_summary
    """
    result = await n8n_service.get_workflow_status(workflow_name)

    if not result.get("success"):
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 500,
            detail=result.get("error")
        )

    return result


@router.get("/history")
async def get_notification_history(
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get notification history for user's events.

    Can filter by event_id or task_id.
    """
    # Build query
    query: Dict = {}

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

    # For now, only show notifications sent by current user
    query["sent_by"] = current_user.id

    # Get notifications from database
    notifications = []
    async for notif_doc in db["notifications"].find(query).sort("sent_at", -1).limit(limit):
        notif_doc["_id"] = str(notif_doc["_id"])
        notifications.append(notif_doc)

    return {
        "success": True,
        "notifications": notifications,
        "total": len(notifications)
    }


@router.get("/status")
async def n8n_service_status(
    n8n_service: EventFlowN8NService = Depends(get_n8n_service),
):
    """
    Get n8n service status and configuration.

    Public endpoint for health checks.
    """
    return {
        "service": "EventFlow n8n Integration",
        "initialized": n8n_service.initialized,
        "configured_workflows": list(n8n_service.workflow_ids.keys()),
        "workflow_count": len(n8n_service.workflow_ids),
        "capabilities": [
            "task_reminders",
            "deadline_alerts",
            "task_escalations",
            "daily_summaries",
            "multi_channel_notifications"
        ],
        "supported_channels": ["sms", "whatsapp", "email"],
        "status": "operational" if n8n_service.initialized else "not_configured"
    }

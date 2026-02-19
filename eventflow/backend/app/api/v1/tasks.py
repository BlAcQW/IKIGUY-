"""
Tasks API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ...core.database import get_database
from ...models.user import UserInDB
from ...models.task import Task, TaskInDB
from ...schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from ...api.dependencies import get_current_user


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """List tasks (public demo mode - no authentication)."""
    query = {}

    # If event_id provided, filter by it (no ownership check for demo)
    if event_id:
        query["event_id"] = event_id

    if status:
        statuses = [s.strip() for s in status.split(",")]
        query["status"] = {"$in": statuses}

    tasks = []
    async for task_doc in db["tasks"].find(query):
        # Map _id to id for response
        task_id = str(task_doc.pop("_id"))

        # Get assigned person info if available
        assigned_person = None
        if task_doc.get("assigned_to"):
            person_doc = await db["responsible_persons"].find_one({
                "_id": ObjectId(task_doc["assigned_to"])
            })
            if person_doc:
                assigned_person = {
                    "id": str(person_doc["_id"]),
                    "name": person_doc["name"],
                    "phone": person_doc["phone"],
                    "role": person_doc["role"],
                }

        # Ensure required fields exist
        from datetime import datetime
        if "created_at" not in task_doc:
            task_doc["created_at"] = datetime.utcnow()
        if "updated_at" not in task_doc:
            task_doc["updated_at"] = datetime.utcnow()

        task_response = TaskResponse(
            id=task_id,
            **task_doc,
            assigned_person=assigned_person
        )
        tasks.append(task_response)

    return TaskListResponse(data=tasks, total=len(tasks))


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    current_user: UserInDB = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Update task status."""
    task = await db["tasks"].find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify user owns the event
    event = await db["events"].find_one({
        "_id": ObjectId(task["event_id"]),
        "organizer_id": current_user.id,
    })
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db["tasks"].update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": status}}
    )

    return {"message": "Task status updated", "status": status}

"""
CRM Task/Todo Management Routes.

Handles task and todo management for CRM workflow.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.database import MongoDB
from app.models.crm import CRMTask, TaskPriority, TaskStatus
from app.schemas.crm import CRMTaskCreate, CRMTaskUpdate, CRMTaskStats
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tasks", response_model=CRMTask, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: CRMTaskCreate,
    scope: OrganizationScoped = Depends(),
):
    """
    Create a new CRM task.

    Tasks can be linked to CRM entities (leads, customers, opportunities, contacts)
    or stand alone as general todos.

    Example request:
    ```json
    {
      "entity_type": "lead",
      "entity_id": "lead_12345",
      "title": "Follow up on proposal",
      "description": "Call to discuss pricing and next steps",
      "priority": "high",
      "due_date": "2025-11-20T17:00:00",
      "assigned_to": "user_123",
      "estimated_hours": 0.5,
      "tags": ["sales", "follow-up"]
    }
    ```
    """
    db = MongoDB.get_database()

    # Create task with organization and user context
    task = CRMTask(
        **task_data.model_dump(),
        organization_id=scope.org_id,
        assigned_by=scope.user.get("id") or scope.user.get("sub"),
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.crm_tasks.insert_one(task.model_dump())
    logger.info(f"Task {task.id} created for {task_data.entity_type or 'general'} in org {scope.org_id}")
    return task


@router.get("/tasks", response_model=List[CRMTask])
async def list_tasks(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None,
    assigned_by: Optional[str] = None,
    overdue_only: bool = False,
    due_today: bool = False,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
):
    """
    List tasks with filters.

    Supports filtering by:
    - entity_type and entity_id (tasks for specific entity)
    - status (todo, in_progress, completed, cancelled)
    - priority (low, medium, high, urgent)
    - assigned_to (user ID)
    - assigned_by (user ID)
    - overdue_only (only overdue tasks)
    - due_today (tasks due today)
    - tags (comma-separated list)
    """
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Apply filters
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if status_filter:
        query["status"] = status_filter
    if priority:
        query["priority"] = priority
    if assigned_to:
        query["assigned_to"] = assigned_to
    if assigned_by:
        query["assigned_by"] = assigned_by
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        query["tags"] = {"$in": tag_list}

    # Date filters
    now = datetime.utcnow()
    if overdue_only:
        query["status"] = {"$ne": TaskStatus.COMPLETED.value}
        query["due_date"] = {"$lt": now}
    if due_today:
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        query["due_date"] = {"$gte": today_start, "$lte": today_end}

    cursor = db.crm_tasks.find(query).skip(skip).limit(limit).sort("due_date", 1)
    tasks = await cursor.to_list(length=limit)
    return [CRMTask(**t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=CRMTask)
async def get_task(
    task_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get task details by ID."""
    db = MongoDB.get_database()
    task = await db.crm_tasks.find_one({"id": task_id, "organization_id": org_id})

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return CRMTask(**task)


@router.patch("/tasks/{task_id}", response_model=CRMTask)
async def update_task(
    task_id: str,
    update_data: CRMTaskUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update a task."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.crm_tasks.update_one(
        {"id": task_id, "organization_id": scope.org_id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = await db.crm_tasks.find_one({"id": task_id})
    return CRMTask(**task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete a task."""
    db = MongoDB.get_database()

    result = await db.crm_tasks.update_one(
        {"id": task_id, "organization_id": org_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return None


@router.get("/tasks/my-tasks", response_model=List[CRMTask])
async def get_my_tasks(
    scope: OrganizationScoped = Depends(),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Get current user's tasks.

    Returns tasks assigned to the authenticated user.
    Useful for personal task dashboards.
    """
    db = MongoDB.get_database()

    user_id = scope.user.get("id") or scope.user.get("sub")

    query = {
        "organization_id": scope.org_id,
        "assigned_to": user_id,
        "is_active": True
    }

    if status_filter:
        query["status"] = status_filter

    cursor = db.crm_tasks.find(query).limit(limit).sort("due_date", 1)
    tasks = await cursor.to_list(length=limit)
    return [CRMTask(**t) for t in tasks]


@router.get("/tasks/assigned-to/{user_id}", response_model=List[CRMTask])
async def get_user_tasks(
    user_id: str,
    org_id: str = Depends(require_organization_access),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Get tasks assigned to a specific user.

    Useful for managers viewing team member tasks.
    """
    db = MongoDB.get_database()

    query = {
        "organization_id": org_id,
        "assigned_to": user_id,
        "is_active": True
    }

    if status_filter:
        query["status"] = status_filter

    cursor = db.crm_tasks.find(query).limit(limit).sort("due_date", 1)
    tasks = await cursor.to_list(length=limit)
    return [CRMTask(**t) for t in tasks]


@router.patch("/tasks/{task_id}/complete", response_model=CRMTask)
async def complete_task(
    task_id: str,
    actual_hours: Optional[float] = Query(None, description="Actual hours spent on task"),
    scope: OrganizationScoped = Depends(),
):
    """
    Mark task as completed.

    Updates status to COMPLETED and records completion timestamp.
    Optionally records actual hours spent.
    """
    db = MongoDB.get_database()

    update_data = {
        "status": TaskStatus.COMPLETED.value,
        "completed_date": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "updated_by": scope.user.get("id") or scope.user.get("sub")
    }

    if actual_hours is not None:
        update_data["actual_hours"] = actual_hours

    result = await db.crm_tasks.update_one(
        {"id": task_id, "organization_id": scope.org_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = await db.crm_tasks.find_one({"id": task_id})
    return CRMTask(**task)


@router.patch("/tasks/{task_id}/start", response_model=CRMTask)
async def start_task(
    task_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Mark task as in progress.

    Updates status to IN_PROGRESS and records start timestamp.
    """
    db = MongoDB.get_database()

    result = await db.crm_tasks.update_one(
        {"id": task_id, "organization_id": scope.org_id},
        {
            "$set": {
                "status": TaskStatus.IN_PROGRESS.value,
                "start_date": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = await db.crm_tasks.find_one({"id": task_id})
    return CRMTask(**task)


@router.patch("/tasks/{task_id}/cancel", response_model=CRMTask)
async def cancel_task(
    task_id: str,
    scope: OrganizationScoped = Depends(),
):
    """
    Cancel a task.

    Updates status to CANCELLED.
    """
    db = MongoDB.get_database()

    result = await db.crm_tasks.update_one(
        {"id": task_id, "organization_id": scope.org_id},
        {
            "$set": {
                "status": TaskStatus.CANCELLED.value,
                "updated_at": datetime.utcnow(),
                "updated_by": scope.user.get("id") or scope.user.get("sub")
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task = await db.crm_tasks.find_one({"id": task_id})
    return CRMTask(**task)


@router.get("/tasks/for-entity/{entity_type}/{entity_id}", response_model=List[CRMTask])
async def get_entity_tasks(
    entity_type: str,
    entity_id: str,
    org_id: str = Depends(require_organization_access),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Get all tasks for a specific CRM entity.

    Returns tasks linked to a lead, customer, opportunity, or contact.
    Useful for entity detail views showing related tasks.
    """
    db = MongoDB.get_database()

    query = {
        "organization_id": org_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "is_active": True
    }

    if status_filter:
        query["status"] = status_filter

    cursor = db.crm_tasks.find(query).limit(limit).sort("due_date", 1)
    tasks = await cursor.to_list(length=limit)
    return [CRMTask(**t) for t in tasks]


@router.get("/tasks/stats", response_model=CRMTaskStats)
async def get_task_stats(
    org_id: str = Depends(require_organization_access),
):
    """
    Get task statistics.

    Returns:
    - Total task count
    - Tasks by status (todo, in_progress, completed, cancelled)
    - Tasks by priority (low, medium, high, urgent)
    - Overdue task count
    - Due today count
    - Due this week count
    - Completion statistics
    - Top assignees by task count
    """
    db = MongoDB.get_database()

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    week_end = datetime.combine((date.today() + timedelta(days=7)), datetime.max.time())

    # Total tasks
    total_tasks = await db.crm_tasks.count_documents({
        "organization_id": org_id,
        "is_active": True
    })

    # Tasks by status
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    tasks_by_status_cursor = db.crm_tasks.aggregate(pipeline)
    tasks_by_status_list = await tasks_by_status_cursor.to_list(length=10)
    tasks_by_status = {item["_id"]: item["count"] for item in tasks_by_status_list}

    # Tasks by priority
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    tasks_by_priority_cursor = db.crm_tasks.aggregate(pipeline)
    tasks_by_priority_list = await tasks_by_priority_cursor.to_list(length=10)
    tasks_by_priority = {item["_id"]: item["count"] for item in tasks_by_priority_list}

    # Overdue tasks
    overdue_tasks = await db.crm_tasks.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "status": {"$ne": TaskStatus.COMPLETED.value},
        "due_date": {"$lt": now}
    })

    # Due today
    due_today = await db.crm_tasks.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "status": {"$ne": TaskStatus.COMPLETED.value},
        "due_date": {"$gte": today_start, "$lte": today_end}
    })

    # Due this week
    due_this_week = await db.crm_tasks.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "status": {"$ne": TaskStatus.COMPLETED.value},
        "due_date": {"$gte": now, "$lte": week_end}
    })

    # Completed this week
    completed_this_week = await db.crm_tasks.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "status": TaskStatus.COMPLETED.value,
        "completed_date": {"$gte": week_ago}
    })

    # Completed this month
    completed_this_month = await db.crm_tasks.count_documents({
        "organization_id": org_id,
        "is_active": True,
        "status": TaskStatus.COMPLETED.value,
        "completed_date": {"$gte": month_ago}
    })

    # Average completion time (for tasks with both start_date and completed_date)
    pipeline = [
        {
            "$match": {
                "organization_id": org_id,
                "is_active": True,
                "status": TaskStatus.COMPLETED.value,
                "start_date": {"$exists": True, "$ne": None},
                "completed_date": {"$exists": True, "$ne": None}
            }
        },
        {
            "$project": {
                "completion_time_ms": {
                    "$subtract": ["$completed_date", "$start_date"]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "avg_completion_time_ms": {"$avg": "$completion_time_ms"}
            }
        }
    ]
    avg_completion_cursor = db.crm_tasks.aggregate(pipeline)
    avg_completion_list = await avg_completion_cursor.to_list(length=1)

    average_completion_time_hours = None
    if avg_completion_list:
        avg_ms = avg_completion_list[0].get("avg_completion_time_ms")
        if avg_ms:
            average_completion_time_hours = round(avg_ms / (1000 * 60 * 60), 2)  # Convert ms to hours

    # Top assignees
    pipeline = [
        {"$match": {"organization_id": org_id, "is_active": True}},
        {"$group": {"_id": "$assigned_to", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_assignees_cursor = db.crm_tasks.aggregate(pipeline)
    top_assignees_list = await top_assignees_cursor.to_list(length=10)
    top_assignees = [
        {"user_id": item["_id"], "task_count": item["count"]}
        for item in top_assignees_list
    ]

    return CRMTaskStats(
        total_tasks=total_tasks,
        tasks_by_status=tasks_by_status,
        tasks_by_priority=tasks_by_priority,
        overdue_tasks=overdue_tasks,
        due_today=due_today,
        due_this_week=due_this_week,
        completed_this_week=completed_this_week,
        completed_this_month=completed_this_month,
        average_completion_time_hours=average_completion_time_hours,
        top_assignees=top_assignees
    )

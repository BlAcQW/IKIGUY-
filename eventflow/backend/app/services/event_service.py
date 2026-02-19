"""
Event service for EventFlow.

Handles event CRUD operations, dashboard stats, and AI task generation.
"""

from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.event import Event, EventInDB
from ..models.task import Task, TaskInDB
from ..schemas.event import EventCreate, EventUpdate, DashboardResponse, TaskStats
from .ai_task_generator import AITaskGenerator


class EventService:
    """Event service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize event service."""
        self.db = db
        self.events_collection = db["events"]
        self.tasks_collection = db["tasks"]
        self.persons_collection = db["responsible_persons"]
        self.ai_generator = AITaskGenerator()  # Initialize AI task generator

    async def create_event(self, user_id: str, event_data: EventCreate) -> EventInDB:
        """
        Create a new event.

        Args:
            user_id: User ID of event organizer
            event_data: Event creation data

        Returns:
            Created event
        """
        event = Event(
            **event_data.model_dump(),
            organizer_id=user_id,
            status="planning",
        )

        result = await self.events_collection.insert_one(event.model_dump())
        event_dict = event.model_dump()
        event_dict["_id"] = str(result.inserted_id)

        return EventInDB(**event_dict)

    async def get_event(self, event_id: str, user_id: str) -> Optional[EventInDB]:
        """
        Get event by ID.

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)

        Returns:
            Event if found and user is authorized
        """
        try:
            event_doc = await self.events_collection.find_one({
                "_id": ObjectId(event_id),
                "organizer_id": user_id,
            })

            if event_doc:
                event_doc["_id"] = str(event_doc["_id"])
                return EventInDB(**event_doc)
            return None
        except Exception:
            return None

    async def list_events(
        self,
        user_id: str,
        status_filter: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[EventInDB], int]:
        """
        List events for user.

        Args:
            user_id: User ID
            status_filter: Optional status filter
            skip: Number of records to skip
            limit: Max number of records to return

        Returns:
            Tuple of (events list, total count)
        """
        query = {"organizer_id": user_id}

        if status_filter:
            query["status"] = {"$in": status_filter}

        # Get total count
        total = await self.events_collection.count_documents(query)

        # Get events
        cursor = self.events_collection.find(query).sort("date", -1).skip(skip).limit(limit)
        events = []

        async for event_doc in cursor:
            event_doc["_id"] = str(event_doc["_id"])
            events.append(EventInDB(**event_doc))

        return events, total

    async def update_event(
        self,
        event_id: str,
        user_id: str,
        event_update: EventUpdate,
    ) -> Optional[EventInDB]:
        """
        Update event.

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)
            event_update: Update data

        Returns:
            Updated event
        """
        try:
            # Filter out None values
            update_data = {
                k: v for k, v in event_update.model_dump().items() if v is not None
            }

            if not update_data:
                return await self.get_event(event_id, user_id)

            update_data["updated_at"] = datetime.utcnow()

            result = await self.events_collection.find_one_and_update(
                {"_id": ObjectId(event_id), "organizer_id": user_id},
                {"$set": update_data},
                return_document=True,
            )

            if result:
                result["_id"] = str(result["_id"])
                return EventInDB(**result)
            return None
        except Exception:
            return None

    async def delete_event(self, event_id: str, user_id: str) -> bool:
        """
        Delete event.

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted
        """
        try:
            result = await self.events_collection.delete_one({
                "_id": ObjectId(event_id),
                "organizer_id": user_id,
            })
            return result.deleted_count > 0
        except Exception:
            return False

    async def get_dashboard(self, event_id: str, user_id: str) -> Optional[DashboardResponse]:
        """
        Get event dashboard statistics.

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)

        Returns:
            Dashboard stats
        """
        # Verify event exists and user is authorized
        event = await self.get_event(event_id, user_id)
        if not event:
            return None

        # Get task statistics
        tasks = await self.tasks_collection.find({"event_id": event_id}).to_list(length=None)

        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
        pending = sum(1 for t in tasks if t.get("status") == "pending")

        # Calculate overdue tasks
        now = datetime.utcnow()
        overdue = sum(
            1 for t in tasks
            if t.get("status") != "completed" and t.get("deadline", now) < now
        )

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0.0

        # Get responsible persons count
        persons_count = await self.persons_collection.count_documents({"event_id": event_id})

        # Calculate days until event
        days_until = (event.date - datetime.utcnow()).days

        return DashboardResponse(
            event_id=event_id,
            tasks=TaskStats(
                total=total_tasks,
                completed=completed,
                in_progress=in_progress,
                pending=pending,
                overdue=overdue,
                completion_rate=completion_rate,
            ),
            responsible_persons_count=persons_count,
            days_until_event=days_until,
            budget_spent=0.0,  # TODO: Calculate from tasks
            budget_remaining=event.budget_max or 0.0,
        )

    async def generate_tasks(self, event_id: str, user_id: str) -> List[TaskInDB]:
        """
        Generate AI-powered tasks for event.

        Uses AI Task Generator service (with RAG integration) to generate tasks.

        Args:
            event_id: Event ID
            user_id: User ID (for authorization)

        Returns:
            List of generated tasks
        """
        event = await self.get_event(event_id, user_id)
        if not event:
            return []

        # Generate tasks using AI service
        task_suggestions = await self.ai_generator.generate_tasks(event, use_ai=False)

        # Save generated tasks to database
        generated_tasks = []
        for task_data in task_suggestions:
            task = Task(
                event_id=event_id,
                title=task_data["title"],
                description=task_data.get("description", ""),
                category=task_data["category"],
                priority=task_data.get("priority", "medium"),
                status=task_data.get("status", "pending"),
                deadline=task_data["deadline"],
            )

            result = await self.tasks_collection.insert_one(task.model_dump())
            task_dict = task.model_dump()
            task_dict["_id"] = str(result.inserted_id)
            generated_tasks.append(TaskInDB(**task_dict))

        return generated_tasks

    # Public demo methods (no authentication required)

    async def list_all_events(
        self,
        status_filter: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[EventInDB], int]:
        """
        List all events (public demo mode - no user filtering).

        Args:
            status_filter: Optional status filter
            skip: Number of records to skip
            limit: Max number of records to return

        Returns:
            Tuple of (events list, total count)
        """
        query = {}

        if status_filter:
            query["status"] = {"$in": status_filter}

        # Get total count
        total = await self.events_collection.count_documents(query)

        # Get events
        cursor = self.events_collection.find(query).sort("date", -1).skip(skip).limit(limit)
        events = []

        async for event_doc in cursor:
            event_doc["_id"] = str(event_doc["_id"])
            events.append(EventInDB(**event_doc))

        return events, total

    async def get_event_public(self, event_id: str) -> Optional[EventInDB]:
        """
        Get event by ID (public demo mode - no authorization check).

        Args:
            event_id: Event ID

        Returns:
            Event if found
        """
        try:
            event_doc = await self.events_collection.find_one({
                "_id": ObjectId(event_id),
            })

            if event_doc:
                event_doc["_id"] = str(event_doc["_id"])
                return EventInDB(**event_doc)
            return None
        except Exception:
            return None

    async def update_event_public(
        self,
        event_id: str,
        event_update: EventUpdate,
    ) -> Optional[EventInDB]:
        """
        Update event (public demo mode - no authorization check).

        Args:
            event_id: Event ID
            event_update: Update data

        Returns:
            Updated event
        """
        try:
            # Filter out None values
            update_data = {
                k: v for k, v in event_update.model_dump().items() if v is not None
            }

            if not update_data:
                return await self.get_event_public(event_id)

            update_data["updated_at"] = datetime.utcnow()

            result = await self.events_collection.find_one_and_update(
                {"_id": ObjectId(event_id)},
                {"$set": update_data},
                return_document=True,
            )

            if result:
                result["_id"] = str(result["_id"])
                return EventInDB(**result)
            return None
        except Exception:
            return None

    async def delete_event_public(self, event_id: str) -> bool:
        """
        Delete event (public demo mode - no authorization check).

        Args:
            event_id: Event ID

        Returns:
            True if deleted
        """
        try:
            result = await self.events_collection.delete_one({
                "_id": ObjectId(event_id),
            })
            return result.deleted_count > 0
        except Exception:
            return False

    async def get_dashboard_public(self, event_id: str) -> Optional[DashboardResponse]:
        """
        Get event dashboard statistics (public demo mode - no authorization check).

        Args:
            event_id: Event ID

        Returns:
            Dashboard stats
        """
        # Get event without authorization
        event = await self.get_event_public(event_id)
        if not event:
            return None

        # Get task statistics
        tasks = await self.tasks_collection.find({"event_id": event_id}).to_list(length=None)

        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
        pending = sum(1 for t in tasks if t.get("status") == "pending")

        # Calculate overdue tasks
        now = datetime.utcnow()
        overdue = sum(
            1 for t in tasks
            if t.get("status") != "completed" and t.get("deadline", now) < now
        )

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0.0

        # Get responsible persons count (don't filter by event_id if not available)
        persons_count = await self.persons_collection.count_documents({})

        # Calculate days until event
        days_until = (event.date - datetime.utcnow()).days

        return DashboardResponse(
            event_id=event_id,
            tasks=TaskStats(
                total=total_tasks,
                completed=completed,
                in_progress=in_progress,
                pending=pending,
                overdue=overdue,
                completion_rate=completion_rate,
            ),
            responsible_persons_count=persons_count,
            days_until_event=days_until,
            budget_spent=0.0,  # TODO: Calculate from tasks
            budget_remaining=event.budget_max or 0.0,
        )

    async def generate_tasks_public(self, event_id: str) -> List[TaskInDB]:
        """
        Generate AI-powered tasks for event (public demo mode - no authorization check).

        Args:
            event_id: Event ID

        Returns:
            List of generated tasks
        """
        event = await self.get_event_public(event_id)
        if not event:
            return []

        # Generate tasks using AI service
        task_suggestions = await self.ai_generator.generate_tasks(event, use_ai=False)

        # Save generated tasks to database
        generated_tasks = []
        for task_data in task_suggestions:
            task = Task(
                event_id=event_id,
                title=task_data["title"],
                description=task_data.get("description", ""),
                category=task_data["category"],
                priority=task_data.get("priority", "medium"),
                status=task_data.get("status", "pending"),
                deadline=task_data["deadline"],
            )

            result = await self.tasks_collection.insert_one(task.model_dump())
            task_dict = task.model_dump()
            task_dict["_id"] = str(result.inserted_id)
            generated_tasks.append(TaskInDB(**task_dict))

        return generated_tasks

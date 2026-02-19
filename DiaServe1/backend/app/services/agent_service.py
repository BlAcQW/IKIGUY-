"""
Agent Service

Business logic for managing real estate agents, their profiles, and availability.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from app.models.agent import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentListResponse,
    AgentStats,
    AgentStatus,
    DaySchedule
)


class AgentService:
    """
    Service for managing real estate agents.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize agent service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.agents_collection = db["agents"]

    async def create_agent(
        self,
        organization_id: str,
        agent_data: AgentCreate
    ) -> Agent:
        """
        Create a new agent profile.

        Args:
            organization_id: Organization ID
            agent_data: Agent creation data

        Returns:
            Created agent

        Raises:
            ValueError: If email already exists for organization
        """
        # Check if email already exists
        existing = await self.agents_collection.find_one({
            "organization_id": organization_id,
            "email": agent_data.email
        })
        if existing:
            raise ValueError(f"Agent with email {agent_data.email} already exists")

        # Create agent
        agent = Agent(
            id=f"agent_{uuid.uuid4().hex[:12]}",
            organization_id=organization_id,
            **agent_data.model_dump()
        )

        # Insert into database
        await self.agents_collection.insert_one(agent.model_dump())

        return agent

    async def get_agent(
        self,
        agent_id: str,
        organization_id: str
    ) -> Optional[Agent]:
        """
        Get agent by ID.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID

        Returns:
            Agent if found, None otherwise
        """
        doc = await self.agents_collection.find_one({
            "id": agent_id,
            "organization_id": organization_id
        })

        if not doc:
            return None

        return Agent(**doc)

    async def list_agents(
        self,
        organization_id: str,
        status: Optional[AgentStatus] = None,
        specialization: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> AgentListResponse:
        """
        List agents with optional filters.

        Args:
            organization_id: Organization ID
            status: Filter by status
            specialization: Filter by specialization
            search: Search in name or email
            limit: Page size
            offset: Page offset

        Returns:
            List of agents with pagination info
        """
        query = {"organization_id": organization_id}

        if status:
            query["status"] = status

        if specialization:
            query["specializations"] = specialization

        if search:
            query["$or"] = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total = await self.agents_collection.count_documents(query)

        # Get paginated results
        cursor = self.agents_collection.find(query).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        agents = [Agent(**doc) for doc in docs]

        return AgentListResponse(
            agents=agents,
            total=total,
            limit=limit,
            offset=offset
        )

    async def update_agent(
        self,
        agent_id: str,
        organization_id: str,
        updates: AgentUpdate
    ) -> Optional[Agent]:
        """
        Update agent profile.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID
            updates: Fields to update

        Returns:
            Updated agent if found, None otherwise
        """
        # Get existing agent
        existing = await self.get_agent(agent_id, organization_id)
        if not existing:
            return None

        # Prepare update data (only include provided fields)
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        # Update in database
        await self.agents_collection.update_one(
            {"id": agent_id, "organization_id": organization_id},
            {"$set": update_data}
        )

        # Return updated agent
        return await self.get_agent(agent_id, organization_id)

    async def delete_agent(
        self,
        agent_id: str,
        organization_id: str
    ) -> bool:
        """
        Delete an agent (soft delete by setting status to inactive).

        Args:
            agent_id: Agent ID
            organization_id: Organization ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.agents_collection.update_one(
            {"id": agent_id, "organization_id": organization_id},
            {
                "$set": {
                    "status": AgentStatus.INACTIVE,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return result.modified_count > 0

    async def get_agent_stats(
        self,
        agent_id: str,
        organization_id: str
    ) -> Optional[AgentStats]:
        """
        Get agent performance statistics.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID

        Returns:
            Agent statistics if found, None otherwise
        """
        agent = await self.get_agent(agent_id, organization_id)
        if not agent:
            return None

        # Get bookings for this agent
        bookings_collection = self.db["bookings"]

        # Count bookings by status
        pipeline = [
            {
                "$match": {
                    "agent_id": agent_id,
                    "organization_id": organization_id
                }
            },
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        status_counts = {}
        async for doc in bookings_collection.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]

        total_bookings = sum(status_counts.values())
        completed = status_counts.get("completed", 0)
        cancelled = status_counts.get("cancelled", 0)
        no_shows = status_counts.get("no-show", 0)

        # Calculate completion rate
        completion_rate = (completed / total_bookings * 100) if total_bookings > 0 else 0

        # Get upcoming bookings (confirmed or requested, scheduled in future)
        now = datetime.utcnow()
        upcoming = await bookings_collection.count_documents({
            "agent_id": agent_id,
            "organization_id": organization_id,
            "status": {"$in": ["requested", "confirmed"]},
            "scheduled_at": {"$gte": now}
        })

        # This week
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        bookings_this_week = await bookings_collection.count_documents({
            "agent_id": agent_id,
            "organization_id": organization_id,
            "scheduled_at": {"$gte": week_start, "$lt": week_end}
        })

        # This month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = month_start + timedelta(days=32)
        month_end = next_month.replace(day=1)
        bookings_this_month = await bookings_collection.count_documents({
            "agent_id": agent_id,
            "organization_id": organization_id,
            "scheduled_at": {"$gte": month_start, "$lt": month_end}
        })

        # Get rating stats
        ratings_pipeline = [
            {
                "$match": {
                    "agent_id": agent_id,
                    "organization_id": organization_id,
                    "rating": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_rating": {"$avg": "$rating"},
                    "count": {"$sum": 1}
                }
            }
        ]

        rating_stats = await bookings_collection.aggregate(ratings_pipeline).to_list(1)
        avg_rating = rating_stats[0]["avg_rating"] if rating_stats else 0.0
        total_ratings = rating_stats[0]["count"] if rating_stats else 0

        return AgentStats(
            agent_id=agent_id,
            total_bookings=total_bookings,
            completed_tours=completed,
            cancelled_bookings=cancelled,
            no_shows=no_shows,
            completion_rate=round(completion_rate, 2),
            average_rating=round(avg_rating, 2),
            total_ratings=total_ratings,
            upcoming_bookings=upcoming,
            bookings_this_week=bookings_this_week,
            bookings_this_month=bookings_this_month
        )

    async def is_agent_available(
        self,
        agent_id: str,
        organization_id: str,
        start_time: datetime,
        duration_minutes: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if agent is available for a booking at the given time.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID
            start_time: Proposed booking start time
            duration_minutes: Duration in minutes

        Returns:
            Tuple of (is_available, reason_if_not_available)
        """
        agent = await self.get_agent(agent_id, organization_id)
        if not agent:
            return False, "Agent not found"

        if agent.status != AgentStatus.ACTIVE:
            return False, f"Agent is {agent.status}"

        # Check working hours
        if agent.working_hours:
            day_name = start_time.strftime("%A").lower()
            day_schedule: Optional[DaySchedule] = getattr(agent.working_hours, day_name, None)

            if not day_schedule or not day_schedule.available:
                return False, f"Agent doesn't work on {day_name.capitalize()}s"

            # Parse time
            start_hour, start_minute = map(int, day_schedule.start.split(":"))
            end_hour, end_minute = map(int, day_schedule.end.split(":"))

            booking_start = start_time.time()
            booking_end = (start_time + timedelta(minutes=duration_minutes)).time()

            work_start = datetime.min.time().replace(hour=start_hour, minute=start_minute)
            work_end = datetime.min.time().replace(hour=end_hour, minute=end_minute)

            if booking_start < work_start or booking_end > work_end:
                return False, f"Outside working hours ({day_schedule.start} - {day_schedule.end})"

        # Check existing bookings for conflicts
        end_time = start_time + timedelta(minutes=duration_minutes)
        buffer = timedelta(minutes=agent.buffer_minutes)

        bookings_collection = self.db["bookings"]
        conflicting = await bookings_collection.find_one({
            "agent_id": agent_id,
            "organization_id": organization_id,
            "status": {"$in": ["requested", "confirmed"]},
            "$or": [
                {
                    # New booking starts during existing booking (with buffer)
                    "scheduled_at": {"$lte": start_time + buffer},
                    "$expr": {
                        "$gte": [
                            {"$add": ["$scheduled_at", {"$multiply": ["$duration_minutes", 60000]}]},
                            start_time - buffer
                        ]
                    }
                }
            ]
        })

        if conflicting:
            return False, "Agent has a conflicting booking at this time"

        # Check max bookings per day
        day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        bookings_count = await bookings_collection.count_documents({
            "agent_id": agent_id,
            "organization_id": organization_id,
            "status": {"$in": ["requested", "confirmed"]},
            "scheduled_at": {"$gte": day_start, "$lt": day_end}
        })

        if bookings_count >= agent.max_bookings_per_day:
            return False, f"Agent has reached max bookings per day ({agent.max_bookings_per_day})"

        return True, None

    async def get_available_agents(
        self,
        organization_id: str,
        start_time: datetime,
        duration_minutes: int,
        specialization: Optional[str] = None
    ) -> List[Agent]:
        """
        Get all agents available for a booking at the given time.

        Args:
            organization_id: Organization ID
            start_time: Proposed booking start time
            duration_minutes: Duration in minutes
            specialization: Filter by specialization

        Returns:
            List of available agents
        """
        query = {
            "organization_id": organization_id,
            "status": AgentStatus.ACTIVE
        }

        if specialization:
            query["specializations"] = specialization

        # Get all active agents
        cursor = self.agents_collection.find(query)
        docs = await cursor.to_list(length=None)
        all_agents = [Agent(**doc) for doc in docs]

        # Filter by availability
        available_agents = []
        for agent in all_agents:
            is_available, _ = await self.is_agent_available(
                agent.id,
                organization_id,
                start_time,
                duration_minutes
            )
            if is_available:
                available_agents.append(agent)

        return available_agents

    async def update_agent_metrics(
        self,
        agent_id: str,
        organization_id: str
    ) -> Optional[Agent]:
        """
        Update agent performance metrics from bookings data.

        Args:
            agent_id: Agent ID
            organization_id: Organization ID

        Returns:
            Updated agent if found
        """
        stats = await self.get_agent_stats(agent_id, organization_id)
        if not stats:
            return None

        # Update agent metrics
        await self.agents_collection.update_one(
            {"id": agent_id, "organization_id": organization_id},
            {
                "$set": {
                    "total_bookings": stats.total_bookings,
                    "completed_tours": stats.completed_tours,
                    "average_rating": stats.average_rating,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return await self.get_agent(agent_id, organization_id)

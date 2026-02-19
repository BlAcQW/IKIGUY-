"""
Dashboard Service for EventFlow.

Provides comprehensive statistics and metrics for the dashboard.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from collections import defaultdict

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Dashboard service for EventFlow.

    Provides comprehensive statistics and metrics for event management,
    including event stats, task stats, budget tracking, and timeline metrics.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize dashboard service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def get_dashboard_statistics(
        self,
        user_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics for a user.

        Args:
            user_id: User ID
            organization_id: Optional organization ID filter

        Returns:
            Dictionary with comprehensive dashboard statistics
        """
        try:
            # Build base query
            base_query: Dict[str, Any] = {}

            # Add organization filter if provided
            if organization_id:
                base_query["organization_id"] = organization_id
            else:
                # Get user's events (as organizer or participant)
                base_query["$or"] = [
                    {"organizer_id": user_id},
                    {"participants": user_id}
                ]

            # Get all relevant events and tasks
            events = await self.db.events.find(base_query).to_list(None)

            # Get tasks for these events
            event_ids = [str(event["_id"]) for event in events]
            tasks = []
            if event_ids:
                tasks = await self.db.tasks.find({
                    "event_id": {"$in": event_ids}
                }).to_list(None)

            # Calculate statistics
            event_stats = self._calculate_event_statistics(events)
            task_stats = self._calculate_task_statistics(tasks)
            budget_stats = self._calculate_budget_statistics(events, tasks)
            timeline_stats = self._calculate_timeline_statistics(events)
            activity_stats = await self._calculate_activity_statistics(events, tasks)

            return {
                "user_id": user_id,
                "organization_id": organization_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "events": event_stats,
                "tasks": task_stats,
                "budget": budget_stats,
                "timeline": timeline_stats,
                "activity": activity_stats,
                "summary": self._generate_summary(
                    event_stats,
                    task_stats,
                    budget_stats,
                    timeline_stats
                )
            }

        except Exception as e:
            self.logger.error(f"Failed to get dashboard statistics: {e}")
            raise

    async def get_event_dashboard(
        self,
        event_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics for a specific event.

        Args:
            event_id: Event ID
            user_id: Optional user ID for personalization

        Returns:
            Dictionary with event-specific dashboard statistics
        """
        try:
            # Get event
            event = await self.db.events.find_one({"_id": ObjectId(event_id)})

            if not event:
                raise ValueError(f"Event not found: {event_id}")

            # Get tasks for this event
            tasks = await self.db.tasks.find({"event_id": event_id}).to_list(None)

            # Get responsible persons
            responsible_persons = await self.db.responsible_persons.find({
                "event_id": ObjectId(event_id)
            }).to_list(None)

            # Calculate statistics
            task_stats = self._calculate_task_statistics(tasks)
            budget_stats = self._calculate_budget_statistics([event], tasks)

            # Calculate completion metrics
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Calculate days until event
            event_date = event.get("date")
            if isinstance(event_date, str):
                event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
            days_until = (event_date - datetime.now(timezone.utc)).days if event_date else None

            # Get overdue tasks
            overdue_tasks = [
                t for t in tasks
                if t.get("status") != "completed" and
                datetime.fromisoformat(t.get("deadline", "").replace('Z', '+00:00')) < datetime.now(timezone.utc)
            ]

            # Get critical tasks not completed
            critical_tasks = [
                t for t in tasks
                if t.get("priority") in ["critical", "high"] and
                t.get("status") != "completed"
            ]

            return {
                "event_id": event_id,
                "event_name": event.get("name"),
                "event_type": event.get("type"),
                "event_status": event.get("status"),
                "event_date": event_date.isoformat() if event_date else None,
                "days_until_event": days_until,
                "location": event.get("location"),
                "num_guests": event.get("num_guests", 0),
                "tasks": task_stats,
                "budget": budget_stats,
                "completion": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "completion_rate": round(completion_rate, 2),
                    "pending_tasks": task_stats["by_status"].get("pending", 0),
                    "in_progress_tasks": task_stats["by_status"].get("in_progress", 0),
                    "overdue_tasks": len(overdue_tasks),
                    "critical_tasks_pending": len(critical_tasks)
                },
                "team": {
                    "total_responsible_persons": len(responsible_persons),
                    "tasks_assigned": sum(1 for t in tasks if t.get("assigned_to")),
                    "tasks_unassigned": sum(1 for t in tasks if not t.get("assigned_to"))
                },
                "alerts": self._generate_event_alerts(
                    event,
                    tasks,
                    overdue_tasks,
                    critical_tasks,
                    days_until
                )
            }

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get event dashboard: {e}")
            raise

    def _calculate_event_statistics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate event statistics.

        Args:
            events: List of events

        Returns:
            Dictionary with event statistics
        """
        now = datetime.now(timezone.utc)

        stats = {
            "total": len(events),
            "by_status": defaultdict(int),
            "by_type": defaultdict(int),
            "upcoming": 0,
            "active": 0,
            "past": 0,
            "this_month": 0,
            "next_month": 0
        }

        for event in events:
            # Count by status
            status = event.get("status", "planning")
            stats["by_status"][status] += 1

            # Count by type
            event_type = event.get("type", "other")
            stats["by_type"][event_type] += 1

            # Count by timeline
            event_date = event.get("date")
            if event_date:
                if isinstance(event_date, str):
                    event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))

                days_until = (event_date - now).days

                if days_until >= 0:
                    stats["upcoming"] += 1
                    if days_until <= 7:
                        stats["active"] += 1
                else:
                    stats["past"] += 1

                # This month / next month
                if event_date.year == now.year and event_date.month == now.month:
                    stats["this_month"] += 1

                next_month = now + timedelta(days=30)
                if event_date.year == next_month.year and event_date.month == next_month.month:
                    stats["next_month"] += 1

        # Convert defaultdict to regular dict
        stats["by_status"] = dict(stats["by_status"])
        stats["by_type"] = dict(stats["by_type"])

        return stats

    def _calculate_task_statistics(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate task statistics.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary with task statistics
        """
        now = datetime.now(timezone.utc)

        stats = {
            "total": len(tasks),
            "by_status": defaultdict(int),
            "by_priority": defaultdict(int),
            "by_category": defaultdict(int),
            "completed": 0,
            "pending": 0,
            "in_progress": 0,
            "overdue": 0,
            "due_this_week": 0,
            "due_today": 0,
            "completion_rate": 0.0
        }

        for task in tasks:
            # Count by status
            status = task.get("status", "pending")
            stats["by_status"][status] += 1

            if status == "completed":
                stats["completed"] += 1
            elif status == "pending":
                stats["pending"] += 1
            elif status == "in_progress":
                stats["in_progress"] += 1

            # Count by priority
            priority = task.get("priority", "medium")
            stats["by_priority"][priority] += 1

            # Count by category
            category = task.get("category", "other")
            stats["by_category"][category] += 1

            # Check deadline
            deadline = task.get("deadline")
            if deadline and status != "completed":
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))

                # Overdue
                if deadline < now:
                    stats["overdue"] += 1

                # Due today
                if deadline.date() == now.date():
                    stats["due_today"] += 1

                # Due this week
                week_end = now + timedelta(days=7)
                if deadline <= week_end:
                    stats["due_this_week"] += 1

        # Calculate completion rate
        if len(tasks) > 0:
            stats["completion_rate"] = round((stats["completed"] / len(tasks)) * 100, 2)

        # Convert defaultdict to regular dict
        stats["by_status"] = dict(stats["by_status"])
        stats["by_priority"] = dict(stats["by_priority"])
        stats["by_category"] = dict(stats["by_category"])

        return stats

    def _calculate_budget_statistics(
        self,
        events: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate budget statistics.

        Args:
            events: List of events
            tasks: List of tasks

        Returns:
            Dictionary with budget statistics
        """
        total_budget_min = 0.0
        total_budget_max = 0.0
        total_cost_estimate = 0.0
        total_cost_actual = 0.0

        # Sum event budgets
        for event in events:
            budget_min = event.get("budget_min", 0)
            budget_max = event.get("budget_max", 0)

            total_budget_min += float(budget_min) if budget_min else 0
            total_budget_max += float(budget_max) if budget_max else 0

        # Sum task costs
        for task in tasks:
            cost_estimate = task.get("cost_estimate", 0)
            cost_actual = task.get("actual_cost", 0)

            total_cost_estimate += float(cost_estimate) if cost_estimate else 0
            total_cost_actual += float(cost_actual) if cost_actual else 0

        # Calculate averages
        num_events = len(events) if len(events) > 0 else 1

        return {
            "total_budget_min": round(total_budget_min, 2),
            "total_budget_max": round(total_budget_max, 2),
            "average_budget_per_event": round(total_budget_max / num_events, 2),
            "total_cost_estimate": round(total_cost_estimate, 2),
            "total_cost_actual": round(total_cost_actual, 2),
            "budget_utilization": round(
                (total_cost_actual / total_budget_max * 100) if total_budget_max > 0 else 0,
                2
            ),
            "cost_variance": round(total_cost_actual - total_cost_estimate, 2),
            "currency": "GHS"
        }

    def _calculate_timeline_statistics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate timeline statistics.

        Args:
            events: List of events

        Returns:
            Dictionary with timeline statistics
        """
        now = datetime.now(timezone.utc)
        upcoming_events = []

        for event in events:
            event_date = event.get("date")
            if event_date:
                if isinstance(event_date, str):
                    event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))

                if event_date >= now:
                    days_until = (event_date - now).days
                    upcoming_events.append({
                        "id": str(event["_id"]),
                        "name": event.get("name"),
                        "date": event_date.isoformat(),
                        "days_until": days_until
                    })

        # Sort by date
        upcoming_events.sort(key=lambda x: x["days_until"])

        # Get next event
        next_event = upcoming_events[0] if upcoming_events else None

        return {
            "next_event": next_event,
            "upcoming_count": len(upcoming_events),
            "upcoming_events": upcoming_events[:5]  # Top 5 upcoming
        }

    async def _calculate_activity_statistics(
        self,
        events: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate activity statistics.

        Args:
            events: List of events
            tasks: List of tasks

        Returns:
            Dictionary with activity statistics
        """
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Recent events
        recent_events = sum(
            1 for event in events
            if event.get("created_at") and
            event["created_at"] >= week_ago
        )

        # Recent tasks
        recent_tasks = sum(
            1 for task in tasks
            if task.get("created_at") and
            task["created_at"] >= week_ago
        )

        # Recently completed tasks
        recently_completed = sum(
            1 for task in tasks
            if task.get("completed_at") and
            task["completed_at"] >= week_ago
        )

        # Recently updated tasks
        recently_updated = sum(
            1 for task in tasks
            if task.get("updated_at") and
            task["updated_at"] >= week_ago
        )

        return {
            "events_created_this_week": recent_events,
            "tasks_created_this_week": recent_tasks,
            "tasks_completed_this_week": recently_completed,
            "tasks_updated_this_week": recently_updated,
            "total_activity_count": recent_events + recent_tasks + recently_completed
        }

    def _generate_summary(
        self,
        event_stats: Dict[str, Any],
        task_stats: Dict[str, Any],
        budget_stats: Dict[str, Any],
        timeline_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate summary insights.

        Args:
            event_stats: Event statistics
            task_stats: Task statistics
            budget_stats: Budget statistics
            timeline_stats: Timeline statistics

        Returns:
            Dictionary with summary insights
        """
        # Generate insights
        insights = []

        # Event insights
        if event_stats["upcoming"] > 0:
            insights.append(f"You have {event_stats['upcoming']} upcoming event(s)")

        if event_stats["active"] > 0:
            insights.append(f"{event_stats['active']} event(s) happening within 7 days")

        # Task insights
        if task_stats["overdue"] > 0:
            insights.append(f"⚠️ {task_stats['overdue']} overdue task(s) need attention")

        if task_stats["due_today"] > 0:
            insights.append(f"🎯 {task_stats['due_today']} task(s) due today")

        if task_stats["completion_rate"] >= 80:
            insights.append(f"✅ Great progress! {task_stats['completion_rate']}% tasks completed")
        elif task_stats["completion_rate"] < 50:
            insights.append(f"📊 {task_stats['completion_rate']}% completion rate - keep pushing!")

        # Budget insights
        if budget_stats["budget_utilization"] > 90:
            insights.append(f"💰 Budget utilization at {budget_stats['budget_utilization']}% - watch spending")

        # Timeline insights
        next_event = timeline_stats.get("next_event")
        if next_event and next_event["days_until"] <= 3:
            insights.append(f"🔥 Next event '{next_event['name']}' in {next_event['days_until']} days!")

        return {
            "insights": insights,
            "health_score": self._calculate_health_score(event_stats, task_stats, budget_stats),
            "priority_actions": self._get_priority_actions(task_stats, timeline_stats)
        }

    def _calculate_health_score(
        self,
        event_stats: Dict[str, Any],
        task_stats: Dict[str, Any],
        budget_stats: Dict[str, Any]
    ) -> int:
        """
        Calculate overall health score (0-100).

        Args:
            event_stats: Event statistics
            task_stats: Task statistics
            budget_stats: Budget statistics

        Returns:
            Health score (0-100)
        """
        score = 100

        # Deduct for overdue tasks
        if task_stats["overdue"] > 0:
            score -= min(task_stats["overdue"] * 5, 30)

        # Deduct for low completion rate
        if task_stats["completion_rate"] < 50:
            score -= 20
        elif task_stats["completion_rate"] < 70:
            score -= 10

        # Deduct for budget overrun
        if budget_stats["budget_utilization"] > 100:
            score -= 15
        elif budget_stats["budget_utilization"] > 90:
            score -= 5

        # Bonus for high completion rate
        if task_stats["completion_rate"] >= 90:
            score += 10

        return max(0, min(100, score))

    def _get_priority_actions(
        self,
        task_stats: Dict[str, Any],
        timeline_stats: Dict[str, Any]
    ) -> List[str]:
        """
        Get priority actions for the user.

        Args:
            task_stats: Task statistics
            timeline_stats: Timeline statistics

        Returns:
            List of priority action strings
        """
        actions = []

        # Overdue tasks
        if task_stats["overdue"] > 0:
            actions.append(f"Address {task_stats['overdue']} overdue task(s)")

        # Tasks due today
        if task_stats["due_today"] > 0:
            actions.append(f"Complete {task_stats['due_today']} task(s) due today")

        # High priority tasks
        high_priority = task_stats["by_priority"].get("critical", 0) + \
                       task_stats["by_priority"].get("high", 0)
        if high_priority > 0:
            actions.append(f"Focus on {high_priority} high-priority task(s)")

        # Upcoming event
        next_event = timeline_stats.get("next_event")
        if next_event and next_event["days_until"] <= 7:
            actions.append(f"Prepare for '{next_event['name']}' in {next_event['days_until']} days")

        return actions[:5]  # Top 5 actions

    def _generate_event_alerts(
        self,
        event: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        overdue_tasks: List[Dict[str, Any]],
        critical_tasks: List[Dict[str, Any]],
        days_until: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Generate alerts for an event.

        Args:
            event: Event data
            tasks: All tasks for the event
            overdue_tasks: Overdue tasks
            critical_tasks: Critical/high priority incomplete tasks
            days_until: Days until event

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # Overdue tasks alert
        if len(overdue_tasks) > 0:
            alerts.append({
                "type": "danger",
                "title": "Overdue Tasks",
                "message": f"{len(overdue_tasks)} task(s) are overdue",
                "action": "Review overdue tasks"
            })

        # Critical tasks alert
        if len(critical_tasks) > 0 and days_until and days_until <= 7:
            alerts.append({
                "type": "warning",
                "title": "Critical Tasks Pending",
                "message": f"{len(critical_tasks)} critical/high priority task(s) not completed with event in {days_until} days",
                "action": "Complete critical tasks"
            })

        # Event approaching alert
        if days_until and days_until <= 3:
            alerts.append({
                "type": "info",
                "title": "Event Approaching",
                "message": f"Event is in {days_until} days",
                "action": "Final preparations"
            })

        # No tasks alert
        if len(tasks) == 0:
            alerts.append({
                "type": "warning",
                "title": "No Tasks",
                "message": "No tasks created for this event",
                "action": "Create tasks"
            })

        return alerts

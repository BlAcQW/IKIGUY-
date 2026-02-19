"""
AI Task Generator Service for EventFlow.

Uses RAG service to generate intelligent tasks based on event type and details.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.rag import RAGService, KnowledgeDocument
from ..models.event import EventInDB
from ..models.task import Task, TaskInDB
from .rag_task_service import RAGTaskService

logger = logging.getLogger(__name__)


class AITaskGenerator:
    """
    AI-powered task generator using RAG service.

    Generates tasks for events based on:
    - Event type (conference, wedding, concert, etc.)
    - Number of guests
    - Budget constraints
    - Location
    - Best practices from knowledge base
    """

    def __init__(self, rag_service: Optional[RAGService] = None):
        """
        Initialize AI task generator.

        Args:
            rag_service: Optional RAG service instance (for testing/mocking)
        """
        self.rag_service = rag_service
        self.rag_task_service = None  # Lazy initialization to avoid blocking
        self.logger = logging.getLogger(__name__)

    async def initialize_rag(self, ai_provider: str = "gemini") -> bool:
        """
        Initialize RAG service if not already initialized.

        Args:
            ai_provider: AI provider to use (gemini, openai, anthropic)

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.rag_service:
            # Lazy initialization of RAG task service
            if not self.rag_task_service:
                self.rag_task_service = RAGTaskService()

            # Try to initialize RAG task service
            initialized = await self.rag_task_service.initialize(ai_provider=ai_provider)
            if initialized:
                self.logger.info(f"RAG service initialized with {ai_provider}")
                return True
            else:
                self.logger.warning("RAG service not initialized, using fallback templates")
                return False
        return True

    async def generate_tasks(
        self,
        event: EventInDB,
        use_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate tasks for an event.

        Args:
            event: Event to generate tasks for
            use_ai: Whether to use AI (RAG) or fallback to templates

        Returns:
            List of task dictionaries
        """
        if use_ai and self.rag_service:
            return await self._generate_with_rag(event)
        else:
            return self._generate_with_templates(event)

    async def _generate_with_rag(self, event: EventInDB) -> List[Dict[str, Any]]:
        """
        Generate tasks using RAG service.

        Args:
            event: Event to generate tasks for

        Returns:
            List of task dictionaries
        """
        try:
            # Lazy initialization of RAG task service
            if not self.rag_task_service:
                self.rag_task_service = RAGTaskService()

            # Try to use RAG task service
            if self.rag_task_service.initialized:
                tasks = await self.rag_task_service.generate_tasks_with_rag(event)
                if tasks:
                    self.logger.info(f"Generated {len(tasks)} tasks using RAG for event {event.id}")
                    return tasks

            # If RAG not available or no tasks generated, fall back to templates
            self.logger.info(f"RAG not available, using templates for event {event.id}")
            return self._generate_with_templates(event)

        except Exception as e:
            self.logger.error(f"RAG task generation failed: {e}")
            return self._generate_with_templates(event)

    def _generate_with_templates(self, event: EventInDB) -> List[Dict[str, Any]]:
        """
        Generate tasks using predefined templates.

        Fallback method when RAG is not available.

        Args:
            event: Event to generate tasks for

        Returns:
            List of task dictionaries
        """
        # Task templates by event type
        task_templates = {
            "conference": [
                {
                    "title": "Book venue",
                    "category": "venue",
                    "priority": "critical",
                    "days_before": 90,
                    "description": "Research and book a suitable conference venue with required capacity"
                },
                {
                    "title": "Arrange catering services",
                    "category": "catering",
                    "priority": "high",
                    "days_before": 60,
                    "description": "Book catering service for meals, refreshments, and coffee breaks"
                },
                {
                    "title": "Invite and confirm speakers",
                    "category": "protocol",
                    "priority": "critical",
                    "days_before": 75,
                    "description": "Reach out to potential speakers and confirm their participation"
                },
                {
                    "title": "Set up registration system",
                    "category": "tech",
                    "priority": "high",
                    "days_before": 45,
                    "description": "Create online registration and ticketing system"
                },
                {
                    "title": "Arrange transport and parking",
                    "category": "transport",
                    "priority": "medium",
                    "days_before": 30,
                    "description": "Coordinate transportation options and parking arrangements"
                },
                {
                    "title": "Setup audio-visual equipment",
                    "category": "tech",
                    "priority": "high",
                    "days_before": 15,
                    "description": "Test and configure projectors, microphones, and sound systems"
                },
            ],
            "wedding": [
                {
                    "title": "Book church/venue",
                    "category": "venue",
                    "priority": "critical",
                    "days_before": 180,
                    "description": "Reserve ceremony and reception venues"
                },
                {
                    "title": "Book caterer",
                    "category": "catering",
                    "priority": "critical",
                    "days_before": 120,
                    "description": "Select and book catering service for reception"
                },
                {
                    "title": "Arrange decorations",
                    "category": "decoration",
                    "priority": "high",
                    "days_before": 90,
                    "description": "Plan and order flowers, centerpieces, and decorations"
                },
                {
                    "title": "Book photographer/videographer",
                    "category": "media",
                    "priority": "critical",
                    "days_before": 150,
                    "description": "Hire professional photographer and videographer"
                },
                {
                    "title": "Send invitations",
                    "category": "protocol",
                    "priority": "high",
                    "days_before": 60,
                    "description": "Design, print, and send wedding invitations"
                },
                {
                    "title": "Arrange transport",
                    "category": "transport",
                    "priority": "medium",
                    "days_before": 45,
                    "description": "Book transportation for bridal party and guests"
                },
            ],
            "concert": [
                {
                    "title": "Book venue",
                    "category": "venue",
                    "priority": "critical",
                    "days_before": 120,
                    "description": "Reserve concert venue with adequate capacity and facilities"
                },
                {
                    "title": "Arrange sound system",
                    "category": "tech",
                    "priority": "critical",
                    "days_before": 60,
                    "description": "Book professional sound equipment and engineers"
                },
                {
                    "title": "Hire security personnel",
                    "category": "security",
                    "priority": "critical",
                    "days_before": 45,
                    "description": "Engage security services for crowd control and safety"
                },
                {
                    "title": "Set up ticketing system",
                    "category": "ticketing",
                    "priority": "high",
                    "days_before": 75,
                    "description": "Create online and offline ticket sales channels"
                },
                {
                    "title": "Arrange artist transport and accommodation",
                    "category": "transport",
                    "priority": "high",
                    "days_before": 30,
                    "description": "Book hotels and transportation for performers"
                },
                {
                    "title": "Stage and lighting setup",
                    "category": "tech",
                    "priority": "high",
                    "days_before": 20,
                    "description": "Design and install stage, lighting, and special effects"
                },
            ],
            "outreach": [
                {
                    "title": "Identify target location",
                    "category": "venue",
                    "priority": "critical",
                    "days_before": 60,
                    "description": "Scout and confirm outreach location"
                },
                {
                    "title": "Recruit volunteers",
                    "category": "protocol",
                    "priority": "critical",
                    "days_before": 45,
                    "description": "Mobilize and train volunteer team"
                },
                {
                    "title": "Arrange supplies and materials",
                    "category": "logistics",
                    "priority": "high",
                    "days_before": 30,
                    "description": "Procure food, clothes, medical supplies, or other materials"
                },
                {
                    "title": "Arrange transport",
                    "category": "transport",
                    "priority": "high",
                    "days_before": 20,
                    "description": "Book vehicles for volunteers and supplies"
                },
                {
                    "title": "Get necessary permits",
                    "category": "protocol",
                    "priority": "high",
                    "days_before": 40,
                    "description": "Obtain required permits and permissions from authorities"
                },
            ],
            "corporate": [
                {
                    "title": "Book venue and facilities",
                    "category": "venue",
                    "priority": "critical",
                    "days_before": 60,
                    "description": "Reserve corporate event space with necessary amenities"
                },
                {
                    "title": "Arrange catering",
                    "category": "catering",
                    "priority": "high",
                    "days_before": 45,
                    "description": "Book professional catering service"
                },
                {
                    "title": "Setup presentation equipment",
                    "category": "tech",
                    "priority": "high",
                    "days_before": 20,
                    "description": "Configure projectors, screens, and conferencing tools"
                },
                {
                    "title": "Send invitations to stakeholders",
                    "category": "protocol",
                    "priority": "high",
                    "days_before": 40,
                    "description": "Distribute formal invitations to attendees"
                },
                {
                    "title": "Arrange team-building activities",
                    "category": "logistics",
                    "priority": "medium",
                    "days_before": 30,
                    "description": "Plan interactive sessions and activities"
                },
            ],
        }

        # Get templates for event type (default to conference)
        templates = task_templates.get(event.type, task_templates["conference"])

        # Generate tasks with calculated deadlines
        tasks = []
        for template in templates:
            # Calculate deadline based on event date
            days_before = template["days_before"]
            deadline = event.date - timedelta(days=days_before)

            # Only include tasks with future deadlines
            if deadline > datetime.utcnow():
                task_dict = {
                    "title": template["title"],
                    "description": template["description"],
                    "category": template["category"],
                    "priority": template["priority"],
                    "deadline": deadline,
                    "status": "pending",
                }
                tasks.append(task_dict)

        self.logger.info(f"Generated {len(tasks)} tasks for {event.type} event using templates")
        return tasks

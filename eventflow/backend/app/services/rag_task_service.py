"""
RAG-based Task Generation Service for EventFlow.

Integrates with shared RAG service to generate intelligent,
context-aware tasks based on event planning best practices.
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument, QueryResult
from ..models.event import EventInDB

logger = logging.getLogger(__name__)


class RAGTaskService:
    """
    RAG-based task generation service.

    Uses RAG (Retrieval-Augmented Generation) to generate intelligent
    tasks based on event planning best practices stored in a knowledge base.
    """

    def __init__(self):
        """Initialize RAG task service."""
        self.rag_service: Optional[RAGService] = None
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    async def initialize(
        self,
        ai_provider: str = "gemini",
        collection_name: str = "event_planning_templates"
    ) -> bool:
        """
        Initialize RAG service with AI provider.

        Args:
            ai_provider: AI provider to use (gemini, openai, anthropic)
            collection_name: Name of knowledge base collection

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # TODO: Initialize RAG service with proper config
            # This requires:
            # 1. PostgreSQL with pgvector extension
            # 2. AI API keys (OPENAI_API_KEY, GOOGLE_API_KEY, or ANTHROPIC_API_KEY)
            # 3. Knowledge base populated with event planning templates

            # For now, log that we're attempting initialization
            self.logger.info(f"Attempting to initialize RAG service with {ai_provider}")

            # Get API key based on provider
            if ai_provider == "gemini":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    self.logger.warning("GOOGLE_API_KEY not found, RAG service unavailable")
                    return False
            elif ai_provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    self.logger.warning("OPENAI_API_KEY not found, RAG service unavailable")
                    return False
            elif ai_provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    self.logger.warning("ANTHROPIC_API_KEY not found, RAG service unavailable")
                    return False
            else:
                self.logger.warning(f"Unknown AI provider: {ai_provider}")
                return False

            # Check PostgreSQL connection
            postgres_host = os.getenv("POSTGRES_SERVER", os.getenv("POSTGRES_HOST", "localhost"))
            if not postgres_host:
                self.logger.warning("POSTGRES_SERVER/POSTGRES_HOST not found, RAG service unavailable")
                return False

            # Initialize RAG service with configuration
            rag_config = RAGConfig(
                postgres_host=postgres_host,
                postgres_port=os.getenv("POSTGRES_PORT", "5432"),
                postgres_user=os.getenv("POSTGRES_USER", "postgres"),
                postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
                postgres_db=os.getenv("POSTGRES_DB_CORE", "kasaai_core"),
                ai_provider=ai_provider,
                api_key=api_key,
                embedding_model="text-embedding-3-small" if ai_provider == "openai" else "models/embedding-001",
                llm_model="gpt-4o-mini" if ai_provider == "openai" else "claude-3-haiku-20240307"
            )

            self.rag_service = RAGService(rag_config)
            self.initialized = True

            self.logger.info(f"✅ RAG service initialized successfully with {ai_provider}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize RAG service: {e}")
            return False

    async def generate_tasks_with_rag(
        self,
        event: EventInDB,
        max_tasks: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate tasks using RAG service.

        Queries the knowledge base for event planning best practices
        and generates contextual tasks.

        Args:
            event: Event to generate tasks for
            max_tasks: Maximum number of tasks to generate

        Returns:
            List of task dictionaries
        """
        if not self.initialized or not self.rag_service:
            self.logger.warning("RAG service not initialized, cannot generate tasks")
            return []

        try:
            # Build context for RAG query
            days_until_event = (event.date - datetime.utcnow()).days

            # Create detailed query for the AI
            query = self._build_task_generation_query(event, days_until_event)

            # Query RAG service
            result = await self.rag_service.query_knowledge_base(
                collection_name="event_planning_templates",
                query=query,
                context={
                    "event_type": event.type,
                    "num_guests": event.num_guests,
                    "location": event.location,
                    "budget_min": float(event.budget_min) if event.budget_min else 0,
                    "budget_max": float(event.budget_max) if event.budget_max else 0,
                    "days_until_event": days_until_event,
                    "date": event.date.isoformat(),
                }
            )

            # Parse AI response into structured tasks
            tasks = self._parse_rag_response(result, event)

            self.logger.info(f"Generated {len(tasks)} tasks using RAG for {event.type} event")
            return tasks[:max_tasks]

        except Exception as e:
            self.logger.error(f"RAG task generation failed: {e}")
            return []

    def _build_task_generation_query(self, event: EventInDB, days_until: int) -> str:
        """
        Build a comprehensive query for task generation.

        Args:
            event: Event details
            days_until: Days until event

        Returns:
            Query string for RAG
        """
        query = f"""
        Generate a comprehensive task list for planning a {event.type} event with these details:

        Event Details:
        - Type: {event.type}
        - Name: {event.name}
        - Expected Guests: {event.num_guests}
        - Location: {event.location}
        - Date: {event.date.strftime('%Y-%m-%d')} ({days_until} days from now)
        - Budget: {event.budget_min or 0} to {event.budget_max or 'unlimited'}

        Requirements:
        1. Provide tasks in order of priority (critical tasks first)
        2. Each task should include:
           - Clear, actionable title
           - Brief description (1-2 sentences)
           - Category (venue, catering, transport, protocol, tech, security, decoration, media, logistics, marketing)
           - Priority (critical, high, medium, low)
           - Recommended days before event to complete
           - Estimated cost range (if applicable)

        3. Consider:
           - Best practices for {event.type} events
           - Scale of event ({event.num_guests} guests)
           - Budget constraints
           - Timeline ({days_until} days available)
           - Local context ({event.location})

        4. Include both essential tasks (venue, catering) and important details (signage, parking, etc.)

        5. Ensure tasks are realistic and achievable within the timeline

        Format the response as a structured list with clear task details.
        """
        return query

    def _parse_rag_response(
        self,
        result: QueryResult,
        event: EventInDB
    ) -> List[Dict[str, Any]]:
        """
        Parse RAG response into structured task list.

        Args:
            result: Query result from RAG service
            event: Event details

        Returns:
            List of task dictionaries
        """
        # TODO: Implement robust parsing of AI response
        # This would involve:
        # 1. Using regex or NLP to extract task details
        # 2. Validating task structure
        # 3. Calculating deadlines based on recommendations
        # 4. Assigning default values for missing fields

        # For now, return empty list
        # In production, you'd parse result.response or result.answer
        self.logger.info(f"Parsing RAG response: {result.confidence_score} confidence")

        tasks = []
        # Example parsing logic would go here
        # tasks = self._extract_tasks_from_text(result.answer, event)

        return tasks

    async def seed_knowledge_base(self) -> bool:
        """
        Seed the knowledge base with event planning templates.

        This should be run once during setup to populate the RAG
        knowledge base with event planning best practices.

        Returns:
            True if successful, False otherwise
        """
        if not self.initialized or not self.rag_service:
            self.logger.warning("RAG service not initialized, cannot seed knowledge base")
            return False

        try:
            # Event planning best practices documents
            documents = [
                KnowledgeDocument(
                    title="Conference Planning Best Practices",
                    content="""
                    Key tasks for conference planning:
                    1. Book venue 3-6 months in advance (critical)
                    2. Secure keynote speakers 2-3 months before (critical)
                    3. Arrange catering 6-8 weeks before (high priority)
                    4. Setup registration system 6-8 weeks before (high priority)
                    5. Organize A/V equipment 3-4 weeks before (high priority)
                    6. Arrange accommodation for speakers 4-6 weeks before (medium)
                    7. Print materials (banners, programs) 2-3 weeks before (medium)
                    8. Test all tech equipment 1 week before (critical)
                    """,
                    category="event_planning",
                    tags=["conference", "corporate", "best-practices"],
                    metadata={"event_type": "conference", "source": "industry_standards"}
                ),
                KnowledgeDocument(
                    title="Wedding Planning Timeline",
                    content="""
                    Essential wedding planning tasks:
                    1. Book ceremony and reception venues 6-12 months before (critical)
                    2. Book photographer/videographer 6-9 months before (critical)
                    3. Book caterer 4-6 months before (critical)
                    4. Order wedding dress 4-6 months before (high priority)
                    5. Send save-the-dates 4-6 months before (high priority)
                    6. Book florist 3-4 months before (high priority)
                    7. Arrange transport 2-3 months before (medium)
                    8. Send invitations 6-8 weeks before (high priority)
                    9. Final venue walkthrough 2 weeks before (critical)
                    """,
                    category="event_planning",
                    tags=["wedding", "personal", "best-practices"],
                    metadata={"event_type": "wedding", "source": "wedding_industry"}
                ),
                KnowledgeDocument(
                    title="Concert/Festival Planning Guide",
                    content="""
                    Critical tasks for concert planning:
                    1. Book venue 4-6 months in advance (critical)
                    2. Book sound/lighting company 3-4 months before (critical)
                    3. Hire security services 2-3 months before (critical)
                    4. Setup ticketing system 3-4 months before (critical)
                    5. Book artist accommodation 2-3 months before (high priority)
                    6. Obtain necessary permits 6-8 weeks before (critical)
                    7. Arrange stage setup 4-6 weeks before (high priority)
                    8. Coordinate artist technical requirements 3-4 weeks before (high priority)
                    9. Setup emergency medical services 2-3 weeks before (critical)
                    """,
                    category="event_planning",
                    tags=["concert", "festival", "entertainment", "best-practices"],
                    metadata={"event_type": "concert", "source": "event_production"}
                ),
            ]

            # Add documents to knowledge base
            for doc in documents:
                await self.rag_service.add_document(
                    collection_name="event_planning_templates",
                    document=doc
                )

            self.logger.info(f"Seeded {len(documents)} documents to knowledge base")
            return True

        except Exception as e:
            self.logger.error(f"Failed to seed knowledge base: {e}")
            return False

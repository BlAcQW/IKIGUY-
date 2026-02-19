"""
LLM Service for EventFlow.

Provides intelligent features:
- Smart task recommendations based on event context
- Task status analysis and progress assessment
- Conversational AI (Ama personality)
- Risk detection and escalation reasoning
- Multi-language support (English, Twi, Ga, French)
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from apps.shared.services.llm_provider_service import (
    LLMProviderService,
    ChatRequest,
    ChatMessage
)

logger = logging.getLogger(__name__)


class EventFlowLLMService:
    """
    LLM service for EventFlow intelligent features.

    Handles:
    - Task recommendations based on event context
    - Conversational AI for Ama assistant
    - Smart suggestions for event planning
    - Risk detection and escalation reasoning
    """

    def __init__(self):
        """Initialize LLM service with shared LLMProviderService."""
        self.llm_provider = LLMProviderService(
            enable_billing=True,
            enable_health_monitoring=True
        )
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize LLM service.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            await self.llm_provider.initialize()
            self._initialized = True
            logger.info("EventFlowLLMService initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            return False

    async def generate_task_recommendations(
        self,
        event_type: str,
        event_name: str,
        days_until_event: int,
        current_tasks: List[Dict],
        user_id: str,
        language: str = "en",
        model_id: str = "llama_32_3b"
    ) -> Optional[Dict]:
        """
        Generate smart task recommendations for an event.

        Args:
            event_type: Event type (conference, wedding, concert, etc.)
            event_name: Event name
            days_until_event: Days until event
            current_tasks: List of current tasks with titles
            user_id: User ID for billing
            language: Language for recommendations (en, tw, ga, fr)
            model_id: LLM model to use

        Returns:
            Dict with recommended tasks and reasoning, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Build list of current task titles
            task_titles = [task.get("title", "") for task in current_tasks]

            # Build language-appropriate system prompt
            if language == "tw":  # Twi
                system_prompt = """Wo yɛ Ama, ɔboafoɔ a ɔboa wɔ dwumadie nhyehyɛeɛ ho wɔ EventFlow.
Wo adwuma ne sɛ wobɛma nyansa wɔ dwuma a ɛsɛ sɛ wɔyɛ ho."""
            elif language == "ga":  # Ga
                system_prompt = """Amɛ Ama lɛ, event planning assistant lɛ EventFlow mli.
Amɛ yɔɔ lɛ task recommendations ni event context lɛ."""
            elif language == "fr":  # French
                system_prompt = """Vous êtes Ama, assistante experte en planification d'événements pour EventFlow.
Votre rôle est de fournir des recommandations intelligentes de tâches basées sur le contexte de l'événement."""
            else:  # English (default)
                system_prompt = """You are Ama, an expert event planning assistant for EventFlow.
Your role is to provide intelligent task recommendations based on event context.
Always respond with practical, actionable tasks."""

            user_prompt = f"""
Event Type: {event_type}
Event Name: {event_name}
Days Until Event: {days_until_event}

Current Tasks:
{', '.join(task_titles) if task_titles else 'No tasks created yet'}

Based on this information, suggest 5 additional critical tasks that are missing.
For each task, provide:
1. Task title
2. Priority (critical, high, medium, low)
3. Recommended deadline (days before event)
4. Category (venue, catering, tech, transport, logistics, marketing, etc.)
5. Brief reasoning (1-2 sentences)

Format your response as JSON with this structure:
{{
  "recommendations": [
    {{
      "title": "Task title",
      "priority": "high",
      "deadline_days_before": 7,
      "category": "venue",
      "reasoning": "Explanation why this task is important"
    }}
  ]
}}
"""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]

            # Create chat request
            chat_request = ChatRequest(
                model_id=model_id,
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                response_format="json"
            )

            # Get recommendations from LLM
            result = await self.llm_provider.chat(
                user_id=user_id,
                request=chat_request
            )

            logger.info(
                f"Generated {event_type} task recommendations: "
                f"{len(json.loads(result.content).get('recommendations', []))} tasks"
            )

            return {
                "recommendations": result.content,
                "model_used": result.model,
                "cost": result.cost,
                "tokens": {
                    "input": result.input_tokens,
                    "output": result.output_tokens,
                    "total": result.total_tokens
                },
                "language": language
            }

        except Exception as e:
            logger.error(f"Failed to generate task recommendations: {e}")
            return None

    async def analyze_task_status(
        self,
        task_title: str,
        task_notes: List[str],
        days_until_deadline: int,
        user_id: str,
        current_status: str = "in_progress",
        model_id: str = "llama_32_3b"
    ) -> Optional[Dict]:
        """
        Analyze task status and provide insights.

        Args:
            task_title: Task title
            task_notes: List of task update notes
            days_until_deadline: Days until task deadline
            user_id: User ID for billing
            current_status: Current task status
            model_id: LLM model to use

        Returns:
            Dict with analysis, risk assessment, and recommendations, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            system_prompt = """You are Ama, an event planning assistant.
Analyze task progress and provide actionable insights.
Be realistic about risks and provide practical next steps."""

            # Format recent notes
            recent_notes = task_notes[-5:] if task_notes else ["No updates yet"]

            user_prompt = f"""
Task: {task_title}
Current Status: {current_status}
Days Until Deadline: {days_until_deadline}

Recent Updates:
{chr(10).join(f"- {note}" for note in recent_notes)}

Analyze the task status and provide:
1. Current progress assessment (0-100%)
2. Risk level (low, medium, high, critical)
3. Top 3 recommended next steps
4. Whether escalation is needed (yes/no)
5. Brief reasoning for your assessment

Format response as JSON:
{{
  "progress_percentage": 50,
  "risk_level": "medium",
  "next_steps": ["Step 1", "Step 2", "Step 3"],
  "escalation_needed": false,
  "reasoning": "Brief explanation of your assessment"
}}
"""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]

            chat_request = ChatRequest(
                model_id=model_id,
                messages=messages,
                temperature=0.5,
                max_tokens=800,
                response_format="json"
            )

            result = await self.llm_provider.chat(
                user_id=user_id,
                request=chat_request
            )

            logger.info(
                f"Analyzed task '{task_title[:30]}...': "
                f"{json.loads(result.content).get('risk_level', 'unknown')} risk"
            )

            return {
                "analysis": result.content,
                "cost": result.cost,
                "tokens": {
                    "input": result.input_tokens,
                    "output": result.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze task status: {e}")
            return None

    async def generate_conversational_response(
        self,
        question: str,
        context: Dict,
        user_id: str,
        language: str = "en",
        personality: str = "friendly",
        model_id: str = "llama_32_3b"
    ) -> Optional[Dict]:
        """
        Generate conversational response from Ama assistant.

        Args:
            question: User's question
            context: Event/task context (event name, task list, etc.)
            user_id: User ID for billing
            language: Response language (en, tw, ga, fr)
            personality: Ama's personality (friendly, professional, casual)
            model_id: LLM model to use

        Returns:
            Dict with conversational response, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Build personality-appropriate system prompt
            personality_traits = {
                "friendly": "warm, encouraging, and supportive",
                "professional": "formal, precise, and business-like",
                "casual": "relaxed, informal, and conversational"
            }

            trait = personality_traits.get(personality, "friendly")

            system_prompt = f"""You are Ama, an event planning assistant for EventFlow.
Your personality is {trait}.
You help event organizers manage their events and tasks effectively.
Always provide helpful, actionable advice."""

            # Build context string
            context_str = ""
            if context.get("event_name"):
                context_str += f"Event: {context['event_name']}\n"
            if context.get("event_type"):
                context_str += f"Type: {context['event_type']}\n"
            if context.get("task_count"):
                context_str += f"Total Tasks: {context['task_count']}\n"
            if context.get("pending_tasks"):
                context_str += f"Pending Tasks: {context['pending_tasks']}\n"

            user_prompt = f"""
{context_str}

User Question: {question}

Please provide a helpful response. If the user is asking about task status, provide specific information.
If asking for advice, give practical recommendations.
Keep your response concise (2-3 sentences).
"""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]

            chat_request = ChatRequest(
                model_id=model_id,
                messages=messages,
                temperature=0.8,
                max_tokens=300
            )

            result = await self.llm_provider.chat(
                user_id=user_id,
                request=chat_request
            )

            logger.info(f"Generated conversational response in {language} ({personality})")

            return {
                "response": result.content,
                "cost": result.cost,
                "tokens": {
                    "input": result.input_tokens,
                    "output": result.output_tokens
                },
                "language": language,
                "personality": personality
            }

        except Exception as e:
            logger.error(f"Failed to generate conversational response: {e}")
            return None

    async def detect_risks_and_suggest_escalation(
        self,
        event_name: str,
        overdue_tasks: List[Dict],
        blocked_tasks: List[Dict],
        user_id: str,
        model_id: str = "llama_32_3b"
    ) -> Optional[Dict]:
        """
        Detect event risks and suggest escalation strategies.

        Args:
            event_name: Event name
            overdue_tasks: List of overdue tasks
            blocked_tasks: List of blocked tasks
            user_id: User ID for billing
            model_id: LLM model to use

        Returns:
            Dict with risk assessment and escalation suggestions, or None if failed
        """
        if not self._initialized:
            await self.initialize()

        try:
            system_prompt = """You are Ama, an event planning expert.
Analyze event risks and provide strategic escalation recommendations.
Focus on critical blockers that could derail the event."""

            # Format task lists
            overdue_str = "\n".join(
                f"- {task.get('title', 'Unknown')} (overdue by {task.get('days_overdue', 0)} days)"
                for task in overdue_tasks[:10]
            ) if overdue_tasks else "None"

            blocked_str = "\n".join(
                f"- {task.get('title', 'Unknown')} (blocked: {task.get('blocker', 'Unknown')})"
                for task in blocked_tasks[:10]
            ) if blocked_tasks else "None"

            user_prompt = f"""
Event: {event_name}

Overdue Tasks ({len(overdue_tasks)}):
{overdue_str}

Blocked Tasks ({len(blocked_tasks)}):
{blocked_str}

Analyze the risk level for this event and provide:
1. Overall risk level (low, medium, high, critical)
2. Top 3 risk factors
3. Recommended escalation actions
4. Suggested communication to stakeholders

Format as JSON:
{{
  "risk_level": "high",
  "risk_factors": ["Factor 1", "Factor 2", "Factor 3"],
  "escalation_actions": ["Action 1", "Action 2", "Action 3"],
  "stakeholder_message": "Brief message to send to event organizer"
}}
"""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]

            chat_request = ChatRequest(
                model_id=model_id,
                messages=messages,
                temperature=0.4,  # Lower temperature for risk assessment
                max_tokens=1000,
                response_format="json"
            )

            result = await self.llm_provider.chat(
                user_id=user_id,
                request=chat_request
            )

            logger.info(
                f"Risk assessment for '{event_name}': "
                f"{json.loads(result.content).get('risk_level', 'unknown')}"
            )

            return {
                "risk_assessment": result.content,
                "cost": result.cost,
                "tokens": {
                    "input": result.input_tokens,
                    "output": result.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Failed to detect risks: {e}")
            return None

    async def get_available_models(self) -> Dict:
        """
        Get available LLM models.

        Returns:
            Dict with available models and their capabilities
        """
        if not self._initialized:
            await self.initialize()

        try:
            models = await self.llm_provider.get_available_models()
            return models
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return {"success": False, "error": str(e)}

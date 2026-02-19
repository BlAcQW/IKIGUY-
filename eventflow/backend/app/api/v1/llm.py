"""
LLM (Language Model) API routes for EventFlow.

Provides endpoints for:
- Task recommendations
- Task status analysis
- Conversational AI (Ama assistant)
- Risk detection and escalation
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List, Dict
from datetime import datetime

from ...services.llm_service import EventFlowLLMService
from ...api.dependencies import get_current_user
from ...core.database import get_database

router = APIRouter(prefix="/llm", tags=["AI Intelligence"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TaskRecommendationRequest(BaseModel):
    """Request for task recommendations."""
    event_type: str = Field(..., description="Event type (conference, wedding, etc.)")
    language: str = Field(default="en", description="Language for recommendations")
    model_id: str = Field(default="llama_32_3b", description="LLM model to use")


class TaskRecommendationResponse(BaseModel):
    """Response with task recommendations."""
    recommendations: str = Field(..., description="JSON string with recommended tasks")
    model_used: str = Field(..., description="Model used for generation")
    cost: float = Field(..., description="Cost in USD")
    tokens: Dict = Field(..., description="Token usage statistics")
    language: str = Field(..., description="Response language")


class TaskAnalysisRequest(BaseModel):
    """Request for task analysis."""
    model_id: str = Field(default="llama_32_3b", description="LLM model to use")


class TaskAnalysisResponse(BaseModel):
    """Response with task analysis."""
    analysis: str = Field(..., description="JSON string with analysis results")
    cost: float = Field(..., description="Cost in USD")
    tokens: Dict = Field(..., description="Token usage statistics")


class ConversationalRequest(BaseModel):
    """Request for conversational response."""
    question: str = Field(..., description="User's question")
    event_id: Optional[str] = Field(None, description="Event context (optional)")
    language: str = Field(default="en", description="Response language")
    personality: str = Field(default="friendly", description="Ama's personality")
    model_id: str = Field(default="llama_32_3b", description="LLM model to use")


class ConversationalResponse(BaseModel):
    """Response from Ama assistant."""
    response: str = Field(..., description="Ama's response")
    cost: float = Field(..., description="Cost in USD")
    tokens: Dict = Field(..., description="Token usage statistics")
    language: str = Field(..., description="Response language")
    personality: str = Field(..., description="Personality used")


class RiskAssessmentRequest(BaseModel):
    """Request for event risk assessment."""
    model_id: str = Field(default="llama_32_3b", description="LLM model to use")


class RiskAssessmentResponse(BaseModel):
    """Response with risk assessment."""
    risk_assessment: str = Field(..., description="JSON string with risk analysis")
    cost: float = Field(..., description="Cost in USD")
    tokens: Dict = Field(..., description="Token usage statistics")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/events/{event_id}/task-recommendations", response_model=TaskRecommendationResponse)
async def get_task_recommendations(
    event_id: str,
    request: TaskRecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI-powered task recommendations for an event.

    **Usage:** Ama analyzes the event type and existing tasks to suggest missing critical tasks.

    **Example Response:**
    ```json
    {
        "recommendations": {
            "recommendations": [
                {
                    "title": "Book venue and confirm capacity",
                    "priority": "critical",
                    "deadline_days_before": 30,
                    "category": "venue",
                    "reasoning": "Venue booking is foundational and requires early confirmation"
                }
            ]
        },
        "model_used": "llama_32_3b",
        "cost": 0.002,
        "language": "en"
    }
    ```
    """
    db = await get_database()

    # Get event details
    try:
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "organizer_id": ObjectId(current_user.user_id)
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found or access denied"
        )

    # Get current tasks
    tasks = await db.tasks.find({"event_id": event_id}).to_list(None)

    # Calculate days until event
    event_date = event.get("date")
    if event_date:
        days_until = (event_date - datetime.utcnow()).days
    else:
        days_until = 30  # Default if no date set

    # Get recommendations
    llm_service = EventFlowLLMService()
    await llm_service.initialize()

    result = await llm_service.generate_task_recommendations(
        event_type=request.event_type or event.get("type", "conference"),
        event_name=event.get("name", "Event"),
        days_until_event=max(days_until, 1),
        current_tasks=tasks,
        user_id=current_user.user_id,
        language=request.language,
        model_id=request.model_id
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate task recommendations"
        )

    return TaskRecommendationResponse(**result)


@router.post("/tasks/{task_id}/analyze", response_model=TaskAnalysisResponse)
async def analyze_task_status(
    task_id: str,
    request: TaskAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze task status and get AI insights.

    **Usage:** Ama analyzes task progress, notes, and deadline to assess risk and suggest next steps.

    **Example Response:**
    ```json
    {
        "analysis": {
            "progress_percentage": 60,
            "risk_level": "medium",
            "next_steps": [
                "Confirm final headcount",
                "Finalize menu selection",
                "Send deposit payment"
            ],
            "escalation_needed": false,
            "reasoning": "Task is progressing but needs attention on specific items"
        },
        "cost": 0.001
    }
    ```
    """
    db = await get_database()

    # Get task details
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify user has access to task's event
    event = await db.events.find_one({
        "_id": task["event_id"],
        "organizer_id": ObjectId(current_user.user_id)
    })

    if not event:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this task"
        )

    # Extract task notes
    task_notes = [note.get("text", "") for note in task.get("notes", [])]

    # Calculate days until deadline
    deadline = task.get("deadline")
    if deadline:
        days_until = (deadline - datetime.utcnow()).days
    else:
        days_until = 7  # Default if no deadline

    # Analyze task
    llm_service = EventFlowLLMService()
    await llm_service.initialize()

    result = await llm_service.analyze_task_status(
        task_title=task.get("title", "Untitled Task"),
        task_notes=task_notes,
        days_until_deadline=days_until,
        user_id=current_user.user_id,
        current_status=task.get("status", "in_progress"),
        model_id=request.model_id
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze task status"
        )

    return TaskAnalysisResponse(**result)


@router.post("/ask-ama", response_model=ConversationalResponse)
async def ask_ama_assistant(
    request: ConversationalRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ask Ama a question about your events or tasks.

    **Usage:** Conversational AI for event planning questions.

    **Example Request:**
    ```json
    {
        "question": "What tasks are pending for the wedding?",
        "event_id": "event_123",
        "language": "en",
        "personality": "friendly"
    }
    ```

    **Example Response:**
    ```json
    {
        "response": "You have 3 pending tasks for the wedding: venue booking, catering menu selection, and invitation design. The venue booking is most urgent as it's due in 5 days.",
        "cost": 0.001,
        "language": "en",
        "personality": "friendly"
    }
    ```
    """
    db = await get_database()

    # Build context from event if provided
    context = {}

    if request.event_id:
        try:
            event = await db.events.find_one({
                "_id": ObjectId(request.event_id),
                "organizer_id": ObjectId(current_user.user_id)
            })
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid event ID")

        if event:
            # Get event context
            context["event_name"] = event.get("name")
            context["event_type"] = event.get("type")

            # Get task counts
            tasks = await db.tasks.find({"event_id": request.event_id}).to_list(None)
            context["task_count"] = len(tasks)
            context["pending_tasks"] = len([t for t in tasks if t.get("status") == "pending"])
            context["completed_tasks"] = len([t for t in tasks if t.get("status") == "completed"])

    # Get response from Ama
    llm_service = EventFlowLLMService()
    await llm_service.initialize()

    result = await llm_service.generate_conversational_response(
        question=request.question,
        context=context,
        user_id=current_user.user_id,
        language=request.language,
        personality=request.personality,
        model_id=request.model_id
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response from Ama"
        )

    return ConversationalResponse(**result)


@router.post("/events/{event_id}/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_event_risks(
    event_id: str,
    request: RiskAssessmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI-powered risk assessment for an event.

    **Usage:** Ama analyzes overdue and blocked tasks to assess event risk and suggest escalation.

    **Example Response:**
    ```json
    {
        "risk_assessment": {
            "risk_level": "high",
            "risk_factors": [
                "3 tasks overdue by 5+ days",
                "Critical venue task blocked",
                "Only 10 days until event"
            ],
            "escalation_actions": [
                "Call venue coordinator immediately",
                "Reassign catering task to backup person",
                "Schedule emergency team meeting"
            ],
            "stakeholder_message": "Event has high risk due to venue delays. Immediate action required on 3 critical tasks."
        },
        "cost": 0.002
    }
    ```
    """
    db = await get_database()

    # Verify event access
    try:
        event = await db.events.find_one({
            "_id": ObjectId(event_id),
            "organizer_id": ObjectId(current_user.user_id)
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found or access denied"
        )

    # Get all tasks
    tasks = await db.tasks.find({"event_id": event_id}).to_list(None)

    # Identify overdue and blocked tasks
    now = datetime.utcnow()
    overdue_tasks = []
    blocked_tasks = []

    for task in tasks:
        deadline = task.get("deadline")
        if deadline and deadline < now and task.get("status") != "completed":
            days_overdue = (now - deadline).days
            overdue_tasks.append({
                "title": task.get("title"),
                "days_overdue": days_overdue
            })

        if task.get("status") == "blocked":
            blocked_tasks.append({
                "title": task.get("title"),
                "blocker": task.get("blocker_reason", "Unknown")
            })

    # Get risk assessment
    llm_service = EventFlowLLMService()
    await llm_service.initialize()

    result = await llm_service.detect_risks_and_suggest_escalation(
        event_name=event.get("name", "Event"),
        overdue_tasks=overdue_tasks,
        blocked_tasks=blocked_tasks,
        user_id=current_user.user_id,
        model_id=request.model_id
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to assess event risks"
        )

    return RiskAssessmentResponse(**result)


@router.get("/models")
async def get_available_llm_models(
    current_user: dict = Depends(get_current_user)
):
    """
    Get available LLM models.

    **Returns:** List of available models and their capabilities

    **Example Response:**
    ```json
    {
        "models": {
            "llama_32_3b": {
                "name": "Llama 3.2 3B",
                "languages": ["en", "tw", "ga", "fr"],
                "capabilities": ["chat", "task_analysis", "recommendations"]
            }
        }
    }
    ```
    """
    llm_service = EventFlowLLMService()
    await llm_service.initialize()

    models = await llm_service.get_available_models()
    return models

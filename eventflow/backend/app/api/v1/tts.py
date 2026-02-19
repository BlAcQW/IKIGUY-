"""
TTS API routes for EventFlow.

Provides endpoints for:
- Voice preview
- Available voices and languages
- Task reminder generation
- Daily summary generation
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from ...services.tts_service import EventFlowTTSService
from ...api.dependencies import get_current_user
from ...core.database import get_database

router = APIRouter(prefix="/tts", tags=["Text-to-Speech"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TTSVoicePreview(BaseModel):
    """Request for TTS voice preview."""
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=500)
    language: str = Field(default="en", description="Language code (en, tw, ga, fr)")
    provider_id: str = Field(default="coqui_xtts", description="TTS provider ID")
    voice_id: Optional[str] = Field(default=None, description="Voice ID (optional)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed (0.5-2.0)")


class TaskReminderRequest(BaseModel):
    """Request for task reminder audio generation."""
    language: str = Field(default="en", description="Language code")
    provider_id: str = Field(default="coqui_xtts", description="TTS provider")
    voice_id: Optional[str] = Field(default=None, description="Voice ID (optional)")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")


class DailySummaryRequest(BaseModel):
    """Request for daily summary audio generation."""
    event_id: str = Field(..., description="Event ID")
    language: str = Field(default="en", description="Language code")
    provider_id: str = Field(default="coqui_xtts", description="TTS provider")
    voice_id: Optional[str] = Field(default=None, description="Voice ID (optional)")


class AudioResponse(BaseModel):
    """Response with generated audio."""
    audio_url: str = Field(..., description="URL to audio file")
    text: str = Field(..., description="Generated text")
    duration: float = Field(..., description="Audio duration in seconds")
    cost: float = Field(..., description="Generation cost in USD")
    provider_used: str = Field(..., description="TTS provider used")
    language: Optional[str] = Field(default=None, description="Language used")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/preview", response_model=AudioResponse)
async def preview_voice(
    request: TTSVoicePreview,
    current_user: dict = Depends(get_current_user)
):
    """
    Preview a TTS voice with sample text.

    **Purpose:** Allow users to test different voices before using them

    **Example:**
    ```json
    {
        "text": "Hello, this is a test of the voice system.",
        "language": "en",
        "provider_id": "coqui_xtts",
        "voice_id": "nova",
        "speed": 1.0
    }
    ```

    **Returns:** Audio file as base64 data URL for immediate playback
    """
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    # Use shared TTS service directly for preview
    from apps.shared.services.tts_provider_service import SynthesisRequest

    synthesis_request = SynthesisRequest(
        provider_id=request.provider_id,
        text=request.text,
        language=request.language,
        voice_id=request.voice_id,
        speed=request.speed,
        pitch=0.0,
        output_format="mp3"
    )

    try:
        result = await tts_service.tts_provider.synthesize(
            user_id=current_user.user_id,
            request=synthesis_request
        )

        # Return as base64 data URL for preview (no storage)
        return AudioResponse(
            audio_url=f"data:audio/mp3;base64,{result.audio_base64}",
            text=request.text,
            duration=result.duration,
            cost=result.cost,
            provider_used=result.provider_id,
            language=request.language
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get("/voices")
async def get_available_voices(
    provider_id: str = "coqui_xtts",
    current_user: dict = Depends(get_current_user)
):
    """
    Get available voices for a TTS provider.

    **Query Parameters:**
    - `provider_id`: TTS provider (default: coqui_xtts)

    **Returns:** List of available voices with metadata
    """
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    voices = await tts_service.get_available_voices(provider_id)
    return voices


@router.get("/languages")
async def get_supported_languages(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all supported languages across all TTS providers.

    **Returns:** Dict mapping providers to supported languages

    **Example Response:**
    ```json
    {
        "coqui_xtts": ["en", "es", "fr", "de", "it", "pt", "tw", "ga"],
        "melotts": ["en", "zh", "es", "fr", "ja", "ko"],
        "f5tts": ["en", "zh", "ja", "ko"]
    }
    ```
    """
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    languages = await tts_service.get_supported_languages()
    return languages


@router.get("/providers")
async def get_providers_status():
    """
    Get status of all TTS providers.

    **Returns:** Provider health status and capabilities

    **Note:** Public endpoint - no authentication required for listing providers
    """
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    status = await tts_service.get_providers_status()
    return status


@router.post("/tasks/{task_id}/reminder", response_model=AudioResponse)
async def generate_task_reminder_audio(
    task_id: str,
    request: TaskReminderRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate voice reminder audio for a task.

    **Purpose:** Create voice message to send to responsible person

    **Workflow:**
    1. Retrieves task details (title, deadline, assigned person)
    2. Generates personalized reminder in preferred language
    3. Synthesizes to audio
    4. Stores audio file
    5. Returns URL and metadata

    **Example:**
    ```json
    {
        "language": "en",
        "provider_id": "coqui_xtts",
        "speed": 1.0
    }
    ```

    **Returns:** Audio URL, text, duration, and cost
    """
    db = await get_database()

    # Get task details
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get event details
    event = await db.events.find_one({"_id": task["event_id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get responsible person
    person = await db.responsible_persons.find_one({"_id": task["assigned_to"]})
    if not person:
        raise HTTPException(status_code=404, detail="Responsible person not found")

    # Generate reminder
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    result = await tts_service.generate_task_reminder(
        task_title=task["title"],
        task_deadline=task["deadline"],
        responsible_person_name=person["name"],
        event_name=event["name"],
        user_id=current_user.user_id,
        language=request.language,
        provider_id=request.provider_id,
        voice_id=request.voice_id,
        speed=request.speed
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate task reminder audio"
        )

    return AudioResponse(**result)


@router.post("/events/{event_id}/daily-summary", response_model=AudioResponse)
async def generate_daily_summary_audio(
    event_id: str,
    request: DailySummaryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate voice daily summary for an event.

    **Purpose:** Create audio summary of event progress for organizer

    **Includes:**
    - Total tasks count
    - Completed tasks count
    - Overdue tasks count
    - High priority pending tasks

    **Example:**
    ```json
    {
        "event_id": "6543210abcdef",
        "language": "en",
        "provider_id": "coqui_xtts"
    }
    ```

    **Returns:** Audio URL with summary
    """
    db = await get_database()

    # Get event
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

    # Get task statistics
    tasks = await db.tasks.find({"event_id": ObjectId(event_id)}).to_list(None)

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
    overdue_tasks = sum(
        1 for t in tasks
        if t["deadline"] < datetime.utcnow() and t["status"] != "completed"
    )

    # Get high priority pending tasks
    high_priority_tasks = [
        t["title"] for t in tasks
        if t["priority"] in ["critical", "high"] and t["status"] != "completed"
    ]

    # Generate summary
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    result = await tts_service.generate_daily_summary(
        event_name=event["name"],
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        high_priority_tasks=high_priority_tasks,
        user_id=current_user.user_id,
        language=request.language,
        provider_id=request.provider_id,
        voice_id=request.voice_id
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate daily summary audio"
        )

    return AudioResponse(**result)


@router.post("/tasks/{task_id}/update-notification", response_model=AudioResponse)
async def generate_task_update_notification(
    task_id: str,
    update_text: str,
    language: str = "en",
    current_user: dict = Depends(get_current_user)
):
    """
    Generate voice notification for task update.

    **Purpose:** Notify organizer of task status change via audio

    **Query Parameters:**
    - `update_text`: The update message
    - `language`: Language code (default: en)

    **Returns:** Audio notification
    """
    db = await get_database()

    # Get task
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get event
    event = await db.events.find_one({"_id": task["event_id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get person who made update
    person = await db.responsible_persons.find_one({"_id": task["assigned_to"]})
    updated_by = person["name"] if person else "Someone"

    # Generate notification
    tts_service = EventFlowTTSService()
    await tts_service.initialize()

    result = await tts_service.generate_task_update_notification(
        task_title=task["title"],
        update_text=update_text,
        updated_by=updated_by,
        event_name=event["name"],
        user_id=current_user.user_id,
        language=language
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate update notification"
        )

    return AudioResponse(**result)

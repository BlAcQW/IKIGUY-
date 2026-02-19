"""
ASR (Automatic Speech Recognition) API routes for EventFlow.

Provides endpoints for:
- Voice task updates
- Voice notes
- Voice questions
- Call response transcription
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

from ...services.asr_service import EventFlowASRService
from ...api.dependencies import get_current_user
from ...core.database import get_database

router = APIRouter(prefix="/asr", tags=["Speech Recognition"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TranscriptionResponse(BaseModel):
    """Response with transcription result."""
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence (0.0-1.0)")
    language: str = Field(..., description="Detected or specified language")
    duration: float = Field(..., description="Audio duration in seconds")
    cost: float = Field(..., description="Transcription cost in USD")
    provider_used: str = Field(..., description="ASR provider used")


class VoiceNoteResponse(BaseModel):
    """Response with voice note details."""
    voice_note_id: str = Field(..., description="Created voice note ID")
    transcription: TranscriptionResponse = Field(..., description="Transcription result")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/tasks/{task_id}/voice-update", response_model=TranscriptionResponse)
async def transcribe_voice_task_update(
    task_id: str,
    audio_file: UploadFile = File(..., description="Audio file (mp3, wav, ogg, m4a)"),
    language: Optional[str] = Form(None, description="Language code (en, tw, ga, fr) or auto-detect"),
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe voice input for task status update.

    **Usage:** Mobile app users can record voice updates like:
    "I've completed the venue booking. The deposit is paid and we're confirmed for Saturday."

    The system will transcribe this and update the task notes.

    **Supported Audio Formats:**
    - MP3, WAV, OGG, M4A, FLAC

    **Max File Size:** 10MB

    **Returns:** Transcription with text, confidence, language, duration, cost
    """
    # Validate task exists
    db = await get_database()
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Read audio file
    audio_data = await audio_file.read()

    # Validate file size (max 10MB)
    if len(audio_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large (max 10MB)")

    # Transcribe
    asr_service = EventFlowASRService()
    await asr_service.initialize()

    result = await asr_service.transcribe_task_update(
        audio_data=audio_data,
        user_id=current_user.user_id,
        task_id=task_id,
        language=language
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Transcription failed. Please try again."
        )

    # Update task with transcribed note
    await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$push": {
                "notes": {
                    "text": result["text"],
                    "source": "voice_input",
                    "transcription_confidence": result["confidence"],
                    "transcription_language": result["language"],
                    "created_by": current_user.user_id,
                    "created_at": datetime.utcnow()
                }
            },
            "$set": {
                "last_updated_at": datetime.utcnow(),
                "last_updated_by": current_user.user_id
            }
        }
    )

    # Return transcription result
    return TranscriptionResponse(
        text=result["text"],
        confidence=result["confidence"],
        language=result["language"],
        duration=result["duration"],
        cost=result["cost"],
        provider_used=result["provider_used"]
    )


@router.post("/voice-notes", response_model=VoiceNoteResponse)
async def transcribe_voice_note(
    audio_file: UploadFile = File(..., description="Audio file"),
    event_id: Optional[str] = Form(None, description="Event ID (optional)"),
    task_id: Optional[str] = Form(None, description="Task ID (optional)"),
    language: Optional[str] = Form(None, description="Language code or auto-detect"),
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe voice note for event or task.

    **Usage:** Attach voice notes to events/tasks for later reference.

    **Example Use Cases:**
    - "Quick reminder: Need to confirm venue capacity tomorrow"
    - "Meeting notes: Caterer prefers Saturday delivery"
    - "Idea: Add a photo booth at the entrance"

    **Supports:** Any language (Whisper auto-detects 30+ languages)

    **Returns:** Voice note ID and transcription
    """
    # Validate at least one ID is provided
    if not event_id and not task_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide either event_id or task_id"
        )

    # Read audio
    audio_data = await audio_file.read()

    # Validate file size
    if len(audio_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Audio file too large (max 10MB)")

    # Transcribe
    asr_service = EventFlowASRService()
    await asr_service.initialize()

    result = await asr_service.transcribe_voice_note(
        audio_data=audio_data,
        user_id=current_user.user_id,
        event_id=event_id,
        task_id=task_id,
        language=language
    )

    if not result:
        raise HTTPException(status_code=500, detail="Transcription failed")

    # Store voice note in database
    db = await get_database()
    voice_note = {
        "text": result["text"],
        "confidence": result["confidence"],
        "language": result["language"],
        "duration": result["duration"],
        "cost": result["cost"],
        "provider_used": result["provider_used"],
        "event_id": event_id,
        "task_id": task_id,
        "created_by": current_user.user_id,
        "created_at": datetime.utcnow()
    }

    insert_result = await db.voice_notes.insert_one(voice_note)

    return VoiceNoteResponse(
        voice_note_id=str(insert_result.inserted_id),
        transcription=TranscriptionResponse(
            text=result["text"],
            confidence=result["confidence"],
            language=result["language"],
            duration=result["duration"],
            cost=result["cost"],
            provider_used=result["provider_used"]
        )
    )


@router.post("/voice-questions", response_model=TranscriptionResponse)
async def transcribe_voice_question(
    audio_file: UploadFile = File(..., description="Audio file"),
    context: str = Form(..., description="Context for the question"),
    language: Optional[str] = Form(None, description="Language code or auto-detect"),
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe voice question for AI assistant.

    **Usage:** Voice-based queries about events/tasks

    **Example Questions:**
    - "What tasks are overdue for the wedding?"
    - "How many people confirmed for the bus to Kumasi?"
    - "What's the budget status for Impact 2025?"

    **Flow:**
    1. Transcribe voice question
    2. Pass to LLM for intelligent response
    3. Return both transcription and answer

    **Returns:** Transcription (answer generation happens in separate endpoint)
    """
    # Read audio
    audio_data = await audio_file.read()

    # Validate file size
    if len(audio_data) > 5 * 1024 * 1024:  # Smaller limit for questions
        raise HTTPException(status_code=413, detail="Audio file too large (max 5MB)")

    # Transcribe
    asr_service = EventFlowASRService()
    await asr_service.initialize()

    result = await asr_service.transcribe_voice_question(
        audio_data=audio_data,
        user_id=current_user.user_id,
        context=context,
        language=language
    )

    if not result:
        raise HTTPException(status_code=500, detail="Transcription failed")

    return TranscriptionResponse(
        text=result["text"],
        confidence=result["confidence"],
        language=result["language"],
        duration=result["duration"],
        cost=result["cost"],
        provider_used=result["provider_used"]
    )


@router.post("/calls/{call_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_call_response(
    call_id: str,
    audio_file: UploadFile = File(..., description="Audio file from call"),
    task_id: str = Form(..., description="Task ID being discussed"),
    language: Optional[str] = Form(None, description="Language code or auto-detect"),
    current_user: dict = Depends(get_current_user)
):
    """
    Transcribe response from VAPI voice call.

    **Usage:** Internal endpoint for transcribing call recordings

    **Flow:**
    1. VAPI makes call to responsible person
    2. Person responds about task status
    3. VAPI sends audio to this endpoint
    4. System transcribes and updates task

    **Returns:** Transcription of call response
    """
    # Read audio
    audio_data = await audio_file.read()

    # Transcribe
    asr_service = EventFlowASRService()
    await asr_service.initialize()

    result = await asr_service.transcribe_call_response(
        audio_data=audio_data,
        user_id=current_user.user_id,
        call_id=call_id,
        task_id=task_id,
        language=language
    )

    if not result:
        raise HTTPException(status_code=500, detail="Transcription failed")

    # Store transcription in database
    db = await get_database()
    await db.call_transcriptions.insert_one({
        "call_id": call_id,
        "task_id": task_id,
        "text": result["text"],
        "confidence": result["confidence"],
        "language": result["language"],
        "duration": result["duration"],
        "created_at": datetime.utcnow()
    })

    return TranscriptionResponse(
        text=result["text"],
        confidence=result["confidence"],
        language=result["language"],
        duration=result["duration"],
        cost=result["cost"],
        provider_used=result["provider_used"]
    )


@router.get("/languages")
async def get_supported_asr_languages(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all supported languages for ASR.

    **Returns:** Dict mapping providers to supported languages

    **Example Response:**
    ```json
    {
        "whisper_large_v3": [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt",
            "tr", "pl", "ca", "nl", "ar", "sv", "it", "id", "hi",
            "fi", "vi", "he", "uk", "el", "ms", "cs", "ro", "da",
            "hu", "ta", "no", "tw"
        ]
    }
    ```

    **Note:** Whisper supports 30+ languages including Twi (tw)
    """
    asr_service = EventFlowASRService()
    await asr_service.initialize()

    languages = await asr_service.get_supported_languages()
    return languages


@router.get("/providers")
async def get_asr_providers_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of all ASR providers.

    **Returns:** Provider health status and capabilities

    **Example Response:**
    ```json
    {
        "providers": {
            "whisper_large_v3": {
                "status": "online",
                "languages": 30,
                "avg_latency_ms": 1200,
                "success_rate": 0.98
            }
        }
    }
    ```
    """
    asr_service = EventFlowASRService()
    await asr_service.initialize()

    status = await asr_service.get_providers_status()
    return status


@router.get("/voice-notes/{voice_note_id}")
async def get_voice_note(
    voice_note_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get voice note by ID.

    **Returns:** Voice note with transcription
    """
    db = await get_database()

    try:
        voice_note = await db.voice_notes.find_one({"_id": ObjectId(voice_note_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid voice note ID")

    if not voice_note:
        raise HTTPException(status_code=404, detail="Voice note not found")

    # Convert ObjectId to string
    voice_note["_id"] = str(voice_note["_id"])

    return voice_note


@router.get("/tasks/{task_id}/voice-notes")
async def get_task_voice_notes(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all voice notes for a task.

    **Returns:** List of voice notes with transcriptions
    """
    db = await get_database()

    # Verify task exists
    try:
        task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get voice notes
    voice_notes = await db.voice_notes.find({"task_id": task_id}).to_list(None)

    # Convert ObjectIds to strings
    for note in voice_notes:
        note["_id"] = str(note["_id"])

    return {
        "task_id": task_id,
        "voice_notes": voice_notes,
        "total": len(voice_notes)
    }


@router.get("/events/{event_id}/voice-notes")
async def get_event_voice_notes(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all voice notes for an event.

    **Returns:** List of voice notes with transcriptions
    """
    db = await get_database()

    # Verify event exists
    try:
        event = await db.events.find_one({"_id": ObjectId(event_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event ID")

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get voice notes
    voice_notes = await db.voice_notes.find({"event_id": event_id}).to_list(None)

    # Convert ObjectIds to strings
    for note in voice_notes:
        note["_id"] = str(note["_id"])

    return {
        "event_id": event_id,
        "voice_notes": voice_notes,
        "total": len(voice_notes)
    }


@router.delete("/voice-notes/{voice_note_id}")
async def delete_voice_note(
    voice_note_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a voice note.

    **Returns:** Success confirmation
    """
    db = await get_database()

    try:
        result = await db.voice_notes.delete_one({
            "_id": ObjectId(voice_note_id),
            "created_by": current_user.user_id  # Only creator can delete
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid voice note ID")

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Voice note not found or you don't have permission to delete it"
        )

    return {
        "success": True,
        "message": "Voice note deleted successfully"
    }

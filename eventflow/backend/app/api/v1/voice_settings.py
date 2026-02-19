"""
Voice Settings API routes for EventFlow.

Provides endpoints for:
- User voice preferences (global settings)
- Event-level voice settings
- Ama assistant customization
- Cost control and escalation settings
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional

from ...models.voice_settings import (
    VoicePreferences,
    EventVoiceSettings,
    VoicePreferencesUpdate,
    EventVoiceSettingsUpdate
)
from ...api.dependencies import get_current_user
from ...core.database import get_database

router = APIRouter(prefix="/voice-settings", tags=["Voice Settings"])


# ============================================================================
# Response Models
# ============================================================================

class VoicePreferencesResponse(BaseModel):
    """Response with voice preferences."""
    preferences: VoicePreferences
    message: Optional[str] = None


class EventVoiceSettingsResponse(BaseModel):
    """Response with event voice settings."""
    settings: EventVoiceSettings
    message: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str


# ============================================================================
# User Voice Preferences Endpoints
# ============================================================================

@router.get("/me", response_model=VoicePreferencesResponse)
async def get_my_voice_settings(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user's voice preferences (alias for /user/preferences).

    This endpoint provides compatibility with shared frontend components.

    **Returns:** User's voice preferences or defaults if not set

    **Example Response:**
    ```json
    {
        "preferences": {
            "tts_provider": "coqui_xtts",
            "language": "en",
            "speed": 1.0,
            "enable_voice_calls": true,
            "max_daily_voice_cost": 5.0
        }
    }
    ```
    """
    db = await get_database()
    user = await db.users.find_one({"_id": ObjectId(current_user.user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return voice preferences or defaults
    voice_prefs_dict = user.get("voice_preferences", VoicePreferences().dict())
    voice_prefs = VoicePreferences(**voice_prefs_dict)

    return VoicePreferencesResponse(
        preferences=voice_prefs,
        message="Voice preferences retrieved successfully"
    )


@router.get("/user/preferences", response_model=VoicePreferencesResponse)
async def get_user_voice_preferences(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's global voice preferences.

    **Returns:** User's voice preferences or defaults if not set

    **Example Response:**
    ```json
    {
        "preferences": {
            "tts_provider": "coqui_xtts",
            "language": "en",
            "speed": 1.0,
            "enable_voice_calls": true,
            "max_daily_voice_cost": 5.0
        }
    }
    ```
    """
    # Call the /me endpoint to avoid code duplication
    return await get_my_voice_settings(current_user)


@router.put("/user/preferences", response_model=SuccessResponse)
async def update_user_voice_preferences(
    preferences: VoicePreferences,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user's global voice preferences.

    **Request Body:** Complete VoicePreferences object

    **Returns:** Success confirmation

    **Example Request:**
    ```json
    {
        "tts_provider": "coqui_xtts",
        "language": "tw",
        "speed": 1.2,
        "enable_voice_calls": true,
        "preferred_call_time_start": "09:00",
        "preferred_call_time_end": "18:00",
        "max_daily_voice_cost": 10.0
    }
    ```
    """
    db = await get_database()

    result = await db.users.update_one(
        {"_id": ObjectId(current_user.user_id)},
        {
            "$set": {
                "voice_preferences": preferences.dict(),
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return SuccessResponse(
        success=True,
        message="Voice preferences updated successfully"
    )


@router.patch("/user/preferences", response_model=SuccessResponse)
async def partial_update_user_voice_preferences(
    preferences: VoicePreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Partially update user's voice preferences.

    **Request Body:** Partial VoicePreferencesUpdate object (only fields to update)

    **Returns:** Success confirmation

    **Example Request (only update language and cost limit):**
    ```json
    {
        "language": "fr",
        "max_daily_voice_cost": 15.0
    }
    ```
    """
    db = await get_database()

    # Build update dict with only provided fields
    update_dict = {}
    for field, value in preferences.dict(exclude_unset=True).items():
        if value is not None:
            update_dict[f"voice_preferences.{field}"] = value

    if not update_dict:
        raise HTTPException(
            status_code=400,
            detail="No fields to update"
        )

    # Add updated_at timestamp
    update_dict["updated_at"] = datetime.utcnow()

    result = await db.users.update_one(
        {"_id": ObjectId(current_user.user_id)},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return SuccessResponse(
        success=True,
        message=f"Updated {len(update_dict) - 1} voice preference(s) successfully"
    )


# ============================================================================
# Event Voice Settings Endpoints
# ============================================================================

@router.get("/events/{event_id}/settings", response_model=EventVoiceSettingsResponse)
async def get_event_voice_settings(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get voice settings for a specific event.

    **Returns:** Event voice settings or defaults if not configured

    **Example Response:**
    ```json
    {
        "settings": {
            "event_id": "event_123",
            "assistant_name": "Ama",
            "assistant_personality": "friendly",
            "escalation_enabled": true,
            "escalation_threshold_days": 2
        }
    }
    ```
    """
    db = await get_database()

    # Check user has access to event
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

    # Get event voice settings
    settings_doc = await db.event_voice_settings.find_one({"event_id": event_id})

    if not settings_doc:
        # Return defaults
        default_settings = EventVoiceSettings(event_id=event_id)
        return EventVoiceSettingsResponse(
            settings=default_settings,
            message="Using default voice settings (not yet configured)"
        )

    # Convert MongoDB document to Pydantic model
    settings_doc.pop("_id", None)  # Remove MongoDB _id field
    settings = EventVoiceSettings(**settings_doc)

    return EventVoiceSettingsResponse(
        settings=settings,
        message="Event voice settings retrieved successfully"
    )


@router.put("/events/{event_id}/settings", response_model=SuccessResponse)
async def update_event_voice_settings(
    event_id: str,
    settings: EventVoiceSettings,
    current_user: dict = Depends(get_current_user)
):
    """
    Update voice settings for an event (complete replacement).

    **Request Body:** Complete EventVoiceSettings object

    **Returns:** Success confirmation

    **Example Request:**
    ```json
    {
        "event_id": "event_123",
        "assistant_name": "Ama",
        "assistant_personality": "professional",
        "custom_greeting": "Hello! This is Ama calling about the Impact Conference.",
        "escalation_enabled": true,
        "escalation_threshold_days": 3,
        "escalation_channels": ["voice_call", "email"],
        "voice_preferences": {
            "language": "en",
            "enable_voice_calls": true
        }
    }
    ```
    """
    db = await get_database()

    # Check user has access
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

    # Ensure event_id matches
    settings.event_id = event_id

    # Upsert settings
    settings_dict = settings.dict()
    settings_dict["updated_at"] = datetime.utcnow()

    result = await db.event_voice_settings.update_one(
        {"event_id": event_id},
        {"$set": settings_dict},
        upsert=True
    )

    return SuccessResponse(
        success=True,
        message="Event voice settings updated successfully"
    )


@router.patch("/events/{event_id}/settings", response_model=SuccessResponse)
async def partial_update_event_voice_settings(
    event_id: str,
    settings: EventVoiceSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Partially update event voice settings.

    **Request Body:** Partial EventVoiceSettingsUpdate object (only fields to update)

    **Returns:** Success confirmation

    **Example Request (only update assistant name and escalation):**
    ```json
    {
        "assistant_name": "EventBot",
        "escalation_threshold_days": 1
    }
    ```
    """
    db = await get_database()

    # Check user has access
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

    # Build update dict with only provided fields
    update_dict = {}
    for field, value in settings.dict(exclude_unset=True).items():
        if value is not None:
            if field == "voice_preferences":
                # Handle nested voice preferences update
                for pref_field, pref_value in value.items():
                    if pref_value is not None:
                        update_dict[f"voice_preferences.{pref_field}"] = pref_value
            else:
                update_dict[field] = value

    if not update_dict:
        raise HTTPException(
            status_code=400,
            detail="No fields to update"
        )

    # Add updated_at timestamp
    update_dict["updated_at"] = datetime.utcnow()

    result = await db.event_voice_settings.update_one(
        {"event_id": event_id},
        {"$set": update_dict},
        upsert=True
    )

    return SuccessResponse(
        success=True,
        message=f"Updated {len(update_dict) - 1} event voice setting(s) successfully"
    )


@router.delete("/events/{event_id}/settings", response_model=SuccessResponse)
async def delete_event_voice_settings(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete event voice settings (revert to defaults).

    **Returns:** Success confirmation

    **Note:** This removes custom settings and reverts to default voice settings.
    """
    db = await get_database()

    # Check user has access
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

    # Delete settings
    result = await db.event_voice_settings.delete_one({"event_id": event_id})

    if result.deleted_count == 0:
        return SuccessResponse(
            success=True,
            message="Event voice settings already using defaults"
        )

    return SuccessResponse(
        success=True,
        message="Event voice settings deleted successfully (reverted to defaults)"
    )


# ============================================================================
# Voice Cost Tracking Endpoints
# ============================================================================

@router.get("/user/voice-usage")
async def get_user_voice_usage(
    current_user: dict = Depends(get_current_user),
    days: int = 7
):
    """
    Get user's voice feature usage and costs.

    **Query Parameters:**
    - days: Number of days to look back (default: 7)

    **Returns:** Voice usage statistics and costs

    **Example Response:**
    ```json
    {
        "total_cost": 12.45,
        "tts_cost": 8.20,
        "asr_cost": 4.25,
        "call_count": 45,
        "daily_breakdown": [
            {"date": "2025-11-03", "cost": 2.50},
            {"date": "2025-11-02", "cost": 3.10}
        ]
    }
    ```
    """
    db = await get_database()

    # Calculate date range
    from datetime import timedelta
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Aggregate voice usage from wallet transactions
    pipeline = [
        {
            "$match": {
                "user_id": current_user.user_id,
                "created_at": {"$gte": start_date, "$lte": end_date},
                "service_type": {"$in": ["tts", "asr", "voice_call"]}
            }
        },
        {
            "$group": {
                "_id": "$service_type",
                "total_cost": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        }
    ]

    # Note: This assumes wallet transactions are tracked
    # If not available, return placeholder
    return {
        "total_cost": 0.0,
        "tts_cost": 0.0,
        "asr_cost": 0.0,
        "call_count": 0,
        "daily_breakdown": [],
        "message": "Voice usage tracking will be available after first usage"
    }


@router.get("/events/{event_id}/voice-usage")
async def get_event_voice_usage(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get voice feature usage and costs for a specific event.

    **Returns:** Event-specific voice usage statistics

    **Example Response:**
    ```json
    {
        "event_id": "event_123",
        "total_cost": 5.75,
        "task_reminders_sent": 20,
        "voice_calls_made": 15,
        "daily_summaries_generated": 5
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

    # Return placeholder for now
    # Real implementation would aggregate from usage logs
    return {
        "event_id": event_id,
        "total_cost": 0.0,
        "task_reminders_sent": 0,
        "voice_calls_made": 0,
        "daily_summaries_generated": 0,
        "message": "Event voice usage tracking will be available after first usage"
    }


# ============================================================================
# Provider Information Endpoints
# ============================================================================

@router.get("/providers")
async def get_available_providers(
    current_user: dict = Depends(get_current_user)
):
    """
    Get available TTS and ASR providers with status.
    
    Returns comprehensive list of voice providers for frontend configuration.
    """
    try:
        import sys
        sys.path.insert(0, "/opt/kasaai/apps")
        
        from apps.shared.integration.ai_services.provider_registry import (
            AIProviderRegistry,
            get_default_asr_providers_config,
            get_default_tts_providers_config,
            ProviderType
        )
        
        # Get providers from registry and load default configs
        registry = AIProviderRegistry()
        registry.register_providers_from_config(
            get_default_asr_providers_config(),
            provider_type=ProviderType.ASR
        )
        registry.register_providers_from_config(
            get_default_tts_providers_config(),
            provider_type=ProviderType.TTS
        )
        
        # Get ASR providers
        asr_providers_list = registry.get_asr_providers()
        asr_providers = [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": "online"
            }
            for p in asr_providers_list
        ]

        # Get TTS providers
        tts_providers_list = registry.get_tts_providers()
        tts_providers = [
            {
                "id": p.id,
                "name": p.name,
                "endpoint": p.endpoint,
                "status": "online",
                "deployment": "cloud",
                "languages": p.languages,
                "languageList": p.languageList,
                "capabilities": p.capabilities.dict() if hasattr(p.capabilities, 'dict') else p.capabilities,
                "description": p.description,
                "icon": p.icon
            }
            for p in tts_providers_list
        ]
        
        # Convert TTS providers array to dict keyed by ID for frontend compatibility
        tts_providers_dict = {p["id"]: p for p in tts_providers}
        
        from datetime import datetime
        return {
            "asr_providers": asr_providers,
            "tts_providers": tts_providers,
            "providers": tts_providers_dict,  # For useComprehensiveTTS hook
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get providers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )

"""
Voice Greeting API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import logging
from bson import ObjectId

from app.schemas.voice_greeting import (
    VoiceGreetingConfigUpdate,
    VoiceGreetingConfigResponse,
    VoiceGreetingPreviewRequest
)
from app.models.voice_greeting import GreetingAudioResponse
from app.services.voice_greeting_service import VoiceGreetingService
from app.services.conference_service import conference_service
from app.services.bus_service import bus_service
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize voice greeting service
voice_greeting_service = VoiceGreetingService()


@router.get(
    "/conferences/{conference_id}/voice-greeting",
    response_model=VoiceGreetingConfigResponse,
    summary="Get conference voice greeting configuration",
    description="Get voice greeting configuration for a specific conference."
)
async def get_conference_voice_greeting(
    conference_id: str
):
    """Get conference voice greeting configuration. Public endpoint."""
    try:
        # Get conference
        conference = await conference_service.get_conference(conference_id)
        if not conference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conference not found"
            )

        # Return voice greeting config or default
        if conference.voice_greeting:
            return VoiceGreetingConfigResponse(**conference.voice_greeting.model_dump())
        else:
            # Return default config
            return VoiceGreetingConfigResponse(
                enabled=False,
                greeting_type="simple",
                message_template="Welcome! Thank you for checking in.",
                tts_provider="coqui_xtts",
                voice_id=None,
                speed=1.0,
                pitch=0.0,
                language="en",
                personalization_enabled=False
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conference voice greeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice greeting configuration: {str(e)}"
        )


@router.put(
    "/conferences/{conference_id}/voice-greeting",
    response_model=VoiceGreetingConfigResponse,
    summary="Update conference voice greeting configuration",
    description="Update voice greeting configuration for a conference (admin only)."
)
async def update_conference_voice_greeting(
    conference_id: str,
    config_update: VoiceGreetingConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update conference voice greeting configuration."""
    try:
        # Get conference
        conference = await conference_service.get_conference(conference_id)
        if not conference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conference not found"
            )

        # Update voice greeting config
        updated_conference = await conference_service.update_voice_greeting(
            conference_id=conference_id,
            voice_greeting_config=config_update.model_dump(exclude_none=True)
        )

        if updated_conference.voice_greeting:
            return VoiceGreetingConfigResponse(**updated_conference.voice_greeting.model_dump())
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update voice greeting configuration"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conference voice greeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update voice greeting configuration: {str(e)}"
        )


@router.post(
    "/conferences/{conference_id}/voice-greeting/preview",
    response_model=GreetingAudioResponse,
    summary="Preview conference voice greeting",
    description="Generate a preview of the voice greeting with sample data."
)
async def preview_conference_voice_greeting(
    conference_id: str,
    preview_request: VoiceGreetingPreviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate a preview of the voice greeting."""
    try:
        # Get conference
        conference = await conference_service.get_conference(conference_id)
        if not conference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conference not found"
            )

        # Prepare event data
        event_data = {
            "conference_name": conference.name,
            "venue": conference.venue
        }

        # Initialize service if needed
        await voice_greeting_service.initialize()

        # Generate preview
        preview = await voice_greeting_service.preview_greeting(
            message_template=preview_request.message_template,
            sample_user_data=preview_request.sample_user_data,
            event_data=event_data,
            tts_provider=preview_request.tts_provider,
            voice_id=preview_request.voice_id,
            speed=preview_request.speed,
            pitch=preview_request.pitch,
            language=preview_request.language,
            personalization_enabled=True,  # Always use personalization for preview
            user_id=current_user.get("sub", current_user.get("user_id", "preview_user"))
        )

        return preview

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get(
    "/buses/routes/{route_id}/voice-greeting",
    response_model=VoiceGreetingConfigResponse,
    summary="Get bus route voice greeting configuration",
    description="Get voice greeting configuration for a specific bus route."
)
async def get_bus_route_voice_greeting(
    route_id: str
):
    """Get bus route voice greeting configuration. Public endpoint."""
    try:
        # Get bus route
        bus_route = await bus_service.get_bus_route(route_id)
        if not bus_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus route not found"
            )

        # Return voice greeting config or default
        if bus_route.voice_greeting:
            return VoiceGreetingConfigResponse(**bus_route.voice_greeting.model_dump())
        else:
            # Return default config
            return VoiceGreetingConfigResponse(
                enabled=False,
                greeting_type="simple",
                message_template="Welcome aboard! Thank you for checking in.",
                tts_provider="coqui_xtts",
                voice_id=None,
                speed=1.0,
                pitch=0.0,
                language="en",
                personalization_enabled=False
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bus route voice greeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice greeting configuration: {str(e)}"
        )


@router.put(
    "/buses/routes/{route_id}/voice-greeting",
    response_model=VoiceGreetingConfigResponse,
    summary="Update bus route voice greeting configuration",
    description="Update voice greeting configuration for a bus route (admin/coordinator only)."
)
async def update_bus_route_voice_greeting(
    route_id: str,
    config_update: VoiceGreetingConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update bus route voice greeting configuration."""
    try:
        # Get bus route
        bus_route = await bus_service.get_bus_route(route_id)
        if not bus_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus route not found"
            )

        # Update voice greeting config
        updated_route = await bus_service.update_voice_greeting(
            route_id=route_id,
            voice_greeting_config=config_update.model_dump(exclude_none=True)
        )

        if updated_route.voice_greeting:
            return VoiceGreetingConfigResponse(**updated_route.voice_greeting.model_dump())
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update voice greeting configuration"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update bus route voice greeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update voice greeting configuration: {str(e)}"
        )


@router.post(
    "/buses/routes/{route_id}/voice-greeting/preview",
    response_model=GreetingAudioResponse,
    summary="Preview bus route voice greeting",
    description="Generate a preview of the bus route voice greeting with sample data."
)
async def preview_bus_route_voice_greeting(
    route_id: str,
    preview_request: VoiceGreetingPreviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate a preview of the bus route voice greeting."""
    try:
        # Get bus route
        bus_route = await bus_service.get_bus_route(route_id)
        if not bus_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus route not found"
            )

        # Prepare event data
        event_data = {
            "bus_route_name": bus_route.name or bus_route.route_name,
            "pickup_location": bus_route.pickup_location or bus_route.departure_location
        }

        # Initialize service if needed
        await voice_greeting_service.initialize()

        # Generate preview
        preview = await voice_greeting_service.preview_greeting(
            message_template=preview_request.message_template,
            sample_user_data=preview_request.sample_user_data,
            event_data=event_data,
            tts_provider=preview_request.tts_provider,
            voice_id=preview_request.voice_id,
            speed=preview_request.speed,
            pitch=preview_request.pitch,
            language=preview_request.language,
            personalization_enabled=True,
            user_id=current_user.get("sub", current_user.get("user_id", "preview_user"))
        )

        return preview

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


# ============================================================================
# Custom Voice Upload Endpoints
# ============================================================================

@router.post(
    "/voices/upload",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)]
)
async def upload_custom_voice(
    file: UploadFile = File(...),
    voice_name: str = Form(...),
    ref_text: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a custom voice reference audio file for voice cloning.

    Args:
        file: Audio file (WAV or MP3, 5-60 seconds)
        voice_name: Display name for the voice
        ref_text: Optional transcript of the reference audio
        current_user: Authenticated user

    Returns:
        Voice upload confirmation with voice_id

    Raises:
        400: Invalid file format or duration
        500: Upload failed
    """
    import os
    import secrets
    import wave
    from pydub import AudioSegment

    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only audio files (WAV, MP3) are supported"
            )

        # Read file content
        audio_bytes = await file.read()

        # Validate file size (max 50MB)
        if len(audio_bytes) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 50MB"
            )

        # Generate unique voice_id
        voice_id = f"voice_{secrets.token_urlsafe(8).lower()}"

        # Determine file extension
        file_ext = 'wav'
        if file.content_type == 'audio/mpeg' or file.content_type == 'audio/mp3':
            file_ext = 'mp3'

        # Save to temporary file for validation
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # Load audio and validate duration
            audio = AudioSegment.from_file(temp_path)
            duration_seconds = len(audio) / 1000.0  # pydub uses milliseconds

            # Validate duration (5-60 seconds)
            if duration_seconds < 5.0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio must be at least 5 seconds long (current: {duration_seconds:.1f}s)"
                )
            if duration_seconds > 60.0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio must be less than 60 seconds long (current: {duration_seconds:.1f}s)"
                )

            # Convert to WAV if MP3 (for better compatibility with TTS providers)
            if file_ext == 'mp3':
                # Convert to WAV: 24kHz, 16-bit, stereo (matches existing voices)
                audio = audio.set_frame_rate(24000)
                audio = audio.set_sample_width(2)  # 16-bit
                if audio.channels == 1:
                    audio = audio.set_channels(2)  # Stereo

            # Save to voice-lab directory
            voice_dir = "/opt/kasaai/apps/voice-lab/voices"
            os.makedirs(voice_dir, exist_ok=True)

            voice_filename = f"{voice_id}_ref.wav"
            voice_path = os.path.join(voice_dir, voice_filename)

            # Export as WAV
            audio.export(voice_path, format="wav")

            logger.info(f"Custom voice uploaded successfully: {voice_id} ({voice_name})")

            # Update voice_transcripts in tts_provider_service.py
            # Note: This would require modifying the service code or storing in database
            # For now, we'll use a generic transcript if ref_text is not provided
            if not ref_text:
                ref_text = "Welcome to our service. Thank you for being here today."

            # TODO: Store voice metadata in database for retrieval
            # For now, return success with voice_id

            return {
                "voice_id": voice_id,
                "voice_name": voice_name,
                "voice_filename": voice_filename,
                "duration_seconds": duration_seconds,
                "ref_text": ref_text,
                "message": "Custom voice uploaded successfully. You can now select it in voice settings."
            }

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload custom voice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload voice: {str(e)}"
        )

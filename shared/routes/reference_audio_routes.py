"""
Shared Reference Audio Routes for All KasaAI Applications

Uses the centralized ReferenceAudioService for all operations.
Can be included in any app with dependency injection.

Apps using this router:
- InkWave (audiobook narration)
- ChurchFlow (announcements, greetings)
- StudyFlow (tutoring voices)
- B2C Portal (voice customization)
- Any app using zero-shot TTS providers

Author: AI Labs Africa
Created: November 29, 2025
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from typing import List, Optional, Callable
import logging

from apps.shared.services.reference_audio_service import (
    get_reference_audio_service,
    ReferenceAudioService,
    ReferenceAudio,
    ReferenceAudioCreate,
    ReferenceAudioUpdate,
    ReferenceAudioFilters,
    ZERO_SHOT_PROVIDERS,
    ACCEPTED_FORMATS,
    MAX_FILE_SIZE
)

logger = logging.getLogger(__name__)


def create_reference_audio_router(
    get_current_user_func: Callable,
    get_database_func: Callable = None,  # Optional, service uses its own connection
    storage_config: Optional[dict] = None,
    storage_base_path: str = "reference_audio"
) -> APIRouter:
    """
    Create reference audio router with dependency injection.

    Args:
        get_current_user_func: Function to get current authenticated user
        get_database_func: Optional database function (service uses its own connection)
        storage_config: Optional Hetzner storage configuration
        storage_base_path: Base path for storage (app-specific)

    Returns:
        FastAPI router for reference audio operations
    """
    router = APIRouter(prefix="/reference-audio", tags=["Reference Audio"])

    def get_user_id(user) -> str:
        """Extract user ID from user dict or Pydantic model"""
        # Handle both dict and Pydantic model
        if hasattr(user, 'model_dump'):
            # Pydantic v2 model
            user_dict = user.model_dump()
        elif hasattr(user, 'dict'):
            # Pydantic v1 model
            user_dict = user.dict()
        elif isinstance(user, dict):
            user_dict = user
        else:
            # Try to access attributes directly
            return getattr(user, 'sub', None) or getattr(user, 'id', None) or getattr(user, 'user_id', '') or ''
        return user_dict.get("sub") or user_dict.get("id") or user_dict.get("user_id") or ""

    def get_org_id(user) -> Optional[str]:
        """Extract organization ID from user dict or Pydantic model"""
        # Handle both dict and Pydantic model
        if hasattr(user, 'model_dump'):
            user_dict = user.model_dump()
        elif hasattr(user, 'dict'):
            user_dict = user.dict()
        elif isinstance(user, dict):
            user_dict = user
        else:
            return getattr(user, 'organization_id', None)
        return user_dict.get("organization_id")

    # Get service instance
    service = get_reference_audio_service(
        storage_config=storage_config,
        storage_base_path=storage_base_path
    )

    # ==================== Upload Reference Audio ====================

    @router.post(
        "/upload",
        summary="Upload reference audio",
        description="Upload reference audio file for zero-shot TTS providers (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS)."
    )
    async def upload_reference_audio(
        audio_file: UploadFile = File(..., description="Audio file (WAV, MP3, OGG, FLAC, M4A, max 10MB)"),
        name: str = Form(..., description="Reference audio name"),
        description: Optional[str] = Form(None, description="Description"),
        create_voice: bool = Form(False, description="Create voice library entry"),
        gender: Optional[str] = Form(None, description="Gender for voice entry"),
        language: Optional[str] = Form("en", description="Language for voice entry"),
        tags: Optional[str] = Form(None, description="Comma-separated tags"),
        current_user = Depends(get_current_user_func)
    ):
        """Upload reference audio file."""
        try:
            user_id = get_user_id(current_user)
            org_id = get_org_id(current_user)

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User ID not found"
                )

            # Validate file
            file_ext = "." + (audio_file.filename.split(".")[-1] if "." in audio_file.filename else "")
            if file_ext not in ACCEPTED_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported format. Please use: {', '.join(ACCEPTED_FORMATS)}"
                )

            # Read file
            audio_bytes = await audio_file.read()

            # Validate size
            if len(audio_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"
                )

            # Create reference audio
            audio_data = ReferenceAudioCreate(
                name=name,
                description=description,
                audio_bytes=audio_bytes,
                audio_filename=audio_file.filename,
                create_voice=create_voice,
                gender=gender,
                language=language,
                tags=tags.split(",") if tags else []
            )

            reference_audio = await service.create_reference_audio(
                audio_data=audio_data,
                user_id=user_id,
                organization_id=org_id
            )

            # Create voice library entry if requested
            voice_id = None
            if create_voice:
                try:
                    from apps.shared.services.voice_library_service import (
                        get_voice_library_service,
                        VoiceCreate,
                        VoiceGender,
                        VoiceCharacteristics,
                        VoiceAccess,
                        VoiceVisibility,
                        VoiceMetadata
                    )

                    voice_service = get_voice_library_service()
                    
                    voice_data = VoiceCreate(
                        name=name,
                        description=description or f"Voice from reference audio: {name}",
                        characteristics=VoiceCharacteristics(
                            gender=VoiceGender(gender) if gender else VoiceGender.UNKNOWN,
                            language=language or "en"
                        ),
                        access=VoiceAccess(
                            visibility=VoiceVisibility.PRIVATE
                        ),
                        metadata=VoiceMetadata(
                            tags=tags.split(",") if tags else [],
                            categories=["zero-shot-tts", "reference-audio"],
                            use_cases=["audiobook", "narration"]
                        )
                    )

                    voice = await voice_service.create_voice(
                        voice_data=voice_data,
                        audio_file=audio_bytes,
                        audio_filename=audio_file.filename,
                        user_id=user_id,
                        organization_id=org_id
                    )

                    voice_id = voice.get("voice_id") if isinstance(voice, dict) else getattr(voice, "voice_id", None)
                    
                    # Update reference audio with voice_id
                    if voice_id:
                        await service.db.reference_audio.update_one(
                            {"reference_audio_id": reference_audio.reference_audio_id},
                            {"$set": {"voice_id": voice_id}}
                        )
                        reference_audio.voice_id = voice_id

                    logger.info(f"Created voice library entry: {voice_id}")
                except Exception as e:
                    logger.error(f"Failed to create voice library entry: {e}")
                    # Don't fail the upload if voice creation fails

            return {
                "success": True,
                "reference_audio_id": reference_audio.reference_audio_id,
                "voice_id": voice_id,
                "name": reference_audio.name,
                "description": reference_audio.description,
                "audio_url": reference_audio.audio_url,
                "file_size_bytes": reference_audio.file_size_bytes,
                "duration_seconds": reference_audio.duration_seconds,
                "format": reference_audio.format,
                "compatible_providers": reference_audio.compatible_providers,
                "created_at": reference_audio.created_at.isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading reference audio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload reference audio: {str(e)}"
            )

    # ==================== List Reference Audio ====================

    @router.get(
        "/",
        summary="List reference audio",
        description="Get list of reference audio files for the current user."
    )
    async def list_reference_audio(
        search: Optional[str] = Query(None, description="Search query"),
        compatible_provider: Optional[str] = Query(None, description="Filter by compatible provider"),
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
        current_user = Depends(get_current_user_func)
    ):
        """List reference audio files."""
        try:
            user_id = get_user_id(current_user)
            org_id = get_org_id(current_user)

            filters = ReferenceAudioFilters(
                user_id=user_id,
                organization_id=org_id,
                search=search,
                compatible_provider=compatible_provider
            )

            reference_audios, total = await service.list_reference_audio(
                filters=filters,
                skip=skip,
                limit=limit
            )

            return {
                "reference_audio": [ra.dict() for ra in reference_audios],
                "total": total,
                "skip": skip,
                "limit": limit
            }

        except Exception as e:
            logger.error(f"Error listing reference audio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list reference audio: {str(e)}"
            )

    # ==================== Get Reference Audio ====================

    @router.get(
        "/{reference_audio_id}",
        summary="Get reference audio",
        description="Get reference audio metadata by ID."
    )
    async def get_reference_audio(
        reference_audio_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Get reference audio by ID."""
        try:
            user_id = get_user_id(current_user)

            reference_audio = await service.get_reference_audio(
                reference_audio_id=reference_audio_id,
                user_id=user_id
            )

            if not reference_audio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reference audio not found"
                )

            return reference_audio.dict()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting reference audio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get reference audio: {str(e)}"
            )

    # ==================== Get Audio File ====================

    @router.get(
        "/{reference_audio_id}/audio",
        summary="Get audio file",
        description="Serve the reference audio file."
    )
    async def get_reference_audio_file(
        reference_audio_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Serve reference audio file."""
        try:
            user_id = get_user_id(current_user)

            reference_audio = await service.get_reference_audio(
                reference_audio_id=reference_audio_id,
                user_id=user_id
            )

            if not reference_audio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reference audio not found"
                )

            # Get audio bytes
            audio_bytes = await service.get_audio_file_bytes(
                reference_audio_id=reference_audio_id,
                user_id=user_id
            )

            if not audio_bytes:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audio file not found"
                )

            # Determine content type
            content_type_map = {
                "wav": "audio/wav",
                "mp3": "audio/mpeg",
                "ogg": "audio/ogg",
                "flac": "audio/flac",
                "m4a": "audio/mp4"
            }
            content_type = content_type_map.get(reference_audio.format.value, "audio/wav")

            return Response(
                content=audio_bytes,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{reference_audio.name}.{reference_audio.format.value}"'
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving audio file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serve audio file: {str(e)}"
            )

    # ==================== Update Reference Audio ====================

    @router.put(
        "/{reference_audio_id}",
        summary="Update reference audio",
        description="Update reference audio metadata."
    )
    async def update_reference_audio(
        reference_audio_id: str,
        name: Optional[str] = Form(None, description="Name"),
        description: Optional[str] = Form(None, description="Description"),
        current_user = Depends(get_current_user_func)
    ):
        """Update reference audio."""
        try:
            user_id = get_user_id(current_user)

            updates = ReferenceAudioUpdate(
                name=name,
                description=description
            )

            reference_audio = await service.update_reference_audio(
                reference_audio_id=reference_audio_id,
                updates=updates,
                user_id=user_id
            )

            if not reference_audio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reference audio not found"
                )

            return reference_audio.dict()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating reference audio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update reference audio: {str(e)}"
            )

    # ==================== Delete Reference Audio ====================

    @router.delete(
        "/{reference_audio_id}",
        summary="Delete reference audio",
        description="Delete reference audio file and metadata."
    )
    async def delete_reference_audio(
        reference_audio_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Delete reference audio."""
        try:
            user_id = get_user_id(current_user)

            success = await service.delete_reference_audio(
                reference_audio_id=reference_audio_id,
                user_id=user_id
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reference audio not found"
                )

            return {
                "success": True,
                "message": "Reference audio deleted successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting reference audio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete reference audio: {str(e)}"
            )

    return router





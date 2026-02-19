"""
Shared Voice Library Routes for All KasaAI Applications

Uses the centralized VoiceLibraryService for all operations.
Can be included in any app with dependency injection.

Apps using this router:
- ChurchFlow (announcements, greetings)
- InkWave (audiobook narration)
- StudyFlow (tutoring voices)
- EventFlow (event announcements)
- Core Backend (TTS services)

Author: AI Labs Africa
Created: November 9, 2025
Updated: November 26, 2025 - Refactored to use VoiceLibraryService
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Callable
import logging

from apps.shared.services.voice_library_service import (
    get_voice_library_service,
    VoiceLibraryService,
    Voice,
    VoiceCreate,
    VoiceUpdate,
    VoiceFilters,
    Pagination,
    VoiceList,
    VoiceVisibility,
    VoiceStatus,
    VoiceGender,
    VoiceCharacteristics,
    VoiceAccess,
    VoiceMetadata,
)

logger = logging.getLogger(__name__)


def create_voice_library_router(
    get_current_user_func: Callable,
    get_database_func: Callable = None,  # Optional, service uses its own connection
    require_admin_func: Optional[Callable] = None
) -> APIRouter:
    """
    Create voice library router with dependency injection.

    Args:
        get_current_user_func: Function to get current authenticated user
        get_database_func: Optional function to get database (not used, kept for backward compat)
        require_admin_func: Optional function to require admin privileges

    Returns:
        Configured APIRouter

    Example:
        from app.core.auth import get_current_user

        router = create_voice_library_router(
            get_current_user_func=get_current_user
        )

        app.include_router(
            router,
            prefix="/api/voice-library",
            tags=["Voice Library"]
        )
    """
    router = APIRouter()

    # Get service instance
    voice_service = get_voice_library_service()

    # ==================== Helper Functions ====================

    def get_user_id(current_user) -> str:
        """Extract user ID from current_user (handles both dict and object)."""
        if isinstance(current_user, dict):
            return current_user.get("sub") or current_user.get("id") or current_user.get("user_id")
        return getattr(current_user, "id", None) or getattr(current_user, "sub", None) or str(current_user)

    def get_org_id(current_user) -> Optional[str]:
        """Extract organization ID from current_user."""
        if isinstance(current_user, dict):
            return current_user.get("organization_id") or current_user.get("org_id")
        return getattr(current_user, "organization_id", None)

    # ==================== Favorites (MUST be before /{voice_id}) ====================

    @router.get(
        "/favorites",
        summary="Get favorite voices",
        description="Get user's favorite voices."
    )
    async def get_favorites(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        current_user = Depends(get_current_user_func)
    ):
        """Get user's favorite voices."""
        try:
            user_id = get_user_id(current_user)

            # Get favorites from service
            favorites = await voice_service.get_user_favorites(user_id, skip, limit)

            return {
                "success": True,
                "message": "Favorites retrieved successfully",
                "voices": [v.dict() for v in favorites] if favorites else [],
                "total": len(favorites) if favorites else 0,
                "skip": skip,
                "limit": limit
            }

        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get favorites: {str(e)}"
            )

    @router.post(
        "/favorites/{voice_id}",
        summary="Add to favorites",
        description="Add a voice to user's favorites."
    )
    async def add_to_favorites(
        voice_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Add voice to favorites."""
        try:
            user_id = get_user_id(current_user)

            success = await voice_service.add_to_favorites(user_id, voice_id)

            return {
                "success": True,
                "message": "Voice added to favorites",
                "voice_id": voice_id
            }

        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add to favorites: {str(e)}"
            )

    @router.delete(
        "/favorites/{voice_id}",
        summary="Remove from favorites",
        description="Remove a voice from user's favorites."
    )
    async def remove_from_favorites(
        voice_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Remove voice from favorites."""
        try:
            user_id = get_user_id(current_user)

            success = await voice_service.remove_from_favorites(user_id, voice_id)

            return {
                "success": True,
                "message": "Voice removed from favorites",
                "voice_id": voice_id
            }

        except Exception as e:
            logger.error(f"Error removing from favorites: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove from favorites: {str(e)}"
            )

    # ==================== Ratings (MUST be before /{voice_id}) ====================

    @router.post(
        "/ratings/{voice_id}",
        summary="Rate voice",
        description="Rate a voice (1-5 stars)."
    )
    async def rate_voice(
        voice_id: str,
        rating: int = Query(..., ge=1, le=5, description="Rating (1-5)"),
        review: Optional[str] = Query(None, description="Optional review text"),
        current_user = Depends(get_current_user_func)
    ):
        """Rate a voice."""
        try:
            user_id = get_user_id(current_user)

            await voice_service.rate_voice(user_id, voice_id, rating, review)

            return {
                "success": True,
                "message": "Voice rated successfully",
                "voice_id": voice_id,
                "rating": rating
            }

        except Exception as e:
            logger.error(f"Error rating voice: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rate voice: {str(e)}"
            )

    # ==================== List Voices ====================

    @router.get(
        "/",
        summary="List voices",
        description="Get list of all accessible voices with filtering and pagination."
    )
    async def list_voices(
        search: Optional[str] = Query(None, description="Search query"),
        gender: Optional[str] = Query(None, description="Filter by gender"),
        language: Optional[str] = Query(None, description="Filter by language"),
        accent: Optional[str] = Query(None, description="Filter by accent"),
        visibility: Optional[str] = Query(None, description="Filter by visibility"),
        categories: Optional[str] = Query(None, description="Filter by categories (comma-separated)"),
        tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
        use_cases: Optional[str] = Query(None, description="Filter by use cases (comma-separated)"),
        featured: Optional[bool] = Query(None, description="Filter by featured status"),
        verified: Optional[bool] = Query(None, description="Filter by verified status"),
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
        sort_by: str = Query("created_at", description="Sort field"),
        sort_order: int = Query(-1, description="Sort order (1=asc, -1=desc)"),
        current_user = Depends(get_current_user_func)
    ):
        """List all accessible voices with filtering and pagination."""
        try:
            user_id = get_user_id(current_user)
            org_id = get_org_id(current_user)

            # Build filters
            filters = VoiceFilters(
                search=search,
                gender=VoiceGender(gender) if gender else None,
                language=language,
                accent=accent,
                visibility=VoiceVisibility(visibility) if visibility else None,
                categories=categories.split(",") if categories else None,
                tags=tags.split(",") if tags else None,
                use_cases=use_cases.split(",") if use_cases else None,
                featured=featured,
                verified=verified
            )

            pagination = Pagination(
                skip=skip,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )

            result = await voice_service.list_voices(
                filters=filters,
                pagination=pagination,
                user_id=user_id,
                organization_id=org_id
            )

            return {
                "success": True,
                "message": "Voices retrieved successfully",
                "voices": [v.dict() for v in result.voices],
                "total": result.total,
                "skip": result.skip,
                "limit": result.limit
            }

        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list voices: {str(e)}"
            )

    # ==================== Create Voice ====================

    @router.post(
        "/",
        summary="Create voice",
        description="Create a new voice with optional audio upload."
    )
    async def create_voice(
        name: str = Form(..., description="Voice name"),
        description: Optional[str] = Form(None, description="Voice description"),
        gender: Optional[str] = Form(None, description="Voice gender"),
        language: Optional[str] = Form("en", description="Voice language"),
        accent: Optional[str] = Form(None, description="Voice accent"),
        visibility: Optional[str] = Form("private", description="Visibility level"),
        tags: Optional[str] = Form(None, description="Comma-separated tags"),
        categories: Optional[str] = Form(None, description="Comma-separated categories"),
        use_cases: Optional[str] = Form(None, description="Comma-separated use cases"),
        audio_file: Optional[UploadFile] = File(None, description="Audio file"),
        current_user = Depends(get_current_user_func)
    ):
        """Create a new voice."""
        try:
            user_id = get_user_id(current_user)
            org_id = get_org_id(current_user)

            # Build voice data
            voice_data = VoiceCreate(
                name=name,
                description=description,
                characteristics=VoiceCharacteristics(
                    gender=VoiceGender(gender) if gender else VoiceGender.UNKNOWN,
                    language=language or "en",
                    accent=accent
                ),
                access=VoiceAccess(
                    visibility=VoiceVisibility(visibility) if visibility else VoiceVisibility.PRIVATE
                ),
                metadata=VoiceMetadata(
                    tags=tags.split(",") if tags else [],
                    categories=categories.split(",") if categories else [],
                    use_cases=use_cases.split(",") if use_cases else []
                )
            )

            # Handle audio file
            audio_bytes = None
            audio_filename = None
            if audio_file:
                audio_bytes = await audio_file.read()
                audio_filename = audio_file.filename

            voice = await voice_service.create_voice(
                voice_data=voice_data,
                audio_file=audio_bytes,
                audio_filename=audio_filename,
                user_id=user_id,
                organization_id=org_id
            )

            return {
                "success": True,
                "message": "Voice created successfully",
                "voice": voice.dict()
            }

        except Exception as e:
            logger.error(f"Error creating voice: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create voice: {str(e)}"
            )

    # ==================== Get Voice (MUST be after specific paths) ====================

    @router.get(
        "/{voice_id}",
        summary="Get voice details",
        description="Get detailed information about a specific voice."
    )
    async def get_voice(
        voice_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Get voice details by ID."""
        try:
            user_id = get_user_id(current_user)

            voice = await voice_service.get_voice(voice_id, user_id)

            if not voice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Voice {voice_id} not found"
                )

            return {
                "success": True,
                "message": "Voice retrieved successfully",
                "voice": voice.dict()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting voice {voice_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get voice: {str(e)}"
            )

    # ==================== Update Voice ====================

    @router.patch(
        "/{voice_id}",
        summary="Update voice",
        description="Update voice metadata."
    )
    async def update_voice(
        voice_id: str,
        updates: dict,
        current_user = Depends(get_current_user_func)
    ):
        """Update voice metadata."""
        try:
            user_id = get_user_id(current_user)

            # Build update object
            voice_update = VoiceUpdate(**updates)

            voice = await voice_service.update_voice(
                voice_id=voice_id,
                updates=voice_update,
                user_id=user_id
            )

            if not voice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Voice {voice_id} not found or you don't have permission to update it"
                )

            return {
                "success": True,
                "message": "Voice updated successfully",
                "voice": voice.dict()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating voice {voice_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update voice: {str(e)}"
            )

    # ==================== Delete Voice ====================

    @router.delete(
        "/{voice_id}",
        summary="Delete voice",
        description="Delete a voice (soft delete by default)."
    )
    async def delete_voice(
        voice_id: str,
        soft_delete: bool = Query(True, description="Soft delete (archive) instead of hard delete"),
        current_user = Depends(get_current_user_func)
    ):
        """Delete a voice."""
        try:
            user_id = get_user_id(current_user)

            success = await voice_service.delete_voice(
                voice_id=voice_id,
                user_id=user_id,
                soft_delete=soft_delete
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Voice {voice_id} not found or you don't have permission to delete it"
                )

            return {
                "success": True,
                "message": f"Voice {'archived' if soft_delete else 'deleted'} successfully",
                "voice_id": voice_id
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting voice {voice_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete voice: {str(e)}"
            )

    # ==================== Usage Tracking ====================

    @router.post(
        "/{voice_id}/use",
        summary="Record voice usage",
        description="Record that a voice was used (for analytics)."
    )
    async def record_usage(
        voice_id: str,
        current_user = Depends(get_current_user_func)
    ):
        """Record voice usage for analytics."""
        try:
            user_id = get_user_id(current_user)
            org_id = get_org_id(current_user)

            await voice_service.record_usage(voice_id, user_id, org_id)

            return {
                "success": True,
                "message": "Usage recorded",
                "voice_id": voice_id
            }

        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            # Don't fail the request for analytics errors
            return {
                "success": True,
                "message": "Usage recording skipped",
                "voice_id": voice_id
            }

    return router

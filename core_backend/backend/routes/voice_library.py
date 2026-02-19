"""
Voice Library Routes - Centralized voice management API

Provides API endpoints for voice library operations:
- Voice CRUD (create, read, update, delete)
- Voice search and filtering
- Favorites and ratings
- Voice analytics
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import shared voice library service
from apps.shared.services.voice_library_service import (
    get_voice_library_service,
    Voice,
    VoiceCreate,
    VoiceUpdate,
    VoiceFilters,
    Pagination,
    VoiceList,
    VoiceVisibility,
    VoiceStatus,
    VoiceGender,
    AudioFormat,
)

from ..auth import get_current_user_mongo
from ..middleware.organization_context import (
    get_organization_context,
    validate_organization_access
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-library", tags=["voice-library"])

# Get service instance
voice_library_service = get_voice_library_service()


# ==================== Request/Response Models ====================

class VoiceCreateRequest(BaseModel):
    """Request to create a new voice"""
    name: str = Field(..., description="Voice name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Voice description", max_length=500)
    gender: Optional[VoiceGender] = None
    language: Optional[str] = None
    accent: Optional[str] = None
    dialect: Optional[str] = None
    tone: Optional[str] = None
    pace: Optional[str] = None
    age_range: Optional[str] = None
    visibility: Optional[VoiceVisibility] = VoiceVisibility.PRIVATE
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None


class VoiceResponse(BaseModel):
    """Voice response model"""
    success: bool
    message: str
    voice: Optional[Voice] = None


class VoiceListResponse(BaseModel):
    """Voice list response model"""
    success: bool
    message: str
    voices: List[Voice]
    total: int
    skip: int
    limit: int


class FavoriteRequest(BaseModel):
    """Request to favorite/unfavorite a voice"""
    voice_id: str


class RatingRequest(BaseModel):
    """Request to rate a voice"""
    voice_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    review: Optional[str] = Field(None, max_length=500)


# ==================== Voice CRUD Endpoints ====================

@router.post("/", response_model=VoiceResponse)
async def create_voice(
    request: Request,
    name: str = Query(..., description="Voice name"),
    description: Optional[str] = Query(None, description="Voice description"),
    gender: Optional[VoiceGender] = Query(None, description="Voice gender"),
    language: Optional[str] = Query(None, description="Language code"),
    accent: Optional[str] = Query(None, description="Accent"),
    dialect: Optional[str] = Query(None, description="Dialect"),
    tone: Optional[str] = Query(None, description="Tone (warm, professional, etc)"),
    pace: Optional[str] = Query(None, description="Pace (slow, medium, fast)"),
    age_range: Optional[str] = Query(None, description="Age range"),
    visibility: Optional[VoiceVisibility] = Query(VoiceVisibility.PRIVATE, description="Visibility"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    use_cases: Optional[str] = Query(None, description="Comma-separated use cases"),
    audio_file: UploadFile = File(..., description="Voice audio file"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Create a new voice with audio upload.

    Now properly scoped to organization. Requires authentication.

    Args:
        name: Voice name
        audio_file: Audio file (WAV, MP3, OGG, FLAC, M4A)
        current_user: Authenticated user

    Returns:
        Created voice
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)
        # Read audio file
        audio_bytes = await audio_file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Parse tags, categories, use_cases
        tags_list = [t.strip() for t in tags.split(",")] if tags else []
        categories_list = [c.strip() for c in categories.split(",")] if categories else []
        use_cases_list = [u.strip() for u in use_cases.split(",")] if use_cases else []

        # Build voice create request
        from apps.shared.services.voice_library_service import (
            VoiceCharacteristics,
            VoiceAccess,
            VoiceMetadata
        )

        voice_data = VoiceCreate(
            name=name,
            description=description,
            characteristics=VoiceCharacteristics(
                gender=gender or VoiceGender.UNKNOWN,
                language=language or "en",
                accent=accent,
                dialect=dialect,
                tone=tone,
                pace=pace,
                age_range=age_range
            ),
            access=VoiceAccess(visibility=visibility),
            metadata=VoiceMetadata(
                tags=tags_list,
                categories=categories_list,
                use_cases=use_cases_list
            )
        )

        # Get user info
        user_id = str(current_user.get("_id"))
        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Creating voice for organization: {organization_id}, user: {user_id}")

        # Create voice
        voice = await voice_library_service.create_voice(
            voice_data=voice_data,
            audio_file=audio_bytes,
            audio_filename=audio_file.filename,
            user_id=user_id,
            organization_id=organization_id
        )

        return VoiceResponse(
            success=True,
            message="Voice created successfully",
            voice=voice
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating voice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    request: Request,
    voice_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Get a voice by ID.

    Now properly scoped to organization. Requires authentication.

    Args:
        voice_id: Voice identifier
        current_user: Authenticated user

    Returns:
        Voice details
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = str(current_user.get("_id"))

        logger.info(f"Getting voice {voice_id} for user: {user_id}, organization: {org_id}")

        voice = await voice_library_service.get_voice(voice_id, user_id)

        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found or access denied")

        # Verify organization ownership if org_id is present
        if org_id and hasattr(voice.owner, 'organization_id'):
            if voice.owner.organization_id != org_id:
                raise HTTPException(status_code=403, detail="Access denied to this voice")

        return VoiceResponse(
            success=True,
            message="Voice retrieved successfully",
            voice=voice
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=VoiceListResponse)
async def list_voices(
    request: Request,
    # Filters
    search: Optional[str] = Query(None, description="Search query"),
    gender: Optional[VoiceGender] = Query(None, description="Filter by gender"),
    language: Optional[str] = Query(None, description="Filter by language"),
    accent: Optional[str] = Query(None, description="Filter by accent"),
    visibility: Optional[VoiceVisibility] = Query(None, description="Filter by visibility"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    use_cases: Optional[str] = Query(None, description="Comma-separated use cases"),
    featured: Optional[bool] = Query(None, description="Featured voices only"),
    verified: Optional[bool] = Query(None, description="Verified voices only"),
    owner_id: Optional[str] = Query(None, description="Filter by owner"),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: int = Query(-1, description="Sort order (1=asc, -1=desc)"),
    # Auth
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    List voices with filtering and pagination.

    Now properly scoped to organization. Requires authentication.

    Args:
        search: Search in name, description, tags
        current_user: Authenticated user

    Returns:
        List of voices
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = str(current_user.get("_id"))
        # Use organization_id from context with fallback
        organization_id = org_id or current_user.get("organization_id")

        logger.info(f"Listing voices for organization: {organization_id}, user: {user_id}")

        # Parse comma-separated filters
        tags_list = [t.strip() for t in tags.split(",")] if tags else None
        categories_list = [c.strip() for c in categories.split(",")] if categories else None
        use_cases_list = [u.strip() for u in use_cases.split(",")] if use_cases else None

        # Build filters
        filters = VoiceFilters(
            search=search,
            gender=gender,
            language=language,
            accent=accent,
            visibility=visibility,
            tags=tags_list,
            categories=categories_list,
            use_cases=use_cases_list,
            featured=featured,
            verified=verified,
            owner_id=owner_id,
            status=VoiceStatus.ACTIVE
        )

        # Build pagination
        pagination = Pagination(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Get voices
        result = await voice_library_service.list_voices(
            filters=filters,
            pagination=pagination,
            user_id=user_id,
            organization_id=organization_id
        )

        return VoiceListResponse(
            success=True,
            message="Voices retrieved successfully",
            voices=result.voices,
            total=result.total,
            skip=result.skip,
            limit=result.limit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing voices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{voice_id}", response_model=VoiceResponse)
async def update_voice(
    request: Request,
    voice_id: str,
    updates: VoiceUpdate,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Update a voice.

    Now properly scoped to organization. Requires authentication and ownership.

    Args:
        voice_id: Voice identifier
        updates: Update data
        current_user: Authenticated user

    Returns:
        Updated voice
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = str(current_user.get("_id"))

        logger.info(f"Updating voice {voice_id} for user: {user_id}, organization: {org_id}")

        # Verify ownership before updating
        existing_voice = await voice_library_service.get_voice(voice_id, user_id)
        if not existing_voice:
            raise HTTPException(status_code=404, detail="Voice not found or access denied")

        # Verify organization ownership if org_id is present
        if org_id and hasattr(existing_voice.owner, 'organization_id'):
            if existing_voice.owner.organization_id != org_id:
                raise HTTPException(status_code=403, detail="Access denied - voice belongs to different organization")

        voice = await voice_library_service.update_voice(
            voice_id=voice_id,
            updates=updates,
            user_id=user_id
        )

        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found or access denied")

        return VoiceResponse(
            success=True,
            message="Voice updated successfully",
            voice=voice
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating voice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{voice_id}")
async def delete_voice(
    request: Request,
    voice_id: str,
    soft_delete: bool = Query(True, description="Soft delete (mark as deleted)"),
    delete_files: bool = Query(False, description="Delete associated files"),
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Delete a voice.

    Now properly scoped to organization. Requires authentication and ownership.

    Args:
        voice_id: Voice identifier
        soft_delete: If True, mark as deleted; if False, remove from DB
        delete_files: If True, delete associated files
        current_user: Authenticated user

    Returns:
        Success response
    """
    try:
        # Validate organization access
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = str(current_user.get("_id"))

        logger.info(f"Deleting voice {voice_id} for user: {user_id}, organization: {org_id}")

        # Verify ownership before deleting
        existing_voice = await voice_library_service.get_voice(voice_id, user_id)
        if not existing_voice:
            raise HTTPException(status_code=404, detail="Voice not found or access denied")

        # Verify organization ownership if org_id is present
        if org_id and hasattr(existing_voice.owner, 'organization_id'):
            if existing_voice.owner.organization_id != org_id:
                raise HTTPException(status_code=403, detail="Access denied - voice belongs to different organization")

        success = await voice_library_service.delete_voice(
            voice_id=voice_id,
            user_id=user_id,
            soft_delete=soft_delete,
            delete_files=delete_files
        )

        if not success:
            raise HTTPException(status_code=404, detail="Voice not found or access denied")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Voice deleted successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Favorites Endpoints ====================

@router.post("/favorites/add")
async def add_favorite(
    request: FavoriteRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Add a voice to favorites"""
    try:
        user_id = str(current_user.get("_id"))

        # Check if voice exists
        voice = await voice_library_service.get_voice(request.voice_id, user_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")

        # Add to favorites
        await voice_library_service.favorites_collection.update_one(
            {"user_id": user_id, "voice_id": request.voice_id},
            {
                "$set": {
                    "user_id": user_id,
                    "voice_id": request.voice_id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        # Increment favorites count
        await voice_library_service.collection.update_one(
            {"voice_id": request.voice_id},
            {"$inc": {"stats.favorites": 1}}
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Voice added to favorites"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/favorites/remove")
async def remove_favorite(
    request: FavoriteRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Remove a voice from favorites"""
    try:
        user_id = str(current_user.get("_id"))

        # Remove from favorites
        result = await voice_library_service.favorites_collection.delete_one(
            {"user_id": user_id, "voice_id": request.voice_id}
        )

        if result.deleted_count > 0:
            # Decrement favorites count
            await voice_library_service.collection.update_one(
                {"voice_id": request.voice_id},
                {"$inc": {"stats.favorites": -1}}
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Voice removed from favorites"
            }
        )

    except Exception as e:
        logger.error(f"Error removing favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/favorites/list")
async def list_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_mongo)
):
    """List user's favorite voices"""
    try:
        user_id = str(current_user.get("_id"))

        # Get favorite voice IDs
        cursor = voice_library_service.favorites_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit)

        favorite_voice_ids = []
        async for fav in cursor:
            favorite_voice_ids.append(fav["voice_id"])

        # Get total count
        total = await voice_library_service.favorites_collection.count_documents(
            {"user_id": user_id}
        )

        # Get voice details
        voices = []
        for voice_id in favorite_voice_ids:
            voice = await voice_library_service.get_voice(voice_id, user_id)
            if voice:
                voices.append(voice)

        return VoiceListResponse(
            success=True,
            message="Favorites retrieved successfully",
            voices=voices,
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        logger.error(f"Error listing favorites: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Ratings Endpoints ====================

@router.post("/ratings/add")
async def add_rating(
    request: RatingRequest,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Rate a voice"""
    try:
        user_id = str(current_user.get("_id"))

        # Check if voice exists
        voice = await voice_library_service.get_voice(request.voice_id, user_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")

        # Add/update rating
        await voice_library_service.ratings_collection.update_one(
            {"user_id": user_id, "voice_id": request.voice_id},
            {
                "$set": {
                    "user_id": user_id,
                    "voice_id": request.voice_id,
                    "rating": request.rating,
                    "review": request.review,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )

        # Recalculate average rating
        pipeline = [
            {"$match": {"voice_id": request.voice_id}},
            {"$group": {"_id": "$voice_id", "avg_rating": {"$avg": "$rating"}}}
        ]

        result = await voice_library_service.ratings_collection.aggregate(pipeline).to_list(1)

        if result:
            avg_rating = result[0]["avg_rating"]
            await voice_library_service.collection.update_one(
                {"voice_id": request.voice_id},
                {"$set": {"stats.rating.average": avg_rating}}
            )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Rating added successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding rating: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analytics Endpoints ====================

@router.post("/{voice_id}/use")
async def record_voice_usage(
    voice_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """Record voice usage for analytics"""
    try:
        user_id = str(current_user.get("_id"))
        organization_id = current_user.get("organization_id")

        # Record usage
        await voice_library_service.usage_logs_collection.insert_one({
            "voice_id": voice_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "timestamp": datetime.utcnow()
        })

        # Increment usage count
        await voice_library_service.collection.update_one(
            {"voice_id": voice_id},
            {
                "$inc": {"stats.uses": 1},
                "$set": {"last_used_at": datetime.utcnow()}
            }
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Usage recorded"
            }
        )

    except Exception as e:
        logger.error(f"Error recording usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{voice_id}/restore")
async def restore_voice_files(
    voice_id: str,
    current_user: dict = Depends(get_current_user_mongo)
):
    """
    Restore voice files from Hetzner Storage Box backup.

    This endpoint downloads voice files from cloud storage if local files are missing.
    Useful for disaster recovery or when migrating to a new server.
    """
    try:
        user_id = str(current_user.get("_id"))
        organization_id = current_user.get("organization_id")

        # Get voice
        voice = await voice_library_service.get_voice(voice_id, user_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")

        # Check if user owns the voice or is admin
        if voice.owner.user_id != user_id:
            # TODO: Check if user is admin
            raise HTTPException(status_code=403, detail="Only voice owner can restore files")

        # Restore files from Hetzner
        restore_status = await voice_library_service.restore_voice_files(voice_id)

        # Check if all files were restored successfully
        all_success = all(restore_status.values())

        return JSONResponse(
            status_code=200,
            content={
                "success": all_success,
                "voice_id": voice_id,
                "restore_status": restore_status,
                "message": "All files restored successfully" if all_success else "Some files failed to restore"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error restoring voice files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

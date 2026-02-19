"""
Book Voice Settings API routes.

Endpoints for managing per-book voice settings that persist across sessions.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any

from apps.shared.dependencies.auth import get_current_user
from app.models.book_voice_settings import BookVoiceSettingsUpdate
from app.services.book_voice_settings_service import get_book_voice_settings_service

router = APIRouter(prefix="/books", tags=["book-voice-settings"])


@router.get("/{book_id}/voice-settings")
async def get_book_voice_settings(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get book-level voice settings for current user.

    Args:
        book_id: Book identifier
        user: Authenticated user

    Returns:
        Book voice settings or None if not set
    """
    user_id = user.get("id") or user.get("user_id")

    service = await get_book_voice_settings_service()

    try:
        settings = await service.get_book_settings(book_id, user_id)
        return {
            "book_id": book_id,
            "voice_settings": settings,
            "has_settings": settings is not None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get book voice settings: {str(e)}"
        )


@router.put("/{book_id}/voice-settings")
async def update_book_voice_settings(
    book_id: str,
    updates: BookVoiceSettingsUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update book-level voice settings.

    These settings persist across all reading sessions for this book.
    They override user defaults but can be overridden by session settings.

    Args:
        book_id: Book identifier
        updates: Voice settings to update
        user: Authenticated user

    Returns:
        Updated voice settings
    """
    user_id = user.get("id") or user.get("user_id")

    service = await get_book_voice_settings_service()

    try:
        result = await service.update_book_settings(
            book_id=book_id,
            user_id=user_id,
            updates=updates.model_dump(exclude_none=True)
        )
        return {
            "message": "Book voice settings updated",
            "book_id": book_id,
            "voice_settings": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update book voice settings: {str(e)}"
        )


@router.delete("/{book_id}/voice-settings")
async def clear_book_voice_settings(
    book_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Clear book-level voice settings, reverting to user defaults.

    Args:
        book_id: Book identifier
        user: Authenticated user

    Returns:
        Success message
    """
    user_id = user.get("id") or user.get("user_id")

    service = await get_book_voice_settings_service()

    try:
        cleared = await service.clear_book_settings(book_id, user_id)
        if cleared:
            return {
                "message": "Book voice settings cleared",
                "book_id": book_id
            }
        else:
            return {
                "message": "No book voice settings found to clear",
                "book_id": book_id
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear book voice settings: {str(e)}"
        )


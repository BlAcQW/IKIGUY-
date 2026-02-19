"""
Reading session routes.

API endpoints for reading sessions, progress tracking, and audio playback.
"""

from typing import List, Optional
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import Response

from app.core.database import Database
from app.core.auth import get_current_user
from app.services.reading_service import ReadingService
from app.services.tts_service import TTSService
from app.services.wallet_service import get_wallet_service as get_wallet_service_singleton
from app.services.leaderboard_service import LeaderboardService
from app.services.achievement_service import AchievementService
from app.services.streak_service import StreakService
from app.models.session import (
    ReadingSessionInDB,
    ReadingSessionUpdate,
    Bookmark,
    SessionVoiceSettingsUpdate
)
from app.models.book import BookChunk
from app.services.session_voice_settings_service import (
    get_session_voice_settings_service,
    EffectiveVoiceSettings
)
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reading", tags=["reading"])


# Background task for non-critical operations
async def process_listening_achievements_and_streaks(user_id: str):
    """
    Background task to process achievements and streaks.

    This runs asynchronously after the response is sent to the client,
    so it doesn't block the listening experience.

    Args:
        user_id: User ID to process
    """
    try:
        db = Database.get_database()

        # Check and award achievements
        try:
            achievement_service = AchievementService(db)
            newly_earned = await achievement_service.check_and_award_achievements(user_id)
            if newly_earned:
                logger.info(
                    f"Background task: User {user_id} earned {len(newly_earned)} achievements: "
                    f"{[ach.name for ach in newly_earned]}"
                )
        except Exception as ach_error:
            logger.error(f"Background task: Failed to check achievements for user {user_id}: {ach_error}")

        # Update daily listening streak
        try:
            streak_service = StreakService(db)
            streak = await streak_service.update_streak(user_id)
            if streak.current_days > 0:
                logger.info(f"Background task: User {user_id} streak: {streak.current_days} days")
        except Exception as streak_error:
            logger.error(f"Background task: Failed to update streak for user {user_id}: {streak_error}")

    except Exception as e:
        logger.error(f"Background task: Error processing achievements/streaks for user {user_id}: {e}")


# Request/Response Models
class SessionCreateRequest(BaseModel):
    """Request to create a reading session."""
    book_id: str


class BookmarkCreateRequest(BaseModel):
    """Request to add a bookmark."""
    chunk_index: int
    position_seconds: float = 0.0
    note: Optional[str] = None
    chapter_title: Optional[str] = None


class BookmarkUpdateRequest(BaseModel):
    """Request to update a bookmark."""
    note: Optional[str] = None


class ChunkAudioResponse(BaseModel):
    """Response with chunk audio URL."""
    chunk_index: int
    audio_url: Optional[str] = None
    audio_inline: bool = False  # If True, audio is in response body


# Dependency to get services
async def get_reading_service() -> ReadingService:
    """Get reading service instance."""
    db = Database.get_database()
    return ReadingService(db)


async def get_tts_service() -> TTSService:
    """Get TTS service instance."""
    return TTSService()


async def get_leaderboard_service() -> LeaderboardService:
    """Get leaderboard service instance."""
    db = Database.get_database()
    return LeaderboardService(db)


@router.post("/sessions", response_model=ReadingSessionInDB)
async def create_session(
    request: SessionCreateRequest,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Create a new reading session or return existing active session.

    Args:
        request: Session creation request
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        ReadingSessionInDB: Created or existing session
    """
    user_id = current_user.user_id

    session = await reading_service.create_session(
        user_id=user_id,
        book_id=request.book_id
    )

    return session


@router.get("/sessions/{session_id}", response_model=ReadingSessionInDB)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Get reading session by ID.

    Args:
        session_id: Session ID
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        ReadingSessionInDB: Session data
    """
    user_id = current_user.user_id

    session = await reading_service.get_session(
        session_id=session_id,
        user_id=user_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )

    return session


@router.put("/sessions/{session_id}", response_model=ReadingSessionInDB)
async def update_session(
    session_id: str,
    update: ReadingSessionUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service),
    wallet_service = Depends(get_wallet_service_singleton),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Update reading session progress.

    Args:
        session_id: Session ID
        update: Progress update data
        current_user: Authenticated user
        reading_service: Reading service instance
        wallet_service: Wallet service instance
        leaderboard_service: Leaderboard service instance

    Returns:
        ReadingSessionInDB: Updated session
    """
    user_id = current_user.user_id

    # Get old session to calculate listening delta
    old_session = await reading_service.get_session(
        session_id=session_id,
        user_id=user_id
    )

    if not old_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )

    # Get old listening time
    old_time = old_session.total_time_spent_minutes

    # Update session
    session = await reading_service.update_progress(
        session_id=session_id,
        user_id=user_id,
        update=update
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )

    # Record listening activity if time increased
    if update.total_time_spent_minutes is not None:
        new_time = update.total_time_spent_minutes
        listening_delta = new_time - old_time

        # Only record if actual listening occurred (delta > 0)
        if listening_delta > 0:
            # Batch transactions: Only create transaction every 5 minutes or on first listen
            now = datetime.utcnow()
            should_create_transaction = False
            accumulated_minutes = 0.0

            # Get the time that was tracked in the last transaction
            # Use old_session to get the last_transaction_time before this update
            # If last_transaction_time is not set, use 0 (first transaction)
            last_transaction_time = getattr(old_session, 'last_transaction_time', None) or 0.0
            
            # Calculate accumulated listening time since last transaction
            accumulated_minutes = new_time - last_transaction_time

            if not old_session.last_transaction_at:
                # First transaction for this session
                should_create_transaction = True
                accumulated_minutes = new_time  # All time is new
            else:
                # Check if 5 minutes have passed since last transaction OR
                # if accumulated time is >= 5 minutes
                time_since_last = (now - session.last_transaction_at).total_seconds()
                if time_since_last >= 300 or accumulated_minutes >= 5.0:  # 5 minutes = 300 seconds
                    should_create_transaction = True

            if should_create_transaction and accumulated_minutes > 0:
                try:
                    # Use cached book title from session (avoid redundant query)
                    book_title = session.book_title or "Unknown Book"

                    # Record listening time as FREE wallet transaction (no charge)
                    # Create transaction directly in database for tracking purposes
                    db = Database.get_database()
                    transaction_doc = {
                    "_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "amount": float(accumulated_minutes) * 0.10,  # Track cost but don't charge
                    "type": "debit",
                    "description": f"Listening: {book_title} - {accumulated_minutes:.1f} minutes (FREE)",
                    "metadata": {
                        "service": "inkwave_listening",
                        "book_id": session.book_id,
                        "book_title": book_title,
                        "duration_minutes": float(accumulated_minutes),
                        "rate_per_minute": 0.10,
                        "session_id": session_id,
                        "free": True
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                    }
                    await db.wallet_transactions.insert_one(transaction_doc)
                    logger.info(f"Tracked FREE listening: {user_id} - {accumulated_minutes:.1f} minutes for {book_title}")

                    # Update session's last_transaction_at and last_transaction_time
                    await reading_service.sessions_collection.update_one(
                        {"session_id": session_id},
                        {"$set": {
                            "last_transaction_at": now,
                            "last_transaction_time": new_time
                        }}
                    )
                    session.last_transaction_at = now
                    session.last_transaction_time = new_time

                    # Update user listening stats (denormalized cache)
                    await leaderboard_service.update_user_listening_stats(
                        user_id=user_id
                    )

                    # Process achievements and streaks in background (non-blocking)
                    background_tasks.add_task(
                        process_listening_achievements_and_streaks,
                        user_id=user_id
                    )

                    logger.info(
                        f"Recorded {accumulated_minutes} minutes of listening for user {user_id} "
                        f"on book {session.book_id}"
                    )

                except Exception as e:
                    # Log error but don't fail the session update
                    logger.error(
                        f"Failed to record listening activity: {e}",
                        exc_info=True
                    )
                    # Continue - session update succeeded even if wallet/stats failed

    return session


@router.post("/sessions/{session_id}/bookmark", response_model=ReadingSessionInDB)
async def add_bookmark(
    session_id: str,
    request: BookmarkCreateRequest,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Add a bookmark to the reading session.

    Args:
        session_id: Session ID
        request: Bookmark data
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        ReadingSessionInDB: Updated session with bookmark
    """
    user_id = current_user.user_id

    session = await reading_service.add_bookmark(
        session_id=session_id,
        user_id=user_id,
        chunk_index=request.chunk_index,
        position_seconds=request.position_seconds,
        note=request.note,
        chapter_title=request.chapter_title
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )

    return session


@router.put("/sessions/{session_id}/bookmark/{bookmark_id}", response_model=ReadingSessionInDB)
async def update_bookmark(
    session_id: str,
    bookmark_id: str,
    request: BookmarkUpdateRequest,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Update a bookmark's note.

    Args:
        session_id: Session ID
        bookmark_id: Bookmark ID
        request: Update data
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        ReadingSessionInDB: Updated session
    """
    user_id = current_user.user_id

    session = await reading_service.update_bookmark(
        session_id=session_id,
        user_id=user_id,
        bookmark_id=bookmark_id,
        note=request.note
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session or bookmark not found"
        )

    return session


@router.delete("/sessions/{session_id}/bookmark/{bookmark_id}", response_model=ReadingSessionInDB)
async def delete_bookmark(
    session_id: str,
    bookmark_id: str,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Delete a bookmark from the reading session.

    Args:
        session_id: Session ID
        bookmark_id: Bookmark ID
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        ReadingSessionInDB: Updated session
    """
    user_id = current_user.user_id

    session = await reading_service.delete_bookmark(
        session_id=session_id,
        user_id=user_id,
        bookmark_id=bookmark_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session or bookmark not found"
        )

    return session


@router.get("/sessions/{session_id}/bookmarks")
async def get_bookmarks(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Get all bookmarks for a reading session.

    Args:
        session_id: Session ID
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        List of bookmarks
    """
    user_id = current_user.user_id

    session = await reading_service.get_session(
        session_id=session_id,
        user_id=user_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )

    return {"bookmarks": session.bookmarks}


@router.get("/sessions/{session_id}/complete", response_model=ReadingSessionInDB)
async def mark_session_complete(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Mark reading session as completed.

    Args:
        session_id: Session ID
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        ReadingSessionInDB: Updated session
    """
    user_id = current_user.user_id

    session = await reading_service.mark_completed(
        session_id=session_id,
        user_id=user_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )

    return session


@router.get("/sessions", response_model=List[ReadingSessionInDB])
async def get_user_sessions(
    active_only: bool = False,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Get all reading sessions for the authenticated user.

    Args:
        active_only: Only return non-completed sessions
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        List[ReadingSessionInDB]: User's sessions
    """
    user_id = current_user.user_id

    sessions = await reading_service.get_user_sessions(
        user_id=user_id,
        active_only=active_only
    )

    return sessions


@router.get("/chunks/{book_id}/{chunk_index}", response_model=BookChunk)
async def get_chunk(
    book_id: str,
    chunk_index: int,
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service)
):
    """
    Get a specific book chunk by index.

    Args:
        book_id: Book ID
        chunk_index: Chunk index
        current_user: Authenticated user
        reading_service: Reading service instance

    Returns:
        BookChunk: Chunk data
    """
    chunk = await reading_service.get_chunk(
        book_id=book_id,
        chunk_index=chunk_index
    )

    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found"
        )

    return chunk


@router.get("/chunks/{book_id}/{chunk_index}/audio")
async def get_chunk_audio(
    book_id: str,
    chunk_index: int,
    voice: str = "alloy",
    current_user: dict = Depends(get_current_user),
    reading_service: ReadingService = Depends(get_reading_service),
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Get or generate audio for a book chunk.

    Args:
        book_id: Book ID
        chunk_index: Chunk index
        voice: TTS voice to use
        current_user: Authenticated user
        reading_service: Reading service instance
        tts_service: TTS service instance

    Returns:
        Audio file (MP3)
    """
    # Get chunk text
    chunk = await reading_service.get_chunk(
        book_id=book_id,
        chunk_index=chunk_index
    )

    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found"
        )

    # Use optimized text if available, otherwise original
    text = chunk.text_optimized or chunk.text

    # Optimize text for TTS
    text = tts_service.optimize_text_for_tts(text)

    # Generate audio
    try:
        audio_data = await tts_service.generate_chunk_audio(
            book_id=book_id,
            chunk_index=chunk_index,
            text=text,
            voice=voice
        )

        # TODO: Debit user wallet for TTS cost
        # cost = tts_service.calculate_cost(len(text))
        # await wallet_service.debit(user_id, cost)

        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=chunk_{chunk_index}.mp3"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio generation failed: {str(e)}"
        )


# Voice Settings Endpoints
@router.get("/sessions/{session_id}/voice-settings", response_model=EffectiveVoiceSettings)
async def get_session_voice_settings(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get effective voice settings for a reading session.

    Merges session overrides with user defaults and system defaults.
    Returns settings with source tracking (session, user, or system).

    Args:
        session_id: Reading session ID
        current_user: Authenticated user

    Returns:
        EffectiveVoiceSettings: Merged settings with source info
    """
    user_id = current_user.user_id

    voice_settings_service = await get_session_voice_settings_service()

    try:
        # Get book_id from session
        from app.core.database import get_db
        db = get_db()
        session = await db.reading_sessions.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        book_id = session.get("book_id") if session else None
        
        settings = await voice_settings_service.get_effective_settings(
            session_id=session_id,
            user_id=user_id,
            book_id=book_id
        )
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice settings: {str(e)}"
        )


@router.put("/sessions/{session_id}/voice-settings")
async def update_session_voice_settings(
    session_id: str,
    updates: SessionVoiceSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update session-level voice settings.

    These settings temporarily override user defaults for the duration
    of this reading session. They do not change permanent user preferences.

    Args:
        session_id: Reading session ID
        updates: Voice settings to override
        current_user: Authenticated user

    Returns:
        Updated voice settings document
    """
    user_id = current_user.user_id

    voice_settings_service = await get_session_voice_settings_service()

    try:
        result = await voice_settings_service.update_session_settings(
            session_id=session_id,
            user_id=user_id,
            updates=updates.model_dump(exclude_none=True)
        )
        return {
            "message": "Session voice settings updated",
            "voice_settings": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update voice settings: {str(e)}"
        )


@router.delete("/sessions/{session_id}/voice-settings")
async def clear_session_voice_settings(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Clear session voice settings, reverting to user defaults.

    Removes all session-level overrides, returning the session
    to use the user's default voice settings.

    Args:
        session_id: Reading session ID
        current_user: Authenticated user

    Returns:
        Success message
    """
    user_id = current_user.user_id

    voice_settings_service = await get_session_voice_settings_service()

    cleared = await voice_settings_service.clear_session_settings(
        session_id=session_id,
        user_id=user_id
    )

    if cleared:
        return {"message": "Session voice settings cleared, using user defaults"}
    else:
        return {"message": "No session voice settings to clear"}

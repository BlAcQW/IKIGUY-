"""
Background tasks for book processing.

Handles asynchronous PDF/EPUB processing to avoid HTTP timeouts.
"""

import logging
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.services.book_processing_service import BookProcessingService

logger = logging.getLogger(__name__)


async def process_book_background(
    book_id: str,
    file_path: str,
    book_metadata: Dict[str, Any],
    uploaded_by: str,
    use_ai_chapter_detection: bool = False
):
    """
    Background task to process a book file asynchronously.

    This function:
    1. Processes the PDF/EPUB file
    2. Extracts text and chunks
    3. Generates embeddings
    4. Updates book status as it progresses

    Progress updates are handled internally by BookProcessingService
    which updates the database with detailed stage/progress/message info.

    Args:
        book_id: Book identifier (pre-created by upload endpoint)
        file_path: Path to book file (must be persistent, not temp)
        book_metadata: Book metadata (title, author, description, cover_url)
        uploaded_by: User ID who uploaded the book
        use_ai_chapter_detection: If True, use Gemini AI for enhanced chapter detection
    """
    logger.info(f"📚 Starting background processing for book: {book_id}")
    logger.info(f"📄 File path: {file_path}")
    logger.info(f"📝 Metadata: title='{book_metadata.get('title')}', author='{book_metadata.get('author')}'")

    db = get_db()

    try:
        # Initialize processing service
        logger.info(f"🔧 [{book_id}] Initializing processing service...")
        processing_service = BookProcessingService()
        await processing_service.initialize()

        # Process the book file - pass book_id so it uses existing record
        # Progress updates are handled internally by process_book_file
        logger.info(f"🚀 [{book_id}] Starting book processing (AI chapters={'enabled' if use_ai_chapter_detection else 'disabled'})...")
        book = await processing_service.process_book_file(
            file_path=file_path,
            book_metadata=book_metadata,
            uploaded_by=uploaded_by,
            book_id=book_id,  # Use existing book record
            use_ai_chapter_detection=use_ai_chapter_detection
        )

        logger.info(f"✅ [{book_id}] Background processing completed successfully!")
        logger.info(f"📊 [{book_id}] Result: processed={book.processed}, chapters={len(book.chapters)}")

        # Trigger audio pre-generation in background
        if book.processed:
            try:
                logger.info(f"🎵 [{book_id}] Triggering audio pre-generation...")
                await trigger_audio_pregeneration_for_book(book_id, uploaded_by)
            except Exception as audio_error:
                logger.error(f"⚠️ [{book_id}] Failed to trigger audio pre-generation: {audio_error}")
                # Don't fail the whole processing if audio generation fails

    except Exception as e:
        logger.error(f"❌ [{book_id}] Background processing failed: {e}", exc_info=True)

        # Update status to error (in case process_book_file didn't catch it)
        try:
            await db.books.update_one(
                {"book_id": book_id},
                {
                    "$set": {
                        "processing_status": "error",
                        "processed": False,
                        "processing_stage": "failed",
                        "processing_progress": 0,
                        "processing_message": f"Processing failed: {str(e)[:100]}",
                        "processing_error": str(e)[:500],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as update_error:
            logger.error(f"❌ [{book_id}] Failed to update error status: {update_error}")

    finally:
        # Clean up uploaded file after processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 [{book_id}] Cleaned up uploaded file: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ [{book_id}] Failed to cleanup file {file_path}: {cleanup_error}")


async def trigger_audio_pregeneration_for_book(
    book_id: str,
    user_id: str,
    voice_settings: Optional[Dict[str, Any]] = None
) -> None:
    """
    Trigger audio pre-generation for a book after processing completes.
    
    Gets user's global voice settings or uses defaults (kokoro/am_michael).
    Runs in background without blocking.
    
    Args:
        book_id: Book identifier
        user_id: User ID who uploaded the book
        voice_settings: Optional voice settings override
    """
    try:
        from app.services.audio_pregeneration_service import (
            get_audio_pregeneration_service,
            trigger_audio_pregeneration
        )
        from app.services.session_voice_settings_service import (
            get_session_voice_settings_service
        )
        
        # Get user's global voice settings if not provided
        if voice_settings is None:
            try:
                session_service = await get_session_voice_settings_service()
                user_settings = await session_service.get_user_settings(user_id, "default")
                
                # Extract TTS settings from user settings
                tts_settings = user_settings.get("tts", {})
                voice_settings = {
                    "provider_id": tts_settings.get("provider") or tts_settings.get("default_provider") or "kokoro",
                    "voice_id": tts_settings.get("voice") or tts_settings.get("default_voice") or "am_michael",
                    "speed": tts_settings.get("speed", 1.0),
                    "language": "en"
                }
                
                logger.info(
                    f"🎵 [{book_id}] Using user voice settings: "
                    f"provider={voice_settings['provider_id']}, "
                    f"voice={voice_settings['voice_id']}"
                )
            except Exception as settings_error:
                logger.warning(
                    f"⚠️ [{book_id}] Failed to get user settings, using defaults: {settings_error}"
                )
                # Use defaults: kokoro/am_michael
                voice_settings = {
                    "provider_id": "kokoro",
                    "voice_id": "am_michael",
                    "speed": 1.0,
                    "language": "en"
                }
        
        # Trigger background audio generation
        await trigger_audio_pregeneration(
            book_id=book_id,
            user_id=user_id,
            voice_settings=voice_settings
        )
        
        logger.info(f"✅ [{book_id}] Audio pre-generation triggered successfully")
        
    except Exception as e:
        logger.error(f"❌ [{book_id}] Failed to trigger audio pre-generation: {e}", exc_info=True)

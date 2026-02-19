"""
Storage routes for serving audio files.

Serves voice clones, voice samples, and other media files from shared storage.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storage", tags=["storage"])

# Base storage directory
STORAGE_BASE = Path("/opt/kasaai/apps/shared/storage")


@router.get("/voice_clones/{filename}")
async def get_voice_clone(filename: str):
    """
    Serve voice clone audio files.

    Args:
        filename: Name of the voice clone file

    Returns:
        Audio file

    Raises:
        HTTPException: If file not found
    """
    file_path = STORAGE_BASE / "voice_clones" / filename

    if not file_path.exists():
        logger.warning(f"Voice clone file not found: {filename}")
        raise HTTPException(status_code=404, detail="Voice clone file not found")

    # Security check: Ensure file is within storage directory
    try:
        file_path.resolve().relative_to(STORAGE_BASE / "voice_clones")
    except ValueError:
        logger.error(f"Attempted path traversal: {filename}")
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=filename
    )


@router.get("/voice_samples/{filename}")
async def get_voice_sample(filename: str):
    """
    Serve voice sample audio files.

    Args:
        filename: Name of the voice sample file

    Returns:
        Audio file

    Raises:
        HTTPException: If file not found
    """
    file_path = STORAGE_BASE / "voice_samples" / filename

    if not file_path.exists():
        logger.warning(f"Voice sample file not found: {filename}")
        raise HTTPException(status_code=404, detail="Voice sample file not found")

    # Security check: Ensure file is within storage directory
    try:
        file_path.resolve().relative_to(STORAGE_BASE / "voice_samples")
    except ValueError:
        logger.error(f"Attempted path traversal: {filename}")
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=filename
    )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Serve general audio files.

    Args:
        filename: Name of the audio file

    Returns:
        Audio file

    Raises:
        HTTPException: If file not found
    """
    file_path = STORAGE_BASE / "audio" / filename

    if not file_path.exists():
        logger.warning(f"Audio file not found: {filename}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Security check: Ensure file is within storage directory
    try:
        file_path.resolve().relative_to(STORAGE_BASE / "audio")
    except ValueError:
        logger.error(f"Attempted path traversal: {filename}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Determine media type from file extension
    media_type = "audio/wav"
    if filename.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif filename.endswith(".ogg"):
        media_type = "audio/ogg"
    elif filename.endswith(".webm"):
        media_type = "audio/webm"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

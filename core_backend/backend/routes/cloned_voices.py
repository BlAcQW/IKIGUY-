"""
Cloned Voices Management Routes
API endpoints for managing voices cloned in the voice-lab
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..auth import get_current_user_mongo
from apps.shared.services.voice_library_service import (
    get_voice_library_service,
    VoiceCreate,
    VoiceGender,
    VoiceVisibility,
    AudioFormat
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cloned-voices", tags=["cloned-voices"])

# Voice lab clones directory
CLONES_DIR = Path("/opt/kasaai/apps/voice-lab/clones")

# Get service instance
voice_library_service = get_voice_library_service()


class ClonedVoiceInfo(BaseModel):
    """Information about a cloned voice file"""
    filename: str
    voice_name: str
    provider: str
    language: str
    timestamp: str
    file_path: str
    file_size: int
    duration: Optional[float] = None


class RegisterClonedVoiceRequest(BaseModel):
    """Request to register a cloned voice in the library"""
    filename: str = Field(..., description="Cloned voice filename")
    name: Optional[str] = Field(None, description="Custom name (defaults to voice_name)")
    description: Optional[str] = None
    gender: Optional[VoiceGender] = None
    tags: Optional[List[str]] = None
    visibility: VoiceVisibility = VoiceVisibility.PRIVATE


def parse_cloned_voice_filename(filename: str) -> Optional[ClonedVoiceInfo]:
    """
    Parse cloned voice filename to extract metadata.

    Format: {voice_name}_{provider}_{language}_{timestamp}.wav
    Example: archbishop_1_f5tts_eng_20251109_222527.wav
    """
    try:
        # Remove .wav extension
        name_without_ext = filename.replace('.wav', '')

        # Split by underscores
        parts = name_without_ext.split('_')

        if len(parts) < 4:
            return None

        # Extract timestamp (last 2 parts: YYYYMMDD_HHMMSS)
        timestamp = f"{parts[-2]}_{parts[-1]}"

        # Extract language (3rd from end)
        language = parts[-3]

        # Extract provider (4th from end)
        provider = parts[-4]

        # Voice name is everything before provider
        voice_name = '_'.join(parts[:-4])

        return ClonedVoiceInfo(
            filename=filename,
            voice_name=voice_name,
            provider=provider,
            language=language,
            timestamp=timestamp,
            file_path="",  # Will be set by caller
            file_size=0  # Will be set by caller
        )
    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {e}")
        return None


@router.get("/list")
async def list_cloned_voices(
    provider: Optional[str] = Query(None, description="Filter by provider (f5tts, styletts2, etc.)"),
    voice_name: Optional[str] = Query(None, description="Filter by voice name"),
    language: Optional[str] = Query(None, description="Filter by language (eng, twi)"),
    current_user = Depends(get_current_user_mongo)
):
    """
    List all available cloned voices from the voice-lab.

    Returns metadata for each cloned voice file including provider,
    voice name, language, and file information.
    """
    try:
        cloned_voices = []

        # Scan all provider directories
        if not CLONES_DIR.exists():
            return JSONResponse(content={
                "success": True,
                "message": "No cloned voices found",
                "voices": [],
                "total": 0
            })

        for provider_dir in CLONES_DIR.iterdir():
            if not provider_dir.is_dir():
                continue

            provider_name = provider_dir.name

            # Filter by provider if specified
            if provider and provider != provider_name:
                continue

            # Scan voice files in provider directory
            for voice_file in provider_dir.glob("*.wav"):
                info = parse_cloned_voice_filename(voice_file.name)

                if info:
                    # Apply filters
                    if voice_name and voice_name not in info.voice_name:
                        continue
                    if language and language != info.language:
                        continue

                    # Set file path and size
                    info.file_path = str(voice_file)
                    info.file_size = voice_file.stat().st_size

                    cloned_voices.append(info.dict())

        return JSONResponse(content={
            "success": True,
            "message": f"Found {len(cloned_voices)} cloned voices",
            "voices": cloned_voices,
            "total": len(cloned_voices)
        })

    except Exception as e:
        logger.error(f"Error listing cloned voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/play/{provider}/{filename}")
async def play_cloned_voice(
    provider: str,
    filename: str,
    current_user = Depends(get_current_user_mongo)
):
    """
    Stream a cloned voice audio file for playback.

    Returns the WAV file for the specified cloned voice.
    """
    try:
        voice_file = CLONES_DIR / provider / filename

        if not voice_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Cloned voice file not found: {filename}"
            )

        return FileResponse(
            voice_file,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Accept-Ranges": "bytes"
            }
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Voice file not found: {filename}"
        )
    except Exception as e:
        logger.error(f"Error playing cloned voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_cloned_voice(
    request: RegisterClonedVoiceRequest,
    current_user = Depends(get_current_user_mongo)
):
    """
    Register a cloned voice in the voice library.

    This makes the cloned voice available in the voice manager
    with proper metadata and organization assignment.
    """
    try:
        # Parse filename to get metadata
        info = parse_cloned_voice_filename(request.filename)

        if not info:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filename format: {request.filename}"
            )

        # Find the voice file
        voice_file = None
        for provider_dir in CLONES_DIR.iterdir():
            if provider_dir.is_dir():
                potential_file = provider_dir / request.filename
                if potential_file.exists():
                    voice_file = potential_file
                    break

        if not voice_file:
            raise HTTPException(
                status_code=404,
                detail=f"Voice file not found: {request.filename}"
            )

        # Create voice in library
        voice_name = request.name or f"{info.voice_name} ({info.provider.upper()}) - {info.language.upper()}"

        # Map language codes
        language_map = {
            "eng": "en",
            "twi": "tw",
            "en": "en",
            "tw": "tw"
        }
        language = language_map.get(info.language, info.language)

        # Determine gender from voice name (simple heuristic)
        gender = request.gender
        if not gender:
            female_names = ["juliet", "nana", "sarah", "emma"]
            male_names = ["archbishop", "adom", "george", "adam"]

            voice_lower = info.voice_name.lower()
            if any(name in voice_lower for name in female_names):
                gender = VoiceGender.FEMALE
            elif any(name in voice_lower for name in male_names):
                gender = VoiceGender.MALE

        voice_create = VoiceCreate(
            name=voice_name,
            description=request.description or f"Cloned voice using {info.provider.upper()} provider",
            provider=info.provider,
            gender=gender,
            language=language,
            accent="Ghanaian" if "archbishop" in info.voice_name.lower() else None,
            visibility=request.visibility,
            tags=request.tags or [info.provider, "cloned", language],
            categories=["cloned", "custom"],
            use_cases=["narration", "voiceover", "audiobook"],
            audio_file_path=str(voice_file),
            audio_format=AudioFormat.WAV,
            is_cloned=True,
            is_custom=True,
            metadata={
                "source": "voice-lab",
                "cloned_from": info.voice_name,
                "provider": info.provider,
                "language_code": info.language,
                "timestamp": info.timestamp,
                "original_filename": request.filename
            }
        )

        # Register in voice library
        voice = await voice_library_service.create_voice(
            voice_create,
            created_by_id=current_user["_id"],
            organization_id=current_user.get("organization_id")
        )

        return JSONResponse(content={
            "success": True,
            "message": f"Cloned voice '{voice_name}' registered successfully",
            "voice": voice.dict()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering cloned voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{provider}/{filename}")
async def download_cloned_voice(
    provider: str,
    filename: str,
    current_user = Depends(get_current_user_mongo)
):
    """Download a cloned voice file."""
    try:
        voice_file = CLONES_DIR / provider / filename

        if not voice_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Voice file not found: {filename}"
            )

        return FileResponse(
            voice_file,
            media_type="audio/wav",
            filename=filename
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Voice file not found: {filename}")
    except Exception as e:
        logger.error(f"Error downloading cloned voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

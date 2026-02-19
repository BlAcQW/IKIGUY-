"""
Audio Conversion Routes

API endpoints for converting audio between different formats.

Created: 2025-10-27
Sprint 4: Advanced Features (Phase 9)
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Literal, List

from ..services.audio_conversion_service import AudioConversionService, AudioFormat


router = APIRouter(prefix="/api/audio", tags=["audio-conversion"])

# Initialize service
audio_service = AudioConversionService()


class ConvertAudioRequest(BaseModel):
    """Request to convert audio format"""
    audio_base64: str
    source_format: AudioFormat
    target_format: AudioFormat
    bitrate: str = "192k"


class BatchConvertRequest(BaseModel):
    """Request to convert audio to multiple formats"""
    audio_base64: str
    source_format: AudioFormat
    target_formats: List[AudioFormat]
    bitrate: str = "192k"


class ConvertAudioResponse(BaseModel):
    """Response with converted audio"""
    audio_base64: str
    format: AudioFormat
    size_bytes: int


class BatchConvertResponse(BaseModel):
    """Response with multiple converted audio formats"""
    results: dict[AudioFormat, str]  # format -> base64 audio


@router.post("/convert", response_model=ConvertAudioResponse)
async def convert_audio(request: ConvertAudioRequest):
    """
    Convert audio from one format to another.

    Supported formats:
    - wav: Waveform Audio File (lossless)
    - mp3: MPEG Layer 3 (lossy, widely compatible)
    - ogg: Ogg Vorbis (lossy, open source)
    - flac: Free Lossless Audio Codec (lossless)
    - m4a: MPEG-4 Audio (lossy, Apple/iTunes)

    Bitrate options: "128k", "192k" (default), "256k", "320k"
    """
    try:
        # Convert audio
        converted_base64 = audio_service.convert_base64_audio(
            audio_base64=request.audio_base64,
            source_format=request.source_format,
            target_format=request.target_format,
            bitrate=request.bitrate,
        )

        # Get size
        import base64
        converted_bytes = base64.b64decode(converted_base64)

        return ConvertAudioResponse(
            audio_base64=converted_base64,
            format=request.target_format,
            size_bytes=len(converted_bytes),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/convert/batch", response_model=BatchConvertResponse)
async def batch_convert_audio(request: BatchConvertRequest):
    """
    Convert audio to multiple formats at once.

    This is more efficient than converting to each format individually,
    as the source audio is only loaded once.
    """
    try:
        import base64

        # Decode source audio
        audio_data = base64.b64decode(request.audio_base64)

        # Batch convert
        results_bytes = audio_service.batch_convert(
            audio_data=audio_data,
            source_format=request.source_format,
            target_formats=request.target_formats,
            bitrate=request.bitrate,
        )

        # Encode to base64
        results_base64 = {}
        for format, audio_bytes in results_bytes.items():
            if audio_bytes:
                results_base64[format] = base64.b64encode(audio_bytes).decode("utf-8")

        return BatchConvertResponse(results=results_base64)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch conversion failed: {str(e)}")


@router.post("/convert/upload")
async def convert_audio_upload(
    file: UploadFile = File(...),
    target_format: AudioFormat = "mp3",
    bitrate: str = "192k",
):
    """
    Convert uploaded audio file to target format.

    Returns the converted audio file for download.
    """
    try:
        # Read uploaded file
        audio_data = await file.read()

        # Detect source format from filename
        source_format = file.filename.split(".")[-1].lower()
        if source_format not in ["wav", "mp3", "ogg", "flac", "m4a"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source format: {source_format}",
            )

        # Convert
        converted_data = audio_service.convert_audio(
            audio_data=audio_data,
            source_format=source_format,
            target_format=target_format,
            bitrate=bitrate,
        )

        # Determine MIME type
        mime_types = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
        }

        return Response(
            content=converted_data,
            media_type=mime_types.get(target_format, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="converted.{target_format}"'
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload conversion failed: {str(e)}")


@router.get("/info")
async def get_supported_formats():
    """
    Get information about supported audio formats.
    """
    return {
        "formats": {
            "wav": {
                "name": "Waveform Audio",
                "extension": ".wav",
                "type": "lossless",
                "description": "Uncompressed audio, highest quality, large file size",
                "mime_type": "audio/wav",
            },
            "mp3": {
                "name": "MPEG Layer 3",
                "extension": ".mp3",
                "type": "lossy",
                "description": "Compressed audio, widely compatible, good quality",
                "mime_type": "audio/mpeg",
                "bitrate_options": ["128k", "192k", "256k", "320k"],
            },
            "ogg": {
                "name": "Ogg Vorbis",
                "extension": ".ogg",
                "type": "lossy",
                "description": "Open-source compressed audio, good quality",
                "mime_type": "audio/ogg",
                "bitrate_options": ["128k", "192k", "256k", "320k"],
            },
            "flac": {
                "name": "Free Lossless Audio Codec",
                "extension": ".flac",
                "type": "lossless",
                "description": "Lossless compression, smaller than WAV, perfect quality",
                "mime_type": "audio/flac",
            },
            "m4a": {
                "name": "MPEG-4 Audio",
                "extension": ".m4a",
                "type": "lossy",
                "description": "Apple/iTunes format, good quality and compatibility",
                "mime_type": "audio/mp4",
                "bitrate_options": ["128k", "192k", "256k", "320k"],
            },
        }
    }

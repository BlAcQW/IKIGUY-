"""
Voice Creation API Endpoints for Kasa AI Voice Studio
Handles voice cloning, training, and management
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import numpy as np
import soundfile as sf
import io

from ..services.voice_creation_service import VoiceCreationService
from ..auth import get_current_account

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/voice", tags=["voice_creation"])

# Initialize service
voice_service = VoiceCreationService()

# Request models
class VoiceCloneRequest(BaseModel):
    name: str
    description: str = ""
    language: str = "en"
    accent: str = "neutral"
    gender: str = "neutral"

class VoiceTrainRequest(BaseModel):
    name: str
    description: str = ""
    language: str
    dataset_id: str
    training_config: Dict[str, Any] = {
        "epochs": 1000,
        "batch_size": 8,
        "learning_rate": 0.0001
    }

class VoiceSynthesisRequest(BaseModel):
    voice_id: str
    text: str
    language: Optional[str] = None

# Response models
class VoiceResponse(BaseModel):
    id: str
    name: str
    description: str
    language: str
    provider: str
    type: str
    status: str
    created_at: float
    user_id: Optional[str] = None

class TrainingProgressResponse(BaseModel):
    voice_id: str
    status: str
    progress: int
    error: Optional[str] = None

@router.post("/clone", response_model=VoiceResponse)
async def clone_voice(
    request: VoiceCloneRequest,
    audio_file: UploadFile = File(...),
    current_user: Optional[Dict] = Depends(get_current_account)
):
    """Clone a voice from uploaded audio file"""
    
    try:
        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio file
        audio_data = await audio_file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Get user ID
        user_id = current_user.get("id") if current_user else None
        
        # Clone voice
        voice_metadata = await voice_service.clone_voice_from_audio(
            audio_file=audio_data,
            voice_name=request.name,
            language=request.language,
            description=request.description,
            user_id=user_id
        )
        
        return VoiceResponse(**voice_metadata)
        
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")

@router.post("/train", response_model=VoiceResponse)
async def train_voice(
    request: VoiceTrainRequest,
    current_user: Optional[Dict] = Depends(get_current_account)
):
    """Train a voice using selected dataset"""
    
    try:
        # Get user ID
        user_id = current_user.get("id") if current_user else None
        
        # Start training
        voice_metadata = await voice_service.train_voice_from_dataset(
            dataset_id=request.dataset_id,
            voice_name=request.name,
            language=request.language,
            training_config=request.training_config,
            user_id=user_id
        )
        
        return VoiceResponse(**voice_metadata)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Voice training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice training failed: {str(e)}")

@router.post("/synthesize")
async def synthesize_speech(request: VoiceSynthesisRequest):
    """Synthesize speech using a custom voice"""
    
    try:
        # Generate audio
        audio_data, sample_rate = await voice_service.synthesize_with_voice(
            voice_id=request.voice_id,
            text=request.text,
            language=request.language
        )
        
        # Convert to audio stream
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(audio_buffer.read()),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=synthesized_speech.wav"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@router.get("/datasets")
async def get_available_datasets():
    """Get list of available training datasets"""
    
    try:
        datasets = voice_service.get_available_datasets()
        return {"datasets": datasets}
        
    except Exception as e:
        logger.error(f"Failed to get datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get datasets: {str(e)}")

@router.get("/{voice_id}/info", response_model=VoiceResponse)
async def get_voice_info(voice_id: str):
    """Get voice metadata and info"""
    
    try:
        voice_info = await voice_service.get_voice_info(voice_id)
        return VoiceResponse(**voice_info)
        
    except Exception as e:
        logger.error(f"Failed to get voice info: {e}")
        raise HTTPException(status_code=404, detail=f"Voice not found: {str(e)}")

@router.get("/{voice_id}/progress", response_model=TrainingProgressResponse)
async def get_training_progress(voice_id: str):
    """Get training progress for a voice"""
    
    try:
        progress = await voice_service.get_training_progress(voice_id)
        return TrainingProgressResponse(**progress)
        
    except Exception as e:
        logger.error(f"Failed to get training progress: {e}")
        raise HTTPException(status_code=404, detail=f"Voice not found: {str(e)}")

@router.get("/user/{user_id}")
async def list_user_voices(
    user_id: str,
    current_user: Optional[Dict] = Depends(get_current_account)
):
    """List all voices created by a user"""
    
    try:
        # Check authorization (user can only see their own voices)
        if current_user and current_user.get("id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        voices = await voice_service.list_user_voices(user_id)
        return {"voices": voices}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list user voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")

@router.delete("/{voice_id}")
async def delete_voice(
    voice_id: str,
    current_user: Optional[Dict] = Depends(get_current_account)
):
    """Delete a custom voice"""
    
    try:
        # Get user ID
        user_id = current_user.get("id") if current_user else None
        
        # Delete voice
        success = await voice_service.delete_voice(voice_id, user_id)
        
        if success:
            return {"message": f"Voice {voice_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete voice")
            
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete voice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete voice: {str(e)}")

@router.get("/{voice_id}/download")
async def download_voice(
    voice_id: str,
    current_user: Optional[Dict] = Depends(get_current_account)
):
    """Download voice files as zip"""
    
    try:
        # This would implement voice file packaging and download
        # For now, return a placeholder
        raise HTTPException(status_code=501, detail="Download functionality coming soon")
        
    except Exception as e:
        logger.error(f"Failed to download voice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download voice: {str(e)}")

# WebSocket endpoint for real-time training updates
@router.websocket("/{voice_id}/training-updates")
async def training_updates_websocket(websocket, voice_id: str):
    """WebSocket endpoint for real-time training progress updates"""
    
    try:
        await websocket.accept()
        
        # Monitor training progress
        while True:
            try:
                progress = await voice_service.get_training_progress(voice_id)
                await websocket.send_json(progress)
                
                # Stop monitoring if training is complete
                if progress["status"] in ["ready", "failed"]:
                    break
                    
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
        
        await websocket.close()
        
    except Exception as e:
        logger.error(f"WebSocket connection failed: {e}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for voice creation service"""
    
    try:
        # Check if models are loaded
        await voice_service.initialize_models()
        
        return {
            "status": "healthy",
            "service": "voice_creation",
            "models_loaded": voice_service.xtts_model is not None,
            "available_datasets": len(voice_service.available_datasets)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "voice_creation",
            "error": str(e)
        }
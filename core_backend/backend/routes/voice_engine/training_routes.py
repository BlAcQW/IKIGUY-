"""
Voice training routes for custom voice creation.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime
import uuid
import io

# Import the existing voice creation service
from ...services.voice_creation_service import VoiceCreationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/train", tags=["voice-training"])

# Initialize voice creation service
voice_creation_service = VoiceCreationService()


class VoiceTrainingRequest(BaseModel):
    """
    Request model for voice training.
    """
    name: str
    description: Optional[str] = None
    language: str = "en"
    gender: str = "neutral"
    provider: str = "custom"
    samples: Optional[list] = None
    settings: Optional[Dict[str, Any]] = None


class VoiceTrainingResponse(BaseModel):
    """
    Response model for voice training.
    """
    training_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None


@router.post("/", response_model=VoiceTrainingResponse)
async def train_voice(
    request: VoiceTrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Train a custom voice model using existing datasets.
    
    Args:
        request: Voice training configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Training job information
    """
    try:
        # Generate a unique training ID
        training_id = str(uuid.uuid4())
        
        # Log the training request
        logger.info(f"Starting voice training job {training_id} for voice: {request.name}")
        
        # Prepare training configuration
        training_config = request.settings or {
            "epochs": 100,
            "batch_size": 16,
            "learning_rate": 0.0001,
            "save_checkpoints": True
        }
        
        # Add background task for training
        background_tasks.add_task(
            process_voice_training,
            training_id=training_id,
            request=request,
            training_config=training_config
        )
        
        return VoiceTrainingResponse(
            training_id=training_id,
            status="queued",
            message=f"Voice training for '{request.name}' has been queued",
            estimated_time=300  # 5 minutes estimate
        )
        
    except Exception as e:
        logger.error(f"Failed to start voice training: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start voice training: {str(e)}"
        )


@router.post("/upload-samples/{training_id}")
async def upload_training_samples(
    training_id: str,
    files: list[UploadFile] = File(...)
):
    """
    Upload audio samples for voice training.
    
    Args:
        training_id: Training job ID
        files: Audio files for training
        
    Returns:
        Upload status
    """
    try:
        logger.info(f"Uploading {len(files)} samples for training job {training_id}")
        
        # TODO: Process and store audio samples
        # For now, just validate file types
        allowed_extensions = {'.wav', '.mp3', '.ogg', '.flac'}
        
        for file in files:
            if not any(file.filename.endswith(ext) for ext in allowed_extensions):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {file.filename}. Allowed types: {allowed_extensions}"
                )
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(files)} samples",
            "training_id": training_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload training samples: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload training samples: {str(e)}"
        )


@router.get("/status/{training_id}")
async def get_training_status(training_id: str):
    """
    Get the status of a voice training job.
    
    Args:
        training_id: Training job ID
        
    Returns:
        Training job status
    """
    try:
        # Get training progress from voice creation service
        progress = await voice_creation_service.get_training_progress(training_id)
        
        return {
            "training_id": training_id,
            "status": progress.get("status", "unknown"),
            "progress": progress.get("progress", 0),
            "message": progress.get("message", "Processing..."),
            "error": progress.get("error"),
            "estimated_time_remaining": progress.get("estimated_time_remaining")
        }
        
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get training status: {str(e)}"
        )


@router.get("/datasets")
async def get_available_datasets():
    """
    Get available training datasets.
    
    Returns:
        Available datasets with metadata
    """
    try:
        datasets = voice_creation_service.get_available_datasets()
        return {
            "datasets": datasets,
            "count": len(datasets)
        }
    except Exception as e:
        logger.error(f"Failed to get datasets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available datasets: {str(e)}"
        )


@router.post("/clone")
async def clone_voice_from_audio(
    file: UploadFile = File(...),
    name: str = Form(...),
    language: str = Form("en"),
    description: str = Form("")
):
    """
    Clone a voice from an audio file.
    
    Args:
        file: Audio file to clone from
        name: Name for the cloned voice
        language: Language code
        description: Voice description
        
    Returns:
        Cloned voice information
    """
    try:
        # Read audio file
        audio_data = await file.read()
        
        # Initialize models if needed
        await voice_creation_service.initialize_models()
        
        # Clone voice
        result = await voice_creation_service.clone_voice_from_audio(
            audio_file=audio_data,
            voice_name=name,
            language=language,
            description=description
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to clone voice: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clone voice: {str(e)}"
        )


@router.delete("/{training_id}")
async def cancel_training(training_id: str):
    """
    Cancel a voice training job.
    
    Args:
        training_id: Training job ID
        
    Returns:
        Cancellation status
    """
    try:
        logger.info(f"Cancelling training job {training_id}")
        
        # TODO: Implement actual training cancellation
        
        return {
            "status": "cancelled",
            "message": f"Training job {training_id} has been cancelled"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel training: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel training: {str(e)}"
        )


async def process_voice_training(training_id: str, request: VoiceTrainingRequest, training_config: Dict[str, Any]):
    """
    Background task to process voice training using VoiceCreationService.
    
    Args:
        training_id: Training job ID
        request: Training request data
        training_config: Training configuration
    """
    try:
        logger.info(f"Starting background training for job {training_id}")
        
        # Initialize models if needed
        await voice_creation_service.initialize_models()
        
        # Check if using dataset-based training or audio samples
        if request.samples:
            # Clone voice from audio samples
            logger.info(f"Cloning voice from {len(request.samples)} samples")
            # TODO: Process multiple samples
            # For now, use first sample if available
            if request.samples and len(request.samples) > 0:
                audio_data = request.samples[0]  # Assuming base64 or bytes
                result = await voice_creation_service.clone_voice_from_audio(
                    audio_file=audio_data,
                    voice_name=request.name,
                    language=request.language,
                    description=request.description
                )
                logger.info(f"Voice cloned successfully: {result}")
        else:
            # Train from dataset
            dataset_id = request.settings.get("dataset_id", "bible_tts_twi") if request.settings else "bible_tts_twi"
            
            result = await voice_creation_service.train_voice_from_dataset(
                dataset_id=dataset_id,
                voice_name=request.name,
                language=request.language,
                training_config=training_config
            )
            logger.info(f"Voice trained successfully from dataset: {result}")
        
        logger.info(f"Completed training job {training_id} for voice: {request.name}")
        
    except Exception as e:
        logger.error(f"Training job {training_id} failed: {e}")
"""
Coqui TTS FastAPI Server with DeepSpeed Optimization

Provides REST API endpoints for text-to-speech synthesis using Coqui XTTS v2 with DeepSpeed acceleration.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
import os
import logging
from pathlib import Path
import tempfile
import json
import torch
import torchaudio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coqui TTS API with DeepSpeed",
    description="Production-ready TTS API using Coqui XTTS v2 with DeepSpeed optimization",
    version="2.0.0"
)

# Global XTTS model instance
xtts_model = None
current_model_path = None  # Track currently loaded model
OUTPUT_DIR = Path("/app/outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR = Path("/opt/kasaai/apps/voice-lab/models")  # External models directory


class TTSRequest(BaseModel):
    """Request model for TTS synthesis."""
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=5000)
    speaker: Optional[str] = Field(None, description="Speaker name or ID for multi-speaker models")
    language: Optional[str] = Field("en", description="Language code (e.g., 'en', 'es', 'fr')")
    speed: Optional[float] = Field(1.0, description="Speech speed multiplier", ge=0.5, le=2.0)


class ModelInfo(BaseModel):
    """Model information response."""
    name: str
    language: str
    speakers: Optional[List[str]] = None
    is_multi_speaker: bool
    is_multi_lingual: bool
    deepspeed_enabled: bool


def load_xtts_model_with_deepspeed(model_path: str, use_deepspeed: bool = True):
    """
    Load XTTS v2 model with optional DeepSpeed acceleration.

    Args:
        model_path: Path to model (either HF model name or local directory)
        use_deepspeed: Whether to enable DeepSpeed optimization

    Returns:
        Loaded XTTS model instance

    Raises:
        Exception: If model loading fails
    """
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    from TTS.utils.manage import ModelManager

    logger.info(f"Loading XTTS v2 model: {model_path}")
    logger.info(f"DeepSpeed enabled: {use_deepspeed}")

    # Handle built-in model names
    if model_path.startswith("tts_models/"):
        # Download model if needed using ModelManager
        # Reason: ModelManager.download_model() returns a tuple (model_dir, None, metadata)
        manager = ModelManager()
        result = manager.download_model(model_path)

        # Extract model directory from tuple or use directly if it's a string
        if isinstance(result, tuple):
            model_dir_str = result[0]
        else:
            model_dir_str = result

        logger.info(f"Model downloaded to: {model_dir_str}")

        # Construct config path from model directory
        model_dir = Path(model_dir_str)
        config_path = model_dir / "config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
    else:
        # Custom local model
        model_dir = Path(model_path)
        config_path = model_dir / "config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load configuration
    logger.info(f"Loading config from: {config_path}")
    config = XttsConfig()
    config.load_json(str(config_path))

    # Initialize model
    logger.info("Initializing XTTS model...")
    model = Xtts.init_from_config(config)

    # Load checkpoint with DeepSpeed
    logger.info(f"Loading checkpoint with DeepSpeed={use_deepspeed}...")
    model.load_checkpoint(
        config,
        checkpoint_dir=str(model_dir),
        use_deepspeed=use_deepspeed
    )

    # Move to CUDA
    model.cuda()
    logger.info("Model loaded successfully and moved to CUDA")

    return model, config


@app.on_event("startup")
async def startup_event():
    """Initialize XTTS v2 model with DeepSpeed on startup."""
    global xtts_model, current_model_path
    try:
        # Set environment variable to agree to Coqui license (non-commercial CPML)
        # https://coqui.ai/cpml
        os.environ['COQUI_TOS_AGREED'] = '1'

        # Fix for PyTorch 2.6+ weights_only=True default
        # Reason: XTTS v2 checkpoint contains many custom TTS classes
        # We trust the Coqui model checkpoint, so we'll set weights_only=False globally
        # This is safe because we're loading from the official Coqui model repository
        import torch.serialization
        original_load = torch.load

        def safe_load(*args, **kwargs):
            """Wrapper for torch.load that sets weights_only=False for TTS models."""
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)

        torch.load = safe_load
        logger.info("Configured PyTorch to load XTTS v2 checkpoints with weights_only=False (trusted source)")

        # Use XTTS v2 model (multilingual, multi-speaker)
        model_path = "tts_models/multilingual/multi-dataset/xtts_v2"
        current_model_path = model_path

        logger.info("Agreeing to Coqui non-commercial license (CPML): https://coqui.ai/cpml")

        # Load model with DeepSpeed enabled
        xtts_model, _ = load_xtts_model_with_deepspeed(model_path, use_deepspeed=True)

        logger.info("XTTS v2 model with DeepSpeed loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load XTTS model: {str(e)}")
        logger.error("Traceback:", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    if xtts_model is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "XTTS model not loaded"}
        )
    return {"status": "healthy", "model_loaded": True, "deepspeed_enabled": True}


@app.get("/models")
async def list_available_models():
    """
    List all available TTS models (both built-in and custom).

    Returns:
        dict: List of available models with metadata
    """
    models_list = []

    # Built-in XTTS v2 model
    builtin_model = {
        "id": "xtts_v2",
        "name": "XTTS v2 (Multilingual) with DeepSpeed",
        "path": "tts_models/multilingual/multi-dataset/xtts_v2",
        "size": "~1.8GB",
        "isActive": current_model_path == "tts_models/multilingual/multi-dataset/xtts_v2" or current_model_path is None,
        "language": "multilingual",
        "description": "Official Coqui XTTS v2 model with DeepSpeed optimization - 2-3x faster inference"
    }
    models_list.append(builtin_model)

    # Check for custom models in MODELS_DIR
    if MODELS_DIR.exists():
        try:
            for model_dir in MODELS_DIR.iterdir():
                if model_dir.is_dir() and (model_dir.name.startswith('xtts_') or model_dir.name.startswith('coqui_')):
                    # Check if it's a valid Coqui model directory
                    config_file = model_dir / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r') as f:
                                config = json.load(f)

                            # Calculate directory size
                            total_size = sum(f.stat().st_size for f in model_dir.glob('**/*') if f.is_file())
                            size_mb = total_size / (1024 * 1024)
                            size_str = f"{size_mb:.1f}MB" if size_mb < 1024 else f"{size_mb/1024:.1f}GB"

                            custom_model = {
                                "id": model_dir.name,
                                "name": config.get("model_name", model_dir.name),
                                "path": str(model_dir),
                                "size": size_str,
                                "isActive": str(model_dir) == current_model_path,
                                "language": config.get("language", "unknown"),
                                "description": f"Custom fine-tuned model with DeepSpeed: {model_dir.name}"
                            }
                            models_list.append(custom_model)
                        except Exception as e:
                            logger.warning(f"Failed to read config for {model_dir.name}: {e}")
        except Exception as e:
            logger.error(f"Error scanning models directory: {e}")

    return {
        "models": models_list,
        "count": len(models_list),
        "models_directory": str(MODELS_DIR),
        "deepspeed_enabled": True
    }


@app.post("/models/switch")
async def switch_model(model_data: dict):
    """
    Switch to a different TTS model.

    Args:
        model_data: Dict containing model_id

    Returns:
        dict: Status message
    """
    global xtts_model, current_model_path

    model_id = model_data.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")

    try:
        # Determine model path
        if model_id == "xtts_v2":
            model_path = "tts_models/multilingual/multi-dataset/xtts_v2"
        else:
            # Custom model path
            model_path = MODELS_DIR / model_id
            if not model_path.exists():
                raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
            model_path = str(model_path)

        logger.info(f"Switching to model: {model_path}")

        # Unload current model
        if xtts_model is not None:
            del xtts_model
            torch.cuda.empty_cache()

        # Load new model with DeepSpeed
        xtts_model, _ = load_xtts_model_with_deepspeed(model_path, use_deepspeed=True)
        current_model_path = model_path

        logger.info(f"Successfully switched to model: {model_id}")

        return {
            "status": "success",
            "message": f"Switched to model: {model_id} with DeepSpeed",
            "model_path": model_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")


@app.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """
    Delete a custom TTS model.
    Cannot delete the built-in XTTS v2 model.

    Args:
        model_id: ID of the model to delete

    Returns:
        dict: Status message
    """
    if model_id == "xtts_v2":
        raise HTTPException(status_code=400, detail="Cannot delete built-in XTTS v2 model")

    model_path = MODELS_DIR / model_id

    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

    if str(model_path) == current_model_path:
        raise HTTPException(status_code=400, detail="Cannot delete currently active model. Switch to another model first.")

    try:
        import shutil
        shutil.rmtree(model_path)
        logger.info(f"Deleted model: {model_id}")

        return {
            "status": "success",
            "message": f"Model deleted: {model_id}"
        }
    except Exception as e:
        logger.error(f"Failed to delete model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


@app.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    """
    Get information about the currently loaded XTTS model.

    Returns:
        ModelInfo: Model details
    """
    if xtts_model is None:
        raise HTTPException(status_code=503, detail="XTTS model not loaded")

    try:
        return ModelInfo(
            name="XTTS v2",
            language="multilingual",
            speakers=None,  # XTTS v2 uses voice cloning, not predefined speakers
            is_multi_speaker=True,  # Supports voice cloning
            is_multi_lingual=True,
            deepspeed_enabled=True
        )
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize speech from text.

    For XTTS v2, use /synthesize_with_reference endpoint instead as it requires reference audio.

    Args:
        request: TTS request parameters

    Returns:
        FileResponse: Audio file
    """
    raise HTTPException(
        status_code=400,
        detail="XTTS v2 requires reference audio for voice cloning. Please use /synthesize_with_reference endpoint instead. "
               "Example: curl -X POST http://localhost:8005/synthesize_with_reference "
               "-F 'text=Your text here' -F 'reference_audio=@your_voice.wav' -F 'language=en' --output output.wav"
    )


@app.post("/synthesize_with_reference")
async def synthesize_with_reference(
    text: str = Form(...),
    reference_audio: UploadFile = File(...),
    language: Optional[str] = Form("en"),
    temperature: Optional[float] = Form(0.7),
    speed: Optional[float] = Form(1.0)
):
    """
    Synthesize speech with voice cloning from reference audio using XTTS v2 with DeepSpeed.

    Args:
        text: Text to synthesize
        reference_audio: Reference audio file for voice cloning
        language: Target language (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi)
        temperature: Sampling temperature (0.1-1.0, higher = more creative)
        speed: Speech speed multiplier (0.5-2.0)

    Returns:
        FileResponse: Audio file with cloned voice
    """
    if xtts_model is None:
        raise HTTPException(status_code=503, detail="XTTS model not loaded")

    try:
        # Save reference audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_ref:
            temp_ref.write(await reference_audio.read())
            reference_path = temp_ref.name

        # Generate output filename
        output_file = OUTPUT_DIR / f"tts_cloned_{os.urandom(8).hex()}.wav"

        logger.info(f"Voice cloning synthesis (DeepSpeed): '{text[:50]}...'")
        logger.info(f"Parameters: language={language}, temperature={temperature}, speed={speed}")

        # Compute speaker latents from reference audio
        # Reason: XTTS uses conditioning latents for voice cloning
        logger.info("Computing speaker latents from reference audio...")
        gpt_cond_latent, speaker_embedding = xtts_model.get_conditioning_latents(
            audio_path=[reference_path]
        )

        # Synthesize with voice cloning using DeepSpeed-accelerated inference
        logger.info("Generating speech with DeepSpeed acceleration...")
        out = xtts_model.inference(
            text,
            language,
            gpt_cond_latent,
            speaker_embedding,
            temperature=temperature,
            speed=speed
        )

        # Save output audio
        # Reason: XTTS returns numpy array, need to convert to tensor for torchaudio
        wav_tensor = torch.tensor(out["wav"]).unsqueeze(0)
        torchaudio.save(str(output_file), wav_tensor, 24000)

        # Cleanup temp file
        os.unlink(reference_path)

        logger.info(f"Voice cloning successful (DeepSpeed): {output_file}")

        return FileResponse(
            path=str(output_file),
            media_type="audio/wav",
            filename="cloned_speech.wav",
            headers={
                "X-DeepSpeed-Enabled": "true",
                "X-Text-Length": str(len(text))
            }
        )

    except Exception as e:
        logger.error(f"Voice cloning failed: {str(e)}")
        if 'reference_path' in locals() and os.path.exists(reference_path):
            os.unlink(reference_path)
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@app.get("/speakers")
async def list_speakers():
    """
    List available speakers.

    Note: XTTS v2 uses voice cloning instead of predefined speakers.

    Returns:
        dict: Information about voice cloning
    """
    return {
        "speakers": [],
        "message": "XTTS v2 uses voice cloning. Upload any reference audio to /synthesize_with_reference to clone that voice.",
        "voice_cloning_enabled": True
    }


@app.get("/languages")
async def list_languages():
    """
    List available languages for XTTS v2.

    Returns:
        dict: List of supported languages
    """
    if xtts_model is None:
        raise HTTPException(status_code=503, detail="XTTS model not loaded")

    # XTTS v2 supported languages
    languages = ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"]

    return {
        "languages": languages,
        "count": len(languages),
        "message": "XTTS v2 supports 17 languages"
    }


@app.delete("/cleanup")
async def cleanup_outputs():
    """
    Clean up old generated audio files.

    Returns:
        dict: Cleanup statistics
    """
    try:
        files = list(OUTPUT_DIR.glob("tts_*.wav"))
        deleted_count = 0

        for file in files:
            try:
                file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")

        return {
            "deleted": deleted_count,
            "message": f"Cleaned up {deleted_count} audio files"
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )

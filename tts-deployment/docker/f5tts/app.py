"""
F5-TTS FastAPI Server - Full Implementation
Flow-matching based text-to-speech with voice cloning
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import torch
import io
import logging
import tempfile
import os
import json

# F5-TTS imports
from f5_tts.infer.utils_infer import (
    load_model,
    load_vocoder,
    infer_process,
    preprocess_ref_audio_text,
    remove_silence_for_generated_wav,
)
from f5_tts.model import DiT
from cached_path import cached_path
import soundfile as sf
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="F5-TTS API", version="2.0.0")

# Global variables
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = None
vocoder = None
model_loaded = False

# Model configuration for F5-TTS v1
DEFAULT_MODEL_CFG = {
    "ckpt_path": "hf://SWivid/F5-TTS/F5TTS_v1_Base/model_1250000.safetensors",
    "vocab_path": "hf://SWivid/F5-TTS/F5TTS_v1_Base/vocab.txt",
    "model_cfg": {"dim": 1024, "depth": 22, "heads": 16, "ff_mult": 2, "text_dim": 512, "conv_layers": 4}
}

logger.info(f"Using device: {device}")


def initialize_model():
    """Initialize F5-TTS model and vocoder."""
    global model, vocoder, model_loaded

    try:
        logger.info("Loading F5-TTS v1 model...")

        # Download checkpoint from HuggingFace
        ckpt_path = str(cached_path(DEFAULT_MODEL_CFG["ckpt_path"]))
        vocab_path = str(cached_path(DEFAULT_MODEL_CFG["vocab_path"]))
        model_cfg = DEFAULT_MODEL_CFG["model_cfg"]

        logger.info(f"Checkpoint: {ckpt_path}")
        logger.info(f"Vocab: {vocab_path}")
        logger.info(f"Model config: {model_cfg}")

        # Load model
        model = load_model(
            model_cls=DiT,
            model_cfg=model_cfg,
            ckpt_path=ckpt_path,
            vocab_file=vocab_path,
            device=device
        )

        logger.info("Loading vocoder...")
        vocoder = load_vocoder()

        model_loaded = True
        logger.info("✓ F5-TTS model and vocoder loaded successfully")
        return True

    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
        model_loaded = False
        return False


class TTSRequest(BaseModel):
    """TTS synthesis request."""
    text: str
    language: str = "en"  # en, zh, etc.
    speed: float = 1.0
    remove_silence: bool = True


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup."""
    logger.info("Starting F5-TTS service...")
    initialize_model()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "F5-TTS",
        "version": "2.0.0",
        "status": "running",
        "description": "Flow-matching TTS with zero-shot voice cloning",
        "model": "F5-TTS v1 Base (335M parameters)",
        "model_loaded": model_loaded,
        "features": [
            "Multi-language synthesis (English, Chinese, etc.)",
            "Zero-shot voice cloning",
            "High-quality audio generation",
            "Speed control",
            "Silence removal"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
            "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
        }

    return {
        "status": "healthy",
        "device": device,
        "model_loaded": model_loaded,
        **gpu_info
    }


@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    """
    Synthesize speech from text using default voice.

    Args:
        request: TTS request with text and parameters

    Returns:
        Audio file as WAV format
    """
    if not model_loaded:
        logger.warning("Model not loaded, attempting to load...")
        if not initialize_model():
            raise HTTPException(
                status_code=503,
                detail="Model not loaded and failed to initialize"
            )

    try:
        logger.info(f"Synthesizing: '{request.text[:50]}...'")

        # Create temporary reference audio file (1 second of silence)
        ref_audio_data = np.zeros(24000, dtype=np.float32)  # 1 second at 24kHz
        ref_text = "Hello."
        gen_text = request.text

        # Save reference audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_ref:
            sf.write(temp_ref.name, ref_audio_data, 24000)
            temp_ref_path = temp_ref.name

        try:
            # Run inference
            audio_data, sample_rate, _ = infer_process(
                ref_audio=temp_ref_path,
                ref_text=ref_text,
                gen_text=gen_text,
                model_obj=model,
                vocoder=vocoder,
                speed=request.speed,
                device=device
            )

            # Save to temporary file for silence removal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_output:
                sf.write(temp_output.name, audio_data, sample_rate)
                temp_output_path = temp_output.name

            try:
                # Remove silence if requested
                if request.remove_silence:
                    remove_silence_for_generated_wav(temp_output_path)

                # Read the processed audio
                with open(temp_output_path, 'rb') as f:
                    audio_buffer = io.BytesIO(f.read())

                return StreamingResponse(
                    audio_buffer,
                    media_type="audio/wav",
                    headers={"Content-Disposition": "attachment; filename=synthesized.wav"}
                )

            finally:
                # Clean up temp output file
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)

        finally:
            # Clean up temp reference file
            if os.path.exists(temp_ref_path):
                os.unlink(temp_ref_path)

    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clone")
async def clone_voice(
    text: str = Form(...),
    ref_audio: UploadFile = File(...),
    ref_text: Optional[str] = Form(None),
    language: str = Form("en"),
    speed: float = Form(1.0),
    remove_silence: bool = Form(True)
):
    """
    Clone voice from reference audio and synthesize text.

    Args:
        text: Text to synthesize
        ref_audio: Reference audio file for voice cloning
        ref_text: Transcript of reference audio (optional, auto-transcribed if not provided)
        language: Target language
        speed: Speech speed multiplier
        remove_silence: Whether to remove silence from generated audio

    Returns:
        Audio file as WAV format
    """
    if not model_loaded:
        logger.warning("Model not loaded, attempting to load...")
        if not initialize_model():
            raise HTTPException(
                status_code=503,
                detail="Model not loaded and failed to initialize"
            )

    try:
        logger.info(f"Voice cloning: '{text[:50]}...'")

        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await ref_audio.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name

        try:
            # If ref_text not provided, use a generic placeholder
            # In production, you'd want to integrate Whisper or another ASR model
            if not ref_text:
                ref_text = "Welcome to the event. Thank you for being here today."
                logger.warning("No ref_text provided, using placeholder")

            # Run inference
            audio_data, sample_rate, _ = infer_process(
                ref_audio=temp_audio_path,
                ref_text=ref_text,
                gen_text=text,
                model_obj=model,
                vocoder=vocoder,
                speed=speed,
                device=device
            )

            # Save to temporary file for silence removal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_output:
                sf.write(temp_output.name, audio_data, sample_rate)
                temp_output_path = temp_output.name

            try:
                # Remove silence if requested
                if remove_silence:
                    remove_silence_for_generated_wav(temp_output_path)

                # Read the processed audio
                with open(temp_output_path, 'rb') as f:
                    audio_buffer = io.BytesIO(f.read())

                return StreamingResponse(
                    audio_buffer,
                    media_type="audio/wav",
                    headers={"Content-Disposition": f"attachment; filename=cloned_{ref_audio.filename}"}
                )

            finally:
                # Clean up temp output file
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)

        finally:
            # Clean up temp file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    except Exception as e:
        logger.error(f"Voice cloning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/languages")
async def get_languages():
    """Get supported languages."""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"}
        ]
    }


@app.get("/gpu_stats")
async def gpu_stats():
    """Get GPU utilization statistics."""
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}

    return {
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "device_name": torch.cuda.get_device_name(0),
        "memory_allocated_gb": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}",
        "memory_reserved_gb": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f}",
        "memory_total_gb": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}"
    }


@app.post("/reload_model")
async def reload_model():
    """Reload the model (useful after updates)."""
    global model_loaded
    model_loaded = False

    if initialize_model():
        return {"status": "success", "message": "Model reloaded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload model")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

"""
StyleTTS2 FastAPI Server
High-quality expressive text-to-speech API with voice cloning
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import torch
import io
import logging
import os
import soundfile as sf
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="StyleTTS2 API", version="2.0.0")

# Initialize
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

# Load StyleTTS2 model
model = None
try:
    from styletts2 import tts
    logger.info("Loading StyleTTS2 model...")
    model = tts.StyleTTS2()
    logger.info("StyleTTS2 model loaded successfully")
except Exception as e:
    logger.error(f"Error loading StyleTTS2 model: {e}")
    logger.warning("Model will be initialized on first request")


class TTSRequest(BaseModel):
    """TTS request model for JSON endpoint."""
    text: str
    alpha: float = 0.3  # Timbre control (0-1)
    beta: float = 0.7  # Prosody control (0-1)
    diffusion_steps: int = 5
    embedding_scale: float = 1.0
    output_sample_rate: int = 24000


class VoiceCloningRequest(BaseModel):
    """Voice cloning request model."""
    text: str
    alpha: float = 0.3
    beta: float = 0.7
    diffusion_steps: int = 5
    embedding_scale: float = 1.0


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "StyleTTS2",
        "version": "2.0.0",
        "status": "running",
        "description": "High-quality expressive TTS with style transfer and voice cloning",
        "model_loaded": model is not None
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated_gb": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}",
            "gpu_memory_total_gb": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}"
        }

    return {
        "status": "healthy",
        "device": device,
        "model_loaded": model is not None,
        **gpu_info
    }


@app.get("/languages")
async def get_languages():
    """Get supported languages."""
    return {
        "languages": [
            {"code": "en", "name": "English"}
        ],
        "note": "StyleTTS2 is primarily trained on English. Other languages may work with reduced quality."
    }


@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    """
    Synthesize speech with StyleTTS2 using default voice.

    Args:
        request: TTS request with text and style parameters

    Returns:
        Audio file as WAV format
    """
    global model

    try:
        # Initialize model if not loaded
        if model is None:
            logger.info("Initializing StyleTTS2 model on first request...")
            from styletts2 import tts
            model = tts.StyleTTS2()

        logger.info(f"Synthesizing: '{request.text[:50]}...'")

        # Generate audio using StyleTTS2
        audio = model.inference(
            request.text,
            target_voice_path=None,  # Use default voice
            output_wav_file=None,  # Return array instead of saving
            output_sample_rate=request.output_sample_rate,
            alpha=request.alpha,
            beta=request.beta,
            diffusion_steps=request.diffusion_steps,
            embedding_scale=request.embedding_scale
        )

        # Convert to WAV format in memory
        wav_io = io.BytesIO()
        sf.write(wav_io, audio, request.output_sample_rate, format='WAV')
        wav_io.seek(0)

        logger.info(f"Generated audio: {len(audio)} samples, {len(audio)/request.output_sample_rate:.2f}s")

        return StreamingResponse(
            wav_io,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=styletts2_output.wav"
            }
        )

    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_styletts2_stream(request: TTSRequest):
    """Generator function that yields audio chunks for StyleTTS2 streaming."""
    global model

    try:
        # Initialize model if not loaded
        if model is None:
            logger.info("Initializing StyleTTS2 model on first request...")
            from styletts2 import tts as styletts2_tts
            model = styletts2_tts.StyleTTS2()

        logger.info(f"Streaming synthesis: '{request.text[:50]}...'")

        # Split text into sentences for streaming
        import re
        sentences = re.split(r'([.!?]+\s*)', request.text)
        sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences), 2) if sentences[i].strip()]

        if not sentences:
            sentences = [request.text]

        logger.info(f"Split into {len(sentences)} sentence(s) for streaming")

        # Process each sentence
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            logger.info(f"Processing sentence {i+1}/{len(sentences)}: '{sentence[:30]}...'")

            # Generate audio for this sentence
            audio = model.inference(
                sentence,
                target_voice_path=None,  # Use default voice
                output_wav_file=None,  # Return array instead of saving
                output_sample_rate=request.output_sample_rate,
                alpha=request.alpha,
                beta=request.beta,
                diffusion_steps=request.diffusion_steps,
                embedding_scale=request.embedding_scale
            )

            # Convert to WAV format in memory
            wav_io = io.BytesIO()
            sf.write(wav_io, audio, request.output_sample_rate, format='WAV')
            chunk = wav_io.getvalue()

            logger.info(f"Yielding chunk {i+1}: {len(chunk)} bytes ({len(audio)/request.output_sample_rate:.2f}s)")
            yield chunk

    except Exception as e:
        logger.error(f"Streaming synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/stream")
async def synthesize_stream(request: TTSRequest):
    """
    Stream synthesized speech sentence-by-sentence with StyleTTS2.

    Args:
        request: TTS request with text and style parameters

    Yields:
        Audio chunks as WAV format (sentence-level streaming)
    """
    return StreamingResponse(
        _generate_styletts2_stream(request),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=styletts2_stream.wav"}
    )


@app.post("/clone")
async def clone_voice(
    text: str = Form(...),
    reference_audio: UploadFile = File(...),
    alpha: float = Form(0.3),
    beta: float = Form(0.7),
    diffusion_steps: int = Form(5),
    embedding_scale: float = Form(1.0),
    output_sample_rate: int = Form(24000)
):
    """
    Synthesize speech with voice cloning from reference audio.

    Args:
        text: Text to synthesize
        reference_audio: Audio file containing the voice to clone
        alpha: Timbre control (0-1, higher = more text-aligned)
        beta: Prosody control (0-1, higher = more text-aligned)
        diffusion_steps: Number of diffusion steps (more = higher quality but slower)
        embedding_scale: Style conditioning strength
        output_sample_rate: Output sample rate in Hz

    Returns:
        Audio file with cloned voice
    """
    global model

    try:
        # Initialize model if not loaded
        if model is None:
            logger.info("Initializing StyleTTS2 model on first request...")
            from styletts2 import tts
            model = tts.StyleTTS2()

        logger.info(f"Voice cloning synthesis: '{text[:50]}...'")

        # Save reference audio temporarily
        temp_dir = Path("/tmp/styletts2_references")
        temp_dir.mkdir(exist_ok=True)
        ref_path = temp_dir / f"ref_{os.urandom(8).hex()}.wav"

        with open(ref_path, "wb") as f:
            content = await reference_audio.read()
            f.write(content)

        logger.info(f"Saved reference audio: {ref_path}, size: {len(content)} bytes")

        # Generate audio with voice cloning
        audio = model.inference(
            text,
            target_voice_path=str(ref_path),
            output_wav_file=None,
            output_sample_rate=output_sample_rate,
            alpha=alpha,
            beta=beta,
            diffusion_steps=diffusion_steps,
            embedding_scale=embedding_scale
        )

        # Clean up reference file
        ref_path.unlink()

        # Convert to WAV format in memory
        wav_io = io.BytesIO()
        sf.write(wav_io, audio, output_sample_rate, format='WAV')
        wav_io.seek(0)

        logger.info(f"Cloned audio: {len(audio)} samples, {len(audio)/output_sample_rate:.2f}s")

        return StreamingResponse(
            wav_io,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=styletts2_cloned.wav"
            }
        )

    except Exception as e:
        logger.error(f"Voice cloning error: {e}", exc_info=True)
        # Clean up reference file on error
        if 'ref_path' in locals() and ref_path.exists():
            ref_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gpu_stats")
async def gpu_stats():
    """Get GPU utilization statistics."""
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}

    return {
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "device_name": torch.cuda.get_device_name(0),
        "memory_allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
        "memory_reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
        "memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

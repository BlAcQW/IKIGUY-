"""
Fish Speech TTS FastAPI Wrapper with Streaming
Provides streaming API for Fish Speech Gradio app
Gradio app runs on port 7860, this wrapper runs on port 8020
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import asyncio
import io
import logging
import re
import soundfile as sf
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fish Speech TTS API", version="1.0.0")

# Gradio app URL
GRADIO_URL = "http://127.0.0.1:7860"


class TTSRequest(BaseModel):
    """TTS request model."""
    text: str
    language: str = "en"
    speed: float = 1.0
    speaker: str = "default"


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Fish Speech TTS",
        "version": "1.0.0",
        "status": "running",
        "gradio_backend": GRADIO_URL
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(GRADIO_URL)
            gradio_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        gradio_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "gradio_backend": gradio_status
    }


@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    """
    Synthesize speech from text (blocking mode).

    Args:
        request: TTS request with text, language, speed, speaker

    Returns:
        Audio file as WAV format
    """
    logger.info(f"[SYNTHESIS] Text: '{request.text[:50]}...', Language: {request.language}")

    try:
        # Call Gradio API using gradio_client
        from gradio_client import Client

        client = Client(GRADIO_URL)

        # Fish Speech API call (adjust parameters based on actual Gradio interface)
        result = client.predict(
            request.text,
            request.language,
            api_name="/predict"  # Adjust based on actual endpoint
        )

        # Result should be audio file path
        if result and isinstance(result, str):
            with open(result, 'rb') as f:
                audio_data = f.read()

            logger.info(f"[SYNTHESIS COMPLETE] Generated {len(audio_data)} bytes")
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename=fish_speech.wav"}
            )
        else:
            raise HTTPException(status_code=500, detail="No audio generated")

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_fish_speech_stream(request: TTSRequest):
    """Generator function for Fish Speech streaming."""
    try:
        from gradio_client import Client

        # Split text into sentences for streaming
        sentences = re.split(r'([.!?]+\s*)', request.text)
        sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences), 2) if sentences[i].strip()]

        if not sentences:
            sentences = [request.text]

        logger.info(f"[STREAMING] Split into {len(sentences)} sentence(s)")

        client = Client(GRADIO_URL)

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            logger.info(f"[STREAMING] Processing sentence {i+1}/{len(sentences)}: '{sentence[:30]}...'")

            # Generate audio for this sentence
            result = client.predict(
                sentence,
                request.language,
                api_name="/predict"
            )

            if result and isinstance(result, str):
                with open(result, 'rb') as f:
                    audio_data = f.read()

                logger.info(f"[STREAMING] Yielding chunk {i+1}: {len(audio_data)} bytes")
                yield audio_data

    except Exception as e:
        logger.error(f"[STREAMING ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/stream")
async def synthesize_stream(request: TTSRequest):
    """
    Stream synthesized speech sentence-by-sentence.

    Args:
        request: TTS request with text, language, speed, speaker

    Yields:
        Audio chunks as WAV format (sentence-level streaming)
    """
    return StreamingResponse(
        _generate_fish_speech_stream(request),
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=fish_speech_stream.wav"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)

"""
Kokoro TTS FastAPI Server
Fast, high-quality TTS with Kokoro-82M model
https://huggingface.co/hexgrad/Kokoro-82M
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import io
import logging
import asyncio
import concurrent.futures
import numpy as np
import soundfile as sf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kokoro TTS API", version="1.0.0")

# Initialize TTS model
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

# Load Kokoro model
model = None
voicepacks = {}

try:
    # Try to load Kokoro from local kokoro package
    import sys
    sys.path.insert(0, '/app/kokoro')

    from kokoro import KPipeline

    logger.info("Kokoro TTS loaded successfully")

    # Create a global pipeline instance
    # We'll initialize language-specific pipelines on demand
    model = {}  # Will store KPipeline instances per language

    # Available voicepacks (from Kokoro repository)
    # Language codes: a=American English, b=British English, p=Portuguese, etc.
    voicepacks = {
        # American English voices
        "af_heart": "Heart (female, American)",
        "af_bella": "Bella (female, American)",
        "af_nicole": "Nicole (female, American)",
        "af_sarah": "Sarah (female, American)",
        "af_sky": "Sky (female, American)",
        "am_adam": "Adam (male, American)",
        "am_michael": "Michael (male, American)",
        # British English voices
        "bf_emma": "Emma (female, British)",
        "bf_isabella": "Isabella (female, British)",
        "bm_george": "George (male, British)",
        "bm_lewis": "Lewis (male, British)"
    }

    logger.info(f"Loaded {len(voicepacks)} voice packs")

except ImportError as e:
    logger.warning(f"Could not import kokoro package: {e}")
    logger.info("Kokoro model not available - synthesis will return 501")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    import traceback
    traceback.print_exc()


class TTSRequest(BaseModel):
    """TTS request model."""
    text: str
    voice: str = "default"
    speed: float = 1.0
    pitch: float = 1.0


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Kokoro TTS",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "device": device,
        "model_loaded": isinstance(model, dict),
        "voicepacks": len(voicepacks)
    }


@app.get("/voices")
async def get_voices():
    """Get available voice packs."""
    if not voicepacks:
        return {
            "voices": [],
            "error": "Kokoro model not loaded"
        }

    voice_list = []
    for voice_id, description in voicepacks.items():
        voice_list.append({
            "id": voice_id,
            "name": description
        })

    return {
        "voices": voice_list,
        "count": len(voice_list)
    }


@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    """
    Synthesize speech from text using Kokoro-82M.

    Args:
        request: TTS request with text, voice, speed, and pitch

    Returns:
        Audio file as WAV format
    """
    logger.info(f"[SYNTHESIS START] Text: '{request.text[:50]}...', Voice: {request.voice}")

    try:
        if model is None:
            logger.error("[SYNTHESIS ERROR] Model not loaded")
            raise HTTPException(
                status_code=503,
                detail="Kokoro model not loaded - check container logs"
            )

        # Validate voice
        voice_id = request.voice if request.voice != "default" else "af_heart"
        if voice_id not in voicepacks:
            logger.error(f"[SYNTHESIS ERROR] Voice not found: {voice_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Voice '{voice_id}' not found. Available: {list(voicepacks.keys())}"
            )

        logger.info(f"[SYNTHESIS] Synthesizing with voice {voice_id}")

        # Determine language from voice prefix
        # Voice format: {lang_code}{gender}_{name}
        # Example: af_heart -> lang_code='a', bf_emma -> lang_code='b'
        lang_code = voice_id[0]  # First character is the language code

        # Define blocking synthesis function
        def do_synthesis():
            logger.info("[THREAD] Starting Kokoro synthesis")

            try:
                # Get or create pipeline for this language
                if lang_code not in model:
                    logger.info(f"[THREAD] Creating KPipeline for language '{lang_code}'")
                    model[lang_code] = KPipeline(lang_code=lang_code)

                pipeline = model[lang_code]

                # Generate audio using KPipeline
                # KPipeline returns a generator of Result objects
                audio_chunks = []
                for result in pipeline(request.text, voice=voice_id, speed=request.speed):
                    if result.audio is not None:
                        audio_chunks.append(result.audio.numpy())

                # Concatenate all audio chunks
                if not audio_chunks:
                    raise ValueError("No audio generated")

                audio_array = np.concatenate(audio_chunks)

                # Kokoro returns numpy array, sample rate is 24000 Hz
                sample_rate = 24000

                logger.info(f"[THREAD] Synthesis complete, audio shape: {audio_array.shape}")
                return (audio_array, sample_rate)

            except Exception as e:
                logger.error(f"[THREAD ERROR] Kokoro synthesis failed: {e}")
                import traceback
                traceback.print_exc()
                raise

        # Run synthesis in thread pool
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            logger.info("[SYNTHESIS] Running synthesis in thread pool...")
            audio_data, sample_rate = await loop.run_in_executor(
                executor,
                do_synthesis
            )

        logger.info("[SYNTHESIS] Thread pool execution complete, preparing response...")

        # Convert to bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format='WAV')
        buffer.seek(0)

        logger.info("[SYNTHESIS COMPLETE] Returning audio response")
        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=kokoro_{voice_id}.wav"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_kokoro_stream(request: TTSRequest):
    """Generator function that yields audio chunks for Kokoro streaming."""
    try:
        if model is None:
            logger.error("[STREAMING ERROR] Model not loaded")
            raise HTTPException(
                status_code=503,
                detail="Kokoro model not loaded - check container logs"
            )

        # Validate voice
        voice_id = request.voice if request.voice != "default" else "af_heart"
        if voice_id not in voicepacks:
            logger.error(f"[STREAMING ERROR] Voice not found: {voice_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Voice '{voice_id}' not found. Available: {list(voicepacks.keys())}"
            )

        logger.info(f"[STREAMING] Synthesizing: '{request.text[:50]}...' with voice {voice_id}")

        # Split text into sentences for streaming
        import re
        sentences = re.split(r'([.!?]+\s*)', request.text)
        sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences), 2) if sentences[i].strip()]

        if not sentences:
            sentences = [request.text]

        logger.info(f"[STREAMING] Split into {len(sentences)} sentence(s)")

        # Determine language from voice prefix
        lang_code = voice_id[0]  # First character is the language code

        # Define blocking synthesis function for each sentence
        def synthesize_sentence(sentence_text):
            try:
                # Get or create pipeline for this language
                if lang_code not in model:
                    logger.info(f"[THREAD] Creating KPipeline for language '{lang_code}'")
                    model[lang_code] = KPipeline(lang_code=lang_code)

                pipeline = model[lang_code]

                # Generate audio using KPipeline
                audio_chunks = []
                for result in pipeline(sentence_text, voice=voice_id, speed=request.speed):
                    if result.audio is not None:
                        audio_chunks.append(result.audio.numpy())

                if not audio_chunks:
                    raise ValueError("No audio generated")

                audio_array = np.concatenate(audio_chunks)
                sample_rate = 24000

                return (audio_array, sample_rate)

            except Exception as e:
                logger.error(f"[THREAD ERROR] Kokoro synthesis failed: {e}")
                raise

        # Process each sentence
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                logger.info(f"[STREAMING] Processing sentence {i+1}/{len(sentences)}: '{sentence[:30]}...'")

                # Run synthesis in thread pool
                audio_data, sample_rate = await loop.run_in_executor(
                    executor,
                    synthesize_sentence,
                    sentence
                )

                # Convert to WAV bytes
                buffer = io.BytesIO()
                sf.write(buffer, audio_data, sample_rate, format='WAV')
                chunk = buffer.getvalue()

                logger.info(f"[STREAMING] Yielding chunk {i+1}: {len(chunk)} bytes")
                yield chunk

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
        request: TTS request with text, voice, speed, and pitch

    Yields:
        Audio chunks as WAV format (sentence-level streaming)
    """
    return StreamingResponse(
        _generate_kokoro_stream(request),
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=kokoro_stream.wav"}
    )


@app.websocket("/ws/synthesize")
async def websocket_synthesize(websocket: WebSocket):
    """
    WebSocket endpoint for streaming TTS.
    Allows real-time text input and audio output streaming.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive text from client
            data = await websocket.receive_json()
            text = data.get("text", "")
            voice = data.get("voice", "default")

            if not text:
                await websocket.send_json({"error": "No text provided"})
                continue

            logger.info(f"WebSocket synthesis: '{text[:50]}...'")

            # TODO: Implement streaming synthesis
            # for audio_chunk in model.synthesize_stream(text, voice=voice):
            #     await websocket.send_bytes(audio_chunk)

            await websocket.send_json({
                "status": "not_implemented",
                "message": "Streaming synthesis not yet implemented"
            })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

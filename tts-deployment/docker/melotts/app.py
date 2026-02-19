"""
MeloTTS FastAPI Server
Fast multilingual text-to-speech API
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
from melo.api import TTS
import io
import logging
import re
from typing import AsyncGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MeloTTS API", version="1.0.0")

# Initialize TTS models
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

# Load models for different languages (lazy loading)
models = {}
supported_languages = ['EN', 'ES', 'FR', 'ZH', 'JP', 'KR']

# Note: Models are loaded on-demand to reduce startup time and memory usage
logger.info(f"MeloTTS ready. Supported languages: {supported_languages}")
logger.info("Models will be loaded on first synthesis request for each language")


def load_model(language: str, max_retries: int = 3):
    """
    Load TTS model for a specific language with retry logic for CUDA busy errors.

    Args:
        language: Language code (EN, ES, FR, ZH, JP, KR)
        max_retries: Maximum number of retry attempts (default: 3)

    Raises:
        Exception: If model fails to load after retries
    """
    if language not in models:
        logger.info(f"Loading model for language: {language}")
        
        import time
        import random
        
        for attempt in range(max_retries):
            try:
                models[language] = TTS(language=language, device=device)
                logger.info(f"Successfully loaded {language} model")
                return
            except RuntimeError as e:
                error_str = str(e)
                # Check if it's a CUDA busy/unavailable error
                if "CUDA" in error_str and ("busy" in error_str.lower() or "unavailable" in error_str.lower()):
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"GPU busy for {language} model (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Failed to load {language} model after {max_retries} attempts: GPU unavailable")
                        raise Exception(f"Failed to load model for language {language}: GPU unavailable after {max_retries} retries")
                else:
                    # Non-CUDA error, raise immediately
                    logger.error(f"Failed to load {language} model: {e}")
                    raise Exception(f"Failed to load model for language {language}: {str(e)}")
            except Exception as e:
                # Other exceptions, raise immediately
                logger.error(f"Failed to load {language} model: {e}")
                raise Exception(f"Failed to load model for language {language}: {str(e)}")


class TTSRequest(BaseModel):
    """TTS request model."""
    text: str
    language: str = "EN"
    speaker_id: int = 0
    speed: float = 1.0


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MeloTTS",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "device": device,
        "models_loaded": list(models.keys())
    }


@app.get("/languages")
async def get_languages():
    """Get supported languages."""
    return {
        "languages": supported_languages,
        "models_loaded": list(models.keys())
    }


@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    """
    Synthesize speech from text.

    Args:
        request: TTS request with text, language, speaker_id, and speed

    Returns:
        Audio file as WAV format
    """
    try:
        # Validate language is supported
        if request.language not in supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{request.language}' not supported. Available: {supported_languages}"
            )

        # Load model if not already loaded (lazy loading)
        load_model(request.language)

        # Get the appropriate model
        model = models[request.language]

        # Get speaker IDs for this language
        # speaker_ids is an HParams object (dict-like) with speaker names as keys and IDs as values
        speaker_ids = model.hps.data.spk2id

        # Convert to list of speaker names for indexing
        speaker_names = list(speaker_ids.keys())

        # Validate speaker ID
        if request.speaker_id >= len(speaker_names):
            raise HTTPException(
                status_code=400,
                detail=f"Speaker ID {request.speaker_id} not available for language {request.language}. Available: {speaker_names}"
            )

        # Get the speaker name by index
        speaker_key = speaker_names[request.speaker_id]
        # Get actual speaker ID value from the dict
        actual_speaker_id = speaker_ids[speaker_key]

        logger.info(f"Synthesizing: '{request.text[:50]}...' in {request.language} with speaker {speaker_key} (ID: {actual_speaker_id})")

        # Synthesize to temporary file first, then read to BytesIO
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Generate speech to file
            model.tts_to_file(
                request.text,
                actual_speaker_id,
                tmp_path,
                speed=request.speed,
                format='wav'
            )

            # Read file into BytesIO
            bio = io.BytesIO()
            with open(tmp_path, 'rb') as f:
                bio.write(f.read())
            bio.seek(0)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return StreamingResponse(bio, media_type="audio/wav")

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences for streaming.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    # Filter out empty strings
    sentences = [s.strip() for s in sentences if s.strip()]

    # If no sentence boundaries found, split by length
    if len(sentences) == 0 or (len(sentences) == 1 and len(sentences[0]) > 200):
        # Split long text into chunks
        words = text.split()
        sentences = []
        current = []
        for word in words:
            current.append(word)
            if len(' '.join(current)) > 100:
                sentences.append(' '.join(current))
                current = []
        if current:
            sentences.append(' '.join(current))

    return sentences


@app.post("/synthesize/stream")
async def synthesize_stream(request: TTSRequest):
    """
    Stream synthesize speech from text, sentence by sentence.

    Args:
        request: TTS request with text, language, speaker_id, and speed

    Yields:
        Audio chunks as WAV format
    """
    try:
        # Validate language is supported
        if request.language not in supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{request.language}' not supported. Available: {supported_languages}"
            )

        # Load model if not already loaded (lazy loading)
        load_model(request.language)

        # Get the appropriate model
        model = models[request.language]

        # Get speaker IDs for this language
        speaker_ids = model.hps.data.spk2id
        speaker_names = list(speaker_ids.keys())

        # Validate speaker ID
        if request.speaker_id >= len(speaker_names):
            raise HTTPException(
                status_code=400,
                detail=f"Speaker ID {request.speaker_id} not available for language {request.language}. Available: {speaker_names}"
            )

        # Get the speaker name by index
        speaker_key = speaker_names[request.speaker_id]
        actual_speaker_id = speaker_ids[speaker_key]

        # Split text into sentences for streaming
        sentences = split_sentences(request.text)
        logger.info(f"Streaming {len(sentences)} sentences in {request.language} with speaker {speaker_key}")

        async def stream_generator() -> AsyncGenerator[bytes, None]:
            """Generate audio chunks for each sentence."""
            import tempfile
            import os

            for i, sentence in enumerate(sentences):
                logger.info(f"Streaming sentence {i+1}/{len(sentences)}: {sentence[:50]}...")

                # Create temp file for this sentence
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_path = tmp_file.name

                try:
                    # Generate speech to file
                    model.tts_to_file(
                        sentence,
                        actual_speaker_id,
                        tmp_path,
                        speed=request.speed,
                        format='wav'
                    )

                    # Stream file contents in chunks
                    with open(tmp_path, 'rb') as f:
                        while True:
                            chunk = f.read(8192)  # 8KB chunks
                            if not chunk:
                                break
                            yield chunk

                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            logger.info(f"✅ Streaming complete: {len(sentences)} sentences")

        return StreamingResponse(stream_generator(), media_type="audio/wav")

    except Exception as e:
        logger.error(f"Stream synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/speakers/{language}")
async def get_speakers(language: str):
    """Get available speakers for a language."""
    # Validate language is supported
    if language not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{language}' not supported. Available: {supported_languages}"
        )

    # Load model if not already loaded
    load_model(language)

    speaker_ids = models[language].hps.data.spk2id
    # Convert HParams to regular dict for JSON serialization
    speakers_dict = dict(speaker_ids.items()) if hasattr(speaker_ids, 'items') else dict(speaker_ids)

    return {
        "language": language,
        "speakers": speakers_dict,
        "speaker_names": list(speakers_dict.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

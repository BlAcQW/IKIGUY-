"""
OpenVoice FastAPI Server
Voice cloning and conversion TTS API

OpenVoice Architecture:
1. Base TTS: Generates initial audio (OpenVoice V1 BaseSpeakerTTS)
2. Tone Color Converter: Converts the audio to match target voice (V2)

This implementation uses OpenVoice V1 BaseSpeakerTTS for base audio generation
and OpenVoice V2 tone color converter for voice cloning.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import io
import logging
import os
import tempfile
import soundfile as sf
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenVoice API",
    version="2.0.0"
)

# Configuration
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using device: {device}")

# Load OpenVoice models
try:
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter, BaseSpeakerTTS

    output_dir = '/app/outputs'
    os.makedirs(output_dir, exist_ok=True)

    # Load V2 Tone Color Converter (improved quality)
    config_path_v2 = '/app/OpenVoice/checkpoints/config_v2.json'
    ckpt_path_v2 = '/app/OpenVoice/checkpoints/converter_v2.pth'
    tone_color_converter = ToneColorConverter(config_path_v2, device=device)
    tone_color_converter.load_ckpt(ckpt_path_v2)
    logger.info("Loaded V2 Tone Color Converter")

    # Load V1 Base TTS Models (English and Chinese)
    base_tts_models = {}

    # English Base TTS
    try:
        en_config = '/app/OpenVoice/checkpoints/base_speakers/EN/config.json'
        en_ckpt = '/app/OpenVoice/checkpoints/base_speakers/EN/checkpoint.pth'
        base_tts_en = BaseSpeakerTTS(en_config, device=device)
        base_tts_en.load_ckpt(en_ckpt)
        base_tts_models['EN'] = base_tts_en
        logger.info("Loaded English Base TTS")
    except Exception as e:
        logger.error(f"Failed to load EN base TTS: {e}")

    # Chinese Base TTS
    try:
        zh_config = '/app/OpenVoice/checkpoints/base_speakers/ZH/config.json'
        zh_ckpt = '/app/OpenVoice/checkpoints/base_speakers/ZH/checkpoint.pth'
        base_tts_zh = BaseSpeakerTTS(zh_config, device=device)
        base_tts_zh.load_ckpt(zh_ckpt)
        base_tts_models['ZH'] = base_tts_zh
        logger.info("Loaded Chinese Base TTS")
    except Exception as e:
        logger.error(f"Failed to load ZH base TTS: {e}")

    # Load V1 base speaker embeddings (for base TTS)
    base_speaker_embeddings = {}
    try:
        en_se_path = '/app/OpenVoice/checkpoints/base_speakers/EN/en_default_se.pth'
        if os.path.exists(en_se_path):
            base_speaker_embeddings['en-default'] = torch.load(en_se_path).to(device)
            logger.info("Loaded EN default speaker embedding")
    except Exception as e:
        logger.warning(f"Failed to load EN speaker embedding: {e}")

    try:
        zh_se_path = '/app/OpenVoice/checkpoints/base_speakers/ZH/zh_default_se.pth'
        if os.path.exists(zh_se_path):
            base_speaker_embeddings['zh-default'] = torch.load(zh_se_path).to(device)
            logger.info("Loaded ZH default speaker embedding")
    except Exception as e:
        logger.warning(f"Failed to load ZH speaker embedding: {e}")

    # Load V2 pre-extracted speaker embeddings (for target voices)
    target_speakers = {}
    v2_speakers_dir = '/app/OpenVoice/checkpoints/base_speakers_v2/ses'
    if os.path.exists(v2_speakers_dir):
        for speaker_file in os.listdir(v2_speakers_dir):
            if speaker_file.endswith('.pth'):
                speaker_name = speaker_file.replace('.pth', '')
                speaker_path = os.path.join(v2_speakers_dir, speaker_file)
                try:
                    target_speakers[speaker_name] = torch.load(speaker_path).to(device)
                    logger.info(f"Loaded target speaker: {speaker_name}")
                except Exception as e:
                    logger.warning(f"Failed to load target speaker {speaker_name}: {e}")

    logger.info(f"OpenVoice loaded: {len(base_tts_models)} base TTS, {len(target_speakers)} target speakers")
except Exception as e:
    logger.error(f"Error loading models: {e}")
    import traceback
    traceback.print_exc()
    tone_color_converter = None
    base_tts_models = {}
    target_speakers = {}
    base_speaker_embeddings = {}


class TTSRequest(BaseModel):
    """TTS request model."""
    text: str
    reference_speaker: str = "en-default"  # Target voice speaker embedding
    language: str = "English"  # "English" or "Chinese"
    speed: float = 1.0


def generate_base_audio(text: str, language: str = "English", speed: float = 1.0) -> str:
    """
    Generate base audio using OpenVoice V1 BaseSpeakerTTS.

    Args:
        text: Text to synthesize
        language: "English" or "Chinese"
        speed: Speech speed

    Returns:
        Path to generated audio file
    """
    # Map language to model key
    lang_key = "EN" if language.lower() in ["english", "en"] else "ZH"

    if lang_key not in base_tts_models:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{language}' not supported. Available: English, Chinese"
        )

    # Generate unique output path
    output_path = os.path.join(
        output_dir,
        f'base_{os.getpid()}_{os.urandom(4).hex()}.wav'
    )

    # Generate audio using BaseSpeakerTTS
    base_tts = base_tts_models[lang_key]
    base_tts.tts(
        text=text,
        output_path=output_path,
        speaker='default',
        language=language,
        speed=speed
    )

    return output_path


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "OpenVoice",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "device": device,
        "tone_converter_loaded": tone_color_converter is not None,
        "base_tts_models": list(base_tts_models.keys()),
        "target_speakers": len(target_speakers)
    }




@app.post("/synthesize")
def synthesize(request: TTSRequest):
    """
    Synthesize speech from text using a reference speaker.

    This uses a two-stage process:
    1. Generate base audio using OpenVoice V1 BaseSpeakerTTS
    2. Convert tone color to match reference speaker embedding

    Args:
        request: TTS request with text, reference_speaker, and language

    Returns:
        Audio file as WAV format
    """
    logger.info(f"[SYNTHESIS START] Text: '{request.text[:50]}...', Speaker: {request.reference_speaker}")

    try:
        if tone_color_converter is None:
            logger.error("[SYNTHESIS ERROR] Tone converter not loaded")
            raise HTTPException(
                status_code=503,
                detail="Tone converter model not loaded"
            )

        # Validate reference speaker
        if request.reference_speaker not in target_speakers:
            logger.error(f"[SYNTHESIS ERROR] Speaker not found: {request.reference_speaker}")
            raise HTTPException(
                status_code=400,
                detail=f"Reference speaker '{request.reference_speaker}' not found. "
                       f"Available: {list(target_speakers.keys())}"
            )

        logger.info(
            f"[SYNTHESIS] Synthesizing: '{request.text[:50]}...' "
            f"with speaker {request.reference_speaker}, language {request.language}"
        )

        # Step 1: Generate base audio
        logger.info("[SYNTHESIS STEP 1] Generating base audio...")
        base_audio_path = generate_base_audio(
            request.text,
            request.language,
            request.speed
        )
        logger.info(f"[SYNTHESIS STEP 1] Base audio generated: {base_audio_path}")

        try:
            # Step 2: Extract source speaker embedding
            logger.info("[SYNTHESIS STEP 2] Extracting source speaker embedding...")
            source_se, _ = se_extractor.get_se(
                base_audio_path,
                tone_color_converter,
                vad=False
            )
            logger.info("[SYNTHESIS STEP 2] Source embedding extracted")

            # Step 3: Get target speaker embedding
            logger.info("[SYNTHESIS STEP 3] Loading target speaker embedding...")
            target_se = target_speakers[request.reference_speaker]
            logger.info("[SYNTHESIS STEP 3] Target embedding loaded")

            # Step 4: Convert tone color
            output_path = os.path.join(
                output_dir,
                f'output_{os.getpid()}_{os.urandom(4).hex()}.wav'
            )

            logger.info("[SYNTHESIS STEP 4] Converting tone color...")
            encode_message = "@OpenVoice"
            tone_color_converter.convert(
                audio_src_path=base_audio_path,
                src_se=source_se,
                tgt_se=target_se,
                output_path=output_path,
                message=encode_message
            )
            logger.info(f"[SYNTHESIS STEP 4] Tone conversion complete: {output_path}")

            # Read the converted audio
            audio_data, sample_rate = sf.read(output_path)

            # Convert to bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, sample_rate, format='WAV')
            buffer.seek(0)

            # Clean up
            os.unlink(output_path)

            logger.info("[SYNTHESIS COMPLETE] Returning audio response")
            return StreamingResponse(
                buffer,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=synthesized.wav"
                }
            )

        finally:
            # Clean up base audio
            if os.path.exists(base_audio_path):
                os.unlink(base_audio_path)

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize/stream")
async def synthesize_stream(request: TTSRequest):
    """
    Stream synthesized speech sentence-by-sentence.

    This uses a two-stage process for each sentence:
    1. Generate base audio using OpenVoice V1 BaseSpeakerTTS
    2. Convert tone color to match reference speaker embedding

    Args:
        request: TTS request with text, reference_speaker, and language

    Yields:
        Audio chunks as WAV format (sentence-level streaming)
    """
    logger.info(f"[STREAMING START] Text: '{request.text[:50]}...', Speaker: {request.reference_speaker}")

    async def stream_audio():
        """Generator function that yields audio chunks."""
        try:
            if tone_color_converter is None:
                logger.error("[STREAMING ERROR] Tone converter not loaded")
                raise HTTPException(
                    status_code=503,
                    detail="Tone converter model not loaded"
                )

            # Validate reference speaker
            if request.reference_speaker not in target_speakers:
                logger.error(f"[STREAMING ERROR] Speaker not found: {request.reference_speaker}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Reference speaker '{request.reference_speaker}' not found. "
                           f"Available: {list(target_speakers.keys())}"
                )

            # Split text into sentences for streaming
            import re
            sentences = re.split(r'([.!?]+\s*)', request.text)
            sentences = [''.join(sentences[i:i+2]).strip() for i in range(0, len(sentences), 2) if sentences[i].strip()]

            if not sentences:
                sentences = [request.text]

            logger.info(f"[STREAMING] Split into {len(sentences)} sentence(s)")

            # Get target speaker embedding
            target_se = target_speakers[request.reference_speaker]

            # Process each sentence
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                logger.info(f"[STREAMING] Processing sentence {i+1}/{len(sentences)}: '{sentence[:30]}...'")

                # Step 1: Generate base audio for this sentence
                base_audio_path = generate_base_audio(
                    sentence,
                    request.language,
                    request.speed
                )

                try:
                    # Step 2: Extract source speaker embedding
                    source_se, _ = se_extractor.get_se(
                        base_audio_path,
                        tone_color_converter,
                        vad=False
                    )

                    # Step 3: Convert tone color
                    output_path = os.path.join(
                        output_dir,
                        f'stream_{os.getpid()}_{os.urandom(4).hex()}.wav'
                    )

                    encode_message = "@OpenVoice"
                    tone_color_converter.convert(
                        audio_src_path=base_audio_path,
                        src_se=source_se,
                        tgt_se=target_se,
                        output_path=output_path,
                        message=encode_message
                    )

                    # Read the converted audio
                    audio_data, sample_rate = sf.read(output_path)

                    # Convert to WAV bytes
                    buffer = io.BytesIO()
                    sf.write(buffer, audio_data, sample_rate, format='WAV')
                    chunk = buffer.getvalue()

                    # Clean up output file
                    os.unlink(output_path)

                    logger.info(f"[STREAMING] Yielding chunk {i+1}: {len(chunk)} bytes")
                    yield chunk

                finally:
                    # Clean up base audio
                    if os.path.exists(base_audio_path):
                        os.unlink(base_audio_path)

        except Exception as e:
            logger.error(f"[STREAMING ERROR] {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        stream_audio(),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=synthesized_stream.wav"}
    )


@app.post("/clone_voice")
async def clone_voice(
    text: str = Form(...),
    reference_audio: UploadFile = File(...),
    language: str = Form("English"),
    speed: float = Form(1.0)
):
    """
    Clone a voice from a reference audio file and synthesize text.

    This endpoint:
    1. Extracts speaker embedding from the reference audio
    2. Generates base audio using OpenVoice V1 BaseSpeakerTTS
    3. Converts the base audio to match the reference voice

    Args:
        text: Text to synthesize
        reference_audio: Audio file containing the voice to clone
        language: "English" or "Chinese"
        speed: Speech speed

    Returns:
        Audio file with cloned voice
    """
    try:
        if tone_color_converter is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded"
            )

        logger.info(f"Cloning voice from reference audio for: '{text[:50]}...'")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_ref:
            content = await reference_audio.read()
            tmp_ref.write(content)
            reference_path = tmp_ref.name

        try:
            # Step 1: Extract speaker embedding from reference audio
            target_se, _ = se_extractor.get_se(
                reference_path,
                tone_color_converter,
                vad=True  # Use VAD for uploaded audio to remove silence
            )

            # Step 2: Generate base audio using OpenVoice V1 BaseSpeakerTTS
            base_audio_path = generate_base_audio(
                text,
                language,
                speed
            )

            try:
                # Step 3: Extract source speaker embedding from base audio
                source_se, _ = se_extractor.get_se(
                    base_audio_path,
                    tone_color_converter,
                    vad=False
                )

                # Step 4: Convert tone color
                output_path = os.path.join(
                    output_dir,
                    f'cloned_{os.getpid()}_{os.urandom(4).hex()}.wav'
                )

                encode_message = "@OpenVoice"
                tone_color_converter.convert(
                    audio_src_path=base_audio_path,
                    src_se=source_se,
                    tgt_se=target_se,
                    output_path=output_path,
                    message=encode_message
                )

                # Read the converted audio
                audio_data, sample_rate = sf.read(output_path)

                # Convert to bytes
                buffer = io.BytesIO()
                sf.write(buffer, audio_data, sample_rate, format='WAV')
                buffer.seek(0)

                # Clean up
                os.unlink(output_path)

                return StreamingResponse(
                    buffer,
                    media_type="audio/wav",
                    headers={
                        "Content-Disposition": f"attachment; filename=cloned_{reference_audio.filename}"
                    }
                )

            finally:
                # Clean up base audio
                if os.path.exists(base_audio_path):
                    os.unlink(base_audio_path)

        finally:
            # Clean up reference audio
            os.unlink(reference_path)

    except Exception as e:
        logger.error(f"Voice cloning error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/speakers")
async def get_speakers():
    """
    Get available pre-loaded speaker embeddings.

    Returns:
        List of available speaker names and their languages
    """
    speakers_info = []
    for speaker_name in sorted(target_speakers.keys()):
        # Parse speaker info from name (e.g., "en-default" -> EN, default)
        parts = speaker_name.split('-')
        language = parts[0].upper() if parts else "Unknown"

        speakers_info.append({
            "name": speaker_name,
            "language": language,
            "description": f"{language} speaker variant"
        })

    return {
        "speakers": speakers_info,
        "count": len(speakers_info),
        "base_tts_languages": list(base_tts_models.keys()),
        "note": "Pre-extracted V2 speaker embeddings for target voice cloning"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30,
        log_level="info"
    )

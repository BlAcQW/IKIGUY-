"""
Meta MMS Voice Routes with Gemini LLM
Web API endpoints for voice chat functionality
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, WebSocket, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
import torchaudio
import numpy as np
import io
import logging
from typing import Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mms", tags=["mms-voice"])

# Configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
GEMINI_API_KEY = "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4"
GEMINI_MODEL = "gemini-2.5-flash"

# Initialize Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info(f"Gemini {GEMINI_MODEL} initialized")
except Exception as e:
    logger.error(f"Failed to initialize Gemini: {e}")
    gemini_model = None

# Model cache
models_cache = {}

def get_asr_model(lang_code="aka"):
    """Get or load ASR model"""
    if "asr" not in models_cache:
        try:
            from transformers import AutoProcessor, Wav2Vec2ForCTC
            logger.info("Loading Meta MMS ASR model...")
            processor = AutoProcessor.from_pretrained("facebook/mms-1b-all")
            model = Wav2Vec2ForCTC.from_pretrained("facebook/mms-1b-all").to(DEVICE).eval()
            models_cache["asr"] = (processor, model)
            logger.info("ASR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            return None, None
    return models_cache["asr"]

def get_tts_model(lang_code="aka"):
    """Get or load TTS model"""
    tts_models = {
        "aka": "facebook/mms-tts-aka",
        "ewe": "facebook/mms-tts-ewe",
        "yor": "facebook/mms-tts-yor",
        "hau": "facebook/mms-tts-hau",
        "eng": "facebook/mms-tts-eng",
    }
    
    cache_key = f"tts_{lang_code}"
    if cache_key not in models_cache:
        try:
            from transformers import VitsModel, AutoTokenizer
            model_id = tts_models.get(lang_code, "facebook/mms-tts-eng")
            logger.info(f"Loading Meta MMS TTS model for {lang_code}...")
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id).to(DEVICE).eval()
            models_cache[cache_key] = (tokenizer, model)
            logger.info(f"TTS model for {lang_code} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            return None, None
    return models_cache[cache_key]

class TextRequest(BaseModel):
    text: str
    language: str = "aka"

class TranscribeResponse(BaseModel):
    transcript: str
    language: str

@router.get("/status")
async def get_status():
    """Check MMS voice service status"""
    return {
        "status": "running",
        "device": DEVICE,
        "gemini_available": gemini_model is not None,
        "supported_languages": ["aka", "ewe", "yor", "hau", "eng"],
        "models_loaded": list(models_cache.keys())
    }

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    lang_code: str = "aka"
):
    """Transcribe audio to text using Meta MMS"""
    try:
        # Read audio data
        audio_bytes = await audio_file.read()
        
        # Convert to tensor
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_array).unsqueeze(0)
        
        # Resample to 16kHz if needed
        if audio_tensor.shape[1] > 0:
            # Assume input is 48kHz, resample to 16kHz
            audio_16k = torchaudio.functional.resample(audio_tensor, 48000, 16000)
        else:
            return TranscribeResponse(transcript="", language=lang_code)
        
        # Get ASR model
        processor, model = get_asr_model(lang_code)
        if not processor or not model:
            raise HTTPException(status_code=500, detail="ASR model not available")
        
        # Set language
        processor.tokenizer.set_target_lang(lang_code)
        try:
            model.load_adapter(lang_code)
        except:
            pass
        
        # Transcribe
        inputs = processor(audio_16k.squeeze().numpy(), sampling_rate=16000, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            logits = model(**inputs).logits
        ids = torch.argmax(logits, dim=-1)[0]
        text = processor.decode(ids).strip()
        
        return TranscribeResponse(transcript=text, language=lang_code)
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/synthesize")
async def synthesize_speech(request: TextRequest):
    """Synthesize speech from text using Meta MMS"""
    try:
        # Get TTS model
        tokenizer, model = get_tts_model(request.language)
        if not tokenizer or not model:
            raise HTTPException(status_code=500, detail="TTS model not available")
        
        # Generate speech
        inputs = tokenizer(text=request.text, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            output = model(**inputs)
        
        # Get waveform
        waveform = output.waveform[0].cpu()
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        sample_rate = model.config.sampling_rate if hasattr(model.config, 'sampling_rate') else 22050
        torchaudio.save(buffer, waveform.unsqueeze(0), sample_rate, format="wav")
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="audio/wav")
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def voice_chat(
    audio_file: UploadFile = File(...),
    lang_code: str = "aka"
):
    """Complete voice chat: STT -> LLM -> TTS"""
    try:
        # 1. Transcribe audio
        audio_bytes = await audio_file.read()
        
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_array).unsqueeze(0)
        
        # Resample to 16kHz
        audio_16k = torchaudio.functional.resample(audio_tensor, 48000, 16000)
        
        # Get ASR model and transcribe
        processor, asr_model = get_asr_model(lang_code)
        if not processor or not asr_model:
            raise HTTPException(status_code=500, detail="ASR model not available")
            
        processor.tokenizer.set_target_lang(lang_code)
        try:
            asr_model.load_adapter(lang_code)
        except:
            pass
        
        inputs = processor(audio_16k.squeeze().numpy(), sampling_rate=16000, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            logits = asr_model(**inputs).logits
        ids = torch.argmax(logits, dim=-1)[0]
        user_text = processor.decode(ids).strip()
        
        # 2. Get LLM response
        reply_text = "Hello, I heard you!"  # Default response
        
        if gemini_model and user_text:
            try:
                language_names = {
                    "aka": "Akan/Twi",
                    "ewe": "Ewe",
                    "yor": "Yoruba",
                    "hau": "Hausa",
                    "eng": "English"
                }
                lang_name = language_names.get(lang_code, lang_code)
                
                prompt = f"""You are a helpful assistant. Respond in {lang_name} language. 
                Keep your response to 1-2 sentences. Be conversational and friendly.
                
                User: {user_text}
                Assistant:"""
                
                response = gemini_model.generate_content(prompt)
                reply_text = response.text.strip()
            except Exception as e:
                logger.error(f"Gemini response failed: {e}")
                reply_text = f"I heard: {user_text}"
        
        # 3. Synthesize response
        tokenizer, tts_model = get_tts_model(lang_code)
        if not tokenizer or not tts_model:
            raise HTTPException(status_code=500, detail="TTS model not available")
            
        tts_inputs = tokenizer(text=reply_text, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            tts_output = tts_model(**tts_inputs)
        
        waveform = tts_output.waveform[0].cpu()
        
        # Create WAV file
        buffer = io.BytesIO()
        sample_rate = tts_model.config.sampling_rate if hasattr(tts_model.config, 'sampling_rate') else 22050
        torchaudio.save(buffer, waveform.unsqueeze(0), sample_rate, format="wav")
        buffer.seek(0)
        
        # Return audio with metadata in headers
        return StreamingResponse(
            buffer, 
            media_type="audio/wav",
            headers={
                "X-Transcript": user_text,
                "X-Response": reply_text,
                "X-Language": lang_code
            }
        )
        
    except Exception as e:
        logger.error(f"Voice chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



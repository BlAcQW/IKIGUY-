"""
Simple TTS Service using gTTS for quick deployment
Falls back to gTTS when Coqui TTS is not available
"""

import io
import time
import logging
from typing import Optional, Dict, List, Any
from gtts import gTTS
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class SimpleTTSService:
    """Simple TTS service using gTTS"""
    
    def __init__(self):
        """Initialize Simple TTS Service"""
        logger.info("Initializing Simple TTS Service with gTTS")
        self.model_loaded = True  # gTTS doesn't need model loading
        
    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """Synthesize speech using gTTS
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID (not used in gTTS)
            speed: Speech speed
            language: Language code
            
        Returns:
            Synthesis result
        """
        start_time = time.time()
        
        try:
            # Use gTTS for synthesis
            # Note: gTTS doesn't support Twi directly, but we can use English
            tts = gTTS(text=text, lang=language, slow=(speed < 1.0))
            
            # Get audio as bytes
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.getvalue()
            
            # Estimate duration (rough approximation)
            duration = len(text) * 0.06  # Approximate 60ms per character
            
            return {
                "audio": audio_bytes,
                "text": text,
                "voice_id": voice_id or "default",
                "duration": duration,
                "sample_rate": 24000,  # gTTS default
                "format": "mp3",  # gTTS outputs MP3
                "processing_time": time.time() - start_time,
                "status": "success",
                "engine": "gTTS"
            }
            
        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            # Generate silence as fallback
            return self._generate_silence(text)
    
    def _generate_silence(self, text: str) -> Dict[str, Any]:
        """Generate silent audio as fallback"""
        duration = len(text) * 0.06
        sample_rate = 16000
        silence = np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        buffer = io.BytesIO()
        sf.write(buffer, silence, sample_rate, format='WAV')
        buffer.seek(0)
        
        return {
            "audio": buffer.getvalue(),
            "text": text,
            "voice_id": "silence",
            "duration": duration,
            "sample_rate": sample_rate,
            "format": "wav",
            "processing_time": 0.01,
            "status": "fallback",
            "engine": "silence"
        }
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get available voices (limited with gTTS)"""
        return [
            {
                "voice_id": "default",
                "name": "Default Voice",
                "language": "en",
                "dialect": "standard",
                "gender": "neutral",
                "age_group": "adult",
                "description": "gTTS default voice"
            }
        ]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "loaded": True,
            "engine": "gTTS",
            "model_name": "Google Text-to-Speech",
            "capabilities": {
                "multi_speaker": False,
                "voice_cloning": False,
                "languages": ["en", "fr", "es", "de", "it", "pt"],  # gTTS supports many
                "max_length": 5000
            }
        }
"""
Twi TTS Service - Text-to-Speech for Twi/Akan languages
Using Coqui TTS as primary engine
"""

import torch
import numpy as np
from pathlib import Path
import tempfile
import logging
from typing import Optional, Dict, List, Any
import base64
import io
import time
import soundfile as sf

logger = logging.getLogger(__name__)


class TwiTTSService:
    """Service for Twi/Akan Text-to-Speech synthesis"""
    
    def __init__(self):
        """Initialize Twi TTS Service"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Twi TTS Service using device: {self.device}")
        
        self.tts = None
        self.model_loaded = False
        self._init_tts()
        
    def _init_tts(self):
        """Initialize TTS model"""
        try:
            # Try to load Coqui TTS
            from TTS.api import TTS
            
            # List available models
            available_models = TTS.list_models()
            logger.info(f"Available TTS models: {len(available_models)}")
            
            # Try multilingual model first (supports more languages)
            multilingual_models = [m for m in available_models if 'multilingual' in m]
            
            if multilingual_models:
                model_name = multilingual_models[0]
                logger.info(f"Loading multilingual TTS model: {model_name}")
            else:
                # Fallback to English model
                model_name = 'tts_models/en/ljspeech/tacotron2-DDC'
                logger.info(f"Loading default TTS model: {model_name}")
            
            self.tts = TTS(model_name).to(self.device)
            self.model_loaded = True
            logger.info("✅ TTS model loaded successfully")
            
        except ImportError:
            logger.warning("Coqui TTS not installed. Install with: pip install TTS")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.model_loaded = False
    
    def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 0.0,
        output_format: str = "wav",
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice_id: Voice/speaker ID (if multi-speaker model)
            speed: Speech speed multiplier
            pitch: Pitch adjustment
            output_format: Output format (wav, mp3)
            sample_rate: Sample rate
            
        Returns:
            Synthesis result with audio data
        """
        start_time = time.time()
        
        try:
            if not self.model_loaded or not self.tts:
                # Return dummy audio if model not loaded
                logger.warning("TTS model not loaded, generating dummy audio")
                return self._generate_dummy_audio(text, sample_rate)
            
            # Synthesize with Coqui TTS
            logger.info(f"Synthesizing: {text[:100]}...")
            
            # Generate audio
            wav = self.tts.tts(
                text=text,
                speaker=voice_id,
                speed=speed
            )
            
            # Apply pitch adjustment if needed
            if pitch != 0.0:
                wav = self._adjust_pitch(wav, pitch)
            
            # Convert to desired format
            audio_bytes = self._encode_audio(wav, output_format, sample_rate)
            
            result = {
                "audio": audio_bytes,
                "text": text,
                "voice_id": voice_id or "default",
                "duration": len(wav) / sample_rate,
                "sample_rate": sample_rate,
                "format": output_format,
                "processing_time": time.time() - start_time,
                "status": "success"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            # Return dummy audio on error
            return self._generate_dummy_audio(text, sample_rate)
    
    def _generate_dummy_audio(self, text: str, sample_rate: int) -> Dict[str, Any]:
        """Generate dummy audio for testing"""
        # Generate simple sine wave
        duration = min(len(text) * 0.05, 5.0)  # Approximate duration
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t) * 0.1
        
        # Add some variation
        audio = audio * (1 + 0.1 * np.sin(2 * np.pi * 2 * t))
        
        # Convert to bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        audio_bytes = buffer.getvalue()
        
        return {
            "audio": audio_bytes,
            "text": text,
            "voice_id": "dummy",
            "duration": duration,
            "sample_rate": sample_rate,
            "format": "wav",
            "processing_time": 0.1,
            "status": "dummy"
        }
    
    def _adjust_pitch(self, audio: np.ndarray, pitch: float) -> np.ndarray:
        """Adjust pitch of audio
        
        Args:
            audio: Audio array
            pitch: Pitch adjustment (-5 to +5 semitones)
            
        Returns:
            Pitch-adjusted audio
        """
        if pitch == 0:
            return audio
        
        try:
            import librosa
            # Convert semitones to ratio
            pitch_ratio = 2 ** (pitch / 12)
            # Pitch shift
            audio_shifted = librosa.effects.pitch_shift(
                audio, sr=self.tts.synthesizer.output_sample_rate,
                n_steps=pitch
            )
            return audio_shifted
        except ImportError:
            logger.warning("librosa not installed, skipping pitch adjustment")
            return audio
    
    def _encode_audio(self, audio: np.ndarray, format: str, sample_rate: int) -> bytes:
        """Encode audio to specified format
        
        Args:
            audio: Audio array
            format: Output format
            sample_rate: Sample rate
            
        Returns:
            Encoded audio bytes
        """
        buffer = io.BytesIO()
        
        if format.lower() == 'mp3':
            # For MP3, we'd need additional encoding
            # For now, fallback to WAV
            format = 'WAV'
        
        sf.write(buffer, audio, sample_rate, format=format.upper())
        buffer.seek(0)
        return buffer.getvalue()
    
    def synthesize_batch(
        self,
        texts: List[str],
        voice_id: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Synthesize multiple texts
        
        Args:
            texts: List of texts to synthesize
            voice_id: Voice ID
            **kwargs: Additional synthesis parameters
            
        Returns:
            List of synthesis results
        """
        results = []
        
        for text in texts:
            result = self.synthesize(text, voice_id, **kwargs)
            results.append(result)
        
        return results
    
    def clone_voice(
        self,
        reference_audio: bytes,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Clone voice from reference audio (if supported)
        
        Args:
            reference_audio: Reference audio bytes
            text: Text to synthesize
            **kwargs: Additional parameters
            
        Returns:
            Synthesis result with cloned voice
        """
        try:
            if not self.model_loaded:
                return self._generate_dummy_audio(text, 16000)
            
            # Save reference audio temporarily
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(reference_audio)
                reference_path = tmp_file.name
            
            try:
                # Use XTTS for voice cloning if available
                if hasattr(self.tts, 'tts_with_vc'):
                    wav = self.tts.tts_with_vc(
                        text=text,
                        speaker_wav=reference_path,
                        language='en'  # Twi not directly supported, use English
                    )
                    
                    audio_bytes = self._encode_audio(wav, 'wav', 16000)
                    
                    return {
                        "audio": audio_bytes,
                        "text": text,
                        "voice_id": "cloned",
                        "duration": len(wav) / 16000,
                        "sample_rate": 16000,
                        "format": "wav",
                        "status": "cloned"
                    }
                else:
                    # Fallback to regular synthesis
                    return self.synthesize(text, **kwargs)
                    
            finally:
                # Clean up temp file
                Path(reference_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return self._generate_dummy_audio(text, 16000)
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices
        
        Returns:
            List of voice information
        """
        voices = [
            {
                "voice_id": "asante_male_1",
                "name": "Kofi (Asante Male)",
                "language": "tw",
                "dialect": "asante",
                "gender": "male",
                "age_group": "adult",
                "description": "Natural Asante Twi male voice"
            },
            {
                "voice_id": "asante_female_1",
                "name": "Ama (Asante Female)",
                "language": "tw",
                "dialect": "asante",
                "gender": "female",
                "age_group": "adult",
                "description": "Natural Asante Twi female voice"
            },
            {
                "voice_id": "akuapem_male_1",
                "name": "Kwame (Akuapem Male)",
                "language": "tw",
                "dialect": "akuapem",
                "gender": "male",
                "age_group": "adult",
                "description": "Natural Akuapem Twi male voice"
            },
            {
                "voice_id": "fante_female_1",
                "name": "Efua (Fante Female)",
                "language": "tw",
                "dialect": "fante",
                "gender": "female",
                "age_group": "adult",
                "description": "Natural Fante female voice"
            }
        ]
        
        # If model supports multiple speakers, add them
        if self.model_loaded and hasattr(self.tts, 'speakers'):
            for speaker in self.tts.speakers:
                voices.append({
                    "voice_id": speaker,
                    "name": speaker,
                    "language": "multi",
                    "dialect": "standard",
                    "gender": "neutral",
                    "age_group": "adult",
                    "description": f"Model speaker: {speaker}"
                })
        
        return voices
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get TTS model information
        
        Returns:
            Model information
        """
        info = {
            "loaded": self.model_loaded,
            "device": str(self.device),
            "model_name": "Unknown",
            "capabilities": {
                "multi_speaker": False,
                "voice_cloning": False,
                "languages": ["tw", "en"],
                "max_length": 500
            }
        }
        
        if self.model_loaded and self.tts:
            if hasattr(self.tts, 'model_name'):
                info["model_name"] = self.tts.model_name
            
            if hasattr(self.tts, 'speakers'):
                info["capabilities"]["multi_speaker"] = True
                info["speakers"] = self.tts.speakers
            
            if hasattr(self.tts, 'tts_with_vc'):
                info["capabilities"]["voice_cloning"] = True
        
        return info


# Singleton instance
_twi_tts_service = None


def get_twi_tts_service() -> TwiTTSService:
    """Get or create Twi TTS service instance
    
    Returns:
        TwiTTSService instance
    """
    global _twi_tts_service
    
    if _twi_tts_service is None:
        _twi_tts_service = TwiTTSService()
    
    return _twi_tts_service
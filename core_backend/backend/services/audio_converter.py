"""
Audio format converter for handling WebM/Opus and other formats
Converts various audio formats to PCM for processing
"""

import io
import logging
import numpy as np
import subprocess
import tempfile
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AudioConverter:
    """Converts various audio formats to PCM for processing"""
    
    @staticmethod
    def convert_webm_to_pcm(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """
        Convert WebM/Opus audio to PCM using ffmpeg
        
        Args:
            audio_bytes: WebM/Opus audio bytes
            
        Returns:
            PCM audio array and sample rate
        """
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
                webm_file.write(audio_bytes)
                webm_path = webm_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_path = wav_file.name
            
            try:
                # Convert WebM to WAV using ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', webm_path,
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono
                    '-y',            # Overwrite output
                    wav_path
                ]
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg conversion failed: {result.stderr.decode()}")
                    raise RuntimeError("Audio conversion failed")
                
                # Read WAV file
                import wave
                with wave.open(wav_path, 'rb') as wav:
                    frames = wav.readframes(wav.getnframes())
                    sample_rate = wav.getframerate()
                    
                # Convert to numpy array
                audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                
                return audio_array, sample_rate
                
            finally:
                # Clean up temporary files
                os.unlink(webm_path)
                os.unlink(wav_path)
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            raise RuntimeError("Audio conversion timed out")
        except FileNotFoundError:
            logger.error("FFmpeg not found. Install with: apt-get install ffmpeg")
            raise RuntimeError("FFmpeg not installed")
        except Exception as e:
            logger.error(f"Failed to convert WebM audio: {e}")
            raise
    
    @staticmethod
    def detect_format(audio_bytes: bytes) -> str:
        """
        Detect audio format from bytes
        
        Args:
            audio_bytes: Audio data bytes
            
        Returns:
            Format string ('webm', 'wav', 'mp3', etc.)
        """
        # Check for WebM signature
        if audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
            return 'webm'
        
        # Check for WAV signature
        if audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
            return 'wav'
        
        # Check for MP3 signatures
        if audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb':
            return 'mp3'
        
        # Check for OGG signature
        if audio_bytes[:4] == b'OggS':
            return 'ogg'
        
        return 'unknown'
    
    @staticmethod
    def convert_to_pcm(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """
        Convert any supported audio format to PCM
        
        Args:
            audio_bytes: Audio data in any supported format
            
        Returns:
            PCM audio array and sample rate
        """
        format_type = AudioConverter.detect_format(audio_bytes)
        logger.info(f"Detected audio format: {format_type}")
        
        if format_type == 'webm':
            return AudioConverter.convert_webm_to_pcm(audio_bytes)
        elif format_type == 'wav':
            # WAV is already PCM, just decode
            import wave
            import io
            wav_io = io.BytesIO(audio_bytes)
            with wave.open(wav_io, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                sample_rate = wav.getframerate()
            audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            return audio_array, sample_rate
        else:
            # Try generic ffmpeg conversion for other formats
            return AudioConverter.convert_webm_to_pcm(audio_bytes)
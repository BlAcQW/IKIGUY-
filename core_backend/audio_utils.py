"""
Audio processing utilities using pydub for Python 3.12 compatibility.
Alternative to librosa for basic audio operations.
"""

import os
import tempfile
from typing import Optional, Tuple
from pydub import AudioSegment
import soundfile as sf
import numpy as np


def load_audio(file_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Load audio file and convert to target sample rate.
    
    Args:
        file_path: Path to audio file
        target_sr: Target sample rate (default: 16000)
    
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    try:
        # Load audio with pydub
        audio = AudioSegment.from_file(file_path)
        
        # Convert to target sample rate
        audio = audio.set_frame_rate(target_sr)
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            audio.export(temp_file.name, format='wav')
            temp_path = temp_file.name
        
        # Load with soundfile for numpy array
        audio_data, sr = sf.read(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return audio_data, sr
        
    except Exception as e:
        raise RuntimeError(f"Failed to load audio file {file_path}: {str(e)}")


def save_audio(audio_data: np.ndarray, file_path: str, sample_rate: int = 16000) -> None:
    """
    Save audio data to file.
    
    Args:
        audio_data: Audio data as numpy array
        file_path: Output file path
        sample_rate: Sample rate (default: 16000)
    """
    try:
        sf.write(file_path, audio_data, sample_rate)
    except Exception as e:
        raise RuntimeError(f"Failed to save audio file {file_path}: {str(e)}")


def get_audio_duration(file_path: str) -> float:
    """
    Get duration of audio file in seconds.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Duration in seconds
    """
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # Convert milliseconds to seconds
    except Exception as e:
        raise RuntimeError(f"Failed to get duration for {file_path}: {str(e)}")


def convert_audio_format(input_path: str, output_path: str, output_format: str = 'wav') -> None:
    """
    Convert audio file to different format.
    
    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        output_format: Output format (wav, mp3, etc.)
    """
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=output_format)
    except Exception as e:
        raise RuntimeError(f"Failed to convert audio format: {str(e)}")


def normalize_audio(audio_data: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """
    Normalize audio to target dB level.
    
    Args:
        audio_data: Audio data as numpy array
        target_db: Target dB level (default: -20.0)
    
    Returns:
        Normalized audio data
    """
    try:
        # Convert to pydub AudioSegment
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, 16000)
            temp_path = temp_file.name
        
        audio = AudioSegment.from_wav(temp_path)
        
        # Normalize
        normalized_audio = audio.normalize(headroom=target_db)
        
        # Export back to numpy array
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file2:
            normalized_audio.export(temp_file2.name, format='wav')
            temp_path2 = temp_file2.name
        
        normalized_data, _ = sf.read(temp_path2)
        
        # Clean up temp files
        os.unlink(temp_path)
        os.unlink(temp_path2)
        
        return normalized_data
        
    except Exception as e:
        raise RuntimeError(f"Failed to normalize audio: {str(e)}")


def trim_silence(audio_data: np.ndarray, sample_rate: int = 16000, 
                silence_threshold: float = -40.0, min_silence_len: int = 1000) -> np.ndarray:
    """
    Trim silence from beginning and end of audio.
    
    Args:
        audio_data: Audio data as numpy array
        sample_rate: Sample rate
        silence_threshold: Silence threshold in dB
        min_silence_len: Minimum silence length in ms
    
    Returns:
        Trimmed audio data
    """
    try:
        # Convert to pydub AudioSegment
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            temp_path = temp_file.name
        
        audio = AudioSegment.from_wav(temp_path)
        
        # Trim silence
        trimmed_audio = audio.strip_silence(
            silence_len=min_silence_len,
            silence_thresh=silence_threshold
        )
        
        # Export back to numpy array
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file2:
            trimmed_audio.export(temp_file2.name, format='wav')
            temp_path2 = temp_file2.name
        
        trimmed_data, _ = sf.read(temp_path2)
        
        # Clean up temp files
        os.unlink(temp_path)
        os.unlink(temp_path2)
        
        return trimmed_data
        
    except Exception as e:
        raise RuntimeError(f"Failed to trim silence: {str(e)}")


def get_audio_info(file_path: str) -> dict:
    """
    Get audio file information.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Dictionary with audio information
    """
    try:
        audio = AudioSegment.from_file(file_path)
        info = {
            'duration_ms': len(audio),
            'duration_seconds': len(audio) / 1000.0,
            'channels': audio.channels,
            'sample_rate': audio.frame_rate,
            'sample_width': audio.sample_width,
            'frame_count': audio.frame_count(),
            'max_possible_amplitude': audio.max_possible_amplitude,
            'dBFS': audio.dBFS
        }
        return info
    except Exception as e:
        raise RuntimeError(f"Failed to get audio info for {file_path}: {str(e)}")


# Example usage and compatibility functions
def librosa_compatible_load(file_path: str, sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
    """
    librosa-compatible load function using pydub.
    
    Args:
        file_path: Path to audio file
        sr: Sample rate (if None, uses original sample rate)
    
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    if sr is None:
        # Load with original sample rate
        audio = AudioSegment.from_file(file_path)
        sr = audio.frame_rate
    
    return load_audio(file_path, sr)


def librosa_compatible_get_duration(file_path: str) -> float:
    """
    librosa-compatible get_duration function.
    
    Args:
        file_path: Path to audio file
    
    Returns:
        Duration in seconds
    """
    return get_audio_duration(file_path)

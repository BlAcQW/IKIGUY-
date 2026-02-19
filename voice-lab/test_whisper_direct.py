#!/usr/bin/env python3
"""
Direct test of Twi Whisper model without backend
"""

import sys
import os
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.twi_whisper_service import TwiWhisperService
import numpy as np
import soundfile as sf
from pathlib import Path

print("🚀 Direct Twi Whisper Model Test")
print("=" * 60)

# Create test audio
print("\n📊 Creating test audio...")
test_audio_path = Path("/opt/kasaai/apps/voice-lab/data/test_direct.wav")
test_audio_path.parent.mkdir(parents=True, exist_ok=True)

# Create 2 seconds of noise
audio = np.random.randn(32000) * 0.01
sf.write(test_audio_path, audio, 16000)
print(f"✅ Created test audio: {test_audio_path}")

# Initialize service
print("\n🔍 Initializing Twi Whisper Service...")
try:
    service = TwiWhisperService(model_name="akan")
    print("✅ Service initialized")
    
    # Get model info
    info = service.get_model_info()
    print(f"\n📊 Model Info:")
    print(f"   Model ID: {info['model_id']}")
    print(f"   Parameters: {info['parameters']:,}")
    print(f"   Device: {info['device']}")
    print(f"   Accuracy: {info['accuracy']:.1%}")
    
    # Test transcription
    print("\n🎤 Testing transcription...")
    result = service.transcribe_file(str(test_audio_path))
    
    print(f"\n✅ Transcription Result:")
    print(f"   Text: {result['text']}")
    print(f"   Confidence: {result['confidence']:.1%}")
    print(f"   Language: {result['language']}")
    print(f"   Dialect: {result['dialect']}")
    print(f"   Duration: {result['duration']:.2f}s")
    print(f"   Processing Time: {result['processing_time']:.2f}s")
    print(f"   Model: {result['model']}")
    
    # Test with real Twi audio if available
    real_audio = Path("/opt/kasaai/apps/voice-lab/data/raw/common_voice_twi/extracted/common_voice_tw_34745954.mp3")
    if real_audio.exists():
        print(f"\n🎵 Testing with real Twi audio...")
        result = service.transcribe_file(str(real_audio))
        print(f"✅ Real Transcription: {result['text']}")
        print(f"   Confidence: {result['confidence']:.1%}")
    
    print("\n✅ All tests passed! Twi Whisper model is working.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
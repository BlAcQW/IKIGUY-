#!/usr/bin/env python3
"""
Test simple TTS with gTTS
"""

import sys
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.simple_tts_service import SimpleTTSService

print("🚀 Simple TTS Test (gTTS)")
print("=" * 60)

# Initialize service
service = SimpleTTSService()

# Get model info
info = service.get_model_info()
print(f"\n📊 TTS Info:")
print(f"   Engine: {info['engine']}")
print(f"   Model: {info['model_name']}")
print(f"   Loaded: {info['loaded']}")

# Test texts
test_texts = [
    "Hello, this is a test",
    "Me ma wo akye",  # Twi greeting
    "Welcome to Voice Lab"
]

print("\n🎤 Testing synthesis...")
for i, text in enumerate(test_texts):
    print(f"\n[{i+1}] Text: '{text}'")
    
    result = service.synthesize(text)
    
    print(f"   Status: {result['status']}")
    print(f"   Engine: {result['engine']}")
    print(f"   Duration: {result['duration']:.2f}s")
    print(f"   Format: {result['format']}")
    print(f"   Audio size: {len(result['audio'])} bytes")
    
    # Save audio
    ext = result['format']
    output_path = f"/opt/kasaai/apps/voice-lab/data/simple_tts_{i}.{ext}"
    with open(output_path, 'wb') as f:
        f.write(result['audio'])
    print(f"   Saved to: {output_path}")

print("\n✅ Simple TTS test complete!")
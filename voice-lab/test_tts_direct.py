#!/usr/bin/env python3
"""
Direct test of Twi TTS model
"""

import sys
import os
sys.path.append('/opt/kasaai/apps/core_backend')

print("🚀 Direct Twi TTS Model Test")
print("=" * 60)

# Check if TTS is available
try:
    from TTS.api import TTS
    print("✅ Coqui TTS is installed")
    
    # List available models
    models = TTS.list_models()
    print(f"\n📊 Available TTS models: {len(models)}")
    
    # Show first few models
    print("\nSample models:")
    for model in models[:5]:
        print(f"  - {model}")
    
    # Check for multilingual models
    multilingual = [m for m in models if 'multilingual' in m]
    print(f"\n🌍 Multilingual models: {len(multilingual)}")
    for model in multilingual:
        print(f"  - {model}")
        
except ImportError:
    print("❌ Coqui TTS not installed")
    print("Installing TTS...")
    os.system("pip install -q TTS")
    print("Please run the script again after installation")
    sys.exit(1)

# Test the TTS service
try:
    from backend.services.twi_tts_service import TwiTTSService
    
    print("\n🔍 Initializing Twi TTS Service...")
    service = TwiTTSService()
    
    # Get model info
    info = service.get_model_info()
    print(f"\n📊 TTS Model Info:")
    print(f"   Loaded: {info['loaded']}")
    print(f"   Device: {info['device']}")
    print(f"   Model: {info['model_name']}")
    print(f"   Multi-speaker: {info['capabilities']['multi_speaker']}")
    print(f"   Voice cloning: {info['capabilities']['voice_cloning']}")
    
    # Get available voices
    voices = service.get_available_voices()
    print(f"\n🎭 Available Voices: {len(voices)}")
    for voice in voices[:3]:
        print(f"   - {voice['name']} ({voice['voice_id']}): {voice['description']}")
    
    # Test synthesis
    print("\n🎤 Testing TTS synthesis...")
    test_texts = [
        "Me ma wo akye",
        "Wo ho te sɛn?",
        "Me pɛ sɛ mekasa Twi"
    ]
    
    for text in test_texts:
        print(f"\nSynthesizing: '{text}'")
        result = service.synthesize(text)
        
        print(f"   Status: {result['status']}")
        print(f"   Duration: {result['duration']:.2f}s")
        print(f"   Processing time: {result['processing_time']:.3f}s")
        print(f"   Audio size: {len(result['audio'])} bytes")
        
        # Save to file
        output_path = f"/opt/kasaai/apps/voice-lab/data/tts_test_{test_texts.index(text)}.wav"
        with open(output_path, 'wb') as f:
            f.write(result['audio'])
        print(f"   Saved to: {output_path}")
    
    print("\n✅ TTS test complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
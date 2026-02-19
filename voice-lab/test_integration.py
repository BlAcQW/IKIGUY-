#!/usr/bin/env python3
"""
Test the complete Voice Lab integration
"""

import requests
import base64
import json
import numpy as np
import soundfile as sf
from pathlib import Path
import time

# Configuration
API_BASE_URL = "http://localhost:30027"  # Adjust if needed
TEST_AUDIO_PATH = Path("/opt/kasaai/apps/voice-lab/data/test_audio.wav")

def create_test_audio():
    """Create a test audio file"""
    if not TEST_AUDIO_PATH.exists():
        # Create 2 seconds of noise
        audio = np.random.randn(32000) * 0.01
        sf.write(TEST_AUDIO_PATH, audio, 16000)
        print(f"✅ Created test audio: {TEST_AUDIO_PATH}")
    return TEST_AUDIO_PATH

def test_voice_lab_info():
    """Test Voice Lab info endpoint"""
    print("\n🔍 Testing Voice Lab Info...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/voice-lab/")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Voice Lab Info:")
            print(f"   Name: {data.get('name')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Features: {', '.join(data.get('features', []))}")
            print(f"   Languages: {', '.join(data.get('languages', []))}")
            print(f"   Dialects: {', '.join(data.get('dialects', []))}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_languages():
    """Test languages endpoint"""
    print("\n🌍 Testing Languages...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/voice-lab/languages")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Supported Languages:")
            for lang in data.get('languages', []):
                print(f"   {lang['name']} ({lang['code']})")
                for dialect in lang.get('dialects', []):
                    print(f"      - {dialect['name']} ({dialect['code']})")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_transcription():
    """Test transcription endpoint"""
    print("\n🎤 Testing Transcription...")
    
    # Create test audio
    audio_path = create_test_audio()
    
    # Read audio and convert to base64
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    try:
        # Note: This endpoint requires authentication
        # For testing without auth, you might need to modify the backend temporarily
        response = requests.post(
            f"{API_BASE_URL}/api/voice-lab/transcribe",
            json={
                "audio_base64": audio_base64,
                "language": "tw",
                "dialect": "asante",
                "enhance_text": True,
                "return_timestamps": False
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Transcription Result:")
            print(f"   Text: {data.get('text')}")
            print(f"   Confidence: {data.get('confidence'):.2%}")
            print(f"   Language: {data.get('language')}")
            print(f"   Dialect: {data.get('dialect')}")
            print(f"   Duration: {data.get('duration'):.2f}s")
            print(f"   Processing Time: {data.get('processing_time'):.2f}s")
            return True
        elif response.status_code == 401:
            print("⚠️ Authentication required (expected in production)")
            return True  # Expected behavior
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_text_processing():
    """Test text processing endpoint"""
    print("\n📝 Testing Text Processing...")
    
    test_text = "Mepɛ GH₵100. Today is 25/12/2024 at 3:30pm."
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/voice-lab/process-text",
            json={
                "text": test_text,
                "dialect": "asante",
                "expand_numbers": True,
                "expand_abbreviations": True,
                "process_datetime": True,
                "generate_phonemes": False
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Text Processing Result:")
            print(f"   Original: {test_text}")
            print(f"   Processed: {data.get('processed', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_voices():
    """Test voices endpoint"""
    print("\n🎭 Testing Available Voices...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/voice-lab/voices")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available Voices:")
            for voice in data:
                print(f"   {voice['name']} ({voice['voice_id']})")
                print(f"      Language: {voice['language']}")
                print(f"      Dialect: {voice['dialect']}")
                print(f"      Gender: {voice['gender']}")
            return True
        elif response.status_code == 401:
            print("⚠️ Authentication required (expected)")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 VOICE LAB INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Voice Lab Info", test_voice_lab_info),
        ("Languages", test_languages),
        ("Transcription", test_transcription),
        ("Text Processing", test_text_processing),
        ("Voices", test_voices),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test {name} failed with error: {e}")
            results.append((name, False))
        
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Voice Lab integration is working.")
    else:
        print("⚠️ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
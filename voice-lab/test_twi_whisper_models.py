#!/usr/bin/env python3
"""
Test existing Twi Whisper models from HuggingFace
"""

import os
import sys
import torch
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("🚀 Testing Existing Twi Whisper Models")
print("=" * 60)

# Check environment
print(f"🔥 PyTorch version: {torch.__version__}")
print(f"🎯 CUDA available: {torch.cuda.is_available()}")

# Available Twi models
TWI_MODELS = [
    "jackiejoe45/twi_trained_whisper",  # WER: 14%
    "GiftMark/akan-whisper-model",      # Akan (includes Twi)
    "dkt-py-bot/whisper-small-DL-Twi",  # Fine-tuned on Twi
    "dkt-py-bot/Whisper-FineTuned-DL-Twi",  # Another Twi model
    "jdapaah/whisper-small-twi-arxiv",  # Common Voice 16.0
]

# Data paths
DATA_PATH = Path('/opt/kasaai/apps/voice-lab/data')
OUTPUT_PATH = Path('/opt/kasaai/apps/voice-lab/models/twi_whisper_hf')
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

# Test audio preparation
import soundfile as sf
import librosa

test_audio_path = DATA_PATH / "test_twi_whisper.wav"
if not test_audio_path.exists():
    print("\n📊 Creating test audio...")
    # Create 2 seconds of noise for testing
    audio = np.random.randn(32000) * 0.01
    sf.write(test_audio_path, audio, 16000)
    print(f"✅ Created test audio: {test_audio_path}")

# Load real data if available
metadata_path = DATA_PATH / 'metadata/all_datasets_processed.csv'
real_audio = None
real_text = None

if metadata_path.exists():
    df = pd.read_csv(metadata_path)
    # Try to find a real audio file
    for idx, row in df.iterrows():
        audio_path = row.get('audio_path', row.get('audio', ''))
        text = row.get('processed_text', row.get('original_text', ''))
        
        if audio_path and Path(audio_path).exists():
            real_audio = audio_path
            real_text = text
            print(f"\n✅ Found real Twi audio: {Path(audio_path).name}")
            print(f"📝 Expected text: {text[:100]}...")
            break

# Test models
from transformers import WhisperProcessor, WhisperForConditionalGeneration

results = []

for model_id in TWI_MODELS:
    print(f"\n{'='*60}")
    print(f"🎯 Testing: {model_id}")
    print(f"{'='*60}")
    
    try:
        # Load processor and model
        print(f"📥 Loading model...")
        processor = WhisperProcessor.from_pretrained(model_id)
        model = WhisperForConditionalGeneration.from_pretrained(model_id)
        
        # Get model info
        num_params = model.num_parameters()
        print(f"✅ Model loaded: {num_params:,} parameters")
        
        # Test on dummy audio
        print(f"\n🎤 Testing on dummy audio...")
        audio, sr = librosa.load(test_audio_path, sr=16000)
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
        
        with torch.no_grad():
            predicted_ids = model.generate(inputs.input_features)
        
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        print(f"📝 Dummy transcription: '{transcription}'")
        
        # Test on real audio if available
        if real_audio:
            print(f"\n🎵 Testing on real Twi audio...")
            try:
                audio, sr = librosa.load(real_audio, sr=16000)
                # Limit to 30 seconds
                if len(audio) > 30 * 16000:
                    audio = audio[:30 * 16000]
                
                inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
                
                with torch.no_grad():
                    predicted_ids = model.generate(inputs.input_features)
                
                transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
                print(f"📝 Real transcription: '{transcription}'")
                print(f"📝 Expected: '{real_text[:100]}'")
                
                # Calculate simple accuracy (character overlap)
                if real_text:
                    common_chars = sum(1 for c in transcription.lower() if c in real_text.lower())
                    accuracy = common_chars / max(len(transcription), len(real_text)) * 100
                    print(f"📊 Character overlap: {accuracy:.1f}%")
            except Exception as e:
                print(f"⚠️ Error with real audio: {e}")
        
        # Save results
        results.append({
            "model": model_id,
            "parameters": num_params,
            "status": "success",
            "transcription": transcription
        })
        
        print(f"✅ Model test complete!")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        results.append({
            "model": model_id,
            "parameters": 0,
            "status": "failed",
            "error": str(e)
        })

# Summary
print(f"\n{'='*60}")
print("📊 SUMMARY OF TWI WHISPER MODELS")
print(f"{'='*60}")

for result in results:
    status_icon = "✅" if result["status"] == "success" else "❌"
    print(f"\n{status_icon} {result['model']}")
    if result["status"] == "success":
        print(f"   Parameters: {result['parameters']:,}")
        print(f"   Sample output: {result.get('transcription', 'N/A')[:50]}...")
    else:
        print(f"   Error: {result.get('error', 'Unknown')[:100]}...")

# Recommend best model
successful_models = [r for r in results if r["status"] == "success"]
if successful_models:
    best_model = successful_models[0]["model"]
    print(f"\n🏆 RECOMMENDATION: Use {best_model}")
    print(f"   This model loaded successfully and can transcribe audio")
    
    # Save recommendation
    import json
    recommendation = {
        "recommended_model": best_model,
        "all_models_tested": TWI_MODELS,
        "successful_models": [r["model"] for r in successful_models],
        "test_date": str(pd.Timestamp.now())
    }
    
    with open(OUTPUT_PATH / "model_recommendation.json", "w") as f:
        json.dump(recommendation, f, indent=2)
    
    print(f"\n💾 Saved recommendation to {OUTPUT_PATH}/model_recommendation.json")

print(f"\n{'='*60}")
print("✅ Testing complete!")
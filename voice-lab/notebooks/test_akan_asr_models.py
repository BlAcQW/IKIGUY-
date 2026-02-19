#!/usr/bin/env python3
"""
Test Akan/Twi ASR Models
Demonstrates the two models you asked about:
1. azunre/wav2vec2large-xlsr-akan - Wav2Vec2 large with XLSR architecture
2. GiftMark/akan-whisper-model - Fine-tuned Whisper-small for Akan

This script tests both models and compares their performance.
"""

import torch
import librosa
import numpy as np
from transformers import (
    Wav2Vec2Processor,
    Wav2Vec2ForCTC,
    WhisperProcessor,
    WhisperForConditionalGeneration,
    pipeline
)
import time
from pathlib import Path

class AkanASRTester:
    """Test Akan/Twi ASR models."""
    
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.models = {}
        print(f"Using device: {self.device}")
    
    def load_wav2vec2_akan(self):
        """Load azunre/wav2vec2large-xlsr-akan model."""
        print("Loading azunre/wav2vec2large-xlsr-akan...")
        
        try:
            model_id = "azunre/wav2vec2large-xlsr-akan"
            
            processor = Wav2Vec2Processor.from_pretrained(model_id)
            model = Wav2Vec2ForCTC.from_pretrained(model_id)
            model = model.to(self.device)
            
            self.models['wav2vec2_akan'] = {
                'model': model,
                'processor': processor,
                'type': 'wav2vec2',
                'name': 'Wav2Vec2-Large-XLSR-Akan',
                'status': 'loaded'
            }
            
            print("✓ Wav2Vec2-Akan model loaded successfully")
            print(f"  Parameters: {model.num_parameters():,}")
            
        except Exception as e:
            print(f"✗ Error loading Wav2Vec2-Akan: {e}")
            self.models['wav2vec2_akan'] = {'status': 'error', 'error': str(e)}
    
    def load_whisper_akan(self):
        """Load GiftMark/akan-whisper-model."""
        print("Loading GiftMark/akan-whisper-model...")
        
        try:
            model_id = "GiftMark/akan-whisper-model"
            
            processor = WhisperProcessor.from_pretrained(model_id)
            model = WhisperForConditionalGeneration.from_pretrained(model_id)
            model = model.to(self.device)
            
            self.models['whisper_akan'] = {
                'model': model,
                'processor': processor,
                'type': 'whisper',
                'name': 'Whisper-Small-Akan',
                'status': 'loaded'
            }
            
            print("✓ Whisper-Akan model loaded successfully")
            print(f"  Parameters: {model.num_parameters():,}")
            
        except Exception as e:
            print(f"✗ Error loading Whisper-Akan: {e}")
            self.models['whisper_akan'] = {'status': 'error', 'error': str(e)}
    
    def transcribe_wav2vec2(self, audio_path: str) -> dict:
        """Transcribe using Wav2Vec2 model."""
        if 'wav2vec2_akan' not in self.models or self.models['wav2vec2_akan']['status'] != 'loaded':
            return {'error': 'Wav2Vec2 model not loaded'}
        
        model_info = self.models['wav2vec2_akan']
        model = model_info['model']
        processor = model_info['processor']
        
        try:
            # Load and preprocess audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Process audio
            inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Measure inference time
            start_time = time.time()
            
            with torch.no_grad():
                logits = model(**inputs).logits
            
            # Decode
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = processor.batch_decode(predicted_ids)[0]
            
            inference_time = time.time() - start_time
            
            return {
                'transcription': transcription,
                'inference_time': inference_time,
                'audio_duration': len(audio) / sr,
                'real_time_factor': inference_time / (len(audio) / sr),
                'model': 'Wav2Vec2-Akan'
            }
            
        except Exception as e:
            return {'error': f'Transcription failed: {e}', 'model': 'Wav2Vec2-Akan'}
    
    def transcribe_whisper(self, audio_path: str) -> dict:
        """Transcribe using Whisper model."""
        if 'whisper_akan' not in self.models or self.models['whisper_akan']['status'] != 'loaded':
            return {'error': 'Whisper model not loaded'}
        
        model_info = self.models['whisper_akan']
        model = model_info['model']
        processor = model_info['processor']
        
        try:
            # Load and preprocess audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Process audio
            input_features = processor(
                audio, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).input_features
            input_features = input_features.to(self.device)
            
            # Measure inference time
            start_time = time.time()
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = model.generate(input_features)
                
            transcription = processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0]
            
            inference_time = time.time() - start_time
            
            return {
                'transcription': transcription,
                'inference_time': inference_time,
                'audio_duration': len(audio) / sr,
                'real_time_factor': inference_time / (len(audio) / sr),
                'model': 'Whisper-Akan'
            }
            
        except Exception as e:
            return {'error': f'Transcription failed: {e}', 'model': 'Whisper-Akan'}
    
    def compare_models(self, audio_path: str) -> dict:
        """Compare both models on the same audio."""
        print(f"\nTesting both models on: {audio_path}")
        print("=" * 50)
        
        results = {}
        
        # Test Wav2Vec2
        wav2vec2_result = self.transcribe_wav2vec2(audio_path)
        results['wav2vec2'] = wav2vec2_result
        
        print(f"\nWav2Vec2-Akan Results:")
        if 'error' in wav2vec2_result:
            print(f"  ✗ Error: {wav2vec2_result['error']}")
        else:
            print(f"  ✓ Transcription: '{wav2vec2_result['transcription']}'")
            print(f"  ⏱️ Inference time: {wav2vec2_result['inference_time']:.3f}s")
            print(f"  📊 Real-time factor: {wav2vec2_result['real_time_factor']:.3f}")
        
        # Test Whisper
        whisper_result = self.transcribe_whisper(audio_path)
        results['whisper'] = whisper_result
        
        print(f"\nWhisper-Akan Results:")
        if 'error' in whisper_result:
            print(f"  ✗ Error: {whisper_result['error']}")
        else:
            print(f"  ✓ Transcription: '{whisper_result['transcription']}'")
            print(f"  ⏱️ Inference time: {whisper_result['inference_time']:.3f}s")
            print(f"  📊 Real-time factor: {whisper_result['real_time_factor']:.3f}")
        
        return results
    
    def generate_test_audio(self, text: str = "Hello, this is a test", output_path: str = "test_audio.wav"):
        """Generate synthetic test audio for demonstration."""
        try:
            from gtts import gTTS
            import io
            
            # Create TTS audio (English for demo)
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to file
            tts.save(output_path)
            print(f"✓ Test audio generated: {output_path}")
            return output_path
            
        except ImportError:
            print("gtts not available for test audio generation")
            return None
        except Exception as e:
            print(f"Error generating test audio: {e}")
            return None
    
    def model_summary(self):
        """Print summary of loaded models."""
        print("\n" + "=" * 60)
        print("AKAN/TWI ASR MODELS SUMMARY")
        print("=" * 60)
        
        for model_key, model_info in self.models.items():
            print(f"\n{model_info.get('name', model_key)}:")
            print(f"  Status: {model_info['status']}")
            
            if model_info['status'] == 'loaded':
                print(f"  Type: {model_info['type']}")
                print(f"  Device: {self.device}")
                
                if 'model' in model_info:
                    params = model_info['model'].num_parameters()
                    print(f"  Parameters: {params:,}")
            
            elif model_info['status'] == 'error':
                print(f"  Error: {model_info.get('error', 'Unknown error')}")

def main():
    """Main testing function."""
    print("🎵 AKAN/TWI ASR MODEL TESTING")
    print("=" * 60)
    print("Testing the two models you asked about:")
    print("1. azunre/wav2vec2large-xlsr-akan")
    print("2. GiftMark/akan-whisper-model")
    print()
    
    # Initialize tester
    tester = AkanASRTester()
    
    # Load models
    print("Loading models...")
    tester.load_wav2vec2_akan()
    print()
    tester.load_whisper_akan()
    
    # Print summary
    tester.model_summary()
    
    # Test with synthetic audio if no real audio available
    test_audio = tester.generate_test_audio("Akwaaba, me din de Kofi", "akan_test.wav")
    
    if test_audio and Path(test_audio).exists():
        # Compare models
        results = tester.compare_models(test_audio)
        
        print("\n" + "=" * 60)
        print("CONCLUSION:")
        print("=" * 60)
        
        # Model comparison
        if any('error' not in r for r in results.values()):
            print("✅ At least one model loaded successfully")
            
            # Performance comparison
            for model_name, result in results.items():
                if 'error' not in result:
                    rtf = result['real_time_factor']
                    if rtf < 0.3:
                        print(f"✅ {result['model']} meets real-time requirements (RTF: {rtf:.3f})")
                    else:
                        print(f"⚠️  {result['model']} may be slow for real-time (RTF: {rtf:.3f})")
        else:
            print("❌ Both models failed to load")
            print("This may be due to:")
            print("  - Network connectivity issues")
            print("  - Missing dependencies")
            print("  - Model repository access")
    
    else:
        print("\n⚠️  No test audio available for comparison")
        print("Models are loaded and ready for audio input")

if __name__ == "__main__":
    main()
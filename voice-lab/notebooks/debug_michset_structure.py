#!/usr/bin/env python
"""
Debug MichSet dataset structure to understand why audio extraction is failing
"""

import sys
from pathlib import Path

# Add Google Drive path
sys.path.append('/content/drive/MyDrive/voice-lab-data')

try:
    from datasets import load_from_disk
    import json
    print("✅ Required libraries imported")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Installing required packages...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "datasets"], check=True)
    from datasets import load_from_disk
    import json

# Setup paths
BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')
MICHSET_DIR = BASE_DIR / 'raw' / 'michsethowusu'

print("🔍 MICHSET DATASET STRUCTURE ANALYSIS")
print("=" * 60)

print(f"Base directory: {BASE_DIR}")
print(f"MichSet directory: {MICHSET_DIR}")
print(f"MichSet exists: {MICHSET_DIR.exists()}")

if MICHSET_DIR.exists():
    print(f"\nContents of {MICHSET_DIR}:")
    for item in MICHSET_DIR.iterdir():
        print(f"  📁 {item.name} {'(dir)' if item.is_dir() else '(file)'}")

# Check each dataset
datasets_to_check = [
    'twi_multispeaker_audio_transcribed',
    'akuapem_multispeaker_audio_transcribed', 
    'fante_multispeaker_audio_transcribed'
]

for dataset_name in datasets_to_check:
    dataset_path = MICHSET_DIR / dataset_name
    
    print(f"\n📊 ANALYZING: {dataset_name}")
    print("-" * 50)
    print(f"Path: {dataset_path}")
    print(f"Exists: {dataset_path.exists()}")
    
    if not dataset_path.exists():
        continue
    
    try:
        # Load dataset
        print("Loading dataset...")
        dataset = load_from_disk(str(dataset_path))
        
        print(f"Dataset keys: {list(dataset.keys())}")
        
        if 'train' in dataset:
            train_data = dataset['train']
            print(f"Train samples: {len(train_data)}")
            print(f"Train features: {train_data.features}")
            
            # Check first few samples
            print(f"\n🔍 First 3 samples analysis:")
            for i in range(min(3, len(train_data))):
                print(f"\nSample {i}:")
                sample = train_data[i]
                print(f"  Keys: {list(sample.keys())}")
                
                # Check each key
                for key, value in sample.items():
                    if key == 'audio':
                        print(f"  {key}: {type(value)}")
                        if isinstance(value, dict):
                            print(f"    Audio keys: {list(value.keys())}")
                            if 'array' in value:
                                array = value['array']
                                print(f"    Array type: {type(array)}")
                                print(f"    Array length: {len(array) if hasattr(array, '__len__') else 'unknown'}")
                            if 'sampling_rate' in value:
                                print(f"    Sample rate: {value['sampling_rate']}")
                            if 'path' in value:
                                print(f"    Path: {value['path']}")
                    elif key == 'audio_path':
                        print(f"  {key}: {value}")
                        # Check if path exists
                        if isinstance(value, str):
                            path_obj = Path(value)
                            print(f"    Path exists: {path_obj.exists()}")
                    elif key == 'transcription':
                        text_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"  {key}: {text_preview}")
                    else:
                        print(f"  {key}: {type(value)} - {str(value)[:30]}...")
            
            # Try to access audio data directly
            print(f"\n🎵 Testing audio access:")
            try:
                first_sample = train_data[0]
                
                # Method 1: Direct audio access
                if 'audio' in first_sample:
                    audio_data = first_sample['audio']
                    print(f"  Method 1 - Direct 'audio': {type(audio_data)}")
                    
                    if isinstance(audio_data, dict):
                        if 'array' in audio_data:
                            array = audio_data['array']
                            print(f"    Array available: {type(array)}, length: {len(array) if hasattr(array, '__len__') else 'unknown'}")
                            
                            # Try to convert to audio
                            try:
                                import numpy as np
                                if not isinstance(array, np.ndarray):
                                    array = np.array(array)
                                print(f"    Converted to numpy: shape {array.shape}, dtype {array.dtype}")
                                print(f"    Audio range: {np.min(array):.4f} to {np.max(array):.4f}")
                                
                                # Check if it's actual audio data
                                if np.max(np.abs(array)) > 0.001:
                                    print(f"    ✅ Looks like real audio data!")
                                else:
                                    print(f"    ❌ Looks like silent/zero data")
                                    
                            except Exception as e:
                                print(f"    ❌ Array conversion failed: {e}")
                
                # Method 2: Audio path access
                if 'audio_path' in first_sample:
                    audio_path = first_sample['audio_path']
                    print(f"  Method 2 - 'audio_path': {audio_path}")
                    
                    if isinstance(audio_path, str):
                        path_obj = Path(audio_path)
                        print(f"    Path exists: {path_obj.exists()}")
                        if path_obj.exists():
                            print(f"    File size: {path_obj.stat().st_size} bytes")
                
            except Exception as e:
                print(f"  ❌ Audio access test failed: {e}")
        
        else:
            print("❌ No 'train' split found")
            
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")

print(f"\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)

print(f"\n🔧 Based on this analysis, the audio extraction issue is likely:")
print(f"1. Audio data is in a different format than expected")
print(f"2. Audio arrays are silent/zero (no actual audio content)")  
print(f"3. Dataset structure has changed")
print(f"4. Audio data requires different decoding method")

print(f"\n💡 Recommendations:")
print(f"1. Check the exact audio data format and structure")
print(f"2. Verify audio arrays contain non-zero values")
print(f"3. Try alternative audio extraction methods")
print(f"4. Check if torchcodec is properly decoding the data")
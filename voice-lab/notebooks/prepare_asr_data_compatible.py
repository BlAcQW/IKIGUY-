#!/usr/bin/env python
"""
Fix ASR notebook data compatibility issues
Creates the exact data structure expected by 004_phase2_asr_development.ipynb
"""

import pandas as pd
from pathlib import Path
import json
import numpy as np

# Match the paths expected by ASR notebook
BASE_DIR = Path("G:/My Drive/voice-lab-data")
SPLITS_DIR = BASE_DIR / 'splits'  # ASR notebook expects this
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

print("ASR NOTEBOOK DATA COMPATIBILITY FIXES")
print("=" * 60)

# 1. Check what data we actually have
source_file = BASE_DIR / 'metadata' / 'processed_data_enhanced.csv'

if not source_file.exists():
    print(f"❌ ERROR: Source data not found at {source_file}")
    print("Run the updated 002_phase1_data_processing_enhanced.ipynb first!")
    exit(1)

# Load our processed data
df = pd.read_csv(source_file)
print(f"✅ Loaded {len(df)} samples from processed data")
print(f"Columns: {list(df.columns)}")
print(f"Sources: {df['source'].unique()}")

# 2. Check audio file availability
print(f"\n🔍 CHECKING AUDIO FILE AVAILABILITY:")
print("-" * 40)

# Test first 10 audio paths
sample_audio_paths = df['audio'].head(10).tolist()
existing_audio = 0
missing_audio = 0

for audio_path in sample_audio_paths:
    exists = Path(audio_path).exists()
    status = "✅" if exists else "❌"
    filename = Path(audio_path).name
    print(f"  {status} {filename}")
    
    if exists:
        existing_audio += 1
    else:
        missing_audio += 1

audio_availability = (existing_audio / len(sample_audio_paths)) * 100 if sample_audio_paths else 0
print(f"\n📊 Audio availability: {audio_availability:.1f}% ({existing_audio}/{len(sample_audio_paths)} checked)")

# 3. Create ASR-compatible splits
print(f"\n🎯 CREATING ASR-COMPATIBLE SPLITS:")
print("-" * 40)

# Filter data - prioritize real audio if available
if audio_availability > 0:
    print("Using samples with existing audio files...")
    # Check all audio files (this might take a while)
    df['audio_exists'] = df['audio'].apply(lambda x: Path(x).exists())
    working_df = df[df['audio_exists']].copy()
    working_df = working_df.drop('audio_exists', axis=1)
    print(f"  Real audio samples: {len(working_df)}")
else:
    print("No real audio files found - using all samples (for text processing)")
    working_df = df.copy()

if len(working_df) == 0:
    print("❌ No usable data found!")
    exit(1)

# Required columns for ASR notebook: 'audio', 'text'
required_columns = ['audio', 'text']
available_columns = list(working_df.columns)

print(f"\nColumn mapping:")
for col in required_columns:
    if col in available_columns:
        print(f"  ✅ {col}: available")
    else:
        print(f"  ❌ {col}: MISSING")

# Ensure we have the required columns
if 'text' not in working_df.columns:
    print("❌ Critical error: 'text' column missing!")
    exit(1)

if 'audio' not in working_df.columns:
    print("❌ Critical error: 'audio' column missing!")
    exit(1)

# Create train/validation/test splits (ASR notebook expects these exact files)
print(f"\n📁 Creating splits...")

# Shuffle data
working_df = working_df.sample(frac=1, random_state=42).reset_index(drop=True)

# Split ratios: 80% train, 10% validation, 10% test
n_samples = len(working_df)
n_train = int(0.8 * n_samples)
n_val = int(0.1 * n_samples)
n_test = n_samples - n_train - n_val

# Create splits
train_df = working_df[:n_train].copy()
val_df = working_df[n_train:n_train+n_val].copy()
test_df = working_df[n_train+n_val:].copy()

# Save splits in the format expected by ASR notebook
train_file = SPLITS_DIR / 'train.csv'
val_file = SPLITS_DIR / 'validation.csv'
test_file = SPLITS_DIR / 'test.csv'

train_df.to_csv(train_file, index=False)
val_df.to_csv(val_file, index=False)
test_df.to_csv(test_file, index=False)

print(f"  ✅ train.csv: {len(train_df)} samples")
print(f"  ✅ validation.csv: {len(val_df)} samples")
print(f"  ✅ test.csv: {len(test_df)} samples")

# 4. Create ASR-specific configuration
print(f"\n⚙️  CREATING ASR CONFIGURATION:")
print("-" * 40)

asr_config = {
    "dataset_name": "twi_asr_splits",
    "base_dir": str(BASE_DIR),
    "splits_dir": str(SPLITS_DIR),
    "splits": {
        "train": len(train_df),
        "validation": len(val_df),
        "test": len(test_df)
    },
    "total_samples": len(working_df),
    "languages": list(working_df['dialect'].unique()) if 'dialect' in working_df.columns else ['twi'],
    "audio_format": "mixed (FLAC, OGG, WAV)",
    "sampling_rate": 16000,
    "data_quality": {
        "audio_files_exist": audio_availability > 50,
        "estimated_audio_paths": audio_availability < 50,
        "real_audio_samples": existing_audio,
        "total_checked": len(sample_audio_paths)
    },
    "model_recommendations": {
        "development": "openai/whisper-base" if audio_availability < 50 else "openai/whisper-large-v3",
        "production": "openai/whisper-large-v3",
        "fast_inference": "faster-whisper large-v3",
        "alternative": "facebook/mms-1b-all"
    },
    "training_recommendations": {
        "batch_size": 4 if audio_availability < 50 else 8,
        "gradient_accumulation_steps": 4 if audio_availability < 50 else 2,
        "learning_rate": "1e-5",
        "max_steps": 1000 if audio_availability < 50 else 5000,
        "evaluation_strategy": "steps",
        "eval_steps": 250 if audio_availability < 50 else 500
    },
    "compatibility": {
        "notebook": "004_phase2_asr_development.ipynb",
        "expected_paths": [
            str(train_file),
            str(val_file),
            str(test_file)
        ],
        "status": "compatible"
    }
}

config_file = SPLITS_DIR / 'asr_data_config.json'
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(asr_config, f, indent=2, ensure_ascii=False)

print(f"  ✅ Configuration saved: {config_file}")

# 5. Verify ASR notebook compatibility
print(f"\n🔬 ASR NOTEBOOK COMPATIBILITY CHECK:")
print("-" * 40)

# Check that the paths match what the notebook expects
expected_paths = [
    BASE_DIR / 'splits' / 'train.csv',
    BASE_DIR / 'splits' / 'validation.csv', 
    BASE_DIR / 'splits' / 'test.csv'
]

all_paths_exist = True
for path in expected_paths:
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {path}")
    if not exists:
        all_paths_exist = False

# Test loading the first few samples like the notebook does
print(f"\n📊 Sample data verification:")
test_sample = train_df.head(3)
for i, (_, row) in enumerate(test_sample.iterrows()):
    audio_path = row['audio']
    text = row['text']
    audio_exists = Path(audio_path).exists()
    
    print(f"  Sample {i+1}:")
    print(f"    Audio: {Path(audio_path).name} ({'exists' if audio_exists else 'MISSING'})")
    print(f"    Text: {text[:50]}..." if len(text) > 50 else f"    Text: {text}")

# 6. Final summary and recommendations
print(f"\n" + "=" * 60)
print("ASR DATA COMPATIBILITY SUMMARY")
print("=" * 60)

if all_paths_exist:
    print("✅ SUCCESS: ASR notebook data structure is compatible!")
    print("✅ All required CSV files created")
    
    if audio_availability > 50:
        print("✅ REAL AUDIO FILES AVAILABLE - Ready for training!")
        print(f"   🎯 Recommendation: Full ASR training pipeline")
    else:
        print("⚠️  AUDIO FILES MISSING - Text processing only")
        print(f"   🎯 Recommendation: Run MichSet audio extraction first")
        print(f"      Use updated 002_phase1_data_processing_enhanced.ipynb")
        print(f"      Install torchcodec and extract real audio files")
else:
    print("❌ Some required files are missing!")

print(f"\n📁 Created files:")
print(f"  📄 {train_file} ({len(train_df)} samples)")
print(f"  📄 {val_file} ({len(val_df)} samples)")
print(f"  📄 {test_file} ({len(test_df)} samples)")
print(f"  ⚙️  {config_file} (configuration)")

print(f"\n🚀 004_phase2_asr_development.ipynb is now compatible!")

if audio_availability < 50:
    print(f"\n⚠️  IMPORTANT: For real ASR training:")
    print(f"   1. Run the updated Phase 1 notebook with MichSet extraction")
    print(f"   2. Install: pip install torchcodec")
    print(f"   3. Extract real audio files from Arrow datasets")
    print(f"   4. Re-run this script to update paths")
    print(f"   5. Then run ASR training")
else:
    print(f"\n🎉 Ready for ASR training with real audio files!")
    
print(f"\n[COMPLETE] ASR notebook compatibility fixed!")
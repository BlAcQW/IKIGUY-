#!/usr/bin/env python
"""
Prepare our processed data for the ASR training notebook
Organize data in the format expected by 004_phase2_asr_development.ipynb
"""

import pandas as pd
from pathlib import Path
import json
import shutil

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"
SPLITS_DIR = BASE_DIR / "splits"
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

print("PREPARING DATA FOR ASR TRAINING")
print("=" * 60)

# 1. Prepare Financial Inclusion audio data
print("\n1. FINANCIAL INCLUSION AUDIO")
print("-" * 40)

fi_manifests = {
    'train': [],
    'validation': [],
    'test': []
}

# Load Financial Inclusion manifests
# First try audio_data directory (where we processed them)
audio_dir = PROCESSED_DIR / "audio_data"
fi_dir = PROCESSED_DIR / "financial_inclusion_twi"

if audio_dir.exists():
    for csv_file in audio_dir.glob("*.csv"):
        if 'train' in csv_file.name:
            split = 'train'
        elif 'test' in csv_file.name:
            split = 'test'
        else:
            continue
        
        try:
            df = pd.read_csv(csv_file)
            # Map columns to expected format
            if 'audio_path' in df.columns:
                df['audio'] = df['audio_path']
            if 'transcript' in df.columns:
                df['text'] = df['transcript']
            elif 'transcription' in df.columns:
                df['text'] = df['transcription']
            
            # Filter valid entries
            if 'audio' in df.columns and 'text' in df.columns:
                valid_df = df[['audio', 'text']].dropna()
                
                # Add language/dialect info
                if 'dialect' in df.columns:
                    valid_df['language'] = df['dialect']
                elif 'akuapem' in csv_file.name.lower():
                    valid_df['language'] = 'akuapem_twi'
                elif 'asante' in csv_file.name.lower():
                    valid_df['language'] = 'asante_twi'
                elif 'fante' in csv_file.name.lower():
                    valid_df['language'] = 'fante'
                else:
                    valid_df['language'] = 'twi'
                
                # Add duration placeholder
                valid_df['duration'] = -1
                
                fi_manifests[split].extend(valid_df.to_dict('records'))
                print(f"  Loaded {len(valid_df)} from {csv_file.name}")
        except Exception as e:
            print(f"  Error loading {csv_file.name}: {str(e)[:50]}")

# 2. Add Bible TTS data (if processed)
print("\n2. BIBLE TTS AUDIO")
print("-" * 40)

bible_dir = PROCESSED_DIR / "bible_tts_complete"
if bible_dir.exists():
    for csv_file in bible_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            
            # Map columns
            if 'audio_filepath' in df.columns:
                df['audio'] = df['audio_filepath']
            if 'text' in df.columns and 'has_text' in df.columns:
                # Filter only entries with text
                valid_df = df[df['has_text'] == True][['audio', 'text']]
                
                # Determine split
                if 'train' in csv_file.name:
                    split = 'train'
                elif 'test' in csv_file.name:
                    split = 'test'
                elif 'dev' in csv_file.name:
                    split = 'validation'
                else:
                    split = 'train'  # Default
                
                # Add metadata
                if 'dialect' in df.columns:
                    valid_df['language'] = df['dialect']
                else:
                    valid_df['language'] = 'twi'
                
                valid_df['duration'] = -1
                
                fi_manifests[split].extend(valid_df.to_dict('records'))
                print(f"  Loaded {len(valid_df)} from {csv_file.name}")
        except Exception as e:
            print(f"  Error loading {csv_file.name}: {str(e)[:50]}")
else:
    print("  Bible TTS not fully processed yet")

# 3. Add MichSet audio data
print("\n3. MICHSET AUDIO")
print("-" * 40)

michset_dir = PROCESSED_DIR / "michset_audio_manifests"
if michset_dir.exists():
    # Load metadata to understand structure
    for json_file in michset_dir.glob("*_metadata.json"):
        try:
            with open(json_file, 'r') as f:
                metadata = json.load(f)
            
            dataset_name = json_file.stem.replace('_metadata', '')
            print(f"  {dataset_name}: {metadata.get('actual_samples', 'unknown')} samples")
            
            # Note: Audio paths need to be resolved
            # The actual audio files are in Arrow format and need extraction
            
        except Exception as e:
            print(f"  Error loading {json_file.name}: {str(e)[:50]}")
else:
    print("  MichSet manifests not found")

# 4. Create train/validation/test splits
print("\n4. CREATING SPLITS")
print("-" * 40)

# Convert to DataFrames
train_df = pd.DataFrame(fi_manifests['train']) if fi_manifests['train'] else pd.DataFrame()
test_df = pd.DataFrame(fi_manifests['test']) if fi_manifests['test'] else pd.DataFrame()
val_df = pd.DataFrame(fi_manifests['validation']) if fi_manifests['validation'] else pd.DataFrame()

# If no validation set, split from train
if len(val_df) == 0 and len(train_df) > 100:
    print("  Creating validation set from training data...")
    val_size = min(1000, int(len(train_df) * 0.1))
    val_df = train_df.sample(n=val_size, random_state=42)
    train_df = train_df.drop(val_df.index)

# Save splits
if len(train_df) > 0:
    train_path = SPLITS_DIR / "train.csv"
    train_df.to_csv(train_path, index=False)
    print(f"  [SAVED] train.csv ({len(train_df)} samples)")

if len(val_df) > 0:
    val_path = SPLITS_DIR / "validation.csv"
    val_df.to_csv(val_path, index=False)
    print(f"  [SAVED] validation.csv ({len(val_df)} samples)")

if len(test_df) > 0:
    test_path = SPLITS_DIR / "test.csv"
    test_df.to_csv(test_path, index=False)
    print(f"  [SAVED] test.csv ({len(test_df)} samples)")

# 5. Create configuration file
print("\n5. CREATING CONFIGURATION")
print("-" * 40)

config = {
    "dataset_name": "twi_asr_combined",
    "languages": list(set(train_df['language'].unique()) if 'language' in train_df.columns else ['twi']),
    "splits": {
        "train": len(train_df),
        "validation": len(val_df),
        "test": len(test_df)
    },
    "total_samples": len(train_df) + len(val_df) + len(test_df),
    "audio_format": "mixed (FLAC, OGG, WAV)",
    "sampling_rate": 16000,
    "model_recommendations": {
        "whisper": "openai/whisper-large-v3",
        "faster_whisper": "large-v3",
        "mms": "facebook/mms-1b-all",
        "wav2vec2": "facebook/wav2vec2-large-xlsr-53"
    },
    "training_params": {
        "batch_size": 8,
        "gradient_accumulation_steps": 2,
        "learning_rate": 1e-5,
        "warmup_steps": 500,
        "num_epochs": 10,
        "fp16": True
    }
}

config_path = SPLITS_DIR / "asr_config.json"
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print(f"  [SAVED] asr_config.json")

# 6. Create sample audio for testing
print("\n6. CREATING TEST SAMPLES")
print("-" * 40)

samples_dir = SPLITS_DIR / "samples"
samples_dir.mkdir(exist_ok=True)

# Copy a few sample audio files for quick testing
sample_count = 0
max_samples = 5

if len(train_df) > 0 and 'audio' in train_df.columns:
    for _, row in train_df.head(max_samples).iterrows():
        audio_path = Path(row['audio'])
        if audio_path.exists():
            # Copy audio file
            dest_audio = samples_dir / f"sample_{sample_count}{audio_path.suffix}"
            shutil.copy2(audio_path, dest_audio)
            
            # Save text
            text_file = samples_dir / f"sample_{sample_count}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(row.get('text', ''))
            
            sample_count += 1
            print(f"  Created sample_{sample_count}")

print(f"  Total samples created: {sample_count}")

# Summary
print("\n" + "=" * 60)
print("DATA PREPARATION COMPLETE!")
print("=" * 60)

print(f"\nData location: {SPLITS_DIR}")
print(f"\nDataset Statistics:")
print(f"  Total samples: {config['total_samples']:,}")
print(f"  Languages: {', '.join(config['languages'])}")
print(f"  Train: {config['splits']['train']:,}")
print(f"  Validation: {config['splits']['validation']:,}") 
print(f"  Test: {config['splits']['test']:,}")

print("\n[OK] Ready for ASR training!")
print("\nNext steps:")
print("  1. Open 004_phase2_asr_development.ipynb")
print("  2. Mount Google Drive (if in Colab)")
print("  3. Run the training pipeline")
print("  4. Monitor with TensorBoard")

print("\n📝 To start training:")
print("  run_training_pipeline()")

# Create a quick start script
quickstart = """
# Quick Start for ASR Training

import sys
sys.path.append('/content/drive/MyDrive/voice-lab-data')

from pathlib import Path
BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')

# The data is ready in:
# BASE_DIR / 'splits' / 'train.csv'
# BASE_DIR / 'splits' / 'validation.csv'
# BASE_DIR / 'splits' / 'test.csv'

print("Data ready for training!")
"""

quickstart_path = SPLITS_DIR / "quickstart.py"
with open(quickstart_path, 'w') as f:
    f.write(quickstart)

print(f"\n[SAVED] quickstart.py for easy setup")
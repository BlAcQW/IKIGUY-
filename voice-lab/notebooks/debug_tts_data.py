#!/usr/bin/env python
"""
Debug script to understand what's happening with TTS data preparation
"""

import pandas as pd
from pathlib import Path
import json

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"

print("DEBUGGING TTS DATA PREPARATION")
print("=" * 50)

all_data = []

# Check MichSet loading
print("\n1. CHECKING MICHSET LOADING")
print("-" * 30)

try:
    import datasets
    print("  HuggingFace datasets available: YES")
    
    michset_base = BASE_DIR / "raw" / "michsethowusu"
    datasets_info = [
        ("twi_multispeaker_audio_transcribed", "twi", 5),
        ("akuapem_multispeaker_audio_transcribed", "akuapem_twi", 3),
        ("fante_multispeaker_audio_transcribed", "fante", 3)
    ]
    
    for dataset_name, dialect, sample_limit in datasets_info:
        dataset_path = michset_base / dataset_name
        print(f"\n  Checking {dataset_name}...")
        print(f"    Path: {dataset_path}")
        print(f"    Exists: {dataset_path.exists()}")
        
        if dataset_path.exists():
            try:
                dataset = datasets.load_from_disk(str(dataset_path))
                print(f"    Dataset loaded successfully")
                print(f"    Keys: {list(dataset.keys())}")
                
                if 'train' in dataset:
                    train_data = dataset['train']
                    print(f"    Train samples: {len(train_data)}")
                    print(f"    Features: {train_data.features}")
                    
                    # Try to access first few samples
                    for i in range(min(sample_limit, len(train_data))):
                        try:
                            sample = train_data[i]
                            print(f"    Sample {i}:")
                            print(f"      Keys: {list(sample.keys())}")
                            
                            if 'audio_path' in sample:
                                print(f"      Audio path: {sample['audio_path']}")
                                audio_path = sample['audio_path']
                                if not str(audio_path).startswith('/'):
                                    full_path = dataset_path / audio_path
                                else:
                                    full_path = Path(audio_path)
                                print(f"      Full path: {full_path}")
                                print(f"      Audio exists: {full_path.exists() if full_path else 'N/A'}")
                            
                            if 'transcription' in sample:
                                transcription = sample['transcription']
                                print(f"      Transcription: {transcription[:50]}..." if len(str(transcription)) > 50 else f"      Transcription: {transcription}")
                            
                            # Add to all_data like in the main script
                            if 'audio_path' in sample and 'transcription' in sample:
                                entry = {
                                    'audio': str(full_path),
                                    'text': sample['transcription'],
                                    'original_text': sample['transcription'],
                                    'dialect': dialect,
                                    'speaker_id': f"{dialect}_speaker_{i // 100}",
                                    'duration': 3.0,
                                    'source': 'michset'
                                }
                                all_data.append(entry)
                                print(f"      Added to all_data: YES")
                            else:
                                print(f"      Added to all_data: NO (missing keys)")
                            
                            print()
                        except Exception as e:
                            print(f"      Error accessing sample {i}: {e}")
                            break
                
            except Exception as e:
                print(f"    Error loading dataset: {e}")

except ImportError:
    print("  HuggingFace datasets not available: NO")

# Check text data
print("\n2. CHECKING TEXT DATA")
print("-" * 30)

text_dir = PROCESSED_DIR / "text_data"
print(f"  Text dir: {text_dir}")
print(f"  Text dir exists: {text_dir.exists()}")

if text_dir.exists():
    sample_file = text_dir / "train_sample.csv"
    print(f"  Sample file: {sample_file}")
    print(f"  Sample file exists: {sample_file.exists()}")
    
    if sample_file.exists():
        try:
            sample_df = pd.read_csv(sample_file)
            print(f"  Sample file loaded: {len(sample_df)} rows")
            print(f"  Columns: {list(sample_df.columns)}")
            print(f"  First few rows:")
            print(sample_df.head(3))
            
            # Add synthetic samples
            synthetic_samples = sample_df.head(3)
            for _, row in synthetic_samples.iterrows():
                if 'twi' in row and 'english' in row:
                    entry = {
                        'audio': 'SYNTHETIC',
                        'text': row['twi'],
                        'original_text': row['twi'],
                        'dialect': 'twi',
                        'speaker_id': 'synthetic_speaker',
                        'duration': len(str(row['twi'])) * 0.1,
                        'source': 'synthetic',
                        'english_translation': row['english']
                    }
                    all_data.append(entry)
                    print(f"  Added synthetic entry: {row['twi'][:30]}...")
                    
        except Exception as e:
            print(f"  Error loading sample file: {e}")

print(f"\n3. FINAL RESULTS")
print("-" * 30)
print(f"  Total entries in all_data: {len(all_data)}")

if all_data:
    print(f"  Sample entries:")
    for i, entry in enumerate(all_data[:3]):
        print(f"    Entry {i}:")
        for key, value in entry.items():
            if key == 'text':
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            else:
                display_value = str(value)
            print(f"      {key}: {display_value}")
        print()
    
    # Convert to DataFrame
    combined_df = pd.DataFrame(all_data)
    print(f"  DataFrame created: {len(combined_df)} rows")
    print(f"  DataFrame columns: {list(combined_df.columns)}")
    
    # Check for duplicates
    print(f"  Duplicates by text: {combined_df.duplicated(subset=['text']).sum()}")
    
    # Check for real vs synthetic
    real_audio = combined_df[combined_df['audio'] != 'SYNTHETIC']
    synthetic = combined_df[combined_df['audio'] == 'SYNTHETIC']
    print(f"  Real audio entries: {len(real_audio)}")
    print(f"  Synthetic entries: {len(synthetic)}")
    
else:
    print("  No data found")

print(f"\n[DONE] Debug complete")
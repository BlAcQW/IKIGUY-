#!/usr/bin/env python
"""
Practical TTS data preparation script
Works with currently available processed data to create training files
"""

import pandas as pd
from pathlib import Path
import json
import sys

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"
METADATA_DIR.mkdir(parents=True, exist_ok=True)

print("PRACTICAL TTS DATA PREPARATION")
print("=" * 60)

# Collect all available audio-text pairs
all_data = []
data_sources = []

# 1. Use MichSet via HuggingFace datasets (if available)
print("\n1. MICHSET DATA (Via HuggingFace)")
print("-" * 40)

try:
    # Try to load from HuggingFace datasets
    import datasets
    
    michset_base = BASE_DIR / "raw" / "michsethowusu"
    datasets_info = [
        ("twi_multispeaker_audio_transcribed", "twi", 1000),
        ("akuapem_multispeaker_audio_transcribed", "akuapem_twi", 500),
        ("fante_multispeaker_audio_transcribed", "fante", 500)
    ]
    
    for dataset_name, dialect, sample_limit in datasets_info:
        dataset_path = michset_base / dataset_name
        if dataset_path.exists():
            try:
                print(f"  Loading {dataset_name}...")
                dataset = datasets.load_from_disk(str(dataset_path))
                
                if 'train' in dataset:
                    train_data = dataset['train']
                    print(f"    Found {len(train_data)} training samples")
                    
                    # Take a subset for TTS (we don't need all samples)
                    samples_to_use = min(sample_limit, len(train_data))
                    
                    for i in range(samples_to_use):
                        try:
                            sample = train_data[i]
                            if 'audio_path' in sample and 'transcription' in sample:
                                # Use relative path from the dataset
                                audio_path = sample['audio_path']
                                if not str(audio_path).startswith('/'):
                                    full_path = dataset_path / audio_path
                                else:
                                    full_path = Path(audio_path)
                                
                                entry = {
                                    'audio': str(full_path),
                                    'text': sample['transcription'],
                                    'original_text': sample['transcription'],
                                    'dialect': dialect,
                                    'speaker_id': f"{dialect}_speaker_{i // 100}",  # Group by speaker
                                    'duration': 3.0,  # Default estimate
                                    'source': 'michset'
                                }
                                all_data.append(entry)
                        except Exception as e:
                            continue  # Skip problematic samples
                    
                    print(f"    Added {samples_to_use} entries from {dataset_name}")
                    data_sources.append(f"{dataset_name}: {samples_to_use} samples")
                    
            except Exception as e:
                print(f"    Error loading {dataset_name}: {str(e)[:50]}")
        else:
            print(f"    {dataset_name} not found")

except ImportError:
    print("  HuggingFace datasets not available")
    print("  Install with: pip install datasets")

# 2. Text-only data for synthetic TTS
print("\n2. TEXT DATA FOR SYNTHETIC TTS")
print("-" * 40)

text_dir = PROCESSED_DIR / "text_data"
if text_dir.exists():
    # Load sample pairs for synthetic TTS generation
    sample_file = text_dir / "train_sample.csv"
    if sample_file.exists():
        try:
            sample_df = pd.read_csv(sample_file)
            print(f"  Found {len(sample_df)} text pairs")
            
            # Use first 500 for synthetic TTS
            synthetic_samples = sample_df.head(500)
            
            for _, row in synthetic_samples.iterrows():
                if 'twi' in row and 'english' in row:
                    entry = {
                        'audio': 'SYNTHETIC',  # Will be generated
                        'text': row['twi'],
                        'original_text': row['twi'],
                        'dialect': 'twi',
                        'speaker_id': 'synthetic_speaker',
                        'duration': len(row['twi']) * 0.1,  # Rough estimate
                        'source': 'synthetic',
                        'english_translation': row['english']
                    }
                    all_data.append(entry)
            
            print(f"  Added {len(synthetic_samples)} synthetic entries")
            data_sources.append(f"Synthetic TTS: {len(synthetic_samples)} samples")
            
        except Exception as e:
            print(f"  Error loading text samples: {str(e)}")

# 3. Create training dataset
print("\n3. CREATING TRAINING DATASET")
print("-" * 40)

if all_data:
    # Convert to DataFrame
    combined_df = pd.DataFrame(all_data)
    
    # Remove duplicates by text (keep audio when available)
    combined_df = combined_df.drop_duplicates(subset=['text'])
    
    # Separate real audio from synthetic
    real_audio_df = combined_df[combined_df['audio'] != 'SYNTHETIC'].copy()
    synthetic_df = combined_df[combined_df['audio'] == 'SYNTHETIC'].copy()
    
    print(f"  Real audio samples: {len(real_audio_df)}")
    print(f"  Synthetic samples: {len(synthetic_df)}")
    print(f"  Total samples: {len(combined_df)}")
    
    # Save main dataset
    output_file = METADATA_DIR / "processed_data_enhanced.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"  [SAVED] {output_file.name}")
    
    # Save real audio only (for immediate training)
    if len(real_audio_df) > 0:
        real_audio_file = METADATA_DIR / "real_audio_tts.csv"
        real_audio_df.to_csv(real_audio_file, index=False)
        print(f"  [SAVED] real_audio_tts.csv ({len(real_audio_df)} real audio samples)")
        
        # Create Coqui TTS format for real audio
        tts_metadata = []
        for _, row in real_audio_df.iterrows():
            tts_metadata.append(f"{row['audio']}|{row['text']}|{row['speaker_id']}")
        
        metadata_txt = METADATA_DIR / "metadata.txt"
        with open(metadata_txt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(tts_metadata))
        print(f"  [SAVED] metadata.txt (Coqui TTS format)")
    
    # Save synthetic text (for TTS generation)
    if len(synthetic_df) > 0:
        synthetic_file = METADATA_DIR / "synthetic_tts_texts.csv"
        synthetic_df.to_csv(synthetic_file, index=False)
        print(f"  [SAVED] synthetic_tts_texts.csv ({len(synthetic_df)} texts for synthesis)")
    
    # Create dialect-specific files
    for dialect in combined_df['dialect'].unique():
        dialect_df = combined_df[combined_df['dialect'] == dialect]
        dialect_file = METADATA_DIR / f"tts_data_{dialect}.csv"
        dialect_df.to_csv(dialect_file, index=False)
        print(f"  [SAVED] {dialect_file.name} ({len(dialect_df)} entries)")
    
    # Statistics
    print("\n  Dataset Statistics:")
    print(f"    Total samples: {len(combined_df):,}")
    print(f"    Real audio: {len(real_audio_df):,}")
    print(f"    Synthetic text: {len(synthetic_df):,}")
    print(f"    Dialects: {', '.join(combined_df['dialect'].unique())}")
    print(f"    Speakers: {len(combined_df['speaker_id'].unique())}")
    
    if len(real_audio_df) > 0:
        print(f"    Total duration: {real_audio_df['duration'].sum():.1f} seconds")
    
    # Data sources summary
    print("\n  Data Sources:")
    for source in data_sources:
        print(f"    - {source}")

else:
    print("  No data found - creating minimal dummy dataset")
    
    # Create basic dummy data
    dummy_data = pd.DataFrame({
        'audio': ['SYNTHETIC'],
        'text': ['Mema mo akwaaba'],
        'original_text': ['Mema mo akwaaba'],
        'dialect': ['twi'],
        'speaker_id': ['demo_speaker'],
        'duration': [2.0],
        'source': ['dummy']
    })
    
    output_file = METADATA_DIR / "processed_data_enhanced.csv"
    dummy_data.to_csv(output_file, index=False)
    print(f"  [SAVED] Dummy data to {output_file.name}")

# 4. Create TTS configuration
print("\n4. CREATING TTS CONFIGURATION")
print("-" * 40)

has_real_audio = 'real_audio_df' in locals() and len(real_audio_df) > 0
has_synthetic = 'synthetic_df' in locals() and len(synthetic_df) > 0

tts_config = {
    "dataset": "twi_tts_practical",
    "version": "1.0",
    "total_samples": len(combined_df) if 'combined_df' in locals() else 0,
    "real_audio_samples": len(real_audio_df) if has_real_audio else 0,
    "synthetic_samples": len(synthetic_df) if has_synthetic else 0,
    "languages": list(combined_df['dialect'].unique()) if 'combined_df' in locals() and len(combined_df) > 0 else ["twi"],
    "training_approach": {
        "stage1": "Train on real audio samples" if has_real_audio else "No real audio available",
        "stage2": "Fine-tune with synthetic audio" if has_synthetic else "No synthetic data",
        "recommended": "Real audio first, then synthetic augmentation"
    },
    "model_recommendations": {
        "small_dataset": "Coqui TTS - Tacotron2 (works with <1000 samples)",
        "voice_cloning": "XTTS v2 (needs ~10 minutes per speaker)",
        "edge_deployment": "Kokoro-82M (smallest, fastest)",
        "experimental": "F5-TTS (high quality, newer architecture)"
    },
    "training_params": {
        "batch_size": 8 if has_real_audio and len(real_audio_df) < 1000 else 16,
        "learning_rate": 0.001,
        "epochs": 500 if has_real_audio and len(real_audio_df) < 500 else 1000,
        "save_step": 100,
        "eval_step": 50,
        "grad_clip": 5.0
    },
    "paths": {
        "main_dataset": str(METADATA_DIR / "processed_data_enhanced.csv"),
        "real_audio": str(METADATA_DIR / "real_audio_tts.csv") if has_real_audio else None,
        "synthetic_texts": str(METADATA_DIR / "synthetic_tts_texts.csv") if has_synthetic else None,
        "metadata_txt": str(METADATA_DIR / "metadata.txt") if has_real_audio else None,
        "output_dir": str(BASE_DIR / "models" / "tts")
    },
    "next_steps": [
        "Install TTS framework: pip install TTS",
        "Open 005_phase3_tts_development.ipynb",
        "Mount Google Drive in Colab",
        "Start with real audio training" if has_real_audio else "Generate synthetic audio first",
        "Test with: tts --text 'Mema mo akwaaba' --model_name tts_models/your_model"
    ]
}

config_file = METADATA_DIR / "tts_config_practical.json"
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(tts_config, f, indent=2, ensure_ascii=False)
print(f"  [SAVED] tts_config_practical.json")

# Summary
print("\n" + "=" * 60)
print("PRACTICAL TTS DATA PREPARATION COMPLETE!")
print("=" * 60)

print(f"\nOutput location: {METADATA_DIR}")

if 'combined_df' in locals() and len(combined_df) > 0:
    print(f"\nDataset ready for TTS training:")
    print(f"  Main file: processed_data_enhanced.csv ({len(combined_df)} samples)")
    if has_real_audio:
        print(f"  Real audio: real_audio_tts.csv ({len(real_audio_df)} samples)")
        print(f"  Coqui format: metadata.txt")
    if has_synthetic:
        print(f"  Synthetic texts: synthetic_tts_texts.csv ({len(synthetic_df)} samples)")
    print(f"  Configuration: tts_config_practical.json")
else:
    print(f"\nDummy dataset created for testing")

print(f"\n[STATUS] TTS training data is ready!")

# Recommendations based on available data
if has_real_audio and len(real_audio_df) > 100:
    print(f"\n[RECOMMENDATION] You have {len(real_audio_df)} real audio samples.")
    print("  This is good for training a basic TTS model!")
    print("  Start with Coqui TTS using metadata.txt")
elif has_synthetic and len(synthetic_df) > 500:
    print(f"\n[RECOMMENDATION] You have {len(synthetic_df)} text samples.")
    print("  Consider generating synthetic audio first using:")
    print("  1. Edge-TTS for bootstrap audio")
    print("  2. Then train your own model")
else:
    print(f"\n[RECOMMENDATION] Limited training data available.")
    print("  Wait for Bible TTS processing to complete, or")
    print("  Use pre-trained models with fine-tuning")

print(f"\nReady for 005_phase3_tts_development.ipynb!")
#!/usr/bin/env python
"""
Prepare our processed data for TTS training
Organize data for 005_phase3_tts_development.ipynb
"""

import pandas as pd
from pathlib import Path
import json
import shutil

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"
METADATA_DIR.mkdir(parents=True, exist_ok=True)

print("PREPARING DATA FOR TTS TRAINING")
print("=" * 60)

# Collect all available audio-text pairs
all_data = []

# 1. Bible TTS Data (if processed)
print("\n1. BIBLE TTS DATA")
print("-" * 40)

bible_dir = PROCESSED_DIR / "bible_tts_complete"
if bible_dir.exists():
    for csv_file in bible_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            
            # Filter entries with text
            if 'text' in df.columns and 'has_text' in df.columns:
                valid_df = df[df['has_text'] == True].copy()
                
                # Map columns for TTS
                if 'audio_filepath' in df.columns:
                    valid_df['audio'] = df['audio_filepath']
                elif 'audio_path' in df.columns:
                    valid_df['audio'] = df['audio_path']
                
                # Ensure we have required columns
                if 'audio' in valid_df.columns and 'text' in valid_df.columns:
                    valid_df['original_text'] = valid_df['text']
                    valid_df['dialect'] = df.get('dialect', 'twi')
                    valid_df['speaker_id'] = f"{valid_df['dialect'].iloc[0]}_speaker" if len(valid_df) > 0 else "twi_speaker"
                    valid_df['duration'] = df.get('file_size_mb', 0) * 10  # Rough estimate
                    
                    all_data.append(valid_df[['audio', 'text', 'original_text', 'dialect', 'speaker_id', 'duration']])
                    print(f"  Loaded {len(valid_df)} entries from {csv_file.name}")
        except Exception as e:
            print(f"  Error loading {csv_file.name}: {str(e)[:50]}")
else:
    print("  Bible TTS not fully processed yet")

# 2. Financial Inclusion Data
print("\n2. FINANCIAL INCLUSION DATA")
print("-" * 40)

# Check the processed audio_data directory
audio_dir = PROCESSED_DIR / "audio_data"
if audio_dir.exists():
    # Load audio manifest
    audio_manifest = pd.read_csv(audio_dir / "audio_manifest.csv") if (audio_dir / "audio_manifest.csv").exists() else pd.DataFrame()
    
    if len(audio_manifest) > 0:
        print(f"  Found {len(audio_manifest)} audio files")
        
        # Try to load transcriptions from original metadata
        fi_base = BASE_DIR / "raw" / "financial_inclusion"
        
        # Map different datasets
        fi_datasets = {
            'fante_90': fi_base / 'fante_90' / 'fisd-fanti-90p' / 'data.csv',
            'fante_10': fi_base / 'fante_10' / 'fisd-fanti-10p' / 'data.csv',
            'akuapem_twi_90': fi_base / 'akuapem_twi_90' / 'fisd-akuapim-twi-90p' / 'data.csv',
            'akuapem_twi_10': fi_base / 'akuapem_twi_10' / 'fisd-akuapim-twi-10p' / 'data.csv',
            'asante_twi_90': fi_base / 'asante_twi_90' / 'fisd-asanti-twi-90p' / 'data.csv',
            'asante_twi_10': fi_base / 'asante_twi_10' / 'fisd-asanti-twi-10p' / 'data.csv'
        }
        
        for dataset_name, metadata_path in fi_datasets.items():
            if metadata_path.exists():
                try:
                    # Load metadata with transcriptions
                    metadata_df = pd.read_csv(metadata_path)
                    
                    if 'Transcription' in metadata_df.columns:
                        # Extract filename from Audio Filepath
                        metadata_df['filename'] = metadata_df['Audio Filepath'].apply(lambda x: Path(x).name if pd.notna(x) else '')
                        
                        # Match with audio manifest
                        dataset_audio = audio_manifest[audio_manifest['dataset'] == dataset_name.replace('_', '')].copy()
                        
                        if len(dataset_audio) > 0:
                            # Merge on filename
                            dataset_audio['filename'] = dataset_audio['audio_filename']
                            merged = dataset_audio.merge(metadata_df[['filename', 'Transcription', 'Translation']], 
                                                        on='filename', how='left')
                            
                            # Filter valid entries
                            valid = merged[merged['Transcription'].notna()].copy()
                            
                            if len(valid) > 0:
                                valid['audio'] = valid['audio_path']
                                valid['text'] = valid['Transcription']
                                valid['original_text'] = valid['Transcription']
                                valid['dialect'] = valid['language']
                                valid['speaker_id'] = f"{valid['language'].iloc[0]}_speaker"
                                valid['duration'] = valid['file_size_mb'] * 10  # Rough estimate
                                
                                all_data.append(valid[['audio', 'text', 'original_text', 'dialect', 'speaker_id', 'duration']])
                                print(f"    Matched {len(valid)} entries from {dataset_name}")
                    
                except Exception as e:
                    print(f"    Error processing {dataset_name}: {str(e)[:50]}")

# 3. Text-only data (for reference)
print("\n3. TEXT DATA (Reference)")
print("-" * 40)

text_dir = PROCESSED_DIR / "text_data"
if text_dir.exists():
    # Load vocabulary for reference
    vocab_file = text_dir / "twi_vocab.txt"
    if vocab_file.exists():
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab_lines = f.readlines()
        print(f"  Vocabulary loaded: {len(vocab_lines)} words")
    
    # Load sample pairs for synthetic TTS
    sample_file = text_dir / "train_sample.csv"
    if sample_file.exists():
        sample_df = pd.read_csv(sample_file)
        print(f"  Sample text pairs: {len(sample_df)} entries")

# 4. Combine and save
print("\n4. COMBINING DATA")
print("-" * 40)

if all_data:
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['audio'])
    
    # Filter valid entries
    combined_df = combined_df[combined_df['text'].notna()]
    combined_df = combined_df[combined_df['audio'].notna()]
    
    # Check if audio files exist
    combined_df['audio_exists'] = combined_df['audio'].apply(lambda x: Path(x).exists() if pd.notna(x) else False)
    valid_df = combined_df[combined_df['audio_exists']].drop('audio_exists', axis=1)
    
    print(f"  Total valid entries: {len(valid_df)}")
    
    # Save as processed_data_enhanced.csv
    output_file = METADATA_DIR / "processed_data_enhanced.csv"
    valid_df.to_csv(output_file, index=False)
    print(f"  [SAVED] {output_file.name}")
    
    # Create dialect-specific files
    for dialect in valid_df['dialect'].unique():
        dialect_df = valid_df[valid_df['dialect'] == dialect]
        dialect_file = METADATA_DIR / f"processed_data_{dialect}.csv"
        dialect_df.to_csv(dialect_file, index=False)
        print(f"  [SAVED] {dialect_file.name} ({len(dialect_df)} entries)")
    
    # Create TTS metadata format (audio_path|text|speaker)
    tts_metadata = []
    for _, row in valid_df.iterrows():
        tts_metadata.append(f"{row['audio']}|{row['text']}|{row['speaker_id']}")
    
    metadata_txt = METADATA_DIR / "metadata.txt"
    with open(metadata_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tts_metadata))
    print(f"  [SAVED] metadata.txt (Coqui TTS format)")
    
    # Statistics
    print("\n  Statistics:")
    print(f"    Total samples: {len(valid_df)}")
    print(f"    Dialects: {', '.join(valid_df['dialect'].unique())}")
    print(f"    Speakers: {len(valid_df['speaker_id'].unique())}")
    print(f"    Total duration: {valid_df['duration'].sum():.1f} seconds (estimated)")
    
else:
    print("  No valid TTS data found")
    
    # Create dummy file for notebook
    dummy_data = pd.DataFrame({
        'audio': ['dummy_audio.wav'],
        'text': ['Mema mo akwaaba'],
        'original_text': ['Mema mo akwaaba'],
        'dialect': ['asante'],
        'speaker_id': ['asante_speaker'],
        'duration': [2.0]
    })
    
    output_file = METADATA_DIR / "processed_data_enhanced.csv"
    dummy_data.to_csv(output_file, index=False)
    print(f"  [SAVED] Dummy data to {output_file.name}")

# 5. Create TTS configuration
print("\n5. CREATING TTS CONFIG")
print("-" * 40)

tts_config = {
    "dataset": "twi_tts_combined",
    "languages": ["twi", "asante_twi", "akuapem_twi", "fante"],
    "total_samples": len(valid_df) if 'valid_df' in locals() else 0,
    "features": {
        "enhanced_text_processing": True,
        "phoneme_generation": True,
        "number_expansion": True,
        "currency_processing": True,
        "date_time_processing": True,
        "multi_dialect": True
    },
    "model_recommendations": {
        "primary": "Coqui TTS - Tacotron2",
        "voice_cloning": "XTTS v2",
        "edge": "Kokoro-82M",
        "alternative": "F5-TTS"
    },
    "training_params": {
        "batch_size": 16,
        "learning_rate": 0.001,
        "epochs": 1000,
        "save_step": 500,
        "eval_step": 100
    },
    "paths": {
        "metadata": str(METADATA_DIR / "processed_data_enhanced.csv"),
        "metadata_txt": str(METADATA_DIR / "metadata.txt"),
        "output_dir": str(BASE_DIR / "models" / "tts")
    }
}

config_file = METADATA_DIR / "tts_config.json"
with open(config_file, 'w') as f:
    json.dump(tts_config, f, indent=2)
print(f"  [SAVED] tts_config.json")

# Summary
print("\n" + "=" * 60)
print("TTS DATA PREPARATION COMPLETE!")
print("=" * 60)

print(f"\nData location: {METADATA_DIR}")
print(f"Main file: processed_data_enhanced.csv")

if 'valid_df' in locals() and len(valid_df) > 0:
    print(f"\nDataset Statistics:")
    print(f"  Total samples: {len(valid_df)}")
    print(f"  Dialects: {', '.join(valid_df['dialect'].unique())}")
    print(f"  Ready for training: YES")
else:
    print("\nNo audio-text pairs found. Using dummy data.")

print("\n[OK] Ready for TTS training!")
print("\nNext steps:")
print("  1. Open 005_phase3_tts_development.ipynb")
print("  2. Mount Google Drive (if in Colab)")
print("  3. Run the TTS training pipeline")
print("  4. Test voice synthesis with Twi text")

print("\nTo test synthesis:")
print('  synthesizer.synthesize("Mema mo akwaaba!")')
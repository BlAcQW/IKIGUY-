#!/usr/bin/env python
"""
Enhanced TTS data preparation using MichSet metadata
Create audio-text pairs for TTS training from available processed data
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

print("ENHANCED TTS DATA PREPARATION")
print("=" * 60)

# Collect all available audio-text pairs
all_data = []

# 1. MichSet Data (using metadata files)
print("\n1. MICHSET DATASETS")
print("-" * 40)

michset_dir = PROCESSED_DIR / "michset_audio_manifests"
if michset_dir.exists():
    for json_file in michset_dir.glob("*_metadata.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            dataset_name = json_file.stem.replace('_metadata', '')
            print(f"  Loading {dataset_name}...")
            
            # Extract language/dialect from dataset name
            if 'twi' in dataset_name.lower():
                dialect = 'asante_twi' if 'asante' in dataset_name.lower() else 'twi'
            elif 'akuapem' in dataset_name.lower():
                dialect = 'akuapem_twi'
            elif 'fante' in dataset_name.lower():
                dialect = 'fante'
            else:
                dialect = 'twi'
            
            # Create entries from samples
            samples = metadata.get('samples', [])[:5000]  # Limit to first 5000 for TTS
            
            for sample in samples:
                if 'audio_path' in sample and 'transcription' in sample:
                    # Convert relative audio path to full path
                    audio_path = sample['audio_path']
                    if not audio_path.startswith('/'):
                        # Assume it's relative to the raw michset directory
                        base_dataset_path = BASE_DIR / "raw" / "michsethowusu" / f"{dataset_name}_audio_transcribed"
                        full_audio_path = base_dataset_path / audio_path
                    else:
                        full_audio_path = Path(audio_path)
                    
                    entry = {
                        'audio': str(full_audio_path),
                        'text': sample['transcription'],
                        'original_text': sample['transcription'],
                        'dialect': dialect,
                        'speaker_id': f"{dialect}_speaker_{sample.get('speaker_id', '1')}",
                        'duration': sample.get('duration', 3.0)  # Default estimate
                    }
                    all_data.append(entry)
            
            print(f"    Added {len(samples)} entries from {dataset_name}")
            
        except Exception as e:
            print(f"    Error loading {json_file.name}: {str(e)}")
else:
    print("  MichSet metadata not found")

# 2. Bible TTS Data (if processed)
print("\n2. BIBLE TTS DATA")
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
                    valid_df['speaker_id'] = f"{valid_df['dialect'].iloc[0]}_bible_speaker"
                    valid_df['duration'] = df.get('file_size_mb', 0) * 10  # Rough estimate
                    
                    entries = valid_df[['audio', 'text', 'original_text', 'dialect', 'speaker_id', 'duration']].to_dict('records')
                    all_data.extend(entries)
                    print(f"  Loaded {len(valid_df)} entries from {csv_file.name}")
        except Exception as e:
            print(f"  Error loading {csv_file.name}: {str(e)[:50]}")
else:
    print("  Bible TTS not processed yet")

# 3. Financial Inclusion Data (with proper transcription matching)
print("\n3. FINANCIAL INCLUSION DATA")
print("-" * 40)

audio_dir = PROCESSED_DIR / "audio_data"
if audio_dir.exists():
    # Load audio manifest
    audio_manifest_path = audio_dir / "audio_manifest.csv"
    if audio_manifest_path.exists():
        try:
            audio_manifest = pd.read_csv(audio_manifest_path)
            print(f"  Found {len(audio_manifest)} audio files")
            
            # Try to match with original transcriptions
            fi_base = BASE_DIR / "raw" / "financial_inclusion"
            
            # Process each dataset that has transcriptions
            datasets_with_transcriptions = {
                'akuapemtwi90': fi_base / 'akuapem_twi_90' / 'fisd-akuapim-twi-90p',
                'akuapemtwi10': fi_base / 'akuapem_twi_10' / 'fisd-akuapim-twi-10p',
                'asantetwi90': fi_base / 'asante_twi_90' / 'fisd-asanti-twi-90p',
                'asantetwi10': fi_base / 'asante_twi_10' / 'fisd-asanti-twi-10p',
                'fante90': fi_base / 'fante_90' / 'fisd-fanti-90p',
                'fante10': fi_base / 'fante_10' / 'fisd-fanti-10p'
            }
            
            for dataset_key, dataset_path in datasets_with_transcriptions.items():
                data_csv = dataset_path / 'data.csv'
                if data_csv.exists():
                    try:
                        # Read with different encodings and separators
                        for encoding in ['utf-8', 'latin1', 'cp1252']:
                            for sep in [',', '|', '\t']:
                                try:
                                    metadata_df = pd.read_csv(data_csv, encoding=encoding, sep=sep)
                                    if len(metadata_df.columns) > 1:  # Found valid structure
                                        break
                                except:
                                    continue
                            else:
                                continue
                            break
                        
                        if 'Transcription' in metadata_df.columns and 'Audio Filepath' in metadata_df.columns:
                            # Extract filename from Audio Filepath
                            metadata_df['filename'] = metadata_df['Audio Filepath'].apply(
                                lambda x: Path(x).name if pd.notna(x) else ''
                            )
                            
                            # Match with audio manifest by filename
                            dataset_audio = audio_manifest[
                                audio_manifest['audio_filename'].str.contains(dataset_key, case=False, na=False)
                            ].copy()
                            
                            if len(dataset_audio) > 0:
                                # Try to match filenames
                                dataset_audio['filename'] = dataset_audio['audio_filename']
                                merged = dataset_audio.merge(
                                    metadata_df[['filename', 'Transcription']],
                                    on='filename', how='inner'
                                )
                                
                                if len(merged) > 0:
                                    for _, row in merged.iterrows():
                                        entry = {
                                            'audio': row['audio_path'],
                                            'text': row['Transcription'],
                                            'original_text': row['Transcription'],
                                            'dialect': row.get('language', dataset_key),
                                            'speaker_id': f"{dataset_key}_speaker",
                                            'duration': row.get('file_size_mb', 0) * 10
                                        }
                                        all_data.append(entry)
                                    
                                    print(f"    Matched {len(merged)} entries from {dataset_key}")
                        
                    except Exception as e:
                        print(f"    Error processing {dataset_key}: {str(e)[:50]}")
            
        except Exception as e:
            print(f"  Error loading audio manifest: {str(e)}")
else:
    print("  Audio manifest not found")

# 4. Combine and save
print("\n4. COMBINING DATA")
print("-" * 40)

if all_data:
    # Convert to DataFrame
    combined_df = pd.DataFrame(all_data)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['audio'])
    
    # Filter valid entries
    combined_df = combined_df[combined_df['text'].notna()]
    combined_df = combined_df[combined_df['audio'].notna()]
    combined_df = combined_df[combined_df['text'].str.len() > 0]  # Non-empty text
    
    print(f"  Total combined entries: {len(combined_df)}")
    
    # Save as processed_data_enhanced.csv
    output_file = METADATA_DIR / "processed_data_enhanced.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"  [SAVED] {output_file.name}")
    
    # Create dialect-specific files
    for dialect in combined_df['dialect'].unique():
        dialect_df = combined_df[combined_df['dialect'] == dialect]
        dialect_file = METADATA_DIR / f"processed_data_{dialect}.csv"
        dialect_df.to_csv(dialect_file, index=False)
        print(f"  [SAVED] {dialect_file.name} ({len(dialect_df)} entries)")
    
    # Create TTS metadata format (audio_path|text|speaker)
    tts_metadata = []
    for _, row in combined_df.iterrows():
        tts_metadata.append(f"{row['audio']}|{row['text']}|{row['speaker_id']}")
    
    metadata_txt = METADATA_DIR / "metadata.txt"
    with open(metadata_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tts_metadata))
    print(f"  [SAVED] metadata.txt (Coqui TTS format)")
    
    # Statistics
    print("\n  Statistics:")
    print(f"    Total samples: {len(combined_df)}")
    print(f"    Dialects: {', '.join(combined_df['dialect'].unique())}")
    print(f"    Speakers: {len(combined_df['speaker_id'].unique())}")
    print(f"    Total duration: {combined_df['duration'].sum():.1f} seconds (estimated)")
    
    # Create sample for quick testing
    sample_size = min(100, len(combined_df))
    sample_df = combined_df.head(sample_size)
    sample_file = METADATA_DIR / "tts_sample.csv"
    sample_df.to_csv(sample_file, index=False)
    print(f"  [SAVED] tts_sample.csv ({sample_size} samples for quick testing)")
    
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

# 5. Create enhanced TTS configuration
print("\n5. CREATING ENHANCED TTS CONFIG")
print("-" * 40)

tts_config = {
    "dataset": "twi_tts_enhanced",
    "languages": list(combined_df['dialect'].unique()) if 'combined_df' in locals() and len(combined_df) > 0 else ["twi"],
    "total_samples": len(combined_df) if 'combined_df' in locals() else 0,
    "data_sources": {
        "michset": "Audio-text pairs from MichSet datasets",
        "bible_tts": "Professional Bible recordings",
        "financial_inclusion": "Domain-specific financial audio"
    },
    "features": {
        "enhanced_text_processing": True,
        "phoneme_generation": True,
        "number_expansion": True,
        "currency_processing": True,
        "date_time_processing": True,
        "multi_dialect": True,
        "multi_speaker": True
    },
    "model_recommendations": {
        "primary": "Coqui TTS - Tacotron2",
        "voice_cloning": "XTTS v2",
        "edge": "Kokoro-82M",
        "alternative": "F5-TTS",
        "multi_speaker": "YourTTS"
    },
    "training_params": {
        "batch_size": 16,
        "learning_rate": 0.001,
        "epochs": 1000,
        "save_step": 500,
        "eval_step": 100,
        "grad_clip": 5.0,
        "scheduler": "exponential"
    },
    "paths": {
        "metadata": str(METADATA_DIR / "processed_data_enhanced.csv"),
        "metadata_txt": str(METADATA_DIR / "metadata.txt"),
        "sample": str(METADATA_DIR / "tts_sample.csv"),
        "output_dir": str(BASE_DIR / "models" / "tts")
    },
    "quality_checks": {
        "min_duration": 0.5,
        "max_duration": 15.0,
        "min_text_length": 3,
        "max_text_length": 200,
        "audio_validation": True,
        "text_cleaning": True
    }
}

config_file = METADATA_DIR / "tts_config_enhanced.json"
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(tts_config, f, indent=2, ensure_ascii=False)
print(f"  [SAVED] tts_config_enhanced.json")

# Summary
print("\n" + "=" * 60)
print("ENHANCED TTS DATA PREPARATION COMPLETE!")
print("=" * 60)

print(f"\nData location: {METADATA_DIR}")
print(f"Main file: processed_data_enhanced.csv")

if 'combined_df' in locals() and len(combined_df) > 0:
    print(f"\nDataset Statistics:")
    print(f"  Total samples: {len(combined_df):,}")
    print(f"  Dialects: {', '.join(combined_df['dialect'].unique())}")
    print(f"  Ready for training: YES")
    print(f"  Sample file for testing: tts_sample.csv")
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
print('  synthesizer.synthesize("Yebetumi ayɛ ɛne biribiara wɔ Twi kasa mu!")')
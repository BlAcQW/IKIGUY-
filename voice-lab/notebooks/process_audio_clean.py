#!/usr/bin/env python
"""
Process audio data from Financial Inclusion and other datasets
Windows compatible - no Unicode symbols
"""

import pandas as pd
from pathlib import Path
import json
import os

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
AUDIO_DIR = PROCESSED_DIR / "audio_data"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING AUDIO DATASETS")
print("=" * 50)

# 1. Financial Inclusion datasets
print("\n1. FINANCIAL INCLUSION AUDIO")
print("-" * 30)

fi_datasets = {
    'fante_10': {
        'audio_dir': 'financial_inclusion/fante_10/fisd-fanti-10p/audios',
        'metadata_path': 'financial_inclusion/fante_10/fisd-fanti-10p/data.csv',
        'split': 'test',
        'language': 'fante'
    },
    'fante_90': {
        'audio_dir': 'financial_inclusion/fante_90/fisd-fanti-90p/audios',
        'metadata_path': 'financial_inclusion/fante_90/fisd-fanti-90p/data.csv',
        'split': 'train',
        'language': 'fante'
    },
    'twi_10': {
        'audio_dir': 'financial_inclusion/twi_10/fisd-twi-10p/audios',
        'metadata_path': 'financial_inclusion/twi_10/fisd-twi-10p/data.csv',
        'split': 'test',
        'language': 'twi'
    },
    'twi_90': {
        'audio_dir': 'financial_inclusion/twi_90/fisd-twi-90p/audios',
        'metadata_path': 'financial_inclusion/twi_90/fisd-twi-90p/data.csv',
        'split': 'train',
        'language': 'twi'
    },
    'ewe_10': {
        'audio_dir': 'financial_inclusion/ewe_10/fisd-ewe-10p/audios',
        'metadata_path': 'financial_inclusion/ewe_10/fisd-ewe-10p/data.csv',
        'split': 'test',
        'language': 'ewe'
    },
    'ewe_90': {
        'audio_dir': 'financial_inclusion/ewe_90/fisd-ewe-90p/audios',
        'metadata_path': 'financial_inclusion/ewe_90/fisd-ewe-90p/data.csv',
        'split': 'train',
        'language': 'ewe'
    }
}

audio_manifest = []
total_audio_files = 0
total_duration_seconds = 0

for dataset_name, config in fi_datasets.items():
    audio_dir = RAW_DIR / config['audio_dir']
    metadata_path = RAW_DIR / config['metadata_path']
    
    if not audio_dir.exists():
        print(f"  [SKIP] {dataset_name}: Audio directory not found")
        continue
    
    # Count audio files
    audio_files = list(audio_dir.glob('*.ogg')) + list(audio_dir.glob('*.wav'))
    audio_files += list(audio_dir.glob('*.mp3'))
    
    if not audio_files:
        print(f"  [SKIP] {dataset_name}: No audio files found")
        continue
    
    print(f"\n  {dataset_name}:")
    print(f"    Audio files: {len(audio_files)}")
    
    # Load metadata if exists
    metadata_df = None
    if metadata_path.exists():
        try:
            metadata_df = pd.read_csv(metadata_path)
            print(f"    Metadata entries: {len(metadata_df)}")
            
            # Check columns
            if 'file_name' in metadata_df.columns and 'text' in metadata_df.columns:
                print(f"    [OK] Required columns found")
            else:
                print(f"    [WARNING] Missing columns. Found: {metadata_df.columns.tolist()[:5]}")
        except Exception as e:
            print(f"    [ERROR] Could not load metadata: {str(e)[:50]}")
    else:
        print(f"    [WARNING] No metadata file found")
    
    # Create manifest entries
    for audio_file in audio_files:
        entry = {
            'audio_path': str(audio_file),
            'audio_filename': audio_file.name,
            'dataset': dataset_name,
            'split': config['split'],
            'language': config['language'],
            'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
        }
        
        # Add transcription if available
        if metadata_df is not None:
            # Try to match audio file with metadata
            audio_stem = audio_file.stem
            
            # Try different column names
            for col in ['file_name', 'filename', 'audio_file', 'audio']:
                if col in metadata_df.columns:
                    matches = metadata_df[metadata_df[col].str.contains(audio_stem, na=False)]
                    if not matches.empty:
                        # Get transcription
                        for text_col in ['text', 'transcription', 'transcript', 'sentence']:
                            if text_col in matches.columns:
                                entry['transcription'] = matches.iloc[0][text_col]
                                break
                        break
        
        audio_manifest.append(entry)
    
    total_audio_files += len(audio_files)

print(f"\nTotal Financial Inclusion audio files: {total_audio_files}")

# 2. Check for BibleTTS audio
print("\n2. BIBLE TTS AUDIO")
print("-" * 30)

bible_dirs = [
    RAW_DIR / "bible_tts",
    RAW_DIR / "bibletss",
    RAW_DIR / "BibleTTS"
]

for bible_dir in bible_dirs:
    if bible_dir.exists():
        # Look for audio files recursively
        audio_files = list(bible_dir.rglob('*.wav')) + list(bible_dir.rglob('*.mp3'))
        audio_files += list(bible_dir.rglob('*.ogg'))
        
        if audio_files:
            print(f"  Found {len(audio_files)} audio files in {bible_dir.name}")
            
            # Group by subdirectory
            by_subdir = {}
            for audio_file in audio_files:
                subdir = audio_file.parent.name
                if subdir not in by_subdir:
                    by_subdir[subdir] = []
                by_subdir[subdir].append(audio_file)
            
            for subdir, files in by_subdir.items():
                print(f"    {subdir}: {len(files)} files")
                
                # Add to manifest
                for audio_file in files[:100]:  # Sample first 100
                    audio_manifest.append({
                        'audio_path': str(audio_file),
                        'audio_filename': audio_file.name,
                        'dataset': f'bible_tts_{subdir}',
                        'split': 'train',
                        'language': 'twi',
                        'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
                    })
            
            total_audio_files += len(audio_files)
            break

# 3. Check for MichSetHowusu audio
print("\n3. MICHSETHOWUSU AUDIO")
print("-" * 30)

michset_audio_dir = RAW_DIR / "michsethowusu" / "audio"
if michset_audio_dir.exists():
    audio_files = list(michset_audio_dir.rglob('*.wav')) + list(michset_audio_dir.rglob('*.mp3'))
    if audio_files:
        print(f"  Found {len(audio_files)} audio files")
        
        for audio_file in audio_files[:100]:
            audio_manifest.append({
                'audio_path': str(audio_file),
                'audio_filename': audio_file.name,
                'dataset': 'michsethowusu_audio',
                'split': 'train',
                'language': 'twi',
                'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
            })
        
        total_audio_files += len(audio_files)
else:
    print("  No audio directory found")

# 4. Save audio manifest
print("\n" + "=" * 50)
print("SAVING AUDIO MANIFEST")
print("=" * 50)

if audio_manifest:
    manifest_df = pd.DataFrame(audio_manifest)
    
    # Save full manifest
    manifest_path = AUDIO_DIR / "audio_manifest.csv"
    manifest_df.to_csv(manifest_path, index=False)
    print(f"\n[SAVED] audio_manifest.csv ({len(manifest_df)} entries)")
    
    # Save by split
    for split in ['train', 'test']:
        split_df = manifest_df[manifest_df['split'] == split]
        if not split_df.empty:
            split_path = AUDIO_DIR / f"audio_manifest_{split}.csv"
            split_df.to_csv(split_path, index=False)
            print(f"[SAVED] audio_manifest_{split}.csv ({len(split_df)} entries)")
    
    # Save by language
    for language in manifest_df['language'].unique():
        lang_df = manifest_df[manifest_df['language'] == language]
        lang_path = AUDIO_DIR / f"audio_manifest_{language}.csv"
        lang_df.to_csv(lang_path, index=False)
        print(f"[SAVED] audio_manifest_{language}.csv ({len(lang_df)} entries)")
    
    # Statistics
    stats = {
        'total_audio_files': len(manifest_df),
        'total_size_gb': manifest_df['file_size_mb'].sum() / 1024,
        'languages': manifest_df['language'].value_counts().to_dict(),
        'datasets': manifest_df['dataset'].value_counts().to_dict(),
        'splits': manifest_df['split'].value_counts().to_dict(),
        'files_with_transcriptions': manifest_df['transcription'].notna().sum() if 'transcription' in manifest_df.columns else 0
    }
    
    stats_path = AUDIO_DIR / "audio_statistics.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\n[SAVED] audio_statistics.json")
    
    # Print summary
    print("\n" + "=" * 50)
    print("AUDIO PROCESSING COMPLETE!")
    print("=" * 50)
    
    print("\nAudio Statistics:")
    print("-" * 30)
    print(f"  Total files: {stats['total_audio_files']:,}")
    print(f"  Total size: {stats['total_size_gb']:.2f} GB")
    
    if stats.get('files_with_transcriptions'):
        print(f"  Files with transcriptions: {stats['files_with_transcriptions']:,}")
    
    print("\n  By Language:")
    for lang, count in stats['languages'].items():
        print(f"    {lang}: {count:,} files")
    
    print("\n  By Split:")
    for split, count in stats['splits'].items():
        print(f"    {split}: {count:,} files")
    
    print(f"\nOutput location: {AUDIO_DIR}")
    
else:
    print("\n[WARNING] No audio files found to process")

print("\nNext steps:")
print("  1. Extract JW300 and Common Voice archives")
print("  2. Convert audio to 16kHz mono WAV format")
print("  3. Align transcriptions with audio durations")
print("  4. Create ASR training manifests")
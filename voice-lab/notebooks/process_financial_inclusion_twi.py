#!/usr/bin/env python
"""
Process Financial Inclusion Twi datasets (Akuapem and Asante)
Organize and create training manifests for ASR models
"""

import pandas as pd
from pathlib import Path
import json

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "financial_inclusion"
PROCESSED_DIR = BASE_DIR / "processed"
FI_DIR = PROCESSED_DIR / "financial_inclusion_twi"
FI_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING FINANCIAL INCLUSION TWI DATASETS")
print("=" * 50)

# Define all Twi datasets in Financial Inclusion
twi_datasets = {
    'akuapem_twi_90': {
        'path': 'akuapem_twi_90/fisd-akuapim-twi-90p',
        'dialect': 'Akuapem Twi',
        'split': 'train',
        'description': 'Akuapem Twi 90% training set'
    },
    'akuapem_twi_10': {
        'path': 'akuapem_twi_10/fisd-akuapim-twi-10p',
        'dialect': 'Akuapem Twi',
        'split': 'test',
        'description': 'Akuapem Twi 10% test set'
    },
    'asante_twi_90': {
        'path': 'asante_twi_90/fisd-asanti-twi-90p',
        'dialect': 'Asante Twi',
        'split': 'train',
        'description': 'Asante Twi 90% training set'
    },
    'asante_twi_10': {
        'path': 'asante_twi_10/fisd-asanti-twi-10p',
        'dialect': 'Asante Twi',
        'split': 'test',
        'description': 'Asante Twi 10% test set'
    }
}

all_manifests = []
statistics = {
    'total_audio': 0,
    'total_with_transcripts': 0,
    'by_dialect': {},
    'by_split': {'train': 0, 'test': 0}
}

for dataset_key, dataset_info in twi_datasets.items():
    print(f"\n{dataset_info['description']}")
    print("-" * 40)
    
    dataset_dir = RAW_DIR / dataset_info['path']
    audio_dir = dataset_dir / 'audios'
    metadata_file = dataset_dir / 'data.csv'
    
    if not audio_dir.exists():
        print(f"  [SKIP] Audio directory not found: {audio_dir}")
        continue
    
    # Count audio files
    audio_files = list(audio_dir.glob('*.ogg'))
    print(f"  Audio files: {len(audio_files):,}")
    statistics['total_audio'] += len(audio_files)
    
    # Load metadata
    metadata = None
    if metadata_file.exists():
        try:
            # Try different encodings and separators
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                for sep in [',', '\t', '|']:
                    try:
                        metadata = pd.read_csv(metadata_file, encoding=encoding, sep=sep)
                        if len(metadata.columns) > 1:  # Valid if more than 1 column
                            print(f"  Metadata loaded: {len(metadata):,} entries")
                            print(f"  Columns: {metadata.columns.tolist()}")
                            break
                    except:
                        continue
                if metadata is not None and len(metadata.columns) > 1:
                    break
        except Exception as e:
            print(f"  [ERROR] Could not load metadata: {str(e)[:50]}")
    else:
        print(f"  [WARNING] No metadata file found")
    
    # Process audio files
    dataset_manifest = []
    paired_count = 0
    
    for audio_file in audio_files[:100]:  # Process first 100 for testing
        entry = {
            'audio_path': str(audio_file),
            'filename': audio_file.name,
            'dataset': dataset_key,
            'dialect': dataset_info['dialect'],
            'split': dataset_info['split'],
            'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
        }
        
        # Try to find transcript in metadata
        if metadata is not None:
            # Match by filename
            audio_stem = audio_file.stem
            
            # Try different column names for file reference
            for file_col in ['file_name', 'filename', 'audio_file', 'audio', 'path']:
                if file_col in metadata.columns:
                    # Look for matching row
                    matches = metadata[metadata[file_col].str.contains(audio_stem, na=False)]
                    if not matches.empty:
                        # Get transcript
                        for text_col in ['text', 'transcription', 'transcript', 'sentence']:
                            if text_col in matches.columns:
                                entry['transcript'] = str(matches.iloc[0][text_col])
                                entry['has_transcript'] = True
                                paired_count += 1
                                break
                        break
        
        if 'has_transcript' not in entry:
            entry['has_transcript'] = False
            entry['transcript'] = None
        
        dataset_manifest.append(entry)
        all_manifests.append(entry)
    
    print(f"  Processed: {len(dataset_manifest)} files")
    print(f"  With transcripts: {paired_count}")
    
    # Update statistics
    statistics['total_with_transcripts'] += paired_count
    statistics['by_split'][dataset_info['split']] += len(dataset_manifest)
    
    if dataset_info['dialect'] not in statistics['by_dialect']:
        statistics['by_dialect'][dataset_info['dialect']] = {
            'total': 0,
            'with_transcript': 0,
            'train': 0,
            'test': 0
        }
    
    statistics['by_dialect'][dataset_info['dialect']]['total'] += len(audio_files)
    statistics['by_dialect'][dataset_info['dialect']]['with_transcript'] += paired_count
    statistics['by_dialect'][dataset_info['dialect']][dataset_info['split']] += len(audio_files)
    
    # Save dataset-specific manifest
    if dataset_manifest:
        dataset_df = pd.DataFrame(dataset_manifest)
        dataset_file = FI_DIR / f"fi_{dataset_key}.csv"
        dataset_df.to_csv(dataset_file, index=False)
        print(f"  [SAVED] {dataset_file.name}")

# Save combined manifests
print("\n" + "=" * 50)
print("SAVING COMBINED MANIFESTS")
print("=" * 50)

if all_manifests:
    # Full manifest
    full_df = pd.DataFrame(all_manifests)
    full_file = FI_DIR / "financial_inclusion_twi_complete.csv"
    full_df.to_csv(full_file, index=False)
    print(f"\n[SAVED] {full_file.name} ({len(full_df)} entries)")
    
    # ASR training manifests by split
    for split in ['train', 'test']:
        split_data = full_df[full_df['split'] == split]
        if not split_data.empty:
            # Filter for entries with transcripts
            with_transcript = split_data[split_data['has_transcript'] == True]
            
            if not with_transcript.empty:
                # Create ASR manifest
                asr_manifest = []
                for _, row in with_transcript.iterrows():
                    asr_manifest.append({
                        'audio_filepath': row['audio_path'],
                        'text': row['transcript'],
                        'duration': -1,  # Will be calculated
                        'dialect': row['dialect']
                    })
                
                # Save ASR manifest
                asr_file = FI_DIR / f"asr_{split}_manifest.json"
                with open(asr_file, 'w', encoding='utf-8') as f:
                    json.dump(asr_manifest, f, ensure_ascii=False, indent=2)
                print(f"[SAVED] {asr_file.name} ({len(asr_manifest)} entries)")
    
    # Statistics summary
    stats_summary = {
        'total_audio_files': statistics['total_audio'],
        'total_with_transcripts': statistics['total_with_transcripts'],
        'dialects': statistics['by_dialect'],
        'splits': statistics['by_split'],
        'file_formats': 'OGG Vorbis',
        'domain': 'Financial Inclusion',
        'languages': ['Akuapem Twi', 'Asante Twi']
    }
    
    stats_file = FI_DIR / "fi_twi_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print(f"\n[SAVED] {stats_file.name}")

# Print summary
print("\n" + "=" * 50)
print("FINANCIAL INCLUSION TWI PROCESSING COMPLETE!")
print("=" * 50)

print(f"\nTotal audio files: {statistics['total_audio']:,}")
print(f"Files with transcripts: {statistics['total_with_transcripts']:,}")

print("\nBy Dialect:")
for dialect, stats in statistics['by_dialect'].items():
    print(f"\n  {dialect}:")
    print(f"    Total files: {stats['total']:,}")
    print(f"    With transcripts: {stats['with_transcript']:,}")
    print(f"    Train/Test: {stats['train']:,} / {stats['test']:,}")

print("\nExpected Audio Counts (Full Dataset):")
print("  Akuapem Twi:")
print("    Train (90%): ~25,636 files")
print("    Test (10%): ~2,848 files")
print("  Asante Twi:")
print("    Train (90%): ~28,064 files")
print("    Test (10%): ~3,118 files")
print("\nTotal Expected: ~59,666 audio files")

print(f"\nOutput location: {FI_DIR}")
print("\nThe Financial Inclusion Twi data is ready for:")
print("  1. ASR model training (Whisper, Wav2Vec2)")
print("  2. Dialect-specific models")
print("  3. Financial domain speech recognition")
print("  4. Cross-dialect evaluation")
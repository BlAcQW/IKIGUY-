#!/usr/bin/env python
"""
Fixed extraction for MichSetHowusu Arrow audio
Handles audio paths instead of arrays
"""

from datasets import load_from_disk, Audio
from pathlib import Path
import json
import pandas as pd
import os

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "michsethowusu"
PROCESSED_DIR = BASE_DIR / "processed"
OUTPUT_DIR = PROCESSED_DIR / "michset_audio_manifests"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("EXTRACTING MICHSETHOWUSU AUDIO - FIXED VERSION")
print("=" * 60)

# Define datasets
datasets_info = [
    {
        'name': 'twi_multispeaker',
        'path': RAW_DIR / 'twi_multispeaker_audio_transcribed',
        'language': 'Twi'
    },
    {
        'name': 'akuapem_multispeaker',
        'path': RAW_DIR / 'akuapem_multispeaker_audio_transcribed',
        'language': 'Akuapem Twi'
    },
    {
        'name': 'fante_multispeaker',
        'path': RAW_DIR / 'fante_multispeaker_audio_transcribed',
        'language': 'Fante'
    }
]

all_manifests = []
total_samples = 0

for dataset_info in datasets_info:
    print(f"\n{dataset_info['name'].upper()}")
    print("-" * 40)
    
    dataset_path = dataset_info['path']
    
    if not dataset_path.exists():
        print(f"  [SKIP] Not found: {dataset_path}")
        continue
    
    try:
        # Load dataset
        print(f"  Loading dataset...")
        dataset = load_from_disk(str(dataset_path))
        
        print(f"  Dataset loaded!")
        print(f"  Splits: {list(dataset.keys())}")
        
        # Process each split
        for split_name in dataset.keys():
            split_data = dataset[split_name]
            num_examples = len(split_data)
            print(f"\n  {split_name} split: {num_examples:,} examples")
            
            # Get features
            features = split_data.features
            print(f"    Features: {list(features.keys())}")
            
            # Create manifest without extracting audio
            manifest_entries = []
            
            # Process in batches for efficiency
            batch_size = 100
            num_batches = (num_examples + batch_size - 1) // batch_size
            
            print(f"    Processing {min(1000, num_examples)} examples...")
            
            for batch_idx in range(min(10, num_batches)):  # Process up to 1000 examples
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, num_examples)
                
                # Get batch
                batch = split_data[start_idx:end_idx]
                
                # Process each example in batch
                for i in range(len(batch['transcription'])):
                    try:
                        # Get audio path if available
                        audio_path = None
                        if 'audio_path' in batch:
                            audio_path = batch['audio_path'][i]
                        elif 'audio' in batch:
                            # Audio might be a dict with path
                            audio_data = batch['audio'][i]
                            if isinstance(audio_data, dict) and 'path' in audio_data:
                                audio_path = audio_data['path']
                        
                        # Get transcription
                        transcription = batch['transcription'][i] if 'transcription' in batch else ""
                        
                        # Create manifest entry
                        entry = {
                            'index': start_idx + i,
                            'audio_path': audio_path if audio_path else f"audio_{start_idx + i}",
                            'transcription': transcription,
                            'dataset': dataset_info['name'],
                            'language': dataset_info['language'],
                            'split': split_name
                        }
                        
                        manifest_entries.append(entry)
                        
                    except Exception as e:
                        print(f"      Error at index {start_idx + i}: {str(e)[:50]}")
                        continue
                
                if (batch_idx + 1) % 5 == 0:
                    print(f"      Processed {(batch_idx + 1) * batch_size} examples...")
            
            # Save split manifest
            if manifest_entries:
                split_file = OUTPUT_DIR / f"{dataset_info['name']}_{split_name}_manifest.csv"
                split_df = pd.DataFrame(manifest_entries)
                split_df.to_csv(split_file, index=False)
                print(f"    [SAVED] {split_file.name} ({len(manifest_entries)} entries)")
                
                # Add to combined manifest
                all_manifests.extend(manifest_entries)
                total_samples += len(manifest_entries)
                
                # Show sample entries
                if len(manifest_entries) > 0:
                    print(f"\n    Sample entries:")
                    for entry in manifest_entries[:3]:
                        print(f"      Audio: {entry['audio_path']}")
                        if entry['transcription']:
                            print(f"      Text: {entry['transcription'][:60]}...")
        
        # Also try to get actual dataset info
        dataset_info_file = dataset_path / "dataset_info.json"
        if dataset_info_file.exists():
            with open(dataset_info_file, 'r') as f:
                info = json.load(f)
            
            # Save for reference
            info_output = OUTPUT_DIR / f"{dataset_info['name']}_info.json"
            with open(info_output, 'w') as f:
                json.dump(info, f, indent=2)
            print(f"\n  [SAVED] Dataset info: {info_output.name}")
            
            # Extract useful stats
            if 'download_size' in info:
                print(f"  Dataset size: {info['download_size'] / (1024**3):.2f} GB")
            if 'dataset_size' in info:
                print(f"  Uncompressed: {info['dataset_size'] / (1024**3):.2f} GB")
        
    except Exception as e:
        print(f"  Error loading dataset: {str(e)}")
        
        # Try alternative: read metadata directly
        print(f"  Attempting to read metadata directly...")
        
        metadata_file = dataset_path / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                print(f"  Metadata loaded: {metadata.get('actual_samples', 'unknown')} samples")
                
                # Save metadata
                meta_output = OUTPUT_DIR / f"{dataset_info['name']}_metadata.json"
                with open(meta_output, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"  [SAVED] {meta_output.name}")
                
            except Exception as e2:
                print(f"  Could not read metadata: {str(e2)[:50]}")

# Save combined manifest
print("\n" + "=" * 60)
print("SAVING COMBINED MANIFEST")
print("=" * 60)

if all_manifests:
    combined_df = pd.DataFrame(all_manifests)
    combined_file = OUTPUT_DIR / "michset_all_manifests.csv"
    combined_df.to_csv(combined_file, index=False)
    print(f"\n[SAVED] {combined_file.name} ({len(combined_df)} entries)")
    
    # Create ASR training manifests
    for split in ['train', 'test']:
        split_data = combined_df[combined_df['split'] == split]
        if not split_data.empty:
            # Create JSON manifest for ASR
            asr_manifest = []
            for _, row in split_data.iterrows():
                asr_manifest.append({
                    'audio_filepath': row['audio_path'],
                    'text': row['transcription'],
                    'duration': -1,  # Unknown
                    'language': row['language']
                })
            
            asr_file = OUTPUT_DIR / f"asr_{split}_manifest.json"
            with open(asr_file, 'w', encoding='utf-8') as f:
                json.dump(asr_manifest, f, ensure_ascii=False, indent=2)
            print(f"[SAVED] {asr_file.name} ({len(asr_manifest)} entries)")
    
    # Statistics
    stats = {
        'total_entries': len(combined_df),
        'datasets': combined_df['dataset'].value_counts().to_dict(),
        'languages': combined_df['language'].value_counts().to_dict(),
        'splits': combined_df['split'].value_counts().to_dict(),
        'entries_with_text': len(combined_df[combined_df['transcription'] != ""]),
        'unique_transcriptions': combined_df['transcription'].nunique()
    }
    
    stats_file = OUTPUT_DIR / "michset_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"\n[SAVED] {stats_file.name}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE!")
    print("=" * 60)
    
    print(f"\nTotal manifest entries: {stats['total_entries']:,}")
    print(f"Entries with transcriptions: {stats['entries_with_text']:,}")
    print(f"Unique transcriptions: {stats['unique_transcriptions']:,}")
    
    print("\nBy Dataset:")
    for dataset, count in stats['datasets'].items():
        print(f"  {dataset}: {count:,}")
    
    print("\nBy Language:")
    for lang, count in stats['languages'].items():
        print(f"  {lang}: {count:,}")
    
    print("\nBy Split:")
    for split, count in stats['splits'].items():
        print(f"  {split}: {count:,}")

else:
    print("\nNo manifests created")

print(f"\nOutput location: {OUTPUT_DIR}")

print("\n" + "=" * 60)
print("IMPORTANT NOTES")
print("=" * 60)
print("\n1. The audio files are referenced by paths, not embedded")
print("2. To use for training, you need to:")
print("   - Locate the actual audio files")
print("   - Or use HuggingFace's automatic audio loading")
print("3. The manifests can be used with ASR frameworks")
print("4. Total estimated audio: ~12 GB across all datasets")
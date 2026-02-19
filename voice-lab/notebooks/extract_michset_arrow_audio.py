#!/usr/bin/env python
"""
Extract MichSetHowusu Arrow audio using HuggingFace datasets
Convert Arrow format to usable audio files and manifests
"""

from datasets import load_from_disk
from pathlib import Path
import json
import pandas as pd
import soundfile as sf
import numpy as np

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "michsethowusu"
PROCESSED_DIR = BASE_DIR / "processed"
AUDIO_OUTPUT_DIR = PROCESSED_DIR / "michset_extracted_audio"
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("EXTRACTING MICHSETHOWUSU ARROW AUDIO WITH HUGGINGFACE")
print("=" * 60)

# Define datasets to process
datasets_to_process = [
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
total_extracted = 0

for dataset_info in datasets_to_process:
    print(f"\n{dataset_info['name'].upper()}")
    print("-" * 40)
    
    dataset_path = dataset_info['path']
    
    if not dataset_path.exists():
        print(f"  [SKIP] Not found: {dataset_path}")
        continue
    
    try:
        # Load the dataset using HuggingFace datasets
        print(f"  Loading dataset from {dataset_path.name}...")
        dataset = load_from_disk(str(dataset_path))
        
        print(f"  Dataset loaded successfully!")
        print(f"  Splits: {list(dataset.keys())}")
        
        # Process each split
        for split_name in dataset.keys():
            split_data = dataset[split_name]
            print(f"\n  Processing {split_name} split...")
            print(f"    Number of examples: {len(split_data)}")
            
            # Check features
            if split_data.features:
                print(f"    Features: {list(split_data.features.keys())}")
            
            # Create output directory for this dataset/split
            split_output_dir = AUDIO_OUTPUT_DIR / dataset_info['name'] / split_name
            split_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process a sample of the data
            sample_size = min(100, len(split_data))  # Process up to 100 samples
            print(f"    Processing {sample_size} samples...")
            
            manifest_entries = []
            
            for idx in range(sample_size):
                try:
                    example = split_data[idx]
                    
                    # Extract audio
                    audio_data = None
                    sample_rate = None
                    
                    if 'audio' in example:
                        audio_info = example['audio']
                        if isinstance(audio_info, dict):
                            if 'array' in audio_info:
                                audio_data = audio_info['array']
                                sample_rate = audio_info.get('sampling_rate', 16000)
                            elif 'path' in audio_info:
                                # Audio is a file path
                                audio_path = audio_info['path']
                                print(f"      Audio path found: {audio_path}")
                    elif 'audio_path' in example:
                        # Direct audio path
                        audio_path = example['audio_path']
                        print(f"      Audio path: {audio_path}")
                    
                    # Extract transcription
                    transcript = None
                    if 'transcription' in example:
                        transcript = example['transcription']
                    elif 'text' in example:
                        transcript = example['text']
                    elif 'sentence' in example:
                        transcript = example['sentence']
                    
                    # Save audio if we have array data
                    if audio_data is not None and isinstance(audio_data, (list, np.ndarray)):
                        # Convert to numpy array if needed
                        if isinstance(audio_data, list):
                            audio_data = np.array(audio_data)
                        
                        # Save as WAV file
                        audio_filename = f"{dataset_info['name']}_{split_name}_{idx:05d}.wav"
                        audio_filepath = split_output_dir / audio_filename
                        
                        # Save audio
                        sf.write(str(audio_filepath), audio_data, sample_rate)
                        
                        # Create manifest entry
                        manifest_entries.append({
                            'audio_filepath': str(audio_filepath),
                            'text': transcript if transcript else "",
                            'duration': len(audio_data) / sample_rate,
                            'sample_rate': sample_rate,
                            'language': dataset_info['language'],
                            'dataset': dataset_info['name'],
                            'split': split_name,
                            'index': idx
                        })
                        
                        total_extracted += 1
                        
                        if (idx + 1) % 10 == 0:
                            print(f"      Extracted {idx + 1} audio files...")
                    
                    # If no audio array but have path, record it
                    elif 'audio_path' in locals():
                        manifest_entries.append({
                            'audio_filepath': audio_path,
                            'text': transcript if transcript else "",
                            'duration': -1,
                            'sample_rate': -1,
                            'language': dataset_info['language'],
                            'dataset': dataset_info['name'],
                            'split': split_name,
                            'index': idx,
                            'needs_extraction': True
                        })
                    
                except Exception as e:
                    print(f"      Error processing example {idx}: {str(e)[:50]}")
                    continue
            
            # Save manifest for this split
            if manifest_entries:
                manifest_df = pd.DataFrame(manifest_entries)
                manifest_file = split_output_dir / f"manifest.csv"
                manifest_df.to_csv(manifest_file, index=False)
                print(f"    [SAVED] {manifest_file}")
                
                # Add to overall manifest
                all_manifests.extend(manifest_entries)
                
                # Show sample
                print(f"    Sample entry:")
                sample = manifest_entries[0]
                print(f"      Audio: {Path(sample['audio_filepath']).name}")
                if sample.get('text'):
                    print(f"      Text: {sample['text'][:80]}...")
                if sample.get('duration', -1) > 0:
                    print(f"      Duration: {sample['duration']:.2f}s")
        
    except Exception as e:
        print(f"  Error loading dataset: {str(e)}")
        print(f"  This dataset may need to be loaded differently")

# Save combined manifest
print("\n" + "=" * 60)
print("SAVING COMBINED MANIFEST")
print("=" * 60)

if all_manifests:
    combined_df = pd.DataFrame(all_manifests)
    combined_file = AUDIO_OUTPUT_DIR / "michset_all_extracted.csv"
    combined_df.to_csv(combined_file, index=False)
    print(f"\n[SAVED] {combined_file.name} ({len(combined_df)} entries)")
    
    # Statistics
    stats = {
        'total_files_extracted': total_extracted,
        'total_manifest_entries': len(all_manifests),
        'datasets_processed': [d['name'] for d in datasets_to_process if (d['path']).exists()],
        'languages': combined_df['language'].unique().tolist() if 'language' in combined_df else [],
        'splits': combined_df['split'].unique().tolist() if 'split' in combined_df else [],
        'total_duration_seconds': combined_df[combined_df['duration'] > 0]['duration'].sum() if 'duration' in combined_df else 0,
        'files_with_text': len(combined_df[combined_df['text'] != ""]) if 'text' in combined_df else 0
    }
    
    stats_file = AUDIO_OUTPUT_DIR / "extraction_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"[SAVED] {stats_file.name}")
    
    # Print summary
    print("\nExtraction Summary:")
    print(f"  Total audio files extracted: {total_extracted}")
    print(f"  Total manifest entries: {len(all_manifests)}")
    if stats['total_duration_seconds'] > 0:
        print(f"  Total duration: {stats['total_duration_seconds']/3600:.1f} hours")
    print(f"  Files with transcriptions: {stats['files_with_text']}")

else:
    print("\nNo audio files were extracted")
    print("The datasets may be in a different format or need different loading method")

print(f"\nOutput location: {AUDIO_OUTPUT_DIR}")
print("\nNote: If extraction failed, the audio may be:")
print("  1. Stored as file paths rather than arrays")
print("  2. In a different format requiring custom loading")
print("  3. Accessible through the original audio files referenced in metadata")
#!/usr/bin/env python
"""
Process MichSetHowusu Arrow format audio datasets
Convert from HuggingFace Arrow format to usable audio files
"""

import pandas as pd
from pathlib import Path
import json
import pyarrow.parquet as pq
import pyarrow as pa

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "michsethowusu"
PROCESSED_DIR = BASE_DIR / "processed"
ARROW_OUTPUT_DIR = PROCESSED_DIR / "michset_audio"
ARROW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING MICHSETHOWUSU ARROW AUDIO DATASETS")
print("=" * 60)

# Define the Arrow datasets
arrow_datasets = {
    'twi_multispeaker': {
        'path': 'twi_multispeaker_audio_transcribed',
        'language': 'Twi',
        'description': 'Twi multispeaker audio with transcriptions'
    },
    'akuapem_multispeaker': {
        'path': 'akuapem_multispeaker_audio_transcribed',
        'language': 'Akuapem Twi',
        'description': 'Akuapem Twi multispeaker audio with transcriptions'
    },
    'fante_multispeaker': {
        'path': 'fante_multispeaker_audio_transcribed',
        'language': 'Fante',
        'description': 'Fante multispeaker audio with transcriptions'
    }
}

all_manifests = []
total_samples = 0

for dataset_key, dataset_info in arrow_datasets.items():
    print(f"\n{dataset_info['description'].upper()}")
    print("-" * 40)
    
    dataset_dir = RAW_DIR / dataset_info['path']
    if not dataset_dir.exists():
        print(f"  [SKIP] Directory not found: {dataset_dir}")
        continue
    
    # Check for metadata
    metadata_file = dataset_dir / "metadata.json"
    dataset_dict_file = dataset_dir / "dataset_dict.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            print(f"  Metadata found: {list(metadata.keys())[:5]}")
        except Exception as e:
            print(f"  Error loading metadata: {str(e)[:50]}")
    
    if dataset_dict_file.exists():
        try:
            with open(dataset_dict_file, 'r', encoding='utf-8') as f:
                dataset_dict = json.load(f)
            
            # Show dataset structure
            if 'splits' in dataset_dict:
                for split_name, split_info in dataset_dict['splits'].items():
                    print(f"  Split '{split_name}': {split_info.get('num_examples', 'unknown')} examples")
        except Exception as e:
            print(f"  Error loading dataset_dict: {str(e)[:50]}")
    
    # Process train and test splits
    for split in ['train', 'test']:
        split_dir = dataset_dir / split
        if not split_dir.exists():
            print(f"  [SKIP] {split} directory not found")
            continue
        
        print(f"\n  Processing {split} split...")
        
        # Look for Arrow files
        arrow_files = list(split_dir.glob("*.arrow"))
        if arrow_files:
            print(f"    Found {len(arrow_files)} Arrow files")
            
            # Try to load Arrow data
            try:
                # Load the first Arrow file to understand structure
                first_arrow = arrow_files[0]
                
                # Try using pyarrow to read
                try:
                    with pa.memory_map(str(first_arrow)) as source:
                        batch_reader = pa.ipc.open_file(source)
                        
                        # Get schema
                        schema = batch_reader.schema
                        print(f"    Schema fields: {schema.names[:5]}")
                        
                        # Read first batch
                        if batch_reader.num_record_batches > 0:
                            batch = batch_reader.get_batch(0)
                            print(f"    First batch: {batch.num_rows} rows")
                            
                            # Convert to pandas for easier handling
                            df_sample = batch.to_pandas()
                            
                            # Show columns
                            print(f"    Columns: {df_sample.columns.tolist()}")
                            
                            # Create manifest entries
                            manifest_entries = []
                            for idx, row in df_sample.head(10).iterrows():
                                entry = {
                                    'dataset': dataset_key,
                                    'language': dataset_info['language'],
                                    'split': split,
                                    'index': idx
                                }
                                
                                # Map common column names
                                for col in df_sample.columns:
                                    if 'text' in col.lower() or 'transcript' in col.lower():
                                        entry['transcript'] = str(row[col])
                                    elif 'audio' in col.lower() or 'path' in col.lower():
                                        entry['audio_info'] = str(row[col])[:100]
                                    elif 'speaker' in col.lower():
                                        entry['speaker'] = str(row[col])
                                
                                manifest_entries.append(entry)
                            
                            if manifest_entries:
                                # Save sample manifest
                                sample_file = ARROW_OUTPUT_DIR / f"{dataset_key}_{split}_sample.json"
                                with open(sample_file, 'w', encoding='utf-8') as f:
                                    json.dump(manifest_entries, f, ensure_ascii=False, indent=2)
                                print(f"    [SAVED] {sample_file.name}")
                            
                            total_samples += batch.num_rows
                            
                except Exception as e:
                    print(f"    Error reading Arrow file: {str(e)[:100]}")
                
            except Exception as e:
                print(f"    Error processing Arrow files: {str(e)[:100]}")
        
        # Check for dataset_info.json
        dataset_info_file = split_dir / "dataset_info.json"
        if dataset_info_file.exists():
            try:
                with open(dataset_info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                
                # Extract useful information
                if 'dataset_size' in info:
                    print(f"    Dataset size: {info['dataset_size'] / (1024**2):.1f} MB")
                if 'download_size' in info:
                    print(f"    Download size: {info['download_size'] / (1024**2):.1f} MB")
                if 'features' in info:
                    features = info['features']
                    print(f"    Features: {list(features.keys())}")
                    
                    # Check for audio feature
                    if 'audio' in features:
                        audio_info = features['audio']
                        print(f"    Audio feature found: {audio_info}")
                    
                    # Check for text/transcript
                    for key in ['text', 'transcript', 'transcription']:
                        if key in features:
                            print(f"    Text feature: {key}")
                
                # Save the info for reference
                info_output = ARROW_OUTPUT_DIR / f"{dataset_key}_{split}_info.json"
                with open(info_output, 'w', encoding='utf-8') as f:
                    json.dump(info, f, indent=2)
                print(f"    [SAVED] {info_output.name}")
                
            except Exception as e:
                print(f"    Error reading dataset_info: {str(e)[:50]}")
        
        # Check state.json for dataset state
        state_file = split_dir / "state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                if '_data_files' in state:
                    data_files = state['_data_files']
                    print(f"    Data files in state: {len(data_files)}")
                if '_split' in state:
                    print(f"    Split name: {state['_split']}")
                
            except Exception as e:
                print(f"    Error reading state: {str(e)[:50]}")

# Summary
print("\n" + "=" * 60)
print("ARROW DATASET PROCESSING SUMMARY")
print("=" * 60)

print(f"\nTotal samples found: {total_samples:,}")
print(f"Output location: {ARROW_OUTPUT_DIR}")

print("\nNOTE: Arrow files contain audio data in binary format")
print("To fully extract audio, you need to:")
print("  1. Install HuggingFace datasets library")
print("  2. Load the dataset using datasets.load_from_disk()")
print("  3. Extract audio arrays and save as WAV files")

print("\nAlternative: Use the metadata files to understand structure")
print("and process the original audio if available elsewhere.")

# Create summary report
summary = {
    'datasets_found': list(arrow_datasets.keys()),
    'total_arrow_files': sum(len(list((RAW_DIR / d['path']).rglob("*.arrow"))) 
                            for d in arrow_datasets.values() 
                            if (RAW_DIR / d['path']).exists()),
    'total_samples_examined': total_samples,
    'note': 'Arrow files need HuggingFace datasets library for full extraction'
}

summary_file = ARROW_OUTPUT_DIR / "arrow_datasets_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print(f"\n[SAVED] Summary: {summary_file.name}")
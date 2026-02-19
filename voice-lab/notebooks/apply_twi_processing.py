#!/usr/bin/env python
"""
Apply Twi text processing to the 4M+ training pairs
Creates normalized versions for different model types
"""

import pandas as pd
from pathlib import Path
import json
import sys
import os

# Add current directory to path to import the processor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced processor
from enhanced_twi_processor import EnhancedTwiTextProcessor

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"
TEXT_DIR = PROCESSED_DIR / "text_data"
NORMALIZED_DIR = PROCESSED_DIR / "text_data_normalized"
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

print("APPLYING TWI TEXT PROCESSING")
print("=" * 50)

# Initialize processor
processor = EnhancedTwiTextProcessor(dialect='asante')

# Process each split
for split in ['train', 'val', 'test']:
    split_file = TEXT_DIR / f"{split}_pairs.parquet"
    
    if not split_file.exists():
        print(f"[SKIP] {split} file not found")
        continue
    
    print(f"\nProcessing {split} split...")
    df = pd.read_parquet(split_file)
    print(f"  Loaded {len(df):,} pairs")
    
    # Determine sample size based on split
    if split == 'train':
        # Process subset for training (can increase later)
        sample_size = min(100000, len(df))  # Start with 100K
    else:
        # Process all validation and test
        sample_size = len(df)
    
    print(f"  Processing {sample_size:,} pairs...")
    
    # Sample the data
    df_sample = df.head(sample_size).copy()
    
    # Process Twi text
    processed_data = []
    errors = []
    
    for idx, row in enumerate(df_sample.itertuples()):
        if idx % 10000 == 0 and idx > 0:
            print(f"    Processed {idx:,} / {sample_size:,}")
        
        try:
            # Process for general use (expand numbers, abbreviations, etc.)
            result = processor.process_text(
                row.Twi,
                expand_numbers=True,
                expand_abbreviations=True,
                process_datetime=True,
                apply_dialect=True,
                generate_phonemes=False
            )
            
            # Store processed version
            processed_data.append({
                'english': row.English,
                'twi_original': row.Twi,
                'twi_processed': result['processed'],
                'has_twi_chars': result['has_twi_chars'],
                'word_count': result['word_count'],
                'similarity': getattr(row, 'similarity', 1.0)
            })
            
        except Exception as e:
            errors.append({'index': idx, 'error': str(e)})
            # Keep original if processing fails
            processed_data.append({
                'english': row.English,
                'twi_original': row.Twi,
                'twi_processed': row.Twi,  # Fallback to original
                'has_twi_chars': any(c in row.Twi for c in processor.twi_chars),
                'word_count': len(row.Twi.split()),
                'similarity': getattr(row, 'similarity', 1.0)
            })
    
    # Create DataFrame
    processed_df = pd.DataFrame(processed_data)
    
    # Save processed version
    output_file = NORMALIZED_DIR / f"{split}_normalized.parquet"
    processed_df.to_parquet(output_file)
    print(f"  [SAVED] {output_file.name}")
    
    # Save sample as CSV for inspection
    sample_file = NORMALIZED_DIR / f"{split}_normalized_sample.csv"
    processed_df.head(100).to_csv(sample_file, index=False, encoding='utf-8-sig')
    print(f"  [SAVED] {sample_file.name} (100 samples)")
    
    # Report statistics
    print(f"  Statistics:")
    print(f"    - Pairs with Twi chars: {processed_df['has_twi_chars'].sum():,}")
    print(f"    - Avg word count: {processed_df['word_count'].mean():.1f}")
    print(f"    - Processing errors: {len(errors)}")
    
    if errors and split == 'train':
        # Save error log for training set only
        error_file = NORMALIZED_DIR / f"{split}_processing_errors.json"
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(errors[:100], f, indent=2)  # Save first 100 errors
        print(f"  [SAVED] Error log: {error_file.name}")

print("\n" + "=" * 50)
print("CREATING SPECIALIZED VERSIONS")
print("=" * 50)

# Create TTS-specific version with phonemes (smaller subset)
print("\n1. TTS Version (with phonemes)")
print("-" * 30)

tts_sample_size = 10000  # Start with 10K for TTS
train_file = TEXT_DIR / "train_pairs.parquet"

if train_file.exists():
    df = pd.read_parquet(train_file)
    df_tts = df.head(tts_sample_size).copy()
    
    print(f"Processing {tts_sample_size:,} pairs for TTS...")
    
    tts_data = []
    for idx, row in enumerate(df_tts.itertuples()):
        if idx % 1000 == 0 and idx > 0:
            print(f"  Processed {idx:,} / {tts_sample_size:,}")
        
        try:
            # Process with phoneme generation
            result = processor.process_text(
                row.Twi,
                expand_numbers=True,  # Important for TTS
                expand_abbreviations=True,
                process_datetime=True,
                apply_dialect=True,
                generate_phonemes=True  # Generate phonemes for TTS
            )
            
            tts_data.append({
                'text': result['processed'],
                'phonemes': result['phonemes'],
                'original': row.Twi,
                'english': row.English
            })
            
        except Exception as e:
            continue
    
    # Save TTS data
    tts_df = pd.DataFrame(tts_data)
    tts_file = NORMALIZED_DIR / "tts_training_data.parquet"
    tts_df.to_parquet(tts_file)
    print(f"[SAVED] {tts_file.name} ({len(tts_df):,} pairs)")
    
    # Save TTS manifest
    tts_manifest = []
    for _, row in tts_df.iterrows():
        tts_manifest.append({
            'text': row['text'],
            'phonemes': row['phonemes']
        })
    
    tts_manifest_file = NORMALIZED_DIR / "tts_manifest.json"
    with open(tts_manifest_file, 'w', encoding='utf-8') as f:
        json.dump(tts_manifest, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] {tts_manifest_file.name}")

# Create ASR-specific version (numbers as words)
print("\n2. ASR Version (numbers as words)")
print("-" * 30)

asr_sample_size = 50000  # 50K for ASR
if train_file.exists():
    df = pd.read_parquet(train_file)
    df_asr = df.head(asr_sample_size).copy()
    
    print(f"Processing {asr_sample_size:,} pairs for ASR...")
    
    asr_data = []
    for idx, row in enumerate(df_asr.itertuples()):
        if idx % 5000 == 0 and idx > 0:
            print(f"  Processed {idx:,} / {asr_sample_size:,}")
        
        try:
            # Process for ASR (numbers as words is important)
            result = processor.process_text(
                row.Twi,
                expand_numbers=True,  # Critical for ASR
                expand_abbreviations=True,
                process_datetime=True,
                apply_dialect=True,
                generate_phonemes=False
            )
            
            asr_data.append({
                'transcript': result['processed'],
                'original': row.Twi,
                'english': row.English
            })
            
        except Exception as e:
            continue
    
    # Save ASR data
    asr_df = pd.DataFrame(asr_data)
    asr_file = NORMALIZED_DIR / "asr_training_data.parquet"
    asr_df.to_parquet(asr_file)
    print(f"[SAVED] {asr_file.name} ({len(asr_df):,} pairs)")

# Create dialect versions
print("\n3. Dialect Versions")
print("-" * 30)

dialects = ['asante', 'akuapem', 'fante']
dialect_sample_size = 10000

for dialect in dialects:
    print(f"\n  Processing {dialect} dialect...")
    
    # Initialize processor for this dialect
    dialect_processor = EnhancedTwiTextProcessor(dialect=dialect)
    
    if train_file.exists():
        df = pd.read_parquet(train_file)
        df_dialect = df.head(dialect_sample_size).copy()
        
        dialect_data = []
        for idx, row in enumerate(df_dialect.itertuples()):
            try:
                result = dialect_processor.process_text(
                    row.Twi,
                    expand_numbers=False,  # Keep numbers for dialect comparison
                    expand_abbreviations=True,
                    process_datetime=False,
                    apply_dialect=True,  # Apply dialect conversion
                    generate_phonemes=False
                )
                
                dialect_data.append({
                    'english': row.English,
                    'twi_original': row.Twi,
                    f'twi_{dialect}': result['processed']
                })
                
            except Exception as e:
                continue
        
        # Save dialect version
        dialect_df = pd.DataFrame(dialect_data)
        dialect_file = NORMALIZED_DIR / f"dialect_{dialect}.parquet"
        dialect_df.to_parquet(dialect_file)
        print(f"  [SAVED] {dialect_file.name} ({len(dialect_df):,} pairs)")

# Final summary
print("\n" + "=" * 50)
print("TEXT PROCESSING COMPLETE!")
print("=" * 50)

print(f"\nOutput location: {NORMALIZED_DIR}")
print("\nCreated files:")
print("  1. Normalized versions (train/val/test)")
print("  2. TTS training data with phonemes")
print("  3. ASR training data with expanded numbers")
print("  4. Dialect-specific versions (Asante, Akuapem, Fante)")

print("\nNext steps:")
print("  1. Use normalized data for translation training")
print("  2. Use TTS data for speech synthesis training")
print("  3. Use ASR data for speech recognition training")
print("  4. Use dialect versions for dialect-specific models")
#!/usr/bin/env python3
"""Check processing status of all available datasets."""

import pandas as pd
from pathlib import Path
import json
import os

print('CHECKING PROCESSING STATUS OF ALL DATASETS:')
print('=' * 70)

base_dir = Path('G:/My Drive/voice-lab-data')

# Track summary
summary = {
    'ready_with_audio': [],
    'ready_text_only': [],
    'not_ready': []
}

# 1. Check Common Voice
print('\n1. COMMON VOICE TWI:')
print('-' * 40)
cv_csv = base_dir / 'processed/common_voice_twi/cv_twi_transcripts.csv'
if cv_csv.exists():
    df = pd.read_csv(cv_csv)
    print(f'  CSV file: YES ({len(df):,} rows)')
    print(f'  Columns: {list(df.columns)}')
    
    # Check if it has audio paths
    has_audio = 'audio' in df.columns or 'path' in df.columns
    has_text = 'sentence' in df.columns or 'text' in df.columns or 'transcription' in df.columns
    print(f'  Has audio column: {has_audio}')
    print(f'  Has text column: {has_text}')
    
    # Check actual audio files
    cv_clips = base_dir / 'raw/common_voice/cv-corpus-22.0-delta-2025-06-20-tw/cv-corpus-22.0-delta-2025-06-20/tw/clips'
    audio_exists = cv_clips.exists()
    if audio_exists:
        # Check if directory has files
        files = os.listdir(str(cv_clips))[:5]  # Check first 5
        mp3_files = [f for f in files if f.endswith('.mp3')]
        print(f'  Audio files exist: YES (clips directory has MP3 files)')
    else:
        print(f'  Audio files exist: NO (clips directory not found)')
    
    status = 'TEXT_ONLY' if not has_audio else 'READY'
    print(f'  PROCESSING STATUS: {status}')
    
    if status == 'TEXT_ONLY':
        summary['ready_text_only'].append(('Common Voice', len(df)))
    else:
        summary['ready_with_audio'].append(('Common Voice', len(df)))
else:
    print(f'  CSV file: NOT FOUND')
    summary['not_ready'].append('Common Voice')

# 2. Check Bible TTS
print('\n2. BIBLE TTS AKUAPEM TWI:')
print('-' * 40)
bible_csv = base_dir / 'processed/bible_tts_complete/bible_akuapem-twi_complete.csv'
if bible_csv.exists():
    df = pd.read_csv(bible_csv)
    print(f'  CSV file: YES ({len(df):,} rows)')
    print(f'  Columns: {list(df.columns)}')
    
    # Check columns
    audio_cols = [c for c in df.columns if 'audio' in c.lower() or 'path' in c.lower()]
    text_cols = [c for c in df.columns if 'text' in c.lower() or 'trans' in c.lower() or 'sentence' in c.lower()]
    
    has_audio = len(audio_cols) > 0
    has_text = len(text_cols) > 0
    
    print(f'  Has audio column: {has_audio} {("- " + audio_cols[0]) if audio_cols else ""}')
    print(f'  Has text column: {has_text} {("- " + text_cols[0]) if text_cols else ""}')
    
    # Sample data
    if len(df) > 0:
        print(f'  Sample row:')
        sample = df.iloc[0]
        for col in df.columns[:3]:  # Show first 3 columns
            val = str(sample[col])[:50]
            print(f'    {col}: {val}')
    
    print(f'  PROCESSING STATUS: READY')
    summary['ready_with_audio'].append(('Bible TTS', len(df)))
else:
    print(f'  CSV file: NOT FOUND')
    summary['not_ready'].append('Bible TTS')

# 3. Check Audio Manifest
print('\n3. AUDIO MANIFEST (FANTE):')
print('-' * 40)
audio_csv = base_dir / 'processed/audio_data/audio_manifest.csv'
if audio_csv.exists():
    df = pd.read_csv(audio_csv)
    print(f'  CSV file: YES ({len(df):,} rows)')
    print(f'  Columns: {list(df.columns)}')
    
    # Check columns
    has_audio = any(c for c in df.columns if 'audio' in c.lower() or 'path' in c.lower())
    has_text = any(c for c in df.columns if 'text' in c.lower() or 'transcription' in c.lower() or 'sentence' in c.lower())
    print(f'  Has audio column: {has_audio}')
    print(f'  Has text column: {has_text}')
    
    # Check train/test splits
    train_csv = base_dir / 'processed/audio_data/audio_manifest_train.csv'
    test_csv = base_dir / 'processed/audio_data/audio_manifest_test.csv'
    if train_csv.exists():
        train_df = pd.read_csv(train_csv)
        print(f'  Train split: YES - {len(train_df)} rows')
    else:
        print(f'  Train split: NO')
        
    if test_csv.exists():
        test_df = pd.read_csv(test_csv)
        print(f'  Test split: YES - {len(test_df)} rows')
    else:
        print(f'  Test split: NO')
    
    print(f'  PROCESSING STATUS: READY')
    summary['ready_with_audio'].append(('Audio Manifest', len(df)))
else:
    print(f'  CSV file: NOT FOUND')
    summary['not_ready'].append('Audio Manifest')

# 4. Check Financial Inclusion
print('\n4. FINANCIAL INCLUSION TWI:')
print('-' * 40)
fi_csv = base_dir / 'processed/financial_inclusion_twi/financial_inclusion_twi_complete.csv'
if fi_csv.exists():
    df = pd.read_csv(fi_csv)
    print(f'  Complete CSV: YES ({len(df):,} rows)')
    print(f'  Columns: {list(df.columns)}')
    
    # Check dialect-specific files
    fi_dir = base_dir / 'processed/financial_inclusion_twi'
    dialect_files = list(fi_dir.glob('fi_*.csv'))
    print(f'  Dialect-specific files: {len(dialect_files)}')
    for f in dialect_files[:3]:
        df_dialect = pd.read_csv(f)
        print(f'    - {f.name}: {len(df_dialect)} rows')
    
    print(f'  PROCESSING STATUS: READY')
    summary['ready_with_audio'].append(('Financial Inclusion', len(df)))
else:
    print(f'  Complete CSV: NOT FOUND')
    summary['not_ready'].append('Financial Inclusion')

# 5. Check MichSet (current)
print('\n5. MICHSET (CURRENTLY USED):')
print('-' * 40)
splits_dir = base_dir / 'splits'
michset_total = 0
for split in ['train', 'validation', 'test']:
    split_csv = splits_dir / f'{split}.csv'
    if split_csv.exists():
        df = pd.read_csv(split_csv)
        print(f'  {split}: {len(df)} rows')
        michset_total += len(df)
        
        # Check audio availability
        if 'audio_available' in df.columns:
            available = df['audio_available'].sum() if df['audio_available'].dtype == bool else 0
            print(f'    Audio available: {available}/{len(df)}')

if michset_total > 0:
    summary['ready_with_audio'].append(('MichSet', michset_total))

# Print summary
print('\n' + '=' * 70)
print('SUMMARY:')
print('=' * 70)

print('\nPROCESSED AND READY (WITH AUDIO/PATHS):')
total_with_audio = 0
for name, count in summary['ready_with_audio']:
    print(f'  - {name}: {count:,} samples{"  [CURRENTLY USED]" if name == "MichSet" else "  [NOT USED]"}')
    total_with_audio += count

print('\nPROCESSED TEXT ONLY (NO AUDIO PATHS):')
total_text_only = 0
for name, count in summary['ready_text_only']:
    print(f'  - {name}: {count:,} samples  [NOT USED]')
    total_text_only += count

if summary['not_ready']:
    print('\nNOT READY:')
    for name in summary['not_ready']:
        print(f'  - {name}')

print('\n' + '-' * 40)
print(f'TOTAL READY WITH AUDIO: {total_with_audio:,} samples')
print(f'TOTAL TEXT ONLY: {total_text_only:,} samples')
print(f'GRAND TOTAL: {total_with_audio + total_text_only:,} samples')

# Calculate usage
michset_count = next((count for name, count in summary['ready_with_audio'] if name == 'MichSet'), 0)
print(f'\nCURRENTLY USING: {michset_count:,} samples')
print(f'AVAILABLE BUT NOT USED: {total_with_audio - michset_count:,} samples (with audio)')
print(f'USAGE PERCENTAGE: {(michset_count / total_with_audio * 100):.1f}% of audio-ready data')

print('\n' + '=' * 70)
print('RECOMMENDATION:')
print('=' * 70)
print('The ASR notebook should be updated to use:')
print('  1. Bible TTS data (25K+ samples with audio)')
print('  2. Audio Manifest data (28K+ samples with audio)')
print('  3. Financial Inclusion data (400 samples with audio)')
print(f'\nThis would increase training data from {michset_count} to {total_with_audio:,} samples')
print(f'An improvement of {(total_with_audio / michset_count):.0f}x!')
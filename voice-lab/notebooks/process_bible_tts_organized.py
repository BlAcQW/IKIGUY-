#!/usr/bin/env python
"""
Process organized Bible TTS data (already split into train/dev/test)
Create manifests for TTS training
"""

import pandas as pd
from pathlib import Path
import json
import os

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "bibletts"
PROCESSED_DIR = BASE_DIR / "processed"
BIBLE_DIR = PROCESSED_DIR / "bible_tts_data"
BIBLE_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING ORGANIZED BIBLE TTS DATA")
print("=" * 50)

# Bible book names mapping
BIBLE_BOOKS = {
    'GEN': 'Genesis', 'EXO': 'Exodus', 'LEV': 'Leviticus', 'NUM': 'Numbers',
    'DEU': 'Deuteronomy', 'JOS': 'Joshua', 'JDG': 'Judges', 'RUT': 'Ruth',
    '1SA': '1 Samuel', '2SA': '2 Samuel', '1KI': '1 Kings', '2KI': '2 Kings',
    '1CH': '1 Chronicles', '2CH': '2 Chronicles', 'EZR': 'Ezra', 'NEH': 'Nehemiah',
    'EST': 'Esther', 'JOB': 'Job', 'PSA': 'Psalms', 'PRO': 'Proverbs',
    'ECC': 'Ecclesiastes', 'SNG': 'Song of Solomon', 'ISA': 'Isaiah', 'JER': 'Jeremiah',
    'LAM': 'Lamentations', 'EZK': 'Ezekiel', 'DAN': 'Daniel', 'HOS': 'Hosea',
    'JOL': 'Joel', 'AMO': 'Amos', 'OBA': 'Obadiah', 'JON': 'Jonah',
    'MIC': 'Micah', 'NAM': 'Nahum', 'HAB': 'Habakkuk', 'ZEP': 'Zephaniah',
    'HAG': 'Haggai', 'ZEC': 'Zechariah', 'MAL': 'Malachi',
    # New Testament
    'MAT': 'Matthew', 'MRK': 'Mark', 'LUK': 'Luke', 'JHN': 'John',
    'ACT': 'Acts', 'ROM': 'Romans', '1CO': '1 Corinthians', '2CO': '2 Corinthians',
    'GAL': 'Galatians', 'EPH': 'Ephesians', 'PHP': 'Philippians', 'COL': 'Colossians',
    '1TH': '1 Thessalonians', '2TH': '2 Thessalonians', '1TI': '1 Timothy', '2TI': '2 Timothy',
    'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews', 'JAS': 'James',
    '1PE': '1 Peter', '2PE': '2 Peter', '1JN': '1 John', '2JN': '2 John',
    '3JN': '3 John', 'JUD': 'Jude', 'REV': 'Revelation'
}

all_data = []
statistics = {}

for dialect in ['akuapem-twi', 'asante-twi']:
    print(f"\n{dialect.upper()}")
    print("-" * 30)
    
    dialect_dir = RAW_DIR / dialect
    if not dialect_dir.exists():
        print(f"  [SKIP] Not found")
        continue
    
    dialect_stats = {
        'train': 0,
        'dev': 0,
        'test': 0,
        'total_audio': 0,
        'total_text': 0,
        'paired': 0,
        'books': set()
    }
    
    # Process each split
    for split in ['train', 'dev', 'test']:
        split_dir = dialect_dir / split
        if not split_dir.exists():
            print(f"  [SKIP] {split} directory not found")
            continue
        
        print(f"\n  Processing {split} split...")
        
        # Get all book directories
        book_dirs = [d for d in split_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        print(f"    Found {len(book_dirs)} books")
        
        split_data = []
        
        # Process each book (sample first few files from each)
        for book_dir in book_dirs[:10]:  # Process first 10 books for testing
            book_code = book_dir.name
            book_name = BIBLE_BOOKS.get(book_code, book_code)
            dialect_stats['books'].add(book_name)
            
            # Find audio files in this book
            audio_files = list(book_dir.glob('*.wav'))[:50]  # Sample 50 files per book
            
            for audio_file in audio_files:
                # Check for corresponding text file
                txt_file = audio_file.with_suffix('.txt')
                has_text = txt_file.exists()
                transcript = None
                
                if has_text:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            transcript = f.read().strip()
                        dialect_stats['paired'] += 1
                    except Exception as e:
                        print(f"      Error reading {txt_file.name}: {str(e)[:30]}")
                
                # Parse filename for chapter and verse
                # Typical format: GEN_001_001.wav (book_chapter_verse)
                parts = audio_file.stem.split('_')
                chapter = parts[1] if len(parts) > 1 else '001'
                verse = parts[2] if len(parts) > 2 else '001'
                
                entry = {
                    'audio_path': str(audio_file),
                    'text_path': str(txt_file) if has_text else None,
                    'transcript': transcript,
                    'dialect': dialect.replace('-', '_'),
                    'split': split,
                    'book_code': book_code,
                    'book_name': book_name,
                    'chapter': chapter,
                    'verse': verse,
                    'has_text': has_text,
                    'filename': audio_file.name,
                    'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
                }
                
                split_data.append(entry)
                all_data.append(entry)
            
            dialect_stats['total_audio'] += len(audio_files)
        
        dialect_stats[split] = len(split_data)
        
        print(f"    Processed {len(split_data)} files from {split}")
        
        # Save split-specific manifest
        if split_data:
            split_df = pd.DataFrame(split_data)
            split_file = BIBLE_DIR / f"bible_tts_{dialect}_{split}.csv"
            split_df.to_csv(split_file, index=False)
            print(f"    [SAVED] {split_file.name}")
    
    # Print dialect statistics
    print(f"\n  {dialect} Statistics:")
    print(f"    Total audio: {dialect_stats['total_audio']}")
    print(f"    Paired with text: {dialect_stats['paired']}")
    print(f"    Books covered: {len(dialect_stats['books'])}")
    print(f"    Train/Dev/Test: {dialect_stats['train']}/{dialect_stats['dev']}/{dialect_stats['test']}")
    
    statistics[dialect] = dialect_stats

# Save complete manifest
print("\n" + "=" * 50)
print("SAVING COMPLETE MANIFESTS")
print("=" * 50)

if all_data:
    # Full dataset
    full_df = pd.DataFrame(all_data)
    full_file = BIBLE_DIR / "bible_tts_complete.csv"
    full_df.to_csv(full_file, index=False)
    print(f"\n[SAVED] {full_file.name} ({len(full_df)} entries)")
    
    # TTS training manifest (only paired audio-text)
    paired_df = full_df[full_df['has_text'] == True]
    if not paired_df.empty:
        # Create JSON manifest for TTS training
        tts_manifests = {}
        
        for split in ['train', 'dev', 'test']:
            split_data = paired_df[paired_df['split'] == split]
            if not split_data.empty:
                manifest = []
                for _, row in split_data.iterrows():
                    if row['transcript']:
                        manifest.append({
                            'audio_filepath': row['audio_path'],
                            'text': row['transcript'],
                            'duration': -1,  # Will be calculated
                            'dialect': row['dialect'],
                            'book': row['book_name'],
                            'reference': f"{row['book_code']}_{row['chapter']}:{row['verse']}"
                        })
                
                tts_manifests[split] = manifest
                
                # Save split manifest
                manifest_file = BIBLE_DIR / f"tts_{split}_manifest.json"
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2)
                print(f"[SAVED] {manifest_file.name} ({len(manifest)} entries)")
    
    # Summary statistics
    stats_summary = {
        'total_entries': len(full_df),
        'paired_entries': len(paired_df) if not paired_df.empty else 0,
        'unpaired_entries': len(full_df[full_df['has_text'] == False]),
        'dialects': full_df['dialect'].value_counts().to_dict(),
        'splits': full_df['split'].value_counts().to_dict(),
        'books': len(full_df['book_name'].unique()),
        'total_size_gb': full_df['file_size_mb'].sum() / 1024,
        'average_file_size_mb': full_df['file_size_mb'].mean()
    }
    
    # Add per-dialect stats
    for dialect, dstats in statistics.items():
        stats_summary[f'{dialect}_books'] = list(dstats['books'])[:10]  # First 10 books
    
    stats_file = BIBLE_DIR / "bible_tts_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {stats_file.name}")
    
    # Print final summary
    print("\n" + "=" * 50)
    print("BIBLE TTS PROCESSING COMPLETE!")
    print("=" * 50)
    
    print(f"\nTotal entries processed: {stats_summary['total_entries']:,}")
    print(f"Paired (audio+text): {stats_summary['paired_entries']:,}")
    print(f"Audio only: {stats_summary['unpaired_entries']:,}")
    print(f"Total size: {stats_summary['total_size_gb']:.2f} GB")
    print(f"Books covered: {stats_summary['books']}")
    
    print("\nBy Split:")
    for split, count in stats_summary['splits'].items():
        print(f"  {split}: {count:,}")
    
    print("\nBy Dialect:")
    for dialect, count in stats_summary['dialects'].items():
        print(f"  {dialect}: {count:,}")
    
    # Show sample entries
    if not paired_df.empty:
        print("\nSample paired entries:")
        for idx, row in paired_df.head(3).iterrows():
            print(f"\n  {row['book_name']} {row['chapter']}:{row['verse']}")
            print(f"  Audio: {Path(row['audio_path']).name}")
            if row['transcript']:
                print(f"  Text: {row['transcript'][:80]}...")

else:
    print("\n[WARNING] No data processed")

print(f"\nOutput location: {BIBLE_DIR}")
print("\nThe Bible TTS data is now organized and ready for:")
print("  1. TTS model training (VITS, Tacotron2, etc.)")
print("  2. Voice cloning experiments")
print("  3. High-quality Twi speech synthesis")
print("  4. Prosody and intonation studies")
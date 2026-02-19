#!/usr/bin/env python
"""
Fully process Bible TTS dataset - create complete manifests
Process all ~93K FLAC files with their text transcripts
"""

import pandas as pd
from pathlib import Path
import json
from collections import defaultdict

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "bibletts"
PROCESSED_DIR = BASE_DIR / "processed"
BIBLE_OUTPUT_DIR = PROCESSED_DIR / "bible_tts_complete"
BIBLE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("FULLY PROCESSING BIBLE TTS DATASET")
print("=" * 60)

# Bible book mapping
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
    'MAT': 'Matthew', 'MRK': 'Mark', 'LUK': 'Luke', 'JHN': 'John',
    'ACT': 'Acts', 'ROM': 'Romans', '1CO': '1 Corinthians', '2CO': '2 Corinthians',
    'GAL': 'Galatians', 'EPH': 'Ephesians', 'PHP': 'Philippians', 'COL': 'Colossians',
    '1TH': '1 Thessalonians', '2TH': '2 Thessalonians', '1TI': '1 Timothy', '2TI': '2 Timothy',
    'TIT': 'Titus', 'PHM': 'Philemon', 'HEB': 'Hebrews', 'JAS': 'James',
    '1PE': '1 Peter', '2PE': '2 Peter', '1JN': '1 John', '2JN': '2 John',
    '3JN': '3 John', 'JUD': 'Jude', 'REV': 'Revelation'
}

# Process each dialect
dialects = ['akuapem-twi', 'asante-twi']
all_manifests = []
statistics = defaultdict(lambda: defaultdict(int))

for dialect in dialects:
    print(f"\n{dialect.upper()}")
    print("-" * 40)
    
    dialect_dir = RAW_DIR / dialect
    if not dialect_dir.exists():
        print(f"  [SKIP] Not found: {dialect_dir}")
        continue
    
    dialect_manifests = []
    
    # Process each split
    for split in ['train', 'dev', 'test']:
        split_dir = dialect_dir / split
        if not split_dir.exists():
            print(f"  [SKIP] {split} not found")
            continue
        
        print(f"\n  Processing {split} split...")
        
        # Get all book directories
        book_dirs = [d for d in split_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        print(f"    Books found: {len(book_dirs)}")
        
        split_manifest = []
        paired_count = 0
        unpaired_count = 0
        
        # Process each book
        for book_dir in book_dirs:
            book_code = book_dir.name
            book_name = BIBLE_BOOKS.get(book_code, book_code)
            
            # Find all FLAC files
            flac_files = list(book_dir.glob("*.flac"))
            
            if not flac_files:
                continue
            
            # Process each audio file
            for audio_file in flac_files:
                # Check for corresponding text file
                txt_file = audio_file.with_suffix('.txt')
                has_text = txt_file.exists()
                
                transcript = None
                if has_text:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            transcript = f.read().strip()
                        paired_count += 1
                    except Exception as e:
                        print(f"      Error reading {txt_file.name}: {str(e)[:30]}")
                        unpaired_count += 1
                else:
                    unpaired_count += 1
                
                # Parse filename for chapter and verse
                # Format: GEN_002_Verse_001.flac
                parts = audio_file.stem.split('_')
                chapter = parts[1] if len(parts) > 1 else '001'
                verse = parts[3] if len(parts) > 3 else '001'
                
                # Create manifest entry
                entry = {
                    'audio_filepath': str(audio_file),
                    'audio_filename': audio_file.name,
                    'text': transcript if transcript else "",
                    'has_text': has_text,
                    'dialect': dialect.replace('-', '_'),
                    'split': split,
                    'book_code': book_code,
                    'book_name': book_name,
                    'chapter': int(chapter) if chapter.isdigit() else 0,
                    'verse': int(verse) if verse.isdigit() else 0,
                    'reference': f"{book_code}_{chapter}:{verse}",
                    'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
                }
                
                split_manifest.append(entry)
                dialect_manifests.append(entry)
                all_manifests.append(entry)
            
            # Update statistics
            statistics[dialect][f'{split}_files'] += len(flac_files)
            statistics[dialect][f'{split}_books'] += 1
        
        statistics[dialect][f'{split}_paired'] = paired_count
        statistics[dialect][f'{split}_unpaired'] = unpaired_count
        
        print(f"    Files processed: {len(split_manifest):,}")
        print(f"    Paired (with text): {paired_count:,}")
        print(f"    Unpaired (audio only): {unpaired_count:,}")
        
        # Save split manifest
        if split_manifest:
            split_df = pd.DataFrame(split_manifest)
            split_file = BIBLE_OUTPUT_DIR / f"bible_{dialect}_{split}.csv"
            split_df.to_csv(split_file, index=False)
            print(f"    [SAVED] {split_file.name}")
    
    # Save dialect-specific complete manifest
    if dialect_manifests:
        dialect_df = pd.DataFrame(dialect_manifests)
        dialect_file = BIBLE_OUTPUT_DIR / f"bible_{dialect}_complete.csv"
        dialect_df.to_csv(dialect_file, index=False)
        print(f"  [SAVED] Complete manifest: {dialect_file.name} ({len(dialect_df):,} files)")

# Save combined manifest
print("\n" + "=" * 60)
print("SAVING COMPLETE MANIFESTS")
print("=" * 60)

if all_manifests:
    # Full manifest
    full_df = pd.DataFrame(all_manifests)
    full_file = BIBLE_OUTPUT_DIR / "bible_tts_all.csv"
    full_df.to_csv(full_file, index=False)
    print(f"\n[SAVED] {full_file.name} ({len(full_df):,} entries)")
    
    # TTS-ready manifest (only files with text)
    tts_ready = full_df[full_df['has_text'] == True]
    if not tts_ready.empty:
        # Create JSON manifest for TTS training
        for split in ['train', 'dev', 'test']:
            split_data = tts_ready[tts_ready['split'] == split]
            
            if not split_data.empty:
                tts_manifest = []
                for _, row in split_data.iterrows():
                    tts_manifest.append({
                        'audio_filepath': row['audio_filepath'],
                        'text': row['text'],
                        'duration': -1,  # Will be calculated during training
                        'dialect': row['dialect'],
                        'reference': row['reference']
                    })
                
                # Save JSON manifest
                json_file = BIBLE_OUTPUT_DIR / f"tts_{split}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(tts_manifest, f, ensure_ascii=False, indent=2)
                print(f"[SAVED] {json_file.name} ({len(tts_manifest):,} entries)")
    
    # Statistics summary
    stats_summary = {
        'total_files': len(full_df),
        'files_with_text': len(tts_ready) if not tts_ready.empty else 0,
        'files_without_text': len(full_df[full_df['has_text'] == False]),
        'total_size_gb': full_df['file_size_mb'].sum() / 1024,
        'dialects': full_df['dialect'].value_counts().to_dict(),
        'splits': full_df['split'].value_counts().to_dict(),
        'books': len(full_df['book_name'].unique()),
        'chapters': len(full_df.groupby(['book_code', 'chapter']).size()),
        'per_dialect_stats': dict(statistics)
    }
    
    # Add book distribution
    book_counts = full_df['book_name'].value_counts().head(10).to_dict()
    stats_summary['top_10_books'] = book_counts
    
    stats_file = BIBLE_OUTPUT_DIR / "bible_tts_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print(f"\n[SAVED] {stats_file.name}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("BIBLE TTS PROCESSING COMPLETE!")
    print("=" * 60)
    
    print(f"\nTotal files processed: {stats_summary['total_files']:,}")
    print(f"Files with text: {stats_summary['files_with_text']:,}")
    print(f"Files without text: {stats_summary['files_without_text']:,}")
    print(f"Total size: {stats_summary['total_size_gb']:.2f} GB")
    print(f"Books covered: {stats_summary['books']}")
    print(f"Chapters: {stats_summary['chapters']}")
    
    print("\nBy Split:")
    for split, count in stats_summary['splits'].items():
        percentage = (count / stats_summary['total_files']) * 100
        print(f"  {split}: {count:,} ({percentage:.1f}%)")
    
    print("\nBy Dialect:")
    for dialect, count in stats_summary['dialects'].items():
        print(f"  {dialect}: {count:,}")
    
    print("\nTop 5 Books:")
    for book, count in list(book_counts.items())[:5]:
        print(f"  {book}: {count:,} verses")
    
    # Sample entries
    print("\nSample entries with text:")
    for idx, row in tts_ready.head(3).iterrows():
        print(f"\n  {row['reference']} ({row['dialect']})")
        print(f"  Audio: {Path(row['audio_filepath']).name}")
        if row['text']:
            print(f"  Text: {row['text'][:80]}...")

else:
    print("\n[WARNING] No files processed")

print(f"\nOutput location: {BIBLE_OUTPUT_DIR}")
print("\nThe Bible TTS dataset is now fully processed and ready for:")
print("  1. High-quality TTS model training")
print("  2. Voice cloning experiments")
print("  3. Prosody and intonation studies")
print("  4. Biblical Twi language models")
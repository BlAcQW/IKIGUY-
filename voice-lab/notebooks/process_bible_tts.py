#!/usr/bin/env python
"""
Process Bible TTS audio files (Akuapem and Asante Twi)
Organize and create training manifests for TTS models
"""

import pandas as pd
from pathlib import Path
import json
import os
from collections import defaultdict

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "bibletts"
PROCESSED_DIR = BASE_DIR / "processed"
BIBLE_DIR = PROCESSED_DIR / "bible_tts_data"
BIBLE_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING BIBLE TTS DATA")
print("=" * 50)

# Process each dialect
dialects = {
    'akuapem-twi': {
        'name': 'Akuapem Twi',
        'code': 'ak-tw',
        'dir': RAW_DIR / 'akuapem-twi'
    },
    'asante-twi': {
        'name': 'Asante Twi', 
        'code': 'as-tw',
        'dir': RAW_DIR / 'asante-twi'
    }
}

all_manifests = []
total_audio_files = 0
total_text_files = 0

for dialect_key, dialect_info in dialects.items():
    print(f"\n{dialect_info['name'].upper()}")
    print("-" * 30)
    
    dialect_dir = dialect_info['dir']
    if not dialect_dir.exists():
        print(f"  [SKIP] Directory not found: {dialect_dir}")
        continue
    
    # Find all audio files
    audio_extensions = ['.wav', '.mp3', '.ogg', '.flac']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(list(dialect_dir.rglob(f'*{ext}')))
    
    print(f"  Found {len(audio_files):,} audio files")
    
    # Find text/transcript files
    text_files = list(dialect_dir.rglob('*.txt'))
    print(f"  Found {len(text_files):,} text files")
    
    # Check for metadata files
    metadata_files = list(dialect_dir.rglob('*.csv')) + list(dialect_dir.rglob('*.tsv'))
    print(f"  Found {len(metadata_files)} metadata files")
    
    # Organize by book/chapter structure (Bible typically organized this way)
    books = defaultdict(lambda: defaultdict(list))
    
    for audio_file in audio_files[:1000]:  # Process first 1000 for testing
        # Parse path structure
        parts = audio_file.relative_to(dialect_dir).parts
        
        # Typical structure: book/chapter/verse.wav or similar
        if len(parts) >= 2:
            book = parts[0]
            chapter = parts[1] if len(parts) > 2 else 'all'
            books[book][chapter].append(audio_file)
        else:
            books['misc']['all'].append(audio_file)
    
    print(f"\n  Books found: {len(books)}")
    for book, chapters in list(books.items())[:5]:  # Show first 5 books
        total_files = sum(len(files) for files in chapters.values())
        print(f"    {book}: {len(chapters)} chapters, {total_files} files")
    
    # Look for corresponding text files
    audio_text_pairs = []
    orphan_audio = []
    
    for audio_file in audio_files[:1000]:  # Process subset
        # Try to find matching text file
        text_candidates = [
            audio_file.with_suffix('.txt'),
            audio_file.parent / f"{audio_file.stem}.txt",
            audio_file.parent / "text.txt",
            audio_file.parent / "transcript.txt"
        ]
        
        text_file = None
        transcript = None
        
        for candidate in text_candidates:
            if candidate.exists():
                text_file = candidate
                try:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        transcript = f.read().strip()
                    break
                except Exception as e:
                    print(f"    Error reading {text_file.name}: {str(e)[:50]}")
        
        # Create manifest entry
        entry = {
            'audio_path': str(audio_file),
            'audio_filename': audio_file.name,
            'dialect': dialect_info['name'],
            'dialect_code': dialect_info['code'],
            'book': audio_file.parent.parent.name if len(audio_file.parts) > 2 else 'unknown',
            'chapter': audio_file.parent.name if len(audio_file.parts) > 1 else 'unknown',
            'has_text': text_file is not None,
            'text_path': str(text_file) if text_file else None,
            'transcript': transcript,
            'file_size_mb': audio_file.stat().st_size / (1024 * 1024)
        }
        
        all_manifests.append(entry)
        
        if text_file:
            audio_text_pairs.append(entry)
        else:
            orphan_audio.append(entry)
    
    print(f"\n  Audio-text pairs: {len(audio_text_pairs)}")
    print(f"  Audio without text: {len(orphan_audio)}")
    
    total_audio_files += len(audio_files)
    total_text_files += len(text_files)
    
    # Save dialect-specific manifest
    dialect_manifest_df = pd.DataFrame([e for e in all_manifests if e['dialect'] == dialect_info['name']])
    dialect_file = BIBLE_DIR / f"bible_tts_{dialect_key}.csv"
    dialect_manifest_df.to_csv(dialect_file, index=False)
    print(f"\n  [SAVED] {dialect_file.name}")

# Save combined manifest
print("\n" + "=" * 50)
print("SAVING COMBINED MANIFESTS")
print("=" * 50)

if all_manifests:
    # Full manifest
    full_df = pd.DataFrame(all_manifests)
    full_file = BIBLE_DIR / "bible_tts_manifest_full.csv"
    full_df.to_csv(full_file, index=False)
    print(f"\n[SAVED] {full_file.name} ({len(full_df)} entries)")
    
    # Manifest with text only (for TTS training)
    with_text = full_df[full_df['has_text'] == True]
    if not with_text.empty:
        tts_file = BIBLE_DIR / "bible_tts_with_text.csv"
        with_text.to_csv(tts_file, index=False)
        print(f"[SAVED] {tts_file.name} ({len(with_text)} pairs)")
        
        # Create TTS training manifest
        tts_manifest = []
        for _, row in with_text.iterrows():
            if row['transcript']:
                tts_manifest.append({
                    'audio_filepath': row['audio_path'],
                    'text': row['transcript'],
                    'dialect': row['dialect'],
                    'duration': -1  # Will be calculated during training
                })
        
        tts_json_file = BIBLE_DIR / "tts_training_manifest.json"
        with open(tts_json_file, 'w', encoding='utf-8') as f:
            json.dump(tts_manifest, f, ensure_ascii=False, indent=2)
        print(f"[SAVED] {tts_json_file.name} ({len(tts_manifest)} entries)")
    
    # Statistics
    stats = {
        'total_audio_files': total_audio_files,
        'total_text_files': total_text_files,
        'processed_entries': len(all_manifests),
        'audio_with_text': len(with_text) if not with_text.empty else 0,
        'audio_without_text': len(full_df[full_df['has_text'] == False]),
        'dialects': full_df['dialect'].value_counts().to_dict(),
        'total_size_gb': full_df['file_size_mb'].sum() / 1024,
        'books': len(full_df['book'].unique()),
        'chapters': len(full_df.groupby(['book', 'chapter']).size())
    }
    
    stats_file = BIBLE_DIR / "bible_tts_statistics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"\n[SAVED] {stats_file.name}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("BIBLE TTS PROCESSING COMPLETE!")
    print("=" * 50)
    
    print("\nStatistics:")
    print(f"  Total audio files found: {total_audio_files:,}")
    print(f"  Total text files found: {total_text_files:,}")
    print(f"  Processed entries: {stats['processed_entries']:,}")
    print(f"  Audio with text: {stats['audio_with_text']:,}")
    print(f"  Audio without text: {stats['audio_without_text']:,}")
    print(f"  Total size: {stats['total_size_gb']:.2f} GB")
    print(f"  Books: {stats['books']}")
    print(f"  Chapters: {stats['chapters']}")
    
    print("\nBy Dialect:")
    for dialect, count in stats['dialects'].items():
        print(f"  {dialect}: {count:,} files")
    
    # Sample entries
    print("\nSample entries with text:")
    for idx, row in with_text.head(3).iterrows():
        print(f"\n  Audio: {Path(row['audio_path']).name}")
        if row['transcript']:
            print(f"  Text: {row['transcript'][:100]}...")

else:
    print("\n[WARNING] No files processed")

print(f"\nOutput location: {BIBLE_DIR}")
print("\nNext steps:")
print("  1. Review the manifests to check text alignment")
print("  2. Convert audio to consistent format (16kHz WAV)")
print("  3. Train TTS model with paired audio-text data")
print("  4. Use for high-quality Twi speech synthesis")
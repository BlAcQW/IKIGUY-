"""
Explore Common Voice Twi dataset structure
"""

import os
import pandas as pd
from pathlib import Path

# Path to Common Voice dataset
cv_path = Path(r"G:\My Drive\voice-lab-data\raw\common_voice\cv-corpus-22.0-delta-2025-06-20-tw\cv-corpus-22.0-delta-2025-06-20\tw")

print("=" * 60)
print("COMMON VOICE TWI DATASET EXPLORATION")
print("=" * 60)

# Check if path exists
if not cv_path.exists():
    print(f"Path not found: {cv_path}")
    exit(1)

print(f"\nDataset location: {cv_path}")

# List main files
print("\nMain files:")
for file in cv_path.iterdir():
    if file.is_file():
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name} ({size_mb:.2f} MB)")

# Check clips folder
clips_path = cv_path / "clips"
if clips_path.exists():
    # Count audio files
    mp3_files = list(clips_path.glob("*.mp3"))
    print(f"\nAudio files in clips/: {len(mp3_files)}")
    
    if mp3_files:
        # Show sample files
        print("\nSample audio files:")
        for file in mp3_files[:5]:
            size_kb = file.stat().st_size / 1024
            print(f"  - {file.name} ({size_kb:.1f} KB)")
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in mp3_files)
        print(f"\nTotal audio size: {total_size / (1024**3):.2f} GB")
else:
    print("\nWarning: No clips folder found")

# Load and analyze TSV files
print("\nDataset metadata:")

# Validated sentences
validated_path = cv_path / "validated_sentences.tsv"
if validated_path.exists():
    df_validated = pd.read_csv(validated_path, sep='\t', encoding='utf-8')
    print(f"\nValidated sentences:")
    print(f"  - Total: {len(df_validated):,}")
    print(f"  - Columns: {', '.join(df_validated.columns)}")
    
    # Check for clips usage
    if 'clips_count' in df_validated.columns:
        has_clips = df_validated[df_validated['clips_count'] > 0]
        print(f"  - Sentences with clips: {len(has_clips):,}")
        print(f"  - Average clips per sentence: {df_validated['clips_count'].mean():.2f}")
    
    # Show sample sentences
    print("\n  Sample validated sentences:")
    for idx, row in df_validated.head(3).iterrows():
        sentence = row['sentence'][:100] + "..." if len(row['sentence']) > 100 else row['sentence']
        try:
            print(f"    {idx+1}. {sentence}")
        except UnicodeEncodeError:
            print(f"    {idx+1}. [Contains Twi special characters]")

# Unvalidated sentences
unvalidated_path = cv_path / "unvalidated_sentences.tsv"
if unvalidated_path.exists():
    df_unvalidated = pd.read_csv(unvalidated_path, sep='\t', encoding='utf-8')
    print(f"\nUnvalidated sentences:")
    print(f"  - Total: {len(df_unvalidated):,}")

# Clip durations
durations_path = cv_path / "clip_durations.tsv"
if durations_path.exists():
    df_durations = pd.read_csv(durations_path, sep='\t')
    if len(df_durations) > 0:
        print(f"\nClip durations:")
        print(f"  - Total clips with duration: {len(df_durations):,}")
        print(f"  - Average duration: {df_durations['duration[ms]'].mean() / 1000:.2f} seconds")
        print(f"  - Total duration: {df_durations['duration[ms]'].sum() / (1000 * 60 * 60):.2f} hours")

# Reported sentences
reported_path = cv_path / "reported.tsv"
if reported_path.exists():
    df_reported = pd.read_csv(reported_path, sep='\t', encoding='utf-8')
    print(f"\nReported issues:")
    print(f"  - Total: {len(df_reported):,}")

# Check for any train/test/dev splits
for split in ['train', 'test', 'dev', 'validated', 'other']:
    split_file = cv_path / f"{split}.tsv"
    if split_file.exists():
        df_split = pd.read_csv(split_file, sep='\t', encoding='utf-8')
        print(f"\n{split.upper()} split:")
        print(f"  - Samples: {len(df_split):,}")
        print(f"  - Columns: {', '.join(df_split.columns)}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)

# Summary
print("\nSUMMARY:")
print(f"- Dataset version: Common Voice 22.0 Delta (2025-06-20)")
print(f"- Language: Twi (tw)")
print(f"- Validated sentences: {len(df_validated):,}")
print(f"- Audio clips: {len(mp3_files) if 'mp3_files' in locals() else 0}")

if len(mp3_files) == 0:
    print("\nWARNING: No MP3 files found in clips folder!")
    print("This appears to be a metadata-only download.")
    print("To get audio files, you need to:")
    print("1. Download the full Common Voice dataset")
    print("2. Or use the HuggingFace datasets library with audio=True")
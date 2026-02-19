#!/usr/bin/env python
"""
Process Common Voice Twi dataset
Extract and organize audio with transcripts
"""

import pandas as pd
from pathlib import Path
import json
import shutil

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "common_voice"
CV_DIR = RAW_DIR / "cv-corpus-22.0-delta-2025-06-20-tw" / "cv-corpus-22.0-delta-2025-06-20" / "tw"
PROCESSED_DIR = BASE_DIR / "processed"
CV_OUTPUT_DIR = PROCESSED_DIR / "common_voice_twi"
CV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING COMMON VOICE TWI DATASET")
print("=" * 60)

if not CV_DIR.exists():
    print(f"ERROR: Common Voice directory not found: {CV_DIR}")
    exit(1)

# List contents
print("\nChecking Common Voice structure...")
for item in CV_DIR.iterdir():
    if item.is_file():
        print(f"  File: {item.name}")
    elif item.is_dir():
        file_count = len(list(item.iterdir()))
        print(f"  Directory: {item.name} ({file_count} items)")

# Load metadata files
print("\n" + "-" * 60)
print("LOADING METADATA")
print("-" * 60)

# Load validated sentences
validated_file = CV_DIR / "validated_sentences.tsv"
if validated_file.exists():
    print(f"\nLoading validated sentences...")
    validated_df = pd.read_csv(validated_file, sep='\t')
    print(f"  Validated sentences: {len(validated_df):,}")
    print(f"  Columns: {validated_df.columns.tolist()}")
    
    # Show sample
    if len(validated_df) > 0:
        print("\n  Sample validated sentence:")
        for col in validated_df.columns:
            try:
                print(f"    {col}: {str(validated_df.iloc[0][col])[:50]}")
            except:
                print(f"    {col}: [Unicode display error]")
else:
    validated_df = pd.DataFrame()
    print("  No validated sentences file found")

# Load clip durations
durations_file = CV_DIR / "clip_durations.tsv"
if durations_file.exists():
    print(f"\nLoading clip durations...")
    durations_df = pd.read_csv(durations_file, sep='\t')
    print(f"  Clips with durations: {len(durations_df):,}")
    if len(durations_df) > 0:
        print(f"  Total duration: {durations_df['duration[ms]'].sum() / 1000 / 60:.1f} minutes")
else:
    durations_df = pd.DataFrame()

# Count audio clips
clips_dir = CV_DIR / "clips"
audio_files = []
if clips_dir.exists():
    print(f"\nScanning audio clips...")
    # Common Voice typically uses MP3
    audio_files = list(clips_dir.glob("*.mp3"))
    if not audio_files:
        audio_files = list(clips_dir.glob("*.wav"))
    if not audio_files:
        audio_files = list(clips_dir.glob("*.ogg"))
    
    print(f"  Audio files found: {len(audio_files):,}")
    
    if audio_files:
        # Check file sizes
        total_size = sum(f.stat().st_size for f in audio_files[:100]) / (1024 * 1024)
        print(f"  Sample size (100 files): {total_size:.1f} MB")

# Process and create manifests
print("\n" + "-" * 60)
print("CREATING TRAINING MANIFESTS")
print("-" * 60)

if not validated_df.empty and audio_files:
    # Match audio with transcripts
    print("\nMatching audio with transcripts...")
    
    manifest = []
    matched = 0
    unmatched = 0
    
    for audio_file in audio_files[:1000]:  # Process first 1000
        audio_name = audio_file.stem
        
        # Try to find in validated sentences
        # Common Voice usually has 'path' or 'filename' column
        match_found = False
        
        for col in ['path', 'filename', 'audio', 'clip']:
            if col in validated_df.columns:
                matches = validated_df[validated_df[col].str.contains(audio_name, na=False)]
                if not matches.empty:
                    # Get transcript
                    sentence_col = 'sentence' if 'sentence' in matches.columns else 'text'
                    if sentence_col in matches.columns:
                        transcript = matches.iloc[0][sentence_col]
                        
                        # Get duration if available
                        duration = -1
                        if not durations_df.empty and 'clip' in durations_df.columns:
                            dur_match = durations_df[durations_df['clip'].str.contains(audio_name, na=False)]
                            if not dur_match.empty and 'duration[ms]' in dur_match.columns:
                                duration = dur_match.iloc[0]['duration[ms]'] / 1000  # Convert to seconds
                        
                        manifest.append({
                            'audio_filepath': str(audio_file),
                            'audio_filename': audio_file.name,
                            'text': transcript,
                            'duration': duration,
                            'dataset': 'common_voice_twi'
                        })
                        matched += 1
                        match_found = True
                        break
                
                if match_found:
                    break
        
        if not match_found:
            unmatched += 1
    
    print(f"  Matched: {matched}")
    print(f"  Unmatched: {unmatched}")
    
    if manifest:
        # Save manifest
        manifest_df = pd.DataFrame(manifest)
        
        # Split into train/test
        test_size = int(len(manifest_df) * 0.1)
        test_df = manifest_df.iloc[:test_size]
        train_df = manifest_df.iloc[test_size:]
        
        # Save CSV manifests
        train_csv = CV_OUTPUT_DIR / "cv_twi_train.csv"
        train_df.to_csv(train_csv, index=False)
        print(f"\n[SAVED] {train_csv.name} ({len(train_df)} entries)")
        
        test_csv = CV_OUTPUT_DIR / "cv_twi_test.csv"
        test_df.to_csv(test_csv, index=False)
        print(f"[SAVED] {test_csv.name} ({len(test_df)} entries)")
        
        # Save JSON manifests for ASR
        train_json = CV_OUTPUT_DIR / "cv_twi_train_manifest.json"
        with open(train_json, 'w', encoding='utf-8') as f:
            json.dump(train_df.to_dict('records'), f, ensure_ascii=False, indent=2)
        print(f"[SAVED] {train_json.name}")
        
        test_json = CV_OUTPUT_DIR / "cv_twi_test_manifest.json"
        with open(test_json, 'w', encoding='utf-8') as f:
            json.dump(test_df.to_dict('records'), f, ensure_ascii=False, indent=2)
        print(f"[SAVED] {test_json.name}")
        
        # Statistics
        stats = {
            'total_clips': len(audio_files),
            'processed_clips': len(manifest),
            'matched_clips': matched,
            'unmatched_clips': unmatched,
            'train_size': len(train_df),
            'test_size': len(test_df),
            'total_duration_seconds': manifest_df['duration'].sum() if manifest_df['duration'].max() > 0 else -1,
            'unique_sentences': manifest_df['text'].nunique()
        }
        
        stats_file = CV_OUTPUT_DIR / "cv_twi_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"\n[SAVED] {stats_file.name}")
        
        # Show samples
        print("\nSample entries:")
        for idx, row in manifest_df.head(3).iterrows():
            print(f"\n  Audio: {Path(row['audio_filepath']).name}")
            print(f"  Text: {row['text'][:80]}...")
            if row['duration'] > 0:
                print(f"  Duration: {row['duration']:.1f}s")

elif not validated_df.empty:
    # No audio but have transcripts
    print("\nNo audio files found, but have transcripts")
    print(f"Saving {len(validated_df)} transcripts for reference...")
    
    transcript_file = CV_OUTPUT_DIR / "cv_twi_transcripts.csv"
    validated_df.to_csv(transcript_file, index=False)
    print(f"[SAVED] {transcript_file.name}")

else:
    print("\nNo data to process")

# Summary
print("\n" + "=" * 60)
print("COMMON VOICE TWI PROCESSING COMPLETE!")
print("=" * 60)

print(f"\nOutput location: {CV_OUTPUT_DIR}")

if audio_files:
    print(f"\nTotal audio clips available: {len(audio_files):,}")
    print("Next steps:")
    print("  1. Process remaining audio clips")
    print("  2. Convert to 16kHz WAV if needed")
    print("  3. Use for ASR model training")
else:
    print("\nNo audio clips found. Check if extraction is complete.")
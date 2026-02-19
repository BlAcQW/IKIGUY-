#!/usr/bin/env python
"""
Extract and process JW300 parallel corpus
Focus on Twi language pairs
"""

import zipfile
from pathlib import Path
import json
import pandas as pd

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw" / "jw300"
PROCESSED_DIR = BASE_DIR / "processed"
JW_OUTPUT_DIR = PROCESSED_DIR / "jw300_text"
JW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("PROCESSING JW300 PARALLEL CORPUS")
print("=" * 60)

# Check for the archive
archive_file = RAW_DIR / "opus-2020-01-08.zip"

if not archive_file.exists():
    print(f"ERROR: Archive not found: {archive_file}")
    exit(1)

print(f"Archive found: {archive_file.name}")
print(f"Size: {archive_file.stat().st_size / (1024**2):.1f} MB")

# Extract selectively (only Twi-related files)
print("\nExtracting Twi-related files...")

extract_dir = RAW_DIR / "extracted"
extract_dir.mkdir(exist_ok=True)

twi_files = []
other_files = []

try:
    with zipfile.ZipFile(archive_file, 'r') as zip_ref:
        # List all files
        all_files = zip_ref.namelist()
        print(f"Total files in archive: {len(all_files):,}")
        
        # Filter for Twi-related files
        for filename in all_files:
            # Check for Twi language codes (tw, twi, akan)
            if any(code in filename.lower() for code in ['tw.', '-tw-', 'twi.', '-twi-', 'akan']):
                twi_files.append(filename)
            else:
                other_files.append(filename)
        
        print(f"Twi-related files found: {len(twi_files)}")
        
        if twi_files:
            # Extract only Twi files
            print(f"\nExtracting {len(twi_files)} Twi files...")
            extracted_count = 0
            
            for file in twi_files[:100]:  # Extract first 100 for testing
                try:
                    zip_ref.extract(file, extract_dir)
                    extracted_count += 1
                    
                    if extracted_count % 10 == 0:
                        print(f"  Extracted {extracted_count} files...")
                        
                except Exception as e:
                    print(f"  Error extracting {file}: {str(e)[:50]}")
            
            print(f"Successfully extracted {extracted_count} files")
            
            # Show sample of what was extracted
            print("\nSample extracted files:")
            for file in twi_files[:10]:
                print(f"  - {file}")
        
        else:
            print("No Twi-related files found in archive")
            
            # Show sample of what's in the archive
            print("\nSample files in archive:")
            for file in all_files[:20]:
                print(f"  - {file}")
                
except Exception as e:
    print(f"Error processing archive: {str(e)}")

# Process extracted files
print("\n" + "-" * 60)
print("PROCESSING EXTRACTED FILES")
print("-" * 60)

if extract_dir.exists():
    # Find all text files
    txt_files = list(extract_dir.rglob("*.txt"))
    xml_files = list(extract_dir.rglob("*.xml"))
    
    print(f"Text files found: {len(txt_files)}")
    print(f"XML files found: {len(xml_files)}")
    
    # Process parallel text files
    parallel_texts = []
    
    # Look for language pairs
    for txt_file in txt_files[:50]:  # Process first 50
        # JW300 typically has format: JW300.en-tw.tw (English-Twi, Twi side)
        filename = txt_file.name
        
        if 'tw' in filename.lower():
            # Try to find corresponding pair
            lang_pair = None
            
            if '.en-tw.' in filename:
                lang_pair = 'en-tw'
            elif '.fr-tw.' in filename:
                lang_pair = 'fr-tw'
            elif '.de-tw.' in filename:
                lang_pair = 'de-tw'
            
            if lang_pair:
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    parallel_texts.append({
                        'file': filename,
                        'language_pair': lang_pair,
                        'lines': len(lines),
                        'sample': lines[0][:100] if lines else ''
                    })
                    
                except Exception as e:
                    print(f"  Error reading {filename}: {str(e)[:50]}")
    
    if parallel_texts:
        # Save summary
        summary_df = pd.DataFrame(parallel_texts)
        summary_file = JW_OUTPUT_DIR / "jw300_twi_files.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\n[SAVED] {summary_file.name}")
        
        # Show statistics
        print("\nLanguage pairs found:")
        for pair in summary_df['language_pair'].unique():
            pair_data = summary_df[summary_df['language_pair'] == pair]
            total_lines = pair_data['lines'].sum()
            print(f"  {pair}: {len(pair_data)} files, {total_lines:,} lines")
    
    # Create combined parallel corpus
    print("\nCreating combined parallel corpus...")
    
    en_tw_pairs = []
    
    # Look for English-Twi pairs
    for txt_file in txt_files:
        if '.en-tw.en' in txt_file.name:
            # This is English side
            tw_file = txt_file.parent / txt_file.name.replace('.en-tw.en', '.en-tw.tw')
            
            if tw_file.exists():
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        en_lines = f.readlines()
                    with open(tw_file, 'r', encoding='utf-8') as f:
                        tw_lines = f.readlines()
                    
                    # Create pairs
                    for en_line, tw_line in zip(en_lines[:100], tw_lines[:100]):
                        if en_line.strip() and tw_line.strip():
                            en_tw_pairs.append({
                                'english': en_line.strip(),
                                'twi': tw_line.strip(),
                                'source': 'jw300'
                            })
                    
                except Exception as e:
                    print(f"  Error processing pair: {str(e)[:50]}")
    
    if en_tw_pairs:
        # Save parallel corpus
        pairs_df = pd.DataFrame(en_tw_pairs)
        pairs_file = JW_OUTPUT_DIR / "jw300_en_tw_pairs.csv"
        pairs_df.to_csv(pairs_file, index=False)
        print(f"[SAVED] {pairs_file.name} ({len(pairs_df)} pairs)")
        
        # Show samples
        print("\nSample parallel sentences:")
        for idx, row in pairs_df.head(3).iterrows():
            print(f"\n  EN: {row['english'][:80]}...")
            print(f"  TW: {row['twi'][:80]}...")

# Summary
print("\n" + "=" * 60)
print("JW300 PROCESSING COMPLETE!")
print("=" * 60)

print(f"\nOutput location: {JW_OUTPUT_DIR}")

# Statistics
stats = {
    'archive_size_mb': archive_file.stat().st_size / (1024**2),
    'twi_files_in_archive': len(twi_files),
    'files_extracted': extracted_count if 'extracted_count' in locals() else 0,
    'parallel_pairs': len(en_tw_pairs) if 'en_tw_pairs' in locals() else 0
}

stats_file = JW_OUTPUT_DIR / "jw300_statistics.json"
with open(stats_file, 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2)

print(f"[SAVED] {stats_file.name}")

print("\nNext steps:")
print("  1. Extract remaining files if needed")
print("  2. Combine with existing 4M+ pairs")
print("  3. Use for translation model training")
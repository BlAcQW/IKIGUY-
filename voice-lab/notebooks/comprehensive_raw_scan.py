#!/usr/bin/env python
"""
Comprehensive scan of all raw data folders
Identify what we have and what we've missed
"""

from pathlib import Path
import json
from collections import defaultdict

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

print("COMPREHENSIVE RAW DATA SCAN")
print("=" * 60)

# Track all findings
findings = {
    'directories': {},
    'unprocessed': [],
    'processed': [],
    'archives': [],
    'summary': {}
}

def scan_directory(dir_path, level=0, max_level=3):
    """Recursively scan directory and gather statistics"""
    if level > max_level:
        return {}
    
    stats = {
        'path': str(dir_path),
        'name': dir_path.name,
        'subdirs': [],
        'files': defaultdict(int),
        'total_files': 0,
        'total_size_mb': 0
    }
    
    try:
        # Count files by extension
        for item in dir_path.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                stats['files'][ext] += 1
                stats['total_files'] += 1
                try:
                    stats['total_size_mb'] += item.stat().st_size / (1024 * 1024)
                except:
                    pass
            elif item.is_dir() and not item.name.startswith('.'):
                # Recursively scan subdirectories
                subdir_stats = scan_directory(item, level + 1, max_level)
                if subdir_stats['total_files'] > 0:  # Only include non-empty dirs
                    stats['subdirs'].append(subdir_stats)
    except Exception as e:
        stats['error'] = str(e)[:50]
    
    return stats

print("Scanning raw directory structure...")
print("-" * 60)

# First, list all top-level directories
top_dirs = [d for d in RAW_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
print(f"\nTop-level directories found: {len(top_dirs)}")
for dir in sorted(top_dirs):
    print(f"  - {dir.name}")

print("\n" + "=" * 60)
print("DETAILED SCAN BY DIRECTORY")
print("=" * 60)

# Scan each top-level directory
for top_dir in sorted(top_dirs):
    print(f"\n{top_dir.name.upper()}")
    print("-" * 40)
    
    # Quick stats for this directory
    dir_stats = scan_directory(top_dir, max_level=2)
    findings['directories'][top_dir.name] = dir_stats
    
    # Print summary
    print(f"  Total files: {dir_stats['total_files']:,}")
    print(f"  Total size: {dir_stats['total_size_mb']:.1f} MB")
    
    if dir_stats['files']:
        print(f"  File types:")
        for ext, count in sorted(dir_stats['files'].items(), key=lambda x: -x[1])[:5]:
            print(f"    {ext}: {count:,}")
    
    if dir_stats['subdirs']:
        print(f"  Subdirectories: {len(dir_stats['subdirs'])}")
        for subdir in dir_stats['subdirs'][:3]:  # Show first 3
            print(f"    - {subdir['name']}: {subdir['total_files']} files")

# Identify specific dataset types
print("\n" + "=" * 60)
print("DATASET IDENTIFICATION")
print("=" * 60)

# Check for unprocessed archives
print("\n1. ARCHIVES (May need extraction):")
print("-" * 40)
archive_extensions = ['.zip', '.tar', '.gz', '.tgz', '.7z', '.rar']
for dir_name, stats in findings['directories'].items():
    archives_found = []
    for ext in archive_extensions:
        if ext in stats['files'] and stats['files'][ext] > 0:
            archives_found.append(f"{stats['files'][ext]} {ext} files")
    
    if archives_found:
        print(f"  {dir_name}: {', '.join(archives_found)}")
        findings['archives'].append(dir_name)

# Check for audio datasets
print("\n2. AUDIO DATASETS:")
print("-" * 40)
audio_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.wma']
for dir_name, stats in findings['directories'].items():
    audio_count = sum(stats['files'].get(ext, 0) for ext in audio_extensions)
    
    # Also check subdirectories
    for subdir in stats.get('subdirs', []):
        audio_count += sum(subdir['files'].get(ext, 0) for ext in audio_extensions)
    
    if audio_count > 0:
        print(f"  {dir_name}: {audio_count:,} audio files")

# Check for text datasets
print("\n3. TEXT DATASETS:")
print("-" * 40)
text_extensions = ['.txt', '.csv', '.tsv', '.json', '.jsonl', '.parquet']
for dir_name, stats in findings['directories'].items():
    text_count = sum(stats['files'].get(ext, 0) for ext in text_extensions)
    
    # Check subdirectories
    for subdir in stats.get('subdirs', []):
        text_count += sum(subdir['files'].get(ext, 0) for ext in text_extensions)
    
    if text_count > 0:
        print(f"  {dir_name}: {text_count:,} text/data files")

# Identify what we've processed vs unprocessed
print("\n" + "=" * 60)
print("PROCESSING STATUS")
print("=" * 60)

processed_datasets = [
    'michsethowusu',  # 4M+ pairs processed
    'financial_inclusion',  # Partially processed
    'bibletts',  # Identified, structure known
]

unprocessed_candidates = []

for dir_name in findings['directories']:
    if dir_name not in processed_datasets:
        stats = findings['directories'][dir_name]
        if stats['total_files'] > 10:  # Significant content
            unprocessed_candidates.append(dir_name)
            findings['unprocessed'].append({
                'name': dir_name,
                'files': stats['total_files'],
                'size_mb': stats['total_size_mb']
            })
    else:
        findings['processed'].append(dir_name)

print("\nPROCESSED DATASETS:")
for name in findings['processed']:
    stats = findings['directories'][name]
    print(f"  [OK] {name}: {stats['total_files']:,} files")

print("\nUNPROCESSED/PARTIALLY PROCESSED:")
for item in findings['unprocessed']:
    print(f"  ? {item['name']}: {item['files']:,} files ({item['size_mb']:.1f} MB)")

# Special checks
print("\n" + "=" * 60)
print("SPECIAL FINDINGS")
print("=" * 60)

# Check Common Voice
if 'common_voice' in findings['directories']:
    cv_stats = findings['directories']['common_voice']
    print("\nCommon Voice:")
    print(f"  Files: {cv_stats['total_files']}")
    print(f"  Needs extraction: {'.gz' in cv_stats['files'] or '.tar' in cv_stats['files']}")

# Check JW300
if 'jw300' in findings['directories']:
    jw_stats = findings['directories']['jw300']
    print("\nJW300:")
    print(f"  Files: {jw_stats['total_files']}")
    if '.zip' in jw_stats['files']:
        print(f"  Archives to extract: {jw_stats['files']['.zip']}")

# Check African Whisper
if 'african_whisper' in findings['directories']:
    aw_stats = findings['directories']['african_whisper']
    print("\nAfrican Whisper:")
    print(f"  Files: {aw_stats['total_files']}")

# Check AfriSpeech
if 'afrispeech' in findings['directories']:
    as_stats = findings['directories']['afrispeech']
    print("\nAfriSpeech:")
    print(f"  Files: {as_stats['total_files']}")

# Save comprehensive report
report = {
    'scan_date': pd.Timestamp.now().isoformat() if 'pd' in globals() else str(Path.cwd()),
    'raw_directory': str(RAW_DIR),
    'total_directories': len(findings['directories']),
    'processed_count': len(findings['processed']),
    'unprocessed_count': len(findings['unprocessed']),
    'directories': findings['directories'],
    'unprocessed': findings['unprocessed'],
    'archives_found': findings['archives']
}

report_file = PROCESSED_DIR / "raw_data_comprehensive_scan.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

print(f"\n[SAVED] Comprehensive report: {report_file.name}")

# Final summary
print("\n" + "=" * 60)
print("SCAN COMPLETE - SUMMARY")
print("=" * 60)

total_files = sum(d['total_files'] for d in findings['directories'].values())
total_size = sum(d['total_size_mb'] for d in findings['directories'].values())

print(f"\nTotal directories scanned: {len(findings['directories'])}")
print(f"Total files found: {total_files:,}")
print(f"Total size: {total_size/1024:.2f} GB")
print(f"\nProcessed datasets: {len(findings['processed'])}")
print(f"Unprocessed/Partial: {len(findings['unprocessed'])}")
print(f"Archives to extract: {len(findings['archives'])}")

print("\nRECOMMENDATIONS:")
print("-" * 40)
print("1. Extract archives in:", ', '.join(findings['archives'][:3]))
print("2. Process remaining datasets:", ', '.join([u['name'] for u in findings['unprocessed'][:3]]))
print("3. Verify Financial Inclusion transcript alignment")
print("4. Check Common Voice for Twi language data")
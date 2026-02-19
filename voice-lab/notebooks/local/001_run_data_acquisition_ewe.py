#!/usr/bin/env python3
"""
Data Acquisition Script for Ewe Language Datasets
Auto-generated script for downloading and organizing Ewe language datasets
"""

import os
import sys
import json
import tarfile
import zipfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Logging utility
def log_progress(message, level='INFO'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prefix = {
        'INFO': '📋',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠️',
        'START': '🚀',
        'DOWNLOAD': '📥',
        'EXTRACT': '📦',
        'SAVE': '💾'
    }.get(level, 'ℹ️')
    print(f"{prefix} [{timestamp}] {message}")
    sys.stdout.flush()

# Import optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    log_progress("pandas not installed, some features may be limited", "WARNING")
    HAS_PANDAS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    log_progress("requests not installed, downloads may fail", "WARNING")
    HAS_REQUESTS = False

try:
    from tqdm.auto import tqdm
    HAS_TQDM = True
except ImportError:
    log_progress("tqdm not installed, no progress bars", "WARNING")
    tqdm = lambda x, **kwargs: x
    HAS_TQDM = False

try:
    import librosa
    import soundfile as sf
    HAS_AUDIO = True
except ImportError:
    log_progress("librosa/soundfile not installed, audio processing limited", "WARNING")
    HAS_AUDIO = False

try:
    from datasets import load_dataset, Dataset, DatasetDict
    HAS_DATASETS = True
except ImportError:
    log_progress("datasets not installed, HuggingFace datasets unavailable", "WARNING")
    HAS_DATASETS = False

# Environment detection
IN_COLAB = 'google.colab' in sys.modules
IN_KAGGLE = 'kaggle_secrets' in sys.modules

log_progress('Starting Data Acquisition Pipeline for Ewe Language', 'START')
print('='*80)
print(f"Environment: {'Google Colab' if IN_COLAB else 'Kaggle' if IN_KAGGLE else 'Local'}")
print(f"Python version: {sys.version}")
print('='*80)

# Configure HF token
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    log_progress("HF_TOKEN not found in environment variables", "WARNING")
    log_progress("Some datasets may not be accessible", "WARNING")

# Configure base directory
if IN_COLAB:
    BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data/ewe')
elif IN_KAGGLE:
    BASE_DIR = Path('/kaggle/working/voice-lab-data/ewe')
else:
    BASE_DIR = Path('/opt/kasaai/apps/voice-lab/data/ewe')

# Create directory structure
DIRS = {
    'raw': BASE_DIR / 'raw',
    'processed': BASE_DIR / 'processed',
    'synthetic': BASE_DIR / 'synthetic',
    'metadata': BASE_DIR / 'metadata'
}

for dir_path in DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

log_progress(f"Base directory: {BASE_DIR}", "INFO")
log_progress("Directory structure created:", "INFO")
for name, path in DIRS.items():
    print(f"  {name}: {path}")

# Download helper function
def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """Download file with progress bar."""
    if not HAS_REQUESTS:
        log_progress("requests not available, cannot download", "ERROR")
        return False

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(dest_path, 'wb') as file:
            if HAS_TQDM:
                with tqdm(total=total_size, unit='iB', unit_scale=True, desc=dest_path.name) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
        return True
    except Exception as e:
        log_progress(f"Error downloading {url}: {e}", "ERROR")
        return False

# 1. Download Financial Inclusion Speech Dataset (FISD) - Ewe Language
log_progress("Starting Financial Inclusion Speech Dataset (Ewe) download", "DOWNLOAD")

FISD_URLS = {
    'ewe_90': 'https://fisd-dataset.s3.amazonaws.com/fisd-ewe-90p.zip',
    'ewe_10': 'https://fisd-dataset.s3.amazonaws.com/fisd-ewe-10p.zip',
}

fisd_dir = DIRS['raw'] / 'fisd'
fisd_dir.mkdir(exist_ok=True)

download_stats = {'total_files': len(FISD_URLS), 'downloaded': 0, 'extracted': 0, 'failed': []}

for name, url in FISD_URLS.items():
    zip_path = fisd_dir / f"{name}.zip"
    extract_dir = fisd_dir / name

    # Skip if already extracted
    if extract_dir.exists() and any(extract_dir.iterdir()):
        log_progress(f"{name} already extracted", "SUCCESS")
        download_stats['extracted'] += 1
        continue

    # Download
    if not zip_path.exists():
        log_progress(f"Downloading {name}...", "DOWNLOAD")
        if download_file(url, zip_path):
            download_stats['downloaded'] += 1
        else:
            download_stats['failed'].append(name)
            continue

    # Extract
    try:
        log_progress(f"Extracting {name}...", "EXTRACT")
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        download_stats['extracted'] += 1

        # Count audio files
        audio_files = list(extract_dir.rglob('*.ogg')) + list(extract_dir.rglob('*.wav'))
        log_progress(f"Extracted {name} successfully ({len(audio_files)} audio files)", "SUCCESS")
    except Exception as e:
        log_progress(f"Error extracting {name}: {e}", "ERROR")
        download_stats['failed'].append(name)

# Save metadata
if HAS_PANDAS:
    metadata = {
        'download_date': datetime.now().isoformat(),
        'language': 'ee',
        'language_name': 'Ewe',
        'total_datasets': download_stats['extracted'],
        'failed_downloads': download_stats['failed'],
        'dataset_info': {
            'fisd': {
                'name': 'Financial Inclusion Speech Dataset',
                'source': 'Ashesi University & Nokwary Technologies',
                'license': 'CC-BY-4.0',
                'speakers': '~200',
                'hours': '~40',
                'format': '.ogg',
                'url': 'https://github.com/Ashesi-Org/Financial-Inclusion-Speech-Dataset'
            }
        }
    }
    with open(DIRS['metadata'] / 'dataset_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

log_progress(f"Financial Inclusion Speech Dataset: {download_stats['extracted']} datasets extracted", "SUCCESS")

# 2. Generate dataset statistics
log_progress("Generating dataset statistics...", "INFO")

stats = {
    'total_audio_files': 0,
    'total_size_mb': 0,
    'formats': {},
    'datasets': {}
}

for dataset_dir in [fisd_dir]:
    if dataset_dir.exists():
        audio_files = list(dataset_dir.rglob('*.ogg')) + \
                     list(dataset_dir.rglob('*.wav')) + \
                     list(dataset_dir.rglob('*.flac')) + \
                     list(dataset_dir.rglob('*.mp3'))

        stats['total_audio_files'] += len(audio_files)

        for audio_file in audio_files:
            ext = audio_file.suffix
            stats['formats'][ext] = stats['formats'].get(ext, 0) + 1
            stats['total_size_mb'] += audio_file.stat().st_size / (1024**2)

        stats['datasets'][dataset_dir.name] = {
            'audio_files': len(audio_files),
            'formats': {}
        }

        for audio_file in audio_files:
            ext = audio_file.suffix
            stats['datasets'][dataset_dir.name]['formats'][ext] = \
                stats['datasets'][dataset_dir.name]['formats'].get(ext, 0) + 1

# Save statistics
if HAS_PANDAS:
    with open(DIRS['metadata'] / 'dataset_statistics.json', 'w') as f:
        json.dump(stats, f, indent=2)

# 3. Summary
log_progress("Data Acquisition Pipeline Complete", "SUCCESS")
print('='*80)
print("\n📊 DOWNLOAD SUMMARY:")
print(f"  Base directory: {BASE_DIR}")
print(f"\n  Language: Ewe (ee)")
print(f"\n  Downloaded Datasets:")
print(f"    - Financial Inclusion Speech Dataset (FISD)")
print(f"      • 90% split: fisd-ewe-90p.zip")
print(f"      • 10% split: fisd-ewe-10p.zip")
print(f"      • ~40 hours, ~200 speakers")
print(f"      • License: CC-BY-4.0")
print(f"\n  Dataset Statistics:")
print(f"    - Total audio files: {stats['total_audio_files']}")
print(f"    - Total size: {stats['total_size_mb']:.1f} MB")
print(f"    - Audio formats: {', '.join(stats['formats'].keys())}")
print(f"\n  Data saved to:")
for name, path in DIRS.items():
    if path.exists():
        size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        size_mb = size / (1024**2)
        print(f"    {name}: {path} ({size_mb:.1f} MB)")
print('='*80)

# 4. Notes and next steps
print("\n📝 NOTES:")
print("  • Ewe language datasets are limited compared to other Ghanaian languages")
print("  • Currently available: Financial Inclusion Speech Dataset only")
print("  • NOT available: BibleTTS, Mozilla Common Voice, UGSpeechData")
print("  • For TTS/ASR training, consider data augmentation strategies")
print("  • For LLM training, additional text corpora may be needed")
print("\n  Next Steps:")
print("    1. Process audio files for ASR training")
print("    2. Extract transcriptions from data.csv files")
print("    3. Consider synthetic data generation")
print("    4. Explore web scraping for additional text data")
print('='*80)

log_progress("Pipeline execution complete!", "SUCCESS")

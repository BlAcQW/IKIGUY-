#!/usr/bin/env python3
"""
Data Acquisition Script for Hausa Language Datasets
Auto-generated script for downloading and organizing Hausa language datasets
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

log_progress('Starting Data Acquisition Pipeline for Hausa Language', 'START')
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
    BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data/hausa')
elif IN_KAGGLE:
    BASE_DIR = Path('/kaggle/working/voice-lab-data/hausa')
else:
    BASE_DIR = Path('/opt/kasaai/apps/voice-lab/data/hausa')

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

all_datasets_info = {}
total_extracted = 0

# 1. Download Mozilla Common Voice (via HuggingFace)
log_progress("Starting Mozilla Common Voice (Hausa) download", "DOWNLOAD")

if HAS_DATASETS:
    cv_dir = DIRS['raw'] / 'common_voice'
    cv_dir.mkdir(exist_ok=True)

    try:
        log_progress("Downloading Google FLEURS (Hausa) from HuggingFace...", "DOWNLOAD")
        # Google FLEURS dataset - uses standard format
        dataset = load_dataset(
            "google/fleurs",
            "ha_ng",  # Hausa (Nigeria)
            token=HF_TOKEN if HF_TOKEN else None,
            trust_remote_code=True
        )

        # Save dataset splits
        for split in dataset.keys():
            split_dir = cv_dir / split
            split_dir.mkdir(exist_ok=True)
            dataset[split].save_to_disk(str(split_dir))
            log_progress(f"Saved {split} split: {len(dataset[split])} samples", "SUCCESS")

        all_datasets_info['fleurs'] = {
            'name': 'Google FLEURS',
            'source': 'Google Research',
            'license': 'CC-BY-4.0',
            'splits': {split: len(dataset[split]) for split in dataset.keys()},
            'total_samples': sum(len(dataset[split]) for split in dataset.keys()),
            'url': 'https://huggingface.co/datasets/google/fleurs'
        }
        total_extracted += 1

    except Exception as e:
        log_progress(f"Error downloading Common Voice: {e}", "ERROR")
else:
    log_progress("Skipping Common Voice (HuggingFace datasets not available)", "WARNING")

# 2. Download BibleTTS (if available via HuggingFace)
log_progress("Starting BibleTTS (Hausa) download", "DOWNLOAD")

if HAS_DATASETS:
    bibletts_dir = DIRS['raw'] / 'bibletts'
    bibletts_dir.mkdir(exist_ok=True)

    try:
        log_progress("Downloading BibleTTS from HuggingFace...", "DOWNLOAD")
        dataset = load_dataset(
            "bible-tts/hausa",
            token=HF_TOKEN if HF_TOKEN else None,
            trust_remote_code=True
        )

        # Save dataset
        for split in dataset.keys():
            split_dir = bibletts_dir / split
            split_dir.mkdir(exist_ok=True)
            dataset[split].save_to_disk(str(split_dir))
            log_progress(f"Saved {split} split: {len(dataset[split])} samples", "SUCCESS")

        all_datasets_info['bibletts'] = {
            'name': 'BibleTTS',
            'source': 'Bible.is',
            'license': 'Various (check individual speakers)',
            'splits': {split: len(dataset[split]) for split in dataset.keys()},
            'total_samples': sum(len(dataset[split]) for split in dataset.keys()),
            'url': 'https://huggingface.co/datasets/bible-tts'
        }
        total_extracted += 1

    except Exception as e:
        log_progress(f"BibleTTS not available or error: {e}", "WARNING")
else:
    log_progress("Skipping BibleTTS (HuggingFace datasets not available)", "WARNING")

# 3. Download ALFFA Hausa (if available)
log_progress("Checking for ALFFA Hausa dataset", "DOWNLOAD")

if HAS_DATASETS:
    alffa_dir = DIRS['raw'] / 'alffa'
    alffa_dir.mkdir(exist_ok=True)

    try:
        log_progress("Downloading ALFFA Hausa from HuggingFace...", "DOWNLOAD")
        dataset = load_dataset(
            "ksharma/alffa_hausa",
            token=HF_TOKEN if HF_TOKEN else None,
            trust_remote_code=True
        )

        # Save dataset
        for split in dataset.keys():
            split_dir = alffa_dir / split
            split_dir.mkdir(exist_ok=True)
            dataset[split].save_to_disk(str(split_dir))
            log_progress(f"Saved {split} split: {len(dataset[split])} samples", "SUCCESS")

        all_datasets_info['alffa'] = {
            'name': 'ALFFA Hausa',
            'source': 'ALFFA Project',
            'license': 'CC-BY-4.0',
            'splits': {split: len(dataset[split]) for split in dataset.keys()},
            'total_samples': sum(len(dataset[split]) for split in dataset.keys()),
            'url': 'https://github.com/getalp/ALFFA_PUBLIC'
        }
        total_extracted += 1

    except Exception as e:
        log_progress(f"ALFFA Hausa not available or error: {e}", "WARNING")
else:
    log_progress("Skipping ALFFA (HuggingFace datasets not available)", "WARNING")

# Save metadata
if HAS_PANDAS:
    metadata = {
        'download_date': datetime.now().isoformat(),
        'language': 'ha',
        'language_name': 'Hausa',
        'total_datasets': total_extracted,
        'dataset_info': all_datasets_info
    }
    with open(DIRS['metadata'] / 'dataset_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

log_progress(f"Downloaded {total_extracted} datasets successfully", "SUCCESS")

# 4. Generate dataset statistics
log_progress("Generating dataset statistics...", "INFO")

stats = {
    'total_audio_files': 0,
    'total_size_mb': 0,
    'formats': {},
    'datasets': {}
}

for dataset_dir in [DIRS['raw'] / 'common_voice', DIRS['raw'] / 'bibletts', DIRS['raw'] / 'alffa']:
    if dataset_dir.exists():
        audio_files = list(dataset_dir.rglob('*.mp3')) + \
                     list(dataset_dir.rglob('*.wav')) + \
                     list(dataset_dir.rglob('*.flac')) + \
                     list(dataset_dir.rglob('*.ogg'))

        stats['total_audio_files'] += len(audio_files)

        for audio_file in audio_files:
            ext = audio_file.suffix
            stats['formats'][ext] = stats['formats'].get(ext, 0) + 1
            try:
                stats['total_size_mb'] += audio_file.stat().st_size / (1024**2)
            except:
                pass

        if audio_files:
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

# 5. Summary
log_progress("Data Acquisition Pipeline Complete", "SUCCESS")
print('='*80)
print("\n📊 DOWNLOAD SUMMARY:")
print(f"  Base directory: {BASE_DIR}")
print(f"\n  Language: Hausa (ha)")
print(f"\n  Downloaded Datasets:")

for dataset_name, dataset_info in all_datasets_info.items():
    print(f"    - {dataset_info['name']}")
    print(f"      • Source: {dataset_info['source']}")
    print(f"      • License: {dataset_info['license']}")
    if 'total_samples' in dataset_info:
        print(f"      • Samples: {dataset_info['total_samples']}")
    if 'splits' in dataset_info:
        print(f"      • Splits: {', '.join(dataset_info['splits'].keys())}")

print(f"\n  Dataset Statistics:")
print(f"    - Total audio files: {stats['total_audio_files']}")
print(f"    - Total size: {stats['total_size_mb']:.1f} MB")
if stats['formats']:
    print(f"    - Audio formats: {', '.join(stats['formats'].keys())}")

print(f"\n  Data saved to:")
for name, path in DIRS.items():
    if path.exists():
        try:
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            size_mb = size / (1024**2)
            print(f"    {name}: {path} ({size_mb:.1f} MB)")
        except:
            print(f"    {name}: {path}")
print('='*80)

# 6. Notes and next steps
print("\n📝 NOTES:")
print("  • Hausa is one of the most well-resourced African languages")
print("  • Multiple high-quality datasets available")
print("  • Good coverage for both ASR and TTS training")
print("  • Consider combining datasets for better model performance")
print("\n  Next Steps:")
print("    1. Process audio files for ASR training")
print("    2. Extract and normalize transcriptions")
print("    3. Create unified dataset with all sources")
print("    4. Generate train/val/test splits")
print("    5. Consider data augmentation for specific domains")
print('='*80)

log_progress("Pipeline execution complete!", "SUCCESS")

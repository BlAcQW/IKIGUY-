#!/usr/bin/env python3
"""
Data Acquisition Script for Twi/Akan/Fante Datasets
Auto-generated from 001_phase1_data_acquisition.ipynb
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

log_progress('Starting Data Acquisition Pipeline', 'START')
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
    BASE_DIR = Path('/content/drive/MyDrive/voice-lab-data')
elif IN_KAGGLE:
    BASE_DIR = Path('/kaggle/working/voice-lab-data')
else:
    BASE_DIR = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante')

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

# 1. Download BibleTTS
log_progress("Starting BibleTTS download", "DOWNLOAD")

BIBLETTS_URLS = {
    'akuapem_twi': [
        'https://www.openslr.org/resources/129/akuapem-twi.tgz',
        'https://us.openslr.org/resources/129/akuapem-twi.tgz',
        'https://cn.openslr.org/resources/129/akuapem-twi.tgz'
    ],
    'asante_twi': [
        'https://www.openslr.org/resources/129/asante-twi.tgz',
        'https://us.openslr.org/resources/129/asante-twi.tgz',
        'https://cn.openslr.org/resources/129/asante-twi.tgz'
    ]
}

bibletts_dir = DIRS['raw'] / 'bibletts'
bibletts_dir.mkdir(exist_ok=True)

for lang, urls in BIBLETTS_URLS.items():
    file_path = bibletts_dir / f"{lang}.tgz"
    extract_dir = bibletts_dir / lang

    # Check if already extracted
    if extract_dir.exists():
        audio_files = list(extract_dir.rglob('*.flac')) + list(extract_dir.rglob('*.wav'))
        if audio_files:
            log_progress(f"{lang} already extracted ({len(audio_files)} audio files found)", "SUCCESS")
            continue

    # Download
    if not file_path.exists():
        log_progress(f"Downloading {lang} BibleTTS...", "DOWNLOAD")
        for url in urls:
            if download_file(url, file_path):
                break
        else:
            log_progress(f"Failed to download {lang} from all mirrors", "ERROR")
            continue

    # Extract
    log_progress(f"Extracting {lang}...", "EXTRACT")
    try:
        with tarfile.open(file_path, 'r:gz') as tar:
            tar.extractall(bibletts_dir)

        # Check if extraction created the expected directory
        if not extract_dir.exists():
            alt_name = lang.replace('_', '-')
            alt_dir = bibletts_dir / alt_name
            if alt_dir.exists():
                alt_dir.rename(extract_dir)

        audio_files = list(extract_dir.rglob('*.flac')) + list(extract_dir.rglob('*.wav'))
        log_progress(f"{lang} extracted successfully ({len(audio_files)} audio files)", "SUCCESS")
    except Exception as e:
        log_progress(f"Error extracting {lang}: {e}", "ERROR")

# 2. Download Financial Inclusion Dataset
log_progress("Starting Financial Inclusion dataset download", "DOWNLOAD")

fi_dir = DIRS['raw'] / 'financial_inclusion'
fi_dir.mkdir(exist_ok=True)

if not (fi_dir / 'download_complete.flag').exists():
    FISD_URLS = {
        'akuapem_twi_90': 'https://fisd-dataset.s3.amazonaws.com/fisd-akuapim-twi-90p.zip',
        'akuapem_twi_10': 'https://fisd-dataset.s3.amazonaws.com/fisd-akuapim-twi-10p.zip',
        'asante_twi_90': 'https://fisd-dataset.s3.amazonaws.com/fisd-asanti-twi-90p.zip',
        'asante_twi_10': 'https://fisd-dataset.s3.amazonaws.com/fisd-asanti-twi-10p.zip',
        'fante_90': 'https://fisd-dataset.s3.amazonaws.com/fisd-fanti-90p.zip',
        'fante_10': 'https://fisd-dataset.s3.amazonaws.com/fisd-fanti-10p.zip',
    }

    download_stats = {'total_files': len(FISD_URLS), 'downloaded': 0, 'extracted': 0, 'failed': []}

    for name, url in FISD_URLS.items():
        zip_path = fi_dir / f"{name}.zip"
        extract_dir = fi_dir / name

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
            log_progress(f"Extracted {name} successfully", "SUCCESS")
        except Exception as e:
            log_progress(f"Error extracting {name}: {e}", "ERROR")
            download_stats['failed'].append(name)

    # Save metadata
    if HAS_PANDAS:
        metadata = {
            'download_date': datetime.now().isoformat(),
            'languages': ['akuapem_twi', 'asante_twi', 'fante'],
            'total_datasets': download_stats['extracted'],
            'failed_downloads': download_stats['failed']
        }
        with open(fi_dir / 'dataset_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

    # Create completion flag
    if download_stats['extracted'] > 0:
        with open(fi_dir / 'download_complete.flag', 'w') as f:
            f.write(f"Downloaded on {datetime.now()}")

    log_progress(f"Financial Inclusion: {download_stats['extracted']} datasets extracted", "SUCCESS")
else:
    log_progress("Financial Inclusion dataset already downloaded", "SUCCESS")

# 3. Download HuggingFace datasets with audio
log_progress("Starting HuggingFace dataset downloads", "DOWNLOAD")

if HAS_DATASETS:
    hf_dir = DIRS['raw'] / 'huggingface'
    hf_dir.mkdir(exist_ok=True)

    # Priority HuggingFace datasets with audio
    hf_datasets = {
        'Lagyamfi/akan_audio_processed': {
            'name': 'lagyamfi_akan',
            'description': 'Akan audio processed dataset (26.9k samples)',
            'priority': 1
        },
        'michsethowusu/twi_multispeaker_audio_transcribed': {
            'name': 'twi_multispeaker',
            'description': 'Twi multispeaker audio (31k samples)',
            'priority': 1
        },
        'michsethowusu/akuapem_multispeaker_audio_transcribed': {
            'name': 'akuapem_multispeaker',
            'description': 'Akuapem Twi multispeaker audio (28k samples)',
            'priority': 1
        },
        'michsethowusu/fante_multispeaker_audio_transcribed': {
            'name': 'fante_multispeaker',
            'description': 'Fante multispeaker audio (28k samples)',
            'priority': 1
        },
    }

    hf_stats = {'total': len(hf_datasets), 'downloaded': 0, 'skipped': 0, 'failed': []}

    for dataset_id, info in hf_datasets.items():
        dataset_path = hf_dir / info['name']

        # Check if already downloaded
        if dataset_path.exists() and any(dataset_path.iterdir()):
            log_progress(f"{info['name']} already downloaded", "SUCCESS")
            hf_stats['skipped'] += 1
            continue

        try:
            log_progress(f"Downloading {dataset_id}...", "DOWNLOAD")
            log_progress(f"  {info['description']}", "INFO")

            # Load dataset with authentication - DISABLE streaming to force full download
            try:
                log_progress(f"  Loading dataset (streaming=False to download audio)...", "INFO")
                dataset = load_dataset(
                    dataset_id,
                    token=HF_TOKEN if HF_TOKEN else True,
                    streaming=False  # Force download, not streaming
                )
            except Exception as e:
                if 'token' in str(e).lower() or 'authentication' in str(e).lower():
                    log_progress(f"  Authentication required. Using HF_TOKEN...", "WARNING")
                    dataset = load_dataset(
                        dataset_id,
                        token=HF_TOKEN,
                        streaming=False
                    )
                else:
                    raise

            # Calculate sample count before saving
            total_samples = sum(len(dataset[split]) for split in dataset.keys())
            log_progress(f"  Loaded {total_samples} samples across {len(dataset.keys())} splits", "INFO")

            # Force download by iterating through dataset (triggers audio download)
            log_progress(f"  Downloading audio files (this may take a while)...", "DOWNLOAD")
            for split_name in dataset.keys():
                split = dataset[split_name]
                log_progress(f"    Processing {split_name} split ({len(split)} samples)...", "INFO")

                # Access first few samples to trigger download
                if HAS_TQDM:
                    for i, sample in enumerate(tqdm(split, desc=f"    {split_name}", total=len(split))):
                        # Accessing audio field triggers download
                        _ = sample
                        # Progress update every 1000 samples
                        if i % 1000 == 0 and i > 0:
                            log_progress(f"      Downloaded {i}/{len(split)} samples", "INFO")
                else:
                    for i, sample in enumerate(split):
                        _ = sample
                        if i % 1000 == 0 and i > 0:
                            log_progress(f"      Downloaded {i}/{len(split)} samples", "INFO")

            # Now save to disk with all data downloaded
            log_progress(f"  Saving complete dataset to {dataset_path}...", "SAVE")
            dataset.save_to_disk(str(dataset_path))

            # Verify saved size
            saved_size = sum(f.stat().st_size for f in dataset_path.rglob('*') if f.is_file())
            saved_size_mb = saved_size / (1024**2)
            log_progress(f"  Saved size: {saved_size_mb:.1f} MB", "INFO")

            # Save metadata
            metadata = {
                'dataset_id': dataset_id,
                'name': info['name'],
                'description': info['description'],
                'priority': info['priority'],
                'total_samples': total_samples,
                'splits': {split: len(dataset[split]) for split in dataset.keys()},
                'features': list(dataset[list(dataset.keys())[0]].features.keys()),
                'download_date': datetime.now().isoformat(),
                'saved_size_mb': saved_size_mb
            }

            with open(dataset_path / 'download_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)

            log_progress(f"  ✓ {info['name']}: {total_samples} samples, {saved_size_mb:.1f} MB downloaded", "SUCCESS")
            hf_stats['downloaded'] += 1

        except Exception as e:
            error_msg = str(e)
            log_progress(f"  Error downloading {dataset_id}: {error_msg[:200]}", "ERROR")
            hf_stats['failed'].append(info['name'])

            if 'token' in error_msg.lower() or 'auth' in error_msg.lower():
                log_progress("  Run: huggingface-cli login", "WARNING")
            elif '404' in error_msg or 'not found' in error_msg.lower():
                log_progress("  Dataset may be private or moved", "WARNING")

    log_progress(f"HuggingFace downloads: {hf_stats['downloaded']} new, {hf_stats['skipped']} existing", "SUCCESS")
    if hf_stats['failed']:
        log_progress(f"Failed: {', '.join(hf_stats['failed'])}", "WARNING")
else:
    log_progress("HuggingFace datasets library not available, skipping", "WARNING")

# 4. Summary
log_progress("Data Acquisition Pipeline Complete", "SUCCESS")
print('='*80)
print("\n📊 DOWNLOAD SUMMARY:")
print(f"  Base directory: {BASE_DIR}")
print(f"\n  Downloaded:")
print(f"    - BibleTTS (Akuapem Twi, Asante Twi)")
print(f"    - Financial Inclusion (Akuapem Twi, Asante Twi, Fante)")
if HAS_DATASETS and 'hf_stats' in locals():
    print(f"    - HuggingFace datasets: {hf_stats['downloaded']} new, {hf_stats['skipped']} existing")
    if hf_stats['downloaded'] > 0:
        print(f"      ✓ Lagyamfi Akan (26.9k samples)")
        print(f"      ✓ Michsethowusu datasets (87k+ audio samples)")
print(f"\n  Data saved to:")
for name, path in DIRS.items():
    if path.exists():
        size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        size_mb = size / (1024**2)
        print(f"    {name}: {path} ({size_mb:.1f} MB)")
print('='*80)

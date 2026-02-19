#!/usr/bin/env python3
"""
Local Twi Data Processing Pipeline
Processes Twi/Akan/Fante datasets for ASR and TTS training at multiple sample rates
"""

import os
import sys
import json
import re
import unicodedata
import logging
import traceback
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import time

import numpy as np
import pandas as pd
import soundfile as sf
import librosa
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')

# Configure logging
LOG_DIR = Path('/opt/kasaai/apps/voice-lab/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f'twi_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_memory_usage():
    """Log current memory usage."""
    process = psutil.Process()
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / 1024 / 1024
    logger.info(f"Memory usage: {mem_mb:.2f} MB")
    return mem_mb

# --- TEXT PROCESSOR ---
class TwiTextProcessor:
    """Twi text processing and normalization."""

    def __init__(self):
        self.twi_chars = {'ɛ', 'Ɛ', 'ɔ', 'Ɔ', 'ã', 'ẽ', 'ĩ', 'õ', 'ũ'}

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Normalize unicode
        text = unicodedata.normalize('NFC', text)

        # Fix common encoding issues
        replacements = {
            'è': 'ɛ', 'È': 'Ɛ',
            'ò': 'ɔ', 'Ò': 'Ɔ',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove extra spaces
        text = ' '.join(text.split())

        return text

    def process_text(self, text: str) -> Dict:
        """Process text and return metadata."""
        original = text
        text = self.clean_text(text)

        return {
            'original': original,
            'processed': text,
            'has_twi_chars': any(c in text for c in self.twi_chars),
            'word_count': len(text.split()),
            'char_count': len(text)
        }

# --- CONFIGURATION ---
@dataclass
class ProcessingConfig:
    """Configuration for data processing."""
    base_path: Path
    output_path: Path

    # Sample rate configurations
    sample_rates: Dict[str, int] = field(default_factory=lambda: {
        'asr_16k': 16000,      # ASR models: Whisper, Wav2Vec2, MMS, Moshi
        'tts_22k': 22050,      # TTS models: Coqui XTTS, MeloTTS
        'tts_24k': 24000       # High-quality TTS: OpenVoice, Kokoro, F5, ChatTTS
    })

    # Quality thresholds
    min_duration: float = 0.5
    max_duration: float = 30.0
    min_text_length: int = 3
    max_text_length: int = 500
    target_db: float = -20.0

    # Model categories
    model_categories: Dict[str, List[str]] = field(default_factory=lambda: {
        'asr_16k': ['faster_whisper', 'wav2vec2', 'mms', 'moshi'],
        'tts_22k': ['coqui_xtts', 'melo_tts'],
        'tts_24k': ['openvoice', 'kokoro_tts', 'f5_tts', 'chattts']
    })

# --- DATA LOADER ---
class TwiDataLoader:
    """Load and scan Twi datasets."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.text_processor = TwiTextProcessor()

    def scan_all_datasets(self) -> pd.DataFrame:
        """Scan all available Twi datasets."""
        logger.info("=" * 80)
        logger.info("Starting dataset scanning")
        logger.info("=" * 80)
        log_memory_usage()

        print("🔄 Scanning Twi datasets...")

        all_samples = []
        dataset_stats = {}

        # Scan BibleTTS
        bibletts_path = self.config.base_path / 'bibletts'
        logger.info(f"Checking BibleTTS path: {bibletts_path}")
        if bibletts_path.exists():
            logger.info("BibleTTS path exists, starting scan")
            print("\n--- Scanning BibleTTS ---")
            try:
                samples = self._scan_bibletts(bibletts_path)
                all_samples.extend(samples)
                dataset_stats['bibletts'] = {'status': 'success', 'samples': len(samples)}
                logger.info(f"Successfully scanned BibleTTS: {len(samples)} samples")
                print(f"   ✅ Found {len(samples)} BibleTTS samples")
            except Exception as e:
                dataset_stats['bibletts'] = {'status': 'failed', 'error': str(e)}
                logger.error(f"Error scanning BibleTTS: {e}")
                logger.error(traceback.format_exc())
                print(f"   ❌ Failed to scan BibleTTS: {e}")
        else:
            logger.warning(f"BibleTTS path does not exist: {bibletts_path}")
            dataset_stats['bibletts'] = {'status': 'not_found'}

        # Scan Financial Inclusion
        fisd_path = self.config.base_path / 'financial_inclusion'
        logger.info(f"Checking Financial Inclusion path: {fisd_path}")
        if fisd_path.exists():
            logger.info("Financial Inclusion path exists, starting scan")
            print("\n--- Scanning Financial Inclusion ---")
            try:
                samples = self._scan_financial_inclusion(fisd_path)
                all_samples.extend(samples)
                dataset_stats['financial_inclusion'] = {'status': 'success', 'samples': len(samples)}
                logger.info(f"Successfully scanned Financial Inclusion: {len(samples)} samples")
                print(f"   ✅ Found {len(samples)} Financial Inclusion samples")
            except Exception as e:
                dataset_stats['financial_inclusion'] = {'status': 'failed', 'error': str(e)}
                logger.error(f"Error scanning Financial Inclusion: {e}")
                logger.error(traceback.format_exc())
                print(f"   ❌ Failed to scan Financial Inclusion: {e}")
        else:
            logger.warning(f"Financial Inclusion path does not exist: {fisd_path}")
            dataset_stats['financial_inclusion'] = {'status': 'not_found'}

        # Scan HuggingFace datasets
        hf_path = self.config.base_path / 'huggingface'
        logger.info(f"Checking HuggingFace path: {hf_path}")
        if hf_path.exists():
            logger.info("HuggingFace path exists, starting scan")
            print("\n--- Scanning HuggingFace Datasets ---")
            try:
                samples = self._scan_huggingface_datasets(hf_path)
                all_samples.extend(samples)
                dataset_stats['huggingface'] = {'status': 'success', 'samples': len(samples)}
                logger.info(f"Successfully scanned HuggingFace: {len(samples)} samples")
                print(f"   ✅ Found {len(samples)} HuggingFace samples")
            except Exception as e:
                dataset_stats['huggingface'] = {'status': 'failed', 'error': str(e)}
                logger.error(f"Error scanning HuggingFace: {e}")
                logger.error(traceback.format_exc())
                print(f"   ❌ Failed to scan HuggingFace: {e}")
        else:
            logger.warning(f"HuggingFace path does not exist: {hf_path}")
            dataset_stats['huggingface'] = {'status': 'not_found'}

        # Scan Common Voice Twi
        cv_path = self.config.base_path / 'common_voice_twi'
        logger.info(f"Checking Common Voice path: {cv_path}")
        if cv_path.exists():
            logger.info("Common Voice path exists, starting scan")
            print("\n--- Scanning Common Voice Twi ---")
            try:
                samples = self._scan_common_voice(cv_path)
                all_samples.extend(samples)
                dataset_stats['common_voice_twi'] = {'status': 'success', 'samples': len(samples)}
                logger.info(f"Successfully scanned Common Voice: {len(samples)} samples")
                print(f"   ✅ Found {len(samples)} Common Voice samples")
            except Exception as e:
                dataset_stats['common_voice_twi'] = {'status': 'failed', 'error': str(e)}
                logger.error(f"Error scanning Common Voice: {e}")
                logger.error(traceback.format_exc())
                print(f"   ❌ Failed to scan Common Voice: {e}")
        else:
            logger.warning(f"Common Voice path does not exist: {cv_path}")
            dataset_stats['common_voice_twi'] = {'status': 'not_found'}

        # Log dataset statistics
        print("\n" + "=" * 80)
        print("📊 DATASET SCANNING SUMMARY:")
        for dataset_name, stats in dataset_stats.items():
            status = stats['status']
            if status == 'success':
                print(f"   ✅ {dataset_name}: {stats['samples']} samples")
            elif status == 'failed':
                print(f"   ❌ {dataset_name}: {stats.get('error', 'Unknown error')}")
            elif status == 'not_found':
                print(f"   ⚠️  {dataset_name}: Directory not found")
        print("=" * 80)

        if not all_samples:
            logger.error("No samples found in any dataset!")
            raise ValueError("No samples found in any dataset!")

        # Create DataFrame
        logger.info(f"Creating DataFrame from {len(all_samples)} samples")
        df = pd.DataFrame(all_samples)
        print(f"\n✅ Total samples collected: {len(df)}")
        log_memory_usage()

        # Add metadata
        logger.info("Adding audio metadata")
        df = self._add_audio_metadata(df)
        logger.info("Adding text metadata")
        df = self._process_text_metadata(df)
        log_memory_usage()

        logger.info(f"Dataset scanning complete: {len(df)} total samples")
        return df

    def _scan_bibletts(self, bibletts_path: Path) -> List[Dict]:
        """Scan BibleTTS structure with co-located .txt files."""
        samples = []

        for audio_file in tqdm(list(bibletts_path.glob('**/*.flac')), desc="Scanning BibleTTS"):
            if '__MACOSX' in str(audio_file):
                continue

            text_file = audio_file.with_suffix('.txt')
            if text_file.exists():
                try:
                    text = text_file.read_text(encoding='utf-8').strip()
                    if text:
                        # Extract dialect from path
                        parts = audio_file.parts
                        if 'akuapem' in str(audio_file).lower():
                            dialect = 'akuapem_twi'
                        elif 'asante' in str(audio_file).lower():
                            dialect = 'asante_twi'
                        else:
                            dialect = 'twi'

                        speaker_id = f"bibletts_{dialect}_{audio_file.parent.name}"

                        samples.append({
                            'audio_path': str(audio_file),
                            'text': text,
                            'speaker_id': speaker_id,
                            'language': 'tw',
                            'dataset': 'bibletts',
                            'dialect': dialect
                        })
                except Exception as e:
                    continue

        return samples

    def _scan_financial_inclusion(self, fisd_path: Path) -> List[Dict]:
        """Scan Financial Inclusion structure with data.csv manifest."""
        samples = []
        logger.info(f"Scanning Financial Inclusion from: {fisd_path}")

        # Find all data.csv files
        csv_files = list(fisd_path.glob('**/data.csv'))
        logger.info(f"Found {len(csv_files)} CSV files")

        for csv_file in csv_files:
            if '__MACOSX' in str(csv_file):
                continue

            logger.info(f"Processing CSV: {csv_file}")

            try:
                # Try different CSV parsing strategies
                df = None
                try:
                    # First try: tab-delimited with index
                    df = pd.read_csv(csv_file, sep='\t', index_col=0, on_bad_lines='skip')
                    logger.info(f"  Parsed as tab-delimited with index. Columns: {list(df.columns)}")
                except:
                    try:
                        # Second try: comma-delimited
                        df = pd.read_csv(csv_file, on_bad_lines='skip')
                        logger.info(f"  Parsed as comma-delimited. Columns: {list(df.columns)}")
                    except Exception as e:
                        logger.error(f"  Failed to parse CSV: {e}")
                        continue

                if df is None or df.empty:
                    logger.warning(f"  Empty or unparseable CSV")
                    continue

                # Find relevant columns
                audio_col = next((c for c in df.columns if 'filepath' in c.lower() or 'audio' in c.lower()), None)
                text_col = next((c for c in df.columns if 'transcript' in c.lower()), None)

                logger.info(f"  Audio column: {audio_col}")
                logger.info(f"  Text column: {text_col}")

                if not (audio_col and text_col):
                    logger.warning(f"  Required columns not found")
                    continue

                # Extract dialect from path
                parent_name = csv_file.parent.parent.name
                if 'akuapem' in parent_name.lower():
                    dialect = 'akuapem_twi'
                elif 'asante' in parent_name.lower():
                    dialect = 'asante_twi'
                elif 'fante' in parent_name.lower():
                    dialect = 'fante'
                else:
                    dialect = 'twi'

                logger.info(f"  Dialect: {dialect}")

                # Process each row
                found_count = 0
                missing_count = 0

                for _, row in df.iterrows():
                    audio_path_rel = row[audio_col]
                    text = row[text_col]

                    if not isinstance(text, str) or not isinstance(audio_path_rel, str):
                        continue

                    # Extract just the filename from the CSV path
                    # CSV has: lacuna-audios-train/akuapim-twi/audios/filename.ogg
                    # Actual location: audios/filename.ogg
                    filename = Path(audio_path_rel).name
                    audio_file = csv_file.parent / 'audios' / filename

                    if not audio_file.exists():
                        # Try alternative paths
                        audio_file = csv_file.parent / audio_path_rel
                        if not audio_file.exists():
                            audio_file = csv_file.parent.parent / audio_path_rel

                    if audio_file.exists():
                        found_count += 1
                        speaker_id = f"fisd_{dialect}"

                        samples.append({
                            'audio_path': str(audio_file),
                            'text': text,
                            'speaker_id': speaker_id,
                            'language': 'tw',
                            'dataset': 'financial_inclusion',
                            'dialect': dialect
                        })
                    else:
                        missing_count += 1

                logger.info(f"  Found {found_count} audio files, missing {missing_count}")

            except Exception as e:
                logger.error(f"  Error processing {csv_file}: {e}")
                logger.error(traceback.format_exc())
                print(f"   ⚠️ Error processing {csv_file}: {e}")
                continue

        logger.info(f"Total Financial Inclusion samples: {len(samples)}")
        return samples

    def _scan_huggingface_datasets(self, hf_path: Path) -> List[Dict]:
        """Scan HuggingFace datasets with Arrow files containing embedded audio."""
        samples = []
        logger.info(f"Scanning HuggingFace datasets from: {hf_path}")

        # Import datasets library
        try:
            from datasets import load_from_disk
        except ImportError:
            logger.error("datasets library not available, skipping HuggingFace datasets")
            return samples

        # Find all dataset directories
        dataset_dirs = [d for d in hf_path.iterdir() if d.is_dir()]
        logger.info(f"Found {len(dataset_dirs)} dataset directories")

        for dataset_dir in dataset_dirs:
            dataset_name = dataset_dir.name
            logger.info(f"Processing dataset: {dataset_name}")

            # Check if this is a dataset saved with save_to_disk (has dataset_dict.json)
            if (dataset_dir / 'dataset_dict.json').exists():
                # This is a DatasetDict saved with save_to_disk
                try:
                    logger.info(f"  Loading as DatasetDict from {dataset_dir}")
                    dataset_dict = load_from_disk(str(dataset_dir))

                    for split_name, dataset in dataset_dict.items():
                        logger.info(f"  Processing split: {split_name} ({len(dataset)} samples)")
                        samples.extend(self._process_hf_dataset(dataset, dataset_name, split_name))

                except Exception as e:
                    logger.error(f"  Error loading DatasetDict from {dataset_dir}: {e}")
                    logger.error(traceback.format_exc())
                    continue
            else:
                # Try loading individual splits
                for split_dir in dataset_dir.iterdir():
                    if not split_dir.is_dir():
                        continue

                    split_name = split_dir.name
                    logger.info(f"  Processing split: {split_name}")

                    # Check for Arrow files
                    arrow_files = sorted(list(split_dir.glob('data-*.arrow')))
                    if not arrow_files:
                        logger.warning(f"    No Arrow files found in {split_dir}")
                        continue

                    logger.info(f"    Found {len(arrow_files)} Arrow files")

                    try:
                        # Load using datasets library
                        logger.info(f"    Loading split from {split_dir}")
                        dataset = load_from_disk(str(split_dir))
                        logger.info(f"    Loaded {len(dataset)} samples")

                        samples.extend(self._process_hf_dataset(dataset, dataset_name, split_name))

                    except Exception as e:
                        logger.error(f"    Error processing {split_dir}: {e}")
                        logger.error(traceback.format_exc())
                        continue

        logger.info(f"Total HuggingFace samples: {len(samples)}")
        return samples

    def _process_hf_dataset(self, dataset, dataset_name: str, split_name: str) -> List[Dict]:
        """Process a HuggingFace dataset split and extract samples."""
        samples = []

        # Find relevant columns
        columns = dataset.column_names if hasattr(dataset, 'column_names') else list(dataset.features.keys())
        text_col = next((c for c in ['transcription', 'transcript', 'text', 'sentence'] if c in columns), None)
        audio_col = next((c for c in ['audio', 'audio_path', 'speech'] if c in columns), None)
        speaker_col = next((c for c in ['speaker_id', 'client_id'] if c in columns), 'client_id')

        if not (text_col and audio_col):
            logger.error(f"    Missing required columns. Available: {columns}")
            return samples

        logger.info(f"    Text column: {text_col}, Audio column: {audio_col}")

        # Create temporary audio directory
        temp_audio_dir = self.config.output_path / 'temp_audio' / dataset_name / split_name
        temp_audio_dir.mkdir(parents=True, exist_ok=True)

        # Process each sample
        processed_count = 0
        error_count = 0

        for index in tqdm(range(len(dataset)), desc=f"    {dataset_name}/{split_name}", leave=False):
            try:
                sample = dataset[index]
                audio_data = sample.get(audio_col)
                text = sample.get(text_col)

                if not (audio_data and isinstance(text, str) and text.strip()):
                    continue

                speaker_id = sample.get(speaker_col, 'unknown_speaker')

                # Extract and save audio
                if isinstance(audio_data, dict) and 'array' in audio_data:
                    # Audio is embedded as dict with array and sampling_rate
                    audio_array = np.array(audio_data['array'], dtype=np.float32)
                    sampling_rate = audio_data['sampling_rate']

                    temp_filename = f"{dataset_name}_{split_name}_{speaker_id}_{index}.wav"
                    temp_filepath = temp_audio_dir / temp_filename

                    sf.write(temp_filepath, audio_array, sampling_rate)

                    samples.append({
                        'audio_path': str(temp_filepath),
                        'text': text.strip(),
                        'speaker_id': f"{dataset_name}_{speaker_id}",
                        'language': 'tw',
                        'dataset': f'hf_{dataset_name}',
                        'dialect': dataset_name.split('_')[0] if '_' in dataset_name else 'twi'
                    })

                    processed_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1
                if error_count % 100 == 0:
                    logger.warning(f"    Error processing sample {index}: {e}")
                continue

        logger.info(f"    Processed: {processed_count} samples, Errors: {error_count}")
        return samples

    def _scan_common_voice(self, cv_path: Path) -> List[Dict]:
        """Scan Common Voice dataset structure."""
        samples = []
        logger.info(f"Scanning Common Voice from: {cv_path}")

        # Common Voice typically has train.tsv, dev.tsv, test.tsv manifests
        tsv_files = list(cv_path.glob('*.tsv'))
        logger.info(f"Found {len(tsv_files)} TSV files")

        for tsv_file in tsv_files:
            try:
                logger.info(f"Processing TSV: {tsv_file}")
                df = pd.read_csv(tsv_file, sep='\t', on_bad_lines='skip')
                logger.info(f"  Loaded {len(df)} rows. Columns: {list(df.columns)}")

                # Common Voice columns: path, sentence, client_id
                path_col = next((c for c in ['path', 'audio_path', 'filename'] if c in df.columns), None)
                text_col = next((c for c in ['sentence', 'text', 'transcript'] if c in df.columns), None)
                speaker_col = next((c for c in ['client_id', 'speaker_id'] if c in df.columns), 'client_id')

                if not (path_col and text_col):
                    logger.warning(f"  Required columns not found in {tsv_file}")
                    continue

                # Look for clips directory
                clips_dir = cv_path / 'clips'
                if not clips_dir.exists():
                    logger.warning(f"  clips directory not found")
                    continue

                found_count = 0
                missing_count = 0

                for _, row in df.iterrows():
                    audio_filename = row[path_col]
                    text = row[text_col]
                    speaker_id = row.get(speaker_col, 'unknown')

                    if not isinstance(text, str) or not text.strip():
                        continue

                    audio_file = clips_dir / audio_filename
                    if audio_file.exists():
                        found_count += 1
                        samples.append({
                            'audio_path': str(audio_file),
                            'text': text.strip(),
                            'speaker_id': f"cv_{speaker_id}",
                            'language': 'tw',
                            'dataset': 'common_voice_twi',
                            'dialect': 'twi'
                        })
                    else:
                        missing_count += 1

                logger.info(f"  Found {found_count} audio files, missing {missing_count}")

            except Exception as e:
                logger.error(f"  Error processing {tsv_file}: {e}")
                logger.error(traceback.format_exc())
                continue

        logger.info(f"Total Common Voice samples: {len(samples)}")
        return samples

    def _add_audio_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add audio metadata to DataFrame."""
        print("   📊 Adding audio metadata...")

        metadata = []
        for audio_path in tqdm(df['audio_path'], desc="Audio metadata", leave=False):
            try:
                info = sf.info(audio_path)
                metadata.append({
                    'duration': info.duration,
                    'sample_rate': info.samplerate,
                    'channels': info.channels,
                    'audio_exists': True
                })
            except Exception:
                metadata.append({
                    'duration': 0.0,
                    'sample_rate': 0,
                    'channels': 0,
                    'audio_exists': False
                })

        meta_df = pd.DataFrame(metadata)
        df = pd.concat([df.reset_index(drop=True), meta_df], axis=1)

        return df

    def _process_text_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process text and add metadata."""
        print("   📝 Processing text metadata...")

        text_metadata = []
        for text in tqdm(df['text'], desc="Text processing", leave=False):
            processed = self.text_processor.process_text(text)
            text_metadata.append({
                'processed_text': processed['processed'],
                'text_length': processed['char_count'],
                'word_count': processed['word_count'],
                'has_twi_chars': processed['has_twi_chars']
            })

        text_df = pd.DataFrame(text_metadata)
        df = pd.concat([df.reset_index(drop=True), text_df], axis=1)

        return df

# --- AUDIO PROCESSOR ---
class MultiRateAudioProcessor:
    """Process audio at multiple sample rates."""

    def __init__(self, config: ProcessingConfig):
        self.config = config

    def process_for_all_rates(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Process dataset for all configured sample rates."""
        logger.info("=" * 80)
        logger.info("Starting multi-rate audio processing")
        logger.info("=" * 80)
        log_memory_usage()

        print("\n🎵 Processing audio for multiple sample rates...")

        # Apply quality filters
        logger.info("Applying quality filters")
        df_filtered = self._apply_quality_filters(df)
        logger.info(f"Filtered dataset size: {len(df_filtered)} samples")
        log_memory_usage()

        processed_datasets = {}

        for rate_category, sample_rate in self.config.sample_rates.items():
            logger.info("=" * 80)
            logger.info(f"PROCESSING: {rate_category} ({sample_rate}Hz)")
            logger.info("=" * 80)
            print(f"\n--- Processing {rate_category} ({sample_rate}Hz) ---")
            start_time = time.time()

            # Create output directory
            audio_dir = self.config.output_path / 'processed_audio' / rate_category
            logger.info(f"Output directory: {audio_dir}")
            audio_dir.mkdir(parents=True, exist_ok=True)

            processed_samples = []
            failed_count = 0

            for idx, row in enumerate(tqdm(df_filtered.iterrows(), total=len(df_filtered), desc=f"Processing {rate_category}")):
                _, row = row
                try:
                    # Log every 100th sample
                    if idx % 100 == 0:
                        logger.info(f"Progress: {idx}/{len(df_filtered)} samples processed for {rate_category}")
                        log_memory_usage()

                    # Load and resample audio
                    audio, sr = librosa.load(row['audio_path'], sr=sample_rate, mono=True)

                    # Normalize audio
                    audio = self._normalize_audio(audio)

                    # Create output filename
                    audio_stem = Path(row['audio_path']).stem
                    output_filename = f"{row['dialect']}_{row['speaker_id']}_{audio_stem}.wav"
                    output_path = audio_dir / output_filename

                    # Save processed audio
                    sf.write(output_path, audio, sample_rate)

                    # Create sample record
                    sample_data = row.to_dict()
                    sample_data.update({
                        'processed_audio_path': str(output_path),
                        'processed_sample_rate': sample_rate,
                        'processed_duration': len(audio) / sample_rate,
                        'rate_category': rate_category
                    })

                    processed_samples.append(sample_data)

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing {row['audio_path']}: {e}")
                    if failed_count <= 5:  # Only log full traceback for first 5 errors
                        logger.error(traceback.format_exc())
                    print(f"   ⚠️ Error processing {row['audio_path']}: {e}")
                    continue

            elapsed_time = time.time() - start_time
            logger.info(f"Completed {rate_category} in {elapsed_time:.2f} seconds")
            logger.info(f"Successfully processed: {len(processed_samples)} samples")
            logger.info(f"Failed: {failed_count} samples")
            log_memory_usage()

            if processed_samples:
                logger.info(f"Creating DataFrame for {rate_category}")
                processed_df = pd.DataFrame(processed_samples)
                processed_datasets[rate_category] = processed_df

                print(f"   ✅ Processed {len(processed_df)} samples for {rate_category}")

                # Save dataset manifest
                manifest_path = self.config.output_path / 'manifests' / f'{rate_category}_dataset.csv'
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Saving manifest to {manifest_path}")
                processed_df.to_csv(manifest_path, index=False)

                print(f"   📄 Manifest saved: {manifest_path}")
            else:
                logger.warning(f"No samples processed for {rate_category}")

        logger.info("Multi-rate audio processing complete")
        log_memory_usage()
        return processed_datasets

    def _apply_quality_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply quality filters to dataset."""
        print("   🔍 Applying quality filters...")

        initial_count = len(df)

        df_filtered = df[
            (df['audio_exists']) &
            (df['duration'] >= self.config.min_duration) &
            (df['duration'] <= self.config.max_duration) &
            (df['text_length'] >= self.config.min_text_length) &
            (df['text_length'] <= self.config.max_text_length)
        ].copy()

        retained_count = len(df_filtered)
        retention_rate = (retained_count / initial_count * 100) if initial_count > 0 else 0

        print(f"   Filtered: {initial_count} → {retained_count} samples ({retention_rate:.1f}% retained)")

        return df_filtered

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to target dB level."""
        rms = np.sqrt(np.mean(audio**2))

        if rms > 0:
            target_rms = 10**(self.config.target_db / 20)
            audio = audio * (target_rms / rms)
            audio = np.clip(audio, -1.0, 1.0)

        return audio

# --- MANIFEST GENERATOR ---
class ManifestGenerator:
    """Generate model-specific training manifests."""

    def __init__(self, config: ProcessingConfig):
        self.config = config

    def generate_all_manifests(self, processed_datasets: Dict[str, pd.DataFrame]):
        """Generate manifests for all model types."""
        logger.info("=" * 80)
        logger.info("Starting manifest generation")
        logger.info("=" * 80)

        print("\n📋 Generating model-specific manifests...")

        manifest_dir = self.config.output_path / 'model_manifests'
        manifest_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Manifest directory: {manifest_dir}")

        for rate_category, models in self.config.model_categories.items():
            if rate_category not in processed_datasets:
                logger.warning(f"No processed data for {rate_category}")
                print(f"   ⚠️ No processed data for {rate_category}")
                continue

            df = processed_datasets[rate_category]
            logger.info(f"Generating manifests for {rate_category} ({len(df)} samples)")

            for model_name in models:
                logger.info(f"Creating manifest for {model_name}")
                print(f"   📝 Creating manifest for {model_name}...")

                try:
                    if 'whisper' in model_name or 'wav2vec2' in model_name or 'mms' in model_name or 'moshi' in model_name:
                        self._create_asr_manifest(df, model_name, manifest_dir)
                    else:
                        self._create_tts_manifest(df, model_name, manifest_dir)
                    logger.info(f"  Successfully created manifest for {model_name}")
                except Exception as e:
                    logger.error(f"  Error creating manifest for {model_name}: {e}")
                    logger.error(traceback.format_exc())

    def _create_asr_manifest(self, df: pd.DataFrame, model_name: str, manifest_dir: Path):
        """Create ASR training manifest."""
        asr_data = []

        for _, row in df.iterrows():
            asr_data.append({
                'audio_path': row['processed_audio_path'],
                'transcript': row['processed_text'],
                'duration': row['processed_duration'],
                'speaker_id': row['speaker_id'],
                'language': row['language'],
                'dialect': row['dialect'],
                'dataset': row['dataset']
            })

        asr_df = pd.DataFrame(asr_data)

        # Create train/val splits
        train_df = asr_df.sample(frac=0.95, random_state=42)
        val_df = asr_df.drop(train_df.index)

        # Save manifests
        train_path = manifest_dir / f'{model_name}_train.csv'
        val_path = manifest_dir / f'{model_name}_val.csv'

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)

        print(f"     Train: {len(train_df)} samples → {train_path.name}")
        print(f"     Val: {len(val_df)} samples → {val_path.name}")

    def _create_tts_manifest(self, df: pd.DataFrame, model_name: str, manifest_dir: Path):
        """Create TTS training manifest."""
        tts_data = []

        for _, row in df.iterrows():
            if 'coqui' in model_name:
                # Coqui format: filepath|text|speaker_name
                rel_path = Path(row['processed_audio_path']).name
                tts_data.append(f"wavs/{rel_path}|{row['processed_text']}|{row['speaker_id']}")
            else:
                # Generic TTS format
                tts_data.append({
                    'audio_path': row['processed_audio_path'],
                    'text': row['processed_text'],
                    'speaker_id': row['speaker_id'],
                    'language': row['language'],
                    'dialect': row['dialect'],
                    'duration': row['processed_duration']
                })

        if 'coqui' in model_name:
            # Save as text file for Coqui
            train_lines = tts_data[:int(len(tts_data) * 0.95)]
            val_lines = tts_data[int(len(tts_data) * 0.95):]

            train_path = manifest_dir / f'{model_name}_train.txt'
            val_path = manifest_dir / f'{model_name}_val.txt'

            with open(train_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(train_lines))

            with open(val_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(val_lines))
        else:
            # Save as CSV
            tts_df = pd.DataFrame(tts_data)
            train_df = tts_df.sample(frac=0.95, random_state=42)
            val_df = tts_df.drop(train_df.index)

            train_path = manifest_dir / f'{model_name}_train.csv'
            val_path = manifest_dir / f'{model_name}_val.csv'

            train_df.to_csv(train_path, index=False)
            val_df.to_csv(val_path, index=False)

        print(f"     Manifests saved for {model_name}")

# --- MAIN PIPELINE ---
def main():
    """Main processing pipeline."""
    logger.info("=" * 80)
    logger.info("TWI DATA PROCESSING PIPELINE STARTED")
    logger.info("=" * 80)
    logger.info(f"Log file: {LOG_FILE}")
    log_memory_usage()

    print("=" * 80)
    print("🚀 TWI DATA PROCESSING PIPELINE")
    print("=" * 80)
    print(f"📝 Log file: {LOG_FILE}")

    try:
        # Initialize configuration
        BASE_PATH = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante/raw')
        OUTPUT_PATH = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed')

        logger.info(f"Base path: {BASE_PATH}")
        logger.info(f"Output path: {OUTPUT_PATH}")

        config = ProcessingConfig(
            base_path=BASE_PATH,
            output_path=OUTPUT_PATH
        )

        print(f"\n🔧 Configuration:")
        print(f"   Base path: {config.base_path}")
        print(f"   Output path: {config.output_path}")
        print(f"   Sample rates: {config.sample_rates}")

        # Step 1: Load data
        print("\n" + "=" * 80)
        print("STEP 1: LOADING DATASETS")
        print("=" * 80)
        logger.info("STEP 1: LOADING DATASETS")

        loader = TwiDataLoader(config)
        raw_dataset = loader.scan_all_datasets()
    except Exception as e:
        logger.error(f"FATAL ERROR in data loading: {e}")
        logger.error(traceback.format_exc())
        raise

    logger.info("Data loading completed successfully")
    print(f"\n📊 Raw Dataset Summary:")
    print(f"   Total samples: {len(raw_dataset):,}")
    print(f"   Unique speakers: {raw_dataset['speaker_id'].nunique():,}")
    print(f"   Datasets: {list(raw_dataset['dataset'].unique())}")
    print(f"   Dialects: {list(raw_dataset['dialect'].unique())}")
    print(f"   Total duration: {raw_dataset['duration'].sum()/3600:.1f} hours")
    logger.info(f"Raw dataset: {len(raw_dataset)} samples, {raw_dataset['duration'].sum()/3600:.1f} hours")

    # Step 2: Process audio
    try:
        print("\n" + "=" * 80)
        print("STEP 2: PROCESSING AUDIO")
        print("=" * 80)
        logger.info("STEP 2: PROCESSING AUDIO")

        processor = MultiRateAudioProcessor(config)
        processed_datasets = processor.process_for_all_rates(raw_dataset)

        logger.info(f"Audio processing completed. Processed {len(processed_datasets)} sample rate categories")
    except Exception as e:
        logger.error(f"FATAL ERROR in audio processing: {e}")
        logger.error(traceback.format_exc())
        raise

    # Step 3: Generate manifests
    try:
        print("\n" + "=" * 80)
        print("STEP 3: GENERATING MANIFESTS")
        print("=" * 80)
        logger.info("STEP 3: GENERATING MANIFESTS")

        manifest_gen = ManifestGenerator(config)
        manifest_gen.generate_all_manifests(processed_datasets)

        logger.info("Manifest generation completed")
    except Exception as e:
        logger.error(f"FATAL ERROR in manifest generation: {e}")
        logger.error(traceback.format_exc())
        raise

    # Step 4: Summary
    print("\n" + "=" * 80)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 80)

    print(f"\n📋 Summary:")
    print(f"   Raw samples: {len(raw_dataset):,}")
    total_processed = sum(len(df) for df in processed_datasets.values())
    print(f"   Processed samples: {total_processed:,}")
    print(f"   Sample rate categories: {len(processed_datasets)}")
    logger.info(f"Total processed samples: {total_processed}")

    for rate_category, df in processed_datasets.items():
        total_duration = df['processed_duration'].sum() / 3600
        print(f"\n   {rate_category}:")
        print(f"     - Samples: {len(df):,}")
        print(f"     - Duration: {total_duration:.1f} hours")
        print(f"     - Sample rate: {config.sample_rates[rate_category]}Hz")
        logger.info(f"{rate_category}: {len(df)} samples, {total_duration:.1f} hours")

    print(f"\n📁 Output directories:")
    print(f"   Processed audio: {config.output_path / 'processed_audio'}")
    print(f"   Manifests: {config.output_path / 'manifests'}")
    print(f"   Model manifests: {config.output_path / 'model_manifests'}")

    # Save processing metadata
    try:
        metadata = {
            'processing_date': datetime.now().isoformat(),
            'total_raw_samples': len(raw_dataset),
            'total_processed_samples': total_processed,
            'sample_rates': config.sample_rates,
            'datasets': raw_dataset['dataset'].value_counts().to_dict(),
            'dialects': raw_dataset['dialect'].value_counts().to_dict(),
            'total_hours': raw_dataset['duration'].sum() / 3600
        }

        metadata_path = config.output_path / 'processing_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n💾 Metadata saved: {metadata_path}")
        logger.info(f"Metadata saved to {metadata_path}")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")
        logger.error(traceback.format_exc())

    print("\n" + "=" * 80)
    print("🏁 PIPELINE FINISHED SUCCESSFULLY!")
    print("=" * 80)
    logger.info("=" * 80)
    logger.info("PIPELINE FINISHED SUCCESSFULLY!")
    logger.info("=" * 80)
    logger.info(f"Total execution time logged. Check {LOG_FILE} for details")

if __name__ == "__main__":
    main()

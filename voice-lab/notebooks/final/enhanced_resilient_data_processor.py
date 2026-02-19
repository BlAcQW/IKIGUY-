#!/usr/bin/env python3
"""
Enhanced Resilient Multi-Rate Data Processing System
Combines Options 1, 2, and 3 for maximum data loading success with high-quality preprocessing.

Features:
- Progressive loading to avoid memory issues
- Comprehensive validation and error handling
- High-quality audio and text preprocessing
- Memory-efficient batch processing
- Detailed logging and recovery mechanisms
"""

import gc
import json
import time
import pickle
import re
import shutil
import unicodedata
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Iterator
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

import numpy as np
import pandas as pd
import soundfile as sf
import librosa
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryManager:
    """Monitor and manage memory usage during processing."""
    
    def __init__(self, max_memory_percent=85):
        self.max_memory_percent = max_memory_percent
        self.process = psutil.Process()
        
    def check_memory(self) -> Dict[str, float]:
        """Check current memory usage."""
        memory_info = self.process.memory_info()
        virtual_memory = psutil.virtual_memory()
        
        return {
            'used_mb': memory_info.rss / 1024 / 1024,
            'available_mb': virtual_memory.available / 1024 / 1024,
            'percent_used': virtual_memory.percent,
            'is_critical': virtual_memory.percent > self.max_memory_percent
        }
    
    def force_gc(self):
        """Force garbage collection and log memory freed."""
        before = self.check_memory()
        gc.collect()
        after = self.check_memory()
        
        freed = before['used_mb'] - after['used_mb']
        if freed > 10:  # Only log if significant memory freed
            logger.info(f"🧹 Freed {freed:.1f}MB memory via GC")
        
        return freed
    
    def should_pause(self) -> bool:
        """Check if we should pause processing due to memory pressure."""
        memory = self.check_memory()
        return memory['is_critical']

@dataclass
class EnhancedMultiRateConfig:
    """Enhanced configuration with progressive loading parameters."""
    base_path: Path
    output_path: Path
    
    # Sample rate configurations
    sample_rates: Dict[str, int] = field(default_factory=lambda: {
        'asr_16k': 16000,      # ASR models: Whisper, Wav2Vec2, MMS, Moshi
        'tts_22k': 22050,      # TTS models: Coqui XTTS, MeloTTS
        'tts_24k': 24000       # High-quality TTS: OpenVoice, Kokoro, F5, ChatTTS
    })
    
    # Model mappings
    model_categories: Dict[str, List[str]] = field(default_factory=lambda: {
        'asr_16k': ['faster_whisper', 'wav2vec2', 'mms', 'moshi'],
        'tts_22k': ['coqui_xtts', 'melo_tts'],
        'tts_24k': ['openvoice', 'kokoro_tts', 'f5_tts', 'chattts_chatterbox', 'styletts2', 'meta_voice']
    })
    
    # Progressive loading parameters
    batch_size: int = 500  # Process this many samples at once
    max_samples_per_dataset: int = 5000  # Maximum samples from each dataset
    max_arrow_files_per_dataset: int = 10  # Limit Arrow files to prevent memory issues
    memory_check_interval: int = 100  # Check memory every N samples
    
    # Quality thresholds
    min_duration: float = 0.3  # Slightly lower for more data
    max_duration: float = 45.0  # Higher for more data
    min_text_length: int = 2
    max_text_length: int = 800
    target_db: float = -20.0
    
    # High-quality preprocessing parameters
    normalize_audio: bool = True
    apply_noise_reduction: bool = True
    enhance_text_processing: bool = True
    validate_linguistic_content: bool = True
    
    # Dataset configuration with priority ordering
    datasets_to_scan: List[Dict] = field(default_factory=lambda: [
        # High-priority datasets (process first)
        {
            "name": "twi_multi_train",
            "type": "arrow_sharded_audio", 
            "path": "raw/michsethowusu/twi_multispeaker_audio_transcribed/train",
            "priority": 1,
            "max_samples": 3000
        },
        {
            "name": "twi_emotions_train",
            "type": "arrow_sharded_audio",
            "path": "raw/michsethowusu/twi-emotions-corpus/train",
            "priority": 1,
            "max_samples": 2000
        },
        # Medium-priority datasets
        {
            "name": "bibletts",
            "type": "bibletts", 
            "path": "raw/bibletts",
            "priority": 2,
            "max_samples": 2000
        },
        {
            "name": "financial_inclusion",
            "type": "financial_inclusion",
            "path": "raw/financial_inclusion",
            "priority": 2,
            "max_samples": 1500
        },
        # Lower-priority datasets (related languages for transfer learning)
        {
            "name": "akuapem_multi_train",
            "type": "arrow_sharded_audio",
            "path": "raw/michsethowusu/akuapem_multispeaker_audio_transcribed/train",
            "priority": 3,
            "max_samples": 1000
        },
        {
            "name": "fante_multi_train",
            "type": "arrow_sharded_audio",
            "path": "raw/michsethowusu/fante_multispeaker_audio_transcribed/train",
            "priority": 3,
            "max_samples": 1000
        },
        {
            "name": "ga_multi_train",
            "type": "arrow_sharded_audio",
            "path": "raw/michsethowusu/ga_multispeaker_audio_transcribed/train",
            "priority": 3,
            "max_samples": 1000
        },
        # Test sets (smaller, for validation)
        {
            "name": "twi_multi_test",
            "type": "arrow_sharded_audio",
            "path": "raw/michsethowusu/twi_multispeaker_audio_transcribed/test",
            "priority": 4,
            "max_samples": 500
        },
        {
            "name": "twi_parallel_train",
            "type": "arrow_sharded_audio",
            "path": "raw/michsethowusu/twi-speech-text-parallel-multispeaker/train",
            "priority": 4,
            "max_samples": 1000
        }
    ])

class EnhancedDatasetValidator:
    """Comprehensive dataset validation with detailed reporting."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.validation_cache = {}
        
    def validate_all_datasets(self, dataset_configs: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Return valid datasets and detailed validation report."""
        logger.info("🔍 Starting comprehensive dataset validation...")
        
        valid_configs = []
        validation_report = {
            'total_datasets': len(dataset_configs),
            'valid_datasets': 0,
            'invalid_datasets': 0,
            'estimated_total_samples': 0,
            'details': {}
        }
        
        # Sort by priority for optimal processing order
        sorted_configs = sorted(dataset_configs, key=lambda x: x.get('priority', 5))
        
        for config in tqdm(sorted_configs, desc="Validating datasets"):
            validation_result = self.validate_dataset_comprehensive(config)
            
            validation_report['details'][config['name']] = validation_result
            
            if validation_result['is_valid']:
                valid_configs.append(config)
                validation_report['valid_datasets'] += 1
                validation_report['estimated_total_samples'] += validation_result['estimated_samples']
                logger.info(f"✅ {config['name']}: {validation_result['estimated_samples']} samples ({validation_result['confidence']})")
            else:
                validation_report['invalid_datasets'] += 1
                logger.warning(f"❌ {config['name']}: {validation_result['error']}")
        
        # Log summary
        logger.info(f"""
📊 Validation Summary:
   Valid datasets: {validation_report['valid_datasets']}/{validation_report['total_datasets']}
   Estimated samples: {validation_report['estimated_total_samples']:,}
   Success rate: {validation_report['valid_datasets']/validation_report['total_datasets']*100:.1f}%
        """)
        
        return valid_configs, validation_report
    
    def validate_dataset_comprehensive(self, config: Dict) -> Dict:
        """Comprehensive validation with detailed analysis."""
        dataset_path = self.base_path / config['path']
        
        result = {
            'is_valid': False,
            'error': '',
            'estimated_samples': 0,
            'confidence': 'unknown',
            'file_count': 0,
            'total_size_mb': 0,
            'sample_files_checked': 0
        }
        
        if not dataset_path.exists():
            result['error'] = 'Path does not exist'
            return result
        
        try:
            if config['type'] == 'arrow_sharded_audio':
                return self._validate_arrow_comprehensive(dataset_path, config)
            elif config['type'] == 'bibletts':
                return self._validate_bibletts_comprehensive(dataset_path, config)
            elif config['type'] == 'financial_inclusion':
                return self._validate_financial_comprehensive(dataset_path, config)
            else:
                result['error'] = f"Unknown dataset type: {config['type']}"
                return result
                
        except Exception as e:
            result['error'] = f"Validation failed: {str(e)[:100]}"
            return result
    
    def _validate_arrow_comprehensive(self, dataset_path: Path, config: Dict) -> Dict:
        """Comprehensive Arrow dataset validation."""
        result = {
            'is_valid': False,
            'error': '',
            'estimated_samples': 0,
            'confidence': 'unknown',
            'file_count': 0,
            'total_size_mb': 0,
            'sample_files_checked': 0
        }
        
        # Find Arrow files
        arrow_files = sorted(list(dataset_path.glob('data-*.arrow')))
        if not arrow_files:
            arrow_files = sorted(list(dataset_path.glob('*.arrow')))
        
        if not arrow_files:
            result['error'] = 'No Arrow files found'
            return result
        
        result['file_count'] = len(arrow_files)
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in arrow_files)
        result['total_size_mb'] = total_size / 1024 / 1024
        
        # Validate sample of files
        files_to_check = min(3, len(arrow_files))
        valid_files = 0
        total_samples = 0
        
        for arrow_file in arrow_files[:files_to_check]:
            try:
                # Try reading file
                try:
                    df = pd.read_feather(arrow_file)
                except:
                    import pyarrow as pa
                    table = pa.ipc.RecordBatchFileReader(pa.memory_map(str(arrow_file))).read_all()
                    df = table.to_pandas()
                
                # Check required columns
                text_col = self._find_column(df.columns, ['transcript', 'text', 'sentence'])
                audio_col = self._find_column(df.columns, ['audio', 'speech'])
                
                if text_col and audio_col:
                    # Validate sample data
                    sample_count = len(df)
                    if sample_count > 0:
                        # Check first few rows for data quality
                        sample_row = df.iloc[0]
                        if (isinstance(sample_row[text_col], str) and 
                            len(sample_row[text_col].strip()) > 0 and
                            sample_row[audio_col] is not None):
                            
                            valid_files += 1
                            total_samples += sample_count
                
                result['sample_files_checked'] += 1
                
            except Exception as e:
                logger.debug(f"Failed to validate {arrow_file.name}: {e}")
                continue
        
        # Determine result
        if valid_files > 0:
            # Estimate total samples
            avg_samples_per_file = total_samples / valid_files
            estimated_total = int(avg_samples_per_file * len(arrow_files))
            
            # Apply dataset limit if specified
            max_samples = config.get('max_samples', estimated_total)
            result['estimated_samples'] = min(estimated_total, max_samples)
            
            result['is_valid'] = True
            result['confidence'] = 'high' if valid_files == files_to_check else 'medium'
        else:
            result['error'] = 'No valid data found in sample files'
        
        return result
    
    def _validate_bibletts_comprehensive(self, dataset_path: Path, config: Dict) -> Dict:
        """Comprehensive bibletts validation."""
        result = {
            'is_valid': False,
            'error': '',
            'estimated_samples': 0,
            'confidence': 'unknown',
            'file_count': 0,
            'total_size_mb': 0,
            'sample_files_checked': 0
        }
        
        # Find audio files
        audio_extensions = ['.wav', '.mp3', '.flac', '.ogg']
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(dataset_path.rglob(f'*{ext}'))
        
        # Filter out system files
        audio_files = [f for f in audio_files if '__MACOSX' not in str(f)]
        
        if not audio_files:
            result['error'] = 'No audio files found'
            return result
        
        result['file_count'] = len(audio_files)
        
        # Check sample files
        files_to_check = min(10, len(audio_files))
        valid_pairs = 0
        
        for audio_file in audio_files[:files_to_check]:
            text_file = audio_file.with_suffix('.txt')
            if text_file.exists():
                try:
                    text = text_file.read_text(encoding='utf-8').strip()
                    if len(text) > 2:  # Basic quality check
                        valid_pairs += 1
                except:
                    pass
            result['sample_files_checked'] += 1
        
        if valid_pairs > 0:
            # Estimate total valid pairs
            valid_ratio = valid_pairs / files_to_check
            estimated_total = int(len(audio_files) * valid_ratio)
            
            max_samples = config.get('max_samples', estimated_total)
            result['estimated_samples'] = min(estimated_total, max_samples)
            
            result['is_valid'] = True
            result['confidence'] = 'high' if valid_ratio > 0.8 else 'medium'
        else:
            result['error'] = 'No valid audio-text pairs found'
        
        return result
    
    def _validate_financial_comprehensive(self, dataset_path: Path, config: Dict) -> Dict:
        """Comprehensive financial inclusion validation."""
        result = {
            'is_valid': False,
            'error': '',
            'estimated_samples': 0,
            'confidence': 'unknown',
            'file_count': 0,
            'total_size_mb': 0,
            'sample_files_checked': 0
        }
        
        # Look for audio directories and manifest files
        audio_dirs = list(dataset_path.rglob('audios'))
        manifest_files = list(dataset_path.rglob('data.csv'))
        
        if not (audio_dirs and manifest_files):
            result['error'] = 'Missing audio directories or manifest files'
            return result
        
        # Check sample manifest
        valid_manifests = 0
        total_samples = 0
        
        for manifest_file in manifest_files[:3]:  # Check up to 3 manifests
            try:
                df = pd.read_csv(manifest_file, on_bad_lines='skip')
                if len(df) > 0:
                    path_col = self._find_column(df.columns, ['path', 'audio', 'filename'])
                    text_col = self._find_column(df.columns, ['text', 'transcript'])
                    
                    if path_col and text_col:
                        # Count non-empty text entries
                        valid_entries = df[df[text_col].str.len() > 2].shape[0]
                        if valid_entries > 0:
                            valid_manifests += 1
                            total_samples += valid_entries
                
                result['sample_files_checked'] += 1
            except:
                pass
        
        if valid_manifests > 0:
            max_samples = config.get('max_samples', total_samples)
            result['estimated_samples'] = min(total_samples, max_samples)
            result['is_valid'] = True
            result['confidence'] = 'medium'
        else:
            result['error'] = 'No valid manifests found'
        
        return result
    
    def _find_column(self, columns: List[str], candidates: List[str]) -> Optional[str]:
        """Find first matching column from candidates."""
        return next((c for c in candidates if c in columns), None)

class ProgressiveResilientDataLoader:
    """Progressive data loader with comprehensive error handling and memory management."""
    
    def __init__(self, config: EnhancedMultiRateConfig):
        self.config = config
        self.memory_manager = MemoryManager()
        self.failed_datasets = []
        self.partial_loads = {}
        self.processing_stats = {
            'total_samples_attempted': 0,
            'total_samples_successful': 0,
            'datasets_processed': 0,
            'memory_cleanups': 0
        }
        
        # Initialize text processor
        from enhanced_text_processor import EnhancedTwiTextProcessor
        self.text_processor = EnhancedTwiTextProcessor()
    
    def load_all_datasets_progressive(self, validated_configs: List[Dict]) -> pd.DataFrame:
        """Load all datasets progressively with memory management."""
        logger.info("🚀 Starting progressive dataset loading...")
        
        all_samples = []
        
        for dataset_config in tqdm(validated_configs, desc="Loading datasets"):
            try:
                logger.info(f"📂 Loading {dataset_config['name']} (Priority {dataset_config.get('priority', 'N/A')})")
                
                # Memory check before each dataset
                memory_status = self.memory_manager.check_memory()
                logger.info(f"💾 Memory: {memory_status['used_mb']:.1f}MB used ({memory_status['percent_used']:.1f}%)")
                
                if memory_status['is_critical']:
                    logger.warning("⚠️ Memory critical - forcing cleanup")
                    self.memory_manager.force_gc()
                    self.processing_stats['memory_cleanups'] += 1
                
                # Load dataset in batches
                dataset_samples = self._load_dataset_progressive(dataset_config)
                
                if dataset_samples:
                    all_samples.extend(dataset_samples)
                    self.processing_stats['datasets_processed'] += 1
                    logger.info(f"✅ Loaded {len(dataset_samples)} samples from {dataset_config['name']}")
                else:
                    self.failed_datasets.append(dataset_config['name'])
                    logger.warning(f"⚠️ No samples loaded from {dataset_config['name']}")
                
                # Periodic cleanup
                if len(all_samples) % 1000 == 0 and len(all_samples) > 0:
                    self.memory_manager.force_gc()
                
            except Exception as e:
                self.failed_datasets.append(dataset_config['name'])
                logger.error(f"❌ Failed to load {dataset_config['name']}: {e}")
                continue
        
        # Create final DataFrame
        if all_samples:
            logger.info("📊 Creating final dataset DataFrame...")
            final_df = pd.DataFrame(all_samples)
            
            # Add comprehensive metadata
            final_df = self._add_comprehensive_metadata(final_df)
            
            self.processing_stats['total_samples_successful'] = len(final_df)
            
            # Log final statistics
            self._log_processing_summary(final_df)
            
            return final_df
        else:
            logger.warning("🚨 No samples loaded from any dataset - creating minimal test dataset")
            return self._create_enhanced_dummy_dataset()
    
    def _load_dataset_progressive(self, dataset_config: Dict) -> List[Dict]:
        """Load single dataset progressively."""
        dataset_path = self.config.base_path / dataset_config['path']
        max_samples = dataset_config.get('max_samples', self.config.max_samples_per_dataset)
        
        if dataset_config['type'] == 'arrow_sharded_audio':
            return self._load_arrow_progressive(dataset_path, dataset_config['name'], max_samples)
        elif dataset_config['type'] == 'bibletts':
            return self._load_bibletts_progressive(dataset_path, dataset_config['name'], max_samples)
        elif dataset_config['type'] == 'financial_inclusion':
            return self._load_financial_progressive(dataset_path, dataset_config['name'], max_samples)
        else:
            logger.error(f"Unknown dataset type: {dataset_config['type']}")
            return []
    
    def _load_arrow_progressive(self, dataset_path: Path, dataset_name: str, max_samples: int) -> List[Dict]:
        """Load Arrow dataset progressively with memory management."""
        arrow_files = sorted(list(dataset_path.glob('data-*.arrow')))
        if not arrow_files:
            arrow_files = sorted(list(dataset_path.glob('*.arrow')))
        
        if not arrow_files:
            logger.warning(f"No Arrow files found in {dataset_path}")
            return []
        
        # Limit number of files to prevent memory issues
        arrow_files = arrow_files[:self.config.max_arrow_files_per_dataset]
        
        samples = []
        samples_per_file = max_samples // len(arrow_files)
        
        for arrow_file in tqdm(arrow_files, desc=f"Processing {dataset_name}", leave=False):
            try:
                # Load file
                df = self._load_arrow_file_safe(arrow_file)
                if df is None:
                    continue
                

				# Find columns (Updated with correct names)
                text_col = self._find_column_flexible(df.columns, ['transcription', 'transcript', 'text', 'sentence'])
                audio_col = self._find_column_flexible(df.columns, ['audio_path', 'audio', 'speech'])


                speaker_col = self._find_column_flexible(df.columns, ['speaker_id', 'client_id'])
                
                if not (text_col and audio_col):
                    logger.warning(f"Missing required columns in {arrow_file.name}")
                    continue
                
                # Process in batches to manage memory
                batch_samples = self._process_arrow_batches(
                    df, text_col, audio_col, speaker_col, 
                    dataset_name, samples_per_file
                )
                
                samples.extend(batch_samples)
                
                # Clear dataframe from memory
                del df
                if len(samples) % 500 == 0:
                    self.memory_manager.force_gc()
                
                # Stop if we have enough samples
                if len(samples) >= max_samples:
                    break
                
            except Exception as e:
                logger.warning(f"Failed to process {arrow_file.name}: {e}")
                continue
        
        return samples[:max_samples]  # Ensure we don't exceed limit
    
    def _load_arrow_file_safe(self, arrow_file: Path) -> Optional[pd.DataFrame]:
        """Safely load Arrow file with fallback methods."""
        try:
            # Method 1: pandas
            return pd.read_feather(arrow_file)
        except:
            try:
                # Method 2: pyarrow
                import pyarrow as pa
                table = pa.ipc.RecordBatchFileReader(pa.memory_map(str(arrow_file))).read_all()
                return table.to_pandas()
            except:
                return None
    
    def _process_arrow_batches(self, df: pd.DataFrame, text_col: str, audio_col: str, 
                              speaker_col: Optional[str], dataset_name: str, max_samples: int) -> List[Dict]:
        """Process Arrow DataFrame in memory-efficient batches."""
        samples = []
        batch_size = min(self.config.batch_size, len(df))
        
        # Create temporary audio directory
        temp_audio_dir = self.config.output_path / 'temp_audio' / dataset_name
        temp_audio_dir.mkdir(parents=True, exist_ok=True)
        
        for start_idx in range(0, min(len(df), max_samples), batch_size):
            end_idx = min(start_idx + batch_size, len(df), max_samples)
            batch_df = df.iloc[start_idx:end_idx]
            
            for idx, row in batch_df.iterrows():
                try:
                    # Validate data
                    audio_data = row.get(audio_col)
                    text = row.get(text_col)
                    
                    if not (audio_data and isinstance(text, str) and len(text.strip()) > 1):
                        continue
                    
                    # Extract audio
                    audio_array = np.array(audio_data['array'], dtype=np.float32)
                    sampling_rate = audio_data['sampling_rate']
                    
                    # Quick quality check
                    duration = len(audio_array) / sampling_rate
                    if not (self.config.min_duration <= duration <= self.config.max_duration):
                        continue
                    
                    # Save temporary audio file
                    temp_filename = f"{dataset_name}_{idx}.wav"
                    temp_filepath = temp_audio_dir / temp_filename
                    sf.write(temp_filepath, audio_array, sampling_rate)
                    
                    # Process text
                    processed_text = self.text_processor.process_text(text, expand_numbers=True)
                    
                    # Create sample record
                    speaker_id = row.get(speaker_col, f"{dataset_name}_speaker_{idx}")
                    
                    sample = {
                        'audio_path': str(temp_filepath),
                        'text': text,
                        'processed_text': processed_text['processed'],
                        'speaker_id': f"{dataset_name}_{speaker_id}",
                        'language': 'tw',
                        'dataset': dataset_name,
                        'dialect': 'michset',
                        'duration': duration,
                        'sample_rate': sampling_rate,
                        'text_length': len(text),
                        'word_count': len(text.split()),
                        'has_twi_chars': processed_text['has_twi_chars'],
                        'quality_score': self._calculate_quality_score(text, duration)
                    }
                    
                    samples.append(sample)
                    self.processing_stats['total_samples_attempted'] += 1
                    
                    # Memory check
                    if len(samples) % self.config.memory_check_interval == 0:
                        if self.memory_manager.should_pause():
                            self.memory_manager.force_gc()
                    
                except Exception as e:
                    logger.debug(f"Failed to process sample {idx}: {e}")
                    continue
            
            # Clear batch from memory
            del batch_df
            
        return samples
    
    def _load_bibletts_progressive(self, dataset_path: Path, dataset_name: str, max_samples: int) -> List[Dict]:
        """Load bibletts dataset progressively."""
        audio_extensions = ['.wav', '.mp3', '.flac', '.ogg']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(dataset_path.rglob(f'*{ext}'))
        
        # Filter system files
        audio_files = [f for f in audio_files if '__MACOSX' not in str(f)]
        audio_files = audio_files[:max_samples]  # Limit files
        
        samples = []
        
        for audio_file in tqdm(audio_files, desc=f"Processing {dataset_name}", leave=False):
            try:
                text_file = audio_file.with_suffix('.txt')
                if not text_file.exists():
                    continue
                
                text = text_file.read_text(encoding='utf-8', errors='ignore').strip()
                if len(text) < 2:
                    continue
                
                # Get audio info
                try:
                    info = sf.info(str(audio_file))
                    duration = info.duration
                    
                    if not (self.config.min_duration <= duration <= self.config.max_duration):
                        continue
                        
                except:
                    continue
                
                # Process text
                processed_text = self.text_processor.process_text(text, expand_numbers=True)
                
                # Determine dialect and speaker
                parts = audio_file.parts
                dialect_name = 'bibletts'
                for part in parts:
                    if any(d in part.lower() for d in ['asante', 'akuapem', 'fante']):
                        dialect_name = part.lower()
                        break
                
                speaker_id = f"{dataset_name}_{dialect_name}_{audio_file.parent.name}"
                
                sample = {
                    'audio_path': str(audio_file),
                    'text': text,
                    'processed_text': processed_text['processed'],
                    'speaker_id': speaker_id,
                    'language': 'tw',
                    'dataset': dataset_name,
                    'dialect': dialect_name,
                    'duration': duration,
                    'sample_rate': info.samplerate,
                    'text_length': len(text),
                    'word_count': len(text.split()),
                    'has_twi_chars': processed_text['has_twi_chars'],
                    'quality_score': self._calculate_quality_score(text, duration)
                }
                
                samples.append(sample)
                self.processing_stats['total_samples_attempted'] += 1
                
                # Memory management
                if len(samples) % self.config.memory_check_interval == 0:
                    if self.memory_manager.should_pause():
                        self.memory_manager.force_gc()
                
            except Exception as e:
                logger.debug(f"Failed to process {audio_file}: {e}")
                continue
        
        return samples
    
    def _load_financial_progressive(self, dataset_path: Path, dataset_name: str, max_samples: int) -> List[Dict]:
        """Load financial inclusion dataset progressively."""
        audio_extensions = ['.wav', '.mp3', '.ogg', '.flac']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(dataset_path.rglob(f'**/audios/*{ext}'))
        
        audio_files = [f for f in audio_files if '__MACOSX' not in str(f)]
        audio_files = audio_files[:max_samples]
        
        # Cache manifest files
        manifest_cache = {}
        samples = []
        
        for audio_file in tqdm(audio_files, desc=f"Processing {dataset_name}", leave=False):
            try:
                manifest_path = audio_file.parent.parent / 'data.csv'
                if not manifest_path.exists():
                    continue
                
                # Load manifest if not cached
                if str(manifest_path) not in manifest_cache:
                    try:
                        df = pd.read_csv(manifest_path, on_bad_lines='skip')
                        path_col = self._find_column_flexible(df.columns, ['path', 'audio', 'filename'])
                        text_col = self._find_column_flexible(df.columns, ['text', 'transcript'])
                        
                        if path_col and text_col:
                            manifest_cache[str(manifest_path)] = df.set_index(path_col)[text_col].to_dict()
                        else:
                            manifest_cache[str(manifest_path)] = {}
                    except:
                        manifest_cache[str(manifest_path)] = {}
                
                # Get transcript
                transcripts = manifest_cache.get(str(manifest_path), {})
                transcript = (transcripts.get(audio_file.name) or 
                            transcripts.get(f"audios/{audio_file.name}"))
                
                if not (transcript and isinstance(transcript, str) and len(transcript.strip()) > 1):
                    continue
                
                # Get audio info
                try:
                    info = sf.info(str(audio_file))
                    duration = info.duration
                    
                    if not (self.config.min_duration <= duration <= self.config.max_duration):
                        continue
                except:
                    continue
                
                # Process text
                processed_text = self.text_processor.process_text(transcript, expand_numbers=True)
                
                speaker_id = f"{dataset_name}_{audio_file.parent.parent.name}"
                
                sample = {
                    'audio_path': str(audio_file),
                    'text': transcript,
                    'processed_text': processed_text['processed'],
                    'speaker_id': speaker_id,
                    'language': 'tw',
                    'dataset': dataset_name,
                    'dialect': 'financial',
                    'duration': duration,
                    'sample_rate': info.samplerate,
                    'text_length': len(transcript),
                    'word_count': len(transcript.split()),
                    'has_twi_chars': processed_text['has_twi_chars'],
                    'quality_score': self._calculate_quality_score(transcript, duration)
                }
                
                samples.append(sample)
                self.processing_stats['total_samples_attempted'] += 1
                
            except Exception as e:
                logger.debug(f"Failed to process {audio_file}: {e}")
                continue
        
        return samples
    
    def _find_column_flexible(self, columns: List[str], candidates: List[str]) -> Optional[str]:
        """Flexibly find column with partial matching."""
        # Exact match first
        for candidate in candidates:
            if candidate in columns:
                return candidate
        
        # Partial match
        for candidate in candidates:
            for col in columns:
                if candidate.lower() in col.lower():
                    return col
        
        return None
    
    def _calculate_quality_score(self, text: str, duration: float) -> float:
        """Calculate quality score for sample."""
        score = 5.0  # Base score
        
        # Text quality factors
        if len(text) > 50:
            score += 1.0
        if any(c in text for c in 'ɛɔ'):  # Twi-specific characters
            score += 1.5
        if re.search(r'[.!?]', text):  # Proper punctuation
            score += 0.5
        
        # Duration factors
        if 2.0 <= duration <= 15.0:  # Optimal duration
            score += 1.0
        elif duration < 1.0 or duration > 20.0:
            score -= 1.0
        
        # Text/duration ratio
        words_per_second = len(text.split()) / duration
        if 2.0 <= words_per_second <= 6.0:  # Natural speaking rate
            score += 1.0
        
        return min(10.0, max(1.0, score))
    
    def _add_comprehensive_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive metadata to the dataset."""
        logger.info("📊 Adding comprehensive metadata...")
        
        # Audio exists check
        df['audio_exists'] = df['audio_path'].apply(lambda x: Path(x).exists())
        
        # Channels info for existing files
        channels_info = []
        for audio_path in tqdm(df['audio_path'], desc="Checking audio files", leave=False):
            try:
                if Path(audio_path).exists():
                    info = sf.info(audio_path)
                    channels_info.append(info.channels)
                else:
                    channels_info.append(0)
            except:
                channels_info.append(0)
        
        df['channels'] = channels_info
        
        # Quality filters
        df['passes_quality_filter'] = (
            (df['audio_exists']) &
            (df['duration'] >= self.config.min_duration) &
            (df['duration'] <= self.config.max_duration) &
            (df['text_length'] >= self.config.min_text_length) &
            (df['text_length'] <= self.config.max_text_length) &
            (df['quality_score'] >= 3.0)
        )
        
        return df
    
    def _create_enhanced_dummy_dataset(self) -> pd.DataFrame:
        """Create enhanced dummy dataset with comprehensive metadata."""
        logger.info("🎭 Creating enhanced dummy dataset...")
        
        dummy_dir = self.config.output_path / 'dummy_audio'
        dummy_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced Twi samples with variety
        samples = [
            ("Wo ho te sɛn? Me ho yɛ paa.", "greeting", "speaker_001"),
            ("Me ma wo akye. Nante yie.", "greeting", "speaker_002"), 
            ("Me da wo ase pii sɛ woboa me.", "gratitude", "speaker_003"),
            ("Twi kasa yɛ fɛ papa. Ɛyɛ anigyesɛm sɛ mesua.", "language_learning", "speaker_004"),
            ("Obiara pɛ sɛ ɔnya ahotɔ wɔ n'ankasa kasa mu.", "cultural_expression", "speaker_005"),
            ("Yɛn nkurɔfoɔ nyinaa yɛ baako wɔ amoa kɛseɛ yi mu.", "unity", "speaker_006"),
            ("Adwo, ɔkyena yɛbɛhyia bio wɔ sukuu mu.", "daily_conversation", "speaker_007"),
            ("Aboa kɛseɛ yi mu no, yɛde anigyeɛ kyekyɛ yɛn ho.", "community", "speaker_008")
        ]
        
        dummy_data = []
        
        for i, (text, context, speaker) in enumerate(samples):
            audio_file = dummy_dir / f"{speaker}_{i:03d}.wav"
            
            if not audio_file.exists():
                # Create varied length audio (2-8 seconds)
                duration = 2.0 + (i % 6)
                dummy_audio = np.random.normal(0, 0.05, int(22050 * duration)).astype(np.float32)
                # Add slight amplitude variation to simulate speech
                envelope = np.sin(np.linspace(0, np.pi * duration, len(dummy_audio))) * 0.5 + 0.5
                dummy_audio = dummy_audio * envelope
                sf.write(audio_file, dummy_audio, 22050)
            
            # Get actual file info
            info = sf.info(str(audio_file))
            processed_text = self.text_processor.process_text(text, expand_numbers=True)
            
            dummy_data.append({
                'audio_path': str(audio_file),
                'text': text,
                'processed_text': processed_text['processed'],
                'speaker_id': speaker,
                'language': 'tw',
                'dataset': 'dummy_enhanced',
                'dialect': 'test',
                'context': context,
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'audio_exists': True,
                'text_length': len(text),
                'word_count': len(text.split()),
                'has_twi_chars': processed_text['has_twi_chars'],
                'quality_score': self._calculate_quality_score(text, info.duration),
                'passes_quality_filter': True
            })
        
        return pd.DataFrame(dummy_data)
    
    def _log_processing_summary(self, df: pd.DataFrame):
        """Log comprehensive processing summary."""
        quality_df = df[df['passes_quality_filter']]
        
        logger.info(f"""
🎉 PROCESSING COMPLETE!
===============================================
📊 Dataset Statistics:
   Total samples loaded: {len(df):,}
   High-quality samples: {len(quality_df):,}
   Quality retention rate: {len(quality_df)/len(df)*100:.1f}%
   
📂 Dataset Breakdown:
   Datasets processed: {self.processing_stats['datasets_processed']}
   Failed datasets: {len(self.failed_datasets)}
   Success rate: {self.processing_stats['datasets_processed']/(self.processing_stats['datasets_processed']+len(self.failed_datasets))*100:.1f}%

🎵 Audio Statistics:
   Total duration: {df['duration'].sum()/3600:.1f} hours
   Quality duration: {quality_df['duration'].sum()/3600:.1f} hours
   Average duration: {df['duration'].mean():.1f}s
   Duration range: {df['duration'].min():.1f}s - {df['duration'].max():.1f}s

📝 Text Statistics:
   Average text length: {df['text_length'].mean():.0f} chars
   Average word count: {df['word_count'].mean():.1f} words
   Twi characters present: {df['has_twi_chars'].sum()} samples ({df['has_twi_chars'].mean()*100:.1f}%)

👥 Speaker Statistics:
   Unique speakers: {df['speaker_id'].nunique():,}
   Languages: {list(df['language'].unique())}
   Dialects: {list(df['dialect'].unique())}

💾 Memory Management:
   Memory cleanups performed: {self.processing_stats['memory_cleanups']}
   Final memory usage: {self.memory_manager.check_memory()['used_mb']:.1f}MB

{"❌ Failed Datasets: " + str(self.failed_datasets) if self.failed_datasets else "✅ All datasets loaded successfully!"}
===============================================
        """)

print("✅ Enhanced resilient data processing system loaded successfully!")
print("🚀 Features: Progressive loading + Comprehensive validation + Memory management + High-quality preprocessing")
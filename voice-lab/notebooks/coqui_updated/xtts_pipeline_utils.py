# xtts_pipeline_utils.py

import json
import time
import pickle
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np
import pandas as pd
import soundfile as sf
import torch
import librosa
from tqdm.auto import tqdm

# Attempt to import TTS and SpeechBrain, handling cases where they might not be installed yet
try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    from speechbrain.pretrained import SpeakerRecognition
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

# --- CONFIGURATION ---

@dataclass
class OptimizedXTTSConfig:
    """Optimized configuration for XTTS with comprehensive Twi support."""
    # Environment paths
    data_path: Path
    model_path: Path
    output_path: Path

    # Device configuration
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    mixed_precision: bool = True

    # Audio configuration
    sample_rate: int = 22050
    hop_length: int = 256
    win_length: int = 1024
    n_fft: int = 1024
    n_mels: int = 80
    mel_fmin: int = 0
    mel_fmax: Optional[int] = None

    # Training configuration
    batch_size: int = 2 if torch.cuda.is_available() else 1
    eval_batch_size: int = 1
    num_loader_workers: int = 2
    epochs: int = 1000
    save_step: int = 5000
    print_step: int = 100

    # Optimizer settings
    lr: float = 5e-6
    weight_decay: float = 1e-6
    grad_clip: float = 1.0

    # Language configuration
    languages: List[str] = field(default_factory=lambda: [
        "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl",
        "cs", "ar", "zh-cn", "ja", "hu", "ko", "tw"
    ])

    # Data filtering
    min_audio_len: float = 1.0
    max_audio_len: float = 11.0
    min_text_len: int = 10
    max_text_len: int = 500

    def __post_init__(self):
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.model_path.mkdir(parents=True, exist_ok=True)
        if torch.cuda.is_available():
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            if gpu_memory_gb < 12: self.batch_size = 1
            elif gpu_memory_gb < 24: self.batch_size = 2
            else: self.batch_size = 4

# --- DATA LOADER ---

class ComprehensiveTTSDataLoader:
    """Load and process comprehensive TTS data inventory."""
    def __init__(self, paths: Dict[str, Path]):
        self.paths = paths
        self.speaker_stats = None

    def create_unified_dataset(self) -> pd.DataFrame:
        """Create a unified dataset from the inventory file."""
        print("🔄 Creating unified TTS dataset...")
        inventory_file = self.paths['inventory'] / 'tts_training_data_inventory.csv'

        if not inventory_file.exists():
            print(f"   ⚠️ TTS inventory not found at {inventory_file}. Creating a dummy dataset for demonstration.")
            return self._create_dummy_dataset()

        try:
            inventory_df = pd.read_csv(inventory_file)
            print(f"   ✅ Loaded {len(inventory_df)} dataset entries from inventory.")
        except Exception as e:
            print(f"   ❌ Error loading TTS inventory: {e}. Falling back to dummy data.")
            return self._create_dummy_dataset()

        all_pairs = []
        for _, row in tqdm(inventory_df.iterrows(), total=len(inventory_df), desc="Processing datasets"):
            pairs = self._discover_audio_text_pairs(row)
            if pairs:
                print(f"   Found {len(pairs)} samples in {row['data_name']}")
                all_pairs.extend(pairs)

        if not all_pairs:
            print("   ⚠️ No audio/text pairs found from the inventory. Falling back to dummy data.")
            return self._create_dummy_dataset()

        unified_df = pd.DataFrame(all_pairs)
        unified_df = self._add_audio_metadata(unified_df)
        unified_df = self._quality_filter(unified_df)
        self._generate_speaker_stats(unified_df)
        return unified_df

    def _discover_audio_text_pairs(self, inventory_row: pd.Series) -> List[Dict]:
        """Discover audio-text pairs from an inventory entry."""
        pairs = []
        base_path = self.paths['base']
        
        # Construct absolute paths from the CSV data
        audio_dir = base_path / inventory_row['audio_file_directory']
        text_dir = base_path / inventory_row['text_files_directory']

        if not audio_dir.exists() or not text_dir.exists():
            print(f"   ⚠️ Warning: Directory not found for {inventory_row['data_name']}. Searched for: {audio_dir}")
            return pairs

        audio_files = [p for p in audio_dir.glob('**/*.wav')]
        for audio_file in tqdm(audio_files, desc=f"Scanning {inventory_row['data_name']}", leave=False):
            text_file = text_dir / f"{audio_file.stem}.txt"
            if text_file.exists():
                try:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        text_content = f.read().strip()
                    if text_content:
                        # Assume speaker ID is the parent directory of the audio file
                        speaker_id = audio_file.parent.name
                        pairs.append({
                            'audio_path': str(audio_file),
                            'text': text_content,
                            'speaker_id': speaker_id,
                            'language': 'tw', # Defaulting to Twi, can be refined
                            'dataset': inventory_row['data_name']
                        })
                except Exception:
                    continue
        return pairs

    def _add_audio_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add audio metadata (duration, sample rate, etc.)."""
        print("   Adding audio metadata...")
        metadata = []
        for path in tqdm(df['audio_path'], desc="Reading audio metadata"):
            try:
                info = sf.info(path)
                metadata.append({
                    'duration': info.duration,
                    'sample_rate': info.samplerate,
                    'audio_exists': True
                })
            except Exception:
                metadata.append({'duration': 0.0, 'sample_rate': 0, 'audio_exists': False})
        
        meta_df = pd.DataFrame(metadata)
        df = pd.concat([df.reset_index(drop=True), meta_df], axis=1)
        df['text_length'] = df['text'].str.len()
        return df

    def _quality_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply quality filtering based on duration and text length."""
        print("   Applying quality filters...")
        initial_count = len(df)
        df = df[
            (df['audio_exists']) &
            (df['duration'] >= 1.0) &
            (df['duration'] <= 15.0) &
            (df['text_length'] >= 10) &
            (df['text_length'] <= 500)
        ].copy()
        retained_percent = (len(df) / initial_count * 100) if initial_count > 0 else 0
        print(f"   Filtered: {initial_count} -> {len(df)} samples ({retained_percent:.1f}% retained)")
        return df

    def _generate_speaker_stats(self, df: pd.DataFrame):
        print("   Generating speaker statistics...")
        if 'speaker_id' in df.columns:
            self.speaker_stats = df.groupby('speaker_id').agg(
                sample_count=('audio_path', 'count'),
                total_duration=('duration', 'sum')
            ).round(2)
            print(f"   📊 Found {len(self.speaker_stats)} speakers.")
        return self.speaker_stats

    def _create_dummy_dataset(self) -> pd.DataFrame:
        """Creates a small, local dataset for testing if real data fails to load."""
        print("   Creating dummy TTS dataset...")
        dummy_dir = self.paths['tts_ready'] / 'dummy_tts'
        dummy_dir.mkdir(exist_ok=True)
        samples = [
            ("Wo ho te sɛn? Me ho yɛ.", "twi", "speaker_001"),
            ("Me ma wo akye. Nante yie.", "twi", "speaker_002"),
            ("This is a test of English voice cloning.", "en", "speaker_003"),
        ]
        dummy_data = []
        for i, (text, lang, speaker) in enumerate(samples):
            audio_file = dummy_dir / f"{speaker}_{i:03d}.wav"
            if not audio_file.exists():
                duration = np.random.uniform(3.0, 8.0)
                dummy_audio = np.random.normal(0, 0.1, int(22050 * duration)).astype(np.float32)
                sf.write(audio_file, dummy_audio, 22050)
            info = sf.info(str(audio_file))
            dummy_data.append({
                'audio_path': str(audio_file), 'text': text,
                'speaker_id': speaker, 'language': lang,
                'duration': info.duration, 'sample_rate': info.samplerate,
                'audio_exists': True, 'text_length': len(text)
            })
        df = pd.DataFrame(dummy_data)
        self._generate_speaker_stats(df)
        return df

# --- TRAINER CLASS ---
# (The rest of the file remains the same as the previous version)
class AdvancedXTTSTrainer:
    """Advanced XTTS trainer for handling embeddings and data preparation."""
    def __init__(self, config: OptimizedXTTSConfig, dataset: pd.DataFrame):
        self.config = config
        self.dataset = dataset
        self.speaker_encoder = None
        self._setup_speaker_recognition()

    def _setup_speaker_recognition(self):
        print("\n🎯 Setting up speaker recognition...")
        if not SPEECHBRAIN_AVAILABLE:
            print("   ⚠️ SpeechBrain not found. Using fallback for embeddings.")
            return
        try:
            self.speaker_encoder = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=str(self.config.model_path / "speaker_encoder")
            )
            print("   ✅ SpeechBrain speaker encoder loaded")
        except Exception as e:
            print(f"   ⚠️ Could not load SpeechBrain: {e}. Using fallback.")
            self.speaker_encoder = None

    def generate_speaker_embeddings(self) -> Dict[str, np.ndarray]:
        print("\n🔊 Generating speaker embeddings...")
        speaker_embeddings = {}
        speaker_groups = self.dataset.groupby('speaker_id')
        for speaker_id, group in tqdm(speaker_groups, desc="Speaker embeddings"):
            best_audio_path = group.iloc[0]['audio_path']
            if self.speaker_encoder:
                embedding = self.speaker_encoder.encode_file(best_audio_path)
                speaker_embeddings[speaker_id] = embedding.squeeze().cpu().numpy()
            else:
                speaker_embeddings[speaker_id] = np.random.rand(1, 192).astype(np.float32)

        print(f"   ✅ Generated embeddings for {len(speaker_embeddings)} speakers")
        embeddings_path = self.config.output_path / "speaker_embeddings.pkl"
        with open(embeddings_path, 'wb') as f:
            pickle.dump(speaker_embeddings, f)
        print(f"   📁 Embeddings saved to {embeddings_path}")
        return speaker_embeddings

    def prepare_coqui_dataset(self) -> Path:
        print("\n📄 Preparing Coqui TTS dataset...")
        dataset_dir = self.config.data_path / "coqui_xtts_dataset"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        audio_dir = dataset_dir / "wavs"
        audio_dir.mkdir(exist_ok=True)
        metadata_lines = []
        for _, row in tqdm(self.dataset.iterrows(), total=len(self.dataset), desc="Processing audio"):
            audio, sr = librosa.load(row['audio_path'], sr=self.config.sample_rate)
            text = re.sub(r'[^\w\s.,?!]', '', row['text']).strip()
            
            output_filename = f"{row['speaker_id']}_{Path(row['audio_path']).stem}.wav"
            output_path = audio_dir / output_filename
            sf.write(output_path, audio, self.config.sample_rate)
            # Corrected metadata format for XTTS
            metadata_lines.append(f"{Path('wavs') / output_filename}|{text}|{row['speaker_id']}")

        self._create_train_val_splits(dataset_dir, metadata_lines)
        print(f"   ✅ Processed {len(metadata_lines)} samples.")
        print(f"   📁 Dataset saved to: {dataset_dir}")
        return dataset_dir

    def _create_train_val_splits(self, dataset_dir: Path, metadata: List[str]):
        print("   Creating train/validation splits...")
        np.random.shuffle(metadata)
        split_idx = int(len(metadata) * 0.9)
        train_lines, val_lines = metadata[:split_idx], metadata[split_idx:]
        with open(dataset_dir / "metadata_train.csv", 'w', encoding='utf-8') as f:
            f.write('\n'.join(train_lines))
        with open(dataset_dir / "metadata_val.csv", 'w', encoding='utf-8') as f:
            f.write('\n'.join(val_lines))
        print(f"   Train samples: {len(train_lines)}, Validation samples: {len(val_lines)}")


# --- INFERENCE CLASS ---
class OptimizedXTTSInference:
    """Optimized XTTS inference engine."""
    def __init__(self, config: OptimizedXTTSConfig):
        self.config = config
        self.model = None

    def load_model(self):
        print(f"\n🤖 Loading XTTS model...")
        if not TTS_AVAILABLE:
            print("   ⚠️ TTS not available, using mock model.")
            self.model = self._create_mock_model()
            return
        try:
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=torch.cuda.is_available())
            print(f"   ✅ Model loaded successfully.")
        except Exception as e:
            print(f"   ❌ Error loading model: {e}")
            self.model = self._create_mock_model()

    def _create_mock_model(self):
        class MockXTTSModel:
            def tts_to_file(self, text, speaker_wav, language, file_path):
                dummy_audio = np.random.normal(0, 0.1, 22050 * 3).astype(np.float32)
                sf.write(file_path, dummy_audio, 22050)
                return file_path
        return MockXTTSModel()

    def test_voice_cloning(self, reference_audios: List[str]):
        print("\n🧪 Testing voice cloning capabilities...")
        if not reference_audios:
            print("   ⚠️ No reference audio files to test cloning.")
            return
        test_phrases = [
            ("Wo ho te sɛn? Me ho yɛ.", "tw"),
            ("This is a test of English voice cloning.", "en")
        ]
        for text, lang in test_phrases:
            ref_audio = np.random.choice(reference_audios)
            output_path = self.config.output_path / f"cloned_{lang}_{int(time.time())}.wav"
            print(f"   Cloning '{text[:30]}...' using {Path(ref_audio).name}")
            self.model.tts_to_file(
                text=text,
                speaker_wav=ref_audio,
                language=lang,
                file_path=str(output_path)
            )
            print(f"   ✅ Voice cloned to: {output_path}")

# --- PIPELINE FUNCTIONS ---
def quick_start_training(trainer: AdvancedXTTSTrainer):
    """Complete quick start pipeline for XTTS training."""
    print("\n🚀 Starting XTTS training pipeline...")
    if not trainer:
        print("   ⚠️ No trainer available.")
        return None, None
    try:
        trainer.generate_speaker_embeddings()
        dataset_path = trainer.prepare_coqui_dataset()
        print("\n🎓 Training pipeline ready!")
        return trainer, dataset_path
    except Exception as e:
        print(f"   ❌ Error in training pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def get_training_commands(dataset_path: Path, config: OptimizedXTTSConfig):
    """Generate and save the training command."""
    print(f"\n📜 Generating XTTS Training Commands...")
    # These paths are placeholders as the pre-trained model is not downloaded yet by TTS
    config_path = config.output_path / "training_output/config.json"
    restore_path = config.output_path / "training_output/best_model.pth"
    
    training_cmd = (
        f"python -m TTS.bin.train_tts \\\n"
        f"    --config_path {config_path} \\\n"
        f"    --restore_path {restore_path} \\\n"
        f"    --train_csv {dataset_path}/metadata_train.csv \\\n"
        f"    --eval_csv {dataset_path}/metadata_val.csv \\\n"
        f"    --output_path {config.output_path}/training_output \\\n"
        f"    --num_loader_workers {config.num_loader_workers} \\\n"
        f"    --batch_size {config.batch_size} \\\n"
        f"    --eval_batch_size {config.eval_batch_size} \\\n"
        f"    --epochs {config.epochs} \\\n"
        f"    --save_step {config.save_step} \\\n"
        f"    --print_step {config.print_step} \\\n"
        f"    --lr {config.lr} \\\n"
        f"    --use_cuda {torch.cuda.is_available()}"
    )
    print(f"\n---\nNOTE: You must first run a training session to download the base model and generate the config.json. The paths above are placeholders.\n\n{training_cmd}\n---")
    script_path = config.output_path / "train_xtts.sh"
    with open(script_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write(training_cmd)
    print(f"📄 Training script saved to: {script_path}")
    return training_cmd

def benchmark_model_performance(inference_engine: OptimizedXTTSInference, dataset: pd.DataFrame):
    """Benchmark model performance and calculate RTF."""
    print(f"\n⚡ Benchmarking XTTS model performance...")
    if not inference_engine or not inference_engine.model or dataset.empty:
        print("   ⚠️ Inference engine not loaded or dataset is empty.")
        return
    
    test_cases = [
        {"name": "Short Twi", "text": "Me ho yɛ.", "lang": "tw", "exp_dur": 1.5},
        {"name": "Long Twi", "text": "Ɛyɛ adesua a ɛho hia sɛ yɛka Twi kasa.", "lang": "tw", "exp_dur": 5.0},
        {"name": "English", "text": "This is a test of English voice synthesis.", "lang": "en", "exp_dur": 3.0}
    ]
    ref_audio = dataset.iloc[0]['audio_path']
    results = []

    for case in test_cases:
        times = []
        print(f"\n   Testing: {case['name']}")
        for i in range(3):
            start_time = time.time()
            output_path = inference_engine.config.output_path / f"benchmark_{i}.wav"
            inference_engine.model.tts_to_file(text=case['text'], speaker_wav=ref_audio, language=case['lang'], file_path=str(output_path))
            elapsed = time.time() - start_time
            times.append(elapsed)
            actual_duration = sf.info(str(output_path)).duration
            print(f"     Run {i+1}: {elapsed:.2f}s (audio: {actual_duration:.2f}s)")
        
        avg_time = np.mean(times)
        rtf = avg_time / case['exp_dur']
        results.append({'test_case': case['name'], 'avg_time': avg_time, 'rtf': rtf})
        print(f"     ✅ Average: {avg_time:.2f}s | RTF: {rtf:.2f}x")

    benchmark_path = inference_engine.config.output_path / "performance_benchmark.json"
    with open(benchmark_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Detailed results saved to: {benchmark_path}")
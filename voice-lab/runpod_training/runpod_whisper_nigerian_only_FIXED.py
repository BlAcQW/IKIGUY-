#!/usr/bin/env python3
"""
Whisper Small Multi-Language QLoRA Fine-tuning for African Languages
FIXED VERSION with Hetzner Remote Data Loading + Storage-Aware Batching

UPDATED: 2025-10-22 - Fixed for RunPod with Hetzner external storage

KEY FIXES:
1. Remote data loading from Hetzner Storage Box via rsync
2. Batch-based data syncing to work within RunPod storage limits
3. Fixed input_ids bug - properly handle audio column casting
4. Streaming-first approach for all datasets

Target Languages: Twi, Hausa, Yoruba, Igbo (4 languages - Ewe removed, not available)
Training Method: QLoRA (4-bit quantization + LoRA adapters)
Expected WER: 12-35% across languages

STORAGE STRATEGY:
- HuggingFace datasets: Stream directly (no local storage)
- Hetzner data (Twi): Sync manifests first, then batch audio files as needed
- Total local storage needed: <50GB (vs 476GB full dataset)
"""

import os
import sys
import json
import argparse
import psutil
import gc
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

import torch
import torchaudio
from datasets import load_dataset, concatenate_datasets, Dataset, DatasetDict, Audio, interleave_datasets, IterableDataset
from transformers import (
    WhisperFeatureExtractor,
    WhisperTokenizer,
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    TrainerCallback,
    EarlyStoppingCallback,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training
)
import evaluate
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

# Memory utilities
def log_memory(prefix=""):
    """Log current memory usage."""
    process = psutil.Process()
    mem = process.memory_info().rss / 1024 / 1024
    print(f"{prefix}Memory: {mem:.1f}MB")
    if torch.cuda.is_available():
        gpu_mem = torch.cuda.memory_allocated() / 1024**3
        print(f"{prefix}GPU Memory: {gpu_mem:.2f}GB")
    return mem

def cleanup_memory():
    """Force garbage collection and CUDA cache cleanup."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# --- HETZNER STORAGE UTILITIES ---
class HetznerDataSync:
    """Manage data syncing from Hetzner Storage Box to RunPod workspace."""

    def __init__(self,
                 hetzner_key: str = "/root/.ssh/hetzner_key",
                 hetzner_user: str = "u497034-sub1",
                 hetzner_host: str = "u497034-sub1.your-storagebox.de",
                 ssh_port: int = 23,
                 workspace: str = "/workspace"):
        self.hetzner_key = hetzner_key
        self.hetzner_user = hetzner_user
        self.hetzner_host = hetzner_host
        self.ssh_port = ssh_port
        self.workspace = Path(workspace)
        self.data_dir = self.workspace / "training-data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def sync_manifests_only(self, language: str = "twi-akan-fante") -> bool:
        """
        Sync only manifest files (CSVs, JSONs) - very lightweight.

        Returns:
            bool: True if successful
        """
        print(f"\n📥 Syncing manifests for {language} from Hetzner...")

        remote_path = f"{self.hetzner_user}@{self.hetzner_host}:/home/voice-lab/data/{language}/"
        local_path = self.data_dir / language
        local_path.mkdir(parents=True, exist_ok=True)

        # Check if manifest already exists
        manifest_file = local_path / "processed" / "manifests" / "asr_16k_dataset.csv"
        if manifest_file.exists():
            print(f"✅ Manifest already exists at {manifest_file}, skipping rsync")
            return True


        # Only sync manifests, CSVs, JSONs - exclude audio
        cmd = [
            "rsync", "-avzP",
            "--include=*/",  # Include directories
            "--include=*.csv",
            "--include=*.json",
            "--include=*.txt",
            "--exclude=*",  # Exclude everything else (audio files)
            "-e", f"ssh -p {self.ssh_port} -i {self.hetzner_key} -o StrictHostKeyChecking=no",
            remote_path,
            str(local_path)
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Manifests synced to {local_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Rsync failed: {e.stderr}")
            return False

    def get_audio_from_hetzner(self, audio_path: str, language: str = "twi-akan-fante") -> Optional[str]:
        """
        Fetch a single audio file from Hetzner on-demand.

        Args:
            audio_path: Relative path to audio file
            language: Language dataset name

        Returns:
            Local path to audio file, or None if failed
        """
        # Extract just the filename and relative path structure
        rel_path = Path(audio_path).relative_to(f"/opt/kasaai/apps/voice-lab/data/{language}") \
                   if f"/opt/kasaai/apps/voice-lab/data/{language}" in audio_path \
                   else Path(audio_path)

        remote_file = f"{self.hetzner_user}@{self.hetzner_host}:/home/voice-lab/data/{language}/{rel_path}"
        local_file = self.data_dir / language / rel_path
        local_file.parent.mkdir(parents=True, exist_ok=True)

        # Skip if already exists locally
        if local_file.exists():
            return str(local_file)

        # Fetch via rsync
        cmd = [
            "rsync", "-azq",
            "-e", f"ssh -p {self.ssh_port} -i {self.hetzner_key} -o StrictHostKeyChecking=no",
            remote_file,
            str(local_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            return str(local_file)
        except Exception as e:
            print(f"⚠️  Failed to fetch {rel_path}: {e}")
            return None

# --- CONFIGURATION ---
@dataclass
class MultiLangWhisperConfig:
    """Configuration for multi-language Whisper QLoRA fine-tuning."""

    # Paths
    output_dir: Path = Path('./outputs/whisper-small-african-qlora')
    cache_dir: Path = Path('./cache')

    # Hetzner storage config
    use_hetzner_storage: bool = False
    hetzner_sync_manifests_only: bool = True  # Only sync lightweight manifests

    # Model configuration
    model_name: str = "openai/whisper-small"  # 244M parameters
    task: str = "transcribe"

    # Languages with CONFIRMED data availability and weights
    # Removed Ewe - not available in Common Voice
    languages: List[Dict] = field(default_factory=lambda: [
        # Twi disabled for Option A - will add in Option B
        # {"code": "tw", "name": "Twi", "hours": 335, "weight": 1.0, "source": "hetzner"},
        {"code": "ha", "name": "Hausa", "hours": 650, "weight": 1.0, "source": "naijavoices"},
        {"code": "yo", "name": "Yoruba", "hours": 600, "weight": 1.0, "source": "naijavoices"},
        {"code": "ig", "name": "Igbo", "hours": 630, "weight": 1.0, "source": "naijavoices"},
    ])

    # Audio preprocessing
    sample_rate: int = 16000
    min_audio_length: float = 0.5  # seconds
    max_audio_length: float = 30.0  # seconds

    # Training parameters (optimized for A40 with 4-bit)
    per_device_train_batch_size: int = 16  # Increased from 8
    gradient_accumulation_steps: int = 2   # 16*2 = effective batch 32
    learning_rate: float = 1e-4
    warmup_steps: int = 500
    max_steps: int = 15000  # ~72 hours of training
    eval_steps: int = 1000
    save_steps: int = 1000
    logging_steps: int = 50

    # LoRA configuration
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05

    # 4-bit quantization config
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_quant_type: str = "nf4"

    # Early stopping
    early_stopping_patience: int = 3

    # Streaming
    use_streaming: bool = True  # IMPORTANT: Must be True for storage efficiency

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def print_summary(self):
        """Print training configuration summary."""
        total_hours = sum(lang["hours"] for lang in self.languages)
        print("\n" + "="*80)
        print("🚀 WHISPER AFRICAN MULTI-LANGUAGE QLORA FINE-TUNING")
        print("="*80)
        print(f"🔥 GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
        if torch.cuda.is_available():
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"🔥 GPU: {torch.cuda.get_device_name(0)} ({gpu_mem:.1f} GB VRAM)")
        print(f"📊 Languages: {len(self.languages)}")
        for lang in self.languages:
            print(f"   {lang['name']}: {lang['hours']}h (weight: {lang['weight']})")
        print(f"\n💾 Storage Mode: {'Hetzner Remote + Streaming' if self.use_hetzner_storage else 'Local'}")
        print(f"📡 Streaming: {'ENABLED' if self.use_streaming else 'DISABLED'}")
        print(f"📦 Total Training Data: {total_hours}h ({total_hours/24:.1f} days)")

# --- DATASET LOADER ---
class MultiLanguageDatasetLoader:
    """Load and prepare multi-language datasets with Hetzner remote loading."""

    def __init__(self, config: MultiLangWhisperConfig):
        self.config = config
        self.processor = WhisperProcessor.from_pretrained(
            config.model_name,
            task=config.task
        )

        # Initialize Hetzner sync if enabled
        self.hetzner_sync = None
        if config.use_hetzner_storage:
            self.hetzner_sync = HetznerDataSync()
            print("✅ Hetzner storage sync initialized")

    def load_naijavoices(self, language_code: str, streaming: bool = True):
        """Load NaijaVoices dataset for a specific language with streaming support."""
        print(f"📥 Loading NaijaVoices {language_code} ({'streaming' if streaming else 'full download'})...")

        lang_map = {"ha": "hausa", "yo": "yoruba", "ig": "igbo"}
        if language_code not in lang_map:
            return None

        datasets_list = []
        for batch_num in range(1, 11):  # 10 batches per language
            try:
                ds = load_dataset(
                    "naijavoices/naijavoices-dataset",
                    f"{lang_map[language_code]}-batch-{batch_num}",
                    split="train",
                    streaming=streaming,
                    cache_dir=str(self.config.cache_dir)
                )
                datasets_list.append(ds)
            except Exception as e:
                break

        if datasets_list:
            if streaming:
                # For streaming datasets, use interleave_datasets
                combined = interleave_datasets(datasets_list)
                print(f"   ✅ Loaded streaming dataset ({len(datasets_list)} batches)")
            else:
                combined = concatenate_datasets(datasets_list)
                print(f"   ✅ Loaded {len(combined)} samples")
            return combined
        return None

    def load_hetzner_data(self, language_code: str) -> Optional[Dataset]:
        """
        Load data from Hetzner Storage Box with manifest-first approach.

        This syncs only the CSV manifests first (lightweight), then fetches
        audio files on-demand during training.
        """
        print(f"📥 Loading Hetzner {language_code} data...")

        if not self.hetzner_sync:
            print("   ⚠️  Hetzner sync not initialized")
            return None

        # Map language codes to Hetzner directory names
        lang_dir_map = {
            "tw": "twi-akan-fante",
            "gaa": "ga",
        }

        dir_name = lang_dir_map.get(language_code, language_code)

        # Step 1: Sync manifests only (very quick - few MB)
        if not self.hetzner_sync.sync_manifests_only(dir_name):
            print(f"   ❌ Failed to sync manifests from Hetzner")
            return None

        # Step 2: Load manifest CSV
        manifest_path = self.hetzner_sync.data_dir / dir_name / "processed" / "manifests" / "asr_16k_dataset.csv"

        # Try alternative locations
        if not manifest_path.exists():
            manifest_path = self.hetzner_sync.data_dir / dir_name / "asr_16k_dataset.csv"

        if not manifest_path.exists():
            print(f"   ⚠️  Manifest not found at {manifest_path}")
            return None

        print(f"   📄 Loading manifest from {manifest_path.name}...")
        df = pd.read_csv(manifest_path)

        # Fix paths to point to Hetzner (will be fetched on-demand)
        if 'audio_path' in df.columns:
            df['original_path'] = df['audio_path'].copy()
            df['language_dataset'] = dir_name
        elif 'path' in df.columns:
            df['audio_path'] = df['path']
            df['original_path'] = df['path'].copy()
            df['language_dataset'] = dir_name

        # Ensure we have required columns
        if 'text' not in df.columns and 'transcription' in df.columns:
            df['text'] = df['transcription']
        elif 'text' not in df.columns and 'sentence' in df.columns:
            df['text'] = df['sentence']

        ds = Dataset.from_pandas(df).to_iterable_dataset()

        # CRITICAL FIX: Don't cast audio column yet - we'll handle it in preprocessing
        # This prevents trying to load all audio files at once
        print(f"   ✅ Loaded Hetzner dataset (manifest only, audio on-demand)")
        return ds

    def load_local_data(self, language_code: str) -> Optional[Dataset]:
        """
        Legacy local data loader - now redirects to Hetzner for Twi/Ga.
        """
        if self.config.use_hetzner_storage and language_code in ["tw", "gaa"]:
            return self.load_hetzner_data(language_code)

        # Original local path (won't work on RunPod)
        print(f"📥 Loading local {language_code} data...")
        lang_dir_map = {
            "tw": "twi-akan-fante",
            "gaa": "ga",
        }

        dir_name = lang_dir_map.get(language_code, language_code)
        local_path = Path(f"/opt/kasaai/apps/voice-lab/data/{dir_name}")

        if not local_path.exists():
            print(f"   ⚠️  Directory not found: {local_path}")
            return None

        manifest_path = local_path / "asr_16k_dataset.csv"
        if manifest_path.exists():
            print(f"   📄 Loading from {manifest_path.name}...")
            df = pd.read_csv(manifest_path)
            ds = Dataset.from_pandas(df).to_iterable_dataset()
            ds = ds.cast_column("audio_path", Audio(sampling_rate=16000))
            ds = ds.rename_column("audio_path", "audio")
            if "text" in ds.column_names:
                ds = ds.rename_column("text", "sentence")
            print(f"   ✅ Loaded dataset samples")
            return ds

        return None

    def preprocess_audio(self, batch):
        """
        Preprocess audio to Whisper input format.

        CRITICAL FIX: Properly handle both streaming and Hetzner datasets.
        """
        # Handle different audio input formats
        if "audio" in batch and isinstance(batch["audio"], dict):
            # Already loaded audio
            audio = batch["audio"]
        elif "original_path" in batch and "language_dataset" in batch:
            # Hetzner data - fetch on-demand
            audio_path = batch["original_path"]
            language = batch["language_dataset"]

            local_path = self.hetzner_sync.get_audio_from_hetzner(audio_path, language)
            if local_path is None:
                # Skip this sample if we can't fetch it
                batch["input_features"] = None
                batch["labels"] = None
                return batch

            # Load audio from local cached file
            audio_array, sr = torchaudio.load(local_path)
            audio = {
                "array": audio_array.numpy()[0],  # Convert to numpy and take first channel
                "sampling_rate": sr
            }
        else:
            # Try to load from audio_path if present
            if "audio_path" in batch:
                try:
                    audio_array, sr = torchaudio.load(batch["audio_path"])
                    audio = {
                        "array": audio_array.numpy()[0],
                        "sampling_rate": sr
                    }
                except Exception as e:
                    print(f"⚠️  Failed to load audio: {e}")
                    batch["input_features"] = None
                    batch["labels"] = None
                    return batch
            else:
                print("⚠️  No audio found in batch")
                batch["input_features"] = None
                batch["labels"] = None
                return batch

        # Resample if needed
        if audio["sampling_rate"] != self.config.sample_rate:
            import librosa
            audio_array = librosa.resample(
                np.array(audio["array"], dtype=np.float32),
                orig_sr=audio["sampling_rate"],
                target_sr=self.config.sample_rate
            )
        else:
            audio_array = np.array(audio["array"], dtype=np.float32)

        # Compute input features
        input_features = self.processor.feature_extractor(
            audio_array,
            sampling_rate=self.config.sample_rate
        ).input_features[0]

        # Encode text - handle multiple possible column names
        text = batch.get("sentence") or batch.get("text") or batch.get("transcription") or batch.get("transcript", "")
        labels = self.processor.tokenizer(text).input_ids

        batch["input_features"] = input_features
        batch["labels"] = labels
        return batch

    def filter_duration(self, example):
        """Filter samples by duration."""
        if "audio" not in example or example["audio"] is None:
            return False

        audio = example["audio"]
        if isinstance(audio, dict) and "array" in audio and "sampling_rate" in audio:
            duration = len(audio["array"]) / audio["sampling_rate"]
            return (self.config.min_audio_length <= duration <= self.config.max_audio_length)
        return True  # Keep if we can't determine duration

    def load_all_languages(self, use_streaming: bool = True):
        """Load all language datasets with streaming support and weighted sampling."""
        print("\n" + "="*80)
        print("🌍 LOADING MULTI-LANGUAGE DATASETS")
        print("="*80)
        print(f"📡 Streaming mode: {'ENABLED' if use_streaming else 'DISABLED'}")

        all_datasets = []
        sampling_weights = []

        for lang_info in self.config.languages:
            lang_code = lang_info["code"]
            lang_name = lang_info["name"]
            weight = lang_info["weight"]
            source = lang_info.get("source", "unknown")

            print(f"\n📂 Processing {lang_name} ({lang_code}) - Weight: {weight}")
            print("-" * 60)

            datasets_to_combine = []

            # Load based on source
            if source == "hetzner":
                # Priority 1: Hetzner data (Twi, Ga)
                hetzner_ds = self.load_hetzner_data(lang_code)
                if hetzner_ds:
                    datasets_to_combine.append(hetzner_ds)
                    print(f"   ✅ Loaded Hetzner data")

            elif source == "naijavoices":
                # Priority 2: NaijaVoices (Hausa, Yoruba, Igbo)
                nv_ds = self.load_naijavoices(lang_code, streaming=use_streaming)
                if nv_ds:
                    datasets_to_combine.append(nv_ds)
                    print(f"   ✅ Loaded NaijaVoices data")

            if not datasets_to_combine:
                print(f"   ⚠️  No data found for {lang_name}, skipping...")
                continue

            # Combine if multiple sources
            if len(datasets_to_combine) == 1:
                final_ds = datasets_to_combine[0]
            else:
                if use_streaming:
                    final_ds = interleave_datasets(datasets_to_combine)
                else:
                    final_ds = concatenate_datasets(datasets_to_combine)

            all_datasets.append(final_ds)
            sampling_weights.append(weight)

        if not all_datasets:
            raise ValueError("No datasets loaded! Check your configuration.")

        print("\n" + "="*80)
        print("🔀 COMBINING ALL LANGUAGES")
        print("="*80)

        # Calculate sampling probabilities
        total_weight = sum(sampling_weights)
        probabilities = [w / total_weight for w in sampling_weights]

        # Combine with weighted sampling
        if use_streaming:
            combined_dataset = interleave_datasets(
                all_datasets,
                probabilities=probabilities,
                seed=42
            )
            print(f"✅ Combined {len(all_datasets)} streaming datasets with weighted sampling")
        else:
            combined_dataset = interleave_datasets(
                all_datasets,
                probabilities=probabilities,
                seed=42,
                stopping_strategy="all_exhausted"
            )
            print(f"✅ Combined {len(all_datasets)} datasets with {len(combined_dataset)} total samples")

        print(f"   Sampling probabilities: {[f'{p:.2f}' for p in probabilities]}")

        return combined_dataset

# --- DATA COLLATOR ---
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Data collator for Whisper - handles None values from failed audio loads."""
    processor: WhisperProcessor

    def __call__(self, features: List[Dict]) -> Dict:
        # Filter out failed samples (None input_features)
        features = [f for f in features if f.get("input_features") is not None and f.get("labels") is not None]

        if not features:
            # Return empty batch if all failed
            return {
                "input_features": torch.tensor([]),
                "labels": torch.tensor([])
            }

        # Pad input features
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # Pad labels
        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        # Remove BOS token if present
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]

        # Return only input_features and labels (no input_ids!)
        return {"input_features": batch["input_features"], "labels": labels}

# --- METRICS ---
def compute_metrics(pred, tokenizer):
    """Compute WER and CER metrics."""
    wer_metric = evaluate.load("wer")
    cer_metric = evaluate.load("cer")

    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token
    label_ids[label_ids == -100] = tokenizer.pad_token_id

    # Decode predictions and references
    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    cer = cer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer, "cer": cer}

# --- MAIN TRAINING ---
def main(args):
    """Main training function."""
    config = MultiLangWhisperConfig()
    config.print_summary()

    # Load dataset
    loader = MultiLanguageDatasetLoader(config)
    dataset = loader.load_all_languages(use_streaming=config.use_streaming)

    # Preprocess
    print("\n🔧 Preprocessing datasets...")
    dataset = dataset.map(
        loader.preprocess_audio,
        remove_columns=dataset.column_names if hasattr(dataset, 'column_names') else []
    )

    # Load model with 4-bit quantization
    print("\n🔧 Loading Whisper model with 4-bit quantization...")
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=config.load_in_4bit,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type=config.bnb_4bit_quant_type
    )

    model = WhisperForConditionalGeneration.from_pretrained(
        config.model_name,
        quantization_config=quantization_config,
        device_map="auto"
    )

    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []
    model.config.use_cache = False

    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Apply LoRA
    print("🔧 Applying LoRA adapters...")
    # IMPORTANT: Do NOT set task_type for Whisper models
    # Whisper uses input_features (audio) not input_ids (text)
    # Setting task_type=SEQ_2_SEQ_LM causes PEFT to wrap with PeftModelForSeq2SeqLM
    # which expects input_ids and breaks Whisper's forward()
    # Solution: Omit task_type to use base PeftModel class
    # Reference: https://github.com/huggingface/peft/issues/1988
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=config.lora_dropout,
        bias="none"
        # task_type removed - let PEFT use base PeftModel
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        max_steps=config.max_steps,
        gradient_checkpointing=True,
        fp16=False,
        bf16=True,
        evaluation_strategy="no",  # Fixed: Disabled eval since no eval_dataset provided
        # eval_steps=config.eval_steps,  # Commented out - not needed without evaluation
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        report_to=["tensorboard"],
        load_best_model_at_end=False,  # Fixed: Can't load best model without evaluation
        # metric_for_best_model="wer",  # Commented out - not needed without evaluation
        # greater_is_better=False,  # Commented out - not needed without evaluation
        push_to_hub=False,
        remove_unused_columns=False,
        label_names=["labels"]
    )

    # Data collator
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=loader.processor
    )

    # Trainer - no custom Trainer needed now that task_type is removed
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=dataset,
        data_collator=data_collator,
        compute_metrics=lambda pred: compute_metrics(pred, loader.processor.tokenizer),
        # callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)]  # Fixed: Removed - requires evaluation
    )

    # Train
    print("\n🚀 Starting training...")
    log_memory("Before training: ")

    trainer.train()

    # Save
    print("\n💾 Saving final model...")
    trainer.save_model(str(config.output_dir / "final"))
    loader.processor.save_pretrained(str(config.output_dir / "final"))

    print("\n✅ Training complete!")
    print(f"📁 Model saved to: {config.output_dir / 'final'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming mode")
    args = parser.parse_args()

    main(args)

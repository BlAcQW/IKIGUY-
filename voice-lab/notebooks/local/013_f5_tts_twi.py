#!/usr/bin/env python3
"""
F5-TTS Fine-tuning for Twi - Flow Matching Diffusion TTS
Zero-shot voice cloning with flow-matching
Optimized for RTX 4000 20GB GPU

Server Resources:
- GPU: RTX 4000 (20GB VRAM)
- RAM: 62GB
- CPU: 20 cores

Note: F5-TTS uses flow-matching diffusion for high-quality speech synthesis
"""

import os
import sys
from pathlib import Path
import torch
import torchaudio
from dataclasses import dataclass
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from tqdm.auto import tqdm
import argparse
import json

# Transformers & Training
from transformers import (
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from transformers import logging as hf_logging
from datasets import Dataset, Audio

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
hf_logging.set_verbosity_info()

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class F5TTSConfig:
    """F5-TTS training configuration for 20GB GPU."""

    # Paths
    base_path: Path = Path("/opt/kasaai/apps/voice-lab")
    manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/f5_tts_train.csv"
    val_manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/f5_tts_val.csv"
    output_dir: Path = base_path / "models/f5_tts_twi"

    # Model - F5-TTS from SWivid
    model_name: str = "SWivid/F5-TTS"

    # Training hyperparameters (optimized for 20GB GPU)
    batch_size: int = 2  # Diffusion models are memory-intensive
    gradient_accumulation_steps: int = 16  # Effective batch = 32
    num_train_epochs: int = 15
    learning_rate: float = 1e-5
    warmup_steps: int = 1000
    fp16: bool = True

    # Early stopping
    early_stopping_patience: int = 3

    # Audio processing
    max_audio_length: float = 15.0  # seconds
    sampling_rate: int = 24000  # F5-TTS uses 24kHz

    # Evaluation
    eval_steps: int = 1000
    save_steps: int = 1000
    logging_steps: int = 50

config = F5TTSConfig()
config.output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATA PREPARATION
# =============================================================================

class F5TTSDatasetProcessor:
    """Process Twi dataset for F5-TTS training."""

    def __init__(self, config: F5TTSConfig):
        self.config = config

    def load_dataset(self, manifest_path: Path) -> Dataset:
        """Load dataset from manifest."""
        logger.info(f"Loading dataset from {manifest_path}")

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        # Read manifest
        df = pd.read_csv(manifest_path)
        logger.info(f"Loaded {len(df)} samples")

        # Filter by duration
        df = df[df['duration'] <= self.config.max_audio_length]
        logger.info(f"After duration filter: {len(df)} samples")

        # Ensure text column exists
        if 'text' not in df.columns and 'transcript' in df.columns:
            df = df.rename(columns={'transcript': 'text'})

        # Create dataset
        dataset = Dataset.from_pandas(df[['audio_path', 'text', 'duration', 'speaker_id']])

        # Cast audio column
        dataset = dataset.cast_column(
            "audio_path",
            Audio(sampling_rate=self.config.sampling_rate)
        )
        dataset = dataset.rename_column("audio_path", "audio")

        return dataset

    def preprocess_function(self, batch):
        """Preprocess batch for F5-TTS training."""
        # Extract audio arrays
        audio_arrays = []
        for item in batch["audio"]:
            audio = item["array"]
            sr = item["sampling_rate"]

            # Resample if necessary
            if sr != self.config.sampling_rate:
                resampler = torchaudio.transforms.Resample(sr, self.config.sampling_rate)
                audio = resampler(torch.tensor(audio)).numpy()

            audio_arrays.append(audio)

        # Prepare batch
        batch["audio_values"] = audio_arrays
        batch["text"] = batch["text"]
        batch["speaker_id"] = batch["speaker_id"]

        return batch

# =============================================================================
# DATA COLLATOR
# =============================================================================

@dataclass
class F5TTSDataCollator:
    """Data collator for F5-TTS training."""

    sampling_rate: int
    padding: bool = True

    def __call__(self, features: List[Dict]) -> Dict[str, torch.Tensor]:
        # Extract text
        texts = [f["text"] for f in features]

        # Process audio
        audio_values = [torch.tensor(f["audio_values"]) for f in features]

        # Pad audio to same length
        max_audio_len = max(a.shape[0] for a in audio_values)
        audio_padded = torch.zeros(len(audio_values), max_audio_len)

        for i, audio in enumerate(audio_values):
            audio_padded[i, :audio.shape[0]] = audio

        # Speaker IDs
        speaker_ids = torch.tensor([f.get("speaker_id", 0) for f in features])

        return {
            "text": texts,
            "audio_values": audio_padded,
            "speaker_id": speaker_ids
        }

# =============================================================================
# TRAINING
# =============================================================================

def train(args):
    """Main training function."""
    logger.info("=" * 80)
    logger.info("F5-TTS Fine-tuning for Twi - Flow Matching Diffusion")
    logger.info("=" * 80)
    logger.info(f"GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")

    # Initialize processor
    dataset_processor = F5TTSDatasetProcessor(config)

    # Load datasets
    logger.info("\nLoading datasets...")
    try:
        train_dataset = dataset_processor.load_dataset(config.manifest_path)
        val_dataset = dataset_processor.load_dataset(config.val_manifest_path)
    except FileNotFoundError as e:
        logger.error(f"✗ {e}")
        logger.error("Please run data processing first: 002_process_twi_data_local.py")
        sys.exit(1)

    logger.info(f"Train samples: {len(train_dataset)}")
    logger.info(f"Val samples: {len(val_dataset)}")

    # Preprocess datasets
    logger.info("\nPreprocessing datasets...")
    train_dataset = train_dataset.map(
        dataset_processor.preprocess_function,
        batch_size=32,
        batched=True,
        num_proc=4,
        remove_columns=train_dataset.column_names
    )

    val_dataset = val_dataset.map(
        dataset_processor.preprocess_function,
        batch_size=32,
        batched=True,
        num_proc=4,
        remove_columns=val_dataset.column_names
    )

    logger.info("\n⚠️  F5-TTS Model Implementation Note:")
    logger.info("=" * 80)
    logger.info("F5-TTS uses flow-matching diffusion for TTS.")
    logger.info("Full training requires:")
    logger.info("- F5-TTS model architecture from SWivid/F5-TTS")
    logger.info("- Flow-matching diffusion process")
    logger.info("- Duration predictor")
    logger.info("- Phoneme encoder (optional for better quality)")
    logger.info("\nData pipeline is ready. Model integration needed.")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info("=" * 80)

    # Save config
    training_config = {
        "model_name": config.model_name,
        "sampling_rate": config.sampling_rate,
        "batch_size": config.batch_size,
        "gradient_accumulation": config.gradient_accumulation_steps,
        "num_epochs": config.num_train_epochs,
        "learning_rate": config.learning_rate,
        "max_audio_length": config.max_audio_length,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
    }

    with open(config.output_dir / "training_config.json", 'w') as f:
        json.dump(training_config, f, indent=2)

    logger.info(f"\n✓ Training config saved to: {config.output_dir}/training_config.json")

def inference(args):
    """Example inference with trained model."""
    logger.info("\n" + "=" * 80)
    logger.info("F5-TTS Inference - Zero-shot Voice Cloning")
    logger.info("=" * 80)

    logger.info("\n⚠️  Example inference workflow:")
    logger.info("1. Load trained F5-TTS model")
    logger.info("2. Provide reference audio (3-5 seconds)")
    logger.info("3. Input text: 'Ɛte sɛn?' (How are you?)")
    logger.info("4. Generate speech with reference voice characteristics")
    logger.info("\nExample code:")
    logger.info("  reference_audio = load_audio('reference.wav')")
    logger.info("  text = 'Ɛte sɛn?'")
    logger.info("  speech = model.synthesize(text, reference_audio)")
    logger.info("=" * 80)

# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="F5-TTS Fine-tuning for Twi")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["train", "inference"],
        default="train",
        help="Mode: train or inference"
    )
    args = parser.parse_args()

    if args.mode == "train":
        train(args)
    else:
        inference(args)

if __name__ == "__main__":
    main()

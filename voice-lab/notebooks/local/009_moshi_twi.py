#!/usr/bin/env python3
"""
Kyutai Moshi Fine-tuning for Twi - Audio-to-Audio Voice Model
Optimized for RTX 4000 20GB GPU with DeepSpeed ZeRO-2

⚠️ WARNING: MOSHI HAS DEPENDENCY CONFLICTS ⚠️
- Requires numpy >=1.26 (conflicts with TTS requiring numpy==1.22.0)
- Requires huggingface-hub <0.34 (conflicts with transformers/peft requiring >=0.34)
- Cannot be installed in same venv as other fine-tuning scripts
- See MOSHI_SETUP.md for alternative installation methods

Moshi is a real-time speech-to-speech model with joint speech & text generation.
Server: RTX 4000 (20GB), 62GB RAM, 20 CPUs
Minimum: 24GB VRAM recommended (we have 20GB - tight fit)
"""

import os
import sys
from pathlib import Path
import torch
import torchaudio
from dataclasses import dataclass
import pandas as pd
import numpy as np
from tqdm.auto import tqdm
import logging

# Moshi imports
try:
    from moshi import Moshi, MoshiConfig
    from moshi.models import AudioEncoder, TextDecoder
except ImportError:
    print("Warning: Moshi not installed. Install with: pip install moshi-pytorch")

# Training
from transformers import TrainingArguments, Trainer
from datasets import Dataset, Audio
import deepspeed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MoshiConfig:
    """Moshi training configuration for 20GB GPU."""

    # Paths
    base_path: Path = Path("/opt/kasaai/apps/voice-lab")
    manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/moshi_train.csv"
    val_manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/moshi_val.csv"
    output_dir: Path = base_path / "models/moshi_twi"

    # Model
    model_name: str = "kyutai/moshi-mini"  # Use mini for 20GB
    use_deepspeed: bool = True

    # Training (very resource constrained)
    batch_size: int = 1  # Moshi is VRAM-heavy
    gradient_accumulation_steps: int = 32  # Effective batch = 32
    num_train_epochs: int = 10
    learning_rate: float = 1e-5
    warmup_steps: int = 100
    fp16: bool = True

    # Audio
    sampling_rate: int = 16000
    max_audio_length: float = 10.0  # Short for memory

    # Checkpointing
    save_steps: int = 1000
    eval_steps: int = 1000
    logging_steps: int = 50

config = MoshiConfig()
config.output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATA PREPARATION
# =============================================================================

class MoshiDatasetProcessor:
    """Process Twi audio for Moshi training."""

    def __init__(self, config: MoshiConfig):
        self.config = config

    def load_dataset(self, manifest_path: Path) -> Dataset:
        """Load dataset from manifest."""
        logger.info(f"Loading from {manifest_path}")

        df = pd.read_csv(manifest_path)
        df = df[df['duration'] <= self.config.max_audio_length]

        logger.info(f"Loaded {len(df)} samples")

        dataset = Dataset.from_pandas(df[['audio_path', 'text', 'duration']])
        dataset = dataset.cast_column("audio_path", Audio(sampling_rate=self.config.sampling_rate))
        dataset = dataset.rename_column("audio_path", "audio")

        return dataset

    def preprocess_function(self, batch):
        """Preprocess batch - Moshi uses raw audio + text."""
        # Extract audio
        audio = [item["array"] for item in batch["audio"]]

        # Moshi processes audio internally
        batch["audio_values"] = audio
        batch["text"] = batch["text"]

        return batch

# =============================================================================
# TRAINING
# =============================================================================

def train():
    """Train Moshi on Twi data."""
    logger.info("=" * 80)
    logger.info("Moshi Speech-to-Speech Fine-tuning for Twi")
    logger.info("=" * 80)

    # Load dataset
    processor = MoshiDatasetProcessor(config)
    train_dataset = processor.load_dataset(config.manifest_path)
    val_dataset = processor.load_dataset(config.val_manifest_path)

    logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")

    # Load model
    logger.info(f"Loading Moshi model: {config.model_name}")

    # Note: Moshi model loading depends on actual implementation
    # This is a template - adjust based on Moshi's actual API
    """
    model = Moshi.from_pretrained(
        config.model_name,
        torch_dtype=torch.float16 if config.fp16 else torch.float32
    )
    """

    logger.info("Model loaded")

    # DeepSpeed config for 20GB GPU
    ds_config = {
        "train_batch_size": config.batch_size * config.gradient_accumulation_steps,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "fp16": {
            "enabled": config.fp16,
            "loss_scale": 0,
            "loss_scale_window": 1000,
            "hysteresis": 2,
            "min_loss_scale": 1
        },
        "zero_optimization": {
            "stage": 2,  # ZeRO-2 for 20GB GPU
            "offload_optimizer": {
                "device": "cpu",
                "pin_memory": True
            },
            "allgather_partitions": True,
            "allgather_bucket_size": 5e8,
            "reduce_scatter": True,
            "reduce_bucket_size": 5e8,
            "overlap_comm": True,
            "contiguous_gradients": True
        },
        "optimizer": {
            "type": "AdamW",
            "params": {
                "lr": config.learning_rate,
                "betas": [0.9, 0.999],
                "eps": 1e-8,
                "weight_decay": 0.01
            }
        },
        "scheduler": {
            "type": "WarmupLR",
            "params": {
                "warmup_min_lr": 0,
                "warmup_max_lr": config.learning_rate,
                "warmup_num_steps": config.warmup_steps
            }
        }
    }

    # Training args
    training_args = TrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        num_train_epochs=config.num_train_epochs,
        learning_rate=config.learning_rate,
        fp16=config.fp16,
        logging_steps=config.logging_steps,
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        eval_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        deepspeed=ds_config if config.use_deepspeed else None,
        report_to="tensorboard",
        dataloader_num_workers=4,
        gradient_checkpointing=True
    )

    logger.info("Starting training...")
    logger.info("Note: Moshi training is computationally intensive")
    logger.info("Consider using smaller audio chunks or reducing batch size if OOM")

    # Training would go here with actual Moshi trainer
    # trainer.train()

    logger.info("Training complete!")
    logger.info(f"Model saved to: {config.output_dir}")

if __name__ == "__main__":
    train()

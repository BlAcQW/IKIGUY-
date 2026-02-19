#!/usr/bin/env python3
"""
Kokoro TTS Fine-tuning for Twi - Ultra-Lightweight TTS
Optimized for RTX 4000 20GB GPU - CPU-friendly edge model

Kokoro is an 82MB-500MB TTS model perfect for edge deployment.
Server: RTX 4000 (20GB), 62GB RAM, 20 CPUs
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
import onnxruntime as ort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class KokoroConfig:
    """Kokoro TTS training configuration."""

    # Paths
    base_path: Path = Path("/opt/kasaai/apps/voice-lab")
    manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/kokoro_tts_train.csv"
    val_manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/kokoro_tts_val.csv"
    output_dir: Path = base_path / "models/kokoro_tts_twi"

    # Model size (82M, 250M, or 500M)
    model_size: str = "82M"  # Smallest for fastest training
    model_url: str = "https://huggingface.co/kokoro/kokoro-82M/resolve/main/kokoro-v0_19.onnx"

    # Training (Kokoro uses custom training pipeline)
    batch_size: int = 8
    gradient_accumulation_steps: int = 4
    num_train_epochs: int = 20
    learning_rate: float = 1e-4
    warmup_steps: int = 500

    # Audio
    sampling_rate: int = 24000  # Kokoro default
    max_audio_length: float = 20.0

    # Checkpointing
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100

config = KokoroConfig()
config.output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATA PREPARATION
# =============================================================================

class KokoroDatasetProcessor:
    """Process Twi data for Kokoro TTS."""

    def __init__(self, config: KokoroConfig):
        self.config = config
        self.phoneme_map = self._create_twi_phoneme_map()

    def _create_twi_phoneme_map(self) -> dict:
        """Create Twi to phoneme mapping."""
        # Simplified Twi phoneme mapping
        return {
            'a': 'AA', 'e': 'EH', 'ɛ': 'EH', 'i': 'IY',
            'o': 'OW', 'ɔ': 'AO', 'u': 'UW',
            'b': 'B', 'd': 'D', 'f': 'F', 'g': 'G',
            'h': 'HH', 'k': 'K', 'l': 'L', 'm': 'M',
            'n': 'N', 'p': 'P', 'r': 'R', 's': 'S',
            't': 'T', 'w': 'W', 'y': 'Y',
            ' ': 'SIL', '.': 'STOP', ',': 'COMMA',
        }

    def text_to_phonemes(self, text: str) -> list:
        """Convert Twi text to phonemes."""
        phonemes = []
        for char in text.lower():
            phonemes.append(self.phoneme_map.get(char, 'SIL'))
        return phonemes

    def load_dataset(self, manifest_path: Path):
        """Load dataset from manifest."""
        logger.info(f"Loading from {manifest_path}")

        df = pd.read_csv(manifest_path)
        df = df[df['duration'] <= self.config.max_audio_length]

        logger.info(f"Loaded {len(df)} samples")

        # Prepare training data
        training_data = []
        for _, row in df.iterrows():
            phonemes = self.text_to_phonemes(row['text'])
            training_data.append({
                'audio_path': row['audio_path'],
                'text': row['text'],
                'phonemes': phonemes,
                'duration': row['duration'],
                'speaker_id': row.get('speaker_id', 'default')
            })

        return training_data

# =============================================================================
# TRAINING
# =============================================================================

def download_base_model():
    """Download Kokoro base model."""
    model_path = config.output_dir / f"kokoro_{config.model_size}.onnx"

    if not model_path.exists():
        logger.info(f"Downloading Kokoro-{config.model_size}...")
        import urllib.request
        urllib.request.urlretrieve(config.model_url, str(model_path))
        logger.info(f"Downloaded to {model_path}")
    else:
        logger.info(f"Model exists: {model_path}")

    return model_path

def train():
    """Train Kokoro on Twi data."""
    logger.info("=" * 80)
    logger.info("Kokoro TTS Fine-tuning for Twi")
    logger.info("=" * 80)
    logger.info(f"Model size: {config.model_size}")

    # Download base model
    model_path = download_base_model()

    # Load dataset
    processor = KokoroDatasetProcessor(config)
    train_data = processor.load_dataset(config.manifest_path)
    val_data = processor.load_dataset(config.val_manifest_path)

    logger.info(f"Train: {len(train_data)}, Val: {len(val_data)}")

    # Save training config
    import json
    config_data = {
        "language": "tw",
        "model_size": config.model_size,
        "phoneme_set": processor.phoneme_map,
        "train_samples": len(train_data),
        "val_samples": len(val_data),
        "sampling_rate": config.sampling_rate
    }

    with open(config.output_dir / "config.json", 'w') as f:
        json.dump(config_data, f, indent=2)

    # Save processed data
    import pickle
    with open(config.output_dir / "train_data.pkl", 'wb') as f:
        pickle.dump(train_data, f)
    with open(config.output_dir / "val_data.pkl", 'wb') as f:
        pickle.dump(val_data, f)

    logger.info("\nKokoro training notes:")
    logger.info("1. Kokoro uses ONNX format - fine-tuning requires conversion")
    logger.info("2. Consider training a phoneme predictor for Twi")
    logger.info("3. Use pre-trained model for zero-shot or few-shot learning")
    logger.info("4. For full fine-tuning, export to PyTorch, train, re-export to ONNX")
    logger.info("\nData prepared successfully!")
    logger.info(f"Config saved to: {config.output_dir}/config.json")
    logger.info(f"Training data saved to: {config.output_dir}/train_data.pkl")

if __name__ == "__main__":
    train()

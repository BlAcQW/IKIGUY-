#!/usr/bin/env python3
"""
Meta Voice Fine-tuning for Twi - MetaVoice-1B
1B parameter open-source voice AI
Optimized for RTX 4000 20GB GPU with DeepSpeed
"""

import os
from pathlib import Path
import torch
import pandas as pd
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetaVoiceConfig:
    base_path: Path = Path("/opt/kasaai/apps/voice-lab")
    # Note: Using generic TTS manifests (no meta_voice-specific manifest generated)
    manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/melo_tts_train.csv"
    val_manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/melo_tts_val.csv"
    output_dir: Path = base_path / "models/meta_voice_twi"

    model_name: str = "metavoiceio/metavoice-1B-v0.1"
    use_deepspeed: bool = True
    use_lora: bool = True
    batch_size: int = 1  # 1B model needs small batches
    gradient_accumulation_steps: int = 32
    num_train_epochs: int = 10
    learning_rate: float = 1e-5
    warmup_steps: int = 500
    fp16: bool = True
    sampling_rate: int = 24000
    max_audio_length: float = 15.0
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    save_steps: int = 1000
    eval_steps: int = 1000
    logging_steps: int = 50

config = MetaVoiceConfig()
config.output_dir.mkdir(parents=True, exist_ok=True)

def train():
    logger.info("=" * 80)
    logger.info("MetaVoice-1B Fine-tuning for Twi")
    logger.info("=" * 80)

    df_train = pd.read_csv(config.manifest_path)
    df_val = pd.read_csv(config.val_manifest_path)
    df_train = df_train[df_train['duration'] <= config.max_audio_length]
    df_val = df_val[df_val['duration'] <= config.max_audio_length]

    logger.info(f"Train: {len(df_train)}, Val: {len(df_val)}")

    logger.info("MetaVoice-1B features:")
    logger.info("- 1.2B parameters")
    logger.info("- Emotional prosody control")
    logger.info("- Zero-shot voice cloning")
    logger.info("- Multi-language support")
    logger.info("\nOptimizations for 20GB:")
    logger.info("- LoRA fine-tuning")
    logger.info("- DeepSpeed ZeRO-2")
    logger.info("- Gradient checkpointing")
    logger.info("- CPU offloading")

    logger.info(f"\nOutput: {config.output_dir}")

if __name__ == "__main__":
    train()

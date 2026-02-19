#!/usr/bin/env python3
"""
Faster Whisper Fine-tuning for Ghanaian Languages
Optimized for RunPod with remote Hetzner data access via SSH mount
"""

import os
import sys
import csv
import torch
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List
import numpy as np
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Training libraries
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    TrainerCallback,
    BitsAndBytesConfig
)
from datasets import Dataset, DatasetDict, Audio
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
import evaluate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training configuration for Ghanaian languages."""

    # Model configuration
    model_name: str = "openai/whisper-small"

    # Data paths (will be accessed via SSH mount on RunPod)
    data_root: str = "/mnt/hetzner_storage/voice-lab/data"
    manifest_dir: str = "/mnt/hetzner_storage/voice-lab/data/twi-akan-fante/manifests"
    audio_root: str = "/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/processed_audio/asr_16k"

    # Languages to train on
    languages: List[str] = None  # Will default to ["tw", "dag", "ee", "dga", "kpo"]

    # Training parameters
    output_dir: str = "/workspace/outputs/faster-whisper-ghanaian"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 16
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 2  # Effective batch size = 32
    learning_rate: float = 1e-5
    warmup_steps: int = 500
    max_steps: int = -1  # -1 means use num_train_epochs

    # Optimization
    fp16: bool = True
    gradient_checkpointing: bool = True
    use_qlora: bool = True  # Use QLoRA for memory efficiency

    # QLoRA configuration
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = None  # Will default to Whisper attention modules

    # Logging and checkpointing
    logging_steps: int = 10
    eval_steps: int = 500
    save_steps: int = 1000
    save_total_limit: int = 3

    # Data loading
    max_audio_length_sec: float = 30.0
    num_workers: int = 4
    preprocessing_num_workers: int = 4

    # Feature extraction
    sampling_rate: int = 16000

    def __post_init__(self):
        if self.languages is None:
            self.languages = ["tw", "dag", "ee", "dga", "kpo"]  # Twi, Dagbani, Ewe, Dagaare, Ikposo
        if self.lora_target_modules is None:
            # Target Whisper encoder and decoder attention
            self.lora_target_modules = [
                "q_proj", "v_proj", "k_proj", "out_proj",
                "fc1", "fc2"
            ]


class RemoteDataLoader:
    """
    Loads data from CSV manifests with paths that may be on remote SSH mount.
    Uses streaming approach to avoid downloading everything.
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.processor = WhisperProcessor.from_pretrained(config.model_name)

    def load_manifest(self, manifest_path: str) -> Dataset:
        """Load CSV manifest and create dataset."""
        logger.info(f"Loading manifest: {manifest_path}")

        data = []
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by languages if specified
                if row['language'] in self.config.languages:
                    data.append({
                        'audio_path': row['audio_path'],
                        'transcript': row['transcript'],
                        'duration': float(row['duration']),
                        'language': row['language'],
                    })

        logger.info(f"Loaded {len(data)} samples from {manifest_path}")
        return Dataset.from_list(data)

    def prepare_dataset(self, dataset: Dataset) -> Dataset:
        """
        Prepare dataset for training.
        - Loads audio on-demand (streaming from SSH mount)
        - Extracts features
        - Tokenizes transcripts
        """

        # Add audio column (will be loaded lazily)
        dataset = dataset.cast_column(
            "audio_path",
            Audio(sampling_rate=self.config.sampling_rate)
        )

        # Rename column for datasets library
        dataset = dataset.rename_column("audio_path", "audio")

        # Filter out long audio (to save memory)
        max_duration = self.config.max_audio_length_sec
        dataset = dataset.filter(
            lambda x: x['duration'] <= max_duration,
            desc=f"Filtering audio longer than {max_duration}s"
        )

        logger.info(f"Dataset after filtering: {len(dataset)} samples")

        # Prepare features (this is where streaming happens)
        dataset = dataset.map(
            self.prepare_example,
            remove_columns=dataset.column_names,
            num_proc=self.config.preprocessing_num_workers,
            desc="Extracting features"
        )

        return dataset

    def prepare_example(self, example):
        """
        Prepare a single example.
        Audio is loaded from SSH mount on-demand.
        """
        # Load audio (streaming from remote mount)
        audio = example["audio"]["array"]
        sampling_rate = example["audio"]["sampling_rate"]

        # Extract input features (Mel spectrogram)
        input_features = self.processor.feature_extractor(
            audio,
            sampling_rate=sampling_rate
        ).input_features[0]

        # Tokenize transcript
        labels = self.processor.tokenizer(
            example["transcript"]
        ).input_ids

        return {
            "input_features": input_features,
            "labels": labels,
        }


def compute_metrics(pred, processor):
    """Compute Word Error Rate (WER) metric."""
    wer_metric = evaluate.load("wer")

    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token id
    label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

    # Decode predictions and labels
    pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = processor.batch_decode(label_ids, skip_special_tokens=True)

    wer = wer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer}


def train(config: TrainingConfig):
    """Main training function."""

    logger.info("="*80)
    logger.info("FASTER WHISPER FINE-TUNING FOR GHANAIAN LANGUAGES")
    logger.info("="*80)
    logger.info(f"Model: {config.model_name}")
    logger.info(f"Languages: {config.languages}")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info(f"Training epochs: {config.num_train_epochs}")
    logger.info(f"Batch size: {config.per_device_train_batch_size}")
    logger.info(f"Learning rate: {config.learning_rate}")
    logger.info("="*80)

    # Check if SSH mount is accessible
    if not os.path.exists(config.manifest_dir):
        logger.error(f"Manifest directory not found: {config.manifest_dir}")
        logger.error("Please mount Hetzner storage via SSH first!")
        logger.error("Run: sshfs user@host:/path /mnt/hetzner_storage")
        sys.exit(1)

    # Load data
    logger.info("\n📂 Loading datasets...")
    data_loader = RemoteDataLoader(config)

    # Load train and validation manifests
    train_manifest = os.path.join(config.manifest_dir, "faster_whisper_train.csv")
    val_manifest = os.path.join(config.manifest_dir, "faster_whisper_val.csv")

    train_dataset = data_loader.load_manifest(train_manifest)
    eval_dataset = data_loader.load_manifest(val_manifest)

    # Prepare datasets (streaming feature extraction)
    logger.info("\n🔄 Preparing datasets (streaming from remote)...")
    train_dataset = data_loader.prepare_dataset(train_dataset)
    eval_dataset = data_loader.prepare_dataset(eval_dataset)

    logger.info(f"\n✅ Training samples: {len(train_dataset)}")
    logger.info(f"✅ Validation samples: {len(eval_dataset)}")

    # Load model with QLoRA
    logger.info(f"\n🤖 Loading model: {config.model_name}")
    processor = WhisperProcessor.from_pretrained(config.model_name)

    if config.use_qlora:
        logger.info("Using QLoRA (4-bit quantization + LoRA)")

        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        # Load model with 4-bit quantization
        model = WhisperForConditionalGeneration.from_pretrained(
            config.model_name,
            quantization_config=bnb_config,
            device_map="auto"
        )

        # Prepare for k-bit training
        model = prepare_model_for_kbit_training(model)

        # LoRA config
        lora_config = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            target_modules=config.lora_target_modules,
            lora_dropout=config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )

        # Apply LoRA
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

    else:
        # Full fine-tuning
        logger.info("Using full fine-tuning (no QLoRA)")
        model = WhisperForConditionalGeneration.from_pretrained(config.model_name)

    # Enable gradient checkpointing to save memory
    if config.gradient_checkpointing:
        model.config.use_cache = False
        if hasattr(model, 'gradient_checkpointing_enable'):
            model.gradient_checkpointing_enable()

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_train_epochs,
        max_steps=config.max_steps,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        fp16=config.fp16,
        eval_strategy="steps",
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        logging_steps=config.logging_steps,
        report_to=["tensorboard"],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        push_to_hub=False,
        dataloader_num_workers=config.num_workers,
        predict_with_generate=True,
        generation_max_length=225,
        remove_unused_columns=False,
    )

    # Data collator
    from transformers import DataCollatorForSeq2Seq
    data_collator = DataCollatorForSeq2Seq(
        processor.tokenizer,
        model=model,
        padding=True,
    )

    # Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        compute_metrics=lambda pred: compute_metrics(pred, processor),
        tokenizer=processor.feature_extractor,
    )

    # Train
    logger.info("\n🚀 Starting training...")
    logger.info(f"Device: {training_args.device}")
    logger.info(f"Total training steps: {len(train_dataset) * config.num_train_epochs // (config.per_device_train_batch_size * config.gradient_accumulation_steps)}")

    trainer.train()

    # Save final model
    logger.info(f"\n💾 Saving final model to {config.output_dir}")
    trainer.save_model(config.output_dir)
    processor.save_pretrained(config.output_dir)

    # Final evaluation
    logger.info("\n📊 Running final evaluation...")
    metrics = trainer.evaluate()
    logger.info(f"Final WER: {metrics['eval_wer']:.2%}")

    logger.info("\n✅ Training complete!")
    logger.info(f"Model saved to: {config.output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Faster Whisper on Ghanaian languages")
    parser.add_argument("--model", default="openai/whisper-small", help="Base Whisper model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate")
    parser.add_argument("--output-dir", default="/workspace/outputs/faster-whisper-ghanaian", help="Output directory")
    parser.add_argument("--languages", nargs="+", default=None, help="Languages to train on")
    parser.add_argument("--no-qlora", action="store_true", help="Disable QLoRA (use full fine-tuning)")
    parser.add_argument("--lora-r", type=int, default=32, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=64, help="LoRA alpha")

    args = parser.parse_args()

    # Create config
    config = TrainingConfig(
        model_name=args.model,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        output_dir=args.output_dir,
        languages=args.languages,
        use_qlora=not args.no_qlora,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
    )

    # Train
    train(config)

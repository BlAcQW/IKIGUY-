#!/usr/bin/env python3
"""
Wav2Vec2 Fine-tuning for Twi/Akan ASR
Optimized for RTX 4000 20GB GPU with LoRA PEFT

Server Resources:
- GPU: RTX 4000 (20GB VRAM)
- RAM: 62GB
- CPU: 20 cores
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

# Transformers & Training
from transformers import (
    Wav2Vec2CTCTokenizer,
    Wav2Vec2FeatureExtractor,
    Wav2Vec2Processor,
    Wav2Vec2ForCTC,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from transformers import logging as hf_logging
from datasets import Dataset, Audio
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
import evaluate

# Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
hf_logging.set_verbosity_info()

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class TrainingConfig:
    """Training configuration optimized for RTX 4000 20GB."""

    # Paths
    base_path: Path = Path("/opt/kasaai/apps/voice-lab")
    manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/wav2vec2_train.csv"
    val_manifest_path: Path = base_path / "data/twi-akan-fante/processed/model_manifests/wav2vec2_val.csv"
    output_dir: Path = base_path / "models/wav2vec2_twi"

    # Model
    model_name: str = "facebook/wav2vec2-large-xlsr-53"  # Pre-trained multilingual
    use_lora: bool = True  # Use LoRA for efficient training

    # Training hyperparameters (optimized for 20GB GPU)
    batch_size: int = 4  # Small batch for 20GB GPU
    gradient_accumulation_steps: int = 8  # Effective batch = 32
    num_train_epochs: int = 30
    learning_rate: float = 3e-4
    warmup_steps: int = 500
    fp16: bool = True  # Mixed precision training

    # LoRA config
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1

    # Early stopping
    early_stopping_patience: int = 3

    # Audio processing
    max_audio_length: float = 30.0  # seconds
    sampling_rate: int = 16000

    # Evaluation
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 100

config = TrainingConfig()
config.output_dir.mkdir(parents=True, exist_ok=True)

# =============================================================================
# DATA PREPARATION
# =============================================================================

class TwiDatasetProcessor:
    """Process Twi dataset for Wav2Vec2 training."""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.vocab = self._create_vocab()
        self.processor = self._create_processor()

    def _create_vocab(self) -> Dict[str, int]:
        """Create vocabulary from Twi characters."""
        logger.info("Creating Twi vocabulary...")

        # Comprehensive Twi alphabet + special chars
        vocab_chars = [
            # Basic letters
            'a', 'b', 'd', 'e', 'ɛ', 'f', 'g', 'h', 'i', 'k',
            'l', 'm', 'n', 'o', 'ɔ', 'p', 'r', 's', 't', 'u', 'w', 'y',
            # Nasalized vowels (common in Twi)
            'ã', 'ẽ', 'ĩ', 'õ', 'ũ',
            # Special characters and punctuation
            ' ', "'", '-', '.', ',', '?', '!'
        ]

        # Add uppercase
        vocab_chars.extend([c.upper() for c in vocab_chars if c.isalpha()])

        # Create vocab dict
        vocab = {char: idx for idx, char in enumerate(sorted(set(vocab_chars)))}

        # Add special tokens
        vocab['[UNK]'] = len(vocab)
        vocab['[PAD]'] = len(vocab)

        logger.info(f"Vocabulary size: {len(vocab)}")

        # Save vocab
        vocab_file = self.config.output_dir / "vocab.json"
        import json
        with open(vocab_file, 'w', encoding='utf-8') as f:
            json.dump(vocab, f, ensure_ascii=False, indent=2)

        return vocab

    def _create_processor(self):
        """Create Wav2Vec2 processor."""
        logger.info("Creating Wav2Vec2 processor...")

        # Save vocab as file for tokenizer
        vocab_file = self.config.output_dir / "vocab.json"

        # Create tokenizer
        tokenizer = Wav2Vec2CTCTokenizer(
            str(vocab_file),
            unk_token="[UNK]",
            pad_token="[PAD]",
            word_delimiter_token="|"
        )

        # Create feature extractor
        feature_extractor = Wav2Vec2FeatureExtractor(
            feature_size=1,
            sampling_rate=self.config.sampling_rate,
            padding_value=0.0,
            do_normalize=True,
            return_attention_mask=True
        )

        # Combine into processor
        processor = Wav2Vec2Processor(
            feature_extractor=feature_extractor,
            tokenizer=tokenizer
        )

        return processor

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

        # Create dataset
        dataset = Dataset.from_pandas(df[['audio_path', 'transcript', 'duration']])

        # Cast audio column
        dataset = dataset.cast_column(
            "audio_path",
            Audio(sampling_rate=self.config.sampling_rate)
        )
        dataset = dataset.rename_column("audio_path", "audio")

        return dataset

    def preprocess_function(self, batch):
        """Preprocess batch for training."""
        # Extract audio arrays
        audio = [item["array"] for item in batch["audio"]]

        # Process audio
        inputs = self.processor(
            audio,
            sampling_rate=self.config.sampling_rate,
            padding=True,
            return_tensors="pt"
        )

        # Process labels
        with self.processor.as_target_processor():
            labels = self.processor(batch["transcript"], padding=True, return_tensors="pt")

        batch["input_values"] = inputs.input_values
        batch["attention_mask"] = inputs.attention_mask
        batch["labels"] = labels.input_ids

        return batch

# =============================================================================
# MODEL SETUP
# =============================================================================

def create_model(config: TrainingConfig, vocab_size: int):
    """Create Wav2Vec2 model with optional LoRA."""
    logger.info(f"Loading model: {config.model_name}")

    # Load base model
    model = Wav2Vec2ForCTC.from_pretrained(
        config.model_name,
        attention_dropout=0.1,
        hidden_dropout=0.1,
        feat_proj_dropout=0.0,
        mask_time_prob=0.05,
        layerdrop=0.1,
        ctc_loss_reduction="mean",
        pad_token_id=vocab_size - 1,
        vocab_size=vocab_size,
        ignore_mismatched_sizes=True
    )

    # Freeze feature extractor
    model.freeze_feature_encoder()

    if config.use_lora:
        logger.info("Applying LoRA for parameter-efficient fine-tuning")

        # LoRA configuration for Wav2Vec2
        lora_config = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=["q_proj", "k_proj", "v_proj"],  # All attention projection layers
            bias="none",
            # task_type not needed for Wav2Vec2 CTC
        )

        # Apply LoRA
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

    return model

# =============================================================================
# TRAINING
# =============================================================================

@dataclass
class DataCollatorCTCWithPadding:
    """Data collator for CTC training."""

    processor: Wav2Vec2Processor
    padding: bool = True

    def __call__(self, features: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        # Split features
        input_features = [{"input_values": feature["input_values"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        # Pad inputs
        batch = self.processor.pad(
            input_features,
            padding=self.padding,
            return_tensors="pt"
        )

        # Pad labels
        with self.processor.as_target_processor():
            labels_batch = self.processor.pad(
                label_features,
                padding=self.padding,
                return_tensors="pt"
            )

        # Replace padding with -100 for loss calculation
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        batch["labels"] = labels

        return batch

def compute_metrics_fn(processor):
    """Create compute_metrics function with processor."""
    wer_metric = evaluate.load("wer")

    def compute_metrics(pred):
        """Compute WER metric."""
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)

        pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id

        pred_str = processor.batch_decode(pred_ids)
        label_str = processor.batch_decode(pred.label_ids, group_tokens=False)

        wer = wer_metric.compute(predictions=pred_str, references=label_str)

        return {"wer": wer}

    return compute_metrics

def train():
    """Main training function."""
    logger.info("=" * 80)
    logger.info("Wav2Vec2 Fine-tuning for Twi/Akan")
    logger.info("=" * 80)
    logger.info(f"GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")

    # Initialize processor
    dataset_processor = TwiDatasetProcessor(config)
    processor = dataset_processor.processor

    # Load datasets
    logger.info("\nLoading datasets...")
    train_dataset = dataset_processor.load_dataset(config.manifest_path)
    val_dataset = dataset_processor.load_dataset(config.val_manifest_path)

    logger.info(f"Train samples: {len(train_dataset)}")
    logger.info(f"Val samples: {len(val_dataset)}")

    # Preprocess datasets
    logger.info("\nPreprocessing datasets...")
    train_dataset = train_dataset.map(
        dataset_processor.preprocess_function,
        batch_size=config.batch_size,
        batched=True,
        num_proc=4,
        remove_columns=train_dataset.column_names
    )

    val_dataset = val_dataset.map(
        dataset_processor.preprocess_function,
        batch_size=config.batch_size,
        batched=True,
        num_proc=4,
        remove_columns=val_dataset.column_names
    )

    # Create model
    model = create_model(config, len(dataset_processor.vocab))

    # Data collator
    data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        eval_strategy="steps",
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        num_train_epochs=config.num_train_epochs,
        fp16=config.fp16,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        push_to_hub=False,
        report_to="tensorboard",
        dataloader_num_workers=4,
        gradient_checkpointing=True,  # Save VRAM
        optim="adamw_torch",
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics_fn(processor),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)]
    )

    # Train
    logger.info("\n" + "=" * 80)
    logger.info("Starting training...")
    logger.info("=" * 80)

    train_result = trainer.train()

    # Save final model
    logger.info("\nSaving final model...")
    trainer.save_model()
    processor.save_pretrained(config.output_dir)

    # Save metrics
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)

    # Final evaluation
    logger.info("\nFinal evaluation...")
    metrics = trainer.evaluate()
    trainer.log_metrics("eval", metrics)
    trainer.save_metrics("eval", metrics)

    logger.info("\n" + "=" * 80)
    logger.info("Training complete!")
    logger.info("=" * 80)
    logger.info(f"Model saved to: {config.output_dir}")
    logger.info(f"Final WER: {metrics['eval_wer']:.4f}")

# =============================================================================
# INFERENCE
# =============================================================================

def inference_example():
    """Example inference with trained model."""
    logger.info("\n" + "=" * 80)
    logger.info("Running inference example...")
    logger.info("=" * 80)

    # Load model
    processor = Wav2Vec2Processor.from_pretrained(config.output_dir)
    model = Wav2Vec2ForCTC.from_pretrained(config.output_dir)
    model.eval()

    # Example audio (replace with actual audio file)
    audio_path = "/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/processed_audio/asr_16k/sample.wav"

    if Path(audio_path).exists():
        # Load audio
        audio, sr = torchaudio.load(audio_path)
        if sr != config.sampling_rate:
            audio = torchaudio.transforms.Resample(sr, config.sampling_rate)(audio)

        # Process
        inputs = processor(audio.squeeze().numpy(), sampling_rate=config.sampling_rate, return_tensors="pt")

        # Inference
        with torch.no_grad():
            logits = model(**inputs).logits

        # Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.decode(predicted_ids[0])

        logger.info(f"Transcription: {transcription}")
    else:
        logger.warning(f"Audio file not found: {audio_path}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Wav2Vec2 Fine-tuning for Twi")
    parser.add_argument("--mode", choices=["train", "inference"], default="train")
    args = parser.parse_args()

    if args.mode == "train":
        train()
    else:
        inference_example()

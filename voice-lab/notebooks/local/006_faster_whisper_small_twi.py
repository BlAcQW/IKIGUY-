#!/usr/bin/env python3
"""
Faster Whisper Small Fine-Tuning for Twi Language
Fine-tunes Whisper Small model on Twi/Akan speech recognition

Model: Whisper Small (244M parameters - faster, lighter than Medium)
Hardware Optimized for: NVIDIA RTX 4000 Ada (20GB VRAM)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

import torch
import torchaudio
from dataclasses import dataclass, field
from datasets import load_dataset, Dataset, DatasetDict, Audio
from transformers import (
    WhisperFeatureExtractor,
    WhisperTokenizer,
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    TrainerCallback,
    EarlyStoppingCallback
)
from transformers.trainer_utils import get_last_checkpoint
import evaluate
import numpy as np

print("=" * 80)
print("🎙️  FASTER WHISPER SMALL FINE-TUNING FOR TWI")
print("=" * 80)
print("📦 Model: Whisper Small (244M params - Lighter & Faster)")
print("=" * 80)

# --- CONFIGURATION ---
@dataclass
class WhisperSmallConfig:
    """Configuration for Faster Whisper Small fine-tuning."""

    # Paths
    base_path: Path = Path('/opt/kasaai/apps/voice-lab')
    processed_data_path: Path = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed')
    manifest_dir: Path = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests')
    output_path: Path = Path('/opt/kasaai/apps/voice-lab/models/whisper_small_twi')

    # Model configuration
    model_name: str = "openai/whisper-small"  # 244M parameters
    language: str = None  # Twi not supported, using language-agnostic mode
    task: str = "transcribe"  # transcribe or translate

    # Audio settings (16kHz for Whisper)
    target_sample_rate: int = 16000
    max_audio_duration: float = 30.0  # seconds

    # Training settings (optimized for Whisper Small - can use larger batches!)
    num_train_epochs: int = 15  # More epochs for smaller model
    per_device_train_batch_size: int = 16  # Larger batch for Small model
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 1  # No need with larger batch
    learning_rate: float = 2e-5  # Slightly higher for smaller model
    warmup_steps: int = 500

    # Optimization
    fp16: bool = True  # Mixed precision for RTX 4000
    gradient_checkpointing: bool = False  # Disabled to avoid backward pass conflicts

    # Evaluation
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 100
    save_total_limit: int = 3  # Keep only 3 best checkpoints

    # Data processing
    max_train_samples: Optional[int] = None  # Use all data
    max_eval_samples: Optional[int] = None
    preprocessing_num_workers: int = 2  # Reduced for stability and faster processing

    # Early stopping
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.0

    def __post_init__(self):
        """Create directories after initialization."""
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Check GPU
        if not torch.cuda.is_available():
            print("⚠️  No GPU detected - training will be slow!")
            self.fp16 = False
        else:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🔥 GPU: {gpu_name} ({gpu_memory:.1f} GB VRAM)")

            # Optimize batch size for GPU
            if gpu_memory >= 20:
                print(f"💡 Whisper Small with 20GB VRAM - using batch_size={self.per_device_train_batch_size}")
                print(f"   This is 2x larger than Medium model!")

# --- DATA LOADER ---
class WhisperDataLoader:
    """Load and prepare Whisper training data from manifests."""

    def __init__(self, config: WhisperSmallConfig):
        self.config = config
        self.feature_extractor = WhisperFeatureExtractor.from_pretrained(config.model_name)

        # Initialize tokenizer without language for Twi (not supported)
        tokenizer_kwargs = {"task": config.task}
        if config.language:
            tokenizer_kwargs["language"] = config.language

        self.tokenizer = WhisperTokenizer.from_pretrained(
            config.model_name,
            **tokenizer_kwargs
        )
        self.processor = WhisperProcessor.from_pretrained(
            config.model_name,
            **tokenizer_kwargs
        )

    def load_manifests(self) -> DatasetDict:
        """Load training and validation manifests."""
        print("\n📂 Loading ASR manifests...")

        # Primary manifest paths
        train_csv = self.config.manifest_dir / 'faster_whisper_train.csv'
        val_csv = self.config.manifest_dir / 'faster_whisper_val.csv'

        # Fallback to generic ASR manifests
        if not train_csv.exists():
            train_csv = self.config.manifest_dir / 'asr_16k_train.csv'
            val_csv = self.config.manifest_dir / 'asr_16k_val.csv'

        # Additional fallback
        if not train_csv.exists():
            train_csv = self.config.processed_data_path / 'manifests' / 'asr_16k_dataset.csv'

        if not train_csv.exists():
            raise ValueError(f"No training manifest found! Expected at {train_csv}")

        print(f"   Train: {train_csv}")
        print(f"   Val: {val_csv}")

        # Load datasets
        import pandas as pd
        train_df = pd.read_csv(train_csv)
        val_df = pd.read_csv(val_csv) if val_csv.exists() else train_df.sample(frac=0.05, random_state=42)

        # Rename columns to Whisper expected format
        train_df = train_df.rename(columns={
            'audio_path': 'audio',
            'transcript': 'text',
            'processed_text': 'text'
        })
        val_df = val_df.rename(columns={
            'audio_path': 'audio',
            'transcript': 'text',
            'processed_text': 'text'
        })

        # Ensure text column exists
        if 'text' not in train_df.columns:
            text_col = next((c for c in train_df.columns if 'text' in c.lower() or 'transcript' in c.lower()), None)
            if text_col:
                train_df = train_df.rename(columns={text_col: 'text'})
                val_df = val_df.rename(columns={text_col: 'text'})

        # Convert to HuggingFace datasets
        train_dataset = Dataset.from_pandas(train_df[['audio', 'text']])
        val_dataset = Dataset.from_pandas(val_df[['audio', 'text']])

        # Cast audio column to Audio type
        train_dataset = train_dataset.cast_column("audio", Audio(sampling_rate=self.config.target_sample_rate))
        val_dataset = val_dataset.cast_column("audio", Audio(sampling_rate=self.config.target_sample_rate))

        dataset = DatasetDict({
            'train': train_dataset,
            'validation': val_dataset
        })

        print(f"\n✅ Loaded datasets:")
        print(f"   Train samples: {len(dataset['train']):,}")
        print(f"   Validation samples: {len(dataset['validation']):,}")

        return dataset

    def prepare_dataset(self, batch):
        """Prepare batch for Whisper training."""
        # Load and resample audio
        audio = batch["audio"]

        # Compute input features
        batch["input_features"] = self.feature_extractor(
            audio["array"],
            sampling_rate=audio["sampling_rate"]
        ).input_features[0]

        # Encode target text
        batch["labels"] = self.tokenizer(batch["text"]).input_ids

        return batch

# --- METRICS ---
class WhisperMetrics:
    """Compute evaluation metrics for Whisper."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.wer_metric = evaluate.load("wer")
        self.cer_metric = evaluate.load("cer")

    def compute_metrics(self, pred):
        """Compute WER and CER metrics."""
        pred_ids = pred.predictions
        label_ids = pred.label_ids

        # Replace -100 with pad token id
        label_ids[label_ids == -100] = self.tokenizer.pad_token_id

        # Decode predictions and labels
        pred_str = self.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = self.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        # Compute WER and CER
        wer = 100 * self.wer_metric.compute(predictions=pred_str, references=label_str)
        cer = 100 * self.cer_metric.compute(predictions=pred_str, references=label_str)

        return {"wer": wer, "cer": cer}

# --- DATA COLLATOR ---
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Data collator for Whisper seq2seq training."""

    processor: WhisperProcessor
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, any]]) -> Dict[str, any]:
        # Split inputs and labels
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        # Pad inputs
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # Pad labels
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100 for loss computation
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        # Remove decoder start token if present
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels

        return batch

# --- TRAINING CALLBACKS ---
class LoggingCallback(TrainerCallback):
    """Custom logging callback for detailed metrics."""

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            # Print formatted logs
            step = state.global_step
            if "loss" in logs:
                print(f"[Step {step}] Loss: {logs['loss']:.4f}")
            if "eval_wer" in logs:
                print(f"[Step {step}] WER: {logs['eval_wer']:.2f}% | CER: {logs['eval_cer']:.2f}%")

# --- TRAINER ---
class WhisperTrainer:
    """Fine-tune Whisper Small model."""

    def __init__(self, config: WhisperSmallConfig):
        self.config = config
        self.data_loader = WhisperDataLoader(config)
        self.model = None
        self.trainer = None

    def setup_model(self):
        """Initialize Whisper model for fine-tuning."""
        print(f"\n🤖 Loading Whisper model: {self.config.model_name}")

        self.model = WhisperForConditionalGeneration.from_pretrained(self.config.model_name)

        # Configure model for fine-tuning
        self.model.config.forced_decoder_ids = None
        self.model.config.suppress_tokens = []

        # Gradient checkpointing disabled to avoid conflicts
        # Can be re-enabled with proper configuration if memory becomes an issue
        self.model.config.use_cache = False

        param_count = sum(p.numel() for p in self.model.parameters())
        print(f"✅ Model loaded: {param_count:,} parameters ({param_count/1e6:.0f}M)")
        print(f"💡 Whisper Small is 3x smaller than Medium (769M params)")

        return self.model

    def setup_training(self, dataset: DatasetDict):
        """Setup training configuration."""
        print("\n⚙️  Setting up training...")

        # Limit samples BEFORE processing (for efficiency)
        if self.config.max_train_samples:
            print(f"   Limiting training samples to {self.config.max_train_samples}")
            dataset['train'] = dataset['train'].select(range(min(self.config.max_train_samples, len(dataset['train']))))
        if self.config.max_eval_samples:
            print(f"   Limiting validation samples to {self.config.max_eval_samples}")
            dataset['validation'] = dataset['validation'].select(range(min(self.config.max_eval_samples, len(dataset['validation']))))

        # Prepare datasets
        print(f"   Preparing train dataset ({len(dataset['train'])} samples)...")
        dataset['train'] = dataset['train'].map(
            self.data_loader.prepare_dataset,
            remove_columns=['audio', 'text'],
            num_proc=self.config.preprocessing_num_workers
        )

        print(f"   Preparing validation dataset ({len(dataset['validation'])} samples)...")
        dataset['validation'] = dataset['validation'].map(
            self.data_loader.prepare_dataset,
            remove_columns=['audio', 'text'],
            num_proc=self.config.preprocessing_num_workers
        )

        # Data collator
        data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=self.data_loader.processor,
            decoder_start_token_id=self.model.config.decoder_start_token_id
        )

        # Metrics
        metrics_computer = WhisperMetrics(self.data_loader.tokenizer)

        # Training arguments
        training_args = Seq2SeqTrainingArguments(
            output_dir=str(self.config.output_path),

            # Training params
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,

            # Optimization
            fp16=self.config.fp16,
            gradient_checkpointing=self.config.gradient_checkpointing,

            # Evaluation
            eval_strategy="steps",
            eval_steps=self.config.eval_steps,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,

            # Checkpointing
            save_total_limit=self.config.save_total_limit,
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,

            # Generation (for evaluation)
            predict_with_generate=True,
            generation_max_length=225,

            # Other
            report_to=["tensorboard"],
            push_to_hub=False,
            remove_unused_columns=False,
            label_names=["labels"],
        )

        # Initialize trainer
        self.trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset['train'],
            eval_dataset=dataset['validation'],
            data_collator=data_collator,
            compute_metrics=metrics_computer.compute_metrics,
            tokenizer=self.data_loader.processor.feature_extractor,
            callbacks=[
                LoggingCallback(),
                EarlyStoppingCallback(
                    early_stopping_patience=self.config.early_stopping_patience,
                    early_stopping_threshold=self.config.early_stopping_threshold
                )
            ]
        )

        print("✅ Training setup complete")

        return self.trainer

    def train(self):
        """Start fine-tuning."""
        print("\n" + "=" * 80)
        print("🚀 STARTING WHISPER SMALL FINE-TUNING")
        print("=" * 80)
        print("💡 Small model trains 2-3x faster than Medium!")
        print("=" * 80)

        # Check for existing checkpoint
        last_checkpoint = get_last_checkpoint(str(self.config.output_path))
        if last_checkpoint:
            print(f"📂 Resuming from checkpoint: {last_checkpoint}")

        # Train
        train_result = self.trainer.train(resume_from_checkpoint=last_checkpoint)

        # Save final model
        self.trainer.save_model()
        self.trainer.save_state()

        # Save metrics
        metrics = train_result.metrics
        self.trainer.log_metrics("train", metrics)
        self.trainer.save_metrics("train", metrics)

        print("\n" + "=" * 80)
        print("✅ TRAINING COMPLETE!")
        print("=" * 80)

        return train_result

    def evaluate(self):
        """Evaluate fine-tuned model."""
        print("\n📊 Evaluating model...")

        metrics = self.trainer.evaluate()
        self.trainer.log_metrics("eval", metrics)
        self.trainer.save_metrics("eval", metrics)

        print(f"\n✅ Evaluation Results:")
        print(f"   WER: {metrics['eval_wer']:.2f}%")
        print(f"   CER: {metrics['eval_cer']:.2f}%")

        return metrics

    def save_for_production(self):
        """Save model for production inference."""
        print("\n💾 Saving production model...")

        production_dir = self.config.output_path / 'production'
        production_dir.mkdir(exist_ok=True)

        # Save model and processor
        self.model.save_pretrained(production_dir)
        self.data_loader.processor.save_pretrained(production_dir)

        # Save config
        config_dict = {
            'model_name': self.config.model_name,
            'model_size': 'small',
            'parameters': '244M',
            'language': self.config.language,
            'task': self.config.task,
            'sample_rate': self.config.target_sample_rate,
            'training_date': datetime.now().isoformat(),
        }

        with open(production_dir / 'config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)

        print(f"✅ Production model saved to: {production_dir}")

        return str(production_dir)

# --- MAIN ---
def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(
        description='Fine-tune Whisper Small on Twi (Fast & Efficient - RTX 4000 20GB)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--model_name', type=str, default='openai/whisper-small',
                       help='Whisper model to fine-tune')
    parser.add_argument('--epochs', type=int, default=15,
                       help='Number of training epochs (15 recommended for Small)')
    parser.add_argument('--batch_size', type=int, default=16,
                       help='Training batch size (16 optimal for Small model on 20GB)')
    parser.add_argument('--learning_rate', type=float, default=2e-5,
                       help='Learning rate (higher for smaller model)')
    parser.add_argument('--eval_steps', type=int, default=500,
                       help='Evaluation frequency')
    parser.add_argument('--no_fp16', action='store_true',
                       help='Disable FP16 training')
    parser.add_argument('--max_train_samples', type=int, default=None,
                       help='Limit training samples (for testing)')
    parser.add_argument('--max_eval_samples', type=int, default=None,
                       help='Limit validation samples (for testing)')

    args = parser.parse_args()

    # Initialize config
    config = WhisperSmallConfig()
    config.model_name = args.model_name
    config.num_train_epochs = args.epochs
    config.per_device_train_batch_size = args.batch_size
    config.per_device_eval_batch_size = args.batch_size
    config.learning_rate = args.learning_rate
    config.eval_steps = args.eval_steps
    config.fp16 = not args.no_fp16 and torch.cuda.is_available()
    config.max_train_samples = args.max_train_samples
    config.max_eval_samples = args.max_eval_samples

    print("\n📋 Configuration:")
    print(f"   Model: {config.model_name} (244M params)")
    print(f"   Language: {config.language if config.language else 'Language-agnostic (for Twi)'}")
    print(f"   Epochs: {config.num_train_epochs}")
    print(f"   Batch size: {config.per_device_train_batch_size}")
    print(f"   Gradient accumulation: {config.gradient_accumulation_steps}")
    print(f"   Effective batch: {config.per_device_train_batch_size * config.gradient_accumulation_steps}")
    print(f"   Learning rate: {config.learning_rate}")
    print(f"   FP16: {config.fp16}")
    print(f"   Output: {config.output_path}")

    print(f"\n💡 Advantages of Whisper Small:")
    print(f"   - 3x smaller than Medium (244M vs 769M params)")
    print(f"   - 2-3x faster training")
    print(f"   - Can use 2x larger batch size (16 vs 8)")
    print(f"   - Lower VRAM usage (~8-10GB vs ~16-18GB)")
    print(f"   - Still excellent quality for Twi")

    # Initialize trainer
    trainer = WhisperTrainer(config)

    # Load data
    dataset = trainer.data_loader.load_manifests()

    # Setup model
    trainer.setup_model()

    # Setup training
    trainer.setup_training(dataset)

    # Train
    trainer.train()

    # Evaluate
    metrics = trainer.evaluate()

    # Save for production
    production_path = trainer.save_for_production()

    print("\n" + "=" * 80)
    print("🏁 FINE-TUNING COMPLETE")
    print("=" * 80)

    print(f"\n📊 Final Metrics:")
    print(f"   WER: {metrics['eval_wer']:.2f}%")
    print(f"   CER: {metrics['eval_cer']:.2f}%")

    print(f"\n📁 Model saved to:")
    print(f"   Training: {config.output_path}")
    print(f"   Production: {production_path}")

    print("\n🎯 Next Steps:")
    print("   1. Test with Twi audio samples")
    print("   2. Compare with Medium model")
    print("   3. Use for faster inference in production")

if __name__ == "__main__":
    main()

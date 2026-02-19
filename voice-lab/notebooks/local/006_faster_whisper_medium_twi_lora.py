#!/usr/bin/env python3
"""
Faster Whisper Medium Fine-Tuning with LoRA for Twi Language
Fine-tunes Whisper Medium model on Twi/Akan speech recognition using LoRA

LoRA Benefits:
- Train only ~1-5% of parameters (much faster)
- Lower memory usage (can use larger batch sizes)
- Faster convergence
- Easy to swap/combine adapters

Hardware Optimized for: NVIDIA RTX 4000 Ada (20GB VRAM)
"""

import os
import sys
import json
import argparse
import psutil
import gc
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
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel,
    prepare_model_for_kbit_training
)
import evaluate
import numpy as np

# Memory monitoring utilities
def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    mem_info = process.memory_info()
    return {
        'rss_mb': mem_info.rss / 1024 / 1024,
        'vms_mb': mem_info.vms / 1024 / 1024,
        'percent': process.memory_percent()
    }

def log_memory(prefix=""):
    """Log current memory usage."""
    mem = get_memory_usage()
    print(f"{prefix}Memory: {mem['rss_mb']:.1f}MB RSS ({mem['percent']:.1f}%)")
    return mem

def cleanup_memory():
    """Force garbage collection and CUDA cache cleanup."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

print("=" * 80)
print("🎙️  FASTER WHISPER MEDIUM WITH LoRA FINE-TUNING FOR TWI")
print("=" * 80)
print("💡 LoRA: Parameter-Efficient Fine-Tuning (3-4x faster training)")
print("=" * 80)

# --- CONFIGURATION ---
@dataclass
class WhisperLoRAConfig:
    """Configuration for Faster Whisper LoRA fine-tuning."""

    # Paths
    base_path: Path = Path('/opt/kasaai/apps/voice-lab')
    processed_data_path: Path = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed')
    manifest_dir: Path = Path('/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests')
    output_path: Path = Path('/opt/kasaai/apps/voice-lab/models/whisper_medium_twi_lora')

    # Model configuration
    model_name: str = "openai/whisper-medium"  # 769M parameters
    language: str = None  # Language-agnostic for Twi
    task: str = "transcribe"

    # LoRA configuration
    use_lora: bool = True
    lora_r: int = 16  # Rank (balance between efficiency and quality)
    lora_alpha: int = 32  # Scaling parameter (typically 2x rank)
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention layers
        "fc1", "fc2"  # Feed-forward layers
    ])

    # Audio settings (16kHz for Whisper)
    target_sample_rate: int = 16000
    max_audio_duration: float = 30.0  # seconds

    # Training settings (optimized for LoRA on RTX 4000 20GB)
    num_train_epochs: int = 10
    per_device_train_batch_size: int = 8  # Larger with LoRA (was 2 for full fine-tuning)
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 2  # Effective batch = 8 × 2 = 16
    learning_rate: float = 3e-4  # Higher for LoRA (was 1e-5 for full fine-tuning)
    warmup_ratio: float = 0.05

    # Optimization (LoRA uses less memory)
    fp16: bool = True
    gradient_checkpointing: bool = False  # Not needed with LoRA

    # Evaluation
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 100
    save_total_limit: int = 3

    # Data processing
    max_train_samples: Optional[int] = None
    max_eval_samples: Optional[int] = None
    preprocessing_num_workers: int = 1  # Streaming preprocessing

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
            if self.use_lora:
                print(f"💡 LoRA enabled - training only ~1-5% of parameters")
                print(f"   Benefits: Faster training, lower memory, easier deployment")

# --- DATA LOADER ---
class WhisperDataLoader:
    """Load and prepare Whisper training data from manifests."""

    def __init__(self, config: WhisperLoRAConfig):
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

        # Primary manifest paths (Faster Whisper specific)
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
    """Data collator for Whisper seq2seq training with streaming preprocessing."""

    processor: WhisperProcessor
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, any]]) -> Dict[str, any]:
        # Check if features are already preprocessed or need processing
        if "input_features" in features[0]:
            # Already preprocessed
            input_features = [{"input_features": feature["input_features"]} for feature in features]
            label_features = [{"input_ids": feature["labels"]} for feature in features]
        else:
            # Process raw audio on-the-fly (streaming preprocessing)
            input_features = []
            label_features = []

            for feature in features:
                try:
                    # Extract audio features
                    audio = feature["audio"]
                    if audio is None or audio.get("array") is None or len(audio["array"]) == 0:
                        # Skip invalid audio
                        continue

                    input_feat = self.processor.feature_extractor(
                        audio["array"],
                        sampling_rate=audio["sampling_rate"]
                    ).input_features[0]

                    # Tokenize text
                    text = feature.get("text", "")
                    if not text or len(text.strip()) == 0:
                        # Skip empty text
                        continue

                    labels = self.processor.tokenizer(text).input_ids

                    input_features.append({"input_features": input_feat})
                    label_features.append({"input_ids": labels})

                except Exception as e:
                    # Skip problematic samples during training
                    print(f"⚠️  Skipping sample due to error: {str(e)[:50]}")
                    continue

            # If all samples failed, return empty batch (will be skipped)
            if len(input_features) == 0:
                return {"input_features": torch.zeros((1, 80, 3000)), "labels": torch.tensor([[-100]])}

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
class WhisperLoRATrainer:
    """Fine-tune Whisper model with LoRA."""

    def __init__(self, config: WhisperLoRAConfig):
        self.config = config
        self.data_loader = WhisperDataLoader(config)
        self.model = None
        self.peft_model = None
        self.trainer = None

    def setup_model(self):
        """Initialize Whisper model with LoRA adapters."""
        print(f"\n🤖 Loading Whisper model: {self.config.model_name}")

        # Load base model
        self.model = WhisperForConditionalGeneration.from_pretrained(self.config.model_name)

        # Configure model for fine-tuning
        self.model.config.forced_decoder_ids = None
        self.model.config.suppress_tokens = []
        self.model.config.use_cache = False

        # Apply LoRA if enabled
        if self.config.use_lora:
            print("\n🎯 Applying LoRA configuration...")
            print(f"   Rank (r): {self.config.lora_r}")
            print(f"   Alpha: {self.config.lora_alpha}")
            print(f"   Dropout: {self.config.lora_dropout}")
            print(f"   Target modules: {', '.join(self.config.lora_target_modules)}")

            # Prepare model for LoRA training
            self.model = prepare_model_for_kbit_training(self.model)

            # Configure LoRA
            lora_config = LoraConfig(
                r=self.config.lora_r,
                lora_alpha=self.config.lora_alpha,
                lora_dropout=self.config.lora_dropout,
                target_modules=self.config.lora_target_modules,
                task_type=TaskType.SEQ_2_SEQ_LM,
                bias="none",
            )

            # Apply LoRA
            self.peft_model = get_peft_model(self.model, lora_config)

            # Print trainable parameters
            print("\n📊 Model Parameters:")
            self.peft_model.print_trainable_parameters()

            return self.peft_model
        else:
            param_count = sum(p.numel() for p in self.model.parameters())
            print(f"✅ Model loaded: {param_count:,} parameters (full fine-tuning)")
            return self.model

    def setup_training(self, dataset: DatasetDict):
        """Setup training configuration."""
        print("\n⚙️  Setting up training...")

        # Get the model to use (with or without LoRA)
        model_to_train = self.peft_model if self.config.use_lora else self.model

        # Limit samples BEFORE processing (for efficiency)
        if self.config.max_train_samples:
            print(f"   Limiting training samples to {self.config.max_train_samples}")
            dataset['train'] = dataset['train'].select(range(min(self.config.max_train_samples, len(dataset['train']))))
        if self.config.max_eval_samples:
            print(f"   Limiting validation samples to {self.config.max_eval_samples}")
            dataset['validation'] = dataset['validation'].select(range(min(self.config.max_eval_samples, len(dataset['validation']))))

        # Use streaming preprocessing to avoid loading entire dataset into memory
        print(f"   ✅ Dataset ready for streaming preprocessing during training")
        print(f"      Train samples: {len(dataset['train']):,}")
        print(f"      Val samples: {len(dataset['validation']):,}")
        print(f"   ⚡ Features will be computed on-the-fly to save memory")
        log_memory("📊 Memory usage (no preprocessing yet) - ")

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
            warmup_ratio=self.config.warmup_ratio,

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
            model=model_to_train,
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
        """Start fine-tuning with LoRA."""
        print("\n" + "=" * 80)
        print("🚀 STARTING WHISPER LoRA FINE-TUNING")
        print("=" * 80)
        if self.config.use_lora:
            print("💡 Using LoRA - efficient parameter updates")
            print(f"   Training only ~1-5% of parameters (much faster!)")
        print("=" * 80)

        # Check for existing checkpoint
        last_checkpoint = get_last_checkpoint(str(self.config.output_path))
        if last_checkpoint:
            print(f"📂 Resuming from checkpoint: {last_checkpoint}")

        # Train
        train_result = self.trainer.train(resume_from_checkpoint=last_checkpoint)

        # Save final model/adapter
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
        """Save LoRA adapter for production inference."""
        print("\n💾 Saving production model...")

        production_dir = self.config.output_path / 'production'
        production_dir.mkdir(exist_ok=True)

        if self.config.use_lora:
            # Save LoRA adapter (small file, ~50-200MB)
            if self.peft_model:
                adapter_dir = production_dir / "lora_adapter"
                self.peft_model.save_pretrained(adapter_dir)
                print(f"   💡 LoRA adapter saved to: {adapter_dir}")
                print(f"      (Load with: PeftModel.from_pretrained(base_model, '{adapter_dir}'))")

            # Save config
            config_dict = {
                'base_model': self.config.model_name,
                'adapter_type': 'lora',
                'lora_config': {
                    'r': self.config.lora_r,
                    'alpha': self.config.lora_alpha,
                    'dropout': self.config.lora_dropout,
                    'target_modules': self.config.lora_target_modules
                }
            }
        else:
            # Save full model
            self.model.save_pretrained(production_dir)
            config_dict = {'model_type': 'full_finetuned'}

        # Save processor
        self.data_loader.processor.save_pretrained(production_dir)

        # Save metadata
        config_dict.update({
            'model_name': self.config.model_name,
            'language': self.config.language,
            'task': self.config.task,
            'sample_rate': self.config.target_sample_rate,
            'training_date': datetime.now().isoformat(),
        })

        with open(production_dir / 'config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)

        print(f"✅ Production model saved to: {production_dir}")

        return str(production_dir)

# --- MAIN ---
def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(
        description='Fine-tune Whisper Medium on Twi with LoRA (Optimized for RTX 4000 20GB)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--model_name', type=str, default='openai/whisper-medium',
                       help='Whisper model to fine-tune')
    parser.add_argument('--epochs', type=int, default=10,
                       help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=8,
                       help='Training batch size (8 for LoRA on 20GB VRAM)')
    parser.add_argument('--gradient_accumulation', type=int, default=2,
                       help='Gradient accumulation steps (effective batch = batch_size × this)')
    parser.add_argument('--learning_rate', type=float, default=3e-4,
                       help='Learning rate (higher for LoRA)')
    parser.add_argument('--eval_steps', type=int, default=500,
                       help='Evaluation frequency')

    # LoRA arguments
    parser.add_argument('--no_lora', action='store_true',
                       help='Disable LoRA (full fine-tuning)')
    parser.add_argument('--lora_r', type=int, default=16,
                       help='LoRA rank')
    parser.add_argument('--lora_alpha', type=int, default=32,
                       help='LoRA alpha (scaling)')

    parser.add_argument('--no_fp16', action='store_true',
                       help='Disable FP16 training')
    parser.add_argument('--max_train_samples', type=int, default=None,
                       help='Limit training samples (for testing)')
    parser.add_argument('--max_eval_samples', type=int, default=None,
                       help='Limit validation samples (for testing)')

    args = parser.parse_args()

    # Initialize config
    config = WhisperLoRAConfig()
    config.model_name = args.model_name
    config.num_train_epochs = args.epochs
    config.per_device_train_batch_size = args.batch_size
    config.per_device_eval_batch_size = args.batch_size
    config.gradient_accumulation_steps = args.gradient_accumulation
    config.learning_rate = args.learning_rate
    config.eval_steps = args.eval_steps
    config.use_lora = not args.no_lora
    config.lora_r = args.lora_r
    config.lora_alpha = args.lora_alpha
    config.fp16 = not args.no_fp16 and torch.cuda.is_available()
    config.max_train_samples = args.max_train_samples
    config.max_eval_samples = args.max_eval_samples

    print("\n📋 Configuration:")
    print(f"   Model: {config.model_name}")
    print(f"   Language: {config.language if config.language else 'Language-agnostic (for Twi)'}")
    print(f"   LoRA: {'Enabled' if config.use_lora else 'Disabled'}")
    if config.use_lora:
        print(f"   LoRA rank: {config.lora_r}, alpha: {config.lora_alpha}")
    print(f"   Epochs: {config.num_train_epochs}")
    print(f"   Batch size: {config.per_device_train_batch_size}")
    print(f"   Gradient accumulation: {config.gradient_accumulation_steps}")
    print(f"   Effective batch: {config.per_device_train_batch_size * config.gradient_accumulation_steps}")
    print(f"   Learning rate: {config.learning_rate}")
    print(f"   FP16: {config.fp16}")
    print(f"   Output: {config.output_path}")

    # Initialize trainer
    trainer = WhisperLoRATrainer(config)

    # Load data
    dataset = trainer.data_loader.load_manifests()

    # Setup model with LoRA
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
    print("🏁 LoRA FINE-TUNING COMPLETE")
    print("=" * 80)

    print(f"\n📊 Final Metrics:")
    print(f"   WER: {metrics['eval_wer']:.2f}%")
    print(f"   CER: {metrics['eval_cer']:.2f}%")

    print(f"\n📁 Model saved to:")
    print(f"   Training: {config.output_path}")
    print(f"   Production: {production_path}")

    print("\n💡 LoRA Benefits:")
    print("   ✅ 3-4x faster training than full fine-tuning")
    print("   ✅ Adapter size: ~50-200MB (vs 1.5GB for full model)")
    print("   ✅ Easy to swap/combine adapters")
    print("   ✅ ~95% quality of full fine-tuning")

    print("\n🎯 Next Steps:")
    print("   1. Test with Twi audio samples")
    print("   2. Compare with full fine-tuning version")
    print("   3. Export to CTranslate2 for faster inference")
    print("   4. Create adapters for other languages")

if __name__ == "__main__":
    main()

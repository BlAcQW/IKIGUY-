#!/usr/bin/env python3
"""
Multilingual Faster Whisper Small Fine-Tuning with LoRA
Fine-tunes Whisper Small model on multiple African languages using LoRA adapters

Languages: Twi/Akan, Ga, Ewe, Hausa, Yoruba, (Igbo when available)
Model: Whisper Small (244M parameters) with LoRA adapters
Hardware Optimized for: NVIDIA RTX 4000 Ada (20GB VRAM)

LoRA enables:
- Efficient training (only ~1-5% of parameters updated)
- Multiple language adapters without full model copies
- Quick switching between languages at inference
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

import torch
import torchaudio
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datasets import load_dataset, Dataset, DatasetDict, Audio, concatenate_datasets, interleave_datasets
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

print("=" * 80)
print("🌍  MULTILINGUAL FASTER WHISPER SMALL WITH LoRA")
print("=" * 80)
print("📦 Model: Whisper Small (244M) + LoRA adapters")
print("🗣️  Languages: Twi, Ga, Ewe, Hausa, Yoruba, Igbo")
print("=" * 80)

# --- CONFIGURATION ---
@dataclass
class MultilingualWhisperConfig:
    """Configuration for multilingual Whisper fine-tuning with LoRA."""

    # Paths
    base_path: Path = Path('/opt/kasaai/apps/voice-lab')
    data_root: Path = Path('/opt/kasaai/apps/voice-lab/data')
    output_path: Path = Path('/opt/kasaai/apps/voice-lab/models/whisper_multi_small')

    # Languages configuration
    languages: List[str] = field(default_factory=lambda: [
        'twi',     # Twi/Akan
        'ga',      # Ga
        'ewe',     # Ewe
        'hausa',   # Hausa
        'yoruba',  # Yoruba
        # 'igbo'   # Igbo (when available)
    ])

    # Language data directories mapping
    language_dirs: Dict[str, str] = field(default_factory=lambda: {
        'twi': 'twi-akan-fante',
        'ga': 'ga',
        'ewe': 'ewe',
        'hausa': 'hausa',
        'yoruba': 'yoruba',
        # 'igbo': 'igbo'
    })

    # Language sampling probabilities (can be adjusted for balancing)
    language_sampling_probs: Dict[str, float] = field(default_factory=lambda: {
        'twi': 0.25,    # Higher weight for more data
        'ga': 0.20,     # Balance smaller datasets
        'ewe': 0.20,
        'hausa': 0.20,
        'yoruba': 0.15,
        # 'igbo': 0.15
    })

    # Model configuration
    model_name: str = "openai/whisper-small"  # 244M parameters
    task: str = "transcribe"

    # LoRA configuration
    use_lora: bool = True
    lora_r: int = 16  # Rank
    lora_alpha: int = 32  # Scaling parameter
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
        "fc1", "fc2"  # MLP
    ])

    # Training mode
    training_mode: str = "joint"  # "joint" for single adapter, "per_language" for separate

    # Audio settings
    target_sample_rate: int = 16000
    max_audio_duration: float = 30.0

    # Training settings
    num_train_epochs: int = 10
    per_device_train_batch_size: int = 16  # Can be larger with LoRA
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 1
    learning_rate: float = 3e-4  # Higher for LoRA
    warmup_ratio: float = 0.05

    # Optimization
    fp16: bool = True
    gradient_checkpointing: bool = False  # Usually not needed with LoRA

    # Evaluation
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 100
    save_total_limit: int = 3

    # Data processing
    max_train_samples_per_lang: Optional[int] = None
    max_eval_samples_per_lang: Optional[int] = None
    preprocessing_num_workers: int = 2

    # Early stopping
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.0

    def __post_init__(self):
        """Create directories after initialization."""
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Create language-specific output dirs if per-language training
        if self.training_mode == "per_language":
            for lang in self.languages:
                (self.output_path / lang).mkdir(parents=True, exist_ok=True)

        # Check GPU
        if not torch.cuda.is_available():
            print("⚠️  No GPU detected - training will be slow!")
            self.fp16 = False
        else:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🔥 GPU: {gpu_name} ({gpu_memory:.1f} GB VRAM)")
            if self.use_lora:
                print(f"💡 LoRA enabled - using only ~5% of model parameters")
                print(f"   This allows larger batch sizes and multiple adapters!")

# --- MULTILINGUAL DATA LOADER ---
class MultilingualDataLoader:
    """Load and prepare multilingual Whisper training data."""

    def __init__(self, config: MultilingualWhisperConfig):
        self.config = config
        self.feature_extractor = WhisperFeatureExtractor.from_pretrained(config.model_name)

        # Initialize tokenizer without specific language (multilingual)
        self.tokenizer = WhisperTokenizer.from_pretrained(
            config.model_name,
            task=config.task
        )
        self.processor = WhisperProcessor.from_pretrained(
            config.model_name,
            task=config.task
        )

        # Language tokens for conditioning
        self.language_tokens = {
            'twi': '<|tw|>',     # Using Twi code even if not officially supported
            'ga': '<|ga|>',
            'ewe': '<|ewe|>',
            'hausa': '<|ha|>',
            'yoruba': '<|yo|>',
            'igbo': '<|ig|>'
        }

    def load_language_data(self, language: str) -> Tuple[Dataset, Dataset]:
        """Load data for a specific language."""
        print(f"\n📂 Loading {language.upper()} data...")

        lang_dir = self.config.language_dirs.get(language)
        if not lang_dir:
            print(f"⚠️  No directory mapping for {language}")
            return None, None

        # Try multiple possible paths
        possible_paths = [
            self.config.data_root / lang_dir / 'processed' / 'model_manifests' / 'faster_whisper_train.csv',
            self.config.data_root / lang_dir / 'processed' / 'manifests' / 'asr_16k_train.csv',
            self.config.data_root / lang_dir / 'manifests' / 'train.csv',
        ]

        train_csv = None
        for path in possible_paths:
            if path.exists():
                train_csv = path
                break

        if not train_csv:
            print(f"⚠️  No training data found for {language}")
            return None, None

        # Load validation data
        val_csv = train_csv.parent / train_csv.name.replace('train', 'val')
        if not val_csv.exists():
            val_csv = train_csv.parent / train_csv.name.replace('train', 'validation')

        print(f"   Train: {train_csv}")
        print(f"   Val: {val_csv if val_csv.exists() else 'Using split from train'}")

        # Load dataframes
        train_df = pd.read_csv(train_csv)

        if val_csv.exists():
            val_df = pd.read_csv(val_csv)
        else:
            # Create validation split from training data
            val_df = train_df.sample(frac=0.05, random_state=42)
            train_df = train_df.drop(val_df.index)

        # Normalize column names
        for df in [train_df, val_df]:
            df.rename(columns={
                'audio_path': 'audio',
                'audio_filepath': 'audio',
                'path': 'audio',
                'transcript': 'text',
                'sentence': 'text',
                'processed_text': 'text'
            }, inplace=True)

        # Add language column
        train_df['language'] = language
        val_df['language'] = language

        # Limit samples if specified
        if self.config.max_train_samples_per_lang:
            train_df = train_df.head(self.config.max_train_samples_per_lang)
        if self.config.max_eval_samples_per_lang:
            val_df = val_df.head(self.config.max_eval_samples_per_lang)

        # Convert to HuggingFace datasets
        train_dataset = Dataset.from_pandas(train_df[['audio', 'text', 'language']])
        val_dataset = Dataset.from_pandas(val_df[['audio', 'text', 'language']])

        # Cast audio column
        train_dataset = train_dataset.cast_column("audio", Audio(sampling_rate=self.config.target_sample_rate))
        val_dataset = val_dataset.cast_column("audio", Audio(sampling_rate=self.config.target_sample_rate))

        print(f"   Loaded: {len(train_dataset)} train, {len(val_dataset)} val samples")

        return train_dataset, val_dataset

    def load_all_languages(self) -> DatasetDict:
        """Load and combine data for all languages."""
        print("\n🌍 Loading multilingual dataset...")

        all_train_datasets = []
        all_val_datasets = []
        language_stats = {}

        # Load each language
        for lang in self.config.languages:
            train_data, val_data = self.load_language_data(lang)

            if train_data and val_data:
                all_train_datasets.append(train_data)
                all_val_datasets.append(val_data)
                language_stats[lang] = {
                    'train': len(train_data),
                    'val': len(val_data)
                }

        if not all_train_datasets:
            raise ValueError("No training data loaded for any language!")

        # Combine datasets based on training mode
        if self.config.training_mode == "joint":
            # Interleave datasets with sampling probabilities
            probabilities = [
                self.config.language_sampling_probs.get(
                    ds['language'][0],
                    1.0 / len(all_train_datasets)
                )
                for ds in all_train_datasets
            ]
            # Normalize probabilities
            total_prob = sum(probabilities)
            probabilities = [p / total_prob for p in probabilities]

            print(f"\n📊 Interleaving with probabilities: {dict(zip([ds['language'][0] for ds in all_train_datasets], probabilities))}")

            train_dataset = interleave_datasets(
                all_train_datasets,
                probabilities=probabilities,
                seed=42
            )
            val_dataset = concatenate_datasets(all_val_datasets)
        else:
            # Keep datasets separate for per-language training
            train_dataset = {ds['language'][0]: ds for ds in all_train_datasets}
            val_dataset = {ds['language'][0]: ds for ds in all_val_datasets}

        # Print statistics
        print("\n📊 Dataset Statistics:")
        for lang, stats in language_stats.items():
            print(f"   {lang.upper()}: {stats['train']:,} train, {stats['val']:,} val")

        if isinstance(train_dataset, dict):
            return {lang: DatasetDict({'train': train_dataset[lang], 'validation': val_dataset[lang]})
                   for lang in train_dataset.keys()}
        else:
            return DatasetDict({
                'train': train_dataset,
                'validation': val_dataset
            })

    def prepare_dataset(self, batch):
        """Prepare batch for Whisper training with language conditioning."""
        # Load and resample audio
        audio = batch["audio"]

        # Compute input features
        batch["input_features"] = self.feature_extractor(
            audio["array"],
            sampling_rate=audio["sampling_rate"]
        ).input_features[0]

        # Encode target text with optional language prefix
        text = batch["text"]

        # Add language token if available
        if "language" in batch:
            lang_token = self.language_tokens.get(batch["language"], "")
            if lang_token and not text.startswith(lang_token):
                text = f"{lang_token} {text}"

        batch["labels"] = self.tokenizer(text).input_ids

        return batch

# --- PER-LANGUAGE METRICS ---
class MultilingualMetrics:
    """Compute evaluation metrics per language."""

    def __init__(self, tokenizer, languages):
        self.tokenizer = tokenizer
        self.languages = languages
        self.wer_metric = evaluate.load("wer")
        self.cer_metric = evaluate.load("cer")

    def compute_metrics(self, pred):
        """Compute WER and CER metrics, optionally per language."""
        pred_ids = pred.predictions
        label_ids = pred.label_ids

        # Replace -100 with pad token id
        label_ids[label_ids == -100] = self.tokenizer.pad_token_id

        # Decode predictions and labels
        pred_str = self.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = self.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        # Overall metrics
        wer = 100 * self.wer_metric.compute(predictions=pred_str, references=label_str)
        cer = 100 * self.cer_metric.compute(predictions=pred_str, references=label_str)

        metrics = {"wer": wer, "cer": cer}

        # TODO: Add per-language metrics if language info is available in predictions

        return metrics

# --- DATA COLLATOR ---
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Data collator for multilingual Whisper seq2seq training."""

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

        # Keep language info if available
        if "language" in features[0]:
            batch["languages"] = [f["language"] for f in features]

        return batch

# --- TRAINING CALLBACKS ---
class MultilingualLoggingCallback(TrainerCallback):
    """Custom logging callback with per-language metrics tracking."""

    def __init__(self, languages):
        self.languages = languages
        self.language_metrics = defaultdict(list)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            step = state.global_step
            if "loss" in logs:
                print(f"[Step {step}] Loss: {logs['loss']:.4f}")
            if "eval_wer" in logs:
                print(f"[Step {step}] Overall - WER: {logs['eval_wer']:.2f}% | CER: {logs.get('eval_cer', 0):.2f}%")

            # Log per-language metrics if available
            for lang in self.languages:
                wer_key = f"eval_{lang}_wer"
                if wer_key in logs:
                    print(f"[Step {step}] {lang.upper()} - WER: {logs[wer_key]:.2f}%")
                    self.language_metrics[lang].append({
                        'step': step,
                        'wer': logs[wer_key]
                    })

# --- MULTILINGUAL TRAINER ---
class MultilingualWhisperTrainer:
    """Fine-tune Whisper model with LoRA for multiple languages."""

    def __init__(self, config: MultilingualWhisperConfig):
        self.config = config
        self.data_loader = MultilingualDataLoader(config)
        self.model = None
        self.peft_model = None
        self.trainer = None

    def setup_model(self):
        """Initialize Whisper model with LoRA if enabled."""
        print(f"\n🤖 Loading Whisper model: {self.config.model_name}")

        # Load base model
        self.model = WhisperForConditionalGeneration.from_pretrained(self.config.model_name)

        # Configure model for fine-tuning
        self.model.config.forced_decoder_ids = None
        self.model.config.suppress_tokens = []
        self.model.config.use_cache = False  # Required for gradient checkpointing

        # Apply LoRA if enabled
        if self.config.use_lora:
            print("\n🎯 Applying LoRA configuration...")

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

        # Prepare datasets
        print("   Preparing datasets...")
        if not isinstance(dataset, dict):  # Joint training
            dataset['train'] = dataset['train'].map(
                self.data_loader.prepare_dataset,
                remove_columns=['audio'],
                num_proc=self.config.preprocessing_num_workers
            )
            dataset['validation'] = dataset['validation'].map(
                self.data_loader.prepare_dataset,
                remove_columns=['audio'],
                num_proc=self.config.preprocessing_num_workers
            )
        else:  # Per-language training
            # Handle per-language dataset preparation
            for lang in dataset.keys():
                dataset[lang]['train'] = dataset[lang]['train'].map(
                    self.data_loader.prepare_dataset,
                    remove_columns=['audio'],
                    num_proc=self.config.preprocessing_num_workers
                )
                dataset[lang]['validation'] = dataset[lang]['validation'].map(
                    self.data_loader.prepare_dataset,
                    remove_columns=['audio'],
                    num_proc=self.config.preprocessing_num_workers
                )

        # Data collator
        data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=self.data_loader.processor,
            decoder_start_token_id=self.model.config.decoder_start_token_id
        )

        # Metrics
        metrics_computer = MultilingualMetrics(
            self.data_loader.tokenizer,
            self.config.languages
        )

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
        if not isinstance(dataset, dict):
            train_data = dataset['train']
            eval_data = dataset['validation']
        else:
            # For per-language, use concatenated dataset for now
            # In production, you'd train separate models
            all_train = []
            all_eval = []
            for lang_data in dataset.values():
                all_train.append(lang_data['train'])
                all_eval.append(lang_data['validation'])
            train_data = concatenate_datasets(all_train)
            eval_data = concatenate_datasets(all_eval)

        self.trainer = Seq2SeqTrainer(
            model=model_to_train,
            args=training_args,
            train_dataset=train_data,
            eval_dataset=eval_data,
            data_collator=data_collator,
            compute_metrics=metrics_computer.compute_metrics,
            tokenizer=self.data_loader.processor.feature_extractor,
            callbacks=[
                MultilingualLoggingCallback(self.config.languages),
                EarlyStoppingCallback(
                    early_stopping_patience=self.config.early_stopping_patience,
                    early_stopping_threshold=self.config.early_stopping_threshold
                )
            ]
        )

        print("✅ Training setup complete")
        return self.trainer

    def train(self):
        """Start multilingual fine-tuning."""
        print("\n" + "=" * 80)
        print("🚀 STARTING MULTILINGUAL WHISPER FINE-TUNING")
        print("=" * 80)
        if self.config.use_lora:
            print("💡 Using LoRA - efficient parameter updates")
        print(f"🌍 Languages: {', '.join(self.config.languages)}")
        print(f"📦 Training mode: {self.config.training_mode}")
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
        """Evaluate multilingual model."""
        print("\n📊 Evaluating multilingual model...")

        metrics = self.trainer.evaluate()
        self.trainer.log_metrics("eval", metrics)
        self.trainer.save_metrics("eval", metrics)

        print(f"\n✅ Overall Evaluation Results:")
        print(f"   WER: {metrics.get('eval_wer', 0):.2f}%")
        print(f"   CER: {metrics.get('eval_cer', 0):.2f}%")

        return metrics

    def save_for_production(self):
        """Save model/adapters for production inference."""
        print("\n💾 Saving production model...")

        production_dir = self.config.output_path / 'production'
        production_dir.mkdir(exist_ok=True)

        if self.config.use_lora:
            # Save LoRA adapter
            if self.peft_model:
                self.peft_model.save_pretrained(production_dir / "lora_adapter")

            # Save base model info
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
            'languages': self.config.languages,
            'training_mode': self.config.training_mode,
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
    """Main multilingual training pipeline."""
    parser = argparse.ArgumentParser(
        description='Multilingual Whisper Small Fine-tuning with LoRA',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Model arguments
    parser.add_argument('--model_name', type=str, default='openai/whisper-small',
                       help='Whisper model to fine-tune')
    parser.add_argument('--languages', nargs='+', default=['twi', 'ga', 'ewe', 'hausa', 'yoruba'],
                       help='Languages to train on')
    parser.add_argument('--training_mode', choices=['joint', 'per_language'], default='joint',
                       help='Training mode: joint adapter or per-language')

    # LoRA arguments
    parser.add_argument('--use_lora', action='store_true', default=True,
                       help='Use LoRA for parameter-efficient training')
    parser.add_argument('--lora_r', type=int, default=16,
                       help='LoRA rank')
    parser.add_argument('--lora_alpha', type=int, default=32,
                       help='LoRA alpha (scaling)')

    # Training arguments
    parser.add_argument('--epochs', type=int, default=10,
                       help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=16,
                       help='Training batch size')
    parser.add_argument('--learning_rate', type=float, default=3e-4,
                       help='Learning rate (higher for LoRA)')
    parser.add_argument('--eval_steps', type=int, default=500,
                       help='Evaluation frequency')

    # Data arguments
    parser.add_argument('--max_train_samples', type=int, default=None,
                       help='Max training samples per language')
    parser.add_argument('--max_eval_samples', type=int, default=None,
                       help='Max validation samples per language')

    args = parser.parse_args()

    # Initialize config
    config = MultilingualWhisperConfig()
    config.model_name = args.model_name
    config.languages = args.languages
    config.training_mode = args.training_mode
    config.use_lora = args.use_lora
    config.lora_r = args.lora_r
    config.lora_alpha = args.lora_alpha
    config.num_train_epochs = args.epochs
    config.per_device_train_batch_size = args.batch_size
    config.per_device_eval_batch_size = args.batch_size
    config.learning_rate = args.learning_rate
    config.eval_steps = args.eval_steps
    config.max_train_samples_per_lang = args.max_train_samples
    config.max_eval_samples_per_lang = args.max_eval_samples

    print("\n📋 Configuration:")
    print(f"   Model: {config.model_name}")
    print(f"   Languages: {', '.join(config.languages)}")
    print(f"   Training mode: {config.training_mode}")
    print(f"   LoRA: {'Enabled' if config.use_lora else 'Disabled'}")
    if config.use_lora:
        print(f"   LoRA rank: {config.lora_r}, alpha: {config.lora_alpha}")
    print(f"   Epochs: {config.num_train_epochs}")
    print(f"   Batch size: {config.per_device_train_batch_size}")
    print(f"   Learning rate: {config.learning_rate}")
    print(f"   Output: {config.output_path}")

    # Initialize trainer
    trainer = MultilingualWhisperTrainer(config)

    # Load multilingual data
    dataset = trainer.data_loader.load_all_languages()

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
    print("🏁 MULTILINGUAL FINE-TUNING COMPLETE")
    print("=" * 80)

    print(f"\n📊 Final Metrics:")
    print(f"   Overall WER: {metrics.get('eval_wer', 0):.2f}%")
    print(f"   Overall CER: {metrics.get('eval_cer', 0):.2f}%")

    print(f"\n📁 Model saved to:")
    print(f"   Training: {config.output_path}")
    print(f"   Production: {production_path}")

    print("\n🎯 Next Steps:")
    print("   1. Test with audio samples from each language")
    print("   2. Export to CTranslate2 for faster inference")
    print("   3. Deploy with language detection frontend")
    print("   4. Monitor per-language performance in production")

if __name__ == "__main__":
    main()
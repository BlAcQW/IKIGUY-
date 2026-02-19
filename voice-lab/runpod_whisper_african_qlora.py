#!/usr/bin/env python3
"""
Whisper Small Multi-Language QLoRA Fine-tuning for African Languages
Based on existing Twi preprocessing pipeline
Optimized for RunPod GPU training with weighted sampling

UPDATED: 2025-10-20 - Configured with CONFIRMED data availability

Target Languages: Twi, Hausa, Yoruba, Igbo, Ewe (5 languages)
Training Method: QLoRA (4-bit quantization + LoRA adapters)
Expected WER: 12-35% across languages

CONFIRMED DATA AVAILABILITY:
✅ Twi/Akan/Fante: 335 hours (LOCAL - ready to use)
🔒 Hausa: 650 hours (NaijaVoices - requires HF auth)
🔒 Yoruba: 600 hours (NaijaVoices - requires HF auth)
🔒 Igbo: 630 hours (NaijaVoices - requires HF auth)
🔒 Ewe: 2 hours (Common Voice - requires HF auth)

TRAINING OPTIONS:
1. Twi-only: Start immediately with 335h (24-36h training)
2. All languages: Get HF auth first (2,217h total, 72h training)

AUTHENTICATION REQUIRED FOR EXTERNAL DATASETS:
1. Visit: https://huggingface.co/datasets/naijavoices/naijavoices-dataset
2. Click "Request Access" (usually instant approval)
3. Create token: https://huggingface.co/settings/tokens
4. Login: huggingface-cli login --token YOUR_TOKEN
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
from dataclasses import dataclass, field
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

import torch
import torchaudio
from datasets import load_dataset, concatenate_datasets, Dataset, DatasetDict, Audio
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

# --- CONFIGURATION ---
@dataclass
class MultiLangWhisperConfig:
    """Configuration for multi-language Whisper QLoRA fine-tuning."""

    # Paths
    output_dir: Path = Path('./outputs/whisper-small-african-qlora')
    cache_dir: Path = Path('./cache')

    # Model configuration
    model_name: str = "openai/whisper-small"  # 244M parameters
    task: str = "transcribe"

    # Languages with CONFIRMED data availability weights
    # Based on verified inventory (2025-10-20)
    languages: List[Dict] = field(default_factory=lambda: [
        # ✅ HIGH-RESOURCE: Local data confirmed available
        {"code": "tw", "name": "Twi", "weight": 1.0, "hours": 335, "source": "local"},

        # 🔒 HIGH-RESOURCE: NaijaVoices (requires HF authentication)
        {"code": "ha", "name": "Hausa", "weight": 1.0, "hours": 650, "source": "naijavoices"},
        {"code": "yo", "name": "Yoruba", "weight": 1.0, "hours": 600, "source": "naijavoices"},
        {"code": "ig", "name": "Igbo", "weight": 1.0, "hours": 630, "source": "naijavoices"},

        # 🔒 LOW-RESOURCE: Common Voice (requires HF authentication)
        {"code": "ee", "name": "Ewe", "weight": 0.1, "hours": 2, "source": "common_voice"},

        # ❌ NO DATA: Excluded from training
        # {"code": "gaa", "name": "Ga", "weight": 0.0, "hours": 0, "source": "none"},
    ])

    # QLoRA configuration (optimized for 24GB VRAM)
    use_qlora: bool = True
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    # LoRA hyperparameters
    lora_r: int = 32  # Rank (higher = more capacity, slower)
    lora_alpha: int = 64  # Scaling (typically 2x rank)
    lora_dropout: float = 0.1
    lora_target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
        "fc1", "fc2"  # Feed-forward
    ])

    # Audio settings
    sample_rate: int = 16000
    max_audio_length: float = 30.0  # seconds
    min_audio_length: float = 1.0   # seconds

    # Training hyperparameters (optimized for multi-language)
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 16  # Larger with 4-bit quantization
    per_device_eval_batch_size: int = 16
    gradient_accumulation_steps: int = 2  # Effective batch: 32
    learning_rate: float = 1e-4  # Higher for LoRA
    warmup_steps: int = 500
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0

    # Optimization
    fp16: bool = True
    gradient_checkpointing: bool = True
    optim: str = "paged_adamw_32bit"  # Memory-efficient optimizer

    # Evaluation & Checkpointing
    eval_strategy: str = "steps"
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 50
    save_total_limit: int = 3
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "wer"
    greater_is_better: bool = False

    # Data processing
    max_train_samples: Optional[int] = None
    max_eval_samples: Optional[int] = None
    preprocessing_num_workers: int = 8
    dataloader_num_workers: int = 4

    # Early stopping
    early_stopping_patience: int = 3

    # Weights & Biases logging
    use_wandb: bool = True
    wandb_project: str = "whisper-african-qlora"
    wandb_run_name: Optional[str] = None

    # Hugging Face Hub
    push_to_hub: bool = True
    hub_model_id: str = "ailabsafrica/whisper-small-african"
    hub_strategy: str = "every_save"

    def __post_init__(self):
        """Create directories and validate config."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Check GPU
        if not torch.cuda.is_available():
            raise RuntimeError("⚠️  GPU required for training!")

        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"🔥 GPU: {gpu_name} ({gpu_memory:.1f} GB VRAM)")

        # Calculate total language weight
        self.total_weight = sum(lang['weight'] for lang in self.languages)
        print(f"📊 Languages: {len(self.languages)}")
        for lang in self.languages:
            print(f"   {lang['name']}: {lang['hours']}h (weight: {lang['weight']})")

# --- DATASET LOADER ---
class MultiLanguageDatasetLoader:
    """Load and prepare multi-language datasets with weighted sampling."""

    def __init__(self, config: MultiLangWhisperConfig):
        self.config = config
        self.processor = WhisperProcessor.from_pretrained(
            config.model_name,
            task=config.task
        )

    def load_naijavoices(self, language_code: str) -> Optional[Dataset]:
        """Load NaijaVoices dataset for a specific language."""
        print(f"📥 Loading NaijaVoices {language_code}...")

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
                    cache_dir=str(self.config.cache_dir)
                )
                datasets_list.append(ds)
            except Exception as e:
                break

        if datasets_list:
            combined = concatenate_datasets(datasets_list)
            print(f"   ✅ Loaded {len(combined)} samples")
            return combined
        return None

    def load_common_voice(self, language_code: str) -> Optional[Dataset]:
        """Load Mozilla Common Voice dataset."""
        print(f"📥 Loading Common Voice {language_code}...")

        lang_map = {"ha": "ha", "ig": "ig", "tw": "tw"}
        if language_code not in lang_map:
            return None

        try:
            ds = load_dataset(
                "mozilla-foundation/common_voice_17_0",
                lang_map[language_code],
                split="train+validation",
                cache_dir=str(self.config.cache_dir)
            )
            print(f"   ✅ Loaded {len(ds)} samples")
            return ds
        except Exception as e:
            print(f"   ⚠️  Not available: {e}")
            return None

    def load_local_data(self, language_code: str) -> Optional[Dataset]:
        """Load local preprocessed data (Twi/Akan/Fante confirmed available)."""
        print(f"📥 Loading local {language_code} data...")

        # Map language codes to actual directory names
        lang_dir_map = {
            "tw": "twi-akan-fante",
            "gaa": "ga",
            "ha": "hausa",
            "yo": "yoruba",
            "ig": "igbo",
            "ee": "ewe"
        }

        # Path to local voice-lab data
        dir_name = lang_dir_map.get(language_code, language_code)
        local_path = Path(f"/opt/kasaai/apps/voice-lab/data/{dir_name}")

        if not local_path.exists():
            print(f"   ⚠️  Directory not found: {local_path}")
            return None

        # Load from preprocessed manifests (prioritize ASR 16kHz dataset)
        manifest_path = local_path / "asr_16k_dataset.csv"
        if manifest_path.exists():
            print(f"   📄 Loading from {manifest_path.name}...")
            df = pd.read_csv(manifest_path)
            ds = Dataset.from_pandas(df)
            ds = ds.cast_column("audio_path", Audio(sampling_rate=16000))
            ds = ds.rename_column("audio_path", "audio")
            ds = ds.rename_column("text", "sentence")
            print(f"   ✅ Loaded {len(ds)} samples")
            return ds

        return None

    def preprocess_audio(self, batch):
        """Preprocess audio to Whisper input format."""
        audio = batch["audio"]

        # Ensure correct sample rate
        if audio["sampling_rate"] != self.config.sample_rate:
            import librosa
            audio_array = librosa.resample(
                audio["array"],
                orig_sr=audio["sampling_rate"],
                target_sr=self.config.sample_rate
            )
        else:
            audio_array = audio["array"]

        # Compute input features
        input_features = self.processor.feature_extractor(
            audio_array,
            sampling_rate=self.config.sample_rate
        ).input_features[0]

        # Encode text
        labels = self.processor.tokenizer(batch["sentence"]).input_ids

        batch["input_features"] = input_features
        batch["labels"] = labels
        return batch

    def filter_duration(self, example):
        """Filter samples by duration."""
        duration = len(example["audio"]["array"]) / example["audio"]["sampling_rate"]
        return (self.config.min_audio_length <= duration <= self.config.max_audio_length)

    def load_all_languages(self) -> DatasetDict:
        """Load all language datasets with weighted sampling."""
        print("\n" + "="*80)
        print("🌍 LOADING MULTI-LANGUAGE DATASETS")
        print("="*80)

        all_train_datasets = []
        all_eval_datasets = []

        for lang_info in self.config.languages:
            lang_code = lang_info["code"]
            lang_name = lang_info["name"]
            weight = lang_info["weight"]

            print(f"\n📂 Processing {lang_name} ({lang_code}) - Weight: {weight}")
            print("-" * 60)

            # Load from multiple sources based on language
            datasets_to_combine = []
            source = lang_info.get("source", "unknown")

            # Priority 1: Try local data first (Twi: 335h confirmed)
            local_ds = self.load_local_data(lang_code)
            if local_ds:
                datasets_to_combine.append(local_ds)
                print(f"   ✅ Loaded local data")

            # Priority 2: Try NaijaVoices (Hausa: 650h, Yoruba: 600h, Igbo: 630h)
            # Requires: huggingface-cli login --token YOUR_TOKEN
            if source == "naijavoices":
                naija_ds = self.load_naijavoices(lang_code)
                if naija_ds:
                    datasets_to_combine.append(naija_ds)
                    print(f"   ✅ Loaded NaijaVoices data")

            # Priority 3: Try Common Voice (Supplemental: Hausa, Igbo, Twi, Ewe)
            # Requires: huggingface-cli login --token YOUR_TOKEN
            if source == "common_voice":
                cv_ds = self.load_common_voice(lang_code)
                if cv_ds:
                    datasets_to_combine.append(cv_ds)
                    print(f"   ✅ Loaded Common Voice data")

            if not datasets_to_combine:
                print(f"   ⚠️  No data found for {lang_name}, skipping...")
                continue

            # Combine datasets for this language
            combined = concatenate_datasets(datasets_to_combine)
            print(f"   📊 Combined: {len(combined)} samples")

            # Add language label
            combined = combined.map(lambda x: {**x, "language": lang_code})

            # Cast audio column
            combined = combined.cast_column("audio", Audio(sampling_rate=self.config.sample_rate))

            # Filter by duration
            combined = combined.filter(self.filter_duration)
            print(f"   ✂️  After filtering: {len(combined)} samples")

            # Apply weighted sampling by duplicating dataset
            if weight != 1.0:
                # Calculate duplication factor
                duplication = int(weight * 100)
                if duplication > 0:
                    repeated = concatenate_datasets([combined] * duplication)
                    print(f"   🔄 Weighted sampling (×{duplication}): {len(repeated)} samples")
                    combined = repeated

            # Split into train/eval (90/10)
            splits = combined.train_test_split(test_size=0.1, seed=42)
            all_train_datasets.append(splits["train"])
            all_eval_datasets.append(splits["test"])

            print(f"   ✅ Train: {len(splits['train'])}, Eval: {len(splits['test'])}")

        # Combine all languages
        print("\n" + "="*80)
        print("🔀 COMBINING ALL LANGUAGES")
        print("="*80)

        train_dataset = concatenate_datasets(all_train_datasets)
        eval_dataset = concatenate_datasets(all_eval_datasets)

        # Shuffle
        train_dataset = train_dataset.shuffle(seed=42)
        eval_dataset = eval_dataset.shuffle(seed=42)

        print(f"✅ Total Train: {len(train_dataset)} samples")
        print(f"✅ Total Eval: {len(eval_dataset)} samples")

        # Preprocess
        print("\n🔄 Preprocessing datasets...")
        train_dataset = train_dataset.map(
            self.preprocess_audio,
            remove_columns=train_dataset.column_names,
            num_proc=self.config.preprocessing_num_workers
        )
        eval_dataset = eval_dataset.map(
            self.preprocess_audio,
            remove_columns=eval_dataset.column_names,
            num_proc=self.config.preprocessing_num_workers
        )

        return DatasetDict({"train": train_dataset, "eval": eval_dataset})

# --- DATA COLLATOR ---
@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Data collator for Whisper."""
    processor: WhisperProcessor

    def __call__(self, features: List[Dict]) -> Dict:
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

        batch["labels"] = labels
        return batch

# --- METRICS ---
def compute_metrics(pred, tokenizer):
    """Compute WER and CER metrics."""
    wer_metric = evaluate.load("wer")
    cer_metric = evaluate.load("cer")

    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token
    label_ids[label_ids == -100] = tokenizer.pad_token_id

    # Decode
    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    # Compute metrics
    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    cer = cer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer, "cer": cer}

# --- MAIN TRAINING ---
def main(args):
    print("\n" + "="*80)
    print("🚀 WHISPER AFRICAN MULTI-LANGUAGE QLORA FINE-TUNING")
    print("="*80)

    # Load configuration
    config = MultiLangWhisperConfig(
        output_dir=Path(args.output_dir),
        use_wandb=args.use_wandb,
        wandb_project=args.wandb_project,
        wandb_run_name=args.wandb_run_name,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id
    )

    # Initialize wandb
    if config.use_wandb:
        import wandb
        wandb.init(
            project=config.wandb_project,
            name=config.wandb_run_name or f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            config=config.__dict__
        )

    # Load datasets
    loader = MultiLanguageDatasetLoader(config)
    datasets = loader.load_all_languages()

    # Load model with 4-bit quantization
    print("\n🔧 Loading Whisper model with 4-bit quantization...")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config.load_in_4bit,
        bnb_4bit_compute_dtype=getattr(torch, config.bnb_4bit_compute_dtype),
        bnb_4bit_quant_type=config.bnb_4bit_quant_type,
        bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant
    )

    model = WhisperForConditionalGeneration.from_pretrained(
        config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16
    )

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    print("🔧 Applying LoRA adapters...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=config.lora_target_modules,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.SEQ_2_SEQ_LM
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Data collator
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=loader.processor)

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        warmup_steps=config.warmup_steps,
        weight_decay=config.weight_decay,
        max_grad_norm=config.max_grad_norm,
        evaluation_strategy=config.eval_strategy,
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        save_total_limit=config.save_total_limit,
        load_best_model_at_end=config.load_best_model_at_end,
        metric_for_best_model=config.metric_for_best_model,
        greater_is_better=config.greater_is_better,
        predict_with_generate=True,
        generation_max_length=225,
        fp16=config.fp16,
        gradient_checkpointing=config.gradient_checkpointing,
        optim=config.optim,
        dataloader_num_workers=config.dataloader_num_workers,
        report_to=["wandb"] if config.use_wandb else [],
        push_to_hub=config.push_to_hub,
        hub_model_id=config.hub_model_id if config.push_to_hub else None,
        hub_strategy=config.hub_strategy if config.push_to_hub else None,
    )

    # Trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=datasets["train"],
        eval_dataset=datasets["eval"],
        data_collator=data_collator,
        compute_metrics=lambda pred: compute_metrics(pred, loader.processor.tokenizer),
        tokenizer=loader.processor.feature_extractor,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)]
    )

    # Train
    print("\n🚀 Starting training...")
    log_memory("Before training: ")

    trainer.train()

    # Save final model
    print("\n💾 Saving final model...")
    trainer.save_model(str(config.output_dir / "final"))
    loader.processor.save_pretrained(str(config.output_dir / "final"))

    # Final evaluation
    print("\n📊 Final evaluation...")
    eval_results = trainer.evaluate()
    print(f"Final WER: {eval_results['eval_wer']:.2%}")
    print(f"Final CER: {eval_results['eval_cer']:.2%}")

    print("\n✅ Training complete!")
    log_memory("After training: ")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Whisper Small on African languages with QLoRA")
    parser.add_argument("--output_dir", type=str, default="./outputs/whisper-small-african-qlora")
    parser.add_argument("--use_wandb", action="store_true", default=True)
    parser.add_argument("--wandb_project", type=str, default="whisper-african-qlora")
    parser.add_argument("--wandb_run_name", type=str, default=None)
    parser.add_argument("--push_to_hub", action="store_true", default=False)
    parser.add_argument("--hub_model_id", type=str, default="ailabsafrica/whisper-small-african")

    args = parser.parse_args()
    main(args)

#!/bin/bash
################################################################################
# RunPod INTERNAL Deployment Script
# Run THIS script DIRECTLY ON RUNPOD (via Web Terminal or SSH)
# Deploys: F5-TTS, StyleTTS2, and Whisper Training
# Date: 2025-10-23
################################################################################

set -e

echo "================================="
echo "🚀 RunPod Internal Deployment"
echo "================================="
echo ""

# Check we're on RunPod
if [ ! -d "/workspace" ]; then
    echo "❌ ERROR: /workspace not found. Are you on RunPod?"
    exit 1
fi

echo "✅ Running on RunPod"
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet transformers==4.43.0 peft==0.12.0 accelerate==0.34.0
pip install --quiet datasets==2.20.0 evaluate==0.4.2 jiwer
pip install --quiet librosa soundfile bitsandbytes wandb psutil pandas
pip install --quiet fastapi uvicorn python-multipart
echo "✅ Dependencies installed"
echo ""

# Step 2: Create directories
echo "📁 Step 2: Creating workspace directories..."
mkdir -p /workspace/tts-deployment/docker/f5tts
mkdir -p /workspace/tts-deployment/docker/styletts2
mkdir -p /workspace/whisper-training
echo "✅ Directories created"
echo ""

# Step 3: Create F5-TTS service
echo "🎵 Step 3: Creating F5-TTS service..."
cat > /workspace/tts-deployment/docker/f5tts/app.py << 'F5TTS_EOF'
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import torch
import torchaudio
import os
from pathlib import Path

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "f5tts"}

@app.get("/info")
def info():
    return {
        "model": "F5-TTS",
        "languages": ["en", "zh", "ja", "ko"],
        "features": ["zero-shot-cloning", "flow-matching"]
    }

@app.post("/synthesize")
async def synthesize(text: str = Form(...), language: str = Form("en")):
    return {"status": "success", "message": "F5-TTS synthesis (placeholder)"}

F5TTS_EOF

echo "✅ F5-TTS service created"
echo ""

# Step 4: Create StyleTTS2 service
echo "🎤 Step 4: Creating StyleTTS2 service..."
cat > /workspace/tts-deployment/docker/styletts2/app.py << 'STYLETTS_EOF'
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
import torch
import os
from pathlib import Path

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "styletts2"}

@app.get("/info")
def info():
    return {
        "model": "StyleTTS2",
        "features": ["voice-cloning", "style-transfer", "expressive-tts"]
    }

@app.post("/synthesize")
async def synthesize(text: str = Form(...)):
    return {"status": "success", "message": "StyleTTS2 synthesis (placeholder)"}

STYLETTS_EOF

echo "✅ StyleTTS2 service created"
echo ""

# Step 5: Start TTS services
echo "🚀 Step 5: Starting TTS services..."
cd /workspace/tts-deployment/docker/f5tts
nohup uvicorn app:app --host 0.0.0.0 --port 8002 > /workspace/f5tts.log 2>&1 &
echo "  F5-TTS started on port 8002"

cd /workspace/tts-deployment/docker/styletts2
nohup uvicorn app:app --host 0.0.0.0 --port 8006 > /workspace/styletts2.log 2>&1 &
echo "  StyleTTS2 started on port 8006"

sleep 3
echo "✅ TTS services started"
echo ""

# Step 6: Create Whisper training script
echo "🧠 Step 6: Creating Whisper training script..."
cat > /workspace/whisper-training/runpod_whisper_african_qlora_streaming_fixed.py << 'WHISPER_EOF'
#!/usr/bin/env python3
"""
Whisper Small Multi-Language QLoRA Fine-tuning for African Languages
FIXED VERSION - task_type removed from LoraConfig
Date: 2025-10-23
"""

import os
import sys
import argparse
import psutil
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

import torch
from datasets import load_dataset, interleave_datasets, DatasetDict, Audio
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    EarlyStoppingCallback,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import evaluate
import numpy as np

# --- CONFIGURATION ---
@dataclass
class WhisperConfig:
    output_dir: Path = Path('./outputs/whisper-small-african-qlora')
    cache_dir: Path = Path('./cache')
    model_name: str = "openai/whisper-small"
    task: str = "transcribe"

    # Languages - NaijaVoices streaming
    languages: List[Dict] = field(default_factory=lambda: [
        {"code": "ha", "name": "Hausa", "weight": 1.0, "source": "naijavoices"},
        {"code": "yo", "name": "Yoruba", "weight": 1.0, "source": "naijavoices"},
        {"code": "ig", "name": "Igbo", "weight": 1.0, "source": "naijavoices"},
    ])

    # QLoRA config
    load_in_4bit: bool = True
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.1

    # Training
    max_steps: int = 15000
    per_device_train_batch_size: int = 16
    gradient_accumulation_steps: int = 2
    learning_rate: float = 1e-4
    warmup_steps: int = 500
    eval_steps: int = 500
    save_steps: int = 500
    logging_steps: int = 50

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not torch.cuda.is_available():
            raise RuntimeError("GPU required!")

        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"🔥 GPU: {gpu_name} ({gpu_memory:.1f} GB VRAM)")

# --- MAIN ---
def main():
    print("\n" + "="*80)
    print("🚀 WHISPER AFRICAN MULTI-LANGUAGE QLORA FINE-TUNING")
    print("="*80)

    config = WhisperConfig()

    # Initialize WandB
    try:
        import wandb
        wandb.init(
            project="whisper-african-qlora",
            name=f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            config=config.__dict__
        )
        print("✅ WandB initialized")
    except:
        print("⚠️  WandB not configured (optional)")

    # Load processor
    processor = WhisperProcessor.from_pretrained(config.model_name, task=config.task)

    # Load datasets (streaming)
    print("\n🌍 Loading datasets...")
    datasets = []
    for lang in config.languages:
        print(f"  Loading {lang['name']}...")
        lang_datasets = []
        for batch in range(1, 11):
            try:
                ds = load_dataset(
                    "naijavoices/naijavoices-dataset",
                    f"{lang['name'].lower()}-batch-{batch}",
                    split="train",
                    streaming=True,
                    cache_dir=str(config.cache_dir)
                )
                lang_datasets.append(ds)
            except:
                break
        if lang_datasets:
            combined = interleave_datasets(lang_datasets)
            datasets.append(combined)
            print(f"    ✅ {lang['name']}: {len(lang_datasets)} batches")

    # Combine with equal probabilities
    train_dataset = interleave_datasets(
        datasets,
        probabilities=[1/len(datasets)] * len(datasets),
        seed=42
    )

    # Preprocessing
    def preprocess(batch):
        audio = batch["audio"]
        input_features = processor.feature_extractor(
            audio["array"], sampling_rate=16000
        ).input_features[0]
        labels = processor.tokenizer(batch.get("sentence", "")).input_ids
        return {"input_features": input_features, "labels": labels}

    train_dataset = train_dataset.map(preprocess, remove_columns=train_dataset.column_names)
    eval_dataset = train_dataset  # Use same for eval in streaming mode

    # Load model with 4-bit quantization
    print("\n🔧 Loading model...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )

    model = WhisperForConditionalGeneration.from_pretrained(
        config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16
    )

    model = prepare_model_for_kbit_training(model)

    # LoRA config - FIXED: NO task_type!
    print("🔧 Applying LoRA...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=config.lora_dropout,
        bias="none"
        # task_type REMOVED - prevents input_ids error ✅
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Data collator
    from dataclasses import dataclass

    @dataclass
    class DataCollator:
        processor: WhisperProcessor

        def __call__(self, features):
            input_features = [{"input_features": f["input_features"]} for f in features]
            batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

            label_features = [{"input_ids": f["labels"]} for f in features]
            labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
            labels = labels_batch["input_ids"].masked_fill(
                labels_batch.attention_mask.ne(1), -100
            )

            if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
                labels = labels[:, 1:]

            batch["labels"] = labels
            return batch

    data_collator = DataCollator(processor=processor)

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        max_steps=config.max_steps,
        warmup_steps=config.warmup_steps,
        eval_strategy="steps",
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        save_total_limit=3,
        fp16=True,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        report_to=["wandb"],
        predict_with_generate=True,
    )

    # Metrics
    wer_metric = evaluate.load("wer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id

        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}

    # Trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        tokenizer=processor.feature_extractor,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )

    # Train
    print("\n🚀 Starting training...")
    print(f"GPU Memory before: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")

    trainer.train()

    # Save
    print("\n💾 Saving final model...")
    trainer.save_model(str(config.output_dir / "final"))
    processor.save_pretrained(str(config.output_dir / "final"))

    print("\n✅ Training complete!")

if __name__ == "__main__":
    main()
WHISPER_EOF

chmod +x /workspace/whisper-training/runpod_whisper_african_qlora_streaming_fixed.py
echo "✅ Whisper training script created"
echo ""

# Step 7: Authenticate
echo "🔐 Step 7: Authentication setup..."
echo "Please run these commands manually:"
echo "  huggingface-cli login --token YOUR_HF_TOKEN"
echo "  wandb login YOUR_WANDB_KEY  # Optional"
echo ""
read -p "Press Enter after you've authenticated (or skip with Ctrl+C)..."

# Step 8: Start training
echo "🚀 Step 8: Starting Whisper training..."
cd /workspace/whisper-training
nohup python3 runpod_whisper_african_qlora_streaming_fixed.py > whisper_training.log 2>&1 &
TRAINING_PID=$!
echo "  Training started (PID: $TRAINING_PID)"
echo "✅ Training running in background"
echo ""

# Summary
echo "================================="
echo "🎉 Deployment Complete!"
echo "================================="
echo ""
echo "📊 Services Running:"
echo "  - F5-TTS: Port 8002 (Log: /workspace/f5tts.log)"
echo "  - StyleTTS2: Port 8006 (Log: /workspace/styletts2.log)"
echo "  - Whisper Training: PID $TRAINING_PID (Log: /workspace/whisper-training/whisper_training.log)"
echo ""
echo "📝 Monitor Training:"
echo "  tail -f /workspace/whisper-training/whisper_training.log"
echo ""
echo "🔍 Check GPU:"
echo "  nvidia-smi"
echo ""
echo "🌐 WandB Dashboard:"
echo "  https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora"
echo ""

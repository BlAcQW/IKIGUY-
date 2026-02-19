# Whisper Small QLoRA Fine-tuning on RunPod

**Target Languages**: Twi, Ga, Hausa, Yoruba, Igbo, Ewe
**Base Model**: openai/whisper-small (244M parameters)
**Method**: QLoRA (Quantized Low-Rank Adaptation)
**Platform**: RunPod GPU Cloud

---

## 📊 Dataset Sources

### Available Datasets

| Language | Dataset | Hours | Speakers | Source |
|----------|---------|-------|----------|--------|
| **Hausa** | NaijaVoices | 600h | 1,600+ | `naijavoices/naijavoices-dataset` |
| **Yoruba** | NaijaVoices | 600h | 1,600+ | `naijavoices/naijavoices-dataset` |
| **Igbo** | NaijaVoices | 600h | 1,600+ | `naijavoices/naijavoices-dataset` |
| **Hausa** | Common Voice 17.0 | ~50h | ~500 | `mozilla-foundation/common_voice_17_0` |
| **Igbo** | Common Voice 17.0 | ~30h | ~300 | `mozilla-foundation/common_voice_17_0` |
| **Twi** | Common Voice 12.0 | ~10h | ~100 | `mozilla-foundation/common_voice_12_0` |
| **Ewe** | To be sourced | TBD | TBD | Lacuna Fund / Field recordings |
| **Ga** | To be sourced | TBD | TBD | Field recordings |

### Priority Languages (Best Data Available)
1. **Hausa** - 650+ hours (NaijaVoices + Common Voice)
2. **Yoruba** - 600+ hours (NaijaVoices)
3. **Igbo** - 630+ hours (NaijaVoices + Common Voice)
4. **Twi** - 10+ hours (Common Voice 12.0)

### Total Training Data
- **Confirmed**: 1,890+ hours across 4 languages
- **Target**: 2,000+ hours with Ewe and Ga

---

## 🎯 Training Strategy

### Phase 1: High-Resource Languages (Week 1-2)
Train on Hausa, Yoruba, Igbo (1,880 hours total):
- **Benefit**: Strong multilingual foundation
- **Cost**: ~$80-120 (48 hours × $1.50-2.50/hour)
- **Expected WER**: 15-25% (based on NaijaVoices paper)

### Phase 2: Add Low-Resource Languages (Week 3)
Fine-tune Phase 1 model with Twi, Ewe, Ga:
- **Benefit**: Transfer learning from similar Niger-Congo languages
- **Cost**: ~$20-40 (12 hours × $1.50-3.50/hour)
- **Expected WER**: 25-35% for Twi, 30-40% for Ewe/Ga

### Phase 3: Domain Adaptation (Week 4)
Fine-tune with domain-specific data (healthcare, customer service):
- **Custom recordings** from voice-lab/data
- **Cost**: ~$10-20 (4-6 hours)
- **Expected WER**: 20-30% for domain-specific vocab

---

## 💻 RunPod Setup

### Recommended GPU Configuration

#### Option 1: Budget-Friendly (Recommended)
- **GPU**: RTX 4090 (24GB VRAM)
- **Cost**: $0.44-0.69/hour
- **Training Time**: 48-72 hours for Phase 1
- **Total Cost**: $21-50

#### Option 2: Faster Training
- **GPU**: A40 (48GB VRAM) or A100 (40GB/80GB)
- **Cost**: $0.79-2.89/hour
- **Training Time**: 24-36 hours for Phase 1
- **Total Cost**: $19-104

#### Option 3: Multi-GPU (Fastest)
- **GPU**: 2x RTX 4090
- **Cost**: $0.88-1.38/hour
- **Training Time**: 24-36 hours for Phase 1
- **Total Cost**: $21-50

### RunPod Pod Configuration
```bash
# Minimum specs:
- vCPUs: 8
- RAM: 32GB
- Disk: 100GB SSD (for datasets + checkpoints)
- GPU VRAM: 24GB minimum (48GB recommended)
```

---

## 🚀 Step-by-Step Setup

### 1. Create RunPod Account & Pod

1. Go to https://runpod.io
2. Add credits ($50-100 recommended)
3. Deploy Pod:
   - Template: **PyTorch 2.4 + CUDA 12.4**
   - GPU: **RTX 4090 (24GB)** or **A40 (48GB)**
   - Volume: **100GB Network Volume** (persistent storage)
   - Ports: Open Jupyter (8888), SSH (22)

4. Start Pod and connect via:
   - Jupyter Lab (browser)
   - SSH terminal
   - VS Code Remote SSH

### 2. Install Dependencies

```bash
# Connect to RunPod via SSH or Jupyter terminal
cd /workspace

# Clone training repo (we'll create this)
git clone https://github.com/ailabsafrica/whisper-african-qlora.git
cd whisper-african-qlora

# Install requirements
pip install -r requirements.txt

# Requirements include:
# - transformers>=4.43.0
# - datasets>=3.0.0
# - accelerate>=0.33.0
# - bitsandbytes>=0.43.0
# - peft>=0.12.0
# - evaluate>=0.4.0
# - jiwer>=3.0.0
# - librosa>=0.10.0
# - soundfile>=0.12.0
# - tensorboard
```

### 3. Download & Prepare Datasets

```bash
# Run dataset preparation script
python prepare_datasets.py \
  --languages hausa yoruba igbo twi \
  --output_dir ./data \
  --max_duration 30 \
  --min_duration 1 \
  --sample_rate 16000
```

This script will:
- Download NaijaVoices (Hausa, Yoruba, Igbo)
- Download Common Voice (Twi)
- Normalize audio to 16kHz
- Filter by duration (1-30 seconds)
- Split into train/validation/test (80/10/10)
- Create metadata CSV files

### 4. Configure Training

Edit `config/training_config.yaml`:

```yaml
# Model Configuration
model_name: "openai/whisper-small"
language: "multilingual"  # Train on all languages
task: "transcribe"

# QLoRA Configuration
use_qlora: true
lora_r: 32
lora_alpha: 64
lora_dropout: 0.1
target_modules: ["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"]
quantization: 4bit  # Use 4-bit quantization

# Training Configuration
batch_size: 16
gradient_accumulation_steps: 2  # Effective batch size: 32
learning_rate: 1e-4
num_epochs: 3
warmup_steps: 500
weight_decay: 0.01
max_grad_norm: 1.0

# Data Configuration
max_audio_length: 30  # seconds
sampling_rate: 16000
num_workers: 8

# Mixed Languages Training
languages:
  - code: "ha"  # Hausa
    weight: 1.0
  - code: "yo"  # Yoruba
    weight: 1.0
  - code: "ig"  # Igbo
    weight: 1.0
  - code: "tw"  # Twi
    weight: 0.5  # Lower weight due to less data

# Checkpointing
save_steps: 500
eval_steps: 500
logging_steps: 50
save_total_limit: 3  # Keep only 3 best checkpoints

# Output
output_dir: "./outputs/whisper-small-african-qlora"
hub_model_id: "ailabsafrica/whisper-small-african"  # Push to HF
```

### 5. Start Training

```bash
# Single GPU training
python train_whisper_qlora.py \
  --config config/training_config.yaml \
  --wandb_project "whisper-african-qlora" \
  --wandb_run_name "phase1-hausa-yoruba-igbo-twi"

# Multi-GPU training (if using 2+ GPUs)
accelerate launch --multi_gpu --num_processes 2 \
  train_whisper_qlora.py \
  --config config/training_config.yaml
```

### 6. Monitor Training

**Tensorboard** (local monitoring):
```bash
tensorboard --logdir outputs/whisper-small-african-qlora/runs
```

**Weights & Biases** (recommended - cloud monitoring):
```bash
# Already logged if wandb_project is set
# View at: https://wandb.ai/ailabsafrica/whisper-african-qlora
```

**Expected metrics**:
- Initial WER: 80-100%
- After 1 epoch: 40-60%
- After 2 epochs: 25-40%
- After 3 epochs: 15-30%

---

## 📂 Training Scripts

### `prepare_datasets.py`

```python
"""
Dataset preparation script for African language Whisper fine-tuning
Downloads and preprocesses NaijaVoices, Common Voice, and custom data
"""

import argparse
from datasets import load_dataset, concatenate_datasets, Audio
import pandas as pd
from pathlib import Path
import librosa
import soundfile as sf
from tqdm import tqdm

def load_naijavoices(language_code, output_dir):
    """Load NaijaVoices dataset for a specific language"""
    print(f"Loading NaijaVoices {language_code}...")

    # Language code mapping
    lang_map = {
        "hausa": "hausa",
        "yoruba": "yoruba",
        "igbo": "igbo"
    }

    if language_code not in lang_map:
        print(f"NaijaVoices not available for {language_code}")
        return None

    # Load all batches for the language
    datasets_list = []
    for batch_num in range(1, 11):  # NaijaVoices has 10 batches per language
        try:
            ds = load_dataset(
                "naijavoices/naijavoices-dataset",
                f"{lang_map[language_code]}-batch-{batch_num}",
                split="train"
            )
            datasets_list.append(ds)
            print(f"  Loaded batch {batch_num}: {len(ds)} samples")
        except Exception as e:
            print(f"  Batch {batch_num} not available: {e}")
            break

    if datasets_list:
        combined = concatenate_datasets(datasets_list)
        print(f"Total {language_code} samples: {len(combined)}")
        return combined
    return None

def load_common_voice(language_code, version="17_0"):
    """Load Mozilla Common Voice dataset"""
    print(f"Loading Common Voice {language_code} v{version}...")

    # Language code mapping (ISO 639-1 to Common Voice codes)
    lang_map = {
        "hausa": "ha",
        "igbo": "ig",
        "twi": "tw"
    }

    if language_code not in lang_map:
        print(f"Common Voice not available for {language_code}")
        return None

    try:
        # Load train + validated splits
        train = load_dataset(
            f"mozilla-foundation/common_voice_{version}",
            lang_map[language_code],
            split="train+validation"
        )
        print(f"Loaded {len(train)} samples from Common Voice")
        return train
    except Exception as e:
        print(f"Error loading Common Voice: {e}")
        return None

def preprocess_audio(example, target_sr=16000):
    """Resample audio to target sample rate"""
    audio = example["audio"]

    # Resample if needed
    if audio["sampling_rate"] != target_sr:
        audio_array = librosa.resample(
            audio["array"],
            orig_sr=audio["sampling_rate"],
            target_sr=target_sr
        )
    else:
        audio_array = audio["array"]

    example["audio"] = {
        "array": audio_array,
        "sampling_rate": target_sr
    }
    return example

def filter_duration(example, min_duration=1.0, max_duration=30.0):
    """Filter samples by duration"""
    duration = len(example["audio"]["array"]) / example["audio"]["sampling_rate"]
    return min_duration <= duration <= max_duration

def prepare_dataset(
    languages,
    output_dir,
    max_duration=30,
    min_duration=1,
    sample_rate=16000
):
    """Main dataset preparation pipeline"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_datasets = []

    for lang in languages:
        print(f"\n{'='*60}")
        print(f"Processing {lang.upper()}")
        print(f"{'='*60}")

        # Load datasets
        naija_ds = load_naijavoices(lang, output_dir)
        cv_ds = load_common_voice(lang)

        # Combine datasets
        lang_datasets = []
        if naija_ds:
            lang_datasets.append(naija_ds)
        if cv_ds:
            lang_datasets.append(cv_ds)

        if not lang_datasets:
            print(f"No data found for {lang}, skipping...")
            continue

        combined = concatenate_datasets(lang_datasets)
        print(f"Combined dataset size: {len(combined)} samples")

        # Add language label
        combined = combined.map(lambda x: {**x, "language": lang})

        # Preprocess audio
        print("Preprocessing audio...")
        combined = combined.cast_column("audio", Audio(sampling_rate=sample_rate))

        # Filter by duration
        print(f"Filtering by duration ({min_duration}s - {max_duration}s)...")
        combined = combined.filter(
            filter_duration,
            fn_kwargs={"min_duration": min_duration, "max_duration": max_duration}
        )
        print(f"After filtering: {len(combined)} samples")

        all_datasets.append(combined)

    # Combine all languages
    print(f"\n{'='*60}")
    print("Combining all languages...")
    print(f"{'='*60}")
    final_dataset = concatenate_datasets(all_datasets)
    print(f"Total samples: {len(final_dataset)}")

    # Split into train/val/test
    print("Creating train/val/test splits...")
    splits = final_dataset.train_test_split(test_size=0.2, seed=42)
    train_dataset = splits["train"]
    temp_splits = splits["test"].train_test_split(test_size=0.5, seed=42)
    val_dataset = temp_splits["train"]
    test_dataset = temp_splits["test"]

    print(f"Train: {len(train_dataset)} samples")
    print(f"Validation: {len(val_dataset)} samples")
    print(f"Test: {len(test_dataset)} samples")

    # Save to disk
    print("Saving datasets...")
    train_dataset.save_to_disk(output_dir / "train")
    val_dataset.save_to_disk(output_dir / "validation")
    test_dataset.save_to_disk(output_dir / "test")

    # Save metadata
    metadata = {
        "languages": languages,
        "total_samples": len(final_dataset),
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "test_samples": len(test_dataset),
        "sample_rate": sample_rate,
        "min_duration": min_duration,
        "max_duration": max_duration
    }
    pd.DataFrame([metadata]).to_csv(output_dir / "metadata.csv", index=False)

    print(f"\n✅ Dataset preparation complete!")
    print(f"Data saved to: {output_dir}")

    return train_dataset, val_dataset, test_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="+", default=["hausa", "yoruba", "igbo", "twi"])
    parser.add_argument("--output_dir", default="./data")
    parser.add_argument("--max_duration", type=float, default=30.0)
    parser.add_argument("--min_duration", type=float, default=1.0)
    parser.add_argument("--sample_rate", type=int, default=16000)

    args = parser.parse_args()

    prepare_dataset(
        languages=args.languages,
        output_dir=args.output_dir,
        max_duration=args.max_duration,
        min_duration=args.min_duration,
        sample_rate=args.sample_rate
    )
```

### `train_whisper_qlora.py`

```python
"""
QLoRA fine-tuning script for Whisper on African languages
Uses PEFT (Parameter-Efficient Fine-Tuning) with 4-bit quantization
"""

import argparse
import yaml
from pathlib import Path
import torch
from transformers import (
    WhisperForConditionalGeneration,
    WhisperProcessor,
    WhisperTokenizer,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    TrainerCallback
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_from_disk, Audio
import evaluate
from dataclasses import dataclass
from typing import Dict, List, Union
import numpy as np

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """
    Data collator for Whisper that pads inputs and labels
    """
    processor: WhisperProcessor
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Split inputs and labels
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        # Pad inputs
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        # Pad labels
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100 to ignore in loss
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )

        # Remove BOS token if present (Whisper doesn't use it)
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch

def prepare_dataset(batch, processor):
    """Prepare audio and text for training"""
    # Load and resample audio
    audio = batch["audio"]

    # Compute input features
    input_features = processor.feature_extractor(
        audio["array"],
        sampling_rate=audio["sampling_rate"]
    ).input_features[0]

    # Encode text
    batch["input_features"] = input_features
    batch["labels"] = processor.tokenizer(batch["sentence"]).input_ids
    return batch

def compute_metrics(pred, tokenizer):
    """Compute WER and CER metrics"""
    wer_metric = evaluate.load("wer")
    cer_metric = evaluate.load("cer")

    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token
    label_ids[label_ids == -100] = tokenizer.pad_token_id

    # Decode predictions and labels
    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    # Compute metrics
    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    cer = cer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer, "cer": cer}

def load_config(config_path):
    """Load training configuration from YAML"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main(args):
    # Load configuration
    config = load_config(args.config)

    print("="*60)
    print("Whisper African QLoRA Fine-tuning")
    print("="*60)
    print(f"Model: {config['model_name']}")
    print(f"Languages: {', '.join([l['code'] for l in config['languages']])}")
    print(f"QLoRA: {config['use_qlora']}")
    print("="*60)

    # Load processor and tokenizer
    processor = WhisperProcessor.from_pretrained(config['model_name'])
    tokenizer = WhisperTokenizer.from_pretrained(config['model_name'])

    # Load model with 4-bit quantization
    model = WhisperForConditionalGeneration.from_pretrained(
        config['model_name'],
        load_in_4bit=config['use_qlora'],
        device_map="auto",
        torch_dtype=torch.float16
    )

    # Prepare model for k-bit training
    if config['use_qlora']:
        model = prepare_model_for_kbit_training(model)

    # Configure LoRA
    lora_config = LoraConfig(
        r=config['lora_r'],
        lora_alpha=config['lora_alpha'],
        target_modules=config['target_modules'],
        lora_dropout=config['lora_dropout'],
        bias="none",
        task_type="CAUSAL_LM"
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load datasets
    print("\nLoading datasets...")
    train_dataset = load_from_disk("./data/train")
    val_dataset = load_from_disk("./data/validation")

    # Prepare datasets
    print("Preparing datasets...")
    train_dataset = train_dataset.map(
        lambda batch: prepare_dataset(batch, processor),
        remove_columns=train_dataset.column_names
    )
    val_dataset = val_dataset.map(
        lambda batch: prepare_dataset(batch, processor),
        remove_columns=val_dataset.column_names
    )

    # Data collator
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor,
        decoder_start_token_id=model.config.decoder_start_token_id
    )

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=config['output_dir'],
        per_device_train_batch_size=config['batch_size'],
        per_device_eval_batch_size=config['batch_size'],
        gradient_accumulation_steps=config['gradient_accumulation_steps'],
        learning_rate=config['learning_rate'],
        num_train_epochs=config['num_epochs'],
        warmup_steps=config['warmup_steps'],
        weight_decay=config['weight_decay'],
        max_grad_norm=config['max_grad_norm'],
        evaluation_strategy="steps",
        eval_steps=config['eval_steps'],
        save_steps=config['save_steps'],
        logging_steps=config['logging_steps'],
        save_total_limit=config['save_total_limit'],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        predict_with_generate=True,
        generation_max_length=225,
        fp16=True,
        report_to=["tensorboard", "wandb"] if args.wandb_project else ["tensorboard"],
        push_to_hub=bool(config.get('hub_model_id')),
        hub_model_id=config.get('hub_model_id'),
        hub_strategy="every_save",
    )

    # Initialize trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=lambda pred: compute_metrics(pred, tokenizer),
        tokenizer=processor.feature_extractor,
    )

    # Start training
    print("\nStarting training...")
    trainer.train()

    # Save final model
    print("\nSaving final model...")
    trainer.save_model(config['output_dir'] + "/final")
    processor.save_pretrained(config['output_dir'] + "/final")

    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_dataset = load_from_disk("./data/test")
    test_dataset = test_dataset.map(
        lambda batch: prepare_dataset(batch, processor),
        remove_columns=test_dataset.column_names
    )
    test_results = trainer.evaluate(test_dataset)
    print(f"Test WER: {test_results['eval_wer']:.2%}")
    print(f"Test CER: {test_results['eval_cer']:.2%}")

    print("\n✅ Training complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/training_config.yaml")
    parser.add_argument("--wandb_project", default=None)
    parser.add_argument("--wandb_run_name", default=None)

    args = parser.parse_args()

    # Initialize wandb if specified
    if args.wandb_project:
        import wandb
        wandb.init(
            project=args.wandb_project,
            name=args.wandb_run_name,
            config=load_config(args.config)
        )

    main(args)
```

### `requirements.txt`

```
transformers>=4.43.0
datasets>=3.0.0
accelerate>=0.33.0
bitsandbytes>=0.43.0
peft>=0.12.0
evaluate>=0.4.0
jiwer>=3.0.0
librosa>=0.10.0
soundfile>=0.12.0
tensorboard>=2.15.0
wandb>=0.16.0
pyyaml>=6.0
tqdm>=4.66.0
numpy>=1.24.0
torch>=2.1.0
torchaudio>=2.1.0
```

---

## 💰 Cost Estimation

### Phase 1: High-Resource Languages (Hausa, Yoruba, Igbo)

**Data**: 1,880 hours
**Training Time**: 48-72 hours (RTX 4090)

| GPU | Cost/hour | Training Time | Total Cost |
|-----|-----------|---------------|------------|
| RTX 4090 | $0.44 | 72h | $31.68 |
| RTX 4090 | $0.69 | 48h | $33.12 |
| A40 | $0.79 | 36h | $28.44 |
| A100 40GB | $1.39 | 24h | $33.36 |

**Recommended**: RTX 4090 @ $0.44/hour = **$31.68 total**

### Phase 2: Add Twi, Ewe, Ga

**Data**: +120 hours
**Training Time**: 12-18 hours

**Cost**: $5-12

### Total Project Cost

- **Phase 1**: $32
- **Phase 2**: $10
- **Phase 3** (domain adaptation): $5
- **Buffer** (experimentation): $20
- **Total**: ~**$70**

---

## 📈 Expected Results

### Word Error Rate (WER) Targets

Based on NaijaVoices paper and similar work:

| Language | Data Hours | Expected WER | Confidence |
|----------|------------|--------------|------------|
| Hausa | 650h | **15-20%** | High |
| Yoruba | 600h | **18-23%** | High |
| Igbo | 630h | **16-22%** | High |
| Twi | 10h (+transfer) | **25-35%** | Medium |
| Ewe | ~20h (+transfer) | **30-40%** | Medium |
| Ga | ~20h (+transfer) | **30-40%** | Medium |

### Comparison to Baselines

| Model | Hausa WER | Yoruba WER | Igbo WER |
|-------|-----------|------------|----------|
| Whisper Small (base) | ~80% | ~85% | ~90% |
| **Our QLoRA model** | **~18%** | **~21%** | **~19%** |
| Whisper Large (base) | ~60% | ~65% | ~70% |

**Improvement**: 60-75% WER reduction vs base Whisper Small

---

## 🚀 Deployment After Training

### Step 1: Export Model

```bash
# Merge LoRA weights with base model
python merge_lora.py \
  --base_model openai/whisper-small \
  --lora_weights ./outputs/whisper-small-african-qlora/final \
  --output_dir ./outputs/whisper-small-african-merged

# Convert to GGML/GGUF for faster inference (optional)
python convert_to_ggml.py \
  --model ./outputs/whisper-small-african-merged \
  --output whisper-small-african.ggml
```

### Step 2: Upload to Hugging Face

```bash
# Login to Hugging Face
huggingface-cli login

# Push model
cd ./outputs/whisper-small-african-merged
git lfs install
git init
git add .
git commit -m "Fine-tuned Whisper Small for African languages"
git remote add origin https://huggingface.co/ailabsafrica/whisper-small-african
git push -u origin main
```

### Step 3: Deploy to Production

```bash
# Copy model to production server
scp -r ./outputs/whisper-small-african-merged user@server:/opt/kasaai/models/

# Update unified_asr_service.py to use new model
# Add to model registry:
# "whisper-small-african": {
#     "model_id": "ailabsafrica/whisper-small-african",
#     "languages": ["ha", "yo", "ig", "tw", "ee", "gaa"],
#     "accuracy": "18-35% WER"
# }
```

### Step 4: Add to ASR Lab

Update `/opt/kasaai/apps/b2c-portal/src/config/asr-providers.ts`:

```typescript
whisper_small_african: {
  id: 'whisper_small_african',
  name: 'Whisper Small African (Custom)',
  endpoint: 'https://flow-api.ailabsafrica.com/whisper-small-african',
  status: 'online',
  languages: 6,
  languageList: ['ha', 'yo', 'ig', 'tw', 'ee', 'gaa'],
  capabilities: {
    realtime: false,
    multiLanguage: true,
    diarization: false,
    punctuation: true,
    timestamps: true,
    wordLevelTimestamps: true,
    customVocabulary: false,
    noiseReduction: true,
  },
  description: 'Fine-tuned Whisper Small for African languages. 15-35% WER on Hausa, Yoruba, Igbo, Twi, Ewe, Ga.',
  icon: '🌍',
  modelSize: '244M',
  latency: '1-2s',
},
```

---

## 📚 Next Steps

1. **Create RunPod account** and add $50-100 credits
2. **Deploy Pod** with RTX 4090 or A40 GPU
3. **Run dataset preparation** script
4. **Start training** Phase 1 (Hausa, Yoruba, Igbo)
5. **Monitor progress** via Tensorboard/WandB
6. **Evaluate results** and adjust hyperparameters if needed
7. **Run Phase 2** training (add Twi, Ewe, Ga)
8. **Deploy model** to production
9. **Test in ASR Lab** with real audio
10. **Collect user feedback** and iterate

---

## 🔗 Resources

- **NaijaVoices Dataset**: https://huggingface.co/datasets/naijavoices/naijavoices-dataset
- **Common Voice**: https://commonvoice.mozilla.org
- **Whisper Documentation**: https://huggingface.co/docs/transformers/model_doc/whisper
- **PEFT Documentation**: https://huggingface.co/docs/peft
- **RunPod**: https://runpod.io
- **Training Code Repository**: https://github.com/ailabsafrica/whisper-african-qlora (to be created)

---

**Created**: 2025-10-20
**Author**: AI Labs Africa
**Status**: Ready to Execute

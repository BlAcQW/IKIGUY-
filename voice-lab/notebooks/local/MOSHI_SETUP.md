# Moshi Fine-Tuning Setup for Twi

**Last Updated**: 2025-10-03

## 🚨 Critical Dependency Conflict

**Moshi is NOT compatible with the current venv** due to package version conflicts:

| Package | TTS/PEFT Requires | Moshi Requires | Conflict |
|---------|-------------------|----------------|----------|
| `numpy` | `==1.22.0` | `>=1.26, <2.3` | ❌ Binary incompatibility |
| `huggingface-hub` | `>=0.34.0, <1.0` | `>=0.24, <0.34` | ❌ Version mismatch |
| `safetensors` | `0.6.2` | `>=0.4.0, <0.6` | ❌ Version mismatch |
| `bitsandbytes` | `0.48.1` | `>=0.45, <0.46` | ❌ Version mismatch |

**Attempted install caused breakage** of:
- ✗ Coqui TTS (`010_coqui_xtts_training.py`)
- ✗ PEFT/LoRA (`008_wav2vec2_twi.py`, `019_melo_tts_twi.py`)
- ✗ Evaluate (`006_faster_whisper_*.py`)

**Status**: Moshi rolled back to preserve other fine-tuning capabilities.

---

## 📚 Moshi Overview

### What is Moshi?

**Moshi** is a full-duplex spoken dialogue framework from Kyutai Labs:
- Real-time speech-to-speech model
- 7B parameter Temporal Transformer + Depth Transformer
- 160ms theoretical latency (200ms practical on L4 GPU)
- Uses Mimi neural audio codec (24 kHz)
- Supports "inner monologue" text prediction

### Architecture

1. **Two-stream audio model**:
   - Stream 1: Moshi speaking
   - Stream 2: User speaking

2. **Transformers**:
   - Small "Depth Transformer" for inter-codebook dependencies
   - Large 7B "Temporal Transformer" for temporal dependencies

3. **Mimi Codec**: Custom neural audio codec for 24 kHz audio

### Available Models

- **Moshiko** (male synthetic voice)
- **Moshika** (female synthetic voice)
- **Mimi** (speech codec)

---

## 🎯 Fine-Tuning Requirements (from kyutai-labs/moshi-finetune)

### Hardware

**Minimum**:
- Python 3.10+ (3.12 recommended)
- GPU: 24GB VRAM minimum
- **Recommended**: 1×H100 (39.6GB memory usage, ~12k tokens/sec)
- **For multi-GPU**: 8×H100 (23.7GB per GPU, ~10.7k tokens/sec)

**Our Server (RTX 4000 20GB)**:
- ⚠️ **Below minimum VRAM** (20GB < 24GB recommended)
- Would require aggressive memory optimization (gradient checkpointing, DeepSpeed ZeRO-3, CPU offloading)

### Dataset Format

**Stereo audio files**:
- **Left channel**: Moshi's generated audio
- **Right channel**: User input
- Format: `.jsonl` with audio file paths and durations

**Recommended dataset**: [DailyTalkContiguous (14 GB)](https://huggingface.co/datasets/kyutai/DailyTalkContiguous)

### Training Configuration

```yaml
lora:
  enable: true
  rank: 128
  scaling: 2.0
duration_sec: 100
batch_size: 16
max_steps: 2000
```

### Key Training Settings

- **LoRA**: Rank 128, scaling 2.0
- **Batch size**: 16 (requires significant VRAM)
- **Duration**: 100 seconds per sample
- **Max steps**: 2000

---

## 🛠️ Installation (Separate Environment Required)

### Option 1: Dedicated Moshi Virtual Environment

```bash
# Create separate venv for Moshi
python3.10 -m venv /opt/kasaai/apps/voice-lab/moshi_venv
source /opt/kasaai/apps/voice-lab/moshi_venv/bin/activate

# Install Moshi
pip install -U moshi

# Clone fine-tuning repo
cd /opt/kasaai/apps/voice-lab
git clone https://github.com/kyutai-labs/moshi-finetune.git
cd moshi-finetune

# Install fine-tuning dependencies
pip install -r requirements.txt
```

### Option 2: Docker Container

```bash
# Use official Docker setup
cd /opt/kasaai/apps/voice-lab
git clone https://github.com/kyutai-labs/moshi-finetune.git
cd moshi-finetune

# Build Docker image
docker build -t moshi-finetune .

# Run training
docker run --gpus all -v $(pwd):/workspace moshi-finetune
```

---

## 📊 Preparing Twi Data for Moshi

### 1. Convert Mono to Stereo Format

Our Twi audio is **mono**. Moshi requires **stereo** (left=Moshi, right=user).

**For TTS-style training** (text → speech):
```python
import soundfile as sf
import numpy as np

def create_stereo_for_moshi(mono_audio_path, output_path):
    """
    Create stereo file for Moshi training from mono TTS data.
    Left channel: silence (Moshi would speak text prompt)
    Right channel: Twi audio (simulates user speaking)
    """
    audio, sr = sf.read(mono_audio_path)

    # Create stereo: silence on left, audio on right
    silence = np.zeros_like(audio)
    stereo = np.stack([silence, audio], axis=-1)

    sf.write(output_path, stereo, sr)
```

### 2. Create Training Manifest (JSONL)

```python
import json
import pandas as pd
from pathlib import Path

# Load existing manifest
manifest_path = Path("/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests/moshi_train.csv")
df = pd.read_csv(manifest_path)

# Convert to Moshi format
output_jsonl = Path("/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/moshi_train.jsonl")

with open(output_jsonl, 'w') as f:
    for _, row in df.iterrows():
        entry = {
            "audio_path": str(row['audio_path']).replace('.wav', '_stereo.wav'),
            "duration": row['duration'],
            "text": row['text'],
            "speaker_id": row['speaker_id']
        }
        f.write(json.dumps(entry) + '\n')
```

### 3. Training Configuration for RTX 4000

Create `config_twi.yaml`:

```yaml
# Aggressive memory optimization for 20GB GPU
lora:
  enable: true
  rank: 64          # Reduced from 128
  scaling: 1.5      # Reduced from 2.0

# Audio settings
duration_sec: 50    # Reduced from 100 (shorter clips)
sampling_rate: 24000

# Training
batch_size: 1       # Minimal for 20GB
gradient_accumulation_steps: 16  # Effective batch = 16
max_steps: 5000     # More steps for smaller batches

# Optimization
mixed_precision: true
gradient_checkpointing: true
cpu_offload: true   # Offload optimizer to CPU

# DeepSpeed ZeRO-3
deepspeed:
  stage: 3
  offload_optimizer:
    device: cpu
  offload_param:
    device: cpu

# Data
train_data: /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/moshi_train.jsonl
val_data: /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/moshi_val.jsonl

# Monitoring
wandb: true
project_name: moshi-twi-finetune
```

---

## 🚀 Training Commands (Once Separate Environment Ready)

### Prepare Data
```bash
# Convert mono → stereo
python scripts/prepare_stereo_data.py \
    --input /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/processed_audio/tts_24k \
    --output /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/moshi_stereo \
    --manifest /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests/moshi_train.csv

# Create JSONL manifest
python scripts/create_moshi_manifest.py
```

### Start Training
```bash
# Single GPU (RTX 4000)
torchrun --nproc_per_node=1 train.py \
    --config config_twi.yaml \
    --output_dir /opt/kasaai/apps/voice-lab/models/moshi_twi
```

### Monitor Training
```bash
# TensorBoard
tensorboard --logdir /opt/kasaai/apps/voice-lab/models/moshi_twi/logs

# Weights & Biases (if configured)
wandb login
# Training will automatically log to W&B
```

---

## ⚠️ Challenges for RTX 4000 (20GB)

### Memory Constraints

| Component | Memory Usage | Our Capacity |
|-----------|--------------|--------------|
| Base Model | ~14-16 GB | 20 GB |
| Batch Size 1 | ~18-20 GB | 20 GB |
| **Risk**: OOM errors | **HIGH** | **Requires optimization** |

### Mitigation Strategies

1. **LoRA rank 64** (instead of 128)
2. **Batch size 1** + gradient accumulation 16
3. **DeepSpeed ZeRO-3** with CPU offloading
4. **Gradient checkpointing**
5. **Short audio clips** (50 sec instead of 100 sec)
6. **Mixed precision (FP16/BF16)**

### Expected Performance

- **Tokens/sec**: ~1-2k (vs 12k on H100)
- **Training time**: ~5-7 days (vs ~1 day on H100)
- **Memory**: 19-20 GB (close to limit)

---

## 🎯 Recommendation

### Short-term: Skip Moshi

**Reasons**:
1. Dependency conflicts with other fine-tuning scripts
2. Below minimum VRAM requirements (20GB < 24GB)
3. Complex stereo audio preparation needed
4. Long training time on RTX 4000

**Focus instead on**:
- ✅ Wav2Vec2 (008) - Ready to use
- ✅ MeloTTS (019) - Ready to use
- ✅ Coqui XTTS (010) - Ready to use

### Long-term: Dedicated Setup

If Moshi becomes critical:

1. **Separate server** with ≥24GB GPU (e.g., RTX 4090, A100)
2. **Docker container** for isolation
3. **Dedicated venv** to avoid conflicts
4. **Custom data pipeline** for stereo conversion

---

## 📚 Resources

- **Moshi Paper**: https://kyutai.org/Moshi.pdf
- **GitHub**: https://github.com/kyutai-labs/moshi
- **Fine-tuning Repo**: https://github.com/kyutai-labs/moshi-finetune
- **Dataset**: https://huggingface.co/datasets/kyutai/DailyTalkContiguous
- **Models**: https://huggingface.co/kyutai

---

## 📝 Status

- ✅ Research completed
- ✅ Installation tested (conflicts found)
- ❌ Not compatible with current venv
- ⚠️ Hardware below minimum specs
- 📋 Documented setup for future use

**Decision**: **Defer Moshi** until separate environment or dedicated hardware available.

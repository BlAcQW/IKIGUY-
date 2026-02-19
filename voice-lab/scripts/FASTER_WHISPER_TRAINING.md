# Faster Whisper Fine-tuning for Ghanaian Languages

## Overview

This training setup allows fine-tuning Whisper models on Ghanaian language data stored on Hetzner, while running on RunPod GPU, **without downloading all data to RunPod**.

## Strategy: SSH Mount + Streaming DataLoader

### Why This Approach?

1. **No Preprocessing Needed**: Audio is already 16kHz WAV (perfect for ASR)
2. **Space Efficient**: Only manifests (19MB) + model checkpoints (~1GB) on RunPod
3. **Streaming**: Audio loaded on-demand during training via SSH mount
4. **Feature Caching**: Mel spectrograms cached in memory (much smaller than audio)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ RunPod GPU Instance (A40 / A100)                            │
│                                                              │
│  ┌────────────────┐         ┌──────────────────────┐       │
│  │  Training Loop │ ◄─────► │  SSH Mount (SSHFS)   │       │
│  │   (Streaming)  │         │  /mnt/hetzner_storage│       │
│  └────────────────┘         └──────────┬───────────┘       │
│         │                               │                   │
│         │  Loads batches                │  Network          │
│         ▼  on-demand                    ▼  streaming        │
│  ┌────────────────┐                                         │
│  │ Feature Cache  │         ┌──────────────────────┐       │
│  │ (Mel Spectro)  │         │   Hetzner Storage    │       │
│  └────────────────┘         │   (10TB, 600GB used) │       │
│                              │                      │       │
│  ┌────────────────┐         │  - Twi: 335h         │       │
│  │ Model Checkpts │         │  - Dagbani: 18k files│       │
│  │  (~1-2GB each) │         │  - Ewe: ~20k files   │       │
│  └────────────────┘         │  - + others          │       │
│                              └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Data Format

### Manifest Structure (faster_whisper_train.csv)

```csv
audio_path,transcript,duration,speaker_id,language,dialect,dataset
/opt/kasaai/.../audio_file.wav,Transcript text,1.5,speaker_id,tw,fante,dataset_name
```

### Current Data Available

| Language | Hours | Files | Format | Status |
|----------|-------|-------|--------|--------|
| **Twi-Akan-Fante** | 335h | 212k | 16kHz WAV | ✅ Ready |
| **Dagbani** | ~50h | 18k | MP3 | 🔄 Transferring |
| **Ewe** | ~60h | 19k+15k | MP3 | ⏸️ Extracting |
| **Dagaare** | ~40h | ~15k | TAR | 🔄 Downloading |
| **Ikposo** | ~40h | ~15k | ZIP | ⏸️ Queued |

**Total Available**: ~525+ hours across 5 Ghanaian languages

## Setup Instructions

### 1. Prerequisites

**On RunPod:**
- GPU: A40, A100, or similar (16GB+ VRAM)
- Storage: ~50GB for checkpoints + cache
- Python 3.8+

**On Hetzner:**
- Storage Box with SSH access
- Data already organized with manifests

### 2. Deployment

Upload scripts to RunPod:

```bash
# On local machine
scp -P <runpod_port> -i ~/.ssh/id_ed25519 \
    train_faster_whisper_ghanaian.py \
    deploy_faster_whisper_runpod.sh \
    root@<runpod_host>:/workspace/
```

Run deployment script:

```bash
# On RunPod
cd /workspace
chmod +x deploy_faster_whisper_runpod.sh
./deploy_faster_whisper_runpod.sh
```

This will:
1. Install dependencies (transformers, datasets, sshfs, etc.)
2. Mount Hetzner storage via SSH
3. Verify data accessibility
4. Setup training environment

### 3. Training

#### Basic Training (Twi only)

```bash
python train_faster_whisper_ghanaian.py \
    --model openai/whisper-small \
    --epochs 3 \
    --batch-size 16 \
    --lr 1e-5 \
    --languages tw \
    --output-dir /workspace/outputs/whisper-twi
```

#### Multi-language Training (All Ghanaian languages)

```bash
python train_faster_whisper_ghanaian.py \
    --model openai/whisper-small \
    --epochs 5 \
    --batch-size 16 \
    --lr 1e-5 \
    --languages tw dag ee dga kpo \
    --output-dir /workspace/outputs/whisper-ghanaian
```

#### Advanced Options

```bash
python train_faster_whisper_ghanaian.py \
    --model openai/whisper-medium \     # Larger model
    --epochs 10 \                        # More epochs
    --batch-size 8 \                     # Smaller batch (for larger models)
    --lr 5e-6 \                          # Lower learning rate
    --languages tw dag \                 # Subset of languages
    --output-dir /workspace/outputs/whisper-tw-dag
```

### 4. Monitoring

**TensorBoard:**

```bash
tensorboard --logdir /workspace/outputs/whisper-ghanaian
# Access at: http://<runpod_public_ip>:6006
```

**Training Log:**

```bash
tail -f /workspace/outputs/whisper-ghanaian/training.log
```

**GPU Usage:**

```bash
watch -n 1 nvidia-smi
```

## Performance Expectations

### Training Speed (A40 GPU)

| Batch Size | Steps/sec | Hours for 10k steps |
|------------|-----------|---------------------|
| 8          | ~0.5      | ~5.5 hours          |
| 16         | ~0.8      | ~3.5 hours          |
| 32         | ~1.0      | ~2.8 hours          |

### Expected WER (Word Error Rate)

| Language | Baseline | After 3 epochs | After 10 epochs |
|----------|----------|----------------|-----------------|
| Twi      | ~60%     | ~25-30%        | ~15-20%         |
| Dagbani  | ~80%     | ~35-45%        | ~25-35%         |
| Ewe      | ~75%     | ~30-40%        | ~20-30%         |

*Baseline = openai/whisper-small without fine-tuning*

## Advantages of This Approach

### ✅ Space Efficient

- **No full download**: Audio streamed from Hetzner during training
- **Small footprint**: Only ~50GB for checkpoints (vs 500GB+ for full data)
- **Scalable**: Can train on 1000+ hours without storage issues

### ✅ Flexible

- **Easy data updates**: Just update manifests, no re-download
- **Language filtering**: Train on subsets by filtering manifest
- **Quick iterations**: No waiting for multi-hour downloads

### ✅ Cost Effective

- **Shorter pod runtime**: No download time
- **Smaller storage**: Don't pay for unused storage on RunPod
- **One-time data transfer**: Data stays on Hetzner (cheaper storage)

## Preprocessing: NOT NEEDED! ✅

### Why No Preprocessing?

1. **Audio already correct format**: 16kHz WAV files (Whisper's native)
2. **Manifests ready**: CSV files with paths and transcripts
3. **On-the-fly extraction**: Features extracted during training (cached)

### What About Feature Extraction?

Features (Mel spectrograms) are:
- **Extracted on-demand** during first training pass
- **Cached in memory** for subsequent epochs
- **Much smaller** than audio (~10x compression)

A 30-second audio file:
- Raw WAV: ~960KB
- Mel spectrogram: ~80KB (cached)

For 335 hours of Twi:
- Raw audio: ~480GB
- Cached features: ~48GB (fits in GPU memory + RAM)

## Alternative: Full Download (If Needed)

If SSH mount is unstable, you can pre-download:

```bash
# On RunPod
rsync -avz --progress \
    user@hetzner:/voice-lab/data/twi-akan-fante/processed/processed_audio/asr_16k/ \
    /workspace/data/twi/

# Then update manifest paths
sed -i 's|/opt/kasaai/apps/voice-lab/data|/workspace/data|g' \
    faster_whisper_train.csv
```

But this takes:
- **Time**: ~2-4 hours for 335h of Twi
- **Space**: ~480GB
- **Cost**: More RunPod storage fees

## Troubleshooting

### SSH Mount Fails

```bash
# Check Hetzner access
ssh user@your-storagebox.de

# Remount
fusermount -u /mnt/hetzner_storage
sshfs user@your-storagebox.de:/ /mnt/hetzner_storage
```

### Slow Training

- **Reduce batch size**: Lower memory usage allows bigger batches
- **Check network**: `iftop` to monitor Hetzner bandwidth
- **Cache features**: First epoch slower (extracting), subsequent faster

### Out of Memory

- **Lower batch size**: Try 8 or 4
- **Use gradient checkpointing**: Already enabled in script
- **Use smaller model**: whisper-tiny or whisper-base

## Cost Estimate

### RunPod A40 @ $0.79/hour

| Training Scenario | Duration | Cost |
|------------------|----------|------|
| Twi only (3 epochs) | ~10 hours | ~$8 |
| 3 languages (5 epochs) | ~40 hours | ~$32 |
| 5 languages (10 epochs) | ~100 hours | ~$79 |

### Hetzner Storage @ $3.81/month (1TB)

- **One-time cost**: Storage already paid
- **No extra charges**: Just streaming bandwidth (free within limits)

## Next Steps

1. **Start with Twi only**: Validate the setup works
2. **Add more languages**: Once Twi works, add Dagbani, Ewe, etc.
3. **Evaluate results**: Test WER on held-out test sets
4. **Deploy model**: Export to ONNX/CTranslate2 for production

## Scripts Reference

- **`train_faster_whisper_ghanaian.py`**: Main training script
- **`deploy_faster_whisper_runpod.sh`**: RunPod setup automation
- **`FASTER_WHISPER_TRAINING.md`**: This documentation

## Contact

For issues or questions:
- Check logs: `/workspace/outputs/whisper-ghanaian/training.log`
- GPU issues: `nvidia-smi`
- Mount issues: `df -h | grep hetzner`

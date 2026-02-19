# MeloTTS Twi Training Guide

Complete guide for training MeloTTS models on Twi language data.

## Table of Contents
- [Overview](#overview)
- [Dataset Specifications](#dataset-specifications)
- [Directory Structure](#directory-structure)
- [Training Workflow](#training-workflow)
- [Configuration Files](#configuration-files)
- [Training Commands](#training-commands)
- [Monitoring Training](#monitoring-training)
- [Troubleshooting](#troubleshooting)

## Overview

This guide covers the complete workflow for training MeloTTS models on Twi language data, from data preparation to training and inference.

**Key Specifications:**
- **Sample Rate**: 44.1kHz (MeloTTS standard)
- **Source Data**: Twi-Akan-Fante dataset (22.05kHz)
- **Training Approach**: VITS-based architecture with BERT embeddings
- **Dataset Sizes**:
  - Small: 10K samples (for quick testing)
  - Full: 212,000 training + 11,650 validation samples

## Dataset Specifications

### Available Datasets

| Dataset | Training Samples | Validation Samples | Purpose |
|---------|-----------------|-------------------|---------|
| Small (`data/twi/`) | 10,000 | 2,000 | Quick testing and experimentation |
| Full (`data/twi_full/`) | 212,000 | 11,650 | Production training |

### Data Requirements

- **Audio Format**: WAV, 44.1kHz, mono
- **Source Sample Rate**: 22.05kHz (automatically resampled to 44.1kHz)
- **Text Format**: UTF-8 encoded text transcriptions
- **Speaker**: Single speaker (TWI-Speaker)

## Directory Structure

```
/opt/kasaai/apps/voice-lab/
├── data/twi-akan-fante/processed/
│   ├── model_manifests/
│   │   ├── melo_tts_train.csv      # Training manifest (212K samples)
│   │   └── melo_tts_val.csv        # Validation manifest (11K samples)
│   ├── melo_tts_44k/               # Small dataset (10K samples, 44.1kHz)
│   └── melo_tts_44k_full/          # Full dataset (212K samples, 44.1kHz)
│       ├── train_wavs/
│       └── val_wavs/
│
├── notebooks/local/
│   ├── prepare_twi_full_dataset.py # Data preparation script
│   └── MeloTTS/
│       └── melo/
│           ├── data/
│           │   ├── twi/            # Small dataset config and lists
│           │   │   ├── config.json
│           │   │   ├── metadata.list
│           │   │   ├── train.list
│           │   │   └── val.list
│           │   └── twi_full/       # Full dataset config and lists
│           │       ├── config.json
│           │       ├── metadata.list
│           │       ├── train.list
│           │       └── val.list
│           ├── preprocess_text_melo_tts.py  # BERT embedding generation
│           ├── train.py            # Training script
│           ├── train.sh            # Training wrapper
│           └── logs/               # Training logs and checkpoints
```

## Training Workflow

### Phase 1: Data Preparation (Full Dataset)

**Script**: `/opt/kasaai/apps/voice-lab/notebooks/local/prepare_twi_full_dataset.py`

This script:
1. Loads training/validation manifests
2. Resamples audio from 22.05kHz → 44.1kHz
3. Converts to mono if needed
4. Creates metadata.list in MeloTTS format

**Format**: `path/to/audio.wav|<speaker_name>|<language_code>|<text>`

**Run:**
```bash
cd /opt/kasaai/apps/voice-lab/notebooks/local
python prepare_twi_full_dataset.py
```

**Output:**
- Resampled audio: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/melo_tts_44k_full/`
- Metadata file: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/data/twi_full/metadata.list`

**Duration**: ~40 hours for 212K samples

### Phase 2: BERT Embedding Generation

**Script**: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/preprocess_text_melo_tts.py`

This script:
1. Reads metadata.list
2. Generates BERT embeddings for text
3. Creates train.list and val.list with embedded paths

**Run:**
```bash
cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo
/opt/kasaai/apps/core_backend/venv/bin/python preprocess_text_melo_tts.py --metadata data/twi_full/metadata.list --clean
```

**Output:**
- `data/twi_full/metadata.list.cleaned` - Cleaned metadata
- `data/twi_full/train.list` - Training samples with BERT embeddings (default: only 4-8 samples)
- `data/twi_full/val.list` - Validation samples with BERT embeddings

**Important:** The default validation split is too small (4-8 samples). After BERT preprocessing, create a proper train/val split:

```bash
# Shuffle and split: 212K train / 11.6K val
cat data/twi_full/metadata.list.cleaned | shuf > data/twi_full/metadata.list.shuffled
head -212000 data/twi_full/metadata.list.shuffled > data/twi_full/train.list
tail -11650 data/twi_full/metadata.list.shuffled > data/twi_full/val.list
```

**Duration**: ~1-2 hours for 223K samples

### Phase 3: Training

**Script**: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/train.sh`

**Run:**
```bash
cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo

# Run in foreground (with output to terminal)
bash train.sh data/twi_full/config.json 1

# OR run in background (recommended for long training)
nohup /opt/kasaai/apps/core_backend/venv/bin/torchrun --nproc_per_node=1 --master_port=$((RANDOM + 30000)) train.py --c data/twi_full/config.json --model twi_full > /opt/kasaai/apps/voice-lab/notebooks/local/melo_training_full.log 2>&1 &
```

**Arguments:**
- First argument: Path to config file
- Second argument: Number of GPUs

**Output:**
- Checkpoints: `logs/twi_full/` (saved every 1000 iterations)
- Training logs: `logs/twi_full/train.log` and `/opt/kasaai/apps/voice-lab/notebooks/local/melo_training_full.log` (if running in background)

**Expected Training Time:**
- Total iterations: ~33,274 (212K samples ÷ 6 batch size × epochs)
- Duration: ~24-48 hours depending on hardware
- Checkpoint frequency: Every 1000 iterations
- Evaluation frequency: Every 1000 iterations

## Configuration Files

### Small Dataset: `data/twi/config.json`

```json
{
  "train": {
    "log_interval": 200,
    "eval_interval": 1000,
    "epochs": 10000,
    "learning_rate": 0.0003,
    "batch_size": 6,
    "segment_size": 16384
  },
  "data": {
    "training_files": "data/twi/train.list",
    "validation_files": "data/twi/val.list",
    "sampling_rate": 44100,
    "n_mel_channels": 128,
    "n_speakers": 1,
    "spk2id": {
      "TWI-Speaker": 0
    }
  }
}
```

### Full Dataset: `data/twi_full/config.json`

Identical to small dataset config, but with updated file paths:
```json
{
  "data": {
    "training_files": "data/twi_full/train.list",
    "validation_files": "data/twi_full/val.list",
    ...
  }
}
```

### Key Training Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `batch_size` | 6 | Samples per batch |
| `learning_rate` | 0.0003 | Initial learning rate |
| `lr_decay` | 0.999875 | Learning rate decay |
| `sampling_rate` | 44100 | Audio sample rate (Hz) |
| `segment_size` | 16384 | Audio segment length |
| `log_interval` | 200 | Steps between log outputs |
| `eval_interval` | 1000 | Steps between evaluations |

## Training Commands

### Small Dataset (10K samples)
```bash
cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo
bash train.sh data/twi/config.json 1
```

### Full Dataset (212K samples)
```bash
cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo
bash train.sh data/twi_full/config.json 1
```

### Multi-GPU Training
```bash
bash train.sh data/twi_full/config.json 2  # Use 2 GPUs
```

### Resume Training
The training script automatically loads the latest checkpoint from `logs/{model_name}/` if available.

## Monitoring Training

### Training Logs

Logs are saved to: `logs/{model_name}/`

**Key Metrics:**
- `loss_disc`: Discriminator loss
- `loss_gen`: Generator loss
- `loss_mel`: Mel-spectrogram loss
- `loss_kl`: KL divergence loss
- `grad_norm`: Gradient norm (monitor for instability)

### Check Progress

```bash
# View training log (for small dataset)
tail -f /opt/kasaai/apps/voice-lab/notebooks/local/melo_training.log

# View training log (for full dataset in background)
tail -f /opt/kasaai/apps/voice-lab/notebooks/local/melo_training_full.log

# View detailed training log
tail -f logs/twi_full/train.log

# Check GPU usage
nvidia-smi -l 1

# Monitor checkpoint directory
ls -lht logs/twi_full/ | head -20

# Check training process
ps aux | grep "train.py" | grep -v grep
```

### Training Output Example

From `logs/twi_full/train.log`:
```
2025-10-07 05:15:12,519	twi_full	INFO	Train Epoch: 1 [0%]
2025-10-07 05:15:12,532	twi_full	INFO	[3.245, 2.671, 9.154, 21.540, 6.112, 6.040, 0, 0.0003]
```

Metrics format: `[loss_disc, loss_gen, loss_mel, loss_kl, loss_fm_g, loss_fm_d, loss_dur, learning_rate]`

### Evaluation Checkpoints

Evaluation runs every 1000 steps. Checkpoints saved:
- `logs/twi_full/G_{iteration}.pth` - Generator checkpoint
- `logs/twi_full/D_{iteration}.pth` - Discriminator checkpoint
- `logs/twi_full/DUR_{iteration}.pth` - Duration predictor checkpoint

## Troubleshooting

### Common Issues

#### 1. Out of Memory (OOM)
**Error**: `CUDA out of memory`

**Solutions:**
- Reduce `batch_size` in config.json (try 4 or 2)
- Use gradient accumulation
- Enable mixed precision training (`fp16_run: true`)

#### 2. Audio Resampling Fails
**Error**: `Expected 22050Hz, got XXXXX Hz`

**Solutions:**
- Check source audio sample rate
- Update `SOURCE_SR` in `prepare_twi_full_dataset.py`
- Verify audio files are not corrupted

#### 3. BERT Embedding Generation Slow
**Solutions:**
- Ensure GPU is available for BERT model
- Process in smaller batches
- Use multi-GPU preprocessing if available

#### 4. Training Divergence
**Symptoms**: Loss values become NaN or explode

**Solutions:**
- Reduce learning rate in config.json
- Check for corrupted audio/text pairs
- Verify BERT embeddings are generated correctly
- Enable gradient clipping

#### 5. Checkpoint Not Loading
**Error**: `Error loading checkpoint`

**Solutions:**
- Check checkpoint file integrity
- Verify model architecture matches config
- Clear old checkpoints and restart training

### Performance Tips

1. **Data Loading**: Pre-generate all BERT embeddings before training
2. **Storage**: Use SSD for faster data loading during training
3. **Monitoring**: Use tensorboard for detailed loss curves
4. **Checkpointing**: Save checkpoints every 1000-5000 steps
5. **Validation**: Monitor validation loss to detect overfitting

## Next Steps

### After Training Completes

1. **Test Model with Inference**
   ```bash
   cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo
   /opt/kasaai/apps/core_backend/venv/bin/python infer.py \
     -m logs/twi_full/G_4000.pth \
     -t "Maakye, ɛte sɛn? Me din de Kofi" \
     -l EN \
     -o test_outputs

   # Output will be saved to: test_outputs/TWI-Speaker/output.wav
   ```

2. **Export for Production**
   - Copy best checkpoint to production directory
   - Test inference speed and quality
   - Create model card with training details

3. **Fine-tuning**
   - Adjust learning rate for fine-tuning
   - Use smaller batch size for stability
   - Monitor validation loss closely

## Reference Files

### Critical Scripts
- `prepare_twi_full_dataset.py` - Data preparation (audio resampling)
- `preprocess_text_melo_tts.py` - BERT embedding generation
- `train.py` - Main training script
- `train.sh` - Training wrapper with GPU management
- `infer.py` - Inference script for testing trained models

### Configuration Files
- `data/twi/config.json` - Small dataset config (10K)
- `data/twi_full/config.json` - Full dataset config (212K)

### Data Files
- `data/twi_full/metadata.list` - Audio paths and transcriptions
- `data/twi_full/train.list` - Training set with embeddings
- `data/twi_full/val.list` - Validation set with embeddings

## Support

For issues or questions:
1. Check this documentation first
2. Review training logs for error messages
3. Consult the original MeloTTS documentation: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/README.md`
4. Check GPU memory and disk space availability

---

**Last Updated**: 2025-10-07
**MeloTTS Version**: Based on VITS2 architecture
**Dataset**: Twi-Akan-Fante (212K training + 11.6K validation samples)
**Current Training**: Full dataset training in progress at `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/logs/twi_full/`

## Quick Start Summary

```bash
# 1. Prepare data (resample to 44.1kHz)
cd /opt/kasaai/apps/voice-lab/notebooks/local
python prepare_twi_full_dataset.py

# 2. Generate BERT embeddings
cd /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo
/opt/kasaai/apps/core_backend/venv/bin/python preprocess_text_melo_tts.py --metadata data/twi_full/metadata.list --clean

# 3. Create proper train/val split (default split is too small!)
cat data/twi_full/metadata.list.cleaned | shuf > data/twi_full/metadata.list.shuffled
head -212000 data/twi_full/metadata.list.shuffled > data/twi_full/train.list
tail -11650 data/twi_full/metadata.list.shuffled > data/twi_full/val.list

# 4. Start training in background
nohup /opt/kasaai/apps/core_backend/venv/bin/torchrun --nproc_per_node=1 --master_port=$((RANDOM + 30000)) train.py --c data/twi_full/config.json --model twi_full > /opt/kasaai/apps/voice-lab/notebooks/local/melo_training_full.log 2>&1 &

# 5. Monitor training
tail -f /opt/kasaai/apps/voice-lab/notebooks/local/melo_training_full.log
tail -f logs/twi_full/train.log

# 6. Test trained model
/opt/kasaai/apps/core_backend/venv/bin/python infer.py -m logs/twi_full/G_4000.pth -t "Maakye, ɛte sɛn?" -l EN -o test_outputs
```

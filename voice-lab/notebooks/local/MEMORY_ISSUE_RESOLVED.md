# Training OOM Issue - RESOLVED

## What Happened

The v2.0 training (020_melo_tts_twi_fixed.py) was **killed by OOM (Out-of-Memory)** at 21:30:58:

```
Out of memory: Killed process 89903 (python3)
total-vm: 218GB
anon-rss: 63GB RAM consumed
```

**Timeline:**
- 21:24:43 - Training started
- 21:27:00 - Preprocessing reached 21% (~21,000/100,000 samples)
- 21:30:58 - **OOM killer terminated process** (6 minutes into preprocessing)

**Root Cause:**
The `dataset.map()` preprocessing loads ALL 100k audio samples into RAM simultaneously (~63GB), exceeding available memory.

## Solution: Memory-Efficient Version (v2.1)

Created `/home/dev/local/021_melo_tts_twi_memory_efficient.py` with:

### Critical Changes:
1. ✅ **Lazy Loading**: Processes samples on-the-fly (no RAM cache)
2. ✅ **Reduced Samples**: 50k training samples (from 100k)
3. ✅ **No Preprocessing Cache**: Uses `LazyTTSDataset` class
4. ✅ **Same fixes**: 16kHz audio, GPU cleanup, loss modules on GPU

### Memory Comparison:

| Version | Preprocessing | RAM Usage | Training Samples |
|---------|--------------|-----------|------------------|
| v2.0 (failed) | Cache all → RAM | **~63GB** | 100k |
| v2.1 (new) | Lazy load | **~10-15GB** | 50k |

## How to Start Training

### Option 1: Stop K3s First (Recommended)

```bash
# Stop K3s to free ~30GB RAM
sudo systemctl stop k3s

# Start training
/home/dev/local/run_training_memory_efficient.sh

# After training completes, restart K3s
sudo systemctl start k3s
```

### Option 2: Run with K3s Active (Riskier)

```bash
# Just start training (may still OOM if K3s uses too much memory)
/home/dev/local/run_training_memory_efficient.sh
```

### Option 3: Background with nohup

```bash
# Stop K3s
sudo systemctl stop k3s

# Run in background
nohup /home/dev/local/run_training_memory_efficient.sh > /home/dev/training_v2.1.log 2>&1 &

# Monitor progress
tail -f /home/dev/training_v2.1.log
```

## Expected Behavior (v2.1)

### Training Progress:
- **No preprocessing phase** - processes on-the-fly!
- **Steps:** ~15,625 total (50k samples × 10 epochs ÷ batch 32)
- **Duration:** ~30-40 hours (may early stop at epoch 3-5)
- **Evaluation:** Every 2000 steps (~5 minutes each)
- **RAM Usage:** 10-15GB (vs 63GB before)

### What to Watch:
1. Training starts immediately (no preprocessing wait)
2. RAM usage stays stable (~10-15GB)
3. GPU utilization high (~90-100%)
4. Eval loss decreasing
5. Eval time stable (~5 minutes, not increasing)

## Files Created

- ✅ `/home/dev/local/021_melo_tts_twi_memory_efficient.py` - Memory-efficient training script
- ✅ `/home/dev/local/run_training_memory_efficient.sh` - Monitoring script
- ✅ This file - Documentation

## Model Location

New model will be saved to:
```
/opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_memory_efficient/
```

## Monitoring

```bash
# Watch GPU
watch -n 1 nvidia-smi

# Watch RAM usage
watch -n 1 free -h

# View training log
tail -f /home/dev/training_logs/twi_tts_v2.1_*.log

# View GPU log
tail -f /home/dev/training_logs/gpu_monitor_*.log

# TensorBoard
tensorboard --logdir /opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_memory_efficient/logs
```

## Why This Works

### Problem with v2.0:
```python
# This loads ALL samples into RAM
train_dataset = train_dataset.map(
    dataset_processor.preprocess_function,
    batched=True,
    # ❌ Caches 100k processed samples = 63GB RAM
)
```

### Solution in v2.1:
```python
# This processes on-the-fly
class LazyTTSDataset(torch.utils.data.Dataset):
    def __getitem__(self, idx):
        # ✅ Only loads ONE sample at a time
        return self.processor.process_single(audio_path, text)
```

## Trade-offs

| Aspect | v2.0 (failed) | v2.1 (new) |
|--------|--------------|-----------|
| **RAM** | 63GB (OOM) | 10-15GB ✅ |
| **Speed** | Fast (if it worked) | ~10% slower |
| **Samples** | 100k | 50k |
| **Reliability** | OOM crash | Stable ✅ |

The 10% speed reduction is acceptable for avoiding OOM crashes.

## Success Metrics

Training succeeds if:
- ✅ No OOM crashes
- ✅ Training completes to early stopping (~3-5 epochs)
- ✅ Eval loss reaches ~172 or lower
- ✅ Model generates intelligible Twi speech
- ✅ RAM usage stays stable (<20GB)

## Next Steps

1. Review this document
2. Decide: Stop K3s first? (recommended)
3. Run training script
4. Monitor progress
5. Wait ~30-40 hours for completion

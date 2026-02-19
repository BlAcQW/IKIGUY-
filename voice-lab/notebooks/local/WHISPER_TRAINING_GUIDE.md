# Whisper Medium Twi Training - Stop & Resume Guide

## ✅ Good News: Auto-Resume is Built-In!

The training script **automatically resumes** from the last checkpoint when restarted.

---

## 🛑 How to STOP Training Safely

### Option 1: Graceful Stop (Recommended)
Wait for the current checkpoint to save, then stop:

```bash
# Monitor for next checkpoint save
tail -f whisper_medium_twi_training.log

# When you see "Saving model checkpoint to..." or evaluation completes,
# press Ctrl+C in the terminal running the training
```

### Option 2: Kill Process (If Necessary)
```bash
# Find the process
ps aux | grep "006_faster_whisper_medium_twi.py" | grep -v grep

# Kill gracefully (allows cleanup)
kill -15 <PID>

# If it doesn't stop after 30 seconds, force kill
kill -9 <PID>
```

**Current PID**: 305796
```bash
# Stop current training
kill -15 305796
```

---

## ▶️ How to RESUME Training

### Automatic Resume (Easiest)
Just run the same command again - it will auto-detect the last checkpoint:

```bash
cd /opt/kasaai/apps/voice-lab/notebooks/local

# Run with same parameters as before
nohup python3 006_faster_whisper_medium_twi.py \
  --no_gradient_checkpointing \
  > whisper_medium_twi_training.log 2>&1 &
```

The script will print:
```
📂 Resuming from checkpoint: /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/checkpoint-XXXX
```

### Manual Resume from Specific Checkpoint
If you want to resume from a specific checkpoint:

```bash
# The script auto-finds the latest, but you can modify the code to specify one
# Current checkpoints:
ls -lth /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/
```

---

## 📋 What Gets Saved in Checkpoints

Each checkpoint contains everything needed to resume:

```
checkpoint-6500/
├── model.safetensors          # Model weights (2.9GB)
├── optimizer.pt               # Optimizer state (5.7GB)
├── scheduler.pt               # Learning rate scheduler
├── trainer_state.json         # Training progress, metrics, step count
├── rng_state.pth              # Random number generator state
├── config.json                # Model configuration
├── generation_config.json     # Generation settings
└── preprocessor_config.json   # Audio preprocessing settings
```

**Total Size**: ~8.6GB per checkpoint

---

## 🔍 Before Resuming - Check Status

```bash
# 1. Find latest checkpoint
ls -lth /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/ | grep checkpoint | head -3

# 2. Check what step it's at
cat /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/checkpoint-6500/trainer_state.json | \
  python3 -c "import sys, json; state=json.load(sys.stdin); print(f\"Step: {state['global_step']}, Epoch: {state['log_history'][-1].get('epoch', 'N/A')}\")"

# 3. Check metrics
grep "eval_wer" whisper_medium_twi_training.log | tail -3
```

---

## ⚠️ Important Notes

### Resume Behavior
- ✅ **Step count continues** from where it stopped
- ✅ **Optimizer state preserved** (learning continues smoothly)
- ✅ **Best model tracking maintained** (best WER checkpoint remembered)
- ✅ **Epoch count continues**
- ✅ **Random seed state preserved** (reproducibility)

### When Stopping
- **Safe time to stop**: Right after checkpoint save (every 500 steps / ~12 min)
- **Risky time to stop**: During checkpoint save (wait for completion)
- **Lost work**: At most ~500 steps (12 minutes) if stopped between checkpoints

### Disk Space
- Each checkpoint: **~8.6GB**
- Max checkpoints kept: **3** (due to `save_total_limit=3`)
- Total disk usage: **~26GB** for checkpoints + logs

---

## 📊 Example: Stop & Resume Flow

### Scenario: Stop at Step 7500, Resume Later

```bash
# 1. CHECK CURRENT STATUS
tail -10 whisper_medium_twi_training.log
# Shows: Step 1591/5591 (28%)

# 2. STOP TRAINING
kill -15 305796
# Wait 10-20 seconds for graceful shutdown

# 3. VERIFY CHECKPOINTS SAVED
ls -lth /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/
# checkpoint-6500 (latest)
# checkpoint-6000
# checkpoint-5500

# 4. RESUME LATER (hours, days later - doesn't matter!)
cd /opt/kasaai/apps/voice-lab/notebooks/local
nohup python3 006_faster_whisper_medium_twi.py \
  --no_gradient_checkpointing \
  > whisper_medium_twi_training.log 2>&1 &

# 5. CONFIRM RESUME
tail -20 whisper_medium_twi_training.log
# Should see: "📂 Resuming from checkpoint: .../checkpoint-6500"
# Training continues from step 6500!
```

---

## 🚨 Troubleshooting

### Problem: "No checkpoint found" on resume
**Solution**: Check if checkpoints exist
```bash
ls /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/checkpoint-*
```
If empty, training will start from scratch.

### Problem: "Checkpoint corrupted" error
**Solution**: Use previous checkpoint
```bash
# Rename/remove corrupted checkpoint
mv checkpoint-6500 checkpoint-6500.bad

# Restart - will use checkpoint-6000 instead
```

### Problem: Training restarts from Step 0
**Cause**: Output directory doesn't contain valid checkpoints
**Solution**:
1. Check `--output_path` matches where checkpoints are saved
2. Ensure checkpoints weren't deleted

### Problem: Out of disk space during checkpoint save
**Solution**:
1. Free up space immediately
2. Increase `save_total_limit` to keep fewer checkpoints
3. Use external storage for checkpoint directory

---

## 💡 Best Practices

### 1. Before Stopping
```bash
# Wait for checkpoint save completion
tail -f whisper_medium_twi_training.log | grep -E "Saving|checkpoint"
```

### 2. Regular Backups (Optional but Recommended)
```bash
# Backup best checkpoint
cp -r /opt/kasaai/apps/voice-lab/models/whisper_medium_twi/checkpoint-6500 \
      /backup/location/checkpoint-6500-backup-$(date +%Y%m%d)
```

### 3. Monitor Before Resume
```bash
# Check GPU availability
nvidia-smi

# Check disk space
df -h /opt/kasaai/apps/voice-lab/

# Check memory
free -h
```

### 4. Test Resume on Small Dataset First
If unsure, test resume functionality:
```bash
# Train with limited samples
python3 006_faster_whisper_medium_twi.py \
  --max_train_samples 1000 \
  --max_eval_samples 100

# Stop after 1-2 checkpoints
# Resume and verify it continues correctly
```

---

## 📈 Resume Impact on Training

**No negative impact!** The resume is seamless:

- Learning rate schedule continues correctly
- Model convergence unaffected
- Metrics continuous (no spike or drop)
- Total training time = sum of all sessions

**Example Timeline:**
```
Session 1: Train steps 0 → 6500 (stopped)
Session 2: Resume steps 6500 → 15000 (stopped)
Session 3: Resume steps 15000 → 55910 (complete)

Final model: Identical to training 0 → 55910 in one session
```

---

## Summary

✅ **Stopping is safe** - worst case lose <500 steps (~12 min)
✅ **Resuming is automatic** - just rerun the same command
✅ **No quality loss** - training continues seamlessly
✅ **Flexible timing** - resume hours or days later

**Current Training PID**: 305796
**Latest Checkpoint**: checkpoint-6500 (Step 6500, WER 16.38%)
**Safe to stop**: Anytime, but best right after checkpoint save

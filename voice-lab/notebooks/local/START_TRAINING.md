# How to Start the Fixed Twi TTS Training

## Quick Start

```bash
# Option 1: Run in foreground (you can see output in real-time)
/home/dev/local/run_training_with_monitoring.sh

# Option 2: Run in background with nohup (recommended for long training)
nohup /home/dev/local/run_training_with_monitoring.sh > /home/dev/training_output.log 2>&1 &

# Check if it's running
ps aux | grep 020_melo_tts_twi_fixed
```

## What This Training Does

### Critical Fixes Applied:
1. ✅ **16kHz audio** - No resampling! (was causing 20x slowdown)
2. ✅ **100k samples** - Increased from 50k
3. ✅ **2k validation** - Reduced from 5k (faster evaluation)
4. ✅ **Fixed GPU initialization** - Loss modules start on GPU
5. ✅ **Memory cleanup** - Prevents memory leaks during evaluation

### Training Parameters:
- **Dataset:** 100,000 training samples, 2,000 validation samples
- **Epochs:** 10 (but will likely early stop at ~3)
- **Batch size:** 2 (effective 32 with gradient accumulation)
- **Evaluation:** Every 2,000 steps
- **Save:** Every 2,000 steps (keeps best 3 checkpoints)
- **Early stopping:** 3 evaluations without improvement

### Expected Behavior:
- **Total steps:** ~31,250
- **Duration:** ~50-60 hours (may stop earlier)
- **Evaluation time:** ~5 minutes (vs 83 minutes before!)
- **Memory usage:** Stable (no leak)

## Monitoring Progress

### View Live Logs:
```bash
tail -f /home/dev/training_logs/twi_tts_v2_fixed_*.log
```

### Check GPU Usage:
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# View GPU log
tail -f /home/dev/training_logs/gpu_monitor_*.log
```

### TensorBoard (view training curves):
```bash
tensorboard --logdir /opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_fixed/logs
```

## Checkpoints

Checkpoints saved at: `/opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_fixed/`

- `checkpoint-2000/` - First checkpoint
- `checkpoint-4000/` - Second checkpoint
- `checkpoint-XXXX/` - Best model (will be identified in trainer_state.json)

## Stopping Training

```bash
# If running in foreground, press Ctrl+C

# If running in background:
ps aux | grep 020_melo_tts_twi_fixed
kill <PID>
```

## After Training Completes

The best model will be at the checkpoint with lowest `eval_loss` (check `trainer_state.json`).

To test the model:
```python
from transformers import VitsModel, AutoTokenizer
import torchaudio

# Load best checkpoint (example: checkpoint-4000)
model = VitsModel.from_pretrained(
    "/opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_fixed/checkpoint-4000"
)
tokenizer = AutoTokenizer.from_pretrained(
    "/opt/kasaai/apps/voice-lab/models/melo_tts_twi_v2_fixed/checkpoint-4000"
)

# Generate speech
model.eval()
model = model.to("cuda")
text = "Meda wo ase"  # Thank you in Twi
inputs = tokenizer(text, return_tensors="pt").to("cuda")
outputs = model(**inputs)
waveform = outputs.waveform

# Save
waveform_cpu = waveform.cpu().squeeze(0)
if waveform_cpu.dim() == 1:
    waveform_cpu = waveform_cpu.unsqueeze(0)
torchaudio.save("output.wav", waveform_cpu, 16000)
```

## Comparison with Previous Training

| Metric | Old (v1) | New (v2 Fixed) | Improvement |
|--------|----------|----------------|-------------|
| Sampling rate | 22kHz → 16kHz | Native 16kHz | No resampling |
| Training samples | 50,000 | 100,000 | 2x more data |
| Validation samples | 5,000 | 2,000 | Faster eval |
| Eval time (step 1000) | 138s | ~5min | Similar |
| Eval time (step 5000) | 5,017s (83min!) | ~5min | **16x faster!** |
| Memory leak | Yes | Fixed | Stable |
| Output quality | Low amplitude | Normalized | Better |

## Backup Previous Model

The old model (checkpoint-3000) is still available at:
`/opt/kasaai/apps/voice-lab/models/melo_tts_twi_production/checkpoint-3000`

This is a working model you can use if needed!

# Whisper African Languages Training - Restart Guide

**Date:** 2025-10-23
**Status:** Ready to restart with fixed script
**Issue:** PEFT + Whisper compatibility (RESOLVED)

---

## Executive Summary

The initial Whisper training run crashed immediately at step 0 due to a PEFT configuration error. The issue has been identified, fixed, and documented. This guide provides the complete restart procedure.

---

## What Happened

### Initial Error
```
TypeError: WhisperForConditionalGeneration.forward() got an unexpected keyword argument 'input_ids'
```

### Root Cause
- **Location:** `runpod_whisper_african_qlora_streaming.py:599`
- **Issue:** LoraConfig included `task_type=TaskType.SEQ_2_SEQ_LM`
- **Why It Failed:**
  - This task type wraps Whisper with `PeftModelForSeq2SeqLM`
  - This wrapper is for text-to-text models (T5, BART) using `input_ids`
  - Whisper is speech-to-text using `input_features` (mel spectrograms)
  - PEFT injected wrong argument → immediate crash at step 0

### Timeline
- **Oct 22, 09:19 AM**: Training started with broken script
- **Oct 22, 09:19 AM**: Crashed at step 0 (0% progress)
- **Oct 23, 07:40 PM**: Fixed script created with `task_type` removed

### Impact
- **No checkpoints saved** (crashed before first save at step 50)
- **No training progress** made
- **Must restart from scratch** with fixed script

---

## The Fix

### Changed Code

**Before (Broken):**
```python
lora_config = LoraConfig(
    r=config.lora_r,
    lora_alpha=config.lora_alpha,
    target_modules=config.lora_target_modules,
    lora_dropout=config.lora_dropout,
    bias="none",
    task_type=TaskType.SEQ_2_SEQ_LM  # ❌ This breaks Whisper!
)
```

**After (Fixed):**
```python
lora_config = LoraConfig(
    r=config.lora_r,
    lora_alpha=config.lora_alpha,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=config.lora_dropout,
    bias="none"
    # task_type removed - let PEFT use base PeftModel ✅
)
```

### Fixed Files
- ✅ `runpod_whisper_african_qlora_streaming_fixed.py` - Main training script
- ✅ `start_whisper_fixed.sh` - Startup script
- ✅ `WHISPER_PEFT_FIX.md` - Technical documentation

---

## Restart Procedure

### Prerequisites

1. **RunPod Instance**
   - GPU: NVIDIA A40 (46GB VRAM)
   - Template: RunPod PyTorch 2.1.0
   - Storage: 50GB+ container disk

2. **HuggingFace Authentication**
   ```bash
   huggingface-cli login --token YOUR_HF_TOKEN
   ```
   - Required for NaijaVoices dataset access
   - Token: https://huggingface.co/settings/tokens
   - Access request: https://huggingface.co/datasets/naijavoices/naijavoices-dataset

3. **Weights & Biases** (Optional but recommended)
   ```bash
   wandb login YOUR_WANDB_KEY
   ```

### Step 1: Start RunPod Instance

```bash
# If you have an existing pod
runpod start POD_ID

# Or create a new pod via RunPod web interface
# Recommended: A40 (46GB VRAM), PyTorch 2.1.0 template
```

### Step 2: Connect and Setup

```bash
# SSH into RunPod
ssh -p PORT root@RUNPOD_IP

# Navigate to workspace
cd /workspace

# Create training directory
mkdir -p whisper-training
cd whisper-training
```

### Step 3: Copy Fixed Scripts

**From local machine:**
```bash
# Copy fixed training script
scp -P PORT \
  /opt/kasaai/apps/tts-deployment/runpod-backup/runpod_whisper_african_qlora_streaming_fixed.py \
  root@RUNPOD_IP:/workspace/whisper-training/

# Copy startup script
scp -P PORT \
  /opt/kasaai/apps/tts-deployment/runpod-backup/start_whisper_fixed.sh \
  root@RUNPOD_IP:/workspace/whisper-training/

# Make executable
ssh -p PORT root@RUNPOD_IP "chmod +x /workspace/whisper-training/start_whisper_fixed.sh"
```

### Step 4: Install Dependencies

**On RunPod:**
```bash
pip install --upgrade pip
pip install transformers==4.43.0
pip install peft==0.12.0
pip install accelerate==0.34.0
pip install datasets==2.20.0
pip install evaluate==0.4.2
pip install jiwer  # For WER metric
pip install librosa
pip install soundfile
pip install bitsandbytes
pip install wandb
pip install psutil
pip install pandas
```

### Step 5: Authenticate

```bash
# HuggingFace (REQUIRED for NaijaVoices)
huggingface-cli login --token YOUR_HF_TOKEN

# Weights & Biases (optional)
wandb login YOUR_WANDB_KEY
```

### Step 6: Start Training

```bash
# Using the startup script
./start_whisper_fixed.sh

# Or directly with Python
python3 runpod_whisper_african_qlora_streaming_fixed.py \
  --output_dir ./outputs/whisper-small-african-qlora \
  --use_wandb \
  --wandb_project whisper-african-qlora \
  --wandb_run_name "run-$(date +%Y%m%d-%H%M%S)"
```

### Step 7: Monitor Training

**Real-time logs:**
```bash
tail -f whisper_training.log
```

**GPU monitoring:**
```bash
watch -n 1 nvidia-smi
```

**Weights & Biases:**
- Visit: https://wandb.ai/YOUR_USERNAME/whisper-african-qlora

### Step 8: Backup Checkpoints

Set up periodic checkpoint backups to Hetzner:

```bash
# Create backup script
cat > backup_checkpoints.sh << 'EOF'
#!/bin/bash
CHECKPOINT_DIR="/workspace/whisper-training/outputs/whisper-small-african-qlora"
BACKUP_HOST="dev@148.251.0.46"
BACKUP_DIR="/opt/kasaai/apps/voice-lab/models/whisper-checkpoints"

rsync -avz --progress \
  $CHECKPOINT_DIR/ \
  $BACKUP_HOST:$BACKUP_DIR/
EOF

chmod +x backup_checkpoints.sh

# Run every 6 hours
*/360 * * * * /workspace/whisper-training/backup_checkpoints.sh
```

---

## Expected Training Metrics

### Configuration
- **Model:** openai/whisper-small (244M parameters)
- **Method:** QLoRA (4-bit quantization)
- **Trainable:** 11.2M parameters (4.4% of total)
- **Batch Size:** 16 per device × 2 gradient accumulation = 32 effective
- **Steps:** 15,000 total
- **Evaluation:** Every 500 steps
- **Checkpoints:** Every 500 steps (3 most recent kept)

### Data
- **Languages:** 3 (Hausa, Yoruba, Igbo)
- **Total Hours:** ~1,880 hours (streaming)
- **Source:** NaijaVoices HuggingFace datasets
- **Sampling:** Weighted by language (equal probabilities)

### Performance Targets
- **WER Target:** 12-25% (depending on language)
- **Training Time:** ~48-72 hours on A40
- **GPU Memory:** ~10-15GB / 46GB
- **Final Model Size:** ~100MB (LoRA adapters only)

---

## Monitoring Checklist

During training, verify:

- [ ] Training starts without errors
- [ ] GPU utilization >80%
- [ ] Loss decreasing over time
- [ ] WER decreasing over time
- [ ] Checkpoints saving every 500 steps
- [ ] No OOM (out of memory) errors
- [ ] Dataset streaming working (no 504 errors)
- [ ] Weights & Biases logging active

---

## Troubleshooting

### Issue: Training still crashes with `input_ids` error
**Solution:** Verify you're using the FIXED script:
```bash
grep -n "task_type" runpod_whisper_african_qlora_streaming_fixed.py
# Should NOT find task_type in LoraConfig
```

### Issue: HuggingFace authentication fails
**Solution:**
1. Request access: https://huggingface.co/datasets/naijavoices/naijavoices-dataset
2. Create token: https://huggingface.co/settings/tokens (write access)
3. Login: `huggingface-cli login --token YOUR_TOKEN`

### Issue: Out of memory
**Solutions:**
- Reduce batch size: Change `per_device_train_batch_size` from 16 to 8
- Reduce max audio length: Change `max_audio_length` from 30 to 20 seconds

### Issue: Dataset streaming slow/failing
**Solutions:**
- Check internet connection on RunPod
- Verify HF authentication
- Enable caching: Set `cache_dir` in dataset loading

---

## Post-Training Steps

After training completes successfully:

### 1. Save Final Model
```bash
# Model saved automatically to:
./outputs/whisper-small-african-qlora/final/
```

### 2. Backup to Hetzner
```bash
rsync -avz --progress \
  /workspace/whisper-training/outputs/ \
  dev@148.251.0.46:/opt/kasaai/apps/voice-lab/models/whisper-african/
```

### 3. Push to HuggingFace Hub (Optional)
```bash
# If --push_to_hub was enabled
# Model will be at: huggingface.co/ailabsafrica/whisper-small-african
```

### 4. Test the Model
```bash
# Create test script on Hetzner
python test_whisper_model.py --model_path ./models/whisper-african/final
```

### 5. Update Documentation
- [ ] Update README.md with training results (WER, CER)
- [ ] Document model performance per language
- [ ] Add usage examples
- [ ] Create model card for HuggingFace

---

## Success Criteria

Training is considered successful when:

1. ✅ Completes 15,000 steps without crashes
2. ✅ Final WER < 25% on evaluation set
3. ✅ All checkpoints saved properly
4. ✅ Model backed up to Hetzner
5. ✅ Model performs well on test samples

---

## Contact & Support

- **Training Logs:** `whisper_training.log`
- **Checkpoints:** `/workspace/whisper-training/outputs/whisper-small-african-qlora/checkpoint-*`
- **Technical Docs:** `/opt/kasaai/apps/tts-deployment/runpod-backup/WHISPER_PEFT_FIX.md`
- **WandB Project:** https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora

---

**Created:** 2025-10-23
**Last Updated:** 2025-10-23
**Version:** 1.0

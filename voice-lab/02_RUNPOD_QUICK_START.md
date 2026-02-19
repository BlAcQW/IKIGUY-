# RunPod Whisper African QLoRA - Quick Start Guide

**🎯 Goal**: Fine-tune Whisper Small for 6 African languages in ~48-72 hours for $30-50

**Languages**: Twi, Ga, Hausa, Yoruba, Igbo, Ewe
**Expected WER**: 15-35% (60-75% improvement over base model)

---

## 🚀 Quick Setup (5 minutes)

### 1. Create RunPod Account
```bash
# Go to https://runpod.io
# Sign up and add $50 credits
```

### 2. Deploy Pod
```
Template: PyTorch 2.4 + CUDA 12.4
GPU: RTX 4090 (24GB) - $0.44/hour
Volume: 100GB Network Volume (persistent)
Ports: 8888 (Jupyter), 22 (SSH)
```

### 3. Connect via SSH
```bash
# Copy SSH command from RunPod dashboard
ssh root@<pod-ip> -p <port> -i ~/.ssh/id_rsa
```

### 4. Clone Training Code
```bash
cd /workspace

# Copy training script from local server
scp dev@<your-server-ip>:/opt/kasaai/apps/voice-lab/runpod_whisper_african_qlora.py .
scp dev@<your-server-ip>:/opt/kasaai/apps/voice-lab/WHISPER_QLORA_RUNPOD_SETUP.md .

# OR upload via Jupyter
# http://<pod-ip>:8888
```

### 5. Install Dependencies
```bash
pip install --upgrade pip

pip install transformers==4.43.0 \
    datasets==3.0.0 \
    accelerate==0.33.0 \
    bitsandbytes==0.43.0 \
    peft==0.12.0 \
    evaluate==0.4.0 \
    jiwer==3.0.0 \
    librosa==0.10.0 \
    soundfile==0.12.0 \
    wandb==0.16.0 \
    tqdm psutil pandas
```

### 6. Login to Hugging Face & Weights & Biases
```bash
# Hugging Face (for dataset downloads & model uploads)
pip install huggingface-cli
huggingface-cli login
# Paste your HF token

# Weights & Biases (for training monitoring)
wandb login
# Paste your WandB API key
```

### 7. Start Training!
```bash
python runpod_whisper_african_qlora.py \
  --output_dir ./outputs/whisper-small-african \
  --use_wandb \
  --wandb_project whisper-african-qlora \
  --wandb_run_name phase1-hausa-yoruba-igbo-twi \
  --push_to_hub \
  --hub_model_id ailabsafrica/whisper-small-african
```

---

## 📊 Monitor Training

### Option 1: Weights & Biases (Recommended)
```bash
# View at: https://wandb.ai/yourname/whisper-african-qlora
```

### Option 2: Tensorboard (Local)
```bash
# In another terminal
tensorboard --logdir ./outputs/whisper-small-african
# Open: http://localhost:6006
```

### Option 3: Check Logs
```bash
tail -f ./outputs/whisper-small-african/trainer_state.json
```

---

## ⏱️ Expected Timeline

| Phase | Duration | Checkpoint | WER |
|-------|----------|------------|-----|
| **Initial** | 0h | Start | ~80-100% |
| **Epoch 1** | 24h | 5,000 steps | ~40-60% |
| **Epoch 2** | 48h | 10,000 steps | ~25-40% |
| **Epoch 3** | 72h | 15,000 steps | **~15-30%** ✅ |

---

## 💰 Cost Tracking

```bash
# RTX 4090 @ $0.44/hour
# 72 hours = $31.68 total

# Check current cost
echo "Hours: $(uptime -p)"
echo "Estimated cost: $(($(uptime -s | cut -d: -f2) * 0.44))"
```

---

## 🔧 Troubleshooting

### Out of Memory (OOM)
```python
# Reduce batch size in script
per_device_train_batch_size: int = 8  # Was 16
gradient_accumulation_steps: int = 4  # Was 2
```

### Slow Training
```python
# Reduce workers
preprocessing_num_workers: int = 4  # Was 8
dataloader_num_workers: int = 2  # Was 4
```

### Dataset Download Fails
```bash
# Pre-download datasets
python -c "
from datasets import load_dataset
load_dataset('naijavoices/naijavoices-dataset', 'hausa-batch-1')
load_dataset('naijavoices/naijavoices-dataset', 'yoruba-batch-1')
load_dataset('naijavoices/naijavoices-dataset', 'igbo-batch-1')
load_dataset('mozilla-foundation/common_voice_17_0', 'ha')
"
```

---

## 📥 After Training

### 1. Download Model
```bash
# On your local server
scp -r root@<pod-ip>:/workspace/outputs/whisper-small-african/final ./models/
```

### 2. Test Model
```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa

# Load model
processor = WhisperProcessor.from_pretrained("./models/final")
model = WhisperForConditionalGeneration.from_pretrained("./models/final")

# Test transcription
audio, sr = librosa.load("test.wav", sr=16000)
inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
generated_ids = model.generate(**inputs)
transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(transcription)
```

### 3. Deploy to Production
See `WHISPER_QLORA_RUNPOD_SETUP.md` for deployment instructions

---

## 📚 Advanced Options

### Use Multiple GPUs
```bash
accelerate launch --multi_gpu --num_processes 2 \
  runpod_whisper_african_qlora.py \
  --output_dir ./outputs/whisper-small-african
```

### Resume from Checkpoint
```bash
python runpod_whisper_african_qlora.py \
  --output_dir ./outputs/whisper-small-african \
  --resume_from_checkpoint ./outputs/whisper-small-african/checkpoint-5000
```

### Custom Language Weights
Edit `runpod_whisper_african_qlora.py`:
```python
languages: List[Dict] = field(default_factory=lambda: [
    {"code": "ha", "name": "Hausa", "weight": 1.5, "hours": 650},  # Increase Hausa
    {"code": "yo", "name": "Yoruba", "weight": 1.0, "hours": 600},
    {"code": "ig", "name": "Igbo", "weight": 1.0, "hours": 630},
    {"code": "tw", "name": "Twi", "weight": 0.5, "hours": 10},  # Increase Twi
])
```

---

## ✅ Checklist

- [ ] RunPod account created with $50 credits
- [ ] Pod deployed with RTX 4090
- [ ] SSH connection working
- [ ] Dependencies installed
- [ ] HuggingFace token configured
- [ ] WandB account set up
- [ ] Training script copied to /workspace
- [ ] Training started
- [ ] Monitoring via WandB
- [ ] Model checkpoint saved
- [ ] Final model downloaded
- [ ] Model tested locally
- [ ] Model deployed to production

---

**Questions?** Check `WHISPER_QLORA_RUNPOD_SETUP.md` for detailed documentation.

**Estimated Total Time**: 5 min setup + 72h training = ~3 days
**Estimated Total Cost**: $31.68 (RTX 4090 @ $0.44/hour × 72h)
**Expected WER**: 15-30% (Hausa, Yoruba, Igbo), 25-35% (Twi, Ewe, Ga)

🎉 **Good luck with training!**

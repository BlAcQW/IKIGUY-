# RunPod Start Instructions

**Date:** 2025-10-23
**Objective:** Start RunPod pod and deploy all services + Whisper training

---

## Option 1: Manual Start via Web Dashboard (RECOMMENDED)

### Step 1: Start the Pod

1. **Login to RunPod:**
   - Go to: https://www.runpod.io/console/pods
   - Login with your account

2. **Find and Start the Pod:**
   - Look for Pod ID: `jzfmzviw26huka-644113c7`
   - Or create a new pod with:
     - GPU: **A40** (46GB VRAM) or **A100** (80GB VRAM)
     - Template: **RunPod PyTorch 2.1.0**
     - Container Disk: **50GB+**
     - Volume: Optional (for persistent storage)

3. **Get Connection Details:**
   - Once started, note the:
     - SSH Port (e.g., 22048)
     - IP Address (e.g., 194.68.245.121)
     - Pod ID

### Step 2: Deploy Everything with One Command

Once the pod is running, from your Hetzner server, run:

```bash
cd /opt/kasaai/apps/tts-deployment/runpod-backup
./deploy_all_runpod.sh
```

**This script will automatically:**
- ✅ Check SSH connectivity
- ✅ Deploy F5-TTS and StyleTTS2 via docker-compose
- ✅ Copy fixed Whisper training script
- ✅ Install all dependencies
- ✅ Set up authentication (HF, WandB)
- ✅ Start Whisper training in background
- ✅ Create SSH tunnels for TTS services
- ✅ Verify all services are running

**Expected time:** 5-10 minutes

---

## Option 2: Manual Step-by-Step

If the automated script fails, follow these manual steps:

### Prerequisites

Export authentication tokens (if you have them):
```bash
export HUGGING_FACE_HUB_TOKEN="your_hf_token_here"
export WANDB_API_KEY="your_wandb_key_here"
```

### Step 1: Connect to RunPod

```bash
ssh -p 22048 root@194.68.245.121
# Or use the new connection details from the web dashboard
```

### Step 2: Deploy TTS Services

```bash
# On RunPod
mkdir -p /workspace/tts-deployment
cd /workspace/tts-deployment

# From Hetzner (new terminal)
cd /opt/kasaai/apps/tts-deployment
scp -P 22048 docker-compose.runpod.yml root@194.68.245.121:/workspace/tts-deployment/docker-compose.yml
scp -P 22048 -r docker/f5tts docker/styletts2 root@194.68.245.121:/workspace/tts-deployment/docker/

# Back on RunPod
cd /workspace/tts-deployment
docker compose up -d f5tts styletts2
docker compose ps
```

### Step 3: Deploy Whisper Training

```bash
# On RunPod
mkdir -p /workspace/whisper-training
cd /workspace/whisper-training

# From Hetzner
cd /opt/kasaai/apps/tts-deployment/runpod-backup
scp -P 22048 runpod_whisper_african_qlora_streaming_fixed.py root@194.68.245.121:/workspace/whisper-training/
scp -P 22048 start_whisper_fixed.sh root@194.68.245.121:/workspace/whisper-training/

# Back on RunPod - Install dependencies
pip install transformers==4.43.0 peft==0.12.0 accelerate==0.34.0
pip install datasets==2.20.0 evaluate==0.4.2 jiwer
pip install librosa soundfile bitsandbytes wandb psutil pandas
```

### Step 4: Authenticate

```bash
# On RunPod
huggingface-cli login --token YOUR_HF_TOKEN
wandb login YOUR_WANDB_KEY  # Optional
```

### Step 5: Start Training

```bash
# On RunPod
cd /workspace/whisper-training
chmod +x start_whisper_fixed.sh
nohup ./start_whisper_fixed.sh > whisper_training.log 2>&1 &

# Check it started
tail -f whisper_training.log
# Press Ctrl+C to exit tail
```

### Step 6: Setup SSH Tunnels (from Hetzner)

```bash
# F5-TTS tunnel
ssh -f -N -L 8002:localhost:8002 -p 22048 root@194.68.245.121

# StyleTTS2 tunnel
ssh -f -N -L 8006:localhost:8006 -p 22048 root@194.68.245.121

# Verify
curl http://localhost:8002/health
curl http://localhost:8006/health
```

---

## Monitoring

### Check Training Progress

```bash
# Via SSH
ssh -p 22048 root@194.68.245.121 'tail -f /workspace/whisper-training/whisper_training.log'

# Via WandB
# Open: https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora
```

### Check GPU Usage

```bash
ssh -p 22048 root@194.68.245.121 'nvidia-smi'
```

### Check TTS Services

```bash
ssh -p 22048 root@194.68.245.121 'cd /workspace/tts-deployment && docker compose ps'
```

### Test Endpoints

```bash
# F5-TTS
curl http://localhost:8002/health
curl https://f5tts.ailabsafrica.com/health

# StyleTTS2
curl http://localhost:8006/health
curl https://styletts.ailabsafrica.com/health
```

---

## Troubleshooting

### Pod Won't Start
- Check RunPod balance (costs ~$0.34/hour for A40)
- Try different GPU if A40 unavailable
- Check region availability

### SSH Connection Refused
- Verify pod is in "Running" state (not "Stopped" or "Terminating")
- Check firewall rules in RunPod dashboard
- Wait 30-60 seconds after pod starts

### Training Crashes Immediately
- Verify you're using the FIXED script: `runpod_whisper_african_qlora_streaming_fixed.py`
- Check it has NO `task_type` in LoraConfig:
  ```bash
  grep -n "task_type" runpod_whisper_african_qlora_streaming_fixed.py
  # Should return no matches in LoraConfig section
  ```

### HuggingFace Authentication Fails
1. Request access: https://huggingface.co/datasets/naijavoices/naijavoices-dataset
2. Create token (write access): https://huggingface.co/settings/tokens
3. Login: `huggingface-cli login --token YOUR_TOKEN`

### TTS Services Won't Start
- Check Docker is running: `docker ps`
- Check logs: `docker compose logs f5tts`
- Verify GPU access in container: `docker compose exec f5tts nvidia-smi`

---

## Expected Timeline

| Task | Time |
|------|------|
| Pod startup | 1-2 minutes |
| Service deployment | 3-5 minutes |
| Training startup | 2-3 minutes |
| **Total Setup** | **~10 minutes** |
| **Training Duration** | **48-72 hours** |

---

## Success Criteria

Deployment is successful when:

- ✅ Pod shows "Running" status in dashboard
- ✅ SSH connection works
- ✅ `docker compose ps` shows f5tts and styletts2 as "Up"
- ✅ Training log shows progress (step 1, 2, 3...)
- ✅ GPU shows ~10-15GB usage in `nvidia-smi`
- ✅ WandB shows live training metrics
- ✅ Local endpoints respond: http://localhost:8002/health
- ✅ Public endpoints respond: https://f5tts.ailabsafrica.com/health

---

## Cost Estimate

- **A40 GPU:** ~$0.34/hour = $8.16/day
- **72 hours training:** ~$24.48
- **With 20% overhead:** ~$30 total

---

## Quick Reference Commands

```bash
# Start everything (automated)
cd /opt/kasaai/apps/tts-deployment/runpod-backup
./deploy_all_runpod.sh

# Monitor training
ssh -p 22048 root@194.68.245.121 'tail -f /workspace/whisper-training/whisper_training.log'

# Check GPU
ssh -p 22048 root@194.68.245.121 'nvidia-smi'

# Check services
ssh -p 22048 root@194.68.245.121 'docker compose -f /workspace/tts-deployment/docker-compose.yml ps'

# Stop pod (when training done)
# Use RunPod web dashboard to stop the pod
```

---

**Created:** 2025-10-23
**Last Updated:** 2025-10-23

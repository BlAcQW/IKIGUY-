# MeloTTS Training on RunPod - Twi-Fante Dataset

Complete guide for training MeloTTS on RunPod for Twi language synthesis.

## 📋 Overview

- **Model**: MeloTTS (VITS-based TTS)
- **Dataset**: Twi-Fante (894,600 samples, 480GB)
- **Recommended GPU**: RTX 4090 24GB
- **Estimated Cost**: $122
- **Estimated Time**: 15 days (360 hours)
- **Optimized Config**: batch_size=32, fp16=true, epochs=2000

## 🚀 Quick Start

### Step 1: Create RunPod Pod

1. Go to [RunPod.io](https://www.runpod.io/)
2. Click "Deploy" → "GPU Pods"
3. Select GPU: **RTX 4090 24GB** ($0.34/hour)
4. Container Image: `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`
5. Disk Space: **500GB** (for dataset + checkpoints)
6. Deploy Pod

### Step 2: Setup Environment

SSH into your RunPod pod:

```bash
# Clone repository
git clone https://github.com/myshell-ai/MeloTTS.git /workspace/MeloTTS

# Install dependencies
cd /workspace/MeloTTS
pip install -e .
pip install wandb tensorboard librosa

# Create directories
mkdir -p /workspace/data /workspace/checkpoints /workspace/logs
```

### Step 3: Upload Data

Upload your Twi-Fante dataset to RunPod:

**Option A: Using RunPod's Web Interface**
- Go to your pod's "Connect" tab
- Use the file upload feature
- Upload to `/workspace/data/twi_full/`

**Option B: Using rsync**
```bash
# From your local machine
rsync -avz -e "ssh -p <POD_SSH_PORT>" \
  /opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/data/twi_full/ \
  root@<POD_IP>:/workspace/data/twi_full/
```

**Option C: Using RunPod Network Storage**
- Create a network volume
- Upload data to volume
- Mount to your pod

### Step 4: Verify Data

```bash
# Check data structure
ls -lh /workspace/data/twi_full/
# Should see: config.json, train.list, val.list, train_wavs/, val_wavs/

# Verify config is optimized
cat /workspace/data/twi_full/config.json | grep -E "batch_size|epochs|fp16_run"
# Should show: batch_size: 32, epochs: 2000, fp16_run: true
```

### Step 5: Start Training

```bash
# Download training scripts
cd /workspace
wget https://raw.githubusercontent.com/YOUR_REPO/train_on_runpod.sh
chmod +x train_on_runpod.sh

# Start training
bash train_on_runpod.sh
```

Or manually:

```bash
cd /workspace/MeloTTS/melo
ln -s /workspace/data/twi_full data/twi_full

python train.py \
  --c data/twi_full/config.json \
  --model twi_melotts
```

### Step 6: Monitor Training

**TensorBoard** (if enabled in script):
```bash
# Access via RunPod's web interface or SSH tunnel
ssh -L 6006:localhost:6006 -p <POD_SSH_PORT> root@<POD_IP>
# Open http://localhost:6006 in browser
```

**Weights & Biases** (optional):
```bash
# Set API key before training
export WANDB_API_KEY="your_api_key"
```

**Check logs**:
```bash
tail -f /workspace/logs/training_*.log
```

**Check GPU usage**:
```bash
watch -n 1 nvidia-smi
```

## 📊 Training Progress

### Expected Timeline

| Epoch | Hours | Days | Checkpoint Size | Validation Loss |
|-------|-------|------|-----------------|-----------------|
| 100   | 18    | 0.75 | ~50MB          | ~2.5           |
| 500   | 90    | 3.75 | ~50MB          | ~1.2           |
| 1000  | 180   | 7.5  | ~50MB          | ~0.8           |
| 1500  | 270   | 11.25| ~50MB          | ~0.6           |
| 2000  | 360   | 15   | ~50MB          | ~0.5           |

### Quality Checkpoints

- **Epoch 500**: Usable quality, intelligible speech
- **Epoch 1000**: Good quality, natural prosody emerging
- **Epoch 1500**: Very good quality, production-ready
- **Epoch 2000**: Best quality, diminishing returns after this

## 💰 Cost Tracking

### RunPod RTX 4090 Pricing: $0.34/hour

| Duration | Hours | Cost   | Quality Level |
|----------|-------|--------|---------------|
| 3 days   | 72    | $24    | Early test    |
| 1 week   | 168   | $57    | Usable        |
| 10 days  | 240   | $82    | Good          |
| 15 days  | 360   | $122   | Excellent     |
| 20 days  | 480   | $163   | Best          |

**Tip**: You can stop training early if validation loss plateaus to save costs.

## 🔍 Troubleshooting

### Out of Memory (OOM) Errors

```bash
# Reduce batch size in config.json
"batch_size": 16  # Instead of 32

# Or enable gradient accumulation
"accumulation_steps": 2
```

### Training Too Slow

```bash
# Verify FP16 is enabled
cat /workspace/data/twi_full/config.json | grep fp16_run
# Should be: "fp16_run": true

# Check GPU utilization
nvidia-smi
# Should show ~90-100% GPU utilization
```

### Data Not Found

```bash
# Verify symbolic link
ls -la /workspace/MeloTTS/melo/data/
# Should show: twi_full -> /workspace/data/twi_full

# Recreate if needed
ln -sf /workspace/data/twi_full /workspace/MeloTTS/melo/data/twi_full
```

### Checkpoint Corruption

```bash
# Training saves checkpoints every eval_interval
# If last checkpoint is corrupted, use previous one
ls -lt /workspace/checkpoints/twi_melotts/
# Load from: G_<epoch>.pth and D_<epoch>.pth
```

## 📦 Saving Checkpoints

### Download Checkpoints

**Option A: RunPod Web Interface**
- Navigate to Files tab
- Download from `/workspace/checkpoints/twi_melotts/`

**Option B: rsync**
```bash
# From local machine
rsync -avz -e "ssh -p <POD_SSH_PORT>" \
  root@<POD_IP>:/workspace/checkpoints/twi_melotts/ \
  ./local_checkpoints/
```

**Option C: Cloud Storage**
```bash
# Upload to S3/GCS during training
pip install awscli  # or google-cloud-storage

# Periodic backup
aws s3 sync /workspace/checkpoints/twi_melotts/ s3://your-bucket/melotts-checkpoints/
```

### Important Files to Save

```
checkpoints/twi_melotts/
├── G_2000.pth          # Generator model (main TTS model)
├── D_2000.pth          # Discriminator (for training only)
├── config.json         # Training configuration
└── vocab.txt           # Phoneme vocabulary
```

**Minimum for inference**: `G_2000.pth` + `config.json` (~50MB total)

## 🧪 Testing Inference

### Quick Test on RunPod

```bash
cd /workspace/MeloTTS/melo

# Test synthesis
python -c "
from melo.api import TTS

# Load your trained model
tts = TTS(
    language='EN',  # Use 'EN' for Twi (uses same phoneme set)
    device='cuda',
    ckpt_path='/workspace/checkpoints/twi_melotts/G_2000.pth',
    config_path='/workspace/data/twi_full/config.json'
)

# Generate speech
output_path = 'test_output.wav'
tts.tts_to_file('Akwaaba. Ɛte sɛn?', speaker='TWI-Speaker', output_path=output_path)
print(f'Generated: {output_path}')
"

# Play audio (if sox installed)
play test_output.wav
```

### Batch Testing

```bash
# Test multiple phrases
cat > test_phrases.txt << 'EOF'
Akwaaba
Ɛte sɛn?
Me din de Kofi
Meda wo ase
Medaase paa
EOF

# Generate all
while read phrase; do
    python inference.py --text "$phrase" --output "outputs/${phrase// /_}.wav"
done < test_phrases.txt
```

## 🚀 Next Steps After Training

### 1. Deploy to RunPod Serverless

Create serverless endpoint for production inference:

```python
# handler.py for RunPod Serverless
import runpod
from melo.api import TTS

# Load model once
tts = TTS(
    language='EN',
    device='cuda',
    ckpt_path='./checkpoints/G_2000.pth',
    config_path='./config.json'
)

def handler(event):
    text = event['input']['text']
    speaker = event['input'].get('speaker', 'TWI-Speaker')

    # Generate audio
    output_path = '/tmp/output.wav'
    tts.tts_to_file(text, speaker=speaker, output_path=output_path)

    # Read audio bytes
    with open(output_path, 'rb') as f:
        audio_bytes = f.read()

    return {
        'audio': audio_bytes.hex(),
        'sample_rate': 44100
    }

runpod.serverless.start({'handler': handler})
```

### 2. Integrate with Your Backend

See `/opt/kasaai/apps/voice-lab/runpod/deployment/` for integration examples.

### 3. Fine-tune Further (Optional)

If quality isn't perfect:
- Train for 500-1000 more epochs
- Adjust learning rate: 0.0001
- Fine-tune on specific phrases/domains

## 📚 Configuration Reference

### Optimized Config (Current)

```json
{
  "train": {
    "batch_size": 32,      // ✅ Optimized for RTX 4090
    "epochs": 2000,        // ✅ Realistic target
    "fp16_run": true,      // ✅ 2x speedup
    "learning_rate": 0.0002, // ✅ Good for batch_size=32
    "eval_interval": 1000,
    "keep_ckpts": 3
  }
}
```

### Alternative Configs

**Faster Training (Lower Quality)**:
```json
{
  "batch_size": 64,
  "epochs": 1000,
  "fp16_run": true
}
```
Cost: ~$60, Time: 7 days

**Highest Quality (Longer)**:
```json
{
  "batch_size": 16,
  "epochs": 3000,
  "fp16_run": true
}
```
Cost: ~$250, Time: 25 days

## 🆘 Support

### Common Issues

1. **Training loss not decreasing**
   - Check learning rate (try 0.0001 instead of 0.0002)
   - Verify data quality
   - Ensure FP16 is working

2. **Generated audio is garbled**
   - Train for more epochs (need at least 500)
   - Check if config.json matches training

3. **Pod keeps timing out**
   - Use RunPod's "Auto-restart" feature
   - Set up checkpoint saving more frequently
   - Consider spot instances with auto-resume

### Getting Help

- RunPod Discord: https://discord.gg/runpod
- MeloTTS Issues: https://github.com/myshell-ai/MeloTTS/issues
- Your team Slack/Discord

## 📈 Monitoring & Optimization

### Key Metrics to Watch

1. **Training Loss**: Should decrease steadily
   - Target: < 1.0 by epoch 1000
   - Target: < 0.5 by epoch 2000

2. **Validation Loss**: Should track training loss
   - If diverging, reduce learning rate

3. **GPU Utilization**: Should be 90-100%
   - If lower, increase batch size or check I/O

4. **Generation Quality**: Test every 100 epochs
   - Listen for naturalness
   - Check pronunciation accuracy

### Cost Optimization Tips

1. **Use Spot Instances**: 40-60% cheaper
   - Enable auto-restart
   - Save checkpoints frequently

2. **Stop Early**: Monitor validation loss
   - If plateaued for 200 epochs, can stop

3. **Pause Overnight**: If on tight budget
   - Save checkpoint
   - Resume next day

4. **Multi-task**: Train multiple models in parallel
   - Use different pods
   - Reduces calendar time

## ✅ Checklist

Before starting training:
- [ ] RunPod pod deployed (RTX 4090, 500GB disk)
- [ ] Data uploaded (480GB, 894k samples)
- [ ] Config verified (batch_size=32, fp16=true)
- [ ] Scripts downloaded and made executable
- [ ] TensorBoard/WandB configured (optional)
- [ ] Checkpoint backup strategy ready

During training:
- [ ] Monitor GPU usage (should be ~95%)
- [ ] Check training loss every 100 epochs
- [ ] Test audio quality every 500 epochs
- [ ] Save checkpoints regularly
- [ ] Track costs

After training:
- [ ] Download final checkpoint
- [ ] Test inference locally
- [ ] Deploy to RunPod Serverless
- [ ] Integrate with backend API
- [ ] Celebrate! 🎉

## 📞 Quick Commands Reference

```bash
# Start training
bash train_on_runpod.sh

# Monitor training
tail -f /workspace/logs/training_*.log

# Check GPU
nvidia-smi

# Test inference
python inference.py --checkpoint /workspace/checkpoints/twi_melotts/G_2000.pth --text "Akwaaba"

# Download checkpoint
scp -P <PORT> root@<IP>:/workspace/checkpoints/twi_melotts/G_2000.pth ./

# Stop gracefully
# Press Ctrl+C once (saves checkpoint before exit)
```

---

**Ready to train?** 🚀

Estimated investment: **$122** for production-quality Twi TTS in **15 days**!

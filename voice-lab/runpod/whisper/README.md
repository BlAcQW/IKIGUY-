# Whisper Small Training on RunPod - Twi-Fante ASR

Complete guide for fine-tuning Whisper Small for Twi speech recognition.

## 📋 Overview

- **Model**: Whisper Small (244M parameters)
- **Dataset**: Twi-Fante (894,600 samples, ~500 hours)
- **Recommended GPU**: RTX 4090 24GB
- **Estimated Cost**: $68
- **Estimated Time**: 8 days (200 hours)
- **Optimized**: FP16, batch_size=16, gradient checkpointing

## 🚀 Quick Start

### Step 1: Deploy RunPod Pod

1. Go to [RunPod.io](https://www.runpod.io/)
2. Select: **RTX 4090 24GB** ($0.34/hour)
3. Container: `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`
4. Disk: **100GB** (model + checkpoints)
5. Deploy

### Step 2: Setup Environment

```bash
# Install dependencies
pip install transformers datasets accelerate evaluate jiwer librosa wandb

# Create directories
mkdir -p /workspace/data/twi_asr /workspace/checkpoints /workspace/logs

# Download training script
cd /workspace
wget https://raw.githubusercontent.com/YOUR_REPO/train_whisper.py
wget https://raw.githubusercontent.com/YOUR_REPO/train_on_runpod.sh
chmod +x train_on_runpod.sh
```

### Step 3: Prepare Data

**Option A: Use Mozilla Common Voice (Automatic)**
```bash
# Script will auto-download Common Voice Twi dataset
# No manual preparation needed!
```

**Option B: Upload Your Custom Dataset**

Your dataset should be in this format:
```
/workspace/data/twi_asr/
├── train/
│   ├── audio_001.wav
│   ├── audio_002.wav
│   └── metadata.csv  # columns: file_name, text
└── validation/
    ├── audio_001.wav
    └── metadata.csv
```

Or use Hugging Face dataset format:
```bash
# Upload dataset to HuggingFace Hub
# Then modify train_whisper.py to load from your dataset
```

### Step 4: Start Training

```bash
# Optional: Set WandB API key for experiment tracking
export WANDB_API_KEY="your_api_key"

# Start training
bash train_on_runpod.sh
```

## 📊 Training Configuration

### Default Settings (Optimized for RTX 4090)

```python
{
    "model": "openai/whisper-small",
    "batch_size": 16,
    "gradient_accumulation_steps": 1,
    "learning_rate": 1e-5,
    "epochs": 10,
    "fp16": True,
    "gradient_checkpointing": True,
    "warmup_steps": 500
}
```

### Memory Usage

| Batch Size | VRAM Usage | Training Speed | Recommendation |
|------------|------------|----------------|----------------|
| 8          | ~10GB      | Slower         | Use if OOM     |
| 16         | ~16GB      | Optimal        | ✅ Recommended |
| 24         | ~22GB      | Faster         | If VRAM allows |
| 32         | ~24GB+     | Fastest        | May OOM        |

## 🔍 Monitoring Training

### TensorBoard

```bash
# Access via SSH tunnel
ssh -L 6006:localhost:6006 -p <PORT> root@<POD_IP>

# Open in browser
http://localhost:6006
```

### Weights & Biases

```bash
# Set API key before training
export WANDB_API_KEY="your_api_key"

# View at wandb.ai
```

### Key Metrics to Watch

1. **Training Loss**: Should decrease steadily
   - Target: < 0.5 by epoch 5
   - Target: < 0.3 by epoch 10

2. **Validation WER (Word Error Rate)**: Lower is better
   - Good: < 30%
   - Excellent: < 15%
   - Best: < 10%

3. **GPU Utilization**: Should be 90-100%

## 💰 Cost Tracking

| Checkpoint | Epoch | Hours | Cost  | Expected WER |
|------------|-------|-------|-------|--------------|
| checkpoint-500  | 1  | 20  | $7   | ~40%        |
| checkpoint-2500 | 5  | 100 | $34  | ~20%        |
| checkpoint-5000 | 10 | 200 | $68  | ~10-15%     |

## 🧪 Testing Inference

### Quick Test

```bash
python test_inference.py \
  --model /workspace/checkpoints/whisper_twi/final_model \
  --audio test_audio.wav
```

### Test Script

```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa

# Load model
model_path = "/workspace/checkpoints/whisper_twi/final_model"
processor = WhisperProcessor.from_pretrained(model_path)
model = WhisperForConditionalGeneration.from_pretrained(model_path)
model.to("cuda")

# Load and process audio
audio, sr = librosa.load("test_audio.wav", sr=16000)
input_features = processor(
    audio,
    sampling_rate=16000,
    return_tensors="pt"
).input_features.to("cuda")

# Generate transcription
predicted_ids = model.generate(input_features)
transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

print(f"Transcription: {transcription}")
```

## 🚀 Convert to Faster-Whisper (4x Faster Inference!)

After training, convert to Faster-Whisper for production:

```bash
# Install CTranslate2
pip install ctranslate2 faster-whisper

# Convert model
ct2-transformers-converter \
  --model /workspace/checkpoints/whisper_twi/final_model \
  --output_dir /workspace/checkpoints/whisper_twi_ct2 \
  --copy_files tokenizer.json \
  --quantization float16

# Test Faster-Whisper
python << 'EOF'
from faster_whisper import WhisperModel

model = WhisperModel(
    "/workspace/checkpoints/whisper_twi_ct2",
    device="cuda",
    compute_type="float16"
)

segments, info = model.transcribe("test_audio.wav", language="tw")

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
EOF
```

### Faster-Whisper Benefits

| Metric | Original Whisper | Faster-Whisper | Improvement |
|--------|------------------|----------------|-------------|
| Inference Speed | 1.0x | 4.0x | 4x faster |
| VRAM Usage | 1GB | 0.5GB | 50% less |
| CPU Offload | No | Yes | Better scaling |
| Batch Processing | Limited | Excellent | 10x throughput |

**Production Recommendation**: Always use Faster-Whisper for deployment!

## 📦 Deployment

### Option 1: RunPod Serverless (Recommended)

See `/opt/kasaai/apps/voice-lab/runpod/deployment/whisper_serverless.py`

### Option 2: Your Own API

```python
from faster_whisper import WhisperModel
from fastapi import FastAPI, File, UploadFile
import io

app = FastAPI()
model = WhisperModel("/path/to/whisper_twi_ct2", device="cuda")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # Save temporarily
    with open("/tmp/audio.wav", "wb") as f:
        f.write(audio_bytes)

    # Transcribe
    segments, info = model.transcribe("/tmp/audio.wav", language="tw")

    # Collect results
    transcription = " ".join([segment.text for segment in segments])

    return {
        "transcription": transcription,
        "language": info.language,
        "language_probability": info.language_probability
    }
```

## 🎯 Advanced: Custom Dataset Format

If you have your own Twi dataset:

```python
# Create dataset script: twi_asr_dataset.py
from datasets import Dataset, Audio
import pandas as pd

# Load your data
df = pd.read_csv("/workspace/data/twi_asr/metadata.csv")
# Columns: file_path, text

# Create dataset
dataset = Dataset.from_dict({
    "audio": df["file_path"].tolist(),
    "text": df["text"].tolist()
})

# Cast audio column
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

# Save
dataset.save_to_disk("/workspace/data/twi_asr_processed")
```

Then modify `train_whisper.py`:
```python
# Replace dataset loading
from datasets import load_from_disk
dataset = load_from_disk("/workspace/data/twi_asr_processed")
```

## 🔧 Troubleshooting

### Out of Memory

```bash
# Reduce batch size
# In train_whisper.py, change:
per_device_train_batch_size = 8  # Instead of 16
gradient_accumulation_steps = 2  # Maintain effective batch size
```

### Training Too Slow

```bash
# Check GPU utilization
nvidia-smi

# Increase dataloader workers
dataloader_num_workers = 8  # Instead of 4

# Verify FP16 is enabled
fp16 = True  # Should be True
```

### Poor WER Results

1. **Train longer**: Try 15-20 epochs
2. **More data**: Add more Twi audio samples
3. **Data quality**: Check transcription accuracy
4. **Learning rate**: Try 5e-6 or 2e-5

### Model Not Learning

1. **Check data**: Verify audio and text alignment
2. **Increase warmup**: Try warmup_steps=1000
3. **Adjust LR**: Try learning_rate=5e-6
4. **Check logs**: Look for errors in data loading

## 📚 Model Comparison

### Whisper Model Sizes

| Model | Parameters | VRAM | Training Time | Cost | WER (Twi) |
|-------|-----------|------|---------------|------|-----------|
| Tiny  | 39M | 4GB | 2 days | $16 | ~30-40% |
| Base  | 74M | 6GB | 4 days | $33 | ~20-30% |
| **Small** | **244M** | **16GB** | **8 days** | **$68** | **~10-15%** |
| Medium | 769M | 24GB | 17 days | $138 | ~5-10% |
| Large | 1.5B | 40GB | 33 days | $267 | ~3-8% |

**Recommendation**: Whisper Small is the sweet spot for low-resource languages!

## ✅ Quality Checklist

Before deploying:
- [ ] WER < 20% on validation set
- [ ] Test on diverse accents/dialects
- [ ] Check punctuation quality
- [ ] Verify proper Twi characters (ɛ, ɔ, etc.)
- [ ] Test with noisy audio
- [ ] Benchmark inference speed
- [ ] Convert to Faster-Whisper
- [ ] Load test API endpoints

## 🎓 Next Steps

1. **Combine with TTS**: Train MeloTTS for complete ASR+TTS pipeline
2. **Fine-tune more**: Add dialect-specific data
3. **Optimize inference**: Use Faster-Whisper with quantization
4. **Deploy**: RunPod Serverless or your infrastructure
5. **Monitor**: Track real-world WER and user feedback

---

**Estimated Total Investment**: $68 for production-ready Twi ASR! 🚀

Combined with MeloTTS ($122), you have full ASR+TTS for **$190**!

# Faster Whisper Medium Fine-Tuning for Twi

## 🎯 Overview

Fine-tune OpenAI's Whisper Medium model on Twi language for high-quality automatic speech recognition (ASR).

## 📁 Files

1. **`006_faster_whisper_medium_twi.py`** - Fine-tuning script
2. **`007_faster_whisper_inference.py`** - Inference script
3. **`README_WHISPER.md`** - This documentation

## 🖥️ Hardware Requirements

**Optimized for your server:**
- ✅ NVIDIA RTX 4000 Ada (20GB VRAM)
- ✅ 62GB RAM
- ✅ 20 CPU cores

## 🚀 Quick Start

### Step 1: Fine-Tune Whisper on Twi

```bash
# Default (optimized settings)
python notebooks/local/006_faster_whisper_medium_twi.py

# With custom parameters
python notebooks/local/006_faster_whisper_medium_twi.py \
    --epochs 10 \
    --batch_size 8 \
    --learning_rate 1e-5
```

**Expected:**
- ⏱️ Training time: ~6-8 hours (10 epochs)
- 💾 VRAM usage: ~16-18 GB
- 📊 Final WER: 5-15% (depending on data quality)

### Step 2: Test Inference

```bash
# Single file transcription
python notebooks/local/007_faster_whisper_inference.py \
    --model models/whisper_medium_twi/production \
    --audio sample_twi_audio.wav

# Batch transcription
python notebooks/local/007_faster_whisper_inference.py \
    --model models/whisper_medium_twi/production \
    --audio_list twi_audio_files.txt \
    --output transcriptions.json
```

## ⚙️ Configuration Options

### Model Selection

| Model | Parameters | VRAM | WER | Speed | Recommendation |
|-------|-----------|------|-----|-------|----------------|
| tiny | 39M | ~2GB | High | Fast | Testing only |
| base | 74M | ~4GB | Medium | Fast | Quick prototyping |
| small | 244M | ~8GB | Good | Medium | Balanced |
| **medium** | **769M** | **~16GB** | **Best** | **Good** | **Recommended** ✅ |
| large | 1.5B | ~20GB | Excellent | Slow | If you have time |

**For your RTX 4000 (20GB):** Use **medium** (default)

### Batch Size Optimization

| Batch Size | VRAM Usage | Speed | Quality | Use Case |
|------------|------------|-------|---------|----------|
| 4 | ~8-10 GB | Slow | Excellent | Conservative |
| 6 | ~12-14 GB | Medium | Excellent | Balanced |
| **8** | **~16-18 GB** | **Good** | **Excellent** | **Recommended** ✅ |
| 12 | ~19-20 GB | Fast | Good | Max throughput |

**Effective batch size = batch_size × gradient_accumulation_steps**
- Default: 8 × 2 = 16 (optimal)

### Learning Rate

| Learning Rate | Effect | When to Use |
|---------------|--------|-------------|
| 5e-6 | Very conservative | Minimal changes to base model |
| **1e-5** | **Balanced** | **Fine-tuning (Recommended)** ✅ |
| 3e-5 | Aggressive | Fast adaptation, risk of overfitting |
| 5e-5 | Very aggressive | Only for very large datasets |

## 📊 Training Details

### What Gets Fine-Tuned

```python
# Whisper Medium Architecture
- Encoder: 24 layers, 1024 hidden size
- Decoder: 24 layers, 1024 hidden size
- Total: 769M parameters

# Fine-tuning strategy:
✅ All parameters are updated (not frozen)
✅ Starting from pre-trained multilingual weights
✅ Adapted to Twi language phonetics
```

### Training Process

1. **Data Loading**
   - Uses 16kHz processed audio
   - Loads from ASR manifests
   - ~118 hours of Twi data

2. **Optimization**
   - FP16 mixed precision (2x faster)
   - Gradient checkpointing (lower memory)
   - AdamW optimizer

3. **Evaluation**
   - WER (Word Error Rate) metric
   - CER (Character Error Rate) metric
   - Evaluated every 500 steps

4. **Early Stopping**
   - Patience: 3 evaluations
   - Prevents overfitting

## 📈 Expected Results

### Performance Metrics

**After fine-tuning:**
- **WER:** 5-15% (excellent for low-resource language)
- **CER:** 3-10%
- **Inference speed:** ~2-3x real-time on GPU

**Comparison with base model:**
- Base Whisper Medium on Twi: ~30-50% WER
- Fine-tuned on Twi: ~5-15% WER
- **Improvement:** 3-5x better accuracy ✨

### Quality Improvements

**What the model learns:**
1. ✅ Twi-specific phonemes (ɛ, ɔ, ã, etc.)
2. ✅ Twi pronunciation patterns
3. ✅ Common Twi words and phrases
4. ✅ Dialect variations (Akuapem, Asante)
5. ✅ Contextual understanding

## 🔧 Advanced Options

### Resume Training

```bash
# Training will auto-resume from last checkpoint
python notebooks/local/006_faster_whisper_medium_twi.py
```

### Custom Dataset Sampling

```bash
# Use only 10,000 samples (for quick testing)
python notebooks/local/006_faster_whisper_medium_twi.py \
    --max_train_samples 10000
```

### Disable FP16 (if issues occur)

```bash
python notebooks/local/006_faster_whisper_medium_twi.py \
    --no_fp16
```

## 📁 Output Structure

```
models/whisper_medium_twi/
├── checkpoint-500/          # Training checkpoints
├── checkpoint-1000/
├── checkpoint-1500/
├── production/              # Production-ready model
│   ├── config.json
│   ├── preprocessor_config.json
│   ├── tokenizer_config.json
│   ├── model.safetensors
│   └── ...
├── trainer_state.json       # Training state
└── all_results.json         # Final metrics
```

## 🎯 Usage Examples

### Example 1: Basic Transcription

```bash
python notebooks/local/007_faster_whisper_inference.py \
    --model models/whisper_medium_twi/production \
    --audio twi_speech.wav
```

**Output:**
```
Transcription: "Wo ho te sɛn? Me ho yɛ pa ara."
```

### Example 2: Batch Processing

```bash
# Create file list
ls data/twi_audio/*.wav > audio_files.txt

# Transcribe all
python notebooks/local/007_faster_whisper_inference.py \
    --model models/whisper_medium_twi/production \
    --audio_list audio_files.txt \
    --output results.json
```

### Example 3: Translation to English

```bash
python notebooks/local/007_faster_whisper_inference.py \
    --model models/whisper_medium_twi/production \
    --audio twi_speech.wav \
    --task translate
```

## 🔍 Monitoring Training

### TensorBoard

```bash
# Start TensorBoard
tensorboard --logdir models/whisper_medium_twi --port 6006

# Open browser
http://localhost:6006
```

**What to monitor:**
- Training loss (should decrease)
- Validation loss (should decrease, not increase)
- WER (should decrease)
- Learning rate schedule

### GPU Monitoring

```bash
# Real-time GPU stats
watch -n 1 nvidia-smi
```

## 🚨 Troubleshooting

### Out of Memory (OOM)

**Solution 1:** Reduce batch size
```bash
python notebooks/local/006_faster_whisper_medium_twi.py --batch_size 4
```

**Solution 2:** Increase gradient accumulation
```python
# Edit script: config.gradient_accumulation_steps = 4
```

### Poor Performance (High WER)

**Solution 1:** Train longer
```bash
python notebooks/local/006_faster_whisper_medium_twi.py --epochs 20
```

**Solution 2:** Lower learning rate
```bash
python notebooks/local/006_faster_whisper_medium_twi.py --learning_rate 5e-6
```

### Slow Training

**Solution 1:** Ensure FP16 is enabled (default)
**Solution 2:** Increase batch size if VRAM allows
**Solution 3:** Check GPU utilization with `nvidia-smi`

## 🏆 Best Practices

### 1. Data Quality
- ✅ Use clean audio (low noise)
- ✅ Verify transcriptions are accurate
- ✅ Ensure consistent audio quality

### 2. Training Strategy
- ✅ Start with default settings
- ✅ Monitor validation metrics
- ✅ Use early stopping
- ✅ Save multiple checkpoints

### 3. Evaluation
- ✅ Test on unseen data
- ✅ Compare with base model
- ✅ Evaluate on different speakers
- ✅ Check dialect performance

### 4. Production Deployment
- ✅ Use production model directory
- ✅ Test inference speed
- ✅ Benchmark on real data
- ✅ Monitor in production

## 📊 Comparison with Base Model

### Test the Difference

```bash
# Base model (not fine-tuned)
python -c "
from transformers import pipeline
pipe = pipeline('automatic-speech-recognition', model='openai/whisper-medium')
result = pipe('twi_audio.wav', generate_kwargs={'language': 'tw'})
print('Base:', result['text'])
"

# Fine-tuned model
python notebooks/local/007_faster_whisper_inference.py \
    --model models/whisper_medium_twi/production \
    --audio twi_audio.wav
```

**Expected improvement:** 3-5x better WER

## 🎯 Next Steps After Fine-Tuning

1. **Quantization** (for faster inference)
   ```bash
   # Convert to ONNX or int8 for production
   ```

2. **Integration**
   ```python
   # Add to core_backend API
   from transformers import pipeline

   transcriber = pipeline(
       'automatic-speech-recognition',
       model='models/whisper_medium_twi/production'
   )
   ```

3. **Continuous Improvement**
   - Collect more Twi data
   - Fine-tune on domain-specific data
   - Ensemble with other models

## 📚 References

- [Whisper Paper](https://arxiv.org/abs/2212.04356)
- [Hugging Face Whisper](https://huggingface.co/docs/transformers/model_doc/whisper)
- [Fine-tuning Guide](https://huggingface.co/blog/fine-tune-whisper)

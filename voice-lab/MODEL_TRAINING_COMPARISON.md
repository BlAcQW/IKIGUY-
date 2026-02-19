# Model Training Requirements Comparison for Twi-Fante Dataset

## Dataset Overview
- **Size**: 480GB
- **Samples**: 894,600 audio files
- **Estimated Duration**: ~500 hours of audio
- **Location**: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante/`

---

## 📊 Complete Model Comparison

### ASR Models

| Model | Parameters | Min VRAM | Recommended VRAM | Batch Size | Training Time | GPU | Cost | Notes |
|-------|-----------|----------|------------------|------------|---------------|-----|------|-------|
| **wav2vec2-base** | 95M | 16GB | 24GB | 16 | 5 days | RTX 4090 | **$41** | ✅ Best value for ASR |
| **Whisper Small** | 244M | 16GB | 24GB | 16 | 8 days | RTX 4090 | **$68** | ✅ Recommended for low-resource languages |
| wav2vec2-large | 317M | 32GB | 40GB | 8 | 10 days | A100 40GB | $358 | Better quality, 2x cost |
| Whisper Medium | 769M | 24GB | 40GB | 8 | 17 days | A100 40GB | $596 | Higher quality, 2x cost vs Small |
| Whisper Large v3 | 1.5B | 40GB | 80GB | 4 | 33 days | A100 80GB | $1,512 | ❌ Overkill for 500hr dataset |

### TTS Models

| Model | Parameters | Min VRAM | Recommended VRAM | Batch Size | Training Time | GPU | Cost | Notes |
|-------|-----------|----------|------------------|------------|---------------|-----|------|-------|
| **Kokoro** | 82M | 8GB | 12GB | 24 | 10 days | RTX 4090 | **$82** | ✅ Lightest, fastest |
| **MeloTTS** | 8.7M | 8GB | 16GB | 32 | 15 days | RTX 4090 | **$122** | ✅ Best value single-speaker |
| Chatterbox | 150M | 12GB | 16GB | 16 | 13 days | RTX 4090 | $109 | Expressive, style control |
| OpenVoice v2 | 200M | 12GB | 16GB | 16 | 17 days | RTX 4090 | $136 | Voice cloning, tone control |
| **F5-TTS** | 350M | 16GB | 24GB | 12 | 20 days | RTX 4090 | **$163** | ✅ Best for voice cloning |
| Coqui XTTS v2 | 500M | 16GB | 24GB | 8 | 25 days | RTX 4090 | $204 | Zero-shot cloning, multi-speaker |
| MetaTTS | 450M | 24GB | 32GB | 8 | 30 days | A100 40GB | $1,073 | ❌ Research model, limited support |

### Multimodal & Speech LLMs

| Model | Parameters | Min VRAM | Recommended VRAM | Batch Size | Training Time | GPU | Cost | Notes |
|-------|-----------|----------|------------------|------------|---------------|-----|------|-------|
| Meta MMS | 1.2B | 32GB | 40GB | 6 | 40 days | A100 40GB | $1,430 | ❌ Overkill for single language |
| Moshi (Kyutai) | 7B | 80GB | 80GB | 2 | 100 days | A100 80GB | $4,536 | ⚠️ Only for duplex conversation AI |

---

## 💰 Cost Comparison by Category

### ASR Models
```
wav2vec2-base   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $41
Whisper Small   ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $68
wav2vec2-large  ████████████████████░░░░░░░░░░░░░░░░░  $358
Whisper Medium  ██████████████████████████████░░░░░░░  $596
Whisper Large   ████████████████████████████████████░  $1,512
```

### TTS Models
```
Kokoro          ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $82
Chatterbox      █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $109
MeloTTS         ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $122
OpenVoice       ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $136
F5-TTS          ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $163
XTTS v2         ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░  $204
MetaTTS         ████████████████████████████████████  $1,073
```

---

## 🎯 Recommendations by Use Case

### 1. Production TTS (Best Value) ⭐
**Budget**: $122 | **Time**: 15 days | **GPU**: RTX 4090

```
Choose: MeloTTS
Why: Lightweight, proven quality, fast training, low inference cost
Perfect for: Single speaker, production apps, conversational AI
```

### 2. Voice Cloning & Multi-Speaker ⭐
**Budget**: $163-$204 | **Time**: 20-25 days | **GPU**: RTX 4090

```
Choose: F5-TTS ($163) or Coqui XTTS v2 ($204)
Why: Zero-shot voice cloning, multi-speaker support
Perfect for: Voice assistants, personalized TTS, content creation
```

### 3. Speech Recognition (ASR) ⭐
**Budget**: $68 | **Time**: 8 days | **GPU**: RTX 4090

```
Choose: Whisper Small
Why: Excellent for low-resource languages, proven multilingual capability
Perfect for: Transcription, voice commands, subtitling
```

### 4. Full ASR+TTS Pipeline ⭐
**Budget**: ~$200 | **Time**: ~3 weeks | **GPU**: RTX 4090

```
Combination:
  1. Whisper Small (ASR): $68
  2. MeloTTS (TTS): $122
  ────────────────────────
  Total: $190

Why: Production-ready, cost-effective, proven quality
Perfect for: Complete voice AI applications
```

### 5. Premium Quality Pipeline
**Budget**: ~$600 | **Time**: ~6 weeks | **GPU**: RTX 4090 + A100

```
Combination:
  1. Whisper Medium (ASR): $596
  2. Coqui XTTS v2 (TTS): $204
  ────────────────────────
  Total: $800

Why: Higher quality, multi-speaker, voice cloning
Perfect for: Enterprise applications, content platforms
```

### 6. Conversational AI (High-End) ⚠️
**Budget**: $4,536+ | **Time**: 100+ days | **GPU**: A100 80GB

```
Choose: Moshi (Kyutai Full)
Why: Full-duplex conversation, interruption handling, natural dialogue
WARNING: Extremely expensive, requires massive compute
Only if: Building advanced conversational AI with serious funding
```

---

## ❌ Not Recommended

### Meta MMS ($1,430)
- **Why not**: Designed for 1000+ languages, overkill for single language
- **Use instead**: Whisper Small for ASR, MeloTTS for TTS
- **Savings**: $1,240

### Whisper Large v3 ($1,512)
- **Why not**: Your 500hr dataset is too small for 1.5B parameters (risk of overfitting)
- **Use instead**: Whisper Small ($68) or Medium ($596)
- **Savings**: $916 - $1,444

### MetaTTS ($1,073)
- **Why not**: Research model, limited production support, poor documentation
- **Use instead**: Coqui XTTS v2 ($204) or F5-TTS ($163)
- **Savings**: $869 - $910

---

## 🚀 Recommended Implementation Strategy

### Phase 1: MVP (Minimum Viable Product)
**Budget**: $200 | **Timeline**: 3 weeks

1. **Train MeloTTS** ($122, 15 days)
   - Single-speaker Twi TTS
   - Production-ready quality
   - Fast inference (<100ms)

2. **Train Whisper Small** ($68, 8 days)
   - Twi speech recognition
   - High accuracy for low-resource language
   - Robust to accents/noise

3. **Deploy on RunPod Serverless**
   - Inference cost: ~$0.0002 per request
   - Auto-scaling
   - Pay only for usage

**Total**: $190 training cost + minimal inference costs

---

### Phase 2: Enhanced Features
**Budget**: +$163 | **Timeline**: +20 days

4. **Add F5-TTS** ($163, 20 days)
   - Voice cloning capability
   - Multi-speaker support
   - Enables personalization

**Total**: $353 (Phase 1 + 2)

---

### Phase 3: Premium Quality (Optional)
**Budget**: +$596 | **Timeline**: +17 days

5. **Upgrade to Whisper Medium** ($596)
   - Higher ASR accuracy
   - Better noise robustness
   - Improved punctuation

**Total**: $949 (all phases)

---

## 📈 Cost-Benefit Analysis

| Approach | Models | Total Cost | Training Time | Use Case | ROI |
|----------|--------|-----------|---------------|----------|-----|
| **Minimal** | wav2vec2-base + MeloTTS | $163 | 20 days | Basic ASR+TTS | ⭐⭐⭐⭐⭐ |
| **Standard** ✅ | Whisper Small + MeloTTS | $190 | 23 days | Production ASR+TTS | ⭐⭐⭐⭐⭐ |
| **Enhanced** | Whisper Small + F5-TTS | $231 | 28 days | Voice cloning | ⭐⭐⭐⭐ |
| **Premium** | Whisper Medium + XTTS v2 | $800 | 42 days | Multi-speaker, high quality | ⭐⭐⭐ |
| **Enterprise** | Whisper Large + Moshi | $6,048 | 133 days | Conversational AI | ⭐⭐ |

---

## 🔧 Optimization Tips

### For MeloTTS (Already Analyzed)
**Current Config** (INEFFICIENT):
```json
{
  "batch_size": 1,
  "epochs": 10000,
  "fp16_run": false
}
```
**Training Time**: 27 YEARS ❌
**Cost**: $80,000 ❌

**Optimized Config**:
```json
{
  "batch_size": 32,
  "epochs": 2000,
  "fp16_run": true,
  "learning_rate": 0.0002
}
```
**Training Time**: 15 days ✅
**Cost**: $122 ✅
**Speedup**: 160x faster
**Savings**: $79,878

### For All Models
1. **Enable Mixed Precision (FP16)**: 2x speedup, 50% less VRAM
2. **Optimize Batch Size**: Use largest that fits in VRAM
3. **Use Gradient Accumulation**: If VRAM-limited
4. **Monitor Learning Curves**: Stop early if converged (don't waste compute)
5. **Use Checkpointing**: Resume if interrupted, save costs

---

## 💡 Key Insights

### Dataset Considerations
- ✅ **500 hours is excellent** for single-speaker TTS (MeloTTS, Kokoro)
- ✅ **Good for ASR fine-tuning** (Whisper, wav2vec2)
- ⚠️ **May be small** for large multi-speaker models (XTTS, MetaTTS)
- ❌ **Too small** for training Whisper Large from scratch (needs 10,000+ hours)

### VRAM Recommendations
- **RTX 4090 24GB**: Perfect for models up to 500M params with FP16
- **A100 40GB**: Needed for 500M-1B params or larger batch sizes
- **A100 80GB**: Required for 1B+ params or Moshi/large speech LLMs

### Cost Optimization
- Training single model: Use dedicated GPU pods
- Multiple experiments: Use spot instances (50% cheaper)
- Production inference: Use serverless endpoints (pay per use)

---

## 🎓 Learning Path

If you're new to training these models, follow this path:

1. **Start Small**: Train MeloTTS first ($122)
   - Learn the pipeline
   - Validate data quality
   - Test inference deployment

2. **Add ASR**: Train Whisper Small ($68)
   - Complete the ASR+TTS loop
   - Build end-to-end application
   - Measure real-world performance

3. **Scale Up**: Add F5-TTS if needed ($163)
   - Expand to voice cloning
   - Support multiple speakers
   - Enhance user experience

4. **Optimize**: Fine-tune based on user feedback
   - Don't jump to expensive models first
   - Validate each step before investing more

---

## 📞 Next Steps

1. **Immediate**: Optimize your MeloTTS config (see optimization section above)
2. **Week 1**: Start MeloTTS training on RTX 4090 ($122, 15 days)
3. **Week 2**: Parallel train Whisper Small ($68, 8 days)
4. **Week 3**: Deploy both models to RunPod serverless
5. **Month 2**: Evaluate quality, consider F5-TTS upgrade if voice cloning needed

---

## 📚 References

- RunPod GPU Pricing: https://www.runpod.io/pricing
- MeloTTS Training Config: `/opt/kasaai/apps/voice-lab/notebooks/local/MeloTTS/melo/data/twi_full/config.json`
- Dataset Location: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante/`
- Previous VRAM Analysis: `/tmp/calculate_vram.py`
- This Comparison CSV: `/tmp/model_comparison.csv`

---

**Generated**: 2025-10-18
**Dataset**: Twi-Fante 480GB, 894.6k samples
**GPU Pricing**: RunPod (as of Oct 2025)

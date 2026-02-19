# Coqui XTTS Fine-Tuning for Twi Language

## 🎯 Fine-Tuning vs Training from Scratch

### Fine-Tuning (What We're Doing) ✅
- **Starts with:** Pre-trained XTTS v2 multilingual model weights
- **Training time:** 20 epochs (~few hours depending on GPU)
- **Data needed:** Works well with our ~118 hours of Twi data
- **Quality:** High quality from the start, improves with Twi-specific patterns
- **Learning rate:** Lower (5e-6) to preserve pre-trained knowledge
- **Result:** Model that speaks Twi with good prosody and naturalness

### Training from Scratch (What We're NOT Doing) ❌
- **Starts with:** Random initialized weights
- **Training time:** 1000+ epochs (~weeks of GPU time)
- **Data needed:** Requires 500+ hours for acceptable quality
- **Quality:** Poor initially, slowly improves over many epochs
- **Learning rate:** Higher (1e-4) to learn from scratch
- **Result:** Unstable and inefficient for our use case

## 📁 Files Created

1. **`010_coqui_xtts_training.py`** - Fine-tuning script
2. **`011_coqui_xtts_inference.py`** - Inference/generation script
3. **`README_COQUI_XTTS.md`** - This file

## 🚀 How to Use

### Step 1: Process Data (Already Running)
```bash
python notebooks/002_process_twi_data_local.py
```

This creates:
- Processed audio at 22.05kHz in `data/processed/twi-akan-fante/processed_audio/tts_22k/`
- Training manifests in `data/processed/twi-akan-fante/model_manifests/`

### Step 2: Fine-Tune XTTS on Twi
```bash
# Basic fine-tuning (20 epochs)
python notebooks/local/010_coqui_xtts_training.py

# With custom parameters
python notebooks/local/010_coqui_xtts_training.py \
    --epochs 20 \
    --batch_size 4 \
    --learning_rate 5e-6

# Faster fine-tuning (freeze encoder, only train decoder)
python notebooks/local/010_coqui_xtts_training.py \
    --freeze_encoder \
    --epochs 15
```

**What happens:**
1. Downloads pre-trained XTTS v2 model (~2GB)
2. Loads your Twi training data
3. Fine-tunes model on Twi for 20 epochs
4. Saves checkpoints every 500 steps
5. Outputs fine-tuned model to `models/coqui_xtts_twi/`

### Step 3: Generate Twi Speech
```bash
# Single text synthesis
python notebooks/local/011_coqui_xtts_inference.py \
    --model models/coqui_xtts_twi/checkpoints/best_model.pth \
    --text "Me ma wo akye" \
    --speaker data/processed/twi-akan-fante/processed_audio/tts_22k/sample_speaker.wav \
    --output output/my_twi_speech.wav

# Batch synthesis from file
python notebooks/local/011_coqui_xtts_inference.py \
    --model models/coqui_xtts_twi/checkpoints/best_model.pth \
    --text_file twi_sentences.txt \
    --speaker reference_voice.wav \
    --output_dir output/tts_batch/
```

## 🎛️ Fine-Tuning Parameters Explained

### Key Parameters

| Parameter | Default | Description | When to Change |
|-----------|---------|-------------|----------------|
| `--epochs` | 20 | Number of fine-tuning passes | Increase if validation loss still decreasing |
| `--batch_size` | 4 | Samples per GPU batch | Decrease if GPU OOM, increase if GPU underutilized |
| `--learning_rate` | 5e-6 | How fast model learns | **Keep low for fine-tuning!** Higher = catastrophic forgetting |
| `--freeze_encoder` | False | Only train decoder | Set True for faster training with less data |

### Why These Values?

**Lower Learning Rate (5e-6):**
- Pre-trained model already knows how to speak
- We're just teaching it Twi-specific patterns
- Too high = model forgets multilingual knowledge

**Fewer Epochs (20 vs 1000):**
- Fine-tuning converges much faster
- Pre-trained model is already good at TTS
- Just adapting to new language

**Smaller Batch Size (4):**
- XTTS is a large model (~2GB)
- Works on consumer GPUs
- Increase to 8 or 16 if you have more VRAM

## 📊 Expected Results

### After Fine-Tuning:
- **Twi pronunciation:** Accurate phonetics
- **Natural prosody:** Good rhythm and intonation
- **Speaker cloning:** Can clone Twi speaker voices
- **Quality:** Similar to base XTTS v2, but for Twi

### Training Metrics:
- **Loss:** Should decrease from ~0.5 to ~0.1
- **Time:** ~3-5 hours on RTX 3090 for 20 epochs
- **Checkpoints:** Saved every 500 steps

## 🔧 Troubleshooting

### GPU Out of Memory
```bash
# Reduce batch size
python notebooks/local/010_coqui_xtts_training.py --batch_size 2

# Or freeze encoder
python notebooks/local/010_coqui_xtts_training.py --freeze_encoder
```

### Training Too Slow
```bash
# Use mixed precision (already enabled by default)
# Or reduce data by sampling
```

### Poor Quality After Fine-Tuning
```bash
# Lower learning rate further
python notebooks/local/010_coqui_xtts_training.py --learning_rate 1e-6

# Or train for more epochs
python notebooks/local/010_coqui_xtts_training.py --epochs 30
```

## 📈 Monitoring Training

Check tensorboard logs:
```bash
tensorboard --logdir models/coqui_xtts_twi/logs
```

Look for:
- **Loss decreasing** ✅
- **Validation loss not increasing** ✅ (no overfitting)
- **Sample quality improving** ✅

## 🎯 Next Steps After Fine-Tuning

1. **Evaluate on test set**
   - Compare with base XTTS v2
   - Measure intelligibility

2. **Test with native speakers**
   - Get feedback on pronunciation
   - Adjust if needed

3. **Export for production**
   - Convert to ONNX or TorchScript
   - Optimize for inference

4. **Integrate with backend**
   - Add to `core_backend` API
   - Deploy as TTS service

## 🔬 Technical Details

### Model Architecture
- **Base:** XTTS v2 (GPT-based TTS)
- **Parameters:** ~450M
- **Languages (base):** 13 multilingual
- **Added:** Twi (fine-tuned)

### Fine-Tuning Process
1. Load pre-trained XTTS v2 checkpoint
2. Initialize optimizer with low LR
3. Train on Twi data with warmup
4. Preserve multilingual capabilities
5. Save best checkpoint

### Dataset Used
- **BibleTTS:** 46,841 samples (118.2 hours)
- **Speakers:** 127 unique
- **Dialects:** Akuapem Twi, Asante Twi
- **Sample rate:** 22.05kHz

## 📚 References

- [Coqui TTS Documentation](https://docs.coqui.ai/en/latest/)
- [XTTS v2 Paper](https://arxiv.org/abs/2311.18293)
- [Fine-Tuning Guide](https://docs.coqui.ai/en/latest/tutorial_for_nervous_beginners.html)

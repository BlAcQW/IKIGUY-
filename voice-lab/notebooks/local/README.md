# Twi/Akan Fine-tuning Scripts

Fine-tuning scripts for 10 voice AI models optimized for RTX 4000 20GB GPU.

## 📋 Created Scripts

**See [STATUS.md](STATUS.md) for detailed implementation status of each script.**

### ASR Models (Speech-to-Text)

1. **008_wav2vec2_twi.py** - Wav2Vec2 ASR ✅ **READY**
   - Pre-trained: facebook/wav2vec2-large-xlsr-53
   - LoRA PEFT for efficient training
   - Full implementation with training loop
   - 16kHz audio, batch_size=4
   - Gradient accumulation: 8 (effective batch=32)

2. **009_moshi_twi.py** - Kyutai Moshi (Audio-to-Audio) ⚠️ **PARTIAL**
   - Real-time speech-to-speech model
   - DeepSpeed ZeRO-2 for memory efficiency
   - Very VRAM intensive, batch_size=1
   - Gradient accumulation: 32
   - Status: Needs training loop completion

### TTS Models (Text-to-Speech)

3. **011_kokoro_tts_twi.py** - Kokoro TTS (Edge) ⚠️ **PARTIAL**
   - Ultra-lightweight (82MB-500MB)
   - Perfect for mobile/edge deployment
   - ONNX format, CPU-friendly
   - 24kHz audio
   - Status: Data prep only, needs training pipeline

4. **012_meta_mms_tts_aka.py** - Meta MMS TTS ⚠️ **PARTIAL**
   - Massively multilingual (1000+ languages)
   - LoRA for efficient fine-tuning
   - 16kHz audio, batch_size=4
   - Status: Model setup only, needs data pipeline

5. **013_f5_tts_twi.py** - F5-TTS 📝 **STUB**
   - Flow-matching diffusion TTS
   - Zero-shot voice cloning
   - Memory intensive, batch_size=2
   - 24kHz audio

6. **014_chattts_twi.py** - ChatTTS 📝 **STUB**
   - Conversational/expressive TTS
   - GPT-like architecture
   - Multi-speaker support
   - 24kHz audio, batch_size=2

7. **015_openvoice_twi.py** - OpenVoice 📝 **STUB**
   - Instant voice cloning (3-5 sec reference)
   - Flexible style control
   - Tone color converter
   - 24kHz audio, batch_size=4, LoRA

8. **017_styletts2_twi.py** - StyleTTS2 📝 **STUB**
   - Human-level naturalness
   - Style diffusion + adversarial training
   - Very high quality
   - 24kHz audio, batch_size=2

9. **018_meta_voice_twi.py** - MetaVoice-1B 📝 **STUB**
   - 1.2B parameter model
   - Emotional prosody control
   - DeepSpeed + LoRA for 20GB GPU
   - 24kHz audio, batch_size=1

10. **019_melo_tts_twi.py** - MeloTTS ✅ **READY**
    - Fast, efficient synthesis
    - Multi-speaker support
    - Full implementation with training loop
    - Easy deployment
    - 22.05kHz audio, batch_size=4, LoRA

## 🎯 Server Resources

All scripts optimized for:
- **GPU:** RTX 4000 (20GB VRAM)
- **RAM:** 62GB
- **CPU:** 20 cores

## 🔧 Optimization Techniques Used

1. **LoRA/PEFT** - Parameter-efficient fine-tuning (Wav2Vec2, MMS, OpenVoice, MeloTTS, MetaVoice)
2. **DeepSpeed ZeRO-2** - Memory-efficient training (Moshi, MetaVoice)
3. **Gradient Accumulation** - Larger effective batch sizes (all models)
4. **Mixed Precision (FP16)** - Faster training, less VRAM (all models)
5. **Gradient Checkpointing** - Trade compute for memory (all models)
6. **Small Batch Sizes** - Fit in 20GB VRAM (adjusted per model)

## 📊 Data Requirements

Scripts expect manifests in:
```
/opt/kasaai/apps/voice-lab/data/processed/twi-akan-fante/model_manifests/
```

Manifest format (CSV):
- `audio_path`: Path to audio file
- `transcript` or `text`: Text transcription
- `duration`: Audio duration in seconds
- `speaker_id`: Speaker identifier
- `language`: Language code (tw)
- `dialect`: Dialect (akuapem_twi, asante_twi, fante)

## 🚀 Usage

### Basic Training
```bash
# ASR
python notebooks/local/008_wav2vec2_twi.py --mode train

# TTS
python notebooks/local/019_melo_tts_twi.py
```

### Inference
```bash
python notebooks/local/008_wav2vec2_twi.py --mode inference
```

## 📈 Training Recommendations

### ✅ Ready to Train Now:
1. **Wav2Vec2** (008) - Proven ASR, complete implementation ⭐ START HERE FOR ASR
2. **MeloTTS** (019) - Fast TTS, complete implementation ⭐ START HERE FOR TTS

### ⚠️ Needs Completion (For Developers):
3. **Meta MMS TTS** (012) - Add data pipeline
4. **Kokoro** (011) - Add ONNX training workflow
5. **Moshi** (009) - Complete training loop

### 📝 Needs Full Implementation:
6. **OpenVoice** (015) - Voice cloning
7. **ChatTTS** (014) - Conversational
8. **F5-TTS** (013) - Zero-shot TTS
9. **StyleTTS2** (017) - State-of-the-art quality
10. **MetaVoice-1B** (018) - Large model

## ⚠️ Important Notes

1. **Manifest Files**: Wait for `002_process_twi_data_local.py` to complete
   - Creates manifests in `model_manifests/` directory
   - Includes model-specific train/val splits

2. **Memory Management**:
   - Monitor VRAM with `nvidia-smi`
   - Reduce batch_size if OOM errors occur
   - Use gradient_accumulation to maintain effective batch size

3. **Training Time**:
   - Wav2Vec2: ~8-12 hours (30 epochs)
   - TTS models: ~12-24 hours (20 epochs)
   - Moshi/MetaVoice: ~24-48 hours (10 epochs)

4. **Checkpoints**:
   - Models save checkpoints every 500-1000 steps
   - Resume training from checkpoints if interrupted
   - Best models saved in `output_dir/`

## 📁 Output Structure

```
/opt/kasaai/apps/voice-lab/models/
├── wav2vec2_twi/
│   ├── config.json
│   ├── pytorch_model.bin
│   ├── vocab.json
│   └── training_args.bin
├── melo_tts_twi/
│   ├── config.json
│   ├── pytorch_model.bin
│   └── training_config.json
└── [other models...]
```

## 🐛 Troubleshooting

### CUDA Out of Memory
- Reduce `batch_size` by half
- Increase `gradient_accumulation_steps` by 2x
- Enable `gradient_checkpointing`
- Use smaller model variants

### Slow Training
- Check `dataloader_num_workers` (default: 4)
- Ensure data is on fast storage (SSD)
- Verify GPU utilization with `nvidia-smi`

### Import Errors
```bash
# Install missing packages
pip install transformers datasets peft deepspeed
pip install librosa soundfile torchaudio
pip install onnxruntime evaluate
```

## 📚 Model Documentation

- **Wav2Vec2**: https://huggingface.co/facebook/wav2vec2-large-xlsr-53
- **Moshi**: https://kyutai.org/moshi
- **Kokoro**: https://github.com/thewh1teagle/kokoro-onnx
- **Meta MMS**: https://huggingface.co/facebook/mms-tts
- **F5-TTS**: https://github.com/SWivid/F5-TTS
- **ChatTTS**: https://github.com/2noise/ChatTTS
- **OpenVoice**: https://github.com/myshell-ai/OpenVoice
- **StyleTTS2**: https://github.com/yl4579/StyleTTS2
- **MetaVoice**: https://huggingface.co/metavoiceio/metavoice-1B-v0.1
- **MeloTTS**: https://github.com/myshell-ai/MeloTTS

## ✅ Next Steps

1. ✅ Data processing complete (128,483 training samples)
2. ✅ Manifest files created for all models
3. ✅ Ready-to-use scripts: Wav2Vec2 (ASR) & MeloTTS (TTS)
4. 🚀 **You can start training now!**

### To Start Training:

**ASR (Speech Recognition):**
```bash
python notebooks/local/008_wav2vec2_twi.py --mode train
```

**TTS (Speech Synthesis):**
```bash
python notebooks/local/019_melo_tts_twi.py --mode train
```

5. Monitor training with TensorBoard:
```bash
tensorboard --logdir /opt/kasaai/apps/voice-lab/models/
```

6. Run inference after training:
```bash
python notebooks/local/008_wav2vec2_twi.py --mode inference
python notebooks/local/019_melo_tts_twi.py --mode inference
```

## 📞 Support

For issues or questions:
- Check logs in model output directories
- Review TensorBoard training curves
- Adjust hyperparameters in script configs
- Consider starting with smaller dataset for testing

---

**Created**: 2025-10-03
**Optimized for**: RTX 4000 20GB GPU
**Dataset**: Twi/Akan/Fante (135k+ samples)

# Fine-tuning Scripts Status

**Last Updated**: 2025-10-03

## ✅ Production Ready (Full Implementation)

These scripts have complete training pipelines and can be run immediately:

### 1. **008_wav2vec2_twi.py** - Wav2Vec2 ASR ✓
- **Status**: COMPLETE
- **Features**:
  - Full training loop with Trainer API
  - LoRA for parameter-efficient training
  - Custom Twi vocabulary
  - CTC loss for ASR
  - WER metrics
  - Inference mode
- **Usage**: `python notebooks/local/008_wav2vec2_twi.py --mode train`
- **Manifests**: ✓ wav2vec2_train.csv, wav2vec2_val.csv
- **Recommended**: YES - Start here for ASR

### 2. **019_melo_tts_twi.py** - MeloTTS ✓
- **Status**: COMPLETE
- **Features**:
  - Full training loop with Trainer API
  - LoRA for VITS architecture
  - Custom Twi tokenizer
  - TTS data collator
  - Inference mode
  - 22.05kHz audio
- **Usage**: `python notebooks/local/019_melo_tts_twi.py --mode train`
- **Manifests**: ✓ melo_tts_train.csv, melo_tts_val.csv
- **Recommended**: YES - Start here for TTS

## ⚠️ Partially Implemented (Needs Completion)

These scripts have some implementation but require additional work:

### 3. **011_kokoro_tts_twi.py** - Kokoro TTS (Edge)
- **Status**: PARTIAL - Data prep only
- **What's Missing**:
  - ONNX model fine-tuning pipeline
  - PyTorch conversion workflow
  - Training loop
- **Current**: Downloads base model, prepares data, saves config
- **Manifests**: ✓ kokoro_tts_train.csv, kokoro_tts_val.csv
- **Notes**: Kokoro uses ONNX format - requires custom training approach

### 4. **012_meta_mms_tts_aka.py** - Meta MMS TTS
- **Status**: PARTIAL - Model loading only
- **What's Missing**:
  - Data preprocessing pipeline
  - Training loop implementation
  - VITS-specific data collator
- **Current**: Loads model with LoRA, sets training args
- **Manifests**: ✓ mms_train.csv, mms_val.csv
- **Fix Applied**: Corrected manifest path from meta_mms_* to mms_*

### 5. **009_moshi_twi.py** - Kyutai Moshi (Audio-to-Audio)
- **Status**: PARTIAL - Blocked by dependency conflicts ⚠️
- **What's Missing**:
  - ❌ `moshi` library (conflicts with numpy/huggingface-hub versions)
  - Complete data preprocessing (stereo audio format needed)
  - Training loop
  - DeepSpeed integration
- **Current**: Config, dataset processor stub
- **Manifests**: ✓ moshi_train.csv, moshi_val.csv
- **Critical Issues**:
  - Dependency conflicts: numpy 2.x vs 1.22.0, huggingface-hub <0.34 vs >=0.34
  - Hardware: 24GB VRAM recommended, we have 20GB
  - Requires separate venv or Docker container
- **See**: `MOSHI_SETUP.md` for detailed installation guide
- **Recommendation**: DEFER until separate environment available

## ✅ Data Pipelines Ready (Need Model Architecture)

These scripts have complete data pipelines, preprocessing, and training setup - only need model architecture integration:

### 6. **013_f5_tts_twi.py** - F5-TTS (Flow Matching) ✓
- **Status**: DATA PIPELINE COMPLETE (296 lines)
- **Features**:
  - ✓ Full dataset loader with audio resampling
  - ✓ F5TTSDatasetProcessor class
  - ✓ F5TTSDataCollator for batch processing
  - ✓ Training configuration optimized for 20GB GPU
  - ✓ Train/inference CLI modes
  - ✓ Configuration saving
- **Manifests**: ✓ f5_tts_train.csv, f5_tts_val.csv
- **Missing**: F5-TTS model architecture from SWivid/F5-TTS
- **Can Run**: Yes (data pipeline test)

### 7. **014_chattts_twi.py** - ChatTTS (Conversational) ✓
- **Status**: DATA PIPELINE COMPLETE (299 lines)
- **Features**:
  - ✓ Full dataset loader
  - ✓ ChatTTSDatasetProcessor class
  - ✓ ChatTTSDataCollator for batch processing
  - ✓ Training configuration for conversational TTS
  - ✓ Train/inference CLI modes
  - ✓ Style and emotion control support
- **Manifests**: ✓ chattts_train.csv, chattts_val.csv
- **Missing**: ChatTTS model from 2Noise/ChatTTS
- **Can Run**: Yes (data pipeline test)

### 8. **015_openvoice_twi.py** - OpenVoice (Voice Cloning) ✓
- **Status**: DATA PIPELINE COMPLETE (244 lines)
- **Features**:
  - ✓ Full dataset loader
  - ✓ OpenVoiceDatasetProcessor class
  - ✓ Audio preprocessing pipeline
  - ✓ Two-stage training config (Base TTS + Tone Color)
  - ✓ Voice cloning support (3-5 sec reference)
  - ✓ Train/inference CLI modes
- **Manifests**: ✓ openvoice_train.csv, openvoice_val.csv
- **Missing**: OpenVoice model from myshell-ai/OpenVoice
- **Can Run**: Yes (data pipeline test)

### 9. **017_styletts2_twi.py** - StyleTTS2 (Style Diffusion)
- **Status**: STUB
- **Lines**: 67
- **Manifests**: ⚠️ Using melo_tts manifests (no styletts2-specific manifest)
- **Fix Applied**: Updated to use generic TTS manifests
- **Notes**: Human-level naturalness, adversarial training

### 10. **018_meta_voice_twi.py** - MetaVoice-1B
- **Status**: STUB
- **Lines**: 73
- **Manifests**: ⚠️ Using melo_tts manifests (no meta_voice-specific manifest)
- **Fix Applied**: Updated to use generic TTS manifests
- **Notes**: 1.2B params, needs DeepSpeed + LoRA

## 📊 Data Processing Status

✅ **COMPLETE** - All manifests generated successfully

- **Total samples**: 128,483 (train) per model
- **Validation samples**: ~6,769 (val) per model
- **Audio processed**:
  - 16kHz (asr_16k) ✓
  - 22.05kHz (tts_22k) ✓
  - 24kHz (tts_24k) ✓
- **Missing manifests**: styletts2, meta_voice (using generic TTS manifests instead)

## 🎯 Recommended Next Steps

### For Users Starting Now:

1. **ASR Training**: Use `008_wav2vec2_twi.py` (READY ✓)
2. **TTS Training**: Use `019_melo_tts_twi.py` (READY ✓)
3. **Model Evaluation**: Use `evaluate_models.py` (READY ✓)
4. **Test Data Pipelines**: Run `013_f5_tts_twi.py`, `014_chattts_twi.py`, `015_openvoice_twi.py` (READY ✓)

### For Developers:

**Priority 1 - Complete Partially Implemented Scripts:**
1. Complete `012_meta_mms_tts_aka.py` - add data pipeline
2. Complete `011_kokoro_tts_twi.py` - add ONNX training workflow
3. Complete `009_moshi_twi.py` - add training loop + DeepSpeed

**Priority 2 - Implement Configuration Stubs:**
4. Implement `015_openvoice_twi.py` - voice cloning is popular
5. Implement `014_chattts_twi.py` - conversational TTS
6. Implement `013_f5_tts_twi.py` - zero-shot TTS

**Priority 3 - Advanced Models:**
7. Implement `017_styletts2_twi.py` - research-grade quality
8. Implement `018_meta_voice_twi.py` - large-scale model

## 🔧 Implementation Template

For completing stub scripts, follow the pattern from `008_wav2vec2_twi.py` or `019_melo_tts_twi.py`:

1. **Data Processing Class** - Load manifests, preprocess audio/text
2. **Model Setup** - Load base model, apply LoRA if needed
3. **Data Collator** - Batch processing with proper padding
4. **Training Loop** - HuggingFace Trainer with proper arguments
5. **Metrics** - Compute relevant metrics (WER for ASR, loss for TTS)
6. **Inference** - Example inference code
7. **CLI** - argparse with train/inference modes

## 📚 Dependencies

### ✅ Installed and Working

All fine-tuning dependencies are installed:
```bash
# Core fine-tuning (INSTALLED ✓)
peft==0.17.1
evaluate==0.4.6
TTS==0.22.0 (Coqui)
deepspeed==0.17.6
tensorboard==2.20.0
bitsandbytes==0.48.1

# Supporting libraries (INSTALLED ✓)
transformers>=4.30.0
datasets>=2.14.0
torch>=2.5.0
torchaudio>=2.0.0
librosa==0.10.1
soundfile==0.13.1
```

### ⚠️ Moshi - NOT INSTALLED (Dependency Conflicts)

**Moshi cannot be installed** due to incompatible package versions:
- Moshi requires: `numpy>=1.26`, `huggingface-hub<0.34`
- Our setup requires: `numpy==1.22.0`, `huggingface-hub>=0.34`

**Solution**: Use separate venv or Docker (see `MOSHI_SETUP.md`)

## 🚨 Known Issues

1. **Moshi (009)**: **CRITICAL** - Dependency conflicts prevent installation in current venv
   - Requires separate venv/Docker (see `MOSHI_SETUP.md`)
   - Below minimum VRAM specs (20GB < 24GB recommended)
2. **StyleTTS2 & MetaVoice**: No dedicated manifests - using generic TTS manifests
3. **Kokoro**: ONNX format requires custom training approach
4. **F5-TTS, ChatTTS**: No reference implementations yet

## 📞 Support

- Check training logs in model output directories
- Review TensorBoard for training curves
- Adjust hyperparameters in script configs
- Start with smaller dataset for testing

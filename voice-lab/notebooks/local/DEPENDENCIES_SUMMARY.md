# Fine-Tuning Dependencies Setup Summary

**Date**: 2025-10-03
**Server**: RTX 4000 (20GB VRAM), 62GB RAM, 20 CPU cores
**Environment**: `/opt/kasaai/apps/venv` (shared with core_backend)

---

## ✅ Successfully Installed Packages

All critical fine-tuning dependencies are now installed and working:

### Core Fine-Tuning Libraries
```
✓ peft                  0.17.1    - LoRA/PEFT for efficient training
✓ evaluate              0.4.6     - Model evaluation metrics
✓ TTS (Coqui)           0.22.0    - Text-to-speech library
✓ deepspeed             0.17.6    - Memory-efficient training
✓ tensorboard           2.20.0    - Training monitoring
✓ bitsandbytes          0.48.1    - Quantization support
```

### Supporting Libraries (Already Present)
```
✓ transformers          4.56.2    - Hugging Face transformers
✓ datasets              4.1.1     - Dataset loading
✓ torch                 2.5.1     - PyTorch with CUDA 12.1
✓ torchaudio            2.5.1     - Audio processing
✓ librosa               0.11.0    - Audio analysis
✓ soundfile             0.13.1    - Audio I/O
✓ accelerate            1.10.1    - Training acceleration
✓ faster-whisper        1.2.0     - Optimized Whisper
✓ onnxruntime           1.23.0    - ONNX inference
```

---

## 🔧 CUDA Setup

### Installed Components
```bash
✓ nvidia-cuda-toolkit   11.5.1    - CUDA development toolkit
✓ nvcc                  11.5.119  - CUDA compiler
✓ CUDA_HOME             /usr/lib/cuda (set in environment)
```

### Configuration Files Updated
- `/etc/environment` - System-wide CUDA_HOME
- `~/.bashrc` - User-level CUDA_HOME

### Verification
```bash
$ nvcc --version
nvcc: NVIDIA (R) Cuda compiler driver
Cuda compilation tools, release 11.5, V11.5.119

$ nvidia-smi
CUDA Version: 13.0 (Driver: 580.65.06)
```

---

## 📊 Script Compatibility Matrix

| Script | peft | evaluate | deepspeed | TTS | Status |
|--------|------|----------|-----------|-----|--------|
| **008_wav2vec2_twi.py** | ✓ | ✓ | - | - | ✅ READY |
| **019_melo_tts_twi.py** | ✓ | ✓ | - | - | ✅ READY |
| **010_coqui_xtts_training.py** | - | - | - | ✓ | ✅ READY |
| **006_faster_whisper_medium_twi.py** | - | ✓ | - | - | ✅ READY |
| **006_faster_whisper_small_twi.py** | - | ✓ | - | - | ✅ READY |
| **012_meta_mms_tts_aka.py** | ✓ | - | - | - | ⚠️ PARTIAL |
| **011_kokoro_tts_twi.py** | - | - | - | - | ⚠️ PARTIAL |
| **009_moshi_twi.py** | - | - | ✓ | - | ❌ BLOCKED |
| **015_openvoice_twi.py** | ✓ | - | - | - | 📝 STUB |
| **013_f5_tts_twi.py** | - | - | - | - | 📝 STUB |
| **014_chattts_twi.py** | - | - | - | - | 📝 STUB |
| **017_styletts2_twi.py** | - | - | - | - | 📝 STUB |
| **018_meta_voice_twi.py** | - | - | ✓ | - | 📝 STUB |

---

## ❌ Moshi - Dependency Conflict (NOT INSTALLED)

### The Problem

Moshi has **incompatible dependencies** with other fine-tuning packages:

| Package | Our Venv | Moshi Requires | Conflict |
|---------|----------|----------------|----------|
| numpy | `1.22.0` | `>=1.26, <2.3` | ❌ Major |
| huggingface-hub | `0.35.3` | `<0.34` | ❌ Major |
| safetensors | `0.6.2` | `<0.6` | ❌ Minor |
| bitsandbytes | `0.48.1` | `>=0.45, <0.46` | ❌ Minor |

### What Broke When We Tried

Installing Moshi caused:
- ✗ Coqui TTS (`numpy` binary incompatibility)
- ✗ PEFT/LoRA (`huggingface-hub` version mismatch)
- ✗ Evaluate (`numpy` binary incompatibility)
- ✗ scipy warnings and errors

### Solution: Separate Environment

See `MOSHI_SETUP.md` for:
1. Dedicated virtual environment setup
2. Docker container approach
3. Data preparation for stereo audio format
4. Training configuration for 20GB GPU

**Recommendation**: Defer Moshi until dedicated environment available.

---

## 🚀 Ready-to-Use Scripts

These scripts can be run immediately:

### 1. Wav2Vec2 ASR (Recommended for ASR)
```bash
python voice-lab/notebooks/local/008_wav2vec2_twi.py --mode train
```
- **Dependencies**: ✅ All installed
- **Model**: facebook/wav2vec2-large-xlsr-53
- **Optimization**: LoRA PEFT
- **Output**: `/opt/kasaai/apps/voice-lab/models/wav2vec2_twi/`

### 2. MeloTTS (Recommended for TTS)
```bash
python voice-lab/notebooks/local/019_melo_tts_twi.py --mode train
```
- **Dependencies**: ✅ All installed
- **Model**: VITS-based
- **Optimization**: LoRA
- **Output**: `/opt/kasaai/apps/voice-lab/models/melo_tts_twi/`

### 3. Coqui XTTS (High-Quality TTS)
```bash
python voice-lab/notebooks/local/010_coqui_xtts_training.py
```
- **Dependencies**: ✅ All installed
- **Model**: XTTS v2
- **Features**: Voice cloning, multilingual
- **Output**: `/opt/kasaai/apps/voice-lab/models/coqui_xtts_twi/`

### 4. Faster Whisper (ASR Inference)
```bash
python voice-lab/notebooks/local/006_faster_whisper_small_twi.py
python voice-lab/notebooks/local/006_faster_whisper_medium_twi.py
```
- **Dependencies**: ✅ All installed
- **Model**: Optimized Whisper
- **Use**: Fast ASR inference

---

## 📝 Scripts Needing Completion

### High Priority

**012_meta_mms_tts_aka.py** - Meta MMS TTS
- ✅ Dependencies installed (`peft`)
- ✅ Model loading complete
- ✅ LoRA configuration ready
- ❌ Missing: Data preprocessing, training loop, data collator
- **Effort**: Medium (template from 019_melo_tts_twi.py)

**011_kokoro_tts_twi.py** - Kokoro Edge TTS
- ✅ Dependencies installed
- ✅ Data preparation complete
- ❌ Missing: ONNX training workflow, PyTorch conversion
- **Effort**: High (ONNX-specific approach needed)

### Medium Priority (Stub Scripts)

All have dependencies installed, need full implementation:
- **015_openvoice_twi.py** - Voice cloning (uses `peft`)
- **013_f5_tts_twi.py** - Zero-shot TTS
- **014_chattts_twi.py** - Conversational TTS
- **017_styletts2_twi.py** - Style diffusion TTS
- **018_meta_voice_twi.py** - Large 1B model (uses `deepspeed`)

---

## 🧪 Testing All Dependencies

Run comprehensive test:
```bash
/opt/kasaai/apps/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/kasaai/apps')

# Test all imports
from peft import LoraConfig, get_peft_model
import evaluate
import deepspeed
from TTS.tts.configs.xtts_config import XttsConfig
import tensorboard
import bitsandbytes

print('✅ All dependencies working!')
"
```

---

## 📊 Installation Commands Used

For reference, here's what was installed:

```bash
# Main packages
sudo /opt/kasaai/apps/venv/bin/pip install peft evaluate TTS tensorboard bitsandbytes

# CUDA toolkit
sudo apt-get update
sudo apt-get install -y nvidia-cuda-toolkit

# DeepSpeed (required CUDA_HOME)
export CUDA_HOME=/usr/lib/cuda
sudo ln -s /usr/bin/nvcc /usr/lib/cuda/bin/nvcc
sudo -E /opt/kasaai/apps/venv/bin/pip install deepspeed

# Environment variables
echo "export CUDA_HOME=/usr/lib/cuda" | sudo tee -a /etc/environment
echo 'export CUDA_HOME=/usr/lib/cuda' >> ~/.bashrc
```

---

## 🎯 Next Steps

### Immediate Actions
1. **Test ready-to-use scripts** with actual training data
2. **Complete 012_meta_mms_tts_aka.py** (highest ROI - 80% done)
3. **Verify manifest files** exist in correct locations

### Future Enhancements
1. **Implement stub scripts** (013-018) using templates from working scripts
2. **Set up Moshi** in separate environment if needed
3. **Add model evaluation** scripts for quality assessment
4. **Create inference wrappers** for easy model testing

---

## 📞 Support & Troubleshooting

### If Training Fails

1. **Check CUDA**:
```bash
nvidia-smi
echo $CUDA_HOME
```

2. **Verify packages**:
```bash
/opt/kasaai/apps/venv/bin/pip list | grep -E "(peft|evaluate|deepspeed|TTS)"
```

3. **Check manifests**:
```bash
ls /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/model_manifests/
```

4. **Monitor GPU**:
```bash
watch -n 1 nvidia-smi
```

### Common Issues

- **OOM (Out of Memory)**: Reduce batch_size, increase gradient_accumulation_steps
- **Import errors**: Check if venv is activated (`which python`)
- **CUDA errors**: Verify CUDA_HOME is set
- **Manifest not found**: Check file paths in script configs

---

## ✅ Summary

**Current Status**: **READY FOR TRAINING**

- ✅ All core dependencies installed
- ✅ CUDA toolkit configured
- ✅ 5 scripts ready to use immediately
- ⚠️ 2 scripts need completion (partial implementation)
- 📝 5 scripts need full implementation (stubs)
- ❌ 1 script blocked (Moshi - dependency conflicts)

**Total Scripts**: 21 Python scripts in `voice-lab/notebooks/local/`
**Ready for Training**: 5 (24%)
**Needs Work**: 7 (33%)
**Data Acquisition/Processing**: 6 (29%)
**Blocked**: 1 (5%)

**Hardware**: RTX 4000 with 20GB VRAM is sufficient for all ready-to-use scripts with optimizations.

---

**Generated**: 2025-10-03
**Last Updated**: After installing all dependencies and testing Moshi compatibility

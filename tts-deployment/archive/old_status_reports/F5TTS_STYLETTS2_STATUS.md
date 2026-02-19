# F5-TTS and StyleTTS2 Deployment Status

**Date:** 2025-10-20
**Status:** ✅ **FULLY OPERATIONAL - 100% Tests Passed**

---

## 🎉 Summary

Both **F5-TTS** and **StyleTTS2** have been successfully deployed on RunPod GPU and are fully operational with complete voice cloning capabilities.

### Services Status

| Service | Status | Model | Deployment | SSL | Test Results |
|---------|--------|-------|------------|-----|--------------|
| **F5-TTS** | ✅ Online | F5TTS_v1_Base (~700MB) | RunPod A40 (48GB) | ✅ Valid until 2026-01-18 | ✅ 100% Pass |
| **StyleTTS2** | ✅ Online | StyleTTS2-LibriTTS (~736MB) | RunPod A40 (48GB) | ✅ Valid until 2026-01-18 | ✅ 100% Pass |

---

## 📊 Service Details

### F5-TTS (Flow-Matching TTS)
- **URL:** https://f5tts.ailabsafrica.com
- **Version:** 1.0.0
- **Model:** F5TTS_v1_Base
- **Features:**
  - Voice cloning with reference audio
  - Auto-transcription of reference audio
  - Multi-language support (en/zh/ja/ko)
  - Adjustable speed (0.5-2.0x)
  - Configurable classifier-free guidance (CFG)
  - NFE steps for quality control (16=fast, 32=balanced, 64=high quality)
  - Remove silence option
  - Reproducible results with seed control
- **Sample Rate:** 24kHz
- **GPU Memory Usage:** ~0.68 GB
- **Inference Speed:** ~2 seconds for typical sentences

**Endpoints:**
- `POST /synthesize_with_reference` - Main synthesis endpoint
- `POST /transcribe` - Audio transcription
- `GET /health` - Health check
- `GET /languages` - Supported languages
- `GET /gpu_stats` - GPU statistics
- `GET /` - Service info

### StyleTTS2 (Style Diffusion TTS)
- **URL:** https://styletts.ailabsafrica.com
- **Version:** 2.0.0
- **Model:** StyleTTS2-LibriTTS
- **Features:**
  - High-quality expressive TTS with style transfer
  - Voice cloning with reference audio
  - Timbre control (alpha parameter)
  - Prosody control (beta parameter)
  - Diffusion steps for quality control (5=fast, 10=balanced, 20=high quality)
  - Style embedding scale adjustment
  - Human-level TTS synthesis quality
- **Sample Rate:** 24kHz
- **GPU Memory Usage:** ~0.72-0.84 GB
- **Inference Speed:** ~1-3 seconds for typical sentences

**Endpoints:**
- `POST /synthesize_with_reference` - Main synthesis with style transfer
- `GET /health` - Health check
- `GET /languages` - Supported languages
- `GET /gpu_stats` - GPU statistics
- `GET /` - Service info

---

## 🏗️ Architecture

### Deployment Setup
```
┌─────────────────────────────────────────────┐
│  Local Server (148.251.0.46)               │
│  ┌──────────────────────────────────────┐  │
│  │  Nginx Reverse Proxy (SSL/TLS)      │  │
│  │  - f5tts.ailabsafrica.com          │  │
│  │  - styletts.ailabsafrica.com       │  │
│  └──────────────────────────────────────┘  │
│               │                             │
│               ▼                             │
│  ┌──────────────────────────────────────┐  │
│  │  SSH Tunnels (Port Forwarding)       │  │
│  │  - Port 8002 → RunPod:8002          │  │
│  │  - Port 8006 → RunPod:8006          │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                │
                │ SSH Tunnel
                ▼
┌─────────────────────────────────────────────┐
│  RunPod GPU (194.68.245.121:22048)         │
│  ┌──────────────────────────────────────┐  │
│  │  NVIDIA A40 GPU (46GB VRAM)         │  │
│  │  ┌──────────────────────────────┐   │  │
│  │  │  F5-TTS (Port 8002)         │   │  │
│  │  │  - FastAPI Server           │   │  │
│  │  │  - F5TTS v1 Base Model      │   │  │
│  │  │  - Vocos Vocoder            │   │  │
│  │  │  - WhisperX ASR             │   │  │
│  │  └──────────────────────────────┘   │  │
│  │  ┌──────────────────────────────┐   │  │
│  │  │  StyleTTS2 (Port 8006)      │   │  │
│  │  │  - FastAPI Server           │   │  │
│  │  │  - StyleTTS2 LibriTTS Model │   │  │
│  │  │  - PLBERT                   │   │  │
│  │  │  - ASR Model                │   │  │
│  │  │  - F0 Predictor             │   │  │
│  │  │  - Diffusion Sampler        │   │  │
│  │  └──────────────────────────────┘   │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## ✅ Test Results

### Comprehensive Test Suite
**Test Script:** `/opt/kasaai/apps/tts-deployment/test_tts_services.py`

**Results (2025-10-20):**
```
F5-TTS:
   Health: ✅ PASS
   Info: ✅ PASS
   Synthesis: 2/2 passed

StyleTTS2:
   Health: ✅ PASS
   Info: ✅ PASS
   Synthesis: 2/2 passed

Overall: 8/8 tests passed (100.0%)
```

### Sample Synthesis Performance

**Test Configuration:**
- Text: "Hello! This is a test of the text to speech system. The quality should be very high and natural sounding."
- Reference Audio: 8-second clips of Archbishop Duncan-Williams
- Sample Rate: 24kHz

**F5-TTS Performance:**
- Synthesis Time: 1.8-2.5 seconds
- Output Size: ~320-400 KB
- NFE Steps: 32 (balanced quality)
- CFG Strength: 2.0

**StyleTTS2 Performance:**
- Synthesis Time: 1.3-2.8 seconds
- Output Size: ~365-400 KB
- Audio Duration: 7.6-8.4 seconds
- Diffusion Steps: 10 (balanced quality)

---

## 🚀 Implementation Details

### F5-TTS Implementation
**File:** `/workspace/tts-deployment/f5tts/F5-TTS/app.py` (on RunPod)

**Key Features Implemented:**
1. **Model Loading:**
   - F5TTS_v1_Base from HuggingFace (SWivid/F5-TTS)
   - Automatic model download on first run
   - Vocos mel-24khz vocoder

2. **Voice Cloning Pipeline:**
   - Reference audio upload
   - Automatic transcription with ASR
   - Style extraction from reference
   - Flow-matching inference
   - Audio generation at 24kHz

3. **API Parameters:**
   - `text`: Text to synthesize
   - `reference_audio`: Reference WAV/MP3/FLAC file
   - `language`: Language code (en/zh/ja/ko)
   - `speed`: Speech speed multiplier (0.5-2.0)
   - `cfg_strength`: Classifier-free guidance (1.0-5.0)
   - `nfe_step`: Quality control (16/32/64)
   - `remove_silence`: Boolean flag
   - `seed`: Optional random seed

### StyleTTS2 Implementation
**File:** `/workspace/tts-deployment/styletts2/StyleTTS2/app.py` (on RunPod)

**Key Features Implemented:**
1. **Model Loading:**
   - StyleTTS2-LibriTTS model from HuggingFace (yl4579/StyleTTS2-LibriTTS)
   - PLBERT language model
   - ASR model for text alignment
   - F0 pitch predictor
   - Diffusion sampler with ADPM2 and Karras schedule

2. **Style Transfer Pipeline:**
   - Reference audio processing
   - Mel spectrogram extraction
   - Style embedding computation (style + predictor encoders)
   - Text phonemization (espeak-ng backend)
   - BERT duration prediction
   - Diffusion-based style generation
   - Timbre and prosody blending
   - HiFiGAN decoding

3. **API Parameters:**
   - `text`: Text to synthesize
   - `reference_audio`: Reference audio file
   - `alpha`: Timbre control (0-1, lower = more like reference)
   - `beta`: Prosody control (0-1, lower = more like reference)
   - `diffusion_steps`: Quality (5/10/20)
   - `embedding_scale`: Scale factor (0.5-2.0)

### Dependencies Installed
**F5-TTS:**
- torch, torchaudio
- f5_tts (from official repo)
- fastapi, uvicorn, pydantic
- soundfile

**StyleTTS2:**
- torch, torchaudio, librosa
- phonemizer (espeak-ng backend)
- nltk (punkt_tab tokenizer)
- munch, yaml
- fastapi, uvicorn, pydantic
- soundfile

---

## 📝 Usage Examples

### F5-TTS Example (Python)
```python
import requests

url = "https://f5tts.ailabsafrica.com/synthesize_with_reference"

with open("reference_audio.wav", "rb") as f:
    files = {"reference_audio": f}
    data = {
        "text": "Hello, this is a test of F5-TTS voice cloning.",
        "language": "en",
        "speed": 1.0,
        "cfg_strength": 2.0,
        "nfe_step": 32
    }

    response = requests.post(url, files=files, data=data, verify=False)

    with open("output.wav", "wb") as out:
        out.write(response.content)
```

### StyleTTS2 Example (Python)
```python
import requests

url = "https://styletts.ailabsafrica.com/synthesize_with_reference"

with open("reference_audio.wav", "rb") as f:
    files = {"reference_audio": f}
    data = {
        "text": "Hello, this is a test of StyleTTS2 voice cloning.",
        "alpha": 0.3,  # Lower = more like reference timbre
        "beta": 0.7,   # Lower = more like reference prosody
        "diffusion_steps": 10
    }

    response = requests.post(url, files=files, data=data, verify=False)

    with open("output.wav", "wb") as out:
        out.write(response.content)
```

### cURL Examples
```bash
# F5-TTS
curl -X POST "https://f5tts.ailabsafrica.com/synthesize_with_reference" \
  -F "reference_audio=@reference.wav" \
  -F "text=Hello world!" \
  -F "language=en" \
  -F "speed=1.0" \
  -F "cfg_strength=2.0" \
  -F "nfe_step=32" \
  --output output.wav

# StyleTTS2
curl -X POST "https://styletts.ailabsafrica.com/synthesize_with_reference" \
  -F "reference_audio=@reference.wav" \
  -F "text=Hello world!" \
  -F "alpha=0.3" \
  -F "beta=0.7" \
  -F "diffusion_steps=10" \
  --output output.wav
```

---

## 🔧 Management Commands

### Check Service Health
```bash
# F5-TTS
curl -s https://f5tts.ailabsafrica.com/health | python3 -m json.tool

# StyleTTS2
curl -s https://styletts.ailabsafrica.com/health | python3 -m json.tool
```

### RunPod Service Management
```bash
# SSH to RunPod
ssh -p 22048 root@194.68.245.121

# Check tmux sessions
tmux ls

# Attach to F5-TTS session
tmux attach -t f5tts

# Attach to StyleTTS2 session
tmux attach -t styletts2

# Restart all services
cd /workspace/tts-deployment && ./start_all.sh

# Check logs
tail -f /workspace/tts-deployment/logs/f5tts.log
tail -f /workspace/tts-deployment/logs/styletts2.log
```

### SSH Tunnel Management (Local Server)
```bash
# Check tunnel status
ps aux | grep 'ssh.*8002\|ssh.*8006'

# Restart tunnels (if needed)
killall -9 ssh  # Kill existing tunnels
# Then re-establish (done automatically on system restart)
```

---

## 🔍 Monitoring

### GPU Usage
```bash
# On RunPod
ssh -p 22048 root@194.68.245.121 "nvidia-smi"

# Check via API
curl -s https://f5tts.ailabsafrica.com/gpu_stats
curl -s https://styletts.ailabsafrica.com/gpu_stats
```

### Service Logs
```bash
# F5-TTS logs
ssh -p 22048 root@194.68.245.121 "tail -100 /workspace/tts-deployment/logs/f5tts.log"

# StyleTTS2 logs
ssh -p 22048 root@194.68.245.121 "tail -100 /workspace/tts-deployment/logs/styletts2.log"
```

---

## 🐛 Known Issues and Solutions

### Issue 1: Reference Audio Too Large (>100MB)
**Solution:** Create 8-second reference clips:
```bash
ffmpeg -i long_audio.wav -ss 0 -t 8 -ar 24000 reference.wav
```

### Issue 2: NLTK punkt_tab Missing
**Solution:** (Already fixed)
```bash
python -c 'import nltk; nltk.download("punkt_tab")'
```

### Issue 3: Port Already in Use
**Solution:** Kill existing process:
```bash
tmux kill-session -t f5tts
tmux kill-session -t styletts2
```

---

## 📚 Additional Resources

### Model Sources
- **F5-TTS:** https://github.com/SWivid/F5-TTS
- **F5-TTS Models:** https://huggingface.co/SWivid/F5-TTS
- **StyleTTS2:** https://github.com/yl4579/StyleTTS2
- **StyleTTS2 Models:** https://huggingface.co/yl4579/StyleTTS2-LibriTTS

### Documentation
- **F5-TTS Paper:** Flow Matching for Text-to-Speech
- **StyleTTS2 Paper:** https://arxiv.org/abs/2306.07691
- **Demo Samples:** https://styletts2.github.io/

---

## ✅ Next Steps

1. **Integration with Core Backend:**
   - Add TTS provider endpoints to `@apps/core_backend/`
   - Implement service selection logic
   - Add caching for frequently used voices

2. **Performance Optimization:**
   - Implement request queuing for multiple concurrent requests
   - Add response caching for identical requests
   - Consider batch processing for multiple texts

3. **Monitoring:**
   - Set up Prometheus metrics
   - Add Grafana dashboards
   - Configure alerting for service downtime

4. **Voice Library:**
   - Create reference voice library
   - Implement voice management API
   - Add voice preview functionality

---

**Deployment Completed:** 2025-10-20
**Tested By:** Claude Code
**Status:** ✅ Production Ready

# RVC Voice Conversion Service

**Version:** 1.0.0
**Status:** Production
**Last Updated:** November 8, 2025

---

## Overview

The RVC (Retrieval-based Voice Conversion) service provides high-quality voice conversion capabilities, allowing users to transform audio using trained voice models. Built on the VITS framework with HiFi-GAN vocoder, RVC enables real-time voice conversion with excellent quality.

### Key Features

- ✅ **Voice Conversion** - Transform voice characteristics while preserving content
- ✅ **Multiple Pitch Extraction Methods** - RMVPE, Harvest, PM, FCPE, CREPE
- ✅ **Index-based Retrieval** - High-quality voice feature matching
- ✅ **GPU Acceleration** - NVIDIA A40 (44GB VRAM) on RunPod
- ✅ **FastAPI REST API** - Easy integration with any application
- ✅ **Real-time Processing** - Suitable for live applications

---

## Architecture

### VITS Framework
- **Variational Inference with adversarial learning** for high-quality synthesis
- **HiFi-GAN** vocoder for natural audio generation
- **ContentVec** for voice feature extraction
- **HuBERT** base model for speech representation (181MB)

### Components

```
Client Application
    ↓
RVC FastAPI (Port 8017)
    ↓
VITS Model + HiFi-GAN
    ├── ContentVec Feature Extractor
    ├── HuBERT Speech Representation
    ├── RMVPE Pitch Extractor
    └── Index-based Retrieval
    ↓
Converted Audio Output
```

---

## Deployment

### RunPod GPU Cloud
**Endpoint:** `https://rvc.ailabsafrica.com`
**Port:** 8017
**GPU:** NVIDIA A40 (44.43GB VRAM)
**Location:** `/workspace/rvc-webui/` on RunPod
**Python:** 3.10 (dedicated venv)

### Dependencies
- **PyTorch:** 2.1.0 with CUDA 12.1
- **fairseq:** 0.12.2 (requires Python ≤3.10)
- **gradio:** 3.34.0
- **librosa:** 0.9.1
- **FastAPI** + **uvicorn** for API server

### Models Downloaded (3.2GB total)
- HuBERT base model (181MB)
- RMVPE model (173MB)
- Pretrained G/D models
- UVR5 weights for vocal separation

---

## API Reference

### Base URL
```
https://rvc.ailabsafrica.com
```

### Health Check
**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "device": "cuda:0",
  "current_model": null,
  "timestamp": 1762625858.2960699
}
```

---

### List Available Models
**GET** `/models`

**Response:**
```json
{
  "models": [
    {
      "name": "my_model",
      "path": "logs/my_model/model.pth",
      "size_mb": 54.2
    }
  ]
}
```

**Note:** Models should be placed in `/workspace/rvc-webui/logs/` directory.

---

### Convert Voice
**POST** `/convert`

**Request (multipart/form-data):**
```
audio: <binary audio file>
model_path: logs/my_model/model.pth
pitch_shift: 0
index_rate: 0.75
filter_radius: 3
rms_mix_rate: 0.25
protect: 0.33
f0_method: rmvpe
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `audio` | file | Yes | - | Audio file to convert (WAV format) |
| `model_path` | string | Yes | - | Path to RVC model (relative to RVC directory) |
| `pitch_shift` | integer | No | 0 | Pitch shift in semitones (-12 to +12) |
| `index_rate` | float | No | 0.75 | Index rate for voice retrieval (0.0-1.0) |
| `filter_radius` | integer | No | 3 | Median filter radius for smoothing |
| `rms_mix_rate` | float | No | 0.25 | RMS mix rate for volume matching (0.0-1.0) |
| `protect` | float | No | 0.33 | Protect voiceless consonants (0.0-0.5) |
| `f0_method` | string | No | rmvpe | Pitch extraction method |

**F0 Methods:**
- `rmvpe` - Robust Model for Voice Pitch Estimation (recommended)
- `harvest` - High-quality but slower
- `pm` - ParselMouth (fast but less accurate)
- `fcpe` - Fast and accurate
- `crepe` - Deep learning-based

**Response:**
```
Content-Type: audio/wav
Content-Disposition: attachment; filename="converted_input.wav"
X-Inference-Time: 2.45
X-Output-Size: 524288
```

Returns converted audio file as binary WAV data.

---

### API Information
**GET** `/`

**Response:**
```json
{
  "name": "RVC Voice Conversion API",
  "version": "1.0.0",
  "endpoints": {
    "/health": "Health check",
    "/models": "List available models",
    "/convert": "Convert voice using RVC model",
    "/docs": "API documentation"
  }
}
```

---

## Python Integration

### Basic Voice Conversion

```python
import requests
from pathlib import Path

# Read audio file
audio_path = Path("input_audio.wav")
with open(audio_path, "rb") as f:
    audio_data = f.read()

# Prepare request
files = {"audio": ("input.wav", audio_data, "audio/wav")}
data = {
    "model_path": "logs/my_model/model.pth",
    "pitch_shift": 0,
    "index_rate": 0.75,
    "filter_radius": 3,
    "rms_mix_rate": 0.25,
    "protect": 0.33,
    "f0_method": "rmvpe"
}

# Send request
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files=files,
    data=data
)

# Save converted audio
if response.status_code == 200:
    with open("converted_output.wav", "wb") as f:
        f.write(response.content)
    print(f"Converted in {response.headers['X-Inference-Time']}s")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### Using Shared Service (Future)

```python
# Future implementation in @shared/services/
from apps.shared.services.rvc_service import (
    RVCService,
    RVCConversionRequest
)

# Initialize service
rvc_service = RVCService()

# Convert voice
request = RVCConversionRequest(
    audio_base64=audio_b64,
    model_path="logs/my_model/model.pth",
    pitch_shift=0,
    index_rate=0.75,
    f0_method="rmvpe"
)

result = await rvc_service.convert_voice(request)
# result.audio_base64 contains converted audio
# result.inference_time shows processing time
```

---

## Use Cases

### 1. Voice Character Transformation
Transform a speaker's voice to match a specific character or persona while maintaining the original speech content.

```python
# Convert narrator voice to character voice
result = convert_voice(
    audio="narrator_recording.wav",
    model="logs/character_voice/model.pth",
    pitch_shift=2,  # Slightly higher pitch
    index_rate=0.8  # High similarity to character
)
```

### 2. Voice Anonymization
Protect speaker identity while preserving speech content.

```python
# Anonymize voice for privacy
result = convert_voice(
    audio="original_interview.wav",
    model="logs/neutral_voice/model.pth",
    protect=0.5,  # Preserve consonants for clarity
    rms_mix_rate=0.3  # Match volume
)
```

### 3. Voice Restoration
Improve voice quality in poor recordings.

```python
# Restore clarity to low-quality recording
result = convert_voice(
    audio="phone_recording.wav",
    model="logs/clear_voice/model.pth",
    filter_radius=5,  # More smoothing
    index_rate=0.7
)
```

### 4. Multilingual Dubbing
Convert voice while maintaining speaker characteristics across languages.

```python
# Dub content with voice conversion
result = convert_voice(
    audio="translated_audio.wav",
    model="logs/original_speaker/model.pth",
    pitch_shift=0,
    index_rate=0.85  # High fidelity to original
)
```

---

## Model Training

### Training Your Own Models

RVC models need to be trained separately using the RVC training pipeline:

1. **Prepare Training Data**
   - Collect 5-30 minutes of clean audio from target speaker
   - Ensure consistent quality (same microphone, environment)
   - Remove background noise

2. **Training Process** (on RunPod or local GPU)
   ```bash
   # SSH to RunPod
   ssh -p 22153 root@194.68.245.121

   # Navigate to RVC directory
   cd /workspace/rvc-webui
   source venv/bin/activate

   # Use Gradio WebUI for training
   python infer-web.py
   # Access at http://localhost:7865
   ```

3. **Training Steps**
   - Upload training audio
   - Process audio (extract features)
   - Train model (2-4 hours on A40)
   - Generate index file
   - Test model quality

4. **Deploy Model**
   - Copy trained .pth file to `logs/<model_name>/`
   - Copy index file to same directory
   - Model automatically available via API

---

## Performance Benchmarks

### Inference Speed
- **Short Audio (5s):** ~1-2 seconds
- **Medium Audio (30s):** ~6-8 seconds
- **Long Audio (2min):** ~25-30 seconds

### Quality Metrics
- **Pitch Accuracy:** >95% with RMVPE
- **Voice Similarity:** 80-95% (depends on model quality)
- **Audio Quality:** 24kHz, 16-bit WAV output

### Resource Usage
- **GPU Memory:** ~2GB VRAM during inference
- **CPU Usage:** Minimal (GPU-accelerated)
- **Bandwidth:** ~88KB per second of audio (WAV format)

---

## Troubleshooting

### Model Not Found
```json
{
  "detail": "Model file not found: logs/my_model/model.pth"
}
```

**Solution:** Verify model file exists in `/workspace/rvc-webui/logs/` on RunPod.

### Out of Memory
```json
{
  "detail": "CUDA out of memory"
}
```

**Solution:** Reduce batch size or wait for current processing to complete.

### Poor Conversion Quality
**Symptoms:** Robotic sound, artifacts, unclear speech

**Solutions:**
1. Adjust `index_rate` (try 0.5-0.9)
2. Change `f0_method` (try `rmvpe` or `harvest`)
3. Increase `filter_radius` for more smoothing
4. Retrain model with more/better quality data

### Pitch Issues
**Symptoms:** Voice too high or low

**Solutions:**
1. Adjust `pitch_shift` parameter (-12 to +12 semitones)
2. Use gender-matched models (male → male, female → female)

---

## Security & Best Practices

### Model Security
- **Access Control:** Models stored on RunPod with SSH access only
- **Version Control:** Track model versions and training data
- **Backup:** Regular backups of trained models

### Audio Privacy
- **Temporary Storage:** Uploaded audio deleted after conversion
- **No Logging:** Audio content not logged
- **Encryption:** HTTPS for all API communication

### Usage Best Practices
1. **Use appropriate models** - Match source/target gender and language
2. **Test parameters** - Experiment with settings for best quality
3. **Monitor resources** - Check GPU usage before large batches
4. **Validate output** - Always verify conversion quality
5. **Cache results** - Store converted audio to avoid reprocessing

---

## Limitations

### Current Limitations
- **Model Training:** Requires separate training process (not via API)
- **Language Dependency:** Quality varies by source audio language
- **Real-time Latency:** Not suitable for live streaming (3-5s latency)
- **Model Size:** Large models (50-100MB) require significant storage

### Coming Soon
- [ ] Batch conversion API
- [ ] Streaming conversion support
- [ ] Model marketplace/library
- [ ] Automatic model selection
- [ ] Multi-speaker conversion

---

## Support & Resources

### Documentation
- **API Docs:** https://rvc.ailabsafrica.com/docs
- **Health Check:** https://rvc.ailabsafrica.com/health
- **GitHub:** https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

### Internal References
- **Deployment:** `/workspace/rvc-webui/` on RunPod (194.68.245.121:22153)
- **API Code:** `/workspace/rvc-webui/app.py`
- **Nginx Config:** `/tmp/rvc.ailabsafrica.com.conf` on production server
- **SSL Certificate:** Let's Encrypt (expires 2026-02-06)

### Contact
For issues or questions, contact the AI Labs Africa Infrastructure Team.

---

**Document Version:** 1.0.0
**Last Updated:** November 8, 2025
**Next Review:** December 8, 2025

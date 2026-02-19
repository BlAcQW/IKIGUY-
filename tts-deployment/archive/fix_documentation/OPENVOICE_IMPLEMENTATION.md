# OpenVoice Implementation Status

## Overview

OpenVoice V2 is a voice cloning TTS system that uses a two-stage architecture:

1. **Base TTS**: Generates initial speech audio from text
2. **Tone Color Converter**: Converts the generated audio to match a target voice

## Implementation Details

### Architecture

OpenVoice V2 does NOT include a built-in base TTS model. It only provides the tone color converter model. According to the official demos:

- **demo_part1.ipynb**: Uses a local base TTS model (EN/ZH checkpoints - not included in v2 download)
- **demo_part2.ipynb**: Uses OpenAI TTS API as the base TTS

Our implementation uses **MeloTTS** (already deployed in our infrastructure) as the base TTS.

### Synthesis Pipeline

```
Text → MeloTTS (Base TTS) → Base Audio → OpenVoice Tone Converter → Target Voice Audio
```

**Step-by-step process:**
1. User sends text + target speaker embedding name
2. MeloTTS generates base audio from text
3. OpenVoice extracts speaker embedding from base audio
4. OpenVoice loads target speaker embedding (pre-extracted)
5. OpenVoice converts base audio tone to match target speaker
6. Return converted audio

### API Endpoints

#### GET /health
Health check endpoint
```json
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "available_speakers": 11
}
```

#### GET /speakers
List available pre-extracted speaker embeddings
```json
{
  "speakers": [
    {"name": "en-default", "language": "EN", "description": "EN speaker variant"},
    {"name": "en-us", "language": "EN", "description": "EN speaker variant"},
    ...
  ],
  "count": 11
}
```

#### POST /synthesize
Synthesize speech with voice cloning

**Request:**
```json
{
  "text": "Hello, this is a test",
  "reference_speaker": "en-default",
  "base_speaker": "EN-Default",  // MeloTTS speaker
  "language": "EN",
  "speed": 1.0
}
```

**Response:** Audio file (WAV format)

#### POST /clone_voice
Clone voice from uploaded audio file

**Form Data:**
- `text` (string): Text to synthesize
- `reference_audio` (file): Audio file with target voice
- `base_speaker` (string, optional): MeloTTS speaker
- `speed` (float, optional): Speech speed

**Response:** Audio file (WAV format)

### Available Speaker Embeddings

Pre-extracted speaker embeddings (fast synthesis):
- `en-au` - English Australian
- `en-br` - English British
- `en-default` - English Default
- `en-india` - English Indian
- `en-newest` - English Newest
- `en-us` - English US
- `es` - Spanish
- `fr` - French
- `jp` - Japanese
- `kr` - Korean
- `zh` - Chinese

## Current Status

### ✅ Completed

1. **Models Loaded**:
   - Tone Color Converter model loaded successfully
   - 11 pre-extracted speaker embeddings loaded
   - Device: CUDA

2. **API Implementation**:
   - `/health` endpoint working
   - `/speakers` endpoint working
   - `/synthesize` endpoint implemented
   - `/clone_voice` endpoint implemented

3. **Docker Setup**:
   - Dockerfile configured
   - OpenVoice V2 checkpoints downloaded
   - Network connectivity to MeloTTS verified

### ⚠️ Known Issues

1. **cuDNN Library Warning**:
   ```
   Unable to load any of {libcudnn_cnn.so.9.1.0, libcudnn_cnn.so.9.1, libcudnn_cnn.so.9, libcudnn_cnn.so}
   Invalid handle. Cannot load symbol cudnnCreateConvolutionDescriptor
   ```

   **Impact**: Synthesis requests hang/timeout

   **Cause**: The base CUDA 12.1 runtime image may have cuDNN version mismatch

   **Solution Options**:
   - Option A: Use CUDA devel image with full cuDNN 9.x
   - Option B: Install compatible cuDNN version in current image
   - Option C: Use CPU mode for OpenVoice (slower but functional)

2. **Config File Missing**:
   - `config_v2.json` was not extracted from checkpoint zip during Docker build
   - **Workaround Applied**: Manually copied config file to container
   - **Fix Needed**: Update Dockerfile to ensure config is properly extracted

## Files Modified

1. `/opt/kasaai/apps/tts-deployment/docker/openvoice/app.py`
   - Implemented full FastAPI server with all endpoints
   - Integration with MeloTTS for base audio generation
   - Speaker embedding management

2. `/opt/kasaai/apps/tts-deployment/docker/openvoice/Dockerfile`
   - Added httpx dependency
   - OpenVoice V2 checkpoint download and extraction
   - PyAV 13.1.0 compatibility fixes

## Next Steps

### High Priority

1. **Fix cuDNN Issue**:
   - Test with CUDA 12.1 devel image or install cuDNN 9.x libraries
   - Alternative: Implement CPU fallback mode

2. **Fix Dockerfile Checkpoint Extraction**:
   - Ensure `config_v2.json` is properly copied during build
   - Verify all checkpoints are in correct locations

3. **End-to-End Testing**:
   - Test `/synthesize` endpoint with fixed cuDNN
   - Test `/clone_voice` with sample audio file
   - Measure latency and quality

### Medium Priority

4. **Performance Optimization**:
   - Cache MeloTTS base audio for common phrases
   - Implement async processing for long texts
   - Add request queuing for multiple concurrent requests

5. **Error Handling**:
   - Better error messages for invalid speakers
   - Timeout handling for MeloTTS requests
   - Audio format validation

### Low Priority

6. **Feature Enhancements**:
   - Support for custom speaker embedding upload
   - Batch processing endpoint
   - Streaming audio output
   - Support for multiple base TTS engines (not just MeloTTS)

## Usage Examples

### Using with curl

```bash
# List available speakers
curl http://localhost:8003/speakers

# Synthesize with pre-loaded speaker
curl -X POST http://localhost:8003/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "reference_speaker": "en-default"}' \
  -o output.wav

# Clone voice from audio file
curl -X POST http://localhost:8003/clone_voice \
  -F "text=Hello, this is a test" \
  -F "reference_audio=@my_voice.wav" \
  -o cloned.wav
```

### Using with Python

```python
import httpx

# Synthesize
response = httpx.post(
    "http://localhost:8003/synthesize",
    json={
        "text": "Hello world",
        "reference_speaker": "en-default"
    }
)
with open("output.wav", "wb") as f:
    f.write(response.content)

# Clone voice
files = {"reference_audio": open("my_voice.wav", "rb")}
data = {"text": "Hello, this is a test"}
response = httpx.post(
    "http://localhost:8003/clone_voice",
    files=files,
    data=data
)
with open("cloned.wav", "wb") as f:
    f.write(response.content)
```

## Technical Notes

### Why Use MeloTTS as Base TTS?

OpenVoice V2 requires a base TTS to generate initial audio. We chose MeloTTS because:
1. Already deployed in our infrastructure
2. Supports multiple languages
3. Fast inference on GPU
4. Good quality output for conversion

Alternative options:
- OpenAI TTS API (requires API key, costs money)
- Coqui TTS (also deployed, but slower)
- Download OpenVoice V1 base TTS models (not included in V2)

### Speaker Embeddings

The pre-extracted speaker embeddings in `checkpoints/base_speakers/ses/` are:
- Size: ~1.7KB each (very small)
- Format: PyTorch tensor (.pth)
- Purpose: Fast synthesis without VAD processing
- Can be loaded in bulk at startup

For custom voices, the `/clone_voice` endpoint extracts embeddings on-the-fly using:
- OpenVoice's `se_extractor.get_se()`
- Voice Activity Detection (VAD) to remove silence
- Takes a few seconds per audio file

## References

- [OpenVoice GitHub](https://github.com/myshell-ai/OpenVoice)
- [OpenVoice V2 Paper](https://arxiv.org/abs/2312.01479)
- OpenVoice Demo Notebooks (included in repo)

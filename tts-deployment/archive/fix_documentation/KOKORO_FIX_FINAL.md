# Kokoro TTS Fix - October 20, 2025

## Problem Summary

Kokoro container was starting but showing as **unhealthy** in Docker status. Initial investigation revealed multiple issues preventing proper operation.

## Root Causes

### Issue 1: Missing `transformers` Library
**Error:** `Could not import kokoro package: No module named 'transformers'`

**Analysis:**
- Dockerfile manually installed dependencies instead of using Kokoro's `pyproject.toml`
- Missing key dependencies: `transformers`, `huggingface_hub`, `misaki[en]`, etc.

**Solution:**
Replaced manual dependency installation with proper package installation:
```dockerfile
# Install Kokoro package and its dependencies from pyproject.toml
RUN pip3 install -e .
```

### Issue 2: Incorrect Import Pattern
**Error:** `cannot import name 'generate' from 'kokoro'`

**Analysis:**
- Kokoro doesn't export a `generate` function
- Uses `KPipeline` class for TTS synthesis
- Returns generator of `Result` objects, not direct audio

**Solution:**
Updated `app.py` to use Kokoro's actual API:
```python
from kokoro import KPipeline

# Create pipeline for language
pipeline = KPipeline(lang_code=lang_code)

# Generate audio (returns generator of Result objects)
audio_chunks = []
for result in pipeline(text, voice=voice_id, speed=speed):
    if result.audio is not None:
        audio_chunks.append(result.audio.numpy())

audio_array = np.concatenate(audio_chunks)
```

### Issue 3: Health Check Failure
**Error:** `curl: executable file not found in $PATH`

**Analysis:**
- Dockerfile's healthcheck uses `curl` but doesn't install it
- Health check was failing, marking container as unhealthy

**Solution:**
Added `curl` to system dependencies:
```dockerfile
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \    # Added
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
```

## Files Modified

1. **`/opt/kasaai/apps/tts-deployment/docker/kokoro/Dockerfile`**
   - Added `curl` to system dependencies
   - Replaced manual dependency installation with `pip3 install -e .`

2. **`/opt/kasaai/apps/tts-deployment/docker/kokoro/app.py`**
   - Updated imports to use `KPipeline` instead of `generate`
   - Fixed synthesis logic to use KPipeline generator pattern
   - Updated voice pack list with correct Kokoro voices
   - Fixed health check to work with dict-based model storage

## Deployment Steps

1. Updated Dockerfile: `/opt/kasaai/apps/tts-deployment/docker/kokoro/Dockerfile`
2. Updated app.py: `/opt/kasaai/apps/tts-deployment/docker/kokoro/app.py`
3. Rebuilt container:
   ```bash
   sudo docker-compose -f docker-compose.local.yml build kokoro
   ```
4. Removed old container:
   ```bash
   sudo docker rm -f kokoro
   ```
5. Started fresh container:
   ```bash
   sudo docker-compose -f docker-compose.local.yml up -d kokoro
   ```

## Verification

**Container Status:**
```bash
$ sudo docker ps | grep kokoro
1915d49350c1   tts-deployment_kokoro   Up 30 seconds (healthy)   0.0.0.0:8010->8010/tcp
```

**Health Check:**
```bash
$ curl -s http://localhost:8010/health | python3 -m json.tool
{
    "status": "healthy",
    "device": "cuda",
    "model_loaded": true,
    "voicepacks": 11
}
```

**Startup Logs:**
```
INFO:__main__:Using device: cuda
INFO:__main__:Kokoro TTS loaded successfully
INFO:__main__:Loaded 11 voice packs
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8010 (Press CTRL+C to quit)
```

## Available Voices

Kokoro now provides 11 voice packs:
- **American English:** af_heart, af_bella, af_nicole, af_sarah, af_sky, am_adam, am_michael
- **British English:** bf_emma, bf_isabella, bm_george, bm_lewis

## Technical Details

### Kokoro Architecture

Kokoro uses a generator-based pipeline:
1. **KPipeline**: Main synthesis class, created per language
2. **Result Objects**: Each contains audio chunk + metadata (phonemes, etc.)
3. **Voice Codes**: Format `{lang}{gender}_{name}` (e.g., `af_heart` = American female)

### Language Codes
- `a` = American English
- `b` = British English
- `p` = Brazilian Portuguese
- `e` = Spanish
- `f` = French
- `j` = Japanese
- `z` = Mandarin Chinese
(More languages available in Kokoro repository)

### Implementation Pattern

```python
# Language determined from voice prefix
lang_code = voice_id[0]  # "af_heart" -> "a"

# Create or reuse pipeline
if lang_code not in model:
    model[lang_code] = KPipeline(lang_code=lang_code)

# Generate audio (streaming)
for result in model[lang_code](text, voice=voice_id, speed=speed):
    if result.audio is not None:
        audio_chunks.append(result.audio.numpy())

# Concatenate chunks
audio = np.concatenate(audio_chunks)
```

## Status

✅ **RESOLVED** - Kokoro container is running stable and healthy

## All TTS Services Status

- **MeloTTS**: ✅ Healthy (port 8001)
- **OpenVoice**: ✅ Healthy (port 8003)
- **Kokoro**: ✅ Healthy (port 8010)

## Related Documentation

- Kokoro GitHub: https://github.com/hexgrad/kokoro
- Hugging Face Model: https://huggingface.co/hexgrad/Kokoro-82M
- Dependencies: See `pyproject.toml` in Kokoro repository

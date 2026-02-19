# RunPod TTS Service Wrappers

This directory contains FastAPI wrappers for RunPod Gradio-based TTS services to enable streaming support.

## Overview

Each wrapper provides:
- `/synthesize` - Blocking synthesis endpoint
- `/synthesize/stream` - Streaming synthesis endpoint (sentence-level)
- `/health` - Health check endpoint
- Automatic fallback to blocking mode on streaming errors

## Wrappers

### 1. Fish Speech Wrapper
- **Directory**: `fish_speech_wrapper/`
- **Gradio Port**: 7860
- **Wrapper Port**: 8020
- **Features**: Zero-shot voice cloning, fast inference, natural prosody

### 2. TTS-WebUI (OuteTTS) Wrapper
- **Directory**: `tts_webui_wrapper/`
- **Gradio Port**: 8017
- **Wrapper Port**: 8021
- **Features**: 20+ TTS models (StyleTTS2, F5-TTS, XTTS, RVC, etc.)

### 3. GPT-SoVITS Wrapper
- **Directory**: `gptsovits_wrapper/`
- **Gradio Port**: 9880
- **Wrapper Port**: 8022
- **Features**: GPT-based zero-shot cloning, high-quality synthesis

### 4. Zonos TTS Wrapper
- **Directory**: `zonos_wrapper/`
- **Gradio Port**: 7861
- **Wrapper Port**: 8023
- **Features**: Emotion control sliders, prosody control, expressiveness

## Deployment on RunPod

### Prerequisites
```bash
pip install fastapi uvicorn httpx gradio_client soundfile numpy pydantic
```

### Running a Wrapper

Each wrapper can be run independently:

```bash
# Fish Speech
cd fish_speech_wrapper
python app.py

# TTS-WebUI
cd tts_webui_wrapper
python app.py

# GPT-SoVITS
cd gptsovits_wrapper
python app.py

# Zonos TTS
cd zonos_wrapper
python app.py
```

### Using Supervisor (Recommended)

Create `/etc/supervisor/conf.d/tts_wrappers.conf`:

```ini
[program:fish_speech_wrapper]
command=python /workspace/fish_speech_wrapper/app.py
directory=/workspace/fish_speech_wrapper
autostart=true
autorestart=true
stderr_logfile=/var/log/fish_speech_wrapper.err.log
stdout_logfile=/var/log/fish_speech_wrapper.out.log

[program:tts_webui_wrapper]
command=python /workspace/tts_webui_wrapper/app.py
directory=/workspace/tts_webui_wrapper
autostart=true
autorestart=true
stderr_logfile=/var/log/tts_webui_wrapper.err.log
stdout_logfile=/var/log/tts_webui_wrapper.out.log

[program:gptsovits_wrapper]
command=python /workspace/gptsovits_wrapper/app.py
directory=/workspace/gptsovits_wrapper
autostart=true
autorestart=true
stderr_logfile=/var/log/gptsovits_wrapper.err.log
stdout_logfile=/var/log/gptsovits_wrapper.out.log

[program:zonos_wrapper]
command=python /workspace/zonos_wrapper/app.py
directory=/workspace/zonos_wrapper
autostart=true
autorestart=true
stderr_logfile=/var/log/zonos_wrapper.err.log
stdout_logfile=/var/log/zonos_wrapper.out.log
```

Then reload supervisor:
```bash
supervisorctl reread
supervisorctl update
supervisorctl status
```

## API Usage

### Blocking Synthesis
```bash
curl -X POST http://localhost:8020/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test.",
    "language": "en",
    "speed": 1.0
  }' \
  --output output.wav
```

### Streaming Synthesis
```bash
curl -X POST http://localhost:8020/synthesize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world. This is a streaming test. The audio should arrive in chunks.",
    "language": "en",
    "speed": 1.0
  }' \
  --output output_stream.wav
```

### TTS-WebUI Multi-Model Example
```bash
curl -X POST http://localhost:8021/synthesize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Advanced synthesis with F5-TTS model.",
    "model": "f5-tts",
    "language": "en",
    "speed": 1.0
  }' \
  --output f5tts_output.wav
```

## Architecture

```
User Request
    ↓
FastAPI Wrapper (Port 802X)
    ↓
Gradio API Client
    ↓
Gradio App (Port 78XX/98XX)
    ↓
TTS Model Inference
    ↓
Audio Chunks (Sentence-level)
    ↓
Stream to User
```

## Integration with Unified TTS Service

The wrappers are integrated into the unified TTS service via the provider classes in `apps/shared/tts/providers.py`:

- `FishSpeechProvider.stream_synthesize()` → Fish Speech wrapper
- `TTSWebUIProvider.stream_synthesize()` → TTS-WebUI wrapper
- `GPTSoVITSProvider.stream_synthesize()` → GPT-SoVITS wrapper
- `ZonosTTSProvider.stream_synthesize()` → Zonos wrapper

All providers implement automatic fallback to blocking mode if streaming fails.

## Port Allocation

| Service | Gradio | Wrapper | RunPod Proxy |
|---------|--------|---------|--------------|
| Fish Speech | 7860 | 8020 | 8012.proxy.runpod.net |
| TTS-WebUI | 8017 | 8021 | 8014.proxy.runpod.net |
| GPT-SoVITS | 9880 | 8022 | 8011.proxy.runpod.net |
| Zonos TTS | 7861 | 8023 | 8013.proxy.runpod.net |

## Notes

- All wrappers use sentence-level streaming (not word-level)
- Text is split using regex: `r'([.!?]+\s*)'`
- Default chunk size: 8KB for efficient network transmission
- Gradio API names (`/tts`, `/synthesize`, etc.) may need adjustment based on actual Gradio interface
- Check Gradio app logs to verify correct API endpoint names

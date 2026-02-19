# Whisper ASR Service Consolidation

**Date:** 2025-11-27
**Status:** ✅ Complete

---

## 🎯 Summary

Successfully consolidated Whisper ASR services by:
1. ✅ Updated RunPod whisper-asr service to match `faster_whisper_service.py` functionality
2. ✅ Configured service on port 8011 at `whisper.ailabsafrica.com`
3. ✅ Updated `core_backend` to use RunPod API endpoint instead of local service
4. ✅ Removed old `whisper-api` directory
5. ✅ Updated documentation

---

## ✅ Changes Made

### 1. RunPod Whisper ASR Service (`/workspace/tts-deployment/docker/whisper-asr`)

**Updated Features:**
- ✅ Port changed from 8020 → **8011**
- ✅ Added Gift Mark Akan Whisper model support (92.9% Twi accuracy)
- ✅ Added Ghanaian language mapping (Twi, Ewe, Ga, Dagbani, Hausa, Yoruba, Igbo, Swahili)
- ✅ Matches `faster_whisper_service.py` functionality exactly
- ✅ Supports all endpoints: `/health`, `/transcribe`, `/v1/audio/transcriptions`, `/ws/stream`

**Endpoints:**
- `GET /health` - Health check
- `GET /v1/models` - List available models
- `POST /v1/audio/transcriptions` - OpenAI-compatible transcription
- `POST /transcribe` - Simplified transcription endpoint
- `WS /ws/stream` - WebSocket streaming transcription

**Configuration:**
- Default model: `base` (changed from `medium`)
- Port: `8011`
- Device: `cuda` (GPU-accelerated on RunPod)
- Akan model path: `/workspace/models/akan_whisper` (configurable via `AKAN_MODEL_PATH`)

### 2. Core Backend Updates

**Updated Files:**
- `backend/services/unified_whisper_service.py` - Now uses API client by default
- `backend/services/whisper_api_client.py` - Default model changed to `base`
- `backend/routes/voice_lab_routes.py` - Uses API client instead of local service

**Key Changes:**
- `UnifiedWhisperService` now uses RunPod API by default (`WHISPER_USE_API=true`)
- Falls back to local `faster_whisper_service` if API unavailable
- All whisper endpoints now route through RunPod service

### 3. Removed Files
- ✅ `/opt/kasaai/apps/whisper-api/` - Removed (consolidated into RunPod service)

---

## 🌐 Service Access

**URL:** https://whisper.ailabsafrica.com
**Port:** 8011
**RunPod Port:** 8011 (HTTP Service Ready)

**Health Check:**
```bash
curl https://whisper.ailabsafrica.com/health
```

**Transcribe:**
```bash
curl -X POST https://whisper.ailabsafrica.com/transcribe \
  -F "audio_file=@audio.wav" \
  -F "model=base" \
  -F "language=tw"
```

---

## 🔄 Migration Path

### For Developers

**Before:**
```python
from backend.services.faster_whisper_service import faster_whisper_service

result = await faster_whisper_service.transcribe_audio(audio_path, language="tw")
```

**After (Recommended):**
```python
from backend.services.unified_whisper_service import unified_whisper_service

# Automatically uses RunPod API
result = await unified_whisper_service.transcribe_audio(audio_path, language="tw")
```

**Or Direct API Client:**
```python
from backend.services.whisper_api_client import get_whisper_api_client

client = get_whisper_api_client()
result = await client.transcribe_audio(audio_path, language="tw")
```

### Environment Variables

**To use local service (fallback):**
```bash
WHISPER_USE_API=false
```

**To use RunPod API (default):**
```bash
WHISPER_USE_API=true  # or omit (default)
WHISPER_API_URL=https://whisper.ailabsafrica.com
```

---

## 📊 Feature Parity

| Feature | Local Service | RunPod API | Status |
|---------|--------------|------------|--------|
| Faster Whisper models | ✅ | ✅ | ✅ |
| Akan Whisper model (92.9%) | ✅ | ✅ | ✅ |
| Ghanaian languages | ✅ | ✅ | ✅ |
| Word timestamps | ✅ | ✅ | ✅ |
| VAD filtering | ✅ | ✅ | ✅ |
| WebSocket streaming | ❌ | ✅ | ✅ |
| GPU acceleration | ❌ | ✅ | ✅ |

---

## 🧪 Testing

**Test Health Endpoint:**
```bash
curl https://whisper.ailabsafrica.com/health
```

**Test Transcription:**
```bash
curl -X POST https://whisper.ailabsafrica.com/transcribe \
  -F "audio_file=@test.wav" \
  -F "model=base" \
  -F "language=tw"
```

**Test Akan Model:**
```bash
curl -X POST https://whisper.ailabsafrica.com/transcribe \
  -F "audio_file=@twi_audio.wav" \
  -F "language=twi"
# Automatically uses Gift Mark Akan model (92.9% accuracy)
```

---

## 📝 Notes

- Local `faster_whisper_service.py` is kept as fallback for development/testing
- RunPod service provides better performance with GPU acceleration
- All endpoints maintain backward compatibility with existing code
- Akan model automatically selected for Twi/Akan languages

---

## 🔗 Related Documentation

- `apps/core_backend/backend/services/faster_whisper_service.py` - Original service (now fallback)
- `apps/core_backend/backend/services/whisper_api_client.py` - API client
- `apps/tts-deployment/docker/whisper-asr/app.py` - RunPod service implementation


# Whisper ASR Migration to RunPod

**Date:** 2025-01-27  
**Goal:** Move Whisper ASR from local server to RunPod to free up GPU for TTS services  
**Status:** 📋 Planning

---

## 🎯 Objective

Move Whisper ASR service from local server (148.251.0.46) to RunPod (194.68.245.121) to:
- ✅ Free up GPU memory for TTS services (MeloTTS, Coqui, etc.)
- ✅ Reduce CUDA device contention
- ✅ Leverage RunPod's powerful A40 GPU (46GB VRAM)
- ✅ Maintain same API endpoint (`whisper.ailabsafrica.com`)

---

## 📊 Current Setup

### Local Whisper ASR
- **Location:** `apps/whisper-api/main.py`
- **Port:** 30042 (internal)
- **Domain:** `whisper.ailabsafrica.com`
- **GPU Usage:** ~2-3GB VRAM (medium model)
- **Status:** ✅ Working but causing GPU contention

### RunPod Pod
- **Pod ID:** jzfmzviw26huka-644113c7
- **GPU:** NVIDIA A40 (46GB VRAM)
- **Storage:** 200GB
- **SSH:** `ssh -p 22153 -i ~/.ssh/id_ed25519 root@194.68.245.121`
- **Available Ports:** 8010-8019, 8888
- **Current Usage:** TTS services (F5-TTS, StyleTTS2, Zonos, Fish Speech, TTS-WebUI, RVC)

---

## 🚀 Migration Plan

### Phase 1: Deploy Whisper ASR on RunPod

#### Step 1: Create Whisper ASR Service on RunPod

**File:** `apps/tts-deployment/docker/whisper-asr/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Expose port
EXPOSE 8020

# Run service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8020"]
```

**File:** `apps/tts-deployment/docker/whisper-asr/requirements.txt`

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
faster-whisper>=1.0.0
pydantic>=2.0.0
python-multipart>=0.0.6
numpy>=1.24.0
```

**File:** `apps/tts-deployment/docker/whisper-asr/app.py`

```python
"""
Whisper ASR API Service for RunPod
Port: 8020
"""
import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper-asr")

# Configuration
PORT = int(os.getenv("WHISPER_PORT", "8020"))
DEFAULT_MODEL = os.getenv("WHISPER_MODEL", "medium")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

# Model manager
class WhisperModelManager:
    def __init__(self):
        self.models: Dict[str, WhisperModel] = {}
        self.device = DEVICE
        self.compute_type = COMPUTE_TYPE

    def load_model(self, model_size: str) -> WhisperModel:
        if model_size in self.models:
            return self.models[model_size]

        logger.info(f"Loading Whisper model: {model_size} on {self.device}")
        model = WhisperModel(
            model_size_or_path=model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        self.models[model_size] = model
        logger.info(f"Model '{model_size}' loaded successfully")
        return model

    def get_model(self, model_size: str) -> WhisperModel:
        if model_size not in self.models:
            return self.load_model(model_size)
        return self.models[model_size]

model_manager = WhisperModelManager()

# Preload default model
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Whisper ASR service...")
    model_manager.load_model(DEFAULT_MODEL)
    logger.info(f"Preloaded default model: {DEFAULT_MODEL}")
    yield
    logger.info("Shutting down Whisper ASR service...")

app = FastAPI(
    title="Whisper ASR API",
    description="Faster Whisper ASR API for RunPod",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    probability: float

class TranscriptionSegment(BaseModel):
    text: str
    start: float
    end: float
    confidence: float
    words: List[WordTimestamp] = []

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[TranscriptionSegment] = []
    task: str = "transcribe"
    model: str = ""
    model_size: str = ""

class HealthResponse(BaseModel):
    status: str
    models_loaded: List[str]
    gpu_available: bool
    device: str

@app.get("/health")
async def health():
    """Health check endpoint"""
    import torch
    return HealthResponse(
        status="healthy",
        models_loaded=list(model_manager.models.keys()),
        gpu_available=torch.cuda.is_available() if DEVICE == "cuda" else False,
        device=DEVICE
    )

@app.post("/transcribe")
async def transcribe(
    audio_file: UploadFile = File(...),
    model: str = Query("whisper-medium", description="Model to use"),
    language: Optional[str] = Query(None, description="Language code (auto-detect if None)"),
    task: str = Query("transcribe", description="Task: transcribe or translate"),
    word_timestamps: bool = Query(False, description="Include word-level timestamps")
):
    """Transcribe audio file"""
    try:
        # Extract model size
        model_size = model.replace("whisper-", "").strip()
        if model_size not in ["tiny", "base", "small", "medium", "large-v2", "large-v3"]:
            raise HTTPException(status_code=400, detail=f"Invalid model: {model_size}")

        # Get model
        whisper_model = model_manager.get_model(model_size)

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_path = tmp_file.name
            content = await audio_file.read()
            tmp_file.write(content)

        try:
            # Transcribe
            options = {
                "language": language if language else None,
                "task": task,
                "word_timestamps": word_timestamps,
            }

            segments_iter, info = whisper_model.transcribe(tmp_path, **options)

            # Build response
            segments = []
            full_text = []
            words_list = []

            for segment in segments_iter:
                segment_words = []
                if word_timestamps and segment.words:
                    for word in segment.words:
                        segment_words.append(WordTimestamp(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            probability=word.probability
                        ))
                        words_list.append(word.word)

                segments.append(TranscriptionSegment(
                    text=segment.text,
                    start=segment.start,
                    end=segment.end,
                    confidence=segment.no_speech_prob,
                    words=segment_words
                ))
                full_text.append(segment.text)

            return TranscriptionResponse(
                text=" ".join(full_text),
                language=info.language,
                confidence=1.0 - info.language_prob,
                duration=info.duration,
                segments=segments,
                task=task,
                model=f"faster-whisper-{model_size}",
                model_size=model_size
            )

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

#### Step 2: Add to RunPod Docker Compose

**File:** `apps/tts-deployment/docker-compose.runpod.yml`

Add after existing services:

```yaml
  whisper-asr:
    build: ./docker/whisper-asr
    container_name: whisper-asr
    ports:
      - "8020:8020"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities:
                - gpu
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - NVIDIA_VISIBLE_DEVICES=all
      - WHISPER_PORT=8020
      - WHISPER_MODEL=medium
      - WHISPER_DEVICE=cuda
      - WHISPER_COMPUTE_TYPE=float16
    volumes:
      - whisper_models:/root/.cache/huggingface
    restart: unless-stopped
    networks:
      - tts_network
```

#### Step 3: Deploy on RunPod

```bash
# SSH into RunPod
ssh -p 22153 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Navigate to deployment directory
cd /workspace/tts-deployment

# Build and start Whisper ASR
docker-compose -f docker-compose.runpod.yml up -d whisper-asr

# Check logs
docker logs -f whisper-asr

# Test health endpoint
curl http://localhost:8020/health
```

#### Step 4: Expose Port on RunPod Dashboard

1. Go to RunPod Dashboard: https://www.runpod.io/console/pods
2. Find pod: **jzfmzviw26huka-644113c7**
3. Click **"Edit Pod"**
4. Add port **8020** to "Expose HTTP Ports"
5. Save and wait 1-2 minutes

**RunPod Proxy URL:** `https://jzfmzviw26huka-8020.proxy.runpod.net`

---

### Phase 2: Update Nginx Configuration

**File:** `/etc/nginx/sites-enabled/whisper.ailabsafrica.com`

Update to point to RunPod:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name whisper.ailabsafrica.com;

    location / {
        proxy_pass https://jzfmzviw26huka-8020.proxy.runpod.net;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**Test:**
```bash
sudo nginx -t
sudo systemctl reload nginx
curl https://whisper.ailabsafrica.com/health
```

---

### Phase 3: Update Provider Registry

**File:** `apps/shared/integration/ai_services/provider_registry.py`

Update Whisper endpoint (line 762):

```python
# FROM:
whisper_endpoint = os.getenv("WHISPER_ENDPOINT", "https://whisper.ailabsafrica.com")

# TO: (No change needed - domain stays the same, nginx handles routing)
whisper_endpoint = os.getenv("WHISPER_ENDPOINT", "https://whisper.ailabsafrica.com")
```

**Note:** The endpoint URL stays the same because nginx proxies to RunPod transparently.

---

### Phase 4: Stop Local Whisper Service

```bash
# Stop local Whisper API service
sudo systemctl stop whisper-api  # If running as systemd service
# OR
docker stop whisper-api  # If running in Docker

# Verify it's stopped
curl http://localhost:30042/health  # Should fail
```

---

## ✅ Verification Checklist

- [ ] Whisper ASR deployed on RunPod (port 8020)
- [ ] Port 8020 exposed on RunPod dashboard
- [ ] Health endpoint working: `curl https://jzfmzviw26huka-8020.proxy.runpod.net/health`
- [ ] Nginx configuration updated
- [ ] Domain working: `curl https://whisper.ailabsafrica.com/health`
- [ ] Transcription test successful
- [ ] Local Whisper service stopped
- [ ] All ASR providers still working
- [ ] GPU memory freed on local server

---

## 📊 Expected Benefits

### GPU Memory Freed
- **Before:** ~11.2GB used (55% of 20GB)
- **After:** ~8-9GB used (40-45% of 20GB)
- **Freed:** ~2-3GB for TTS services

### CUDA Contention Reduced
- **Before:** 6 services competing for GPU (5 TTS + 1 ASR)
- **After:** 5 services (TTS only)
- **Result:** Less contention, faster model loading

### Performance
- **RunPod A40:** More powerful than local RTX 4000
- **Dedicated GPU:** ASR gets full GPU access
- **Latency:** Similar (nginx proxy adds ~10-20ms)

---

## 🔄 Rollback Plan

If issues occur:

1. **Revert nginx config:**
   ```bash
   sudo cp /etc/nginx/sites-enabled/whisper.ailabsafrica.com.backup /etc/nginx/sites-enabled/whisper.ailabsafrica.com
   sudo systemctl reload nginx
   ```

2. **Restart local Whisper:**
   ```bash
   sudo systemctl start whisper-api
   # OR
   docker start whisper-api
   ```

3. **Update provider registry** (if needed):
   - Revert to local endpoint

---

## 📝 Next Steps

1. ✅ Create Whisper ASR Docker setup
2. ⏳ Deploy on RunPod
3. ⏳ Expose port 8020
4. ⏳ Update nginx configuration
5. ⏳ Test and verify
6. ⏳ Stop local service
7. ⏳ Monitor GPU usage

---

**Migration Date:** TBD  
**Estimated Time:** 30-60 minutes  
**Risk Level:** Low (easy rollback)


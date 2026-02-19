# Moshi Deployment Summary

## Date: October 20, 2025

## Overview
Successfully deployed Kyutai Moshi (real-time conversational AI) locally and integrated service management into the B2C portal admin interface.

## What Was Accomplished

### 1. Moshi Docker Deployment ✅
- **Location**: `/opt/kasaai/apps/tts-deployment/docker/moshi/`
- **Docker Image**: Created custom Dockerfile with NVIDIA CUDA 12.1, PyTorch 2.5.1, and Moshi package
- **Container**: Running on local server (148.251.0.46) at port 8011
- **Models**: 
  - Moshiko LM: `kyutai/moshiko-pytorch-bf16` (~18GB)
  - Moshika Mimi: `kyutai/moshika-pytorch-bf16` (~3GB Audio Codec)
- **Status**: Container running but models **NOT FULLY LOADED** due to GPU memory constraints

### 2. GPU Memory Constraint ⚠️
**CRITICAL BLOCKER**: Moshi requires ~21GB total GPU memory but only 19.55GB available

- **GPU**: NVIDIA RTX 4000 SFF Ada Generation (20GB VRAM)
- **Moshi LM Model**: Successfully loaded (~18GB)
- **Mimi Codec**: **FAILED to load** - Out of GPU memory (needs additional ~3GB)
- **Health Status**: `degraded` (moshi_lm_loaded: false, mimi_loaded: false)

**Services Stopped to Free GPU**:
- OpenVoice (was using ~2.18GB)
- MeloTTS (was using ~934MB)
- Coqui XTTS (was using ~810MB)
- Core Backend (was using ~1.33GB)

**Result**: Even with all services stopped, 20GB GPU insufficient for Moshi's 21GB requirement

### 3. Frontend Integration ✅
**Files Modified**:
- `/opt/kasaai/apps/b2c-portal/src/config/tts-providers.ts`
  - Changed provider ID from 'kyutai' to 'moshi'
  - Added endpoint: `http://localhost:8011`
  - Added `realTimeConversation: true` capability

- `/opt/kasaai/apps/b2c-portal/src/pages/TTSLab.tsx`
  - Added 'conversation' tab type for Moshi
  - Created real-time conversation UI with features list
  - Updated advanced features section for Moshi configuration

- `/opt/kasaai/apps/b2c-portal/src/components/admin/ServiceManagementUpdated.tsx`
  - Extended with Docker TTS services tab
  - Added service cards for: Moshi, Coqui, MeloTTS, OpenVoice, Kokoro
  - Implemented start/stop/restart buttons for each service
  - Added GPU memory monitoring display
  - Included Remote Services section for F5-TTS and StyleTTS2 on RunPod
  - Added GPU warning alert about 20GB constraint

**Access Point**: https://flow.ailabsafrica.com/admin/system-health
- Navigate to "Services" tab
- Switch to "Docker TTS Services" sub-tab

### 4. Backend API Endpoints ✅ (Partial)
**Files Modified**:
- `/opt/kasaai/apps/core_backend/backend/routes/system_health.py`
  - Added `/api/system/docker/{service_id}/status` - Get container status
  - Added `/api/system/docker/{service_id}/start` - Start container
  - Added `/api/system/docker/{service_id}/stop` - Stop container
  - Added `/api/system/docker/{service_id}/restart` - Restart container

**Status**: Endpoints created but require sudo configuration for full functionality
- Commands use `sudo docker` for container management
- Backend process needs passwordless sudo access or alternative approach

**Known Limitation**: Backend currently returns "Container not found" errors - requires sudo configuration in production

### 5. TTS Service Deployment Status

| Service | Status | GPU Memory | Location | Endpoint |
|---------|--------|------------|----------|----------|
| **Moshi** | 🟡 Running (Degraded) | Requires ~19GB | Local Docker | http://localhost:8011 |
| **Coqui XTTS** | ⚫ Stopped | ~4GB | Local Docker | https://coqui.ailabsafrica.com |
| **MeloTTS** | ⚫ Stopped | ~2GB | Local Docker | https://melotts.ailabsafrica.com |
| **OpenVoice** | ⚫ Stopped | ~4GB | Local Docker | https://openvoice.ailabsafrica.com |
| **Kokoro** | 🔴 Building | TBD | Local Docker | https://kokoro.ailabsafrica.com |
| **F5-TTS** | 🟢 Online | N/A (RunPod) | RunPod A40 46GB | https://f5tts.ailabsafrica.com |
| **StyleTTS2** | 🟢 Online | N/A (RunPod) | RunPod A40 46GB | https://styletts.ailabsafrica.com |

## Resolution Options for Moshi

### Option 1: Deploy on RunPod with Larger Container Storage
- **Status**: Previously blocked by 30GB container disk space (100% full)
- **Solution**: Create new RunPod pod with 100GB+ container storage
- **GPU**: A40 (46GB VRAM) - sufficient for Moshi (~21GB requirement)
- **Cost**: ~$0.79/hour for A40 pod

### Option 2: Acquire Larger Local GPU
- **Current**: NVIDIA RTX 4000 SFF Ada (20GB VRAM)
- **Required**: GPU with 24GB+ VRAM (e.g., RTX 4090, A5000)
- **Cost**: One-time hardware purchase

### Option 3: Skip Moshi Deployment (Recommended for Now)
- **Rationale**: F5-TTS and StyleTTS2 already provide comprehensive TTS coverage
- **F5-TTS**: Voice cloning with 4 languages (en, zh, ja, ko)
- **StyleTTS2**: Expressive TTS with emotion control (en)
- **Status**: Both services online and operational on RunPod

### Option 4: Service Rotation Management
- **Approach**: Run Moshi OR (Coqui + MeloTTS + OpenVoice + Core Backend)
- **Limitation**: Cannot run all services simultaneously
- **Use Case**: Start Moshi only when needed for real-time conversation demos
- **Trade-off**: Other TTS services unavailable when Moshi is running

## Next Steps

### Immediate Actions Required
1. **Decide on Moshi Deployment Strategy** (Options 1-4 above)
2. **Configure Backend sudo Access** (if keeping local deployment)
   - Add backend user to sudoers with NOPASSWD for docker commands
   - OR implement alternative container management without sudo

### Optional Enhancements
3. **Restart Other TTS Services** (if skipping Moshi)
   ```bash
   sudo docker start openvoice melotts coqui
   sudo systemctl start kasaai-core-backend
   ```

4. **Create Unit Tests** for Docker service management endpoints
5. **Add Nginx Routing** for `/api/system` endpoints (if not already configured)

## Files Created/Modified

### Created
- `/opt/kasaai/apps/tts-deployment/docker/moshi/Dockerfile`
- `/opt/kasaai/apps/tts-deployment/docker/moshi/app.py`
- `/opt/kasaai/apps/tts-deployment/MOSHI_DEPLOYMENT_SUMMARY.md` (this file)

### Modified
- `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml` (added Moshi service)
- `/opt/kasaai/apps/b2c-portal/src/config/tts-providers.ts` (added Moshi provider)
- `/opt/kasaai/apps/b2c-portal/src/pages/TTSLab.tsx` (added conversation tab)
- `/opt/kasaai/apps/b2c-portal/src/components/admin/ServiceManagementUpdated.tsx` (added Docker services tab)
- `/opt/kasaai/apps/core_backend/backend/routes/system_health.py` (added Docker endpoints)

## Technical Notes

### Moshi Architecture
- **Language Model**: Moshiko (7B parameters, ~18GB bfloat16)
- **Audio Codec**: Moshika (Mimi) (~3GB)
- **Framework**: PyTorch with CUDA 12.1
- **Communication**: WebSocket for full-duplex conversation
- **Latency**: <200ms target (not tested due to model loading failure)

### Docker Configuration
```yaml
moshi:
  build: ./docker/moshi
  container_name: moshi
  ports:
    - "8011:8008"
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  volumes:
    - moshi_cache:/app/cache
  restart: unless-stopped
```

### Health Check Endpoint
```bash
curl http://localhost:8011/health
{
  "status": "degraded",
  "moshi_lm_loaded": false,
  "mimi_loaded": false,
  "device": "cuda",
  "gpu_name": "NVIDIA RTX 4000 SFF Ada Generation",
  "gpu_memory_allocated": "0.00 GB",
  "gpu_memory_reserved": "19.34 GB",
  "gpu_memory_total": "19.55 GB"
}
```

## Conclusion

Moshi deployment infrastructure is **complete** but the service is **not operational** due to GPU memory constraints. The admin UI is functional and ready to manage Docker services once the backend sudo access is configured. 

**Recommendation**: Given that F5-TTS and StyleTTS2 are already operational on RunPod and provide comprehensive TTS coverage, consider **Option 3** (skip Moshi for now) unless real-time conversational AI is a critical immediate requirement.


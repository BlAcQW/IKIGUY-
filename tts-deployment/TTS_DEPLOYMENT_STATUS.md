# TTS Services Deployment Status

Last Updated: November 2, 2025

## Overview

This document tracks the deployment status of all Text-to-Speech services for the Kasaai platform.

## RunPod GPU Instance (194.68.245.121)

**Instance Details:**
- **GPU:** NVIDIA A40 (46GB VRAM)
- **Storage:** 200GB (70GB available)
- **SSH Port:** 22130
- **VRAM Used:** ~16.5GB total

### Services Running on RunPod

| Service | Status | Port | GPU Memory | Description |
|---------|--------|------|------------|-------------|
| **F5-TTS** | ✅ Online | 8002 | ~1.5GB | Flow-matching TTS with voice cloning |
| **StyleTTS2** | ✅ Online | 8004 | ~1.5GB | Expressive TTS with style transfer |
| **Moshi** | ✅ Online | 8006 | ~15GB | Real-time conversational AI (18GB LM + 3GB Mimi) |

### RunPod Access
```bash
# SSH to RunPod
ssh root@194.68.245.121 -p 22130

# Port forwarding for services
./tts-deployment/scripts/runpod_tunnels.sh
```

## Local Docker Services (Live Server)

**Server:** 148.251.0.46
**GPU:** NVIDIA GPU with 20GB VRAM
**VRAM Used:** ~4GB total

### Services Running Locally

| Service | Status | Port | GPU Memory | Description |
|---------|--------|------|------------|-------------|
| **Coqui XTTS** | ✅ Online | 8005 | ~2GB | Multilingual TTS (17 languages) with voice cloning |
| **MeloTTS** | ✅ Online | 8001 | ~1GB | Fast multilingual synthesis (6 languages) |
| **OpenVoice** | ✅ Online | 8003 | ~1GB | Voice cloning with emotion control (EN/ZH) |

### Docker Management
```bash
# Check service status
sudo docker ps

# View logs
sudo docker logs tts-deployment-coqui-1
sudo docker logs tts-deployment-melo-1
sudo docker logs tts-deployment-openvoice-1

# Restart services
cd /opt/kasaai/apps/tts-deployment
sudo docker-compose -f docker-compose.local.yml restart
```

## Service Health Endpoints

All services expose health endpoints for monitoring:

```bash
# RunPod services (via tunnel)
curl http://localhost:8002/health  # F5-TTS
curl http://localhost:8004/health  # StyleTTS2
curl http://localhost:8006/health  # Moshi

# Local services
curl http://localhost:8005/health  # Coqui XTTS
curl http://localhost:8001/health  # MeloTTS
curl http://localhost:8003/health  # OpenVoice
```

## Nginx Proxy Configuration

All services are proxied through Nginx with SSL:

- **F5-TTS:** https://f5tts.ailabsafrica.com
- **StyleTTS2:** https://styletts.ailabsafrica.com
- **Moshi:** https://moshi.ailabsafrica.com
- **Coqui XTTS:** https://coqui.ailabsafrica.com
- **MeloTTS:** https://melotts.ailabsafrica.com
- **OpenVoice:** https://openvoice.ailabsafrica.com

## Shared TTS Module

A unified TTS interface has been implemented in `/opt/kasaai/apps/shared/tts/` that provides:

- Unified client for all TTS providers
- Automatic provider selection
- Voice cloning support
- Real-time conversation (Moshi WebSocket)
- Batch processing
- Audio utilities (format conversion, normalization)
- Both sync and async clients

### Usage Example
```python
from shared.tts import TTSClient, TTSProvider

client = TTSClient()

# Synthesize with auto-selection
response = client.synthesize("Hello world!")

# Use specific provider
response = client.synthesize(
    "Hello from Coqui",
    provider=TTSProvider.COQUI_XTTS,
    language="en"
)
```

## Resource Allocation Summary

**Total GPU Memory Usage:**
- RunPod: ~16.5GB / 46GB (35% utilized)
- Local: ~4GB / 20GB (20% utilized)

**Service Distribution:**
- Heavy services (Moshi) on RunPod due to 15GB+ requirement
- Lighter services distributed locally to balance load
- All services accessible via HTTPS with SSL

## Notes

1. **Moshi Deployment:** Successfully deployed on RunPod on November 2, 2025 after resolving disk space issues (expanded from 30GB to 200GB).

2. **Local Services:** Coqui XTTS, MeloTTS, and OpenVoice are running locally in Docker containers and are fully operational.

3. **GPU Optimization:** Services are distributed between RunPod and local server to optimize GPU memory usage and ensure all services can run simultaneously.

4. **Monitoring:** All services have health endpoints that report status, GPU memory usage, and model loading state.
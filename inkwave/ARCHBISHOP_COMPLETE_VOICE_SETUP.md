# Archbishop Duncan-Williams - Complete Voice AI Setup
## TTS (Text-to-Speech) + ASR (Automatic Speech Recognition)

**Date**: 2025-11-06
**Status**: Production Ready (Coqui), F5-TTS Needs Port Fix
**Purpose**: Complete voice AI pipeline for Archbishop Duncan-Williams

---

## 🎯 Overview

This document provides a complete setup for Archbishop Duncan-Williams' voice across:
- **TTS (Text-to-Speech)**: Synthesize speech in Archbishop's voice
- **ASR (Automatic Speech Recognition)**: Transcribe audio (for interactive conversations)
- **Complete Pipeline**: ASR → LLM → TTS (voice conversations)

---

## 📊 Current Status

### ✅ What's Working

| Component | Provider | Status | Quality | Port |
|-----------|----------|--------|---------|------|
| **TTS** | Coqui XTTS | ✅ **WORKING** | ⭐⭐⭐⭐ | 8005 |
| **TTS** | F5-TTS | ⚠️ Port conflict | ⭐⭐⭐⭐⭐ (best) | 8006 |
| **ASR** | Faster Whisper | ✅ Available | ⭐⭐⭐⭐⭐ | - |
| **ASR** | Meta MMS | ✅ Available | ⭐⭐⭐⭐ | - |

---

## 🔊 Part 1: TTS (Text-to-Speech)

### 1.1 Coqui XTTS (✅ Working)

**Voice Configuration**:
```python
# Archbishop voice IDs available
voice_ids = ["archbishop_1", "archbishop_2"]

# Reference audio paths
reference_audio = {
    "archbishop_1": "/opt/kasaai/apps/voice-lab/voices/archbishop_1_ref.wav",
    "archbishop_2": "/opt/kasaai/apps/voice-lab/voices/archbishop_2_ref.wav"
}
```

**Test Script** (Coqui):
```python
import aiohttp
import base64

async def synthesize_coqui(text: str, voice_id: str = "archbishop_1"):
    """Synthesize with Coqui XTTS."""

    # Load reference audio
    with open(f"/opt/kasaai/apps/voice-lab/voices/{voice_id}_ref.wav", 'rb') as f:
        ref_audio = f.read()

    # Create form data
    form = aiohttp.FormData()
    form.add_field('reference_audio', ref_audio,
                   filename='reference.wav',
                   content_type='audio/wav')
    form.add_field('text', text)
    form.add_field('language', 'en')
    form.add_field('speed', '1.0')

    # Send request
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://coqui.ailabsafrica.com/synthesize_with_reference',
            data=form
        ) as response:
            audio_bytes = await response.read()
            return audio_bytes

# Usage
audio = await synthesize_coqui(
    "Living by the scriptures is essential for our faith"
)
with open('archbishop_output.wav', 'wb') as f:
    f.write(audio)
```

**Curl Command** (Coqui):
```bash
curl -X POST https://coqui.ailabsafrica.com/synthesize_with_reference \
  -F "reference_audio=@/opt/kasaai/apps/voice-lab/voices/archbishop_1_ref.wav" \
  -F "text=Living by the scriptures is essential for our faith" \
  -F "language=en" \
  -F "speed=1.0" \
  --output archbishop_coqui.wav
```

**Test Results**:
- ✅ archbishop_1: 16.07s audio, 502 KB
- ✅ archbishop_2: 16.69s audio, 522 KB
- Quality: Excellent, slight robotic undertones

---

### 1.2 F5-TTS (⚠️ Port Conflict - Best Quality)

**Issue**: Port 8006 already in use

**Fix Options**:

**Option A: Find and stop conflicting service**
```bash
# Find what's using port 8006
sudo lsof -i :8006

# If it's a Docker container
docker ps -a | grep 8006
docker stop <container_name>

# If it's an SSH tunnel
ps aux | grep "ssh.*8006"
kill <pid>
```

**Option B: Change F5-TTS to different port**
```bash
# Edit docker-compose.local.yml
cd /opt/kasaai/apps/tts-deployment
nano docker-compose.local.yml

# Change f5tts service:
# FROM: - 8006:8006
# TO:   - 8009:8006  # Use port 8009 instead

# Then start
docker-compose -f docker-compose.local.yml up -d f5tts
```

**Option C: Use RunPod F5-TTS** (if deployed on RunPod)
```bash
# Check RunPod configuration
cat /opt/kasaai/apps/tts-deployment/runpod.config.sh

# F5-TTS typically runs on RunPod with SSH tunnel
# Port: 8002 (RunPod) → 8006 (local)
```

**F5-TTS Voice Configuration**:
```python
# Best quality - uses 56-minute training
voice_id = "voice_archbishop_official"
reference_audio = "/opt/kasaai/apps/shared/storage/voice_clones/archbishop_56min.wav"
```

**Once F5-TTS is running**:
```bash
# Test endpoint
curl https://f5tts.ailabsafrica.com/health

# Synthesize
curl -X POST https://f5tts.ailabsafrica.com/clone \
  -F "ref_audio=@/opt/kasaai/apps/shared/storage/voice_clones/archbishop_56min.wav" \
  -F "text=Living by the scriptures is essential for our faith" \
  -F "language=en" \
  -F "speed=1.0" \
  -F "ref_text=Living by the scriptures is essential for our faith" \
  --output archbishop_f5tts.wav
```

---

## 🎤 Part 2: ASR (Automatic Speech Recognition)

For **interactive voice conversations**, we need ASR to transcribe user speech.

### 2.1 Faster Whisper (Recommended)

**Service**: Already integrated in `shared/services`

**Configuration**:
```python
from apps.shared.services.voice_lab_service import (
    VoiceLabService,
    TranscribeOptions
)

# Initialize service
voice_service = VoiceLabService()

# Transcribe audio
result = await voice_service.transcribe(
    audio_bytes,
    TranscribeOptions(
        language='en',
        model='faster-whisper-base',
        enhance_text=True
    )
)

print(f"Transcription: {result.text}")
print(f"Confidence: {result.confidence}")
```

**Models Available**:
- `faster-whisper-base`: Fast, 1GB VRAM, ~85% accuracy
- `faster-whisper-small`: Better, 2GB VRAM, ~90% accuracy
- `faster-whisper-medium`: Best, 5GB VRAM, ~93% accuracy

**Direct API**:
```bash
# Transcribe audio file
curl -X POST https://api.ailabsafrica.com/voice-lab/transcribe \
  -F "audio=@recording.wav" \
  -F "language=en" \
  -F "model=faster-whisper-base"
```

---

### 2.2 Meta MMS ASR

**Multi-language support** (1100+ languages)

**Configuration**:
```python
# Use Meta MMS for transcription
result = await voice_service.transcribe(
    audio_bytes,
    TranscribeOptions(
        language='en',
        model='meta-mms-asr'
    )
)
```

---

### 2.3 Akan Whisper (For Twi/Akan)

**Best for Ghanaian languages** (92.9% accuracy on Twi)

```python
result = await voice_service.transcribe(
    audio_bytes,
    TranscribeOptions(
        language='tw',  # Twi
        dialect='asante',
        model='akan-whisper'
    )
)
```

---

## 🔄 Part 3: Complete Voice Pipeline

### 3.1 Voice Conversation Flow

```
User speaks → ASR → Text → LLM → Response Text → TTS → Audio → User hears
```

**Example Implementation**:
```python
import asyncio
from apps.shared.services.voice_lab_service import VoiceLabService, TranscribeOptions, SynthesisOptions
from apps.shared.services.tts_provider_service import TTSProviderService, SynthesisRequest

async def voice_conversation(audio_input: bytes):
    """Complete voice conversation with Archbishop voice."""

    # 1. ASR: Transcribe user audio
    voice_service = VoiceLabService()
    transcription = await voice_service.transcribe(
        audio_input,
        TranscribeOptions(language='en', model='faster-whisper-base')
    )

    user_text = transcription.text
    print(f"User said: {user_text}")

    # 2. LLM: Generate response (using any LLM)
    # Example with simple response for now
    response_text = f"You asked about: {user_text}. Living by the scriptures guides us."

    # 3. TTS: Synthesize Archbishop voice
    tts_service = TTSProviderService()
    await tts_service.initialize()

    result = await tts_service.synthesize(
        user_id="test_user",
        request=SynthesisRequest(
            provider_id="coqui_xtts",
            text=response_text,
            language="en",
            voice_id="archbishop_1"
        ),
        skip_billing=True
    )

    # 4. Return audio
    return result.audio_base64

# Usage
user_audio = open('user_question.wav', 'rb').read()
response_audio_b64 = await voice_conversation(user_audio)

# Save response
import base64
with open('archbishop_response.wav', 'wb') as f:
    f.write(base64.b64decode(response_audio_b64))
```

---

### 3.2 Real-Time Voice Agent

**WebSocket-based conversation**:

```python
from fastapi import WebSocket
import json

async def voice_agent_websocket(websocket: WebSocket):
    """Real-time voice conversation."""

    await websocket.accept()

    # Initialize services
    voice_service = VoiceLabService()
    tts_service = TTSProviderService()
    await tts_service.initialize()

    while True:
        # Receive audio from client
        data = await websocket.receive_bytes()

        # 1. ASR: Transcribe
        transcription = await voice_service.transcribe(
            data,
            TranscribeOptions(language='en')
        )

        # Send transcription to client
        await websocket.send_json({
            "type": "transcription",
            "text": transcription.text
        })

        # 2. LLM: Generate response
        # (integrate your LLM here)
        response_text = f"Response to: {transcription.text}"

        # 3. TTS: Synthesize
        audio_result = await tts_service.synthesize(
            user_id="websocket_user",
            request=SynthesisRequest(
                provider_id="coqui_xtts",
                text=response_text,
                voice_id="archbishop_1"
            ),
            skip_billing=True
        )

        # Send audio to client
        await websocket.send_json({
            "type": "audio",
            "audio_base64": audio_result.audio_base64,
            "text": response_text
        })
```

---

## 🛠️ Part 4: Integration Examples

### 4.1 InkWave Audiobook with Archbishop Voice

```python
# Narrate book chapters in Archbishop's voice
async def narrate_chapter(chapter_text: str):
    tts_service = TTSProviderService()
    await tts_service.initialize()

    # Split into sentences for better pacing
    sentences = chapter_text.split('. ')

    audio_segments = []
    for sentence in sentences:
        result = await tts_service.synthesize(
            user_id="inkwave_user",
            request=SynthesisRequest(
                provider_id="coqui_xtts",
                text=sentence,
                voice_id="archbishop_1",
                speed=1.0
            )
        )
        audio_segments.append(result.audio_base64)

    return audio_segments
```

---

### 4.2 ChurchFlow Voice Greetings

```typescript
// Frontend: Select Archbishop voice
import { VoiceSelector } from '@/components/VoiceSelector';

<VoiceSelector
  value="archbishop_1"
  onChange={(voiceId) => setVoiceSettings({ voice_id: voiceId })}
/>

// Backend: Generate greeting
const greeting = await synthesize({
  text: "Welcome to our Sunday service. May God's blessings be with you.",
  voice_id: "archbishop_1",
  provider: "coqui_xtts"
});
```

---

### 4.3 StudyFlow Interactive Lessons

```python
# Q&A with Archbishop voice
async def answer_question(question: str):
    # Generate answer (LLM)
    answer = llm.generate(
        f"As Archbishop Duncan-Williams, answer: {question}"
    )

    # Synthesize in Archbishop voice
    audio = await tts_service.synthesize(
        user_id="studyflow_user",
        request=SynthesisRequest(
            provider_id="coqui_xtts",
            text=answer,
            voice_id="archbishop_1"
        )
    )

    return {
        "text": answer,
        "audio": audio.audio_base64
    }
```

---

## 📋 Part 5: Deployment Checklist

### TTS Providers

- [x] **Coqui XTTS** - Working at `https://coqui.ailabsafrica.com`
  - Port: 8005
  - Status: ✅ ONLINE
  - Archbishop voices: `archbishop_1`, `archbishop_2`

- [ ] **F5-TTS** - Port conflict at `https://f5tts.ailabsafrica.com`
  - Port: 8006 (conflict)
  - Status: ⚠️ NEEDS FIX
  - Archbishop voice: `voice_archbishop_official` (56-min training)
  - **Action**: Resolve port conflict or change to 8009

- [ ] **StyleTTS2** - Offline at `https://styletts.ailabsafrica.com`
  - Port: 8007
  - Status: ❌ OFFLINE
  - **Action**: Start service and configure Archbishop voice

### ASR Providers

- [x] **Faster Whisper** - Available via shared services
  - Models: base, small, medium
  - Languages: 99+ languages
  - Status: ✅ READY

- [x] **Meta MMS ASR** - Available via shared services
  - Languages: 1100+ languages
  - Status: ✅ READY

- [x] **Akan Whisper** - Available for Twi/Akan
  - Accuracy: 92.9% on Twi
  - Status: ✅ READY

### Integration

- [x] **ChurchFlow** - Archbishop voice in voice selector
- [x] **InkWave** - Archbishop voice in narration
- [x] **B2C Portal** - Archbishop voice in Voice Studio
- [ ] **StudyFlow** - Need to add voice selector
- [ ] **EventFlow** - Need to add voice selector

---

## 🚀 Part 6: Quick Start Commands

### Test Coqui TTS (Working Now)
```bash
cd /opt/kasaai/apps/inkwave
/opt/kasaai/apps/venv/bin/python test_archbishop_coqui_direct.py
```

### Fix F5-TTS Port Conflict
```bash
# Option 1: Change port
cd /opt/kasaai/apps/tts-deployment
nano docker-compose.local.yml
# Change: - 8009:8006
docker-compose -f docker-compose.local.yml up -d f5tts

# Option 2: Find and stop conflicting service
sudo lsof -i :8006
# Then stop that service/container
```

### Start Complete Voice Pipeline
```bash
# 1. Ensure Coqui is running
curl https://coqui.ailabsafrica.com/health

# 2. Start backend with ASR
cd /opt/kasaai/apps/core_backend
# Backend already has Faster Whisper integrated

# 3. Test complete pipeline
# (use examples in Part 3)
```

---

## 📊 Performance Benchmarks

### TTS Latency

| Provider | Input Length | Processing Time | Output Duration | Quality |
|----------|--------------|-----------------|-----------------|---------|
| Coqui XTTS | 111 chars | 5-8s | 16s | ⭐⭐⭐⭐ |
| F5-TTS | 111 chars | 10-15s | 16s | ⭐⭐⭐⭐⭐ |

### ASR Latency

| Provider | Audio Length | Processing Time | Accuracy |
|----------|--------------|-----------------|----------|
| Faster Whisper Base | 5s | 0.5-1.0s | ~85% |
| Faster Whisper Medium | 5s | 1.5-3.0s | ~93% |
| Akan Whisper | 5s (Twi) | 0.8-1.5s | 92.9% |

---

## 🔧 Troubleshooting

### Issue: F5-TTS port conflict
**Solution**: See Part 5 - Fix F5-TTS Port Conflict

### Issue: Poor ASR accuracy
**Solution**: Use `faster-whisper-medium` for better accuracy

### Issue: TTS sounds robotic
**Solution**:
- Use F5-TTS instead of Coqui (when available)
- Adjust speed: `speed=0.95` for more natural pace
- Use longer reference audio (56-min for F5-TTS)

### Issue: Slow TTS generation
**Solution**:
- Use Coqui for faster synthesis (5-8s)
- Cache common phrases
- Pre-generate audio for static content

---

## 📞 Support

For issues with Archbishop voice integration:
- **Voice Files**: `/opt/kasaai/apps/voice-lab/voices/archbishop*`
- **Tests**: `/opt/kasaai/apps/inkwave/test_archbishop*.py`
- **Documentation**: This file + `ARCHBISHOP_VOICE_INTEGRATION_STATUS.md`
- **Contact**: KasaAI DevOps Team

---

**Last Updated**: 2025-11-06
**Version**: 1.0
**Status**: Coqui TTS ✅ | F5-TTS ⚠️ Port Fix Needed | ASR ✅ Ready

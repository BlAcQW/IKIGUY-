# Twi Voice API Integration Guide

Complete guide for integrating Twi ASR+TTS into your applications.

## 📋 Overview

The Twi Voice API provides:
- ✅ **Text-to-Speech (TTS)**: Convert Twi text to natural speech
- ✅ **Speech-to-Text (ASR)**: Transcribe Twi audio to text
- ✅ **Full Conversation**: Complete ASR→TTS cycle for voice bots
- ✅ **High Quality**: Production-ready models trained on 894k samples
- ✅ **Low Latency**: <200ms typical response time via RunPod
- ✅ **Scalable**: Auto-scaling serverless infrastructure

## 🚀 Quick Start

### 1. Setup Backend

Add the new routes to your FastAPI app:

```python
# In apps/core_backend/backend/main.py

from backend.routes import twi_voice

# Add to your FastAPI app
app.include_router(twi_voice.router)
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key_here
RUNPOD_TTS_ENDPOINT_ID=your_melotts_endpoint_id
RUNPOD_ASR_ENDPOINT_ID=your_whisper_endpoint_id
```

### 3. Restart Backend

```bash
sudo systemctl restart kasaai-core-backend
```

### 4. Test Endpoints

```bash
# Health check
curl https://api.ailabsafrica.com/twi-voice/health

# TTS test
curl -X POST "https://api.ailabsafrica.com/twi-voice/tts/audio" \
  -F "text=Akwaaba! Ɛte sɛn?" \
  -o test_output.wav

# ASR test
curl -X POST "https://api.ailabsafrica.com/twi-voice/asr/upload" \
  -F "file=@test_audio.wav"
```

## 📚 API Reference

### Base URL

```
Production: https://api.ailabsafrica.com/twi-voice
Staging: https://staging-api.ailabsafrica.com/twi-voice
```

### Authentication

Currently, the API uses the same authentication as your core backend.
Future versions may include API key authentication for external clients.

---

## 🎤 Text-to-Speech (TTS)

### POST /twi-voice/tts

Convert Twi text to speech (returns JSON with base64 audio)

**Request Body:**
```json
{
  "text": "Akwaaba! Ɛte sɛn? Me din de Kofi.",
  "speaker": "TWI-Speaker",
  "speed": 1.0
}
```

**Response:**
```json
{
  "audio": "UklGRh4AAABXQVZFZm10...",
  "sample_rate": 44100,
  "duration": 3.5,
  "text": "Akwaaba! Ɛte sɛn? Me din de Kofi.",
  "speaker": "TWI-Speaker",
  "format": "base64"
}
```

**cURL Example:**
```bash
curl -X POST "https://api.ailabsafrica.com/twi-voice/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Akwaaba! Ɛte sɛn?",
    "speaker": "TWI-Speaker",
    "speed": 1.0
  }'
```

**Python Example:**
```python
import requests
import base64

response = requests.post(
    "https://api.ailabsafrica.com/twi-voice/tts",
    json={
        "text": "Akwaaba! Ɛte sɛn?",
        "speaker": "TWI-Speaker",
        "speed": 1.0
    }
)

data = response.json()
audio_bytes = base64.b64decode(data["audio"])

with open("output.wav", "wb") as f:
    f.write(audio_bytes)
```

### POST /twi-voice/tts/audio

Convert Twi text to speech (returns WAV audio file directly)

**Parameters:**
- `text` (form): Twi text to synthesize
- `speaker` (form, optional): Speaker ID
- `speed` (form, optional): Speech speed (0.5-2.0)

**Response:** WAV audio file

**cURL Example:**
```bash
curl -X POST "https://api.ailabsafrica.com/twi-voice/tts/audio" \
  -F "text=Meda wo ase! Me din de Kofi." \
  -F "speaker=TWI-Speaker" \
  -F "speed=1.0" \
  -o output.wav
```

**JavaScript Example:**
```javascript
async function textToSpeech(text) {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('speaker', 'TWI-Speaker');
  formData.append('speed', '1.0');

  const response = await fetch('https://api.ailabsafrica.com/twi-voice/tts/audio', {
    method: 'POST',
    body: formData
  });

  const audioBlob = await response.blob();
  const audioUrl = URL.createObjectURL(audioBlob);

  // Play audio
  const audio = new Audio(audioUrl);
  audio.play();
}
```

---

## 🎧 Speech-to-Text (ASR)

### POST /twi-voice/asr

Transcribe Twi speech to text (base64 audio input)

**Request Body:**
```json
{
  "audio": "UklGRh4AAABXQVZFZm10...",
  "language": "tw",
  "task": "transcribe",
  "return_timestamps": true,
  "vad_filter": true
}
```

**Response:**
```json
{
  "text": "Akwaaba! Ɛte sɛn? Me din de Kofi.",
  "segments": [
    {
      "start": 0.0,
      "end": 1.5,
      "text": "Akwaaba! Ɛte sɛn?",
      "words": [
        {"word": "Akwaaba", "start": 0.0, "end": 0.8, "probability": 0.98},
        {"word": "Ɛte", "start": 0.9, "end": 1.1, "probability": 0.95},
        {"word": "sɛn", "start": 1.2, "end": 1.5, "probability": 0.97}
      ]
    },
    {
      "start": 1.5,
      "end": 3.5,
      "text": "Me din de Kofi.",
      "words": [...]
    }
  ],
  "language": "tw",
  "language_probability": 0.99,
  "duration": 3.5,
  "num_segments": 2
}
```

### POST /twi-voice/asr/upload

Transcribe Twi speech to text (file upload)

**Parameters:**
- `file` (form): Audio file (WAV, MP3, FLAC, etc.)
- `language` (form, optional): Language code (default: "tw")
- `task` (form, optional): "transcribe" or "translate"
- `return_timestamps` (form, optional): Include timestamps

**Response:** Same as /asr endpoint

**cURL Example:**
```bash
curl -X POST "https://api.ailabsafrica.com/twi-voice/asr/upload" \
  -F "file=@input_audio.wav" \
  -F "language=tw" \
  -F "return_timestamps=true"
```

**Python Example:**
```python
import requests

with open("audio.wav", "rb") as f:
    files = {"file": f}
    data = {
        "language": "tw",
        "task": "transcribe",
        "return_timestamps": "true"
    }

    response = requests.post(
        "https://api.ailabsafrica.com/twi-voice/asr/upload",
        files=files,
        data=data
    )

result = response.json()
print(f"Transcription: {result['text']}")
print(f"Duration: {result['duration']:.2f}s")
print(f"Confidence: {result['language_probability']:.2%}")
```

---

## 💬 Full Conversation Endpoint

### POST /twi-voice/conversation

Complete ASR→TTS cycle for voice conversations

**Use Case:** Voice bot that:
1. Listens to user (ASR)
2. Processes request
3. Responds with speech (TTS)

**Parameters:**
- `file` (form): User audio input
- `response_text` (form, optional): Bot response text
- `speaker` (form, optional): TTS speaker
- `speed` (form, optional): TTS speed

**Response:**
```json
{
  "user_transcription": "Akwaaba! Ɛte sɛn?",
  "user_segments": [...],
  "user_duration": 2.5,
  "response_text": "Me ho yɛ! Me din de Ama.",
  "response_audio": "UklGRh4AAABXQVZF...",
  "response_sample_rate": 44100,
  "response_duration": 3.0,
  "conversation_id": "audio_1703001234"
}
```

**Example Workflow:**

```python
import requests
import base64

def voice_conversation(audio_file_path, bot_response_text=None):
    """Complete voice conversation cycle"""

    with open(audio_file_path, "rb") as f:
        files = {"file": f}
        data = {}

        if bot_response_text:
            data["response_text"] = bot_response_text

        response = requests.post(
            "https://api.ailabsafrica.com/twi-voice/conversation",
            files=files,
            data=data
        )

    result = response.json()

    print(f"User said: {result['user_transcription']}")
    print(f"Bot responded: {result['response_text']}")

    # Save bot's audio response
    audio_bytes = base64.b64decode(result["response_audio"])
    with open("bot_response.wav", "wb") as f:
        f.write(audio_bytes)

    return result


# Usage
result = voice_conversation(
    "user_audio.wav",
    bot_response_text="Meda wo ase! Me din de Kofi. Me betumi aboa wo?"
)
```

---

## 🔌 Frontend Integration

### React/TypeScript Example

```typescript
// hooks/useTwiVoice.ts
import { useState } from 'react';

interface TTSOptions {
  text: string;
  speaker?: string;
  speed?: number;
}

interface ASROptions {
  audioFile: File;
  language?: string;
  returnTimestamps?: boolean;
}

export function useTwiVoice() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const textToSpeech = async (options: TTSOptions): Promise<Blob> => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('text', options.text);
      if (options.speaker) formData.append('speaker', options.speaker);
      if (options.speed) formData.append('speed', options.speed.toString());

      const response = await fetch('/api/twi-voice/tts/audio', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('TTS failed');

      return await response.blob();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'TTS failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const speechToText = async (options: ASROptions): Promise<any> => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', options.audioFile);
      if (options.language) formData.append('language', options.language);
      if (options.returnTimestamps !== undefined) {
        formData.append('return_timestamps', options.returnTimestamps.toString());
      }

      const response = await fetch('/api/twi-voice/asr/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('ASR failed');

      return await response.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'ASR failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    textToSpeech,
    speechToText,
    loading,
    error
  };
}
```

**Component Example:**

```typescript
// components/TwiVoiceDemo.tsx
import React, { useState } from 'react';
import { useTwiVoice } from '../hooks/useTwiVoice';

export function TwiVoiceDemo() {
  const [text, setText] = useState('');
  const [transcription, setTranscription] = useState('');
  const { textToSpeech, speechToText, loading, error } = useTwiVoice();

  const handleTTS = async () => {
    try {
      const audioBlob = await textToSpeech({ text });
      const audioUrl = URL.createObjectURL(audioBlob);

      const audio = new Audio(audioUrl);
      audio.play();
    } catch (err) {
      console.error('TTS error:', err);
    }
  };

  const handleASR = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const result = await speechToText({ audioFile: file });
      setTranscription(result.text);
    } catch (err) {
      console.error('ASR error:', err);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3>Text-to-Speech</h3>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter Twi text..."
          className="border p-2 w-full"
        />
        <button
          onClick={handleTTS}
          disabled={loading}
          className="mt-2 bg-blue-500 text-white px-4 py-2 rounded"
        >
          {loading ? 'Generating...' : 'Speak'}
        </button>
      </div>

      <div>
        <h3>Speech-to-Text</h3>
        <input
          type="file"
          accept="audio/*"
          onChange={handleASR}
          className="border p-2"
        />
        {transcription && (
          <div className="mt-2 p-4 bg-gray-100 rounded">
            <strong>Transcription:</strong> {transcription}
          </div>
        )}
      </div>

      {error && (
        <div className="text-red-500">Error: {error}</div>
      )}
    </div>
  );
}
```

---

## 💰 Cost Estimates

Based on RunPod Serverless (RTX 4090 @ $0.34/hr):

| Request Type | Avg Time | Cost | Monthly (10k requests) |
|--------------|----------|------|------------------------|
| TTS (short) | 0.5s | $0.00005 | $0.50 |
| TTS (medium) | 1.5s | $0.00014 | $1.40 |
| ASR (short) | 0.3s | $0.00003 | $0.30 |
| ASR (medium) | 1.0s | $0.00009 | $0.90 |
| Conversation | 2.0s | $0.00019 | $1.90 |

**Total**: For 10k requests/month of each type = ~$5/month

---

## 🔒 Security & Rate Limiting

### Current Security

- Backend-to-RunPod communication uses API keys
- Same authentication as core backend
- HTTPS encryption

### Recommended Rate Limiting

```python
# Add to twi_voice.py

from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/tts")
@limiter.limit("100/minute")  # 100 requests per minute
async def text_to_speech(request: TTSRequest):
    ...
```

### Future Enhancements

- [ ] API key authentication for external clients
- [ ] Usage quotas per organization
- [ ] Cost tracking and billing integration
- [ ] Webhook notifications for errors

---

## 📊 Monitoring

### Key Metrics to Track

1. **Latency**
   - P50, P95, P99 response times
   - Target: <200ms for TTS, <150ms for ASR

2. **Error Rate**
   - Failed requests %
   - Target: <1%

3. **Cost**
   - Daily/monthly RunPod costs
   - Cost per request

4. **Usage**
   - Requests per day
   - Peak request rate

### Logging Example

```python
# Add to your service
import logging

logger = logging.getLogger(__name__)

# In each function
logger.info(f"TTS request: text_length={len(text)}, duration={duration}s")
logger.error(f"TTS error: {str(e)}", exc_info=True)
```

---

## 🧪 Testing

### Unit Tests

```python
# tests/test_twi_voice.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_tts_endpoint():
    """Test TTS endpoint"""
    response = client.post(
        "/twi-voice/tts",
        json={
            "text": "Akwaaba",
            "speaker": "TWI-Speaker",
            "speed": 1.0
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "audio" in data
    assert data["sample_rate"] == 44100
    assert data["text"] == "Akwaaba"

def test_asr_endpoint_upload(audio_file):
    """Test ASR upload endpoint"""
    with open("test_audio.wav", "rb") as f:
        response = client.post(
            "/twi-voice/asr/upload",
            files={"file": f},
            data={"language": "tw"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "segments" in data
    assert data["language"] == "tw"

def test_health_endpoint():
    """Test health check"""
    response = client.get("/twi-voice/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
```

---

## ✅ Integration Checklist

- [ ] Add routes to FastAPI app
- [ ] Configure environment variables
- [ ] Test all endpoints locally
- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Update API documentation
- [ ] Train team on new endpoints
- [ ] Set up monitoring/alerts
- [ ] Monitor costs for first week

---

## 📞 Support

- **Documentation**: This guide
- **API Docs**: https://api.ailabsafrica.com/docs#/Twi%20Voice
- **Issues**: Contact backend team
- **RunPod Support**: https://discord.gg/runpod

---

**Ready to integrate!** 🚀

Estimated setup time: **30 minutes**
Monthly cost (10k requests): **~$5**

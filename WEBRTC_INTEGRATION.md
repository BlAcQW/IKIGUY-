# WebRTC Integration Guide

## Overview

KasaAI now has a unified WebRTC voice integration using:

1. **Gradio FastRTC** (https://github.com/gradio-app/fastrtc) - For WebRTC communication
2. **HF Speech-to-Speech Pattern** (https://github.com/huggingface/speech-to-speech) - Pipeline architecture
3. **Shared Integration Module** (@shared/integration/webrtc.py) - Reusable across all apps

## Architecture

```
User Browser (WebRTC)
    ↓
FastRTC (automatic turn-taking)
    ↓
VoicePipeline (HF speech-to-speech pattern)
    ├─ VAD (Voice Activity Detection)
    ├─ STT (Speech-to-Text) - Whisper
    ├─ LLM (Language Model) - OpenAI/Anthropic/etc
    └─ TTS (Text-to-Speech) - Streaming
    ↓
FastRTC (audio streaming)
    ↓
User Browser (audio playback)
```

## Features

✅ **Low-latency voice conversations** (<50ms audio chunks)
✅ **Automatic turn-taking** (detects when user stops speaking)
✅ **Streaming TTS** (audio starts playing before full response generated)
✅ **Multi-language support** (English, Twi, Yoruba, and more)
✅ **Barge-in support** (user can interrupt assistant)
✅ **Gradio UI** for testing
✅ **Standard WebRTC** for custom frontends

## Installation

### 1. Install FastRTC

```bash
cd /opt/kasaai/apps/shared
pip install -e ".[voice]"
```

Or for core_backend specifically:

```bash
cd /opt/kasaai/apps/core_backend
pip install -r requirements.txt
```

This will install:
- `fastrtc[vad,tts]` - Core WebRTC library with voice activity detection
- Plus all dependencies (numpy, torch, etc.)

### 2. Verify Installation

```python
python3 -c "from fastrtc import Stream; print('✅ FastRTC installed')"
```

## Usage

### Quick Start (Any FastAPI App)

```python
from fastapi import FastAPI
from apps.shared.integration.webrtc import setup_webrtc

app = FastAPI()

# Add WebRTC voice functionality
setup_webrtc(
    app=app,
    assistant_id="your-assistant-id",
    mount_path="/voice/webrtc"
)
```

That's it! Your app now has WebRTC voice at `/voice/webrtc/`

### Advanced Usage

```python
from apps.shared.integration.webrtc import (
    setup_webrtc,
    create_webrtc_stream,
    WebRTCVoiceAgent
)

# Custom callbacks
def on_transcription(text: str):
    print(f"User said: {text}")

def on_response(text: str):
    print(f"Assistant responding: {text}")

# Setup with callbacks
setup_webrtc(
    app=app,
    assistant_id="your-assistant-id",
    pause_threshold_ms=1500,  # Pause detection (ms)
    ui_title="My Voice Assistant",
    ui_subtitle="Speak naturally...",
    on_transcription=on_transcription,
    on_response=on_response
)
```

### Frontend Integration

#### Option 1: Use Gradio UI (for testing)

Navigate to: `http://your-server/voice/webrtc/`

#### Option 2: Custom Frontend (React/TypeScript)

The existing frontend at `@b2c-portal/src/hooks/useWebRTCChat.ts` already works!

```typescript
import { useWebRTCChat } from '@/hooks/useWebRTCChat';

const {
  isConnected,
  isRecording,
  isSpeaking,
  startRecording,
  stopRecording
} = useWebRTCChat({
  assistantId: 'your-assistant-id',
  onTranscription: (text, isFinal) => console.log(text),
  onTextResponse: (text) => console.log(text)
});
```

## Configuration

### Environment Variables

```bash
# .env
DEFAULT_ASSISTANT_ID=your-assistant-id
```

### Assistant Configuration

In MongoDB `assistants` collection:

```json
{
  "id": "your-assistant-id",
  "name": "My Assistant",
  "system_prompt": "You are a helpful assistant...",
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "stt_provider": "whisper",
  "tts_provider": "parler",
  "voice_description": "A clear, friendly voice",
  "language": "en"
}
```

## Endpoints

After mounting at `/voice/webrtc`:

- **GET** `/voice/webrtc/` - Gradio UI for testing
- **POST** `/voice/webrtc/offer` - WebRTC SDP offer endpoint
- **GET** `/voice/webrtc/answer` - WebRTC SDP answer endpoint
- **WS** `/voice/webrtc/ws` - WebSocket fallback (if needed)

## Testing

### 1. Test with Gradio UI

```bash
# Start server
cd /opt/kasaai/apps/core_backend
uvicorn backend.main:app --reload --port 30027
```

Navigate to: `http://localhost:30027/voice/webrtc/`

### 2. Test with Frontend

```bash
# Start frontend
cd /opt/kasaai/apps/b2c-portal
npm run dev
```

Navigate to Voice Agent page, select assistant, click "Start Conversation", choose "WebRTC" mode.

### 3. Test Programmatically

```python
import asyncio
import numpy as np
from apps.shared.integration.webrtc import WebRTCVoiceAgent

async def test():
    agent = WebRTCVoiceAgent(
        assistant_id="test-assistant",
        pause_threshold_ms=1500
    )

    # Simulate audio input (16kHz, 3 seconds of silence)
    audio_data = np.zeros(16000 * 3, dtype=np.float32)
    sample_rate = 16000

    # Process audio
    for response_audio in agent((sample_rate, audio_data)):
        print(f"Got response audio: {len(response_audio[1])} samples")

asyncio.run(test())
```

## Troubleshooting

### FastRTC Not Installed

```
❌ Cannot setup WebRTC - fastrtc not installed
💡 Install with: pip install 'fastrtc[vad,tts]'
```

**Solution:**
```bash
pip install 'fastrtc[vad,tts]'
```

### Import Error

```
ImportError: cannot import name 'setup_webrtc' from 'apps.shared.integration.webrtc'
```

**Solution:**
```bash
# Reinstall shared module
cd /opt/kasaai/apps/shared
pip install -e .
```

### WebRTC Connection Failed

Check:
1. Server is running and accessible
2. CORS configured correctly in nginx
3. SSL certificates valid (WebRTC requires HTTPS)
4. Firewall allows WebRTC ports

### No Audio Output

Check:
1. TTS provider configured in assistant
2. Voice description set
3. Browser microphone permissions granted
4. Audio output not muted

## Architecture Details

### VoicePipeline (HF Speech-to-Speech Pattern)

Located at: `@shared/integration/voice_pipeline.py`

Stages:
1. **VAD** - Silero VAD v5 for voice activity detection
2. **STT** - Faster Whisper for transcription
3. **LLM** - Configurable (OpenAI, Anthropic, etc.)
4. **TTS** - Streaming TTS (Parler, F5, etc.)

### FastRTC Integration

Located at: `@shared/integration/webrtc.py`

Components:
- `WebRTCVoiceAgent` - Handles audio processing
- `create_webrtc_stream()` - Creates FastRTC stream
- `setup_webrtc()` - Mounts on FastAPI app

### Frontend Implementation

Located at: `@b2c-portal/src/hooks/useWebRTCChat.ts`

Uses standard WebRTC APIs:
- `RTCPeerConnection` - WebRTC connection
- `RTCDataChannel` - Control messages
- `getUserMedia()` - Microphone access
- Audio playback via Web Audio API

## Apps Using WebRTC

Currently integrated in:
- ✅ **core_backend** - Main API server
- 🔜 **developer_platform** - For developer testing
- 🔜 **studyflow** - Educational voice interactions
- 🔜 **churchflow** - Voice-based church services
- 🔜 **eventflow** - Voice event registration

To add to any app:

```python
from apps.shared.integration.webrtc import setup_webrtc

setup_webrtc(app, assistant_id="app-specific-assistant")
```

## Performance

Expected latencies:
- **First audio chunk**: <500ms (TTS start)
- **Audio streaming**: <50ms chunks
- **End-to-end response**: 1-3 seconds (depends on LLM)
- **Pause detection**: ~200ms after user stops

## Security

WebRTC requires:
- ✅ HTTPS (SSL/TLS)
- ✅ Authentication (Bearer tokens)
- ✅ CORS properly configured
- ✅ Rate limiting on endpoints

## Contributing

To improve the WebRTC integration:

1. Edit: `@shared/integration/webrtc.py`
2. Test in multiple apps
3. Update this documentation
4. Create pull request

## References

- [Gradio FastRTC](https://github.com/gradio-app/fastrtc)
- [HF Speech-to-Speech](https://github.com/huggingface/speech-to-speech)
- [WebRTC Standard](https://webrtc.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-core-backend -f`
- GitHub Issues: https://github.com/kasaai/core
- Email: team@kasaai.com

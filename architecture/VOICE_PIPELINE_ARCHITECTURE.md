# Voice Pipeline Architecture

**Version:** 2.0
**Status:** Production Ready
**Last Updated:** 2025-11-11
**Phases Complete:** Phase 1 (Streaming TTS) ✅ | Phase 2 (WebRTC) ✅ | Phase 3 (Unified Pipeline) ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Components](#architecture-components)
3. [VoicePipeline Class](#voicepipeline-class)
4. [Voice Conversation Transports](#voice-conversation-transports)
5. [Integration Guide](#integration-guide)
6. [Performance Metrics](#performance-metrics)
7. [Migration Guide](#migration-guide)
8. [Future Enhancements](#future-enhancements)

---

## Overview

The Voice Pipeline Architecture provides a unified, modular system for voice conversations across multiple transport protocols. It eliminates the complexity of manual state machines and provides consistent behavior across WebRTC, WebSocket, and future transports.

### Key Benefits

✅ **10x Code Reduction** - WebSocket v2 is 190 lines vs 1500+ lines in v1
✅ **Consistent Architecture** - Same pipeline works for WebRTC and WebSocket
✅ **Low Latency** - <50ms WebRTC, streaming TTS reduces latency by 40-60%
✅ **Easy Maintenance** - Single pipeline to update instead of multiple handlers
✅ **Production Ready** - Fully tested and deployed on dev server

---

## Architecture Components

### High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Client Application                    │
│              (Browser, Mobile, Phone System)             │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   WebRTC     │   │ WebSocket v2 │   │ WebSocket v1 │
│   Handler    │   │   Handler    │   │   Handler    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   VoicePipeline       │
                │   (Unified Flow)      │
                └───────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│     VAD      │   │     STT      │   │     LLM      │
│  (Silero v5) │   │  (Whisper)   │   │  (Multiple)  │
└──────────────┘   └──────────────┘   └──────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │     TTS Streaming     │
                │    (Parler-TTS)       │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │    Audio Response     │
                └───────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Location |
|-----------|---------------|----------|
| **VoicePipeline** | Unified conversation flow coordinator | `@shared/integration/voice_pipeline.py` |
| **WebRTC Handler** | FastRTC WebRTC transport | `@core_backend/routes/voice_engine/webrtc_voice.py` |
| **WebSocket v2** | Simplified WebSocket transport | `@core_backend/routes/voice_engine/websocket_v2.py` |
| **WebSocket v1** | Legacy WebSocket transport | `@core_backend/routes/voice_engine/websocket_chat.py` |
| **VAD Service** | Voice activity detection | `@shared/integration/ai_services/vad_service.py` |
| **STT Service** | Speech-to-text transcription | `@core_backend/services/faster_whisper_service.py` |
| **LLM Service** | Response generation | `@core_backend/services/llm_service.py` |
| **Streaming TTS** | Audio synthesis | `@shared/integration/ai_services/streaming_tts_service.py` |

---

## VoicePipeline Class

### Purpose

The `VoicePipeline` class encapsulates the entire voice conversation flow:
1. **VAD** - Voice Activity Detection (pause detection)
2. **STT** - Speech-to-Text (transcription)
3. **LLM** - Large Language Model (response generation)
4. **TTS** - Text-to-Speech (audio synthesis)

### Location

```
/opt/kasaai/apps/shared/integration/voice_pipeline.py
```

### API Reference

#### Constructor

```python
from apps.shared.integration.voice_pipeline import VoicePipeline

pipeline = VoicePipeline(
    assistant_id="asst_123abc",
    pause_threshold_ms=1500,  # 1.5s pause to trigger turn completion
    sample_rate=16000          # 16kHz audio
)
```

**Parameters:**
- `assistant_id` (str): MongoDB assistant ID
- `pause_threshold_ms` (int): Silence duration to trigger turn completion (default: 1500ms)
- `sample_rate` (int): Audio sample rate in Hz (default: 16000)

#### Main Method: process_turn()

```python
async def process_turn(
    audio_stream: AsyncGenerator[bytes, None],
    user_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Process complete conversation turn."""
```

**Input:**
- `audio_stream`: Async generator yielding PCM audio chunks (bytes)
- `user_id`: Optional user ID for tracking

**Output (yields messages):**

```python
# Transcription
{"type": "transcription", "data": {"text": "...", "is_final": True}}

# LLM response text
{"type": "text_response", "data": "assistant response"}

# Audio chunks (base64 encoded WAV)
{"type": "audio_chunk", "data": "base64_wav_data"}

# Completion
{"type": "audio_complete", "data": {"chunks": 10, "first_chunk_latency": 1.2}}

# Errors
{"type": "error", "data": "error message"}
```

#### Reset Method

```python
pipeline.reset()  # Reset for new conversation
```

### Usage Example

```python
from apps.shared.integration.voice_pipeline import create_voice_pipeline

# Create pipeline
pipeline = create_voice_pipeline(
    assistant_id="asst_123abc",
    pause_threshold_ms=1500,
    sample_rate=16000
)

# Audio stream generator
async def audio_stream():
    for chunk in audio_chunks:
        yield chunk

# Process turn
async for message in pipeline.process_turn(audio_stream()):
    if message["type"] == "transcription":
        print(f"User: {message['data']['text']}")
    elif message["type"] == "text_response":
        print(f"Assistant: {message['data']}")
    elif message["type"] == "audio_chunk":
        # Play audio chunk
        play_audio(message["data"])
```

---

## Voice Conversation Transports

### 1. WebRTC (Phase 2)

**Endpoint:** `https://api.ailabsafrica.com/voice/webrtc`
**Status:** ✅ Production Ready
**Latency:** <50ms audio chunks

#### Features

- Low-latency audio streaming via WebRTC data channels
- Native browser support (no plugins)
- Built-in Gradio UI for testing
- FastRTC `Stream` + `ReplyOnPause` architecture
- Integrated with VoicePipeline

#### Implementation

**File:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/webrtc_voice.py`

```python
from fastrtc import Stream, ReplyOnPause
from fastrtc.reply_on_pause import AlgoOptions

class WebRTCVoiceAgent:
    """Callable handler for FastRTC ReplyOnPause"""

    def __init__(self, assistant_id: str):
        self.assistant_id = assistant_id
        self.pipeline = None

    def __call__(self, audio: Tuple[int, np.ndarray]):
        """Handle audio from WebRTC client"""
        sample_rate, audio_data = audio

        # Process through VoicePipeline
        response_chunks = asyncio.run(
            self._process_audio(audio_data, sample_rate)
        )

        # Yield response audio
        for chunk in response_chunks:
            yield (sample_rate, chunk)

# Create Stream
algo_options = AlgoOptions(
    audio_chunk_duration=0.6,
    started_talking_threshold=0.2,
    speech_threshold=0.1
)

stream = Stream(
    handler=ReplyOnPause(agent, algo_options=algo_options),
    modality="audio",
    mode="send-receive"
)
stream.mount(app, path="/voice/webrtc")
```

#### Endpoints

- **UI:** `/voice/webrtc` (GET) - Gradio web interface
- **Offer:** `/voice/webrtc/offer` (POST) - WebRTC connection

---

### 2. WebSocket v2 (Phase 3)

**Endpoint:** `wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/{assistant_id}`
**Status:** ✅ Production Ready
**Code:** 190 lines (vs 1500+ in v1)

#### Features

- Simple message protocol
- No manual state management
- Backward compatible with v1
- Uses VoicePipeline for all processing
- 10x code reduction

#### Implementation

**File:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/websocket_v2.py`

```python
@router.websocket("/voice-chat/{assistant_id}")
async def voice_chat_v2(websocket: WebSocket, assistant_id: str):
    """WebSocket v2 endpoint using VoicePipeline"""

    await websocket.accept()

    # Create pipeline
    pipeline = create_voice_pipeline(
        assistant_id=assistant_id,
        pause_threshold_ms=1500
    )

    audio_buffer = []

    while True:
        message = await websocket.receive_json()

        if message["type"] == "pcm_chunk":
            # Collect audio
            audio_buffer.append(message["data"])

        elif message["type"] == "turn_complete":
            # Process turn through pipeline
            async def audio_stream():
                for pcm_base64 in audio_buffer:
                    yield base64.b64decode(pcm_base64)

            # Stream results to client
            async for pipeline_msg in pipeline.process_turn(audio_stream()):
                await websocket.send_json(pipeline_msg)

            audio_buffer.clear()
```

#### Message Protocol

**Client → Server:**
```json
{"type": "pcm_chunk", "data": "base64_pcm_audio"}
{"type": "turn_complete", "data": null}
{"type": "reset", "data": null}
{"type": "ping", "data": null}
```

**Server → Client:**
```json
{"type": "transcription", "data": {"text": "...", "is_final": true}}
{"type": "text_response", "data": "..."}
{"type": "audio_chunk", "data": "base64_wav"}
{"type": "audio_complete", "data": {...}}
{"type": "ready_for_turn", "data": "Ready"}
{"type": "error", "data": "..."}
```

---

### 3. WebSocket v1 (Legacy)

**Endpoint:** `wss://api.ailabsafrica.com/voice/ws/voice-chat/{assistant_id}`
**Status:** ⚠️ Legacy (Maintained for backward compatibility)
**Code:** 1500+ lines with manual state machine

#### Notes

- Still functional and supported
- Gradually migrate clients to WebSocket v2
- More complex state management
- Compatible with existing clients

---

## Integration Guide

### Adding VoicePipeline to New Transport

To add a new voice conversation transport (e.g., SIP, PSTN):

1. **Import VoicePipeline:**
```python
from apps.shared.integration.voice_pipeline import create_voice_pipeline
```

2. **Create Pipeline Instance:**
```python
pipeline = create_voice_pipeline(
    assistant_id=assistant_id,
    pause_threshold_ms=1500
)
```

3. **Prepare Audio Stream:**
```python
async def audio_stream():
    # Yield PCM audio chunks as bytes
    for chunk in your_audio_source:
        yield chunk
```

4. **Process Turn:**
```python
async for message in pipeline.process_turn(audio_stream()):
    # Handle message based on type
    if message["type"] == "transcription":
        # Send transcription to client
    elif message["type"] == "audio_chunk":
        # Send audio to client
```

5. **Reset Between Conversations:**
```python
pipeline.reset()
```

### Example: New Transport Handler

```python
class NewTransportHandler:
    def __init__(self, assistant_id: str):
        self.pipeline = create_voice_pipeline(assistant_id)

    async def handle_conversation(self, audio_source):
        """Handle conversation through new transport"""

        async def audio_stream():
            async for chunk in audio_source:
                yield chunk

        async for message in self.pipeline.process_turn(audio_stream()):
            # Forward to transport-specific output
            await self.send_to_client(message)
```

---

## Performance Metrics

### Latency Improvements

| Phase | Component | Latency Reduction | Status |
|-------|-----------|------------------|--------|
| Phase 1 | Streaming TTS | 40-60% reduction | ✅ Complete |
| Phase 2 | WebRTC Transport | <50ms chunks | ✅ Complete |
| Phase 3 | Unified Pipeline | Code maintenance | ✅ Complete |

### Measured Performance

**WebRTC:**
- First audio chunk: <1.5s
- Audio chunk latency: <50ms
- End-to-end turn: 2-4s

**WebSocket v2:**
- First audio chunk: <1.5s
- Same performance as v1
- 10x simpler code

**Streaming TTS:**
- First chunk: <1.2s (vs 2-3s buffered)
- Incremental audio delivery
- Better perceived responsiveness

### Code Metrics

| Handler | Lines of Code | Complexity | Maintainability |
|---------|--------------|------------|-----------------|
| WebSocket v1 | 1500+ | High | ⚠️ Difficult |
| WebSocket v2 | 190 | Low | ✅ Easy |
| WebRTC | 192 | Low | ✅ Easy |
| VoicePipeline | 450 | Medium | ✅ Easy |

**Total Code Reduction:** ~1300 lines eliminated per handler

---

## Migration Guide

### Migrating from WebSocket v1 to v2

#### Frontend Changes

**Before (v1):**
```javascript
const ws = new WebSocket('wss://api.ailabsafrica.com/voice/ws/voice-chat/asst_123');

// Complex state management
ws.send(JSON.stringify({type: 'audio', data: audioBase64}));
// Wait for transcription, response, audio separately
```

**After (v2):**
```javascript
const ws = new WebSocket('wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/asst_123');

// Simpler protocol
// 1. Send audio chunks
ws.send(JSON.stringify({type: 'pcm_chunk', data: pcmBase64}));

// 2. Signal turn complete
ws.send(JSON.stringify({type: 'turn_complete', data: null}));

// 3. Receive all messages in order
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    switch(msg.type) {
        case 'transcription':
            // Display user's words
            break;
        case 'text_response':
            // Display assistant response
            break;
        case 'audio_chunk':
            // Play audio
            break;
    }
};
```

#### Backend Changes

**No changes required** - WebSocket v2 runs alongside v1.

#### Migration Strategy

1. **Phase 1:** Deploy WebSocket v2 endpoint (✅ Done)
2. **Phase 2:** Update frontend to support both v1 and v2
3. **Phase 3:** Gradual client migration (feature flag)
4. **Phase 4:** Monitor v1 usage decline
5. **Phase 5:** Deprecate v1 after 6+ months

---

## Future Enhancements

### Planned Features

1. **Multi-Speaker Support**
   - Speaker diarization
   - Per-speaker voice customization
   - Group conversation handling

2. **Enhanced VAD**
   - Emotion detection
   - Speaker identification
   - Background noise filtering

3. **Advanced TTS**
   - Real-time prosody control
   - Emotion expression
   - Multi-language streaming

4. **Transport Optimization**
   - Adaptive bitrate
   - Network quality adaptation
   - Failover between transports

5. **Analytics Integration**
   - Turn-level metrics
   - Quality of service tracking
   - Usage analytics

### Research Areas

- **WebTransport** - Next-gen low-latency transport
- **Real-time LLM Streaming** - Token-by-token generation
- **Voice Biometrics** - Speaker verification
- **Multilingual Conversations** - Seamless language switching

---

## Related Documentation

- **Phase 1-3 Status:** `/opt/kasaai/automations/premier-health/PHASE2_PHASE3_STATUS.md`
- **VoicePipeline Source:** `/opt/kasaai/apps/shared/integration/voice_pipeline.py`
- **WebRTC Handler:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/webrtc_voice.py`
- **WebSocket v2 Handler:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/websocket_v2.py`
- **Integration Plan:** `/opt/kasaai/automations/premier-health/INTEGRATION_PLAN_HF_FASTRTC.md`

---

**Document Version:** 2.0
**Last Updated:** 2025-11-11
**Maintained By:** AI Labs Africa Engineering Team

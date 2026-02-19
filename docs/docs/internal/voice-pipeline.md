# Voice Pipeline Architecture (Internal)

## Overview

This document provides internal technical details about the Voice Pipeline architecture implemented in Phases 1-3. It's intended for KasaAI engineers who need to understand, maintain, or extend the voice conversation system.

## Status

- **Phase 1:** Streaming TTS + torch.compile ✅ Complete
- **Phase 2:** FastRTC WebRTC Integration ✅ Complete
- **Phase 3:** Unified VoicePipeline ✅ Complete
- **Overall Progress:** 100%
- **Production Status:** Deployed on dev server (85.214.12.174)

## Architecture Overview

The Voice Pipeline provides a unified conversation flow that eliminates manual state machine complexity:

```
VAD → STT → LLM → TTS (Streaming)
```

### Component Stack

| Layer | Component | Location | Purpose |
|-------|-----------|----------|---------|
| **Transport** | WebRTC, WebSocket v2, WebSocket v1 | `@core_backend/routes/voice_engine/` | Handle client connections |
| **Pipeline** | VoicePipeline | `@shared/integration/voice_pipeline.py` | Unified conversation flow |
| **VAD** | Silero v5 | `@shared/integration/ai_services/vad_service.py` | Voice activity detection |
| **STT** | Faster Whisper | `@core_backend/services/faster_whisper_service.py` | Speech-to-text |
| **LLM** | Multiple (OpenAI, Gemini, etc.) | `@core_backend/services/llm_service.py` | Response generation |
| **TTS** | Parler-TTS (streaming) | `@shared/integration/ai_services/streaming_tts_service.py` | Text-to-speech |

## File Locations

### Core Implementation

```
/opt/kasaai/apps/
├── shared/integration/
│   ├── voice_pipeline.py              # Main VoicePipeline class (450 lines)
│   └── ai_services/
│       ├── vad_service.py             # VAD with Silero v5
│       └── streaming_tts_service.py   # Streaming TTS
│
├── core_backend/backend/
│   ├── routes/voice_engine/
│   │   ├── webrtc_voice.py           # WebRTC handler (192 lines)
│   │   ├── websocket_v2.py           # WebSocket v2 handler (190 lines)
│   │   └── websocket_chat.py         # WebSocket v1 (legacy, 1500+ lines)
│   │
│   └── services/
│       ├── faster_whisper_service.py  # STT service
│       ├── llm_service.py             # LLM service
│       └── pcm_vad_handler.py         # PCM audio utilities
│
└── automations/premier-health/
    ├── PHASE2_PHASE3_STATUS.md        # Implementation status
    └── INTEGRATION_PLAN_HF_FASTRTC.md # Original integration plan
```

### Documentation

```
/opt/kasaai/apps/
├── architecture/
│   └── VOICE_PIPELINE_ARCHITECTURE.md  # Public architecture doc
│
├── shared/
│   └── INTEGRATION_GUIDE.md            # Integration guide
│
├── developer_platform/
│   └── API_DOCUMENTATION.md            # API reference
│
└── docs/docs/internal/
    └── voice-pipeline.md               # This file
```

## Implementation Details

### VoicePipeline Class

**Location:** `/opt/kasaai/apps/shared/integration/voice_pipeline.py`

```python
class VoicePipeline:
    """
    Unified voice conversation pipeline.
    Handles: VAD → STT → LLM → TTS streaming
    """

    def __init__(
        self,
        assistant_id: str,
        pause_threshold_ms: int = 1500,
        sample_rate: int = 16000
    ):
        self.assistant_id = assistant_id
        self.pause_threshold = pause_threshold_ms
        self.sample_rate = sample_rate

        # Lazy-loaded components
        self.assistant = None
        self.vad_session = None
        self.whisper_service = None
        self.streaming_tts = None

    async def process_turn(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process complete conversation turn"""
        # 1. Collect audio with VAD
        utterance_audio = await self._collect_utterance(audio_stream)

        # 2. Transcribe (STT)
        transcription = await self._transcribe(utterance_audio)
        yield {"type": "transcription", "data": {...}}

        # 3. Generate response (LLM)
        response_text = await self._generate_response(transcription)
        yield {"type": "text_response", "data": response_text}

        # 4. Stream TTS
        async for audio_chunk in self._stream_tts(response_text):
            yield {"type": "audio_chunk", "data": audio_base64}

        yield {"type": "audio_complete", "data": {...}}
```

### WebRTC Handler

**Location:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/webrtc_voice.py`

Uses FastRTC's `Stream` + `ReplyOnPause` pattern:

```python
class WebRTCVoiceAgent:
    """Callable handler for FastRTC"""

    def __call__(self, audio: Tuple[int, np.ndarray]):
        """
        Handle audio from WebRTC client.
        Called by ReplyOnPause when user pauses speaking.
        """
        sample_rate, audio_data = audio

        # Process through VoicePipeline (synchronously)
        response_chunks = asyncio.run(
            self._process_audio(audio_data, sample_rate)
        )

        # Yield response audio
        for chunk in response_chunks:
            yield (sample_rate, chunk)
```

**Key API Details:**
- `ReplyOnPause` requires `AlgoOptions` for pause detection config
- Handler signature: `(sample_rate, np.ndarray) → yields (sample_rate, np.ndarray)`
- Uses `asyncio.run()` to bridge sync handler and async VoicePipeline

### WebSocket v2 Handler

**Location:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/websocket_v2.py`

Simplified message-based protocol:

```python
@router.websocket("/voice-chat/{assistant_id}")
async def voice_chat_v2(websocket: WebSocket, assistant_id: str):
    """WebSocket v2 endpoint using VoicePipeline"""

    pipeline = create_voice_pipeline(assistant_id)
    audio_buffer = []

    while True:
        message = await websocket.receive_json()

        if message["type"] == "pcm_chunk":
            audio_buffer.append(message["data"])

        elif message["type"] == "turn_complete":
            # Process turn through pipeline
            async def audio_stream():
                for pcm_base64 in audio_buffer:
                    yield base64.b64decode(pcm_base64)

            async for pipeline_msg in pipeline.process_turn(audio_stream()):
                await websocket.send_json(pipeline_msg)

            audio_buffer.clear()
```

## Development Guidelines

### Adding New Voice Transport

To add a new transport (e.g., SIP, PSTN):

1. Create handler file in `@core_backend/routes/voice_engine/`
2. Import VoicePipeline:
   ```python
   from apps.shared.integration.voice_pipeline import create_voice_pipeline
   ```
3. Create pipeline instance for assistant
4. Prepare async audio stream generator
5. Process turns through `pipeline.process_turn()`
6. Handle yielded messages (transcription, text_response, audio_chunk, etc.)

### Extending VoicePipeline

Override internal methods for custom behavior:

```python
class CustomVoicePipeline(VoicePipeline):
    async def _transcribe(self, audio: np.ndarray) -> str:
        """Custom transcription logic"""
        # Your implementation
        pass

    async def _generate_response(self, text: str) -> str:
        """Custom response generation"""
        # Your implementation
        pass
```

### Testing

**Unit Tests:** Create tests in `@core_backend/tests/test_voice_pipeline.py`

```python
import pytest
from apps.shared.integration.voice_pipeline import create_voice_pipeline

@pytest.mark.asyncio
async def test_voice_pipeline_process_turn():
    """Test complete turn processing"""
    pipeline = create_voice_pipeline("test-assistant")

    async def audio_stream():
        # Yield test audio chunks
        yield test_audio_chunk

    messages = []
    async for msg in pipeline.process_turn(audio_stream()):
        messages.append(msg)

    # Assert message types and order
    assert messages[0]["type"] == "transcription"
    assert messages[1]["type"] == "text_response"
    assert messages[2]["type"] == "audio_chunk"
```

**Integration Tests:** Test with real WebRTC/WebSocket clients

### Common Issues and Solutions

#### Issue: Import Errors

**Problem:** `ModuleNotFoundError: No module named 'apps.voice_lab'`

**Solution:** Use correct import path:
```python
from apps.core_backend.backend.services.pcm_vad_handler import pcm_to_wav
```

#### Issue: FastRTC API Mismatch

**Problem:** `ImportError: cannot import name 'RTCApp'`

**Solution:** Use correct FastRTC API:
```python
from fastrtc import Stream, ReplyOnPause
from fastrtc.reply_on_pause import AlgoOptions

# Correct API
stream = Stream(
    handler=ReplyOnPause(agent, algo_options=AlgoOptions(...)),
    modality="audio"
)
```

#### Issue: VAD Not Detecting Speech

**Solution:** Adjust pause threshold:
```python
pipeline = create_voice_pipeline(
    assistant_id=assistant_id,
    pause_threshold_ms=800  # Lower for faster detection
)
```

## Deployment

### Dev Server (85.214.12.174)

**Services:**
- WebRTC: `https://api.ailabsafrica.com/voice/webrtc`
- WebSocket v2: `wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/{assistant_id}`
- WebSocket v1: `wss://api.ailabsafrica.com/voice/ws/voice-chat/{assistant_id}`

**Backend Service:**
```bash
sudo systemctl status kasaai-core-backend
sudo systemctl restart kasaai-core-backend
sudo journalctl -u kasaai-core-backend -f
```

### Configuration

**Environment Variables:**
- `DEFAULT_ASSISTANT_ID`: Default assistant for WebRTC (optional)
- Standard MongoDB, Supabase, API keys

**Dependencies:**
```txt
fastrtc==0.0.33
aiortc==1.14.0
silero-vad>=5.0.0
faster-whisper>=0.10.0
parler-tts>=0.1.0
```

### Monitoring

**Key Metrics:**
- First audio chunk latency (<1.5s target)
- End-to-end turn time (2-4s target)
- Active WebRTC/WebSocket connections
- GPU memory usage (~2GB per conversation)

**Logs:**
```bash
# View WebRTC logs
sudo journalctl -u kasaai-core-backend -f | grep WebRTC

# View VoicePipeline logs
sudo journalctl -u kasaai-core-backend -f | grep VoicePipeline
```

## Performance Optimization

### Latency Reduction Strategies

1. **Streaming TTS (Phase 1):** 40-60% latency reduction
   - Stream audio chunks incrementally
   - No buffering required

2. **WebRTC Transport (Phase 2):** <50ms audio chunk latency
   - Native WebRTC data channels
   - No WebSocket overhead

3. **GPU Acceleration:**
   - STT: Faster Whisper on CUDA
   - TTS: Parler-TTS on CUDA
   - ~2GB VRAM per conversation

### Code Optimization

**Before (WebSocket v1):**
- 1500+ lines with manual state machine
- Complex state transitions
- Difficult to maintain

**After (WebSocket v2 with VoicePipeline):**
- 190 lines (10x reduction)
- No manual state management
- Easy to maintain and extend

## Future Enhancements

### Planned (Phase 4+)

1. **WebTransport:** Next-gen low-latency transport
2. **Real-time LLM Streaming:** Token-by-token generation
3. **Multi-speaker Support:** Speaker diarization
4. **Enhanced VAD:** Emotion detection, background noise filtering
5. **Voice Biometrics:** Speaker verification

### Research Areas

- WebTransport for sub-10ms latency
- Real-time prosody control
- Multilingual conversation switching
- Edge deployment (WebAssembly, mobile SDKs)

## Support and Questions

**Internal Support:**
- Slack: #voice-engine-dev
- Email: engineering@ailabsafrica.com
- Documentation: This file + related docs

**External Resources:**
- FastRTC Docs: https://fastrtc.org
- Silero VAD: https://github.com/snakers4/silero-vad
- Faster Whisper: https://github.com/guillaumekln/faster-whisper

---

**Last Updated:** 2025-11-11
**Maintained By:** AI Labs Africa Engineering Team
**Version:** 2.0

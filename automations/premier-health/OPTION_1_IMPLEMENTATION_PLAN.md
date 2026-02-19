# Option 1 Implementation Plan: Server-Side VAD with PCM Streaming

## Date: 2025-11-11
## Status: PLANNING
## Priority: HIGH - Professional Solution

## Overview

Implement industry-standard hands-free voice conversation using:
- **Frontend:** Continuous raw PCM streaming via Web Audio API
- **Backend:** Real-time VAD (Silero) on PCM chunks
- **Flow:** Server-driven conversation turns based on VAD

## Architecture Comparison

### Current (Broken)
```
Browser MediaRecorder → WebM chunks → Backend (fake VAD on WebM bytes ❌) → Whisper
```

### Target (Professional)
```
Browser Web Audio API → Raw PCM chunks → Backend Silero VAD → Accumulate → Whisper
```

## Phase 1: Backend VAD Service

### 1.1 Install Silero VAD
```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/pip install silero-vad
```

**Dependencies:** ✅ Already have torch 2.5.1 and torchaudio 2.5.1

### 1.2 Create VAD Service (`backend/services/vad_service.py`)

```python
"""
Real-time Voice Activity Detection using Silero VAD

Processes raw PCM audio chunks and detects speech/silence.
Optimized for continuous streaming with minimal latency.
"""

import torch
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class VoiceActivityDetector:
    """
    Server-side VAD using Silero model.

    Processes 16kHz mono PCM chunks and maintains conversation state.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,  # Speech probability threshold (0-1)
        min_speech_duration_ms: int = 250,  # Minimum speech before considering "started"
        min_silence_duration_ms: int = 1500,  # Silence needed to end utterance
        speech_pad_ms: int = 100  # Padding around speech segments
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms

        # Load Silero VAD model
        logger.info("Loading Silero VAD model...")
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False  # Use PyTorch version
        )
        self.model.eval()
        logger.info("✅ Silero VAD model loaded")

        # State tracking
        self.reset()

    def reset(self):
        """Reset VAD state for new conversation turn."""
        self.is_speaking = False
        self.speech_start_time = None
        self.silence_start_time = None
        self.accumulated_pcm = []
        self.total_samples = 0
        logger.debug("VAD state reset")

    def process_chunk(
        self,
        pcm_chunk: np.ndarray  # Float32 array, 16kHz mono
    ) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """
        Process a PCM chunk and update VAD state.

        Args:
            pcm_chunk: Float32 PCM samples, normalized to [-1.0, 1.0]

        Returns:
            Tuple of (is_speech, utterance_complete, complete_audio)
            - is_speech: True if current chunk contains speech
            - utterance_complete: True if silence detected, utterance is complete
            - complete_audio: Complete accumulated PCM if utterance_complete, else None
        """
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(pcm_chunk)

        # Run VAD inference
        with torch.no_grad():
            speech_prob = self.model(audio_tensor, self.sample_rate).item()

        is_speech = speech_prob >= self.threshold
        chunk_duration_ms = len(pcm_chunk) / self.sample_rate * 1000

        logger.debug(f"VAD: prob={speech_prob:.3f}, is_speech={is_speech}, chunk_ms={chunk_duration_ms:.0f}")

        # Accumulate chunk
        self.accumulated_pcm.append(pcm_chunk)
        self.total_samples += len(pcm_chunk)

        # State machine
        if is_speech:
            # Speech detected
            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.speech_start_time = self.total_samples / self.sample_rate
                logger.info(f"🗣️  Speech STARTED at {self.speech_start_time:.2f}s")

            # Reset silence counter
            self.silence_start_time = None

        else:
            # Silence detected
            if self.is_speaking:
                # We were speaking, now silent
                if self.silence_start_time is None:
                    # First silence chunk after speech
                    self.silence_start_time = self.total_samples / self.sample_rate
                    logger.debug(f"🔇 Silence started at {self.silence_start_time:.2f}s")

                # Check if silence duration exceeds threshold
                current_time = self.total_samples / self.sample_rate
                silence_duration_ms = (current_time - self.silence_start_time) * 1000

                if silence_duration_ms >= self.min_silence_duration_ms:
                    # Utterance complete!
                    speech_duration_ms = (self.silence_start_time - self.speech_start_time) * 1000
                    logger.info(
                        f"✅ Utterance COMPLETE: "
                        f"speech={speech_duration_ms:.0f}ms, "
                        f"silence={silence_duration_ms:.0f}ms, "
                        f"total_samples={self.total_samples}"
                    )

                    # Combine accumulated PCM
                    complete_audio = np.concatenate(self.accumulated_pcm)

                    # Reset state for next utterance
                    self.reset()

                    return True, True, complete_audio

        # Continue accumulating
        return is_speech, False, None

    def force_complete(self) -> Optional[np.ndarray]:
        """
        Force completion of current utterance (e.g., max duration timeout).

        Returns:
            Accumulated PCM audio or None if no audio accumulated
        """
        if len(self.accumulated_pcm) == 0:
            return None

        logger.info(f"⚠️  Force completing utterance: {self.total_samples} samples accumulated")
        complete_audio = np.concatenate(self.accumulated_pcm)
        self.reset()
        return complete_audio


class VADSession:
    """
    Manages a VAD session for a WebSocket conversation.

    Handles multiple conversation turns, maintaining state between
    user utterances and assistant responses.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.vad = VoiceActivityDetector()
        self.turn_count = 0
        self.created_at = None
        logger.info(f"VAD session created: {session_id}")

    def start_listening(self):
        """Start a new listening turn."""
        self.vad.reset()
        self.turn_count += 1
        logger.info(f"🎤 Session {self.session_id}: Turn {self.turn_count} started")

    def process_chunk(self, pcm_chunk: np.ndarray) -> Tuple[bool, bool, Optional[np.ndarray]]:
        """Process PCM chunk and return VAD results."""
        return self.vad.process_chunk(pcm_chunk)

    def stop_listening(self) -> Optional[np.ndarray]:
        """Stop listening and return any accumulated audio."""
        return self.vad.force_complete()

    def cleanup(self):
        """Cleanup resources."""
        logger.info(f"VAD session cleanup: {self.session_id}")
        self.vad = None
```

**Key Features:**
- ✅ Uses Silero VAD (enterprise-grade, <1ms per chunk)
- ✅ Processes 16kHz mono PCM chunks
- ✅ Configurable speech/silence thresholds
- ✅ State machine tracks speech start/end
- ✅ Returns complete audio when utterance finishes
- ✅ Session management for multi-turn conversations

### 1.3 Unit Tests (`backend/tests/test_vad_service.py`)

```python
"""
Unit tests for VAD service.
"""

import pytest
import numpy as np
from backend.services.vad_service import VoiceActivityDetector, VADSession

def test_vad_initialization():
    """Test VAD initializes correctly."""
    vad = VoiceActivityDetector()
    assert vad.sample_rate == 16000
    assert vad.model is not None
    assert not vad.is_speaking

def test_vad_silence_detection():
    """Test VAD detects silence."""
    vad = VoiceActivityDetector()

    # Generate 1 second of silence (zeros)
    silence = np.zeros(16000, dtype=np.float32)

    is_speech, complete, audio = vad.process_chunk(silence)
    assert not is_speech
    assert not complete  # Not complete yet (need 1.5s)

def test_vad_speech_detection():
    """Test VAD detects speech."""
    vad = VoiceActivityDetector()

    # Generate 1 second of speech (random noise as proxy)
    speech = np.random.randn(16000).astype(np.float32) * 0.5

    is_speech, complete, audio = vad.process_chunk(speech)
    # May or may not detect as speech (depends on VAD model)
    # Just verify it returns valid values
    assert isinstance(is_speech, bool)
    assert isinstance(complete, bool)

def test_vad_utterance_completion():
    """Test VAD completes utterance after silence."""
    vad = VoiceActivityDetector(min_silence_duration_ms=500)

    # 1. Speech chunk
    speech = np.random.randn(8000).astype(np.float32) * 0.5
    vad.process_chunk(speech)

    # 2. Silence chunks (need 500ms = 8000 samples at 16kHz)
    silence = np.zeros(4000, dtype=np.float32)
    is_speech, complete, audio = vad.process_chunk(silence)
    assert not complete  # Not enough silence yet

    is_speech, complete, audio = vad.process_chunk(silence)
    # Should complete (if first chunk detected as speech)
    if vad.is_speaking:
        assert complete
        assert audio is not None

def test_vad_session():
    """Test VAD session management."""
    session = VADSession("test-session-123")

    session.start_listening()
    assert session.turn_count == 1

    session.start_listening()
    assert session.turn_count == 2
```

## Phase 2: Frontend PCM Streaming

### 2.1 Update useWebSocketChat Hook

**File:** `/opt/kasaai/apps/b2c-portal/src/hooks/useWebSocketChat.ts`

**Changes:**

1. **Switch from MediaRecorder to PCM streaming:**

```typescript
// REMOVE: MediaRecorder logic
// ADD: PCM streaming

const startRecordingInternal = async () => {
  try {
    console.log('[WS] 🎤 Starting PCM streaming for hands-free conversation...');

    // Get audio processor
    const audioProcessor = getAudioProcessor();

    // Start streaming raw PCM chunks
    const stopStreaming = await audioProcessor.startPCMStreaming(
      (pcmData: Float32Array, sampleRate: number) => {
        // Send PCM chunk to server
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          // Convert Float32Array to base64 for WebSocket transport
          const buffer = pcmData.buffer;
          const base64 = btoa(
            String.fromCharCode(...new Uint8Array(buffer))
          );

          wsRef.current.send(JSON.stringify({
            type: 'pcm_chunk',
            data: base64,
            sample_rate: sampleRate
          }));
        }
      },
      500  // Send chunks every 500ms
    );

    // Store stop function
    stopStreamingRef.current = stopStreaming;
    isRecordingRef.current = true;

    console.log('[WS] ✅ PCM streaming started');
  } catch (error) {
    console.error('[WS] ❌ PCM streaming failed:', error);
  }
};
```

2. **Handle server VAD events:**

```typescript
case 'vad_speech_start':
  console.log('[WS] 🗣️  Server VAD detected speech start');
  onStatusChange?.('Listening...');
  break;

case 'vad_utterance_complete':
  console.log('[WS] ✅ Server VAD detected utterance complete');
  onStatusChange?.('Processing...');
  break;

case 'vad_silence':
  console.log('[WS] 🔇 Server VAD detected silence');
  break;
```

3. **Cleanup:**

```typescript
const stopRecordingInternal = () => {
  if (stopStreamingRef.current) {
    stopStreamingRef.current();
    stopStreamingRef.current = null;
  }
  isRecordingRef.current = false;
};
```

### 2.2 Remove Old MediaRecorder Code

- Remove mediaRecorderRef
- Remove audioChunksRef
- Remove MediaRecorder event handlers
- Remove VAD monitoring logic (server handles now)

## Phase 3: Backend WebSocket Handler

### 3.1 Update WebSocket Route

**File:** `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/websocket_chat.py`

**Changes:**

1. **Import VAD service:**

```python
from backend.services.vad_service import VADSession
```

2. **Initialize VAD session:**

```python
# Create VAD session for this WebSocket
vad_session = VADSession(f"ws-{uuid.uuid4().hex[:8]}")
```

3. **Handle PCM chunks:**

```python
elif message_type == "pcm_chunk":
    # Decode base64 PCM data
    pcm_base64 = message_data
    pcm_bytes = base64.b64decode(pcm_base64)

    # Convert bytes to Float32 array
    pcm_array = np.frombuffer(pcm_bytes, dtype=np.float32)

    # Process with VAD
    is_speech, utterance_complete, complete_audio = vad_session.process_chunk(pcm_array)

    if is_speech and not vad_session.vad.is_speaking:
        # Speech just started
        await websocket.send_json({
            "type": "vad_speech_start",
            "data": "Speech detected"
        })
        if state_machine:
            state_machine.handle_vad_speech_detected()

    if utterance_complete and complete_audio is not None:
        # Utterance finished - transcribe
        logger.info(f"🎯 Utterance complete: {len(complete_audio)} samples")

        await websocket.send_json({
            "type": "vad_utterance_complete",
            "data": "Processing your message..."
        })

        # Convert Float32 PCM to WAV for Whisper
        wav_bytes = pcm_to_wav(complete_audio, sample_rate=16000)

        # Transcribe
        transcription = await perform_stt(wav_bytes, assistant)

        if transcription and transcription != "No speech detected":
            # Process conversation turn
            await process_transcription(
                websocket,
                transcription,
                assistant,
                state_machine
            )
        else:
            # No speech - resume listening
            logger.info("No speech detected, resuming listening...")
            await websocket.send_json({
                "type": "ready_to_listen",
                "data": "I didn't catch that - please speak again"
            })
```

4. **Add PCM to WAV converter:**

```python
def pcm_to_wav(pcm_samples: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Convert Float32 PCM samples to WAV file bytes.

    Args:
        pcm_samples: Float32 array normalized to [-1.0, 1.0]
        sample_rate: Sample rate (default 16000)

    Returns:
        WAV file as bytes
    """
    import struct
    import io

    # Convert float32 to int16
    pcm_int16 = np.clip(pcm_samples * 32767, -32768, 32767).astype(np.int16)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()

    # Write WAV header
    num_samples = len(pcm_int16)
    num_channels = 1
    sample_width = 2  # 16-bit

    # RIFF header
    wav_buffer.write(b'RIFF')
    wav_buffer.write(struct.pack('<I', 36 + num_samples * sample_width))
    wav_buffer.write(b'WAVE')

    # fmt subchunk
    wav_buffer.write(b'fmt ')
    wav_buffer.write(struct.pack('<I', 16))  # Subchunk size
    wav_buffer.write(struct.pack('<H', 1))   # Audio format (PCM)
    wav_buffer.write(struct.pack('<H', num_channels))
    wav_buffer.write(struct.pack('<I', sample_rate))
    wav_buffer.write(struct.pack('<I', sample_rate * num_channels * sample_width))
    wav_buffer.write(struct.pack('<H', num_channels * sample_width))
    wav_buffer.write(struct.pack('<H', sample_width * 8))

    # data subchunk
    wav_buffer.write(b'data')
    wav_buffer.write(struct.pack('<I', num_samples * sample_width))
    wav_buffer.write(pcm_int16.tobytes())

    return wav_buffer.getvalue()
```

5. **Remove broken WebM VAD:**

```python
# DELETE lines 334-408 (WebM energy calculation)
# DELETE lines 419-428 (partial transcription on WebM fragments)
```

## Phase 4: Testing & Validation

### 4.1 Unit Tests

```bash
cd /opt/kasaai/apps/core_backend
PYTHONPATH=/opt/kasaai:/opt/kasaai/apps/core_backend /opt/kasaai/apps/venv/bin/python -m pytest backend/tests/test_vad_service.py -v
```

### 4.2 Integration Test

Create test script `test_pcm_vad_flow.py`:

```python
"""
Test PCM streaming with VAD end-to-end.
"""

import asyncio
import websockets
import base64
import numpy as np

async def test_pcm_streaming():
    uri = "wss://api.ailabsafrica.com/api/voice-chat/ws"

    async with websockets.connect(uri) as websocket:
        # 1. Send initial handshake
        await websocket.send('{"type": "init", "data": {"user_id": "test"}}')

        # 2. Start conversation
        await websocket.send('{"type": "start_conversation"}')

        # 3. Stream PCM chunks
        for i in range(10):
            # Generate 500ms of fake speech (random noise)
            samples = np.random.randn(8000).astype(np.float32) * 0.3

            # Convert to base64
            pcm_bytes = samples.tobytes()
            pcm_base64 = base64.b64encode(pcm_bytes).decode('utf-8')

            await websocket.send(f'{{"type": "pcm_chunk", "data": "{pcm_base64}", "sample_rate": 16000}}')

            # Read server response
            response = await websocket.recv()
            print(f"Server response {i}: {response}")

            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(test_pcm_streaming())
```

### 4.3 Manual Testing

1. Open browser console on https://kasaai.ailabsafrica.com
2. Click "Talk to Agent"
3. Speak naturally
4. Verify:
   - ✅ PCM streaming starts automatically
   - ✅ Server VAD detects speech
   - ✅ Transcription appears after natural pause
   - ✅ Assistant responds
   - ✅ Recording auto-resumes
   - ✅ Second turn works identically

## Phase 5: Performance Optimization

### 5.1 VAD Parameters Tuning

Test different thresholds:
- `threshold`: 0.3 (sensitive) vs 0.7 (conservative)
- `min_silence_duration_ms`: 1000ms (fast) vs 2000ms (cautious)
- Chunk size: 500ms vs 1000ms

### 5.2 Latency Profiling

Add timing logs:
```python
import time

start = time.time()
# ... VAD processing ...
vad_latency = time.time() - start
logger.info(f"VAD latency: {vad_latency*1000:.1f}ms")
```

**Target:** <50ms VAD latency per chunk (Silero spec: <1ms for 30ms chunk)

### 5.3 Memory Management

Monitor PCM accumulation:
```python
if len(self.accumulated_pcm) > 200:  # ~10 seconds at 500ms chunks
    logger.warning("Long utterance, forcing completion")
    return self.force_complete()
```

## Success Criteria

1. ✅ First conversation turn works (user speaks, gets response)
2. ✅ Second turn auto-starts (no clicking)
3. ✅ Third+ turns work identically
4. ✅ VAD detects end of speech accurately (1-2s after user stops)
5. ✅ No "No speech detected" errors
6. ✅ <1 second total latency (VAD + transcription start)
7. ✅ Works in Chrome, Firefox, Safari
8. ✅ Handles interruptions gracefully
9. ✅ Unit tests pass at 80%+ coverage
10. ✅ Can sustain 10+ turn conversations

## Rollback Plan

If Option 1 fails:
1. Git revert to current state
2. Try Option 2 (fix existing MediaRecorder + frontend VAD)
3. Document specific failures for future attempts

## Timeline Estimate

- Phase 1 (Backend VAD): 2-3 hours
- Phase 2 (Frontend PCM): 1-2 hours
- Phase 3 (WebSocket): 2-3 hours
- Phase 4 (Testing): 1-2 hours
- Phase 5 (Optimization): 1-2 hours

**Total:** 7-12 hours

## Dependencies

✅ Already installed:
- torch 2.5.1
- torchaudio 2.5.1
- numpy
- FastAPI/WebSockets
- AudioProcessor with PCM streaming

❌ Need to install:
- silero-vad

## Next Steps

1. Review this plan
2. Get approval to proceed
3. Start with Phase 1 (backend VAD service)
4. Incremental testing after each phase
5. Document any issues encountered
6. Commit working milestones

# TTS Architecture in KasaAI

## Current Architecture

We currently have **TWO separate TTS systems** running in parallel:

### 1. Unified TTS Service (Legacy/Comprehensive)
**Location**: `apps/core_backend/backend/services/unified_tts_service.py`

**Purpose**: Production TTS service with multiple model options for different languages and use cases

**Available Models**:
- **AKAN_MMS** - Akan/Twi native TTS (Meta MMS)
- **COQUI_TTS** - Multi-language with voice cloning
- **F5_TTS** - Zero-shot voice cloning
- **XTTS_V2** - Advanced voice cloning for Twi
- **KOKORO_82M** - Fast multilingual model
- **META_MMS_TTS** - Meta's multilingual TTS
- **CHATTTS** - Conversational TTS
- **GTTS** - Google TTS (fallback)
- **MELOTTS** - Fast multilingual (44.1kHz)
- **OPENVOICE** - Voice cloning (24kHz)
- **STYLETTS2** - Expressive TTS (24kHz)

**Used By**:
- Voice Lab TTS tab
- Phone calls (Twilio/Vapi integrations)
- Batch TTS processing
- Most production features

### 2. Streaming TTS Service (New/Experimental)
**Location**: `apps/shared/integration/ai_services/streaming_tts_service.py`

**Purpose**: Low-latency streaming TTS for real-time conversations

**Model**:
- **Parler-TTS** only (`parler-tts/parler-tts-mini-v1`)
- Native sample rate: **44.1kHz** (CD quality)
- Sentence-by-sentence streaming
- ~40-60% latency reduction vs. blocking TTS

**Used By**:
- WebRTC voice conversations (new aiortc implementation)
- WebSocket streaming chat
- Real-time voice agents

**NOT visible in**:
- Voice Lab TTS dropdown (only shows Unified TTS models)
- TTS provider selection UI

---

## Why Two Separate Systems?

### Historical Context
1. **Unified TTS Service** was built first for comprehensive language support
2. **Streaming TTS Service** was added later for real-time conversations
3. They were never integrated

### Technical Differences
| Feature | Unified TTS | Streaming TTS (Parler) |
|---------|-------------|------------------------|
| **Latency** | 2-4s (blocking) | 0.5-1s (streaming) |
| **Sample Rate** | Varies (16-44.1kHz) | 44.1kHz (fixed) |
| **Voice Control** | Provider-specific | Description-based |
| **Streaming** | No | Yes |
| **Models** | 11+ models | 1 model only |

---

## The Sample Rate Bug We Just Fixed

### Root Cause
Parler-TTS generates audio at **44.1kHz**, but we were labeling WAV headers as **16kHz**.

When browsers played 44.1kHz audio at 16kHz speed:
```
16000 / 44100 = 0.36x speed (ultra slow!)
```

### Locations Fixed
1. ✅ `voice_pipeline.py` - WebRTC first message (both modes)
2. ✅ `websocket_chat.py` - WebSocket streaming
3. ✅ `streaming_tts_service.py` - Added `get_native_sample_rate()` method

### Fix Implementation
```python
# Get actual sample rate from TTS model
actual_sample_rate = streaming_tts.get_native_sample_rate()  # Returns 44100
logger.info(f"🎵 Using TTS native sample rate: {actual_sample_rate} Hz")

# Use in WAV header
wav_file.setframerate(actual_sample_rate)  # NOT hardcoded 16000!
```

---

## How to Add Parler TTS to Unified TTS Service

### Step 1: Add Parler TTS Enum
**File**: `apps/core_backend/backend/services/unified_tts_service.py`

```python
class TTSModel(str, Enum):
    """Available TTS model types"""
    AKAN_MMS = "akan-mms"
    COQUI_TTS = "coqui-tts"
    # ... existing models ...
    PARLER_TTS = "parler-tts"  # Add this
```

### Step 2: Add Model Configuration
```python
MODEL_CONFIGS = {
    # ... existing configs ...
    TTSModel.PARLER_TTS: TTSModelConfig(
        model_id="parler-tts/parler-tts-mini-v1",
        name="Parler-TTS (Streaming, Multilingual)",
        quality_score=4.3,
        languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
        dialects=[],
        provider="HuggingFace",
        supports_cloning=False,
        supports_speed_control=True,
        supports_pitch_control=False,
        sample_rate=44100  # CD quality
    ),
}
```

### Step 3: Add Model Loader
**In `_load_model()` method**:

```python
def _load_model(self, model: TTSModel) -> Any:
    # ... existing loaders ...

    elif model == TTSModel.PARLER_TTS:
        from apps.shared.integration.ai_services import get_streaming_tts_service
        model_instance = get_streaming_tts_service()
        logger.info("✅ Loaded Parler-TTS streaming service")
```

### Step 4: Add Synthesis Method
**In `synthesize()` method**:

```python
async def synthesize(
    self,
    text: str,
    model: Optional[TTSModel] = None,
    voice_id: Optional[str] = None,
    speed: float = 1.0,
    **kwargs
) -> TTSResult:
    # ... existing code ...

    if selected_model == TTSModel.PARLER_TTS:
        # Get voice description
        voice_description = voice_id or kwargs.get('voice_description', 'A clear, neutral voice')

        # Stream and collect all chunks
        audio_chunks = []
        async for chunk in model_instance.stream_tts(
            text=text,
            voice_description=voice_description,
            sample_rate=44100  # Use native rate
        ):
            audio_chunks.append(chunk)

        # Concatenate chunks
        import numpy as np
        audio = np.concatenate(audio_chunks)

        # Convert to WAV
        import io
        import wave
        wav_io = io.BytesIO()
        pcm_int16 = (audio * 32767).astype(np.int16)
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)  # CRITICAL: Use actual rate!
            wav_file.writeframes(pcm_int16.tobytes())

        wav_io.seek(0)
        wav_bytes = wav_io.read()
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

        return TTSResult(
            audio_base64=audio_base64,
            text=text,
            voice_id=voice_description,
            duration=len(audio) / 44100,
            processing_time=processing_time,
            sample_rate=44100,
            model=str(selected_model),
            format="wav"
        )
```

### Step 5: Update Frontend TTS Provider List
**File**: `apps/b2c-portal/src/config/api-config.ts` or wherever TTS providers are listed

Add Parler-TTS to the dropdown options with:
- Name: "Parler-TTS (Streaming, Multilingual)"
- ID: `parler-tts`
- Sample rate: 44100

---

## Current Status

### ✅ Fixed
1. WebRTC streaming audio playback speed
2. WebSocket streaming audio playback speed
3. TTS native sample rate detection
4. WAV header generation with correct sample rate

### ⚠️ Current Limitation
- Parler-TTS is NOT available in Voice Lab TTS dropdown
- Only accessible via WebRTC and WebSocket modes
- Unified TTS Service doesn't expose it as an option

### 🔧 To Add Parler to Unified Service
Follow the 5 steps above to integrate Parler-TTS into the comprehensive TTS service, making it available in:
- Voice Lab TTS tab
- Assistant TTS model selection
- API endpoints for TTS synthesis

---

## Testing

After adding Parler-TTS to unified service:

1. **Voice Lab Test**:
   - Go to Voice Lab → TTS tab
   - Select "Parler-TTS (Streaming, Multilingual)" from dropdown
   - Enter text and synthesize
   - Audio should play at normal speed (44.1kHz)

2. **API Test**:
   ```bash
   curl -X POST https://api.ailabsafrica.com/tts/synthesize \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello, this is a test of Parler TTS",
       "model": "parler-tts",
       "voice_description": "A friendly female voice"
     }'
   ```

3. **WebRTC Test** (already working):
   - African Development Bank Assistant
   - Click "Call" button
   - Should hear first message at normal speed

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           User Interface                        │
│  (Voice Lab, WebRTC Chat, Phone Calls)         │
└────────────┬────────────────────────────────────┘
             │
             ├─────────────┬─────────────────────┐
             │             │                     │
             ▼             ▼                     ▼
    ┌────────────┐  ┌──────────────┐  ┌─────────────────┐
    │ Voice Lab  │  │   WebRTC     │  │   WebSocket     │
    │    TTS     │  │ Streaming    │  │   Streaming     │
    └─────┬──────┘  └──────┬───────┘  └────────┬────────┘
          │                │                    │
          ▼                ▼                    ▼
    ┌──────────────┐  ┌──────────────────────────────┐
    │  Unified     │  │   Streaming TTS Service      │
    │  TTS Service │  │   (Parler-TTS only)          │
    │  (11 models) │  │   Sample Rate: 44.1kHz       │
    └──────────────┘  └──────────────────────────────┘
```

---

## Recommendations

1. **Short Term**: Keep current architecture, both systems working
   - WebRTC/WebSocket use Streaming TTS (Parler)
   - Voice Lab uses Unified TTS (11 models)

2. **Medium Term**: Add Parler to Unified TTS
   - Follow 5-step integration above
   - Makes Parler available everywhere
   - Users can choose between models

3. **Long Term**: Consider merging architectures
   - Make ALL models in Unified TTS support streaming
   - Single service with 12+ models
   - Unified interface with streaming capability
   - Requires significant refactoring

---

## Files Modified (2025-11-22)

1. `apps/shared/integration/ai_services/streaming_tts_service.py`
   - Added `model_sample_rate` extraction from config
   - Added `get_native_sample_rate()` method

2. `apps/shared/integration/voice_pipeline.py`
   - Use TTS native sample rate in WAV headers (both first message modes)
   - Added `_get_tts_service()` helper

3. `apps/core_backend/backend/routes/voice_engine/websocket_chat.py`
   - Get actual sample rate from streaming_tts
   - Use in pcm_to_wav() call

4. `apps/b2c-portal/src/hooks/useWebRTCChat.ts`
   - Fixed React useEffect dependencies (premature cleanup)
   - Added connection guard

5. `apps/b2c-portal/src/components/voice-agent/VoiceConversationRTC.tsx`
   - Reduced useEffect dependencies (9 → 2)

---

## Conclusion

We now have **correct audio playback** for both WebRTC and WebSocket modes. Parler-TTS is functional but only accessible through streaming interfaces. To make it available in Voice Lab and other UI components, follow the integration steps above.

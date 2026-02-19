# HF Speech-to-Speech Integration Status

## ❓ Is HF Speech-to-Speech Integrated?

**Answer: PARTIALLY** ✅❌

### What's Integrated ✅

1. **HF Speech-to-Speech PATTERN** - The architectural pattern is fully implemented:
   ```
   VAD → STT → LLM → TTS
   ```

   Located at: `@shared/integration/voice_pipeline.py`

   - ✅ **VAD** - Silero VAD v5 for voice activity detection
   - ✅ **STT** - Faster Whisper for speech-to-text
   - ✅ **LLM** - Configurable (OpenAI, Anthropic, etc.)
   - ✅ **TTS** - Multiple providers (see below)

2. **Modular Pipeline Architecture** - Just like HF speech-to-speech
   - Clean separation of concerns
   - Async generators for streaming
   - Easy to swap components

### What's NOT Integrated ❌

1. **HF Speech-to-Speech Library** - The actual Python package from https://github.com/huggingface/speech-to-speech is NOT installed
   - We're using the PATTERN, not the library
   - Our implementation is more flexible and integrated with KasaAI infrastructure

2. **HF-Specific Models** - Not using their exact model choices:
   - They use Paraformer for STT → We use Faster Whisper
   - They use MeloTTS/Parler-TTS → We support 20+ TTS providers
   - They use specific LLM → We support any LLM

---

## 🎙️ Current TTS Provider

The WebRTC integration currently uses: **Parler-TTS** (streaming)

Located at: `@shared/integration/ai_services/streaming_tts_service.py`

### Parler-TTS Features
- ✅ Streaming TTS (sentence-by-sentence)
- ✅ Voice description-based synthesis
- ✅ torch.compile optimization (20-30% faster)
- ✅ Low-latency first chunk (<500ms)
- ✅ English language support

### How It Works
```python
# Voice is controlled via text description
tts.stream_tts(
    text="Hello, how can I help you?",
    voice_description="A friendly female voice with British accent"
)
```

---

## 🎭 Available TTS Providers

Your system has **20+ TTS providers** available!

### Production-Grade Providers

| Provider | Type | Languages | Voice Cloning | Streaming | Status |
|----------|------|-----------|---------------|-----------|--------|
| **F5-TTS** | Neural | EN, ZH, JA, KO | ✅ | ✅ | 🟢 RunPod |
| **StyleTTS2** | Neural | EN | ✅ | ✅ | 🟢 RunPod |
| **Moshi** | Conversational | EN | ❌ | ✅ | 🟢 RunPod |
| **Coqui XTTS** | Neural | 17 languages | ✅ | ✅ | 🟢 Docker |
| **MeloTTS** | Fast | EN, ES, FR, ZH, JP, KR | ❌ | ✅ | 🟢 Docker |
| **OpenVoice** | Advanced | EN, ZH | ✅ | ❌ | 🟢 Docker |
| **Parler-TTS** | Streaming | EN | ❌ | ✅ | 🟢 Current |
| **OpenAI TTS** | API | Many | ❌ | ✅ | 🟡 API Key |
| **ElevenLabs** | API | Many | ✅ | ✅ | 🟡 API Key |
| **Google TTS** | API | 100+ | ❌ | ❌ | 🟡 API Key |

### African Language Providers

| Provider | Languages | Status |
|----------|-----------|--------|
| **Meta MMS** | Twi, Ewe, Hausa, Akan | 🟢 Available |
| **GhanaNLP** | Twi, Ga, Ewe | 🟡 Integration |

---

## 🔄 How to Switch TTS Providers

### Method 1: Per-Assistant Configuration (Recommended)

Edit assistant in MongoDB:

```json
{
  "id": "your-assistant-id",
  "name": "My Assistant",
  "tts_provider": "f5tts",  // Change this!
  "voice_description": "A clear, professional voice",
  "language": "en"
}
```

Supported `tts_provider` values:
- `"parler"` - Parler-TTS (current default)
- `"f5tts"` - F5-TTS
- `"styletts2"` - StyleTTS2
- `"coqui"` - Coqui XTTS v2
- `"melotts"` - MeloTTS
- `"openvoice"` - OpenVoice
- `"moshi"` - Moshi (conversational)
- `"openai"` - OpenAI TTS
- `"elevenlabs"` - ElevenLabs
- `"google"` - Google TTS

### Method 2: Update Streaming TTS Service

Edit `/opt/kasaai/apps/shared/integration/ai_services/streaming_tts_service.py`:

```python
# Change the get_streaming_tts_service function
def get_streaming_tts_service(provider: str = "parler"):
    if provider == "parler":
        return StreamingTTSService()
    elif provider == "f5tts":
        return F5TTSStreamingService()
    # etc...
```

### Method 3: Use TTS Client Directly

```python
from apps.shared.tts.client import TTSClient

# Initialize with specific provider
tts = TTSClient(provider="f5tts")

# Synthesize
audio = await tts.synthesize(
    text="Hello world",
    language="en",
    voice_description="Clear female voice"
)
```

---

## 🎤 How to Add/Switch Voices

### For Parler-TTS (Current Default)

Parler-TTS uses **text descriptions** instead of voice IDs!

```python
# Change voice via assistant configuration
{
  "voice_description": "A young female voice with American accent, speaking slowly"
}
```

Voice description examples:
- `"A deep male voice with British accent"`
- `"A friendly female voice, speaking energetically"`
- `"An elderly man with a calm, soothing voice"`
- `"A professional newsreader voice"`

### For F5-TTS (Voice Cloning)

1. **Upload Reference Audio**:
```bash
curl -X POST https://f5tts.ailabsafrica.com/clone \
  -F "audio=@reference_voice.wav" \
  -F "text=The text spoken in the reference"
```

2. **Get Voice ID** and use in assistant config:
```json
{
  "tts_provider": "f5tts",
  "voice_id": "cloned-voice-123",
  "voice_description": "Custom cloned voice"
}
```

### For Coqui XTTS (Multi-language + Cloning)

```json
{
  "tts_provider": "coqui",
  "language": "es",  // Spanish
  "voice_id": "default",
  "voice_description": "Spanish speaker"
}
```

Supported languages: EN, ES, FR, DE, IT, PT, PL, TR, RU, NL, CS, AR, ZH, HU, KO, JA, HI

### For MeloTTS (Multi-speaker)

```json
{
  "tts_provider": "melotts",
  "language": "EN",
  "speaker_id": "EN-BR",  // British English
  "voice_description": "British accent"
}
```

Available speakers:
- `EN-US` - American English
- `EN-BR` - British English
- `EN-INDIA` - Indian English
- `EN-AU` - Australian English

### For ElevenLabs (Voice Library)

```json
{
  "tts_provider": "elevenlabs",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",  // Rachel voice
  "api_key": "your-elevenlabs-key"
}
```

Browse voices at: https://elevenlabs.io/voice-library

---

## 📝 Complete Integration Example

### 1. Create Assistant with Custom TTS

```python
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://admin:password@localhost:27017/")
db = client.kasaai_core

# Create assistant with F5-TTS
assistant = {
    "id": "f5-assistant",
    "name": "F5 Voice Assistant",
    "system_prompt": "You are a helpful assistant.",

    # LLM Configuration
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",

    # STT Configuration
    "stt_provider": "whisper",
    "language": "en",

    # TTS Configuration - THIS IS KEY!
    "tts_provider": "f5tts",
    "voice_description": "A professional female voice with clear pronunciation",

    # Optional voice cloning
    "voice_reference_audio": "/path/to/reference.wav",
    "voice_reference_text": "The text spoken in the reference audio"
}

db.assistants.insert_one(assistant)
```

### 2. Use in WebRTC

```python
from apps.shared.integration.webrtc import setup_webrtc

# The WebRTC integration automatically uses the assistant's TTS config!
setup_webrtc(
    app=app,
    assistant_id="f5-assistant"  # Uses F5-TTS automatically
)
```

### 3. Test It

```bash
# Start server
uvicorn backend.main:app --reload --port 30027

# Open browser
http://localhost:30027/voice/webrtc/

# Speak - voice will use F5-TTS!
```

---

## 🚀 Recommended TTS Providers by Use Case

### For English Conversations
1. **Parler-TTS** (current) - Best for natural English
2. **F5-TTS** - Best for voice cloning
3. **ElevenLabs** - Best for ultra-realistic voices (requires API key)

### For African Languages
1. **Meta MMS** - Twi, Hausa, Ewe
2. **GhanaNLP** - Ghanaian languages
3. **Coqui XTTS** - Multilingual with cloning

### For Speed
1. **MeloTTS** - Fastest synthesis
2. **Parler-TTS** - Fast streaming
3. **OpenAI TTS** - Fast API

### For Voice Cloning
1. **F5-TTS** - Best quality cloning
2. **OpenVoice** - Advanced cloning with emotion
3. **StyleTTS2** - Expressive cloning
4. **Coqui XTTS** - Multilingual cloning
5. **ElevenLabs** - Professional cloning (paid)

### For Streaming
1. **Parler-TTS** - Sentence-level streaming
2. **F5-TTS** - Flow-matching streaming
3. **Moshi** - Full-duplex conversation
4. **OpenAI TTS** - API streaming

---

## 🔧 Implementation Guide

### Step 1: Choose Your TTS Provider

Based on your needs:
- Need English? → Parler-TTS (already configured)
- Need voice cloning? → F5-TTS
- Need African languages? → Meta MMS
- Need fastest? → MeloTTS
- Need ultra-realistic? → ElevenLabs

### Step 2: Update Assistant Config

```bash
# Using MongoDB shell
mongosh "mongodb://admin:password@localhost:27017/"

use kasaai_core

db.assistants.updateOne(
  { id: "your-assistant-id" },
  { $set: {
    tts_provider: "f5tts",
    voice_description: "Your desired voice description"
  }}
)
```

### Step 3: Restart Server

```bash
sudo systemctl restart kasaai-core-backend
```

### Step 4: Test

Open WebRTC UI and test the new voice!

---

## 📊 TTS Provider Comparison

| Feature | Parler-TTS | F5-TTS | Coqui XTTS | MeloTTS | ElevenLabs |
|---------|------------|--------|------------|---------|------------|
| **Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Streaming** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Voice Clone** | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Languages** | 1 | 4 | 17 | 6 | 29 |
| **Cost** | Free | Free | Free | Free | Paid |
| **Setup** | Easy | Medium | Medium | Easy | Easy |

---

## 🎯 Summary

### Current Status

✅ **HF Speech-to-Speech PATTERN** - Fully implemented
❌ **HF Speech-to-Speech LIBRARY** - Not installed (not needed)
✅ **Current TTS** - Parler-TTS with streaming
✅ **Available Providers** - 20+ options
✅ **Voice Customization** - Text descriptions or voice IDs
✅ **Easy Switching** - Just update assistant config

### To Switch TTS:

1. Choose provider from table above
2. Update assistant in MongoDB
3. Restart server
4. Test in WebRTC UI

### To Add Voices:

1. For Parler-TTS: Update `voice_description`
2. For F5-TTS: Clone voice and get voice ID
3. For MeloTTS: Choose speaker ID
4. For ElevenLabs: Browse voice library

**Need help?** Check:
- `/opt/kasaai/apps/shared/tts/README.md` - Full TTS documentation
- `/opt/kasaai/apps/shared/tts/config.py` - All provider configs
- `/opt/kasaai/apps/WEBRTC_INTEGRATION.md` - WebRTC integration guide

🎉 **You have a powerful, flexible TTS system ready to use!**

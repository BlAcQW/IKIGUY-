# Shared TTS Module

Unified Text-to-Speech interface for all Kasaai applications, providing seamless access to multiple TTS providers including F5-TTS, StyleTTS2, Moshi, Coqui XTTS, MeloTTS, OpenVoice, Kokoro, TTS-WebUI (20+ models), Fish Speech, GPT-SoVITS, Zonos TTS, IndexTTS 2.0, and VoxCPM.

## 🌟 TTS Lab - Unified Hub

All TTS services are accessible through a consolidated web interface at **https://ttslab.ailabsafrica.com**

The TTS Lab provides:
- 🎨 Modern landing page with all 17+ TTS services
- 📊 Real-time status indicators for each provider
- 🔗 Direct links to Gradio UIs and API endpoints
- 📚 Feature descriptions and use case guidance
- 🚀 One-click access to both RunPod GPU and local services

## Features

- 🎯 **Unified Interface**: Single API for all TTS providers
- 🌐 **TTS Lab Hub**: Centralized web access at https://ttslab.ailabsafrica.com
- 🔄 **Auto Provider Selection**: Automatically selects best available provider
- 🎭 **Voice Cloning**: Support for voice cloning across compatible providers
- 💬 **Real-time Conversation**: WebSocket support for Moshi's bidirectional dialogue
- 📦 **Batch Processing**: Process multiple texts efficiently
- 🎵 **Audio Utilities**: Format conversion, normalization, resampling
- 🔌 **Async/Sync Support**: Both synchronous and asynchronous clients
- 🧪 **Comprehensive Testing**: Unit tests with mocking

## Installation

```bash
# From the shared directory
cd /opt/kasaai/apps/shared
pip install -e .
```

## Quick Start

### Basic Synthesis

```python
from shared.tts import TTSClient, TTSProvider

# Synchronous client
client = TTSClient()

# Synthesize with auto-selected provider
response = client.synthesize("Hello, world!")
audio_data = response.audio

# Synthesize with specific provider
response = client.synthesize(
    "Hello from F5-TTS",
    provider=TTSProvider.F5TTS,
    language="en",
    speed=1.2
)

# Save audio to file
with open("output.wav", "wb") as f:
    f.write(response.audio)
```

### Asynchronous Usage

```python
import asyncio
from shared.tts import AsyncTTSClient, TTSProvider

async def main():
    async with AsyncTTSClient() as client:
        # Single synthesis
        response = await client.synthesize(
            "Async synthesis example",
            provider=TTSProvider.STYLETTS2
        )

        # Batch synthesis
        texts = ["First text", "Second text", "Third text"]
        batch_response = await client.synthesize_batch(
            texts,
            provider=TTSProvider.F5TTS,
            parallel=True,
            max_workers=3
        )

        print(f"Processed {batch_response.successful} texts successfully")

asyncio.run(main())
```

### Voice Cloning

```python
from shared.tts import TTSClient, TTSProvider

client = TTSClient()

# Load reference audio
with open("reference_voice.wav", "rb") as f:
    reference_audio = f.read()

# Clone voice
response = client.clone_voice(
    text="This is spoken in the cloned voice",
    reference_audio=reference_audio,
    provider=TTSProvider.F5TTS  # or STYLETTS2, COQUI_XTTS, OPENVOICE
)
```

### Real-time Conversation (Moshi)

```python
import asyncio
from shared.tts.websocket import ConversationManager

async def on_audio_received(audio_data: bytes):
    """Handle received audio."""
    # Play audio or save to file
    print(f"Received {len(audio_data)} bytes of audio")

async def on_text_received(text: str):
    """Handle received text."""
    print(f"Moshi says: {text}")

async def main():
    manager = ConversationManager()

    # Start conversation
    client = await manager.start_conversation(
        initial_text="Hello, can you hear me?",
        on_audio=on_audio_received,
        on_text=on_text_received
    )

    # Keep conversation running
    await asyncio.sleep(30)

    # Stop conversation
    await manager.stop_conversation()

asyncio.run(main())
```

## Providers

### Available Providers

Access all providers through **[TTS Lab](https://ttslab.ailabsafrica.com)** or directly via endpoints below:

**RunPod GPU Services:**

| Provider | Status | Features | Languages | Endpoint |
|----------|--------|----------|-----------|----------|
| **TTS-WebUI** | 🟢 Online | 20+ models platform, OpenAI API | 9+ langs | https://tts-webui.ailabsafrica.com |
| **IndexTTS 2.0** | 🟢 Online | Voice cloning, Emotion control, Speech editing | en, zh | RunPod Proxy (8016) |
| **VoxCPM** | 🟢 Online | Context-aware, Voice cloning, CPM family | en, zh | RunPod Proxy (8016) |
| **GPT-SoVITS** | 🟢 Online | Community #1, Superior cloning | Multi | RunPod Proxy |
| **Fish Speech** | 🟢 Online | Zero-shot cloning, Fast (5-6x RT) | 8 langs | RunPod Proxy |
| **Zonos TTS** | 🟢 Online | Emotion sliders, Prosody control | en | RunPod Proxy |
| **F5-TTS** | 🟢 Online | Flow-matching, Zero-shot cloning | en, zh, ja, ko | RunPod Proxy |
| **StyleTTS2** | 🟢 Online | Human-level (4.9/5), Style transfer | en | https://styletts.ailabsafrica.com |
| **Moshi** | 🟢 Online | Real-time conversation, WebSocket | en | https://moshi.ailabsafrica.com |

**Local Infrastructure Services:**

| Provider | Status | Features | Languages | Endpoint |
|----------|--------|----------|-----------|----------|
| **Coqui XTTS** | 🟢 Online | Production-tested, 20+ languages | 17 langs | https://coqui.ailabsafrica.com |
| **MeloTTS** | 🟢 Online | Fast synthesis, Multi-speaker | 6 langs | https://melotts.ailabsafrica.com |
| **OpenVoice** | 🟢 Online | Voice + tone transfer, Emotion | en, zh | https://openvoice.ailabsafrica.com |
| **Kokoro** | 🟢 Online | 11 voice packs, Natural prosody | en | https://kokoro.ailabsafrica.com |
| **F5-TTS API** | 🟢 Online | Local API, Same as RunPod quality | en, zh, ja, ko | https://f5tts.ailabsafrica.com |

### Provider Status

```python
from shared.tts import TTSClient

client = TTSClient()

# Get single provider status
status = client.get_provider_status(TTSProvider.F5TTS)
print(f"{status.name}: {status.status}")
print(f"GPU Memory: {status.gpu_memory_gb}GB")
print(f"Model Loaded: {status.model_loaded}")

# Get all provider statuses
all_statuses = client.get_all_statuses()
for provider_id, status in all_statuses.items():
    print(f"{status.name}: {status.status}")
```

## Audio Utilities

### Format Conversion

```python
from shared.tts import AudioUtils, AudioFormat

# Convert WAV to PCM
wav_data = open("input.wav", "rb").read()
pcm_data = AudioUtils.convert_format(
    wav_data,
    input_format=AudioFormat.WAV,
    output_format=AudioFormat.PCM,
    sample_rate=22050
)

# Convert numpy array to audio
import numpy as np
audio_array = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 22050))
wav_bytes = AudioUtils.numpy_to_bytes(
    audio_array,
    AudioFormat.WAV,
    sample_rate=22050
)
```

### Audio Processing

```python
from shared.tts import AudioUtils, AudioFormat

# Normalize audio volume
normalized = AudioUtils.normalize_audio(
    audio_data,
    AudioFormat.WAV,
    sample_rate=22050,
    target_db=-20.0  # Target volume in dB
)

# Resample audio
resampled = AudioUtils.resample(
    audio_data,
    AudioFormat.WAV,
    input_rate=44100,
    output_rate=22050
)

# Get audio duration
duration = AudioUtils.get_audio_duration(
    audio_data,
    AudioFormat.WAV,
    sample_rate=22050
)
print(f"Audio duration: {duration:.2f} seconds")
```

### Base64 Encoding

```python
from shared.tts import AudioUtils

# Encode for transmission
encoded = AudioUtils.encode_base64(audio_data)

# Decode received audio
decoded = AudioUtils.decode_base64(encoded)
```

## Advanced Usage

### Custom Provider Configuration

```python
from shared.tts import F5TTSProvider, TTSProviderConfig, ProviderEndpoint

# Create custom configuration
config = TTSProviderConfig(
    id=TTSProvider.F5TTS,
    name="Custom F5-TTS",
    description="Custom F5-TTS instance",
    endpoint=ProviderEndpoint(
        base_url="http://localhost:8002",
        timeout=60,
        retry_count=5
    ),
    capabilities=...
)

# Use custom provider
provider = F5TTSProvider(config)
async with provider:
    response = await provider.synthesize(request)
```

### WebSocket Streaming

```python
from shared.tts.websocket import MoshiWebSocketClient

client = MoshiWebSocketClient()

# Set up callbacks
client.on_connected = lambda: print("Connected!")
client.on_audio_received = lambda audio: process_audio(audio)
client.on_text_received = lambda text: print(f"Text: {text}")
client.on_error = lambda error: print(f"Error: {error}")

async def stream_conversation():
    await client.connect()

    # Send audio stream
    async def audio_generator():
        while True:
            audio_chunk = get_microphone_input()  # Your audio input
            yield audio_chunk
            await asyncio.sleep(0.02)  # 20ms chunks

    async for chunk in audio_generator():
        await client.send_audio(chunk)
```

### Error Handling

```python
from shared.tts import (
    TTSClient,
    ProviderNotAvailableError,
    AudioProcessingError,
    ModelNotLoadedError
)

client = TTSClient()

try:
    response = client.synthesize(
        "Test text",
        provider=TTSProvider.F5TTS
    )
except ProviderNotAvailableError as e:
    print(f"Provider not available: {e.provider}")
    # Try alternative provider
    response = client.synthesize("Test text")  # Auto-select
except AudioProcessingError as e:
    print(f"Audio processing failed: {e.message}")
except ModelNotLoadedError as e:
    print(f"Model not loaded: {e.model_name}")
```

### Using Kokoro TTS (11 Voice Packs)

```python
from shared.tts import AsyncTTSClient, TTSProvider, TTSRequest

async def kokoro_example():
    async with AsyncTTSClient() as client:
        # Use American female voice "Heart" (default)
        request = TTSRequest(
            text="Hello, this is Heart speaking with natural prosody.",
            provider=TTSProvider.KOKORO,
            speaker="af_heart",
            speed=1.0,
            pitch=1.0
        )
        response = await client.synthesize_from_request(request)

        # Use British male voice "George"
        request = TTSRequest(
            text="Good day, this is George with a British accent.",
            provider=TTSProvider.KOKORO,
            speaker="bm_george",
            speed=1.1
        )
        response = await client.synthesize_from_request(request)

        # All available Kokoro voices:
        # American Female: af_heart, af_bella, af_nicole, af_sarah, af_sky
        # American Male: am_adam, am_michael
        # British Female: bf_emma, bf_isabella
        # British Male: bm_george, bm_lewis
```

### Using TTS-WebUI (20+ Models)

```python
from shared.tts import AsyncTTSClient, TTSProvider, TTSRequest

async def tts_webui_example():
    async with AsyncTTSClient() as client:
        # Use StyleTTS2 model
        request = TTSRequest(
            text="High-quality expressive speech with StyleTTS2.",
            provider=TTSProvider.TTS_WEBUI,
            model="styletts2",  # Model parameter required!
            voice="default",
            language="en"
        )
        response = await client.synthesize_from_request(request)

        # Use F5-TTS model for voice cloning
        request = TTSRequest(
            text="Voice cloning with F5-TTS via WebUI.",
            provider=TTSProvider.TTS_WEBUI,
            model="f5-tts",
            voice="custom_voice",
            language="en",
            speed=1.2
        )
        response = await client.synthesize_from_request(request)

        # Use Kokoro model through TTS-WebUI
        request = TTSRequest(
            text="Fast natural speech with Kokoro.",
            provider=TTSProvider.TTS_WEBUI,
            model="kokoro",
            voice="af_heart",
            language="en"
        )
        response = await client.synthesize_from_request(request)

        # Available models: styletts2, rvc, bark, tortoise, melotts, mms,
        # f5-tts, xtts_v2, openvoice, kokoro, parler-tts, whisper,
        # musicgen, stable-audio, demucs, gpt-sovits, chatterbox,
        # mahaTTS, vall-e-x, and more!
```

### OpenAI-Compatible API (TTS-WebUI)

```python
from shared.tts import AsyncTTSClient, TTSProvider, TTSRequest, AudioFormat

async def openai_compatible_example():
    """TTS-WebUI supports OpenAI-compatible API format."""
    async with AsyncTTSClient() as client:
        # OpenAI-style request
        request = TTSRequest(
            text="This uses OpenAI-compatible API format.",
            provider=TTSProvider.TTS_WEBUI,
            model="styletts2",
            voice="alloy",  # OpenAI voice parameter
            speed=1.0,
            output_format=AudioFormat.MP3
        )
        response = await client.synthesize_from_request(request)

        # The provider automatically formats this as:
        # POST /api/v1/audio/speech
        # {
        #   "model": "styletts2",
        #   "input": "This uses OpenAI-compatible API format.",
        #   "voice": "alloy",
        #   "response_format": "mp3",
        #   "speed": 1.0
        # }
```

### Using Fish Speech (Zero-Shot Voice Cloning)

```python
from shared.tts import AsyncTTSClient, TTSProvider, TTSRequest, VoiceCloneRequest

async def fish_speech_example():
    """Fish Speech - Community #2 favorite for voice cloning."""
    async with AsyncTTSClient() as client:
        # Standard synthesis (fast inference)
        request = TTSRequest(
            text="Natural speech with Fish Speech's fast inference.",
            provider=TTSProvider.FISH_SPEECH,
            language="en",
            speed=1.0
        )
        response = await client.synthesize_from_request(request)

        # Zero-shot voice cloning with minimal reference audio
        with open("reference_voice.wav", "rb") as f:
            reference_audio = f.read()

        clone_request = VoiceCloneRequest(
            text="This is cloned speech using zero-shot learning.",
            reference_audio=reference_audio,
            provider=TTSProvider.FISH_SPEECH,
            language="en",
            enhance=True  # Audio enhancement
        )
        response = await client.clone_voice_from_request(clone_request)

        # Multilingual support (8 languages)
        for lang in ["en", "zh", "ja", "ko", "es", "fr", "de", "ru"]:
            request = TTSRequest(
                text=f"Multilingual support in {lang}",
                provider=TTSProvider.FISH_SPEECH,
                language=lang
            )
            response = await client.synthesize_from_request(request)
```

### Using Zonos TTS (Emotion Control)

```python
from shared.tts import AsyncTTSClient, TTSProvider, TTSRequest

async def zonos_example():
    """Zonos TTS - Experimental with emotion sliders."""
    async with AsyncTTSClient() as client:
        # Happy emotion
        request = TTSRequest(
            text="This is a joyful announcement!",
            provider=TTSProvider.ZONOS,
            language="en",
            emotion="happy",  # Emotion control
            speed=1.1,
            pitch=1.05
        )
        response = await client.synthesize_from_request(request)

        # Sad emotion
        request = TTSRequest(
            text="This is a somber message.",
            provider=TTSProvider.ZONOS,
            language="en",
            emotion="sad",
            speed=0.9,
            pitch=0.95
        )
        response = await client.synthesize_from_request(request)

        # Custom prosody control
        request = TTSRequest(
            text="Highly customizable prosody and expressiveness.",
            provider=TTSProvider.ZONOS,
            language="en",
            emotion="neutral",
            speed=1.0,
            pitch=1.0
        )
        response = await client.synthesize_from_request(request)
```

## Testing

```bash
# Run all tests
cd /opt/kasaai/apps/shared
pytest tests/test_tts.py -v

# Run specific test category
pytest tests/test_tts.py::TestAudioUtils -v

# Run with coverage
pytest tests/test_tts.py --cov=shared.tts --cov-report=html
```

## API Reference

### Main Classes

- `TTSClient`: Synchronous TTS client
- `AsyncTTSClient`: Asynchronous TTS client
- `MoshiWebSocketClient`: WebSocket client for real-time conversation
- `ConversationManager`: High-level conversation manager
- `AudioUtils`: Audio processing utilities

### Models

- `TTSRequest`: Standard TTS request
- `TTSResponse`: TTS response with audio
- `VoiceCloneRequest`: Voice cloning request
- `ConversationRequest`: Real-time conversation request
- `TTSProvider`: Provider enumeration
- `AudioFormat`: Audio format enumeration

### Exceptions

- `TTSException`: Base exception
- `ProviderNotAvailableError`: Provider offline/unavailable
- `ModelNotLoadedError`: Model not loaded
- `AudioProcessingError`: Audio processing failed
- `InvalidRequestError`: Invalid request parameters
- `WebSocketError`: WebSocket operation failed

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from shared.tts import AsyncTTSClient, TTSProvider

app = FastAPI()
client = AsyncTTSClient()

@app.on_event("startup")
async def startup():
    await client._initialize_providers()

@app.on_event("shutdown")
async def shutdown():
    await client.close()

@app.post("/synthesize")
async def synthesize(text: str, provider: str = None):
    try:
        provider_enum = TTSProvider[provider] if provider else None
        response = await client.synthesize(text, provider=provider_enum)
        return {
            "audio": response.audio.hex() if response.audio else None,
            "provider": response.provider.value,
            "duration": response.duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Django Integration

```python
# views.py
from django.http import HttpResponse, JsonResponse
from shared.tts import TTSClient, TTSProvider

client = TTSClient()

def synthesize_view(request):
    text = request.POST.get('text')
    provider = request.POST.get('provider')

    try:
        provider_enum = TTSProvider[provider] if provider else None
        response = client.synthesize(text, provider=provider_enum)

        # Return audio file
        return HttpResponse(
            response.audio,
            content_type=f'audio/{response.format.value}'
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

## Contributing

1. Add new providers by extending `BaseTTSProvider`
2. Update `PROVIDER_CONFIGS` in `config.py`
3. Add tests in `tests/test_tts.py`
4. Update documentation

## License

Part of the Kasaai platform. All rights reserved.
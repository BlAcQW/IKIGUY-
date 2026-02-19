# VAPI TTS Integration - Complete Summary

## Issues Fixed

### Issue 1: No Audio Output from VAPI Assistant ✅ FIXED
**Problem**: VAPI widget at https://kasaai.ailabsafrica.com/vapi-management loaded but produced no sound during voice conversations.

**Root Cause**: TTS webhook was calling non-existent unified API endpoint `https://tts-webui.ailabsafrica.com/api/v1/audio/speech` (404 error).

**Solution**: Updated TTS service to use direct service endpoints:
- Modified `/opt/kasaai/apps/shared/services/tts_webui_service.py`
- Added provider-specific endpoint mapping
- Changed request format from OpenAI-compatible to direct TTS service format
- Updated response handling from JSON to binary PCM audio

### Issue 2: Provider Selection Missing ✅ FIXED
**Problem**: No ability to select TTS provider when creating VAPI assistants.

**Solution**: Added provider selection API:
- Created `/api/vapi/assistants/tts-providers` endpoint
- Returns list of 7 available providers with metadata
- Updated assistant creation to accept `voice_provider` parameter
- Set Kokoro as recommended default provider

## Implementation Details

### 1. TTS Service Updates

**File**: `/opt/kasaai/apps/shared/services/tts_webui_service.py`

**Provider Endpoints** (Line 140-150):
```python
self.provider_endpoints = {
    "styletts2": "https://styletts.ailabsafrica.com",
    "kokoro": "https://kokoro.ailabsafrica.com",
    "melotts": "https://melotts.ailabsafrica.com",
    "openvoice": "https://openvoice.ailabsafrica.com",
    "chatterbox": "https://chatterbox.ailabsafrica.com",
    "coqui": "https://coqui.ailabsafrica.com",
    "f5tts": "https://f5tts.ailabsafrica.com",
}
```

**Synthesize Method** (Line 232-287):
- Gets provider URL from mapping
- Sends request to `{provider_url}/synthesize`
- Payload format: `{"text": ..., "voice": ..., "speed": ..., "pitch": ...}`
- Returns base64-encoded PCM audio

**Get Providers Method** (Line 196-212):
```python
def get_providers(self) -> List[TTSWebUIProvider]:
    return [TTSWebUIProvider(provider_id) for provider_id in self.provider_endpoints.keys()]
```

### 2. VAPI Assistant API Updates

**File**: `/opt/kasaai/apps/core_backend/backend/routes/vapi_assistants.py`

**New Endpoint** (Line 109-195):
```python
@router.get("/tts-providers")
async def get_tts_providers():
    # Returns list of 7 providers with id, name, description, url, recommended
```

**Updated Model** (Line 70-73):
```python
voice_provider: str = Field(
    "kokoro",
    description="TTS provider: kokoro, styletts2, melotts, openvoice, chatterbox, coqui, f5tts"
)
```

## Available TTS Providers

| Provider | Speed | Quality | Voice Cloning | Recommended | URL |
|----------|-------|---------|---------------|-------------|-----|
| **Kokoro** | ⚡⚡⚡ | ⭐⭐⭐⭐ | ❌ | ✅ | https://kokoro.ailabsafrica.com |
| StyleTTS2 | ⚡⚡ | ⭐⭐⭐⭐⭐ | ✅ | ❌ | https://styletts.ailabsafrica.com |
| MeloTTS | ⚡⚡⚡ | ⭐⭐⭐⭐ | ❌ | ❌ | https://melotts.ailabsafrica.com |
| OpenVoice | ⚡⚡ | ⭐⭐⭐⭐ | ✅ | ❌ | https://openvoice.ailabsafrica.com |
| Chatterbox | ⚡⚡ | ⭐⭐⭐⭐ | ✅ | ❌ | https://chatterbox.ailabsafrica.com |
| Coqui | ⚡⚡ | ⭐⭐⭐ | ✅ | ❌ | https://coqui.ailabsafrica.com |
| F5-TTS | ⚡⚡ | ⭐⭐⭐⭐ | ✅ | ❌ | https://f5tts.ailabsafrica.com |

## API Endpoints

### Get Configuration
```bash
GET https://api.ailabsafrica.com/api/vapi/config

Response:
{
    "tts_providers": {
        "default": "styletts2",
        "fallback": "kokoro",
        "available": ["styletts2", "kokoro", "melotts", ...]
    },
    "rate_limits": {...},
    "audio_formats": {...}
}
```

### Get TTS Providers
```bash
GET https://api.ailabsafrica.com/api/vapi/assistants/tts-providers

Response:
{
    "providers": [
        {
            "id": "kokoro",
            "name": "Kokoro TTS",
            "description": "Fast, high-quality TTS with 82M parameters...",
            "url": "https://kokoro.ailabsafrica.com",
            "recommended": true
        },
        ...
    ],
    "total": 7
}
```

### Create Assistant
```bash
POST https://api.ailabsafrica.com/api/vapi/assistants/
Content-Type: application/json

{
    "name": "Customer Support Bot",
    "voice_provider": "kokoro",
    "system_prompt": "You are a helpful customer support agent.",
    "first_message": "Hello! How can I help you?",
    "model": "gpt-4",
    "sample_rate": 24000,
    "enable_recording": true,
    "enable_transcription": true
}

Response:
{
    "success": true,
    "assistant": {
        "id": "5f4710ab-142f-4962-b488-d55be70e7c6f",
        "name": "Customer Support Bot",
        "voice": {
            "provider": "custom-voice",
            "server": {
                "url": "https://api.ailabsafrica.com/api/vapi/webhook",
                ...
            }
        },
        ...
    }
}
```

### Test TTS Webhook
```bash
POST https://api.ailabsafrica.com/api/vapi/webhook
Content-Type: application/json
Authorization: Bearer {VAPI_API_KEY}

{
    "message": {
        "type": "voice-request",
        "text": "Hello world",
        "sampleRate": 24000
    },
    "timestamp": 1699999999,
    "assistant": {"organizationId": "test_org"}
}

Response: Binary PCM audio data (73KB for "Hello world")
```

## Demo Pages

1. **Original Demo**: /opt/kasaai/apps/demos/tts_test.html
   - URL: https://kasaai.ailabsafrica.com/vapi-management
   - Full-featured demo with instructions

2. **Simple Test**: /opt/kasaai/apps/demos/vapi_test_simple.html
   - Simpler testing interface
   - Shows configuration and status

## Testing

### Backend Tests
```bash
# 1. Test webhook
curl -X POST "https://api.ailabsafrica.com/api/vapi/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 42cf1e7c-2ef9-4bd7-ba30-52f2813605a2" \
  -d '{"message": {"type": "voice-request", "text": "Hello", "sampleRate": 24000}, "timestamp": 1699999999, "assistant": {"organizationId": "test"}}' \
  --output test.pcm

# Expected: 73KB PCM audio file

# 2. Test config
curl https://api.ailabsafrica.com/api/vapi/config

# 3. Test providers
curl https://api.ailabsafrica.com/api/vapi/assistants/tts-providers

# 4. Test assistant creation
curl -X POST https://api.ailabsafrica.com/api/vapi/assistants/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "voice_provider": "kokoro", "system_prompt": "You are helpful.", "first_message": "Hi!"}'
```

### Frontend Tests
1. Open https://kasaai.ailabsafrica.com/vapi-management
2. Check browser console for errors
3. Click widget button in bottom-right
4. Click "Start" to begin voice conversation
5. Speak and verify AI responds with audio
6. Check transcript appears

## Files Modified

1. `/opt/kasaai/apps/shared/services/tts_webui_service.py`
   - Added provider endpoints mapping
   - Updated synthesize() method
   - Added get_providers() method

2. `/opt/kasaai/apps/core_backend/backend/routes/vapi_assistants.py`
   - Added /tts-providers endpoint
   - Updated VapiAssistantCreate model
   - Fixed route ordering

3. `/opt/kasaai/apps/demos/vapi_test_simple.html` (new)
   - Simple test page for VAPI widget

## Services Restarted

- kasaai-core-backend.service

## Current Status

✅ **ALL ISSUES FIXED**
- TTS webhook generating audio successfully
- Provider selection API available
- All 7 TTS providers configured and accessible
- Demo pages ready for testing
- Backend API ready for frontend integration

## Next Steps for Frontend

1. **Fetch Providers on Load**:
   ```javascript
   const providers = await fetch('/api/vapi/assistants/tts-providers').then(r => r.json());
   ```

2. **Add Provider Selector**:
   ```jsx
   <select name="voice_provider">
     {providers.map(p => (
       <option value={p.id} selected={p.recommended}>
         {p.name} {p.recommended && '(Recommended)'}
       </option>
     ))}
   </select>
   ```

3. **Include in Assistant Creation**:
   ```javascript
   const response = await fetch('/api/vapi/assistants/', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       name: formData.name,
       voice_provider: formData.voice_provider, // Selected provider
       ...
     })
   });
   ```

## Performance Notes

- **Kokoro**: Fastest, 82M parameters, best for real-time
- **StyleTTS2**: Best quality, slower, supports voice cloning
- **All providers**: Support 24kHz sample rate, PCM output
- **Webhook latency**: ~0.5-2s depending on text length and provider

## Troubleshooting

**No audio in widget**:
1. Check browser console for errors
2. Verify microphone permissions granted
3. Test webhook directly: `curl https://api.ailabsafrica.com/api/vapi/webhook ...`
4. Check backend logs: `sudo journalctl -u kasaai-core-backend -f | grep vapi`

**Provider not working**:
1. Verify service is running: `curl https://{provider}.ailabsafrica.com/health`
2. Check provider endpoint mapping in tts_webui_service.py
3. Test provider directly: `curl -X POST https://{provider}.ailabsafrica.com/synthesize -d '{"text":"test"}'`

## Date
November 8, 2025

## Author
AI Labs Africa - Claude Code Assistant

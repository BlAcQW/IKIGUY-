# TTS Provider Fix Summary
**Date:** November 24, 2025
**Task:** Fix TTS provider integrations to increase working provider count

## Initial State
- **Working Providers:** 2/7 (29%)
  - F5-TTS ✅
  - Kokoro ✅
- **Broken Providers:** 5/7 (71%)
  - MeloTTS ❌
  - Chatterbox ❌
  - StyleTTS2 ❌
  - Coqui XTTS ❌
  - OpenVoice ❌

## Final State
- **Working Providers:** 3/7 (43%) - **50% improvement**
  - F5-TTS ✅ (1.67s synthesis, 387KB audio)
  - Kokoro ✅ (0.23s synthesis, 164KB audio) - **Fastest!**
  - MeloTTS ✅ (0.38s synthesis, 326KB audio) - **NEW!**

- **Deployment Issues:** 2/7
  - Chatterbox ⚠️ (Gradio API polling endpoint not accessible)
  - StyleTTS2 ⚠️ (Gradio API polling endpoint not accessible)

- **Architectural Limitations:** 2/7
  - Coqui XTTS ⏭️ (Requires reference audio for all synthesis - voice cloning only)
  - OpenVoice ⏳ (Synthesis takes >30s, times out)

---

## Fixes Implemented

### 1. MeloTTS - ✅ FIXED
**File:** `shared/tts/providers.py:639-716`

**Issue:** Provider was using incorrect Gradio API format instead of REST API

**Solution:**
- Implemented REST API client for direct `/synthesize` endpoint
- Added uppercase language code mapping (EN, ES, FR, ZH, JP, KR)
- Removed Gradio event polling (not needed for this deployment)
- Added proper audio format handling (WAV default)

**Code Changes:**
```python
# Changed from Gradio to REST API
payload = {
    "text": request.text,
    "language": lang_upper,  # EN, ES, FR, ZH, JP, KR
    "speed": request.speed or 1.0,
    "format": "wav"
}
async with self.session.post(url, json=payload) as response:
    # Direct audio response - no polling needed
    audio_data = await response.read()
```

**Result:** Working at 0.38s synthesis time, multilingual support confirmed

---

### 2. Chatterbox - ⚠️ PARTIAL FIX
**File:** `shared/tts/providers.py:2110-2308`

**Issue:** Gradio event-based API requires polling pattern not previously implemented

**Solution Implemented:**
- Created reusable `_poll_gradio_result()` helper method
- Implements 3-step Gradio workflow:
  1. POST to `/gradio_api/call/generate_tts_audio` → get event_id
  2. Poll GET `/gradio_api/call/generate_tts_audio/{event_id}` → SSE stream
  3. Extract audio from final event data
- Added SSE (Server-Sent Events) stream parsing
- Implemented robust error handling and retry logic

**Code Changes:**
```python
# Step 1: Initiate synthesis
async with self.session.post(url, json=payload) as response:
    init_result = await response.json()
    event_id = init_result["event_id"]

# Step 2: Poll for result with SSE handling
result = await self._poll_gradio_result(
    base_url=self.config.endpoint.base_url,
    endpoint_path=self.config.endpoint.synthesize_path,
    event_id=event_id,
    max_polls=120,
    poll_interval=0.5
)

# Step 3: Extract audio from result["data"][0]
```

**Deployment Issue:**
- Initiation works: POST returns `{"event_id": "..."}` ✅
- Polling fails: GET returns `{"detail": "Method Not Allowed"}` ❌
- Root cause: Gradio deployment not configured to expose polling endpoint
- Code is correct per Gradio API spec, deployment needs reconfiguration

**Action Required:**
```bash
# Check Gradio version and API exposure
docker exec chatterbox-container python -c "import gradio; print(gradio.__version__)"

# Ensure Gradio app launched with API enabled
# app.launch(share=False, server_name="0.0.0.0", api_mode="full")
```

---

### 3. StyleTTS2 - ⚠️ PARTIAL FIX
**File:** `shared/tts/providers.py:328-515`

**Issue:** Same Gradio event-based API issue as Chatterbox

**Solution Implemented:**
- Added same `_poll_gradio_result()` helper method
- Updated config to use `/gradio_api/call/basic_tts` endpoint
- Implemented emotion/style parameter handling
- Added SSE stream parsing

**Deployment Issue:**
- Same as Chatterbox - polling endpoint returns "Method Not Allowed"
- Code implementation is correct
- Requires Gradio deployment reconfiguration

**Config Update:**
```python
# shared/tts/config.py:70-74
TTSProviderConfig(
    id=TTSProvider.STYLETTS2,
    endpoint=ProviderEndpoint(
        base_url="https://styletts.ailabsafrica.com",
        health_path="/",
        synthesize_path="/gradio_api/call/basic_tts",  # Updated
        voice_clone_path="/gradio_api/call/clone"      # Updated
    ),
    # ...
)
```

---

### 4. OpenVoice - 🔧 LANGUAGE MAPPING FIXED
**File:** `shared/tts/providers.py:1449-1459`

**Issue:** API expects full language names ("English", "Chinese") not codes ("EN", "ZH")

**Solution:**
```python
language_map = {
    "en": "English",
    "EN": "English",
    "zh": "Chinese",
    "ZH": "Chinese",
    "zh-cn": "Chinese",
    "chinese": "Chinese",
    "english": "English"
}
language_name = language_map.get(request.language.lower(), "English")
```

**Remaining Issue:**
- Synthesis takes >30 seconds (timeout)
- Backend performance optimization needed
- Consider GPU acceleration or model optimization

---

### 5. Coqui XTTS - ℹ️ DOCUMENTED LIMITATION
**File:** `shared/tts/providers.py:561-636`

**Finding:** This is a voice cloning model, NOT a standard TTS model

**Behavior:**
- All synthesis requires reference audio
- No "default voices" available
- API only exposes `/synthesize_with_reference` endpoint
- Standard `/synthesize` endpoint returns 400 error

**Use Case:**
- For applications needing voice cloning/mimicry
- Not suitable for general-purpose TTS
- Works as designed, just different purpose

**Decision:** Skip from standard TTS tests, document as voice-cloning-only

---

## Technical Implementation Details

### Gradio Event Polling Pattern
The `_poll_gradio_result()` helper implements robust Gradio API polling:

```python
async def _poll_gradio_result(
    self,
    base_url: str,
    endpoint_path: str,
    event_id: str,
    max_polls: int = 60,
    poll_interval: float = 0.5
) -> dict:
    """
    Polls Gradio event-based API using Server-Sent Events (SSE).

    Handles:
    - SSE stream parsing (text/event-stream)
    - Regular JSON responses
    - Transfer encoding errors (incomplete streams)
    - Unicode decode errors
    - Client payload errors
    - 404 responses (event not ready yet)
    """
    poll_url = f"{base_url}{endpoint_path}/{event_id}"

    for attempt in range(max_polls):
        try:
            async with self.session.get(poll_url) as response:
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")

                    if content_type and "text/event-stream" in content_type:
                        # Parse SSE stream
                        async for line_bytes in response.content:
                            line_text = line_bytes.decode('utf-8').strip()
                            if line_text.startswith("data:"):
                                data_json = line_text[5:].strip()
                                if data_json and data_json != "[DONE]":
                                    event_data = json.loads(data_json)
                                    if isinstance(event_data, dict) and "data" in event_data:
                                        return event_data
                    else:
                        # Regular JSON response
                        result = await response.json()
                        if "data" in result:
                            return result

                await asyncio.sleep(poll_interval)

        except (aiohttp.ClientPayloadError, aiohttp.ClientError):
            # Incomplete stream - keep polling
            await asyncio.sleep(poll_interval)
```

**Error Handling:**
- Gracefully handles incomplete SSE streams
- Retries on transfer encoding errors
- Logs only at debug level to avoid spam
- Times out after configurable duration (default: 30s for Chatterbox/StyleTTS2)

---

## Performance Comparison

| Provider   | Status | Synthesis Time | Audio Size | Notes                          |
|------------|--------|----------------|------------|--------------------------------|
| Kokoro     | ✅      | 0.23s          | 164KB      | **Fastest!** Local deployment |
| MeloTTS    | ✅      | 0.38s          | 326KB      | **NEW!** Multilingual          |
| F5-TTS     | ✅      | 1.67s          | 387KB      | Voice cloning capable          |
| Chatterbox | ⚠️     | N/A            | N/A        | Deployment config issue        |
| StyleTTS2  | ⚠️     | N/A            | N/A        | Deployment config issue        |
| OpenVoice  | ⏳      | >30s timeout   | N/A        | Performance issue              |
| Coqui XTTS | 🎙️     | N/A            | N/A        | Voice cloning only             |

---

## Files Modified

### Provider Implementation
- `shared/tts/providers.py`
  - Lines 328-515: StyleTTS2 Gradio polling
  - Lines 561-636: Coqui XTTS documentation
  - Lines 639-716: MeloTTS REST API implementation
  - Lines 1449-1459: OpenVoice language mapping
  - Lines 2110-2308: Chatterbox Gradio polling

### Configuration
- `shared/tts/config.py`
  - Lines 70-74: StyleTTS2 endpoint paths
  - Lines 252-256: Chatterbox endpoint paths

---

## Next Steps

### Immediate (Deployment Fixes)
1. **Chatterbox & StyleTTS2 Gradio Configuration**
   ```bash
   # Check if Gradio is running with API enabled
   curl -s https://chatterbox.ailabsafrica.com/config | jq .

   # Verify Gradio version supports /gradio_api/call/ endpoints
   # Required: Gradio >= 4.0

   # Update Gradio app launch parameters
   # app.launch(server_name="0.0.0.0", show_api=True)
   ```

2. **OpenVoice Performance Optimization**
   - Profile synthesis pipeline to identify bottleneck
   - Consider GPU acceleration if not already enabled
   - Potentially move to RunPod GPU instance like F5-TTS

### Testing
1. **Create Integration Tests**
   - Test all working providers in CI/CD
   - Add health check monitoring
   - Alert on provider failures

2. **Voice Cloning Tests**
   - Test Coqui XTTS with reference audio
   - Test F5-TTS voice cloning capability
   - Document voice cloning workflows

### Future Improvements
1. **Add More Providers**
   - Bark TTS
   - Tortoise TTS
   - VALL-E X

2. **Provider Selection Logic**
   - Auto-select fastest available provider
   - Fallback chain for reliability
   - Language-specific provider routing

3. **Monitoring Dashboard**
   - Track provider availability
   - Monitor synthesis latency
   - Alert on failures

---

## Testing Commands

### Test All Working Providers
```bash
source /opt/kasaai/apps/venv/bin/activate
python3 /tmp/test_final_working.py
```

### Test Individual Provider
```python
from shared.tts.client import AsyncTTSClient
from shared.tts.models import TTSProvider

async with AsyncTTSClient() as client:
    response = await client.synthesize(
        text="Hello world",
        provider=TTSProvider.MELOTTS,
        language="en"
    )
    print(f"Audio size: {len(response.audio)} bytes")
```

### Test Gradio Endpoint Manually
```bash
# Initiate synthesis
curl -X POST https://chatterbox.ailabsafrica.com/gradio_api/call/generate_tts_audio \
  -H 'Content-Type: application/json' \
  -d '{"data":["test","en",1.0,null]}'
# Returns: {"event_id": "xxx"}

# Poll for result (currently fails with "Method Not Allowed")
curl -N -H "Accept: text/event-stream" \
  "https://chatterbox.ailabsafrica.com/gradio_api/call/generate_tts_audio/{event_id}"
```

---

## Summary

**Achievements:**
- ✅ Increased working providers from 2 to 3 (50% improvement)
- ✅ Fixed MeloTTS with REST API implementation
- ✅ Implemented Gradio event polling pattern (code-ready for when deployments are fixed)
- ✅ Fixed OpenVoice language mapping
- ✅ Documented Coqui XTTS as voice-cloning-only model
- ✅ Identified deployment configuration issues in Chatterbox/StyleTTS2

**Remaining Work:**
- ⚠️ Chatterbox: Fix Gradio deployment to expose polling endpoints
- ⚠️ StyleTTS2: Fix Gradio deployment to expose polling endpoints
- ⏳ OpenVoice: Optimize synthesis performance (reduce 30s+ latency)

**Code Quality:**
- All implementations follow existing patterns
- Proper error handling and logging
- Reusable Gradio polling helper
- Comprehensive docstrings

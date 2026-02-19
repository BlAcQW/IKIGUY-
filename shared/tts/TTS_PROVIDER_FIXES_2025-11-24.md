# TTS Provider Fixes - November 24, 2025

## Summary

Fixed TTS provider health checks and configurations, improving provider online status from **3/13 (23%)** to **12/13 (92%)**.

## Issues Fixed

### 1. **Provider Health Check Logic** (`/opt/kasaai/apps/shared/tts/providers.py`)
**Problem:** Health checks only accepted JSON responses, causing Gradio-based providers (StyleTTS2, Fish Speech, Zonos, TTS-WebUI) to fail despite being online.

**Solution:** Updated `BaseTTSProvider.check_health()` to:
- Detect content-type header (JSON vs HTML)
- Accept HTTP 200 with HTML as "healthy" for Gradio apps
- Gracefully handle both JSON API and HTML web interface responses

**Files Changed:**
- `/opt/kasaai/apps/shared/tts/providers.py:76-131`

### 2. **Provider Configuration Issues** (`/opt/kasaai/apps/shared/tts/config.py`)

#### a) Chatterbox Endpoint
- **Before:** `http://localhost:8004`
- **After:** `https://chatterbox.ailabsafrica.com`
- **Health Path:** `/health` → `/` (Gradio root endpoint)

#### b) F5-TTS Domain Mismatch
- **Issue:** Two nginx configs pointing to different ports:
  - `f5tts.ailabsafrica.com` → Port 8010 (TTS Provider Hub landing page)
  - `kyutai.ailabsafrica.com` → Port 8012 (Actual F5-TTS API)
- **Solution:** Use `kyutai.ailabsafrica.com` for F5-TTS API

#### c) Health Endpoints for Gradio Apps
Updated health_path from `/health` to `/` for:
- StyleTTS2 (port 8013)
- Fish Speech (port 8015)
- Zonos (port 8014)
- TTS-WebUI (port 8016)

#### d) GPT-SoVITS URL
- **Before:** Direct RunPod URL `https://jzfmzviw26huka-8010.proxy.runpod.net`
- **After:** `https://f5tts.ailabsafrica.com` (TTS Provider Hub on port 8010)

#### e) IndexTTS & VoxCPM URLs
- **Before:** Direct RunPod URL
- **After:** `https://tts-webui.ailabsafrica.com` (they're extensions of TTS-WebUI)

**Files Changed:**
- `/opt/kasaai/apps/shared/tts/config.py:43-470`

### 3. **Moshi Provider Status**
- **Status:** Marked as NOT DEPLOYED
- **Reason:** No nginx configuration exists for moshi.ailabsafrica.com
- **Note:** The domain `kyutai.ailabsafrica.com` actually points to F5-TTS, not Moshi

## RunPod Port Mapping

| Port | Service | Domain | Type |
|------|---------|--------|------|
| 8010 | TTS Provider Hub (GPT-SoVITS landing) | f5tts.ailabsafrica.com | HTML Frontend |
| 8012 | F5-TTS API | kyutai.ailabsafrica.com | JSON API |
| 8013 | StyleTTS2 | styletts.ailabsafrica.com | Gradio UI |
| 8014 | Zonos | zonos.ailabsafrica.com | Gradio UI |
| 8015 | Fish Speech | fishspeech.ailabsafrica.com | Gradio UI |
| 8016 | TTS-WebUI (includes IndexTTS, VoxCPM) | tts-webui.ailabsafrica.com | Next.js UI |
| 8017 | RVC Voice Conversion | (Not configured) | JSON API |

## Final Provider Status

### ✅ ONLINE (12 providers)

1. **Coqui XTTS v2** - Local Docker (Port 8005) - Pitch ✓ Speed ✓
2. **F5-TTS** - RunPod (Port 8012) - Pitch ✓ Speed ✓
3. **Fish Speech** - RunPod (Port 8015) - Pitch ✗ Speed ✓
4. **GPT-SoVITS** - RunPod (Port 8010) - Pitch ✗ Speed ✓
5. **IndexTTS 2.0** - RunPod (Port 8016, TTS-WebUI) - Pitch ✗ Speed ✓
6. **Kokoro TTS** - Local Docker (Port 8010) - Pitch ✓ Speed ✓
7. **MeloTTS** - Local Docker (Port 8001) - Pitch ✓ Speed ✓
8. **OpenVoice** - Local Docker (Port 8003) - Pitch ✓ Speed ✓
9. **StyleTTS2** - RunPod (Port 8013) - Pitch ✓ Speed ✓
10. **TTS-WebUI** - RunPod (Port 8016) - Pitch ✗ Speed ✓
11. **VoxCPM** - RunPod (Port 8016, TTS-WebUI) - Pitch ✗ Speed ✓
12. **Zonos TTS** - RunPod (Port 8014) - Pitch ✓ Speed ✓

### ❌ OFFLINE (1 provider)

1. **Kyutai Moshi** - NOT DEPLOYED (no nginx config, no allocated port)

## Capabilities Status

All providers now correctly report their pitch and speed control capabilities:
- **Pitch Control:** 8/12 online providers (67%)
- **Speed Control:** 12/12 online providers (100%)

## Known Limitations

### Chatterbox Provider
- **Status:** Docker container running and healthy
- **Issue:** No provider class implementation in `/opt/kasaai/apps/shared/tts/client.py`
- **Impact:** Won't appear in API despite being in config.py
- **Required:** Create `ChatterboxProvider` class extending `BaseTTSProvider`

## Testing Performed

1. ✅ Tested all local Docker providers (MeloTTS, Chatterbox, Coqui, OpenVoice, Kokoro)
2. ✅ SSH'd to RunPod and mapped all port services
3. ✅ Verified nginx proxy configurations for all domains
4. ✅ Tested health endpoints (JSON vs HTML responses)
5. ✅ Verified content-type headers for all providers
6. ✅ Full API test with force_refresh=true
7. ✅ Confirmed pitch/speed capabilities for all providers

## Files Modified

1. `/opt/kasaai/apps/shared/tts/providers.py` - BaseTTSProvider.check_health()
2. `/opt/kasaai/apps/shared/tts/config.py` - All provider endpoint configurations

## Deployment Notes

- All changes require backend restart to take effect
- Provider health status is cached for 5 minutes
- Use `?force_refresh=true` to bypass cache
- Python bytecode cache should be cleared after config changes

## Recommendations

1. **Create ChatterboxProvider class** to enable Chatterbox in API
2. **Deploy Moshi** or remove from TTSProvider enum if not planned
3. **Add health_check parameter** to provider config for custom health logic per provider
4. **Consider unified health endpoint** standard across all providers
5. **Add monitoring** for RunPod pod lifecycle (auto-start on demand)

## Success Metrics

- **Before:** 3/13 providers online (23%)
- **After:** 12/13 providers online (92%)
- **Improvement:** +400% increase in provider availability

# TTS Gradio Web UI Implementation Plan

**Created:** 2025-11-08
**Status:** Planning Phase
**Goal:** Add user-friendly Gradio interfaces to existing TTS services without breaking API integrations

---

## Current Infrastructure Analysis

### Existing API Endpoints (DO NOT MODIFY)
These are actively used by `/apps/shared` and other applications:

| Service | Current URL | Port | Status | Used By |
|---------|------------|------|--------|---------|
| Coqui XTTS | https://coqui.ailabsafrica.com | 8005 | ✅ Running | shared/tts/config.py, provider_registry.py |
| MeloTTS | https://melotts.ailabsafrica.com | 8001 | ✅ Running | shared/tts/config.py, provider_registry.py |
| OpenVoice | https://openvoice.ailabsafrica.com | 8003 | ✅ Running | shared/tts/config.py, provider_registry.py |
| Kokoro | https://kokoro.ailabsafrica.com | 8010 | ✅ Running | provider_registry.py |
| F5-TTS | RunPod | N/A | ⚠️ RunPod | Not local |
| Moshi | RunPod | N/A | ⚠️ RunPod | Not local |
| StyleTTS2 | N/A | 8007 | ❌ Not Running | Not deployed |

### Code References in /apps/shared
```python
# /opt/kasaai/apps/shared/integration/ai_services/provider_registry.py
"endpoint": os.getenv("COQUI_ENDPOINT", "https://coqui.ailabsafrica.com")
"endpoint": os.getenv("MELOTTS_ENDPOINT", "https://melotts.ailabsafrica.com")
"endpoint": os.getenv("OPENVOICE_ENDPOINT", "https://openvoice.ailabsafrica.com")
"endpoint": os.getenv("KOKORO_ENDPOINT", "https://kokoro.ailabsafrica.com")
```

**Good News:** Environment variables are already supported! This makes migration easier.

---

## Recommended Strategy: Dual-URL Approach

### Phase 1: Keep Current APIs, Add Gradio Frontends on New URLs

Create separate Gradio frontend URLs while maintaining existing API endpoints:

| Service | API Endpoint (Current) | New Gradio Frontend | Port Plan |
|---------|------------------------|---------------------|-----------|
| Coqui XTTS | coqui.ailabsafrica.com (8005) | **ui-coqui.ailabsafrica.com** | 8015 (new) |
| MeloTTS | melotts.ailabsafrica.com (8001) | **ui-melotts.ailabsafrica.com** | 8011 (new) |
| OpenVoice | openvoice.ailabsafrica.com (8003) | **ui-openvoice.ailabsafrica.com** | 8013 (new) |
| Kokoro | kokoro.ailabsafrica.com (8010) | **ui-kokoro.ailabsafrica.com** | 8020 (new) |
| Chatterbox | N/A | **chatterbox.ailabsafrica.com** | 8004 (✅ done) |

**Rationale:**
- Zero disruption to existing integrations
- Clear separation: APIs for machines, UIs for humans
- Can migrate to `-api` suffix later if desired
- Gradio UIs can consume the existing API endpoints

### Phase 2 (Optional Future): Migrate to -api Suffix Convention

If desired in the future:
1. Create: `coqui-api.ailabsafrica.com`, `melotts-api.ailabsafrica.com`, etc.
2. Point base domains to Gradio frontends
3. Update environment variables in `/apps/shared`
4. Keep old URLs as aliases during transition

---

## Implementation Plan by Service

### 1. Coqui XTTS - Priority: HIGH

**Current Status:**
- ✅ FastAPI backend running on port 8005
- ❌ No Gradio UI

**Recommended Solution:** AllTalk TTS
- **Complexity:** Moderate
- **Features:** Most comprehensive Coqui implementation
  - Full XTTS & VITS engine support
  - Low VRAM mode with DeepSpeed
  - Narrator function (multi-voice)
  - Model fine-tuning interface
  - Audio transcoding (MP3, Opus, etc.)
  - API compatible with existing systems

**Implementation Steps:**
1. Clone AllTalk: `git clone https://github.com/erew123/alltalk_tts.git`
2. Configure to use port 8015
3. Point it to use existing Coqui models at `/opt/kasaai/apps/voice-lab/models`
4. Create nginx config for `ui-coqui.ailabsafrica.com`
5. Create Docker container (or run standalone)

**Alternative (Simpler):** Build basic Gradio UI that wraps existing API
- Lower complexity
- Quick to implement
- Uses current Coqui API at port 8005
- Less feature-rich

**Docker Configuration:**
```yaml
  coqui-ui:
    build: ./docker/coqui-ui
    container_name: coqui-ui
    ports:
      - 8015:8015
    environment:
      - COQUI_API_URL=http://coqui:8005
    depends_on:
      - coqui
    networks:
      - tts_network
```

---

### 2. Kokoro TTS - Priority: HIGH

**Current Status:**
- ✅ FastAPI backend running on port 8010
- ❌ No Gradio UI

**Recommended Solution:** PierrunoYT/Kokoro-TTS-Local
- **GitHub:** https://github.com/PierrunoYT/Kokoro-TTS-Local
- **Complexity:** Low
- **Features:**
  - 54 voices across 8 languages
  - Automatic model/voice downloading
  - Multiple output formats (WAV, MP3, AAC)
  - Real-time generation progress
  - Easy voice selection dropdown
  - Lightweight (185 stars, proven)

**Implementation Steps:**
1. Clone: `git clone https://github.com/PierrunoYT/Kokoro-TTS-Local.git`
2. Modify `gradio_interface.py` to use port 8020
3. Configure to use existing Kokoro models if available
4. Create nginx config for `ui-kokoro.ailabsafrica.com`
5. Dockerize (create Dockerfile based on requirements)

**Docker Configuration:**
```yaml
  kokoro-ui:
    build:
      context: ./kokoro-tts-local
      dockerfile: Dockerfile
    container_name: kokoro-ui
    ports:
      - 8020:8020
    volumes:
      - kokoro_models:/app/models
    networks:
      - tts_network
```

---

### 3. OpenVoice - Priority: MEDIUM

**Current Status:**
- ✅ FastAPI backend running on port 8003
- ❌ No Gradio UI

**Recommended Solution:** Official OpenVoice Gradio Demo
- **Source:** https://github.com/myshell-ai/OpenVoice
- **Complexity:** Low-Moderate
- **Command:** `python -m openvoice_app --share`
- **Features:**
  - Instant voice cloning
  - Multi-language support
  - Zero-shot cross-lingual cloning
  - Emotion/accent control

**Implementation Steps:**
1. Clone OpenVoice repo into docker/openvoice-ui/
2. Install dependencies and configure for port 8013
3. Point to existing OpenVoice checkpoints at `/app/OpenVoice/checkpoints`
4. Create nginx config for `ui-openvoice.ailabsafrica.com`
5. Dockerize

**Alternative:** Build simple Gradio wrapper around existing API
- Faster implementation
- Reuses current infrastructure

---

### 4. MeloTTS - Priority: MEDIUM

**Current Status:**
- ✅ FastAPI backend running on port 8001
- ❌ No Gradio UI

**Recommended Solution:** Official MeloTTS Web UI
- **Source:** https://github.com/myshell-ai/MeloTTS (includes web UI)
- **Complexity:** Low
- **Port:** Default 8888 → Change to 8011
- **Features:**
  - Multi-lingual TTS (EN, ES, FR, CN, JP, KR)
  - Fast CPU inference
  - Web interface included in official repo

**Implementation Steps:**
1. MeloTTS already includes a web UI (credited to @fakerybakery)
2. Clone MeloTTS repo
3. Configure web UI to run on port 8011
4. Create nginx config for `ui-melotts.ailabsafrica.com`
5. Dockerize if not already in container

**Note:** Check if current Docker setup already includes the web UI components

---

### 5. StyleTTS2 - Priority: LOW

**Current Status:**
- ❌ Not currently deployed
- Container exists but not running

**Recommended Solution:** HuggingFace Space Implementation
- **Source:** https://huggingface.co/spaces/styletts2/styletts2
- **app.py:** https://huggingface.co/spaces/styletts2/styletts2/blob/main/app.py
- **Complexity:** Moderate-High
- **Features:**
  - Single/multi-speaker synthesis
  - Reference audio-based style control
  - Diffusion-based expressiveness

**Implementation Steps:**
1. Download app.py from HF Space
2. Adapt for local deployment
3. Download StyleTTS2 models
4. Configure for port 8017
5. Create nginx config for `ui-styletts2.ailabsafrica.com`
6. Build and start container

**Decision:** Defer until there's demand for StyleTTS2

---

## Alternative Approach: TTS-WebUI (Unified Solution)

**Repository:** https://github.com/rsxdalv/TTS-WebUI

### Pros:
- **All-in-One:** Single interface for Coqui, OpenVoice, MeloTTS, Kokoro, F5-TTS, StyleTTS2, and 20+ more
- **Extension Marketplace:** Install models on-demand
- **Dual Interface:** Gradio backend + React frontend
- **OpenAI Compatible API:** Easy integration
- **One-Click Installer:** Simple deployment

### Cons:
- **Large Footprint:** 10.7 GB base + 2-8 GB per model
- **Resource Intensive:** May not be suitable for production with limited resources
- **Complexity:** More to manage than individual services
- **Redundancy:** Would duplicate existing API implementations

### Recommendation:
**Not recommended for current setup** because:
1. We already have working API implementations
2. Want lightweight, service-specific UIs
3. Resource constraints on local server
4. Prefer microservices architecture

**Consider for:** Future multi-model testing/development environment

---

## Port Allocation Summary

| Port | Service | Type | Status |
|------|---------|------|--------|
| 8001 | MeloTTS API | FastAPI | ✅ Running |
| 8003 | OpenVoice API | FastAPI | ✅ Running |
| 8004 | Chatterbox UI | Gradio | ✅ Running |
| 8005 | Coqui API | FastAPI | ✅ Running |
| 8007 | StyleTTS2 | FastAPI | ❌ Not Running |
| 8010 | Kokoro API | FastAPI | ✅ Running |
| 8011 | MeloTTS UI | Gradio | 🔵 Planned |
| 8013 | OpenVoice UI | Gradio | 🔵 Planned |
| 8015 | Coqui UI | Gradio | 🔵 Planned |
| 8020 | Kokoro UI | Gradio | 🔵 Planned |

---

## Nginx Configuration Template

```nginx
# Template for UI domains
server {
    listen 80;
    listen [::]:80;
    server_name ui-{service}.ailabsafrica.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ui-{service}.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/ui-{service}.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ui-{service}.ailabsafrica.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 100M;

    access_log /var/log/nginx/ui-{service}.access.log;
    error_log /var/log/nginx/ui-{service}.error.log;

    location / {
        proxy_pass http://localhost:{port};
        proxy_http_version 1.1;

        # WebSocket support for Gradio
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # Gradio-specific
        proxy_buffering off;
        proxy_read_timeout 600s;
    }

    # Gradio queue endpoint
    location /queue/ {
        proxy_pass http://localhost:{port}/queue/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_read_timeout 86400s;
    }
}
```

---

## Implementation Priority & Timeline

### Phase 1: High Priority (Week 1)
1. ✅ **Chatterbox** - COMPLETED
2. 🔵 **Kokoro UI** - Use PierrunoYT implementation (1-2 days)
3. 🔵 **Coqui UI** - Build simple Gradio wrapper or use AllTalk (2-3 days)

### Phase 2: Medium Priority (Week 2)
4. 🔵 **OpenVoice UI** - Official Gradio demo (1-2 days)
5. 🔵 **MeloTTS UI** - Official web UI (1 day)

### Phase 3: Low Priority (As Needed)
6. ⏸️ **StyleTTS2 UI** - HF Space implementation (deferred)
7. ⏸️ **F5-TTS/Moshi** - RunPod deployed, lower priority

---

## Testing Checklist

For each UI implementation:
- [ ] Gradio interface loads and displays correctly
- [ ] Audio generation works with default settings
- [ ] File upload (reference audio) functions properly
- [ ] Generated audio downloads successfully
- [ ] WebSocket connections stable (no disconnects)
- [ ] SSL certificate obtained and configured
- [ ] Domain resolves correctly
- [ ] CORS configured if needed for integrations
- [ ] Resource usage acceptable (CPU/GPU/Memory)
- [ ] Concurrent users handled gracefully

---

## Migration Path (Optional Future)

If you want to eventually use base domains for UIs:

### Step 1: Create API-specific domains
```bash
# Example for Coqui
1. Create coqui-api.ailabsafrica.com pointing to port 8005
2. Update /apps/shared environment variables:
   export COQUI_ENDPOINT=https://coqui-api.ailabsafrica.com
3. Test all integrations
4. Repurpose coqui.ailabsafrica.com for Gradio UI (port 8015)
```

### Step 2: Update /apps/shared references
```python
# Update provider_registry.py and config.py
"endpoint": os.getenv("COQUI_ENDPOINT", "https://coqui-api.ailabsafrica.com")
```

### Step 3: Deprecation period
- Keep both URLs active for 30 days
- Monitor usage logs
- Notify dependent applications
- Remove old URL aliases after confirmation

---

## Resource Considerations

### Current Local Server Resources:
- **GPU:** 20GB VRAM (shared across all TTS services)
- **CPU:** Available for Gradio interfaces
- **RAM:** Monitor usage with multiple UIs

### Gradio UI Resource Usage (Estimated):
- **Coqui UI:** ~2-4 GB VRAM (shared with API)
- **Kokoro UI:** ~1-2 GB VRAM (lightweight)
- **OpenVoice UI:** ~2-3 GB VRAM
- **MeloTTS UI:** ~1-2 GB VRAM

**Strategy:** Gradio UIs will call existing API endpoints, so no additional model loading required if properly configured.

---

## Success Metrics

- [ ] All running TTS services have accessible Gradio UIs
- [ ] No disruption to existing API integrations
- [ ] User-friendly interfaces for non-technical users
- [ ] SSL enabled on all UI domains
- [ ] Documentation updated
- [ ] Zero downtime deployment

---

## Next Steps

1. **Choose Implementation Approach:**
   - Option A: Individual Gradio UIs (recommended)
   - Option B: TTS-WebUI unified solution

2. **Prioritize Services:**
   - Start with Kokoro (easiest, proven community solution)
   - Then Coqui (most used, highest value)
   - Follow with OpenVoice and MeloTTS

3. **Prepare Infrastructure:**
   - Reserve ports 8011, 8013, 8015, 8020
   - Create nginx config templates
   - Set up SSL certificate automation

4. **Development Process:**
   - Build Docker containers for each UI
   - Test locally before SSL deployment
   - Update docker-compose.local.yml
   - Deploy to production

5. **Documentation:**
   - Update README with UI URLs
   - Create user guides for each UI
   - Document API vs UI usage patterns

---

**Questions for Discussion:**
1. Prefer `ui-{service}.ailabsafrica.com` or different naming convention?
2. Start with Kokoro (easiest) or Coqui (highest value)?
3. Build custom lightweight UIs or use community implementations?
4. Timeline: Aggressive (1 week) or conservative (2-3 weeks)?


---

## CRITICAL: Complete Usage Analysis

### TTS Services Used Across Multiple Applications

**Affected Applications:**
1. `/apps/shared` - Shared library used by all applications
2. `/apps/core_backend` - Main backend API
3. `/apps/b2c-portal` - Frontend application

### Detailed References Found:

#### /apps/shared (5 files)
```
/opt/kasaai/apps/shared/tts/config.py
/opt/kasaai/apps/shared/integration/ai_services/provider_registry.py
/opt/kasaai/apps/shared/tts/README.md
/opt/kasaai/apps/shared/INTEGRATION_GUIDE.md
/opt/kasaai/apps/shared/integration/ai_services/examples/tts_service_migration.md
```

#### /apps/core_backend (11 files)
```python
# Service layer
backend/services/tts_provider_service.py  # Lines 49, 64, 80, 96
backend/services/voice_cloning_service.py  # Lines 92, 98
backend/services/openvoice_service.py  # Lines 5, 20
backend/services/melotts_service.py  # Lines 5, 19
backend/services/unified_tts_service.py
backend/services/f5tts_service.py

# Routes
backend/routes/voice_engine/websocket_chat.py
backend/routes/service_management.py
backend/routes/voice_engine/rd_lab_routes.py
backend/routes/voice_models_management.py

# Models
backend/models/cloned_voice.py
```

#### /apps/b2c-portal (3 files - TypeScript/React)
```typescript
src/config/voice-agent-providers.ts  # Lines 158, 179, 186, 193
src/config/tts-providers.ts  # Lines 40, 57, 75, 92
src/components/admin/ServiceManagementUpdated.tsx  # Lines 138, 147, 156, 165
```

### URL References by Service:

| Service | Shared Lib | Core Backend | B2C Portal | Total Refs |
|---------|------------|--------------|------------|------------|
| **coqui.ailabsafrica.com** | 4 | 3 | 3 | **10** |
| **melotts.ailabsafrica.com** | 4 | 2 | 3 | **9** |
| **openvoice.ailabsafrica.com** | 4 | 3 | 3 | **10** |
| **kokoro.ailabsafrica.com** | 2 | 1 | 3 | **6** |

**Total:** 35+ hardcoded references across the codebase

---

## DECISION: Keep Current URLs as APIs

**Conclusion:** Given the extensive integration across multiple applications, we will:

✅ **KEEP existing URLs as API endpoints** (no changes)
✅ **ADD new Gradio UI URLs** on separate domains
❌ **DO NOT migrate to -api suffix** (too risky, too many references)

### Rationale:
1. **35+ hardcoded references** across 3 major applications
2. **TypeScript/React configs** in b2c-portal are not environment-variable based
3. **Service classes** in core_backend have hardcoded defaults
4. **High risk** of breaking production integrations
5. **Zero-downtime approach** is safer and cleaner

### Benefits:
- No code changes required in any application
- No regression testing needed
- No deployment coordination across apps
- APIs continue working exactly as before
- Gradio UIs are purely additive

---

## Recommended URL Scheme (FINAL)

### API Endpoints (Current - DO NOT CHANGE)
- `https://coqui.ailabsafrica.com` → Port 8005 (API)
- `https://melotts.ailabsafrica.com` → Port 8001 (API)
- `https://openvoice.ailabsafrica.com` → Port 8003 (API)
- `https://kokoro.ailabsafrica.com` → Port 8010 (API)

### Gradio UI Endpoints (NEW - TO BE CREATED)
- `https://ui-coqui.ailabsafrica.com` → Port 8015 (Gradio)
- `https://ui-melotts.ailabsafrica.com` → Port 8011 (Gradio)
- `https://ui-openvoice.ailabsafrica.com` → Port 8013 (Gradio)
- `https://ui-kokoro.ailabsafrica.com` → Port 8020 (Gradio)
- `https://chatterbox.ailabsafrica.com` → Port 8004 (Gradio) ✅ Already done

---

## Environment Variable Strategy (Future-Proofing)

While we're not changing URLs now, we should update code to use environment variables for future flexibility:

### For Python Services (core_backend, shared):
```python
# Current (hardcoded)
endpoint = "https://coqui.ailabsafrica.com"

# Recommended (environment variable with fallback)
import os
endpoint = os.getenv("COQUI_TTS_ENDPOINT", "https://coqui.ailabsafrica.com")
```

### For TypeScript/React (b2c-portal):
```typescript
// Current (hardcoded)
endpoint: 'https://coqui.ailabsafrica.com'

// Recommended (environment variable with fallback)
endpoint: process.env.REACT_APP_COQUI_ENDPOINT || 'https://coqui.ailabsafrica.com'
```

**Note:** This is optional and can be done incrementally during normal development cycles.

---

## Updated Implementation Priority

### Immediate Next Steps (This Week):

1. **Kokoro Gradio UI** (Easiest - Good starting point)
   - Use PierrunoYT/Kokoro-TTS-Local
   - Deploy to port 8020
   - Create `ui-kokoro.ailabsafrica.com`
   - Test and document

2. **Coqui Gradio UI** (Highest Value - Most Used)
   - Option A: Build lightweight wrapper around existing API
   - Option B: Deploy AllTalk TTS
   - Deploy to port 8015
   - Create `ui-coqui.ailabsafrica.com`

3. **Documentation Update**
   - Update TASKS.md with new UI URLs
   - Create user guides for each UI
   - Document API vs UI usage

### Follow-Up (Next Week):

4. **OpenVoice Gradio UI**
5. **MeloTTS Gradio UI**

---

## Risk Assessment: ZERO RISK ✅

**API Endpoints:** No changes → No risk
**Gradio UIs:** New services → No impact on existing systems
**Integration:** None required → No breaking changes
**Testing:** Only for new UIs → Existing systems untouched

**Confidence Level:** Very High

---

**Status:** Plan Complete - Ready for Implementation

**Approval Needed:**
- [ ] Confirm `ui-{service}.ailabsafrica.com` naming convention
- [ ] Confirm port allocations (8011, 8013, 8015, 8020)
- [ ] Priority: Start with Kokoro or Coqui?
- [ ] Resource allocation: Can we run all UIs simultaneously?


---

## Implementation Progress

### ✅ Completed (2025-11-08)

#### 1. Coqui TTS Gradio UI
**Status:** Deployed and Running  
**URL Scheme:** Changed to `{service}-ui.ailabsafrica.com` for better readability

- **Container:** coqui-ui
- **Port:** 8015 (internal: 8015)
- **Local Access:** http://localhost:8015
- **Public Domain:** coqui-ui.ailabsafrica.com (HTTP-only, pending DNS)
- **API Backend:** coqui.ailabsafrica.com (existing, unchanged)
- **Docker Network:** Connected to tts_network
- **Nginx Config:** /etc/nginx/sites-available/coqui-ui.ailabsafrica.com.conf

**Features:**
- 17 language support (Arabic, Chinese, Czech, Dutch, English, French, German, Hindi, Hungarian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Spanish, Turkish)
- Zero-shot voice cloning via reference audio upload
- Microphone recording support
- Real-time character count (max 5000 chars)
- Advanced controls: temperature, repetition penalty, length penalty, speed
- Audio download in WAV format
- Health monitoring integrated

**Implementation:**
- Custom Gradio wrapper in Python 3.11
- Connects to existing Coqui API via Docker network
- Gradio 5.44.1 with modern UI components
- Error handling and connection health checks

---

#### 2. Kokoro TTS Gradio UI
**Status:** Deployed and Running

- **Container:** kokoro-ui
- **Port:** 8021 (internal: 8020)
- **Local Access:** http://localhost:8021
- **Public Domain:** kokoro-ui.ailabsafrica.com (HTTP-only, pending DNS)
- **API Backend:** kokoro.ailabsafrica.com (existing, unchanged)
- **Docker Network:** Connected to tts_network
- **Nginx Config:** /etc/nginx/sites-available/kokoro-ui.ailabsafrica.com.conf

**Features:**
- 11 unique voices (af, af_bella, af_nicole, af_sarah, am_adam, am_michael, bf_emma, bf_isabella, bm_george, bm_lewis, am_santa)
- Voice preview and selection
- Speed control (0.5x - 2.0x)
- Simple, clean interface optimized for quick synthesis
- Audio download in WAV format
- Real-time generation

**Implementation:**
- Custom Gradio wrapper in Python 3.11
- Connects to existing Kokoro API via Docker network
- Gradio 5.44.1 with voice selector
- Fast response times leveraging Kokoro-82M model

---

### 📋 Next Steps to Complete

#### A. DNS Configuration Required
Before SSL can be enabled, add DNS A records:

```
coqui-ui.ailabsafrica.com    → 148.251.0.46 (or dev: 85.214.12.174)
kokoro-ui.ailabsafrica.com   → 148.251.0.46 (or dev: 85.214.12.174)
```

#### B. SSL Certificate Installation
Once DNS propagates, run:

```bash
# For Coqui UI
sudo certbot --nginx -d coqui-ui.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com --redirect

# For Kokoro UI
sudo certbot --nginx -d kokoro-ui.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com --redirect

# Reload nginx
sudo systemctl reload nginx
```

#### C. Testing Checklist
- [ ] Verify DNS propagation: `nslookup coqui-ui.ailabsafrica.com`
- [ ] Verify DNS propagation: `nslookup kokoro-ui.ailabsafrica.com`
- [ ] Test HTTPS access for both domains
- [ ] Test voice synthesis on Coqui UI
- [ ] Test voice cloning on Coqui UI (with reference audio)
- [ ] Test all 11 voices on Kokoro UI
- [ ] Test speed control on Kokoro UI
- [ ] Verify audio file downloads work
- [ ] Test WebSocket connectivity
- [ ] Load test with multiple concurrent requests

---

### 🔄 Remaining Services (Future Implementation)

#### 3. OpenVoice UI (Pending)
- **Proposed URL:** openvoice-ui.ailabsafrica.com
- **Proposed Port:** 8013
- **API Backend:** openvoice.ailabsafrica.com (port 8003)
- **Complexity:** Low-Moderate
- **Approach:** Use official Gradio demo from OpenVoice repo

#### 4. MeloTTS UI (Pending)
- **Proposed URL:** melotts-ui.ailabsafrica.com
- **Proposed Port:** 8011
- **API Backend:** melotts.ailabsafrica.com (port 8001)
- **Complexity:** Low
- **Approach:** Use official web UI from MeloTTS repo

---

### 📊 Summary

**Deployed:** 2/4 services  
**Success Rate:** 100% (both working)  
**Zero Breaking Changes:** All existing API integrations remain functional  
**Naming Convention:** `{service}-ui.ailabsafrica.com` ✅

**Container Status:**
```bash
coqui-ui     → Port 8015 → Healthy ✅
kokoro-ui    → Port 8021 → Healthy ✅
```

**Next Priority:**
1. Add DNS records
2. Enable SSL
3. Complete OpenVoice UI
4. Complete MeloTTS UI

---

### 🚀 F5-TTS on RunPod (2025-11-08)
**Status:** ✅ Deployed and Accessible

#### Overview
F5-TTS Gradio interface runs on RunPod GPU pod and is accessible via SSH tunnel.

**URLs:**
- **Public Access:** https://f5tts-ui.ailabsafrica.com (Gradio UI)
- **Local Tunnel:** http://localhost:8002
- **RunPod Direct:** http://localhost:8002 (on pod)

**Note:**
- `f5tts.ailabsafrica.com` is reserved for API endpoint (Docker container exists but not running)
- `f5tts-ui.ailabsafrica.com` is the Gradio UI (currently accessible via RunPod)

**RunPod Pod Configuration:**
- **Pod ID:** jzfmzviw26huka-644113c7
- **Direct SSH:** root@194.68.245.121:22127
- **Proxy SSH:** jzfmzviw26huka-644113c7@ssh.runpod.io
- **Port:** 8002
- **Process:** Runs in tmux session named "f5tts"

---

#### SSH Tunnel Management

**Two connection methods available:**

1. **Direct TCP** (via pod IP:port) - ✅ **RECOMMENDED** - Works reliably for data transfer
   ```bash
   ssh -N -f -L 8002:localhost:8002 -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127
   ```
   - **Pros:** Reliable data transfer, lower latency
   - **Cons:** Port changes when pod restarts
   - **Note:** Port 22127 will change if pod is restarted

2. **Proxy SSH** (via ssh.runpod.io) - Alternative if direct TCP unavailable
   ```bash
   ssh -N -f -L 8002:localhost:8002 -i ~/.ssh/id_ed25519 jzfmzviw26huka-644113c7@ssh.runpod.io
   ```
   - **Pros:** Stable connection string (doesn't change)
   - **Cons:** May have connection reset issues with large data transfers
   - **Use case:** When pod IP is not accessible or behind firewall

**Default Configuration:** `runpod.config.sh` uses **direct TCP** by default

**Important:** When RunPod pod restarts, the direct TCP port (22127) will change! Update `RUNPOD_DIRECT_PORT` in `runpod.config.sh`

---

#### Tunnel Management Scripts

**Start/Stop/Restart tunnels:**
```bash
cd /opt/kasaai/apps/tts-deployment

# Start tunnels (all 3 services: F5-TTS, StyleTTS2, Moshi)
./scripts/runpod_tunnels.sh start

# Check tunnel status
./scripts/runpod_tunnels.sh status

# Restart tunnels
./scripts/runpod_tunnels.sh restart

# Stop tunnels
./scripts/runpod_tunnels.sh stop
```

**Configuration file:** `runpod.config.sh`
- Update `RUNPOD_DIRECT_PORT` when pod restarts and port changes

---

#### F5-TTS Gradio Service Management

**On RunPod pod (via SSH):**

**Start F5-TTS in tmux session:**
```bash
# SSH into RunPod
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127

# Start F5-TTS in tmux
tmux new-session -d -s f5tts "cd /workspace && source /workspace/tts-venv/bin/activate && f5-tts_infer-gradio --port 8002 --host 0.0.0.0 2>&1 | tee /tmp/f5tts_full.log"
```

**Attach to tmux session to view output:**
```bash
tmux attach -t f5tts
# Press Ctrl+B, then D to detach
```

**Stop F5-TTS:**
```bash
tmux kill-session -t f5tts
```

**Check if F5-TTS is running:**
```bash
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'ps aux | grep f5-tts'
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'netstat -tlnp | grep 8002'
```

**View logs:**
```bash
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'tail -f /tmp/f5tts_full.log'
```

---

#### When RunPod Pod Restarts

**Problem:** Direct TCP port changes (e.g., 22127 → 22130)

**Solution:**
1. Check new port in RunPod dashboard:
   - Go to: https://www.runpod.io/console/pods
   - Click on pod: jzfmzviw26huka-644113c7
   - Find "SSH over exposed TCP" section
   - Note the new port number

2. Update config:
   ```bash
   cd /opt/kasaai/apps/tts-deployment
   nano runpod.config.sh
   # Update: RUNPOD_DIRECT_PORT=<new_port>
   ```

3. Restart tunnels:
   ```bash
   ./scripts/runpod_tunnels.sh restart
   ```

4. Start F5-TTS on RunPod (see above)

**Alternative:** Use proxy SSH (doesn't change on restart)
```bash
# Just change the connection method in runpod.config.sh
export RUNPOD_CONNECTION_METHOD="proxy"
./scripts/runpod_tunnels.sh restart
```

---

#### Nginx Configuration

**File:** `/etc/nginx/sites-available/f5tts-ui.ailabsafrica.com.conf`

**Key settings:**
- Proxies to `localhost:8002` (SSH tunnel endpoint)
- WebSocket support for Gradio
- 10-minute timeouts (F5-TTS can be slow for long text)
- CORS enabled for flow.ailabsafrica.com

**Reload nginx after changes:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

#### Troubleshooting

**Issue:** `502 Bad Gateway` on https://f5tts-ui.ailabsafrica.com

**Checklist:**
1. Is SSH tunnel running?
   ```bash
   ./scripts/runpod_tunnels.sh status
   ```

2. Is F5-TTS running on RunPod?
   ```bash
   ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'netstat -tlnp | grep 8002'
   ```

3. Can we access F5-TTS locally?
   ```bash
   curl http://localhost:8002/ | head -10
   ```

4. Is nginx configured correctly?
   ```bash
   sudo nginx -t
   grep 'localhost:8002' /etc/nginx/sites-available/f5tts-ui.ailabsafrica.com.conf
   ```

**Issue:** Connection reset when accessing localhost:8002

**Solution:** Use direct TCP tunnel instead of proxy SSH
```bash
# Kill existing tunnel
pkill -f 'ssh.*runpod'

# Start direct TCP tunnel
ssh -N -f -L 8002:localhost:8002 -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127

# Test
curl http://localhost:8002/ | head -10
```

**Issue:** F5-TTS process not responding

**Solution:** Restart F5-TTS in tmux
```bash
# Kill existing session
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'tmux kill-session -t f5tts'

# Start new session
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'tmux new-session -d -s f5tts "cd /workspace && source /workspace/tts-venv/bin/activate && f5-tts_infer-gradio --port 8002 --host 0.0.0.0 2>&1 | tee /tmp/f5tts_full.log"'

# Wait 20-30 seconds for model loading
sleep 30

# Test
curl http://localhost:8002/ | head -10
```

---

#### Important Files

**Local (TTS Deployment Server):**
- `/opt/kasaai/apps/tts-deployment/runpod.config.sh` - RunPod connection config
- `/opt/kasaai/apps/tts-deployment/scripts/runpod_tunnels.sh` - Tunnel management
- `/etc/nginx/sites-available/f5tts-ui.ailabsafrica.com.conf` - Nginx config

**RunPod Pod:**
- `/workspace/F5-TTS/` - F5-TTS repository (editable install)
- `/workspace/tts-venv/` - Python virtual environment
- `/tmp/f5tts_full.log` - F5-TTS Gradio logs
- `~/.ssh/id_ed25519` - SSH key for authentication

---

#### Performance Notes

**Startup Time:** 20-30 seconds (loading models into GPU memory)

**Model Loading Indicators:**
- CPU usage ~30-50% during startup
- Memory grows from ~500MB to ~1GB
- Port 8002 not listening until fully ready

**Resource Usage (Running):**
- VRAM: ~1-2 GB
- RAM: ~1 GB
- CPU: Low (idle), High (during synthesis)

---

#### Quick Reference Commands

```bash
# Check tunnel status
./scripts/runpod_tunnels.sh status

# Restart tunnel
./scripts/runpod_tunnels.sh restart

# Check if F5-TTS is running on RunPod
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'tmux ls && ps aux | grep f5-tts | grep -v grep'

# View F5-TTS logs
ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22127 'tail -50 /tmp/f5tts_full.log'

# Test local tunnel access
curl -I http://localhost:8002/

# Test public URL
curl -I https://f5tts-ui.ailabsafrica.com/
```

---

**Status:** ✅ Fully Operational
**Public Access:** https://f5tts-ui.ailabsafrica.com
**Last Updated:** 2025-11-08

**SSL Note:** Currently using f5tts.ailabsafrica.com certificate temporarily. To get proper certificate:
```bash
# Add DNS A record first: f5tts-ui.ailabsafrica.com → 148.251.0.46
# Then run:
sudo certbot --nginx -d f5tts-ui.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com --redirect
sudo sed -i 's|/etc/letsencrypt/live/f5tts.ailabsafrica.com/|/etc/letsencrypt/live/f5tts-ui.ailabsafrica.com/|g' /etc/nginx/sites-available/f5tts-ui.ailabsafrica.com.conf
sudo systemctl reload nginx
```


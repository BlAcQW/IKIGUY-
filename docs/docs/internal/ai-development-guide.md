# AI Development Guide: Working with Claude on Multi-Project Architecture

## Overview

This guide provides best practices, pro tips, and essential guidelines for working with Claude AI on the KasaAI platform, which uses a shared library architecture serving multiple projects.

---

## Architecture Understanding

### Our Multi-Project Structure

```
/opt/kasaai/
├── apps/
│   ├── shared/              # Shared library for all projects
│   │   ├── auth/            # Supabase authentication
│   │   ├── services/        # Common services
│   │   ├── database/        # MongoDB utilities
│   │   ├── models/          # Shared data models
│   │   └── branding/        # Common assets
│   ├── core_backend/        # Main API (api.ailabsafrica.com)
│   ├── studyflow/           # Education platform
│   ├── churchflow/          # Church management
│   ├── eventflow/           # Event management
│   ├── inkwave/             # Content creation
│   ├── erp/                 # Enterprise resource planning
│   ├── developer_platform/  # Developer console
│   └── docs/                # This documentation site
└── .env                     # Shared environment variables
```

### Key Architectural Principles

1. **Shared Virtual Environment**: All backends use `/opt/kasaai/apps/venv`
2. **Common Authentication**: All apps use Supabase from `@shared/auth/`
3. **Unified Database**: MongoDB credentials in `/opt/kasaai/.env`
4. **Consistent Ports**: Each service has a dedicated port (30027-30035)
5. **Nginx Routing**: All apps behind reverse proxy with SSL

---

## Essential Prompt Guidelines

### 1. Always Provide Architecture Context

**❌ Bad Prompt:**
```
Add authentication to the user routes
```

**✅ Good Prompt:**
```
Add authentication to the user routes in @studyflow/backend/app/api/routes/users.py

Context:
- We use Supabase authentication from @shared/auth/
- All routes should use the get_current_user dependency
- Database operations use MongoDB via @shared/database/
- This follows the same pattern as @core_backend/ and @churchflow/
```

### 2. Specify Which Project You're Working On

**❌ Bad Prompt:**
```
Fix the login endpoint
```

**✅ Good Prompt:**
```
Fix the login endpoint in @core_backend/app/api/routes/auth.py

This is the main API used by @b2c-portal/ frontend.
The endpoint should return the same response format as documented in @docs/api-reference/
```

### 3. Reference Existing Implementations

**❌ Bad Prompt:**
```
Create a new CRUD API for schools
```

**✅ Good Prompt:**
```
Create a new CRUD API for schools in @studyflow/backend/

Follow the same pattern as:
- @studyflow/backend/app/api/routes/materials.py (existing CRUD example)
- @shared/services/base_service.py (base service class)
- Use organization scoping like other StudyFlow routes
```

### 4. Mention Impact on Other Projects

**❌ Bad Prompt:**
```
Update the authentication service
```

**✅ Good Prompt:**
```
Update the authentication service in @shared/auth/supabase_client.py

⚠️ IMPORTANT: This is used by ALL projects:
- @core_backend/
- @studyflow/
- @churchflow/
- @eventflow/
- @inkwave/
- @erp/
- @developer_platform/
- @docs/

Please ensure backward compatibility and update any affected imports across all projects.
```

### 5. Specify Testing Requirements

**❌ Bad Prompt:**
```
Add a new feature for payments
```

**✅ Good Prompt:**
```
Add a new feature for payment processing in @studyflow/backend/

Requirements:
- Create unit tests following @apps/core_backend/TEST_SUITE_ANALYSIS.md
- Test with real database integration (not mocks)
- Include CRUD tests: create, fetch, update, delete
- Verify data persistence in MongoDB
- Test organization scoping
```

---

## Best Practices for AI-Assisted Development

### 1. Use PLANNING.md and TASK.md

**Before Starting Any Task:**

```bash
# 1. Check if PLANNING.md exists in the project
cat /opt/kasaai/apps/studyflow/PLANNING.md

# 2. Check if TASK.md exists
cat /opt/kasaai/apps/studyflow/TASK.md

# 3. Add your task to TASK.md
echo "- [Date] Add payment processing feature" >> TASK.md
```

**In Your Prompt:**
```
I've added this task to @studyflow/TASK.md:
"- 2025-11-07: Add payment processing feature"

Please implement this following the architecture patterns in PLANNING.md
```

### 2. Request File Structure Exploration First

**For New Codebases:**
```
I need to understand the @studyflow/ codebase structure before making changes.

Please:
1. List the main directories and their purposes
2. Identify existing CRUD patterns I should follow
3. Find the test structure
4. Locate configuration files
```

### 3. Ask for Code Review and Testing

**After Implementation:**
```
I've implemented the payment feature in @studyflow/backend/

Please:
1. Review the code for potential issues
2. Check if it follows our existing patterns
3. Verify imports from @shared/ are correct
4. Create comprehensive unit tests
5. Test CRUD operations with real database
```

### 4. Request Documentation Updates

**Complete Implementation:**
```
Please update:
1. README.md with new feature documentation
2. API documentation in @docs/ (if public API)
3. TASK.md to mark the task as completed
4. Add inline comments for complex logic
```

### 5. Always Create Git Commits

**After Completion:**
```
Create a git commit with:
- Clear commit message describing what was added
- Reference to any related issues or tasks
- Include co-authorship: "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Pro Tips for Working with Claude

### 1. Breaking Down Large Tasks

**❌ Don't:**
```
Build a complete payment system with Stripe integration, invoicing,
refunds, subscriptions, and email notifications
```

**✅ Do:**
```
Phase 1: Basic Stripe integration
Phase 2: Invoice generation
Phase 3: Refund handling
Phase 4: Subscription management
Phase 5: Email notifications

Let's start with Phase 1: Basic Stripe integration in @studyflow/backend/
```

### 2. Providing File Paths Explicitly

**❌ Vague:**
```
Update the user model
```

**✅ Specific:**
```
Update the user model in @studyflow/backend/app/models/user.py
Also check if we need to update the shared model in @shared/models/user.py
```

### 3. Handling Errors Effectively

**When You Get an Error:**
```
I got this error when running the studyflow backend:

[paste full error traceback]

Context:
- This happened after adding the payment feature
- I'm running on port 30031
- MongoDB connection works fine
- Other routes are working

Please help diagnose and fix this issue.
```

### 4. Requesting Explanations

**Understanding Complex Code:**
```
Can you explain how the organization scoping works in @studyflow/?

I see it in:
- @studyflow/backend/app/services/organization_service.py
- @studyflow/backend/app/api/routes/materials.py

How should I apply this pattern to my new payment routes?
```

### 5. Iterative Refinement

**After Initial Implementation:**
```
The payment feature works, but I need improvements:

1. Add error handling for failed transactions
2. Implement retry logic for network issues
3. Add logging for audit trail
4. Optimize database queries

Let's tackle these one by one, starting with error handling.
```

---

## Multi-Project Development Guidelines

### 1. Shared Library Changes

**When Modifying @shared/:**

```markdown
⚠️ CRITICAL CHECKLIST:

Before modifying any file in @shared/:

1. [ ] Identify all projects importing this file:
   ```bash
   grep -r "from shared.auth" apps/*/backend/
   ```

2. [ ] Check if change is backward compatible
3. [ ] Update imports in ALL affected projects
4. [ ] Test ALL affected projects, not just one
5. [ ] Update shared library documentation
6. [ ] Create git commit mentioning all affected projects
```

**Example Prompt:**
```
I need to add a new function to @shared/auth/supabase_client.py

This is used by all 7 projects. Please:
1. Add the new function with backward compatibility
2. Update all imports across all projects
3. Add tests in @shared/tests/
4. Document the new function
```

### 2. Port Management

**Available Ports:**
```
30027 - Core Backend (api.ailabsafrica.com)
30028 - Developer Platform Backend
30030 - ChurchFlow Backend
30031 - StudyFlow Backend
30032 - EventFlow Backend
30033 - InkWave Backend
30034 - ERP Backend
30035 - Documentation Backend
```

**When Adding New Service:**
```
I'm adding a new microservice for analytics.

Please:
1. Assign the next available port (30036)
2. Create systemd service file
3. Create nginx configuration
4. Add to infrastructure documentation
5. Update CLAUDE.md with new service info
```

### 3. Database Naming Conventions

**MongoDB Databases:**
```
kasaai_core       - Core backend data
studyflow         - StudyFlow data
churchflow        - ChurchFlow data
eventflow         - EventFlow data
inkwave           - InkWave data
erp               - ERP data
kasaai_docs       - Documentation users/metadata
```

**Creating Collections:**
```
When creating a new collection in @studyflow/:

1. Use lowercase with underscores: study_materials (not StudyMaterials)
2. Add indexes for frequently queried fields
3. Include organization_id for multi-tenancy
4. Document schema in PLANNING.md
5. Create migration script if needed
```

### 4. Frontend-Backend Integration

**API Configuration:**
```typescript
// ❌ Don't hardcode URLs
const response = await fetch('https://api.ailabsafrica.com/users');

// ✅ Use API config
import { API_ENDPOINTS } from '@/config/api-config';
const response = await fetch(API_ENDPOINTS.users.list);
```

**In Your Prompts:**
```
When adding new API endpoints to @studyflow/backend/, please also:

1. Update @studyflow/frontend/src/config/api-config.ts
2. Create TypeScript types for request/response
3. Add API call functions in @studyflow/frontend/src/services/
4. Update frontend components to use the new endpoint
```

### 5. Environment Variables

**Shared vs. Project-Specific:**

```bash
# Shared (.env at root) - Used by ALL projects
MONGO_USER=admin
MONGO_PASSWORD=***
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=***

# Project-Specific (studyflow/backend/.env) - Only for StudyFlow
STRIPE_SECRET_KEY=***
SENDGRID_API_KEY=***
```

**Prompt Template:**
```
I need to add Stripe integration to @studyflow/backend/

Please:
1. Add STRIPE_SECRET_KEY to @studyflow/backend/.env.example
2. Document in @studyflow/README.md
3. Use environment variable, never hardcode
4. Add validation that key exists on startup
```

---

## Common Pitfalls and Solutions

### 1. Import Path Issues

**Problem:**
```python
# This breaks when shared library moves
from shared.auth import get_current_user
```

**Solution:**
```python
# Use relative imports within project
from app.dependencies import get_current_user

# Or absolute from shared
from shared.auth.supabase_client import get_current_user
```

**In Prompts:**
```
When adding imports, please:
1. Check existing import patterns in the same project
2. Use consistent import style throughout
3. Avoid circular dependencies
4. Import from @shared/ only when necessary
```

### 2. Database Connection Sharing

**Problem:**
```python
# Creating new connection per request - WRONG
def get_users():
    client = MongoClient(os.getenv("MONGO_URL"))
    # ...
```

**Solution:**
```python
# Use shared singleton connection
from shared.database import get_database

def get_users():
    db = get_database()
    # ...
```

**Prompt Reminder:**
```
When working with MongoDB, always use the shared database connection from
@shared/database/ - never create new MongoClient instances.
```

### 3. Authentication Inconsistencies

**Problem:**
```python
# Different auth patterns across projects
def get_current_user_custom():
    # Custom auth logic
```

**Solution:**
```python
# Use shared authentication
from shared.auth import get_current_user, verify_token
```

**Prompt Template:**
```
For authentication in [project]:
1. Use @shared/auth/supabase_client.py
2. Follow the pattern in @core_backend/app/dependencies.py
3. Support universal admin accounts from DEFAULT_USERS.md
4. Return consistent user object structure
```

### 4. Testing with Mocks vs. Real Database

**Problem:**
```python
# Test with mocks - doesn't catch real issues
@pytest.fixture
def mock_db():
    return MagicMock()
```

**Solution:**
```python
# Test with real database
@pytest.fixture
def test_db():
    db = get_database()
    yield db
    # Cleanup after test
    db[test_collection].delete_many({})
```

**Testing Requirements in Prompts:**
```
Create tests following @apps/core_backend/TEST_SUITE_ANALYSIS.md:

1. Use real database integration (not mocks)
2. Test actual CRUD operations
3. Verify data persists in MongoDB
4. Clean up test data after each test
5. Test edge cases and error conditions
```

### 5. Forgetting Organization Scoping

**Problem:**
```python
# Returns ALL materials (security issue!)
def get_materials():
    return db.materials.find()
```

**Solution:**
```python
# Filter by organization
def get_materials(organization_id: str):
    return db.materials.find({"organization_id": organization_id})
```

**Multi-Tenancy Reminder:**
```
⚠️ SECURITY: Always include organization scoping in queries!

For multi-tenant apps (@studyflow/, @churchflow/, @eventflow/):
1. Add organization_id to all documents
2. Filter queries by organization_id
3. Verify user belongs to organization
4. Test cross-organization data isolation
```

---

## Deployment and Service Management

### 1. Service Restart After Changes

**After Code Changes:**
```bash
# Restart specific service
sudo systemctl restart kasaai-studyflow-backend

# Check status
sudo systemctl status kasaai-studyflow-backend

# View logs
sudo journalctl -u kasaai-studyflow-backend -f
```

**In Prompts:**
```
After implementing the payment feature:

1. Rebuild the frontend: npm run build
2. Restart the backend: sudo systemctl restart kasaai-studyflow-backend
3. Check service status
4. Verify logs for any errors
5. Test the new endpoints
```

### 2. Nginx Configuration Updates

**When Adding New Endpoints:**
```
If you added new API routes that need CORS or special headers:

Please update:
1. /etc/nginx/sites-available/studyflow-api.ailabsafrica.com.conf
2. Add necessary CORS headers
3. Test nginx config: sudo nginx -t
4. Reload nginx: sudo systemctl reload nginx
```

### 3. Frontend Build and Deploy

**Production Deployment:**
```bash
cd /opt/kasaai/apps/studyflow/frontend
npm run build
# Built files go to dist/
# Nginx serves from this directory
```

**Prompt Template:**
```
After frontend changes:

1. Build for production: npm run build
2. Verify dist/ directory created
3. Check nginx is serving from correct path
4. Clear browser cache for testing
5. Verify on production URL
```

---

## TTS and Voice Services

### Overview

AI Labs Africa maintains a comprehensive suite of TTS (Text-to-Speech) and voice processing services deployed across multiple platforms. All services are production-ready with SSL certificates, health monitoring, and API documentation.

### 1. Available TTS Services

#### Production TTS Services

**1. TTS-WebUI (Comprehensive Platform)**
- **URL:** https://tts-webui.ailabsafrica.com
- **Type:** Multi-model TTS platform
- **Features:** AllTalk, Coqui, Piper, Sherpa-ONNX, XTTS, StyleTTS2
- **Best For:** Unified TTS API with model selection
- **Documentation:** https://tts-webui.ailabsafrica.com/docs

**2. Coqui XTTS v2**
- **API URL:** https://coqui.ailabsafrica.com
- **UI URL:** https://coqui-ui.ailabsafrica.com (Gradio Interface)
- **Type:** Neural TTS with voice cloning
- **Languages:** 17 languages (English, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Hungarian, Korean, Hindi)
- **Best For:** Multilingual TTS, voice cloning from 6+ seconds of audio
- **GPU:** NVIDIA L4 (24GB VRAM) on RunPod
- **Deployment:** API on localhost:8015, UI on localhost:8015
- **Documentation:** https://coqui.ailabsafrica.com/docs

**3. MeloTTS**
- **API URL:** https://melotts.ailabsafrica.com
- **UI URL:** https://melotts-ui.ailabsafrica.com (Gradio Interface)
- **Type:** High-quality multilingual TTS
- **Languages:** English (US, UK, India, Australia), Spanish, French, Chinese, Japanese, Korean
- **Best For:** Fast, natural-sounding speech with accent control
- **Speed:** ~2-3 seconds for short text
- **Deployment:** API on localhost:8010, UI on localhost:8011
- **Documentation:** https://melotts.ailabsafrica.com/docs

**4. StyleTTS2**
- **API URL:** https://styletts.ailabsafrica.com
- **UI URL:** https://styletts-ui.ailabsafrica.com (TTS-WebUI Gradio Interface)
- **Type:** Style-based TTS with prosody control
- **Languages:** English (primary)
- **Best For:** Expressive speech, emotion control, audiobooks
- **GPU:** NVIDIA L4 on RunPod
- **Deployment:** API on RunPod port 8006, UI on RunPod port 8013
- **Documentation:** https://styletts.ailabsafrica.com/docs

**5. F5-TTS**
- **API URL:** https://f5tts.ailabsafrica.com
- **UI URL:** https://f5tts-ui.ailabsafrica.com (Gradio Interface)
- **Type:** Fast, high-fidelity TTS
- **Languages:** English, Chinese
- **Best For:** Low-latency, high-quality synthesis
- **Speed:** ~1-2 seconds for medium text
- **GPU:** NVIDIA A40 on RunPod
- **Deployment:** API on localhost, UI on RunPod port 8011
- **Documentation:** https://f5tts.ailabsafrica.com/docs

**6. OpenVoice**
- **API URL:** https://openvoice.ailabsafrica.com
- **UI URL:** https://openvoice-ui.ailabsafrica.com (Gradio Interface)
- **Type:** Voice cloning and tone control
- **Languages:** English, Spanish, French, Chinese, Japanese, Korean
- **Best For:** Instant voice cloning, granular voice control
- **GPU:** NVIDIA L4 on RunPod
- **Deployment:** API on localhost, UI on localhost:8013
- **Documentation:** https://openvoice.ailabsafrica.com/docs

**7. Kokoro TTS**
- **API URL:** https://kokoro.ailabsafrica.com
- **UI URL:** https://kokoro-ui.ailabsafrica.com (Gradio Interface)
- **Type:** Lightweight, fast TTS
- **Languages:** English (US, UK accents)
- **Best For:** Resource-efficient TTS, real-time applications
- **Speed:** Less than 1 second for short text
- **Deployment:** API on localhost, UI on localhost:8021
- **Documentation:** https://kokoro.ailabsafrica.com/docs

#### Specialty Voice Services

**8. RVC (Voice Conversion)**
- **URL:** https://rvc.ailabsafrica.com
- **Type:** Retrieval-based Voice Conversion
- **Best For:** Voice transformation, character voices, anonymization, voice restoration
- **GPU:** NVIDIA A40 (44GB VRAM) on RunPod
- **Features:** Pitch control, index-based retrieval, 5 F0 extraction methods
- **Documentation:** https://rvc.ailabsafrica.com/docs

**9. Fish Speech**
- **URL:** https://fishspeech.ailabsafrica.com (Gradio UI)
- **Type:** Zero-shot voice cloning
- **Languages:** Multilingual
- **Best For:** Natural speech from minimal reference audio
- **GPU:** NVIDIA L4 on RunPod
- **Status:** Gradio interface available

**10. Zonos TTS**
- **URL:** https://zonos.ailabsafrica.com (Gradio UI)
- **Type:** Experimental TTS
- **Languages:** English
- **Best For:** Research and testing
- **GPU:** NVIDIA L4 on RunPod
- **Status:** Gradio interface available

### 2. Service Selection Guide

#### When to Use Which Service

**For Multilingual Content:**
- Primary: **Coqui XTTS** (17 languages, voice cloning)
- Alternative: **MeloTTS** (9 languages, faster)
- Voice Matching: **OpenVoice** (6 languages, tone control)

**For English-Only Content:**
- Expressive/Audiobooks: **StyleTTS2** (emotion control)
- Fast/Real-time: **Kokoro TTS** (sub-second latency)
- High Fidelity: **F5-TTS** (superior quality)

**For Voice Transformation:**
- Character Voices: **RVC** (voice conversion)
- Voice Cloning: **Coqui XTTS** or **Fish Speech**
- Tone Adjustment: **OpenVoice**

**For Platform Integration:**
- Unified API: **TTS-WebUI** (access all models)
- Direct Integration: Individual service APIs

### 3. Integration Examples

#### Basic TTS Request (Coqui XTTS)

```python
import requests

response = requests.post(
    "https://coqui.ailabsafrica.com/api/v1/audio/speech",
    json={
        "input": "Hello, this is a test of the Coqui XTTS system.",
        "language": "en",
        "speaker_wav": "https://example.com/reference_voice.wav",
        "temperature": 0.75
    }
)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
```

#### Voice Conversion Pipeline (TTS + RVC)

```python
import requests

# Step 1: Generate speech with MeloTTS
tts_response = requests.post(
    "https://melotts.ailabsafrica.com/api/v1/audio/speech",
    json={
        "input": "The quick brown fox jumps over the lazy dog.",
        "language": "EN",
        "accent": "EN-US",
        "speed": 1.0
    }
)

# Step 2: Convert voice with RVC
files = {"audio": ("input.wav", tts_response.content, "audio/wav")}
data = {
    "model_path": "logs/character_voice/model.pth",
    "pitch_shift": 0,
    "index_rate": 0.75,
    "f0_method": "rmvpe"
}

rvc_response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files=files,
    data=data
)

if rvc_response.status_code == 200:
    with open("character_voice.wav", "wb") as f:
        f.write(rvc_response.content)
```

#### Multi-Service Comparison

```python
import requests
import concurrent.futures

def generate_tts(service_name, url, payload):
    """Generate TTS from a specific service."""
    response = requests.post(url, json=payload)
    return service_name, response.content if response.status_code == 200 else None

# Test same text across multiple services
text = "Welcome to AI Labs Africa's TTS platform."

services = [
    ("Coqui", "https://coqui.ailabsafrica.com/api/v1/audio/speech",
     {"input": text, "language": "en"}),
    ("MeloTTS", "https://melotts.ailabsafrica.com/api/v1/audio/speech",
     {"input": text, "language": "EN", "accent": "EN-US"}),
    ("StyleTTS2", "https://styletts.ailabsafrica.com/api/v1/audio/speech",
     {"input": text, "alpha": 0.3, "beta": 0.7}),
]

# Generate in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(generate_tts, name, url, payload)
               for name, url, payload in services]

    for future in concurrent.futures.as_completed(futures):
        service_name, audio_data = future.result()
        if audio_data:
            with open(f"{service_name.lower()}_output.wav", "wb") as f:
                f.write(audio_data)
            print(f"{service_name}: Generated successfully")
```

### 4. Service Health Monitoring

#### Check All Service Health

```bash
# Check all TTS API services
curl https://coqui.ailabsafrica.com/health
curl https://melotts.ailabsafrica.com/health
curl https://styletts.ailabsafrica.com/health
curl https://f5tts.ailabsafrica.com/health
curl https://openvoice.ailabsafrica.com/health
curl https://kokoro.ailabsafrica.com/health
curl https://rvc.ailabsafrica.com/health
curl https://tts-webui.ailabsafrica.com/health

# Check all TTS UI services (Gradio interfaces)
curl -I https://coqui-ui.ailabsafrica.com
curl -I https://melotts-ui.ailabsafrica.com
curl -I https://styletts-ui.ailabsafrica.com
curl -I https://f5tts-ui.ailabsafrica.com
curl -I https://openvoice-ui.ailabsafrica.com
curl -I https://kokoro-ui.ailabsafrica.com
```

#### Python Health Check Script

```python
import requests

TTS_SERVICES = {
    # API Services
    "Coqui XTTS": "https://coqui.ailabsafrica.com/health",
    "MeloTTS": "https://melotts.ailabsafrica.com/health",
    "StyleTTS2": "https://styletts.ailabsafrica.com/health",
    "F5-TTS": "https://f5tts.ailabsafrica.com/health",
    "OpenVoice": "https://openvoice.ailabsafrica.com/health",
    "Kokoro TTS": "https://kokoro.ailabsafrica.com/health",
    "RVC": "https://rvc.ailabsafrica.com/health",
    "TTS-WebUI": "https://tts-webui.ailabsafrica.com/health",
}

UI_SERVICES = {
    # Gradio UI Services
    "Coqui UI": "https://coqui-ui.ailabsafrica.com",
    "MeloTTS UI": "https://melotts-ui.ailabsafrica.com",
    "StyleTTS UI": "https://styletts-ui.ailabsafrica.com",
    "F5-TTS UI": "https://f5tts-ui.ailabsafrica.com",
    "OpenVoice UI": "https://openvoice-ui.ailabsafrica.com",
    "Kokoro UI": "https://kokoro-ui.ailabsafrica.com",
}

print("=== TTS API Services ===")
for service_name, health_url in TTS_SERVICES.items():
    try:
        response = requests.get(health_url, timeout=5)
        status = "✅ ONLINE" if response.status_code == 200 else "⚠️ DEGRADED"
        print(f"{service_name:15} {status}")
    except Exception as e:
        print(f"{service_name:15} ❌ OFFLINE - {str(e)}")

print("\n=== TTS UI Services (Gradio) ===")
for service_name, url in UI_SERVICES.items():
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        status = "✅ ONLINE" if response.status_code in [200, 405] else "⚠️ DEGRADED"
        print(f"{service_name:15} {status}")
    except Exception as e:
        print(f"{service_name:15} ❌ OFFLINE - {str(e)}")
```

### 5. Platform URLs Reference

#### Primary Platforms
- **Main Website:** https://ailabsafrica.com
- **Main Platform:** https://kasaai.ailabsafrica.com
- **Core API:** https://api.ailabsafrica.com
- **Developer Portal:** https://developer.ailabsafrica.com
- **Developer API:** https://developer-portal-api.ailabsafrica.com
- **Documentation:** https://docs.ailabsafrica.com

#### Vertical Solutions
- **ChurchFlow:** https://churchflow.ailabsafrica.com
- **ChurchFlow API:** https://churchflow-api.ailabsafrica.com
- **StudyFlow:** https://studyflow.ailabsafrica.com
- **StudyFlow API:** https://studyflow-api.ailabsafrica.com
- **EventFlow:** https://eventflow.ailabsafrica.com
- **EventFlow API:** https://eventflow-api.ailabsafrica.com
- **InkWave:** https://inkwave.ailabsafrica.com
- **InkWave API:** https://inkwave-api.ailabsafrica.com

#### Development Environments
All production services have dev equivalents:
- **Dev Core API:** https://dev-api.ailabsafrica.com
- **Dev StudyFlow:** https://dev-studyflow.ailabsafrica.com
- **Dev ChurchFlow:** https://dev-churchflow.ailabsafrica.com
- **Dev EventFlow:** https://dev-eventflow.ailabsafrica.com
- **Dev InkWave:** https://dev-inkwave.ailabsafrica.com

### 6. Best Practices for TTS Integration

#### Rate Limiting and Caching
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def generate_tts_cached(text: str, service: str = "coqui"):
    """Cache TTS results to avoid regenerating identical requests."""
    text_hash = hashlib.md5(text.encode()).hexdigest()

    # Check cache first (implement your cache storage)
    cached_audio = get_from_cache(text_hash, service)
    if cached_audio:
        return cached_audio

    # Generate new TTS
    if service == "coqui":
        url = "https://coqui.ailabsafrica.com/api/v1/audio/speech"
        payload = {"input": text, "language": "en"}
    elif service == "melotts":
        url = "https://melotts.ailabsafrica.com/api/v1/audio/speech"
        payload = {"input": text, "language": "EN", "accent": "EN-US"}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        save_to_cache(text_hash, service, response.content)
        return response.content

    return None
```

#### Error Handling with Fallbacks
```python
def generate_tts_with_fallback(text: str, language: str = "en"):
    """Try multiple TTS services with automatic fallback."""
    services = [
        ("Coqui", "https://coqui.ailabsafrica.com/api/v1/audio/speech",
         {"input": text, "language": language}),
        ("MeloTTS", "https://melotts.ailabsafrica.com/api/v1/audio/speech",
         {"input": text, "language": language.upper(), "accent": f"{language.upper()}-US"}),
        ("Kokoro", "https://kokoro.ailabsafrica.com/api/v1/audio/speech",
         {"input": text}),
    ]

    for service_name, url, payload in services:
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"✅ Generated with {service_name}")
                return response.content
        except Exception as e:
            print(f"⚠️ {service_name} failed: {str(e)}")
            continue

    raise Exception("All TTS services failed")
```

#### Prompt Guidelines for TTS Tasks

When asking Claude to integrate TTS services:

```
Please integrate Coqui XTTS for multilingual narration:

1. Use https://coqui.ailabsafrica.com/api/v1/audio/speech
2. Support languages: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko, hi
3. Include voice cloning with speaker_wav parameter
4. Add error handling with fallback to MeloTTS
5. Cache results to avoid regenerating identical text
6. Return WAV format audio data
7. Log inference time from X-Inference-Time header
```

### 7. Deployment Information

**RunPod GPU Cloud:**
- **SSH Access:** `ssh -i ~/.ssh/id_ed25519 root@194.68.245.121 -p 22153`
- **TTS Services:** /workspace/tts-deployment/
- **RVC Service:** /workspace/rvc-webui/
- **Fish Speech:** /workspace/fish-speech/
- **Zonos:** /workspace/Zonos/
- **Shared Venv:** /workspace/tts-venv/

**Production Server (148.251.0.46):**
- All Nginx configurations in `/etc/nginx/sites-available/`
- SSL certificates managed by certbot
- All expire: January 24, 2026

**Dev Server (85.214.12.174):**
- Dev environment mirrors production
- Separate SSL certificates for dev-*.ailabsafrica.com

### 8. Quick Reference

#### Language Support Matrix

| Service | English | Spanish | French | German | Chinese | Japanese | Korean | Arabic |
|---------|---------|---------|--------|--------|---------|----------|--------|--------|
| Coqui XTTS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| MeloTTS | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ | - |
| OpenVoice | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ | - |
| StyleTTS2 | ✅ | - | - | - | - | - | - | - |
| F5-TTS | ✅ | - | - | - | ✅ | - | - | - |
| Kokoro | ✅ | - | - | - | - | - | - | - |
| RVC | Language-agnostic (voice conversion) |

#### Performance Comparison

| Service | Speed (5s text) | Quality | GPU | Best Use Case |
|---------|-----------------|---------|-----|---------------|
| Kokoro | Sub-1s | Good | CPU-capable | Real-time apps |
| F5-TTS | 1-2s | Excellent | L4 (24GB) | High fidelity |
| MeloTTS | 2-3s | Very Good | L4 (24GB) | Multilingual |
| Coqui XTTS | 3-5s | Excellent | L4 (24GB) | Voice cloning |
| StyleTTS2 | 4-6s | Excellent | L4 (24GB) | Expressive speech |
| OpenVoice | 2-4s | Very Good | L4 (24GB) | Tone control |
| RVC | 1-2s | N/A | A40 (44GB) | Voice transformation |

---

## Code Quality Standards

### 1. File Size Limits

**Rule: No file over 500 lines**

```
If a file approaches 500 lines:
1. Refactor into multiple modules
2. Extract helper functions
3. Split by feature/responsibility
4. Create subdirectories for organization
```

**In Prompts:**
```
The user_service.py file is getting large (450 lines).

Please refactor into:
- user_service.py (core CRUD operations)
- user_validators.py (validation logic)
- user_utils.py (helper functions)
```

### 2. Documentation Requirements

**Every Function Must Have Docstring:**

```python
def create_payment(
    user_id: str,
    amount: float,
    organization_id: str
) -> Payment:
    """
    Create a new payment record.

    Args:
        user_id: The ID of the user making payment
        amount: Payment amount in USD
        organization_id: Organization ID for multi-tenancy

    Returns:
        Payment: Created payment object

    Raises:
        ValueError: If amount is negative
        DatabaseError: If database operation fails
    """
    # Implementation
```

**Prompt Requirement:**
```
When writing new functions, always include:
1. Google-style docstrings
2. Type hints for all parameters
3. Return type annotations
4. Explanation of raised exceptions
```

### 3. Error Handling Patterns

**Standard Error Response:**

```python
from fastapi import HTTPException, status

# ❌ Generic errors
raise Exception("Something went wrong")

# ✅ Specific HTTP exceptions
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Payment not found"
)

# ✅ With context
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={
        "message": "Invalid payment amount",
        "field": "amount",
        "provided": amount
    }
)
```

### 4. Logging Best Practices

**Use Structured Logging:**

```python
import logging

logger = logging.getLogger(__name__)

# ❌ Poor logging
print("Payment created")

# ✅ Structured logging
logger.info(
    "Payment created",
    extra={
        "payment_id": payment.id,
        "user_id": user_id,
        "amount": amount,
        "organization_id": organization_id
    }
)

# ✅ Error logging
logger.error(
    "Payment processing failed",
    extra={"error": str(e), "payment_id": payment_id},
    exc_info=True
)
```

---

## Security Guidelines

### 1. Never Commit Secrets

**Before Committing:**
```bash
# Check for potential secrets
git diff | grep -i "password\|secret\|key\|token"

# Use .env files
echo "STRIPE_SECRET_KEY=sk_test_xxx" >> .env

# Add to .gitignore
echo ".env" >> .gitignore
```

**Prompt Reminder:**
```
When implementing API integrations:

1. Use environment variables for all secrets
2. Add to .env.example with placeholder values
3. Document in README.md
4. Never log secret values
5. Use secret scanning tools
```

### 2. Input Validation

**Always Validate User Input:**

```python
from pydantic import BaseModel, validator, Field

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Must be positive")
    currency: str = Field(..., regex="^(USD|EUR|GHS)$")

    @validator('amount')
    def validate_amount(cls, v):
        if v > 1000000:
            raise ValueError('Amount exceeds maximum')
        return round(v, 2)
```

### 3. SQL Injection Prevention

**Use Parameterized Queries:**

```python
# ❌ SQL injection vulnerable
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ Safe with MongoDB
db.users.find_one({"email": email})

# ✅ Safe with parameters
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

### 4. Authentication on All Protected Routes

**FastAPI Dependencies:**

```python
from fastapi import Depends
from shared.auth import get_current_user

@router.get("/payments")
async def get_payments(
    current_user: User = Depends(get_current_user)  # Always add this!
):
    # Only authenticated users can access
    pass
```

---

## Performance Optimization

### 1. Database Indexing

**Create Indexes for Common Queries:**

```python
# In migration script or startup
db.payments.create_index([("user_id", 1)])
db.payments.create_index([("organization_id", 1)])
db.payments.create_index([("created_at", -1)])
db.payments.create_index([
    ("organization_id", 1),
    ("user_id", 1),
    ("created_at", -1)
])
```

**Prompt Template:**
```
When creating new collections, please:
1. Identify frequently queried fields
2. Create appropriate indexes
3. Add compound indexes for common filter combinations
4. Document indexes in PLANNING.md
```

### 2. Pagination for Large Datasets

**Always Paginate:**

```python
@router.get("/materials")
async def get_materials(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    organization_id: str = Depends(get_organization_id)
):
    materials = await db.materials.find(
        {"organization_id": organization_id}
    ).skip(skip).limit(limit).to_list(length=limit)

    total = await db.materials.count_documents(
        {"organization_id": organization_id}
    )

    return {
        "items": materials,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### 3. Caching Strategy

**Use Redis for Frequent Reads:**

```python
import redis
from functools import lru_cache

# Connection pool
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

@lru_cache(maxsize=100)
def get_organization_settings(org_id: str):
    # Cached in memory
    return db.organizations.find_one({"_id": org_id})
```

---

## Collaboration Best Practices

### 1. Communication in Prompts

**When Working on Shared Features:**
```
I'm working on the payment integration for @studyflow/

This might impact:
- @core_backend/ (if we add shared payment utilities)
- @eventflow/ (might need similar payment features later)
- @shared/services/ (could create base payment service)

Should we:
1. Implement StudyFlow-specific solution now
2. Create shared payment service for future use
3. Both - implement specific now, refactor to shared later

What do you recommend?
```

### 2. Code Review Checklist

**Before Finalizing:**
```
Please review my implementation against this checklist:

- [ ] Follows existing code patterns in the project
- [ ] Uses @shared/ libraries where appropriate
- [ ] Has comprehensive unit tests
- [ ] Includes docstrings and type hints
- [ ] No hardcoded secrets or URLs
- [ ] Proper error handling
- [ ] Logging for debugging
- [ ] Performance considerations (indexes, pagination)
- [ ] Security best practices
- [ ] Documentation updated
- [ ] Git commit created
```

### 3. Backward Compatibility

**When Updating Shared Code:**
```
I need to update @shared/auth/supabase_client.py to add new functionality.

Please:
1. Add new features without breaking existing code
2. Maintain existing function signatures
3. Add new optional parameters with defaults
4. Deprecate old functions gradually (don't remove immediately)
5. Update all projects to use new features
6. Document migration path
```

---

## Quick Reference Commands

### Common Development Tasks

```bash
# Check which projects are running
sudo systemctl list-units "kasaai-*.service" --all

# Restart a specific service
sudo systemctl restart kasaai-studyflow-backend

# View live logs
sudo journalctl -u kasaai-studyflow-backend -f

# Find which projects use a shared function
grep -r "get_current_user" /opt/kasaai/apps/*/backend/

# Check MongoDB collections
mongosh "mongodb://admin:PASSWORD@127.0.0.1:27017/"
use studyflow
show collections

# Test API endpoint
curl -X GET "https://studyflow-api.ailabsafrica.com/api/health"

# Build frontend
cd /opt/kasaai/apps/studyflow/frontend
npm run build

# Run tests
cd /opt/kasaai/apps/studyflow/backend
pytest tests/ -v

# Check nginx config
sudo nginx -t
sudo systemctl reload nginx

# Git operations
git status
git add -A
git commit -m "feat: Add payment integration"
git log --oneline -10
```

---

## Summary Checklist

**Before Starting Development:**
- [ ] Read project PLANNING.md
- [ ] Check TASK.md for similar tasks
- [ ] Understand which project(s) will be affected
- [ ] Review existing patterns to follow
- [ ] Check if @shared/ libraries should be used

**During Development:**
- [ ] Follow existing code patterns
- [ ] Add comprehensive tests
- [ ] Include docstrings and type hints
- [ ] Use environment variables for config
- [ ] Add proper error handling
- [ ] Implement logging
- [ ] Consider performance implications
- [ ] Maintain organization scoping

**After Development:**
- [ ] Run tests (pytest)
- [ ] Update documentation
- [ ] Mark TASK.md as complete
- [ ] Create git commit
- [ ] Restart services
- [ ] Test in production
- [ ] Monitor logs for errors

**For Shared Library Changes:**
- [ ] Identify all affected projects
- [ ] Ensure backward compatibility
- [ ] Update all imports
- [ ] Test ALL projects
- [ ] Update shared documentation
- [ ] Create comprehensive commit message

---

## Additional Resources

- **Architecture Documentation**: `/opt/kasaai/CLAUDE.md`
- **Shared Auth Docs**: `/opt/kasaai/apps/shared/auth/DEFAULT_USERS.md`
- **Test Guidelines**: `/opt/kasaai/apps/core_backend/TEST_SUITE_ANALYSIS.md`
- **Onboarding Guide**: `/internal/onboarding`
- **Deployment Guide**: `/internal/deployment`

---

**Last Updated**: November 7, 2025
**Maintained By**: KasaAI Engineering Team

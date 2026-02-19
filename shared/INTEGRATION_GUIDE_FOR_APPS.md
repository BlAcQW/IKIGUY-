# Shared Services Integration Guide for Apps

**Version:** 1.0.0
**Last Updated:** November 8, 2025
**Audience:** App Developers (ChurchFlow, InkWave, StudyFlow, EventFlow, Core Backend, etc.)

---

## Table of Contents

1. [Overview](#overview)
2. [Setup & Configuration](#setup--configuration)
3. [Available Services](#available-services)
4. [Integration Patterns](#integration-patterns)
5. [Step-by-Step Examples](#step-by-step-examples)
6. [Rate Limiting & Authentication](#rate-limiting--authentication)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The `@shared/` directory contains centralized services that can be used by **all KasaAI applications**. This guide shows you how to integrate these services into your app.

### Why Use Shared Services?

✅ **No code duplication** - Write once, use everywhere
✅ **Consistent behavior** - Same logic across all apps
✅ **Centralized billing** - Automatic usage tracking and wallet deductions
✅ **Rate limiting** - Built-in protection against abuse
✅ **Health monitoring** - Automatic provider failover
✅ **Easy upgrades** - Update once, all apps benefit

### Directory Structure

```
/opt/kasaai/apps/shared/
├── services/              # High-level business logic services
│   ├── tts_provider_service.py       # TTS with billing
│   ├── tts_webui_service.py          # TTS-WebUI access
│   ├── tts_health_notifier.py        # TTS health monitoring
│   ├── llm_provider_service.py       # LLM with billing
│   ├── asr_provider_service.py       # ASR with billing
│   ├── pdf_extraction_service.py     # PDF data extraction
│   ├── file_upload_service.py        # Cloud file storage
│   ├── email_account_service.py      # Email account management
│   └── README.md
├── integration/           # External service wrappers
│   ├── ai_services/      # AI provider management
│   ├── wallet/           # Wallet & billing
│   ├── rag_service/      # RAG for Q&A
│   └── document_processor/
├── middleware/            # FastAPI middleware
│   ├── rate_limiter.py   # Rate limiting
│   └── organization_context.py
├── models/                # Pydantic models
├── auth/                  # Authentication utilities
└── utils/                 # Helper functions
```

---

## Setup & Configuration

### 1. Python Path Configuration

All apps already have `@shared/` in their Python path. You can import directly:

```python
from apps.shared.services.tts_webui_service import TTSWebUIService
```

### 2. Environment Variables

Add these to your app's `.env` file (or use the global `/opt/kasaai/.env`):

```bash
# TTS-WebUI Configuration
TTSWEBUI_WEBUI_ENDPOINT=https://tts-webui.ailabsafrica.com
TTSWEBUI_API_ENDPOINT=https://tts-webui.ailabsafrica.com/api
TTSWEBUI_API_KEY=optional-api-key-if-needed

# Rate Limiting (optional - defaults provided)
TTSWEBUI_USER_RPM=60          # Requests per minute per user
TTSWEBUI_USER_RPH=1000        # Requests per hour per user
TTSWEBUI_ORG_RPM=600          # Requests per minute per org
TTSWEBUI_ORG_RPH=10000        # Requests per hour per org

# TTS Providers (existing)
COQUI_ENDPOINT=https://coqui.ailabsafrica.com
MELOTTS_ENDPOINT=https://melotts.ailabsafrica.com
# ... etc
```

### 3. Dependencies

Most dependencies are already installed in `/opt/kasaai/apps/venv`. If you need additional packages:

```bash
source /opt/kasaai/apps/venv/bin/activate
pip install httpx pydantic
```

---

## Available Services

### 1. TTS-WebUI Service (NEW)

**Purpose:** Access 20+ TTS models through a unified API

**File:** `apps/shared/services/tts_webui_service.py`

**Features:**
- 20+ TTS models (StyleTTS2, RVC, Bark, Tortoise, etc.)
- Voice cloning support
- OpenAI-compatible API
- Built-in rate limiting
- Provider discovery

**Quick Example:**
```python
from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)

# Initialize service
service = TTSWebUIService()

# Synthesize
request = TTSWebUISynthesisRequest(
    text="Hello world",
    provider_id=TTSWebUIProvider.STYLETTS2,
    language="en"
)

response = await service.synthesize(
    request,
    user_id="user_123",      # For rate limiting
    org_id="org_abc"         # For rate limiting
)

# Get audio
audio_bytes = base64.b64decode(response.audio_base64)
```

---

### 2. TTS Provider Service

**Purpose:** Access individual TTS providers with billing

**File:** `apps/shared/services/tts_provider_service.py`

**Features:**
- 6 production TTS providers (Coqui, MeloTTS, F5-TTS, etc.)
- Automatic wallet deductions
- Cost estimation
- Health monitoring
- Voice cloning

**Quick Example:**
```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)

# Initialize
tts_service = TTSProviderService()
await tts_service.initialize()

# Estimate cost first
cost = await tts_service.estimate_cost(
    text="Hello world",
    provider_id="coqui_xtts"
)
print(f"Cost: ${cost.total_cost:.4f}")

# Synthesize with automatic billing
result = await tts_service.synthesize(
    user_id="user_123",
    request=SynthesisRequest(
        provider_id="coqui_xtts",
        text="Hello world",
        language="en"
    )
)

# result.audio_base64, result.duration, result.cost
```

---

### 3. LLM Provider Service

**Purpose:** Chat with LLMs with automatic billing

**File:** `apps/shared/services/llm_provider_service.py`

**Quick Example:**
```python
from apps.shared.services.llm_provider_service import (
    LLMProviderService,
    ChatRequest
)

llm_service = LLMProviderService()
await llm_service.initialize()

response = await llm_service.chat(
    user_id="user_123",
    request=ChatRequest(
        provider_id="gemini_pro",
        messages=[{"role": "user", "content": "Hello!"}]
    )
)

# response.message, response.cost, response.tokens
```

---

### 4. PDF Extraction Service

**Purpose:** Extract structured data from receipts and invoices

**File:** `apps/shared/services/pdf_extraction_service.py`

**Quick Example:**
```python
from apps.shared.services.pdf_extraction_service import get_pdf_extraction_service

pdf_service = get_pdf_extraction_service(use_ocr=True)

with open("receipt.pdf", "rb") as pdf_file:
    expense_data = await pdf_service.extract_from_pdf(pdf_file)

print(f"Merchant: {expense_data.merchant}")
print(f"Amount: {expense_data.amount}")
print(f"Confidence: {expense_data.confidence}")
```

---

### 5. File Upload Service

**Purpose:** Upload files to cloud storage (Hetzner Storage Box)

**File:** `apps/shared/services/file_upload_service.py`

**Quick Example:**
```python
from apps.shared.services.file_upload_service import get_file_upload_service

upload_service = await get_file_upload_service()

with open("document.pdf", "rb") as file:
    upload_info = await upload_service.upload_file(
        file=file,
        filename="document.pdf",
        organization_id="org_abc123",
        file_category="documents"
    )

print(f"File URL: {upload_info['url']}")
```

---

### 6. Email Account Service

**Purpose:** Create email accounts on iRedMail server

**File:** `apps.shared.services.email_account_service.py`

**Quick Example:**
```python
from apps.shared.services.email_account_service import get_email_account_service

email_service = get_email_account_service()

result = await email_service.create_account(
    first_name="John",
    last_name="Doe",
    email="john.doe@ailabsafrica.com"
)

print(f"Email: {result['email']}")
print(f"Temporary Password: {result['password']}")
```

---

### 7. Vapi TTS Webhook Service (NEW)

**Purpose:** Custom TTS integration for Vapi voice AI assistants

**Files:**
- `apps/shared/services/vapi_tts_webhook.py` (Service)
- `apps/shared/routers/vapi_webhook_router.py` (FastAPI Router)

**Features:**
- Custom TTS webhook for Vapi voice agents
- Uses TTS-WebUI with 20+ models
- Real-time PCM audio conversion
- Rate limiting per user/organization
- Authentication via Vapi API key
- Fallback provider support
- Health monitoring and statistics

**Quick Example:**
```python
from apps.shared.services.vapi_tts_webhook import (
    VapiTTSWebhookService,
    VapiWebhookRequest,
    get_vapi_webhook_service
)

# Initialize service
vapi_service = VapiTTSWebhookService(
    default_provider=TTSWebUIProvider.STYLETTS2,
    fallback_provider=TTSWebUIProvider.KOKORO,
    enable_rate_limiting=True
)

# Process webhook request from Vapi
request = VapiWebhookRequest(
    message={
        "type": "voice-request",
        "text": "Hello, welcome to KasaAI!",
        "sampleRate": 24000
    },
    timestamp=1234567890,
    call={"id": "call_123"},
    assistant={"organizationId": "org_abc"}
)

# Returns raw PCM audio for Vapi
pcm_audio = await vapi_service.process_webhook_request(
    request=request,
    auth_header="Bearer your-vapi-api-key"
)

# Get statistics
stats = vapi_service.get_stats()
print(f"Success rate: {stats['success_rate']:.1%}")
```

**FastAPI Router Integration:**
```python
from fastapi import FastAPI
from apps.shared.routers import vapi_webhook_router

app = FastAPI()

# Add Vapi webhook endpoints
app.include_router(
    vapi_webhook_router,
    prefix="/api/vapi",
    tags=["vapi"]
)

# Endpoints added:
# POST /api/vapi/tts-webhook - Main webhook endpoint
# GET  /api/vapi/health - Health check
# GET  /api/vapi/config - Configuration info
# POST /api/vapi/stats/reset - Reset statistics
```

**Vapi Configuration:**

In your Vapi assistant configuration, set up the custom TTS provider:

```json
{
  "voice": {
    "provider": "custom-tts",
    "url": "https://your-app.ailabsafrica.com/api/vapi/tts-webhook",
    "secret": "your-vapi-api-key",
    "timeout": 30
  },
  "voiceSettings": {
    "sampleRate": 24000
  }
}
```

**Environment Variables:**

Add to your app's `.env`:

```bash
# Vapi Configuration
VAPI_API_KEY=your-vapi-api-key

# Rate Limits (optional - defaults shown)
VAPI_USER_RPM=30          # Requests per minute per user
VAPI_USER_RPH=500         # Requests per hour per user
VAPI_ORG_RPM=100          # Requests per minute per org
VAPI_ORG_RPH=2000         # Requests per hour per org
```

**Audio Format Requirements:**

Vapi requires audio in this exact format:
- **Format:** Raw PCM (no file headers)
- **Channels:** Mono (1 channel)
- **Bit Depth:** 16-bit signed integer
- **Byte Order:** Little-endian
- **Sample Rates:** 8000, 16000, 22050, or 24000 Hz
- **Content-Type:** `application/octet-stream`

The service handles all conversion automatically.

**Integration Example (Complete FastAPI App):**

```python
# apps/yourapp/backend/app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from apps.shared.routers import vapi_webhook_router
from apps.shared.services.vapi_tts_webhook import VapiTTSWebhookService, TTSWebUIProvider

# Global service instance
vapi_service: VapiTTSWebhookService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Vapi webhook service on startup."""
    global vapi_service

    print("Initializing Vapi TTS webhook service...")
    vapi_service = VapiTTSWebhookService(
        default_provider=TTSWebUIProvider.STYLETTS2,
        fallback_provider=TTSWebUIProvider.KOKORO,
        enable_rate_limiting=True,
        org_rpm=100,
        user_rpm=30,
        timeout=30
    )

    yield  # App runs

    print("Shutting down Vapi webhook service...")
    # Cleanup if needed

app = FastAPI(lifespan=lifespan)

# Include Vapi webhook routes
app.include_router(
    vapi_webhook_router,
    prefix="/api/vapi",
    tags=["vapi"]
)

@app.get("/")
async def root():
    return {"service": "My App with Vapi TTS"}
```

**Testing the Webhook:**

```bash
# Health check
curl https://your-app.ailabsafrica.com/api/vapi/health

# Get configuration
curl https://your-app.ailabsafrica.com/api/vapi/config

# Test webhook (returns raw PCM audio)
curl -X POST https://your-app.ailabsafrica.com/api/vapi/tts-webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-vapi-api-key" \
  -d '{
    "message": {
      "type": "voice-request",
      "text": "Testing Vapi webhook",
      "sampleRate": 24000
    },
    "timestamp": 1234567890
  }' \
  --output test_audio.pcm

# Play the PCM audio (requires ffmpeg)
ffplay -f s16le -ar 24000 -ac 1 test_audio.pcm
```

**Benefits vs. ElevenLabs/PlayHT:**

✅ **Cost Savings:** Use your own TTS infrastructure (no per-minute costs to 3rd party)
✅ **Control:** Choose from 20+ TTS models
✅ **Voice Cloning:** Use CoquiTTS/XTTS for custom voices
✅ **Quality:** Select models for specific use cases
✅ **Privacy:** Audio never leaves your infrastructure
✅ **Customization:** Fine-tune providers for your needs

---

## Integration Patterns

### Pattern 1: Service Initialization at App Startup

**When:** App starts (e.g., FastAPI `lifespan` or `startup` event)

**Why:** Initialize once, reuse throughout app lifetime

**Example (FastAPI):**
```python
# apps/yourapp/backend/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from apps.shared.services.tts_webui_service import TTSWebUIService

# Global service instances
tts_webui_service: TTSWebUIService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    global tts_webui_service

    # Startup
    print("Initializing TTS-WebUI service...")
    tts_webui_service = TTSWebUIService(
        enable_rate_limiting=True,
        user_rpm=60,
        org_rpm=600
    )

    yield  # App runs

    # Shutdown
    print("Closing TTS-WebUI service...")
    await tts_webui_service.close()

app = FastAPI(lifespan=lifespan)

# Use in routes
@app.post("/synthesize")
async def synthesize_text(request: SynthesizeRequest):
    global tts_webui_service

    response = await tts_webui_service.synthesize(
        TTSWebUISynthesisRequest(
            text=request.text,
            provider_id=TTSWebUIProvider.STYLETTS2
        ),
        user_id=request.user_id,
        org_id=request.org_id
    )

    return {"audio_base64": response.audio_base64}
```

---

### Pattern 2: Singleton Pattern

**When:** Need a single instance across the app

**Why:** Avoid re-initialization, share resources

**Example:**
```python
# apps/yourapp/backend/app/services/tts_service.py

from apps.shared.services.tts_webui_service import TTSWebUIService

_tts_webui_service: TTSWebUIService = None

async def get_tts_webui_service() -> TTSWebUIService:
    """Get or create singleton TTS-WebUI service."""
    global _tts_webui_service

    if _tts_webui_service is None:
        _tts_webui_service = TTSWebUIService()

    return _tts_webui_service

# Usage in routes
from app.services.tts_service import get_tts_webui_service

@app.post("/generate-audio")
async def generate_audio(text: str):
    service = await get_tts_webui_service()
    response = await service.synthesize(...)
    return response
```

---

### Pattern 3: Dependency Injection (FastAPI)

**When:** Using FastAPI dependency injection

**Why:** Clean, testable, follows FastAPI conventions

**Example:**
```python
# apps/yourapp/backend/app/dependencies.py

from fastapi import Depends
from apps.shared.services.tts_webui_service import TTSWebUIService

async def get_tts_webui_service() -> TTSWebUIService:
    """Dependency for TTS-WebUI service."""
    service = TTSWebUIService()
    try:
        yield service
    finally:
        await service.close()

# Usage in routes
from fastapi import Depends
from app.dependencies import get_tts_webui_service

@app.post("/synthesize")
async def synthesize(
    text: str,
    service: TTSWebUIService = Depends(get_tts_webui_service)
):
    response = await service.synthesize(...)
    return response
```

---

### Pattern 4: App-Specific Service Wrapper

**When:** Need custom logic on top of shared service

**Why:** Encapsulate app-specific behavior

**Example:**
```python
# apps/churchflow/backend/app/services/greeting_service.py

from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)

class ChurchGreetingService:
    """ChurchFlow-specific greeting generation."""

    def __init__(self):
        self.tts_service = TTSWebUIService()

    async def generate_welcome_greeting(
        self,
        member_name: str,
        event_name: str,
        user_id: str,
        org_id: str
    ):
        """Generate personalized greeting for church member."""

        # Custom greeting template
        text = f"Welcome {member_name} to {event_name}! We're blessed to have you with us today."

        # Use shared TTS service
        request = TTSWebUISynthesisRequest(
            text=text,
            provider_id=TTSWebUIProvider.STYLETTS2,
            language="en",
            speed=0.95  # Slightly slower for clarity
        )

        response = await self.tts_service.synthesize(
            request,
            user_id=user_id,
            org_id=org_id
        )

        return {
            "text": text,
            "audio_base64": response.audio_base64,
            "duration": response.duration
        }
```

---

## Step-by-Step Examples

### Example 1: Add TTS-WebUI to ChurchFlow

**Goal:** Generate voice greetings for conference check-ins using TTS-WebUI

**Steps:**

1. **Create Service Wrapper**

   `apps/churchflow/backend/app/services/tts_greeting_service.py`:
   ```python
   from apps.shared.services.tts_webui_service import (
       TTSWebUIService,
       TTSWebUISynthesisRequest,
       TTSWebUIProvider
   )

   class TTSGreetingService:
       def __init__(self):
           self.service = TTSWebUIService()

       async def generate_greeting(
           self,
           member_name: str,
           event_name: str,
           user_id: str,
           org_id: str
       ):
           text = f"Welcome {member_name} to {event_name}!"

           request = TTSWebUISynthesisRequest(
               text=text,
               provider_id=TTSWebUIProvider.STYLETTS2,
               language="en"
           )

           return await self.service.synthesize(
               request,
               user_id=user_id,
               org_id=org_id
           )
   ```

2. **Use in Route**

   `apps/churchflow/backend/app/api/routes/registrations.py`:
   ```python
   from app.services.tts_greeting_service import TTSGreetingService

   @router.post("/check-in")
   async def check_in_attendee(registration_id: str, user_id: str):
       # Get registration
       registration = await db.registrations.find_one({"_id": registration_id})

       # Generate greeting
       tts_service = TTSGreetingService()
       greeting = await tts_service.generate_greeting(
           member_name=registration["user_name"],
           event_name=registration["event_name"],
           user_id=user_id,
           org_id=registration["organization_id"]
       )

       return {
           "message": "Check-in successful",
           "greeting_audio": greeting.audio_base64
       }
   ```

3. **Test**
   ```bash
   curl -X POST http://localhost:30030/api/check-in \
     -H "Content-Type: application/json" \
     -d '{"registration_id": "reg_123", "user_id": "user_456"}'
   ```

---

### Example 2: Add TTS-WebUI to InkWave (Audiobook App)

**Goal:** Generate audiobook narration using multiple TTS models

**Steps:**

1. **Create Narration Service**

   `apps/inkwave/backend/app/services/audiobook_narration_service.py`:
   ```python
   from apps.shared.services.tts_webui_service import (
       TTSWebUIService,
       TTSWebUISynthesisRequest,
       TTSWebUIProvider,
       RateLimitExceeded
   )
   import base64

   class AudiobookNarrationService:
       def __init__(self):
           self.service = TTSWebUIService()

       async def narrate_chapter(
           self,
           book_id: str,
           chapter_text: str,
           provider: str,  # "styletts2", "bark", "tortoise"
           user_id: str,
           org_id: str
       ):
           """Narrate a book chapter using selected provider."""

           # Map provider string to enum
           provider_map = {
               "styletts2": TTSWebUIProvider.STYLETTS2,
               "bark": TTSWebUIProvider.BARK,
               "tortoise": TTSWebUIProvider.TORTOISE
           }

           provider_id = provider_map.get(provider, TTSWebUIProvider.STYLETTS2)

           try:
               request = TTSWebUISynthesisRequest(
                   text=chapter_text,
                   provider_id=provider_id,
                   language="en",
                   speed=1.0
               )

               response = await self.service.synthesize(
                   request,
                   user_id=user_id,
                   org_id=org_id
               )

               return {
                   "audio_base64": response.audio_base64,
                   "duration": response.duration,
                   "provider_used": response.provider_used
               }

           except RateLimitExceeded as e:
               return {
                   "error": "rate_limit_exceeded",
                   "message": e.message,
                   "retry_after": e.retry_after
               }
   ```

2. **Use in Route**

   `apps/inkwave/backend/app/api/routes/audiobooks.py`:
   ```python
   from app.services.audiobook_narration_service import AudiobookNarrationService

   @router.post("/narrate-chapter")
   async def narrate_chapter(
       book_id: str,
       chapter_number: int,
       provider: str = "styletts2"
   ):
       # Get chapter text from database
       chapter = await db.chapters.find_one({
           "book_id": book_id,
           "chapter_number": chapter_number
       })

       # Generate narration
       narration_service = AudiobookNarrationService()
       result = await narration_service.narrate_chapter(
           book_id=book_id,
           chapter_text=chapter["text"],
           provider=provider,
           user_id=chapter["author_id"],
           org_id=chapter["organization_id"]
       )

       if "error" in result:
           return {"error": result["error"], "retry_after": result["retry_after"]}

       # Save audio to storage
       audio_bytes = base64.b64decode(result["audio_base64"])
       # ... save to file storage

       return {
           "chapter_number": chapter_number,
           "audio_url": "...",
           "duration": result["duration"]
       }
   ```

---

### Example 3: Add TTS-WebUI to StudyFlow (Education App)

**Goal:** Generate pronunciation guides for vocabulary words

**Steps:**

1. **Create Pronunciation Service**

   `apps/studyflow/backend/app/services/pronunciation_service.py`:
   ```python
   from apps.shared.services.tts_webui_service import (
       TTSWebUIService,
       TTSWebUISynthesisRequest,
       TTSWebUIProvider
   )

   class PronunciationService:
       def __init__(self):
           self.service = TTSWebUIService()

       async def generate_pronunciation(
           self,
           word: str,
           language: str,
           user_id: str,
           org_id: str
       ):
           """Generate clear pronunciation of a word."""

           request = TTSWebUISynthesisRequest(
               text=word,
               provider_id=TTSWebUIProvider.KOKORO,  # Clear pronunciation
               language=language,
               speed=0.8  # Slower for learning
           )

           response = await self.service.synthesize(
               request,
               user_id=user_id,
               org_id=org_id
           )

           return {
               "word": word,
               "audio_base64": response.audio_base64,
               "duration": response.duration
           }
   ```

2. **Use in Route**

   `apps/studyflow/backend/app/api/routes/vocabulary.py`:
   ```python
   from app.services.pronunciation_service import PronunciationService

   @router.get("/word/{word_id}/pronunciation")
   async def get_word_pronunciation(word_id: str, user_id: str):
       # Get word
       word = await db.vocabulary.find_one({"_id": word_id})

       # Generate pronunciation
       pronunciation_service = PronunciationService()
       result = await pronunciation_service.generate_pronunciation(
           word=word["text"],
           language=word["language"],
           user_id=user_id,
           org_id=word["organization_id"]
       )

       return result
   ```

---

## Rate Limiting & Authentication

### Understanding Rate Limits

**Default Rate Limits (TTS-WebUI):**
- **Per User**: 60 requests/minute, 1000 requests/hour
- **Per Organization**: 600 requests/minute, 10,000 requests/hour

**Environment Variables:**
```bash
TTSWEBUI_USER_RPM=60
TTSWEBUI_USER_RPH=1000
TTSWEBUI_ORG_RPM=600
TTSWEBUI_ORG_RPH=10000
```

### Handling Rate Limits

```python
from apps.shared.middleware.rate_limiter import RateLimitExceeded

try:
    response = await service.synthesize(
        request,
        user_id="user_123",
        org_id="org_abc"
    )
except RateLimitExceeded as e:
    return {
        "error": "Rate limit exceeded",
        "message": e.message,
        "retry_after": e.retry_after
    }
```

### Disabling Rate Limiting (Development)

```python
service = TTSWebUIService(enable_rate_limiting=False)
```

### Custom Rate Limits

```python
service = TTSWebUIService(
    user_rpm=120,  # 120 requests/minute per user
    org_rpm=1200   # 1200 requests/minute per org
)
```

---

## Best Practices

### 1. Initialize Services Once

**✅ Good:**
```python
# At app startup
tts_service = TTSWebUIService()

# Use throughout app
response = await tts_service.synthesize(...)
```

**❌ Bad:**
```python
# Don't create new service on every request
@app.post("/synthesize")
async def synthesize(text: str):
    service = TTSWebUIService()  # Don't do this!
    response = await service.synthesize(...)
```

### 2. Always Pass User/Org IDs

**✅ Good:**
```python
response = await service.synthesize(
    request,
    user_id="user_123",
    org_id="org_abc"
)
```

**❌ Bad:**
```python
response = await service.synthesize(request)  # No rate limiting!
```

### 3. Handle Errors Gracefully

**✅ Good:**
```python
try:
    response = await service.synthesize(...)
except RateLimitExceeded as e:
    return {"error": "rate_limit", "retry_after": e.retry_after}
except httpx.HTTPError as e:
    logger.error(f"TTS failed: {e}")
    return {"error": "service_unavailable"}
```

### 4. Use Appropriate Provider

**✅ Good:**
```python
# For expressive content
provider_id=TTSWebUIProvider.STYLETTS2

# For fast synthesis
provider_id=TTSWebUIProvider.KOKORO

# For creative content
provider_id=TTSWebUIProvider.BARK
```

### 5. Clean Up Resources

**✅ Good:**
```python
# Use context manager
async with TTSWebUIService() as service:
    response = await service.synthesize(...)
# Auto-cleanup

# Or manually
service = TTSWebUIService()
try:
    response = await service.synthesize(...)
finally:
    await service.close()
```

---

## Troubleshooting

### Issue: Import Error

**Error:**
```
ModuleNotFoundError: No module named 'apps.shared'
```

**Solution:**
Ensure Python path includes `/opt/kasaai/apps`:
```python
# Add to your app's main.py or __init__.py
import sys
import os
sys.path.insert(0, "/opt/kasaai/apps")
```

Or set in environment:
```bash
export PYTHONPATH=/opt/kasaai/apps:/opt/kasaai/apps/yourapp/backend
```

---

### Issue: Rate Limit Exceeded

**Error:**
```
RateLimitExceeded: Rate limit exceeded for user. Try again in 45s.
```

**Solution:**
Wait for the retry_after period, or adjust rate limits:
```python
service = TTSWebUIService(
    user_rpm=120,  # Increase limit
    enable_rate_limiting=False  # Or disable for development
)
```

---

### Issue: Service Timeout

**Error:**
```
httpx.TimeoutException: Request timed out
```

**Solution:**
Increase timeout for long text:
```python
service = TTSWebUIService(timeout=600)  # 10 minutes
```

---

### Issue: Missing Environment Variables

**Error:**
```
Service returns 404 or connection refused
```

**Solution:**
Check environment variables are set:
```bash
echo $TTSWEBUI_WEBUI_ENDPOINT
# Should show: https://tts-webui.ailabsafrica.com
```

Add to `/opt/kasaai/.env`:
```bash
TTSWEBUI_WEBUI_ENDPOINT=https://tts-webui.ailabsafrica.com
TTSWEBUI_API_ENDPOINT=https://tts-webui.ailabsafrica.com/api
```

---

## Quick Reference

### Import Statements

```python
# TTS-WebUI
from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIVoiceCloneRequest,
    TTSWebUIProvider
)

# TTS Provider Service
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    VoiceCloneRequest
)

# Rate Limiting
from apps.shared.middleware.rate_limiter import (
    ServiceRateLimiter,
    RateLimitExceeded
)

# PDF Extraction
from apps.shared.services.pdf_extraction_service import get_pdf_extraction_service

# File Upload
from apps.shared.services.file_upload_service import get_file_upload_service

# Email Account
from apps.shared.services.email_account_service import get_email_account_service
```

### Environment Files

**Global:** `/opt/kasaai/.env` (shared by all apps)
**App-specific:** `/opt/kasaai/apps/yourapp/backend/.env`

---

## Support

**Questions?**
- Check service README: `/opt/kasaai/apps/shared/services/README.md`
- Check architecture docs: `/opt/kasaai/apps/architecture/`
- Check existing app implementations: `@apps/churchflow/`, `@apps/inkwave/`

**Found a bug or need a feature?**
- Update shared service and all apps benefit!
- Document patterns in this guide for other developers

---

**Last Updated:** November 8, 2025
**Version:** 1.0.0
**Maintainer:** AI Labs Africa Development Team

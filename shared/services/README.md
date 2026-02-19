# Shared Services - KasaAI Platform

Centralized services that can be used across all KasaAI applications.

## Overview

This directory contains high-level services that orchestrate multiple integration components to provide complete business functionality. These services are designed to be imported and used by any application in the platform.

## Available Services

### 1. TTS Provider Service (`tts_provider_service.py`)

**Purpose**: Centralized text-to-speech service with integrated billing, health monitoring, and provider management.

**What it provides**:
- Access to 10 TTS providers (Coqui, MeloTTS, F5-TTS, StyleTTS2, OpenVoice, Kokoro, Moshi, Akan MMS, Crawl4AI, and more)
- Automatic cost calculation and wallet deductions
- Provider health monitoring and status tracking
- Voice cloning support for compatible providers
- Request/response normalization across all providers
- Multi-language and multi-speaker support

**Architecture**:
```
Apps (Inkwave, StudyFlow, etc.)
    ↓
TTSProviderService (centralized service)
    ↓
├─> ProviderRegistry (ai_services) - Provider discovery
├─> HealthMonitor (ai_services) - Health monitoring
├─> WalletService (wallet integration) - Billing
└─> UsageCalculator (cost calculation) - Pricing
    ↓
TTS Provider Endpoints (Coqui, F5-TTS, etc.)
```

**Usage Example**:

```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    VoiceCloneRequest
)

# Initialize service (do this once, typically at app startup)
tts_service = TTSProviderService()
await tts_service.initialize()

# Get available providers
providers = await tts_service.get_available_providers()
print(f"Available: {list(providers.keys())}")

# Estimate cost before synthesis
cost_estimate = await tts_service.estimate_cost(
    text="Hello world, this is a test.",
    provider_id="coqui_xtts",
    voice_cloning=False
)
print(f"Estimated cost: ${cost_estimate.total_cost:.4f}")

# Synthesize speech (with automatic billing)
request = SynthesisRequest(
    provider_id="coqui_xtts",
    text="Hello world, this is a test.",
    language="en",
    voice_id="nova",
    speed=1.0
)

result = await tts_service.synthesize(
    user_id="user_123",
    request=request
)

# result contains:
# - audio_base64: Base64-encoded audio
# - duration: Audio duration in seconds
# - cost: Actual cost deducted
# - transaction_id: Wallet transaction ID
# - processing_time: Time taken to generate
```

**Voice Cloning Example**:

```python
from apps.shared.services.tts_provider_service import VoiceCloneRequest

# Synthesize with voice cloning (requires compatible provider)
clone_request = VoiceCloneRequest(
    provider_id="f5tts",  # or styletts2, coqui_xtts, openvoice
    text="This is my cloned voice speaking",
    reference_audio_base64=audio_base64,
    language="en",
    speed=1.0
)

clone_result = await tts_service.synthesize_with_voice_cloning(
    user_id="user_123",
    request=clone_request
)
```

**Cost Model**:
- **Base cost**: $0.015 per 1000 characters
- **Voice cloning premium**: +$0.05 per request
- **Provider premium**: 2x for premium providers (StyleTTS2, F5-TTS, OpenVoice)

**Example costs**:
- Coqui XTTS, 500 chars: $0.0075
- F5-TTS, 500 chars + voice cloning: $0.0650 ($0.015 base × 2 + $0.05 cloning)
- Akan MMS, 1000 chars: $0.0150

**Provider Capabilities**:

| Provider | Voice Cloning | Multi-Language | Speed Control | Pitch Control | Emotion Control |
|----------|--------------|----------------|---------------|---------------|-----------------|
| Coqui XTTS | ✅ | ✅ (17 langs) | ✅ | ❌ | ❌ |
| MeloTTS | ❌ | ✅ (6 langs) | ✅ | ✅ | ❌ |
| F5-TTS | ✅ | ✅ (4 langs) | ✅ | ❌ | ❌ |
| StyleTTS2 | ✅ | ❌ (EN only) | ❌ | ❌ | ✅ |
| OpenVoice | ✅ | ✅ (EN, ZH) | ❌ | ✅ | ✅ |
| Kokoro | ❌ | ❌ (EN only) | ✅ | ❌ | ❌ |
| Moshi | ❌ | ❌ (EN only) | ❌ | ❌ | ❌ |
| Akan MMS | ❌ | ❌ (Twi only) | ✅ | ✅ | ❌ |

**Error Handling**:

```python
from apps.shared.services.tts_provider_service import TTSProviderService

try:
    result = await tts_service.synthesize(user_id, request)
except ValueError as e:
    # Provider offline, invalid parameters, etc.
    print(f"Invalid request: {e}")
except Exception as e:
    # Insufficient funds, synthesis failed, etc.
    print(f"Synthesis failed: {e}")
```

**Testing (skip billing)**:

```python
# For development/testing, skip wallet deductions
result = await tts_service.synthesize(
    user_id="test_user",
    request=request,
    skip_billing=True  # No wallet deduction
)
```

**Initialization Options**:

```python
# Disable billing (useful for testing)
tts_service = TTSProviderService(
    enable_billing=False,
    enable_health_monitoring=True
)

# Disable health monitoring (faster startup)
tts_service = TTSProviderService(
    enable_billing=True,
    enable_health_monitoring=False
)

# Custom cache TTL
tts_service = TTSProviderService(
    cache_ttl=60  # Cache provider status for 60 seconds
)
```

**Shutdown**:

```python
# Cleanup when app shuts down
await tts_service.shutdown()
```

---

### 2. Voice Lab Service (`voice_lab_service.py`)

**Purpose**: Generic voice processing operations (ASR, TTS, voice cloning).

**What it provides**:
- Speech-to-text transcription (ASR)
- Text-to-speech synthesis (basic)
- LLM-powered chat
- Voice configuration models

**Note**: For full TTS provider access with billing, use `TTSProviderService` instead.

---

### 3. PDF Extraction Service (`pdf_extraction_service.py`)

**Purpose**: Extract structured data from expense receipts and invoices with automatic field detection.

**What it provides**:
- Text-based PDF extraction (pdfplumber)
- OCR support for scanned documents (Tesseract)
- Pattern matching for common receipt formats
- Confidence scoring for extracted data
- Multi-currency support (USD, GHS, EUR, GBP, NGN, ZAR, etc.)

**Extracted Fields**:
- Merchant/Vendor name
- Transaction date
- Total amount
- Tax amount
- Currency
- Category (inferred from keywords)
- Payment method
- Receipt number

**Usage Example**:

```python
from apps.shared.services.pdf_extraction_service import (
    get_pdf_extraction_service,
    PDFExtractionError
)

# Get service instance
pdf_service = get_pdf_extraction_service(use_ocr=True)

# Extract data from PDF
with open("receipt.pdf", "rb") as pdf_file:
    expense_data = await pdf_service.extract_from_pdf(pdf_file)

# Access extracted fields
print(f"Merchant: {expense_data.merchant}")
print(f"Amount: {expense_data.amount}")
print(f"Date: {expense_data.date}")
print(f"Confidence: {expense_data.confidence}")

# Convert to dict for API responses
data_dict = expense_data.to_dict()
```

**Confidence Scoring**:
- `1.0`: All fields extracted successfully
- `0.8-0.9`: Most fields extracted (high confidence)
- `0.5-0.7`: Some fields extracted (medium confidence)
- `< 0.5`: Few fields extracted (low confidence)

**Dependencies**:
```bash
pip install pdfplumber>=0.11.0
pip install pytesseract>=0.3.10
pip install Pillow>=10.0.0
pip install pdf2image>=1.16.3

# System dependencies
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
```

**Full Documentation**: `/opt/kasaai/apps/architecture/PDF_EXTRACTION_SERVICE.md`

---

### 4. File Upload Service (`file_upload_service.py`)

**Purpose**: Handle file uploads to cloud storage with validation, organization, and URL generation.

**What it provides**:
- File validation (size, type, content)
- Automatic file organization by org/category/date
- Cloud storage integration (Hetzner Storage Box)
- Fallback to local storage for development
- Unique file ID generation
- Metadata tracking

**Supported File Types**:
- **Documents**: PDF, DOC, DOCX, TXT, CSV (max 25-50MB)
- **Images**: JPEG, PNG, GIF, WebP (max 10MB)
- **Spreadsheets**: XLS, XLSX (max 50MB)

**File Organization**:
```
uploads/{org_id}/{category}/{year}/{month}/{file_id}{extension}

Example:
uploads/org_abc123/receipts/2025/11/20251103120000_a1b2c3d4.pdf
```

**Usage Example**:

```python
from apps.shared.services.file_upload_service import (
    get_file_upload_service,
    FileUploadError,
    FileValidationError
)

# Get service instance
upload_service = await get_file_upload_service()

# Upload file
with open("receipt.pdf", "rb") as file:
    upload_info = await upload_service.upload_file(
        file=file,
        filename="receipt.pdf",
        organization_id="org_abc123",
        file_category="receipts",
        metadata={
            "uploaded_by": "user_123",
            "description": "Office supplies receipt"
        }
    )

print(f"File URL: {upload_info['url']}")
print(f"File ID: {upload_info['file_id']}")

# Delete file
await upload_service.delete_file(upload_info['path'])
```

**With FastAPI**:

```python
from fastapi import UploadFile, File
from apps.shared.services.file_upload_service import get_file_upload_service

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), org_id: str):
    content = await file.read()

    upload_service = await get_file_upload_service()
    upload_info = await upload_service.upload_file(
        file=content,
        filename=file.filename,
        organization_id=org_id,
        file_category="receipts"
    )

    return upload_info
```

**Error Handling**:

```python
try:
    upload_info = await upload_service.upload_file(...)
except FileValidationError as e:
    # File validation failed (wrong type, too large, corrupted)
    return {"error": "Invalid file", "message": str(e)}
except FileUploadError as e:
    # Upload failed (storage issue, network error)
    return {"error": "Upload failed", "message": str(e)}
```

**Full Documentation**: `/opt/kasaai/apps/architecture/PDF_EXTRACTION_SERVICE.md`

---

### 5. Email Account Service (`email_account_service.py`)

**Purpose**: Manage email accounts on iRedMail server for employee onboarding/offboarding automation.

**What it provides**:
- Automatic email account creation for new employees
- Email account deactivation on employee termination
- Email address generation with duplicate handling
- Operation logging and error handling
- Integration with custom iRedMail REST API

**Email Generation**:
- Format: `firstname.lastname@ailabsafrica.com`
- Duplicate handling: `john.doe2@ailabsafrica.com`, `john.doe3@...`
- Name sanitization (removes special characters)

**Usage Example**:

```python
from apps.shared.services.email_account_service import (
    get_email_account_service,
    EmailAccountError,
    EmailAlreadyExistsError
)

# Get service instance
email_service = get_email_account_service()

# Create email account
result = await email_service.create_account(
    first_name="John",
    last_name="Doe",
    email="john.doe@ailabsafrica.com",  # Optional - can auto-generate
    quota_mb=512
)

print(f"Email: {result['email']}")
print(f"Temporary Password: {result['password']}")
print(f"Status: {result['status']}")

# Check if account exists
exists = await email_service.check_exists("john.doe@ailabsafrica.com")

# Disable account (on termination)
await email_service.disable_account("john.doe@ailabsafrica.com")

# Enable account (reactivation)
await email_service.enable_account("john.doe@ailabsafrica.com")
```

**With Employee Creation**:

```python
from apps.shared.services.email_account_service import get_email_account_service

# In employee creation endpoint
employee_data = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@ailabsafrica.com",
    "department": "Engineering",
    ...
}

# Create employee record first
employee = await db.employees.insert_one(employee_data)

# Then create email account
email_service = get_email_account_service()
try:
    result = await email_service.create_account(
        first_name=employee_data["first_name"],
        last_name=employee_data["last_name"],
        email=employee_data["email"]
    )

    # Update employee record with email details
    await db.employees.update_one(
        {"_id": employee["_id"]},
        {
            "$set": {
                "email_account_created": True,
                "email_account_status": "active",
                "email_temporary_password": result["password"]
            }
        }
    )

    # Return password to user (display once)
    return {
        "employee": employee_data,
        "temporary_password": result["password"]
    }

except EmailAlreadyExistsError:
    # Handle duplicate email
    logger.warning(f"Email already exists: {employee_data['email']}")
    # Employee still created, just flag email creation failed
```

**Error Handling**:

```python
try:
    result = await email_service.create_account(...)
except EmailAlreadyExistsError as e:
    # Email account already exists
    print(f"Duplicate email: {e}")
except EmailAccountError as e:
    # General error (API down, network issue, etc.)
    print(f"Failed to create email: {e}")
```

**Auto-retry Logic**:
- Automatic retry with exponential backoff
- Max 3 attempts (1s, 2s, 4s delay)
- Timeout: 30 seconds per request

**Configuration** (from .env):
```ini
IREDMAIL_API_URL=http://85.214.12.174:8100
IREDMAIL_API_KEY=your-secret-api-key
IREDMAIL_DEFAULT_QUOTA_MB=512
```

**Backend Architecture**:
```
ERP Employee Routes
    ↓
EmailAccountService (shared service)
    ↓ HTTP
iRedMail REST API (mail server)
    ↓ CLI
iRedMail Server (mail.ailabsafrica.com)
```

**Security**:
- API key authentication
- IP whitelist (ERP server only)
- Secure password generation (16 chars, crypto-random)
- HTTPS recommended for production
- Audit logging of all operations

**Full Documentation**: `/opt/kasaai/apps/erp/EMPLOYEE_EMAIL_AUTOMATION.md`

---

### 6. TTS-WebUI Service (`tts_webui_service.py`)

**Purpose**: Programmatic access to TTS-WebUI, a comprehensive platform supporting 20+ TTS models with React UI and Gradio backend.

**What it provides**:
- Access to 20+ TTS models (StyleTTS2, RVC, Bark, Tortoise, Kokoro, OpenVoice, F5-TTS, etc.)
- Voice cloning for compatible providers
- Multi-language synthesis
- OpenAI-compatible API interface
- Extension management and provider discovery
- Real-time synthesis with various audio formats

**Supported Providers**:
- **StyleTTS2** - High-quality expressive TTS with voice cloning and emotion control
- **RVC** - Voice conversion and transformation
- **Bark** - Multi-lingual TTS with music and sound effects
- **Tortoise TTS** - High-quality slow synthesis
- **MeloTTS** - Fast synthesis with multiple speakers
- **Kokoro TTS** - English narration with 11 voicepacks
- **OpenVoice** - Voice cloning with emotion and tone control
- **F5-TTS** - Flow-matching based voice cloning
- **Parler TTS** - Natural conversational synthesis
- **VALL-E X** - Zero-shot voice cloning
- **XTTS v2** - Multi-lingual voice cloning
- **And 10+ more models**

**Provider Capabilities**:

| Provider | Voice Cloning | Languages | Emotion Control | Special Features |
|----------|--------------|-----------|-----------------|------------------|
| StyleTTS2 | ✅ | EN | ✅ | Style transfer, expressive |
| RVC | ✅ | Multi | ❌ | Voice conversion |
| F5-TTS | ✅ | EN,ZH,JA,KO | ❌ | Flow-matching, high quality |
| OpenVoice | ✅ | EN,ZH | ✅ | Tone conversion |
| Bark | ❌ | Multi | ❌ | Music, sound effects |
| Kokoro | ❌ | EN | ❌ | 11 voicepacks |
| MeloTTS | ❌ | 6 langs | ❌ | Fast synthesis |

**Usage Example**:

```python
from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)

# Initialize service
service = TTSWebUIService()

# Simple synthesis
request = TTSWebUISynthesisRequest(
    text="Hello from AI Labs Africa!",
    provider_id=TTSWebUIProvider.STYLETTS2,
    language="en",
    speed=1.0,
    output_format="wav"
)

response = await service.synthesize(request)

# Access audio
audio_bytes = base64.b64decode(response.audio_base64)
with open("output.wav", "wb") as f:
    f.write(audio_bytes)

print(f"Duration: {response.duration:.2f}s")
print(f"Sample Rate: {response.sample_rate}Hz")
```

**Voice Cloning Example**:

```python
from apps.shared.services.tts_webui_service import (
    TTSWebUIVoiceCloneRequest,
    TTSWebUIProvider
)

# Load reference audio
with open("reference_voice.wav", "rb") as f:
    ref_audio_b64 = base64.b64encode(f.read()).decode()

# Clone voice
request = TTSWebUIVoiceCloneRequest(
    text="This is my cloned voice speaking",
    provider_id=TTSWebUIProvider.STYLETTS2,
    reference_audio_base64=ref_audio_b64,
    reference_text="Transcript of reference audio",  # Optional but recommended
    language="en",
    speed=1.0
)

response = await service.synthesize_with_voice_cloning(request)
```

**Provider Discovery**:

```python
# List all available providers
providers = await service.list_providers()
for provider in providers:
    print(f"{provider.name}:")
    print(f"  Languages: {provider.languages}")
    print(f"  Voice Cloning: {provider.capabilities.get('voice_cloning', False)}")
    print(f"  Installed: {provider.installed}")

# Get specific provider info
info = await service.get_provider_info(TTSWebUIProvider.STYLETTS2)
print(f"StyleTTS2 capabilities: {info.capabilities}")

# List voices for a provider
voices = await service.list_voices(TTSWebUIProvider.KOKORO)
print(f"Kokoro voices: {voices}")
```

**Health Check**:

```python
# Check TTS-WebUI health
health = await service.health_check()
print(f"Status: {health['status']}")
print(f"Models loaded: {health.get('models_loaded', 0)}")
```

**Async Context Manager**:

```python
# Automatic cleanup
async with TTSWebUIService() as service:
    request = TTSWebUISynthesisRequest(
        text="Hello world",
        provider_id=TTSWebUIProvider.BARK
    )
    response = await service.synthesize(request)
    # Connection automatically closed when exiting context
```

**Singleton Pattern**:

```python
from apps.shared.services.tts_webui_service import get_tts_webui_service

# Get global singleton instance
service = await get_tts_webui_service()

# Use in multiple places without re-initialization
response1 = await service.synthesize(request1)
response2 = await service.synthesize(request2)
```

**Configuration** (from .env):
```ini
# TTS-WebUI Endpoints
TTSWEBUI_WEBUI_ENDPOINT=https://tts-webui.ailabsafrica.com
TTSWEBUI_API_ENDPOINT=https://tts-webui.ailabsafrica.com/api
TTSWEBUI_API_KEY=optional-api-key-if-auth-enabled
```

**Deployment Architecture**:
```
Applications (Inkwave, StudyFlow, etc.)
    ↓
TTSWebUIService (shared service)
    ↓ HTTPS
TTS-WebUI API (port 7778)
    ↓
Gradio Backend (port 7770)
    ↓
20+ TTS Models (StyleTTS2, RVC, Bark, etc.)
```

**RunPod Deployment**:
- **Server**: RunPod GPU Cloud (NVIDIA A40, 44GB VRAM)
- **React UI**: Port 3000 (Next.js)
- **Gradio Backend**: Port 7770
- **OpenAI API**: Port 7778
- **Nginx Proxy**: Port 8016 → 3000
- **Public URL**: https://tts-webui.ailabsafrica.com
- **RunPod URL**: https://jzfmzviw26huka-8016.proxy.runpod.net

**Available Models** (via Extension Manager):
- Core: StyleTTS2, RVC, Bark, Tortoise, MeloTTS, MMS
- Advanced: F5-TTS, XTTS v2, OpenVoice, Kokoro, Parler TTS
- Specialty: Whisper (ASR), MusicGen, Stable Audio, Demucs (separation)
- Experimental: GPT-SoVITS, Chatterbox, MahaTTS, VALL-E X

**Error Handling**:

```python
import httpx

try:
    response = await service.synthesize(request)
except httpx.HTTPStatusError as e:
    # HTTP error (404, 500, etc.)
    print(f"API error: {e.response.status_code} - {e.response.text}")
except httpx.TimeoutException:
    # Request timeout (default: 300s)
    print("Request timed out")
except ValueError as e:
    # Invalid parameters or provider not found
    print(f"Invalid request: {e}")
```

**Best Practices**:

1. **Use appropriate provider for task**:
   - StyleTTS2 for expressive English content
   - F5-TTS for high-quality voice cloning
   - Bark for creative content with sound effects
   - Kokoro for fast English narration
   - RVC for voice transformation/conversion

2. **Provide reference text for voice cloning**:
   ```python
   # ✅ Good: Include reference text
   request = TTSWebUIVoiceCloneRequest(
       text="New text to synthesize",
       reference_audio_base64=audio_b64,
       reference_text="Transcript of reference audio",  # Improves quality
       provider_id=TTSWebUIProvider.STYLETTS2
   )
   ```

3. **Handle timeouts for long text**:
   ```python
   # For long text, increase timeout
   service = TTSWebUIService(timeout=600)  # 10 minutes
   ```

4. **Use singleton for multiple requests**:
   ```python
   # ✅ Good: Reuse service instance
   service = await get_tts_webui_service()
   for text in texts:
       response = await service.synthesize(...)

   # ❌ Bad: Create new service each time
   for text in texts:
       service = TTSWebUIService()
       response = await service.synthesize(...)
       await service.close()
   ```

**Testing Without Deployment**:

```python
# For development, point to local TTS-WebUI instance
service = TTSWebUIService(
    webui_endpoint="http://localhost:3000",
    api_endpoint="http://localhost:7778",
    timeout=300
)
```

**Full Documentation**:
- Service file: `/opt/kasaai/apps/shared/services/tts_webui_service.py`
- Deployment guide: `/opt/kasaai/apps/tts-deployment/TTS_WEBUI_DEPLOYMENT_STATUS.md`
- Architecture: `/opt/kasaai/apps/architecture/TTS_INFRASTRUCTURE.md`

---

### 7. Vapi TTS Webhook Service (`vapi_tts_webhook.py`)

**Purpose**: Custom TTS webhook integration for Vapi voice AI assistants using our TTS-WebUI infrastructure.

**What it provides**:
- Custom TTS endpoint for Vapi voice assistants
- Real-time PCM audio conversion for phone calls
- Access to 20+ TTS models through TTS-WebUI
- Rate limiting per user/organization
- Fallback provider support
- Health monitoring and statistics
- Authentication via Vapi API key

**Architecture**:
```
Vapi Phone Call
    ↓
Vapi sends POST request with text
    ↓
Your App's Vapi Webhook Endpoint
    ↓
VapiTTSWebhookService
    ├─> TTSWebUIService (synthesize speech)
    ├─> ServiceRateLimiter (rate limiting)
    └─> Audio Converter (PCM conversion)
    ↓
Returns raw PCM audio (16-bit, mono, 24kHz)
    ↓
Vapi streams audio to caller
```

**Usage Example**:

```python
from apps.shared.services.vapi_tts_webhook import (
    VapiTTSWebhookService,
    VapiWebhookRequest,
    get_vapi_webhook_service
)
from apps.shared.routers import vapi_webhook_router
from fastapi import FastAPI

# Method 1: Use the pre-built FastAPI router (recommended)
app = FastAPI()
app.include_router(
    vapi_webhook_router,
    prefix="/api/vapi",
    tags=["vapi"]
)

# This adds these endpoints:
# POST /api/vapi/tts-webhook - Main webhook
# GET  /api/vapi/health - Health check
# GET  /api/vapi/config - Configuration
# POST /api/vapi/stats/reset - Reset stats

# Method 2: Use the service directly
service = VapiTTSWebhookService(
    default_provider=TTSWebUIProvider.STYLETTS2,
    fallback_provider=TTSWebUIProvider.KOKORO,
    enable_rate_limiting=True,
    org_rpm=100,  # 100 requests/minute per org
    user_rpm=30   # 30 requests/minute per user
)

# Process Vapi webhook request
request = VapiWebhookRequest(
    message={
        "type": "voice-request",
        "text": "Hello, welcome to KasaAI!",
        "sampleRate": 24000
    },
    timestamp=1234567890,
    assistant={"organizationId": "org_123"}
)

pcm_audio = await service.process_webhook_request(
    request=request,
    auth_header="Bearer your-vapi-api-key"
)
# Returns raw PCM bytes ready for Vapi
```

**Vapi Assistant Configuration**:

In your Vapi dashboard, configure your assistant to use the custom TTS:

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

**Environment Variables**:

```bash
# Add to your app's .env
VAPI_API_KEY=your-vapi-api-key

# Rate limits (optional - defaults shown)
VAPI_USER_RPM=30          # Requests per minute per user
VAPI_USER_RPH=500         # Requests per hour per user
VAPI_ORG_RPM=100          # Requests per minute per org
VAPI_ORG_RPH=2000         # Requests per hour per org
```

**Error Handling**:

```python
from apps.shared.middleware.rate_limiter import RateLimitExceeded

try:
    pcm_audio = await service.process_webhook_request(request, auth_header)
except ValueError as e:
    # Invalid request or authentication failure
    print(f"Invalid request: {e}")
except RateLimitExceeded as e:
    # Rate limit exceeded
    print(f"Rate limited: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
except Exception as e:
    # TTS synthesis failed
    print(f"TTS failed: {e}")
```

**Health Monitoring**:

```python
# Get service statistics
stats = service.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Fallback usage: {stats['fallback_rate']:.1%}")

# Reset statistics
service.reset_stats()
```

**Testing**:

```bash
# Health check
curl https://your-app.ailabsafrica.com/api/vapi/health

# Test webhook
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
  --output test.pcm

# Play PCM audio (requires ffmpeg)
ffplay -f s16le -ar 24000 -ac 1 test.pcm
```

**Best Practices**:

1. **Choose appropriate providers**:
   - StyleTTS2: Expressive, natural voices (default)
   - Kokoro: Fast, low-latency (good fallback)
   - CoquiTTS: Voice cloning for custom voices

2. **Enable rate limiting**: Protect against abuse
   ```python
   service = VapiTTSWebhookService(
       enable_rate_limiting=True,
       org_rpm=100,  # Per organization
       user_rpm=30   # Per user (phone number)
   )
   ```

3. **Configure fallback provider**: Ensure reliability
   ```python
   service = VapiTTSWebhookService(
       default_provider=TTSWebUIProvider.STYLETTS2,
       fallback_provider=TTSWebUIProvider.KOKORO
   )
   ```

4. **Adjust timeout for long text**:
   ```python
   service = VapiTTSWebhookService(timeout=45)  # 45 seconds
   ```

**Benefits vs. ElevenLabs/PlayHT**:

✅ **Cost Savings**: No per-minute charges to third parties
✅ **Full Control**: Choose from 20+ TTS models
✅ **Voice Cloning**: Use custom voices with CoquiTTS/XTTS
✅ **Privacy**: Audio stays in your infrastructure
✅ **Flexibility**: Switch providers based on use case

**Full Documentation**:
- Service file: `/home/dev/apps/shared/services/vapi_tts_webhook.py`
- Router file: `/home/dev/apps/shared/routers/vapi_webhook_router.py`
- Integration guide: `/home/dev/apps/shared/INTEGRATION_GUIDE_FOR_APPS.md#7-vapi-tts-webhook-service-new`
- Tests: `/home/dev/apps/shared/tests/test_vapi_webhook.py`

---

## Integration Patterns

### Pattern 1: Inkwave (Audiobook App)

```python
# apps/inkwave/backend/services/narration_service.py

from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)

class NarrationService:
    def __init__(self):
        self.tts = TTSProviderService()

    async def narrate_book_chunk(
        self,
        user_id: str,
        book_id: str,
        chunk_text: str,
        provider_id: str = "coqui_xtts"
    ):
        # 1. Estimate cost
        cost = await self.tts.estimate_cost(chunk_text, provider_id)

        # 2. Synthesize with automatic billing
        result = await self.tts.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id=provider_id,
                text=chunk_text,
                language="en",
                speed=1.0
            )
        )

        # 3. Save audio to storage and return URL
        audio_url = await self.save_audio_to_storage(
            book_id=book_id,
            audio_base64=result.audio_base64
        )

        return {
            "audio_url": audio_url,
            "duration": result.duration,
            "cost": result.cost,
            "transaction_id": result.transaction_id
        }
```

### Pattern 2: StudyFlow (Educational App)

```python
# apps/studyflow/backend/services/pronunciation_service.py

from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)

class PronunciationService:
    def __init__(self):
        self.tts = TTSProviderService()

    async def generate_pronunciation_guide(
        self,
        user_id: str,
        word: str,
        language: str = "en"
    ):
        # Use high-quality provider for pronunciation
        result = await self.tts.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id="coqui_xtts",  # Clear pronunciation
                text=word,
                language=language,
                speed=0.8  # Slower for learning
            )
        )

        return {
            "word": word,
            "audio_base64": result.audio_base64,
            "cost": result.cost
        }
```

### Pattern 3: Core Backend (B2C Portal)

```python
# apps/core_backend/backend/services/tts_lab_service.py

from apps.shared.services.tts_provider_service import (
    get_tts_service  # Use singleton
)

class TTSLabService:
    async def test_provider(
        self,
        user_id: str,
        provider_id: str,
        text: str
    ):
        # Get global TTS service instance
        tts_service = await get_tts_service()

        # Test synthesis (with billing)
        result = await tts_service.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id=provider_id,
                text=text,
                language="en"
            )
        )

        return result
```

---

## Best Practices

### 1. Initialize Once

```python
# ✅ Good: Initialize at app startup
async def startup():
    global tts_service
    tts_service = TTSProviderService()
    await tts_service.initialize()

# ❌ Bad: Initialize on every request
async def synthesize_text(text):
    tts = TTSProviderService()  # Don't do this!
    await tts.initialize()
```

### 2. Handle Errors Gracefully

```python
# ✅ Good: Catch specific exceptions
try:
    result = await tts_service.synthesize(user_id, request)
except ValueError as e:
    return {"error": "Invalid provider or parameters"}
except Exception as e:
    logger.error(f"Synthesis failed: {e}")
    return {"error": "Service temporarily unavailable"}
```

### 3. Estimate Cost First

```python
# ✅ Good: Show cost estimate to user
cost = await tts_service.estimate_cost(text, provider_id)
if user_confirms_cost:
    result = await tts_service.synthesize(...)

# ❌ Bad: Surprise charges
result = await tts_service.synthesize(...)  # User didn't know cost
```

### 4. Use Appropriate Provider

```python
# ✅ Good: Match provider to use case
if need_voice_cloning:
    provider_id = "f5tts"  # Excellent cloning
elif language == "tw":
    provider_id = "akan_mms"  # Native Twi
elif need_fast:
    provider_id = "melotts"  # Fast synthesis
else:
    provider_id = "coqui_xtts"  # Good all-rounder
```

### 5. Cleanup on Shutdown

```python
# ✅ Good: Cleanup resources
async def shutdown():
    await tts_service.shutdown()
```

---

## Testing

### Unit Tests

```python
# tests/test_tts_service.py

import pytest
from apps.shared.services.tts_provider_service import TTSProviderService

@pytest.mark.asyncio
async def test_cost_estimation():
    service = TTSProviderService(enable_billing=False)
    await service.initialize()

    cost = await service.estimate_cost(
        text="Hello world",
        provider_id="coqui_xtts",
        voice_cloning=False
    )

    assert cost.total_cost > 0
    assert cost.character_count == 11

@pytest.mark.asyncio
async def test_synthesis_without_billing():
    service = TTSProviderService(enable_billing=False)
    await service.initialize()

    result = await service.synthesize(
        user_id="test_user",
        request=SynthesisRequest(
            provider_id="coqui_xtts",
            text="Test",
            language="en"
        ),
        skip_billing=True
    )

    assert result.audio_base64 is not None
    assert result.duration > 0
```

---

## Troubleshooting

### Problem: "Provider not found"

**Solution**: Check that provider ID is correct and registered:

```python
providers = await tts_service.get_available_providers()
print(list(providers.keys()))
```

### Problem: "Provider is offline"

**Solution**: Check provider health:

```python
provider = await tts_service.get_provider("coqui_xtts")
print(f"Status: {provider['status']}")
```

### Problem: "Insufficient balance"

**Solution**: Check user wallet:

```python
from apps.shared.integration.wallet import WalletService

wallet_service = WalletService()
wallet = await wallet_service.get_wallet_by_user(user_id)
print(f"Balance: ${wallet.balance:.2f}")
```

### Problem: "TTSProviderService not initialized"

**Solution**: Always initialize before use:

```python
tts_service = TTSProviderService()
await tts_service.initialize()  # Don't forget this!
```

---

## Architecture Decision Records

### Why Proxy Pattern instead of Registry?

**Decision**: Apps call shared service, which calls providers (proxy pattern).

**Rationale**:
- Centralized billing (can't trust clients to report usage)
- Consistent error handling across all apps
- Easier to add caching, rate limiting, logging
- Single point for provider failover/retry

### Why @apps/shared/services/ instead of @apps/shared/integration/?

**Decision**: TTS service lives in `services/`, not `integration/`.

**Rationale**:
- `integration/` is for external service wrappers (Stripe, Gemini, etc.)
- `services/` is for business logic orchestrating multiple integrations
- TTS service orchestrates: providers + wallet + usage calculator

---

## Migration Guide

### From core_backend/tts_provider_service.py

**Before**:
```python
from apps.core_backend.backend.services.tts_provider_service import TTSProviderService
```

**After**:
```python
from apps.shared.services.tts_provider_service import TTSProviderService
```

### From @apps/shared/integration/ai_services/tts_service.py

**Before** (external providers only):
```python
from apps.shared.integration.ai_services.tts_service import TTSService

tts = TTSService(provider="openai", api_key=key)
audio = await tts.synthesize("Hello")
```

**After** (all providers + billing):
```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)

tts = TTSProviderService()
await tts.initialize()

result = await tts.synthesize(
    user_id="user_123",
    request=SynthesisRequest(
        provider_id="coqui_xtts",
        text="Hello",
        language="en"
    )
)
```

---

## Additional Resources

- **Provider Registry**: `/opt/kasaai/apps/shared/integration/ai_services/provider_registry.py`
- **Health Monitor**: `/opt/kasaai/apps/shared/integration/ai_services/health_monitor_service.py`
- **Wallet Service**: `/opt/kasaai/apps/shared/integration/wallet.py`
- **Usage Calculator**: `/opt/kasaai/apps/shared/integration/usage_calculator.py`
- **Architecture Docs**: `/opt/kasaai/apps/architecture/ARCHITECTURE.md`
- **Integration Guide**: `/opt/kasaai/apps/architecture/INTEGRATION_GUIDE.md`

---

**Questions or Issues?**

- Check existing app implementations (`@apps/inkwave/`, `@apps/studyflow/`)
- Review shared service source code for detailed behavior
- Update this README if you find better patterns!

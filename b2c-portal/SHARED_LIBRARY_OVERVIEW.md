# KasaAI Shared Library - Comprehensive Exploration Report

**Generated**: 2025-11-11  
**Location**: `/opt/kasaai/apps/shared/`  
**Total Python Files**: 286  
**Total Services**: 34  
**Total Integrations**: 50+  
**Total Industry Modules**: 13  
**Frontend Components**: 20+

---

## Executive Summary

The shared library is a **production-ready, comprehensive platform for all KasaAI applications**. It provides:

- **Unified Authentication** via Supabase
- **34 High-level Business Services** (TTS, PDF extraction, file upload, etc.)
- **50+ Integration Endpoints** (payments, CRM, ERP, communication, etc.)
- **13 Industry-Specific Modules** with automation workflows
- **Voice Processing Pipeline** (ASR, TTS, VAD, RAG)
- **Multi-tenant Organization System**
- **Reusable Frontend Components** (React/TypeScript)

**Critical Finding**: The shared library is mature and well-tested. **B2C Portal should heavily leverage these components rather than reimplementing them.**

---

## 1. AUTHENTICATION & AUTHORIZATION

### Location
- `/opt/kasaai/apps/shared/auth/`
- `/opt/kasaai/apps/shared/models/organization.py`

### Key Components

#### Supabase Authentication (`supabase_auth.py`)
**Purpose**: Centralized JWT-based authentication for all apps

**Key Functions**:
```python
get_current_user(request, authorization) -> Dict[str, Any]
    # Required for protected routes
    # Returns: {id, email, user_metadata, app_metadata, display_name, etc.}

get_current_user_optional(request, authorization) -> Optional[Dict[str, Any]]
    # For endpoints that work with both authenticated and anonymous users

verify_supabase_token(token: str) -> Optional[Dict[str, Any]]
    # Low-level token verification without FastAPI dependency

get_supabase_client() -> Client
    # Get or create Supabase client instance
```

**Usage Pattern**:
```python
from fastapi import Depends
from apps.shared.auth.supabase_auth import get_current_user

@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return {"user_id": user["id"], "email": user["email"]}
```

#### Organization Model (`organization.py`)
**Purpose**: Multi-tenant support with roles and permissions

**Key Classes**:
- `Organization` - Tenant entity with billing, branding, settings
- `OrganizationUser` - User membership with roles
- `OrganizationRole` - UNIVERSAL_ADMIN, ADMIN, USER
- `Address`, `InvoiceSettings` - Supporting structures

**Key Fields**:
- Organization ID (UUID)
- Display name, description, industry
- Billing settings (subscription, wallet, cost tracking)
- Brand settings (logo, colors, fonts)
- Feature flags and module settings
- Audit trail and creation dates

### Reusability for B2C Portal
✅ **READY TO USE** - Import and use directly:
```python
from apps.shared.auth.supabase_auth import get_current_user
from apps.shared.models.organization import Organization
```

---

## 2. VOICE & LANGUAGE SERVICES

### Location
- `/opt/kasaai/apps/shared/services/` (voice services)
- `/opt/kasaai/apps/shared/integration/ai_services/` (low-level AI infrastructure)
- `/opt/kasaai/apps/shared/voice_engine/` (WebRTC & outbound calls)

### 2.1 High-Level Voice Services (Recommended for B2C)

#### ConversationalVoiceService
**Purpose**: Complete voice chat with RAG integration

**Pipeline**:
```
User Voice Input → ASR (transcription) → RAG + LLM (response) → TTS (audio output)
```

**Key Features**:
- Real-time streaming support
- Domain-specific knowledge bases via RAG
- Multi-language support
- Conversation history tracking
- ASR/TTS provider selection

**Usage**:
```python
from apps.shared.services.conversational_voice_service import (
    ConversationalVoiceService,
    VoiceConversationRequest
)

service = ConversationalVoiceService()
await service.initialize()

result = await service.process_voice_message(
    user_id="user_123",
    request=VoiceConversationRequest(
        audio_base64="...",
        collection_name="kasaai_faq",  # RAG collection
        asr_provider_id="whisper_large_v3",
        tts_provider_id="coqui_xtts",
        language="en"
    )
)
# Returns: {transcription, response_text, audio_base64, duration, etc.}
```

#### TTSProviderService
**Purpose**: Unified TTS with automatic billing and provider failover

**Supported Providers** (11 total):
- Coqui XTTS v2 (self-hosted, voice cloning)
- ElevenLabs (high-quality English)
- Google Text-to-Speech
- OpenAI TTS
- PlayHT
- F5-TTS (voice cloning)
- IndexTTS 2.0 (voice cloning, emotion)
- VoxCPM (context-aware, multilingual)
- Glow-TTS
- VITS-fast
- Bark

**Key Features**:
- Voice cloning support
- Multi-language support
- Automatic cost calculation and billing
- Health monitoring and failover
- Request/response normalization

**Usage**:
```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    VoiceCloneRequest
)

tts = TTSProviderService()
await tts.initialize()

# Basic synthesis with auto-billing
result = await tts.synthesize(
    user_id="user_123",
    request=SynthesisRequest(
        provider_id="coqui_xtts",
        text="Hello world",
        language="en",
        voice_id="nova"
    )
)
# Returns: {audio_base64, duration, cost, transaction_id}

# Voice cloning
clone_result = await tts.synthesize_with_voice_cloning(
    user_id="user_123",
    request=VoiceCloneRequest(
        provider_id="f5tts",
        text="Custom text",
        reference_audio_base64=audio_b64,
        language="en"
    )
)
```

#### ASRProviderService
**Purpose**: Speech-to-text with multiple provider support

**Supported Providers**:
- OpenAI Whisper (multiple sizes: base, medium, large-v3)
- Google Speech-to-Text
- Assembly AI
- Deepgram
- DeepSeek Whisper

**Usage**:
```python
from apps.shared.services.asr_provider_service import (
    ASRProviderService,
    TranscriptionRequest
)

asr = ASRProviderService()
result = await asr.transcribe(
    user_id="user_123",
    request=TranscriptionRequest(
        provider_id="whisper_large_v3",
        audio_base64="...",
        language="en"  # Optional, auto-detects if None
    )
)
# Returns: {transcription, language, confidence, duration, cost}
```

#### VoiceLabService
**Purpose**: Generic voice operations (ASR/TTS/chat)

**Usage**:
```python
from apps.shared.services.voice_lab_service import VoiceLabService

voice_lab = VoiceLabService()
await voice_lab.initialize()

# Direct ASR call
transcription = await voice_lab.transcribe_audio(audio_bytes, language="en")

# Direct TTS call
audio = await voice_lab.synthesize_speech(text, voice_id, language="en")

# Voice chat
response = await voice_lab.voice_chat(
    user_input_audio, 
    system_prompt="Be helpful and concise"
)
```

### 2.2 Low-Level AI Services Infrastructure

#### Provider Registry
**Purpose**: Centralized configuration management for all AI providers

**Location**: `/opt/kasaai/apps/shared/integration/ai_services/provider_registry.py`

**Provides**:
- Provider discovery and registration
- Health monitoring
- Environment-based configuration
- Provider capabilities metadata

#### VAD Service (Voice Activity Detection)
**Purpose**: Real-time voice detection using Silero model

**Features**:
- Enterprise-grade VAD
- < 1ms per 30ms chunk processing
- Automatic utterance segmentation
- Session management for multi-turn conversations
- Natural conversation flow

**Usage**:
```python
from apps.shared.integration.ai_services.vad_service import (
    VoiceActivityDetector,
    VADSession
)

detector = VoiceActivityDetector(
    sample_rate=16000,
    threshold=0.5,
    min_speech_duration_ms=250,
    min_silence_duration_ms=1500
)

session = VADSession("user_123")
session.start_listening()

# Process audio chunks (16kHz PCM)
is_speech, complete, audio = session.process_chunk(pcm_samples)

if complete:
    # Utterance finished, transcribe with ASR
    transcription = await asr_service.transcribe(audio)
```

#### TTS Service (Low-level)
**Location**: `/opt/kasaai/apps/shared/integration/ai_services/tts_service.py`

**Provides**: Direct provider access without billing layer

#### STT Service (Low-level)
**Location**: `/opt/kasaai/apps/shared/integration/ai_services/stt_service.py`

**Provides**: Direct speech-to-text access

### 2.3 Voice Engine (WebRTC & Telephony)

#### WebRTC Bridge
**Purpose**: Real-time browser-to-voice service communication

**Location**: `/opt/kasaai/apps/shared/voice_engine/webrtc_bridge.py`

**Provides**:
- Browser audio capture
- Real-time streaming
- Echo cancellation
- Automatic gain control

#### Outbound Call Manager
**Purpose**: Initiate and manage outbound voice calls via VAPI

**Location**: `/opt/kasaai/apps/shared/voice_engine/outbound_call.py`

**Usage**:
```python
from apps.shared.voice_engine import OutboundCallManager

manager = OutboundCallManager(vapi_key="...")
call = await manager.initiate_call(
    phone_number="+1234567890",
    system_prompt="You are a helpful assistant",
    first_message="Hello, how can I help?"
)
```

### Voice Services Summary

| Service | Purpose | Reusability | Billing |
|---------|---------|-------------|---------|
| **ConversationalVoiceService** | Full voice chat with RAG | HIGH - use directly | Auto |
| **TTSProviderService** | Text-to-speech | HIGH - use directly | Auto |
| **ASRProviderService** | Speech-to-text | HIGH - use directly | Auto |
| **VoiceLabService** | Generic voice ops | HIGH - use directly | Auto |
| **VADService** | Voice activity detection | HIGH - low-level | None |
| **WebRTC Bridge** | Browser voice capture | MEDIUM - integrate | None |
| **Outbound Call Manager** | VAPI integration | MEDIUM - extend | Auto |

### Reusability for B2C Portal
✅ **HIGH REUSABILITY** - These are production-ready services designed for multi-app use:
```python
# Import and use directly
from apps.shared.services.conversational_voice_service import ConversationalVoiceService
from apps.shared.services.tts_provider_service import TTSProviderService
from apps.shared.services.asr_provider_service import ASRProviderService
```

---

## 3. RETRIEVAL-AUGMENTED GENERATION (RAG)

### Location
- `/opt/kasaai/apps/shared/integration/rag.py`

### Purpose
Generic RAG service for semantic search and LLM Q&A with document knowledge bases

### Architecture
```
Documents → Text Splitting → Embeddings (pgvector) → LangChain Retriever
                                                          ↓
                                                    LLM Chain
                                                          ↓
                                                    Q&A Response
```

### Key Components

#### RAGConfig
```python
class RAGConfig(BaseModel):
    # PostgreSQL with pgvector
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "kasaai_core"
    
    # AI Provider (openai, gemini, anthropic)
    ai_provider: str = "openai"
    api_key: str
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    
    # RAG parameters
    chunk_size: int = 1000
    retrieval_k: int = 3  # Top-k documents
    similarity_threshold: float = 0.3
    confidence_threshold: float = 0.7
    temperature: float = 0.1
```

#### RAGService Methods
```python
async def index_documents(collection_name, documents: List[KnowledgeDocument])
    # Index documents with embeddings

async def query(collection_name, query_text, filters=None) -> QueryResult
    # Semantic search + LLM Q&A
    # Returns: {success, response, confidence_score, sources_used, escalation_required}

async def delete_documents(collection_name, document_ids)
    # Remove documents from knowledge base

async def get_collection_stats(collection_name)
    # Get collection metadata
```

### Usage Example
```python
from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument

config = RAGConfig(
    postgres_password="...",
    ai_provider="openai",
    api_key="sk-..."
)

rag = RAGService(config)

# Index documents
await rag.index_documents("kasaai_faq", [
    KnowledgeDocument(
        title="What is KasaAI?",
        content="KasaAI is an AI platform...",
        category="FAQ",
        tags=["general", "info"]
    )
])

# Query
result = await rag.query("kasaai_faq", "What is KasaAI?")
# Returns: {success: True, response: "...", confidence_score: 0.95, ...}
```

### Reusability for B2C Portal
✅ **READY TO USE** - Perfect for building chatbots with company knowledge:
```python
from apps.shared.integration.rag import RAGService, RAGConfig

# Initialize once per app startup
rag_service = RAGService(RAGConfig(...))

# Use in routes/services
result = await rag_service.query("b2c_knowledge_base", user_query)
```

---

## 4. AI SERVICE INTEGRATIONS

### Location
- `/opt/kasaai/apps/shared/services/llm_provider_service.py`
- `/opt/kasaai/apps/shared/integration/gemini_service.py`

### LLM Provider Service
**Purpose**: Multi-provider LLM orchestration

**Supported Providers**:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Google Gemini (Pro, Pro Vision)
- Anthropic Claude (3 Opus, Sonnet, Haiku)
- Mistral (Large, Medium, Small)

**Usage**:
```python
from apps.shared.services.llm_provider_service import LLMProviderService

llm = LLMProviderService()

result = await llm.call(
    provider="openai",
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)
```

### Gemini Service
**Purpose**: Direct Google Gemini integration

**Features**:
- Vision capabilities
- Extended context windows
- JSON output mode

---

## 5. PAYMENT & BILLING INTEGRATIONS

### Location
- `/opt/kasaai/apps/shared/integration/wallet/`
- `/opt/kasaai/apps/shared/services/billing_service.py`

### Wallet System
**Purpose**: Multi-provider wallet with fraud detection and notifications

**Supported Providers**:
- Stripe (payment processing)
- Flutterwave (African payments)
- Paystack (Nigerian payments)
- M-Pesa (Mobile money)

**Key Features**:
- Credit/debit wallet
- Transaction history
- Fraud detection
- Webhook handling
- Notifications (email, SMS, push)

**Usage**:
```python
from apps.shared.integration.wallet import WalletService

wallet = WalletService()

# Get balance
balance = await wallet.get_balance(user_id)

# Create transaction
transaction = await wallet.create_transaction(
    user_id=user_id,
    amount=100.00,
    currency="USD",
    description="TTS synthesis"
)

# Process payment
result = await wallet.process_payment(
    user_id=user_id,
    amount=50.00,
    provider="stripe",
    payment_method_id="pm_..."
)
```

### Payment Integrations
**Location**: `/opt/kasaai/apps/shared/integration/`

**Providers**:
- `stripe.py` - Stripe (global)
- `flutterwave.py` - Flutterwave (African)
- `paystack.py` - Paystack (Nigeria/Ghana)
- `mtn_mobile_money.py` - MTN Mobile Money
- `ghana_interbank.py` - Ghana Interbank

### Reusability for B2C Portal
✅ **READY TO USE** - Integrate wallet for service billing:
```python
from apps.shared.integration.wallet import WalletService
from apps.shared.services.billing_service import BillingService
```

---

## 6. COMMUNICATION INTEGRATIONS

### Location
- `/opt/kasaai/apps/shared/integration/` (50+ files)

### Email
**Providers**: SMTP, SendGrid, Resend

**Usage**:
```python
from apps.shared.integration.email import EmailIntegration

email = EmailIntegration(config)
await email.send_email(
    to="user@example.com",
    subject="Welcome",
    body="Hello!",
    html_body="<h1>Hello!</h1>"
)
```

### SMS
**Providers**: Twilio, MessageBird, Vonage

**Usage**:
```python
from apps.shared.integration.sms import SMSIntegration

sms = SMSIntegration(config)
await sms.send_sms(
    to="+1234567890",
    message="Your code is 123456",
    from_number="+0987654321"
)
```

### WhatsApp Business
**Features**:
- Template messages
- Media sharing
- Interactive buttons

**Usage**:
```python
from apps.shared.integration.whatsapp_business import WhatsAppIntegration

wa = WhatsAppIntegration(config)
await wa.send_template_message(
    template_name="welcome",
    to="1234567890",
    variables={"name": "John"}
)
```

### CRM Integrations
- HubSpot, Freshdesk, Freshsales, Pipedrive, Salesforce, Zendesk, Intercom

### Productivity
- Google Workspace (Sheets, Docs, Calendar)
- Microsoft 365
- Slack
- Confluence
- Notion

### Data & Analytics
- Google Analytics
- Mixpanel
- Grafana
- Prometheus

---

## 7. SERVICES LAYER (34 Total)

### Location
- `/opt/kasaai/apps/shared/services/`

### High-Level Services

| Service | Purpose | Key Method |
|---------|---------|-----------|
| **TTS Provider** | Voice synthesis (11 providers) | `synthesize()` |
| **ASR Provider** | Speech-to-text | `transcribe()` |
| **LLM Provider** | Multi-LLM orchestration | `call()` |
| **PDF Extraction** | Receipt/invoice OCR | `extract_from_pdf()` |
| **File Upload** | Cloud storage (Hetzner) | `upload_file()` |
| **Email Account** | iRedMail automation | `create_account()` |
| **Billing** | Cost tracking & invoicing | `calculate_cost()` |
| **Organization** | Tenant management | `create_org()` |
| **Voice Lab** | Generic voice operations | `transcribe_audio()` |
| **Prompt Validation** | Input safety checks | `validate()` |
| **Drive** | Google Drive integration | `upload_file()` |
| **Certificate** | Credentials & validation | `validate_certificate()` |
| **QR Code** | QR generation & scanning | `generate_qr()` |
| **Web Scraper** | Content extraction | `scrape()` |
| **Audio Conversion** | Format conversion | `convert()` |
| **Alert** | Notification system | `send_alert()` |
| **Export** | Data export (CSV, JSON) | `export_data()` |
| **Gamification** | Points & badges | `award_points()` |
| **Linear** | Linear issue tracking | `create_issue()` |
| **Unified Email** | Multi-provider email | `send_email()` |
| **Unified Analytics** | Cross-app analytics | `track_event()` |
| **Conversational Voice** | Voice chat with RAG | `process_voice_message()` |
| **Conversational Assessment** | AI-powered assessments | `evaluate()` |
| **Audio Validation** | Audio quality checks | `validate_audio()` |
| **Voice Library** | Voice collection mgmt | `list_voices()` |
| **TTS WebUI** | RunPod TTS interface | `synthesize()` |
| **Bug Report** | Bug tracking | `report_bug()` |
| **Init Voice Indexes** | Vector index setup | `initialize()` |

### Reusability for B2C Portal
✅ **EXTENSIVE** - Pick services as needed:
```python
# Import what you need
from apps.shared.services.tts_provider_service import TTSProviderService
from apps.shared.services.asr_provider_service import ASRProviderService
from apps.shared.services.llm_provider_service import LLMProviderService
from apps.shared.services.pdf_extraction_service import PDFExtractionService
from apps.shared.services.file_upload_service import FileUploadService
from apps.shared.services.billing_service import BillingService
from apps.shared.services.organization_service import OrganizationService
```

---

## 8. INDUSTRY MODULES

### Location
- `/opt/kasaai/apps/shared/modules/`

### 13 Available Modules

Each module provides:
- **Capabilities** - Domain operations (methods)
- **Workflows** - Automation sequences
- **Integration Points** - External system connections
- **Compliance** - Industry standards

**Modules**:
1. **Healthcare** - HIPAA-compliant patient & appointment mgmt
2. **Finance** - PCI-DSS banking & loan management
3. **Retail** - Inventory, orders, customer analytics
4. **Manufacturing** - Production, QA, supply chain
5. **Logistics** - Fleet, routes, delivery tracking
6. **Telecom** - Calls, customers, billing
7. **Insurance** - Claims, policies, underwriting
8. **Real Estate** - Properties, tenants, maintenance
9. **Education** - Students, courses, enrollment
10. **Professional Services** - Cases, projects, billing
11. **Automotive** - Vehicles, service, sales
12. **Hospitality** - Rooms, guests, bookings
13. **Government** - Citizens, permits, services
14. **Utilities** - Meters, billing, outages

### Usage Example
```python
from apps.shared.modules.factory import create_module

# Create a healthcare module for your tenant
healthcare = create_module("healthcare", tenant_id="tenant_123")

# Initialize
await healthcare.initialize(tenant_id, {
    "ehr_system": "epic",
    "compliance_level": "hipaa"
})

# Execute capability
result = await healthcare.execute_capability("schedule_appointment", {
    "patient_id": "p_123",
    "doctor_id": "d_456",
    "date": "2024-12-15",
    "time": "14:30"
})

# Execute workflow
workflow_result = await healthcare.execute_workflow("appointment_reminder_workflow", {
    "patient_id": "p_123",
    "appointment_id": "apt_789"
})
```

### Reusability for B2C Portal
⚠️ **MEDIUM** - Modules are domain-specific. Use only if B2C serves specific industries:
```python
# Example: If B2C supports education customers
from apps.shared.modules.education import EducationModule
```

---

## 9. FRONTEND COMPONENTS & HOOKS

### Location
- `/opt/kasaai/apps/shared/frontend/`

### React Components

#### Voice Settings Panel
**Component**: `VoiceSettingsPanel.tsx`

**Props**:
- `onSettingsChange?: (settings) => void`
- `initialSettings?: VoiceSettings`

**Features**:
- ASR provider selector
- TTS provider selector
- LLM model selector
- Voice library selector
- Voice upload/management

**Usage**:
```tsx
import { VoiceSettingsPanel } from '@shared/frontend/components/voice-settings';

export function MyVoiceSettings() {
  return (
    <VoiceSettingsPanel
      onSettingsChange={(settings) => console.log(settings)}
    />
  );
}
```

#### ASR Provider Selector
**Component**: `ASRProviderSelector.tsx`

**Features**:
- List available STT providers
- Language selection
- Model selection

#### TTS Provider Selector
**Component**: `TTSProviderSelector.tsx`

**Features**:
- List available TTS providers
- Voice selection
- Speed/pitch controls

#### Voice Library Selector
**Component**: `VoiceLibrarySelector.tsx`

**Features**:
- Browse available voices
- Voice preview
- Voice details

#### Voice Upload Modal
**Component**: `VoiceUploadModal.tsx`

**Features**:
- Audio file upload
- Voice registration
- Quality validation

#### Admin Components
- `OrganizationManagement.tsx` - Org settings
- `UserManagement.tsx` - User admin
- `AdminLayout.tsx` - Layout wrapper
- `OrganizationBilling.tsx` - Billing dashboard

### Custom Hooks

#### useVoiceSettings
```typescript
const { settings, updateSettings, isLoading } = useVoiceSettings(orgId);

// Get current settings
const asr_provider = settings.asr_provider;

// Update settings
await updateSettings({ tts_provider: "coqui_xtts" });
```

#### useASRProvider
```typescript
const { providers, selectedProvider, setProvider } = useASRProvider();

// List available ASR providers
providers.forEach(p => console.log(p.id, p.name));
```

#### useTTSProvider
```typescript
const { providers, selectedProvider, synthesize } = useTTSProvider();

// Synthesize text
const audio = await synthesize("Hello world", { voice_id: "nova" });
```

#### useLLMModel
```typescript
const { models, selectedModel, setModel } = useLLMModel();
```

#### useClonedVoices
```typescript
const { voices, addVoice, deleteVoice } = useClonedVoices(userId);
```

### Reusability for B2C Portal
✅ **HIGH** - Import and customize:
```tsx
import { VoiceSettingsPanel } from '@shared/frontend/components/voice-settings';
import { OrganizationManagement } from '@shared/frontend/admin-components';
import { useVoiceSettings } from '@shared/frontend/hooks';
```

---

## 10. MODELS & DATA STRUCTURES

### Location
- `/opt/kasaai/apps/shared/models/`

### Key Models

#### Organization
```python
class Organization(BaseModel):
    id: str
    name: str  # Unique identifier
    display_name: str
    description: Optional[str]
    
    # Billing
    subscription_tier: str  # free, pro, enterprise
    wallet_balance: float
    
    # Branding
    logo_url: Optional[str]
    primary_color: Optional[str]
    
    # Modules & Features
    enabled_modules: List[str]
    feature_flags: Dict[str, bool]
    
    # Settings
    settings: Dict[str, Any]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
```

#### Assessment Models
**Location**: `/opt/kasaai/apps/shared/models/assessment_models.py`

**Purpose**: AI-powered assessment definitions and results

**Models**:
- `AssessmentQuestion` - Question with options
- `AssessmentResult` - Student answers & scoring
- `AssessmentMetrics` - Performance analysis

### Reusability for B2C Portal
✅ **READY TO USE** - Extend as needed:
```python
from apps.shared.models.organization import Organization
from apps.shared.models.assessment_models import AssessmentResult
```

---

## 11. MIDDLEWARE & SECURITY

### Location
- `/opt/kasaai/apps/shared/middleware/`
- `/opt/kasaai/apps/shared/security/`

### Middleware
- **CORS** - Cross-origin request handling
- **Rate Limiting** - Request throttling
- **Logging** - Request/response logging
- **Error Handling** - Standardized error responses

### Security
- **JWT Validation** - Token verification
- **HTTPS** - SSL/TLS enforcement
- **API Key Management** - Credential handling
- **Input Validation** - Pydantic models

### Reusability for B2C Portal
✅ **USE DIRECTLY** - FastAPI integrations:
```python
from apps.shared.middleware import setup_cors, setup_rate_limiting
```

---

## 12. CONFIGURATION & ENVIRONMENT

### Location
- `/opt/kasaai/apps/shared/config/`

### Environment Variables
```bash
# Authentication
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=...
SUPABASE_KEY=...

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_PASSWORD=...
MONGODB_URI=mongodb://...

# Voice Services
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
ELEVENLABS_API_KEY=...

# Payment
STRIPE_API_KEY=...
FLUTTERWAVE_KEY=...

# Storage
HETZNER_USER=...
HETZNER_PASSWORD=...
```

---

## 13. TESTING & QUALITY ASSURANCE

### Location
- `/opt/kasaai/apps/shared/tests/`

### Test Structure
```
tests/
├── test_tts.py - TTS provider tests
├── test_vapi_webhook.py - VAPI webhook tests
├── integration/
│   └── (integration tests)
└── multi_app/
    └── (multi-app scenario tests)
```

### Running Tests
```bash
# All tests
pytest /opt/kasaai/apps/shared/tests/

# Specific test
pytest /opt/kasaai/apps/shared/tests/test_tts.py -v

# With coverage
pytest --cov=shared /opt/kasaai/apps/shared/tests/
```

---

## ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                      B2C Portal (New)                        │
│  (FastAPI routes, React frontend, business logic)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   Shared Library (@apps/shared/)   │
        │   Production-Ready Services        │
        └────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌────────┐   ┌────────────┐   ┌──────────┐
    │Services│   │Integrations│   │  Modules │
    └────────┘   └────────────┘   └──────────┘
        │            │                   │
    TTS │        Email  │          Healthcare │
    ASR │        SMS    │          Finance    │
    LLM │        Stripe │          Education │
    PDF │        RAG    │          ...       │
        │        ...    │
        │
        ▼                ▼                ▼
    ┌────────────────────────────────────────┐
    │     External Services & Databases       │
    │  (Supabase, PostgreSQL, MongoDB, etc.)  │
    └────────────────────────────────────────┘
```

---

## 14. QUICK START FOR B2C PORTAL

### 1. Authentication
```python
from apps.shared.auth.supabase_auth import get_current_user
from fastapi import Depends

@router.get("/protected")
async def protected(user: dict = Depends(get_current_user)):
    return {"user_id": user["id"]}
```

### 2. Voice Capabilities
```python
from apps.shared.services.conversational_voice_service import ConversationalVoiceService

voice_service = ConversationalVoiceService()
await voice_service.initialize()

# Use in your routes
```

### 3. LLM Integration
```python
from apps.shared.services.llm_provider_service import LLMProviderService

llm = LLMProviderService()
response = await llm.call(
    provider="openai",
    model="gpt-4o",
    messages=[...]
)
```

### 4. Payment Processing
```python
from apps.shared.integration.wallet import WalletService

wallet = WalletService()
transaction = await wallet.create_transaction(user_id, amount, "USD")
```

### 5. Email/SMS
```python
from apps.shared.integration.email import EmailIntegration
from apps.shared.integration.sms import SMSIntegration

email = EmailIntegration(config)
await email.send_email(to, subject, body)

sms = SMSIntegration(config)
await sms.send_sms(to, message)
```

### 6. Frontend Components
```tsx
import { VoiceSettingsPanel } from '@shared/frontend/components/voice-settings';
import { useVoiceSettings } from '@shared/frontend/hooks';
```

---

## 15. IMPLEMENTATION CHECKLIST FOR B2C PORTAL

### Must Use (Foundation)
- [ ] Supabase authentication (`get_current_user`)
- [ ] Organization model for multi-tenancy
- [ ] Wallet system for billing

### Should Use (Voice)
- [ ] ConversationalVoiceService for chat
- [ ] TTSProviderService for voice output
- [ ] ASRProviderService for voice input
- [ ] RAGService for knowledge base

### Consider Using (Enhancement)
- [ ] Email/SMS for notifications
- [ ] LLM Provider for AI features
- [ ] PDF extraction for document processing
- [ ] File upload for media management

### Don't Need
- [ ] Industry modules (unless B2C serves specific sectors)
- [ ] Low-level AI services (use high-level services instead)

---

## 16. FILE LOCATIONS REFERENCE

### Key Files
- **Authentication**: `/opt/kasaai/apps/shared/auth/supabase_auth.py`
- **Voice Services**: `/opt/kasaai/apps/shared/services/conversational_voice_service.py`
- **TTS**: `/opt/kasaai/apps/shared/services/tts_provider_service.py`
- **ASR**: `/opt/kasaai/apps/shared/services/asr_provider_service.py`
- **RAG**: `/opt/kasaai/apps/shared/integration/rag.py`
- **Organization**: `/opt/kasaai/apps/shared/models/organization.py`
- **Wallet**: `/opt/kasaai/apps/shared/integration/wallet/wallet_service.py`
- **Email**: `/opt/kasaai/apps/shared/integration/email.py`
- **Integrations**: `/opt/kasaai/apps/shared/integration/` (50+ files)
- **Frontend**: `/opt/kasaai/apps/shared/frontend/`
- **Tests**: `/opt/kasaai/apps/shared/tests/`

### Documentation
- **Quick Reference**: `/opt/kasaai/apps/shared/QUICK_REFERENCE.md`
- **Main README**: `/opt/kasaai/apps/shared/README.md`
- **Integration Guide**: `/opt/kasaai/apps/shared/INTEGRATION_GUIDE.md`
- **Organization System**: `/opt/kasaai/apps/shared/ORGANIZATION_SYSTEM.md`

---

## CONCLUSION

The shared library is **mature, comprehensive, and production-ready**. It provides:

✅ **Unified authentication** across all apps  
✅ **34 high-level business services** ready to use  
✅ **50+ integrations** to external systems  
✅ **Complete voice pipeline** (ASR, TTS, RAG, chat)  
✅ **Multi-tenant organization system** with billing  
✅ **Reusable React components** and TypeScript hooks  
✅ **Extensive documentation** and examples  

**Recommendation**: The B2C Portal should heavily leverage these components rather than reimplementing them. This ensures consistency across the platform and reduces development time significantly.

---

**End of Report**

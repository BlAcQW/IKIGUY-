# KasaAI Shared Library - Comprehensive Exploration Report

**Generated**: 2025-11-06  
**Location**: `/opt/kasaai/apps/shared/`  
**Status**: Production-Ready  

---

## Executive Summary

The KasaAI Shared Library is a comprehensive, modular platform providing:
- **13 Industry-Specific Modules** (Healthcare, Finance, Retail, Manufacturing, Logistics, Telecom, Insurance, Real Estate, Education, Professional Services, Automotive, Hospitality, Utilities, Government)
- **50+ Integration Services** (Email, SMS, WhatsApp, Google Workspace, Stripe, Zendesk, HubSpot, Zapier, etc.)
- **Core Platform Services** (Authentication, File Upload, PDF Extraction, TTS, ASR, Email Management, Billing, Analytics)
- **Unified Wallet & Billing System** with support for multiple currencies (GHS, USD, EUR, GBP, NGN, KES, ZAR)
- **RAG Service** for semantic search and AI-powered Q&A across knowledge bases
- **Advanced Frontend Components** (React, TypeScript) for admin interfaces and shared UI

All components follow consistent patterns and are designed for **multi-tenant** deployment across all KasaAI applications.

---

## Directory Structure

```
shared/
├── services/                          # High-level business services
│   ├── tts_provider_service.py       # Text-to-speech (10 providers, billing)
│   ├── llm_provider_service.py       # LLM orchestration (Gemini, OpenAI, etc.)
│   ├── voice_lab_service.py          # Voice operations (ASR, TTS, Chat)
│   ├── pdf_extraction_service.py     # Receipt/invoice extraction with OCR
│   ├── file_upload_service.py        # Cloud storage (Hetzner Storage Box)
│   ├── email_account_service.py      # iRedMail email account management
│   ├── tts_health_notifier.py        # TTS provider health monitoring
│   ├── billing_service.py            # Billing and usage tracking
│   ├── asr_provider_service.py       # Speech-to-text providers
│   ├── organization_service.py       # Organization management
│   ├── alert_service.py              # Alert and notification system
│   └── [20+ more services]           # Export, Analytics, Voice Settings, etc.
│
├── integration/                       # External service integrations
│   ├── ai_services/                  # AI provider orchestration
│   │   ├── provider_registry.py      # Registry for 10+ TTS/LLM providers
│   │   ├── health_monitor_service.py # Provider health checks
│   │   ├── ai_provider_service.py    # Multi-provider LLM interface
│   │   ├── tts_service.py            # TTS orchestration
│   │   ├── stt_service.py            # Speech-to-text orchestration
│   │   └── tests/                    # Contract, integration, E2E tests
│   │
│   ├── wallet/                       # Wallet and billing system
│   │   ├── __init__.py              # 199 lines - wallet service implementation
│   │   ├── providers/               # Payment provider integrations
│   │   └── tests/                   # Comprehensive wallet tests
│   │
│   ├── [Email Services]
│   │   ├── email.py                 # SMTP, SendGrid, Resend (1372 lines)
│   │   ├── sms.py                   # Twilio, MessageBird SMS
│   │   ├── sms_providers.py         # SMS provider implementations
│   │   ├── whatsapp_business.py     # WhatsApp Business API
│   │   └── whatsapp.py              # WhatsApp integration
│   │
│   ├── [Business Systems]
│   │   ├── stripe.py                # Stripe payments
│   │   ├── flutterwave.py           # African payments (Ghana)
│   │   ├── paystack.py              # Paystack payments
│   │   ├── financial_systems.py     # ERP systems (Fiserv, FIS, Jack Henry)
│   │   ├── healthcare_systems.py    # EHR systems (Epic, Cerner, Allscripts)
│   │   └── ghana_interbank.py       # Ghana Interbank Connect
│   │
│   ├── [CRM & Business Tools]
│   │   ├── freshdesk.py             # Freshdesk support tickets
│   │   ├── freshsales.py            # Freshsales CRM
│   │   ├── hubspot.py               # HubSpot CRM integration
│   │   ├── pipedrive.py             # Pipedrive sales pipeline
│   │   ├── salesforce.py            # Salesforce integration
│   │   ├── zendesk.py               # Zendesk helpdesk
│   │   └── intercom.py              # Intercom chat
│   │
│   ├── [Productivity & Automation]
│   │   ├── google_workspace.py      # Google Sheets, Calendar, Docs
│   │   ├── google_drive.py          # Google Drive storage
│   │   ├── microsoft_365.py         # Office 365, Teams, SharePoint
│   │   ├── confluence.py            # Atlassian Confluence
│   │   ├── notion.py                # Notion databases
│   │   ├── zapier.py                # Zapier automation
│   │   ├── make.py                  # Make.com automation
│   │   ├── calendly.py              # Calendly scheduling
│   │   └── discord.py               # Discord webhooks
│   │
│   ├── [Data & Knowledge]
│   │   ├── rag.py                   # RAG service (pgvector semantic search)
│   │   ├── document_processor.py    # PDF, DOCX extraction
│   │   ├── firecrawl.py             # Web scraping
│   │   ├── tavily.py                # Web search
│   │   ├── brave.py                 # Brave search integration
│   │   └── google_analytics.py      # Analytics integration
│   │
│   ├── [Database & Storage]
│   │   ├── mongodb.py               # MongoDB operations
│   │   ├── supabase.py              # Supabase client
│   │   ├── supabase_admin.py        # Supabase admin API
│   │   └── supabase_mcp_server.py   # MCP server interface
│   │
│   ├── [Monitoring & Logging]
│   │   ├── prometheus.py            # Prometheus metrics
│   │   ├── grafana.py               # Grafana dashboards
│   │   └── analytics_service.py     # Analytics backend
│   │
│   ├── usage_calculator.py          # Cost & usage calculation
│   ├── cost_tracker_factory.py      # Cost tracking factory
│   ├── gemini_service.py            # Google Gemini LLM
│   ├── integration_manager.py       # Integration orchestration (994 lines)
│   ├── types.py                     # Integration type definitions
│   └── tests/                       # Integration test suite
│
├── modules/                          # Industry-specific modules
│   ├── base.py                       # Base module class
│   ├── workflow.py                   # Automation workflow engine
│   ├── factory.py                    # Module factory pattern
│   ├── api.py                        # Standardized API endpoints
│   │
│   ├── [Healthcare]
│   │   └── healthcare.py             # Patient management, appointments, HIPAA
│   │
│   ├── [Finance]
│   │   └── financial.py              # Banking, loans, transactions, PCI-DSS
│   │
│   ├── [Retail]
│   │   └── retail.py                 # Inventory, orders, loyalty programs
│   │
│   ├── [Manufacturing]
│   │   └── manufacturing.py          # Production, QA, supply chain
│   │
│   ├── [Logistics & Transportation]
│   │   └── logistics.py              # Fleet, delivery, tracking
│   │
│   ├── [Telecom]
│   │   └── telecom.py                # Call management, customer support
│   │
│   ├── [Insurance]
│   │   └── insurance.py              # Claims, policies, coverage
│   │
│   ├── [Real Estate]
│   │   └── real_estate.py            # Properties, tenants, maintenance
│   │
│   ├── [Education]
│   │   └── education.py              # Students, courses, grading
│   │
│   ├── [Professional Services]
│   │   └── professional_services.py  # Legal, consulting, projects
│   │
│   ├── [Automotive]
│   │   └── automotive.py             # Vehicles, service, sales
│   │
│   ├── [Hospitality]
│   │   └── hospitality.py            # Rooms, guests, bookings
│   │
│   ├── [Utilities]
│   │   └── utilities.py              # Meters, billing, outages
│   │
│   └── [Government]
│       └── government.py             # Citizens, permits, services
│
├── auth/                             # Authentication
│   ├── supabase_auth.py             # Supabase JWT authentication
│   ├── DEFAULT_USERS.md             # Default test users
│   └── README.md                     # Auth documentation
│
├── storage/                          # Data storage backends
│   ├── hetzner_storage_box.py       # Hetzner cloud storage (SFTP)
│   ├── redis.py                     # Redis cache
│   ├── postgres.py                  # PostgreSQL backend
│   ├── memory.py                    # In-memory storage
│   ├── interfaces.py                # Storage interface definitions
│   ├── voice_clones/                # Voice cloning storage
│   ├── voice_samples/               # Voice sample storage
│   └── HETZNER_STORAGE_BOX.md       # Storage documentation
│
├── frontend/                         # Shared React/TypeScript components
│   ├── components/                  # Reusable UI components
│   ├── admin-components/            # Admin dashboard components
│   ├── hooks/                       # React custom hooks
│   ├── services/                    # Frontend API services
│   ├── types/                       # TypeScript type definitions
│   ├── tests/                       # Component tests
│   ├── package.json                 # Dependencies
│   └── README.md                    # Frontend docs
│
├── config/                          # Configuration management
│   ├── engine.py                    # Configuration engine
│   ├── models.py                    # Config models
│   ├── interfaces.py                # Config interfaces
│   └── module_system.py             # Module system config
│
├── middleware/                      # Express/FastAPI middleware
│   ├── organization_context.py      # Multi-tenant context middleware
│   └── __init__.py
│
├── dependencies/                    # FastAPI dependency injection
│   ├── auth.py                      # Auth dependencies
│   └── __init__.py
│
├── models/                          # Data models
│   ├── organization.py              # Organization models
│   └── __init__.py
│
├── voice-engine/                    # Voice processing
│   ├── backend/                     # Backend voice implementation
│   │   └── sip_manager.py           # SIP call management
│   └── [Other voice components]
│
├── security/                        # Security features
│   ├── engine.py                    # Security engine
│   ├── interfaces.py                # Security interfaces
│   └── __init__.py
│
├── monitoring/                      # System monitoring
│   ├── engine.py                    # Monitoring engine
│   ├── interfaces.py                # Monitoring interfaces
│   └── __init__.py
│
├── license/                         # License management
│   ├── engine.py                    # License validation
│   ├── models.py                    # License models
│   ├── interfaces.py                # License interfaces
│   └── __init__.py
│
├── events/                          # Event system
│   ├── models.py                    # Event models
│   ├── interfaces.py                # Event interfaces
│   └── __init__.py
│
├── usage/                           # Usage tracking
│   └── [Usage tracking components]
│
├── ai/                              # AI utilities
│   ├── ghanaian_error_handler.py    # Error handling
│   ├── ghanaian_sentiment_analyzer.py
│   ├── ghanaian_intent_detector.py
│   ├── ghanaian_ner_analyzer.py     # Named entity recognition
│   ├── ghanaian_model_finetuner.py  # Model fine-tuning
│   ├── ghanaian_offline_processor.py
│   ├── ghanaian_e2e_tester.py       # End-to-end testing
│   ├── ghanaian_performance_benchmark.py
│   └── ai_powered_features.py
│
├── analytics/                       # Business intelligence
│   ├── predictive_analytics.py      # Forecasting
│   ├── business_intelligence.py     # BI tools
│   └── __init__.py
│
├── speech/                          # Speech processing
│   ├── real_time_processor.py       # Real-time speech
│   ├── code_switch.py               # Language code-switching
│   └── __init__.py
│
├── telephony/                       # Telephony adapters
│   └── adapters/                    # Provider adapters
│
├── tts/                             # Text-to-speech utilities
│   └── [TTS utilities]
│
├── tenant/                          # Multi-tenant support
│   └── [Tenant utilities]
│
├── utils/                           # General utilities
│   └── [Utility functions]
│
├── docs/                            # Documentation
│   └── [Documentation files]
│
├── tests/                           # Test suite
│   └── [Test files]
│
├── README.md                        # Main documentation
├── INTEGRATION_GUIDE.md             # Integration patterns
├── ORGANIZATION_SYSTEM.md           # Organization management
├── ORGANIZATION_IMPLEMENTATION_SUMMARY.md
├── GEMINI_LLM_INTEGRATION.md        # Gemini setup
├── GEMINI_COMPREHENSIVE_TEST_REPORT.md
├── MOBILE_RECEIPT_UPLOAD.md         # Mobile upload guide
└── setup.py                         # Package setup
```

---

## Core Components & Services

### 1. **TTS Provider Service** (`services/tts_provider_service.py`)

**Purpose**: Centralized text-to-speech with automatic billing and provider management

**Supported Providers** (10):
- **Coqui XTTS** - Voice cloning, multilingual (17 languages), speed control
- **MeloTTS** - Fast synthesis, pitch control, multilingual (6 languages)
- **F5-TTS** - Premium voice cloning, 4 languages
- **StyleTTS2** - Premium emotion control, English only
- **OpenVoice** - Voice cloning with pitch/emotion, EN/ZH
- **Kokoro** - Fast and natural English synthesis
- **Moshi** - Conversational TTS
- **Akan MMS** - Native Twi language support
- **Crawl4AI** - Web scraping TTS
- Plus OpenAI, Google, etc.

**Key Features**:
- Automatic cost calculation and wallet deduction
- Provider health monitoring
- Voice cloning support
- Request/response normalization
- Multi-language and multi-speaker support
- Cost model: $0.015 per 1000 chars + $0.05 voice cloning premium

**Usage Pattern**:
```python
from apps.shared.services.tts_provider_service import TTSProviderService
tts = TTSProviderService()
await tts.initialize()
result = await tts.synthesize(user_id, request)
```

---

### 2. **PDF Extraction Service** (`services/pdf_extraction_service.py`)

**Purpose**: Extract structured data from expense receipts and invoices

**Features**:
- Text-based extraction (pdfplumber)
- OCR support for scanned documents (Tesseract)
- Pattern matching for receipt formats
- Confidence scoring
- Multi-currency support (USD, GHS, EUR, GBP, NGN, ZAR)

**Extracted Fields**:
- Merchant/vendor name
- Transaction date
- Total amount & tax
- Currency
- Category (AI-inferred)
- Payment method
- Receipt number

---

### 3. **File Upload Service** (`services/file_upload_service.py`)

**Purpose**: Handle file uploads to cloud storage

**Storage Options**:
- **Primary**: Hetzner Storage Box (SFTP)
- **Fallback**: Local filesystem

**Supported File Types**:
- Documents: PDF, DOC, DOCX, TXT, CSV (25-50MB)
- Images: JPEG, PNG, GIF, WebP (10MB)
- Spreadsheets: XLS, XLSX (50MB)

**Organization Pattern**:
```
uploads/{org_id}/{category}/{year}/{month}/{file_id}{extension}
```

---

### 4. **Email Account Service** (`services/email_account_service.py`)

**Purpose**: Automatic email account management on iRedMail server

**Features**:
- Auto email creation for new employees
- Deactivation on termination
- Duplicate handling
- Operation logging

**Email Format**: `firstname.lastname@ailabsafrica.com`

---

### 5. **Wallet & Billing System** (`integration/wallet.py`)

**Supported Currencies**: GHS, USD, EUR, GBP, NGN, KES, ZAR

**Transaction Types**:
- CREDIT (money added)
- DEBIT (money deducted)
- REFUND (returned money)
- REVERSAL (transaction reversal)

**Features**:
- Multi-currency support
- Transaction history
- Wallet balance tracking
- Payment provider integration (Stripe, Flutterwave, Paystack)
- Fraud detection
- KYC verification

---

### 6. **RAG Service** (`integration/rag.py`)

**Purpose**: Semantic search and AI-powered Q&A for knowledge bases

**Features**:
- Multi-provider support (OpenAI, Gemini, Anthropic)
- pgvector for efficient semantic search
- Automatic chunking and embedding
- Confidence scoring
- Escalation logic

**Database**: PostgreSQL with pgvector extension

---

### 7. **LLM Provider Service** (`services/llm_provider_service.py`)

**Purpose**: Orchestrate multiple LLM providers with cost tracking

**Supported Providers**:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Google Gemini
- Anthropic Claude
- Mistral
- Groq
- Local models (Ollama)

---

### 8. **AI Services** (`integration/ai_services/`)

**Components**:
- **Provider Registry** - Discover and manage 10+ providers
- **Health Monitor** - Track provider availability
- **TTS Service** - Multi-provider speech synthesis
- **STT Service** - Multi-provider speech recognition

---

## Integration Services (50+)

### Payment Systems
- **Stripe** - Credit card processing
- **Flutterwave** - African payments
- **Paystack** - Nigerian payments
- **MTN Mobile Money** - Mobile money
- **Ghana Interbank** - Ghana banking

### Communication
- **Email** - SMTP, SendGrid, Resend (1372 lines)
- **SMS** - Twilio, MessageBird
- **WhatsApp** - Business API, templates
- **Telegram** - Bot integration
- **Discord** - Webhooks

### CRM & Productivity
- **HubSpot** - CRM & sales
- **Freshdesk** - Support tickets
- **Freshsales** - Sales pipeline
- **Pipedrive** - Sales management
- **Zendesk** - Helpdesk
- **Intercom** - Chat
- **Zapier** - Automation
- **Make.com** - Workflow automation

### Business Systems
- **Healthcare**: Epic, Cerner, Allscripts (EHR)
- **Financial**: Fiserv, FIS, Jack Henry (Core banking)
- **QuickBooks** - Accounting
- **Odoo** - ERP
- **ServiceNow** - ITSM
- **Salesforce** - Enterprise CRM

### Productivity Tools
- **Google Workspace** - Sheets, Calendar, Docs
- **Google Drive** - Cloud storage
- **Microsoft 365** - Office, Teams, SharePoint
- **Confluence** - Team wiki
- **Notion** - Databases & docs
- **Calendly** - Scheduling

### Data & Knowledge
- **Firecrawl** - Web scraping
- **Tavily** - Web search
- **Brave** - Search API
- **Google Analytics** - Analytics data

---

## Industry Modules (13)

Each module provides:
- **Capabilities**: Domain-specific operations
- **Automation Workflows**: Multi-step business processes
- **Integration Points**: External system connections
- **Compliance Frameworks**: HIPAA, PCI-DSS, etc.

### Module List

| Module | Key Features | Lines | Status |
|--------|---|---|---|
| **Healthcare** | Patient management, appointments, HIPAA | 44,251 | ✅ Enhanced |
| **Financial** | Banking, loans, PCI-DSS, fraud detection | 35,755 | ✅ Enhanced |
| **Retail** | Inventory, orders, loyalty, demand forecast | 24,989 | ✅ Enhanced |
| **Manufacturing** | Production, QA, maintenance, supply chain | 54,479 | ✅ Complete |
| **Logistics** | Fleet, delivery, tracking, route optimization | 52,331 | ✅ Complete |
| **Telecom** | Call management, customer support | 50,705 | ✅ Complete |
| **Insurance** | Claims, policies, coverage | 57,268 | ✅ Complete |
| **Real Estate** | Properties, tenants, maintenance | 60,108 | ✅ Complete |
| **Education** | Students, courses, academic workflow | 62,087 | ✅ Enhanced |
| **Professional Services** | Legal, consulting, projects | 71,085 | ✅ Complete |
| **Automotive** | Vehicles, service, sales, warranty | 87,090 | ✅ Complete |
| **Hospitality** | Rooms, guests, bookings | 45,524 | ✅ Complete |
| **Utilities** | Meters, billing, outages | 51,408 | ✅ Complete |
| **Government** | Citizens, permits, services | 51,323 | ✅ Complete |

---

## How Other Apps Use the Shared Library

### Import Patterns

```python
# 1. Shared services
from apps.shared.services.tts_provider_service import TTSProviderService
from apps.shared.services.pdf_extraction_service import get_pdf_extraction_service
from apps.shared.services.file_upload_service import get_file_upload_service

# 2. Integrations
from apps.shared.integration.email import EmailIntegration
from apps.shared.integration.stripe import StripeIntegration
from apps.shared.integration.wallet import WalletService

# 3. Industry modules
from apps.shared.modules.healthcare import HealthcareModule
from apps.shared.modules.financial import FinancialModule

# 4. Authentication
from apps.shared.auth.supabase_auth import get_current_user
from apps.shared.dependencies import require_organization_access

# 5. Models & Config
from apps.shared.models.organization import Organization
```

### Current Apps Using Shared Library

- **Core Backend** (`@apps/core_backend/`) - All services, TTS, wallet, industries
- **StudyFlow** (`@apps/studyflow/`) - TTS, pronunciation guides
- **Inkwave** (`@apps/inkwave/`) - TTS for audiobook narration
- **ChurchFlow**, **EventFlow** - Email, SMS, wallet
- **Developer Platform** - Integration management
- **ERP Backend** - Email accounts, PDF extraction, file uploads

---

## Authentication System

**Provider**: Supabase (https://supabase.ailabsafrica.com)

**Default Users**:
- Admin: `admin@ailabsafrica.com`
- User: `user@ailabsafrica.com`

**Implementation**:
- JWT token-based
- Middleware for organization context
- Multi-tenant support
- CORS configured for all apps

**Usage**:
```python
from apps.shared.auth.supabase_auth import get_current_user

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user": user["email"]}
```

---

## Multi-Tenant Architecture

### Organization System

**Models** (`models/organization.py`):
- Organization (tenant)
- User membership
- Role-based access control
- Settings per organization

**Middleware** (`middleware/organization_context.py`):
- Extracts org_id from request context
- Validates user membership
- Applies org-specific settings

**Pattern**:
```python
from apps.shared.dependencies import require_organization_access

@router.get("/data")
async def get_data(
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_access)
):
    # User has access to org_id
    return {"organization": org_id}
```

---

## Frontend Components (`frontend/`)

**Tech Stack**: React, TypeScript, Vitest

**Components**:
- **Admin Components** - Dashboard, user management
- **Reusable Components** - Forms, tables, modals
- **Hooks** - Custom React hooks
- **Services** - API client, auth, data fetching

**Usage**:
```typescript
import { AdminLayout } from '@shared/frontend/components'
import { useAuth } from '@shared/frontend/hooks'
```

---

## Storage Options

### 1. **Hetzner Storage Box** (Primary)
- SFTP-based cloud storage
- Configuration in `storage/HETZNER_STORAGE_BOX.md`
- Used for file uploads, voice samples, voice clones

### 2. **Redis** (Caching)
- In-memory data store
- Session management
- Rate limiting

### 3. **PostgreSQL** (Persistent)
- Relational data storage
- pgvector for embeddings (RAG)

### 4. **Memory** (Development)
- In-memory fallback
- Testing purposes

---

## Key Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main library overview |
| `services/README.md` | Service documentation & examples |
| `INTEGRATION_GUIDE.md` | RAG, Document Processor, Wallet patterns |
| `ORGANIZATION_SYSTEM.md` | Multi-tenant architecture |
| `MOBILE_RECEIPT_UPLOAD.md` | Mobile file upload workflow |
| `storage/HETZNER_STORAGE_BOX.md` | Cloud storage setup |
| `auth/DEFAULT_USERS.md` | Test user credentials |
| `auth/README.md` | Authentication patterns |
| `GEMINI_LLM_INTEGRATION.md` | Gemini LLM setup |

---

## Architecture Patterns

### 1. **Service Factory Pattern**
```python
# Service registry for dynamic instantiation
factory = create_module("healthcare", tenant_id)
```

### 2. **Middleware Pattern**
```python
# Multi-tenant context injection
app.add_middleware(OrganizationContextMiddleware)
```

### 3. **Dependency Injection**
```python
# FastAPI dependencies for auth & org access
def protected_route(
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_access)
)
```

### 4. **Async/Await Pattern**
```python
# All services support async operations
result = await tts_service.synthesize(user_id, request)
```

### 5. **Error Handling Pattern**
```python
# Specific exceptions for different failure modes
try:
    result = await service.operation()
except ValidationError as e:
    # Input validation failed
except ServiceError as e:
    # Service operation failed
```

---

## Configuration

### Environment Variables

```bash
# Authentication
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=<key>
SUPABASE_SERVICE_ROLE_KEY=<key>

# Storage
HETZNER_STORAGE_BOX_HOST=<host>
HETZNER_STORAGE_BOX_USERNAME=<user>
HETZNER_STORAGE_BOX_PASSWORD=<pass>
HETZNER_STORAGE_BOX_PORT=22

# Email
IREDMAIL_API_URL=http://85.214.12.174:8100
IREDMAIL_API_KEY=<key>

# LLM Providers
OPENAI_API_KEY=<key>
GEMINI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>

# Payment Systems
STRIPE_API_KEY=<key>
FLUTTERWAVE_API_KEY=<key>

# Third-party Integrations
HUBSPOT_API_KEY=<key>
FRESHDESK_API_KEY=<key>
```

---

## Testing

### Test Structure
```
tests/
├── test_services/
├── test_integrations/
├── test_modules/
└── test_frontend/
```

### Test Patterns
- Unit tests for individual services
- Integration tests with real databases
- Contract tests for API contracts
- E2E tests for workflows

### Running Tests
```bash
# All tests
python -m pytest shared/tests/

# Specific test file
python -m pytest shared/tests/test_tts_service.py

# With coverage
pytest --cov=shared shared/tests/
```

---

## Deployment & Performance

### Optimization Features
- Caching with Redis
- Lazy loading of modules
- Async/await for I/O operations
- Health monitoring for providers
- Cost tracking and optimization

### Scalability
- Multi-tenant support
- Database sharding ready
- Horizontal scaling compatible
- Load-balanced provider selection

---

## Security & Compliance

### Standards Implemented
- **HIPAA** - Healthcare data protection
- **PCI-DSS** - Payment card data security
- **GDPR** - Data privacy
- **SOC 2** - Security controls

### Security Features
- JWT authentication
- API key management
- Rate limiting
- Input validation
- Encrypted credentials
- Audit logging

---

## Quick Integration Checklist

When adding shared library to a new app:

- [ ] Install shared package: `pip install -e @apps/shared`
- [ ] Configure Supabase auth in `.env`
- [ ] Import required services
- [ ] Add auth dependencies to protected routes
- [ ] Add organization context middleware
- [ ] Configure logging and monitoring
- [ ] Set up error handling
- [ ] Write integration tests
- [ ] Document custom patterns

---

## Common Integration Scenarios

### Scenario 1: Adding TTS to App
```python
# Initialize at startup
tts = TTSProviderService()
await tts.initialize()

# Use in routes
@router.post("/tts")
async def synthesize(text: str, user: dict = Depends(get_current_user)):
    result = await tts.synthesize(user["id"], SynthesisRequest(...))
    return result
```

### Scenario 2: File Upload with Storage
```python
upload_service = await get_file_upload_service()
result = await upload_service.upload_file(
    file=file,
    organization_id=org_id,
    file_category="receipts"
)
```

### Scenario 3: Payment Processing
```python
from apps.shared.integration.stripe import StripeIntegration
stripe = StripeIntegration(api_key=key)
charge = await stripe.create_payment_intent(amount, currency)
```

### Scenario 4: Email Sending
```python
from apps.shared.integration.email import EmailIntegration
email = EmailIntegration(config)
await email.send_email(to, subject, body)
```

---

## Performance Metrics

### Service Latency (Typical)
- TTS synthesis: 1-5 seconds (varies by provider)
- PDF extraction: 0.5-2 seconds
- Email sending: 100-500ms
- API calls: <500ms

### Scaling Capacity
- Concurrent users: 1000+
- Requests/second: 100+ per service
- Storage: Unlimited (Hetzner)

---

## Support & Resources

1. **Service README**: `/opt/kasaai/apps/shared/services/README.md`
2. **Integration Guide**: `/opt/kasaai/apps/shared/INTEGRATION_GUIDE.md`
3. **Organization Docs**: `/opt/kasaai/apps/shared/ORGANIZATION_SYSTEM.md`
4. **Frontend Guide**: `/opt/kasaai/apps/shared/frontend/README.md`
5. **Auth Setup**: `/opt/kasaai/apps/shared/auth/README.md`

---

**Version**: 1.0  
**Last Updated**: 2025-11-06  
**Maintainer**: KasaAI Platform Team

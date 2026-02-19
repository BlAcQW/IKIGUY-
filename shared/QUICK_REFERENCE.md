# KasaAI Shared Library - Quick Reference Guide

**Total Codebase**: 76,003 lines of Python + React/TypeScript

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    KasaAI Applications                            │
│  (Core Backend, StudyFlow, Inkwave, ChurchFlow, ERP, etc.)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────┐
        │   Shared Library (@apps/shared/)           │
        │   Production-Ready Platform Services       │
        └────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │   Services   │   │ Integrations │   │   Modules    │
  │   (8.4 KB)   │   │  (48.6 KB)   │   │  (19.0 KB)   │
  └──────────────┘   └──────────────┘   └──────────────┘
         │                    │                    │
         ├─ TTS Provider      ├─ Email            ├─ Healthcare
         ├─ PDF Extract       ├─ SMS              ├─ Finance
         ├─ File Upload       ├─ WhatsApp         ├─ Retail
         ├─ LLM Provider      ├─ Stripe           ├─ Manufacturing
         ├─ Email Account     ├─ Flutterwave      ├─ Logistics
         ├─ Billing           ├─ HubSpot          ├─ Telecom
         ├─ ASR Provider      ├─ Freshdesk        ├─ Insurance
         ├─ Organization      ├─ Google Workspace ├─ Real Estate
         └─ etc.              ├─ RAG Service      ├─ Education
                              ├─ Wallet System    ├─ Professional Svc
                              ├─ Integration Mgr  ├─ Automotive
                              └─ etc. (50+ more)  ├─ Hospitality
                                                   ├─ Utilities
                                                   └─ Government
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ Core Support │   │  Storage     │   │  Frontend    │
  └──────────────┘   └──────────────┘   └──────────────┘
    - Auth            - Hetzner Box      - React Comps
    - Config          - PostgreSQL       - TypeScript
    - Middleware      - Redis            - Admin UI
    - Monitoring      - MongoDB          - Hooks
    - Security        - Memory
    - Licensing
```

---

## Services Layer (8.4 KB Code)

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **TTS Provider** | Text-to-speech synthesis | 10 providers, voice cloning, billing |
| **PDF Extraction** | Receipt/invoice parsing | OCR, pattern matching, confidence scores |
| **File Upload** | Cloud storage management | Hetzner Storage Box, org-based folders |
| **Email Account** | iRedMail automation | Auto create/disable accounts |
| **LLM Provider** | Multi-LLM orchestration | OpenAI, Gemini, Anthropic, Mistral |
| **ASR Provider** | Speech-to-text | Multiple STT providers |
| **Billing** | Cost tracking & invoicing | Multi-currency support |
| **Organization** | Tenant management | Multi-tenant context |
| **Voice Lab** | Voice operations | Generic ASR/TTS/chat |
| **Prompt Validation** | Input validation | Prompt safety checks |

---

## Integrations Layer (48.6 KB Code)

### By Category

**Payment Systems** (5)
- Stripe, Flutterwave, Paystack, MTN Mobile Money, Ghana Interbank

**Communication** (8)
- Email (SMTP, SendGrid, Resend), SMS, WhatsApp, Telegram, Discord, Vonage

**CRM & Sales** (7)
- HubSpot, Freshdesk, Freshsales, Pipedrive, Salesforce, Zendesk, Intercom

**Business Systems** (7)
- Healthcare (Epic, Cerner, Allscripts), Finance (Fiserv, FIS, Jack Henry), QuickBooks

**Productivity** (9)
- Google Workspace, Google Drive, Microsoft 365, Confluence, Notion, Calendly, Zapier, Make, ServiceNow

**Data & Knowledge** (6)
- RAG (semantic search), Document Processor, Firecrawl, Tavily, Brave, Google Analytics

**Other** (8)
- MongoDB, Supabase, Redis, Prometheus, Grafana, VAPI, Integration Manager, Cost Calculator

**Totals**: 50+ integrations covering payments, communication, CRM, ERP, productivity, and analytics

---

## Modules Layer (19.0 KB Code)

### 13 Industry Modules

Each module includes:
- **Capabilities**: Domain operations (e.g., schedule_appointment)
- **Workflows**: Automation sequences (e.g., appointment_reminder_workflow)
- **Integration Points**: External connections
- **Compliance**: Industry standards (HIPAA, PCI-DSS, GDPR)

| Module | Capabilities | Workflows | Compliance |
|--------|---|---|---|
| **Healthcare** | Patient mgmt, Appointments, Labs, Rx | Appointment reminders, Lab processing | HIPAA |
| **Finance** | Accounts, Loans, Transfers | Fraud detection, Default alerts | PCI-DSS |
| **Retail** | Inventory, Orders, Customers | Demand forecasting, Loyalty | PCI-DSS |
| **Manufacturing** | Production, QA, Supply Chain | Maintenance scheduling, Safety | ISO 9001 |
| **Logistics** | Fleet, Routes, Delivery | Real-time tracking, Notifications | DOT |
| **Telecom** | Calls, Customers, Billing | Support automation, CRM sync | FCC |
| **Insurance** | Claims, Policies, Coverage | Claims processing, Underwriting | SOX |
| **Real Estate** | Properties, Tenants, Maintenance | Rent collection, Lease renewal | Fair Housing |
| **Education** | Students, Courses, Grades | Enrollment, Graduation workflows | FERPA |
| **Professional Svc** | Cases, Projects, Clients | Billing, Time tracking | Bar Association |
| **Automotive** | Vehicles, Service, Sales | Maintenance reminders, Recalls | NHTSA |
| **Hospitality** | Rooms, Guests, Bookings | Housekeeping, Guest experience | ADA |
| **Utilities** | Meters, Billing, Outages | Meter reading, Outage alerts | FERC |
| **Government** | Citizens, Permits, Services | Licensing, Emergency response | HIPAA, FERPA |

---

## Import Guide

### Where to Import From

```python
# ✅ Services
from apps.shared.services.tts_provider_service import TTSProviderService
from apps.shared.services.pdf_extraction_service import get_pdf_extraction_service
from apps.shared.services.file_upload_service import get_file_upload_service

# ✅ Integrations
from apps.shared.integration.email import EmailIntegration
from apps.shared.integration.stripe import StripeIntegration
from apps.shared.integration.wallet import WalletService
from apps.shared.integration.rag import RAGService

# ✅ Modules
from apps.shared.modules.healthcare import HealthcareModule
from apps.shared.modules.factory import create_module

# ✅ Authentication & Dependencies
from apps.shared.auth.supabase_auth import get_current_user
from apps.shared.dependencies import require_organization_access

# ✅ Models
from apps.shared.models.organization import Organization

# ❌ Don't import
# from apps.shared.integration.ai_services.provider_registry import...  # Use TTSProviderService instead
```

---

## Common Usage Patterns

### 1. TTS Synthesis with Billing
```python
from apps.shared.services.tts_provider_service import TTSProviderService

tts = TTSProviderService()
await tts.initialize()

# Estimate cost
cost = await tts.estimate_cost("Hello world", "coqui_xtts")

# Synthesize with auto-billing
result = await tts.synthesize(
    user_id="user_123",
    request=SynthesisRequest(
        provider_id="coqui_xtts",
        text="Hello world",
        language="en"
    )
)
# Returns: {audio_base64, duration, cost, transaction_id}
```

### 2. File Upload
```python
upload_service = await get_file_upload_service()

upload_info = await upload_service.upload_file(
    file=file_bytes,
    filename="receipt.pdf",
    organization_id="org_123",
    file_category="receipts"
)
# Returns: {url, file_id, path}
```

### 3. PDF Extraction
```python
pdf_service = get_pdf_extraction_service(use_ocr=True)

result = await pdf_service.extract_from_pdf(pdf_file)
# Returns: {merchant, amount, date, tax, currency, category, confidence}
```

### 4. Email Sending
```python
from apps.shared.integration.email import EmailIntegration

email = EmailIntegration(config)
await email.send_email(
    to="user@example.com",
    subject="Invoice",
    body="Your invoice is attached"
)
```

### 5. Protected Route with Auth
```python
@router.get("/data")
async def get_data(
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_access)
):
    return {"user": user["email"], "org": org_id}
```

### 6. Industry Module
```python
from apps.shared.modules.factory import create_module

healthcare = create_module("healthcare", tenant_id)
await healthcare.initialize(tenant_id, config)

result = await healthcare.execute_capability(
    "schedule_appointment",
    {"patient_id": "p_123", "doctor_id": "d_456", "date": "2024-11-15"}
)
```

---

## Key Dependencies

### Backend (Python)
```
fastapi>=0.100
pydantic>=2.0
motor>=3.0  # MongoDB async
psycopg2-binary>=2.9  # PostgreSQL
aiohttp>=3.8
pdfplumber>=0.11
pytesseract>=0.3
stripe>=7.0
```

### Frontend (TypeScript)
```
react>=18.0
typescript>=5.0
axios>=1.0
vitest>=0.30
@supabase/supabase-js>=2.0
```

---

## File Organization Summary

```
shared/ (76 KB total)
├── services/       (8.4 KB)  - 27 high-level business services
├── integration/    (48.6 KB) - 50+ external system integrations
├── modules/        (19.0 KB) - 13 industry-specific modules
├── auth/           - Supabase JWT authentication
├── storage/        - Cloud storage (Hetzner, Redis, PostgreSQL)
├── frontend/       - React/TypeScript components
├── config/         - Configuration management
├── middleware/     - Express/FastAPI middleware
├── dependencies/   - FastAPI dependency injection
├── models/         - Pydantic data models
├── voice-engine/   - Voice processing & SIP
├── security/       - Security features
├── monitoring/     - System monitoring
├── ai/            - AI utilities (sentiment, NER, etc.)
├── analytics/      - Business intelligence
├── tests/          - Test suite
└── docs/           - Documentation
```

---

## Performance Targets

| Operation | Target Latency | Notes |
|-----------|---|---|
| TTS Synthesis | 1-5s | Varies by provider & text length |
| PDF Extraction | 0.5-2s | With OCR for scanned docs |
| Email Send | 100-500ms | Multiple provider support |
| File Upload | <2s | To Hetzner Storage Box |
| RAG Query | 1-3s | Semantic search + LLM |
| LLM Call | 0.5-5s | Depends on model & input |
| Auth Check | <10ms | Cached JWT verification |

---

## Security & Compliance

### Implemented Standards
- **HIPAA** - Healthcare data (encryption, audit logs)
- **PCI-DSS** - Payment processing (tokenization, compliance checks)
- **GDPR** - Data privacy (deletion, consent tracking)
- **SOC 2** - Security controls (access logs, encryption)

### Built-in Security
- JWT authentication with Supabase
- API key management per service
- Input validation on all endpoints
- Rate limiting on public APIs
- Encrypted credential storage
- Comprehensive audit logging

---

## When to Use Each Service

**TTS Provider** → Need voice synthesis
**PDF Extraction** → Need to read receipts/invoices
**File Upload** → Need cloud file storage
**Email/SMS** → Need communication channels
**Wallet** → Need billing & cost tracking
**RAG** → Need semantic search over docs
**Industry Modules** → Need domain-specific workflows
**LLM Provider** → Need multi-provider LLM access

---

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| Provider offline | Check health monitor: `tts.get_provider("coqui_xtts")` |
| Insufficient balance | Check wallet: `WalletService.get_balance(user_id)` |
| Auth failed | Verify token not expired, check Supabase service |
| Upload failed | Check Hetzner credentials, disk space |
| PDF extraction low confidence | Enable OCR with `use_ocr=True` |
| RAG query timeout | Check PostgreSQL/pgvector performance |

---

## Next Steps

1. Read `/opt/kasaai/apps/shared/services/README.md` for detailed service docs
2. Review `/opt/kasaai/apps/shared/INTEGRATION_GUIDE.md` for integration patterns
3. Check existing apps (StudyFlow, Inkwave) for implementation examples
4. Run tests: `pytest /opt/kasaai/apps/shared/tests/`
5. Review auth docs: `/opt/kasaai/apps/shared/auth/README.md`

---

**Quick Stats**
- Total Lines: 76,003
- Services: 27
- Integrations: 50+
- Industry Modules: 13
- Frontend Components: 20+
- Test Coverage: Comprehensive (unit, integration, E2E)
- Production Status: Ready


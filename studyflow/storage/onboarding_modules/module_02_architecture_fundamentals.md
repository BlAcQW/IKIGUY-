# Module 2: Architecture Fundamentals

**Topics Covered:** architecture, monorepo, shared_services

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 3. The KasaAI Architecture

### 📚 Essential Reading (Start Here!)

**Location**: `/opt/kasaai/apps/architecture/`

This is your **first stop** for understanding the platform. Contains 17 comprehensive files (432 KB):

| Priority | File | Size | What You'll Learn |
|----------|------|------|-------------------|
| **🔴 Critical** | README.md | - | Navigation hub and quick start |
| **🔴 Critical** | ARCHITECTURE.md | 58KB | Core platform design, service boundaries, data flows |
| **🟡 Important** | INTEGRATION_GUIDE.md | 48KB | How to use shared services step-by-step |
| **🟡 Important** | API_DOCUMENTATION.md | 46KB | API contracts, standards, examples |
| **🟢 Reference** | TTS_INFRASTRUCTURE.md | - | TTS deployment and providers |
| **🟢 Reference** | AUTHENTICATION_SETUP.md | - | Supabase auth integration |
| **🟢 Reference** | PDF_EXTRACTION_SERVICE.md | - | Document processing |
| **🟢 Reference** | COMPONENT_PATTERNS.md | - | Frontend patterns |

> 💡 **Pro Tip**: Read ARCHITECTURE.md first, then INTEGRATION_GUIDE.md before writing any code.

---

### 🛠️ Shared Services Library (`@shared/`)

**Location**: `/opt/kasaai/apps/shared/`
**Size**: 76,003 lines of production-ready Python + React/TypeScript code

#### Three Core Layers

<details>
<summary><strong>Layer A: Services (27 Business Services)</strong></summary>

Located in `/opt/kasaai/apps/shared/services/`

| Service | Purpose | Key Features |
|---------|---------|--------------|
| **TTS Provider Service** | Text-to-speech | 10 providers, voice cloning, multi-language |
| **LLM Provider Service** | Language models | Multi-provider orchestration |
| **ASR Service** | Speech recognition | 9 providers, African languages |
| **RAG Service** | Semantic search | pgvector, confidence scoring |
| **Wallet Service** | Payment/credits | Multi-currency, audit trails |
| **PDF Extraction** | Document processing | OCR, pattern matching, chunking |
| **File Upload** | Storage management | Hetzner Storage Box + local |
| **Email Service** | Email automation | iRedMail integration, templates |
| **Organization Service** | Multi-tenancy | Org management, permissions |

</details>

<details>
<summary><strong>Layer B: Integrations (50+ External Systems)</strong></summary>

Located in `/opt/kasaai/apps/shared/integration/`

- **Payment Gateways**: Stripe, Flutterwave, Paystack, MTN MoMo, Ghana Interbank
- **Communication**: SMS, WhatsApp, Telegram, Discord, Email
- **CRM**: HubSpot, Freshdesk, Pipedrive, Zendesk
- **Business**: Healthcare (Epic, Cerner), Finance (Fiserv), QuickBooks
- **Productivity**: Google Workspace, Microsoft 365, Slack, Notion
- **Workflow**: n8n, Zapier automation

</details>

<details>
<summary><strong>Layer C: Modules (13 Industry Verticals)</strong></summary>

Pre-built industry modules with compliance frameworks:
- Healthcare, Finance, Retail, Manufacturing, Logistics
- Telecom, Insurance, Real Estate, Education
- Professional Services, Automotive, Hospitality, Utilities, Government

</details>

#### 🔧 How to Use Shared Services

```python
# Example: Using RAG Service
from apps.shared.integration.rag import get_rag_service

rag = get_rag_service()

# Query knowledge base
results = await rag.query(
    query="What is Ghana known for?",
    collection_name="ghana_facts",
    top_k=5
)

# Add document
await rag.add_document(
    collection_name="ghana_facts",
    text="Ghana is known for cocoa production...",
    metadata={"source": "wikipedia", "language": "en"}
)
```

📖 **Read More**: `/opt/kasaai/apps/shared/QUICK_REFERENCE.md`

---

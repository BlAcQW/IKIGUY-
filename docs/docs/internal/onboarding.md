# KasaAI Developer Intern Onboarding Guide

**Welcome to KasaAI!** 🎉

**Version:** 1.0
**Last Updated:** November 7, 2025
**Target Audience:** New Developer Interns
**Estimated Reading Time:** 60-90 minutes

---

## Table of Contents

1. [Welcome to KasaAI](#1-welcome-to-kasaai)
2. [What is KasaAI?](#2-what-is-kasaai)
3. [The KasaAI Architecture](#3-the-kasaai-architecture)
4. [Core Infrastructure Components](#4-core-infrastructure-components)
5. [Vertical Applications](#5-vertical-applications)
6. [Supporting Infrastructure](#6-supporting-infrastructure)
7. [Development Environment Setup](#7-development-environment-setup)
8. [Your First Tasks](#8-your-first-tasks)
9. [Best Practices & Guidelines](#9-best-practices--guidelines)
10. [Resources & Support](#10-resources--support)

---

## 1. Welcome to KasaAI

### 🎯 Mission

KasaAI is on a mission to make AI-powered voice and conversational services accessible across Africa, particularly focusing on African languages and cultural contexts.

### 🌍 Our Impact

- **23+ AI Service Providers**: TTS, LLM, ASR services
- **1000+ African Languages**: Support via Meta MMS and other providers
- **7+ Production Applications**: Serving education, churches, events, and more
- **Multi-tenant Platform**: Each organization gets isolated, secure access

### 🚀 What You'll Learn

As a KasaAI intern, you will gain hands-on experience with:
- **Modern Backend**: Python, FastAPI, MongoDB, PostgreSQL
- **React Frontend**: TypeScript, React 18, Tailwind CSS
- **AI Integration**: LLMs, TTS, ASR, RAG systems
- **Cloud Infrastructure**: Docker, Nginx, systemd, RunPod GPU
- **Production Systems**: Real users, real data, real impact

---

## 2. What is KasaAI?

### The Big Picture

KasaAI is a **multi-app AI platform** that provides voice AI, conversational AI, and intelligent automation services across Africa.

```
┌─────────────────────────────────────────────────────────────────┐
│                         KasaAI Platform                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Consumer Apps          Enterprise Apps        Developer Tools  │
│  ├─ B2C Portal          ├─ StudyFlow          ├─ Dev Platform  │
│  ├─ Community           ├─ ChurchFlow         └─ API Gateway   │
│  └─ AI Labs Africa      ├─ EventFlow                           │
│                         ├─ InkWave                              │
│                         └─ ERP                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      Shared Services Layer                      │
│  ┌───────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │ AI Models │ RAG      │ Wallet   │ File     │ Email/SMS    │  │
│  │ (TTS/ASR  │ Service  │ Service  │ Upload   │ Integration  │  │
│  │  /LLM)    │ (pgvec)  │ (Multi-  │ Service  │ (iRedMail)   │  │
│  │           │          │  curr.)  │          │              │  │
│  └───────────┴──────────┴──────────┴──────────┴──────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                         │
│  ┌──────────┬──────────┬───────────┬────────────┬────────────┐  │
│  │ MongoDB  │ Postgres │ Redis     │ Docker     │ Nginx      │  │
│  │ (Primary)│ (Auth+   │ (Cache)   │ (AI Svcs)  │ (Gateway)  │  │
│  │          │  RAG)    │           │            │            │  │
│  └──────────┴──────────┴───────────┴────────────┴────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Backend Sharing**: All apps share AI services, RAG, wallet, document processing
2. **Frontend Independence**: Each app has its own UI/UX tailored to its users
3. **Multi-tenancy**: Organizations are isolated with secure data boundaries
4. **Scalability**: Designed to handle thousands of users and millions of requests

---

## 3. The KasaAI Architecture

### 3.1 Architecture Documentation (`@architecture/`)

**Location**: `/opt/kasaai/apps/architecture/`

This is your **first stop** for understanding the platform. Contains 17 comprehensive files (432 KB):

#### Essential Reading (Start Here)

1. **README.md** - Navigation hub and quick start guide
2. **ARCHITECTURE.md** (58KB) - Core platform design, service boundaries, data flows
3. **INTEGRATION_GUIDE.md** (48KB) - Step-by-step integration instructions for shared services
4. **API_DOCUMENTATION.md** (46KB) - API contracts, standards, examples

#### Specialized Documentation

- **TTS_INFRASTRUCTURE.md** - TTS deployment and provider management
- **AUTHENTICATION_SETUP.md** - Supabase auth integration
- **PDF_EXTRACTION_SERVICE.md** - Document processing capabilities
- **COMPONENT_PATTERNS.md** - Frontend patterns (not enforced components)
- **DATABASE_BACKUP_SYSTEM.md** - Data safety and recovery

**💡 Pro Tip**: Read ARCHITECTURE.md first, then INTEGRATION_GUIDE.md before writing any code.

---

### 3.2 Shared Services Library (`@shared/`)

**Location**: `/opt/kasaai/apps/shared/`

**76,003 lines** of production-ready Python + React/TypeScript code providing platform-wide functionality.

#### Three Core Layers

##### A. Services Layer (27 Business Services)

Located in `/opt/kasaai/apps/shared/services/`:

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

##### B. Integrations Layer (50+ External Systems)

Located in `/opt/kasaai/apps/shared/integration/`:

**Payment Gateways**: Stripe, Flutterwave, Paystack, MTN MoMo, Ghana Interbank
**Communication**: SMS, WhatsApp, Telegram, Discord, Email
**CRM**: HubSpot, Freshdesk, Pipedrive, Zendesk
**Business**: Healthcare (Epic, Cerner), Finance (Fiserv), QuickBooks
**Productivity**: Google Workspace, Microsoft 365, Slack, Notion
**Workflow**: n8n, Zapier automation

##### C. Modules Layer (13 Industry Verticals)

Pre-built industry modules with compliance frameworks:
- Healthcare, Finance, Retail, Manufacturing, Logistics
- Telecom, Insurance, Real Estate, Education
- Professional Services, Automotive, Hospitality, Utilities, Government

#### How to Use Shared Services

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

**📖 Read More**: `/opt/kasaai/apps/shared/QUICK_REFERENCE.md`

---

## 4. Core Infrastructure Components

### 4.1 Core Backend (`@core_backend/`)

**Location**: `/opt/kasaai/apps/core_backend/`
**Port**: 30027 (Production), 30027 (Dev)
**URL**: https://api.ailabsafrica.com (Prod), https://dev-api.ailabsafrica.com (Dev)

#### Purpose

The **private control plane** that powers the entire KasaAI platform. Contains all business logic, data management, and orchestration.

#### What It Does

- **40+ Microservices**: Assistants, campaigns, analytics, billing, RAG, webhooks
- **80+ API Endpoints**: Internal APIs consumed by all frontends
- **Multi-tenant Data**: MongoDB for primary data, PostgreSQL for healthcare/RAG
- **Authentication**: JWT-based auth with 6-level RBAC (owner → read-only)

#### Key Features

1. **Voice Assistant Management**
   - Create AI-powered voice agents
   - Configure prompts, voices, models
   - Call management and recording

2. **Campaign Orchestration**
   - Outbound call campaigns
   - Multi-channel notifications (SMS, WhatsApp, Email)
   - Schedule and workflow management

3. **RAG System**
   - Knowledge base management
   - Semantic search with pgvector
   - Multi-organization isolation

4. **Billing & Wallet**
   - Credit-based usage tracking
   - Multi-currency support
   - Payment gateway integration

5. **Analytics & Reporting**
   - Call logs and transcriptions
   - Usage statistics
   - Cost breakdown

#### Technology Stack

- **Backend**: Python 3.11, FastAPI, Pydantic
- **Databases**: MongoDB (primary), PostgreSQL (healthcare, RAG), Redis (cache)
- **Authentication**: Supabase JWT + MongoDB user management
- **APIs**: RESTful, WebSocket for real-time

#### Important Files

- `/opt/kasaai/apps/core_backend/backend/main.py` - FastAPI entry point
- `/opt/kasaai/apps/core_backend/backend/routes/` - API endpoints by domain
- `/opt/kasaai/apps/core_backend/backend/services/` - Business logic services

**🔑 Key Concept**: Core Backend has NO frontend. All UIs (B2C Portal, vertical apps) are separate React apps that call Core Backend APIs.

---

### 4.2 B2C Portal (`@b2c-portal/`)

**Location**: `/opt/kasaai/apps/b2c-portal/`
**URL**: https://kasaai.ailabsafrica.com (Prod), https://dev-kasaai.ailabsafrica.com (Dev)

#### Purpose

The **main web interface** for KasaAI users to build and manage voice AI assistants, campaigns, and integrations.

#### Architecture

- **Pure Frontend**: React 18 + TypeScript + Vite
- **No Backend**: All API calls go to Core Backend (port 30027)
- **State Management**: TanStack Query (React Query)
- **UI Framework**: Tailwind CSS + shadcn/ui components

#### Key Features

1. **Voice Assistant Builder**
   - Visual assistant configuration
   - Prompt engineering interface
   - Voice and model selection
   - Test playground

2. **Campaign Manager**
   - Create outbound call campaigns
   - Contact list management
   - Schedule and analytics

3. **AI Labs**
   - LLM Lab: Test 9 language models
   - TTS Lab: Test 8 TTS providers with voice cloning
   - ASR Lab: Test 9 speech recognition providers

4. **Analytics Dashboard**
   - Real-time call statistics
   - Cost breakdown
   - Usage charts

5. **Billing & Credits**
   - Wallet management
   - Top-up and payment
   - Usage history

#### Technology Stack

- **Frontend**: React 18, TypeScript, Vite
- **Routing**: React Router
- **State**: TanStack Query
- **UI**: Tailwind CSS, shadcn/ui, Radix UI
- **Auth**: Supabase Auth (JWT tokens)

#### Important Files

- `/opt/kasaai/apps/b2c-portal/src/App.tsx` - Main app component
- `/opt/kasaai/apps/b2c-portal/src/pages/` - All page components
- `/opt/kasaai/apps/b2c-portal/src/services/api.ts` - API client

**🎨 Design Pattern**: Headless SPA + Private API Backend

---

### 4.3 Developer Platform (`@developer_platform/`)

**Location**: `/opt/kasaai/apps/developer_platform/`
**Backend Port**: 30028
**URL**: https://developer-portal-api.ailabsafrica.com (Prod)

#### Purpose

A **public API gateway** that enables third-party developers to build on KasaAI's infrastructure.

#### What Makes It Special

- **Public-Facing**: Designed for external developers (unlike Core Backend)
- **API Gateway**: Sits between developers and Core Backend
- **Well-Documented**: Comprehensive API docs + examples
- **Versioned APIs**: /api/v1 for stability

#### Key Capabilities

1. **Voice Assistant Management**: Create and manage AI assistants
2. **Call Management**: Initiate and monitor phone calls
3. **Workflow Automation**: n8n workflows with webhook triggers
4. **TTS/ASR Services**: Text-to-speech and speech recognition
5. **LLM Services**: Access to language models
6. **File Storage**: Upload and retrieve files
7. **Webhooks**: Event notifications with HMAC signing
8. **API Key Management**: Granular scope-based keys
9. **MCP Registry**: Register custom connectors
10. **Analytics & Billing**: Real-time usage tracking

**Total**: 60+ API endpoints across 13 categories

#### Technology Stack

**Backend**:
- Python 3.11, FastAPI
- MongoDB for persistence
- mTLS proxy to Core Backend
- API key-based authentication

**Frontend** (Developer Console):
- React 18.3, TypeScript, Vite
- Tailwind CSS, shadcn/ui
- API key management UI
- Usage dashboard

#### Security

- API key authentication with scopes
- Rate limiting (100 req/min basic, 1000 req/min premium)
- Request signing (HMAC-SHA256)
- CORS protection

#### Important Files

- `/opt/kasaai/apps/developer_platform/backend/main.py` - FastAPI entry point
- `/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md` - Full API reference (40KB)
- `/opt/kasaai/apps/developer_platform/PLANNING.md` - Architecture overview

**📚 Documentation**: Read `API_DOCUMENTATION.md` for complete API reference

---

## 5. Vertical Applications

These are **industry-specific applications** built on top of KasaAI's shared infrastructure.

### 5.1 StudyFlow (EduMate) (`@studyflow/`)

**Purpose**: AI-powered personal tutoring platform for African schools

**Target Users**:
- Students (Grades 9-12)
- Parents (progress tracking, payment)
- Teachers (curriculum upload, class monitoring)
- Schools (bulk enrollment)

**Key Features**:
- RAG-powered Q&A from school materials
- Voice and text conversational learning
- Practice exercises with instant feedback
- Multi-language support (English, Twi, French)
- Parent dashboard with AI progress reports
- Gamification (stars, badges, streaks)

**Technology Stack**:
- Mobile: React Native (Expo)
- Admin Portal: Next.js/React
- Backend: FastAPI + MongoDB
- Vector DB: PostgreSQL + pgvector (RAG)
- Voice: KasaAI Voice Lab + optional VAPI

**Pricing**:
- Free Trial: 30 minutes
- Pay-as-you-learn: ₵20 = 100 minutes
- Monthly Plan: ₵50/month unlimited
- School Plan: ₵30/student/month (min 50 students)

**Shared Services Used**:
- RAG Service (Q&A from materials)
- Document Processor (PDF/DOCX processing)
- Wallet Service (pay-per-use)
- Usage Calculator (cost tracking)

**Status**: Planning complete, ready for development

**📖 Read More**: `/opt/kasaai/apps/studyflow/PLANNING.md`

---

### 5.2 EventFlow (EventPilot) (`@eventflow/`)

**Purpose**: Mobile-first, AI-driven event management with automated voice follow-ups

**Target Users**:
- Event Organizers (conferences, weddings, concerts)
- Transport Coordinators (logistics)
- Responsible Persons (task assignments)
- Vendors/Service Providers

**Key Features**:
- Event setup wizard (auto-generates tasks)
- AI-powered task and timeline management
- **Automated voice calls** to follow up with team members
- Interactive Voice Response (IVR) for confirmations
- SMS/WhatsApp/Email reminders via n8n
- Real-time escalation for overdue tasks
- Organizer dashboard with progress visualization
- AI recommendations and risk detection

**Technology Stack**:
- Mobile: React Native (Expo)
- Web Dashboard: Next.js/React
- Backend: FastAPI + MongoDB
- Notifications: n8n workflows + Twilio + Firebase
- Voice AI: VAPI (primary), Voice Lab (fallback)
- Real-time: WebSockets (FastAPI)

**Pricing**:
| Action | Free | Basic | Premium |
|--------|------|-------|---------|
| Event creation | Free | Free | Free |
| Voice call/min | N/A | ₵2.00 | ₵1.50 |
| SMS reminder | N/A | ₵0.20 | ₵0.15 |
| WhatsApp msg | N/A | ₵0.30 | ₵0.25 |

**Shared Services Used**:
- VAPI Service (automated calls, IVR)
- n8n Workflow Service (multi-channel notifications)
- Wallet Service (pay-per-use)
- RAG Service (AI recommendations)

**Status**: Concept complete, ready for development

**📖 Read More**: `/opt/kasaai/apps/eventflow/PLANNING.md`

---

### 5.3 ChurchFlow (`@churchflow/`)

**Purpose**: Church management and event coordination platform

**Target Users**:
- Church Members (event registration, bus coordination)
- Transport Coordinators (route management)
- Conference Organizers (event creation)
- Church Admins (oversight, analytics)

**Key Features**:
- Phone OTP authentication
- **Bus transportation coordination** with capacity tracking
- Real-time delay notifications (SMS, Push, WhatsApp, Email)
- Auto-assignment when buses reach capacity
- Conference registration with digital check-in
- QR code generation and scanning (under 20s check-in)
- Multi-channel notifications via n8n
- AI Voice Kiosk ("Ama") with motion detection (Phase 2)
- Volunteer role management

**Technology Stack**:
- Mobile: React Native (Expo)
- Kiosk: React Web (tablets)
- Backend: FastAPI + MongoDB
- Auth: Supabase (phone OTP)
- Notifications: n8n + Twilio + Firebase
- Voice AI: VAPI or Voice Lab (Phase 2)

**Deployment**:
- Port: 30030
- URL: https://churchflow.ailabsafrica.com (Prod)
- URL: https://dev-churchflow.ailabsafrica.com (Dev)

**Status**: Phase 1 MVP 90% complete
- ✅ Authentication & user profiles
- ✅ Bus transportation coordination
- ✅ Conference registration & QR check-in
- ✅ Admin dashboard (fully functional)
- ⏳ Multi-channel notifications (n8n pending)
- ⏳ Mobile app (React Native - not started)

**📖 Read More**: `/opt/kasaai/apps/churchflow/PLANNING.md`, `PRD.md`, `MVP_SUMMARY.md`

---

### 5.4 InkWave (`@inkwave/`)

**Purpose**: Interactive audiobook platform with conversational AI

**Target Users**:
- Readers (interactive listening)
- Students (learning while listening)
- Book Lovers (audio with interaction)
- Content Creators (author uploads)

**Key Features**:
- Interactive audiobook playback with user-controlled pacing
- **Conversational Q&A powered by RAG** (semantic search over book content)
- Text-to-Speech with multiple voices and speed controls
- Speech-to-Text for voice questions
- Personalized reading (bookmarks, notes, progress)
- Real-time cost tracking and wallet system
- PDF/DOCX upload and automatic processing
- WebSocket real-time interaction

**Technology Stack**:
- Frontend: React Native (Expo) or PWA (React + Vite)
- Backend: FastAPI with WebSocket
- Task Queue: Celery + Redis (async PDF processing)
- Databases: MongoDB (books, sessions), pgvector (embeddings)
- AI: OpenAI GPT-4 / Gemini / Claude (RAG)
- TTS/STT: ElevenLabs / OpenAI / Coqui XTTS
- Storage: S3 / MinIO (PDFs, audio cache)

**Pricing**:
- Reading (narration): $0.02/min
- Voice input (STT): $0.01/15s
- LLM processing: $0.05/1000 tokens
- TTS output: $0.03/min
- Book processing (one-time): $0.50/50 pages

**Shared Services Used**:
- RAG Service (semantic search over books)
- Document Processor (PDF extraction, chunking)
- Wallet Service (payment management)
- Usage Calculator (cost tracking)

**Status**: Planning complete, ready for MVP

**📖 Read More**: `/opt/kasaai/apps/inkwave/PLANNING.md`

---

### 5.5 ERP (`@erp/`)

**Purpose**: Enterprise Resource Planning for African SMEs

**Features**:
- **Finance**: Accounting, invoicing, expenses (with receipt upload)
- **HR**: Employee management, payroll, benefits (with CV/certificate upload)
- **CRM**: Customer and lead management
- **Projects**: Task and project tracking
- **BI**: Analytics and reporting
- **Integration**: Multi-system integration

**Recent Additions (Nov 6, 2025)**:
- ✅ CV and certificate upload for employees
- ✅ Mobile camera capture for expense receipts
- ✅ Toast notifications for email account creation
- ✅ Document management with secure storage

**Technology Stack**:
- Backend: FastAPI + MongoDB
- Frontend: React + TypeScript + Tailwind
- Auth: Supabase
- File Storage: Local uploads directory

**Deployment**:
- Port: 30034 (Dev only)
- URL: https://dev-erp-api.ailabsafrica.com

**Status**: Active development on dev server

**📖 Read More**: `/opt/kasaai/apps/erp/PLANNING.md`, `README.md`

---

## 6. Supporting Infrastructure

### 6.1 TTS Deployment (`@tts-deployment/`)

**Purpose**: Comprehensive multi-TTS system deployment for state-of-the-art text-to-speech and voice AI

**Infrastructure**:
- **Local GPU**: NVIDIA RTX 4000 SFF Ada (20GB VRAM) - 8 Docker containers
- **RunPod GPU**: NVIDIA A40 (46GB VRAM) - F5-TTS, StyleTTS2

**Services**: 10 AI services (8 fully operational)

| Service | Status | Port | Endpoint | Features |
|---------|--------|------|----------|----------|
| Coqui TTS | ✅ Online | 8005 | https://coqui.ailabsafrica.com | XTTS v2 voice cloning, 20+ languages |
| MeloTTS | ✅ Online | 8001 | https://melotts.ailabsafrica.com | Fast multilingual synthesis |
| OpenVoice | ✅ Online | 8003 | https://openvoice.ailabsafrica.com | Voice cloning + tone transfer |
| Kokoro TTS | ✅ Online | 8010 | https://kokoro.ailabsafrica.com | Lightweight, mobile-optimized |
| F5-TTS | ✅ Online | 8002 | https://f5tts.ailabsafrica.com | Flow-matching TTS (RunPod) |
| StyleTTS2 | 🔄 Building | 8006 | https://styletts.ailabsafrica.com | Human-level expressive TTS (RunPod) |
| Ollama | ✅ Online | 11434 | https://ollama.ailabsafrica.com | 9 LLM models |
| Open WebUI | ✅ Online | 8007 | https://openwebui.ailabsafrica.com | Unified LLM/TTS interface |
| Moshi | 🟡 Degraded | 8011 | http://localhost:8011 | Conversational AI (GPU constrained) |
| Crawl4AI | ✅ Online | 8009 | https://crawl4ai.ailabsafrica.com | Web scraping |

**Key Capabilities**:
- 🎭 **Voice Cloning**: Zero-shot from 5-10 second audio
- 🌍 **African Languages**: 1000+ languages via Meta MMS (Akan/Twi, Ga, Ewe, Hausa, Yoruba, Swahili)
- 🤖 **9 LLM Models**: Including Ghanaian fine-tuned variants
- 🎤 **9 ASR Providers**: Including GiftMark Akan (92.9% accuracy)
- ⚡ **Real-time**: 1-3 second generation time, 24kHz audio

**Frontend Integration**: 3 labs in B2C Portal
- LLM Lab (`/llm-lab`)
- ASR Lab (`/asr-lab`)
- TTS Lab (`/tts-lab`)

**Technology**:
- Docker Compose for orchestration
- Nginx reverse proxy with SSL
- Let's Encrypt certificates (expires Jan 2026)
- Systemd for service management

**Status**: ✅ Production Ready (8/10 services operational)

**📖 Read More**: `/opt/kasaai/apps/tts-deployment/README.md`

---

### 6.2 Community Platform (`@community/`)

**Purpose**: Community-driven African language data collection platform

**Vision**: Create the world's largest, highest-quality, community-driven repository of African language data to power next-generation voice AI systems.

**Core Features**:
- **Language Family Organization**: Niger-Congo, Afroasiatic, Nilo-Saharan
- **Multi-tier Quality System**:
  - Tier 1: Gold Standard (3+ expert validators)
  - Tier 2: Community Reviewed (2 validators)
  - Tier 3: Raw Submissions
- **Multi-channel Submission**:
  - Discord bot (`!submit twi audio "story"`)
  - Mobile app (field recording)
  - Web portal (bulk upload)
- **Gamification**: Points, achievements, leaderboards
- **Community Governance**: Decentralized voting system

**Language Families Supported**:
- **Kwa Family**: Twi, Fante, Ga, Ewe
- **Yoruboid**: Yoruba, Igala
- **Bantu**: Swahili, Zulu, Xhosa
- **Chadic**: Hausa, Kanuri
- **Cushitic**: Amharic, Oromo, Somali

**Data Types**:
- Audio recordings with transcriptions
- Text corpora (stories, proverbs, conversations)
- Phonetic inventories and tonal patterns
- Cultural context notes
- Dialect variations

**Technology Stack**:
- Backend: FastAPI, MongoDB, Redis, WebSockets
- Frontend: React, Supabase Auth
- Discord Bot: Discord.py
- Mobile: React Native
- Storage: MinIO (object storage)

**Integration**: Feeds training pipelines for TTS/ASR model fine-tuning

**Status**: Documentation complete, ready for implementation

**📖 Read More**: `/opt/kasaai/apps/community/COMMUNITY_DATA_PLATFORM.md`, `DEPLOYMENT.md`

---

## 7. Development Environment Setup

### 7.1 Server Access

**Production Server**: 148.251.0.46
**Dev Server**: 85.214.12.174

```bash
# SSH to dev server
ssh dev@85.214.12.174

# Or production (with proper permissions)
ssh dev@148.251.0.46
```

### 7.2 Required Tools

1. **IDE**: VS Code or PyCharm
2. **Python**: 3.11+ (use pyenv for version management)
3. **Node.js**: 18+ (use nvm for version management)
4. **Docker**: For local TTS service development
5. **MongoDB Compass**: For database inspection
6. **Postman/Insomnia**: For API testing

### 7.3 Local Development Setup

#### Backend Setup

```bash
# Navigate to project
cd /opt/kasaai/apps/core_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run development server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend
cd /opt/kasaai/apps/b2c-portal

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with API URLs

# Run development server
npm run dev
```

### 7.4 Database Access

**MongoDB**:
```bash
# Connect to MongoDB
mongo mongodb://admin:password@127.0.0.1:27017/

# Or use MongoDB Compass GUI
# Connection string: mongodb://admin:password@127.0.0.1:27017/
```

**PostgreSQL** (Supabase):
```bash
# Connection details in /opt/kasaai/.env
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=your-key
```

### 7.5 Service Management

```bash
# Check all KasaAI services
sudo systemctl list-units "kasaai-*.service" --all

# Check specific service
sudo systemctl status kasaai-core-backend

# Restart service
sudo systemctl restart kasaai-studyflow-backend

# View logs
sudo journalctl -u kasaai-churchflow-backend -f
```

---

## 8. Your First Tasks

### Week 1: Learning & Exploration

#### Day 1-2: Read Documentation
- [ ] Read this onboarding guide (you're here!)
- [ ] Read `/opt/kasaai/apps/architecture/ARCHITECTURE.md`
- [ ] Read `/opt/kasaai/apps/architecture/INTEGRATION_GUIDE.md`
- [ ] Explore `/opt/kasaai/apps/shared/QUICK_REFERENCE.md`

#### Day 3-4: Environment Setup
- [ ] Get server access credentials from your mentor
- [ ] SSH into dev server
- [ ] Clone a simple app (e.g., b2c-portal) and run locally
- [ ] Access MongoDB and explore collections
- [ ] Test API endpoints with Postman

#### Day 5: Code Exploration
- [ ] Read code in `/opt/kasaai/apps/shared/services/` (pick 2-3 services)
- [ ] Trace a simple API call from frontend → backend → database
- [ ] Run tests for a component

### Week 2: First Contribution

#### Simple Tasks (Choose 1)

1. **Add a New TTS Voice** to TTS Lab
   - File: `/opt/kasaai/apps/b2c-portal/src/pages/TTSLab.tsx`
   - Task: Add a new voice option to an existing provider
   - Skills: React, TypeScript, UI components

2. **Create API Documentation** for an Endpoint
   - File: `/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md`
   - Task: Document a missing endpoint with examples
   - Skills: Technical writing, API understanding

3. **Fix a UI Bug** in B2C Portal
   - Check: `/opt/kasaai/apps/b2c-portal/TASKS.md` for known issues
   - Task: Fix alignment, styling, or minor logic issue
   - Skills: React, CSS, debugging

4. **Add Unit Tests** for a Service
   - File: `/opt/kasaai/apps/shared/services/` (pick any service)
   - Task: Add pytest tests for a service function
   - Skills: Python, pytest, mocking

### Week 3-4: Feature Development

Work with your mentor to choose a feature from one of these:

**StudyFlow**:
- Implement practice exercise generation
- Add progress tracking chart

**ChurchFlow**:
- Complete mobile app QR scanner
- Add SMS notification integration

**EventFlow**:
- Implement task timeline visualization
- Add voice call logging

**ERP**:
- Add expense report generation
- Implement HR performance review forms

---

## 9. Best Practices & Guidelines

### 9.1 Code Quality

**Always Follow**:
1. **PEP 8** for Python code
2. **Type Hints** everywhere (`def function(arg: str) -> int:`)
3. **Docstrings** for all functions (Google style)
4. **Error Handling** with try/except and logging
5. **Consistent Naming**: snake_case (Python), camelCase (TypeScript)

**Example**:
```python
async def get_user_wallet_balance(user_id: str, organization_id: str) -> float:
    """
    Get the current wallet balance for a user.

    Args:
        user_id: The unique identifier for the user
        organization_id: The organization the user belongs to

    Returns:
        The current balance as a float

    Raises:
        ValueError: If user not found
        DatabaseError: If database connection fails
    """
    try:
        wallet = await db.wallets.find_one({
            "user_id": user_id,
            "organization_id": organization_id
        })

        if not wallet:
            raise ValueError(f"Wallet not found for user {user_id}")

        return wallet.get("balance", 0.0)

    except Exception as e:
        logger.error(f"Failed to get wallet balance: {e}")
        raise DatabaseError("Could not retrieve wallet balance") from e
```

### 9.2 Testing

**Test Requirements**:
- **Minimum**: 1 expected use case, 1 edge case, 1 failure case
- **Location**: `/tests/` folder mirroring main structure
- **Use Real Data**: Test with actual databases, not mocks (see `TEST_SUITE_ANALYSIS.md`)

**Example Test**:
```python
import pytest
from backend.services.wallet_service import get_wallet_service

@pytest.mark.asyncio
async def test_get_wallet_balance_success():
    """Test getting wallet balance for existing user."""
    service = get_wallet_service()
    balance = await service.get_balance(
        user_id="user123",
        org_id="org456"
    )
    assert balance >= 0.0

@pytest.mark.asyncio
async def test_get_wallet_balance_user_not_found():
    """Test error handling for non-existent user."""
    service = get_wallet_service()
    with pytest.raises(ValueError, match="Wallet not found"):
        await service.get_balance(
            user_id="nonexistent",
            org_id="org456"
        )
```

### 9.3 Git Workflow

**Commit Rules**:
1. **Create git commit** after each completed task
2. **Write clear commit messages** (imperative mood)
3. **Reference task/issue** if applicable

**Good Commit Messages**:
```bash
# Good ✅
git commit -m "Add CV upload functionality to HR employee form"
git commit -m "Fix mobile camera capture for expense receipts"
git commit -m "Update ERP TASKS.md with completed document management features"

# Bad ❌
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "work in progress"
```

**Branch Strategy**:
```bash
# Create feature branch
git checkout -b feature/add-expense-receipt-upload

# Make changes and commit
git add .
git commit -m "Add expense receipt upload with camera support"

# Push to remote
git push origin feature/add-expense-receipt-upload

# Create pull request (if applicable)
```

### 9.4 API Design

**RESTful Principles**:
- `GET /api/v1/users/{user_id}` - Retrieve
- `POST /api/v1/users` - Create
- `PATCH /api/v1/users/{user_id}` - Partial update
- `DELETE /api/v1/users/{user_id}` - Delete

**Response Format**:
```json
{
  "success": true,
  "data": {
    "id": "user123",
    "name": "John Doe"
  },
  "metadata": {
    "timestamp": "2025-11-07T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Error Format**:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 'user123' not found",
    "details": {
      "user_id": "user123"
    }
  },
  "metadata": {
    "timestamp": "2025-11-07T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### 9.5 Documentation

**Update These After Changes**:
1. **TASKS.md** - Mark completed tasks, add new discoveries
2. **README.md** - Update when adding features or changing setup
3. **PLANNING.md** - Update architecture when making structural changes
4. **API_DOCUMENTATION.md** - Document new endpoints

---

## 10. Resources & Support

### 10.1 Essential Documentation Locations

| Component | Path | Key Files |
|-----------|------|-----------|
| **Architecture** | `/opt/kasaai/apps/architecture/` | ARCHITECTURE.md, INTEGRATION_GUIDE.md |
| **Shared Services** | `/opt/kasaai/apps/shared/` | QUICK_REFERENCE.md, services/README.md |
| **Core Backend** | `/opt/kasaai/apps/core_backend/` | README.md, backend/main.py |
| **B2C Portal** | `/opt/kasaai/apps/b2c-portal/` | README.md, src/App.tsx |
| **Developer Platform** | `/opt/kasaai/apps/developer_platform/` | API_DOCUMENTATION.md, PLANNING.md |
| **StudyFlow** | `/opt/kasaai/apps/studyflow/` | PLANNING.md, PRD.md, MVP_SUMMARY.md |
| **ChurchFlow** | `/opt/kasaai/apps/churchflow/` | PLANNING.md, PRD.md, MVP_SUMMARY.md |
| **EventFlow** | `/opt/kasaai/apps/eventflow/` | PLANNING.md, VOICE_AI_IMPLEMENTATION_PLAN.md |
| **InkWave** | `/opt/kasaai/apps/inkwave/` | PLANNING.md |
| **ERP** | `/opt/kasaai/apps/erp/` | README.md, TASKS.md, PLANNING.md |
| **TTS Deployment** | `/opt/kasaai/apps/tts-deployment/` | README.md, RUNPOD_SETUP.md |
| **Community** | `/opt/kasaai/apps/community/` | COMMUNITY_DATA_PLATFORM.md, DEPLOYMENT.md |

### 10.2 Common Commands Cheat Sheet

**Service Management**:
```bash
# List all KasaAI services
sudo systemctl list-units "kasaai-*.service"

# Check service status
sudo systemctl status kasaai-core-backend

# Restart service
sudo systemctl restart kasaai-studyflow-backend

# View live logs
sudo journalctl -u kasaai-churchflow-backend -f

# Check last 100 log lines
sudo journalctl -u kasaai-core-backend -n 100
```

**Database Operations**:
```bash
# Connect to MongoDB
mongo mongodb://admin:password@127.0.0.1:27017/

# Show databases
show dbs

# Use database
use kasaai_core

# Show collections
show collections

# Query documents
db.users.find({}).limit(5)

# Count documents
db.assistants.count()
```

**Docker (TTS Services)**:
```bash
# List running containers
docker ps

# Check container logs
docker logs -f coqui-tts

# Restart container
docker restart melotts

# Check Docker disk usage
docker system df

# Cleanup unused images
docker image prune -a
```

**Git Operations**:
```bash
# Check status
git status

# Create feature branch
git checkout -b feature/my-feature

# Stage changes
git add .

# Commit with message
git commit -m "Add feature X with Y functionality"

# Push to remote
git push origin feature/my-feature

# Pull latest changes
git pull origin main
```

### 10.3 Troubleshooting

**Common Issues**:

1. **Service won't start**:
   ```bash
   # Check logs for errors
   sudo journalctl -u kasaai-[service-name] -n 100

   # Check if port is in use
   sudo netstat -tulpn | grep [port]

   # Check permissions
   ls -la /opt/kasaai/apps/[app-name]/
   ```

2. **Database connection errors**:
   ```bash
   # Check MongoDB status
   sudo systemctl status mongodb

   # Test connection
   mongo --eval "db.adminCommand('ping')"

   # Check credentials in .env
   cat /opt/kasaai/.env | grep MONGODB
   ```

3. **Import errors**:
   ```bash
   # Ensure virtual environment is activated
   source /opt/kasaai/apps/venv/bin/activate

   # Reinstall dependencies
   pip install -r requirements.txt

   # Check Python path
   echo $PYTHONPATH
   ```

4. **Frontend won't build**:
   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install

   # Clear cache
   npm cache clean --force

   # Check Node version
   node --version  # Should be 18+
   ```

### 10.4 Who to Ask

**Architecture & System Design**: Senior developers, Lead architects
**Backend Development (Python/FastAPI)**: Backend team leads
**Frontend Development (React/TypeScript)**: Frontend team leads
**AI Integration (TTS/ASR/LLM)**: AI/ML team
**Database (MongoDB/PostgreSQL)**: Database administrators
**DevOps (Docker/Nginx/Deployment)**: DevOps team
**Specific Apps (StudyFlow, ChurchFlow, etc.)**: App-specific team leads

**General Questions**: Your assigned mentor

### 10.5 Learning Resources

**Internal**:
- Architecture documentation (`/opt/kasaai/apps/architecture/`)
- Shared services examples (`/opt/kasaai/apps/shared/services/`)
- Existing app code (read before you write!)
- PLANNING.md files for each app

**External**:
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev
- MongoDB Docs: https://docs.mongodb.com
- Supabase Docs: https://supabase.com/docs
- Tailwind CSS: https://tailwindcss.com/docs

---

## Congratulations! 🎉

You've completed the KasaAI Developer Intern Onboarding Guide. You now have a comprehensive understanding of:

✅ KasaAI's mission and architecture
✅ All major platform components
✅ How apps share services and infrastructure
✅ Where to find documentation
✅ How to set up your development environment
✅ Best practices for code, testing, and commits
✅ Who to ask for help

### Next Steps

1. **Schedule a 1:1 with your mentor** to discuss your first tasks
2. **Set up your development environment** following Section 7
3. **Start with Week 1 tasks** from Section 8
4. **Ask questions early and often** - we're here to help!

### Remember

- **Read before you code**: Check PLANNING.md, ARCHITECTURE.md, and existing code
- **Test your changes**: Write pytest tests for backend, check UI manually
- **Document as you go**: Update TASKS.md, README.md, commit messages
- **Commit frequently**: After each completed task or logical unit
- **Ask for help**: Better to ask than to spend hours stuck

**Welcome to the team! Let's build amazing AI products for Africa together.** 🚀🌍

---

**Document Version**: 1.0
**Last Updated**: November 7, 2025
**Maintained By**: KasaAI Engineering Team
**Questions?** Contact your mentor or engineering@ailabsafrica.com

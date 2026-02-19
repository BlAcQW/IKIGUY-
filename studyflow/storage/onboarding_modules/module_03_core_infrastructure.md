# Module 3: Core Infrastructure

**Topics Covered:** core_backend, b2c_portal, developer_platform

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 4. Core Infrastructure Components

### 4.1 Core Backend (`@core_backend/`)

<table>
<tr><td><strong>Location</strong></td><td><code>/opt/kasaai/apps/core_backend/</code></td></tr>
<tr><td><strong>Port</strong></td><td>30027 (Production & Dev)</td></tr>
<tr><td><strong>URL (Prod)</strong></td><td>https://api.ailabsafrica.com</td></tr>
<tr><td><strong>URL (Dev)</strong></td><td>https://dev-api.ailabsafrica.com</td></tr>
</table>

#### 🎯 Purpose

The **private control plane** that powers the entire KasaAI platform. Contains all business logic, data management, and orchestration.

#### ✨ What It Does

- **40+ Microservices**: Assistants, campaigns, analytics, billing, RAG, webhooks
- **80+ API Endpoints**: Internal APIs consumed by all frontends
- **Multi-tenant Data**: MongoDB for primary data, PostgreSQL for healthcare/RAG
- **Authentication**: JWT-based auth with 6-level RBAC (owner → read-only)

#### 🔑 Key Features

<details>
<summary><strong>1. Voice Assistant Management</strong></summary>

- Create AI-powered voice agents
- Configure prompts, voices, models
- Call management and recording

</details>

<details>
<summary><strong>2. Campaign Orchestration</strong></summary>

- Outbound call campaigns
- Multi-channel notifications (SMS, WhatsApp, Email)
- Schedule and workflow management

</details>

<details>
<summary><strong>3. RAG System</strong></summary>

- Knowledge base management
- Semantic search with pgvector
- Multi-organization isolation

</details>

<details>
<summary><strong>4. Billing & Wallet</strong></summary>

- Credit-based usage tracking
- Multi-currency support
- Payment gateway integration

</details>

<details>
<summary><strong>5. Analytics & Reporting</strong></summary>

- Call logs and transcriptions
- Usage statistics
- Cost breakdown

</details>

#### 🛠️ Technology Stack

- **Backend**: Python 3.11, FastAPI, Pydantic
- **Databases**: MongoDB (primary), PostgreSQL (healthcare, RAG), Redis (cache)
- **Authentication**: Supabase JWT + MongoDB user management
- **APIs**: RESTful, WebSocket for real-time

#### 📁 Important Files

- `/opt/kasaai/apps/core_backend/backend/main.py` - FastAPI entry point
- `/opt/kasaai/apps/core_backend/backend/routes/` - API endpoints by domain
- `/opt/kasaai/apps/core_backend/backend/services/` - Business logic services

> 🔑 **Key Concept**: Core Backend has NO frontend. All UIs (B2C Portal, vertical apps) are separate React apps that call Core Backend APIs.

---

### 4.2 B2C Portal (`@b2c-portal/`)

<table>
<tr><td><strong>Location</strong></td><td><code>/opt/kasaai/apps/b2c-portal/</code></td></tr>
<tr><td><strong>URL (Prod)</strong></td><td>https://kasaai.ailabsafrica.com</td></tr>
<tr><td><strong>URL (Dev)</strong></td><td>https://dev-kasaai.ailabsafrica.com</td></tr>
</table>

#### 🎯 Purpose

The **main web interface** for KasaAI users to build and manage voice AI assistants, campaigns, and integrations.

#### 🏗️ Architecture

- **Pure Frontend**: React 18 + TypeScript + Vite
- **No Backend**: All API calls go to Core Backend (port 30027)
- **State Management**: TanStack Query (React Query)
- **UI Framework**: Tailwind CSS + shadcn/ui components

#### ✨ Key Features

1. **Voice Assistant Builder** - Visual assistant configuration
2. **Campaign Manager** - Outbound call campaigns
3. **AI Labs** - Test LLM, TTS, ASR providers
4. **Analytics Dashboard** - Real-time call statistics
5. **Billing & Credits** - Wallet management

#### 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite
- **Routing**: React Router
- **State**: TanStack Query
- **UI**: Tailwind CSS, shadcn/ui, Radix UI
- **Auth**: Supabase Auth (JWT tokens)

#### 📁 Important Files

- `/opt/kasaai/apps/b2c-portal/src/App.tsx` - Main app component
- `/opt/kasaai/apps/b2c-portal/src/pages/` - All page components
- `/opt/kasaai/apps/b2c-portal/src/services/api.ts` - API client

> 🎨 **Design Pattern**: Headless SPA + Private API Backend

---

### 4.3 Developer Platform (`@developer_platform/`)

<table>
<tr><td><strong>Location</strong></td><td><code>/opt/kasaai/apps/developer_platform/</code></td></tr>
<tr><td><strong>Backend Port</strong></td><td>30028</td></tr>
<tr><td><strong>URL (Prod)</strong></td><td>https://developer-portal-api.ailabsafrica.com</td></tr>
</table>

#### 🎯 Purpose

A **public API gateway** that enables third-party developers to build on KasaAI's infrastructure.

#### 🌟 What Makes It Special

- **Public-Facing**: Designed for external developers (unlike Core Backend)
- **API Gateway**: Sits between developers and Core Backend
- **Well-Documented**: Comprehensive API docs + examples
- **Versioned APIs**: /api/v1 for stability

#### ⚡ Key Capabilities

1. Voice Assistant Management
2. Call Management
3. Workflow Automation
4. TTS/ASR Services
5. LLM Services
6. File Storage
7. Webhooks (with HMAC signing)
8. API Key Management
9. MCP Registry
10. Analytics & Billing

**Total**: 60+ API endpoints across 13 categories

#### 🛠️ Technology Stack

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

#### 🔒 Security

- API key authentication with scopes
- Rate limiting (100 req/min basic, 1000 req/min premium)
- Request signing (HMAC-SHA256)
- CORS protection

#### 📁 Important Files

- `/opt/kasaai/apps/developer_platform/backend/main.py` - FastAPI entry point
- `/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md` - Full API reference (40KB)
- `/opt/kasaai/apps/developer_platform/PLANNING.md` - Architecture overview

---

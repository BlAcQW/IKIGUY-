# KasaAI Platform Architecture Documentation

**📚 Single Source of Truth for Platform Architecture**

This folder contains all architectural documentation for the KasaAI platform. Before creating a new app or integrating with shared services, start here to understand the platform's design principles, patterns, and best practices.

---

## 📖 Documentation Index

### 1. [ARCHITECTURE.md](./ARCHITECTURE.md)
**High-level platform architecture and design principles**

- Multi-app platform structure
- Shared services philosophy (backend-only sharing)
- Technology stack overview
- Service boundaries and responsibilities
- Data flow patterns
- Authentication and authorization architecture

**Read this first** to understand the overall platform design.

---

### 2. [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
**API contracts, standards, and conventions**

- RESTful API design standards
- Authentication patterns (JWT, Supabase)
- Request/response formats
- Error handling conventions
- Versioning strategy
- Internal API contracts (AI services, RAG, wallets)

**Essential for** building new APIs or integrating with existing services.

---

### 3. [COMPONENT_PATTERNS.md](./COMPONENT_PATTERNS.md)
**Frontend component patterns and React best practices**

- Documented UI patterns (not enforced shared components)
- AI Lab patterns (TTS, LLM, ASR)
- Reusable React hooks design
- Component composition strategies
- Testing patterns
- Migration guides

**Critical for** building consistent frontend experiences across apps.

---

### 4. [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
**Step-by-step integration guides for shared services**

- AI Provider Services integration
- RAG (Retrieval-Augmented Generation) setup
- Document processing workflows
- Wallet and usage tracking
- Health monitoring setup
- Code examples and templates

**Practical guide** for integrating shared backend services into your app.

---

## 🏗️ Platform Structure

```
apps/
├── architecture/              ← YOU ARE HERE (docs)
├── shared/
│   ├── integration/          ← Backend shared services
│   │   ├── ai_services/      ← AI provider management
│   │   ├── rag_service/      ← RAG and embeddings
│   │   ├── document_processor/ ← Document handling
│   │   └── wallet_service/   ← Usage tracking
│   └── ui-hooks/             ← Shared React hooks
├── b2c-portal/               ← Main SaaS portal
├── developer_platform/        ← Developer API portal
├── ailabsafrica/             ← Company website
├── community/                ← Language community platform
├── bookshop/                 ← Bookshop app
├── church_manager/           ← Church management app
├── event_manager/            ← Event management app
└── personal_tutor/           ← Personal tutor app
```

---

## 🎯 When to Use This Documentation

### Before Starting a New App
1. Read **ARCHITECTURE.md** → Understand platform design philosophy
2. Read **INTEGRATION_GUIDE.md** → Learn what services you can leverage
3. Reference **COMPONENT_PATTERNS.md** → Copy proven UI patterns
4. Check **API_DOCUMENTATION.md** → Understand API contracts

### When Building Features
1. **Adding AI capabilities?** → See INTEGRATION_GUIDE.md (AI Services section)
2. **Building RAG features?** → See INTEGRATION_GUIDE.md (RAG section)
3. **Creating frontend components?** → See COMPONENT_PATTERNS.md
4. **Exposing new APIs?** → Follow standards in API_DOCUMENTATION.md

### When Debugging
1. Check **ARCHITECTURE.md** → Understand service boundaries
2. Check **API_DOCUMENTATION.md** → Verify API contracts
3. Check **INTEGRATION_GUIDE.md** → Confirm correct usage patterns

---

## 🚀 Quick Start: Creating a New App

### Step 1: Understand the Platform (15 min)
```bash
# Read the high-level architecture
cat apps/architecture/ARCHITECTURE.md
```

### Step 2: Plan Your Integration (30 min)
```bash
# Review available shared services
cat apps/architecture/INTEGRATION_GUIDE.md

# Understand API standards
cat apps/architecture/API_DOCUMENTATION.md
```

### Step 3: Set Up Your App Structure
```
your-new-app/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app
│   │   ├── api/
│   │   │   └── routes/          ← Your endpoints
│   │   ├── services/            ← Business logic
│   │   │   └── use_shared.py    ← Import from @apps/shared
│   │   └── models/              ← Pydantic models
│   └── tests/                   ← Pytest tests
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/          ← Copy patterns from COMPONENT_PATTERNS.md
│   │   └── hooks/               ← Import from @apps/shared/ui-hooks
│   └── ...
├── PLANNING.md                  ← Your app's design doc
├── TASK.md                      ← Your task tracker
└── README.md                    ← Your app's README
```

### Step 4: Integrate Shared Services
```python
# In your backend service
from apps.shared.integration.ai_services import (
    AIProviderService,
    ProviderRegistry,
    HealthMonitorService,
    ProviderType
)

# Use shared services instead of building from scratch
```

### Step 5: Follow Component Patterns
```tsx
// In your frontend
// Copy patterns from COMPONENT_PATTERNS.md
// Import shared hooks from @apps/shared/ui-hooks
```

---

## 📋 Design Principles

### 1. **Backend Sharing, Frontend Independence**
- ✅ Share backend services (AI, RAG, wallets, document processing)
- ✅ Share React hooks (logic only)
- ✅ Document UI patterns (copy & adapt)
- ❌ Don't share UI components (allow app-specific UX)

**Rationale**: Different apps have different UX needs (kid-friendly vs enterprise), and shared UI components create coupling and build complexity.

### 2. **Configuration Over Code**
- Use environment variables for endpoints
- Use ProviderRegistry for AI service configuration
- Avoid hardcoding service URLs or credentials

### 3. **Type Safety First**
- Use Pydantic models for all data structures
- Use TypeScript for all frontend code
- Define explicit API contracts

### 4. **Test Everything**
- Write Pytest tests for backend services
- Write Jest/Vitest tests for frontend components
- Test integration points thoroughly

### 5. **Document Patterns, Not Components**
- Provide clear examples and templates
- Allow flexibility for app-specific needs
- Maintain consistency through documentation

---

## 🔧 Technology Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: MongoDB (general), PostgreSQL (auth via Supabase)
- **Vector DB**: pgvector (via Supabase)
- **Async**: asyncio, aiohttp
- **Validation**: Pydantic
- **Testing**: Pytest

### Frontend
- **Language**: TypeScript
- **Framework**: React
- **Build**: Vite
- **Styling**: Tailwind CSS
- **State**: React hooks
- **Testing**: Jest/Vitest + React Testing Library

### Infrastructure
- **Reverse Proxy**: Nginx
- **Authentication**: Supabase Auth
- **AI Services**: Self-hosted (TTS, LLM, ASR)
- **Deployment**: Systemd services

---

## 📞 Getting Help

### Documentation Issues
- If documentation is unclear, update it and commit the improvement
- Add examples and clarifications as needed
- Keep docs in sync with code

### Architecture Questions
- Review existing apps for reference implementations
- Check `@apps/b2c-portal/` for TTS/LLM/ASR patterns
- Check `@apps/community/` for RAG and document processing patterns

### Integration Support
- See code examples in INTEGRATION_GUIDE.md
- Check `@apps/shared/integration/` for service implementations
- Look at tests in shared services for usage examples

---

## 🔄 Keeping Documentation Updated

**When to Update These Docs:**
- Adding new shared services → Update ARCHITECTURE.md + INTEGRATION_GUIDE.md
- Changing API contracts → Update API_DOCUMENTATION.md
- Creating new UI patterns → Update COMPONENT_PATTERNS.md
- Modifying integration flows → Update INTEGRATION_GUIDE.md

**Always commit documentation changes with code changes.**

---

## 📚 Additional Resources

- **Shared Services Code**: `@apps/shared/integration/`
- **Shared Hooks**: `@apps/shared/ui-hooks/`
- **Example Apps**: `@apps/b2c-portal/`, `@apps/community/`
- **Platform CLAUDE.md**: `/opt/kasaai/.claude/CLAUDE.md`

---

**Last Updated**: 2025-10-24
**Maintained By**: Platform Architecture Team

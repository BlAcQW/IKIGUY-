# Module 5: Vertical Applications - Part 2

**Topics Covered:** inkwave, erp

**Part of:** KasaAI Developer Intern Onboarding Course

---

### 5.4 InkWave (`@inkwave/`)

**🎯 Purpose**: Interactive audiobook platform with conversational AI

**👥 Target Users**:
- Readers (interactive listening)
- Students (learning while listening)
- Book Lovers (audio with interaction)
- Content Creators (author uploads)

**✨ Key Features**:
- Interactive audiobook playback with user-controlled pacing
- **Conversational Q&A powered by RAG** (semantic search over book content)
- Text-to-Speech with multiple voices and speed controls
- Speech-to-Text for voice questions
- Personalized reading (bookmarks, notes, progress)
- Real-time cost tracking and wallet system
- PDF/DOCX upload and automatic processing
- WebSocket real-time interaction

**💰 Pricing**:
- Reading (narration): $0.02/min
- Voice input (STT): $0.01/15s
- LLM processing: $0.05/1000 tokens
- TTS output: $0.03/min
- Book processing (one-time): $0.50/50 pages

**🔧 Shared Services Used**:
- RAG Service (semantic search over books)
- Document Processor (PDF extraction, chunking)
- Wallet Service (payment management)
- Usage Calculator (cost tracking)

**📊 Status**: Planning complete, ready for MVP

📖 **Read More**: `/opt/kasaai/apps/inkwave/PLANNING.md`

---

### 5.5 ERP (`@erp/`)

**🎯 Purpose**: Enterprise Resource Planning for African SMEs

**✨ Features**:
- **Finance**: Accounting, invoicing, expenses (with receipt upload)
- **HR**: Employee management, payroll, benefits (with CV/certificate upload)
- **CRM**: Customer and lead management
- **Projects**: Task and project tracking
- **BI**: Analytics and reporting
- **Integration**: Multi-system integration

**🆕 Recent Additions (Nov 6, 2025)**:
- ✅ CV and certificate upload for employees
- ✅ Mobile camera capture for expense receipts
- ✅ Toast notifications for email account creation
- ✅ Document management with secure storage

**🚀 Deployment**:
- Port: 30034 (Dev only)
- URL: https://dev-erp-api.ailabsafrica.com

**📊 Status**: Active development on dev server

📖 **Read More**: `/opt/kasaai/apps/erp/PLANNING.md`, `README.md`

---

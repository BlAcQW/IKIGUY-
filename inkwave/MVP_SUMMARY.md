# Inkwave MVP - Quick Reference

**Version**: 1.0 MVP
**Timeline**: 6 weeks
**Status**: Pre-Development

---

## 🎯 What We're Building

An **interactive audiobook platform** where users:
- Control narration pacing (tap to advance, unlike auto-play)
- Ask questions to an AI companion about what they're reading
- Pay only for what they use (no subscriptions)

**Think**: Audible + ChatGPT for books

---

## ✅ MVP Features (Must-Have)

### 1. User Authentication
- Email/password signup
- Google OAuth login
- $2 free trial credits on signup

### 2. Book Library
- Browse 10+ pre-loaded books
- Search by title/author
- Filter by genre, difficulty
- Book details (cover, summary, themes, reading time)
- Free preview (first chapter)

### 3. Audio Playback (User-Controlled)
- **Tap to advance** to next chunk
- **Swipe back** to previous chunk
- Play/pause
- Speed control (0.5x - 2x)
- Visual progress indicator
- Bookmarks
- Auto-save position

### 4. Text Q&A with AI
- Type questions about the book
- AI retrieves relevant passages (RAG)
- AI responds with context-aware answers
- No spoilers (only content before current position)
- Show estimated cost before asking
- Real-time wallet deduction

### 5. Credit-Based Wallet
- Display balance prominently
- Top-up: $5, $10, $25, $50
- Payment via Stripe or Paystack
- Transaction history
- Low balance warning
- Real-time cost tracking

### 6. User Profile
- Select TTS voice preference
- Set playback speed
- Set reading level (beginner/intermediate/advanced)
- Set explanation depth (brief/detailed)

---

## ❌ NOT in MVP (Future Phases)

- Voice input for questions → **Phase 2**
- Voice output for AI responses → **Phase 2**
- User PDF uploads → **Phase 2**
- Native mobile apps → **Phase 2** (PWA for MVP)
- Offline mode → **Phase 3**
- Background playback → **Phase 3**
- Personalized recommendations → **Phase 3**

---

## 📊 Success Metrics

**Primary KPI**: 20+ minutes average session duration

**Supporting KPIs**:
- 40%+ D7 retention (return within 7 days)
- 3+ Q&A interactions per session
- 30%+ conversion to paid (after free credits)
- 50%+ gross margin (revenue - AI costs)

---

## 💰 Pricing (MVP)

### Credits
- 100 credits = $1
- New users: 200 credits free ($2)

### Costs
- **Narration**: 2 credits/minute ($0.02/min)
  - 1-hour book = $2.40
- **Q&A**: ~1.25 credits per question ($0.0125)
  - 10 questions = ~$0.15

### Top-Up Packages
- $5 → 500 credits
- $10 → 1,000 credits
- $25 → 2,500 + 100 bonus (4%)
- $50 → 5,000 + 300 bonus (6%)

---

## 🏗️ Tech Stack

### Frontend
- **Framework**: React + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Type**: Progressive Web App (PWA)
- **State**: Zustand
- **HTTP**: Axios

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Location**: `@apps/core_backend/bookshop/`
- **URL**: https://api.ailabsafrica.com/bookshop/v1/
- **Validation**: Pydantic

### Shared Services (KasaAI Platform)
- **RAGService**: Semantic search for Q&A
- **DocumentProcessor**: Book processing & chunking
- **WalletService**: Payments (Stripe/Paystack)
- **UsageCalculator**: Cost tracking

### Databases
- **MongoDB**: Books, users, sessions, wallets
- **pgvector**: Embeddings for RAG
- **Supabase**: User authentication

### AI Services
- **LLM**: OpenAI GPT-4o-mini (Q&A)
- **TTS**: OpenAI TTS (narration)
- **Embeddings**: OpenAI text-embedding-3-small

---

## 📅 6-Week Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **1** | Setup | Backend/frontend structure, DB setup, auth integration, shared services testing |
| **2** | Books | Book CRUD, library UI, search/filter, book detail pages |
| **3** | Wallet | Wallet integration, payment flow (Stripe/Paystack), transaction history |
| **4** | Reading | Reading session, TTS integration, audio player UI, progress tracking |
| **5** | Q&A | RAG integration, interaction flow, cost calculation, wallet deduction |
| **6** | Polish | Testing, deployment, documentation, bug fixes, MVP launch |

---

## 🎨 User Experience Flow

### New User Journey
```
1. Land on homepage → "Get Started"
2. Sign up (email or Google)
3. Auto-credit $2 free trial
4. Browse library → Select book
5. View book detail → "Start Reading"
6. Audio player loads → First chapter free
7. Tooltip: "Tap to advance"
8. User explores and listens
```

### Core Reading Flow
```
1. User logs in
2. Dashboard: "Continue Reading: [Book]"
3. Click → Audio player at saved position
4. User listens, taps to advance
5. User clicks "Ask" button
6. Type question → "Est. cost: $0.08"
7. Click "Ask" → AI responds
8. Wallet debited → Can follow up
9. Resume reading → Auto-save position
```

---

## 🚀 Launch Criteria

**Technical**:
- ✅ All MVP features working
- ✅ 80%+ test coverage
- ✅ E2E test passes
- ✅ Performance: API < 500ms (p95), TTS < 2s
- ✅ Security audit passed

**Content**:
- ✅ 10+ books in library
- ✅ All books processed and indexed

**Documentation**:
- ✅ User guide
- ✅ API docs
- ✅ FAQ page

---

## ⚠️ Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **High AI costs** | Pre-generate TTS audio, cache responses, optimize prompts, rate limits |
| **Poor RAG accuracy** | Test with diverse books, tune chunking, implement confidence thresholds |
| **TTS latency** | Pre-generate narration, cache in CDN |
| **Wallet abuse** | Real-time balance checks, no credit extension, fraud detection |
| **Low engagement** | User testing, onboarding flow, iterate on UX |

---

## 🔄 Next Steps After MVP

**If metrics are met** (40%+ D7 retention, 30%+ conversion, 50%+ margin):

### Phase 2 (3-4 weeks)
- Voice input (STT) for questions
- Voice output (TTS) for AI responses
- WebSocket real-time communication
- User PDF uploads
- Enhanced personalization

---

## 📁 Key Documents

- **PRD.md** - Full product requirements document
- **PLANNING.md** - Detailed technical architecture
- **TASK.md** - Implementation task list
- **ARCHITECTURE.md** - Platform architecture
- **/apps/shared/integration/** - Shared services docs

---

## 👥 Team & Roles

**Product**: Define features, prioritize, user testing
**Engineering**: Backend (FastAPI), frontend (React), testing
**Design**: UI/UX, mobile-first responsive design
**QA**: Test coverage, E2E testing, bug tracking

---

## 📞 Questions?

- Check **PRD.md** for detailed specs
- Check **TASK.md** for implementation tasks
- Check **PLANNING.md** for architecture details

---

**Last Updated**: 2025-10-24

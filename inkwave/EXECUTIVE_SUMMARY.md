# Inkwave - Executive Summary

**Product**: Voice-First Interactive Audiobook Platform
**Timeline**: 6 weeks to MVP
**Target Launch**: Early 2025

---

## 🎯 What We're Building

**Inkwave** is a premium voice-first audiobook platform where users can:
- Listen to beautifully narrated books
- **Ask questions by voice** and get AI answers
- Pay only for what they use (no subscriptions)

**Think**: Audible + ChatGPT Voice Mode

---

## ✨ Key Differentiators

1. **Voice Q&A** - Talk to an AI companion about what you're reading
2. **User-controlled pacing** - Tap to advance, unlike auto-play
3. **Premium UI** - Audible/Netflix/Disney+ inspired design
4. **Fair pricing** - Usage-based, not subscriptions
5. **Built on KasaAI infrastructure** - Leverages African AI services

---

## 🏗️ Architecture (Leverage @shared/)

### Shared Services (100% Reuse)

| Service | Purpose | Location |
|---------|---------|----------|
| **RAGService** ✅ | Q&A with Gemini 2.0 Flash | `@apps/shared/integration/rag.py` |
| **AI Provider Service** ✅ | TTS (Coqui, OpenAI) + STT (Whisper) | `@apps/shared/integration/ai_services/` |
| **WalletService** ✅ | Payments (Stripe/Paystack) | `@apps/shared/integration/wallet.py` |
| **UsageCalculator** ✅ | Cost tracking | `@apps/shared/integration/usage_calculator.py` |
| **DocumentProcessor** ✅ | Book processing | `@apps/shared/integration/document_processor.py` |

### Custom Services (Inkwave-Specific)

| Service | Purpose | Location |
|---------|---------|----------|
| BookService | Book CRUD | `@apps/inkwave/backend/services/` |
| ReadingService | Session tracking | `@apps/inkwave/backend/services/` |
| VoiceAgentService | Orchestrate voice Q&A | `@apps/inkwave/backend/services/` |

**Key Principle**: "Share infrastructure, customize experience"

---

## 🎨 User Experience

### Home Screen (Netflix-Style)
```
┌──────────────────────────────────────────┐
│  [Hero Banner: Featured Book]           │
├──────────────────────────────────────────┤
│  Continue Reading              →         │
│  [Book] [Book] [Book] [Book]            │
├──────────────────────────────────────────┤
│  Recommended for You           →         │
│  [Book] [Book] [Book] [Book]            │
└──────────────────────────────────────────┘
```

### Voice Q&A Flow
```
1. User listens to audiobook
2. Taps "🎙️ Ask" button
3. Speaks question: "What does this mean?"
4. AI transcribes (STT) → retrieves context (RAG) → generates answer (Gemini) → speaks (TTS)
5. User hears AI explanation
6. Can ask follow-up or resume reading
```

---

## 💰 Pricing

### Credits
- 100 credits = $1
- New users: 200 credits free ($2)

### Costs
- **Narration**: $0.02/minute (pre-generated, cached)
- **Voice Q&A**: ~$0.04 per question (STT + RAG + TTS)

### Top-Up Packages
- $5 → 500 credits
- $10 → 1,000 credits
- $25 → 2,500 + 100 bonus
- $50 → 5,000 + 300 bonus

---

## 🤖 AI Stack (Best-in-Class)

| Component | Provider | Model | Why |
|-----------|----------|-------|-----|
| **RAG (LLM)** | Gemini | gemini-2.0-flash-exp | Fast, cheap, multilingual-ready |
| **Embeddings** | Gemini | text-embedding-004 | Consistent with LLM |
| **TTS (Narration)** | Coqui XTTS v2 | - | Voice cloning, multilingual |
| **TTS (Q&A)** | OpenAI | tts-1 | Fast, high quality |
| **STT** | OpenAI Whisper | whisper-1 | Best accuracy |

**All integrated via shared services** - no vendor lock-in, easy to swap providers.

---

## 📊 Success Metrics

**Primary KPI**: 20+ minutes average session duration

**Supporting KPIs**:
- 80%+ users try voice Q&A
- 3+ voice questions per session
- 40%+ D7 retention
- 30%+ conversion to paid
- 50%+ gross margin

---

## 📅 6-Week Timeline

| Week | Focus | Key Deliverables |
|------|-------|------------------|
| 1 | Setup + Beautiful UI | Backend/frontend setup, hero banner, shelves |
| 2 | Audio Playback | TTS integration, audio player UI |
| 3 | Voice Input | STT (Whisper), voice recording UI |
| 4 | Voice Q&A | Gemini RAG integration, Q&A flow |
| 5 | Wallet + Polish | Payment flow, animations |
| 6 | Testing + Launch | E2E tests, deployment |

---

## 💡 Why This Will Succeed

### 1. Leveraging Existing Infrastructure
- ✅ **No RAG to build** - shared service ready
- ✅ **No payment system** - wallet service ready
- ✅ **No TTS/STT** - AI services ready
- ✅ **No document processing** - processor ready

**Result**: Build in 6 weeks instead of 6 months

### 2. Unique Value Proposition
- **Only voice-based interactive audiobook platform**
- Fair pricing (no subscriptions)
- Premium experience (beautiful UI)

### 3. Built for Africa
- Leverages KasaAI's African AI infrastructure
- Ready for multilingual expansion (Twi, Yoruba, Swahili)
- Local payment support (Paystack, M-Pesa)

---

## 🚀 Go-to-Market

### Phase 1 (MVP - 6 weeks)
- Launch with 10 English books
- Target: 100 early adopters
- Pricing: $2 free trial + usage-based

### Phase 2 (3 months)
- Add 50+ books
- Implement voice conversations (multi-turn)
- User PDF uploads
- Target: 1,000 active users

### Phase 3 (6 months)
- African language support (Twi, Yoruba, Swahili)
- Native mobile apps (iOS/Android)
- Target: 10,000 active users

---

## 💵 Unit Economics (1,000 Users/Month)

### Revenue
- 1,000 users × $5 avg spend = **$5,000/month**

### Costs
- AI (Gemini + TTS + STT): ~$1,000/month
- Infrastructure: ~$200/month
- Payment fees (3%): ~$150/month
- **Total**: ~$1,350/month

### Gross Margin
- **73%** ($3,650 profit on $5,000 revenue)

**Scalability**: Margins improve with scale (fixed infra costs)

---

## ⚠️ Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Voice costs too high | High | Pre-generate narration, cache responses, use Gemini Flash |
| Poor voice recognition | High | Use Whisper (best accuracy), allow text fallback |
| Slow voice Q&A | Medium | Optimize RAG, use streaming TTS, show "thinking" feedback |
| Low adoption | High | Beautiful UI, free trial, early user testing |

---

## 📁 Key Documents

- **PRD.md** - Full product requirements
- **MVP_VOICE_BASED.md** - Voice-first MVP details
- **SHARED_SERVICES_USAGE.md** - How we leverage @shared/
- **EMBEDDING_COMPARISON.md** - Why Gemini vs OpenAI
- **PLANNING.md** - Technical architecture
- **TASK.md** - Implementation tasks

---

## ✅ Decision Log

**AI Provider**: Gemini 2.0 Flash (cost-effective, fast, multilingual-ready)
**Embeddings**: Gemini text-embedding-004 (consistent with LLM)
**MVP Approach**: Voice-first (not text Q&A)
**UI Inspiration**: Audible + Netflix + Disney+
**Shared Services**: 100% leverage (RAG, Wallet, AI services, etc.)

---

## 👥 Team & Roles

**Product**: Feature prioritization, user testing, metrics
**Engineering**: Backend (FastAPI), Frontend (React), Testing
**Design**: UI/UX, Figma mockups, visual design
**QA**: E2E testing, voice testing, bug tracking

---

## 🎯 Next Steps

1. ✅ **Approve this PRD**
2. Create Figma designs (Home, Player, Voice Q&A)
3. Kickoff meeting with engineering team
4. Week 1: Set up backend + frontend + shared services
5. Week 2-6: Build, test, iterate
6. Launch! 🚀

---

## 📞 Questions?

- **Technical architecture**: See PLANNING.md
- **Shared services**: See SHARED_SERVICES_USAGE.md
- **Task breakdown**: See TASK.md
- **AI comparison**: See EMBEDDING_COMPARISON.md

---

**Last Updated**: 2025-10-24
**Status**: Ready for Development
**Confidence**: High (leveraging proven shared services)

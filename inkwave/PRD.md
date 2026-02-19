# Inkwave - Product Requirements Document (PRD)

**Product Name**: Inkwave
**Version**: 1.0 MVP
**Date**: 2025-10-24
**Status**: Pre-Development
**Document Owner**: Product Team

---

## Executive Summary

Inkwave is a **mobile-first interactive audiobook platform** that transforms passive listening into an active learning experience. Users control narration pacing, engage with an AI voice companion that adapts to their knowledge level, and pay only for what they use through a credit-based system.

### Key Differentiators
- **User-Controlled Pacing**: Tap/swipe to advance, unlike auto-play audiobooks
- **Conversational AI Companion**: Ask questions, get context, discuss themes - all in voice
- **Pay-Per-Use Model**: Fair pricing based on actual usage, no subscriptions
- **Personalized Learning**: AI adapts explanations to user's comprehension level
- **African Languages Ready**: Built on KasaAI's multilingual AI infrastructure

---

## 1. Product Vision

### 1.1 Problem Statement

**Current Audiobook Experience:**
- ❌ Passive consumption with no interaction
- ❌ No way to ask questions or clarify confusion
- ❌ Fixed subscription pricing regardless of usage
- ❌ No personalization based on reading level
- ❌ Limited multilingual support (especially African languages)

**Our Solution:**
- ✅ Interactive reading with AI Q&A companion
- ✅ Voice-based questions and explanations
- ✅ Usage-based pricing (pay for minutes used)
- ✅ Adaptive explanations matching user level
- ✅ Multilingual support via KasaAI's TTS/STT services

### 1.2 Target Users

**Primary Personas:**

1. **The Lifelong Learner** (35-50 years)
   - Reads non-fiction for self-improvement
   - Wants to understand concepts deeply
   - Willing to pay for quality learning experiences
   - Values flexibility and control

2. **The Busy Professional** (28-45 years)
   - Consumes audiobooks during commute
   - Needs quick clarifications without pausing flow
   - Budget-conscious, prefers pay-per-use
   - Time-constrained

3. **The Language Learner** (18-40 years)
   - Reading in non-native language
   - Needs vocabulary/context help
   - Values multilingual support
   - Price-sensitive

**Secondary Personas:**
- Students using textbooks (academic)
- Fiction readers wanting character/plot discussions
- Book clubs seeking discussion prompts

### 1.3 Success Metrics (North Star)

**Primary KPI**: **Average Session Duration** (target: 20+ minutes)
- Indicates engagement with both narration and Q&A

**Supporting KPIs**:
- **D7 Retention Rate**: 40%+ (users returning within 7 days)
- **Q&A Engagement**: 3+ questions per reading session
- **Revenue Per User**: $5+ monthly average
- **Gross Margin**: 50%+ (revenue minus AI costs)

---

## 2. MVP Scope

### 2.1 Core Features (Must-Have)

#### F1: User Authentication
- **Description**: Secure user signup/login via Supabase
- **User Story**: "As a user, I want to create an account and log in securely"
- **Acceptance Criteria**:
  - Email/password signup
  - Social login (Google)
  - JWT-based authentication
  - Password reset flow
- **Priority**: P0 (Critical)

#### F2: Book Library & Discovery
- **Description**: Browse and search available books
- **User Story**: "As a user, I want to browse books by genre and search by title"
- **Acceptance Criteria**:
  - Display book list with cover, title, author, summary
  - Filter by genre, difficulty level
  - Search by title/author
  - Book detail page with metadata (themes, reading time)
  - Free preview (first chapter narration only)
- **Priority**: P0 (Critical)

#### F3: User-Controlled Audio Playback
- **Description**: Interactive audio player with user-paced narration
- **User Story**: "As a user, I want to control reading pace with tap/swipe gestures"
- **Acceptance Criteria**:
  - Play/pause audio
  - Tap screen to advance to next chunk
  - Swipe back to previous chunk
  - Speed control (0.5x - 2x)
  - Visual progress indicator (chapter progress)
  - Bookmark current position
  - Resume from last position
- **Priority**: P0 (Critical)
- **Technical Notes**:
  - Audio delivered in chunks (sentences/paragraphs)
  - Pre-generate TTS audio for narration (cost optimization)
  - Cache audio in CDN

#### F4: Text-Based Q&A with AI
- **Description**: Ask questions about book content via text input
- **User Story**: "As a user, I want to ask questions about what I'm reading and get intelligent answers"
- **Acceptance Criteria**:
  - Text input for questions
  - AI retrieves relevant book passages via RAG (shared service)
  - AI responds with context-aware answers (no spoilers beyond current position)
  - Display conversation history
  - Show estimated cost before asking
  - Real-time cost deduction from wallet
  - Confidence scoring (if low confidence, prompt for clarification)
- **Priority**: P0 (Critical)
- **Technical Notes**:
  - Use shared RAGService for semantic search
  - Use shared UsageCalculator for cost tracking
  - Use shared WalletService for charging

#### F5: Credit-Based Wallet System
- **Description**: Prepaid wallet for usage-based billing
- **User Story**: "As a user, I want to top up my wallet and track spending transparently"
- **Acceptance Criteria**:
  - Display wallet balance prominently
  - Top-up options: $5, $10, $25, $50
  - Payment via Stripe (international) or Paystack (Africa)
  - Transaction history with details (type, amount, timestamp)
  - Low balance warning (< 5 minutes remaining)
  - Real-time cost display during interactions
- **Priority**: P0 (Critical)
- **Technical Notes**:
  - Use shared WalletService (Stripe/Paystack integration)
  - Idempotency for duplicate charge prevention

#### F6: Basic User Profile
- **Description**: User preferences for personalized experience
- **User Story**: "As a user, I want to set my reading preferences"
- **Acceptance Criteria**:
  - Select preferred TTS voice
  - Set default playback speed
  - Set reading level (beginner/intermediate/advanced)
  - Set explanation depth (brief/detailed)
- **Priority**: P1 (High)

### 2.2 Features Explicitly Out of Scope for MVP

- ❌ Voice input (STT) for questions - **Phase 2**
- ❌ Voice output (TTS) for AI responses - **Phase 2**
- ❌ PDF upload by users - **Phase 2**
- ❌ Native mobile apps - **Phase 2** (MVP is PWA)
- ❌ Offline mode - **Phase 3**
- ❌ Background playback - **Phase 3**
- ❌ Social features (sharing, book clubs) - **Phase 3**
- ❌ Personalized recommendations - **Phase 3**
- ❌ Multiple language support - **Phase 3** (English only for MVP)

### 2.3 MVP Timeline

**Total Duration**: 6 weeks

| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1 | Project Setup | Backend/frontend structure, DB setup, auth integration |
| 2 | Book Management | Book CRUD, library UI, search/filter |
| 3 | Wallet System | Wallet integration (shared service), payment flow |
| 4 | Audio Playback | Reading session, TTS integration, audio player UI |
| 5-6 | Q&A System | RAG integration, interaction flow, testing |
| 6 | MVP Launch | Deployment, documentation, initial user testing |

---

## 3. User Flows

### 3.1 New User Onboarding

```
1. Land on homepage
2. Click "Get Started"
3. Sign up (email or Google)
4. Auto-credit $2 free trial credits
5. Browse library
6. Select book → View detail
7. Click "Start Reading"
8. Audio player loads → Narration begins
9. Tooltip: "Tap to advance, swipe to go back"
10. User advances through first chapter (free)
```

### 3.2 Reading & Interaction Flow

```
1. User logs in
2. Dashboard shows: "Continue Reading: [Last Book]"
3. Click book → Audio player loads at saved position
4. User listens and taps to advance
5. User has question → Clicks "Ask" button
6. Modal opens: "What's your question?"
7. User types question
8. System shows: "Estimated cost: $0.08"
9. User clicks "Ask"
10. AI retrieves relevant passages (RAG)
11. AI responds with answer (text)
12. Wallet debited in real-time
13. User can follow up or resume reading
14. User can bookmark position
15. User exits → Position saved automatically
```

### 3.3 Wallet Top-Up Flow

```
1. User sees low balance warning: "< 5 minutes remaining"
2. Clicks "Top Up"
3. Selects amount: $5 / $10 / $25 / $50
4. Selects payment method: Stripe / Paystack
5. Redirected to payment gateway
6. Completes payment
7. Redirected back → Success message
8. Wallet balance updated instantly
9. Can resume reading
```

---

## 4. Functional Requirements

### 4.1 Authentication (Supabase)

**FR-AUTH-001**: System shall support email/password signup
**FR-AUTH-002**: System shall support Google OAuth login
**FR-AUTH-003**: System shall issue JWT tokens valid for 7 days
**FR-AUTH-004**: System shall support password reset via email
**FR-AUTH-005**: System shall create default user profile on first login
**FR-AUTH-006**: System shall create wallet with $2 free credits on signup

### 4.2 Book Management

**FR-BOOK-001**: System shall display book library with pagination (20 books/page)
**FR-BOOK-002**: System shall support filtering by genre, difficulty, language
**FR-BOOK-003**: System shall support search by title and author
**FR-BOOK-004**: System shall display book metadata: title, author, cover, summary, themes, estimated reading time
**FR-BOOK-005**: System shall provide free preview (first chapter narration only)
**FR-BOOK-006**: System shall process books using shared DocumentProcessor (admin-only for MVP)
**FR-BOOK-007**: System shall generate embeddings via shared RAGService

### 4.3 Reading Experience

**FR-READ-001**: System shall deliver audio in chunks (sentences or paragraphs)
**FR-READ-002**: System shall support play/pause controls
**FR-READ-003**: System shall advance chunk on user tap
**FR-READ-004**: System shall go back on user swipe
**FR-READ-005**: System shall support speed control (0.5x, 1x, 1.5x, 2x)
**FR-READ-006**: System shall display visual progress (current chapter, % complete)
**FR-READ-007**: System shall allow bookmarking current position
**FR-READ-008**: System shall auto-save position every 30 seconds
**FR-READ-009**: System shall resume from last position on return
**FR-READ-010**: System shall charge $0.02 per minute of narration

### 4.4 Q&A Interaction

**FR-QA-001**: System shall accept text input for questions
**FR-QA-002**: System shall retrieve relevant book passages via shared RAGService
**FR-QA-003**: System shall use current reading position as context
**FR-QA-004**: System shall filter results to prevent spoilers (only content before current position)
**FR-QA-005**: System shall generate AI response using LLM (OpenAI/Anthropic)
**FR-QA-006**: System shall include user profile (reading level) in prompt
**FR-QA-007**: System shall display confidence score for retrieval
**FR-QA-008**: System shall prompt for clarification if confidence < 0.7
**FR-QA-009**: System shall calculate cost via shared UsageCalculator:
- RAG query: $0.05 per 1,000 tokens (input + output)
- LLM processing: per provider pricing
**FR-QA-010**: System shall debit wallet via shared WalletService before responding
**FR-QA-011**: System shall display conversation history
**FR-QA-012**: System shall support follow-up questions with context

### 4.5 Wallet & Billing

**FR-WALLET-001**: System shall display wallet balance in header (all pages)
**FR-WALLET-002**: System shall support top-up via Stripe (international) using shared WalletService
**FR-WALLET-003**: System shall support top-up via Paystack (Africa) using shared WalletService
**FR-WALLET-004**: System shall show low balance warning when < $1 remaining
**FR-WALLET-005**: System shall prevent interactions when balance = $0
**FR-WALLET-006**: System shall display transaction history (type, amount, description, timestamp)
**FR-WALLET-007**: System shall use idempotency keys to prevent duplicate charges
**FR-WALLET-008**: System shall support refunds via shared WalletService
**FR-WALLET-009**: System shall display estimated cost before charging actions
**FR-WALLET-010**: System shall provide cost breakdown (RAG, LLM, TTS)

### 4.6 User Profile

**FR-PROFILE-001**: System shall store user preferences (voice, speed, reading level)
**FR-PROFILE-002**: System shall allow editing profile settings
**FR-PROFILE-003**: System shall apply preferences to reading experience
**FR-PROFILE-004**: System shall include reading level in AI prompts

---

## 5. Non-Functional Requirements

### 5.1 Performance

**NFR-PERF-001**: API response time p95 < 500ms
**NFR-PERF-002**: TTS generation latency < 2 seconds per chunk
**NFR-PERF-003**: RAG retrieval time < 1 second
**NFR-PERF-004**: Audio player loads within 1 second
**NFR-PERF-005**: Support 100 concurrent users (MVP scale)

### 5.2 Security

**NFR-SEC-001**: All API calls over HTTPS/TLS
**NFR-SEC-002**: JWT tokens signed and verified
**NFR-SEC-003**: Passwords hashed with bcrypt (via Supabase)
**NFR-SEC-004**: Payment data handled by PCI-compliant gateways (Stripe/Paystack)
**NFR-SEC-005**: Rate limiting: 10 requests/minute per user for Q&A
**NFR-SEC-006**: Input sanitization to prevent XSS/SQL injection

### 5.3 Reliability

**NFR-REL-001**: System uptime 99% (MVP target)
**NFR-REL-002**: Automated backups (MongoDB, pgvector) every 24 hours
**NFR-REL-003**: Graceful error handling with user-friendly messages
**NFR-REL-004**: Transaction idempotency to prevent duplicate charges

### 5.4 Scalability

**NFR-SCALE-001**: Database design supports 10,000+ books
**NFR-SCALE-002**: Audio files cached in CDN for fast delivery
**NFR-SCALE-003**: MongoDB indexed for fast queries (books, users, sessions)
**NFR-SCALE-004**: pgvector optimized for vector search (< 1s retrieval)

### 5.5 Usability

**NFR-USE-001**: Mobile-first responsive design (optimized for 375px-430px screens)
**NFR-USE-002**: Touch-optimized UI (tap targets ≥ 44px)
**NFR-USE-003**: Accessible (WCAG AA compliance): screen reader support, keyboard navigation
**NFR-USE-004**: Loading states for all async operations
**NFR-USE-005**: Offline detection with informative message

### 5.6 Maintainability

**NFR-MAINT-001**: 80%+ test coverage (backend)
**NFR-MAINT-002**: API documentation via FastAPI auto-docs
**NFR-MAINT-003**: Code follows PEP8 (Python) and Prettier (TypeScript)
**NFR-MAINT-004**: Modular architecture using shared services

---

## 6. Technical Architecture

### 6.1 System Components

```
┌─────────────────────────────────────────────────────┐
│          FRONTEND (React PWA - Mobile First)        │
│  - Audio player UI                                  │
│  - Q&A interface                                    │
│  - Wallet display                                   │
│  - Book library                                     │
└────────────┬────────────────────────────────────────┘
             │ REST API
             ▼
┌─────────────────────────────────────────────────────┐
│          BACKEND (FastAPI - core_backend)           │
│  URL: https://api.ailabsafrica.com/bookshop/v1/    │
│                                                     │
│  Routes:                                            │
│  ├─ /auth/*         - Authentication                │
│  ├─ /books/*        - Book management               │
│  ├─ /reading/*      - Playback & progress           │
│  ├─ /interaction/*  - Q&A                           │
│  └─ /wallet/*       - Credits & billing             │
│                                                     │
│  Services:                                          │
│  ├─ book_service.py                                 │
│  ├─ reading_service.py                              │
│  ├─ voice_agent.py (LLM + RAG orchestration)       │
│  └─ tts_service.py                                  │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┴───────────┐
    │                    │
    ▼                    ▼
┌──────────────┐  ┌─────────────────┐
│  SHARED      │  │  DATABASES      │
│  SERVICES    │  │                 │
│              │  │  - MongoDB      │
│  ✓ RAGService│  │  - pgvector     │
│  ✓ Document  │  │  - Supabase     │
│    Processor │  │                 │
│  ✓ Wallet    │  └─────────────────┘
│    Service   │
│  ✓ Usage     │
│    Calculator│
└──────────────┘
```

### 6.2 Technology Stack

**Frontend**:
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Zustand (state management)
- Axios (HTTP client)

**Backend**:
- FastAPI (Python 3.11+)
- Pydantic (data validation)
- Motor (async MongoDB)
- Supabase (authentication)

**Shared Services** (apps/shared/integration/):
- RAGService - Semantic search with OpenAI/Gemini embeddings
- DocumentProcessor - PDF/text processing
- WalletService - Payment handling (Stripe/Paystack)
- UsageCalculator - Cost tracking

**Databases**:
- MongoDB - Books, users, sessions, wallets, transactions
- pgvector - Embeddings for RAG
- Supabase PostgreSQL - User authentication

**AI Services**:
- OpenAI GPT-4 / Anthropic Claude (LLM via RAG)
- OpenAI TTS / ElevenLabs (text-to-speech)
- OpenAI Whisper (speech-to-text - Phase 2)

**Infrastructure**:
- Nginx (reverse proxy)
- Systemd (service management)
- S3/MinIO (audio file storage)
- CloudFlare CDN (audio delivery)

### 6.3 Data Models

#### Books (MongoDB)
```python
{
  "_id": ObjectId,
  "title": str,
  "author": str,
  "cover_url": str,
  "metadata": {
    "summary": str,
    "themes": [str],
    "page_count": int,
    "estimated_reading_time_minutes": int,
    "difficulty_level": "beginner" | "intermediate" | "advanced",
    "genre": [str]
  },
  "structure": {
    "chapters": [{
      "title": str,
      "start_chunk_id": int,
      "end_chunk_id": int
    }]
  },
  "processed": bool,
  "created_at": datetime
}
```

#### Book Chunks (MongoDB)
```python
{
  "_id": ObjectId,
  "book_id": ObjectId,
  "chunk_index": int,
  "text": str,
  "text_optimized": str,  # SSML for TTS
  "chapter_id": int,
  "audio_url": str,  # Pre-generated TTS
  "vector_id": str   # Reference to pgvector
}
```

#### Reading Sessions (MongoDB)
```python
{
  "_id": ObjectId,
  "user_id": str,
  "book_id": ObjectId,
  "current_chunk_index": int,
  "current_position_seconds": float,
  "bookmarks": [{
    "chunk_index": int,
    "note": str,
    "created_at": datetime
  }],
  "total_time_spent_minutes": int,
  "last_accessed": datetime
}
```

#### Interactions (MongoDB)
```python
{
  "_id": ObjectId,
  "session_id": ObjectId,
  "user_id": str,
  "book_id": ObjectId,
  "messages": [{
    "role": "user" | "assistant",
    "content": str,
    "timestamp": datetime,
    "tokens_used": int,
    "cost_cents": int
  }],
  "created_at": datetime
}
```

#### Wallets & Transactions
Managed by shared WalletService (see apps/shared/integration/wallet.py)

---

## 7. API Endpoints (MVP)

### 7.1 Authentication
```
POST   /api/bookshop/v1/auth/signup
POST   /api/bookshop/v1/auth/login
POST   /api/bookshop/v1/auth/logout
GET    /api/bookshop/v1/auth/me
```

### 7.2 Books
```
GET    /api/bookshop/v1/books                    # List with pagination
GET    /api/bookshop/v1/books/{book_id}          # Detail
GET    /api/bookshop/v1/books/search?q={query}   # Search
```

### 7.3 Reading
```
POST   /api/bookshop/v1/reading/sessions         # Start session
GET    /api/bookshop/v1/reading/sessions/{id}    # Get session
PUT    /api/bookshop/v1/reading/sessions/{id}    # Update progress
POST   /api/bookshop/v1/reading/sessions/{id}/bookmark
GET    /api/bookshop/v1/reading/chunks/{id}      # Get chunk text
GET    /api/bookshop/v1/reading/chunks/{id}/audio # Get audio
```

### 7.4 Interaction (Q&A)
```
POST   /api/bookshop/v1/interactions             # Start interaction
POST   /api/bookshop/v1/interactions/{id}/messages # Send message
GET    /api/bookshop/v1/interactions/{id}        # Get history
```

### 7.5 Wallet
```
GET    /api/bookshop/v1/wallet                   # Get balance
POST   /api/bookshop/v1/wallet/topup/stripe     # Stripe top-up
POST   /api/bookshop/v1/wallet/topup/paystack   # Paystack top-up
GET    /api/bookshop/v1/wallet/transactions     # History
```

### 7.6 Profile
```
GET    /api/bookshop/v1/profile                  # Get profile
PUT    /api/bookshop/v1/profile                  # Update profile
```

---

## 8. Pricing Strategy (MVP)

### 8.1 Credit Packages
- $5 → 500 credits (100 credits = $1)
- $10 → 1,000 credits
- $25 → 2,500 credits + 100 bonus (4% bonus)
- $50 → 5,000 credits + 300 bonus (6% bonus)

### 8.2 Cost Structure
**Narration**:
- 2 credits per minute ($0.02/min)
- Example: 1-hour book = 120 minutes = 240 credits = $2.40

**Q&A Interaction** (Text-based for MVP):
- Input/Output tokens: 5 credits per 1,000 tokens (~$0.05)
- Average question: 50 tokens input + 200 tokens output = 1.25 credits ($0.0125)
- Example: 10 questions = ~12-15 credits = $0.12-$0.15

### 8.3 Free Trial
- New users: 200 credits free ($2 value)
- Enough for: ~100 minutes of narration OR ~160 Q&A interactions

---

## 9. Success Criteria

### 9.1 MVP Launch Criteria

**Technical**:
- ✅ All P0 features implemented and tested
- ✅ API test coverage > 80%
- ✅ E2E test for complete user flow passes
- ✅ Performance benchmarks met (see NFRs)
- ✅ Security audit passed
- ✅ Deployed to production

**Content**:
- ✅ At least 10 books in library (mix of fiction/non-fiction)
- ✅ All books processed and indexed for RAG

**Documentation**:
- ✅ User guide created
- ✅ API documentation complete
- ✅ Support/FAQ page live

### 9.2 Post-Launch Success Metrics (First 30 Days)

**Acquisition**:
- 100+ signups
- 60%+ signup completion rate

**Engagement**:
- 40%+ D7 retention (users return within 7 days)
- 20+ minutes average session duration
- 3+ Q&A interactions per session average

**Revenue**:
- 30%+ conversion to paid (top-up after free credits)
- $5+ average revenue per paying user
- 50%+ gross margin (revenue - AI costs)

**Technical**:
- 99%+ uptime
- < 5% error rate
- < 3% payment failure rate

---

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **High AI costs** (LLM + TTS) | High | High | Pre-generate TTS audio, optimize prompts, cache responses, set rate limits |
| **Poor RAG accuracy** | Medium | High | Tune chunking strategy, test with diverse books, implement confidence thresholds |
| **TTS latency** | Medium | High | Pre-generate narration audio, use streaming TTS (Phase 2), cache chunks in CDN |
| **Wallet abuse** (negative balance) | Low | High | Real-time balance checks before operations, no credit extension |
| **Low user engagement** | Medium | High | User testing before launch, iterate on UX, implement onboarding flow |
| **Payment gateway failures** | Low | Medium | Support multiple gateways (Stripe + Paystack), retry logic, manual verification |
| **Content copyright issues** | Low | High | Only admin uploads for MVP, implement content verification (Phase 2) |
| **Mobile performance** | Medium | Medium | Optimize bundle size, lazy loading, progressive image loading |

---

## 11. Open Questions & Decisions Needed

### 11.1 Product Decisions
- [ ] **Q1**: What genres should we prioritize for initial 10 books?
  - **Recommendation**: Mix of non-fiction (self-help, business) and fiction (classics)
- [ ] **Q2**: Should we allow free reading without account?
  - **Recommendation**: No - require signup to track usage and prevent abuse
- [ ] **Q3**: Voice selection - how many TTS voices for MVP?
  - **Recommendation**: 2 voices (1 male, 1 female) via OpenAI TTS

### 11.2 Technical Decisions
- [ ] **Q4**: Audio format and bitrate?
  - **Recommendation**: MP3, 64kbps (balance quality vs. storage)
- [ ] **Q5**: RAG embedding model?
  - **Recommendation**: OpenAI text-embedding-3-small (cost-effective, 1536 dimensions)
- [ ] **Q6**: LLM for Q&A?
  - **Recommendation**: OpenAI GPT-4o-mini (balance cost vs. quality)

### 11.3 Business Decisions
- [ ] **Q7**: Pricing - too low or too high?
  - **Action**: A/B test pricing tiers after launch
- [ ] **Q8**: Refund policy?
  - **Recommendation**: 7-day refund for unused credits
- [ ] **Q9**: Free trial amount?
  - **Recommendation**: $2 (200 credits) - enough for 100 minutes or ~160 questions

---

## 12. Phase 2 Preview (Post-MVP)

**Timeline**: 3-4 weeks after MVP launch

**Features**:
- Voice input (STT) for questions
- Voice output (TTS) for AI responses
- WebSocket real-time communication
- User PDF uploads (with processing pipeline)
- Session persistence improvements
- Enhanced user profiles

**Decision Point**: Proceed with Phase 2 only if MVP metrics are met:
- ✅ 40%+ D7 retention
- ✅ 30%+ conversion to paid
- ✅ 50%+ gross margin

---

## 13. Appendix

### 13.1 Glossary

- **Chunk**: A segment of book text (sentence or paragraph) for processing and narration
- **RAG**: Retrieval-Augmented Generation - AI technique for contextual Q&A
- **TTS**: Text-to-Speech - AI voice synthesis
- **STT**: Speech-to-Text - Voice transcription
- **pgvector**: PostgreSQL extension for vector similarity search
- **Credit**: Internal currency (100 credits = $1)

### 13.2 References

- **PLANNING.md**: Detailed technical architecture
- **TASK.md**: Implementation task list
- **Architecture Docs**: `/opt/kasaai/apps/architecture/ARCHITECTURE.md`
- **Shared Services**: `/opt/kasaai/apps/shared/integration/`

### 13.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | Product Team | Initial MVP PRD created |

---

**Approval Required From**:
- [ ] Product Manager
- [ ] Engineering Lead
- [ ] Design Lead
- [ ] Business Owner

**Next Steps**:
1. Review and approve PRD
2. Kickoff meeting with engineering team
3. Sprint planning (Week 1)
4. Begin implementation (see TASK.md)

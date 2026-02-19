# Interactive AI Bookshop - Planning Document

**Project**: Bookshop
**Created**: 2025-10-23
**Status**: Planning Phase

---

## 🎯 Vision

A mobile-first audiobook platform that transforms reading into an interactive, conversational learning experience. Users control the pacing, engage with an AI voice agent that adapts to their knowledge level, and pay only for what they use.

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      MOBILE FRONTEND                         │
│  (React Native / Progressive Web App - Mobile First)         │
│  - Audio player UI                                           │
│  - Voice interaction controls                                │
│  - Wallet/credit display                                     │
│  - Book library & discovery                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ REST/WebSocket API
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    CORE BACKEND (FastAPI)                    │
│  Location: apps/core_backend/                               │
│  Service: kasaai-core-backend.service                       │
│  URL: https://api.ailabsafrica.com                          │
│                                                              │
│  Bookshop Modules:                                           │
│  ├── /bookshop/                                             │
│  │   ├── routes/                                            │
│  │   │   ├── books.py          # CRUD, search, metadata    │
│  │   │   ├── reading.py        # Playback, progress        │
│  │   │   ├── interaction.py    # Q&A, voice agent          │
│  │   │   ├── wallet.py         # Credits API wrapper       │
│  │   │   └── upload.py         # PDF processing workflow   │
│  │   ├── services/                                          │
│  │   │   ├── voice_agent.py    # LLM + TTS orchestration   │
│  │   │   └── tts_service.py    # Audio generation          │
│  │   └── models/                                            │
│  │       ├── book.py           # Book schema               │
│  │       ├── user.py           # User profile schema       │
│  │       └── interaction.py    # Session, message schema   │
│  │                                                           │
│  └── SHARED SERVICES (apps/shared/integration/)             │
│      ├── rag.py                # ✓ RAG knowledge base      │
│      ├── document_processor.py # ✓ PDF/DOCX processing     │
│      ├── wallet.py             # ✓ Payment & credits       │
│      ├── usage_calculator.py   # ✓ Cost tracking           │
│      ├── vapi.py               # ✓ Voice AI (optional)     │
│      └── voice-lab/            # ✓ TTS/STT services        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│   MongoDB    │ │ pgvector │ │   Supabase  │
│              │ │   (RAG)  │ │   (Auth)    │
│ - Books      │ │          │ │             │
│ - Users      │ │ - Book   │ │ - User auth │
│ - Wallets    │ │   chunks │ │ - Sessions  │
│ - Sessions   │ │ - Embed. │ │             │
└──────────────┘ └──────────┘ └─────────────┘

External Services:
├── OpenAI / Anthropic (LLM for Q&A via shared RAG)
├── ElevenLabs / OpenAI TTS (Voice synthesis via voice-lab)
└── Payment Gateway (Stripe/Paystack via shared wallet)
```

### Shared Services Integration

The bookshop leverages KasaAI's shared services library for common functionality:

**✓ RAG Service** (`apps/shared/integration/rag.py`)
- Vector-based semantic search for book Q&A
- Provider-agnostic (OpenAI, Gemini, Anthropic)
- Confidence scoring and escalation logic
- Full knowledge base CRUD operations

**✓ Document Processor** (`apps/shared/integration/document_processor.py`)
- Multi-format support: PDF, DOCX, TXT
- 4 intelligent chunking strategies
- Metadata extraction (author, page count, word count)
- Async batch processing with concurrency control

**✓ Wallet Service** (`apps/shared/integration/wallet.py`)
- Complete wallet management (credit, debit, refund)
- Payment gateway integration (Paystack, Stripe)
- Transaction auditing with idempotency
- Multi-currency support (USD, GHS, EUR, etc.)

**✓ Usage Calculator** (`apps/shared/integration/usage_calculator.py`)
- Real-time cost tracking for RAG queries, TTS, STT
- Multiple pricing tiers (Free, Basic, Premium)
- Detailed cost breakdowns and analytics

**Benefits:**
- ✅ No need to build PDF processing from scratch
- ✅ Battle-tested RAG with confidence scoring
- ✅ Secure payment handling with audit trails
- ✅ Consistent cost calculation across platform

---

## 📱 Core Features

### 1. Book Management

#### 1.1 Browse & Discovery
- **Browse library** with filters (genre, length, difficulty)
- **Search** by title, author, topic, themes
- **Book preview**: AI-generated summary, key themes, estimated reading time
- **Sample listen**: First chapter free (limited to narration only)

#### 1.2 PDF Upload & Processing
**Flow**:
1. User uploads PDF
2. Backend processes using **shared DocumentProcessor**:
   - Text extraction via `document_processor.process_file()`
   - Automatic metadata extraction (author, page count, word count)
   - Smart chunking (4 strategies: Recursive, Sentence-aware, Paragraph-aware, Fixed-size)
   - Content cleanup and normalization
3. RAG indexing using **shared RAGService**:
   - Initialize knowledge base per book with `rag_service.initialize_knowledge_base()`
   - Vector embedding generation (OpenAI/Gemini)
   - Store in pgvector for semantic search
4. Auto-metadata generation (LLM):
   - Summary (250 words)
   - Key themes/topics (5-10 tags)
   - Character list (if fiction)
   - Reading time estimate
   - Difficulty level
5. Cost calculation using **shared UsageCalculator**:
   - User charged one-time processing fee via `wallet_service.debit()`
   - Fee based on: page count, file size
6. Book added to library with "Processing" status → "Ready"

**Shared Services Used**:
- **DocumentProcessor** - Multi-format text extraction and chunking
- **RAGService** - Vector embeddings and knowledge base indexing
- **WalletService** - Processing fee deduction with audit trail
- **UsageCalculator** - Cost calculation for document processing

---

### 2. Interactive Reading Experience

#### 2.1 User-Controlled Playback
- **Tap/swipe to advance**: User controls reading pace
- **Audio player controls**: Play, pause, skip forward/back (by sentence/paragraph)
- **Speed control**: 0.5x - 2x
- **Voice selection**: Multiple TTS voices (male/female, accents)
- **Visual progress**: Chapter map, scroll indicator, time remaining
- **Bookmarks & notes**: Save positions, add text notes

#### 2.2 Conversational Q&A
**Interaction Flow**:
1. User pauses and asks question (voice or text)
2. System uses **shared RAGService**:
   - Captures current reading context (last 2-3 chunks)
   - Performs semantic search via `rag_service.query_knowledge_base()`
   - Retrieves top-k relevant book passages with confidence scoring
   - Includes user profile metadata (reading history, comprehension level)
   - Filters to prevent spoilers (only content before current position)
3. LLM generates response with context:
   ```
   You are a personalized book companion. The user is reading [Book Title].
   Current context: [Last passages read]
   Relevant book content: [RAG results from shared service]
   User profile: [Learning preferences, past interactions]

   Answer the user's question with:
   - Clear, adaptive explanations (match their level)
   - Direct book references (page/chapter)
   - No spoilers beyond current reading position
   ```
4. Response → TTS (voice-lab) → Audio delivered
5. **UsageCalculator** tracks costs:
   - RAG query cost (tokens, retrieval)
   - LLM processing cost
   - TTS generation cost
6. **WalletService** debits user wallet in real-time
7. User can follow up, ask for clarification, or resume reading

**Personalization Features**:
- **Memory**: Store user interactions, preferences (MongoDB)
- **Adaptive explanations**: Track comprehension signals (follow-up questions, confusion markers)
- **Learning profile**: Reading level, favorite genres, discussion depth preference
- **Session continuity**: Remember context across reading sessions
- **Confidence-based escalation**: If RAG confidence < 0.7, prompt user for clarification

**Shared Services Used**:
- **RAGService** - Semantic search with confidence scoring
- **UsageCalculator** - Real-time cost tracking
- **WalletService** - Automatic debit with transaction history

#### 2.3 Session Management
- **WebSocket connection** for real-time voice interaction
- **Session state**: Current position, active context, conversation history
- **Graceful reconnection**: Resume from exact position
- **Background playback**: Continue audio when app backgrounded (mobile)

---

### 3. Wallet & Usage-Based Pricing

**Built on Shared Wallet & Usage Calculator Services**

#### 3.1 Credit System (via WalletService)
- **Wallet balance** displayed prominently via `wallet_service.get_balance()`
- **Top-up options**: $5, $10, $25, $50 via payment gateways:
  - Stripe (international) via `wallet_service.initiate_stripe_topup()`
  - Paystack (Africa) via `wallet_service.initiate_paystack_topup()`
- **Low balance warnings**: Alert when < 5 minutes remaining
  - Automatic detection via `wallet.is_low_balance` property
  - Configurable threshold per user
- **Usage transparency**: Real-time cost display during interaction
- **Transaction history**: Full audit trail via `wallet_service.get_transactions()`
- **Idempotency**: Duplicate charges prevented automatically

#### 3.2 Pricing Structure (via UsageCalculator)

**Reading (Narration)**:
- $0.02 per minute of narration
- Charged in 30-second increments via `usage_calculator.calculate_tts_cost()`
- No charge when paused

**Q&A Interaction**:
- Voice input (STT): $0.01 per 15 seconds via `usage_calculator.calculate_stt_cost()`
- LLM processing: $0.05 per 1,000 tokens via `usage_calculator.calculate_rag_cost()`
  - Includes input + output tokens
  - Provider-specific pricing (OpenAI/Gemini/Anthropic)
- TTS output: $0.03 per minute via `usage_calculator.calculate_tts_cost()`

**Book Processing** (one-time):
- $0.50 per 50 pages (for PDF uploads)
- Calculated via `usage_calculator.calculate_document_processing_cost()`
- Based on page count AND file size (takes higher cost)
- Free for pre-processed books in library

**Pricing Tiers**:
- **Free**: $2 credit on signup, first chapter access
- **Basic**: Standard rates (as above)
- **Premium**: 20% discount on all services
- **Enterprise**: 40% discount, custom pricing

#### 3.3 Usage Tracking & Billing

**Shared Services Architecture**:
```python
# Real-time cost tracking
usage_calculator = UsageCalculator(tier=user.pricing_tier)

# Calculate costs
rag_cost = usage_calculator.calculate_rag_cost(
    input_tokens=500, output_tokens=200, num_queries=1
)
tts_cost = usage_calculator.calculate_tts_cost(
    num_characters=len(response), provider="elevenlabs"
)

# Debit wallet with idempotency
await wallet_service.debit(
    wallet_id=user.wallet_id,
    amount=rag_cost.total_cost + tts_cost.total_cost,
    description=f"Q&A: {book.title}",
    idempotency_key=f"interaction-{interaction_id}",
    metadata={"book_id": book.id, "session_id": session.id}
)
```

**Storage**:
- **Wallets**: Managed by shared WalletService (MongoDB)
- **Transactions**: Full audit trail with timestamps, amounts, metadata
- **Usage metrics**: Tracked by UsageCalculator per service type
- **Cost breakdown**: Available via `usage_calculator.get_cost_breakdown()`

**Benefits**:
- ✅ Automated cost calculation with configurable pricing tiers
- ✅ Secure payment handling with idempotency
- ✅ Detailed transaction audit trail
- ✅ Real-time balance updates with low-balance alerts
- ✅ Support for multiple currencies (USD, GHS, EUR, GBP)

---

## 🗄️ Database Schema

### MongoDB Collections

#### `books`
```python
{
  "_id": ObjectId,
  "title": str,
  "author": str,
  "isbn": str (optional),
  "cover_url": str,
  "pdf_url": str,  # Original PDF (S3/MinIO)
  "processed": bool,
  "processing_status": "pending" | "processing" | "ready" | "failed",
  "metadata": {
    "summary": str,
    "themes": [str],
    "characters": [str],  # Fiction only
    "page_count": int,
    "word_count": int,
    "estimated_reading_time_minutes": int,
    "difficulty_level": "beginner" | "intermediate" | "advanced",
    "genre": [str],
    "language": str
  },
  "structure": {
    "chapters": [
      {
        "title": str,
        "start_chunk_id": int,
        "end_chunk_id": int,
        "word_count": int
      }
    ]
  },
  "uploaded_by": str (user_id),
  "created_at": datetime,
  "updated_at": datetime
}
```

#### `book_chunks` (indexed for fast lookup)
```python
{
  "_id": ObjectId,
  "book_id": ObjectId,
  "chunk_index": int,  # Sequential order
  "text": str,  # Original text
  "text_optimized": str,  # SSML-enhanced for TTS
  "chapter_id": int,
  "vector_id": str,  # Reference to pgvector entry
  "word_count": int,
  "created_at": datetime
}
```

#### `users`
```python
{
  "_id": str (Supabase user_id),
  "email": str,
  "display_name": str,
  "profile": {
    "preferred_voice": str,
    "playback_speed": float,
    "reading_level": "beginner" | "intermediate" | "advanced",
    "interaction_preferences": {
      "explanation_depth": "brief" | "detailed",
      "discussion_topics": ["themes", "characters", "context", ...]
    }
  },
  "created_at": datetime,
  "last_active": datetime
}
```

#### `wallets`
```python
{
  "_id": ObjectId,
  "user_id": str,
  "balance_cents": int,  # Store as cents to avoid float issues
  "currency": "USD",
  "created_at": datetime,
  "updated_at": datetime
}
```

#### `wallet_transactions`
```python
{
  "_id": ObjectId,
  "wallet_id": ObjectId,
  "type": "topup" | "charge" | "refund",
  "amount_cents": int,
  "balance_after_cents": int,
  "description": str,  # e.g., "Top-up via Stripe", "Reading: Book Title"
  "metadata": {
    "payment_id": str (optional),
    "usage_log_id": ObjectId (optional)
  },
  "created_at": datetime
}
```

#### `reading_sessions`
```python
{
  "_id": ObjectId,
  "user_id": str,
  "book_id": ObjectId,
  "current_chunk_index": int,
  "current_position_seconds": float,  # Position within current chunk audio
  "bookmarks": [
    {
      "chunk_index": int,
      "position_seconds": float,
      "note": str (optional),
      "created_at": datetime
    }
  ],
  "total_time_spent_minutes": int,
  "started_at": datetime,
  "last_accessed": datetime,
  "completed": bool
}
```

#### `interactions`
```python
{
  "_id": ObjectId,
  "session_id": ObjectId,
  "user_id": str,
  "book_id": ObjectId,
  "chunk_context": [int],  # Chunk indices in context
  "messages": [
    {
      "role": "user" | "assistant",
      "content": str,
      "audio_url": str (optional),
      "timestamp": datetime,
      "tokens_used": int (optional)
    }
  ],
  "created_at": datetime,
  "updated_at": datetime
}
```

#### `usage_logs`
```python
{
  "_id": ObjectId,
  "user_id": str,
  "session_id": ObjectId,
  "book_id": ObjectId,
  "type": "narration" | "voice_input" | "llm_processing" | "tts_output" | "pdf_processing",
  "duration_seconds": float (optional),
  "tokens_used": int (optional),
  "cost_cents": int,
  "timestamp": datetime,
  "metadata": {
    "chunk_index": int (optional),
    "model": str (optional, e.g., "gpt-4", "eleven_labs")
  }
}
```

### pgvector Schema

#### `book_embeddings`
```sql
CREATE TABLE book_embeddings (
  id SERIAL PRIMARY KEY,
  book_id VARCHAR(255),  -- MongoDB ObjectId as string
  chunk_index INT,
  embedding VECTOR(384),  -- sentence-transformers/all-MiniLM-L6-v2
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON book_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON book_embeddings (book_id);
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React Native (Expo) or PWA (React + Vite)
- **Mobile-first**: Optimized for iOS/Android, responsive for tablets
- **Audio**: Expo AV / react-native-sound
- **Voice input**: Expo Speech / Web Speech API
- **State**: Zustand or React Context
- **API**: Axios + WebSocket (socket.io-client)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Location**: `apps/core_backend/bookshop/`
- **Service**: kasaai-core-backend.service
- **WebSocket**: python-socketio (for real-time interaction)
- **Task queue**: Celery + Redis (for async PDF processing)

### Shared Services (apps/shared/integration/)
- **RAG Service**: `rag.py` - Provider-agnostic vector search (OpenAI/Gemini/Anthropic + LangChain + pgvector)
- **Document Processor**: `document_processor.py` - Multi-format text extraction (PyPDF2/pdfplumber/python-docx)
- **Wallet Service**: `wallet.py` - Payment management (Paystack/Stripe + MongoDB + motor)
- **Usage Calculator**: `usage_calculator.py` - Cost tracking with tiered pricing
- **Voice Lab**: TTS/STT services (Coqui XTTS, Whisper, ElevenLabs)

### Databases
- **MongoDB**: Books, users, sessions, wallets (via shared WalletService), usage logs
- **pgvector**: RAG embeddings (via shared RAGService)
- **Supabase**: Authentication

### AI/ML Services (via Shared Services)
- **LLM**: OpenAI GPT-4 / Gemini / Anthropic Claude (via shared RAGService)
- **TTS**: ElevenLabs / OpenAI TTS / Coqui XTTS (via voice-lab)
- **STT**: OpenAI Whisper (via voice-lab)
- **Embeddings**: OpenAI / Gemini (via shared RAGService)

### Infrastructure
- **Storage**: S3 / MinIO (PDFs, audio cache)
- **CDN**: CloudFlare (audio delivery)
- **Payments**: Paystack (Africa) / Stripe (international) - via shared WalletService

### Key Dependencies
```
# Shared services
apps.shared.integration.rag
apps.shared.integration.document_processor
apps.shared.integration.wallet
apps.shared.integration.usage_calculator

# Backend
fastapi>=0.104.0
python-socketio>=5.10.0
celery>=5.3.0
redis>=5.0.0
motor>=3.3.0  # Async MongoDB
```

---

## 🚀 Development Phases

### Phase 1: MVP (4-6 weeks)
**Goal**: Prove the core interaction concept

**Features**:
- [ ] User auth (Supabase)
- [ ] Basic book CRUD (admin uploads pre-processed books)
- [ ] Simple audio playback (tap to advance)
- [ ] Basic Q&A (text input → LLM → text output)
- [ ] Wallet system (manual top-up, usage tracking)
- [ ] Mobile-responsive web app

**Tech**:
- PWA (React + Vite)
- FastAPI backend
- MongoDB + pgvector
- OpenAI GPT-4 + TTS

### Phase 2: Enhanced Interaction (3-4 weeks)
**Features**:
- [ ] Voice input (STT)
- [ ] Voice output (TTS)
- [ ] WebSocket real-time communication
- [ ] RAG-powered Q&A (contextual retrieval)
- [ ] Session persistence (bookmarks, progress)
- [ ] User profiles (voice preference, reading level)

### Phase 3: PDF Processing (3-4 weeks)
**Features**:
- [ ] PDF upload flow
- [ ] Async processing pipeline (Celery)
- [ ] OCR support
- [ ] Smart chunking
- [ ] Auto-metadata generation
- [ ] Processing status tracking

### Phase 4: Personalization (2-3 weeks)
**Features**:
- [ ] Interaction memory (store past Q&A)
- [ ] Adaptive learning level
- [ ] Reading history analysis
- [ ] Personalized recommendations
- [ ] Custom reading preferences

### Phase 5: Scaling & Polish (3-4 weeks)
**Features**:
- [ ] Native mobile apps (React Native)
- [ ] Audio caching & optimization
- [ ] Multi-voice support
- [ ] Background playback
- [ ] Offline mode (downloaded books)
- [ ] Analytics dashboard (admin)
- [ ] Payment gateway integration (Stripe/Flutterwave)

---

## 📊 Key Metrics to Track

### User Engagement
- Daily active users (DAU)
- Average session duration
- Books completed per user
- Q&A interactions per session
- Retention rate (D1, D7, D30)

### Business Metrics
- Average revenue per user (ARPU)
- Top-up frequency
- Cost per interaction (LLM + TTS)
- Gross margin (revenue - AI costs)
- Conversion rate (free → paid)

### Technical Metrics
- PDF processing time
- RAG retrieval accuracy
- TTS latency (< 2 seconds target)
- WebSocket connection stability
- API response time (p95 < 500ms)

---

## 🔒 Security & Privacy

- **Data encryption**: TLS for all API calls, encrypted storage for sensitive data
- **PII protection**: Minimal data collection, comply with GDPR/CCPA
- **Payment security**: PCI-compliant (use Stripe/Flutterwave SDKs)
- **Content moderation**: Filter inappropriate uploads (title/content checks)
- **Rate limiting**: Prevent abuse (API rate limits, wallet minimum balance)

---

## 🎨 Design Principles

1. **Mobile-first**: Touch-optimized, minimal UI clutter
2. **Voice-forward**: Voice interactions should feel natural, not robotic
3. **Transparent pricing**: Always show cost before/during interaction
4. **Non-intrusive**: User controls all interactions (no auto-play, no interruptions)
5. **Accessible**: Support screen readers, high contrast, text sizing

---

## 📝 Naming Conventions

### File Structure
```
apps/core_backend/bookshop/
├── routes/
│   ├── books.py              # CRUD, search, metadata
│   ├── reading.py            # Playback, progress tracking
│   ├── interaction.py        # Q&A orchestration
│   ├── wallet.py             # Wallet API wrapper (uses shared service)
│   └── upload.py             # PDF processing workflow
├── services/
│   ├── voice_agent.py        # LLM + TTS orchestration
│   └── tts_service.py        # Audio generation wrapper
├── models/
│   ├── book.py               # Book schema
│   ├── user.py               # User profile schema
│   ├── interaction.py        # Session, message schema
│   └── session.py            # Reading session schema
├── tasks/  # Celery tasks
│   └── process_pdf.py        # Async PDF processing
└── config.py

# Shared services (referenced, not duplicated)
apps/shared/integration/
├── rag.py                    # ✓ Used for book Q&A
├── document_processor.py     # ✓ Used for PDF upload
├── wallet.py                 # ✓ Used for payments
├── usage_calculator.py       # ✓ Used for cost tracking
├── vapi.py                   # Optional: voice AI
└── voice-lab/                # ✓ Used for TTS/STT
```

### Code Style
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`
- **Routes**: `/api/bookshop/v1/resource`

---

## 🧪 Testing Strategy

### Unit Tests (`/tests`)
- **Services**: Mock external APIs (LLM, TTS, STT)
- **Utilities**: Test chunking logic, cost calculations
- **Models**: Test Pydantic validation

### Integration Tests
- **API endpoints**: Test full request/response cycles
- **Database**: Test CRUD operations with test MongoDB
- **RAG**: Test retrieval accuracy with sample book

### E2E Tests
- **User flows**: Sign up → browse → read → ask question → pay
- **WebSocket**: Test real-time interaction flow
- **PDF processing**: Upload → process → read pipeline

---

## 🐛 Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| High LLM costs | Business | Rate limiting, optimize prompts, use caching, consider fine-tuned models |
| TTS latency | UX | Pre-generate audio for narration, use streaming TTS for Q&A, cache responses |
| Poor RAG retrieval | UX | Tune chunking strategy, experiment with embeddings, hybrid search (keyword + semantic) |
| Wallet abuse (negative balance) | Financial | Pre-charge for interactions, hard stop when balance = 0, fraud detection |
| PDF processing failures | UX | Robust error handling, manual review queue, refund processing fees |
| User privacy concerns | Legal | Clear privacy policy, minimal data retention, allow data deletion |

---

## 📚 References & Inspiration

- **Audible/Spotify**: Audiobook UX patterns
- **ChatGPT voice mode**: Natural conversational AI
- **Blinkist**: Book summaries & metadata
- **LangChain/LlamaIndex**: RAG best practices
- **OpenAI Cookbook**: Prompt engineering, embeddings

---

**Next Steps**: See `TASK.md` for implementation tasks.

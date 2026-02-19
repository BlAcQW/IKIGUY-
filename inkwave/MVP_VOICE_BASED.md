# Inkwave MVP - Voice-Based Interactive Audiobook Platform

**Version**: 1.0 MVP (Voice-First)
**Timeline**: 6 weeks
**Status**: Pre-Development
**Last Updated**: 2025-10-24

---

## 🎯 Vision

A **voice-first interactive audiobook platform** with a beautiful, premium interface inspired by Audible, Netflix, and Disney+. Users experience immersive storytelling with an AI companion they can talk to.

**"Listen, ask, and learn - all by voice"**

---

## ✨ Key Changes from Original Plan

### ❌ Original MVP (Text-based)
- Text Q&A input
- Text AI responses
- Basic UI

### ✅ New MVP (Voice-First)
- **Voice Q&A input** (STT via Whisper)
- **Voice AI responses** (TTS via Coqui/OpenAI)
- **Voice narration** (pre-generated TTS)
- **Premium UI** (Audible/Netflix/Disney+ inspired)
- **Gemini 2.0 Flash** for RAG (instead of OpenAI)

---

## 🎨 UI/UX Design Philosophy

### Inspiration Sources

**Audible** ✅
- Clean audiobook player
- Chapter navigation
- Speed controls
- Sleep timer

**Netflix** ✅
- Hero banner with featured book
- Horizontal scrolling shelves
- "Continue Reading" section
- Personalized recommendations

**Disney+** ✅
- Premium visual design
- Smooth animations
- Immersive full-screen player
- High-quality cover art

### Design Principles
1. **Mobile-first** - Thumb-friendly, touch-optimized
2. **Dark mode default** - Easier on eyes during long sessions
3. **Minimalist** - Content takes center stage
4. **Smooth transitions** - Polished, premium feel
5. **Voice-forward** - Large, clear "Ask" button

---

## ✅ MVP Features (Voice-Based)

### 1. User Authentication
- Email/password signup
- Google OAuth login
- $2 free trial credits on signup

### 2. Beautiful Home Screen (Netflix-style)

**Hero Banner**:
- Featured book with stunning cover art
- Play button overlay
- Book summary
- "Add to Library" button

**Content Shelves**:
```
┌──────────────────────────────────────────────┐
│  Continue Reading                         →  │
│  ┌──┐  ┌──┐  ┌──┐  ┌──┐                      │
│  │  │  │  │  │  │  │  │                      │
│  └──┘  └──┘  └──┘  └──┘                      │
├──────────────────────────────────────────────┤
│  Recommended for You                      →  │
│  ┌──┐  ┌──┐  ┌──┐  ┌──┐                      │
│  │  │  │  │  │  │  │  │                      │
│  └──┘  └──┘  └──┘  └──┘                      │
├──────────────────────────────────────────────┤
│  Bestsellers                              →  │
│  ┌──┐  ┌──┐  ┌──┐  ┌──┐                      │
│  │  │  │  │  │  │  │  │                      │
│  └──┘  └──┘  └──┘  └──┘                      │
└──────────────────────────────────────────────┘
```

**Features**:
- Horizontal scrolling shelves
- Hover effects on covers
- Progress bars on "Continue Reading"
- "New" badges on recently added books

### 3. Immersive Audio Player

**Full-Screen Player**:
```
┌──────────────────────────────────────────────┐
│                                              │
│              [Book Cover Art]                │
│                                              │
│           The Lean Startup                   │
│           by Eric Ries                       │
│                                              │
│     ═══════════●═════════                    │
│     12:34          1:45:22                   │
│                                              │
│     [◄◄] [▶/❙❙] [►►]     [1.0x]             │
│                                              │
│     ┌───────────────────────────┐            │
│     │   🎙️ Ask a Question       │  ← Large  │
│     └───────────────────────────┘            │
│                                              │
│     Chapter 3: Validated Learning            │
│     Progress: 42% complete                   │
│                                              │
└──────────────────────────────────────────────┘
```

**Controls**:
- Play/Pause (large center button)
- Skip 15s back/forward
- Chapter navigation
- Speed control (0.5x - 2x)
- Sleep timer (optional)
- **Voice Q&A button** (prominent)

**Visual Feedback**:
- Animated waveform during playback
- Glowing "Ask" button when available
- Smooth progress bar animation
- Haptic feedback on interactions

### 4. Voice-Based Q&A System

**User Flow**:
1. User taps **"🎙️ Ask"** button
2. **Voice recording UI** appears:
   ```
   ┌────────────────────────────┐
   │                            │
   │      🎙️ Listening...       │
   │                            │
   │     [Waveform Animation]   │
   │                            │
   │    "What does this mean?"  │  ← Live transcription
   │                            │
   │    [Tap to stop] or auto   │
   └────────────────────────────┘
   ```
3. **STT** (Whisper) transcribes voice → text
4. **Gemini 2.0 Flash RAG** retrieves context + generates answer
5. **TTS** (Coqui/OpenAI) converts answer → voice
6. **AI speaks** the answer (with animated avatar)
7. User can **follow up** or resume reading

**Voice Q&A UI**:
- Large waveform visualization during recording
- Live transcription (STT in real-time)
- "Thinking..." animation while RAG processes
- AI avatar with lip-sync animation (optional MVP+)
- Audio playback with controls (pause/replay)
- Cost displayed: "This cost $0.08"

**Conversation History** (slide-up drawer):
- List of Q&A exchanges
- Tap to replay any answer
- Timestamps
- Cost per interaction

### 5. Credit-Based Wallet (Integrated UI)

**Wallet Display** (top-right header):
```
┌────────────────┐
│ 💰 $12.45      │  ← Balance
└────────────────┘
```

**Low Balance Banner** (when < $1):
```
┌──────────────────────────────────────────────┐
│ ⚠️ Low balance! Top up to continue reading → │
└──────────────────────────────────────────────┘
```

**Top-Up Page** (beautiful cards):
```
┌──────────────────────────────────────────────┐
│                                              │
│          Choose Your Top-Up                  │
│                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │ $5   │  │ $10  │  │ $25  │  │ $50  │     │
│  │      │  │      │  │ +4%  │  │ +6%  │     │
│  │ 500  │  │ 1k   │  │ 2.6k │  │ 5.3k │     │
│  │credits│  │credits│  │credits│  │credits│     │
│  └──────┘  └──────┘  └──────┘  └──────┘     │
│                                              │
│  Payment Method:                             │
│  [ ] Stripe (Card)                           │
│  [ ] Paystack (M-Pesa, Bank)                 │
│                                              │
│  [  Proceed to Payment  ]                    │
│                                              │
└──────────────────────────────────────────────┘
```

### 6. User Profile

**Settings Page** (minimalist):
- Profile picture
- Preferred TTS voice (demo buttons)
- Playback speed default
- Reading level (beginner/intermediate/advanced)
- Dark mode toggle (default: on)
- Notification preferences

---

## 🏗️ Tech Stack (Voice-Based)

### Frontend
- **Framework**: React + TypeScript + Vite
- **UI Library**: Tailwind CSS + Headless UI
- **Animations**: Framer Motion
- **Audio**: Web Audio API
- **Voice**: Web Speech API (STT) + Audio playback
- **State**: Zustand
- **Icons**: Heroicons or Lucide

### Backend (Using Shared Services)
- **Framework**: FastAPI
- **Location**: `@apps/core_backend/bookshop/`
- **URL**: https://api.ailabsafrica.com/bookshop/v1/

### Shared Services

#### 1. **RAGService** (`@apps/shared/integration/rag.py`)
**Configuration for Inkwave**:
```python
rag_config = RAGConfig(
    ai_provider="gemini",  # ✅ As requested
    api_key=os.getenv("GOOGLE_API_KEY"),
    embedding_model="text-embedding-004",  # Gemini embeddings
    llm_model="gemini-2.0-flash-exp",  # ✅ Gemini 2.0 Flash
    retrieval_k=5,
    confidence_threshold=0.7,
    temperature=0.1
)
```

#### 2. **AI Provider Service** (`@apps/shared/integration/ai_services/`)
**TTS Providers** (for narration + Q&A responses):
- Coqui XTTS v2 - Voice cloning, multilingual
- OpenAI TTS - Fast, high quality
- ElevenLabs - Premium voices (optional)

**ASR Providers** (for voice Q&A):
- OpenAI Whisper - Best accuracy
- GiftMark Akan Whisper - African languages (future)

**Configuration**:
```python
from apps.shared.integration.ai_services import (
    AIProviderService,
    ProviderRegistry,
    ProviderType,
    get_default_tts_providers_config,
    get_default_asr_providers_config
)

# Initialize provider registry
registry = ProviderRegistry()
registry.register_providers_from_config(get_default_tts_providers_config())
registry.register_providers_from_config(get_default_asr_providers_config())

# Get TTS service
tts_service = AIProviderService(provider_type=ProviderType.TTS)
tts_providers = registry.get_providers_by_type(ProviderType.TTS)

# Get ASR service
asr_service = AIProviderService(provider_type=ProviderType.ASR)
asr_providers = registry.get_providers_by_type(ProviderType.ASR)
```

#### 3. **WalletService** (`@apps/shared/integration/wallet.py`)
- Credit management
- Stripe + Paystack integration
- Transaction history
- Idempotency

#### 4. **UsageCalculator** (`@apps/shared/integration/usage_calculator.py`)
- Cost tracking for:
  - TTS (narration + Q&A responses)
  - STT (voice input)
  - RAG queries (Gemini embeddings + LLM)
- Real-time cost display

#### 5. **DocumentProcessor** (`@apps/shared/integration/document_processor.py`)
- Book PDF processing
- Smart chunking for RAG
- Metadata extraction

### AI Services

| Service | Provider | Model | Purpose |
|---------|----------|-------|---------|
| **RAG (LLM)** | Gemini | gemini-2.0-flash-exp | Q&A generation |
| **Embeddings** | Gemini | text-embedding-004 | Semantic search |
| **TTS (Narration)** | Coqui XTTS v2 | - | Book narration (pre-gen) |
| **TTS (Q&A)** | OpenAI TTS | tts-1 | AI responses (real-time) |
| **STT** | OpenAI Whisper | whisper-1 | Voice questions |

### Databases
- **MongoDB**: Books, users, sessions, wallets
- **pgvector**: RAG embeddings
- **Supabase**: Authentication

---

## 💰 Updated Pricing (Voice-Based)

### Credit System
- 100 credits = $1
- New users: 200 credits free ($2)

### Costs

**Narration**:
- 2 credits/minute ($0.02/min)
- Pre-generated and cached

**Voice Q&A** (New):
- **Voice input (STT)**: 1 credit per 15 seconds ($0.01)
- **RAG query (Gemini)**: 2 credits per query ($0.02)
  - Embeddings: ~0.5 credits
  - LLM (Gemini 2.0 Flash): ~1.5 credits
- **Voice output (TTS)**: 3 credits per minute ($0.03)

**Example Q&A Cost**:
- User asks 10-second question: 0.67 credits ($0.0067)
- RAG processing: 2 credits ($0.02)
- AI responds with 30-second answer: 1.5 credits ($0.015)
- **Total: ~4.2 credits ($0.042) per voice Q&A**

**Compare**: Text Q&A would be ~1.5 credits ($0.015) - voice adds ~$0.027

---

## 🎯 User Flows

### New User Onboarding
```
1. Land on homepage (beautiful hero + shelves)
2. Click "Get Started"
3. Sign up (email or Google)
4. Auto-credit $2 (200 credits)
5. See "Continue Reading" shelf (empty) + "Recommended" (featured books)
6. Click featured book → Book detail page
7. Click "Start Reading" → Full-screen player loads
8. Narration begins automatically
9. Tooltip: "Tap 🎙️ to ask questions"
10. User explores
```

### Voice Q&A Flow
```
1. User is listening to narration
2. Has a question → Taps "🎙️ Ask"
3. **Voice recording starts** (waveform animation)
4. User speaks: "What does 'validated learning' mean?"
5. **STT transcribes** → Text shown in real-time
6. Tap to stop or auto-stop after silence
7. **Estimated cost shown**: "~$0.04"
8. Tap "Send" → "Thinking..." animation
9. **Gemini RAG** retrieves relevant book passages
10. **Gemini 2.0 Flash** generates contextual answer
11. **OpenAI TTS** converts to voice
12. **AI speaks** the answer (animated avatar)
13. User can tap to replay or "Ask follow-up"
14. Resume narration button appears
```

---

## 🛠️ Implementation Changes

### Additional Backend Endpoints

**Voice Q&A**:
```
POST   /api/bookshop/v1/voice/transcribe     # STT
POST   /api/bookshop/v1/voice/ask            # Q&A (uses RAG)
POST   /api/bookshop/v1/voice/synthesize     # TTS
GET    /api/bookshop/v1/voice/providers      # List TTS/ASR options
```

**Narration**:
```
GET    /api/bookshop/v1/reading/chunks/{id}/audio  # Pre-generated TTS
POST   /api/bookshop/v1/reading/generate-audio     # Batch TTS generation
```

### Frontend Components (Voice-Specific)

**New Components**:
- `VoiceRecorder.tsx` - Voice input with waveform
- `AIAvatar.tsx` - Animated avatar during AI response
- `VoicePlayer.tsx` - Playback controls for AI responses
- `ConversationDrawer.tsx` - Q&A history sidebar
- `AudioPlayerFull.tsx` - Full-screen immersive player
- `BookShelf.tsx` - Horizontal scrolling shelf (Netflix-style)
- `HeroBanner.tsx` - Featured book banner

**Enhanced Components**:
- `AudioPlayer.tsx` - Add voice Q&A button
- `WalletBalance.tsx` - Real-time updates, low-balance banner
- `TopUpModal.tsx` - Beautiful card-based top-up UI

---

## 📅 Updated 6-Week Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **1** | Setup + Beautiful UI | Backend setup, React components, Tailwind config, hero banner, shelves |
| **2** | Audio Playback + TTS | Narration playback, audio player UI, TTS integration (Coqui/OpenAI) |
| **3** | Voice Input (STT) | Voice recording UI, Whisper integration, live transcription |
| **4** | Voice Q&A (RAG) | Gemini RAG integration, voice Q&A flow, cost tracking |
| **5** | Wallet + Polish | Wallet UI, payment flow, animations, transitions |
| **6** | Testing + Launch | E2E tests, bug fixes, deployment, documentation |

---

## 🎨 Design Mockups (To Create)

**Pages needed**:
1. **Home** - Hero + shelves
2. **Book Detail** - Cover, summary, play button
3. **Full-Screen Player** - Immersive audiobook player
4. **Voice Q&A Modal** - Recording UI + AI response
5. **Wallet** - Top-up cards
6. **Profile** - Settings

**Design tools**: Figma (to be created)

---

## ⚠️ Key Risks & Mitigations (Voice-Specific)

| Risk | Mitigation |
|------|------------|
| **High voice costs** (TTS+STT) | Pre-generate narration TTS, cache AI responses, use fast models (Gemini Flash) |
| **STT latency** | Use streaming STT (Whisper), show "Listening..." feedback |
| **TTS latency for Q&A** | Use fast TTS (OpenAI tts-1), stream audio if possible |
| **Voice quality inconsistency** | Use high-quality providers (Coqui for narration, OpenAI for Q&A) |
| **Network issues during voice** | Buffer audio, show clear error messages, allow retry |

---

## 🚀 Launch Criteria (Voice MVP)

**Technical**:
- ✅ Voice Q&A working end-to-end
- ✅ Beautiful UI (Audible/Netflix-inspired)
- ✅ Gemini 2.0 Flash RAG integrated
- ✅ TTS/STT via shared AI services
- ✅ Audio playback smooth (no glitches)
- ✅ 80%+ test coverage

**Content**:
- ✅ 10+ books with pre-generated narration
- ✅ All books indexed in RAG

**UX**:
- ✅ Voice Q&A latency < 5 seconds (STT + RAG + TTS)
- ✅ Smooth animations (60 FPS)
- ✅ Mobile-responsive

---

## 📊 Success Metrics (Voice MVP)

**Engagement**:
- 20+ minutes average session duration
- 3+ voice Q&A per session
- 40%+ D7 retention

**Voice Usage**:
- 80%+ of users try voice Q&A
- 50%+ ask follow-up questions
- Average 5+ voice interactions per book

**Revenue**:
- 30%+ conversion to paid (after free credits)
- $5+ average revenue per paying user
- 50%+ gross margin

---

## 🎯 Why Voice-First?

1. **Natural interaction** - Speaking is faster than typing
2. **Immersive experience** - Feels like talking to a real tutor
3. **Hands-free** - Listen while exercising, cooking, commuting
4. **Accessibility** - Easier for users with typing difficulties
5. **Differentiation** - Most audiobook apps don't have voice Q&A

---

## 📝 Next Steps

1. ✅ Review and approve this voice-based PRD
2. Create Figma designs (Home, Player, Voice Q&A)
3. Set up Gemini API + shared AI services
4. Build beautiful React components
5. Implement voice Q&A flow
6. Test and launch

---

**Last Updated**: 2025-10-24
**Tech Stack**: React + Gemini 2.0 Flash + Shared AI Services (TTS/STT/RAG)
**UI Inspiration**: Audible + Netflix + Disney+

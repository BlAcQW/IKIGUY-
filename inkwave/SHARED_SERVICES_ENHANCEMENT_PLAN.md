# InkWave Enhancement Plan - Shared Services Integration

**Created**: 2025-11-03
**Status**: Planning Phase

## 🎯 Overview

This document outlines enhancements for InkWave based on available shared services from `@apps/shared/`. The goal is to transform InkWave from a basic RAG-powered bookshop into a comprehensive interactive audiobook and reading companion platform.

---

## 📦 Available Shared Services

### 1. **TTS Provider Service** ✅ Ready to Use
**Location**: `@apps/shared/services/tts_provider_service.py`

**Capabilities**:
- 10 TTS providers (Coqui XTTS, F5-TTS, StyleTTS2, MeloTTS, OpenVoice, Kokoro, Moshi, Akan MMS, etc.)
- Automatic billing via WalletService
- Voice cloning support
- Multi-language support (17 languages via Coqui XTTS)
- Health monitoring and failover
- Cost estimation

**Cost Model**:
- Base: $0.015 per 1000 characters
- Voice cloning: +$0.05 per request
- Premium providers: 2x multiplier

**Integration Effort**: Low (ChurchFlow reference available)

---

### 2. **Shared TTS Module** ✅ Ready to Use
**Location**: `@apps/shared/tts/`

**Capabilities**:
- Unified interface for all TTS providers
- Async/sync clients
- Real-time conversation (Moshi WebSocket)
- Batch processing
- Audio utilities (conversion, normalization, resampling)
- Format conversion (WAV, PCM, MP3)

**Use Cases**:
- Audiobook narration
- Q&A response audio
- Real-time voice interaction

**Integration Effort**: Low

---

### 3. **ASR Provider Service** ✅ Ready to Use
**Location**: `@apps/shared/services/asr_provider_service.py`

**Capabilities**:
- Speech-to-text transcription
- Multiple ASR providers
- Multi-language support
- Billing integration

**Use Cases**:
- Voice questions during reading
- Voice bookmarking ("Remember this page")
- Voice navigation ("Next chapter")

**Integration Effort**: Low

---

### 4. **LLM Provider Service** ✅ Ready to Use
**Location**: `@apps/shared/services/llm_provider_service.py`

**Capabilities**:
- Access to multiple LLM providers (OpenAI, Gemini, Anthropic)
- Automatic cost calculation
- Provider failover
- Streaming support

**Use Cases**:
- Enhanced RAG responses
- Book summarization
- Character analysis
- Theme extraction

**Integration Effort**: Low (already using Gemini directly)

---

### 5. **PDF Extraction Service** ✅ Ready to Use
**Location**: `@apps/shared/services/pdf_extraction_service.py`

**Capabilities**:
- Extract text from PDFs
- OCR support for scanned documents
- Structured data extraction
- Receipt/invoice processing

**Use Cases**:
- Book upload and processing
- Automatic chapter detection
- Metadata extraction

**Integration Effort**: Medium

---

### 6. **File Upload Service** ✅ Ready to Use
**Location**: `@apps/shared/services/file_upload_service.py`

**Capabilities**:
- Secure file uploads
- File type validation
- Size limits
- Storage management

**Use Cases**:
- PDF book uploads
- Audio reference uploads for voice cloning
- Cover image uploads

**Integration Effort**: Low

---

### 7. **Billing Service** ✅ Ready to Use
**Location**: `@apps/shared/services/billing_service.py`

**Capabilities**:
- Wallet management
- Transaction tracking
- Payment gateway integration (Stripe, Paystack)
- Cost calculation

**Use Cases**:
- Charge for TTS narration
- Charge for RAG interactions
- Charge for book processing
- Subscription management

**Integration Effort**: Low (already has wallet tables)

---

### 8. **Organization Service** ✅ Ready to Use
**Location**: `@apps/shared/services/organization_service.py`

**Capabilities**:
- Multi-tenant support
- Organization management
- User roles and permissions

**Use Cases**:
- Libraries and schools using InkWave
- Book clubs
- Educational institutions

**Integration Effort**: Medium

---

## 🚀 Implementation Roadmap

### Phase 1: Audio Narration (Week 1-2)
**Goal**: Enable audiobook functionality for existing books

#### Backend Tasks

1. **Create TTS Service Integration** (`app/services/tts_service.py`)
   ```python
   from apps.shared.services.tts_provider_service import TTSProviderService

   class InkWaveTTSService:
       def __init__(self):
           self.tts_provider = TTSProviderService(
               enable_billing=True,
               enable_health_monitoring=True
           )

       async def narrate_chunk(self, chunk_id: str, user_id: str,
                              voice_preference: str = "coqui_xtts"):
           """Generate audio for a book chunk."""
           # Get chunk text
           # Synthesize with TTS
           # Save audio URL
           # Return audio metadata
   ```

2. **Add Audio Generation Endpoints** (`app/api/routes/audio.py`)
   - `POST /api/v1/books/{book_id}/chunks/{chunk_id}/audio` - Generate audio
   - `GET /api/v1/books/{book_id}/chunks/{chunk_id}/audio` - Get cached audio
   - `POST /api/v1/books/{book_id}/narrate-all` - Batch generate (background job)
   - `GET /api/v1/audio/voices` - Get available voices/providers

3. **Update Book Chunks Schema**
   ```python
   class BookChunkInDB:
       chunk_id: str
       book_id: str
       text: str
       audio_url: Optional[str] = None
       audio_duration: Optional[float] = None
       audio_provider: Optional[str] = None
       audio_generated_at: Optional[datetime] = None
   ```

4. **Add User Voice Preferences**
   ```python
   class UserProfile:
       preferred_tts_provider: str = "coqui_xtts"
       preferred_voice_id: str = "nova"
       playback_speed: float = 1.0
       voice_clone_reference: Optional[str] = None  # For personalized narration
   ```

#### Frontend Tasks

1. **Audio Player Component** (`src/components/AudioPlayer.tsx`)
   - Play/pause controls
   - Progress bar
   - Speed control (0.5x - 2x)
   - Skip forward/back (chunk navigation)
   - Auto-advance to next chunk

2. **Voice Settings Page** (`src/pages/VoiceSettingsPage.tsx`)
   - Provider selection
   - Voice preview
   - Speed preference
   - Voice cloning upload

3. **Reading Page Enhancements** (`src/pages/ReadingPage.tsx`)
   - Audio player integration
   - Sync text highlighting with audio
   - Tap to play/pause
   - Background playback support

**Estimated Cost Impact**:
- Per chapter (5000 chars): ~$0.075 with Coqui XTTS
- Per book (100k chars): ~$1.50 with Coqui XTTS
- With voice cloning: +$0.05 per chunk

---

### Phase 2: Voice Q&A (Week 3)
**Goal**: Enable voice-based questions and answers

#### Backend Tasks

1. **Integrate ASR Service** (`app/services/asr_service.py`)
   ```python
   from apps.shared.services.asr_provider_service import ASRProviderService

   async def transcribe_question(audio_file: bytes, user_id: str) -> str:
       """Convert voice to text."""
   ```

2. **Add Voice Interaction Endpoints**
   - `POST /api/v1/interactions/{interaction_id}/voice-question` - Upload audio
   - `GET /api/v1/interactions/{interaction_id}/audio-response` - Get TTS response

3. **Update Interaction Flow**
   ```
   User speaks → ASR transcription → RAG query →
   Generate text response → TTS synthesis → Audio response
   ```

#### Frontend Tasks

1. **Voice Recorder Component** (`src/components/VoiceRecorder.tsx`)
   - Record button
   - Waveform visualization
   - Stop recording
   - Upload to backend

2. **Voice Q&A Modal**
   - Press & hold to record
   - Auto-playback of response
   - Text fallback display

**Estimated Cost Impact**:
- ASR: ~$0.006 per minute
- TTS response: ~$0.015 per 1000 chars
- Total per voice interaction: ~$0.025

---

### Phase 3: PDF Upload & Processing (Week 4-5)
**Goal**: Allow users to upload their own books

#### Backend Tasks

1. **Integrate PDF Extraction Service**
   ```python
   from apps.shared.services.pdf_extraction_service import PDFExtractionService
   from apps.shared.services.file_upload_service import FileUploadService
   ```

2. **Create Processing Pipeline** (`app/services/book_processor.py`)
   - Upload PDF → Extract text → Detect chapters →
     Create chunks → Generate embeddings → Generate metadata

3. **Add Upload Endpoints**
   - `POST /api/v1/books/upload` - Upload PDF
   - `GET /api/v1/books/{book_id}/processing-status` - Check status
   - `POST /api/v1/books/{book_id}/cancel-processing` - Cancel

4. **Background Job (Celery/FastAPI BackgroundTasks)**
   - Process PDF asynchronously
   - Update status in real-time
   - Charge processing fee

#### Frontend Tasks

1. **Upload Page** (`src/pages/UploadBookPage.tsx`)
   - Drag & drop zone
   - File validation
   - Upload progress
   - Processing status

2. **Processing Status Component**
   - Real-time progress updates
   - Estimated completion time
   - Cost breakdown

**Estimated Cost Impact**:
- PDF processing (100 pages): ~$0.50
- Embedding generation (100k chars): ~$0.20
- Metadata generation: ~$0.10
- Total: ~$0.80 per book

---

### Phase 4: Voice Cloning & Personalization (Week 6)
**Goal**: Personalized narration with user's voice

#### Backend Tasks

1. **Voice Clone Management** (`app/services/voice_clone_service.py`)
   ```python
   async def create_voice_clone(
       user_id: str,
       reference_audio: bytes,
       voice_name: str
   ):
       """Create and save voice clone reference."""
   ```

2. **Add Voice Clone Endpoints**
   - `POST /api/v1/user/voice-clones` - Upload reference audio
   - `GET /api/v1/user/voice-clones` - List saved voices
   - `DELETE /api/v1/user/voice-clones/{clone_id}` - Delete voice
   - `POST /api/v1/user/voice-clones/{clone_id}/test` - Test narration

#### Frontend Tasks

1. **Voice Clone Setup Wizard**
   - Record 30-60 seconds of speech
   - Upload audio
   - Test cloned voice
   - Save as preference

2. **Voice Library**
   - Manage saved voices
   - Switch between voices
   - Preview each voice

**Estimated Cost Impact**:
- Voice cloning: +$0.05 per chunk
- Per chapter with cloning: ~$0.325
- Per book with cloning: ~$6.50

---

### Phase 5: Advanced Features (Week 7-8)

#### 1. Real-Time Conversation (Moshi WebSocket)
   - Live dialogue with book character
   - Real-time Q&A
   - Interactive storytelling

#### 2. Multi-Language Support
   - Detect book language
   - Auto-select appropriate TTS provider
   - Support 17 languages (via Coqui XTTS)

#### 3. Offline Mode
   - Pre-download audio chunks
   - Offline reading with sync
   - Background audio download

#### 4. Social Features
   - Share book highlights with audio
   - Voice annotations
   - Book clubs with shared narration

#### 5. Analytics Dashboard
   - Listening time tracking
   - Most popular voices
   - Cost analytics
   - User engagement metrics

---

## 💰 Monetization Strategy

### Pricing Tiers

**Free Tier**:
- RAG Q&A (5 questions/day)
- Basic TTS narration (1 chapter/day)
- Standard voices only

**Premium ($9.99/month)**:
- Unlimited RAG Q&A
- Unlimited TTS narration
- All voice providers
- Voice cloning (3 voices)
- PDF upload (5 books/month)
- Background playback

**Enterprise ($49.99/month)**:
- Everything in Premium
- Organization management
- Unlimited PDF uploads
- Priority processing
- Custom voices
- API access
- Analytics dashboard

### Pay-As-You-Go
- TTS: $0.02 per 1000 characters
- RAG: $0.01 per query
- Voice cloning: $0.10 per request
- PDF processing: $1.00 per book

---

## 🧪 Testing Strategy

### Unit Tests
```python
# Test TTS integration
async def test_narrate_chunk():
    """Test chunk narration with TTS."""

# Test ASR integration
async def test_voice_question():
    """Test voice question transcription."""

# Test PDF processing
async def test_book_upload():
    """Test PDF upload and processing."""

# Test voice cloning
async def test_voice_clone_creation():
    """Test voice clone creation and usage."""
```

### Integration Tests
- End-to-end audiobook generation
- Voice Q&A flow
- PDF upload to narration pipeline
- Billing and wallet integration

### Performance Tests
- Audio generation latency
- Concurrent TTS requests
- PDF processing time
- Background job queue

---

## 📊 Expected Impact

### User Experience
- **Before**: Text-only reading with basic Q&A
- **After**: Full audiobook experience with voice interaction

### Business Metrics
- **Revenue per user**: $5-10/month (estimated)
- **User retention**: +40% (audiobooks increase engagement)
- **Daily active users**: +60% (audio enables mobile usage)

### Technical Metrics
- **API latency**: <2s for TTS generation (cached)
- **PDF processing**: <2 minutes for 100-page book
- **Cost efficiency**: $0.80 per book (amortized over multiple users)

---

## 🔄 Migration Path

### Existing Users
1. Announce new audio features
2. Offer 1-month free Premium trial
3. Migrate reading sessions to include audio
4. Preserve existing Q&A history

### Existing Books
1. Batch generate audio for popular books
2. On-demand generation for less popular books
3. Cache audio permanently
4. Update book metadata with audio availability

---

## 📝 Next Steps

1. **Week 1**: Implement TTS integration (Phase 1)
2. **Week 2**: Add audio player UI
3. **Week 3**: Integrate ASR for voice Q&A (Phase 2)
4. **Week 4**: PDF upload backend (Phase 3)
5. **Week 5**: PDF upload UI & processing
6. **Week 6**: Voice cloning (Phase 4)
7. **Week 7-8**: Advanced features & polish (Phase 5)

---

## 📚 References

- ChurchFlow Voice Greeting Implementation: `@apps/churchflow/backend/app/services/voice_greeting_service.py`
- Shared TTS Provider Service: `@apps/shared/services/tts_provider_service.py`
- Shared TTS Module: `@apps/shared/tts/`
- Shared ASR Service: `@apps/shared/services/asr_provider_service.py`
- Shared PDF Extraction: `@apps/shared/services/pdf_extraction_service.py`
- Shared File Upload: `@apps/shared/services/file_upload_service.py`

---

**Last Updated**: 2025-11-03

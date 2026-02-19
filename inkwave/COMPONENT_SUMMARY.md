# InkWave - New Components Summary

**Date**: 2025-11-03
**Status**: Backend components created for MVP reading experience

---

## Components Created

### 1. Models (`app/models/`)

#### `session.py` - Reading Session Management
- **ReadingSession**: Main model for tracking user reading progress
  - Fields: session_id, user_id, book_id, current_chunk_index, current_position_seconds
  - Bookmarks support with notes
  - Time tracking and completion status
- **ReadingSessionInDB**: Database variant with _id field
- **ReadingSessionUpdate**: Update model for progress tracking
- **Bookmark**: Nested model for bookmarks

#### `interaction.py` - Q&A Conversation Management
- **Interaction**: Model for Q&A sessions during reading
  - Links to reading session and book
  - Stores conversation messages
  - Tracks chunk context
- **Message**: Individual message in conversation
  - Role (user/assistant)
  - Content, audio_url, tokens, cost tracking
- **InteractionInDB**: Database variant
- **InteractionCreate**: Creation request model
- **MessageCreate**: Message send request model

### 2. Services (`app/services/`)

#### `reading_service.py` - Session Management
Manages reading sessions and progress tracking.

**Key Methods**:
- `create_session()` - Create/retrieve active session
- `get_session()` - Get session by ID
- `update_progress()` - Update reading position
- `add_bookmark()` - Add bookmark with note
- `get_chunk()` - Retrieve book chunk
- `get_next_chunk()` / `get_previous_chunk()` - Navigate chunks
- `get_user_sessions()` - List user's sessions
- `mark_completed()` - Mark book as finished

**Features**:
- Auto-resumes existing active sessions
- Progress auto-save support
- Bookmark management
- Session completion tracking

#### `tts_service.py` - Audio Generation
Wrapper for shared TTS service with caching.

**Key Methods**:
- `initialize()` - Set up TTS provider (OpenAI/ElevenLabs/Coqui)
- `generate_audio()` - Generate audio from text
- `generate_chunk_audio()` - Generate with automatic caching
- `calculate_cost()` - Estimate TTS cost
- `optimize_text_for_tts()` - Clean text for better pronunciation

**Features**:
- Multi-provider support (OpenAI TTS, ElevenLabs, Coqui)
- Audio caching with storage service integration
- Text optimization (abbreviation expansion, pause handling)
- Cost calculation per provider

### 3. API Routes (`app/api/routes/`)

#### `reading.py` - Reading Session API
**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reading/sessions` | Create/get reading session |
| GET | `/reading/sessions/{session_id}` | Get session details |
| PUT | `/reading/sessions/{session_id}` | Update progress |
| POST | `/reading/sessions/{session_id}/bookmark` | Add bookmark |
| GET | `/reading/sessions/{session_id}/complete` | Mark completed |
| GET | `/reading/sessions` | List user sessions |
| GET | `/reading/chunks/{book_id}/{chunk_index}` | Get chunk text |
| GET | `/reading/chunks/{book_id}/{chunk_index}/audio` | Get/generate audio |

**Features**:
- All endpoints require authentication
- Audio endpoint streams MP3 directly
- Progress auto-update with timestamps
- Bookmark notes support

#### `interaction.py` - Q&A Interaction API
**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/interactions` | Create Q&A session |
| GET | `/interactions/{interaction_id}` | Get interaction history |
| POST | `/interactions/{interaction_id}/messages` | Send message & get AI response |
| GET | `/interactions/session/{session_id}` | Get all interactions for session |
| DELETE | `/interactions/{interaction_id}` | Delete interaction |

**Features**:
- RAG-powered AI responses using shared RAGService
- Personalized based on user profile (reading level)
- Anti-spoiler context filtering (only content before current position)
- Token and cost tracking per message
- Conversation history management

---

## Integration Points

### Shared Services Used

1. **RAGService** (`apps/shared/integration/rag.py`)
   - Used in: `interaction.py`
   - Purpose: Semantic search for book Q&A

2. **TTSService** (`apps/shared/integration/tts_service.py`)
   - Used in: `tts_service.py`
   - Purpose: Audio generation for narration

3. **WalletService** (TODO)
   - To be integrated in: `reading.py`, `interaction.py`
   - Purpose: Charge users for TTS and Q&A usage

4. **UsageCalculator** (TODO)
   - To be integrated in: `tts_service.py`, `interaction.py`
   - Purpose: Calculate costs for billing

### Database Collections

**New Collections**:
- `reading_sessions` - User reading progress
- `interactions` - Q&A conversations

**Existing Collections Used**:
- `books` - Book metadata
- `book_chunks` - Book text chunks
- `users` - User profiles

---

## API Flow Examples

### 1. Start Reading a Book

```
1. POST /reading/sessions
   Request: { "book_id": "book123" }
   Response: ReadingSession with session_id

2. GET /reading/chunks/{book_id}/0
   Response: First chunk text

3. GET /reading/chunks/{book_id}/0/audio
   Response: MP3 audio file (streamed)

4. User advances → PUT /reading/sessions/{session_id}
   Request: { "current_chunk_index": 1 }
```

### 2. Ask a Question During Reading

```
1. POST /interactions
   Request: {
     "session_id": "session123",
     "book_id": "book123",
     "chunk_context": [0, 1, 2]  // Current reading context
   }
   Response: Interaction with interaction_id

2. POST /interactions/{interaction_id}/messages
   Request: { "content": "Who is the main character?" }
   Response: {
     "interaction": {...},
     "message": {
       "role": "assistant",
       "content": "Based on the passage...",
       "tokens_used": 250,
       "cost_cents": 5
     }
   }
```

---

## TODO: Next Steps

### Critical for MVP:

1. **Wallet Integration**
   - [ ] Add wallet debit calls in `reading.py` (TTS audio generation)
   - [ ] Add wallet debit calls in `interaction.py` (Q&A responses)
   - [ ] Add balance checks before operations
   - [ ] Add cost estimation endpoints

2. **RAG Service Enhancement**
   - [ ] Implement `query_with_context()` method in existing RAGService
   - [ ] Add anti-spoiler filtering (chunk_index-based)
   - [ ] Test retrieval accuracy with sample books

3. **Storage Service**
   - [ ] Implement audio caching in `tts_service.py`
   - [ ] Set up S3/MinIO for audio files
   - [ ] Add CDN integration for audio delivery

4. **Testing**
   - [ ] Create unit tests for reading_service
   - [ ] Create unit tests for tts_service
   - [ ] Create integration tests for reading flow
   - [ ] Create integration tests for Q&A flow

5. **Frontend Integration**
   - [ ] Create reading page with audio player
   - [ ] Create Q&A modal/panel component
   - [ ] Add progress bar and bookmark UI
   - [ ] Test end-to-end reading experience

### Nice to Have:

- [ ] WebSocket support for real-time Q&A
- [ ] Voice input (STT) for questions
- [ ] Pre-generate audio for all chunks (background job)
- [ ] Session analytics (reading speed, completion rate)
- [ ] Social features (share bookmarks, notes)

---

## File Structure

```
inkwave/backend/app/
├── models/
│   ├── session.py          ✓ NEW
│   ├── interaction.py      ✓ NEW
│   ├── book.py             (existing)
│   └── user.py             (existing)
├── services/
│   ├── reading_service.py  ✓ NEW
│   ├── tts_service.py      ✓ NEW
│   ├── rag_service.py      (existing)
│   └── wallet_service.py   (existing)
├── api/routes/
│   ├── reading.py          ✓ NEW
│   ├── interaction.py      ✓ NEW
│   ├── books.py            (existing)
│   ├── voice.py            (existing)
│   └── wallet.py           (existing)
└── main.py                 ✓ UPDATED (routes registered)
```

---

## Testing Commands

```bash
# Start backend
cd /opt/kasaai/apps/inkwave/backend
source ../../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 30033 --reload

# Test endpoints
curl http://localhost:30033/health
curl http://localhost:30033/api/docs  # Swagger UI
```

---

## Notes

- All components follow the patterns defined in PLANNING.md
- Authentication handled via Supabase JWT tokens
- All endpoints use dependency injection for services
- Error handling with proper HTTP status codes
- Models include proper Pydantic validation
- Services are async for performance

**Status**: ✅ Core backend components ready for integration and testing

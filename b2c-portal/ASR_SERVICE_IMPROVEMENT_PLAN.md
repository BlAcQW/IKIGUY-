# ASR Service Improvement Plan
**Date:** 2025-10-27
**Goal:** Enhance ASR service to match TTS service quality with centralized, publicly accessible APIs

## 📊 Current State Analysis

### TTS Service Features (✅ Reference Implementation)
- ✅ Rate limiting with tier-based limits
- ✅ Custom error classes (TTSError, InsufficientBalanceError, etc.)
- ✅ Audio history service (MongoDB-based)
- ✅ Text sanitization (XSS prevention with bleach)
- ✅ Voice samples endpoints (/voices, /voices/{filename})
- ✅ Enhanced provider endpoints (languages, speakers)
- ✅ Audio format conversion (wav, mp3, ogg, flac, m4a)
- ✅ Comprehensive error mapping
- ✅ Non-blocking history saves
- ✅ File upload + base64 support

### ASR Service Current State (⚠️ Needs Improvement)
- ❌ No rate limiting
- ❌ Basic exception handling only
- ❌ No transcription history service
- ❌ No input sanitization
- ❌ No sample audio files for testing
- ❌ Basic provider endpoints only
- ✅ File upload + base64 support
- ✅ Cost estimation
- ✅ Provider health monitoring
- ✅ Automatic billing

---

## 🎯 Improvement Phases

### Phase 1: Error Handling & Security (Priority: HIGH)
**Estimated Time:** 4 hours

#### 1.1 Custom Error Classes
**File:** `/opt/kasaai/apps/core_backend/backend/exceptions/asr_errors.py` (NEW)

```python
"""
ASR-specific error classes for better error handling and user feedback.
"""

class ASRError(Exception):
    """Base exception for ASR errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class InsufficientBalanceError(ASRError):
    """User has insufficient balance for transcription."""
    def __init__(self, required: float, available: float):
        message = f"Insufficient balance. Required: ${required:.2f}, Available: ${available:.2f}"
        super().__init__(message, status_code=402)

class ProviderOfflineError(ASRError):
    """ASR provider is offline or unreachable."""
    def __init__(self, provider_id: str):
        message = f"ASR provider '{provider_id}' is currently offline. Please try another provider."
        super().__init__(message, status_code=503)

class AudioTooLongError(ASRError):
    """Audio file exceeds maximum duration."""
    def __init__(self, duration: float, max_duration: float):
        message = f"Audio too long ({duration:.1f}s). Maximum allowed: {max_duration:.1f}s"
        super().__init__(message, status_code=413)

class InvalidProviderError(ASRError):
    """Invalid or unsupported provider."""
    def __init__(self, provider_id: str):
        message = f"Invalid ASR provider: '{provider_id}'"
        super().__init__(message, status_code=404)

class InvalidLanguageError(ASRError):
    """Unsupported language for provider."""
    def __init__(self, language: str, provider_id: str):
        message = f"Language '{language}' not supported by provider '{provider_id}'"
        super().__init__(message, status_code=400)

class AudioProcessingError(ASRError):
    """Error processing audio file."""
    def __init__(self, detail: str):
        message = f"Audio processing failed: {detail}"
        super().__init__(message, status_code=422)

def map_exception_to_asr_error(exc: Exception) -> ASRError:
    """Map generic exceptions to specific ASR errors."""
    if isinstance(exc, ASRError):
        return exc

    error_msg = str(exc).lower()

    if "balance" in error_msg or "insufficient" in error_msg:
        return InsufficientBalanceError(0, 0)
    elif "offline" in error_msg or "unreachable" in error_msg:
        return ProviderOfflineError("unknown")
    elif "too long" in error_msg or "duration" in error_msg:
        return AudioTooLongError(0, 0)
    elif "language" in error_msg:
        return InvalidLanguageError("unknown", "unknown")
    elif "audio" in error_msg or "format" in error_msg:
        return AudioProcessingError(str(exc))
    else:
        return ASRError(f"Transcription failed: {str(exc)}", status_code=500)
```

#### 1.2 Rate Limiting
**File:** `/opt/kasaai/apps/core_backend/backend/middleware/rate_limiting.py` (ENHANCE)

Add ASR-specific rate limits:
```python
def get_asr_rate_limit(endpoint_type: str, tier: str = "free"):
    """
    Get ASR rate limit configuration.

    Limits:
    - transcribe: 100/day (free), 1000/day (pro)
    - estimate: 500/day (free), unlimited (pro)
    - info: 1000/day (all tiers)
    """
```

#### 1.3 Audio Validation & Sanitization
**File:** `/opt/kasaai/apps/core_backend/backend/routes/asr_services.py` (ENHANCE)

Add validators:
- Maximum audio duration (300s for free tier, 3600s for pro)
- Supported audio formats validation
- Audio file size limits
- Malicious file detection

---

### Phase 2: Transcription History (Priority: HIGH)
**Estimated Time:** 6 hours

#### 2.1 History Service
**File:** `/opt/kasaai/apps/core_backend/backend/services/transcription_history_service.py` (NEW)

```python
"""
Transcription History Service

Stores user transcriptions in MongoDB for replay, export, and analytics.
"""

class TranscriptionHistoryService:
    async def add_to_history(
        user_id: str,
        audio_filename: str,
        provider_id: str,
        transcript: str,
        language: str,
        duration_seconds: float,
        cost: float,
        audio_base64: Optional[str] = None
    ):
        """Save transcription to user history."""

    async def get_user_history(
        user_id: str,
        page: int = 1,
        limit: int = 20,
        search_text: Optional[str] = None,
        provider_filter: Optional[str] = None,
        language_filter: Optional[str] = None
    ):
        """Get paginated transcription history."""

    async def get_history_item(user_id: str, item_id: str):
        """Get specific transcription with full details."""

    async def delete_history_item(user_id: str, item_id: str):
        """Soft delete transcription."""

    async def export_history(user_id: str, format: str = "csv"):
        """Export user history to CSV/JSON."""
```

#### 2.2 MongoDB Schema
**Collection:** `asr_history`

```javascript
{
  _id: ObjectId,
  user_id: String,
  audio_filename: String,
  provider_id: String,
  transcript: String,
  language: String,
  duration_seconds: Number,
  cost: Number,
  audio_base64: String (optional),
  created_at: Date,
  deleted_at: Date (optional),
  metadata: {
    model_name: String,
    task: String (transcribe/translate),
    processing_time: Number
  }
}
```

#### 2.3 API Endpoints
Add to `asr_services.py`:
- `GET /api/asr/history` - List transcriptions
- `GET /api/asr/history/{item_id}` - Get specific item
- `DELETE /api/asr/history/{item_id}` - Delete item
- `GET /api/asr/history/export` - Export to CSV/JSON

---

### Phase 3: Sample Audio Files (Priority: MEDIUM)
**Estimated Time:** 3 hours

#### 3.1 Sample Audio Library
**Directory:** `/opt/kasaai/apps/voice-lab/asr_samples/`

Curated samples:
```
english_samples/
  - hello_world.wav (1s, "Hello, world!")
  - weather_report.wav (10s, news excerpt)
  - phone_conversation.wav (30s, dialog)

twi_samples/
  - akwaaba.wav (2s, "Akwaaba! Ɛte sɛn?")
  - akan_proverb.wav (15s, traditional proverb)
  - market_conversation.wav (20s, marketplace dialog)

multilingual_samples/
  - mixed_language.wav (10s, code-switching)
  - noisy_audio.wav (10s, background noise test)
```

#### 3.2 API Endpoints
```python
@router.get("/samples")
async def list_samples() -> Dict:
    """List all available ASR test samples."""

@router.get("/samples/{language}/{filename}")
async def get_sample_file(language: str, filename: str):
    """Serve ASR sample audio file."""

@router.get("/samples/{sample_id}/transcript")
async def get_sample_transcript(sample_id: str) -> Dict:
    """Get ground truth transcript for sample."""
```

---

### Phase 4: Enhanced Provider Endpoints (Priority: MEDIUM)
**Estimated Time:** 2 hours

#### 4.1 Detailed Provider Info
Enhance existing endpoints:

```python
@router.get("/providers/{provider_id}/languages")
async def get_provider_languages(provider_id: str) -> Dict:
    """
    Get supported languages with metadata.

    Returns:
        {
            "languages": [
                {
                    "code": "en",
                    "name": "English",
                    "native_name": "English",
                    "accuracy": 0.95,
                    "cost_per_minute": 0.006
                },
                ...
            ]
        }
    """

@router.get("/providers/{provider_id}/models")
async def get_provider_models(provider_id: str) -> Dict:
    """Get available models (tiny, base, small, medium, large)."""

@router.get("/providers/{provider_id}/benchmark")
async def get_provider_benchmark(provider_id: str) -> Dict:
    """Get WER (Word Error Rate) benchmarks by language."""
```

---

### Phase 5: Advanced Features (Priority: LOW)
**Estimated Time:** 8 hours

#### 5.1 Audio Format Conversion
**Integration:** Use existing `/opt/kasaai/apps/shared/services/audio_conversion_service.py`

```python
@router.post("/transcribe/convert")
async def transcribe_with_conversion(
    audio_file: UploadFile,
    provider_id: str,
    output_format: str = "json",  # json, text, srt, vtt
    input_format: Optional[str] = None  # Auto-detect if None
):
    """
    Transcribe audio with automatic format conversion.

    Supports: wav, mp3, ogg, flac, m4a, webm
    """
```

#### 5.2 Batch Transcription
```python
@router.post("/transcribe/batch")
async def transcribe_batch(
    audio_files: List[UploadFile],
    provider_id: str,
    language: Optional[str] = None
):
    """
    Transcribe multiple files in a single request.

    Returns:
        {
            "results": [...],
            "total_cost": 0.45,
            "total_duration": 125.3,
            "failed_count": 0
        }
    """
```

#### 5.3 Real-time Streaming Transcription
```python
@router.websocket("/ws/transcribe/stream/{provider_id}")
async def transcribe_stream(websocket: WebSocket, provider_id: str):
    """
    Real-time streaming transcription.

    Client sends audio chunks → Server returns partial transcripts
    """
```

#### 5.4 Diarization Support
```python
@router.post("/transcribe/diarize")
async def transcribe_with_diarization(
    audio_file: UploadFile,
    provider_id: str,
    num_speakers: Optional[int] = None
):
    """
    Transcribe with speaker diarization.

    Returns:
        {
            "segments": [
                {"speaker": "SPEAKER_00", "start": 0.0, "end": 2.5, "text": "..."},
                {"speaker": "SPEAKER_01", "start": 2.6, "end": 5.1, "text": "..."}
            ]
        }
    """
```

---

## 📋 Implementation Checklist

### Phase 1: Error Handling & Security (Week 1)
- [ ] Create `/backend/exceptions/asr_errors.py` with 7 error classes
- [ ] Add `map_exception_to_asr_error()` function
- [ ] Update `asr_services.py` to use custom errors
- [ ] Add rate limiting to all ASR endpoints
- [ ] Add audio validation (duration, format, size)
- [ ] Add malicious file detection
- [ ] Test error responses with Postman

### Phase 2: Transcription History (Week 2)
- [ ] Create `/backend/services/transcription_history_service.py`
- [ ] Create MongoDB `asr_history` collection with indexes
- [ ] Add history endpoints to `asr_services.py`
- [ ] Integrate non-blocking history saves in transcribe endpoints
- [ ] Add pagination and filters
- [ ] Add export to CSV/JSON
- [ ] Test with real transcriptions

### Phase 3: Sample Audio Files (Week 3)
- [ ] Create `/apps/voice-lab/asr_samples/` directory structure
- [ ] Record/curate 10+ sample audio files
- [ ] Create ground truth transcripts JSON
- [ ] Add `/samples` endpoints to `asr_services.py`
- [ ] Add sample metadata (WER, duration, language)
- [ ] Test sample playback and downloads

### Phase 4: Enhanced Provider Endpoints (Week 3)
- [ ] Add `/providers/{id}/languages` with metadata
- [ ] Add `/providers/{id}/models` endpoint
- [ ] Add `/providers/{id}/benchmark` with WER data
- [ ] Update provider health monitoring
- [ ] Add provider comparison endpoint

### Phase 5: Advanced Features (Week 4-5)
- [ ] Audio format conversion integration
- [ ] Batch transcription endpoint
- [ ] Real-time streaming (WebSocket)
- [ ] Speaker diarization support
- [ ] Add comprehensive tests

---

## 🚀 Quick Wins (Can Start Today)

### 1. Rate Limiting (1 hour)
Add to `asr_services.py`:
```python
from ..middleware.rate_limiting import get_asr_rate_limit

@router.post("/transcribe")
async def transcribe(
    ...,
    rate_limit: None = Depends(get_asr_rate_limit("transcribe", "free"))
):
```

### 2. Custom Error Classes (2 hours)
Create `asr_errors.py` and update exception handling.

### 3. Sample Audio Files (1 hour)
Add 3 basic English samples for immediate testing.

---

## 📈 Success Metrics

- **Security:** 100% of inputs sanitized, rate limits enforced
- **Reliability:** Custom error messages for all failure modes
- **Usability:** Sample audio files for testing (10+ samples)
- **Features:** Transcription history with search/export
- **Performance:** Non-blocking history saves (<10ms overhead)
- **Completeness:** Parity with TTS service features

---

## 🔄 Migration Path

1. **Backward Compatible:** All existing endpoints remain unchanged
2. **Gradual Rollout:** New features added without breaking changes
3. **Optional Features:** History, samples, and advanced features are opt-in
4. **API Versioning:** Use `/api/v2/asr` for breaking changes (future)

---

## 💡 Public Accessibility Plan

### Current State
- ✅ `/api/asr/*` endpoints exist
- ❌ Not documented in public API docs
- ❌ No public examples/tutorials
- ❌ No rate limiting for public access

### Public API Strategy
1. **Documentation:** Add to `/apps/developer_platform/API_DOCUMENTATION.md`
2. **API Keys:** Require API key for public access (via Developer Portal)
3. **Rate Limits:** Tier-based limits (free, pro, enterprise)
4. **Examples:** Add code examples in Python, JavaScript, cURL
5. **Playground:** Add ASR testing to Developer Portal
6. **Pricing:** Transparent cost calculator

---

## 🎯 Final State (After All Phases)

```
ASR Service Features:
✅ Rate limiting (tier-based)
✅ Custom error classes (7 types)
✅ Transcription history (MongoDB)
✅ Audio validation & sanitization
✅ Sample audio files (10+ samples)
✅ Enhanced provider endpoints
✅ Audio format conversion
✅ Batch transcription
✅ Real-time streaming (WebSocket)
✅ Speaker diarization
✅ Public API documentation
✅ Developer Portal integration
✅ Comprehensive error handling
✅ Non-blocking operations
✅ Export to CSV/JSON

EQUALS: Production-ready, publicly accessible ASR API 🚀
```

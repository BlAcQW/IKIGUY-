# InkWave Pre-Launch Execution Roadmap
**Generated:** 2026-01-05
**Target:** 100,000 users in 30 days
**Status:** Critical audit complete, remediation in progress

---

## Executive Summary

This roadmap consolidates findings from 6 comprehensive audits covering:
1. **Audio/Voice System** - 10 findings (1 critical, 3 high, 4 medium, 2 low)
2. **Activity Tracking** - 10 findings (2 critical, 2 high, 6 medium)
3. **Data/State Consistency** - 8 issues (2 critical, 2 high, 3 medium, 1 low)
4. **Admin Observability** - 10 findings (2 critical, 5 high, 3 medium)
5. **AI Behavior & Grounding** - 16 findings (7 critical, 4 high, 5 medium)
6. **Scale & Failure Modes** - 13 findings (4 critical, 6 high, 3 medium)

**Total Issues Identified:** 67 unique issues across all audits

---

## Critical Fixes Completed

| ID | Fix | Status | Evidence |
|----|-----|--------|----------|
| C01 | Wallet race condition - Atomic credit reservation | ✅ DONE | `voice.py:reserve_credits_atomic()` |
| C02 | Webhook idempotency - MongoDB payment_records | ✅ DONE | `wallet.py:payment_records collection` |
| C03 | Paystack double-credit - idempotency_key check | ✅ DONE | `wallet.py:idempotency_key` |
| C04 | Buffer underrun detection | ✅ DONE | `useChunkPlayer.ts:stalled/waiting events` |
| H02 | BlobCache LRU eviction | ✅ DONE | `useChunkPlayer.ts:MAX_BLOB_CACHE_SIZE=50` |
| H03 | API timeout for TTS | ✅ DONE | `api.ts:timeout=120000` |

---

## Week 1 (Pre-Launch Critical) - Days 1-7

### MUST FIX BEFORE LAUNCH

#### 1. C05: Offline Consumption Persistence
- **File:** `frontend/src/lib/consumption-tracker.ts`
- **Issue:** Offline listening progress lost on page refresh
- **Fix:** Add localStorage persistence with debounced writes
- **Impact:** Hours of user progress could be lost
- **Status:** 🔴 PENDING

#### 2. C06: Analytics Wrong Collection
- **File:** `backend/app/services/analytics_service.py`
- **Issue:** `get_book_analytics()` queries `wallet_transactions` instead of `consumption_events`
- **Fix:** Update to query consumption_events for listening metrics
- **Impact:** Admin dashboard shows 0 listening time
- **Status:** 🔴 PENDING

#### 3. C07: Session Models Not Synced
- **Files:** `reading.py`, `consumption.py`
- **Issue:** `reading_sessions` and `consumption_events` diverge
- **Fix:** Create SessionSyncService to keep both in sync
- **Impact:** Users see different progress in different views
- **Status:** 🔴 PENDING

#### 4. AI: Spoiler Prevention (CRITICAL)
- **File:** `backend/app/services/embedding_service.py`
- **Issue:** RAG retrieval searches ALL book chunks, ignoring reading position
- **Fix:** Add `max_chunk_index` filter to similarity search
- **Impact:** Users can get book-ending spoilers
- **Status:** 🔴 PENDING

#### 5. AI: Prompt Injection Protection
- **File:** `backend/app/services/rag_service.py`
- **Issue:** User input directly injected into prompts without sanitization
- **Fix:** Add `sanitize_user_input()` function with pattern filtering
- **Impact:** Copyright extraction, harmful content generation
- **Status:** 🔴 PENDING

#### 6. SCALE: WebSocket Connection Limits
- **File:** `backend/app/api/websocket/voice_chat.py`
- **Issue:** No limit on `active_sessions` dict, unbounded memory
- **Fix:** Add `MAX_CONCURRENT_SESSIONS = 500` per worker
- **Impact:** Server memory exhaustion at scale
- **Status:** 🔴 PENDING

#### 7. SCALE: Request Rate Limiting
- **Files:** Multiple route files
- **Issue:** No rate limiting on API endpoints
- **Fix:** Add slowapi middleware with per-user limits
- **Impact:** Single user can exhaust resources
- **Status:** 🔴 PENDING

---

## Week 2 (High Priority) - Days 8-14

### H01: Memory Leak - Blob URL Revocation
- **File:** `frontend/src/hooks/useChunkPlayer.ts`
- **Issue:** Old blob URLs not revoked on source change
- **Fix:** Call `URL.revokeObjectURL()` before switching audio source
- **Status:** 🟡 MEDIUM (LRU eviction partially mitigates)

### H04: Auth Dependency Consistency
- **Files:** `voice.py`, `wallet.py`, multiple routes
- **Issue:** Three different `get_current_user` functions with different return types
- **Fix:** Standardize on single auth dependency
- **Status:** 🔴 PENDING

### H05: STT Failure Fallback
- **File:** `backend/app/services/voice_service.py:183`
- **Issue:** Returns hardcoded question on STT failure, user charged for wrong answer
- **Fix:** Return explicit error, don't charge user
- **Status:** 🔴 PENDING

### H06: Card Ownership Verification
- **File:** `backend/app/api/routes/payments.py`
- **Issue:** No check that payment card belongs to current user
- **Fix:** Add ownership verification before card operations
- **Status:** 🔴 PENDING

### H07: Atomic Payment Status Updates
- **File:** `backend/app/api/routes/payments.py:488-561`
- **Issue:** Status change not atomic with balance changes
- **Fix:** Use MongoDB transactions or findOneAndUpdate
- **Status:** 🔴 PENDING

### H08: Voice Q&A Idempotency
- **File:** `backend/app/api/routes/voice.py`
- **Issue:** Client retry triggers full re-processing and double charge
- **Fix:** Add idempotency key tracking for voice Q&A
- **Status:** 🔴 PENDING

### AI: Citation Requirements
- **File:** `backend/app/services/rag_service.py`
- **Issue:** AI can hallucinate facts, no citation enforcement
- **Fix:** Update system prompt to require `[Quote: "..."]` format
- **Status:** 🔴 PENDING

### AI: Conversation History
- **Files:** `voice_chat.py`, `rag_service.py`
- **Issue:** AI has no memory of previous questions in session
- **Fix:** Pass conversation history to LLM in multi-turn format
- **Status:** 🔴 PENDING

### SCALE: N+1 Leaderboard Query
- **File:** `backend/app/services/leaderboard_service.py`
- **Issue:** Separate query per user in leaderboard
- **Fix:** Rewrite with single aggregation pipeline with $lookup
- **Status:** 🔴 PENDING

### SCALE: TTS Circuit Breaker
- **File:** `backend/app/api/websocket/voice_chat.py`
- **Issue:** No fallback when TTS service fails
- **Fix:** Add circuit breaker with text-only fallback
- **Status:** 🔴 PENDING

---

## Week 3 (Medium Priority) - Days 15-21

### H09-H14: Error Recovery and Edge Cases
- Token refresh gap handling
- readyState check improvements
- Session recovery time tracking
- Rapid chunk skip deduplication
- canplay/loadeddata race condition
- Concurrent loadingChunks access

### Admin Observability
- Add error aggregation service with auto-categorization
- Implement real-time WebSocket error dashboard
- Add search/filter for error logs
- Track error rates by endpoint

### AI Improvements
- Increase confidence threshold from 0.5 to 0.7
- Add out-of-scope question detection
- Replace mock voice Q&A implementation
- Fix RAG fallback random chunk retrieval

---

## Week 4 (Technical Debt) - Days 22-28

### M01-M15: Medium Priority Fixes
- Wallet service init failure handling
- Denormalized social stats locking
- Index creation error handling
- Datetime timezone consistency
- Session voice settings validation
- Chunk retry logic
- Prefetch cancellation
- Base64 response compression
- Progress percentage edge cases
- Mode switch time tracking
- Orphaned session cleanup
- Tracking queue limits
- WebSocket cleanup issues
- Invalid state combination prevention

### SCALE: Database Indexes
- Add leaderboard optimization index
- Add wallet_transactions compound index
- Verify all indexes are created on startup

---

## Post-Launch Monitoring (Days 29-90)

### Metrics to Track
1. **Error Rate:** Target <1% failed requests
2. **P99 Latency:** Target <500ms for API, <2s for TTS
3. **Memory Usage:** Watch for growth patterns
4. **WebSocket Connections:** Track concurrent users
5. **Payment Success Rate:** Target >98%
6. **Buffer Underrun Rate:** Target <5% of sessions

### Alerts to Configure
- Error rate spike (>5% in 5 min window)
- Memory usage >80% per worker
- WebSocket pool exhaustion
- TTS API failures
- Payment webhook failures
- Database query timeouts

---

## Architecture Recommendations for 100K Users

### Horizontal Scaling
- 20+ Uvicorn workers across 4+ servers
- Load balancer with sticky sessions for WebSocket
- Dedicated WebSocket gateway servers

### Background Processing
- Add Celery/RQ for TTS pre-generation
- Queue non-critical analytics writes
- Batch progress updates

### Caching Strategy
- Move leaderboard cache to Redis
- Add Redis for hot book metadata
- Pre-compute popular book chunks

### Database Optimization
- Shard wallet_transactions by user_id
- Add read replicas for analytics queries
- Consider time-series database for consumption_events

---

## Verification Checklist

Before each phase is complete, verify:

### Week 1
- [ ] All critical fixes deployed and tested
- [ ] Load test passed with 1000 concurrent users
- [ ] No memory leaks after 2-hour stress test
- [ ] Wallet operations verified atomic
- [ ] AI spoiler prevention confirmed

### Week 2
- [ ] High priority fixes deployed
- [ ] Error handling improved across services
- [ ] Payment flow end-to-end tested
- [ ] Voice Q&A idempotency verified

### Week 3
- [ ] Admin dashboard shows accurate data
- [ ] Real-time error monitoring active
- [ ] AI response quality improved

### Week 4
- [ ] Technical debt reduced
- [ ] All indexes verified
- [ ] Session cleanup automated
- [ ] Full test coverage achieved

---

## Contact Points

- **Backend Issues:** Review `backend/app/` routes and services
- **Frontend Issues:** Review `frontend/src/hooks/` and `frontend/src/lib/`
- **Infrastructure:** Check systemd services and nginx configs
- **Database:** MongoDB inkwave database

---

**Report Generated By:** Claude Code QA Analysis
**Methodology:** Static analysis, architectural review, persona-based scenario testing

# TTS Router Comparison: Unified vs TTS Services

**Date**: November 24, 2025
**Context**: Understanding why we have two TTS routers and their intended use cases

## Overview

We have **two TTS router implementations** serving different architectural needs:

1. **Unified TTS Router** (`shared/routes/tts_routes.py`) - 585 lines, 8 endpoints
2. **TTS Services Router** (`core_backend/backend/routes/tts_services.py`) - 1241 lines, 19 endpoints

---

## Detailed Comparison

### Architecture & Dependencies

| Aspect | Unified Router | TTS Services Router |
|--------|---------------|---------------------|
| **Location** | `shared/routes/tts_routes.py` | `core_backend/backend/routes/tts_services.py` |
| **Created** | 2025-11-23 (newer) | Earlier (production) |
| **TTS Client** | `AsyncTTSClient` (shared/tts/client.py) | `TTSProviderService` (shared/services/tts_provider_service.py) |
| **Purpose** | Shared library for all apps | Full-featured B2C portal API |
| **Lines of Code** | 585 | 1241 (2x larger) |
| **Endpoints** | 8 | 19 |

---

### Authentication Models

#### **Unified Router: Explicit user_id in Body**
```python
class SynthesizeRequest(BaseModel):
    user_id: str = Field(..., description="User ID for billing")  # ❌ In request body
    text: str
    provider: Optional[str]

@router.post("/synthesize")
async def synthesize_with_billing(
    request: SynthesizeRequest,  # No JWT validation
    billing_manager: TTSBillingManager = Depends(get_billing_manager)
):
```

**Pros:**
- ✅ Simple - no auth dependency needed
- ✅ Works for any app without JWT infrastructure
- ✅ Can be used by internal services (service-to-service calls)

**Cons:**
- ❌ **Security Risk**: Frontend can fake any user_id
- ❌ No authentication validation
- ❌ Susceptible to impersonation attacks

---

#### **TTS Services Router: JWT Token Authentication**
```python
class SynthesisRequestAPI(BaseModel):
    provider_id: str
    text: str
    language: str = "en"
    # NO user_id field - extracted from JWT

@router.post("/synthesize")
async def synthesize(
    req_body: SynthesisRequestAPI,
    request: Request,
    user: dict = Depends(get_current_user_mongo),  # ✅ JWT auth
    rate_limit: None = Depends(get_tts_rate_limit("synthesize", "free"))
):
    user_id = user.get("id") or user.get("sub") or user.get("user_id")
```

**Pros:**
- ✅ **Secure**: Cryptographically signed JWT prevents impersonation
- ✅ Standard OAuth2/JWT authentication pattern
- ✅ Rate limiting per authenticated user
- ✅ Clean API - no user_id in request body

**Cons:**
- ❌ Requires JWT auth infrastructure
- ❌ Not suitable for service-to-service calls without JWT

---

## Feature Comparison

### Unified Router Endpoints (8)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/synthesize` | POST | Basic synthesis with billing |
| `/clone-voice` | POST | Voice cloning with billing |
| `/providers` | GET | List providers |
| `/providers/{id}` | GET | Get provider details |
| `/estimate-cost` | GET | Estimate synthesis cost |
| `/cache/stats` | GET | Cache statistics |
| `/cache` | DELETE | Clear cache |
| `/health` | GET | Health check |

**Core Features:**
- Synthesis with billing
- Voice cloning
- Provider discovery
- Cost estimation
- Audio caching with stats

**Uses**:
- `AsyncTTSClient` from `shared/tts/client.py`
- `TTSBillingManager` for billing
- `TTSAudioCache` for caching
- `WalletService` for wallet integration

---

### TTS Services Router Endpoints (19)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/synthesize` | POST | Synthesis with JWT auth + billing |
| `/synthesize/upload` | POST | Voice cloning via multipart form |
| `/clone` | POST | Voice cloning (base64 audio) |
| `/estimate-cost` | POST | Cost estimation |
| `/voices` | GET | List Ghanaian voice samples |
| `/voices/{filename}` | GET | Download voice sample |
| `/voices/{voice_id}/preview` | GET | Get 5-second voice preview |
| `/providers` | GET | List providers with health status |
| `/providers/{id}` | GET | Get provider details |
| `/providers/{id}/languages` | GET | Get provider languages |
| `/providers/{id}/speakers` | GET | Get provider speakers/voices |
| `/health` | GET | Basic health check |
| `/health/status` | GET | Real-time health for all providers |
| `/health/metrics` | GET | Aggregated health metrics |
| `/health/{id}` | GET | Provider-specific health |
| `/health/test-notification` | POST | Test email alerts |
| `/history` | GET | User's synthesis history (paginated) |
| `/history/{id}` | GET | Get specific history item |
| `/history/{id}` | DELETE | Soft delete history item |

**Extended Features:**
- **Voice Library**: Pre-recorded Ghanaian voices (Nana Aba, Adom Okyere, etc.)
- **Audio History**: Track user's synthesis with search/filters
- **Health Monitoring**: Real-time provider status with email alerts
- **Rate Limiting**: Per-user, per-endpoint limits
- **Multi-format Upload**: Both multipart form and base64
- **Speaker Discovery**: Query available voices per provider

**Uses**:
- `TTSProviderService` from `shared/services/tts_provider_service.py`
- `AudioHistoryService` for history tracking
- Health monitoring with email alerts
- Rate limiting middleware
- MongoDB for history storage

---

## Why We Built Unified Router

### Original Problem
**Date**: ~November 23, 2025 (based on file creation)

**Context**: Multiple backend apps (StudyFlow, ChurchFlow, EventFlow, InkWave, ERP) needed TTS functionality but had different requirements:

1. **StudyFlow**: Educational app, students don't need full billing complexity
2. **ChurchFlow**: Church management, simple TTS for announcements
3. **EventFlow**: Event planning, basic TTS for invitations
4. **InkWave**: Writing assistant, lightweight TTS integration
5. **ERP**: Internal business app, service-to-service TTS calls

### Design Goals

✅ **Shared Library Pattern**
- Single TTS implementation for all apps
- Reduce code duplication
- Consistent TTS interface

✅ **Lightweight Integration**
- Simple request/response models
- No heavy dependencies (auth, rate limiting, history)
- Can be mounted in any FastAPI app

✅ **Service-to-Service Calls**
- Backend services can call TTS directly
- No JWT token required for internal services
- Pass user_id explicitly when known

✅ **Flexible Authentication**
- Apps can add their own auth layer
- Or use without auth for internal endpoints
- Not opinionated about auth strategy

---

## When to Use Each Router

### Use **Unified Router** When:

✅ **Building a new app** that needs basic TTS
- Simple integration, mount and use
- Add your own auth layer if needed

✅ **Service-to-service calls**
- Background jobs generating TTS
- Internal admin tools
- Microservices architecture

✅ **Prototyping/MVP**
- Quick TTS integration
- Minimal dependencies
- Focus on features, not infrastructure

✅ **Apps with custom auth**
- Not using MongoDB JWT
- Custom authentication system
- Want to handle user_id yourself

**Example**:
```python
# StudyFlow, ChurchFlow, etc.
from apps.shared.routes.tts_routes import router as tts_router
app.include_router(tts_router, prefix="/api/tts")

# Add your own auth if needed
@app.middleware("http")
async def add_user_context(request, call_next):
    # Your custom auth logic
    return await call_next(request)
```

---

### Use **TTS Services Router** When:

✅ **Production B2C application**
- User-facing TTS service
- Need security and auth
- Want rate limiting

✅ **Need advanced features**
- Audio history tracking
- Health monitoring with alerts
- Voice library management
- Provider health dashboard

✅ **JWT-based authentication**
- Using Supabase/MongoDB JWT
- Standard OAuth2 pattern
- User impersonation protection

✅ **Enterprise requirements**
- Rate limiting per user
- Email alerts for provider downtime
- Usage tracking and analytics
- Cost monitoring

**Example**:
```python
# Core Backend (B2C Portal)
from .routes.tts_services import router as tts_services_router
app.include_router(tts_services_router)  # Has prefix="/api/tts"

# Automatically gets:
# - JWT authentication
# - Rate limiting
# - History tracking
# - Health monitoring
```

---

## Current Production Usage

### Core Backend (B2C Portal)
- ✅ Uses: **TTS Services Router**
- Why: Full-featured user-facing TTS service
- Features: History, health monitoring, voice library

### StudyFlow
- ✅ Uses: **Unified Router**
- Why: Simple TTS for educational content
- Note: Also has TTS Services Router mounted (redundant)

### ChurchFlow, EventFlow, InkWave, ERP
- ✅ Uses: **Unified Router**
- Why: Lightweight TTS integration
- Simple synthesis without heavy dependencies

---

## Route Conflict Issue (Fixed)

### Problem
Core Backend had **both routers** mounted:
```python
app.include_router(unified_tts_router, prefix="/api/tts")  # ❌ First (wrong)
app.include_router(tts_services_router)  # ✅ Second (correct)
```

FastAPI matches **first** route → Unified router handled requests → Required `user_id` in body → 422 error

### Solution
**Commit**: `0cbac74d`
```python
# app.include_router(unified_tts_router, prefix="/api/tts")  # Disabled
app.include_router(tts_services_router)  # Only use this one
```

---

## Recommendations

### For Future Development

1. **Core Backend**: Keep using TTS Services Router
   - Full security and features needed for user-facing app

2. **StudyFlow/ChurchFlow/etc**: Use Unified Router
   - Simple integration sufficient
   - Can add custom auth if needed later

3. **New Apps**: Start with Unified Router
   - Easier integration
   - Upgrade to TTS Services Router if need advanced features

4. **Internal Services**: Use Unified Router
   - Service-to-service calls don't need JWT
   - Pass user_id explicitly

### Migration Path

If an app needs to **upgrade** from Unified → TTS Services:

1. Implement JWT authentication
2. Update frontend to send JWT tokens
3. Remove user_id from request bodies
4. Switch router import
5. Get advanced features (history, health monitoring)

**No breaking changes** - both routers use same underlying TTS providers.

---

## Technical Implementation Details

### Unified Router Uses:

```python
from shared.tts.client import AsyncTTSClient
from shared.tts.billing import TTSBillingManager
from shared.tts.cache import TTSAudioCache
from shared.integration.wallet import WalletService

# Direct client pattern
async with AsyncTTSClient() as client:
    response = await client.synthesize(TTSRequest(...))
```

**Pros:**
- Lightweight, minimal dependencies
- Direct control over TTS client
- Simple request/response flow

**Cons:**
- No singleton pattern
- Creates new client per request
- No health monitoring
- No history tracking

---

### TTS Services Router Uses:

```python
from apps.shared.services.tts_provider_service import (
    get_tts_service,
    TTSProviderService,
)

# Singleton service pattern
tts_service: TTSProviderService = await get_tts_service()
result = await tts_service.synthesize(user_id, request)
```

**Pros:**
- Singleton pattern (one service instance)
- Built-in health monitoring
- Automatic provider registry
- Billing integration
- History tracking

**Cons:**
- Heavier dependency
- More complex initialization
- Tightly coupled to MongoDB

---

## Conclusion

**Both routers are valid** - they serve different use cases:

- **Unified Router**: Lightweight, flexible, simple integration
- **TTS Services Router**: Full-featured, secure, production-ready

The confusion arose from having both in Core Backend. Now that we've disabled the Unified Router there, the system works correctly.

**Future**: Keep both routers, use appropriately per app requirements.

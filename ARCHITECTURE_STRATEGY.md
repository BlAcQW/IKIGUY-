# Multi-App Architecture Strategy
## Third-Party Developer API Support

**Date:** 2025-10-23
**Status:** Design & Planning Phase

---

## Executive Summary

This document outlines the architecture strategy for:
1. Supporting multiple internal apps that share Vapi/n8n integrations
2. Exposing stable, versioned APIs for third-party developers
3. Maintaining code reusability while ensuring independent scalability

**Recommended Approach:** Enhanced Shared Libraries + Dedicated Public API Layer (Option 1+)

---

## Current State Analysis

### Existing Architecture

```
@apps/
├── core_backend/              # Internal API for b2c-portal
│   ├── services/
│   │   ├── vapi_service.py            (395 lines - extends shared)
│   │   ├── n8n_service.py             (1203 lines - consolidated)
│   │   ├── vapi_sync_service.py
│   │   └── n8n_workflow_service.py
│   └── routes/
│       ├── vapi_consolidated.py
│       ├── vapi.py
│       ├── vapi_healthcare.py
│       ├── vapi_testing.py
│       └── n8n_templates.py
│
├── developer_platform/backend/  # Existing developer APIs
│   ├── core_proxy.py            # Proxy to core_backend (mTLS + JWT)
│   ├── main.py                  # FastAPI app with API key support
│   ├── security.py              # API key auth, rate limiting
│   └── services/
│       └── shared/              # Shared service abstractions
│
├── shared/                      # ✅ Already exists!
│   └── integration/
│       ├── vapi.py              # Base VAPIService class
│       ├── n8n.py               # Base N8NIntegration class
│       └── [50+ other integrations]
│
└── b2c-portal/                  # Frontend (uses core_backend)
```

### Key Findings

✅ **Good Foundation:**
- Shared integration library already exists (`@apps/shared/integration/`)
- `vapi.py` and `n8n.py` provide base classes
- `core_backend` extends shared classes (good pattern)
- `developer_platform` has API key auth + proxy pattern

⚠️ **Needs Improvement:**
- `developer_platform` doesn't expose Vapi/n8n APIs yet
- No API versioning (v1, v2) for stability
- Some duplication between `core_backend` services and `shared/integration`
- Missing rate limiting & usage tracking for public APIs

---

## Recommended Architecture

### Three-Tier Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    TIER 1: Shared Libraries                  │
│                   @apps/shared/integration/                  │
│                                                              │
│  • Core integration logic (Vapi, n8n, etc.)                 │
│  • Reusable across ALL apps                                 │
│  • No business logic, just integration mechanics            │
│  • Well-tested, stable                                      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ imports
                ┌─────────────┴──────────────┐
                │                            │
┌───────────────▼────────┐    ┌──────────────▼───────────────┐
│  TIER 2: Internal APIs │    │ TIER 3: Public Developer API │
│                        │    │                              │
│  • @core_backend/      │    │  • @developer_platform/      │
│  • @new_app_backend/   │    │                              │
│                        │    │  Enhancements:               │
│  Characteristics:      │    │  ✓ Versioned endpoints (v1/) │
│  • Fast iteration      │    │  ✓ API key authentication    │
│  • Breaking changes OK │    │  ✓ Rate limiting             │
│  • JWT/session auth    │    │  ✓ Usage tracking & billing  │
│  • Internal use only   │    │  ✓ Comprehensive OpenAPI docs│
└────────────────────────┘    │  ✓ Stable contracts          │
                              │  ✓ No breaking changes       │
                              └──────────────────────────────┘
```

---

## Detailed Component Design

### 1. Shared Integration Layer (`@apps/shared/integration/`)

**Purpose:** DRY principle - single source of truth for integration logic

**Current State:**
- ✅ `vapi.py` - Base `VAPIService` class with core functionality
- ✅ `n8n.py` - Base `N8NIntegration` class with workflow management
- ⚠️ Some functionality duplicated in `core_backend/services/`

**Enhancements Needed:**
```python
# @apps/shared/integration/vapi.py (already exists, enhance)
class VAPIService:
    """Core Vapi integration - used by ALL backends."""

    async def create_assistant(self, config: VAPIAgent) -> Dict[str, Any]:
        """Create Vapi assistant - actual API call."""

    async def initiate_call(self, call_config: VAPICall) -> Dict[str, Any]:
        """Initiate outbound call."""

    async def get_call_logs(self, filters: dict) -> List[Dict]:
        """Fetch call logs."""

    # Add methods from core_backend/services/vapi_service.py that are generic
```

**Migration Strategy:**
1. Move generic methods from `core_backend/services/vapi_service.py` to `shared/integration/vapi.py`
2. Keep tenant-specific logic in `core_backend`
3. Ensure no breaking changes to existing code

---

### 2. Internal Backend APIs (`@core_backend/`, new apps)

**Purpose:** Fast-moving internal APIs for your own apps

**Architecture:**
```python
# @apps/core_backend/backend/services/vapi_service.py
from shared.integration.vapi import VAPIService

class VAPIServiceWrapper(VAPIService):
    """Core backend specific Vapi service - extends shared."""

    def __init__(self, tenant_db, config):
        super().__init__(config)
        self.tenant_db = tenant_db  # Business logic specific to core_backend

    async def create_tenant_agent(self, tenant_id, agent):
        """Tenant-specific logic (not in shared library)."""
        # Can change quickly without affecting other apps
```

**Routes:**
```python
# @apps/core_backend/backend/routes/internal_vapi.py
@router.post("/internal/vapi/quick-assistant")  # Can change anytime
async def quick_assistant(data: dict, user = Depends(get_current_user)):
    service = VAPIServiceWrapper(tenant_db, config)
    return await service.create_tenant_agent(user.tenant_id, data)
```

**Characteristics:**
- ✅ Import directly from `@apps/shared/`
- ✅ Add app-specific business logic
- ✅ Can iterate quickly
- ✅ Breaking changes are acceptable (you control all clients)
- ✅ Simple auth (JWT, session, internal tokens)

---

### 3. Public Developer Platform API (`@developer_platform/backend/`)

**Purpose:** Stable, versioned APIs for third-party developers

**Current State:**
- ✅ Has API key authentication (`security.py`)
- ✅ Has proxy pattern to `core_backend` (`core_proxy.py`)
- ⚠️ No Vapi/n8n endpoints exposed yet
- ⚠️ No API versioning
- ⚠️ Limited rate limiting

**Enhanced Architecture:**

```
@apps/developer_platform/backend/
├── api/
│   ├── v1/                           # Version 1 (stable)
│   │   ├── __init__.py
│   │   ├── vapi.py                   # Public Vapi endpoints
│   │   ├── n8n.py                    # Public n8n endpoints
│   │   ├── assistants.py
│   │   ├── campaigns.py
│   │   └── calls.py
│   │
│   └── v2/                           # Future version (when v1 needs breaking changes)
│       └── ...
│
├── middleware/
│   ├── api_key_auth.py               # ✅ Already exists
│   ├── rate_limiter.py               # Need to enhance
│   ├── usage_tracker.py              # Need to add
│   └── request_validator.py
│
├── models/
│   ├── v1/
│   │   ├── vapi_models.py            # Strict Pydantic schemas
│   │   └── n8n_models.py
│   └── v2/
│
├── services/
│   ├── billing_service.py            # Track usage for billing
│   └── analytics_service.py
│
├── core_proxy.py                     # ✅ Already exists
└── main.py                           # ✅ Already exists
```

**Example Public API Endpoint:**

```python
# @apps/developer_platform/backend/api/v1/vapi.py
from fastapi import APIRouter, Depends, HTTPException
from shared.integration.vapi import VAPIService
from ..middleware import verify_api_key, rate_limiter, track_usage
from .models import CreateAssistantRequest, AssistantResponse

router = APIRouter(prefix="/api/v1/assistants", tags=["Assistants v1"])

@router.post("/", response_model=AssistantResponse)
async def create_assistant(
    request: CreateAssistantRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(rate_limiter("10/minute"))
):
    """
    Create a Vapi assistant.

    **This endpoint is versioned and stable.**

    Rate limit: 10 requests/minute
    Scopes required: `assistants:write`

    See full documentation at https://developer.ailabsafrica.com/docs/v1/assistants
    """
    # Track usage for billing
    await track_usage(api_key, endpoint="create_assistant", credits=1)

    # Use shared integration library
    vapi_service = VAPIService(config=get_vapi_config())
    result = await vapi_service.create_assistant(request.to_vapi_agent())

    # Return stable response format
    return AssistantResponse.from_vapi_response(result)
```

**Characteristics:**
- ✅ Versioned endpoints (`/api/v1/`, `/api/v2/`)
- ✅ Strict input validation (Pydantic models)
- ✅ Stable response schemas (documented)
- ✅ API key authentication
- ✅ Rate limiting per API key
- ✅ Usage tracking for billing
- ✅ Comprehensive OpenAPI documentation
- ✅ Deprecation warnings before v1 → v2 migration
- ❌ Cannot make breaking changes without new version

---

## Implementation Plan

### Phase 1: Foundation Enhancement (Week 1)

**Goal:** Strengthen shared libraries and ensure consistency

**Tasks:**
1. ✅ Audit existing `shared/integration/vapi.py` and `n8n.py`
2. Extract generic methods from `core_backend/services/vapi_service.py` to shared
3. Extract generic methods from `core_backend/services/n8n_service.py` to shared
4. Update `core_backend` to extend (not duplicate) shared classes
5. Add comprehensive tests for shared integration layer
6. Update `shared/integration/__init__.py` to export Vapi/n8n classes

**Success Criteria:**
- All core Vapi/n8n logic is in `@apps/shared/integration/`
- `core_backend` uses shared classes without duplication
- 100% of existing functionality still works

---

### Phase 2: Developer Platform API Structure (Week 2)

**Goal:** Create versioned API structure in `developer_platform`

**Tasks:**
1. Create `api/v1/` directory structure
2. Add Pydantic models for v1 API contracts
3. Implement versioned Vapi endpoints:
   - `POST /api/v1/assistants` - Create assistant
   - `GET /api/v1/assistants` - List assistants
   - `GET /api/v1/assistants/{id}` - Get assistant
   - `PATCH /api/v1/assistants/{id}` - Update assistant
   - `DELETE /api/v1/assistants/{id}` - Delete assistant
4. Implement versioned n8n endpoints:
   - `POST /api/v1/workflows` - Create workflow
   - `GET /api/v1/workflows` - List workflows
   - `POST /api/v1/workflows/{id}/execute` - Execute workflow
5. Add OpenAPI documentation with examples

**Success Criteria:**
- All endpoints accessible at `/api/v1/*`
- OpenAPI docs show clear request/response schemas
- All endpoints require valid API key

---

### Phase 3: Rate Limiting & Usage Tracking (Week 2-3)

**Goal:** Add production-grade API management

**Tasks:**
1. Enhance rate limiting middleware:
   - Per-API-key limits
   - Per-endpoint limits
   - Configurable limits (free vs paid tiers)
2. Add usage tracking:
   - Log all API calls with metadata
   - Track credits/quota consumption
   - Store in MongoDB for billing
3. Add usage dashboard endpoints:
   - `GET /api/v1/usage` - Current usage
   - `GET /api/v1/usage/history` - Historical usage
4. Add quota enforcement:
   - Reject requests when quota exceeded
   - Return clear error messages with quota info

**Success Criteria:**
- Rate limits enforced per API key
- Usage tracked in database
- Developers can see their usage

---

### Phase 4: Documentation & Developer Experience (Week 3-4)

**Goal:** Make APIs easy to discover and use

**Tasks:**
1. Create comprehensive API documentation site
2. Add code examples in multiple languages:
   - Python
   - JavaScript/TypeScript
   - cURL
3. Create quickstart guides:
   - "Create your first assistant in 5 minutes"
   - "Trigger n8n workflows via API"
4. Add webhook documentation
5. Create API changelog for version tracking
6. Add developer sandbox environment

**Success Criteria:**
- Documentation covers all endpoints
- Code examples work copy-paste
- Quickstart guide takes <5 minutes

---

### Phase 5: New Internal Apps (Ongoing)

**Goal:** Enable new internal apps to reuse Vapi/n8n easily

**For each new app:**

```bash
# 1. Create new backend
mkdir -p @apps/new_app_backend/services
mkdir -p @apps/new_app_backend/routes

# 2. Import shared integrations
# @apps/new_app_backend/services/vapi_wrapper.py
from shared.integration.vapi import VAPIService

class NewAppVapiService(VAPIService):
    """App-specific Vapi service."""

    def __init__(self):
        super().__init__(config=load_config())
        # Add app-specific logic

    async def custom_business_logic(self):
        # Use inherited methods from VAPIService
        result = await self.create_assistant(...)
        # Add app-specific processing
        return result

# 3. Create app-specific routes
# @apps/new_app_backend/routes/vapi.py
from ..services.vapi_wrapper import NewAppVapiService

@router.post("/app-vapi/custom-endpoint")
async def custom_endpoint():
    service = NewAppVapiService()
    return await service.custom_business_logic()
```

**Characteristics:**
- Each app imports from `@apps/shared/`
- Each app adds its own business logic
- No cross-app dependencies
- Independent scaling and deployment

---

## API Versioning Strategy

### When to Create a New Version

Create v2 when you need to make **breaking changes** to v1:

**Breaking Changes:**
- Removing a field from response
- Renaming a field
- Changing field type (string → int)
- Changing endpoint URL
- Removing an endpoint
- Changing authentication method

**Non-Breaking Changes (OK in v1):**
- Adding new optional fields
- Adding new endpoints
- Adding new enum values (if backwards compatible)
- Improving error messages
- Performance improvements
- Bug fixes

### Version Lifecycle

```
v1 (stable)
├── Launch: Day 1
├── Add features: Months 1-12 (non-breaking only)
├── Deprecation notice: Month 12
├── v2 launch: Month 13
├── v1 maintenance mode: Months 13-18
└── v1 sunset: Month 18

v2 (stable)
├── Launch: Month 13
├── Add features: Months 13-24
└── ...
```

### Implementation

```python
# @apps/developer_platform/backend/api/v1/vapi.py
router = APIRouter(prefix="/api/v1", tags=["Assistants v1"])

# @apps/developer_platform/backend/api/v2/vapi.py
router = APIRouter(prefix="/api/v2", tags=["Assistants v2"])

# Both can coexist, giving developers time to migrate
```

---

## Security Considerations

### API Key Management

```python
# Different key types for different use cases
class APIKeyType(Enum):
    PRODUCTION = "production"    # Full access, billed
    DEVELOPMENT = "development"  # Limited quota, free
    SANDBOX = "sandbox"          # Fake data, testing only
```

### Scopes & Permissions

```python
# Fine-grained permissions
class APIScope(Enum):
    ASSISTANTS_READ = "assistants:read"
    ASSISTANTS_WRITE = "assistants:write"
    CALLS_INITIATE = "calls:initiate"
    WORKFLOWS_EXECUTE = "workflows:execute"
    # etc.

# API keys can have subset of scopes
```

### Rate Limiting Tiers

```python
class RateLimitTier(Enum):
    FREE = {
        "requests_per_minute": 10,
        "requests_per_day": 1000,
        "quota_per_month": 10000  # credits
    }
    STARTER = {
        "requests_per_minute": 60,
        "requests_per_day": 10000,
        "quota_per_month": 100000
    }
    PROFESSIONAL = {
        "requests_per_minute": 300,
        "requests_per_day": 100000,
        "quota_per_month": 1000000
    }
```

---

## Testing Strategy

### 1. Shared Integration Tests

```python
# @apps/shared/tests/integration/test_vapi.py
def test_vapi_create_assistant():
    service = VAPIService(config=test_config)
    result = await service.create_assistant(mock_agent)
    assert result["success"] == True

# Run these tests before deploying ANY app
```

### 2. Internal API Tests

```python
# @apps/core_backend/tests/test_vapi_routes.py
def test_internal_vapi_endpoint():
    # Test internal endpoints with JWT auth
    response = client.post("/internal/vapi/quick-assistant",
                           headers={"Authorization": f"Bearer {jwt}"})
    assert response.status_code == 200
```

### 3. Public API Tests

```python
# @apps/developer_platform/tests/api/v1/test_vapi.py
def test_public_vapi_endpoint():
    # Test with API key
    response = client.post("/api/v1/assistants",
                           headers={"X-API-Key": test_api_key})
    assert response.status_code == 200
    # Verify response matches OpenAPI schema

def test_rate_limiting():
    # Make 11 requests (limit is 10/minute)
    for i in range(11):
        response = client.post("/api/v1/assistants",
                               headers={"X-API-Key": test_api_key})
    assert response.status_code == 429  # Too Many Requests

def test_usage_tracking():
    # Make request
    client.post("/api/v1/assistants",
                headers={"X-API-Key": test_api_key})
    # Check usage was recorded
    usage = get_usage(test_api_key)
    assert usage["assistants_created"] == 1
```

---

## Monitoring & Observability

### Key Metrics to Track

**Per API Key:**
- Request count (total, success, failure)
- Response time (p50, p95, p99)
- Error rate
- Quota usage
- Rate limit hits

**Per Endpoint:**
- Request volume
- Response time
- Error rate
- Most common errors

**Per App (internal):**
- Request volume to shared integrations
- Integration success rate
- Response time to Vapi/n8n APIs

### Logging Strategy

```python
# Structured logging for all API calls
logger.info("API request", extra={
    "api_key": api_key_hash,
    "endpoint": request.url.path,
    "method": request.method,
    "response_code": response.status_code,
    "response_time_ms": elapsed_ms,
    "quota_used": credits_used,
    "user_agent": request.headers.get("user-agent")
})
```

---

## Migration Checklist

### For Existing `core_backend`:

- [ ] Identify generic Vapi methods in `services/vapi_service.py`
- [ ] Move generic methods to `shared/integration/vapi.py`
- [ ] Update `core_backend` to extend shared class
- [ ] Run existing tests to ensure no breakage
- [ ] Identify generic n8n methods in `services/n8n_service.py`
- [ ] Move generic methods to `shared/integration/n8n.py`
- [ ] Update `core_backend` to extend shared class
- [ ] Run existing tests to ensure no breakage

### For `developer_platform`:

- [ ] Create `api/v1/` directory structure
- [ ] Create Pydantic models for v1 contracts
- [ ] Implement Vapi endpoints using shared library
- [ ] Implement n8n endpoints using shared library
- [ ] Add rate limiting middleware
- [ ] Add usage tracking
- [ ] Generate OpenAPI documentation
- [ ] Add tests for all endpoints
- [ ] Deploy to staging environment
- [ ] Test with sample API keys
- [ ] Deploy to production

### For New Apps:

- [ ] Create app directory structure
- [ ] Import shared integration library
- [ ] Create app-specific service wrappers
- [ ] Create app-specific routes
- [ ] Add authentication (JWT/session)
- [ ] Add tests
- [ ] Deploy

---

## File Structure Reference

```
@apps/
├── shared/                                    # ← TIER 1: Shared Libraries
│   └── integration/
│       ├── __init__.py                        # Export VAPIService, N8NIntegration
│       ├── vapi.py                            # ✅ Core Vapi integration
│       ├── n8n.py                             # ✅ Core n8n integration
│       └── [other integrations]
│
├── core_backend/                              # ← TIER 2: Internal API
│   ├── services/
│   │   ├── vapi_service.py                    # Extends shared VAPIService
│   │   └── n8n_service.py                     # Extends shared N8NIntegration
│   └── routes/
│       ├── internal_vapi.py                   # Internal routes (fast iteration)
│       └── internal_n8n.py
│
├── developer_platform/backend/                # ← TIER 3: Public API
│   ├── api/
│   │   ├── v1/                                # ✅ Version 1 (stable)
│   │   │   ├── vapi.py                        # Public Vapi endpoints
│   │   │   ├── n8n.py                         # Public n8n endpoints
│   │   │   ├── assistants.py
│   │   │   ├── campaigns.py
│   │   │   └── calls.py
│   │   └── v2/                                # Future version
│   ├── middleware/
│   │   ├── api_key_auth.py                    # ✅ Already exists
│   │   ├── rate_limiter.py                    # Need to enhance
│   │   └── usage_tracker.py                   # Need to add
│   ├── models/
│   │   └── v1/
│   │       ├── vapi_models.py                 # Strict Pydantic schemas
│   │       └── n8n_models.py
│   └── main.py                                # ✅ Already exists
│
└── new_app_backend/                           # ← TIER 2: Another Internal API
    ├── services/
    │   ├── vapi_wrapper.py                    # Extends shared VAPIService
    │   └── n8n_wrapper.py                     # Extends shared N8NIntegration
    └── routes/
        ├── app_vapi.py                        # App-specific routes
        └── app_n8n.py
```

---

## Decision Matrix: When to Use Each Tier

| Scenario | Use This Tier | Why |
|----------|---------------|-----|
| Your internal SaaS app needs Vapi | TIER 2 (Internal API) | Fast iteration, no versioning burden |
| Third-party developer integration | TIER 3 (Public API) | Stable, versioned, documented |
| Building new internal app | TIER 2 (Internal API) | Import shared library, add business logic |
| Need to change Vapi core behavior | TIER 1 (Shared Library) | Change once, affects all apps |
| Need to add app-specific Vapi logic | TIER 2 (Internal API) | Extend shared class in app backend |
| Need to expose new public API | TIER 3 (Public API) | Add versioned endpoint, maintain stability |

---

## Success Metrics

### Phase 1 Success:
- ✅ Zero code duplication between apps and shared library
- ✅ All existing functionality works unchanged
- ✅ 100% test coverage on shared integration library

### Phase 2-3 Success:
- ✅ Public API v1 endpoints operational
- ✅ Rate limiting enforced
- ✅ Usage tracking working
- ✅ OpenAPI documentation complete

### Phase 4 Success:
- ✅ Developer can create assistant in <5 minutes with docs
- ✅ Code examples work copy-paste
- ✅ Support tickets < 5/week related to API confusion

### Long-term Success:
- ✅ New internal apps can integrate Vapi/n8n in <1 day
- ✅ Third-party developers successfully using public APIs
- ✅ Zero breaking changes to v1 API (maintain backwards compatibility)
- ✅ v2 API only created when absolutely necessary

---

## Next Steps

1. **Review this document** - Ensure alignment with team and stakeholders
2. **Prioritize phases** - Determine which phases are most critical
3. **Begin Phase 1** - Start strengthening shared integration library
4. **Set up tracking** - Create issues/tasks for each phase
5. **Schedule check-ins** - Weekly reviews of migration progress

---

## Questions & Answers

**Q: Do we need to migrate all internal apps at once?**
A: No. Migration can be gradual. Start with `core_backend`, then add new apps.

**Q: What if an internal app needs custom Vapi logic?**
A: Extend the shared `VAPIService` class in your app's service layer. Keep generic logic in shared, app-specific logic in your app.

**Q: How do we handle breaking changes in Vapi's own API?**
A: Handle in shared library (`@apps/shared/integration/vapi.py`). This protects all apps from upstream changes.

**Q: Can internal apps call the public API?**
A: They can, but shouldn't. Internal apps should import shared libraries directly for better performance and flexibility.

**Q: How do we test the public API without affecting production?**
A: Use sandbox API keys that point to test environment. Provide fake/mock data for testing.

**Q: What about webhooks?**
A: Public API can register webhooks. Implementation:
- `POST /api/v1/webhooks` - Register webhook URL
- Webhook signature verification for security
- Retry logic for failed webhook deliveries

---

## Appendix: Code Examples

### Example 1: Extending Shared Vapi Service

```python
# @apps/core_backend/backend/services/vapi_service.py
from shared.integration.vapi import VAPIService, VAPIAgent

class CoreBackendVapiService(VAPIService):
    """Core backend specific Vapi service."""

    def __init__(self, tenant_db, config):
        super().__init__(config)
        self.tenant_db = tenant_db

    async def create_tenant_agent(self, tenant_id: str, agent: VAPIAgent):
        """
        Create agent with tenant context.
        Uses inherited create_assistant() from shared library.
        """
        # Add tenant context
        agent.metadata["tenant_id"] = tenant_id

        # Call shared library method
        result = await self.create_assistant(agent)

        # Save to tenant database
        await self.tenant_db.agents.insert_one({
            "tenant_id": tenant_id,
            "vapi_agent_id": result["agent_id"],
            "created_at": datetime.now()
        })

        return result
```

### Example 2: Public API Endpoint

```python
# @apps/developer_platform/backend/api/v1/vapi.py
from fastapi import APIRouter, Depends
from shared.integration.vapi import VAPIService, VAPIAgent
from ..middleware import verify_api_key, rate_limiter, track_usage
from ..models.v1.vapi_models import CreateAssistantRequest, AssistantResponse

router = APIRouter(prefix="/api/v1/assistants", tags=["Assistants v1"])

@router.post("/", response_model=AssistantResponse, status_code=201)
async def create_assistant(
    request: CreateAssistantRequest,
    api_key: dict = Depends(verify_api_key),
    _rate_limit: None = Depends(rate_limiter("10/minute"))
):
    """
    Create a new Vapi assistant.

    **Rate Limit:** 10 requests/minute
    **Scopes Required:** `assistants:write`

    **Example Request:**
    ```json
    {
        "name": "Sales Assistant",
        "system_prompt": "You are a helpful sales assistant...",
        "voice": "alloy",
        "language": "en"
    }
    ```

    **Example Response:**
    ```json
    {
        "id": "asst_123abc",
        "name": "Sales Assistant",
        "status": "active",
        "created_at": "2025-10-23T10:00:00Z"
    }
    ```
    """
    # Track usage for billing
    await track_usage(
        api_key_id=api_key["id"],
        endpoint="create_assistant",
        credits=1
    )

    # Use shared integration library
    vapi_service = VAPIService(config=get_vapi_config())

    # Convert request to VAPIAgent
    agent = VAPIAgent(
        name=request.name,
        system_prompt=request.system_prompt,
        voice=request.voice,
        language=request.language
    )

    # Create assistant
    result = await vapi_service.create_assistant(agent)

    # Return stable response
    return AssistantResponse(
        id=result["agent_id"],
        name=result["name"],
        status=result["status"],
        created_at=result["created_at"]
    )
```

### Example 3: Rate Limiter Middleware

```python
# @apps/developer_platform/backend/middleware/rate_limiter.py
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def rate_limiter(limit: str):
    """
    Rate limiter dependency.

    Args:
        limit: Format "requests/period" (e.g., "10/minute", "1000/day")
    """
    async def check_rate_limit(request: Request, api_key: dict = Depends(verify_api_key)):
        requests_limit, period = limit.split("/")
        requests_limit = int(requests_limit)

        # Redis key: api_key_id:endpoint:period
        key = f"rate_limit:{api_key['id']}:{request.url.path}:{period}"

        # Increment counter
        current_count = redis_client.incr(key)

        # Set expiry on first request
        if current_count == 1:
            if period == "minute":
                redis_client.expire(key, 60)
            elif period == "hour":
                redis_client.expire(key, 3600)
            elif period == "day":
                redis_client.expire(key, 86400)

        # Check if limit exceeded
        if current_count > requests_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Limit: {limit}",
                headers={"Retry-After": str(redis_client.ttl(key))}
            )

    return check_rate_limit
```

---

**End of Document**

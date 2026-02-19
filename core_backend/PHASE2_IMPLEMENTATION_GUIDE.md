# Phase 2: Organization Context Implementation Guide

**Date**: November 9, 2025
**Status**: Implementation Ready
**Previous Phase**: Phase 1 completed 56 endpoints

---

## 🎯 Quick Start

This guide provides step-by-step instructions for implementing organization context across all remaining core_backend endpoints.

### Files Status:
- ✅ **Phase 1 Complete** (56 endpoints): knowledge_base.py, vapi_consolidated.py, premier_health.py, automation_configs.py, organizations.py, admin.py
- 🔴 **Critical Priority** (74 endpoints): wallet.py, analytics.py, vapi_assistants.py, call_logs.py
- 🟠 **High Priority** (32 endpoints): campaigns.py, voice_campaigns.py (need tenant_id migration)
- 🟡 **Medium Priority** (20 endpoints): voice_library.py, call_management.py, automation_analytics.py, integration_webhooks.py

---

## 📚 Standard Implementation Pattern

### Step 1: Add Imports
```python
from ..middleware.organization_context import (
    get_organization_context,
    get_user_organization_filter,
    validate_organization_access
)
```

### Step 2: Add Request Parameter
```python
# Before:
async def my_endpoint(
    current_user: Dict = Depends(get_current_user_mongo)
):

# After:
async def my_endpoint(
    request: Request,  # ADD THIS
    current_user: Dict = Depends(get_current_user_mongo)
):
```

### Step 3: Add Organization Validation
```python
async def my_endpoint(
    request: Request,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Endpoint description.

    Now properly scoped to organization. Requires authentication.  # ADD THIS
    """
    try:
        # Get and validate organization context  # ADD THIS BLOCK
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Your existing endpoint logic here
        ...

    except HTTPException:  # ADD THIS
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 4: Update Database Queries
```python
# Before:
results = await collection.find({"user_id": user_id}).to_list(100)

# After - Option 1 (Simple filter):
org_filter = get_user_organization_filter(current_user, org_id)
query = {**org_filter, "user_id": user_id}
results = await collection.find(query).to_list(100)

# After - Option 2 (Direct organization_id):
query = {"user_id": user_id}
if org_id:
    query["organization_id"] = org_id
results = await collection.find(query).to_list(100)
```

### Step 5: Add Organization to Created Documents
```python
# When creating new documents:
document = {
    "user_id": user_id,
    "organization_id": org_id,  # ADD THIS
    "data": request_data,
    "created_at": datetime.utcnow()
}
await collection.insert_one(document)
```

---

## 🔴 FILE 1: wallet.py - Financial Operations (CRITICAL)

**Endpoints**: 16 (12 authenticated + 4 webhooks)
**Risk**: Financial data exposure across organizations

### Authenticated Endpoints (12):
1. `GET /balance` - ✅ DONE (example completed)
2. `GET /settings` - Need to secure
3. `PATCH /settings` - Need to secure
4. `GET /payment-methods` - Need to secure
5. `POST /payment-methods` - Need to secure
6. `PATCH /payment-methods/{id}` - Need to secure
7. `DELETE /payment-methods/{id}` - Need to secure
8. `POST /deposit` - Need to secure
9. `GET /transactions` - Need to secure
10. `GET /transactions/{id}` - Need to secure
11. `GET /transactions/{id}/receipt` - Need to secure
12. `GET /providers` - Need to secure

### Implementation for Each Endpoint:

```python
# Example: GET /settings
@router.get("/settings", response_model=WalletSettingsResponse)
async def get_wallet_settings(
    request: Request,  # ADD
    currency: Currency = Currency.USD,
    current_user: Dict = Depends(get_current_user_mongo),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """
    Get wallet settings for current user.

    Returns auto-reload and alert settings.

    Now properly scoped to organization. Requires authentication.  # ADD
    """
    try:
        # ADD THIS BLOCK
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("sub") or current_user.get("user_id")

        # ADD organization_id parameter
        wallet = await wallet_service.get_or_create_wallet(
            user_id,
            currency,
            organization_id=org_id  # ADD
        )

        return WalletSettingsResponse(...)

    except HTTPException:  # ADD
        raise
    except Exception as e:
        logger.error(f"Failed to get wallet settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Webhook Endpoints (4):
Track organization in metadata/payload:

```python
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook handler.

    Webhook endpoint - organization context tracked in metadata.  # ADD
    """
    body = await request.json()

    # Extract organization from metadata
    metadata = body.get("data", {}).get("object", {}).get("metadata", {})
    org_id = metadata.get("organization_id")

    logger.info(f"Stripe webhook for org: {org_id}")  # ADD LOGGING

    # Process webhook with organization context
    ...
```

### Service Layer Updates:

**File**: `/opt/kasaai/apps/core_backend/backend/services/wallet_service.py`

Update all wallet service methods to accept and use `organization_id`:

```python
async def get_or_create_wallet(
    self,
    user_id: str,
    currency: Currency = Currency.USD,
    organization_id: Optional[str] = None  # ADD THIS
) -> Wallet:
    """Get or create wallet for user."""

    # Build query with organization context
    query = {
        "user_id": user_id,
        "currency": currency.value
    }
    if organization_id:  # ADD THIS
        query["organization_id"] = organization_id

    wallet = await self.wallets_collection.find_one(query)

    if not wallet:
        # Create with organization
        wallet_data = {
            "user_id": user_id,
            "currency": currency.value,
            "organization_id": organization_id,  # ADD THIS
            "balance": Decimal("0.00"),
            "created_at": datetime.utcnow()
        }
        result = await self.wallets_collection.insert_one(wallet_data)
        ...
```

---

## 🔴 FILE 2: analytics.py - Metrics & Cost Data (CRITICAL)

**Endpoints**: 12
**Risk**: Financial metrics and sensitive analytics exposed

### All Endpoints Need Securing:
1. `GET /overview`
2. `GET /automations`
3. `GET /automations/{automation_id}/health`
4. `GET /vapi`
5. `GET /n8n`
6. `GET /costs`  ← CRITICAL (financial)
7. `GET /profit-margins`  ← CRITICAL (financial)
8. `GET /services/{service}`
9. `GET /tenants/{tenant_id}`  ← Needs tenant_id → organization_id migration
10. `GET /campaigns`
11. `GET /integrations`
12. `GET /dashboard-data`

### Implementation Example:

```python
# Example: GET /costs
@router.get("/costs")
async def get_cost_analytics(
    request: Request,  # ADD
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: Dict = Depends(get_current_user_mongo)
):
    """
    Get cost analytics.

    Now properly scoped to organization. Requires authentication.  # ADD
    """
    try:
        # ADD organization validation
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Build query with organization filter
        org_filter = get_user_organization_filter(current_user, org_id)

        query = {**org_filter}
        if start_date:
            query["created_at"] = {"$gte": start_date}
        if end_date:
            query.setdefault("created_at", {})["$lte"] = end_date

        # Query with organization filtering
        cost_data = await db.costs.aggregate([
            {"$match": query},
            {"$group": {
                "_id": "$service",
                "total_cost": {"$sum": "$amount"}
            }}
        ]).to_list(None)

        return {"costs": cost_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cost analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🟠 FILE 3: campaigns.py - Campaign Management (MIGRATION REQUIRED)

**Endpoints**: 12
**Risk**: Uses deprecated `tenant_id` instead of `organization_id`

### Migration Steps:

1. **Find all tenant_id references**:
```bash
grep -n "tenant_id" /opt/kasaai/apps/core_backend/backend/routes/campaigns.py
```

2. **Replace tenant_id with organization_id**:
```python
# OLD:
tenant_id = current_user.get("tenant_id", "default")
query = {"tenant_id": tenant_id}

# NEW:
org_id = get_organization_context(request)
if org_id:
    await validate_organization_access(request, current_user, org_id)

org_filter = get_user_organization_filter(current_user, org_id)
query = {**org_filter}
```

3. **Update database queries**:
```python
# OLD:
campaign = await campaigns_collection.find_one({
    "_id": campaign_id,
    "tenant_id": tenant_id
})

# NEW:
org_filter = get_user_organization_filter(current_user, org_id)
campaign = await campaigns_collection.find_one({
    "_id": campaign_id,
    **org_filter
})
```

4. **Update created documents**:
```python
# OLD:
campaign_data = {
    "tenant_id": current_user.get("tenant_id", "default"),
    "name": request.name,
    ...
}

# NEW:
campaign_data = {
    "organization_id": org_id,  # CHANGED
    "name": request.name,
    ...
}
```

---

## 🔴 FILE 4: vapi_assistants.py - Assistant Management (CRITICAL)

**Endpoints**: 5
**Risk**: Assistants accessible across organizations

### All Endpoints:
1. `POST /` - create_assistant
2. `GET /` - list_assistants
3. `GET /{assistant_id}` - get_assistant
4. `PATCH /{assistant_id}` - update_assistant
5. `DELETE /{assistant_id}` - delete_assistant

### Implementation Example:

```python
@router.post("/", status_code=201)
async def create_assistant(
    request: Request,  # ADD
    assistant_data: AssistantCreate,
    current_user: Dict = Depends(get_current_user_mongo),
    db=Depends(get_database)
):
    """
    Create a new VAPI assistant.

    Now properly scoped to organization. Requires authentication.  # ADD
    """
    try:
        # ADD organization validation
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        user_id = current_user.get("id") or current_user.get("sub")

        # Create assistant with organization
        assistant = {
            "name": assistant_data.name,
            "organization_id": org_id,  # ADD
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            **assistant_data.dict(exclude={"name"})
        }

        result = await db.assistants.insert_one(assistant)

        return {"id": str(result.inserted_id), "message": "Assistant created"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_assistants(
    request: Request,  # ADD
    current_user: Dict = Depends(get_current_user_mongo),
    db=Depends(get_database)
):
    """
    List all assistants for current organization.

    Now properly scoped to organization. Requires authentication.  # ADD
    """
    try:
        # ADD organization validation
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # Filter by organization
        org_filter = get_user_organization_filter(current_user, org_id)

        assistants = await db.assistants.find(org_filter).to_list(100)

        return {"assistants": assistants}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing assistants: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🟡 FILE 5: voice_library.py - Middleware Upgrade

**Endpoints**: 5
**Current State**: Uses `organization_id` from `current_user` directly
**Need**: Migrate to middleware pattern for consistency

### Changes Required:

```python
# OLD pattern:
@router.get("/{voice_id}")
async def get_voice(
    voice_id: str,
    current_user: Dict = Depends(get_current_user_mongo),
    db=Depends(get_database)
):
    org_id = current_user.get("organization_id")  # OLD
    voice = await db.voices.find_one({"_id": voice_id})  # No org filter!
    return voice

# NEW pattern:
@router.get("/{voice_id}")
async def get_voice(
    request: Request,  # ADD
    voice_id: str,
    current_user: Dict = Depends(get_current_user_mongo),
    db=Depends(get_database)
):
    """
    Get voice by ID.

    Now properly scoped to organization. Requires authentication.  # ADD
    """
    try:
        # NEW: Use middleware
        org_id = get_organization_context(request)
        if org_id:
            await validate_organization_access(request, current_user, org_id)

        # NEW: Add org filter
        org_filter = get_user_organization_filter(current_user, org_id)
        query = {"_id": voice_id, **org_filter}

        voice = await db.voices.find_one(query)

        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")

        return voice

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🧪 Testing Guide

### Unit Tests

Create `/opt/kasaai/apps/core_backend/tests/test_organization_context.py`:

```python
import pytest
from fastapi import Request, HTTPException
from backend.middleware.organization_context import (
    get_organization_context,
    validate_organization_access,
    get_user_organization_filter
)

class TestOrganizationContext:

    @pytest.mark.asyncio
    async def test_organization_validation_success(self):
        """Test successful organization access validation"""
        # Setup mock request with org_id
        request = MockRequest(headers={"X-Organization-ID": "org-123"})
        user = {"id": "user-1", "email": "test@example.com"}

        # Should not raise exception for valid access
        result = await validate_organization_access(request, user, "org-123")
        assert result == True

    @pytest.mark.asyncio
    async def test_cross_organization_access_denied(self):
        """Test that users cannot access other organizations"""
        request = MockRequest(headers={"X-Organization-ID": "org-999"})
        user = {"id": "user-1", "email": "test@example.com"}

        # Should return False for unauthorized access
        result = await validate_organization_access(request, user, "org-999")
        assert result == False

    def test_organization_filter_regular_user(self):
        """Test organization filter for regular users"""
        user = {"id": "user-1", "email": "test@example.com"}

        filter_result = get_user_organization_filter(user, "org-123")
        assert filter_result == {"organization_id": "org-123"}

    def test_organization_filter_universal_admin(self):
        """Test organization filter for universal admin"""
        user = {"id": "admin-1", "email": "admin@ailabsafrica.com"}

        # Admin should get no filter (can see all)
        filter_result = get_user_organization_filter(user, None)
        assert filter_result == {}
```

### Integration Tests

Create `/opt/kasaai/apps/core_backend/tests/test_wallet_organization_isolation.py`:

```python
import pytest
from httpx import AsyncClient

class TestWalletOrganizationIsolation:

    @pytest.mark.asyncio
    async def test_wallet_balance_organization_scoped(self, async_client: AsyncClient):
        """Test wallet balance is scoped to organization"""

        # User 1 in Org A
        headers_org_a = {
            "Authorization": "Bearer token_user1_orgA",
            "X-Organization-ID": "org-a"
        }

        # User 2 in Org B
        headers_org_b = {
            "Authorization": "Bearer token_user2_orgB",
            "X-Organization-ID": "org-b"
        }

        # Each user should only see their own org's data
        response_a = await async_client.get("/wallet/balance", headers=headers_org_a)
        response_b = await async_client.get("/wallet/balance", headers=headers_org_b)

        assert response_a.status_code == 200
        assert response_b.status_code == 200
        assert response_a.json()["wallet_id"] != response_b.json()["wallet_id"]

    @pytest.mark.asyncio
    async def test_cross_organization_access_denied(self, async_client: AsyncClient):
        """Test user cannot access another organization's wallet"""

        # User from Org A trying to access Org B
        headers = {
            "Authorization": "Bearer token_user1_orgA",
            "X-Organization-ID": "org-b"  # Wrong org!
        }

        response = await async_client.get("/wallet/balance", headers=headers)

        # Should be denied
        assert response.status_code in [403, 404]
```

---

## 📋 Implementation Checklist

### Week 1 - Critical (Financial & Sensitive)
- [ ] **wallet.py** - 16 endpoints
  - [ ] Add imports and Request parameters
  - [ ] Add organization validation to 12 authenticated endpoints
  - [ ] Add organization to 4 webhook metadata
  - [ ] Update WalletService to use organization_id
  - [ ] Test financial data isolation

- [ ] **analytics.py** - 12 endpoints
  - [ ] Add organization filtering to all queries
  - [ ] Secure cost/profit endpoints
  - [ ] Migrate tenant_id references
  - [ ] Test analytics isolation

- [ ] **campaigns.py** - 12 endpoints
  - [ ] Find and replace all tenant_id → organization_id
  - [ ] Add organization validation
  - [ ] Update queries and document creation
  - [ ] Test campaign isolation

### Week 2 - VAPI & Voice
- [ ] **vapi_assistants.py** - 5 endpoints
  - [ ] Add organization validation
  - [ ] Update assistant CRUD
  - [ ] Test assistant isolation

- [ ] **voice_campaigns.py** - 8 endpoints
  - [ ] Migrate tenant_id → organization_id
  - [ ] Add organization context
  - [ ] Test voice campaign isolation

- [ ] **voice_library.py** - 5 endpoints
  - [ ] Migrate to middleware pattern
  - [ ] Add ownership checks
  - [ ] Test voice library access

### Week 3 - Audit & Monitoring
- [ ] **call_logs.py** - 7 endpoints
- [ ] **call_management.py** - 3 endpoints
- [ ] **automation_analytics.py** - 7 endpoints

### Week 4 - Webhooks
- [ ] **integration_webhooks.py** - 9 endpoints

---

## 🚀 Deployment

1. **Run tests locally**:
```bash
pytest tests/test_organization_*.py -v
```

2. **Deploy to dev**:
```bash
git add .
git commit -m "feat(security): Add organization context to [FILE_NAME]"
git push origin main
```

3. **Monitor logs**:
```bash
sudo journalctl -u kasaai-core-backend -f | grep "organization"
```

4. **Verify organization isolation**:
- Test cross-organization access attempts
- Check audit logs
- Verify database queries include organization filters

---

## 📞 Support

**Questions**: Refer to Phase 1 completed files as examples:
- `/opt/kasaai/apps/core_backend/backend/routes/knowledge_base.py`
- `/opt/kasaai/apps/core_backend/backend/routes/automation_configs.py`

**Documentation**:
- Organization Context: `/opt/kasaai/apps/core_backend/backend/middleware/organization_context.py`
- Gap Analysis: `/opt/kasaai/apps/core_backend/ORGANIZATION_CONTEXT_GAP_ANALYSIS.md`

---

**Created**: November 9, 2025
**Status**: Ready for Implementation
**Next**: Begin with wallet.py (Week 1 Priority 1)

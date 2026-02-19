# Organization Context Gap Analysis - Core Backend

**Date**: November 9, 2025
**Status**: Phase 2 Planning
**Previous Work**: Phase 1 completed 56 endpoints (knowledge_base.py, vapi_consolidated.py, premier_health.py)

---

## 📊 Executive Summary

**Total CRUD Endpoints Analyzed**: 140+
**Already Secured (Phase 1)**: 56 endpoints (40%)
**Missing Organization Context**: 84 endpoints (60%)

### Critical Findings:
1. **13 route files** still need organization context implementation
2. **3 route files** use deprecated `tenant_id` (need migration)
3. **4 route files** have NO organization scoping at all
4. **Voice library** endpoints need middleware consistency upgrade

---

## 🔴 PRIORITY 1 - CRITICAL DATA SECURITY GAPS

### 1. **vapi_assistants.py** - VAPI Assistant Management
**Risk Level**: 🔴 CRITICAL
**Total Endpoints**: 5
**Missing Organization Context**: 5 (100%)

**Endpoints needing organization context:**
```
POST   /                  - create_assistant (No org validation)
GET    /                  - list_assistants (No org filtering)
GET    /{assistant_id}    - get_assistant (No ownership check)
PATCH  /{assistant_id}    - update_assistant (No ownership check)
DELETE /{assistant_id}    - delete_assistant (No ownership check)
```

**Security Risk**: Users could potentially access/modify assistants from other organizations.

---

### 2. **campaigns.py** - Campaign Management
**Risk Level**: 🔴 CRITICAL
**Total Endpoints**: 12
**Missing Organization Context**: 12 (100%)
**Uses Deprecated**: `tenant_id` instead of `organization_id`

**Endpoints needing migration:**
```
POST   /                       - create_new_campaign (uses tenant_id)
GET    /                       - get_campaigns (uses tenant_id)
GET    /{campaign_id}          - get_campaign (uses tenant_id check)
POST   /{campaign_id}/start    - start_campaign (uses tenant_id check)
POST   /{campaign_id}/pause    - pause_campaign (uses tenant_id check)
DELETE /{campaign_id}           - delete_campaign (uses tenant_id check)
POST   /{campaign_id}/execute  - execute_campaign (uses tenant_id)
GET    /{campaign_id}/status   - get_campaign_status (uses tenant_id)
GET    /{campaign_id}/results  - get_campaign_results (uses tenant_id)
POST   /n8n/register           - register_n8n_campaign (uses tenant_id)
POST   /n8n/update             - update_n8n_campaign (uses tenant_id)
POST   /n8n/execute            - execute_n8n_campaign (uses tenant_id)
```

**Migration Required**: `tenant_id` → `organization_id` across entire file.

---

### 3. **analytics.py** - Analytics & Metrics
**Risk Level**: 🔴 CRITICAL
**Total Endpoints**: 12
**Missing Organization Context**: 12 (100%)

**Endpoints needing organization context:**
```
GET /overview                        - No org filtering (global data leak)
GET /automations                     - No org filtering
GET /automations/{automation_id}/health - No org check
GET /vapi                            - No org filtering
GET /n8n                             - No org filtering
GET /costs                           - No org filtering (financial data!)
GET /profit-margins                  - No org filtering (financial data!)
GET /services/{service}              - No org filtering
GET /tenants/{tenant_id}             - Uses tenant_id (deprecated)
GET /campaigns                       - No org filtering
GET /integrations                    - No org filtering
GET /dashboard-data                  - No org filtering (aggregated leak)
```

**Security Risk**: Financial data and metrics exposed across organizations.

---

### 4. **call_logs.py** - Call History & Audit
**Risk Level**: 🟠 HIGH
**Total Endpoints**: 7
**Missing Organization Context**: 7 (100%)

**Endpoints needing organization context:**
```
POST   /             - create_call_log (No org context)
GET    /             - get_call_logs (No org filtering - major leak)
GET    /stats        - get_call_stats (No org filtering)
GET    /tool-analysis - get_tool_analysis (No org filtering)
PUT    /{log_id}     - update_call_log (No ownership check)
DELETE /{log_id}     - delete_call_log (No ownership check)
GET    /{log_id}     - get_call_log (No ownership check)
```

**Security Risk**: Call history and PII exposed across organizations.

---

### 5. **voice_campaigns.py** - Voice Campaign Operations
**Risk Level**: 🟠 HIGH
**Total Endpoints**: 8
**Missing Organization Context**: 8 (100%)
**Uses Deprecated**: `tenant_id` instead of `organization_id`

**Endpoints needing migration:**
```
POST /database-connections         - create_db_connection (uses tenant_id)
GET  /database-connections         - list_db_connections (uses tenant_id)
GET  /database-connections/{id}    - get_db_connection (uses tenant_id)
PATCH /database-connections/{id}   - update_db_connection (uses tenant_id)
DELETE /database-connections/{id}  - delete_db_connection (uses tenant_id)
POST /campaigns                    - create_voice_campaign (uses tenant_id)
GET  /campaigns/{id}               - get_voice_campaign (uses tenant_id)
DELETE /campaigns/{id}             - delete_voice_campaign (uses tenant_id)
```

**Migration Required**: `tenant_id` → `organization_id` across entire file.

---

## 🟡 PRIORITY 2 - MODERATE RISK

### 6. **wallet.py** - Financial Operations
**Risk Level**: 🟠 HIGH (Financial)
**Total Endpoints**: 16
**Missing Organization Context**: 16 (100%)

**Endpoints needing organization context:**
```
POST   /transactions              - create_transaction (No org context)
GET    /transactions              - list_transactions (No org filtering!)
GET    /transactions/{id}         - get_transaction (No ownership)
GET    /balance                   - get_balance (No org filtering)
POST   /topup                     - topup_wallet (No org context)
POST   /withdraw                  - withdraw_funds (No org context)
GET    /history                   - transaction_history (No org filtering)
POST   /transfer                  - transfer_funds (No org validation)
GET    /limits                    - get_wallet_limits (No org filtering)
PUT    /limits                    - update_limits (No org validation)
GET    /analytics                 - wallet_analytics (No org filtering)
POST   /payment-methods           - add_payment_method (No org context)
GET    /payment-methods           - list_payment_methods (No org filtering)
DELETE /payment-methods/{id}      - remove_payment_method (No ownership)
POST   /invoices                  - create_invoice (No org context)
GET    /invoices                  - list_invoices (No org filtering)
```

**Security Risk**: Financial data breach - balances, transactions exposed!

---

### 7. **call_management.py** - Call Tracking
**Risk Level**: 🟢 PARTIAL (3/6 secured)
**Total Endpoints**: 6
**Already Secured**: 3 (GET /call-logs, GET /call-logs/{id}, GET /call-analytics)
**Missing Organization Context**: 3

**Endpoints needing organization context:**
```
POST /log-call                      - Accepts org_id but doesn't enforce
POST /supabase-integration          - No org context
POST /integrations/supabase/execute - No org context
```

---

### 8. **automation_analytics.py** - Automation Metrics
**Risk Level**: 🟡 MEDIUM
**Total Endpoints**: 7
**Missing Organization Context**: 7 (100%)

**Endpoints needing organization context:**
```
GET /automations/{id}/metrics       - No org filtering
GET /automations/{id}/performance   - No org filtering
GET /automations/{id}/errors        - No org filtering
GET /automations/{id}/costs         - No org filtering
GET /overview                       - No org filtering
GET /trending                       - No org filtering
GET /compare                        - No org filtering
```

---

### 9. **integration_webhooks.py** - Webhook Handlers
**Risk Level**: 🟡 MEDIUM (Webhooks)
**Total Endpoints**: 9
**Missing Organization Context**: 9 (metadata tracking needed)

**Webhook endpoints (need org in metadata):**
```
POST /calendly                  - Webhook (org in metadata needed)
POST /freshdesk                 - Webhook (org in metadata needed)
POST /n8n                       - Webhook (org in metadata needed)
POST /zapier                    - Webhook (org in metadata needed)
POST /stripe                    - Webhook (org in metadata needed)
POST /twilio                    - Webhook (org in metadata needed)
POST /vonage                    - Webhook (org in metadata needed)
POST /hubspot                   - Webhook (org in metadata needed)
POST /salesforce                - Webhook (org in metadata needed)
```

**Note**: These are webhooks from external services, organization should be tracked in metadata/payload.

---

### 10. **voice_library.py** - Voice Library Management
**Risk Level**: 🟢 LOW (Has org_id but needs middleware upgrade)
**Total Endpoints**: 5
**Current Implementation**: Uses `organization_id` from `current_user` directly
**Needs**: Migration to organization context middleware for consistency

**Endpoints with inconsistent pattern:**
```
POST   /              - create_voice (uses current_user org_id)
GET    /{voice_id}    - get_voice (NO org filter - access issue)
GET    /              - list_voices (uses current_user org_id)
PATCH  /{voice_id}    - update_voice (NO org filter)
DELETE /{voice_id}    - delete_voice (NO org filter)
```

**Recommendation**: Migrate to use `get_organization_context()` middleware for consistency with other routes.

---

## ✅ ALREADY SECURED (Phase 1)

### Successfully Implemented:
1. **automation_configs.py** - 19 endpoints ✅ (uses get_organization_context)
2. **organizations.py** - 11 endpoints ✅ (proper access validation)
3. **admin.py** - 4 endpoints ✅ (admin-only access)
4. **knowledge_base.py** - 31 endpoints ✅ (Phase 1)
5. **vapi_consolidated.py** - 10 endpoints ✅ (Phase 1)
6. **premier_health.py** - 15 endpoints ✅ (Phase 1)

---

## 📋 PHASE 2 IMPLEMENTATION PLAN

### Week 1 - Critical Security Fixes
**Priority: Financial & Sensitive Data**

1. **wallet.py** (16 endpoints)
   - Add organization context to all financial operations
   - Implement strict ownership validation
   - Add audit logging for all transactions

2. **analytics.py** (12 endpoints)
   - Add organization filtering to all analytics queries
   - Implement aggregation limits per organization
   - Secure cost/profit margin endpoints

3. **campaigns.py** (12 endpoints)
   - Migrate `tenant_id` → `organization_id`
   - Add organization context validation
   - Update all database queries

### Week 2 - VAPI & Voice Features

4. **vapi_assistants.py** (5 endpoints)
   - Add organization context to assistant CRUD
   - Implement ownership checks
   - Secure assistant access

5. **voice_campaigns.py** (8 endpoints)
   - Migrate `tenant_id` → `organization_id`
   - Add organization context
   - Secure database connections

6. **voice_library.py** (5 endpoints)
   - Migrate to organization context middleware
   - Add ownership checks to GET/PATCH/DELETE
   - Ensure consistency with other routes

### Week 3 - Audit & Monitoring

7. **call_logs.py** (7 endpoints)
   - Add organization filtering to all queries
   - Implement strict ownership validation
   - Add audit trail

8. **call_management.py** (3 remaining endpoints)
   - Complete organization context
   - Enforce organization_id in POST /log-call

9. **automation_analytics.py** (7 endpoints)
   - Add organization filtering
   - Secure metrics access

### Week 4 - Webhooks & Integration

10. **integration_webhooks.py** (9 endpoints)
    - Add organization tracking to webhook metadata
    - Implement webhook signature verification
    - Log organization context in all webhook calls

---

## 🔧 Implementation Pattern

### Standard Pattern (from Phase 1):
```python
from ..security.organization_scope import (
    get_organization_context,
    validate_organization_access,
    get_user_organization_filter
)

@router.get("/endpoint")
async def endpoint_handler(
    current_user: dict = Depends(get_current_user_mongo),
    request: Request = None
):
    """
    Endpoint description.

    Now properly scoped to organization. Requires authentication.
    """
    # Get and validate organization context
    org_id = get_organization_context(request)
    if org_id:
        await validate_organization_access(org_id, current_user)

    # Build organization filter for queries
    org_filter = get_user_organization_filter(current_user)

    # Query with organization filtering
    results = await collection.find(org_filter).to_list(length=100)

    return {"data": results}
```

### Migration Pattern (tenant_id → organization_id):
```python
# OLD (campaigns.py, voice_campaigns.py):
tenant_id = current_user.get("tenant_id", "default")
filter = {"tenant_id": tenant_id}

# NEW:
from ..security.organization_scope import get_organization_context, validate_organization_access

org_id = get_organization_context(request)
if org_id:
    await validate_organization_access(org_id, current_user)

org_filter = get_user_organization_filter(current_user)
# Returns: {"organization_id": org_id} or {} for universal_admin
```

---

## 📊 Statistics Summary

| Category | Files | Endpoints | Status |
|----------|-------|-----------|--------|
| **Fully Secured** | 6 | 56 | ✅ Phase 1 Complete |
| **Needs Organization Context** | 8 | 74 | 🔴 Critical |
| **Needs tenant_id Migration** | 3 | 32 | 🟠 High Priority |
| **Needs Middleware Upgrade** | 1 | 5 | 🟡 Medium |
| **Webhook Tracking Needed** | 1 | 9 | 🟡 Medium |
| **TOTAL** | **19** | **176** | **68% Remaining** |

---

## 🎯 Success Metrics for Phase 2

### Security Goals:
- ✅ 100% of user data CRUD endpoints have organization context
- ✅ 0 cross-organization data leaks in testing
- ✅ All financial endpoints secured with strict validation
- ✅ Complete migration from tenant_id to organization_id

### Code Quality:
- ✅ Consistent security pattern across all routes
- ✅ 80%+ test coverage for organization isolation
- ✅ Comprehensive audit logging
- ✅ Performance benchmarks maintained

### Documentation:
- ✅ All endpoints documented with org requirements
- ✅ Migration guide for tenant_id → organization_id
- ✅ Security testing guide
- ✅ Developer onboarding updated

---

## 📞 Next Actions

1. **Review & Approve** this gap analysis
2. **Prioritize** specific files for Phase 2 implementation
3. **Create** detailed task tickets for each route file
4. **Assign** developers to specific files
5. **Begin** Week 1 implementation (wallet.py, analytics.py, campaigns.py)

---

**Generated**: November 9, 2025
**By**: Claude Code
**Phase**: 2 - Organization Scope Gap Analysis
**Status**: 🔍 ANALYSIS COMPLETE - AWAITING IMPLEMENTATION

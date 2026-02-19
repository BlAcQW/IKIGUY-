# Billing Automation Workflow

## Overview

This document explains how billing records are created automatically for automation calls, how costs are tracked, and how users can view their billing information.

## Architecture

### Collections

1. **`automation_calls`** - Stores individual call details synced from VAPI
   - Fields: call_id, automation_id, vapi_cost, duration, transcript, status
   - Created by: `automation_analytics_service.sync_automation_calls()`

2. **`billing_records`** - Stores billing entries for organization invoicing
   - Fields: organization_id, service_type, amount, metadata, billing_period, status
   - Created by: `billing_service.create_billing_record_from_call()`

3. **`automation_configs`** - Automation configuration with organization link
   - Fields: automation_id, organization_id, vapi_agent.assistant_id
   - Used to: Link calls to organizations for billing

### Services

**`BillingService`** (in `@apps/shared/services/billing_service.py`)
- Manages wallet transactions, usage logs, AND billing records
- Can be used by all apps (StudyFlow, ChurchFlow, EventFlow, InkWave, Core)
- Prevents duplicate billing with call_id checks

## Automated Billing Workflow

### Current Manual Process (Used for Premier Health)

```
1. User imports automation from VAPI
   ↓
2. Automation calls happen (tracked in VAPI)
   ↓
3. Admin manually runs: POST /api/automation-analytics/{config_id}/sync
   - Fetches call data from VAPI
   - Stores in automation_calls collection
   ↓
4. Admin manually runs: POST /api/automation-analytics/{config_id}/create-billing
   - Creates billing_records from automation_calls
   - Links to organization via automation_config.organization_id
   ↓
5. Billing appears in:
   - /api/internal/usage endpoint (for billing page)
   - Individual automation analytics
```

### Recommended Automatic Workflow

**OPTION A: Scheduled Sync + Billing (Recommended)**

```python
# Add to cron or scheduled tasks
# File: apps/core_backend/backend/tasks/billing_sync.py

async def sync_and_bill_all_automations():
    """
    Daily task to sync calls and create billing records.

    Run at: 00:00 UTC daily
    """
    db = get_database()
    analytics_service = await get_analytics_service(db)
    billing_service = get_billing_service(db)

    # Get all active automations
    configs = await db.automation_configs.find({
        "status": "active",
        "organization_id": {"$exists": True}
    }).to_list(length=None)

    for config in configs:
        config_id = str(config["_id"])

        # Step 1: Sync calls from VAPI
        sync_result = await analytics_service.sync_automation_calls(config_id)

        if sync_result.get("success"):
            # Step 2: Create billing records for new calls
            billing_result = await billing_service.create_billing_records_for_automation(config_id)

            logger.info(f"Automation {config_id}: "
                       f"{billing_result.get('billing_records_created')} billing records created, "
                       f"${billing_result.get('total_amount', 0):.4f} total")
```

**Schedule Setup:**

```python
# In main.py or startup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    sync_and_bill_all_automations,
    'cron',
    hour=0,  # Run at midnight UTC
    id='billing_sync'
)
scheduler.start()
```

**OPTION B: Webhook-Triggered Billing (Real-time)**

```python
# Add webhook handler for VAPI call completion
# File: apps/core_backend/backend/routes/webhooks.py

@router.post("/vapi/call-ended")
async def handle_vapi_call_ended(payload: Dict[str, Any]):
    """
    Webhook fired when a VAPI call ends.

    Immediately creates billing record.
    """
    call = payload.get("call", {})
    assistant_id = call.get("assistantId")

    # Find automation by assistant_id
    config = await db.automation_configs.find_one({
        "vapi_agent.assistant_id": assistant_id
    })

    if not config:
        return {"error": "Automation not found"}

    organization_id = config.get("organization_id")
    if not organization_id:
        return {"error": "No organization linked"}

    # Create call record
    call_doc = {
        "automation_id": str(config["_id"]),
        "call_id": call.get("id"),
        "vapi_cost": call.get("cost", 0),
        "duration": call.get("duration"),
        "status": call.get("status"),
        # ... other fields
    }

    await db.automation_calls.insert_one(call_doc)

    # Immediately create billing record
    billing_service = get_billing_service(db)
    billing_id = await billing_service.create_billing_record_from_call(
        call_doc,
        organization_id,
        config.get("automation_name")
    )

    return {
        "success": True,
        "billing_id": billing_id,
        "amount": call.get("cost", 0)
    }
```

## Viewing Billing Data

### Organization-Level Billing Summary

**Endpoint:** `GET /api/internal/usage?tenant_id={organization_id}`

```json
{
  "tenant_id": "68cc350e27636f4707e1f1c4",
  "automation_cost": 0.3187,
  "billing_summary": {
    "organization_id": "68cc350e27636f4707e1f1c4",
    "totals": {
      "pending": 0.3187,
      "billed": 0.0,
      "paid": 0.0,
      "total": 0.3187
    },
    "counts": {
      "pending": 13,
      "billed": 0,
      "paid": 0,
      "total": 13
    }
  }
}
```

**Frontend:** https://kasaai.ailabsafrica.com/billing

### Individual Automation Analytics

**Endpoint:** `GET /api/automation-analytics/{config_id}?time_range=30d`

```json
{
  "success": true,
  "data": {
    "automation_name": "Premier Health Navigator",
    "metrics": {
      "total_calls": 15,
      "total_cost": 0.3187,
      "avg_cost_per_call": 0.0212
    },
    "recent_calls": [
      {
        "call_id": "019a0139-c19d-799d-bd57-cd3d5f7b1d8a",
        "cost": 0.0825,
        "duration": 120,
        "transcript": "...",
        "customer_number": "+233..."
      }
    ]
  }
}
```

### Call Details & Transcripts

**Endpoint:** `GET /api/automation-analytics/{config_id}/calls?page=1&limit=20`

```json
{
  "success": true,
  "data": {
    "calls": [
      {
        "id": "67890",
        "call_id": "019a0139-c19d-799d-bd57-cd3d5f7b1d8a",
        "vapi_cost": 0.0825,
        "status": "ended",
        "transcript": "Full conversation transcript...",
        "started_at": "2025-10-20T10:45:53Z",
        "ended_at": "2025-10-20T10:47:53Z",
        "customer_number": "+233244123456"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 15,
      "pages": 1
    }
  }
}
```

## Data Flow Summary

```
┌─────────────────┐
│  VAPI Platform  │
│  (Calls happen) │
└────────┬────────┘
         │
         │ 1. Sync daily/webhook
         ↓
┌─────────────────────┐
│ automation_calls    │ ← Stores call details with costs
└──────────┬──────────┘
           │
           │ 2. Create billing records
           ↓
┌─────────────────────┐
│ billing_records     │ ← Linked to organization
└──────────┬──────────┘
           │
           │ 3. Aggregate for display
           ↓
┌─────────────────────────────────────┐
│  /api/internal/usage                │
│  (Billing page shows VAPI costs)    │
└─────────────────────────────────────┘
```

## Multi-Automation Support

**Each organization can have multiple automations:**

```
Organization: Premier Health (68cc350e27636f4707e1f1c4)
  ├── Automation 1: Premier Health Navigator
  │   ├── 15 calls ($0.3187)
  │   └── Billing: 13 records (2 zero-cost skipped)
  │
  ├── Automation 2: Appointment Reminder
  │   ├── 42 calls ($0.8901)
  │   └── Billing: 42 records
  │
  └── Total: $1.2088 (55 records)
```

**Billing page shows:**
- `automation_cost`: $1.2088 (sum of all automations)
- `billing_summary.totals.total`: $1.2088
- `billing_summary.counts.total`: 55 records

## Billing Record Status Flow

```
Status: pending
  ↓ (at end of month, admin marks as billed)
Status: billed
  ↓ (after customer payment processed)
Status: paid
```

This allows tracking of:
- Pending charges (current month)
- Billed but unpaid invoices
- Paid historical records

## Implementation Checklist

- [x] Create shared BillingService
- [x] Add billing_records methods
- [x] Update /api/internal/usage endpoint
- [x] Billing page displays costs
- [x] Add scheduled task for daily sync (COMPLETED 2025-10-30)
- [x] Add admin endpoint to manually trigger sync (POST /api/admin/billing/sync-now)
- [x] Add admin endpoint to check sync status (GET /api/admin/billing/sync-status)
- [ ] Set up VAPI webhooks for real-time billing (Optional - scheduled sync is sufficient)
- [ ] Create admin interface to mark billing as "billed"/"paid"
- [ ] Add monthly invoice generation
- [ ] Email billing summaries to organizations

## Notes

- **Idempotency:** `create_billing_record_from_call()` checks for existing call_id to prevent duplicates
- **Multi-app:** Billing service in @apps/shared/ can be used by all apps
- **Zero-cost calls:** Calls with $0.00 cost are not billed
- **Organization required:** Automations must have `organization_id` to generate billing

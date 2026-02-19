# Cost Tracking Integration Guide

## Overview

This document explains how internal cost tracking has been integrated into the KasaAI platform to enable profit margin analysis. The system tracks actual costs paid to providers (VAPI, Twilio, OpenAI, etc.) vs. what we charge customers.

**Status**: ✅ IMPLEMENTED (2025-10-30)

## Architecture

```
User Action (Voice Call, RAG Query, etc.)
    ↓
UsageCalculator.calculate_*() - Calculates customer charge
    ↓
InternalCostTracker.record_*() - Records actual provider cost
    ↓
Cost Record Queued in Memory
    ↓
UsageCalculator.flush_cost_tracker() - Saves to MongoDB
    ↓
cost_records_internal collection
    ↓
Admin Analytics Dashboard (profit margins, provider comparison)
```

## Components

### 1. InternalCostTracker (`@apps/shared/integration/internal_cost_tracker.py`)

**Purpose**: Track actual costs paid to providers

**Key Methods**:
- `record_vapi_call_cost()` - Track VAPI call costs
- `record_twilio_call_cost()` - Track Twilio telephony costs
- `record_ai_token_cost()` - Track AI/LLM token costs
- `record_payment_processing_cost()` - Track payment gateway fees
- `flush_pending_saves()` - Save queued costs to database

**Features**:
- Automatic profit margin calculation (revenue - costs)
- USD to GHS currency conversion
- Metadata tracking for analysis
- Graceful degradation if database unavailable

### 2. CostRecordService (`@apps/core_backend/backend/services/cost_record_service.py`)

**Purpose**: Persist cost records to MongoDB

**Methods**:
- `save_cost_record()` - Save ActualCost to database
- `get_cost_summary()` - Aggregate costs by time period
- `get_cost_breakdown_by_provider()` - Analyze costs per provider

**Database**: `cost_records_internal` collection

### 3. UsageCalculator (`@apps/shared/integration/usage_calculator.py`)

**Purpose**: Calculate customer charges and track costs

**Integration**:
- Initializes `InternalCostTracker` with database service
- Automatically calls `record_*()` methods when calculating costs
- Provides `flush_cost_tracker()` method to save to database

**Example**:
```python
from apps.shared.integration.usage_calculator import UsageCalculator
from apps.shared.integration.cost_tracker_factory import create_cost_tracker_with_db

# Initialize with cost tracking
calculator = UsageCalculator(
    tier=PricingTier.BASIC,
    tenant_id="org_123",
    enable_cost_tracking=True
)

# Calculate voice call cost (automatically tracks internal cost)
metric = calculator.calculate_voice_call_cost(
    duration_minutes=5.5,
    platform="vapi",
    call_id="call_123"
)

# Save cost records to database
saved_count = await calculator.flush_cost_tracker()
print(f"Saved {saved_count} cost records")
```

## Provider Costs (Accurate as of 2025-10-27)

### Voice Providers (per minute, USD)
- **VAPI**: $0.05/min (platform fee only) or $0.20/min (full stack)
- **Twilio**:
  - Inbound: $0.1355/min (Ghana)
  - Outbound: $0.4070/min (Ghana mobile) ⚠️ LOSING MONEY
- **Vonage**: $0.014/min

### AI Providers (per 1K tokens, USD)
- **OpenAI GPT-4o-mini**:
  - Input: $0.00015/1K tokens
  - Output: $0.0006/1K tokens
- **Anthropic Claude**:
  - Input: $0.003/1K tokens
  - Output: $0.015/1K tokens

### TTS/STT Providers
- **OpenAI TTS**: $0.000015/character
- **ElevenLabs TTS**: $0.00018/character
- **OpenAI Whisper**: $0.006/minute
- **Deepgram STT**: $0.0043/minute

### Currency Conversion
- **1 USD = 10.785 GHS** (as of 2025-10-27)

## Usage in Code

### Option A: Automatic Cost Tracking (Recommended)

Cost tracking happens automatically when using `UsageCalculator`:

```python
from apps.shared.integration.usage_calculator import UsageCalculator, PricingTier

# Initialize calculator with tenant ID
calculator = UsageCalculator(
    tier=PricingTier.BASIC,
    tenant_id=organization_id,
    enable_cost_tracking=True  # Default
)

# Calculate costs (internal costs tracked automatically)
voice_metric = calculator.calculate_voice_call_cost(
    duration_minutes=3.5,
    platform="vapi",
    call_id="call_xyz"
)

rag_metric = calculator.calculate_rag_cost(
    input_tokens=500,
    output_tokens=200,
    provider="openai"
)

# Flush cost records to database
saved_count = await calculator.flush_cost_tracker()
print(f"✅ Saved {saved_count} internal cost records for profit analysis")
```

### Option B: Manual Cost Tracking

For advanced use cases:

```python
from apps.shared.integration.internal_cost_tracker import InternalCostTracker, Provider
from apps.shared.integration.cost_tracker_factory import create_cost_tracker_with_db
from decimal import Decimal

# Create tracker with database persistence
tracker = create_cost_tracker_with_db(
    mongodb_client=get_database().client,
    database_name="kasaai_core"
)

# Record VAPI call cost
cost = tracker.record_vapi_call_cost(
    duration_minutes=5.5,
    customer_charge=Decimal('13.75'),  # GHS
    tenant_id="org_123",
    call_id="call_xyz",
    use_full_stack_cost=True
)

print(f"Profit margin: {cost.profit_margin} GHS")

# Save to database
saved_count = await tracker.flush_pending_saves()
```

## Integration Points

### 1. Voice Call Billing

**File**: `@apps/shared/integration/usage_calculator.py:390-463`

```python
def calculate_voice_call_cost(self, duration_minutes, direction, platform, call_id):
    # ... calculate customer charge ...

    # Track internal costs (lines 434-461)
    if self.cost_tracking_enabled and self.tenant_id:
        customer_charge = metric.total_cost

        if platform == "vapi":
            self.cost_tracker.record_vapi_call_cost(
                duration_minutes=duration_minutes,
                customer_charge=customer_charge,
                tenant_id=self.tenant_id,
                call_id=call_id
            )
```

**Status**: ✅ Integrated and queuing costs

### 2. RAG Query Billing

**File**: `@apps/shared/integration/usage_calculator.py:342-388`

**Status**: ⚠️ Customer charge calculated, but AI token cost tracking not yet integrated

**TODO**: Add `record_ai_token_cost()` call after RAG queries

### 3. TTS/STT Operations

**Status**: ⚠️ Customer charges calculated, provider costs not yet tracked

**TODO**: Add TTS/STT cost tracking methods to InternalCostTracker

## Database Schema

### cost_records_internal Collection

```javascript
{
  "_id": ObjectId,
  "timestamp": ISODate,

  // Provider info
  "provider": String, // "vapi", "twilio", "openai", etc.
  "cost_type": String, // "voice_call", "ai_tokens", "tts", "stt"

  // Cost details
  "quantity": Number,
  "unit": String, // "minutes", "tokens", "characters"
  "unit_cost": Number, // USD per unit
  "total_cost": Number, // GHS
  "total_cost_ghs": Number, // GHS (redundant for compatibility)
  "currency": String, // "GHS"

  // Customer charge (for profit calculation)
  "customer_charge": Number, // GHS
  "profit_margin": Number, // customer_charge - total_cost (GHS)
  "profit_margin_percentage": Number, // %

  // Links
  "tenant_id": String,
  "user_id": String,
  "call_id": String,
  "transaction_id": String,

  // Metadata
  "metadata": Object,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**Indexes** (recommended):
- `tenant_id` (1)
- `provider` (1)
- `cost_type` (1)
- `timestamp` (-1)
- `(tenant_id, timestamp)` (compound)

## Admin Endpoints

### 1. Provider Costs (Static)
```
GET /api/admin/cost-analytics/provider-costs
```

Returns actual costs we pay to providers.

### 2. Provider Comparison
```
GET /api/admin/cost-analytics/provider-costs/comparison
```

Compare costs across providers for the same service.

### 3. Profit Margins (Future)
```
GET /api/analytics/profit-margins?start_date=2025-10-01&end_date=2025-10-30
```

**Status**: ⚠️ Endpoint exists but returns placeholder data

**Requires**: Cost records in database (now enabled)

## Testing

### 1. Unit Test Cost Tracking

```python
import pytest
from apps.shared.integration.usage_calculator import UsageCalculator, PricingTier
from decimal import Decimal

@pytest.mark.asyncio
async def test_cost_tracking_integration():
    """Test that cost tracking works end-to-end."""
    calculator = UsageCalculator(
        tier=PricingTier.BASIC,
        tenant_id="test_org",
        enable_cost_tracking=True
    )

    # Calculate voice call
    metric = calculator.calculate_voice_call_cost(
        duration_minutes=5.0,
        platform="vapi",
        call_id="test_call_123"
    )

    # Verify customer charge
    assert metric.total_cost == Decimal('12.50')  # 5 min * 2.50 GHS/min

    # Verify cost record created
    assert len(calculator.cost_tracker.cost_records) == 1
    cost = calculator.cost_tracker.cost_records[0]

    # Verify profit calculation
    assert cost.customer_charge == Decimal('12.50')
    assert cost.total_cost < cost.customer_charge  # We're profitable
    assert cost.profit_margin > 0
```

### 2. Integration Test with Database

```python
@pytest.mark.asyncio
async def test_cost_tracking_saves_to_database(mongodb_client):
    """Test that cost records are saved to MongoDB."""
    from apps.shared.integration.cost_tracker_factory import create_cost_tracker_with_db
    from apps.core_backend.backend.services.cost_record_service import CostRecordService

    # Create tracker with database
    tracker = create_cost_tracker_with_db(
        mongodb_client=mongodb_client,
        database_name="kasaai_core_test"
    )

    # Record cost
    cost = tracker.record_vapi_call_cost(
        duration_minutes=3.0,
        customer_charge=Decimal('7.50'),
        tenant_id="test_org",
        call_id="test_call_456"
    )

    # Flush to database
    saved_count = await tracker.flush_pending_saves()
    assert saved_count == 1

    # Verify in database
    service = CostRecordService(mongodb_client, "kasaai_core_test")
    summary = await service.get_cost_summary(tenant_id="test_org")

    assert summary["total_costs"] > 0
    assert summary["total_revenue"] == 7.50
    assert summary["profit"] > 0
```

## Profit Margin Calculations

### Example 1: VAPI Call

```
Duration: 5 minutes
Platform: VAPI (full stack)

Customer Charge:
  5 min × 2.50 GHS/min = 12.50 GHS

Provider Cost:
  5 min × $0.20/min = $1.00 USD
  $1.00 × 10.785 = 10.785 GHS

Profit Margin:
  12.50 - 10.785 = 1.715 GHS (13.7% margin)
```

### Example 2: Twilio Outbound ⚠️ LOSING MONEY

```
Duration: 5 minutes
Platform: Twilio (Ghana mobile outbound)

Customer Charge:
  5 min × 2.50 GHS/min = 12.50 GHS

Provider Cost:
  5 min × $0.4070/min = $2.035 USD
  $2.035 × 10.785 = 21.95 GHS

Profit Margin:
  12.50 - 21.95 = -9.45 GHS (-75.6% margin) ❌ LOSS
```

**Recommendation**: Increase Twilio outbound pricing to at least 5.00 GHS/min or switch to cheaper provider.

## Monitoring & Alerts

### 1. Low Profit Margin Alert

Automatically check for services with profit margins below 10%:

```python
from apps.shared.integration.scheduled_alert_checker import check_profit_margins

# This runs automatically via APScheduler
# See: backend/services/scheduled_alert_checker.py
```

### 2. Cost Tracking Health Check

Verify cost records are being created:

```bash
# Check recent cost records
mongo kasaai_core --eval "
  db.cost_records_internal.find().sort({created_at: -1}).limit(10)
"

# Check profit margins
mongo kasaai_core --eval "
  db.cost_records_internal.aggregate([
    {$match: {profit_margin: {$exists: true}}},
    {$group: {
      _id: '$provider',
      avg_margin: {$avg: '$profit_margin_percentage'},
      total_revenue: {$sum: '$customer_charge'},
      total_costs: {$sum: '$total_cost'}
    }}
  ])
"
```

## Known Issues & Limitations

1. **RAG Query Cost Tracking**: Not yet integrated for AI token costs
2. **TTS/STT Cost Tracking**: Provider costs not tracked (only customer charges)
3. **Manual Flushing Required**: Cost records must be explicitly flushed with `await calculator.flush_cost_tracker()`
4. **Sync Wrapper Needed**: Current implementation requires async, but some code is synchronous

## Future Enhancements

1. **Automatic Flushing**: Add background task to periodically flush pending costs
2. **Real-time Profit Alerts**: WebSocket notifications for negative margins
3. **Provider Cost Updates**: API to dynamically update provider costs
4. **Cost Forecasting**: Predict monthly costs based on usage trends
5. **Multi-currency Support**: Track costs in multiple currencies
6. **Cost Allocation**: Split costs across multiple organizations for shared services

## References

- Billing Automation Workflow: `/opt/kasaai/apps/core_backend/BILLING_AUTOMATION_WORKFLOW.md`
- Usage Calculator: `/opt/kasaai/apps/shared/integration/usage_calculator.py`
- Internal Cost Tracker: `/opt/kasaai/apps/shared/integration/internal_cost_tracker.py`
- Cost Record Service: `/opt/kasaai/apps/core_backend/backend/services/cost_record_service.py`
- Admin Cost Analytics: `/opt/kasaai/apps/core_backend/backend/routes/cost_analytics.py`

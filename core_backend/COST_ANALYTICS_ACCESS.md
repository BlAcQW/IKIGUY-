# Cost Analytics Access Guide

**INTERNAL/ADMIN ONLY** - How to View Cost Analytics

## Overview

The cost analytics system tracks actual costs we pay to providers (VAPI, Twilio, OpenAI, etc.) vs. what we charge customers. This allows us to:
- Monitor profit margins per service
- Identify services where we're losing money
- Make data-driven pricing decisions
- Compare provider costs

## Important Pricing Insights (Verified 2025-10-27)

### ✅ Profitable Services
- **VAPI Base Only**: 78% profit margin (2.70 GHS cost vs 12.50 GHS charge for 5-min call)
- **Twilio Inbound (Ghana)**: 41% profit margin (1.46 GHS/min cost)
- **Vonage**: Very cheap at $0.014/min (0.15 GHS/min)

### ⚠️ Low Margin Services
- **VAPI Full Stack**: 13-14% profit margin (10.79 GHS cost vs 12.50 GHS charge for 5-min call)

### ❌ LOSING MONEY
- **Twilio Outbound Ghana**: **LOSING MONEY!**
  - Cost: $0.4070/min = 4.39 GHS/min
  - Customer charge: 2.50 GHS/min
  - Loss: -1.89 GHS/min (75% loss!)
  - **ACTION REQUIRED**: Use Vonage instead (29x cheaper)

## Accessing Cost Analytics

### 1. API Endpoints (Admin Only)

Base URL: `https://api.ailabsafrica.com/api/admin/cost-analytics/`

#### Authentication Required
All endpoints require admin authentication. Admin users:
- ailabsafrica@gmail.com
- admin@ailabsafrica.com
- support@ailabsafrica.com
- alfred.anyan@gmail.com

#### Available Endpoints

**1. View Provider Costs** (GET /provider-costs)
```bash
curl -X GET "https://api.ailabsafrica.com/api/admin/cost-analytics/provider-costs" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

Response shows actual costs we pay:
```json
{
  "provider": "multiple",
  "currency": "USD",
  "costs": {
    "currency_conversion_rate": 10.785,
    "vapi_base_cost_per_minute": 0.05,
    "vapi_full_stack_cost_per_minute": 0.20,
    "twilio_voice_inbound_cost_per_minute": 0.1355,
    "twilio_voice_outbound_cost_per_minute": 0.4070,
    "vonage_voice_cost_per_minute": 0.014,
    "openai_gpt4o_mini_input_cost": 0.00015,
    "openai_gpt4o_mini_output_cost": 0.0006,
    "stripe_percentage": 0.029,
    "stripe_fixed": 0.30,
    "paystack_percentage": 0.015,
    "mpesa_percentage": 0.01
  }
}
```

**2. Compare Provider Costs** (GET /provider-costs/comparison)
```bash
curl -X GET "https://api.ailabsafrica.com/api/admin/cost-analytics/provider-costs/comparison" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN"
```

Response shows profit/loss for 10-min call:
```json
{
  "scenario": "10-minute voice call",
  "customer_charge_ghs": 25.0,
  "providers": {
    "vapi_base": {
      "cost_usd": 0.5,
      "cost_ghs": 5.39,
      "profit_ghs": 19.61,
      "margin_percent": 78.44,
      "includes": "VAPI platform fee only"
    },
    "vapi_full_stack": {
      "cost_usd": 2.0,
      "cost_ghs": 21.57,
      "profit_ghs": 3.43,
      "margin_percent": 13.72,
      "includes": "VAPI + transport + TTS + STT"
    },
    "twilio_inbound": {
      "cost_usd": 1.355,
      "cost_ghs": 14.61,
      "profit_ghs": 10.39,
      "margin_percent": 41.56,
      "includes": "Twilio inbound calls (Ghana)"
    },
    "twilio_outbound": {
      "cost_usd": 4.07,
      "cost_ghs": 43.89,
      "profit_ghs": -18.89,
      "margin_percent": -75.56,
      "includes": "Twilio outbound mobile (Ghana)",
      "warning": "⚠️ LOSING MONEY!"
    },
    "vonage": {
      "cost_usd": 0.14,
      "cost_ghs": 1.51,
      "profit_ghs": 23.49,
      "margin_percent": 93.96,
      "includes": "Vonage voice"
    }
  },
  "recommendations": [
    "✅ Use VAPI base + Vonage for maximum profit (92% margin)",
    "✅ VAPI full stack is profitable but low margin (13%)",
    "❌ NEVER use Twilio outbound in Ghana (we lose money!)",
    "✅ Twilio inbound is acceptable (41% margin)"
  ]
}
```

**3. Health Check** (GET /health)
```bash
curl -X GET "https://api.ailabsafrica.com/api/admin/cost-analytics/health"
```

No auth required. Shows system status.

### 2. Using cURL (Quick Test)

```bash
# Set your auth token
export AUTH_TOKEN="your_token_here"

# View provider costs
curl "https://api.ailabsafrica.com/api/admin/cost-analytics/provider-costs" \
  -H "Authorization: Bearer $AUTH_TOKEN" | jq

# Compare providers
curl "https://api.ailabsafrica.com/api/admin/cost-analytics/provider-costs/comparison" \
  -H "Authorization: Bearer $AUTH_TOKEN" | jq
```

### 3. Using Python

```python
import requests

# Your auth token
headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
}

# Get provider costs
response = requests.get(
    "https://api.ailabsafrica.com/api/admin/cost-analytics/provider-costs",
    headers=headers
)
costs = response.json()
print(f"VAPI full stack: ${costs['costs']['vapi_full_stack_cost_per_minute']}/min")
print(f"Twilio outbound: ${costs['costs']['twilio_voice_outbound_cost_per_minute']}/min")

# Get comparison
response = requests.get(
    "https://api.ailabsafrica.com/api/admin/cost-analytics/provider-costs/comparison",
    headers=headers
)
comparison = response.json()

for provider, data in comparison['providers'].items():
    print(f"\n{provider}:")
    print(f"  Cost: {data['cost_ghs']:.2f} GHS")
    print(f"  Profit: {data['profit_ghs']:.2f} GHS")
    print(f"  Margin: {data['margin_percent']:.1f}%")
    if 'warning' in data:
        print(f"  ⚠️  {data['warning']}")
```

### 4. Using Postman

1. **Import Collection**:
   - Base URL: `https://api.ailabsafrica.com`
   - Add Authorization header with Bearer token

2. **Create Requests**:
   - GET `/api/admin/cost-analytics/provider-costs`
   - GET `/api/admin/cost-analytics/provider-costs/comparison`
   - GET `/api/admin/cost-analytics/health`

## Critical Business Insights

### 1. Twilio Outbound is Losing Money

**Problem**: Twilio charges $0.4070/min for outbound calls in Ghana, but we charge customers only 2.50 GHS/min ($0.23/min).

**Impact**:
- 10-min call: We lose 18.89 GHS per call
- 100 calls/day: We lose 1,889 GHS/day
- Monthly loss: ~56,670 GHS ($5,254/month)

**Solution**:
- Use Vonage ($0.014/min) instead of Twilio for outbound
- Savings: $0.407 - $0.014 = $0.393/min (29x cheaper)
- Or increase pricing for outbound calls to at least 5.00 GHS/min

### 2. VAPI Full Stack has Low Margins

**Current**: 13-14% margin (10.79 GHS cost vs 12.50 GHS charge for 5-min call)

**Options**:
1. **Use VAPI base + cheaper providers**:
   - VAPI base: $0.05/min
   - Vonage transport: $0.014/min
   - OpenAI Whisper STT: $0.006/min
   - OpenAI TTS: $0.011/min
   - Total: $0.081/min = 0.87 GHS/min
   - Margin: 65% instead of 13%!

2. **Increase pricing**:
   - Current: 2.50 GHS/min
   - Recommended: 3.00 GHS/min (38% margin)

### 3. Best Provider Combinations

**For Maximum Profit** (94% margin):
- VAPI base ($0.05/min) = 0.54 GHS/min
- Vonage transport ($0.014/min) = 0.15 GHS/min
- OpenAI Whisper STT ($0.006/min) = 0.06 GHS/min
- OpenAI TTS ($0.011/min) = 0.12 GHS/min
- **Total cost**: 0.87 GHS/min
- **Customer charge**: 2.50 GHS/min (current)
- **Profit**: 1.63 GHS/min (65% margin)
- **Savings vs VAPI full stack**: 9.92 GHS per 5-min call

**For Easiest Integration** (13% margin):
- VAPI full stack ($0.20/min) = 2.16 GHS/min
- Customer charge: 2.50 GHS/min
- Profit: 0.34 GHS/min
- Lower profit but less complexity

## Future Enhancements

### Phase 2: Real-Time Cost Tracking

Currently, the endpoints show provider pricing. To track actual usage costs:

1. **Integration Required**:
   - Modify `apps/shared/integration/usage_calculator.py`
   - Add cost tracking to billing flow
   - Store cost records in database

2. **Example Integration**:
```python
from apps.shared.integration.internal_cost_tracker import InternalCostTracker

# In usage calculation:
def calculate_voice_cost(duration_minutes, tenant_id, call_id):
    # Calculate customer charge
    customer_charge = Decimal(str(duration_minutes)) * Decimal('2.50')

    # Track internal cost
    tracker = InternalCostTracker()
    tracker.record_vapi_call_cost(
        duration_minutes=duration_minutes,
        customer_charge=customer_charge,
        tenant_id=tenant_id,
        call_id=call_id,
        use_full_stack_cost=True  # or False if using own transport
    )

    # Continue with billing...
    return customer_charge
```

3. **New Endpoints Available**:
   - `/api/admin/cost-analytics/summary` - Overall cost summary
   - `/api/admin/cost-analytics/profit-analysis` - Detailed profit analysis

### Phase 3: Admin Dashboard

Create frontend dashboard showing:
- Real-time profit margins
- Cost trends over time
- Provider comparison charts
- Alerts for money-losing services

## Security

**IMPORTANT**: These endpoints are INTERNAL ONLY and contain sensitive business data:
- Never expose to end users
- Only accessible to admin users
- Monitor access logs
- Consider adding IP whitelisting
- Rotate admin tokens regularly

## Support

For questions or issues:
- Technical: Development team
- Business insights: Finance/leadership team
- Access issues: System administrator

---

**Last Updated**: 2025-10-27
**Pricing Verified**: 2025-10-27 (VAPI, Twilio, Vonage, OpenAI)
**Exchange Rate**: 1 USD = 10.785 GHS (2025-10-27)

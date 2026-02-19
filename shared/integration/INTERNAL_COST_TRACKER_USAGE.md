# Internal Cost Tracker - Usage Guide

**INTERNAL USE ONLY - DO NOT EXPOSE TO END USERS**

## Overview

The Internal Cost Tracker is a business intelligence tool that tracks actual costs paid to third-party providers (VAPI, Twilio, OpenAI, Stripe, etc.) vs. what we charge customers. This allows us to:

- Monitor actual provider costs
- Calculate profit margins per service
- Identify cost inefficiencies
- Make data-driven pricing decisions
- Track ROI across different providers

**IMPORTANT**: This data contains sensitive business information (actual costs, profit margins) and should NEVER be exposed to end users.

## Features

- ✅ Track voice call costs (VAPI, Twilio, Vonage)
- ✅ Track AI token costs (OpenAI, Anthropic, Google)
- ✅ Track payment processing fees (Stripe, Paystack, M-Pesa)
- ✅ Calculate profit margins automatically
- ✅ Generate profit analysis reports
- ✅ Cost breakdown by provider
- ✅ Customizable provider costs
- ✅ Comprehensive test coverage (30 tests)

## Installation

The Internal Cost Tracker is part of the shared integration module:

```python
from apps.shared.integration.internal_cost_tracker import (
    InternalCostTracker,
    Provider,
    CostType,
    create_custom_cost_tracker
)
```

No additional dependencies required.

## Quick Start

```python
from decimal import Decimal
from apps.shared.integration.internal_cost_tracker import InternalCostTracker

# Create tracker
tracker = InternalCostTracker()

# Record a VAPI call
cost = tracker.record_vapi_call_cost(
    duration_minutes=5.0,
    customer_charge=Decimal('12.50'),  # What we charged customer (5 min × 2.50 GHS)
    tenant_id="tenant_123",
    call_id="call_456"
)

print(f"Cost paid to VAPI: {cost.total_cost} GHS")  # 2.25 GHS (5 × 0.45)
print(f"Customer charged: {cost.customer_charge} GHS")  # 12.50 GHS
print(f"Profit: {cost.profit_margin} GHS")  # 10.25 GHS
print(f"Margin: {(cost.profit_margin / cost.customer_charge * 100):.1f}%")  # 82%

# Get overall summary
summary = tracker.get_summary()
print(f"Total profit: {summary['total_profit']} GHS")
print(f"Profit margin: {summary['profit_margin_percentage']:.2f}%")
```

## Provider Costs (INTERNAL ONLY)

These are the actual costs we pay to providers. **DO NOT share with end users.**

### Voice/Telephony
- **VAPI**: 0.45 GHS/min (we charge 2.50, profit: 2.05/min = 82% margin)
- **Twilio**: 0.30 GHS/min
- **Vonage**: 0.25 GHS/min
- **SMS**: 0.05 GHS/message

### AI Providers (per 1,000 tokens)
- **OpenAI GPT-4**: $0.01 input, $0.03 output
- **OpenAI GPT-4o-mini**: $0.00015 input, $0.0006 output
- **Anthropic**: $0.003 input, $0.015 output
- **Google Gemini**: $0.000125 input, $0.000375 output

### TTS/STT
- **OpenAI TTS**: $0.000015/character
- **ElevenLabs**: $0.00018/character
- **OpenAI Whisper**: $0.006/minute
- **Deepgram**: $0.0043/minute

### Payment Processing
- **Stripe**: 2.9% + $0.30 per transaction
- **Paystack**: 1.5% per transaction
- **M-Pesa**: 1% per transaction

### Infrastructure
- **AWS Storage**: $0.023/GB/month
- **AWS Compute**: $0.10/hour (t3.medium)

## Usage Examples

### 1. Track VAPI Call Cost

```python
from decimal import Decimal

# Record a 5-minute VAPI call
cost = tracker.record_vapi_call_cost(
    duration_minutes=5.0,
    customer_charge=Decimal('12.50'),  # What we billed
    tenant_id="tenant_123",
    call_id="call_456",
    metadata={"call_type": "inbound", "region": "ghana"}
)

# Cost breakdown:
# - We paid VAPI: 5 × 0.45 = 2.25 GHS
# - We charged customer: 12.50 GHS
# - Profit: 12.50 - 2.25 = 10.25 GHS
# - Margin: 82%
```

### 2. Track Twilio Call Cost

```python
cost = tracker.record_twilio_call_cost(
    duration_minutes=10.0,
    customer_charge=Decimal('25.00'),
    tenant_id="tenant_789",
    call_id="call_999"
)

# Cost breakdown:
# - We paid Twilio: 10 × 0.30 = 3.00 GHS
# - We charged customer: 25.00 GHS
# - Profit: 22.00 GHS
# - Margin: 88%
```

### 3. Track AI Token Costs

```python
# OpenAI GPT-4o-mini
cost = tracker.record_ai_token_cost(
    input_tokens=10000,
    output_tokens=5000,
    provider=Provider.OPENAI,
    model="gpt-4o-mini",
    customer_charge=Decimal('0.10'),
    tenant_id="tenant_123"
)

# Cost breakdown:
# - Input: 10,000/1,000 × $0.00015 = $0.0015
# - Output: 5,000/1,000 × $0.0006 = $0.0030
# - Total cost: $0.0045
# - Customer charged: $0.10
# - Profit: $0.0955
# - Margin: 95.5%

# Anthropic Claude
cost = tracker.record_ai_token_cost(
    input_tokens=2000,
    output_tokens=1000,
    provider=Provider.ANTHROPIC,
    model="claude-3",
    customer_charge=Decimal('0.30'),
    tenant_id="tenant_123"
)
```

### 4. Track Payment Processing Costs

```python
# Stripe payment
cost = tracker.record_payment_processing_cost(
    transaction_amount=Decimal('100.00'),
    provider=Provider.STRIPE,
    customer_charge=Decimal('5.00'),  # What we charged customer
    tenant_id="tenant_123",
    transaction_id="txn_stripe_123"
)

# Cost breakdown:
# - Stripe fee: 100 × 2.9% + $0.30 = $3.20
# - We charged customer: $5.00
# - Profit: $1.80
# - Margin: 36%

# Paystack payment
cost = tracker.record_payment_processing_cost(
    transaction_amount=Decimal('200.00'),
    provider=Provider.PAYSTACK,
    customer_charge=Decimal('4.00'),
    tenant_id="tenant_123",
    transaction_id="txn_paystack_456"
)

# Cost breakdown:
# - Paystack fee: 200 × 1.5% = $3.00
# - We charged customer: $4.00
# - Profit: $1.00
# - Margin: 25%
```

### 5. Calculate Profit Analysis

```python
from datetime import datetime, timedelta

# Define time period
start_date = datetime.utcnow() - timedelta(days=30)
end_date = datetime.utcnow()

# Calculate profit for voice calls
analysis = tracker.calculate_profit_analysis(
    service_name="Voice Calls",
    start_date=start_date,
    end_date=end_date,
    cost_type=CostType.VOICE_CALL
)

print(f"Service: {analysis.service_name}")
print(f"Total Revenue: {analysis.total_revenue} GHS")
print(f"Total Costs: {analysis.total_costs} GHS")
print(f"Profit: {analysis.profit} GHS")
print(f"Profit Margin: {analysis.profit_margin_percentage}%")
print(f"Customers: {analysis.customer_count}")
print(f"Transactions: {analysis.transaction_count}")
print(f"Avg Revenue/Transaction: {analysis.average_revenue_per_transaction} GHS")
print(f"Avg Cost/Transaction: {analysis.average_cost_per_transaction} GHS")
```

### 6. Get Cost Breakdown by Provider

```python
# Get total costs paid to each provider
cost_breakdown = tracker.get_cost_breakdown_by_provider()

print("Costs by Provider:")
for provider, cost in cost_breakdown.items():
    print(f"  {provider.value}: {cost} GHS")

# Output:
# Costs by Provider:
#   vapi: 2.25 GHS
#   twilio: 3.00 GHS
#   stripe: 3.20 GHS
#   openai: 0.10 GHS
```

### 7. Get Profit Breakdown by Provider

```python
# Get total profit from each provider's services
profit_breakdown = tracker.get_profit_breakdown_by_provider()

print("Profit by Provider:")
for provider, profit in profit_breakdown.items():
    print(f"  {provider.value}: {profit} GHS")

# Output:
# Profit by Provider:
#   vapi: 10.25 GHS
#   twilio: 22.00 GHS
#   stripe: 1.80 GHS
```

### 8. Get Overall Summary

```python
summary = tracker.get_summary()

print(f"Total Revenue: {summary['total_revenue']} GHS")
print(f"Total Costs: {summary['total_costs']} GHS")
print(f"Total Profit: {summary['total_profit']} GHS")
print(f"Profit Margin: {summary['profit_margin_percentage']:.2f}%")
print(f"Transactions: {summary['transaction_count']}")
print("\nCost by Provider:")
for provider, cost in summary['cost_by_provider'].items():
    print(f"  {provider}: {cost} GHS")
print("\nProfit by Provider:")
for provider, profit in summary['profit_by_provider'].items():
    print(f"  {provider}: {profit} GHS")
```

### 9. Custom Provider Costs

If you need to test with different provider costs:

```python
from apps.shared.integration.internal_cost_tracker import create_custom_cost_tracker
from decimal import Decimal

# Create tracker with custom costs
tracker = create_custom_cost_tracker({
    "vapi_cost_per_minute": Decimal('0.50'),  # Test with higher VAPI cost
    "stripe_percentage": Decimal('0.03'),  # Test with 3% Stripe fee
    "openai_gpt4_input_cost": Decimal('0.012')  # Test with different OpenAI cost
})

# Use tracker with custom costs
cost = tracker.record_vapi_call_cost(
    duration_minutes=5.0,
    customer_charge=Decimal('12.50'),
    tenant_id="tenant_123"
)

# Now uses 0.50/min instead of 0.45/min
assert cost.unit_cost == Decimal('0.50')
assert cost.total_cost == Decimal('2.50')  # 5 × 0.50
```

### 10. Reset Tracker

```python
# Clear all cost records
tracker.reset()

assert len(tracker.cost_records) == 0
```

## Integration Examples

### Integration with Usage Calculator

```python
from apps.shared.integration.usage_calculator import UsageCalculator
from apps.shared.integration.internal_cost_tracker import InternalCostTracker
from decimal import Decimal

# Track both customer billing and internal costs
usage_calc = UsageCalculator()
cost_tracker = InternalCostTracker()

# Customer makes a call
duration_minutes = 5.0
tenant_id = "tenant_123"

# Calculate customer charge
customer_charge = usage_calc.calculate_voice_cost(
    duration_minutes=duration_minutes,
    tier=PricingTier.BASIC,
    is_inbound=True
)  # Returns 12.50 (5 × 2.50)

# Track internal cost
internal_cost = cost_tracker.record_vapi_call_cost(
    duration_minutes=duration_minutes,
    customer_charge=customer_charge,
    tenant_id=tenant_id
)

# Now you have both:
# - Customer billing: 12.50 GHS (what they pay)
# - Internal cost: 2.25 GHS (what we pay VAPI)
# - Profit: 10.25 GHS (what we keep)
```

### Integration with Wallet System

```python
from apps.shared.integration.wallet.wallet_service import WalletService
from apps.shared.integration.internal_cost_tracker import InternalCostTracker

wallet = WalletService()
tracker = InternalCostTracker()

# Customer deposits money via Stripe
deposit_amount = Decimal('100.00')
transaction = await wallet.deposit(
    user_id="user_123",
    tenant_id="tenant_123",
    amount=deposit_amount,
    provider=PaymentProvider.STRIPE
)

# Track payment processing cost
processing_cost = tracker.record_payment_processing_cost(
    transaction_amount=deposit_amount,
    provider=Provider.STRIPE,
    customer_charge=Decimal('0.00'),  # We absorb the fee
    tenant_id="tenant_123",
    transaction_id=transaction.id
)

# Stripe charged us: $3.20 (2.9% + $0.30)
# We charged customer: $0.00
# Loss: -$3.20 (we absorbed the fee)
```

## Business Intelligence Reports

### Monthly Profit Report

```python
from datetime import datetime, timedelta

def generate_monthly_report(tracker: InternalCostTracker, month: int, year: int):
    """Generate monthly profit report."""
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Get analysis for each service
    voice_analysis = tracker.calculate_profit_analysis(
        service_name="Voice Calls",
        start_date=start_date,
        end_date=end_date,
        cost_type=CostType.VOICE_CALL
    )

    ai_analysis = tracker.calculate_profit_analysis(
        service_name="AI Services",
        start_date=start_date,
        end_date=end_date,
        cost_type=CostType.AI_TOKENS
    )

    payment_analysis = tracker.calculate_profit_analysis(
        service_name="Payment Processing",
        start_date=start_date,
        end_date=end_date,
        cost_type=CostType.PAYMENT_PROCESSING
    )

    # Generate report
    report = {
        "month": f"{year}-{month:02d}",
        "voice_calls": {
            "revenue": float(voice_analysis.total_revenue),
            "costs": float(voice_analysis.total_costs),
            "profit": float(voice_analysis.profit),
            "margin_pct": float(voice_analysis.profit_margin_percentage),
            "transactions": voice_analysis.transaction_count
        },
        "ai_services": {
            "revenue": float(ai_analysis.total_revenue),
            "costs": float(ai_analysis.total_costs),
            "profit": float(ai_analysis.profit),
            "margin_pct": float(ai_analysis.profit_margin_percentage),
            "transactions": ai_analysis.transaction_count
        },
        "payment_processing": {
            "revenue": float(payment_analysis.total_revenue),
            "costs": float(payment_analysis.total_costs),
            "profit": float(payment_analysis.profit),
            "margin_pct": float(payment_analysis.profit_margin_percentage),
            "transactions": payment_analysis.transaction_count
        },
        "total": {
            "revenue": sum([voice_analysis.total_revenue, ai_analysis.total_revenue, payment_analysis.total_revenue]),
            "costs": sum([voice_analysis.total_costs, ai_analysis.total_costs, payment_analysis.total_costs]),
            "profit": sum([voice_analysis.profit, ai_analysis.profit, payment_analysis.profit])
        }
    }

    return report

# Example usage
report = generate_monthly_report(tracker, month=10, year=2025)
print(f"Monthly Report for {report['month']}")
print(f"Total Revenue: {report['total']['revenue']} GHS")
print(f"Total Costs: {report['total']['costs']} GHS")
print(f"Total Profit: {report['total']['profit']} GHS")
```

### Provider ROI Analysis

```python
def analyze_provider_roi(tracker: InternalCostTracker):
    """Analyze ROI for each provider."""
    cost_breakdown = tracker.get_cost_breakdown_by_provider()
    profit_breakdown = tracker.get_profit_breakdown_by_provider()

    print("Provider ROI Analysis:")
    print("-" * 60)

    for provider in cost_breakdown.keys():
        cost = cost_breakdown[provider]
        profit = profit_breakdown.get(provider, Decimal('0'))
        revenue = cost + profit
        roi = (profit / cost * 100) if cost > 0 else Decimal('0')

        print(f"\n{provider.value.upper()}:")
        print(f"  Revenue: {revenue:.2f} GHS")
        print(f"  Cost: {cost:.2f} GHS")
        print(f"  Profit: {profit:.2f} GHS")
        print(f"  ROI: {roi:.2f}%")

# Example usage
analyze_provider_roi(tracker)

# Output:
# Provider ROI Analysis:
# ------------------------------------------------------------
#
# VAPI:
#   Revenue: 12.50 GHS
#   Cost: 2.25 GHS
#   Profit: 10.25 GHS
#   ROI: 455.56%
#
# STRIPE:
#   Revenue: 5.00 GHS
#   Cost: 3.20 GHS
#   Profit: 1.80 GHS
#   ROI: 56.25%
```

## Security Considerations

**CRITICAL**: This module contains sensitive business data. Follow these security practices:

1. **Never expose to end users**: Cost data is for internal/admin use only
2. **Access control**: Restrict access to admin/finance roles
3. **Secure storage**: If persisting data, encrypt at rest
4. **Audit logs**: Log all access to cost data
5. **No public APIs**: Never create public-facing endpoints with cost data

## Data Models

### ActualCost

```python
class ActualCost(BaseModel):
    id: str  # Auto-generated UUID
    timestamp: datetime  # When cost was recorded
    provider: Provider  # VAPI, Twilio, OpenAI, etc.
    cost_type: CostType  # voice_call, ai_tokens, etc.
    quantity: Decimal  # Amount of resource used
    unit: str  # minutes, tokens, etc.
    unit_cost: Decimal  # Cost per unit
    total_cost: Decimal  # Total cost paid
    customer_charge: Optional[Decimal]  # What we charged customer
    profit_margin: Optional[Decimal]  # customer_charge - total_cost
    currency: str = "GHS"
    tenant_id: Optional[str]
    user_id: Optional[str]
    call_id: Optional[str]
    transaction_id: Optional[str]
    metadata: Dict[str, Any]
```

### ProfitAnalysis

```python
class ProfitAnalysis(BaseModel):
    service_name: str
    total_revenue: Decimal
    total_costs: Decimal
    profit: Decimal
    profit_margin_percentage: Decimal
    customer_count: int
    transaction_count: int
    average_revenue_per_transaction: Decimal
    average_cost_per_transaction: Decimal
    start_date: datetime
    end_date: datetime
```

## Testing

The module has comprehensive test coverage:

```bash
# Run all tests
PYTHONPATH=/opt/kasaai /opt/kasaai/apps/venv/bin/python -m pytest \
    apps/shared/integration/tests/test_internal_cost_tracker.py -v

# Run specific test class
pytest apps/shared/integration/tests/test_internal_cost_tracker.py::TestVAPICallCostTracking -v

# Run with coverage
pytest apps/shared/integration/tests/test_internal_cost_tracker.py --cov=apps.shared.integration.internal_cost_tracker
```

**Test Coverage**: 30 tests covering:
- ActualCost model creation and validation
- VAPI call cost tracking
- Twilio call cost tracking
- AI token costs (OpenAI, Anthropic, Google)
- Payment processing costs (Stripe, Paystack, M-Pesa)
- Profit analysis calculation
- Cost/profit breakdowns
- Summary generation
- Custom cost tracker
- Edge cases (zero values, rounding, etc.)

## Support

For questions or issues with the Internal Cost Tracker:

1. Check test files for usage examples
2. Review this documentation
3. Contact the KasaAI development team

---

**Remember**: This is INTERNAL ONLY. Never expose cost data to end users.

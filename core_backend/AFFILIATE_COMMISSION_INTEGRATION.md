# Affiliate Commission Integration Guide

## Overview

This document explains how to integrate affiliate commission processing into the payment flow. After a successful wallet top-up or purchase, the system should automatically calculate and attribute commissions to affiliates in the referral chain.

## Architecture

```
User makes purchase → Payment processed → Wallet credited → Commission calculated → Affiliates earn
```

The commission processing is decoupled from the payment flow using the `AffiliateCommissionProcessor` service, which can be called after any successful transaction.

## Integration Points

### 1. Wallet Top-Up Flow

After a successful wallet deposit (via Paystack, Stripe, or other provider), call the commission processor:

```python
from backend.services.affiliate_commission_processor import process_transaction_commission
from decimal import Decimal

# After successful wallet top-up
async def complete_wallet_topup(transaction_id: str, user_id: str, organization_id: str, amount: Decimal):
    # ... existing code to credit wallet ...

    # Process affiliate commissions
    commission_result = await process_transaction_commission(
        user_id=user_id,
        organization_id=organization_id,
        transaction_amount=amount,
        transaction_id=transaction_id,
        transaction_type="wallet_topup"
    )

    if commission_result["success"]:
        logger.info(
            f"Commission processing complete: {commission_result['commissions_calculated']} "
            f"commissions created totaling ${commission_result['total_commission_amount']}"
        )
    else:
        logger.error(f"Commission processing failed: {commission_result.get('error')}")
```

### 2. Direct Purchase Flow

For direct purchases (subscriptions, one-time purchases), follow the same pattern:

```python
# After successful subscription purchase
commission_result = await process_transaction_commission(
    user_id=user_id,
    organization_id=organization_id,
    transaction_amount=Decimal("99.00"),
    transaction_id=subscription_transaction_id,
    transaction_type="subscription"
)
```

### 3. Webhook Integration

If using webhooks for payment confirmation (recommended), integrate in the webhook handler:

**File:** `backend/services/wallet_service.py` or `backend/routes/wallet.py`

```python
@router.post("/webhooks/payment/{provider}")
async def handle_payment_webhook(
    provider: str,
    request: Request,
    current_user: User = Depends(get_current_user_mongo)
):
    # ... existing webhook verification ...

    # Parse webhook payload
    payload = await request.json()
    transaction_id = payload.get("transaction_id")
    amount = Decimal(str(payload.get("amount")))
    user_id = payload.get("user_id")
    org_id = payload.get("organization_id")

    # ... existing code to credit wallet ...

    # Process commissions asynchronously (don't block webhook response)
    from backend.services.affiliate_commission_processor import process_transaction_commission

    asyncio.create_task(
        process_transaction_commission(
            user_id=user_id,
            organization_id=org_id,
            transaction_amount=amount,
            transaction_id=transaction_id
        )
    )

    return {"status": "success"}
```

### 4. Shared Library Integration

If using the shared payment library, integrate at the transaction completion handler:

**File:** `shared/integration/payment_webhook_processor.py` (if exists)

```python
async def on_transaction_complete(transaction: Dict[str, Any]):
    """Called after successful transaction completion."""
    # ... existing code ...

    # Trigger commission calculation
    from backend.services.affiliate_commission_processor import process_transaction_commission

    await process_transaction_commission(
        user_id=transaction["user_id"],
        organization_id=transaction["organization_id"],
        transaction_amount=Decimal(str(transaction["amount"])),
        transaction_id=transaction["id"]
    )
```

## Commission Processing Flow

1. **Check Attribution**: The processor checks if the user was referred by looking up their `referral_attribution` record
2. **Build Chain**: If attributed, the system builds the affiliate chain (up to 3 tiers)
3. **Calculate Commissions**: Commissions are calculated based on tier rates:
   - Tier 1 (Direct): 15%
   - Tier 2: 8%
   - Tier 3: 3%
4. **Create Records**: `commission_record` documents are created in MongoDB with status `pending`
5. **Update Stats**: Affiliate profile stats are updated (total_commissions_earned, pending_commissions)

## Commission Lifecycle

```
pending → approved → paid
```

- **pending**: Initial state, commission calculated but not yet approved
- **approved**: Admin has approved the commission (can be automated)
- **paid**: Commission has been paid out to affiliate

## Error Handling

The commission processor is designed to fail gracefully:

- If a user has no referral attribution, it returns success with 0 commissions
- If commission calculation fails, it logs the error but doesn't throw exceptions
- Transaction can complete successfully even if commission processing fails
- Failed commissions can be retried using the batch processor

## Batch Processing

For backfilling or retry scenarios:

```python
from backend.services.affiliate_commission_processor import get_commission_processor

processor = get_commission_processor()

transactions = [
    {
        "user_id": "user1",
        "organization_id": "org1",
        "transaction_amount": 100.00,
        "transaction_id": "txn1"
    },
    # ... more transactions
]

result = await processor.process_batch_commissions(transactions)
print(f"Processed {result['successful']}/{result['total_transactions']} transactions")
```

## Testing

### Unit Test Example

```python
import pytest
from decimal import Decimal
from backend.services.affiliate_commission_processor import process_transaction_commission

@pytest.mark.asyncio
async def test_commission_processing():
    # Setup: Create affiliate and referred user
    # ...

    # Process commission
    result = await process_transaction_commission(
        user_id="referred_user_id",
        organization_id="org_id",
        transaction_amount=Decimal("100.00"),
        transaction_id="test_txn_123"
    )

    assert result["success"] == True
    assert result["commissions_calculated"] > 0
    assert result["total_commission_amount"] > 0
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_full_purchase_flow_with_commission():
    # 1. User A joins affiliate program
    # 2. User B signs up with User A's referral code
    # 3. User B makes a $100 purchase
    # 4. Verify User A receives $15 commission
    pass
```

## Monitoring

### Logs

Commission processing logs with prefix `[Commission Processor]`:

```
INFO: Processing commission for transaction txn123: user=user456, amount=$100.00
INFO: User user456 was referred by affiliate aff789 via code REF123
INFO: Successfully calculated 2 commissions totaling $23.00 for transaction txn123
```

### Metrics to Track

- Total commissions calculated per day
- Average commission per transaction
- Failed commission processing rate
- Payout requests per month

## Security Considerations

1. **Self-Referral Prevention**: System checks that affiliates can't refer themselves
2. **Duplicate Prevention**: Only one attribution per user is allowed
3. **Audit Trail**: All commission records are immutable with timestamps
4. **Rate Limiting**: Consider rate limiting on commission endpoints if exposed publicly

## Future Enhancements

1. **Automated Approval**: Auto-approve commissions under a certain threshold
2. **Commission Clawback**: Handle refunds by reversing commissions
3. **Custom Rates**: Allow setting custom commission rates per affiliate
4. **Time-Based Bonuses**: Bonus commissions for high-performing periods
5. **Fraud Detection**: ML-based fraud detection for suspicious patterns

## Support

For issues or questions about commission integration:

1. Check logs for error messages
2. Verify attribution records exist for test users
3. Test commission calculation endpoint directly: `POST /api/affiliates/internal/process-commission`
4. Review affiliate service logs for commission calculation details

## Deployment Checklist

- [ ] Commission processor integrated into payment flow
- [ ] Webhook handlers updated (if applicable)
- [ ] Error monitoring alerts configured
- [ ] Commission processing logs reviewed
- [ ] Test transactions verified in staging
- [ ] Admin approval workflow documented
- [ ] Payout process documented

---

**Last Updated:** 2025-11-18
**Version:** 1.0

# Wallet Fraud Detection System - Usage Guide

## Overview

The fraud detection system provides real-time protection against fraudulent transactions using velocity checks, amount anomaly detection, and behavioral pattern analysis.

## Features

- ✅ **Velocity Checks** - Detect rapid transaction patterns
- ✅ **Amount Anomaly Detection** - Flag unusual transaction amounts
- ✅ **Pattern Analysis** - Identify suspicious behavioral patterns
- ✅ **Risk Scoring** - Calculate risk score (0-100) for each transaction
- ✅ **Automatic Blocking** - Block high-risk transactions (81-100)
- ✅ **Manual Review Queue** - Flag medium-risk transactions for review
- ✅ **User Risk Profiles** - Track user behavior over time
- ✅ **Custom Rules** - Define custom fraud detection rules

## Quick Start

### 1. Initialize FraudDetectionService

```python
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.integration.wallet import (
    WalletService,
    FraudDetectionService,
    NotificationService
)

# Initialize MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.kasaai_core

# Initialize Fraud Detection
fraud_service = FraudDetectionService(database=db)

# Initialize Wallet Service with fraud detection
wallet_service = WalletService(
    database=db,
    fraud_detection_service=fraud_service,  # Fraud detection enabled!
    notification_service=notification_service  # Optional
)
```

### 2. Fraud Detection is Automatic

Once configured, fraud checks run automatically on all deposits and withdrawals:

```python
# This automatically runs fraud detection
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet123",
    amount=Decimal("5000.00"),  # Large amount - might trigger fraud check
    payment_provider=PaymentProvider.STRIPE
)

# If fraud score >= 81, transaction is BLOCKED
# If fraud score 61-80, transaction is FLAGGED for review
# If fraud score 31-60, transaction proceeds with ALERT
# If fraud score 0-30, transaction APPROVED
```

## Fraud Detection Rules

### Built-in Velocity Rules

**1. High Velocity - 5 Minutes**
- **Trigger**: More than 3 transactions in 5 minutes
- **Risk Score**: +30
- **Action**: Alert

**2. High Velocity - 1 Hour**
- **Trigger**: More than 10 transactions in 1 hour
- **Risk Score**: +20
- **Action**: Alert

**3. Multiple Failed Attempts**
- **Trigger**: 5+ failed transactions in 1 hour
- **Risk Score**: +50
- **Action**: Review

### Built-in Amount Rules

**4. Amount 5x Average**
- **Trigger**: Transaction amount is 5x user's average
- **Risk Score**: +40
- **Action**: Review

**5. Large Transaction on New Account**
- **Trigger**: Transaction > $1000 on account < 7 days old
- **Risk Score**: +60
- **Action**: Review

**6. Withdrawal >80% of Balance**
- **Trigger**: Withdrawal of 80%+ of wallet balance
- **Risk Score**: +30
- **Action**: Alert

### Built-in Pattern Rules

**7. Unusual Time**
- **Trigger**: Transaction between 2 AM - 5 AM
- **Risk Score**: +20
- **Action**: Alert

**8. Rapid Account Creation + Large Transaction**
- **Trigger**: Account < 1 hour old + transaction > $100
- **Risk Score**: +70
- **Action**: Review

**9. Multiple Payment Methods Added**
- **Trigger**: 3+ payment methods added in 24 hours
- **Risk Score**: +40
- **Action**: Review

## Risk Score Actions

| Risk Score | Risk Level | Decision | Action |
|-----------|------------|----------|--------|
| 0-30 | LOW | ✅ Approved | Transaction proceeds normally |
| 31-60 | MEDIUM | ⚠️  Flagged | Transaction proceeds with alert sent |
| 61-80 | HIGH | 🔍 Review | Transaction proceeds but flagged for manual review |
| 81-100 | CRITICAL | 🚫 Blocked | Transaction blocked, user notified |

## User Risk Profiles

The system maintains a risk profile for each user:

```python
# Get user's risk profile
risk_profile = await fraud_service.get_user_risk_profile(
    user_id="user123",
    wallet_id="wallet123"
)

print(f"Total transactions: {risk_profile.total_transactions}")
print(f"Average amount: {risk_profile.average_amount}")
print(f"Risk score: {risk_profile.risk_score}")
print(f"Risk level: {risk_profile.risk_level}")
print(f"Trusted: {risk_profile.trusted}")
print(f"Flagged transactions: {risk_profile.flagged_transactions_count}")
```

Risk Profile includes:
- Transaction statistics (count, amounts, averages)
- Velocity metrics (transactions per hour/day/week)
- Failure tracking
- Behavioral patterns
- Fraud history

## Manual Review Queue

### Get Pending Reviews

```python
# Get transactions requiring manual review
pending_reviews = await fraud_service.get_review_queue(limit=50)

for fraud_check in pending_reviews:
    print(f"Transaction: {fraud_check.transaction_id}")
    print(f"Risk Score: {fraud_check.risk_score}")
    print(f"Triggered Rules: {fraud_check.triggered_rules}")
    print(f"User: {fraud_check.user_id}")
```

### Approve Transaction

```python
# Approve a flagged transaction
success = await fraud_service.approve_transaction(
    fraud_check_id="fraud_check_123",
    reviewer_id="admin_456",
    notes="Verified with customer via phone"
)
```

### Reject Transaction

```python
# Reject a flagged transaction
success = await fraud_service.reject_transaction(
    fraud_check_id="fraud_check_123",
    reviewer_id="admin_456",
    notes="Confirmed fraudulent activity"
)
```

## Custom Fraud Rules

### Create Custom Rule

```python
from apps.shared.integration.wallet import FraudRule, FraudRuleType, FraudAction

# Define custom rule
custom_rule = FraudRule(
    id="custom_crypto_withdrawal",
    name="Large Crypto Withdrawal",
    description="Withdrawal > $10,000 to crypto address",
    rule_type=FraudRuleType.AMOUNT,
    condition={
        "amount_threshold": 10000,
        "payment_method_type": "crypto"
    },
    risk_score=50,
    action=FraudAction.REVIEW,
    enabled=True,
    priority=10
)

# Save to database
await db.fraud_rules.insert_one(custom_rule.dict())
```

### Disable Rule

```python
# Disable a specific rule
await db.fraud_rules.update_one(
    {"id": "custom_crypto_withdrawal"},
    {"$set": {"enabled": False}}
)
```

## Integration with Notifications

When fraud detection blocks a transaction, it automatically sends security alerts:

```python
# Blocked transaction triggers notification automatically
await wallet_service.deposit(...)
# ❌ Transaction blocked (risk score: 95)
# 📧 Email sent: "Suspicious Activity Detected"
# 📱 SMS sent: "Transaction blocked due to security concerns"
```

## Monitoring & Analytics

### Get Fraud Statistics

```python
from datetime import datetime, timedelta

# Get fraud stats for last 30 days
period_start = datetime.utcnow() - timedelta(days=30)
period_end = datetime.utcnow()

# Count checks by decision
approved = await db.fraud_checks.count_documents({
    "decision": "approved",
    "created_at": {"$gte": period_start, "$lte": period_end}
})

flagged = await db.fraud_checks.count_documents({
    "decision": "flagged",
    "created_at": {"$gte": period_start, "$lte": period_end}
})

blocked = await db.fraud_checks.count_documents({
    "decision": "blocked",
    "created_at": {"$gte": period_start, "$lte": period_end}
})

print(f"Approved: {approved}")
print(f"Flagged: {flagged}")
print(f"Blocked: {blocked}")
```

### Most Triggered Rules

```python
# Get most frequently triggered rules
pipeline = [
    {"$unwind": "$triggered_rules"},
    {"$group": {
        "_id": "$triggered_rules",
        "count": {"$sum": 1}
    }},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]

results = await db.fraud_checks.aggregate(pipeline).to_list(10)

for rule in results:
    print(f"Rule: {rule['_id']}, Triggers: {rule['count']}")
```

## Testing Fraud Detection

### Test with Simulated Scenarios

```python
# Scenario 1: Rapid transactions (velocity check)
for i in range(5):
    await wallet_service.deposit(
        wallet_id="test_wallet",
        amount=Decimal("10.00")
    )
    # After 3rd transaction, risk score increases
    # After 5th, might be blocked

# Scenario 2: Large transaction on new account
new_user_wallet = await wallet_service.get_or_create_wallet(
    user_id="brand_new_user",
    currency=Currency.USD
)

await wallet_service.deposit(
    wallet_id=new_user_wallet.id,
    amount=Decimal("5000.00")  # Large amount
)
# ⚠️ Risk score: 60-70 (flagged for review)

# Scenario 3: Unusual amount
# User's average transaction: $20
await wallet_service.deposit(
    wallet_id="regular_user_wallet",
    amount=Decimal("500.00")  # 25x average!
)
# ⚠️ Risk score: 40 (flagged)
```

### Bypass Fraud Detection (Testing Only)

```python
# Initialize wallet service WITHOUT fraud detection
test_wallet_service = WalletService(
    database=db,
    fraud_detection_service=None  # Disabled
)

# Transactions will NOT be checked
await test_wallet_service.deposit(...)  # No fraud check
```

## Best Practices

### 1. Mark Trusted Users

```python
# Mark verified/trusted users
await db.user_risk_profiles.update_one(
    {"user_id": "verified_user_123"},
    {"$set": {"trusted": True}}
)
# Trusted users skip fraud checks
```

### 2. Gradually Adjust Thresholds

```python
# Start conservative, then adjust based on data
# Week 1: Block at 70+
# Week 2-4: Monitor false positives
# Month 2: Adjust to 81+ if needed
```

### 3. Review Blocked Transactions Daily

```python
# Daily review of blocked transactions
blocked_today = await db.fraud_checks.find({
    "decision": "blocked",
    "created_at": {
        "$gte": datetime.utcnow().replace(hour=0, minute=0)
    }
}).to_list(100)

# Review for false positives
```

### 4. Monitor False Positive Rate

```python
# Track false positives
total_reviewed = await db.fraud_checks.count_documents({
    "status": "reviewed"
})

false_positives = await db.fraud_checks.count_documents({
    "status": "reviewed",
    "review_decision": "approved"  # Reviewer approved what was flagged
})

false_positive_rate = (false_positives / total_reviewed) * 100
print(f"False positive rate: {false_positive_rate:.2f}%")

# Goal: < 5% false positive rate
```

### 5. Use Metadata for Context

```python
# Add context to help fraud detection
await wallet_service.deposit(
    wallet_id="wallet123",
    amount=Decimal("1000.00"),
    metadata={
        "ip_address": "192.168.1.1",
        "device_id": "device_abc123",
        "user_agent": "Mozilla/5.0...",
        "geolocation": {"country": "GH", "city": "Accra"}
    }
)
# Metadata is stored with fraud check for analysis
```

## Troubleshooting

### Transaction Blocked Unexpectedly

```python
# Check fraud check details
fraud_check = await db.fraud_checks.find_one({
    "transaction_id": "txn_123"
})

print(f"Risk Score: {fraud_check['risk_score']}")
print(f"Triggered Rules: {fraud_check['triggered_rules']}")
print(f"Rule Details: {fraud_check['rule_details']}")

# Review and approve if false positive
await fraud_service.approve_transaction(
    fraud_check_id=fraud_check["id"],
    reviewer_id="admin_123",
    notes="False positive - legitimate transaction"
)
```

### Too Many False Positives

1. **Lower risk score thresholds** in `_determine_action()`
2. **Disable overly sensitive rules**
3. **Mark regular users as trusted**
4. **Adjust rule weights** (reduce risk_score values)

### Missing Fraud Checks

```python
# Verify fraud service is configured
if wallet_service.fraud_detection_service:
    print("✅ Fraud detection enabled")
else:
    print("❌ Fraud detection NOT configured")
```

## API Endpoints

### Get Fraud Check

```http
GET /api/wallet/fraud-checks/{fraud_check_id}
Authorization: Bearer <token>
```

### Get Review Queue

```http
GET /api/wallet/fraud-checks/review-queue
Authorization: Bearer <admin-token>
```

### Approve/Reject

```http
POST /api/wallet/fraud-checks/{fraud_check_id}/approve
Authorization: Bearer <admin-token>

{
  "notes": "Verified with customer"
}
```

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-core-backend -f | grep fraud`
- Email: support@kasaai.ailabsafrica.com
- Documentation: https://docs.kasaai.com/wallet/fraud-detection

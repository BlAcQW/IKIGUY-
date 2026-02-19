# Paystack Payment Provider - Usage Guide

## Overview

The Paystack provider enables payment processing for customers in Nigeria, Ghana, Kenya, and South Africa. It supports cards, bank transfers, mobile money, and USSD payments.

## Coverage

- 🇳🇬 **Nigeria** (NGN)
- 🇬🇭 **Ghana** (GHS)
- 🇰🇪 **Kenya** (KES)
- 🇿🇦 **South Africa** (ZAR)

## Supported Payment Methods

- **Cards**: Visa, Mastercard, Verve
- **Bank Transfers**: Direct bank transfers
- **Mobile Money**: MTN Mobile Money, Vodafone Cash, AirtelTigo Money (Ghana)
- **USSD**: USSD payments (Nigeria)
- **QR Code**: QR code payments

## Quick Start

### 1. Get Paystack API Keys

1. Sign up at https://paystack.com
2. Get your API keys from Settings > API Keys
   - Public Key: `pk_test_xxx` or `pk_live_xxx`
   - Secret Key: `sk_test_xxx` or `sk_live_xxx`
3. Set up webhook URL and get webhook secret

### 2. Initialize Paystack Provider

```python
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.integration.wallet import (
    WalletService,
    PaymentProvider,
    ProviderConfig
)
from apps.shared.integration.wallet.providers import PaystackProvider

# Create Paystack config
paystack_config = ProviderConfig(
    provider=PaymentProvider.PAYSTACK,
    api_key="pk_test_xxx",  # Public key
    secret_key="sk_test_xxx",  # Secret key
    webhook_secret="your_webhook_secret",
    is_test_mode=True,  # Use test mode for development
    redirect_url="https://yourapp.com/payment/callback"
)

# Initialize provider
paystack_provider = PaystackProvider(paystack_config)

# Initialize wallet service
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.kasaai_core

wallet_service = WalletService(database=db)

# Register Paystack provider
wallet_service.register_provider(paystack_provider)
```

### 3. Create a Deposit

```python
from decimal import Decimal

# Initialize deposit (creates payment URL)
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("100.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    metadata={
        "customer_email": "customer@example.com"  # Required
    }
)

# Redirect user to payment URL
print(f"Payment URL: {payment_result.payment_url}")
print(f"Reference: {payment_result.reference}")

# User completes payment on Paystack checkout page
# Paystack sends webhook to your server
# Webhook processor updates transaction status automatically
```

## Payment Channels

### All Channels (Default)

```python
# Allow all payment methods
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("50.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    metadata={"customer_email": "customer@example.com"}
)
```

### Specific Channel

```python
# Only allow card payments
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("50.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    payment_method_id="card",  # Specify channel
    metadata={"customer_email": "customer@example.com"}
)

# Available channels:
# - "card"
# - "bank"
# - "ussd"
# - "qr"
# - "mobile_money"
# - "bank_transfer"
```

### Mobile Money (Ghana)

```python
# Mobile money payment
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("20.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    payment_method_id="mobile_money",
    metadata={
        "customer_email": "customer@example.com",
        "mobile_money": {
            "phone": "0241234567",
            "provider": "mtn"  # mtn, vod, tgo
        }
    }
)
```

## Customer Management

### Create Customer

```python
# Create Paystack customer
customer = await paystack_provider.create_customer(
    user_id="user_123",
    email="customer@example.com",
    metadata={
        "name": "John Doe",
        "phone": "0241234567"
    }
)

print(f"Customer Code: {customer['customer_code']}")  # CUS_xxxxx

# Use customer code for future payments
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("100.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    customer_id=customer['customer_code']  # Use customer code
)
```

## Bank Operations

### List Banks

```python
# Get list of banks in Ghana
banks = await paystack_provider.list_banks("ghana")

for bank in banks:
    print(f"{bank['name']} - {bank['code']}")

# Available countries:
# - "ghana"
# - "nigeria"
# - "kenya"
# - "south africa"
```

### Resolve Account Number

```python
# Verify bank account before withdrawal
result = await paystack_provider.resolve_account_number(
    account_number="0123456789",
    bank_code="044"  # Access Bank code
)

if result["success"]:
    print(f"Account Name: {result['account_name']}")
    print(f"Account Number: {result['account_number']}")
else:
    print(f"Error: {result['error']}")
```

## Withdrawals (Transfers)

### Create Transfer Recipient

```python
# Step 1: Create recipient
recipient = await paystack_provider.create_transfer_recipient(
    account_name="John Doe",
    account_number="0123456789",
    bank_code="044",  # Bank code from list_banks()
    currency=Currency.GHS
)

if recipient["success"]:
    recipient_code = recipient["recipient_code"]  # RCP_xxxxx
```

### Initiate Transfer

```python
# Step 2: Initiate transfer
transfer = await paystack_provider.initiate_transfer(
    recipient_code="RCP_xxxxx",
    amount=Decimal("100.00"),
    currency=Currency.GHS,
    reason="Wallet withdrawal - txn_123"
)

if transfer["success"]:
    print(f"Transfer Code: {transfer['transfer_code']}")
    print(f"Status: {transfer['status']}")  # pending, success, failed
```

### Complete Withdrawal Flow

```python
# Complete example: Withdraw to bank account
async def withdraw_to_bank(
    wallet_id: str,
    amount: Decimal,
    account_number: str,
    bank_code: str
):
    # 1. Verify account
    account = await paystack_provider.resolve_account_number(
        account_number, bank_code
    )

    if not account["success"]:
        return {"error": "Invalid account number"}

    # 2. Create recipient
    recipient = await paystack_provider.create_transfer_recipient(
        account_name=account["account_name"],
        account_number=account_number,
        bank_code=bank_code,
        currency=Currency.GHS
    )

    if not recipient["success"]:
        return {"error": "Failed to create recipient"}

    # 3. Create withdrawal transaction
    transaction = await wallet_service.withdraw(
        wallet_id=wallet_id,
        amount=amount,
        payment_provider=PaymentProvider.PAYSTACK,
        payment_method_id=recipient["recipient_code"],
        metadata={
            "recipient_code": recipient["recipient_code"],
            "account_name": account["account_name"],
            "account_number": account_number,
            "bank_code": bank_code
        }
    )

    # 4. Initiate transfer
    transfer = await paystack_provider.initiate_transfer(
        recipient_code=recipient["recipient_code"],
        amount=amount,
        currency=Currency.GHS,
        reason=f"Withdrawal - {transaction.id}"
    )

    return {
        "success": transfer["success"],
        "transaction_id": transaction.id,
        "transfer_code": transfer.get("transfer_code")
    }
```

## Webhook Processing

### Set Up Webhook URL

1. Go to Paystack Dashboard > Settings > API Keys & Webhooks
2. Set webhook URL: `https://yourapp.com/api/wallet/webhooks/paystack`
3. Copy webhook secret

### Process Webhooks

```python
from fastapi import Request, HTTPException

@app.post("/api/wallet/webhooks/paystack")
async def handle_paystack_webhook(request: Request):
    # Get signature from header
    signature = request.headers.get("x-paystack-signature")

    # Get raw body
    raw_body = await request.body()

    # Parse JSON
    payload = await request.json()

    # Verify signature
    is_valid = await paystack_provider.verify_webhook(
        payload=payload,
        signature=signature,
        raw_payload=raw_body
    )

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook
    success, transaction_id, provider_data = await paystack_provider.process_webhook(payload)

    if transaction_id:
        if success:
            # Update transaction as completed
            await wallet_service.process_deposit_success(
                transaction_id=transaction_id,
                provider_transaction_id=provider_data["provider_id"],
                provider_data=provider_data
            )
        else:
            # Update transaction as failed
            await wallet_service.process_deposit_failure(
                transaction_id=transaction_id,
                reason=provider_data.get("failure_reason", "Payment failed")
            )

    return {"status": "success"}
```

### Supported Webhook Events

- **charge.success**: Payment completed successfully
- **charge.failed**: Payment failed
- **transfer.success**: Transfer (withdrawal) completed
- **transfer.failed**: Transfer failed
- **refund.processed**: Refund completed

## Transaction Status

### Check Transaction Status

```python
# Query transaction status from Paystack
status = await paystack_provider.get_transaction_status("ref_xxxxx")

print(f"Status: {status['status']}")  # success, failed, pending
print(f"Amount: {status['amount']}")
print(f"Channel: {status['channel']}")
print(f"Paid at: {status['paid_at']}")
```

## Refunds

### Full Refund

```python
# Refund entire amount
result = await paystack_provider.refund_payment(
    provider_transaction_id="ref_xxxxx",
    reason="Customer requested refund"
)

if result["success"]:
    print(f"Refund ID: {result['refund_id']}")
    print(f"Amount: {result['amount']}")
    print(f"Status: {result['status']}")
```

### Partial Refund

```python
# Refund partial amount
result = await paystack_provider.refund_payment(
    provider_transaction_id="ref_xxxxx",
    amount=Decimal("50.00"),  # Partial amount
    reason="Partial refund"
)
```

## Error Handling

```python
from apps.shared.integration.wallet.exceptions import (
    ProviderAPIError,
    PaymentDeclinedError,
    ValidationError
)

try:
    transaction, payment_result = await wallet_service.deposit(
        wallet_id="wallet_123",
        amount=Decimal("100.00"),
        payment_provider=PaymentProvider.PAYSTACK,
        metadata={"customer_email": "customer@example.com"}
    )
except ValidationError as e:
    # Missing required fields
    print(f"Validation error: {e}")
except ProviderAPIError as e:
    # Paystack API error
    print(f"Provider error: {e.error_message}")
except Exception as e:
    # Other errors
    print(f"Error: {e}")
```

## Testing

### Test Mode

```python
# Use test API keys for development
paystack_config = ProviderConfig(
    provider=PaymentProvider.PAYSTACK,
    api_key="pk_test_xxx",
    secret_key="sk_test_xxx",
    webhook_secret="your_webhook_secret",
    is_test_mode=True  # Test mode
)
```

### Test Cards (Test Mode Only)

Paystack provides test cards for different scenarios:

**Successful Payment:**
- Card: `5061020000000000094`
- CVV: `123`
- Expiry: Any future date
- PIN: `1234`

**Declined Payment:**
- Card: `4084084084084081`
- CVV: `408`
- Expiry: Any future date

**Insufficient Funds:**
- Card: `5060990580000217499`
- CVV: `123`
- Expiry: Any future date
- PIN: `1234`

### Run Unit Tests

```bash
# Run Paystack provider tests
pytest apps/shared/integration/wallet/tests/test_paystack_provider.py -v

# Run with coverage
pytest apps/shared/integration/wallet/tests/test_paystack_provider.py --cov
```

## Best Practices

### 1. Always Verify Email

```python
# Email is required for Paystack
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("100.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    metadata={
        "customer_email": "customer@example.com"  # ✅ Required
    }
)
```

### 2. Store Customer Code

```python
# Create customer once, reuse customer_code
customer = await paystack_provider.create_customer(
    user_id="user_123",
    email="customer@example.com"
)

# Save customer_code in your database
# user.paystack_customer_code = customer["customer_code"]

# Use for future transactions
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet_123",
    amount=Decimal("100.00"),
    payment_provider=PaymentProvider.PAYSTACK,
    customer_id=user.paystack_customer_code  # Reuse customer
)
```

### 3. Verify Bank Accounts Before Withdrawals

```python
# Always resolve account before creating recipient
account = await paystack_provider.resolve_account_number(
    account_number="0123456789",
    bank_code="044"
)

if account["success"]:
    # Confirm with user: "Is this your account?"
    print(f"Account Name: {account['account_name']}")
else:
    # Invalid account - don't proceed
    print("Invalid account number")
```

### 4. Handle Webhook Idempotency

```python
# Store processed webhook IDs to avoid duplicate processing
@app.post("/api/wallet/webhooks/paystack")
async def handle_paystack_webhook(request: Request):
    payload = await request.json()
    event_id = payload.get("id")

    # Check if already processed
    if await webhook_events.find_one({"event_id": event_id}):
        return {"status": "already_processed"}

    # Process webhook...

    # Store event ID
    await webhook_events.insert_one({"event_id": event_id})

    return {"status": "success"}
```

### 5. Monitor Transaction Fees

```python
# Paystack charges fees - check provider_data for fees
status = await paystack_provider.get_transaction_status("ref_xxxxx")

print(f"Amount charged: {status['amount']}")
print(f"Paystack fees: {status['fees']}")
print(f"Net amount: {status['amount'] - status['fees']}")
```

## Common Issues

### Issue: "Email is required"

**Solution**: Always provide customer email in metadata:

```python
metadata={
    "customer_email": "customer@example.com"
}
```

### Issue: Webhook signature verification fails

**Solution**: Ensure you're passing the raw request body:

```python
# ✅ Correct
raw_body = await request.body()  # Bytes
await provider.verify_webhook(
    payload=payload,
    signature=signature,
    raw_payload=raw_body
)

# ❌ Wrong
await provider.verify_webhook(
    payload=payload,
    signature=signature,
    raw_payload=json.dumps(payload)  # Don't re-serialize
)
```

### Issue: Bank account resolution fails

**Solution**: Verify bank code is correct:

```python
# Get correct bank code first
banks = await paystack_provider.list_banks("ghana")

# Use exact bank code from list
result = await paystack_provider.resolve_account_number(
    account_number="0123456789",
    bank_code="044"  # Must match bank code from list_banks()
)
```

## Health Check

```python
# Check Paystack API connectivity
health = await paystack_provider.health_check()

print(f"Status: {health['status']}")  # healthy or unhealthy
print(f"Message: {health['message']}")
print(f"Test Mode: {health['test_mode']}")
```

## Support

For issues or questions:
- Paystack Documentation: https://paystack.com/docs
- Paystack Support: support@paystack.com
- KasaAI Support: support@kasaai.ailabsafrica.com

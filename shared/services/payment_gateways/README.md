# Payment Gateway Integrations

Centralized payment gateway clients for use across all backend applications (EstateFlow, InkWave, ChurchFlow, etc.).

## Overview

This module provides unified interfaces for:
- **Stripe**: International card payments, customer management, subscriptions
- **Flutterwave**: African markets - cards, mobile money, bank transfers

## Installation

Payment gateway packages are already installed in the shared virtual environment:
```bash
# Stripe (already installed)
pip install stripe

# httpx for Flutterwave
pip install httpx
```

## Environment Variables

Add these to `/opt/kasaai/.env`:

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ENVIRONMENT=sandbox  # or production

# Flutterwave
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-...
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-...
FLUTTERWAVE_ENCRYPTION_KEY=FLWSECK-...
FLUTTERWAVE_WEBHOOK_SECRET=...
```

## Usage Examples

### 1. Stripe Integration

```python
import os
from shared.services.payment_gateways import StripeClient
from decimal import Decimal

# Initialize client
stripe_client = StripeClient(
    secret_key=os.getenv("STRIPE_SECRET_KEY"),
    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
)

# Create payment intent
payment_intent = await stripe_client.create_payment_intent(
    amount=Decimal("50.00"),
    currency="usd",
    metadata={
        "order_id": "12345",
        "customer_name": "John Doe"
    }
)

# Get client_secret for frontend
client_secret = payment_intent["client_secret"]

# Verify payment
payment = await stripe_client.retrieve_payment(payment_intent["id"])
print(f"Payment status: {payment['status']}")

# Refund payment
refund = await stripe_client.refund_payment(
    payment_intent_id=payment_intent["id"],
    amount=Decimal("25.00"),  # Partial refund
    reason="requested_by_customer"
)
```

### 2. Flutterwave Integration

```python
import os
from shared.services.payment_gateways import FlutterwaveClient
from decimal import Decimal

# Initialize client
flutterwave_client = FlutterwaveClient(
    secret_key=os.getenv("FLUTTERWAVE_SECRET_KEY"),
    webhook_secret=os.getenv("FLUTTERWAVE_WEBHOOK_SECRET")
)

# Create payment link
payment = await flutterwave_client.create_payment_intent(
    amount=Decimal("100.00"),
    currency="GHS",
    customer_email="customer@example.com",
    customer_name="Kwame Mensah",
    customer_phone="+233244123456",
    redirect_url="https://myapp.com/payment/callback",
    metadata={
        "order_id": "12345"
    }
)

# Redirect user to payment link
payment_link = payment["payment_link"]

# Verify transaction (after callback)
transaction = await flutterwave_client.retrieve_payment(payment["id"])
print(f"Status: {transaction['status']}")
```

### 3. Mobile Money (Flutterwave)

```python
# Initiate mobile money payment
momo_payment = await flutterwave_client.initiate_mobile_money(
    amount=Decimal("50.00"),
    currency="GHS",
    phone_number="0244123456",
    network="MTN",  # MTN, VODAFONE, or TIGO
    customer_email="customer@example.com",
    customer_name="Kwame Mensah",
    metadata={"order_id": "12345"}
)

# Customer receives prompt on their phone
# Verify after they approve
status = await flutterwave_client.retrieve_payment(momo_payment["id"])
```

### 4. Webhook Verification

```python
from fastapi import Request, HTTPException

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        event = stripe_client.verify_webhook_signature(
            payload=payload.decode("utf-8"),
            signature=signature
        )

        # Handle event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            # Update your database

        return {"status": "success"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(request: Request):
    payload = await request.json()
    signature = request.headers.get("verif-hash")

    try:
        event = flutterwave_client.verify_webhook_signature(
            payload=payload,
            signature=signature
        )

        # Handle event
        if event["event"] == "charge.completed":
            transaction = event["data"]
            # Update your database

        return {"status": "success"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
```

### 5. Customer Management (Stripe)

```python
# Create customer
customer_id = await stripe_client.create_customer(
    email="customer@example.com",
    name="John Doe",
    phone="+1234567890",
    metadata={"app": "estateflow"}
)

# Create payment with saved customer
payment = await stripe_client.create_payment_intent(
    amount=Decimal("50.00"),
    currency="usd",
    customer_id=customer_id
)

# List customer's payment methods
payment_methods = await stripe_client.list_payment_methods(customer_id)
```

## Service Layer Integration

### EstateFlow Example

```python
# app/services/payment_service.py
import os
from motor.motor_asyncio import AsyncIOMotorDatabase
from shared.services.payment_gateways import StripeClient, FlutterwaveClient

class PaymentService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

        # Initialize gateway clients
        self.stripe_client = StripeClient(
            secret_key=os.getenv("STRIPE_SECRET_KEY"),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET")
        )

        self.flutterwave_client = FlutterwaveClient(
            secret_key=os.getenv("FLUTTERWAVE_SECRET_KEY"),
            webhook_secret=os.getenv("FLUTTERWAVE_WEBHOOK_SECRET")
        )

    async def create_payment_intent(
        self,
        gateway: str,
        amount: Decimal,
        currency: str,
        **kwargs
    ):
        if gateway == "stripe":
            return await self.stripe_client.create_payment_intent(
                amount=amount,
                currency=currency,
                **kwargs
            )
        elif gateway == "flutterwave":
            return await self.flutterwave_client.create_payment_intent(
                amount=amount,
                currency=currency,
                **kwargs
            )
        else:
            raise ValueError(f"Unknown gateway: {gateway}")
```

## API Reference

### StripeClient Methods

- `create_payment_intent()` - Create payment intent for card payments
- `retrieve_payment()` - Get payment status
- `confirm_payment_intent()` - Confirm payment
- `cancel_payment()` - Cancel pending payment
- `refund_payment()` - Refund completed payment
- `create_customer()` - Create Stripe customer
- `attach_payment_method()` - Save customer's card
- `list_payment_methods()` - Get saved cards
- `verify_webhook_signature()` - Verify webhook events

### FlutterwaveClient Methods

- `create_payment_intent()` - Create payment link
- `initiate_mobile_money()` - Start mobile money payment
- `retrieve_payment()` - Verify transaction
- `refund_payment()` - Refund transaction
- `verify_webhook_signature()` - Verify webhook events
- `get_banks()` - List banks for country
- `verify_account()` - Verify bank account details

### Status Normalization

Both clients provide `normalize_payment_status()` to convert gateway-specific statuses to common `PaymentStatus` enum:

```python
from shared.services.payment_gateways import PaymentStatus

# Stripe statuses → PaymentStatus
stripe_status = stripe_client.normalize_payment_status("succeeded")
# Returns: PaymentStatus.COMPLETED

# Flutterwave statuses → PaymentStatus
flw_status = flutterwave_client.normalize_payment_status("successful")
# Returns: PaymentStatus.COMPLETED
```

## Testing

### Stripe Test Cards
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
3D Secure: 4000 0025 0000 3155
```

### Flutterwave Test Cards
```
Success: 5531 8866 5214 2950 (CVV: 564, Expiry: 09/32, PIN: 3310, OTP: 12345)
```

### Mobile Money Test
Use test phone numbers provided in Flutterwave test environment documentation.

## Migration Guide

### Migrating from Inline Implementation

**Before:**
```python
import stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

intent = stripe.PaymentIntent.create(
    amount=5000,
    currency="usd"
)
```

**After:**
```python
from shared.services.payment_gateways import StripeClient

stripe_client = StripeClient(
    secret_key=os.getenv("STRIPE_SECRET_KEY")
)

intent = await stripe_client.create_payment_intent(
    amount=Decimal("50.00"),
    currency="usd"
)
```

## Architecture Benefits

1. **Consistency**: All apps use the same payment logic
2. **Maintainability**: Update once, applies everywhere
3. **Testing**: Centralized test suites
4. **Error Handling**: Unified error patterns
5. **Logging**: Consistent logging across apps
6. **Type Safety**: Proper type hints and validation

## Support

For issues or questions:
1. Check this README
2. Review implementation in `estateflow/backend/app/services/payment_service.py`
3. Check Stripe docs: https://stripe.com/docs/api
4. Check Flutterwave docs: https://developer.flutterwave.com/docs

## Changelog

### 2024-12-11
- Initial implementation
- StripeClient with full payment intent support
- FlutterwaveClient with cards, mobile money, bank transfers
- Base interface for extensibility
- Comprehensive documentation

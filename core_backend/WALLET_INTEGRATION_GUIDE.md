# 💰 Wallet & Payment Integration Guide

## Overview

Comprehensive wallet and payment system for **flow.ailabsafrica.com/billing** with support for:

- **Stripe** - International card payments
- **Flutterwave** - African card and mobile money
- **MTN Mobile Money** (Ghana)
- **Vodafone Cash** (Ghana)
- **AirtelTigo Money** (Ghana)
- **M-Pesa** (Kenya)
- **Bank Transfers**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)              │
│                   flow.ailabsafrica.com/billing             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTPS/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Wallet API Routes                              │
│           /api/wallet/* endpoints                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 WalletService                               │
│   - Balance Management                                      │
│   - Transaction Processing                                  │
│   - Payment Method Management                               │
│   - Provider Integrations                                   │
└─────────────┬────────────────┬────────────────┬─────────────┘
              │                │                │
       ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
       │   Stripe    │  │Flutterwave│  │ Mobile Money│
       │     API     │  │    API    │  │   Providers │
       └─────────────┘  └───────────┘  └─────────────┘
```

---

## 📊 Database Models

### Wallet Model

```python
{
    "id": "wallet_abc123",
    "user_id": "auth0|user_123",
    "balance": 150.75,
    "pending_balance": 25.00,
    "reserved_balance": 10.00,
    "currency": "USD",
    "auto_reload_enabled": true,
    "auto_reload_threshold": 10.00,
    "auto_reload_amount": 50.00,
    "is_active": true,
    "created_at": "2025-01-20T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
}
```

### Transaction Model

```python
{
    "id": "txn_abc123",
    "user_id": "auth0|user_123",
    "wallet_id": "wallet_abc123",
    "transaction_type": "deposit",  # deposit, withdrawal, usage_charge, refund
    "status": "completed",  # pending, processing, completed, failed
    "amount": 50.00,
    "currency": "USD",
    "processing_fee": 1.75,
    "total_amount": 51.75,
    "payment_method_id": "pm_abc123",
    "payment_provider": "stripe",
    "provider_transaction_id": "pi_stripe_123",
    "description": "Wallet deposit",
    "balance_before": 100.00,
    "balance_after": 150.00,
    "created_at": "2025-01-20T10:00:00Z",
    "completed_at": "2025-01-20T10:00:15Z"
}
```

### Payment Method Model

```python
{
    "id": "pm_abc123",
    "user_id": "auth0|user_123",
    "provider": "stripe",  # stripe, flutterwave, mtn_momo, etc.
    "method_type": "card",  # card, mobile_money, bank_transfer
    "display_name": "Visa ending in 4242",
    "nickname": "My Business Card",
    "provider_payment_method_id": "pm_stripe_123",
    "card_last4": "4242",
    "card_brand": "visa",
    "phone_number": "+233244123456",  # For mobile money
    "is_default": true,
    "is_verified": true,
    "is_active": true,
    "created_at": "2025-01-20T10:00:00Z"
}
```

---

## 🔌 API Endpoints

### Base URL

```
Production: https://flow-api.ailabsafrica.com/api/wallet
Development: http://localhost:8000/api/wallet
```

### Authentication

All endpoints require authentication via Bearer token:

```http
Authorization: Bearer <supabase_jwt_token>
```

---

### 1. Get Wallet Balance

**GET** `/wallet/balance`

Get current wallet balance and statistics.

**Query Parameters:**
- `currency` (optional): Currency code (USD, GHS, etc.). Default: USD

**Response:**
```json
{
    "wallet_id": "wallet_abc123",
    "balance": 150.75,
    "pending_balance": 25.00,
    "reserved_balance": 10.00,
    "available_balance": 140.75,
    "total_balance": 175.75,
    "currency": "USD",
    "last_transaction_at": "2025-01-20T15:30:00Z",
    "auto_reload_enabled": true,
    "low_balance_alert_enabled": true
}
```

---

### 2. Get Available Payment Providers

**GET** `/wallet/providers`

Get list of available payment providers and their capabilities.

**Response:**
```json
{
    "providers": [
        {
            "provider": "stripe",
            "name": "Stripe",
            "methods": ["card"],
            "currencies": ["USD", "EUR", "GBP", "GHS"],
            "countries": ["worldwide"],
            "logo_url": "/assets/logos/stripe.svg"
        },
        {
            "provider": "flutterwave",
            "name": "Flutterwave",
            "methods": ["card", "mobile_money", "bank_transfer"],
            "currencies": ["USD", "GHS", "NGN", "KES"],
            "countries": ["NG", "GH", "KE", "ZA"],
            "logo_url": "/assets/logos/flutterwave.svg"
        },
        {
            "provider": "mtn_momo",
            "name": "MTN Mobile Money",
            "methods": ["mobile_money"],
            "currencies": ["GHS"],
            "countries": ["GH"],
            "logo_url": "/assets/logos/mtn.svg"
        }
    ]
}
```

---

### 3. Get Payment Methods

**GET** `/wallet/payment-methods`

Get all saved payment methods for current user.

**Response:**
```json
[
    {
        "id": "pm_abc123",
        "provider": "stripe",
        "method_type": "card",
        "display_name": "Visa ending in 4242",
        "nickname": "My Business Card",
        "is_default": true,
        "is_verified": true,
        "is_active": true,
        "created_at": "2025-01-20T10:00:00Z",
        "last_used_at": "2025-01-20T15:30:00Z",
        "card_last4": "4242",
        "card_brand": "visa"
    },
    {
        "id": "pm_momo_123",
        "provider": "mtn_momo",
        "method_type": "mobile_money",
        "display_name": "MTN Mobile Money",
        "phone_number_masked": "+233****3456",
        "is_default": false,
        "is_verified": true,
        "is_active": true,
        "created_at": "2025-01-20T11:00:00Z"
    }
]
```

---

### 4. Add Payment Method

**POST** `/wallet/payment-methods`

Add new payment method (card, mobile money, bank account).

**Request Body (Card via Stripe):**
```json
{
    "provider": "stripe",
    "method_type": "card",
    "display_name": "Visa ending in 4242",
    "stripe_payment_method_id": "pm_1234567890",
    "nickname": "My Primary Card"
}
```

**Request Body (Mobile Money):**
```json
{
    "provider": "mtn_momo",
    "method_type": "mobile_money",
    "display_name": "MTN Mobile Money",
    "phone_number": "+233244123456",
    "nickname": "My MTN MoMo"
}
```

**Response:**
```json
{
    "id": "pm_abc123",
    "provider": "stripe",
    "method_type": "card",
    "display_name": "Visa ending in 4242",
    "is_default": true,
    "is_verified": false,
    "is_active": true,
    "created_at": "2025-01-20T10:00:00Z"
}
```

---

### 5. Update Payment Method

**PATCH** `/wallet/payment-methods/{payment_method_id}`

Update payment method (set as default, change nickname).

**Request Body:**
```json
{
    "nickname": "Updated Nickname",
    "is_default": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Payment method updated"
}
```

---

### 6. Delete Payment Method

**DELETE** `/wallet/payment-methods/{payment_method_id}`

Remove payment method (soft delete).

**Response:**
```json
{
    "success": true,
    "message": "Payment method deleted"
}
```

---

### 7. Create Deposit

**POST** `/wallet/deposit`

Initiate wallet deposit with selected payment method.

**Request Body:**
```json
{
    "amount": 50.00,
    "currency": "USD",
    "payment_method_id": "pm_abc123",
    "description": "Add funds to wallet"
}
```

**Response:**
```json
{
    "id": "txn_abc123",
    "transaction_type": "deposit",
    "status": "processing",
    "amount": 50.00,
    "currency": "USD",
    "processing_fee": 1.75,
    "total_amount": 51.75,
    "description": "Add funds to wallet",
    "payment_method_display": "Visa ending in 4242",
    "created_at": "2025-01-20T10:00:00Z",
    "completed_at": null
}
```

**Note:** For mobile money, user will receive prompt on their phone to enter PIN and confirm payment.

---

### 8. Get Transaction History

**GET** `/wallet/transactions`

Get paginated transaction history.

**Query Parameters:**
- `limit` (optional): Number of transactions. Default: 50
- `offset` (optional): Pagination offset. Default: 0

**Response:**
```json
[
    {
        "id": "txn_abc123",
        "transaction_type": "deposit",
        "status": "completed",
        "amount": 50.00,
        "currency": "USD",
        "processing_fee": 1.75,
        "total_amount": 51.75,
        "description": "Wallet deposit via Stripe",
        "payment_method_display": "Visa ending in 4242",
        "created_at": "2025-01-20T10:00:00Z",
        "completed_at": "2025-01-20T10:00:15Z"
    },
    {
        "id": "txn_def456",
        "transaction_type": "usage_charge",
        "status": "completed",
        "amount": 12.50,
        "currency": "USD",
        "description": "Voice AI usage - January",
        "created_at": "2025-01-20T09:00:00Z",
        "completed_at": "2025-01-20T09:00:01Z"
    }
]
```

---

### 9. Get Transaction Details

**GET** `/wallet/transactions/{transaction_id}`

Get detailed information about specific transaction.

**Response:**
```json
{
    "id": "txn_abc123",
    "transaction_type": "deposit",
    "status": "completed",
    "amount": 50.00,
    "currency": "USD",
    "processing_fee": 1.75,
    "total_amount": 51.75,
    "description": "Wallet deposit via Stripe",
    "payment_method_display": "Visa ending in 4242",
    "created_at": "2025-01-20T10:00:00Z",
    "completed_at": "2025-01-20T10:00:15Z"
}
```

---

## 🔐 Webhook Endpoints

### Stripe Webhook

**POST** `/wallet/webhooks/stripe`

Handles Stripe webhook events for payment confirmations.

**Headers:**
- `Stripe-Signature`: Webhook signature for verification

**Events Handled:**
- `payment_intent.succeeded` - Payment successful
- `payment_intent.payment_failed` - Payment failed

---

### Flutterwave Webhook

**POST** `/wallet/webhooks/flutterwave`

Handles Flutterwave webhook events.

**Headers:**
- `verif-hash`: Verification hash

**Events Handled:**
- Transaction status updates
- Payment confirmations

---

### Mobile Money Webhook

**POST** `/wallet/webhooks/momo-callback`

Handles mobile money payment confirmations (MTN, Vodafone, AirtelTigo).

---

### M-Pesa Webhook

**POST** `/wallet/webhooks/mpesa-callback`

Handles M-Pesa STK push callbacks.

---

## 💻 Frontend Integration

### React/TypeScript Example

```typescript
import { useState, useEffect } from 'react';

interface WalletBalance {
    wallet_id: string;
    balance: number;
    available_balance: number;
    currency: string;
}

// Get wallet balance
async function getWalletBalance(): Promise<WalletBalance> {
    const response = await fetch('https://flow-api.ailabsafrica.com/api/wallet/balance', {
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Failed to fetch wallet balance');
    }

    return response.json();
}

// Add payment method (Stripe card)
async function addStripeCard(paymentMethodId: string) {
    const response = await fetch('https://flow-api.ailabsafrica.com/api/wallet/payment-methods', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            provider: 'stripe',
            method_type: 'card',
            display_name: 'Visa ending in 4242',
            stripe_payment_method_id: paymentMethodId
        })
    });

    return response.json();
}

// Add mobile money payment method
async function addMobileMoneyMethod(phoneNumber: string, provider: string) {
    const response = await fetch('https://flow-api.ailabsafrica.com/api/wallet/payment-methods', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            provider: provider,  // 'mtn_momo', 'vodafone_cash', etc.
            method_type: 'mobile_money',
            display_name: `${provider.toUpperCase()} - ${phoneNumber}`,
            phone_number: phoneNumber
        })
    });

    return response.json();
}

// Create deposit
async function createDeposit(amount: number, paymentMethodId: string) {
    const response = await fetch('https://flow-api.ailabsafrica.com/api/wallet/deposit', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            amount: amount,
            currency: 'USD',
            payment_method_id: paymentMethodId,
            description: 'Add funds to wallet'
        })
    });

    return response.json();
}

// Wallet component
function WalletComponent() {
    const [balance, setBalance] = useState<WalletBalance | null>(null);

    useEffect(() => {
        getWalletBalance().then(setBalance);
    }, []);

    return (
        <div>
            <h2>Wallet Balance</h2>
            {balance && (
                <p>Available: ${balance.available_balance.toFixed(2)}</p>
            )}
        </div>
    );
}
```

---

## ⚙️ Environment Configuration

### Required Environment Variables

Create/update `.env` file with provider credentials:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Flutterwave Configuration
FLUTTERWAVE_SECRET_KEY=FLWSECK-...
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK-...
FLUTTERWAVE_ENCRYPTION_KEY=FLWSECK_TEST...
FLUTTERWAVE_WEBHOOK_HASH=...

# MTN Mobile Money (Ghana)
MTN_MOMO_API_KEY=...
MTN_MOMO_API_USER=...
MTN_MOMO_SUBSCRIPTION_KEY=...

# Vodafone Cash (Ghana)
VODAFONE_MERCHANT_ID=...
VODAFONE_API_KEY=...

# M-Pesa (Kenya)
MPESA_CONSUMER_KEY=...
MPESA_CONSUMER_SECRET=...
MPESA_SHORTCODE=...
MPESA_PASSKEY=...

# Webhook URLs
WALLET_WEBHOOK_BASE_URL=https://flow-api.ailabsafrica.com/api/wallet/webhooks
```

### Initialize Provider Configs

```python
# Create provider configurations in MongoDB
from backend.models.wallet import ProviderConfig, PaymentProvider

# Stripe config
stripe_config = ProviderConfig(
    provider=PaymentProvider.STRIPE,
    environment="sandbox",  # or "production"
    api_key=os.getenv("STRIPE_SECRET_KEY"),
    public_key=os.getenv("STRIPE_PUBLISHABLE_KEY"),
    secret_key=os.getenv("STRIPE_SECRET_KEY"),
    webhook_url=f"{os.getenv('WALLET_WEBHOOK_BASE_URL')}/stripe",
    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
    is_active=True
)

# Save to database
await db.provider_configs.insert_one(stripe_config.dict())
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all wallet tests
cd /opt/kasaai/apps/core_backend
pytest tests/test_wallet_service.py -v

# Run specific test
pytest tests/test_wallet_service.py::test_create_deposit_stripe -v

# Run with coverage
pytest tests/test_wallet_service.py --cov=backend.services.wallet_service --cov-report=html
```

### Test Endpoints with cURL

```bash
# Get wallet balance
curl -X GET "https://flow-api.ailabsafrica.com/api/wallet/balance" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get payment providers
curl -X GET "https://flow-api.ailabsafrica.com/api/wallet/providers"

# Create deposit
curl -X POST "https://flow-api.ailabsafrica.com/api/wallet/deposit" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "currency": "USD",
    "payment_method_id": "pm_abc123"
  }'
```

---

## 📝 Processing Fees

| Provider | Card | Mobile Money | Bank Transfer |
|----------|------|--------------|---------------|
| **Stripe** | 2.9% + $0.30 | N/A | N/A |
| **Flutterwave** | 1.4% | 1.4% | 1.4% |
| **MTN MoMo** | N/A | 1.5% + GHS 0.10 | N/A |
| **Vodafone Cash** | N/A | 1.5% + GHS 0.10 | N/A |
| **AirtelTigo** | N/A | 1.5% + GHS 0.10 | N/A |
| **M-Pesa** | N/A | 1.0% | N/A |

---

## 🔄 Transaction Flow

### Card Payment (Stripe/Flutterwave)

```
1. User clicks "Add Funds"
2. Selects payment method or adds new card
3. Backend creates transaction (status: pending)
4. Backend initiates payment with provider
5. Provider processes payment
6. Provider sends webhook confirmation
7. Backend updates transaction (status: completed)
8. Backend updates wallet balance
9. User sees updated balance
```

### Mobile Money (MTN/Vodafone/AirtelTigo/M-Pesa)

```
1. User clicks "Add Funds"
2. Selects mobile money method
3. Backend creates transaction (status: pending)
4. Backend initiates STK push to user's phone
5. User receives prompt on phone
6. User enters PIN and confirms
7. Provider processes payment
8. Provider sends webhook callback
9. Backend updates transaction (status: completed)
10. Backend updates wallet balance
11. User sees updated balance
```

---

## 🚨 Error Handling

### Common Error Responses

**Insufficient Balance:**
```json
{
    "detail": "Insufficient balance"
}
```

**Payment Method Not Found:**
```json
{
    "detail": "Payment method pm_abc123 not found"
}
```

**Invalid Amount:**
```json
{
    "detail": "Amount must be positive"
}
```

**Provider Error:**
```json
{
    "detail": "Stripe payment intent creation failed: card_declined"
}
```

---

## 📞 Support

### Issues and Questions

- **GitHub Issues**: https://github.com/ailabsafrica/kasaai/issues
- **Email**: support@ailabsafrica.com
- **Documentation**: https://docs.ailabsafrica.com/wallet

### Webhook Debugging

Check webhook event logs:
```python
# Get recent webhook events
events = await db.webhook_events.find(
    {"provider": "stripe"}
).sort("created_at", -1).limit(10).to_list(10)

for event in events:
    print(f"Event: {event['event_type']}")
    print(f"Processed: {event['is_processed']}")
    print(f"Error: {event.get('processing_error')}")
```

---

## 🎯 Next Steps

1. ✅ **Models Created** - Wallet, Transaction, PaymentMethod models
2. ✅ **Service Created** - WalletService with all provider integrations
3. ✅ **API Routes Created** - RESTful endpoints for wallet operations
4. ✅ **Unit Tests Written** - Comprehensive test coverage
5. ✅ **Documentation Complete** - API guide and integration docs

### TODO:
- [ ] Configure provider credentials in production
- [ ] Create frontend React components for billing UI
- [ ] Test with sandbox accounts (Stripe, Flutterwave, Mobile Money)
- [ ] Set up webhook endpoints with proper SSL
- [ ] Monitor transactions in production
- [ ] Implement auto-reload functionality
- [ ] Add webhook retry mechanism
- [ ] Create admin dashboard for transaction monitoring

---

**Last Updated:** 2025-01-20
**Version:** 1.0.0
**Status:** ✅ Ready for Integration

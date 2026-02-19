# ExpressPay Integration Guide

Complete guide for integrating ExpressPay payment provider into the KasaAI wallet system.

**Date**: 2025-11-23
**Provider**: ExpressPay (Ghana)
**Documentation**: https://expresspaygh.com/developers
**Coverage**: Ghana (GHS only)

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Configuration](#configuration)
4. [Payment Flow](#payment-flow)
5. [Code Examples](#code-examples)
6. [Webhook Integration](#webhook-integration)
7. [Security Considerations](#security-considerations)
8. [Mobile Money Support](#mobile-money-support)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

ExpressPay is a Ghanaian payment gateway supporting:

- ✅ **Credit/Debit Cards** (Visa, Mastercard, mVisa)
- ✅ **Mobile Money** (MTN, Vodafone, Airtel, Tigo)
- ✅ **Bank Transfers**
- ✅ **Hosted Payment Page** (PCI compliant)
- ⚠️ **No Webhook Signature Verification** (security limitation)
- ❌ **No Refund API** (manual process via email)

**Key Features**:
- Supports Ghana Cedis (GHS) only
- Sandbox and production environments
- Transaction status querying
- Mobile money async payments with callbacks

**Limitations**:
- GHS currency only (no USD, EUR, etc.)
- No webhook signature verification
- No programmatic refunds
- No customer/payment method storage
- Email must be unique per customer

---

## Getting Started

### 1. Create ExpressPay Account

1. Visit https://expresspaygh.com
2. Sign up for a merchant account
3. Complete KYC verification
4. Get your credentials:
   - **Merchant ID**: Unique identifier for your business
   - **API Key**: Secret key for authenticating requests

### 2. Whitelist Your Server IP

⚠️ **Important**: ExpressPay requires IP whitelisting for security.

1. Log into ExpressPay merchant dashboard
2. Navigate to Settings → API Configuration
3. Add your server's public IP address
4. For development: Add your development server IP

**Find Your Server IP**:
```bash
curl ifconfig.me
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# ExpressPay Credentials
EXPRESSPAY_MERCHANT_ID=your_merchant_id_here
EXPRESSPAY_API_KEY=your_api_key_here

# Webhook URL (for mobile money)
EXPRESSPAY_WEBHOOK_URL=https://yourapp.ailabsafrica.com/api/webhooks/expresspay

# Redirect URL (after payment)
EXPRESSPAY_REDIRECT_URL=https://yourapp.ailabsafrica.com/payment/success
```

### Provider Configuration

Create provider configuration:

```python
from apps.shared.integration.wallet import (
    WalletService,
    ProviderConfig,
    PaymentProvider
)
from apps.shared.integration.wallet.providers import ExpressPayProvider

# Create ExpressPay configuration
expresspay_config = ProviderConfig(
    provider=PaymentProvider.EXPRESSPAY,
    secret_key=os.getenv("EXPRESSPAY_API_KEY"),
    credentials={
        "merchant_id": os.getenv("EXPRESSPAY_MERCHANT_ID")
    },
    is_test_mode=True,  # Use False for production
    webhook_url=os.getenv("EXPRESSPAY_WEBHOOK_URL"),
    redirect_url=os.getenv("EXPRESSPAY_REDIRECT_URL"),
    fee_config={
        "percent": 1.95,  # ExpressPay charges ~1.95% for cards
        "fixed": 0.00,    # No fixed fee
        "cap": None       # No cap
    }
)

# Initialize provider
expresspay_provider = ExpressPayProvider(expresspay_config)

# Register with wallet service
wallet_service.register_provider(
    PaymentProvider.EXPRESSPAY,
    expresspay_provider
)
```

---

## Payment Flow

### Standard Flow (Hosted Payment Page)

```
User → Your App → ExpressPay API → Hosted Payment Page → User Pays → Redirect → Your App
                                                                    ↓
                                                                Webhook → Your App
```

1. **Initialize Payment**: Call `initialize_payment()` to get checkout URL
2. **Redirect User**: Send user to ExpressPay hosted payment page
3. **User Completes Payment**: User enters card/mobile money details
4. **Redirect Back**: ExpressPay redirects to your `redirect_url`
5. **Webhook Notification**: ExpressPay sends webhook to your `post-url`
6. **Query Status**: Your app queries transaction status (critical for security)

---

## Code Examples

### Example 1: Initialize Payment

```python
from decimal import Decimal
from apps.shared.integration.wallet import Currency

# Initialize payment
result = await wallet_service.topup_with_gateway(
    wallet_id="wallet_123",
    amount=Decimal("100.00"),
    gateway=PaymentProvider.EXPRESSPAY,
    payment_metadata={
        "customer_email": "user@example.com",  # Required
        "firstname": "John",
        "lastname": "Doe",
        "phone": "0241234567",  # Ghana format
        "description": "Wallet top-up"
    }
)

if result["success"]:
    # Redirect user to payment page
    payment_url = result["payment_url"]
    print(f"Redirect user to: {payment_url}")

    # Save token for webhook verification
    token = result["provider_transaction_id"]
    await save_payment_token(wallet_id, token)
else:
    print(f"Error: {result['error']}")
```

### Example 2: Handle Redirect Callback

After payment, ExpressPay redirects to your `redirect_url` with parameters:

```python
from fastapi import Request

@app.get("/payment/success")
async def payment_success(request: Request):
    """Handle redirect after payment."""

    # Extract parameters
    order_id = request.query_params.get("order-id")
    token = request.query_params.get("token")

    if not order_id or not token:
        return {"error": "Missing parameters"}

    # Query transaction status (critical for security!)
    status = await expresspay_provider.get_transaction_status(token)

    if status["result"] == 1:  # Approved
        # Update wallet balance
        await wallet_service._complete_transaction(
            transaction_id=order_id,
            provider_data=status
        )
        return {"status": "success", "message": "Payment completed"}

    elif status["result"] == 4:  # Pending (mobile money)
        return {"status": "pending", "message": "Payment being processed"}

    else:  # Declined or Error
        return {
            "status": "failed",
            "message": status.get("result-text", "Payment failed")
        }
```

### Example 3: Handle Webhook

⚠️ **Security Critical**: Always query transaction status, don't trust webhook data alone!

```python
from fastapi import Request, HTTPException

@app.post("/api/webhooks/expresspay")
async def expresspay_webhook(request: Request):
    """
    Handle webhook from ExpressPay.

    Security Note: ExpressPay does NOT provide webhook signatures.
    Always query transaction status to verify authenticity.
    """

    # Parse webhook data (form-urlencoded)
    form_data = await request.form()
    payload = dict(form_data)

    # Extract parameters
    order_id = payload.get("order-id") or payload.get("order_id")
    token = payload.get("token")

    if not order_id or not token:
        raise HTTPException(status_code=400, detail="Missing parameters")

    # Verify token belongs to a valid transaction in our system
    transaction = await get_transaction_by_id(order_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction.provider_transaction_id != token:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Query ExpressPay for actual status (critical security step!)
    try:
        status = await expresspay_provider.get_transaction_status(token)
    except Exception as e:
        logger.error(f"Failed to query ExpressPay status: {e}")
        raise HTTPException(status_code=500, detail="Status query failed")

    # Process based on status
    if status["result"] == 1:  # Approved
        await wallet_service._complete_transaction(order_id, status)
        logger.info(f"Payment approved: {order_id}")

    elif status["result"] == 4:  # Still pending
        logger.info(f"Payment still pending: {order_id}")

    else:  # Declined or Error
        await wallet_service._fail_transaction(
            order_id,
            status.get("result-text", "Payment failed")
        )
        logger.warning(f"Payment failed: {order_id}")

    # Return HTTP 200 immediately
    return {"status": "received"}
```

---

## Webhook Integration

### Webhook URL Configuration

1. **Set webhook URL** in provider configuration:
   ```python
   webhook_url="https://yourapp.ailabsafrica.com/api/webhooks/expresspay"
   ```

2. **Ensure HTTPS**: ExpressPay requires HTTPS for webhooks

3. **Return 200 OK quickly**: Process webhook asynchronously

### Webhook Payload

ExpressPay sends minimal data via POST (form-urlencoded):

```
POST /api/webhooks/expresspay
Content-Type: application/x-www-form-urlencoded

order-id=txn_123&token=abc123def456
```

**Important**: The webhook does NOT include transaction status! You must query the API.

### Security Best Practices

Since ExpressPay doesn't provide webhook signatures:

1. ✅ **Validate token ownership**: Verify token belongs to a transaction in your database
2. ✅ **Always query status**: Call `get_transaction_status()` to verify webhook authenticity
3. ✅ **IP whitelisting**: Only accept webhooks from ExpressPay IPs (if they provide them)
4. ✅ **Rate limiting**: Prevent webhook flooding attacks
5. ✅ **Idempotency**: Handle duplicate webhooks gracefully
6. ✅ **Audit logging**: Log all webhook attempts with IP address and payload

---

## Security Considerations

### ⚠️ Critical Security Limitation

**ExpressPay does NOT support webhook signature verification.**

This means webhooks can be spoofed by attackers. **Always** query transaction status:

```python
# ❌ NEVER trust webhook data alone
if payload.get("status") == "success":
    await credit_wallet()  # DANGEROUS!

# ✅ ALWAYS query transaction status
status = await expresspay_provider.get_transaction_status(token)
if status["result"] == 1:  # Verified from ExpressPay API
    await credit_wallet()  # SAFE
```

### Additional Security Measures

1. **HTTPS Only**: All redirect and webhook URLs must use HTTPS
2. **IP Whitelisting**: Whitelist your server IP in ExpressPay dashboard
3. **Token Validation**: Store tokens in database, validate ownership before processing
4. **Transaction Timeouts**: Expire payment sessions after 30 minutes
5. **Fraud Detection**: Enable wallet fraud detection service (see Phase 2)

---

## Mobile Money Support

ExpressPay supports 4 mobile money networks in Ghana:

| Network | Code | Test Number |
|---------|------|-------------|
| MTN Mobile Money | `MTN_MM` | +233244123123 |
| Vodafone Cash | `VODAFONE_CASH` | +233200123123 |
| Airtel Money | `AIRTEL_MM` | +233277123123 |
| Tigo Cash | `TIGO_CASH` | +233277123123 |

### Mobile Money Flow

Mobile money payments are **asynchronous**:

1. User initiates payment on hosted page
2. ExpressPay sends USSD prompt to user's phone
3. User approves on phone
4. Status changes from **Pending (4)** → **Approved (1)**
5. Webhook is sent to your `post-url`
6. You query status to confirm

### Mobile Money Example

```python
# Initialize payment (user will select mobile money on hosted page)
result = await wallet_service.topup_with_gateway(
    wallet_id="wallet_123",
    amount=Decimal("50.00"),
    gateway=PaymentProvider.EXPRESSPAY,
    payment_metadata={
        "customer_email": "user@example.com",
        "phone": "0244123456",  # Mobile money number
        "firstname": "John",
        "lastname": "Doe",
        "description": "Mobile money top-up"
    }
)

# User will be redirected to hosted page
# User selects "Mobile Money"
# User enters phone number (or uses pre-filled)
# ExpressPay sends USSD prompt
# User approves on phone
# Webhook is sent when status changes to Approved
```

---

## Testing

### Sandbox Environment

ExpressPay provides a sandbox for testing:

**Sandbox URLs**:
- Submit: `https://sandbox.expresspaygh.com/api/submit.php`
- Checkout: `https://sandbox.expresspaygh.com/api/checkout.php`
- Query: `https://sandbox.expresspaygh.com/api/query.php`

### Test Credentials

Contact ExpressPay support for sandbox credentials:
- support@expresspaygh.com

### Test Cards (mVisa)

ExpressPay provides test account numbers:
- **Account 412301**: Test success scenario
- **Account 412302**: Test decline scenario
- **Account 412303**: Test insufficient funds
- **Account 412304**: Test invalid card
- **Account 412305**: Test expired card
- **Account 412306**: Test processing error
- **Account 412307**: Test fraud check

### Test Mobile Money Numbers

Use these numbers in sandbox:
- **MTN**: +233244123123
- **Vodafone**: +233200123123
- **Airtel**: +233277123123
- **Tigo**: +233277123123

### Running Tests

```bash
# Run ExpressPay provider tests
cd /opt/kasaai/apps/shared/integration/wallet
pytest tests/test_expresspay_provider.py -v

# Run with coverage
pytest tests/test_expresspay_provider.py --cov=providers/expresspay_provider --cov-report=html

# Run specific test
pytest tests/test_expresspay_provider.py::TestPaymentInitialization::test_initialize_payment_success -v
```

---

## Troubleshooting

### Common Issues

#### 1. **Invalid Credentials Error**

```
ProviderAPIError: Invalid credentials (merchant_id or api_key)
```

**Solutions**:
- Verify `EXPRESSPAY_MERCHANT_ID` in `.env`
- Verify `EXPRESSPAY_API_KEY` in `.env`
- Check for trailing spaces in credentials
- Ensure using correct credentials for sandbox/production

#### 2. **IP Not Whitelisted Error**

```
ProviderAPIError: Server IP not whitelisted with ExpressPay
```

**Solutions**:
- Find your server IP: `curl ifconfig.me`
- Add IP to ExpressPay dashboard: Settings → API Configuration
- Wait 5-10 minutes for IP whitelist to propagate
- For load balanced servers: Whitelist all server IPs

#### 3. **Currency Not Supported Error**

```
ValidationError: ExpressPay only supports GHS, got USD
```

**Solutions**:
- ExpressPay only supports GHS (Ghana Cedis)
- Convert to GHS before calling ExpressPay
- Use different provider for other currencies (Stripe, Paystack)

#### 4. **Webhook Not Received**

**Solutions**:
- Verify webhook URL is HTTPS (HTTP not supported)
- Check webhook URL is publicly accessible
- Verify server firewall allows ExpressPay IPs
- Check application logs for webhook errors
- Test webhook URL with curl:
  ```bash
  curl -X POST https://yourapp.com/api/webhooks/expresspay \
    -d "order-id=test123&token=test_token"
  ```

#### 5. **Mobile Money Payment Stays Pending**

**Solutions**:
- Mobile money requires user approval on phone
- Wait up to 5 minutes for USSD prompt
- Webhook only sent after user approves
- Query status manually if webhook not received:
  ```python
  status = await expresspay_provider.get_transaction_status(token)
  ```

### Debug Mode

Enable detailed logging:

```python
import logging

# Enable debug logging for ExpressPay
logging.getLogger("apps.shared.integration.wallet.providers.expresspay_provider").setLevel(logging.DEBUG)

# Enable debug logging for wallet service
logging.getLogger("apps.shared.integration.wallet.wallet_service").setLevel(logging.DEBUG)
```

### Contact Support

**ExpressPay Support**:
- Email: support@expresspaygh.com
- Phone: +233 (0) 302 740 068
- Website: https://expresspaygh.com/contact

---

## Refunds

⚠️ **ExpressPay does NOT provide a refund API.**

### Manual Refund Process

1. **Log Refund Request**:
   ```python
   try:
       await expresspay_provider.refund_payment(token, amount, reason)
   except NotImplementedError:
       # Expected - log for manual processing
       await log_manual_refund_request(
           provider="expresspay",
           transaction_id=txn_id,
           amount=amount,
           reason=reason,
           customer_email=email
       )
   ```

2. **Contact ExpressPay Support**:
   - Email: support@expresspaygh.com
   - Subject: "Refund Request - Transaction [transaction_id]"
   - Include:
     - Transaction ID (from ExpressPay)
     - Order ID (your system)
     - Amount to refund
     - Reason for refund
     - Customer details

3. **Track Refund Status**:
   - ExpressPay will process refund manually
   - Typically takes 3-5 business days
   - Update your system after refund is confirmed

---

## Best Practices

### 1. Always Query Status

Never trust webhook or redirect data alone:

```python
# After webhook or redirect
status = await expresspay_provider.get_transaction_status(token)

if status["result"] == 1:  # Verified from API
    # Process payment
    pass
```

### 2. Handle Pending Payments

Mobile money payments can stay pending for minutes:

```python
if status["result"] == 4:  # Pending
    # Schedule background check
    await schedule_status_check(token, delay_minutes=2)
```

### 3. Implement Idempotency

Handle duplicate webhooks:

```python
transaction = await get_transaction(order_id)

if transaction.status == "completed":
    # Already processed, return 200 OK
    return {"status": "already_processed"}

# Process webhook
await process_payment(order_id, status)
```

### 4. Log Everything

Comprehensive logging for debugging:

```python
logger.info(f"ExpressPay webhook received: order_id={order_id}, token={token[:20]}...")
logger.info(f"ExpressPay status query: result={status['result']}, text={status['result-text']}")
logger.info(f"ExpressPay payment completed: txn_id={status.get('transaction-id')}")
```

### 5. Monitor Failed Payments

Track and alert on failed payments:

```python
if status["result"] in [2, 3]:  # Declined or Error
    await alert_admin(
        f"ExpressPay payment failed: {order_id}",
        f"Reason: {status.get('result-text')}"
    )
```

---

## Summary

**ExpressPay Integration Checklist**:

- [x] Obtain merchant credentials (merchant-id, api-key)
- [x] Whitelist server IP in ExpressPay dashboard
- [x] Configure environment variables
- [x] Register ExpressPayProvider with wallet service
- [x] Implement payment initialization endpoint
- [x] Implement redirect callback endpoint
- [x] Implement webhook endpoint with status querying
- [x] Add comprehensive error handling
- [x] Enable logging and monitoring
- [x] Test in sandbox environment
- [x] Test mobile money payments
- [x] Implement manual refund tracking
- [x] Deploy to production

**Key Takeaways**:
1. GHS (Ghana Cedis) only
2. Always query transaction status (no webhook signatures)
3. Mobile money is asynchronous (handle pending status)
4. No programmatic refunds (manual via email)
5. IP whitelisting required

---

**Document Version**: 1.0
**Last Updated**: 2025-11-23
**Maintainer**: KasaAI Team

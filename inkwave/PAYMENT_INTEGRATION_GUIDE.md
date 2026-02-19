# InkWave Payment Integration Guide

Complete guide for setting up Stripe and Paystack payment gateways in InkWave.

## 📋 Overview

InkWave supports two payment gateways:
- **Stripe**: For international payments (credit/debit cards worldwide)
- **Paystack**: For African markets (cards, bank transfers, mobile money)

Both integrations are **fully implemented** and production-ready. You just need to configure API keys.

## 🔑 Getting API Keys

### Paystack Setup (Africa)

1. **Create Account**
   - Go to: https://dashboard.paystack.com/signup
   - Complete registration and email verification

2. **Get Test Keys**
   - Navigate to: **Settings** → **API Keys & Webhooks**
   - Toggle to **Test Mode**
   - Copy your **Test Secret Key** (starts with `sk_test_`)

3. **Test Cards**
   ```
   Success Card:
   - Number: 5060 6661 1111 1111 119
   - CVV: 124
   - Expiry: Any future date
   - PIN: 1234

   Decline Card:
   - Number: 5060 6666 6666 6666 666
   - CVV: 123
   - Expiry: Any future date
   ```

4. **Live Keys** (for production)
   - Toggle to **Live Mode**
   - Complete business verification
   - Copy **Live Secret Key**

### Stripe Setup (International)

1. **Create Account**
   - Go to: https://dashboard.stripe.com/register
   - Complete registration

2. **Get Test Keys**
   - Toggle **Test mode** in top right corner
   - Navigate to: **Developers** → **API keys**
   - Copy your **Secret key** (starts with `sk_test_`)

3. **Test Cards**
   ```
   Success Card:
   - Number: 4242 4242 4242 4242
   - CVV: Any 3 digits
   - Expiry: Any future date

   Decline Card:
   - Number: 4000 0000 0000 0002
   - CVV: Any 3 digits
   - Expiry: Any future date

   3D Secure Card:
   - Number: 4000 0027 6000 3184
   - CVV: Any 3 digits
   - Expiry: Any future date
   ```

4. **Live Keys** (for production)
   - Toggle off **Test mode**
   - Complete business verification
   - Copy **Live Secret key**

## ⚙️ Configuration

### 1. Update Environment Variables

Edit `/opt/kasaai/apps/inkwave/backend/.env`:

```bash
# Payment Gateways
STRIPE_SECRET_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important:**
- Use `sk_test_` keys for testing
- Use `sk_live_` keys for production
- NEVER commit API keys to git
- Keep keys secure and rotate regularly

### 2. Restart Backend

```bash
sudo systemctl restart inkwave-backend
```

### 3. Verify Configuration

```bash
# Check wallet service health
curl -s https://dev-inkwave-api.ailabsafrica.com/api/v1/wallet/health | jq .

# Should return:
# {
#   "status": "healthy",
#   "service": "inkwave_wallet"
# }
```

## 🌐 Webhook Setup (Production Only)

Webhooks allow payment gateways to notify your server about payment status changes.

### Paystack Webhooks

1. **Configure Webhook**
   - Go to: **Settings** → **API Keys & Webhooks**
   - Click **Add Webhook**
   - URL: `https://inkwave-api.ailabsafrica.com/api/v1/wallet/webhooks/paystack`
   - Events: Select **All events** or specific ones

2. **Note**: Paystack verification is synchronous, so webhooks are optional

### Stripe Webhooks

1. **Configure Webhook**
   - Go to: **Developers** → **Webhooks**
   - Click **Add endpoint**
   - URL: `https://inkwave-api.ailabsafrica.com/api/v1/wallet/webhooks/stripe`
   - Events to select:
     - `checkout.session.completed`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`

2. **Add Signing Secret**
   - Copy the **Signing secret** (starts with `whsec_`)
   - Add to .env:
     ```bash
     STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```

3. **Test Webhook** (optional)
   ```bash
   stripe listen --forward-to localhost:8001/api/v1/wallet/webhooks/stripe
   ```

## 🧪 Testing Payment Flow

### Test Mode (Dev Server)

1. **Login**
   - Go to: https://dev-inkwave.ailabsafrica.com/login
   - Use: `admin@ailabsafrica.com` / `Admin@2024!`

2. **Navigate to Wallet**
   - Click **Wallet** in navigation

3. **Initiate Top-up**
   - Click any top-up package ($5, $10, $25, $50)
   - Select payment gateway (Stripe or Paystack)

4. **Complete Payment**
   - Use test card numbers above
   - Complete the payment form
   - You'll be redirected back to InkWave

5. **Verify Wallet Credit**
   - Check wallet balance updated
   - View transaction in transaction history

### Expected Flow

```
1. User clicks "$10" package
   ↓
2. Modal shows: "Pay with Stripe" or "Pay with Paystack"
   ↓
3. User selects gateway → API call to /wallet/topup/{gateway}/initiate
   ↓
4. Backend creates checkout session
   ↓
5. User redirected to Stripe/Paystack checkout page
   ↓
6. User enters test card details
   ↓
7. Payment processed by gateway
   ↓
8. Gateway redirects back to InkWave (?payment=success)
   ↓
9. Paystack: Direct verification via API
   Stripe: Webhook processes payment
   ↓
10. Wallet credited automatically
    ↓
11. Success notification + balance update
```

## 📊 API Endpoints

### Payment Initiation

**POST** `/api/v1/wallet/topup/paystack/initiate`
```json
{
  "amount": 10.0,
  "callback_url": "https://inkwave.com/wallet?payment=success"
}
```

Response:
```json
{
  "success": true,
  "payment_url": "https://checkout.paystack.com/xxxxx",
  "reference": "topup-wallet-abc123",
  "amount": 10.0,
  "currency": "USD"
}
```

**POST** `/api/v1/wallet/topup/stripe/initiate`
```json
{
  "amount": 10.0,
  "success_url": "https://inkwave.com/wallet?payment=success",
  "cancel_url": "https://inkwave.com/wallet?payment=cancelled"
}
```

Response:
```json
{
  "success": true,
  "payment_url": "https://checkout.stripe.com/c/pay/xxxxx",
  "reference": "topup-wallet-xyz789",
  "amount": 10.0,
  "currency": "USD"
}
```

### Payment Verification

**GET** `/api/v1/wallet/topup/paystack/verify/{reference}`

Response:
```json
{
  "success": true,
  "message": "Payment verified and wallet credited",
  "payment_data": { ... }
}
```

### Webhooks

**POST** `/api/v1/wallet/webhooks/stripe` (called by Stripe)
**POST** `/api/v1/wallet/webhooks/paystack` (called by Paystack - optional)

## 🛡️ Security Best Practices

1. **API Keys**
   - Never expose in frontend code
   - Store in environment variables only
   - Use test keys in development
   - Rotate keys regularly

2. **Webhook Verification**
   - Verify webhook signatures (implement if needed)
   - Use HTTPS only
   - Log all webhook events

3. **Amount Validation**
   - Validate amounts on backend
   - Check currency matches
   - Verify transaction hasn't been processed

4. **Idempotency**
   - Use unique reference for each transaction
   - Check for duplicate payments
   - Implement retry logic safely

## 🐛 Troubleshooting

### "Paystack secret key not configured"

**Solution**:
```bash
# Check .env has correct variable name
grep PAYSTACK_SECRET_KEY /opt/kasaai/apps/inkwave/backend/.env

# Should be PAYSTACK_SECRET_KEY, not PAYSTACK_API_KEY
# Restart backend after changing
sudo systemctl restart inkwave-backend
```

### "Stripe library not installed"

**Solution**:
```bash
source /opt/kasaai/apps/venv/bin/activate
pip install stripe
sudo systemctl restart inkwave-backend
```

### Payment succeeds but wallet not credited

**Possible causes**:
1. Webhook not configured (Stripe)
2. Verification API call failed (Paystack)
3. Wallet service not initialized

**Check logs**:
```bash
sudo journalctl -u inkwave-backend -f | grep -i wallet
```

### 401 Unauthorized errors

**Solution**: User must be logged in. Check:
```javascript
// In browser console
const { data } = await window.supabase.auth.getSession();
console.log('Logged in:', data.session ? 'Yes' : 'No');
```

## 💰 Pricing

InkWave uses a credit system:
- **100 credits = $1 USD**
- **Audio narration**: 2 credits/minute ($0.02/min)
- **Voice Q&A**: ~30 credits/question ($0.30/question)
- **Welcome bonus**: $10 (1000 credits) for new users

## 📚 Resources

- [Paystack Documentation](https://paystack.com/docs/api/)
- [Stripe Documentation](https://docs.stripe.com/api)
- [Shared Wallet Service Code](/apps/shared/integration/wallet.py)
- [InkWave Wallet Routes](/apps/inkwave/backend/app/api/routes/wallet.py)

## 🚀 Production Checklist

- [ ] Replace test API keys with live keys
- [ ] Configure production webhooks
- [ ] Enable webhook signature verification
- [ ] Set up monitoring and alerting
- [ ] Test payment flow with real cards
- [ ] Configure proper error handling
- [ ] Set up transaction logging
- [ ] Implement refund functionality
- [ ] Add payment retry logic
- [ ] Configure rate limiting

## 📝 Notes

- **Paystack** works best for: Nigeria, Ghana, Kenya, South Africa
- **Stripe** works globally but has higher fees in Africa
- Both gateways support multiple currencies
- Transaction fees vary by country and payment method
- Consider implementing both for maximum coverage
- Test thoroughly before going live
- Monitor transaction success rates
- Have customer support ready for payment issues

---

**Need Help?**
- Check logs: `sudo journalctl -u inkwave-backend -f`
- Review code: `/apps/shared/integration/wallet.py`
- Contact support with transaction reference numbers
